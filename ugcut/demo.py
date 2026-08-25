"""Génère des rushes de synthèse : permet d'essayer la chaîne sans tourner."""

from __future__ import annotations

import os

from .ffmpeg import ffmpeg, filtre_disponible

_POLICES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
)


def _police() -> str | None:
    return next((p for p in _POLICES if os.path.exists(p)), None)


def _etiquette(texte: str, taille: int = 90) -> str:
    """Étiquette le plan si le binaire ffmpeg embarque drawtext (pas toujours le cas)."""
    police = _police()
    if not police or not filtre_disponible("drawtext"):
        return ""
    return (
        f",drawtext=fontfile='{police}':text='{texte}':fontcolor=white@0.92:"
        f"fontsize={taille}:x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.35:boxborderw=24"
    )


def _clip(cible: str, *, largeur: int, hauteur: int, duree: float, couleur: str,
          texte: str, frequence: int, verbose: bool = False) -> str:
    """Un plan de synthèse : fond animé + étiquette + un souffle de 'voix'."""
    video = (
        f"color=c={couleur}:s={largeur}x{hauteur}:r=30:d={duree},"
        f"drawbox=x='mod(t*220,{largeur})':y={hauteur // 3}:w=160:h=160:"
        f"color=white@0.18:t=fill"
        + _etiquette(texte)
    )
    audio = (
        f"sine=frequency={frequence}:duration={duree},"
        f"tremolo=f=5:d=0.7,volume=0.18"
    )
    ffmpeg([
        "-f", "lavfi", "-i", video,
        "-f", "lavfi", "-i", audio,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
        "-t", f"{duree}", cible,
    ], verbose=verbose)
    return cible


def _image(cible: str, *, largeur: int, hauteur: int, couleur: str, texte: str,
           verbose: bool = False) -> str:
    ffmpeg([
        "-f", "lavfi", "-i",
        f"color=c={couleur}:s={largeur}x{hauteur}" + _etiquette(texte, 80),
        "-frames:v", "1", cible,
    ], verbose=verbose)
    return cible


def _musique(cible: str, duree: float = 40.0, verbose: bool = False) -> str:
    """Boucle instrumentale minimaliste (trois notes + pulsation)."""
    graphe = (
        f"sine=frequency=196:duration={duree}[a];"
        f"sine=frequency=294:duration={duree}[b];"
        f"sine=frequency=392:duration={duree}[c];"
        "[a][b][c]amix=inputs=3:normalize=1,"
        "tremolo=f=2:d=0.6,volume=0.35,"
        "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[out]"
    )
    ffmpeg(["-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={duree}",
            "-filter_complex", graphe, "-map", "[out]",
            "-c:a", "libmp3lame", "-b:a", "192k", cible], verbose=verbose)
    return cible


def generer(dossier: str, *, verbose: bool = False) -> dict[str, str]:
    """Crée le jeu de rushes de démonstration. Retourne {clé: chemin relatif}."""
    rushes = os.path.join(dossier, "rushes")
    os.makedirs(rushes, exist_ok=True)
    fichiers = {
        "hook": _clip(os.path.join(rushes, "hook.mp4"), largeur=1080, hauteur=1920,
                      duree=6, couleur="0x1B2A4A", texte="FACE CAM - HOOK",
                      frequence=210, verbose=verbose),
        "probleme": _clip(os.path.join(rushes, "probleme.mp4"), largeur=1080, hauteur=1920,
                          duree=7, couleur="0x3A2140", texte="FACE CAM - PROBLEME",
                          frequence=190, verbose=verbose),
        "produit": _clip(os.path.join(rushes, "produit.mp4"), largeur=1080, hauteur=1920,
                         duree=7, couleur="0x123B32", texte="FACE CAM - PRODUIT",
                         frequence=230, verbose=verbose),
        "broll": _clip(os.path.join(rushes, "broll_paysage.mp4"), largeur=1920, hauteur=1080,
                       duree=6, couleur="0x4A3416", texte="B-ROLL 16:9",
                       frequence=170, verbose=verbose),
        "packshot": _image(os.path.join(rushes, "packshot.png"), largeur=1200, hauteur=1500,
                           couleur="0xE8E2D8", texte="PACKSHOT", verbose=verbose),
        "musique": _musique(os.path.join(rushes, "musique.mp3"), verbose=verbose),
    }
    return {cle: os.path.relpath(chemin, dossier) for cle, chemin in fichiers.items()}
