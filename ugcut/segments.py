"""Découpe et normalisation : chaque plan devient un segment au format cible."""

from __future__ import annotations

import os
from dataclasses import dataclass

from .ffmpeg import ffmpeg
from .probe import Media, analyser
from .spec import ErreurSpec, Plan, Spec
from .video import chaine_audio, chaine_video

DUREE_IMAGE_DEFAUT = 2.5
MARGE_FIN = 0.04     # on ne colle pas la coupe à la dernière image du rush


@dataclass
class Segment:
    plan: Plan
    chemin: str
    duree: float            # durée du segment rendu (après vitesse)
    debut_timeline: float   # position sur le montage final (renseignée à l'assemblage)
    media: Media

    @property
    def fin_timeline(self) -> float:
        return self.debut_timeline + self.duree


def bornes(plan: Plan, media: Media) -> tuple[float, float]:
    """Retourne (debut, longueur lue dans la source) en secondes.

    `debut`, `fin` et `duree` se lisent tous dans le rush ; c'est `vitesse` qui
    détermine ensuite la durée à l'écran (longueur / vitesse).
    """
    if media.est_image:
        return 0.0, plan.duree if plan.duree is not None else DUREE_IMAGE_DEFAUT

    debut = max(0.0, plan.debut)
    if media.duree and debut >= media.duree:
        raise ErreurSpec(
            f"{plan.source} : `debut` ({debut:.2f}s) dépasse la durée du rush "
            f"({media.duree:.2f}s)"
        )
    if plan.duree is not None:
        longueur = plan.duree
    elif plan.fin is not None:
        if plan.fin <= debut:
            raise ErreurSpec(f"{plan.source} : `fin` doit être après `debut`")
        longueur = plan.fin - debut
    else:
        longueur = max(0.0, (media.duree or DUREE_IMAGE_DEFAUT) - debut - MARGE_FIN)

    if media.duree:
        longueur = min(longueur, max(0.0, media.duree - debut))
    if longueur <= 0.05:
        raise ErreurSpec(f"{plan.source} : le plan est vide ou trop court")
    return debut, longueur


def duree_sortie(plan: Plan, media: Media) -> float:
    """Durée du plan une fois posé sur la timeline."""
    _, longueur = bornes(plan, media)
    return longueur / plan.vitesse


def rendre(spec: Spec, plan: Plan, index: int, dossier: str, *, verbose: bool = False) -> Segment:
    """Rend un plan vers un MP4 intermédiaire aux dimensions/cadence du projet."""
    source = spec.resoudre(plan.source)
    media = analyser(source)
    debut, longueur = bornes(plan, media)
    sortie_duree = longueur / plan.vitesse
    cible = os.path.join(dossier, f"seg_{index:03d}.mp4")

    args: list[str] = []
    if media.est_image:
        args += ["-loop", "1", "-t", f"{longueur:.4f}", "-i", source]
    else:
        args += ["-ss", f"{debut:.4f}", "-t", f"{longueur:.4f}", "-i", source]

    utilise_son_source = media.a_du_son and plan.garder_son and spec.voix_off is None
    if not utilise_son_source:
        args += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
        etiquette_audio = "1:a"
    else:
        etiquette_audio = "0:a"

    graphe = (
        f"[0:v]{chaine_video(media, plan, spec.projet, sortie_duree)}[v];"
        f"[{etiquette_audio}]{chaine_audio(plan)}[a]"
    )

    args += [
        "-filter_complex", graphe,
        "-map", "[v]", "-map", "[a]",
        "-t", f"{sortie_duree:.4f}",
        "-r", str(spec.projet.fps),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-video_track_timescale", "90000",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        cible,
    ]
    ffmpeg(args, verbose=verbose)
    return Segment(plan=plan, chemin=cible, duree=sortie_duree, debut_timeline=0.0, media=media)
