# Detailed design — MLX (mflux) as a second local provider (issue #124, Horizon 1)

Design date 2026-07-15 (rev 2 — post adversarial review, verdict
APPROVE-WITH-CHANGES; disposition in §11). Branch `feat/mlx-local-backend`.
Base `main` @ `7d0caa1`. Approved plan: issue #124 comment ("Plan: MLX (mflux)
as a second local provider…"). Feature proposal:
`docs/feature-proposals/124-mlx-local-backend.md`.

**This document is the single source the implementing agents follow.** It is
design-only — no production code is written here. Every function signature,
JSON blob, flag list, and diff below is meant to be transcribed, not
re-derived. Where the code cannot answer a question, it is flagged in §10
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
  `local_args` re-render contract. §2.5 fixes it.
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
    ``detect_local_backend`` but for a *server-less* CLI runtime. Both
    stages are evaluated PER CANDIDATE ENTRY (review m12): a machine with
    only ``mflux-generate-qwen`` on PATH must not select a flux2 entry.

    Candidate order: ``preferred_model`` (operator override, catalog id,
    typically from ``local-config.json`` → ``mlx.academic_figure_model``)
    first when given; then catalogued active ``mlx/*`` entries in catalog
    listing order (Klein 4B, Z-Image-Turbo, Qwen-Image — see §3).

    Per-candidate checks, all must pass (first fully-passing candidate wins):

    Stage 1 — runtime: THIS entry's ``sdk.entrypoint``
    (``mflux-generate-flux2`` / ``mflux-generate-z-image-turbo`` /
    ``mflux-generate-qwen``) is on PATH (``shutil.which``).

    Stage 2 — weights: a COMPLETE Hugging Face cache snapshot
    (``_hf_snapshot_complete``) exists for the entry's ``sdk.hf_repo`` OR
    ``sdk.hf_repo_fallback``, OR a non-empty ``mflux-save`` directory named
    in ``extra_model_dirs`` is registered for it. This is the soft guard
    against a multi-GB first-use download (locked decision 1); the
    wrapper's ``HF_HUB_OFFLINE`` env is the hard guard (§6.3).

    RAM gate: an entry carrying ``capabilities.min_ram_gb`` above the
    machine's physical RAM (``_physical_ram_gb``) is SKIPPED during
    catalog-order auto-selection. An explicit ``preferred_model`` BYPASSES
    the RAM gate with a logged warning (review m11 ruling) — the operator
    who names a model owns the consequence; auto-selection stays gated.

    Returns ``LocalBackend(provider="mlx", model=<catalog id>)`` — the
    catalog id (e.g. ``"mlx/flux2-klein-4b"``), NOT the HF repo. The catalog
    id is passed verbatim as the wrapper's ``--model`` arg and recorded as
    ``model_used`` in the manifest (see §2.7 model trace). Any failure on any
    path degrades to None; a broken/partial MLX install can never block the
    pipeline.

    Args:
        preferred_model: operator model override (catalog id). Checked
            first; bypasses the RAM gate (warning logged); still subject to
            stage 1 + stage 2. Falls through to catalog order when its
            checks fail.
        hf_home: HF cache ROOT override (the dir whose ``hub/`` child is the
            model cache). When None, hub-dir resolution follows the real
            huggingface_hub precedence (review m7): ``$HF_HUB_CACHE`` (used
            as the hub dir directly) → ``$HF_HOME/hub`` →
            ``~/.cache/huggingface/hub``.
        extra_model_dirs: additional ``mflux-save`` local weight dirs to
            treat as available (absolute paths). The BRIDGE merges
            ``local-config.json`` → ``mlx.models`` into this before calling
            (this function does no file I/O — review m16 ruling).
        timeout_seconds: reserved for signature symmetry with
            ``detect_local_backend``; the MLX probe is a synchronous
            filesystem + PATH scan with no network, so this is currently a
            no-op. Kept so ``detect_any_local_backend`` can pass one budget
            to both detectors.
    """
```

Hub-dir resolution is factored as a private helper so the same rule serves
detection, probing, and the wrapper's `--check-weights` mode:

```python
def _resolve_hf_hub_dir(hf_home: str | os.PathLike | None = None) -> Path:
    """HF hub cache dir per huggingface_hub precedence (review m7):
    explicit arg (root; hub is <arg>/hub) > $HF_HUB_CACHE (IS the hub dir)
    > $HF_HOME/hub > ~/.cache/huggingface/hub."""
```

### 2.2 `_hf_snapshot_complete` (private helper)

```python
def _hf_snapshot_complete(repo_id: str, hub_dir: Path) -> bool:
    """True when ``repo_id`` has a complete HF-cache snapshot under hub_dir.

    HF layout: ``<hub_dir>/models--<org>--<name>/`` contains ``refs/``
    (branch → revision hash files), ``snapshots/<rev>/`` (symlinks into
    ``blobs/``), and ``blobs/`` (content-addressed files; partial downloads
    are ``<hash>.incomplete``).

    Revision resolution (review m8): read ``refs/main`` when present and use
    that revision's snapshot dir; otherwise fall back to the
    newest-by-mtime ``snapshots/`` subdir.

    Completeness predicate (false-negative-safe — any doubt returns False so
    detection under-reports rather than triggering a download):
      1. ``models--<org>--<name>/`` exists (org/name → dir name: replace '/'
         with '--', prefix ``models--``).
      2. The resolved revision dir exists and has ≥1 entry.
      3. EVERY symlink in the resolved revision resolves to an existing
         path (``Path.exists()`` follows the link), AND no
         ``<target-blob>.incomplete`` sibling exists for any resolved
         target (the ``.incomplete`` check is scoped to the resolved
         revision's blobs, not the whole ``blobs/`` dir — review m8).
    Any OSError → False.

    Accepted residual (review m8): a download interrupted BETWEEN files can
    leave a revision whose present symlinks all resolve while later files
    were never started — indistinguishable from complete without the repo
    manifest. The wrapper's ``HF_HUB_OFFLINE`` hard guard backstops this:
    the render fails fast with the weights-missing message instead of
    downloading.
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
    """Return the first available local backend in the given provider order.

    PARAMETER-ONLY — this function performs NO file I/O and never reads
    local-config.json (review m16 ruling); the bridge SKILL step reads the
    config and passes everything in. Tries each provider in
    ``provider_order`` and returns the first ``LocalBackend`` a detector
    yields:
      - ``"ollama"`` → ``detect_local_backend(base_url,
        preferred_model=preferred_ollama_model, timeout_seconds=...)``
      - ``"mlx"``    → ``detect_mlx_backend(preferred_model=preferred_mlx_model,
        hf_home=..., extra_model_dirs=extra_mlx_dirs,
        timeout_seconds=...)``

    ``provider_order=None`` → ``("ollama", "mlx")`` (Ollama-first — locked
    decision 5; Horizon 2 may flip this). Unknown provider names in the
    order are skipped with a debug log. Returns None when no provider yields
    a backend — the caller (``build_dispatch_payload``) then takes the
    paperbanana/cloud ladder or, under ``local_only``, returns
    ``local_only_blocked``.

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

**`local_args["steps"]` (review M4c).** `build_dispatch_payload` gains one
provider-aware behaviour: when the detected backend's provider is `"mlx"`,
look up the catalog entry for `local_backend.model` and copy
`capabilities.render_steps` into `local_args["steps"]`. All three `mlx/*`
entries carry `render_steps` (§3.2), so the key is always present for MLX
dispatches; the ollama branch is unchanged (its entries carry no
`render_steps`; the ollama wrapper's default 8 stands). The bridge then
ALWAYS passes `--steps` on the MLX render (§5) — never relying on mflux's
own default (mflux silently defaults to 25 steps when `--model` is an HF
repo id, a confirmed trap).

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

**Intentional behaviour change (review m15):** a *legacy* caller that passes
`backend_used="ollama_local"` explicitly on a dispatch whose
`local_provider` is EMPTY previously took the enrichment branch; after the
fix it falls to the `else` (fallback-reason) branch. This is correct — such
a dispatch has no `local_args` to enrich from, so the old branch emitted
empty strings — but it is a behaviour change and T3 documents it in the
commit message plus a pinning test
(`test_manifest_entry_legacy_ollama_local_without_provider_takes_fallback_branch`).

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
per-provider concrete commands stay generic here; the verify skill (§6.5) and
install guide carry the exact repo ids.)

### 2.7 model-string trace (single source of truth)

`mlx/flux2-klein-4b` (catalog id)
 → `detect_mlx_backend` returns `LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")`
 → `build_dispatch_payload` sets `local_model="mlx/flux2-klein-4b"`, `backend="mlx"`, `local_args["steps"]=20`
 → bridge Step 4.6 passes `--model mlx/flux2-klein-4b --steps 20` to the wrapper
 → wrapper `MLX_MODEL_REGISTRY` maps catalog id → (entrypoint, hf_repo, hf_repo_fallback, default_steps, quantize, timeout)
 → wrapper reports the actually-loaded repo (`MFLUX_REPO_USED=<repo>` on stderr — review m19); bridge stashes it as `local_args["hf_repo_used"]`
 → `build_manifest_entry` records `model_used="mlx/flux2-klein-4b"`, `backend="mlx_local"`, `local_provider="mlx"`, and `local_args` (including `hf_repo_used`).

Rationale for using the catalog id (not the HF repo) as `LocalBackend.model`:
the catalog entry names a *specific* repo via `sdk.hf_repo`, so the id is as
precise as Ollama's installed-tag; it keeps mflux-specific repo strings out of
the seam and the manifest identity field; and it makes the manifest
re-renderable by iterate-slide via the catalog rather than a raw HF path.
When the wrapper falls back to `hf_repo_fallback`, manifest fidelity is kept
by the `hf_repo_used` value inside `local_args` (m19).

## 3. Catalog design — three `mlx/*` entries + schema diff

### 3.1 Schema diff (`model-catalog/model-catalog.schema.json`)

The catalog is validated against this schema by
`plugins/integration_tests/test_model_catalog_integrity.py::TestSchema`
(full jsonschema). Both `sdk` and `capabilities` are
`additionalProperties: false`, so the new fields MUST be declared or the
entries fail CI. Add:

Under `definitions.model.properties.capabilities.properties` add:
```json
"min_ram_gb": {"type": "number", "minimum": 1, "description": "Minimum physical RAM (GB) to load this local model — catalog-order detection skips models above the machine's RAM; an explicit operator preferred_model bypasses with a warning (issue #124)."},
"render_steps": {"type": "integer", "minimum": 1, "description": "Pipeline-validated inference steps the BRIDGE passes as --steps on every render (issue #124: the family-native sdk.default_steps is often too low for label fidelity — klein 4B needs 20 per the 2026-07-11 dogfood — and mflux silently defaults to 25 when --steps is omitted)."}
```

Under `definitions.model.properties.sdk.properties` add:
```json
"entrypoint": {"type": "string", "minLength": 1, "description": "CLI entry point for CLI-dispatched local providers (mflux: 'mflux-generate-flux2' etc.)."},
"hf_repo": {"type": "string", "minLength": 1, "description": "Hugging Face repo id the wrapper loads and detection checks for a complete snapshot (mlx/mflux). Prefer an ungated pre-quantized export (repo name contains '-mflux-')."},
"hf_repo_fallback": {"type": "string", "minLength": 1, "description": "Alternate HF repo id (typically the full-precision base) accepted when the primary is not cached. Loaded with on-load --quantize per sdk.quantize."},
"default_steps": {"type": "integer", "minimum": 1, "description": "FAMILY-NATIVE default inference steps — the wrapper's fallback when --steps is somehow absent. The pipeline value the bridge passes is capabilities.render_steps, not this."},
"quantize": {"type": ["integer", "null"], "minimum": 3, "maximum": 8, "description": "mflux on-load quantization bits, applied ONLY when the resolved repo is full-precision (repo name lacks '-mflux-'). Pre-quantized repos are loaded as-is. Documented mflux values: 3, 4, 5, 6, 8 — kept as an open integer range, not a closed enum, pending verification of the pinned mflux version's parser (review m18). null = never quantize."}
```

Also extend the `sdk.api` description to list `mflux_cli`. Bump
`catalog_version` `1.0.0 → 1.1.0` (minor: new models) and `updated` to
`2026-07-15`.

### 3.2 The three entries (exact JSON — append to `models[]`)

Per-repo licences (review M6 — the DERIVATIVE repo's licence governs the
download, regardless of the base model's licence) are stated in each entry's
notes and MUST be re-verified against the HF model card during T1:

| HF repo | Licence | Size |
|---|---|---|
| `Runpod/FLUX.2-klein-4B-mflux-4bit` | verify on model card (base is Apache 2.0; §10 OQ-A) | 4.3 GB; needs mflux ≥ 0.16 |
| `black-forest-labs/FLUX.2-klein-4B` | Apache 2.0 (confirmed) | ~13 GB |
| `filipstrand/Z-Image-Turbo-mflux-4bit` | **Tongyi Qianwen licence — NOT Apache 2.0** (confirmed) | small |
| `Tongyi-MAI/Z-Image-Turbo` | Apache 2.0 (confirmed) | full precision |
| `filipstrand/Qwen-Image-mflux-6bit` | verify on model card (base is Apache 2.0; §10 OQ-A) | ~15–16 GB |
| `Qwen/Qwen-Image` | Apache 2.0 (confirmed) | ~40 GB |

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
    "render_steps": 20,
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
    "hf_repo_fallback": "black-forest-labs/FLUX.2-klein-4B",
    "default_steps": 4,
    "quantize": 4
  },
  "notes": "FLUX.2 Klein 4B via mflux. Primary: pre-quantized 4-bit community export (4.3 GB, fast cold-load, requires mflux >= 0.16; licence per model card — verify, base is Apache 2.0). Fallback: black-forest-labs/FLUX.2-klein-4B (Apache 2.0, ~13 GB, quantized 4-bit on load). default_steps 4 is the family-native distilled value; render_steps 20 is what the pipeline passes — the 2026-07-11 dogfood showed 4B reaches Klein-9b grade at 20 steps + annotation pattern. MLX default draft model. Horizon-2 gate: Phase 5 dogfood must beat/match the Ollama Klein-9b 8/9 baseline before promotion into role_defaults.local_draft."
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
    "render_steps": 9,
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
    "quantize": 4
  },
  "notes": "Z-Image-Turbo via mflux, requires mflux >= 0.13. LICENCE NOTE (issue #124 review M6): the pre-quantized primary repo is under the Tongyi Qianwen licence, NOT Apache 2.0 — the derivative repo's licence governs the download. Operators needing pure Apache 2.0 should pull the fallback Tongyi-MAI/Z-Image-Turbo (Apache 2.0, full precision, quantized 4-bit on load) instead. 9-step distilled (render_steps == default_steps). timeout_seconds 180 is a conservative placeholder — Mac wall-clock unpublished; Phase 5 measures (proposal risk 2)."
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
    "min_ram_gb": 24,
    "render_steps": 20,
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
    "hf_repo": "filipstrand/Qwen-Image-mflux-6bit",
    "hf_repo_fallback": "Qwen/Qwen-Image",
    "default_steps": 20,
    "quantize": 6
  },
  "notes": "Qwen-Image via mflux, requires mflux >= 0.11. Primary: author-maintained pre-quantized 6-bit export (~15-16 GB; licence per model card — verify, base is Apache 2.0); min_ram_gb 24 sized for the 6-bit primary (review OQ-2 ruling). Fallback: Qwen/Qwen-Image (Apache 2.0, ~40 GB download — called out in the install guide) quantized 6-bit on load; the on-load path needs materially more RAM/disk than the primary. Strongest open-weights in-image text renderer; the challenger most likely to beat the Klein-9b label-fidelity baseline. default_steps 20 confirmed as the family default (review OQ-2). timeout_seconds 900 remains a placeholder pending Phase 5 (§10 OQ-B)."
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
    (e.g. 'Runpod/FLUX.2-klein-4B-mflux-4bit') with a complete snapshot
    under the hub dir resolved per huggingface_hub precedence (review m7:
    ``hf_home`` arg → ``$HF_HUB_CACHE`` → ``$HF_HOME/hub`` →
    ``~/.cache/huggingface/hub``), plus any non-empty ``mflux-save`` dir
    basenames from ``extra_model_dirs``; or
    ``{'status':'skipped','reason': ...}`` when no catalogued mflux entry
    point is on PATH (mflux CLI not installed).

    Snapshot completeness follows the same refs/main-resolved,
    revision-scoped algorithm as ``_hf_snapshot_complete`` (§2.2); a private
    copy lives here — see §10 OQ-C on the duplication trade-off. Never
    raises; scan errors → skipped with the reason string.
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

### 4.3 Local-provider classification — `not_installed` verdict (review M3 ruling)

For a LOCAL provider, "absent upstream" means *not downloaded/pulled on this
machine* — it says nothing about retirement. Classifying a not-yet-pulled
model `suspect_retired` trains operators to ignore alarms. Add:

```python
#: Providers whose probe reflects LOCAL installation state, not upstream
#: existence — absence means "not installed here", never "retired".
LOCAL_PROVIDERS = frozenset({"ollama", "mlx"})
```

In `classify_entries`, after the existing `verified` / `confirmed_retired`
determinations, the not-matched + non-retired branch becomes provider-aware:

- provider in `LOCAL_PROVIDERS` → verdict `"not_installed"` with a
  remediation note:
  - ollama: `"not installed locally — run: ollama pull <entry id>"`
  - mlx: `"weights not cached locally — run: hf download <sdk.hf_repo>"`
- otherwise → `"suspect_retired"` exactly as today.

Retired local entries keep `confirmed_retired` (status check precedes the
local branch). **Side effect on existing tests:** `test_model_probe.py::
TestClassification::test_ollama_tag_prefix_matches` currently asserts
`x/z-image-turbo` is `suspect_retired` when not installed — under this
ruling it must be updated to expect `not_installed` (§7.3). Any verify-skill
prose that renders verdict labels should list the new verdict.

### 4.4 `_CANDIDATE_FILTERS["mlx"]` + report wiring + UNPROBEABLE

- Add to `_CANDIDATE_FILTERS`: `"mlx": ("-mflux-",)` — the community
  quantized-repo suffix convention (`…-mflux-4bit`, `…-mflux-8bit`). New
  candidates = cached mflux repos no catalog entry covers.
- `find_new_candidates`: build `known` from ids/aliases AND every mlx
  entry's `hf_repo`/`hf_repo_fallback`, so a catalogued repo is never
  reported as a candidate; the existing substring filter then applies.
- `probe_report` default probes dict gains `"mlx": probe_mlx_models()`.
- `UNPROBEABLE_PROVIDERS` is UNCHANGED — mlx is probeable (filesystem scan),
  like ollama. Document this in the module note: "mlx probing scans the HF
  cache; there is no server API but 'installed' is directly observable."

## 5. Bridge Step 4.6 diff outline (`imagegen-bridge/SKILL.md`)

The academic-figure dispatch (§ Step 4.6) currently reads
`ollama.academic_figure_model` and calls
`detect_local_backend(preferred_model=preferred)`. Change:

1. **Build-payload block** — read the config keys HERE (the seam function is
   parameter-only, review m16) and call the composed detector. Note the
   `local_only` precedence: the top-level key, WHEN PRESENT, wins outright;
   both legacy provider-namespaced keys sit uniformly below it (review m10):
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
       provider_order=tuple(cfg['local_provider_order'])
           if 'local_provider_order' in cfg else None,
       extra_mlx_dirs=tuple(mlx_cfg.get('models', ())),
   )
   # local_only precedence (m10): slide key > top-level key (when present)
   # > either legacy provider key.
   if 'academic_figure_local_only' in cfg:
       machine_local_only = bool(cfg['academic_figure_local_only'])
   else:
       machine_local_only = bool(
           ollama_cfg.get('academic_figure_local_only', False)
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
   LOCAL_STEPS=$(echo "$DISPATCH_JSON" | jq -r '.local_args.steps')
   OUT_PNG=$(echo "$DISPATCH_JSON" | jq -r '.output_dir')/slide-$(printf '%02d' $SLIDE_NUMBER)-academic-figure-mlx.png
   # Operator quantize override (local-config.json -> mlx.quantize) — m9
   MLX_Q=$(python3 -c "import json;print(json.load(open('local-config.json')).get('mlx',{}).get('quantize',''))" 2>/dev/null)
   python3 "$MLX_PLUGIN_ROOT/src/generate_image.py" \
     --prompt "$LOCAL_PROMPT" --model "$LOCAL_MODEL" \
     --steps "$LOCAL_STEPS" \
     ${MLX_Q:+--quantize "$MLX_Q"} \
     --width $(echo "$DISPATCH_JSON" | jq -r '.local_args.width') \
     --height $(echo "$DISPATCH_JSON" | jq -r '.local_args.height') \
     --output "$OUT_PNG" 2> >(tee /tmp/mlx-render-stderr.log >&2)
   # m19: keep repo fidelity — the wrapper reports the actually-loaded repo.
   REPO_USED=$(grep -o 'MFLUX_REPO_USED=.*' /tmp/mlx-render-stderr.log | cut -d= -f2)
   # Stash REPO_USED into local_args.hf_repo_used before build_manifest_entry.
   ```
   `--steps` is ALWAYS passed (review M4c) — `local_args.steps` carries the
   catalog's `capabilities.render_steps` (§2.4); never let mflux fall back
   to its silent 25-step default. Then the SAME free critique loop, F11
   simplified-label rebuild, **F10 operator gate** (ladder mode — the gate
   prose is repeated verbatim in this branch so a grep for the gate text
   finds it in the mlx branch too; T5 DoD pins this), local_only handling,
   and `build_manifest_entry` call as the ollama branch — `backend_used`
   defaults to the dispatch backend → `mlx_local` (the §2.5 fix makes the
   manifest correct automatically). The branch text says "This is the free
   local tier — F10/F12 gate semantics are IDENTICAL to the ollama branch;
   MLX is a $0 tier."
   Restructure the two branches as one "local draft" branch keyed on
   `dispatch.backend in ("ollama", "mlx")` that selects plugin root +
   filename suffix + extra flags from `dispatch.local_provider`, to avoid
   duplicating the loop prose. (Either shape is acceptable; the
   keyed-single-branch is preferred for maintainability — but the F10 gate
   text must appear in whatever branch structure ships.)

3. **`local-config.json` new keys** (documented in the SKILL prose + install
   guide):

   | Key | Type | Meaning | Precedence |
   |---|---|---|---|
   | `local_provider_order` | array | detection order, default `["ollama","mlx"]` | arg > this > built-in default |
   | `mlx.academic_figure_model` | string (catalog id) | preferred mlx model (bypasses RAM gate with warning — m11) | slide > this > catalog order |
   | `mlx.models` | array of dirs | extra `mflux-save` local weight dirs | additive |
   | `mlx.quantize` | int 3–8 | override on-load quantize | passed to wrapper `--quantize` (m9) |
   | `academic_figure_local_only` | bool | provider-agnostic paid-tier opt-out | slide > **this (when present)** > either legacy `<provider>.academic_figure_local_only` (m10) |

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
drift-guard tests (§7.1, §7.5) assert **full per-field equality** between the
registry and the catalog's `mlx/*` entries — every duplicated field, not just
the keys (review M2) — so the two can never silently diverge. *(This is a
considered deviation from the task's "mirror how cloud vendors the catalog"
framing — see final report.)*

```python
MLX_MODEL_REGISTRY = {
    # catalog id -> dispatch metadata. DRIFT-GUARDED: tests assert each
    # value dict equals the catalog entry's derived fields exactly (M2).
    "mlx/flux2-klein-4b": {
        "entrypoint": "mflux-generate-flux2",
        "hf_repo": "Runpod/FLUX.2-klein-4B-mflux-4bit",
        "hf_repo_fallback": "black-forest-labs/FLUX.2-klein-4B",
        "default_steps": 4,
        "quantize": 4,
        "timeout": 300,
    },
    "mlx/z-image-turbo": {
        "entrypoint": "mflux-generate-z-image-turbo",
        "hf_repo": "filipstrand/Z-Image-Turbo-mflux-4bit",
        "hf_repo_fallback": "Tongyi-MAI/Z-Image-Turbo",
        "default_steps": 9,
        "quantize": 4,
        "timeout": 180,
    },
    "mlx/qwen-image": {
        "entrypoint": "mflux-generate-qwen",
        "hf_repo": "filipstrand/Qwen-Image-mflux-6bit",
        "hf_repo_fallback": "Qwen/Qwen-Image",
        "default_steps": 20,
        "quantize": 6,
        "timeout": 900,
    },
}
DEFAULT_MODEL = "mlx/flux2-klein-4b"
DEFAULT_TIMEOUT = 300
# Cross-provider OOM protection (review M5): the mlx wrapper takes the
# OLLAMA lock FIRST, then its own. Ordering is deadlock-safe because the
# ollama wrapper only ever takes one lock.
OLLAMA_LOCK_PATH = Path(tempfile.gettempdir()) / "jack-tar-ollama-image.lock"
LOCK_PATH = Path(tempfile.gettempdir()) / "jack-tar-mlx-image.lock"
DEFAULT_LOCK_WAIT_TIMEOUT = 600     # mirror issue #75
STALE_LOCK_AGE_SECONDS = 1800       # mirror issue #75
```

**argparse spec** — ollama flags verbatim + mlx additions:

| Flag | Type | Default | Notes |
|---|---|---|---|
| `--prompt` | str | (required¹) | ¹ not required with `--check-weights` |
| `--model` | str | `mlx/flux2-klein-4b` | catalog id; must be a registry key |
| `--output` | str | `output/YYYYMMDD-HHMMSS.png` | same as ollama |
| `--width` | int | 1024 | |
| `--height` | int | 1024 | |
| `--steps` | int | None | None → registry `default_steps`; ALWAYS emitted in argv (M4d) |
| `--seed` | int | None | omitted from CLI when None |
| `--timeout` | int | None | None → registry `timeout`; DEFAULT_TIMEOUT for unknown |
| `--lock-wait-timeout` | int | 600 | issue #75; single deadline shared across BOTH lock acquisitions (M5) |
| `--no-lock` | flag | off | issue #75; skips BOTH locks |
| `--quantize` / `-q` | int (3–8) | None | mlx-only; None → registry `quantize`; only emitted when loading a full-precision repo (see below) |
| `--check-weights` | flag | off | mlx-only (review m17): no render — print per-registry-model `READY`/`NOT_READY <hf download cmd>` using the Python snapshot-completeness check, exit 0. The verify skill shells to this instead of re-implementing the check in bash. |

**Model resolution** (`resolve_model`): look up `--model` in
`MLX_MODEL_REGISTRY`; unknown id → exit 1 with the known-ids list (mirrors the
catalog's `UnknownModelError` shape). Returns the metadata dict.

**Pre-quantized detection + quantize semantics** (review m13):

```python
def _repo_prequantized(repo_id: str) -> bool:
    """True for community pre-quantized exports ('-mflux-' naming convention)."""
    return "-mflux-" in repo_id
```

`-q` is emitted ONLY when the repo being loaded is full-precision:
pre-quantized primary → no `-q`; full-precision fallback (or a
full-precision primary) → `-q <bits>` where bits = explicit `--quantize` if
given else the registry's `quantize`. This keeps the fallback path's RAM
envelope matched to the primary's quantization level — the reason the
fallback exists is weight availability, not a precision upgrade. Note in the
module docstring: the on-load-quantize fallback path still downloads/holds
the full-precision snapshot on disk (~13 GB klein / ~40 GB qwen) — RAM
during load is bounded by mflux's layer-wise quantization but disk is not;
the install guide carries the table.

**Subprocess construction** (`_build_argv(meta, repo, prompt, width, height,
steps, seed, quantize)`):
```
[meta["entrypoint"],
 "--model", repo,                     # HF repo id (primary or fallback)
 "--prompt", prompt,
 "--width", str(width), "--height", str(height),
 "--steps", str(steps if steps is not None else meta["default_steps"]),   # ALWAYS present (M4d)
 "--output", str(output_path),
 "--metadata"]                         # writes JSON sidecar next to output
 + (["--seed", str(seed)] if seed is not None else [])
 + (["-q", str(q)] if (not _repo_prequantized(repo)
                       and (q := quantize if quantize is not None else meta["quantize"]) is not None)
    else [])
```
`--steps` is unconditionally present for every model (review M4d) — mflux
silently defaults to 25 steps when `--steps` is omitted and `--model` is an
HF repo id; the wrapper never exposes that trap. Fallback-repo handling: try
`hf_repo`; if the run fails with a weights-missing signature AND
`hf_repo_fallback` is set, retry once with the fallback repo (with `-q` per
the rule above). Both attempts run under HF_HUB_OFFLINE — neither downloads.

**Refusal-to-download guard.** Run the subprocess with an environment that
forces the HF stack offline so a cache miss fails FAST instead of pulling
multi-GB weights:
```python
env = {**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
```
Review-confirmed sound: mflux resolves all weights via huggingface_hub's
`snapshot_download`, which honours `HF_HUB_OFFLINE=1` (cache-only
resolution; raises `LocalEntryNotFoundError` on a miss rather than hitting
the network). `TRANSFORMERS_OFFLINE=1` is not strictly necessary for mflux
but is kept as belt-and-braces. This is the *hard* guard behind detection's
*soft* (snapshot-completeness) guard — even if detection and render race, or
the m8 between-files residual bites, the render cannot download.

**Execution + stdout/stderr contract.** Use `subprocess.run(argv, env=env,
timeout=resolved_timeout, capture_output=True, text=True)`. On success:
- parse the `--metadata` JSON sidecar — mflux writes it at
  `output_path.with_suffix(".metadata.json")` (i.e. `<output stem>.metadata.json`
  beside the PNG; the metadata is also embedded in the PNG's EXIF — review
  OQ-4 resolution) — for the actual seed/steps used (logging only);
- emit `MFLUX_REPO_USED=<repo>` on **stderr** (review m19) so the bridge can
  record which repo (primary or fallback) actually produced the image;
- **print the output path as the last stdout line** — the exact ollama
  contract (`print(str(output_path))`), so the bridge's `OUT_PNG`-based flow
  is unchanged.

**Partial-output cleanup (review m14).** On ANY non-success exit — timeout
(`subprocess.TimeoutExpired`), non-zero return code, or an exception after
the subprocess started — the wrapper unlinks `output_path` (and the
`.metadata.json` sidecar) if present, inside a `finally`-shaped guard, so a
killed mflux never leaves a partial PNG that downstream steps could mistake
for a render.

**Error taxonomy** (all exit 1, message to stderr, mirror ollama tone):

| Condition | Detection | Message |
|---|---|---|
| CLI missing | `shutil.which(meta["entrypoint"]) is None` before run | `mflux not installed (or too old — {model} needs the '{entrypoint}' entry point) — run: uv tool install --upgrade mflux` |
| weights missing | non-zero exit + `LocalEntryNotFound`/`offline`/`Can't load` in stderr (after fallback repo tried) | `weights for {model} not cached — run: hf download {hf_repo}` (no download attempted) |
| timeout | `subprocess.TimeoutExpired` | `Generation timed out after {timeout}s. Try a smaller model or fewer --steps.` (partial output unlinked — m14) |
| OOM | non-zero exit + `metal`/`out of memory`/`MTLBuffer`/`bad_alloc` in stderr | `{model} may exceed available RAM — try a smaller model or higher quantization (-q 4).` |
| other non-zero | fallthrough | `mflux error (exit {rc}): {stderr tail 200 chars}` |

**Nested single-flight lock (review M5 ruling).** Two independent per-provider
locks do not prevent an Ollama render running concurrently with an mflux
weight load — on one GPU/unified-memory machine that is the OOM scenario the
locks exist to prevent. The mlx wrapper therefore acquires **the ollama lock
FIRST** (`/tmp/jack-tar-ollama-image.lock`), **then its own**
(`/tmp/jack-tar-mlx-image.lock`), both via the ollama `_single_flight_lock`
contextmanager copied verbatim (parameterised by path):

```python
with _single_flight_lock(OLLAMA_LOCK_PATH, deadline_seconds):
    with _single_flight_lock(LOCK_PATH, remaining(deadline)):
        _do_render(...)
```

- **Deadlock safety:** the ollama wrapper only ever takes ONE lock (its
  own), so there is exactly one multi-lock acquirer and one global
  acquisition order — no cycle is possible.
- `--lock-wait-timeout` is a SINGLE deadline shared across both
  acquisitions (monotonic deadline computed once).
- `--no-lock` skips both locks.
- Stale-reclaim (1800 s mtime) applies to each lock independently, exactly
  as in the ollama wrapper.
- **Documented residual:** this serialises ALL local image work — an mflux
  render can wait behind a long Ollama render (up to klein's 600 s budget)
  even on machines with headroom. Accepted for Horizon 1 (correctness over
  throughput on the common single-GPU laptop). **Horizon-2 follow-up
  option:** replace both files with one shared
  `/tmp/jack-tar-local-image.lock` taken by both wrappers, retiring the
  nesting.

### 6.4 `skills/image/SKILL.md` outline

Frontmatter `name: image`, `allowed-tools: Bash(python *), Bash(python3 *)`.
Sections: prerequisites (mflux installed, weights pulled — link install
guide); argument parse (`--model --steps --seed --quantize --width --height`);
invoke `src/generate_image.py`; note the nested single-flight lock (ollama
lock first — §6.3) + `--no-lock`; note this is a $0 local tier; point at
`/jack-tar-mlx:verify` when a render fails.

### 6.5 `skills/verify/SKILL.md` outline

Mirror `jack-tar-ollama/skills/verify/SKILL.md` STATUS-line contract (the
integration test will assert `PLUGIN: jack-tar-mlx`, `STATUS: FULLY_AVAILABLE`,
`STATUS: NOT_AVAILABLE`). Steps:
1. **Runtime check** — per catalogued entry point: `command -v
   mflux-generate-flux2`, `command -v mflux-generate-z-image-turbo`,
   `command -v mflux-generate-qwen`. Report per-family presence — a missing
   entry point on an otherwise-working install usually means the installed
   mflux predates that family (per-family minimums: qwen ≥ 0.11, z-image
   ≥ 0.13, flux2 ≥ 0.15; the Runpod klein repo needs ≥ 0.16 — review m12).
   ALL absent → `DEPENDENCIES: mflux: NOT_READY (run: uv tool install
   --upgrade mflux)`, `STATUS: NOT_AVAILABLE`.
2. **Version** — there is NO plain `mflux` entry point and no `--version`
   flag (review OQ-6 resolution). Resolve the installed version via
   `uv tool list 2>/dev/null | grep mflux`, falling back to
   `pip show mflux`, falling back to
   `python3 -c "import importlib.metadata as m; print(m.version('mflux'))"`.
   Surface it in the report (regression-tracking, proposal risk 5) and flag
   when below a family minimum.
3. **Weights check** — shell to the wrapper's Python helper, NOT a bash
   re-implementation (review m17):
   `python3 "$MLX_PLUGIN_ROOT/src/generate_image.py" --check-weights` —
   prints per-model `READY` / `NOT_READY (run: hf download <repo>)` using
   the same refs/main-resolved snapshot-completeness check as detection.
4. **HF cache location** (resolved per m7 precedence: `HF_HUB_CACHE` →
   `HF_HOME/hub` → `~/.cache/huggingface/hub`) **+ disk usage** line.
5. **STATUS**: `FULLY_AVAILABLE` when runtime + ≥1 model present;
   `NOT_AVAILABLE` when runtime present but no weights (with the exact pull
   command) or runtime absent.

### 6.6 `CLAUDE.md` outline

Short, mirroring `jack-tar-ollama/CLAUDE.md`: purpose, prerequisites
(operator-installed runtime + weights, Apple Silicon), skills table, the
nested single-flight lock note (issue #75 parity + review M5:
`/tmp/jack-tar-ollama-image.lock` then `/tmp/jack-tar-mlx-image.lock`), a
"never auto-downloads / HF_HUB_OFFLINE guard" note, quick start.

## 7. Test matrix

### 7.1 `plugins/jack-tar-mlx/tests/test_generate_image.py` (mirror the 27 ollama tests)

Mock `subprocess.run` (mflux is not installed in CI). Cases:
- `test_builds_argv_with_entrypoint_and_repo` — klein id → `mflux-generate-flux2 --model Runpod/...`.
- `test_steps_always_present_in_argv` — for EVERY registry model, `--steps` appears in the constructed argv even when the caller omits it (review M4d pinning test; guards the mflux silent-25 trap).
- `test_prints_output_path_on_stdout` — stdout last line == resolved output path.
- `test_emits_repo_used_on_stderr` — `MFLUX_REPO_USED=<repo>` line present (m19).
- `test_creates_output_directory` — parent dir made.
- `test_default_output_path_uses_timestamp` — monkeypatched clock.
- `test_seed_included_in_argv` / `test_seed_omitted_when_absent`.
- `test_steps_defaults_from_registry` (klein→4, z-image→9, qwen→20 when caller omits).
- `test_explicit_steps_override`.
- `test_quantize_omitted_for_prequantized_primary` (klein primary: no `-q`).
- `test_quantize_applied_on_fullprecision_fallback` (klein fallback → `-q 4`; qwen fallback → `-q 6` — review m13).
- `test_explicit_quantize_override_still_skipped_on_prequantized` (m13 semantics: `-q` never emitted for a `-mflux-` repo).
- `test_timeout_from_registry` (klein 300 / z-image 180 / qwen 900) / `test_unknown_model_exits` / `test_explicit_timeout_override`.
- `test_subprocess_env_forces_hf_offline` — `HF_HUB_OFFLINE=1` & `TRANSFORMERS_OFFLINE=1` in the passed env (the refusal-to-download guard).
- `test_metadata_flag_present` — `--metadata` in argv.
- `test_metadata_sidecar_path_uses_metadata_json_suffix` — parse path is `with_suffix(".metadata.json")` (OQ-4 resolution).
- `test_cli_missing_exits_with_install_hint` — `shutil.which` → None.
- `test_weights_missing_exits_without_download` — stderr `LocalEntryNotFound`; asserts message names `hf download <repo>` and NO retry hits network.
- `test_fallback_repo_tried_when_primary_missing` — z-image primary miss → fallback repo retried once, with `-q 4` in the fallback argv.
- `test_timeout_expired_message` — `subprocess.TimeoutExpired`.
- `test_timeout_removes_partial_output` — a partial PNG + sidecar written before the timeout are unlinked (review m14).
- `test_nonzero_exit_removes_partial_output` — same cleanup on non-zero rc (m14).
- `test_oom_hint_on_metal_error` — stderr `out of memory` → RAM hint.
- `test_other_nonzero_exit_surfaces_stderr_tail`.
- `test_custom_dimensions`.
- `test_check_weights_mode_lists_models_without_render` — `--check-weights` prints READY/NOT_READY per registry model, no subprocess render, exit 0 (m17).
- Lock tests (copy ollama's 9, plus ordering): `test_no_lock_flag_skips_both_locks`,
  `test_default_invocation_acquires_and_releases_both_locks`,
  `test_lock_acquisition_order_ollama_first` — recorded acquisition order is
  `[jack-tar-ollama-image.lock, jack-tar-mlx-image.lock]` (review M5),
  `test_lock_wait_timeout_is_shared_deadline` — a slow ollama-lock
  acquisition eats into the mlx-lock budget (M5),
  `test_lock_wait_timeout_propagates`, `test_lock_acquisition_timeout_exits`,
  `test_lock_acquired_when_uncontended`, `test_lock_released_on_exception`,
  `test_lock_blocked_then_acquired`, `test_lock_timeout_raises`,
  `test_stale_lock_is_reclaimed` — pointed at the mlx lock path.
- `test_registry_matches_catalog_mlx_entries` — **full-value drift guard
  (review M2)**: for every active catalog `mlx/*` entry, assert
  `MLX_MODEL_REGISTRY[entry.id] == {"entrypoint": sdk.entrypoint,
  "hf_repo": sdk.hf_repo, "hf_repo_fallback": sdk.get("hf_repo_fallback"),
  "default_steps": sdk.default_steps, "quantize": sdk.quantize,
  "timeout": capabilities.timeout_seconds}` AND registry keys == the entry-id
  set (no extra, no missing). Loads the vendored deckhand catalog via a path
  constant.

### 7.2 `plugins/jack-tar-deckhand/tests/test_paperbanana_dispatch.py`

- `test_detect_mlx_backend_returns_none_when_no_cli` (monkeypatch `shutil.which`→None).
- `test_detect_mlx_backend_checks_selected_entrys_entrypoint` — only `mflux-generate-qwen` on PATH → klein/z-image skipped, qwen selectable (review m12).
- `test_detect_mlx_backend_returns_none_when_cli_but_no_weights` (which OK, snapshot check False).
- `test_detect_mlx_backend_returns_catalog_id_when_weights_complete` (fake hub tree via tmp_path; asserts `LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")`).
- `test_detect_mlx_backend_honours_preferred_model`.
- `test_detect_mlx_backend_ram_gate_skips_qwen_in_catalog_order` (monkeypatch `_physical_ram_gb`→16; only qwen weights present, no preferred → None — review m11).
- `test_detect_mlx_backend_preferred_model_bypasses_ram_gate_with_warning` (`_physical_ram_gb`→16, preferred=`mlx/qwen-image` with weights → backend returned; `caplog` records the warning — review m11 ruling).
- `test_detect_mlx_backend_ram_gate_disabled_when_ram_unknown` (`_physical_ram_gb`→None → qwen offered in catalog order).
- `test_resolve_hf_hub_dir_precedence` — `HF_HUB_CACHE` (used directly) beats `HF_HOME/hub` beats `~/.cache/huggingface/hub` (review m7).
- `test_detect_mlx_backend_honours_hf_hub_cache_env` — weights under a `HF_HUB_CACHE`-pointed dir are found (m7 acceptance).
- `test_hf_snapshot_complete_true_for_full_snapshot` / `_false_for_incomplete_blob_in_resolved_revision` / `_false_for_dangling_symlink` / `_false_for_missing_repo`.
- `test_hf_snapshot_complete_resolves_revision_via_refs_main` — with two snapshot dirs, the refs/main-named revision is the one checked (review m8).
- `test_detect_any_local_backend_prefers_ollama_by_default` (both up, `provider_order=None` → ollama — pins the no-arg default-order path).
- `test_detect_any_local_backend_falls_through_to_mlx_when_ollama_down` (the #124 acceptance case).
- `test_detect_any_local_backend_honours_provider_order` (order `("mlx","ollama")` → mlx wins even with ollama up).
- `test_detect_any_local_backend_none_when_no_provider`.
- `test_detect_any_local_backend_does_no_file_io` — monkeypatch `builtins.open`/`Path.open` to raise; the function still runs on injected params (review m16 pin).
- `test_dispatch_payload_mlx_local_args_carry_render_steps` — `local_args["steps"] == 20` for klein (review M4c).
- `test_manifest_entry_for_local_mlx_render` — `backend_used` defaults to `mlx_local`; asserts `source_prompt`/`local_provider`/`local_args`/`model_used` (the `:647` regression guard).
- `test_manifest_entry_escalated_from_mlx_to_paperbanana_after_gate`.
- `test_manifest_entry_legacy_ollama_local_without_provider_takes_fallback_branch` — pins the intentional m15 behaviour change.
- `test_local_only_blocked_message_names_both_providers`.
- `test_build_dispatch_payload_mlx_backend_sets_backend_and_local_model`.
- Regression: all 69 existing tests still pass (ollama paths untouched).

### 7.3 `plugins/jack-tar-cloud/tests/test_model_probe.py`

- `test_probe_mlx_skipped_when_cli_absent` (which→None → skipped).
- `test_probe_mlx_lists_complete_snapshot_repos` (fake hub tree).
- `test_probe_mlx_honours_hf_hub_cache_env` (review m7).
- `test_mlx_entry_matches_on_hf_repo` — `classify_entries` verifies `mlx/flux2-klein-4b` when its `hf_repo` is in the probe set.
- `test_mlx_entry_not_installed_when_repo_absent` — verdict `not_installed` with an `hf download <repo>` note (review M3 ruling; REPLACES the previously-designed `test_mlx_entry_suspect_when_repo_absent`, which pinned the wrong behaviour).
- `test_ollama_entry_not_installed_when_not_pulled` — ollama is in `LOCAL_PROVIDERS` too; **UPDATE the existing `test_ollama_tag_prefix_matches`**, which currently asserts `x/z-image-turbo` → `suspect_retired`, to expect `not_installed` (M3 side effect).
- `test_local_retired_entry_still_confirmed_retired` — retirement status wins over the local branch.
- `test_mlx_candidate_filter_matches_mflux_suffix` — cached `Foo/Bar-mflux-8bit` uncatalogued → candidate under `mlx`.
- `test_mlx_hf_repo_not_reported_as_candidate` — a catalogued repo (primary or fallback) is excluded.
- `test_report_includes_mlx_probe` — `probe_report` default dict has an `mlx` key.

### 7.4 `plugins/jack-tar-cloud/tests/test_model_catalog.py`

- `test_mlx_entries_present` — three ids resolve, provider `mlx`, `flat 0.0`.
- `test_mlx_entries_have_sdk_entrypoint_and_hf_repo`.
- `test_mlx_entries_have_render_steps` — all three carry `capabilities.render_steps` (the bridge depends on it — §2.4).
- `test_mlx_qwen_has_min_ram_gb_24`.
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
- NEW `test_ci_plugin_matrix.py` — **CI matrix self-guard (review M1)**:
  parse `.github/workflows/validation.yml` (yaml or regex), extract the
  `plugin-tests` job's `matrix.plugin` list, and assert it is a superset of
  `{p.name for p in Path("plugins").iterdir() if (p / "tests").is_dir()}`.
  A new plugin with tests that is missing from the CI matrix fails the
  suite — the gap that would otherwise silently exempt jack-tar-mlx from CI
  can never recur.
- NEW `test_mlx_plugin_contract.py` — cross-plugin drift guard
  complementing §7.1: full per-field equality between the mlx wrapper's
  `MLX_MODEL_REGISTRY` and the CANONICAL catalog's `mlx/*` entries —
  `registry[id] == derived(catalog_entry)` for every duplicated field
  (entrypoint, hf_repo, hf_repo_fallback, default_steps, quantize,
  timeout ← capabilities.timeout_seconds), plus exact key-set equality
  (review M2).

## 8. Version + release plan

CI `json-validation` asserts: every `plugins/*/.claude-plugin/plugin.json`
parses; marketplace lists exactly the plugin dirs on disk (bidirectional);
each plugin.json `version` == its marketplace entry `version`. Additionally
(review M1) the `plugin-tests` job hard-codes its plugin matrix at
`.github/workflows/validation.yml:61-67` — **jack-tar-mlx must be added to
that matrix or its tests never run in CI.** Every file below MUST change
together in the release commit:

| File | Change |
|---|---|
| `plugins/jack-tar-mlx/.claude-plugin/plugin.json` | NEW, `version: 0.1.0` |
| `plugins/jack-tar-deckhand/.claude-plugin/plugin.json` | `1.7.0 → 1.8.0` |
| `plugins/jack-tar-cloud/.claude-plugin/plugin.json` | `1.4.0 → 1.5.0` (minor: probe_mlx_models + not_installed verdict) |
| `.claude-plugin/marketplace.json` | ADD jack-tar-mlx entry (0.1.0); bump deckhand→1.8.0, cloud→1.5.0 |
| `.github/workflows/validation.yml` | ADD `jack-tar-mlx` to the `plugin-tests` matrix (review M1) |
| `model-catalog/model-catalog.json` | `catalog_version 1.0.0 → 1.1.0`, three mlx entries |
| `plugins/jack-tar-cloud/src/model-catalog.json` | cp of canonical |
| `plugins/jack-tar-deckhand/src/model-catalog.json` | cp of canonical |
| `model-catalog/model-catalog.schema.json` | §3.1 schema diff (single copy) |
| `docs/model-catalog.md` | regenerated |
| `src/model_probe.py` + `plugins/jack-tar-cloud/src/model_probe.py` | probe_mlx_models, LOCAL_PROVIDERS/not_installed, byte-identical |
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

**T1 — Schema diff + catalog entries + vendoring + markdown + licence
verification.**
- Files: `model-catalog/model-catalog.schema.json` (§3.1 — incl.
  `render_steps`, open-integer `quantize`), `model-catalog/
  model-catalog.json` (§3.2 + version/updated bump), cp to both vendored
  catalogs (§3.3), regen `docs/model-catalog.md`.
- Also: verify the two unconfirmed repo licences (§3.2 table / §10 OQ-A)
  against the HF model cards and correct the entry notes if they differ.
- Depends-on: none.
- DoD: `python model-catalog/catalog_markdown.py --check` OK; three catalog
  copies byte-identical; `test_model_catalog_integrity.py` green;
  `load_catalog().get("mlx/qwen-image")` resolves; every hf_repo/
  hf_repo_fallback in the entries has a licence stated in notes or the
  install-guide table.

**T2 — `jack-tar-mlx` plugin (wrapper + nested lock + skills + tests) + CI
matrix.**
- Files: whole `plugins/jack-tar-mlx/` tree (§6), `test_generate_image.py`
  (§7.1), **`.github/workflows/validation.yml` — add `jack-tar-mlx` to the
  `plugin-tests` matrix (review M1)**.
- Depends-on: T1 (drift-guard test reads catalog mlx ids/values).
- DoD: `pytest plugins/jack-tar-mlx/tests` green; wrapper runs `--help` and
  `--check-weights`; full-value registry↔catalog drift test passes;
  `--steps` always-present test passes; lock-ordering tests pass;
  validation.yml matrix contains `jack-tar-mlx`.

**T3 — Dispatch seam (detect_mlx_backend, detect_any_local_backend,
helpers, `:647` fix, local_only message).**
- Files: `plugins/jack-tar-deckhand/src/paperbanana_dispatch.py` (§2),
  `test_paperbanana_dispatch.py` (§7.2).
- Depends-on: T1 (reads catalog mlx entries).
- DoD: new tests green (incl. m7 HF_HUB_CACHE, m8 refs/main, m11 both-ways
  RAM-gate, m16 no-file-IO pins); all 69 existing dispatch tests still
  pass; `:647` guard generalized; the m15 behaviour change is documented in
  the commit message AND pinned by
  `test_manifest_entry_legacy_ollama_local_without_provider_takes_fallback_branch`.

**T4 — model_probe MLX discovery + local-provider classification.**
- Files: `src/model_probe.py` + cp to `plugins/jack-tar-cloud/src/
  model_probe.py`, `test_model_probe.py` (§7.3).
- Includes: `LOCAL_PROVIDERS`, the `not_installed` verdict (review M3
  ruling), and the UPDATE to the existing `test_ollama_tag_prefix_matches`
  expectation.
- Depends-on: T1.
- DoD: probe tests green; `probe_report()` default dict has `mlx`; copies
  byte-identical; no local-provider entry can classify `suspect_retired`
  for a merely-not-installed model.

**T5 — Bridge Step 4.6 + deckhand verify skill.**
- Files: `imagegen-bridge/SKILL.md` (§5), `skills/verify/SKILL.md` (MLX line).
- Depends-on: T3 (calls detect_any_local_backend), T2 (MLX_PLUGIN_ROOT).
- DoD: `test_imagegen_bridge_skill.py` still green; SKILL references
  `detect_any_local_backend`, `slide-NN-academic-figure-mlx.png`,
  `local_provider_order`, passes `--steps` from `local_args.steps` and
  `--quantize` from `mlx.quantize` (m9); **a grep for the F10 gate text
  ("operator gate" / "WAIT for explicit operator go-ahead") matches inside
  the mlx render branch** (reviewer-named test gap); `hf_repo_used`
  stashing (m19) is present.

**T6 — Integration tests + marketplace + versions.**
- Files: `.claude-plugin/marketplace.json`, deckhand+cloud plugin.json bumps,
  `test_plugin_verify_contracts.py`, `test_plugin_root_discovery.py`,
  NEW `test_ci_plugin_matrix.py` (M1 self-guard), NEW
  `test_mlx_plugin_contract.py` (M2 full-value drift guard).
- Depends-on: T2 (verify skill exists), T1/T4 (versions).
- DoD: full `json-validation` logic passes locally; integration suite green;
  the CI-matrix self-guard fails when `jack-tar-mlx` is removed from
  validation.yml (verified by temporary mutation during development).

**T7 — Docs (ADR addendum, install guide, root CLAUDE.md, retrospective).**
- Files: `docs/architecture/paperbanana-integration-v2.md` (§8.6 addendum:
  second provider landed, composed probe, provider order, HF-offline guard,
  nested lock), `docs/architecture/mlx-install-guide.md` (uv tool install;
  **per-repo** `hf download` + disk table; **per-repo licensing table**
  (review M6) — every hf_repo AND hf_repo_fallback named in §3.2 with its
  own licence row, incl. the Tongyi Qianwen correction for
  `filipstrand/Z-Image-Turbo-mflux-4bit` and the gated/non-commercial note
  for klein-9B / FLUX.1-dev; **per-family minimum mflux versions** (qwen
  ≥ 0.11, z-image ≥ 0.13, flux2 ≥ 0.15, Runpod klein repo ≥ 0.16 — review
  m12); `mflux-save` quantized-local workflow; torch/env-size note; HF-token
  note for gated models we do NOT default to; the ~40 GB Qwen fallback
  call-out), root `CLAUDE.md` status,
  `retrospectives/124-mlx-local-backend.md`.
- Depends-on: T3/T5 (describe final behaviour).
- DoD: links resolve; install guide lists exact repo ids + disk sizes +
  per-repo licences + per-family mflux minimums.

**T8 — Full-suite gate (pre-PR).**
- Run every plugin suite + integration + json-validation; open PR to `main`
  referencing #124.
- Depends-on: T1–T7.
- DoD: all green (including the new jack-tar-mlx CI matrix job); PR body
  maps success criteria to evidence.

## 10. Open questions (remaining after review — need operator or web verification)

- **OQ-A — licences of the two community pre-quantized repos.**
  `Runpod/FLUX.2-klein-4B-mflux-4bit` and `filipstrand/Qwen-Image-mflux-6bit`
  licences must be read off their HF model cards during T1 (the review
  established that the derivative repo's licence governs — M6 — and that
  the z-image derivative is Tongyi Qianwen, so "derivative of Apache 2.0"
  cannot be assumed to be Apache 2.0). If either is non-permissive, the
  entry keeps the repo as primary for capability but the install guide must
  say so, or the operator may direct a swap to on-load quantization of the
  Apache base.
- **OQ-B — Z-Image-Turbo / Qwen Mac wall-clock.** `timeout_seconds` values
  (180 / 900) are conservative placeholders; Mac timings are unpublished
  (proposal risk 2). Phase 5 measures and may retune; also re-check
  `min_ram_gb: 24` for the qwen 6-bit primary empirically.
- **OQ-C — snapshot-completeness helper duplication.** The helper now lives
  in three Python spots: `paperbanana_dispatch.py` (detection),
  `model_probe.py` (discovery), and the mlx wrapper (`--check-weights`,
  added by review m17 so the verify skill has no bash re-implementation).
  Each copy is behind its own tests; a shared module would need a new
  vendored file + byte-identity guard. Confirm the operator prefers the
  ~20-line × 3 duplication over a fourth vendored artifact (design's
  default: duplicate).

Resolved by review (previously OQ-1/2/4/6/7 — retained here as pointers):
klein fallback repo + mflux ≥ 0.16 → §3.2; qwen 6-bit primary + fallback +
steps → §3.2; metadata sidecar path → §6.3; no `mflux --version` → §6.5;
top-level `academic_figure_local_only` precedence → §5.3 (m10).

## 11. Design review disposition (adversarial review 2026-07-15, verdict APPROVE-WITH-CHANGES)

| # | Finding | Resolution | Where |
|---|---|---|---|
| M1 | CI plugin-tests matrix hard-codes six plugins; jack-tar-mlx would never run in CI | validation.yml added to the move-together table; matrix edit folded into T2 files+DoD; NEW `test_ci_plugin_matrix.py` self-guard (matrix ⊇ plugins with tests dirs) | §8, §9 T2/T6, §7.5 |
| M2 | Keys-only registry↔catalog drift guard leaves hf_repo/fallback/default_steps/quantize/timeout free to diverge | Both drift tests upgraded to full per-field equality `registry[id] == derived(catalog_entry)` + exact key-set equality | §6.3, §7.1, §7.5 |
| M3 | Not-yet-downloaded local models would classify `suspect_retired` (alarm fatigue) | RULING applied: `LOCAL_PROVIDERS = {"ollama","mlx"}`; new `not_installed` verdict with pull-command remediation; ollama on the same path; wrong-behaviour test replaced with `test_mlx_entry_not_installed_when_repo_absent`; existing `test_ollama_tag_prefix_matches` expectation updated | §4.3, §7.3 |
| M4 | Steps contradiction (klein default_steps 4 vs 20-step dogfood evidence; bridge passed no --steps; mflux silently defaults to 25) | RULING applied: (a) `sdk.default_steps` stays family-native (4/9/20); (b) NEW `capabilities.render_steps` (20/9/20); (c) bridge ALWAYS passes `--steps` from render_steps via `local_args["steps"]`; (d) wrapper ALWAYS emits `--steps` in argv + pinning test `test_steps_always_present_in_argv` | §2.4, §3.1, §3.2, §5.2, §6.3, §7.1 |
| M5 | Two independent locks don't prevent Ollama-render-concurrent-with-mflux-load OOM | RULING applied: nested lock — mlx wrapper acquires the ollama lock FIRST, then its own (deadlock-safe: single multi-lock acquirer); shared `--lock-wait-timeout` deadline; `--no-lock` skips both; residual (serialization behind long ollama renders) documented; H2 shared-lock option recorded; lock-ordering + shared-deadline tests added | §6.3, §6.6, §7.1 |
| M6 | Licence facts wrong: `filipstrand/Z-Image-Turbo-mflux-4bit` is Tongyi Qianwen, not Apache 2.0; derivative repo licence governs | Per-repo licence table added to §3.2 (two repos flagged verify-on-model-card → OQ-A); z-image entry notes corrected with an explicit licence warning + pure-Apache fallback route; T7 install-guide licensing table made per-repo (not per-family); T1 DoD requires per-repo licence statement | §3.2, §9 T1/T7, §10 OQ-A |
| m7 | HF cache resolution must honour `HF_HUB_CACHE` first | `_resolve_hf_hub_dir` helper specified with real huggingface_hub precedence (`HF_HUB_CACHE` → `HF_HOME/hub` → `~/.cache/huggingface/hub`); used by detection, probe, and `--check-weights`; precedence + env tests added | §2.1, §4.1, §6.5, §7.2, §7.3 |
| m8 | Snapshot revision resolution + .incomplete scoping | refs/main-resolved revision when present; `.incomplete` check scoped to the resolved revision's blobs; between-files gap documented as accepted residual with the wrapper offline-guard as backstop; refs/main test added | §2.2, §7.2 |
| m9 | Bridge must pass `--quantize` from `mlx.quantize` | Conditional `${MLX_Q:+--quantize "$MLX_Q"}` in the §5.2 snippet; key documented in the config table; T5 DoD | §5.2, §5.3, §9 T5 |
| m10 | Legacy local_only keys sit uniformly BELOW the top-level key | Precedence spelled out (top-level wins when PRESENT; else OR of the two legacy keys) and encoded in the §5.1 snippet; resolves former OQ-7 | §5.1, §5.3 |
| m11 | RAM-gate bypass semantics | RULING applied: explicit `preferred_model` bypasses with logged warning; catalog-order auto-selection gated; pinned both ways (`…_skips_qwen_in_catalog_order`, `…_bypasses_ram_gate_with_warning`) | §2.1, §7.2 |
| m12 | Stage-1 must check the SELECTED entry's entrypoint; record per-family mflux minimums | Detection restructured per-candidate (entry's own `sdk.entrypoint`); per-family minimums (qwen ≥0.11, z-image ≥0.13, flux2 ≥0.15, Runpod klein ≥0.16) in entry notes, verify skill, and install guide; `…_checks_selected_entrys_entrypoint` test | §2.1, §3.2, §6.5, §7.2, §9 T7 |
| m13 | Fallback-repo retry quantization | `sdk.quantize` redefined as "bits applied when the resolved repo is full-precision"; `_repo_prequantized` (`-mflux-` convention); fallback retry emits `-q <bits>` matching the entry's quantize; RAM/disk implications noted for the on-load path; tests added | §3.1, §6.3, §7.1 |
| m14 | Partial-output cleanup | Wrapper unlinks output + sidecar on any non-success exit; `test_timeout_removes_partial_output` + `test_nonzero_exit_removes_partial_output` | §6.3, §7.1 |
| m15 | Legacy empty-local_provider edge behaviour change | Documented as intentional in §2.5 + T3 commit-message requirement + pinning test | §2.5, §7.2, §9 T3 |
| m16 | detect_any_local_backend parameter-only | RULING applied: no file I/O in the seam function; all config reads live in the bridge SKILL step; docstring states it; `…_does_no_file_io` pin test | §2.4, §5.1, §7.2 |
| m17 | Verify skill must not re-implement the snapshot check in bash | Wrapper gains `--check-weights` mode; verify skill shells to it; noted that this adds a third Python copy of the helper (OQ-C updated) | §6.3, §6.5, §7.1, §10 OQ-C |
| m18 | `--quantize` schema enum unverified | Closed enum replaced with open integer range 3–8 + documented values in the description, pending verification of the pinned mflux version's parser | §3.1, §6.3 |
| m19 | Repo fidelity on fallback | Wrapper emits `MFLUX_REPO_USED=<repo>` on stderr; bridge stashes `local_args["hf_repo_used"]` before `build_manifest_entry`; `test_emits_repo_used_on_stderr` | §2.7, §5.2, §6.3, §7.1 |
| OQ-1 | klein fallback repo | Resolved: `black-forest-labs/FLUX.2-klein-4B` (Apache 2.0, ~13 GB) as `hf_repo_fallback`; Runpod primary 4.3 GB, mflux ≥ 0.16 recorded | §3.2 |
| OQ-2 | Qwen repos + steps | RULING applied: primary `filipstrand/Qwen-Image-mflux-6bit`, fallback `Qwen/Qwen-Image` (~40 GB, install-guide call-out); default_steps 20 confirmed; `min_ram_gb` revised 32 → 24 for the 6-bit primary (empirical re-check in Phase 5, OQ-B) | §3.2, §10 OQ-B |
| OQ-4 | Metadata sidecar path | Resolved: `<output stem>.metadata.json` via `with_suffix(".metadata.json")`; EXIF embedding noted; parse-path test added | §6.3, §7.1 |
| OQ-6 | mflux version surface | Resolved: NO plain `mflux` entry point, no `--version`; verify uses `uv tool list` → `pip show` → `importlib.metadata` | §6.5 |
| — | Offline guard soundness | Review confirmed: mflux resolves via `snapshot_download`, honours `HF_HUB_OFFLINE`; `TRANSFORMERS_OFFLINE` unnecessary but retained as belt-and-braces | §6.3 |
| — | Reviewer-named test gaps | All added: `--steps`-always-present (§7.1), HF_HUB_CACHE honoured (§7.2/§7.3), `local_provider_order` no-arg default path (§7.2), F10 gate-text grep in the mlx bridge branch (T5 DoD), registry full-value drift (§7.1/§7.5), `not_installed` classification (§7.3), timeout-cleanup (§7.1) | §7, §9 T5 |
