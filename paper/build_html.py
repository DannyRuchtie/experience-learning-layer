"""Build a static, multi-page HTML reading edition of the ELL paper."""

# ruff: noqa: E501 - embedded HTML and CSS retain readable publication lines

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import List, Sequence

from paper.build_paper import DEFAULT_SOURCE, clean_lines, heading_level
from paper.diagrams import DIAGRAMS, write_svg_assets

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs"
DIAGRAM_MARKER = re.compile(r"^\[\[diagram:([a-z0-9-]+)\]\]$")
NUMBERED_ITEM = re.compile(r"^\d+\.\s+(.+)$")


@dataclass(frozen=True)
class Section:
    """One top-level manuscript section and its HTML location."""

    title: str
    slug: str
    lines: Sequence[str]


def slugify(title: str) -> str:
    """Create stable section filenames from manuscript headings."""
    text = re.sub(r"^\d+\.?\s*", "", title).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    prefix = re.match(r"^(\d+)", title)
    return f"{int(prefix.group(1)):02d}-{text}" if prefix else text


def split_sections(source: str) -> tuple[List[str], List[Section]]:
    """Split the manuscript into front matter and top-level sections."""
    lines = clean_lines(source)
    try:
        abstract_index = lines.index("Abstract")
    except ValueError as exc:
        raise ValueError("manuscript must contain an Abstract heading") from exc

    front_matter = lines[:abstract_index]
    sections: List[Section] = []
    title = "Abstract"
    body: List[str] = []
    for line in lines[abstract_index + 1 :]:
        if heading_level(line) == 1:
            sections.append(Section(title=title, slug=slugify(title), lines=tuple(body)))
            title = line
            body = []
        else:
            body.append(line)
    sections.append(Section(title=title, slug=slugify(title), lines=tuple(body)))
    return front_matter, sections


def _flush_paragraph(parts: List[str], output: List[str]) -> None:
    if parts:
        output.append(f"<p>{escape(' '.join(parts))}</p>")
        parts.clear()


def _flush_list(items: List[str], output: List[str], ordered: bool) -> None:
    if items:
        tag = "ol" if ordered else "ul"
        output.append(f"<{tag}>")
        output.extend(f"<li>{escape(item)}</li>" for item in items)
        output.append(f"</{tag}>")
        items.clear()


def render_lines(lines: Sequence[str], *, asset_prefix: str) -> str:
    """Render the manuscript's restrained Markdown subset as semantic HTML."""
    output: List[str] = []
    paragraph: List[str] = []
    items: List[str] = []
    ordered = False

    def flush() -> None:
        _flush_paragraph(paragraph, output)
        _flush_list(items, output, ordered)

    for line in lines:
        marker = DIAGRAM_MARKER.fullmatch(line)
        if marker:
            flush()
            key = marker.group(1)
            diagram = DIAGRAMS[key]
            output.extend(
                [
                    '<figure class="paper-diagram">',
                    f'<img src="{asset_prefix}/diagrams/{key}.svg" alt="{escape(diagram.title)}">',
                    f"<figcaption><strong>{escape(diagram.title)}.</strong> "
                    f"{escape(diagram.caption)}</figcaption>",
                    "</figure>",
                ]
            )
            continue
        if not line:
            flush()
            continue
        level = heading_level(line)
        if level in {2, 3}:
            flush()
            output.append(f"<h{level}>{escape(line)}</h{level}>")
            continue
        if line.startswith("Keywords:"):
            flush()
            output.append(f'<p class="keywords">{escape(line)}</p>')
            continue
        if line.startswith("•"):
            _flush_paragraph(paragraph, output)
            if items and ordered:
                _flush_list(items, output, ordered)
            ordered = False
            items.append(line[1:].strip())
            continue
        numbered = NUMBERED_ITEM.fullmatch(line)
        if numbered and line.endswith((".", ":", ";")):
            _flush_paragraph(paragraph, output)
            if items and not ordered:
                _flush_list(items, output, ordered)
            ordered = True
            items.append(numbered.group(1))
            continue
        if items:
            items[-1] = f"{items[-1]} {line}"
            continue
        paragraph.append(line)
        if line.endswith((".", "?", "!")):
            _flush_paragraph(paragraph, output)

    flush()
    return "\n".join(output)


def navigation(sections: Sequence[Section], current_slug: str = "") -> str:
    """Build the shared paper table of contents."""
    links = []
    for section in sections:
        filename = "index.html" if section.slug == "abstract" else f"paper/{section.slug}.html"
        prefix = "../" if current_slug and current_slug != "abstract" else ""
        active = ' aria-current="page"' if section.slug == current_slug else ""
        links.append(f'<li><a href="{prefix}{filename}"{active}>{escape(section.title)}</a></li>')
    return "\n".join(links)


