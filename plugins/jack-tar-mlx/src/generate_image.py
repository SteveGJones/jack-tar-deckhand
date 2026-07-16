#!/usr/bin/env python3
"""Generate an image via mflux (MLX) on Apple Silicon and save it as PNG.

Issue #124 — MLX as a second local image-generation provider, alongside
Ollama. This module is a subprocess CLI wrapper (not an in-process call)
mirroring ``jack-tar-ollama/src/generate_image.py``'s shape and error
tone, but dispatching to the ``mflux`` CLI family instead of Ollama's
REST API.

Key design points (see docs/superpowers/plans/2026-07-15-mlx-local-backend.md
§6.3 for the full rationale):

- The wrapper does NOT read the model catalog. It carries its own small
  ``MLX_MODEL_REGISTRY`` mapping catalog ids to dispatch metadata. A
  drift-guard test in this plugin's test suite asserts full per-field
  equality against the vendored deckhand catalog's ``mlx/*`` entries, so
  the two can never silently diverge (review M2).
- The operator installs mflux and pulls/caches weights themselves; this
  wrapper NEVER downloads. Every subprocess call runs with
  ``HF_HUB_OFFLINE=1`` / ``TRANSFORMERS_OFFLINE=1`` so a cache miss fails
  fast instead of pulling multi-GB weights (the *hard* guard, behind the
  *soft* guard of catalog/detection-side snapshot-completeness checks).
- ``--steps`` is ALWAYS present in the constructed argv (review M4d) —
  mflux silently defaults to 25 steps when ``--steps`` is omitted and
  ``--model`` is an HF repo id, a confirmed trap.
- Cross-provider OOM protection (review M5): this wrapper takes the
  OLLAMA single-flight lock FIRST, then its own. A machine's GPU/unified
  memory can only run one local render at a time regardless of which
  provider started it; ordering is deadlock-safe because the ollama
  wrapper only ever takes one lock, so there is exactly one multi-lock
  acquirer.
- ``--check-weights`` prints per-registry-model READY/NOT_READY (with the
  exact ``hf download`` remediation) using the same HF-cache
  snapshot-completeness check the deckhand detection seam uses, so the
  verify skill never re-implements the check in bash (review m17).
"""

import argparse
import errno
import fcntl
import os
import shutil
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

# catalog id -> dispatch metadata. DRIFT-GUARDED: tests assert each value
# dict equals the vendored deckhand catalog entry's derived fields exactly
# (review M2) — entrypoint, hf_repo, hf_repo_fallback, default_steps,
# quantize, timeout (<- capabilities.timeout_seconds) — plus exact
# key-set equality.
MLX_MODEL_REGISTRY = {
    "mlx/flux2-klein-4b": {
        "entrypoint": "mflux-generate-flux2",
        "hf_repo": "Runpod/FLUX.2-klein-4B-mflux-4bit",
        "hf_repo_fallback": "black-forest-labs/FLUX.2-klein-4B",
        "default_steps": 4,
        "quantize": 4,
        "timeout": 300,
    },
    "mlx/z-image-turbo": {
        "entrypoint": "mflux-generate-z-image-turbo",
        "hf_repo": "filipstrand/Z-Image-Turbo-mflux-4bit",
        "hf_repo_fallback": "Tongyi-MAI/Z-Image-Turbo",
        "default_steps": 9,
        "quantize": 4,
        "timeout": 180,
    },
    "mlx/qwen-image": {
        "entrypoint": "mflux-generate-qwen",
        "hf_repo": "filipstrand/Qwen-Image-mflux-6bit",
        "hf_repo_fallback": "Qwen/Qwen-Image",
        "default_steps": 20,
        "quantize": 6,
        "timeout": 900,
    },
}
DEFAULT_MODEL = "mlx/flux2-klein-4b"
DEFAULT_TIMEOUT = 300

# Cross-provider OOM protection (review M5): the mlx wrapper takes the
# OLLAMA lock FIRST, then its own. Ordering is deadlock-safe because the
# ollama wrapper only ever takes one lock.
OLLAMA_LOCK_PATH = Path(tempfile.gettempdir()) / "jack-tar-ollama-image.lock"
LOCK_PATH = Path(tempfile.gettempdir()) / "jack-tar-mlx-image.lock"
DEFAULT_LOCK_WAIT_TIMEOUT = 600     # mirror issue #75
STALE_LOCK_AGE_SECONDS = 1800       # mirror issue #75


