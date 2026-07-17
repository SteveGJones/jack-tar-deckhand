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
| `/deck-qa` | Run 25 automated anti-pattern checks |
| `/iterate-slide` | Single-slide critique-driven refinement via paperbanana `--continue-run` (three modes: auto / enumerate / draft) |
| `/annotate-figure` | Perfect-text labeled figures: label-free render (or external image) + vision anchors + programmatic overlay |
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

## Creative vision pipeline (issue #113 — GA flow)

The `creative_vision` rendering strategy treats the image as the slide's deliverable, not an illustration on it. Operator-driven prose → vision-faithful full-slide image via a multi-agent cascade (Director's Brief → Prompt Reviewer → Render → image-reviewer → Director's Critic). The GA flow has four mandatory load-bearing parts — every deck-conductor session passes through them in this order:

1. **Strategy-map cost surface** — when the strategy map flags any slide as `creative_vision`, the strategy-map skill runs `src.creative_vision.cost_estimator.summarise_creative_vision_spend` BEFORE asking for approval. Operator sees per-slide cost band + operator-gate count, plus a deck-level totals row. If declined on cost grounds, fallback strategies (composed / backdrop / full_render) are offered.
2. **Pre-deck Creative Sprint phase** — deck-conductor runs ALL creative_vision slides to operator acceptance BEFORE any composed / backdrop / full_render assembly. Standard-slide work is BLOCKED until the sprint completes. Resumable via `src.creative_vision.sprint.creative_sprint_progress`.
3. **Per-iteration operator gate (F12)** — for creative_vision slides, the gate fires at EVERY iteration regardless of cost transition (Flash 1K → Flash 1K, Ollama → Ollama, all fire). Canonical predicate: `src.creative_vision.orchestrator.should_fire_operator_gate`. Non-creative_vision strategies retain the F10 free→cost-only cadence.
4. **Deck-level creative anchors** — optional `<deck_dir>/creative_anchors.json` captures recurring characters / props / locations / style anchors. Director's Brief inlines them so all slides agree on canonical appearance. Schema: `src/schemas/creative_anchors.schema.json`. Module: `src/creative_vision/anchors.py`.

**Cost discipline.** Three dogfood spends to calibrate against:
- Sun-phases (single-moment scene): $0.067, 3 attempts, ~3 gates — the easy case
- Naval Academy (single-moment ceremonial scene): $0.268, 7 attempts, 6 gates — the model-friendly case
- Data supply chain (multi-scene narrative): $1.016, 14 attempts, ~10 gates — the model-hostile case

**Single-moment scenes are creative_vision-friendly. Multi-scene narratives are not** — the model has strong priors toward collapse-to-fused-room OR grid-to-N-panels. When the operator's vision fits the model's natural composition territory, the cascade flies; otherwise expect 2-3× the iteration count and recommend a fallback strategy at strategy-map approval.

**See also.**
- Issue #113 (this PR's GA-blocking work)
- Issue #105 (parent — creative_vision v1.5.0)
- Issue #112 (Prompt Simplifier follow-up — pairs with F11)
- CLAUDE.md root MANDATORY sections F10 (operator gate), F11 (prompt simplification), F12 (image-level review)
- Dogfood logs in `docs/superpowers/dogfooding/` named `2026-05-2*-creative-vision-*`

## See also — Superpower Bridge route

If you'd rather start from `/pptx` (the upstream skill in the
`superpowers-toolkit` plugin) and have Jack-Tar enrich the resulting
deck, use the **Superpower Bridge** plugin instead of the
`deck-conductor` direct pipeline. The bridge offers `/bridge-brief`
(plan a talk and prep a brief that drives `/pptx`) and `/enrich-deck`
(review an existing `/pptx` deck and layer Jack-Tar visuals onto it).
See `plugins/jack-tar-superpower-bridge/CLAUDE.md` and the
"Choosing your route" section of the top-level `README.md`.
