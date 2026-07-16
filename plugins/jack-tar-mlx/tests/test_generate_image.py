"""Tests for src/generate_image.py — mflux is never actually invoked; all
subprocess calls are mocked (issue #124, MLX local backend)."""

import json
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import generate_image  # noqa: E402

# The full-value registry<->catalog drift guard (review M2) reads the
# vendored deckhand catalog copy directly — no import of deckhand's own
# loader, so this test suite has zero cross-plugin dependency.
DECKHAND_CATALOG_PATH = (
    Path(__file__).parent.parent.parent / "jack-tar-deckhand" / "src" / "model-catalog.json"
)


def success_result(stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["mflux"], returncode=0, stdout="", stderr=stderr)


def make_args(**overrides):
    """Create a Namespace with defaults, overriding as needed."""
    defaults = {
        "prompt": "a lighthouse at sunset",
        "model": generate_image.DEFAULT_MODEL,
        "output": None,
        "width": 1024,
        "height": 1024,
        "steps": None,
        "seed": None,
        "timeout": None,
        "quantize": None,
        "check_weights": False,
        # Issue #75/#124 — nested single-flight lock kwargs.
        "lock_wait_timeout": generate_image.DEFAULT_LOCK_WAIT_TIMEOUT,
        "no_lock": True,  # default to no-lock for fast unit tests
    }
    defaults.update(overrides)
    import argparse
    return argparse.Namespace(**defaults)


class TestArgumentParsing:
    def test_help_exits_zero(self):
        with pytest.raises(SystemExit) as exc_info:
            generate_image.parse_args(["--help"])
        assert exc_info.value.code == 0

    def test_check_weights_does_not_require_prompt(self):
        args = generate_image.parse_args(["--check-weights"])
        assert args.check_weights is True

    def test_missing_prompt_without_check_weights_errors(self):
        with pytest.raises(SystemExit):
            generate_image.parse_args([])


