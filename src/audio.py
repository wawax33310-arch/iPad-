#!/usr/bin/env python3
"""
Piste sonore de la pub Zenvy (20 s) — synthèse pure, aucun sample externe.

  - nappe électronique minimaliste (pas de voix, pas de paroles)
  - intensité qui suit la montée du montage, accélération à partir de 13 s
  - riser + whoosh + impact courts synchronisés sur le flash de la séquence 6

Sortie : out/zenvy-audio.wav (48 kHz, stéréo, 16 bits)
"""

import math
import wave
import struct
import os
import numpy as np

SR = 48000
DUR = 20.0
N = int(SR * DUR)
T = np.arange(N) / SR

FLASH = 16.40          # pic du flash lumineux (séquence 6)
CUT = 16.00            # coupe nette séquence 5 -> 6
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "out", "zenvy-audio.wav")


# --------------------------------------------------------------------------
# utilitaires
# --------------------------------------------------------------------------
def ramp(t, x0, x1, y0, y1):
    """Rampe lissée (smoothstep) de y0 à y1 entre x0 et x1."""
    p = np.clip((t - x0) / (x1 - x0), 0.0, 1.0)
    return y0 + (y1 - y0) * (p * p * (3 - 2 * p))


def window_section(t, start, end, fade=0.5):
    """Fenêtre d'une section d'accord avec fondus enchaînés."""
    up = np.clip((t - start) / fade, 0, 1)
    down = np.clip((end - t) / fade, 0, 1)
    w = np.minimum(up, down)
    return w * w * (3 - 2 * w)


def sweep_noise(t0, t1, f_start, f_end, bw_oct=1.2, seed=1):
    """Bruit filtré passe-bande dont la fréquence centrale balaie f_start -> f_end.
    Filtrage temps-variant par STFT (fenêtres de Hann, overlap-add)."""
    rng = np.random.default_rng(seed)
    i0, i1 = int(t0 * SR), int(t1 * SR)
    length = i1 - i0
    out = np.zeros(N)
    if length <= 0:
        return out

    noise = rng.normal(0, 1, length)
    win_len, hop = 2048, 512
    win = np.hanning(win_len)
    freqs = np.fft.rfftfreq(win_len, 1 / SR)
    freqs[0] = 1e-6
    acc = np.zeros(length + win_len)
    norm = np.zeros(length + win_len)

    for start in range(0, length, hop):
        chunk = np.zeros(win_len)
        seg = noise[start:start + win_len]
        chunk[:len(seg)] = seg
        p = start / max(length - 1, 1)
        fc = f_start * (f_end / f_start) ** p            # balayage exponentiel
        mask = np.exp(-0.5 * (np.log2(freqs / fc) / bw_oct) ** 2)
        filt = np.fft.irfft(np.fft.rfft(chunk * win) * mask, win_len)
        acc[start:start + win_len] += filt * win
        norm[start:start + win_len] += win * win

    acc = acc[:length] / np.maximum(norm[:length], 1e-6)
    out[i0:i1] = acc
    return out


def fft_convolve(sig, ir):
    n = 1
    while n < len(sig) + len(ir):
        n *= 2
    res = np.fft.irfft(np.fft.rfft(sig, n) * np.fft.rfft(ir, n), n)
    return res[:len(sig)]


# --------------------------------------------------------------------------
# 1. Courbe d'intensité : suit la montée du montage
# --------------------------------------------------------------------------
intensity = np.full(N, 0.30)
intensity = np.maximum(intensity, ramp(T, 0.0, 2.0, 0.10, 0.32))
intensity = np.maximum(intensity, ramp(T, 6.5, 8.0, 0.32, 0.42))
intensity = np.maximum(intensity, ramp(T, 12.5, 13.2, 0.42, 0.55))
intensity = np.maximum(intensity, ramp(T, 13.2, FLASH, 0.55, 1.00))
intensity = np.where(T > FLASH, ramp(T, FLASH, 19.6, 1.00, 0.55), intensity)


# --------------------------------------------------------------------------
# 2. Nappe : accords tenus, timbre qui s'ouvre avec l'intensité
# --------------------------------------------------------------------------
A2, C3, D3, E3, F2, F3, G2, G3, A3, B3, C4, E4 = (
    110.00, 130.81, 146.83, 164.81, 87.31, 174.61,
    98.00, 196.00, 220.00, 246.94, 261.63, 329.63)

