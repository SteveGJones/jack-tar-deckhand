"""Aggregate per-case matrices into a summary report."""
from __future__ import annotations

import json
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "results"


def aggregate() -> dict:
    summary: dict = {"cases": []}
    for path in sorted(RESULTS.glob("matrix-*.json")):
        d = json.loads(path.read_text())
        per_field: dict[str, list[bool]] = {}
        for slide in d["slide_comparisons"]:
            for f in slide["fields"]:
                per_field.setdefault(f["field"], []).append(f["agree"])
        summary["cases"].append(
            {
                "case": d["case_name"],
                "pptx_slides": d["pptx_slide_count"],
                "js_slides": d["js_slide_count"],
                "js_error": d.get("js_error"),
                "pptx_markers": d["pptx_marker_total"],
                "js_markers": d["js_marker_total"],
                "agreement_by_field": {
                    field: {
                        "agree": sum(vals),
                        "total": len(vals),
                        "rate": (sum(vals) / len(vals)) if vals else 0.0,
                    }
                    for field, vals in per_field.items()
                },
            }
        )
    return summary


if __name__ == "__main__":
    s = aggregate()
    out = RESULTS / "summary.json"
    out.write_text(json.dumps(s, indent=2))
    print(json.dumps(s, indent=2))
