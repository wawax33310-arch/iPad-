# Tourner sur iPhone / iPad pour du UGC

Le montage ne rattrape pas un rush raté. Voici le minimum à verrouiller avant
d'appuyer sur REC, et comment sortir les fichiers proprement.

## Réglages caméra

| Réglage | Valeur | Pourquoi |
|---|---|---|
| Format | **1080p · 60 i/s** | Assez de définition pour un 1080 × 1920, et 60 i/s laisse la place à un ralenti |
| Appareil photo → Formats | **Haute efficacité** ou **Le plus compatible** | HEVC pèse moins lourd, H.264 s'ouvre partout. `ugcut` lit les deux |
| HDR vidéo | **désactivé** | Le HDR/Dolby Vision vire délavé une fois converti en SDR |
| Verrouillage AE/AF | **activé** (appui long sur le sujet) | Sinon l'expo « pompe » à chaque mouvement |
| Orientation | **verticale** | Ne recadre pas un 16:9 si tu peux tourner en 9:16 |

Sur iPad : cale-le, ne le tiens pas à bout de bras. Le léger tremblement d'un
iPhone tenu à la main est un signal d'authenticité ; un iPad qui tangue est
juste désagréable.

## Lumière et son

- **Une fenêtre en face**, jamais dans le dos. C'est 90 % du rendu.
- **Le son passe avant l'image.** Micro-cravate à 20 € > n'importe quel réglage
  vidéo. À défaut : des écouteurs filaires, ou l'appareil à moins d'un mètre,
  dans une pièce avec du tissu (rideaux, canapé, lit).
- Coupe les notifications : mode Avion pendant la prise.

## Cadrage

- Visage à mi-buste, yeux au **tiers supérieur** de l'image.
- Laisse de l'air en haut et en bas : les zones utiles vont de 220 à 1550 px
  (voir [recette-ugc.md](recette-ugc.md#7-zones-de-sécurité-1080--1920)).
- Rien d'important dans la bande de droite (icônes TikTok).

## Tourner pour le montage

- **Filme trois hooks d'affilée**, formulés différemment, dans le même cadre.
  C'est ce qui alimente `variantes:` et le test A/B.
- **Laisse tourner entre les prises** : les meilleures phrases arrivent juste
  après « voilà, c'est bon ».
- **Répète chaque phrase deux fois.** Au montage, tu gardes la meilleure et
  le raccord passe en jump cut.
- Tourne le **b-roll séparément**, en gestes lents et courts : les mains, le
  produit, le geste d'usage. 3 à 4 s par geste suffisent.

## Sortir les fichiers

Depuis Photos, **Partager → Enregistrer dans Fichiers** exporte la vidéo
d'origine. Évite AirDrop vers un Mac « optimisé » et surtout l'envoi par
messagerie : les rushes sont recompressés et tu perds en qualité avant même
d'avoir monté.

Ensuite : dépose tout dans `rushes/` et note les timecodes utiles au fil de la
relecture — ce sont les `debut:` de ton `montage.yaml`.

## Rotation

Les vidéos iPhone/iPad portent leur orientation dans une métadonnée plutôt que
dans les pixels. `ugcut` la lit et travaille sur les dimensions **affichées** :
un rush qui s'ouvre à l'endroit sur ton téléphone est recadré à l'endroit.

## HEVC : quand convertir

`ugcut` décode le HEVC directement. Si ton ffmpeg est ancien ou que le décodage
rame, convertis une fois pour toutes :

```bash
ffmpeg -i IMG_1234.MOV -c:v libx264 -crf 18 -preset slow \
       -c:a aac -b:a 192k rushes/hook.mp4
```

## Fichiers ProRes / 4K

Inutile pour du UGC : tu vas sortir en 1080 × 1920 de toute façon, et les
rushes 4K ralentissent chaque rendu. Si tu n'as que du 4K, `ugcut` s'en
arrange — mais compte deux à trois fois plus de temps de calcul.
