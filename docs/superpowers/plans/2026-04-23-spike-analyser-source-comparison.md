# Spike 3: Analyser Source Comparison — JS Build Script vs .pptx OOXML

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (recommended) or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Empirically determine whether the Superpower Bridge analyser (Section 3.1 of the spec) should parse the /pptx build script, the .pptx OOXML, or both — by building both analysers against the same inputs and comparing what each actually extracts.

**Architecture:** Two parallel parsers (one JS/text, one OOXML/python-pptx) are built to extract the same field set. A comparison harness runs both against Spike 1's three variant outputs plus one non-PptxGenJS control. A scoring matrix drives the decision.

**Tech Stack:** Python 3.14, python-pptx 1.0.2, esprima/acorn-style JS parsing (preferring a pure-Python AST parser over regex), pytest. No LLM calls; this is deterministic parser work.

**Why this exists:** The team review's most-debated theme was the analyser's input source. Spec says "build script is richer"; reviewers say "OOXML is stable and secure; JS is LLM-variable." Neither Spike 1 nor Spike 2 measured the claim — both used OOXML only. This spike closes that empirical gap with ~2 hours of work so the spec edit isn't guesswork.

---

## Scope

Build parsers that extract the fields Section 3.1 of the bridge spec says the analyser needs:

- F1: Per-slide text content (all body text)
- F2: Marker shape names matching `(IMAGE|SMARTART|BG):[A-Za-z0-9_-]+`
- F3: Marker shape geometry (left, top, width, height in EMU)
- F4: Slide background state (solid colour / image / default)
- F5: Non-marker element types present (chart, table, image, shape, text frame)
- F6: Slide count
- F7: Derived classification — "text-heavy", "list/process", "already-rich"

Out of scope for this spike: actually running the enrichment. This is only about information availability.

## Inputs

Three real PptxGenJS outputs from Spike 1 (each has both `presentation.pptx` and `build.js`):

- `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-a/` — markers in OOXML (objectName)
- `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-b/` — markers absent from OOXML (name dropped)
- `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-c/` — markers absent from OOXML (name dropped)

Plus one synthetic control:

- A minimal non-PptxGenJS .pptx (e.g. python-pptx hand-built) — used to test what happens when no `build.js` is available at all, which is the likely case if a user runs the bridge on a corporate template or a deck produced by a different tool.

## File Structure

```
docs/spikes/2026-04-23-analyser-source-comparison/
  parsers/
    js_parser.py           # Parse build.js → SlideFacts list
    pptx_parser.py         # Parse .pptx → SlideFacts list
    slide_facts.py         # SlideFacts dataclass + helpers (DRY — both parsers emit this type)
    classifier.py          # Classify a SlideFacts list → "text-heavy" / "list" / "already-rich"
  harness/
    compare.py             # Run both parsers on a case, emit comparison matrix
  tests/
    test_js_parser.py
    test_pptx_parser.py
    test_classifier.py
    test_compare.py
  fixtures/
    build_control.py       # Construct the non-PptxGenJS control .pptx
  results/
    matrix-variant-a.json
    matrix-variant-b.json
    matrix-variant-c.json
    matrix-control.json
    summary.json
  README.md                # Findings + decision gate
```

`SlideFacts` is the shared contract between both parsers — each slide produces one `SlideFacts` record, and the harness compares field-by-field. This keeps the comparison apples-to-apples.

---

## Task 1: Scaffold spike directory

**Files:**
- Create: `docs/spikes/2026-04-23-analyser-source-comparison/{parsers,harness,tests,fixtures,results}/`

- [ ] **Step 1: Create tree**

```bash
mkdir -p docs/spikes/2026-04-23-analyser-source-comparison/{parsers,harness,tests,fixtures,results}
touch docs/spikes/2026-04-23-analyser-source-comparison/{parsers,harness,tests,fixtures,results}/.gitkeep
```

- [ ] **Step 2: Commit scaffold**

```bash
git add docs/spikes/2026-04-23-analyser-source-comparison && git commit -m "spike: scaffold analyser source comparison directory"
```

---

## Task 2: Define SlideFacts contract

