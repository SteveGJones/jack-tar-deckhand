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

## Resilience — connection retry decorator (v1.3.2, issue #72)

All cloud API calls are wrapped in a `retry_on_connection_reset` decorator that retries on transient transport failures. As of v1.3.2 the retryable set covers:

- `ConnectionResetError`, `ConnectionError` (stdlib)
- `requests.exceptions.ConnectionError` (requests library)
- `httpx.RemoteProtocolError`, `httpx.ConnectError`, `httpx.ReadError` (httpx layer — raised by google-genai's underlying httpx client)

HTTP status errors (`httpx.HTTPStatusError`, `requests.exceptions.HTTPError`) are **not** retried — those represent deliberate server responses (4xx/5xx) and should propagate immediately. Retry uses a (1, 2, 5) second backoff with three attempts before re-raising.

**Related:** issue [#72](https://github.com/SteveGJones/jack-tar-deckhand/issues/72).

## Recraft V4 default style and fall-through (v1.3.2, issue #73)

The `generate_recraft_direct` function previously defaulted to `style='realistic_image'` — a V3 preset that Recraft V4 rejects with `400 invalid_image_type`. As of v1.3.2:

- The default is now `style=None`. When `None`, the `style` key is omitted from the request body entirely, and Recraft V4 picks a style server-side.
- Explicit V4-compatible styles (e.g. `digital_illustration`, `vector_illustration`) still pass through unchanged.
- If the direct API returns `400 invalid_image_type` AND `FAL_KEY` is configured in the environment, the dispatcher falls through to `generate_recraft_fal()` with the same arguments. This provides a transparent escape hatch for future Recraft API changes. Other 400 errors (content policy, rate limit) propagate immediately without fall-through.

**Related:** issue [#73](https://github.com/SteveGJones/jack-tar-deckhand/issues/73).

## Imagen Fast resolution guard (v1.3.2, issue #74)

Imagen Fast (`imagen-4.0-fast-generate-001`) renders at a fixed native resolution and rejects the `image_size`/`sampleImageSize` parameter with `400 INVALID_ARGUMENT: sampleImageSize is not adjustable`. As of v1.3.2 the Imagen path in `generate_google()` uses a `_IMAGEN_FIXED_RESOLUTION_MODELS` set to determine whether to pass `image_size` in the request body:

- **Imagen Fast** — not in the set; `image_size` is omitted. If the caller requests `resolution='2K'` or higher, a warning is logged and the call proceeds at native 1K.
- **Imagen Standard / Ultra** — in the set; `image_size` is passed as before (supports 1K, 2K).

The resolution table in the "Resolution control" section above reflects this: Imagen Fast is listed with supported tier `1K` only; `n/a` in the native parameter column indicates the kwarg is intentionally absent.

**Related:** issue [#74](https://github.com/SteveGJones/jack-tar-deckhand/issues/74).

## Quick Start

```
/jack-tar-cloud:verify
/jack-tar-cloud:image "a lighthouse at sunset, dramatic clouds"
```
