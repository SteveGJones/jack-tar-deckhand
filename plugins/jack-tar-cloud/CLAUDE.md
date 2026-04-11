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

## Quick Start

```
/jack-tar-cloud:verify
/jack-tar-cloud:image "a lighthouse at sunset, dramatic clouds"
```
