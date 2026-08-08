.PHONY: install test lint typecheck paper clean app-build app-test

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

app-build:
	DEVELOPER_DIR=/Applications/Xcode-beta.app/Contents/Developer CLANG_MODULE_CACHE_PATH=/private/tmp/ell-chat-clang-module-cache SWIFTPM_MODULECACHE_OVERRIDE=/private/tmp/ell-chat-swiftpm-module-cache xcrun swift build --disable-sandbox --product ELLChat

app-test:
	DEVELOPER_DIR=/Applications/Xcode-beta.app/Contents/Developer CLANG_MODULE_CACHE_PATH=/private/tmp/ell-chat-clang-module-cache SWIFTPM_MODULECACHE_OVERRIDE=/private/tmp/ell-chat-swiftpm-module-cache xcrun swift test --disable-sandbox

clean:
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache \) -prune -exec rm -rf {} +
