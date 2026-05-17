"""Tests for the academic_figure strategy classifier (paperbanana E1).

The classifier returns ``"academic_figure"`` only when 2+ unambiguous
academic signals fire and no negative business/executive signal is
present. Single-signal hits and signal-less slides defer to the upstream
Claude pass by returning ``strategy=None``.
"""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

import pytest

from src.strategy_classifier import (  # noqa: E402
    StrategyClassification,
    classify_strategy,
)


# --- Positive cases: 2+ signals → academic_figure ------------------------


def test_classifies_explicit_figure_caption_plus_citation():
    result = classify_strategy(
        "Figure 3: Transformer attention head architecture [12]. "
        "The encoder stack uses 6 layers with 8 attention heads."
    )
    assert result.strategy == "academic_figure"
    assert len(result.matched_signals) >= 2


def test_classifies_latex_math_plus_algorithm():
    result = classify_strategy(
        "Algorithm 2 (gradient descent). Update rule: "
        r"\theta_{t+1} = \theta_t - \alpha \nabla_\theta L(\theta_t). "
        "We show this converges to a local minimum."
    )
    assert result.strategy == "academic_figure"


def test_classifies_block_equation_plus_citation():
    result = classify_strategy(
        "The loss function balances cross-entropy with an L2 regulariser:\n\n"
        "$$L(\\theta) = -\\sum_i y_i \\log \\hat{y}_i + \\lambda \\|\\theta\\|^2$$\n\n"
        "Following Vaswani et al. and the implementation in [7]."
    )
    assert result.strategy == "academic_figure"


def test_classifies_ml_architecture_subject_plus_figure_caption():
    result = classify_strategy(
        "Figure 1: System architecture for a multi-head encoder. "
        "Each layer applies self-attention and a feed-forward head."
    )
    assert result.strategy == "academic_figure"


def test_classifies_ablation_study_plus_table_citation():
    result = classify_strategy(
        "Ablation study results comparing four model variants. "
        "We follow the protocol of [23] and Smith et al."
    )
    assert result.strategy == "academic_figure"


def test_classifies_confusion_matrix_plus_citation():
    result = classify_strategy(
        "Figure 4: Confusion matrix on the test split. "
        "We compare against the baseline reported by Brown et al."
    )
    assert result.strategy == "academic_figure"


# --- Negative cases: single or zero signals → None ----------------------


def test_single_signal_does_not_classify():
    result = classify_strategy("Algorithm 1 is a well-known approach.")
    assert result.strategy is None
    assert len(result.matched_signals) == 1


def test_no_signals_defers_to_upstream():
    result = classify_strategy(
        "Our quarterly revenue grew 18% year over year. "
        "Three drivers explain the result: new logos, expansion, retention."
    )
    assert result.strategy is None
    assert result.matched_signals == []


def test_empty_text_defers_to_upstream():
    result = classify_strategy("")
    assert result.strategy is None
    assert "empty" in result.rationale.lower()


# --- Negative signal vetoes academic_figure ----------------------------


def test_negative_signal_vetoes_even_with_strong_positive_signals():
    """Business-context slides must not be misclassified even when they
    incidentally cite academic work."""
    result = classify_strategy(
        "Executive summary. Figure 1: market sizing model. "
        "Our go-to-market is based on the framework of Christensen et al."
    )
    assert result.strategy is None
    assert any(s.startswith("negative:") for s in result.matched_signals)


def test_press_release_with_figure_caption_does_not_classify():
    result = classify_strategy(
        "Press release. Figure 1 shows our growth chart. "
        "Citation: see [1] for methodology."
    )
    assert result.strategy is None


# --- paperbanana_available flag affects rationale only ----------------


def test_paperbanana_available_changes_rationale():
    text = "Figure 1: encoder architecture [3]. Each layer uses 8 attention heads."
    with_pb = classify_strategy(text, paperbanana_available=True)
    without_pb = classify_strategy(text, paperbanana_available=False)
    assert with_pb.strategy == "academic_figure"
    assert without_pb.strategy == "academic_figure"
    # Both classify the same way; rationale differs only.
    assert "reachable" in with_pb.rationale.lower()
    assert "not detected" in without_pb.rationale.lower() or "fall back" in without_pb.rationale.lower()


# --- Return type sanity -----------------------------------------------


def test_returns_strategy_classification_dataclass():
    result = classify_strategy("Figure 1: x [1].")
    assert isinstance(result, StrategyClassification)
    assert hasattr(result, "strategy")
    assert hasattr(result, "rationale")
    assert hasattr(result, "matched_signals")
    assert isinstance(result.matched_signals, list)


# --- Schema integration ----------------------------------------------


def test_academic_figure_is_in_strategy_enum():
    """Sanity — the classifier's output must validate against the schema."""
    import json

    schema_path = PLUGIN_ROOT / "src" / "schemas" / "strategy_map.schema.json"
    schema = json.loads(schema_path.read_text())
    strategy_enum = schema["properties"]["slides"]["items"]["properties"]["strategy"]["enum"]
    assert "academic_figure" in strategy_enum
    speaker_override_enum = schema["properties"]["slides"]["items"]["properties"]["speaker_override"]["enum"]
    assert "academic_figure" in speaker_override_enum
