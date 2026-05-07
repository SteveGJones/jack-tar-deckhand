# Plugin Architecture Analysis

**EPIC:** [#40 — Convert Jack-Tar Deckhand to distributable Claude Code plugin](https://github.com/SteveGJones/jack-tar-deckhand/issues/40)
**Date:** 2026-04-10
**Status:** Analysis complete, awaiting implementation planning

---

## 1. Executive Summary

Jack-Tar Deckhand is a 17-skill, 8-agent presentation engineering system with 35 Python modules, a JS assembler, 952 tests, and 29 SmartArt layout fixtures. Converting it from a project-local repo to a distributable Claude Code plugin requires solving five structural problems:

1. **Path resolution** — 46 `from src.*` imports across skills/agents assume CWD is the repo root
2. **Runtime bootstrap** — Python venv + npm install must happen at plugin setup time
3. **Fixture relocation** — SmartArt XML layouts live under `tests/` but are runtime data
4. **BSA separation** — 21 methodology skills and 11 agents are co-located but not part of the deck pipeline
5. **Ollama skill ownership** — 4 standalone image skills are currently upstream but should be bundled

The good news: the internal Python architecture is already well-structured. Most modules use `__file__`-relative path resolution (schemas, catalog), which works in any install location. The primary work is in the skill/agent layer and the packaging infrastructure.

---

## 2. Current Architecture Audit

### 2.1 What's in the Repo Today

| Category | Count | Location | Plugin-relevant? |
|----------|-------|----------|-----------------|
| Presentation skills | 17 | `.claude/skills/` | Yes — core plugin |
| Presentation agents | 8 | `.claude/agents/` | Yes — core plugin |
| BSA/methodology skills | 21 | `.claude/skills/` | No — separate concern |
| BSA/methodology agents | 11 | `.claude/agents/` | No — separate concern |
| BSA reference docs | ~30 | `.claude/agents/references/` | No |
| Python modules | 35 | `src/` | Yes — runtime |
| JS assembler | 1 | `src/assembler/` | Yes — runtime |
| JSON schemas | 13 | `src/schemas/` | Yes — runtime |
| SmartArt layouts | 29 dirs | `tests/fixtures/smartart_layouts/` | Yes — runtime data |
| Layout catalog | 2 | `src/smartart_pptx_native/layouts/` | Yes — runtime |
| Tests | 17+ files | `tests/` | Yes — development |
| Research papers | 20 | `research/` | No — development only |
| Architecture docs | 10 | `docs/architecture/` | Optional |
| Tools | 3 | `tools/` | Optional |

### 2.2 Dependency Layers

```
Layer 6: ORCHESTRATION (deck-conductor agent)
    ↓ invokes skills sequentially
Layer 5: ASSEMBLY & QA (deck-assembler skill → build_deck.js, deck-qa → qa/)
    ↓ reads all contracts, produces .pptx
Layer 4: SMARTART (smartart-renderer → svg/, pptx_native/, render_chart)
    ↓ produces SmartArt images/carriers
Layer 3: IMAGE GENERATION (imagegen-bridge → image_router, render_funnel, prompt_translator)
    ↓ routes to ollama/cloud skills
Layer 2: CONTENT PIPELINE (brand-manager, slide-stylist, narrative-architect → brand_profile, etc.)
    ↓ produces DeckContext contracts
Layer 1: INFRASTRUCTURE (deckcontext, schemas/, budget_tracker, provider_discovery, etc.)
    ↓ shared by all layers
Layer 0: STANDALONE (ollama-image, ollama-icon, ollama-pattern, ollama-diagram)
    No internal dependencies — pure CLI/API calls
```

### 2.3 Path Reference Inventory

**Skills with `from src.*` imports:** 14 skills, 31 import statements
- `imagegen-bridge` — 12 imports (most coupled)
- `smartart-renderer` — 2 imports
- `smartart-extractor` — 2 imports
- `cloud-generate-image` — 2 imports
- `cloud-generate-icon` — 2 imports
- `brand-manager` — 2 imports
- `strategy-map` — 1 import
- `slide-stylist` — 1 import
- `narrative-architect` — 1 import
- `speaker-notes-writer` — 1 import
- `smartart-selector` — 1 import
- `deck-qa` — 1 import (uses `-m src.qa.run_qa`)

**Agents with `from src.*` imports:** 1 agent, 15 import statements
- `deck-conductor` — 15 imports

**`.venv` references:** 43 across 12 files

**Node path references:** 1 (`node src/assembler/build_deck.js`)

### 2.4 Python Module Internal Dependencies

```
conductor.py
  ← budget_tracker.py
  ← deckcontext.py
  ← slide_prompt_composer.py

image_router.py
  ← (no internal deps — pure namedtuples + JSON)

smartart_renderer.py
  ← smartart_svg/ (engine + 9 layouts)
  ← render_chart.py

smartart_pptx_native/engine.py
  ← smartart_pptx_native/data_model.py
  ← smartart_pptx_native/builders/ (flat_list, hierarchical, picture)
  ← smartart_pptx_native/layouts/catalog.py

smartart_pptx_native/assembler_patch.py
  ← (standalone — pure OOXML surgery)

qa/run_qa.py
  ← qa/checks/ (8 check modules)
  ← qa/report.py
  ← qa/config.py
  ← deckcontext.py (for schema validation)

deckcontext.py
  ← schemas/ (JSON files, __file__-relative — portable)

generate_cloud_image.py
  ← provider_discovery.py

generate_cloud_icon.py
  ← provider_discovery.py
```

**Key observation:** Most modules use `os.path.dirname(__file__)` or `Path(__file__)` for locating co-packaged files (schemas, catalog). This pattern is **inherently portable** — it works regardless of where the package is installed. The path resolution problem is in the *skills* (which embed Python snippets with `from src.xxx`), not in the Python modules themselves.

---

## 3. Target Plugin Structure

Based on analysis of installed plugins (superpowers 5.0.7, document-skills, sdlc-core):

```
jack-tar-deckhand/
├── .claude-plugin/
│   ├── plugin.json          # name, version, description, author, license
│   └── marketplace.json     # marketplace registry entry
├── CLAUDE.md                # Plugin instructions loaded into context
├── README.md                # Consumer-facing documentation
├── LICENSE
├── package.json             # Version + Node.js dependencies
├── requirements.txt         # Python dependencies
├── skills/
│   ├── brand-manager/SKILL.md
│   ├── slide-stylist/SKILL.md
│   ├── narrative-architect/SKILL.md
│   ├── smartart-selector/SKILL.md
│   ├── strategy-map/SKILL.md
│   ├── smartart-extractor/SKILL.md
│   ├── speaker-notes-writer/SKILL.md
│   ├── imagegen-bridge/SKILL.md
│   ├── smartart-renderer/SKILL.md
│   ├── deck-assembler/SKILL.md
│   ├── deck-qa/SKILL.md
│   ├── cloud-generate-image/SKILL.md
│   ├── cloud-generate-icon/SKILL.md
│   ├── ollama-image/SKILL.md       # ← brought in-house
│   ├── ollama-icon/SKILL.md        # ← brought in-house
│   ├── ollama-pattern/SKILL.md     # ← brought in-house
│   ├── ollama-diagram/SKILL.md     # ← brought in-house
│   └── ollama-presentation/SKILL.md # ← brought in-house
├── agents/
│   ├── deck-conductor.md
│   ├── prompt-engineer.md
│   ├── image-reviewer.md
│   ├── presentation-reviewer.md
│   ├── image-generation-expert.md
│   ├── ollama-image-expert.md      # ← brought in-house
│   ├── vision-analyst.md
│   └── smartart-selector.md
├── hooks/
│   └── post-install.sh             # Bootstrap Python venv + npm install
├── src/                            # Python runtime (unchanged internally)
│   ├── __init__.py
│   ├── deckcontext.py
│   ├── schemas/
│   ├── budget_tracker.py
│   ├── ... (all existing modules)
│   ├── smartart_svg/
│   ├── smartart_pptx_native/
│   ├── assembler/
│   │   └── build_deck.js
│   └── qa/
├── data/
│   └── smartart_layouts/           # ← moved from tests/fixtures/
│       ├── _extraction_manifest.json
│       ├── LICENSING.md
│       ├── process1/
│       │   ├── layout.xml
│       │   ├── quickStyle.xml
│       │   ├── colors.xml
│       │   └── meta.json
│       ├── cycle2/
│       └── ... (29 layout dirs)
├── tools/
│   ├── extract_smartart_layouts.py
│   ├── build_demo_deck.py
│   └── pptx_to_pdf.sh
├── tests/                          # Dev-only, not shipped in plugin
│   ├── fixtures/
│   │   └── smartart_layouts -> ../../data/smartart_layouts  # symlink
│   └── ... (test files)
└── docs/                           # Optional, not required for plugin
```

---

## 4. The Five Structural Problems & Solutions

### 4.1 Path Resolution (the big one)

**Problem:** 46 `from src.*` import statements in skills/agents assume CWD is the repo root. In a plugin context, the code is at `~/.claude/plugins/cache/jack-tar-deckhand/<version>/`.

**Solution: Plugin-root bootstrap pattern**

Every skill that calls Python code should use a two-line bootstrap:

```python
# Before (current — assumes CWD is repo root):
from src.conductor import init_pipeline

# After (plugin-portable):
import sys; sys.path.insert(0, '__PLUGIN_ROOT__')
from src.conductor import init_pipeline
```

**Where `__PLUGIN_ROOT__` comes from:**

Option A (preferred): **Discovery via `__file__` in SKILL.md**
Claude Code skills know their own file path. The SKILL.md can include a bootstrap that discovers the plugin root:

```bash
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$PLUGIN_ROOT/.venv/bin/activate"
python3 -c "
import sys; sys.path.insert(0, '$PLUGIN_ROOT')
from src.conductor import init_pipeline
..."
```

Option B: **Environment variable** set by a post-install hook:
```bash
export JACK_TAR_ROOT="$PLUGIN_INSTALL_PATH"
```

Option C: **Wrapper script** that handles path injection:
```bash
# skills call: $PLUGIN_ROOT/bin/jt-python -c "from src.xxx ..."
# jt-python is a thin wrapper that sets sys.path and activates venv
```

**Recommendation:** Option A with a shared preamble pattern. Create a `bin/jt-run` helper script that:
1. Discovers plugin root from its own location
2. Activates the Python venv
3. Injects `src/` into `sys.path`
4. Runs the provided Python snippet

Then ALL skills use: `"$PLUGIN_ROOT/bin/jt-run" -c "from src.xxx import ..."` instead of `source .venv/bin/activate && python3 -c "from src.xxx ..."`.

For the JS assembler: `node "$PLUGIN_ROOT/src/assembler/build_deck.js" --deck-dir ./tmp/deck`

**Scope:** 14 skills + 1 agent need updating. The `deck-conductor` agent has the most changes (15 import sites).

### 4.2 Runtime Bootstrap

**Problem:** Plugin consumers need Python 3.10+ with pip packages and Node.js with npm packages. No mechanism exists to set these up.

**Solution: Post-install hook + setup skill**

```
hooks/
  post-install.sh    # Runs after plugin installation
```

Post-install script:
1. Check Python 3.10+ is available
2. Create `.venv` inside the plugin directory
3. `pip install -r requirements.txt` into the venv
4. `npm install` in the plugin directory (pptxgenjs, mermaid-cli, vega)
5. Write a `.jack-tar-ready` sentinel file

Additionally, create a `/jack-tar-setup` skill that:
- Re-runs bootstrap if needed
- Configures `local-config.json` for Ollama models
- Runs provider discovery to check API keys
- Reports readiness status

**Dependencies to install:**

Python (requirements.txt):
- jsonschema>=4.20.0
- Pillow>=10.0.0
- requests>=2.31.0
- matplotlib>=3.8.0
- seaborn>=0.13.0
- python-pptx>=1.0.0
- lxml>=4.9.0

Node (package.json):
- pptxgenjs ^4.0.1
- @mermaid-js/mermaid-cli ^11.12.0
- vega ^6.2.0
- vega-cli ^6.2.0
- vega-lite ^6.4.2

### 4.3 SmartArt Fixture Relocation

**Problem:** 29 SmartArt layout directories (116 XML files) live at `tests/fixtures/smartart_layouts/`. They are runtime data, not test data — the pptx_native engine loads them to build carrier .pptx files.

**Solution:**

1. Move `tests/fixtures/smartart_layouts/` → `data/smartart_layouts/`
2. Create a symlink at old location for test backward compatibility
3. Update `catalog.json` entries: `"layout_dir": "tests/fixtures/smartart_layouts/X"` → `"layout_dir": "data/smartart_layouts/X"`
4. `catalog.py` already uses `REPO_ROOT = Path(__file__).resolve().parents[3]` — this resolves correctly as long as the directory is at the right relative position from the `catalog.py` file. After the move, `REPO_ROOT / "data/smartart_layouts/X"` will resolve correctly.
5. Update `tools/extract_smartart_layouts.py` output dir
6. Regenerate `docs/pptx-native-smartart-catalog.md` (CI drift check enforces this)

**Risk:** Low. The path resolution uses `__file__`-relative resolution which is inherently portable.

### 4.4 BSA Separation

**Problem:** 21 methodology skills and 11 BSA agents are co-located in `.claude/skills/` and `.claude/agents/` alongside the deck pipeline artifacts. They're not part of the deck pipeline and shouldn't ship with the plugin.

**Current BSA skills (to exclude from plugin):**
- ai-persona-definition, bpmn-ai-process-generator, bsa-cross-reference-index, bsa-diagram-orchestrator, bsa-documentation-generator, bsa-persona-enricher, bsa-pipeline-orchestrator, canonical-model-manager, canonical-model-validator, change-advisory-circle-manager, cross-model-validator, demo-scenario-validator, dependency-register, measurement-blueprint, methodology-compliance-check, phase-scope-extractor, readiness-scorecard, service-architecture-renderer, sop-definition-generator, vanilla-agent-test-harness, xla-designer

**Current BSA agents (to exclude from plugin):**
- ai-persona-architect, business-solution-architect, governance-reviewer, measurement-designer, methodology-architect, service-discovery-facilitator, v3-setup-orchestrator, sdlc-setup-specialist, sdlc-enforcer, critical-goal-reviewer, solution-architect, api-architect, ai-test-engineer, documentation-architect, pipeline-orchestrator, agent-builder, deep-research-agent, repo-knowledge-distiller

**Also exclude:**
- `.claude/agents/references/` (BSA methodology reference docs)
- `.claude/agents/TOOLKIT-REFERENCE.md`

**Solution:**
- Plugin ships ONLY the 17 presentation skills + 8 presentation agents
- BSA artifacts remain in the repo for project-internal use (they're installed via the ai-first-sdlc plugin anyway)
- CLAUDE.md for the plugin focuses solely on deck production

### 4.5 Ollama Skill Ownership

**Problem:** 4 Ollama image generation skills and 1 agent are referenced by the deck pipeline but currently marked as "upstream — do NOT fork." To ship a self-contained plugin, they need to be bundled.

**Skills to bring in-house:**
- `ollama-image` — local image generation with iterative refinement
- `ollama-icon` — local icon generation
- `ollama-pattern` — local texture/pattern generation
- `ollama-diagram` — local diagram generation (FLUX for text accuracy)
- `ollama-presentation` — meta-skill that orchestrates the above

**Agents to bring in-house:**
- `ollama-image-expert` — advisory domain knowledge agent

**These are Layer 0 components — zero internal dependencies.** They call Ollama's HTTP API directly via curl. Bringing them in-house means:
1. Copying the SKILL.md files to `skills/`
2. Copying the agent .md to `agents/`
3. Removing the "upstream — do NOT fork" restriction from CLAUDE.md
4. Adding tests for skill invocation patterns

**Risk:** Low. These skills are self-contained. The only concern is divergence from upstream improvements — but since we own the plugin, we control the update cycle.

---

## 5. Component Independence Matrix

| Component | Can stand alone? | Required for deck pipeline? | Dependencies |
|-----------|-----------------|---------------------------|--------------|
| ollama-image | Yes | Yes (draft tier) | Ollama binary |
| ollama-icon | Yes | Yes (icons) | Ollama binary |
| ollama-pattern | Yes | Yes (textures) | Ollama binary |
| ollama-diagram | Yes | Yes (diagrams) | Ollama binary |
| cloud-generate-image | Mostly* | Yes (production tier) | src/generate_cloud_image.py, src/provider_discovery.py |
| cloud-generate-icon | Mostly* | Yes (icons) | src/generate_cloud_icon.py, src/provider_discovery.py |
| brand-manager | No | Yes | src/brand_profile.py, src/deckcontext.py |
| slide-stylist | No | Yes | src/style_validation.py |
| narrative-architect | No | Yes | src/content_validation.py |
| strategy-map | No | Yes | src/slide_prompt_composer.py |
| smartart-selector | No | Yes | src/deckcontext.py |
| smartart-extractor | No | Yes | src/smartart_extractor.py |
| speaker-notes-writer | No | Yes | src/content_validation.py |
| imagegen-bridge | No | Yes | 8 src/ modules |
| smartart-renderer | No | Yes | src/smartart_renderer.py, smartart_svg/, smartart_pptx_native/ |
| deck-assembler | No | Yes | src/assembler/build_deck.js, node_modules/ |
| deck-qa | No | Yes | src/qa/ (all checks) |
| deck-conductor | No | Yes | src/conductor.py, invokes all skills |

*"Mostly standalone" means the skill itself just needs 2 Python files — could be made fully standalone with minimal inlining.

---

## 6. Migration Strategy

### Phase 1: Structural Reorganization (no behavior change)
1. Create `data/smartart_layouts/` and move fixtures
2. Create `.claude-plugin/plugin.json` and `marketplace.json`
3. Create `skills/` and `agents/` directories at repo root (plugin standard layout)
4. Copy presentation skills/agents to new locations
5. Keep `.claude/skills/` and `.claude/agents/` as symlinks for backward compatibility during transition
6. All tests must still pass

### Phase 2: Path Resolution
1. Create `bin/jt-run` helper script
2. Update all 14 skills to use `jt-run` instead of `source .venv/bin/activate && python3`
3. Update deck-conductor agent to use `jt-run`
4. Update deck-assembler to use resolved node path
5. Test from both repo-local and plugin-installed contexts

### Phase 3: Runtime Bootstrap
1. Create `hooks/post-install.sh`
2. Create `/jack-tar-setup` setup skill
3. Handle cross-platform venv creation
4. Handle npm install at plugin location
5. Test fresh install on clean machine

### Phase 4: Ollama Integration
1. Copy Ollama skills and agent into the plugin
2. Remove "upstream — do NOT fork" restriction
3. Verify standalone invocation still works
4. Add tests

### Phase 5: BSA Separation
1. Remove BSA skills/agents from plugin structure
2. Update CLAUDE.md for plugin context
3. Verify no deck pipeline skills reference BSA artifacts
4. Clean up agent references directory

### Phase 6: Polish & Publish
1. Write consumer-facing README
2. Create quick-start guide
3. Set up marketplace registration
4. Version as 1.0.0
5. Test installation from marketplace

---

## 7. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Plugin format changes before we ship | Medium | High | Track Claude Code changelog, follow superpowers patterns |
| Path resolution breaks on Windows | Medium | Medium | Use pathlib throughout, test on Windows CI |
| Large plugin size (~30MB with layouts) | Low | Low | XML fixtures compress well, marketplace may have size limits |
| Breaking backward compat for repo users | High | Medium | Dual-mode support in Phase 1, symlinks during transition |
| npm install reliability cross-platform | Medium | Medium | Pin versions, include lockfile, fallback instructions |
| Ollama skill divergence from community | Low | Low | We own the fork — update at our pace |

---

## 8. Size Estimate

| Component | Estimated Size |
|-----------|---------------|
| Python source (src/) | ~200KB |
| JS assembler | ~30KB |
| Node modules (installed) | ~15MB |
| SmartArt layout fixtures (29 × 4 XML) | ~2MB |
| Skills (17 SKILL.md files) | ~150KB |
| Agents (8 .md files) | ~80KB |
| Schemas (13 JSON) | ~40KB |
| **Total (source only)** | **~2.5MB** |
| **Total (with node_modules)** | **~17MB** |

---

## 9. Open Questions

1. **Does Claude Code expose `$PLUGIN_DIR` or similar?** If the platform provides the install path as an environment variable, path resolution becomes trivial. Need to check with the Claude Code team or inspect how superpowers handles this.

2. **Can plugins run post-install hooks?** The superpowers plugin has a `hooks/` directory — need to verify if Claude Code automatically runs `hooks/post-install.sh` or if users must run setup manually.

3. **Marketplace size limits?** If there's a cap, we may need to exclude node_modules and require `npm install` as a setup step.

4. **Multi-plugin from one repo?** The document-skills marketplace.json shows multiple plugins from one repo. Could we ship `jack-tar-deckhand` (full pipeline) and `jack-tar-image` (standalone Ollama/cloud skills) separately? Probably overkill for v1.

5. **Should cloud-generate-image/icon be made fully standalone?** Currently they depend on 2 Python files each. We could inline the generation logic to remove the dependency, making them usable without the full jack-tar runtime. Trade-off: code duplication vs independence.

---

## 10. Recommendation

Ship as a **single monolithic plugin** for v1. The full pipeline is tightly integrated — splitting it would create more complexity than it solves. The Ollama skills are standalone by nature and will work independently even within the monolith (users can invoke `/ollama-image` without running the deck pipeline).

Focus the first implementation sprint on:
1. **Path resolution** (Phase 2) — this is the highest-risk, most impactful work
2. **Fixture relocation** (Phase 1) — simple but blocks other work
3. **Plugin manifest** (Phase 1) — required for any plugin functionality

Defer marketplace publication until the plugin works reliably in local development mode (symlinked from `~/.claude/plugins/`).
