"""Banda sonora original de «Umbral» — síntesis pura en numpy/scipy.

Sin samples, sin bibliotecas de sonidos: cada instrumento se construye a
partir de osciladores, ruido filtrado y modelos físicos sencillos.

Forma (80 BPM, 5 compases, re menor → re mayor):
  c.1  Rem(add9)  misterio: dron, cuerdas que nacen del silencio, piano de fieltro
  c.2  Sib(maj7)  golpe + monolito; motivo descendente sobre «ESTÁ POR DESCUBRIRSE»
  c.3  Solm9      la gota: impacto acuático y la firma melódica de ÓRELAN (5ª descendente)
  c.4  La sus4→La7  las puertas: golpe metálico, latido que se acelera, crescendo
  ---- respiro de 150 ms (silencio) ----
  c.5  Re mayor(add9)  revelación: tutti, campanas de cristal, cola larga
"""
import os
import sys
import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import HITS, DURATION, beat  # noqa: E402

SR = 48000
PIANO_GAIN = 1.9
STRINGS_GAIN = 0.62
N = int(round(DURATION * SR))
rng = np.random.default_rng(1307)


def mtof(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def at(t):
    return int(round(t * SR))


class Bus:
    def __init__(self):
        self.x = np.zeros((2, N + SR * 6))

    def add(self, sig, t0, pan=0.0, gain=1.0):
        """sig: mono (n,) o estéreo (2, n); pan -1..1 (ley de potencia constante)."""
        i = at(t0)
        if sig.ndim == 1:
            a = (pan + 1) * np.pi / 4
            sig = np.vstack([sig * np.cos(a), sig * np.sin(a)]) * np.sqrt(2)
        n = sig.shape[1]
        if i < 0:
            sig = sig[:, -i:]
            n = sig.shape[1]
            i = 0
        end = min(i + n, self.x.shape[1])
        self.x[:, i:end] += sig[:, :end - i] * gain


def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def sos_filter(x, kind, f, order=2):
    sos = signal.butter(order, f, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=-1)


# ---------------------------------------------------------------------------
# instrumentos
# ---------------------------------------------------------------------------
def felt_piano(m, dur=4.0, vel=0.8, bright=1.0):
    """Piano de fieltro: parciales inarmónicos, tres cuerdas por nota,
    decaimiento en dos etapas y golpe de macillo apagado."""
    f0 = mtof(m)
    t = tvec(dur)
    out = np.zeros_like(t)
    B = 0.00032
    for n in range(1, 18):
        fn = n * f0 * np.sqrt(1 + B * n * n)
        if fn > 9000:
            break
        amp = vel * (n ** -1.15) * np.exp(-(n - 1) * (0.32 / bright))
        d1 = 1.2 + 0.55 * n
        d2 = 0.25 + 0.06 * n
        env = 0.55 * np.exp(-d1 * t) + 0.45 * np.exp(-d2 * t)
        for k, det in enumerate((-0.7, 0.0, 0.8)):
            ph = rng.uniform(0, 2 * np.pi)
            out += amp / 3 * env * np.sin(2 * np.pi * fn * (1 + det / 1731) * t + ph)
    att = np.minimum(1.0, t / 0.004)
    out *= att
    ham = rng.standard_normal(int(0.03 * SR)) * np.exp(-np.arange(int(0.03 * SR)) / (0.006 * SR))
    ham = sos_filter(ham, "lowpass", min(1400 * bright, 4000))
    out[:len(ham)] += ham * 0.12 * vel
    rel = np.ones_like(t)
    rl = int(0.4 * SR)
    rel[-rl:] = np.linspace(1, 0, rl) ** 2
    return out * rel * 0.5 * PIANO_GAIN


def glass_bell(m, dur=5.0, vel=0.5, index=2.4):
    """Campana de cristal por FM (relación inarmónica 1:3.5) + parcial 2.76."""
    f = mtof(m)
    t = tvec(dur)
    idx = index * np.exp(-t * 2.2) + 0.25
    mod = np.sin(2 * np.pi * f * 3.5 * t)
    car = np.sin(2 * np.pi * f * t + idx * mod)
    car += 0.35 * np.sin(2 * np.pi * f * 2.756 * t) * np.exp(-t * 2.4)
    car += 0.18 * np.sin(2 * np.pi * f * 5.404 * t) * np.exp(-t * 4.0)
    env = np.exp(-t * 0.85) * np.minimum(1.0, t / 0.002)
    return car * env * vel * 0.3


def strings(notes, dur, attack=1.2, release=1.2, vel=0.5, bright=1800.0, voices=6, cresc=None):
    """Sección de cuerdas sintética: síntesis aditiva de diente de sierra con
    envolvente espectral, desafinación de ensamble y vibrato lento. Estéreo."""
    t = tvec(dur)
    L = np.zeros_like(t)
    R = np.zeros_like(t)
    for m in notes:
        f0 = mtof(m)
        for v in range(voices):
            det = (v - (voices - 1) / 2) * 3.2 + rng.normal(0, 1.0)   # cents
            vib_rate = rng.uniform(4.6, 5.6)
            vib = 0.0018 * np.sin(2 * np.pi * vib_rate * t + rng.uniform(0, 6.28)) * np.minimum(1, t / 1.5)
            fv = f0 * 2 ** (det / 1200) * (1 + vib)
            phase = 2 * np.pi * np.cumsum(fv) / SR
            sig = np.zeros_like(t)
            nmax = int(min(40, 7000 / f0))
            for n in range(1, nmax + 1):
                fn = n * f0
                w = (1.0 / n) / (1 + (fn / bright) ** 2)
                # formantes suaves del cuerpo del instrumento
                w *= 1 + 0.6 * np.exp(-((fn - 450) / 220) ** 2) + 0.35 * np.exp(-((fn - 2600) / 700) ** 2)
                sig += w * np.sin(n * phase + rng.uniform(0, 6.28))
            pan = (v / (voices - 1)) * 2 - 1
            a = (pan * 0.8 + 1) * np.pi / 4
            L += sig * np.cos(a)
            R += sig * np.sin(a)
    env = np.minimum(1, t / attack) ** 1.6
    rl = int(release * SR)
    if rl < len(t):
        env[-rl:] *= np.linspace(1, 0, rl) ** 1.5
    if cresc is not None:
        env *= cresc(t)
    norm = vel / (len(notes) * voices) ** 0.5 * 0.12 * STRINGS_GAIN
    return np.vstack([L, R]) * env * norm


def sub_drone(m, dur, vel=0.4, swell=2.0):
    t = tvec(dur)
    f = mtof(m)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t + 0.3)
    s *= 1 + 0.06 * np.sin(2 * np.pi * 0.21 * t)
    env = np.minimum(1, t / swell) ** 2
    rl = int(0.8 * SR)
    env[-rl:] *= np.linspace(1, 0, rl)
    return s * env * vel


