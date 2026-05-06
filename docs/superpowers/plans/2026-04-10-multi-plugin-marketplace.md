# Multi-Plugin Marketplace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert Jack-Tar Deckhand from a monolithic repo into a marketplace of 5 independent Claude Code plugins.

**Architecture:** One repo, one marketplace, five plugins (jack-tar-ollama, jack-tar-cloud, jack-tar-msft-smartart, jack-tar-custom-smartart, jack-tar-deckhand). Each plugin is independently installable and has a `:verify` skill. The deckhand orchestrator gracefully degrades based on which engine plugins are available.

**Tech Stack:** Python 3.10+, Node.js, Claude Code plugin format (.claude-plugin/plugin.json, marketplace.json), PptxGenJS, Ollama, cloud APIs (OpenAI, Google, FAL, Recraft)

**Spec:** `docs/superpowers/specs/2026-04-10-multi-plugin-marketplace-design.md`

**EPIC:** [#40](https://github.com/SteveGJones/jack-tar-deckhand/issues/40)

---

## Master Phase Overview

This plan is structured in 7 phases. Each phase produces a working, testable state. Phases 1-3 are detailed below with step-level granularity. Phases 4-7 are outlined at task level and will be expanded into their own detailed plans when reached.

| Phase | What | Depends on | Est. tasks |
|-------|------|-----------|------------|
| 1 | Scaffold plugin directories | Nothing | 6 |
| 2 | Copy source into plugins + verify skills | Phase 1 | 15 |
| 3 | Migrate Ollama from external repo | Phase 1 | 5 |
| 4 | Rewrite skill Python invocations | Phases 2-3 | ~15 |
| 5 | Cross-plugin integration testing | Phase 4 | ~8 |
| 6 | Remove legacy structure | Phase 5 | ~6 |
| 7 | Polish and publish | Phase 6 | ~8 |

**Phases 2 and 3 can run in parallel** — they both depend only on Phase 1.

---

## Phase 1: Scaffold Plugin Directories

**Goal:** Create the marketplace structure and plugin.json for all 5 plugins. No code moves. Existing tests unaffected.

### Task 1.1: Create marketplace.json

**Files:**
- Create: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Create the .claude-plugin directory and marketplace.json**

```bash
mkdir -p .claude-plugin
```

Write `.claude-plugin/marketplace.json`:

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

- [ ] **Step 2: Verify existing tests still pass**

Run: `.venv/bin/pytest tests/ -x -q`
Expected: 952 tests pass, 0 fail

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat: add marketplace.json declaring 5 jack-tar plugins"
```

---

### Task 1.2: Scaffold jack-tar-ollama plugin

**Files:**
- Create: `plugins/jack-tar-ollama/.claude-plugin/plugin.json`
- Create: `plugins/jack-tar-ollama/CLAUDE.md`
- Create: `plugins/jack-tar-ollama/requirements.txt`
- Create: `plugins/jack-tar-ollama/package.json`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p plugins/jack-tar-ollama/.claude-plugin
mkdir -p plugins/jack-tar-ollama/skills
mkdir -p plugins/jack-tar-ollama/agents
mkdir -p plugins/jack-tar-ollama/src
mkdir -p plugins/jack-tar-ollama/tests
```

- [ ] **Step 2: Write plugin.json**

Write `plugins/jack-tar-ollama/.claude-plugin/plugin.json`:

```json
{
  "name": "jack-tar-ollama",
  "description": "Local AI image generation via Ollama — images, icons, patterns, diagrams, and quick presentations",
  "version": "1.0.0",
  "author": {
    "name": "Steve Jones"
  },
  "repository": "https://github.com/SteveGJones/jack-tar-deckhand",
  "license": "MIT",
  "keywords": ["ollama", "image-generation", "local-ai", "icons", "patterns", "diagrams"]
}
```

- [ ] **Step 3: Write CLAUDE.md**

Write `plugins/jack-tar-ollama/CLAUDE.md`:

```markdown
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

## Quick Start

```
/jack-tar-ollama:verify
/jack-tar-ollama:image "a lighthouse at sunset, dramatic clouds"
```
```

- [ ] **Step 4: Write requirements.txt**

Write `plugins/jack-tar-ollama/requirements.txt`:

```
requests>=2.31.0
```

- [ ] **Step 5: Write package.json**

Write `plugins/jack-tar-ollama/package.json`:

```json
{
  "name": "jack-tar-ollama",
  "version": "1.0.0",
  "description": "Local AI image generation via Ollama",
  "license": "MIT",
  "dependencies": {
    "pptxgenjs": "^4.0.1"
  }
}
```

- [ ] **Step 6: Commit**

```bash
git add plugins/jack-tar-ollama/
git commit -m "feat: scaffold jack-tar-ollama plugin directory"
```

---

### Task 1.3: Scaffold jack-tar-cloud plugin

**Files:**
- Create: `plugins/jack-tar-cloud/.claude-plugin/plugin.json`
- Create: `plugins/jack-tar-cloud/CLAUDE.md`
- Create: `plugins/jack-tar-cloud/requirements.txt`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p plugins/jack-tar-cloud/.claude-plugin
mkdir -p plugins/jack-tar-cloud/skills
mkdir -p plugins/jack-tar-cloud/agents
mkdir -p plugins/jack-tar-cloud/src
```

- [ ] **Step 2: Write plugin.json**

Write `plugins/jack-tar-cloud/.claude-plugin/plugin.json`:

```json
{
  "name": "jack-tar-cloud",
  "description": "Cloud AI image generation — OpenAI, Google, FAL.ai, Recraft with smart provider routing",
  "version": "1.0.0",
  "author": {
    "name": "Steve Jones"
  },
  "repository": "https://github.com/SteveGJones/jack-tar-deckhand",
  "license": "MIT",
  "keywords": ["cloud", "image-generation", "openai", "google", "fal", "recraft", "icons"]
}
```

- [ ] **Step 3: Write CLAUDE.md**

Write `plugins/jack-tar-cloud/CLAUDE.md`:

```markdown
# jack-tar-cloud

Cloud AI image generation using OpenAI, Google, FAL.ai, and Recraft APIs. Per-provider skills for targeted use, plus smart router skills that pick the best available provider.

## Prerequisites

At least one API key configured:
- `OPENAI_API_KEY` — for OpenAI GPT Image and Recraft V4 icons
- `GOOGLE_CLOUD_PROJECT` — for Google Gemini/Imagen
- `FAL_KEY` — for FAL.ai FLUX Pro/Klein/Ideogram

## Skills

| Skill | Purpose |
|-------|---------|
| `/openai-image` | Generate via OpenAI GPT Image |
| `/google-image` | Generate via Google Gemini/Imagen |
| `/fal-image` | Generate via FAL.ai FLUX |
| `/recraft-icon` | Generate SVG vector icons via Recraft V4 |
| `/image` | Smart router — picks best available provider |
| `/icon` | Smart router for icons — tries Recraft first |
| `/verify` | Check which providers are configured and reachable |

## Quick Start

```
/jack-tar-cloud:verify
/jack-tar-cloud:image "a lighthouse at sunset, dramatic clouds"
```
```

- [ ] **Step 4: Write requirements.txt**

Write `plugins/jack-tar-cloud/requirements.txt`:

```
requests>=2.31.0
openai>=1.0.0
google-genai>=1.0.0
fal-client>=0.4.0
```

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-cloud/
git commit -m "feat: scaffold jack-tar-cloud plugin directory"
```

---

### Task 1.4: Scaffold jack-tar-msft-smartart plugin

**Files:**
- Create: `plugins/jack-tar-msft-smartart/.claude-plugin/plugin.json`
- Create: `plugins/jack-tar-msft-smartart/CLAUDE.md`
- Create: `plugins/jack-tar-msft-smartart/requirements.txt`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p plugins/jack-tar-msft-smartart/.claude-plugin
mkdir -p plugins/jack-tar-msft-smartart/skills
mkdir -p plugins/jack-tar-msft-smartart/src/builders
mkdir -p plugins/jack-tar-msft-smartart/src/layouts
mkdir -p plugins/jack-tar-msft-smartart/data/smartart_layouts
mkdir -p plugins/jack-tar-msft-smartart/tools
mkdir -p plugins/jack-tar-msft-smartart/tests
mkdir -p plugins/jack-tar-msft-smartart/docs
```

- [ ] **Step 2: Write plugin.json**

Write `plugins/jack-tar-msft-smartart/.claude-plugin/plugin.json`:

```json
{
  "name": "jack-tar-msft-smartart",
  "description": "Editable PowerPoint SmartArt graphics — 29 layouts, speakers can modify after delivery",
  "version": "1.0.0",
  "author": {
    "name": "Steve Jones"
  },
  "repository": "https://github.com/SteveGJones/jack-tar-deckhand",
  "license": "MIT",
  "keywords": ["smartart", "powerpoint", "editable", "ooxml", "presentations"]
}
```

- [ ] **Step 3: Write CLAUDE.md**

Write `plugins/jack-tar-msft-smartart/CLAUDE.md`:

```markdown
# jack-tar-msft-smartart

Editable PowerPoint SmartArt graphics using native OOXML. Produces SmartArt that speakers can modify — rename nodes, switch layouts, insert images — directly in PowerPoint after delivery.

29 layouts across 9 categories, all MIT-sourced from dotnet/Open-XML-SDK.

## Prerequisites

- Python 3.10+ with python-pptx and lxml

## Skills

| Skill | Purpose |
|-------|---------|
| `/render` | Generate editable SmartArt carrier .pptx from a spec |
| `/inject` | Graft SmartArt from carriers into an assembled deck |
| `/catalog` | List available layouts with capacity and guidance |
| `/verify` | Check dependencies and layout fixture availability |

## Quick Start

```
/jack-tar-msft-smartart:verify
/jack-tar-msft-smartart:catalog
```
```

- [ ] **Step 4: Write requirements.txt**

Write `plugins/jack-tar-msft-smartart/requirements.txt`:

```
python-pptx>=1.0.0
lxml>=4.9.0
jsonschema>=4.20.0
```

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-msft-smartart/
git commit -m "feat: scaffold jack-tar-msft-smartart plugin directory"
```

---

### Task 1.5: Scaffold jack-tar-custom-smartart plugin

**Files:**
- Create: `plugins/jack-tar-custom-smartart/.claude-plugin/plugin.json`
- Create: `plugins/jack-tar-custom-smartart/CLAUDE.md`
- Create: `plugins/jack-tar-custom-smartart/requirements.txt`
- Create: `plugins/jack-tar-custom-smartart/package.json`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p plugins/jack-tar-custom-smartart/.claude-plugin
mkdir -p plugins/jack-tar-custom-smartart/skills
mkdir -p plugins/jack-tar-custom-smartart/src/smartart_svg/layouts
```

- [ ] **Step 2: Write plugin.json**

Write `plugins/jack-tar-custom-smartart/.claude-plugin/plugin.json`:

```json
{
  "name": "jack-tar-custom-smartart",
  "description": "Data visualisation and custom graphics — SVG, Mermaid, Vega-Lite, matplotlib charts",
  "version": "1.0.0",
  "author": {
    "name": "Steve Jones"
  },
  "repository": "https://github.com/SteveGJones/jack-tar-deckhand",
  "license": "MIT",
  "keywords": ["smartart", "svg", "mermaid", "vega-lite", "charts", "data-viz"]
}
```

- [ ] **Step 3: Write CLAUDE.md**

Write `plugins/jack-tar-custom-smartart/CLAUDE.md`:

```markdown
# jack-tar-custom-smartart

Data visualisation and custom graphics using SVG, Mermaid, Vega-Lite, and matplotlib. Produces rasterised PNGs for embedding into slides.

9 custom SVG layouts: flowchart, decision tree, timeline, Venn, SWOT, feature matrix, pipeline/funnel, radar chart, Gantt.

## Prerequisites

- Python 3.10+ with matplotlib, seaborn, Pillow
- Node.js with @mermaid-js/mermaid-cli, vega-cli, vega-lite
- Optional: cairosvg (for high-quality SVG rasterisation)

## Skills

| Skill | Purpose |
|-------|---------|
| `/render` | Render a graphic to PNG using the appropriate engine |
| `/chart` | Render a data chart (bar, line, pie, scatter, radar, etc.) |
| `/verify` | Check which rendering engines are available |

## Quick Start

```
/jack-tar-custom-smartart:verify
```
```

- [ ] **Step 4: Write requirements.txt and package.json**

Write `plugins/jack-tar-custom-smartart/requirements.txt`:

```
matplotlib>=3.8.0
seaborn>=0.13.0
Pillow>=10.0.0
```

Write `plugins/jack-tar-custom-smartart/package.json`:

```json
{
  "name": "jack-tar-custom-smartart",
  "version": "1.0.0",
  "description": "Custom SmartArt graphics — SVG, Mermaid, Vega-Lite, charts",
  "license": "MIT",
  "dependencies": {
    "@mermaid-js/mermaid-cli": "^11.12.0",
    "vega": "^6.2.0",
    "vega-cli": "^6.2.0",
    "vega-lite": "^6.4.2"
  }
}
```

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-custom-smartart/
git commit -m "feat: scaffold jack-tar-custom-smartart plugin directory"
```

---

### Task 1.6: Scaffold jack-tar-deckhand plugin

**Files:**
- Create: `plugins/jack-tar-deckhand/.claude-plugin/plugin.json`
- Create: `plugins/jack-tar-deckhand/CLAUDE.md`
- Create: `plugins/jack-tar-deckhand/requirements.txt`
- Create: `plugins/jack-tar-deckhand/package.json`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p plugins/jack-tar-deckhand/.claude-plugin
mkdir -p plugins/jack-tar-deckhand/skills
mkdir -p plugins/jack-tar-deckhand/agents
mkdir -p plugins/jack-tar-deckhand/src/schemas
mkdir -p plugins/jack-tar-deckhand/src/assembler
mkdir -p plugins/jack-tar-deckhand/src/qa/checks
```

- [ ] **Step 2: Write plugin.json**

Write `plugins/jack-tar-deckhand/.claude-plugin/plugin.json`:

```json
{
  "name": "jack-tar-deckhand",
  "description": "Full presentation pipeline — brand, style, narrative, images, SmartArt, assembly, QA",
  "version": "1.0.0",
  "author": {
    "name": "Steve Jones"
  },
  "repository": "https://github.com/SteveGJones/jack-tar-deckhand",
  "license": "MIT",
  "keywords": ["presentations", "powerpoint", "pptx", "conference", "pipeline", "orchestration"]
}
```

- [ ] **Step 3: Write CLAUDE.md**

Write `plugins/jack-tar-deckhand/CLAUDE.md`:

```markdown
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
| `/deck-assembler` | Assemble .pptx from all contracts |
| `/deck-qa` | Run 30 anti-pattern checks |
| `/verify` | Check pipeline readiness and engine plugin availability |

## Quick Start

```
/jack-tar-deckhand:verify
```

Then use the deck-conductor agent to orchestrate a full deck build.
```

- [ ] **Step 4: Write requirements.txt and package.json**

Write `plugins/jack-tar-deckhand/requirements.txt`:

```
jsonschema>=4.20.0
Pillow>=10.0.0
requests>=2.31.0
python-pptx>=1.0.0
lxml>=4.9.0
```

Write `plugins/jack-tar-deckhand/package.json`:

```json
{
  "name": "jack-tar-deckhand",
  "version": "1.0.0",
  "description": "Full presentation engineering pipeline",
  "license": "MIT",
  "dependencies": {
    "pptxgenjs": "^4.0.1"
  }
}
```

- [ ] **Step 5: Verify existing tests still pass**

Run: `.venv/bin/pytest tests/ -x -q`
Expected: 952 tests pass (scaffolding changed nothing functional)

- [ ] **Step 6: Commit**

```bash
git add plugins/jack-tar-deckhand/
git commit -m "feat: scaffold jack-tar-deckhand plugin directory"
```

---

## Phase 2: Copy Source Into Plugins

**Goal:** Copy source files into their target plugin directories, adapt internal imports, write verify skills. Original files remain — both structures coexist. Each plugin gets new tests proving its modules load and basic operations work from the plugin directory.

**Phases 2 and 3 can run in parallel** — they are independent.

### Task 2.1: Copy cloud source into jack-tar-cloud

**Files:**
- Copy: `src/generate_cloud_image.py` -> `plugins/jack-tar-cloud/src/generate_cloud_image.py`
- Copy: `src/generate_cloud_icon.py` -> `plugins/jack-tar-cloud/src/generate_cloud_icon.py`
- Copy: `src/provider_discovery.py` -> `plugins/jack-tar-cloud/src/provider_discovery.py`
- Copy: `src/prompt_translator.py` -> `plugins/jack-tar-cloud/src/prompt_translator.py`
- Create: `plugins/jack-tar-cloud/src/__init__.py`
- Create: `plugins/jack-tar-cloud/tests/test_plugin_imports.py`

- [ ] **Step 1: Copy source files**

```bash
cp src/generate_cloud_image.py plugins/jack-tar-cloud/src/
cp src/generate_cloud_icon.py plugins/jack-tar-cloud/src/
cp src/provider_discovery.py plugins/jack-tar-cloud/src/
cp src/prompt_translator.py plugins/jack-tar-cloud/src/
touch plugins/jack-tar-cloud/src/__init__.py
```

- [ ] **Step 2: Write import verification test**

Write `plugins/jack-tar-cloud/tests/test_plugin_imports.py`:

```python
"""Verify jack-tar-cloud modules load from plugin directory."""
import sys
from pathlib import Path

# Inject plugin root into sys.path
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))


