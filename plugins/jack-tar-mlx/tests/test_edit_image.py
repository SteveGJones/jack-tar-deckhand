"""Tests for src/edit_image.py — mflux is never actually invoked; all
subprocess calls are mocked (issue #143, edit tier)."""

import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path so we can import the module (F-01 flat-import convention —
# same as test_generate_image.py).
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import edit_image  # noqa: E402
import generate_image  # noqa: E402


def success_result(stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["mflux"], returncode=0, stdout="", stderr=stderr)


def make_args(**overrides):
    """Create a Namespace with defaults, overriding as needed."""
    defaults = {
        "prompt": "darken the sky, keep the ships",
        "image_paths": None,  # set per-test via tmp_path fixtures
        "model": edit_image.DEFAULT_MODEL,
        "output": None,
        "steps": None,
        "seed": None,
        "guidance": edit_image.DEFAULT_GUIDANCE,
        "timeout": None,
        "quantize": None,
        "check_weights": False,
        "lock_wait_timeout": generate_image.DEFAULT_LOCK_WAIT_TIMEOUT,
        "no_lock": True,  # default to no-lock for fast unit tests
    }
    defaults.update(overrides)
    import argparse
    return argparse.Namespace(**defaults)


@pytest.fixture
def base_image(tmp_path):
    path = tmp_path / "base.png"
    path.write_bytes(b"fake-png-bytes")
    return path


@pytest.fixture
def ref_image(tmp_path):
    path = tmp_path / "ref.png"
    path.write_bytes(b"fake-ref-png-bytes")
    return path


class TestImportForm:
    """F-01 — the module imports the shared helpers FLAT (from
    generate_image import ...), not as a relative package import, and
    resolves via the same sys.path.insert convention the test suite
    already uses for generate_image."""

    def test_shares_the_same_registry_object(self):
        assert edit_image.MLX_MODEL_REGISTRY is generate_image.MLX_MODEL_REGISTRY

    def test_shares_the_same_lock_path_constants(self):
        assert edit_image.OLLAMA_LOCK_PATH is generate_image.OLLAMA_LOCK_PATH
        assert edit_image.LOCK_PATH is generate_image.LOCK_PATH

    def test_shares_the_same_lock_primitive(self):
        assert edit_image._single_flight_lock is generate_image._single_flight_lock

    def test_no_package_relative_import_artifacts(self):
        """A relative import would require __init__.py in src/, which
        does not exist — the module having imported cleanly at all
        already proves the flat form works, this just documents why."""
        assert not (Path(edit_image.__file__).parent / "__init__.py").exists()


class TestArgumentParsing:
    def test_help_exits_zero(self):
        with pytest.raises(SystemExit) as exc_info:
            edit_image.parse_args(["--help"])
        assert exc_info.value.code == 0

    def test_check_weights_does_not_require_prompt_or_image_paths(self):
        args = edit_image.parse_args(["--check-weights"])
        assert args.check_weights is True

    def test_missing_prompt_without_check_weights_errors(self):
        with pytest.raises(SystemExit):
            edit_image.parse_args(["--image-paths", "/tmp/base.png"])

    def test_missing_image_paths_without_check_weights_errors(self):
        with pytest.raises(SystemExit):
            edit_image.parse_args(["--prompt", "darken the sky"])

    def test_plural_image_paths_accepted(self):
        args = edit_image.parse_args([
            "--prompt", "p", "--image-paths", "/tmp/base.png", "/tmp/ref.png",
        ])
        assert args.image_paths == ["/tmp/base.png", "/tmp/ref.png"]

    def test_guidance_defaults_to_3_5(self):
        args = edit_image.parse_args(["--prompt", "p", "--image-paths", "/tmp/base.png"])
        assert args.guidance == 3.5

    def test_guidance_override(self):
        args = edit_image.parse_args([
            "--prompt", "p", "--image-paths", "/tmp/base.png", "--guidance", "1.5",
        ])
        assert args.guidance == 1.5

    def test_no_dims_flags_defined(self):
        """F-03/S7 ruling — the wrapper never exposes dims flags at all.
        Passing --width/--height must be REJECTED as unknown flags."""
        with pytest.raises(SystemExit):
            edit_image.parse_args([
                "--prompt", "p", "--image-paths", "/tmp/base.png", "--width", "512",
            ])
        with pytest.raises(SystemExit):
            edit_image.parse_args([
                "--prompt", "p", "--image-paths", "/tmp/base.png", "--height", "512",
            ])


class TestArgvConstruction:
    def test_builds_argv_with_edit_entrypoint_and_repo(self, base_image):
        meta = edit_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = edit_image._build_edit_argv(
            meta, meta["hf_repo"], "darken the sky", [str(base_image)],
            None, 42, 3.5, None, Path("/tmp/out.png"),
        )
        assert argv[0] == "mflux-generate-flux2-edit"
        assert argv[argv.index("--model") + 1] == "Runpod/FLUX.2-klein-4B-mflux-4bit"

    def test_steps_always_present_in_argv(self):
        """Same mflux silent-25-steps trap the generate wrapper guards
        against, pinned for every edit-capable registry model."""
        for model_id, meta in edit_image.MLX_MODEL_REGISTRY.items():
            if not meta.get("edit_entrypoint"):
                continue
            argv = edit_image._build_edit_argv(
                meta, meta["hf_repo"], "p", ["/tmp/base.png"],
                None, 42, 3.5, None, Path("/tmp/o.png"),
            )
            assert "--steps" in argv, f"--steps missing for {model_id}"

    @pytest.mark.parametrize("model_id,expected_steps", [
        ("mlx/flux2-klein-4b", 4),
        ("mlx/qwen-image", 8),
    ])
    def test_steps_defaults_from_registry_edit_steps(self, model_id, expected_steps):
        meta = edit_image.MLX_MODEL_REGISTRY[model_id]
        argv = edit_image._build_edit_argv(
            meta, meta["hf_repo"], "p", ["/tmp/base.png"],
            None, 42, 3.5, None, Path("/tmp/o.png"),
        )
        idx = argv.index("--steps")
        assert argv[idx + 1] == str(expected_steps)

    def test_explicit_steps_override(self):
        meta = edit_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = edit_image._build_edit_argv(
            meta, meta["hf_repo"], "p", ["/tmp/base.png"],
            99, 42, 3.5, None, Path("/tmp/o.png"),
        )
        idx = argv.index("--steps")
        assert argv[idx + 1] == "99"

    def test_seed_always_in_argv(self):
        """F-08 — by the time _build_edit_argv runs, a seed has always
        been resolved (explicit or generated) by the caller."""
        meta = edit_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = edit_image._build_edit_argv(
            meta, meta["hf_repo"], "p", ["/tmp/base.png"],
            None, 12345, 3.5, None, Path("/tmp/o.png"),
        )
        idx = argv.index("--seed")
        assert argv[idx + 1] == "12345"

    def test_guidance_passthrough(self):
        meta = edit_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = edit_image._build_edit_argv(
            meta, meta["hf_repo"], "p", ["/tmp/base.png"],
            None, 42, 6.0, None, Path("/tmp/o.png"),
        )
        idx = argv.index("--guidance")
        assert argv[idx + 1] == "6.0"

    def test_guidance_omitted_when_none(self):
        meta = edit_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = edit_image._build_edit_argv(
            meta, meta["hf_repo"], "p", ["/tmp/base.png"],
            None, 42, None, None, Path("/tmp/o.png"),
        )
        assert "--guidance" not in argv

    def test_plural_image_paths_in_argv(self):
        meta = edit_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = edit_image._build_edit_argv(
            meta, meta["hf_repo"], "p", ["/tmp/base.png", "/tmp/ref.png"],
            None, 42, 3.5, None, Path("/tmp/o.png"),
        )
        idx = argv.index("--image-paths")
        assert argv[idx + 1] == "/tmp/base.png"
        assert argv[idx + 2] == "/tmp/ref.png"

    def test_no_dims_flags_ever_in_constructed_argv(self):
        """F-03/S7 ruling — the argv must NEVER contain --width/--height,
        regardless of what the caller passes (there is no parameter for
        it at all)."""
        meta = edit_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = edit_image._build_edit_argv(
            meta, meta["hf_repo"], "p", ["/tmp/base.png"],
            None, 42, 3.5, None, Path("/tmp/o.png"),
        )
        assert "--width" not in argv
        assert "--height" not in argv

    def test_quantize_omitted_for_prequantized_primary(self):
        meta = edit_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = edit_image._build_edit_argv(
            meta, meta["hf_repo"], "p", ["/tmp/base.png"],
            None, 42, 3.5, None, Path("/tmp/o.png"),
        )
        assert "-q" not in argv

    def test_quantize_applied_on_fullprecision_fallback(self):
        meta = edit_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = edit_image._build_edit_argv(
            meta, meta["hf_repo_fallback"], "p", ["/tmp/base.png"],
            None, 42, 3.5, None, Path("/tmp/o.png"),
        )
        idx = argv.index("-q")
        assert argv[idx + 1] == "4"

    def test_metadata_flag_present(self):
        meta = edit_image.MLX_MODEL_REGISTRY["mlx/flux2-klein-4b"]
        argv = edit_image._build_edit_argv(
            meta, meta["hf_repo"], "p", ["/tmp/base.png"],
            None, 42, 3.5, None, Path("/tmp/o.png"),
        )
        assert "--metadata" in argv


class TestModelResolution:
    def test_unknown_model_exits(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            edit_image._resolve_edit_meta("mlx/does-not-exist")
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Unknown MLX model" in captured.err

    def test_non_edit_capable_model_exits_with_edit_capable_list(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            edit_image._resolve_edit_meta("mlx/z-image-turbo")
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "is not edit-capable" in captured.err
        assert "mlx/flux2-klein-4b" in captured.err

    def test_edit_capable_model_resolves(self):
        meta = edit_image._resolve_edit_meta("mlx/flux2-klein-4b")
        assert meta["edit_entrypoint"] == "mflux-generate-flux2-edit"


class TestBaseImageValidation:
    def test_missing_base_image_exits_without_fallthrough(self, tmp_path, capsys):
        """Missing base -> exit 1, no fall-through to a from-scratch
        generate (design §3.1)."""
        output = tmp_path / "out.png"
        missing_base = tmp_path / "does-not-exist.png"
        args = make_args(output=str(output), image_paths=[str(missing_base)])
        with patch("edit_image.shutil.which", return_value="/usr/bin/mflux-generate-flux2-edit"), \
             patch("edit_image.subprocess.run") as mock_run:
            with pytest.raises(SystemExit) as exc_info:
                edit_image.edit(args)
        assert exc_info.value.code == 1
        mock_run.assert_not_called()
        captured = capsys.readouterr()
        assert "edit base image not found" in captured.err
        assert str(missing_base) in captured.err

    def test_missing_reference_image_exits(self, tmp_path, base_image, capsys):
        output = tmp_path / "out.png"
        missing_ref = tmp_path / "no-ref.png"
        args = make_args(output=str(output), image_paths=[str(base_image), str(missing_ref)])
        with patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run") as mock_run:
            with pytest.raises(SystemExit):
                edit_image.edit(args)
        mock_run.assert_not_called()
        captured = capsys.readouterr()
        assert str(missing_ref) in captured.err


class TestHappyPath:
    def test_prints_output_path_on_stdout(self, tmp_path, base_image, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)])
        with patch("edit_image.shutil.which", return_value="/usr/bin/mflux-generate-flux2-edit"), \
             patch("edit_image.subprocess.run", return_value=success_result()):
            edit_image.edit(args)

        captured = capsys.readouterr()
        assert captured.out.strip().splitlines()[-1] == str(output)

    def test_emits_repo_used_on_stderr(self, tmp_path, base_image, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)])
        with patch("edit_image.shutil.which", return_value="/usr/bin/mflux-generate-flux2-edit"), \
             patch("edit_image.subprocess.run", return_value=success_result()):
            edit_image.edit(args)

        captured = capsys.readouterr()
        assert "MFLUX_REPO_USED=Runpod/FLUX.2-klein-4B-mflux-4bit" in captured.err

    def test_creates_output_directory(self, tmp_path, base_image):
        output = tmp_path / "nested" / "dir" / "image.png"
        args = make_args(output=str(output), image_paths=[str(base_image)])
        with patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", return_value=success_result()):
            edit_image.edit(args)

        assert output.parent.exists()

    def test_default_output_path_uses_timestamp(self, tmp_path, base_image, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = make_args(output=None, image_paths=[str(base_image)])
        with patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", return_value=success_result()):
            edit_image.edit(args)

        captured = capsys.readouterr()
        # stdout's last line is the output path; MFLUX_SEED_USED/REPO_USED
        # are on stderr, so stdout should carry exactly the path line.
        path = captured.out.strip().splitlines()[-1]
        assert "output" in path
        assert path.endswith(".png")


class TestSeedResolution:
    """F-08, S3-confirmed — an edit's seed must always be resolvable
    after the fact, so the wrapper generates one when omitted and
    ALWAYS reports the resolved value."""

    def test_omitted_seed_generates_one_present_in_argv(self, tmp_path, base_image):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)], seed=None)
        with patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", return_value=success_result()) as mock_run, \
             patch("edit_image.random.randrange", return_value=999888):
            edit_image.edit(args)

        argv = mock_run.call_args.args[0]
        idx = argv.index("--seed")
        assert argv[idx + 1] == "999888"

    def test_omitted_seed_reports_mflux_seed_used_on_stderr(self, tmp_path, base_image, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)], seed=None)
        with patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", return_value=success_result()), \
             patch("edit_image.random.randrange", return_value=999888):
            edit_image.edit(args)

        captured = capsys.readouterr()
        assert "MFLUX_SEED_USED=999888" in captured.err

    def test_explicit_seed_passed_through_verbatim(self, tmp_path, base_image, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)], seed=42)
        with patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", return_value=success_result()) as mock_run:
            edit_image.edit(args)

        argv = mock_run.call_args.args[0]
        idx = argv.index("--seed")
        assert argv[idx + 1] == "42"
        captured = capsys.readouterr()
        assert "MFLUX_SEED_USED=42" in captured.err


