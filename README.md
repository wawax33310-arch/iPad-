# Zenvy — vidéo kinetic typography (13 s, 9:16)

Vidéo de texte animé générée par code (Python + Pillow + ffmpeg), pensée pour
Instagram Reels / TikTok. Aucune ressource externe : le fond, la typo animée et
la bande son sont produits par les scripts ; seul le logo Zenvy est un asset
fourni, détouré automatiquement.

**Livrable :** `out/zenvy_kinetic_13s.mp4` — 1080×1920, 60 fps, 13,000 s,
H.264 (yuv420p) + AAC stéréo 48 kHz.

## Direction artistique

| | |
|---|---|
| Format | 9:16 vertical, 1080×1920, 60 fps |
| Fond | bleu nuit profond, dégradé `#0A0F2A` → `#03050E`, halo central, vignette, grain léger |
| Police | Anton — capitales, grotesque condensée très grasse |
| Composition | blocs façon kinetic typography : lignes empilées serrées, chaque ligne étirée sur 688 px de large (marges franches sur les côtés), contraste de tailles entre mots de liaison et mots clés |
| Couleur de base | blanc cassé `#F5F7FC`, gris froid `#949EBA` sur les temps qui retombent |
| Accent | orange `#FA8C19`, repris du logo, réservé aux mots clés : `TOUT DE SUITE ?` et `20 août` |
| Marque | logo Zenvy détouré + mot « Zenvy » en blanc, halo orange pulsé |
| Durée | 13 s, montage calé sur une grille de tempo à 134,6 BPM : chaque bloc arrive sur un temps, la révélation tombe sur le 24e |
| Son | morceau instrumental sans paroles, synthétisé : kick quatre au sol, clap, charleston, basse et arpège en la mineur, nappes, plus les repères de montage (ticks, whooshes, impacts, riser et pop) |

## Séquence et timing

| Temps | Texte | Animation |
|---|---|---|
| 0 – 2,2 s | *On a tous ce moment où on veut sortir…* | les mots arrivent en glissant des côtés en alternance, toutes les 52 ms, avec un vrai filé de mouvement ; bloc en place en ~0,5 s, push-in pendant la tenue, sortie en vrille vers la gauche |
| 2,1 – 4,5 s | *…mais personne n'est dispo.* | cassure : le bloc tombe en 0,16 s avec flou de mouvement, s'écrase à l'atterrissage (squash amorti, pieds ancrés), secousse caméra, gris froid, sortie vers le haut |
| 4,5 – 6,2 s | *Ou on est dispo…* | reprise, cadence 50 ms, sortie en vrille vers la droite |
| 6,1 – 8,5 s | *…mais on sait pas où aller.* | même mécanique de chute que la première |
| 8,5 – 10,7 s | *Et si on savait tout, tout de suite ?* | cadence 40 ms, push-in plus marqué, accent orange sur « TOUT DE SUITE ? », sortie en zoom vers la caméra |
| 10,7 – 12 s | **logo + Zenvy** | flash, pop d'échelle avec dépassement, interlettrage qui se resserre, halo orange pulsé, whoosh + pop sonore |
| 12 – 13 s | *Lancement le 20 août à Bordeaux* | la marque recule en haut, filet accent + carton final fixe |

Le rythme accélère en continu jusqu'à la révélation (52 → 50 → 40 ms entre les
mots), et l'arrangement suit : charleston sur les contretemps, puis sur les
croches, puis en doubles sur la mesure de montée ; le dernier temps avant la
révélation est vidé pour que le pop claque dans le silence.

## Regénérer

```bash
pip install pillow numpy          # + ffmpeg disponible dans le PATH
./zenvy_kinetic/build.sh
```

Contrôler une image précise sans encoder toute la vidéo :

```bash
python3 zenvy_kinetic/render_video.py --stills 0.8,2.6,9.2,10.9,12.5
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
├── zenvy_kinetic_13s.mp4
└── zenvy_audio.wav
```

`timing.py` est la source unique des textes et des instants : le rendu image et
la bande son y puisent les mêmes valeurs, donc un réglage de rythme reste
automatiquement synchrone. Les réglages purement visuels (couleurs, largeur des
blocs, tailles) sont en haut de `render_video.py`.

Anton © The Anton Project Authors, sous SIL Open Font License 1.1.