def test_provider_discovery_imports():
    from src.provider_discovery import discover_providers
    assert callable(discover_providers)


def test_prompt_translator_imports():
    from src.prompt_translator import translate_prompt
    assert callable(translate_prompt)


def test_generate_cloud_image_imports():
    from src.generate_cloud_image import generate_cloud_image
    assert callable(generate_cloud_image)


def test_generate_cloud_icon_imports():
    from src.generate_cloud_icon import generate_cloud_icon
    assert callable(generate_cloud_icon)
```

- [ ] **Step 3: Run plugin import tests**

Run: `.venv/bin/pytest plugins/jack-tar-cloud/tests/test_plugin_imports.py -v`
Expected: 4 tests pass

- [ ] **Step 4: Verify original tests still pass**

Run: `.venv/bin/pytest tests/ -x -q`
Expected: 952 tests pass

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-cloud/
git commit -m "feat(jack-tar-cloud): copy source modules into plugin directory"
```

---

### Task 2.2: Copy msft-smartart source into jack-tar-msft-smartart

**Files:**
- Copy: `src/smartart_pptx_native/` -> `plugins/jack-tar-msft-smartart/src/` (all .py files preserving subdir structure)
- Copy: `tests/fixtures/smartart_layouts/` -> `plugins/jack-tar-msft-smartart/data/smartart_layouts/`
- Copy: `tools/extract_smartart_layouts.py` -> `plugins/jack-tar-msft-smartart/tools/`
- Copy: `docs/pptx-native-smartart-catalog.md` -> `plugins/jack-tar-msft-smartart/docs/`
- Create: `plugins/jack-tar-msft-smartart/tests/test_plugin_imports.py`

