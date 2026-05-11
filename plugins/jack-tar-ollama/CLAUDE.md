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

## Single-flight protection (issue #75)

Ollama's image-generation backends (`x/z-image-turbo`, `x/flux2-klein`) are GPU-resident and serialise requests on a single GPU context. Parallel callers do not run in parallel — they queue inside Ollama. With the per-call 120 s skill timeout, queued calls time out while waiting behind the first caller.

As of v1.1.1, `generate_image.py` wraps every API call in an `fcntl.flock` at `/tmp/jack-tar-ollama-image.lock` (exact path: `Path(tempfile.gettempdir()) / "jack-tar-ollama-image.lock"`). Multiple concurrent invocations of the skill now serialise politely; each call gets its full GPU-time budget once the lock is acquired. The lock is released automatically by the kernel on process exit (success, exception, or SIGTERM), so a crashed holder does not block subsequent callers indefinitely.

**New CLI flags (v1.1.1):**

- `--lock-wait-timeout SECONDS` — how long a waiting caller will queue before giving up with a `TimeoutError`. Default `600` (10 minutes — covers roughly five sequential 120 s renders). Increase this for flux models with long queue depths.
- `--no-lock` — skip the lock entirely. Use this in test fixtures or operator-driven debug scenarios where you control parallelism yourself and do not want the overhead of lock file I/O.

**When to use `--no-lock`:**
- Running isolated unit tests that mock the Ollama API (no real GPU involved).
- Debugging a single invocation in a terminal where you have confirmed no other image generation is in flight.
- Never use `--no-lock` in a production pipeline where multiple skills might invoke Ollama concurrently — the timeout failures that motivated issue #75 will return.

**Related:** issue [#75](https://github.com/SteveGJones/jack-tar-deckhand/issues/75), retrospective at `docs/superpowers/dogfooding/2026-05-07-blog-post-asset-run.md` (failure #5).

## Quick Start

```
/jack-tar-ollama:verify
/jack-tar-ollama:image "a lighthouse at sunset, dramatic clouds"
```
