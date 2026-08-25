PYTHON ?= python3

.PHONY: test demo check clean install

install:            ## installe la commande `ugcut`
	$(PYTHON) -m pip install -e .

test:               ## suite de tests (le rendu réel est ignoré sans ffmpeg)
	$(PYTHON) -m unittest discover -s tests -t . -v

demo:               ## génère des rushes de synthèse et rend une démo complète
	$(PYTHON) -m ugcut demo --dossier demo

check:              ## contrôle le montage de démo (lance `make demo` d'abord)
	$(PYTHON) -m ugcut check demo/montage.yaml

clean:
	rm -rf demo/ .pytest_cache **/__pycache__ ugcut/__pycache__ tests/__pycache__
