"""Test d'intégration : un vrai rendu, en petit format. Ignoré si ffmpeg manque."""

import os
import tempfile
import unittest

from ugcut.ffmpeg import ErreurFFmpeg, ffmpeg

try:
    from ugcut.ffmpeg import ffmpeg_bin
    ffmpeg_bin()
    FFMPEG = True
except ErreurFFmpeg:
    FFMPEG = False

from ugcut.probe import analyser
from ugcut.render import echapper_filtre, rendre
from ugcut.spec import depuis_dict


def clip(chemin, couleur, duree=1.4, largeur=320, hauteur=568, muet=False):
    entrees = ["-f", "lavfi", "-i",
               f"color=c={couleur}:s={largeur}x{hauteur}:r=30:d={duree}"]
    if not muet:
        entrees += ["-f", "lavfi", "-i", f"sine=frequency=300:duration={duree}"]
    ffmpeg([*entrees, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-t", str(duree), chemin])
    return chemin


@unittest.skipUnless(FFMPEG, "ffmpeg indisponible")
class TestRendu(unittest.TestCase):
    def test_rendu_complet(self):
        with tempfile.TemporaryDirectory() as dossier:
            a = clip(os.path.join(dossier, "a.mp4"), "0x203040")
            b = clip(os.path.join(dossier, "b.mp4"), "0x403020", largeur=568, hauteur=320)
            spec = depuis_dict({
                "projet": {"largeur": 320, "hauteur": 568, "fps": 30,
                           "sortie": "out.mp4"},
                "style": {"taille": 28},
                "plans": [
                    {"source": a, "duree": 1.2, "zoom": 1.06,
                     "textes": [{"contenu": "ACCROCHE", "t": 0, "duree": 1.0}]},
                    {"source": b, "duree": 1.2, "recadrage": "flou",
                     "transition": "fondu", "transition_duree": 0.3},
                ],
                "sous_titres": {"lignes": [{"debut": 0.0, "fin": 2.0,
                                            "texte": "un deux trois quatre"}]},
            }, racine=dossier)
            rendu = rendre(spec, silencieux=True)

            self.assertTrue(os.path.exists(rendu.fichier))
            self.assertAlmostEqual(rendu.duree, 2.1, places=2)   # 1.2 + 1.2 - 0.3
            media = analyser(rendu.fichier)
            self.assertEqual((media.largeur, media.hauteur), (320, 568))
            self.assertTrue(media.a_du_son)
            self.assertAlmostEqual(media.duree, 2.1, delta=0.15)

    def test_rendu_sans_son_ni_musique(self):
        with tempfile.TemporaryDirectory() as dossier:
            a = clip(os.path.join(dossier, "a.mp4"), "0x101010", muet=True)
            spec = depuis_dict({
                "projet": {"largeur": 320, "hauteur": 568, "sortie": "out.mp4"},
                "plans": [{"source": a, "duree": 1.0}],
                "sous_titres": {"actif": False},
            }, racine=dossier)
            rendu = rendre(spec, silencieux=True)
            self.assertTrue(os.path.exists(rendu.fichier))
            self.assertTrue(analyser(rendu.fichier).a_du_son)   # piste silencieuse


class TestEchappement(unittest.TestCase):
    def test_chemin_windows_et_deux_points(self):
        self.assertEqual(echapper_filtre("C:/a b/t.ass"), "C\\:/a b/t.ass")

    def test_virgule_et_crochets(self):
        self.assertEqual(echapper_filtre("/a,b/[x].ass"), "/a\\,b/\\[x\\].ass")


if __name__ == "__main__":
    unittest.main()
