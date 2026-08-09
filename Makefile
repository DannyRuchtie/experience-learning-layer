.PHONY: install test lint typecheck paper pdf html verify-publication check clean

install:
	python3 -m pip install -e ".[dev]"

test:
	python3 -m pytest tests/ -v --tb=short

lint:
	python3 -m ruff check src/ paper tests

typecheck:
	python3 -m mypy src/

paper: pdf html

pdf:
	python3 -m paper.build_paper

html:
	python3 -m paper.build_html

verify-publication:
	python3 -m paper.verify_publication

check: lint typecheck test paper verify-publication

clean:
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache \) -prune -exec rm -rf {} +
