#!/usr/bin/env python3
"""Generate the paper's explanatory visual system as high-resolution PNGs.

The figures are intentionally diagrammatic rather than decorative. Every label is
kept in code so the visuals remain reviewable, reproducible, and consistent with
the claims in the Quarto source.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from PIL import Image, ImageDraw, ImageFont


SCALE = 2
WIDTH = 1200
HEIGHT = 600
OUT = Path(__file__).resolve().parents[1] / "chapters" / "assets" / "visuals"

def first_existing(candidates: Sequence[str]) -> Path:
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    raise FileNotFoundError(f"No supported diagram font found in: {', '.join(candidates)}")


FONT_REGULAR = first_existing(
    (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    )
)
FONT_BOLD = first_existing(
    (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    )
)

BG = "#F7F9FC"
PAPER = "#FFFFFF"
INK = "#17233C"
MUTED = "#5F6C80"
LINE = "#A9B5C5"
BLUE = "#E7F1FF"
BLUE_DARK = "#2D6FB2"
PURPLE = "#EEE9FF"
PURPLE_DARK = "#6D55B5"
GREEN = "#E5F5ED"
GREEN_DARK = "#2E7A59"
AMBER = "#FFF3D5"
AMBER_DARK = "#9B6A13"
RED = "#FDE9EC"
RED_DARK = "#A74551"
GRAY = "#EDF1F5"
GRAY_DARK = "#637084"


@dataclass(frozen=True)
class CardSpec:
    title: str
    lines: tuple[str, ...] = ()
    fill: str = GRAY
    accent: str = GRAY_DARK


class Figure:
    def __init__(self, title: str, kicker: str, subtitle: str = "") -> None:
        self.image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), BG)
        self.draw = ImageDraw.Draw(self.image)
        self.fonts: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}
        self.rounded((12, 12, WIDTH - 12, HEIGHT - 12), 24, PAPER, "#E4E9F0", 1)
        self.text((44, 35), kicker.upper(), 13, MUTED, bold=True)
        self.text((44, 66), title, 29, INK, bold=True)
        if subtitle:
            self.text((44, 106), subtitle, 14, MUTED, max_width=1110)

    def font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        key = (size, bold)
        if key not in self.fonts:
            self.fonts[key] = ImageFont.truetype(
                str(FONT_BOLD if bold else FONT_REGULAR), size * SCALE
            )
        return self.fonts[key]

    @staticmethod
    def s(value: float) -> int:
        return round(value * SCALE)

    def rounded(
        self,
        box: tuple[float, float, float, float],
        radius: float,
        fill: str,
        outline: str | None = None,
        width: int = 1,
    ) -> None:
        self.draw.rounded_rectangle(
            tuple(self.s(v) for v in box),
            radius=self.s(radius),
            fill=fill,
            outline=outline,
            width=self.s(width),
        )

    def line(
        self,
        points: Sequence[tuple[float, float]],
        fill: str = LINE,
        width: int = 2,
    ) -> None:
        self.draw.line(
            [(self.s(x), self.s(y)) for x, y in points],
            fill=fill,
            width=self.s(width),
            joint="curve",
        )

    def arrow(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        fill: str = LINE,
        width: int = 3,
    ) -> None:
        self.line((start, end), fill, width)
        x1, y1 = start
        x2, y2 = end
        dx, dy = x2 - x1, y2 - y1
        length = max((dx * dx + dy * dy) ** 0.5, 1)
        ux, uy = dx / length, dy / length
        px, py = -uy, ux
        size = 10
        tip = (self.s(x2), self.s(y2))
        left = (self.s(x2 - ux * size + px * size * 0.55), self.s(y2 - uy * size + py * size * 0.55))
        right = (self.s(x2 - ux * size - px * size * 0.55), self.s(y2 - uy * size - py * size * 0.55))
        self.draw.polygon((tip, left, right), fill=fill)

    def text(
        self,
        xy: tuple[float, float],
        value: str,
        size: int,
        fill: str = INK,
        *,
        bold: bool = False,
        anchor: str = "la",
        max_width: float | None = None,
        spacing: int = 5,
    ) -> None:
        font = self.font(size, bold)
        value = self.wrap(value, font, max_width) if max_width else value
        self.draw.multiline_text(
            (self.s(xy[0]), self.s(xy[1])),
            value,
            fill=fill,
            font=font,
            anchor=anchor,
            spacing=self.s(spacing),
            align="center" if anchor in {"ma", "mm"} else "left",
        )

    def wrap(self, value: str, font: ImageFont.FreeTypeFont, max_width: float) -> str:
        output: list[str] = []
        for paragraph in value.split("\n"):
            words = paragraph.split()
            if not words:
                output.append("")
                continue
            line = words[0]
            for word in words[1:]:
                candidate = f"{line} {word}"
                box = self.draw.textbbox((0, 0), candidate, font=font)
                if box[2] - box[0] <= self.s(max_width):
                    line = candidate
                else:
                    output.append(line)
                    line = word
            output.append(line)
        return "\n".join(output)

    def card(
        self,
        box: tuple[float, float, float, float],
        spec: CardSpec,
        *,
        title_size: int = 18,
        body_size: int = 13,
        number: str | None = None,
    ) -> None:
        x1, y1, x2, y2 = box
        self.rounded(box, 18, spec.fill, "#C8D1DD", 1)
        self.rounded((x1, y1, x1 + 7, y2), 4, spec.accent)
        if number:
            self.rounded((x1 + 18, y1 + 16, x1 + 51, y1 + 49), 16, spec.accent)
            self.text((x1 + 34.5, y1 + 32.5), number, 13, PAPER, bold=True, anchor="mm")
            title_x = x1 + 64
        else:
            title_x = x1 + 22
        self.text((title_x, y1 + 22), spec.title, title_size, INK, bold=True, max_width=x2 - title_x - 18)
        if spec.lines:
            self.text(
                (x1 + 22, y1 + 58),
                "\n".join(spec.lines),
                body_size,
                MUTED,
                max_width=x2 - x1 - 42,
                spacing=7,
            )

    def pill(self, box: tuple[float, float, float, float], label: str, fill: str, accent: str) -> None:
        self.rounded(box, 14, fill, accent, 1)
        x1, y1, x2, y2 = box
        self.text(((x1 + x2) / 2, (y1 + y2) / 2), label, 13, accent, bold=True, anchor="mm")

    def footer(self, label: str, *, fill: str = PURPLE, accent: str = PURPLE_DARK) -> None:
        self.rounded((44, 526, 1156, 568), 16, fill, accent, 1)
        self.text((600, 547), label, 14, accent, bold=True, anchor="mm")

    def save(self, filename: str) -> None:
        OUT.mkdir(parents=True, exist_ok=True)
        self.image.save(OUT / filename, optimize=True)


def card_grid(
    filename: str,
    title: str,
    kicker: str,
    specs: Sequence[CardSpec],
    *,
    columns: int = 3,
    footer: str = "",
) -> None:
    fig = Figure(title, kicker)
    rows = (len(specs) + columns - 1) // columns
    left, right, top, bottom = 44, 1156, 142, 506
    gap_x, gap_y = 18, 18
    width = (right - left - gap_x * (columns - 1)) / columns
    height = (bottom - top - gap_y * (rows - 1)) / rows
    for index, spec in enumerate(specs):
        row, column = divmod(index, columns)
        x1 = left + column * (width + gap_x)
        y1 = top + row * (height + gap_y)
        fig.card((x1, y1, x1 + width, y1 + height), spec, title_size=16, body_size=12)
    if footer:
        fig.footer(footer)
    fig.save(filename)


def horizontal_flow(
    filename: str,
    title: str,
    kicker: str,
    specs: Sequence[CardSpec],
    *,
    footer: str = "",
) -> None:
    fig = Figure(title, kicker)
    count = len(specs)
    gap = 30
    left, right = 44, 1156
    width = (right - left - gap * (count - 1)) / count
    y1, y2 = 184, 430
    for index, spec in enumerate(specs):
        x1 = left + index * (width + gap)
        fig.card((x1, y1, x1 + width, y2), spec, title_size=17, body_size=13, number=str(index + 1))
        if index < count - 1:
            fig.arrow((x1 + width + 4, 307), (x1 + width + gap - 4, 307), LINE, 3)
    if footer:
        fig.footer(footer)
    fig.save(filename)


def memory_vs_learning() -> None:
    fig = Figure("Remembering is not yet learning", "Core distinction")
    fig.card((44, 150, 520, 448), CardSpec("Memory access", ("Finds relevant past episodes", "Answers: What happened before?", "Can improve continuity"), BLUE, BLUE_DARK), title_size=24, body_size=17)
    fig.card((680, 150, 1156, 448), CardSpec("Experience learning", ("Forms scoped, revisable concepts", "Answers: What should change next?", "Must improve future behaviour"), PURPLE, PURPLE_DARK), title_size=24, body_size=17)
    fig.arrow((530, 299), (670, 299), PURPLE_DARK, 4)
    fig.pill((520, 222, 680, 276), "evidence", GRAY, GRAY_DARK)
    fig.pill((520, 322, 680, 376), "outcomes", GREEN, GREEN_DARK)
    fig.footer("ELL is justified only when the right-hand side adds measurable transfer without weakening safety.")
    fig.save("memory-vs-learning.png")


def intuition_packet() -> None:
    fig = Figure("The delivery object is a compact intuition packet", "From history to useful context")
    fig.card((44, 196, 235, 408), CardSpec("Current situation", ("task", "actor", "purpose", "budget"), GRAY, GRAY_DARK), title_size=18, body_size=13)
    fig.arrow((242, 302), (302, 302), LINE, 3)
    fig.rounded((310, 142, 830, 462), 24, PURPLE, PURPLE_DARK, 2)
    fig.text((570, 172), "INTUITION PACKET", 15, PURPLE_DARK, bold=True, anchor="ma")
    items = [
        ("Scoped concepts", BLUE, BLUE_DARK),
        ("Selected episodes", GRAY, GRAY_DARK),
        ("Counterevidence", RED, RED_DARK),
        ("Uncertainty", AMBER, AMBER_DARK),
        ("Why this was selected", GREEN, GREEN_DARK),
        ("Stable evidence links", BLUE, BLUE_DARK),
    ]
    for i, (label, fill, accent) in enumerate(items):
        row, col = divmod(i, 2)
        x1 = 338 + col * 238
        y1 = 220 + row * 68
        fig.pill((x1, y1, x1 + 214, y1 + 48), label, fill, accent)
    fig.arrow((838, 302), (898, 302), LINE, 3)
    fig.card((905, 196, 1156, 408), CardSpec("Application", ("response", "decision", "action", "outcome feedback"), GREEN, GREEN_DARK), title_size=20, body_size=14)
    fig.footer("Compact by default; inspectable on demand; revisable after outcomes.")
    fig.save("intuition-packet.png")


def useful_concept() -> None:
    card_grid(
        "useful-concept.png",
        "A reusable concept must pass six tests",
        "Problem definition",
        [
            CardSpec("Grounded", ("Traceable to exact episodes",), BLUE, BLUE_DARK),
            CardSpec("General", ("Useful beyond one case",), PURPLE, PURPLE_DARK),
            CardSpec("Scoped", ("States where it may apply",), AMBER, AMBER_DARK),
            CardSpec("Revisable", ("Changes with counterevidence",), RED, RED_DARK),
            CardSpec("Actionable", ("Can affect a later decision",), GREEN, GREEN_DARK),
            CardSpec("Measurable", ("Correctness and utility can be tested",), GRAY, GRAY_DARK),
        ],
        columns=3,
        footer="A fluent summary that fails any one test is not yet trusted knowledge.",
    )


def failure_modes() -> None:
    card_grid(
        "failure-modes.png",
        "Seven ways memory can look intelligent without learning",
        "Failure modes",
        [
            CardSpec("Replay", ("Episodes return", "No principle forms"), RED, RED_DARK),
            CardSpec("Overgeneralise", ("One vivid case", "Becomes a broad rule"), RED, RED_DARK),
            CardSpec("Confirm itself", ("Retrieval favours", "Supporting evidence"), RED, RED_DARK),
            CardSpec("Lose context", ("Conditions disappear", "Scope becomes vague"), AMBER, AMBER_DARK),
            CardSpec("Go stale", ("Reality changes", "Old rule persists"), AMBER, AMBER_DARK),
            CardSpec("Lose provenance", ("Claim survives", "Evidence link does not"), AMBER, AMBER_DARK),
            CardSpec("Claim learning", ("A summary was stored", "Behaviour did not improve"), GRAY, GRAY_DARK),
            CardSpec("ELL response", ("Separate, test, scope,", "revise, and measure"), GREEN, GREEN_DARK),
        ],
        columns=4,
        footer="The architecture is organised around preventing these failures, not around adding another store.",
    )


def claim_hierarchy() -> None:
    fig = Figure("Not every research question can prove the core claim", "Claim hierarchy")
    tiers = [
        ("PRIMARY CONFIRMATORY", "RQ3 - structurally distant transfer", 132, 1050, PURPLE, PURPLE_DARK),
        ("MANDATORY GUARDRAIL", "RQ1 - unsupported generalisation", 194, 900, RED, RED_DARK),
        ("MECHANISMS", "RQ2 revision  |  RQ4 efficiency", 256, 760, BLUE, BLUE_DARK),
        ("EXPLORATORY PRODUCT", "RQ5 - intuition quality", 318, 620, GREEN, GREEN_DARK),
        ("SEPARATE FOLLOW-ON", "RQ6 - governed meta-learning", 380, 480, AMBER, AMBER_DARK),
    ]
    for label, value, y, width, fill, accent in tiers:
        x1 = (WIDTH - width) / 2
        fig.rounded((x1, y, x1 + width, y + 50), 15, fill, accent, 1)
        fig.text((x1 + 20, y + 25), label, 11, accent, bold=True, anchor="lm")
        fig.text((x1 + width - 20, y + 25), value, 15, INK, bold=True, anchor="rm")
    fig.footer("Exploratory scores cannot rescue a failed transfer result; Phase 7 cannot reinterpret ELL-Core.")
    fig.save("claim-hierarchy.png")


def research_landscape() -> None:
    fig = Figure("ELL sits where abstraction meets evidence control", "Research landscape")
    left, top, right, bottom = 135, 152, 1125, 480
    fig.line(((left, bottom), (right, bottom)), GRAY_DARK, 2)
    fig.line(((left, bottom), (left, top)), GRAY_DARK, 2)
    fig.arrow((left, bottom), (right, bottom), GRAY_DARK, 2)
    fig.arrow((left, bottom), (left, top), GRAY_DARK, 2)
    fig.text((630, 507), "more cross-episode abstraction", 13, MUTED, bold=True, anchor="ma")
    fig.text((76, 315), "stronger evidence\nand lifecycle control", 13, MUTED, bold=True, anchor="mm")
    points = [
        (250, 415, "Context\nmanagement", GRAY, GRAY_DARK),
        (430, 372, "Hybrid retrieval\n+ temporal graphs", BLUE, BLUE_DARK),
        (620, 326, "Reflection +\ninsight extraction", AMBER, AMBER_DARK),
        (805, 274, "Schemas, skills,\nworkflows", GREEN, GREEN_DARK),
        (995, 198, "ELL-Core", PURPLE, PURPLE_DARK),
    ]
    for x, y, label, fill, accent in points:
        fig.rounded((x - 82, y - 38, x + 82, y + 38), 18, fill, accent, 2 if label == "ELL-Core" else 1)
        fig.text((x, y), label, 13, INK if label != "ELL-Core" else PURPLE_DARK, bold=True, anchor="mm")
    fig.footer("Novelty is not abstraction alone; the test is measurable transfer under explicit evidence, revision, and cost gates.")
    fig.save("research-landscape.png")


def empirical_cautions() -> None:
    card_grid(
        "empirical-cautions.png",
        "Three cautions shape the comparison discipline",
        "What prior evidence warns us about",
        [
            CardSpec("More architecture", ("can add retrieval competition", "and negative transfer"), RED, RED_DARK),
            CardSpec("More structure", ("does not guarantee", "cross-domain generality"), AMBER, AMBER_DARK),
            CardSpec("More memory", ("can improve recall", "without improving decisions"), BLUE, BLUE_DARK),
            CardSpec("Required response", ("match model, stream, budget,", "outcomes, and total cost"), GREEN, GREEN_DARK),
        ],
        columns=4,
        footer="ELL competes against the strongest eligible baseline, including simple agent-controlled memory.",
    )


def learning_spectrum() -> None:
    horizontal_flow(
        "learning-spectrum.png",
        "The field has moved from storage toward experience abstraction",
        "Related work",
        [
            CardSpec("Storage", ("save", "search", "retrieve"), GRAY, GRAY_DARK),
            CardSpec("Reflection", ("summarise", "interpret", "critique"), BLUE, BLUE_DARK),
            CardSpec("Abstraction", ("schemas", "skills", "concepts"), AMBER, AMBER_DARK),
            CardSpec("Governed learning", ("evidence", "scope", "revision", "outcomes"), PURPLE, PURPLE_DARK),
        ],
        footer="ELL's contribution claim begins only at the last step - and only if the experiment supports it.",
    )


def policy_boundary() -> None:
    fig = Figure("Learning may change strategy, never the constitution", "Governed self-scaffolding")
    fig.rounded((80, 144, 1120, 486), 28, RED, RED_DARK, 2)
    fig.text((110, 176), "IMMUTABLE OUTER BOUNDARY", 15, RED_DARK, bold=True)
    for i, label in enumerate(("provenance", "consent", "permissions", "deletion", "canonical commit", "evaluation + rollback")):
        x1 = 110 + (i % 3) * 330
        y1 = 214 + (i // 3) * 76
        fig.pill((x1, y1, x1 + 294, y1 + 48), label, PAPER, RED_DARK)
    fig.rounded((314, 348, 886, 458), 22, PURPLE, PURPLE_DARK, 2)
    fig.text((600, 375), "LEARNABLE INNER STRATEGY", 15, PURPLE_DARK, bold=True, anchor="ma")
    fig.text((600, 416), "segmentation  |  reflection  |  ranking  |  consolidation  |  budgets", 14, INK, anchor="ma")
    fig.footer("Models may propose a better scaffold; deterministic governance decides whether it may run.", fill=RED, accent=RED_DARK)
    fig.save("policy-boundary.png")


def evidence_ledger() -> None:
    fig = Figure("A concept is a versioned evidence ledger, not a timeless fact", "Architecture")
    y = 300
    fig.line(((90, y), (1110, y)), LINE, 4)
    events = [
        (150, "Support", "episodes 4, 9", BLUE, BLUE_DARK),
        (350, "Concept v1", "scope A", PURPLE, PURPLE_DARK),
        (550, "Counterevidence", "episode 14", RED, RED_DARK),
        (750, "Concept v2", "narrowed scope", PURPLE, PURPLE_DARK),
        (950, "Outcome", "helped in case 21", GREEN, GREEN_DARK),
    ]
    for i, (x, title, body, fill, accent) in enumerate(events):
        fig.rounded((x - 76, y - 40, x + 76, y + 40), 18, fill, accent, 2)
        fig.text((x, y - 10), title, 14, accent, bold=True, anchor="mm")
        fig.text((x, y + 16), body, 12, MUTED, anchor="mm")
        fig.line(((x, y + 42), (x, 455)), accent, 2)
        fig.text((x, 472), f"t{i + 1}", 12, accent, bold=True, anchor="ma")
    fig.footer("Support, contradiction, scope, validity, lineage, and utility remain inspectable across revisions.")
    fig.save("evidence-ledger.png")


def association_reflection() -> None:
    fig = Figure("Associations propose context; reflection proposes meaning", "Architecture")
    episode_points = [(115, 190), (115, 290), (115, 390), (300, 220), (300, 360)]
    for i, (x, y) in enumerate(episode_points, 1):
        fig.rounded((x - 58, y - 32, x + 58, y + 32), 15, GRAY, GRAY_DARK, 1)
        fig.text((x, y), f"Episode {i}", 13, INK, bold=True, anchor="mm")
    for a, b in ((0, 1), (1, 3), (2, 4), (3, 4), (1, 4)):
        fig.line((episode_points[a], episode_points[b]), LINE, 2)
    fig.arrow((360, 290), (505, 290), BLUE_DARK, 3)
    fig.card((520, 170, 790, 410), CardSpec("Reflection proposal", ("cluster summary", "candidate pattern", "cited episode spans"), BLUE, BLUE_DARK), title_size=21, body_size=15)
    fig.arrow((800, 290), (885, 290), PURPLE_DARK, 3)
    fig.card((900, 170, 1145, 410), CardSpec("Critique", ("corroboration?", "contradiction?", "scope?", "novelty?"), AMBER, AMBER_DARK), title_size=21, body_size=15)
    fig.footer("A semantic link can help find evidence; it cannot by itself authorize a concept.")
    fig.save("association-reflection.png")


def concept_anatomy() -> None:
    fig = Figure("What makes a concept inspectable and revisable", "Concept anatomy")
    fig.rounded((430, 190, 770, 430), 26, PURPLE, PURPLE_DARK, 2)
    fig.text((600, 248), "VERSIONED CONCEPT", 20, PURPLE_DARK, bold=True, anchor="ma")
    fig.text((600, 310), "claim or strategy", 18, INK, bold=True, anchor="ma")
    fig.text((600, 354), "never detached from its ledger", 13, MUTED, anchor="ma")
    items = [
        ("Scope", 145, 172, AMBER, AMBER_DARK),
        ("Supporting evidence", 165, 322, BLUE, BLUE_DARK),
        ("Counterevidence", 950, 172, RED, RED_DARK),
        ("Temporal validity", 950, 322, GREEN, GREEN_DARK),
        ("Confidence", 360, 474, GRAY, GRAY_DARK),
        ("Lineage + utility", 840, 474, PURPLE, PURPLE_DARK),
    ]
    for label, x, y, fill, accent in items:
        fig.pill((x - 120, y - 24, x + 120, y + 24), label, fill, accent)
        target = (430, 270) if x < 430 else (770, 270) if x > 770 else (x, 430)
        source = (x, y + 24) if y < 430 else (x, y - 24)
        fig.arrow(source, target, accent, 2)
    fig.save("concept-anatomy.png")


def fast_slow_loops() -> None:
    fig = Figure("Two loops evolve at different speeds and under different authority", "Architecture")
    fig.rounded((44, 150, 1156, 300), 20, GREEN, GREEN_DARK, 1)
    fig.text((72, 178), "FAST LOOP - every application", 14, GREEN_DARK, bold=True)
    fast = ["retrieve packet", "apply concept", "observe outcome", "revise evidence"]
    for i, label in enumerate(fast):
        x = 195 + i * 270
        fig.pill((x - 100, 218, x + 100, 266), label, PAPER, GREEN_DARK)
        if i < len(fast) - 1:
            fig.arrow((x + 106, 242), (x + 164, 242), GREEN_DARK, 2)
    fig.rounded((44, 330, 1156, 486), 20, PURPLE, PURPLE_DARK, 1)
    fig.text((72, 358), "SLOW LOOP - preregistered strategy trials", 14, PURPLE_DARK, bold=True)
    slow = ["propose scaffold", "replay + time-forward test", "shadow + canary", "promote or rollback"]
    for i, label in enumerate(slow):
        x = 195 + i * 270
        fig.pill((x - 100, 398, x + 100, 446), label, PAPER, PURPLE_DARK)
        if i < len(slow) - 1:
            fig.arrow((x + 106, 422), (x + 164, 422), PURPLE_DARK, 2)
    fig.footer("The fast loop revises concepts. The slow loop may revise strategy only after ELL-Core succeeds.")
    fig.save("fast-slow-loops.png")


def algorithm_loop() -> None:
    horizontal_flow(
        "algorithm-loop.png",
        "The minimum learning loop is transparent and interruptible",
        "Proposed algorithms",
        [
            CardSpec("Schedule", ("novelty", "contradiction", "time window"), GRAY, GRAY_DARK),
            CardSpec("Reflect", ("bounded evidence", "typed proposal", "exact citations"), BLUE, BLUE_DARK),
            CardSpec("Critique", ("support", "scope", "counterexamples"), AMBER, AMBER_DARK),
            CardSpec("Consolidate", ("promote", "revise", "merge or split"), PURPLE, PURPLE_DARK),
            CardSpec("Apply + learn", ("retrieve", "record outcome", "update ledger"), GREEN, GREEN_DARK),
        ],
        footer="Each model step proposes; deterministic validation and policy decide what becomes durable.",
    )


def confidence_evidence() -> None:
    fig = Figure("Confidence is computed from evidence, not eloquence", "Evidence-weighted confidence")
    positives = ["independent support", "source diversity", "successful outcomes", "scope fit"]
    negatives = ["counterevidence", "correlated sources", "staleness", "failed outcomes"]
    for i, label in enumerate(positives):
        fig.pill((54, 160 + i * 76, 342, 208 + i * 76), label, GREEN, GREEN_DARK)
        fig.arrow((348, 184 + i * 76), (485, 280), GREEN_DARK, 2)
    for i, label in enumerate(negatives):
        fig.pill((858, 160 + i * 76, 1146, 208 + i * 76), label, RED, RED_DARK)
        fig.arrow((852, 184 + i * 76), (715, 280), RED_DARK, 2)
    fig.rounded((470, 205, 730, 390), 26, PURPLE, PURPLE_DARK, 2)
    fig.text((600, 250), "BOUNDED SCORE", 18, PURPLE_DARK, bold=True, anchor="ma")
    fig.text((600, 307), "confidence [0, 1]", 21, INK, bold=True, anchor="ma")
    fig.text((600, 354), "with an evidence receipt", 13, MUTED, anchor="ma")
    fig.footer("A model may phrase a claim confidently; only the ledger may justify confidence.")
    fig.save("confidence-evidence.png")


def revision_paths() -> None:
    fig = Figure("New evidence can narrow, combine, divide, or retire a concept", "Revision discipline")
    fig.card((44, 224, 264, 392), CardSpec("Concept v1", ("current claim", "known scope"), PURPLE, PURPLE_DARK), title_size=20, body_size=14)
    fig.arrow((270, 308), (384, 308), PURPLE_DARK, 3)
    fig.pill((384, 284, 550, 332), "new evidence", AMBER, AMBER_DARK)
    paths = [
        ("Revise", "new immutable version", 670, 150, BLUE, BLUE_DARK),
        ("Merge", "overlapping concepts", 930, 150, GREEN, GREEN_DARK),
        ("Split", "context-dependent rules", 670, 342, AMBER, AMBER_DARK),
        ("Retire", "no longer reliable", 930, 342, RED, RED_DARK),
    ]
    for title, body, x, y, fill, accent in paths:
        fig.card((x, y, x + 216, y + 140), CardSpec(title, (body,), fill, accent), title_size=19, body_size=13)
        fig.arrow((558, 308), (x - 8, y + 70), accent, 2)
    fig.footer("History is never overwritten; superseded versions remain inspectable and non-retrievable by default.")
    fig.save("revision-paths.png")


def retrieval_invalidation() -> None:
    fig = Figure("Retrieval and deletion are policy operations, not index operations", "Algorithms")
    fig.rounded((44, 150, 1156, 298), 20, BLUE, BLUE_DARK, 1)
    fig.text((70, 176), "RETRIEVAL", 13, BLUE_DARK, bold=True)
    top = ["authorize", "filter lifecycle", "generate candidates", "rank", "restore evidence"]
    for i, label in enumerate(top):
        x = 160 + i * 220
        fig.pill((x - 82, 214, x + 82, 262), label, PAPER, BLUE_DARK)
        if i < len(top) - 1:
            fig.arrow((x + 86, 238), (x + 132, 238), BLUE_DARK, 2)
    fig.rounded((44, 330, 1156, 486), 20, RED, RED_DARK, 1)
    fig.text((70, 356), "DELETION / INVALIDATION", 13, RED_DARK, bold=True)
    bottom = ["exclude immediately", "write tombstone", "close dependent claims", "remove projections", "block resurrection"]
    for i, label in enumerate(bottom):
        x = 160 + i * 220
        fig.pill((x - 82, 398, x + 82, 446), label, PAPER, RED_DARK)
        if i < len(bottom) - 1:
            fig.arrow((x + 86, 422), (x + 132, 422), RED_DARK, 2)
    fig.footer("An approximate index may accelerate candidates; it cannot bypass authorization, validity, or forgetting.")
    fig.save("retrieval-invalidation.png")


def entity_ledger() -> None:
    specs = [
        CardSpec("Source artifact", ("immutable evidence", "stable address"), GRAY, GRAY_DARK),
        CardSpec("Episode", ("bounded experience", "context + outcome"), BLUE, BLUE_DARK),
        CardSpec("Reflection", ("provisional meaning", "quarantined"), AMBER, AMBER_DARK),
        CardSpec("Concept version", ("scoped claim", "evidence ledger"), PURPLE, PURPLE_DARK),
        CardSpec("Application receipt", ("what was used", "in which decision"), GREEN, GREEN_DARK),
        CardSpec("Outcome", ("independent result", "or correction"), RED, RED_DARK),
    ]
    horizontal_flow(
        "entity-ledger.png",
        "Six canonical objects carry the learning claim",
        "Data model",
        specs,
        footer="Every arrow is addressable; every revision is immutable; every outcome has independent provenance.",
    )


def concept_states() -> None:
    fig = Figure("Concepts move through an explicit lifecycle", "State machine")
    states = [
        ("Proposed", AMBER, AMBER_DARK),
        ("Corroborated", BLUE, BLUE_DARK),
        ("Contested", RED, RED_DARK),
        ("Revised", PURPLE, PURPLE_DARK),
        ("Superseded", GRAY, GRAY_DARK),
        ("Retired", GRAY, GRAY_DARK),
    ]
    positions = [(145, 220), (355, 220), (565, 220), (775, 220), (985, 220), (985, 402)]
    for i, ((label, fill, accent), (x, y)) in enumerate(zip(states, positions)):
        fig.rounded((x - 78, y - 38, x + 78, y + 38), 18, fill, accent, 2)
        fig.text((x, y), label, 15, accent, bold=True, anchor="mm")
        if i < len(states) - 1:
            nx, ny = positions[i + 1]
            fig.arrow((x + 84 if ny == y else x, y), (nx - 84 if ny == y else nx, ny - 44), accent, 2)
    fig.arrow((690, 282), (420, 370), PURPLE_DARK, 2)
    fig.pill((300, 360, 540, 412), "new version retains lineage", PURPLE, PURPLE_DARK)
    fig.arrow((300, 386), (230, 258), PURPLE_DARK, 2)
    fig.footer("Contested concepts may remain inspectable while ordinary retrieval excludes superseded or retired versions.")
    fig.save("concept-states.png")


def api_boundary() -> None:
    fig = Figure("A narrow contract keeps models, stores, and applications replaceable", "Public API boundary")
    fig.rounded((380, 180, 820, 430), 28, PURPLE, PURPLE_DARK, 2)
    fig.text((600, 226), "ELL-CORE", 23, PURPLE_DARK, bold=True, anchor="ma")
    fig.text((600, 282), "validate -> commit -> retrieve", 17, INK, bold=True, anchor="ma")
    fig.text((600, 320), "apply -> record outcome -> revise", 17, INK, bold=True, anchor="ma")
    fig.text((600, 370), "canonical identity + policy + ledger", 13, MUTED, anchor="ma")
    ports = [
        ("record source", 145, 190, BLUE, BLUE_DARK),
        ("record episode", 145, 320, BLUE, BLUE_DARK),
        ("propose concept", 145, 450, AMBER, AMBER_DARK),
        ("retrieve packet", 1055, 190, GREEN, GREEN_DARK),
        ("record outcome", 1055, 320, GREEN, GREEN_DARK),
        ("validate source", 1055, 450, RED, RED_DARK),
    ]
    for label, x, y, fill, accent in ports:
        fig.pill((x - 105, y - 25, x + 105, y + 25), label, fill, accent)
        start = (x + 110, y) if x < 600 else (x - 110, y)
        end = (374, min(max(y, 210), 400)) if x < 600 else (826, min(max(y, 210), 400))
        fig.arrow(start, end, accent, 2)
    fig.footer("Adapters may change; canonical semantics and authorization do not.")
    fig.save("api-boundary.png")


def evaluation_stages() -> None:
    fig = Figure("Evaluation widens only after controlled evidence is earned", "Experimental design")
    stages = [
        ("A", "Latent-pattern streams", "controlled transfer", BLUE, BLUE_DARK),
        ("B", "Long conversations", "memory extraction", PURPLE, PURPLE_DARK),
        ("C", "Memory-dependent action", "decisions + tools", GREEN, GREEN_DARK),
        ("D", "Intuition benchmark", "product-facing", AMBER, AMBER_DARK),
        ("E", "Self-scaffolding", "separate follow-on", RED, RED_DARK),
    ]
    for i, (letter, title, body, fill, accent) in enumerate(stages):
        x1 = 60 + i * 225
        y1 = 382 - i * 46
        fig.card((x1, y1 - 120, x1 + 190, y1 + 30), CardSpec(title, (body,), fill, accent), title_size=16, body_size=12, number=letter)
        if i < len(stages) - 1:
            fig.arrow((x1 + 194, y1 - 45), (x1 + 221, y1 - 91), accent, 2)
    fig.footer("Stage A carries the confirmatory claim; later stages broaden interpretation, not the verdict.")
    fig.save("evaluation-stages.png")


def simulation_lab() -> None:
    fig = Figure("The simulation lab exposes memory dynamics before product claims", "Memory Dynamics and Intuition Simulation Lab")
    fig.card((44, 170, 280, 446), CardSpec("Controls", ("stream size", "change points", "noise", "permissions", "delayed outcomes"), GRAY, GRAY_DARK), title_size=20, body_size=14)
    fig.arrow((288, 308), (378, 308), LINE, 3)
    fig.card((390, 150, 795, 466), CardSpec("Paired conditions", ("same chronological stream", "same model and budgets", "baseline vs ELL-Core", "sealed transfer tasks", "full cost receipts"), PURPLE, PURPLE_DARK), title_size=22, body_size=15)
    fig.arrow((805, 308), (895, 308), LINE, 3)
    fig.card((905, 170, 1156, 446), CardSpec("Readouts", ("transfer", "scope safety", "adaptation", "evidence", "cost + latency"), GREEN, GREEN_DARK), title_size=20, body_size=14)
    fig.footer("Parameters are visible and replayable so a favourable result cannot depend on a hidden stream choice.")
    fig.save("simulation-lab.png")


def baseline_lanes() -> None:
    fig = Figure("Every condition receives the same stream, model, and outcome information", "Baseline lanes")
    labels = [
        ("No memory", GRAY, GRAY_DARK),
        ("Maximum context", GRAY, GRAY_DARK),
        ("BM25 / exact / fused", BLUE, BLUE_DARK),
        ("Rolling summary", BLUE, BLUE_DARK),
        ("Direct insight", AMBER, AMBER_DARK),
        ("Agent-controlled files", AMBER, AMBER_DARK),
        ("ELL-Core", PURPLE, PURPLE_DARK),
    ]
    for i, (label, fill, accent) in enumerate(labels):
        y = 150 + i * 50
        fig.pill((54, y, 306, y + 36), label, fill, accent)
        fig.line(((315, y + 18), (1045, y + 18)), accent, 3)
        fig.pill((1045, y, 1146, y + 36), "sealed", PAPER, accent)
    fig.footer("Development data selects the strongest eligible baseline before the sealed comparison is opened.")
    fig.save("baseline-lanes.png")


def metrics_dashboard() -> None:
    card_grid(
        "metrics-dashboard.png",
        "The primary result is only one tile in the decision dashboard",
        "Metrics and mandatory guardrails",
        [
            CardSpec("Transfer", (">= +5 points", "CI excludes zero"), PURPLE, PURPLE_DARK),
            CardSpec("Scope safety", ("<= +2-point harm", "non-inferiority"), RED, RED_DARK),
            CardSpec("Evidence", ("precision >= .95", "counter recall >= .90"), BLUE, BLUE_DARK),
            CardSpec("Adaptation", ("90% corrected", "within 2 contradictions"), AMBER, AMBER_DARK),
            CardSpec("Efficiency", (">= +10% utility", "per total token"), GREEN, GREEN_DARK),
            CardSpec("Governance", ("100% invariants", "+ independent replication"), GRAY, GRAY_DARK),
        ],
        columns=3,
        footer="A positive transfer estimate is labelled supported only when every guardrail also passes.",
    )


def ablation_grid() -> None:
    fig = Figure("Ablations identify which mechanism earned the result", "Experimental diagnostics")
    columns = ["Full ELL", "No critique", "No counter", "No validity", "No outcomes", "No scope"]
    rows = ["transfer", "overgeneralisation", "adaptation", "evidence", "cost"]
    x0, y0, cell_w, cell_h = 265, 172, 142, 58
    for j, label in enumerate(columns):
        fig.text((x0 + j * cell_w + cell_w / 2, 145), label, 12, PURPLE_DARK if j == 0 else MUTED, bold=True, anchor="ma")
    for i, label in enumerate(rows):
        fig.text((230, y0 + i * cell_h + cell_h / 2), label, 13, INK, bold=True, anchor="rm")
        for j in range(len(columns)):
            fill = PURPLE if j == 0 else (RED if (i + j) % 3 == 0 else GRAY)
            accent = PURPLE_DARK if j == 0 else (RED_DARK if fill == RED else GRAY_DARK)
            fig.rounded((x0 + j * cell_w, y0 + i * cell_h, x0 + j * cell_w + 118, y0 + i * cell_h + 40), 12, fill, accent, 1)
            mark = "reference" if j == 0 else "measure delta"
            fig.text((x0 + j * cell_w + 59, y0 + i * cell_h + 20), mark, 10, accent, bold=True, anchor="mm")
    fig.footer("Ablations explain a result; they cannot substitute for a failed confirmatory comparison.")
    fig.save("ablation-grid.png")


def analysis_plan() -> None:
    horizontal_flow(
        "analysis-plan.png",
        "The confirmatory decision is a sealed, paired sequence",
        "Statistical analysis",
        [
            CardSpec("Pair tasks", ("same latent rule", "same stream", "different surface"), BLUE, BLUE_DARK),
            CardSpec("Estimate", ("absolute success", "ELL minus baseline"), PURPLE, PURPLE_DARK),
            CardSpec("Uncertainty", ("paired bootstrap", "95% interval"), AMBER, AMBER_DARK),
            CardSpec("Check gates", ("evidence", "safety", "cost", "governance"), RED, RED_DARK),
            CardSpec("Assign label", ("supported", "partial", "not supported", "unsafe"), GREEN, GREEN_DARK),
        ],
        footer="Exploratory analyses are reported separately and cannot change the preregistered verdict.",
    )


def reproducibility_chain() -> None:
    horizontal_flow(
        "reproducibility-chain.png",
        "A research claim should reproduce from source to verdict",
        "Open-source publication",
        [
            CardSpec("Canonical source", ("Quarto", "schemas", "contract"), GRAY, GRAY_DARK),
            CardSpec("Frozen inputs", ("stream", "model", "prompts", "config"), BLUE, BLUE_DARK),
            CardSpec("Run receipts", ("selection", "application", "outcome", "cost"), AMBER, AMBER_DARK),
            CardSpec("Generated artifact", ("HTML", "PDF", "raw results"), PURPLE, PURPLE_DARK),
            CardSpec("Independent run", ("clean machine", "hash match", "same gates"), GREEN, GREEN_DARK),
        ],
        footer="The paper is generated; the contract and receipts are the machine-readable audit trail.",
    )


def private_boundary() -> None:
    fig = Figure("Public method and private experience must remain separable", "Publication boundary")
    fig.card((44, 160, 515, 454), CardSpec("Public research artifact", ("paper + diagrams", "schemas + code", "synthetic streams", "prompts + configs", "aggregate results"), GREEN, GREEN_DARK), title_size=23, body_size=16)
    fig.card((685, 160, 1156, 454), CardSpec("Private experience", ("raw conversations", "personal documents", "sensitive events", "consent receipts", "deletion requests"), RED, RED_DARK), title_size=23, body_size=16)
    fig.line(((600, 154), (600, 460)), RED_DARK, 4)
    fig.pill((515, 262, 685, 316), "explicit consent", AMBER, AMBER_DARK)
    fig.pill((515, 338, 685, 392), "aggregate only", BLUE, BLUE_DARK)
    fig.footer("No private corpus is required to inspect, reproduce, or criticise the core method.")
    fig.save("private-boundary.png")


def privacy_cascade() -> None:
    fig = Figure("Forgetting must cascade through every derived representation", "Privacy and security")
    fig.card((44, 216, 244, 392), CardSpec("User deletion", ("scope", "identity", "timestamp"), RED, RED_DARK), title_size=20, body_size=14)
    fig.arrow((252, 304), (340, 304), RED_DARK, 3)
    fig.card((350, 196, 600, 412), CardSpec("Canonical action", ("exclude immediately", "write tombstone", "close dependent validity"), RED, RED_DARK), title_size=20, body_size=14)
    targets = [
        ("embeddings", 760, 170),
        ("indexes", 970, 170),
        ("caches", 760, 300),
        ("exports", 970, 300),
        ("adapters", 865, 430),
    ]
    for label, x, y in targets:
        fig.pill((x - 85, y - 24, x + 85, y + 24), label, GRAY, RED_DARK)
        fig.arrow((608, 304), (x - 90, y), RED_DARK, 2)
    fig.footer("Sync and reconstruction must respect the tombstone: deleted evidence may not reappear through a projection.", fill=RED, accent=RED_DARK)
    fig.save("privacy-cascade.png")


def threat_controls() -> None:
    fig = Figure("Security controls attach to the learning path, not just storage", "Threats and controls")
    pairs = [
        ("Prompt injection", "Imported content stays data", RED, RED_DARK),
        ("Sensitive inference", "No automatic durable trait learning", AMBER, AMBER_DARK),
        ("Cross-workspace leak", "Authorize before ranking", RED, RED_DARK),
        ("Provider egress", "Purpose-bound adapters + receipts", BLUE, BLUE_DARK),
        ("Deletion bypass", "Tombstones + invalidation cascade", PURPLE, PURPLE_DARK),
    ]
    for i, (threat, control, fill, accent) in enumerate(pairs):
        y = 150 + i * 70
        fig.pill((54, y, 400, y + 46), threat, fill, accent)
        fig.arrow((410, y + 23), (520, y + 23), accent, 2)
        fig.pill((530, y, 1146, y + 46), control, GREEN, GREEN_DARK)
    fig.footer("Persistent concepts can outlive a session, so permission, purpose, and deletion checks recur at use time.")
    fig.save("threat-controls.png")


def validity_map() -> None:
    card_grid(
        "validity-map.png",
        "Four validity questions constrain what a result can mean",
        "Threats to validity",
        [
            CardSpec("Construct", ("Did the metrics capture learning", "rather than storage or fluency?"), PURPLE, PURPLE_DARK),
            CardSpec("Internal", ("Did matched conditions isolate", "the concept layer?"), BLUE, BLUE_DARK),
            CardSpec("Statistical", ("Was the effect estimated", "with adequate uncertainty?"), AMBER, AMBER_DARK),
            CardSpec("External", ("Does the result transfer beyond", "synthetic streams and one model?"), GREEN, GREEN_DARK),
        ],
        columns=2,
        footer="A controlled benchmark supports a narrow causal claim; product usefulness requires later external evidence.",
    )


def outcome_labels() -> None:
    card_grid(
        "outcome-labels.png",
        "The verdict communicates both benefit and safety",
        "Falsifiability",
        [
            CardSpec("Supported", ("Primary effect passes", "Every guardrail passes"), GREEN, GREEN_DARK),
            CardSpec("Partially supported", ("Some mechanisms work", "Full claim does not"), BLUE, BLUE_DARK),
            CardSpec("Not supported", ("Primary effect fails", "or simpler method matches"), AMBER, AMBER_DARK),
            CardSpec("Unsafe", ("Any immutable", "governance gate fails"), RED, RED_DARK),
        ],
        columns=4,
        footer="The paper reports the assigned label; it does not narratively upgrade a near miss.",
    )


def research_roadmap() -> None:
    fig = Figure("The roadmap is gated evidence, not a feature queue", "Research and implementation plan")
    phases = [
        ("0", "Freeze contract", "current", GREEN, GREEN_DARK),
        ("1", "Build benchmark", "current", GREEN, GREEN_DARK),
        ("2", "Deterministic core", "current", GREEN, GREEN_DARK),
        ("3", "Model-assisted", "next", BLUE, BLUE_DARK),
        ("4", "Confirmatory study", "gated", PURPLE, PURPLE_DARK),
        ("5", "Persistence", "later", GRAY, GRAY_DARK),
        ("6", "External validity", "later", GRAY, GRAY_DARK),
        ("7", "Self-scaffolding", "only if core wins", AMBER, AMBER_DARK),
    ]
    for i, (number, label, status, fill, accent) in enumerate(phases):
        row, col = divmod(i, 4)
        x1 = 48 + col * 278
        y1 = 158 + row * 162
        fig.card((x1, y1, x1 + 250, y1 + 132), CardSpec(label, (status,), fill, accent), title_size=17, body_size=12, number=number)
        if col < 3:
            fig.arrow((x1 + 254, y1 + 66), (x1 + 274, y1 + 66), accent, 2)
        elif row == 0:
            fig.arrow((x1 + 125, y1 + 136), (x1 + 125, y1 + 158), accent, 2)
    fig.footer("Each phase ships a reproducible artifact and an exit report before the next authority is granted.")
    fig.save("research-roadmap.png")


def memory_semantics() -> None:
    card_grid(
        "memory-semantics.png",
        "Different memory types need different authority and lifecycles",
        "Expanded ELL semantics",
        [
            CardSpec("Source", ("immutable artifact",), GRAY, GRAY_DARK),
            CardSpec("Working", ("expiring task state",), BLUE, BLUE_DARK),
            CardSpec("Episodic", ("bounded experience",), BLUE, BLUE_DARK),
            CardSpec("Semantic", ("temporal assertion",), PURPLE, PURPLE_DARK),
            CardSpec("Preference", ("scoped choice",), AMBER, AMBER_DARK),
            CardSpec("Procedural", ("versioned workflow",), GREEN, GREEN_DARK),
            CardSpec("Prospective", ("future commitment",), AMBER, AMBER_DARK),
            CardSpec("Relational", ("evidence-backed edge",), BLUE, BLUE_DARK),
            CardSpec("Reflective", ("uncertainty + gaps",), PURPLE, PURPLE_DARK),
            CardSpec("Policy", ("consent + retention",), RED, RED_DARK),
        ],
        columns=5,
        footer="Shared infrastructure is acceptable; flattened semantics and identical retrieval rules are not.",
    )


def source_event_episode() -> None:
    fig = Figure("Connectors normalise into stable sources, events, and bounded episodes", "Capture boundary")
    sources = ["chat", "tool trace", "document", "calendar"]
    for i, label in enumerate(sources):
        fig.pill((44, 160 + i * 80, 250, 208 + i * 80), label, GRAY, GRAY_DARK)
        fig.arrow((256, 184 + i * 80), (342, 300), LINE, 2)
    fig.card((350, 170, 590, 430), CardSpec("Source artifact", ("identity", "checksum", "consent", "stable spans"), BLUE, BLUE_DARK), title_size=20, body_size=14)
    fig.arrow((598, 300), (688, 300), BLUE_DARK, 3)
    fig.card((700, 150, 930, 450), CardSpec("Experience events", ("messages", "actions", "observations", "feedback", "external events"), AMBER, AMBER_DARK), title_size=20, body_size=14)
    fig.arrow((938, 300), (1000, 300), AMBER_DARK, 3)
    fig.card((1010, 190, 1156, 410), CardSpec("Episode", ("time-bounded", "context + outcome"), PURPLE, PURPLE_DARK), title_size=18, body_size=13)
    fig.footer("Deterministic identifiers make ingestion rerunnable without leaking provider schemas into ELL-Core.")
    fig.save("source-event-episode.png")


def artifact_status() -> None:
    fig = Figure("The repository proves contracts and deterministic slices - not the hypotheses", "Research artifact status")
    phases = [
        ("Phase 0", "contract + schemas", "implemented", GREEN, GREEN_DARK),
        ("Phase 1", "streams + baselines", "implemented", GREEN, GREEN_DARK),
        ("Phase 2", "deterministic ELL-Core", "implemented", GREEN, GREEN_DARK),
        ("Phase 3", "model-assisted learning", "not yet", BLUE, BLUE_DARK),
        ("Phase 4", "confirmatory verdict", "blocked", AMBER, AMBER_DARK),
        ("Phase 5-6", "substrates + external", "support code only", GRAY, GRAY_DARK),
        ("Phase 7", "self-scaffolding", "specification only", RED, RED_DARK),
        ("Claim status", "H1-H7", "no empirical result", RED, RED_DARK),
    ]
    for i, (phase, body, status, fill, accent) in enumerate(phases):
        row, col = divmod(i, 4)
        x1 = 44 + col * 278
        y1 = 154 + row * 174
        fig.card((x1, y1, x1 + 254, y1 + 146), CardSpec(phase, (body, status), fill, accent), title_size=17, body_size=12)
    fig.footer("Passing tests establish implementation integrity; only the sealed study can establish the research claim.")
    fig.save("artifact-status.png")


def remaining_gates() -> None:
    horizontal_flow(
        "remaining-gates.png",
        "The next evidence must arrive in a fixed order",
        "Remaining research gates",
        [
            CardSpec("Reproduce", ("immutable release", "two clean machines"), GRAY, GRAY_DARK),
            CardSpec("Broaden tests", ("generated properties", "adversarial suite"), BLUE, BLUE_DARK),
            CardSpec("Add models", ("two open families", "quarantine outputs"), AMBER, AMBER_DARK),
            CardSpec("Run sealed study", ("matched receipts", "all gates"), PURPLE, PURPLE_DARK),
            CardSpec("Then expand", ("persistence", "external pilot", "self-scaffolding"), GREEN, GREEN_DARK),
        ],
        footer="Support code for later phases does not bypass an unmet earlier gate.",
    )


def north_star() -> None:
    fig = Figure("The north star is evolving intuition under user control", "Conclusion")
    fig.rounded((400, 180, 800, 420), 30, PURPLE, PURPLE_DARK, 2)
    fig.text((600, 240), "EVOLVING INTUITION", 22, PURPLE_DARK, bold=True, anchor="ma")
    fig.text((600, 302), "economical context", 17, INK, bold=True, anchor="ma")
    fig.text((600, 338), "that improves future behaviour", 17, INK, bold=True, anchor="ma")
    fig.text((600, 382), "and remains open to correction", 13, MUTED, anchor="ma")
    items = [
        ("Grounded", 170, 180, BLUE, BLUE_DARK),
        ("Timely", 170, 300, GREEN, GREEN_DARK),
        ("Sensitive to change", 170, 420, AMBER, AMBER_DARK),
        ("Scoped", 1030, 180, BLUE, BLUE_DARK),
        ("Explainable", 1030, 300, PURPLE, PURPLE_DARK),
        ("User-controlled", 1030, 420, RED, RED_DARK),
    ]
    for label, x, y, fill, accent in items:
        fig.pill((x - 130, y - 25, x + 130, y + 25), label, fill, accent)
        start = (x + 135, y) if x < 600 else (x - 135, y)
        end = (394, min(max(y, 210), 390)) if x < 600 else (806, min(max(y, 210), 390))
        fig.arrow(start, end, accent, 2)
    fig.footer("If a simpler method matches ELL at lower cost, the evidence requires adopting the simpler method.")
    fig.save("north-star.png")


def main() -> None:
    generators: tuple[Callable[[], None], ...] = (
        memory_vs_learning,
        intuition_packet,
        useful_concept,
        failure_modes,
        claim_hierarchy,
        research_landscape,
        empirical_cautions,
        learning_spectrum,
        policy_boundary,
        evidence_ledger,
        association_reflection,
        concept_anatomy,
        fast_slow_loops,
        algorithm_loop,
        confidence_evidence,
        revision_paths,
        retrieval_invalidation,
        entity_ledger,
        concept_states,
        api_boundary,
        evaluation_stages,
        simulation_lab,
        baseline_lanes,
        metrics_dashboard,
        ablation_grid,
        analysis_plan,
        reproducibility_chain,
        private_boundary,
        privacy_cascade,
        threat_controls,
        validity_map,
        outcome_labels,
        research_roadmap,
        memory_semantics,
        source_event_episode,
        artifact_status,
        remaining_gates,
        north_star,
    )
    for generator in generators:
        generator()
    print(f"Generated {len(generators)} paper visuals in {OUT}")


if __name__ == "__main__":
    main()
