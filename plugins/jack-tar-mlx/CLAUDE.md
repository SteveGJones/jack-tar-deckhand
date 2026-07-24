# jack-tar-mlx

Local AI image generation on Apple Silicon via the [mflux](https://github.com/filipstrand/mflux) CLI (MLX). A second local provider alongside `jack-tar-ollama` — server-less, operator-installed, $0 per image.

## Prerequisites

- Apple Silicon Mac (MLX is Apple-Silicon-only)
- `mflux` installed: `uv tool install --upgrade mflux`
- Weights for at least one catalogued model, pulled by the operator (this plugin never auto-downloads):
  - `mlx/flux2-klein-4b` — `hf download Runpod/FLUX.2-klein-4B-mflux-4bit` (or the Apache-2.0 fallback `black-forest-labs/FLUX.2-klein-4B`)
  - `mlx/z-image-turbo` — `hf download filipstrand/Z-Image-Turbo-mflux-4bit` (Tongyi Qianwen licence — the Tongyi caveat applies to this model only; operators needing pure Apache 2.0 should pull `Tongyi-MAI/Z-Image-Turbo` instead)
  - `mlx/qwen-image` — `hf download OsaurusAI/Qwen-Image-mflux-4bit` (apache-2.0, verified 2026-07-15; quantized with mflux 0.18 — the previous primary `filipstrand/Qwen-Image-mflux-6bit` is BROKEN on mflux >= 0.13, upstream mflux issue #296, do not use it. Apache-2.0 fallback `Qwen/Qwen-Image` is a much larger ~58 GB download)

Run `/jack-tar-mlx:verify` for the exact per-model readiness state and pull commands.

## Skills

| Skill | Purpose |
|-------|---------|
| `/image` | Generate an image via mflux, flag-compatible with jack-tar-ollama's `/image` |
| `/image-edit` | Apply a targeted $0 local edit to an existing image (base image + instruction) — preserves everything the instruction does not name, instead of regenerating from scratch (issue #143) |
| `/verify` | Check mflux runtime, per-family entry points, cached weights, and report readiness (generate AND edit) |

**Edit-capable models (issue #143):** `mlx/flux2-klein-4b` (16 GB, same
default as generate) and `mlx/qwen-image` (64 GB — a materially heavier
`edit_min_ram_gb` tier than qwen's 32 GB generate floor, per upstream
mflux #420; never auto-selected below 64 GB). `mlx/z-image-turbo` has no
edit CLI at all — mflux ships no z-image edit entry point, so it cannot
be used with `/image-edit`. An edit reuses the SAME cached weights as
generate for a given model id — there is no separate edit weight
download. See `/image-edit`'s SKILL.md for the two documented failure
modes (text-correction re-garbling; reference-content leakage) before
using it.

## Never auto-downloads — the HF_HUB_OFFLINE guard

This plugin never downloads model weights. Detection and `--check-weights` only check whether a complete Hugging Face cache snapshot already exists (a soft guard). Every render subprocess additionally runs with `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` (the hard guard) — a cache miss fails fast with the exact `hf download <repo>` remediation instead of silently pulling multi-GB weights.

## Nested single-flight lock (issue #75 parity + review M5)

mflux and Ollama can both drive the same GPU/unified-memory context. Running an mflux render concurrently with an Ollama render is the machine's real OOM scenario, so `generate_image.py` acquires **both** locks, in a fixed order, before rendering:

1. `/tmp/jack-tar-ollama-image.lock` (the Ollama plugin's lock) — acquired FIRST
2. `/tmp/jack-tar-mlx-image.lock` (this plugin's own lock) — acquired second

This ordering is deadlock-safe: the Ollama wrapper only ever takes its own lock, so there is exactly one multi-lock acquirer and one global acquisition order. `--lock-wait-timeout` is a single deadline shared across both acquisitions; `--no-lock` skips both. A long-running Ollama render (up to the flux2-klein 600s budget) can make an mflux render queue behind it even on a machine with RAM headroom — accepted for Horizon 1; a Horizon-2 follow-up may replace both files with one shared lock.

## Quick Start

```
/jack-tar-mlx:verify
/jack-tar-mlx:image "a lighthouse at sunset, dramatic clouds"
/jack-tar-mlx:image-edit "darken the sky, keep the lighthouse" --image-paths lighthouse.png
```
