"""Loader picks the highest-version cache install when multiple are present.

Run 8 Finding #27: ``/reload-plugins`` re-created an obsolete cache version
of jack-tar-msft-smartart (1.1.0 came back even after deletion), and the
loader's ``_candidate_roots()`` rglob-iteration order returned 1.1.0 first
on some filesystems. ``apply_enrichment`` then picked up the older catalog
and crashed on prose-length bullets that v0.1.2 was supposed to support.

The fix sorts cache matches by semantic version and prefers the highest.
This test populates a temporary cache with two versions of the plugin
manifest and asserts the loader picks the newer one regardless of
filesystem ordering.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.msft_smartart_loader import _candidate_roots, _semver_tuple


def _write_plugin_manifest(plugin_root: Path, name: str, version: str) -> None:
    """Write a minimal .claude-plugin/plugin.json + src/engine.py at plugin_root.

    The loader's discovery requires both files; engine.py is what
    distinguishes a real plugin install from a stub.
    """
    (plugin_root / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    manifest = {"name": name, "version": version}
    (plugin_root / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(manifest, indent=2)
    )
    (plugin_root / "src").mkdir(exist_ok=True)
    (plugin_root / "src" / "engine.py").write_text(
        "# stub engine module for loader test\n"
    )


def test_semver_tuple_basic() -> None:
    """Numeric segments parse cleanly."""
    assert _semver_tuple("1.2.0") == (1, 2, 0)
    assert _semver_tuple("1.2.10") == (1, 2, 10)
    assert _semver_tuple("0.1.2") == (0, 1, 2)
    assert _semver_tuple("10.0.0") == (10, 0, 0)


def test_semver_tuple_handles_prerelease_suffix() -> None:
    """``1.2.0-alpha`` parses as ``(1, 2, 0)``; the prerelease segment is dropped."""
    assert _semver_tuple("1.2.0-alpha") == (1, 2, 0)
    assert _semver_tuple("1.2.0+build.5") == (1, 2, 0)


def test_semver_tuple_handles_unparseable() -> None:
    """Garbled segments sort to zero so they don't accidentally win."""
    assert _semver_tuple("garbage") == (0,)
    assert _semver_tuple("1.junk.3") == (1, 0, 3)


def test_semver_ordering_picks_highest() -> None:
    """``(1, 2, 1)`` sorts above ``(1, 1, 0)``."""
    versions = [
        _semver_tuple("1.1.0"),
        _semver_tuple("1.2.1"),
        _semver_tuple("1.2.0"),
    ]
    assert max(versions) == (1, 2, 1)


def test_loader_picks_highest_cache_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run 8 Finding #27 regression test.

    Populate a temporary cache root with two versions of the msft-smartart
    plugin manifest (1.1.0 and 1.2.1) and assert the loader picks 1.2.1
    regardless of filesystem ordering.
    """
    fake_home = tmp_path
    cache_root = fake_home / ".claude" / "plugins" / "cache" / "jack-tar"

    older_root = cache_root / "jack-tar-msft-smartart" / "1.1.0"
    newer_root = cache_root / "jack-tar-msft-smartart" / "1.2.1"
    _write_plugin_manifest(older_root, "jack-tar-msft-smartart", "1.1.0")
    _write_plugin_manifest(newer_root, "jack-tar-msft-smartart", "1.2.1")

    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.delenv("JACK_TAR_SUPERPOWER_BRIDGE_FORCE_MSFT_ROOT", raising=False)
    # Move cwd somewhere clean so the local-dev fallback doesn't pick up the
    # repo's plugins/ tree alongside the temp cache.
    monkeypatch.chdir(tmp_path)

    roots = _candidate_roots()
    # The cache match is the first candidate; assert it's the newer version.
    assert len(roots) >= 1
    assert roots[0] == newer_root, (
        f"Loader should pick {newer_root} (1.2.1) but picked {roots[0]}. "
        f"Run 8 Finding #27: when /reload-plugins re-creates obsolete versions, "
        f"the loader must prefer the highest semver match."
    )


def test_loader_handles_single_cache_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When only one cache version is present, the loader picks it (baseline)."""
    fake_home = tmp_path
    cache_root = fake_home / ".claude" / "plugins" / "cache" / "jack-tar"
    only_root = cache_root / "jack-tar-msft-smartart" / "1.2.1"
    _write_plugin_manifest(only_root, "jack-tar-msft-smartart", "1.2.1")

    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.delenv("JACK_TAR_SUPERPOWER_BRIDGE_FORCE_MSFT_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)

    roots = _candidate_roots()
    assert len(roots) >= 1
    assert roots[0] == only_root


def test_loader_handles_unparseable_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Garbled plugin.json doesn't crash discovery — its version sorts to 0.

    A real working manifest at a valid version still wins.
    """
    fake_home = tmp_path
    cache_root = fake_home / ".claude" / "plugins" / "cache" / "jack-tar"

    bad_root = cache_root / "jack-tar-msft-smartart" / "1.0.0-bad"
    bad_root.mkdir(parents=True, exist_ok=True)
    (bad_root / ".claude-plugin").mkdir()
    (bad_root / ".claude-plugin" / "plugin.json").write_text("not json{{{")
    (bad_root / "src").mkdir()
    (bad_root / "src" / "engine.py").write_text("# stub\n")

    good_root = cache_root / "jack-tar-msft-smartart" / "1.2.1"
    _write_plugin_manifest(good_root, "jack-tar-msft-smartart", "1.2.1")

    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.delenv("JACK_TAR_SUPERPOWER_BRIDGE_FORCE_MSFT_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)

    roots = _candidate_roots()
    assert roots[0] == good_root, (
        f"Loader should fall through unparseable manifest to the working {good_root}, "
        f"but picked {roots[0]}"
    )


def test_force_env_var_overrides_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The FORCE_MSFT_ROOT env var short-circuits cache discovery (existing contract)."""
    fake_home = tmp_path
    cache_root = fake_home / ".claude" / "plugins" / "cache" / "jack-tar"
    only_root = cache_root / "jack-tar-msft-smartart" / "1.2.1"
    _write_plugin_manifest(only_root, "jack-tar-msft-smartart", "1.2.1")

    forced_path = tmp_path / "forced-elsewhere"
    forced_path.mkdir()

    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.setenv("JACK_TAR_SUPERPOWER_BRIDGE_FORCE_MSFT_ROOT", str(forced_path))

    roots = _candidate_roots()
    assert roots == [forced_path], (
        f"FORCE env var should win. Got {roots}, expected [{forced_path}]"
    )
