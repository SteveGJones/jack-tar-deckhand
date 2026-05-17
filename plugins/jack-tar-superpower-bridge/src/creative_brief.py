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

# Issue #93 — fine-grained per-deck strap-style override. The persona picks
# when this is None (the historical default); the speaker pins it explicitly
# when they want a specific register. Two values:
#   - "all-caps-three-beat" — short uppercase straps in a three-beat cadence
#     (e.g. "BIG. BOLD. CLEAR."). Best for conference keynotes with a strong
#     visual identity.
#   - "prose-sentence" — full sentence-case prose straps (e.g. "The growth
#     plan we already validated"). Best for QBRs, engineering updates, and
#     other internal / formal registers.
# Cluster B overlap: the #87 ``editorial-mixed-case`` register declares a
# default ``strap_style: prose-sentence``; #93's per-deck field overrides
# the register's default when both are set. See plan §2.2.
VALID_STRAP_STYLES = {"all-caps-three-beat", "prose-sentence"}

# Issue #87 — register presets. The set is duplicated here (rather than
# imported from src.registers) to avoid a circular import: creative_brief
# is a leaf module that the registers package depends on for VALID_STRAP_STYLES
# semantics. The single source of truth lives in
# :data:`src.registers.loader.KNOWN_REGISTERS`; the tests assert these stay
# in sync.
VALID_REGISTERS = {
    "infographic-narrative",
    "atmospheric-photo",
    "schematic-diagram",
    "editorial-mixed-case",
}


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
    # Issue #93 — optional strap-style preference. None = persona chooses.
    strap_style: str | None = None
    # Issue #87 — optional register preset name. When set, the persona uses
    # the preset's palette / typography / layout / strap_style as defaults
    # which per-deck fields may override.
    register: str | None = None

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
        if self.strap_style is not None and self.strap_style not in VALID_STRAP_STYLES:
            raise CreativeBriefValidationError(
                f"strap_style {self.strap_style!r} not in {VALID_STRAP_STYLES} "
                f"(or None to defer to the persona)"
            )
        if self.register is not None and self.register not in VALID_REGISTERS:
            raise CreativeBriefValidationError(
                f"register {self.register!r} not in {VALID_REGISTERS} "
                f"(or None to defer to the persona)"
            )

    def to_markdown(self) -> str:
        # Issue #93 — emit Strap style line only when explicitly set; absence
        # signals "persona chooses" so we don't bake an artificial default into
        # the saved markdown.
        strap_line = (
            f"Strap style: {self.strap_style}\n" if self.strap_style else ""
        )
        # Issue #87 — emit Register line only when explicitly set; same rule
        # as strap_style.
        register_line = (
            f"Register: {self.register}\n" if self.register else ""
        )
        return (
            f"# Creative Brief\n\n"
            f"Topic: {self.topic}\n"
            f"Audience: {self.audience}\n"
            f"Duration: {self.duration_minutes} min\n"
            f"Confidentiality: {self.confidentiality}\n"
            f"Budget cap: ${self.budget_cap_usd:.2f}\n"
            f"{register_line}"
            f"{strap_line}"
            f"\n"
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
# Issue #93 — optional per-deck strap_style line. Searched independently
# of the strict header regex so legacy briefs (no Strap style line) parse
# unchanged.
_STRAP_STYLE_RE = re.compile(
    rf"^{_BOLD}Strap style:{_BOLD}\s+(?P<strap_style>all-caps-three-beat|prose-sentence)\s*$",
    re.MULTILINE,
)
# Issue #87 — optional Register line, same scoping rule.
_REGISTER_RE = re.compile(
    rf"^{_BOLD}Register:{_BOLD}\s+(?P<register>infographic-narrative|atmospheric-photo|schematic-diagram|editorial-mixed-case)\s*$",
    re.MULTILINE,
)
_ARC_RE = re.compile(rf"^{_BOLD}Arc:{_BOLD}\s+(?P<arc>.+?)$", re.MULTILINE)
_TAKEAWAY_RE = re.compile(rf"^{_BOLD}Audience takeaway:{_BOLD}\s+(?P<takeaway>.+?)$", re.MULTILINE)
_TONE_RE = re.compile(rf"^{_BOLD}Tone:{_BOLD}\s+(?P<tone>.+?)$", re.MULTILINE)
_VISUAL_RE = re.compile(rf"^{_BOLD}Visual personality:{_BOLD}\s+(?P<vp>.+?)$", re.MULTILINE)

# Capture multi-line Visual personality content (prose + optional palette
# tables, typography blocks, etc.) — everything from the `**Visual
# personality:**` label to the next `##` section header. Used for round-trip
# preservation (Finding #11 fix from Run 3 dogfood) so the palette table
# survives parse → write canonicalisation.
_VISUAL_BLOCK_RE = re.compile(
    rf"^{_BOLD}Visual personality:{_BOLD}\s+(?P<vp>.+?)(?=^## )",
    re.MULTILINE | re.DOTALL,
)


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

    # Prefer the multi-line block capture so palette tables and other
    # structured content following the prose paragraph round-trip cleanly.
    # Fall back to the single-line capture if the block regex doesn't match
    # (e.g. very short briefs with no following content).
    visual_block = _VISUAL_BLOCK_RE.search(text)
    visual_personality_value = (
        visual_block.group("vp").rstrip() if visual_block
        else visual.group("vp").strip()
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

    # Issue #93 / #87 — optional strap_style and register fields. Search only
    # the header region (text up to Section A) to avoid false-positive matches
    # inside Section A/B/C narrative prose.
    header_end = text.index("## Section A — Narrative Architecture")
    strap_match = _STRAP_STYLE_RE.search(text[:header_end])
    strap_style = strap_match.group("strap_style") if strap_match else None
    register_match = _REGISTER_RE.search(text[:header_end])
    register = register_match.group("register") if register_match else None

    return CreativeBrief(
        topic=header.group("topic").strip(),
        audience=header.group("audience").strip(),
        duration_minutes=int(header.group("duration")),
        narrative_arc=arc_match.group("arc").strip(),
        narrative_detail=detail,
        audience_takeaway=takeaway.group("takeaway").strip(),
        tone=tone.group("tone").strip(),
        visual_personality=visual_personality_value,
        placeholder_instructions=placeholder_instructions,
        confidentiality=header.group("confidentiality"),
        budget_cap_usd=float(header.group("budget")),
        strap_style=strap_style,
        register=register,
    )


# ---------------------------------------------------------------------------
# Run 6 Findings #19/#20 — expected_text_content extractor
# ---------------------------------------------------------------------------
#
# The narrative-brief-architect agent writes a Section C subject brief like
#
#     > Schematic integration diagram. Two ox-blood blocks side by side.
#     >
#     > EXACT spelled labels REQUIRED:
#     > - block-left: "Our Platform"
#     > - block-right: "Tessera Edge Stack"
#
# for every text-bearing IMAGE marker. The /enrich-deck SKILL.md calls
# ``extract_expected_text_for_marker`` to lift the quoted strings out
# deterministically and pass them on to the image-reviewer agent. Without
# this list the reviewer (Haiku) confabulates spelling correctness — Run 6
# slide 4 shipped "INFORENCE" because Phase A review said "Text spelling
# correct across all elements" with no comparison reference (Finding #19).
# With the list, Run 6 caught every misspelling on slides 7/8/9 (Finding #20).

# Markers that prefix a Section C reference. The marker grammar is owned by
# ``placeholder.py``; this regex deliberately matches the same prefixes so
# new kinds added there flow through here without changes.
_MARKER_KIND_RE = r"(?:IMAGE|SMARTART-FROM-LIST|SMARTART|BG)"
_MARKER_REF_RE = re.compile(rf"\b{_MARKER_KIND_RE}:[a-z0-9_-]+")

# A bullet line of the form ``- role: "exact text"`` (with optional `>`
# blockquote prefix). The double-quoted text is the expected string; the
# role label before the colon is descriptive and discarded.
_LABEL_BULLET_RE = re.compile(
    r"""^\s*>?\s*-\s+         # leading bullet, optional blockquote prefix
        [^:"]+:\s*            # role label up to its trailing colon
        "(?P<text>[^"]+)"     # exact text in double quotes
        \s*$""",
    re.VERBOSE,
)

_EXACT_HEADER_RE = re.compile(
    r"^\s*>?\s*EXACT\s+spelled\s+labels\s+REQUIRED\s*:\s*$",
    re.IGNORECASE,
)


def extract_expected_text_for_marker(brief_text: str, marker_id: str) -> list[str]:
    """Return the EXACT spelled labels for ``marker_id`` from a brief's Section C.

    Searches ONLY Section C (so example EXACT blocks quoted in Section A as
    narrative cannot leak through as false positives). Within Section C, finds
    the first reference to ``marker_id`` and walks forward looking for an
    ``EXACT spelled labels REQUIRED:`` header. If found, captures the
    double-quoted text from each subsequent ``- role: "text"`` bullet line and
    stops at the next marker reference, the next ``## ``-level heading, or the
    end of the brief.

    Returns an empty list when:
      - the brief has no Section C heading
      - the marker_id is not referenced in Section C
      - the marker is referenced but no EXACT header follows it before the
        next marker / heading / EOF (atmospheric subjects, decorative BG, etc.)

    Empty-list returns are intentional — the SKILL.md uses them to decide
    whether to inject ``expected_text_content`` into the reviewer dispatch.
    Markers without text content should not include it.
    """
    section_c_marker = "## Section C — Placeholder Instructions"
    c_start = brief_text.find(section_c_marker)
    if c_start < 0:
        return []
    section_c = brief_text[c_start:]

    marker_re = re.compile(re.escape(marker_id))
    first_ref = marker_re.search(section_c)
    if first_ref is None:
        return []

    after_ref = section_c[first_ref.end():]

    # Find the next marker reference OR the next ## heading — that's the
    # boundary for THIS marker's block.
    next_marker = _MARKER_REF_RE.search(after_ref)
    next_heading = re.search(r"^## ", after_ref, re.MULTILINE)

    boundary_candidates = [m.start() for m in (next_marker, next_heading) if m is not None]
    boundary = min(boundary_candidates) if boundary_candidates else len(after_ref)
    block = after_ref[:boundary]

    # Look for the EXACT header inside the marker's block.
    lines = block.splitlines()
    label_lines: list[str] = []
    in_label_section = False
    for line in lines:
        if _EXACT_HEADER_RE.match(line):
            in_label_section = True
            continue
        if not in_label_section:
            continue
        bullet = _LABEL_BULLET_RE.match(line)
        if bullet:
            label_lines.append(bullet.group("text"))
            continue
        # A non-bullet, non-blank line ends the label section. Allow blank
        # lines (blockquote spacers, trailing whitespace) to pass through.
        if line.strip() in ("", ">"):
            continue
        break

    return label_lines


# ---------------------------------------------------------------------------
# Brief-save lint (v0.2 #25)
# ---------------------------------------------------------------------------
#
# Run 7 + Run 8 both shipped briefs whose Section C had EXACT-labels blocks
# that the bridge's extractor couldn't parse — usually because operators
# flattened the persona's canonical ``- role: "exact text"`` format into
# plain bullets ``- exact text`` during brief assembly. The brief saved
# successfully, /enrich-deck dispatched the image-reviewer WITHOUT the
# expected-text comparison block, and Haiku confabulated correctness on
# misspelled images. Silent regression of Findings #19/#20.
#
# The lint runs at brief-save time. It enumerates the IMAGE markers
# referenced in Section C and asserts every one of them has at least one
# EXACT-labels entry — UNLESS the marker's subject brief explicitly
# declares it atmospheric. The atmospheric opt-out keeps the lint useful:
# vignette / BG / decorative markers don't need expected text, and the
# lint must not false-positive them.
#
# Atmospheric opt-out signal: any of the words {"atmospheric", "vignette",
# "no specific text", "no text content", "no text"} appearing in the
# marker's block in Section C. The persona's R3b output already uses
# this language for atmospheric markers; the lint just reads it back.
#
# Issue #56 extension (Finding #4, Run 1 dogfood):
# SMARTART-FROM-LIST marker body text that contains an inline-separated
# list (3+ occurrences of · / • / |) is flagged as a soft warning. The
# bridge can recover via downstream splitting, but bullet-line format is
# the preferred contract. The check is a soft warning only — the lint
# still returns a list (not an exception), and SKILL.md decides whether
# to surface it as a halt or a note. This matches the non-throwing
# pattern of the rest of the lint surface.
#
# Inline-separator detection mirrors the threshold in
# ``enrichment_ops.smartart_from_list._split_inline_separators``:
# 3+ occurrences of the same separator in a single line of Section C.
_INLINE_SEP_CANDIDATES: list[str] = ["·", " • ", " | "]
_INLINE_SEP_THRESHOLD = 3


def _detect_inline_separator_in_line(line: str) -> str | None:
    """Return the first inline separator found ≥3 times in ``line``,
    or ``None`` if no dominant separator is present.

    Mirrors the threshold in
    ``enrichment_ops.smartart_from_list._split_inline_separators`` so
    the lint and the extractor agree on what constitutes an inline list.
    Issue #56 (Finding #4, Run 1 dogfood).
    """
    for sep in _INLINE_SEP_CANDIDATES:
        if line.count(sep) >= _INLINE_SEP_THRESHOLD:
            return sep
    return None


class BriefLintError(ValueError):
    """Raised by lint_brief_for_extract_compatibility when a brief's
    Section C has IMAGE markers that the EXACT-labels extractor cannot
    parse AND the marker is not declared atmospheric.

    The error message names every offending marker so the operator can
    locate and fix them in the brief source.
    """


_ATMOSPHERIC_HINTS = (
    "atmospheric",
    "vignette",
    "no specific text",
    "no text content",
    "no text",
    "no exact text",
    "decorative",
    "painterly",
    "no labels",
)


def _marker_is_declared_atmospheric(marker_block: str) -> bool:
    """Return True when the marker's Section C block declares it atmospheric.

    Atmospheric markers don't need EXACT-labels. The lint reads the
    marker's block (between its first reference and the next marker /
    heading / EOF) for any opt-out hint string. Case-insensitive.
    """
    haystack = marker_block.lower()
    return any(hint in haystack for hint in _ATMOSPHERIC_HINTS)


def lint_brief_for_extract_compatibility(brief_text: str) -> list[str]:
    """Validate every text-bearing IMAGE marker in Section C has an
    EXACT-labels block the extractor can parse. Returns a list of error
    messages — one per offending marker. Empty list means the brief is
    clean.

    The lint is intentionally narrow: it only checks IMAGE markers (BG
    and SMARTART-FROM-LIST markers don't carry EXACT-labels in the same
    way). It runs ONLY against Section C (atmospheric example blocks in
    Section A as narrative don't trigger false positives).

    Operator workflow:
      1. /bridge-brief produces a draft brief.
      2. ``write_brief_markdown`` saves the draft to disk.
      3. ``lint_brief_for_extract_compatibility`` runs against the saved
         text. If it returns an empty list, the brief is good. If it
         returns errors, the SKILL.md surfaces them and asks the operator
         to fix the brief before invoking /enrich-deck.

    Returns ``[]`` if Section C is missing — a brief without Section C
    has no markers to lint, which is itself caught by ``parse_brief_markdown``.
    """
    section_c_marker = "## Section C — Placeholder Instructions"
    c_start = brief_text.find(section_c_marker)
    if c_start < 0:
        return []
    section_c = brief_text[c_start:]

    # Enumerate every distinct IMAGE marker in Section C (preserve order
    # of first appearance for deterministic error messages).
    seen: list[str] = []
    seen_set: set[str] = set()
    image_marker_re = re.compile(r"\bIMAGE:[a-z0-9_-]+")
    for match in image_marker_re.finditer(section_c):
        marker_id = match.group(0)
        if marker_id not in seen_set:
            seen.append(marker_id)
            seen_set.add(marker_id)

    errors: list[str] = []
    for marker_id in seen:
        labels = extract_expected_text_for_marker(brief_text, marker_id)
        if labels:
            continue  # has at least one EXACT label — passes lint
        # No EXACT-labels found. Check whether the marker's block
        # declares itself atmospheric.
        first_ref = re.search(re.escape(marker_id), section_c)
        if first_ref is None:
            continue  # shouldn't happen — we just enumerated this marker
        after_ref = section_c[first_ref.end():]
        next_marker = _MARKER_REF_RE.search(after_ref)
        next_heading = re.search(r"^## ", after_ref, re.MULTILINE)
        boundary_candidates = [
            m.start() for m in (next_marker, next_heading) if m is not None
        ]
        boundary = min(boundary_candidates) if boundary_candidates else len(after_ref)
        marker_block = after_ref[:boundary]

        if _marker_is_declared_atmospheric(marker_block):
            continue  # atmospheric opt-out — no EXACT-labels needed

        errors.append(
            f"{marker_id}: no EXACT-labels block found in Section C. "
            f"If this marker carries text content (wordmark, caption, "
            f"named labels), add an `EXACT spelled labels REQUIRED:` "
            f"blockquote with `- role: \"exact text\"` bullets. "
            f"If this marker is atmospheric (no text content), say so "
            f"in the subject brief (use words like \"atmospheric\", "
            f"\"vignette\", or \"no text\") to opt out of the lint."
        )

    # Issue #56 (Finding #4, Run 1 dogfood) — soft-warn on inline-separator
    # lists in SMARTART-FROM-LIST marker body text. The bridge can recover
    # via downstream splitting, but bullet-line format is preferred.
    # We scan every line of Section C that doesn't look like a heading,
    # codeblock, or marker-name line for inline-list patterns (3+ separators).
    smartart_list_marker_re = re.compile(r"\bSMARTART-FROM-LIST:[a-z0-9_-]+")
    current_smartart_marker: str | None = None
    in_code_block = False
    for line in section_c.splitlines():
        # Track fenced code blocks — don't lint inside them
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        # Detect entering a new SMARTART-FROM-LIST marker reference
        sm_match = smartart_list_marker_re.search(line)
        if sm_match:
            current_smartart_marker = sm_match.group(0)
            continue
        # Detect entering any other marker kind — stop attributing to last
        # SMARTART-FROM-LIST marker
        if _MARKER_REF_RE.search(line) and current_smartart_marker:
            if not smartart_list_marker_re.search(line):
                current_smartart_marker = None
            continue
        # Only warn while we're inside a SMARTART-FROM-LIST block
        if current_smartart_marker is None:
            continue
        sep = _detect_inline_separator_in_line(line)
        if sep is not None:
            errors.append(
                f"{current_smartart_marker}: Section C contains an inline "
                f"separator-separated list (separator: {sep!r}, "
                f"≥{_INLINE_SEP_THRESHOLD} occurrences). "
                f"SMARTART-FROM-LIST content should use bullet-line format "
                f"(one item per line) rather than inline-separated lists. "
                f"The bridge will attempt to split at render time, but "
                f"bullet-line format is more reliable."
            )
            current_smartart_marker = None  # warn once per marker block

    return errors
