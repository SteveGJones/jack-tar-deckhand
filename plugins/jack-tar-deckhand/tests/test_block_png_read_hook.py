"""Tests for the discipline hook that blocks Read on image files.

Issue #76 — auto-installed PreToolUse hook (declared in
plugins/jack-tar-deckhand/.claude-plugin/plugin.json) enforces the
"never Read PNGs into orchestration context" rule that the
2026-05-07 blog-post asset run violated.

The hook is a bash script under plugins/jack-tar-deckhand/hooks/.
These tests invoke it as a subprocess with simulated Claude Code
hook-protocol JSON payloads on stdin and assert the exit code +
stderr contents.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


HOOK_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "hooks"
    / "block-png-read.sh"
)


def run_hook(file_path: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Invoke the hook with a simulated Read tool input."""
    payload = json.dumps({"tool_input": {"file_path": file_path}})
    real_env = os.environ.copy()
    if env:
        real_env.update(env)
    # Strip ALLOW_PNG_READ unless explicitly set by the test, so the
    # operator's session env doesn't leak into the test.
    if env is None or "ALLOW_PNG_READ" not in env:
        real_env.pop("ALLOW_PNG_READ", None)
    return subprocess.run(
        [str(HOOK_SCRIPT)],
        input=payload,
        text=True,
        capture_output=True,
        env=real_env,
    )


def test_hook_script_exists_and_is_executable():
    assert HOOK_SCRIPT.is_file(), f"missing hook script: {HOOK_SCRIPT}"
    assert os.access(HOOK_SCRIPT, os.X_OK), f"hook script not executable: {HOOK_SCRIPT}"


@pytest.mark.parametrize("ext", [
    ".png", ".PNG", ".Png",
    ".jpg", ".JPG", ".jpeg", ".JPEG",
    ".gif", ".GIF",
    ".webp", ".WEBP",
    ".bmp", ".BMP",
    ".tif", ".tiff", ".TIFF",
])
def test_hook_blocks_image_extensions(ext):
    """All image extensions, case-insensitive, must block."""
    result = run_hook(f"/tmp/foo{ext}")
    assert result.returncode == 1, (
        f"expected exit 1 for {ext}, got {result.returncode}. stderr: {result.stderr!r}"
    )
    assert "BLOCKED" in result.stderr, (
        f"expected BLOCKED in stderr for {ext}; got {result.stderr!r}"
    )


def test_hook_passes_non_image_files():
    """Read on non-image files must pass through (exit 0)."""
    result = run_hook("/tmp/foo.md")
    assert result.returncode == 0, f"unexpected non-zero exit: {result.stderr!r}"


@pytest.mark.parametrize("path", [
    "/tmp/notes.md",
    "/etc/hosts",
    "/var/log/system.log",
    "src/generate_image.py",
    "package.json",
    "/tmp/data.csv",
    "/tmp/output.txt",
])
def test_hook_passes_various_non_image_paths(path):
    result = run_hook(path)
    assert result.returncode == 0, (
        f"non-image path {path} should pass; got exit {result.returncode}, "
        f"stderr: {result.stderr!r}"
    )


def test_hook_bypass_via_allow_png_read_env():
    """ALLOW_PNG_READ=1 in env bypasses the block — the documented escape
    for cases where the image IS the user-facing answer."""
    result = run_hook("/tmp/foo.png", env={"ALLOW_PNG_READ": "1"})
    assert result.returncode == 0, (
        f"ALLOW_PNG_READ=1 should bypass; got exit {result.returncode}, "
        f"stderr: {result.stderr!r}"
    )


def test_hook_bypass_only_with_explicit_one():
    """ALLOW_PNG_READ must be exactly '1' to bypass — other truthy values
    do NOT count as the operator's deliberate signal."""
    for falsey in ["", "0", "true", "yes"]:
        result = run_hook("/tmp/foo.png", env={"ALLOW_PNG_READ": falsey})
        assert result.returncode == 1, (
            f"ALLOW_PNG_READ={falsey!r} must NOT bypass; got exit {result.returncode}"
        )


def test_hook_handles_malformed_json_gracefully():
    """If the harness sends malformed JSON the hook does not block — let
    the tool call through and let downstream layers report the
    malformation. Defensive: a buggy hook that hard-fails on every Read
    would brick the session."""
    result = subprocess.run(
        [str(HOOK_SCRIPT)],
        input="not valid json {{{",
        text=True,
        capture_output=True,
        env={k: v for k, v in os.environ.items() if k != "ALLOW_PNG_READ"},
    )
    assert result.returncode == 0, (
        f"malformed JSON should pass through; got exit {result.returncode}, "
        f"stderr: {result.stderr!r}"
    )


def test_hook_handles_missing_file_path_field():
    """If tool_input has no file_path, treat as non-image and pass through."""
    result = subprocess.run(
        [str(HOOK_SCRIPT)],
        input=json.dumps({"tool_input": {}}),
        text=True,
        capture_output=True,
        env={k: v for k, v in os.environ.items() if k != "ALLOW_PNG_READ"},
    )
    assert result.returncode == 0


def test_hook_block_message_names_alternatives():
    """The block message must point operators at the right remediation —
    the image-reviewer agent + general-purpose agent. This is the
    discoverable-rule property the hook exists to deliver."""
    result = run_hook("/tmp/foo.png")
    assert "image-reviewer" in result.stderr, (
        "block message must mention the image-reviewer agent"
    )
    assert "general-purpose" in result.stderr, (
        "block message must mention the general-purpose agent fallback"
    )
    assert "ALLOW_PNG_READ" in result.stderr, (
        "block message must document the bypass mechanism"
    )


def test_plugin_manifest_declares_pretooluse_hook():
    """Issue #76 — confirm the plugin.json manifest registers the hook so
    Claude Code auto-installs it on plugin enable. Without this
    declaration, the hook script exists but never fires."""
    manifest_path = (
        Path(__file__).resolve().parents[1]
        / ".claude-plugin"
        / "plugin.json"
    )
    manifest = json.loads(manifest_path.read_text())
    hooks = manifest.get("hooks", {})
    pre_tool_use = hooks.get("PreToolUse", [])
    assert pre_tool_use, "manifest must declare hooks.PreToolUse for issue #76"

    read_matchers = [h for h in pre_tool_use if h.get("matcher") == "Read"]
    assert read_matchers, "manifest must include a Read-matcher in PreToolUse"

    # The hook entry references our script via CLAUDE_PLUGIN_ROOT.
    found_block_png = False
    for matcher in read_matchers:
        for inner in matcher.get("hooks", []):
            cmd = inner.get("command", "")
            if "block-png-read.sh" in cmd:
                found_block_png = True
                assert inner.get("type") == "command", (
                    "hook entry must declare type='command'"
                )
                assert "${CLAUDE_PLUGIN_ROOT}" in cmd, (
                    "hook command must reference ${CLAUDE_PLUGIN_ROOT} for portability"
                )
                break
    assert found_block_png, (
        "manifest must reference plugins/jack-tar-deckhand/hooks/block-png-read.sh"
    )
