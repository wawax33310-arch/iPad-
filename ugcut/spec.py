"""Lecture et validation du fichier de montage (YAML ou JSON).

Les clés sont en français, les équivalents anglais sont acceptés (voir ALIAS).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Iterable

from .sfx import SONS, Effet

RECADRAGES = {"remplir", "flou", "ajuster"}
ZOOM_AUTO = 1.08          # amplitude du punch-in quand `zoom: auto`
STYLES_TEXTE = {"sticker", "titre", "impact"}
MODES_SOUS_TITRES = {"mot_a_mot", "ligne"}

# transition -> nom xfade ; "cut" = coupe franche (pas de xfade)
TRANSITIONS = {
    "cut": None, "coupe": None, "franche": None,
    "fondu": "fade", "fondu_rapide": "fadefast", "fondu_lent": "fadeslow",
    "noir": "fadeblack", "flash": "fadewhite", "gris": "fadegrays",
    "whip": "hlslice", "whip_gauche": "hlslice", "whip_droite": "hrslice",
    "glisse_gauche": "slideleft", "glisse_droite": "slideright",
    "glisse_haut": "slideup", "glisse_bas": "slidedown",
    "doux_gauche": "smoothleft", "doux_droite": "smoothright",
    "zoom": "zoomin", "pixel": "pixelize", "flou_h": "hblur",
    "cercle": "circleopen", "dissous": "dissolve",
    "couvre_haut": "coverup", "revele_haut": "revealup",
}

ALIAS = {
    # projet
    "project": "projet", "name": "nom", "width": "largeur", "height": "hauteur",
    "output": "sortie", "duration": "duree", "max_duration": "duree_max",
    "quality": "crf",
    # style
    "font": "police", "size": "taille", "color": "couleur",
    "highlight": "couleur_active", "outline": "contour", "shadow": "ombre",
    "position": "position", "words_per_screen": "mots_par_ecran",
    "uppercase": "majuscules", "mode": "mode", "fonts_dir": "dossier_polices",
    # plans
    "shots": "plans", "clips": "plans", "source": "source", "start": "debut",
    "end": "fin", "speed": "vitesse", "reframe": "recadrage", "framing": "cadrage",
    "zoom": "zoom", "from": "de", "to": "vers", "transition": "transition",
    "keep_audio": "garder_son", "volume": "volume", "role": "role",
    "texts": "textes", "text": "contenu", "at": "t",
    "sound": "son", "sound_effects": "effets_sonores", "sfx": "effets_sonores",
    # audio
    "music": "musique", "gain_db": "gain_db", "voiceover": "voix_off",
    "offset": "decalage", "fade_in": "fondu_entree", "fade_out": "fondu_sortie",
    # sous-titres
    "subtitles": "sous_titres", "file": "fichier", "lines": "lignes",
    "variants": "variantes",
}


class ErreurSpec(ValueError):
    """Le fichier de montage est invalide."""


def _normaliser(valeur: Any) -> Any:
    """Traduit récursivement les clés anglaises vers leur équivalent français."""
    if isinstance(valeur, dict):
        return {ALIAS.get(str(k), str(k)): _normaliser(v) for k, v in valeur.items()}
    if isinstance(valeur, list):
        return [_normaliser(v) for v in valeur]
    return valeur


def _flottant(source: dict, cle: str, defaut: float | None = None,
              *, contexte: str = "") -> float | None:
    if cle not in source or source[cle] is None:
        return defaut
    try:
        return float(source[cle])
    except (TypeError, ValueError):
        raise ErreurSpec(f"{contexte}{cle} doit être un nombre (reçu : {source[cle]!r})")


@dataclass
class Tempo:
    """Tempo de la musique : la grille sur laquelle tombent les coupes."""
    bpm: float
    signature: int = 4          # temps par mesure

    @property
    def temps(self) -> float:
        """Durée d'un temps, en secondes."""
        return 60.0 / self.bpm

    @property
    def mesure(self) -> float:
        return self.temps * self.signature


@dataclass
class Projet:
    nom: str = "montage"
    largeur: int = 1080
    hauteur: int = 1920
    fps: int = 30
    sortie: str = "sortie/montage.mp4"
    duree_max: float | None = None
    crf: int = 21          # 18 = quasi transparent, 23 = léger, 28 = visible

    @property
    def ratio(self) -> float:
        return self.largeur / self.hauteur