SECTIONS = [
    # (début, fin, notes, gain)      -- Am / F / G(tension) / Am ouvert
    (-0.5, 7.3, [A2, E3, A3, C4], 1.00),
    (6.8, 13.3, [F2, C3, F3, A3], 1.00),
    (12.8, FLASH + 0.1, [G2, D3, G3, B3], 1.05),
    (FLASH - 0.15, 20.5, [A2, E3, A3, C4, E4], 1.15),
]

HARMONICS = 7
pad_l = np.zeros(N)
pad_r = np.zeros(N)
rng = np.random.default_rng(7)

for (s0, s1, notes, gain) in SECTIONS:
    env = window_section(T, s0, s1) * gain
    if not np.any(env > 0):
        continue
    for k, f in enumerate(notes):
        # léger vibrato lent, désaccord doux entre les deux oscillateurs
        drift = 1 + 0.0009 * np.sin(2 * np.pi * (0.07 + 0.013 * k) * T + k)
        for det, pan in ((1.0 - 0.0012, 0.0), (1.0 + 0.0012, 1.0)):
            phase = 2 * np.pi * f * det * drift * T + rng.uniform(0, 6.28)
            voice = np.zeros(N)
            for n in range(1, HARMONICS + 1):
                w = np.exp(-(n - 1) / (1.1 + 5.0 * intensity)) / (n ** 0.7)
                voice += w * np.sin(n * phase)
            voice *= env / (len(notes) * 2.2)
            # note grave centrée, notes hautes légèrement élargies
            width = 0.20 if k == 0 else 0.42
            gl = 0.5 + (0.5 - pan) * width
            gr = 1.0 - gl
            pad_l += voice * gl
            pad_r += voice * gr

pad_l *= 0.34
pad_r *= 0.34


# --------------------------------------------------------------------------
# 3. Pouls rythmique : lent, puis accélération à partir de la séquence 5
# --------------------------------------------------------------------------
pulse = np.zeros(N)
tick = np.zeros(N)


def add_pulse(t_at, amp=1.0, freq=55.0, decay=0.28):
    i0 = int(t_at * SR)
    if i0 >= N or t_at < 0:
        return
    ln = min(int(decay * 3 * SR), N - i0)
    tt = np.arange(ln) / SR
    env = np.exp(-tt / decay)
    f = freq * (1 + 1.6 * np.exp(-tt / 0.02))          # petit "pitch drop"
    pulse[i0:i0 + ln] += amp * env * np.sin(2 * np.pi * f * tt)


def add_tick(t_at, amp=1.0, decay=0.035, seed=3):
    i0 = int(t_at * SR)
    if i0 >= N or t_at < 0:
        return
    ln = min(int(decay * 6 * SR), N - i0)
    r = np.random.default_rng(seed + i0)
    nz = np.diff(r.normal(0, 1, ln + 1))               # bruit "clair"
    tt = np.arange(ln) / SR
    tick[i0:i0 + ln] += amp * np.exp(-tt / decay) * nz


beats = []
t_beat = 0.0
while t_beat < CUT:
    beats.append(t_beat)
    if t_beat < 13.0:
        step = 1.0
    elif t_beat < 15.0:
        step = 0.5
    else:
        step = 0.25
    t_beat += step

for b in beats:
    lvl = 0.42 if b < 13.0 else 0.55 + 0.25 * (b - 13.0) / 3.0
    add_pulse(b, amp=lvl * 0.9)
    if b >= 13.0:
        add_tick(b + 0.25 if b < 13.0 else b, amp=0.05 + 0.05 * (b - 13.0) / 3.0)

# battements sourds après le climax
add_pulse(17.6, amp=0.30)
add_pulse(18.6, amp=0.22)


# --------------------------------------------------------------------------
# 4. Riser + whoosh + impact autour du flash
# --------------------------------------------------------------------------
riser = sweep_noise(13.9, FLASH, 350, 5200, bw_oct=1.4, seed=11)
riser_env = np.clip((T - 13.9) / (FLASH - 13.9), 0, 1) ** 2.2
riser *= riser_env * 0.30

