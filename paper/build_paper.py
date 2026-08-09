"""Render the living ELL Markdown manuscript as a polished, reproducible PDF."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
)
from reportlab.platypus.tableofcontents import TableOfContents

from paper.diagrams import DIAGRAMS, pdf_diagram_flowables

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "paper" / "ELL_Paper.md"
DEFAULT_OUTPUT = ROOT / "output" / "pdf" / "Experience-Learning-Layer-Paper-current.pdf"

PAGE_MARKER = re.compile(r"^--- Page \d+ ---$")
PAGE_NUMBER = re.compile(r"^\d+$")
NUMBERED_HEADING = re.compile(r"^(\d+)(?:\.(\d+))?\.?(?:\s+)(.+)$")
HEADER_PREFIX = "EXPERIENCE LEARNING LAYER"
DIAGRAM_MARKER = re.compile(r"^\[\[diagram:([a-z0-9-]+)\]\]$")


def register_fonts() -> tuple[str, str, str]:
    """Use ReportLab's bundled Unicode fonts for portable paper builds."""
    font_dir = Path(__import__("reportlab").__file__).resolve().parent / "fonts"
    pdfmetrics.registerFont(TTFont("ELLBody", font_dir / "Vera.ttf"))
    pdfmetrics.registerFont(TTFont("ELLBold", font_dir / "VeraBd.ttf"))
    pdfmetrics.registerFont(TTFont("ELLItalic", font_dir / "VeraIt.ttf"))
    return "ELLBody", "ELLBold", "ELLItalic"


class LivingPaperTemplate(BaseDocTemplate):
    """A4 template with bookmarks, a generated contents page, and page furniture."""

    def __init__(self, filename: str, *, title: str, author: str) -> None:
        super().__init__(
            filename,
            pagesize=A4,
            invariant=1,
            title=title,
            author=author,
            subject="Experience Learning Layer research and architecture specification",
            leftMargin=24 * mm,
            rightMargin=24 * mm,
            topMargin=22 * mm,
            bottomMargin=20 * mm,
        )
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="body",
        )
        self.addPageTemplates([PageTemplate(id="paper", frames=[frame], onPage=self._draw_page)])

    def _draw_page(self, canvas: object, document: object) -> None:
        page_number = self.page
        if page_number == 1:
            return
        canvas.saveState()  # type: ignore[attr-defined]
        canvas.setStrokeColor(colors.HexColor("#D8DEE8"))  # type: ignore[attr-defined]
        canvas.setLineWidth(0.4)  # type: ignore[attr-defined]
        canvas.line(24 * mm, 14 * mm, A4[0] - 24 * mm, 14 * mm)  # type: ignore[attr-defined]
        canvas.setFont("ELLBody", 7.5)  # type: ignore[attr-defined]
        canvas.setFillColor(colors.HexColor("#536174"))  # type: ignore[attr-defined]
        canvas.drawString(24 * mm, 9.5 * mm, "EXPERIENCE LEARNING LAYER - LIVING PAPER")  # type: ignore[attr-defined]
        canvas.drawRightString(A4[0] - 24 * mm, 9.5 * mm, str(page_number))  # type: ignore[attr-defined]
        canvas.restoreState()  # type: ignore[attr-defined]

    def afterFlowable(self, flowable: object) -> None:  # noqa: N802 - ReportLab hook
        """Register numbered headings with the PDF outline and contents table."""
        if not isinstance(flowable, Paragraph):
            return
        style_name = flowable.style.name
        if style_name not in {"PaperH1", "PaperH2"}:
            return
        level = 0 if style_name == "PaperH1" else 1
        text = flowable.getPlainText()
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
        key = f"heading-{digest}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=False)
        if text != "References":
            self.notify("TOCEntry", (level, text, self.page, key))