- [ ] **Step 1: Copy source files**

```bash
cp src/smartart_pptx_native/__init__.py plugins/jack-tar-msft-smartart/src/
cp src/smartart_pptx_native/engine.py plugins/jack-tar-msft-smartart/src/
cp src/smartart_pptx_native/data_model.py plugins/jack-tar-msft-smartart/src/
cp src/smartart_pptx_native/assembler_patch.py plugins/jack-tar-msft-smartart/src/
cp src/smartart_pptx_native/pipeline.py plugins/jack-tar-msft-smartart/src/
cp src/smartart_pptx_native/selector_integration.py plugins/jack-tar-msft-smartart/src/
cp -r src/smartart_pptx_native/builders/ plugins/jack-tar-msft-smartart/src/builders/
cp -r src/smartart_pptx_native/layouts/ plugins/jack-tar-msft-smartart/src/layouts/
```

- [ ] **Step 2: Copy layout fixtures and tools**

```bash
cp -r tests/fixtures/smartart_layouts/* plugins/jack-tar-msft-smartart/data/smartart_layouts/
cp tests/fixtures/smartart_layouts/_extraction_manifest.json plugins/jack-tar-msft-smartart/data/smartart_layouts/
cp tests/fixtures/smartart_layouts/LICENSING.md plugins/jack-tar-msft-smartart/data/smartart_layouts/
cp tools/extract_smartart_layouts.py plugins/jack-tar-msft-smartart/tools/
cp docs/pptx-native-smartart-catalog.md plugins/jack-tar-msft-smartart/docs/
```

- [ ] **Step 3: Update catalog.json layout_dir paths**

In `plugins/jack-tar-msft-smartart/src/layouts/catalog.json`, replace all occurrences of `tests/fixtures/smartart_layouts/` with `data/smartart_layouts/`:

Search: `"layout_dir": "tests/fixtures/smartart_layouts/`
Replace: `"layout_dir": "data/smartart_layouts/`

- [ ] **Step 4: Update catalog.py REPO_ROOT**

In `plugins/jack-tar-msft-smartart/src/layouts/catalog.py`, update the REPO_ROOT calculation. The file is now at `plugins/jack-tar-msft-smartart/src/layouts/catalog.py` — the plugin root is 2 levels up from this file (src/layouts/catalog.py -> plugin root):

Change line 28 from:
```python
REPO_ROOT = Path(__file__).resolve().parents[3]
```
To:
```python
REPO_ROOT = Path(__file__).resolve().parents[2]
```

- [ ] **Step 5: Write import verification test**

Write `plugins/jack-tar-msft-smartart/tests/test_plugin_imports.py`:

