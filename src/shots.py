"""Coreografía de los cinco planos: cámaras, luces y eventos, todos anclados
a la rejilla musical de timeline.py."""
import math
import numpy as np
import moderngl

from timeline import SHOTS, HITS, W, H
from typography import render_block
import brand


# ----------------------------------------------------------------------------
# curvas de animación
# ----------------------------------------------------------------------------
def clamp01(x):
    return max(0.0, min(1.0, x))


def lin(t, a, b):
    return clamp01((t - a) / (b - a))


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_in_out(x):
    x = clamp01(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out(x, p=3.0):
    x = clamp01(x)
    return 1 - (1 - x) ** p


def ease_in(x, p=3.0):
    return clamp01(x) ** p


def mix(a, b, k):
    if isinstance(a, (tuple, list)):
        return tuple(ai + (bi - ai) * k for ai, bi in zip(a, b))
    return a + (b - a) * k


class Shot:
    shader = ""
    samples = 12

    def __init__(self, idx):
        self.name, self.start, self.end = SHOTS[idx]

    def samples_at(self, t):
        return self.samples

    def textures(self):
        return []

    def uniforms(self, t):
        return {}

    def post(self, t):
        return {}


# ----------------------------------------------------------------------------
# 1 · UMBRAL — la rendija de luz se enciende en la oscuridad
# ----------------------------------------------------------------------------
class Umbral(Shot):
    shader = "doors.glsl"
    samples = 12

    def uniforms(self, t):
        k = lin(t, 0.0, 3.0)
        m = ease_in_out(k) * 0.55 + k * 0.45
        cam = mix((0.62, 0.30, -3.5), (0.04, 0.52, -2.45), m)
        tgt = mix((0.0, 0.78, 0.0), (0.0, 0.88, 0.0), m)
        ign = lin(t, 0.10, 1.55)
        return dict(uCamPos=cam, uCamTgt=tgt, uRoll=mix(0.018, 0.0, ease_out(k)), uFov=mix(37.0, 34.0, k),
                    uGap=0.0042, uLight=26.0 * smooth(lin(t, 0.0, 0.9)) ** 1.5,
                    uReveal=ease_in_out(ign), uHaze=0.0035, uFill=1.0, uFlood=0.0)

    def post(self, t):
        return dict(bloom=0.30, threshold=1.4, vignette=0.40, grain=0.010,
                    fade=smooth(lin(t, 0.0, 0.35)))


# ----------------------------------------------------------------------------
# 2 · VIDRIO — el monolito conceptual, un barrido de luz en el compás
# ----------------------------------------------------------------------------
class Vidrio(Shot):
    shader = "glass.glsl"
    samples = 16

    def samples_at(self, t):
        # látigo inicial: más submuestras para un desenfoque de movimiento continuo
        return 40 if t - self.start < 0.40 else self.samples

    def uniforms(self, t):
        u = t - self.start
        k = ease_out(u / 2.25, 3.2)
        ang = mix(-1.10, -0.28, k)
        dist = mix(2.0, 3.65, ease_out(u / 2.25, 2.4))
        h = mix(1.85, 1.02, k)
        cam = (dist * math.sin(ang), h, -dist * math.cos(ang))
        tgt = mix((0.05, 1.70, 0.0), (0.0, 1.56, 0.0), k)
        xs = HITS["barrido_luz"] - self.start
        sweep = (u - xs) * 1.25
        sweep_i = 16.0 * math.exp(-((u - xs) / 0.55) ** 2)
        return dict(uCamPos=cam, uCamTgt=tgt, uRoll=mix(0.20, 0.0, k), uFov=mix(33.0, 36.0, k),
                    uSweep=sweep, uSweepI=sweep_i, uKeyI=mix(0.85, 1.0, k))

    def post(self, t):
        return dict(bloom=0.25, threshold=1.6, vignette=0.38, grain=0.010)


# ----------------------------------------------------------------------------
# 3 · LA GOTA — impacto, ondas y el nombre
# ----------------------------------------------------------------------------
class Gota(Shot):
    shader = "liquid.glsl"
    samples = 16
    TITLE_W, TITLE_H = 1000, 380

    def __init__(self, idx, ctx):
        super().__init__(idx)
        TW, TH = self.TITLE_W, self.TITLE_H
        name = render_block([("ÓRELAN", "didone", 150, 0.14, TW / 2, 215)], TW, TH)
        perf = render_block([("PERFUMERÍA", "sans", 34, 0.62, TW / 2, 318)], TW, TH)
        arr = np.stack(name + perf).astype(np.float16)
        self.tex = ctx.texture_array((TW * 2, TH * 2, 6), 1, arr.tobytes(), dtype="f2")
        self.tex.build_mipmaps()
        self.tex.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        self.tex.anisotropy = 8.0

    def textures(self):
        return [("uTitle", self.tex)]

    def uniforms(self, t):
        u = t - self.start
        ti = HITS["impacto_gota"] - self.start          # 0.75
        g = 0.62
        tau = u - ti
        drop_y = 0.0105 * 1.12 + 0.5 * g * max(ti - u, 0.0) ** 2
        # cámara: casi a ras del líquido; tras el impacto, grúa ascendente
        c = ease_in_out(lin(u, ti + 0.10, 3.55))
        cam = mix((0.0, 0.052, -0.50), (0.03, 0.30, -0.80), c)
        cam = (cam[0], cam[1], cam[2] + 0.04 * lin(u, 0.0, ti))
        tgt = mix((0.0, 0.068, 0.0), (0.0, 0.285, 1.0), c)
        fov = mix(30.0, 32.0, c)
        # título
        a0 = HITS["t3a_entra"] - self.start
        b0 = HITS["t3b_entra"] - self.start
        out0, out1 = 3.33, 3.70
        fo = 1.0 - ease_in(lin(u, out0, out1), 2.0)
        name_a = ease_out(lin(u, a0, a0 + 0.55), 2.0) * fo
        name_blur = 2.0 * (1.0 - ease_out(lin(u, a0, a0 + 0.95), 2.4)) + 2.0 * ease_in(lin(u, out0, out1), 2.0)
        reveal = 1.3 * ease_out(lin(u, a0 - 0.05, a0 + 0.9), 2.2)
        perf_a = ease_out(lin(u, b0, b0 + 0.6), 2.0) * fo
        perf_blur = 2.0 * (1.0 - ease_out(lin(u, b0, b0 + 0.8), 2.4)) + 2.0 * ease_in(lin(u, out0, out1), 2.0)
        return dict(uCamPos=cam, uCamTgt=tgt, uRoll=0.0, uFov=fov, uDropY=drop_y, uTau=tau, uKeyI=1.0,
                    uTitleRect=(0.0, 0.43, 0.46, 0.46 * self.TITLE_H / self.TITLE_W), uTitleZ=2.2,
                    uTitleA=(name_a, name_blur, reveal, 2.2), uTitleB=(perf_a, perf_blur, 0.0, 0.0))

    def post(self, t):
        return dict(bloom=0.25, threshold=1.5, vignette=0.38, grain=0.010)


# ----------------------------------------------------------------------------
# 4 · PUERTAS — las hojas se abren, la luz avanza
# ----------------------------------------------------------------------------
class Puertas(Shot):
    shader = "doors.glsl"
    samples = 12

    def gap(self, u):
        return 0.0045 + 0.030 * ease_out(lin(u, 0.0, 0.28), 2.0) + 0.40 * ease_in_out(lin(u, 0.15, 2.95)) ** 1.1

    def uniforms(self, t):
        u = t - self.start
        k = lin(u, 0.0, 3.0)
        mv = 0.55 * k + 0.45 * ease_in(k, 2.6)
        cam = mix((0.0, 1.30, -8.6), (0.0, 1.38, -4.6), mv)
        tgt = mix((0.0, 2.55, 0.0), (0.0, 2.05, 0.0), mv)
        flood = ease_in(lin(u, 2.78, 2.99), 2.0)
        g = self.gap(u)
        haze = 0.0030 * (0.05 / (g + 0.05)) ** 0.75
        return dict(uCamPos=cam, uCamTgt=tgt, uRoll=0.0, uFov=mix(40.0, 37.0, k),
                    uGap=g, uLight=15.0, uReveal=1.0, uHaze=haze, uFill=3.0, uFlood=flood)

    def post(self, t):
        u = t - self.start
        return dict(bloom=0.25 + 0.5 * ease_in(lin(u, 2.6, 3.0), 2.0), threshold=2.0, vignette=0.42,
                    bclamp=1.2 + 12.0 * ease_in(lin(u, 2.5, 3.0), 2.0),
                    grain=0.010, exposure=1.0 + 1.5 * ease_in(lin(u, 2.75, 3.0), 2.5))


# ----------------------------------------------------------------------------
# 5 · REVELACIÓN — la rendija se abre y descubre el logotipo
# ----------------------------------------------------------------------------
class Logo(Shot):
    shader = "logo.glsl"
    samples = 12
    CY = 800.0     # centro vertical del logotipo (px desde arriba)

    def __init__(self, idx, ctx):
        super().__init__(idx)
        layers, (lw, lh), self.source = brand.logo_asset()
        x0, y0, x1, y1 = brand.ink_bounds(layers[0])
        self.lw, self.lh = lw, lh
        self.ink = (x0, y0, x1, y1)
        arr = np.stack(layers).astype(np.float16)
        hh, ww = layers[0].shape
        self.tex = ctx.texture_array((ww, hh, 3), 1, arr.tobytes(), dtype="f2")
        self.tex.build_mipmaps()
        self.tex.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        self.tex.anisotropy = 8.0
        # centro óptico: se centra la tinta, no el lienzo
        ink_cx = (x0 + x1) / 2
        ink_cy = (y0 + y1) / 2
        self.rect_tl = (W / 2 - ink_cx, self.CY - ink_cy)  # esquina sup-izq del lienzo
        self.ink_bottom = self.rect_tl[1] + y1
        self.ink_halfw = (x1 - x0) / 2

    def textures(self):
        return [("uLogo", self.tex)]

    scale = 1.0

    def uniforms(self, t):
        scale = self.scale
        u = t - self.start
        cx = (self.rect_tl[0] + self.lw / 2)
        cy_top = (self.rect_tl[1] + self.lh / 2)
        open_ = (self.ink_halfw + 90.0) * ease_in_out(lin(u, 0.04, 1.05)) ** 0.9
        slit = (1.0 - math.exp(-u / 0.02)) * (0.35 + 0.65 * (1.0 - ease_out(lin(u, 0.0, 1.25), 2.0)))
        slit *= 1.0 - smooth(lin(u, 0.85, 1.35))
        sheen_t = HITS["brillo_logo"] - self.start
        sheen = mix(-700.0, W + 1500.0, ease_in_out(lin(u, sheen_t - 0.55, sheen_t + 0.75)))
        return dict(
            uLogoRect=(cx * scale, (H - cy_top) * scale, self.lw * scale, self.lh * scale),
            uOpen=open_ * scale, uSlitI=slit * 1.3, uSlitH=mix(260.0, 760.0, ease_out(lin(u, 0, 1.0))) * scale,
            uSheen=sheen * scale, uSheenI=0.9, uLogoI=2.15,
            uGlow=smooth(lin(u, 0.2, 1.6)), uPush=1.0 + 0.032 * ease_out(lin(u, 0.0, 3.0), 1.6),
            uReflect=0.0)

    def post(self, t):
        u = t - self.start
        return dict(bloom=0.17, threshold=1.5, vignette=0.42, grain=0.009)


def build_shots(ctx):
    return [Umbral(0), Vidrio(1), Gota(2, ctx), Puertas(3), Logo(4, ctx)]
