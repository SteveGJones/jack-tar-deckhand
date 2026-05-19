"""iterate-slide dispatch helper.

Pure-Python boundary for the ``/jack-tar-deckhand:iterate-slide`` skill.
The subprocess invocation + image-reviewer dispatch happen in SKILL.md
by Claude; everything around them (mode dispatch, feedback assembly,
manifest find/update, F7 workaround, stdout parsing) is covered here
and is unit-testable.

Three refinement modes derived from the 2026-05-18 multi-tier dogfood:

- **auto** — invoke ``paperbanana generate --continue-run --auto
  --max-iterations N``. No transformation of operator feedback. Best
  for explanatory / flow diagrams where the Critic's visual-coherence
  optimisation matches the desired output (dogfood §7c / finding F10).

- **enumerate** — operator supplies structured input (``must_mention``,
  ``must_be_visually_prominent``, ``keep_from_prior``); the helper
  assembles a strong-imperative feedback string with explicit
  enumeration + permission-to-shrink + KEEP header. Default 2 iters
  per finding F8 (single-iter regresses). Best for completeness /
  specification artefacts where the Critic alone cannot infer "list
  all N by name" from the methodology context.

- **draft** — hybrid: emit an auto plan first; the SKILL.md
  orchestrator monitors Critic verdict and re-plans in enumerate
  mode on fallthrough.

See ``docs/superpowers/dogfooding/2026-05-18-paperbanana-integration.md``
§7b/§7c for empirical evidence, ``docs/architecture/paperbanana-integration-v2.md``
for the surrounding integration contract, and issue #89 body for the
full design spec.
"""
from __future__ import annotations

import enum
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping


# Paperbanana run-id pattern: run_<YYYYMMDD>_<HHMMSS>_<short-hash>
_RUN_DIR_PATTERN = re.compile(r"^run_\d{8}_\d{6}_[a-f0-9]+$")

# Paperbanana writes "Output: <path>" or "Output saved to: <path>" near
# the end of a successful run. We grep stdout for that.
_OUTPUT_PATH_PATTERN = re.compile(r"Output(?:\s+saved)?(?:\s+to)?:\s+(\S+)")

# Defaults tuned from the 2026-05-18 dogfood. Reviewable in one place.
_DEFAULT_VLM_PROVIDER = "gemini"
_DEFAULT_VLM_MODEL = "gemini-2.5-flash"
_DEFAULT_IMAGE_PROVIDER = "google_imagen"
_DEFAULT_IMAGE_MODEL = "gemini-3.1-flash-image-preview"
_DEFAULT_BUDGET_USD = 0.25
_DEFAULT_AUTO_MAX_ITERATIONS = 4
_DEFAULT_ENUMERATE_ITERATIONS = 2


class IterateMode(str, enum.Enum):
    """Refinement mode — drives feedback assembly and CLI args."""

    AUTO = "auto"
    ENUMERATE = "enumerate"
    DRAFT = "draft"


@dataclass
class IterateSlideRefinementRequest:
    """Structured input for refinement, regardless of mode.

    Auto mode uses only ``feedback`` (free-text preamble passed through
    to paperbanana verbatim). Enumerate / draft modes use the three
    structured fields below to assemble explicit-enumeration feedback
    per the F9 pattern that converged in the Tier-2 dogfood.

    Attributes:
        feedback: free-text operator note. Auto mode passes through;
            enumerate mode treats this as a preamble before the
            structured sections.
        must_mention: list of items that MUST appear in the refined
            figure (e.g. "all 11 skill names", "the smartart-selector
            footnote"). Enumerate mode expands these into an inline
            enumerated list inside the feedback.
        must_be_visually_prominent: visual properties that must hold
            (e.g. "outer boundary should be solid 2px dark grey").
        keep_from_prior: properties from the previous iteration that
            should NOT regress (e.g. "the saturated coral fill on the
            bridge plugin"). Enumerate mode brackets these under a
            "KEEP" header in the feedback.
    """

    feedback: str = ""
    must_mention: list[str] = field(default_factory=list)
    must_be_visually_prominent: list[str] = field(default_factory=list)
    keep_from_prior: list[str] = field(default_factory=list)


