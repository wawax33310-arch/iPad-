#!/usr/bin/env python3
"""Bande son de la video kinetic typography Zenvy.

Tout est synthetise (aucun sample externe) : kick, clap, charleston, basse,
arpege, nappes, plus les reperes de montage (ticks sur les mots, whooshes sur
les transitions, impacts des chutes, riser et pop sur la reveal).

Le morceau est cale sur la meme grille que l'image (timing.BEAT) : les coupes
tombent sur les temps et la reveal sur le 24e temps.

Sortie : out/zenvy_audio.wav (48 kHz, stereo, duree = timing.DUR)
"""

import os
import wave

import numpy as np

import timing as TM

SR = 48000
DUR = TM.DUR
N = int(SR * DUR)
T = np.arange(N) / SR

BEAT = TM.BEAT
BAR = 4 * BEAT
N_BARS = int(np.ceil(DUR / BAR))

rng = np.random.default_rng(20260820)

# ---------------------------------------------------------------- helpers


def env_exp(start, decay, length=None):
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
    if i0 >= N:
        return buf
    if i0 < 0:
        sig, i0 = sig[-i0:], 0
    n = min(len(sig), N - i0)
    if n > 0:
        buf[i0:i0 + n] += sig[:n] * gain
    return buf


def onepole_lp(x, cutoff):
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


def make_ir(length=1.2, decay=0.26, damp=4600.0):
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
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = onepole_hp(onepole_lp(rng.normal(0, 1, n), hi), lo)
    return x * (np.sin(np.pi * (t / t[-1]) ** shape) ** 1.6)


# ---------------------------------------------------------------- instruments


def _cache(fn):
    """Les sons sont identiques d'une occurrence a l'autre : on les calcule
    une fois puis on les recopie sur la grille."""
    store = {}

    def wrapped(*a):
        if a not in store:
            store[a] = fn(*a)
        return store[a]
    return wrapped


@_cache
def kick(dur=0.40):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 48 + 105 * np.exp(-t / 0.020)           # chute de hauteur : le claquement
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.15)
    click = onepole_lp(rng.normal(0, 1, n), 3500) * np.exp(-t / 0.005) * 0.45
    return (body + click) * 0.85


@_cache
def clap(dur=0.32):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = onepole_hp(onepole_lp(rng.normal(0, 1, n), 3400), 900)
    env = np.exp(-t / 0.075)
    for d in (0.009, 0.018, 0.027):             # reprises rapides : effet clap
        i = int(d * SR)
        env[i:] += np.exp(-t[:n - i] / 0.045) * 0.55
    return x * env * 0.34


@_cache
def hat(open_=False):
    dur = 0.17 if open_ else 0.06
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = onepole_hp(rng.normal(0, 1, n), 7200)
    return x * np.exp(-t / (0.055 if open_ else 0.011)) * 0.30


@_cache
def bass(freq, dur=0.21):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * t) + 0.28 * np.sin(4 * np.pi * freq * t)
    env = np.minimum(1.0, t / 0.004) * np.exp(-t / (dur * 0.45))
    return x * env * 0.42


@_cache
def pluck(freq, dur=0.24):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * freq * t)
         + 0.45 * np.sin(4 * np.pi * freq * t + 0.5)
         + 0.22 * np.sin(6 * np.pi * freq * t))
    return onepole_lp(x, 2600) * np.exp(-t / 0.085) * 0.24


# ---------------------------------------------------------------- arrangement

# progression en la mineur, une couleur par mesure
PROG = [
    (110.00, [220.00, 261.63, 329.63]),   # Am
    (110.00, [220.00, 261.63, 329.63]),   # Am
    (87.31, [174.61, 220.00, 261.63]),    # F
    (98.00, [196.00, 246.94, 293.66]),    # G
    (110.00, [220.00, 261.63, 329.63]),   # Am
    (98.00, [196.00, 246.94, 293.66]),    # G  — mesure de montee
    (110.00, [220.00, 261.63, 329.63]),   # Am — reveal
    (110.00, [220.00, 261.63, 329.63]),   # Am
]