def boom(size=1.0, dur=4.0):
    """Golpe cinematográfico: barrido de seno 100→33 Hz, cuerpo saturado,
    transitorio de ruido grave y cola subsónica."""
    t = tvec(dur)
    f = 33 + 70 * np.exp(-t / 0.07)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / (0.9 * size))
    body = np.tanh(body * 2.2) / np.tanh(2.2)
    tail = 0.5 * np.sin(2 * np.pi * 31 * t) * np.exp(-t / (1.6 * size)) * np.minimum(1, t / 0.05)
    n = rng.standard_normal(len(t)) * np.exp(-t / 0.035)
    n = sos_filter(n, "lowpass", 380, 4)
    click = sos_filter(rng.standard_normal(len(t)) * np.exp(-t / 0.006), "bandpass", [900, 4000])
    return (body * 0.9 + tail + n * 1.2 + click * 0.15) * size


def water_drop(vel=0.6):
    """Gota: resonancia de burbuja con chirp ascendente (modelo de Minnaert)."""
    t = tvec(0.35)
    f = 820 * np.exp(t / 0.045)
    f = np.minimum(f, 3400)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t / 0.05) * np.minimum(1, t / 0.0015)
    plop = np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.03) * 0.5
    return (s + plop) * vel


def metal_thunk(vel=0.8):
    """Cierre metálico pesado: síntesis modal (resonancias inarmónicas)."""
    t = tvec(3.0)
    exc = rng.standard_normal(len(t)) * np.exp(-t / 0.004)
    out = np.zeros_like(t)
    for f, d, a in [(58, 1.5, 1.0), (139, 1.1, 0.6), (231, 0.8, 0.45), (367, 0.55, 0.35),
                    (521, 0.45, 0.25), (797, 0.3, 0.18), (1187, 0.22, 0.12), (1741, 0.15, 0.08)]:
        out += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) * np.exp(-t / d)
    out *= np.minimum(1, t / 0.0015)
    out += sos_filter(exc, "lowpass", 2500) * 0.4
    return out * vel * 0.6