@dataclass
class Style:
    police: str = "Liberation Sans"
    taille: int = 92
    couleur: str = "#FFFFFF"
    couleur_active: str = "#FFE600"
    contour: int = 8
    ombre: int = 3
    position: float = 0.74          # fraction de la hauteur (0 = haut, 1 = bas)
    mots_par_ecran: int = 3
    majuscules: bool = True
    mode: str = "mot_a_mot"
    # style des stickers (petites étiquettes posées à l'image)
    sticker_taille: int = 62
    sticker_couleur: str = "#111111"
    sticker_fond: str = "#FFFFFF"
    sticker_position: float = 0.16
    dossier_polices: str = ""      # pour embarquer une police de marque


@dataclass
class Texte:
    """Étiquette posée sur un plan (repère temporel relatif au plan)."""
    contenu: str
    t: float = 0.0
    duree: float = 1.6
    position: float | None = None
    style: str = "sticker"          # sticker | titre


@dataclass
class Plan:
    source: str
    id: str = ""
    debut: float = 0.0
    fin: float | None = None
    duree: float | None = None
    temps: float | None = None      # durée à l'écran, en temps de la musique
    vitesse: float = 1.0
    recadrage: str = "remplir"
    cadrage: float = 0.5            # 0 = gauche/haut, 1 = droite/bas
    zoom_de: float = 1.0
    zoom_vers: float = 1.0
    transition: str = "cut"         # transition ENTRANTE (vers ce plan)
    transition_duree: float = 0.25
    garder_son: bool = True
    volume: float = 1.0
    role: str = ""                  # hook | probleme | solution | preuve | cta | broll
    textes: list[Texte] = field(default_factory=list)
    zoom_auto: bool = False         # direction décidée à l'assemblage, en alternance
    son: str = ""                   # effet sonore joué au début du plan
    son_gain_db: float = 0.0
    son_decalage: float = 0.0

    @property
    def zoom_actif(self) -> bool:
        return abs(self.zoom_de - 1.0) > 1e-3 or abs(self.zoom_vers - 1.0) > 1e-3


@dataclass
class Ligne:
    """Une ligne de sous-titre sur la timeline finale."""
    debut: float
    fin: float
    texte: str


@dataclass
class SousTitres:
    fichier: str | None = None
    lignes: list[Ligne] = field(default_factory=list)
    actif: bool = True


@dataclass
class Musique:
    fichier: str
    gain_db: float = -18.0
    ducking: bool = True
    debut: float = 0.0
    fondu_entree: float = 0.3
    fondu_sortie: float = 1.2


@dataclass
class VoixOff:
    fichier: str
    decalage: float = 0.0
    gain_db: float = 0.0


@dataclass
class Spec:
    projet: Projet
    style: Style
    tempo: Tempo | None
    plans: list[Plan]
    sous_titres: SousTitres
    musique: Musique | None = None
    voix_off: VoixOff | None = None
    textes: list[Texte] = field(default_factory=list)   # posés sur la timeline
    textes_actifs: bool = True      # coupe d'un coup toutes les incrustations
    variantes: list[Plan] = field(default_factory=list)
    effets_sonores: list[Effet] = field(default_factory=list)
    effets_gain_db: float = -6.0
    racine: str = "."
    chemin: str = ""

    def resoudre(self, chemin: str) -> str:
        """Résout un chemin relatif au fichier de montage."""
        return chemin if os.path.isabs(chemin) else os.path.normpath(os.path.join(self.racine, chemin))


# --------------------------------------------------------------------------- #
# Chargement
# --------------------------------------------------------------------------- #

def _lire_textes(brut: Iterable[Any], contexte: str) -> list[Texte]:
    textes: list[Texte] = []
    for i, item in enumerate(brut or []):
        if isinstance(item, str):
            textes.append(Texte(contenu=item))
            continue
        if not isinstance(item, dict):
            raise ErreurSpec(f"{contexte}textes[{i}] doit être une chaîne ou un objet")
        contenu = item.get("contenu")
        if not contenu:
            raise ErreurSpec(f"{contexte}textes[{i}] : clé `contenu` manquante")
        style = str(item.get("style", "sticker")).lower()
        if style not in STYLES_TEXTE:
            raise ErreurSpec(f"{contexte}textes[{i}].style doit être : "
                             f"{', '.join(sorted(STYLES_TEXTE))}")
        textes.append(Texte(
            contenu=str(contenu),
            t=_flottant(item, "t", 0.0, contexte=contexte) or 0.0,
            duree=_flottant(item, "duree", 1.6, contexte=contexte) or 1.6,
            position=_flottant(item, "position", None, contexte=contexte),
            style=style,
        ))
    return textes


