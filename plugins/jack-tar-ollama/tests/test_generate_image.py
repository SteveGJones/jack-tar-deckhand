"""Tests for src/generate_image.py — all HTTP calls mocked."""

import base64
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

# Add src to path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import generate_image  # noqa: E402

FAKE_IMAGE_DATA = b"\x89PNG\r\n\x1a\nfake image data"
FAKE_IMAGE_B64 = base64.b64encode(FAKE_IMAGE_DATA).decode()


def mock_response(status_code=200, json_data=None, text=None):
    """Create a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text if text is not None else (json.dumps(json_data) if json_data else "")
    resp.json.return_value = json_data or {}
    return resp


def make_args(**overrides):
    """Create a Namespace with defaults, overriding as needed."""
    defaults = {
        "prompt": "a cat",
        "model": "x/z-image-turbo",
        "output": None,
        "width": 1024,
        "height": 1024,
        "steps": 8,
        "seed": None,
        "timeout": None,
        # Issue #75 — single-flight lock kwargs.
        "lock_wait_timeout": generate_image.DEFAULT_LOCK_WAIT_TIMEOUT,
        "no_lock": True,  # default to no-lock for fast unit tests
    }
    defaults.update(overrides)
    import argparse
    return argparse.Namespace(**defaults)


class TestHappyPath:
    def test_generates_image_and_prints_path(self, tmp_path, capsys):
        output = tmp_path / "test.png"
        args = make_args(output=str(output))
        with patch("generate_image.requests.post", return_value=mock_response(
            json_data={"done": True, "image": FAKE_IMAGE_B64}
        )):
            generate_image.generate(args)

        captured = capsys.readouterr()
        assert str(output) in captured.out.strip()
        assert output.exists()
        assert output.read_bytes() == FAKE_IMAGE_DATA

    def test_creates_output_directory(self, tmp_path, capsys):
        output = tmp_path / "nested" / "dir" / "image.png"
        args = make_args(output=str(output))
        with patch("generate_image.requests.post", return_value=mock_response(
            json_data={"done": True, "image": FAKE_IMAGE_B64}
        )):
            generate_image.generate(args)

        assert output.exists()

    def test_default_output_path_uses_timestamp(self, tmp_path, capsys, monkeypatch):
        monkeypatch.chdir(tmp_path)
        args = make_args(output=None)
        with patch("generate_image.requests.post", return_value=mock_response(
            json_data={"done": True, "image": FAKE_IMAGE_B64}
        )):
            generate_image.generate(args)

        captured = capsys.readouterr()
        path = captured.out.strip()
        assert "output" in path
        assert path.endswith(".png")


class TestSeedHandling:
    def test_seed_included_in_request(self, tmp_path):
        output = tmp_path / "test.png"
        args = make_args(output=str(output), seed=42)
        with patch("generate_image.requests.post", return_value=mock_response(
            json_data={"done": True, "image": FAKE_IMAGE_B64}
        )) as mock_post:
            generate_image.generate(args)

        body = mock_post.call_args.kwargs["json"]
        assert body["seed"] == 42

    def test_seed_omitted_when_not_provided(self, tmp_path):
        output = tmp_path / "test.png"
        args = make_args(output=str(output), seed=None)
        with patch("generate_image.requests.post", return_value=mock_response(
            json_data={"done": True, "image": FAKE_IMAGE_B64}
        )) as mock_post:
            generate_image.generate(args)

        body = mock_post.call_args.kwargs["json"]
        assert "seed" not in body


class TestErrorHandling:
    def test_connection_refused(self, tmp_path):
        output = tmp_path / "test.png"
        args = make_args(output=str(output))
        with patch("generate_image.requests.post", side_effect=requests.ConnectionError("refused")):
            with pytest.raises(SystemExit) as exc_info:
                generate_image.generate(args)
        assert exc_info.value.code == 1

    def test_model_not_found_404(self, tmp_path, capsys):
        output = tmp_path / "test.png"
        args = make_args(output=str(output), model="x/fake-model")
        with patch("generate_image.requests.post", return_value=mock_response(
            status_code=404, text="model 'x/fake-model' not found"
        )):
            with pytest.raises(SystemExit) as exc_info:
                generate_image.generate(args)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()
        assert "ollama pull" in captured.err

    def test_timeout(self, tmp_path):
        output = tmp_path / "test.png"
        args = make_args(output=str(output))
        with patch("generate_image.requests.post", side_effect=requests.Timeout("timed out")):
            with pytest.raises(SystemExit) as exc_info:
                generate_image.generate(args)
        assert exc_info.value.code == 1

    def test_empty_image_data(self, tmp_path, capsys):
        output = tmp_path / "test.png"
        args = make_args(output=str(output))
        with patch("generate_image.requests.post", return_value=mock_response(
            json_data={"done": True}
        )):
            with pytest.raises(SystemExit) as exc_info:
                generate_image.generate(args)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "no image data" in captured.err.lower()

    def test_other_http_error(self, tmp_path, capsys):
        output = tmp_path / "test.png"
        args = make_args(output=str(output))
        with patch("generate_image.requests.post", return_value=mock_response(
            status_code=500, text="internal server error"
        )):
            with pytest.raises(SystemExit) as exc_info:
                generate_image.generate(args)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "500" in captured.err


class TestTimeoutResolution:
    def test_z_image_turbo_gets_120s(self):
        assert generate_image.resolve_timeout("x/z-image-turbo", None) == 120

    def test_z_image_turbo_with_tag_gets_120s(self):
        assert generate_image.resolve_timeout("x/z-image-turbo:fp8", None) == 120

    def test_flux_gets_600s(self):
        assert generate_image.resolve_timeout("x/flux2-klein", None) == 600

    def test_flux_with_tag_gets_600s(self):
        assert generate_image.resolve_timeout("x/flux2-klein:9b", None) == 600

    def test_unknown_model_gets_default_300s(self):
        assert generate_image.resolve_timeout("x/some-new-model", None) == 300

    def test_explicit_timeout_overrides_model_default(self):
        assert generate_image.resolve_timeout("x/z-image-turbo", 60) == 60


class TestArgumentParsing:
    def test_custom_dimensions_and_steps(self, tmp_path):
        output = tmp_path / "test.png"
        args = make_args(output=str(output), width=512, height=768, steps=20)
        with patch("generate_image.requests.post", return_value=mock_response(
            json_data={"done": True, "image": FAKE_IMAGE_B64}
        )) as mock_post:
            generate_image.generate(args)

        body = mock_post.call_args.kwargs["json"]
        assert body["width"] == 512
        assert body["height"] == 768
        assert body["steps"] == 20

    def test_model_passed_to_request(self, tmp_path):
        output = tmp_path / "test.png"
        args = make_args(output=str(output), model="x/flux2-klein")
        with patch("generate_image.requests.post", return_value=mock_response(
            json_data={"done": True, "image": FAKE_IMAGE_B64}
        )) as mock_post:
            generate_image.generate(args)

        body = mock_post.call_args.kwargs["json"]
        assert body["model"] == "x/flux2-klein"


class TestSingleFlightLock:
    """Issue #75 — Ollama image gen serialises on a single GPU context.
    Concurrent invocations queue inside Ollama and timeout. The
    single-flight lock makes parallel callers serialise politely on the
    process side so each call gets its full GPU-time budget once it
    acquires the lock."""

    def test_no_lock_flag_skips_lock_machinery(self, tmp_path):
        """--no-lock bypasses _single_flight_lock entirely. Used by test
        fixtures and operator-driven debug sessions."""
        output = tmp_path / "test.png"
        args = make_args(output=str(output), no_lock=True)

        with patch("generate_image._single_flight_lock") as mock_lock, \
             patch("generate_image.requests.post", return_value=mock_response(
                 json_data={"done": True, "image": FAKE_IMAGE_B64}
             )):
            generate_image.generate(args)

        mock_lock.assert_not_called()
        assert output.exists()

    def test_default_invocation_acquires_and_releases_lock(self, tmp_path):
        """When --no-lock is NOT set, the API call is wrapped in the
        single-flight context manager."""
        output = tmp_path / "test.png"
        args = make_args(output=str(output), no_lock=False)

        # Patch the context manager to record entry/exit but otherwise
        # behave as a no-op so the inner _do_api_call still runs.
        from contextlib import contextmanager
        events = []

        @contextmanager
        def fake_lock(timeout_seconds):
            events.append(("acquire", timeout_seconds))
            try:
                yield 0
            finally:
                events.append(("release", None))

        with patch("generate_image._single_flight_lock", fake_lock), \
             patch("generate_image.requests.post", return_value=mock_response(
                 json_data={"done": True, "image": FAKE_IMAGE_B64}
             )):
            generate_image.generate(args)

        kinds = [e[0] for e in events]
        assert kinds == ["acquire", "release"]
        # Default timeout was passed through.
        assert events[0][1] == generate_image.DEFAULT_LOCK_WAIT_TIMEOUT

    def test_lock_wait_timeout_propagates(self, tmp_path):
        """A custom --lock-wait-timeout is honoured by the lock context."""
        output = tmp_path / "test.png"
        args = make_args(output=str(output), no_lock=False, lock_wait_timeout=42)

        from contextlib import contextmanager
        captured = []

        @contextmanager
        def fake_lock(timeout_seconds):
            captured.append(timeout_seconds)
            yield 0

        with patch("generate_image._single_flight_lock", fake_lock), \
             patch("generate_image.requests.post", return_value=mock_response(
                 json_data={"done": True, "image": FAKE_IMAGE_B64}
             )):
            generate_image.generate(args)

        assert captured == [42]

    def test_lock_acquisition_timeout_exits_with_clear_message(self, tmp_path, capsys):
        """If the lock cannot be acquired within the timeout, exit code 1
        and a clear stderr message — not a silent hang."""
        output = tmp_path / "test.png"
        args = make_args(output=str(output), no_lock=False, lock_wait_timeout=1)

        from contextlib import contextmanager

        @contextmanager
        def fake_lock(timeout_seconds):
            raise TimeoutError(
                f"Could not acquire Ollama single-flight lock at /tmp/x.lock "
                f"within {timeout_seconds}s. Another image generation is "
                f"in progress; serialise your callers or use cloud "
                f"generation for parallelism."
            )
            yield  # noqa: unreachable, satisfies decorator shape

        with patch("generate_image._single_flight_lock", fake_lock):
            with pytest.raises(SystemExit) as exc_info:
                generate_image.generate(args)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "single-flight lock" in captured.err
        assert "Another image generation is in progress" in captured.err


class TestLockMechanism:
    """Lower-level tests of _single_flight_lock itself."""

    def test_lock_acquired_when_uncontended(self, tmp_path, monkeypatch):
        """A single caller acquires the lock immediately and the context
        body executes. The lock file gets created."""
        lock_path = tmp_path / "test.lock"
        monkeypatch.setattr(generate_image, "LOCK_PATH", lock_path)

        ran = []
        with generate_image._single_flight_lock(timeout_seconds=5):
            ran.append("body")
            assert lock_path.exists()
        assert ran == ["body"]

    def test_lock_released_on_exception(self, tmp_path, monkeypatch):
        """If the body raises, the lock is still released so subsequent
        callers don't deadlock."""
        lock_path = tmp_path / "test.lock"
        monkeypatch.setattr(generate_image, "LOCK_PATH", lock_path)

        with pytest.raises(RuntimeError, match="boom"):
            with generate_image._single_flight_lock(timeout_seconds=5):
                raise RuntimeError("boom")

        # Verify subsequent acquisition succeeds (lock is released).
        with generate_image._single_flight_lock(timeout_seconds=5):
            pass

    def test_lock_blocked_then_acquired(self, tmp_path, monkeypatch):
        """When the lock file is held by another process (simulated via a
        second fd holding the flock), the first caller's acquisition
        attempts block. Once the holding fd releases, the next attempt
        succeeds. We only check that the lock-recovery path runs and
        eventually exits successfully — timing details are out of scope.
        """
        import fcntl
        lock_path = tmp_path / "test.lock"
        monkeypatch.setattr(generate_image, "LOCK_PATH", lock_path)

        # Acquire and hold the lock externally.
        held_fd = open(str(lock_path), "w")
        fcntl.flock(held_fd, fcntl.LOCK_EX)

        sleeps = []

        def fake_sleep(s):
            sleeps.append(s)
            # On second sleep, release the holder so acquisition succeeds.
            if len(sleeps) == 2:
                fcntl.flock(held_fd, fcntl.LOCK_UN)
                held_fd.close()

        monkeypatch.setattr(generate_image.time, "sleep", fake_sleep)

        ran = []
        with generate_image._single_flight_lock(timeout_seconds=10):
            ran.append("body")
        assert ran == ["body"]
        # We slept at least once while waiting.
        assert len(sleeps) >= 1

    def test_lock_timeout_raises(self, tmp_path, monkeypatch):
        """Timeout propagates as TimeoutError when the lock can't be
        acquired in time."""
        import fcntl
        lock_path = tmp_path / "test.lock"
        monkeypatch.setattr(generate_image, "LOCK_PATH", lock_path)

        # Hold the lock for the duration of the test.
        held_fd = open(str(lock_path), "w")
        fcntl.flock(held_fd, fcntl.LOCK_EX)

        # Fast-forward time so the timeout deadline is exceeded
        # immediately on the first poll.
        clock = [0.0]

        def fake_monotonic():
            t = clock[0]
            clock[0] += 5.0
            return t

        monkeypatch.setattr(generate_image.time, "monotonic", fake_monotonic)
        monkeypatch.setattr(generate_image.time, "sleep", lambda s: None)

        with pytest.raises(TimeoutError, match="single-flight lock"):
            with generate_image._single_flight_lock(timeout_seconds=2):
                pass

        fcntl.flock(held_fd, fcntl.LOCK_UN)
        held_fd.close()

    def test_stale_lock_is_reclaimed(self, tmp_path, monkeypatch):
        """A lock file with mtime older than STALE_LOCK_AGE_SECONDS is
        reclaimed: the file is unlinked so the next acquisition can
        proceed. Defensive recovery for crashed-without-cleanup processes
        (suspended, killed -9 with the file still mapped, etc.)."""
        import fcntl
        lock_path = tmp_path / "test.lock"
        monkeypatch.setattr(generate_image, "LOCK_PATH", lock_path)

        # Create a "stale" lock file: held externally, but with old mtime.
        held_fd = open(str(lock_path), "w")
        fcntl.flock(held_fd, fcntl.LOCK_EX)
        # Backdate mtime past the stale threshold.
        old_time = generate_image.time.time() - generate_image.STALE_LOCK_AGE_SECONDS - 60
        os_module = generate_image.os
        os_module.utime(str(lock_path), (old_time, old_time))

        sleeps_taken = []
        def fake_sleep(s):
            sleeps_taken.append(s)
            # After the first sleep, simulate the holder releasing too.
            # Actual reclaim path: our code unlinks the file, then on the
            # next iteration creates a fresh fd and acquires.
            if len(sleeps_taken) == 1:
                # The holder still has the kernel-level flock, but our
                # code already unlinked the file. Release the flock now
                # so the next acquisition can complete.
                try:
                    fcntl.flock(held_fd, fcntl.LOCK_UN)
                    held_fd.close()
                except OSError:
                    pass

        monkeypatch.setattr(generate_image.time, "sleep", fake_sleep)

        ran = []
        with generate_image._single_flight_lock(timeout_seconds=30):
            ran.append("body")
        assert ran == ["body"]