def page_shell(
    *,
    title: str,
    content: str,
    sections: Sequence[Section],
    current_slug: str,
    previous_link: str = "",
    next_link: str = "",
) -> str:
    """Wrap paper content in the static reading layout."""
    nested = current_slug != "abstract"
    root = "../" if nested else ""
    footer_links = []
    if previous_link:
        footer_links.append(f'<a class="previous" href="{previous_link}">← Previous</a>')
    if next_link:
        footer_links.append(f'<a class="next" href="{next_link}">Next →</a>')
    pager = "".join(footer_links)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="The Experience Learning Layer paper: evidence-grounded learning from episodes to revisable concepts.">
  <title>{escape(title)} · Experience Learning Layer</title>
  <link rel="stylesheet" href="{root}assets/paper.css">
</head>
<body>
  <a class="skip-link" href="#paper">Skip to paper</a>
  <header class="site-header">
    <a class="brand" href="{root}index.html">Experience Learning Layer</a>
    <nav aria-label="Repository links">
      <a href="{root}../README.md">Overview</a>
      <a href="{root}../output/pdf/Experience-Learning-Layer-Paper-current.pdf">PDF</a>
      <a href="{root}../paper/ELL_Paper.md">Source</a>
    </nav>
  </header>
  <div class="reading-layout">
    <aside class="contents" aria-label="Paper contents">
      <p class="eyebrow">Paper contents</p>
      <ol>{navigation(sections, current_slug)}</ol>
    </aside>
    <main id="paper" class="paper">
      {content}
      <nav class="pager" aria-label="Section navigation">{pager}</nav>
    </main>
  </div>
</body>
</html>
"""


def index_content(
    front_matter: Sequence[str], abstract: Section, sections: Sequence[Section]
) -> str:
    """Create the visual landing page and abstract."""
    revision = next((line for line in front_matter if line.startswith("Revision note.")), "")
    cards = []
    for section in sections:
        if section.slug == "abstract":
            continue
        cards.append(
            f'<li><a href="paper/{section.slug}.html"><span>{escape(section.title)}</span>'
            '<span aria-hidden="true">→</span></a></li>'
        )
    abstract_html = render_lines(abstract.lines, asset_prefix="assets")
    return f"""
<section class="hero">
  <p class="eyebrow">Living research paper · open specification</p>
  <h1>From episodes to revisable concepts</h1>
  <p class="lede">A model-independent Experience Learning Layer that turns attributable history into scoped, evidence-backed learning without hiding how a conclusion was formed.</p>
  <div class="actions">
    <a class="button primary" href="paper/01-introduction.html">Read the paper</a>
    <a class="button" href="../output/pdf/Experience-Learning-Layer-Paper-current.pdf">Download PDF</a>
  </div>
</section>
<figure class="paper-diagram hero-diagram">
  <img src="assets/diagrams/ell-overview.svg" alt="Where the Experience Learning Layer sits">
  <figcaption>{escape(DIAGRAMS["ell-overview"].caption)}</figcaption>
</figure>
<section class="abstract">
  <p class="eyebrow">Abstract</p>
  {abstract_html}
</section>
<aside class="revision"><strong>Current revision.</strong> {escape(revision.removeprefix("Revision note. "))}</aside>
<section class="section-index">
  <p class="eyebrow">Table of contents</p>
  <h2>Read the complete paper</h2>
  <ol>{"".join(cards)}</ol>
