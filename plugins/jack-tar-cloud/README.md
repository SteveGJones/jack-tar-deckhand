# jack-tar-cloud

Cloud AI image generation using OpenAI, Google, FAL.ai, and Recraft APIs.

## What it does

Generates production-quality images and vector icons via cloud AI providers. Includes
per-provider skills for targeted use and smart router skills that automatically pick the
best available provider based on your configured API keys. The smart router implements a
"try cheap first" principle — starting at lower-cost tiers and escalating only when the
image reviewer signals quality is insufficient.

## Prerequisites

At least one API key configured as an environment variable:

| Variable | Provider | Used for |
|----------|----------|----------|
| `OPENAI_API_KEY` | OpenAI | GPT Image generation |
| `GOOGLE_CLOUD_PROJECT` | Google | Gemini / Nanobanana image generation |
| `FAL_KEY` | FAL.ai | FLUX Pro, Klein, Ideogram |
| `OPENAI_API_KEY` | Recraft | SVG vector icons via Recraft V4 |

Run `/jack-tar-cloud:verify` to see which providers are reachable with your current keys.

## Installation

Install via Claude Code marketplace:
```
claude plugin install SteveGJones/jack-tar
```

Or install just this plugin:
```
claude plugin install SteveGJones/jack-tar --plugin jack-tar-cloud
```

## Verify

```
/jack-tar-cloud:verify
```

## Skills

| Skill | Description |
|-------|-------------|
| `/jack-tar-cloud:openai-image` | Generate via OpenAI GPT Image |
| `/jack-tar-cloud:google-image` | Generate via Google Gemini / Nanobanana |
| `/jack-tar-cloud:fal-image` | Generate via FAL.ai FLUX Pro / Klein / Ideogram |
| `/jack-tar-cloud:recraft-icon` | Generate SVG vector icons via Recraft V4 |
| `/jack-tar-cloud:image` | Smart router — picks best available provider automatically |
| `/jack-tar-cloud:icon` | Smart router for icons — tries Recraft SVG first, falls back to raster |
| `/jack-tar-cloud:verify` | Check which providers are configured and reachable |

## Quick Examples

Generate a hero image using the smart router (uses best available provider):
```
/jack-tar-cloud:image "a lighthouse at sunset, dramatic storm clouds, cinematic wide shot"
```

Generate an SVG vector icon (requires Recraft / OpenAI key):
```
/jack-tar-cloud:recraft-icon "minimalist shield with circuit pattern, flat design, dark blue"
```

Generate specifically via FAL.ai FLUX:
```
/jack-tar-cloud:fal-image "abstract geometric background, deep navy and gold, conference stage"
```

## Cost Notes

- Smart router starts at 720p / low-tier pricing and escalates only if the image reviewer
  flags quality issues.
- Recraft V4 SVG: standard $0.08/image, pro $0.30/image.
- See `provider_config.json` at the repo root for per-provider dimension limits and pricing.

## License

MIT
