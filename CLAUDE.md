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

## Plugin Architecture (EPIC #40)

This repository is now a **5-plugin Claude Code marketplace**. The presentation pipeline has been refactored into independently installable plugins:

| Plugin | Purpose | Skills |
|--------|---------|--------|
| `jack-tar-ollama` | Local AI image generation via Ollama | image, icon, pattern, diagram, presentation, verify |
| `jack-tar-cloud` | Cloud AI image generation (OpenAI, Google, FAL, Recraft) | openai-image, google-image, fal-image, recraft-icon, image, icon, verify |
| `jack-tar-msft-smartart` | Editable PowerPoint SmartArt (29 layouts) | render, inject, catalog, verify |
| `jack-tar-custom-smartart` | Data viz and custom graphics (SVG, Mermaid, Vega) | render, chart, verify |
| `jack-tar-deckhand` | Full presentation pipeline orchestrator | brand-manager, slide-stylist, narrative-architect, strategy-map, smartart-selector, smartart-extractor, speaker-notes-writer, imagegen-bridge, deck-assembler, deck-qa, verify |

**Plugin files:** `plugins/<name>/` — each plugin has `.claude-plugin/plugin.json`, `skills/`, `agents/`, `src/`, `tests/`

**Marketplace manifest:** `.claude-plugin/marketplace.json`

**Quick start:** `/jack-tar-deckhand:verify` → reports which engine plugins are ready

The original `src/` directory remains as the development source of truth. Plugin directories contain copies that are distributed.

## Project: Jack-Tar Deckhand

Claude Code skills and agents for conference-quality PowerPoint presentations. This is NOT a standalone app — it runs inside Claude Code.

### Current Status (2026-05-03)

