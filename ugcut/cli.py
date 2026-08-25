"""Interface en ligne de commande : init, check, render, variantes, demo."""

from __future__ import annotations

import argparse
import copy
import os
import sys
from pathlib import Path

from . import __version__
from .ffmpeg import ErreurFFmpeg
from .lint import analyser_montage, resume
from .probe import analyser
from .segments import duree_sortie
from .spec import ErreurSpec, Plan, Spec, charger

MODELES = Path(__file__).parent / "modeles"


def _modele(nom: str) -> str:
    return (MODELES / nom).read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Commandes
# --------------------------------------------------------------------------- #

def cmd_init(args: argparse.Namespace) -> int:
    dossier = Path(args.dossier)
    (dossier / "rushes").mkdir(parents=True, exist_ok=True)
    (dossier / "sortie").mkdir(parents=True, exist_ok=True)
    cible = dossier / "montage.yaml"
    if cible.exists() and not args.forcer:
        print(f"{cible} existe déjà (utilise --forcer pour écraser).")
        return 1
    cible.write_text(_modele("montage.yaml"), encoding="utf-8")
    print(f"Projet initialisé dans {dossier}/")
    print(f"  1. dépose tes rushes dans {dossier}/rushes/")
    print(f"  2. décris le montage dans {cible}")
    print(f"  3. python -m ugcut render {cible}")
    return 0


def _afficher_controle(spec: Spec) -> int:
    constats = analyser_montage(spec)
    for constat in constats:
        print("  " + str(constat))
    alertes, conseils, _ = resume(constats)
    print(f"\n  {alertes} alerte(s), {conseils} conseil(s)")
    return alertes


def cmd_check(args: argparse.Namespace) -> int:
    spec = charger(args.montage)
    print(f"Contrôle de {args.montage} :\n")
    alertes = _afficher_controle(spec)
    return 1 if (alertes and args.strict) else 0


def cmd_render(args: argparse.Namespace) -> int:
    from .render import rendre  # import tardif : ffmpeg n'est requis qu'ici

    spec = charger(args.montage)
    if not args.sans_controle:
        print("Contrôle :")
        alertes = _afficher_controle(spec)
        if alertes and args.strict:
            print("\nRendu interrompu (--strict). Corrige les alertes ci-dessus.")
            return 1
        print()

    print(f"Rendu de « {spec.projet.nom} » :")
    rendu = rendre(spec, sortie=args.sortie, verbose=args.verbose,
                   garder_temp=args.garder_temp)
    taille = os.path.getsize(rendu.fichier) / 1e6
    print(f"\n✓ {rendu.fichier} — {rendu.duree:.2f}s, {taille:.1f} Mo "
          f"(rendu en {rendu.secondes_calcul:.1f}s)")
    return 0


def _spec_variante(spec: Spec, variante: Plan) -> Spec:
    """Remplace le hook par une variante et recale les sous-titres."""
    nouvelle = copy.deepcopy(spec)
    origine = duree_sortie(spec.plans[0], analyser(spec.resoudre(spec.plans[0].source)))
    remplacante = duree_sortie(variante, analyser(spec.resoudre(variante.source)))
    decalage = remplacante - origine

    nouvelle.plans[0] = copy.deepcopy(variante)
    nouvelle.plans[0].transition = "cut"
    if abs(decalage) > 1e-3:
        for ligne in nouvelle.sous_titres.lignes:
            if ligne.debut >= origine - 1e-6:      # tout ce qui suit le hook glisse
                ligne.debut = max(0.0, ligne.debut + decalage)
                ligne.fin = max(ligne.debut + 0.1, ligne.fin + decalage)
    return nouvelle


