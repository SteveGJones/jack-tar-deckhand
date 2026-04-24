"""Creative brief — Phase 1 output, Phase 3 input.

The brief carries narrative architecture (arc + pacing), communication
intent (audience takeaway + tone + visual personality), placeholder
instructions for the superpower, and operational settings
(confidentiality tier and budget cap) that gate Phase 3 cloud spend.

The file format is human-readable markdown — the user reads and
edits it before handing it to /pptx. The bridge parses it back when
/enrich-deck runs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

VALID_CONFIDENTIALITY = {"public", "internal", "restricted"}
DEFAULT_BUDGET_CAP_USD = 1.00


class CreativeBriefValidationError(ValueError):
    """Raised when a CreativeBrief fails validation or markdown parsing."""


@dataclass
class CreativeBrief:
    topic: str
    audience: str
    duration_minutes: int
    narrative_arc: str
    narrative_detail: str
    audience_takeaway: str
    tone: str
    visual_personality: str
    placeholder_instructions: str
    confidentiality: str = "public"
    budget_cap_usd: float = DEFAULT_BUDGET_CAP_USD

    def __post_init__(self) -> None:
        if self.confidentiality not in VALID_CONFIDENTIALITY:
            raise CreativeBriefValidationError(
                f"confidentiality {self.confidentiality!r} not in {VALID_CONFIDENTIALITY}"
            )
        if self.duration_minutes <= 0:
            raise CreativeBriefValidationError(
                f"duration_minutes must be positive, got {self.duration_minutes}"
            )
        if self.budget_cap_usd < 0:
            raise CreativeBriefValidationError(
                f"budget_cap_usd must be non-negative, got {self.budget_cap_usd}"
            )

    def to_markdown(self) -> str:
        return (
            f"# Creative Brief\n\n"
            f"Topic: {self.topic}\n"
            f"Audience: {self.audience}\n"
            f"Duration: {self.duration_minutes} min\n"
            f"Confidentiality: {self.confidentiality}\n"
            f"Budget cap: ${self.budget_cap_usd:.2f}\n\n"
            f"## Section A — Narrative Architecture\n\n"
            f"**Arc:** {self.narrative_arc}\n\n"
            f"{self.narrative_detail}\n\n"
            f"## Section B — Communication & Visual Intent\n\n"
            f"**Audience takeaway:** {self.audience_takeaway}\n"
            f"**Tone:** {self.tone}\n"
            f"**Visual personality:** {self.visual_personality}\n\n"
            f"## Section C — Placeholder Instructions\n\n"
            f"{self.placeholder_instructions}\n\n"
            f"### PptxGenJS API note\n\n"
            f"When emitting marker placeholders, use the `objectName` property on "
            f"`addShape()`. PptxGenJS 4.0.1 silently drops the `name` property; "
            f"`objectName` is the only key that survives into OOXML where the bridge "
            f"reads it.\n\n"
            f"```javascript\n"
            f"slide.addShape(pres.shapes.RECTANGLE, {{\n"
            f"  objectName: \"IMAGE:agent-architecture\",  // <-- objectName, not name\n"
            f"  x: 5.5, y: 1.5, w: 4, h: 3,\n"
            f"  fill: {{ color: \"F0F0F0\" }},\n"
            f"  line: {{ color: \"CCCCCC\", width: 1, dashType: \"dash\" }},\n"
            f"}});\n"
            f"slide.addText(\"IMAGE:agent-architecture\", {{\n"
            f"  x: 5.5, y: 2.8, w: 4, h: 0.5,\n"
            f"  align: \"center\", color: \"888888\", fontSize: 14,\n"
            f"}});\n"
            f"```\n"
        )


def write_brief_markdown(brief: CreativeBrief, path: Path | str) -> None:
    Path(path).write_text(brief.to_markdown())


# Accept both plain `Label:` and bold `**Label:**` forms so hand-edited
# briefs stay parseable even if the user re-bolds labels in an editor.
_BOLD = r"(?:\*\*)?"
_HEADER_RE = re.compile(
    rf"^{_BOLD}Topic:{_BOLD}\s+(?P<topic>.+?)\n"
    rf"{_BOLD}Audience:{_BOLD}\s+(?P<audience>.+?)\n"
    rf"{_BOLD}Duration:{_BOLD}\s+(?P<duration>\d+)\s*min\n"
    rf"{_BOLD}Confidentiality:{_BOLD}\s+(?P<confidentiality>public|internal|restricted)\n"
    rf"{_BOLD}Budget cap:{_BOLD}\s+\$(?P<budget>[0-9]+(?:\.[0-9]+)?)",
    re.MULTILINE,
)
_ARC_RE = re.compile(rf"^{_BOLD}Arc:{_BOLD}\s+(?P<arc>.+?)$", re.MULTILINE)
_TAKEAWAY_RE = re.compile(rf"^{_BOLD}Audience takeaway:{_BOLD}\s+(?P<takeaway>.+?)$", re.MULTILINE)
_TONE_RE = re.compile(rf"^{_BOLD}Tone:{_BOLD}\s+(?P<tone>.+?)$", re.MULTILINE)
_VISUAL_RE = re.compile(rf"^{_BOLD}Visual personality:{_BOLD}\s+(?P<vp>.+?)$", re.MULTILINE)


def parse_brief_markdown(text: str) -> CreativeBrief:
    """Parse a creative-brief.md back into a CreativeBrief.

    Strict — missing sections raise CreativeBriefValidationError.
    Used by /enrich-deck to recover confidentiality + budget_cap from the brief.
    """
    header = _HEADER_RE.search(text)
    if not header:
        raise CreativeBriefValidationError("missing top-of-brief header block")

    if "## Section A — Narrative Architecture" not in text:
        raise CreativeBriefValidationError("missing Section A heading")
    if "## Section B — Communication & Visual Intent" not in text:
        raise CreativeBriefValidationError("missing Section B heading")
    if "## Section C — Placeholder Instructions" not in text:
        raise CreativeBriefValidationError("missing Section C heading")

    arc_match = _ARC_RE.search(text)
    takeaway = _TAKEAWAY_RE.search(text)
    tone = _TONE_RE.search(text)
    visual = _VISUAL_RE.search(text)
    if not all([arc_match, takeaway, tone, visual]):
        raise CreativeBriefValidationError(
            "one of Arc/Audience takeaway/Tone/Visual personality is missing"
        )

    # Section A narrative_detail = text between Arc line and Section B heading
    a_start = text.index("## Section A — Narrative Architecture")
    b_start = text.index("## Section B — Communication & Visual Intent")
    section_a = text[a_start:b_start]
    arc_line = arc_match.group(0)
    detail = section_a.split(arc_line, 1)[1].strip()

    # Section C placeholder_instructions = text between Section C heading and the
    # PptxGenJS API note (or end of file)
    c_start = text.index("## Section C — Placeholder Instructions")
    pptxgenjs_note_pos = text.find("### PptxGenJS API note", c_start)
    c_end = pptxgenjs_note_pos if pptxgenjs_note_pos >= 0 else len(text)
    section_c = text[c_start:c_end]
    placeholder_instructions = section_c.split("\n", 1)[1].strip()

    return CreativeBrief(
        topic=header.group("topic").strip(),
        audience=header.group("audience").strip(),
        duration_minutes=int(header.group("duration")),
        narrative_arc=arc_match.group("arc").strip(),
        narrative_detail=detail,
        audience_takeaway=takeaway.group("takeaway").strip(),
        tone=tone.group("tone").strip(),
        visual_personality=visual.group("vp").strip(),
        placeholder_instructions=placeholder_instructions,
        confidentiality=header.group("confidentiality"),
        budget_cap_usd=float(header.group("budget")),
    )
