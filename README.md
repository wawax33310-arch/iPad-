# Zenvy — pub kinetic typography (20 s, 9:16)

Vidéo publicitaire en typographie animée, générée entièrement par code
(aucun projet After Effects, aucun rush vidéo) : la scène est décrite en
HTML/CSS/JS, rendue image par image dans Chromium, la bande son est
synthétisée en Python, le tout encodé en H.264 avec ffmpeg.

**Livrable : [`out/zenvy-kinetic-20s.mp4`](out/zenvy-kinetic-20s.mp4)**
— 1080 × 1920 (9:16), 60 fps, 20,0 s, H.264 + AAC 48 kHz stéréo.
Format prêt pour Instagram Reels et TikTok.

## Direction artistique

| Élément | Choix |
|---|---|
| Fond | noir pur `#000000`, uni, sans texture ni vignette |
| Typo | **Anton** — grotesque ultra-grasse, capitales, interlettrage resserré (−0,012 em), lignes justifiées à la largeur du cadre et empilées serré (réf. affiche « ANIMATION DE TEXTE ») |
| Couleur principale | blanc pur `#FFFFFF` |
| Accent orange Zenvy | `#FF8A1E` |
| Accent violet Zenvy | `#8B31F4` |
| Dégradé de marque | violet → orange en diagonale (105°), réservé au mot « Zenvy » |
| Zone sûre | bloc de texte centré, remonté de ~60 px pour rester au-dessus de l'UI Reels/TikTok |

## Découpage et animations

| Séquence | Temps | Texte | Animation |
|---|---|---|---|
| 1 | 0 → 4 s | On a tous ce moment où on veut sortir… | Révélation mot par mot : opacité 0→100 % en 0,3 s, Y +20 px → 0, scale 95 % → 100 %, ease-out sans overshoot, stagger 0,15 s |
| 2 | 4 → 7 s | …mais personne n'est dispo. | Entrée mot par mot avec rotation −2° → 0°, puis **retombée** : Y 0 → +15 px en ease-in et assombrissement 100 % → 85 % |
| 3 | 7 → 10 s | Ou on est dispo… | Reprise exacte de l'entrée de la séquence 1 |
| 4 | 10 → 13 s | …mais on sait pas où aller. | Reprise exacte de la retombée de la séquence 2 |
| 5 | 13 → 16 s | Et si on savait tout, **tout de suite ?** | Stagger réduit à 0,08 s, Y +40 px → 0, scale 80 % → 105 % → 100 % (easeOutBack), flou directionnel vertical proportionnel à la vitesse ; « tout de suite ? » en orange |
| 6 | 16 → 19 s | **Zenvy** | Coupe nette. Scale 50 % → 130 % en 0,4 s (easeOutExpo) puis rebond retour à 100 %, dégradé violet → orange sur les lettres, **flash blanc plein écran** (0 → 60 % → 0 en 0,2 s) calé sur le pic à t = 16,40 s, puis pulse continu 100 % ↔ 103 % |
| 7 | 19 → 20 s | Bordeaux, **20 août.** | Fade-in simple 0 → 100 % en 0,3 s, sans mouvement ni scale ; « 20 août. » en orange |

**Transitions** : *whip* de 0,22 s entre chaque bloc — le texte sortant est
chassé hors champ en translation + rotation + zoom avec flou directionnel
horizontal, le bloc suivant arrive du côté opposé (sens alterné). Un léger
zoom continu anime chaque plan. Entre les séquences 5 et 6 : coupe nette,
soulignée par le flash.

## Bande son (`src/audio.py`)

Prod électronique rythmée, sans voix ni paroles, **120 BPM** — une mesure de
2 s, donc chaque séquence tombe pile sur une mesure. Kick, sub, clap, hats,
stabs d'accord et nappe sont tous synthétisés (aucun sample externe), sur la
grille Am → F → C → G → Am.

| Mesures | Temps | Arrangement |
|---|---|---|
| 1-2 | 0 → 4 s | intro : kick sur 1 et 3, hats en croches, nappe filtrée |
| 3-4 | 4 → 8 s | groove : kick 4/4, basse en contretemps, clap sur 2 et 4 |
| 5-6 | 8 → 12 s | basse en croches, hats en doubles, stabs d'accord |
| 7-8 | 12 → 16 s | build : roulement qui accélère (8ᵉ → 16ᵉ → 32ᵉ), riser filtré, coupe de 0,5 s avant le drop |
| 9-10 | 16 → 20 s | drop : impact sub, kick + basse pleines, stabs larges, sortie en fondu |

Le whoosh + pop tombent exactement sur le flash lumineux (t = 16,40 s). Le
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
src/render.js    Chromium -> 1200 images PNG -> pipe ffmpeg -> MP4
src/audio.py     synthèse de la piste sonore (WAV 48 kHz stéréo)
src/preview.js   export d'images clés en PNG pour contrôle visuel
src/build.sh     enchaînement complet
assets/fonts/    Anton (SIL OFL) + Inter ExtraBold en repli
out/             livrables générés
```

L'animation ne dépend d'aucune horloge : `renderFrame(t)` est une fonction
pure du temps, donc le rendu est déterministe et le montage se retouche en
modifiant le tableau `SEQS` de `src/scene.html` (textes, minutage, tailles,
couleurs) sans toucher au moteur d'animation.
