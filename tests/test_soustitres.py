import os
import tempfile
import unittest

from ugcut.soustitres import (couleur_ass, construire, decouper, echapper,
                              horodatage, lire_srt, _texte_groupe)
from ugcut.segments import Segment
from ugcut.spec import Ligne, Texte, depuis_dict


class TestFormats(unittest.TestCase):
    def test_couleur_inversee(self):
        self.assertEqual(couleur_ass("#FFE600"), "&H0000E6FF")
        self.assertEqual(couleur_ass("#000000"), "&H00000000")
        self.assertEqual(couleur_ass("#FFF"), "&H00FFFFFF")

    def test_couleur_invalide_retombe_sur_blanc(self):
        self.assertEqual(couleur_ass("bleu"), "&H00FFFFFF")

    def test_horodatage(self):
        self.assertEqual(horodatage(0), "0:00:00.00")
        self.assertEqual(horodatage(75.34), "0:01:15.34")
        self.assertEqual(horodatage(-3), "0:00:00.00")

    def test_echappement(self):
        self.assertEqual(echapper("{\\fs90}texte"), "(fs90)texte")
        self.assertEqual(echapper("deux\nlignes"), "deux\\Nlignes")


class TestDecoupage(unittest.TestCase):
    def test_paquets_de_trois(self):
        groupes = decouper([Ligne(0, 3, "un deux trois quatre cinq")], 3)
        self.assertEqual([g.mots for g in groupes],
                         [["un", "deux", "trois"], ["quatre", "cinq"]])

    def test_les_paquets_couvrent_la_ligne(self):
        groupes = decouper([Ligne(2.0, 6.0, "a bb ccc dddd eeeee ffffff")], 2)
        self.assertAlmostEqual(groupes[0].debut, 2.0)
        self.assertAlmostEqual(groupes[-1].fin, 6.0, places=5)
        for precedent, suivant in zip(groupes, groupes[1:]):
            self.assertAlmostEqual(precedent.fin, suivant.debut, places=5)

    def test_ligne_vide_ignoree(self):
        self.assertEqual(decouper([Ligne(0, 1, "   ")], 3), [])


class TestEvenements(unittest.TestCase):
    def setUp(self):
        self.spec = depuis_dict({"plans": [{"source": "a.mp4"}]})

    def test_un_evenement_par_mot(self):
        groupe = decouper([Ligne(0, 3, "un deux trois")], 3)[0]
        evenements = _texte_groupe(groupe, self.spec.style)
        self.assertEqual(len(evenements), 3)
        self.assertAlmostEqual(evenements[-1][1], 3.0, places=5)
        # chaque événement affiche les trois mots, un seul est mis en avant
        for _, _, texte in evenements:
            self.assertEqual(texte.count("\\c&H"), 1)
            for mot in ("UN", "DEUX", "TROIS"):
                self.assertIn(mot, texte)

    def test_mode_ligne(self):
        self.spec.style.mode = "ligne"
        groupe = decouper([Ligne(0, 3, "un deux trois")], 3)[0]
        self.assertEqual(len(_texte_groupe(groupe, self.spec.style)), 1)

    def test_sans_majuscules(self):
        self.spec.style.majuscules = False
        groupe = decouper([Ligne(0, 1, "Bonjour")], 3)[0]
        self.assertIn("Bonjour", _texte_groupe(groupe, self.spec.style)[0][2])


class TestSrt(unittest.TestCase):
    def test_lecture(self):
        contenu = (
            "1\n00:00:01,000 --> 00:00:03,500\nPremière ligne\n\n"
            "2\n00:00:04,000 --> 00:00:06,000\nDeuxième\nsur deux lignes\n"
        )
        with tempfile.TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "v.srt")
            with open(chemin, "w", encoding="utf-8") as fh:
                fh.write(contenu)
            lignes = lire_srt(chemin)
        self.assertEqual(len(lignes), 2)
        self.assertAlmostEqual(lignes[0].debut, 1.0)
        self.assertAlmostEqual(lignes[0].fin, 3.5)
        self.assertEqual(lignes[1].texte, "Deuxième sur deux lignes")


class TestFichierAss(unittest.TestCase):
    def _segment(self, textes, debut, duree):
        spec = depuis_dict({"plans": [{"source": "a.mp4"}]})
        plan = spec.plans[0]
        plan.textes = textes
        return Segment(plan=plan, chemin="", duree=duree, debut_timeline=debut, media=None)

    def test_construction_complete(self):
        spec = depuis_dict({
            "plans": [{"source": "a.mp4"}],
            "sous_titres": {"lignes": [{"debut": 0, "fin": 2, "texte": "salut le monde"}]},
        })
        segment = self._segment([Texte(contenu="ACCROCHE", t=0.2, duree=1.0)], 0.0, 2.0)
        with tempfile.TemporaryDirectory() as dossier:
            cible = os.path.join(dossier, "t.ass")
            self.assertEqual(construire(spec, [segment], cible), cible)
            with open(cible, encoding="utf-8") as fh:
                contenu = fh.read()
        self.assertIn("[V4+ Styles]", contenu)
        self.assertIn("Style: Sub,", contenu)
        self.assertIn("ACCROCHE", contenu)
        self.assertIn("PlayResY: 1920", contenu)

    def test_sticker_cale_sur_la_timeline(self):
        spec = depuis_dict({"plans": [{"source": "a.mp4"}], "sous_titres": {"actif": False}})
        segment = self._segment([Texte(contenu="X", t=0.5, duree=1.0)], 10.0, 3.0)
        with tempfile.TemporaryDirectory() as dossier:
            cible = os.path.join(dossier, "t.ass")
            construire(spec, [segment], cible)
            with open(cible, encoding="utf-8") as fh:
                contenu = fh.read()
        self.assertIn("0:00:10.50", contenu)

    def test_styles_de_texte(self):
        spec = depuis_dict({"plans": [{"source": "a.mp4"}], "sous_titres": {"actif": False}})
        segment = self._segment([
            Texte(contenu="haut", t=0.0, duree=1.0, style="sticker"),
            Texte(contenu="titre", t=0.0, duree=1.0, style="titre"),
            Texte(contenu="offert", t=0.0, duree=1.0, style="impact"),
        ], 0.0, 2.0)
        with tempfile.TemporaryDirectory() as dossier:
            cible = os.path.join(dossier, "t.ass")
            construire(spec, [segment], cible)
            with open(cible, encoding="utf-8") as fh:
                contenu = fh.read()
        self.assertIn("Style: Impact,", contenu)
        self.assertIn(",Sticker,", contenu)
        self.assertIn(",Titre,", contenu)
        self.assertIn(",Impact,", contenu)
        self.assertIn("\\fscx140", contenu)          # le mot-clé entre en grand
        self.assertIn("haut", contenu)                 # étiquette : casse d'origine
        self.assertIn("TITRE", contenu)                # titre et impact : majuscules
        self.assertIn("OFFERT", contenu)

    def test_sans_texte_aucun_fichier(self):
        spec = depuis_dict({"plans": [{"source": "a.mp4"}]})
        segment = self._segment([], 0.0, 2.0)
        with tempfile.TemporaryDirectory() as dossier:
            self.assertIsNone(construire(spec, [segment], os.path.join(dossier, "t.ass")))


if __name__ == "__main__":
    unittest.main()
