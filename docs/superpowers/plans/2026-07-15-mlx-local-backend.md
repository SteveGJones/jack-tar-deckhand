# Detailed design — MLX (mflux) as a second local provider (issue #124, Horizon 1)

Design date 2026-07-15. Branch `feat/mlx-local-backend`. Base `main` @ `7d0caa1`.
Approved plan: issue #124 comment ("Plan: MLX (mflux) as a second local
provider…"). Feature proposal: `docs/feature-proposals/124-mlx-local-backend.md`.

**This document is the single source the implementing agents follow.** It is
design-only — no production code is written here. Every function signature,
JSON blob, flag list, and diff below is meant to be transcribed, not
re-derived. Where the code cannot answer a question, it is flagged in §9
rather than guessed.

## 0. Scope and locked decisions (from the approved plan — do not relitigate)

1. **Operator installs everything; the plugin bundles nothing, never
   auto-downloads.** Runtime via `uv tool install --upgrade mflux`; weights
   via operator-run `hf download …` / `mflux-save …`.
2. **Two-stage detection.** mflux CLI on PATH **AND** at least one catalogued
   model's weights present as a complete HF-cache snapshot → backend
   available. CLI present, no weights → NOT available (verify prints the exact
   pull command).
3. **Subprocess CLI dispatch, not in-process.** A wrapper mirroring
   `jack-tar-ollama/src/generate_image.py`.
4. **New sibling plugin `jack-tar-mlx`** (skills: `image`, `verify`),
   flag-compatible with the ollama wrapper.
5. **Two horizons.** This PR = MLX as *second* local provider behind the
   `LocalBackend` seam. `role_defaults.local_draft` stays Ollama-first.
   Horizon 2 (replacement) is a separate follow-up issue, out of scope here.

