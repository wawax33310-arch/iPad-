#!/usr/bin/env python3
"""Table de montage partagee par le rendu image et la synthese audio.

Un seul endroit definit les textes, les tailles relatives et les timings :
la bande son reste donc calee sur l'image, meme apres un reglage.

Chaque segment est un bloc typographique facon kinetic typography : des
lignes empilees serrees, chaque ligne etant etiree sur toute la largeur du
bloc. Le poids d'un mot ne fixe que son contraste DANS sa ligne (0,5 = mot
de liaison discret, 1,0 = mot cle).
"""

FPS = 60
DUR = 15.0

WHITE = "white"
DIM = "dim"
ACCENT = "accent"

# --- blocs de texte -------------------------------------------------------
# mode "punch" : les mots claquent un par un, tres vite
# entry "fly"  : ils arrivent en glissant des cotes, en alternance
# mode "slam"  : le bloc entier tombe et s'ecrase (cassure de rythme)

SEGMENTS = [
    {
        "key": "s1",
        "mode": "punch",
        "entry": "fly",
        "color": WHITE,
        "lines": [
            [("ON A", 0.5), ("TOUS", 1.0)],
            [("CE", 0.5), ("MOMENT", 1.0)],
            [("OÙ ON VEUT", 0.5), ("SORTIR…", 1.0)],
        ],
        "start": 0.15, "stagger": 0.058, "punch": 0.16,
        "out": 2.74, "outdur": 0.16, "whip": (-1.0, -0.12),
    },
    {
        "key": "s2",
        "mode": "slam",
        "color": DIM,
        "lines": [
            [("…MAIS", 0.55), ("PERSONNE", 1.0)],
            [("N’EST", 0.55), ("DISPO.", 1.0)],
        ],
        "start": 2.96, "fall": 0.15,
        "out": 5.12, "outdur": 0.16, "whip": (0.0, -1.0),
    },
    {
        "key": "s3",
        "mode": "punch",
        "entry": "fly",
        "color": WHITE,
        "lines": [
            [("OU ON", 0.5), ("EST", 1.0)],
            [("DISPO…", 1.0)],
        ],
        "start": 5.34, "stagger": 0.054, "punch": 0.16,
        "out": 7.42, "outdur": 0.16, "whip": (1.0, -0.12),
    },
    {
        "key": "s4",
        "mode": "slam",
        "color": DIM,
        "lines": [
            [("…MAIS ON", 0.5), ("SAIT PAS", 1.0)],
            [("OÙ", 0.5), ("ALLER.", 1.0)],
        ],
        "start": 7.64, "fall": 0.15,
        "out": 9.82, "outdur": 0.16, "whip": (0.0, -1.0),
    },
    {
        "key": "s5",
        "mode": "punch",
        "entry": "fly",
        "color": WHITE,
        "accent": {"TOUT DE", "SUITE ?"},
        "lines": [
            [("ET SI ON", 0.45), ("SAVAIT", 1.0)],
            [("TOUT,", 1.0)],
            [("TOUT DE", 0.55), ("SUITE ?", 1.0)],
        ],
        "start": 10.04, "stagger": 0.042, "punch": 0.13,
        "out": 11.94, "outdur": 0.18, "whip": (0.0, 0.0),  # sortie en zoom
    },
]

# --- reveal de la marque --------------------------------------------------

ZEN_IN = 12.25         # flash + logo
ZEN_SHRINK = 13.70     # le bloc marque recule
ZEN_SHRINK_D = 0.35
FINAL_IN = 14.00       # carton "Lance 20 août à Bordeaux"


def segment(key):
    return next(s for s in SEGMENTS if s["key"] == key)


def tokens(seg):
    """Tous les mots d'un segment, dans l'ordre d'apparition."""
    return [tok for line in seg["lines"] for tok in line]


def word_times(seg):
    """Instant d'apparition de chaque mot (vide pour les blocs qui tombent)."""
    if seg["mode"] != "punch":
        return []
    return [seg["start"] + i * seg["stagger"] for i in range(len(tokens(seg)))]


def land_time(seg):
    """Instant d'impact d'un bloc qui tombe."""
    return seg["start"] + seg["fall"]


IMPACTS = [land_time(s) for s in SEGMENTS if s["mode"] == "slam"]
WHIPS = [s["out"] for s in SEGMENTS]
ALL_WORD_TIMES = [(s["key"], t) for s in SEGMENTS for t in word_times(s)]