class TestArgvConstruction:
    def test_builds_argv_with_entrypoint_and_repo(self):
        meta = generate_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = generate_image._build_argv(
            meta, meta["hf_repo"], "a cat", 1024, 1024, None, None, None, Path("/tmp/out.png"),
        )
        assert argv[0] == "mflux-generate-flux2"
        assert argv[argv.index("--model") + 1] == "Runpod/FLUX.2-klein-4B-mflux-4bit"

    def test_steps_always_present_in_argv(self):
        """Review M4d pinning test — guards the mflux silent-25-steps trap
        for EVERY registry model, even when the caller omits --steps."""
        for model_id, meta in generate_image.MLX_MODEL_REGISTRY.items():
            argv = generate_image._build_argv(
                meta, meta["hf_repo"], "p", 1024, 1024, None, None, None, Path("/tmp/o.png"),
            )
            assert "--steps" in argv, f"--steps missing for {model_id}"

    @pytest.mark.parametrize("model_id,expected_steps", [
        ("mlx/flux2-klein-4b", 4),
        ("mlx/z-image-turbo", 9),
        ("mlx/qwen-image", 20),
    ])
    def test_steps_defaults_from_registry(self, model_id, expected_steps):
        meta = generate_image.MLX_MODEL_REGISTRY[model_id]
        argv = generate_image._build_argv(
            meta, meta["hf_repo"], "p", 1024, 1024, None, None, None, Path("/tmp/o.png"),
        )
        idx = argv.index("--steps")
        assert argv[idx + 1] == str(expected_steps)

    def test_explicit_steps_override(self):
        meta = generate_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = generate_image._build_argv(
            meta, meta["hf_repo"], "p", 1024, 1024, 99, None, None, Path("/tmp/o.png"),
        )
        idx = argv.index("--steps")
        assert argv[idx + 1] == "99"

    def test_seed_included_in_argv(self):
        meta = generate_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = generate_image._build_argv(
            meta, meta["hf_repo"], "p", 1024, 1024, None, 42, None, Path("/tmp/o.png"),
        )
        idx = argv.index("--seed")
        assert argv[idx + 1] == "42"

    def test_seed_omitted_when_absent(self):
        meta = generate_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = generate_image._build_argv(
            meta, meta["hf_repo"], "p", 1024, 1024, None, None, None, Path("/tmp/o.png"),
        )
        assert "--seed" not in argv

    def test_quantize_omitted_for_prequantized_primary(self):
        """klein primary is a '-mflux-' pre-quantized export — never -q."""
        meta = generate_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = generate_image._build_argv(
            meta, meta["hf_repo"], "p", 1024, 1024, None, None, None, Path("/tmp/o.png"),
        )
        assert "-q" not in argv

    @pytest.mark.parametrize("model_id,expected_q", [
        ("mlx/flux2-klein-4b", 4),
        ("mlx/qwen-image", 6),
    ])
    def test_quantize_applied_on_fullprecision_fallback(self, model_id, expected_q):
        meta = generate_image.MLX_MODEL_REGISTRY[model_id]
        argv = generate_image._build_argv(
            meta, meta["hf_repo_fallback"], "p", 1024, 1024, None, None, None, Path("/tmp/o.png"),
        )
        idx = argv.index("-q")
        assert argv[idx + 1] == str(expected_q)

    def test_explicit_quantize_override_still_skipped_on_prequantized(self):
        """Review m13 — -q is NEVER emitted for a '-mflux-' repo, even when
        the caller passes an explicit --quantize."""
        meta = generate_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = generate_image._build_argv(
            meta, meta["hf_repo"], "p", 1024, 1024, None, None, 8, Path("/tmp/o.png"),
        )
        assert "-q" not in argv

    def test_metadata_flag_present(self):
        meta = generate_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = generate_image._build_argv(
            meta, meta["hf_repo"], "p", 1024, 1024, None, None, None, Path("/tmp/o.png"),
        )
        assert "--metadata" in argv

    def test_custom_dimensions(self):
        meta = generate_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = generate_image._build_argv(
            meta, meta["hf_repo"], "p", 512, 768, None, None, None, Path("/tmp/o.png"),
        )
        assert argv[argv.index("--width") + 1] == "512"
        assert argv[argv.index("--height") + 1] == "768"


class TestMetadataSidecar:
    def test_metadata_sidecar_path_uses_metadata_json_suffix(self):
        """Review OQ-4 — mflux writes <stem>.metadata.json, not
        <name>.png.metadata.json."""
        assert generate_image._metadata_sidecar_path(Path("/tmp/foo.png")) == Path("/tmp/foo.metadata.json")


class TestTimeoutResolution:
    @pytest.mark.parametrize("model_id,expected_timeout", [
        ("mlx/flux2-klein-4b", 300),
        ("mlx/z-image-turbo", 180),
        ("mlx/qwen-image", 900),
    ])
    def test_timeout_from_registry(self, model_id, expected_timeout):
        meta = generate_image.MLX_MODEL_REGISTRY[model_id]
        assert generate_image.resolve_timeout(meta, None) == expected_timeout

    def test_explicit_timeout_override(self):
        meta = generate_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        assert generate_image.resolve_timeout(meta, 42) == 42