class TestSubprocessEnv:
    def test_subprocess_env_forces_hf_offline(self, tmp_path, base_image):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)])
        with patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", return_value=success_result()) as mock_run:
            edit_image.edit(args)

        env = mock_run.call_args.kwargs["env"]
        assert env["HF_HUB_OFFLINE"] == "1"
        assert env["TRANSFORMERS_OFFLINE"] == "1"


class TestErrorHandling:
    def test_edit_entrypoint_missing_exits_with_install_hint(self, tmp_path, base_image, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)])
        with patch("edit_image.shutil.which", return_value=None):
            with pytest.raises(SystemExit) as exc_info:
                edit_image.edit(args)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "uv tool install --upgrade mflux" in captured.err
        assert "mflux-generate-flux2-edit" in captured.err

    def test_weights_missing_exits_without_download(self, tmp_path, base_image, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)])
        fail = subprocess.CompletedProcess(
            args=["x"], returncode=1, stdout="",
            stderr="LocalEntryNotFoundError: weights not cached",
        )
        with patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", return_value=fail) as mock_run:
            with pytest.raises(SystemExit) as exc_info:
                edit_image.edit(args)

        assert exc_info.value.code == 1
        assert mock_run.call_count == 2  # primary AND fallback tried
        captured = capsys.readouterr()
        assert "hf download Runpod/FLUX.2-klein-4B-mflux-4bit" in captured.err
        assert not output.exists()

    def test_fallback_repo_tried_when_primary_missing(self, tmp_path, base_image):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)], model="mlx/qwen-image")
        fail = subprocess.CompletedProcess(
            args=["x"], returncode=1, stdout="", stderr="running in offline mode, cannot load",
        )
        with patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", side_effect=[fail, success_result()]) as mock_run:
            edit_image.edit(args)

        assert mock_run.call_count == 2
        second_argv = mock_run.call_args_list[1].args[0]
        assert "Qwen/Qwen-Image" in second_argv
        idx = second_argv.index("-q")
        assert second_argv[idx + 1] == "4"

    def test_timeout_expired_message(self, tmp_path, base_image, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)])
        with patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="x", timeout=300)):
            with pytest.raises(SystemExit) as exc_info:
                edit_image.edit(args)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "timed out" in captured.err.lower()

    def test_timeout_removes_partial_output(self, tmp_path, base_image):
        output = tmp_path / "out.png"
        output.write_bytes(b"partial-png-bytes")
        sidecar = output.with_suffix(".metadata.json")
        sidecar.write_text("{}")
        args = make_args(output=str(output), image_paths=[str(base_image)])
        with patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="x", timeout=300)):
            with pytest.raises(SystemExit):
                edit_image.edit(args)

        assert not output.exists()
        assert not sidecar.exists()

    def test_nonzero_exit_removes_partial_output(self, tmp_path, base_image):
        output = tmp_path / "out.png"
        output.write_bytes(b"partial-png-bytes")
        sidecar = output.with_suffix(".metadata.json")
        sidecar.write_text("{}")
        args = make_args(output=str(output), image_paths=[str(base_image)])
        fail = subprocess.CompletedProcess(args=["x"], returncode=1, stdout="", stderr="some unrelated failure")
        with patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", return_value=fail):
            with pytest.raises(SystemExit):
                edit_image.edit(args)

        assert not output.exists()
        assert not sidecar.exists()

    def test_oom_hint_on_metal_error(self, tmp_path, base_image, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)])
        fail = subprocess.CompletedProcess(
            args=["x"], returncode=1, stdout="",
            stderr="Metal: out of memory allocating MTLBuffer",
        )
        with patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", return_value=fail):
            with pytest.raises(SystemExit) as exc_info:
                edit_image.edit(args)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "RAM" in captured.err
        assert "-q 4" in captured.err

    def test_other_nonzero_exit_surfaces_stderr_tail(self, tmp_path, base_image, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)])
        long_stderr = ("boilerplate traceback frame\n" * 40) + "ValueError: the actual error"
        fail = subprocess.CompletedProcess(
            args=["x"], returncode=7, stdout="", stderr=long_stderr,
        )
        with patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", return_value=fail):
            with pytest.raises(SystemExit) as exc_info:
                edit_image.edit(args)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "mflux edit error (exit 7)" in captured.err
        assert "ValueError: the actual error" in captured.err