@contextmanager
def _single_flight_lock(lock_path: Path, timeout_seconds: float):
    """Acquire an exclusive flock on ``lock_path``, yield, release on exit.

    Parameterised copy of the ollama wrapper's ``_single_flight_lock``
    (issue #75) — same stale-lock reclaim behaviour, but keyed by an
    explicit path so this module can nest two independent locks (review
    M5: the ollama lock, then this module's own).

    Raises:
        TimeoutError: lock could not be acquired within ``timeout_seconds``.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_seconds

    def _open_fd():
        return os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o644)

    fd = _open_fd()
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break  # acquired
            except (BlockingIOError, OSError) as exc:
                if isinstance(exc, OSError) and exc.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
                    raise

                if time.monotonic() > deadline:
                    raise TimeoutError(
                        f"Could not acquire MLX single-flight lock at "
                        f"{lock_path} within {timeout_seconds}s. Another "
                        f"local image generation is in progress; serialise "
                        f"your callers or use cloud generation for "
                        f"parallelism."
                    ) from exc

                try:
                    age = time.time() - lock_path.stat().st_mtime
                except FileNotFoundError:
                    age = -1.0
                if age > STALE_LOCK_AGE_SECONDS:
                    try:
                        lock_path.unlink()
                    except FileNotFoundError:
                        pass
                    try:
                        os.close(fd)
                    except OSError:
                        pass
                    fd = _open_fd()

                time.sleep(1)
        try:
            os.utime(str(lock_path), None)
        except OSError:
            pass
        yield fd
    finally:
        if fd is not None:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
            try:
                os.close(fd)
            except OSError:
                pass


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an image via mflux (MLX) — local Apple Silicon backend"
    )
    parser.add_argument("--prompt", default=None, help="Text prompt for image generation (required unless --check-weights)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Catalog model id (e.g. mlx/flux2-klein-4b)")
    parser.add_argument("--output", default=None, help="Output file path (default: output/YYYYMMDD-HHMMSS.png)")
    parser.add_argument("--width", type=int, default=1024, help="Image width in pixels")
    parser.add_argument("--height", type=int, default=1024, help="Image height in pixels")
    parser.add_argument("--steps", type=int, default=None, help="Inference steps (default: registry default_steps)")
    parser.add_argument("--seed", type=int, default=None, help="Seed for reproducibility")
    parser.add_argument("--timeout", type=int, default=None, help="Subprocess timeout (default: auto from --model)")
    parser.add_argument(
        "--lock-wait-timeout",
        type=int,
        default=DEFAULT_LOCK_WAIT_TIMEOUT,
        help=(
            "Seconds to wait for the local single-flight locks before "
            "giving up. Default 600s (10 min); shared as a single "
            "deadline across BOTH the ollama and mlx locks. Issue #124/#75."
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
        "--check-weights",
        action="store_true",
        help=(
            "Print per-registry-model READY/NOT_READY (with the exact "
            "'hf download' remediation) and exit — no render, no --prompt "
            "required."
        ),
    )
    args = parser.parse_args(argv)
    if not args.check_weights and not args.prompt:
        parser.error("--prompt is required unless --check-weights is set")
    return args


def resolve_output_path(output: str | None) -> Path:
    if output:
        path = Path(output).resolve()
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = Path(f"output/{timestamp}.png").resolve()
    os.makedirs(path.parent, exist_ok=True)
    return path


def resolve_model(model_id: str) -> dict:
    """Look up ``model_id`` in ``MLX_MODEL_REGISTRY``.

    Unknown id -> exit 1 with the known-ids list (mirrors the catalog's
    UnknownModelError shape).
    """
    meta = MLX_MODEL_REGISTRY.get(model_id)
    if meta is None:
        known = ", ".join(sorted(MLX_MODEL_REGISTRY))
        print(f"Unknown MLX model '{model_id}'. Known models: {known}", file=sys.stderr)
        sys.exit(1)
    return meta


def resolve_timeout(meta: dict, explicit_timeout: int | None) -> int:
    if explicit_timeout is not None:
        return explicit_timeout
    return meta.get("timeout", DEFAULT_TIMEOUT)


def _repo_prequantized(repo_id: str) -> bool:
    """True for community pre-quantized exports ('-mflux-' naming convention)."""
    return "-mflux-" in repo_id


def _metadata_sidecar_path(output_path: Path) -> Path:
    """mflux writes its --metadata JSON sidecar at <stem>.metadata.json."""
    return output_path.with_suffix(".metadata.json")


def _build_argv(meta, repo, prompt, width, height, steps, seed, quantize, output_path) -> list[str]:
    """Construct the mflux CLI argv for one render attempt against ``repo``.

    ``--steps`` is ALWAYS present (review M4d) — mflux silently defaults
    to 25 steps when omitted and ``--model`` is an HF repo id. ``-q`` is
    emitted ONLY when ``repo`` is full-precision (review m13) — a
    pre-quantized primary never gets ``-q``, but a full-precision
    fallback (or full-precision primary) gets ``-q <bits>`` where bits is
    the explicit ``--quantize`` if given, else the registry's quantize.
    """
    resolved_steps = steps if steps is not None else meta["default_steps"]
    argv = [
        meta["entrypoint"],
        "--model", repo,
        "--prompt", prompt,
        "--width", str(width),
        "--height", str(height),
        "--steps", str(resolved_steps),
        "--output", str(output_path),
        "--metadata",
    ]
    if seed is not None:
        argv += ["--seed", str(seed)]
    if not _repo_prequantized(repo):
        q = quantize if quantize is not None else meta["quantize"]
        if q is not None:
            argv += ["-q", str(q)]
    return argv


def _cleanup_partial_output(output_path: Path) -> None:
    """Unlink a partial PNG + metadata sidecar left by a killed/failed run.

    Review m14 — on ANY non-success exit (timeout, non-zero return code,
    or an exception after the subprocess started), the wrapper removes
    both files so downstream steps never mistake a partial render for a
    complete one.
    """
    for path in (output_path, _metadata_sidecar_path(output_path)):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass


def _weights_missing(stderr_text: str) -> bool:
    lowered = stderr_text.lower()
    return any(sig in lowered for sig in ("localentrynotfound", "offline", "can't load"))


def _oom_signature(stderr_text: str) -> bool:
    lowered = stderr_text.lower()
    return any(sig in lowered for sig in ("metal", "out of memory", "mtlbuffer", "bad_alloc"))


def _do_render(args: argparse.Namespace) -> None:
    """Inner render logic — assumes both locks (if any) are already held."""
    meta = resolve_model(args.model)
    entrypoint = meta["entrypoint"]

    if shutil.which(entrypoint) is None:
        print(
            f"mflux not installed (or too old — {args.model} needs the "
            f"'{entrypoint}' entry point) — run: uv tool install --upgrade mflux",
            file=sys.stderr,
        )
        sys.exit(1)

    output_path = resolve_output_path(args.output)
    timeout_seconds = resolve_timeout(meta, args.timeout)

    # Refusal-to-download guard: forces the HF stack offline so a cache
    # miss fails fast instead of pulling multi-GB weights. This is the
    # *hard* guard behind detection's *soft* snapshot-completeness guard.
    env = {**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}

    repos = [meta["hf_repo"]]
    if meta.get("hf_repo_fallback"):
        repos.append(meta["hf_repo_fallback"])

    last_result = None
    for index, repo in enumerate(repos):
        argv = _build_argv(
            meta, repo, args.prompt, args.width, args.height,
            args.steps, args.seed, args.quantize, output_path,
        )
        try:
            last_result = subprocess.run(
                argv, env=env, timeout=timeout_seconds, capture_output=True, text=True,
            )
        except subprocess.TimeoutExpired:
            _cleanup_partial_output(output_path)
            print(
                f"Generation timed out after {timeout_seconds}s. "
                f"Try a smaller model or fewer --steps.",
                file=sys.stderr,
            )
            sys.exit(1)

        if last_result.returncode == 0:
            # Review m19 — report the actually-loaded repo (primary or
            # fallback) so the bridge can keep manifest repo fidelity.
            print(f"MFLUX_REPO_USED={repo}", file=sys.stderr)
            # Exact ollama contract: print the output path as the last
            # stdout line so the bridge's OUT_PNG-based flow is unchanged.
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
    print(f"mflux error (exit {rc}): {stderr_text[:200]}", file=sys.stderr)
    sys.exit(1)


def generate(args: argparse.Namespace) -> None:
    """Generate an image, holding the nested single-flight locks (review M5).

    Acquires the OLLAMA lock first, then this module's own lock, so an
    mflux render can never run concurrently with an Ollama render on a
    single-GPU/unified-memory machine. Deadlock-safe: the ollama wrapper
    only ever takes one lock, so there is exactly one multi-lock acquirer
    and one global acquisition order.

    ``--lock-wait-timeout`` is a SINGLE deadline shared across both
    acquisitions. ``--no-lock`` skips both locks entirely.
    """
    if getattr(args, "no_lock", False):
        _do_render(args)
        return

    lock_wait = getattr(args, "lock_wait_timeout", DEFAULT_LOCK_WAIT_TIMEOUT)
    deadline = time.monotonic() + lock_wait
    try:
        with _single_flight_lock(OLLAMA_LOCK_PATH, lock_wait):
            remaining = max(0.0, deadline - time.monotonic())
            with _single_flight_lock(LOCK_PATH, remaining):
                _do_render(args)
    except TimeoutError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


# --- --check-weights support -------------------------------------------
#
# Review OQ-C: the HF-cache snapshot-completeness helper now lives in
# three Python spots (paperbanana_dispatch.py detection, model_probe.py
# discovery, and here) — a considered duplication rather than a fourth
# vendored artifact (review m17: the verify skill must not re-implement
# the check in bash, so the wrapper needs its own copy).

def _resolve_hf_hub_dir(hf_home: str | os.PathLike | None = None) -> Path:
    """HF hub cache dir per huggingface_hub precedence (review m7):
    explicit arg (root; hub is <arg>/hub) > $HF_HUB_CACHE (IS the hub dir)
    > $HF_HOME/hub > ~/.cache/huggingface/hub."""
    if hf_home is not None:
        return Path(hf_home) / "hub"
    env_cache = os.environ.get("HF_HUB_CACHE")
    if env_cache:
        return Path(env_cache)
    env_home = os.environ.get("HF_HOME")
    if env_home:
        return Path(env_home) / "hub"
    return Path.home() / ".cache" / "huggingface" / "hub"


def _hf_snapshot_complete(repo_id: str, hub_dir: Path) -> bool:
    """True when ``repo_id`` has a complete HF-cache snapshot under hub_dir.

    Mirrors the deckhand detection seam's completeness predicate: resolve
    the revision via refs/main when present (else newest-by-mtime
    snapshot dir), then require every symlink in that revision to resolve
    with no dangling target. Any doubt returns False (false-negative-safe
    — under-report rather than trigger a download). Any OSError -> False.
    """
    try:
        repo_dir = hub_dir / ("models--" + repo_id.replace("/", "--"))
        if not repo_dir.is_dir():
            return False

        snapshots_dir = repo_dir / "snapshots"
        if not snapshots_dir.is_dir():
            return False

        revision_dir = None
        refs_main = repo_dir / "refs" / "main"
        if refs_main.is_file():
            try:
                revision = refs_main.read_text().strip()
            except OSError:
                revision = ""
            if revision:
                candidate = snapshots_dir / revision
                if candidate.is_dir():
                    revision_dir = candidate

        if revision_dir is None:
            candidates = [p for p in snapshots_dir.iterdir() if p.is_dir()]
            if not candidates:
                return False
            revision_dir = max(candidates, key=lambda p: p.stat().st_mtime)

        entries = list(revision_dir.iterdir())
        if not entries:
            return False

        for entry in entries:
            if entry.is_symlink():
                target = entry.resolve()
                if not target.exists():
                    return False
                if Path(str(target) + ".incomplete").exists():
                    return False
        return True
    except OSError:
        return False


def check_weights() -> None:
    """Print per-registry-model READY / NOT_READY, no render (review m17)."""
    hub_dir = _resolve_hf_hub_dir()
    for model_id, meta in MLX_MODEL_REGISTRY.items():
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
    generate(args)


if __name__ == "__main__":
    main()
