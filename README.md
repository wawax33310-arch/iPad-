# Zenvy — pub kinetic typography (15 s, 9:16)

Vidéo publicitaire en typographie animée, générée entièrement par code
(aucun projet After Effects, aucun rush vidéo) : la scène est décrite en
HTML/CSS/JS, rendue image par image dans Chromium, la bande son est
synthétisée en Python, le tout encodé en H.264 avec ffmpeg.

**Livrable : [`out/zenvy-kinetic-15s.mp4`](out/zenvy-kinetic-15s.mp4)**
— 1080 × 1920 (9:16), 60 fps, 15,0 s, H.264 + AAC 48 kHz stéréo.
Format prêt pour Instagram Reels et TikTok.

## Direction artistique

| Élément | Choix |
|---|---|
| Fond | noir pur `#000000`, uni, sans texture ni vignette |
| Typo | **Anton** — grotesque ultra-grasse, capitales, interlettrage resserré (−0,012 em), lignes calées à la même largeur et empilées serré (réf. affiche « ANIMATION DE TEXTE ») |
| Couleur principale | blanc pur `#FFFFFF` |
| Accent orange Zenvy | `#FF8A1E` |
| Accent violet Zenvy | `#8B31F4` |
| Dégradé de marque | violet → orange en diagonale (105°), réservé au mot « Zenvy » |
| Échelle | lignes calées sur 630 px de large, bloc limité à 760 px de haut : le texte ne touche jamais les bords |
| Zone sûre | bloc centré, remonté de ~55 px pour rester au-dessus de l'UI Reels/TikTok |
| Logo | icône Zenvy détourée sur fond noir, plan final |

## Découpage et animations

| Séquence | Temps | Texte | Animation |
|---|---|---|---|
| 1 | 0 → 3 s | On a tous ce moment où on veut sortir… | Révélation mot par mot : opacité 0→100 % en 0,26 s, Y +20 px → 0, scale 95 % → 100 %, ease-out sans overshoot, stagger 0,10 s |
| 2 | 3 → 5 s | …mais personne n'est dispo. | Entrée mot par mot avec rotation −2° → 0°, puis **retombée** : Y 0 → +15 px en ease-in et assombrissement 100 % → 85 % |
| 3 | 5 → 7 s | Ou on est dispo… | Reprise exacte de l'entrée de la séquence 1 |
| 4 | 7 → 9 s | …mais on sait pas où aller. | Reprise exacte de la retombée de la séquence 2 |
| 5 | 9 → 12 s | Et si on savait tout, **tout de suite ?** | Stagger 0,06 s, Y +40 px → 0, scale 80 % → 105 % → 100 % (easeOutBack), flou directionnel vertical proportionnel à la vitesse ; « tout de suite ? » en orange |
| 6 | 12 → 14 s | **Zenvy** | Coupe nette. Scale 50 % → 130 % en 0,4 s (easeOutExpo) puis rebond retour à 100 %, dégradé violet → orange sur les lettres, **flash blanc plein écran** (0 → 60 % → 0 en 0,2 s) calé sur le pic à t = 12,40 s, puis pulse continu 100 % ↔ 103 % |
| 7 | 14 → 15 s | logo Zenvy + Lancement le **20 août** à Bordeaux | Plan final fixe : le logo apparaît en fondu avec un léger scale 86 % → 100 %, le texte suit 0,12 s plus tard ; « 20 août » en orange |

**Transitions** : *whip* de 0,18 s entre chaque bloc — le texte sortant est
chassé hors champ en translation + rotation + zoom avec flou directionnel
horizontal, le bloc suivant arrive du côté opposé (sens alterné). Un léger
zoom continu anime chaque plan. Entre les séquences 5 et 6 : coupe nette,
soulignée par le flash. Le plan final ne repart pas en whip : il tient
jusqu'au bout.

## Bande son (`src/audio.py`)

Prod électronique rythmée, sans voix ni paroles, **120 BPM** — une mesure de
2 s, donc chaque séquence tombe pile sur une mesure. Kick, sub, clap, hats,
stabs d'accord et nappe sont tous synthétisés (aucun sample externe), sur la
grille Am → F → C → G → Am.

| Mesures | Temps | Arrangement |
|---|---|---|
| 1-2 | 0 → 4 s | intro : kick sur 1 et 3 puis 4/4, hats, clap, nappe filtrée |
| 3-4 | 4 → 8 s | groove : basse en croches, hats en doubles, stabs d'accord |
| 5-6 | 8 → 12 s | build : roulement qui accélère (8ᵉ → 16ᵉ → 32ᵉ), riser filtré, coupe de 0,5 s avant le drop |
| 7-8 | 12 → 15 s | drop : impact sub, kick + basse pleines, stabs larges, sortie en fondu |

Le whoosh + pop tombent exactement sur le flash lumineux (t = 12,40 s). Le
master applique un arc d'énergie croissant, une compression de bus douce et
un lift d'aigus pour rester lisible sur haut-parleur de téléphone.

## Reproduire le rendu

```bash
./src/build.sh                  # audio + rendu + encodage
FPS=30 OUT=out/test.mp4 ./src/build.sh
```

Dépendances : Node ≥ 18 avec `playwright` (Chromium), Python 3 avec `numpy`,
et un ffmpeg compilé avec libx264/aac (`pip install imageio-ffmpeg` suffit,
ou définir `FFMPEG_BIN`).

### Fichiers

```
src/scene.html   scène 1080x1920 ; window.renderFrame(t) = état exact à l'instant t
src/render.js    Chromium -> 900 images PNG -> pipe ffmpeg -> MP4
src/audio.py     synthèse de la piste sonore (WAV 48 kHz stéréo)
src/preview.js   export d'images clés en PNG pour contrôle visuel
src/build.sh     enchaînement complet
assets/fonts/    Anton (SIL OFL) + Inter ExtraBold en repli
assets/zenvy-logo.png  logo détouré (fond transparent) du plan final
out/             livrables générés
```

L'animation ne dépend d'aucune horloge : `renderFrame(t)` est une fonction
pure du temps, donc le rendu est déterministe et le montage se retouche en
modifiant le tableau `SEQS` de `src/scene.html` (textes, minutage, tailles,
couleurs) sans toucher au moteur d'animation.