class TestTimeoutResolution:
    def test_timeout_defaults_from_registry(self, tmp_path, base_image):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)], timeout=None)
        with patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", return_value=success_result()) as mock_run:
            edit_image.edit(args)

        assert mock_run.call_args.kwargs["timeout"] == 300  # klein-4b registry timeout

    def test_explicit_timeout_override_honoured(self, tmp_path, base_image):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)], timeout=42)
        with patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", return_value=success_result()) as mock_run:
            edit_image.edit(args)

        assert mock_run.call_args.kwargs["timeout"] == 42


class TestCheckWeights:
    def test_check_weights_mode_lists_only_edit_capable_models(self, capsys):
        def fake_complete(repo_id, hub_dir):
            return repo_id == "Runpod/FLUX.2-klein-4B-mflux-4bit"

        with patch("edit_image._hf_snapshot_complete", side_effect=fake_complete), \
             patch("edit_image.subprocess.run") as mock_run:
            edit_image.check_weights()

        mock_run.assert_not_called()
        captured = capsys.readouterr()
        lines = captured.out.strip().splitlines()
        assert any(line.startswith("mlx/flux2-klein-4b: READY") for line in lines)
        assert any(
            line == "mlx/qwen-image: NOT_READY (run: hf download OsaurusAI/Qwen-Image-mflux-4bit)"
            for line in lines
        )
        # z-image-turbo is not edit-capable — must not appear at all.
        assert not any("z-image-turbo" in line for line in lines)