def make_styles() -> dict[str, ParagraphStyle]:
    """Create the restrained visual system used by the manuscript."""
    body_font, bold_font, italic_font = register_fonts()
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "PaperTitle",
            parent=base["Title"],
            fontName=bold_font,
            fontSize=25,
            leading=30,
            textColor=colors.HexColor("#142033"),
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "subtitle": ParagraphStyle(
            "PaperSubtitle",
            parent=base["Normal"],
            fontName=body_font,
            fontSize=12,
            leading=17,
            textColor=colors.HexColor("#44536A"),
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "meta": ParagraphStyle(
            "PaperMeta",
            parent=base["Normal"],
            fontName=body_font,
            fontSize=9,
            leading=14,
            textColor=colors.HexColor("#657187"),
            alignment=TA_CENTER,
        ),
        "revision": ParagraphStyle(
            "PaperRevision",
            parent=base["Normal"],
            fontName=italic_font,
            fontSize=9,
            leading=14,
            textColor=colors.HexColor("#334155"),
            borderColor=colors.HexColor("#B9C7DA"),
            borderWidth=0.8,
            borderPadding=10,
            backColor=colors.HexColor("#F4F7FB"),
            spaceBefore=24,
        ),
        "h1": ParagraphStyle(
            "PaperH1",
            parent=base["Heading1"],
            fontName=bold_font,
            fontSize=17,
            leading=21,
            textColor=colors.HexColor("#174A78"),
            spaceBefore=15,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "PaperH2",
            parent=base["Heading2"],
            fontName=bold_font,
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#245C88"),
            spaceBefore=11,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "PaperH3",
            parent=base["Heading3"],
            fontName=bold_font,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334E68"),
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "PaperBody",
            parent=base["BodyText"],
            fontName=body_font,
            fontSize=9,
            leading=13.2,
            textColor=colors.HexColor("#1E293B"),
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            splitLongWords=True,
        ),
        "bullet": ParagraphStyle(
            "PaperBullet",
            parent=base["BodyText"],
            fontName=body_font,
            fontSize=8.8,
            leading=12.8,
            textColor=colors.HexColor("#1E293B"),
            leftIndent=4,
            spaceAfter=2,
        ),
        "small": ParagraphStyle(
            "PaperSmall",
            parent=base["BodyText"],
            fontName=italic_font,
            fontSize=7.8,
            leading=11,
            textColor=colors.HexColor("#556274"),
            spaceAfter=6,
        ),
        "caption": ParagraphStyle(
            "PaperCaption",
            parent=base["BodyText"],
            fontName=body_font,
            fontSize=7.4,
            leading=10.5,
            textColor=colors.HexColor("#556274"),
            spaceAfter=7,
        ),
    }


def clean_lines(source: str) -> list[str]:
    """Remove extraction-only page furniture while retaining manuscript content."""
    result: list[str] = []
    for raw_line in source.splitlines():
        line = raw_line.strip()
        if PAGE_MARKER.fullmatch(line) or PAGE_NUMBER.fullmatch(line):
            continue
        if line.startswith(HEADER_PREFIX) and "WORKING DRAFT" in line:
            continue
        if line.startswith(("https://", "http://")) and result and result[-1]:
            result[-1] = f"{result[-1]} {line}"
            continue
        result.append(line)
    return result


def heading_level(line: str) -> int | None:
    """Recognize manuscript headings without mistaking prose lists for sections."""
    if line in {"Abstract", "Acknowledgements", "References"}:
        return 1
    if line.startswith("Stage ") and len(line) < 90:
        return 3
    match = NUMBERED_HEADING.fullmatch(line)
    if not match or len(line) > 100 or line.endswith((".", ":", ";", "?", "!")):
        return None
    section = int(match.group(1))
    if not 1 <= section <= 15:
        return None
    return 2 if match.group(2) is not None else 1


def join_wrapped_lines(parts: list[str]) -> str:
    """Join extracted manuscript lines without splitting hyphenated words."""
    text = ""
    for part in parts:
        if not text:
            text = part
        elif text.endswith("-"):
            text += part
        else:
            text += f" {part}"
    return text


