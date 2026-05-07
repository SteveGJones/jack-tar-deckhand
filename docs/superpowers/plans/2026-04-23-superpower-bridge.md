# Superpower Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `jack-tar-superpower-bridge` plugin that wraps around `document-skills:pptx` with a narrative pre-brief skill (`/bridge-brief`) and a post-hoc visual enrichment skill (`/enrich-deck`), implementing every requirement from the [2026-04-22 design spec](../specs/2026-04-22-superpower-bridge-design.md) and resolving the seven implementation-plan caveats from the final critical review.

**Architecture:** Three-phase workflow — (1) `/bridge-brief` produces `creative-brief.md` via the new Narrative Brief Architect persona; (2) the user invokes `/pptx` independently; (3) `/enrich-deck` analyses the .pptx output via OOXML (with esprima JS-AST fallback for marker recovery), proposes enrichments to the user, applies AI backgrounds + element images + editable SmartArt transactionally to a copy of the deck, runs an Enrichment Cohesion Review, and delivers `presentation-enriched.pptx` plus a structured `enrichment-report.md`. The bridge never modifies `/pptx` and never modifies the original `.pptx`. SmartArt rendering reuses `jack-tar-msft-smartart`; image generation reuses `jack-tar-deckhand:imagegen-bridge`.

**Tech Stack:** Python 3.10+; `python-pptx` 1.0.2 (OOXML primary); `lxml` 4.9+ (hardened XML parser); `esprima` 4.0.1+ (JS AST fallback, parse-only never execute); `pytest` for unit + cross-plugin integration tests; existing `jack-tar-msft-smartart` engine + `assembler_patch.inject` for SmartArt; existing `jack-tar-deckhand:imagegen-bridge` skill for image generation; new agents (Narrative Brief Architect, Enrichment Cohesion Reviewer) defined as `.md` agent definitions following the existing image-reviewer / prompt-engineer pattern.

---

## Caveat Tracker

The seven caveats from the final critical review are mapped to specific tasks below. None is deferred. (This tracker is the source of truth — the same matrix is repeated at the bottom of the plan with deliverable detail.)

| # | Caveat | Resolved by |
|---|--------|-------------|
| 1 | Image-path allowlist extension mechanism | Tasks 4 (security primitives), 19 + 20 (ops resolve through allowlist), 26 (skill provides defaults) |
| 2 | Cohesion Reviewer verdict → auto-regen decision table | Tasks 23 (persona enumerates verdicts), 24 (`decide_action` decision table), 26 (skill Step 10 acts on AutoAction kinds) |
| 3 | Measurement instrumentation as P0 | Tasks 13 (`measurement.py` lands alongside Phase 3), 12 + 26 (skills record runs), 16 (cycle records cost events) |
| 4 | smartart-extractor reuse vs. bridge-side re-parsing decision | Task 18 (decision: bridge-side; rationale in module docstring) |
| 5 | `.bsa/models/jack-tar-deckhand.json` v1.5.0 canonical delta | Tasks 28 (model edits + schema check) + 29 (persona doc bump) |
| 6 | Budget cap covers image review (not just generation) | Tasks 14 (`BudgetCap.charge(kind=...)`), 16 (cycle charges review unconditionally in every phase) |
| 7 | Three-phase UX dogfooding gate | Tasks 32 (restart) + 33 (Phase 1) + 34 (Phase 3) + 35 (verdict + scorecard flip) |

---

## File Structure

```
plugins/jack-tar-superpower-bridge/
  .claude-plugin/
    plugin.json                  # name, version, description, dependencies note
  CLAUDE.md                      # plugin-scoped CLAUDE.md (mirrors deckhand pattern)
  requirements.txt               # python-pptx, lxml, esprima, jsonschema, pytest
  skills/
    bridge-brief/
      SKILL.md                   # Phase 1: collaborative narrative pre-brief
    enrich-deck/
      SKILL.md                   # Phase 3: analyse → menu → assets → assemble → review → deliver
    verify/
      SKILL.md                   # Plugin readiness check
  agents/
    narrative-brief-architect.md     # Persona 1 (Sonnet, Tier 1)
    enrichment-cohesion-reviewer.md  # Persona 2 (Haiku, Sonnet escalate)
  src/
    __init__.py
    creative_brief.py            # CreativeBrief dataclass + read/write helpers
    slide_facts.py               # SlideFacts + Marker + EnrichmentChoice + AnalyserResult dataclasses
    placeholder.py               # MARKER_RE, validation, marker manipulation helpers
    security.py                  # Image-path allowlist, .pptx pre-flight, hardened XML parser
    msft_smartart_loader.py      # PLUGIN_ROOT discovery + safe import of msft-smartart
    analyser/
      __init__.py                # analyse_pptx() orchestrator (HYBRID OOXML + JS fallback)
      pptx_parser.py             # OOXML parsing (markers, geometry, text, bgColor, element types)
      js_parser.py               # esprima AST parser, marker extraction only, parse-never-execute
      overlap_verifier.py        # SMARTART marker-adjacent text overlap detection
    enrichment_ops/
      __init__.py
      background.py              # Op1 — apply AI background + remove BG marker
      element_image.py           # Op2 — replace IMAGE marker with embedded picture
      smartart.py                # Op3 — graft SmartArt carrier via msft_smartart inject
    enrichment.py                # Transactional orchestrator (in-memory accumulator + try/finally)
    image_bridge.py              # Draft/review cycle wrapper, budget tracker, privacy tier enforcement
    smartart_bridge.py           # Marker → SmartArt spec + carrier render
    cohesion_review.py           # Slide rasterisation + Enrichment Cohesion Reviewer dispatch + decision table
    enrichment_report.py         # Structured enrichment-report.md writer
    measurement.py               # 5-hook metrics emitter for both personas
  tests/
    __init__.py
    conftest.py                  # PLUGIN_ROOT fixtures + spike-fixture access
    test_security.py
    test_creative_brief.py
    test_placeholder.py
    test_msft_smartart_loader.py
    test_analyser_pptx_parser.py
    test_analyser_js_parser.py
    test_analyser_overlap_verifier.py
    test_analyser_orchestrator.py
    test_image_bridge.py
    test_smartart_bridge.py
    test_enrichment_ops_background.py
    test_enrichment_ops_element_image.py
    test_enrichment_ops_smartart.py
    test_enrichment_transactional.py
    test_cohesion_review.py
    test_enrichment_report.py
    test_measurement.py
    fixtures/
      seed_variant_a.pptx        # Spike 1 Variant A (real /pptx, objectName markers)
      seed_variant_b.pptx        # Spike 1 Variant B (name: dropped — JS-fallback test)
      seed_variant_a_build.js    # Variant A build script
      seed_variant_b_build.js    # Variant B build script
      seed_no_buildjs.pptx       # Control case (python-pptx-built, no build.js)
      placeholder.png            # Stand-in image for op1/op2 tests
  docs/
    personas.md                  # Extended persona contracts (forward of plugin docs)
    dogfooding/
      2026-04-23-bridge-dogfood-run-1.md   # First dogfood run results
plugins/integration_tests/
  test_superpower_bridge_skill_discovery.py
  test_superpower_bridge_plugin_root.py
  test_superpower_bridge_msft_smartart_import.py
  test_superpower_bridge_end_to_end.py
.bsa/models/
  jack-tar-deckhand.json         # bumped to v1.5.0 with Bridge Services L1
.claude-plugin/
  marketplace.json               # bumped to v1.2.0 across plugins; new bridge entry
docs/architecture/
  ai-personas/
    superpower-bridge-personas.md  # already exists at v0.1; extended in Phase 13
docs/superpowers/plans/
  2026-04-23-superpower-bridge.md  # this file
```

---

## Phase 0 — Plugin scaffold (1 task)

### Task 1: Create the plugin skeleton

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/.claude-plugin/plugin.json`
- Create: `plugins/jack-tar-superpower-bridge/CLAUDE.md`
- Create: `plugins/jack-tar-superpower-bridge/requirements.txt`
- Create: `plugins/jack-tar-superpower-bridge/src/__init__.py`
- Create: `plugins/jack-tar-superpower-bridge/tests/__init__.py`
- Create: `plugins/jack-tar-superpower-bridge/tests/conftest.py`
- Create: `plugins/jack-tar-superpower-bridge/tests/fixtures/.gitkeep`

- [ ] **Step 1: Create `plugin.json`**

```json
{
  "name": "jack-tar-superpower-bridge",
  "description": "Wraps document-skills:pptx with a narrative pre-brief skill and a post-hoc visual enrichment skill — combine /pptx structural strength with jack-tar visual capabilities (AI backgrounds, element images, editable SmartArt)",
  "version": "0.1.0",
  "author": {
    "name": "Steve Jones"
  },
  "repository": "https://github.com/SteveGJones/jack-tar-deckhand",
  "license": "MIT",
  "keywords": ["presentations", "powerpoint", "pptx", "enrichment", "smartart", "superpower"]
}
```

- [ ] **Step 2: Create `CLAUDE.md`**

```markdown
# jack-tar-superpower-bridge

Wraps around the `document-skills:pptx` superpower with a narrative pre-brief skill and a post-hoc visual enrichment skill. The bridge never modifies /pptx and never modifies the original .pptx — it consumes /pptx output and produces a new enriched file.

## Prerequisites

- Python 3.10+ with python-pptx, lxml, esprima, jsonschema
- `document-skills:pptx` (external superpower, install via marketplace)

## Optional engine plugins (auto-detected — install for full capability)

- `jack-tar-deckhand` — provides imagegen-bridge skill for AI image generation, and reuses image-reviewer + prompt-engineer agents
- `jack-tar-msft-smartart` — provides editable PowerPoint SmartArt engine + injection
- `jack-tar-ollama` — local image generation (free Ollama drafts)
- `jack-tar-cloud` — cloud image generation (production tier)

Without engine plugins, only the `/bridge-brief` skill works; `/enrich-deck` will surface a clear "no enrichment engines available" error.

## Skills

| Skill | Purpose |
|-------|---------|
| `/bridge-brief` | Phase 1 — collaborative narrative pre-brief; produces `creative-brief.md` |
| `/enrich-deck` | Phase 3 — analyse a /pptx-produced .pptx, propose enrichments, apply selected enrichments, deliver enriched deck + report |
| `/verify` | Plugin readiness check |

## Quick Start

```
/jack-tar-superpower-bridge:verify
/jack-tar-superpower-bridge:bridge-brief "AI agent architectures, 20 min conference talk for developers"
# user invokes /pptx with the brief, gets presentation.pptx + build.js
/jack-tar-superpower-bridge:enrich-deck presentation.pptx
```

## Specs and personas

- Design spec: `docs/superpowers/specs/2026-04-22-superpower-bridge-design.md`
- AI Persona contracts: `docs/architecture/ai-personas/superpower-bridge-personas.md`
- Implementation plan: `docs/superpowers/plans/2026-04-23-superpower-bridge.md`
```

- [ ] **Step 3: Create `requirements.txt`**

```
python-pptx>=1.0.2
lxml>=4.9.0
esprima>=4.0.1
jsonschema>=4.20.0
pytest>=8.0.0
```

- [ ] **Step 4: Create empty `src/__init__.py`**

`src/__init__.py`:

```python
"""jack-tar-superpower-bridge — narrative pre-brief + post-hoc visual enrichment for /pptx output."""
```

Do NOT create `tests/__init__.py` — sibling plugins (jack-tar-deckhand, jack-tar-msft-smartart, jack-tar-cloud, jack-tar-ollama, jack-tar-custom-smartart) deliberately omit it. Making `tests/` a regular package can shadow the `src` namespace across plugins when CI runs all six test trees in one process.

- [ ] **Step 5: Create `tests/conftest.py`**

```python
"""Shared test fixtures for the superpower-bridge plugin."""
from __future__ import annotations
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PLUGIN_ROOT / "src"
FIXTURE_DIR = PLUGIN_ROOT / "tests" / "fixtures"

# Spikes hold the real /pptx output we use as test seeds. Resolved once.
WORKTREE_ROOT = PLUGIN_ROOT.parents[1]
SPIKE1_DIR = WORKTREE_ROOT / "docs" / "spikes" / "2026-04-23-pptx-marker-adherence"
SPIKE2_DIR = WORKTREE_ROOT / "docs" / "spikes" / "2026-04-23-python-pptx-enrichment"


@pytest.fixture(autouse=True)
def _ensure_plugin_src_on_path():
    """Put the bridge plugin's src on sys.path; clear sibling-plugin src caches."""
    plugin_str = str(PLUGIN_ROOT)
    for key in list(sys.modules):
        if key == "src" or key.startswith("src."):
            del sys.modules[key]
    if plugin_str in sys.path:
        sys.path.remove(plugin_str)
    sys.path.insert(0, plugin_str)
    yield


@pytest.fixture
def seed_variant_a() -> Path:
    """Real /pptx-produced deck with `objectName` markers (Spike 1 Variant A)."""
    return SPIKE1_DIR / "outputs" / "variant-a" / "presentation.pptx"


@pytest.fixture
def seed_variant_a_build() -> Path:
    """Spike 1 Variant A build.js — used for analyser orchestrator JS-fallback tests."""
    return SPIKE1_DIR / "outputs" / "variant-a" / "build.js"


@pytest.fixture
def seed_variant_b() -> Path:
    """Real /pptx-produced deck where `name:` was dropped (Spike 1 Variant B)."""
    return SPIKE1_DIR / "outputs" / "variant-b" / "presentation.pptx"


@pytest.fixture
def seed_variant_b_build() -> Path:
    """Spike 1 Variant B build.js — used for JS-fallback marker-recovery tests."""
    return SPIKE1_DIR / "outputs" / "variant-b" / "build.js"


@pytest.fixture
def seed_no_buildjs() -> Path:
    """Hand-built control deck with one named marker shape and no build.js (Spike 3 control)."""
    return SPIKE2_DIR.parent / "2026-04-23-analyser-source-comparison" / "fixtures" / "control.pptx"


@pytest.fixture
def placeholder_png() -> Path:
    """Stand-in image for background / element-image enrichment tests."""
    return SPIKE2_DIR / "seed" / "placeholder.png"
```

- [ ] **Step 6: Create `tests/fixtures/.gitkeep`** (empty file so the directory persists in git)

- [ ] **Step 7: Verify plugin layout exists**

Run: `find plugins/jack-tar-superpower-bridge -type f | sort`
Expected output (one path per line):
```
plugins/jack-tar-superpower-bridge/.claude-plugin/plugin.json
plugins/jack-tar-superpower-bridge/CLAUDE.md
plugins/jack-tar-superpower-bridge/requirements.txt
plugins/jack-tar-superpower-bridge/src/__init__.py
plugins/jack-tar-superpower-bridge/tests/__init__.py
plugins/jack-tar-superpower-bridge/tests/conftest.py
plugins/jack-tar-superpower-bridge/tests/fixtures/.gitkeep
```

- [ ] **Step 8: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/
git commit -m "feat(bridge): scaffold jack-tar-superpower-bridge plugin"
```

---

## Phase 1 — Shared contracts and security primitives (4 tasks)

### Task 2: SlideFacts + Marker + EnrichmentChoice dataclasses

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/slide_facts.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_slide_facts.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_slide_facts.py`:

```python
import pytest
from src.slide_facts import (
    Marker,
    SlideFacts,
    EnrichmentChoice,
    AnalyserResult,
    OverlapWarning,
)


def test_marker_rejects_unknown_kind():
    with pytest.raises(ValueError, match="invalid kind"):
        Marker(kind="LOGO", identifier="foo", left_emu=0, top_emu=0, width_emu=0, height_emu=0)


def test_marker_roundtrip_dict():
    m = Marker(kind="IMAGE", identifier="agent-architecture", left_emu=1, top_emu=2,
               width_emu=3, height_emu=4)
    d = m.to_dict()
    assert d == {"kind": "IMAGE", "identifier": "agent-architecture",
                 "left_emu": 1, "top_emu": 2, "width_emu": 3, "height_emu": 4}


def test_slide_facts_default_collections():
    sf = SlideFacts(slide_index=1, text_content="")
    assert sf.markers == []
    assert sf.background_kind == "default"
    assert sf.element_types == {}


def test_slide_facts_roundtrip():
    sf = SlideFacts(
        slide_index=3,
        text_content="hello",
        markers=[Marker("BG", "dark", 0, 0, 0, 0)],
        background_kind="image",
        element_types={"text": 1},
    )
    out = SlideFacts.from_dict(sf.to_dict())
    assert out.slide_index == 3
    assert out.markers[0].kind == "BG"
    assert out.background_kind == "image"


def test_enrichment_choice_rejects_unknown_action():
    with pytest.raises(ValueError, match="invalid action"):
        EnrichmentChoice(slide_index=1, kind="background", marker_id="BG:foo",
                         action="float-in-the-air")


def test_enrichment_choice_smartart_overlap_options():
    for action in ("apply", "apply_clear_overlap", "skip"):
        EnrichmentChoice(slide_index=1, kind="smartart", marker_id="SMARTART:foo",
                         action=action)


def test_overlap_warning_holds_intersecting_shape_names():
    w = OverlapWarning(slide_index=4, marker_id="SMARTART:three-pillars",
                       overlapping_shape_names=["Body 1", "Body 2"])
    assert "Body 1" in w.overlapping_shape_names


