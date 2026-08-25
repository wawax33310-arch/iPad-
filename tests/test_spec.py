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

    def test_zoom_auto_alterne(self):
        spec = depuis_dict({"plans": [{"source": "a.mp4", "zoom": "auto"},
                                      {"source": "b.mp4", "zoom": "auto"},
                                      {"source": "c.mp4", "zoom": "auto"}]})
        sens = [(p.zoom_de, p.zoom_vers) for p in spec.plans]
        self.assertEqual(sens[0], (1.0, 1.08))
        self.assertEqual(sens[1], (1.08, 1.0))     # sens inverse du précédent
        self.assertEqual(sens[2], (1.0, 1.08))
        self.assertTrue(all(p.zoom_actif for p in spec.plans))

    def test_zoom_explicite_ignore_l_alternance(self):
        spec = depuis_dict({"plans": [{"source": "a.mp4", "zoom": "auto"},
                                      {"source": "b.mp4", "zoom": {"de": 1.2, "vers": 1.0}}]})
        self.assertEqual((spec.plans[1].zoom_de, spec.plans[1].zoom_vers), (1.2, 1.0))

    def test_zoom_invalide(self):
        with self.assertRaises(ErreurSpec):
            depuis_dict({"plans": [{"source": "a.mp4", "zoom": "beaucoup"}]})

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


class TestTempo(unittest.TestCase):
    def test_temps_en_secondes(self):
        spec = depuis_dict({"tempo": {"bpm": 120},
                            "plans": [{"source": "a.mp4", "temps": 2}]})
        self.assertEqual(spec.tempo.temps, 0.5)
        self.assertEqual(spec.tempo.mesure, 2.0)
        self.assertAlmostEqual(spec.plans[0].duree, 1.0)

    def test_la_vitesse_ne_decale_pas_la_grille(self):
        """`temps` est une durée à l'écran : la source doit être plus longue."""
        spec = depuis_dict({"tempo": 120,
                            "plans": [{"source": "a.mp4", "temps": 2, "vitesse": 1.5}]})
        plan = spec.plans[0]
        self.assertAlmostEqual(plan.duree, 1.5)              # lu dans le rush
        self.assertAlmostEqual(plan.duree / plan.vitesse, 1.0)   # à l'écran

    def test_le_fondu_est_compense(self):
        """Un fondu avance le plan : on le rallonge d'autant."""
        spec = depuis_dict({"tempo": 120, "plans": [
            {"source": "a.mp4", "temps": 2},
            {"source": "b.mp4", "temps": 4, "transition": "flash",
             "transition_duree": 0.2}]})
        self.assertAlmostEqual(spec.plans[1].duree, 2.2)

    def test_duree_explicite_intacte(self):
        spec = depuis_dict({"tempo": 120,
                            "plans": [{"source": "a.mp4", "duree": 1.37}]})
        self.assertAlmostEqual(spec.plans[0].duree, 1.37)

    def test_temps_sans_tempo(self):
        with self.assertRaises(ErreurSpec):
            depuis_dict({"plans": [{"source": "a.mp4", "temps": 2}]})

    def test_bpm_aberrant(self):
        with self.assertRaises(ErreurSpec):
            depuis_dict({"tempo": {"bpm": 900}, "plans": [{"source": "a.mp4"}]})


class TestSonEtStyles(unittest.TestCase):
    def test_son_sur_un_plan(self):
        spec = depuis_dict(base(plans=[{"source": "a.mp4", "son": "whoosh",
                                        "son_gain_db": -3}]))
        self.assertEqual(spec.plans[0].son, "whoosh")
        self.assertEqual(spec.plans[0].son_gain_db, -3.0)

    def test_son_inconnu(self):
        with self.assertRaises(ErreurSpec):
            depuis_dict(base(plans=[{"source": "a.mp4", "son": "explosion"}]))

    def test_effets_sonores(self):
        spec = depuis_dict(base(effets_sonores=[{"t": 2.0, "son": "riser", "duree": 1.5},
                                                {"t": 0.5, "son": "impact"}]))
        self.assertEqual([e.t for e in spec.effets_sonores], [0.5, 2.0])   # triés
        self.assertEqual(spec.effets_sonores[1].duree, 1.5)

    def test_effet_avec_fichier_maison(self):
        spec = depuis_dict(base(effets_sonores=[{"t": 1.0, "fichier": "sons/whip.wav"}]))
        self.assertEqual(spec.effets_sonores[0].fichier, "sons/whip.wav")

    def test_effet_son_inconnu(self):
        with self.assertRaises(ErreurSpec):
            depuis_dict(base(effets_sonores=[{"t": 1.0, "son": "boum"}]))

    def test_style_de_texte_invalide(self):
        with self.assertRaises(ErreurSpec):
            depuis_dict(base(plans=[{"source": "a.mp4",
                                     "textes": [{"contenu": "x", "style": "neon"}]}]))


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
