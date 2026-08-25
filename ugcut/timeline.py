"""Assemblage de la timeline : positions des segments et raccords entre plans."""

from __future__ import annotations

import os
from typing import Iterable

from .ffmpeg import ffmpeg
from .segments import Segment
from .spec import TRANSITIONS, Spec

FONDU_MIN = 0.08
TB_VIDEO = "settb=1/90000"
TB_AUDIO = "asettb=1/48000"


def nom_xfade(transition: str) -> str | None:
    return TRANSITIONS.get(transition)


def recouvrement(precedent: Segment, courant: Segment) -> float:
    """Durée réelle du raccord, bridée pour ne jamais avaler un plan entier."""
    if nom_xfade(courant.plan.transition) is None:
        return 0.0
    marge = 0.5 * min(precedent.duree, courant.duree)
    return max(FONDU_MIN, min(courant.plan.transition_duree, marge))


def placer(segments: list[Segment]) -> float:
    """Calcule debut_timeline de chaque segment. Retourne la durée totale."""
    fin = 0.0
    for i, seg in enumerate(segments):
        chevauchement = 0.0 if i == 0 else recouvrement(segments[i - 1], seg)
        seg.debut_timeline = max(0.0, fin - chevauchement)
        fin = seg.debut_timeline + seg.duree
    return fin


def _concat_demuxer(segments: Iterable[Segment], dossier: str, cible: str,
                    *, verbose: bool = False) -> str:
    liste = os.path.join(dossier, "concat.txt")
    with open(liste, "w", encoding="utf-8") as fh:
        for seg in segments:
            chemin = os.path.abspath(seg.chemin).replace("'", "'\\''")
            fh.write(f"file '{chemin}'\n")
    ffmpeg(["-f", "concat", "-safe", "0", "-i", liste, "-c", "copy",
            "-movflags", "+faststart", cible], verbose=verbose)
    return cible


def _concat_xfade(spec: Spec, segments: list[Segment], cible: str,
                  *, verbose: bool = False) -> str:
    """Chaîne xfade/concat. Les bases de temps sont réalignées à chaque étape :
    concat et xfade ne sortent pas la même, et xfade refuse de les mélanger."""
    args: list[str] = []
    for seg in segments:
        args += ["-i", seg.chemin]

    chaines: list[str] = []
    for i in range(len(segments)):
        chaines.append(f"[{i}:v]fps={spec.projet.fps},format=yuv420p,{TB_VIDEO}[v{i}e]")
        chaines.append(f"[{i}:a]aresample=48000,asetpts=PTS-STARTPTS,{TB_AUDIO}[a{i}e]")

    v_acc, a_acc = "v0e", "a0e"
    for i in range(1, len(segments)):
        chevauchement = recouvrement(segments[i - 1], segments[i])
        v_out, a_out = f"vx{i}", f"ax{i}"
        if chevauchement > 0:
            effet = nom_xfade(segments[i].plan.transition) or "fade"
            offset = segments[i].debut_timeline
            chaines.append(
                f"[{v_acc}][v{i}e]xfade=transition={effet}:"
                f"duration={chevauchement:.3f}:offset={offset:.3f},{TB_VIDEO}[{v_out}]"
            )
            chaines.append(
                f"[{a_acc}][a{i}e]acrossfade=d={chevauchement:.3f}:c1=tri:c2=tri,"
                f"{TB_AUDIO}[{a_out}]"
            )
        else:
            chaines.append(f"[{v_acc}][v{i}e]concat=n=2:v=1:a=0,{TB_VIDEO}[{v_out}]")
            chaines.append(f"[{a_acc}][a{i}e]concat=n=2:v=0:a=1,{TB_AUDIO}[{a_out}]")
        v_acc, a_acc = v_out, a_out

    args += [
        "-filter_complex", ";".join(chaines),
        "-map", f"[{v_acc}]", "-map", f"[{a_acc}]",
        "-r", str(spec.projet.fps),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-video_track_timescale", "90000",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        cible,
    ]
    ffmpeg(args, verbose=verbose)
    return cible


def assembler(spec: Spec, segments: list[Segment], dossier: str,
              *, verbose: bool = False) -> tuple[str, float]:
    """Colle les segments bout à bout. Retourne (fichier, durée totale)."""
    duree = placer(segments)
    cible = os.path.join(dossier, "timeline.mp4")
    if len(segments) == 1:
        return segments[0].chemin, duree
    avec_raccords = any(
        recouvrement(segments[i - 1], segments[i]) > 0 for i in range(1, len(segments))
    )
    if avec_raccords:
        return _concat_xfade(spec, segments, cible, verbose=verbose), duree
    return _concat_demuxer(segments, dossier, cible, verbose=verbose), duree
