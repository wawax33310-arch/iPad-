"""Orchestration du rendu : plans -> timeline -> incrustations -> mixage -> MP4."""

from __future__ import annotations

import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field

from . import audio as mix_audio
from . import soustitres
from .ffmpeg import ffmpeg
from .probe import analyser
from .segments import Segment, rendre as rendre_segment
from .spec import ErreurSpec, Spec
from .timeline import assembler


@dataclass
class Rendu:
    fichier: str
    duree: float
    segments: list[Segment] = field(default_factory=list)
    secondes_calcul: float = 0.0


def echapper_filtre(chemin: str) -> str:
    """Échappe un chemin pour l'intérieur d'un filtergraph ffmpeg."""
    chemin = chemin.replace("\\", "/")
    for caractere in (":", "'", "[", "]", ",", ";"):
        chemin = chemin.replace(caractere, "\\" + caractere)
    return chemin


def verifier_sources(spec: Spec) -> None:
    manquants = []
    for plan in spec.plans + spec.variantes:
        chemin = spec.resoudre(plan.source)
        if not os.path.exists(chemin):
            manquants.append(chemin)
    for media in (spec.musique, spec.voix_off):
        if media and not os.path.exists(spec.resoudre(media.fichier)):
            manquants.append(spec.resoudre(media.fichier))
    if spec.sous_titres.fichier:
        chemin = spec.resoudre(spec.sous_titres.fichier)
        if not os.path.exists(chemin):
            manquants.append(chemin)
    if manquants:
        liste = "\n  - ".join(manquants)
        raise ErreurSpec(f"Fichiers introuvables :\n  - {liste}")


def rendre(spec: Spec, *, sortie: str | None = None, verbose: bool = False,
           garder_temp: bool = False, silencieux: bool = False) -> Rendu:
    """Rend le montage complet et retourne le chemin du MP4 final."""
    depart = time.time()
    verifier_sources(spec)

    cible = spec.resoudre(sortie or spec.projet.sortie)
    os.makedirs(os.path.dirname(os.path.abspath(cible)) or ".", exist_ok=True)
    travail = tempfile.mkdtemp(prefix="ugcut-")

    def info(message: str) -> None:
        if not silencieux:
            print(message, flush=True)

    try:
        # 1. Normalisation plan par plan
        segments: list[Segment] = []
        for i, plan in enumerate(spec.plans):
            media = analyser(spec.resoudre(plan.source))
            etiquette = plan.id or plan.role or os.path.basename(plan.source)
            info(f"  [{i + 1}/{len(spec.plans)}] {etiquette} "
                 f"({media.largeur}x{media.hauteur}{' image' if media.est_image else ''})")
            segments.append(rendre_segment(spec, plan, i, travail, verbose=verbose))

        # 2. Assemblage + raccords
        timeline, duree = assembler(spec, segments, travail, verbose=verbose)
        info(f"  timeline : {duree:.2f}s, {len(segments)} plans")

        # 3. Sous-titres et étiquettes
        ass = soustitres.construire(spec, segments, os.path.join(travail, "textes.ass"))

        # 4. Passe finale : incrustation + mixage + encodage de diffusion
        args = ["-i", timeline, *mix_audio.entrees(spec)]
        voix_presente = spec.voix_off is not None or any(
            seg.media.a_du_son and seg.plan.garder_son for seg in segments
        )
        chaines, etiquette_audio = mix_audio.graphe(spec, duree, voix_presente=voix_presente)

        etapes_video = []
        if ass:
            filtre = f"subtitles=filename={echapper_filtre(ass)}"
            if spec.style.dossier_polices:
                filtre += f":fontsdir={echapper_filtre(spec.resoudre(spec.style.dossier_polices))}"
            etapes_video.append(filtre)
        etapes_video.append("format=yuv420p")
        chaines.insert(0, "[0:v]" + ",".join(etapes_video) + "[vout]")

        fps = spec.projet.fps
        args += [
            "-filter_complex", ";".join(chaines),
            "-map", "[vout]", "-map", f"[{etiquette_audio}]",
            "-t", f"{duree:.3f}",
            "-r", str(fps),
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
            "-g", str(fps * 2), "-movflags", "+faststart",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            cible,
        ]
        ffmpeg(args, verbose=verbose)
        return Rendu(fichier=cible, duree=duree, segments=segments,
                     secondes_calcul=time.time() - depart)
    finally:
        if garder_temp:
            print(f"  fichiers intermédiaires : {travail}")
        else:
            shutil.rmtree(travail, ignore_errors=True)
