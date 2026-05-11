#!/usr/bin/env python3
"""Generate an image via Ollama's REST API and save it as PNG.

Issue #75 — Single-flight protection. Ollama's image-generation
backends (z-image-turbo, flux2-klein) serialise on a single GPU
context; parallel API calls don't run in parallel, they queue inside
Ollama. Combined with the per-call 120s timeout, queued calls timeout
while waiting. This module wraps the API call in a process-level
``fcntl.flock`` so multiple concurrent invocations of this script
serialise politely and each call gets its full GPU-time budget once it
acquires the lock. The lock is automatically released by the kernel
on process exit (graceful or crash), so stale lock recovery is not
strictly required — but a defensive 30-minute mtime guard reclaims a
lock if a process held it without updating mtime for that long
(filesystem clock skew, suspended process, etc.).
"""

import argparse
import base64
import errno
import fcntl
import os
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

# Model-aware default timeouts (seconds)
MODEL_TIMEOUTS = {
    "x/z-image-turbo": 120,
    "x/flux2-klein": 600,
}
DEFAULT_TIMEOUT = 300

# Single-flight lock — covers the whole image-generation API call. The
# lock file is at the OS tmpdir so concurrent invocations of this
# script (across processes, terminals, plugins) serialise on a single
# Ollama instance.
LOCK_PATH = Path(tempfile.gettempdir()) / "jack-tar-ollama-image.lock"

DEFAULT_LOCK_WAIT_TIMEOUT = 600  # 10 minutes — covers ~5 sequential 120s renders.
STALE_LOCK_AGE_SECONDS = 1800    # 30 minutes — older than this and we reclaim.


@contextmanager
def _single_flight_lock(timeout_seconds: int):
    """Acquire an exclusive flock on LOCK_PATH, yield, release on exit.

    Issue #75 — protects Ollama's single-GPU-context image API from
    parallel callers queueing internally and timing out waiting. The
    lock is released by the kernel automatically when the file
    descriptor closes (on success, on exception, or on SIGTERM/SIGKILL).

    Stale-lock recovery: if acquisition is still blocked after
    ``STALE_LOCK_AGE_SECONDS`` AND the lock file's mtime is older than
    that, force-reclaim by removing the file and re-trying. Catches
    the rare case where a process held the lock without crashing
    cleanly (suspended, killed -9 with the file still mapped, etc.).

    Raises:
        TimeoutError: lock could not be acquired within ``timeout_seconds``.
    """
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_seconds

    def _open_fd():
        return os.open(str(LOCK_PATH), os.O_CREAT | os.O_RDWR, 0o644)

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
                        f"Could not acquire Ollama single-flight lock at "
                        f"{LOCK_PATH} within {timeout_seconds}s. Another "
                        f"image generation is in progress; serialise your "
                        f"callers or use cloud generation for parallelism."
                    ) from exc

                # Stale-lock recovery: if the lock file is genuinely
                # ancient, reclaim it. The kernel releases fcntl flocks
                # automatically when the holding process dies, so this
                # is only needed for the rare edge case of a long-running
                # suspended process holding the fd. After unlinking, our
                # current fd still points to the old (now-detached)
                # inode; we need a fresh fd on the new path so we can
                # compete on equal footing with future callers.
                try:
                    age = time.time() - LOCK_PATH.stat().st_mtime
                except FileNotFoundError:
                    age = -1.0
                if age > STALE_LOCK_AGE_SECONDS:
                    try:
                        LOCK_PATH.unlink()
                    except FileNotFoundError:
                        pass
                    # Reopen onto the new inode so flock targets the file
                    # the next acquirer will see.
                    try:
                        os.close(fd)
                    except OSError:
                        pass
                    fd = _open_fd()

                time.sleep(1)
        # Touch mtime so stale-lock detection doesn't trip on a long-but-
        # legitimate hold (e.g. flux2-klein at 600s timeout). Best-effort:
        # if the file was unlinked between acquisition and now (rare
        # interleaving), don't fail the whole operation.
        try:
            os.utime(str(LOCK_PATH), None)
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an image via Ollama")
    parser.add_argument("--prompt", required=True, help="Text prompt for image generation")
    parser.add_argument("--model", default="x/z-image-turbo", help="Ollama model identifier")
    parser.add_argument("--output", default=None, help="Output file path (default: output/YYYYMMDD-HHMMSS.png)")
    parser.add_argument("--width", type=int, default=1024, help="Image width in pixels")
    parser.add_argument("--height", type=int, default=1024, help="Image height in pixels")
    parser.add_argument("--steps", type=int, default=8, help="Number of inference steps")
    parser.add_argument("--seed", type=int, default=None, help="Seed for reproducibility")
    parser.add_argument("--timeout", type=int, default=None, help="HTTP timeout in seconds (auto-detected from model if not set)")
    parser.add_argument(
        "--lock-wait-timeout",
        type=int,
        default=DEFAULT_LOCK_WAIT_TIMEOUT,
        help=(
            "Seconds to wait for the Ollama single-flight lock before "
            "giving up. Default 600s (10 min) — covers ~5 sequential "
            "renders on a single GPU. Issue #75."
        ),
    )
    parser.add_argument(
        "--no-lock",
        action="store_true",
        help=(
            "Disable the single-flight lock. Use ONLY when you know "
            "Ollama is being driven by a single caller (debugging, "
            "test fixtures). Default: lock is on. Issue #75."
        ),
    )
    return parser.parse_args()


