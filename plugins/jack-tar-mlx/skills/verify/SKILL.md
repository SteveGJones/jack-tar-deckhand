---
name: verify
description: Check mflux (MLX) availability, per-family runtime presence, cached weights, and report readiness status.
allowed-tools: Bash(command -v *), Bash(python *), Bash(python3 *), Bash(uv *), Bash(pip *), Bash(du *)
---

# /verify

Check whether this plugin's prerequisites are met and report readiness.

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
```

## Step 1: Runtime check — per catalogued entry point

```bash
command -v mflux-generate-flux2
command -v mflux-generate-z-image-turbo
command -v mflux-generate-qwen
```

Report per-family presence. A missing entry point on an otherwise-working install usually means the installed mflux predates that family:

| Family | Minimum mflux version |
|---|---|
| qwen (mflux-generate-qwen) | >= 0.11 |
| z-image (mflux-generate-z-image-turbo) | >= 0.13 |
| flux2 (mflux-generate-flux2) | >= 0.15 (the Runpod klein primary repo needs >= 0.16) |

If ALL entry points are absent, report:

```
PLUGIN: jack-tar-mlx
VERSION: 0.1.0

DEPENDENCIES:
  mflux:           NOT_READY (run: uv tool install --upgrade mflux)

STATUS: NOT_AVAILABLE
REASON: mflux is not installed
```

## Step 2: Version

There is no plain `mflux` entry point and no `--version` flag. Resolve the installed version with fallbacks, in order:

```bash
uv tool list 2>/dev/null | grep mflux
```

If empty:

```bash
pip show mflux 2>/dev/null
```

If empty:

```bash
python3 -c "import importlib.metadata as m; print(m.version('mflux'))" 2>/dev/null
```

Surface the resolved version in the report, and flag if it is below any family minimum from Step 1 whose entry point is present.

## Step 3: Weights check

Shell to the wrapper's own Python helper — do NOT re-implement the snapshot-completeness check in bash:

```bash
python3 "$PLUGIN_ROOT/src/generate_image.py" --check-weights
```

This prints, per catalogued model, either `READY (<repo>)` or `NOT_READY (run: hf download <repo>)`, using the same HF-cache snapshot-completeness check the deckhand detection seam uses.

## Step 4: HF cache location + disk usage

Resolve the HF hub cache dir per precedence (`HF_HUB_CACHE` env var directly → `HF_HOME/hub` → `~/.cache/huggingface/hub`) and report its path plus disk usage:

```bash
du -sh "$HF_HUB_DIR" 2>/dev/null
```

## Step 5: Report status

If mflux runtime is present but no model is `READY` from Step 3:

```
PLUGIN: jack-tar-mlx
VERSION: 0.1.0

DEPENDENCIES:
  mflux:           READY (version X.Y.Z)

ENTRY POINTS:
  mflux-generate-flux2:          READY / NOT_READY
  mflux-generate-z-image-turbo:  READY / NOT_READY
  mflux-generate-qwen:           READY / NOT_READY

WEIGHTS:
  mlx/flux2-klein-4b:   NOT_READY (run: hf download Runpod/FLUX.2-klein-4B-mflux-4bit)
  mlx/z-image-turbo:    NOT_READY (run: hf download filipstrand/Z-Image-Turbo-mflux-4bit)
  mlx/qwen-image:       NOT_READY (run: hf download OsaurusAI/Qwen-Image-mflux-4bit)

HF CACHE: <resolved hub dir> (<disk usage>)

STATUS: NOT_AVAILABLE
REASON: mflux is installed but no catalogued model has cached weights
```

If mflux runtime is present AND at least one model is `READY`:

```
PLUGIN: jack-tar-mlx
VERSION: 0.1.0

DEPENDENCIES:
  mflux:           READY (version X.Y.Z)

ENTRY POINTS:
  mflux-generate-flux2:          READY

WEIGHTS:
  mlx/flux2-klein-4b:   READY (Runpod/FLUX.2-klein-4B-mflux-4bit)

HF CACHE: <resolved hub dir> (<disk usage>)

CAPABILITIES:
  image:           READY

STATUS: FULLY_AVAILABLE
REASON: mflux runtime + N cached model(s) available
```

If mflux runtime is entirely absent, use the Step 1 `NOT_AVAILABLE` report and skip Steps 2-4.
