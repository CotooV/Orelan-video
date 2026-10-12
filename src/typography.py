"""Sistema tipográfico de Órelan.

Pareja tipográfica:
  · Bodoni Moda (óptico 96, peso 400): didona de alto contraste, la voz de la
    alta perfumería; para las palabras protagonistas.
  · Jost (peso 300-350): sans geométrica de raíz Futura, muy espaciada; para
    las líneas de apoyo, en verde oliva.

Cada glifo se rasteriza a 2× en un atlas con varios niveles de desenfoque
gaussiano precalculados, para animar foco y opacidad letra a letra sin perder
nitidez.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), "fonts")

FACES = {
    "didone": (os.path.join(FONTS, "BodoniModa-Variable.ttf"), [400, 96]),
    "didone_m": (os.path.join(FONTS, "BodoniModa-Variable.ttf"), [440, 96]),
    "sans": (os.path.join(FONTS, "Jost-Variable.ttf"), [340]),
    "sans_l": (os.path.join(FONTS, "Jost-Variable.ttf"), [300]),
}

SCALE = 2                                  # resolución del atlas respecto a la salida
BLUR_SIGMAS = [0.0, 1.2, 3.0, 6.0, 11.0, 18.0]   # en píxeles de salida
PAD = int(3 * BLUR_SIGMAS[-1] * SCALE) + 4

# Colores de interfaz (sRGB de pantalla, 0..1). La tipografía se compone
# después del tonemapping, así que estos valores son exactos en pantalla.
WHITE = (0.945, 0.930, 0.890)
OLIVE = (0.700, 0.725, 0.505)              # verde oliva claro, legible sobre negro
OLIVE_DEEP = (0.520, 0.545, 0.330)

_font_cache = {}


def font(face, size):
    key = (face, size)
    if key not in _font_cache:
        path, axes = FACES[face]
        f = ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
        f.set_variation_by_axes(axes)
        _font_cache[key] = f
    return _font_cache[key]


class Glyph:
    __slots__ = ("ch", "face", "size", "w", "h", "ox", "oy", "u0", "v0", "u1", "v1", "img")


class Line:
    """Una línea compuesta: posición de cada glifo en píxeles de salida."""

    def __init__(self, text, face, size, tracking, cx, baseline, color):
        self.text, self.face, self.size = text, face, size
        self.tracking, self.cx, self.baseline, self.color = tracking, cx, baseline, color
        self.glyphs = []   # (Glyph, x_pen, index)
        self.width = 0.0
        self.pen = []


class Atlas:
    def __init__(self):
        self.glyphs = {}
        self.texture = None

    def glyph(self, face, size, ch):
        key = (face, size, ch)
        if key in self.glyphs:
            return self.glyphs[key]
        f = font(face, size * SCALE)
        x0, y0, x1, y1 = f.getbbox(ch, anchor="ls")
        w, h = (x1 - x0) + 2 * PAD, (y1 - y0) + 2 * PAD
        img = Image.new("L", (w, h), 0)
        ImageDraw.Draw(img).text((PAD - x0, PAD - y0), ch, font=f, fill=255, anchor="ls")
        g = Glyph()
        g.ch, g.face, g.size = ch, face, size
        g.img = img
        g.w, g.h = w / SCALE, h / SCALE
        g.ox, g.oy = (x0 - PAD) / SCALE, (y0 - PAD) / SCALE   # respecto a pluma/línea base
        self.glyphs[key] = g
        return g

    def layout(self, text, face, size, tracking, cx, baseline, color):
        ln = Line(text, face, size, tracking, cx, baseline, color)
        f = font(face, size * SCALE)
        n = len(text)
        track = tracking * size
        pens = []
        for i in range(n):
            pens.append(f.getlength(text[:i]) / SCALE + i * track)
        width = f.getlength(text) / SCALE + (n - 1) * track
        # centrado óptico: se descuenta el espacio lateral del primer/último glifo
        bx0 = f.getbbox(text[0], anchor="ls")[0] / SCALE
        last = text[-1]
        lb = f.getbbox(last, anchor="ls")
        adv_last = f.getlength(last) / SCALE
        rside = adv_last - lb[2] / SCALE
        ink = width - bx0 - rside
        start = cx - ink / 2 - bx0
        for i, ch in enumerate(text):
            if ch == " ":
                continue
            g = self.glyph(face, size, ch)
            ln.glyphs.append((g, start + pens[i], i))
        ln.width = ink
        ln.start = start
        return ln

    def build(self, ctx):
        """Empaqueta todos los glifos y sube un array de texturas (un nivel de
        desenfoque por capa)."""
        import moderngl
        items = sorted(self.glyphs.values(), key=lambda g: -g.img.size[1])
        maxw = 8192
        x = y = rowh = 0
        places = []
        for g in items:
            w, h = g.img.size
            if x + w > maxw:
                x, y, rowh = 0, y + rowh, 0
            places.append((g, x, y))
            x += w
            rowh = max(rowh, h)
        aw, ah = maxw, y + rowh
        base = np.zeros((ah, aw), np.float32)
        for g, px, py in places:
            w, h = g.img.size
            base[py:py + h, px:px + w] = np.asarray(g.img, np.float32) / 255.0
            g.u0, g.v0, g.u1, g.v1 = px / aw, py / ah, (px + w) / aw, (py + h) / ah
        layers = []
        for s in BLUR_SIGMAS:
            if s == 0:
                layers.append(base)
            else:
                b = gaussian_filter(base, s * SCALE, mode="constant")
                layers.append(b)
        arr = np.stack(layers).astype(np.float32)
        tex = ctx.texture_array((aw, ah, len(layers)), 1, arr.astype(np.float16).tobytes(), dtype="f2")
        tex.build_mipmaps()
        tex.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        tex.anisotropy = 4.0
        self.texture = tex
        self.size = (aw, ah)
        return tex


def render_block(lines, width, height, scale=2, sigmas=(0.0, 4.0, 14.0)):
    """Rasteriza un bloque de líneas a una imagen (para texturas 3D/logotipo).
    lines: [(text, face, size, tracking, cx, baseline)] en píxeles de salida.
    Devuelve una lista de arrays float32 (una por sigma)."""
    img = Image.new("L", (int(width * scale), int(height * scale)), 0)
    d = ImageDraw.Draw(img)
    for text, face, size, tracking, cx, baseline in lines:
        f = font(face, int(size * scale))
        track = tracking * size * scale
        n = len(text)
        width_px = f.getlength(text) + (n - 1) * track
        x0 = f.getbbox(text[0], anchor="ls")[0]
        lb = f.getbbox(text[-1], anchor="ls")
        rside = f.getlength(text[-1]) - lb[2]
        ink = width_px - x0 - rside
        start = cx * scale - ink / 2 - x0
        for i, ch in enumerate(text):
            if ch == " ":
                continue
            px = start + f.getlength(text[:i]) + i * track
            d.text((px, baseline * scale), ch, font=f, fill=255, anchor="ls")
    base = np.asarray(img, np.float32) / 255.0
    out = []
    for s in sigmas:
        out.append(base if s == 0 else gaussian_filter(base, s * scale))
    return out
