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
| `/verify` | Check pipeline readiness and engine plugin availability |

## Quick Start

```
/jack-tar-deckhand:verify
```

Then use the deck-conductor agent to orchestrate a full deck build.

## See also — Superpower Bridge route

If you'd rather start from `/pptx` (the upstream skill in the
`superpowers-toolkit` plugin) and have Jack-Tar enrich the resulting
deck, use the **Superpower Bridge** plugin instead of the
`deck-conductor` direct pipeline. The bridge offers `/bridge-brief`
(plan a talk and prep a brief that drives `/pptx`) and `/enrich-deck`
(review an existing `/pptx` deck and layer Jack-Tar visuals onto it).
See `plugins/jack-tar-superpower-bridge/CLAUDE.md` and the
"Choosing your route" section of the top-level `README.md`.
