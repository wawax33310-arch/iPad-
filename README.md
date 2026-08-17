# Zenvy — vidéo kinetic typography (20 s, 9:16)

Vidéo de texte animé générée par code (Python + Pillow + ffmpeg), pensée pour
Instagram Reels / TikTok. Aucune ressource externe : le fond, la typo animée et
la bande son sont produits par les scripts ; seul le logo Zenvy est un asset
fourni, détouré automatiquement.

**Livrable :** `out/zenvy_kinetic_20s.mp4` — 1080×1920, 60 fps, 20,000 s,
H.264 (yuv420p) + AAC stéréo 48 kHz.

## Direction artistique

| | |
|---|---|
| Format | 9:16 vertical, 1080×1920, 60 fps |
| Fond | bleu nuit profond, dégradé `#0A0F2A` → `#03050E`, halo central, vignette, grain léger |
| Police | Anton — capitales, grotesque condensée très grasse |
| Composition | blocs façon kinetic typography : lignes empilées serrées, chaque ligne étirée sur 816 px de large (marges franches sur les côtés), contraste de tailles entre mots de liaison et mots clés |
| Couleur de base | blanc cassé `#F5F7FC`, gris froid `#949EBA` sur les temps qui retombent |
| Accent | orange `#FA8C19`, repris du logo, réservé aux mots clés : `TOUT DE SUITE ?` et `20 août` |
| Marque | logo Zenvy détouré + mot « Zenvy » en blanc, halo orange pulsé |
| Son | ambiance minimaliste sans paroles : drone sub, nappe filtrée, pulsations qui accélèrent, ticks sur chaque mot, whooshes sur les transitions, whoosh + pop sur la reveal |

## Séquence et timing

| Temps | Texte | Animation |
|---|---|---|
| 0 – 4 s | *On a tous ce moment où on veut sortir…* | les mots arrivent en glissant des côtés en alternance, toutes les 65 ms, avec un vrai filé de mouvement ; bloc en place en ~0,5 s, push-in pendant la tenue, sortie en vrille vers la gauche |
| 4 – 7 s | *…mais personne n'est dispo.* | cassure : le bloc tombe en 0,16 s avec flou de mouvement, s'écrase à l'atterrissage (squash amorti, pieds ancrés), secousse caméra, gris froid, sortie vers le haut |
| 7 – 10 s | *Ou on est dispo…* | reprise, cadence 60 ms, sortie en vrille vers la droite |
| 10 – 13 s | *…mais on sait pas où aller.* | même mécanique de chute que la première |
| 13 – 16 s | *Et si on savait tout, tout de suite ?* | cadence 48 ms, push-in plus marqué, accent orange sur « TOUT DE SUITE ? », sortie en zoom vers la caméra |
| 16 – 19 s | **logo + Zenvy** | flash, pop d'échelle avec dépassement, interlettrage qui se resserre, halo orange pulsé, whoosh + pop sonore |
| 19 – 20 s | *Lance 20 août à Bordeaux* | la marque recule en haut, filet accent + carton final fixe |

Le rythme accélère en continu jusqu'à la révélation (65 → 60 → 48 ms entre les
mots, pulsations audio de 2 s à 0,45 s), puis se stabilise sur le carton final.

## Regénérer

```bash
pip install pillow numpy          # + ffmpeg disponible dans le PATH
./zenvy_kinetic/build.sh
```

Contrôler une image précise sans encoder toute la vidéo :

```bash
python3 zenvy_kinetic/render_video.py --stills 0.9,4.4,14.9,16.4,19.5
```

## Fichiers

```
zenvy_kinetic/
├── timing.py         # table de montage : textes, tailles relatives, timings
├── render_video.py   # moteur d'animation image par image + encodage
├── make_audio.py     # synthèse de l'ambiance sonore (WAV 20 s)
├── prepare_logo.py   # détourage du logo sur fond uni -> PNG RGBA
├── build.sh          # audio puis vidéo
├── assets/           # logo détouré
└── fonts/            # Anton (SIL Open Font License)
out/
├── zenvy_kinetic_20s.mp4
└── zenvy_audio.wav
```

`timing.py` est la source unique des textes et des instants : le rendu image et
la bande son y puisent les mêmes valeurs, donc un réglage de rythme reste
automatiquement synchrone. Les réglages purement visuels (couleurs, largeur des
blocs, tailles) sont en haut de `render_video.py`.

Anton © The Anton Project Authors, sous SIL Open Font License 1.1.