def _lire_plan(brut: Any, contexte: str) -> Plan:
    if isinstance(brut, str):
        brut = {"source": brut}
    if not isinstance(brut, dict):
        raise ErreurSpec(f"{contexte} doit être un objet ou un chemin de fichier")
    source = brut.get("source")
    if not source:
        raise ErreurSpec(f"{contexte} : clé `source` manquante")

    zoom = brut.get("zoom") or {}
    zoom_auto = isinstance(zoom, str) and zoom.lower() == "auto"
    if zoom_auto:
        zoom = {}
    elif isinstance(zoom, (int, float)):        # zoom: 1.08 -> punch-in de 1.0 vers 1.08
        zoom = {"de": 1.0, "vers": float(zoom)}
    if not isinstance(zoom, dict):
        raise ErreurSpec(f"{contexte}zoom doit être `auto`, un nombre, ou {{de, vers}}")

    transition = str(brut.get("transition", "cut")).lower()
    if transition not in TRANSITIONS:
        connues = ", ".join(sorted(TRANSITIONS))
        raise ErreurSpec(f"{contexte}transition inconnue : {transition!r}. Au choix : {connues}")

    recadrage = str(brut.get("recadrage", "remplir")).lower()
    if recadrage not in RECADRAGES:
        raise ErreurSpec(f"{contexte}recadrage doit être : {', '.join(sorted(RECADRAGES))}")

    cadrage = brut.get("cadrage", 0.5)
    if isinstance(cadrage, str):
        cadrage = {"gauche": 0.0, "haut": 0.0, "centre": 0.5,
                   "droite": 1.0, "bas": 1.0}.get(cadrage.lower(), 0.5)

    son = str(brut.get("son", "")).lower()
    if son and son not in SONS:
        raise ErreurSpec(f"{contexte}son inconnu : {son!r}. Au choix : {', '.join(sorted(SONS))}")

    vitesse = _flottant(brut, "vitesse", 1.0, contexte=contexte) or 1.0
    if not 0.25 <= vitesse <= 4.0:
        raise ErreurSpec(f"{contexte}vitesse doit être entre 0.25 et 4.0 (reçu {vitesse})")

    return Plan(
        source=str(source),
        id=str(brut.get("id", "")),
        debut=_flottant(brut, "debut", 0.0, contexte=contexte) or 0.0,
        fin=_flottant(brut, "fin", None, contexte=contexte),
        duree=_flottant(brut, "duree", None, contexte=contexte),
        temps=_flottant(brut, "temps", None, contexte=contexte),
        vitesse=vitesse,
        recadrage=recadrage,
        cadrage=float(cadrage),
        zoom_de=float(zoom.get("de", 1.0)),
        zoom_vers=float(zoom.get("vers", 1.0)),
        zoom_auto=zoom_auto,
        transition=transition,
        transition_duree=_flottant(brut, "transition_duree", 0.25, contexte=contexte) or 0.25,
        garder_son=bool(brut.get("garder_son", True)),
        volume=_flottant(brut, "volume", 1.0, contexte=contexte) or 1.0,
        role=str(brut.get("role", "")).lower(),
        textes=_lire_textes(brut.get("textes"), contexte),
        son=son,
        son_gain_db=_flottant(brut, "son_gain_db", 0.0, contexte=contexte) or 0.0,
        son_decalage=_flottant(brut, "son_decalage", 0.0, contexte=contexte) or 0.0,
    )


def _caler_sur_le_tempo(plans: list[Plan], tempo: Tempo) -> None:
    """Convertit les durées exprimées en temps, et compense les fondus.

    Un fondu de durée T fait démarrer le plan T secondes plus tôt : sans
    compensation, tout ce qui suit sort de la grille. On rallonge donc le plan
    de T pour que la coupe suivante retombe sur le temps.
    """
    for plan in plans:
        if plan.temps is None:
            continue
        secondes = plan.temps * tempo.temps
        if plan.transition in TRANSITIONS and TRANSITIONS[plan.transition] is not None:
            secondes += plan.transition_duree
        plan.duree = secondes * plan.vitesse