def heartbeat(vel=0.5):
    t = tvec(0.5)
    f = 48 + 60 * np.exp(-t / 0.03)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / 0.14) * vel


def noise_sweep(dur, f0, f1, q=0.35, curve=2.0, vel=0.3):
    """Ruido con filtro de banda móvil (STFT): ‘riser’/‘aire’."""
    n = int(dur * SR)
    x = rng.standard_normal(n + 4096)
    f, tt, Z = signal.stft(x, SR, nperseg=2048, noverlap=1536)
    prog = np.clip(tt / dur, 0, 1) ** curve
    fc = f0 * (f1 / f0) ** prog
    bw = fc * q
    mask = np.exp(-((f[:, None] - fc[None, :]) / bw[None, :]) ** 2)
    _, y = signal.istft(Z * mask, SR, nperseg=2048, noverlap=1536)
    y = y[:n]
    return y / (np.abs(y).max() + 1e-9) * vel


def tone_riser(m0, m1, dur, vel=0.2):
    t = tvec(dur)
    k = (t / dur) ** 2.2
    f = mtof(m0) * 2 ** ((m1 - m0) * k / 12)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + 0.4 * np.sin(2 * ph + 0.5) + 0.2 * np.sin(3 * ph)
    return s * (t / dur) ** 2.5 * vel


# ---------------------------------------------------------------------------
# reverberación por convolución (respuesta al impulso sintética)
# ---------------------------------------------------------------------------
def make_ir(rt_low=3.6, rt_mid=3.0, rt_high=1.8, length=5.0, predelay=0.022, seed=5):
    r = np.random.default_rng(seed)
    t = tvec(length)
    ir = np.zeros((2, len(t)))
    for ch in range(2):
        nz = r.standard_normal(len(t))
        lo = sos_filter(nz, "lowpass", 400) * np.exp(-6.91 * t / rt_low)
        mi = sos_filter(nz, "bandpass", [400, 3500]) * np.exp(-6.91 * t / rt_mid)
        hi = sos_filter(nz, "highpass", 3500) * np.exp(-6.91 * t / rt_high)
        ir[ch] = lo + mi + 0.7 * hi
        ir[ch] *= np.minimum(1, t / 0.08) ** 0.6           # difusión gradual
        for d, a in [(0.011, 0.5), (0.019, 0.35), (0.027, 0.3), (0.041, 0.22), (0.057, 0.16)]:
            i = at(d + 0.003 * ch)
            ir[ch, i] += a * (1 if r.random() > 0.5 else -1) * 3
    pd = at(predelay)
    ir = np.concatenate([np.zeros((2, pd)), ir], axis=1)
    ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
    return ir


def reverb(x, ir, wet=0.3):
    y = np.vstack([signal.fftconvolve(x[c], ir[c])[:x.shape[1]] for c in range(2)])
    return y * wet


