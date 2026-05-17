"""Paperbanana dispatch helper — academic_figure routing (paperbanana E2).

When the strategy classifier (paperbanana E1, ``strategy_classifier.py``)
labels a slide ``"academic_figure"``, the imagegen-bridge routes the
image-generation step through paperbanana's
``paperbanana:generate-diagram`` skill instead of the regular cloud
image path. This module is the **testable boundary** for that
dispatch — the Skill invocation itself happens inside SKILL.md by
Claude, but everything around it (availability detection, args
assembly, fallback decision, manifest shape) is pure-Python and
covered by unit tests.

Design goals:

- **Pure functions**: availability detection accepts an explicit
  ``env`` mapping and ``fs_exists`` callable so tests can mock both
  without monkey-patching ``os``.
- **Graceful fallback**: when paperbanana is not detected, return a
  fallback payload describing the cloud-image dispatch the bridge
  should run instead, plus a ``fallback_reason`` for the manifest /
  audit log.
- **Manifest stability**: ``build_manifest_entry`` produces the exact
  shape the bridge writes to ``image-manifest.json`` so downstream
  consumers (production-upgrade-plan, QA checks) can identify slides
  that went through paperbanana.

See also:
    docs/superpowers/plans/2026-05-17-v1.4-push-and-paperbanana.md §6.5 E2
    plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md — academic_figure branch
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping


# Canonical skill name dispatched when paperbanana is reachable.
PAPERBANANA_SKILL_NAME = "paperbanana:generate-diagram"

# Environment variable an operator can set to point at a paperbanana
# install outside the standard Claude plugin cache (e.g. development
# checkout). The value is a directory containing
# ``.claude-plugin/plugin.json``.
PAPERBANANA_ROOT_ENV = "PAPERBANANA_ROOT"

# Standard locations the Claude Code plugin manager extracts plugins to.
# Searched in order; the first match wins.
_DEFAULT_SEARCH_ROOTS: tuple[str, ...] = (
    "~/.claude/plugins/cache",
    "~/.claude/plugins",
)


@dataclass
class PaperbananaDispatch:
    """Result of building an imagegen dispatch for an academic_figure slide.

    Attributes:
        available: whether paperbanana was detected. When False, the
            bridge MUST take the cloud fallback path (see
            ``fallback_provider`` / ``fallback_model``).
        skill: the Claude Code skill name to invoke when available.
            Empty string when ``available`` is False.
        args: argument mapping passed to the dispatched skill. Empty
            when ``available`` is False.
        slide_number: 1-based slide index, copied from the slide dict.
        output_path: where the bridge expects paperbanana to write the
            rendered figure (or the cloud fallback to write its PNG).
        fallback_provider: cloud provider to use when paperbanana is
            absent. ``"google"`` by default.
        fallback_model: cloud model to use when paperbanana is absent.
            ``"gemini-3.1-flash-image-preview"`` (Nano Banana Flash 1K)
            by default — the cheapest tier that handles complex text.
        fallback_reason: human-readable explanation when ``available``
            is False. Empty when paperbanana was found.
    """

    available: bool
    slide_number: int
    output_path: str
    skill: str = ""
    args: dict = field(default_factory=dict)
    fallback_provider: str = "google"
    fallback_model: str = "gemini-3.1-flash-image-preview"
    fallback_reason: str = ""


def is_paperbanana_available(
    *,
    env: Mapping[str, str] | None = None,
    fs_exists: Callable[[Path], bool] | None = None,
) -> bool:
    """Return True when the paperbanana plugin is reachable.

    The check is filesystem-only — we look for
    ``<root>/paperbanana/.claude-plugin/plugin.json`` under one of:

    1. ``$PAPERBANANA_ROOT`` (operator override, points directly at the
       plugin directory).
    2. ``~/.claude/plugins/cache/<source>/paperbanana/``.
    3. ``~/.claude/plugins/paperbanana/``.

    Args:
        env: mapping to consult for env vars. Defaults to ``os.environ``.
            Injected for tests.
        fs_exists: predicate that returns True when a path exists. Defaults
            to ``Path.exists``. Injected for tests.
    """
    env = env if env is not None else os.environ
    fs_exists = fs_exists if fs_exists is not None else Path.exists

    override = env.get(PAPERBANANA_ROOT_ENV)
    if override:
        manifest = Path(override).expanduser() / ".claude-plugin" / "plugin.json"
        if fs_exists(manifest):
            return True

    for root_str in _DEFAULT_SEARCH_ROOTS:
        root = Path(root_str).expanduser()
        # Direct install path: <root>/paperbanana/.claude-plugin/plugin.json
        direct = root / "paperbanana" / ".claude-plugin" / "plugin.json"
        if fs_exists(direct):
            return True
        # Marketplace cache path: <root>/<source>/paperbanana/.claude-plugin/plugin.json
        # We can't enumerate without listing the directory, so only the
        # direct shape is supported by the offline check. Operators using
        # marketplace cache layouts should set $PAPERBANANA_ROOT.

    return False


def _slide_subject_text(slide: Mapping) -> str:
    """Extract the descriptive text from a slide dict.

    Falls back through common outline shapes so this works whether the
    caller passes a raw outline slide or a richer object.
    """
    for key in ("visual_direction", "headline", "title"):
        value = slide.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    body = slide.get("body_points")
    if isinstance(body, list) and body:
        return " · ".join(str(point) for point in body if point)

    return ""


def build_dispatch_payload(
    slide: Mapping,
    *,
    output_dir: str,
    style_guide: Mapping | None = None,
    paperbanana_available: bool | None = None,
    availability_env: Mapping[str, str] | None = None,
    fs_exists: Callable[[Path], bool] | None = None,
) -> PaperbananaDispatch:
    """Build the dispatch payload for an ``academic_figure`` slide.

    Args:
        slide: the outline slide dict. Must contain ``slide_number`` and
            at least one of ``visual_direction`` / ``headline`` /
            ``title`` / ``body_points``.
        output_dir: directory where the resulting PNG / SVG should land.
            Typically ``./tmp/deck/images``.
        style_guide: optional StyleGuide dict — palette hexes are passed
            through to paperbanana so the figure picks up brand colours.
        paperbanana_available: short-circuit the availability check
            (used by callers who have already detected paperbanana, e.g.
            the verify-skill helper).
        availability_env / fs_exists: forwarded to
            ``is_paperbanana_available`` when ``paperbanana_available``
            is None.

    Returns:
        A ``PaperbananaDispatch``. When paperbanana is available, ``skill``
        and ``args`` are populated. Otherwise ``fallback_provider`` /
        ``fallback_model`` describe the cloud dispatch the bridge should
        run instead, and ``fallback_reason`` carries the audit-log line.
    """
    slide_number = int(slide.get("slide_number", 0))
    subject = _slide_subject_text(slide)
    suffix = "fig" if subject else "figure"
    output_path = str(
        Path(output_dir) / f"slide-{slide_number:02d}-academic-{suffix}.png"
    )

    if paperbanana_available is None:
        paperbanana_available = is_paperbanana_available(
            env=availability_env,
            fs_exists=fs_exists,
        )

    if not paperbanana_available:
        return PaperbananaDispatch(
            available=False,
            slide_number=slide_number,
            output_path=output_path,
            fallback_reason=(
                "paperbanana plugin not detected — falling back to "
                "Nano Banana Flash 1K with academic-figure-aware prompting; "
                "install paperbanana for publication-quality figures"
            ),
        )

    palette: list[str] = []
    if isinstance(style_guide, Mapping):
        candidate = style_guide.get("palette") or {}
        if isinstance(candidate, Mapping):
            for key in ("primary", "accent", "background", "ink"):
                hex_value = candidate.get(key)
                if isinstance(hex_value, str) and hex_value.startswith("#"):
                    palette.append(hex_value)

    args: dict = {
        "subject": subject,
        "output_path": output_path,
        "slide_number": slide_number,
        "context": "deck-figure",
    }
    if palette:
        args["palette_hex"] = palette

    return PaperbananaDispatch(
        available=True,
        slide_number=slide_number,
        output_path=output_path,
        skill=PAPERBANANA_SKILL_NAME,
        args=args,
    )


def build_manifest_entry(
    dispatch: PaperbananaDispatch,
    *,
    dispatch_succeeded: bool,
    content_hash: str | None = None,
    error: str | None = None,
) -> dict:
    """Build the ``image-manifest`` entry for an academic_figure slide.

    Args:
        dispatch: the result of ``build_dispatch_payload``.
        dispatch_succeeded: whether paperbanana (or the fallback cloud
            call, if paperbanana was unavailable) produced the image.
        content_hash: sha256 of the rendered file when generation
            succeeded. ``None`` when generation failed / was skipped.
        error: short error string when ``dispatch_succeeded`` is False.

    Returns:
        A dict shaped like other image-manifest entries (slide_number,
        file_path, status, source_prompt, ...). The ``source_prompt``
        field carries the paperbanana subject string (or the fallback
        prompt) so downstream production upgrades can re-render.
    """
    if dispatch.available:
        backend = "paperbanana"
        model_used = PAPERBANANA_SKILL_NAME
        source_prompt = dispatch.args.get("subject", "")
    else:
        backend = "cloud_fallback"
        model_used = dispatch.fallback_model
        source_prompt = dispatch.args.get("subject", "")  # fallback path leaves args empty

    status = "generated" if dispatch_succeeded else "failed"

    entry: dict = {
        "slide_number": dispatch.slide_number,
        "file_path": dispatch.output_path,
        "status": status,
        "image_id": f"slide-{dispatch.slide_number:02d}-academic-figure",
        "model_used": model_used,
        "backend": backend,
        "source_prompt": source_prompt,
    }
    if content_hash is not None:
        entry["content_hash"] = content_hash
    if not dispatch.available:
        entry["fallback_reason"] = dispatch.fallback_reason
    if error is not None:
        entry["error"] = error
    return entry
