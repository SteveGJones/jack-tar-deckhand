"""Tests for the iterate-slide dispatch helper.

The helper is the testable boundary around the
``/jack-tar-deckhand:iterate-slide`` skill — the subprocess invocation
+ image-reviewer dispatch happen in SKILL.md by Claude, but the
mode-dispatch, feedback assembly, manifest find/update, F7 workaround,
and stdout parsing are pure Python and covered here.

See also:
- ``docs/superpowers/dogfooding/2026-05-18-paperbanana-integration.md``
  §7b/§7c for the empirical evidence behind the F8/F9/F10 findings the
  helper implements.
- Issue #89 body for the full design spec.
"""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

import pytest

from src.iterate_slide_dispatch import (  # noqa: E402
    IterateMode,
    IterateSlidePlan,
    IterateSlideRefinementRequest,
    build_enumerate_feedback,
    cli_args_to_argv,
    ensure_run_dir_local,
    find_manifest_entry,
    parse_output_path_from_stdout,
    plan_refinement,
    update_manifest_entry,
)


VALID_RUN_ID = "run_20260518_190654_814b57"
VALID_RUN_ID_2 = "run_20260519_120000_abc1234"


# --- IterateMode enum ----------------------------------------------------


def test_iterate_mode_values_are_stable():
    """The three string values are the public contract — pin them."""
    assert IterateMode.AUTO.value == "auto"
    assert IterateMode.ENUMERATE.value == "enumerate"
    assert IterateMode.DRAFT.value == "draft"


def test_iterate_mode_str_to_enum_via_constructor():
    assert IterateMode("auto") is IterateMode.AUTO
    assert IterateMode("enumerate") is IterateMode.ENUMERATE
    assert IterateMode("draft") is IterateMode.DRAFT


def test_iterate_mode_unknown_string_raises():
    with pytest.raises(ValueError):
        IterateMode("xyz")


# --- IterateSlideRefinementRequest ---------------------------------------


def test_request_defaults_are_empty():
    req = IterateSlideRefinementRequest()
    assert req.feedback == ""
    assert req.must_mention == []
    assert req.must_be_visually_prominent == []
    assert req.keep_from_prior == []


def test_request_lists_are_independent_per_instance():
    """Defaults from field(default_factory=list) must not share state."""
    a = IterateSlideRefinementRequest()
    b = IterateSlideRefinementRequest()
    a.must_mention.append("X")
    assert b.must_mention == []


# --- build_enumerate_feedback --------------------------------------------


def test_enumerate_feedback_empty_request_returns_empty():
    assert build_enumerate_feedback(IterateSlideRefinementRequest()) == ""


def test_enumerate_feedback_preamble_only():
    req = IterateSlideRefinementRequest(feedback="The colours need work.")
    fb = build_enumerate_feedback(req)
    assert fb == "The colours need work."


def test_enumerate_feedback_strips_preamble_whitespace():
    req = IterateSlideRefinementRequest(feedback="   padded   ")
    assert build_enumerate_feedback(req) == "padded"


def test_enumerate_feedback_must_mention_uses_strong_imperative():
    req = IterateSlideRefinementRequest(
        must_mention=["item-A", "item-B", "item-C"],
    )
    fb = build_enumerate_feedback(req)
    assert "MUST-MENTION" in fb
    assert "MUST appear" in fb
    assert "NO omissions" in fb
    assert "NO substitutions" in fb
    assert "- item-A\n- item-B\n- item-C" in fb


def test_enumerate_feedback_must_mention_grants_shrink_permission():
    """The F9 finding: permission to shrink/relayout is what unblocks
    the Visualizer's defence of prior layout against unbounded growth.
    """
    req = IterateSlideRefinementRequest(
        must_mention=["one", "two"],
    )
    fb = build_enumerate_feedback(req).lower()
    assert "permission" in fb
    assert "shrink" in fb or "font" in fb


