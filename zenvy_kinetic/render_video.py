#!/usr/bin/env python3
"""Zenvy — video kinetic typography 20 s, format vertical 9:16 (1080x1920).

Rendu image par image avec Pillow, encodage H.264 via ffmpeg (pipe rawvideo),
audio muxe depuis out/zenvy_audio.wav.

Sequence :
  0-4 s    "On a tous ce moment ou on veut sortir..."  mot a mot, doux
  4-7 s    "...mais personne n'est dispo."             chute + ecrasement
  7-10 s   "Ou on est dispo..."                        reprise douce
  10-13 s  "...mais on sait pas ou aller."             deuxieme chute
  13-16 s  "Et si on savait tout, tout de suite ?"     rapide, ca monte
  16-19 s  "Zenvy"                                     flash + pulse, accent
  19-20 s  "Bordeaux, 20 aout."                        carton final fixe

Usage :
  python3 render_video.py                 # rendu complet
  python3 render_video.py --stills 1,5,16 # exporte des PNG de controle
"""

import argparse
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------- config

W, H = 1080, 1920
FPS = 60
DUR = 20.0

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONT_BOLD = os.path.join(HERE, "fonts", "Poppins-Bold.ttf")
FONT_XBOLD = os.path.join(HERE, "fonts", "Poppins-ExtraBold.ttf")
OUT_DIR = os.path.join(ROOT, "out")

# palette : fond bleu nuit profond, un seul accent (vert menthe)
BG_TOP = (11, 18, 34)
BG_BOT = (4, 6, 13)
WHITE = (244, 247, 251)
DIM = (176, 186, 203)      # segments "qui retombent"
ACCENT = (46, 230, 168)    # vert menthe, uniquement sur les mots cles

CX = W // 2

# ---------------------------------------------------------------- easing


def clamp01(x):
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


