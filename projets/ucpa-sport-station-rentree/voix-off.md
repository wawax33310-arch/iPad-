# Voix off — Réel rentrée UCPA Sport Station Bordeaux

Durée du montage : **42,3 s**. Ton : spontané, énergique, débit rapide, sourire
audible. On enchaîne sans respirer entre les blocs — c'est le montage qui
respire, pas la voix.

Les phrases marquées **(sous-titrée)** sont incrustées à l'image : dis-les mot
pour mot, sinon le texte et la voix se décalent. Les autres sont libres : à ce
moment-là, l'écran affiche un titre ou les noms d'activités.

| Timecode | Ce qui est à l'image | Texte à dire |
|---|---|---|
| 00:00,2 → 00:02,7 | Mur d'escalade, padel rooftop | **(sous-titrée)** « À Bordeaux y'a un endroit pour tout faire » |
| 00:02,8 → 00:04,1 | Escalade | « De l'escalade… » |
| 00:04,1 → 00:05,4 | Padel | « …du padel… » |
| 00:05,4 → 00:06,7 | Squash | « …du squash… » |
| 00:06,7 → 00:08,0 | Golf | « …du golf… » |
| 00:08,0 → 00:09,3 | Cours de fitness | « …du fitness… » |
| 00:09,3 → 00:10,6 | Muscu / cross training | « …de la muscu, un escape game… » |
| 00:10,6 → 00:12,0 | Planche apéro au Resto | « …un resto… » |
| 00:12,0 → 00:13,5 | Rooftop | « …et un rooftop. » |
| 00:13,6 → 00:15,2 | Titre « UCPA SPORT STATION » | **(sous-titrée)** « Tout ça au même endroit » |
| 00:15,7 → 00:17,2 | Titre « OFFRE DE RENTRÉE » | **(sous-titrée)** « Et pour la rentrée » |
| 00:17,4 → 00:22,2 | Golf, fitness, golf indoor | **(sous-titrée)** « la liberté du sans engagement au prix du avec engagement, à vie » |
| 00:22,4 → 00:23,6 | Escalade | **(sous-titrée)** « Frais de dossier offerts » |
| 00:23,7 → 00:24,9 | Padel, titre « -40 € » | **(sous-titrée)** « 40 euros d'économisés » |
| 00:25,1 → 00:26,6 | Yoga | **(sous-titrée)** « Jusqu'au 30 septembre » |
| 00:26,7 → 00:28,4 | Pétanque au coucher du soleil | **(sous-titrée)** « packs heures pleines ou creuses » |
| 00:28,2 → 00:30,2 | Titre « ENVIE D'ESSAYER AVANT ? » | « Envie d'essayer avant de t'abonner ? » |
| 00:30,0 → 00:32,0 | Titre « PORTES OUVERTES », samedi 12 septembre | « Rendez-vous samedi 12 septembre » |
| 00:32,1 → 00:34,6 | Squash, étiquette « 9H - 18H » | **(sous-titrée)** « C'est gratuit et ouvert à tous » |
| 00:34,7 → 00:36,6 | Golf enfants, photobooth | **(sous-titrée)** « Initiations escalade, squash, padel et golf » |
| 00:36,7 → 00:39,6 | Maquillage, jeux extérieurs, tapas rooftop | **(sous-titrée)** « Y'a de quoi occuper toute la famille » |
| 00:39,9 → 00:42,3 | Terrasse du rooftop, « INSCRIS-TOI » | **(sous-titrée)** « Inscris-toi sur le site UCPA » |

Environ 110 mots. À l'enregistrement, garde 1 à 2 dixièmes d'avance sur le
timecode : une voix qui arrive juste avant la coupe donne l'impression d'être
en avance sur l'image, et c'est ce qui fait le rythme.

## Poser la voix dans le montage

1. Enregistre d'une traite (mémo vocal du téléphone suffit), en suivant les
   timecodes ci-dessus.
2. Dépose le fichier dans `rushes/voix.m4a`.
3. Décommente dans `montage.yaml` :

```yaml
voix_off:
  fichier: rushes/voix.m4a
musique:
  fichier: rushes/musique.mp3
  gain_db: -20
  ducking: true
  fondu_sortie: 1.5
```

4. `ugcut render montage.yaml`

La voix est normalisée à −14 LUFS et la musique s'efface automatiquement
dessous. Si la voix enregistrée démarre trop tôt ou trop tard, ajuste
`decalage:` (en secondes, négatif pour avancer) plutôt que de refaire la prise.

## Sans voix off

Le montage livré fonctionne tel quel en muet : les étiquettes et les
sous-titres portent les trois messages. Il ne reste qu'à poser un son
tendance depuis Instagram au moment de la publication.