**Files:**
- Create: `docs/spikes/2026-04-23-analyser-source-comparison/parsers/slide_facts.py`
- Test: `docs/spikes/2026-04-23-analyser-source-comparison/tests/test_slide_facts.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_slide_facts.py
import sys
from pathlib import Path
SPIKE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE / "parsers"))

from slide_facts import SlideFacts, Marker

def test_slide_facts_roundtrip_dict():
    sf = SlideFacts(
        slide_index=1,
        text_content="Hello world",
        markers=[Marker(kind="IMAGE", identifier="hero", left_emu=0, top_emu=0, width_emu=914400, height_emu=914400)],
        background_kind="solid",
        element_types={"text": 2, "shape": 1},
    )
    as_dict = sf.to_dict()
    back = SlideFacts.from_dict(as_dict)
    assert back == sf

def test_marker_validates_kind():
    import pytest
    with pytest.raises(ValueError):
        Marker(kind="BOGUS", identifier="x", left_emu=0, top_emu=0, width_emu=1, height_emu=1)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest docs/spikes/2026-04-23-analyser-source-comparison/tests/test_slide_facts.py -v
# Expected: ModuleNotFoundError: slide_facts
```

- [ ] **Step 3: Implement SlideFacts**

```python
# parsers/slide_facts.py
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Literal

MarkerKind = Literal["IMAGE", "SMARTART", "BG"]
VALID_KINDS = {"IMAGE", "SMARTART", "BG"}


@dataclass
class Marker:
    kind: str
    identifier: str
    left_emu: int
    top_emu: int
    width_emu: int
    height_emu: int

    def __post_init__(self) -> None:
        if self.kind not in VALID_KINDS:
            raise ValueError(f"invalid kind {self.kind!r}; want one of {VALID_KINDS}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SlideFacts:
    slide_index: int          # 1-based
    text_content: str         # concatenated text on the slide
    markers: list[Marker] = field(default_factory=list)
    background_kind: str = "default"   # "default" | "solid" | "image" | "unknown"
    element_types: dict[str, int] = field(default_factory=dict)  # {"text": n, "shape": n, "image": n, "chart": n, "table": n}

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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest docs/spikes/2026-04-23-analyser-source-comparison/tests/test_slide_facts.py -v
# Expected: 2 passed
```

- [ ] **Step 5: Commit**

```bash
git add docs/spikes/2026-04-23-analyser-source-comparison/parsers/slide_facts.py \
        docs/spikes/2026-04-23-analyser-source-comparison/tests/test_slide_facts.py
git commit -m "spike: SlideFacts shared contract with tests"
```

---

## Task 3: Implement the .pptx (OOXML) parser

**Files:**
- Create: `docs/spikes/2026-04-23-analyser-source-comparison/parsers/pptx_parser.py`
- Test: `docs/spikes/2026-04-23-analyser-source-comparison/tests/test_pptx_parser.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_pptx_parser.py
import sys
from pathlib import Path
SPIKE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE / "parsers"))

from pptx_parser import parse_pptx
from slide_facts import SlideFacts

VARIANT_A = (Path(__file__).resolve().parents[2]
             / "2026-04-23-pptx-marker-adherence/outputs/variant-a/presentation.pptx")


def test_parses_all_slides():
    facts = parse_pptx(VARIANT_A)
    assert len(facts) == 10
    assert all(isinstance(f, SlideFacts) for f in facts)


def test_finds_objectname_markers_in_variant_a():
    facts = parse_pptx(VARIANT_A)
    all_markers = [m for f in facts for m in f.markers]
    kinds = sorted(m.kind for m in all_markers)
    assert kinds.count("IMAGE") >= 2
    assert kinds.count("SMARTART") >= 1
    assert kinds.count("BG") >= 1


def test_records_text_content_per_slide():
    facts = parse_pptx(VARIANT_A)
    # slide 1 is the title slide — should contain "AI Agents"
    assert "AI Agents" in facts[0].text_content


def test_counts_element_types():
    facts = parse_pptx(VARIANT_A)
    for f in facts:
        assert "text" in f.element_types
        assert f.element_types["text"] >= 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest docs/spikes/2026-04-23-analyser-source-comparison/tests/test_pptx_parser.py -v
# Expected: ModuleNotFoundError
```

- [ ] **Step 3: Implement parser**

