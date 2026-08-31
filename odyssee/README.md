# Réel — L'Odyssée, buffet à volonté (Bègles)

| Fichier | Rôle |
|---|---|
| `build.sh` | Moteur de montage. Prend une liste de plans en CSV, sort un MP4 1080×1920 / 30 fps. |
| `shots-demo.csv` | Le découpage de la démo de traitement (8 plans, 2 rushs). |
| `rushs-a-fournir.md` | Ce qui manque à tourner, par priorité, et comment le filmer. |
| `odyssee-demo-traitement.mp4` | La démo rendue — 9 s, à valider avant le montage complet. |

## Lancer un montage

```bash
./build.sh shots-demo.csv sortie.mp4
```

Une ligne de CSV = un plan :

```
source ; entrée_s ; durée_sortie_s ; vitesse ; zoom_début ; zoom_fin ; ancre_x ; ancre_y
```

`vitesse` 1.0 = normal, 1.6 = accéléré, 0.85 = ralenti.
`zoom` 1.0 = plein cadre, 1.5 = serré ; début ≠ fin crée le mouvement.
`ancre_x/y` entre 0 et 1 : où se centre le cadre (0.5 / 0.5 = centre).

Le script refuse un plan qui dépasserait la fin de son rush, en le nommant.

## Parti pris de montage

- Aucun sous-titre : ils sont ajoutés en aval.
- Aucun plan immobile — punch-in permanent, même imperceptible.
- Coupes entre 0,9 s et 1,4 s, jamais deux valeurs de plan identiques à la suite.
- Étalonnage commun : contraste +8 %, saturation +20 %, léger renforcement de netteté.
- Ambiance du lieu conservée à 30 % du volume, sous le niveau d'une voix off.