def manuscript_story(source: str, styles: dict[str, ParagraphStyle]) -> list[object]:
    """Convert the living plain-Markdown manuscript into Platypus flowables."""
    lines = clean_lines(source)
    revision = next((line for line in lines if line.startswith("Revision note.")), "")
    version = next((line for line in lines if line.startswith("Living working draft")), "")
    try:
        abstract_index = lines.index("Abstract")
    except ValueError as exc:
        raise ValueError("manuscript must contain an Abstract heading") from exc

    story: list[object] = [
        Spacer(1, 32 * mm),
        Paragraph("From Episodes to Revisable Concepts", styles["title"]),
        Paragraph(
            "The Experience Learning Layer for Evidence-Grounded Learning in Language Agents",
            styles["subtitle"],
        ),
        Spacer(1, 8 * mm),
        Paragraph("Danny Ruchtie", styles["meta"]),
        Paragraph(escape(version), styles["meta"]),
        Paragraph("OPEN RESEARCH SPECIFICATION / EXPERIMENTAL PROTOCOL", styles["meta"]),
        Paragraph(escape(revision.removeprefix("Revision note. ")), styles["revision"]),
        PageBreak(),
        Paragraph("Contents", styles["h1"]),
    ]
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOC1",
            fontName="ELLBold",
            fontSize=9,
            leading=15,
            leftIndent=0,
            firstLineIndent=0,
            textColor=colors.HexColor("#244A70"),
        ),
        ParagraphStyle(
            "TOC2",
            fontName="ELLBody",
            fontSize=8.3,
            leading=13,
            leftIndent=12,
            firstLineIndent=0,
            textColor=colors.HexColor("#46566C"),
        ),
    ]
    story.extend([toc, PageBreak()])

    paragraph_parts: list[str] = []
    bullets: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_parts:
            text = join_wrapped_lines([part for part in paragraph_parts if part])
            story.append(Paragraph(escape(text), styles["body"]))
            paragraph_parts.clear()

    def flush_bullets() -> None:
        if bullets:
            items = [
                ListItem(Paragraph(escape(item), styles["bullet"]), leftIndent=10)
                for item in bullets
            ]
            story.append(
                ListFlowable(
                    items,
                    bulletType="bullet",
                    bulletFontName="ELLBody",
                    bulletFontSize=6,
                    leftIndent=14,
                    bulletColor=colors.HexColor("#245C88"),
                    spaceAfter=6,
                )
            )
            bullets.clear()

    for line in lines[abstract_index:]:
        marker = DIAGRAM_MARKER.fullmatch(line)
        if marker:
            flush_paragraph()
            flush_bullets()
            key = marker.group(1)
            if key not in DIAGRAMS:
                raise ValueError(f"unknown diagram marker: {key}")
            story.extend(pdf_diagram_flowables(key, styles["caption"]))
            continue
        if not line:
            flush_paragraph()
            flush_bullets()
            continue
        level = heading_level(line)
        if level is not None:
            flush_paragraph()
            flush_bullets()
            story.append(Paragraph(escape(line), styles[f"h{level}"]))
            continue
        if line.startswith("Keywords:"):
            flush_paragraph()
            flush_bullets()
            story.append(Paragraph(escape(line), styles["small"]))
            continue
        if line.startswith("•"):
            flush_paragraph()
            bullets.append(line[1:].strip())
            continue
        if bullets:
            if bullets[-1].endswith((".", "?", "!")) and line[0].isupper():
                flush_bullets()
            else:
                bullets[-1] = join_wrapped_lines([bullets[-1], line])
                continue
        paragraph_parts.append(line)
        if line.endswith((".", "?", "!")):
            flush_paragraph()

    flush_paragraph()
    flush_bullets()
    return story


def build(source_path: Path, output_path: Path) -> None:
    """Build the paper twice so contents and bookmarks receive final page numbers."""
    source = source_path.read_text(encoding="utf-8")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = LivingPaperTemplate(
        str(output_path),
        title="From Episodes to Revisable Concepts",
        author="Danny Ruchtie",
    )
    document.multiBuild(manuscript_story(source, make_styles()))


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.source.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
