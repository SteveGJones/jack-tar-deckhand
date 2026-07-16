---
name: image
description: Generate an image locally on Apple Silicon via the mflux CLI (MLX). Flag-compatible with jack-tar-ollama's /image — a $0 local tier, no API keys needed.
argument-hint: "a description of the image" [--model MODEL] [--output PATH] [--width INT] [--height INT] [--steps INT] [--seed INT] [--quantize N] [--lock-wait-timeout SECONDS] [--no-lock]
allowed-tools: Bash(python *), Bash(python3 *)
---

# /image (jack-tar-mlx)

Generate an image via mflux (MLX) and report the file path. This is a **$0 local tier** — no API keys, no per-image cost. Operator installs the runtime and pulls weights themselves; this skill never downloads.

## Prerequisites

- `mflux` installed: `uv tool install --upgrade mflux`
- Weights for at least one catalogued model cached locally (`hf download <repo>` — see `/jack-tar-mlx:verify` for the exact command per model)
- Apple Silicon (mflux is MLX-based; it does not run on Intel Macs or other platforms)

If you are not sure whether prerequisites are met, run `/jack-tar-mlx:verify` first.

## Parse Arguments

Parse `$ARGUMENTS` for:
- **Prompt**: the quoted text description (required)
- **--model MODEL**: catalog model id — one of `mlx/flux2-klein-4b` (default), `mlx/z-image-turbo`, `mlx/qwen-image`
- **--output PATH**: where to save the image (default: `output/YYYYMMDD-HHMMSS.png`)
- **--width INT** / **--height INT**: image dimensions (default: 1024x1024)
- **--steps INT**: inference steps (default: the model's pipeline-validated step count — 20 for flux2-klein-4b, 9 for z-image-turbo, 20 for qwen-image; you do not need to pass this unless overriding)
- **--seed INT**: seed for reproducibility (optional)
- **--quantize N**: on-load quantization bits (3-8). Only relevant when the model falls back to its full-precision repo; ignored for pre-quantized primaries. You do not normally need to set this.
- **--lock-wait-timeout SECONDS**: how long to wait for the local single-flight locks before giving up (default: 600)
- **--no-lock**: skip the locks. Test fixtures / debug only — never in a production pipeline.

If no prompt is provided, stop and tell the user to provide one.

## Locate Plugin

```bash
PLUGIN_ROOT=$(python3 -c "
from pathlib import Path
import sys, os

if os.environ.get('JACK_TAR_MLX_ROOT'):
    print(os.environ['JACK_TAR_MLX_ROOT']); sys.exit()

home = Path.home()
for base in [home / '.claude' / 'plugins' / 'cache']:
    for p in base.rglob('jack-tar-mlx/.claude-plugin/plugin.json'):
        print(str(p.parent.parent)); sys.exit()

dev = Path.cwd() / 'plugins' / 'jack-tar-mlx'
if dev.exists():
    print(str(dev)); sys.exit()

print('NOT_FOUND')
" 2>/dev/null)
if [ -z "$PLUGIN_ROOT" ] || [ "$PLUGIN_ROOT" = "NOT_FOUND" ]; then
  echo "ERROR: jack-tar-mlx plugin not found. Set JACK_TAR_MLX_ROOT or install the plugin."
  exit 1
fi
```

## Generate

```bash
python3 "$PLUGIN_ROOT/src/generate_image.py" \
  --prompt "THE PROMPT" --model "THE MODEL" --output "THE PATH" \
  --width WIDTH --height HEIGHT \
  [--steps STEPS] [--seed SEED] [--quantize N] \
  [--lock-wait-timeout SECONDS] [--no-lock]
```

1. If exit code is 0: read the output path from the last stdout line.
2. If exit code is non-zero: read stderr and report the error verbatim — the wrapper's messages already name the exact remediation command (`uv tool install --upgrade mflux`, `hf download <repo>`, etc). Point the user at `/jack-tar-mlx:verify` for a full readiness report.

## Nested lock note (review M5, issue #124/#75)

This wrapper acquires the **Ollama** single-flight lock first, then its own, before rendering. This prevents an mflux render running concurrently with an Ollama render on a single-GPU/unified-memory machine (the OOM scenario both locks exist to prevent). This means an mflux render can queue behind a long-running Ollama render — accepted for Horizon 1. `--no-lock` skips both locks.

## Report Result

Report:
- The absolute file path to the generated image
- The model used (and which repo — primary or fallback — actually rendered it, if surfaced)
- The prompt used
- That this was a $0 local render (no cost accrued)

Do not ask follow-up questions. Report and stop.
