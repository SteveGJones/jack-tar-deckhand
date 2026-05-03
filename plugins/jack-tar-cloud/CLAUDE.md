# jack-tar-cloud

Cloud AI image generation using OpenAI, Google, FAL.ai, and Recraft APIs. Per-provider skills for targeted use, plus smart router skills that pick the best available provider.

## Prerequisites

At least one API key configured:
- `OPENAI_API_KEY` — for OpenAI GPT Image and Recraft V4 icons
- `GOOGLE_CLOUD_PROJECT` — for Google Gemini/Imagen
- `FAL_KEY` — for FAL.ai FLUX Pro/Klein/Ideogram

## Skills

| Skill | Purpose |
|-------|---------|
| `/openai-image` | Generate via OpenAI GPT Image |
| `/google-image` | Generate via Google Gemini/Imagen |
| `/fal-image` | Generate via FAL.ai FLUX |
| `/recraft-icon` | Generate SVG vector icons via Recraft V4 |
| `/image` | Smart router — picks best available provider |
| `/icon` | Smart router for icons — tries Recraft first |
| `/verify` | Check which providers are configured and reachable |

## Resolution control (v1.2.0)

`generate_cloud_image()` accepts a unified `resolution=` keyword argument routing each provider to its native resolution field:

| Provider / Model | Supported tiers | Native parameter |
|---|---|---|
| OpenAI `gpt-image-1.5` | `1K` | `size` (3 fixed strings) |
| Google Imagen Fast | `1K` | n/a |
| Google Imagen Standard / Ultra | `1K`, `2K` | `image_size` on `GenerateImagesConfig` |
| Google Nano Banana Pro | `1K`, `2K`, `4K` | `image_config.image_size` on `GenerateContentConfig` |
| Google Nano Banana Flash | `512`, `1K`, `2K`, `4K` | same |
| FAL FLUX 2 Pro | `1K`, `2K` | `image_size` (preset OR `{width, height}` dict) |
| FAL FLUX 2 Klein | `1K` | preset |
| FAL Ideogram v3 | `1K` | preset |

Default `resolution="1K"` preserves prior behaviour. Unsupported combinations raise `ProviderResolutionUnsupportedError(provider, model, requested, supported)` — the exception carries the closest supported tier list so callers can retry intelligently.

Imagen pricing has two backends: `GOOGLE_APPLICATION_CREDENTIALS` set → Vertex AI flat per-image; `GOOGLE_API_KEY` only → Gemini Developer API token-based (2K is dearer). `estimate_google_cost(model, resolution)` detects the active backend and returns the right rate.

Per-model resolution capability is also surfaced via `discover_providers()`:

```python
from src.provider_discovery import discover_providers
providers = discover_providers()
providers["google"]["models"]["gemini-3-pro-image-preview"]["supported_resolutions"]
# ['1K', '2K', '4K']
```

SKILL.md `--resolution` flag wiring + render-funnel integration land in [Issue #60](https://github.com/SteveGJones/jack-tar-deckhand/issues/60); Recraft V4 raster as a first-class provider lands in [#61](https://github.com/SteveGJones/jack-tar-deckhand/issues/61). Until those merge, callers using `generate_cloud_image()` directly get the resolution kwarg; the per-provider SKILL.md flag surface stays unchanged from v1.1.x.

## Quick Start

```
/jack-tar-cloud:verify
/jack-tar-cloud:image "a lighthouse at sunset, dramatic clouds"
```
