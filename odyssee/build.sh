#!/usr/bin/env bash
# Moteur de montage — Réel "L'Odyssée, buffet à volonté"
# Usage : ./build.sh shots.csv sortie.mp4
# Sortie : 1080x1920, 30 fps, H.264 — prêt pour Instagram / TikTok.
#
# Format de shots.csv (une ligne par plan, # = commentaire) :
#   fichier_source ; entree_s ; duree_sortie_s ; vitesse ; zoom_debut ; zoom_fin ; ancre_x ; ancre_y
#
#   entree_s        point d'entree dans le rush
#   duree_sortie_s  duree du plan dans le montage final
#   vitesse         1.0 = normal, 1.6 = accelere, 0.85 = ralenti
#   zoom_debut/fin  1.0 = plein cadre, 1.5 = serre. Debut != fin => mouvement.
#   ancre_x/y       0.0-1.0, ou se centre le cadre (0.5 0.5 = centre)
#
# Contrainte : entree_s + duree_sortie_s * vitesse <= duree du rush.

set -euo pipefail

SHOTS="${1:?usage: build.sh shots.csv sortie.mp4}"
OUT="${2:?usage: build.sh shots.csv sortie.mp4}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

W=1080; H=1920; FPS=30
# Etalonnage commun a tous les plans : contraste, saturation, nettete.
GRADE="eq=contrast=1.08:saturation=1.20:brightness=0.005,unsharp=5:5:0.8:5:5:0.0"

i=0
: > "$WORK/list.txt"

while IFS=';' read -r -u 9 src tin dur speed z0 z1 ax ay; do
  case "${src// /}" in ''|'#'*) continue ;; esac
  src="$(echo "$src" | xargs)"; tin="$(echo "$tin" | xargs)"
  dur="$(echo "$dur" | xargs)"; speed="$(echo "$speed" | xargs)"
  z0="$(echo "$z0" | xargs)";   z1="$(echo "$z1" | xargs)"
  ax="$(echo "$ax" | xargs)";   ay="$(echo "$ay" | xargs)"

  i=$((i+1))
  n=$(printf '%03d' "$i")
  frames=$(python3 -c "print(max(1,round($dur*$FPS)))")
  srcdur=$(python3 -c "print(round($dur*$speed,3))")

  # Garde-fou : le plan depasse-t-il la fin du rush ?
  avail=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$src")
  python3 - "$tin" "$srcdur" "$avail" "$src" <<'PY'
import sys
tin, need, avail, src = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
if tin + need > avail + 0.02:
    sys.exit(f"ERREUR: {src} — le plan demande {tin+need:.2f}s mais le rush fait {avail:.2f}s")
PY

  # scale : on travaille en 1.5x de la sortie pour garder du piqué au punch-in.
  ffmpeg -nostdin -v error -ss "$tin" -t "$srcdur" -i "$src" \
    -vf "scale=$((W*3/2)):$((H*3/2)):flags=lanczos,setsar=1,setpts=PTS/$speed,fps=$FPS,\
zoompan=z='$z0+($z1-$z0)*on/$frames':d=1\
:x='max(0,min(iw-iw/zoom,iw*$ax-(iw/zoom/2)))'\
:y='max(0,min(ih-ih/zoom,ih*$ay-(ih/zoom/2)))'\
:s=${W}x${H}:fps=$FPS,$GRADE" \
    -frames:v "$frames" -an \
    -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -r "$FPS" \
    "$WORK/s$n.mp4"

  echo "file '$WORK/s$n.mp4'" >> "$WORK/list.txt"
  printf '  plan %s  %-28s  %ss  x%s  zoom %s→%s\n' \
    "$n" "$(basename "$src")" "$dur" "$speed" "$z0" "$z1"
done 9< "$SHOTS"

ffmpeg -v error -f concat -safe 0 -i "$WORK/list.txt" -c copy "$WORK/video.mp4"

# Lit d'ambiance continu, pris sur le premier rush, sous le niveau d'une voix off.
FIRST=$(awk -F';' '!/^ *#/ && NF>1 {print $1; exit}' "$SHOTS" | xargs)
TOTAL=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WORK/video.mp4")
ffmpeg -v error -stream_loop -1 -i "$FIRST" -t "$TOTAL" \
  -vn -af "volume=0.30,afade=t=in:d=0.4,afade=t=out:st=$(python3 -c "print(max(0,$TOTAL-0.6))"):d=0.6,aresample=48000" \
  -c:a aac -b:a 192k "$WORK/ambiance.m4a"

ffmpeg -v error -i "$WORK/video.mp4" -i "$WORK/ambiance.m4a" \
  -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT" -y

echo
echo "OK  $OUT  —  ${TOTAL}s  ${W}x${H}  ${FPS}fps"
