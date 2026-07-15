"""Paperbanana dispatch helper — academic_figure routing.

When the strategy classifier (``strategy_classifier.py``) labels a slide
``"academic_figure"``, the imagegen-bridge routes the image-generation
step through the **paperbanana CLI via subprocess** instead of the
regular cloud image path. This module is the **testable boundary** for
that dispatch — the subprocess call itself happens inside SKILL.md by
Claude, but everything around it (availability detection, args
assembly, fallback decision, manifest shape) is pure-Python and covered
by unit tests.

Local-first tier (2026-07-10): when a local Ollama instance carries an
image-capable model (``x/flux2-klein``, ``x/z-image-turbo``), the
dispatch routes the FIRST render through Ollama at $0 — consistent with
the F10 operator gate at every free→cost transition. Paperbanana (when
installed) and the Nano Banana cloud fallback become paid escalation
tiers behind explicit operator go-ahead. The ``LocalBackend`` seam is
provider-shaped so an MLX backend can slot in later without touching
the ladder logic.

Paperbanana is treated as an **external CLI tool** (like LaTeX or
ImageMagick), not as a Claude Code plugin. Operators install it via
``pip install 'paperbanana[google]'`` (or ``pipx`` / ``uvx``). See
``docs/architecture/paperbanana-integration-v2.md`` for the full
framing rationale.

Design goals:

- **Pure functions**: helpers accept explicit ``slide`` Mappings and
  return data structures; no I/O. ``is_paperbanana_available`` probes
  runnability (``find_spec`` + ``shutil.which``); easy to verify against
  a real venv.
- **Graceful fallback**: when paperbanana is not runnable, return a
  fallback payload describing the cloud-image dispatch the bridge
  should run instead, plus a ``fallback_reason`` for the manifest /
  audit log.
- **Manifest stability**: ``build_manifest_entry`` produces the exact
  shape the bridge writes to ``image-manifest.json`` so downstream
  consumers (production-upgrade-plan, QA checks, iterate-slide via
  ``paperbanana_run_id``) can identify and re-invoke slides that went
  through paperbanana.

See also:
    docs/architecture/paperbanana-integration-v2.md
    docs/superpowers/plans/2026-05-18-paperbanana-dispatch-refactor.md
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

# Default Ollama endpoint. The bridge may override via detect_local_backend's
# base_url arg if the operator runs Ollama elsewhere.
OLLAMA_BASE_URL = "http://localhost:11434"

# Image-capable Ollama model families, in quality-priority order for
# academic figures, from the catalog's local_draft role preference list
# (EPIC #125). flux2-klein (FLUX.2 Klein) renders labelled diagrams
# better than z-image-turbo, so it is listed first. Exact installed tags
# (e.g. ``x/flux2-klein:4b``) are resolved against this prefix list at
# detection time — never hardcode a tag; the operator's tag comes back
# from Ollama's /api/tags.
try:
    from .model_catalog import get_catalog as _get_model_catalog
except ImportError:  # pragma: no cover - direct-script execution path
    from src.model_catalog import get_catalog as _get_model_catalog

_LOCAL_IMAGE_MODEL_PREFERENCE = tuple(
    _get_model_catalog().role_default("local_draft")
)

_PAPERBANANA_ABSENT_REASON = (
    "paperbanana CLI not on PATH and paperbanana package not "
    "importable — falling back to Nano Banana Flash 1K with "
    "academic-figure-aware prompting. Install paperbanana via "
    "`pip install 'paperbanana[google]'` for publication-tier "
    "output. See /jack-tar-deckhand:verify for guidance."
)


@dataclass(frozen=True)
class LocalBackend:
    """A detected local image-generation backend.

    Attributes:
        provider: backend family — ``"ollama"`` today; ``"mlx"`` is the
            planned second provider behind the same seam.
        model: exact installed model tag as reported by the backend
            (e.g. ``"x/flux2-klein:4b"``), passed verbatim to the
            render call.
    """

    provider: str
    model: str


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
            The catalog's image_gen role default (Nano Banana Flash 1K)
            by default — the cheapest tier that handles complex text.
        fallback_reason: human-readable explanation when ``available``
            is False. Empty when paperbanana was found.
        backend: primary render route for the FIRST render of this
            slide: ``"ollama"`` (free local draft — the default whenever
            a local image model is detected), ``"paperbanana"``, or
            ``"cloud_fallback"``. Empty string on legacy direct
            constructions; ``build_manifest_entry`` then derives the
            backend from ``available`` as before.
        local_provider: local backend family when ``backend`` is a
            local route (``"ollama"``; later ``"mlx"``). Empty otherwise.
        local_model: exact installed local model tag (e.g.
            ``"x/flux2-klein:4b"``). Empty when no local tier.
        local_args: render args for the local draft:
            ``{prompt, caption, width, height, iterations}``. The
            prompt is a single-shot academic-figure-aware synthesis of
            source_context + caption (local diffusion models don't run
            paperbanana's multi-agent pipeline — the prompt has to
            carry the intent alone). ``iterations`` is the free
            critique-loop budget per gate visit: 5 in local_only mode
            (matches the creative_vision cascade's ollama tier cap),
            3 in ladder mode. Empty when no local tier.
        local_only: operator opt-out of ALL paid tiers for this slide.
            When True the bridge must never dispatch paperbanana or
            cloud — exhausting the iteration budget surfaces
            best-so-far at the operator gate, where the operator can
            loop again (free), accept, or hand-edit. Set per-slide via
            ``slide["local_only"]`` or machine-wide via
            ``local-config.json`` → ``ollama.academic_figure_local_only``
            (the bridge passes the merged value in).
    """

    available: bool
    slide_number: int
    output_dir: str
    args: dict = field(default_factory=dict)
    fallback_provider: str = "google"
    fallback_model: str = _get_model_catalog().default_model("image_gen")["id"]
    fallback_reason: str = ""
    backend: str = ""
    local_provider: str = ""
    local_model: str = ""
    local_args: dict = field(default_factory=dict)
    local_only: bool = False


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


