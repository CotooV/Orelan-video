"""Activos de marca: logotipo oficial (SVG) o, si no se ha entregado,
composición tipográfica del nombre comercial.

IMPORTANTE: el pipeline busca primero `brand/orelan-logo.svg`. Si existe, se
rasteriza fielmente (sin redibujar, sin alterar proporciones) y se usa como
máscara del cierre. Si no existe, NO se inventa ningún monograma: el cierre
compone únicamente el nombre comercial «ÓRELAN PERFUMERÍA» con la tipografía
de la campaña, y así se documenta en DECISIONES.md.
"""
import io
import os
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

from typography import render_block

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_SVG = os.path.join(ROOT, "brand", "orelan-logo.svg")

SCALE = 2
BOX_W, BOX_H = 780, 560          # caja máxima del logotipo en píxeles de salida
HALO_SIGMAS = (0.0, 6.0, 26.0)


def has_official_logo():
    return os.path.isfile(LOGO_SVG)


def _blur_layers(base):
    out = []
    for s in HALO_SIGMAS:
        out.append(base if s == 0 else gaussian_filter(base, s * SCALE))
    return out


def official_logo_layers():
    import cairosvg
    with open(LOGO_SVG, "rb") as f:
        svg = f.read()
    # rasterizado a alta resolución preservando proporción
    png = cairosvg.svg2png(bytestring=svg, output_width=BOX_W * SCALE * 2)
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    a = np.asarray(im, np.float32)[..., 3] / 255.0
    ys, xs = np.nonzero(a > 0.002)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = a.shape
    k = min(BOX_W * SCALE / w, BOX_H * SCALE / h)
    nw, nh = int(round(w * k)), int(round(h * k))
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    pad = 60 * SCALE
    canvas = np.zeros((nh + 2 * pad, nw + 2 * pad), np.float32)
    canvas[pad:pad + nh, pad:pad + nw] = np.asarray(im, np.float32) / 255.0
    return _blur_layers(canvas), (canvas.shape[1] / SCALE, canvas.shape[0] / SCALE), pad / SCALE


def wordmark_layers():
    """Composición tipográfica del nombre comercial (sin monograma)."""
    W, H = 900, 380
    lines = [
        ("ÓRELAN", "didone", 176, 0.13, W / 2, 220),
        ("PERFUMERÍA", "sans", 31, 0.66, W / 2, 318),
    ]
    layers = render_block(lines, W, H, scale=SCALE, sigmas=HALO_SIGMAS)
    return layers, (W, H), 0.0


def logo_asset():
    """Devuelve (capas float32 [3], (w, h) en px de salida, nombre de origen)."""
    if has_official_logo():
        layers, size, _ = official_logo_layers()
        return layers, size, "svg-oficial"
    layers, size, _ = wordmark_layers()
    return layers, size, "composicion-tipografica"


def ink_bounds(layer0):
    """Límites de tinta (px de salida) dentro del lienzo del logotipo."""
    ys, xs = np.nonzero(layer0 > 0.05)
    return xs.min() / SCALE, ys.min() / SCALE, xs.max() / SCALE, ys.max() / SCALE
