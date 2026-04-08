# CLAUDE.md

All rules are in **CONSTITUTION.md**. Core instructions are in **CLAUDE-CORE.md**.

## MANDATORY: Visual Output Review (Constitution Article 9.4)

**NEVER return visual artifacts to the user without reviewing every output first.** This means:
- View each generated image (SmartArt, Ollama, cloud) immediately after creation
- View each rasterised PNG after SVG-to-PNG conversion
- View assembled slides after deck assembly (rasterise .pptx to PNG if needed)
- Compare every visual against the original intent
- "File exists" or "pipeline completed" is NOT a review

This rule exists because visual review was skipped THREE TIMES across multiple conversations, each time producing decks with blank slides, missing text, or broken graphics that the user had to catch.

## MANDATORY: Agent Definition Reloading

**Agent definitions in `.claude/agents/*.md` are loaded at session start, NOT on every dispatch.** When you modify an agent's protocol (e.g., `image-reviewer.md`):
- The change is NOT picked up by the actual subagent until Claude Code is restarted
- The `general-purpose` agent reads prompts fresh each call, so prompt-injected protocols work without restart
- For iterative reviewer development: test via `general-purpose` agent first, then restart and validate the actual subagent picks up the new definition
- Always tell the user to restart Claude Code after modifying agent definitions if you need the changes to take effect this session

**Validation pattern**: After updating `.claude/agents/<name>.md`, dispatch the subagent and check whether its responses reflect the new criteria. If they don't, the definition is cached and a restart is required.

**Vision capability note**: The `image-reviewer` agent uses Haiku, which has visual perception limitations (e.g., misjudging proportional widths in tapered shapes). For high-accuracy visual review, the `general-purpose` agent (Sonnet/Opus) is more reliable. Use both in parallel for cross-validation when possible.

## Project: Jack-Tar Deckhand

Claude Code skills and agents for conference-quality PowerPoint presentations. This is NOT a standalone app — it runs inside Claude Code.

### Current Status (2026-04-08)

- **BSA Architecture:** v1.4.0, includes keynote pipeline + rendering strategy expansion + image reviewer + SmartArt intelligent graphics
  - Canonical model: `.bsa/models/jack-tar-deckhand.json` (33 services, 6 AI personas, 60 interactions)
  - Documentation: `docs/architecture/` (10 docs + 7 SVG diagrams)

- **Research Library:** Complete — 20 papers, ~110K words in `research/`
  - Start with `research/RESEARCH-INDEX.md` for fast lookup
  - Create `research/synthesis-[skill-name].md` before implementing any skill
  - `research/report-1-landscape-and-spec.md` and `report-2-implementation-and-validation.md` are the pptx_native SmartArt research Phase 1/2

