# Réel rentrée — UCPA Sport Station Bordeaux

Trois montages, sur les mêmes rushes :

| | Durée | Plans | Plan moyen | Caractère |
|---|---|---|---|---|
| `montage-v3.yaml` **(livré en dernier)** | 42,6 s | 42 | 1,0 s | Le plus dynamique : mouvement sur chaque plan, plans larges accélérés, rythme irrégulier |
| `montage-v2.yaml` | 44,4 s | 31 | 1,4 s | Mots-clés plein cadre, sound design, speed ramp |
| `montage.yaml` | 42,3 s | 28 | 1,5 s | Première version, plus sobre, sans effets sonores |

Scripts de voix off : `voix-off-v2.md` (valable aussi pour la v3, à recaler sur
les nouveaux timecodes) et `voix-off.md`.

## v3 — ce qui la rend dynamique

Le rythme de coupe n'était pas le problème : la v2 coupait déjà toutes les
1,4 s, dans la cible du brief. Ce qui manquait, c'était du **mouvement dans le
cadre** — 5 plans sur 31 avaient un zoom, les autres étaient des cadres fixes,
et beaucoup de rushes sont larges avec des sujets petits et lents.

| Levier | v2 | v3 |
|---|---|---|
| Plans | 31 (1,4 s de moyenne) | 42 (1,0 s) |
| Plans avec un mouvement | 5 | 42 — `zoom: auto` alterne le sens à chaque coupe |
| Plans larges accélérés | 0 | 11, entre 1,2× et 1,5× |
| Ralentis / speed ramps | 2 | 4 |
| Régularité | coupes uniformes | rafales de 0,8 s, respirations de 1,6 s |
| Effets sonores | 16 | 20 |

Deux étiquettes ont été raccourcies : à 0,85 s à l'écran, « MUSCU & CROSS
TRAINING » n'était pas lisible — une étiquette qu'on ne lit pas est du bruit.

---

## v2 — la structure

| Bloc | Timecode | Contenu |
|---|---|---|
| Hook | 0 → 3 s | Escalade, padel, rooftop, fitness, golf — une coupe toutes les 0,6 s, whoosh sur chaque |
| Le centre | 3 → 15 s | Une activité par plan, speed ramp sur le padel |
| L'offre | 14,8 → 28,8 s | « SANS ENGAGEMENT », « MÊME PRIX », « À VIE », « 40 € OFFERTS » en mots-clés plein cadre, riser + impact à l'ouverture |
| Portes ouvertes | 28,6 → 40,4 s | « TU PRÉFÈRES TESTER ? », puis samedi 12 septembre, 9h-18h, 100 % gratuit, initiations, animations |
| CTA | 40,4 → 44,4 s | Ralenti 0,5× : « JOURNÉE PORTES OUVERTES / 12 SEPTEMBRE · 100 % GRATUIT », « INSCRIS-TOI », le site en sous-titre |

L'accroche du hook est déclarée à la racine du montage (`textes:`) et non sur
un plan : un texte de plan serait coupé au bout de 0,6 s.

Pas de sous-titres : les étiquettes d'activité et les mots-clés plein cadre
portent seuls le message. Les lignes restent dans `montage-v2.yaml` sous
`sous_titres.actif: false` — elles servent à caler la voix off, et il suffit de
repasser `actif: true` pour les réafficher.

Sound design : 16 effets synthétisés (whoosh sur les coupes du hook, impact à
chaque changement de bloc, pop sur les mots-clés, riser avant l'offre, drop sur
la bascule), à −5 dB pour laisser la place à la voix et à la musique.

---

## v1 — la structure

Montage de 42,3 s en 1080 × 1920, 28 plans (plan moyen 1,5 s), qui fait passer
les trois messages dans l'ordre : **découverte du centre → offre de rentrée →
Journée Portes Ouvertes**.

| Bloc | Timecode | Contenu |
|---|---|---|
| Le lieu | 00,0 → 02,8 | Mur d'escalade, padel sur le rooftop |
| Les activités | 02,8 → 13,5 | Escalade, padel, squash, golf, fitness, muscu, resto, rooftop — une étiquette par activité |
| Signature | 13,3 → 15,3 | « UCPA SPORT STATION » sur le rooftop au coucher du soleil |
| Offre de rentrée | 15,1 → 28,5 | Sans engagement au prix de l'engagement, à vie · frais de dossier offerts (−40 €) · jusqu'au 30 septembre · heures pleines ou creuses |
| Bascule | 28,2 → 30,2 | « Envie d'essayer avant ? » sur la vue de Bordeaux |
| Portes ouvertes | 30,0 → 39,7 | Samedi 12 septembre, 9h-18h gratuit, initiations, photobooth, animations enfants, jeux extérieurs, tapas |
| CTA | 39,7 → 42,3 | « Inscris-toi » · UCPA Sport Station Bordeaux |

## Fichiers

- `montage-v2.yaml`, `voix-off-v2.md` — la version livrée en dernier
- `montage.yaml`, `voix-off.md` — la première version
- Rejouer : `ugcut render montage-v2.yaml`

Les rushes ne sont pas versionnés. Pour rejouer le montage, place les fichiers
`IMG_*.mov` dans un dossier `rushes/` à côté du `montage.yaml`.

## Points ouverts

- **Aucun plan face caméra** dans les rushes : le brief v2 demandait de finir
  face caméra, le montage finit donc sur la terrasse du rooftop au ralenti.
  Trois secondes de face caméra suffiraient à remplacer le dernier plan :

  ```yaml
  - {id: cta, role: cta, source: rushes/face-cam.mov, debut: 0.3, duree: 3.8,
     garder_son: true, son: impact, textes: [...]}
  ```

- **Vélo à smoothie et sculpteur de ballons** : absents des rushes eux aussi.
  Ils ne sont ni montrés ni annoncés — les annoncer sur une image qui montre
  autre chose ferait perdre la confiance que le format UGC repose dessus.
  (`IMG_9130` est le bar du resto : tireuses et shaker, pas le vélo à smoothie.)

- **Escape game** : aucun rush ne le montre. Il est cité par la voix off, mais
  pas illustré. Dès qu'un plan existe, l'insérer après `b6-muscu` suffit :

  ```yaml
  - {id: b7-escape, source: rushes/escape.mov, debut: 1.0, duree: 1.3,
     garder_son: false, textes: [{contenu: "ESCAPE GAME", t: 0.0, duree: 1.2}]}
  ```

  Il faudra alors retirer ~1,3 s ailleurs (les plans du bloc D, par exemple)
  pour rester sous les 45 s.
- **Son** : le montage est livré muet, prêt pour la voix off et la musique
  (voir `voix-off.md`). Les rushes sont coupés : sur 28 plans, les ambiances
  hétérogènes hachent l'écoute.
- **Contrôle (v2)** : `ugcut check` signale l'absence de sous-titres et le fait
  que seul le sound design soit présent. Les deux sont des choix : sous-titres
  retirés à la demande, voix off et musique à venir.
- **Contrôle (v1)** : couverture de sous-titres à 61 % et absence de son. Les deux sont des choix : pas de sous-titres pendant
  l'énumération des activités (les étiquettes portent le message) ni sur les
  trois plans à titre plein cadre.
