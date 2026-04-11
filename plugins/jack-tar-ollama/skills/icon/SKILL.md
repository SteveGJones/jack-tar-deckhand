---
name: ollama-icon
description: Generate application icons, favicons, and document markers. Produces clean, recognizable icons optimized for small sizes with optional multi-size output.
argument-hint: "icon description" [--sizes 64,128,256,512] [--style flat|3d|outlined] [--output PATH] [--model MODEL]
allowed-tools: Bash(python *), Bash(curl *), Bash(ollama *), Read, Glob
---

# /ollama-icon

Generate a clean, recognizable icon. Icons need special prompt engineering — they must be simple enough to read at small sizes, use flat geometric shapes, and avoid fine detail that disappears when scaled down.

Default model is `x/flux2-klein` (better for clean geometric shapes and text rendering). Default size is 512x512.

Consult the `ollama-image-expert` agent for model-specific prompt strategies.

## Parse Arguments

Parse `$ARGUMENTS` for:
- **Description**: The quoted text describing the icon
- **--sizes SIZES**: Comma-separated pixel sizes to generate (e.g., `64,128,256,512`). Default: just `512`
- **--style STYLE**: `flat` (default), `3d`, or `outlined`
- **--output PATH**: Output path or directory. Default: `output/icon-YYYYMMDD-HHMMSS.png`
- **--model MODEL**: Override model (default: `x/flux2-klein`)
- **--prompt-file PATH**: Read description from a file

If no description and no `--prompt-file`, stop and ask the user what icon they need.

## Discover Available Models

Discover available image generation models:

```bash
ollama list
```

Filter the output for models with the `x/` prefix — these are image generation models (e.g., `x/z-image-turbo`, `x/flux2-klein`). Machines with more memory may have more models available.

- If `--model` is specified: verify it appears in the list. If not, tell the user it's not available, show them the available `x/` models, and suggest `ollama pull MODEL`.
- If `--model` is NOT specified: default to `x/flux2-klein` if available (better for icons). If not, use any available `x/` model. If NO `x/` models are available, tell the user to pull one: `ollama pull x/flux2-klein`.

## Build the Icon Prompt

Take the user's description and wrap it in icon-optimized prompt structure:

**For flat style (default):**
> A minimalist [DESCRIPTION] icon. Clean flat design with simple geometric shapes, bold colors, no gradients, no shadows, no background detail. The icon must be instantly recognizable at small sizes. Centered composition with generous padding. Vector illustration style on a plain light grey background. Suitable for use as an application icon or favicon.

**For 3d style:**
> A [DESCRIPTION] icon with subtle 3D depth. Soft gradients, gentle shadows, rounded surfaces. Modern app icon aesthetic similar to macOS or iOS icons. Centered on a clean background. Simple enough to be recognizable at small sizes.

**For outlined style:**
> A [DESCRIPTION] icon in outline style. Clean single-weight line art, no fill colors, minimal detail. Monochrome dark lines on a light background. Suitable for use in technical documentation or UI toolbars. Must be legible at 16x16 pixels.

## Locate Plugin

Before running any Python scripts, discover the plugin root:

```bash
PLUGIN_ROOT=$(python3 -c "
from pathlib import Path
import sys, os

if os.environ.get('JACK_TAR_OLLAMA_ROOT'):
    print(os.environ['JACK_TAR_OLLAMA_ROOT']); sys.exit()

home = Path.home()
for base in [home / '.claude' / 'plugins' / 'cache']:
    for p in base.rglob('jack-tar-ollama/.claude-plugin/plugin.json'):
        print(str(p.parent.parent)); sys.exit()

dev = Path.cwd() / 'plugins' / 'jack-tar-ollama'
if dev.exists():
    print(str(dev)); sys.exit()

print('NOT_FOUND')
" 2>/dev/null)
if [ -z "$PLUGIN_ROOT" ] || [ "$PLUGIN_ROOT" = "NOT_FOUND" ]; then
  echo "ERROR: jack-tar-ollama plugin not found. Set JACK_TAR_OLLAMA_ROOT or install the plugin."
  exit 1
fi
```

## Generate

For each requested size, run the helper script:

```bash
python3 "$PLUGIN_ROOT/src/generate_image.py" --prompt "BUILT PROMPT" --model "MODEL" --output "PATH" --width SIZE --height SIZE --steps STEPS
```

Steps default: 20 for flux models, 8 for z-image-turbo.

If multiple sizes are requested (`--sizes 64,128,256,512`), generate at the largest size first, then use that as the base. Name files with the size suffix: `icon-512.png`, `icon-256.png`, `icon-128.png`, `icon-64.png`.

Note: Since Ollama doesn't support image resizing, each size is generated independently. For best results at small sizes, the prompt automatically emphasizes simplicity.

For sizes 128 and below, append to the prompt: "Extremely simple, maximum 2-3 shapes, thick bold lines, no fine detail."

## Report Result

Report:
- Path(s) to the generated icon(s)
- The model used
- The sizes generated

One shot. No follow-up.
