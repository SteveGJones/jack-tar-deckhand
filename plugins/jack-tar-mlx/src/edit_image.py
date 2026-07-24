#!/usr/bin/env python3
"""Edit an image via mflux (MLX) on Apple Silicon — targeted local edit.

Issue #143 — the edit tier: a $0 local action that takes a base image +
an instruction and preserves everything the instruction does not name,
instead of regenerating the whole image from scratch. Design doc:
docs/superpowers/plans/2026-07-23-edit-tier.md.

This module is a SIBLING to ``generate_image.py``, not a mode flag on
it (design D1/D3) — the edit argv shape differs materially (one-or-more
``--image-paths`` reference images, a distinct entrypoint per family,
distinct provenance semantics), and folding it into ``generate_image.py``
would thread ``if edit:`` conditionals through the plugin's most heavily
reviewed, drift-guarded file.

**Import form (design F-01):** ``plugins/jack-tar-mlx/src/`` has no
``__init__.py``, the ``/image-edit`` skill invokes this module as a
script, and the plugin's tests import flat via ``sys.path.insert`` — so
a relative ``from .generate_image import ...`` is unrunnable. This
module therefore imports the shared helpers FLAT (resolves via the
script's own directory on ``sys.path`` in script mode, and via the test
suite's existing ``sys.path.insert`` in test mode). The ONLY change made
to ``generate_image.py`` for the edit tier is the additive
``edit_entrypoint``/``edit_steps`` keys on ``MLX_MODEL_REGISTRY`` (T2) —
this module makes zero edits to the generate render path.

Key design points (see the design doc §3.1-§3.3 for the full rationale):

- **No ``--width``/``--height`` flags, EVER (S7 ruling).** The edit CLI
  inherits the SOURCE image's dimensions when dims flags are omitted
  (confirmed exact by the 2026-07-23 smoke, 1408x768 -> 1408x768).
  Explicit dims DIFFERING from the base are a reproducible mflux hang
  (>10 min, stalls at step 1/4, leaked semaphore, no output) — a
  documented non-feature, not a wrapper bug to route around. This
  wrapper therefore never emits dims flags and does not even define
  ``--width``/``--height`` as arguments — passing them is rejected by
  argparse as unknown flags.
- **Seed always resolved and recorded (F-08).** The 2026-07-23 smoke
  (S3) proved an unseeded edit leaves ZERO trace of its seed anywhere
  (stdout, stderr, and the ``--metadata`` sidecar are all silent/null).
  When ``--seed`` is omitted this wrapper generates one and ALWAYS
  reports the resolved seed (generated or caller-supplied) on stderr as
  ``MFLUX_SEED_USED=<n>`` — sibling to ``MFLUX_REPO_USED`` — so a caller
  building manifest provenance (PR D's ``edit_chain``) can always
  recover the seed that actually ran, regardless of which path supplied
  it.
- **Text-correction edits are NOT gated by this wrapper (D9).** S1 showed
  the simplest word-for-word edit re-garbles in-image text
  ("NOTICE" -> "NOBTICE"). That routing decision lives in the CALLER
  (``iterate_slide``/creative_vision's ``classify_edit_locality``, PR D)
  — this wrapper will happily run whatever instruction it is given; it
  is not itself a content classifier.
- **``--steps`` is ALWAYS present** in the constructed argv (the same
  mlux silent-step-default trap the generate wrapper guards against).
- **Nested single-flight lock, SAME paths and order as generate**
  (ollama lock, then the mlx lock) — reuses ``generate_image``'s lock
  primitive and path constants directly, so an edit correctly queues
  against a running generate (either provider) and vice versa.
- **``HF_HUB_OFFLINE=1``/``TRANSFORMERS_OFFLINE=1``** hard guard on the
  subprocess — an edit never triggers a download. Edits reuse the
  ALREADY-cached generate weights for the same catalog model id (PoC
  fact); there is no separate edit weight set.
"""

