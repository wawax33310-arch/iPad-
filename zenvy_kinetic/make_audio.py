#!/usr/bin/env python3
"""Ambiance sonore minimaliste pour la video kinetic typography Zenvy.

Tout est synthetise (aucun sample externe) : drone sub, nappe filtree,
pulsations qui accelerent, ticks sur chaque mot, whooshes sur les whips,
impacts sur les deux chutes, riser puis pop sur la reveal de la marque.

Les instants viennent de timing.py : la bande son reste calee sur l'image.

Sortie : out/zenvy_audio.wav (48 kHz, stereo, 20 s)
"""

import os
import wave

import numpy as np

import timing as TM

SR = 48000
DUR = TM.DUR
N = int(SR * DUR)
T = np.arange(N) / SR

rng = np.random.default_rng(20260820)

# ---------------------------------------------------------------- helpers


def env_exp(start, decay, length=None):
    """Enveloppe exponentielle demarrant a `start` secondes."""
    e = np.zeros(N)
    i0 = int(start * SR)
    if i0 >= N:
        return e
    n = int((length if length else decay * 6) * SR)
    n = min(n, N - i0)
    if n <= 0:
        return e
    t = np.arange(n) / SR
    e[i0:i0 + n] = np.exp(-t / decay)
    return e


def add(buf, sig, start, gain=1.0):
    """Additionne `sig` dans `buf` a partir de `start` secondes."""
    i0 = int(start * SR)
    if i0 < 0 or i0 >= N:
        return buf
    n = min(len(sig), N - i0)
    if n > 0:
        buf[i0:i0 + n] += sig[:n] * gain
    return buf


def onepole_lp(x, cutoff):
    """Passe-bas 1 pole, cutoff scalaire ou tableau (Hz)."""
    c = np.asarray(cutoff, dtype=np.float64)
    a = np.exp(-2.0 * np.pi * c / SR)
    y = np.empty_like(x)
    acc = 0.0
    if a.ndim == 0:
        a_val = float(a)
        for i in range(len(x)):
            acc = a_val * acc + (1.0 - a_val) * x[i]
            y[i] = acc
    else:
        for i in range(len(x)):
            ai = a[i]
            acc = ai * acc + (1.0 - ai) * x[i]
            y[i] = acc
    return y


def onepole_hp(x, cutoff):
    return x - onepole_lp(x, cutoff)


def fft_convolve(x, ir):
    n = len(x) + len(ir) - 1
    nfft = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)
    return y[:len(x)]