```python
"""Verify jack-tar-msft-smartart modules load from plugin directory."""
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))


def test_engine_imports():
    from src.engine import render
    assert callable(render)


def test_data_model_imports():
    from src.data_model import make_node_pt, wrap_data_model
    assert callable(make_node_pt)
    assert callable(wrap_data_model)


def test_catalog_loads():
    from src.layouts.catalog import load_catalog, get_entry
    catalog = load_catalog()
    assert len(catalog["entries"]) >= 27
    entry = get_entry("process1")
    assert entry["id"] == "process1"


def test_layout_fixtures_present():
    from src.layouts.catalog import load_catalog, resolve_layout_dir
    catalog = load_catalog()
    for entry in catalog["entries"]:
        layout_dir = resolve_layout_dir(entry)
        assert layout_dir.exists(), f"Missing layout dir: {layout_dir}"
        assert (layout_dir / "layout.xml").exists(), f"Missing layout.xml in {layout_dir}"


def test_flat_list_builder_imports():
    from src.builders.flat_list import build
    assert callable(build)


def test_hierarchical_builder_imports():
    from src.builders.hierarchical import build
    assert callable(build)


def test_assembler_patch_imports():
    from src.assembler_patch import inject
    assert callable(inject)
```

- [ ] **Step 6: Run plugin import tests**

Run: `.venv/bin/pytest plugins/jack-tar-msft-smartart/tests/test_plugin_imports.py -v`
Expected: 7 tests pass

- [ ] **Step 7: Verify original tests still pass**

Run: `.venv/bin/pytest tests/ -x -q`
Expected: 952 tests pass

- [ ] **Step 8: Commit**

```bash
git add plugins/jack-tar-msft-smartart/
git commit -m "feat(jack-tar-msft-smartart): copy source, fixtures, and catalog into plugin directory"
```

---

### Task 2.3: Copy custom-smartart source into jack-tar-custom-smartart

**Files:**
- Copy: `src/smartart_svg/` -> `plugins/jack-tar-custom-smartart/src/smartart_svg/`
- Copy: `src/smartart_renderer.py` -> `plugins/jack-tar-custom-smartart/src/smartart_renderer.py`
- Copy: `src/render_chart.py` -> `plugins/jack-tar-custom-smartart/src/render_chart.py`
- Create: `plugins/jack-tar-custom-smartart/src/__init__.py`
- Create: `plugins/jack-tar-custom-smartart/tests/test_plugin_imports.py`

- [ ] **Step 1: Copy source files**

```bash
cp -r src/smartart_svg/ plugins/jack-tar-custom-smartart/src/smartart_svg/
cp src/smartart_renderer.py plugins/jack-tar-custom-smartart/src/
cp src/render_chart.py plugins/jack-tar-custom-smartart/src/
touch plugins/jack-tar-custom-smartart/src/__init__.py
```

- [ ] **Step 2: Remove pptx_native dispatch from plugin's smartart_renderer.py**

In `plugins/jack-tar-custom-smartart/src/smartart_renderer.py`, remove the import of `src.smartart_pptx_native` and the `pptx_native` entry from `_ENGINE_DISPATCH`. This plugin only dispatches to engines it owns (mermaid, vega, custom_svg, matplotlib).

Remove the line:
```python
from src.smartart_pptx_native.engine import render as pptx_native_render
```

And remove `'pptx_native'` from the `_ENGINE_DISPATCH` dict if it exists.

- [ ] **Step 3: Write import verification test**

Write `plugins/jack-tar-custom-smartart/tests/test_plugin_imports.py`:

```python
"""Verify jack-tar-custom-smartart modules load from plugin directory."""
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))


def test_smartart_svg_engine_imports():
    from src.smartart_svg.engine import Container
    assert Container is not None


def test_smartart_svg_primitives_imports():
    from src.smartart_svg.primitives import svg_rect, svg_text
    assert callable(svg_rect)
    assert callable(svg_text)


def test_smartart_svg_tokens_imports():
    from src.smartart_svg.tokens import extract_style_tokens
    assert callable(extract_style_tokens)


def test_all_svg_layouts_import():
    from src.smartart_svg.layouts import flowchart, decision_tree, timeline
    from src.smartart_svg.layouts import venn, swot, feature_matrix
    from src.smartart_svg.layouts import pipeline_funnel, radar_chart, gantt
    assert flowchart is not None
    assert gantt is not None


def test_render_chart_imports():
    from src.render_chart import render_chart
    assert callable(render_chart)


def test_smartart_renderer_imports():
    from src.smartart_renderer import render
    assert callable(render)
```

- [ ] **Step 4: Run plugin import tests**

Run: `.venv/bin/pytest plugins/jack-tar-custom-smartart/tests/test_plugin_imports.py -v`
Expected: 6 tests pass

- [ ] **Step 5: Verify original tests still pass**

Run: `.venv/bin/pytest tests/ -x -q`
Expected: 952 tests pass

- [ ] **Step 6: Commit**

```bash
git add plugins/jack-tar-custom-smartart/
git commit -m "feat(jack-tar-custom-smartart): copy SVG engine, chart renderer, and dispatcher into plugin"
```

---

### Task 2.4: Copy deckhand source into jack-tar-deckhand

**Files:**
- Copy: pipeline/DeckContext modules -> `plugins/jack-tar-deckhand/src/`
- Copy: schemas -> `plugins/jack-tar-deckhand/src/schemas/`
- Copy: assembler -> `plugins/jack-tar-deckhand/src/assembler/`
- Copy: qa -> `plugins/jack-tar-deckhand/src/qa/`
- Create: `plugins/jack-tar-deckhand/tests/test_plugin_imports.py`

- [ ] **Step 1: Copy core pipeline modules**

```bash
cp src/__init__.py plugins/jack-tar-deckhand/src/
cp src/deckcontext.py plugins/jack-tar-deckhand/src/
cp src/conductor.py plugins/jack-tar-deckhand/src/
cp src/budget_tracker.py plugins/jack-tar-deckhand/src/
cp src/slide_prompt_composer.py plugins/jack-tar-deckhand/src/
cp src/render_funnel.py plugins/jack-tar-deckhand/src/
cp src/image_router.py plugins/jack-tar-deckhand/src/
cp src/brand_profile.py plugins/jack-tar-deckhand/src/
cp src/style_validation.py plugins/jack-tar-deckhand/src/
cp src/content_validation.py plugins/jack-tar-deckhand/src/
cp src/process_image.py plugins/jack-tar-deckhand/src/
cp src/cache_manager.py plugins/jack-tar-deckhand/src/
cp src/manifest_utils.py plugins/jack-tar-deckhand/src/
cp src/smartart_extractor.py plugins/jack-tar-deckhand/src/
```

- [ ] **Step 2: Copy schemas**

```bash
cp src/schemas/__init__.py plugins/jack-tar-deckhand/src/schemas/
cp src/schemas/*.schema.json plugins/jack-tar-deckhand/src/schemas/
```

- [ ] **Step 3: Copy assembler**

```bash
cp src/assembler/build_deck.js plugins/jack-tar-deckhand/src/assembler/
cp src/assembler/optimise.js plugins/jack-tar-deckhand/src/assembler/
cp src/assembler/progressive_builds.js plugins/jack-tar-deckhand/src/assembler/
cp src/assembler/slide_masters.js plugins/jack-tar-deckhand/src/assembler/
```

- [ ] **Step 4: Copy QA module**

