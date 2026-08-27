"""Génération du fichier ASS : sous-titres façon UGC + étiquettes posées à l'image.

Le rendu se fait en une seule passe sur la timeline assemblée, donc tous les
repères temporels sont absolus (secondes depuis le début du montage).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from .spec import Ligne, Spec, Style


def couleur_ass(couleur: str, alpha: int = 0) -> str:
    """#RRGGBB -> &HAABBGGRR (ordre inversé, comme le veut ASS)."""
    c = couleur.strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6:
        c = "FFFFFF"
    r, v, b = c[0:2], c[2:4], c[4:6]
    return f"&H{alpha:02X}{b}{v}{r}".upper()


def horodatage(secondes: float) -> str:
    secondes = max(0.0, secondes)
    h = int(secondes // 3600)
    m = int((secondes % 3600) // 60)
    s = secondes % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def echapper(texte: str) -> str:
    """Neutralise ce que libass interpréterait comme des balises."""
    return (
        texte.replace("\\", "")
        .replace("{", "(")
        .replace("}", ")")
        .replace("\r", "")
        .replace("\n", "\\N")
        .strip()
    )


# --------------------------------------------------------------------------- #
# Sous-titres
# --------------------------------------------------------------------------- #

_RE_TEMPS_SRT = re.compile(
    r"(\d+):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*(\d+):(\d{2}):(\d{2})[,.](\d{1,3})"
)


def lire_srt(chemin: str) -> list[Ligne]:
    """Lit un .srt (ou .vtt simple) et retourne des lignes de timeline."""
    with open(chemin, "r", encoding="utf-8-sig") as fh:
        contenu = fh.read()
    lignes: list[Ligne] = []
    for bloc in re.split(r"\n\s*\n", contenu.strip()):
        m = _RE_TEMPS_SRT.search(bloc)
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        debut = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / (1000 if g[3] > 99 else 100)
        fin = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / (1000 if g[7] > 99 else 100)
        texte = " ".join(
            l.strip() for l in bloc.splitlines()
            if l.strip() and not _RE_TEMPS_SRT.search(l) and not l.strip().isdigit()
        )
        if texte and fin > debut:
            lignes.append(Ligne(debut=debut, fin=fin, texte=texte))
    return sorted(lignes, key=lambda l: l.debut)


@dataclass
class Groupe:
    debut: float
    fin: float
    mots: list[str]


def decouper(lignes: list[Ligne], mots_par_ecran: int) -> list[Groupe]:
    """Découpe chaque ligne en paquets de N mots, au prorata de leur longueur."""
    groupes: list[Groupe] = []
    for ligne in lignes:
        mots = [m for m in ligne.texte.split() if m]
        if not mots:
            continue
        paquets = [mots[i:i + mots_par_ecran] for i in range(0, len(mots), mots_par_ecran)]
        poids = [sum(len(m) + 1 for m in p) for p in paquets]
        total = sum(poids) or 1
        duree = max(0.0, ligne.fin - ligne.debut)
        curseur = ligne.debut
        for paquet, poid in zip(paquets, poids):
            part = duree * poid / total
            groupes.append(Groupe(debut=curseur, fin=curseur + part, mots=paquet))
            curseur += part
    return groupes


def _texte_groupe(groupe: Groupe, style: Style) -> list[tuple[float, float, str]]:
    """Un événement par mot actif : c'est ce qui donne le rythme 'mot qui pop'."""
    mots = [echapper(m.upper() if style.majuscules else m) for m in groupe.mots]
    if style.mode == "ligne":
        return [(groupe.debut, groupe.fin, " ".join(mots))]

    actif = couleur_ass(style.couleur_active)
    poids = [len(m) + 1 for m in mots]
    total = sum(poids) or 1
    duree = max(0.0, groupe.fin - groupe.debut)
    evenements: list[tuple[float, float, str]] = []
    curseur = groupe.debut
    for i, (mot, poid) in enumerate(zip(mots, poids)):
        part = max(0.12, duree * poid / total)
        rendu = " ".join(
            f"{{\\c{actif}\\fscx106\\fscy106}}{m}{{\\r}}" if j == i else m
            for j, m in enumerate(mots)
        )
        evenements.append((curseur, min(curseur + part, groupe.fin), rendu))
        curseur += part
    if evenements:  # le dernier mot tient jusqu'au bout du paquet
        d, _, t = evenements[-1]
        evenements[-1] = (d, groupe.fin, t)
    return evenements


# --------------------------------------------------------------------------- #
# Fichier ASS
# --------------------------------------------------------------------------- #

_FORMAT_STYLE = (
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
    "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
    "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"
)


def entete(spec: Spec) -> str:
    s, p = spec.style, spec.projet
    styles = [
        # Sous-titres : gros, gras, contour épais + ombre portée (lisible sur tout fond)
        "Style: Sub,{police},{taille},{blanc},{blanc},{noir},{ombre_c},-1,0,0,0,"
        "100,100,0,0,1,{contour},{ombre},5,90,90,90,1".format(
            police=s.police, taille=s.taille,
            blanc=couleur_ass(s.couleur), noir=couleur_ass("#000000"),
            ombre_c=couleur_ass("#000000", alpha=0x60),
            contour=s.contour, ombre=s.ombre,
        ),
        # Étiquette : BorderStyle=3 = pavé plein derrière le texte
        "Style: Sticker,{police},{taille},{texte},{texte},{fond},{fond},-1,0,0,0,"
        "100,100,0,0,3,14,0,5,60,60,60,1".format(
            police=s.police, taille=s.sticker_taille,
            texte=couleur_ass(s.sticker_couleur), fond=couleur_ass(s.sticker_fond),
        ),
        # Titre : texte plein cadre, sans pavé
        "Style: Titre,{police},{taille},{blanc},{blanc},{noir},{noir},-1,0,0,0,"
        "100,100,0,0,1,{contour},{ombre},5,60,60,60,1".format(
            police=s.police, taille=int(s.taille * 1.05),
            blanc=couleur_ass(s.couleur), noir=couleur_ass("#000000"),
            contour=s.contour, ombre=s.ombre,
        ),
        # Impact : mot-clé plein cadre, pour les arguments qui doivent claquer
        "Style: Impact,{police},{taille},{blanc},{blanc},{noir},{noir},-1,0,0,0,"
        "100,100,2,0,1,{contour},{ombre},5,50,50,50,1".format(
            police=s.police, taille=int(s.taille * 1.45),
            blanc=couleur_ass(s.couleur), noir=couleur_ass("#000000"),
            contour=int(s.contour * 1.3), ombre=s.ombre + 2,
        ),
    ]
    return "\n".join([
        "[Script Info]",
        "; généré par ugcut",
        "ScriptType: v4.00+",
        f"PlayResX: {p.largeur}",
        f"PlayResY: {p.hauteur}",
        "WrapStyle: 0",   # coupe intelligemment les groupes trop larges
        "ScaledBorderAndShadow: yes",
        "YCbCr Matrix: TV.709",
        "",
        "[V4+ Styles]",
        _FORMAT_STYLE,
        *styles,
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ])


def _dialogue(debut: float, fin: float, style: str, texte: str, couche: int = 0) -> str:
    return (f"Dialogue: {couche},{horodatage(debut)},{horodatage(fin)},{style},,"
            f"0,0,0,,{texte}")


def evenements_sous_titres(spec: Spec, lignes: list[Ligne]) -> list[str]:
    s, p = spec.style, spec.projet
    y = int(p.hauteur * min(max(s.position, 0.05), 0.95))
    sortie: list[str] = []
    for groupe in decouper(lignes, s.mots_par_ecran):
        for debut, fin, texte in _texte_groupe(groupe, s):
            if fin - debut < 0.05:
                continue
            balises = f"{{\\an5\\pos({p.largeur // 2},{y})\\fad(40,40)}}"
            sortie.append(_dialogue(debut, fin, "Sub", balises + texte))
    return sortie


# style du texte -> (style ASS, position par défaut, animation d'apparition)
_ANIM_DOUCE = "\\t(0,110,\\fscx108\\fscy108)\\t(110,220,\\fscx100\\fscy100)"
_ANIM_IMPACT = ("\\fscx140\\fscy140\\t(0,90,\\fscx97\\fscy97)"
                "\\t(90,170,\\fscx104\\fscy104)\\t(170,240,\\fscx100\\fscy100)")

STYLES_TEXTE = {
    "sticker": ("Sticker", None, _ANIM_DOUCE, "(90,120)"),
    "titre": ("Titre", 0.42, _ANIM_DOUCE, "(90,120)"),
    "impact": ("Impact", 0.40, _ANIM_IMPACT, "(50,90)"),
}


def evenements_stickers(spec: Spec, segments) -> list[str]:
    """Textes attachés à un plan : le repère temporel est relatif au plan."""
    sortie: list[str] = []
    for seg in segments:
        for texte in seg.plan.textes:
            debut = seg.debut_timeline + max(0.0, texte.t)
            fin = min(debut + max(0.2, texte.duree), seg.fin_timeline + 0.15)
            if fin <= debut:
                continue
            sortie.append(_evenement_texte(spec, texte, debut, fin))
    return sortie


def _evenement_texte(spec: Spec, texte, debut: float, fin: float) -> str:
    s, p = spec.style, spec.projet
    style_ass, position_defaut, animation, fondu = STYLES_TEXTE[texte.style]
    position = texte.position
    if position is None:
        position = position_defaut if position_defaut is not None else s.sticker_position
    y = int(p.hauteur * min(max(position, 0.05), 0.95))
    balises = f"{{\\an5\\pos({p.largeur // 2},{y})\\fad{fondu}{animation}}}"
    contenu = echapper(texte.contenu)
    if s.majuscules and texte.style != "sticker":
        contenu = contenu.upper()
    return _dialogue(debut, fin, style_ass, balises + contenu, couche=2)


def evenements_textes(spec: Spec) -> list[str]:
    """Textes posés à un instant absolu du montage, sans lien avec un plan.

    C'est ce qu'il faut pour une accroche qui doit tenir sur plusieurs plans.
    """
    return [
        _evenement_texte(spec, texte, texte.t, texte.t + max(0.2, texte.duree))
        for texte in spec.textes
    ]


def lignes_sous_titres(spec: Spec) -> list[Ligne]:
    """Sous-titres du montage : fichier .srt si fourni, sinon lignes inline."""
    st = spec.sous_titres
    if not st.actif:
        return []
    if st.fichier:
        chemin = spec.resoudre(st.fichier)
        if not os.path.exists(chemin):
            raise FileNotFoundError(f"Sous-titres introuvables : {chemin}")
        return lire_srt(chemin)
    return list(st.lignes)


def construire(spec: Spec, segments, cible: str) -> str | None:
    """Écrit le .ass complet. Retourne None s'il n'y a rien à incruster."""
    evenements = evenements_sous_titres(spec, lignes_sous_titres(spec))
    if spec.textes_actifs:
        evenements += evenements_stickers(spec, segments)
        evenements += evenements_textes(spec)
    if not evenements:
        return None
    with open(cible, "w", encoding="utf-8") as fh:
        fh.write(entete(spec) + "\n" + "\n".join(evenements) + "\n")
    return cible
