#!/usr/bin/env python3
"""
Bande son de la pub Zenvy (20 s) — synthèse pure, aucun sample externe.

Prod électronique rythmée, sans voix ni paroles, calée sur le montage :
  120 BPM (1 mesure = 2 s), donc chaque séquence tombe pile sur une mesure.

  mes. 1-2 (0-4 s)   intro     kick 1 & 3, hat 8e, nappe filtrée
  mes. 3-4 (4-8 s)   groove    kick 4/4, basse contretemps, clap sur 2 et 4
  mes. 5-6 (8-12 s)  montée    basse en croches, hats en doubles, stabs
  mes. 7-8 (12-16 s) build     roulement qui accélère, riser, coupe avant le drop
  mes. 9-10 (16-20 s) drop     impact, kick + basse pleine, stabs larges, sortie

Sortie : out/zenvy-audio.wav (48 kHz, stéréo, 16 bits)
"""

import os
import wave
import numpy as np

SR = 48000
DUR = 20.0
N = int(SR * DUR)
T = np.arange(N) / SR

BPM = 120.0
BEAT = 60.0 / BPM          # 0.5 s
BAR = 4 * BEAT             # 2 s
DROP = 16.0                # coupe nette séquence 5 -> 6
FLASH = 16.40              # pic du flash lumineux

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "out", "zenvy-audio.wav")

rng = np.random.default_rng(2024)
mix = np.zeros((N, 2))


# --------------------------------------------------------------------------
# outils
# --------------------------------------------------------------------------
def add(sig, at, gain=1.0, pan=0.0):
    """Ajoute un signal mono dans le mix à l'instant `at` (s)."""
    i0 = int(at * SR)
    if i0 >= N:
        return
    if i0 < 0:
        sig = sig[-i0:]
        i0 = 0
    ln = min(len(sig), N - i0)
    l = gain * np.sqrt(0.5 * (1 - pan))
    r = gain * np.sqrt(0.5 * (1 + pan))
    mix[i0:i0 + ln, 0] += sig[:ln] * l
    mix[i0:i0 + ln, 1] += sig[:ln] * r


def env_exp(n, decay, attack=0.002):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-5), 0, 1)
    return a * np.exp(-t / decay)


def kick(decay=0.34, f0=115.0, f1=44.0, punch=1.0):
    n = int(decay * 3 * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.026)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / decay)
    click = np.exp(-t / 0.004) * rng.normal(0, 1, n) * 0.25 * punch
    return np.tanh((body + click) * 1.4) * 0.9


