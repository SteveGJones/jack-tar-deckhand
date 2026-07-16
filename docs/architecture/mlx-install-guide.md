# MLX (mflux) operator install guide

`jack-tar-mlx` (issue #124) is a second local, $0 image-generation
provider alongside `jack-tar-ollama` — Apple Silicon only, no server
daemon, driven by the [mflux](https://github.com/filipstrand/mflux) CLI.
Like paperbanana, mflux is an **external CLI tool the operator installs
themselves** — the plugin bundles no runtime and never auto-downloads
model weights. This guide covers runtime install, weight pre-pulling,
per-repo licensing, and verification.

See [`docs/superpowers/plans/2026-07-15-mlx-local-backend.md`](../superpowers/plans/2026-07-15-mlx-local-backend.md)
for the full design and [ADR §8.6](paperbanana-integration-v2.md#86-addendum--mlx-mflux-as-a-second-local-provider-2026-07-15)
for how MLX composes with the existing Ollama local tier.

## 1. Install the mflux runtime

```
uv tool install --upgrade --with hf_transfer mflux
```

`--with hf_transfer` pulls in the accelerated Rust-based Hugging Face
downloader (`hf_transfer`) as an extra so any weight pull you run below
goes faster — it is not required for correctness.

You also need the `hf` CLI to pre-pull weights (see §2):

```
uv tool install "huggingface_hub[cli]"
```

**Note on install size:** mflux depends on PyTorch/MLX and pulls a
non-trivial toolchain (~2-4 GB of Python packages, separate from the
model weights below). `uv tool install` isolates this into its own
managed environment — it will not pollute jack-tar's own `.venv` or any
project virtualenv.

There is **no plain `mflux` entry point and no `--version` flag** — mflux
installs a family of `mflux-generate-*` entry points instead (see §4).
`/jack-tar-mlx:verify` resolves the installed version via `uv tool list`,
falling back to `pip show mflux`, falling back to
`python3 -c "import importlib.metadata as m; print(m.version('mflux'))"`.

## 2. Pull weights for at least one model

The plugin **never downloads weights on your behalf** — every render
subprocess runs with `HF_HUB_OFFLINE=1` / `TRANSFORMERS_OFFLINE=1`, so a
cache miss fails fast with the exact `hf download` command instead of
silently pulling multi-GB weights mid-deck-build. Pull at least one
model's primary repo before your first render:

```
hf download Runpod/FLUX.2-klein-4B-mflux-4bit          # mlx/flux2-klein-4b (default draft model)
hf download filipstrand/Z-Image-Turbo-mflux-4bit       # mlx/z-image-turbo
hf download filipstrand/Qwen-Image-mflux-6bit          # mlx/qwen-image
```

You do not need all three — `flux2-klein-4b` is the plugin's default
draft model and the fastest cold-load. Pull the others only if you want
Qwen-Image's stronger in-image text rendering or want to compare
Z-Image-Turbo.

### Disk size + minimum mflux version per model

| Catalog id | Primary repo | Size | Fallback repo | Fallback size | Min mflux version |
|---|---|---|---|---|---|
| `mlx/flux2-klein-4b` | `Runpod/FLUX.2-klein-4B-mflux-4bit` | 4.3 GB | `black-forest-labs/FLUX.2-klein-4B` | ~13 GB (full precision, quantized 4-bit on load) | >= 0.15 (Runpod primary repo needs >= 0.16) |
| `mlx/z-image-turbo` | `filipstrand/Z-Image-Turbo-mflux-4bit` | small (4-bit) | `Tongyi-MAI/Z-Image-Turbo` | full precision, quantized 4-bit on load | >= 0.13 |
| `mlx/qwen-image` | `filipstrand/Qwen-Image-mflux-6bit` | ~15-16 GB | `Qwen/Qwen-Image` | **~40 GB** full precision, quantized 6-bit on load | >= 0.11 |

**The Qwen fallback is a ~40 GB download.** Only pull
`Qwen/Qwen-Image` directly if you specifically need pure Apache 2.0
licensing (see §3) or the primary repo is unavailable — the on-load
quantization path also needs materially more RAM/disk headroom during
load than the pre-quantized primary.

## 3. Per-repo licensing — read this before pulling

**The derivative (pre-quantized) repo's licence governs the download,
not the base model's licence.** This project verified each repo's HF
model card during implementation (issue #124 review M6) and found two
of the three "-mflux-" community exports are **not** Apache 2.0 despite
their Apache-2.0 base models — do not assume a derivative inherits the
base's licence.

| Repo | Role | Licence | Notes |
|---|---|---|---|
| `Runpod/FLUX.2-klein-4B-mflux-4bit` | primary (klein) | **Apache 2.0** (confirmed via HF model card metadata) | Same terms as the base model — no relicensing. |
| `black-forest-labs/FLUX.2-klein-4B` | fallback (klein) | **Apache 2.0** (confirmed) | ~13 GB. |
| `filipstrand/Z-Image-Turbo-mflux-4bit` | primary (z-image) | **Tongyi Qianwen licence** (`license:other` tag) — **NOT Apache 2.0** (confirmed) | Pull the fallback below if you need pure Apache 2.0. |
| `Tongyi-MAI/Z-Image-Turbo` | fallback (z-image) | **Apache 2.0** (confirmed) | Full precision; quantized 4-bit on load. |
| `filipstrand/Qwen-Image-mflux-6bit` | primary (qwen) | **Tongyi Qianwen licence** (`license:other` tag) — **NOT Apache 2.0** (confirmed) | Same derivative-relicensing pattern as Z-Image-Turbo. |
| `Qwen/Qwen-Image` | fallback (qwen) | **Apache 2.0** (confirmed) | ~40 GB; quantized 6-bit on load. |

If your use requires pure Apache-2.0 provenance end-to-end, pull the
**fallback** repo directly (`hf download <fallback repo>`) instead of
the pre-quantized primary — the wrapper will use whichever repo has a
complete cached snapshot, trying the primary first, falling back to the
secondary automatically.

**Never defaulted, warn-only:** Klein-9B and the entire FLUX.1-dev
family are **gated and non-commercial** on Hugging Face. Nothing in the
`jack-tar-mlx` catalog or wrapper points at them by default — if you
choose to pull one yourself for evaluation, you accept the licence terms
directly with Hugging Face and are responsible for compliance; the
plugin will not stop you (`--model` accepts any registered catalog id;
adding a gated model to the catalog is out of scope for this repo).

## 4. RAM guidance

| Catalog id | `min_ram_gb` | Notes |
|---|---|---|
| `mlx/flux2-klein-4b` | 16 | |
| `mlx/z-image-turbo` | 16 | |
| `mlx/qwen-image` | 24 | Sized for the 6-bit primary; the full-precision fallback needs materially more RAM/disk during on-load quantization. |

Detection (`detect_mlx_backend`) skips a catalog-order candidate whose
`min_ram_gb` exceeds the machine's physical RAM (read via `sysctl
hw.memsize` on macOS). An explicit `preferred_model` (via
`local-config.json` → `mlx.academic_figure_model`) bypasses the RAM gate
with a logged warning — naming a model yourself means you own the
consequence if it doesn't fit.

## 5. `mflux-save` — quantized-local workflow

If you'd rather quantize a full-precision repo once and keep a local
copy instead of relying on mflux's on-load `-q` quantization every
render, use `mflux-save` (ships with the mflux install):

```
mflux-save --model black-forest-labs/FLUX.2-klein-4B -q 4 --path ~/mlx-models/klein-4b-q4
```

Point `local-config.json` → `mlx.models` at the resulting directory (an
array of `mflux-save` output paths) — `detect_mlx_backend` treats a
non-empty registered directory as satisfying the weights-present check
the same way a complete HF-cache snapshot does.

## 6. Hugging Face token

**Not needed for anything this plugin defaults to.** All three
catalogued models (primary and fallback repos) are publicly downloadable
without authentication. You only need `hf auth login` / an `HF_TOKEN` if
you choose to pull a **gated** model yourself (e.g. Klein-9B or a
FLUX.1-dev variant, §3) — those are explicitly outside the catalog's
defaults.

## 7. `local-config.json` keys

All keys are optional; the plugin behaves correctly with none of them
set (Ollama-first provider order, catalog-default models and
quantization).

| Key | Type | Meaning | Precedence |
|---|---|---|---|
| `local_provider_order` | array of `"ollama"` \| `"mlx"` | Detection order for `detect_any_local_backend`. | explicit function arg > this key > built-in default `["ollama", "mlx"]` |
| `mlx.academic_figure_model` | string (catalog id) | Preferred MLX model; bypasses the RAM gate (warning logged). | per-slide strategy annotation > this key > catalog order |
| `mlx.models` | array of paths | Extra `mflux-save` local weight directories to treat as available (§5). | additive to the HF-cache scan |
| `mlx.quantize` | integer 3-8 | Override the on-load `-q` quantization bits (only applied when the resolved repo is full-precision — never emitted for a pre-quantized `-mflux-` repo). | passed through as `--quantize` to the wrapper |
| `academic_figure_local_only` | bool | Provider-agnostic switch forbidding ALL paid tiers for academic_figure slides on this machine. | per-slide `local_only` > this top-level key (when present) > either legacy `ollama.academic_figure_local_only` / `mlx.academic_figure_local_only` |

Example:

```json
{
  "ollama": { "academic_figure_model": "x/flux2-klein:9b" },
  "mlx": {
    "academic_figure_model": "mlx/qwen-image",
    "quantize": 4,
    "models": ["/Users/you/mlx-models/klein-4b-q4"]
  },
  "local_provider_order": ["mlx", "ollama"]
}
```

`local-config.json` is gitignored — it is machine-specific and never
committed.

## 8. Verify

```
/jack-tar-mlx:verify
```

Reports, in order: per-family entry-point presence
(`mflux-generate-flux2` / `-z-image-turbo` / `-qwen`) with the
per-family minimum-version table from §1/§2 above; the resolved mflux
version; per-model weight readiness via the wrapper's own
`--check-weights` mode (not a bash re-implementation of the snapshot
check):

```
python3 <jack-tar-mlx plugin root>/src/generate_image.py --check-weights
```

which prints one `READY (<repo>)` or `NOT_READY (run: hf download
<repo>)` line per catalogued model; the resolved HF cache directory (per
the `HF_HUB_CACHE` → `HF_HOME/hub` → `~/.cache/huggingface/hub`
precedence) plus its disk usage; and an overall `STATUS`:
`FULLY_AVAILABLE` when the runtime is present and at least one model is
`READY`, `NOT_AVAILABLE` otherwise (with the exact remediation command).

`/jack-tar-deckhand:verify` also reports MLX readiness alongside Ollama
— draft images are READY for the academic_figure free tier when
**either** provider is available.

## 9. Quick start end-to-end

```
uv tool install --upgrade --with hf_transfer mflux
uv tool install "huggingface_hub[cli]"
hf download Runpod/FLUX.2-klein-4B-mflux-4bit
/jack-tar-mlx:verify
/jack-tar-mlx:image "a lighthouse at sunset, dramatic clouds"
```
