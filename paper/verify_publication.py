"""Verify the generated paper website and shared visual assets."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
from typing import List, Tuple
from urllib.parse import unquote, urlparse

from paper.build_html import DEFAULT_OUTPUT, DEFAULT_SOURCE, split_sections
from paper.diagrams import DIAGRAMS

ROOT = Path(__file__).resolve().parents[1]


class PublicationParser(HTMLParser):
    """Collect local links, images, and structural landmarks."""

    def __init__(self) -> None:
        super().__init__()
        self.references: List[Tuple[str, str]] = []
        self.main_count = 0
        self.title_count = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "main":
            self.main_count += 1
        elif tag == "title":
            self.title_count += 1
        elif tag == "a" and attributes.get("href"):
            self.references.append(("href", attributes["href"] or ""))
        elif tag == "img" and attributes.get("src"):
            if not attributes.get("alt"):
                raise ValueError("every publication image requires alt text")
            self.references.append(("src", attributes["src"] or ""))


def _local_target(page: Path, reference: str) -> Path | None:
    parsed = urlparse(reference)
    if parsed.scheme or parsed.netloc or reference.startswith("#"):
        return None
    return (page.parent / unquote(parsed.path)).resolve()


def verify(source_path: Path = DEFAULT_SOURCE, output_dir: Path = DEFAULT_OUTPUT) -> None:
    """Fail loudly when the static publication is incomplete or internally broken."""
    source = source_path.read_text(encoding="utf-8")
    _, sections = split_sections(source)
    expected_pages = {output_dir / "index.html"}
    expected_pages.update(
        output_dir / "paper" / f"{section.slug}.html"
        for section in sections
        if section.slug != "abstract"
    )
    missing_pages = sorted(path for path in expected_pages if not path.is_file())
    if missing_pages:
        raise FileNotFoundError(f"missing generated HTML pages: {missing_pages}")

    expected_diagrams = {output_dir / "assets" / "diagrams" / f"{key}.svg" for key in DIAGRAMS}
    missing_diagrams = sorted(path for path in expected_diagrams if not path.is_file())
    if missing_diagrams:
        raise FileNotFoundError(f"missing generated diagrams: {missing_diagrams}")

    allowed_roots = (ROOT.resolve(), output_dir.resolve())
    broken: List[Tuple[Path, str]] = []
    for page in sorted(expected_pages):
        parser = PublicationParser()
        parser.feed(page.read_text(encoding="utf-8"))
        if parser.main_count != 1 or parser.title_count != 1:
            raise ValueError(f"{page} must contain exactly one title and one main landmark")
        for _, reference in parser.references:
            target = _local_target(page, reference)
            if target is None:
                continue
            within_repository = any(
                target == root or root in target.parents for root in allowed_roots
            )
            if not within_repository or not target.exists():
                broken.append((page, reference))
    if broken:
        raise FileNotFoundError(f"broken local publication references: {broken}")

    forbidden = ("ELLChat", "SwiftUI", "Codex CLI", "macOS preview")
    found = [term for term in forbidden if term.lower() in source.lower()]
    if found:
        raise ValueError(f"retired app terminology remains in manuscript: {found}")


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    verify(args.source.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
