PYTHON ?= python3
PYTHONPATH := src

.PHONY: schemas test lint typecheck verify benchmark-development research-status paper-visuals paper

schemas:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m ell.schema_export --output schemas/v0.6

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check src tests

typecheck:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m mypy src

verify: schemas lint typecheck test

benchmark-development:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m ell.benchmark --partition development --sealed-commitment "$(SEALED_COMMITMENT)" --output artifacts/benchmark-development

research-status:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m ell.status

paper-visuals:
	$(PYTHON) script/generate_paper_visuals.py

paper: paper-visuals
	quarto render
