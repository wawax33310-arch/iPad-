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
DUR = 13.0

# Le montage est cale sur une grille de tempo : la reveal tombe sur le 24e
# temps, et chaque bloc arrive sur un temps. BPM = 60 / BEAT ~ 134,6.
BEAT = 10.70 / 24.0

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
        "start": 0.06, "stagger": 0.052, "punch": 0.15,
        "out": 2.079, "outdur": 0.15, "whip": (-1.0, -0.12),
    },
    {
        "key": "s2",
        "mode": "slam",
        "color": DIM,
        "lines": [
            [("…MAIS", 0.55), ("PERSONNE", 1.0)],
            [("N’EST", 0.55), ("DISPO.", 1.0)],
        ],
        "start": 2.089, "fall": 0.14,
        "out": 4.308, "outdur": 0.15, "whip": (0.0, -1.0),
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
        "start": 4.458, "stagger": 0.050, "punch": 0.15,
        "out": 6.092, "outdur": 0.15, "whip": (1.0, -0.12),
    },
    {
        "key": "s4",
        "mode": "slam",
        "color": DIM,
        "lines": [
            [("…MAIS ON", 0.5), ("SAIT PAS", 1.0)],
            [("OÙ", 0.5), ("ALLER.", 1.0)],
        ],
        "start": 6.102, "fall": 0.14,
        "out": 8.321, "outdur": 0.15, "whip": (0.0, -1.0),
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
        "start": 8.471, "stagger": 0.040, "punch": 0.13,
        "out": 10.54, "outdur": 0.16, "whip": (0.0, 0.0),  # sortie en zoom
    },
]

# --- reveal de la marque --------------------------------------------------

ZEN_IN = 10.70         # flash + logo, sur le 24e temps
ZEN_SHRINK = 11.59     # le bloc marque recule
ZEN_SHRINK_D = 0.30
FINAL_IN = 12.04       # carton "Lance 20 août à Bordeaux"


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
