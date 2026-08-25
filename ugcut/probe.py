"""Analyse des rushes : durée, dimensions, fps, présence d'une piste son, rotation."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache

from .ffmpeg import ErreurFFmpeg, ffmpeg_bin, ffprobe_bin, run

EXTENSIONS_IMAGE = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".heic", ".tif", ".tiff"}


@dataclass(frozen=True)
class Media:
    chemin: str
    duree: float          # secondes (0.0 pour une image fixe)
    largeur: int          # dimensions AFFICHÉES (rotation iPhone/iPad déjà appliquée)
    hauteur: int
    fps: float
    a_du_son: bool
    est_image: bool
    rotation: int = 0

    @property
    def vertical(self) -> bool:
        return self.hauteur >= self.largeur

    @property
    def ratio(self) -> float:
        return self.largeur / self.hauteur if self.hauteur else 0.0


def _fraction(txt: str | None, defaut: float = 30.0) -> float:
    if not txt:
        return defaut
    if "/" in txt:
        num, _, den = txt.partition("/")
        try:
            n, d = float(num), float(den)
        except ValueError:
            return defaut
        return n / d if d else defaut
    try:
        return float(txt)
    except ValueError:
        return defaut


def _rotation_depuis_ffprobe(flux: dict) -> int:
    tags = flux.get("tags") or {}
    if "rotate" in tags:
        try:
            return int(float(tags["rotate"])) % 360
        except ValueError:
            pass
    for donnee in flux.get("side_data_list") or []:
        if "rotation" in donnee:
            try:
                return int(round(float(donnee["rotation"]))) % 360
            except (TypeError, ValueError):
                pass
    return 0


def _probe_avec_ffprobe(chemin: str) -> Media | None:
    binaire = ffprobe_bin()
    if not binaire:
        return None
    res = run(
        [binaire, "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", chemin],
        check=False,
    )
    if res.code != 0:
        return None
    data = json.loads(res.stdout or "{}")
    flux_v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if flux_v is None:
        raise ErreurFFmpeg(f"Aucun flux vidéo dans {chemin}")
    a_du_son = any(s.get("codec_type") == "audio" for s in data.get("streams", []))
    duree = 0.0
    for source in (flux_v.get("duration"), (data.get("format") or {}).get("duration")):
        try:
            duree = float(source)
            break
        except (TypeError, ValueError):
            continue
    largeur, hauteur = int(flux_v.get("width", 0)), int(flux_v.get("height", 0))
    rotation = _rotation_depuis_ffprobe(flux_v)
    if rotation in (90, 270):
        largeur, hauteur = hauteur, largeur
    return Media(
        chemin=chemin,
        duree=max(duree, 0.0),
        largeur=largeur,
        hauteur=hauteur,
        fps=_fraction(flux_v.get("avg_frame_rate") or flux_v.get("r_frame_rate")),
        a_du_son=a_du_son,
        est_image=est_image(chemin),
        rotation=rotation,
    )


_RE_DUREE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)")
_RE_VIDEO = re.compile(r"Stream #\d+:\d+.*?: Video:.*?(\d{2,5})x(\d{2,5})")
_RE_FPS = re.compile(r"(\d+(?:\.\d+)?)\s+fps")
_RE_AUDIO = re.compile(r"Stream #\d+:\d+.*?: Audio:")
_RE_ROTATION = re.compile(r"rotation of (-?\d+(?:\.\d+)?) degrees")


def _probe_avec_ffmpeg(chemin: str) -> Media:
    """Repli quand ffprobe n'est pas installé : on lit le rapport de `ffmpeg -i`."""
    res = run([ffmpeg_bin(), "-hide_banner", "-i", chemin], check=False)
    sortie = res.stderr
    m_video = _RE_VIDEO.search(sortie)
    if not m_video:
        raise ErreurFFmpeg(f"Impossible de lire les dimensions de {chemin}")
    largeur, hauteur = int(m_video.group(1)), int(m_video.group(2))
    duree = 0.0
    if (m := _RE_DUREE.search(sortie)):
        duree = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    rotation = 0
    if (m := _RE_ROTATION.search(sortie)):
        rotation = int(round(float(m.group(1)))) % 360
    if rotation in (90, 270):
        largeur, hauteur = hauteur, largeur
    fps = float(m.group(1)) if (m := _RE_FPS.search(sortie)) else 30.0
    return Media(
        chemin=chemin,
        duree=duree,
        largeur=largeur,
        hauteur=hauteur,
        fps=fps,
        a_du_son=bool(_RE_AUDIO.search(sortie)),
        est_image=est_image(chemin),
        rotation=rotation,
    )


def est_image(chemin: str) -> bool:
    return os.path.splitext(chemin)[1].lower() in EXTENSIONS_IMAGE


@lru_cache(maxsize=256)
def analyser(chemin: str) -> Media:
    """Analyse un fichier source (résultat mis en cache)."""
    if not os.path.exists(chemin):
        raise ErreurFFmpeg(f"Source introuvable : {chemin}")
    media = _probe_avec_ffprobe(chemin) or _probe_avec_ffmpeg(chemin)
    if media.est_image:
        media = Media(**{**media.__dict__, "duree": 0.0, "a_du_son": False})
    return media