_TAG_SIZE_PATTERN = re.compile(r"^(\d+(?:\.\d+)?)b$")


def _tag_param_size(name: str) -> float:
    """Parse a parameter-size sort key from an Ollama tag (``9b`` → 9.0).

    Tags without a size suffix (``latest``, ``fp8``) sort as -1 so any
    sized variant outranks them; among equal keys ``max`` keeps the
    first-listed name.
    """
    tag = name.split(":", 1)[1].lower() if ":" in name else ""
    match = _TAG_SIZE_PATTERN.match(tag)
    return float(match.group(1)) if match else -1.0


def detect_local_backend(
    base_url: str = OLLAMA_BASE_URL,
    *,
    preferred_model: str | None = None,
    timeout_seconds: float = 2.0,
) -> LocalBackend | None:
    """Probe local Ollama for an image-capable model.

    Returns a ``LocalBackend`` naming the exact installed tag, or None
    when Ollama is unreachable or carries no image-capable model. Any
    probe failure (server down, timeout, malformed payload) degrades to
    None — the dispatch then takes the paperbanana/cloud ladder exactly
    as before, so a broken Ollama can never block the pipeline.

    Args:
        base_url: Ollama server root. Default localhost:11434.
        preferred_model: operator override, typically from
            ``local-config.json``'s ``ollama.academic_figure_model``.
            Matched against installed tags exactly, then by base name
            (tag-insensitive). Falls through to the preference list
            when not installed.
        timeout_seconds: probe budget. Kept short — this runs in the
            bridge's routing step, not the render step.
    """
    import json as _json
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(
            f"{base_url}/api/tags", timeout=timeout_seconds
        ) as resp:
            payload = _json.load(resp)
    except (urllib.error.URLError, OSError, ValueError):
        return None

    models = payload.get("models") or []
    names = [m.get("name", "") for m in models if isinstance(m, Mapping)]

    if preferred_model:
        for name in names:
            if name == preferred_model or name.split(":")[0] == preferred_model:
                return LocalBackend(provider="ollama", model=name)

    for prefix in _LOCAL_IMAGE_MODEL_PREFERENCE:
        matches = [n for n in names if n.split(":")[0] == prefix]
        if matches:
            # Largest parameter variant wins within a family (klein 9b
            # renders figure titles correctly where 4b garbles them —
            # 2026-07-11 three-way review). Ties / unsized tags keep
            # Ollama's listing order.
            return LocalBackend(
                provider="ollama", model=max(matches, key=_tag_param_size)
            )
    return None


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


# Single-shot local models get the whole intent in one prompt — cap the
# methodology text so the style directives at the tail keep their weight
# within the text encoder's window.
_MAX_LOCAL_CONTEXT_CHARS = 800

_LOCAL_PROMPT_STYLE = (
    "Style: clean publication-quality academic paper figure, flat vector "
    "diagram aesthetic, white background, thin precise lines, clearly "
    "labelled components with correctly spelled text, muted professional "
    "colour palette, generous whitespace, 16:9 composition. No "
    "photorealism, no decorative clutter, no watermark."
)


