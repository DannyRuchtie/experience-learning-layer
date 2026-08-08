.PHONY: install test lint typecheck paper clean

install:
	python3 -m pip install -e ".[dev]"

test:
	python3 -m pytest tests/ -v --tb=short

lint:
	python3 -m ruff check src/ paper tests

typecheck:
	python3 -m mypy src/

paper:
	python3 paper/build_paper.py

clean:
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache \) -prune -exec rm -rf {} +