def resolve_output_path(output: str | None) -> Path:
    if output:
        path = Path(output).resolve()
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = Path(f"output/{timestamp}.png").resolve()
    os.makedirs(path.parent, exist_ok=True)
    return path


def resolve_timeout(model: str, explicit_timeout: int | None) -> int:
    if explicit_timeout is not None:
        return explicit_timeout
    base_model = model.split(":")[0]
    return MODEL_TIMEOUTS.get(base_model, DEFAULT_TIMEOUT)


def _do_api_call(args: argparse.Namespace) -> None:
    """Inner generation logic — assumes the lock has already been acquired."""
    output_path = resolve_output_path(args.output)
    timeout = resolve_timeout(args.model, args.timeout)

    body = {
        "model": args.model,
        "prompt": args.prompt,
        "stream": False,
        "width": args.width,
        "height": args.height,
        "steps": args.steps,
    }
    if args.seed is not None:
        body["seed"] = args.seed

    try:
        resp = requests.post(OLLAMA_URL, json=body, timeout=timeout)
    except requests.ConnectionError:
        print("Ollama is not running. Start it with: ollama serve", file=sys.stderr)
        sys.exit(1)
    except requests.Timeout:
        print(
            f"Generation timed out after {timeout}s. Try reducing --steps or image dimensions.",
            file=sys.stderr,
        )
        sys.exit(1)

    if resp.status_code == 404 or "not found" in resp.text.lower():
        print(f"Model {args.model} not found. Pull it with: ollama pull {args.model}", file=sys.stderr)
        sys.exit(1)

    if resp.status_code != 200:
        print(f"Ollama API error: {resp.status_code} {resp.text[:200]}", file=sys.stderr)
        sys.exit(1)

    if not resp.text or not resp.text.strip():
        print("Ollama returned an empty response. The server may be busy or the request too large.", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    image_b64 = data.get("image")
    if not image_b64:
        print("Ollama returned no image data. The model may not support image generation.", file=sys.stderr)
        sys.exit(1)

    output_path.write_bytes(base64.b64decode(image_b64))
    print(str(output_path))


def generate(args: argparse.Namespace) -> None:
    """Generate an image, holding the single-flight lock across the API call.

    Issue #75 — concurrent invocations of this script against the same
    Ollama instance now serialise on the lock. Pass ``--no-lock`` to
    bypass for legitimate single-caller scenarios (test fixtures,
    debugging).
    """
    if getattr(args, "no_lock", False):
        _do_api_call(args)
        return

    lock_wait = getattr(args, "lock_wait_timeout", DEFAULT_LOCK_WAIT_TIMEOUT)
    try:
        with _single_flight_lock(lock_wait):
            _do_api_call(args)
    except TimeoutError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    generate(parse_args())
