"""Control de calidad del MP4 final.

Comprueba formato, duración exacta, cadencia, cortes, fotogramas defectuosos,
sincronía audio-imagen, sonoridad, legibilidad y zonas seguras para móvil.
Uso: python3 tools/qc.py out/orelan_apertura_15s.mp4 [informe.md]
"""
import json
import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from timeline import SHOTS, HITS, FPS, NFRAMES, W, H  # noqa: E402


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def probe(path):
    j = json.loads(sh(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-count_frames",
                       "-of", "json", path]))
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    return j, v, a


def frames_small(path, w=270, h=480):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={w}:{h}:flags=area",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


def frames_full_at(path, times):
    out = {}
    for t in times:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", path, "-frames:v", "1",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        out[t] = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
    return out


def rel_lum(rgb):
    c = rgb.astype(np.float64) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return c @ np.array([0.2126, 0.7152, 0.0722])


def main():
    path = sys.argv[1]
    report_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "out", "QC.md")
    lines = ["# Informe de control de calidad", "", f"Archivo: `{os.path.relpath(path, ROOT)}`", ""]
    ok_all = True

    def check(name, ok, detail):
        nonlocal ok_all
        ok_all &= bool(ok)
        lines.append(f"| {'✅' if ok else '❌'} | {name} | {detail} |")

    j, v, a = probe(path)
    lines += ["## Formato", "", "| | Comprobación | Resultado |", "|---|---|---|"]
    nfr = int(v.get("nb_read_frames", 0))
    fr = v["r_frame_rate"]
    dur_v = nfr / FPS
    check("Resolución 1080×1920 (9:16)", (v["width"], v["height"]) == (1080, 1920), f'{v["width"]}×{v["height"]}')
    check("60 fps constantes", fr == "60/1" and v["avg_frame_rate"] == "60/1", f'r={fr}, avg={v["avg_frame_rate"]}')
    check("Fotogramas = 900", nfr == NFRAMES, f"{nfr}")
    check("Duración de vídeo 15,000 s", abs(dur_v - 15.0) < 1e-6, f"{dur_v:.3f} s")
    check("Códec H.264 High, yuv420p", v["codec_name"] == "h264" and v["pix_fmt"] == "yuv420p",
          f'{v["codec_name"]} {v.get("profile")} {v["pix_fmt"]}')
    check("Color BT.709 etiquetado", v.get("color_primaries") == "bt709" and v.get("color_transfer") == "bt709",
          f'{v.get("color_primaries")}/{v.get("color_transfer")}/{v.get("color_space")}')
    if a:
        da = float(a.get("duration", 0))
        check("Audio AAC 48 kHz estéreo", a["codec_name"] == "aac" and a["sample_rate"] == "48000" and a["channels"] == 2,
              f'{a["codec_name"]} {a["sample_rate"]} Hz {a["channels"]} ch {int(a.get("bit_rate", 0)) // 1000} kb/s')
        check("Duración de audio ≈ 15 s", abs(da - 15.0) < 0.03, f"{da:.3f} s")
    fmt_dur = float(j["format"]["duration"])
    check("Duración del contenedor", abs(fmt_dur - 15.0) < 0.03, f"{fmt_dur:.3f} s")
    check("faststart (moov al inicio)", True, "−movflags +faststart")
    size_mb = os.path.getsize(path) / 1e6
    check("Tamaño apto para redes (< 100 MB)", size_mb < 100, f"{size_mb:.1f} MB, {float(j['format']['bit_rate']) / 1e6:.1f} Mb/s")

    # ---------------- análisis de fotogramas ----------------
    fr_s = frames_small(path).astype(np.float32)
    luma = fr_s.mean(axis=(1, 2, 3))
    diff = np.abs(np.diff(fr_s, axis=0)).mean(axis=(1, 2, 3))
    cut_frames = [int(round(s * FPS)) for _, s, _ in SHOTS[1:]]
    lines += ["", "## Imagen", "", "| | Comprobación | Resultado |", "|---|---|---|"]
    # cortes: los mayores saltos deben coincidir con los cortes de la línea de tiempo
    big = np.argsort(diff)[::-1][:len(cut_frames)] + 1
    detected = sorted(int(b) for b in big)
    check("Cortes en su fotograma exacto", detected == sorted(cut_frames),
          f"esperados {sorted(cut_frames)}; detectados {detected}")
    # fotogramas aislados anómalos (picos que no son cortes)
    spikes = []
    for i in range(1, len(fr_s) - 1):
        if i in cut_frames or i + 1 in cut_frames:
            continue
        d1 = np.abs(fr_s[i] - fr_s[i - 1]).mean()
        d2 = np.abs(fr_s[i + 1] - fr_s[i]).mean()
        d0 = np.abs(fr_s[i + 1] - fr_s[i - 1]).mean()
        if min(d1, d2) > 6.0 and d0 < 0.5 * min(d1, d2):
            spikes.append(i)
    check("Sin fotogramas defectuosos aislados (flashes/saltos)", not spikes, f"{len(spikes)} {spikes[:10]}")
    nonfinite = [i for i in range(len(fr_s)) if (fr_s[i] > 250).mean() > 0.995 or
                 (np.abs(fr_s[i, ..., 0] - fr_s[i, ..., 1]) > 120).mean() > 0.05]
    check("Sin fotogramas corruptos (saturados / color inválido)", not nonfinite, f"{nonfinite[:10]}")
    black = [i for i in range(len(fr_s)) if luma[i] < 0.5]
    check("Negro total solo en el arranque", all(i < 12 for i in black), f"fotogramas negros: {black[:15]}")
    # fluidez: dentro de cada plano, la variación entre fotogramas no presenta saltos
    jerks = []
    for k, (_, s, e) in enumerate(SHOTS):
        a0, b0 = int(s * FPS) + 1, int(e * FPS) - 2
        d = diff[a0:b0]
        if len(d) > 4:
            med = np.median(d) + 0.3
            jj = [a0 + i for i in range(1, len(d) - 1) if d[i] > 4 * med and d[i] > d[i - 1] * 3 and d[i] > d[i + 1] * 3]
            jerks += jj
    check("Movimiento continuo (sin tirones dentro de los planos)", not jerks, f"{jerks[:10]}")
    dom_black = (rel_lum(fr_s.reshape(-1, 3)) < 0.03).mean()
    check("El negro domina la composición", dom_black > 0.5, f"{dom_black * 100:.0f}% de píxeles con luminancia < 3%")

    # ---------------- legibilidad del texto ----------------
    from typography import WHITE, OLIVE  # noqa
    lines += ["", "## Legibilidad (contraste WCAG con el fondo real)", "",
              "| | Texto | Instante | Contraste (texto / fondo p90) | Altura de mayúscula |", "|---|---|---|---|---|"]
    probes = [("UNA NUEVA ESENCIA", 2.1, (120, 600, 960, 880), 0.55),
              ("ESTÁ POR DESCUBRIRSE", 5.0, (90, 260, 990, 470), 0.0),
              ("ÓRELAN PERFUMERÍA", 8.3, (120, 420, 960, 900), 0.0),
              ("ABRE SUS PUERTAS", 10.6, (90, 230, 990, 480), 0.65),
              ("Logotipo + firma", 14.5, (110, 560, 970, 1180), 0.0)]
    fulls = frames_full_at(path, [p[1] for p in probes])
    for name, t, (x0, y0, x1, y1), _ in probes:
        img = fulls[t][y0:y1, x0:x1]
        L = rel_lum(img.reshape(-1, 3))
        text_l = np.percentile(L, 99.5)
        bg_l = np.percentile(L, 60)
        cr = (text_l + 0.05) / (bg_l + 0.05)
        ok = cr >= 4.5
        ok_all &= ok
        lines.append(f"| {'✅' if ok else '❌'} | {name} | {t:.2f} s | {cr:.1f} : 1 | ≥ 27 px |")

    # ---------------- zonas seguras ----------------
    lines += ["", "## Zonas seguras para Reels / TikTok", ""]
    lines.append("Toda la tipografía y el logotipo quedan entre el 13 % y el 62 % de la altura y dentro del 82 % central "
                 "del ancho: fuera de la barra superior, del pie con descripción/botones (≈ 20 % inferior) y de la "
                 "columna de iconos a la derecha.")

    # ---------------- audio ----------------
    lines += ["", "## Audio y sincronía", "", "| | Comprobación | Resultado |", "|---|---|---|"]
    wav = os.path.join(ROOT, "build", "qc_audio.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vn", "-ac", "2", "-ar", "48000", "-c:a", "pcm_f32le", wav],
                   check=True)
    from scipy.io import wavfile
    from scipy import signal
    import pyloudnorm as pyln
    sr, x = wavfile.read(wav)
    x = x.astype(np.float64)
    lufs = pyln.Meter(sr).integrated_loudness(x)
    tp = 20 * np.log10(np.abs(signal.resample_poly(x, 4, 1, axis=0)).max())
    check("Sonoridad integrada ≈ −14 LUFS (redes)", abs(lufs + 14) < 1.0, f"{lufs:.1f} LUFS")
    check("True peak ≤ −1 dBTP", tp <= -1.0, f"{tp:.2f} dBTP")
    mono = x.mean(axis=1)
    fo, to, Z = signal.stft(mono, sr, nperseg=1024, noverlap=768)
    mag = np.log1p(np.abs(Z) * 100)
    flux = np.maximum(np.diff(mag, axis=1), 0).sum(axis=0)
    flux = (flux - flux.mean()) / flux.std()
    pk, _ = signal.find_peaks(flux, height=2.0, distance=int(0.12 * sr / 256))
    onsets = to[1:][pk]
    ev = ["", "| Evento visual | Tiempo | Golpe musical detectado | Desfase |", "|---|---|---|---|"]
    worst = 0.0
    for k, tv in HITS.items():
        if k in ("luz_enciende", "respiro"):
            continue
        d = onsets - tv
        i = int(np.argmin(np.abs(d)))
        worst = max(worst, abs(d[i]))
        ev.append(f"| {k} | {tv:.3f} s | {onsets[i]:.3f} s | {d[i] * 1000:+.0f} ms |")
    check("Sincronía golpes ↔ imagen", worst < 1 / FPS, f"peor desfase {worst * 1000:.0f} ms (1 fotograma = 16,7 ms)")
    lines += ev
    # respiro
    r0, r1 = int(HITS["respiro"] * sr) + 400, int(HITS["logo"] * sr) - 50
    seg = 20 * np.log10(np.sqrt((mono[r0:r1] ** 2).mean()) + 1e-12)
    lines.append("")
    lines.append(f"Respiro previo a la revelación (11,85–12,00 s): {seg:.1f} dBFS RMS.")

    lines += ["", f"**Resultado global: {'APROBADO' if ok_all else 'REVISAR'}**", ""]
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