```bash
cp src/qa/__init__.py plugins/jack-tar-deckhand/src/qa/
cp src/qa/config.py plugins/jack-tar-deckhand/src/qa/
cp src/qa/report.py plugins/jack-tar-deckhand/src/qa/
cp src/qa/run_qa.py plugins/jack-tar-deckhand/src/qa/
cp src/qa/checks/__init__.py plugins/jack-tar-deckhand/src/qa/checks/
cp src/qa/checks/animations.py plugins/jack-tar-deckhand/src/qa/checks/
cp src/qa/checks/chart_quality.py plugins/jack-tar-deckhand/src/qa/checks/
cp src/qa/checks/consistency.py plugins/jack-tar-deckhand/src/qa/checks/
cp src/qa/checks/contrast.py plugins/jack-tar-deckhand/src/qa/checks/
cp src/qa/checks/element_layout.py plugins/jack-tar-deckhand/src/qa/checks/
cp src/qa/checks/image_quality.py plugins/jack-tar-deckhand/src/qa/checks/
cp src/qa/checks/keynote_checks.py plugins/jack-tar-deckhand/src/qa/checks/
cp src/qa/checks/smartart_checks.py plugins/jack-tar-deckhand/src/qa/checks/
cp src/qa/checks/structural.py plugins/jack-tar-deckhand/src/qa/checks/
cp src/qa/checks/visual_inspection.py plugins/jack-tar-deckhand/src/qa/checks/
```

- [ ] **Step 5: Write import verification test**

Write `plugins/jack-tar-deckhand/tests/test_plugin_imports.py`:

```python
"""Verify jack-tar-deckhand modules load from plugin directory."""
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))


def test_deckcontext_imports():
    from src.deckcontext import init_deck, write_contract, read_contract
    assert callable(init_deck)


def test_conductor_imports():
    from src.conductor import init_pipeline, pipeline_summary_markdown
    assert callable(init_pipeline)


def test_budget_tracker_imports():
    from src.budget_tracker import BudgetTracker
    assert BudgetTracker is not None


def test_schemas_exist():
    schemas_dir = PLUGIN_ROOT / "src" / "schemas"
    schema_files = list(schemas_dir.glob("*.schema.json"))
    assert len(schema_files) >= 13, f"Expected 13+ schemas, found {len(schema_files)}"


def test_image_router_imports():
    from src.image_router import route_all_slides
    assert callable(route_all_slides)


def test_qa_run_imports():
    from src.qa.run_qa import run_qa
    assert callable(run_qa)


def test_brand_profile_imports():
    from src.brand_profile import load_brand_profile, save_brand_profile
    assert callable(load_brand_profile)


def test_content_validation_imports():
    from src.content_validation import validate_outline_schema
    assert callable(validate_outline_schema)
```

- [ ] **Step 6: Run plugin import tests**

Run: `.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_plugin_imports.py -v`
Expected: 8 tests pass

- [ ] **Step 7: Verify original tests still pass**

Run: `.venv/bin/pytest tests/ -x -q`
Expected: 952 tests pass

- [ ] **Step 8: Commit**

```bash
git add plugins/jack-tar-deckhand/
git commit -m "feat(jack-tar-deckhand): copy pipeline, schemas, assembler, and QA into plugin directory"
```

---

### Task 2.5: Write jack-tar-ollama:verify skill

**Files:**
- Create: `plugins/jack-tar-ollama/skills/verify/SKILL.md`

- [ ] **Step 1: Write the verify skill**

Write `plugins/jack-tar-ollama/skills/verify/SKILL.md`:

```markdown
---
name: verify
description: Check Ollama availability, list installed image generation models, and report readiness status.
allowed-tools: Bash(curl *), Bash(ollama *)
---

# /verify

Check whether this plugin's prerequisites are met and report readiness.

## Step 1: Check Ollama is running

```bash
curl -s http://localhost:11434/api/tags 2>/dev/null | head -c 1
```

If the curl fails or returns empty, report:

```
PLUGIN: jack-tar-ollama
VERSION: 1.0.0

DEPENDENCIES:
  Ollama:          NOT_READY (Ollama is not running — start with 'ollama serve')

STATUS: NOT_AVAILABLE
REASON: Ollama is not running
```

## Step 2: List available image models

```bash
ollama list 2>/dev/null | grep '^x/' | awk '{print $1}'
```

Collect the list of `x/` prefixed models. These are image generation models.

## Step 3: Report status

If Ollama is running but no `x/` models are found:

```
PLUGIN: jack-tar-ollama
VERSION: 1.0.0

DEPENDENCIES:
  Ollama:          READY (running)

MODELS:
  (none found)     NOT_READY (no x/ image models installed — try 'ollama pull x/z-image-turbo')

STATUS: NOT_AVAILABLE
REASON: No image generation models installed
```

If Ollama is running and models are found, list each one:

```
PLUGIN: jack-tar-ollama
VERSION: 1.0.0

DEPENDENCIES:
  Ollama:          READY (running)

MODELS:
  x/z-image-turbo: READY
  x/flux2-klein:   READY

CAPABILITIES:
  image:           READY
  icon:            READY
  pattern:         READY
  diagram:         READY
  presentation:    READY

STATUS: FULLY_AVAILABLE
REASON: Ollama running with N image model(s) available
```
```

- [ ] **Step 2: Commit**

```bash
git add plugins/jack-tar-ollama/skills/verify/
git commit -m "feat(jack-tar-ollama): add verify skill"
```

---

### Task 2.6: Write jack-tar-cloud:verify skill

**Files:**
- Create: `plugins/jack-tar-cloud/skills/verify/SKILL.md`

- [ ] **Step 1: Write the verify skill**

Write `plugins/jack-tar-cloud/skills/verify/SKILL.md`:

```markdown
---
name: verify
description: Check which cloud image providers are configured and report readiness status.
allowed-tools: Bash(python *)
---

# /verify

Check whether this plugin's prerequisites are met and report per-provider readiness.

## Step 1: Check Python dependencies

```bash
python3 -c "
missing = []
try:
    import requests
except ImportError:
    missing.append('requests')
try:
    import openai
except ImportError:
    missing.append('openai')
try:
    from google import genai
except ImportError:
    missing.append('google-genai')
try:
    import fal_client
except ImportError:
    missing.append('fal-client')
if missing:
    print('MISSING:' + ','.join(missing))
else:
    print('ALL_PRESENT')
"
```

If any packages are missing, report NOT_AVAILABLE with install instructions.

## Step 2: Check provider API keys

```bash
python3 -c "
import os
providers = {
    'openai': bool(os.environ.get('OPENAI_API_KEY')),
    'google': bool(os.environ.get('GOOGLE_CLOUD_PROJECT')),
    'fal': bool(os.environ.get('FAL_KEY')),
}
# Recraft uses OPENAI_API_KEY
providers['recraft'] = providers['openai']
import json
print(json.dumps(providers))
"
```

## Step 3: Report status

Count ready providers. If 0, status is NOT_AVAILABLE. If some but not all, PARTIALLY_AVAILABLE. If all, FULLY_AVAILABLE.

```
PLUGIN: jack-tar-cloud
VERSION: 1.0.0

DEPENDENCIES:
  Python:          READY (3.12.x)
  requests:        READY
  openai:          READY
  google-genai:    READY
  fal-client:      READY

PROVIDERS:
  openai:          READY (OPENAI_API_KEY set)
  google:          NOT_READY (GOOGLE_CLOUD_PROJECT not set)
  fal:             READY (FAL_KEY set)
  recraft:         READY (uses OPENAI_API_KEY)

CAPABILITIES:
  image:           READY (3/4 providers available)
  icon:            READY (recraft available)

STATUS: PARTIALLY_AVAILABLE
REASON: Google provider not configured (missing GOOGLE_CLOUD_PROJECT)
```
```

- [ ] **Step 2: Commit**