@dataclass
class IterateSlidePlan:
    """Result of ``plan_refinement`` — the bridge converts this to argv.

    Attributes:
        mode: the IterateMode the plan was built for.
        run_id: the paperbanana run_id (from the manifest entry's
            ``paperbanana_run_id`` field) we'll continue.
        feedback: the assembled feedback string (auto: passthrough;
            enumerate: assembled via build_enumerate_feedback).
        iterations: how many additional iterations paperbanana should
            run. Honours mode defaults (auto: 4, enumerate: 2) unless
            overridden by the caller.
        cli_args: ordered dict of CLI flag → value. Bridge converts
            this to argv via ``cli_args_to_argv``.
        budget_usd: paperbanana --budget guard (belt-and-braces; jack-
            tar's own accounting is authoritative).
    """

    mode: IterateMode
    run_id: str
    feedback: str
    iterations: int
    cli_args: dict = field(default_factory=dict)
    budget_usd: float = _DEFAULT_BUDGET_USD


def build_enumerate_feedback(request: IterateSlideRefinementRequest) -> str:
    """Assemble explicit-enumeration feedback string for enumerate mode.

    Implements the F9 pattern that converged in the 2026-05-18
    Tier-2 dogfood:

    1. Optional free-text preamble (request.feedback).
    2. MUST-MENTION block — strong-imperative enumeration with
       permission to shrink/relayout when adding items (the
       Visualizer otherwise defends prior layout against unbounded
       growth — F9 finding).
    3. MUST-BE-VISUALLY-PROMINENT block — explicit visual constraints
       the Visualizer must honour.
    4. KEEP block — properties from the prior iteration that must NOT
       regress (the Tier-2 dogfood pattern that protected iter-4 wins
       through 2 more iters of refinement).

    Empty / missing sections are omitted from the output. When all
    structured fields are empty AND ``request.feedback`` is empty,
    returns the empty string.
    """
    parts: list[str] = []

    preamble = request.feedback.strip()
    if preamble:
        parts.append(preamble)

    if request.must_mention:
        items = "\n".join(f"- {item}" for item in request.must_mention)
        parts.append(
            "MUST-MENTION (these items MUST appear in the figure, exactly as "
            "named, with NO omissions and NO substitutions; permission "
            "granted to shrink the body font, narrow line height, or split "
            "into a multi-column sub-grid if needed to fit them all — "
            "completeness takes precedence over text size on this "
            f"revision):\n{items}"
        )

    if request.must_be_visually_prominent:
        items = "\n".join(f"- {item}" for item in request.must_be_visually_prominent)
        parts.append(
            f"MUST-BE-VISUALLY-PROMINENT (these visual properties MUST hold):\n{items}"
        )

    if request.keep_from_prior:
        items = "\n".join(f"- {item}" for item in request.keep_from_prior)
        parts.append(
            "KEEP (these properties landed cleanly in the prior iteration — "
            f"do NOT undo them):\n{items}"
        )

    return "\n\n".join(parts)