class TestModelResolution:
    def test_unknown_model_exits(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            generate_image.resolve_model("mlx/does-not-exist")
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Unknown MLX model" in captured.err


class TestHappyPath:
    def test_prints_output_path_on_stdout(self, tmp_path, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output))
        with patch("generate_image.shutil.which", return_value="/usr/bin/mflux-generate-flux2"), \
             patch("generate_image.subprocess.run", return_value=success_result()):
            generate_image.generate(args)

        captured = capsys.readouterr()
        assert captured.out.strip().splitlines()[-1] == str(output)

    def test_emits_repo_used_on_stderr(self, tmp_path, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output))
        with patch("generate_image.shutil.which", return_value="/usr/bin/mflux-generate-flux2"), \
             patch("generate_image.subprocess.run", return_value=success_result()):
            generate_image.generate(args)

        captured = capsys.readouterr()
        assert "MFLUX_REPO_USED=Runpod/FLUX.2-klein-4B-mflux-4bit" in captured.err

    def test_creates_output_directory(self, tmp_path):
        output = tmp_path / "nested" / "dir" / "image.png"
        args = make_args(output=str(output))
        with patch("generate_image.shutil.which", return_value="/usr/bin/x"), \
             patch("generate_image.subprocess.run", return_value=success_result()):
            generate_image.generate(args)

        assert output.parent.exists()

    def test_default_output_path_uses_timestamp(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = make_args(output=None)
        with patch("generate_image.shutil.which", return_value="/usr/bin/x"), \
             patch("generate_image.subprocess.run", return_value=success_result()):
            generate_image.generate(args)

        captured = capsys.readouterr()
        path = captured.out.strip()
        assert "output" in path
        assert path.endswith(".png")


class TestSubprocessEnv:
    def test_subprocess_env_forces_hf_offline(self, tmp_path):
        """The refusal-to-download guard — HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE
        are always set so a cache miss fails fast instead of downloading."""
        output = tmp_path / "out.png"
        args = make_args(output=str(output))
        with patch("generate_image.shutil.which", return_value="/usr/bin/x"), \
             patch("generate_image.subprocess.run", return_value=success_result()) as mock_run:
            generate_image.generate(args)

        env = mock_run.call_args.kwargs["env"]
        assert env["HF_HUB_OFFLINE"] == "1"
        assert env["TRANSFORMERS_OFFLINE"] == "1"


class TestErrorHandling:
    def test_cli_missing_exits_with_install_hint(self, tmp_path, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output))
        with patch("generate_image.shutil.which", return_value=None):
            with pytest.raises(SystemExit) as exc_info:
                generate_image.generate(args)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "uv tool install --upgrade mflux" in captured.err

    def test_weights_missing_exits_without_download(self, tmp_path, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output))
        fail = subprocess.CompletedProcess(
            args=["x"], returncode=1, stdout="",
            stderr="LocalEntryNotFoundError: weights not cached",
        )
        with patch("generate_image.shutil.which", return_value="/usr/bin/x"), \
             patch("generate_image.subprocess.run", return_value=fail) as mock_run:
            with pytest.raises(SystemExit) as exc_info:
                generate_image.generate(args)

        assert exc_info.value.code == 1
        # Primary AND fallback both tried, both fail — no download either way.
        assert mock_run.call_count == 2
        captured = capsys.readouterr()
        assert "hf download Runpod/FLUX.2-klein-4B-mflux-4bit" in captured.err
        assert not output.exists()

    def test_fallback_repo_tried_when_primary_missing(self, tmp_path):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), model="mlx/z-image-turbo")
        fail = subprocess.CompletedProcess(
            args=["x"], returncode=1, stdout="", stderr="running in offline mode, cannot load",
        )
        with patch("generate_image.shutil.which", return_value="/usr/bin/x"), \
             patch("generate_image.subprocess.run", side_effect=[fail, success_result()]) as mock_run:
            generate_image.generate(args)

        assert mock_run.call_count == 2
        second_argv = mock_run.call_args_list[1].args[0]
        assert "Tongyi-MAI/Z-Image-Turbo" in second_argv
        idx = second_argv.index("-q")
        assert second_argv[idx + 1] == "4"

    def test_timeout_expired_message(self, tmp_path, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output))
        with patch("generate_image.shutil.which", return_value="/usr/bin/x"), \
             patch("generate_image.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="x", timeout=300)):
            with pytest.raises(SystemExit) as exc_info:
                generate_image.generate(args)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "timed out" in captured.err.lower()

    def test_timeout_removes_partial_output(self, tmp_path):
        """Review m14 — a partial PNG + sidecar written before a timeout
        are unlinked so downstream steps never see a half-render."""
        output = tmp_path / "out.png"
        output.write_bytes(b"partial-png-bytes")
        sidecar = generate_image._metadata_sidecar_path(output)
        sidecar.write_text("{}")
        args = make_args(output=str(output))
        with patch("generate_image.shutil.which", return_value="/usr/bin/x"), \
             patch("generate_image.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="x", timeout=300)):
            with pytest.raises(SystemExit):
                generate_image.generate(args)

        assert not output.exists()
        assert not sidecar.exists()

    def test_nonzero_exit_removes_partial_output(self, tmp_path):
        """Review m14 — same cleanup on a non-zero mflux return code."""
        output = tmp_path / "out.png"
        output.write_bytes(b"partial-png-bytes")
        sidecar = generate_image._metadata_sidecar_path(output)
        sidecar.write_text("{}")
        args = make_args(output=str(output))
        fail = subprocess.CompletedProcess(args=["x"], returncode=1, stdout="", stderr="some unrelated failure")
        with patch("generate_image.shutil.which", return_value="/usr/bin/x"), \
             patch("generate_image.subprocess.run", return_value=fail):
            with pytest.raises(SystemExit):
                generate_image.generate(args)

        assert not output.exists()
        assert not sidecar.exists()

    def test_oom_hint_on_metal_error(self, tmp_path, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output))
        fail = subprocess.CompletedProcess(
            args=["x"], returncode=1, stdout="",
            stderr="Metal: out of memory allocating MTLBuffer",
        )
        with patch("generate_image.shutil.which", return_value="/usr/bin/x"), \
             patch("generate_image.subprocess.run", return_value=fail):
            with pytest.raises(SystemExit) as exc_info:
                generate_image.generate(args)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "RAM" in captured.err
        assert "-q 4" in captured.err

    def test_other_nonzero_exit_surfaces_stderr_tail(self, tmp_path, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output))
        fail = subprocess.CompletedProcess(
            args=["x"], returncode=7, stdout="", stderr="some unrelated crash trace " * 10,
        )
        with patch("generate_image.shutil.which", return_value="/usr/bin/x"), \
             patch("generate_image.subprocess.run", return_value=fail):
            with pytest.raises(SystemExit) as exc_info:
                generate_image.generate(args)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "mflux error (exit 7)" in captured.err