```bash
git add plugins/jack-tar-cloud/skills/verify/
git commit -m "feat(jack-tar-cloud): add verify skill"
```

---

### Task 2.7: Write jack-tar-msft-smartart:verify skill

**Files:**
- Create: `plugins/jack-tar-msft-smartart/skills/verify/SKILL.md`

- [ ] **Step 1: Write the verify skill**

Write `plugins/jack-tar-msft-smartart/skills/verify/SKILL.md`:

```markdown
---
name: verify
description: Check python-pptx, lxml, layout fixtures, and test carrier build capability.
allowed-tools: Bash(python *)
---

# /verify

Check whether this plugin's prerequisites are met and report readiness.

## Step 1: Check Python dependencies

```bash
python3 -c "
import json
deps = {}
try:
    import pptx; deps['python-pptx'] = pptx.__version__
except Exception: deps['python-pptx'] = None
try:
    import lxml.etree; deps['lxml'] = lxml.etree.__version__
except Exception: deps['lxml'] = None
try:
    import jsonschema; deps['jsonschema'] = jsonschema.__version__
except Exception: deps['jsonschema'] = None
print(json.dumps(deps))
"
```

## Step 2: Check layout fixtures

Count how many layout directories exist under `data/smartart_layouts/` in the plugin directory. Each should contain `layout.xml`, `quickStyle.xml`, `colors.xml`, and `meta.json`.

## Step 3: Test carrier build

Attempt to render a minimal process1 SmartArt carrier to a temp directory. If the render succeeds and produces a valid .pptx, the engine is working.

## Step 4: Report status

```
PLUGIN: jack-tar-msft-smartart
VERSION: 1.0.0

DEPENDENCIES:
  python-pptx:     READY (1.0.2)
  lxml:            READY (5.1.0)
  jsonschema:      READY (4.21.0)

LAYOUT FIXTURES:
  Total:           29/29 present
  Process (8):     READY
  Cycle (2):       READY
  Hierarchy (5):   READY
  List (6):        READY
  Matrix (1):      READY
  Pyramid (1):     READY
  Relationship (4): READY

TEST CARRIER:
  process1:        BUILD OK

STATUS: FULLY_AVAILABLE
REASON: All dependencies installed, 29 layouts available, test carrier builds successfully
```
```

- [ ] **Step 2: Commit**

```bash
git add plugins/jack-tar-msft-smartart/skills/verify/
git commit -m "feat(jack-tar-msft-smartart): add verify skill"
```

---

### Task 2.8: Write jack-tar-custom-smartart:verify skill

**Files:**
- Create: `plugins/jack-tar-custom-smartart/skills/verify/SKILL.md`

- [ ] **Step 1: Write the verify skill**

Write `plugins/jack-tar-custom-smartart/skills/verify/SKILL.md`:

```markdown
---
name: verify
description: Check Mermaid CLI, Vega CLI, matplotlib, cairosvg availability and report readiness.
allowed-tools: Bash(python *), Bash(npx *), Bash(which *)
---

# /verify

Check whether this plugin's prerequisites are met and report readiness.

## Step 1: Check Python dependencies

```bash
python3 -c "
import json
deps = {}
try:
    import matplotlib; deps['matplotlib'] = matplotlib.__version__
except Exception: deps['matplotlib'] = None
try:
    import seaborn; deps['seaborn'] = seaborn.__version__
except Exception: deps['seaborn'] = None
try:
    from PIL import Image; import PIL; deps['Pillow'] = PIL.__version__
except Exception: deps['Pillow'] = None
try:
    import cairosvg; deps['cairosvg'] = 'installed'
except Exception: deps['cairosvg'] = None
print(json.dumps(deps))
"
```

## Step 2: Check Node.js CLI tools

```bash
npx mmdc --version 2>/dev/null || echo "NOT_FOUND"
npx vl2svg --version 2>/dev/null || echo "NOT_FOUND"
```

## Step 3: Report status

```
PLUGIN: jack-tar-custom-smartart
VERSION: 1.0.0

DEPENDENCIES:
  matplotlib:      READY (3.9.1)
  seaborn:         READY (0.13.2)
  Pillow:          READY (10.2.0)
  cairosvg:        READY (rasteriser: cairosvg)
  Mermaid CLI:     READY (11.12.0)
  Vega CLI:        READY (6.2.0)
  Vega-Lite:       READY (6.4.2)

ENGINES:
  custom_svg:      READY (9 layouts: flowchart, decision_tree, timeline, venn, swot, feature_matrix, pipeline_funnel, radar_chart, gantt)
  mermaid:         READY
  vega_lite:       READY
  matplotlib:      READY (chart types: bar, line, area, pie, donut, scatter, radar)

STATUS: FULLY_AVAILABLE
REASON: All rendering engines available
```

If Mermaid or Vega CLIs are missing, status is PARTIALLY_AVAILABLE (custom SVG and matplotlib still work).
```

- [ ] **Step 2: Commit**

```bash
git add plugins/jack-tar-custom-smartart/skills/verify/
git commit -m "feat(jack-tar-custom-smartart): add verify skill"
```

---

### Task 2.9: Write jack-tar-deckhand:verify skill

**Files:**
- Create: `plugins/jack-tar-deckhand/skills/verify/SKILL.md`

- [ ] **Step 1: Write the verify skill**

Write `plugins/jack-tar-deckhand/skills/verify/SKILL.md`:

```markdown
---
name: verify
description: Meta-verify — discover all jack-tar engine plugins, call each verify, report aggregate pipeline capability.
allowed-tools: Bash(python *), Bash(node *), Skill
---

# /verify

Discover all installed jack-tar engine plugins, call each plugin's `:verify` skill, and report aggregate pipeline capability.

## Step 1: Check local dependencies

Check that Python and Node.js with pptxgenjs are available:

```bash
python3 --version
node -e "require('pptxgenjs'); console.log('pptxgenjs OK')" 2>/dev/null || echo "pptxgenjs NOT_FOUND"
```

## Step 2: Discover engine plugins

Call each engine plugin's verify skill. If the skill doesn't exist (plugin not installed), record as "Not installed".

Invoke each in sequence:
1. `jack-tar-ollama:verify`
2. `jack-tar-cloud:verify`
3. `jack-tar-msft-smartart:verify`
4. `jack-tar-custom-smartart:verify`

For each, extract the STATUS line from the output.

## Step 3: Determine pipeline capabilities

Based on engine plugin availability:
- **Draft images:** READY if jack-tar-ollama is FULLY_AVAILABLE or PARTIALLY_AVAILABLE
- **Production images:** READY if jack-tar-cloud is FULLY_AVAILABLE or PARTIALLY_AVAILABLE
- **Editable SmartArt:** READY if jack-tar-msft-smartart is FULLY_AVAILABLE
- **Custom graphics:** READY if jack-tar-custom-smartart is FULLY_AVAILABLE or PARTIALLY_AVAILABLE
- **Deck assembly:** READY if pptxgenjs is installed
- **QA checks:** always READY (built into this plugin)

## Step 4: Report status

```
PLUGIN: jack-tar-deckhand
VERSION: 1.0.0

DEPENDENCIES:
  Python:          READY (3.12.x)
  Node.js:         READY (22.x)
  pptxgenjs:       READY

ENGINE PLUGINS:
  jack-tar-ollama:           FULLY_AVAILABLE
  jack-tar-cloud:            PARTIALLY_AVAILABLE
  jack-tar-msft-smartart:    FULLY_AVAILABLE
  jack-tar-custom-smartart:  NOT_AVAILABLE

