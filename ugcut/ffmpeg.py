"""Localisation et exécution des binaires ffmpeg / ffprobe."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence


class ErreurFFmpeg(RuntimeError):
    """ffmpeg est absent, ou a rendu un code de sortie non nul."""


def _depuis_imageio() -> str | None:
    try:
        import imageio_ffmpeg  # type: ignore
    except Exception:
        return None
    try:
        chemin = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None
    return chemin if chemin and os.path.exists(chemin) else None


def ffmpeg_bin() -> str:
    """Retourne le binaire ffmpeg : $UGCUT_FFMPEG, puis le PATH, puis imageio-ffmpeg."""
    forced = os.environ.get("UGCUT_FFMPEG")
    if forced:
        if not shutil.which(forced) and not os.path.exists(forced):
            raise ErreurFFmpeg(f"UGCUT_FFMPEG pointe vers un binaire introuvable : {forced}")
        return forced
    trouve = shutil.which("ffmpeg") or _depuis_imageio()
    if not trouve:
        raise ErreurFFmpeg(
            "ffmpeg est introuvable.\n"
            "  macOS   : brew install ffmpeg\n"
            "  Debian  : sudo apt install ffmpeg\n"
            "  Sinon   : pip install imageio-ffmpeg (binaire statique)\n"
            "  Ou      : export UGCUT_FFMPEG=/chemin/vers/ffmpeg"
        )
    return trouve


def ffprobe_bin() -> str | None:
    """ffprobe si disponible ; None sinon (on retombe alors sur `ffmpeg -i`)."""
    forced = os.environ.get("UGCUT_FFPROBE")
    if forced and (shutil.which(forced) or os.path.exists(forced)):
        return forced
    return shutil.which("ffprobe")


@dataclass
class Resultat:
    code: int
    stdout: str
    stderr: str


def run(args: Sequence[str], *, verbose: bool = False, check: bool = True) -> Resultat:
    """Lance une commande, remonte la fin de stderr en cas d'échec (ffmpeg est bavard)."""
    if verbose:
        print("  $ " + " ".join(str(a) for a in args))
    proc = subprocess.run(
        [str(a) for a in args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        errors="replace",
    )
    res = Resultat(proc.returncode, proc.stdout, proc.stderr)
    if check and proc.returncode != 0:
        queue = "\n".join(res.stderr.strip().splitlines()[-25:])
        raise ErreurFFmpeg(f"Échec de la commande (code {proc.returncode}) :\n{queue}")
    return res


def ffmpeg(args: Sequence[str], *, verbose: bool = False) -> Resultat:
    """`ffmpeg -hide_banner -nostdin -y <args>`."""
    base = [ffmpeg_bin(), "-hide_banner", "-nostdin", "-loglevel", "error", "-y"]
    return run([*base, *args], verbose=verbose)


@lru_cache(maxsize=1)
def filtres_disponibles() -> frozenset[str]:
    """Filtres compilés dans le binaire ffmpeg courant."""
    res = run([ffmpeg_bin(), "-hide_banner", "-filters"], check=False)
    noms = set()
    for ligne in res.stdout.splitlines():
        morceaux = ligne.split()
        if len(morceaux) >= 2 and not ligne.startswith("Filters:"):
            noms.add(morceaux[1])
    return frozenset(noms)


def filtre_disponible(nom: str) -> bool:
    return nom in filtres_disponibles()