- **Cloud Resolution Control (Issue #59 — landed):** `jack-tar-cloud` v1.2.0 adds a unified `resolution=` kwarg routing 1K / 2K / 4K to each provider's native API field. New `ProviderResolutionUnsupportedError` carries supported-tier metadata for retry. Per-model capability surfaced via `provider_discovery.discover_providers()`. Imagen dual-pricing detection (Vertex flat vs Gemini Developer API token-based) wired into `estimate_google_cost`.
  - **What's wired:** Nano Banana Pro (1K/2K/4K), Nano Banana Flash (0.5K/1K/2K/4K), Imagen Standard/Ultra (1K/2K), Imagen Fast (1K only), FLUX 2 Pro (1K/2K). 4K ladder validated end-to-end on real API ($0.659 smoke-test spend).
  - **What's deferred:** SKILL.md surface, render funnel `cloud_2k`/`cloud_4k` stages, image-router upgrade tiers, cross-tier refinement loop integration → Issue #60. Recraft V4 raster as first-class provider → Issue #61.
  - **EPIC:** [#58](https://github.com/SteveGJones/jack-tar-deckhand/issues/58) (1 of 4 child issues complete; #62 docs already merged via PR #63)
  - **Spec:** `docs/superpowers/specs/2026-05-02-cloud-resolution-control-design.md`
  - **Plan:** `docs/superpowers/plans/2026-05-02-cloud-resolution-control.md` (10 phases, all complete)
  - **Spike:** `docs/spikes/2026-05-02-google-genai-image-config-spike.md` (PATH-B: typed `ImageConfig` from `google.genai.types`)
  - **Smoke test:** `docs/superpowers/dogfooding/2026-05-03-resolution-smoke-test.md` — Jack Tar wallchart through Ollama → Flash 1K → Flash 4K → Pro 1K → Pro 4K. Pro 4K hero render at 4096×4096 in `output/smoke-test-jack-tar-on-a-page/pro-4k/render.png`. Real bug caught: legacy `src/` at worktree root collides with plugin `src/` on direct Python invocation (does not affect skill-based invocation; documented in dogfood report).
  - **Tests:** 50 unit tests in `plugins/jack-tar-cloud/tests/` (was 4 before this work).

### Current Status (2026-04-16)

- **BSA Architecture:** v1.4.1, includes keynote pipeline + rendering strategy expansion + image reviewer + SmartArt intelligent graphics + cloud resolution control (1K/2K/4K)
  - Canonical model: `.bsa/models/jack-tar-deckhand.json` (33 services, 6 AI personas, 60 interactions)
  - Documentation: `docs/architecture/` (10 docs + 7 SVG diagrams)

- **Research Library:** Complete — 20 papers, ~110K words in `research/`
  - Start with `research/RESEARCH-INDEX.md` for fast lookup
  - Create `research/synthesis-[skill-name].md` before implementing any skill
  - `research/report-1-landscape-and-spec.md` and `report-2-implementation-and-validation.md` are the pptx_native SmartArt research Phase 1/2

- **Test suite: 1010 monorepo + 33 cross-plugin integration tests**
  - Phases 1-6: Foundation through Orchestration (518 tests)
  - SmartArt Intelligent Graphics (PR #21, merged 2026-04-07): 132 tests
  - pptx_native SmartArt engine (PR #39, merged 2026-04-10): ~300 tests across 17 test files — 28 layouts, picture embedding, multi-slide integration
  - Cross-plugin integration tests: `plugins/integration_tests/` (33 tests — verify contracts, PLUGIN_ROOT discovery, msft-smartart pipeline, bridge skill names)

- **Full Pipeline:** `/jack-tar-deckhand:deck-conductor` orchestrates: brand-manager → slide-stylist → narrative-architect → **smartart-selector** → **strategy-map** → **smartart-extractor** → speaker-notes-writer → imagegen-bridge → **smartart-renderer** → chart-renderer → deck-assembler → deck-qa → presentation-reviewer

- **deck-conductor invocation contract (issue #42, fixed):** The conductor is a conversational orchestrator — run as primary agent in a dedicated session, OR as a subagent when TalkBrief provides `preferences.budget_cap_usd` and `preferences.image_backend` (skips Step 0 escalation). Fix: `read_brief_defaults()` in conductor.py extracts budget/providers from brief; agent definition makes escalation conditional.

- **Template-Driven Layout Support (issue #45):** Speakers can provide a corporate .pptx template via `branding.template_pptx_path`. Template analyser (`src/template_analyser.py`) extracts layouts and placeholder geometry, auto-maps to slide types (Speaker confirms). python-pptx assembly engine (`src/assembler/build_deck_template.py`) opens the template, strips example slides, places content into typed placeholders (TITLE, BODY, CONTENT, PICTURE). Strategy map constrained to `composed` in template mode. SmartArt injection works unchanged via placeholder rects in content zones.
  - **Design spec:** `docs/superpowers/specs/2026-04-17-template-driven-layout-design.md`
  - **Implementation plan:** `docs/superpowers/plans/2026-04-17-template-driven-layout.md`

- **Speaker Notes Import (issue #44):** Speakers can provide per-slide narrative notes in external .md/.txt files via `preferences.speaker_notes_path`. Notes parser (`src/notes_parser.py`) supports heading-based, number-marker, and headline fuzzy matching. Writer enriches imported notes with timing/cues and generates for uncovered slides. Enables voiceover auto-generation and self-presenting visual-heavy decks.

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

- **pptx_native SmartArt engine (merged 2026-04-10, PR #39, issue #38):** Fourth SmartArt engine that produces editable PowerPoint SmartArt graphics (not rasterised PNGs). Speakers can edit nodes, rename them, switch layouts, and insert images directly in PowerPoint after delivery. 28 layouts across 8 categories, all MIT-sourced from `dotnet/Open-XML-SDK`. Picture SmartArt with AI-generated embedded images via child-node architecture. SmartArt over AI backgrounds.
  - **Technique:** template injection — three opaque XML parts per layout (layout.xml, quickStyle.xml, colors.xml) extracted from MIT-licensed SDK fixtures; engine generates a fresh `data1.xml` per graphic via generic builders; JS assembler places a named placeholder rect; Python post-process grafts the diagram parts in after build_deck.js finishes and replaces the placeholder with a `<p:graphicFrame>`.
  - **v1 scope (27 layouts shipped, 2 deferred across 9 categories):**
    - **Process (8):** process1 (Basic Process), process4, chevron1, hProcess4, hProcess7, hProcess9, hProcess11, lProcess2
    - **Cycle (2):** cycle2 (Basic Cycle), cycle8
    - **Hierarchy (5):** orgChart1 (Organization Chart — **includes asst node support**), hierarchy2, hierarchy4, hierarchy5, hierarchy6
    - **List (6):** list1 (Basic List), hList6, vList2, vList3, vList4, vList5
    - **Matrix (1):** matrix2
    - **Pyramid (1):** pyramid2
    - **Relationship (4):** venn1 (Basic Venn), venn3, funnel1, target3
    - **Deferred:** `pList1` (Picture List — needs spike 6 image integration), `default` (uncategorised)
    - basicTimeline1 not in SDK fixtures; deferred
  - **Architecture:** `src/smartart_pptx_native/` package
    - `engine.py` — `render(spec, output_dir)` builds carrier `.pptx` from scratch with hand-authored OOXML scaffolding + the three extracted layout XML files + generated data1.xml. No seed unzipping.
    - `data_model.py` — XML construction primitives: `gid`, `make_doc_pt`, `make_node_pt(text, is_asst=False)`, `make_par_trans`, `make_sib_trans`, `make_cxn`, `wrap_data_model`, `build_doc_prset(layout_uri, qs_type_id, cs_type_id)`
    - `builders/flat_list.py` — **generic** flat-list builder handles 22 layouts (Process, Cycle, List, Matrix, Pyramid, Relationship). Accepts `items` canonical key + legacy aliases `steps`/`stages`/`phases`/`nodes`/`labels`.
    - `builders/hierarchical.py` — **generic** hierarchical builder handles 5 layouts (OrgChart, hierarchy2-6). Respects `node_type_capabilities` — only layouts declaring `"asst"` emit `type="asst"` on assistant nodes.
    - `builders/__init__.py` — `BUILDER_BY_DATA_SHAPE` dispatcher. Engine calls `builders.build(data_shape, data, entry)`.
    - `assembler_patch.py` — Stage 2 Python post-process: `inject(host_pptx, requests)` grafts diagram parts from carriers into the assembled deck, allocating fresh rIds per slide rels, fresh diagram numbers per package
    - `pipeline.py` — `run_injection_step(deck_dir)` orchestration wrapper; `format_delivery_message(deck_dir)` speaker-facing status
    - `selector_integration.py` — `is_pptx_native_candidate` / `score_pptx_native_candidate` / `format_selector_rationale` helpers
    - `layouts/catalog.json` (v2.0.0) — **single source of truth for per-layout metadata** (29 entries, `layout_dir` + `qs_type_id` + `cs_type_id` + `data_shape` fields replace Phase 1-7 `seed_path` + `builder_module`). Canonical layouts ordered first so `get_layout_id_for_graphic_type` returns sensible defaults (`flowchart` → `process1`, `cycle` → `cycle2`, `org_chart` → `orgChart1`, etc.)
    - `layouts/catalog.schema.json` — Draft-07 validator for the new v2 shape
    - `layouts/catalog.py` — `load_catalog()`, `get_entry(id)`, `list_entries(v1_only=False)`, `resolve_layout_dir(entry)`, `get_layout_id_for_graphic_type(graphic_type)`, `list_layout_ids_for_graphic_type(graphic_type)`
    - `layouts/catalog_markdown.py` — generator for `docs/pptx-native-smartart-catalog.md` (CI drift detection)
    - `tests/fixtures/smartart_layouts/<id>/` — 29 extracted layout directories × 4 files each (layout.xml, quickStyle.xml, colors.xml, meta.json). All MIT-sourced.
  - **Adding a new layout is a pure catalog change** — zero Python code per layout. Generic builders dispatch by data_shape.
  - **Extraction tool:** `tools/extract_smartart_layouts.py` — walks `dotnet/Open-XML-SDK` repo, downloads every .pptx/.potx, extracts SmartArt layout content into the fixtures dir. `--sdk` mode runs against the full repo in one pass. Safe to rerun — overwrites existing layouts with the latest version. Handles any `.pptx`/`.potx` input if you want to extract from a different source.
  - **Engine integration:** wired into `src/smartart_renderer.py` `_ENGINE_DISPATCH['pptx_native']`. Extractor handles `engine='pptx_native'` with unified data shapes: `{"items": [...]}` for all flat-list graphic types, `{"tree": {...}}` for hierarchical. Org chart extractor parses 2-space-indented body_points with `(asst)` or `[asst]` markers.
  - **JS assembler:** `buildSmartArtSlide` in `src/assembler/build_deck.js` has a pptx_native branch — when `saEntry.engine_used === 'pptx_native'`, emits a named placeholder rect (name format `pptx_native_placeholder_<slide_number>`) instead of `addImage`.
  - **QA checks:** SA-06 (diagram parts present), SA-07 (slide references diagram + no orphaned placeholder), SA-08 (no stale drawing cache). All run post-injection.
  - **Test coverage (290 pptx_native tests, 940 total):** organised by scope:
    - Layout fixture sanity (164 parametrized tests across 27 v1 entries)
    - Catalog + schema + loader
    - Data model primitives
    - Generic builders (flat_list, hierarchical)
    - Engine render end-to-end
    - Extractor routing for all graphic types
    - Dispatch wiring into smartart_renderer
    - Assembler patch injection (spike 3 technique, per-slide + multi-slide)
    - JS placeholder emission
    - QA checks SA-06/07/08
    - Pipeline orchestration wrapper + delivery message
    - Selector integration helpers
    - **Multi-slide deck integration** — proves injection coexists with other strategies via byte-identity check on non-target slides
  - **Validation spikes (all 4 passed in PowerPoint Mac):**
    1. Mutation of process1 seed → editable SmartArt
    2. Generalisation to cycle2 (proves technique crosses algorithm families)
    3. Injection into blank host (proves delivery-time operation works)
    4. Recursive tree builder + assistant nodes for orgChart1
    (Spike 5 — layout stub experiment — obsoleted by Phase 8 full SDK adoption)
  - **Design spec:** `docs/superpowers/specs/2026-04-08-pptx-native-smartart-engine.md`
  - **Spike report:** `docs/spikes/2026-04-08-pptx-native-smartart-injection.md`
  - **Catalog docs:** `docs/pptx-native-smartart-catalog.md` (auto-generated)
  - **Layout provenance + licensing:** `tests/fixtures/smartart_layouts/LICENSING.md` (MIT-sourced, precedent documented)
  - **Extraction manifest:** `tests/fixtures/smartart_layouts/_extraction_manifest.json` (per-layout source trace)
  - **Manual gate checklist:** `tests/manual/MANUAL_GATE.md`
  - **GitHub issue:** #38 (closed), **PR:** #39 (merged 2026-04-10)
  - **Demo deck:** `tools/build_demo_deck.py` — 15-slide "Building AI Agents That Actually Work" conference talk exercising 10 layout types with AI backgrounds and picture embedding
  - **Remaining refinements (not blocking):**
    1. Per-layout capacity constraint refinement (first-pass defaults for non-core layouts)
    2. imagegen-bridge integration for automated image prompts per Picture SmartArt item
    3. Ollama image generation blocked by MLX architecture bug in Ollama 0.20.5 — use cloud (FAL/FLUX) for now
  - **Key design decisions:**
    - SDK as canonical source — all layout content from MIT-licensed `dotnet/Open-XML-SDK` test fixtures. Future Microsoft additions picked up by re-running the extraction script.
    - Generic builders keyed by data_shape, not per-layout modules. Adding a layout is a catalog-only change.
    - Canonical layout ordering in catalog.json (process1, cycle2, orgChart1, list1, matrix2, pyramid2, venn1 first) so reverse lookups return sensible defaults.
    - Injection happens AFTER the JS assembler finishes. JS owns position, Python owns surgery. Contract between them = a named placeholder rect.
    - No drawing1.xml ever written — PowerPoint regenerates the presentation tree from layout1.xml on first open (proven by all 4 spikes).
    - Catalog-driven throughout. Catalog markdown is CI drift-checked — if you edit catalog.json you MUST regenerate the markdown in the same commit.

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

- **CI:** `.github/workflows/validation.yml` runs five jobs on every PR — `code-quality` (flake8 + pre-commit), `plugin-tests` (pytest matrix per plugin), `integration-tests` (cross-plugin contracts), `json-validation` (canonical model + marketplace + per-plugin manifests parse and version-match), and a `summary` PR comment. All jobs must pass before merge. **No `--admin` merging** — if CI fails, fix it.

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
| Template analyser | `src/template_analyser.py` | 36 | Done |
| Template assembler | `src/assembler/build_deck_template.py` | 10 | Done |
| Template integration | `tests/test_template_integration.py` | 12 | Done |
| Notes parser | `src/notes_parser.py` | ~31 | Done |

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

