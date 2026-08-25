import unittest

from ugcut.probe import Media
from ugcut.segments import DUREE_IMAGE_DEFAUT, bornes, duree_sortie
from ugcut.spec import ErreurSpec, depuis_dict

VIDEO = Media("a.mp4", duree=12.0, largeur=1080, hauteur=1920, fps=30.0,
              a_du_son=True, est_image=False)
IMAGE = Media("a.png", duree=0.0, largeur=1200, hauteur=1500, fps=25.0,
              a_du_son=False, est_image=True)


def plan(**kwargs):
    return depuis_dict({"plans": [{"source": "a.mp4", **kwargs}]}).plans[0]


class TestBornes(unittest.TestCase):
    def test_duree_explicite(self):
        self.assertEqual(bornes(plan(debut=2, duree=3), VIDEO), (2.0, 3.0))

    def test_point_de_sortie(self):
        self.assertEqual(bornes(plan(debut=2, fin=5), VIDEO), (2.0, 3.0))

    def test_duree_prime_sur_fin(self):
        self.assertEqual(bornes(plan(debut=1, duree=2, fin=9), VIDEO), (1.0, 2.0))

    def test_sans_borne_on_prend_tout_le_rush(self):
        _, longueur = bornes(plan(debut=1), VIDEO)
        self.assertAlmostEqual(longueur, 12.0 - 1.0 - 0.04)

    def test_bride_a_la_fin_du_rush(self):
        _, longueur = bornes(plan(debut=10, duree=8), VIDEO)
        self.assertAlmostEqual(longueur, 2.0)

    def test_debut_au_dela_du_rush(self):
        with self.assertRaises(ErreurSpec):
            bornes(plan(debut=20), VIDEO)

    def test_plan_vide(self):
        with self.assertRaises(ErreurSpec):
            bornes(plan(debut=5, fin=5.01), VIDEO)

    def test_fin_avant_debut(self):
        with self.assertRaises(ErreurSpec):
            bornes(plan(debut=5, fin=3), VIDEO)

    def test_image_sans_duree(self):
        self.assertEqual(bornes(plan(), IMAGE), (0.0, DUREE_IMAGE_DEFAUT))

    def test_image_avec_duree(self):
        self.assertEqual(bornes(plan(duree=4), IMAGE), (0.0, 4.0))


class TestDureeSortie(unittest.TestCase):
    def test_la_vitesse_raccourcit(self):
        self.assertAlmostEqual(duree_sortie(plan(debut=0, duree=4, vitesse=2.0), VIDEO), 2.0)

    def test_ralenti(self):
        self.assertAlmostEqual(duree_sortie(plan(debut=0, duree=2, vitesse=0.5), VIDEO), 4.0)

    def test_image_accelerec(self):
        self.assertAlmostEqual(duree_sortie(plan(duree=3), IMAGE), 3.0)


if __name__ == "__main__":
    unittest.main()
