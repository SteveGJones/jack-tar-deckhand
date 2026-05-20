# jack-tar-deckhand

Full presentation engineering pipeline. Create conference-quality PowerPoint decks through an orchestrated multi-step process: brand profiling, style derivation, narrative architecture, image generation, SmartArt graphics, assembly, and quality assurance.

## Prerequisites

- Python 3.10+ with jsonschema, Pillow, python-pptx
- Node.js with pptxgenjs

## Optional Engine Plugins (install for enhanced capability)

- `jack-tar-ollama` — local image generation (draft tier, free)
- `jack-tar-cloud` — cloud image generation (production tier)
- `jack-tar-msft-smartart` — editable PowerPoint SmartArt
- `jack-tar-custom-smartart` — SVG/Mermaid/Vega data visualisation

Without engine plugins, the pipeline produces text-only slides with placeholder images.

## Skills

| Skill | Purpose |
|-------|---------|
| `/brand-manager` | Extract/load brand profiles |
| `/slide-stylist` | Derive palette, typography, layout rules |
| `/narrative-architect` | Build narrative arc and slide outline |
| `/strategy-map` | Classify per-slide rendering strategy |
| `/smartart-selector` | Select SmartArt graphic types |
| `/smartart-extractor` | Transform content for SmartArt engines |
| `/speaker-notes-writer` | Generate timed speaker notes |
| `/imagegen-bridge` | Route image generation to available plugins |
| `/deck-assembler` | Assemble .pptx — routes to PptxGenJS (standard) or python-pptx (template mode) |
| `/deck-qa` | Run 30 anti-pattern checks |
| `/iterate-slide` | Single-slide critique-driven refinement via paperbanana `--continue-run` (three modes: auto / enumerate / draft) |
| `/verify` | Check pipeline readiness and engine plugin availability |

## Quick Start

```
/jack-tar-deckhand:verify
```

Then use the deck-conductor agent to orchestrate a full deck build.

## Discipline hook (issue #76)

This plugin auto-installs a `PreToolUse` hook that **blocks `Read` on image files** (PNG, JPG, JPEG, GIF, WEBP, BMP, TIF, TIFF — case-insensitive). The hook is declared in `.claude-plugin/plugin.json` and is registered automatically when the plugin is enabled; no separate setup skill or manual `settings.json` edit is needed.

**Why it exists:** During the 2026-05-07 blog-post asset run, 9 generated PNGs were `Read` directly into the orchestration context before the user caught it. Each PNG carries thousands of tokens that compound across every subsequent turn — that single failure consumed more context than the rest of the run combined. The feedback memory rule was already present and was broken anyway; memory alone does not bind. The harness must enforce.

**What it does:** When a `Read` call targets a file with an image extension, the hook emits a clear remediation message to stderr and exits non-zero, blocking the call. The message names the two correct alternatives:

- **`jack-tar-deckhand:image-reviewer`** agent — dispatches Haiku with the image path + intent, returns a compact JSON verdict. Use for routine per-image review.
- **`general-purpose`** agent (Sonnet/Opus) — higher visual accuracy for complex scenes or when cross-validation with the image-reviewer is needed.

Both subagents read the image into their own context and return text — the orchestration context stays lean.

**Bypass:** Set `ALLOW_PNG_READ=1` in the environment when the image IS the user-facing answer — for example, the user explicitly said "show me X". The bypass requires exact string `1`; other truthy values do not bypass. Treat this as a deliberate signal, not a workaround. For test fixtures that need to inspect generated images, document the bypass in the test and scope it tightly.

**Hook script location:** `plugins/jack-tar-deckhand/hooks/block-png-read.sh`

**Verify the hook is active:** `/jack-tar-deckhand:verify` reports a "DISCIPLINE HOOK" section with three checks — script present + executable, registration in operator settings, and a synthetic fire test (PNG blocked, `ALLOW_PNG_READ` bypassed, non-image passed through).

**Related:** issue [#76](https://github.com/SteveGJones/jack-tar-deckhand/issues/76), retrospective at `docs/superpowers/dogfooding/2026-05-07-blog-post-asset-run.md` (failure #1), plan at `docs/superpowers/plans/2026-05-08-discipline-hook.md`.

## See also — Superpower Bridge route

If you'd rather start from `/pptx` (the upstream skill in the
`superpowers-toolkit` plugin) and have Jack-Tar enrich the resulting
deck, use the **Superpower Bridge** plugin instead of the
`deck-conductor` direct pipeline. The bridge offers `/bridge-brief`
(plan a talk and prep a brief that drives `/pptx`) and `/enrich-deck`
(review an existing `/pptx` deck and layer Jack-Tar visuals onto it).
See `plugins/jack-tar-superpower-bridge/CLAUDE.md` and the
"Choosing your route" section of the top-level `README.md`.
