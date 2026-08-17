#!/usr/bin/env bash
# Genere l'ambiance sonore puis la video finale (out/zenvy_kinetic_<duree>s.mp4).
set -euo pipefail

cd "$(dirname "$0")/.."

python3 zenvy_kinetic/make_audio.py
python3 zenvy_kinetic/render_video.py

echo
echo "Termine :"
ls -lh out/zenvy_kinetic_*s.mp4