def ease_out_expo(x):
    x = clamp01(x)
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def ease_out_cubic(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_in_quad(x):
    x = clamp01(x)
    return x * x


def ease_in_out_cubic(x):
    x = clamp01(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out_back(x, s=1.9):
    x = clamp01(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


# ---------------------------------------------------------------- glyphes

_font_cache = {}
_glyph_cache = {}
PAD = 26  # marge autour du glyphe pour absorber le flou


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


class Glyph:
    """Un mot pre-rendu, cale sur sa ligne de base pour un layout stable."""

    __slots__ = ("img", "adv", "asc", "desc")

    def __init__(self, text, fnt, color):
        self.asc, self.desc = fnt.getmetrics()
        self.adv = fnt.getlength(text)
        w = int(math.ceil(self.adv)) + 2 * PAD
        h = self.asc + self.desc + 2 * PAD
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.text((PAD, PAD + self.asc), text, font=fnt, fill=color + (255,), anchor="ls")
        self.img = im


def glyph(text, fnt_path, size, color):
    key = (text, fnt_path, size, color)
    g = _glyph_cache.get(key)
    if g is None:
        g = Glyph(text, font(fnt_path, size), color)
        _glyph_cache[key] = g
    return g


def layout(tokens, fnt_path, size, color, max_width, center_y, line_gap=1.14):
    """Repartit les mots sur plusieurs lignes centrees.

    Retourne (items, block_top, block_bottom) ou chaque item porte le centre
    (cx, cy) du rectangle naturel du glyphe.
    """
    fnt = font(fnt_path, size)
    space = fnt.getlength(" ")
    lines, cur, cur_w = [], [], 0.0
    for tok in tokens:
        adv = fnt.getlength(tok)
        add_w = adv if not cur else cur_w + space + adv
        if cur and add_w > max_width:
            lines.append((cur, cur_w))
            cur, cur_w = [tok], adv
        else:
            cur, cur_w = cur + [tok], add_w
    if cur:
        lines.append((cur, cur_w))

    asc, desc = fnt.getmetrics()
    line_h = (asc + desc) * line_gap
    total_h = line_h * len(lines)
    top = center_y - total_h / 2

    items = []
    for li, (words, line_w) in enumerate(lines):
        baseline = top + asc + li * line_h
        pen = CX - line_w / 2
        for word in words:
            g = glyph(word, fnt_path, size, color[word] if isinstance(color, dict) else color)
            items.append({
                "g": g,
                "cx": pen - PAD + g.img.width / 2,
                "cy": baseline - g.asc - PAD + g.img.height / 2,
                "line": li,
            })
            pen += g.adv + space
    return items, top, top + total_h


def paste(canvas, g, cx, cy, scale=1.0, alpha=1.0, blur=0.0, sx=1.0, sy=1.0):
    if alpha <= 0.004:
        return
    im = g.img
    tw = max(1, int(round(im.width * scale * sx)))
    th = max(1, int(round(im.height * scale * sy)))
    if (tw, th) != im.size:
        im = im.resize((tw, th), Image.BILINEAR)
    if blur > 0.35:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    if alpha < 0.996:
        a = im.getchannel("A").point(lambda v, k=alpha: int(v * k))
        im = im.copy()
        im.putalpha(a)
    canvas.alpha_composite(im, (int(round(cx - tw / 2)), int(round(cy - th / 2))))


# ---------------------------------------------------------------- decor


def build_background():
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    top = np.array(BG_TOP, dtype=np.float32)
    bot = np.array(BG_BOT, dtype=np.float32)
    bg = top[None, None, :] * (1 - y[..., None]) + bot[None, None, :] * y[..., None]
    bg = np.repeat(bg, W, axis=1)

    xx = (np.arange(W, dtype=np.float32) - CX) / (W * 0.62)
    yy = (np.arange(H, dtype=np.float32) - H * 0.47) / (H * 0.55)
    r2 = xx[None, :] ** 2 + yy[:, None] ** 2

    # halo froid tres discret au centre
    bg += np.exp(-r2 * 2.4)[..., None] * np.array([10, 16, 30], dtype=np.float32)
    # vignette
    bg *= np.clip(1.0 - 0.42 * r2, 0.42, 1.0)[..., None]
    return np.clip(bg, 0, 255).astype(np.uint8)


def build_glow():
    """Masque radial reutilise pour le halo accent derriere 'Zenvy'."""
    xx = (np.arange(W, dtype=np.float32) - CX) / (W * 0.48)
    yy = (np.arange(H, dtype=np.float32) - H * 0.49) / (H * 0.34)
    r2 = xx[None, :] ** 2 + yy[:, None] ** 2
    return np.exp(-r2 * 2.0).astype(np.float32)


BG = build_background()
GLOW = build_glow()
ACCENT_F = np.array(ACCENT, dtype=np.float32)
_rng = np.random.default_rng(7)
# grain leger : casse le banding du degrade sans faire exploser le debit
GRAIN = [(_rng.normal(0, 1.7, (H, W))).astype(np.int16) for _ in range(8)]

# ---------------------------------------------------------------- sequence

S1 = {
    "tokens": "On a tous ce moment où on veut sortir…".split(),
    "size": 78, "maxw": 860, "y": 962,
    "start": 0.30, "gap": 0.30, "rev": 0.55,
    "out": 3.78, "outdur": 0.26,
}
S3 = {
    "tokens": "Ou on est dispo…".split(),
    "size": 78, "maxw": 860, "y": 962,
    "start": 7.18, "gap": 0.26, "rev": 0.50,
    "out": 9.76, "outdur": 0.24,
}
S2 = {
    "tokens": "…mais personne n’est dispo.".split(),
    "size": 94, "maxw": 900, "y": 962,
    "drop": 4.12, "fall": 0.30, "out": 6.74, "outdur": 0.26,
}
S4 = {
    "tokens": "…mais on sait pas où aller.".split(),
    "size": 94, "maxw": 900, "y": 962,
    "drop": 10.10, "fall": 0.30, "out": 12.74, "outdur": 0.26,
}
S5 = {
    "tokens": ["Et", "si", "on", "savait", "tout,", "tout", "de", "suite ?"],
    "accent": {"tout", "de", "suite ?"},
    "size": 106, "maxw": 900, "y": 962,
    "start": 13.08, "gap": 0.145, "rev": 0.30,
    "out": 15.58, "outdur": 0.24,
}

ZEN_IN = 16.0        # impact / flash
ZEN_SHRINK = 18.55   # le mot recule pour laisser place au carton final
ZEN_SHRINK_D = 0.42
ZEN_Y_BIG, ZEN_Y_SMALL = 946.0, 806.0
ZEN_S_SMALL = 0.50
FINAL_IN = 19.0


def fit_size(text, fnt_path, target_w, lo=80, hi=460):
    """Plus grande taille dont la largeur reste sous target_w."""
    best = lo
    while lo <= hi:
        mid = (lo + hi) // 2
        if font(fnt_path, mid).getlength(text) <= target_w:
            best, lo = mid, mid + 1
        else:
            hi = mid - 1
    return best


ZEN_SIZE = fit_size("Zenvy", FONT_XBOLD, 830)
ZEN_LETTERS = list("Zenvy")


def shake(t):
    """Secousse courte sur les deux impacts + sur la reveal."""
    dx = dy = 0.0
    for t0, amp in ((4.42, 15.0), (10.36, 15.0), (16.0, 22.0)):
        u = t - t0
        if 0 <= u < 0.45:
            k = math.exp(-u * 11.0) * amp
            dx += math.sin(u * 78.0) * k * 0.45
            dy += math.sin(u * 64.0 + 1.1) * k
    return dx, dy


def breathe(t):
    """Micro-derive verticale : evite l'image figee."""
    return math.sin(t * 0.55) * 5.0


# ---------------------------------------------------------------- segments


def draw_soft_block(canvas, cfg, t, ox, oy):
    """Segments 1 et 3 : construction mot a mot, apparition douce."""
    end = cfg["out"] + cfg["outdur"]
    if not (cfg["start"] - 0.05 <= t <= end):
        return
    items, _, _ = layout(cfg["tokens"], FONT_BOLD, cfg["size"], WHITE, cfg["maxw"], cfg["y"])

    # sortie du bloc entier
    op = clamp01((t - cfg["out"]) / cfg["outdur"])
    out_a = 1.0 - ease_in_quad(op)
    out_dy = -34.0 * ease_in_quad(op)
    out_blur = 7.0 * op

    for i, it in enumerate(items):
        p = clamp01((t - (cfg["start"] + i * cfg["gap"])) / cfg["rev"])
        if p <= 0:
            continue
        a = ease_out_cubic(p) * out_a
        dy = 26.0 * (1 - ease_out_expo(p)) + out_dy
        blur = max(6.5 * (1 - ease_out_cubic(min(1.0, p / 0.55))), out_blur)
        s = 0.965 + 0.035 * ease_out_expo(p)
        paste(canvas, it["g"], it["cx"] + ox, it["cy"] + dy + oy, s, a, blur)


def draw_drop_block(canvas, cfg, t, ox, oy):
    """Segments 2 et 4 : le bloc tombe et s'ecrase, l'ambiance retombe."""
    end = cfg["out"] + cfg["outdur"]
    if not (cfg["drop"] - 0.05 <= t <= end):
        return
    items, top, bottom = layout(cfg["tokens"], FONT_BOLD, cfg["size"], DIM, cfg["maxw"], cfg["y"])

    land = cfg["drop"] + cfg["fall"]
    if t < land:
        p = clamp01((t - cfg["drop"]) / cfg["fall"])
        dy = -300.0 * (1 - ease_in_quad(p))
        a = clamp01(p / 0.42)
        blur = 5.5 * (1 - p) + 1.0
        sx = sy = 1.0
    else:
        u = t - land
        q = math.exp(-u * 8.5) * math.cos(2 * math.pi * 3.1 * u)
        sy = 1.0 - 0.19 * q
        sx = 1.0 + 0.12 * q
        dy = 0.0
        a = 1.0
        blur = 0.0

    op = clamp01((t - cfg["out"]) / cfg["outdur"])
    a *= 1.0 - ease_in_quad(op)
    dy += 22.0 * ease_in_quad(op)
    blur = max(blur, 6.0 * op)

    for it in items:
        # ecrasement ancre sur le bas du bloc : les mots gardent les pieds au sol
        cy = bottom - (bottom - it["cy"]) * sy
        cx = CX + (it["cx"] - CX) * sx
        paste(canvas, it["g"], cx + ox, cy + dy + oy, 1.0, a, blur, sx, sy)


def draw_fast_block(canvas, cfg, t, ox, oy):
    """Segment 5 : plus rapide, le texte grossit, le ton monte."""
    end = cfg["out"] + cfg["outdur"]
    if not (cfg["start"] - 0.05 <= t <= end):
        return
    colors = {tok: (ACCENT if tok in cfg["accent"] else WHITE) for tok in cfg["tokens"]}
    items, _, _ = layout(cfg["tokens"], FONT_BOLD, cfg["size"], colors, cfg["maxw"], cfg["y"])

    grow = 1.0 + 0.10 * ease_in_out_cubic((t - cfg["start"]) / (cfg["out"] - cfg["start"]))
    op = clamp01((t - cfg["out"]) / cfg["outdur"])
    out_a = 1.0 - ease_in_quad(op)
    grow *= 1.0 + 0.09 * op
    out_blur = 9.0 * op

    for i, it in enumerate(items):
        p = clamp01((t - (cfg["start"] + i * cfg["gap"])) / cfg["rev"])
        if p <= 0:
            continue
        a = clamp01(p / 0.35) * out_a
        pop = 1.0 + 0.16 * (1 - ease_out_back(p))
        dy = 16.0 * (1 - ease_out_expo(p))
        blur = max(4.0 * (1 - clamp01(p / 0.4)), out_blur)
        cx = CX + (it["cx"] - CX) * grow
        cy = cfg["y"] + (it["cy"] - cfg["y"]) * grow
        paste(canvas, it["g"], cx + ox, cy + dy + oy, grow * pop, a, blur)


def zenvy_state(t):
    """Echelle, position et intensite du halo pour le mot 'Zenvy'."""
    p = clamp01((t - ZEN_IN) / 0.38)
    scale = 0.70 + 0.30 * ease_out_back(p, 2.1)
    u = max(0.0, t - (ZEN_IN + 0.36))
    scale *= 1.0 + 0.022 * math.sin(2 * math.pi * 1.45 * u) * math.exp(-u / 1.9)
    y = ZEN_Y_BIG
    k = clamp01((t - ZEN_SHRINK) / ZEN_SHRINK_D)
    if k > 0:
        e = ease_in_out_cubic(k)
        scale *= 1.0 + (ZEN_S_SMALL - 1.0) * e
        y = ZEN_Y_BIG + (ZEN_Y_SMALL - ZEN_Y_BIG) * e
    track = 44.0 * (1 - ease_out_expo(clamp01((t - ZEN_IN) / 0.5))) + 4.0
    glow = ease_out_cubic(clamp01((t - ZEN_IN) / 0.22))
    glow *= 0.72 + 0.28 * math.exp(-max(0.0, t - ZEN_IN) / 1.6)
    glow *= 1.0 + 0.22 * math.sin(2 * math.pi * 1.45 * u) * math.exp(-u / 2.2)
    glow *= 1.0 - 0.55 * clamp01((t - ZEN_SHRINK) / ZEN_SHRINK_D)
    return scale, y, track, glow


def draw_zenvy(canvas, t, ox, oy):
    if t < ZEN_IN - 0.02:
        return
    scale, y, track, _ = zenvy_state(t)
    fnt = font(FONT_XBOLD, ZEN_SIZE)
    asc, _ = fnt.getmetrics()
    advs = [fnt.getlength(c) for c in ZEN_LETTERS]
    total = sum(advs) + track * (len(ZEN_LETTERS) - 1)

    # centrage optique sur l'encre reelle du mot, pas sur la boite de police
    bb = fnt.getbbox("Zenvy")
    ink_mid = (bb[1] + bb[3]) / 2 - asc
    baseline = y - ink_mid * scale

    pen = -total / 2
    for i, ch in enumerate(ZEN_LETTERS):
        g = glyph(ch, FONT_XBOLD, ZEN_SIZE, ACCENT)
        lx = pen - PAD + g.img.width / 2
        ly = -g.asc - PAD + g.img.height / 2
        # micro-decalage par lettre : le mot arrive d'un bloc, avec du relief
        p = clamp01((t - (ZEN_IN + i * 0.012)) / 0.26)
        a = clamp01(p / 0.22)
        dy = 20.0 * (1 - ease_out_expo(p))
        paste(canvas, g, CX + lx * scale + ox,
              baseline + ly * scale + dy + oy, scale, a,
              4.0 * (1 - clamp01(p / 0.30)))
        pen += advs[i] + track


def draw_final(canvas, t, ox, oy):
    if t < FINAL_IN:
        return
    p = clamp01((t - FINAL_IN) / 0.34)
    a = ease_out_cubic(p)
    dy = 18.0 * (1 - ease_out_expo(p))
    size = 60
    fnt = font(FONT_BOLD, size)
    parts = [("Bordeaux,", WHITE), ("20 août.", ACCENT)]
    space = fnt.getlength(" ")
    total = sum(fnt.getlength(s) for s, _ in parts) + space
    y = 1128.0
    asc, _ = fnt.getmetrics()

    # filet accent discret au-dessus du carton
    line_w = 96 * a
    if line_w > 1:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        ly = y - 74 + dy + oy
        d.rounded_rectangle(
            [CX - line_w / 2 + ox, ly - 2, CX + line_w / 2 + ox, ly + 2],
            radius=2, fill=ACCENT + (int(210 * a),))
        canvas.alpha_composite(ov)

    pen = CX - total / 2
    for text, col in parts:
        g = glyph(text, FONT_BOLD, size, col)
        paste(canvas, g, pen - PAD + g.img.width / 2 + ox,
              y - asc - PAD + g.img.height / 2 + dy + oy, 1.0, a, 0.0)
        pen += g.adv + space


# ---------------------------------------------------------------- frame


def render_frame(t):
    ox, oy = shake(t)
    oy += breathe(t)

    canvas = Image.frombuffer("RGB", (W, H), BG.tobytes(), "raw", "RGB", 0, 1).convert("RGBA")

    draw_soft_block(canvas, S1, t, ox, oy)
    draw_drop_block(canvas, S2, t, ox, oy)
    draw_soft_block(canvas, S3, t, ox, oy)
    draw_drop_block(canvas, S4, t, ox, oy)
    draw_fast_block(canvas, S5, t, ox, oy)
    draw_zenvy(canvas, t, ox, oy)
    draw_final(canvas, t, ox, oy)

    frame = np.asarray(canvas.convert("RGB"), dtype=np.float32)

    # halo accent derriere le logo
    if t >= ZEN_IN - 0.05:
        _, _, _, glow = zenvy_state(t)
        if glow > 0.01:
            frame += GLOW[..., None] * ACCENT_F[None, None, :] * (0.30 * glow)

    # flash court sur l'impact "Zenvy"
    fu = t - ZEN_IN
    if -0.02 <= fu < 0.30:
        f = 0.62 * math.exp(-max(fu, 0.0) / 0.045)
        if fu < 0:
            f = 0.0
        frame += (255.0 - frame) * min(f, 0.92)

    frame = frame + GRAIN[int(t * FPS) % len(GRAIN)][..., None]
    return np.clip(frame, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- pilote


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", help="temps (s) separes par des virgules -> PNG de controle")
    ap.add_argument("--out", default=os.path.join(OUT_DIR, "zenvy_kinetic_20s.mp4"))
    ap.add_argument("--audio", default=os.path.join(OUT_DIR, "zenvy_audio.wav"))
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)

    if args.stills:
        for s in args.stills.split(","):
            t = float(s)
            p = os.path.join(OUT_DIR, f"still_{t:06.2f}.png")
            Image.fromarray(render_frame(t)).save(p)
            print("still :", p)
        return

    n_frames = int(round(DUR * FPS))
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    ]
    has_audio = os.path.exists(args.audio)
    if has_audio:
        cmd += ["-i", args.audio]
    cmd += [
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.2",
        "-x264-params", "keyint=120:min-keyint=60",
        "-movflags", "+faststart",
    ]
    if has_audio:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest"]
    cmd += [args.out]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n_frames):
        proc.stdin.write(render_frame(i / FPS).tobytes())
        if i % 120 == 0:
            print(f"  {i}/{n_frames} images ({i / FPS:5.2f}s)", flush=True)
    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        sys.exit(f"ffmpeg a echoue (code {rc})")
    print("video :", args.out)


if __name__ == "__main__":
    main()