```python
# parsers/pptx_parser.py
from __future__ import annotations
import re
from pathlib import Path
from typing import Union

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn

from slide_facts import Marker, SlideFacts

MARKER_RE = re.compile(r"^(IMAGE|SMARTART|BG):([A-Za-z0-9_-]+)$")


def _shape_element_type(shape) -> str:
    st = shape.shape_type
    if st == MSO_SHAPE_TYPE.PICTURE:
        return "image"
    if st == MSO_SHAPE_TYPE.CHART:
        return "chart"
    if st == MSO_SHAPE_TYPE.TABLE:
        return "table"
    # text frames and plain shapes get disambiguated
    if shape.has_text_frame and shape.text_frame.text.strip():
        return "text"
    return "shape"


def _background_kind(slide) -> str:
    cSld = slide.element.find(qn("p:cSld"))
    bg = cSld.find(qn("p:bg"))
    if bg is None:
        return "default"
    if bg.find(".//" + qn("a:blipFill")) is not None:
        return "image"
    if bg.find(".//" + qn("a:solidFill")) is not None:
        return "solid"
    return "unknown"


def parse_pptx(path: Union[str, Path]) -> list[SlideFacts]:
    prs = Presentation(str(path))
    results: list[SlideFacts] = []
    for idx, slide in enumerate(prs.slides, start=1):
        text_parts: list[str] = []
        markers: list[Marker] = []
        counts: dict[str, int] = {"text": 0, "shape": 0, "image": 0, "chart": 0, "table": 0}
        for shape in slide.shapes:
            name = getattr(shape, "name", "") or ""
            m = MARKER_RE.match(name)
            if m:
                markers.append(Marker(
                    kind=m.group(1),
                    identifier=m.group(2),
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
        facts = SlideFacts(
            slide_index=idx,
            text_content="\n".join(t for t in text_parts if t.strip()),
            markers=markers,
            background_kind=_background_kind(slide),
            element_types=counts,
        )
        results.append(facts)
    return results


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) != 2:
        print("usage: pptx_parser.py <path.pptx>", file=sys.stderr)
        sys.exit(2)
    facts = parse_pptx(sys.argv[1])
    print(json.dumps([f.to_dict() for f in facts], indent=2))
```

- [ ] **Step 4: Run test to verify it passes**

```bash
/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest docs/spikes/2026-04-23-analyser-source-comparison/tests/test_pptx_parser.py -v
# Expected: 4 passed
```

- [ ] **Step 5: Commit**

```bash
git add docs/spikes/2026-04-23-analyser-source-comparison/parsers/pptx_parser.py \
        docs/spikes/2026-04-23-analyser-source-comparison/tests/test_pptx_parser.py
git commit -m "spike: pptx (OOXML) parser producing SlideFacts"
```

---

## Task 4: Implement the JS build-script parser

**Files:**
- Create: `docs/spikes/2026-04-23-analyser-source-comparison/parsers/js_parser.py`
- Test: `docs/spikes/2026-04-23-analyser-source-comparison/tests/test_js_parser.py`

The JS parser should use a real parser, not pure regex, so we measure the best-case for the JS path. Python has `esprima` (pip installable; produces JS AST).

- [ ] **Step 1: Install esprima (if not already)**

```bash
/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pip install esprima
```

- [ ] **Step 2: Write the test**

```python
# tests/test_js_parser.py
import sys
from pathlib import Path
SPIKE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE / "parsers"))

from js_parser import parse_js
from slide_facts import SlideFacts

VARIANT_A_JS = (Path(__file__).resolve().parents[2]
                / "2026-04-23-pptx-marker-adherence/outputs/variant-a/build.js")


def test_parses_all_slides():
    facts = parse_js(VARIANT_A_JS)
    assert len(facts) == 10
    assert all(isinstance(f, SlideFacts) for f in facts)


def test_finds_objectname_markers_in_variant_a():
    facts = parse_js(VARIANT_A_JS)
    all_markers = [m for f in facts for m in f.markers]
    kinds = sorted(m.kind for m in all_markers)
    assert kinds.count("IMAGE") >= 2
    assert kinds.count("SMARTART") >= 1
    assert kinds.count("BG") >= 1


def test_variant_c_finds_no_objectname_markers_but_text_labels_present():
    # Variants B and C used `name:` (dropped by PptxGenJS) — but the JS literal
    # strings "IMAGE:..." / "SMARTART:..." / "BG:..." appear in addText calls.
    # This test documents that the JS parser CAN find marker intent via text scan
    # even when objectName is missing. Key question for the spike.
    VARIANT_C_JS = (Path(__file__).resolve().parents[2]
                    / "2026-04-23-pptx-marker-adherence/outputs/variant-c/build.js")
    facts = parse_js(VARIANT_C_JS)
    # addShape name missing but addText strings present
    all_text = "\n".join(f.text_content for f in facts)
    assert "IMAGE:" in all_text
    assert "SMARTART:" in all_text or "BG:" in all_text
```