**Horizon-1 acceptance (issue #124):** a `local_only` slide on an MLX-only
machine renders at $0 through the same critique loop with gate semantics
unchanged; manifest records `backend: "mlx_local"`, `local_provider: "mlx"`,
exact `model_used`. Ollama-down + mflux-present → `detect_any_local_backend`
returns an MLX `LocalBackend`, not `local_only_blocked`. mflux present but no
weights → NOT available with the exact pull command; never a download.

## 1. What the existing code already gives us (verified reads)

The seam is further along than the issue assumed. Confirmed against HEAD:

- `build_dispatch_payload` already sets `backend=local_backend.provider`
  (`paperbanana_dispatch.py:494`) — no hardcoded `"ollama"`.
- `build_manifest_entry` already generalizes the `_local` suffix
  (`:613-617`) and `model_used` resolution (`:621-622`) off
  `dispatch.local_provider`. **One** ollama literal remains: the `elif
  backend_used == "ollama_local":` branch at **`:647`** — an `mlx_local`
  entry would skip that branch and lose its `source_prompt`/`local_provider`/
  `local_args` re-render contract. §2.4 fixes it.
- `LocalBackend` (`:90-103`) is already provider-shaped (`provider` + `model`).
- Catalog schema `provider` enum doc already lists `mlx`
  (`model-catalog.schema.json:55`); `catalog_markdown.py:27` already has an
  `"MLX (local, free)"` display label; `test_model_catalog.py::
  test_local_override_adds_model` already exercises an `mlx/flux-dev-q8`
  local-config override end-to-end. **The local-config override path works for
  MLX today with zero code changes** — this PR ships first-class catalog
  entries + detection + a wrapper, not the override mechanism.

Everything in §2–§6 builds on those seams; nothing rebuilds them.

## 2. `paperbanana_dispatch.py` — detection + dispatch seam

New functions and one literal fix. All live in the canonical
`src/paperbanana_dispatch.py`? — **No.** `paperbanana_dispatch.py` is NOT
vendored (it is deckhand-only; there is one copy at
`plugins/jack-tar-deckhand/src/paperbanana_dispatch.py`). Edit that one file.

### 2.1 `detect_mlx_backend`

```python
def detect_mlx_backend(
    *,
    preferred_model: str | None = None,
    hf_home: str | os.PathLike | None = None,
    extra_model_dirs: tuple[str, ...] = (),
    timeout_seconds: float = 2.0,
) -> LocalBackend | None:
    """Probe for a runnable local MLX (mflux) image backend.

    Two-stage detection (issue #124, locked decision 2), mirroring
    ``detect_local_backend`` but for a *server-less* CLI runtime:

    Stage 1 — runtime present: at least one mflux entry point
    (``mflux-generate-flux2`` / ``mflux-generate-z-image-turbo`` /
    ``mflux-generate-qwen``) is on PATH (``shutil.which``). None → return
    None (mflux not installed; the composed probe falls through to the next
    provider or the pre-MLX ladder).

    Stage 2 — weights present: at least one catalogued ``mlx/*`` entry has a
    COMPLETE Hugging Face cache snapshot (``_hf_snapshot_complete``) for its
    ``sdk.hf_repo`` (or ``sdk.hf_repo_fallback``), OR a non-empty
    ``mflux-save`` directory named in ``extra_model_dirs`` /
    ``local-config.json`` → ``mlx.models``. This is the guard that prevents
    a multi-GB first-use download (locked decision 1): a model whose weights
    are not fully cached is NOT offered.

    RAM gate: an entry carrying ``capabilities.min_ram_gb`` above the
    machine's physical RAM (``_physical_ram_gb``) is skipped — detection
    never offers a model the machine cannot load (e.g. Qwen-Image ~32 GB on a
    16 GB Mac). See §9 risk 3.

    Selection order (first match wins):
      1. ``preferred_model`` — operator override (catalog id), typically from
         ``local-config.json`` → ``mlx.academic_figure_model``. Matched
         exactly against catalogued ``mlx/*`` ids.
      2. catalogued ``mlx/*`` entries in catalog listing order (Klein 4B,
         Z-Image-Turbo, Qwen-Image — see §3), each subject to the RAM gate
         and the snapshot check.

    Returns ``LocalBackend(provider="mlx", model=<catalog id>)`` — the
    catalog id (e.g. ``"mlx/flux2-klein-4b"``), NOT the HF repo. The catalog
    id is passed verbatim as the wrapper's ``--model`` arg and recorded as
    ``model_used`` in the manifest (see §2.5 model trace). Any failure on any
    path degrades to None; a broken/partial MLX install can never block the
    pipeline.

    Args:
        preferred_model: operator model override (catalog id). Falls through
            to the catalog order when not installed/complete.
        hf_home: HF cache root override. Default: ``$HF_HOME`` or
            ``~/.cache/huggingface``. The hub dir is ``<root>/hub``.
        extra_model_dirs: additional ``mflux-save`` local weight dirs to
            treat as available (absolute paths). Merged with
            ``local-config.json`` → ``mlx.models`` by the caller.
        timeout_seconds: reserved for signature symmetry with
            ``detect_local_backend``; the MLX probe is a synchronous
            filesystem + PATH scan with no network, so this is currently a
            no-op. Kept so ``detect_any_local_backend`` can pass one budget
            to both detectors.
    """
```

### 2.2 `_hf_snapshot_complete` (private helper)

```python
def _hf_snapshot_complete(repo_id: str, hub_dir: Path) -> bool:
    """True when ``repo_id`` has a complete HF-cache snapshot under hub_dir.

    HF layout: ``<hub_dir>/models--<org>--<name>/snapshots/<rev>/`` holds
    symlinks into ``models--<org>--<name>/blobs/``. A partial download leaves
    ``*.incomplete`` files in ``blobs/`` and dangling snapshot symlinks.

    Completeness predicate (false-negative-safe — any doubt returns False so
    detection under-reports rather than triggering a download):
      1. ``models--<org>--<name>/`` exists (org/name → dir name: replace '/'
         with '--', prefix ``models--``).
      2. ``snapshots/`` contains ≥1 revision dir with ≥1 entry.
      3. NO ``blobs/*.incomplete`` file exists for the repo.
      4. EVERY symlink in the newest snapshot revision resolves to an existing
         path (``Path.exists()`` follows the link).
    Any OSError → False.
    """
```

### 2.3 `_physical_ram_gb` (private helper)

```python
def _physical_ram_gb() -> float | None:
    """Physical RAM in GB, or None when undetectable.

    MLX is Apple-Silicon-only, so macOS is the primary path:
      1. ``sysctl -n hw.memsize`` (bytes) via ``subprocess.run`` — the
         canonical macOS source.
      2. Fallback: ``os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE')``
         (present on Linux/most Unix; ``SC_PHYS_PAGES`` may be absent on some
         macOS builds — hence sysctl first).
    None on any failure — a None RAM reading DISABLES the RAM gate (fail open
    to detection; the wrapper's own OOM handling is the backstop) rather than
    hiding all models.
    """
```

### 2.4 `detect_any_local_backend` (composed probe)

```python
def detect_any_local_backend(
    *,
    base_url: str = OLLAMA_BASE_URL,
    preferred_ollama_model: str | None = None,
    preferred_mlx_model: str | None = None,
    provider_order: tuple[str, ...] | None = None,
    hf_home: str | os.PathLike | None = None,
    extra_mlx_dirs: tuple[str, ...] = (),
    timeout_seconds: float = 2.0,
) -> LocalBackend | None:
    """Return the first available local backend in operator-configured order.

    Tries each provider in ``provider_order`` and returns the first
    ``LocalBackend`` a detector yields:
      - ``"ollama"`` → ``detect_local_backend(base_url,
        preferred_model=preferred_ollama_model, timeout_seconds=...)``
      - ``"mlx"``    → ``detect_mlx_backend(preferred_model=preferred_mlx_model,
        hf_home=..., extra_model_dirs=extra_mlx_dirs,
        timeout_seconds=...)``

    ``provider_order`` default resolution: the argument, else
    ``local-config.json`` → top-level ``local_provider_order``, else
    ``("ollama", "mlx")`` (Ollama-first — locked decision 5; Horizon 2 may
    flip this). Unknown provider names in the order are skipped with a debug
    log. Returns None when no provider yields a backend — the caller
    (``build_dispatch_payload``) then takes the paperbanana/cloud ladder or,
    under ``local_only``, returns ``local_only_blocked``.

    Acceptance case (issue #124): Ollama down + mflux+weights present, default
    order → ``detect_local_backend`` returns None, ``detect_mlx_backend``
    returns an MLX backend → this returns the MLX backend.
    """
```

Note: `build_dispatch_payload`'s `local_backend=None` auto-detect currently
calls `detect_local_backend()` (`:460`). Change that default-detect to
`detect_any_local_backend()` so an un-parameterised call picks up MLX. The
bridge (§5) passes an explicit backend, so this only affects direct/test
callers — keep it, it is the least-surprising default.

### 2.5 The `:647` literal fix (exact before/after)

`build_manifest_entry`, currently:

```python
    elif backend_used == "ollama_local":
        entry["source_prompt"] = dispatch.local_args.get("prompt", "")
        entry["caption"] = dispatch.local_args.get("caption", "")
        entry["local_provider"] = dispatch.local_provider
        entry["local_args"] = dict(dispatch.local_args)
```

Replace the guard line only (body unchanged):

```python
    elif dispatch.local_provider and backend_used == f"{dispatch.local_provider}_local":
        entry["source_prompt"] = dispatch.local_args.get("prompt", "")
        entry["caption"] = dispatch.local_args.get("caption", "")
        entry["local_provider"] = dispatch.local_provider
        entry["local_args"] = dict(dispatch.local_args)
```

This mirrors the already-generalized guards at `:616` and `:621`. After the
fix, an `mlx_local` render writes `source_prompt`/`caption`/`local_provider`/
`local_args` exactly as `ollama_local` does.

### 2.6 provider-aware `local_only_blocked` message

Replace the ollama-specific `fallback_reason` in the `local_only` +
no-backend branch (`:518-524`) with a module-level constant that names both
providers so an MLX-only operator gets actionable remediation. Add near the
other reason constants:

```python
_LOCAL_ONLY_BLOCKED_REASON = (
    "local_only is set for this slide but no local image backend was "
    "detected across the configured providers. Bring up at least one: "
    "Ollama — `ollama serve` then `ollama pull x/flux2-klein`; "
    "MLX (Apple Silicon) — `uv tool install --upgrade mflux` then "
    "`hf download <repo>` for a catalogued mlx/* model (see "
    "docs/architecture/mlx-install-guide.md). Cloud dispatch is FORBIDDEN "
    "for this slide."
)
```

and set `fallback_reason=_LOCAL_ONLY_BLOCKED_REASON` in that branch. (The
per-provider concrete commands stay generic here; the verify skill (§2.7) and
install guide carry the exact repo ids.)

### 2.7 model-string trace (single source of truth)

`mlx/flux2-klein-4b` (catalog id)
 → `detect_mlx_backend` returns `LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")`
 → `build_dispatch_payload` sets `local_model="mlx/flux2-klein-4b"`, `backend="mlx"`
 → bridge Step 4.6 passes `--model mlx/flux2-klein-4b` to the wrapper
 → wrapper `MLX_MODEL_REGISTRY` maps catalog id → (entrypoint, hf_repo, steps, quantize, timeout)
 → `build_manifest_entry` records `model_used="mlx/flux2-klein-4b"`, `backend="mlx_local"`, `local_provider="mlx"`.

Rationale for using the catalog id (not the HF repo) as `LocalBackend.model`:
the catalog entry names a *specific* repo via `sdk.hf_repo`, so the id is as
precise as Ollama's installed-tag; it keeps mflux-specific repo strings out of
the seam and the manifest; and it makes the manifest re-renderable by
iterate-slide via the catalog rather than a raw HF path.

## 3. Catalog design — three `mlx/*` entries + schema diff

### 3.1 Schema diff (`model-catalog/model-catalog.schema.json`)

The catalog is validated against this schema by
`plugins/integration_tests/test_model_catalog_integrity.py::TestSchema`
(full jsonschema). Both `sdk` and `capabilities` are
`additionalProperties: false`, so the new fields MUST be declared or the
entries fail CI. Add:

Under `definitions.model.properties.capabilities.properties` add:
```json
"min_ram_gb": {"type": "number", "minimum": 1, "description": "Minimum physical RAM (GB) to load this local model — detection skips models above the machine's RAM (issue #124, MLX Qwen-Image ~32 GB)."}
```

Under `definitions.model.properties.sdk.properties` add:
```json
"entrypoint": {"type": "string", "minLength": 1, "description": "CLI entry point for CLI-dispatched local providers (mflux: 'mflux-generate-flux2' etc.)."},
"hf_repo": {"type": "string", "minLength": 1, "description": "Hugging Face repo id the wrapper loads and detection checks for a complete snapshot (mlx/mflux). Prefer the ungated pre-quantized community export."},
"hf_repo_fallback": {"type": "string", "minLength": 1, "description": "Alternate HF repo id (e.g. full-precision) accepted when the primary is not cached."},
"default_steps": {"type": "integer", "minimum": 1, "description": "Family-native default inference steps when the caller omits --steps."},
"quantize": {"type": ["integer", "null"], "enum": [3, 4, 5, 6, 8, null], "description": "mflux on-load quantization bits (--quantize). null/omitted for already-quantized repos."}
```

Also extend the `sdk.api` description to list `mflux_cli`. Bump
`catalog_version` `1.0.0 → 1.1.0` (minor: new models) and `updated` to
`2026-07-15`.

### 3.2 The three entries (exact JSON — append to `models[]`)

```json
{
  "id": "mlx/flux2-klein-4b",
  "provider": "mlx",
  "aliases": ["flux2-klein-4b-mflux"],
  "status": "active",
  "replacement": null,
  "roles": ["image_gen", "local_draft"],
  "quirks": [],
  "capabilities": {
    "resolutions": ["1K"],
    "text_rendering": "good",
    "timeout_seconds": 300,
    "min_ram_gb": 16,
    "prompt_budget": {"max_words": 200, "style": "detailed_spatial"}
  },
  "pricing": {
    "currency": "USD",
    "verified": "2026-07-15",
    "estimate": false,
    "flat": 0.0
  },
  "sdk": {
    "api": "mflux_cli",
    "entrypoint": "mflux-generate-flux2",
    "hf_repo": "Runpod/FLUX.2-klein-4B-mflux-4bit",
    "default_steps": 4,
    "quantize": null
  },
  "notes": "FLUX.2 Klein 4B via mflux (Apache 2.0, ungated). hf_repo is the pre-quantized 4-bit community export (~4-5 GB, fast cold-load); no --quantize on load. MLX default draft model (2026-07-11 dogfood: 4B reaches Klein-9b grade at 20 steps + annotation pattern). min_ram_gb 16 conservative. Horizon-2 gate: Phase 5 dogfood must beat/match the Ollama Klein-9b 8/9 baseline before promotion into role_defaults.local_draft."
},
{
  "id": "mlx/z-image-turbo",
  "provider": "mlx",
  "aliases": ["z-image-turbo-mflux"],
  "status": "active",
  "replacement": null,
  "roles": ["image_gen", "local_draft"],
  "quirks": [],
  "capabilities": {
    "resolutions": ["1K"],
    "text_rendering": "fair",
    "timeout_seconds": 180,
    "min_ram_gb": 16,
    "prompt_budget": {"max_words": 50, "style": "concise_camera"}
  },
  "pricing": {
    "currency": "USD",
    "verified": "2026-07-15",
    "estimate": false,
    "flat": 0.0
  },
  "sdk": {
    "api": "mflux_cli",
    "entrypoint": "mflux-generate-z-image-turbo",
    "hf_repo": "filipstrand/Z-Image-Turbo-mflux-4bit",
    "hf_repo_fallback": "Tongyi-MAI/Z-Image-Turbo",
    "default_steps": 9,
    "quantize": null
  },
  "notes": "Z-Image-Turbo via mflux (Apache 2.0, ungated). Pre-quantized 4-bit primary, full-precision fallback. 9-step distilled. timeout_seconds 180 is a conservative placeholder — Mac wall-clock unpublished; Phase 5 measures (proposal risk 2)."
},
{
  "id": "mlx/qwen-image",
  "provider": "mlx",
  "aliases": ["qwen-image-mflux"],
  "status": "active",
  "replacement": null,
  "roles": ["image_gen", "local_draft"],
  "quirks": [],
  "capabilities": {
    "resolutions": ["1K"],
    "text_rendering": "excellent",
    "timeout_seconds": 900,
    "min_ram_gb": 32,
    "prompt_budget": {"max_words": 120, "style": "detailed_spatial"}
  },
  "pricing": {
    "currency": "USD",
    "verified": "2026-07-15",
    "estimate": false,
    "flat": 0.0
  },
  "sdk": {
    "api": "mflux_cli",
    "entrypoint": "mflux-generate-qwen",
    "hf_repo": "Qwen/Qwen-Image",
    "default_steps": 20,
    "quantize": 4
  },
  "notes": "Qwen-Image via mflux (Apache 2.0, ungated). Full-precision repo quantized on load (--quantize 4, ~12 GB, needs ~32 GB RAM — min_ram_gb 32 gates it off smaller machines). Strongest open-weights in-image text renderer; the challenger most likely to beat the Klein-9b label-fidelity baseline. default_steps 20 and timeout_seconds 900 are placeholders — Qwen family default + Mac cold-load are unverified (§9 OQ-2/OQ-3)."
}
```

`role_defaults.local_draft` is UNCHANGED (`["x/flux2-klein", "x/z-image-turbo"]`)
— locked decision 5.

### 3.3 Three-copy vendoring rule + markdown regen

`test_model_catalog_integrity.py` enforces byte-identity across three catalog
copies. Edit the canonical, then copy to both vendored locations in the SAME
commit:

```
model-catalog/model-catalog.json                    # canonical — edit here
plugins/jack-tar-cloud/src/model-catalog.json       # cp
plugins/jack-tar-deckhand/src/model-catalog.json    # cp
```

The schema (`model-catalog/model-catalog.schema.json`) is single-copy — edit
only there. After editing the catalog, regenerate the markdown doc (CI runs
`catalog_markdown.py --check`):

```
python model-catalog/catalog_markdown.py     # rewrites docs/model-catalog.md
```

Commit `docs/model-catalog.md` in the same commit.

## 4. `model_probe.py` — MLX discovery

`model_probe.py` is vendored: canonical `src/model_probe.py` + one copy at
`plugins/jack-tar-cloud/src/model_probe.py` (byte-identity enforced by the
integrity test). Edit canonical, copy to cloud.

### 4.1 `probe_mlx_models`

```python
def probe_mlx_models(hf_home=None, extra_model_dirs=()):
    """List HF-cached mlx/mflux image-weight repos with COMPLETE snapshots.

    Server-less analogue of ``probe_ollama_models``: "installed" == weights
    fully cached (mflux has no list API). Returns
    ``{'status':'ok','models': set[str]}`` of HF repo ids
    (e.g. 'Runpod/FLUX.2-klein-4B-mflux-4bit') with a complete snapshot under
    ``<hf_home or $HF_HOME or ~/.cache/huggingface>/hub``, plus any non-empty
    ``mflux-save`` dir basenames from ``extra_model_dirs``; or
    ``{'status':'skipped','reason': ...}`` when no mflux entry point is on
    PATH (mflux CLI not installed).

    Reuses ``_hf_snapshot_complete`` semantics (a private copy lives here;
    the dispatch module's copy is the same algorithm — see §9 OQ-5 on whether
    to share). Never raises; scan errors → skipped with the reason string.
    """
```

### 4.2 `_entry_upstream_match` generalization

The probe returns HF repo ids; mlx catalog *ids* are `mlx/flux2-klein-4b`. So
matching an mlx entry to the probe must compare on `sdk.hf_repo` /
`hf_repo_fallback`, not the entry id/aliases. Extend the helper:

```python
def _entry_upstream_match(entry, upstream):
    names = [entry["id"], *entry.get("aliases", [])]
    if entry["provider"] == "ollama":
        return any(tag == name or tag.startswith(f"{name}:")
                   for name in names for tag in upstream)
    if entry["provider"] == "mlx":
        sdk = entry.get("sdk") or {}
        repos = [r for r in (sdk.get("hf_repo"), sdk.get("hf_repo_fallback")) if r]
        return any(repo in upstream for repo in repos)
    return any(name in upstream for name in names)
```

### 4.3 `_CANDIDATE_FILTERS["mlx"]` + report wiring + UNPROBEABLE

- Add to `_CANDIDATE_FILTERS`: `"mlx": ("-mflux-",)` — the community
  quantized-repo suffix convention (`…-mflux-4bit`, `…-mflux-8bit`). New
  candidates = cached mflux repos no catalog entry covers.
- `find_new_candidates` matches an entry-covered repo via the same
  `hf_repo`-aware logic; add an mlx branch so a cached `hf_repo` is not
  reported as a candidate (mirror the ollama-prefix exclusion). Simplest:
  build `known` from ids/aliases AND every mlx entry's `hf_repo`/
  `hf_repo_fallback`, then the existing substring filter applies.
- `probe_report` default probes dict gains `"mlx": probe_mlx_models()`.
- `UNPROBEABLE_PROVIDERS` is UNCHANGED — mlx is probeable (filesystem scan),
  like ollama. Document this in the module note: "mlx probing scans the HF
  cache; there is no server API but 'installed' is directly observable."

## 5. Bridge Step 4.6 diff outline (`imagegen-bridge/SKILL.md`)

The academic-figure dispatch (§ Step 4.6) currently reads
`ollama.academic_figure_model` and calls
`detect_local_backend(preferred_model=preferred)`. Change:

1. **Build-payload block** — read the new config keys and call the composed
   detector:
   ```python
   cfg = {}
   try:
       with open('local-config.json') as f:
           cfg = json.load(f)
   except FileNotFoundError:
       pass
   ollama_cfg = cfg.get('ollama', {})
   mlx_cfg = cfg.get('mlx', {})
   from src.paperbanana_dispatch import detect_any_local_backend
   backend = detect_any_local_backend(
       preferred_ollama_model=ollama_cfg.get('academic_figure_model'),
       preferred_mlx_model=mlx_cfg.get('academic_figure_model'),
       provider_order=tuple(cfg.get('local_provider_order', ('ollama', 'mlx'))),
       extra_mlx_dirs=tuple(mlx_cfg.get('models', ())),
   )
   # local_only: slide key wins; else provider-agnostic top-level, then legacy
   machine_local_only = bool(
       cfg.get('academic_figure_local_only',
               ollama_cfg.get('academic_figure_local_only', False))
       or mlx_cfg.get('academic_figure_local_only', False)
   )
   dispatch = build_dispatch_payload(
       slide, output_dir='./tmp/deck/images',
       local_backend=backend,
       local_only=bool(slide.get('local_only', machine_local_only)),
   )
   ```

2. **New `mlx_local` render branch** — a sibling of the existing ollama
   branch (prose mirrors it verbatim, swapping plugin root, filename, and the
   pull-command remediation). When `dispatch.backend == "mlx"`:
   ```bash
   MLX_PLUGIN_ROOT=$(dirname "$PLUGIN_ROOT")/jack-tar-mlx
   LOCAL_PROMPT=$(echo "$DISPATCH_JSON" | jq -r '.local_args.prompt')
   LOCAL_MODEL=$(echo "$DISPATCH_JSON" | jq -r '.local_model')
   OUT_PNG=$(echo "$DISPATCH_JSON" | jq -r '.output_dir')/slide-$(printf '%02d' $SLIDE_NUMBER)-academic-figure-mlx.png
   python3 "$MLX_PLUGIN_ROOT/src/generate_image.py" \
     --prompt "$LOCAL_PROMPT" --model "$LOCAL_MODEL" \
     --width $(echo "$DISPATCH_JSON" | jq -r '.local_args.width') \
     --height $(echo "$DISPATCH_JSON" | jq -r '.local_args.height') \
     --output "$OUT_PNG"
   ```
   Then the SAME free critique loop, F11 simplified-label rebuild, F10 gate
   (ladder mode), local_only handling, and `build_manifest_entry` call as the
   ollama branch — `backend_used` defaults to the dispatch backend →
   `mlx_local` (the §2.5 fix makes the manifest correct automatically). The
   branch text says "This is the free local tier — F10/F12 gate semantics are
   IDENTICAL to the ollama branch; MLX is a $0 tier."
   Restructure the two branches as one "local draft" branch keyed on
   `dispatch.backend in ("ollama", "mlx")` that selects plugin root +
   filename suffix from `dispatch.local_provider`, to avoid duplicating the
   loop prose. (Either shape is acceptable; the keyed-single-branch is
   preferred for maintainability.)

3. **`local-config.json` new keys** (documented in the SKILL prose + install
   guide):

   | Key | Type | Meaning | Precedence |
   |---|---|---|---|
   | `local_provider_order` | array | detection order, default `["ollama","mlx"]` | arg > this > default |
   | `mlx.academic_figure_model` | string (catalog id) | preferred mlx model | slide > this > catalog order |
   | `mlx.models` | array of dirs | extra `mflux-save` local weight dirs | additive |
   | `mlx.quantize` | int 3–8 | override on-load quantize | passed to wrapper `--quantize` |
   | `academic_figure_local_only` | bool | provider-agnostic paid-tier opt-out | slide > this > `<provider>.academic_figure_local_only` (legacy) |

   `ollama.academic_figure_model` / `ollama.academic_figure_local_only` are
   retained unchanged (back-compat).

Also update the deckhand `verify` skill (§ ENGINE PLUGINS block) to report MLX
readiness beside Ollama: shell `jack-tar-mlx:verify` when the plugin is
present; "Draft images READY if ollama OR mlx is FULLY/PARTIALLY_AVAILABLE."

## 6. `jack-tar-mlx` plugin design

### 6.1 File tree

```
plugins/jack-tar-mlx/
├── .claude-plugin/
│   └── plugin.json
├── CLAUDE.md
├── src/
│   └── generate_image.py
├── skills/
│   ├── image/
│   │   └── SKILL.md
│   └── verify/
│       └── SKILL.md
└── tests/
    ├── __init__.py
    └── test_generate_image.py
```

No `hooks` (ollama's plugin.json has none). No vendored catalog/loader — the
wrapper is catalog-independent (see §6.3 decision).

### 6.2 `plugin.json`

```json
{
  "name": "jack-tar-mlx",
  "description": "Local AI image generation on Apple Silicon via the mflux CLI (MLX) — server-less, operator-installed weights, flag-compatible with jack-tar-ollama",
  "version": "0.1.0",
  "author": {"name": "Steve Jones"},
  "repository": "https://github.com/SteveGJones/jack-tar-deckhand",
  "license": "MIT",
  "keywords": ["mlx", "mflux", "image-generation", "local-ai", "apple-silicon"]
}
```

### 6.3 `src/generate_image.py` — module design

**Catalog-reading decision.** The wrapper does NOT read the model catalog. It
mirrors `jack-tar-ollama/src/generate_image.py`, which is fully self-contained
(hardcoded `MODEL_TIMEOUTS`, no catalog import). Reasons: (a) the wrapper must
run in the mflux plugin's minimal environment without dragging in the loader;
(b) vendoring a third catalog+loader copy would triple the byte-identity
surface the integrity test guards for no routing benefit — the catalog→
entrypoint mapping is deckhand's routing concern, resolved before the wrapper
is called; (c) it matches the ollama precedent exactly, keeping the two
wrappers symmetric. Instead the wrapper carries a small internal registry, and
a drift-guard test (§7) asserts the registry keys equal the catalog's `mlx/*`
ids so the two never silently diverge. *(This is a considered deviation from
the task's "mirror how cloud vendors the catalog" framing — see final report.)*

```python
MLX_MODEL_REGISTRY = {
    # catalog id -> dispatch metadata
    "mlx/flux2-klein-4b": {
        "entrypoint": "mflux-generate-flux2",
        "hf_repo": "Runpod/FLUX.2-klein-4B-mflux-4bit",
        "hf_repo_fallback": None,
        "default_steps": 4,
        "quantize": None,
        "timeout": 300,
    },
    "mlx/z-image-turbo": {
        "entrypoint": "mflux-generate-z-image-turbo",
        "hf_repo": "filipstrand/Z-Image-Turbo-mflux-4bit",
        "hf_repo_fallback": "Tongyi-MAI/Z-Image-Turbo",
        "default_steps": 9,
        "quantize": None,
        "timeout": 180,
    },
    "mlx/qwen-image": {
        "entrypoint": "mflux-generate-qwen",
        "hf_repo": "Qwen/Qwen-Image",
        "hf_repo_fallback": None,
        "default_steps": 20,
        "quantize": 4,
        "timeout": 900,
    },
}
DEFAULT_MODEL = "mlx/flux2-klein-4b"
DEFAULT_TIMEOUT = 300
LOCK_PATH = Path(tempfile.gettempdir()) / "jack-tar-mlx-image.lock"
DEFAULT_LOCK_WAIT_TIMEOUT = 600     # mirror issue #75
STALE_LOCK_AGE_SECONDS = 1800       # mirror issue #75
```

**argparse spec** — ollama flags verbatim + one mlx addition:

| Flag | Type | Default | Notes |
|---|---|---|---|
| `--prompt` | str | (required) | |
| `--model` | str | `mlx/flux2-klein-4b` | catalog id; must be a registry key |
| `--output` | str | `output/YYYYMMDD-HHMMSS.png` | same as ollama |
| `--width` | int | 1024 | |
| `--height` | int | 1024 | |
| `--steps` | int | None | None → registry `default_steps` |
| `--seed` | int | None | omitted from CLI when None |
| `--timeout` | int | None | None → registry `timeout`; DEFAULT_TIMEOUT for unknown |
| `--lock-wait-timeout` | int | 600 | issue #75 |
| `--no-lock` | flag | off | issue #75 |
| `--quantize` / `-q` | int (3–8) | None | mlx-only; None → registry `quantize`; only emitted when non-None |

**Model resolution** (`resolve_model`): look up `--model` in
`MLX_MODEL_REGISTRY`; unknown id → exit 1 with the known-ids list (mirrors the
catalog's `UnknownModelError` shape). Returns the metadata dict.

**Subprocess construction** (`_build_argv`):
```
[meta["entrypoint"],
 "--model", meta["hf_repo"],          # HF repo id (mflux accepts repo id / name / path)
 "--prompt", prompt,
 "--width", str(width), "--height", str(height),
 "--steps", str(steps or meta["default_steps"]),
 "--output", str(output_path),
 "--metadata"]                         # writes JSON sidecar next to output
 + (["--seed", str(seed)] if seed is not None else [])
 + (["-q", str(q)] if (q := (quantize if quantize is not None else meta["quantize"])) is not None else [])
```
Fallback-repo handling: try `hf_repo`; if the run fails with a
weights-missing signature AND `hf_repo_fallback` is set, retry once with the
fallback repo. (Both attempts run under HF_HUB_OFFLINE — neither downloads.)

**Refusal-to-download guard.** Run the subprocess with an environment that
forces the HF stack offline so a cache miss fails FAST instead of pulling
multi-GB weights:
```python
env = {**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
```
`HF_HUB_OFFLINE=1` is the canonical `huggingface_hub` mechanism: `from_pretrained`
/ `hf_hub_download` resolve from cache only and raise
`LocalEntryNotFoundError` on a miss rather than hitting the network.
`TRANSFORMERS_OFFLINE=1` is belt-and-braces for any transformers-mediated
load. This is the hard guard behind detection's soft (snapshot-completeness)
guard — even if detection and render race, the render cannot download.

**Execution + stdout contract.** Use `subprocess.run(argv, env=env,
timeout=resolved_timeout, capture_output=True, text=True)`. On success: parse
the `--metadata` JSON sidecar (mflux writes `<output>.json` alongside the PNG;
verify exact sidecar path — §9 OQ-4) for the actual seed/steps used (for
logging only), then **print the output path as the last stdout line** — the
exact ollama contract (`print(str(output_path))`), so the bridge's
`OUT_PNG`-based flow is unchanged.

**Error taxonomy** (all exit 1, message to stderr, mirror ollama tone):

| Condition | Detection | Message |
|---|---|---|
| CLI missing | `shutil.which(meta["entrypoint"]) is None` before run | `mflux not installed — run: uv tool install --upgrade mflux` |
| weights missing | non-zero exit + `LocalEntryNotFound`/`offline`/`Can't load` in stderr (after fallback repo tried) | `weights for {model} not cached — run: hf download {hf_repo}` (no download attempted) |
| timeout | `subprocess.TimeoutExpired` | `Generation timed out after {timeout}s. Try a smaller model or fewer --steps.` |
| OOM | non-zero exit + `metal`/`out of memory`/`MTLBuffer`/`bad_alloc` in stderr | `{model} may exceed available RAM — try a smaller model or higher quantization (-q 4).` |
| other non-zero | fallthrough | `mflux error (exit {rc}): {stderr tail 200 chars}` |

**Single-flight lock.** Copy the ollama `_single_flight_lock` contextmanager
verbatim, changing only `LOCK_PATH` to the mlx path. Same `--no-lock` /
`--lock-wait-timeout` semantics, same stale-reclaim at 1800 s. (Rationale in
plan: two concurrent multi-GB MLX loads OOM the machine — the lock matters
more here than for Ollama's warm server.)

### 6.4 `skills/image/SKILL.md` outline

Frontmatter `name: image`, `allowed-tools: Bash(python *), Bash(python3 *)`.
Sections: prerequisites (mflux installed, weights pulled — link install
guide); argument parse (`--model --steps --seed --quantize --width --height`);
invoke `src/generate_image.py`; note single-flight lock + `--no-lock`; note
this is a $0 local tier; point at `/jack-tar-mlx:verify` when a render fails.

### 6.5 `skills/verify/SKILL.md` outline

Mirror `jack-tar-ollama/skills/verify/SKILL.md` STATUS-line contract (the
integration test will assert `PLUGIN: jack-tar-mlx`, `STATUS: FULLY_AVAILABLE`,
`STATUS: NOT_AVAILABLE`). Steps:
1. **Runtime check** — `command -v mflux-generate-flux2` (any entrypoint). Absent →
   `DEPENDENCIES: mflux: NOT_READY (run: uv tool install --upgrade mflux)`,
   `STATUS: NOT_AVAILABLE`.
2. **Version** — `mflux --version` or `uv tool list | grep mflux` /
   `pip show mflux` (surface for the manifest/regression note — proposal risk
   5).
3. **Weights check** — for each catalogued `mlx/*` repo, scan
   `${HF_HOME:-~/.cache/huggingface}/hub` for a complete snapshot; report
   `READY` / `NOT_READY (run: hf download <repo>)` per model, with the disk
   size when present.
4. **HF cache location + disk usage** line.
5. **STATUS**: `FULLY_AVAILABLE` when runtime + ≥1 model present;
   `NOT_AVAILABLE` when runtime present but no weights (with the exact pull
   command) or runtime absent.

### 6.6 `CLAUDE.md` outline

Short, mirroring `jack-tar-ollama/CLAUDE.md`: purpose, prerequisites
(operator-installed runtime + weights, Apple Silicon), skills table, the
single-flight lock note (issue #75 parity, `/tmp/jack-tar-mlx-image.lock`), a
"never auto-downloads / HF_HUB_OFFLINE guard" note, quick start.

## 7. Test matrix

### 7.1 `plugins/jack-tar-mlx/tests/test_generate_image.py` (mirror the 27 ollama tests)

Mock `subprocess.run` (mflux is not installed in CI). Cases:
- `test_builds_argv_with_entrypoint_and_repo` — klein id → `mflux-generate-flux2 --model Runpod/...`.
- `test_prints_output_path_on_stdout` — stdout last line == resolved output path.
- `test_creates_output_directory` — parent dir made.
- `test_default_output_path_uses_timestamp` — monkeypatched clock.
- `test_seed_included_in_argv` / `test_seed_omitted_when_absent`.
- `test_steps_defaults_from_registry` (klein→4, z-image→9, qwen→20).
- `test_explicit_steps_override`.
- `test_quantize_from_registry` (qwen→`-q 4`) / `test_quantize_omitted_for_prequantized` (klein) / `test_explicit_quantize_override`.
- `test_timeout_from_registry` (klein 300 / z-image 180 / qwen 900) / `test_unknown_model_exits` / `test_explicit_timeout_override`.
- `test_subprocess_env_forces_hf_offline` — `HF_HUB_OFFLINE=1` & `TRANSFORMERS_OFFLINE=1` in the passed env (the refusal-to-download guard).
- `test_metadata_flag_present` — `--metadata` in argv.
- `test_cli_missing_exits_with_install_hint` — `shutil.which` → None.
- `test_weights_missing_exits_without_download` — stderr `LocalEntryNotFound`; asserts message names `hf download <repo>` and NO retry hits network.
- `test_fallback_repo_tried_when_primary_missing` — z-image primary miss → fallback repo retried once.
- `test_timeout_expired_message` — `subprocess.TimeoutExpired`.
- `test_oom_hint_on_metal_error` — stderr `out of memory` → RAM hint.
- `test_other_nonzero_exit_surfaces_stderr_tail`.
- `test_custom_dimensions`.
- Lock tests (copy ollama's 9): `test_no_lock_flag_skips_lock_machinery`,
  `test_default_invocation_acquires_and_releases_lock`,
  `test_lock_wait_timeout_propagates`, `test_lock_acquisition_timeout_exits`,
  `test_lock_acquired_when_uncontended`, `test_lock_released_on_exception`,
  `test_lock_blocked_then_acquired`, `test_lock_timeout_raises`,
  `test_stale_lock_is_reclaimed` — pointed at `jack-tar-mlx-image.lock`.
- `test_registry_keys_match_catalog_mlx_ids` — drift guard: registry keys ==
  `{e['id'] for e in catalog.entries(provider='mlx', status='active')}`
  (loads the vendored deckhand catalog via a path constant).

### 7.2 `plugins/jack-tar-deckhand/tests/test_paperbanana_dispatch.py`

- `test_detect_mlx_backend_returns_none_when_no_cli` (monkeypatch `shutil.which`→None).
- `test_detect_mlx_backend_returns_none_when_cli_but_no_weights` (which OK, snapshot check False).
- `test_detect_mlx_backend_returns_catalog_id_when_weights_complete` (fake hub tree via tmp_path; asserts `LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")`).
- `test_detect_mlx_backend_honours_preferred_model`.
- `test_detect_mlx_backend_ram_gate_skips_qwen_on_small_machine` (monkeypatch `_physical_ram_gb`→16; only qwen weights present → None).
- `test_detect_mlx_backend_ram_gate_disabled_when_ram_unknown` (`_physical_ram_gb`→None → qwen offered).
- `test_hf_snapshot_complete_true_for_full_snapshot` / `_false_for_incomplete_blob` / `_false_for_dangling_symlink` / `_false_for_missing_repo`.
- `test_detect_any_local_backend_prefers_ollama_by_default` (both up → ollama).
- `test_detect_any_local_backend_falls_through_to_mlx_when_ollama_down` (the #124 acceptance case).
- `test_detect_any_local_backend_honours_provider_order` (order `["mlx","ollama"]` → mlx wins even with ollama up).
- `test_detect_any_local_backend_none_when_no_provider` .
- `test_manifest_entry_for_local_mlx_render` — `backend_used` defaults to `mlx_local`; asserts `source_prompt`/`local_provider`/`local_args`/`model_used` (the `:647` regression guard).
- `test_manifest_entry_escalated_from_mlx_to_paperbanana_after_gate`.
- `test_local_only_blocked_message_names_both_providers`.
- `test_build_dispatch_payload_mlx_backend_sets_backend_and_local_model`.
- Regression: all 69 existing tests still pass (ollama paths untouched).

### 7.3 `plugins/jack-tar-cloud/tests/test_model_probe.py`

- `test_probe_mlx_skipped_when_cli_absent` (which→None → skipped).
- `test_probe_mlx_lists_complete_snapshot_repos` (fake hub tree).
- `test_mlx_entry_matches_on_hf_repo` — `classify_entries` verifies `mlx/flux2-klein-4b` when its `hf_repo` is in the probe set.
- `test_mlx_entry_suspect_when_repo_absent`.
- `test_mlx_candidate_filter_matches_mflux_suffix` — cached `Foo/Bar-mflux-8bit` uncatalogued → candidate under `mlx`.
- `test_mlx_hf_repo_not_reported_as_candidate` — a catalogued repo is excluded.
- `test_report_includes_mlx_probe` — `probe_report` default dict has an `mlx` key.

### 7.4 `plugins/jack-tar-cloud/tests/test_model_catalog.py`

- `test_mlx_entries_present` — three ids resolve, provider `mlx`, `flat 0.0`.
- `test_mlx_entries_have_sdk_entrypoint_and_hf_repo`.
- `test_mlx_qwen_has_min_ram_gb_32`.
- (schema validity is covered by the integration integrity test §7.5.)

### 7.5 `plugins/integration_tests/`

- `test_model_catalog_integrity.py::TestSchema` — already validates the full
  catalog against the schema; passes once the §3.1 schema diff lands. Add an
  explicit `test_mlx_entries_validate` if desired.
- `test_model_catalog_integrity.py::TestCopyIdentity` — three catalog copies
  byte-identical (already parametrized; passes after the §3.3 copy).
- `test_model_catalog_integrity.py` — `docs/model-catalog.md --check` passes
  after regen.
- `test_plugin_verify_contracts.py` — ADD `test_mlx_verify_has_status_lines`
  (`PLUGIN: jack-tar-mlx`, `STATUS: FULLY_AVAILABLE`, `STATUS: NOT_AVAILABLE`).
- `test_plugin_root_discovery.py` — ADD jack-tar-mlx to whatever plugin-set
  assertion it makes (verify it discovers the new plugin dir).
- New `test_mlx_plugin_contract.py` (optional, recommended) — asserts the
  wrapper's `MLX_MODEL_REGISTRY` keys equal catalog `mlx/*` ids (cross-plugin
  drift guard, complementing §7.1's in-plugin copy).

## 8. Version + release plan

CI `json-validation` asserts: every `plugins/*/.claude-plugin/plugin.json`
parses; marketplace lists exactly the plugin dirs on disk (bidirectional);
each plugin.json `version` == its marketplace entry `version`. Therefore every
file below MUST change together in the release commit:

| File | Change |
|---|---|
| `plugins/jack-tar-mlx/.claude-plugin/plugin.json` | NEW, `version: 0.1.0` |
| `plugins/jack-tar-deckhand/.claude-plugin/plugin.json` | `1.7.0 → 1.8.0` |
| `plugins/jack-tar-cloud/.claude-plugin/plugin.json` | `1.4.0 → 1.5.0` (minor: probe_mlx_models) |
| `.claude-plugin/marketplace.json` | ADD jack-tar-mlx entry (0.1.0); bump deckhand→1.8.0, cloud→1.5.0 |
| `model-catalog/model-catalog.json` | `catalog_version 1.0.0 → 1.1.0`, three mlx entries |
| `plugins/jack-tar-cloud/src/model-catalog.json` | cp of canonical |
| `plugins/jack-tar-deckhand/src/model-catalog.json` | cp of canonical |
| `model-catalog/model-catalog.schema.json` | §3.1 schema diff (single copy) |
| `docs/model-catalog.md` | regenerated |
| `src/model_probe.py` + `plugins/jack-tar-cloud/src/model_probe.py` | probe_mlx_models etc., byte-identical |
| `plugins/jack-tar-deckhand/src/paperbanana_dispatch.py` | §2 |
| `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md` | §5 |
| `plugins/jack-tar-deckhand/skills/verify/SKILL.md` | MLX readiness line |
| `docs/architecture/paperbanana-integration-v2.md` | §8.6 v3 addendum |
| `docs/architecture/mlx-install-guide.md` | NEW |
| `CLAUDE.md` (root) | status update (v1.8.0, MLX second provider) |
| `retrospectives/124-mlx-local-backend.md` | NEW (from feature proposal) |

marketplace.json has no top-level version field — only per-plugin entries
change. The `.bsa/models/jack-tar-deckhand.json` model is NOT
version-gated by CI (json-validation only parses it) — a canonical-model
update is optional and can be deferred to a follow-up.

## 9. Task breakdown (ordered, delegation-sized)

Each task is mechanically unambiguous. Prompts that touch generated images
MUST carry the no-PNG-Read inline reminder (issue #86).

**T1 — Schema diff + catalog entries + vendoring + markdown.**
- Files: `model-catalog/model-catalog.schema.json` (§3.1), `model-catalog/
  model-catalog.json` (§3.2 + version/updated bump), cp to both vendored
  catalogs (§3.3), regen `docs/model-catalog.md`.
- Depends-on: none.
- DoD: `python model-catalog/catalog_markdown.py --check` OK; three catalog
  copies byte-identical; `test_model_catalog_integrity.py` green;
  `load_catalog().get("mlx/qwen-image")` resolves.

**T2 — `jack-tar-mlx` plugin (wrapper + lock + skills + tests).**
- Files: whole `plugins/jack-tar-mlx/` tree (§6), `test_generate_image.py`
  (§7.1).
- Depends-on: T1 (drift-guard test reads catalog mlx ids).
- DoD: `pytest plugins/jack-tar-mlx/tests` green; wrapper runs
  `--help`; registry-keys-match-catalog test passes.

**T3 — Dispatch seam (detect_mlx_backend, detect_any_local_backend, helpers,
`:647` fix, local_only message).**
- Files: `plugins/jack-tar-deckhand/src/paperbanana_dispatch.py` (§2),
  `test_paperbanana_dispatch.py` (§7.2).
- Depends-on: T1 (reads catalog mlx entries).
- DoD: new tests green; all 69 existing dispatch tests still pass; `:647`
  guard generalized.

**T4 — model_probe MLX discovery.**
- Files: `src/model_probe.py` + cp to `plugins/jack-tar-cloud/src/
  model_probe.py`, `test_model_probe.py` (§7.3).
- Depends-on: T1.
- DoD: probe tests green; `probe_report()` default dict has `mlx`; copies
  byte-identical.

**T5 — Bridge Step 4.6 + deckhand verify skill.**
- Files: `imagegen-bridge/SKILL.md` (§5), `skills/verify/SKILL.md` (MLX line).
- Depends-on: T3 (calls detect_any_local_backend), T2 (MLX_PLUGIN_ROOT).
- DoD: `test_imagegen_bridge_skill.py` still green; SKILL references
  `detect_any_local_backend`, `slide-NN-academic-figure-mlx.png`,
  `local_provider_order`.

**T6 — Integration tests + marketplace + versions.**
- Files: `.claude-plugin/marketplace.json`, deckhand+cloud plugin.json bumps,
  `test_plugin_verify_contracts.py`, `test_plugin_root_discovery.py`,
  optional `test_mlx_plugin_contract.py`.
- Depends-on: T2 (verify skill exists), T1/T4 (versions).
- DoD: full `json-validation` logic passes locally; integration suite green.

**T7 — Docs (ADR addendum, install guide, root CLAUDE.md, retrospective).**
- Files: `docs/architecture/paperbanana-integration-v2.md` (§8.6 addendum:
  second provider landed, composed probe, provider order, HF-offline guard),
  `docs/architecture/mlx-install-guide.md` (uv tool install; per-model
  `hf download` + disk table; licensing table — Apache-2.0 trio vs gated
  9B/dev; `mflux-save` quantized-local workflow; torch/env-size note; HF-token
  note for gated models we do NOT default to), root `CLAUDE.md` status,
  `retrospectives/124-mlx-local-backend.md`.
- Depends-on: T3/T5 (describe final behaviour).
- DoD: links resolve; install guide lists exact repo ids + disk sizes.

**T8 — Full-suite gate (pre-PR).**
- Run every plugin suite + integration + json-validation; open PR to `main`
  referencing #124.
- Depends-on: T1–T7.
- DoD: all green; PR body maps success criteria to evidence.

## 10. Open questions (could not resolve from the code / need operator or web verification)

- **OQ-1 — full-precision Klein 4B HF repo id.** The proposal names the
  pre-quantized `Runpod/FLUX.2-klein-4B-mflux-4bit` but not the full-precision
  repo. Design uses the pre-quantized repo as the sole `hf_repo` for klein
  (no fallback). If a canonical full-precision repo id is wanted as a
  fallback, the operator must supply it (candidate: `black-forest-labs/
  FLUX.2-klein-4B` — UNVERIFIED). Flagged; not blocking.
- **OQ-2 — Qwen-Image quantized repo + default_steps.** No confidently-named
  community `Qwen-Image-mflux-4bit` repo; design loads full `Qwen/Qwen-Image`
  with `--quantize 4` on load. `default_steps: 20` is a placeholder — Qwen
  family default is unverified. Phase 5 measures.
- **OQ-3 — Z-Image-Turbo / Qwen Mac wall-clock.** `timeout_seconds` values
  (180 / 900) are conservative placeholders; Mac timings are unpublished
  (proposal risk 2). Phase 5 measures and may retune.
- **OQ-4 — mflux `--metadata` sidecar exact path/filename.** Design assumes
  `<output>.json` beside the PNG. If mflux writes a differently-named sidecar
  (e.g. `<output>_metadata.json`), the wrapper's optional sidecar parse must
  adjust — but since the stdout contract is the output path (not the sidecar),
  a wrong guess degrades only the optional seed/steps logging, not the
  contract. Verify against installed mflux v0.18.0.
- **OQ-5 — share `_hf_snapshot_complete` or duplicate?** It is needed in both
  `paperbanana_dispatch.py` (deckhand) and `model_probe.py` (canonical +
  cloud copy). These live in different plugins with no shared import path;
  design duplicates the small helper in each (a shared util would need a new
  vendored module + byte-identity guard). Confirm the operator is comfortable
  with the ~20-line duplication vs a new shared vendored file.
- **OQ-6 — `mflux --version` surface.** The verify skill wants the installed
  mflux version (proposal risk 5). Whether mflux exposes `mflux --version` (vs
  only `pip show mflux` / `uv tool list`) is unverified against v0.18.0; the
  verify skill should try `mflux --version` then fall back to `pip show`.
- **OQ-7 — provider-agnostic `academic_figure_local_only` key.** Design adds a
  top-level `academic_figure_local_only` while keeping the legacy
  `ollama.academic_figure_local_only`. Confirm the operator wants the new
  top-level key (vs a per-provider `mlx.academic_figure_local_only` only).