import argparse
import os
import random
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Flat import (F-01) — see module docstring. All 12 names verified to
# exist at generate_image.py module scope with the claimed semantics
# (design §3.1). This is the ONLY coupling to generate_image.py; no
# generate render-path code is touched by this module.
from generate_image import (
    _single_flight_lock, OLLAMA_LOCK_PATH, LOCK_PATH,
    DEFAULT_LOCK_WAIT_TIMEOUT, STALE_LOCK_AGE_SECONDS,
    _resolve_hf_hub_dir, _hf_snapshot_complete,
    _cleanup_partial_output, _weights_missing, _oom_signature,
    _repo_prequantized, MLX_MODEL_REGISTRY,
)

DEFAULT_MODEL = "mlx/flux2-klein-4b"
DEFAULT_GUIDANCE = 3.5  # S2 sweep: optimal-strong default; 1.5 subtle; avoid >6


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Edit an image via mflux (MLX) — targeted local edit, $0"
    )
    parser.add_argument("--prompt", default=None, help="Edit instruction (required unless --check-weights)")
    parser.add_argument(
        "--image-paths",
        nargs="+",
        default=None,
        metavar="PATH",
        help=(
            "Base image, optionally followed by one or more reference "
            "images (required unless --check-weights; at least one path). "
            "A second+ reference strongly influences the edit (element "
            "transfer, not just style pull) — scope the instruction "
            "tightly and watch for reference-content leakage."
        ),
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help="Catalog model id — must be image_edit-capable (default: mlx/flux2-klein-4b)",
    )
    parser.add_argument("--output", default=None, help="Output file path (default: output/YYYYMMDD-HHMMSS.png)")
    parser.add_argument("--steps", type=int, default=None, help="Inference steps (default: registry edit_steps)")
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Seed for reproducibility (default: wrapper generates one and reports it via MFLUX_SEED_USED)",
    )
    parser.add_argument(
        "--guidance", type=float, default=DEFAULT_GUIDANCE,
        help="Edit strength (default 3.5 = optimal-strong; 1.5 = subtle; quality cliff 3.5-6; avoid >6)",
    )
    parser.add_argument("--timeout", type=int, default=None, help="Subprocess timeout (default: auto from --model)")
    parser.add_argument(
        "--quantize", "-q",
        type=int,
        default=None,
        help=(
            "On-load quantization bits (documented mflux values: 3, 4, 5, "
            "6, 8). Only applied when the resolved repo is full-precision "
            "— never emitted for a pre-quantized '-mflux-' repo. Defaults "
            "to the registry's quantize value for --model."
        ),
    )
    parser.add_argument(
        "--lock-wait-timeout",
        type=int,
        default=DEFAULT_LOCK_WAIT_TIMEOUT,
        help=(
            "Seconds to wait for the local single-flight locks before "
            "giving up. Default 600s (10 min); shared as a single "
            "deadline across BOTH the ollama and mlx locks."
        ),
    )
    parser.add_argument(
        "--no-lock",
        action="store_true",
        help=(
            "Disable both single-flight locks (ollama + mlx). Use ONLY "
            "when you know local image generation is single-caller "
            "(debugging, test fixtures)."
        ),
    )
    parser.add_argument(
        "--check-weights",
        action="store_true",
        help=(
            "Print per-edit-capable-model READY/NOT_READY (with the "
            "exact 'hf download' remediation) and exit — no edit, no "
            "--prompt/--image-paths required."
        ),
    )
    args = parser.parse_args(argv)
    if not args.check_weights:
        if not args.prompt:
            parser.error("--prompt is required unless --check-weights is set")
        if not args.image_paths:
            parser.error("--image-paths is required (at least one base image) unless --check-weights is set")
    return args


def resolve_output_path(output: str | None) -> Path:
    if output:
        path = Path(output).resolve()
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = Path(f"output/{timestamp}.png").resolve()
    os.makedirs(path.parent, exist_ok=True)
    return path


