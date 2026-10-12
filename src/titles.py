"""Coreografía tipográfica: cada letra tiene su propia curva de foco, opacidad
y posición, sincronizada con las notas de la partitura (timeline.HITS)."""
import numpy as np

from timeline import HITS, W
from typography import Atlas, WHITE, OLIVE
from shots import lin, ease_out, ease_in, ease_in_out, smooth


def center_rank(n):
    c = (n - 1) / 2
    order = sorted(range(n), key=lambda i: (abs(i - c), i))
    rank = [0] * n
    for r, i in enumerate(order):
        rank[i] = r // 2 if n % 2 == 0 else (r + 1) // 2
    return rank


class Titles:
    def __init__(self, ctx, logo_shot):
        self.atlas = Atlas()
        A = self.atlas
        cx = W / 2
        # T1 — UNA NUEVA / ESENCIA
        self.t1a = A.layout("UNA NUEVA", "sans", 40, 0.50, cx, 668, OLIVE)
        self.t1b = A.layout("ESENCIA", "didone", 134, 0.10, cx, 832, WHITE)
        # T2 — ESTÁ POR / DESCUBRIRSE
        self.t2a = A.layout("ESTÁ POR", "sans", 40, 0.50, cx, 318, OLIVE)
        self.t2b = A.layout("DESCUBRIRSE", "didone", 96, 0.055, cx, 446, WHITE)
        # T4 — ABRE SUS / PUERTAS
        self.t4a = A.layout("ABRE SUS", "sans", 40, 0.50, cx, 292, OLIVE)
        self.t4b = A.layout("PUERTAS", "didone", 134, 0.11, cx, 452, WHITE)
        # firma bajo el logotipo
        self.tag = A.layout("ABRE SUS PUERTAS", "sans", 30, 0.60, cx, logo_shot.ink_bottom + 118, OLIVE)
        tex = A.build(ctx)
        self.texture = tex

    # ------------------------------------------------------------------
    shadow = 0.0   # opacidad de la sombra suave bajo las letras (legibilidad sobre la luz)

    def emit(self, out, line, i_glyph, op, blur=0.0, dx=0.0, dy=0.0, scale=1.0, pivot=None, clip=-1.0, xmul=1.0):
        g, pen, idx = line.glyphs[i_glyph]
        if op <= 0.002:
            return
        cx = line.cx
        x = cx + (pen - cx) * xmul + dx
        y = line.baseline + dy
        if pivot is None:
            pivot = (cx, line.baseline - line.size * 0.35)
        if self.shadow > 0:
            out.append([x + g.ox, y + g.oy + 2.0, g.w, g.h, g.u0, g.v0, g.u1, g.v1,
                        op * self.shadow, 4.0, scale, clip, 0.0, 0.0, 0.0, pivot[0], pivot[1]])
        out.append([x + g.ox, y + g.oy, g.w, g.h, g.u0, g.v0, g.u1, g.v1,
                    op, blur, scale, clip, line.color[0], line.color[1], line.color[2], pivot[0], pivot[1]])

    def __call__(self, t):
        out = []
        self.shadow = 0.55
        self.t1(t, out)
        self.shadow = 0.0
        self.t2(t, out)
        self.shadow = 0.65
        self.t4(t, out)
        self.shadow = 0.0
        self.tagline(t, out)
        if not out:
            return None
        return np.array(out, dtype=np.float32)

    # ------------------------------------------------------------------
    def t1(self, t, out):
        t0 = HITS["t1_entra"]
        if not (t0 - 0.1 < t < 3.0):
            return
        o0, o1 = 2.42, 2.93
        fo = 1.0 - ease_in(lin(t, o0, o1), 2.0)
        blur_out = 4.0 * ease_in(lin(t, o0, o1), 1.6)
        piv = (W / 2, 760)
        drift = 1.0 + 0.028 * lin(t, t0, 3.0)
        la = self.t1a
        n = len(la.glyphs)
        rk = center_rank(n)
        conv = 1.0 + 0.30 * (1.0 - ease_out(lin(t, t0, t0 + 1.7), 3.0)) + 0.06 * ease_in(lin(t, o0, o1))
        for i in range(n):
            s = t0 + 0.045 * rk[i]
            k = ease_out(lin(t, s, s + 0.75), 2.0)
            self.emit(out, la, i, k * fo, blur=3.2 * (1 - k) + blur_out, xmul=conv, scale=drift, pivot=piv)
        lb = self.t1b
        n = len(lb.glyphs)
        rk = center_rank(n)
        for i in range(n):
            s = t0 + 0.30 + 0.07 * rk[i]
            k = ease_out(lin(t, s, s + 1.0), 2.4)
            rise = 16.0 * (1.0 - ease_out(lin(t, s, s + 1.25), 3.0))
            self.emit(out, lb, i, k * fo, blur=4.5 * (1 - k) + blur_out, dy=rise - 6.0 * ease_in(lin(t, o0, o1)),
                      scale=drift, pivot=piv, xmul=1.0 + 0.03 * ease_in(lin(t, o0, o1)))

    def t2(self, t, out):
        ta, tb = HITS["t2a_entra"], HITS["t2b_entra"]
        if not (ta - 0.1 < t < 6.0):
            return
        o0, o1 = 5.55, 5.95
        fo = 1.0 - ease_in(lin(t, o0, o1), 2.0)
        bo = 5.0 * ease_in(lin(t, o0, o1), 1.5)
        up = -12.0 * ease_in(lin(t, o0, o1), 2.0)
        la = self.t2a
        for i in range(len(la.glyphs)):
            s = ta + 0.04 * i
            k = ease_out(lin(t, s, s + 0.55), 2.2)
            self.emit(out, la, i, k * fo, blur=2.5 * (1 - k) + bo, dx=10.0 * (1 - k), dy=up)
        lb = self.t2b
        clip = lb.baseline + 2.0
        for i in range(len(lb.glyphs)):
            s = tb + 0.045 * i
            k = ease_out(lin(t, s, s + 0.80), 4.0)
            rise = lb.size * 0.95 * (1.0 - k)
            self.emit(out, lb, i, min(1.0, 0.25 + k) * fo, blur=bo, dy=rise + up,
                      clip=clip + up if t < o0 else -1.0)

    def t4(self, t, out):
        ta, tb = HITS["t4a_entra"], HITS["t4b_entra"]
        if not (ta - 0.1 < t < 11.6):
            return
        o0, o1 = 11.05, 11.50
        fo = 1.0 - ease_in(lin(t, o0, o1), 2.0)
        bo = 4.0 * ease_in(lin(t, o0, o1), 1.5)
        sc = 1.0 + 0.05 * ease_in(lin(t, o0, o1), 2.0)
        piv = (W / 2, 380)
        la = self.t4a
        rk = center_rank(len(la.glyphs))
        for i in range(len(la.glyphs)):
            s = ta + 0.05 * rk[i]
            k = ease_out(lin(t, s, s + 0.6), 2.2)
            self.emit(out, la, i, k * fo, blur=3.0 * (1 - k) + bo, scale=sc, pivot=piv)
        lb = self.t4b
        rk = center_rank(len(lb.glyphs))
        # las letras se separan desde el eje, como las hojas de la puerta
        spread = 0.62 + 0.38 * ease_in_out(lin(t, tb, tb + 1.35))
        for i in range(len(lb.glyphs)):
            s = tb + 0.04 * rk[i]
            k = ease_out(lin(t, s, s + 0.7), 2.4)
            self.emit(out, lb, i, k * fo, blur=3.5 * (1 - k) + bo, xmul=spread, scale=sc, pivot=piv)

    def tagline(self, t, out):
        t0 = HITS["firma"]
        if t < t0 - 0.1:
            return
        ln = self.tag
        rk = center_rank(len(ln.glyphs))
        conv = 1.0 + 0.12 * (1.0 - ease_out(lin(t, t0, t0 + 1.6), 3.0))
        for i in range(len(ln.glyphs)):
            s = t0 + 0.035 * rk[i]
            k = ease_out(lin(t, s, s + 0.8), 2.0)
            self.emit(out, ln, i, k, blur=3.0 * (1 - k), xmul=conv)
