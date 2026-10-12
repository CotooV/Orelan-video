"""Línea de tiempo maestra de «Umbral» — Órelan Perfumería, 15 s.

Todo el anuncio (imagen y música) se deriva de esta única tabla, de modo que
cada corte, aparición tipográfica y golpe musical comparten el mismo reloj.

Tempo: 80 BPM -> 1 tiempo = 0,75 s = 45 fotogramas exactos a 60 fps.
5 compases de 4/4 = 20 tiempos = 15,000 s = 900 fotogramas.
"""

W, H = 1080, 1920
FPS = 60
DURATION = 15.0
NFRAMES = int(round(DURATION * FPS))  # 900

BPM = 80.0
BEAT = 60.0 / BPM  # 0.75 s


def beat(n: float) -> float:
    """Tiempo absoluto (s) del tiempo musical n (0 = inicio)."""
    return n * BEAT


# ---------------------------------------------------------------------------
# Planos (cortes secos; el motion blur nunca cruza estos límites)
# ---------------------------------------------------------------------------
SHOTS = [
    # nombre,     inicio,     fin
    ("umbral",   beat(0),    beat(4)),     # 0.00 – 3.00  la grieta de luz
    ("vidrio",   beat(4),    beat(7)),     # 3.00 – 5.25  monolito de vidrio
    ("gota",     beat(7),    beat(12)),    # 5.25 – 9.00  la gota / el nombre
    ("puertas",  beat(12),   beat(16)),    # 9.00 – 12.00 las puertas se abren
    ("logo",     beat(16),   DURATION),    # 12.00 – 15.00 revelación final
]

# ---------------------------------------------------------------------------
# Golpes musicales clave (s). La música y la imagen leen de aquí.
# ---------------------------------------------------------------------------
HITS = {
    "luz_enciende":   beat(0),      # la grieta empieza a respirar
    "t1_entra":       beat(1),      # UNA NUEVA ESENCIA
    "corte_vidrio":   beat(4),      # golpe 1 + corte
    "t2a_entra":      beat(5),      # ESTÁ POR
    "t2b_entra":      beat(5.5),    # DESCUBRIRSE
    "barrido_luz":    beat(6),      # barrido de luz sobre el vidrio
    "corte_gota":     beat(7),      # destello: la gota cae
    "impacto_gota":   beat(8),      # golpe 2: impacto + ondas
    "t3a_entra":      beat(8.5),    # ÓRELAN
    "t3b_entra":      beat(9.5),    # PERFUMERÍA
    "puertas":        beat(12),     # golpe 3: las puertas empiezan a abrirse
    "t4a_entra":      beat(12.5),   # ABRE SUS
    "t4b_entra":      beat(13),     # PUERTAS
    "respiro":        beat(16) - 0.15,  # silencio antes de la revelación
    "logo":           beat(16),     # golpe final: revelación del logotipo
    "firma":          beat(17.5),   # línea «ABRE SUS PUERTAS» bajo el logo
    "brillo_logo":    beat(18.5),   # segundo destello sobre el logotipo
}


def shot_at(t: float):
    for i, (name, a, b) in enumerate(SHOTS):
        if a <= t < b:
            return i, name, a, b
    name, a, b = SHOTS[-1]
    return len(SHOTS) - 1, name, a, b


# Obturador cinematográfico de 180°: cada fotograma integra medio intervalo.
SHUTTER = 0.5
