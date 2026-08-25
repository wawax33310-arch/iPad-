import unittest

from ugcut.segments import Segment
from ugcut.spec import depuis_dict
from ugcut.timeline import placer, recouvrement
from ugcut.video import chaine_atempo, chaine_recadrage, chaine_video, chaine_zoom
from ugcut.probe import Media


def segments(spec, durees):
    return [Segment(plan=p, chemin="", duree=d, debut_timeline=0.0, media=None)
            for p, d in zip(spec.plans, durees)]


class TestPlacement(unittest.TestCase):
    def test_coupes_franches(self):
        spec = depuis_dict({"plans": [{"source": "a.mp4"}] * 3})
        segs = segments(spec, [2.0, 3.0, 1.5])
        total = placer(segs)
        self.assertAlmostEqual(total, 6.5)
        self.assertEqual([s.debut_timeline for s in segs], [0.0, 2.0, 5.0])

    def test_le_fondu_raccourcit_la_timeline(self):
        spec = depuis_dict({"plans": [{"source": "a.mp4"},
                                      {"source": "b.mp4", "transition": "fondu",
                                       "transition_duree": 0.5}]})
        segs = segments(spec, [2.0, 2.0])
        self.assertAlmostEqual(placer(segs), 3.5)
        self.assertAlmostEqual(segs[1].debut_timeline, 1.5)

    def test_recouvrement_bride_par_le_plan_le_plus_court(self):
        spec = depuis_dict({"plans": [{"source": "a.mp4"},
                                      {"source": "b.mp4", "transition": "fondu",
                                       "transition_duree": 2.0}]})
        segs = segments(spec, [4.0, 0.6])
        self.assertAlmostEqual(recouvrement(segs[0], segs[1]), 0.3)

    def test_pas_de_recouvrement_sur_une_coupe(self):
        spec = depuis_dict({"plans": [{"source": "a.mp4"}, {"source": "b.mp4"}]})
        segs = segments(spec, [2.0, 2.0])
        self.assertEqual(recouvrement(segs[0], segs[1]), 0.0)


class TestFiltres(unittest.TestCase):
    def test_atempo_reste_dans_les_bornes(self):
        for vitesse in (0.5, 0.8, 1.5, 2.0, 3.0, 4.0, 0.3):
            chaine = chaine_atempo(vitesse)
            facteurs = [float(m.split("=")[1]) for m in chaine.split(",")]
            produit = 1.0
            for f in facteurs:
                self.assertGreaterEqual(f, 0.5)
                self.assertLessEqual(f, 2.0)
                produit *= f
            self.assertAlmostEqual(produit, vitesse, places=4)

    def test_atempo_neutre(self):
        self.assertEqual(chaine_atempo(1.0), "")

    def test_recadrage_remplir(self):
        spec = depuis_dict({"plans": [{"source": "a.mp4", "cadrage": "gauche"}]})
        chaine = chaine_recadrage(None, 1080, 1920, spec.plans[0])
        self.assertIn("force_original_aspect_ratio=increase", chaine)
        self.assertIn("crop=1080:1920:'(iw-ow)*0.0000'", chaine)

    def test_recadrage_flou(self):
        spec = depuis_dict({"plans": [{"source": "a.mp4", "recadrage": "flou"}]})
        chaine = chaine_recadrage(None, 1080, 1920, spec.plans[0])
        self.assertIn("gblur", chaine)
        self.assertIn("overlay", chaine)

    def test_zoom_cale_sur_le_nombre_d_images(self):
        spec = depuis_dict({"plans": [{"source": "a.mp4", "zoom": {"de": 1.0, "vers": 1.1}}]})
        chaine = chaine_zoom(spec.plans[0], spec.projet, 2.0)
        self.assertIn("on/59", chaine)      # 2 s à 30 i/s
        self.assertIn("s=1080x1920", chaine)

    def test_pas_de_zoom_sans_zoom(self):
        spec = depuis_dict({"plans": [{"source": "a.mp4"}]})
        self.assertEqual(chaine_zoom(spec.plans[0], spec.projet, 2.0), "")

    def test_chaine_complete_avec_zoom_passe_par_un_intermediaire(self):
        spec = depuis_dict({"plans": [{"source": "a.mp4", "zoom": 1.08, "vitesse": 2.0}]})
        media = Media("a.mp4", 10.0, 1920, 1080, 30.0, True, False)
        chaine = chaine_video(media, spec.plans[0], spec.projet, 2.0)
        self.assertIn("setpts=PTS/2", chaine)
        self.assertIn("scale=1620:2880", chaine)
        self.assertIn("zoompan", chaine)
        self.assertTrue(chaine.endswith("format=yuv420p"))


if __name__ == "__main__":
    unittest.main()
