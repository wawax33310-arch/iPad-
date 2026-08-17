#!/usr/bin/env python3
"""Detoure le logo Zenvy (fond bleu nuit uni) en PNG RGBA utilisable sur
n'importe quel fond, et imprime les couleurs dominantes de la marque.

Sortie : zenvy_kinetic/assets/zenvy_logo.png
"""

import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "/root/.claude/uploads/4b990f3a-10a9-5391-90e8-f38dc4581846/2ba5f8fb-Design_sans_titre.png"
DST_DIR = os.path.join(HERE, "assets")
DST = os.path.join(DST_DIR, "zenvy_logo.png")
WORK = 1200  # taille de travail, largement suffisante pour du 1080x1920

im = Image.open(SRC).convert("RGB")
a = np.asarray(im, dtype=np.float32)
bg = np.array(im.getpixel((0, 0)), dtype=np.float32)
print("fond source :", tuple(int(v) for v in bg))

# alpha = distance a la couleur de fond ; les blobs sont tres eloignes du
# bleu nuit, un seuil bas suffit et garde les bords antialiases propres.
dist = np.linalg.norm(a - bg[None, None, :], axis=2)
alpha = np.clip(dist / 42.0, 0.0, 1.0)

# de-premultiplication : on retire la contribution du fond sur les bords
safe = np.maximum(alpha, 1e-3)[..., None]
rgb = bg[None, None, :] + (a - bg[None, None, :]) / safe
rgb = np.clip(rgb, 0, 255)

out = np.dstack([rgb, alpha * 255.0]).astype(np.uint8)
logo = Image.fromarray(out, "RGBA")

# recadrage sur l'encre reelle
bbox = logo.getbbox()
logo = logo.crop(bbox)
logo.thumbnail((WORK, WORK), Image.LANCZOS)

os.makedirs(DST_DIR, exist_ok=True)
logo.save(DST)
print(f"logo detoure : {DST}  {logo.size}")

# couleurs dominantes (pixels opaques uniquement), pour caler l'accent
px = np.asarray(logo, dtype=np.float32)
solid = px[px[..., 3] > 240][:, :3]
warm = solid[(solid[:, 0] > solid[:, 2] + 40)]
cool = solid[(solid[:, 2] > solid[:, 0] + 40)]
if len(warm):
    print("orange moyen :", tuple(int(v) for v in warm.mean(0)),
          " plus sature :", tuple(int(v) for v in warm[np.argmax(warm[:, 0] - warm[:, 2])]))
if len(cool):
    print("violet moyen :", tuple(int(v) for v in cool.mean(0)))
