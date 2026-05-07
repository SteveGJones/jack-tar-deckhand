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
    # When Flash passes and budget allows, Phase C runs Pro single-shot;
    # otherwise the Flash result stands. Either is a valid cloud escalation.
    assert result.tier_used in ("nanobanana_flash", "nanobanana_pro")


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
    # Privacy gating: restricted tier returns halted_restricted (per spec
    # caveat — distinct from accepted_with_issues which is reserved for
    # internal-tier-unconfirmed). Cloud must not have been called.
    assert result.status == "halted_restricted"
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