PIPELINE CAPABILITY:
  Draft images:      READY (ollama available)
  Production images: READY (cloud partially available)
  Editable SmartArt: READY (msft-smartart available)
  Custom graphics:   NOT_READY (custom-smartart not available)
  Deck assembly:     READY (pptxgenjs installed)
  QA checks:         READY

STATUS: PARTIALLY_AVAILABLE
REASON: jack-tar-custom-smartart not available
```

Overall STATUS:
- FULLY_AVAILABLE: pptxgenjs installed + at least one image plugin + at least one SmartArt plugin
- PARTIALLY_AVAILABLE: pptxgenjs installed but some engine plugins missing
- NOT_AVAILABLE: pptxgenjs not installed (can't assemble decks at all)
```

- [ ] **Step 2: Commit**

```bash
git add plugins/jack-tar-deckhand/skills/verify/
git commit -m "feat(jack-tar-deckhand): add meta-verify skill"
```

---

### Task 2.10: Copy presentation skills into jack-tar-deckhand

**Files:**
- Copy: `.claude/skills/brand-manager/SKILL.md` -> `plugins/jack-tar-deckhand/skills/brand-manager/SKILL.md`
- Copy: `.claude/skills/slide-stylist/SKILL.md` -> `plugins/jack-tar-deckhand/skills/slide-stylist/SKILL.md`
- Copy: `.claude/skills/narrative-architect/SKILL.md` -> `plugins/jack-tar-deckhand/skills/narrative-architect/SKILL.md`
- Copy: `.claude/skills/strategy-map/SKILL.md` -> `plugins/jack-tar-deckhand/skills/strategy-map/SKILL.md`
- Copy: `.claude/skills/smartart-selector/SKILL.md` -> `plugins/jack-tar-deckhand/skills/smartart-selector/SKILL.md`
- Copy: `.claude/skills/smartart-extractor/SKILL.md` -> `plugins/jack-tar-deckhand/skills/smartart-extractor/SKILL.md`
- Copy: `.claude/skills/speaker-notes-writer/SKILL.md` -> `plugins/jack-tar-deckhand/skills/speaker-notes-writer/SKILL.md`
- Copy: `.claude/skills/imagegen-bridge/SKILL.md` -> `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md`
- Copy: `.claude/skills/deck-assembler/SKILL.md` -> `plugins/jack-tar-deckhand/skills/deck-assembler/SKILL.md`
- Copy: `.claude/skills/deck-qa/SKILL.md` -> `plugins/jack-tar-deckhand/skills/deck-qa/SKILL.md`

- [ ] **Step 1: Copy all presentation skills**

```bash
for skill in brand-manager slide-stylist narrative-architect strategy-map smartart-selector smartart-extractor speaker-notes-writer imagegen-bridge deck-assembler deck-qa; do
  mkdir -p "plugins/jack-tar-deckhand/skills/$skill"
  cp ".claude/skills/$skill/SKILL.md" "plugins/jack-tar-deckhand/skills/$skill/SKILL.md"
done
```

- [ ] **Step 2: Commit**

```bash
git add plugins/jack-tar-deckhand/skills/
git commit -m "feat(jack-tar-deckhand): copy presentation skills into plugin directory"
```

---

### Task 2.11: Copy presentation agents into jack-tar-deckhand

**Files:**
- Copy: `.claude/agents/deck-conductor.md` -> `plugins/jack-tar-deckhand/agents/deck-conductor.md`
- Copy: `.claude/agents/prompt-engineer.md` -> `plugins/jack-tar-deckhand/agents/prompt-engineer.md`
- Copy: `.claude/agents/image-reviewer.md` -> `plugins/jack-tar-deckhand/agents/image-reviewer.md`
- Copy: `.claude/agents/presentation-reviewer.md` -> `plugins/jack-tar-deckhand/agents/presentation-reviewer.md`
- Copy: `.claude/agents/vision-analyst.md` -> `plugins/jack-tar-deckhand/agents/vision-analyst.md`
- Copy: `.claude/agents/smartart-selector.md` -> `plugins/jack-tar-deckhand/agents/smartart-selector.md`

- [ ] **Step 1: Copy all presentation agents**

```bash
for agent in deck-conductor prompt-engineer image-reviewer presentation-reviewer vision-analyst smartart-selector; do
  cp ".claude/agents/$agent.md" "plugins/jack-tar-deckhand/agents/$agent.md"
done
```

- [ ] **Step 2: Commit**

```bash
git add plugins/jack-tar-deckhand/agents/
git commit -m "feat(jack-tar-deckhand): copy presentation agents into plugin directory"
```

---

### Task 2.12: Copy cloud skills into jack-tar-cloud

**Files:**
- Copy: `.claude/skills/cloud-generate-image/SKILL.md` -> `plugins/jack-tar-cloud/skills/openai-image/SKILL.md` (will be split in Phase 4)
- Copy: `.claude/skills/cloud-generate-icon/SKILL.md` -> `plugins/jack-tar-cloud/skills/recraft-icon/SKILL.md` (will be adapted in Phase 4)
- Copy: `.claude/agents/image-generation-expert.md` -> `plugins/jack-tar-cloud/agents/image-generation-expert.md`

- [ ] **Step 1: Copy skills and agent**

```bash
mkdir -p plugins/jack-tar-cloud/skills/openai-image
mkdir -p plugins/jack-tar-cloud/skills/recraft-icon
cp .claude/skills/cloud-generate-image/SKILL.md plugins/jack-tar-cloud/skills/openai-image/SKILL.md
cp .claude/skills/cloud-generate-icon/SKILL.md plugins/jack-tar-cloud/skills/recraft-icon/SKILL.md
cp .claude/agents/image-generation-expert.md plugins/jack-tar-cloud/agents/
```

Note: These skill files are placeholder copies. In Phase 4, the single `cloud-generate-image` skill will be split into per-provider skills (openai-image, google-image, fal-image) and the router skills (image, icon) will be written.

- [ ] **Step 2: Commit**

```bash
git add plugins/jack-tar-cloud/skills/ plugins/jack-tar-cloud/agents/
git commit -m "feat(jack-tar-cloud): copy cloud skills and image-generation-expert agent into plugin"
```

---

## Phase 3: Migrate Ollama from External Repo

**Goal:** Bring the Ollama skills, agent, and Python helper from `../claude-ollama-image-generator/` into the jack-tar-ollama plugin. Can run in parallel with Phase 2.

### Task 3.1: Copy Ollama skills into jack-tar-ollama

**Files:**
- Copy: `../claude-ollama-image-generator/.claude/skills/ollama-image/SKILL.md` -> `plugins/jack-tar-ollama/skills/image/SKILL.md`
- Copy: `../claude-ollama-image-generator/.claude/skills/ollama-icon/SKILL.md` -> `plugins/jack-tar-ollama/skills/icon/SKILL.md`
- Copy: `../claude-ollama-image-generator/.claude/skills/ollama-pattern/SKILL.md` -> `plugins/jack-tar-ollama/skills/pattern/SKILL.md`
- Copy: `../claude-ollama-image-generator/.claude/skills/ollama-diagram/SKILL.md` -> `plugins/jack-tar-ollama/skills/diagram/SKILL.md`
- Copy: `../claude-ollama-image-generator/.claude/skills/ollama-presentation/SKILL.md` -> `plugins/jack-tar-ollama/skills/presentation/SKILL.md`

- [ ] **Step 1: Copy skill files**

