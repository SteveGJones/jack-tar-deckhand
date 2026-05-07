# Spike: /pptx Marker Adherence

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Determine whether the `/pptx` superpower will reliably emit named placeholder shapes (e.g. `IMAGE:agent-architecture`, `SMARTART:flowchart`, `BG:dramatic-contrast`) when instructed to via a creative brief, and produce findings that either confirm the Superpower Bridge Phase 1/2 handoff as designed or reshape the marker protocol.

**Architecture:** This is a time-boxed investigation (target: one working day). Three variant briefs with escalating instruction specificity are fed to the `/pptx` superpower. Each output is parsed to count named shapes that match the marker protocol. Adherence rates plus qualitative observations feed a findings document with a go / adjust / no-go decision.

**Tech Stack:** python-pptx (shape inspection), pytest (for the analyser's unit tests), the `document-skills:pptx` skill (the superpower under test), jq / python for counting.

**Out of scope:**
- Any enrichment logic — this spike only measures marker emission, nothing downstream.
- Modifying the pptx superpower — we observe, we do not touch.
- Writing the real bridge plugin code — we only write throwaway analysis scripts.

---

## File Structure

All spike artefacts live under a single directory so they can be archived or thrown away cleanly.

```
docs/spikes/2026-04-23-pptx-marker-adherence/
  README.md                        # Findings report (written last)
  briefs/
    brief-a-minimal.md             # Variant A: bare mention of markers
    brief-b-explicit.md            # Variant B: marker protocol table
    brief-c-exemplar.md            # Variant C: protocol + worked example slide
  outputs/
    variant-a/presentation.pptx    # /pptx output for each variant
    variant-a/build.js             # build script if /pptx emits one
    variant-b/presentation.pptx
    variant-b/build.js
    variant-c/presentation.pptx
    variant-c/build.js
  tools/
    analyse_markers.py             # Parse .pptx → list named shapes + marker counts
    score_adherence.py             # Compare requested vs. actual markers
  results/
    variant-a-report.json          # Per-variant machine-readable results
    variant-b-report.json
    variant-c-report.json
    summary.json                   # Aggregate
  tests/
    test_analyse_markers.py        # Unit tests for the analyser (TDD)
    fixtures/
      minimal.pptx                 # Hand-built fixture with known markers
```

**Files that matter beyond the spike:**
- `docs/spikes/2026-04-23-pptx-marker-adherence/README.md` — the only artefact the rest of the project will read.

Everything under `tools/` and `tests/` is disposable. If the spike succeeds and the bridge plugin is built, the analyser may be cribbed into `plugins/jack-tar-superpower-bridge/src/analyser.py` — but do not engineer for that outcome yet.

---

## Task 1: Scaffold the spike directory

**Files:**
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/briefs/.gitkeep`
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/.gitkeep`
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/tools/.gitkeep`
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/results/.gitkeep`
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/tests/fixtures/.gitkeep`

- [ ] **Step 1: Create the directory tree**

```bash
mkdir -p docs/spikes/2026-04-23-pptx-marker-adherence/{briefs,outputs,tools,results,tests/fixtures}
touch docs/spikes/2026-04-23-pptx-marker-adherence/{briefs,outputs,tools,results,tests/fixtures}/.gitkeep
```

- [ ] **Step 2: Commit the scaffold**

```bash
git add docs/spikes/2026-04-23-pptx-marker-adherence
git commit -m "spike: scaffold pptx marker adherence directory"
```

---

## Task 2: Write the minimal fixture for analyser TDD

The analyser needs a known-correct input before we point it at real /pptx output. Build a tiny .pptx by hand with three named shapes — one for each marker type — so we can assert against ground truth.

**Files:**
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/tests/fixtures/build_minimal.py`

- [ ] **Step 1: Write the fixture builder**

```python
"""Build a minimal .pptx with three named marker shapes for analyser tests."""
from pptx import Presentation
from pptx.util import Inches

prs = Presentation()
blank = prs.slide_layouts[6]

# Slide 1: IMAGE marker
slide1 = prs.slides.add_slide(blank)
img_shape = slide1.shapes.add_shape(1, Inches(1), Inches(1), Inches(3), Inches(2))
img_shape.name = "IMAGE:agent-architecture"
img_shape.text_frame.text = "IMAGE:agent-architecture"

# Slide 2: SMARTART marker
slide2 = prs.slides.add_slide(blank)
sa_shape = slide2.shapes.add_shape(1, Inches(1), Inches(1), Inches(5), Inches(3))
sa_shape.name = "SMARTART:flowchart"
sa_shape.text_frame.text = "SMARTART:flowchart"

# Slide 3: BG marker (small corner label)
slide3 = prs.slides.add_slide(blank)
bg_shape = slide3.shapes.add_shape(1, Inches(0.2), Inches(0.2), Inches(1.5), Inches(0.3))
bg_shape.name = "BG:dramatic-contrast"
bg_shape.text_frame.text = "BG:dramatic-contrast"

# Slide 4: non-marker shape (distractor — must not be counted)
slide4 = prs.slides.add_slide(blank)
other = slide4.shapes.add_shape(1, Inches(1), Inches(1), Inches(2), Inches(1))
other.name = "TitleBox"
other.text_frame.text = "Plain content, no marker"

prs.save("docs/spikes/2026-04-23-pptx-marker-adherence/tests/fixtures/minimal.pptx")
print("Wrote minimal.pptx with 3 markers + 1 distractor")
```

- [ ] **Step 2: Run it to produce the fixture**

Run: `.venv/bin/python docs/spikes/2026-04-23-pptx-marker-adherence/tests/fixtures/build_minimal.py`
Expected stdout: `Wrote minimal.pptx with 3 markers + 1 distractor`
Expected file: `docs/spikes/2026-04-23-pptx-marker-adherence/tests/fixtures/minimal.pptx` (~30 KB)

- [ ] **Step 3: Commit**

```bash
git add docs/spikes/2026-04-23-pptx-marker-adherence/tests/fixtures/
git commit -m "spike: add minimal pptx fixture with known markers"
```

---

## Task 3: Write the analyser — TDD

The analyser parses a .pptx and returns every shape whose name matches the marker grammar `(IMAGE|SMARTART|BG):<identifier>`.

**Files:**
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/tests/test_analyse_markers.py`
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/tools/analyse_markers.py`

- [ ] **Step 1: Write the failing test**

```python
"""Unit tests for the marker analyser."""
import sys
from pathlib import Path

SPIKE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE_DIR / "tools"))

from analyse_markers import analyse_pptx

FIXTURE = SPIKE_DIR / "tests" / "fixtures" / "minimal.pptx"


def test_finds_all_three_marker_types():
    report = analyse_pptx(FIXTURE)
    kinds = sorted(m["kind"] for m in report["markers"])
    assert kinds == ["BG", "IMAGE", "SMARTART"]


def test_extracts_identifier_after_colon():
    report = analyse_pptx(FIXTURE)
    ids = {m["kind"]: m["identifier"] for m in report["markers"]}
    assert ids["IMAGE"] == "agent-architecture"
    assert ids["SMARTART"] == "flowchart"
    assert ids["BG"] == "dramatic-contrast"


def test_records_slide_index_per_marker():
    report = analyse_pptx(FIXTURE)
    for m in report["markers"]:
        assert m["slide_index"] >= 1, f"slide_index should be 1-based, got {m}"


def test_records_shape_geometry():
    report = analyse_pptx(FIXTURE)
    img = next(m for m in report["markers"] if m["kind"] == "IMAGE")
    assert "left_emu" in img and img["left_emu"] > 0
    assert "top_emu" in img and img["top_emu"] > 0
    assert "width_emu" in img and img["width_emu"] > 0
    assert "height_emu" in img and img["height_emu"] > 0


def test_ignores_non_marker_shapes():
    report = analyse_pptx(FIXTURE)
    names = [m["shape_name"] for m in report["markers"]]
    assert "TitleBox" not in names, "Distractor shape should not be treated as a marker"


def test_totals_reported():
    report = analyse_pptx(FIXTURE)
    assert report["totals"]["markers"] == 3
    assert report["totals"]["slides"] == 4
    assert report["totals"]["by_kind"] == {"IMAGE": 1, "SMARTART": 1, "BG": 1}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/pytest docs/spikes/2026-04-23-pptx-marker-adherence/tests/test_analyse_markers.py -v`
Expected: ImportError (`analyse_markers` not found) or collection error.

- [ ] **Step 3: Implement the analyser**

```python
"""Parse a .pptx, find shapes whose names match the marker protocol.

Marker grammar: (IMAGE|SMARTART|BG):<identifier>
where identifier is one or more of [A-Za-z0-9_-].
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pptx import Presentation

MARKER_RE = re.compile(r"^(IMAGE|SMARTART|BG):([A-Za-z0-9_-]+)$")


def analyse_pptx(path: str | Path) -> dict[str, Any]:
    prs = Presentation(str(path))
    markers: list[dict[str, Any]] = []
    for slide_idx, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            name = getattr(shape, "name", "") or ""
            m = MARKER_RE.match(name)
            if not m:
                continue
            markers.append(
                {
                    "slide_index": slide_idx,
                    "shape_name": name,
                    "kind": m.group(1),
                    "identifier": m.group(2),
                    "left_emu": shape.left or 0,
                    "top_emu": shape.top or 0,
                    "width_emu": shape.width or 0,
                    "height_emu": shape.height or 0,
                }
            )
    by_kind: dict[str, int] = {}
    for mk in markers:
        by_kind[mk["kind"]] = by_kind.get(mk["kind"], 0) + 1
    return {
        "source": str(path),
        "markers": markers,
        "totals": {
            "markers": len(markers),
            "slides": len(prs.slides),
            "by_kind": by_kind,
        },
    }


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 2:
        print("usage: analyse_markers.py <path.pptx>", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(analyse_pptx(sys.argv[1]), indent=2))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest docs/spikes/2026-04-23-pptx-marker-adherence/tests/test_analyse_markers.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add docs/spikes/2026-04-23-pptx-marker-adherence/tools/analyse_markers.py \
        docs/spikes/2026-04-23-pptx-marker-adherence/tests/test_analyse_markers.py
git commit -m "spike: add marker analyser with tests"
```

---

## Task 4: Write the adherence scorer

Given an analyser report and a "requested markers" manifest (what the brief asked for), compute adherence = emitted / requested plus qualitative buckets.

**Files:**
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/tools/score_adherence.py`
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/tests/test_score_adherence.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for the adherence scorer."""
import sys
from pathlib import Path

SPIKE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE_DIR / "tools"))

from score_adherence import score


def test_full_adherence_when_all_kinds_emitted():
    requested = {"IMAGE": 2, "SMARTART": 1, "BG": 1}
    emitted = {"IMAGE": 2, "SMARTART": 1, "BG": 1}
    result = score(requested, emitted)
    assert result["overall_rate"] == 1.0
    assert result["verdict"] == "full"


def test_partial_adherence():
    requested = {"IMAGE": 2, "SMARTART": 1, "BG": 1}
    emitted = {"IMAGE": 1, "SMARTART": 0, "BG": 1}
    result = score(requested, emitted)
    assert 0 < result["overall_rate"] < 1
    assert result["verdict"] == "partial"
    assert result["missing"] == {"IMAGE": 1, "SMARTART": 1}


def test_zero_adherence():
    requested = {"IMAGE": 2, "SMARTART": 1, "BG": 1}
    emitted = {"IMAGE": 0, "SMARTART": 0, "BG": 0}
    result = score(requested, emitted)
    assert result["overall_rate"] == 0.0
    assert result["verdict"] == "none"


def test_over_emission_capped_at_requested():
    # /pptx emits more markers than asked — count only up to requested
    requested = {"IMAGE": 1}
    emitted = {"IMAGE": 3}
    result = score(requested, emitted)
    assert result["overall_rate"] == 1.0
    assert result["extra"] == {"IMAGE": 2}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/pytest docs/spikes/2026-04-23-pptx-marker-adherence/tests/test_score_adherence.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement the scorer**

```python
"""Score marker adherence: emitted vs. requested by kind."""
from __future__ import annotations

from typing import Any


def score(requested: dict[str, int], emitted: dict[str, int]) -> dict[str, Any]:
    total_requested = sum(requested.values())
    total_counted = 0
    missing: dict[str, int] = {}
    extra: dict[str, int] = {}
    for kind, want in requested.items():
        have = emitted.get(kind, 0)
        counted = min(have, want)
        total_counted += counted
        if have < want:
            missing[kind] = want - have
        elif have > want:
            extra[kind] = have - want
    rate = (total_counted / total_requested) if total_requested else 0.0
    if rate >= 0.95:
        verdict = "full"
    elif rate > 0:
        verdict = "partial"
    else:
        verdict = "none"
    return {
        "requested": requested,
        "emitted": emitted,
        "overall_rate": rate,
        "verdict": verdict,
        "missing": missing,
        "extra": extra,
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest docs/spikes/2026-04-23-pptx-marker-adherence/tests/test_score_adherence.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add docs/spikes/2026-04-23-pptx-marker-adherence/tools/score_adherence.py \
        docs/spikes/2026-04-23-pptx-marker-adherence/tests/test_score_adherence.py
git commit -m "spike: add adherence scorer with tests"
```

---

## Task 5: Draft Variant A brief — minimal instruction

Variant A is the control: tell /pptx to build a deck and mention markers once in passing. Measures baseline willingness.

**Files:**
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/briefs/brief-a-minimal.md`

- [ ] **Step 1: Write the brief**

```markdown
# Brief A — Minimal marker instruction

Build a 10-slide conference talk titled "AI Agents That Actually Work" for a developer audience, 20 minutes long. Cover: why most AI agent demos fail in production, the three architectural pillars (planning, memory, tool use), a concrete case study, and a call to action.

Where a slide would benefit from a full illustration, leave a placeholder shape named starting with `IMAGE:`. Where a slide shows a process or relationship, leave a placeholder shape named starting with `SMARTART:`. Where a slide should have an atmospheric background, leave a placeholder shape named starting with `BG:`.

## Requested markers (for scoring)

- `IMAGE:*` — at least 2
- `SMARTART:*` — at least 1
- `BG:*` — at least 1
```

- [ ] **Step 2: Commit**

```bash
git add docs/spikes/2026-04-23-pptx-marker-adherence/briefs/brief-a-minimal.md
git commit -m "spike: add variant A brief (minimal)"
```

---

## Task 6: Draft Variant B brief — explicit marker protocol

Variant B spells out the protocol with a table, exact naming rules, and shape appearance.

**Files:**
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/briefs/brief-b-explicit.md`

- [ ] **Step 1: Write the brief**

```markdown
# Brief B — Explicit marker protocol

Build a 10-slide conference talk titled "AI Agents That Actually Work" for a developer audience, 20 minutes long. Cover: why most AI agent demos fail in production, the three architectural pillars (planning, memory, tool use), a concrete case study, and a call to action.

## Placeholder protocol (MUST follow exactly)

Some slides need visual enrichment that will be added by a downstream tool. When you build those slides, do not try to generate the visual yourself — instead, leave a **placeholder shape** that the downstream tool will find by name.

The placeholder is a rectangle with:
- Fill: light grey `F0F0F0`
- Border: 1pt dashed `CCCCCC`
- Visible text inside the rectangle equal to the shape's name

Use the PptxGenJS `name` property on the shape so the downstream tool can find it. Naming rules:

| Marker prefix | When to use | Example shape name |
|---------------|-------------|--------------------|
| `IMAGE:`      | Slide needs an AI-generated illustration (e.g. hero image, architecture sketch, conceptual art) | `IMAGE:agent-architecture`, `IMAGE:pillar-planning` |
| `SMARTART:`   | Slide content is a process, cycle, hierarchy, list, or relationship that should become an editable SmartArt diagram | `SMARTART:flowchart`, `SMARTART:cycle`, `SMARTART:pyramid` |
| `BG:`         | Slide would benefit from an atmospheric AI background behind its text. Place a small label shape (~1.5 in × 0.3 in) in the bottom-left corner named `BG:<mood>` | `BG:dramatic-contrast`, `BG:calm-minimal` |

Identifier after the colon: lowercase letters, digits, hyphens, underscores only. Be descriptive — it hints at the visual intent.

## Requested markers (for scoring)

- `IMAGE:*` — at least 2 (e.g. one hero illustration, one architecture sketch)
- `SMARTART:*` — at least 1 (e.g. the three pillars, or the case-study timeline)
- `BG:*` — at least 1 (e.g. the opening or closing slide)
```

- [ ] **Step 2: Commit**

```bash
git add docs/spikes/2026-04-23-pptx-marker-adherence/briefs/brief-b-explicit.md
git commit -m "spike: add variant B brief (explicit protocol)"
```

---

## Task 7: Draft Variant C brief — protocol + worked example

Variant C gives the protocol plus a fully-worked example slide demonstrating the shape placement so /pptx has a concrete pattern to mimic.

**Files:**
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/briefs/brief-c-exemplar.md`

- [ ] **Step 1: Write the brief**

```markdown
# Brief C — Protocol + worked example

Build a 10-slide conference talk titled "AI Agents That Actually Work" for a developer audience, 20 minutes long. Cover: why most AI agent demos fail in production, the three architectural pillars (planning, memory, tool use), a concrete case study, and a call to action.

## Placeholder protocol (MUST follow exactly)

Some slides need visual enrichment that will be added by a downstream tool. When you build those slides, do not try to generate the visual yourself — instead, leave a **placeholder shape** that the downstream tool will find by name.

| Marker prefix | When to use | Example shape name |
|---------------|-------------|--------------------|
| `IMAGE:`      | AI illustration | `IMAGE:agent-architecture` |
| `SMARTART:`   | Process / cycle / hierarchy / relationship | `SMARTART:flowchart` |
| `BG:`         | Atmospheric AI background (place a small corner label shape) | `BG:dramatic-contrast` |

### Worked example — what a slide with an IMAGE marker should look like in your build script

```javascript
// Slide 3: "Why most agents fail"
const slide3 = pres.addSlide();
slide3.addText("Why most agents fail", { x: 0.5, y: 0.3, w: 9, h: 0.8, fontSize: 32, bold: true });
slide3.addText([
  { text: "Prompt engineering hits a ceiling", options: { bullet: true } },
  { text: "No persistent memory", options: { bullet: true } },
  { text: "Tool use is brittle", options: { bullet: true } },
], { x: 0.5, y: 1.5, w: 4.5, h: 3, fontSize: 20 });

// IMAGE placeholder on the right 40% of the slide
slide3.addShape(pres.ShapeType.rect, {
  x: 5.5, y: 1.5, w: 4, h: 3,
  fill: { color: "F0F0F0" },
  line: { color: "CCCCCC", width: 1, dashType: "dash" },
  name: "IMAGE:agents-failing",        // <-- shape name matters
});
slide3.addText("IMAGE:agents-failing", { x: 5.5, y: 2.8, w: 4, h: 0.5, align: "center", color: "888888", fontSize: 14 });
```

### Worked example — BG corner label

```javascript
// Slide 1: title — wants a dramatic background
const slide1 = pres.addSlide();
slide1.addText("AI Agents That Actually Work", { x: 0.5, y: 2.5, w: 9, h: 1.5, fontSize: 48, bold: true });

// Small corner label — the BG marker
slide1.addShape(pres.ShapeType.rect, {
  x: 0.2, y: 6.8, w: 1.8, h: 0.3,
  fill: { color: "F0F0F0" },
  line: { color: "CCCCCC", width: 1, dashType: "dash" },
  name: "BG:dramatic-opening",
});
slide1.addText("BG:dramatic-opening", { x: 0.2, y: 6.8, w: 1.8, h: 0.3, align: "center", color: "888888", fontSize: 10 });
```

Follow this pattern for every slide that needs a marker.

## Requested markers (for scoring)

- `IMAGE:*` — at least 2
- `SMARTART:*` — at least 1
- `BG:*` — at least 1
```

- [ ] **Step 2: Commit**

```bash
git add docs/spikes/2026-04-23-pptx-marker-adherence/briefs/brief-c-exemplar.md
git commit -m "spike: add variant C brief (protocol + worked example)"
```

---

## Task 8: Run Variant A through /pptx and capture output

Invoke the `document-skills:pptx` skill with Brief A as the prompt. This is a single-shot run — no iteration. Capture the .pptx and (if emitted) the build script.

**Files:**
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-a/presentation.pptx`
- Create (if skill emits it): `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-a/build.js`
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-a/run-notes.md`

- [ ] **Step 1: Invoke /pptx with Brief A**

Invoke the `document-skills:pptx` skill with the following prompt:

> Read the brief at `docs/spikes/2026-04-23-pptx-marker-adherence/briefs/brief-a-minimal.md` and build the deck it describes. Save the .pptx to `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-a/presentation.pptx`. If your workflow produces an intermediate build script, save it alongside as `build.js`.

Use the Skill tool, passing `document-skills:pptx` as the skill name.

- [ ] **Step 2: Capture run notes**

Write `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-a/run-notes.md` with:
- Timestamp
- Skill invocation used
- Any prompts or iteration the skill ran
- Whether a build script was emitted (yes/no + path)
- Observable behaviour — did the model acknowledge the marker instructions? Did it object?
- File sizes

Example content:

```markdown
# Variant A — Run notes

**Timestamp:** 2026-04-23 14:22
**Skill:** document-skills:pptx
**Build script emitted:** yes / no
**Build script path:** outputs/variant-a/build.js
**Deck size:** 47 KB
**Slides produced:** 10

**Observable behaviour:**

<Describe what the skill did — did it read the brief, did it mention markers, did it ask clarifying questions?>
```

- [ ] **Step 3: Commit outputs**

```bash
git add docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-a/
git commit -m "spike: capture variant A output from /pptx"
```

---

## Task 9: Analyse Variant A output

**Files:**
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/results/variant-a-report.json`

- [ ] **Step 1: Run the analyser**

Run:
```bash
.venv/bin/python docs/spikes/2026-04-23-pptx-marker-adherence/tools/analyse_markers.py \
  docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-a/presentation.pptx \
  > docs/spikes/2026-04-23-pptx-marker-adherence/results/variant-a-analysis.json
```

Expected: a JSON report with a `markers` array (possibly empty) and `totals`.

- [ ] **Step 2: Compute adherence score**

Write a small inline script — do not save it — that loads the analysis JSON, constructs the requested dict from the brief (`{"IMAGE": 2, "SMARTART": 1, "BG": 1}`), calls `score()`, and writes the result to `variant-a-report.json`:

```bash
.venv/bin/python - <<'PY'
import json
import sys
from pathlib import Path

sys.path.insert(0, "docs/spikes/2026-04-23-pptx-marker-adherence/tools")
from score_adherence import score

analysis = json.loads(Path("docs/spikes/2026-04-23-pptx-marker-adherence/results/variant-a-analysis.json").read_text())
requested = {"IMAGE": 2, "SMARTART": 1, "BG": 1}
emitted = analysis["totals"].get("by_kind", {})
report = {
    "variant": "A",
    "brief": "brief-a-minimal.md",
    "analysis": analysis,
    "adherence": score(requested, emitted),
}
Path("docs/spikes/2026-04-23-pptx-marker-adherence/results/variant-a-report.json").write_text(json.dumps(report, indent=2))
print(report["adherence"])
PY
```

Expected output: a printed dict like `{'requested': {...}, 'emitted': {...}, 'overall_rate': 0.0, 'verdict': 'none', ...}` (value depends on what /pptx actually did).

- [ ] **Step 3: Commit**

```bash
git add docs/spikes/2026-04-23-pptx-marker-adherence/results/variant-a-*
git commit -m "spike: analyse variant A — adherence report"
```

---

## Task 10: Run and analyse Variant B

Repeat Tasks 8 and 9 with Brief B.

- [ ] **Step 1: Invoke /pptx with Brief B**

Invoke the `document-skills:pptx` skill with this prompt:

> Read the brief at `docs/spikes/2026-04-23-pptx-marker-adherence/briefs/brief-b-explicit.md` and build the deck it describes. Save the .pptx to `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-b/presentation.pptx`. If your workflow produces an intermediate build script, save it alongside as `build.js`.

- [ ] **Step 2: Write run notes**

Write `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-b/run-notes.md` (same template as Variant A).

- [ ] **Step 3: Run analyser**

```bash
.venv/bin/python docs/spikes/2026-04-23-pptx-marker-adherence/tools/analyse_markers.py \
  docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-b/presentation.pptx \
  > docs/spikes/2026-04-23-pptx-marker-adherence/results/variant-b-analysis.json
```

- [ ] **Step 4: Compute adherence**

```bash
.venv/bin/python - <<'PY'
import json
import sys
from pathlib import Path

sys.path.insert(0, "docs/spikes/2026-04-23-pptx-marker-adherence/tools")
from score_adherence import score

analysis = json.loads(Path("docs/spikes/2026-04-23-pptx-marker-adherence/results/variant-b-analysis.json").read_text())
requested = {"IMAGE": 2, "SMARTART": 1, "BG": 1}
emitted = analysis["totals"].get("by_kind", {})
report = {
    "variant": "B",
    "brief": "brief-b-explicit.md",
    "analysis": analysis,
    "adherence": score(requested, emitted),
}
Path("docs/spikes/2026-04-23-pptx-marker-adherence/results/variant-b-report.json").write_text(json.dumps(report, indent=2))
print(report["adherence"])
PY
```

- [ ] **Step 5: Commit**

```bash
git add docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-b/ \
        docs/spikes/2026-04-23-pptx-marker-adherence/results/variant-b-*
git commit -m "spike: capture and analyse variant B"
```

---

## Task 11: Run and analyse Variant C

Repeat for Brief C.

- [ ] **Step 1: Invoke /pptx with Brief C**

Invoke the `document-skills:pptx` skill with this prompt:

> Read the brief at `docs/spikes/2026-04-23-pptx-marker-adherence/briefs/brief-c-exemplar.md` and build the deck it describes. Follow the worked examples in the brief exactly when emitting placeholder shapes. Save the .pptx to `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-c/presentation.pptx`. Save the build script alongside as `build.js`.

- [ ] **Step 2: Write run notes**

Write `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-c/run-notes.md`.

- [ ] **Step 3: Run analyser**

```bash
.venv/bin/python docs/spikes/2026-04-23-pptx-marker-adherence/tools/analyse_markers.py \
  docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-c/presentation.pptx \
  > docs/spikes/2026-04-23-pptx-marker-adherence/results/variant-c-analysis.json
```

- [ ] **Step 4: Compute adherence**

```bash
.venv/bin/python - <<'PY'
import json
import sys
from pathlib import Path

sys.path.insert(0, "docs/spikes/2026-04-23-pptx-marker-adherence/tools")
from score_adherence import score

analysis = json.loads(Path("docs/spikes/2026-04-23-pptx-marker-adherence/results/variant-c-analysis.json").read_text())
requested = {"IMAGE": 2, "SMARTART": 1, "BG": 1}
emitted = analysis["totals"].get("by_kind", {})
report = {
    "variant": "C",
    "brief": "brief-c-exemplar.md",
    "analysis": analysis,
    "adherence": score(requested, emitted),
}
Path("docs/spikes/2026-04-23-pptx-marker-adherence/results/variant-c-report.json").write_text(json.dumps(report, indent=2))
print(report["adherence"])
PY
```

- [ ] **Step 5: Commit**

```bash
git add docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-c/ \
        docs/spikes/2026-04-23-pptx-marker-adherence/results/variant-c-*
git commit -m "spike: capture and analyse variant C"
```

---

## Task 12: Visual review of every output deck

Constitution Article 9.4 — every visual output is reviewed before conclusions are drawn. Also, the numeric adherence score is only half the story; slide quality and marker positioning matter.

**Files:**
- Modify: `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-a/run-notes.md`
- Modify: `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-b/run-notes.md`
- Modify: `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-c/run-notes.md`

- [ ] **Step 1: Rasterise each deck to PNGs**

Run:
```bash
for v in a b c; do
  dir=docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-$v
  tools/pptx_to_pdf.sh "$dir/presentation.pptx" "$dir/presentation.pdf"
  mkdir -p "$dir/slides"
  pdftoppm -r 96 "$dir/presentation.pdf" "$dir/slides/slide" -png
done
```

Expected: `slides/slide-1.png`, `slides/slide-2.png`, ... in each variant dir. Check that each directory contains at least 10 PNGs (one per slide).

- [ ] **Step 2: Open every slide PNG with the Read tool and observe**

For each variant, use the Read tool on every `slide-N.png` and note in the run-notes:
- Are marker placeholders visibly present (grey rectangles with marker-name text)?
- Do the marker positions make sense given slide content?
- Are slide contents coherent with the requested topic?
- Anything surprising — e.g. /pptx tried to draw the actual illustration instead of leaving a placeholder?

Append a "Visual review" section to each variant's `run-notes.md`:

```markdown
## Visual review

- Slide 1: <what you observed>
- Slide 2: <what you observed>
...
```

- [ ] **Step 3: Commit**

```bash
git add docs/spikes/2026-04-23-pptx-marker-adherence/outputs/
git commit -m "spike: visual review of all variant decks"
```

---

## Task 13: Build summary report

**Files:**
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/results/summary.json`

- [ ] **Step 1: Aggregate all three variants**

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path

results_dir = Path("docs/spikes/2026-04-23-pptx-marker-adherence/results")
summary = {"variants": []}
for variant in ("a", "b", "c"):
    report = json.loads((results_dir / f"variant-{variant}-report.json").read_text())
    summary["variants"].append(
        {
            "variant": variant.upper(),
            "brief": report["brief"],
            "requested": report["adherence"]["requested"],
            "emitted": report["adherence"]["emitted"],
            "overall_rate": report["adherence"]["overall_rate"],
            "verdict": report["adherence"]["verdict"],
            "missing": report["adherence"]["missing"],
            "extra": report["adherence"]["extra"],
            "marker_count": report["analysis"]["totals"]["markers"],
            "slide_count": report["analysis"]["totals"]["slides"],
        }
    )
(results_dir / "summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
PY
```

- [ ] **Step 2: Commit**

```bash
git add docs/spikes/2026-04-23-pptx-marker-adherence/results/summary.json
git commit -m "spike: aggregate adherence summary across all variants"
```

---

## Task 14: Write findings README and decision gate

**Files:**
- Create: `docs/spikes/2026-04-23-pptx-marker-adherence/README.md`

- [ ] **Step 1: Write the findings report**

Use this template — replace every `<...>` with observed fact:

```markdown
# Spike: /pptx marker adherence — Findings

**Date:** 2026-04-23
**Related:** [docs/superpowers/specs/2026-04-22-superpower-bridge-design.md](../../superpowers/specs/2026-04-22-superpower-bridge-design.md), GitHub issue #53

## Question

Will the `/pptx` superpower reliably emit named placeholder shapes (`IMAGE:*`, `SMARTART:*`, `BG:*`) when instructed via a creative brief, and at what level of instruction specificity?

## Procedure

Three variant briefs were fed to `document-skills:pptx`:

- **A:** Minimal — markers mentioned once in passing
- **B:** Explicit — full protocol table, naming rules, shape appearance
- **C:** Exemplar — protocol plus a worked PptxGenJS code example

Each output was parsed with the analyser in `tools/analyse_markers.py` and scored against the requested marker counts (2× IMAGE, 1× SMARTART, 1× BG).

## Results

| Variant | Emitted IMAGE | Emitted SMARTART | Emitted BG | Overall rate | Verdict |
|---------|---------------|------------------|------------|--------------|---------|
| A       | <n>           | <n>              | <n>        | <%>          | <verdict> |
| B       | <n>           | <n>              | <n>        | <%>          | <verdict> |
| C       | <n>           | <n>              | <n>        | <%>          | <verdict> |

### Qualitative observations

- <Did /pptx understand the marker concept?>
- <Did it use PptxGenJS shape `name` property, or something else?>
- <Were identifiers lowercase / hyphenated as requested, or did it invent its own format?>
- <Did it place markers sensibly (right 40% for IMAGE, corner for BG), or randomly?>
- <Did it sometimes try to draw the real visual instead of leaving a placeholder?>
- <Were there any marker grammar deviations — e.g. `Image:` vs `IMAGE:`, or spaces in identifiers?>

### Variant-specific notes

**Variant A:** <one paragraph>

**Variant B:** <one paragraph>

**Variant C:** <one paragraph>

## Decision

Choose ONE:

- [ ] **GO as designed** — Variant B (explicit protocol) hits ≥95% adherence. Bridge Phase 1 brief template uses Variant B structure. Proceed with the spec as-written.

- [ ] **GO with adjusted protocol** — Adherence was partial but salvageable. Specific adjustments required:
  - <list the marker grammar changes that match what /pptx actually produces>
  - <list any fall-through logic needed in the analyser for observed deviations>
  - Spec update ticket: <link>

- [ ] **PIVOT** — /pptx will not reliably emit structured markers even with exemplar briefs. The Phase 1 pre-brief remains valuable for narrative architecture but the placeholder protocol must be dropped. The enrichment Phase 3 analyser must rely entirely on content-based slide classification (text-heavy, list/process, etc.). Redesign required.

- [ ] **NO-GO** — /pptx output is so variable that neither markers nor content classification would produce a usable enrichment menu. The bridge concept needs rethinking before any further work.

## Recommended next steps

<Concrete actions — e.g. "Update the superpower-bridge-design spec's Phase 1 section to use the Variant B brief template verbatim" or "File new issue to explore content-based classification as primary mechanism">
```

- [ ] **Step 2: Confirm decision with user**

Do not commit the findings until the user has reviewed the report and agreed with the chosen decision. Present the completed README and ask: "I've picked `<decision>`. Do you agree, or should we revise?"

- [ ] **Step 3: Commit**

```bash
git add docs/spikes/2026-04-23-pptx-marker-adherence/README.md
git commit -m "spike: findings and decision gate for /pptx marker adherence"
```

- [ ] **Step 4: Close out**

If the spike produced actionable changes to the superpower-bridge spec, open a follow-up issue on GitHub. If the decision is NO-GO, update the spec with a `Status: Blocked by spike` banner at the top.

---

## Self-review checklist (done after writing the plan — do not remove)

- [x] Every task has exact file paths
- [x] Every code step has full code — no placeholders
- [x] Every command has expected output stated
- [x] Visual review step present (Article 9.4)
- [x] Decision gate at end
- [x] No step forward-references undefined functions
- [x] Spec requirements covered: marker emission measurement (Tasks 8–12), adherence scoring (Task 4), qualitative observations (Task 12), decision record (Task 14)