REVEAL_BAR = int(round(TM.ZEN_IN / BAR))        # mesure ou tombe la reveal
BUILD_BAR = REVEAL_BAR - 1
STOP = TM.FINAL_IN + 0.02                       # les percussions s'arretent la

dry = np.zeros(N)
send = np.zeros(N)

arp_i = 0
for b in range(N_BARS):
    root, notes = PROG[b % len(PROG)]
    t_bar = b * BAR

    for j in range(4):
        tb = t_bar + j * BEAT
        if tb > DUR:
            break
        # le dernier temps avant la reveal est vide : tout retombe, puis ca claque
        gap = (b == BUILD_BAR and j == 3)

        # --- kick : quatre au sol, de plus en plus present
        if tb <= STOP and not gap:
            g = 0.55 if b < 2 else (0.85 if b < REVEAL_BAR else 1.0)
            add(dry, kick(), tb, g)
            add(send, kick(), tb, g * 0.12)

        # --- clap sur les temps 2 et 4
        if b >= 2 and j in (1, 3) and tb <= STOP and not gap:
            g = 0.5 if b < REVEAL_BAR else 0.62
            add(dry, clap(), tb, g)
            add(send, clap(), tb, g * 0.5)

        # --- charleston : contretemps, puis croches, puis doubles sur la montee
        if tb <= STOP:
            if b == BUILD_BAR:
                steps = [0.0, 0.25, 0.5, 0.75]
            elif b >= 3:
                steps = [0.0, 0.5]
            elif b >= 1:
                steps = [0.5]
            else:
                steps = []
            for st in steps:
                th = tb + st * BEAT
                if th > DUR:
                    break
                is_open = (st == 0.5 and b >= 3 and j == 3)
                add(dry, hat(is_open), th, 0.55 if st else 0.38)

        # --- basse : fondamentale sur le temps, relance a l'octave en contretemps
        if b >= 2 and tb <= STOP and not gap:
            add(dry, bass(root, 0.26), tb, 0.9 if j == 0 else 0.55)
            if b != BUILD_BAR or j < 2:
                add(dry, bass(root * 2, 0.16), tb + 0.5 * BEAT, 0.35)

        # --- arpege
        if b >= 3 and tb <= STOP:
            for st in (0.0, 0.5):
                ta = tb + st * BEAT
                if ta > DUR:
                    break
                g = 0.85 if b < REVEAL_BAR else 1.15
                note = notes[arp_i % len(notes)]
                add(dry, pluck(note), ta, g)
                add(send, pluck(note), ta, g * 0.45)
                arp_i += 1

# roulement de claps qui se resserre sur le dernier temps avant la reveal
for k in range(6):
    add(dry, clap(), TM.ZEN_IN - BEAT + BEAT * (k / 6.0) ** 1.35, 0.22 + 0.05 * k)

# ---------------------------------------------------------------- nappes

pad_env = smoothstep(T / 0.8) * (1.0 - smoothstep((T - (TM.FINAL_IN + 0.35)) / 0.55))
sub = 0.55 * np.sin(2 * np.pi * 55.0 * T) + 0.18 * np.sin(2 * np.pi * 110.0 * T + 0.4)
dry += sub * pad_env * 0.10

cut = 420 + 1600 * smoothstep((T - (TM.ZEN_IN - 2.4)) / 2.4)
pad = onepole_hp(onepole_lp(rng.normal(0, 1, N), cut), 110.0) * 0.045 * pad_env
dry += pad
send += pad * 0.5

sh_env = smoothstep((T - TM.ZEN_IN) / 0.35) * (1.0 - smoothstep((T - (TM.FINAL_IN + 0.3)) / 0.6))
shimmer = (0.6 * np.sin(2 * np.pi * 440.0 * T)
           + 0.4 * np.sin(2 * np.pi * 659.3 * T + 0.7)
           + 0.3 * np.sin(2 * np.pi * 880.0 * T + 1.9))
dry += shimmer * sh_env * 0.026
send += shimmer * sh_env * 0.016

# ---------------------------------------------------------------- reperes

# ticks tres discrets sur les mots : le groove porte deja le rythme
for key, wt in TM.ALL_WORD_TIMES:
    add(dry, noise_burst(0.04, 2600, 12000), wt, 0.045 if key == "s5" else 0.03)

