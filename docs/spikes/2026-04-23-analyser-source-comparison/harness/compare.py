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
