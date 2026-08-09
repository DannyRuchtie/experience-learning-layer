.PHONY: install lint paper pdf html verify-publication check clean

install:
	python3 -m pip install -e ".[dev]"

lint:
	python3 -m ruff check --no-cache paper

paper: pdf html

pdf:
	python3 -m paper.build_paper

html:
	python3 -m paper.build_html

verify-publication:
	python3 -m paper.verify_publication

check: lint paper verify-publication

clean:
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache \) -prune -exec rm -rf {} +
