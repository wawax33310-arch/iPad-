import unittest
from unittest import mock

from ugcut.lint import ALERTE, CONSEIL, analyser_montage, resume
from ugcut.spec import depuis_dict


def codes(constats, niveau=None):
    return {c.code for c in constats if niveau is None or c.niveau == niveau}


def montage(plans, durees, **extra):
    spec = depuis_dict({"plans": plans, **extra})
    with mock.patch("ugcut.lint._durees", return_value=(durees, [])), \
         mock.patch("ugcut.lint.analyser") as faux:
        faux.return_value = mock.Mock(a_du_son=True)
        with mock.patch("os.path.exists", return_value=True):
            return analyser_montage(spec)


BON = {
    "plans": [
        {"source": "h.mp4", "role": "hook", "duree": 2.0,
         "textes": [{"contenu": "ACCROCHE", "t": 0.0, "duree": 1.8}]},
        {"source": "p.mp4", "duree": 3.0},
        {"source": "s.mp4", "duree": 3.0},
        {"source": "c.mp4", "role": "cta", "duree": 2.0},
    ],
    "durees": [2.0, 3.0, 3.0, 2.0],
    "sous_titres": {"lignes": [{"debut": 0.0, "fin": 9.5, "texte": "une phrase"}]},
    "musique": {"fichier": "m.mp3", "gain_db": -20},
}


class TestMontageSain(unittest.TestCase):
    def test_aucune_alerte(self):
        constats = montage(BON["plans"], BON["durees"],
                           sous_titres=BON["sous_titres"], musique=BON["musique"])
        self.assertEqual(codes(constats, ALERTE), set())
        self.assertEqual(resume(constats)[0], 0)


class TestRegles(unittest.TestCase):
    def test_hook_trop_long(self):
        plans = [dict(BON["plans"][0], duree=5.0)] + BON["plans"][1:]
        constats = montage(plans, [5.0, 3.0, 3.0, 2.0],
                           sous_titres=BON["sous_titres"], musique=BON["musique"])
        self.assertIn("hook", codes(constats, ALERTE))

    def test_hook_sans_texte(self):
        plans = [{"source": "h.mp4", "role": "hook", "duree": 2.0}] + BON["plans"][1:]
        constats = montage(plans, BON["durees"],
                           sous_titres={"lignes": [{"debut": 2.0, "fin": 9.0, "texte": "x"}]},
                           musique=BON["musique"])
        self.assertIn("hook_texte", codes(constats, ALERTE))

    def test_sans_sous_titres(self):
        constats = montage(BON["plans"], BON["durees"], musique=BON["musique"])
        self.assertIn("sous_titres", codes(constats, ALERTE))

    def test_couverture_insuffisante(self):
        constats = montage(
            BON["plans"], BON["durees"], musique=BON["musique"],
            sous_titres={"lignes": [{"debut": 0.0, "fin": 2.0, "texte": "trop court"}]})
        self.assertIn("sous_titres", codes(constats, ALERTE))

    def test_sous_titre_apres_la_fin(self):
        constats = montage(
            BON["plans"], BON["durees"], musique=BON["musique"],
            sous_titres={"lignes": [{"debut": 0.0, "fin": 30.0, "texte": "déborde"}]})
        self.assertIn("sous_titres_hors_champ", codes(constats, ALERTE))

    def test_sans_cta(self):
        plans = BON["plans"][:3] + [{"source": "c.mp4", "duree": 2.0}]
        constats = montage(plans, BON["durees"],
                           sous_titres={"lignes": [{"debut": 0.0, "fin": 4.0, "texte": "x"}]},
                           musique=BON["musique"])
        self.assertIn("cta", codes(constats, ALERTE))

    def test_trop_long(self):
        plans = BON["plans"] + [{"source": "x.mp4", "duree": 60.0}]
        constats = montage(plans, BON["durees"] + [60.0],
                           sous_titres={"lignes": [{"debut": 0, "fin": 65, "texte": "x"}]},
                           musique=BON["musique"])
        self.assertIn("duree", codes(constats, ALERTE))

    def test_plan_statique_trop_long(self):
        plans = [BON["plans"][0], {"source": "p.mp4", "duree": 8.0}] + BON["plans"][2:]
        constats = montage(plans, [2.0, 8.0, 3.0, 2.0],
                           sous_titres={"lignes": [{"debut": 0, "fin": 14, "texte": "x"}]},
                           musique=BON["musique"])
        self.assertIn("plan_statique", codes(constats, CONSEIL))

    def test_zone_sure_des_sous_titres(self):
        constats = montage(BON["plans"], BON["durees"], musique=BON["musique"],
                           sous_titres=BON["sous_titres"], style={"position": 0.95})
        self.assertIn("zone_sure", codes(constats, CONSEIL))

    def test_musique_trop_forte(self):
        constats = montage(BON["plans"], BON["durees"], sous_titres=BON["sous_titres"],
                           musique={"fichier": "m.mp3", "gain_db": -2})
        self.assertIn("musique_gain", codes(constats, CONSEIL))

    def test_ducking_desactive(self):
        constats = montage(BON["plans"], BON["durees"], sous_titres=BON["sous_titres"],
                           musique={"fichier": "m.mp3", "gain_db": -20, "ducking": False})
        self.assertIn("ducking", codes(constats, CONSEIL))

    def test_format_non_natif(self):
        constats = montage(BON["plans"], BON["durees"], sous_titres=BON["sous_titres"],
                           musique=BON["musique"], projet={"largeur": 1920, "hauteur": 1080})
        self.assertIn("format", codes(constats, CONSEIL))

    def test_vitesse_excessive(self):
        plans = [dict(BON["plans"][0], vitesse=2.0)] + BON["plans"][1:]
        constats = montage(plans, BON["durees"], sous_titres=BON["sous_titres"],
                           musique=BON["musique"])
        self.assertIn("vitesse", codes(constats, CONSEIL))


class TestSoundDesign(unittest.TestCase):
    """Rushes coupés et pas de musique : le montage est muet — sauf sound design."""

    MUETS = [dict(p, garder_son=False) for p in BON["plans"]]

    def test_muet_sans_rien(self):
        constats = montage(self.MUETS, BON["durees"], sous_titres=BON["sous_titres"])
        self.assertIn("audio", codes(constats, ALERTE))

    def test_sound_design_seul_est_un_conseil(self):
        plans = [dict(self.MUETS[0], son="impact")] + self.MUETS[1:]
        constats = montage(plans, BON["durees"], sous_titres=BON["sous_titres"])
        self.assertNotIn("audio", codes(constats, ALERTE))
        self.assertIn("audio", codes(constats, CONSEIL))

    def test_effets_sonores_globaux_comptent_aussi(self):
        constats = montage(self.MUETS, BON["durees"], sous_titres=BON["sous_titres"],
                           effets_sonores=[{"t": 1.0, "son": "whoosh"}])
        self.assertIn("audio", codes(constats, CONSEIL))


class TestResilience(unittest.TestCase):
    def test_rush_absent_ne_plante_pas(self):
        spec = depuis_dict({"plans": [{"source": "introuvable.mp4"}]})
        constats = analyser_montage(spec)
        self.assertIn("source", codes(constats, ALERTE))


if __name__ == "__main__":
    unittest.main()
