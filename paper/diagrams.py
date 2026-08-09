"""Shared diagram definitions for the README, HTML edition, and PDF paper."""

# ruff: noqa: E501 - SVG fragments are clearer as complete elements

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Dict, Iterable, Tuple

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer


@dataclass(frozen=True)
class Node:
    """A labelled box in an architecture diagram."""

    identifier: str
    lines: Tuple[str, ...]
    x: float
    y: float
    width: float
    height: float
    fill: str


@dataclass(frozen=True)
class Edge:
    """A directed relationship between two nodes."""

    source: str
    target: str
    label: str = ""
    dashed: bool = False


@dataclass(frozen=True)
class Diagram:
    """A reusable diagram and its paper caption."""

    key: str
    title: str
    caption: str
    width: float
    height: float
    nodes: Tuple[Node, ...]
    edges: Tuple[Edge, ...]


INK = "#162033"
MUTED = "#5B6575"
LINE = "#8A98AA"
BLUE = "#E8F2FF"
INDIGO = "#EEEAFE"
AMBER = "#FFF4D8"
GREEN = "#E6F6EE"
ROSE = "#FDECEF"
SLATE = "#EEF2F6"


DIAGRAMS: Dict[str, Diagram] = {
    "ell-overview": Diagram(
        key="ell-overview",
        title="Where the Experience Learning Layer sits",
        caption=(
            "ELL turns consented experience into evidence-backed, revisable concepts, then "
            "uses observed outcomes to improve or challenge them."
        ),
        width=960,
        height=330,
        nodes=(
            Node(
                "sources",
                ("Consented experience", "events, episodes, outcomes"),
                30,
                105,
                190,
                110,
                SLATE,
            ),
            Node(
                "experience",
                ("Experience layer", "normalize, preserve, associate"),
                270,
                105,
                190,
                110,
                BLUE,
            ),
            Node(
                "learning",
                ("Learning layer", "reflect, consolidate, revise"),
                510,
                105,
                190,
                110,
                INDIGO,
            ),
            Node("use", ("Application", "scoped context and decisions"), 750, 105, 180, 110, GREEN),
        ),
        edges=(
            Edge("sources", "experience", "provenance"),
            Edge("experience", "learning", "evidence"),
            Edge("learning", "use", "concepts"),
            Edge("use", "experience", "outcomes", dashed=True),
        ),
    ),
    "learning-lifecycle": Diagram(
        key="learning-lifecycle",
        title="From one episode to a revisable concept",
        caption=(
            "Interpretation remains provisional until evidence, scope, policy, and "
            "counterevidence support promotion into a versioned concept."
        ),
        width=1080,
        height=420,
        nodes=(
            Node("episode", ("Episode", "what happened"), 25, 80, 145, 90, SLATE),
            Node("reflection", ("Reflection", "provisional meaning"), 205, 80, 155, 90, BLUE),
            Node("candidate", ("Candidate", "typed hypothesis"), 395, 80, 155, 90, AMBER),
            Node("concept", ("Versioned concept", "scope + evidence"), 585, 80, 170, 90, INDIGO),
            Node("application", ("Application", "used in context"), 790, 80, 135, 90, GREEN),
            Node("outcome", ("Outcome", "did it help?"), 960, 80, 100, 90, GREEN),
            Node("counter", ("Counterevidence", "correction or change"), 400, 270, 180, 90, ROSE),
            Node("revision", ("New version", "narrow, contest, retire"), 650, 270, 180, 90, INDIGO),
        ),
        edges=(
            Edge("episode", "reflection"),
            Edge("reflection", "candidate"),
            Edge("candidate", "concept", "validate"),
            Edge("concept", "application"),
            Edge("application", "outcome"),
            Edge("outcome", "revision", "feedback", dashed=True),
            Edge("counter", "revision"),
            Edge("revision", "concept", "supersedes", dashed=True),
        ),
    ),
    "governed-commit": Diagram(
        key="governed-commit",
        title="Models interpret; deterministic code governs",
        caption=(
            "Generated interpretations enter quarantine. Schema validation and deterministic "
            "policy decide whether they are rejected, reviewed, or committed."
        ),
        width=980,
        height=390,
        nodes=(
            Node(
                "evidence", ("Exact evidence", "source spans + provenance"), 20, 65, 180, 95, SLATE
            ),
            Node("model", ("Model proposal", "typed candidate"), 245, 65, 170, 95, BLUE),
            Node(
                "quarantine", ("Candidate quarantine", "not retrievable"), 460, 65, 180, 95, AMBER
            ),
            Node(
                "policy", ("Validation + policy", "deterministic checks"), 685, 65, 180, 95, INDIGO
            ),
            Node(
                "commit",
                ("Immutable revision", "concept + evidence ledger"),
                760,
                255,
                200,
                95,
                GREEN,
            ),
            Node("review", ("Human review", "supported but uncertain"), 410, 255, 175, 95, BLUE),
            Node("reject", ("Reject", "unsupported or unsafe"), 90, 255, 165, 95, ROSE),
        ),
        edges=(
            Edge("evidence", "model"),
            Edge("model", "quarantine"),
            Edge("quarantine", "policy"),
            Edge("policy", "commit", "commit"),
            Edge("policy", "review", "review"),
            Edge("policy", "reject", "reject"),
        ),
    ),
    "provider-neutral": Diagram(
        key="provider-neutral",
        title="Canonical learning stays provider-neutral",
        caption=(
            "Clients, model providers, stores, and indexes are replaceable adapters. Canonical "
            "identity, evidence, policy, lifecycle, and audit remain inside ELL."
        ),
        width=960,
        height=500,
        nodes=(
            Node(
                "clients", ("Clients + connectors", "capture and consent"), 330, 25, 300, 85, SLATE
            ),
            Node("models", ("Model providers", "propose interpretations"), 25, 190, 210, 95, BLUE),
            Node(
                "core",
                (
                    "ELL canonical core",
                    "evidence · policy · lifecycle",
                    "versioning · audit · retrieval",
                ),
                320,
                165,
                320,
                150,
                INDIGO,
            ),
            Node(
                "stores", ("Stores + indexes", "rebuildable projections"), 725, 190, 210, 95, AMBER
            ),
            Node(
                "outputs",
                ("Evidence packets + exports", "applications and evaluation"),
                330,
                385,
                300,
                85,
                GREEN,
            ),
        ),
        edges=(
            Edge("clients", "core", "episodes"),
            Edge("models", "core", "candidates"),
            Edge("stores", "core", "retrieval"),
            Edge("core", "outputs", "scoped use"),
        ),
    ),
}