def make_ir(length=1.4, decay=0.32, damp=4200.0):
    """Petite reverb : bruit decroissant + amortissement des aigus."""
    n = int(length * SR)
    t = np.arange(n) / SR
    ir = rng.normal(0, 1, n) * np.exp(-t / decay)
    ir[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    ir = onepole_lp(ir, damp)
    return ir / (np.abs(ir).max() + 1e-9) * 0.5


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def noise_burst(dur, lo, hi, shape=1.0):
    """Petit souffle bande-passante, utilise pour ticks et whooshes."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    x = onepole_lp(x, hi)
    x = onepole_hp(x, lo)
    return x * (np.sin(np.pi * (t / t[-1]) ** shape) ** 1.6)


# ---------------------------------------------------------------- couches

dry = np.zeros(N)   # signal direct
send = np.zeros(N)  # bus vers la reverb

# --- 1. Drone sub / nappe -------------------------------------------------
drone_env = smoothstep(T / 1.2) * (1.0 - smoothstep((T - 19.1) / 0.9))
drone_env = drone_env * (1.0 + 0.55 * smoothstep((T - 12.8) / 3.0)
                         * (1 - smoothstep((T - 18.6) / 1.2)))

drone = (
    0.50 * np.sin(2 * np.pi * 55.0 * T)
    + 0.22 * np.sin(2 * np.pi * 110.0 * T + 0.4)
    + 0.10 * np.sin(2 * np.pi * 164.8 * T + 1.1)
    + 0.16 * np.sin(2 * np.pi * 55.35 * T + 2.0)   # battement lent
)
drone *= drone_env * 0.16
dry += drone

cut = 380 + 260 * np.sin(2 * np.pi * 0.06 * T) + 1500 * smoothstep((T - 13.0) / 3.0)
pad = onepole_hp(onepole_lp(rng.normal(0, 1, N), cut), 90.0) * 0.055 * drone_env
dry += pad
send += pad * 0.5

sh_env = smoothstep((T - TM.ZEN_IN) / 0.5) * (1.0 - smoothstep((T - 19.2) / 0.8))
shimmer = (
    0.6 * np.sin(2 * np.pi * 440.0 * T)
    + 0.4 * np.sin(2 * np.pi * 659.3 * T + 0.7)
    + 0.3 * np.sin(2 * np.pi * 880.0 * T + 1.9)
)
shimmer *= sh_env * 0.022 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.5 * T))
dry += shimmer
send += shimmer * 0.6

# --- 2. Pulsations qui accelerent ----------------------------------------
pulse_times = [0.30, 2.30, 4.30, 6.30, 8.30, 10.30, 12.30,
               13.30, 14.05, 14.70, 15.25, 15.70]
for i, pt in enumerate(pulse_times):
    e = env_exp(pt, 0.20 + 0.02 * i)
    thump = np.sin(2 * np.pi * 64.0 * (T - pt) * (T >= pt)) * e
    g = 0.10 + 0.06 * (i / (len(pulse_times) - 1))
    dry += thump * g
    send += thump * g * 0.25

# --- 3. Ticks sur chaque mot ---------------------------------------------
# Les mots claquent vite : un tick discret par mot souligne le rythme.
for key, wt in TM.ALL_WORD_TIMES:
    g = 0.075 if key == "s5" else 0.05
    add(dry, noise_burst(0.045, 2200, 12000), wt, g)
    add(send, noise_burst(0.045, 2200, 12000), wt, g * 0.4)

# --- 4. Impacts des deux chutes ------------------------------------------
for imp in TM.IMPACTS:
    e = env_exp(imp, 0.30)
    body = np.sin(2 * np.pi * 46.0 * (T - imp) * (T >= imp)) * e * 0.42
    click = onepole_lp(rng.normal(0, 1, N), 900.0) * env_exp(imp, 0.035) * 0.30
    dry += body + click
    send += (body + click) * 0.45

# --- 5. Whooshes sur les sorties en whip ---------------------------------
for i, wt in enumerate(TM.WHIPS):
    if wt > 15.0:
        continue                      # la derniere sortie est couverte par le riser
    wh = noise_burst(0.26, 420, 6500, shape=0.75)
    add(dry, wh, wt - 0.04, 0.20)
    add(send, wh, wt - 0.04, 0.10)

# --- 6. Riser 13 -> 16 s --------------------------------------------------
ri = int(13.0 * SR)
rn = int(2.95 * SR)
rt = np.arange(rn) / SR
riser = onepole_lp(rng.normal(0, 1, rn), 300 * (1 + 14 * (rt / rt[-1]) ** 2.2))
riser = onepole_hp(riser, 200 + 1600 * (rt / rt[-1]) ** 2)
riser *= (rt / rt[-1]) ** 2.0 * 0.30
riser *= 1.0 - smoothstep((rt - 2.85) / 0.10)
dry[ri:ri + rn] += riser
send[ri:ri + rn] += riser * 0.4

f_up = 180 * np.exp(np.log(6.0) * (rt / rt[-1]))
dry[ri:ri + rn] += np.sin(2 * np.pi * np.cumsum(f_up) / SR) * (rt / rt[-1]) ** 3 * 0.05

# --- 7. Whoosh + pop sur la reveal ---------------------------------------
wi = int((TM.ZEN_IN - 0.58) * SR)
wn = int(0.60 * SR)
wt_ = np.arange(wn) / SR
wh = onepole_lp(rng.normal(0, 1, wn), 500 * (1 + 9 * (wt_ / wt_[-1]) ** 1.6))
wh = onepole_hp(wh, 350.0)
wh *= np.sin(np.pi * (wt_ / wt_[-1]) ** 0.8) ** 1.5 * 0.42
dry[wi:wi + wn] += wh
send[wi:wi + wn] += wh * 0.55

pn = int(0.14 * SR)
pt_ = np.arange(pn) / SR
f_pop = 1100 * np.exp(-pt_ / 0.020) + 150
ppop = np.sin(2 * np.pi * np.cumsum(f_pop) / SR) * np.exp(-pt_ / 0.030) * 0.55
add(dry, ppop, TM.ZEN_IN)
add(send, ppop, TM.ZEN_IN, 0.5)

be = env_exp(TM.ZEN_IN, 0.55)
boom = np.sin(2 * np.pi * 48.0 * (T - TM.ZEN_IN) * (T >= TM.ZEN_IN)) * be * 0.50
boom += onepole_lp(rng.normal(0, 1, N), 600.0) * env_exp(TM.ZEN_IN, 0.05) * 0.22
dry += boom
send += boom * 0.5

# souffle d'apparition du carton final
dry += onepole_hp(rng.normal(0, 1, N), 1800.0) * env_exp(TM.FINAL_IN, 0.22) * 0.05

# ---------------------------------------------------------------- mix

wet = fft_convolve(send, make_ir())
mix = dry + wet * 0.30

high = onepole_hp(mix, 700.0)
low = mix - high
delay = int(0.011 * SR)
left = low + np.concatenate([np.zeros(delay), high[:-delay]]) * 0.95
right = low + high * 0.95
stereo = np.stack([left, right], axis=1)

stereo = np.tanh(stereo * 1.25) / 1.25
fi = int(0.05 * SR)
stereo[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(0.75 * SR)
stereo[-fo:] *= np.linspace(1, 0, fo)[:, None]
stereo *= 0.92 / (np.abs(stereo).max() + 1e-9)

out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
os.makedirs(out_dir, exist_ok=True)
path = os.path.join(out_dir, "zenvy_audio.wav")

pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
with wave.open(path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"audio ecrit : {path}  ({DUR:.1f}s, {SR} Hz, stereo)")
print(f"  {len(TM.ALL_WORD_TIMES)} ticks, {len(TM.IMPACTS)} impacts, "
      f"{len([w for w in TM.WHIPS if w <= 15.0])} whooshes")
