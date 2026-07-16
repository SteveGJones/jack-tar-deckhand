# Feature Proposal: MLX (mflux) backend as a second local provider

**Proposal Number:** 124 ([issue #124](https://github.com/SteveGJones/jack-tar-deckhand/issues/124))
**Status:** In Progress
**Author:** Claude (AI Agent), directed by operator
**Created:** 2026-07-15
**Target Branch:** `feat/mlx-local-backend`
**Full plan:** [issue #124 comment](https://github.com/SteveGJones/jack-tar-deckhand/issues/124#issuecomment-4986531799)

---

## Executive Summary

Add a direct MLX backend (Apple Silicon native, via the
[mflux](https://github.com/filipstrand/mflux) CLI, no server daemon) as a
second local provider behind the `LocalBackend` seam shipped in #120. A
new sibling plugin `jack-tar-mlx` wraps the mflux CLI with the same flag
contract as `jack-tar-ollama`'s `generate_image.py`; `detect_mlx_backend()`
composes with the existing Ollama probe under an operator-configurable
provider order. Everything is operator-installed — the plugin bundles no
runtime and never auto-downloads weights (4–30+ GB per model, some
license-gated).

This is **Horizon 1** of the plan: MLX as *second* provider. Horizon 2
(MLX as *replacement* free tier on Apple Silicon) is a follow-up issue
gated on an evaluation dogfood beating/matching the Klein-9b 8/9 baseline
(F15/F16 protocol).

---

## Motivation

### Problem Statement

The local free tier depends entirely on the Ollama server, which has had
three architecture-level image-gen breakages on Apple Silicon in five
months (x86-only `libmlxc.dylib`, M5 Metal kernel failures, silent empty
responses after v0.23.1), offers exactly two image models with no
quantization control, and requires `ollama serve` plus single-flight lock
contention. mflux natively runs the same commercial-safe models (FLUX.2
Klein 4B, Z-Image-Turbo — both Apache 2.0) plus Qwen-Image, the strongest
open-weights in-image text renderer — directly relevant to
`academic_figure` label fidelity.

### User Stories

- As an operator on a machine without Ollama (or with Ollama down), I
  want academic figures to render at $0 through the same critique loop
  via mflux, so the free tier does not depend on one daemon.
- As an operator, I want to install the runtime and pull weights myself
  with clear guidance, so a deck run never triggers a surprise multi-GB
  download or a license acceptance on my behalf.
- As a developer, I want the MLX wrapper flag-compatible with the Ollama
  wrapper, so a future free-tier provider swap changes call-site paths,
  not contracts.

---

## Proposed Solution

1. **Phase 1 — `plugins/jack-tar-mlx/` v0.1.0**: `src/generate_image.py`
   flag-compatible with the Ollama wrapper (`--prompt --model --output
   --width --height --steps --seed --timeout --lock-wait-timeout
   --no-lock`); dispatches to the right mflux entry point per catalog
   `sdk` metadata; parses `--metadata` JSON sidecars; own
   `fcntl` single-flight lock (`jack-tar-mlx-image.lock`); `image` +
   `verify` skills.
2. **Phase 2 — dispatch seam**: `detect_mlx_backend()` two-stage probe
   (mflux CLI on PATH **and** catalogued weights present in the HF
   cache); `detect_any_local_backend()` honouring `local-config.json →
   local_provider_order` (default `["ollama", "mlx"]`); provider-aware
   `local_only_blocked` message; fix the last `"ollama_local"` literal in
   `build_manifest_entry` (~`paperbanana_dispatch.py:647`).
3. **Phase 3 — catalog + discovery**: ship `mlx/flux2-klein-4b`,
   `mlx/z-image-turbo`, `mlx/qwen-image` entries (`pricing.flat: 0.0`,
   `sdk.api: "mflux_cli"`); `probe_mlx_models()` in `model_probe.py`
   (HF-cache scan — mflux has no server API); `role_defaults.local_draft`
   stays Ollama-first until the Horizon 2 evaluation.
4. **Phase 4 — bridge + docs**: imagegen-bridge Step 4.6 `mlx_local`
   render branch (same `local_args` contract, F10/F12 gate semantics
   unchanged); `mlx.*` namespace in `local-config.json`; ADR §8.5 v3
   addendum; operator install guide with per-model disk table.
5. **Phase 5 — evaluation dogfood ($0, operator-run, post-PR)**: rerun
   the 2026-07-11 model-comparison protocol on mflux Klein 4B (4-/8-bit),
   Z-Image-Turbo, Qwen-Image vs the Ollama Klein 9b control.

### Acceptance Criteria

Given a `local_only` slide on an MLX-only machine (no Ollama)
When the slide is dispatched
Then the academic figure renders at $0 through the same critique loop
with gate semantics unchanged, and the manifest records
`backend: "mlx_local"`, `local_provider: "mlx"`, exact `model_used`.

Given Ollama is down and mflux + weights are present
When `detect_any_local_backend()` runs
Then it returns an MLX `LocalBackend` instead of `local_only_blocked`.

Given the mflux CLI is installed but no model weights are cached
When detection or verify runs
Then the backend is reported NOT available with the exact pull command —
no automatic download is ever triggered.

---

## Success Criteria

- [ ] `jack-tar-mlx` plugin ships with wrapper + lock + verify, tests green
- [ ] `detect_mlx_backend()` + composed probe order, dispatch tests green
      (69 existing tests still pass; new MLX paths covered)
- [ ] Catalog entries + `probe_mlx_models()` + markdown regeneration, CI
      drift check green
- [ ] Bridge Step 4.6 `mlx_local` branch + install guide + ADR addendum
- [ ] All plugin suites + integration tests + json-validation green; PR
      to main referencing #124

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| mflux CLI cold-loads weights per invocation (no warm server) | 3–5-render critique loop pays load time each render | Default to pre-quantized community exports (fast load); record wall-clock in Phase 5; deferred in-process/daemon option documented |
| Klein 9B (our best-scoring baseline) is gated + non-commercial on HF | Operators casually pull a model they can't use commercially | Ladder defaults locked to the Apache-2.0 trio; install guide carries an explicit licensing table |
| Qwen-Image needs ~32 GB RAM at Q4 | Detection offers a model the machine can't run | `capabilities.min_ram_gb` in catalog; detection skips models above machine RAM |
| Z-Image-Turbo Mac timings unpublished | Timeout defaults wrong | Conservative catalog `timeout_seconds`; Phase 5 measures |
| Weights scan of HF cache misreads partial downloads | False-positive availability | Probe checks for complete snapshots (HF `snapshots/` layout), degrade-to-None on any doubt |

---

## Changes Made

| Action | File |
|--------|------|
| Create | `plugins/jack-tar-mlx/` (plugin.json, src/generate_image.py, skills/image, skills/verify, tests/) |
| Modify | `plugins/jack-tar-deckhand/src/paperbanana_dispatch.py` (detect_mlx_backend, detect_any_local_backend, :647 literal fix) |
| Modify | `plugins/jack-tar-deckhand/tests/test_paperbanana_dispatch.py` |
| Modify | `model-catalog/model-catalog.json` + both vendored copies (mlx/* entries) |
| Modify | `plugins/jack-tar-cloud/src/model_probe.py` (probe_mlx_models) + tests |
| Modify | `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md` (Step 4.6 mlx_local branch) |
| Modify | `docs/architecture/paperbanana-integration-v2.md` (§8.5 v3 addendum) |
| Create | `docs/architecture/mlx-install-guide.md` |
| Modify | `.claude-plugin/marketplace.json`, `CLAUDE.md` |
| Create | `docs/feature-proposals/124-mlx-local-backend.md` (this file) |
| Create | `retrospectives/124-mlx-local-backend.md` |
