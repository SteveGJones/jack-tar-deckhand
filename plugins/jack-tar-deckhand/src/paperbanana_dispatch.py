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

import re
from dataclasses import dataclass, field
from typing import Mapping


# Paperbanana writes run outputs to ``<output_dir>/run_<YYYYMMDD>_<HHMMSS>_<short-hash>/``.
# We extract the run-id directory name from manifest paths so iterate-slide (#89)
# can call ``paperbanana generate --continue-run <id> --feedback ...`` for cheap
# critique-driven refinement instead of re-running from scratch.
_RUN_ID_PATTERN = re.compile(r"/(run_\d{8}_\d{6}_[a-f0-9]+)/")


@dataclass
class PaperbananaDispatch:
    """Result of building an imagegen dispatch for an academic_figure slide.

    Attributes:
        available: whether paperbanana was detected. When False, the
            bridge MUST take the cloud fallback path (see
            ``fallback_provider`` / ``fallback_model``).
        slide_number: 1-based slide index, copied from the slide dict.
            Stays on the struct (not in ``args``) for manifest accounting.
        args: argument mapping the bridge passes through to the
            ``paperbanana generate`` CLI invocation. Shape:
            ``{source_context, caption, aspect_ratio, iterations}``.
            Empty when ``available`` is False.
        output_dir: directory the bridge passes as ``paperbanana generate
            --output <dir>``. Paperbanana writes its run directory inside
            this dir (``<output_dir>/run_<ts>_<hash>/final_output.png``);
            the caller does NOT control the run-id subdirectory name or
            the final filename. See spike report §3 / ADR-v2 §4.
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
    output_dir: str
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


_MIN_SOURCE_CONTEXT_NOTES_CHARS = 200


def _build_source_context_from_slide(slide: Mapping) -> str:
    """Synthesise a methodology paragraph for paperbanana's Retriever agent.

    Paperbanana's pipeline (Retriever → Planner → Stylist → Visualizer →
    Critic) expects ~5–20 sentences of paper-style methodology prose
    describing what the figure should depict. A slide headline is too
    thin; the spike confirmed thin source_context produces lower-quality
    figures (the Retriever can't surface relevant exemplars).

    Priority order (first non-empty wins):

    1. ``slide["methodology_context"]`` — explicit operator pre-annotation
       on the outline. Best signal when the speaker has thought about it.
    2. ``slide["speaker_notes"]`` — when ≥200 chars, this is typically a
       paragraph or two and works well as methodology context.
    3. ``visual_direction + body_points`` joined into prose. Last-resort
       synthesis from whatever slide content exists.
    4. ``headline`` / ``title`` — produces a thin source_context (and
       thinner figures). Surfaced for graceful degradation, not as a
       happy path.

    Returns the empty string only when the slide has none of the above.
    """
    explicit = slide.get("methodology_context")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()

    notes = slide.get("speaker_notes")
    if isinstance(notes, str) and len(notes.strip()) >= _MIN_SOURCE_CONTEXT_NOTES_CHARS:
        return notes.strip()

    parts: list[str] = []
    visual_direction = slide.get("visual_direction")
    if isinstance(visual_direction, str) and visual_direction.strip():
        parts.append(visual_direction.strip())

    body = slide.get("body_points")
    if isinstance(body, list) and body:
        parts.extend(str(point).strip() for point in body if point)

    if parts:
        # Naive sentence-joining; paperbanana's Retriever is robust to
        # imperfect prose, and we'd rather pass the operator's actual
        # words than risk rewriting them.
        return ". ".join(parts).rstrip(".") + "."

    for key in ("headline", "title"):
        value = slide.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return ""


def _build_caption_from_slide(slide: Mapping) -> str:
    """Extract the figure caption — paperbanana's ``caption`` arg.

    Paperbanana distinguishes ``source_context`` (the methodology — what
    the system does) from ``caption`` (the communicative intent — what
    the figure should depict / what the reader should take away). The
    Stylist + Critic agents both consume caption directly.

    Priority order: explicit ``caption`` field, then ``headline``, then
    ``title``, then the first body point.
    """
    for key in ("caption", "headline", "title"):
        value = slide.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    body = slide.get("body_points")
    if isinstance(body, list) and body:
        first = body[0]
        if first:
            return str(first).strip()

    return ""


def build_dispatch_payload(
    slide: Mapping,
    *,
    output_dir: str,
    paperbanana_available: bool | None = None,
) -> PaperbananaDispatch:
    """Build the dispatch payload for an ``academic_figure`` slide.

    The returned ``PaperbananaDispatch`` carries the args the bridge
    will pass to ``paperbanana generate`` via subprocess (CLI transport;
    see ADR-v2 §4). When paperbanana is unavailable, ``args`` is empty
    and ``fallback_provider`` / ``fallback_model`` describe the cloud
    fallback dispatch the bridge should run instead.

    Args:
        slide: the outline slide dict. Must contain ``slide_number``.
            For useful figure generation, also needs one or more of
            ``methodology_context`` / ``speaker_notes`` / ``body_points``
            / ``visual_direction`` to feed paperbanana's ``source_context``
            arg, and one of ``caption`` / ``headline`` / ``title`` for
            paperbanana's ``caption`` arg.
        output_dir: directory the bridge passes as ``--output <dir>`` to
            ``paperbanana generate``. Paperbanana writes its run directory
            INSIDE this dir; the caller does not control the run-id
            subdirectory name or the final filename. See spike §3.
        paperbanana_available: short-circuit the availability check
            (used by callers who have already detected paperbanana, e.g.
            the verify-skill helper). When None, calls
            ``is_paperbanana_available()`` to decide.

    Returns:
        A ``PaperbananaDispatch``. When paperbanana is available, ``args``
        carries the four-key real contract. Otherwise ``fallback_*``
        fields describe the Nano Banana Flash 1K fallback dispatch.
    """
    slide_number = int(slide.get("slide_number", 0))

    if paperbanana_available is None:
        paperbanana_available = is_paperbanana_available()

    if not paperbanana_available:
        return PaperbananaDispatch(
            available=False,
            slide_number=slide_number,
            output_dir=output_dir,
            fallback_reason=(
                "paperbanana CLI not on PATH and paperbanana package not "
                "importable — falling back to Nano Banana Flash 1K with "
                "academic-figure-aware prompting. Install paperbanana via "
                "`pip install 'paperbanana[google]'` for publication-tier "
                "output. See /jack-tar-deckhand:verify for guidance."
            ),
        )

    args: dict = {
        "source_context": _build_source_context_from_slide(slide),
        "caption": _build_caption_from_slide(slide),
        "aspect_ratio": "16:9",
        "iterations": int(slide.get("paperbanana_iterations", 1)),
    }

    return PaperbananaDispatch(
        available=True,
        slide_number=slide_number,
        output_dir=output_dir,
        args=args,
    )


def _extract_run_id(output_path: str) -> str:
    """Parse paperbanana's run_id from a final output path.

    Paperbanana writes outputs as
    ``<output_dir>/run_<YYYYMMDD>_<HHMMSS>_<short-hash>/final_output.png``
    (or ``.mcp.jpg`` when MCP transport re-compresses PNGs >3.75 MB —
    spike §9.3). This returns the ``run_<ts>_<hash>`` directory name so
    iterate-slide (#89) can call
    ``paperbanana generate --continue-run <id> --feedback ...`` for
    cheap critique-driven refinement.

    Returns the empty string when the path doesn't match the expected
    pattern — for example, the cloud-fallback path writes to a
    jack-tar-managed location with no paperbanana run-id.
    """
    match = _RUN_ID_PATTERN.search(output_path)
    return match.group(1) if match else ""


def build_manifest_entry(
    dispatch: PaperbananaDispatch,
    *,
    dispatch_succeeded: bool,
    output_path: str,
    content_hash: str | None = None,
    error: str | None = None,
) -> dict:
    """Build the ``image-manifest`` entry for an academic_figure slide.

    Args:
        dispatch: the result of ``build_dispatch_payload``.
        dispatch_succeeded: whether paperbanana (or the fallback cloud
            call, if paperbanana was unavailable) produced the image.
        output_path: the actual file paperbanana (or the fallback) wrote.
            For paperbanana, this is ``<output_dir>/run_<ts>_<hash>/
            final_output.png`` (or ``.mcp.jpg``) — the caller is
            responsible for parsing paperbanana's stdout / scanning the
            run directory to find this path. For the cloud fallback,
            this is the jack-tar-conventional path the bridge wrote.
        content_hash: sha256 of the rendered file when generation
            succeeded. ``None`` when generation failed / was skipped.
        error: short error string when ``dispatch_succeeded`` is False.

    Returns:
        A dict shaped like other image-manifest entries:
        ``slide_number``, ``file_path``, ``status``, ``image_id``,
        ``model_used``, ``backend``, ``source_prompt`` (methodology
        text), ``caption`` (figure caption), plus paperbanana-specific
        ``paperbanana_run_id`` and ``paperbanana_args`` when available.
        ``source_prompt`` carries the methodology text, ``caption``
        carries the communicative intent — distinct fields because
        iterate-slide (#89) needs both to re-call paperbanana with the
        same semantic input.
    """
    if dispatch.available:
        backend = "paperbanana"
        model_used = "paperbanana"
    else:
        backend = "cloud_fallback"
        model_used = dispatch.fallback_model

    status = "generated" if dispatch_succeeded else "failed"

    entry: dict = {
        "slide_number": dispatch.slide_number,
        "file_path": output_path,
        "status": status,
        "image_id": f"slide-{dispatch.slide_number:02d}-academic-figure",
        "model_used": model_used,
        "backend": backend,
        "source_prompt": dispatch.args.get("source_context", ""),
        "caption": dispatch.args.get("caption", ""),
    }
    if content_hash is not None:
        entry["content_hash"] = content_hash
    if dispatch.available:
        run_id = _extract_run_id(output_path)
        if run_id:
            entry["paperbanana_run_id"] = run_id
        # Full args dict so iterate-slide can re-call with the same
        # semantic input via --continue-run + --feedback.
        entry["paperbanana_args"] = dict(dispatch.args)
    else:
        entry["fallback_reason"] = dispatch.fallback_reason
    if error is not None:
        entry["error"] = error
    return entry