- [ ] **Step 3: Run test to verify it fails**

```bash
/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest docs/spikes/2026-04-23-analyser-source-comparison/tests/test_js_parser.py -v
# Expected: ModuleNotFoundError
```

- [ ] **Step 4: Implement JS parser**

```python
# parsers/js_parser.py
"""Parse a PptxGenJS build.js → list[SlideFacts].

Strategy: use esprima to produce an AST, then walk it looking for:
  - calls to .addSlide() to establish slide order
  - calls to .addShape(...) with objectName matching the marker protocol
  - calls to .addText(...) for text content
  - background colour/image setters

We treat a build.js as a sequence of top-level statements where slide objects
are bound to variables (const s = pres.addSlide()) and subsequent s.addX()
calls attach content to that slide.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any, Union

import esprima

from slide_facts import Marker, SlideFacts

MARKER_RE = re.compile(r"^(IMAGE|SMARTART|BG):([A-Za-z0-9_-]+)$")

# Approximate EMU-per-inch for PptxGenJS coordinate conversion
EMU_PER_INCH = 914400


def _literal_value(node):
    if node is None:
        return None
    if node.type == "Literal":
        return node.value
    if node.type == "UnaryExpression" and node.operator == "-":
        return -_literal_value(node.argument)
    return None


def _extract_object_properties(obj_node) -> dict[str, Any]:
    """Flatten a JS ObjectExpression into a Python dict (best effort)."""
    out: dict[str, Any] = {}
    if obj_node is None or obj_node.type != "ObjectExpression":
        return out
    for prop in obj_node.properties:
        if prop.type != "Property":
            continue
        key = prop.key.name if prop.key.type == "Identifier" else prop.key.value
        val = _literal_value(prop.value)
        out[key] = val
    return out


def _inches_to_emu(v) -> int:
    if v is None:
        return 0
    try:
        return int(float(v) * EMU_PER_INCH)
    except (TypeError, ValueError):
        return 0


def parse_js(path: Union[str, Path]) -> list[SlideFacts]:
    source = Path(path).read_text()
    tree = esprima.parseScript(source, options={"tolerant": True})

    # Track slide objects by variable name → facts
    slides: dict[str, SlideFacts] = {}
    order: list[str] = []  # variable names in declaration order

    def _slide_facts_for(var_name: str) -> SlideFacts:
        if var_name not in slides:
            slides[var_name] = SlideFacts(slide_index=len(order) + 1, text_content="")
            order.append(var_name)
        return slides[var_name]

    def walk(nodes):
        for n in nodes:
            if n is None:
                continue
            # const X = pres.addSlide() or pres.addSlide(...)
            if n.type == "VariableDeclaration":
                for decl in n.declarations:
                    init = decl.init
                    if init and init.type == "CallExpression" and _is_add_slide(init):
                        _slide_facts_for(decl.id.name)
                continue

            # s.addShape(...) / s.addText(...) / s.background = ...
            if n.type == "ExpressionStatement":
                expr = n.expression
                if expr.type == "CallExpression":
                    _handle_call(expr)
                elif expr.type == "AssignmentExpression":
                    _handle_assignment(expr)

            # BlockStatement — descend
            if hasattr(n, "body") and isinstance(n.body, list):
                walk(n.body)

    def _is_add_slide(call) -> bool:
        callee = call.callee
        return (callee.type == "MemberExpression"
                and callee.property.type == "Identifier"
                and callee.property.name == "addSlide")

    def _handle_call(call):
        callee = call.callee
        if callee.type != "MemberExpression":
            return
        if callee.object.type != "Identifier":
            return
        var_name = callee.object.name
        method = callee.property.name
        if var_name not in slides:
            return
        facts = slides[var_name]

        if method == "addText":
            # first arg is text content (string or array); we take strings & join
            if not call.arguments:
                return
            arg0 = call.arguments[0]
            if arg0.type == "Literal" and isinstance(arg0.value, str):
                facts.text_content = (facts.text_content + "\n" + arg0.value).strip()
            elif arg0.type == "ArrayExpression":
                parts: list[str] = []
                for el in arg0.elements:
                    if el is None:
                        continue
                    if el.type == "Literal" and isinstance(el.value, str):
                        parts.append(el.value)
                    elif el.type == "ObjectExpression":
                        props = _extract_object_properties(el)
                        if isinstance(props.get("text"), str):
                            parts.append(props["text"])
                if parts:
                    facts.text_content = (facts.text_content + "\n" + "\n".join(parts)).strip()

        elif method == "addShape":
            # second arg is options object; look for objectName + geometry
            if len(call.arguments) < 2:
                return
            props = _extract_object_properties(call.arguments[1])
            object_name = props.get("objectName") or props.get("name")
            if isinstance(object_name, str):
                m = MARKER_RE.match(object_name)
                if m:
                    facts.markers.append(Marker(
                        kind=m.group(1),
                        identifier=m.group(2),
                        left_emu=_inches_to_emu(props.get("x")),
                        top_emu=_inches_to_emu(props.get("y")),
                        width_emu=_inches_to_emu(props.get("w")),
                        height_emu=_inches_to_emu(props.get("h")),
                    ))
                    return
            facts.element_types["shape"] = facts.element_types.get("shape", 0) + 1

        elif method == "addImage":
            facts.element_types["image"] = facts.element_types.get("image", 0) + 1
        elif method == "addChart":
            facts.element_types["chart"] = facts.element_types.get("chart", 0) + 1
        elif method == "addTable":
            facts.element_types["table"] = facts.element_types.get("table", 0) + 1

    def _handle_assignment(expr):
        # s.background = { color: "..." } or { path: "..." }
        lhs = expr.left
        if lhs.type != "MemberExpression":
            return
        if lhs.object.type != "Identifier":
            return
        var_name = lhs.object.name
        if var_name not in slides:
            return
        if lhs.property.type == "Identifier" and lhs.property.name == "background":
            props = _extract_object_properties(expr.right)
            if props.get("path") or props.get("data"):
                slides[var_name].background_kind = "image"
            elif props.get("color") or props.get("fill"):
                slides[var_name].background_kind = "solid"

    walk(tree.body)

    # Count text elements after walk (one bump per addText call seen via text_content length proxy)
    for facts in slides.values():
        if facts.text_content:
            facts.element_types["text"] = facts.element_types.get("text", 0) + facts.text_content.count("\n") + 1

    return [slides[v] for v in order]


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) != 2:
        print("usage: js_parser.py <path.js>", file=sys.stderr)
        sys.exit(2)
    facts = parse_js(sys.argv[1])
    print(json.dumps([f.to_dict() for f in facts], indent=2))
```

