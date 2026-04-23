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
    requested = {"IMAGE": 1}
    emitted = {"IMAGE": 3}
    result = score(requested, emitted)
    assert result["overall_rate"] == 1.0
    assert result["extra"] == {"IMAGE": 2}