- **Test suite: 826 passing** (650 at PR #21 merge + 168 new for pptx_native + 8 parametrized expansions)
  - Phases 1-6: Foundation through Orchestration (518 tests)
  - SmartArt Intelligent Graphics (PR #21, merged 2026-04-07): 132 tests
  - pptx_native SmartArt engine (in-progress on `feat/pptx-native-smartart-engine`): 168 tests, 20 commits, all 8 phases complete pending merge

- **Full Pipeline:** `/deck-conductor` orchestrates: brand-manager → slide-stylist → narrative-architect → **smartart-selector** → **strategy-map** → **smartart-extractor** → speaker-notes-writer → imagegen-bridge → **smartart-renderer** → chart-renderer → deck-assembler → deck-qa → presentation-reviewer

- **SmartArt Intelligent Graphics (merged 2026-04-07, PR #21):** AI-driven templated graphic generation
  - 10 v1 graphic types: flowchart, decision tree, bar/line chart, radar chart, SWOT, feature matrix, Venn, timeline, pipeline/funnel, Gantt
  - 3 rendering engines: Mermaid.js (graph-based), Vega-Lite (data viz), Custom SVG (spatial/infographic)
  - 4 enrichment tiers: T0 pure programmatic, T1 AI background, T2 AI element icons, T3 full AI render
  - Draft-phase comparator: competing engines render same data, image-reviewer scores, winner locked for production
  - Negotiation pattern: smartart-selector proposes graphic types, narrative-architect approves/rejects (max 2 rounds)
  - New AI persona: SmartArt Selector (Haiku default, Sonnet escalation)
  - **Auto-routing for poor aspect ratios:** 4+ node flowcharts route from Mermaid LR to `src/smartart_svg/layouts/flowchart.py` (2x2/2x3/3x3 grid). 3+ rule decision trees route from Mermaid TB to `src/smartart_svg/layouts/decision_tree.py` (2-column "if/then" layout). Routing logic in `extract()` in `src/smartart_extractor.py`.
  - **Design spec:** `docs/superpowers/specs/2026-04-03-smartart-intelligent-graphics-design.md`
  - **Research:** `research/ai-driven-templated-graphic-generation-research.md`
  - **Latest demo deck:** `output/jack-tar-deckhand-smartart-demo-v7.pptx` (16.2 MB, 28 slides reviewed)
  - **GitHub issue:** #17 (closed)

- **pptx_native SmartArt engine (in progress 2026-04-08, issue #38, branch `feat/pptx-native-smartart-engine`):** Fourth SmartArt engine that produces editable PowerPoint SmartArt graphics (not rasterised PNGs). Speakers can edit nodes, rename them, and switch layouts directly in PowerPoint after delivery.
  - **Technique:** template injection — hand-authored seed `.pptx` files per layout; engine generates a fresh `data1.xml` per graphic; JS assembler places a named placeholder rect; Python post-process grafts the diagram parts in after build_deck.js finishes and replaces the placeholder with a `<p:graphicFrame>`.
  - **v1 scope (3 layouts shipped, 1 deferred):**
    - `process1` (flowchart graphic_type) — working
    - `cycle2` (cycle graphic_type) — working, note Mac PowerPoint's "Basic Cycle" binds to `cycle2` not `cycle1`
    - `orgChart1` (org_chart graphic_type) — working, **includes assistant nodes via `type="asst"` on destination point** (not the connection)
    - `basicTimeline1` — deferred pending seed authoring
  - **Architecture:** `src/smartart_pptx_native/` package
    - `engine.py` — `render(spec, output_dir)` entry point produces a carrier `.pptx` with one slide containing the editable SmartArt
    - `data_model.py` — XML construction primitives: `gid`, `make_doc_pt`, `make_node_pt(text, is_asst=False)`, `make_par_trans`, `make_sib_trans`, `make_cxn`, `wrap_data_model`. Layout-agnostic — flat list and hierarchical layouts use identical primitives, differing only in traversal (linear iteration vs recursive walk)
    - `assembler_patch.py` — Stage 2 Python post-process: `inject(host_pptx, requests)` grafts diagram parts from carriers into the assembled deck, allocating fresh rIds per slide rels, fresh diagram numbers per package (data1/data2/...), patching content types
    - `pipeline.py` — `run_injection_step(deck_dir)` orchestration wrapper; `format_delivery_message(deck_dir)` speaker-facing status
    - `selector_integration.py` — `is_pptx_native_candidate` / `score_pptx_native_candidate` / `format_selector_rationale` helpers the selector agent can use programmatically
    - `layouts/catalog.json` — **single source of truth for per-layout metadata** (seed paths, layout URIs, min/max nodes, max label chars, when_to_use / when_not_to_use, example_input, selector rationale templates). Validated against `catalog.schema.json` (Draft-07) at load time.
    - `layouts/catalog_markdown.py` — generator for `docs/pptx-native-smartart-catalog.md` (checked-in, CI drift detection). Run `.venv/bin/python -m src.smartart_pptx_native.layouts.catalog_markdown` to regenerate.
    - `layouts/process.py` / `cycle.py` / `org_chart.py` — per-layout builders, all constants come from catalog (no hardcoding)
  - **Engine integration:** wired into `src/smartart_renderer.py` `_ENGINE_DISPATCH['pptx_native']`. Extractor handles `engine='pptx_native'` with per-layout data shapes (`{"steps": [...]}`, `{"stages": [...]}`, `{"tree": {...}}`). Org chart extractor parses 2-space-indented body_points with `(asst)` or `[asst]` markers.
  - **JS assembler:** `buildSmartArtSlide` in `src/assembler/build_deck.js` has a pptx_native branch — when `saEntry.engine_used === 'pptx_native'`, emits a named placeholder rect (name format `pptx_native_placeholder_<slide_number>`) instead of `addImage`. Placeholder position drives the injected graphicFrame's xfrm via Python lookup.
  - **QA checks:** SA-06 (diagram parts present), SA-07 (slide references diagram + no orphaned placeholder), SA-08 (no stale drawing cache). All three run against the post-injection deck.
  - **Test coverage (168 pptx_native tests):**
    - Catalog + schema + loader (9)
    - Data model primitives (13)
    - Process builder (15)
    - Engine render + surgical diff (11)
    - Seed sanity parametrized over v1 entries (7, expands with each new entry)
    - Dispatch wiring into smartart_renderer (6)
    - Extractor support (8)
    - Phase 2 integration (6)
    - Assembler patch injection (14)
    - JS placeholder emission (4)
    - QA checks SA-06/07/08 (8)
    - Pipeline orchestration wrapper (7)
    - Phase 4 cycle + orgChart layouts (26)
    - Catalog consolidation — drift, linting, per-entry audit (9)
    - Selector integration helpers (14)
    - Delivery message (10)
    - **Multi-slide deck integration (Phase 3.4, 1 test, 18 distinct invariants)** — proves injection coexists with other strategies via byte-identity check on non-target slides
  - **Validation spikes (all 4 passed in PowerPoint Mac):**
    1. Mutation of process1 seed → editable SmartArt
    2. Generalisation to cycle2 (proves lin ↔ cycle are both supported by the same data model builder, only `loTypeId` changes)
    3. Injection into blank host (proves the delivery-time operation works, not just mutation of existing SmartArt)
    4. Recursive tree builder + assistant nodes for orgChart1
  - **Design spec:** `docs/superpowers/specs/2026-04-08-pptx-native-smartart-engine.md`
  - **Spike report:** `docs/spikes/2026-04-08-pptx-native-smartart-injection.md`
  - **Catalog docs:** `docs/pptx-native-smartart-catalog.md` (auto-generated)
  - **Seed authoring guide:** `docs/dev/smartart-seed-authoring.md`
  - **Seed licensing:** `tests/fixtures/smartart_seeds/LICENSING.md`
  - **Manual gate checklist:** `tests/manual/MANUAL_GATE.md`
  - **GitHub issue:** #38 (open, ready for PR pending legal)
  - **Remaining blockers before merge:**
    1. Legal review of seed file licensing (spec §11.6). Seeds contain Mac PowerPoint–authored layout1.xml/quickStyle1.xml/colors1.xml as opaque blobs. The licensing angle might be eliminable via spike 5 (test if PowerPoint falls back to built-in layouts when given stub layout1.xml with just the matching uniqueId).
    2. basicTimeline1 seed authoring (not strictly required for merge; Phase 4.3 is deferred)
  - **Key design decisions:**
    - Injection happens AFTER the JS assembler finishes (not during). JS owns position, Python owns surgery. Contract between them = a named placeholder rect with known naming convention.
    - Seeds are checked into `tests/fixtures/smartart_seeds/` and the engine reads layout1/quickStyle1/colors1 as opaque bytes. Only data1.xml is generated at runtime.
    - No drawing1.xml ever written — PowerPoint regenerates the presentation tree from layout1.xml on first open (proven by all 4 spikes).
    - Catalog-driven: no per-layout Python constants. Updating catalog.json changes behaviour without touching builder code (but docs/pptx-native-smartart-catalog.md must be regenerated — CI drift detection enforces this).
    - Agent definitions in `.claude/agents/smartart-selector.md` cite the catalog doc as authoritative source rather than restating per-layout metadata — prompt stays in sync with code.

- **Keynote Pipeline:** Five rendering strategies per slide (expanded from 3, 2026-03-30):
  - `full_render` — entire slide as AI-generated image (title, section divider, closing)
  - `background` — atmospheric AI background + text in template zones (5 variants: left_panel, right_panel, bottom_bar, top_band, center_float)
  - `backdrop` — structured AI scene + vision post-analysis for text positioning (Claude Code vision-analyst agent)
  - `pragmatic_composition` — individual AI-generated elements assembled at exact positions with text labels
  - `composed` — standard PptxGenJS assembly (diagrams, charts, code)
  - `backdrop_render` retained for backward compatibility (maps to `background` with `left_panel`)
  - Three-stage render funnel: Ollama draft (free) → cloud low 720p (cheap) → cloud full 2K+ (production)
  - Prompt Engineer agent (Haiku default, Sonnet escalation) generates creative prompts from structured briefs
  - Post-hoc single-slide upgrade via `upgrade_slide_strategy()`
  - **Spike:** `docs/spikes/backdrop-content-aware-positioning.md`
  - **Implementation plan:** `docs/superpowers/plans/2026-03-30-rendering-strategy-expansion.md` (14 tasks)

- **Production Rendering Engine Strategy (2026-03-31):** Expert-advised two-track production upgrade system
  - **Raster Track (raster_upscale):** Ollama draft → cloud production (FLUX Pro, GPT Image, Nanobanana Flash/Pro)
  - **Vector Track (vector_conversion):** Ollama/FLUX draft → Recraft V4 SVG (standard $0.08, pro $0.30)
  - Image-generation-expert produces `production-upgrade-plan.json` before any money is spent
  - Presentation-reviewer returns per-slide verdicts (pass/escalate_tier/escalate_provider/flag_for_speaker)
  - "Try cheap first" principle: start at cheaper tier, reviewer evaluates, escalate if needed
  - **Spec:** `docs/superpowers/specs/2026-03-31-production-rendering-engine-strategy.md`

- **Image Reviewer Agent (2026-04-01):** Subagent-based visual quality gate
  - Dispatched per image after generation, returns compact JSON verdict (pass/refine)
  - Keeps images out of main orchestration context — bridge accumulates only summary strings
  - Haiku default, Sonnet escalation after 3 consecutive refine verdicts
  - 5 assessment criteria: artifacts, subject match, palette compliance, composition, strategy fit
  - `accepted_with_issues` status for images passing after max iterations
  - **Spec:** `docs/superpowers/specs/2026-04-01-image-reviewer-agent-design.md`

- **Production Pipeline Learnings (2026-03-31):** First production render documented 11 gaps
  - `docs/changelog/2026-03-31-production-pipeline-learnings.md`
  - Fixes: source_prompt in manifest, per-image review, local-config.json, provider dimension limits

- **Footer:** Metamirror logo bottom-right on every slide (assembler `addFooterLogo()` helper)

- **Architecture Docs:** `docs/architecture/` (10 docs + 7 SVG diagrams, 4 L1 service docs)

- **Existing ollama-* skills are upstream — do NOT fork or modify them.** The imagegen-bridge handles all DeckContext integration.

- **Local config:** `local-config.json` (gitignored) contains machine-specific settings — Ollama model tags, timeouts. Always read this before Ollama commands. Never hardcode model names without tags.

- **Claude Code permissions:** `.claude/settings.local.json` (tracked, per-developer overrides) controls which commands Claude can run silently vs prompts for. The free iteration loop (Ollama draft + slide review) needs minimal prompting — see `docs/dev/claude-permissions-guide.md` for the three-tier model and the exact commands the SmartArt loop needs. Use wildcard prefix matches (`Bash(tool:*)`) over exact strings.

- **CI is pre-existing broken:** The `AI-First SDLC Validation` GitHub Actions workflow fails on every commit (including main itself) because it references a `tools/` directory that doesn't exist. The failures predate any feature work. Don't try to fix this as part of feature PRs. The substantive `Code Quality Analysis` check passes — that's the one to watch. When merging, `mergeStateStatus: UNSTABLE` from these failing checks is expected.

- **Merge convention:** Use `gh pr merge <n> --merge` (merge commit), never `--squash`. This project ships features through many small fix commits during iteration rounds, and squashing destroys the per-fix granularity.

### Implementation Status

| Module | Location | Tests | Status |
|--------|----------|-------|--------|
| DeckContext management | `src/deckcontext.py` | 10 | Done |
| JSON Schemas (8 contracts) | `src/schemas/` | 27 | Done |
| Image processing | `src/process_image.py` | 19 | Done |
| Provider discovery | `src/provider_discovery.py` | 24 | Done |
| Budget tracker | `src/budget_tracker.py` | 17 | Done |
| Chart renderer | `src/render_chart.py` | 15 | Done |
| Cache manager | `src/cache_manager.py` | 15 | Done |
| Prompt translator | `src/prompt_translator.py` | 20 | Done |
| Cloud image gen | `src/generate_cloud_image.py` | 49 | Done |
| Cloud icon gen | `src/generate_cloud_icon.py` | 28 | Done |
| Image router | `src/image_router.py` | 35 | Done |
| Integration test | `tests/test_integration.py` | 1 | Done |
| Deck assembler | `src/assembler/` | 5 | Done |
| QA checks (30 APs) | `src/qa/` | 65 | Done |
| Phase 5 E2E | `tests/test_phase5_integration.py` | 2 | Done |
| Brand profile utils | `src/brand_profile.py` | 12 | Done |
| Style validation | `src/style_validation.py` | 10 | Done |
| Schema tests (P2) | `tests/test_schemas.py` | 5 | Done |
| Content validation | `src/content_validation.py` | 12 | Done |
| Conductor utils | `src/conductor.py` | 19 | Done |
| Manifest utilities | `src/manifest_utils.py` | 7 | Done |
| SVG rasterisation | `src/process_image.py` | 27 | Done |
| Production upgrade | `src/image_router.py` | 40 | Done |
| Strategy Map schema | `src/schemas/strategy_map.schema.json` | 4 | Done |
| Slide prompt composer | `src/slide_prompt_composer.py` | 20 | Done |
| Prompt engineer agent | `.claude/agents/prompt-engineer.md` | -- | Done |
| Image reviewer agent | `.claude/agents/image-reviewer.md` | -- | Done |
| RenderLog schema | `src/schemas/render_log.schema.json` | 3 | Done |
| Render funnel | `src/render_funnel.py` | 8 | Done |
| Assembler keynote paths | `src/assembler/build_deck.js` | 6 | Done |
| Keynote QA checks | `src/qa/checks/keynote_checks.py` | 5 | Done |
| Strategy-aware QA | `src/qa/run_qa.py` | 65 | Done |
| Pipeline step order | `src/deckcontext.py` | 1 | Done |
| Upgrade slide strategy | `src/conductor.py` | 23 | Done |
| Production upgrade plan | `src/image_router.py`, `src/schemas/` | 11 | Done |

### Architecture Summary

- **Approach B (Domain-Centric):** Services designed for reuse beyond deck production
- **4 L1 Services:** Content, Design, Image, Assembly & QA
- **6 AI Personas:** Deck Conductor (orchestrator), Image Generation Expert (advisory), Image Reviewer (quality), Presentation Reviewer (advisory), Prompt Engineer (invoker, Haiku/Sonnet), SmartArt Selector (invoker, Haiku/Sonnet)
- **24 Deliverables:** 17 skills + 3 capabilities + 6 agents
- **Naming Convention:** Provider prefix — `ollama-*` for local, `cloud-*` for cloud image skills

### Key Files

| File | Purpose |
|------|---------|
| `.bsa/models/jack-tar-deckhand.json` | Canonical model (single source of truth) |
| `docs/architecture/architecture-overview.md` | One-page architecture summary |
| `docs/architecture/ai-persona-summaries.md` | 6 agent contracts |
| `docs/architecture/diagrams/` | 7 SVG architecture diagrams |
| `research/RESEARCH-INDEX.md` | Research library index with key findings |
| `docs/superpowers/specs/2026-03-29-bsa-architecture-design.md` | Full design decisions |

# AI-First Architecture Toolkit

This project uses the AI-First Business Service Architecture methodology toolkit.

## Methodology Reference

The following file provides complete access to all agents, skills, and methodology references:

@.claude/agents/TOOLKIT-REFERENCE.md

For detailed documentation, see:
- Installation: .claude/agents/TOOLKIT-REFERENCE.md (Agents & Skills section)
- Diagram Tools: .bsa/diagram-tools/README.md
- Design Assets: .bsa/design/