class TestCheckWeights:
    def test_check_weights_mode_lists_models_without_render(self, capsys):
        def fake_complete(repo_id, hub_dir):
            return repo_id == "Runpod/FLUX.2-klein-4B-mflux-4bit"

        with patch("generate_image._hf_snapshot_complete", side_effect=fake_complete), \
             patch("generate_image.subprocess.run") as mock_run:
            generate_image.check_weights()

        mock_run.assert_not_called()
        captured = capsys.readouterr()
        lines = captured.out.strip().splitlines()
        assert any(line.startswith("mlx/flux2-klein-4b: READY") for line in lines)
        assert any(
            line == "mlx/z-image-turbo: NOT_READY (run: hf download filipstrand/Z-Image-Turbo-mflux-4bit)"
            for line in lines
        )
        assert any(
            line == "mlx/qwen-image: NOT_READY (run: hf download filipstrand/Qwen-Image-mflux-6bit)"
            for line in lines
        )


class TestSingleFlightLockGenerate:
    """Issue #124/#75 — the mlx wrapper nests two locks: the ollama lock
    FIRST, then its own (review M5). These tests drive ``generate()`` with
    ``_single_flight_lock`` faked so we can observe acquisition order and
    the shared deadline without touching the filesystem."""

    def test_no_lock_flag_skips_both_locks(self, tmp_path):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), no_lock=True)
        with patch("generate_image._single_flight_lock") as mock_lock, \
             patch("generate_image.shutil.which", return_value="/usr/bin/x"), \
             patch("generate_image.subprocess.run", return_value=success_result()):
            generate_image.generate(args)
        mock_lock.assert_not_called()

    def test_default_invocation_acquires_and_releases_both_locks(self, tmp_path):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), no_lock=False)
        events = []

        @contextmanager
        def fake_lock(lock_path, timeout_seconds):
            events.append(("acquire", lock_path))
            try:
                yield 0
            finally:
                events.append(("release", lock_path))

        with patch("generate_image._single_flight_lock", fake_lock), \
             patch("generate_image.shutil.which", return_value="/usr/bin/x"), \
             patch("generate_image.subprocess.run", return_value=success_result()):
            generate_image.generate(args)

        assert events == [
            ("acquire", generate_image.OLLAMA_LOCK_PATH),
            ("acquire", generate_image.LOCK_PATH),
            ("release", generate_image.LOCK_PATH),
            ("release", generate_image.OLLAMA_LOCK_PATH),
        ]

    def test_lock_acquisition_order_ollama_first(self, tmp_path):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), no_lock=False)
        order = []

        @contextmanager
        def fake_lock(lock_path, timeout_seconds):
            order.append(lock_path)
            yield 0

        with patch("generate_image._single_flight_lock", fake_lock), \
             patch("generate_image.shutil.which", return_value="/usr/bin/x"), \
             patch("generate_image.subprocess.run", return_value=success_result()):
            generate_image.generate(args)

        assert order == [generate_image.OLLAMA_LOCK_PATH, generate_image.LOCK_PATH]

    def test_lock_wait_timeout_is_shared_deadline(self, tmp_path, monkeypatch):
        """A slow ollama-lock acquisition eats into the mlx-lock budget."""
        output = tmp_path / "out.png"
        args = make_args(output=str(output), no_lock=False, lock_wait_timeout=600)
        timeouts = []
        clock = [0.0]

        monkeypatch.setattr(generate_image.time, "monotonic", lambda: clock[0])

        @contextmanager
        def fake_lock(lock_path, timeout_seconds):
            timeouts.append(timeout_seconds)
            if lock_path == generate_image.OLLAMA_LOCK_PATH:
                clock[0] += 100  # simulate the ollama lock taking 100s to acquire
            yield 0

        with patch("generate_image._single_flight_lock", fake_lock), \
             patch("generate_image.shutil.which", return_value="/usr/bin/x"), \
             patch("generate_image.subprocess.run", return_value=success_result()):
            generate_image.generate(args)

        assert timeouts[0] == 600
        assert timeouts[1] == pytest.approx(500, abs=1)

    def test_lock_wait_timeout_propagates(self, tmp_path):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), no_lock=False, lock_wait_timeout=42)
        captured_timeouts = []

        @contextmanager
        def fake_lock(lock_path, timeout_seconds):
            captured_timeouts.append(timeout_seconds)
            yield 0

        with patch("generate_image._single_flight_lock", fake_lock), \
             patch("generate_image.shutil.which", return_value="/usr/bin/x"), \
             patch("generate_image.subprocess.run", return_value=success_result()):
            generate_image.generate(args)

        assert captured_timeouts[0] == 42

    def test_lock_acquisition_timeout_exits(self, tmp_path, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), no_lock=False, lock_wait_timeout=1)

        @contextmanager
        def fake_lock(lock_path, timeout_seconds):
            raise TimeoutError(
                f"Could not acquire MLX single-flight lock at {lock_path} "
                f"within {timeout_seconds}s. Another local image generation "
                f"is in progress; serialise your callers or use cloud "
                f"generation for parallelism."
            )
            yield  # noqa: unreachable, satisfies decorator shape

        with patch("generate_image._single_flight_lock", fake_lock):
            with pytest.raises(SystemExit) as exc_info:
                generate_image.generate(args)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "single-flight lock" in captured.err
        assert "Another local image generation is in progress" in captured.err