def test_enumerate_feedback_visually_prominent_block():
    req = IterateSlideRefinementRequest(
        must_be_visually_prominent=[
            "outer boundary solid 2px dark grey",
            "title text at 36pt minimum",
        ],
    )
    fb = build_enumerate_feedback(req)
    assert "MUST-BE-VISUALLY-PROMINENT" in fb
    assert "outer boundary solid 2px dark grey" in fb
    assert "title text at 36pt minimum" in fb


def test_enumerate_feedback_keep_block_protects_prior_iter_wins():
    """The F9 'KEEP header' pattern — the dogfood Tier-2 named iter-4
    wins explicitly so they survived 2 more iters of refinement.
    """
    req = IterateSlideRefinementRequest(
        keep_from_prior=[
            "saturated coral on the bridge plugin",
            "rerouted upstream arrow",
        ],
    )
    fb = build_enumerate_feedback(req)
    assert "KEEP" in fb
    assert "do NOT undo" in fb
    assert "saturated coral on the bridge plugin" in fb


def test_enumerate_feedback_all_four_sections_in_order():
    """Section order matters for the F9 pattern."""
    req = IterateSlideRefinementRequest(
        feedback="Preamble.",
        must_mention=["A"],
        must_be_visually_prominent=["B"],
        keep_from_prior=["C"],
    )
    fb = build_enumerate_feedback(req)
    # Order: preamble → MUST-MENTION → MUST-BE-VISUALLY-PROMINENT → KEEP
    preamble_idx = fb.index("Preamble.")
    mm_idx = fb.index("MUST-MENTION")
    mvp_idx = fb.index("MUST-BE-VISUALLY-PROMINENT")
    keep_idx = fb.index("KEEP")
    assert preamble_idx < mm_idx < mvp_idx < keep_idx


def test_enumerate_feedback_omits_empty_sections():
    """Only-keep section, no preamble — must work without empty markers."""
    req = IterateSlideRefinementRequest(
        keep_from_prior=["something"],
    )
    fb = build_enumerate_feedback(req)
    assert "MUST-MENTION" not in fb
    assert "MUST-BE-VISUALLY-PROMINENT" not in fb
    assert "KEEP" in fb


# --- plan_refinement -----------------------------------------------------


def test_plan_refinement_invalid_run_id_raises():
    with pytest.raises(ValueError, match="paperbanana pattern"):
        plan_refinement("auto", "not-a-run-id", IterateSlideRefinementRequest())


def test_plan_refinement_auto_default_iterations_is_4():
    plan = plan_refinement("auto", VALID_RUN_ID, IterateSlideRefinementRequest())
    assert plan.mode == IterateMode.AUTO
    assert plan.iterations == 4


def test_plan_refinement_auto_emits_auto_flag_and_max_iterations():
    plan = plan_refinement("auto", VALID_RUN_ID, IterateSlideRefinementRequest())
    assert plan.cli_args.get("--auto") is True
    assert plan.cli_args.get("--max-iterations") == "4"
    assert plan.cli_args.get("--continue-run") == VALID_RUN_ID


def test_plan_refinement_auto_no_feedback_omits_feedback_flag():
    """Empty feedback in auto mode must not produce an empty --feedback ''."""
    plan = plan_refinement("auto", VALID_RUN_ID, IterateSlideRefinementRequest())
    assert "--feedback" not in plan.cli_args


def test_plan_refinement_auto_with_feedback_passes_through_verbatim():
    req = IterateSlideRefinementRequest(feedback="Make the colours bolder.")
    plan = plan_refinement("auto", VALID_RUN_ID, req)
    # Auto mode passes feedback through; NO enumeration expansion
    assert plan.feedback == "Make the colours bolder."
    assert plan.cli_args["--feedback"] == "Make the colours bolder."
    assert "MUST-MENTION" not in plan.cli_args["--feedback"]


def test_plan_refinement_enumerate_default_iterations_is_2():
    """F8: single-iter regresses; default to 2 for enumerate mode."""
    plan = plan_refinement(
        "enumerate", VALID_RUN_ID,
        IterateSlideRefinementRequest(must_mention=["x"]),
    )
    assert plan.iterations == 2


