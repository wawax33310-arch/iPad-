"""Construction des chaînes de filtres vidéo : recadrage 9:16, punch-in, vitesse."""

from __future__ import annotations

from .probe import Media
from .spec import Plan, Projet

# Facteur de suréchantillonnage avant un punch-in : on recadre plus grand que la
# cible pour que le zoom pioche dans des vrais pixels au lieu d'interpoler.
MARGE_ZOOM = 1.5


def chaine_recadrage(media: Media, largeur: int, hauteur: int, plan: Plan) -> str:
    """Amène n'importe quelle source au format cible (par défaut 1080x1920)."""
    cadrage = min(max(plan.cadrage, 0.0), 1.0)
    if plan.recadrage == "remplir":
        return (
            f"scale={largeur}:{hauteur}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={largeur}:{hauteur}:'(iw-ow)*{cadrage:.4f}':'(ih-oh)*{cadrage:.4f}',"
            f"setsar=1"
        )
    if plan.recadrage == "flou":
        # Fond = la même image, agrandie, floutée et assombrie ; devant = l'image entière.
        return (
            f"split=2[bg][fg];"
            f"[bg]scale={largeur}:{hauteur}:force_original_aspect_ratio=increase,"
            f"crop={largeur}:{hauteur},gblur=sigma=28,eq=brightness=-0.12:saturation=0.7[bgb];"
            f"[fg]scale={largeur}:{hauteur}:force_original_aspect_ratio=decrease:flags=lanczos[fgs];"
            f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,setsar=1"
        )
    # ajuster : bandes noires
    return (
        f"scale={largeur}:{hauteur}:force_original_aspect_ratio=decrease:flags=lanczos,"
        f"pad={largeur}:{hauteur}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
    )


def chaine_zoom(plan: Plan, projet: Projet, duree_sortie: float) -> str:
    """Punch-in linéaire via zoompan, calé sur le nombre exact d'images du plan."""
    if not plan.zoom_actif:
        return ""
    images = max(2, int(round(duree_sortie * projet.fps)))
    zd, zv = max(1.0, plan.zoom_de), max(1.0, plan.zoom_vers)
    z = f"{zd:.4f}+({zv - zd:.4f})*on/{images - 1}"
    return (
        f"zoompan=z='{z}':d=1:fps={projet.fps}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"s={projet.largeur}x{projet.hauteur},setsar=1"
    )


def chaine_video(media: Media, plan: Plan, projet: Projet, duree_sortie: float) -> str:
    """Chaîne complète d'un plan : vitesse -> cadence -> recadrage -> punch-in."""
    etapes: list[str] = []
    if abs(plan.vitesse - 1.0) > 1e-6:
        etapes.append(f"setpts=PTS/{plan.vitesse:.6f}")
    etapes.append(f"fps={projet.fps}")

    if plan.zoom_actif:
        inter_l = int(projet.largeur * MARGE_ZOOM) // 2 * 2
        inter_h = int(projet.hauteur * MARGE_ZOOM) // 2 * 2
        etapes.append(chaine_recadrage(media, inter_l, inter_h, plan))
        etapes.append(chaine_zoom(plan, projet, duree_sortie))
    else:
        etapes.append(chaine_recadrage(media, projet.largeur, projet.hauteur, plan))

    etapes.append("format=yuv420p")
    return ",".join(e for e in etapes if e)


def chaine_atempo(vitesse: float) -> str:
    """atempo ne gère que 0.5x..2x par instance : on empile si besoin."""
    if abs(vitesse - 1.0) < 1e-6:
        return ""
    facteurs: list[float] = []
    reste = vitesse
    while reste > 2.0:
        facteurs.append(2.0)
        reste /= 2.0
    while reste < 0.5:
        facteurs.append(0.5)
        reste /= 0.5
    facteurs.append(reste)
    return ",".join(f"atempo={f:.6f}" for f in facteurs)


def chaine_audio(plan: Plan) -> str:
    etapes = ["aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo"]
    if (tempo := chaine_atempo(plan.vitesse)):
        etapes.append(tempo)
    if abs(plan.volume - 1.0) > 1e-6:
        etapes.append(f"volume={plan.volume:.4f}")
    etapes.append("asetpts=PTS-STARTPTS")
    return ",".join(etapes)
