from pathlib import Path

from paper.build_html import split_sections, write_site
from paper.diagrams import DIAGRAMS, diagram_svg
from paper.verify_publication import verify


def test_html_publication_contains_every_paper_section(tmp_path: Path) -> None:
    source_path = Path("paper/ELL_Paper.md").resolve()
    output_dir = tmp_path / "docs"

    write_site(source_path, output_dir)
    verify(source_path, output_dir)

    _, sections = split_sections(source_path.read_text(encoding="utf-8"))
    generated_pages = {path.name for path in (output_dir / "paper").glob("*.html")}
    expected_pages = {f"{section.slug}.html" for section in sections if section.slug != "abstract"}
    assert generated_pages == expected_pages


def test_shared_diagrams_are_accessible_standalone_svg() -> None:
    for diagram in DIAGRAMS.values():
        svg = diagram_svg(diagram)
        assert svg.startswith("<svg")
        assert f'<title id="title">{diagram.title}</title>' in svg
        assert '<desc id="desc">' in svg
        assert 'marker-end="url(#arrow)"' in svg
