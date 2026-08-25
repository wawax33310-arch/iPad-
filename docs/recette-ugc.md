# La recette d'un montage UGC

Ce document décrit ce qu'on monte et pourquoi. Le « comment » est dans le
[README](../README.md) ; la plupart des règles ci-dessous sont vérifiées
automatiquement par `ugcut check`.

---

## 1. La structure en cinq temps

Une UGC qui convertit raconte toujours la même histoire, dans le même ordre.

| Temps | Rôle (`role:`) | Durée | Ce qu'on y met |
|---|---|---|---|
| 0 – 2 s | `hook` | 1,5 à 2 s | L'accroche. Une phrase, un visage, un texte à l'image. |
| 2 – 6 s | `probleme` | 3 à 4 s | La situation d'avant, celle que la cible reconnaît. |
| 6 – 15 s | `solution` | 5 à 8 s | Le produit **en usage**, filmé à la main, pas en vitrine. |
| 15 – 25 s | `preuve` | 3 à 6 s | Le résultat : un avant/après, un chiffre, une réaction. |
| 25 – 30 s | `cta` | 2 à 3 s | Une seule action, dite **et** écrite. |

Total visé : **20 à 35 s**. En dessous de 15 s on n'a pas le temps de prouver,
au-delà de 45 s la complétion s'effondre — et la complétion est ce que
l'algorithme regarde en premier.

## 2. Le hook : les deux premières secondes

C'est 80 % du résultat. Trois formules qui marchent :

- **le résultat d'abord** — « 30 jours avec ça, voilà ce que ça donne »
- **l'erreur** — « si tu fais ça le matin, arrête tout de suite »
- **la question fermée** — « t'as déjà remarqué que… ? »

Les règles, dans l'ordre d'importance :

1. **Entre en plein milieu.** Coupe tout ce qui précède la première syllabe
   utile. Pas de « salut c'est moi », pas d'inspiration avant de parler. En
   pratique : `debut:` tombe presque toujours 0,3 à 1 s après le début du rush.
2. **Écris l'accroche à l'image** dès la première image (`textes:` avec `t: 0`).
   Le texte est lu avant que le son ne soit entendu — beaucoup de vues démarrent
   en sourdine.
3. **Un visage plein cadre**, cadré à mi-buste, regard caméra.
4. **Ne mets pas de musique sur le hook**, ou très bas : la voix seule paraît
   plus authentique et plus urgente.

## 3. Le rythme

- **Une coupe toutes les 1,5 à 3 s.** Le contrôle `rythme` te le rappelle.
- Les coupes sont des **jump cuts** : même cadre, on enlève juste les
  respirations et les hésitations. C'est le geste central du montage UGC.
- **Aucun plan fixe au-delà de 5 s.** S'il doit durer, ajoute un punch-in :
  `zoom: {de: 1.0, vers: 1.06}`. 4 à 8 % suffisent — au-delà, ça se voit et ça
  fait « monté ».
- Le **b-roll** illustre ce qui est dit, jamais l'inverse : 1,5 à 2,5 s, son
  coupé (`garder_son: false`), et on revient au visage.
- **Les transitions sont l'exception.** 90 % des raccords sont des coupes
  franches. Un `whip` avant le b-roll, un `flash` sur le packshot : deux
  effets par vidéo, pas plus, sinon ça sent la pub.

## 4. Les sous-titres

85 % des vues se font sans le son. Les sous-titres ne sont pas une option
d'accessibilité, ce sont **la piste principale**.

- **2 à 4 mots à l'écran** (`mots_par_ecran: 3`), pas des phrases entières.
- **Un mot mis en couleur au moment où il est prononcé** (`mode: mot_a_mot`) :
  c'est ce qui accroche l'œil et fait rester.
- **Majuscules, gras, contour noir épais** : lisible sur un fond clair comme sur
  un fond sombre, sans pavé de couleur.
- **Position 0,70 à 0,78 de la hauteur** : au-dessus de l'UI TikTok, en dessous
  du visage.
- Pas de point final, pas de virgule décorative. Le rythme, c'est la coupe.
- Couverture visée : **plus de 80 %** de la durée. Un silence sous-titré, c'est
  un silence qu'il fallait couper.

## 5. Le son

| Élément | Cible | Pourquoi |
|---|---|---|
| Voix | −14 LUFS intégré | Norme de fait TikTok / Reels / Shorts |
| Musique | −18 à −22 dB sous la voix | Elle porte le rythme, elle ne raconte rien |
| Ducking | activé | La musique s'efface d'elle-même sous la voix |
| Silences | coupés au-delà de 0,3 s | Le silence, c'est le moment où on scrolle |

`ugcut` applique `loudnorm` sur la voix, le ducking par compression sidechain et
un limiteur en sortie. Tu n'as donc à régler que `gain_db`.

## 6. Zones de sécurité (1080 × 1920)

Les interfaces des plateformes mangent les bords :

| Zone | Pixels | À éviter |
|---|---|---|
| Haut | 0 – 220 px | Nom de compte, boutons |
| Bas | 1620 – 1920 px | Légende, barre de progression |
| Droite | 950 – 1080 px | Colonne d'icônes TikTok |

En pratique : tout ce qui compte tient entre **220 et 1550 px** de hauteur.
D'où les valeurs par défaut `position: 0.74` (sous-titres, ≈ 1420 px) et
`sticker_position: 0.15` (≈ 290 px).

## 7. Le CTA

- **Une seule action.** « Lien en bio » OU « code UGC20 », pas les deux.
- **Dite et écrite** en même temps.
- 2 à 3 s, jamais plus — et surtout pas de générique de fin.
- Le dernier plan reste vivant : on ne finit pas sur un packshot figé.

## 8. Les erreurs qui reviennent

| Erreur | Correction |
|---|---|
| Intro de politesse | Coupe : le hook commence à la première syllabe utile |
| Plan de 8 s sans mouvement | Recoupe, ou punch-in |
| Sous-titres phrase entière | 3 mots à l'écran, mode mot à mot |
| Musique trop forte | `gain_db: -20` + `ducking: true` |
| Deux appels à l'action | N'en garde qu'un |
| Vidéo de 70 s | Coupe le problème, garde la preuve |
| Transitions partout | Coupes franches, deux effets maximum |

## 9. Tester ses hooks

Le corps de la vidéo se réutilise ; c'est le hook qui décide de la performance.
Filme-en trois d'affilée, déclare-les sous `variantes:` et rends une vidéo par
hook :

```bash
ugcut variantes montage.yaml
# sortie/ma-video-hook-question.mp4
# sortie/ma-video-hook-resultat.mp4
```

Les sous-titres sont recalés automatiquement si la variante n'a pas exactement
la durée du hook d'origine.

---

## Ce que `ugcut check` vérifie

| Code | Règle |
|---|---|
| `duree` | Durée totale entre 15 et 45 s, alerte au-delà de 60 s |
| `hook` | Premier plan sous 2,5 s |
| `hook_texte` | Du texte à l'image dans la première seconde |
| `rythme` | Plan moyen sous 3 s |
| `plan_statique` | Aucun plan de plus de 5 s sans mouvement |
| `sous_titres` | Présents, et couvrant plus de 80 % de la durée |
| `cta` | Un appel à l'action sur les 5 dernières secondes |
| `zone_sure` | Textes hors des zones mangées par l'UI |
| `musique_gain`, `ducking` | Musique entre −24 et −12 dB, ducking actif |
| `format`, `fps` | 1080 × 1920, cadence standard |
| `vitesse` | Pas de voix accélérée au-delà de 1,3× |