def _node_map(diagram: Diagram) -> Dict[str, Node]:
    return {node.identifier: node for node in diagram.nodes}


def _edge_points(source: Node, target: Node) -> Tuple[float, float, float, float]:
    if source.y + source.height <= target.y:
        return (
            source.x + source.width / 2,
            source.y + source.height,
            target.x + target.width / 2,
            target.y,
        )
    if target.y + target.height <= source.y:
        return (
            source.x + source.width / 2,
            source.y,
            target.x + target.width / 2,
            target.y + target.height,
        )
    if source.x < target.x:
        return (
            source.x + source.width,
            source.y + source.height / 2,
            target.x,
            target.y + target.height / 2,
        )
    return (
        source.x,
        source.y + source.height / 2,
        target.x + target.width,
        target.y + target.height / 2,
    )


def diagram_svg(diagram: Diagram) -> str:
    """Render one diagram as accessible standalone SVG."""
    nodes = _node_map(diagram)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {diagram.width:g} {diagram.height:g}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(diagram.title)}</title>',
        f'<desc id="desc">{escape(diagram.caption)}</desc>',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#8A98AA"/></marker></defs>',
        '<rect width="100%" height="100%" rx="24" fill="#FBFCFE"/>',
    ]
    for edge in diagram.edges:
        x1, y1, x2, y2 = _edge_points(nodes[edge.source], nodes[edge.target])
        dash = ' stroke-dasharray="8 7"' if edge.dashed else ""
        parts.append(
            f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{LINE}" stroke-width="2.2" marker-end="url(#arrow)"{dash}/>'
        )
        if edge.label:
            parts.append(
                f'<text x="{(x1 + x2) / 2:g}" y="{(y1 + y2) / 2 - 8:g}" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif" font-size="14" fill="{MUTED}">{escape(edge.label)}</text>'
            )
    for node in diagram.nodes:
        parts.append(
            f'<rect x="{node.x:g}" y="{node.y:g}" width="{node.width:g}" height="{node.height:g}" rx="16" fill="{node.fill}" stroke="#B8C3D1" stroke-width="1.5"/>'
        )
        line_height = 24
        first_y = node.y + node.height / 2 - (len(node.lines) - 1) * line_height / 2
        for index, line in enumerate(node.lines):
            weight = "700" if index == 0 else "500"
            size = "17" if index == 0 else "14"
            parts.append(
                f'<text x="{node.x + node.width / 2:g}" y="{first_y + index * line_height:g}" dominant-baseline="middle" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif" font-size="{size}" font-weight="{weight}" fill="{INK}">{escape(line)}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def write_svg_assets(output_dir: Path) -> None:
    """Write every tracked SVG asset from its shared diagram definition."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for key, diagram in DIAGRAMS.items():
        (output_dir / f"{key}.svg").write_text(diagram_svg(diagram), encoding="utf-8")


def pdf_diagram_flowables(key: str, caption_style: object) -> Iterable[object]:
    """Render one shared diagram for the ReportLab paper."""
    diagram = DIAGRAMS[key]
    width = 455.0
    scale = width / diagram.width
    height = diagram.height * scale
    drawing = Drawing(width, height)
    nodes = _node_map(diagram)

    for edge in diagram.edges:
        x1, y1, x2, y2 = _edge_points(nodes[edge.source], nodes[edge.target])
        px1, py1 = x1 * scale, height - y1 * scale
        px2, py2 = x2 * scale, height - y2 * scale
        line = Line(px1, py1, px2, py2)
        line.strokeColor = colors.HexColor(LINE)
        line.strokeWidth = 1.2
        if edge.dashed:
            line.strokeDashArray = [4, 3]
        drawing.add(line)
        arrow_size = 4.0
        direction = 1 if px2 >= px1 else -1
        drawing.add(
            Polygon(
                [
                    px2,
                    py2,
                    px2 - direction * arrow_size,
                    py2 + 2.5,
                    px2 - direction * arrow_size,
                    py2 - 2.5,
                ],
                fillColor=colors.HexColor(LINE),
                strokeColor=colors.HexColor(LINE),
            )
        )
        if edge.label:
            drawing.add(
                String(
                    (px1 + px2) / 2,
                    (py1 + py2) / 2 + 4,
                    edge.label,
                    fontName="ELLBody",
                    fontSize=5.8,
                    fillColor=colors.HexColor(MUTED),
                    textAnchor="middle",
                )
            )

    for node in diagram.nodes:
        x = node.x * scale
        y = height - (node.y + node.height) * scale
        drawing.add(
            Rect(
                x,
                y,
                node.width * scale,
                node.height * scale,
                rx=7,
                ry=7,
                fillColor=colors.HexColor(node.fill),
                strokeColor=colors.HexColor("#B8C3D1"),
                strokeWidth=0.7,
            )
        )
        line_height = 9.0
        center_y = y + node.height * scale / 2
        first_y = center_y + (len(node.lines) - 1) * line_height / 2
        for index, text in enumerate(node.lines):
            drawing.add(
                String(
                    x + node.width * scale / 2,
                    first_y - index * line_height,
                    text,
                    fontName="ELLBold" if index == 0 else "ELLBody",
                    fontSize=7.2 if index == 0 else 6.2,
                    fillColor=colors.HexColor(INK),
                    textAnchor="middle",
                )
            )

    caption = Paragraph(f"<b>{escape(diagram.title)}.</b> {escape(diagram.caption)}", caption_style)
    return (Spacer(1, 8), drawing, Spacer(1, 4), caption, Spacer(1, 8))
