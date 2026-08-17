# Zenvy — vidéo kinetic typography (20 s, 9:16)

Vidéo de texte animé générée par code (Python + Pillow + ffmpeg), pensée pour
Instagram Reels / TikTok. Aucune ressource externe : le fond, le texte et la
bande son sont entièrement synthétisés.

**Livrable :** `out/zenvy_kinetic_20s.mp4` — 1080×1920, 60 fps, 20,000 s,
H.264 (yuv420p) + AAC stéréo 48 kHz.

## Direction artistique

| | |
|---|---|
| Format | 9:16 vertical, 1080×1920, 60 fps |
| Fond | bleu nuit profond, dégradé `#0B1222` → `#04060D`, halo central froid, vignette, grain léger |
| Police | Poppins Bold / ExtraBold (unique famille sans-serif) |
| Couleur de base | blanc cassé `#F4F7FB` (gris `#B0BACB` sur les temps qui retombent) |
| Accent | vert menthe `#2EE6A8`, uniquement sur les mots clés : `tout de suite ?`, `Zenvy`, `20 août.` |
| Son | ambiance minimaliste sans paroles : drone sub, nappe filtrée, pulsations qui accélèrent, whoosh + pop sur « Zenvy » |

## Séquence et timing

| Temps | Texte | Animation |
|---|---|---|
| 0 – 4 s | *On a tous ce moment où on veut sortir…* | construction mot à mot (0,30 s d'écart), fondu + flou qui se résorbe, petite taille centrée |
| 4 – 7 s | *…mais personne n'est dispo.* | cassure : le bloc tombe (flou de mouvement), s'écrase à l'atterrissage (squash amorti, pieds ancrés), secousse caméra, teinte grise |
| 7 – 10 s | *Ou on est dispo…* | reprise douce, cadence resserrée (0,26 s) |
| 10 – 13 s | *…mais on sait pas où aller.* | même mécanique de chute que la première |
| 13 – 16 s | *Et si on savait tout, tout de suite ?* | cadence rapide (0,145 s), pop par mot, le bloc grossit de 10 %, accent sur « tout de suite ? » |
| 16 – 19 s | **Zenvy** | flash blanc court, pop d'échelle (overshoot), interlettrage qui se resserre, halo accent pulsé, whoosh + pop sonore |
| 19 – 20 s | *Bordeaux, 20 août.* | « Zenvy » recule en haut, filet accent + carton final fixe, sans animation |

Le rythme accélère en continu (0,30 → 0,26 → 0,145 s entre les mots, pulsations
audio de plus en plus rapprochées de 2 s à 0,45 s) jusqu'à la révélation, puis se
stabilise sur le carton final.

## Regénérer

```bash
pip install pillow numpy          # + ffmpeg disponible dans le PATH
./zenvy_kinetic/build.sh
```

Contrôler une image précise sans encoder toute la vidéo :

```bash
python3 zenvy_kinetic/render_video.py --stills 3,4.5,16.05,19.5
```

## Fichiers

```
zenvy_kinetic/
├── render_video.py   # moteur d'animation image par image + encodage
├── make_audio.py     # synthèse de l'ambiance sonore (WAV 20 s)
├── build.sh          # audio puis vidéo
└── fonts/            # Poppins (SIL Open Font License)
out/
├── zenvy_kinetic_20s.mp4
└── zenvy_audio.wav
```

Les réglages (couleurs, tailles, timings de chaque segment) sont regroupés en
haut de `render_video.py` dans les blocs `S1`…`S5` et les constantes `ZEN_*`.

Poppins © The Indian Type Foundry & Jonny Pinhorn, sous SIL Open Font License 1.1.
