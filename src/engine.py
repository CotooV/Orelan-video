"""Motor de render: GLSL sobre OpenGL 3.3 (moderngl), acumulación temporal
para motion blur real + antialiasing, bloom y revelado fílmico.

Cada fotograma integra N submuestras dentro de un obturador de 180°. Las
submuestras se recortan al intervalo del plano, de modo que el desenfoque de
movimiento nunca mezcla imágenes a través de un corte.
"""
import os
import numpy as np
import moderngl

from timeline import W, H, FPS, SHUTTER

HERE = os.path.dirname(os.path.abspath(__file__))
SHADERS = os.path.join(HERE, "shaders")


def read_shader(name):
    with open(os.path.join(SHADERS, name), encoding="utf-8") as f:
        return f.read()


def halton(i, b):
    f, r = 1.0, 0.0
    while i > 0:
        f /= b
        r += f * (i % b)
        i //= b
    return r


def make_noise_volume(n=128, seed=7):
    """Ruido fBm tileable por síntesis espectral (1/f^beta)."""
    rng = np.random.default_rng(seed)
    white = rng.standard_normal((n, n, n)).astype(np.float32)
    F = np.fft.rfftn(white)
    kx = np.fft.fftfreq(n)[:, None, None]
    ky = np.fft.fftfreq(n)[None, :, None]
    kz = np.fft.rfftfreq(n)[None, None, :]
    k = np.sqrt(kx ** 2 + ky ** 2 + kz ** 2)
    k[0, 0, 0] = 1.0
    amp = k ** (-1.55) * np.exp(-(k / 0.22) ** 2)
    amp[0, 0, 0] = 0.0
    vol = np.fft.irfftn(F * amp, s=(n, n, n)).astype(np.float32)
    vol -= vol.mean()
    vol /= 3.2 * vol.std()
    vol = np.clip(vol + 0.5, 0.0, 1.0)
    return vol


