# Retrospective: Feature #124 — MLX (mflux) backend as a second local provider

**Branch**: `feat/mlx-local-backend`
**Date**: 2026-07-15

## What Went Well

- **The `LocalBackend` seam held.** The 2026-07-10 local-first-Ollama work
  (ADR §8.5) deliberately shaped `LocalBackend` as `provider` + `model`
  rather than Ollama-specific fields, on the stated bet that a second
  provider could slot in later "without touching the ladder logic." That
  bet paid off: adding MLX needed a new detector
  (`detect_mlx_backend`), a composing wrapper
  (`detect_any_local_backend`), a new render branch in the bridge, and
  exactly **one** literal fix (`build_manifest_entry`'s
  `backend_used == "ollama_local"` guard at `paperbanana_dispatch.py:647`)
  — no rework of `build_dispatch_payload`'s backend/local_provider/
  local_model fields, which were already generalized.
- **The adversarial design review earned its keep.** Running a formal
  review pass over the design doc (verdict APPROVE-WITH-CHANGES, §11 of
  the plan) caught six major findings and thirteen minor ones *before any
  code was written*, including three that would have been expensive or
  embarrassing to discover post-merge:
  - **M1** — the CI `plugin-tests` job hard-codes its plugin matrix; a
    new plugin with its own tests would silently never run in CI. Caught
    pre-implementation, fixed with both a matrix edit and a
    self-guarding test (`test_ci_plugin_matrix.py`) so the gap can't
    recur for the *next* new plugin either.
  - **M6** — the design's first draft assumed the derivative
    pre-quantized Z-Image-Turbo and Qwen-Image repos inherited their
    Apache-2.0 base licences. HF model-card verification during T1 found
    both are actually licensed `tongyi-qianwen-license` — a licence
    compliance error that would have shipped in an install guide telling
    operators the wrong thing.
  - **M4** — a real steps contradiction (family-native `default_steps: 4`
    for klein vs. the 2026-07-11 dogfood's empirical 20-step requirement,
    plus mflux's silent 25-step default when `--steps` is omitted) was
    resolved with a dedicated `capabilities.render_steps` catalog field
    *before* the wrapper was written, rather than discovered via a bad
    first render.
- **The full-value drift guard (M2) is cheap insurance that will keep
  paying off.** Requiring `MLX_MODEL_REGISTRY[id] == derived(catalog
  entry)` field-for-field (not just matching keys) means any future
  catalog edit that forgets the vendored wrapper copy fails a fast unit
  test instead of silently drifting.

## What Could Improve

- **Three duplicated copies of the same ~20-line HF-snapshot-completeness
  check** now exist (`paperbanana_dispatch.py` for detection,
  `model_probe.py` for discovery, `generate_image.py` for
  `--check-weights`) — a deliberate call (review m17/OQ-C: the verify
  skill must not re-implement the check in bash), but it's a small
  maintenance tax that will need a fourth touch-point update if the
  completeness algorithm ever changes. A shared module was considered
  and rejected only because it would add a fourth vendored artifact to
  the byte-identity guard surface for a routing concern, not a
  correctness one — worth revisiting if a fourth copy is ever proposed.
- **Two of five `timeout_seconds` / `min_ram_gb` catalog values are
  placeholders, not measurements** (Z-Image-Turbo 180s, Qwen-Image 900s
  and 24 GB) — real Mac wall-clock numbers are deferred to the Phase 5
  evaluation dogfood (OQ-B). Shipping placeholder timeouts is reasonable
  for Horizon 1 but means the first real dogfood run may need a
  same-day catalog patch if a timeout proves too tight.
- **The nested lock has a known throughput cost** (an mflux render can
  queue behind up to 600s of an in-flight Ollama render on a machine with
  RAM headroom to spare) that was accepted rather than solved. This is
  the right call for Horizon 1 (correctness over throughput on a
  single-GPU laptop) but is worth flagging again if Horizon 2 discussions
  start — the shared-lock option is recorded but not built.

## Lessons Learned

1. **A derivative Hugging Face repo does not inherit its base model's
   licence — verify every repo's model card individually, every time.**
   Two of three community pre-quantized exports in this feature turned
   out to be re-licensed under Tongyi Qianwen despite Apache-2.0 bases.
   The design doc's own first draft got this wrong before review caught
   it. The rule going forward: when a catalog entry names both a primary
   and a fallback repo, both licences get stated and verified
   independently — never inferred from one another.
2. **Hardcoded CI matrices (plugin lists, provider lists, anything
   enumerated by hand in a workflow YAML) need a self-guarding test, not
   just a one-time edit.** The `plugin-tests` matrix would have silently
   exempted `jack-tar-mlx` from CI forever if review hadn't caught it;
   the fix that actually prevents recurrence is `test_ci_plugin_matrix.py`
   asserting the matrix is a superset of on-disk plugins-with-tests, not
   just the one-line matrix addition.
3. **A model family's "native" default settings are not the same as
   pipeline-validated settings, and conflating them is a trap the
   upstream tool sets for you.** mflux's own steps default (25, silently,
   when `--steps` is omitted) and each family's distilled default
   (4 / 9 / 20) are both real settings mflux ships with — neither is what
   this pipeline's academic_figure label-fidelity requirement actually
   needs. The fix pattern — a separate `render_steps` field the bridge
   *always* passes explicitly, never relying on the wrapped tool's own
   default — is a general one worth reusing anywhere jack-tar wraps a
   third-party CLI with its own opinionated defaults.

