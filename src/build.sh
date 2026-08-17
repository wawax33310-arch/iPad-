#!/usr/bin/env bash
# Chaîne de fabrication complète : audio -> images -> MP4 (1080x1920, 60 fps, 15 s)
set -euo pipefail

cd "$(dirname "$0")/.."

FPS="${FPS:-60}"
OUT="${OUT:-out/zenvy-kinetic-15s.mp4}"

echo "→ 1/2  synthèse de la bande son"
python3 src/audio.py

echo "→ 2/2  rendu des images + encodage H.264"
NODE_PATH="${NODE_PATH:-/opt/node22/lib/node_modules}" \
  node src/render.js --fps "$FPS" --out "$OUT" --audio out/zenvy-audio.wav

echo "✔ terminé : $OUT"
