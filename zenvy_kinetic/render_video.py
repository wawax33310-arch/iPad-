#!/usr/bin/env python3
"""Zenvy — video kinetic typography 20 s, format vertical 9:16 (1080x1920).

Style : blocs de capitales Anton etires sur toute la largeur, contraste de
tailles dans chaque ligne, mots qui claquent un par un avec flou directionnel,
sorties en whip. Reveal de la marque avec le logo Zenvy.

Rendu image par image avec Pillow, encodage H.264 via ffmpeg (pipe rawvideo),
audio muxe depuis out/zenvy_audio.wav.

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

import timing as TM

# ---------------------------------------------------------------- config

W, H = 1080, 1920
FPS = TM.FPS
DUR = TM.DUR

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONT = os.path.join(HERE, "fonts", "Anton-Regular.ttf")
LOGO_PATH = os.path.join(HERE, "assets", "zenvy_logo.png")
OUT_DIR = os.path.join(ROOT, "out")

# palette calee sur le logo : bleu nuit profond, accent orange de la marque
BG_TOP = (10, 15, 42)
BG_BOT = (3, 5, 14)
COLORS = {
    TM.WHITE: (245, 247, 252),
    TM.DIM: (148, 158, 186),
    TM.ACCENT: (250, 140, 25),
}
ACCENT = COLORS[TM.ACCENT]

CX = W // 2
BLOCK_W = 936          # largeur utile des blocs de texte
BLOCK_Y = 968          # centre vertical des blocs
MAX_SIZE = 300         # garde-fou sur les lignes d'un seul mot court
BASE_SIZE = 120        # taille de reference avant etirement

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
PAD = 30  # marge autour du glyphe pour absorber le flou


def font(size):
    size = max(8, int(size))
    if size not in _font_cache:
        _font_cache[size] = ImageFont.truetype(FONT, size)
    return _font_cache[size]


class Glyph:
    """Un mot pre-rendu, cale sur sa ligne de base."""

    __slots__ = ("img", "adv", "asc", "top", "bottom")

    def __init__(self, text, size, color):
        fnt = font(size)
        self.asc, desc = fnt.getmetrics()
        self.adv = fnt.getlength(text)
        bb = fnt.getbbox(text)                 # repere : ligne d'ascendante
        self.top = bb[1] - self.asc            # encre au-dessus de la base
        self.bottom = bb[3] - self.asc         # encre sous la base
        w = int(math.ceil(self.adv)) + 2 * PAD
        h = self.asc + desc + 2 * PAD
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((PAD, PAD + self.asc), text, font=fnt,
                                fill=color + (255,), anchor="ls")
        self.img = im


def glyph(text, size, color):
    key = (text, int(size), color)
    g = _glyph_cache.get(key)
    if g is None:
        g = Glyph(text, int(size), color)
        _glyph_cache[key] = g
    return g


def build_block(seg):
    """Compose un segment : chaque ligne est etiree sur BLOCK_W.

    Retourne la liste des mots avec leur centre (cx, cy) et le rectangle du
    bloc, le tout dans un repere centre sur (CX, BLOCK_Y).
    """
    accent = seg.get("accent", set())
    base_col = COLORS[seg["color"]]

    laid = []
    for line in seg["lines"]:
        # 1re passe a taille de reference pour mesurer, puis mise a l'echelle
        sizes = [BASE_SIZE * w for _, w in line]
        widths = [font(s).getlength(txt) for (txt, _), s in zip(line, sizes)]
        space = font(BASE_SIZE * max(w for _, w in line)).getlength(" ")
        total = sum(widths) + space * (len(line) - 1)
        k = min(BLOCK_W / total, MAX_SIZE / max(sizes))
        sizes = [s * k for s in sizes]

        glyphs = []
        for (txt, _), s in zip(line, sizes):
            col = ACCENT if txt in accent else base_col
            glyphs.append(glyph(txt, s, col))
        sp = font(max(sizes)).getlength(" ")
        line_w = sum(g.adv for g in glyphs) + sp * (len(glyphs) - 1)
        laid.append({"glyphs": glyphs, "w": line_w, "sp": sp,
                     "top": min(g.top for g in glyphs),
                     "bottom": max(g.bottom for g in glyphs)})

    # empilement serre, en tenant compte de l'encre reelle (accents compris)
    gap = BASE_SIZE * 0.13
    cursor = 0.0
    for ln in laid:
        ln["baseline"] = cursor - ln["top"]
        cursor = ln["baseline"] + ln["bottom"] + gap
    total_h = cursor - gap
    shift = BLOCK_Y - total_h / 2

    items = []
    for ln in laid:
        pen = CX - ln["w"] / 2
        for g in ln["glyphs"]:
            items.append({
                "g": g,
                "cx": pen - PAD + g.img.width / 2,
                "cy": ln["baseline"] + shift - g.asc - PAD + g.img.height / 2,
            })
            pen += g.adv + ln["sp"]
    return items, shift, shift + total_h


_block_cache = {}


def block(seg):
    if seg["key"] not in _block_cache:
        _block_cache[seg["key"]] = build_block(seg)
    return _block_cache[seg["key"]]


def paste(canvas, im, cx, cy, alpha=1.0):
    if alpha <= 0.004:
        return
    if alpha < 0.996:
        a = im.getchannel("A").point(lambda v, k=alpha: int(v * k))
        im = im.copy()
        im.putalpha(a)
    canvas.alpha_composite(im, (int(round(cx - im.width / 2)),
                                int(round(cy - im.height / 2))))


def transform(g, scale=1.0, blur=0.0, sx=1.0, sy=1.0):
    im = g.img if hasattr(g, "img") else g
    tw = max(1, int(round(im.width * scale * sx)))
    th = max(1, int(round(im.height * scale * sy)))
    if (tw, th) != im.size:
        im = im.resize((tw, th), Image.BILINEAR)
    if blur > 0.35:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return im


def paste_mb(canvas, im, cx, cy, alpha, vx, vy, samples=8):
    """Flou de mouvement par accumulation le long du vecteur vitesse."""
    d = math.hypot(vx, vy)
    if d < 2.0 or samples <= 1:
        paste(canvas, im, cx, cy, alpha)
        return
    n = min(samples, max(2, int(d / 7)))
    a = alpha / n
    for i in range(n):
        f = (i / (n - 1) - 0.5)
        paste(canvas, im, cx + vx * f, cy + vy * f, a)


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
    bg += np.exp(-r2 * 2.4)[..., None] * np.array([12, 16, 34], dtype=np.float32)
    bg *= np.clip(1.0 - 0.44 * r2, 0.40, 1.0)[..., None]
    return np.clip(bg, 0, 255).astype(np.uint8)


def build_glow():
    xx = (np.arange(W, dtype=np.float32) - CX) / (W * 0.52)
    yy = (np.arange(H, dtype=np.float32) - H * 0.44) / (H * 0.32)
    r2 = xx[None, :] ** 2 + yy[:, None] ** 2
    return np.exp(-r2 * 2.0).astype(np.float32)


BG = build_background()
GLOW = build_glow()
ACCENT_F = np.array(ACCENT, dtype=np.float32)
_rng = np.random.default_rng(7)
GRAIN = [(_rng.normal(0, 1.7, (H, W))).astype(np.int16) for _ in range(8)]

LOGO = Image.open(LOGO_PATH).convert("RGBA")
LOGO_H = 540
LOGO = LOGO.resize((int(LOGO.width * LOGO_H / LOGO.height), LOGO_H), Image.LANCZOS)
_logo_scaled = {}


def logo_at(scale):
    k = round(scale, 3)
    if k not in _logo_scaled:
        w = max(1, int(LOGO.width * k))
        h = max(1, int(LOGO.height * k))
        _logo_scaled[k] = LOGO.resize((w, h), Image.LANCZOS)
    return _logo_scaled[k]


# ---------------------------------------------------------------- marque

MARK_Y = 812      # centre du logo pendant la reveal
WORD_Y = 1198     # ligne de base du mot ZENVY
WORD_SIZE = 210
WORD_TRACK = 10
FINAL_Y = 1130
BRAND_SHRINK = 0.52
BRAND_UP = -140.0


def brand_state(t):
    """Echelle, decalage vertical et intensite du halo du bloc marque."""
    p = clamp01((t - TM.ZEN_IN) / 0.34)
    scale = 0.68 + 0.32 * ease_out_back(p, 2.2)
    u = max(0.0, t - (TM.ZEN_IN + 0.32))
    pulse = math.sin(2 * math.pi * 1.5 * u) * math.exp(-u / 1.7)
    scale *= 1.0 + 0.020 * pulse

    dy = 0.0
    k = clamp01((t - TM.ZEN_SHRINK) / TM.ZEN_SHRINK_D)
    if k > 0:
        e = ease_in_out_cubic(k)
        scale *= 1.0 + (BRAND_SHRINK - 1.0) * e
        dy = BRAND_UP * e

    glow = ease_out_cubic(clamp01((t - TM.ZEN_IN) / 0.20))
    glow *= 0.70 + 0.30 * math.exp(-max(0.0, t - TM.ZEN_IN) / 1.5)
    glow *= 1.0 + 0.25 * pulse
    glow *= 1.0 - 0.55 * k
    return scale, dy, glow, p


def draw_tracked(canvas, text, size, color, cy_center, scale, alpha, track,
                 ox, oy, blur=0.0):
    """Texte en capitales avec interlettrage, centre optiquement."""
    fnt = font(size)
    asc, _ = fnt.getmetrics()
    advs = [fnt.getlength(c) for c in text]
    total = sum(advs) + track * (len(text) - 1)
    bb = fnt.getbbox(text)
    baseline = cy_center - ((bb[1] + bb[3]) / 2 - asc) * scale

    pen = -total / 2
    for ch, adv in zip(text, advs):
        if ch != " ":
            g = glyph(ch, size, color)
            im = transform(g, scale, blur)
            paste(canvas, im, CX + (pen - PAD + g.img.width / 2) * scale + ox,
                  baseline + (-g.asc - PAD + g.img.height / 2) * scale + oy, alpha)
        pen += adv + track


def draw_brand(canvas, t, ox, oy):
    if t < TM.ZEN_IN - 0.02:
        return
    scale, dy, _, p = brand_state(t)
    a = clamp01((t - TM.ZEN_IN) / 0.12)
    blur = 6.0 * (1 - clamp01((t - TM.ZEN_IN) / 0.22))

    entry = 26.0 * (1 - ease_out_expo(p))

    mark = logo_at(scale)
    if blur > 0.35:
        mark = mark.filter(ImageFilter.GaussianBlur(blur))
    paste(canvas, mark, CX + ox, MARK_Y + dy + entry + oy, a)

    # le mot reste solidaire du logo : il s'ecarte proportionnellement a l'echelle
    word_cy = MARK_Y + dy + (WORD_Y - MARK_Y) * scale
    track = WORD_TRACK + 60 * (1 - ease_out_expo(clamp01((t - TM.ZEN_IN) / 0.45)))
    draw_tracked(canvas, "ZENVY", WORD_SIZE, ACCENT, word_cy, scale, a, track,
                 ox, oy + entry, blur)


def draw_final(canvas, t, ox, oy):
    if t < TM.FINAL_IN:
        return
    p = clamp01((t - TM.FINAL_IN) / 0.30)
    a = ease_out_cubic(p)
    dy = 16.0 * (1 - ease_out_expo(p))

    size = 62
    fnt = font(size)
    track = 7.0
    parts = [("BORDEAUX", COLORS[TM.WHITE]), ("—", COLORS[TM.DIM]), ("20 AOÛT", ACCENT)]
    gap = fnt.getlength(" ") * 1.6
    widths = [sum(fnt.getlength(c) for c in txt) + track * (len(txt) - 1)
              for txt, _ in parts]
    total = sum(widths) + gap * (len(parts) - 1)
    asc, _ = fnt.getmetrics()
    bb = fnt.getbbox("BORDEAUX")
    baseline = FINAL_Y - ((bb[1] + bb[3]) / 2 - asc)

    # filet accent au-dessus du carton
    lw = 104 * a
    if lw > 1:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ly = FINAL_Y - 66 + dy + oy
        ImageDraw.Draw(ov).rounded_rectangle(
            [CX - lw / 2 + ox, ly - 2, CX + lw / 2 + ox, ly + 2],
            radius=2, fill=ACCENT + (int(220 * a),))
        canvas.alpha_composite(ov)

    pen = CX - total / 2
    for (txt, col), wdt in zip(parts, widths):
        for ch in txt:
            g = glyph(ch, size, col)
            paste(canvas, g.img, pen - PAD + g.img.width / 2 + ox,
                  baseline - g.asc - PAD + g.img.height / 2 + dy + oy, a)
            pen += fnt.getlength(ch) + track
        pen += gap - track


# ---------------------------------------------------------------- segments


def seg_alive(seg, t):
    end = seg["out"] + seg["outdur"]
    start = seg["start"] - 0.05
    return start <= t <= end


def draw_segment(canvas, seg, t, ox, oy):
    if not seg_alive(seg, t):
        return
    items, top, bottom = block(seg)

    # respiration du bloc : leger push-in pendant la tenue
    hold = clamp01((t - seg["start"]) / max(0.4, seg["out"] - seg["start"]))
    push = 1.0 + 0.045 * ease_out_cubic(hold)
    if seg["key"] == "s5":
        push = 1.0 + 0.11 * ease_in_out_cubic(hold)   # le ton monte

    # sortie : whip lateral ou zoom avant
    op = clamp01((t - seg["out"]) / seg["outdur"])
    wx, wy = seg["whip"]
    out_a = 1.0 - ease_in_quad(op) ** 0.85
    e = ease_in_quad(op)
    off_x, off_y = wx * 1180.0 * e, wy * 900.0 * e
    vx, vy = wx * 240.0 * op, wy * 200.0 * op
    if seg["key"] == "s5":
        push *= 1.0 + 1.05 * e                        # explose vers la camera
        vx = vy = 0.0

    for i, it in enumerate(items):
        if seg["mode"] == "punch":
            p = clamp01((t - (seg["start"] + i * seg["stagger"])) / seg["punch"])
            if p <= 0:
                continue
            a = clamp01(p / 0.30) * out_a
            s = push * (1.0 + 0.30 * (1 - ease_out_expo(p)))
            dy = 34.0 * (1 - ease_out_expo(p))
            mb = 150.0 * (1 - p) ** 2          # trainee verticale du claquement
            blur = 3.0 * (1 - clamp01(p / 0.35))
            sx = sy = 1.0
        else:
            land = TM.land_time(seg)
            if t < land:
                p = clamp01((t - seg["start"]) / seg["fall"])
                a = clamp01(p / 0.35) * out_a
                dy = -420.0 * (1 - ease_in_quad(p))
                mb = 300.0 * (1 - p)           # trainee de la chute
                s, blur, sx, sy = push, 1.5, 1.0, 1.0
            else:
                u = t - land
                q = math.exp(-u * 9.0) * math.cos(2 * math.pi * 3.2 * u)
                sx, sy = 1.0 + 0.13 * q, 1.0 - 0.20 * q
                a, dy, mb, blur, s = out_a, 0.0, 0.0, 0.0, push

        cx = CX + (it["cx"] - CX) * s
        cy = BLOCK_Y + (it["cy"] - BLOCK_Y) * s
        if sx != 1.0 or sy != 1.0:
            # ecrasement ancre sur le bas du bloc : les mots gardent les pieds au sol
            bottom_s = BLOCK_Y + (bottom - BLOCK_Y) * s
            cy = bottom_s - (bottom_s - cy) * sy
            cx = CX + (cx - CX) * sx

        im = transform(it["g"], s, blur + 4.0 * op, sx, sy)
        paste_mb(canvas, im, cx + off_x + ox, cy + dy + off_y + oy, a,
                 vx, vy - mb)


# ---------------------------------------------------------------- frame


def shake(t):
    dx = dy = 0.0
    for t0, amp in [(TM.IMPACTS[0], 17.0), (TM.IMPACTS[1], 17.0), (TM.ZEN_IN, 24.0)]:
        u = t - t0
        if 0 <= u < 0.45:
            k = math.exp(-u * 11.0) * amp
            dx += math.sin(u * 78.0) * k * 0.45
            dy += math.sin(u * 64.0 + 1.1) * k
    return dx, dy


def render_frame(t):
    ox, oy = shake(t)
    oy += math.sin(t * 0.55) * 4.0

    canvas = Image.frombuffer("RGB", (W, H), BG.tobytes(), "raw", "RGB", 0, 1).convert("RGBA")

    for seg in TM.SEGMENTS:
        draw_segment(canvas, seg, t, ox, oy)
    draw_brand(canvas, t, ox, oy)
    draw_final(canvas, t, ox, oy)

    frame = np.asarray(canvas.convert("RGB"), dtype=np.float32)

    if t >= TM.ZEN_IN - 0.05:
        glow = brand_state(t)[2]
        if glow > 0.01:
            frame += GLOW[..., None] * ACCENT_F[None, None, :] * (0.15 * glow)

    fu = t - TM.ZEN_IN
    if 0 <= fu < 0.30:
        frame += (255.0 - frame) * min(0.62 * math.exp(-fu / 0.045), 0.92)

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