# ---------------------------------------------------------------------------
# composición
# ---------------------------------------------------------------------------
def compose():
    mus = Bus()      # piano, cuerdas, campanas → reverb larga
    fx = Bus()       # golpes, risers → reverb corta
    dry = Bus()      # sub y transitorios secos
    swell = Bus()    # material que se invierte (reverse swells)

    H = HITS
    # ---- compás 1: Rem(add9) ------------------------------------------------
    dry.add(sub_drone(26, 3.2, vel=0.20, swell=1.6), 0.0)
    dry.add(sub_drone(38, 3.1, vel=0.12, swell=1.2), 0.0)
    mus.add(strings([50, 57, 64, 65], 3.4, attack=1.6, release=0.9, vel=0.42, bright=1100), 0.0)
    air = noise_sweep(3.0, 2500, 6000, q=0.5, curve=1.0, vel=0.025)
    fx.add(air * np.minimum(1, tvec(3.0) / 1.5), 0.0)
    mus.add(felt_piano(69, 3.5, 0.55), H["t1_entra"], pan=-0.1)
    mus.add(glass_bell(81, 4.0, 0.16), H["t1_entra"], pan=0.3)
    mus.add(felt_piano(74, 3.0, 0.45), beat(1.5), pan=0.0)
    mus.add(felt_piano(76, 3.0, 0.50), beat(2), pan=0.1)
    mus.add(felt_piano(77, 3.0, 0.42), beat(3), pan=0.15)
    mus.add(felt_piano(62, 3.0, 0.30), beat(3), pan=-0.2)

    # ---- compás 2: Sib(maj7) -------------------------------------------------
    t2 = H["corte_vidrio"]
    dry.add(boom(0.75, 3.5), t2, gain=0.85)
    dry.add(sub_drone(22, 3.0, vel=0.16, swell=0.05), t2)        # Sib0
    mus.add(strings([46, 53, 57, 62], 3.3, attack=0.25, release=0.8, vel=0.50, bright=1400), t2)
    mus.add(glass_bell(86, 4.0, 0.22), t2, pan=-0.3)
    mus.add(felt_piano(77, 3.0, 0.62), H["t2a_entra"], pan=0.1)      # ESTÁ POR
    mus.add(felt_piano(76, 3.0, 0.62), H["t2b_entra"], pan=0.0)      # DESCUBRIRSE
    mus.add(felt_piano(57, 3.0, 0.40), H["t2b_entra"], pan=-0.25)
    mus.add(glass_bell(88, 2.5, 0.10), H["t2b_entra"], pan=0.35)
    mus.add(felt_piano(74, 3.0, 0.52), H["barrido_luz"], pan=-0.1)
    mus.add(glass_bell(93, 3.0, 0.12), H["barrido_luz"], pan=0.4)
    mus.add(felt_piano(69, 3.0, 0.40), beat(6.5), pan=-0.15)
    mus.add(glass_bell(93, 3.0, 0.18), H["corte_gota"], pan=0.25)  # destello de corte
    # absorción hacia el impacto
    sw = strings([55, 62, 70], 1.0, attack=0.02, release=0.6, vel=0.7, bright=2500)
    swell.add(sw, H["impacto_gota"] - 0.0)

    # ---- compás 3: Solm9 ------------------------------------------------------
    t3 = H["impacto_gota"]
    fx.add(water_drop(0.75), t3, pan=0.0)
    dry.add(boom(0.95, 3.8), t3, gain=0.9)
    dry.add(sub_drone(31, 3.2, vel=0.16, swell=0.05), t3)       # Sol1
    mus.add(strings([43, 50, 58, 65, 69], 3.3, attack=0.4, release=0.9, vel=0.50, bright=1500), t3)
    mus.add(felt_piano(74, 3.0, 0.62), H["t3a_entra"], pan=0.0)       # Ó-RE-LAN: 5ª descendente
    mus.add(felt_piano(62, 3.0, 0.35), H["t3a_entra"], pan=-0.2)
    mus.add(glass_bell(86, 3.5, 0.15), H["t3a_entra"], pan=0.3)
    mus.add(felt_piano(69, 3.0, 0.58), H["t3b_entra"], pan=0.05)      # PERFUMERÍA
    mus.add(felt_piano(70, 2.5, 0.40), beat(10.5), pan=-0.05)
    mus.add(felt_piano(69, 2.5, 0.38), beat(11), pan=0.05)
    fx.add(noise_sweep(1.0, 300, 5000, q=0.3, curve=2.0, vel=0.10), H["puertas"] - 1.0)
    swell.add(boom(0.6, 1.0) * 0.4, H["puertas"])
    swell.add(strings([57, 64, 69], 1.0, attack=0.02, release=0.6, vel=0.6, bright=2500), H["puertas"])

    # ---- compás 4: La sus4 → La7 ----------------------------------------------
    t4 = H["puertas"]
    fx.add(metal_thunk(0.85), t4, pan=0.0)
    dry.add(boom(1.0, 3.5), t4, gain=0.85)
    dry.add(sub_drone(33, 2.9, vel=0.20, swell=0.05), t4)       # La1
    cres = lambda t: 0.55 + 0.45 * (t / 2.85) ** 1.5
    mus.add(strings([45, 52, 62, 64], 1.55, attack=0.3, release=0.25, vel=0.62, bright=1700, cresc=cres), t4)
    mus.add(strings([45, 52, 61, 64, 67], 1.35, attack=0.25, release=0.05, vel=0.75, bright=2600,
                    cresc=lambda t: 0.75 + 0.55 * (t / 1.35) ** 2), beat(14))
    mus.add(felt_piano(76, 2.5, 0.60), H["t4a_entra"], pan=0.1)   # ABRE SUS
    mus.add(felt_piano(74, 2.5, 0.66), H["t4b_entra"], pan=-0.05)  # PUERTAS
    mus.add(felt_piano(62, 2.5, 0.42), H["t4b_entra"], pan=0.2)
    mus.add(glass_bell(86, 2.5, 0.10), H["t4b_entra"], pan=-0.35)
    mus.add(felt_piano(73, 2.0, 0.55), beat(14), pan=0.0)         # sensible: tensión
    mus.add(felt_piano(76, 1.5, 0.45), beat(15), pan=0.1)
    # latido que se acelera
    for tb, v in [(beat(12), 0.55), (beat(13), 0.5), (beat(14), 0.6), (beat(14.5), 0.55),
                  (beat(15), 0.7), (beat(15.5), 0.75), (beat(15.75), 0.8)]:
        dry.add(heartbeat(v), tb)
    # deslizamiento de las hojas: rumor grave
    rum = sos_filter(rng.standard_normal(int(2.85 * SR)), "lowpass", 140, 4)
    rum *= np.minimum(1, tvec(2.85) / 0.6) * (0.4 + 0.6 * tvec(2.85) / 2.85)
    fx.add(rum / np.abs(rum).max() * 0.20, t4 + 0.2)
    # riser final
    rdur = H["respiro"] - (t4 + 0.8)
    fx.add(noise_sweep(rdur, 250, 9000, q=0.28, curve=2.4, vel=0.20), t4 + 0.8, pan=0.0)
    mus.add(tone_riser(57, 69, rdur, vel=0.10), t4 + 0.8, pan=-0.3)
    mus.add(tone_riser(64, 76, rdur, vel=0.08), t4 + 0.8, pan=0.3)
    swell.add(strings([50, 57, 62, 66], 1.4, attack=0.01, release=0.8, vel=0.8, bright=3000), H["logo"])
    swell.add(np.vstack([glass_bell(86, 2.0, 0.6)] * 2), H["logo"])

    # ---- compás 5: Re mayor(add9) — revelación ---------------------------------
    t5 = H["logo"]
    dry.add(boom(1.45, 4.0), t5, gain=1.15)
    dry.add(sub_drone(26, 3.6, vel=0.34, swell=0.03), t5)
    dry.add(sub_drone(38, 3.4, vel=0.14, swell=0.03), t5)
    mus.add(strings([38, 50, 57, 62, 66, 69, 76], 3.6, attack=0.06, release=2.2, vel=1.45, bright=2600), t5)
    for m, d, v, p in [(50, 0.0, 0.55, -0.3), (57, 0.012, 0.5, -0.1), (66, 0.024, 0.5, 0.1),
                       (69, 0.036, 0.5, 0.2), (74, 0.05, 0.6, 0.0)]:
        mus.add(felt_piano(m, 3.5, v, bright=1.3), t5 + d, pan=p)
    for m, d, v, p in [(86, 0.0, 0.30, -0.4), (93, 0.09, 0.22, 0.4), (90, 0.19, 0.20, -0.1),
                       (100, 0.31, 0.12, 0.2), (98, 0.47, 0.10, -0.25)]:
        mus.add(glass_bell(m, 4.0, v, index=2.8), t5 + d, pan=p)
    mus.add(felt_piano(78, 2.6, 0.90, bright=1.3), H["firma"], pan=0.1)     # firma: fa# (3ª mayor)
    mus.add(felt_piano(66, 2.6, 0.50), H["firma"], pan=-0.15)
    mus.add(glass_bell(90, 2.6, 0.26), H["firma"], pan=-0.25)
    mus.add(glass_bell(93, 2.0, 0.30, index=3.2), H["brillo_logo"], pan=0.35)   # destello
    mus.add(glass_bell(98, 1.8, 0.16), H["brillo_logo"] + 0.11, pan=-0.35)
    return mus, fx, dry, swell


