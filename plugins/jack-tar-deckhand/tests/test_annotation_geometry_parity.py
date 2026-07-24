"""Cross-path parity tests for the shared annotation geometry helpers
(issue #142 v2, T4 — docs/superpowers/plans/2026-07-17-annotate-figure-v2.md
§4.6, §8.3, F13).

Both assembler paths (PptxGenJS in T6, python-pptx template in T5) must
place leader-line termini and label boxes IDENTICALLY, or a native
annotation overlay will look subtly different depending on which
assembler built the deck. The two geometry primitives are:

- ``segment_box_entry`` (Python, ``src.annotation_payload`` — a thin
  re-export of ``annotate_figure._segment_box_entry``) and its JS port
  ``segmentBoxEntry`` (``src/assembler/annotation_geometry.js``).
- ``estimate_label_box`` (Python) and its JS port ``estimateLabelBox``.

This module runs a fixed table of segments/boxes and label/font combos
through BOTH the Python functions (called directly) and the JS functions
(via a small ``node`` subprocess harness that JSON-prints results), then
asserts per-case agreement: geometry within 1e-9, the box estimator
within 1e-6. Skips cleanly when ``node`` is absent (mirrors the
``_have_node_with_pptxgenjs`` skip pattern in test_full_bleed_scale.py —
this module has zero JS dependencies, so only a bare ``node`` probe is
needed, no ``pptxgenjs`` resolution check).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.annotation_payload import estimate_label_box, segment_box_entry  # noqa: E402

GEOMETRY_JS = PLUGIN_ROOT / "src" / "assembler" / "annotation_geometry.js"

GEOMETRY_TOL = 1e-9
ESTIMATOR_TOL = 1e-6

# --- fixed test table --------------------------------------------------

SEGMENT_CASES = [
    {
        "name": "generic_diagonal_approach",
        "p0": [0.0, 0.0], "p1": [10.0, 5.0], "box": [6.0, 2.0, 9.0, 4.0],
    },
    {
        "name": "axis_aligned_horizontal_approach",
        "p0": [0.0, 5.0], "p1": [10.0, 5.0], "box": [8.0, 3.0, 12.0, 7.0],
    },
    {
        "name": "axis_aligned_vertical_approach",
        "p0": [5.0, 0.0], "p1": [5.0, 10.0], "box": [3.0, 8.0, 7.0, 12.0],
    },
    {
        "name": "anchor_inside_box_zero_length_collapse",
        # Both p0 and p1 (label centre) lie inside the box -> the slab
        # clip never needs to advance past t=0, so the entry point IS
        # the anchor itself (zero-length leader).
        "p0": [4.0, 4.0], "p1": [6.0, 6.0], "box": [2.0, 2.0, 8.0, 8.0],
    },
    {
        "name": "corner_grazing_diagonal",
        # The p0->p1 diagonal (y = x) passes exactly through the box's
        # top-left and bottom-right corners.
        "p0": [0.0, 0.0], "p1": [10.0, 10.0], "box": [4.0, 4.0, 6.0, 6.0],
    },
    {
        "name": "parallel_outside_slab_degenerate",
        # Vertical segment (dx == 0) whose x sits outside the box's
        # x-range entirely -> never enters the box; falls back to p1.
        "p0": [0.0, 0.0], "p1": [0.0, 10.0], "box": [5.0, 2.0, 10.0, 8.0],
    },
    {
        "name": "box_disjoint_from_segment_degenerate",
        # Box far away from the p0->p1 segment -> t_min > t_max fallback.
        "p0": [0.0, 0.0], "p1": [5.0, 5.0], "box": [20.0, 20.0, 25.0, 25.0],
    },
    {
        "name": "negative_coordinate_space",
        "p0": [-5.0, -5.0], "p1": [-1.0, -1.0], "box": [-3.0, -3.0, -0.5, -0.5],
    },
]

ESTIMATE_CASES = [
    {"text": "Rudder", "font_size_pt": 18},
    {"text": "Mizzenmast", "font_size_pt": 12},
    {"text": "Keel", "font_size_pt": 36},
    {"text": "A", "font_size_pt": 9},
    {"text": "Bow thruster (fwd)", "font_size_pt": 14, "pad_in": 0.1},
]


def _have_node() -> bool:
    """True only if `node` is on PATH.

    This module has zero JS dependencies (plain CommonJS, no requires
    beyond core), so — unlike ``_have_node_with_pptxgenjs`` in
    test_full_bleed_scale.py — no package-resolution probe is needed.
    """
    return shutil.which("node") is not None


_HARNESS_TEMPLATE = """
const {{ segmentBoxEntry, estimateLabelBox }} = require({module_path});
const cases = {cases_json};
const out = {{ segment: [], estimate: [] }};
for (const c of cases.segment) {{
  out.segment.push(segmentBoxEntry(c.p0, c.p1, c.box));
}}
for (const c of cases.estimate) {{
  out.estimate.push(estimateLabelBox(c.text, c.font_size_pt, c.pad_in));
}}
process.stdout.write(JSON.stringify(out));
"""


def _run_js_harness(tmp_path: Path) -> dict:
    module_path = json.dumps(str(GEOMETRY_JS))
    cases_json = json.dumps({"segment": SEGMENT_CASES, "estimate": ESTIMATE_CASES})
    script = _HARNESS_TEMPLATE.format(module_path=module_path, cases_json=cases_json)
    script_path = tmp_path / "annotation_geometry_harness.js"
    script_path.write_text(script)

    result = subprocess.run(
        ["node", str(script_path)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"JS geometry harness failed: {result.stderr}"
    return json.loads(result.stdout)


def _run_python(cases_key: str = None) -> dict:
    segment_results = []
    for case in SEGMENT_CASES:
        segment_results.append(list(segment_box_entry(
            tuple(case["p0"]), tuple(case["p1"]), tuple(case["box"]),
        )))

    estimate_results = []
    for case in ESTIMATE_CASES:
        pad_in = case.get("pad_in", 0.06)
        estimate_results.append(list(
            estimate_label_box(case["text"], case["font_size_pt"], pad_in=pad_in)
        ))

    return {"segment": segment_results, "estimate": estimate_results}


# --- parity tests --------------------------------------------------------


@pytest.mark.skipif(not _have_node(), reason="node not available")
def test_js_segment_box_entry_parity(tmp_path):
    """JS `segmentBoxEntry` output matches Python `segment_box_entry`
    (delegating to `annotate_figure._segment_box_entry`) for every case in
    the fixed segment/box table, including the anchor-inside-box
    zero-length collapse, axis-aligned approaches, corner grazing, and
    both flavours of degenerate fallback."""
    js_results = _run_js_harness(tmp_path)
    py_results = _run_python()

    assert len(js_results["segment"]) == len(SEGMENT_CASES)
    for case, js_point, py_point in zip(
        SEGMENT_CASES, js_results["segment"], py_results["segment"]
    ):
        for axis in (0, 1):
            assert js_point[axis] == pytest.approx(py_point[axis], abs=GEOMETRY_TOL), (
                f"case {case['name']!r} axis {axis}: "
                f"js={js_point} py={py_point}"
            )

    # Sanity-check two cases against hand-computed expected geometry, so
    # the parity assertion above cannot be satisfied by a bug shared
    # identically by both ports.
    by_name = {c["name"]: i for i, c in enumerate(SEGMENT_CASES)}

    i = by_name["axis_aligned_vertical_approach"]
    assert py_results["segment"][i] == pytest.approx([5.0, 8.0], abs=GEOMETRY_TOL)
    assert js_results["segment"][i] == pytest.approx([5.0, 8.0], abs=GEOMETRY_TOL)

    i = by_name["anchor_inside_box_zero_length_collapse"]
    assert py_results["segment"][i] == pytest.approx([4.0, 4.0], abs=GEOMETRY_TOL)
    assert js_results["segment"][i] == pytest.approx([4.0, 4.0], abs=GEOMETRY_TOL)

    i = by_name["corner_grazing_diagonal"]
    assert py_results["segment"][i] == pytest.approx([4.0, 4.0], abs=GEOMETRY_TOL)
    assert js_results["segment"][i] == pytest.approx([4.0, 4.0], abs=GEOMETRY_TOL)

    i = by_name["parallel_outside_slab_degenerate"]
    assert py_results["segment"][i] == pytest.approx([0.0, 10.0], abs=GEOMETRY_TOL)
    assert js_results["segment"][i] == pytest.approx([0.0, 10.0], abs=GEOMETRY_TOL)

    i = by_name["box_disjoint_from_segment_degenerate"]
    assert py_results["segment"][i] == pytest.approx([5.0, 5.0], abs=GEOMETRY_TOL)
    assert js_results["segment"][i] == pytest.approx([5.0, 5.0], abs=GEOMETRY_TOL)


@pytest.mark.skipif(not _have_node(), reason="node not available")
def test_label_box_estimator_parity(tmp_path):
    """JS `estimateLabelBox` output matches Python `estimate_label_box`
    for a fixed label/font-size table (incl. a pad_in override), within
    1e-6 — the estimator-level parity T4 owns. (OOXML-level estimator
    parity in the assembled deck belongs to T5/T6, per the design doc.)"""
    js_results = _run_js_harness(tmp_path)
    py_results = _run_python()

    assert len(js_results["estimate"]) == len(ESTIMATE_CASES)
    for case, js_box, py_box in zip(
        ESTIMATE_CASES, js_results["estimate"], py_results["estimate"]
    ):
        assert js_box[0] == pytest.approx(py_box[0], abs=ESTIMATOR_TOL), (
            f"case {case!r} width: js={js_box} py={py_box}"
        )
        assert js_box[1] == pytest.approx(py_box[1], abs=ESTIMATOR_TOL), (
            f"case {case!r} height: js={js_box} py={py_box}"
        )


def test_js_and_python_case_tables_stay_in_sync():
    """Guards against a future edit adding a case to one list constant
    without the other — both parity tests iterate SEGMENT_CASES /
    ESTIMATE_CASES by shared index, so a length mismatch would silently
    truncate coverage via zip()."""
    assert len({c["name"] for c in SEGMENT_CASES}) == len(SEGMENT_CASES), (
        "duplicate case name in SEGMENT_CASES"
    )
    assert len(ESTIMATE_CASES) >= 5