def test_plan_refinement_enumerate_assembles_feedback_from_structured_input():
    req = IterateSlideRefinementRequest(
        must_mention=["a", "b"],
        keep_from_prior=["c"],
    )
    plan = plan_refinement("enumerate", VALID_RUN_ID, req)
    assert "MUST-MENTION" in plan.cli_args["--feedback"]
    assert "KEEP" in plan.cli_args["--feedback"]
    assert "- a" in plan.cli_args["--feedback"]
    assert "- c" in plan.cli_args["--feedback"]


def test_plan_refinement_enumerate_omits_auto_flag():
    plan = plan_refinement(
        "enumerate", VALID_RUN_ID,
        IterateSlideRefinementRequest(must_mention=["x"]),
    )
    assert "--auto" not in plan.cli_args
    assert "--max-iterations" not in plan.cli_args
    assert plan.cli_args["--iterations"] == "2"


def test_plan_refinement_draft_emits_auto_phase_first():
    """Draft mode emits the auto phase plan first — SKILL.md re-plans
    in enumerate on fallthrough."""
    req = IterateSlideRefinementRequest(
        feedback="something",
        must_mention=["x", "y"],
    )
    plan = plan_refinement("draft", VALID_RUN_ID, req)
    assert plan.mode == IterateMode.DRAFT  # mode reported as DRAFT for orchestrator
    assert plan.cli_args.get("--auto") is True
    # Auto phase passes feedback through verbatim; structured input not
    # expanded yet (that happens on enumerate fallthrough)
    assert "MUST-MENTION" not in plan.cli_args.get("--feedback", "")


def test_plan_refinement_iterations_override():
    plan = plan_refinement(
        "enumerate", VALID_RUN_ID,
        IterateSlideRefinementRequest(must_mention=["x"]),
        iterations=5,
    )
    assert plan.iterations == 5
    assert plan.cli_args["--iterations"] == "5"


def test_plan_refinement_budget_override():
    plan = plan_refinement(
        "auto", VALID_RUN_ID,
        IterateSlideRefinementRequest(),
        budget_usd=0.10,
    )
    assert plan.budget_usd == 0.10
    assert plan.cli_args["--budget"] == "0.10"


def test_plan_refinement_unknown_mode_raises():
    # Mock an IterateMode-shaped value that doesn't match any branch
    # (cleanest path: pass a string that bypasses the enum coerce step
    # by being a valid mode but not handled — there isn't such a case
    # in practice because the enum is exhaustive. So we test by
    # corrupting the mode parameter after enum construction is bypassed.)
    # Instead, verify the string→enum conversion rejects unknowns.
    with pytest.raises(ValueError):
        plan_refinement("unknown-mode", VALID_RUN_ID, IterateSlideRefinementRequest())


def test_plan_refinement_includes_explicit_models():
    """F2 finding: must NOT rely on paperbanana's deprecated defaults."""
    plan = plan_refinement("auto", VALID_RUN_ID, IterateSlideRefinementRequest())
    assert plan.cli_args["--vlm-model"] == "gemini-2.5-flash"
    assert plan.cli_args["--image-model"] == "gemini-3.1-flash-image-preview"


# --- cli_args_to_argv ----------------------------------------------------


def test_cli_args_to_argv_basic_key_value():
    args = {"--foo": "bar", "--baz": "qux"}
    assert cli_args_to_argv(args) == ["--foo", "bar", "--baz", "qux"]


def test_cli_args_to_argv_boolean_true_becomes_bare_flag():
    args = {"--verbose": True, "--input": "x"}
    assert cli_args_to_argv(args) == ["--verbose", "--input", "x"]


def test_cli_args_to_argv_false_and_none_omitted():
    args = {"--keep": "yes", "--skip-1": False, "--skip-2": None}
    assert cli_args_to_argv(args) == ["--keep", "yes"]


def test_cli_args_to_argv_preserves_insertion_order():
    """Order matters for log consistency."""
    args = {"--first": "1", "--second": "2", "--third": "3"}
    argv = cli_args_to_argv(args)
    assert argv == ["--first", "1", "--second", "2", "--third", "3"]


# --- parse_output_path_from_stdout ---------------------------------------