def _resoudre_zooms_auto(plans: list[Plan]) -> None:
    """`zoom: auto` : on alterne punch-in et punch-out d'un plan à l'autre.

    Deux plans voisins qui zooment dans le même sens se ressemblent ; en
    alternant, chaque coupe change le sens du mouvement et se voit.
    """
    for i, plan in enumerate(plans):
        if not plan.zoom_auto:
            continue
        if i % 2 == 0:
            plan.zoom_de, plan.zoom_vers = 1.0, ZOOM_AUTO
        else:
            plan.zoom_de, plan.zoom_vers = ZOOM_AUTO, 1.0


def _lire_sous_titres(brut: Any) -> SousTitres:
    if brut is None:
        return SousTitres()
    if isinstance(brut, bool):
        return SousTitres(actif=brut)
    if not isinstance(brut, dict):
        raise ErreurSpec("sous_titres doit être un objet")
    lignes = []
    for i, item in enumerate(brut.get("lignes") or []):
        if not isinstance(item, dict) or "texte" not in item:
            raise ErreurSpec(f"sous_titres.lignes[{i}] : attendu {{debut, fin, texte}}")
        debut = _flottant(item, "debut", 0.0, contexte=f"sous_titres.lignes[{i}].") or 0.0
        fin = _flottant(item, "fin", None, contexte=f"sous_titres.lignes[{i}].")
        if fin is None:
            fin = debut + (_flottant(item, "duree", 1.5) or 1.5)
        if fin <= debut:
            raise ErreurSpec(f"sous_titres.lignes[{i}] : `fin` doit être après `debut`")
        lignes.append(Ligne(debut=debut, fin=fin, texte=str(item["texte"])))
    return SousTitres(
        fichier=brut.get("fichier"),
        lignes=sorted(lignes, key=lambda l: l.debut),
        actif=bool(brut.get("actif", True)),
    )


def _lire_effets(brut: Any) -> list[Effet]:
    """Effets sonores posés à un instant absolu de la timeline."""
    if not brut:
        return []
    if not isinstance(brut, list):
        raise ErreurSpec("effets_sonores doit être une liste")
    effets: list[Effet] = []
    for i, item in enumerate(brut):
        contexte = f"effets_sonores[{i}]."
        if not isinstance(item, dict):
            raise ErreurSpec(f"{contexte[:-1]} doit être un objet {{t, son}}")
        son = str(item.get("son", "whoosh")).lower()
        fichier = item.get("fichier")
        if not fichier and son not in SONS:
            raise ErreurSpec(f"{contexte}son inconnu : {son!r}. "
                             f"Au choix : {', '.join(sorted(SONS))}")
        effets.append(Effet(
            t=_flottant(item, "t", 0.0, contexte=contexte) or 0.0,
            son=son,
            fichier=str(fichier) if fichier else None,
            duree=_flottant(item, "duree", None, contexte=contexte),
            gain_db=_flottant(item, "gain_db", 0.0, contexte=contexte) or 0.0,
        ))
    return sorted(effets, key=lambda e: e.t)


def charger(chemin: str) -> Spec:
    """Charge un fichier de montage YAML ou JSON et le valide."""
    if not os.path.exists(chemin):
        raise ErreurSpec(f"Fichier de montage introuvable : {chemin}")
    with open(chemin, "r", encoding="utf-8") as fh:
        contenu = fh.read()
    if chemin.lower().endswith((".yaml", ".yml")):
        try:
            import yaml  # type: ignore
        except ImportError:
            raise ErreurSpec("PyYAML est requis pour les fichiers .yaml (pip install pyyaml)")
        brut = yaml.safe_load(contenu)
    else:
        brut = json.loads(contenu)
    if not isinstance(brut, dict):
        raise ErreurSpec("Le fichier de montage doit contenir un objet à la racine")
    return depuis_dict(brut, racine=os.path.dirname(os.path.abspath(chemin)), chemin=chemin)


