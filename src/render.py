"""Render del anuncio «Umbral» — Órelan Perfumería.

Uso:
  python3 src/render.py --out out/video.mp4 [--audio build/music.wav]
  python3 src/render.py --stills 1.5,4.5 --scale 0.5     (fotogramas sueltos)
  python3 src/render.py --scale 0.5 --samples 3 --out build/preview.mp4
Requiere un contexto OpenGL 3.3 (en servidores: xvfb-run).
"""
import argparse
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from timeline import W, H, FPS, NFRAMES, shot_at  # noqa: E402
from engine import Engine  # noqa: E402
from shots import build_shots  # noqa: E402
from titles import Titles  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--samples", type=int, default=0, help="forzar submuestras por fotograma")
    ap.add_argument("--frames", default="", help="rango a:b de fotogramas")
    ap.add_argument("--stills", default="", help="tiempos (s) separados por comas")
    ap.add_argument("--stills-dir", default="build/stills")
    ap.add_argument("--out", default="")
    ap.add_argument("--audio", default="")
    ap.add_argument("--crf", type=int, default=12)
    args = ap.parse_args()

    w, h = int(round(W * args.scale)) // 2 * 2, int(round(H * args.scale)) // 2 * 2
    eng = Engine(w, h)
    shots = build_shots(eng.ctx)
    for s in shots:
        s.scale = w / W
    titles = Titles(eng.ctx, shots[-1])
    eng.atlas = titles.texture
    print(f"logotipo: {shots[-1].source}", flush=True)

    def render(frame):
        t = frame / FPS
        i, _, _, _ = shot_at(t + 1e-9)
        shot = shots[i]
        n = args.samples or shot.samples_at(t)
        return eng.render_frame(frame, shot, n, overlay=titles, post=shot.post(t))

    if args.stills:
        os.makedirs(args.stills_dir, exist_ok=True)
        for ts in args.stills.split(","):
            f = int(round(float(ts) * FPS))
            t0 = time.time()
            img = render(f)
            p = os.path.join(args.stills_dir, f"f{f:04d}.png")
            Image.fromarray(img).save(p)
            print(f"{p}  {time.time() - t0:.2f}s", flush=True)
        return

    a, b = 0, NFRAMES
    if args.frames:
        a, b = (int(x) for x in args.frames.split(":"))
    out = args.out or "build/render.mp4"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-"]
    if args.audio:
        cmd += ["-i", args.audio]
    cmd += ["-map", "0:v"]
    if args.audio:
        cmd += ["-map", "1:a", "-c:a", "aac", "-b:a", "320k", "-ar", "48000"]
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", str(args.crf), "-tune", "film",
            "-profile:v", "high", "-level", "4.2", "-pix_fmt", "yuv420p",
            "-vf", "scale=out_color_matrix=bt709:out_range=tv",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
            "-x264-params", "keyint=60:min-keyint=60:aq-mode=3:deblock=-1,-1",
            "-r", str(FPS), "-frames:v", str(b - a), "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t_start = time.time()
    for f in range(a, b):
        img = render(f)
        proc.stdin.write(img.tobytes())
        if f % 30 == 0 or f == b - 1:
            el = time.time() - t_start
            done = f - a + 1
            print(f"frame {f}/{b - 1}  {el:.0f}s  eta {el / done * (b - a - done):.0f}s", flush=True)
    proc.stdin.close()
    proc.wait()
    print("listo:", out, f"{time.time() - t_start:.0f}s")


if __name__ == "__main__":
    main()