def _resolve_edit_meta(model_id: str) -> dict:
    """Look up ``model_id`` in ``MLX_MODEL_REGISTRY`` and verify it is
    edit-capable. Unknown id or non-edit-capable model -> exit 1."""
    meta = MLX_MODEL_REGISTRY.get(model_id)
    if meta is None:
        known = ", ".join(sorted(MLX_MODEL_REGISTRY))
        print(f"Unknown MLX model '{model_id}'. Known models: {known}", file=sys.stderr)
        sys.exit(1)
    if not meta.get("edit_entrypoint"):
        edit_capable = ", ".join(
            sorted(k for k, v in MLX_MODEL_REGISTRY.items() if v.get("edit_entrypoint"))
        )
        print(
            f"model {model_id} is not edit-capable; edit-capable models: {edit_capable}",
            file=sys.stderr,
        )
        sys.exit(1)
    return meta


def _build_edit_argv(meta, repo, prompt, image_paths,
                      steps, seed, guidance, quantize, output_path) -> list[str]:
    """Construct the mflux edit CLI argv for one attempt against ``repo``.

    ``--steps`` is ALWAYS present (same silent-25-steps trap the generate
    path guards against). NO ``--width``/``--height``, EVER (S7 ruling) —
    the edit always inherits the base image's dimensions; that behaviour
    is achieved by never emitting the flags, not by reading the base's
    pixel dimensions and passing them through. ``--seed`` is ALWAYS
    present — the caller (``_do_edit``) has already resolved a concrete
    seed (explicit or generated) by the time this is called (F-08).
    """
    resolved_steps = steps if steps is not None else meta["edit_steps"]
    argv = [meta["edit_entrypoint"], "--model", repo, "--prompt", prompt]
    argv += ["--image-paths", *image_paths]          # required-and-plural (F-07)
    argv += ["--steps", str(resolved_steps),
             "--output", str(output_path), "--metadata"]
    argv += ["--seed", str(seed)]                    # F-08: always resolved by the caller
    if guidance is not None:                         # default 3.5 optimal (S2)
        argv += ["--guidance", str(guidance)]
    if not _repo_prequantized(repo):
        q = quantize if quantize is not None else meta["quantize"]
        if q is not None:
            argv += ["-q", str(q)]
    return argv


