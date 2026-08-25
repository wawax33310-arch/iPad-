# Réel rentrée — UCPA Sport Station Bordeaux

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

- `montage.yaml` — le montage, rejouable : `ugcut render montage.yaml`
- `voix-off.md` — le script de la voix off, avec les timecodes de chaque phrase

Les rushes ne sont pas versionnés. Pour rejouer le montage, place les fichiers
`IMG_*.mov` dans un dossier `rushes/` à côté du `montage.yaml`.

## Points ouverts

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
- **Contrôle** : `ugcut check` signale une couverture de sous-titres à 61 % et
  l'absence de son. Les deux sont des choix : pas de sous-titres pendant
  l'énumération des activités (les étiquettes portent le message) ni sur les
  trois plans à titre plein cadre.
