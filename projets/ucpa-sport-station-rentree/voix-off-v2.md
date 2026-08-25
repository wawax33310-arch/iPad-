# Voix off — Réel UGC v2 (44,4 s)

Ton : spontané, énergique, débit rapide, sourire audible. Tu enchaînes sans
respirer entre les blocs — c'est le montage qui respire, pas la voix.

Les phrases **(sous-titrée)** sont incrustées à l'image : dis-les mot pour mot,
sinon le texte et la voix se décalent. Les autres sont libres — à ce moment-là,
l'écran affiche un mot-clé plein cadre.

| Timecode | À l'image | Texte à dire |
|---|---|---|
| 00:00,2 → 00:02,9 | Escalade, padel, rooftop, fitness, golf — cinq plans en 3 s | **(sous-titrée)** « Tu savais qu'à Bordeaux tu peux faire tout ça » |
| 00:03,2 → 00:07,4 | Escalade, padel (speed ramp) | **(sous-titrée)** « Que tu viennes pour te challenger ou découvrir un nouveau sport » |
| 00:07,6 → 00:10,9 | Squash, golf, fitness | **(sous-titrée)** « ou juste passer un bon moment entre amis » |
| 00:11,1 → 00:14,9 | Muscu, resto, rooftop | **(sous-titrée)** « il y a même un escape game, un resto et un rooftop » |
| 00:15,0 → 00:17,7 | « OFFRE DE RENTRÉE » | **(sous-titrée)** « C'est le meilleur moment pour s'inscrire » |
| 00:17,9 → 00:20,5 | « SANS ENGAGEMENT », « MÊME PRIX » | **(sous-titrée)** « le sans engagement au prix de l'engagement » |
| 00:20,7 → 00:22,5 | « À VIE » | **(sous-titrée)** « et ça, à vie » |
| 00:22,7 → 00:24,7 | « 40 € OFFERTS » | **(sous-titrée)** « les frais de dossier offerts » |
| 00:25,0 → 00:26,4 | Yoga, « 24 AOÛT - 30 SEPTEMBRE » | **(sous-titrée)** « jusqu'au 30 septembre » |
| 00:26,6 → 00:28,7 | Bar, rooftop | **(sous-titrée)** « packs heures pleines ou creuses » |
| 00:28,6 → 00:30,1 | « TU PRÉFÈRES TESTER ? » sur la vue de Bordeaux | « Tu préfères tester avant ? » |
| 00:29,9 → 00:31,7 | « PORTES OUVERTES », samedi 12 septembre | « Rendez-vous samedi 12 septembre » |
| 00:31,8 → 00:34,5 | Squash, golf, « 100 % GRATUIT » | **(sous-titrée)** « Initiations escalade, padel, squash et golf » |
| 00:34,8 → 00:37,6 | Photobooth, maquillage enfants | **(sous-titrée)** « des animations pour toute la famille » |
| 00:37,8 → 00:40,3 | Jeux extérieurs, tapas | **(sous-titrée)** « et de quoi se poser après » |
| 00:41,0 → 00:44,3 | « INSCRIS-TOI », terrasse du rooftop au ralenti | **(sous-titrée)** « sur le site UCPA Sport Station Bordeaux » |

Environ 120 mots. Sur le dernier plan, si ton débit le permet, tu peux
attaquer par « Alors, tu attends quoi ? » vers 00:40,4 et finir sur « On se
retrouve là-bas ! » — mais ne sacrifie pas le nom du site, c'est lui qui porte
l'inscription.

À l'enregistrement, garde un ou deux dixièmes d'avance sur le timecode : une
voix qui arrive juste avant la coupe donne l'impression d'être en avance sur
l'image, et c'est ce qui fait le rythme.

## Poser la voix

1. Enregistre d'une traite (mémo vocal du téléphone suffit).
2. Dépose le fichier dans `rushes/voix.m4a`.
3. Décommente dans `montage-v2.yaml` :

```yaml
voix_off: {fichier: rushes/voix.m4a}
musique:  {fichier: rushes/musique.mp3, gain_db: -20, ducking: true, fondu_sortie: 1.5}
```

4. `ugcut render montage-v2.yaml`

La voix est normalisée à −14 LUFS, la musique s'efface automatiquement dessous,
et le sound design reste au-dessus. Si la prise démarre trop tôt ou trop tard,
ajuste `decalage:` plutôt que de refaire la prise.

## Sans voix off

Le montage livré fonctionne tel quel : sous-titres, mots-clés animés et sound
design portent les trois messages. Il ne reste qu'à poser un son tendance
depuis Instagram au moment de la publication — c'est aussi ce que l'algorithme
préfère.