def sub(freq, dur, decay=None, shape=0.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    d = decay if decay else dur * 0.6
    sig = np.sin(2 * np.pi * freq * t)
    sig += shape * np.sin(4 * np.pi * freq * t) * 0.35      # harmonique = grain
    e = np.minimum(np.clip(t / 0.006, 0, 1), np.exp(-t / d))
    return np.tanh(sig * e * 1.3) * 0.8


def noise_hit(decay, bright=1.0, seed=None):
    n = int(decay * 5 * SR)
    r = np.random.default_rng(seed) if seed is not None else rng
    nz = r.normal(0, 1, n + 1)
    hp = np.diff(nz)                                        # bruit éclairci
    body = hp * bright + nz[:n] * (1 - bright) * 0.6
    return body * env_exp(n, decay, attack=0.0008)


def clap(decay=0.16):
    n = int(decay * 5 * SR)
    out = np.zeros(n)
    for k, off in enumerate((0.0, 0.011, 0.021)):           # 3 rebonds = clap
        i = int(off * SR)
        seg = noise_hit(0.035, bright=0.85, seed=100 + k)
        ln = min(len(seg), n - i)
        out[i:i + ln] += seg[:ln] * (0.8 ** k)
    tail = noise_hit(decay, bright=0.7, seed=200)
    out[:len(tail)] += tail * 0.5
    return out * 0.55


def hat(decay=0.028, bright=1.0):
    return noise_hit(decay, bright=bright, seed=int(rng.integers(1e6))) * 0.35


def stab(freqs, dur=0.22, harm=6, glide=0.0):
    """Accord court, timbre saw filtré (harmoniques décroissantes)."""
    n = int(dur * 3 * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        ff = f * (1 + glide * np.exp(-t / 0.05))
        ph = 2 * np.pi * np.cumsum(ff) / SR
        for k in range(1, harm + 1):
            out += np.sin(k * ph) / (k ** 1.25) * np.exp(-k / 4.0)
    out /= len(freqs)
    return out * env_exp(n, dur * 0.45, attack=0.004) * 0.5


def sweep_noise(dur, f_start, f_end, bw_oct=1.2, seed=1):
    """Bruit passe-bande balayé (riser / whoosh), filtrage STFT temps-variant."""
    length = int(dur * SR)
    r = np.random.default_rng(seed)
    noise = r.normal(0, 1, length)
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
        fc = f_start * (f_end / f_start) ** p
        mask = np.exp(-0.5 * (np.log2(freqs / fc) / bw_oct) ** 2)
        acc[start:start + win_len] += np.fft.irfft(np.fft.rfft(chunk * win) * mask, win_len) * win
        norm[start:start + win_len] += win * win
    return acc[:length] / np.maximum(norm[:length], 1e-6)


def fft_convolve(sig, ir):
    n = 1
    while n < len(sig) + len(ir):
        n *= 2
    return np.fft.irfft(np.fft.rfft(sig, n) * np.fft.rfft(ir, n), n)[:len(sig)]


# --------------------------------------------------------------------------
# harmonie : Am - F - C - G - Am (une couleur par 2 mesures)
# --------------------------------------------------------------------------
NOTE = {'A1': 55.00, 'C2': 65.41, 'E2': 82.41, 'F1': 43.65, 'G1': 49.00,
        'A2': 110.00, 'C3': 130.81, 'E3': 164.81, 'F2': 87.31, 'G2': 98.00,
        'A3': 220.00, 'C4': 261.63, 'E4': 329.63, 'F3': 174.61, 'G3': 196.00,
        'B3': 246.94, 'D4': 293.66, 'A4': 440.00}

SECTIONS = [                     # (début, fin, basse, accord)
    (0.0,  4.0, NOTE['A1'], [NOTE['A3'], NOTE['C4'], NOTE['E4']]),
    (4.0,  8.0, NOTE['F1'], [NOTE['A3'], NOTE['C4'], NOTE['F3']]),
    (8.0, 12.0, NOTE['C2'], [NOTE['C4'], NOTE['E4'], NOTE['G3']]),
    (12.0, 16.0, NOTE['G1'], [NOTE['B3'], NOTE['D4'], NOTE['G3']]),
    (16.0, 20.0, NOTE['A1'], [NOTE['A3'], NOTE['C4'], NOTE['E4'], NOTE['A4']]),
]


def section_at(t):
    for s in SECTIONS:
        if s[0] <= t < s[1]:
            return s
    return SECTIONS[-1]


# --------------------------------------------------------------------------
# nappe de fond (elle tient l'harmonie sous le rythme)
# --------------------------------------------------------------------------
intensity = np.interp(T, [0, 4, 8, 12, 15.5, 16.0, 19.0, 20.0],
                         [0.25, 0.35, 0.5, 0.62, 0.95, 1.0, 0.8, 0.5])

for (s0, s1, bass, chord) in SECTIONS:
    i0, i1 = int(s0 * SR), int(s1 * SR)
    tt = np.arange(i1 - i0) / SR
    seg = np.zeros(i1 - i0)
    inten = intensity[i0:i1]
    for f in chord:
        for det in (0.9988, 1.0012):
            ph = 2 * np.pi * f * det * tt
            for k in range(1, 6):
                seg += np.sin(k * ph) * np.exp(-(k - 1) / (0.9 + 4.0 * inten)) / (k ** 0.8)
    seg /= (len(chord) * 2 * 3.0)
    fade = np.minimum(np.clip(tt / 0.35, 0, 1), np.clip((s1 - s0 - tt) / 0.35, 0, 1))
    add(seg * fade * 0.16, s0, pan=-0.15)
    add(np.roll(seg, 240) * fade * 0.16, s0, pan=0.15)


# --------------------------------------------------------------------------
# rythmique
# --------------------------------------------------------------------------
def bar_time(bar_idx, beat=0.0):
    return bar_idx * BAR + beat * BEAT


# --- kick -----------------------------------------------------------------
for bar in range(10):
    for b in range(4):
        t0 = bar_time(bar, b)
        if t0 >= 15.5 and t0 < DROP:            # respiration avant le drop
            continue
        if bar < 2:                             # intro : temps 1 et 3
            if b % 2 == 0:
                add(kick(decay=0.30), t0, gain=0.72)
        elif bar < 6:
            add(kick(), t0, gain=0.88)
        elif bar < 8:
            add(kick(), t0, gain=0.92)
            if b == 3:
                add(kick(decay=0.22), t0 + BEAT / 2, gain=0.7)
        else:                                   # drop
            add(kick(decay=0.38, punch=1.2), t0, gain=1.0)
            if b == 2:
                add(kick(decay=0.20), t0 + BEAT * 0.75, gain=0.6)

# --- basse ----------------------------------------------------------------
for bar in range(10):
    s = section_at(bar_time(bar))
    root = s[2]
    if bar < 2:
        add(sub(root, BEAT * 1.5, decay=0.5), bar_time(bar, 0), gain=0.5)
    elif bar < 4:                               # contretemps
        for b in range(4):
            add(sub(root, BEAT * 0.45, decay=0.16, shape=0.4),
                bar_time(bar, b) + BEAT / 2, gain=0.55)
    elif bar < 8:                               # croches, avec quinte de passage
        for k in range(8):
            t0 = bar_time(bar) + k * BEAT / 2
            if t0 >= 15.5:
                continue
            f = root * (1.5 if k in (5, 7) else 1.0)
            add(sub(f, BEAT * 0.42, decay=0.15, shape=0.5), t0, gain=0.52)
    else:                                       # drop : basse pleine
        for k in range(8):
            t0 = bar_time(bar) + k * BEAT / 2
            f = root * (1.0 if k % 4 < 2 else 1.5)
            add(sub(f, BEAT * 0.46, decay=0.20, shape=0.6), t0, gain=0.62)

# --- clap / snare ---------------------------------------------------------
for bar in range(10):
    for b in (1, 3):
        t0 = bar_time(bar, b)
        if t0 >= 15.5 and t0 < DROP:
            continue
        if bar >= 2:
            add(clap(), t0, gain=0.75 if bar < 8 else 0.95)

# --- hats -----------------------------------------------------------------
for bar in range(10):
    if bar < 2:
        steps, lvl = 8, 0.35
    elif bar < 4:
        steps, lvl = 8, 0.5
    elif bar < 8:
        steps, lvl = 16, 0.45
    else:
        steps, lvl = 16, 0.6
    for k in range(steps):
        t0 = bar_time(bar) + k * BAR / steps
        if 15.5 <= t0 < DROP:
            continue
        accent = 1.0 if (k % (steps // 4) == 0) else 0.55
        add(hat(decay=0.030 if accent > 0.9 else 0.020), t0,
            gain=lvl * accent, pan=0.25 * (1 if k % 2 else -1))

# --- stabs d'accord -------------------------------------------------------
for bar in range(4, 10):
    s = section_at(bar_time(bar))
    chord = s[3]
    if bar < 8:
        for b in (1, 2.5):
            t0 = bar_time(bar, b)
            if t0 >= 15.5:
                continue
            add(stab(chord, dur=0.20), t0, gain=0.30, pan=0.1)
    else:                                       # drop : stabs plus larges
        for b in (0, 1.5, 2, 3.5):
            add(stab(chord, dur=0.26, harm=8), bar_time(bar, b), gain=0.42,
                pan=0.15 if b % 2 else -0.15)


# --------------------------------------------------------------------------
# build (mes. 7-8) : roulement qui accélère + riser, puis coupe
# --------------------------------------------------------------------------
t_roll = 14.0
step = 0.25
while t_roll < 15.5:
    lvl = 0.25 + 0.55 * (t_roll - 14.0) / 1.5
    add(noise_hit(0.05, bright=0.9, seed=int(t_roll * 1000)) * 0.8, t_roll, gain=lvl)
    step = max(0.0625, step * 0.82)             # 8e -> 16e -> 32e
    t_roll += step

riser = sweep_noise(2.6, 300, 6000, bw_oct=1.4, seed=11)
r_env = np.linspace(0, 1, len(riser)) ** 2.4
add(riser * r_env, 13.8, gain=0.34)

n_sw = int(2.6 * SR)
tt = np.linspace(0, 1, n_sw)
f_sw = 160 * (1600 / 160) ** tt
add(np.sin(2 * np.pi * np.cumsum(f_sw) / SR) * (tt ** 3), 13.8, gain=0.16)

# petit silence tendu juste avant la coupe : seule la queue du riser reste


# --------------------------------------------------------------------------
# drop : impact sur la coupe + accent sur le flash
# --------------------------------------------------------------------------
n_imp = int(2.0 * SR)
t_imp = np.arange(n_imp) / SR
impact = 0.9 * np.exp(-t_imp / 0.55) * np.sin(2 * np.pi * 42 * t_imp)
impact += 0.35 * np.exp(-t_imp / 0.10) * rng.normal(0, 1, n_imp)
add(np.tanh(impact * 1.2), DROP, gain=0.85)
add(sweep_noise(1.2, 9000, 500, bw_oct=1.5, seed=41) * np.exp(-np.arange(int(1.2 * SR)) / SR / 0.35),
    DROP, gain=0.30)                            # crash inversé -> descendant

# whoosh + pop pile sur le flash lumineux
whoosh = sweep_noise(0.75, 600, 9000, bw_oct=1.6, seed=23)
w_env = np.concatenate([
    np.linspace(0, 1, int(0.55 * SR)) ** 2.5,
    np.exp(-np.arange(len(whoosh) - int(0.55 * SR)) / SR / 0.08)])
add(whoosh * w_env[:len(whoosh)], FLASH - 0.55, gain=0.55)

n_pop = int(0.5 * SR)
t_pop = np.arange(n_pop) / SR
f_pop = 130 + 900 * np.exp(-t_pop / 0.02)
add(np.exp(-t_pop / 0.09) * np.sin(2 * np.pi * np.cumsum(f_pop) / SR), FLASH, gain=0.45)
add(np.exp(-t_pop / 0.30) * np.sin(2 * np.pi * 48 * t_pop), FLASH, gain=0.55)


# --------------------------------------------------------------------------
# réverbération courte sur l'ensemble (colle le mix)
# --------------------------------------------------------------------------
ir_len = int(0.9 * SR)
ir_t = np.arange(ir_len) / SR
ir = rng.normal(0, 1, ir_len) * np.exp(-ir_t / 0.22) * np.linspace(1, 0.15, ir_len)
ir[:int(0.006 * SR)] = 0
ir /= np.sqrt(np.sum(ir ** 2))
wet = np.stack([fft_convolve(mix[:, 0], ir), fft_convolve(mix[:, 1], ir)], axis=1)
out = mix + wet * 0.18

# arc d'énergie : chaque bloc de 4 s pousse un peu plus fort que le précédent
arc = np.interp(T, [0, 4, 8, 12, 15.5, 16.0, 19.0, 20.0],
                   [0.72, 0.82, 0.90, 0.96, 1.00, 1.06, 1.04, 0.98])
out *= arc[:, None]

# lift d'aigus (dérivée = pente +6 dB/oct) : lisibilité sur haut-parleur de téléphone
hf = np.diff(out, axis=0, prepend=out[:1])
out = out + 0.55 * hf


# --------------------------------------------------------------------------
# master
# --------------------------------------------------------------------------
master = np.clip(T / 0.12, 0, 1) * np.clip((20.0 - T) / 0.45, 0, 1) ** 0.7
out *= master[:, None]

# compression douce type « colle de bus » + limitation
env = np.abs(out).max(axis=1)
k = int(0.02 * SR)
env = np.convolve(env, np.ones(k) / k, mode='same')
gain = 1.0 / (1.0 + np.maximum(env - 0.55, 0) * 1.6)
out *= gain[:, None]
out = np.tanh(out * 1.25) / 1.05
peak = np.max(np.abs(out))
out *= 0.94 / peak

os.makedirs(os.path.dirname(OUT), exist_ok=True)
pcm = (out * 32767).astype(np.int16)
with wave.open(OUT, "wb") as f:
    f.setnchannels(2)
    f.setsampwidth(2)
    f.setframerate(SR)
    f.writeframes(pcm.tobytes())

rms = np.sqrt(np.mean(out ** 2))
print(f"✔ {OUT} — {DUR:.0f}s, {BPM:.0f} BPM, pic brut {peak:.2f} -> 0.94, RMS {rms:.3f}")