```bash
OLLAMA_SRC="../claude-ollama-image-generator/.claude/skills"
for pair in "ollama-image:image" "ollama-icon:icon" "ollama-pattern:pattern" "ollama-diagram:diagram" "ollama-presentation:presentation"; do
  src="${pair%%:*}"
  dst="${pair##*:}"
  mkdir -p "plugins/jack-tar-ollama/skills/$dst"
  cp "$OLLAMA_SRC/$src/SKILL.md" "plugins/jack-tar-ollama/skills/$dst/SKILL.md"
done
```

- [ ] **Step 2: Commit**

```bash
git add plugins/jack-tar-ollama/skills/
git commit -m "feat(jack-tar-ollama): migrate 5 skills from claude-ollama-image-generator"
```

---

### Task 3.2: Copy Ollama agent and Python helper

**Files:**
- Copy: `../claude-ollama-image-generator/.claude/agents/ollama-image-expert.md` -> `plugins/jack-tar-ollama/agents/ollama-image-expert.md`
- Copy: `../claude-ollama-image-generator/src/generate_image.py` -> `plugins/jack-tar-ollama/src/generate_image.py`

- [ ] **Step 1: Copy agent and source**

```bash
cp ../claude-ollama-image-generator/.claude/agents/ollama-image-expert.md plugins/jack-tar-ollama/agents/
cp ../claude-ollama-image-generator/src/generate_image.py plugins/jack-tar-ollama/src/
```

- [ ] **Step 2: Commit**

```bash
git add plugins/jack-tar-ollama/agents/ plugins/jack-tar-ollama/src/
git commit -m "feat(jack-tar-ollama): migrate agent and generate_image.py from claude-ollama-image-generator"
```

---

### Task 3.3: Copy Ollama tests

**Files:**
- Copy: `../claude-ollama-image-generator/tests/test_generate_image.py` -> `plugins/jack-tar-ollama/tests/test_generate_image.py`

- [ ] **Step 1: Copy test file**

```bash
cp ../claude-ollama-image-generator/tests/test_generate_image.py plugins/jack-tar-ollama/tests/
```

- [ ] **Step 2: Run the copied tests from plugin directory**

Run: `.venv/bin/pytest plugins/jack-tar-ollama/tests/test_generate_image.py -v`
Expected: 18 tests pass

If imports fail because the test uses `from src.generate_image import ...`, update the test to inject the plugin root into sys.path (same pattern as the import verification tests in Task 2.1).

- [ ] **Step 3: Commit**

```bash
git add plugins/jack-tar-ollama/tests/
git commit -m "feat(jack-tar-ollama): migrate 18 tests from claude-ollama-image-generator"
```

---

### Task 3.4: Verify complete Ollama plugin

- [ ] **Step 1: Run all Ollama plugin tests**

Run: `.venv/bin/pytest plugins/jack-tar-ollama/tests/ -v`
Expected: 18+ tests pass

- [ ] **Step 2: Verify original tests still pass**

Run: `.venv/bin/pytest tests/ -x -q`
Expected: 952 tests pass

- [ ] **Step 3: Verify plugin structure is complete**

```bash
ls -la plugins/jack-tar-ollama/skills/
ls -la plugins/jack-tar-ollama/agents/
ls -la plugins/jack-tar-ollama/src/
ls -la plugins/jack-tar-ollama/.claude-plugin/
```

Confirm: 6 skill dirs (image, icon, pattern, diagram, presentation, verify), 1 agent, 1 Python source, plugin.json, CLAUDE.md, requirements.txt, package.json.

---

## Phase 4: Rewrite Skill Python Invocations (Outline)

> **This phase will be expanded into a detailed plan when Phases 2-3 are complete.** The work here depends on discoveries made during the copy phase.

**Goal:** Update all 14 skills + 1 agent to use plugin-portable path resolution instead of repo-root-relative paths.

### Task 4.1: Create bin/jt-run helper for each plugin with Python runtime
- Write `bin/jt-run` for: jack-tar-cloud, jack-tar-msft-smartart, jack-tar-custom-smartart, jack-tar-deckhand
- jack-tar-ollama's skills call `src/generate_image.py` directly — adapt those paths too
- Test each helper from a non-repo directory

### Task 4.2: Update jack-tar-cloud skills
- Rewrite openai-image, google-image, fal-image, recraft-icon skills to use `$PLUGIN_ROOT/bin/jt-run`
- Write the router skills (image, icon) — new skills that call verify then dispatch to per-provider skills
- 7 skills total (4 per-provider + 2 routers + verify already done)

### Task 4.3: Update jack-tar-msft-smartart skills
- Rewrite render and catalog skills to use `$PLUGIN_ROOT/bin/jt-run`
- Write the inject skill — new skill wrapping assembler_patch.py
- 4 skills total (render, inject, catalog, verify already done)

### Task 4.4: Update jack-tar-custom-smartart skills
- Rewrite render and chart skills to use `$PLUGIN_ROOT/bin/jt-run`
- Handle Node.js path resolution for Mermaid/Vega CLIs
- 3 skills total (render, chart, verify already done)

### Task 4.5: Update jack-tar-deckhand skills (the big one)
- Rewrite all 10 skills to use `$PLUGIN_ROOT/bin/jt-run`
- Update deck-conductor agent (15 import sites)
- Update deck-assembler to resolve build_deck.js from plugin root
- Update imagegen-bridge to discover engine plugins via verify instead of direct imports
- Adapt image_router.py to work without provider_discovery.py (use verify contract instead)
- 10 skills + 1 agent = ~60 import sites to update

### Task 4.6: Update jack-tar-ollama skills
- Update 5 skills to resolve `src/generate_image.py` from plugin root instead of CWD
- Relatively simple — single Python file reference per skill

---

## Phase 5: Cross-Plugin Integration Testing (Outline)

> **This phase will be expanded into a detailed plan when Phase 4 is complete.**

### Task 5.1: Test deckhand verify discovers engine plugins
### Task 5.2: Test imagegen-bridge routes to ollama when available
### Task 5.3: Test imagegen-bridge routes to cloud when available
### Task 5.4: Test imagegen-bridge graceful degradation (no plugins)
### Task 5.5: Test smartart-extractor routes to msft-smartart:render
### Task 5.6: Test smartart-extractor routes to custom-smartart:render
### Task 5.7: Test assembler patch injection via msft-smartart:inject
### Task 5.8: Full pipeline integration test (all plugins installed)

---

## Phase 6: Remove Legacy Structure (Outline)

> **This phase will be expanded into a detailed plan when Phase 5 is complete.**

### Task 6.1: Remove original src/ files that have been moved to plugins
### Task 6.2: Remove original .claude/skills/ presentation skills
### Task 6.3: Remove original .claude/agents/ presentation agents
### Task 6.4: Update repo-level CLAUDE.md for plugin context
### Task 6.5: Update EPIC #40 with completion status
### Task 6.6: Final test run — all plugin tests pass, no legacy references remain

---

## Phase 7: Polish and Publish (Outline)

> **This phase will be expanded into a detailed plan when Phase 6 is complete.**

### Task 7.1: Write consumer-facing README per plugin
### Task 7.2: Write quick-start guide per plugin
### Task 7.3: Add LICENSE to each plugin directory
### Task 7.4: Version all plugins as 1.0.0
### Task 7.5: Test marketplace installation on clean machine
### Task 7.6: Publish to Claude Code marketplace
### Task 7.7: Test fresh install → verify → first deck build
### Task 7.8: Update docs/architecture/ to reflect new plugin structure