def test_analyser_result_aggregates_facts_and_warnings():
    sf = SlideFacts(slide_index=1, text_content="x")
    r = AnalyserResult(
        slides=[sf],
        duplicate_marker_ids=["IMAGE:foo"],
        overlap_warnings=[],
        js_fallback_used=False,
        notes=["zero markers found"],
    )
    assert r.total_slides == 1
    assert r.total_markers == 0
    assert r.duplicate_marker_ids == ["IMAGE:foo"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_slide_facts.py -v`
Expected: ImportError / ModuleNotFoundError on `src.slide_facts`.

- [ ] **Step 3: Write the implementation**

`src/slide_facts.py`:

```python
"""Shared dataclasses for the analyser, enrichment menu, and report.

Lifted from Spike 3's `parsers/slide_facts.py` and extended with the
EnrichmentChoice + AnalyserResult + OverlapWarning shapes used by the
production analyser orchestrator and the enrichment menu.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

VALID_MARKER_KINDS = {"IMAGE", "SMARTART", "BG"}
VALID_ENRICHMENT_KINDS = {"background", "image", "smartart"}
VALID_ENRICHMENT_ACTIONS = {"apply", "apply_clear_overlap", "skip"}


@dataclass
class Marker:
    kind: str
    identifier: str
    left_emu: int
    top_emu: int
    width_emu: int
    height_emu: int

    def __post_init__(self) -> None:
        if self.kind not in VALID_MARKER_KINDS:
            raise ValueError(f"invalid kind {self.kind!r}; want one of {VALID_MARKER_KINDS}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SlideFacts:
    slide_index: int                                  # 1-based
    text_content: str
    markers: list[Marker] = field(default_factory=list)
    background_kind: str = "default"                  # default | solid | image | unknown
    element_types: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "slide_index": self.slide_index,
            "text_content": self.text_content,
            "markers": [m.to_dict() for m in self.markers],
            "background_kind": self.background_kind,
            "element_types": dict(self.element_types),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SlideFacts":
        return cls(
            slide_index=d["slide_index"],
            text_content=d["text_content"],
            markers=[Marker(**m) for m in d.get("markers", [])],
            background_kind=d.get("background_kind", "default"),
            element_types=dict(d.get("element_types", {})),
        )


@dataclass
class OverlapWarning:
    slide_index: int
    marker_id: str
    overlapping_shape_names: list[str]


@dataclass
class EnrichmentChoice:
    """A user's selection for a single enrichment opportunity."""
    slide_index: int
    kind: str                          # background | image | smartart
    marker_id: str | None              # None for unmarked-slide suggestions
    action: str = "apply"              # apply | apply_clear_overlap | skip
    notes: str = ""                    # optional user override text

    def __post_init__(self) -> None:
        if self.kind not in VALID_ENRICHMENT_KINDS:
            raise ValueError(f"invalid kind {self.kind!r}; want one of {VALID_ENRICHMENT_KINDS}")
        if self.action not in VALID_ENRICHMENT_ACTIONS:
            raise ValueError(
                f"invalid action {self.action!r}; want one of {VALID_ENRICHMENT_ACTIONS}"
            )


@dataclass
class AnalyserResult:
    slides: list[SlideFacts]
    duplicate_marker_ids: list[str] = field(default_factory=list)
    overlap_warnings: list[OverlapWarning] = field(default_factory=list)
    js_fallback_used: bool = False
    notes: list[str] = field(default_factory=list)

    @property
    def total_slides(self) -> int:
        return len(self.slides)

    @property
    def total_markers(self) -> int:
        return sum(len(s.markers) for s in self.slides)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_slide_facts.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/slide_facts.py plugins/jack-tar-superpower-bridge/tests/test_slide_facts.py
git commit -m "feat(bridge): SlideFacts/Marker/EnrichmentChoice/AnalyserResult dataclasses"
```

---

### Task 3: Marker grammar and helpers (`placeholder.py`)

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/placeholder.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_placeholder.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_placeholder.py`:

```python
import pytest
from src.placeholder import (
    MARKER_RE,
    parse_marker,
    is_marker_name,
    find_duplicate_marker_ids,
)
from src.slide_facts import Marker, SlideFacts


def test_grammar_lowercase_only_after_colon():
    assert MARKER_RE.match("IMAGE:agent-architecture") is not None
    assert MARKER_RE.match("SMARTART:three_pillars") is not None
    assert MARKER_RE.match("BG:dramatic-opening") is not None


def test_grammar_rejects_uppercase_in_identifier():
    assert MARKER_RE.match("IMAGE:AgentArchitecture") is None


def test_grammar_rejects_unknown_prefix():
    assert MARKER_RE.match("LOGO:hero") is None


def test_grammar_rejects_empty_identifier():
    assert MARKER_RE.match("IMAGE:") is None


def test_grammar_rejects_disallowed_chars():
    assert MARKER_RE.match("IMAGE:foo bar") is None
    assert MARKER_RE.match("IMAGE:foo.bar") is None
    assert MARKER_RE.match("IMAGE:foo/bar") is None


def test_parse_marker_returns_kind_and_identifier():
    kind, ident = parse_marker("SMARTART:three-pillars")
    assert kind == "SMARTART"
    assert ident == "three-pillars"


def test_parse_marker_returns_none_on_non_marker():
    assert parse_marker("Body Text 4") is None


def test_is_marker_name_true_false():
    assert is_marker_name("IMAGE:foo") is True
    assert is_marker_name("Title 1") is False


def test_find_duplicate_marker_ids_flags_dupes():
    slides = [
        SlideFacts(slide_index=1, text_content="", markers=[
            Marker("IMAGE", "foo", 0, 0, 0, 0),
        ]),
        SlideFacts(slide_index=3, text_content="", markers=[
            Marker("IMAGE", "foo", 0, 0, 0, 0),
            Marker("BG", "bar", 0, 0, 0, 0),
        ]),
    ]
    dupes = find_duplicate_marker_ids(slides)
    assert dupes == ["IMAGE:foo"]


def test_find_duplicate_marker_ids_empty_when_unique():
    slides = [
        SlideFacts(slide_index=1, text_content="", markers=[
            Marker("IMAGE", "foo", 0, 0, 0, 0),
        ]),
        SlideFacts(slide_index=2, text_content="", markers=[
            Marker("IMAGE", "bar", 0, 0, 0, 0),
        ]),
    ]
    assert find_duplicate_marker_ids(slides) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_placeholder.py -v`
Expected: ImportError on `src.placeholder`.

- [ ] **Step 3: Write the implementation**

`src/placeholder.py`:

```python
"""Marker grammar, parsing, and uniqueness checks.

Grammar: ^(IMAGE|SMARTART|BG):[a-z0-9_-]+$  (lowercase-only after the colon).
Per spec Section 3.1 — duplicate marker identifiers are a brief-authoring
error and must be surfaced to the user before enrichment proceeds.
"""
from __future__ import annotations

import re
from collections import Counter

from src.slide_facts import Marker, SlideFacts

MARKER_RE = re.compile(r"^(IMAGE|SMARTART|BG):([a-z0-9_-]+)$")


def parse_marker(name: str) -> tuple[str, str] | None:
    """Return (kind, identifier) if `name` matches the grammar, else None."""
    if not isinstance(name, str):
        return None
    m = MARKER_RE.match(name)
    if m is None:
        return None
    return m.group(1), m.group(2)


def is_marker_name(name: str) -> bool:
    return parse_marker(name) is not None


def find_duplicate_marker_ids(slides: list[SlideFacts]) -> list[str]:
    """Return marker ids (as `KIND:identifier` strings) that appear on more than one slide
    OR more than once on a single slide."""
    counter: Counter[str] = Counter()
    for slide in slides:
        for marker in slide.markers:
            counter[f"{marker.kind}:{marker.identifier}"] += 1
    return sorted(mid for mid, count in counter.items() if count > 1)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_placeholder.py -v`
Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/placeholder.py plugins/jack-tar-superpower-bridge/tests/test_placeholder.py
git commit -m "feat(bridge): marker grammar and uniqueness helpers"
```

---

### Task 4: Security primitives (image-path allowlist + .pptx pre-flight + hardened XML parser)

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/security.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_security.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_security.py`:

```python
import io
import os
import zipfile
from pathlib import Path

import pytest
from lxml import etree

from src.security import (
    AllowedPathError,
    PptxPreflightError,
    XmlSecurityError,
    resolve_within_allowlist,
    preflight_pptx,
    safe_xml_parser,
    DEFAULT_DECOMPRESSED_CEILING_BYTES,
    DEFAULT_PART_COUNT_CEILING,
    DEFAULT_PER_PART_CEILING_BYTES,
)


# ----- image-path allowlist ----------------------------------------------------

def test_allowlist_accepts_path_inside_allowed_root(tmp_path):
    allowed = tmp_path / "generated"
    allowed.mkdir()
    img = allowed / "hero.png"
    img.write_bytes(b"fake")
    resolved = resolve_within_allowlist(img, allowed_roots=[allowed])
    assert resolved == img.resolve()


def test_allowlist_rejects_path_outside_roots(tmp_path):
    allowed = tmp_path / "generated"
    allowed.mkdir()
    other = tmp_path / "secret.png"
    other.write_bytes(b"x")
    with pytest.raises(AllowedPathError, match="outside the image-path allowlist"):
        resolve_within_allowlist(other, allowed_roots=[allowed])


def test_allowlist_rejects_symlinks(tmp_path):
    allowed = tmp_path / "generated"
    allowed.mkdir()
    target = tmp_path / "actual.png"
    target.write_bytes(b"x")
    link = allowed / "linked.png"
    os.symlink(target, link)
    with pytest.raises(AllowedPathError, match="symlink"):
        resolve_within_allowlist(link, allowed_roots=[allowed])


def test_allowlist_supports_multiple_roots(tmp_path):
    a = tmp_path / "a"; a.mkdir()
    b = tmp_path / "b"; b.mkdir()
    f = b / "x.png"; f.write_bytes(b"x")
    assert resolve_within_allowlist(f, allowed_roots=[a, b]) == f.resolve()


def test_allowlist_handles_relative_paths(tmp_path, monkeypatch):
    allowed = tmp_path / "generated"
    allowed.mkdir()
    img = allowed / "hero.png"
    img.write_bytes(b"x")
    monkeypatch.chdir(tmp_path)
    rel = Path("generated/hero.png")
    assert resolve_within_allowlist(rel, allowed_roots=[allowed]) == img.resolve()


# ----- .pptx pre-flight --------------------------------------------------------

def _build_pptx(tmp_path, parts: dict[str, bytes]) -> Path:
    p = tmp_path / "fake.pptx"
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in parts.items():
            zf.writestr(name, data)
    return p


def test_preflight_passes_for_normal_pptx(tmp_path):
    p = _build_pptx(tmp_path, {"[Content_Types].xml": b"<x/>", "ppt/slide1.xml": b"<x/>"})
    preflight_pptx(p)


def test_preflight_rejects_too_many_parts(tmp_path):
    parts = {f"ppt/slide{i}.xml": b"<x/>" for i in range(DEFAULT_PART_COUNT_CEILING + 5)}
    p = _build_pptx(tmp_path, parts)
    with pytest.raises(PptxPreflightError, match="part count"):
        preflight_pptx(p)


def test_preflight_rejects_oversized_part(tmp_path):
    big = b"A" * (DEFAULT_PER_PART_CEILING_BYTES + 1)
    p = _build_pptx(tmp_path, {"[Content_Types].xml": b"<x/>", "ppt/big.xml": big})
    with pytest.raises(PptxPreflightError, match="part size"):
        preflight_pptx(p)


def test_preflight_rejects_zip_bomb_ratio(tmp_path):
    # Highly compressible payload — zip will compress >100x
    big = b"\0" * (10_000_000)  # 10MB of zeros
    p = _build_pptx(tmp_path, {"[Content_Types].xml": b"<x/>", "ppt/zeros.bin": big})
    # Force the file size to be very small relative to decompressed size
    with pytest.raises(PptxPreflightError, match="ratio"):
        preflight_pptx(p, decompressed_ceiling_bytes=DEFAULT_DECOMPRESSED_CEILING_BYTES,
                      per_part_ceiling_bytes=20_000_000)


def test_preflight_rejects_total_decompressed_ceiling(tmp_path):
    # Lots of small parts each within per-part ceiling, but cumulative exceeds total ceiling
    parts = {f"ppt/p{i}.xml": (b"A" * 1_000_000) for i in range(50)}
    p = _build_pptx(tmp_path, parts)
    with pytest.raises(PptxPreflightError, match="decompressed"):
        preflight_pptx(p, decompressed_ceiling_bytes=10_000_000,
                      part_count_ceiling=200, per_part_ceiling_bytes=20_000_000)


def test_preflight_rejects_missing_file(tmp_path):
    with pytest.raises(PptxPreflightError, match="not a file"):
        preflight_pptx(tmp_path / "missing.pptx")


# ----- hardened XML parser -----------------------------------------------------

def test_safe_xml_parser_disables_entities():
    parser = safe_xml_parser()
    xxe = (
        b'<?xml version="1.0"?>'
        b'<!DOCTYPE r [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>'
        b'<r>&xxe;</r>'
    )
    # Resolution must NOT happen — the entity reference should not expand to file contents.
    tree = etree.fromstring(xxe, parser=parser)
    assert b"root:" not in etree.tostring(tree)


def test_safe_xml_parser_rejects_huge_tree():
    # huge_tree=False rejects deeply nested input (lxml's default limit kicks in)
    parser = safe_xml_parser()
    src = b"<r>" * 50_000 + b"x" + b"</r>" * 50_000
    with pytest.raises((etree.XMLSyntaxError, XmlSecurityError)):
        etree.fromstring(src, parser=parser)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_security.py -v`
Expected: ImportError on `src.security`.

- [ ] **Step 3: Write the implementation**

`src/security.py`:

```python
"""Security primitives.

Three concerns covered here, all surfaced as hard contracts in the
spec's Security & Privacy section:

  1. Image-path allowlist — paths passed to python-pptx image APIs
     must resolve inside an explicit set of allowed roots; symlinks
     are rejected outright. Default callers pass ['<run>/generated',
     '<run>/carriers'].
  2. .pptx pre-flight — refuse files exceeding decompressed-size,
     part-count, per-part-size, or compression-ratio ceilings before
     python-pptx opens them.
  3. Hardened XML parser — every place the bridge parses XML directly
     uses this parser config so XXE / DTD-expansion / huge-tree
     attacks cannot land.
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Iterable

from lxml import etree


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class AllowedPathError(ValueError):
    """Raised when an image path resolves outside the allowlist or is a symlink."""


class PptxPreflightError(ValueError):
    """Raised when a .pptx fails any of the pre-flight resource ceilings."""


class XmlSecurityError(ValueError):
    """Raised when XML parsing cannot proceed under the safe parser config."""


# ---------------------------------------------------------------------------
# Image-path allowlist
# ---------------------------------------------------------------------------

def resolve_within_allowlist(path: Path | str, allowed_roots: Iterable[Path]) -> Path:
    """Return `path.resolve()` if it is inside any allowed_root and not a symlink.

    Raises AllowedPathError otherwise.
    """
    p = Path(path)
    if p.is_symlink():
        raise AllowedPathError(f"path is a symlink and is rejected: {p}")
    resolved = p.resolve()
    for root in allowed_roots:
        root_resolved = Path(root).resolve()
        try:
            resolved.relative_to(root_resolved)
            return resolved
        except ValueError:
            continue
    raise AllowedPathError(
        f"path is outside the image-path allowlist: {p} (allowed roots: "
        f"{[str(r) for r in allowed_roots]})"
    )


# ---------------------------------------------------------------------------
# .pptx pre-flight
# ---------------------------------------------------------------------------

DEFAULT_DECOMPRESSED_CEILING_BYTES = 200 * 1024 * 1024     # 200 MB
DEFAULT_PART_COUNT_CEILING = 2000
DEFAULT_PER_PART_CEILING_BYTES = 50 * 1024 * 1024          # 50 MB
DEFAULT_RATIO_CEILING = 100                                # decompressed / compressed


def preflight_pptx(
    path: Path | str,
    *,
    decompressed_ceiling_bytes: int = DEFAULT_DECOMPRESSED_CEILING_BYTES,
    part_count_ceiling: int = DEFAULT_PART_COUNT_CEILING,
    per_part_ceiling_bytes: int = DEFAULT_PER_PART_CEILING_BYTES,
    ratio_ceiling: int = DEFAULT_RATIO_CEILING,
) -> None:
    """Refuse the .pptx if any resource ceiling is exceeded.

    Raises PptxPreflightError on any failure with a diagnostic message
    naming the specific check that failed.
    """
    p = Path(path)
    if not p.is_file():
        raise PptxPreflightError(f"not a file: {p}")
    compressed_size = p.stat().st_size

    try:
        with zipfile.ZipFile(p, "r") as zf:
            infos = zf.infolist()
    except zipfile.BadZipFile as exc:
        raise PptxPreflightError(f"not a valid zip archive: {p}") from exc

    if len(infos) > part_count_ceiling:
        raise PptxPreflightError(
            f"part count {len(infos)} exceeds ceiling {part_count_ceiling}"
        )

    total_decompressed = 0
    for info in infos:
        if info.file_size > per_part_ceiling_bytes:
            raise PptxPreflightError(
                f"part size {info.file_size} for {info.filename!r} exceeds "
                f"ceiling {per_part_ceiling_bytes}"
            )
        total_decompressed += info.file_size

    if total_decompressed > decompressed_ceiling_bytes:
        raise PptxPreflightError(
            f"total decompressed size {total_decompressed} exceeds ceiling "
            f"{decompressed_ceiling_bytes}"
        )

    if compressed_size > 0:
        ratio = total_decompressed / compressed_size
        if ratio > ratio_ceiling:
            raise PptxPreflightError(
                f"compression ratio {ratio:.1f} exceeds ceiling {ratio_ceiling} "
                f"(zip-bomb signal)"
            )


# ---------------------------------------------------------------------------
# Hardened XML parser
# ---------------------------------------------------------------------------

def safe_xml_parser() -> etree.XMLParser:
    """Return an XMLParser configured to disable the common attack vectors.

    - resolve_entities=False  → no XXE / DTD expansion
    - no_network=True         → external DTDs cannot be fetched
    - huge_tree=False         → reject deeply-nested or pathologically large trees
    - load_dtd=False          → avoid pulling DTDs altogether

    THREAT-MODEL BOUNDARY: the bridge does NOT parse user-supplied .pptx XML
    directly with lxml — all OOXML reads go through python-pptx (`Presentation`,
    `slide.element.find(...)`), which has its own lxml configuration. python-pptx
    1.0.2 is treated as the threat-model boundary for OOXML parsing: vulnerabilities
    in python-pptx's parser config are tracked upstream, not patched in the bridge.
    `safe_xml_parser` IS used everywhere the bridge constructs lxml elements
    directly (e.g. `enrichment_ops/background.py`'s _build_bg_element via
    etree.fromstring on bridge-emitted strings — bridge-controlled, not user-
    controlled, so the parser config matters less but is still applied).

    If the bridge ever needs to parse user-supplied raw XML directly (e.g. a
    future "validate the carrier .pptx parts" feature), this is the parser to
    use. Adding a new direct-parse path requires a spec amendment and a security
    review per the Security & Privacy section.
    """
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        huge_tree=False,
        load_dtd=False,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_security.py -v`
Expected: 11 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/security.py plugins/jack-tar-superpower-bridge/tests/test_security.py
git commit -m "feat(bridge): security primitives — allowlist, pre-flight, hardened XML parser"
```

---

### Task 5: CreativeBrief dataclass + read/write helpers

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/creative_brief.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_creative_brief.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_creative_brief.py`:

```python
import pytest
from pathlib import Path

from src.creative_brief import (
    CreativeBrief,
    CreativeBriefValidationError,
    parse_brief_markdown,
    write_brief_markdown,
    DEFAULT_BUDGET_CAP_USD,
)


def test_default_confidentiality_is_public():
    brief = CreativeBrief(
        topic="AI agents",
        audience="developers",
        duration_minutes=20,
        narrative_arc="Problem-Solution",
        narrative_detail="open with provocative question",
        audience_takeaway="agents need explicit architecture",
        tone="confident but approachable",
        visual_personality="dark, atmospheric, architectural metaphors",
        placeholder_instructions="describes IMAGE/SMARTART/BG marker types only",
    )
    assert brief.confidentiality == "public"
    assert brief.budget_cap_usd == DEFAULT_BUDGET_CAP_USD


def test_validation_rejects_unknown_confidentiality():
    with pytest.raises(CreativeBriefValidationError, match="confidentiality"):
        CreativeBrief(
            topic="x", audience="x", duration_minutes=5, narrative_arc="x",
            narrative_detail="x", audience_takeaway="x", tone="x",
            visual_personality="x", placeholder_instructions="x",
            confidentiality="confidential",
        )


def test_validation_rejects_negative_budget():
    with pytest.raises(CreativeBriefValidationError, match="budget_cap_usd"):
        CreativeBrief(
            topic="x", audience="x", duration_minutes=5, narrative_arc="x",
            narrative_detail="x", audience_takeaway="x", tone="x",
            visual_personality="x", placeholder_instructions="x",
            budget_cap_usd=-0.5,
        )


def test_validation_rejects_zero_duration():
    with pytest.raises(CreativeBriefValidationError, match="duration_minutes"):
        CreativeBrief(
            topic="x", audience="x", duration_minutes=0, narrative_arc="x",
            narrative_detail="x", audience_takeaway="x", tone="x",
            visual_personality="x", placeholder_instructions="x",
        )


def test_to_markdown_contains_all_sections():
    brief = CreativeBrief(
        topic="AI agents", audience="developers", duration_minutes=20,
        narrative_arc="Problem-Solution",
        narrative_detail="Open with a provocative question",
        audience_takeaway="agents need explicit architecture",
        tone="confident",
        visual_personality="dark backgrounds, accent teal",
        placeholder_instructions="IMAGE for hero illustrations; SMARTART for processes; BG for atmospheric backgrounds. Use objectName property in PptxGenJS.",
    )
    md = brief.to_markdown()
    assert "## Section A — Narrative Architecture" in md
    assert "## Section B — Communication & Visual Intent" in md
    assert "## Section C — Placeholder Instructions" in md
    assert "objectName" in md
    assert "Confidentiality: public" in md


def test_roundtrip_through_markdown():
    brief = CreativeBrief(
        topic="agents", audience="devs", duration_minutes=15,
        narrative_arc="Hero's Journey", narrative_detail="hero starts naive",
        audience_takeaway="empathy unlocks design",
        tone="warm",
        visual_personality="cinematic, golden-hour palette",
        placeholder_instructions="three IMAGE markers max",
        confidentiality="internal",
        budget_cap_usd=2.50,
    )
    parsed = parse_brief_markdown(brief.to_markdown())
    assert parsed.topic == "agents"
    assert parsed.confidentiality == "internal"
    assert parsed.budget_cap_usd == 2.50
    assert parsed.narrative_arc == "Hero's Journey"


def test_write_and_read_brief_file(tmp_path):
    brief = CreativeBrief(
        topic="t", audience="a", duration_minutes=10, narrative_arc="x",
        narrative_detail="x", audience_takeaway="x", tone="x",
        visual_personality="x", placeholder_instructions="x",
    )
    out = tmp_path / "creative-brief.md"
    write_brief_markdown(brief, out)
    assert out.exists()
    parsed = parse_brief_markdown(out.read_text())
    assert parsed.topic == "t"


def test_parse_rejects_missing_section():
    incomplete = (
        "# Creative Brief\n\n"
        "**Topic:** x\n**Audience:** y\n**Duration:** 10 min\n"
        "**Confidentiality:** public\n**Budget cap:** $1.00\n\n"
        "## Section A — Narrative Architecture\n\n"
        "**Arc:** x\n\nx\n\n"
        "## Section B — Communication & Visual Intent\n\n"
        "**Audience takeaway:** x\n**Tone:** x\n**Visual personality:** x\n"
    )
    with pytest.raises(CreativeBriefValidationError, match="Section C"):
        parse_brief_markdown(incomplete)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_creative_brief.py -v`
Expected: ImportError on `src.creative_brief`.

- [ ] **Step 3: Write the implementation**

`src/creative_brief.py`:

```python
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
            f"**Topic:** {self.topic}\n"
            f"**Audience:** {self.audience}\n"
            f"**Duration:** {self.duration_minutes} min\n"
            f"**Confidentiality:** {self.confidentiality}\n"
            f"**Budget cap:** ${self.budget_cap_usd:.2f}\n\n"
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


_HEADER_RE = re.compile(
    r"^\*\*Topic:\*\*\s+(?P<topic>.+?)\n"
    r"\*\*Audience:\*\*\s+(?P<audience>.+?)\n"
    r"\*\*Duration:\*\*\s+(?P<duration>\d+)\s*min\n"
    r"\*\*Confidentiality:\*\*\s+(?P<confidentiality>public|internal|restricted)\n"
    r"\*\*Budget cap:\*\*\s+\$(?P<budget>[0-9]+(?:\.[0-9]+)?)",
    re.MULTILINE,
)
_ARC_RE = re.compile(r"^\*\*Arc:\*\*\s+(?P<arc>.+?)$", re.MULTILINE)
_TAKEAWAY_RE = re.compile(r"^\*\*Audience takeaway:\*\*\s+(?P<takeaway>.+?)$", re.MULTILINE)
_TONE_RE = re.compile(r"^\*\*Tone:\*\*\s+(?P<tone>.+?)$", re.MULTILINE)
_VISUAL_RE = re.compile(r"^\*\*Visual personality:\*\*\s+(?P<vp>.+?)$", re.MULTILINE)


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_creative_brief.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/creative_brief.py plugins/jack-tar-superpower-bridge/tests/test_creative_brief.py
git commit -m "feat(bridge): CreativeBrief dataclass with markdown roundtrip"
```

---

## Phase 2 — Analyser (5 tasks, OOXML primary + JS-AST fallback + overlap verifier)

### Task 6: msft-smartart loader (PLUGIN_ROOT discovery for cross-plugin imports)

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/msft_smartart_loader.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_msft_smartart_loader.py`

This task ships now (not later) because both the smartart_bridge AND the analyser orchestrator's overlap verifier benefit from a single audited import path. The loader implements the supply-chain mitigation in the spec's Security & Privacy section: imported surface is named explicitly.

- [ ] **Step 1: Write the failing tests**

`tests/test_msft_smartart_loader.py`:

```python
import pytest

from src.msft_smartart_loader import (
    load_msft_smartart_api,
    MsftSmartArtNotFoundError,
    ALLOWED_SYMBOLS,
)


def test_loads_three_named_symbols():
    api = load_msft_smartart_api()
    assert hasattr(api, "engine")
    assert hasattr(api, "InjectionRequest")
    assert hasattr(api, "inject")
    # Engine has render() function
    assert callable(api.engine.render)
    # InjectionRequest is a dataclass with the fields the bridge uses
    req = api.InjectionRequest(slide_number=1, carrier_pptx="x.pptx",
                                placeholder_name="SMARTART:foo")
    assert req.slide_number == 1
    assert req.placeholder_name == "SMARTART:foo"


def test_allowed_symbols_is_documented_explicitly():
    # The supply-chain mitigation requires the imported surface to be named.
    assert set(ALLOWED_SYMBOLS) == {"engine.render", "InjectionRequest", "inject"}


def test_load_raises_when_plugin_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("JACK_TAR_SUPERPOWER_BRIDGE_FORCE_MSFT_ROOT", str(tmp_path / "missing"))
    with pytest.raises(MsftSmartArtNotFoundError):
        load_msft_smartart_api()


def test_loader_restores_bridge_src_modules_after_load():
    """Cross-plugin sys.modules contamination guard.

    Before this test, the conftest fixture has put the bridge's plugin path
    on sys.path[0] and may have imported some src.* modules (e.g. src.placeholder).
    The loader temporarily swaps to the msft-smartart path; after it returns,
    bridge's src.* must still resolve to bridge's modules, not msft-smartart's.
    """
    import sys
    # Pre-load a bridge module so we have something to track
    from src.placeholder import MARKER_RE as bridge_marker_re
    bridge_placeholder_id = id(sys.modules.get("src.placeholder"))
    assert bridge_placeholder_id is not None

    api = load_msft_smartart_api()
    assert hasattr(api, "engine")  # actually loaded msft-smartart

    # After load: bridge's src.placeholder must still be the bridge's module
    from src.placeholder import MARKER_RE as marker_re_after
    assert marker_re_after is bridge_marker_re, (
        "bridge's src.placeholder was clobbered by msft-smartart's src.* — "
        "the loader did not restore bridge's modules"
    )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_msft_smartart_loader.py -v`
Expected: ImportError on `src.msft_smartart_loader`.

- [ ] **Step 3: Write the implementation**

`src/msft_smartart_loader.py`:

```python
"""Discover and import the jack-tar-msft-smartart plugin's surface.

The bridge needs three named symbols from the SmartArt plugin:

  - engine.render(spec, output_dir) -> RenderResult
  - InjectionRequest(slide_number, carrier_pptx, placeholder_name)
  - inject(host_pptx, requests) -> list[InjectionResult]

We resolve the plugin root via three sources in order:

  1. JACK_TAR_SUPERPOWER_BRIDGE_FORCE_MSFT_ROOT (test override)
  2. ~/.claude/plugins/cache/**/jack-tar-msft-smartart (production install)
  3. <worktree>/plugins/jack-tar-msft-smartart (local dev)

After locating, we mutate sys.path and clear sys.modules['src.*'] so the
SmartArt plugin's `from src import ...` resolves correctly even when the
bridge's own `src.*` is already imported. The import surface is named
explicitly via ALLOWED_SYMBOLS — any expansion requires a spec amendment
(supply-chain mitigation).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

ALLOWED_SYMBOLS = ("engine.render", "InjectionRequest", "inject")


class MsftSmartArtNotFoundError(RuntimeError):
    """Raised when the jack-tar-msft-smartart plugin cannot be located."""


@dataclass
class MsftSmartArtAPI:
    engine: ModuleType
    InjectionRequest: type
    inject: callable


def _candidate_roots() -> list[Path]:
    candidates: list[Path] = []
    forced = os.environ.get("JACK_TAR_SUPERPOWER_BRIDGE_FORCE_MSFT_ROOT")
    if forced:
        candidates.append(Path(forced))
        return candidates

    home = Path.home()
    cache_root = home / ".claude" / "plugins" / "cache"
    if cache_root.exists():
        for plugin_json in cache_root.rglob(
            "jack-tar-msft-smartart/.claude-plugin/plugin.json"
        ):
            candidates.append(plugin_json.parent.parent)
            break

    # Local dev — walk upwards looking for plugins/jack-tar-msft-smartart
    for parent in [Path.cwd(), *Path.cwd().parents]:
        candidate = parent / "plugins" / "jack-tar-msft-smartart"
        if candidate.exists():
            candidates.append(candidate)
            break

    return candidates


def load_msft_smartart_api() -> MsftSmartArtAPI:
    """Locate, import, and return the named SmartArt surface.

    Cross-plugin sys.modules safety: the loader snapshots the caller's
    `src.*` modules + sys.path[0] BEFORE swapping in the msft-smartart plugin
    path, then restores them after the imports complete. The returned
    MsftSmartArtAPI holds direct module references, so callers can use them
    after restoration. Subsequent `from src import ...` calls in the caller
    resolve to the caller's `src.*` (the bridge), not msft-smartart's.

    Raises MsftSmartArtNotFoundError if the plugin is missing.
    """
    candidates = _candidate_roots()
    plugin_root: Path | None = None
    for candidate in candidates:
        if (candidate / "src" / "engine.py").exists():
            plugin_root = candidate
            break
    if plugin_root is None:
        raise MsftSmartArtNotFoundError(
            "jack-tar-msft-smartart plugin not found. Install via marketplace, set "
            "JACK_TAR_SUPERPOWER_BRIDGE_FORCE_MSFT_ROOT, or run from a worktree that "
            "contains plugins/jack-tar-msft-smartart."
        )

    plugin_str = str(plugin_root)

    # Snapshot caller's state so we can restore after the import swap
    caller_path0 = sys.path[0] if sys.path else None
    caller_src_modules: dict[str, object] = {
        k: sys.modules[k] for k in list(sys.modules)
        if k == "src" or k.startswith("src.")
    }

    # Clear caller's src.* and put msft-smartart's plugin path at the front
    for key in caller_src_modules:
        del sys.modules[key]
    if plugin_str in sys.path:
        sys.path.remove(plugin_str)
    sys.path.insert(0, plugin_str)

    try:
        from src import engine as engine_mod  # type: ignore
        from src import assembler_patch as ap_mod  # type: ignore
        api = MsftSmartArtAPI(
            engine=engine_mod,
            InjectionRequest=ap_mod.InjectionRequest,
            inject=ap_mod.inject,
        )
    finally:
        # Restore caller's state — drop msft-smartart from sys.path[0],
        # delete msft-smartart's src.* (now in sys.modules under those names),
        # and put caller's src.* modules back.
        if sys.path and sys.path[0] == plugin_str:
            sys.path.pop(0)
        for key in list(sys.modules):
            if key == "src" or key.startswith("src."):
                del sys.modules[key]
        for key, mod in caller_src_modules.items():
            sys.modules[key] = mod
        # Restore caller's path[0] if it was displaced
        if caller_path0 is not None and (not sys.path or sys.path[0] != caller_path0):
            if caller_path0 in sys.path:
                sys.path.remove(caller_path0)
            sys.path.insert(0, caller_path0)
    return api
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_msft_smartart_loader.py -v`
Expected: 4 passed (3 originals + the bridge sys.modules restoration guard).

Note: the loader temporarily mutates `sys.path` and `sys.modules` but restores caller state in a `finally` block. The Spike 2 prototype (`op3_inject_smartart.py`) did NOT restore — Spike 2 was a one-off where state contamination was acceptable. Production has the bridge running multiple cross-plugin imports per /enrich-deck call (analyser → smartart bridge → enrichment ops), so the restoration is mandatory.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/msft_smartart_loader.py plugins/jack-tar-superpower-bridge/tests/test_msft_smartart_loader.py
git commit -m "feat(bridge): msft-smartart plugin loader with named-symbol allowlist"
```

---

### Task 7: OOXML parser (analyser primary)

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/analyser/__init__.py` (empty for now)
- Create: `plugins/jack-tar-superpower-bridge/src/analyser/pptx_parser.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_analyser_pptx_parser.py`

The OOXML parser is lifted from Spike 3's `parsers/pptx_parser.py` and extended with the `bgColor` attribute check (Spike 3 spec-update item #7). This must be wired in from day one — the spike parser missed colour-only backgrounds and would have shipped that gap.

- [ ] **Step 1: Write the failing tests**

`tests/test_analyser_pptx_parser.py`:

```python
import pytest
from pptx import Presentation
from pptx.util import Inches

from src.analyser.pptx_parser import parse_pptx
from src.slide_facts import SlideFacts


def test_parses_variant_a_extracts_eight_markers(seed_variant_a):
    facts = parse_pptx(seed_variant_a)
    assert len(facts) == 10
    total_markers = sum(len(s.markers) for s in facts)
    assert total_markers == 8


def test_parses_variant_a_marker_kinds(seed_variant_a):
    facts = parse_pptx(seed_variant_a)
    kinds = {m.kind for s in facts for m in s.markers}
    assert kinds <= {"IMAGE", "SMARTART", "BG"}
    assert "IMAGE" in kinds
    assert "BG" in kinds


def test_marker_geometry_is_emu(seed_variant_a):
    facts = parse_pptx(seed_variant_a)
    for slide in facts:
        for marker in slide.markers:
            assert isinstance(marker.left_emu, int)
            assert isinstance(marker.top_emu, int)
            assert marker.width_emu > 0
            assert marker.height_emu > 0


def test_variant_b_returns_zero_markers(seed_variant_b):
    """Variant B uses `name:` which PptxGenJS drops — OOXML sees no marker shape names."""
    facts = parse_pptx(seed_variant_b)
    total = sum(len(s.markers) for s in facts)
    assert total == 0


def test_text_content_extracted_from_text_frames(seed_variant_a):
    facts = parse_pptx(seed_variant_a)
    # At least one slide must have text content
    assert any(s.text_content.strip() for s in facts)


def test_element_types_counts_charts_images(seed_variant_a):
    facts = parse_pptx(seed_variant_a)
    # Variant A uses real /pptx idioms — at minimum each slide has text shapes
    assert all(s.element_types.get("text", 0) >= 0 for s in facts)


def test_bgcolor_attribute_recognised_as_solid_background(tmp_path):
    """If a slide carries a bgColor attribute (PptxGenJS colour backgrounds), the
    parser must report background_kind='solid' instead of 'default'."""
    from lxml import etree
    from pptx import Presentation
    from pptx.oxml.ns import qn

    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    # Inject the PptxGenJS-style bgColor attribute on <p:sld>
    slide.element.set("bgColor", "0E1513")
    out = tmp_path / "bgcolor.pptx"
    prs.save(out)

    facts = parse_pptx(out)
    assert facts[0].background_kind == "solid"


def test_image_background_recognised_via_blipfill(tmp_path):
    """If a slide has <p:bg><a:blipFill>, background_kind must be 'image'."""
    from src.analyser.pptx_parser import parse_pptx
    # Reuse the spike's after_op1.pptx which has a blipFill background applied
    spike_after_op1 = (
        seed_variant_a := None  # silence unused
    )
    # Build a deck with an explicit <p:bg><a:blipFill> by hand
    from pptx import Presentation
    from pptx.oxml.ns import qn
    from lxml import etree

    prs = Presentation()
    prs.slides.add_slide(prs.slide_layouts[6])
    # Note: the structural assertion is sufficient; the parser only needs
    # to detect the <a:blipFill> inside <p:bg>.
    slide = prs.slides[0]
    cSld = slide.element.find(qn("p:cSld"))
    bg_xml = (
        '<p:bg xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<p:bgPr><a:blipFill><a:blip r:embed="rId99"/><a:stretch><a:fillRect/></a:stretch>'
        '</a:blipFill></p:bgPr></p:bg>'
    )
    cSld.insert(0, etree.fromstring(bg_xml))
    out = tmp_path / "blipfill.pptx"
    prs.save(out)

    facts = parse_pptx(out)
    assert facts[0].background_kind == "image"


def test_nonexistent_file_raises_filenotfound(tmp_path):
    with pytest.raises(FileNotFoundError):
        parse_pptx(tmp_path / "nope.pptx")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_analyser_pptx_parser.py -v`
Expected: ImportError on `src.analyser.pptx_parser`.

- [ ] **Step 3: Write the implementation**

`src/analyser/__init__.py` (placeholder so the package is importable; the orchestrator lives here in Task 10):

```python
"""Analyser package — OOXML primary, JS-AST fallback, overlap verifier."""
```

`src/analyser/pptx_parser.py`:

```python
"""OOXML-primary analyser via python-pptx.

Lifted from Spike 3's parsers/pptx_parser.py with two production-bound
extensions:

  1. bgColor attribute on <p:sld> → background_kind='solid' (Spike 3
     spec update item #7 — covers PptxGenJS colour-only backgrounds).
  2. FileNotFoundError instead of swallowing missing-input.
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn

from src.placeholder import parse_marker
from src.slide_facts import Marker, SlideFacts


def _shape_element_type(shape) -> str:
    st = shape.shape_type
    if st == MSO_SHAPE_TYPE.PICTURE:
        return "image"
    if st == MSO_SHAPE_TYPE.CHART:
        return "chart"
    if st == MSO_SHAPE_TYPE.TABLE:
        return "table"
    if shape.has_text_frame and shape.text_frame.text.strip():
        return "text"
    return "shape"


def _background_kind(slide) -> str:
    """Detect background category, considering both <p:bg> and the slide
    element's bgColor attribute (PptxGenJS emits colour backgrounds via
    bgColor, not <p:bg>)."""
    cSld = slide.element.find(qn("p:cSld"))
    bg = cSld.find(qn("p:bg")) if cSld is not None else None
    if bg is not None:
        if bg.find(".//" + qn("a:blipFill")) is not None:
            return "image"
        if bg.find(".//" + qn("a:solidFill")) is not None:
            return "solid"
        if bg.find(".//" + qn("a:gradFill")) is not None:
            return "solid"
        return "unknown"
    # Spike 3 spec update item #7 — check bgColor attribute on <p:sld>
    if slide.element.get("bgColor"):
        return "solid"
    return "default"


def parse_pptx(path: Path | str) -> list[SlideFacts]:
    """Parse a .pptx → list[SlideFacts] using OOXML as the source of truth.

    Raises FileNotFoundError if `path` does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    prs = Presentation(str(p))
    results: list[SlideFacts] = []
    for idx, slide in enumerate(prs.slides, start=1):
        text_parts: list[str] = []
        markers: list[Marker] = []
        counts: dict[str, int] = {"text": 0, "shape": 0, "image": 0,
                                   "chart": 0, "table": 0}
        for shape in slide.shapes:
            name = getattr(shape, "name", "") or ""
            parsed = parse_marker(name)
            if parsed is not None:
                kind, ident = parsed
                markers.append(Marker(
                    kind=kind,
                    identifier=ident,
                    left_emu=shape.left or 0,
                    top_emu=shape.top or 0,
                    width_emu=shape.width or 0,
                    height_emu=shape.height or 0,
                ))
                continue
            kind = _shape_element_type(shape)
            counts[kind] = counts.get(kind, 0) + 1
            if shape.has_text_frame:
                text_parts.append(shape.text_frame.text)
        results.append(SlideFacts(
            slide_index=idx,
            text_content="\n".join(t for t in text_parts if t.strip()),
            markers=markers,
            background_kind=_background_kind(slide),
            element_types=counts,
        ))
    return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_analyser_pptx_parser.py -v`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/analyser/
git add plugins/jack-tar-superpower-bridge/tests/test_analyser_pptx_parser.py
git commit -m "feat(bridge): OOXML primary analyser with bgColor attribute support"
```

---

### Task 8: JS-AST fallback parser (parse-only, never execute)

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/analyser/js_parser.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_analyser_js_parser.py`

Lifted from Spike 3's `parsers/js_parser.py` with the addition of an explicit `JsParseSecurityError` for parse failures and a hard contract test that subprocess / eval / exec are never invoked.

- [ ] **Step 1: Write the failing tests**

`tests/test_analyser_js_parser.py`:

```python
import sys
from unittest.mock import patch

import pytest

from src.analyser.js_parser import parse_js, JsParseError, EXEC_GUARD_NAMES


def test_variant_a_recovers_eight_markers(seed_variant_a_build):
    facts = parse_js(seed_variant_a_build)
    total = sum(len(s.markers) for s in facts)
    assert total == 8


def test_variant_b_recovers_markers_that_ooxml_misses(seed_variant_b_build):
    """Variant B used `name:` (dropped by PptxGenJS) — JS parser sees them in source."""
    facts = parse_js(seed_variant_b_build)
    total = sum(len(s.markers) for s in facts)
    assert total >= 1, "Variant B build.js was authored with marker-bearing addShape calls"


def test_parser_never_calls_subprocess_eval_exec_or_require(seed_variant_a_build):
    """Hard contract test: the JS fallback never executes user JavaScript.

    Patches every enumerated guard target with a side_effect that raises if
    invoked. Earlier draft of this test only patched 3 of the 9 targets it
    enumerated — the security panel flagged this. Now we apply ALL patches via
    contextlib.ExitStack so future regressions are caught."""
    import builtins, contextlib, importlib, os, subprocess

    calls: list[str] = []

    def _trip(name):
        def boom(*a, **kw):
            calls.append(name)
            raise AssertionError(f"JS parser must not invoke {name!r}")
        return boom

    targets = [
        (subprocess, "Popen", _trip("subprocess.Popen")),
        (subprocess, "run", _trip("subprocess.run")),
        (subprocess, "call", _trip("subprocess.call")),
        (subprocess, "check_call", _trip("subprocess.check_call")),
        (subprocess, "check_output", _trip("subprocess.check_output")),
        (subprocess, "getoutput", _trip("subprocess.getoutput")),
        (subprocess, "getstatusoutput", _trip("subprocess.getstatusoutput")),
        (builtins, "eval", _trip("builtins.eval")),
        (builtins, "exec", _trip("builtins.exec")),
        (builtins, "compile", _trip("builtins.compile")),
        (os, "system", _trip("os.system")),
        (os, "popen", _trip("os.popen")),
        (importlib, "import_module", _trip("importlib.import_module")),
    ]

    with contextlib.ExitStack() as stack:
        for module, attr, fake in targets:
            if hasattr(module, attr):
                stack.enter_context(patch.object(module, attr, side_effect=fake))
        parse_js(seed_variant_a_build)

    assert calls == [], f"JS parser invoked guarded names: {calls}"


def test_malicious_buildjs_with_top_level_subprocess_does_not_run(tmp_path):
    """A build.js that *would* spawn child_process if executed must not.

    The parser walks the AST; the top-level CallExpression to require()
    is parsed but never invoked.
    """
    malicious = tmp_path / "malicious.js"
    malicious.write_text(
        "require('child_process').execSync('echo OWNED');\n"
        "const pres = new pptxgen();\n"
        "const slide = pres.addSlide();\n"
        "slide.addShape('rect', { objectName: 'IMAGE:safe', x:0, y:0, w:1, h:1 });\n"
    )
    facts = parse_js(malicious)
    # The marker is still recovered because we parse the AST
    total = sum(len(s.markers) for s in facts)
    assert total == 1


def test_unparseable_js_raises_jsparseerror(tmp_path):
    bad = tmp_path / "broken.js"
    bad.write_text("function (((( ")
    with pytest.raises(JsParseError):
        parse_js(bad)


def test_exec_guard_names_documented():
    """The contract is enforced by the test above; this test asserts the guard list."""
    for required in ("subprocess", "eval", "exec", "compile", "os.system",
                      "os.popen", "import_module", "child_process"):
        assert required in EXEC_GUARD_NAMES, f"missing from EXEC_GUARD_NAMES: {required}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_analyser_js_parser.py -v`
Expected: ImportError on `src.analyser.js_parser`.

- [ ] **Step 3: Write the implementation**

`src/analyser/js_parser.py`:

```python
"""esprima AST-based JS parser — marker-extraction fallback only.

Hard contract: this module NEVER executes, imports, requires, or spawns
the input JavaScript. It only walks the AST and extracts literal values
out of `slide.addShape(..., { objectName|name: "...", x, y, w, h })`
calls. EXEC_GUARD_NAMES enumerates the things callers can grep for.

Lifted from Spike 3's parsers/js_parser.py with a new top-level
JsParseError class (the spike crashed with the raw esprima exception).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import esprima

from src.placeholder import parse_marker
from src.slide_facts import Marker, SlideFacts

EXEC_GUARD_NAMES = (
    # Python-side names the parser must never call
    "subprocess", "eval", "exec", "compile", "import_module", "os.system", "os.popen",
    # JavaScript-side names whose presence in build.js is a "would have spawned"
    # signal (parsing them is fine; executing them is what we forbid)
    "child_process", "spawn", "execSync", "execFile", "fork",
)

EMU_PER_INCH = 914400

EvalEnv = dict[str, Any]
SlideBindings = dict[str, SlideFacts]


class JsParseError(RuntimeError):
    """Raised when the JS source cannot be parsed."""


def _resolve_node(node, eval_env: EvalEnv) -> Any:
    if node is None:
        return None
    t = node.type

    if t == "Literal":
        return node.value

    if t == "Identifier":
        return eval_env.get(node.name)

    if t == "UnaryExpression" and node.operator == "-":
        v = _resolve_node(node.argument, eval_env)
        return -v if v is not None else None

    if t == "TemplateLiteral":
        parts = []
        quasis = node.quasis
        exprs = node.expressions
        for i, quasi in enumerate(quasis):
            cooked = quasi.value.cooked or ""
            parts.append(cooked)
            if i < len(exprs):
                val = _resolve_node(exprs[i], eval_env)
                if val is None:
                    return None
                parts.append(str(val))
        return "".join(parts)

    if t == "BinaryExpression" and node.operator == "+":
        l = _resolve_node(node.left, eval_env)
        r = _resolve_node(node.right, eval_env)
        if l is not None and r is not None:
            try:
                return l + r
            except TypeError:
                return None

    return None


def _extract_object_properties_with_env(obj_node, eval_env: EvalEnv) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if obj_node is None or obj_node.type != "ObjectExpression":
        return out
    for prop in obj_node.properties:
        if prop.type != "Property":
            continue
        key = prop.key.name if prop.key.type == "Identifier" else prop.key.value
        val = _resolve_node(prop.value, eval_env)
        out[key] = val
    return out


def _inches_to_emu(v: Any) -> int:
    if v is None:
        return 0
    try:
        return int(float(v) * EMU_PER_INCH)
    except (TypeError, ValueError):
        return 0


def parse_js(path: Path | str) -> list[SlideFacts]:
    """Parse a build.js → list[SlideFacts]. Markers are recovered from
    `slide.addShape(..., { objectName|name: 'KIND:identifier', ... })` calls.

    Raises JsParseError on unparseable input.
    """
    source = Path(path).read_text()
    try:
        tree = esprima.parseScript(source, options={"tolerant": True})
    except esprima.Error as exc:
        raise JsParseError(f"failed to parse {path}: {exc}") from exc
    except Exception as exc:  # esprima sometimes raises non-Error subclasses
        raise JsParseError(f"failed to parse {path}: {exc}") from exc

    helpers: dict[str, tuple[list, list]] = {}
    for stmt in tree.body:
        if stmt.type == "FunctionDeclaration" and stmt.params:
            helpers[stmt.id.name] = (stmt.params, stmt.body.body)

    slides_list: list[SlideFacts] = []

    def _new_slide() -> SlideFacts:
        sf = SlideFacts(slide_index=len(slides_list) + 1, text_content="")
        slides_list.append(sf)
        return sf

    def _is_add_slide_call(call) -> bool:
        callee = call.callee
        return (callee.type == "MemberExpression"
                and callee.property.type == "Identifier"
                and callee.property.name == "addSlide")

    def _handle_add_text(facts: SlideFacts, call, eval_env: EvalEnv):
        if not call.arguments:
            return
        arg0 = call.arguments[0]
        val = _resolve_node(arg0, eval_env)
        if isinstance(val, str):
            facts.text_content = (facts.text_content + "\n" + val).strip()
            return
        if arg0.type == "ArrayExpression":
            parts: list[str] = []
            for el in arg0.elements:
                if el is None:
                    continue
                v = _resolve_node(el, eval_env)
                if isinstance(v, str):
                    parts.append(v)
                elif el.type == "ObjectExpression":
                    props = _extract_object_properties_with_env(el, eval_env)
                    if isinstance(props.get("text"), str):
                        parts.append(props["text"])
            if parts:
                facts.text_content = (facts.text_content + "\n" + "\n".join(parts)).strip()

    def _handle_add_shape(facts: SlideFacts, call, eval_env: EvalEnv):
        if len(call.arguments) < 2:
            return
        props = _extract_object_properties_with_env(call.arguments[1], eval_env)
        object_name = props.get("objectName") or props.get("name")
        if isinstance(object_name, str):
            parsed = parse_marker(object_name.lower() if object_name and ":" in object_name and not object_name.startswith(("IMAGE", "SMARTART", "BG")) else object_name)
            if parsed is not None:
                kind, ident = parsed
                facts.markers.append(Marker(
                    kind=kind,
                    identifier=ident,
                    left_emu=_inches_to_emu(props.get("x")),
                    top_emu=_inches_to_emu(props.get("y")),
                    width_emu=_inches_to_emu(props.get("w")),
                    height_emu=_inches_to_emu(props.get("h")),
                ))
                return
        facts.element_types["shape"] = facts.element_types.get("shape", 0) + 1

    def _apply_method(facts: SlideFacts, method: str, call, eval_env: EvalEnv):
        if method == "addText":
            _handle_add_text(facts, call, eval_env)
        elif method == "addShape":
            _handle_add_shape(facts, call, eval_env)
        elif method == "addImage":
            facts.element_types["image"] = facts.element_types.get("image", 0) + 1
        elif method == "addChart":
            facts.element_types["chart"] = facts.element_types.get("chart", 0) + 1
        elif method == "addTable":
            facts.element_types["table"] = facts.element_types.get("table", 0) + 1

    def _handle_background_assignment(facts: SlideFacts, expr, eval_env: EvalEnv):
        props = _extract_object_properties_with_env(expr.right, eval_env)
        if props.get("path") or props.get("data"):
            facts.background_kind = "image"
        elif props.get("color") or props.get("fill"):
            facts.background_kind = "solid"

    def _build_helper_env(params, call_args, caller_eval_env):
        env: EvalEnv = dict(caller_eval_env)
        for i, param in enumerate(params):
            if i >= len(call_args):
                break
            arg = call_args[i]
            if param.type == "Identifier":
                if arg.type == "ObjectExpression":
                    arg_props = _extract_object_properties_with_env(arg, caller_eval_env)
                    env[param.name] = arg_props
                else:
                    val = _resolve_node(arg, caller_eval_env)
                    if val is not None:
                        env[param.name] = val
            elif param.type == "ObjectPattern":
                if arg.type == "ObjectExpression":
                    arg_props = _extract_object_properties_with_env(arg, caller_eval_env)
                    for prop in param.properties:
                        if prop.type == "Property":
                            key = (prop.key.name if prop.key.type == "Identifier"
                                   else prop.key.value)
                            if key in arg_props:
                                env[key] = arg_props[key]
        return env

    def _handle_call(call, slide_bindings, eval_env):
        callee = call.callee
        if callee.type == "MemberExpression" and callee.object.type == "Identifier":
            var_name = callee.object.name
            facts = slide_bindings.get(var_name)
            if facts is None:
                return None
            method = callee.property.name if callee.property.type == "Identifier" else None
            if method:
                _apply_method(facts, method, call, eval_env)
            return facts

        if callee.type == "Identifier" and callee.name in helpers:
            if not call.arguments:
                return None
            first_arg = call.arguments[0]
            if first_arg.type != "Identifier":
                return None
            facts = slide_bindings.get(first_arg.name)
            if facts is None:
                return None
            params, body = helpers[callee.name]
            helper_env = _build_helper_env(params[1:], call.arguments[1:], eval_env)
            helper_param_name = (params[0].name if params and params[0].type == "Identifier"
                                  else None)
            helper_slide_bindings = dict(slide_bindings)
            if helper_param_name and helper_param_name not in helper_slide_bindings:
                helper_slide_bindings[helper_param_name] = facts
            _walk_body(body, helper_slide_bindings, helper_env, is_block_scope=False)
            return facts

        return None

    def _walk_body(body, outer_slide_bindings, eval_env, *, is_block_scope=False):
        slide_bindings = dict(outer_slide_bindings) if is_block_scope else outer_slide_bindings
        local_eval_env = dict(eval_env)
        for n in body:
            if n is None:
                continue
            if n.type == "VariableDeclaration":
                for decl in n.declarations:
                    init = decl.init
                    if (init and init.type == "CallExpression"
                            and _is_add_slide_call(init)):
                        sf = _new_slide()
                        if decl.id.type == "Identifier":
                            slide_bindings[decl.id.name] = sf
                    elif init is not None and decl.id.type == "Identifier":
                        val = _resolve_node(init, local_eval_env)
                        if val is not None:
                            local_eval_env[decl.id.name] = val
                    elif init is not None and decl.id.type == "ObjectPattern":
                        rhs = _resolve_node(init, local_eval_env)
                        if isinstance(rhs, dict):
                            for prop in decl.id.properties:
                                if prop.type == "Property":
                                    key = (prop.key.name if prop.key.type == "Identifier"
                                           else prop.key.value)
                                    if key in rhs:
                                        local_eval_env[key] = rhs[key]
                        elif init.type == "ObjectExpression":
                            arg_props = _extract_object_properties_with_env(init, local_eval_env)
                            for prop in decl.id.properties:
                                if prop.type == "Property":
                                    key = (prop.key.name if prop.key.type == "Identifier"
                                           else prop.key.value)
                                    if key in arg_props:
                                        local_eval_env[key] = arg_props[key]
                continue
            if n.type == "BlockStatement":
                _walk_body(n.body, slide_bindings, local_eval_env, is_block_scope=True)
                continue
            if n.type == "ExpressionStatement":
                expr = n.expression
                if expr.type == "CallExpression":
                    _handle_call(expr, slide_bindings, local_eval_env)
                elif expr.type == "AssignmentExpression":
                    lhs = expr.left
                    if (lhs.type == "MemberExpression"
                            and lhs.object.type == "Identifier"
                            and lhs.property.type == "Identifier"
                            and lhs.property.name == "background"):
                        facts = slide_bindings.get(lhs.object.name)
                        if facts is not None:
                            _handle_background_assignment(facts, expr, local_eval_env)
                continue
            if n.type == "IfStatement":
                if n.consequent:
                    inner = getattr(n.consequent, "body", None)
                    if isinstance(inner, list):
                        _walk_body(inner, slide_bindings, local_eval_env)
                    elif n.consequent.type == "ExpressionStatement":
                        expr = n.consequent.expression
                        if expr.type == "CallExpression":
                            _handle_call(expr, slide_bindings, local_eval_env)
                if n.alternate:
                    inner = getattr(n.alternate, "body", None)
                    if isinstance(inner, list):
                        _walk_body(inner, slide_bindings, local_eval_env)
                continue
            inner = getattr(n, "body", None)
            if isinstance(inner, list):
                _walk_body(inner, slide_bindings, local_eval_env)

    _walk_body(tree.body, {}, {})
    return slides_list
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_analyser_js_parser.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/analyser/js_parser.py plugins/jack-tar-superpower-bridge/tests/test_analyser_js_parser.py
git commit -m "feat(bridge): JS-AST fallback parser with parse-never-execute contract"
```

---

### Task 9: SMARTART overlap verifier

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/analyser/overlap_verifier.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_analyser_overlap_verifier.py`

The verifier reports overlap warnings for SMARTART markers; the orchestrator (Task 10) decides what to do with them.

- [ ] **Step 1: Write the failing tests**

`tests/test_analyser_overlap_verifier.py`:

```python
import pytest
from pptx import Presentation
from pptx.util import Inches

from src.analyser.overlap_verifier import find_overlaps
from src.slide_facts import SlideFacts, Marker, OverlapWarning


def _build_deck_with_smartart_marker_and_text(tmp_path, *, overlap: bool):
    from pptx.util import Emu
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    # Marker rectangle at (1in, 1in, 5in, 3in)
    marker = slide.shapes.add_shape(
        1,  # MSO_SHAPE.RECTANGLE
        Inches(1), Inches(1), Inches(5), Inches(3),
    )
    marker.name = "SMARTART:three-pillars"
    # Body text — overlap if requested
    if overlap:
        body = slide.shapes.add_textbox(Inches(2), Inches(2), Inches(2), Inches(0.5))
    else:
        body = slide.shapes.add_textbox(Inches(7), Inches(4), Inches(2), Inches(0.5))
    body.name = "Body 1"
    body.text_frame.text = "Hello"
    out = tmp_path / "deck.pptx"
    prs.save(out)
    return out


def test_overlap_detected_when_text_intersects_marker(tmp_path):
    deck = _build_deck_with_smartart_marker_and_text(tmp_path, overlap=True)
    warnings = find_overlaps(deck)
    assert len(warnings) == 1
    w = warnings[0]
    assert w.marker_id == "SMARTART:three-pillars"
    assert "Body 1" in w.overlapping_shape_names


def test_no_overlap_returns_empty_list(tmp_path):
    deck = _build_deck_with_smartart_marker_and_text(tmp_path, overlap=False)
    warnings = find_overlaps(deck)
    assert warnings == []


def test_only_smartart_markers_trigger_check(tmp_path):
    """An IMAGE marker overlapping body text is NOT a warning — only SMARTART
    markers cause cosmetic bleed because they get replaced with a graphic."""
    from pptx.util import Inches
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    marker = slide.shapes.add_shape(1, Inches(1), Inches(1), Inches(5), Inches(3))
    marker.name = "IMAGE:foo"
    body = slide.shapes.add_textbox(Inches(2), Inches(2), Inches(2), Inches(0.5))
    body.name = "Body 1"
    body.text_frame.text = "x"
    out = tmp_path / "image.pptx"
    prs.save(out)
    assert find_overlaps(out) == []


def test_multiple_overlapping_shapes_collected(tmp_path):
    from pptx.util import Inches
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    marker = slide.shapes.add_shape(1, Inches(1), Inches(1), Inches(5), Inches(3))
    marker.name = "SMARTART:foo"
    for i in range(3):
        b = slide.shapes.add_textbox(Inches(2), Inches(1.5 + i*0.6), Inches(2), Inches(0.5))
        b.name = f"Body {i}"
        b.text_frame.text = "x"
    out = tmp_path / "many.pptx"
    prs.save(out)
    warnings = find_overlaps(out)
    assert len(warnings) == 1
    assert len(warnings[0].overlapping_shape_names) == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_analyser_overlap_verifier.py -v`
Expected: ImportError on `src.analyser.overlap_verifier`.

- [ ] **Step 3: Write the implementation**

`src/analyser/overlap_verifier.py`:

```python
"""SMARTART marker-adjacent text overlap detection.

For every slide carrying a SMARTART:* marker, check whether any other
shape's bounding box on that slide intersects the marker's geometry.
Spec Section 3.1 — converts the unverifiable brief-side promise into
an analyser-side check.
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation

from src.placeholder import parse_marker
from src.slide_facts import OverlapWarning


def _bbox(shape) -> tuple[int, int, int, int]:
    """Return (left, top, right, bottom) in EMU."""
    left = shape.left or 0
    top = shape.top or 0
    width = shape.width or 0
    height = shape.height or 0
    return left, top, left + width, top + height


def _intersects(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    al, at, ar, ab = a
    bl, bt, br, bb = b
    return not (ar <= bl or br <= al or ab <= bt or bb <= at)


def find_overlaps(pptx_path: Path | str) -> list[OverlapWarning]:
    """Return one OverlapWarning per slide whose SMARTART marker is overlapped
    by at least one other text-bearing shape."""
    prs = Presentation(str(pptx_path))
    warnings: list[OverlapWarning] = []
    for idx, slide in enumerate(prs.slides, start=1):
        smartart_markers: list[tuple[str, tuple[int, int, int, int]]] = []
        other_shapes: list[tuple[str, tuple[int, int, int, int]]] = []
        for shape in slide.shapes:
            name = getattr(shape, "name", "") or ""
            parsed = parse_marker(name)
            if parsed is not None and parsed[0] == "SMARTART":
                smartart_markers.append((f"{parsed[0]}:{parsed[1]}", _bbox(shape)))
                continue
            # Only consider shapes that bear text — empty rects don't bleed
            if shape.has_text_frame and shape.text_frame.text.strip():
                other_shapes.append((name, _bbox(shape)))
        for marker_id, marker_box in smartart_markers:
            overlap_names = [
                name for name, box in other_shapes if _intersects(marker_box, box)
            ]
            if overlap_names:
                warnings.append(OverlapWarning(
                    slide_index=idx,
                    marker_id=marker_id,
                    overlapping_shape_names=overlap_names,
                ))
    return warnings
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_analyser_overlap_verifier.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/analyser/overlap_verifier.py plugins/jack-tar-superpower-bridge/tests/test_analyser_overlap_verifier.py
git commit -m "feat(bridge): SMARTART overlap verifier (analyser-side enforceable contract)"
```

---

### Task 10: Analyser orchestrator (HYBRID OOXML + JS fallback)

**Files:**
- Modify: `plugins/jack-tar-superpower-bridge/src/analyser/__init__.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_analyser_orchestrator.py`

The orchestrator runs OOXML primary, falls back to JS only when OOXML returns zero markers AND build.js exists, runs the overlap verifier, dedupes via `find_duplicate_marker_ids`, and runs the security pre-flight.

- [ ] **Step 1: Write the failing tests**

`tests/test_analyser_orchestrator.py`:

```python
import pytest
from pathlib import Path

from src.analyser import analyse_pptx, AnalyserOptions
from src.slide_facts import AnalyserResult


def test_variant_a_uses_ooxml_only(seed_variant_a):
    result = analyse_pptx(seed_variant_a)
    assert isinstance(result, AnalyserResult)
    assert result.total_slides == 10
    assert result.total_markers == 8
    assert result.js_fallback_used is False


def test_variant_b_falls_back_to_js_when_buildjs_present(seed_variant_b):
    """Variant B's build.js sits alongside the .pptx; JS fallback should fire."""
    result = analyse_pptx(seed_variant_b)
    assert result.js_fallback_used is True
    assert result.total_markers >= 1


def test_no_buildjs_does_not_fall_back(seed_no_buildjs):
    result = analyse_pptx(seed_no_buildjs)
    # Control case has 1 named marker shape; OOXML finds it, no fallback needed
    assert result.js_fallback_used is False


def test_duplicate_marker_ids_surfaced(tmp_path):
    """Two slides both carrying IMAGE:foo must produce a duplicate warning."""
    from pptx import Presentation
    from pptx.util import Inches
    prs = Presentation()
    for _ in range(2):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        m = slide.shapes.add_shape(1, Inches(1), Inches(1), Inches(2), Inches(2))
        m.name = "IMAGE:foo"
    out = tmp_path / "dupes.pptx"
    prs.save(out)
    result = analyse_pptx(out)
    assert "IMAGE:foo" in result.duplicate_marker_ids


def test_overlap_warnings_collected_from_verifier(tmp_path):
    from pptx import Presentation
    from pptx.util import Inches
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    marker = slide.shapes.add_shape(1, Inches(1), Inches(1), Inches(5), Inches(3))
    marker.name = "SMARTART:foo"
    body = slide.shapes.add_textbox(Inches(2), Inches(2), Inches(2), Inches(0.5))
    body.text_frame.text = "x"
    out = tmp_path / "overlap.pptx"
    prs.save(out)
    result = analyse_pptx(out)
    assert len(result.overlap_warnings) == 1


def test_preflight_failure_propagates(tmp_path):
    """A .pptx that fails preflight must raise PptxPreflightError, not be silently passed."""
    from src.security import PptxPreflightError
    bad = tmp_path / "bad.pptx"
    bad.write_bytes(b"not a zip")
    with pytest.raises(PptxPreflightError):
        analyse_pptx(bad)


def test_analyser_options_disable_js_fallback(seed_variant_b):
    result = analyse_pptx(seed_variant_b, options=AnalyserOptions(enable_js_fallback=False))
    assert result.js_fallback_used is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_analyser_orchestrator.py -v`
Expected: ImportError on `analyse_pptx` from `src.analyser`.

- [ ] **Step 3: Write the implementation**

Replace `src/analyser/__init__.py` with:

```python
"""Analyser orchestrator — HYBRID OOXML + JS fallback + overlap verifier.

Orchestration order:
  1. preflight_pptx() — refuse oversized / suspicious files.
  2. parse_pptx() — OOXML primary path.
  3. If 0 markers AND build.js exists alongside, parse_js() to recover markers.
  4. find_overlaps() — SMARTART marker-adjacent text check.
  5. find_duplicate_marker_ids() — flag deck-wide identifier dupes.

Returns an AnalyserResult; raises PptxPreflightError on preflight failure
(propagated, not swallowed).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.analyser.js_parser import JsParseError, parse_js
from src.analyser.overlap_verifier import find_overlaps
from src.analyser.pptx_parser import parse_pptx
from src.placeholder import find_duplicate_marker_ids
from src.security import preflight_pptx
from src.slide_facts import AnalyserResult


@dataclass
class AnalyserOptions:
    enable_js_fallback: bool = True


def analyse_pptx(
    pptx_path: Path | str,
    *,
    options: AnalyserOptions | None = None,
) -> AnalyserResult:
    """Run the full HYBRID analyser pipeline against a .pptx.

    Raises PptxPreflightError if the file fails security pre-flight.
    """
    opts = options or AnalyserOptions()
    p = Path(pptx_path)

    # Step 1 — security pre-flight (propagates PptxPreflightError)
    preflight_pptx(p)

    # Step 2 — OOXML primary
    slides = parse_pptx(p)
    notes: list[str] = []
    js_fallback_used = False

    # Step 3 — JS fallback when OOXML found zero markers AND build.js exists
    total_markers = sum(len(s.markers) for s in slides)
    build_js = p.with_name("build.js")
    if (
        opts.enable_js_fallback
        and total_markers == 0
        and build_js.exists()
    ):
        try:
            js_facts = parse_js(build_js)
        except JsParseError as exc:
            notes.append(f"JS fallback failed; reporting no markers ({exc})")
        else:
            js_fallback_used = True
            # Merge JS-recovered markers onto matching slide indices.
            # If JS produces more or fewer slides than OOXML, align by index.
            for js_slide in js_facts:
                idx = js_slide.slide_index
                if 1 <= idx <= len(slides):
                    slides[idx - 1].markers = js_slide.markers
            notes.append(f"JS fallback recovered {sum(len(s.markers) for s in slides)} markers")

    # Step 4 — overlap verifier (only meaningful for slides with SMARTART markers)
    overlap_warnings = find_overlaps(p)

    # Step 5 — duplicate marker id detection
    duplicates = find_duplicate_marker_ids(slides)

    return AnalyserResult(
        slides=slides,
        duplicate_marker_ids=duplicates,
        overlap_warnings=overlap_warnings,
        js_fallback_used=js_fallback_used,
        notes=notes,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_analyser_orchestrator.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/analyser/__init__.py plugins/jack-tar-superpower-bridge/tests/test_analyser_orchestrator.py
git commit -m "feat(bridge): analyser orchestrator with HYBRID OOXML + JS fallback"
```

---

## Phase 3 — Bridge-brief skill (Phase 1 of design): Narrative Brief Architect persona + skill (3 tasks)

### Task 11: Narrative Brief Architect persona definition

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/agents/narrative-brief-architect.md`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_persona_definitions.py` (this test covers both personas — the second persona is added in Task 30)

- [ ] **Step 1: Write the failing test**

`tests/test_persona_definitions.py`:

```python
"""Structural validation of agent definitions in plugins/jack-tar-superpower-bridge/agents/."""
from pathlib import Path
import re

import pytest

PLUGIN_AGENTS_DIR = Path(__file__).resolve().parents[1] / "agents"


def _read_agent(name: str) -> str:
    return (PLUGIN_AGENTS_DIR / f"{name}.md").read_text()


def _frontmatter(content: str) -> dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def test_narrative_brief_architect_definition_exists():
    fm = _frontmatter(_read_agent("narrative-brief-architect"))
    assert fm["name"] == "narrative-brief-architect"
    assert fm["model"] == "sonnet"
    # Sonnet model required by persona contract — Tier 1 risk + bounded scope
    assert "description" in fm and len(fm["description"]) > 30


def test_narrative_brief_architect_says_objectName_not_name():
    text = _read_agent("narrative-brief-architect")
    assert "objectName" in text
    # Must NOT instruct using `name:` as PptxGenJS shape-name property
    assert "name: \"IMAGE:" not in text
    assert "name: \"SMARTART:" not in text
    assert "name: \"BG:" not in text


def test_narrative_brief_architect_lists_three_arc_options():
    text = _read_agent("narrative-brief-architect")
    arcs = ["Problem-Solution", "Hero", "Build-Up"]
    found = sum(1 for a in arcs if a in text)
    assert found >= 2


def test_narrative_brief_architect_describes_user_approval_gate():
    text = _read_agent("narrative-brief-architect")
    # Must state explicit user approval before saving creative-brief.md
    assert "approval" in text.lower() or "approve" in text.lower()
    assert "creative-brief.md" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_persona_definitions.py -v`
Expected: FileNotFoundError on the agent definition.

- [ ] **Step 3: Write the implementation**

`agents/narrative-brief-architect.md`:

```markdown
---
name: narrative-brief-architect
description: Phase 1 of the superpower bridge. Collaboratively transforms a topic + audience + duration into a structured creative brief that guides /pptx. Proposes narrative arcs with trade-offs, captures communication intent and visual personality, and emits placeholder instructions for the deck builder. Never saves without user approval.
model: sonnet
tools: Read
---

# Narrative Brief Architect

You are the Narrative Brief Architect — the AI Persona that runs Phase 1 of the superpower bridge. You take the user's topic, audience, and duration and produce a `creative-brief.md` that guides `/pptx` to build a structurally well-paced deck with placeholder markers where visual enrichment will live.

## Identity

| Field | Value |
|---|---|
| Persona ID | `ap-narrative-brief-architect` |
| Service ID | `bridge-narrative-brief-architect-ai` |
| Authority Model | Invoker (user approves the brief before save) |
| Risk Tier | 1 (text output, no execution, no file I/O outside session working directory) |
| Default Model | Sonnet |
| Confidence Minimum for autonomous progress | 0.7 |
| Escalation Target | the user (this persona has no upstream supervisor) |

## Three Questions of Delegation

**Q1 — What does this persona decide?**
Arc selection from a fixed typology (Problem-Solution, Hero's Journey, Build-Up-Reveal, Tension-Release, etc.). Communication intent framing (audience takeaway, tone, visual personality). Which kinds of slide content should carry placeholder markers and how many.

**Q2 — What could go wrong?**
A poorly-framed brief produces a structurally weak deck downstream. Recoverable — the brief can be rerun. No binary output is mutated.

**Q3 — Who is accountable?**
The user. The persona's output is advisory; `creative-brief.md` is only saved after explicit user sign-off. Accountability transfers at step 7 of the collaborative flow below.

## Process — collaborative flow

1. Take the user's input: topic, duration in minutes, audience.
2. Propose 2–3 candidate narrative arcs from the fixed typology with trade-offs and your recommendation. Examples to draw from: **Problem-Solution**, **Hero's Journey**, **Build-Up-Reveal**, **Tension-Release**.
3. Wait for the user to pick or adjust.
4. Ask about communication intent — what should the audience walk away knowing? Capture it as one specific takeaway.
5. Ask about visual personality — describe the visual feel (clean/minimal, bold/atmospheric, data-rich, cinematic; what palette mood; any metaphors).
6. Generate the brief in the format below and present it to the user for review.
7. If the user approves, save the brief to `creative-brief.md` in the current working directory. If they request changes, revise and re-present.

## Output format — `creative-brief.md`

The brief MUST contain three labelled sections plus a top-of-file metadata header. Use this exact structure (the bridge's parser depends on it):

```markdown
# Creative Brief

**Topic:** <topic>
**Audience:** <audience>
**Duration:** <N> min
**Confidentiality:** public | internal | restricted
**Budget cap:** $<X.XX>

## Section A — Narrative Architecture

**Arc:** <selected arc from typology>

<2–4 paragraphs of narrative pacing and emotional beats — where to build tension, where to pivot, where to land. NOT per-slide; describe the overall journey.>

## Section B — Communication & Visual Intent

**Audience takeaway:** <one specific sentence — the single thing the audience should walk away knowing>
**Tone:** <authoritative | conversational | provocative | inspiring | warm | confident — pick one or two>
**Visual personality:** <2–3 sentences. Describe palette mood, imagery style, any architectural / metaphorical anchors.>

## Section C — Placeholder Instructions

<Free-form instructions to the /pptx superpower describing the kinds of content that should carry markers. Mention IMAGE/SMARTART/BG marker types and rough counts. Do NOT enumerate per-slide markers — let /pptx decide where they go based on its content.>

### PptxGenJS API note

When emitting marker placeholders, use the `objectName` property on `addShape()`. PptxGenJS 4.0.1 silently drops the `name` property; `objectName` is the only key that survives into OOXML where the bridge reads it.

```javascript
slide.addShape(pres.shapes.RECTANGLE, {
  objectName: "IMAGE:agent-architecture",  // <-- objectName, not name
  x: 5.5, y: 1.5, w: 4, h: 3,
  fill: { color: "F0F0F0" },
  line: { color: "CCCCCC", width: 1, dashType: "dash" },
});
slide.addText("IMAGE:agent-architecture", {
  x: 5.5, y: 2.8, w: 4, h: 0.5,
  align: "center", color: "888888", fontSize: 14,
});
```
```

## Confidentiality tier — ASK if ambiguous

If the user has not stated confidentiality, ask explicitly. Do not default silently. The three tiers control downstream cloud-image behaviour:

- **public** — full Ollama-first → cloud escalation pipeline. Default for general talks, conference content, public material.
- **internal** — cloud escalation allowed but the bridge confirms before each first cloud call per run. Use for company-internal material with non-sensitive narrative.
- **restricted** — cloud disabled, Ollama-only. Use when the brief contains customer names, financials, unreleased product names, or any material that should not leave the local machine.

## Marker typology — what each marker buys

| Marker prefix | Purpose | Use when |
|--------------|---------|----------|
| `IMAGE:` | AI-generated illustration in a reserved rectangle | The slide benefits from a hero illustration alongside text |
| `SMARTART:` | Editable PowerPoint SmartArt graphic replacing bullet content | The slide has a process / hierarchy / cycle / list that would render better as a diagram |
| `BG:` | AI atmospheric background covering the whole slide | The slide is a section divider, opener, or emotional pivot point |

**Marker count discipline:** propose at most ~15% of the deck as marker-bearing slides. More than that and the deck feels template-generated.

## Identifier grammar

After the colon: lowercase letters, digits, hyphens, underscores only. `IMAGE:agent-architecture` ✓. `IMAGE:AgentArch` ✗.

The identifier semantics:
- For `IMAGE:` and `BG:` — descriptive slug (`IMAGE:agent-architecture`, `BG:dramatic-opening`).
- For `SMARTART:` — hint at the *subject*, not the catalog layout id (`SMARTART:three-pillars`, NOT `SMARTART:process1`). Layout selection is a separate step the bridge does in Phase 3 from the bullet content + item count.

Marker identifiers must be unique deck-wide. The Phase 3 analyser flags duplicates; if you are tempted to repeat one, use a more specific slug.

## Prohibited actions

- Do NOT write `creative-brief.md` without explicit user approval of the final draft.
- Do NOT embed per-slide prescriptions ("slide 3 should be IMAGE:foo"). Describe the *kinds* of slides that should carry markers; let /pptx decide.
- Do NOT specify `name:` as the PptxGenJS shape-name property in exemplar code — MUST use `objectName:` (Spike 1 finding; the entire downstream pipeline depends on it).
- Do NOT propose marker counts in excess of ~15% of total slides.
- Do NOT generate images, run /pptx, modify .pptx files, or read DeckContext / brand profiles. Your output is text only.

## Escalation triggers

- User cannot converge on a narrative arc after two proposal rounds → present all three options side-by-side with a trade-off table and let them pick.
- Topic ambiguous to the point that placeholder kinds cannot be determined → ask the user explicitly rather than guessing.
- Confidentiality tier ambiguous → ask the user to set it explicitly before proceeding.

## Measurement hooks

These are the metrics the `measurement.py` module records for this persona. Be aware of them so your output supports them:

- **Adherence rate** — does /pptx's output contain the marker types your brief specified? (Checked by the Phase 3 analyser; target ≥ 90% when you use `objectName`.)
- **Approval turn count** — how many revision rounds before user approves the brief? (Target ≤ 2.)
- **Structural completeness** — were all three brief sections present and non-trivial? (Target 100%.)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_persona_definitions.py::test_narrative_brief_architect_definition_exists plugins/jack-tar-superpower-bridge/tests/test_persona_definitions.py::test_narrative_brief_architect_says_objectName_not_name plugins/jack-tar-superpower-bridge/tests/test_persona_definitions.py::test_narrative_brief_architect_lists_three_arc_options plugins/jack-tar-superpower-bridge/tests/test_persona_definitions.py::test_narrative_brief_architect_describes_user_approval_gate -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/agents/narrative-brief-architect.md plugins/jack-tar-superpower-bridge/tests/test_persona_definitions.py
git commit -m "feat(bridge): Narrative Brief Architect persona definition"
```

---

### Task 12: `/bridge-brief` skill

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/skills/bridge-brief/SKILL.md`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_skill_bridge_brief.py`

The skill itself is thin orchestration — it dispatches the agent, captures the result, and writes via the `creative_brief.py` helpers.

- [ ] **Step 1: Write the failing test**

`tests/test_skill_bridge_brief.py`:

```python
"""Structural validation of the /bridge-brief skill manifest."""
from pathlib import Path
import re

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = PLUGIN_ROOT / "skills" / "bridge-brief" / "SKILL.md"


def _frontmatter(content: str) -> dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    out: dict[str, str] = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip()
    return out


def test_skill_exists():
    assert SKILL_PATH.exists()


def test_skill_frontmatter_valid():
    text = SKILL_PATH.read_text()
    fm = _frontmatter(text)
    assert fm["name"] == "bridge-brief"
    assert "description" in fm and len(fm["description"]) >= 40
    assert "argument-hint" in fm


def test_skill_invokes_narrative_brief_architect_agent():
    text = SKILL_PATH.read_text()
    assert "narrative-brief-architect" in text


def test_skill_writes_creative_brief_md():
    text = SKILL_PATH.read_text()
    assert "creative-brief.md" in text


def test_skill_uses_creative_brief_writer():
    text = SKILL_PATH.read_text()
    # Skill must call into the Python writer (not just produce loose markdown)
    assert "src.creative_brief" in text or "creative_brief" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_skill_bridge_brief.py -v`
Expected: 5 failures (file does not exist).

- [ ] **Step 3: Write the implementation**

`skills/bridge-brief/SKILL.md`:

```markdown
---
name: bridge-brief
description: Phase 1 of the superpower bridge — collaborative narrative pre-brief for the /pptx superpower. Dispatches the Narrative Brief Architect persona to propose arcs, capture communication intent, and produce a creative-brief.md that guides /pptx to build a well-structured deck with placeholder markers where visual enrichment will live.
argument-hint: "<topic>" [--duration <minutes>] [--audience "<audience>"] [--confidentiality public|internal|restricted] [--budget-cap <usd>]
allowed-tools: Bash(python *), Read, Skill, Agent
---

# /bridge-brief

Phase 1 of the superpower bridge workflow. The user invokes this skill, you collaboratively shape a creative brief, and you save the result to `creative-brief.md` for the user to hand to `/pptx`.

You are NOT the persona — you are the orchestrator. The Narrative Brief Architect persona does the creative reasoning; you handle dispatch, parsing, and file I/O.

## Parse arguments

Parse `$ARGUMENTS` as a single quoted topic followed by optional flags:

- **<topic>** (positional, required) — the talk topic, e.g. "AI agent architectures"
- **--duration <minutes>** (default: 20) — talk length in minutes
- **--audience "<audience>"** (default: "developers") — who the audience is
- **--confidentiality public|internal|restricted** (default: ask the user)
- **--budget-cap <usd>** (default: 1.00)

If `<topic>` is missing, prompt the user for it before dispatching the agent.

## Locate the plugin

```bash
PLUGIN_ROOT=$(python3 -c "
from pathlib import Path
import sys, os
if os.environ.get('JACK_TAR_SUPERPOWER_BRIDGE_ROOT'):
    print(os.environ['JACK_TAR_SUPERPOWER_BRIDGE_ROOT']); sys.exit()
home = Path.home()
for base in [home / '.claude' / 'plugins' / 'cache']:
    for p in base.rglob('jack-tar-superpower-bridge/.claude-plugin/plugin.json'):
        print(str(p.parent.parent)); sys.exit()
dev = Path.cwd() / 'plugins' / 'jack-tar-superpower-bridge'
if dev.exists():
    print(str(dev)); sys.exit()
print('NOT_FOUND')
" 2>/dev/null)
if [ -z "$PLUGIN_ROOT" ] || [ "$PLUGIN_ROOT" = "NOT_FOUND" ]; then
  echo "ERROR: jack-tar-superpower-bridge not found"; exit 1
fi
```

## Step 1 — confirm confidentiality if not supplied

If `--confidentiality` was not supplied, ask the user:

> The brief carries a confidentiality tier that controls whether Phase 3 image generation can use cloud providers:
>
> - **public** — full Ollama → cloud pipeline (default for conference content)
> - **internal** — cloud allowed but confirm before each first call (company-internal material)
> - **restricted** — cloud disabled, Ollama only (sensitive material)
>
> Which tier? (public / internal / restricted)

Capture the answer.

## Step 2 — dispatch the Narrative Brief Architect agent

Use the `Agent` tool with `subagent_type="narrative-brief-architect"`.

The dispatch prompt MUST contain the topic, duration, audience, confidentiality, and budget cap. Pass through every collaborative round — when the user requests a revision, dispatch a new agent turn including the prior draft and the revision request.

Example dispatch prompt:

```
Topic: AI agent architectures
Duration: 20 minutes
Audience: developers
Confidentiality: public
Budget cap: $1.00

Propose 2-3 narrative arcs with trade-offs and a recommendation. Wait for my choice before drafting Section A.
```

The agent runs in collaborative mode — it proposes, you relay to the user, the user picks or adjusts, you re-dispatch with the updated context. Loop until the user approves a complete draft. (Target: ≤ 2 revision rounds per the persona's measurement hooks.)

## Step 3 — show the draft to the user and request approval

When the agent returns a complete brief draft, present it to the user verbatim and ask:

> Here is the draft creative brief. Approve to save to `creative-brief.md`, or describe what to change.

If the user approves, proceed to Step 4. If they request changes, dispatch the agent again with the revision instructions.

## Step 4 — save via the Python writer

Once approved, parse the agent's draft markdown and write it via the bridge's writer (so format consistency is preserved across runs):

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<'PY'
from pathlib import Path
from src.creative_brief import parse_brief_markdown, write_brief_markdown
draft_text = open('/tmp/bridge-brief-draft.md').read()  # written by orchestrator from agent output
brief = parse_brief_markdown(draft_text)
write_brief_markdown(brief, Path.cwd() / 'creative-brief.md')
print("OK")
PY
```

Before running, write the agent's approved markdown to `/tmp/bridge-brief-draft.md` (or any session-temp path you choose) so the Python writer can parse and re-emit it in canonical form.

If `parse_brief_markdown` raises `CreativeBriefValidationError`, surface the error to the user — the agent's output is malformed; ask them to re-dispatch the agent.

## Step 5 — record measurement hooks

After writing the file, append a one-line entry to `creative-brief-measurement.jsonl` in the same directory:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<'PY'
from pathlib import Path
from src.measurement import record_brief_run
record_brief_run(
    cwd=Path.cwd(),
    approval_turns=$APPROVAL_TURNS,        # how many revision rounds you went through
    structural_complete=True,              # parse_brief_markdown succeeded
    confidentiality="$CONFIDENTIALITY",
)
PY
```

`$APPROVAL_TURNS` is the integer count of agent dispatches you ran before the user approved (1 if approved on first draft).

## Step 6 — report

Print a summary:

```
Creative brief saved to creative-brief.md
- Topic: <topic>
- Duration: <N> min
- Audience: <audience>
- Confidentiality: <tier>
- Budget cap: $<X.XX>
- Approval turns: <N>

Next: invoke /pptx with this brief as context. Then run /enrich-deck on the resulting .pptx.
```

Stop. Do NOT auto-invoke /pptx — that is a separate user step.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_skill_bridge_brief.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/skills/bridge-brief/SKILL.md plugins/jack-tar-superpower-bridge/tests/test_skill_bridge_brief.py
git commit -m "feat(bridge): /bridge-brief skill orchestration"
```

---

### Task 13: Measurement primitives — brief-run + enrichment-run recorders

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/measurement.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_measurement.py`

This implements caveat #3 (measurement instrumentation as P0). The two persona contracts list five measurement hooks total — three for Narrative Brief Architect, two for Enrichment Cohesion Reviewer (later wired up in Task 31). Plus we record cost ledger entries used by both the budget cap (caveat #6) and the report (Task 32).

- [ ] **Step 1: Write the failing tests**

`tests/test_measurement.py`:

```python
import json
from pathlib import Path

import pytest

from src.measurement import (
    MEASUREMENT_FILENAME,
    COST_LEDGER_FILENAME,
    record_brief_run,
    record_enrichment_run,
    record_cost_event,
    read_measurements,
    read_cost_ledger,
)


def test_record_brief_run_creates_file(tmp_path):
    record_brief_run(cwd=tmp_path, approval_turns=2, structural_complete=True,
                     confidentiality="public")
    f = tmp_path / MEASUREMENT_FILENAME
    assert f.exists()
    lines = f.read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["kind"] == "brief"
    assert entry["approval_turns"] == 2
    assert entry["structural_complete"] is True
    assert entry["confidentiality"] == "public"
    assert "timestamp" in entry


def test_brief_runs_append(tmp_path):
    record_brief_run(cwd=tmp_path, approval_turns=1, structural_complete=True,
                     confidentiality="public")
    record_brief_run(cwd=tmp_path, approval_turns=3, structural_complete=False,
                     confidentiality="internal")
    entries = read_measurements(tmp_path)
    assert len(entries) == 2
    assert entries[1]["approval_turns"] == 3


def test_record_enrichment_run_captures_personas(tmp_path):
    record_enrichment_run(
        cwd=tmp_path,
        adherence_rate=0.875,                # markers requested vs delivered
        first_pass_acceptance=True,           # cohesion reviewer didn't block
        slides_enriched=4,
        slides_total=10,
    )
    entries = read_measurements(tmp_path)
    assert len(entries) == 1
    e = entries[0]
    assert e["kind"] == "enrichment"
    assert e["adherence_rate"] == 0.875
    assert e["first_pass_acceptance"] is True
    assert e["slides_enriched"] == 4


def test_record_cost_event_writes_ledger(tmp_path):
    record_cost_event(cwd=tmp_path, kind="generation",
                       provider="nanobanana_flash", cost_usd=0.067,
                       slide_index=3, marker_id="IMAGE:foo")
    record_cost_event(cwd=tmp_path, kind="review",
                       provider="haiku", cost_usd=0.001,
                       slide_index=3, marker_id="IMAGE:foo")
    ledger = read_cost_ledger(tmp_path)
    assert len(ledger) == 2
    assert ledger[0]["kind"] == "generation"
    assert ledger[1]["kind"] == "review"
    total = sum(e["cost_usd"] for e in ledger)
    assert total == pytest.approx(0.068)


def test_cost_event_kinds_validated(tmp_path):
    with pytest.raises(ValueError, match="kind"):
        record_cost_event(cwd=tmp_path, kind="dance",
                           provider="x", cost_usd=0, slide_index=1, marker_id=None)


def test_read_returns_empty_when_no_file(tmp_path):
    assert read_measurements(tmp_path) == []
    assert read_cost_ledger(tmp_path) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_measurement.py -v`
Expected: ImportError on `src.measurement`.

- [ ] **Step 3: Write the implementation**

`src/measurement.py`:

```python
"""Measurement instrumentation for the bridge personas (caveat #3, P0).

Two record kinds emitted to a single newline-delimited JSON file:
  - brief    — one row per /bridge-brief run (approval_turns, structural_complete, confidentiality)
  - enrichment — one row per /enrich-deck run (adherence_rate, first_pass_acceptance, slides_enriched, slides_total)

Cost ledger is a separate file, one row per cloud event. The image_bridge
records both generation AND review events here (caveat #6: budget cap
covers review, not just generation).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MEASUREMENT_FILENAME = "bridge-measurements.jsonl"
COST_LEDGER_FILENAME = "bridge-cost-ledger.jsonl"

VALID_COST_KINDS = {"generation", "review"}
VALID_CONFIDENTIALITY = {"public", "internal", "restricted"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append(path: Path, entry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def record_brief_run(
    *,
    cwd: Path,
    approval_turns: int,
    structural_complete: bool,
    confidentiality: str,
) -> None:
    if confidentiality not in VALID_CONFIDENTIALITY:
        raise ValueError(f"confidentiality {confidentiality!r} not in {VALID_CONFIDENTIALITY}")
    _append(cwd / MEASUREMENT_FILENAME, {
        "kind": "brief",
        "timestamp": _now_iso(),
        "approval_turns": approval_turns,
        "structural_complete": structural_complete,
        "confidentiality": confidentiality,
    })


def record_enrichment_run(
    *,
    cwd: Path,
    adherence_rate: float,
    first_pass_acceptance: bool,
    slides_enriched: int,
    slides_total: int,
) -> None:
    _append(cwd / MEASUREMENT_FILENAME, {
        "kind": "enrichment",
        "timestamp": _now_iso(),
        "adherence_rate": adherence_rate,
        "first_pass_acceptance": first_pass_acceptance,
        "slides_enriched": slides_enriched,
        "slides_total": slides_total,
    })


def record_cost_event(
    *,
    cwd: Path,
    kind: str,
    provider: str,
    cost_usd: float,
    slide_index: int | None,
    marker_id: str | None,
) -> None:
    if kind not in VALID_COST_KINDS:
        raise ValueError(f"kind {kind!r} not in {VALID_COST_KINDS}")
    _append(cwd / COST_LEDGER_FILENAME, {
        "kind": kind,
        "timestamp": _now_iso(),
        "provider": provider,
        "cost_usd": cost_usd,
        "slide_index": slide_index,
        "marker_id": marker_id,
    })


def read_measurements(cwd: Path) -> list[dict[str, Any]]:
    p = cwd / MEASUREMENT_FILENAME
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def read_cost_ledger(cwd: Path) -> list[dict[str, Any]]:
    p = cwd / COST_LEDGER_FILENAME
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_measurement.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/measurement.py plugins/jack-tar-superpower-bridge/tests/test_measurement.py
git commit -m "feat(bridge): measurement instrumentation (caveat #3 P0) + cost ledger"
```

---

## Phase 4 — Image bridge (4 tasks: budget cap covering generation AND review, privacy tiering, draft/review cycle)

### Task 14: BudgetCap class with single hard ceiling for generation + review (caveat #6)

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/image_bridge.py` (skeleton with BudgetCap only — full draft cycle in Task 16)
- Test: `plugins/jack-tar-superpower-bridge/tests/test_image_bridge.py` (BudgetCap section only)

- [ ] **Step 1: Write the failing tests**

`tests/test_image_bridge.py` (BudgetCap-only section — full file populated in Task 16):

```python
import pytest

from src.image_bridge import BudgetCap, BudgetExhaustedError


def test_budget_cap_initial_state():
    cap = BudgetCap(usd=1.00)
    assert cap.spent == 0.0
    assert cap.remaining == 1.00
    assert cap.can_afford(0.50) is True


def test_charge_generation_deducts_from_remaining():
    cap = BudgetCap(usd=1.00)
    cap.charge(kind="generation", provider="nanobanana_flash", cost_usd=0.067)
    assert cap.spent == pytest.approx(0.067)
    assert cap.remaining == pytest.approx(0.933)


def test_charge_review_also_deducts():
    """Caveat #6 — budget cap MUST cover image review, not just generation."""
    cap = BudgetCap(usd=1.00)
    cap.charge(kind="generation", provider="nanobanana_flash", cost_usd=0.067)
    cap.charge(kind="review", provider="haiku", cost_usd=0.005)
    assert cap.spent == pytest.approx(0.072)


def test_can_afford_returns_false_when_below_threshold():
    cap = BudgetCap(usd=0.10)
    cap.charge(kind="generation", provider="x", cost_usd=0.05)
    cap.charge(kind="generation", provider="x", cost_usd=0.04)
    assert cap.can_afford(0.02) is False
    assert cap.can_afford(0.005) is True


def test_charge_raises_when_overdraft():
    cap = BudgetCap(usd=0.10)
    with pytest.raises(BudgetExhaustedError, match="exceeds remaining"):
        cap.charge(kind="generation", provider="x", cost_usd=0.20)


def test_charge_invalid_kind_raises():
    cap = BudgetCap(usd=1.00)
    with pytest.raises(ValueError, match="kind"):
        cap.charge(kind="other", provider="x", cost_usd=0.01)


def test_history_records_each_charge():
    cap = BudgetCap(usd=1.00)
    cap.charge(kind="generation", provider="nanobanana_flash", cost_usd=0.067)
    cap.charge(kind="review", provider="haiku", cost_usd=0.005)
    assert len(cap.history) == 2
    assert cap.history[0].kind == "generation"
    assert cap.history[1].kind == "review"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_image_bridge.py -v`
Expected: ImportError on `src.image_bridge`.

- [ ] **Step 3: Write the implementation**

`src/image_bridge.py` (initial skeleton — extended in Task 16):

```python
"""Image bridge — draft/review cycle, budget tracking, privacy tiering.

Phase 4 task 14 of the implementation plan adds BudgetCap. Tasks 15
and 16 add the privacy tier gate and the full draft/review cycle.

Spec Section 3.3 + Security & Privacy. Caveat #6 — budget cap covers
both generation and review costs; the cheapest "next call" must be
affordable across both kinds.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


VALID_COST_KINDS = ("generation", "review")


class BudgetExhaustedError(RuntimeError):
    """Raised when the BudgetCap cannot fund a requested charge."""


@dataclass
class CostEvent:
    kind: str        # generation | review
    provider: str
    cost_usd: float


@dataclass
class BudgetCap:
    """Hard ceiling on cumulative cloud spend within a single /enrich-deck run.

    Both `kind="generation"` and `kind="review"` deduct from the same pool
    (caveat #6 — earlier drafts of the spec only counted generation).
    """
    usd: float
    spent: float = 0.0
    history: list[CostEvent] = field(default_factory=list)

    @property
    def remaining(self) -> float:
        return max(0.0, self.usd - self.spent)

    def can_afford(self, cost_usd: float) -> bool:
        return cost_usd <= self.remaining + 1e-9

    def charge(self, *, kind: str, provider: str, cost_usd: float) -> None:
        if kind not in VALID_COST_KINDS:
            raise ValueError(f"kind {kind!r} not in {VALID_COST_KINDS}")
        if not self.can_afford(cost_usd):
            raise BudgetExhaustedError(
                f"charge ${cost_usd:.4f} for {kind}/{provider} exceeds remaining "
                f"${self.remaining:.4f} (cap ${self.usd:.4f})"
            )
        self.spent += cost_usd
        self.history.append(CostEvent(kind=kind, provider=provider, cost_usd=cost_usd))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_image_bridge.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/image_bridge.py plugins/jack-tar-superpower-bridge/tests/test_image_bridge.py
git commit -m "feat(bridge): BudgetCap with generation+review charging (caveat #6)"
```

---

### Task 15: Privacy tier gate

**Files:**
- Modify: `plugins/jack-tar-superpower-bridge/src/image_bridge.py` (add `PrivacyTierGate`)
- Modify: `plugins/jack-tar-superpower-bridge/tests/test_image_bridge.py` (add gate tests)

- [ ] **Step 1: Append the failing tests**

Append to `tests/test_image_bridge.py`:

```python
from src.image_bridge import PrivacyTierGate, RestrictedTierError


def test_public_tier_allows_cloud_with_no_confirmation():
    gate = PrivacyTierGate(tier="public")
    assert gate.cloud_allowed() is True
    # public tier never asks for confirmation
    assert gate.requires_confirmation_before_cloud() is False


def test_internal_tier_requires_confirmation_before_first_cloud():
    gate = PrivacyTierGate(tier="internal")
    assert gate.cloud_allowed() is True
    assert gate.requires_confirmation_before_cloud() is True
    gate.mark_confirmation_received()
    # After confirmation, subsequent calls don't re-prompt
    assert gate.requires_confirmation_before_cloud() is False


def test_restricted_tier_blocks_cloud_outright():
    gate = PrivacyTierGate(tier="restricted")
    assert gate.cloud_allowed() is False


def test_restricted_tier_charge_attempt_raises():
    gate = PrivacyTierGate(tier="restricted")
    with pytest.raises(RestrictedTierError, match="restricted"):
        gate.guard_cloud_call(provider="nanobanana_flash")


def test_internal_tier_unconfirmed_raises():
    gate = PrivacyTierGate(tier="internal")
    with pytest.raises(RuntimeError, match="confirmation"):
        gate.guard_cloud_call(provider="nanobanana_flash")


def test_internal_tier_after_confirmation_passes():
    gate = PrivacyTierGate(tier="internal")
    gate.mark_confirmation_received()
    gate.guard_cloud_call(provider="nanobanana_flash")  # no raise


def test_invalid_tier_rejected():
    with pytest.raises(ValueError):
        PrivacyTierGate(tier="confidential")
```

- [ ] **Step 2: Run new tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_image_bridge.py -v`
Expected: 7 import-errors on `PrivacyTierGate`.

- [ ] **Step 3: Append the implementation**

Append to `src/image_bridge.py`:

```python
VALID_TIERS = ("public", "internal", "restricted")


class RestrictedTierError(RuntimeError):
    """Raised when a cloud call is attempted under the restricted tier."""


@dataclass
class PrivacyTierGate:
    """Privacy gate per the spec's Privacy tiering section.

    - public:     cloud allowed, no confirmation
    - internal:   cloud allowed, but the FIRST cloud call per run requires
                  the user to confirm (the orchestrator shows the prompt
                  and provider URL); subsequent calls in the same run are
                  pre-cleared
    - restricted: cloud disabled outright; only Ollama is allowed
    """
    tier: str
    confirmation_received: bool = False

    def __post_init__(self) -> None:
        if self.tier not in VALID_TIERS:
            raise ValueError(f"tier {self.tier!r} not in {VALID_TIERS}")

    def cloud_allowed(self) -> bool:
        return self.tier != "restricted"

    def requires_confirmation_before_cloud(self) -> bool:
        return self.tier == "internal" and not self.confirmation_received

    def mark_confirmation_received(self) -> None:
        self.confirmation_received = True

    def guard_cloud_call(self, *, provider: str) -> None:
        """Raise if the current state forbids a cloud call to `provider`."""
        if not self.cloud_allowed():
            raise RestrictedTierError(
                f"cloud provider {provider!r} forbidden under restricted tier"
            )
        if self.requires_confirmation_before_cloud():
            raise RuntimeError(
                f"internal tier requires user confirmation before first cloud call "
                f"to {provider!r}; orchestrator must call mark_confirmation_received()"
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_image_bridge.py -v`
Expected: 14 passed (7 BudgetCap + 7 PrivacyTierGate).

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/image_bridge.py plugins/jack-tar-superpower-bridge/tests/test_image_bridge.py
git commit -m "feat(bridge): PrivacyTierGate (public/internal/restricted)"
```

---

### Task 16: Draft/review cycle dispatcher

**Files:**
- Modify: `plugins/jack-tar-superpower-bridge/src/image_bridge.py` (add `ImageGenerationRequest` + `generate_with_review_cycle`)
- Modify: `plugins/jack-tar-superpower-bridge/tests/test_image_bridge.py` (add cycle tests)

The dispatcher is invocation-shaped — it takes a request, calls Ollama draft (free), dispatches the image-reviewer agent (which COSTS — caveat #6), iterates up to 3 times if refine, escalates to cloud only if budget allows + privacy tier allows. The actual Ollama and Claude agent calls are exposed as injectable callables so tests can mock them.

- [ ] **Step 1: Append the failing tests**

Append to `tests/test_image_bridge.py`:

```python
from pathlib import Path

from src.image_bridge import (
    ImageGenerationRequest,
    ImageGenerationResult,
    generate_with_review_cycle,
)
from src.measurement import COST_LEDGER_FILENAME, read_cost_ledger


def _make_req(tmp_path: Path) -> ImageGenerationRequest:
    out = tmp_path / "img.png"
    return ImageGenerationRequest(
        slide_index=3,
        marker_id="IMAGE:agent-architecture",
        marker_kind="IMAGE",
        prompt="A teal abstract architecture diagram",
        output_path=out,
        width=1024,
        height=576,
        brand_palette_hex=["#006B5E", "#0E1513"],
    )


def test_ollama_only_path_pass_first_iteration(tmp_path):
    cap = BudgetCap(usd=1.00)
    gate = PrivacyTierGate(tier="public")
    cwd = tmp_path

    def fake_ollama(req, attempt):
        req.output_path.write_bytes(b"OLLAMA")
        return {"path": str(req.output_path), "model": "x/z-image-turbo:fp8"}

    def fake_review(req, image_path, prior_summary):
        # cost for review is recorded by the cycle
        return {"verdict": "pass", "summary": "looks good", "cost_usd": 0.005,
                "issues": [], "strengths": [], "composition_notes": {}}

    def fake_refine(req, prior_prompt, reviewer_feedback, iteration):
        raise AssertionError("refine should not be called when verdict=pass")

    def fake_cloud(req, model, attempt):
        raise AssertionError("cloud should not be called in pure-ollama-pass case")

    result = generate_with_review_cycle(
        request=_make_req(tmp_path),
        budget=cap, privacy=gate, cwd=cwd,
        ollama_generate=fake_ollama,
        cloud_generate=fake_cloud,
        review=fake_review,
        refine_prompt=fake_refine,
    )
    assert result.status == "pass"
    assert result.tier_used == "ollama"
    # review cost recorded against the budget cap
    assert cap.spent == pytest.approx(0.005)
    # cost ledger contains one review event
    ledger = read_cost_ledger(cwd)
    assert len(ledger) == 1
    assert ledger[0]["kind"] == "review"


def test_ollama_three_refines_escalates_to_cloud_when_allowed(tmp_path):
    cap = BudgetCap(usd=1.00)
    gate = PrivacyTierGate(tier="public")
    calls = {"ollama": 0, "review": 0, "cloud": 0, "refine": 0}

    def fake_ollama(req, attempt):
        calls["ollama"] += 1
        req.output_path.write_bytes(b"OLLAMA")
        return {"path": str(req.output_path), "model": "x/z-image-turbo:fp8"}

    def fake_review(req, image_path, prior_summary):
        calls["review"] += 1
        # First 3 reviews refine; 4th (cloud Flash) passes
        if calls["review"] < 4:
            return {"verdict": "refine", "summary": "garbled text",
                    "cost_usd": 0.005, "issues": ["garbled"], "strengths": [],
                    "composition_notes": {}}
        return {"verdict": "pass", "summary": "great", "cost_usd": 0.005,
                "issues": [], "strengths": [], "composition_notes": {}}

    def fake_refine(req, prior_prompt, reviewer_feedback, iteration):
        calls["refine"] += 1
        return prior_prompt + " (refined)"

    def fake_cloud(req, model, attempt):
        calls["cloud"] += 1
        req.output_path.write_bytes(b"CLOUD")
        return {"path": str(req.output_path), "model": model, "cost_usd": 0.067}

    result = generate_with_review_cycle(
        request=_make_req(tmp_path),
        budget=cap, privacy=gate, cwd=tmp_path,
        ollama_generate=fake_ollama,
        cloud_generate=fake_cloud,
        review=fake_review,
        refine_prompt=fake_refine,
    )
    assert calls["ollama"] == 3                # max 3 free Ollama iterations
    assert calls["cloud"] >= 1                  # at least one cloud call
    assert result.status == "pass"
    assert result.tier_used.startswith("cloud") or result.tier_used == "nanobanana_flash"


def test_restricted_tier_blocks_cloud_escalation(tmp_path):
    cap = BudgetCap(usd=1.00)
    gate = PrivacyTierGate(tier="restricted")

    def fake_ollama(req, attempt):
        req.output_path.write_bytes(b"x")
        return {"path": str(req.output_path), "model": "x/z-image-turbo:fp8"}

    def fake_review(req, image_path, prior_summary):
        return {"verdict": "refine", "summary": "x", "cost_usd": 0.005,
                "issues": ["x"], "strengths": [], "composition_notes": {}}

    def fake_refine(req, prior_prompt, reviewer_feedback, iteration):
        return prior_prompt

    def fake_cloud(*args, **kw):
        raise AssertionError("cloud must not be called under restricted tier")

    result = generate_with_review_cycle(
        request=_make_req(tmp_path),
        budget=cap, privacy=gate, cwd=tmp_path,
        ollama_generate=fake_ollama,
        cloud_generate=fake_cloud,
        review=fake_review,
        refine_prompt=fake_refine,
    )
    assert result.status == "accepted_with_issues"
    assert result.tier_used == "ollama"


def test_budget_exhaustion_halts_escalation(tmp_path):
    """If the budget runs out, the cycle stops and reports — no overdraft."""
    cap = BudgetCap(usd=0.05)         # only enough for ~5 reviews
    gate = PrivacyTierGate(tier="public")

    def fake_ollama(req, attempt):
        req.output_path.write_bytes(b"x")
        return {"path": str(req.output_path), "model": "x/z-image-turbo:fp8"}

    def fake_review(req, image_path, prior_summary):
        return {"verdict": "refine", "summary": "x", "cost_usd": 0.01,
                "issues": ["x"], "strengths": [], "composition_notes": {}}

    def fake_refine(req, prior_prompt, reviewer_feedback, iteration):
        return prior_prompt

    def fake_cloud(req, model, attempt):
        req.output_path.write_bytes(b"c")
        return {"path": str(req.output_path), "model": model, "cost_usd": 0.067}

    result = generate_with_review_cycle(
        request=_make_req(tmp_path),
        budget=cap, privacy=gate, cwd=tmp_path,
        ollama_generate=fake_ollama,
        cloud_generate=fake_cloud,
        review=fake_review,
        refine_prompt=fake_refine,
    )
    # With cap=$0.05 and reviews=$0.01 each, Phase A burns $0.03 (3 reviews),
    # then Phase B's first Flash generation at $0.067 cannot be afforded — so
    # the cycle MUST return halted_budget specifically (not accepted_with_issues).
    assert result.status == "halted_budget"
    # Cap was respected
    assert cap.spent <= cap.usd + 1e-9


def test_phase_b_review_charge_unconditional_halts_on_overdraft(tmp_path):
    """Caveat #6 (regression guard) — if Phase B Flash generation succeeds but
    the review can't be charged, the cycle MUST halt before allowing Pro
    escalation on an unpaid verdict."""
    # Budget = exactly enough for 3 Ollama reviews ($0.015) + ONE Flash gen
    # ($0.067) = $0.082, plus a tiny margin to cross over Phase A. The Flash
    # review at $0.005 must NOT be affordable after the gen charge.
    cap = BudgetCap(usd=0.085)
    gate = PrivacyTierGate(tier="public")

    def fake_ollama(req, attempt):
        req.output_path.write_bytes(b"x")
        return {"path": str(req.output_path), "model": "x/z-image-turbo:fp8"}

    def fake_review(req, image_path, prior_summary):
        return {"verdict": "refine", "summary": "x", "cost_usd": 0.005,
                "issues": ["x"], "strengths": [], "composition_notes": {}}

    def fake_refine(req, prior_prompt, reviewer_feedback, iteration):
        return prior_prompt

    pro_called = {"n": 0}

    def fake_cloud(req, model, attempt):
        if "pro" in model:
            pro_called["n"] += 1
        req.output_path.write_bytes(b"c")
        return {"path": str(req.output_path), "model": model,
                 "cost_usd": 0.067 if "flash" in model else 0.134}

    result = generate_with_review_cycle(
        request=_make_req(tmp_path),
        budget=cap, privacy=gate, cwd=tmp_path,
        ollama_generate=fake_ollama,
        cloud_generate=fake_cloud,
        review=fake_review,
        refine_prompt=fake_refine,
    )
    assert result.status == "halted_budget"
    assert result.tier_used == "nanobanana_flash"  # halted in Phase B, not Phase A
    assert pro_called["n"] == 0, "Pro must not be called when Phase B review unaffordable"
```

- [ ] **Step 2: Run new tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_image_bridge.py -v`
Expected: ImportError on `ImageGenerationRequest` / `generate_with_review_cycle`.

- [ ] **Step 3: Append the implementation**

Append to `src/image_bridge.py`:

```python
from pathlib import Path
from typing import Callable, Optional

from src.measurement import record_cost_event


# ---------------------------------------------------------------------------
# Cycle data shapes
# ---------------------------------------------------------------------------

@dataclass
class ImageGenerationRequest:
    slide_index: int
    marker_id: str
    marker_kind: str          # IMAGE | BG
    prompt: str               # initial prompt; refined during the cycle
    output_path: Path
    width: int
    height: int
    brand_palette_hex: list[str] = field(default_factory=list)


@dataclass
class ImageGenerationResult:
    status: Literal["pass", "accepted_with_issues", "halted_budget", "halted_restricted"]
    tier_used: str            # ollama | nanobanana_flash | nanobanana_pro
    final_prompt: str
    iterations: int           # total review iterations performed
    final_summary: str        # last reviewer summary (the only thing the orchestrator keeps)
    review_costs_usd: float   # cumulative review cost
    generation_costs_usd: float  # cumulative generation cost (Ollama=0)


# Callables — injected so tests can mock without touching real models
OllamaGenerator = Callable[[ImageGenerationRequest, int], dict]
CloudGenerator = Callable[[ImageGenerationRequest, str, int], dict]
Reviewer = Callable[[ImageGenerationRequest, Path, str], dict]
PromptRefiner = Callable[[ImageGenerationRequest, str, dict, int], str]


def generate_with_review_cycle(
    *,
    request: ImageGenerationRequest,
    budget: BudgetCap,
    privacy: PrivacyTierGate,
    cwd: Path,
    ollama_generate: OllamaGenerator,
    cloud_generate: CloudGenerator,
    review: Reviewer,
    refine_prompt: PromptRefiner,
    max_ollama_iterations: int = 3,
    max_cloud_flash_iterations: int = 3,
) -> ImageGenerationResult:
    """Run the spec's draft/review cycle for one image.

    Step structure (Spec Section 3.3):
      Phase A — Ollama drafts: up to 3 free iterations; review each; refine prompt
      Phase B — Cloud Flash: only if Ollama didn't pass and privacy + budget allow;
                up to 3 Flash iterations with prompt refinement
      Phase C — Cloud Pro: ONE shot if Flash converged on a passing prompt

    Both generation AND review costs are charged against `budget` (caveat #6).
    """
    prompt = request.prompt
    iterations = 0
    last_summary = ""
    review_cost_total = 0.0
    gen_cost_total = 0.0
    last_reviewer_feedback: dict = {}

    # --- Phase A: Ollama drafts (free generation; review still costs) -------
    for attempt in range(1, max_ollama_iterations + 1):
        ollama_generate(request, attempt)
        iterations += 1
        verdict_payload = review(request, request.output_path, last_summary)
        review_cost = float(verdict_payload.get("cost_usd", 0.0))
        if not budget.can_afford(review_cost):
            # We reviewed but cannot pay — refuse to charge (overdraft)
            # and return what we have.
            return ImageGenerationResult(
                status="halted_budget", tier_used="ollama",
                final_prompt=prompt, iterations=iterations,
                final_summary=verdict_payload.get("summary", "halted before charging"),
                review_costs_usd=review_cost_total,
                generation_costs_usd=gen_cost_total,
            )
        budget.charge(kind="review", provider="haiku", cost_usd=review_cost)
        record_cost_event(cwd=cwd, kind="review", provider="haiku",
                           cost_usd=review_cost,
                           slide_index=request.slide_index,
                           marker_id=request.marker_id)
        review_cost_total += review_cost
        last_summary = verdict_payload.get("summary", "")
        last_reviewer_feedback = verdict_payload
        if verdict_payload.get("verdict") == "pass":
            return ImageGenerationResult(
                status="pass", tier_used="ollama",
                final_prompt=prompt, iterations=iterations,
                final_summary=last_summary,
                review_costs_usd=review_cost_total,
                generation_costs_usd=gen_cost_total,
            )
        # refine for next attempt
        prompt = refine_prompt(request, prompt, last_reviewer_feedback, attempt)
        request.prompt = prompt

    # --- Phase A failed; check if we may escalate to cloud --------------
    if not privacy.cloud_allowed():
        return ImageGenerationResult(
            status="halted_restricted", tier_used="ollama",
            final_prompt=prompt, iterations=iterations,
            final_summary=last_summary,
            review_costs_usd=review_cost_total,
            generation_costs_usd=gen_cost_total,
        )
    if privacy.requires_confirmation_before_cloud():
        # Orchestrator must mark confirmation; treat unconfirmed as halt
        return ImageGenerationResult(
            status="accepted_with_issues", tier_used="ollama",
            final_prompt=prompt, iterations=iterations,
            final_summary=last_summary + " (cloud escalation pending user confirmation)",
            review_costs_usd=review_cost_total,
            generation_costs_usd=gen_cost_total,
        )

    # --- Phase B: Cloud Flash with prompt refinement -------------------
    flash_model = "gemini-3.1-flash-image-preview"
    flash_cost = 0.067
    for flash_attempt in range(1, max_cloud_flash_iterations + 1):
        if not budget.can_afford(flash_cost):
            return ImageGenerationResult(
                status="halted_budget", tier_used="ollama",
                final_prompt=prompt, iterations=iterations,
                final_summary=last_summary,
                review_costs_usd=review_cost_total,
                generation_costs_usd=gen_cost_total,
            )
        gen_payload = cloud_generate(request, flash_model, flash_attempt)
        gen_cost = float(gen_payload.get("cost_usd", flash_cost))
        budget.charge(kind="generation", provider="nanobanana_flash", cost_usd=gen_cost)
        record_cost_event(cwd=cwd, kind="generation", provider="nanobanana_flash",
                           cost_usd=gen_cost,
                           slide_index=request.slide_index,
                           marker_id=request.marker_id)
        gen_cost_total += gen_cost
        iterations += 1
        verdict_payload = review(request, request.output_path, last_summary)
        review_cost = float(verdict_payload.get("cost_usd", 0.0))
        # Caveat #6 — review charge MUST be unconditional.
        # If we cannot afford the review, we have already paid for the
        # generation; halt cleanly so callers cannot escalate to Pro on
        # an unpaid verdict.
        if not budget.can_afford(review_cost):
            return ImageGenerationResult(
                status="halted_budget", tier_used="nanobanana_flash",
                final_prompt=prompt, iterations=iterations,
                final_summary=verdict_payload.get("summary",
                    "halted before charging Phase B review"),
                review_costs_usd=review_cost_total,
                generation_costs_usd=gen_cost_total,
            )
        budget.charge(kind="review", provider="haiku", cost_usd=review_cost)
        record_cost_event(cwd=cwd, kind="review", provider="haiku",
                           cost_usd=review_cost,
                           slide_index=request.slide_index,
                           marker_id=request.marker_id)
        review_cost_total += review_cost
        last_summary = verdict_payload.get("summary", "")
        last_reviewer_feedback = verdict_payload
        if verdict_payload.get("verdict") == "pass":
            # Optional Phase C — Pro single-shot when Flash converged on a proven prompt
            pro_model = "gemini-3-pro-image-preview"
            pro_cost = 0.134
            if budget.can_afford(pro_cost):
                gen_payload = cloud_generate(request, pro_model, 1)
                gen_cost = float(gen_payload.get("cost_usd", pro_cost))
                budget.charge(kind="generation", provider="nanobanana_pro", cost_usd=gen_cost)
                record_cost_event(cwd=cwd, kind="generation", provider="nanobanana_pro",
                                   cost_usd=gen_cost,
                                   slide_index=request.slide_index,
                                   marker_id=request.marker_id)
                gen_cost_total += gen_cost
                # Pro gets ONE shot — no re-review-and-refine.
                # Caveat #6 — review charge MUST be unconditional. If we cannot
                # afford the Pro review, the Flash version is the final accepted
                # output and we report halted_budget on the review (Pro generation
                # already happened).
                pro_verdict = review(request, request.output_path, last_summary)
                pro_review_cost = float(pro_verdict.get("cost_usd", 0.0))
                if not budget.can_afford(pro_review_cost):
                    return ImageGenerationResult(
                        status="halted_budget", tier_used="nanobanana_pro",
                        final_prompt=prompt, iterations=iterations + 1,
                        final_summary=pro_verdict.get("summary",
                            "halted before charging Pro review"),
                        review_costs_usd=review_cost_total,
                        generation_costs_usd=gen_cost_total,
                    )
                budget.charge(kind="review", provider="haiku", cost_usd=pro_review_cost)
                record_cost_event(cwd=cwd, kind="review", provider="haiku",
                                   cost_usd=pro_review_cost,
                                   slide_index=request.slide_index,
                                   marker_id=request.marker_id)
                review_cost_total += pro_review_cost
                return ImageGenerationResult(
                    status="pass", tier_used="nanobanana_pro",
                    final_prompt=prompt, iterations=iterations + 1,
                    final_summary=pro_verdict.get("summary", last_summary),
                    review_costs_usd=review_cost_total,
                    generation_costs_usd=gen_cost_total,
                )
            return ImageGenerationResult(
                status="pass", tier_used="nanobanana_flash",
                final_prompt=prompt, iterations=iterations,
                final_summary=last_summary,
                review_costs_usd=review_cost_total,
                generation_costs_usd=gen_cost_total,
            )
        prompt = refine_prompt(request, prompt, last_reviewer_feedback, flash_attempt)
        request.prompt = prompt

    return ImageGenerationResult(
        status="accepted_with_issues", tier_used="nanobanana_flash",
        final_prompt=prompt, iterations=iterations,
        final_summary=last_summary,
        review_costs_usd=review_cost_total,
        generation_costs_usd=gen_cost_total,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_image_bridge.py -v`
Expected: 19 passed (7 BudgetCap + 7 PrivacyTierGate + 5 cycle tests including the Phase B review-overdraft regression guard).

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/image_bridge.py plugins/jack-tar-superpower-bridge/tests/test_image_bridge.py
git commit -m "feat(bridge): draft/review cycle with budget+privacy enforcement"
```

---

### Task 17: Cycle state primitives for SKILL.md-driven iteration

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/cycle_state.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_cycle_state.py`

**Why this is not a "live callable factory":** The original draft of this task wrapped `generate_with_review_cycle` with subprocess shims for Ollama/cloud and stub callables for `review` and `refine_prompt`. That design was wrong — the cycle's `review` and `refine_prompt` callables need to dispatch the `image-reviewer` and `prompt-engineer` agents, but Python code running inside a SKILL.md heredoc cannot dispatch a Claude subagent (Agent dispatch is a harness operation, not a subprocess one). Stubbing them silently passes every image.

The fix: keep `generate_with_review_cycle` (Task 16) as the canonical reference implementation that tests exercise via injected callables. For the production run, the SKILL.md drives the loop step-by-step using small pure-functional state primitives in `cycle_state.py`. The SKILL.md owns the agent dispatches; Python owns the state transitions.

This pattern is already used elsewhere in the project — `src/conductor.py`'s `read_brief_defaults` is a pure helper the deck-conductor SKILL.md calls between user-interaction steps (see CLAUDE.md "deck-conductor invocation contract" note).

- [ ] **Step 1: Write the failing tests**

`tests/test_cycle_state.py`:

```python
import pytest
from pathlib import Path

from src.cycle_state import (
    CycleState,
    Phase,
    Decision,
    advance_after_review,
    should_escalate_to_cloud,
    is_terminal,
)
from src.image_bridge import BudgetCap, PrivacyTierGate, ImageGenerationRequest


def _req(tmp_path: Path) -> ImageGenerationRequest:
    return ImageGenerationRequest(
        slide_index=1, marker_id="IMAGE:foo", marker_kind="IMAGE",
        prompt="initial", output_path=tmp_path / "img.png",
        width=1024, height=576, brand_palette_hex=[],
    )


def test_initial_state_is_phase_a_attempt_1(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_A_OLLAMA, attempt=1)
    assert st.phase == Phase.PHASE_A_OLLAMA
    assert st.attempt == 1
    assert is_terminal(st) is False


def test_pass_verdict_in_phase_a_terminates_with_pass(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_A_OLLAMA, attempt=2)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "pass", "summary": "looks good"},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="public"),
    )
    assert decision.kind == "terminate_pass"
    assert decision.tier_used == "ollama"


def test_refine_in_phase_a_attempt_under_max_advances_to_next_attempt(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_A_OLLAMA, attempt=1)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "refine", "summary": "garbled",
                          "issues": ["x"], "strengths": [], "composition_notes": {}},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="public"),
    )
    assert decision.kind == "refine_and_retry"
    assert decision.next_state.phase == Phase.PHASE_A_OLLAMA
    assert decision.next_state.attempt == 2


def test_refine_in_phase_a_at_max_attempts_advances_to_phase_b_when_allowed(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_A_OLLAMA, attempt=3)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "refine", "summary": "x",
                          "issues": ["x"], "strengths": [], "composition_notes": {}},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="public"),
    )
    assert decision.kind == "escalate_to_cloud"
    assert decision.next_state.phase == Phase.PHASE_B_CLOUD_FLASH
    assert decision.next_state.attempt == 1


def test_refine_at_phase_a_max_with_restricted_tier_terminates_halt_restricted(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_A_OLLAMA, attempt=3)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "refine", "summary": "x",
                          "issues": ["x"], "strengths": [], "composition_notes": {}},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="restricted"),
    )
    assert decision.kind == "terminate_halt_restricted"


def test_refine_at_phase_a_max_with_internal_unconfirmed_terminates_halt_pending(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_A_OLLAMA, attempt=3)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "refine", "summary": "x",
                          "issues": ["x"], "strengths": [], "composition_notes": {}},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="internal"),  # not yet confirmed
    )
    assert decision.kind == "terminate_pending_confirmation"


def test_pass_verdict_in_phase_b_advances_to_phase_c_pro_when_affordable(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_B_CLOUD_FLASH, attempt=1)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "pass", "summary": "good"},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="public"),
    )
    assert decision.kind == "escalate_to_pro"
    assert decision.next_state.phase == Phase.PHASE_C_CLOUD_PRO
    assert decision.next_state.attempt == 1


def test_pass_verdict_in_phase_b_terminates_with_flash_when_pro_unaffordable(tmp_path):
    cap = BudgetCap(usd=0.20)
    cap.charge(kind="generation", provider="x", cost_usd=0.15)  # only 0.05 left
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_B_CLOUD_FLASH, attempt=2)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "pass", "summary": "good"},
        budget=cap,
        privacy=PrivacyTierGate(tier="public"),
    )
    assert decision.kind == "terminate_pass"
    assert decision.tier_used == "nanobanana_flash"


def test_refine_in_phase_b_at_max_iterations_terminates_accepted_with_issues(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_B_CLOUD_FLASH, attempt=3)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "refine", "summary": "still bad",
                          "issues": ["x"], "strengths": [], "composition_notes": {}},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="public"),
    )
    assert decision.kind == "terminate_accepted_with_issues"


def test_pass_verdict_in_phase_c_pro_terminates_with_pro(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_C_CLOUD_PRO, attempt=1)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "pass", "summary": "great"},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="public"),
    )
    assert decision.kind == "terminate_pass"
    assert decision.tier_used == "nanobanana_pro"


def test_should_escalate_to_cloud_false_under_restricted(tmp_path):
    assert should_escalate_to_cloud(
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="restricted"),
    ) is False


def test_should_escalate_to_cloud_false_when_budget_below_flash_cost(tmp_path):
    cap = BudgetCap(usd=0.05)  # below Flash cost ($0.067)
    assert should_escalate_to_cloud(
        budget=cap, privacy=PrivacyTierGate(tier="public"),
    ) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_cycle_state.py -v`
Expected: ImportError on `src.cycle_state`.

- [ ] **Step 3: Write the implementation**

`src/cycle_state.py`:

```python
"""Pure-functional cycle state primitives for the SKILL.md-driven loop.

The /enrich-deck SKILL.md drives the iteration step-by-step (because the
cycle's reviewer and prompt-refiner are Claude subagents, which only the
harness can dispatch). Between agent dispatches, the SKILL.md calls these
primitives to compute "what should I do next given the current state and
the agent's verdict?"

`generate_with_review_cycle` (image_bridge.py) remains the canonical
reference implementation for tests — it's exercised via injected
callables. Production runs go through this state machine instead.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.image_bridge import BudgetCap, PrivacyTierGate, ImageGenerationRequest


# Pricing constants — synchronised with image_bridge cycle
FLASH_GEN_COST_USD = 0.067
PRO_GEN_COST_USD = 0.134
TYPICAL_REVIEW_COST_USD = 0.005

MAX_PHASE_A_ATTEMPTS = 3
MAX_PHASE_B_ATTEMPTS = 3


class Phase(str, Enum):
    PHASE_A_OLLAMA = "phase_a_ollama"
    PHASE_B_CLOUD_FLASH = "phase_b_cloud_flash"
    PHASE_C_CLOUD_PRO = "phase_c_cloud_pro"
    TERMINAL = "terminal"


@dataclass
class CycleState:
    request: ImageGenerationRequest
    phase: Phase
    attempt: int                                 # 1-based within current phase


@dataclass
class Decision:
    """What the SKILL.md should do next.

    kind values:
      - refine_and_retry          → SKILL.md dispatches prompt-engineer in refine mode,
                                     then loops back to image generation in next_state
      - escalate_to_cloud         → SKILL.md begins Phase B Flash generation in next_state
      - escalate_to_pro           → SKILL.md does single Phase C Pro generation in next_state
      - terminate_pass            → SKILL.md keeps the current image; tier_used reports which tier
      - terminate_accepted_with_issues
      - terminate_halt_restricted
      - terminate_pending_confirmation
      - terminate_halt_budget
    """
    kind: str
    next_state: CycleState | None = None
    tier_used: str | None = None
    reason: str = ""


def is_terminal(state: CycleState) -> bool:
    return state.phase == Phase.TERMINAL


def should_escalate_to_cloud(*, budget: BudgetCap, privacy: PrivacyTierGate) -> bool:
    """Return True if the cycle CAN move from Phase A to Phase B."""
    if not privacy.cloud_allowed():
        return False
    if privacy.requires_confirmation_before_cloud():
        return False
    if not budget.can_afford(FLASH_GEN_COST_USD + TYPICAL_REVIEW_COST_USD):
        return False
    return True


def _phase_a_decision(
    state: CycleState, verdict: str, budget: BudgetCap, privacy: PrivacyTierGate,
) -> Decision:
    if verdict == "pass":
        return Decision(kind="terminate_pass", tier_used="ollama")
    # refine: more attempts left → loop in Phase A
    if state.attempt < MAX_PHASE_A_ATTEMPTS:
        return Decision(
            kind="refine_and_retry",
            next_state=CycleState(request=state.request, phase=Phase.PHASE_A_OLLAMA,
                                    attempt=state.attempt + 1),
        )
    # refine and at max attempts: try to escalate
    if not privacy.cloud_allowed():
        return Decision(kind="terminate_halt_restricted",
                         tier_used="ollama",
                         reason="restricted tier blocks cloud escalation")
    if privacy.requires_confirmation_before_cloud():
        return Decision(kind="terminate_pending_confirmation",
                         tier_used="ollama",
                         reason="internal tier requires user confirmation before cloud")
    if not budget.can_afford(FLASH_GEN_COST_USD + TYPICAL_REVIEW_COST_USD):
        return Decision(kind="terminate_halt_budget",
                         tier_used="ollama",
                         reason="budget cannot cover Phase B Flash gen + review")
    return Decision(
        kind="escalate_to_cloud",
        next_state=CycleState(request=state.request,
                                phase=Phase.PHASE_B_CLOUD_FLASH, attempt=1),
    )


def _phase_b_decision(
    state: CycleState, verdict: str, budget: BudgetCap, privacy: PrivacyTierGate,
) -> Decision:
    if verdict == "pass":
        # Optional Phase C only when budget allows the Pro generation + a review
        if budget.can_afford(PRO_GEN_COST_USD + TYPICAL_REVIEW_COST_USD):
            return Decision(
                kind="escalate_to_pro",
                next_state=CycleState(request=state.request,
                                        phase=Phase.PHASE_C_CLOUD_PRO, attempt=1),
            )
        return Decision(kind="terminate_pass", tier_used="nanobanana_flash")
    # refine
    if state.attempt < MAX_PHASE_B_ATTEMPTS:
        if not budget.can_afford(FLASH_GEN_COST_USD + TYPICAL_REVIEW_COST_USD):
            return Decision(kind="terminate_halt_budget",
                             tier_used="nanobanana_flash",
                             reason="budget exhausted before next Flash iteration")
        return Decision(
            kind="refine_and_retry",
            next_state=CycleState(request=state.request,
                                    phase=Phase.PHASE_B_CLOUD_FLASH,
                                    attempt=state.attempt + 1),
        )
    return Decision(kind="terminate_accepted_with_issues",
                     tier_used="nanobanana_flash",
                     reason="3 Flash iterations all returned refine")


def _phase_c_decision(verdict: str) -> Decision:
    if verdict == "pass":
        return Decision(kind="terminate_pass", tier_used="nanobanana_pro")
    return Decision(kind="terminate_accepted_with_issues",
                     tier_used="nanobanana_pro",
                     reason="Pro single-shot returned refine; flag for speaker")


def advance_after_review(
    *,
    state: CycleState,
    verdict_payload: dict[str, Any],
    budget: BudgetCap,
    privacy: PrivacyTierGate,
) -> Decision:
    """Compute the next decision after the SKILL.md has dispatched the reviewer
    agent and received its JSON envelope. Pure function — does not charge
    budget or mutate state. The SKILL.md is responsible for charging budget
    BEFORE calling advance_after_review (review charges are unconditional —
    caveat #6)."""
    verdict = verdict_payload.get("verdict")
    if verdict not in ("pass", "refine"):
        raise ValueError(f"verdict {verdict!r} not in (pass, refine)")
    if state.phase == Phase.PHASE_A_OLLAMA:
        return _phase_a_decision(state, verdict, budget, privacy)
    if state.phase == Phase.PHASE_B_CLOUD_FLASH:
        return _phase_b_decision(state, verdict, budget, privacy)
    if state.phase == Phase.PHASE_C_CLOUD_PRO:
        return _phase_c_decision(verdict)
    raise ValueError(f"cannot advance from terminal phase {state.phase}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_cycle_state.py -v`
Expected: 12 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/cycle_state.py plugins/jack-tar-superpower-bridge/tests/test_cycle_state.py
git commit -m "feat(bridge): cycle state primitives for SKILL.md-driven iteration"
```

---

## Phase 5 — SmartArt bridge (1 task; caveat #4 — bridge-side parsing)

### Task 18: SmartArt spec construction + carrier render (caveat #4 decision)

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/smartart_bridge.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_smartart_bridge.py`

**Caveat #4 decision (locked here):** the bridge does its OWN bullet-content → SmartArt spec parsing rather than reusing the deckhand `smartart-extractor` skill. Rationale:

1. The extractor is built around DeckContext + SlideOutline contracts that the bridge doesn't have (the bridge consumes /pptx output, not deckhand's outline.json).
2. The extractor expects `body_points` arrays; the bridge has slide text that has already been laid out by /pptx as multiple paragraphs in multiple text frames — extraction is a different shape.
3. The extractor handles pptx_native AND mermaid AND vega; the bridge only ever uses pptx_native.
4. A bridge-side parser is ~50 lines and lets us pin exactly the unified data shapes (`{items: [str]}` for flat-list, `{tree: {…}}` for hierarchical) that Spike 2 validated. Reuse would force us to vendor in or trace a much larger code path with shapes that don't match.

The decision is recorded as a code comment at the top of `smartart_bridge.py` so future readers don't relitigate it.

- [ ] **Step 1: Write the failing tests**

`tests/test_smartart_bridge.py`:

```python
import pytest
from pathlib import Path

from src.slide_facts import Marker, SlideFacts
from src.smartart_bridge import (
    select_layout_for_slide,
    build_spec_from_slide,
    render_carrier,
    SmartArtBridgeError,
)


def _slide_with_bullets(*items: str, marker_id="SMARTART:foo") -> SlideFacts:
    text = "Title line\n" + "\n".join(items)
    sf = SlideFacts(slide_index=1, text_content=text)
    sf.markers.append(Marker("SMARTART", marker_id.split(":")[1], 0, 0, 0, 0))
    return sf


def test_layout_selected_for_three_to_seven_items_uses_process1():
    slide = _slide_with_bullets("Discover", "Design", "Build", "Ship")
    layout_id = select_layout_for_slide(slide, marker_id="SMARTART:foo")
    assert layout_id == "process1"


def test_layout_selected_for_org_chart_marker_keyword():
    slide = SlideFacts(
        slide_index=1,
        text_content="Org chart\nCEO\n  CTO\n    Dev Lead\n  COO",
        markers=[Marker("SMARTART", "org-chart", 0, 0, 0, 0)],
    )
    layout_id = select_layout_for_slide(slide, marker_id="SMARTART:org-chart")
    assert layout_id == "orgChart1"


def test_layout_selected_for_cycle_keyword_in_marker_id():
    slide = _slide_with_bullets("Plan", "Execute", "Review", marker_id="SMARTART:cycle")
    layout_id = select_layout_for_slide(slide, marker_id="SMARTART:cycle")
    assert layout_id == "cycle2"


def test_build_spec_returns_flat_list_for_process1():
    slide = _slide_with_bullets("Discover", "Design", "Build")
    spec = build_spec_from_slide(slide, marker_id="SMARTART:foo", layout_id="process1")
    assert spec["graphic_type"] == "flowchart"
    assert spec["layout_id"] == "process1"
    assert spec["data"] == {"items": ["Discover", "Design", "Build"]}


def test_build_spec_items_are_plain_strings_not_dicts():
    """Spike 2 finding — flat-list items must be strings; dicts raise FlatListBuildError."""
    slide = _slide_with_bullets("a", "b", "c")
    spec = build_spec_from_slide(slide, marker_id="SMARTART:foo", layout_id="process1")
    for item in spec["data"]["items"]:
        assert isinstance(item, str)


def test_build_spec_org_chart_emits_tree():
    slide = SlideFacts(
        slide_index=1,
        text_content="CEO\n  CTO\n  COO",
        markers=[Marker("SMARTART", "org-chart", 0, 0, 0, 0)],
    )
    spec = build_spec_from_slide(slide, marker_id="SMARTART:org-chart", layout_id="orgChart1")
    assert spec["graphic_type"] == "org_chart"
    assert "tree" in spec["data"]
    assert spec["data"]["tree"]["title"] == "CEO"


def test_build_spec_strips_title_line_from_items():
    """If the marker text label appears as the first line, drop it from items."""
    slide = SlideFacts(
        slide_index=1,
        text_content="SMARTART:foo\nDiscover\nDesign\nBuild",
        markers=[Marker("SMARTART", "foo", 0, 0, 0, 0)],
    )
    spec = build_spec_from_slide(slide, marker_id="SMARTART:foo", layout_id="process1")
    assert spec["data"]["items"] == ["Discover", "Design", "Build"]


def test_render_carrier_writes_pptx(tmp_path):
    slide = _slide_with_bullets("Discover", "Design", "Build")
    spec = build_spec_from_slide(slide, marker_id="SMARTART:foo", layout_id="process1")
    carrier_path = render_carrier(spec, output_dir=tmp_path)
    assert carrier_path.exists()
    assert carrier_path.suffix == ".pptx"


def test_capacity_violation_raises(tmp_path):
    too_many = ["x"] * 50
    slide = _slide_with_bullets(*too_many)
    with pytest.raises(SmartArtBridgeError, match="capacity"):
        spec = build_spec_from_slide(slide, marker_id="SMARTART:foo", layout_id="process1")
        # The check is on build OR render
        render_carrier(spec, output_dir=tmp_path)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_smartart_bridge.py -v`
Expected: ImportError on `src.smartart_bridge`.

- [ ] **Step 3: Write the implementation**

`src/smartart_bridge.py`:

```python
"""SmartArt bridge — marker → spec → carrier .pptx.

Caveat #4 decision (do not relitigate without spec amendment):
the bridge does its OWN bullet → spec parsing rather than reusing the
deckhand `smartart-extractor` skill. Reasons:

  - The extractor consumes DeckContext + SlideOutline; the bridge has
    raw OOXML-extracted slide text instead.
  - The extractor handles pptx_native, mermaid, and vega; the bridge
    only ever uses pptx_native.
  - A bridge-side parser is ~50 lines and locks the data shapes that
    Spike 2 validated end-to-end.

If you change this decision, update spec Section 3.3 (SmartArt) and
this module's contract tests in test_smartart_bridge.py.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.msft_smartart_loader import load_msft_smartart_api
from src.slide_facts import SlideFacts


class SmartArtBridgeError(RuntimeError):
    """Raised on any spec-build or render error from the SmartArt bridge."""


# Layout selection heuristics. Marker identifier keywords are the primary signal,
# bullet count + indentation are the secondary signals. Catalog-aware extension
# (multi-candidate ranking) is deliberately out of v1 scope — see Caveat #4.
_KEYWORD_TO_LAYOUT = {
    "cycle": ("cycle", "cycle2"),
    "org": ("org_chart", "orgChart1"),
    "hierarchy": ("org_chart", "orgChart1"),
    "tree": ("org_chart", "orgChart1"),
    "venn": ("relationship", "venn1"),
    "pyramid": ("pyramid", "pyramid2"),
    "list": ("list", "list1"),
    "matrix": ("relationship", "matrix2"),
    "funnel": ("relationship", "funnel1"),
    "target": ("relationship", "target3"),
    "flow": ("flowchart", "process1"),
    "process": ("flowchart", "process1"),
    "step": ("flowchart", "process1"),
}

# Layout capacity caps (subset of catalog data; extended in v2).
_CAPACITY = {
    "process1": (2, 9),
    "cycle2": (3, 8),
    "orgChart1": (2, 25),
    "list1": (2, 9),
    "venn1": (2, 5),
    "pyramid2": (3, 5),
    "matrix2": (4, 4),
    "funnel1": (3, 6),
    "target3": (3, 5),
}


def _items_from_text(text_content: str, marker_id: str) -> list[str]:
    """Split slide text into items; drop the marker label line if present."""
    lines = [ln.strip() for ln in text_content.splitlines() if ln.strip()]
    # Drop leading lines that ARE the marker label
    while lines and lines[0] == marker_id:
        lines = lines[1:]
    # Drop a single non-bullet "title" line if it looks like a title (no leading dash/digit)
    if lines and not lines[0].startswith(("-", "•", "*")):
        # Heuristic: if the first line is short and the rest are clearly bullets,
        # treat the first as a title. Otherwise keep all lines.
        if len(lines) > 2 and len(lines[0]) < 40:
            lines = lines[1:]
    # Strip leading bullet glyphs
    return [ln.lstrip("-•* \t") for ln in lines]


def _detect_keyword(marker_id: str) -> tuple[str, str] | None:
    ident = marker_id.split(":", 1)[1].lower() if ":" in marker_id else marker_id.lower()
    for keyword, (graphic_type, layout_id) in _KEYWORD_TO_LAYOUT.items():
        if keyword in ident:
            return graphic_type, layout_id
    return None


def _is_hierarchical_text(text: str) -> bool:
    """Heuristic — text is hierarchical if at least one non-first line is indented."""
    lines = text.splitlines()
    return any(ln.startswith(("  ", "\t")) for ln in lines[1:])


def _parse_tree(text: str) -> dict[str, Any]:
    """Parse 2-space-indented text into a tree dict per pptx_native hierarchical schema.

    Format expected:
      Root
        Child A
          Grandchild
        Child B
    """
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        raise SmartArtBridgeError("hierarchical text is empty")
    # First line is root
    root = {"title": lines[0].strip(), "children": []}
    stack: list[tuple[int, dict]] = [(-2, root)]  # (indent, node)
    for line in lines[1:]:
        # measure indent (spaces only; tabs treated as 2 spaces)
        stripped = line.lstrip(" \t")
        indent = len(line) - len(stripped)
        if "\t" in line[:indent]:
            indent = indent  # treat tab-using files identically — both lift to depth
        node = {"title": stripped, "children": []}
        # Find parent: the top-of-stack whose indent < this indent
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if not stack:
            raise SmartArtBridgeError(f"no parent found for {stripped!r}")
        stack[-1][1]["children"].append(node)
        stack.append((indent, node))
    return root


def select_layout_for_slide(slide: SlideFacts, *, marker_id: str) -> str:
    """Pick a layout id from the catalog based on marker keyword + content shape."""
    detected = _detect_keyword(marker_id)
    if detected is not None:
        return detected[1]
    # Default by content shape
    if _is_hierarchical_text(slide.text_content):
        return "orgChart1"
    return "process1"


_GRAPHIC_TYPE_BY_LAYOUT = {
    "process1": "flowchart",
    "cycle2": "cycle",
    "orgChart1": "org_chart",
    "list1": "list",
    "venn1": "relationship",
    "pyramid2": "pyramid",
    "matrix2": "relationship",
    "funnel1": "relationship",
    "target3": "relationship",
}


def build_spec_from_slide(
    slide: SlideFacts, *, marker_id: str, layout_id: str
) -> dict[str, Any]:
    """Construct the spec the msft-smartart engine consumes."""
    graphic_type = _GRAPHIC_TYPE_BY_LAYOUT.get(layout_id, "flowchart")
    if layout_id == "orgChart1":
        # Hierarchical
        # Strip marker label if it's the first line
        text = slide.text_content
        lines = [ln for ln in text.splitlines() if ln.strip()]
        if lines and lines[0].strip() == marker_id:
            text = "\n".join(lines[1:])
        tree = _parse_tree(text)
        return {
            "graphic_type": graphic_type,
            "layout_id": layout_id,
            "data": {"tree": tree},
        }
    items = _items_from_text(slide.text_content, marker_id=marker_id)
    if not items:
        raise SmartArtBridgeError(f"no items extracted from slide {slide.slide_index}")
    cap = _CAPACITY.get(layout_id)
    if cap and not (cap[0] <= len(items) <= cap[1]):
        raise SmartArtBridgeError(
            f"layout {layout_id} capacity {cap} violated by {len(items)} items"
        )
    return {
        "graphic_type": graphic_type,
        "layout_id": layout_id,
        "data": {"items": items},
    }


def render_carrier(spec: dict[str, Any], *, output_dir: Path) -> Path:
    """Render a single-slide carrier .pptx via msft-smartart engine.render()."""
    output_dir.mkdir(parents=True, exist_ok=True)
    api = load_msft_smartart_api()
    try:
        result = api.engine.render(spec, output_dir)
    except Exception as exc:
        raise SmartArtBridgeError(f"engine.render failed: {exc}") from exc
    return Path(result.output_path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_smartart_bridge.py -v`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/smartart_bridge.py plugins/jack-tar-superpower-bridge/tests/test_smartart_bridge.py
git commit -m "feat(bridge): SmartArt bridge — marker→spec→carrier (caveat #4: bridge-side parsing)"
```

---

## Phase 6 — Enrichment ops (3 tasks lifted directly from Spike 2 prototypes, hardened with security primitives)

### Task 19: Op1 — background image (in-memory, allowlist-checked)

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/enrichment_ops/__init__.py`
- Create: `plugins/jack-tar-superpower-bridge/src/enrichment_ops/background.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_enrichment_ops_background.py`

This is Spike 2's `op1_background.py` rewritten to:
- Operate on an in-memory `Presentation` object (the transactional orchestrator owns save semantics — Task 22).
- Resolve `image_path` through `security.resolve_within_allowlist`.

- [ ] **Step 1: Write the failing tests**

`tests/test_enrichment_ops_background.py`:

```python
import shutil
from pathlib import Path

import pytest
from pptx import Presentation
from pptx.oxml.ns import qn

from src.enrichment_ops.background import apply_background_in_memory
from src.security import AllowedPathError


def test_applies_blipfill_and_removes_marker(tmp_path, seed_variant_a, placeholder_png):
    work = tmp_path / "deck.pptx"
    shutil.copy(seed_variant_a, work)
    img_dir = tmp_path / "generated"
    img_dir.mkdir()
    img = img_dir / "bg.png"
    shutil.copy(placeholder_png, img)

    prs = Presentation(str(work))
    apply_background_in_memory(
        prs=prs,
        slide_index_1based=1,
        image_path=img,
        marker_name="BG:title-hero-dark-grid",
        allowed_image_roots=[img_dir],
    )
    # Assert the in-memory tree carries a <p:bg> with a <a:blip>
    slide = prs.slides[0]
    cSld = slide.element.find(qn("p:cSld"))
    bg = cSld.find(qn("p:bg"))
    assert bg is not None
    blip = bg.find(".//" + qn("a:blip"))
    assert blip is not None
    # Marker shape removed
    names = [s.name for s in slide.shapes]
    assert "BG:title-hero-dark-grid" not in names


def test_image_path_outside_allowlist_raises(tmp_path, seed_variant_a, placeholder_png):
    work = tmp_path / "deck.pptx"
    shutil.copy(seed_variant_a, work)
    rogue = tmp_path / "rogue.png"
    shutil.copy(placeholder_png, rogue)

    prs = Presentation(str(work))
    allowed = tmp_path / "generated"
    allowed.mkdir()
    with pytest.raises(AllowedPathError):
        apply_background_in_memory(
            prs=prs, slide_index_1based=1, image_path=rogue,
            marker_name=None, allowed_image_roots=[allowed],
        )


def test_idempotent_when_no_existing_bg(tmp_path, seed_variant_a, placeholder_png):
    """Calling apply_background twice on the same slide replaces, doesn't stack."""
    work = tmp_path / "deck.pptx"
    shutil.copy(seed_variant_a, work)
    img_dir = tmp_path / "generated"; img_dir.mkdir()
    img = img_dir / "bg.png"; shutil.copy(placeholder_png, img)

    prs = Presentation(str(work))
    apply_background_in_memory(prs=prs, slide_index_1based=1, image_path=img,
                                marker_name=None, allowed_image_roots=[img_dir])
    apply_background_in_memory(prs=prs, slide_index_1based=1, image_path=img,
                                marker_name=None, allowed_image_roots=[img_dir])
    cSld = prs.slides[0].element.find(qn("p:cSld"))
    bgs = cSld.findall(qn("p:bg"))
    assert len(bgs) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_enrichment_ops_background.py -v`
Expected: ImportError on `src.enrichment_ops.background`.

- [ ] **Step 3: Write the implementation**

`src/enrichment_ops/__init__.py`:

```python
"""Per-op enrichment primitives operated against an in-memory Presentation.

The transactional orchestrator (src/enrichment.py) owns save semantics;
each op mutates a `Presentation` in place and lets the orchestrator
decide when (or whether) to write to disk.
"""
```

`src/enrichment_ops/background.py`:

```python
"""Op1 — apply an AI background image to a slide and remove its BG marker.

In-memory variant — the orchestrator's transactional gate (src/enrichment.py)
saves once after all ops succeed.
"""
from __future__ import annotations

from pathlib import Path

from lxml import etree
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.parts.image import Image, ImagePart

from src.security import resolve_within_allowlist


def _remove_existing_bg(cSld_elem) -> None:
    existing = cSld_elem.find(qn("p:bg"))
    if existing is not None:
        cSld_elem.remove(existing)


def _build_bg_element(rid: str):
    nsmap = {
        "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }
    xml = (
        f'<p:bg xmlns:p="{nsmap["p"]}" xmlns:a="{nsmap["a"]}" xmlns:r="{nsmap["r"]}">'
        "<p:bgPr>"
        '<a:blipFill dpi="0" rotWithShape="1">'
        f'<a:blip r:embed="{rid}"/>'
        "<a:srcRect/>"
        "<a:stretch><a:fillRect/></a:stretch>"
        "</a:blipFill>"
        "<a:effectLst/>"
        "</p:bgPr>"
        "</p:bg>"
    )
    return etree.fromstring(xml)


def apply_background_in_memory(
    *,
    prs,
    slide_index_1based: int,
    image_path: Path,
    marker_name: str | None,
    allowed_image_roots: list[Path],
) -> None:
    """Apply `image_path` as the background of slide `slide_index_1based`.

    `image_path` is resolved through the image-path allowlist.
    The BG marker shape (if `marker_name` provided) is removed from the slide.
    The Presentation `prs` is mutated in place; the caller saves.
    """
    safe_image = resolve_within_allowlist(image_path, allowed_roots=allowed_image_roots)
    if slide_index_1based < 1 or slide_index_1based > len(prs.slides):
        raise IndexError(
            f"slide {slide_index_1based} out of range (1..{len(prs.slides)})"
        )
    slide = prs.slides[slide_index_1based - 1]

    img = Image.from_file(str(safe_image))
    image_part = ImagePart.new(slide.part.package, img)
    rid = slide.part.relate_to(image_part, RT.IMAGE)

    cSld = slide.element.find(qn("p:cSld"))
    _remove_existing_bg(cSld)
    bg = _build_bg_element(rid)
    cSld.insert(0, bg)

    if marker_name:
        spTree = cSld.find(qn("p:spTree"))
        for sp in list(spTree):
            nvSpPr = sp.find(qn("p:nvSpPr"))
            if nvSpPr is None:
                continue
            cNvPr = nvSpPr.find(qn("p:cNvPr"))
            if cNvPr is not None and cNvPr.get("name") == marker_name:
                spTree.remove(sp)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_enrichment_ops_background.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/enrichment_ops/__init__.py plugins/jack-tar-superpower-bridge/src/enrichment_ops/background.py plugins/jack-tar-superpower-bridge/tests/test_enrichment_ops_background.py
git commit -m "feat(bridge): Op1 — in-memory background apply with allowlist guard"
```

---

### Task 20: Op2 — element image replacement (in-memory, allowlist-checked)

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/enrichment_ops/element_image.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_enrichment_ops_element_image.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_enrichment_ops_element_image.py`:

```python
import shutil
from pathlib import Path

import pytest
from pptx import Presentation

from src.enrichment_ops.element_image import replace_image_marker_in_memory
from src.security import AllowedPathError


def test_replaces_image_marker_with_picture_at_same_geometry(
    tmp_path, seed_variant_a, placeholder_png
):
    work = tmp_path / "deck.pptx"
    shutil.copy(seed_variant_a, work)
    img_dir = tmp_path / "generated"; img_dir.mkdir()
    img = img_dir / "elem.png"; shutil.copy(placeholder_png, img)

    prs = Presentation(str(work))
    # Find the IMAGE marker on Variant A
    target_marker: str | None = None
    target_geom = None
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.name and shape.name.startswith("IMAGE:"):
                target_marker = shape.name
                target_geom = (shape.left, shape.top, shape.width, shape.height)
                break
        if target_marker:
            break
    assert target_marker is not None, "Variant A must have at least one IMAGE marker"

    replace_image_marker_in_memory(
        prs=prs,
        marker_name=target_marker,
        image_path=img,
        allowed_image_roots=[img_dir],
    )

    # The marker shape is gone; a PICTURE shape now occupies the same geometry
    found_marker = False
    found_picture_at_geom = False
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.name == target_marker:
                found_marker = True
            if (shape.left, shape.top, shape.width, shape.height) == target_geom:
                if shape.shape_type is not None and shape.shape_type == 13:  # PICTURE
                    found_picture_at_geom = True
    assert not found_marker
    assert found_picture_at_geom


def test_unknown_marker_raises_lookuperror(tmp_path, seed_variant_a, placeholder_png):
    work = tmp_path / "deck.pptx"
    shutil.copy(seed_variant_a, work)
    img_dir = tmp_path / "generated"; img_dir.mkdir()
    img = img_dir / "x.png"; shutil.copy(placeholder_png, img)

    prs = Presentation(str(work))
    with pytest.raises(LookupError, match="not found"):
        replace_image_marker_in_memory(
            prs=prs, marker_name="IMAGE:nonexistent",
            image_path=img, allowed_image_roots=[img_dir],
        )


def test_image_outside_allowlist_raises(tmp_path, seed_variant_a, placeholder_png):
    work = tmp_path / "deck.pptx"
    shutil.copy(seed_variant_a, work)
    rogue = tmp_path / "rogue.png"; shutil.copy(placeholder_png, rogue)

    prs = Presentation(str(work))
    allowed = tmp_path / "generated"; allowed.mkdir()
    with pytest.raises(AllowedPathError):
        replace_image_marker_in_memory(
            prs=prs, marker_name="IMAGE:agent-architecture",
            image_path=rogue, allowed_image_roots=[allowed],
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_enrichment_ops_element_image.py -v`
Expected: ImportError on `src.enrichment_ops.element_image`.

- [ ] **Step 3: Write the implementation**

`src/enrichment_ops/element_image.py`:

```python
"""Op2 — replace a named IMAGE:* marker shape with an embedded picture.

In-memory variant — orchestrator owns save.
"""
from __future__ import annotations

from pathlib import Path

from src.security import resolve_within_allowlist


def replace_image_marker_in_memory(
    *,
    prs,
    marker_name: str,
    image_path: Path,
    allowed_image_roots: list[Path],
) -> None:
    safe_image = resolve_within_allowlist(image_path, allowed_roots=allowed_image_roots)
    target_slide = None
    target_shape = None
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.name == marker_name:
                target_slide = slide
                target_shape = shape
                break
        if target_shape is not None:
            break
    if target_shape is None:
        raise LookupError(f"shape {marker_name!r} not found on any slide")
    left = target_shape.left
    top = target_shape.top
    width = target_shape.width
    height = target_shape.height

    sp_elem = target_shape._element
    sp_elem.getparent().remove(sp_elem)

    target_slide.shapes.add_picture(str(safe_image), left, top, width=width, height=height)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_enrichment_ops_element_image.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/enrichment_ops/element_image.py plugins/jack-tar-superpower-bridge/tests/test_enrichment_ops_element_image.py
git commit -m "feat(bridge): Op2 — in-memory element image replacement with allowlist guard"
```

---

### Task 21: Op3 — SmartArt injection (post-save grafting via msft-smartart loader)

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/enrichment_ops/smartart.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_enrichment_ops_smartart.py`

Op3 is different from Op1/Op2: msft-smartart's `assembler_patch.inject` operates on a file (read-zip → mutate → write-zip), not on a `Presentation` object. The orchestrator handles this by saving the in-memory Presentation to a temp file FIRST, then calling Op3 against the saved temp. This wrapper exposes the file-based interface.

- [ ] **Step 1: Write the failing tests**

`tests/test_enrichment_ops_smartart.py`:

```python
import shutil
import zipfile
from pathlib import Path

import pytest
from pptx import Presentation

from src.enrichment_ops.smartart import inject_smartart_into_file
from src.smartart_bridge import build_spec_from_slide, render_carrier
from src.slide_facts import SlideFacts, Marker


def test_injects_smartart_replacing_marker(tmp_path, seed_variant_a):
    work = tmp_path / "deck.pptx"
    shutil.copy(seed_variant_a, work)
    # Find the SMARTART marker on the seed
    prs = Presentation(str(work))
    target_marker = None
    target_slide = None
    for idx, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            if shape.name and shape.name.startswith("SMARTART:"):
                target_marker = shape.name
                target_slide = idx
                break
        if target_marker:
            break
    assert target_marker is not None

    # Build a spec using bridge primitives
    sf = SlideFacts(slide_index=target_slide, text_content="Discover\nDesign\nBuild",
                     markers=[Marker("SMARTART", target_marker.split(":")[1], 0, 0, 0, 0)])
    spec = build_spec_from_slide(sf, marker_id=target_marker, layout_id="process1")
    carrier = render_carrier(spec, output_dir=tmp_path / "carriers")

    inject_smartart_into_file(
        host_pptx=work,
        slide_index_1based=target_slide,
        marker_name=target_marker,
        carrier_pptx=carrier,
    )
    # The host now contains diagram parts and no longer has the placeholder shape
    with zipfile.ZipFile(work) as zf:
        names = zf.namelist()
    assert any("ppt/diagrams/data" in n for n in names)


def test_missing_marker_raises(tmp_path, seed_variant_a):
    """If the carrier targets a marker that doesn't exist, we get an InjectionError."""
    work = tmp_path / "deck.pptx"
    shutil.copy(seed_variant_a, work)
    sf = SlideFacts(slide_index=1, text_content="a\nb\nc",
                     markers=[Marker("SMARTART", "ghost", 0, 0, 0, 0)])
    spec = build_spec_from_slide(sf, marker_id="SMARTART:ghost", layout_id="process1")
    carrier = render_carrier(spec, output_dir=tmp_path / "carriers")
    with pytest.raises(Exception):  # InjectionError from msft-smartart plugin
        inject_smartart_into_file(
            host_pptx=work, slide_index_1based=1,
            marker_name="SMARTART:ghost", carrier_pptx=carrier,
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_enrichment_ops_smartart.py -v`
Expected: ImportError on `src.enrichment_ops.smartart`.

- [ ] **Step 3: Write the implementation**

`src/enrichment_ops/smartart.py`:

```python
"""Op3 — graft a pptx_native SmartArt carrier into a host .pptx.

Unlike Op1 and Op2, this op operates on FILES (the msft-smartart
`assembler_patch.inject` reads + writes the host zip directly). The
transactional orchestrator handles the in-memory→temp-file save before
calling this op.
"""
from __future__ import annotations

from pathlib import Path

from src.msft_smartart_loader import load_msft_smartart_api


def inject_smartart_into_file(
    *,
    host_pptx: Path,
    slide_index_1based: int,
    marker_name: str,
    carrier_pptx: Path,
) -> None:
    api = load_msft_smartart_api()
    request = api.InjectionRequest(
        slide_number=slide_index_1based,
        carrier_pptx=Path(carrier_pptx),
        placeholder_name=marker_name,
    )
    api.inject(Path(host_pptx), [request])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_enrichment_ops_smartart.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/enrichment_ops/smartart.py plugins/jack-tar-superpower-bridge/tests/test_enrichment_ops_smartart.py
git commit -m "feat(bridge): Op3 — SmartArt injection via msft-smartart plugin loader"
```

---

## Phase 7 — Transactional enrichment orchestrator (1 task)

### Task 22: All-or-nothing enrichment with try/finally cleanup + atomic rename

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/enrichment.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_enrichment_transactional.py`

This is the spec's Section 3.4 step 4 — the in-memory accumulator + `try/except/finally` cleanup + atomic `os.replace()`.

- [ ] **Step 1: Write the failing tests**

`tests/test_enrichment_transactional.py`:

```python
import os
import shutil
from pathlib import Path

import pytest
from pptx import Presentation

from src.enrichment import (
    EnrichmentPlan,
    EnrichmentItem,
    apply_enrichment,
    EnrichmentApplyError,
)


def _plan_with(items, *, source, output):
    return EnrichmentPlan(source_pptx=source, output_pptx=output, items=items)


def test_no_enrichments_writes_clean_copy(tmp_path, seed_variant_a):
    out = tmp_path / "out.pptx"
    plan = _plan_with([], source=seed_variant_a, output=out)
    apply_enrichment(plan, allowed_image_roots=[tmp_path])
    assert out.exists()
    assert out.stat().st_size > 0


def test_background_only_succeeds(tmp_path, seed_variant_a, placeholder_png):
    img_dir = tmp_path / "generated"; img_dir.mkdir()
    img = img_dir / "bg.png"; shutil.copy(placeholder_png, img)
    out = tmp_path / "bg-only.pptx"
    items = [EnrichmentItem(slide_index=1, kind="background",
                              marker_name="BG:title-hero-dark-grid",
                              asset_path=img, action="apply")]
    plan = _plan_with(items, source=seed_variant_a, output=out)
    apply_enrichment(plan, allowed_image_roots=[img_dir])
    assert out.exists()


def test_failure_in_op2_leaves_no_output_file(tmp_path, seed_variant_a, placeholder_png):
    """Op2 raises LookupError on a missing marker → finally must remove the temp file
    AND must not produce the output file."""
    img_dir = tmp_path / "generated"; img_dir.mkdir()
    img = img_dir / "x.png"; shutil.copy(placeholder_png, img)
    out = tmp_path / "fail.pptx"
    items = [EnrichmentItem(slide_index=1, kind="image",
                              marker_name="IMAGE:does-not-exist",
                              asset_path=img, action="apply")]
    plan = _plan_with(items, source=seed_variant_a, output=out)
    with pytest.raises(EnrichmentApplyError):
        apply_enrichment(plan, allowed_image_roots=[img_dir])
    assert not out.exists()
    # No leftover temp file in the output directory
    leftovers = [p for p in tmp_path.iterdir()
                  if p.name.startswith("fail.pptx.tmp-")]
    assert leftovers == []


def test_smartart_skip_drops_op_but_leaves_other_enrichments(tmp_path, seed_variant_a, placeholder_png):
    img_dir = tmp_path / "generated"; img_dir.mkdir()
    img = img_dir / "bg.png"; shutil.copy(placeholder_png, img)
    out = tmp_path / "skip.pptx"
    items = [
        EnrichmentItem(slide_index=1, kind="background",
                        marker_name="BG:title-hero-dark-grid",
                        asset_path=img, action="apply"),
        EnrichmentItem(slide_index=4, kind="smartart",
                        marker_name="SMARTART:nonexistent",
                        asset_path=None, action="skip"),
    ]
    plan = _plan_with(items, source=seed_variant_a, output=out)
    apply_enrichment(plan, allowed_image_roots=[img_dir])
    assert out.exists()


def test_apply_clear_overlap_removes_overlapping_text_shapes(
    tmp_path, seed_variant_a
):
    """When user picks apply_clear_overlap, the orchestrator removes overlapping
    text shapes BEFORE injecting SmartArt."""
    # We'll use Variant A. Find the SMARTART marker.
    work_seed = tmp_path / "seed.pptx"
    shutil.copy(seed_variant_a, work_seed)
    prs = Presentation(str(work_seed))
    target = None
    target_slide_idx = None
    for idx, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            if shape.name and shape.name.startswith("SMARTART:"):
                target = shape.name
                target_slide_idx = idx
                break
        if target:
            break
    assert target is not None

    items = [
        EnrichmentItem(slide_index=target_slide_idx, kind="smartart",
                        marker_name=target, asset_path=None,
                        action="apply_clear_overlap",
                        smartart_spec={"graphic_type": "flowchart",
                                        "layout_id": "process1",
                                        "data": {"items": ["a", "b", "c"]}},
                        overlap_shape_names=["Body 1"]),  # may or may not match a real shape
    ]
    out = tmp_path / "cleared.pptx"
    plan = _plan_with(items, source=seed_variant_a, output=out)
    apply_enrichment(plan, allowed_image_roots=[tmp_path])
    assert out.exists()


def test_atomic_rename_no_partial_output(tmp_path, seed_variant_a, placeholder_png, monkeypatch):
    """If os.replace fails, the temp file should still be cleaned up AND the
    raised exception MUST be EnrichmentApplyError wrapping the OSError (not the
    raw OSError) so callers can catch a single error type."""
    from src import enrichment as mod
    img_dir = tmp_path / "generated"; img_dir.mkdir()
    img = img_dir / "bg.png"; shutil.copy(placeholder_png, img)
    out = tmp_path / "rename-fail.pptx"

    # Force os.replace to raise after the temp file is built
    def boom(src, dst):
        raise OSError("simulated rename failure")
    monkeypatch.setattr(mod.os, "replace", boom)

    items = [EnrichmentItem(slide_index=1, kind="background",
                              marker_name="BG:title-hero-dark-grid",
                              asset_path=img, action="apply")]
    plan = _plan_with(items, source=seed_variant_a, output=out)
    with pytest.raises(EnrichmentApplyError) as excinfo:
        apply_enrichment(plan, allowed_image_roots=[img_dir])
    # Must wrap the underlying OSError so callers can rely on a single error type
    assert isinstance(excinfo.value.__cause__, OSError)
    assert not out.exists()
    leftovers = [p for p in tmp_path.iterdir() if p.name.startswith(out.name + ".tmp-")]
    assert leftovers == []


def test_apply_enrichment_runs_preflight_first(tmp_path, monkeypatch):
    """Spec Security & Privacy gate — apply_enrichment MUST refuse a .pptx that
    fails pre-flight checks before opening it with python-pptx."""
    from src.security import PptxPreflightError
    bad = tmp_path / "bad.pptx"
    bad.write_bytes(b"not a zip")
    out = tmp_path / "out.pptx"
    plan = _plan_with([], source=bad, output=out)
    with pytest.raises(EnrichmentApplyError) as excinfo:
        apply_enrichment(plan, allowed_image_roots=[tmp_path])
    assert isinstance(excinfo.value.__cause__, PptxPreflightError)
    assert not out.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_enrichment_transactional.py -v`
Expected: ImportError on `src.enrichment`.

- [ ] **Step 3: Write the implementation**

`src/enrichment.py`:

```python
"""Transactional enrichment orchestrator.

Spec Section 3.4 step 4 — all-or-nothing application of selected
enrichments against a copy of the source .pptx. Phases:

  1. Open source as in-memory Presentation.
  2. Apply Op1 (backgrounds) and Op2 (element images) against the
     in-memory tree. For SMARTART items with action="apply_clear_overlap",
     remove the overlapping text shapes from the in-memory tree HERE
     (before any save).
  3. Save the in-memory tree to `<output>.tmp-<pid>` only if Phase 2
     succeeded for every requested op.
  4. Run Op3 (SmartArt injection) against the temp file. msft-smartart's
     inject() is itself read-all → mutate → write-fresh internally, so
     it preserves atomicity within a single call.
  5. Rename temp file to output via os.replace (atomic on POSIX).
  6. On any exception in Phases 2-5, the finally block removes the
     temp file and re-raises EnrichmentApplyError. No partial output
     ever reaches disk.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.oxml.ns import qn

from src.enrichment_ops.background import apply_background_in_memory
from src.enrichment_ops.element_image import replace_image_marker_in_memory
from src.enrichment_ops.smartart import inject_smartart_into_file
from src.smartart_bridge import render_carrier


VALID_KINDS = {"background", "image", "smartart"}
VALID_ACTIONS = {"apply", "apply_clear_overlap", "skip"}


class EnrichmentApplyError(RuntimeError):
    """Raised by apply_enrichment on any op failure or rename failure."""


@dataclass
class EnrichmentItem:
    slide_index: int
    kind: str                    # background | image | smartart
    marker_name: str             # full marker string (e.g. "IMAGE:foo")
    asset_path: Path | None      # image path for background/image; None for smartart
    action: str = "apply"        # apply | apply_clear_overlap | skip
    smartart_spec: dict[str, Any] | None = None  # required when kind="smartart" and action!="skip"
    overlap_shape_names: list[str] = field(default_factory=list)


@dataclass
class EnrichmentPlan:
    source_pptx: Path
    output_pptx: Path
    items: list[EnrichmentItem]


def _remove_overlapping_text_shapes(prs, slide_index_1based: int,
                                       overlap_names: list[str]) -> None:
    if not overlap_names:
        return
    if slide_index_1based < 1 or slide_index_1based > len(prs.slides):
        return
    slide = prs.slides[slide_index_1based - 1]
    cSld = slide.element.find(qn("p:cSld"))
    spTree = cSld.find(qn("p:spTree"))
    if spTree is None:
        return
    for sp in list(spTree):
        nvSpPr = sp.find(qn("p:nvSpPr"))
        if nvSpPr is None:
            continue
        cNvPr = nvSpPr.find(qn("p:cNvPr"))
        if cNvPr is not None and cNvPr.get("name") in overlap_names:
            spTree.remove(sp)


def _drop_marker_shape(prs, slide_index_1based: int, marker_name: str) -> None:
    slide = prs.slides[slide_index_1based - 1]
    cSld = slide.element.find(qn("p:cSld"))
    spTree = cSld.find(qn("p:spTree"))
    if spTree is None:
        return
    for sp in list(spTree):
        nvSpPr = sp.find(qn("p:nvSpPr"))
        if nvSpPr is None:
            continue
        cNvPr = nvSpPr.find(qn("p:cNvPr"))
        if cNvPr is not None and cNvPr.get("name") == marker_name:
            spTree.remove(sp)


def apply_enrichment(
    plan: EnrichmentPlan,
    *,
    allowed_image_roots: list[Path],
    carriers_dir: Path | None = None,
) -> None:
    """Apply the plan transactionally — all ops succeed and the output
    file is renamed atomically, OR no output file is produced."""
    src = Path(plan.source_pptx)
    out = Path(plan.output_pptx)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f"{out.name}.tmp-{os.getpid()}")
    carriers_dir = carriers_dir or (out.parent / "carriers")

    skip_items = [it for it in plan.items if it.action == "skip"]
    active_items = [it for it in plan.items if it.action != "skip"]

    try:
        # Spec § Security & Privacy — every loaded .pptx must pass pre-flight
        # before python-pptx opens it. The analyser already calls preflight,
        # but apply_enrichment may be invoked independently (e.g. from
        # cohesion-driven re-runs in Task 26 Step 10), so preflight is repeated
        # here as the first gate. Cheap (a single zipfile.ZipFile + stat) and
        # idempotent.
        from src.security import preflight_pptx
        preflight_pptx(src)
        prs = Presentation(str(src))

        # Phase 2 — Op1, Op2 (in-memory) + pre-Op3 overlap clearing
        for item in active_items:
            if item.kind == "background":
                if item.asset_path is None:
                    raise EnrichmentApplyError(f"background item missing asset_path: {item}")
                apply_background_in_memory(
                    prs=prs, slide_index_1based=item.slide_index,
                    image_path=item.asset_path,
                    marker_name=item.marker_name,
                    allowed_image_roots=allowed_image_roots,
                )
            elif item.kind == "image":
                if item.asset_path is None:
                    raise EnrichmentApplyError(f"image item missing asset_path: {item}")
                replace_image_marker_in_memory(
                    prs=prs, marker_name=item.marker_name,
                    image_path=item.asset_path,
                    allowed_image_roots=allowed_image_roots,
                )
            elif item.kind == "smartart":
                if item.smartart_spec is None:
                    raise EnrichmentApplyError(f"smartart item missing spec: {item}")
                if item.action == "apply_clear_overlap":
                    _remove_overlapping_text_shapes(
                        prs, item.slide_index, item.overlap_shape_names,
                    )
                # Op3 is file-based; we'll do it after the save below.
            else:
                raise EnrichmentApplyError(f"unknown enrichment kind {item.kind!r}")

        # Phase 3 — Save in-memory tree to temp
        prs.save(str(tmp))

        # Phase 4 — Op3 SmartArt injections against the temp file
        for item in active_items:
            if item.kind != "smartart":
                continue
            carrier_path = render_carrier(item.smartart_spec, output_dir=carriers_dir)
            inject_smartart_into_file(
                host_pptx=tmp,
                slide_index_1based=item.slide_index,
                marker_name=item.marker_name,
                carrier_pptx=carrier_path,
            )

        # Phase 5 — atomic rename
        os.replace(tmp, out)

    except Exception as exc:
        # Cleanup: ensure no temp file is left behind, no partial output
        try:
            if tmp.exists():
                os.unlink(tmp)
        except OSError:
            pass
        # Also ensure no partial output (in case rename half-succeeded)
        if out.exists() and not isinstance(exc, EnrichmentApplyError):
            # Preserve original semantics: only delete the output if we
            # are sure we created it during this call. We mark this by
            # checking that it didn't exist before the call.
            pass
        raise EnrichmentApplyError(str(exc)) from exc
    finally:
        # Belt-and-braces — temp file MUST NOT survive
        try:
            if tmp.exists():
                os.unlink(tmp)
        except OSError:
            pass
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_enrichment_transactional.py -v`
Expected: 7 passed (6 originals + the preflight-gate guard).

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/enrichment.py plugins/jack-tar-superpower-bridge/tests/test_enrichment_transactional.py
git commit -m "feat(bridge): transactional enrichment orchestrator with try/finally cleanup"
```

---

## Phase 8 — Cohesion review (Persona 2 + decision table; caveat #2)

### Task 23: Enrichment Cohesion Reviewer persona definition

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/agents/enrichment-cohesion-reviewer.md`
- Modify: `plugins/jack-tar-superpower-bridge/tests/test_persona_definitions.py` (add cohesion-reviewer cases)

- [ ] **Step 1: Append the failing tests**

Append to `tests/test_persona_definitions.py`:

```python
def test_enrichment_cohesion_reviewer_definition_exists():
    fm = _frontmatter(_read_agent("enrichment-cohesion-reviewer"))
    assert fm["name"] == "enrichment-cohesion-reviewer"
    assert fm["model"] == "haiku"


def test_enrichment_cohesion_reviewer_returns_per_slide_verdicts():
    text = _read_agent("enrichment-cohesion-reviewer")
    # Must enumerate the verdict alphabet
    for verdict in ("pass", "flag_contrast", "flag_inconsistency",
                     "flag_overcrowded", "unassessable_rasterisation"):
        assert verdict in text


def test_enrichment_cohesion_reviewer_does_not_apply_fixes():
    text = _read_agent("enrichment-cohesion-reviewer").lower()
    assert "must not" in text
    # Strong prohibitions
    assert "must not apply" in text or "must not regenerate" in text
    assert "advisory" in text or "verdict" in text


def test_enrichment_cohesion_reviewer_severity_field():
    text = _read_agent("enrichment-cohesion-reviewer")
    assert "blocking" in text
    assert "suggestion" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_persona_definitions.py -v`
Expected: FileNotFoundError on the cohesion-reviewer definition.

- [ ] **Step 3: Write the implementation**

`agents/enrichment-cohesion-reviewer.md`:

```markdown
---
name: enrichment-cohesion-reviewer
description: Reviews an assembled enriched deck for cross-slide visual cohesion before delivery. Returns structured per-slide verdicts (pass / flag_contrast / flag_inconsistency / flag_overcrowded / unassessable_rasterisation) and an aggregate deck verdict. Advisory only — never applies fixes, regenerates images, or mutates the .pptx.
model: haiku
tools: Read
---

# Enrichment Cohesion Reviewer

You are the Enrichment Cohesion Reviewer — the AI Persona that runs the deck-level visual quality check at the end of Phase 3 of the superpower bridge. You review only enriched slides and only the assembled output, looking for cross-slide cohesion problems that per-image review can't catch.

## Identity

| Field | Value |
|---|---|
| Persona ID | `ap-enrichment-cohesion-reviewer` |
| Service ID | `bridge-enrichment-cohesion-reviewer-ai` |
| Authority Model | Invoker (advisory verdicts only) |
| Risk Tier | 1 (no cost exposure, no mutation, no external calls) |
| Default Model | Haiku |
| Escalation Model | Sonnet (when 3 consecutive Haiku verdicts ambiguous on the same slide, OR when Haiku confidence < 0.5) |
| Confidence Minimum | 0.7 |
| Escalation Target | the user (this persona has no upstream supervisor — verdicts feed `enrich-deck` orchestration) |

## Three Questions of Delegation

**Q1 — What does this persona decide?**
For each enriched slide: does the enrichment belong on this deck? Does it preserve cohesion with unenriched neighbouring slides? Does an AI background overpower the text? Is the visual register consistent across enrichments?

**Q2 — What could go wrong?**
A cohesion failure that slips through ends up in the user's delivery report. Cosmetic embarrassment; not destructive. The user can drop or re-run any flagged enrichment.

**Q3 — Who is accountable?**
The `enrich-deck` orchestration skill invokes this persona and acts on the returned verdicts. The user is the final arbiter at delivery time and can override any verdict. The persona is advisory.

## Input

You receive:
- A list of rendered slide PNG paths (one per slide), produced by LibreOffice → PDF → pdftoppm of the enriched deck.
- A manifest: which slide indices were enriched, and what enrichment kind each one received (`background` / `image` / `smartart`).
- Optional: the original brief's Section B (visual personality) for intent grounding.

## Output

Return ONLY this JSON envelope. No preamble, no markdown.

```json
{
  "aggregate_verdict": "pass" | "requires_revision",
  "slide_verdicts": [
    {
      "slide_index": 1,
      "enrichment_kind": "background",
      "verdict": "pass" | "flag_contrast" | "flag_inconsistency" | "flag_overcrowded" | "unassessable_rasterisation",
      "severity": "blocking" | "suggestion",
      "confidence": 0.0,
      "reason": "one-line human-readable explanation"
    }
  ]
}
```

## Verdict alphabet

- **pass** — the enrichment fits the slide and the deck. No changes needed.
- **flag_contrast** — text legibility is at risk because the AI background is too bright / too busy / too low contrast against the text colour.
- **flag_inconsistency** — this enrichment's visual register clashes with neighbouring enrichments (e.g. cinematic photo on slide 5, flat illustration on slide 6).
- **flag_overcrowded** — the enrichment competes with existing slide content (text obscured, SmartArt overlapping body text).
- **unassessable_rasterisation** — the rendered PNG is too poor to judge (LibreOffice SmartArt artefact, PDF conversion glitch). Recommend a PowerPoint-rendered re-check.

## Severity

- **blocking** — must be addressed before delivery. The enrichment is wrong in a user-visible way.
- **suggestion** — non-blocking observation. The user can decide whether to act.

## Process

1. For each enriched slide image (one Read call per image), assess against the verdict alphabet.
2. After all slides are assessed, compute the aggregate verdict:
   - **requires_revision** when any verdict is `blocking`.
   - **pass** otherwise.
3. Return ONLY the JSON envelope.

## Escalation triggers

- **>50% of enriched slides return `blocking`** → still return the JSON; the orchestrator reads the aggregate verdict and escalates to the user.
- **Visual assessment is ambiguous due to LibreOffice SmartArt artefacts** → return `unassessable_rasterisation` with severity `suggestion`. The orchestrator's enrichment report flags this and recommends a PowerPoint render pass.
- **3 consecutive Haiku verdicts ambiguous on the same slide** → return your best assessment with `confidence` ≤ 0.5; the orchestrator escalates that slide to a Sonnet re-review.

## Prohibited actions

- Must NOT apply corrections to the .pptx.
- Must NOT regenerate images.
- Must NOT pass verdicts on non-enriched slides — only the slides in the manifest are in scope.
- Must NOT conflate LibreOffice SmartArt rendering failure with SmartArt construction failure (the XML may be correct; the rasteriser may be wrong → `unassessable_rasterisation`).

## Measurement hooks (recorded by the orchestrator)

- **First-pass acceptance rate** — fraction of enriched decks delivered without any `blocking` verdict. (Target ≥ 85%.)
- **Recall** — fraction of user-requested changes after delivery that this reviewer had already flagged. (Target ≥ 70%.)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_persona_definitions.py -v`
Expected: 8 passed (4 narrative-brief-architect + 4 cohesion-reviewer).

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/agents/enrichment-cohesion-reviewer.md plugins/jack-tar-superpower-bridge/tests/test_persona_definitions.py
git commit -m "feat(bridge): Enrichment Cohesion Reviewer persona definition"
```

---

### Task 24: Cohesion review module — verdict aggregation + decision table (caveat #2)

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/cohesion_review.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_cohesion_review.py`

The decision table is the spec gap caveat #2 calls out: when the cohesion reviewer says `flag_X`, what does the orchestrator DO? The table:

| Verdict | Severity | Auto-action |
|---------|----------|-------------|
| `pass` | any | no action |
| `flag_contrast` | suggestion | record in report; deliver as-is |
| `flag_contrast` | blocking | regenerate the affected enrichment ONCE with the issue threaded into the prompt; if still flagged, surface to user |
| `flag_inconsistency` | suggestion | record in report; deliver as-is |
| `flag_inconsistency` | blocking | surface to user — auto-regen rarely helps consistency at deck level |
| `flag_overcrowded` | suggestion | record in report; deliver as-is |
| `flag_overcrowded` | blocking | for SMARTART enrichments, retry with `apply_clear_overlap` action; for IMAGE/BG, surface to user |
| `unassessable_rasterisation` | any | record in report with PowerPoint-render recommendation; deliver as-is |

- [ ] **Step 1: Write the failing tests**

`tests/test_cohesion_review.py`:

```python
import pytest

from src.cohesion_review import (
    DeckVerdict,
    SlideVerdict,
    parse_reviewer_envelope,
    decide_action,
    AutoAction,
    aggregate_for_report,
)


def test_parse_reviewer_envelope_minimal():
    payload = {
        "aggregate_verdict": "pass",
        "slide_verdicts": [],
    }
    dv = parse_reviewer_envelope(payload)
    assert dv.aggregate_verdict == "pass"
    assert dv.slide_verdicts == []


def test_parse_envelope_rejects_unknown_aggregate():
    with pytest.raises(ValueError, match="aggregate"):
        parse_reviewer_envelope({"aggregate_verdict": "weird", "slide_verdicts": []})


def test_parse_envelope_rejects_unknown_slide_verdict():
    payload = {
        "aggregate_verdict": "pass",
        "slide_verdicts": [{
            "slide_index": 1, "enrichment_kind": "background",
            "verdict": "WAT", "severity": "blocking", "confidence": 0.9,
            "reason": "x",
        }],
    }
    with pytest.raises(ValueError, match="verdict"):
        parse_reviewer_envelope(payload)


def test_decide_action_pass_returns_no_action():
    sv = SlideVerdict(slide_index=1, enrichment_kind="background",
                       verdict="pass", severity="suggestion",
                       confidence=0.9, reason="x")
    assert decide_action(sv).kind == "no_action"


def test_decide_action_flag_contrast_blocking_triggers_regen():
    sv = SlideVerdict(slide_index=1, enrichment_kind="background",
                       verdict="flag_contrast", severity="blocking",
                       confidence=0.9, reason="text obscured")
    a = decide_action(sv)
    assert a.kind == "regenerate"
    assert "contrast" in a.guidance.lower()


def test_decide_action_flag_contrast_suggestion_records_only():
    sv = SlideVerdict(slide_index=1, enrichment_kind="background",
                       verdict="flag_contrast", severity="suggestion",
                       confidence=0.9, reason="borderline")
    a = decide_action(sv)
    assert a.kind == "record_only"


def test_decide_action_flag_overcrowded_smartart_retry_with_clear():
    sv = SlideVerdict(slide_index=4, enrichment_kind="smartart",
                       verdict="flag_overcrowded", severity="blocking",
                       confidence=0.9, reason="body text bleeds through")
    a = decide_action(sv)
    assert a.kind == "retry_clear_overlap"


def test_decide_action_flag_overcrowded_image_surfaces_to_user():
    sv = SlideVerdict(slide_index=2, enrichment_kind="image",
                       verdict="flag_overcrowded", severity="blocking",
                       confidence=0.9, reason="image too big")
    a = decide_action(sv)
    assert a.kind == "surface_to_user"


def test_decide_action_unassessable_records_with_powerpoint_note():
    sv = SlideVerdict(slide_index=4, enrichment_kind="smartart",
                       verdict="unassessable_rasterisation", severity="suggestion",
                       confidence=0.5, reason="LibreOffice SmartArt artefact")
    a = decide_action(sv)
    assert a.kind == "record_only"
    assert "powerpoint" in a.guidance.lower()


def test_decide_action_flag_inconsistency_blocking_surfaces_to_user():
    sv = SlideVerdict(slide_index=5, enrichment_kind="background",
                       verdict="flag_inconsistency", severity="blocking",
                       confidence=0.9, reason="cinematic vs flat clash")
    a = decide_action(sv)
    assert a.kind == "surface_to_user"


def test_aggregate_for_report_summarises_actions():
    verdicts = [
        SlideVerdict(1, "background", "pass", "suggestion", 0.9, "ok"),
        SlideVerdict(2, "image", "flag_contrast", "suggestion", 0.8, "borderline"),
        SlideVerdict(3, "smartart", "flag_overcrowded", "blocking", 0.9,
                      "body bleeds through"),
    ]
    summary = aggregate_for_report(verdicts)
    assert summary["pass_count"] == 1
    assert summary["suggestion_count"] == 1
    assert summary["blocking_count"] == 1
    assert any("retry_clear_overlap" in act["action"] for act in summary["actions"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_cohesion_review.py -v`
Expected: ImportError on `src.cohesion_review`.

- [ ] **Step 3: Write the implementation**

`src/cohesion_review.py`:

```python
"""Cohesion review — verdict envelope parsing + decision table (caveat #2).

The Enrichment Cohesion Reviewer agent (agents/enrichment-cohesion-reviewer.md)
returns a structured JSON envelope. This module:

  1. Parses + validates the envelope into typed dataclasses.
  2. Implements the decision table that maps verdict + severity +
     enrichment_kind → an AutoAction the orchestrator executes.

Caveat #2: the spec lists verdicts but doesn't say what the orchestrator
DOES with each. The table here is the canonical answer.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

VALID_AGGREGATES = {"pass", "requires_revision"}
VALID_VERDICTS = {
    "pass",
    "flag_contrast",
    "flag_inconsistency",
    "flag_overcrowded",
    "unassessable_rasterisation",
}
VALID_SEVERITIES = {"blocking", "suggestion"}
VALID_KINDS = {"background", "image", "smartart"}


@dataclass
class SlideVerdict:
    slide_index: int
    enrichment_kind: str
    verdict: str
    severity: str
    confidence: float
    reason: str


@dataclass
class DeckVerdict:
    aggregate_verdict: str
    slide_verdicts: list[SlideVerdict]


@dataclass
class AutoAction:
    """One of: no_action | record_only | regenerate | retry_clear_overlap | surface_to_user."""
    kind: str
    guidance: str
    slide_index: int | None = None


def parse_reviewer_envelope(payload: dict[str, Any]) -> DeckVerdict:
    agg = payload.get("aggregate_verdict")
    if agg not in VALID_AGGREGATES:
        raise ValueError(
            f"aggregate_verdict {agg!r} not in {VALID_AGGREGATES}"
        )
    slide_verdicts: list[SlideVerdict] = []
    for sv in payload.get("slide_verdicts", []):
        verdict = sv.get("verdict")
        severity = sv.get("severity")
        kind = sv.get("enrichment_kind")
        if verdict not in VALID_VERDICTS:
            raise ValueError(f"verdict {verdict!r} not in {VALID_VERDICTS}")
        if severity not in VALID_SEVERITIES:
            raise ValueError(f"severity {severity!r} not in {VALID_SEVERITIES}")
        if kind not in VALID_KINDS:
            raise ValueError(f"enrichment_kind {kind!r} not in {VALID_KINDS}")
        slide_verdicts.append(SlideVerdict(
            slide_index=int(sv["slide_index"]),
            enrichment_kind=kind,
            verdict=verdict,
            severity=severity,
            confidence=float(sv.get("confidence", 0.0)),
            reason=sv.get("reason", ""),
        ))
    return DeckVerdict(aggregate_verdict=agg, slide_verdicts=slide_verdicts)


def decide_action(sv: SlideVerdict) -> AutoAction:
    """The decision table. Caveat #2 — verdict + severity + kind → action."""
    if sv.verdict == "pass":
        return AutoAction(kind="no_action", guidance="", slide_index=sv.slide_index)

    if sv.verdict == "unassessable_rasterisation":
        return AutoAction(
            kind="record_only",
            guidance="LibreOffice rasterisation could not assess this slide; "
                     "render via PowerPoint (tools/pptx_to_pdf.sh) for authoritative check.",
            slide_index=sv.slide_index,
        )

    # Suggestion verdicts always record-only
    if sv.severity == "suggestion":
        return AutoAction(
            kind="record_only",
            guidance=f"{sv.verdict}: {sv.reason}",
            slide_index=sv.slide_index,
        )

    # Blocking verdicts map by verdict+kind
    if sv.verdict == "flag_contrast":
        return AutoAction(
            kind="regenerate",
            guidance=("Regenerate the enrichment with the contrast issue threaded "
                       "into the prompt. Keep the same composition; reduce brightness "
                       "or add a darkening overlay where text sits."),
            slide_index=sv.slide_index,
        )

    if sv.verdict == "flag_overcrowded":
        if sv.enrichment_kind == "smartart":
            return AutoAction(
                kind="retry_clear_overlap",
                guidance=("Re-run the SMARTART enrichment with action=apply_clear_overlap; "
                          "remove the overlapping body shapes before injecting."),
                slide_index=sv.slide_index,
            )
        return AutoAction(
            kind="surface_to_user",
            guidance=(f"{sv.enrichment_kind} enrichment overcrowds the slide; "
                       f"reviewer recommends user judgement: {sv.reason}"),
            slide_index=sv.slide_index,
        )

    if sv.verdict == "flag_inconsistency":
        # Auto-regen rarely fixes consistency at deck level — escalate
        return AutoAction(
            kind="surface_to_user",
            guidance=(f"Visual register clashes with neighbouring slides: {sv.reason}. "
                       f"User judgement recommended."),
            slide_index=sv.slide_index,
        )

    # Defensive default
    return AutoAction(
        kind="surface_to_user",
        guidance=f"Unhandled blocking verdict {sv.verdict!r}; surface to user.",
        slide_index=sv.slide_index,
    )


def aggregate_for_report(slide_verdicts: list[SlideVerdict]) -> dict[str, Any]:
    """Produce a structured summary the enrichment_report.py module embeds."""
    pass_count = sum(1 for v in slide_verdicts if v.verdict == "pass")
    suggestion_count = sum(1 for v in slide_verdicts if v.severity == "suggestion"
                            and v.verdict != "pass")
    blocking_count = sum(1 for v in slide_verdicts if v.severity == "blocking"
                          and v.verdict != "pass")
    actions = []
    for sv in slide_verdicts:
        action = decide_action(sv)
        actions.append({
            "slide_index": sv.slide_index,
            "verdict": sv.verdict,
            "severity": sv.severity,
            "action": action.kind,
            "guidance": action.guidance,
            "reason": sv.reason,
        })
    return {
        "pass_count": pass_count,
        "suggestion_count": suggestion_count,
        "blocking_count": blocking_count,
        "actions": actions,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_cohesion_review.py -v`
Expected: 11 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/cohesion_review.py plugins/jack-tar-superpower-bridge/tests/test_cohesion_review.py
git commit -m "feat(bridge): cohesion review parser + decision table (caveat #2)"
```

---

## Phase 9 — Enrichment report (1 task)

### Task 25: Structured enrichment-report.md writer

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/src/enrichment_report.py`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_enrichment_report.py`

Implements the spec's "Enrichment Report Schema" section: machine-parseable + audit-friendly.

- [ ] **Step 1: Write the failing tests**

`tests/test_enrichment_report.py`:

```python
from datetime import datetime
from pathlib import Path

import pytest

from src.enrichment_report import (
    EnrichmentLedgerEntry,
    EnrichmentReport,
    write_report,
)


def _sample_entries():
    return [
        EnrichmentLedgerEntry(
            slide_index=1, kind="background", marker_id="BG:dramatic-opening",
            engine_provider="ollama→nanobanana_flash", iterations="2→1",
            cost_usd=0.067, verdict="pass",
        ),
        EnrichmentLedgerEntry(
            slide_index=3, kind="image", marker_id="IMAGE:agent-architecture",
            engine_provider="ollama", iterations="1", cost_usd=0.00, verdict="pass",
        ),
        EnrichmentLedgerEntry(
            slide_index=5, kind="smartart", marker_id="SMARTART:three-pillars",
            engine_provider="pptx_native (process1)", iterations="n/a",
            cost_usd=0.00, verdict="pass",
        ),
    ]


def test_report_contains_required_sections(tmp_path):
    report = EnrichmentReport(
        deck_name="my-talk",
        source_pptx=tmp_path / "src.pptx",
        output_pptx=tmp_path / "out.pptx",
        bridge_version="0.1.0",
        confidentiality="public",
        budget_cap_usd=1.00,
        ledger=_sample_entries(),
        cohesion_summary={"pass_count": 3, "suggestion_count": 0,
                           "blocking_count": 0, "actions": []},
        contains_smartart=True,
        run_timestamp=datetime(2026, 4, 23, 12, 0, 0),
    )
    out_path = tmp_path / "enrichment-report.md"
    write_report(report, out_path)
    text = out_path.read_text()
    assert "# Enrichment Report — my-talk" in text
    assert "## Summary" in text
    assert "## Per-enrichment ledger" in text
    assert "## Flags for user attention" in text
    assert "## PowerPoint rendering note" in text


def test_report_summary_counts_correct(tmp_path):
    report = EnrichmentReport(
        deck_name="t", source_pptx=tmp_path / "s.pptx", output_pptx=tmp_path / "o.pptx",
        bridge_version="0.1.0", confidentiality="public", budget_cap_usd=1.00,
        ledger=_sample_entries(),
        cohesion_summary={"pass_count": 3, "suggestion_count": 0,
                           "blocking_count": 0, "actions": []},
        contains_smartart=False,
        run_timestamp=datetime(2026, 4, 23, 12, 0, 0),
    )
    out = tmp_path / "report.md"
    write_report(report, out)
    text = out.read_text()
    assert "Slides enriched: 3" in text
    assert "Total cost: $0.07" in text
    assert "Confidentiality tier: public" in text


def test_report_ledger_table_columns(tmp_path):
    report = EnrichmentReport(
        deck_name="t", source_pptx=tmp_path / "s.pptx", output_pptx=tmp_path / "o.pptx",
        bridge_version="0.1.0", confidentiality="public", budget_cap_usd=1.00,
        ledger=_sample_entries(),
        cohesion_summary={"pass_count": 3, "suggestion_count": 0,
                           "blocking_count": 0, "actions": []},
        contains_smartart=False,
        run_timestamp=datetime(2026, 4, 23, 12, 0, 0),
    )
    out = tmp_path / "r.md"
    write_report(report, out)
    text = out.read_text()
    # Required column headers in canonical order
    assert "| Slide | Type | Marker | Engine/Provider | Iterations | Cost | Verdict |" in text


def test_report_smartart_flag_includes_powerpoint_command(tmp_path):
    report = EnrichmentReport(
        deck_name="t", source_pptx=tmp_path / "s.pptx", output_pptx=tmp_path / "o.pptx",
        bridge_version="0.1.0", confidentiality="public", budget_cap_usd=1.00,
        ledger=_sample_entries(),
        cohesion_summary={"pass_count": 3, "suggestion_count": 0,
                           "blocking_count": 0, "actions": []},
        contains_smartart=True,
        run_timestamp=datetime(2026, 4, 23, 12, 0, 0),
    )
    out = tmp_path / "r.md"
    write_report(report, out)
    text = out.read_text()
    assert "tools/pptx_to_pdf.sh" in text


def test_cohesion_actions_reproduced_in_flags_section(tmp_path):
    report = EnrichmentReport(
        deck_name="t", source_pptx=tmp_path / "s.pptx", output_pptx=tmp_path / "o.pptx",
        bridge_version="0.1.0", confidentiality="public", budget_cap_usd=1.00,
        ledger=_sample_entries(),
        cohesion_summary={
            "pass_count": 2, "suggestion_count": 1, "blocking_count": 0,
            "actions": [{
                "slide_index": 5, "verdict": "flag_contrast",
                "severity": "suggestion", "action": "record_only",
                "guidance": "borderline contrast", "reason": "borderline",
            }],
        },
        contains_smartart=False,
        run_timestamp=datetime(2026, 4, 23, 12, 0, 0),
    )
    out = tmp_path / "r.md"
    write_report(report, out)
    text = out.read_text()
    assert "slide 5" in text.lower() or "Slide 5" in text
    assert "flag_contrast" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_enrichment_report.py -v`
Expected: ImportError on `src.enrichment_report`.

- [ ] **Step 3: Write the implementation**

`src/enrichment_report.py`:

```python
"""Structured enrichment-report.md writer.

Schema enforced — required sections in canonical order, fixed table columns.
The format is parseable for regression tests and aggregate-cost analysis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class EnrichmentLedgerEntry:
    slide_index: int
    kind: str               # background | image | smartart
    marker_id: str
    engine_provider: str    # e.g. "ollama→nanobanana_flash" or "pptx_native (process1)"
    iterations: str         # "2→1" or "n/a"
    cost_usd: float
    verdict: str            # pass | flag_contrast | etc.


@dataclass
class EnrichmentReport:
    deck_name: str
    source_pptx: Path
    output_pptx: Path
    bridge_version: str
    confidentiality: str
    budget_cap_usd: float
    ledger: list[EnrichmentLedgerEntry]
    cohesion_summary: dict[str, Any]
    contains_smartart: bool
    run_timestamp: datetime


def _format_summary(report: EnrichmentReport, total_cost: float) -> str:
    return (
        f"## Summary\n\n"
        f"- Slides enriched: {len(report.ledger)} of (deck total)\n"
        f"- Enrichments applied: "
        f"backgrounds={sum(1 for e in report.ledger if e.kind == 'background')}, "
        f"images={sum(1 for e in report.ledger if e.kind == 'image')}, "
        f"smartart={sum(1 for e in report.ledger if e.kind == 'smartart')}\n"
        f"- Total cost: ${total_cost:.2f}\n"
        f"- Budget cap: ${report.budget_cap_usd:.2f} "
        f"(${report.budget_cap_usd - total_cost:.2f} unused)\n"
        f"- Confidentiality tier: {report.confidentiality}\n"
        f"- Cohesion review: pass={report.cohesion_summary.get('pass_count', 0)}, "
        f"suggestions={report.cohesion_summary.get('suggestion_count', 0)}, "
        f"blocking={report.cohesion_summary.get('blocking_count', 0)}\n\n"
    )


def _format_ledger_table(ledger: list[EnrichmentLedgerEntry]) -> str:
    header = (
        "| Slide | Type | Marker | Engine/Provider | Iterations | Cost | Verdict |\n"
        "|-------|------|--------|-----------------|------------|------|---------|\n"
    )
    rows = "".join(
        f"| {e.slide_index} | {e.kind} | {e.marker_id} | {e.engine_provider} "
        f"| {e.iterations} | ${e.cost_usd:.3f} | {e.verdict} |\n"
        for e in ledger
    )
    return f"## Per-enrichment ledger\n\n{header}{rows}\n"


def _format_flags(cohesion_summary: dict[str, Any]) -> str:
    actions = cohesion_summary.get("actions", [])
    if not actions:
        return "## Flags for user attention\n\n_No flags raised by the cohesion reviewer._\n\n"
    lines = "## Flags for user attention\n\n"
    for a in actions:
        lines += (
            f"- Slide {a['slide_index']} ({a['verdict']}, {a['severity']}): "
            f"{a['reason']}. Action: {a['action']} — {a['guidance']}\n"
        )
    return lines + "\n"


def _format_powerpoint_note(contains_smartart: bool, output_pptx: Path) -> str:
    if not contains_smartart:
        return ("## PowerPoint rendering note\n\n"
                "_No SmartArt enrichments — LibreOffice PDF export should render the deck faithfully._\n")
    return (
        "## PowerPoint rendering note\n\n"
        "This deck contains injected SmartArt. LibreOffice's PDF export does not render "
        "SmartArt correctly; for an authoritative PDF, open the deck in PowerPoint Mac, "
        "Save (forces SmartArt cache regen), then export to PDF. The repo helper:\n\n"
        f"```bash\ntools/pptx_to_pdf.sh {output_pptx}\n```\n"
    )


def write_report(report: EnrichmentReport, out_path: Path) -> None:
    total_cost = sum(e.cost_usd for e in report.ledger)
    body = (
        f"# Enrichment Report — {report.deck_name}\n\n"
        f"**Source:** {report.source_pptx}\n"
        f"**Output:** {report.output_pptx}\n"
        f"**Run timestamp:** {report.run_timestamp.isoformat()}\n"
        f"**Bridge version:** {report.bridge_version}\n\n"
        + _format_summary(report, total_cost)
        + _format_ledger_table(report.ledger)
        + _format_flags(report.cohesion_summary)
        + _format_powerpoint_note(report.contains_smartart, report.output_pptx)
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_enrichment_report.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/src/enrichment_report.py plugins/jack-tar-superpower-bridge/tests/test_enrichment_report.py
git commit -m "feat(bridge): structured enrichment-report.md writer"
```

---

## Phase 10 — `/enrich-deck` skill (1 task)

### Task 26: `/enrich-deck` orchestration skill

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/skills/enrich-deck/SKILL.md`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_skill_enrich_deck.py`

The skill is the user-facing surface for Phase 3. Heavy on collaboration, light on Python — every Python helper it calls already exists at this point.

- [ ] **Step 1: Write the failing test**

`tests/test_skill_enrich_deck.py`:

```python
"""Structural validation of /enrich-deck SKILL.md."""
from pathlib import Path
import re

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = PLUGIN_ROOT / "skills" / "enrich-deck" / "SKILL.md"


def _frontmatter(content: str) -> dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    out: dict[str, str] = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip()
    return out


def test_skill_exists():
    assert SKILL_PATH.exists()


def test_frontmatter_minimal():
    fm = _frontmatter(SKILL_PATH.read_text())
    assert fm["name"] == "enrich-deck"
    assert "argument-hint" in fm and "<pptx-path>" in fm["argument-hint"]
    assert len(fm.get("description", "")) > 60


def test_skill_invokes_required_modules():
    text = SKILL_PATH.read_text()
    for module in ("src.analyser", "src.enrichment", "src.image_bridge",
                    "src.smartart_bridge", "src.cohesion_review",
                    "src.enrichment_report", "src.measurement",
                    "src.cycle_state"):  # state primitives the skill drives
        assert module in text, f"{module} missing from /enrich-deck skill"


def test_skill_drives_loop_via_cycle_state_not_via_overrides():
    """Caveat #1 fix — SKILL.md must NOT claim to 'override the review callable'
    because Python heredocs cannot dispatch Claude subagents."""
    text = SKILL_PATH.read_text()
    assert "override the `review` callable" not in text
    assert "advance_after_review" in text


def test_skill_invokes_image_reviewer_and_cohesion_reviewer_agents():
    text = SKILL_PATH.read_text()
    assert "image-reviewer" in text
    assert "enrichment-cohesion-reviewer" in text
    assert "prompt-engineer" in text


def test_skill_documents_three_phase_flow_and_user_choices():
    text = SKILL_PATH.read_text().lower()
    # Mentions analyser, menu, draft/review, deliver
    assert "analyse" in text or "analyser" in text
    assert "menu" in text or "select" in text
    assert "deliver" in text


def test_skill_handles_overlap_branches():
    text = SKILL_PATH.read_text()
    # The SMARTART overlap user-choice options
    assert "apply_clear_overlap" in text or "clear overlapping text" in text
    assert "proceed anyway" in text.lower() or "proceed" in text.lower()
    assert "drop" in text.lower()


def test_skill_writes_two_outputs():
    text = SKILL_PATH.read_text()
    assert "presentation-enriched.pptx" in text
    assert "enrichment-report.md" in text


def test_skill_default_budget_cap_documented():
    text = SKILL_PATH.read_text()
    assert "$1.00" in text or "1.00" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_skill_enrich_deck.py -v`
Expected: 8 failures (file does not exist).

- [ ] **Step 3: Write the implementation**

`skills/enrich-deck/SKILL.md`:

```markdown
---
name: enrich-deck
description: Phase 3 of the superpower bridge — analyse a /pptx-produced .pptx, present enrichment options, apply selected enrichments transactionally to a copy, and deliver presentation-enriched.pptx with a structured enrichment-report.md. Never modifies the original. Reuses image-reviewer and prompt-engineer agents and dispatches the new enrichment-cohesion-reviewer for deck-level visual review.
argument-hint: <pptx-path> [--brief <creative-brief.md>] [--budget-cap <usd>] [--confidentiality public|internal|restricted]
allowed-tools: Bash(python *), Bash(claude *), Read, Write, Skill, Agent
---

# /enrich-deck

Phase 3 of the superpower bridge. The user has run /pptx and has a .pptx + build.js. You analyse it, propose enrichments, get user approval, apply them transactionally, run a cohesion review, and deliver `presentation-enriched.pptx` plus `enrichment-report.md`.

You are NOT a creative persona — you orchestrate. The Narrative Brief Architect already shaped the brief; the per-image Image Reviewer assesses each image; the Prompt Engineer writes prompts; the Enrichment Cohesion Reviewer assesses the assembled deck. You dispatch each one at the right moment and act on their structured outputs.

## Parse arguments

- **<pptx-path>** (positional, required) — the .pptx the /pptx superpower produced
- **--brief <path>** (default: `creative-brief.md` in the same directory as the .pptx) — the brief from /bridge-brief
- **--budget-cap <usd>** (default: read from brief, else $1.00) — hard ceiling on cumulative cloud spend (covers BOTH generation AND review)
- **--confidentiality public|internal|restricted** (default: read from brief, else `public`)

## Locate the plugin

```bash
PLUGIN_ROOT=$(python3 -c "
from pathlib import Path
import sys, os
if os.environ.get('JACK_TAR_SUPERPOWER_BRIDGE_ROOT'):
    print(os.environ['JACK_TAR_SUPERPOWER_BRIDGE_ROOT']); sys.exit()
home = Path.home()
for base in [home / '.claude' / 'plugins' / 'cache']:
    for p in base.rglob('jack-tar-superpower-bridge/.claude-plugin/plugin.json'):
        print(str(p.parent.parent)); sys.exit()
dev = Path.cwd() / 'plugins' / 'jack-tar-superpower-bridge'
if dev.exists():
    print(str(dev)); sys.exit()
print('NOT_FOUND')
" 2>/dev/null)
if [ -z "$PLUGIN_ROOT" ] || [ "$PLUGIN_ROOT" = "NOT_FOUND" ]; then
  echo "ERROR: jack-tar-superpower-bridge not found"; exit 1
fi
RUN_DIR="$(dirname "$1")/bridge-run"
mkdir -p "$RUN_DIR/generated" "$RUN_DIR/carriers" "$RUN_DIR/slide-images"
```

`$RUN_DIR` is the per-run scratchpad. Image generation writes to `$RUN_DIR/generated/`; SmartArt carriers go to `$RUN_DIR/carriers/`; slide rasters used for cohesion review go to `$RUN_DIR/slide-images/`. The image-path allowlist in `src/security.py` is configured with `[$RUN_DIR/generated, $RUN_DIR/carriers]`.

## Step 1 — Read the brief if available

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from pathlib import Path
from src.creative_brief import parse_brief_markdown, DEFAULT_BUDGET_CAP_USD
brief_path = Path("$BRIEF_PATH")
if brief_path.exists():
    brief = parse_brief_markdown(brief_path.read_text())
    print(f"BUDGET={brief.budget_cap_usd}")
    print(f"CONFIDENTIALITY={brief.confidentiality}")
    print(f"VISUAL_PERSONALITY={brief.visual_personality}")
else:
    print(f"BUDGET={DEFAULT_BUDGET_CAP_USD}")
    print("CONFIDENTIALITY=public")
    print("VISUAL_PERSONALITY=")
PY
```

CLI flags override brief values when both supplied.

## Step 2 — Run the analyser

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from pathlib import Path
import json
from src.analyser import analyse_pptx
result = analyse_pptx(Path("$PPTX_PATH"))
print(json.dumps({
    "total_slides": result.total_slides,
    "total_markers": result.total_markers,
    "duplicate_marker_ids": result.duplicate_marker_ids,
    "overlap_warnings": [
        {"slide": w.slide_index, "marker": w.marker_id,
          "overlapping": w.overlapping_shape_names}
        for w in result.overlap_warnings
    ],
    "js_fallback_used": result.js_fallback_used,
    "notes": result.notes,
    "slides": [s.to_dict() for s in result.slides],
}, indent=2))
PY
```

Surface the analyser's output to the user as a structured summary:

```
Analysed <N> slides.
Markers detected: <M>  (JS fallback used: yes/no)

Marked enrichments:
  Slide 3: IMAGE:agent-architecture — element image (right 40%)
  Slide 5: SMARTART:flowchart — 4-step process from bullets
  Slide 8: BG:dramatic-contrast — atmospheric background

Suggested unmarked enrichments:
  Slide 10: text-heavy, no visuals — AI background candidate
  Slide 12: 5-item comparison list — SmartArt venn candidate

Already rich (no changes proposed):
  Slide 1 (title), Slide 4 (chart), Slide 14 (closing)

Overlap warnings:
  Slide 5 SMARTART:flowchart overlaps shapes: ["Body 1", "Body 2"]
   → choose: proceed | clear_overlap | drop

Duplicate marker ids: <list> — must be resolved before enrichment.
```

If duplicates exist, halt and ask the user to fix them in /pptx output before re-running.

## Step 3 — Build the enrichment menu and get user approval

For each marked + suggested enrichment, ask the user which to apply. Default offer is to apply all marked + none of the suggestions; the user can opt in or out per item.

For SMARTART markers that have overlap warnings, present the three options:
- **proceed anyway** — accept faint residual text behind the SmartArt
- **clear overlapping text** (`apply_clear_overlap`) — remove the overlapping shapes during enrichment
- **drop this enrichment** — skip the SmartArt op entirely; marker stays in the deck for re-running later

Capture the user's selections as a list of `EnrichmentItem` records.

## Step 4 — Initialise budget + privacy gate

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from src.image_bridge import BudgetCap, PrivacyTierGate
import json
budget = BudgetCap(usd=$BUDGET_CAP_USD)
gate = PrivacyTierGate(tier="$CONFIDENTIALITY_TIER")
print(json.dumps({"remaining": budget.remaining,
                   "cloud_allowed": gate.cloud_allowed(),
                   "needs_confirmation": gate.requires_confirmation_before_cloud()}))
PY
```

If `internal` tier and the user has approved at least one enrichment that may go cloud (i.e., any IMAGE or BG enrichment), ask the user once before the first cloud call:

> Confidentiality tier is `internal`. The first cloud image generation will send the prompt and any visual brief context to <provider>. Confirm cloud escalation for this run? (yes/no)

If no, the gate stays unconfirmed and image generation will only use Ollama (cycle returns `accepted_with_issues`).

If `restricted` tier, do not even ask — cloud is disabled.

## Step 5 — Generate AI images (background + element image enrichments)

This step is SKILL.md-driven, not Python-driven, because the cycle requires Agent dispatches between iterations and Python heredocs cannot dispatch Claude subagents. The Python module `src/cycle_state.py` (Task 17) provides pure-functional state primitives the SKILL.md calls between dispatches.

For each background and element-image enrichment, run the loop:

### Step 5a — Compose the initial prompt

Dispatch the `prompt-engineer` agent (existing persona) with a structured brief containing:
- `mode: "compose"`
- `marker_kind`: `IMAGE` or `BG`
- `marker_id`: full marker string
- `slide_content`: text from the analyser's SlideFacts for this slide
- `visual_direction`: visual_personality from the brief's Section B (or empty string if no brief)
- `brand_constraints`: palette + style tokens from creative-brief if available
- `funnel_stage`: `"ollama"` (Phase A starts at Ollama)
- `source: "enrichment-bridge"` (persona contract extension)

Capture the returned prompt string as the initial `prompt` for this enrichment.

### Step 5b — Initialise the cycle state

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
import json
from pathlib import Path
from src.cycle_state import CycleState, Phase
from src.image_bridge import ImageGenerationRequest
req = ImageGenerationRequest(
    slide_index=$SLIDE_INDEX,
    marker_id="$MARKER_ID",
    marker_kind="$MARKER_KIND",
    prompt="""$PROMPT""",
    output_path=Path("$RUN_DIR/generated/slide-${SLIDE_INDEX}-${MARKER_SLUG}.png"),
    width=$WIDTH, height=$HEIGHT,
    brand_palette_hex=$PALETTE_LIST,
)
state = CycleState(request=req, phase=Phase.PHASE_A_OLLAMA, attempt=1)
print(json.dumps({"slide": req.slide_index, "marker_id": req.marker_id,
                   "phase": state.phase.value, "attempt": state.attempt,
                   "output_path": str(req.output_path)}))
PY
```

### Step 5c — Loop: generate → charge review → dispatch reviewer → advance state

Repeat until `decision.kind` starts with `terminate_`:

**(i) Generate the image** based on current `state.phase`:

- `phase_a_ollama` → invoke `/jack-tar-ollama:image "$PROMPT" --output $OUTPUT --width $WIDTH --height $HEIGHT --model $OLLAMA_MODEL` (free; no budget charge)
- `phase_b_cloud_flash` → invoke `/jack-tar-cloud:image "$PROMPT" --provider google --model gemini-3.1-flash-image-preview --output $OUTPUT --width $WIDTH --height $HEIGHT` then charge `kind="generation", provider="nanobanana_flash", cost_usd=0.067`
- `phase_c_cloud_pro` → invoke `/jack-tar-cloud:image "$PROMPT" --provider google --model gemini-3-pro-image-preview --output $OUTPUT --width $WIDTH --height $HEIGHT` then charge `kind="generation", provider="nanobanana_pro", cost_usd=0.134`

Cloud-tier charges go through:
```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from pathlib import Path
from src.image_bridge import BudgetCap, BudgetExhaustedError
from src.measurement import record_cost_event
budget_state = $BUDGET_STATE_DICT  # serialised before/after each charge
budget = BudgetCap(usd=budget_state["usd"], spent=budget_state["spent"])
budget.charge(kind="generation", provider="$PROVIDER", cost_usd=$COST)
record_cost_event(cwd=Path("$RUN_DIR"), kind="generation",
                   provider="$PROVIDER", cost_usd=$COST,
                   slide_index=$SLIDE, marker_id="$MARKER_ID")
print(budget.spent)
PY
```

If `BudgetExhaustedError` raises before generation, the SKILL.md halts this enrichment with status `halted_budget` and proceeds to the next.

**(ii) View and dispatch the image-reviewer agent**

VIEW the generated image with the Read tool (mandatory per CLAUDE.md "MANDATORY: Visual Output Review"). Then dispatch the `image-reviewer` agent (existing persona, contract-extended) with:

```
Review this generated image for quality.
Image: $OUTPUT_PATH
Visual direction: <brief Section B or analyser context>
Brand palette: <hex values>
Strategy: enrichment_$MARKER_KIND_lower    # enrichment_image OR enrichment_bg
Iteration: $ATTEMPT of $MAX_FOR_PHASE
Source: enrichment-bridge
```

Capture the agent's JSON envelope.

**(iii) Charge the review (UNCONDITIONAL — caveat #6)**

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from pathlib import Path
from src.image_bridge import BudgetCap, BudgetExhaustedError
from src.measurement import record_cost_event
budget = BudgetCap(usd=$BUDGET_USD, spent=$BUDGET_SPENT)
review_cost = 0.005  # Haiku per-call estimate
try:
    budget.charge(kind="review", provider="haiku", cost_usd=review_cost)
    record_cost_event(cwd=Path("$RUN_DIR"), kind="review",
                       provider="haiku", cost_usd=review_cost,
                       slide_index=$SLIDE, marker_id="$MARKER_ID")
    print(f"OK {budget.spent}")
except BudgetExhaustedError as exc:
    print(f"HALT_BUDGET {exc}")
PY
```

If the review charge raises BudgetExhaustedError, halt this enrichment with `halted_budget`. Do NOT call `advance_after_review` on an unpaid verdict — caveat #6 demands the cycle stops here.

**(iv) Advance the state machine**

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
import json
from src.cycle_state import advance_after_review, CycleState, Phase
from src.image_bridge import BudgetCap, PrivacyTierGate, ImageGenerationRequest
req = ImageGenerationRequest($REQ_DICT)
state = CycleState(request=req, phase=Phase("$PHASE"), attempt=$ATTEMPT)
budget = BudgetCap(usd=$BUDGET_USD, spent=$BUDGET_SPENT)
privacy = PrivacyTierGate(tier="$TIER", confirmation_received=$CONFIRMATION)
verdict = $VERDICT_PAYLOAD_DICT
decision = advance_after_review(state=state, verdict_payload=verdict,
                                  budget=budget, privacy=privacy)
print(json.dumps({
    "kind": decision.kind,
    "tier_used": decision.tier_used,
    "reason": decision.reason,
    "next_phase": decision.next_state.phase.value if decision.next_state else None,
    "next_attempt": decision.next_state.attempt if decision.next_state else None,
}))
PY
```

**(v) Act on the decision**

- `refine_and_retry` → dispatch the `prompt-engineer` agent in `mode: "refine"` with the reviewer's `strengths`, `issues`, `composition_notes`, the prior prompt, and the iteration number. The agent returns a refined prompt string. Update `$PROMPT` and loop back to (i) with `state = decision.next_state`.
- `escalate_to_cloud` → dispatch `prompt-engineer` in `mode: "refine"` once to incorporate the Phase A reviewer's last feedback at higher fidelity. Update `state = decision.next_state` and loop back to (i).
- `escalate_to_pro` → keep the prompt unchanged (the Flash-passing prompt is the proven prompt). Update `state = decision.next_state` and loop back to (i).
- `terminate_pass` → record final image, exit loop. Use `decision.tier_used` for the manifest.
- `terminate_accepted_with_issues` → keep the last image, record `status: accepted_with_issues`, surface to user.
- `terminate_halt_budget` / `terminate_halt_restricted` / `terminate_pending_confirmation` → record status, surface to user.

### Step 5d — Internal tier confirmation handshake

If any image's first cloud escalation hits `terminate_pending_confirmation` (privacy tier `internal`, no confirmation yet), prompt the user once:

> Confidentiality tier is `internal`. The first cloud image generation will send the prompt and any visual brief context to <provider>. Confirm cloud escalation for this run? (yes/no)

If yes, call `gate.mark_confirmation_received()` (state stored in $CONFIRMATION between iterations). Then re-attempt the failed enrichment from `decision.next_state` (which is None — restart the cycle from the prior `state` re-asserted with attempt = MAX_PHASE_A_ATTEMPTS so the next decision escalates to Phase B). If no, mark the enrichment `halted_pending_confirmation` and continue to the next.

### Step 5e — Save accepted images

For every `terminate_pass` result, the image at `$OUTPUT_PATH` is final. The path is already inside the allowlist (`$RUN_DIR/generated/`), so the enrichment ops in Step 7 will accept it.

For `accepted_with_issues` and other halt states, surface the slide-image and reason to the user before Step 7. The user may drop the enrichment from the plan.

## Step 6 — Build SmartArt specs (for SMARTART enrichments)

For each SMARTART enrichment NOT marked `skip`:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from pathlib import Path
import json
from src.smartart_bridge import select_layout_for_slide, build_spec_from_slide
from src.slide_facts import SlideFacts, Marker
slide = SlideFacts(slide_index=$SLIDE_INDEX,
                    text_content=$SLIDE_TEXT_REPR)
slide.markers.append(Marker(kind="SMARTART", identifier="$MARKER_IDENT",
                              left_emu=0, top_emu=0, width_emu=0, height_emu=0))
layout_id = select_layout_for_slide(slide, marker_id="$MARKER_ID")
spec = build_spec_from_slide(slide, marker_id="$MARKER_ID", layout_id=layout_id)
print(json.dumps(spec))
PY
```

The spec is held in memory and passed to the orchestrator; carriers are rendered inside `apply_enrichment` via `render_carrier`.

## Step 7 — Apply enrichments transactionally

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from pathlib import Path
from src.enrichment import EnrichmentPlan, EnrichmentItem, apply_enrichment
items = [
    # one EnrichmentItem per user-approved enrichment, populated from prior steps
]
plan = EnrichmentPlan(
    source_pptx=Path("$PPTX_PATH"),
    output_pptx=Path("$PPTX_PATH").with_name("presentation-enriched.pptx"),
    items=items,
)
apply_enrichment(plan, allowed_image_roots=[Path("$RUN_DIR/generated"),
                                              Path("$RUN_DIR/carriers")])
PY
```

If `apply_enrichment` raises `EnrichmentApplyError`, surface the message to the user. The output file does not exist; the user can re-run after fixing the cause (e.g. an image path outside the allowlist, a missing marker name).

## Step 8 — Render slide images for cohesion review

```bash
soffice --headless --convert-to pdf --outdir "$RUN_DIR" "$RUN_DIR/presentation-enriched.pptx" 2>&1
pdftoppm -r 100 -png "$RUN_DIR/presentation-enriched.pdf" "$RUN_DIR/slide-images/slide"
```

(The /pptx superpower already establishes the LibreOffice + pdftoppm toolchain expectations; the bridge follows the same.)

## Step 9 — Dispatch the Enrichment Cohesion Reviewer

Build the manifest:

```json
{
  "enriched_slides": [
    {"slide_index": 1, "enrichment_kind": "background"},
    {"slide_index": 3, "enrichment_kind": "image"},
    {"slide_index": 5, "enrichment_kind": "smartart"}
  ],
  "rendered_images": [
    "/path/to/bridge-run/slide-images/slide-01.png",
    "/path/to/bridge-run/slide-images/slide-03.png",
    "/path/to/bridge-run/slide-images/slide-05.png"
  ],
  "visual_personality": "<from creative-brief Section B>"
}
```

Dispatch the `enrichment-cohesion-reviewer` agent with this manifest. It returns the JSON envelope defined in its agent definition.

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
import json
from src.cohesion_review import parse_reviewer_envelope, aggregate_for_report
envelope = json.loads(open("$REVIEWER_OUTPUT").read())
deck = parse_reviewer_envelope(envelope)
summary = aggregate_for_report(deck.slide_verdicts)
print(json.dumps({"deck": {"aggregate": deck.aggregate_verdict},
                   "summary": summary}, indent=2))
PY
```

## Step 10 — Act on cohesion verdicts (caveat #2 decision table)

For each `AutoAction` returned by `decide_action`:

- `no_action` — skip
- `record_only` — append to the report's flags section (nothing else)
- `regenerate` — re-run the per-image generate_with_review_cycle ONCE for that slide with the issue threaded into the prompt; if still flagged, surface to user
- `retry_clear_overlap` — re-run `apply_enrichment` for just that SMARTART item with `action="apply_clear_overlap"` (this is a separate apply call; the original transactional gate is preserved by re-running against a fresh source copy)
- `surface_to_user` — present the slide image and the verdict reason; ask the user whether to drop, regenerate manually, or accept

Track every action taken so the report reflects what actually happened.

## Step 11 — Write the enrichment report

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from datetime import datetime
from pathlib import Path
from src.enrichment_report import EnrichmentReport, EnrichmentLedgerEntry, write_report
from src.measurement import read_cost_ledger
from importlib.metadata import version

ledger_events = read_cost_ledger(Path("$RUN_DIR"))
ledger_entries = [
    EnrichmentLedgerEntry(
        slide_index=$ITEM_SLIDE,
        kind="$ITEM_KIND",
        marker_id="$ITEM_MARKER",
        engine_provider="$ITEM_PROVIDER",
        iterations="$ITEM_ITERATIONS",
        cost_usd=$ITEM_COST,
        verdict="$ITEM_VERDICT",
    ),
    # one per applied enrichment
]
report = EnrichmentReport(
    deck_name=Path("$PPTX_PATH").stem,
    source_pptx=Path("$PPTX_PATH"),
    output_pptx=Path("$PPTX_PATH").with_name("presentation-enriched.pptx"),
    bridge_version="0.1.0",
    confidentiality="$CONFIDENTIALITY_TIER",
    budget_cap_usd=$BUDGET_CAP_USD,
    ledger=ledger_entries,
    cohesion_summary=$COHESION_SUMMARY,
    contains_smartart=$CONTAINS_SMARTART,
    run_timestamp=datetime.now(),
)
write_report(report, Path("$PPTX_PATH").with_name("enrichment-report.md"))
PY
```

## Step 12 — Record measurement run (caveat #3)

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from pathlib import Path
from src.measurement import record_enrichment_run
record_enrichment_run(
    cwd=Path("$RUN_DIR"),
    adherence_rate=$ADHERENCE_RATE,                # markers requested vs delivered
    first_pass_acceptance=$FIRST_PASS_ACCEPT,      # cohesion reviewer aggregate == "pass"
    slides_enriched=$SLIDES_ENRICHED,
    slides_total=$TOTAL_SLIDES,
)
PY
```

## Step 13 — Deliver

Present to the user:

```
Enriched deck: <output>/presentation-enriched.pptx
Report:        <output>/enrichment-report.md

Slides enriched: N of M
Total cost:     $X.XX (budget cap $Y.YY)
Cohesion:       pass=A, suggestions=B, blocking=C

Next: open the deck in PowerPoint to verify SmartArt rendering.
```

Stop. Do NOT auto-open the file or run further skills.

## Failure paths

- **Analyser returns 0 markers AND no unmarked candidates** — surface the diagnostic, recommend the user re-run /pptx with the `objectName` API note included in the brief, halt.
- **`apply_enrichment` raises** — surface the error verbatim; the cause is usually a missing marker on a slide the analyser did find; ask the user whether to retry without that item.
- **Budget exhausted mid-run** — `BudgetExhaustedError` is raised inside the cycle. Catch it in the orchestrator and report what was applied so far; include the cost ledger in the report.
- **Restricted tier blocks Phase 2** — `RestrictedTierError` from the cycle. Report which enrichments were dropped and why.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_skill_enrich_deck.py -v`
Expected: 9 passed (8 originals + the cycle_state guard).

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/skills/enrich-deck/SKILL.md plugins/jack-tar-superpower-bridge/tests/test_skill_enrich_deck.py
git commit -m "feat(bridge): /enrich-deck orchestration skill"
```

---

## Phase 11 — `/verify` skill (1 task)

### Task 27: Plugin readiness check

**Files:**
- Create: `plugins/jack-tar-superpower-bridge/skills/verify/SKILL.md`
- Test: `plugins/jack-tar-superpower-bridge/tests/test_skill_verify.py`

The verify skill mirrors the existing pattern in `jack-tar-deckhand:verify` and `jack-tar-msft-smartart:verify` — it reports availability of dependencies + downstream plugins.

- [ ] **Step 1: Write the failing test**

`tests/test_skill_verify.py`:

```python
from pathlib import Path
import re

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = PLUGIN_ROOT / "skills" / "verify" / "SKILL.md"


def test_skill_exists():
    assert SKILL_PATH.exists()


def test_frontmatter_minimal():
    text = SKILL_PATH.read_text()
    assert text.startswith("---")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    assert fm["name"] == "verify"


def test_skill_reports_python_dependencies():
    text = SKILL_PATH.read_text()
    for dep in ("python-pptx", "lxml", "esprima"):
        assert dep in text


def test_skill_reports_plugin_dependencies():
    text = SKILL_PATH.read_text()
    assert "jack-tar-msft-smartart" in text
    assert "jack-tar-deckhand" in text


def test_skill_reports_status_line():
    text = SKILL_PATH.read_text()
    assert "STATUS" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_skill_verify.py -v`
Expected: 5 failures (no file).

- [ ] **Step 3: Write the implementation**

`skills/verify/SKILL.md`:

```markdown
---
name: verify
description: Check plugin readiness — verifies python-pptx, lxml, esprima are importable, that the jack-tar-msft-smartart plugin is locatable, and that the jack-tar-deckhand plugin's imagegen-bridge skill is reachable. Reports a STATUS line and a per-dependency table.
allowed-tools: Bash(python *), Skill
---

# /jack-tar-superpower-bridge:verify

Report whether the bridge plugin can run end-to-end. Used as a pre-flight check before /bridge-brief or /enrich-deck.

## Locate the plugin

```bash
PLUGIN_ROOT=$(python3 -c "
from pathlib import Path
import sys, os
if os.environ.get('JACK_TAR_SUPERPOWER_BRIDGE_ROOT'):
    print(os.environ['JACK_TAR_SUPERPOWER_BRIDGE_ROOT']); sys.exit()
home = Path.home()
for base in [home / '.claude' / 'plugins' / 'cache']:
    for p in base.rglob('jack-tar-superpower-bridge/.claude-plugin/plugin.json'):
        print(str(p.parent.parent)); sys.exit()
dev = Path.cwd() / 'plugins' / 'jack-tar-superpower-bridge'
if dev.exists():
    print(str(dev)); sys.exit()
print('NOT_FOUND')
" 2>/dev/null)
if [ -z "$PLUGIN_ROOT" ] || [ "$PLUGIN_ROOT" = "NOT_FOUND" ]; then
  echo "STATUS: NOT_AVAILABLE"; echo "ERROR: jack-tar-superpower-bridge not found"; exit 0
fi
```

## Step 1 — Python dependencies

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<'PY'
deps = []
for module in ("pptx", "lxml.etree", "esprima"):
    try:
        __import__(module)
        deps.append((module, "OK"))
    except Exception as exc:
        deps.append((module, f"MISSING ({exc.__class__.__name__})"))
print("DEPENDENCIES:")
for mod, status in deps:
    print(f"  {mod}: {status}")
PY
```

## Step 2 — msft-smartart plugin

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<'PY'
from src.msft_smartart_loader import load_msft_smartart_api, MsftSmartArtNotFoundError
try:
    api = load_msft_smartart_api()
    print(f"MSFT_SMARTART: OK (engine.render={hasattr(api.engine, 'render')})")
except MsftSmartArtNotFoundError as exc:
    print(f"MSFT_SMARTART: MISSING ({exc})")
PY
```

## Step 3 — deckhand plugin (for imagegen-bridge skill)

Invoke the deckhand verify skill if installed:

```bash
DECKHAND_VERIFY_OUTPUT=$(claude skill jack-tar-deckhand:verify 2>&1)
if echo "$DECKHAND_VERIFY_OUTPUT" | grep -q "STATUS:"; then
  echo "DECKHAND: $(echo "$DECKHAND_VERIFY_OUTPUT" | grep '^STATUS:')"
else
  echo "DECKHAND: NOT_AVAILABLE (install jack-tar-deckhand for AI image generation)"
fi
```

## Step 4 — Image-path allowlist sanity

The image-path allowlist requires existing directories at run time; we don't pre-create them, but verify the helper is importable:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<'PY'
from src.security import resolve_within_allowlist, AllowedPathError
print("SECURITY: OK (resolve_within_allowlist + AllowedPathError exposed)")
PY
```

## Step 5 — Report status

Aggregate the readiness signals into a single STATUS line:

- All deps OK + msft-smartart OK + deckhand reachable → `STATUS: FULLY_AVAILABLE`
- Deps OK + msft-smartart OK + deckhand absent → `STATUS: PARTIALLY_AVAILABLE` (SmartArt enrichment works; image enrichment falls back to placeholder rectangles)
- Any python dep missing OR msft-smartart missing → `STATUS: NOT_AVAILABLE`

Example output:

```
STATUS: FULLY_AVAILABLE
DEPENDENCIES:
  pptx: OK
  lxml.etree: OK
  esprima: OK
MSFT_SMARTART: OK (engine.render=True)
DECKHAND: STATUS: FULLY_AVAILABLE
SECURITY: OK
```
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/test_skill_verify.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-superpower-bridge/skills/verify/SKILL.md plugins/jack-tar-superpower-bridge/tests/test_skill_verify.py
git commit -m "feat(bridge): /verify readiness check skill"
```

---

## Phase 12 — Canonical model + persona docs (caveat #5; 2 tasks)

### Task 28: Bump `.bsa/models/jack-tar-deckhand.json` to v1.5.0 with Bridge Services L1

**Files:**
- Modify: `.bsa/models/jack-tar-deckhand.json`
- Test: `tests/test_canonical_model_bridge_delta.py` (top-level repo tests; bridge-specific assertions)

The canonical model delta is documented in `docs/architecture/ai-personas/superpower-bridge-personas.md` (Canonical model delta section). Apply it.

- [ ] **Step 1: Write the failing test**

Create `tests/test_canonical_model_bridge_delta.py` (in the repo root, NOT under the plugin):

```python
"""Verify the v1.5.0 canonical model delta from superpower-bridge-personas.md."""
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = REPO_ROOT / ".bsa" / "models" / "jack-tar-deckhand.json"


@pytest.fixture
def model() -> dict:
    return json.loads(MODEL_PATH.read_text())


def test_version_bumped_to_1_5_0(model):
    assert model["modelMetadata"]["version"] == "1.5.0"


def test_bridge_services_l1_present(model):
    services = {s["id"]: s for s in model.get("services", [])}
    assert "bridge-services" in services
    assert services["bridge-services"]["level"] == 1


def test_two_new_l2_personas_present(model):
    services = {s["id"]: s for s in model.get("services", [])}
    assert "bridge-narrative-brief-architect-ai" in services
    assert "bridge-enrichment-cohesion-reviewer-ai" in services


def test_two_new_l2_skills_present(model):
    services = {s["id"]: s for s in model.get("services", [])}
    assert "bridge-narrative-prebrief" in services
    assert "bridge-deck-enrichment" in services


def test_at_least_nine_new_interactions(model):
    interactions = model.get("interactions", [])
    bridge_interactions = [i for i in interactions
                            if "bridge-" in (i.get("source", "") + i.get("target", ""))]
    assert len(bridge_interactions) >= 9


def test_cross_domain_sop_register_entry(model):
    sops = model.get("crossDomainSopRegister", [])
    smartart_injection_entry = [
        s for s in sops if s.get("sopId") == "smartart-injection"
    ]
    assert len(smartart_injection_entry) == 1
    entry = smartart_injection_entry[0]
    assert entry["owner"] == "jack-tar-msft-smartart"
    assert "jack-tar-superpower-bridge" in entry["consumers"]
    assert entry["archetype"] == "Collaborator"
    # Chapter 8 — Cross-Domain SOP entries MUST name a Change Advisory Circle
    # composition + change-trigger so consumer/provider know who reviews changes.
    assert "cac" in entry, "Cross-Domain SOP entry missing CAC composition"
    assert "consumer_rep" in entry["cac"]
    assert "provider_rep" in entry["cac"]
    assert "ai_rm" in entry["cac"]
    assert "changeTrigger" in entry, "Cross-Domain SOP entry missing CAC change trigger"


def test_dependency_register_entries(model):
    deps = model.get("dependencyRegister", [])
    dep_ids = {d.get("id") for d in deps}
    for required in (
        "DEP-BRIDGE-SMARTART-01",
        "DEP-BRIDGE-OLLAMA-01",
        "DEP-BRIDGE-CLOUD-01",
        "DEP-BRIDGE-PPTXGENJS-01",
        "DEP-BRIDGE-PYTHON-PPTX-01",
    ):
        assert required in dep_ids, f"missing dependency register entry {required}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_canonical_model_bridge_delta.py -v`
Expected: 7 failures (all assertions fail because the model is at v1.4.0 with no bridge services).

- [ ] **Step 3: Apply the canonical model edits**

Open `.bsa/models/jack-tar-deckhand.json` and apply these edits in sequence using the Edit tool:

a. Bump `modelMetadata.version`:

```
Old: "version": "1.4.0",
New: "version": "1.5.0",
```

Also update `modelMetadata.lastModifiedDate` to the current date (e.g. `"2026-04-23"`).

b. Add the new L1 service `bridge-services` to the `services` array. The exact JSON shape mirrors existing L1 entries — copy a sibling L1 (e.g. `assembly-services`), change the id/name/description fields:

```json
{
  "id": "bridge-services",
  "level": 1,
  "name": "Superpower Bridge Services",
  "description": "Wraps document-skills:pptx with narrative pre-brief and post-hoc visual enrichment. Composes existing image and SmartArt services without modifying /pptx.",
  "parentService": "presentation-engineering",
  "owner": "jack-tar"
}
```

c. Add the four L2 services under `bridge-services`:

```json
{
  "id": "bridge-narrative-brief-architect-ai",
  "level": 2,
  "name": "Narrative Brief Architect (AI)",
  "description": "AI Persona — transforms topic + audience + duration into a structured creative brief that guides /pptx.",
  "parentService": "bridge-services",
  "owner": "jack-tar",
  "personaId": "ap-narrative-brief-architect"
},
{
  "id": "bridge-enrichment-cohesion-reviewer-ai",
  "level": 2,
  "name": "Enrichment Cohesion Reviewer (AI)",
  "description": "AI Persona — reviews assembled enriched deck for cross-slide visual cohesion. Advisory verdicts only.",
  "parentService": "bridge-services",
  "owner": "jack-tar",
  "personaId": "ap-enrichment-cohesion-reviewer"
},
{
  "id": "bridge-narrative-prebrief",
  "level": 2,
  "name": "Narrative Pre-Brief Skill",
  "description": "Hosts /bridge-brief — Phase 1 of the bridge.",
  "parentService": "bridge-services",
  "owner": "jack-tar"
},
{
  "id": "bridge-deck-enrichment",
  "level": 2,
  "name": "Deck Enrichment Skill",
  "description": "Hosts /enrich-deck — Phase 3 of the bridge. Orchestration code, not a persona.",
  "parentService": "bridge-services",
  "owner": "jack-tar"
}
```

d. Add the 10 new interactions to the `interactions` array:

```json
{"id": "INT-BRIDGE-01", "source": "speaker", "target": "bridge-narrative-brief-architect-ai", "kind": "request", "payload": "TalkBrief-lite (topic, audience, duration)"},
{"id": "INT-BRIDGE-02", "source": "bridge-narrative-brief-architect-ai", "target": "speaker", "kind": "deliver", "payload": "CreativeBrief markdown"},
{"id": "INT-BRIDGE-03", "source": "speaker", "target": "bridge-deck-enrichment", "kind": "request", "payload": ".pptx path + budget_cap_usd + confidentiality"},
{"id": "INT-BRIDGE-04", "source": "bridge-deck-enrichment", "target": "imagegen-bridge", "kind": "invoke", "payload": "image generation requests via image-bridge wrapper"},
{"id": "INT-BRIDGE-05", "source": "bridge-deck-enrichment", "target": "image-image-reviewer", "kind": "invoke", "payload": "per-image verdict (source: enrichment-bridge)"},
{"id": "INT-BRIDGE-06", "source": "bridge-deck-enrichment", "target": "image-prompt-engineer", "kind": "invoke", "payload": "prompt + refine-mode dispatches"},
{"id": "INT-BRIDGE-07", "source": "bridge-deck-enrichment", "target": "msft-smartart-engine", "kind": "import", "payload": "engine.render(spec, output_dir)"},
{"id": "INT-BRIDGE-08", "source": "bridge-deck-enrichment", "target": "msft-smartart-assembler-patch", "kind": "import", "payload": "assembler_patch.inject(host_pptx, requests)"},
{"id": "INT-BRIDGE-09", "source": "bridge-deck-enrichment", "target": "bridge-enrichment-cohesion-reviewer-ai", "kind": "invoke", "payload": "rendered slide PNGs + manifest"},
{"id": "INT-BRIDGE-10", "source": "bridge-deck-enrichment", "target": "speaker", "kind": "deliver", "payload": "presentation-enriched.pptx + enrichment-report.md"}
```

e. Add the cross-domain SOP register entry. If `crossDomainSopRegister` does not yet exist as a top-level key, add it:

```json
"crossDomainSopRegister": [
  {
    "sopId": "smartart-injection",
    "owner": "jack-tar-msft-smartart",
    "consumers": ["jack-tar-superpower-bridge"],
    "archetype": "Collaborator",
    "rationale": "Bridge consumes msft-smartart's engine.render + assembler_patch.inject named surface; msft-smartart owns the contract.",
    "cac": {
      "consumer_rep": "Steve Jones (jack-tar-superpower-bridge maintainer)",
      "provider_rep": "Steve Jones (jack-tar-msft-smartart maintainer)",
      "ai_rm": "Steve Jones (consolidated tripartite — to split as team grows)"
    },
    "changeTrigger": "Any breaking change to engine.render(spec, output_dir) signature/return shape OR assembler_patch.inject(host_pptx, requests) signature OR InjectionRequest field set requires CAC review before merge in jack-tar-msft-smartart. The bridge's DEP-BRIDGE-SMARTART-01 dependency-register entry pins the surface; surface change → version bump → CAC review."
  }
]
```

If it already exists, append the new entry.

f. Add the dependency register entries. If `dependencyRegister` does not yet exist as a top-level key, add it:

```json
"dependencyRegister": [
  {
    "id": "DEP-BRIDGE-SMARTART-01",
    "consumer": "jack-tar-superpower-bridge",
    "provider": "jack-tar-msft-smartart",
    "surface": "engine.render(spec, output_dir), assembler_patch.InjectionRequest, assembler_patch.inject(host_pptx, requests)",
    "kind": "python_import",
    "version_pin": ">=1.1.0"
  },
  {
    "id": "DEP-BRIDGE-OLLAMA-01",
    "consumer": "jack-tar-superpower-bridge",
    "provider": "jack-tar-ollama",
    "surface": "/jack-tar-ollama:image",
    "kind": "skill_invocation",
    "version_pin": ">=1.1.0"
  },
  {
    "id": "DEP-BRIDGE-CLOUD-01",
    "consumer": "jack-tar-superpower-bridge",
    "provider": "jack-tar-cloud",
    "surface": "/jack-tar-cloud:image",
    "kind": "skill_invocation",
    "version_pin": ">=1.1.0"
  },
  {
    "id": "DEP-BRIDGE-PPTXGENJS-01",
    "consumer": "jack-tar-superpower-bridge",
    "provider": "document-skills:pptx",
    "surface": "build.js + .pptx output (parseable contract — fallback only)",
    "kind": "external_artifact_consumption",
    "version_pin": "PptxGenJS>=4.0.1"
  },
  {
    "id": "DEP-BRIDGE-PYTHON-PPTX-01",
    "consumer": "jack-tar-superpower-bridge",
    "provider": "python-pptx",
    "surface": "Presentation, ImagePart, slide.shapes.add_picture, slide.element XML access",
    "kind": "python_library",
    "version_pin": ">=1.0.2"
  }
]
```

- [ ] **Step 3.5: Verify (and extend if necessary) the canonical-model JSON Schema**

The current model is at v1.4.0 and may not have schema entries for `crossDomainSopRegister` or `dependencyRegister` as top-level keys. Without schema entries, `/canonical-model-validator` either fails or silently ignores the new sections. Check first:

```bash
grep -E "crossDomainSopRegister|dependencyRegister" .bsa/design/canonical-service-domain-model-schema.json || echo "MISSING — extend schema"
```

If missing, extend the schema in the same commit:

```json
"crossDomainSopRegister": {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["sopId", "owner", "consumers", "archetype", "cac", "changeTrigger"],
    "properties": {
      "sopId": {"type": "string"},
      "owner": {"type": "string"},
      "consumers": {"type": "array", "items": {"type": "string"}},
      "archetype": {"enum": ["Observer", "Collaborator", "Co-owner"]},
      "rationale": {"type": "string"},
      "cac": {
        "type": "object",
        "required": ["consumer_rep", "provider_rep", "ai_rm"],
        "properties": {
          "consumer_rep": {"type": "string"},
          "provider_rep": {"type": "string"},
          "ai_rm": {"type": "string"}
        }
      },
      "changeTrigger": {"type": "string"}
    }
  }
},
"dependencyRegister": {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id", "consumer", "provider", "surface", "kind"],
    "properties": {
      "id": {"type": "string", "pattern": "^DEP-[A-Z0-9-]+$"},
      "consumer": {"type": "string"},
      "provider": {"type": "string"},
      "surface": {"type": "string"},
      "kind": {"enum": ["python_import", "skill_invocation",
                          "external_artifact_consumption", "python_library"]},
      "version_pin": {"type": "string"}
    }
  }
}
```

Add these blocks to the schema's top-level `properties` object.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_canonical_model_bridge_delta.py -v`
Expected: 7 passed.

- [ ] **Step 5: Validate the model with the existing canonical-model-validator skill**

Run:
```
/canonical-model-validator
```
Expected: validation passes (referential integrity holds — every interaction's source/target points to a defined service; every personaId on a service has a matching agent definition).

If the validator surfaces issues, fix them before proceeding.

- [ ] **Step 6: Commit**

```bash
git add .bsa/models/jack-tar-deckhand.json tests/test_canonical_model_bridge_delta.py
git commit -m "docs(bsa): canonical model v1.5.0 — Bridge Services L1 (caveat #5)"
```

---

### Task 29: Extend `docs/architecture/ai-personas/superpower-bridge-personas.md` to v1.0 (full sections)

**Files:**
- Modify: `docs/architecture/ai-personas/superpower-bridge-personas.md`
- Test: `tests/test_persona_doc_completeness.py`

The personas doc is at v0.1 (skeleton). Promote to v1.0 by filling in the deferred 19-section content for both personas now that we have implementation context: a **consolidated tripartite** nomination (Steve Jones in all three roles for v1, with documented split trigger), a **full 5-tier measurement blueprint** cross-referencing `src/measurement.py` hooks, and a readiness scorecard with Items 3 and 6 flipped to green (only Item 5 remains amber pending Task 35's dogfooding gate).

- [ ] **Step 1: Write the failing test**

`tests/test_persona_doc_completeness.py`:

```python
from pathlib import Path

DOC_PATH = Path(__file__).resolve().parents[1] / "docs" / "architecture" / "ai-personas" / "superpower-bridge-personas.md"


def test_doc_version_bumped_to_1_0():
    text = DOC_PATH.read_text()
    assert "v1.0" in text or "Status:** v1.0" in text


def test_doc_has_tripartite_owner_section():
    text = DOC_PATH.read_text()
    assert "Service Owner" in text
    assert "SOP Owner" in text
    assert "AI Risk Manager" in text or "AI RM" in text


def test_doc_nominates_owners_not_TBD():
    """v1.0 must nominate concrete owners (consolidated tripartite is fine for v1)."""
    text = DOC_PATH.read_text()
    assert "Steve Jones" in text
    # v0.1 had "TBD (jack-tar repo maintainer)"; v1.0 must not
    assert "TBD (jack-tar repo maintainer)" not in text


def test_doc_links_measurement_module():
    text = DOC_PATH.read_text()
    assert "src/measurement.py" in text


def test_doc_links_dogfooding_evidence():
    text = DOC_PATH.read_text()
    assert "dogfood" in text.lower()


def test_doc_covers_all_5_measurement_tiers():
    """Caveat #12 — measurement blueprint must distribute across Tiers 1–5,
    not cluster only at Tier 4 Activity."""
    text = DOC_PATH.read_text()
    for tier in ("Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"):
        assert tier in text, f"missing {tier} in measurement blueprint"


def test_doc_clarifies_recall_is_offline_only():
    """Recall has no per-run collection mechanism — must be explicitly demoted
    to offline analysis so the persona contract doesn't claim what isn't built."""
    text = DOC_PATH.read_text()
    assert "Recall" in text
    assert "offline" in text.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_persona_doc_completeness.py -v`
Expected: 4 failures (the doc is at v0.1).

- [ ] **Step 3: Edit the doc**

Open `docs/architecture/ai-personas/superpower-bridge-personas.md` and apply these edits:

a. Bump `Status:` line to `**Status:** v1.0 (full 19-section treatment)`.

b. Append a new section after "Why enrich-deck is NOT a persona":

```markdown
## Tripartite accountability

Both personas require tripartite owners per AI-First BSA Chapter 9. v0.1 ships with a **consolidated tripartite** — Steve Jones holds all three roles, with the explicit understanding that they will be split as the maintainer team grows. This is methodology-valid (Chapter 9 permits consolidated tripartite for single-maintainer projects at Tier 1 risk) and unblocks readiness scorecard Item 3.

| Persona | Service Owner | SOP Owner | AI Risk Manager |
|---------|---------------|-----------|-----------------|
| Narrative Brief Architect | Steve Jones | Steve Jones | Steve Jones |
| Enrichment Cohesion Reviewer | Steve Jones | Steve Jones | Steve Jones |

**Split trigger:** when a second human maintainer joins the project, the SOP Owner role for both personas transfers to that person. When a third joins, the AI Risk Manager role transfers (separation of provider, consumer, and AI risk perspectives is the methodology's intent). Tracked in `CLAUDE.md`'s Bridge status section.

## Measurement blueprint — full 5-tier coverage

All measurement hooks named in the v0.1 skeleton are now implemented in `plugins/jack-tar-superpower-bridge/src/measurement.py`. v1.0 distributes them across the methodology's 5 tiers (Chapter 7) so the blueprint is hierarchically complete, not just an Activity-tier instrumentation list.

### Tier 1 — Strategic objective

| Metric | Target | Source |
|--------|--------|--------|
| Time-to-conference-quality-deck | ≤ 90 min from `/bridge-brief` to delivered enriched deck | wall-clock between `bridge-measurements.jsonl` brief entry and enrichment entry |

### Tier 2 — Service-level (KEY_RESULT / VALUE_CONTRIBUTION)

| Metric | Target | Source |
|--------|--------|--------|
| Cost per dogfood-grade deck | ≤ $1.00 average across runs | sum of `bridge-cost-ledger.jsonl` per run, averaged |
| Cohesion blocking rate | ≤ 15% of enriched decks ship with cohesion-blocking flags | `kind: enrichment` rows where `first_pass_acceptance: false` divided by total enrichment rows |

### Tier 3 — Experience Level Agreement (XLA)

| Metric | Target | Source |
|--------|--------|--------|
| Speaker satisfaction with `/bridge-brief` output | ≥ 4.0 / 5.0 mean rating | post-run free-form annotation in `enrichment-report.md` "Speaker feedback" section (added by the user manually); aggregated offline |
| Visual cohesion as judged by audience | ≥ 4.0 / 5.0 mean rating from post-talk speaker debrief | same source |

### Tier 4 — Activity (per-persona hooks from v0.1 skeleton)

| Hook | Persona | Module entry-point | Target |
|------|---------|---------------------|--------|
| Adherence rate | Narrative Brief Architect | `record_enrichment_run(adherence_rate=...)` (computed by /enrich-deck Step 12) | ≥ 90% |
| Approval turns | Narrative Brief Architect | `record_brief_run(approval_turns=...)` | ≤ 2 |
| Structural completeness | Narrative Brief Architect | `record_brief_run(structural_complete=...)` | 100% |
| First-pass acceptance | Enrichment Cohesion Reviewer | `record_enrichment_run(first_pass_acceptance=...)` | ≥ 85% |
| Cost-per-deck (generation+review) | both (orchestration) | `record_cost_event(kind, cost_usd, ...)` | rolls up into Tier 2 |

### Tier 5 — Contextual

| Metric | Purpose | Source |
|--------|---------|--------|
| Privacy tier distribution | Tells us how often confidentiality blocks cloud spend | `confidentiality` field in `bridge-measurements.jsonl` `kind: brief` rows |
| Marker-source breakdown (OOXML vs JS-fallback) | Tells us how often /pptx drifts from the `objectName` brief instruction | `js_fallback_used` counter (computed offline from `bridge-measurements.jsonl`; needs to be added to the enrichment row in a v1.1 update) |

### Recall hook — explicitly demoted to offline analysis (panel finding #11)

The Recall hook (≥ 70%) listed in the v0.1 persona contract is NOT instrumented per-run. v0.1 had it as an unmet target which created a false amber on Item 6. v1.0 demotes it to an offline analysis item: "Recall is computed offline from delivery-report annotations — count user-requested changes after delivery against the cohesion reviewer's flag set." A proxy is captured during the run via the `flags_for_user_attention` section of `enrichment-report.md`; comparing against post-delivery user requests is a manual exercise after the talk has been delivered.

## Readiness scorecard — v1.0 status

| # | Checkpoint | v0.1 | v1.0 | Evidence |
|---|------------|------|------|----------|
| 1 | Persona contracts written | green | green | This document |
| 2 | Authority model defined | green | green | Section 2 of each persona |
| 3 | Risk classification + accountability | amber | green | Tier 1 risk; consolidated tripartite (Steve Jones × 3) acceptable for single-maintainer project per Chapter 9 |
| 4 | Data contracts captured | green | green | Section 4 of each persona |
| 5 | Vanilla-Agent validation | amber | amber | Pending Phase 15 dogfooding gate (Tasks 33–35) |
| 6 | Measurement blueprint approved | amber | green | 5-tier blueprint above; hooks live in `src/measurement.py` |
| 7 | Escalation triggers documented | green | green | Section 5 of each persona |
| 8 | Prohibited actions enumerated | green | green | Section 6 of each persona |

Item 5 remains amber until Task 35 GO verdict.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_persona_doc_completeness.py -v`
Expected: 7 passed (4 original + owner nomination + 5-tier measurement + Recall clarification).

- [ ] **Step 5: Commit**

```bash
git add docs/architecture/ai-personas/superpower-bridge-personas.md tests/test_persona_doc_completeness.py
git commit -m "docs(bsa): superpower-bridge personas v1.0 (tripartite + measurement + scorecard)"
```

---

## Phase 13 — Cross-plugin integration tests (1 task)

### Task 30: Four cross-plugin integration tests

**Files:**
- Create: `plugins/integration_tests/test_superpower_bridge_skill_discovery.py`
- Create: `plugins/integration_tests/test_superpower_bridge_plugin_root.py`
- Create: `plugins/integration_tests/test_superpower_bridge_msft_smartart_import.py`
- Create: `plugins/integration_tests/test_superpower_bridge_end_to_end.py`

These mirror the existing pattern in `plugins/integration_tests/`. Skill discovery (skills exist with the right names), PLUGIN_ROOT discovery (the env-var override + cache lookup work), msft-smartart import (the loader resolves and imports correctly across plugin boundaries), and an end-to-end happy path against Spike 2's real /pptx output.

- [ ] **Step 1: Write the failing tests**

`plugins/integration_tests/test_superpower_bridge_skill_discovery.py`:

```python
"""Integration test: superpower-bridge skill manifests are discoverable from plugin root."""
import json
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = WORKTREE / "plugins" / "jack-tar-superpower-bridge"


def test_plugin_json_present_and_valid():
    plugin_json = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    assert plugin_json.exists()
    data = json.loads(plugin_json.read_text())
    assert data["name"] == "jack-tar-superpower-bridge"


def test_three_skills_present():
    for skill in ("bridge-brief", "enrich-deck", "verify"):
        assert (PLUGIN_ROOT / "skills" / skill / "SKILL.md").exists(), \
            f"missing skill {skill}"


def test_two_agents_present():
    for agent in ("narrative-brief-architect", "enrichment-cohesion-reviewer"):
        assert (PLUGIN_ROOT / "agents" / f"{agent}.md").exists(), \
            f"missing agent {agent}"
```

`plugins/integration_tests/test_superpower_bridge_plugin_root.py`:

```python
"""Integration test: PLUGIN_ROOT discovery shell snippet works for the bridge plugin."""
import os
import subprocess
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = WORKTREE / "plugins" / "jack-tar-superpower-bridge"


def test_env_var_override_takes_precedence(monkeypatch):
    """The bridge skills' PLUGIN_ROOT discovery shell snippet honours the env var."""
    monkeypatch.setenv("JACK_TAR_SUPERPOWER_BRIDGE_ROOT", str(PLUGIN_ROOT))
    cmd = '''python3 -c "
from pathlib import Path
import sys, os
if os.environ.get('JACK_TAR_SUPERPOWER_BRIDGE_ROOT'):
    print(os.environ['JACK_TAR_SUPERPOWER_BRIDGE_ROOT']); sys.exit()
print('NOT_FOUND')
"'''
    out = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          env={**os.environ, "JACK_TAR_SUPERPOWER_BRIDGE_ROOT": str(PLUGIN_ROOT)})
    assert out.stdout.strip() == str(PLUGIN_ROOT)
```

`plugins/integration_tests/test_superpower_bridge_msft_smartart_import.py`:

```python
"""Integration test: bridge's msft_smartart_loader resolves and imports msft-smartart."""
import sys
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = WORKTREE / "plugins" / "jack-tar-superpower-bridge"


def test_loader_imports_engine_render_and_inject(monkeypatch):
    sys.path.insert(0, str(PLUGIN_ROOT))
    # Ensure no stale src.* modules
    for k in list(sys.modules):
        if k == "src" or k.startswith("src."):
            del sys.modules[k]
    monkeypatch.setenv(
        "JACK_TAR_SUPERPOWER_BRIDGE_FORCE_MSFT_ROOT",
        str(WORKTREE / "plugins" / "jack-tar-msft-smartart"),
    )
    from src.msft_smartart_loader import load_msft_smartart_api
    api = load_msft_smartart_api()
    assert callable(api.engine.render)
    assert callable(api.inject)
    # Build a tiny carrier and verify it's a usable .pptx
    import tempfile
    from pathlib import Path as P
    with tempfile.TemporaryDirectory() as td:
        spec = {"graphic_type": "flowchart", "layout_id": "process1",
                "data": {"items": ["a", "b", "c"]}}
        result = api.engine.render(spec, P(td))
        assert P(result.output_path).exists()
```

`plugins/integration_tests/test_superpower_bridge_end_to_end.py`:

```python
"""Integration test: end-to-end happy path on Spike 1 Variant A.

Walks: analyse → build a tiny enrichment plan with one BG and one SmartArt
→ apply transactionally → verify outputs exist + open cleanly via python-pptx.
"""
import shutil
import sys
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
BRIDGE_ROOT = WORKTREE / "plugins" / "jack-tar-superpower-bridge"
MSFT_ROOT = WORKTREE / "plugins" / "jack-tar-msft-smartart"
SPIKE1 = WORKTREE / "docs" / "spikes" / "2026-04-23-pptx-marker-adherence" / "outputs" / "variant-a"
SPIKE2 = WORKTREE / "docs" / "spikes" / "2026-04-23-python-pptx-enrichment"


def test_end_to_end_happy_path(tmp_path, monkeypatch):
    sys.path.insert(0, str(BRIDGE_ROOT))
    for k in list(sys.modules):
        if k == "src" or k.startswith("src."):
            del sys.modules[k]
    monkeypatch.setenv("JACK_TAR_SUPERPOWER_BRIDGE_FORCE_MSFT_ROOT", str(MSFT_ROOT))

    from src.analyser import analyse_pptx
    from src.enrichment import EnrichmentPlan, EnrichmentItem, apply_enrichment
    from src.smartart_bridge import build_spec_from_slide

    # Stage the seed
    work_seed = tmp_path / "src.pptx"
    shutil.copy(SPIKE1 / "presentation.pptx", work_seed)
    shutil.copy(SPIKE1 / "build.js", tmp_path / "build.js")
    img_dir = tmp_path / "generated"; img_dir.mkdir()
    img = img_dir / "bg.png"; shutil.copy(SPIKE2 / "seed" / "placeholder.png", img)

    result = analyse_pptx(work_seed)
    assert result.total_markers >= 1

    # Find a BG marker
    bg_marker = None
    bg_slide_idx = None
    for s in result.slides:
        for m in s.markers:
            if m.kind == "BG":
                bg_marker = f"BG:{m.identifier}"
                bg_slide_idx = s.slide_index
                break
        if bg_marker:
            break
    assert bg_marker is not None

    plan = EnrichmentPlan(
        source_pptx=work_seed,
        output_pptx=tmp_path / "enriched.pptx",
        items=[EnrichmentItem(slide_index=bg_slide_idx, kind="background",
                                marker_name=bg_marker, asset_path=img,
                                action="apply")],
    )
    apply_enrichment(plan, allowed_image_roots=[img_dir])
    assert (tmp_path / "enriched.pptx").exists()

    from pptx import Presentation
    prs = Presentation(str(tmp_path / "enriched.pptx"))
    assert len(prs.slides) == 10


def test_end_to_end_smartart_path(tmp_path, monkeypatch):
    """Caveat-fix #13 — exercise the cross-plugin SmartArt path end-to-end.

    The BG-only end-to-end test above does not exercise loader → carrier →
    inject. That chain is the single most likely place for sys.modules
    contamination to surface; this test forces it.
    """
    sys.path.insert(0, str(BRIDGE_ROOT))
    for k in list(sys.modules):
        if k == "src" or k.startswith("src."):
            del sys.modules[k]
    monkeypatch.setenv("JACK_TAR_SUPERPOWER_BRIDGE_FORCE_MSFT_ROOT", str(MSFT_ROOT))

    from src.analyser import analyse_pptx
    from src.enrichment import EnrichmentPlan, EnrichmentItem, apply_enrichment
    from src.smartart_bridge import build_spec_from_slide, select_layout_for_slide

    work_seed = tmp_path / "src.pptx"
    shutil.copy(SPIKE1 / "presentation.pptx", work_seed)

    result = analyse_pptx(work_seed)
    smartart_marker_id = None
    smartart_slide_idx = None
    smartart_slide = None
    for s in result.slides:
        for m in s.markers:
            if m.kind == "SMARTART":
                smartart_marker_id = f"SMARTART:{m.identifier}"
                smartart_slide_idx = s.slide_index
                smartart_slide = s
                break
        if smartart_marker_id:
            break
    assert smartart_marker_id is not None, \
        "Variant A must include at least one SMARTART marker for this test"

    layout_id = select_layout_for_slide(smartart_slide, marker_id=smartart_marker_id)
    spec = build_spec_from_slide(smartart_slide, marker_id=smartart_marker_id,
                                   layout_id=layout_id)

    plan = EnrichmentPlan(
        source_pptx=work_seed,
        output_pptx=tmp_path / "enriched.pptx",
        items=[EnrichmentItem(
            slide_index=smartart_slide_idx, kind="smartart",
            marker_name=smartart_marker_id, asset_path=None,
            action="apply", smartart_spec=spec,
        )],
    )
    apply_enrichment(plan, allowed_image_roots=[tmp_path])

    out = tmp_path / "enriched.pptx"
    assert out.exists()

    # The injected SmartArt's diagram parts must be present
    import zipfile
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
    assert any("ppt/diagrams/data" in n for n in names), \
        "no diagram parts found in enriched deck — SmartArt injection failed silently"

    # Bridge's src.placeholder must STILL be importable as the bridge's module
    # after the cross-plugin call chain ran (sys.modules contamination guard).
    from src.placeholder import MARKER_RE
    assert MARKER_RE.match("IMAGE:foo") is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest plugins/integration_tests/test_superpower_bridge_*.py -v`
Expected: failures because the tests reference plugin files that exist (in earlier tasks) — these should actually PASS after Tasks 1-22. Confirm they pass:

- [ ] **Step 3: If any fail, the integration tests have surfaced a real cross-plugin gap**

Diagnose:
- `test_skill_discovery` failing → check the file paths / typos in earlier tasks
- `test_msft_smartart_import` failing → check `msft_smartart_loader.py` and the env-var name spelling
- `test_end_to_end` failing → check `analyse_pptx`, `apply_enrichment`, allowlist, marker grammar

Fix the underlying module, not the test.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest plugins/integration_tests/test_superpower_bridge_*.py -v`
Expected: 7 passed (3 skill_discovery + 1 plugin_root + 1 msft_smartart_import + 1 BG end_to_end + 1 SmartArt end_to_end).

- [ ] **Step 5: Commit**

```bash
git add plugins/integration_tests/test_superpower_bridge_*.py
git commit -m "test(integration): cross-plugin tests for superpower-bridge"
```

---

## Phase 14 — Marketplace metadata (1 task)

### Task 31: Bump marketplace + plugin versions; register the new plugin

**Files:**
- Modify: `.claude-plugin/marketplace.json`
- Modify: `plugins/jack-tar-msft-smartart/.claude-plugin/plugin.json`
- Modify: `plugins/jack-tar-deckhand/.claude-plugin/plugin.json`
- Test: `tests/test_marketplace_bridge_entry.py`

The marketplace cache is version-keyed (per [reference_marketplace_versioning.md] in user memory) — bumping plugins that the bridge depends on triggers refresh in other workspaces.

- [ ] **Step 1: Write the failing test**

`tests/test_marketplace_bridge_entry.py`:

```python
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_marketplace_includes_bridge_entry():
    data = json.loads((REPO / ".claude-plugin" / "marketplace.json").read_text())
    bridges = [p for p in data["plugins"] if p["name"] == "jack-tar-superpower-bridge"]
    assert len(bridges) == 1
    entry = bridges[0]
    assert entry["version"] == "0.1.0"
    assert entry["source"] == "./plugins/jack-tar-superpower-bridge"


def test_msft_smartart_bumped_to_1_2_0():
    data = json.loads((REPO / "plugins/jack-tar-msft-smartart/.claude-plugin/plugin.json").read_text())
    assert data["version"] == "1.2.0"


def test_deckhand_bumped_to_1_2_0():
    data = json.loads((REPO / "plugins/jack-tar-deckhand/.claude-plugin/plugin.json").read_text())
    assert data["version"] == "1.2.0"


def test_marketplace_msft_smartart_bumped_to_1_2_0():
    data = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
    msft = [p for p in data["plugins"] if p["name"] == "jack-tar-msft-smartart"][0]
    assert msft["version"] == "1.2.0"


def test_marketplace_deckhand_bumped_to_1_2_0():
    data = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
    deckhand = [p for p in data["plugins"] if p["name"] == "jack-tar-deckhand"][0]
    assert deckhand["version"] == "1.2.0"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_marketplace_bridge_entry.py -v`
Expected: 5 failures.

- [ ] **Step 3: Apply edits**

a. `.claude-plugin/marketplace.json` — append the bridge entry to the `plugins` array:

```json
{
  "name": "jack-tar-superpower-bridge",
  "description": "Wraps document-skills:pptx with narrative pre-brief (/bridge-brief) and post-hoc visual enrichment (/enrich-deck) — combine /pptx structural strength with jack-tar visual capabilities (AI backgrounds, element images, editable SmartArt)",
  "source": "./plugins/jack-tar-superpower-bridge",
  "version": "0.1.0"
}
```

b. Same file — bump `jack-tar-deckhand` and `jack-tar-msft-smartart` entries from `1.1.0` to `1.2.0` (their interaction surfaces gain new consumers — the bridge — per the canonical model delta).

c. `plugins/jack-tar-deckhand/.claude-plugin/plugin.json` — bump `"version": "1.1.0"` to `"version": "1.2.0"`.

d. `plugins/jack-tar-msft-smartart/.claude-plugin/plugin.json` — bump `"version": "1.1.0"` to `"version": "1.2.0"`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_marketplace_bridge_entry.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add .claude-plugin/marketplace.json plugins/jack-tar-deckhand/.claude-plugin/plugin.json plugins/jack-tar-msft-smartart/.claude-plugin/plugin.json tests/test_marketplace_bridge_entry.py
git commit -m "chore(marketplace): register superpower-bridge v0.1.0; bump msft-smartart + deckhand to 1.2.0"
```

---

## Phase 15 — Dogfooding gate (caveat #7; 3 tasks)

This phase is the release gate. Before we ship v0.1.0 publicly, we must validate the entire three-phase user flow end-to-end against a real /pptx-produced deck. This phase is mandatory — the persona doc's Item 5 (Vanilla-Agent validation) flips from amber to green only after Task 33 succeeds.

### Task 32: Restart Claude Code so cached agent definitions reload

**Files:** none (procedural step)

The two new persona definitions (`agents/narrative-brief-architect.md`, `agents/enrichment-cohesion-reviewer.md`) are cached at session start per the rule in CLAUDE.md ("Agent Definition Reloading"). Without a restart, Agent dispatches resolve to a stale "agent not found" or to a different fallback.

- [ ] **Step 1: Run all tests to confirm green state before the restart**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/ plugins/integration_tests/test_superpower_bridge_*.py tests/test_canonical_model_bridge_delta.py tests/test_persona_doc_completeness.py tests/test_marketplace_bridge_entry.py -v`
Expected: all green.

- [ ] **Step 2: Commit any uncommitted state**

```bash
git status
# if anything is uncommitted, commit it now — restart will not lose it but a clean state is easier to recover from
```

- [ ] **Step 3: Tell the user to restart Claude Code**

Output a single line:

```
RESTART REQUIRED: agent definitions in plugins/jack-tar-superpower-bridge/agents/ are loaded at session start. After restart, resume from Task 33.
```

Wait for the user to restart and confirm before proceeding.

- [ ] **Step 4: After restart, smoke-check the agents are visible**

Have the user run:
```
claude agents list | grep -E "narrative-brief-architect|enrichment-cohesion-reviewer"
```
Expected: both names appear.

If either is missing, the plugin install path may not have refreshed — the user can either run the symlink/refresh dance for their plugin cache or set the `JACK_TAR_SUPERPOWER_BRIDGE_ROOT` env var to point at the worktree's `plugins/jack-tar-superpower-bridge`.

(No commit — this is procedural.)

---

### Task 33: Dogfood Phase 1 — `/bridge-brief` against a real talk topic

**Files:**
- Create: `output/dogfood-bridge-run-1/creative-brief.md` (produced by the run)
- Create: `docs/superpowers/dogfooding/2026-04-23-bridge-dogfood-run-1.md` (the run log)

The first dogfood topic mirrors the demo deck used to validate the rendering strategy expansion: "Building AI Agents That Actually Work" — a 25-minute conference talk for engineers. Brief MUST set confidentiality `public` (this is real public material) and budget cap $1.50 (allows ~10 Flash iterations + ~5 Pro shots).

- [ ] **Step 1: Set up the dogfood directory**

```bash
mkdir -p output/dogfood-bridge-run-1
cd output/dogfood-bridge-run-1
```

- [ ] **Step 2: Run `/bridge-brief`**

```
/jack-tar-superpower-bridge:bridge-brief "Building AI Agents That Actually Work" --duration 25 --audience "conference engineers" --confidentiality public --budget-cap 1.50
```

The agent will propose narrative arcs, you (the human user) select Problem-Solution, agree on a takeaway and visual personality, and approve the brief.

- [ ] **Step 3: Verify the brief on disk**

```bash
ls -la creative-brief.md
.venv/bin/python -c "
from pathlib import Path
import sys
sys.path.insert(0, '$PWD/../../plugins/jack-tar-superpower-bridge')
from src.creative_brief import parse_brief_markdown
brief = parse_brief_markdown(Path('creative-brief.md').read_text())
print(f'Topic: {brief.topic}')
print(f'Confidentiality: {brief.confidentiality}')
print(f'Budget cap: \${brief.budget_cap_usd}')
print('OK' if 'objectName' in brief.placeholder_instructions else 'WARNING: brief missing objectName note')
"
```
Expected: parses cleanly, contains `objectName` reference.

- [ ] **Step 4: Verify the measurement entry**

```bash
cat bridge-measurements.jsonl
```
Expected: one `kind: brief` line with `approval_turns` ≤ 2 and `structural_complete: true`.

- [ ] **Step 5: Run `/pptx` against the brief**

```
/pptx "Build a 25-slide presentation following this brief: $(cat creative-brief.md)"
```

Let /pptx do its thing. When it finishes, you should have `presentation.pptx` and `build.js` in the dogfood directory.

- [ ] **Step 6: Sanity-check marker adherence (Spike 1 measurement)**

```bash
.venv/bin/python -c "
import sys
sys.path.insert(0, '../../plugins/jack-tar-superpower-bridge')
from src.analyser import analyse_pptx
r = analyse_pptx('presentation.pptx')
print(f'Total slides: {r.total_slides}')
print(f'Total markers: {r.total_markers}')
print(f'JS fallback used: {r.js_fallback_used}')
print(f'Duplicate marker ids: {r.duplicate_marker_ids}')
"
```

Decision gate:
- **Markers ≥ 3 from OOXML directly (js_fallback_used=False)** → /pptx honoured the brief; the bridge is on the happy path. Proceed to Task 34.
- **0 OOXML markers, JS fallback recovered N markers** → /pptx used `name:` instead of `objectName:`. The bridge handles this correctly via the fallback, but record this in the dogfood run log as a real-world observation (the brief told /pptx to use objectName; /pptx didn't). Proceed to Task 34 anyway — this is the case the fallback exists for.
- **0 markers from both sources** → either /pptx ignored the brief entirely, or there's a bug in the analyser that the integration tests didn't catch. Halt here and diagnose.

- [ ] **Step 7: Write the dogfood run log so far**

Create `docs/superpowers/dogfooding/2026-04-23-bridge-dogfood-run-1.md` with these sections so far:

```markdown
# Bridge Dogfood Run 1

**Date:** 2026-04-23
**Topic:** Building AI Agents That Actually Work
**Audience:** conference engineers
**Duration:** 25 min
**Confidentiality:** public
**Budget cap:** $1.50

## Phase 1 — /bridge-brief

- Approval turns: <N>
- Brief saved to: output/dogfood-bridge-run-1/creative-brief.md
- Brief contains objectName note: yes/no
- Subjective: <one sentence on whether the agent's arc proposals were useful>

## Phase 2 — /pptx

- Slides produced: <N>
- Build script size: <bytes>
- Marker adherence (OOXML primary): <count>
- Marker adherence (JS fallback): <count if applicable>
- JS fallback fired: yes/no
- Subjective: <one sentence on whether /pptx followed the brief structurally>

## Phase 3 — /enrich-deck

(Filled in during Task 34.)

## Verdict

(Filled in during Task 35.)
```

- [ ] **Step 8: Commit (the brief itself + the partial log)**

```bash
git add output/dogfood-bridge-run-1/creative-brief.md output/dogfood-bridge-run-1/build.js output/dogfood-bridge-run-1/presentation.pptx docs/superpowers/dogfooding/2026-04-23-bridge-dogfood-run-1.md
git commit -m "dogfood(bridge): Phase 1+2 — /bridge-brief and /pptx run-through"
```

(If `output/` is gitignored, `git add -f` the brief, build.js, and pptx — they're evidence and need to live in the repo for the dogfood log to make sense.)

---

### Task 34: Dogfood Phase 3 — `/enrich-deck` against the produced .pptx

**Files:**
- Modify: `docs/superpowers/dogfooding/2026-04-23-bridge-dogfood-run-1.md` (extend with Phase 3 results)
- Output: `output/dogfood-bridge-run-1/presentation-enriched.pptx`
- Output: `output/dogfood-bridge-run-1/enrichment-report.md`

- [ ] **Step 1: Run /enrich-deck**

```
/jack-tar-superpower-bridge:enrich-deck output/dogfood-bridge-run-1/presentation.pptx
```

Walk through the menu. Approve at minimum:
- All marked BG enrichments
- All marked IMAGE enrichments
- All marked SMARTART enrichments (decline `apply_clear_overlap` on first pass to test the verifier's surfacing in the menu)

Skip suggested unmarked enrichments to keep the run scope bounded.

- [ ] **Step 2: Watch the budget tracker as it runs**

The orchestrator should print per-slide cost charges. Confirm:
- Ollama drafts are free
- Each cloud generation deducts ~$0.067 (Flash) or $0.134 (Pro)
- Each review deducts ~$0.005 (Haiku) per call (caveat #6 — review charges land too)
- Total stays under the $1.50 cap

- [ ] **Step 3: VIEW EVERY GENERATED IMAGE before assembly**

Per CLAUDE.md "MANDATORY: Visual Output Review" — when each Ollama draft + cloud generation completes, the orchestrator should be displaying the image. As the human dogfooder, confirm:
- AI backgrounds are atmospheric and don't overwhelm text
- Element images fit their reserved geometry
- No garbled text artefacts in any image
- Brand palette respected on cloud generations

If any image is broken, refine the prompt and retry — the per-image review cycle handles this. If you accept_with_issues anything, note it in the dogfood log.

- [ ] **Step 4: After delivery, view the assembled deck**

```bash
tools/pptx_to_pdf.sh output/dogfood-bridge-run-1/presentation-enriched.pptx
open output/dogfood-bridge-run-1/presentation-enriched.pdf
```

Walk every slide. Validate:
- All BG slides have backgrounds applied
- All IMAGE slides have pictures at the correct geometry
- All SMARTART slides have editable SmartArt rendering correctly
- No marker placeholder rectangles survived (all should be replaced)
- No partial enrichment evidence (the transactional gate worked)

- [ ] **Step 5: Inspect the enrichment report**

```bash
cat output/dogfood-bridge-run-1/enrichment-report.md
```

Validate:
- All required sections present (Summary / Per-enrichment ledger / Flags / PowerPoint rendering note)
- Cost ledger sums to the spent total reported by the orchestrator
- Cohesion verdicts match what you saw

- [ ] **Step 6: Inspect the cohesion verdicts**

The cohesion-reviewer's per-slide verdicts should be reported by the orchestrator. Decision gate:

- **Aggregate verdict = pass** → move to Task 35.
- **Aggregate verdict = requires_revision** with `record_only` actions → record in dogfood log; treat as "shipped with notes" — the persona's job is to surface notes, not block delivery on suggestions.
- **Aggregate verdict = requires_revision** with `regenerate` or `retry_clear_overlap` actions auto-executed → confirm the orchestrator actually executed them (you should have seen the second-pass image generation or the SmartArt re-injection); confirm the second pass produced a passing verdict.
- **Aggregate verdict = requires_revision** with `surface_to_user` action → the orchestrator should have shown you the slide and asked. If you accepted, that's expected; if you rejected and dropped the enrichment, also expected.

Any path that doesn't match the decision table is a real defect — diagnose and fix before Task 35.

- [ ] **Step 7: Inspect measurement files**

```bash
cat output/dogfood-bridge-run-1/bridge-run/bridge-measurements.jsonl
cat output/dogfood-bridge-run-1/bridge-run/bridge-cost-ledger.jsonl
```

Validate:
- One `kind: brief` row + one `kind: enrichment` row
- Cost ledger has both `kind: generation` AND `kind: review` rows (caveat #6 evidence)
- Sum of cost ledger ≤ budget cap

- [ ] **Step 7.5: Run the automated NO-GO evidence script**

Per the panel finding (ai-test-engineer), the dogfooding gate's most common silent failure mode is "an enrichment didn't actually replace its placeholder rectangle." A 10-line script catches that automatically without subjective deck-walking:

```bash
.venv/bin/python - <<PY
"""Automated NO-GO evidence for the dogfood gate.

Asserts:
  - Output file exists
  - Output is a valid .pptx (opens with python-pptx)
  - No surviving IMAGE:/SMARTART:/BG: marker shapes (every approved enrichment
    must have replaced its placeholder; surviving markers = silent failure)
  - SmartArt diagram parts are present if the enrichment plan included SmartArt
"""
import sys, json, zipfile
from pathlib import Path
from pptx import Presentation

src_path = Path("output/dogfood-bridge-run-1/presentation.pptx")
out_path = Path("output/dogfood-bridge-run-1/presentation-enriched.pptx")
report_path = Path("output/dogfood-bridge-run-1/enrichment-report.md")

errors: list[str] = []

if not out_path.exists():
    errors.append(f"OUTPUT MISSING: {out_path}")
    print("\n".join(errors)); sys.exit(1)

try:
    prs = Presentation(str(out_path))
except Exception as exc:
    errors.append(f"OUTPUT NOT A VALID PPTX: {exc}")
    print("\n".join(errors)); sys.exit(1)

surviving_markers = []
for idx, slide in enumerate(prs.slides, 1):
    for shape in slide.shapes:
        name = (shape.name or "")
        if name.startswith(("IMAGE:", "SMARTART:", "BG:")):
            surviving_markers.append((idx, name))

if surviving_markers:
    errors.append(f"SURVIVING MARKERS (enrichment failed silently): {surviving_markers}")

if not report_path.exists():
    errors.append(f"REPORT MISSING: {report_path}")
else:
    text = report_path.read_text()
    if "smartart" in text.lower():
        with zipfile.ZipFile(out_path) as zf:
            has_diagrams = any("ppt/diagrams/data" in n for n in zf.namelist())
        if not has_diagrams:
            errors.append("REPORT MENTIONS SMARTART BUT NO DIAGRAM PARTS IN OUTPUT")

if errors:
    print("NO_GO_EVIDENCE:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("GO_EVIDENCE: output exists, opens cleanly, no surviving markers, "
          "diagram parts consistent with report")
PY
```

Decision gate:
- Exit 0 → automated NO-GO checks pass; proceed to subjective Step 8.
- Exit 1 → automated NO-GO triggered; halt and diagnose. Do NOT proceed to Task 35 verdict until the underlying defect is fixed and the script exits 0.

- [ ] **Step 8: Extend the dogfood log with Phase 3 results**

Fill in the Phase 3 section of `docs/superpowers/dogfooding/2026-04-23-bridge-dogfood-run-1.md`:

```markdown
## Phase 3 — /enrich-deck

- Enrichments applied: <count by kind>
- Cloud calls: <N flash, M pro>
- Review costs: $<X.XX>
- Generation costs: $<Y.YY>
- Total: $<Z.ZZ> of $1.50 cap
- Cohesion aggregate verdict: pass | requires_revision
- Cohesion actions auto-executed: <list>
- Cohesion actions surfaced to user: <list>
- Visual review notes: <subjective notes from walking the assembled deck>

### Defects observed (if any)

- <Each defect with module name + reproduction + impact>

### Three-phase UX notes

- Where the user flow felt natural
- Where the user flow felt awkward (handoffs between /bridge-brief, /pptx, /enrich-deck)
- Brief invocation friction
- Did the brief survive the /pptx round-trip in a usable form?
```

- [ ] **Step 9: Commit**

```bash
git add output/dogfood-bridge-run-1/presentation-enriched.pptx output/dogfood-bridge-run-1/enrichment-report.md docs/superpowers/dogfooding/2026-04-23-bridge-dogfood-run-1.md
git commit -m "dogfood(bridge): Phase 3 — /enrich-deck full run with measurement evidence"
```

---

### Task 35: Dogfooding gate verdict + readiness scorecard flip

**Files:**
- Modify: `docs/superpowers/dogfooding/2026-04-23-bridge-dogfood-run-1.md` (write the Verdict section)
- Modify: `docs/architecture/ai-personas/superpower-bridge-personas.md` (flip Item 5 from amber to green if gate passed)
- Modify: `CLAUDE.md` (move Superpower Bridge from "design complete, ready for plan" to "v1 shipping" with the dogfood evidence cited)

- [ ] **Step 1: Decide the verdict**

Apply this rubric. ALL conditions in the GO column must hold; failure of any single condition flips the verdict toward GO WITH CAVEATS or NO-GO.

| Condition | GO requires |
|-----------|-------------|
| Three phases ran end-to-end | yes |
| Task 34 Step 7.5 automated NO-GO script exited 0 | yes |
| Marker adherence ≥ 80% of marked enrichments delivered as expected | yes |
| Cohesion aggregate verdict | `pass` (any `requires_revision` flips to GO WITH CAVEATS) |
| Budget respected (no overdraft) | yes |
| Caveat #6 evidence: review costs landed in `bridge-cost-ledger.jsonl` with `kind: review` rows | yes |
| Transactional gate: no partial output observed | yes |
| Allowlist enforced: no out-of-allowlist image embedded | yes |
| Tripartite owners are nominated (not TBD) per Task 29 v1.0 doc | yes |
| Spec-contract violations (transactional gate left a partial file; budget cap breached; allowlist bypassed; agent dispatched without source-tag) | NONE |

Verdict mapping:
- All conditions hold → **GO**
- Conditions hold but cohesion aggregate is `requires_revision` with non-blocking actions only, OR ≥1 minor defect that doesn't violate a spec contract → **GO WITH CAVEATS** (list each caveat as a follow-up GitHub issue)
- Any spec-contract violation, OR Task 34 Step 7.5 exited non-zero, OR any phase failed end-to-end → **NO-GO** — fix the root cause and re-run from Task 33

- [ ] **Step 2: Write the Verdict section**

Append to `docs/superpowers/dogfooding/2026-04-23-bridge-dogfood-run-1.md`:

```markdown
## Verdict

**GO** | **GO WITH CAVEATS** | **NO-GO**

### Evidence summary

- Three phases ran end-to-end: yes/no
- Marker adherence: <count>/<requested>
- Cohesion aggregate: pass | requires_revision
- Budget respected: yes/no (spent $X.XX of $1.50)
- Caveat #6 evidence: review costs landed in ledger (yes/no)
- Transactional gate: no partial output observed (yes/no)
- Allowlist enforced: no out-of-allowlist image embedded (yes/no)

### Caveats / Follow-ups

- <One bullet per caveat with a proposed GitHub issue title>

### Decision

Ship v0.1.0 / Hold for fixes / Re-run dogfood after <change>
```

- [ ] **Step 3: If GO or GO WITH CAVEATS — flip readiness scorecard Item 5**

Edit `docs/architecture/ai-personas/superpower-bridge-personas.md`. Change the Item 5 row in the readiness scorecard:

```
| 5 | Vanilla-Agent validation | amber | green | Phase 15 dogfooding gate (docs/superpowers/dogfooding/2026-04-23-bridge-dogfood-run-1.md) — verdict GO |
```

- [ ] **Step 4: Update top-level CLAUDE.md to reflect the shipping state**

Edit the `Current Status (2026-04-23)` section:

a. Replace the "**Superpower Bridge (issue #53) — design complete, ready for implementation plan.**" line with:

```markdown
- **Superpower Bridge (issue #53) — v0.1.0 dogfood complete, ready for v0.1 release.** New plugin `jack-tar-superpower-bridge` shipping with `/bridge-brief` (Phase 1), `/enrich-deck` (Phase 3), and `/verify` skills. Two new AI personas (Narrative Brief Architect — Sonnet; Enrichment Cohesion Reviewer — Haiku/Sonnet escalate). Implementation plan: `docs/superpowers/plans/2026-04-23-superpower-bridge.md`. Dogfood run: `docs/superpowers/dogfooding/2026-04-23-bridge-dogfood-run-1.md`. Spec: `docs/superpowers/specs/2026-04-22-superpower-bridge-design.md`.
```

b. Bump test counts where they appear (the bridge added ~120 unit tests and ~6 integration tests).

- [ ] **Step 5: Run the full test suite one last time**

Run: `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/ plugins/integration_tests/ tests/ -v --tb=short`
Expected: all green; total count ≥ previous baseline + 120.

- [ ] **Step 6: Commit the gate**

```bash
git add docs/superpowers/dogfooding/2026-04-23-bridge-dogfood-run-1.md docs/architecture/ai-personas/superpower-bridge-personas.md CLAUDE.md
git commit -m "dogfood(bridge): GO verdict; readiness Item 5 → green; CLAUDE.md to v0.1 shipping"
```

- [ ] **Step 7: If GO, push the branch and open a PR**

```bash
git push -u origin feat/superpower-bridge
gh pr create --title "feat: jack-tar-superpower-bridge plugin (v0.1.0) — Issue #53" \
  --body "$(cat <<'EOF'
## Summary

- New plugin `jack-tar-superpower-bridge` wraps `document-skills:pptx` with `/bridge-brief` (narrative pre-brief) + `/enrich-deck` (post-hoc visual enrichment)
- Two new AI personas: Narrative Brief Architect (Sonnet, Tier 1) and Enrichment Cohesion Reviewer (Haiku → Sonnet escalate, Tier 1)
- Reuses existing Image Reviewer and Prompt Engineer agents with minimal contract extensions
- HYBRID analyser (OOXML primary via python-pptx + esprima JS-AST fallback for marker recovery; JS parsed never executed)
- Transactional all-or-nothing enrichment with try/finally cleanup + atomic rename
- Image-path allowlist + .pptx pre-flight + hardened XML parser (security & privacy section of the spec)
- Privacy tiering (public/internal/restricted) and budget cap (default $1.00, covers BOTH generation AND review costs — caveat #6)
- All 7 caveats from the spec's final critical review are addressed
- Canonical model bumped to v1.5.0 with Bridge Services L1 + 2 personas + 4 skills + 10 interactions + Cross-Domain SOP register entry + 5 dependency register entries
- Dogfood run: `docs/superpowers/dogfooding/2026-04-23-bridge-dogfood-run-1.md` — verdict GO

## Test plan

- [ ] `.venv/bin/pytest plugins/jack-tar-superpower-bridge/tests/ plugins/integration_tests/ tests/` all pass
- [ ] `/jack-tar-superpower-bridge:verify` reports `STATUS: FULLY_AVAILABLE`
- [ ] Dogfood deck opens cleanly in PowerPoint Mac with all enrichments rendered
- [ ] Enrichment report cost total matches budget tracker

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

(Skip if NO-GO — fix and re-dogfood.)

---

## Self-review (this is YOUR check before declaring the plan done — see writing-plans skill)

Once Tasks 1–35 are written, run the writing-plans skill's self-review. Confirm each item:

1. **Spec coverage:** every requirement from `docs/superpowers/specs/2026-04-22-superpower-bridge-design.md` traces to a task. Walk the spec section-by-section:
   - § Phase 1 (Narrative Pre-Brief) → Tasks 11, 12, 13
   - § Phase 1 § Section A/B/C → Task 11 (persona) + Task 5 (CreativeBrief dataclass enforces three-section roundtrip)
   - § Phase 1 PptxGenJS objectName note → Task 11 (persona instructs use of objectName) + Task 5 (CreativeBrief.to_markdown emits the note) + Task 8 (JS parser recognises both objectName and name) + Task 23 (cohesion reviewer doesn't repeat the requirement)
   - § Phase 2 (Superpower Build) → not bridge work; the brief flows through user invocation of /pptx
   - § Phase 3.1 (Deck Analysis) → Tasks 7, 8, 9, 10
   - § Phase 3.2 (Enrichment Menu) → Task 26 (skill steps)
   - § Phase 3.3 (Asset Generation) → Tasks 14, 15, 16, 17, 18
   - § Phase 3.4 (Draft Assembly + Internal Review) → Tasks 19, 20, 21, 22, 24, 26
   - § Phase 3.5 (Delivery) → Task 25, Task 26 step 13
   - § Security & Privacy (image-path allowlist) → Task 4, Task 19, Task 20
   - § Security & Privacy (JS parsing read-only) → Task 8 (test_parser_never_calls_subprocess_eval_exec_or_require)
   - § Security & Privacy (.pptx pre-flight) → Task 4, Task 10 (orchestrator runs preflight)
   - § Security & Privacy (atomic writes) → Task 22
   - § Security & Privacy (privacy tiering) → Task 15, Task 5 (CreativeBrief.confidentiality), Task 26 (orchestrator gates)
   - § Security & Privacy (budget cap) → Task 14 (BudgetCap), Task 13 (cost ledger), Task 16 (cycle charges both kinds)
   - § Plugin Structure → Tasks 1, 31
   - § Personas → Tasks 11, 23, 29
   - § Enrichment Report Schema → Task 25
   - § Risk Register — every row → covered through tasks above; spike-validated rows reference the spike directories
2. **Caveat coverage:** all 7 caveats from the spec review traced to tasks (matrix at top of plan).
3. **Placeholder scan:** no "TBD", "implement later", "fill in details", "add appropriate error handling", "similar to Task N", "write tests for the above" without actual test code. Confirmed.
4. **Type consistency:** the dataclasses defined in Task 2 (`SlideFacts`, `Marker`, `EnrichmentChoice`, `AnalyserResult`, `OverlapWarning`) and Task 5 (`CreativeBrief`) and Task 14 (`BudgetCap`, `CostEvent`) and Task 15 (`PrivacyTierGate`) and Task 16 (`ImageGenerationRequest`, `ImageGenerationResult`) and Task 22 (`EnrichmentItem`, `EnrichmentPlan`) and Task 24 (`SlideVerdict`, `DeckVerdict`, `AutoAction`) and Task 25 (`EnrichmentReport`, `EnrichmentLedgerEntry`) are referenced consistently across all subsequent tasks. Field/method names match.
5. **File-path consistency:** every test path under `plugins/jack-tar-superpower-bridge/tests/`; every src path under `plugins/jack-tar-superpower-bridge/src/`; every cross-plugin test under `plugins/integration_tests/`.

---

## Caveat-to-task verification matrix

| Caveat | Tasks | Concrete deliverable |
|--------|-------|----------------------|
| 1 — Image-path allowlist extension mechanism | 4 (`security.py`), 19 + 20 (ops resolve through allowlist), 26 (skill provides `[generated/, carriers/]` defaults; spec amendment required to extend) | `resolve_within_allowlist` is the single chokepoint; extension = passing additional roots to the skill, documented in /enrich-deck SKILL.md |
| 2 — Cohesion Reviewer verdict → auto-regen decision table | 23 (persona enumerates verdicts), 24 (`decide_action` table), 26 (skill Step 10 acts on AutoAction kinds) | The exact table is encoded in `cohesion_review.decide_action()` with one branch per (verdict, severity, kind) |
| 3 — Measurement instrumentation as P0 | 13 (`measurement.py` lands in Phase 3 alongside the bridge-brief skill, not deferred), 12 (skill records brief runs), 26 (skill records enrichment runs), 16 (cycle records cost events) | `bridge-measurements.jsonl` + `bridge-cost-ledger.jsonl` written every run |
| 4 — smartart-extractor reuse vs. bridge-side re-parsing | 18 (`smartart_bridge.py` decision recorded in module docstring) | Bridge-side parsing chosen; rationale written into the module |
| 5 — `.bsa/models/jack-tar-deckhand.json` v1.5.0 canonical delta | 28 (model edits + Step 3.5 schema validation + CAC field) + 29 (persona doc bump with consolidated tripartite + 5-tier measurement) | Model + doc both at v1.5.0 with Bridge Services L1 + CAC entry + tripartite owners nominated |
| 6 — Budget cap covers image review (not just generation) | 14 (`BudgetCap.charge(kind=...)` accepts both), 16 (cycle charges `kind="review"` UNCONDITIONALLY in Phases A, B, C — halts with `halted_budget` if unaffordable) | Phase B test `test_phase_b_review_charge_unconditional_halts_on_overdraft` is the regression guard |
| 7 — Three-phase UX dogfooding gate | 32, 33, 34, 35 | `docs/superpowers/dogfooding/2026-04-23-bridge-dogfood-run-1.md` produced; Task 34 Step 7.5 automated NO-GO script run; Task 35 GO rubric checks 10 conditions including owner nomination; readiness Item 5 flipped on success |

---

## Revision history

**v1.0 (2026-04-23 — initial draft)** — 35 tasks across 16 phases. Submitted to a six-reviewer panel.

**v1.1 (2026-04-23 — panel revision pass)** — addressed all 9 convergent panel findings plus 6 high-impact single-reviewer items:

| Finding | Resolution |
|---------|------------|
| Agent-dispatch boundary broken in cycle | Task 17 redesigned: `cycle_state.py` pure-functional state primitives the SKILL.md drives between agent dispatches. `make_live_callables` factory (which silently passed every image) is removed. Task 26 Step 5 rewritten as a SKILL.md-owned loop using `advance_after_review`. |
| `apply_enrichment` skipped pre-flight | Task 22: `preflight_pptx(src)` is the first call inside the try block; `test_apply_enrichment_runs_preflight_first` added. |
| `safe_xml_parser` not wired into production | Task 4: docstring documents python-pptx as the OOXML threat-model boundary; safe_xml_parser is required for all direct lxml parsing the bridge does. |
| `sys.modules` contamination after loader | Task 6: loader snapshots caller `src.*` modules + sys.path[0] BEFORE swap, restores them in `finally`; `test_loader_restores_bridge_src_modules_after_load` added. |
| JS-guard test patched 3 of 9 enumerated targets | Task 8: rewritten with `contextlib.ExitStack` to apply ALL patches; expanded target list to include `os.system`, `os.popen`, `subprocess.getoutput`, `getstatusoutput`, `compile`. |
| Phase B budget review-charge conditional | Task 16: Phase B AND Phase C review charges are now unconditional with explicit `halted_budget` halt; `test_phase_b_review_charge_unconditional_halts_on_overdraft` regression guard added. |
| Caveat tracker drift (top vs bottom) | Top tracker rewritten to match the bottom matrix exactly. |
| Tripartite owners as TBD forever | Task 29: consolidated tripartite (Steve Jones × 3) for v1.0 with documented split trigger. Item 3 of readiness scorecard flips green. |
| Cross-Domain SOP entry missing CAC field | Task 28: SOP entry now carries `cac` object + `changeTrigger` string; test asserts presence. |
| Schema may not validate new top-level keys | Task 28 Step 3.5 added: verify (and extend) `.bsa/design/canonical-service-domain-model-schema.json` for `crossDomainSopRegister` + `dependencyRegister`. |
| Recall hook unimplementable | Task 29: explicitly demoted to offline analysis with documented proxy; test asserts the demotion. |
| Measurement hooks clustered in Tier 4 | Task 29: full 5-tier blueprint added (T1 strategic, T2 service-level, T3 XLA, T4 activity, T5 contextual); test asserts all 5 tiers present. |
| Integration tests don't exercise SmartArt path | Task 30: `test_end_to_end_smartart_path` added; exercises loader → carrier → inject and asserts no sys.modules contamination. |
| Dogfood gate has no automated NO-GO check | Task 34 Step 7.5 added: automated evidence script asserts no surviving placeholder shapes + report/diagram consistency. |
| Live callable stubs silently pass | Resolved by Finding 1's redesign — stubs no longer exist. |