# impacts des deux chutes : elles tombent sur un temps, donc sur un kick
for imp in TM.IMPACTS:
    e = env_exp(imp, 0.28)
    body = np.sin(2 * np.pi * 46.0 * (T - imp) * (T >= imp)) * e * 0.38
    click = onepole_lp(rng.normal(0, 1, N), 900.0) * env_exp(imp, 0.03) * 0.26
    dry += body + click
    send += (body + click) * 0.4

# whooshes sur les sorties en vrille
for wt in TM.WHIPS:
    if wt > TM.ZEN_IN - 1.0:
        continue                        # la derniere est couverte par le riser
    wh = noise_burst(0.24, 420, 6500, shape=0.75)
    add(dry, wh, wt - 0.04, 0.17)
    add(send, wh, wt - 0.04, 0.09)

# riser sur toute la mesure de montee
ri = int((TM.ZEN_IN - BAR) * SR)
rn = int(BAR * SR)
rt = np.arange(rn) / SR
riser = onepole_lp(rng.normal(0, 1, rn), 300 * (1 + 14 * (rt / rt[-1]) ** 2.2))
riser = onepole_hp(riser, 200 + 1600 * (rt / rt[-1]) ** 2)
riser *= (rt / rt[-1]) ** 2.0 * 0.26
riser *= 1.0 - smoothstep((rt - (rt[-1] - 0.08)) / 0.08)
dry[ri:ri + rn] += riser
send[ri:ri + rn] += riser * 0.4

# whoosh + pop + boom sur la reveal
wi = int((TM.ZEN_IN - 0.55) * SR)
wn = int(0.57 * SR)
wt_ = np.arange(wn) / SR
wh = onepole_hp(onepole_lp(rng.normal(0, 1, wn),
                           500 * (1 + 9 * (wt_ / wt_[-1]) ** 1.6)), 350.0)
wh *= np.sin(np.pi * (wt_ / wt_[-1]) ** 0.8) ** 1.5 * 0.40
dry[wi:wi + wn] += wh
send[wi:wi + wn] += wh * 0.5

pn = int(0.14 * SR)
pt_ = np.arange(pn) / SR
ppop = np.sin(2 * np.pi * np.cumsum(1100 * np.exp(-pt_ / 0.020) + 150) / SR)
ppop *= np.exp(-pt_ / 0.030) * 0.50
add(dry, ppop, TM.ZEN_IN)
add(send, ppop, TM.ZEN_IN, 0.5)

be = env_exp(TM.ZEN_IN, 0.50)
dry += np.sin(2 * np.pi * 48.0 * (T - TM.ZEN_IN) * (T >= TM.ZEN_IN)) * be * 0.45

# souffle d'apparition du carton final
dry += onepole_hp(rng.normal(0, 1, N), 1800.0) * env_exp(TM.FINAL_IN, 0.20) * 0.05

# ---------------------------------------------------------------- mix

mix = dry + fft_convolve(send, make_ir()) * 0.28

high = onepole_hp(mix, 700.0)
low = mix - high
delay = int(0.010 * SR)
left = low + np.concatenate([np.zeros(delay), high[:-delay]]) * 0.95
right = low + high * 0.95
stereo = np.stack([left, right], axis=1)

stereo = np.tanh(stereo * 1.15) / 1.15
fi = int(0.04 * SR)
stereo[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(0.55 * SR)
stereo[-fo:] *= np.linspace(1, 0, fo)[:, None]
stereo *= 0.94 / (np.abs(stereo).max() + 1e-9)

out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
os.makedirs(out_dir, exist_ok=True)
path = os.path.join(out_dir, "zenvy_audio.wav")

pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
with wave.open(path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"audio ecrit : {path}  ({DUR:.1f}s, {60 / BEAT:.1f} BPM, {N_BARS} mesures)")
print(f"  reveal mesure {REVEAL_BAR}, montee mesure {BUILD_BAR}, "
      f"{len(TM.ALL_WORD_TIMES)} ticks, {len(TM.IMPACTS)} impacts")