def plan_refinement(
    mode: IterateMode | str,
    run_id: str,
    request: IterateSlideRefinementRequest,
    *,
    iterations: int | None = None,
    budget_usd: float | None = None,
    vlm_model: str = _DEFAULT_VLM_MODEL,
    image_model: str = _DEFAULT_IMAGE_MODEL,
) -> IterateSlidePlan:
    """Build the IterateSlidePlan for a mode + request.

    Args:
        mode: ``IterateMode`` value or its string form.
        run_id: paperbanana run id (validated to match
            ``run_<YYYYMMDD>_<HHMMSS>_<hash>``).
        request: structured refinement input.
        iterations: override the mode default. None uses the default
            (auto: 4, enumerate/draft: 2).
        budget_usd: override the CLI ``--budget`` cap.
        vlm_model: override the VLM model.
        image_model: override the image model.

    Returns:
        An IterateSlidePlan whose ``cli_args`` are ready for
        ``cli_args_to_argv``.

    Raises:
        ValueError: if mode is unknown or run_id doesn't match the
            paperbanana pattern.
    """
    mode_enum = IterateMode(mode) if isinstance(mode, str) else mode
    if not _RUN_DIR_PATTERN.match(run_id):
        raise ValueError(
            f"run_id doesn't match paperbanana pattern "
            f"run_<YYYYMMDD>_<HHMMSS>_<hash>: {run_id!r}"
        )

    budget = budget_usd if budget_usd is not None else _DEFAULT_BUDGET_USD

    # Common args shared across modes
    common = {
        "--continue-run": run_id,
        "--vlm-provider": _DEFAULT_VLM_PROVIDER,
        "--vlm-model": vlm_model,
        "--image-provider": _DEFAULT_IMAGE_PROVIDER,
        "--image-model": image_model,
        "--budget": f"{budget:.2f}",
    }

    if mode_enum == IterateMode.AUTO:
        iters = iterations if iterations is not None else _DEFAULT_AUTO_MAX_ITERATIONS
        cli_args: dict = {
            **common,
            "--auto": True,
            "--max-iterations": str(iters),
        }
        if request.feedback.strip():
            cli_args["--feedback"] = request.feedback.strip()
        return IterateSlidePlan(
            mode=mode_enum,
            run_id=run_id,
            feedback=request.feedback.strip(),
            iterations=iters,
            cli_args=cli_args,
            budget_usd=budget,
        )

    if mode_enum == IterateMode.ENUMERATE:
        iters = iterations if iterations is not None else _DEFAULT_ENUMERATE_ITERATIONS
        feedback = build_enumerate_feedback(request)
        cli_args = {
            **common,
            "--iterations": str(iters),
            "--feedback": feedback,
        }
        return IterateSlidePlan(
            mode=mode_enum,
            run_id=run_id,
            feedback=feedback,
            iterations=iters,
            cli_args=cli_args,
            budget_usd=budget,
        )

    if mode_enum == IterateMode.DRAFT:
        # Draft mode emits the auto-phase plan first. The SKILL.md
        # orchestrator monitors paperbanana's Critic verdict; if not
        # "satisfied" at safety cap, it re-calls plan_refinement with
        # mode=ENUMERATE on the same request to drive convergence.
        # The plan carries mode=DRAFT so callers can detect the
        # cascade is in flight (vs a plain AUTO that should stop at
        # max-iterations).
        iters = iterations if iterations is not None else _DEFAULT_ENUMERATE_ITERATIONS
        cli_args = {
            **common,
            "--auto": True,
            "--max-iterations": str(iters),
        }
        if request.feedback.strip():
            cli_args["--feedback"] = request.feedback.strip()
        return IterateSlidePlan(
            mode=mode_enum,
            run_id=run_id,
            feedback=request.feedback.strip(),
            iterations=iters,
            cli_args=cli_args,
            budget_usd=budget,
        )

    raise ValueError(f"Unknown IterateMode: {mode!r}")


def cli_args_to_argv(args: Mapping) -> list[str]:
    """Convert a CLI args dict to an argv-style list for ``subprocess.run``.

    Boolean True values become bare flag strings. False / None values are
    omitted. Everything else becomes ``[key, str(value)]``.

    Order of insertion is preserved (Python 3.7+ dict ordering), which
    means the dispatch struct's args appear in the CLI in a consistent
    order — useful for diffing log output across runs.
    """
    argv: list[str] = []
    for key, value in args.items():
        if value is True:
            argv.append(key)
        elif value is False or value is None:
            continue
        else:
            argv.append(key)
            argv.append(str(value))
    return argv


def parse_output_path_from_stdout(stdout: str) -> str:
    """Extract the final output PNG path from paperbanana's stdout.

    Paperbanana prints ``Output: <path>`` or ``Output saved to: <path>``
    near the end of a successful run. First match wins.

    Returns:
        The path string when found, or the empty string when not.
        Empty-string return is the bridge's signal to fall back to
        scanning the run directory directly.
    """
    match = _OUTPUT_PATH_PATTERN.search(stdout or "")
    return match.group(1) if match else ""