</section>
"""


def write_site(source_path: Path, output_dir: Path) -> None:
    """Build all HTML pages, CSS, and shared SVG assets."""
    source = source_path.read_text(encoding="utf-8")
    front_matter, sections = split_sections(source)
    output_dir.mkdir(parents=True, exist_ok=True)
    paper_dir = output_dir / "paper"
    assets_dir = output_dir / "assets"
    paper_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    write_svg_assets(assets_dir / "diagrams")
    (assets_dir / "paper.css").write_text(STYLESHEET, encoding="utf-8")
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    abstract = sections[0]
    first_page = f"paper/{sections[1].slug}.html" if len(sections) > 1 else ""
    index = page_shell(
        title="From Episodes to Revisable Concepts",
        content=index_content(front_matter, abstract, sections),
        sections=sections,
        current_slug="abstract",
        next_link=first_page,
    )
    (output_dir / "index.html").write_text(index, encoding="utf-8")

    article_sections = sections[1:]
    for index_value, section in enumerate(article_sections):
        previous = (
            "../index.html"
            if index_value == 0
            else f"{article_sections[index_value - 1].slug}.html"
        )
        next_link = (
            f"{article_sections[index_value + 1].slug}.html"
            if index_value + 1 < len(article_sections)
            else ""
        )
        content = f'<p class="eyebrow">Living paper</p><h1>{escape(section.title)}</h1>'
        content += render_lines(section.lines, asset_prefix="../assets")
        page = page_shell(
            title=section.title,
            content=content,
            sections=sections,
            current_slug=section.slug,
            previous_link=previous,
            next_link=next_link,
        )
        (paper_dir / f"{section.slug}.html").write_text(page, encoding="utf-8")


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    write_site(args.source.resolve(), args.output.resolve())


STYLESHEET = """\
:root {
  color-scheme: light;
  --ink: #162033;
  --muted: #5b6575;
  --line: #d9e0e9;
  --paper: #ffffff;
  --wash: #f4f7fb;
  --blue: #1f5f94;
  --indigo: #5a4aa3;
  font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { margin: 0; color: var(--ink); background: #f8fafc; line-height: 1.65; }
a { color: var(--blue); }
.skip-link { position: absolute; left: -9999px; }
.skip-link:focus { left: 1rem; top: 1rem; z-index: 10; background: white; padding: .7rem 1rem; }
.site-header { position: sticky; top: 0; z-index: 5; display: flex; justify-content: space-between; gap: 1rem; align-items: center; min-height: 64px; padding: 0 4vw; border-bottom: 1px solid var(--line); background: rgba(255,255,255,.94); backdrop-filter: blur(16px); }
.site-header a { text-decoration: none; color: var(--ink); }
.site-header nav { display: flex; gap: 1.2rem; font-size: .92rem; }
.brand { font-weight: 750; letter-spacing: -.02em; }
.reading-layout { display: grid; grid-template-columns: minmax(210px, 290px) minmax(0, 820px); gap: clamp(2rem, 5vw, 5rem); max-width: 1240px; margin: 0 auto; padding: 3.5rem 4vw 7rem; }
.contents { position: sticky; top: 96px; align-self: start; max-height: calc(100vh - 120px); overflow: auto; font-size: .82rem; }
.contents ol { list-style: none; margin: 0; padding: 0; border-left: 1px solid var(--line); }
.contents a { display: block; padding: .34rem 0 .34rem 1rem; color: var(--muted); text-decoration: none; }
.contents a:hover, .contents a[aria-current="page"] { color: var(--blue); border-left: 2px solid var(--blue); margin-left: -1px; }
.paper { min-width: 0; }
.hero { padding: clamp(2rem, 5vw, 5rem) 0 2rem; }
.eyebrow { margin: 0 0 .65rem; color: var(--indigo); font-size: .76rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
h1, h2, h3 { line-height: 1.15; letter-spacing: -.025em; }
h1 { margin: 0 0 1.4rem; font-size: clamp(2.35rem, 6vw, 4.9rem); }
.paper > h1 { font-size: clamp(2.2rem, 5vw, 3.7rem); }
h2 { margin-top: 3.6rem; font-size: clamp(1.6rem, 3vw, 2.1rem); }
h3 { margin-top: 2.5rem; font-size: 1.25rem; }
p, li { font-family: ui-serif, Georgia, Cambria, "Times New Roman", serif; font-size: 1.05rem; }
.lede { max-width: 720px; color: #3d4a5c; font-size: clamp(1.2rem, 2.2vw, 1.48rem); }
.actions { display: flex; flex-wrap: wrap; gap: .8rem; margin-top: 2rem; }
.button { display: inline-flex; padding: .72rem 1rem; border: 1px solid var(--line); border-radius: 9px; background: white; color: var(--ink); text-decoration: none; font-weight: 700; }
.button.primary { color: white; background: var(--blue); border-color: var(--blue); }
.paper-diagram { margin: 2.5rem 0; padding: 1rem; border: 1px solid var(--line); border-radius: 18px; background: var(--paper); box-shadow: 0 18px 45px rgba(35, 54, 83, .07); }
.paper-diagram img { display: block; width: 100%; height: auto; }
figcaption { padding: .8rem .4rem .2rem; color: var(--muted); font-size: .88rem; }
.abstract, .revision, .section-index { margin-top: 4rem; }
.revision { padding: 1.2rem 1.4rem; border-left: 4px solid var(--indigo); background: #f0eefb; border-radius: 0 10px 10px 0; color: #3f4860; }
.section-index ol { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .7rem; padding: 0; list-style: none; }
.section-index a { display: flex; justify-content: space-between; gap: 1rem; height: 100%; padding: 1rem; border: 1px solid var(--line); border-radius: 10px; background: white; color: var(--ink); text-decoration: none; font-weight: 650; }
.paper p { max-width: 72ch; }
.paper li { margin-bottom: .45rem; }
.keywords { color: var(--muted); font-style: italic; }
.pager { display: flex; justify-content: space-between; gap: 1rem; margin-top: 5rem; padding-top: 1.5rem; border-top: 1px solid var(--line); }
.pager a { text-decoration: none; font-weight: 700; }
.next { margin-left: auto; }
@media (max-width: 850px) {
  .reading-layout { display: block; padding-top: 2rem; }
  .contents { position: static; max-height: none; margin-bottom: 3rem; }
  .contents ol { columns: 2; }
  .section-index ol { grid-template-columns: 1fr; }
}
@media (max-width: 560px) {
  .site-header nav a:first-child { display: none; }
  .contents ol { columns: 1; }
  h1 { font-size: 2.5rem; }
}
@media print {
  .site-header, .contents, .pager, .actions { display: none; }
  .reading-layout { display: block; max-width: none; padding: 0; }
  body { background: white; }
}
"""


if __name__ == "__main__":
    main()