def master(mus, fx, dry, swell):
    ir_long = make_ir(3.8, 3.2, 2.0, 5.5)
    ir_short = make_ir(1.6, 1.3, 0.8, 2.5, seed=9)

    def cut(b):
        return b.x[:, :N + SR * 6]

    m = cut(mus)
    out = m * 0.80 + reverb(m, ir_long, 0.55)
    f = cut(fx)
    out += f * 0.9 + reverb(f, ir_short, 0.35)
    d = cut(dry)
    out += d + reverb(d, ir_short, 0.10)

    # reverse swells: cada evento se reverbera, se invierte y desemboca en su golpe
    s = cut(swell)
    for hit in (HITS["impacto_gota"], HITS["puertas"], HITS["logo"]):
        i = at(hit)
        seg = np.zeros_like(s)
        seg[:, i:i + int(1.6 * SR)] = s[:, i:i + int(1.6 * SR)]
        if not np.any(seg):
            continue
        wet = reverb(seg[:, i:i + int(1.6 * SR)], ir_long, 1.0)
        tail = np.concatenate([seg[:, i:i + int(1.6 * SR)] * 0.2 + wet, np.zeros((2, SR * 3))], axis=1)
        L = int(1.2 * SR) if hit != HITS["logo"] else int(1.5 * SR)
        rev = tail[:, :L][:, ::-1]
        rev *= np.linspace(0, 1, L) ** 2.2
        gain = 0.6 if hit != HITS["logo"] else 0.8
        out[:, i - L:i] += rev * gain

    # respiro: silencio súbito antes de la revelación
    r0, r1 = at(HITS["respiro"]), at(HITS["logo"])
    g = np.ones(out.shape[1])
    fade = int(0.012 * SR)
    g[r0 - fade:r0] = np.linspace(1, 0.04, fade)
    g[r0:r1] = 0.04
    out *= g

    out = out[:, :N]
    out = sos_filter(out, "highpass", 24, 2)
    # compresión de bus suave (RMS, 3:1 por encima del umbral)
    env = np.sqrt(signal.lfilter([1 - np.exp(-1 / (0.03 * SR))], [1, -np.exp(-1 / (0.03 * SR))],
                                 (out ** 2).mean(axis=0)))
    thr = 0.22
    gr = np.where(env > thr, (thr * (env / thr) ** (1 / 2)) / np.maximum(env, 1e-9), 1.0)
    out *= gr
    return out