- [ ] **Step 5: Run test to verify it passes**

```bash
/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest docs/spikes/2026-04-23-analyser-source-comparison/tests/test_js_parser.py -v
# Expected: 3 passed
```

If a test fails, read the actual error carefully — the JS parser will need adjustment for the specific idioms Spike 1's variants used (e.g. helper functions like `addMarker(slide, name, {...})` rather than inline `slide.addShape(...)`). Task 4 Step 6 below handles that.

- [ ] **Step 6: Handle helper-function indirection**

Spike 1 Variant A uses `addMarker(slide, "IMAGE:hero", {...})` and Variants B/C use `addMarkerRect(slide, name, {...})`. A pure AST walk that only follows `slide.addShape(...)` will miss these. Extend the parser to:
- Recognise top-level function declarations whose names start with `add` or contain `Marker`/`Rect`.
- When such a function is called with a slide variable as first arg, descend into its body and apply the same rules.

If time-boxed, this is the only production-quality work in the spike. Keep the implementation in the same file; add a new test:

```python
def test_resolves_helper_function_marker_calls_in_variant_a():
    facts = parse_js(VARIANT_A_JS)
    marker_counts: dict[str, int] = {}
    for f in facts:
        for m in f.markers:
            marker_counts[m.kind] = marker_counts.get(m.kind, 0) + 1
    # Spike 1's analyser found 8 markers in Variant A via OOXML — JS parser
    # should find the same count (helper-indirection resolved).
    assert sum(marker_counts.values()) == 8
```

This test failing is the key empirical finding — if the JS parser cannot find the same 8 markers the OOXML parser found, that is a data point about robustness, not a blocker for the spike.

- [ ] **Step 7: Commit**

