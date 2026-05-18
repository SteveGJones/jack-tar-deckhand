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

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping


# Canonical skill name dispatched when paperbanana is reachable.
# NOTE: vestigial in Task 1 — build_dispatch_payload still references it.
# Task 2 switches the dispatch transport to CLI subprocess, at which point
# this constant gets removed entirely.
PAPERBANANA_SKILL_NAME = "paperbanana:generate-diagram"


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


def is_paperbanana_available() -> bool:
    """Return True when the paperbanana CLI or Python package is runnable.

    Paperbanana is treated as an external CLI tool (like LaTeX or
    ImageMagick), not as a Claude Code plugin. The operator installs it
    via ``pip install 'paperbanana[google]'`` (in jack-tar's venv),
    ``pipx install 'paperbanana[google]'`` (globally), or ``uvx`` (MCP
    server transport, v1.4.1+ candidate). jack-tar shells out on demand.

    Detection probes runnability, not installation marker:

    1. ``importlib.util.find_spec("paperbanana")`` — covers pip-installed
       in jack-tar's venv (the common case for v1.4 E6 dogfood).
    2. ``shutil.which("paperbanana")`` — covers pipx, system install, and
       any case where the CLI is on PATH but the Python package isn't on
       jack-tar's ``sys.path``.

    Either check returning True is sufficient. See
    ``docs/architecture/paperbanana-integration-v2.md`` for the full
    framing rationale.
    """
    import importlib.util
    import shutil

    if importlib.util.find_spec("paperbanana") is not None:
        return True
    return shutil.which("paperbanana") is not None


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
        # availability_env and fs_exists params are vestigial after Task 1 —
        # is_paperbanana_available() is now zero-arg. The params survive on
        # build_dispatch_payload's signature only until Task 2 rewrites this
        # function end-to-end against the real contract.
        paperbanana_available = is_paperbanana_available()

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
