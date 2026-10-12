"""Análisis de la banda sonora: espectrograma, envolvente y onsets vs. golpes."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np
from scipy.io import wavfile
from scipy import signal
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from timeline import HITS, SHOTS

path, out = sys.argv[1], sys.argv[2]
sr, x = wavfile.read(path)
x = x.astype(np.float64)
if x.ndim == 2: mono = x.mean(axis=1)
else: mono = x
f, t, S = signal.spectrogram(mono, sr, nperseg=2048, noverlap=1792)
win = int(0.01 * sr)
rms = np.sqrt(np.convolve(mono ** 2, np.ones(win) / win, mode="same"))
# flujo espectral para onsets
fo, to, Z = signal.stft(mono, sr, nperseg=1024, noverlap=768)
mag = np.log1p(np.abs(Z) * 100)
flux = np.maximum(np.diff(mag, axis=1), 0).sum(axis=0)
flux = (flux - flux.mean()) / flux.std()
peaks, _ = signal.find_peaks(flux, height=2.0, distance=int(0.12 * sr / 256))
onsets = to[1:][peaks]
fig, ax = plt.subplots(3, 1, figsize=(16, 9), sharex=True)
ax[0].pcolormesh(t, f, 10 * np.log10(S + 1e-12), shading="auto", cmap="magma", vmin=-110, vmax=-30)
ax[0].set_yscale("symlog", linthresh=200); ax[0].set_ylim(20, 16000)
ax[1].plot(np.arange(len(rms)) / sr, 20 * np.log10(rms + 1e-9), lw=0.6); ax[1].set_ylim(-70, 0)
ax[2].plot(to[1:], flux, lw=0.6)
ax[2].plot(onsets, flux[peaks], "rx")
for k, v in HITS.items():
    for a in ax: a.axvline(v, color="c", lw=0.6, alpha=0.6)
    ax[2].text(v, ax[2].get_ylim()[1] * 0.9, k, rotation=90, fontsize=7, va="top")
for _, a0, b0 in SHOTS:
    for a in ax: a.axvline(a0, color="w" if a is ax[0] else "k", lw=1.2, ls="--")
plt.tight_layout(); plt.savefig(out, dpi=90)
print("onsets detectados:", " ".join(f"{o:.3f}" for o in onsets))
for k, v in HITS.items():
    d = onsets - v
    j = np.argmin(np.abs(d)) if len(d) else None
    print(f"  {k:14s} {v:6.3f}s  onset más cercano {onsets[j]:6.3f}s  Δ={d[j]*1000:+5.0f} ms")