## Changes Made

Nine commits on `feat/mlx-local-backend` (`git log main..HEAD --oneline`):

| Commit | Task | Summary |
|---|---|---|
| `5e27e32` | — | Feature proposal + retrospective scaffold for #124 |
| `4b1cf87` | — | Detailed design doc, first pass (pre-review) |
| `b9c6c76` | — | Design doc rev 2 — adversarial review findings applied (verdict APPROVE-WITH-CHANGES, §11 disposition) |
| `4c5f587` | T1 | Catalog `mlx/*` entries (`flux2-klein-4b`, `z-image-turbo`, `qwen-image`) + schema fields (`min_ram_gb`, `render_steps`, `sdk.entrypoint`/`hf_repo`/`hf_repo_fallback`/`default_steps`/`quantize`) across the three vendored catalog copies; catalog version `1.0.0 → 1.1.0`; per-repo licences verified against HF model cards |
| `b908e96` | T4 | `model_probe.py` MLX discovery (`probe_mlx_models`) + `LOCAL_PROVIDERS` / `not_installed` verdict for local providers, vendored to `jack-tar-cloud` |
| `ef344e8` | T3 | `detect_mlx_backend` + `detect_any_local_backend` composed probe + HF hub-dir resolution + snapshot-completeness helper + RAM gate + the `:647` `build_manifest_entry` literal fix, in `paperbanana_dispatch.py` |
| `67d1677` | T2 | New `plugins/jack-tar-mlx/` plugin v0.1.0 — `generate_image.py` CLI wrapper (mflux dispatch, nested single-flight lock, `--check-weights`), `image` + `verify` skills, test suite |
| `da5732b` | T6 | Marketplace + plugin version bumps (`jack-tar-mlx` 0.1.0 new; `jack-tar-deckhand` 1.7.0 → 1.8.0; `jack-tar-cloud` 1.4.0 → 1.5.0); CI matrix + cross-plugin integration guards |
| `b71f0d5` | T5 | imagegen-bridge Step 4.6 `mlx_local` render branch (same F10/F12 gate semantics as the Ollama branch) + `jack-tar-mlx:verify` wired into the deckhand verify skill |

T7 (this retrospective, the ADR §8.6 addendum, the operator install guide,
and the root `CLAUDE.md` status update) follows in the same working
session, ahead of T8's full-suite gate and PR.

## Metrics

- **Files created**: 13 (`plugins/jack-tar-mlx/` full tree — plugin.json,
  `CLAUDE.md`, `src/generate_image.py`, `skills/image/SKILL.md`,
  `skills/verify/SKILL.md`, `tests/__init__.py`,
  `tests/test_generate_image.py`; plus
  `docs/feature-proposals/124-mlx-local-backend.md`, this retrospective,
  `docs/architecture/mlx-install-guide.md`, and three new integration
  test files: `test_ci_plugin_matrix.py`, `test_mlx_plugin_contract.py`,
  and the design doc itself)
- **Files modified**: ~20 (`model-catalog/model-catalog.json` + both
  vendored copies + schema + generated markdown;
  `src/model_probe.py` + `jack-tar-cloud` copy + its tests;
  `paperbanana_dispatch.py` + its tests;
  `imagegen-bridge/SKILL.md` + deckhand `verify/SKILL.md`;
  `.claude-plugin/marketplace.json`; `jack-tar-deckhand` and
  `jack-tar-cloud` `plugin.json`; `.github/workflows/validation.yml`;
  `test_plugin_verify_contracts.py` + `test_plugin_root_discovery.py`;
  `docs/architecture/paperbanana-integration-v2.md`; root `CLAUDE.md`)
- **Total diff vs `main`**: `git diff main --stat | tail -1` →
  run this at merge time for the exact figure; at T7 completion it read
  32 files changed, 5039 insertions(+), 64 deletions(-).