class TestSingleFlightLockEdit:
    """Issue #143 — the edit wrapper nests the SAME two locks, in the
    SAME order, as generate (reused directly via the flat import)."""

    def test_no_lock_flag_skips_both_locks(self, tmp_path, base_image):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)], no_lock=True)
        with patch("edit_image._single_flight_lock") as mock_lock, \
             patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", return_value=success_result()):
            edit_image.edit(args)
        mock_lock.assert_not_called()

    def test_lock_acquisition_order_ollama_first(self, tmp_path, base_image):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)], no_lock=False)
        order = []

        @contextmanager
        def fake_lock(lock_path, timeout_seconds):
            order.append(lock_path)
            yield 0

        with patch("edit_image._single_flight_lock", fake_lock), \
             patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", return_value=success_result()):
            edit_image.edit(args)

        assert order == [edit_image.OLLAMA_LOCK_PATH, edit_image.LOCK_PATH]

    def test_default_invocation_acquires_and_releases_both_locks(self, tmp_path, base_image):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)], no_lock=False)
        events = []

        @contextmanager
        def fake_lock(lock_path, timeout_seconds):
            events.append(("acquire", lock_path))
            try:
                yield 0
            finally:
                events.append(("release", lock_path))

        with patch("edit_image._single_flight_lock", fake_lock), \
             patch("edit_image.shutil.which", return_value="/usr/bin/x"), \
             patch("edit_image.subprocess.run", return_value=success_result()):
            edit_image.edit(args)

        assert events == [
            ("acquire", edit_image.OLLAMA_LOCK_PATH),
            ("acquire", edit_image.LOCK_PATH),
            ("release", edit_image.LOCK_PATH),
            ("release", edit_image.OLLAMA_LOCK_PATH),
        ]

    def test_lock_acquisition_timeout_exits(self, tmp_path, base_image, capsys):
        output = tmp_path / "out.png"
        args = make_args(output=str(output), image_paths=[str(base_image)], no_lock=False, lock_wait_timeout=1)

        @contextmanager
        def fake_lock(lock_path, timeout_seconds):
            raise TimeoutError(
                f"Could not acquire MLX single-flight lock at {lock_path} "
                f"within {timeout_seconds}s. Another local image generation "
                f"is in progress; serialise your callers or use cloud "
                f"generation for parallelism."
            )
            yield  # noqa: unreachable, satisfies decorator shape

        with patch("edit_image._single_flight_lock", fake_lock):
            with pytest.raises(SystemExit) as exc_info:
                edit_image.edit(args)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "single-flight lock" in captured.err
