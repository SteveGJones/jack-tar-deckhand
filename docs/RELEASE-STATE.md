# Jack-Tar — Release State

Current-state summary of the Jack-Tar Claude Code marketplace. Versions below are
read directly from each plugin's `.claude-plugin/plugin.json` and the marketplace
manifest at `.claude-plugin/marketplace.json`. This is an index / summary doc, not a
changelog.

## Plugins

| Plugin | Version | Purpose |
|--------|---------|---------|
| `jack-tar-ollama` | 1.1.1 | Local AI image generation via Ollama (free draft tier) |
| `jack-tar-cloud` | 1.3.3 | Cloud AI image generation (OpenAI, Google, FAL.ai, Recraft) |
| `jack-tar-msft-smartart` | 1.2.2 | Editable PowerPoint SmartArt (29 layouts, native OOXML) |
| `jack-tar-custom-smartart` | 1.1.1 | Data viz and custom graphics (SVG, Mermaid, Vega-Lite, matplotlib) |
| `jack-tar-deckhand` | 1.5.1 | Full presentation pipeline orchestrator |
| `jack-tar-superpower-bridge` | 0.3.0 | Bridge from `/pptx` decks into Jack-Tar enrichment |

## Marketplace manifest

`.claude-plugin/marketplace.json` registers all six plugins under the `jack-tar`
marketplace (owner: Steve Jones). The manifest tracks versions per-plugin (listed in
the table above); it does not carry a single top-level marketplace version field.

## What's GA vs in-progress

**GA / shipped:**

- The core deck pipeline in `jack-tar-deckhand` (brand-manager → slide-stylist →
  narrative-architect → strategy-map → smartart selection/extraction →
  speaker-notes-writer → imagegen-bridge → deck-assembler → deck-qa).
- Five rendering strategies plus `full_bleed` (image-is-the-slide, zero chrome).
- Editable SmartArt (`jack-tar-msft-smartart`) and custom data-viz graphics
  (`jack-tar-custom-smartart`).
- Cloud resolution control (1K / 2K / 4K) and Recraft V4 brand-fidelity raster in
  `jack-tar-cloud`.
- The Superpower Bridge route (`/bridge-brief`, `/enrich-deck`) for enriching
  `/pptx`-authored decks.

**Headline recent capability — `creative_vision` (v1.5):**

- Operator prose → vision-faithful full-slide image via a multi-agent cascade
  (Director's Brief → Prompt Reviewer → Render → image-reviewer → Director's Critic).
- Always pairs with `full_bleed` assembly. GA flow has four load-bearing parts:
  strategy-map cost surfacing, a pre-deck Creative Sprint phase, a per-iteration
  operator gate (F12), and optional deck-level creative anchors.
- See the "Creative vision pipeline" section of
  `plugins/jack-tar-deckhand/CLAUDE.md` for the full GA flow.

**Optional external integration:**

- `academic_figure` slides route through the external **paperbanana** CLI when it is
  installed locally (`pip install 'paperbanana[google]'`, `pipx`, or `uvx`).
  paperbanana is treated as an external CLI tool — a sibling orchestrator like LaTeX
  or ImageMagick — not as a Claude Code plugin. When absent, the bridge falls back to
  Nano Banana Flash 1K with academic-figure-aware prompting; pipelines never break on
  the absent optional dependency. ADR:
  `docs/architecture/paperbanana-integration-v2.md`.

## Tests

Per-plugin test counts are not hand-maintained here — run `pytest` within each plugin
(via `.venv/bin/pytest`) for current counts.