def _do_edit(args: argparse.Namespace) -> None:
    """Inner edit logic — assumes both locks (if any) are already held."""
    meta = _resolve_edit_meta(args.model)
    entrypoint = meta["edit_entrypoint"]

    if shutil.which(entrypoint) is None:
        print(
            f"mflux edit entry point '{entrypoint}' not found (model {args.model} "
            f"needs it) — run: uv tool install --upgrade mflux",
            file=sys.stderr,
        )
        sys.exit(1)

    # Input validation: every --image-paths entry must exist. Missing
    # base -> exit 1, no fall-through to a from-scratch generate.
    for image_path in args.image_paths:
        if not Path(image_path).is_file():
            print(f"edit base image not found: {image_path}", file=sys.stderr)
            sys.exit(1)

    output_path = resolve_output_path(args.output)
    timeout_seconds = args.timeout if args.timeout is not None else meta["timeout"]

    # F-08: the seed is ALWAYS resolved before dispatch, whether
    # caller-supplied or generated here — the S3 smoke proved an
    # unseeded edit is otherwise unrecoverable (no trace anywhere).
    seed = args.seed if args.seed is not None else random.randrange(2**32)

    # Refusal-to-download guard — identical to generate.
    env = {**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}

    repos = [meta["hf_repo"]]
    if meta.get("hf_repo_fallback"):
        repos.append(meta["hf_repo_fallback"])

    last_result = None
    for index, repo in enumerate(repos):
        argv = _build_edit_argv(
            meta, repo, args.prompt, args.image_paths,
            args.steps, seed, args.guidance, args.quantize, output_path,
        )
        try:
            last_result = subprocess.run(
                argv, env=env, timeout=timeout_seconds, capture_output=True, text=True,
            )
        except subprocess.TimeoutExpired:
            _cleanup_partial_output(output_path)
            print(
                f"Edit timed out after {timeout_seconds}s. "
                f"Try a smaller model or fewer --steps.",
                file=sys.stderr,
            )
            sys.exit(1)

        if last_result.returncode == 0:
            # Same contract as generate: repo used on stderr, output path
            # as the last stdout line. Seed is ALWAYS reported too (F-08)
            # so a caller building edit_chain provenance never has to
            # guess whether the seed was caller-supplied or generated.
            print(f"MFLUX_REPO_USED={repo}", file=sys.stderr)
            print(f"MFLUX_SEED_USED={seed}", file=sys.stderr)
            print(str(output_path))
            return

        stderr_text = last_result.stderr or ""
        is_last_repo = index == len(repos) - 1
        if _weights_missing(stderr_text) and not is_last_repo:
            continue  # retry once with the fallback repo
        break

    _cleanup_partial_output(output_path)
    stderr_text = (last_result.stderr or "") if last_result is not None else ""

    if _weights_missing(stderr_text):
        print(
            f"weights for {args.model} not cached — run: hf download {meta['hf_repo']}",
            file=sys.stderr,
        )
        sys.exit(1)
    if _oom_signature(stderr_text):
        print(
            f"{args.model} may exceed available RAM — try a smaller model "
            f"or higher quantization (-q 4).",
            file=sys.stderr,
        )
        sys.exit(1)

    rc = last_result.returncode if last_result is not None else 1
    # Tail, not head — the exception line of a Python traceback is last.
    print(f"mflux edit error (exit {rc}): {stderr_text[-500:]}", file=sys.stderr)
    sys.exit(1)


def edit(args: argparse.Namespace) -> None:
    """Edit an image, holding the nested single-flight locks.

    Reuses generate_image's lock primitive AND its lock path constants
    directly (imported, not redefined) — an mflux edit therefore queues
    against a running generate (either provider) and vice versa, exactly
    like two concurrent generates would. ``--lock-wait-timeout`` is a
    single deadline shared across both acquisitions; ``--no-lock`` skips
    both.
    """
    if getattr(args, "no_lock", False):
        _do_edit(args)
        return

    lock_wait = getattr(args, "lock_wait_timeout", DEFAULT_LOCK_WAIT_TIMEOUT)
    deadline = time.monotonic() + lock_wait
    try:
        with _single_flight_lock(OLLAMA_LOCK_PATH, lock_wait):
            remaining = max(0.0, deadline - time.monotonic())
            with _single_flight_lock(LOCK_PATH, remaining):
                _do_edit(args)
    except TimeoutError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


def check_weights() -> None:
    """Print per-edit-capable-model READY / NOT_READY, no edit run.

    Edit reuses the SAME cached weights as generate for a given catalog
    model id (PoC fact) — so this is the same snapshot-completeness
    check as generate_image.py's --check-weights, scoped to only the
    entries this module can actually dispatch an edit to.
    """
    hub_dir = _resolve_hf_hub_dir()
    edit_capable = {
        model_id: meta for model_id, meta in MLX_MODEL_REGISTRY.items()
        if meta.get("edit_entrypoint")
    }
    for model_id, meta in edit_capable.items():
        primary = meta["hf_repo"]
        fallback = meta.get("hf_repo_fallback")

        if _hf_snapshot_complete(primary, hub_dir):
            print(f"{model_id}: READY ({primary})")
        elif fallback and _hf_snapshot_complete(fallback, hub_dir):
            print(f"{model_id}: READY ({fallback})")
        else:
            print(f"{model_id}: NOT_READY (run: hf download {primary})")


def main(argv=None) -> None:
    args = parse_args(argv)
    if args.check_weights:
        check_weights()
        return
    edit(args)


if __name__ == "__main__":
    main()