class Engine:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.ctx = moderngl.create_standalone_context(require=330)
        ctx = self.ctx
        quad = np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype="f4")
        self.quad_vbo = ctx.buffer(quad.tobytes())
        self.vert = read_shader("fullscreen.vert")
        self.common = read_shader("common.glsl")

        vol = make_noise_volume()
        self.noise = ctx.texture3d(vol.shape, 1, (vol * 255).astype(np.uint8).tobytes(), dtype="f1")
        self.noise.repeat_x = self.noise.repeat_y = self.noise.repeat_z = True
        self.noise.filter = (moderngl.LINEAR, moderngl.LINEAR)

        self.scene_tex = ctx.texture((w, h), 4, dtype="f4")
        self.scene_fbo = ctx.framebuffer([self.scene_tex])
        self.accum_tex = ctx.texture((w, h), 4, dtype="f4")
        self.accum_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        for t in (self.scene_tex, self.accum_tex):
            t.repeat_x = t.repeat_y = False
        self.accum_fbo = ctx.framebuffer([self.accum_tex])
        self.text_tmp = ctx.texture((w, h), 4, dtype="f4")
        self.text_tmp_fbo = ctx.framebuffer([self.text_tmp])
        self.text_acc = ctx.texture((w, h), 4, dtype="f4")
        for t in (self.text_tmp, self.text_acc):
            t.repeat_x = t.repeat_y = False
        self.text_acc_fbo = ctx.framebuffer([self.text_acc])
        self.out_tex = ctx.texture((w, h), 3, dtype="f1")
        self.out_fbo = ctx.framebuffer([self.out_tex])

        # cadena de bloom
        self.bloom_levels = []
        bw, bh = w // 2, h // 2
        for _ in range(7):
            t = ctx.texture((bw, bh), 4, dtype="f2")
            t.filter = (moderngl.LINEAR, moderngl.LINEAR)
            t.repeat_x = t.repeat_y = False
            self.bloom_levels.append((t, ctx.framebuffer([t]), bw, bh))
            bw, bh = max(1, bw // 2), max(1, bh // 2)

        self.p_accum = self.program(read_shader("accum.frag"))
        self.p_down = self.program(read_shader("downsample.frag"))
        self.p_up = self.program(read_shader("upsample.frag"))
        self.p_post = self.program(read_shader("post.frag"))
        self.p_text = ctx.program(vertex_shader=read_shader("text.vert"), fragment_shader=read_shader("text.frag"))
        self.p_copy4 = self.program(read_shader("accum.frag").replace(
            "fragColor = vec4(texture(uSrc, vUV).rgb * uWeight, uWeight);",
            "fragColor = texture(uSrc, vUV) * uWeight;"))
        corners = np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype="f4")
        self.corner_vbo = ctx.buffer(corners.tobytes())
        self.inst_vbo = ctx.buffer(reserve=17 * 4 * 512, dynamic=True)
        self.text_vao = ctx.vertex_array(self.p_text, [
            (self.corner_vbo, "2f", "in_corner"),
            (self.inst_vbo, "4f 4f 4f 4f 1f/i", "i_rect", "i_uv", "i_par", "i_col", "i_piv"),
        ])
        self.atlas = None
        self.vaos = {}
        self.scene_programs = {}

    # ------------------------------------------------------------------
    def program(self, frag, with_common=False):
        src = (self.common + "\n" + frag) if with_common else frag
        return self.ctx.program(vertex_shader=self.vert, fragment_shader=src)

    def vao(self, prog):
        key = id(prog)
        if key not in self.vaos:
            self.vaos[key] = self.ctx.vertex_array(prog, [(self.quad_vbo, "2f", "in_pos")])
        return self.vaos[key]

    def scene_program(self, name):
        if name not in self.scene_programs:
            self.scene_programs[name] = self.program(read_shader(name), with_common=True)
        return self.scene_programs[name]

    @staticmethod
    def set_uniforms(prog, values):
        for k, v in values.items():
            if k in prog:
                u = prog[k]
                if isinstance(v, (list, tuple, np.ndarray)):
                    u.value = tuple(float(x) for x in v)
                elif isinstance(v, int) and not isinstance(v, bool):
                    try:
                        u.value = v
                    except Exception:
                        u.value = float(v)
                else:
                    u.value = float(v)

    def draw_fullscreen(self, prog, fbo, uniforms, textures=()):
        fbo.use()
        for unit, (name, tex) in enumerate(textures):
            tex.use(location=unit)
            if name in prog:
                prog[name].value = unit
        self.set_uniforms(prog, uniforms)
        self.vao(prog).render(moderngl.TRIANGLE_STRIP)

    # ------------------------------------------------------------------
    def draw_text(self, inst, jit):
        """Compone los glifos de una submuestra y los suma al acumulador."""
        ctx = self.ctx
        self.text_tmp_fbo.clear(0.0, 0.0, 0.0, 0.0)
        n = len(inst)
        self.inst_vbo.write(np.ascontiguousarray(inst, dtype="f4").tobytes())
        self.text_tmp_fbo.use()
        self.atlas.use(location=0)
        self.p_text["uAtlas"].value = 0
        self.p_text["uRes"].value = (float(self.w), float(self.h))
        self.p_text["uJit"].value = tuple(float(j) for j in jit)
        self.p_text["uScale"].value = self.w / 1080.0
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = moderngl.ONE, moderngl.ONE_MINUS_SRC_ALPHA
        self.text_vao.render(moderngl.TRIANGLE_STRIP, instances=n)
        ctx.disable(moderngl.BLEND)

    def render_frame(self, frame, shot, nsamples, overlay=None, post=None):
        """Integra `nsamples` submuestras del plano `shot` y revela el fotograma.

        shot: objeto con .name, .start, .end, .shader, .textures(), .uniforms(t)
        overlay: callable(t, fbo) que compone tipografía sobre la escena.
        Devuelve un array uint8 (H, W, 3) orientado de arriba abajo.
        """
        ctx = self.ctx
        t0 = frame / FPS
        dt = SHUTTER / FPS
        self.accum_fbo.clear(0.0, 0.0, 0.0, 0.0)
        self.text_acc_fbo.clear(0.0, 0.0, 0.0, 0.0)
        prog = self.scene_program(shot.shader)
        for s in range(nsamples):
            # muestreo estratificado del obturador, recortado al plano
            ts = t0 + (s + 0.5) / nsamples * dt
            ts = min(ts, shot.end - 1e-4)
            jit = (halton(s + 1, 2) - 0.5, halton(s + 1, 3) - 0.5)
            u = {
                "uRes": (self.w, self.h),
                "uT": ts - shot.start,
                "uG": ts,
                "uJit": jit,
                "uSeed": float(frame * 64 + s) * 0.618034 % 97.0 + s,
                "uSample": s,
            }
            u.update(shot.uniforms(ts))
            ctx.disable(moderngl.BLEND)
            texs = [("uNoise", self.noise)] + list(shot.textures())
            self.draw_fullscreen(prog, self.scene_fbo, u, texs)
            inst = overlay(ts) if overlay is not None else None
            if inst is not None and len(inst):
                self.draw_text(inst, jit)
                ctx.enable(moderngl.BLEND)
                ctx.blend_func = moderngl.ONE, moderngl.ONE
                self.draw_fullscreen(self.p_copy4, self.text_acc_fbo, {"uWeight": 1.0 / nsamples},
                                     [("uSrc", self.text_tmp)])
                ctx.disable(moderngl.BLEND)
            ctx.enable(moderngl.BLEND)
            ctx.blend_func = moderngl.ONE, moderngl.ONE
            ctx.blend_equation = moderngl.FUNC_ADD
            self.draw_fullscreen(self.p_accum, self.accum_fbo, {"uWeight": 1.0 / nsamples},
                                 [("uSrc", self.scene_tex)])
            ctx.disable(moderngl.BLEND)
        return self.develop(frame, post or {})

    def develop(self, frame, post):
        ctx = self.ctx
        ctx.disable(moderngl.BLEND)
        src, sw, sh = self.accum_tex, self.w, self.h
        for i, (t, fbo, bw, bh) in enumerate(self.bloom_levels):
            self.draw_fullscreen(self.p_down, fbo, {
                "uTexel": (1.0 / sw, 1.0 / sh), "uPrefilter": 1 if i == 0 else 0,
                "uThreshold": post.get("threshold", 1.2), "uKnee": 0.6, "uClamp": post.get("bclamp", 1e4),
            }, [("uSrc", src)])
            src, sw, sh = t, bw, bh
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = moderngl.ONE, moderngl.ONE
        for i in range(len(self.bloom_levels) - 1, 0, -1):
            lo, _, lw, lh = self.bloom_levels[i]
            _, hi_fbo, hw, hh = self.bloom_levels[i - 1]
            hi_fbo.use()
            self.draw_fullscreen(self.p_up, hi_fbo, {"uTexel": (1.0 / lw, 1.0 / lh), "uRadius": 1.0},
                                 [("uSrc", lo)])
        ctx.disable(moderngl.BLEND)
        self.draw_fullscreen(self.p_post, self.out_fbo, {
            "uRes": (self.w, self.h),
            "uExposure": post.get("exposure", 1.0),
            "uBloomAmt": post.get("bloom", 0.08) / len(self.bloom_levels),
            "uVignette": post.get("vignette", 0.35),
            "uGrain": post.get("grain", 0.010),
            "uFrame": float(frame),
            "uFade": post.get("fade", 1.0),
        }, [("uHDR", self.accum_tex), ("uBloom", self.bloom_levels[0][0]), ("uText", self.text_acc)])
        data = self.out_fbo.read(components=3, alignment=1)
        img = np.frombuffer(data, dtype=np.uint8).reshape(self.h, self.w, 3)
        return img[::-1]
