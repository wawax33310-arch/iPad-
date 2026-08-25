# ugcut — montage de vidéos UGC

Un montage UGC, c'est toujours la même mécanique : un hook de deux secondes, des
coupes toutes les deux secondes, des sous-titres mot à mot, une musique sous la
voix, un appel à l'action. `ugcut` décrit ce montage dans un fichier texte et le
rend en MP4 vertical prêt à publier — sans ouvrir de logiciel de montage.

```yaml
plans:
  - {id: hook, role: hook, source: rushes/hook.mov, debut: 0.8, duree: 2.0,
     zoom: 1.06, textes: [{contenu: "3 SEMAINES DE TEST", t: 0, duree: 1.9}]}
  - {id: probleme, source: rushes/probleme.mov, debut: 2.4, duree: 3.2}
  - {id: broll, source: rushes/broll.mov, duree: 2.0, recadrage: flou,
     garder_son: false, transition: whip}
```

```
$ ugcut render montage.yaml
✓ sortie/serum-routine.mp4 — 21.35s, 12.4 Mo
```

**Pourquoi un fichier plutôt qu'une timeline ?** Parce qu'un montage UGC se
refait dix fois : trois hooks à tester, deux durées, une version sans musique.
Un fichier texte se duplique, se versionne et se rejoue ; une timeline se
refait à la main.

- La recette du montage lui-même : **[docs/recette-ugc.md](docs/recette-ugc.md)**
- Tourner et exporter depuis un iPhone/iPad : **[docs/tournage-iphone-ipad.md](docs/tournage-iphone-ipad.md)**
- Un montage complet commenté : **[exemples/montage-produit.yaml](exemples/montage-produit.yaml)**

---

## Installation

Il faut Python 3.10+ et **ffmpeg** (compilé avec libass, ce qui est le cas des
paquets standards).

```bash
pip install -e .          # installe la commande `ugcut`
```

```bash
brew install ffmpeg               # macOS
sudo apt install ffmpeg           # Debian / Ubuntu
pip install imageio-ffmpeg        # sinon : binaire statique, sans droits admin
```

`ugcut` cherche ffmpeg dans `$UGCUT_FFMPEG`, puis dans le `PATH`, puis dans
`imageio-ffmpeg`. Sans installation, tout marche aussi avec
`python -m ugcut …` depuis la racine du dépôt.

## Prise en main

```bash
ugcut demo                    # rushes de synthèse + montage complet, sans rien tourner
ugcut init mon-projet         # squelette : montage.yaml, rushes/, sortie/
ugcut check  montage.yaml     # relit le montage : hook, rythme, sous-titres, CTA
ugcut render montage.yaml     # rend le MP4
ugcut variantes montage.yaml  # une vidéo par variante de hook (test A/B)
```

`ugcut demo` ne demande aucun rush : il fabrique des plans de synthèse, écrit un
`montage.yaml` et rend une vidéo de bout en bout. C'est le moyen le plus rapide
de vérifier que la chaîne fonctionne sur ta machine.

## Le contrôle avant rendu

`check` (joué aussi automatiquement avant chaque `render`) applique les règles
du format — celles de [docs/recette-ugc.md](docs/recette-ugc.md) :

```
✓ [duree] Durée : 18.7s
✓ [hook] Hook : 2.2s
✓ [rythme] Plan moyen : 2.7s (7 plans)
! [sous_titres] Sous-titres sur 62% de la vidéo seulement (vise 80%+).
· [plan_statique] preuve : 6.2s sans mouvement. Ajoute un punch-in (zoom: 1.06).
```

`!` = alerte, `·` = conseil. Rien ne bloque le rendu, sauf avec `--strict`.

---

## Le fichier de montage

YAML ou JSON. Les clés sont en français ; leurs équivalents anglais
(`shots`, `start`, `speed`, `transition`, `music`…) sont acceptés.

### `projet`

| Clé | Défaut | Rôle |
|---|---|---|
| `nom` | `montage` | Nom du projet |
| `largeur` / `hauteur` | `1080` / `1920` | Format de sortie |
| `fps` | `30` | Cadence |
| `sortie` | `sortie/montage.mp4` | Fichier produit (relatif au montage) |
| `duree_max` | — | Limite de contrôle ; ne coupe rien |

### `plans`

Un plan = un extrait d'un rush. `debut`, `fin` et `duree` se lisent **dans le
rush** ; `vitesse` détermine ensuite la durée à l'écran (`duree / vitesse`).

| Clé | Défaut | Rôle |
|---|---|---|
| `source` | requis | Vidéo ou image (`.jpg`, `.png`…) |
| `id`, `role` | — | Étiquettes. `role` sert au contrôle : `hook`, `probleme`, `solution`, `preuve`, `cta`, `broll` |
| `debut` | `0` | Point d'entrée dans le rush |
| `fin` / `duree` | fin du rush | Point de sortie, ou longueur prise dans le rush |
| `vitesse` | `1.0` | 0.25 à 4.0, audio compris |
| `recadrage` | `remplir` | `remplir` (recadre), `flou` (fond flouté), `ajuster` (bandes noires) |
| `cadrage` | `0.5` | Où recadrer : `0`/`gauche` … `1`/`droite` |
| `zoom` | — | `1.06` ou `{de: 1.0, vers: 1.06}` — punch-in linéaire |
| `transition` | `cut` | Raccord **entrant** (voir plus bas) |
| `transition_duree` | `0.25` | Bridée à la moitié du plus court des deux plans |
| `garder_son` | `true` | `false` pour un b-roll muet |
| `volume` | `1.0` | Gain du plan |
| `textes` | — | Étiquettes posées à l'image |

