"""Contrôle du montage avant rendu : les règles du format UGC, encodées.

Rien ici ne bloque le rendu — c'est un relecteur, pas un gendarme.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from .probe import analyser
from .segments import Segment, duree_sortie
from .soustitres import lignes_sous_titres
from .spec import Spec
from .timeline import recouvrement

OK, CONSEIL, ALERTE = "ok", "conseil", "alerte"

DUREE_IDEALE = (15.0, 45.0)
DUREE_MAX_RECOMMANDEE = 60.0
HOOK_MAX = 2.5
PLAN_MOYEN_MAX = 3.0
PLAN_STATIQUE_MAX = 5.0
COUVERTURE_MIN = 0.80
ZONE_SOUS_TITRES = (0.55, 0.84)   # au-dessus de l'UI TikTok/Reels
ZONE_STICKER = (0.06, 0.34)


@dataclass
class Constat:
    niveau: str
    code: str
    message: str

    def __str__(self) -> str:
        puce = {OK: "✓", CONSEIL: "·", ALERTE: "!"}[self.niveau]
        return f"{puce} [{self.code}] {self.message}"


def _durees(spec: Spec) -> tuple[list[float], list[str]]:
    durees: list[float] = []
    erreurs: list[str] = []
    for plan in spec.plans:
        chemin = spec.resoudre(plan.source)
        if not os.path.exists(chemin):
            erreurs.append(plan.source)
            durees.append(0.0)
            continue
        try:
            durees.append(duree_sortie(plan, analyser(chemin)))
        except Exception as exc:            # rush illisible : on le signale sans planter
            erreurs.append(f"{plan.source} ({exc})")
            durees.append(0.0)
    return durees, erreurs


def analyser_montage(spec: Spec) -> list[Constat]:
    constats: list[Constat] = []
    durees, erreurs = _durees(spec)

    for manquant in erreurs:
        constats.append(Constat(ALERTE, "source", f"Rush illisible ou absent : {manquant}"))

    # Durée totale, raccords déduits
    total = sum(durees)
    for i in range(1, len(spec.plans)):
        if durees[i - 1] and durees[i]:
            faux_prec = Segment(spec.plans[i - 1], "", durees[i - 1], 0.0, None)  # type: ignore[arg-type]
            faux_cour = Segment(spec.plans[i], "", durees[i], 0.0, None)          # type: ignore[arg-type]
            total -= recouvrement(faux_prec, faux_cour)

    if total == 0:
        return constats or [Constat(ALERTE, "vide", "Aucun plan exploitable")]

    if total > DUREE_MAX_RECOMMANDEE:
        constats.append(Constat(ALERTE, "duree", (
            f"{total:.1f}s : au-delà de 60s le taux de complétion s'effondre. "
            "Coupe les respirations et les redites.")))
    elif not DUREE_IDEALE[0] <= total <= DUREE_IDEALE[1]:
        constats.append(Constat(CONSEIL, "duree", (
            f"{total:.1f}s : la zone confortable en UGC est 15-45s.")))
    else:
        constats.append(Constat(OK, "duree", f"Durée : {total:.1f}s"))

    if spec.projet.duree_max and total > spec.projet.duree_max:
        constats.append(Constat(ALERTE, "duree_max", (
            f"{total:.1f}s dépasse la limite fixée dans le projet "
            f"({spec.projet.duree_max:.0f}s)")))

    # Hook : les 2 premières secondes décident de tout
    hook = durees[0]
    if hook > HOOK_MAX:
        constats.append(Constat(ALERTE, "hook", (
            f"Premier plan de {hook:.1f}s : rentre dans le vif avant {HOOK_MAX:.0f}s "
            "(coupe le silence avant la première syllabe).")))
    else:
        constats.append(Constat(OK, "hook", f"Hook : {hook:.1f}s"))

    lignes = lignes_sous_titres(spec)
    texte_tot = any(t.t <= 1.0 for t in spec.plans[0].textes)
    texte_st = any(l.debut <= 1.0 for l in lignes)
    if not (texte_tot or texte_st):
        constats.append(Constat(ALERTE, "hook_texte", (
            "Rien d'écrit à l'image dans la 1re seconde : ajoute l'accroche en texte, "
            "elle est lue avant d'être entendue.")))

    # Rythme
    moyenne = total / len(durees)
    if moyenne > PLAN_MOYEN_MAX:
        constats.append(Constat(CONSEIL, "rythme", (
            f"Plan moyen {moyenne:.1f}s : en UGC on coupe toutes les 1,5 à 3s.")))
    else:
        constats.append(Constat(OK, "rythme", f"Plan moyen : {moyenne:.1f}s "
                                              f"({len(durees)} plans)"))

    for plan, duree in zip(spec.plans, durees):
        if duree > PLAN_STATIQUE_MAX and not plan.zoom_actif:
            nom = plan.id or plan.source
            constats.append(Constat(CONSEIL, "plan_statique", (
                f"{nom} : {duree:.1f}s sans mouvement. Ajoute un punch-in "
                "(zoom: 1.06) ou recoupe.")))

    # Sous-titres : 85 % des vues se font sans le son
    if not lignes:
        constats.append(Constat(ALERTE, "sous_titres", (
            "Aucun sous-titre : indispensable, la majorité regarde sans le son.")))
    else:
        couvert = sum(max(0.0, min(l.fin, total) - l.debut) for l in lignes)
        ratio = couvert / total
        if ratio < COUVERTURE_MIN:
            constats.append(Constat(ALERTE, "sous_titres", (
                f"Sous-titres sur {ratio * 100:.0f}% de la vidéo seulement "
                f"(vise {COUVERTURE_MIN * 100:.0f}%+).")))
        else:
            constats.append(Constat(OK, "sous_titres",
                                    f"Sous-titres : {ratio * 100:.0f}% de couverture"))
        if lignes[-1].fin > total + 0.5:
            constats.append(Constat(ALERTE, "sous_titres_hors_champ", (
                f"Le dernier sous-titre finit à {lignes[-1].fin:.1f}s, "
                f"après la fin du montage ({total:.1f}s).")))

    # Appel à l'action
    debut_fin = total - 5.0
    cta = any(p.role == "cta" for p in spec.plans)
    cta = cta or any(l.debut >= debut_fin and l.texte for l in lignes)
    cta = cta or any(
        t for p, d in zip(spec.plans, durees) for t in p.textes if p.role == "cta"
    )
    if not cta:
        constats.append(Constat(ALERTE, "cta", (
            "Pas d'appel à l'action identifié sur les 5 dernières secondes "
            "(role: cta sur le dernier plan, ou une phrase de fin).")))
    else:
        constats.append(Constat(OK, "cta", "Appel à l'action présent"))

    # Zones de sécurité (UI des plateformes)
    if not ZONE_SOUS_TITRES[0] <= spec.style.position <= ZONE_SOUS_TITRES[1]:
        constats.append(Constat(CONSEIL, "zone_sure", (
            f"style.position = {spec.style.position} : garde les sous-titres entre "
            f"{ZONE_SOUS_TITRES[0]} et {ZONE_SOUS_TITRES[1]}, sinon l'UI TikTok "
            "et la légende Reels passent dessus.")))
    if not ZONE_STICKER[0] <= spec.style.sticker_position <= ZONE_STICKER[1]:
        constats.append(Constat(CONSEIL, "zone_sure_sticker", (
            "style.sticker_position sort de la zone haute lisible "
            f"({ZONE_STICKER[0]}-{ZONE_STICKER[1]}).")))

    # Son
    voix = spec.voix_off is not None or any(
        p.garder_son and os.path.exists(spec.resoudre(p.source))
        and analyser(spec.resoudre(p.source)).a_du_son
        for p in spec.plans
    )
    if spec.musique:
        if not -26.0 <= spec.musique.gain_db <= -8.0:
            constats.append(Constat(CONSEIL, "musique_gain", (
                f"musique.gain_db = {spec.musique.gain_db} : la fourchette utile est "
                "-24 à -12 dB sous la voix.")))
        if voix and not spec.musique.ducking:
            constats.append(Constat(CONSEIL, "ducking", (
                "Musique sans ducking alors qu'il y a de la voix : "
                "active `ducking: true`.")))
    elif not voix:
        sound_design = bool(spec.effets_sonores) or any(p.son for p in spec.plans)
        if sound_design:
            constats.append(Constat(CONSEIL, "audio", (
                "Seul le sound design est présent : prévois la voix off, ou un son "
                "tendance ajouté à la publication.")))
        else:
            constats.append(Constat(ALERTE, "audio", "Ni voix ni musique : la vidéo est muette."))

    # Format de sortie
    if (spec.projet.largeur, spec.projet.hauteur) != (1080, 1920):
        constats.append(Constat(CONSEIL, "format", (
            f"{spec.projet.largeur}x{spec.projet.hauteur} : le format natif "
            "TikTok/Reels/Shorts est 1080x1920.")))
    if spec.projet.fps not in (24, 25, 30, 50, 60):
        constats.append(Constat(CONSEIL, "fps", f"{spec.projet.fps} fps est inhabituel."))

    for plan, duree in zip(spec.plans, durees):
        if plan.vitesse > 1.35 and plan.garder_son:
            constats.append(Constat(CONSEIL, "vitesse", (
                f"{plan.id or plan.source} accéléré à {plan.vitesse}x avec le son : "
                "la voix devient vite désagréable au-delà de 1,3x.")))

    return constats


def resume(constats: list[Constat]) -> tuple[int, int, int]:
    """(alertes, conseils, ok)"""
    return (
        sum(c.niveau == ALERTE for c in constats),
        sum(c.niveau == CONSEIL for c in constats),
        sum(c.niveau == OK for c in constats),
    )