def depuis_dict(brut: dict, *, racine: str = ".", chemin: str = "") -> Spec:
    brut = _normaliser(brut)

    p = brut.get("projet") or {}
    projet = Projet(
        nom=str(p.get("nom", "montage")),
        largeur=int(p.get("largeur", 1080)),
        hauteur=int(p.get("hauteur", 1920)),
        fps=int(p.get("fps", 30)),
        sortie=str(p.get("sortie", "sortie/montage.mp4")),
        duree_max=_flottant(p, "duree_max", None, contexte="projet."),
        crf=int(p.get("crf", p.get("qualite", 21))),
    )
    if not 0 <= projet.crf <= 51:
        raise ErreurSpec("projet.crf doit être entre 0 et 51 (18-28 en pratique)")
    if projet.largeur % 2 or projet.hauteur % 2:
        raise ErreurSpec("projet.largeur et projet.hauteur doivent être pairs (contrainte H.264)")

    s = brut.get("style") or {}
    style = Style(
        police=str(s.get("police", Style.police)),
        taille=int(s.get("taille", Style.taille)),
        couleur=str(s.get("couleur", Style.couleur)),
        couleur_active=str(s.get("couleur_active", Style.couleur_active)),
        contour=int(s.get("contour", Style.contour)),
        ombre=int(s.get("ombre", Style.ombre)),
        position=float(s.get("position", Style.position)),
        mots_par_ecran=max(1, int(s.get("mots_par_ecran", Style.mots_par_ecran))),
        majuscules=bool(s.get("majuscules", Style.majuscules)),
        mode=str(s.get("mode", Style.mode)),
        sticker_taille=int(s.get("sticker_taille", Style.sticker_taille)),
        sticker_couleur=str(s.get("sticker_couleur", Style.sticker_couleur)),
        sticker_fond=str(s.get("sticker_fond", Style.sticker_fond)),
        sticker_position=float(s.get("sticker_position", Style.sticker_position)),
        dossier_polices=str(s.get("dossier_polices", "")),
    )
    if style.mode not in MODES_SOUS_TITRES:
        raise ErreurSpec(f"style.mode doit être : {', '.join(sorted(MODES_SOUS_TITRES))}")

    plans_bruts = brut.get("plans")
    if not plans_bruts:
        raise ErreurSpec("Aucun plan : ajoute au moins une entrée sous `plans:`")
    plans = [_lire_plan(pl, f"plans[{i}].") for i, pl in enumerate(plans_bruts)]
    variantes = [_lire_plan(pl, f"variantes[{i}].")
                 for i, pl in enumerate(brut.get("variantes") or [])]
    for v in variantes:
        v.transition = "cut"
    plans[0].transition = "cut"      # rien à fondre avant le premier plan

    tempo = None
    if (t := brut.get("tempo")):
        if isinstance(t, (int, float)):
            t = {"bpm": t}
        bpm = _flottant(t, "bpm", None, contexte="tempo.")
        if not bpm or not 30 <= bpm <= 300:
            raise ErreurSpec("tempo.bpm doit être un nombre entre 30 et 300")
        tempo = Tempo(bpm=bpm, signature=int(t.get("signature", 4)))
        _caler_sur_le_tempo(plans, tempo)
        _caler_sur_le_tempo(variantes, tempo)
    elif any(p.temps is not None for p in plans):
        raise ErreurSpec("des plans utilisent `temps:` mais `tempo:` n'est pas défini")

    _resoudre_zooms_auto(plans)

    musique = None
    if (m := brut.get("musique")):
        if isinstance(m, str):
            m = {"fichier": m}
        if not m.get("fichier"):
            raise ErreurSpec("musique.fichier est requis")
        musique = Musique(
            fichier=str(m["fichier"]),
            gain_db=_flottant(m, "gain_db", -18.0, contexte="musique.") or -18.0,
            ducking=bool(m.get("ducking", True)),
            debut=_flottant(m, "debut", 0.0, contexte="musique.") or 0.0,
            fondu_entree=_flottant(m, "fondu_entree", 0.3, contexte="musique.") or 0.3,
            fondu_sortie=_flottant(m, "fondu_sortie", 1.2, contexte="musique.") or 1.2,
        )

    voix_off = None
    if (v := brut.get("voix_off")):
        if isinstance(v, str):
            v = {"fichier": v}
        if not v.get("fichier"):
            raise ErreurSpec("voix_off.fichier est requis")
        voix_off = VoixOff(
            fichier=str(v["fichier"]),
            decalage=_flottant(v, "decalage", 0.0, contexte="voix_off.") or 0.0,
            gain_db=_flottant(v, "gain_db", 0.0, contexte="voix_off.") or 0.0,
        )

    return Spec(
        projet=projet,
        style=style,
        tempo=tempo,
        plans=plans,
        sous_titres=_lire_sous_titres(brut.get("sous_titres")),
        textes=_lire_textes(brut.get("textes"), "textes."),
        textes_actifs=bool(brut.get("textes_actifs", True)),
        musique=musique,
        voix_off=voix_off,
        variantes=variantes,
        effets_sonores=_lire_effets(brut.get("effets_sonores")),
        effets_gain_db=_flottant(brut, "effets_gain_db", -6.0) or -6.0,
        racine=racine,
        chemin=chemin,
    )