```bash
git add docs/spikes/2026-04-23-analyser-source-comparison/parsers/js_parser.py \
        docs/spikes/2026-04-23-analyser-source-comparison/tests/test_js_parser.py
git commit -m "spike: JS build-script parser via esprima AST"
```

---

## Task 5: Build a non-PptxGenJS control .pptx

**Files:**
- Create: `docs/spikes/2026-04-23-analyser-source-comparison/fixtures/build_control.py`

- [ ] **Step 1: Write the builder**

```python
# fixtures/build_control.py
"""Construct a non-PptxGenJS control .pptx using python-pptx directly.

Simulates a user handing the bridge a .pptx with NO accompanying build.js —
e.g. a deck exported from Keynote, a corporate template, or a deck the user
edited in PowerPoint. The JS parser cannot work here at all; the OOXML parser
must still return useful results.
"""
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

OUT = Path(__file__).resolve().parent / "control.pptx"

prs = Presentation()
blank = prs.slide_layouts[6]

# Slide 1: title-like slide, no markers
s = prs.slides.add_slide(blank)
tb = s.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(1))
tb.text_frame.text = "Corporate All-Hands Q2 Update"

# Slide 2: bullets only, unmarked — candidate for SmartArt suggestion
s = prs.slides.add_slide(blank)
tb = s.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(4))
tb.text_frame.text = "Strategic priorities:\n- Growth\n- Efficiency\n- Culture"

# Slide 3: deliberately named marker shape (as if a tech-savvy user pre-marked it)
s = prs.slides.add_slide(blank)
shp = s.shapes.add_shape(1, Inches(5), Inches(1), Inches(4), Inches(4))
shp.name = "IMAGE:vision-diagram"
shp.text_frame.text = "IMAGE:vision-diagram"

prs.save(OUT)
print(f"wrote {OUT}")
```

- [ ] **Step 2: Run the builder**

```bash
/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/python docs/spikes/2026-04-23-analyser-source-comparison/fixtures/build_control.py
```

Expected: `wrote .../control.pptx`

- [ ] **Step 3: Commit**

```bash
git add docs/spikes/2026-04-23-analyser-source-comparison/fixtures/ && \
git commit -m "spike: non-PptxGenJS control .pptx builder"
```

---

## Task 6: Implement the comparison harness

