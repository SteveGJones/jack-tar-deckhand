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
