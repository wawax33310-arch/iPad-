import unittest

from ugcut.spec import ErreurSpec, depuis_dict


def base(**extra):
    return {"plans": [{"source": "a.mp4", "duree": 2}], **extra}


class TestChargement(unittest.TestCase):
    def test_valeurs_par_defaut(self):
        spec = depuis_dict(base())
        self.assertEqual((spec.projet.largeur, spec.projet.hauteur), (1080, 1920))
        self.assertEqual(spec.projet.fps, 30)
        self.assertEqual(spec.plans[0].transition, "cut")
        self.assertTrue(spec.plans[0].garder_son)

    def test_plan_en_raccourci(self):
        spec = depuis_dict({"plans": ["a.mp4", "b.mp4"]})
        self.assertEqual([p.source for p in spec.plans], ["a.mp4", "b.mp4"])

    def test_alias_anglais(self):
        spec = depuis_dict({
            "project": {"name": "x", "width": 720, "height": 1280},
            "shots": [{"source": "a.mp4", "start": 1, "end": 3, "speed": 1.5}],
            "music": {"file": "m.mp3", "fade_out": 2},
        })
        self.assertEqual(spec.projet.nom, "x")
        self.assertEqual(spec.projet.largeur, 720)
        self.assertEqual((spec.plans[0].debut, spec.plans[0].fin), (1.0, 3.0))
        self.assertEqual(spec.plans[0].vitesse, 1.5)
        self.assertEqual(spec.musique.fondu_sortie, 2.0)

    def test_zoom_raccourci(self):
        spec = depuis_dict(base(plans=[{"source": "a.mp4", "zoom": 1.08}]))
        self.assertEqual((spec.plans[0].zoom_de, spec.plans[0].zoom_vers), (1.0, 1.08))
        self.assertTrue(spec.plans[0].zoom_actif)

    def test_cadrage_nomme(self):
        spec = depuis_dict({"plans": [{"source": "a.mp4", "cadrage": "droite"}]})
        self.assertEqual(spec.plans[0].cadrage, 1.0)

    def test_premiere_transition_forcee_en_coupe(self):
        spec = depuis_dict({"plans": [{"source": "a.mp4", "transition": "fondu"},
                                      {"source": "b.mp4", "transition": "fondu"}]})
        self.assertEqual(spec.plans[0].transition, "cut")
        self.assertEqual(spec.plans[1].transition, "fondu")

    def test_qualite_encodage(self):
        self.assertEqual(depuis_dict(base()).projet.crf, 21)
        self.assertEqual(depuis_dict(base(projet={"crf": 24})).projet.crf, 24)
        self.assertEqual(depuis_dict(base(projet={"qualite": 18})).projet.crf, 18)
        with self.assertRaises(ErreurSpec):
            depuis_dict(base(projet={"crf": 80}))

    def test_musique_en_chaine(self):
        spec = depuis_dict(base(musique="m.mp3"))
        self.assertEqual(spec.musique.fichier, "m.mp3")
        self.assertTrue(spec.musique.ducking)


class TestErreurs(unittest.TestCase):
    def test_sans_plan(self):
        with self.assertRaises(ErreurSpec):
            depuis_dict({"projet": {"nom": "x"}})

    def test_source_manquante(self):
        with self.assertRaises(ErreurSpec):
            depuis_dict({"plans": [{"duree": 2}]})

    def test_transition_inconnue(self):
        with self.assertRaises(ErreurSpec) as ctx:
            depuis_dict({"plans": [{"source": "a.mp4"}, {"source": "b.mp4",
                                                         "transition": "explosion"}]})
        self.assertIn("explosion", str(ctx.exception))

    def test_vitesse_hors_bornes(self):
        with self.assertRaises(ErreurSpec):
            depuis_dict({"plans": [{"source": "a.mp4", "vitesse": 12}]})

    def test_dimensions_impaires(self):
        with self.assertRaises(ErreurSpec):
            depuis_dict(base(projet={"largeur": 1081}))

    def test_sous_titre_a_l_envers(self):
        with self.assertRaises(ErreurSpec):
            depuis_dict(base(sous_titres={"lignes": [{"debut": 3, "fin": 1, "texte": "x"}]}))

    def test_nombre_invalide(self):
        with self.assertRaises(ErreurSpec):
            depuis_dict({"plans": [{"source": "a.mp4", "duree": "deux"}]})


if __name__ == "__main__":
    unittest.main()