def test_parse_output_path_with_output_colon_prefix():
    stdout = "Done! 200.0s total · 2 iterations\n  Output: outputs/run_x/final_output.png\n  Run ID: run_x"
    assert parse_output_path_from_stdout(stdout) == "outputs/run_x/final_output.png"


def test_parse_output_path_with_output_saved_to_prefix():
    stdout = "Done! Output saved to: /tmp/run_y/final_output.png"
    assert parse_output_path_from_stdout(stdout) == "/tmp/run_y/final_output.png"


def test_parse_output_path_missing_returns_empty():
    assert parse_output_path_from_stdout("just some unrelated text") == ""


def test_parse_output_path_empty_input():
    assert parse_output_path_from_stdout("") == ""


def test_parse_output_path_first_match_wins():
    """When paperbanana echoes its output line multiple times, first wins."""
    stdout = "Output: first.png\nSomething else\nOutput: second.png"
    assert parse_output_path_from_stdout(stdout) == "first.png"


# --- ensure_run_dir_local (F7 workaround) --------------------------------


def test_ensure_run_dir_local_returns_existing_target(tmp_path):
    """If the run dir already exists under target_outputs, no copy."""
    target = tmp_path / "outputs"
    (target / VALID_RUN_ID).mkdir(parents=True)
    (target / VALID_RUN_ID / "final_output.png").touch()

    result = ensure_run_dir_local(VALID_RUN_ID, "/nonexistent/source", str(target))
    assert (target / VALID_RUN_ID).exists()
    assert Path(result).name == VALID_RUN_ID


def test_ensure_run_dir_local_copies_from_source(tmp_path):
    """When the run dir doesn't exist locally, copy from source root."""
    source_root = tmp_path / "tmp"
    target_root = tmp_path / "deck-dir" / "outputs"
    source_dir = source_root / VALID_RUN_ID
    source_dir.mkdir(parents=True)
    (source_dir / "final_output.png").write_bytes(b"png data")
    (source_dir / "metadata.json").write_text("{}")

    result = ensure_run_dir_local(VALID_RUN_ID, str(source_root), str(target_root))
    target_dir = target_root / VALID_RUN_ID
    assert target_dir.exists()
    assert (target_dir / "final_output.png").read_bytes() == b"png data"
    assert (target_dir / "metadata.json").read_text() == "{}"
    assert Path(result).name == VALID_RUN_ID


def test_ensure_run_dir_local_invalid_run_id_raises():
    with pytest.raises(ValueError, match="paperbanana pattern"):
        ensure_run_dir_local("garbage", "/tmp", "/tmp/outputs")


def test_ensure_run_dir_local_source_missing_raises(tmp_path):
    """When neither target nor source has the run dir, raise FileNotFound."""
    with pytest.raises(FileNotFoundError, match="Source run dir not found"):
        ensure_run_dir_local(
            VALID_RUN_ID,
            str(tmp_path / "nonexistent-source"),
            str(tmp_path / "outputs"),
        )


# --- find_manifest_entry -------------------------------------------------


def test_find_manifest_entry_in_entries_key():
    manifest = {"entries": [{"slide_number": 1}, {"slide_number": 7, "file_path": "/x"}]}
    assert find_manifest_entry(manifest, 7) == {"slide_number": 7, "file_path": "/x"}


def test_find_manifest_entry_in_images_key():
    """Legacy schemas use 'images' instead of 'entries'."""
    manifest = {"images": [{"slide_number": 3, "model_used": "ollama"}]}
    assert find_manifest_entry(manifest, 3) == {"slide_number": 3, "model_used": "ollama"}


def test_find_manifest_entry_missing_returns_none():
    manifest = {"entries": [{"slide_number": 1}]}
    assert find_manifest_entry(manifest, 99) is None


def test_find_manifest_entry_empty_manifest_returns_none():
    assert find_manifest_entry({}, 1) is None


def test_find_manifest_entry_returns_fresh_dict():
    """Caller mutation must not bleed into the source manifest."""
    original = {"slide_number": 1, "model_used": "paperbanana"}
    manifest = {"entries": [original]}
    found = find_manifest_entry(manifest, 1)
    found["model_used"] = "MUTATED"
    assert original["model_used"] == "paperbanana"