def ensure_run_dir_local(
    run_id: str,
    source_run_dir_root: str,
    target_outputs_dir: str = "outputs",
) -> str:
    """F7 workaround — ensure paperbanana's run dir is under cwd/outputs/.

    Paperbanana's ``--continue-run`` resolves the run dir against
    ``settings.output_dir`` (default ``outputs/`` relative to cwd), not
    against the path paperbanana originally wrote to or against any
    flag passed at continuation time (verified in the 2026-05-18
    dogfood, F7 finding; upstream issue
    `llmsresearch/paperbanana#217 <https://github.com/llmsresearch/paperbanana/issues/217>`_).

    This helper ensures the run dir lives at
    ``<target_outputs_dir>/<run_id>/`` before the bridge invokes
    continue-run. If it already exists locally (the common path on a
    re-refinement), no-ops. If not, copies the source run dir over.

    Args:
        run_id: paperbanana run id (validated to match the standard
            pattern).
        source_run_dir_root: the directory CONTAINING the source
            ``run_<id>/`` dir. E.g. ``"/tmp"`` if paperbanana wrote
            ``/tmp/run_<id>/``.
        target_outputs_dir: where the local ``outputs/`` lives.
            Default ``"outputs"`` (relative to cwd) matches
            paperbanana's default.

    Returns:
        Absolute path string to the local run directory.

    Raises:
        ValueError: if run_id doesn't match the paperbanana pattern.
        FileNotFoundError: if source_run_dir_root/<run_id>/ doesn't
            exist (and the target also doesn't exist locally).
    """
    if not _RUN_DIR_PATTERN.match(run_id):
        raise ValueError(
            f"run_id doesn't match paperbanana pattern: {run_id!r}"
        )

    target_dir = Path(target_outputs_dir) / run_id
    if target_dir.exists():
        return str(target_dir.resolve())

    source_dir = Path(source_run_dir_root) / run_id
    if not source_dir.exists():
        raise FileNotFoundError(
            f"Source run dir not found: {source_dir}. "
            f"Paperbanana may have written elsewhere; check "
            f"`paperbanana runs list --output-dir <root>` "
            f"to locate the run, then call ensure_run_dir_local with "
            f"the correct source_run_dir_root."
        )

    Path(target_outputs_dir).mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, target_dir)
    return str(target_dir.resolve())


def find_manifest_entry(
    manifest: Mapping,
    slide_number: int,
) -> dict | None:
    """Find the manifest entry for a given slide_number.

    The image-manifest schema carries entries under either ``"entries"``
    or ``"images"`` (different parts of the codebase have used both —
    we accept either). Returns the first matching entry as a fresh
    dict (caller mutation doesn't bleed into the source manifest).

    Returns None when no entry matches.
    """
    entries = manifest.get("entries") or manifest.get("images") or []
    for entry in entries:
        if entry.get("slide_number") == slide_number:
            return dict(entry)
    return None


def update_manifest_entry(
    prior_entry: Mapping,
    new_file_path: str,
    new_content_hash: str,
    *,
    refinement_args: Mapping | None = None,
) -> dict:
    """Build an updated manifest entry after successful refinement.

    Returns a NEW dict (does not mutate the input). Behaviour:

    - ``file_path`` and ``content_hash`` overwritten with the new
      refined values.
    - ``paperbanana_history`` list maintained: first refinement seeds
      it with the original ``paperbanana_args`` under iteration
      ``"initial"``; subsequent refinements append the new args
      under ``"refinement_<N>"``.
    - ``paperbanana_args`` updated to the LATEST refinement's args
      (so the manifest entry's args reflect the current state, while
      the history preserves the full chain).
    - ``refinement_count`` incremented.

    Args:
        prior_entry: the existing manifest entry (probably from
            ``find_manifest_entry``).
        new_file_path: where the refined image was written.
        new_content_hash: sha256 of the refined image.
        refinement_args: the args dict the bridge passed to paperbanana
            for this refinement (extracted from the dispatch plan).
            None means no history update — used when we want to fix
            a path without recording a refinement.

    Returns:
        A new dict ready to write back to the manifest.
    """
    updated = dict(prior_entry)
    updated["file_path"] = new_file_path
    updated["content_hash"] = new_content_hash

    # Only touch the history chain + paperbanana_args when we're recording
    # an actual refinement. refinement_args=None means "fix the path/hash
    # without recording an iteration" — leaves the history untouched.
    if refinement_args is not None:
        history = list(updated.get("paperbanana_history") or [])
        if "paperbanana_args" in updated and not history:
            history.append({
                "iteration": "initial",
                "args": dict(updated["paperbanana_args"]),
            })
        history.append({
            "iteration": f"refinement_{len(history)}",
            "args": dict(refinement_args),
        })
        updated["paperbanana_args"] = dict(refinement_args)
        updated["paperbanana_history"] = history

    updated["refinement_count"] = int(updated.get("refinement_count", 0)) + 1
    return updated
