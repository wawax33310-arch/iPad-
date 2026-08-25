"""Mixage : voix normalisée, musique de fond, ducking sous la voix."""

from __future__ import annotations

from .spec import Spec

# Cible de loudness : -14 LUFS, ce que visent TikTok / Reels / Shorts.
LOUDNESS_CIBLE = -14.0
DUCKING = "sidechaincompress=threshold=0.035:ratio=8:attack=15:release=280:makeup=1"


def entrees(spec: Spec) -> list[str]:
    """Entrées ffmpeg supplémentaires (musique, voix off), dans l'ordre attendu."""
    args: list[str] = []
    if spec.musique:
        # -stream_loop : la musique boucle si elle est plus courte que le montage
        args += ["-stream_loop", "-1", "-ss", f"{spec.musique.debut:.3f}",
                 "-i", spec.resoudre(spec.musique.fichier)]
    if spec.voix_off:
        args += ["-i", spec.resoudre(spec.voix_off.fichier)]
    return args


def graphe(spec: Spec, duree: float, *, voix_presente: bool) -> tuple[list[str], str]:
    """Construit les chaînes audio. Retourne (chaînes, étiquette de sortie)."""
    index = 1
    index_musique = index_voix_off = None
    if spec.musique:
        index_musique = index
        index += 1
    if spec.voix_off:
        index_voix_off = index
        index += 1

    chaines: list[str] = []

    # --- bus voix -----------------------------------------------------------
    etiquette_voix = None
    if index_voix_off is not None:
        vo = spec.voix_off
        etapes = ["aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo"]
        if vo.decalage > 0:
            ms = int(vo.decalage * 1000)
            etapes.append(f"adelay={ms}|{ms}")
        elif vo.decalage < 0:
            etapes.append(f"atrim=start={abs(vo.decalage):.3f},asetpts=PTS-STARTPTS")
        if abs(vo.gain_db) > 0.01:
            etapes.append(f"volume={vo.gain_db:.2f}dB")
        etapes.append(f"loudnorm=I={LOUDNESS_CIBLE}:TP=-1.5:LRA=11")
        chaines.append(f"[{index_voix_off}:a]" + ",".join(etapes) + "[voix]")
        etiquette_voix = "voix"
    elif voix_presente:
        chaines.append(
            f"[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
            f"loudnorm=I={LOUDNESS_CIBLE}:TP=-1.5:LRA=11[voix]"
        )
        etiquette_voix = "voix"

    # --- bus musique --------------------------------------------------------
    etiquette_musique = None
    if index_musique is not None:
        mus = spec.musique
        etapes = [
            "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo",
            f"atrim=duration={duree:.3f}",
            "asetpts=PTS-STARTPTS",
            f"volume={mus.gain_db:.2f}dB",
        ]
        if mus.fondu_entree > 0:
            etapes.append(f"afade=t=in:st=0:d={mus.fondu_entree:.3f}")
        if mus.fondu_sortie > 0:
            debut_fondu = max(0.0, duree - mus.fondu_sortie)
            etapes.append(f"afade=t=out:st={debut_fondu:.3f}:d={mus.fondu_sortie:.3f}")
        chaines.append(f"[{index_musique}:a]" + ",".join(etapes) + "[musique]")
        etiquette_musique = "musique"

    # --- mixage -------------------------------------------------------------
    if etiquette_voix and etiquette_musique:
        if spec.musique and spec.musique.ducking:
            chaines.append(f"[{etiquette_voix}]asplit=2[voix_mix][voix_sc]")
            chaines.append(f"[{etiquette_musique}][voix_sc]{DUCKING}[musique_duck]")
            chaines.append(
                "[musique_duck][voix_mix]amix=inputs=2:normalize=0:dropout_transition=0[mix]"
            )
        else:
            chaines.append(
                f"[{etiquette_musique}][{etiquette_voix}]"
                "amix=inputs=2:normalize=0:dropout_transition=0[mix]"
            )
        brut = "mix"
    elif etiquette_voix:
        brut = etiquette_voix
    elif etiquette_musique:
        brut = etiquette_musique
    else:
        chaines.append("[0:a]anull[mix]")
        brut = "mix"

    chaines.append(f"[{brut}]alimiter=limit=0.95:level=disabled,"
                   f"aresample=48000,atrim=duration={duree:.3f}[aout]")
    return chaines, "aout"
