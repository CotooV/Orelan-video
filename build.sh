#!/usr/bin/env bash
# Reconstruye el anuncio completo desde código: música, imagen, control de calidad.
# Si existe brand/orelan-logo.svg se usa automáticamente en el cierre.
set -euo pipefail
cd "$(dirname "$0")"
pip install --quiet moderngl numpy scipy pillow pyloudnorm cairosvg matplotlib
mkdir -p build out
python3 src/music.py build/music.wav
xvfb-run -a -s "-screen 0 1280x1024x24" \
  python3 src/render.py --out out/orelan_apertura_15s.mp4 --audio build/music.wav --crf 12
python3 tools/qc.py out/orelan_apertura_15s.mp4 out/QC.md