Transitions : `cut` · `fondu` · `fondu_rapide` · `fondu_lent` · `noir` ·
`flash` · `gris` · `whip` (`whip_gauche`, `whip_droite`) · `glisse_gauche`
(`_droite`, `_haut`, `_bas`) · `doux_gauche` (`_droite`) · `zoom` · `pixel` ·
`flou_h` · `cercle` · `dissous` · `couvre_haut` · `revele_haut`.
En UGC, 90 % des raccords restent des coupes franches.

### `textes` (étiquettes)

```yaml
textes:
  - {contenu: "3 SEMAINES DE TEST", t: 0.0, duree: 1.9}          # pavé blanc en haut
  - {contenu: "LIEN EN BIO", t: 0.4, duree: 2.0, style: titre, position: 0.35}
```

`t` est relatif au **début du plan**. `style` vaut `sticker` (pavé plein) ou
`titre` (grand texte à contour). `position` est une fraction de la hauteur.

### `sous_titres`

```yaml
sous_titres:
  fichier: rushes/voix.srt        # export Whisper / CapCut …
```

ou, à la main, sur la timeline finale :

```yaml
sous_titres:
  lignes:
    - {debut: 0.05, fin: 2.00, texte: "Ma peau tirait tous les matins"}
```

Les lignes sont recoupées en paquets de `mots_par_ecran` mots, et chaque mot
s'allume à son tour. `sous_titres: false` désactive tout.

### `style`

| Clé | Défaut | Rôle |
|---|---|---|
| `police` | `Liberation Sans` | Famille installée (voir `dossier_polices` pour une police de marque) |
| `taille` | `92` | Corps des sous-titres |
| `couleur` / `couleur_active` | blanc / `#FFE600` | Texte, puis mot en cours |
| `contour` / `ombre` | `8` / `3` | Lisibilité sur fond clair |
| `position` | `0.74` | Hauteur des sous-titres (garde 0.55–0.84) |
| `mots_par_ecran` | `3` | 2 à 4 en UGC |
| `majuscules` | `true` | |
| `mode` | `mot_a_mot` | ou `ligne` |
| `sticker_taille`, `sticker_couleur`, `sticker_fond`, `sticker_position` | | Étiquettes |

### `musique` et `voix_off`

```yaml
musique:
  fichier: rushes/musique.mp3
  gain_db: -21          # -24 à -12 : la voix passe devant
  ducking: true         # la musique s'efface sous la voix (compression sidechain)
  fondu_sortie: 1.5

voix_off:               # remplace le son des plans si présente
  fichier: rushes/voix.m4a
  decalage: 0.0
```

La musique boucle si elle est plus courte que le montage. La voix est
normalisée à −14 LUFS (la cible TikTok / Reels / Shorts) et l'ensemble passe
par un limiteur.

### `variantes`

Des hooks de rechange. `ugcut variantes` rend une vidéo par entrée, en
remplaçant le premier plan et en recalant les sous-titres si la durée change.

---

## Ce qui se passe au rendu

```
rushes ─┬─► 1. normalisation par plan     coupe · vitesse · recadrage 9:16 · punch-in
        │
        ├─► 2. assemblage                 coupes franches, ou chaîne xfade si raccords
        │
        ├─► 3. incrustation               un seul fichier ASS : sous-titres + étiquettes
        │
        └─► 4. mixage et encodage         loudnorm · ducking · limiteur · H.264 faststart
```

Chaque plan est d'abord ramené au format du projet, ce qui permet de mélanger
sans y penser du 9:16, du 16:9 et des photos. Les textes sont générés en une
seule passe sur la timeline assemblée, donc leurs repères temporels sont
absolus. La sortie est un H.264 High yuv420p + AAC 48 kHz, `+faststart` :
le fichier que les plateformes réencodent le mieux.

Détails d'implémentation utiles :

- le punch-in passe par un recadrage intermédiaire à 1,5× pour éviter le
  tremblement classique de `zoompan` ;
- les bases de temps sont réalignées entre chaque `xfade` (sinon ffmpeg refuse
  de chaîner) ;
- la rotation des vidéos iPhone/iPad est lue et appliquée avant tout calcul de
  cadrage ;
- si `ffprobe` manque, l'analyse retombe sur la sortie de `ffmpeg -i`.

## Développement

```bash
make test     # 71 tests ; le rendu réel est ignoré si ffmpeg est absent
make demo     # rushes de synthèse + rendu complet
```

```
ugcut/
  spec.py         lecture et validation du fichier de montage
  probe.py        analyse des rushes (durée, dimensions, rotation, son)
  video.py        filtres : recadrage 9:16, punch-in, vitesse
  segments.py     un plan → un MP4 normalisé
  timeline.py     placement des plans et raccords
  soustitres.py   génération du fichier ASS
  audio.py        voix, musique, ducking
  render.py       orchestration
  lint.py         les règles du format UGC
  demo.py         rushes de synthèse
  cli.py          init · check · render · variantes · demo
```

## Dépannage

| Symptôme | Cause probable |
|---|---|
| `ffmpeg est introuvable` | Installe-le, ou `export UGCUT_FFMPEG=/chemin/vers/ffmpeg` |
| `No such filter: 'subtitles'` | ffmpeg compilé sans libass : prends un paquet standard ou `pip install imageio-ffmpeg` |
| Sous-titres dans une autre police | La famille de `style.police` n'est pas installée ; mets un nom installé ou renseigne `style.dossier_polices` |
| Rush à l'envers | Rotation absente du fichier : ajoute `recadrage: flou` ou réexporte le rush |
| Rendu très lent | Rushes 4K : le calcul est deux à trois fois plus long qu'en 1080p |