def limiter(x, ceiling):
    peak = np.abs(x).max(axis=0)
    look = int(0.004 * SR)
    from scipy.ndimage import maximum_filter1d, uniform_filter1d
    pk = maximum_filter1d(peak, size=2 * look + 1)
    g = np.minimum(1.0, ceiling / np.maximum(pk, 1e-9))
    g = uniform_filter1d(g, size=look)
    g = np.minimum(g, np.minimum(1.0, ceiling / np.maximum(maximum_filter1d(peak, size=3), 1e-9)))
    return x * g


def true_peak(x):
    up = signal.resample_poly(x, 4, 1, axis=1)
    return np.abs(up).max()


def render(path, target_lufs=-14.0):
    import pyloudnorm as pyln
    from scipy.io import wavfile
    out = master(*compose())
    meter = pyln.Meter(SR)
    for _ in range(4):
        lufs = meter.integrated_loudness(out.T)
        out *= 10 ** ((target_lufs - lufs) / 20)
        out = limiter(out, 10 ** (-1.5 / 20))
    # micro fundido final para un cierre limpio
    fl = int(0.35 * SR)
    out[:, -fl:] *= np.linspace(1, 0, fl) ** 1.5
    lufs = meter.integrated_loudness(out.T)
    tp = 20 * np.log10(true_peak(out))
    wavfile.write(path, SR, out.T.astype(np.float32))
    return lufs, tp


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "build/music.wav"
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    lufs, tp = render(p)
    print(f"{p}: {N / SR:.3f}s  {lufs:.1f} LUFS  true-peak {tp:.2f} dBTP")