# --- update_manifest_entry -----------------------------------------------


def test_update_manifest_entry_overwrites_path_and_hash():
    prior = {"slide_number": 7, "file_path": "/old.png", "content_hash": "old"}
    updated = update_manifest_entry(prior, "/new.png", "newhash")
    assert updated["file_path"] == "/new.png"
    assert updated["content_hash"] == "newhash"


def test_update_manifest_entry_does_not_mutate_input():
    prior = {"slide_number": 7, "file_path": "/old.png", "content_hash": "old"}
    update_manifest_entry(prior, "/new.png", "newhash")
    assert prior["file_path"] == "/old.png"


def test_update_manifest_entry_first_refinement_seeds_history_with_initial_args():
    """First refinement: history should contain the ORIGINAL paperbanana_args
    under 'initial' before the new refinement args."""
    prior = {
        "slide_number": 7,
        "file_path": "/old.png",
        "content_hash": "old",
        "paperbanana_args": {"iterations": 2, "aspect_ratio": "16:9"},
    }
    updated = update_manifest_entry(
        prior, "/new.png", "newhash",
        refinement_args={"mode": "enumerate", "iterations": 2},
    )
    assert len(updated["paperbanana_history"]) == 2
    assert updated["paperbanana_history"][0]["iteration"] == "initial"
    assert updated["paperbanana_history"][0]["args"]["aspect_ratio"] == "16:9"
    assert updated["paperbanana_history"][1]["iteration"] == "refinement_1"


def test_update_manifest_entry_increments_refinement_count():
    prior = {"slide_number": 7, "refinement_count": 2}
    updated = update_manifest_entry(prior, "/new.png", "newhash")
    assert updated["refinement_count"] == 3


def test_update_manifest_entry_zero_count_on_first_call():
    """No refinement_count present → starts at 0, becomes 1 after first call."""
    prior = {"slide_number": 7}
    updated = update_manifest_entry(prior, "/new.png", "newhash")
    assert updated["refinement_count"] == 1


def test_update_manifest_entry_subsequent_refinement_appends_only():
    """Second refinement: history already seeded; just append, don't re-seed."""
    prior = {
        "slide_number": 7,
        "file_path": "/v2.png",
        "content_hash": "hash2",
        "paperbanana_args": {"mode": "enumerate"},
        "paperbanana_history": [
            {"iteration": "initial", "args": {"iterations": 2}},
            {"iteration": "refinement_1", "args": {"mode": "enumerate"}},
        ],
        "refinement_count": 1,
    }
    updated = update_manifest_entry(
        prior, "/v3.png", "hash3",
        refinement_args={"mode": "auto", "iterations": 4},
    )
    assert len(updated["paperbanana_history"]) == 3
    assert updated["paperbanana_history"][2]["iteration"] == "refinement_2"
    assert updated["paperbanana_history"][2]["args"]["mode"] == "auto"
    assert updated["refinement_count"] == 2


def test_update_manifest_entry_no_refinement_args_skips_history_append():
    """When refinement_args is None — used for in-place path-fix without
    recording a refinement — history is not appended."""
    prior = {
        "slide_number": 7,
        "file_path": "/old.png",
        "content_hash": "old",
        "paperbanana_args": {"iterations": 2},
    }
    updated = update_manifest_entry(prior, "/new.png", "newhash", refinement_args=None)
    assert updated["file_path"] == "/new.png"
    # No history appended; original paperbanana_args preserved
    assert updated["paperbanana_args"] == {"iterations": 2}
    assert "paperbanana_history" not in updated


# --- IterateSlidePlan dataclass ------------------------------------------


def test_plan_dataclass_construction():
    plan = IterateSlidePlan(
        mode=IterateMode.AUTO,
        run_id=VALID_RUN_ID,
        feedback="x",
        iterations=4,
    )
    assert plan.mode == IterateMode.AUTO
    assert plan.cli_args == {}
    assert plan.budget_usd == 0.25
