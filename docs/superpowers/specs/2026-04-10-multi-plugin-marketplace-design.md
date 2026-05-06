# Multi-Plugin Marketplace Architecture

**EPIC:** [#40 — Convert Jack-Tar Deckhand to distributable Claude Code plugin](https://github.com/SteveGJones/jack-tar-deckhand/issues/40)
**Date:** 2026-04-10
**Status:** Design approved, awaiting implementation planning

---

## 1. Vision

Jack-Tar Deckhand becomes a **marketplace of five independent plugins** that users install selectively based on their needs. Someone who just wants local image generation installs `jack-tar-ollama`. Someone who wants the full presentation pipeline installs `jack-tar-deckhand` plus whichever engine plugins they want. The orchestrator gracefully degrades based on what's available — verified at runtime via each plugin's `:verify` skill.

```
claude plugins install jack-tar-ollama                    # just local image gen
claude plugins install jack-tar-cloud                     # just cloud image gen
claude plugins install jack-tar-msft-smartart             # just editable SmartArt
claude plugins install jack-tar-deckhand                  # full pipeline (works alone, better with engines)
claude plugins install jack-tar-ollama jack-tar-cloud \
  jack-tar-msft-smartart jack-tar-custom-smartart \
  jack-tar-deckhand                                       # everything
```

---

## 2. The Five Plugins

### 2.1 jack-tar-ollama

**Standalone value:** Local AI image generation for any project. No API keys, no cloud costs, no network dependency.

**Migrated from:** `github.com/SteveGJones/claude-ollama-image-generator`

**Skills:**
| Skill | Purpose | Default model |
|-------|---------|---------------|
| `jack-tar-ollama:image` | General image generation with iterative vision-based refinement | x/z-image-turbo |
| `jack-tar-ollama:icon` | App icons/favicons optimised for small sizes | x/flux2-klein |
| `jack-tar-ollama:pattern` | Seamless textures and repeating patterns (5 style types) | x/z-image-turbo |
| `jack-tar-ollama:diagram` | Technical diagrams with FLUX spatial hierarchy prompting | x/flux2-klein |
| `jack-tar-ollama:presentation` | Quick presentation generation (images + pptxgenjs) | x/z-image-turbo |
| `jack-tar-ollama:verify` | Is Ollama running? Which x/ models are pulled? | — |

**Agents:**
- `ollama-image-expert` — domain knowledge: scoring rubric (6 dimensions, >=7.5 threshold), prompt engineering per model (z-image-turbo structure vs FLUX spatial hierarchy), convergence rules, mutation strategies

**Runtime:**
```
plugins/jack-tar-ollama/
├── .claude-plugin/plugin.json
├── CLAUDE.md
├── requirements.txt              # requests>=2.31.0
├── package.json                  # pptxgenjs (for presentation skill only)
├── skills/
│   ├── image/SKILL.md
│   ├── icon/SKILL.md
│   ├── pattern/SKILL.md
│   ├── diagram/SKILL.md
│   ├── presentation/SKILL.md
│   └── verify/SKILL.md
├── agents/
│   └── ollama-image-expert.md
├── src/
│   └── generate_image.py         # 104 lines, requests-only Ollama API helper
└── tests/
    └── test_generate_image.py    # 18 unit tests (all HTTP mocked)
```

**Prerequisites:** Ollama binary installed and running. At least one `x/` prefix image generation model pulled.

**What migrates from `claude-ollama-image-generator`:**
- 5 SKILL.md files (renamed: `ollama-image` -> `image`, etc. — plugin namespace provides prefix)
- 1 agent (ollama-image-expert.md)
- 1 Python file (src/generate_image.py)
- 18 tests (test_generate_image.py)
- The `install-image-gen` agent is dropped (replaced by plugin install mechanism)
- The `ollama-presentation` skill stays — it's a lightweight alternative for users who don't need the full deckhand pipeline

---

### 2.2 jack-tar-cloud

**Standalone value:** Cloud AI image generation for any project. Per-provider skills so users can target a specific API, plus router skills that pick the best available.

**Skills:**
| Skill | Purpose | Requires |
|-------|---------|----------|
| `jack-tar-cloud:openai-image` | Generate via OpenAI GPT Image | `OPENAI_API_KEY` |
| `jack-tar-cloud:google-image` | Generate via Google Gemini/Imagen | `GOOGLE_CLOUD_PROJECT` |
| `jack-tar-cloud:fal-image` | Generate via FAL.ai FLUX Pro/Klein/Ideogram | `FAL_KEY` |
| `jack-tar-cloud:recraft-icon` | Generate SVG vector icons via Recraft V4 | `OPENAI_API_KEY` (Recraft uses OpenAI-compatible API) |
| `jack-tar-cloud:image` | Smart router: discovers configured providers, picks best available | Any one provider key |
| `jack-tar-cloud:icon` | Smart router for icons: tries Recraft SVG first, falls back | Any one provider key |
| `jack-tar-cloud:verify` | Checks each provider's API key, tests connectivity | — |

**Agents:**
- `image-generation-expert` — advisory agent for prompt translation across providers, production upgrade planning (raster vs vector track), quality scoring guidance

**Runtime:**
```
plugins/jack-tar-cloud/
├── .claude-plugin/plugin.json
├── CLAUDE.md
├── requirements.txt              # requests, openai, google-genai, fal-client
├── skills/
│   ├── openai-image/SKILL.md
│   ├── google-image/SKILL.md
│   ├── fal-image/SKILL.md
│   ├── recraft-icon/SKILL.md
│   ├── image/SKILL.md            # router
│   ├── icon/SKILL.md             # router
│   └── verify/SKILL.md
├── agents/
│   └── image-generation-expert.md
└── src/
    ├── generate_cloud_image.py   # per-provider generation (OpenAI, Google, FAL)
    ├── generate_cloud_icon.py    # Recraft + FAL icon generation
    ├── provider_discovery.py     # probe which providers are configured
    └── prompt_translator.py      # model-specific prompt adaptation
```

**What changes from today:**
- `generate_cloud_image.py` currently has all providers in one file with a dispatch function. Per-provider skills call the same module specifying the provider explicitly — no refactoring needed.
- `provider_discovery.py` moves from deckhand's `src/` into this plugin — it's fundamentally about cloud provider availability.
- `prompt_translator.py` moves here — it translates prompts between model-specific formats.
- The router skill (`jack-tar-cloud:image`) does what `image_router.py`'s cloud portion does today, as a standalone skill.
- Deckhand's `image_router.py` is adapted to work via the verify contract rather than importing `provider_discovery.py` directly. The bridge calls `jack-tar-cloud:verify` to learn which providers are ready, then invokes per-provider skills accordingly.

---

### 2.3 jack-tar-msft-smartart

**Standalone value:** Editable PowerPoint SmartArt graphics. Speakers can modify nodes, switch layouts, and insert images directly in PowerPoint after delivery. 29 layouts across 9 categories, all MIT-sourced from dotnet/Open-XML-SDK.

**Skills:**
| Skill | Purpose |
|-------|---------|
| `jack-tar-msft-smartart:render` | Generate editable SmartArt carrier .pptx from a spec (layout ID + data) |
| `jack-tar-msft-smartart:inject` | Graft SmartArt diagram parts from carrier files into an assembled deck |
| `jack-tar-msft-smartart:catalog` | List available layouts with capacity, visual character, when-to-use guidance |
| `jack-tar-msft-smartart:verify` | Are python-pptx and lxml installed? Are layout fixtures present? Can we build a test carrier? |

**No agents** — the smartart-selector agent lives in deckhand (orchestration concern).

**Runtime:**
```
plugins/jack-tar-msft-smartart/
├── .claude-plugin/plugin.json
├── CLAUDE.md
├── requirements.txt              # python-pptx>=1.0.0, lxml>=4.9.0, jsonschema>=4.20.0
├── skills/
│   ├── render/SKILL.md
│   ├── inject/SKILL.md
│   ├── catalog/SKILL.md
│   └── verify/SKILL.md
├── src/
│   ├── engine.py                 # render(spec, output_dir) -> carrier .pptx
│   ├── data_model.py             # XML construction primitives
│   ├── builders/
│   │   ├── __init__.py           # BUILDER_BY_DATA_SHAPE dispatcher
│   │   ├── flat_list.py          # 22 layouts (process, cycle, list, matrix, pyramid, relationship)
│   │   ├── hierarchical.py       # 5 layouts (orgChart, hierarchy2-6)
│   │   └── picture.py            # picture-embedding SmartArt
│   ├── layouts/
│   │   ├── catalog.py            # load_catalog(), get_entry(), resolve_layout_dir()
│   │   ├── catalog.json          # single source of truth (29 entries)
│   │   ├── catalog.schema.json   # Draft-07 validator
│   │   └── catalog_markdown.py   # auto-generates docs
│   ├── assembler_patch.py        # inject(host_pptx, requests) — post-assembly surgery
│   ├── pipeline.py               # run_injection_step() orchestration wrapper
│   └── selector_integration.py   # is_pptx_native_candidate(), score helpers
├── data/
│   └── smartart_layouts/         # 29 layout dirs x 4 XML files each (MIT-sourced)
│       ├── _extraction_manifest.json
│       ├── LICENSING.md
│       ├── process1/             # layout.xml, quickStyle.xml, colors.xml, meta.json
│       ├── cycle2/
│       └── ... (27 more)
├── tools/
│   └── extract_smartart_layouts.py   # re-extract from dotnet/Open-XML-SDK
├── tests/
│   └── (16 test files, ~300 tests)
└── docs/
    └── pptx-native-smartart-catalog.md  # auto-generated, CI drift-checked
```

**Key architectural notes:**
- Layout fixtures move from `tests/fixtures/smartart_layouts/` -> `data/smartart_layouts/`. `catalog.py`'s `REPO_ROOT` path calculation adjusts for new depth. The `Path(__file__).resolve().parents[N]` pattern is inherently portable.
- `catalog.json` `layout_dir` entries update from `tests/fixtures/smartart_layouts/X` -> `data/smartart_layouts/X`.
- The `:inject` skill is the bridge between deckhand's assembler and pptx_native surgery. Contract: deckhand calls `jack-tar-msft-smartart:inject` passing the host .pptx path and carrier paths. Inject runs `assembler_patch.py` and returns the patched .pptx.
- Adding a new layout remains a pure catalog change — zero Python code per layout.
- The extraction tool stays in this plugin — re-running `extract_smartart_layouts.py --sdk` picks up new Microsoft layouts.

---

### 2.4 jack-tar-custom-smartart

**Standalone value:** Data visualisation and custom graphics — SVG layouts, Mermaid diagrams, Vega-Lite charts, matplotlib/seaborn data charts. Produces rasterised PNGs embedded into slides.

**Skills:**
| Skill | Purpose |
|-------|---------|
| `jack-tar-custom-smartart:render` | Dispatch to the right engine based on graphic type, produce a PNG |
| `jack-tar-custom-smartart:chart` | Render a data chart (bar, line, area, pie, donut, scatter, radar) |
| `jack-tar-custom-smartart:verify` | Are Mermaid CLI, Vega CLI, matplotlib, cairosvg installed? |

**No agents** — selector lives in deckhand.

**Runtime:**
```
plugins/jack-tar-custom-smartart/
├── .claude-plugin/plugin.json
├── CLAUDE.md
├── requirements.txt              # matplotlib>=3.8.0, seaborn>=0.13.0, Pillow>=10.0.0
├── package.json                  # @mermaid-js/mermaid-cli, vega, vega-cli, vega-lite
├── skills/
│   ├── render/SKILL.md
│   ├── chart/SKILL.md
│   └── verify/SKILL.md
└── src/
    ├── smartart_renderer.py      # engine dispatcher (mermaid, vega, custom_svg, matplotlib)
    ├── render_chart.py           # matplotlib/seaborn chart rendering
    └── smartart_svg/
        ├── __init__.py
        ├── engine.py             # constraint-based container layout engine
        ├── primitives.py         # SVG primitive generators
        ├── tokens.py             # style token extraction (colors, contrast)
        └── layouts/
            ├── __init__.py
            ├── flowchart.py      # 2x2/2x3/3x3 grid layout
            ├── decision_tree.py  # 2-column if/then layout
            ├── timeline.py
            ├── venn.py
            ├── swot.py
            ├── feature_matrix.py
            ├── pipeline_funnel.py
            ├── radar_chart.py
            └── gantt.py
```

**Key architectural notes:**
- Each SmartArt plugin has its own `:render` skill. Deckhand's smartart-extractor decides which plugin to invoke based on the selector's recommendation. No cross-plugin Python imports.
- `smartart_renderer.py` in this plugin only dispatches to the engines it owns (Mermaid, Vega, custom SVG, matplotlib). The pptx_native dispatch path is removed — that routing happens in deckhand.
- Both Python and Node runtimes needed. Verify checks both.
- SVG-to-PNG rasterisation uses cairosvg (preferred) or falls back to Node sharp.

---

### 2.5 jack-tar-deckhand

**Standalone value:** Full presentation engineering pipeline. Sequences brand -> style -> narrative -> strategy -> notes -> images -> SmartArt -> assembly -> QA. Works with any combination of engine plugins, or none at all.

**Skills:**
| Skill | Purpose |
|-------|---------|
| `jack-tar-deckhand:brand-manager` | Extract/load brand profiles from PDF guidelines, .pptx templates, logos |
| `jack-tar-deckhand:slide-stylist` | Derive palette, typography, layout rules through collaborative exploration |
| `jack-tar-deckhand:narrative-architect` | Propose narrative arcs, build SlideOutline |
| `jack-tar-deckhand:strategy-map` | Classify each slide's rendering strategy |
| `jack-tar-deckhand:smartart-selector` | Orchestrate SmartArt type selection, negotiate with narrative-architect |
| `jack-tar-deckhand:smartart-extractor` | Transform slide content into engine-specific data, route to right SmartArt plugin |
| `jack-tar-deckhand:speaker-notes-writer` | Generate timed, transition-cued speaker notes |
| `jack-tar-deckhand:imagegen-bridge` | Discover installed engine plugins via :verify, route images, manage budget/cache/funnel |
| `jack-tar-deckhand:deck-assembler` | Assemble .pptx from all contracts via PptxGenJS, invoke msft-smartart:inject if needed |
| `jack-tar-deckhand:deck-qa` | Run 30 anti-pattern checks |
| `jack-tar-deckhand:verify` | Meta-verify: discover all jack-tar plugins, call each :verify, report aggregate capability |

**Agents:**
| Agent | Model | Purpose |
|-------|-------|---------|
| `deck-conductor` | Opus | Top-level orchestrator, sequences all skills, draft/production lifecycle |
| `prompt-engineer` | Haiku/Sonnet | Transforms structured briefs into creative image prompts |
| `image-reviewer` | Haiku/Sonnet | Per-image quality gate, JSON verdicts (pass/refine) |
| `presentation-reviewer` | — | Reviews assembled deck against conference best practices |
| `vision-analyst` | — | Analyses images for text positioning in backdrop/pragmatic slides |
| `smartart-selector` | Haiku/Sonnet | Recommends graphic types and enrichment tiers |

**Runtime:**
```
plugins/jack-tar-deckhand/
├── .claude-plugin/plugin.json
├── CLAUDE.md
├── requirements.txt              # jsonschema, Pillow, requests, python-pptx
├── package.json                  # pptxgenjs
├── skills/
│   ├── brand-manager/SKILL.md
│   ├── slide-stylist/SKILL.md
│   ├── narrative-architect/SKILL.md
│   ├── strategy-map/SKILL.md
│   ├── smartart-selector/SKILL.md
│   ├── smartart-extractor/SKILL.md
│   ├── speaker-notes-writer/SKILL.md
│   ├── imagegen-bridge/SKILL.md
│   ├── deck-assembler/SKILL.md
│   ├── deck-qa/SKILL.md
│   └── verify/SKILL.md
├── agents/
│   ├── deck-conductor.md
│   ├── prompt-engineer.md
│   ├── image-reviewer.md
│   ├── presentation-reviewer.md
│   ├── vision-analyst.md
│   └── smartart-selector.md
└── src/
    ├── deckcontext.py            # DeckContext init/read/write/validate
    ├── schemas/                  # 13 JSON schemas (all contracts)
    ├── conductor.py              # pipeline state, budget bridge, QA tracking
    ├── budget_tracker.py         # cost tracking across providers
    ├── slide_prompt_composer.py  # strategy classification, brief assembly
    ├── render_funnel.py          # 3-stage draft->production render funnel
    ├── image_router.py           # routing matrix, fallback chains
    ├── brand_profile.py          # brand extraction and persistence
    ├── style_validation.py       # StyleGuide validation
    ├── content_validation.py     # outline/notes schema validation
    ├── process_image.py          # resize, crop, hash, SVG rasterise, placeholders
    ├── cache_manager.py          # 2-tier image cache
    ├── manifest_utils.py         # surgical manifest updates
    ├── assembler/
    │   └── build_deck.js         # PptxGenJS assembly
    └── qa/
        ├── run_qa.py
        ├── config.py
        ├── report.py
        └── checks/               # 10 check modules, 30 anti-patterns
```

**Graceful degradation via verify:**

| Installed plugins | Capability |
|---|---|
| All four engines | Full pipeline: draft Ollama -> production cloud, editable + rasterised SmartArt |
| ollama only | Draft-quality decks with Ollama images, text-only SmartArt fallback |
| cloud only | Production-quality images, no local generation, text-only SmartArt |
| msft-smartart only | Text-only slides but with editable SmartArt graphics |
| custom-smartart only | Text-only slides but with rasterised data viz |
| None | Text-only deck with placeholder images — still a valid .pptx |

---

## 3. The Verify Contract

Every plugin implements `:verify` with a consistent output format that is both human-readable and parseable.

### Output format

```
PLUGIN: <plugin-name>
VERSION: <semver>

DEPENDENCIES:
  <name>:          READY (<version>) | NOT_READY (<reason>)

<PLUGIN-SPECIFIC SECTIONS>:
  <name>:          READY (<detail>) | NOT_READY (<reason>)

STATUS: FULLY_AVAILABLE | PARTIALLY_AVAILABLE | NOT_AVAILABLE
REASON: <human-readable explanation if not fully available>
```

### Status semantics

| Status | Meaning | Bridge behaviour |
|--------|---------|-----------------|
| `FULLY_AVAILABLE` | All capabilities operational | Route normally |
| `PARTIALLY_AVAILABLE` | Some capabilities work, some don't | Route selectively to working capabilities |
| `NOT_AVAILABLE` | Fundamental prerequisites missing | Skip entirely, try fallbacks |
| Not installed | Plugin doesn't exist in Claude Code | Skip entirely |

### Deckhand meta-verify

`jack-tar-deckhand:verify` discovers all installed jack-tar plugins, calls each `:verify`, and produces an aggregate capability report:

```
PLUGIN: jack-tar-deckhand
VERSION: 1.0.0

ENGINE PLUGINS:
  jack-tar-ollama:           FULLY_AVAILABLE
  jack-tar-cloud:            PARTIALLY_AVAILABLE
  jack-tar-msft-smartart:    FULLY_AVAILABLE
  jack-tar-custom-smartart:  NOT_AVAILABLE (mermaid-cli not installed)

PIPELINE CAPABILITY:
  Draft images:      READY (ollama available)
  Production images: READY (cloud partially available — openai, fal)
  Editable SmartArt: READY (msft-smartart available)
  Custom graphics:   NOT_READY (custom-smartart not available)
  Deck assembly:     READY (pptxgenjs installed)
  QA checks:         READY

STATUS: PARTIALLY_AVAILABLE
REASON: jack-tar-custom-smartart not available (install mermaid-cli)
```

---

## 4. Marketplace Structure

### One repo, one marketplace, five plugins

**Root `marketplace.json`:**

```json
{
  "name": "jack-tar",
  "description": "Conference-quality presentation engineering for Claude Code",
  "owner": {
    "name": "Steve Jones"
  },
  "plugins": [
    {
      "name": "jack-tar-ollama",
      "description": "Local AI image generation via Ollama — images, icons, patterns, diagrams, and quick presentations",
      "source": "./plugins/jack-tar-ollama",
      "version": "1.0.0"
    },
    {
      "name": "jack-tar-cloud",
      "description": "Cloud AI image generation — OpenAI, Google, FAL.ai, Recraft with smart provider routing",
      "source": "./plugins/jack-tar-cloud",
      "version": "1.0.0"
    },
    {
      "name": "jack-tar-msft-smartart",
      "description": "Editable PowerPoint SmartArt graphics — 29 layouts, speakers can modify after delivery",
      "source": "./plugins/jack-tar-msft-smartart",
      "version": "1.0.0"
    },
    {
      "name": "jack-tar-custom-smartart",
      "description": "Data visualisation and custom graphics — SVG, Mermaid, Vega-Lite, matplotlib charts",
      "source": "./plugins/jack-tar-custom-smartart",
      "version": "1.0.0"
    },
    {
      "name": "jack-tar-deckhand",
      "description": "Full presentation pipeline — brand, style, narrative, images, SmartArt, assembly, QA",
      "source": "./plugins/jack-tar-deckhand",
      "version": "1.0.0"
    }
  ]
}
```

### Top-level repo structure

```
jack-tar-deckhand/                    # the repo (marketplace root)
├── .claude-plugin/
│   └── marketplace.json              # declares all 5 plugins
├── plugins/
│   ├── jack-tar-ollama/
│   ├── jack-tar-cloud/
│   ├── jack-tar-msft-smartart/
│   ├── jack-tar-custom-smartart/
│   └── jack-tar-deckhand/
├── tests/                            # shared test infrastructure
├── docs/                             # architecture, research
├── tools/                            # extraction scripts, utilities
├── research/                         # 20 papers (dev reference only, not shipped)
├── .bsa/                             # BSA canonical model (dev reference only)
├── README.md                         # consumer-facing
├── LICENSE
└── CLAUDE.md                         # repo-level dev instructions
```

**Not shipped in any plugin:**
- `research/` — 20 papers, development reference only
- `.bsa/` — BSA canonical model
- BSA skills and agents — from the ai-first-sdlc plugin, not jack-tar
- `docs/superpowers/` — design specs and plans
- `docs/spikes/` — spike investigations
- `CONSTITUTION.md`, `CLAUDE-CORE.md` — repo-level governance
- `tools/build_demo_deck.py` — developer utility

---

## 5. Cross-Plugin Contracts

### 5.1 How deckhand discovers engine plugins

The `imagegen-bridge` skill calls `:verify` on each known engine plugin name at pipeline start. It doesn't import code from other plugins — it invokes skills via the `Skill` tool:

```
# Bridge discovery pseudocode (executed as skill invocations, not Python imports)
for plugin in ['jack-tar-ollama', 'jack-tar-cloud', 'jack-tar-msft-smartart', 'jack-tar-custom-smartart']:
    result = invoke(f'{plugin}:verify')
    capabilities[plugin] = parse_status(result)
```

### 5.2 How deckhand routes to engine plugins

| Slide need | Plugin invoked | Skill |
|------------|---------------|-------|
| Draft hero image | `jack-tar-ollama:image` | Via imagegen-bridge |
| Production hero image | `jack-tar-cloud:image` | Via imagegen-bridge |
| Editable SmartArt | `jack-tar-msft-smartart:render` | Via smartart-extractor |
| Custom SVG/chart | `jack-tar-custom-smartart:render` or `:chart` | Via smartart-extractor |
| Post-assembly SmartArt injection | `jack-tar-msft-smartart:inject` | Via deck-assembler |

### 5.3 How the assembler_patch injection works

1. `deck-assembler` runs `build_deck.js` -> produces `presentation.pptx` with named placeholder rects for any pptx_native SmartArt slides
2. `deck-assembler` checks if SmartArt carriers exist (produced by `jack-tar-msft-smartart:render`)
3. If yes, invokes `jack-tar-msft-smartart:inject` passing:
   - Host .pptx path
   - List of carrier .pptx paths with their target slide numbers
4. `jack-tar-msft-smartart:inject` runs `assembler_patch.py`, replaces placeholder rects with real SmartArt diagram parts
5. Returns the patched .pptx path

### 5.4 DeckContext contracts

The 13 JSON schemas stay in `jack-tar-deckhand` since they define the pipeline's internal contracts. Engine plugins don't read or write DeckContext — they receive specs as arguments and return file paths.

---

## 6. Path Resolution Strategy

### The problem

Skills embed Python snippets with `from src.xxx import ...` which requires the Python path to include the plugin's root directory. In a plugin context, the code is at `~/.claude/plugins/cache/jack-tar/<plugin>/<version>/`.

### The solution: `bin/jt-run` per plugin

Each plugin that has Python runtime code includes a `bin/jt-run` shell script:

```bash
#!/usr/bin/env bash
# Discover plugin root from this script's location
PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Create venv if it doesn't exist
if [ ! -d "$PLUGIN_ROOT/.venv" ]; then
    python3 -m venv "$PLUGIN_ROOT/.venv"
    "$PLUGIN_ROOT/.venv/bin/pip" install -r "$PLUGIN_ROOT/requirements.txt"
fi

# Activate venv and set Python path
export PYTHONPATH="$PLUGIN_ROOT:$PYTHONPATH"
"$PLUGIN_ROOT/.venv/bin/python3" "$@"
```

Skills use it instead of bare `python3`:

```bash
# Before (repo-local):
source .venv/bin/activate && python3 -c "from src.conductor import init_pipeline; ..."

# After (plugin-portable):
"$PLUGIN_ROOT/bin/jt-run" -c "from src.conductor import init_pipeline; ..."
```

Each skill discovers `$PLUGIN_ROOT` from its own SKILL.md location. Claude Code knows where skill files live, so the skill preamble resolves the path.

---

## 7. Migration Path

### Constraints
- The existing 952 tests must pass throughout migration
- Main branch is never broken
- Each phase produces a working, testable state

### Phase 1: Scaffold plugin directories
- Create `plugins/` with all 5 plugin subdirectories
- Create `.claude-plugin/plugin.json` for each
- Create root `marketplace.json`
- No code moves — just scaffolding
- **Test gate:** existing tests still pass (nothing changed)

### Phase 2: Copy and adapt (parallel work per plugin)
- Copy source files into target plugin directories
- Adapt internal imports so modules reference each other locally
- Write `:verify` skill for each plugin
- Write `CLAUDE.md` for each plugin
- Write `bin/jt-run` for plugins with Python runtime
- Original files remain untouched — both structures coexist
- **Test gate:** write new tests per plugin that verify modules load and basic operations work from the plugin directory

### Phase 3: Migrate Ollama from claude-ollama-image-generator
- Copy 5 SKILL.md files, 1 agent, `generate_image.py` from `../claude-ollama-image-generator/`
- Rename skills (remove `ollama-` prefix, plugin namespace handles it)
- Copy 18 tests
- Add verify skill
- Drop install-image-gen agent
- **Test gate:** 18 Ollama tests pass from plugin directory + verify skill works

### Phase 4: Rewrite skill Python invocations
- Update all skills to use `$PLUGIN_ROOT/bin/jt-run` instead of `source .venv/bin/activate && python3`
- Update the 46 `from src.*` import references across 14 skills + 1 agent
- Update deck-assembler to resolve `build_deck.js` from plugin root
- **Test gate:** each plugin's skills can be invoked from a non-repo directory

### Phase 5: Cross-plugin integration testing
- Verify deckhand can discover and invoke engine plugin skills
- Verify the verify contract works across all plugins
- Verify graceful degradation (remove plugins one by one, confirm deckhand adapts)
- Verify assembler_patch injection flow via `jack-tar-msft-smartart:inject`
- Verify imagegen-bridge routes correctly based on verify results
- **Test gate:** full pipeline integration test with all plugins installed + degradation tests

### Phase 6: Remove legacy structure
- Remove original `src/` files that have been copied to plugins
- Remove original `.claude/skills/` presentation skills (keep BSA skills)
- Remove original `.claude/agents/` presentation agents (keep BSA agents)
- Update repo-level CLAUDE.md
- Update EPIC #40
- **Test gate:** all plugin tests pass, no references to old paths remain

### Phase 7: Polish and publish
- Consumer-facing README per plugin
- Quick-start guide per plugin
- Version all plugins as 1.0.0
- Publish to marketplace
- Test fresh install on clean machine
- **Test gate:** `claude plugins install jack-tar-deckhand` works, verify reports ready, first deck builds

---

## 8. Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Claude Code plugin API changes | Medium | High | Follow superpowers/document-skills patterns |
| Cross-plugin skill invocation latency | Low | Medium | Skills are invoked sequentially anyway in the pipeline |
| Plugin install order matters | Low | Medium | Each plugin is independently installable; deckhand degrades gracefully |
| Large total install size (~50MB all plugins) | Low | Low | Users install only what they need |
| `$PLUGIN_ROOT` discovery fails | Medium | High | Test on macOS + Linux; provide fallback env var |
| Breaking existing repo-based users | High | Medium | Phase 2 maintains both structures; Phase 6 is the clean break |
| Ollama repo diverges after we fork | Low | Low | We own the fork; upstream was our repo anyway |

---

## 9. Success Criteria

1. Each plugin is independently installable via `claude plugins install <name>`
2. Each plugin's `:verify` accurately reports availability
3. `jack-tar-deckhand:verify` aggregates all engine plugin status
4. `imagegen-bridge` routes correctly based on available plugins
5. Full pipeline works with all plugins installed
6. Pipeline degrades gracefully with partial plugin installation
7. Ollama skills work standalone without deckhand
8. Cloud skills work standalone without deckhand
9. SmartArt skills produce valid output standalone
10. All existing tests pass throughout migration
11. Fresh install on clean machine produces a working deck