# sine sweep discret qui accompagne le riser
sw = np.zeros(N)
i0, i1 = int(13.9 * SR), int(FLASH * SR)
tt = np.linspace(0, 1, i1 - i0)
f_sw = 180 * (1400 / 180) ** tt
ph = 2 * np.pi * np.cumsum(f_sw) / SR
sw[i0:i1] = np.sin(ph) * (tt ** 3) * 0.12

# whoosh court centré sur le flash
whoosh = sweep_noise(FLASH - 0.55, FLASH + 0.30, 700, 9000, bw_oct=1.6, seed=23)
wi0 = int((FLASH - 0.55) * SR)
wi1 = int((FLASH + 0.30) * SR)
wt = np.arange(wi1 - wi0) / SR
wenv = np.where(wt < 0.55, (wt / 0.55) ** 2.5, np.exp(-(wt - 0.55) / 0.09))
whoosh[wi0:wi1] *= wenv * 0.55

# "pop" transitoire + impact sub, pile sur le flash
impact = np.zeros(N)
i0 = int(FLASH * SR)
ln = min(int(1.6 * SR), N - i0)
tt = np.arange(ln) / SR
f_pop = 120 + 780 * np.exp(-tt / 0.02)
impact[i0:i0 + ln] += 0.45 * np.exp(-tt / 0.09) * np.sin(2 * np.pi * np.cumsum(f_pop) / SR)
impact[i0:i0 + ln] += 0.80 * np.exp(-tt / 0.45) * np.sin(2 * np.pi * 45 * tt)
r = np.random.default_rng(5)
impact[i0:i0 + ln] += 0.12 * np.exp(-tt / 0.10) * r.normal(0, 1, ln)

# petit souffle sur la coupe nette 5 -> 6
cut_fx = sweep_noise(CUT - 0.18, CUT + 0.12, 1200, 400, bw_oct=1.3, seed=31)
ci0, ci1 = int((CUT - 0.18) * SR), int((CUT + 0.12) * SR)
ct = np.arange(ci1 - ci0) / SR
cut_fx[ci0:ci1] *= np.exp(-np.abs(ct - 0.18) / 0.06) * 0.18

fx = riser + sw + whoosh + impact + cut_fx


# --------------------------------------------------------------------------
# 5. Réverbération légère sur le bus effets (queue synthétique)
# --------------------------------------------------------------------------
ir_len = int(1.1 * SR)
ir_t = np.arange(ir_len) / SR
r = np.random.default_rng(99)
ir = r.normal(0, 1, ir_len) * np.exp(-ir_t / 0.30)
ir *= np.linspace(1, 0.2, ir_len)
ir[:int(0.008 * SR)] = 0
ir /= np.sqrt(np.sum(ir ** 2))
wet = fft_convolve(fx, ir) * 0.55


# --------------------------------------------------------------------------
# 6. Mixage
# --------------------------------------------------------------------------
mono = pulse * 0.9 + tick * 0.6 + fx * 0.95 + wet * 0.45
left = pad_l + mono
right = pad_r + mono

# léger élargissement stéréo sur les effets aigus
delay = int(0.008 * SR)
right[delay:] += 0.12 * (fx[:-delay] * 0.5)

# enveloppe globale : fondu d'entrée + fondu de sortie sur la dernière seconde
master = np.ones(N)
master *= np.clip(T / 0.25, 0, 1)
master *= np.clip((20.0 - T) / 0.55, 0, 1) ** 0.8
left *= master
right *= master

stereo = np.stack([left, right], axis=1)
stereo = np.tanh(stereo * 1.15) / 1.05          # limitation douce
peak = np.max(np.abs(stereo))
stereo *= 0.92 / peak

os.makedirs(os.path.dirname(OUT), exist_ok=True)
pcm = (stereo * 32767).astype(np.int16)
with wave.open(OUT, "wb") as f:
    f.setnchannels(2)
    f.setsampwidth(2)
    f.setframerate(SR)
    f.writeframes(pcm.tobytes())

print(f"✔ {OUT} — {DUR:.1f}s, {SR} Hz, stéréo, pic {peak:.3f} -> 0.92")