class TestLockMechanism:
    """Lower-level tests of _single_flight_lock itself, pointed at a tmp_path
    lock file (the mlx lock path is a plain constructor argument here, so no
    module-attribute monkeypatching is needed)."""

    def test_lock_acquired_when_uncontended(self, tmp_path):
        lock_path = tmp_path / "test.lock"
        ran = []
        with generate_image._single_flight_lock(lock_path, timeout_seconds=5):
            ran.append("body")
            assert lock_path.exists()
        assert ran == ["body"]

    def test_lock_released_on_exception(self, tmp_path):
        lock_path = tmp_path / "test.lock"
        with pytest.raises(RuntimeError, match="boom"):
            with generate_image._single_flight_lock(lock_path, timeout_seconds=5):
                raise RuntimeError("boom")

        # Verify subsequent acquisition succeeds (lock is released).
        with generate_image._single_flight_lock(lock_path, timeout_seconds=5):
            pass

    def test_lock_blocked_then_acquired(self, tmp_path, monkeypatch):
        import fcntl
        lock_path = tmp_path / "test.lock"

        held_fd = open(str(lock_path), "w")
        fcntl.flock(held_fd, fcntl.LOCK_EX)

        sleeps = []

        def fake_sleep(s):
            sleeps.append(s)
            if len(sleeps) == 2:
                fcntl.flock(held_fd, fcntl.LOCK_UN)
                held_fd.close()

        monkeypatch.setattr(generate_image.time, "sleep", fake_sleep)

        ran = []
        with generate_image._single_flight_lock(lock_path, timeout_seconds=10):
            ran.append("body")
        assert ran == ["body"]
        assert len(sleeps) >= 1

    def test_lock_timeout_raises(self, tmp_path, monkeypatch):
        import fcntl
        lock_path = tmp_path / "test.lock"

        held_fd = open(str(lock_path), "w")
        fcntl.flock(held_fd, fcntl.LOCK_EX)

        clock = [0.0]

        def fake_monotonic():
            t = clock[0]
            clock[0] += 5.0
            return t

        monkeypatch.setattr(generate_image.time, "monotonic", fake_monotonic)
        monkeypatch.setattr(generate_image.time, "sleep", lambda s: None)

        with pytest.raises(TimeoutError, match="single-flight lock"):
            with generate_image._single_flight_lock(lock_path, timeout_seconds=2):
                pass

        fcntl.flock(held_fd, fcntl.LOCK_UN)
        held_fd.close()

    def test_stale_lock_is_reclaimed(self, tmp_path, monkeypatch):
        import fcntl
        lock_path = tmp_path / "test.lock"

        held_fd = open(str(lock_path), "w")
        fcntl.flock(held_fd, fcntl.LOCK_EX)
        old_time = generate_image.time.time() - generate_image.STALE_LOCK_AGE_SECONDS - 60
        generate_image.os.utime(str(lock_path), (old_time, old_time))

        sleeps_taken = []

        def fake_sleep(s):
            sleeps_taken.append(s)
            if len(sleeps_taken) == 1:
                try:
                    fcntl.flock(held_fd, fcntl.LOCK_UN)
                    held_fd.close()
                except OSError:
                    pass

        monkeypatch.setattr(generate_image.time, "sleep", fake_sleep)

        ran = []
        with generate_image._single_flight_lock(lock_path, timeout_seconds=30):
            ran.append("body")
        assert ran == ["body"]


class TestCatalogDriftGuard:
    """Review M2 — full per-field equality between MLX_MODEL_REGISTRY and
    the vendored deckhand catalog's active mlx/* entries, so the two can
    never silently diverge."""

    def test_registry_matches_catalog_mlx_entries(self):
        catalog = json.loads(DECKHAND_CATALOG_PATH.read_text())
        mlx_entries = {
            m["id"]: m for m in catalog["models"]
            if m["provider"] == "mlx" and m.get("status") == "active"
        }

        # Exact key-set equality — no extra, no missing.
        assert set(generate_image.MLX_MODEL_REGISTRY.keys()) == set(mlx_entries.keys())

        for entry_id, entry in mlx_entries.items():
            sdk = entry["sdk"]
            capabilities = entry["capabilities"]
            expected = {
                "entrypoint": sdk["entrypoint"],
                "hf_repo": sdk["hf_repo"],
                "hf_repo_fallback": sdk.get("hf_repo_fallback"),
                "default_steps": sdk["default_steps"],
                "quantize": sdk["quantize"],
                "timeout": capabilities["timeout_seconds"],
            }
            assert generate_image.MLX_MODEL_REGISTRY[entry_id] == expected
