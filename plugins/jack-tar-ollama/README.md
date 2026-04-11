# jack-tar-ollama

Local AI image generation using Ollama — no API keys, no cloud costs.

## What it does

Generates images, icons, seamless patterns, technical diagrams, and complete PowerPoint
presentations using locally-running Ollama models. All generation happens on your machine,
making it ideal for draft-tier rendering where speed and cost matter more than photorealism.
Works best paired with `jack-tar-deckhand` as the draft tier in the three-stage render funnel.

## Prerequisites

- [Ollama](https://ollama.com) installed and running (`ollama serve`)
- At least one image generation model pulled, e.g.:
  ```
  ollama pull x/z-image-turbo
  ```
- A `local-config.json` at your repo root (see the deckhand plugin's docs) specifying your
  preferred model tags and timeouts

## Installation

Install via Claude Code marketplace:
```
claude plugin install SteveGJones/jack-tar
```

Or install just this plugin:
```
claude plugin install SteveGJones/jack-tar --plugin jack-tar-ollama
```

## Verify

```
/jack-tar-ollama:verify
```

This checks that Ollama is reachable, lists installed models, and confirms at least one
image-capable model is available.

## Skills

| Skill | Description |
|-------|-------------|
| `/jack-tar-ollama:image` | Generate a single image with optional iterative refinement (up to 10 rounds, free) |
| `/jack-tar-ollama:icon` | Generate app icons optimised for small sizes and icon grids |
| `/jack-tar-ollama:pattern` | Generate seamless textures and repeating background patterns |
| `/jack-tar-ollama:diagram` | Generate technical diagrams, flowcharts, and architecture illustrations |
| `/jack-tar-ollama:presentation` | Generate a complete PowerPoint with AI-generated slide images |
| `/jack-tar-ollama:verify` | Check Ollama availability and list installed image models |

## Quick Examples

Generate a dramatic hero image for a title slide:
```
/jack-tar-ollama:image "a lighthouse at sunset, dramatic storm clouds, cinematic wide shot"
```

Generate an app icon in a specific style:
```
/jack-tar-ollama:icon "minimalist shield with a circuit pattern, dark blue on white"
```

Generate a seamless background texture:
```
/jack-tar-ollama:pattern "subtle carbon fibre weave, dark grey, tileable"
```

## Notes

- Ollama image generation quality varies by model. `x/z-image-turbo` is a good default.
- Use `/jack-tar-ollama:image` with iterative refinement to improve results at zero cost
  before spending money on cloud generation.
- Ollama MLX image generation may be blocked on some Apple Silicon configs — check the
  output of `/jack-tar-ollama:verify` if you encounter errors.

## License

MIT
