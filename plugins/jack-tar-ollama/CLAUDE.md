# jack-tar-ollama

Local AI image generation using Ollama. Generate images, icons, patterns, diagrams, and quick presentations — all locally, no API keys needed.

## Prerequisites

- Ollama installed and running (`ollama serve`)
- At least one image generation model pulled (e.g., `ollama pull x/z-image-turbo`)

## Skills

| Skill | Purpose |
|-------|---------|
| `/image` | Generate images with optional iterative refinement |
| `/icon` | Generate app icons optimised for small sizes |
| `/pattern` | Generate seamless textures and repeating patterns |
| `/diagram` | Generate technical diagrams and flowcharts |
| `/presentation` | Generate a complete PowerPoint with AI images |
| `/verify` | Check Ollama availability and list installed models |

## Quick Start

```
/jack-tar-ollama:verify
/jack-tar-ollama:image "a lighthouse at sunset, dramatic clouds"
```