def _build_local_prompt(source_context: str, caption: str) -> str:
    """Compose the single-shot academic-figure prompt for a local model.

    Local diffusion models (flux2-klein, z-image-turbo) don't run
    paperbanana's Retriever→…→Critic pipeline, so the communicative
    intent (caption) and the methodology (source_context) are folded
    into one prompt with an explicit paper-figure style block.
    """
    ctx = source_context.strip()
    if len(ctx) > _MAX_LOCAL_CONTEXT_CHARS:
        ctx = ctx[:_MAX_LOCAL_CONTEXT_CHARS].rsplit(" ", 1)[0].rstrip(" ,;:.") + "…"

    parts: list[str] = []
    if caption:
        parts.append(f"Academic figure for a research paper: {caption}.")
    if ctx and ctx != caption:
        parts.append(f"The figure must faithfully depict this methodology: {ctx}")
    parts.append(_LOCAL_PROMPT_STYLE)
    return " ".join(parts)


# Free critique-loop budgets (renders per operator-gate visit).
# local_only matches the creative_vision cascade's ollama iteration cap;
# ladder mode stays tighter because a paid escalation path exists.
LOCAL_ONLY_ITERATIONS = 5
LOCAL_LADDER_ITERATIONS = 3


def build_dispatch_payload(
    slide: Mapping,
    *,
    output_dir: str,
    paperbanana_available: bool | None = None,
    local_backend: LocalBackend | None | bool = None,
    local_only: bool | None = None,
) -> PaperbananaDispatch:
    """Build the dispatch payload for an ``academic_figure`` slide.

    Ladder (2026-07-10, local-first): when a local Ollama image model is
    detected, the FIRST render always goes through it at $0 —
    ``backend`` is ``"ollama"`` and ``local_args`` carries the render
    contract. Paperbanana args (when installed) and the ``fallback_*``
    cloud fields ride along on the same struct so the bridge can
    escalate AFTER the F10 operator gate without rebuilding the payload.
    With no local backend, behaviour is unchanged from v1.4: paperbanana
    when available, Nano Banana Flash 1K cloud fallback otherwise.

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
            The local draft is written directly into this dir by the
            bridge (jack-tar-conventional filename — no run subdir).
        paperbanana_available: short-circuit the availability check
            (used by callers who have already detected paperbanana, e.g.
            the verify-skill helper). When None, calls
            ``is_paperbanana_available()`` to decide.
        local_backend: the local tier. ``None`` (default) auto-detects
            via ``detect_local_backend()``; ``False`` skips the local
            tier entirely (tests, operator opt-out); a ``LocalBackend``
            uses that backend without probing.
        local_only: never leave the local tier — no paperbanana, no
            cloud, ever (see the dataclass docstring). ``None``
            (default) reads ``slide["local_only"]``; the bridge passes
            the machine-wide ``local-config.json`` value here when the
            slide doesn't specify. Sets the free iteration budget to
            ``LOCAL_ONLY_ITERATIONS`` (5) instead of
            ``LOCAL_LADDER_ITERATIONS`` (3); the slide can override
            either via ``slide["local_iterations"]``.

    Returns:
        A ``PaperbananaDispatch``. ``backend`` names the primary render
        route. When paperbanana is available, ``args`` carries the
        four-key real contract; when a local backend is active,
        ``local_args`` carries ``{prompt, caption, width, height}``.
    """
    slide_number = int(slide.get("slide_number", 0))

    if paperbanana_available is None:
        paperbanana_available = is_paperbanana_available()
    if local_backend is None:
        local_backend = detect_local_backend()
    if local_only is None:
        local_only = bool(slide.get("local_only", False))

    source_context = _build_source_context_from_slide(slide)
    caption = _build_caption_from_slide(slide)

    # In local_only mode the paid tiers don't exist for this slide —
    # never assemble escalation args, even when paperbanana is installed.
    paperbanana_args: dict = {}
    if paperbanana_available and not local_only:
        paperbanana_args = {
            "source_context": source_context,
            "caption": caption,
            "aspect_ratio": "16:9",
            "iterations": int(slide.get("paperbanana_iterations", 1)),
        }

    if isinstance(local_backend, LocalBackend):
        default_iterations = (
            LOCAL_ONLY_ITERATIONS if local_only else LOCAL_LADDER_ITERATIONS
        )
        return PaperbananaDispatch(
            available=paperbanana_available and not local_only,
            slide_number=slide_number,
            output_dir=output_dir,
            args=paperbanana_args,
            fallback_reason=(
                "" if (paperbanana_available or local_only)
                else _PAPERBANANA_ABSENT_REASON
            ),
            # Issue #124: the backend is whatever local provider was
            # detected ("ollama" today, "mlx" behind the same seam) —
            # never a hardcoded literal.
            backend=local_backend.provider,
            local_provider=local_backend.provider,
            local_model=local_backend.model,
            local_args={
                "prompt": _build_local_prompt(source_context, caption),
                "caption": caption,
                "width": 1024,
                "height": 576,
                "iterations": int(slide.get("local_iterations", default_iterations)),
            },
            local_only=local_only,
        )

    if local_only:
        # Operator forbade paid tiers but no local backend is up: hard
        # stop, never silently fall through to spend. The bridge must
        # surface this to the operator (placeholder slide / skip), not
        # dispatch a cloud render.
        return PaperbananaDispatch(
            available=False,
            slide_number=slide_number,
            output_dir=output_dir,
            backend="local_only_blocked",
            local_only=True,
            fallback_reason=(
                "local_only is set for this slide but no local image "
                "backend was detected — Ollama unreachable or no "
                "image-capable model pulled. Start Ollama (`ollama "
                "serve`) or pull a model (`ollama pull x/flux2-klein`). "
                "Cloud dispatch is FORBIDDEN for this slide."
            ),
        )

    if not paperbanana_available:
        return PaperbananaDispatch(
            available=False,
            slide_number=slide_number,
            output_dir=output_dir,
            backend="cloud_fallback",
            fallback_reason=_PAPERBANANA_ABSENT_REASON,
        )

    return PaperbananaDispatch(
        available=True,
        slide_number=slide_number,
        output_dir=output_dir,
        backend="paperbanana",
        args=paperbanana_args,
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
    backend_used: str | None = None,
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
        backend_used: which route actually produced the image —
            ``"ollama_local"`` (or ``"ollama"``), ``"paperbanana"``, or
            ``"cloud_fallback"``. Needed when the bridge escalated past
            the local draft after the operator gate. When None, derived
            from the dispatch: its ``backend`` field, or (legacy direct
            constructions with no ``backend``) from ``available``.

    Returns:
        A dict shaped like other image-manifest entries:
        ``slide_number``, ``file_path``, ``status``, ``image_id``,
        ``model_used``, ``backend``, ``source_prompt`` (methodology
        text), ``caption`` (figure caption), plus paperbanana-specific
        ``paperbanana_run_id`` and ``paperbanana_args`` when available.
        ``source_prompt`` carries the methodology text, ``caption``
        carries the communicative intent — distinct fields because
        iterate-slide (#89) needs both to re-call paperbanana with the
        same semantic input. For ``ollama_local`` entries,
        ``source_prompt`` carries the composed single-shot prompt and
        ``local_provider`` / ``local_args`` support re-render with the
        same semantic input.
    """
    if backend_used is None:
        backend_used = dispatch.backend or (
            "paperbanana" if dispatch.available else "cloud_fallback"
        )
    # Issue #124: any local provider family maps to "<provider>_local"
    # ("ollama" -> "ollama_local", "mlx" -> "mlx_local") — the seam is
    # provider-shaped, not ollama-shaped.
    if dispatch.local_provider and backend_used == dispatch.local_provider:
        backend_used = f"{backend_used}_local"

    if backend_used == "paperbanana":
        model_used = "paperbanana"
    elif dispatch.local_provider and backend_used == f"{dispatch.local_provider}_local":
        model_used = dispatch.local_model
    else:
        model_used = dispatch.fallback_model

    status = "generated" if dispatch_succeeded else "failed"

    entry: dict = {
        "slide_number": dispatch.slide_number,
        "file_path": output_path,
        "status": status,
        "image_id": f"slide-{dispatch.slide_number:02d}-academic-figure",
        "model_used": model_used,
        "backend": backend_used,
        "source_prompt": dispatch.args.get("source_context", ""),
        "caption": dispatch.args.get("caption", ""),
    }
    if content_hash is not None:
        entry["content_hash"] = content_hash
    if backend_used == "paperbanana":
        run_id = _extract_run_id(output_path)
        if run_id:
            entry["paperbanana_run_id"] = run_id
        # Full args dict so iterate-slide can re-call with the same
        # semantic input via --continue-run + --feedback.
        entry["paperbanana_args"] = dict(dispatch.args)
    elif backend_used == "ollama_local":
        entry["source_prompt"] = dispatch.local_args.get("prompt", "")
        entry["caption"] = dispatch.local_args.get("caption", "")
        entry["local_provider"] = dispatch.local_provider
        # Full local args so iterate-slide can re-render with the same
        # semantic input (tweaked prompt, same dimensions).
        entry["local_args"] = dict(dispatch.local_args)
    else:
        entry["fallback_reason"] = dispatch.fallback_reason
    if dispatch.local_only:
        entry["local_only"] = True
    if error is not None:
        entry["error"] = error
    return entry