def cmd_variantes(args: argparse.Namespace) -> int:
    from .render import rendre

    spec = charger(args.montage)
    if not spec.variantes:
        print("Aucune variante dans `variantes:` — rien à faire.")
        return 1

    base = spec.resoudre(args.sortie or spec.projet.sortie)
    racine, extension = os.path.splitext(base)
    codes = 0
    for i, variante in enumerate(spec.variantes):
        etiquette = variante.id or f"v{i + 1}"
        cible = f"{racine}-{etiquette}{extension}"
        print(f"\nVariante « {etiquette} » :")
        try:
            rendu = rendre(_spec_variante(spec, variante), sortie=cible,
                           verbose=args.verbose)
            print(f"✓ {rendu.fichier} — {rendu.duree:.2f}s")
        except (ErreurSpec, ErreurFFmpeg) as exc:
            print(f"✗ {etiquette} : {exc}", file=sys.stderr)
            codes = 1
    return codes


def cmd_demo(args: argparse.Namespace) -> int:
    from .demo import generer
    from .render import rendre

    dossier = Path(args.dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    print(f"Génération des rushes de démonstration dans {dossier}/rushes/ …")
    generer(str(dossier), verbose=args.verbose)

    montage = dossier / "montage.yaml"
    montage.write_text(_modele("demo.yaml"), encoding="utf-8")
    print(f"Fichier de montage : {montage}\n")

    spec = charger(str(montage))
    print("Contrôle :")
    _afficher_controle(spec)
    print(f"\nRendu de « {spec.projet.nom} » :")
    rendu = rendre(spec, verbose=args.verbose)
    taille = os.path.getsize(rendu.fichier) / 1e6
    print(f"\n✓ {rendu.fichier} — {rendu.duree:.2f}s, {taille:.1f} Mo "
          f"(rendu en {rendu.secondes_calcul:.1f}s)")
    return 0


# --------------------------------------------------------------------------- #

def construire_parseur() -> argparse.ArgumentParser:
    parseur = argparse.ArgumentParser(
        prog="ugcut",
        description="Montage de vidéos UGC verticales, piloté par un fichier de montage.",
    )
    parseur.add_argument("--version", action="version", version=f"ugcut {__version__}")
    sous = parseur.add_subparsers(dest="commande", required=True)

    p_init = sous.add_parser("init", help="crée un projet vide (montage.yaml + dossiers)")
    p_init.add_argument("dossier", nargs="?", default=".")
    p_init.add_argument("--forcer", action="store_true", help="écrase un montage.yaml existant")
    p_init.set_defaults(func=cmd_init)

    p_check = sous.add_parser("check", help="contrôle le montage (rythme, hook, sous-titres, CTA)")
    p_check.add_argument("montage")
    p_check.add_argument("--strict", action="store_true", help="code de sortie 1 s'il reste des alertes")
    p_check.set_defaults(func=cmd_check)

    p_render = sous.add_parser("render", help="rend le montage en MP4")
    p_render.add_argument("montage")
    p_render.add_argument("-o", "--sortie", help="remplace projet.sortie")
    p_render.add_argument("--sans-controle", action="store_true")
    p_render.add_argument("--strict", action="store_true", help="refuse de rendre s'il reste des alertes")
    p_render.add_argument("--garder-temp", action="store_true", help="conserve les fichiers intermédiaires")
    p_render.add_argument("-v", "--verbose", action="store_true")
    p_render.set_defaults(func=cmd_render)

    p_var = sous.add_parser("variantes", help="rend une vidéo par variante de hook (test A/B)")
    p_var.add_argument("montage")
    p_var.add_argument("-o", "--sortie")
    p_var.add_argument("-v", "--verbose", action="store_true")
    p_var.set_defaults(func=cmd_variantes)

    p_demo = sous.add_parser("demo", help="génère des rushes de synthèse et rend une démo")
    p_demo.add_argument("--dossier", default="demo")
    p_demo.add_argument("-v", "--verbose", action="store_true")
    p_demo.set_defaults(func=cmd_demo)

    return parseur


def main(argv: list[str] | None = None) -> int:
    args = construire_parseur().parse_args(argv)
    try:
        return args.func(args)
    except (ErreurSpec, ErreurFFmpeg, FileNotFoundError) as exc:
        print(f"\nErreur : {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nInterrompu.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