**Files:**
- Create: `docs/spikes/2026-04-23-analyser-source-comparison/harness/compare.py`
- Test: `docs/spikes/2026-04-23-analyser-source-comparison/tests/test_compare.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_compare.py
import sys
from pathlib import Path
SPIKE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE / "parsers"))
sys.path.insert(0, str(SPIKE / "harness"))

from compare import compare_case, CaseResult

VARIANT_A_DIR = (Path(__file__).resolve().parents[2]
                 / "2026-04-23-pptx-marker-adherence/outputs/variant-a")


def test_compare_returns_structured_result():
    result = compare_case(
        case_name="variant-a",
        pptx_path=VARIANT_A_DIR / "presentation.pptx",
        js_path=VARIANT_A_DIR / "build.js",
    )
    assert isinstance(result, CaseResult)
    assert result.case_name == "variant-a"
    assert result.pptx_slide_count == 10
    assert result.js_slide_count == 10


def test_handles_missing_js():
    # When js_path doesn't exist, harness should still return pptx-only result
    result = compare_case(
        case_name="no-js",
        pptx_path=VARIANT_A_DIR / "presentation.pptx",
        js_path=Path("/nonexistent/build.js"),
    )
    assert result.js_slide_count is None
    assert result.pptx_slide_count == 10
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement harness**

```python
# harness/compare.py
"""Run both parsers on a case and produce a structured comparison result."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional, Union

from pptx_parser import parse_pptx  # type: ignore
from js_parser import parse_js  # type: ignore


@dataclass
class FieldAgreement:
    field: str
    pptx_value: Any
    js_value: Any
    agree: bool


@dataclass
class SlideComparison:
    slide_index: int
    fields: list[FieldAgreement]


@dataclass
class CaseResult:
    case_name: str
    pptx_slide_count: Optional[int]
    js_slide_count: Optional[int]
    js_error: Optional[str]
    pptx_marker_total: int
    js_marker_total: Optional[int]
    slide_comparisons: list[SlideComparison]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_name": self.case_name,
            "pptx_slide_count": self.pptx_slide_count,
            "js_slide_count": self.js_slide_count,
            "js_error": self.js_error,
            "pptx_marker_total": self.pptx_marker_total,
            "js_marker_total": self.js_marker_total,
            "slide_comparisons": [
                {
                    "slide_index": sc.slide_index,
                    "fields": [asdict(f) for f in sc.fields],
                }
                for sc in self.slide_comparisons
            ],
        }


def _marker_set(facts):
    return sorted(f"{m.kind}:{m.identifier}" for m in facts.markers)


def compare_case(
    case_name: str,
    pptx_path: Union[str, Path],
    js_path: Union[str, Path],
) -> CaseResult:
    pptx_path = Path(pptx_path)
    js_path = Path(js_path)

    pptx_facts = parse_pptx(pptx_path) if pptx_path.exists() else []
    js_facts: list = []
    js_error: Optional[str] = None
    if js_path.exists():
        try:
            js_facts = parse_js(js_path)
        except Exception as exc:  # noqa: BLE001
            js_error = f"{type(exc).__name__}: {exc}"

    pptx_by_idx = {f.slide_index: f for f in pptx_facts}
    js_by_idx = {f.slide_index: f for f in js_facts}
    all_indices = sorted(set(pptx_by_idx) | set(js_by_idx))

    comparisons: list[SlideComparison] = []
    for idx in all_indices:
        p = pptx_by_idx.get(idx)
        j = js_by_idx.get(idx)
        fields: list[FieldAgreement] = []
        fields.append(FieldAgreement(
            field="markers",
            pptx_value=_marker_set(p) if p else None,
            js_value=_marker_set(j) if j else None,
            agree=(p is not None and j is not None and _marker_set(p) == _marker_set(j)),
        ))
        fields.append(FieldAgreement(
            field="background_kind",
            pptx_value=p.background_kind if p else None,
            js_value=j.background_kind if j else None,
            agree=(p is not None and j is not None and p.background_kind == j.background_kind),
        ))
        fields.append(FieldAgreement(
            field="text_content_len",
            pptx_value=len(p.text_content) if p else None,
            js_value=len(j.text_content) if j else None,
            agree=(p is not None and j is not None
                   and abs(len(p.text_content) - len(j.text_content)) <= 20),
        ))
        comparisons.append(SlideComparison(slide_index=idx, fields=fields))

    return CaseResult(
        case_name=case_name,
        pptx_slide_count=len(pptx_facts) if pptx_facts else None,
        js_slide_count=len(js_facts) if (js_facts or js_path.exists()) else None,
        js_error=js_error,
        pptx_marker_total=sum(len(f.markers) for f in pptx_facts),
        js_marker_total=sum(len(f.markers) for f in js_facts) if js_facts else (0 if js_path.exists() and not js_error else None),
        slide_comparisons=comparisons,
    )


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) != 4:
        print("usage: compare.py <case_name> <pptx> <js>", file=sys.stderr)
        sys.exit(2)
    r = compare_case(sys.argv[1], sys.argv[2], sys.argv[3])
    print(json.dumps(r.to_dict(), indent=2))
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add docs/spikes/2026-04-23-analyser-source-comparison/harness/ \
        docs/spikes/2026-04-23-analyser-source-comparison/tests/test_compare.py && \
git commit -m "spike: comparison harness producing per-case agreement matrix"
```

---

## Task 7: Run the comparison on all four cases

**Files:**
- Create: `docs/spikes/2026-04-23-analyser-source-comparison/results/matrix-variant-a.json`
- Create: `docs/spikes/2026-04-23-analyser-source-comparison/results/matrix-variant-b.json`
- Create: `docs/spikes/2026-04-23-analyser-source-comparison/results/matrix-variant-c.json`
- Create: `docs/spikes/2026-04-23-analyser-source-comparison/results/matrix-control.json`
- Create: `docs/spikes/2026-04-23-analyser-source-comparison/results/summary.json`

- [ ] **Step 1: Run harness on each case**

```bash
PY=/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/python
SPIKE=docs/spikes/2026-04-23-analyser-source-comparison
MARK=docs/spikes/2026-04-23-pptx-marker-adherence/outputs

for v in a b c; do
  $PY $SPIKE/harness/compare.py \
    variant-$v \
    $MARK/variant-$v/presentation.pptx \
    $MARK/variant-$v/build.js \
    > $SPIKE/results/matrix-variant-$v.json
done

$PY $SPIKE/harness/compare.py \
    control \
    $SPIKE/fixtures/control.pptx \
    /nonexistent/build.js \
    > $SPIKE/results/matrix-control.json
```

- [ ] **Step 2: Aggregate summary**

```python
# one-off aggregation — save as harness/aggregate.py or run inline
import json
from pathlib import Path

res = Path("docs/spikes/2026-04-23-analyser-source-comparison/results")
summary = {"cases": []}
for p in sorted(res.glob("matrix-*.json")):
    d = json.loads(p.read_text())
    per_field_agreement: dict[str, list[bool]] = {}
    for slide in d["slide_comparisons"]:
        for f in slide["fields"]:
            per_field_agreement.setdefault(f["field"], []).append(f["agree"])
    summary["cases"].append({
        "case": d["case_name"],
        "pptx_slides": d["pptx_slide_count"],
        "js_slides": d["js_slide_count"],
        "js_error": d.get("js_error"),
        "pptx_markers": d["pptx_marker_total"],
        "js_markers": d["js_marker_total"],
        "agreement_by_field": {
            k: {"agree": sum(v), "total": len(v), "rate": sum(v) / len(v) if v else 0}
            for k, v in per_field_agreement.items()
        },
    })
(res / "summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
```

Run via `.venv/bin/python` with the script saved as `harness/aggregate.py` or inline via `-c`.

- [ ] **Step 3: Commit**

```bash
git add docs/spikes/2026-04-23-analyser-source-comparison/results/ \
        docs/spikes/2026-04-23-analyser-source-comparison/harness/aggregate.py && \
git commit -m "spike: comparison matrix across 3 PptxGenJS variants + 1 non-PptxGenJS control"
```

---

## Task 8: Write findings README + decision gate

**Files:**
- Create: `docs/spikes/2026-04-23-analyser-source-comparison/README.md`

- [ ] **Step 1: Draft the findings doc**

Required sections:
1. **Question** — restated: for the analyser's Section 3.1 needs, does JS or OOXML win?
2. **Procedure** — four cases, both parsers, SlideFacts contract, agreement matrix.
3. **Results** — populated from `summary.json`. Per case: slide count match, marker match, background match, text-length agreement, JS parse errors.
4. **Field-by-field scoring** — a table with rows for each SlideFacts field and columns for OOXML and JS showing "works", "works with caveats", "breaks". Populate empirically, not by theory.
5. **Robustness observations** — note any case where JS parsing raised, helper-function resolution failed, or text extraction drifted more than 20 chars from OOXML.
6. **Richness observations** — does the JS parser expose any data OOXML doesn't (function names, comments, variable names)? Be honest — if it exposes stuff but the analyser doesn't need it, say so.
7. **Decision** — GO with OOXML primary / GO with JS primary / HYBRID (use both, specify which fields come from which) — PICK ONE based on the evidence.
8. **Spec update list** — concrete changes to the bridge spec that follow from the decision.

- [ ] **Step 2: Present findings to user and await decision**

Do not commit the README directly — offer the findings as a response, let the user confirm the decision, then commit with their agreement. This matches how Spikes 1 and 2 closed out.

- [ ] **Step 3: After user agrees, commit**

```bash
git add docs/spikes/2026-04-23-analyser-source-comparison/README.md && \
git commit -m "spike: findings and decision gate for analyser source comparison"
```

---

## Self-review

Coverage check:
- [x] JS parser (Task 4) — answers "what can JS give us"
- [x] OOXML parser (Task 3) — answers "what can OOXML give us"
- [x] SlideFacts contract (Task 2) — makes comparison apples-to-apples
- [x] Control case (Task 5) — answers "what if there is no build.js"
- [x] Three variants (Task 7) — answers "how does each perform on real /pptx output"
- [x] Field-by-field scoring (Task 8 step 1 §4) — answers the primary question
- [x] Decision gate (Task 8 step 1 §7) — surfaces the outcome for user sign-off

Placeholder scan: no TBDs, no "similar to Task N" references. Each step either has the code inline or a command with an expected outcome.

Type consistency: both parsers return `list[SlideFacts]`. Harness consumes `list[SlideFacts]`. Marker dataclass consistent.

Time box: ~2 hours if the JS parser's helper-function resolution behaves. If esprima struggles with a particular idiom, the spike's finding is "JS parsing is fragile against idiom X" — which IS the answer to the spike's question, not a blocker.
