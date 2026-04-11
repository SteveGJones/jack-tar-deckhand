---
name: ollama-pattern
description: Generate seamless textures and repeating patterns for backgrounds, materials, and design assets.
argument-hint: "pattern description" [--style geometric|organic|textile|abstract] [--output PATH] [--model MODEL] [--count N]
allowed-tools: Bash(python *), Bash(curl *), Bash(ollama *), Read, Glob
---

# /ollama-pattern

Generate a seamless repeating pattern or texture. Patterns need specific prompt engineering to ensure they tile well and have consistent visual rhythm.

Default model is `x/z-image-turbo` (faster, good for textures and photorealistic materials). Default size is 1024x1024 (square for tiling).

Consult the `ollama-image-expert` agent for model-specific prompt strategies.

## Parse Arguments

Parse `$ARGUMENTS` for:
- **Description**: The quoted text describing the pattern
- **--style STYLE**: `geometric`, `organic`, `textile`, `abstract`, or `material` (default: inferred from description)
- **--output PATH**: Output path. Default: `output/pattern-YYYYMMDD-HHMMSS.png`
- **--model MODEL**: Override model (default: `x/z-image-turbo`)
- **--count N**: Generate N variations with different seeds (default: 1)
- **--width INT**: Width (default: 1024)
- **--height INT**: Height (default: 1024)
- **--prompt-file PATH**: Read description from a file

If no description and no `--prompt-file`, stop and ask the user what pattern they need.

## Discover Available Models

Discover available image generation models:

```bash
ollama list
```

Filter the output for models with the `x/` prefix — these are image generation models (e.g., `x/z-image-turbo`, `x/flux2-klein`). Machines with more memory may have more models available.

- If `--model` is specified: verify it appears in the list. If not, tell the user it's not available, show them the available `x/` models, and suggest `ollama pull MODEL`.
- If `--model` is NOT specified: default to `x/z-image-turbo` if available (better for textures/patterns). If not, use any available `x/` model. If NO `x/` models are available, tell the user to pull one: `ollama pull x/z-image-turbo`.

## Build the Pattern Prompt

Take the user's description and wrap it in pattern-optimized prompt structure.

**For geometric:**
> A seamless repeating geometric pattern. [DESCRIPTION]. Clean precise geometric shapes arranged in a regular repeating grid. Perfect symmetry, consistent spacing, sharp edges. The pattern should tile seamlessly in all directions with no visible seam lines. Flat design, bold colors, no gradients, no texture noise. Viewed from directly above as a flat 2D surface.

**For organic:**
> A seamless repeating organic pattern. [DESCRIPTION]. Natural flowing shapes arranged in a repeating layout. Leaves, vines, flowers, or natural forms interlocking smoothly. The pattern should tile seamlessly with no visible seam lines or abrupt edges. Soft natural colors, gentle variations in tone. Viewed from directly above as a flat surface.

**For textile:**
> A seamless fabric textile pattern. [DESCRIPTION]. The pattern shows the texture and weave of fabric with a repeating motif. Realistic fabric texture visible at close inspection. The pattern tiles seamlessly in all directions. Photorealistic material quality, natural fiber texture, consistent lighting across the surface. Shot from directly above, flat lay photography.

**For abstract:**
> A seamless repeating abstract pattern. [DESCRIPTION]. Bold abstract shapes, colors, and forms arranged in a tileable repeating composition. The pattern should flow continuously with no visible seam lines. Modern design aesthetic, vibrant or muted palette as appropriate. Viewed as a flat 2D surface from directly above.

**For material (photorealistic surfaces):**
> A seamless photorealistic material texture. [DESCRIPTION]. High-resolution surface detail showing the natural variation of the material. Even, consistent lighting with no directional shadows. The texture must tile seamlessly in all directions with no visible seams or repeating artifacts. Shot from directly above with diffuse lighting. Photorealistic quality.

**If style is not specified**, infer from the description:
- Words like "marble", "wood", "stone", "metal", "concrete" → material
- Words like "floral", "leaf", "vine", "botanical" → organic
- Words like "hexagon", "chevron", "grid", "stripe" → geometric
- Words like "fabric", "linen", "silk", "plaid", "tartan" → textile
- Otherwise → abstract

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

For each variation (1 to `--count`):

```bash
python3 "$PLUGIN_ROOT/src/generate_image.py" --prompt "BUILT PROMPT" --model "MODEL" --output "PATH" --width WIDTH --height HEIGHT --steps STEPS --seed SEED
```

Steps default: 8 for z-image-turbo, 20 for flux.

When `--count` > 1, generate each with a different random seed. Name files with variation suffix: `pattern-001.png`, `pattern-002.png`, etc.

## Report Result

Report:
- Path(s) to the generated pattern(s)
- The model used
- The style applied
- Number of variations generated

One shot. No follow-up.
