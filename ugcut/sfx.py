"""Sound design : whoosh, impacts et pops synthétisés, calés sur le montage.

Les sons sont générés par ffmpeg (aucun fichier à fournir), puis assemblés en
une piste unique mixée au rendu final. Un fichier maison peut remplacer
n'importe quel son intégré.
"""

from __future__ import annotations

from dataclasses import dataclass

from .ffmpeg import ffmpeg

STEREO = "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo"


@dataclass
class Effet:
    """Un son posé à un instant précis de la timeline finale."""
    t: float
    son: str = "whoosh"
    fichier: str | None = None
    duree: float | None = None
    gain_db: float = 0.0


def _whoosh(duree: float) -> str:
    """Souffle large : bruit rose (le bruit brun perd tout son énergie au
    passe-haut) et une enveloppe rapide à la montée, lente à la retombée."""
    montee = duree * 0.35
    return (
        f"anoisesrc=color=pink:duration={duree:.3f}:amplitude=0.9,"
        f"highpass=f=220,lowpass=f=7000,"
        f"afade=t=in:st=0:d={montee:.3f}:curve=qua,"
        f"afade=t=out:st={montee:.3f}:d={duree - montee:.3f}:curve=exp,"
        f"volume=1.8,{STEREO}"
    )


def _impact(duree: float) -> str:
    """Basse courte à décroissance rapide : le « boum » sous une coupe.

    Le générateur `sine` de ffmpeg sort à -18 dBFS : on synthétise donc tout à
    l'expression, pour que les sons partagent la même référence de niveau.
    """
    return (
        f"aevalsrc='0.45*(sin(2*PI*62*t)+0.35*sin(2*PI*124*t))*exp(-9*t)':"
        f"d={duree:.3f}:s=48000,{STEREO}"
    )


def _pop(duree: float) -> str:
    """Clic bref pour l'apparition d'un mot."""
    return (
        f"aevalsrc='0.5*sin(2*PI*980*t)*exp(-26*t)':d={duree:.3f}:s=48000,{STEREO}"
    )


def _riser(duree: float) -> str:
    """Montée en tension avant une révélation."""
    return (
        f"aevalsrc='0.45*sin(2*PI*(150+520*t/{duree:.3f})*t)':d={duree:.3f}:s=48000,"
        f"volume=volume='pow(t/{duree:.3f},2)':eval=frame,"
        f"afade=t=out:st={duree * 0.92:.3f}:d={duree * 0.08:.3f},{STEREO}"
    )


def _sub_drop(duree: float) -> str:
    """Descente grave : ponctue la fin d'un bloc."""
    return (
        f"aevalsrc='0.45*sin(2*PI*(150-105*t/{duree:.3f})*t)':d={duree:.3f}:s=48000,"
        f"volume=volume='exp(-3*t)':eval=frame,{STEREO}"
    )


# nom -> (générateur, durée par défaut)
SONS = {
    "whoosh": (_whoosh, 0.42),
    "impact": (_impact, 0.55),
    "pop": (_pop, 0.14),
    "riser": (_riser, 1.20),
    "drop": (_sub_drop, 0.80),
}


def construire_piste(effets: list[Effet], duree_totale: float, cible: str,
                     *, resoudre=None, verbose: bool = False) -> str | None:
    """Rend tous les effets dans une seule piste audio. None s'il n'y en a pas."""
    effets = [e for e in effets if 0.0 <= e.t < duree_totale]
    if not effets:
        return None

    entrees: list[str] = []
    chaines: list[str] = []
    etiquettes: list[str] = []

    for i, effet in enumerate(effets):
        etiquette = f"s{i}"
        etapes: list[str] = []
        if effet.fichier:
            chemin = resoudre(effet.fichier) if resoudre else effet.fichier
            entrees += ["-i", chemin]
            source = f"{len([a for a in entrees if a == '-i']) - 1}:a"
            etapes.append(STEREO)
        else:
            generateur, defaut = SONS[effet.son]
            duree = effet.duree or defaut
            entrees += ["-f", "lavfi", "-i", generateur(duree)]
            source = f"{len([a for a in entrees if a == '-i']) - 1}:a"
        if abs(effet.gain_db) > 0.01:
            etapes.append(f"volume={effet.gain_db:.2f}dB")
        if effet.t > 0:
            ms = int(round(effet.t * 1000))
            etapes.append(f"adelay={ms}|{ms}")
        etapes.append(f"apad=whole_dur={duree_totale:.3f}")
        chaines.append(f"[{source}]" + ",".join(etapes) + f"[{etiquette}]")
        etiquettes.append(etiquette)

    melange = "".join(f"[{e}]" for e in etiquettes)
    chaines.append(
        f"{melange}amix=inputs={len(etiquettes)}:normalize=0:dropout_transition=0,"
        f"alimiter=limit=0.9:level=disabled,atrim=duration={duree_totale:.3f}[sfx]"
    )
    ffmpeg([*entrees, "-filter_complex", ";".join(chaines), "-map", "[sfx]",
            "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", cible], verbose=verbose)
    return cible


def depuis_montage(spec, segments) -> list[Effet]:
    """Effets déclarés dans le montage : `son:` sur un plan + `effets_sonores:`."""
    effets = [
        Effet(t=max(0.0, seg.debut_timeline + seg.plan.son_decalage), son=seg.plan.son,
              gain_db=seg.plan.son_gain_db)
        for seg in segments if seg.plan.son
    ]
    effets += list(spec.effets_sonores)
    return sorted(effets, key=lambda e: e.t)
