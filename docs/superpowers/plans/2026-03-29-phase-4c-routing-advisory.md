# Phase 4C: Image Routing & Advisory -- imagegen-bridge + image-generation-expert

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the integration layer that ties all image generation capabilities together -- the `imagegen-bridge` skill that orchestrates ALL image generation routing, and the `image-generation-expert` advisory agent that provides prompt engineering and quality guidance across all models.

**Architecture:** The bridge is a Claude Code skill at `.claude/skills/imagegen-bridge/SKILL.md` that reads DeckContext (SlideOutline, StyleGuide), classifies slides by visual_type, routes each to the appropriate generation skill, tracks budget and cache, and produces the ImageManifest and ChartManifest. The routing logic lives in a testable Python module `src/image_router.py`. The expert agent at `.claude/agents/image-generation-expert.md` extends the existing `ollama-image-expert.md` with cloud model knowledge and is consulted by the bridge for prompt translation and quality scoring.

**Tech Stack:** Python 3.8+, pytest, jsonschema (all dependencies from Phase 1 and Phase 4A)

**Dependencies:**
- Phase 1 (complete): `src/deckcontext.py`, JSON schemas, test fixtures
- Phase 4A (complete): `src/cache_manager.py`, `src/budget_tracker.py`, `src/provider_discovery.py`, `src/prompt_translator.py`, `src/process_image.py`, `src/render_chart.py`
- Phase 4B (complete): `cloud-generate-image` skill, `cloud-generate-icon` skill
- Existing (unmodified): `ollama-image`, `ollama-icon`, `ollama-pattern`, `ollama-diagram` skills

**Phases overview (this is Phase 4C of Phase 4, which is Phase 4 of 6):**
- Phase 4A: Utility modules (cache, budget, discovery, translator, processor, chart renderer)
- Phase 4B: Cloud generation skills (cloud-generate-image, cloud-generate-icon)
- **Phase 4C: Routing & Advisory (this plan)** -- imagegen-bridge skill + image-generation-expert agent

---

## File Structure

```
research/
  synthesis-imagegen-bridge.md          # Research distillation for bridge
  synthesis-image-generation-expert.md  # Research distillation for expert agent
src/
  image_router.py                       # Routing matrix, fallback chains, classification (testable)
.claude/
  skills/
    imagegen-bridge/SKILL.md            # Top-level image orchestrator skill
  agents/
    image-generation-expert.md          # Advisory agent (extends ollama-image-expert)
tests/
  test_image_router.py                  # Unit tests for routing logic
  fixtures/
    routing_slide_outline.json          # 10-slide outline exercising all visual_types
```

---

## Task 1: Research Synthesis -- imagegen-bridge

**Files:**
- Create: `research/synthesis-imagegen-bridge.md`

- [ ] **Step 1: Create the synthesis document**

Create `research/synthesis-imagegen-bridge.md`:

```markdown
# Synthesis: imagegen-bridge

> Distilled from: research/05-multi-model-routing-pipeline.md, research/13-cost-optimisation-caching.md, docs/architecture/architecture-overview.md, docs/architecture/data-contracts.md

## 1. Core Knowledge Base

- The imagegen-bridge is the TOP-LEVEL image orchestrator within Image Services. It is invoked by the Deck Conductor and delegates to individual generation skills. It never generates images directly.
- Provider discovery runs at the start of every image generation phase. Ollama is probed via HTTP health check to localhost:11434. Cloud providers are detected via environment variables: OPENAI_API_KEY, GOOGLE_CLOUD_PROJECT, FAL_KEY, RECRAFT_API_KEY.
- The system operates on a "use what's available" principle -- it works with Ollama alone, cloud APIs alone, or any combination.

## 2. Routing Matrix (from Research 05 Finding 1.1)

| visual_type        | Draft Mode            | Production Mode        |
|--------------------|-----------------------|------------------------|
| hero_image         | ollama-image          | cloud-generate-image   |
| icon_set           | cloud-generate-icon   | cloud-generate-icon    |
| pattern_background | ollama-pattern        | cloud-generate-image   |
| diagram            | ollama-diagram        | ollama-diagram         |
| chart              | render_chart.py       | render_chart.py        |
| none               | skip                  | skip                   |

Icons always route to cloud because Recraft V4 is the ONLY model producing native SVG output. Diagrams always route to Ollama because AI-generated diagrams have text quality limitations regardless of model; the overlay pattern handles labels. Charts always route to programmatic rendering via matplotlib -- never AI-generated.

## 3. Fallback Chains (from Research 05 Finding 5.2)

hero_image: cloud-generate-image (FLUX.2 Pro) -> cloud-generate-image (GPT Image 1.5) -> ollama-image -> placeholder
icon_set: cloud-generate-icon (Recraft V4) -> cloud-generate-icon (FAL Recraft) -> placeholder (unicode symbol)
pattern_background: cloud-generate-image (Imagen 4 Fast) -> cloud-generate-image (FLUX.2 Pro) -> ollama-pattern -> placeholder
diagram: ollama-diagram -> placeholder
chart: render_chart.py -> placeholder (should never fail)

## 4. Budget Degradation (from Research 13 Section 4)

| State            | Threshold  | Image Strategy                                 |
|------------------|------------|------------------------------------------------|
| ALLOW            | 0-70% spent| Full multi-model routing                       |
| ALLOW_WITH_CAPS  | 70-90%     | Downgrade heroes to Imagen 4 Fast, skip decorative |
| DEGRADE          | 90-100%    | All remaining via Ollama (free)                |
| TYPOGRAPHY_ONLY  | 100%       | No image generation, placeholders only         |

## 5. Draft vs Production Lifecycle

Draft mode: uses Ollama for quick composition testing (free), cloud at reduced quality for prompt refinement. Production mode: full-quality cloud rendering at approved resolution. The Deck Conductor manages the lifecycle; the bridge just respects the --mode parameter.

## 6. ImageManifest Contract

File: ./tmp/deck/image-manifest.json. Required fields per image: image_id, slide_number, file_path, status. Status enum: generated, cached, placeholder, failed. Summary object tracks counts and timing.

## 7. ChartManifest Contract

File: ./tmp/deck/chart-manifest.json. Required fields per chart: chart_id, slide_number, file_path, chart_type, status. Status enum: rendered, cached, failed.

## 8. Anti-Patterns

- Never draft icons locally (raster vs SVG modality mismatch)
- Never draft text-heavy slides locally (garbled text makes assessment impossible)
- Never route all images through a single cloud provider (outage risk)
- Never chase local detail quality -- stop when composition is right
```

- [ ] **Step 2: Commit**

```bash
git add research/synthesis-imagegen-bridge.md
git commit -m "docs: add research synthesis for imagegen-bridge skill"
```

---

## Task 2: Research Synthesis -- image-generation-expert

**Files:**
- Create: `research/synthesis-image-generation-expert.md`

- [ ] **Step 1: Create the synthesis document**

Create `research/synthesis-image-generation-expert.md`:

```markdown
# Synthesis: image-generation-expert

> Distilled from: research/06-prompt-engineering-patterns.md, research/05-multi-model-routing-pipeline.md, docs/architecture/ai-persona-summaries.md, .claude/agents/ollama-image-expert.md

## 1. Core Identity

The Image Generation Expert is an ADVISORY AI Persona (L2, Invoker authority). It never generates images directly, never accesses DeckContext, and never makes routing decisions. It provides:
- Prompt engineering advice for any model
- Model-specific prompt translation
- Quality scoring against a 6-dimension rubric
- Model selection advice given asset type + available providers
- Iteration convergence guidance
- Safety filter recovery
- Style consistency advice

Escalation target: Deck Conductor (not Speaker directly).

## 2. Model-Specific Translation Rules

### z-image-turbo (Ollama, local)
- ~75 token window, front-load subject in first 10 words
- Camera specs boost quality: "Shot on Canon 5D Mark IV with 85mm f/1.4"
- Supports negative prompts via Ollama
- Best for: photorealism, skin textures, lighting

### flux2-klein (Ollama, local)
- ~100-250 word window, spatial hierarchy works best
- "In the foreground... Behind it... In the background..."
- NO negative prompt support (FLUX architecture)
- NEVER use "white background" -- causes fuzzy output
- Best for: text rendering, complex compositions, spatial accuracy

### GPT Image 1.5 (OpenAI, cloud)
- Unlimited token window, natural language paragraphs
- Background -> Subject -> Details -> Constraints structure
- Supports negative phrasing explicitly: "no watermark, no extra text"
- Native transparency via background="transparent" API parameter
- Quality parameter: low ($0.009), medium ($0.034), high ($0.133)
- Best for: illustrations, text-in-image, reasoning-heavy compositions

### FLUX.2 Pro (BFL via FAL.ai, cloud)
- 30-80 word sweet spot, photography-specific prompts
- Front-load subject, camera + lens + aperture + film stock
- NO negative prompt support
- Native transparency via transparent_bg toggle
- $0.030/megapixel
- Best for: hero images, photorealistic scenes, product photos

### Imagen 4 (Google Vertex AI, cloud)
- Large token window, natural descriptive language
- "A photo of..." start to leverage photorealistic capabilities
- 2-3 quality boosters MAX (more causes muddy output)
- Person generation requires explicit API parameter
- Fast: $0.020, Standard: $0.040, Ultra: $0.060
- Best for: backgrounds, textures, people, corporate scenes

### Recraft V4 (cloud)
- Focus on form and clarity, not photorealistic detail
- Specify stroke weight: "consistent 2px stroke weight"
- Native API colour palette parameter (RGB arrays)
- SVG output for icons, raster for illustrations
- SVG: $0.080, Pro SVG: $0.300
- Best for: icons, pictograms, design elements (ONLY native SVG)

### Ideogram 3.0 (cloud)
- ~150-160 word window, natural sentence-style
- Place text to render in quotes EARLY in prompt
- Max 25 characters per phrase, 2-3 phrases max
- 90-95% English text accuracy
- $0.030-$0.090 depending on tier
- Best for: typography-heavy designs (but prefer overlay pattern)

## 3. Quality Scoring Rubric

| Dimension               | Weight | Assessment Criteria |
|--------------------------|--------|---------------------|
| Composition              | 25%    | Subject placement, negative space for text overlay, rule of thirds, visual balance |
| Colour & Palette Match   | 20%    | Brand palette adherence, colour harmony, lighting consistency |
| Clarity & Sharpness      | 15%    | Free of artifacts, blur, distortion, extra limbs |
| Relevance to Slide       | 20%    | Matches visual_direction, appropriate for slide_type, supports headline |
| Technical Quality        | 10%    | Resolution appropriate, no banding, proper aspect ratio |
| Text Accuracy            | 10%    | For diagrams/text-bearing: legibility, correctness of rendered text |

Weighted score = sum(dimension_score * weight). Score 1-10 per dimension.

## 4. Convergence Rules

1. Accept: weighted score >= 7.5
2. Max iterations: hit configured limit (3 for hero, 2 for illustration, 1 for everything else)
3. Plateau: score not improved by > 0.3 across last 2 iterations
4. Oscillation: scores bouncing without upward trend
5. Escalation: quality below 6.0 after max iterations -> recommend fallback to next provider

## 5. Safety Filter Recovery

When cloud APIs reject a prompt:
1. Remove potentially sensitive terms (violence, medical, political)
2. Replace specific terms with metaphorical alternatives
3. Add "professional corporate presentation" qualifier
4. Try "safe" rephrasing: specific object -> abstract concept
5. Switch to different provider (different safety policies)
6. Fall back to text-free abstract background + overlay pattern

## 6. Style Consistency Techniques

1. Palette injection: append hex codes to every prompt
2. Visual baseline: generate hero first, extract style description as suffix for all subsequent prompts
3. Style suffixes: mood, lighting quality, texture, and atmosphere descriptors appended consistently
4. Where supported (FLUX Kontext, Ideogram): pass hero image as style reference
```

- [ ] **Step 2: Commit**

```bash
git add research/synthesis-image-generation-expert.md
git commit -m "docs: add research synthesis for image-generation-expert agent"
```

---

## Task 3: Routing Test Fixture

**Files:**
- Create: `tests/fixtures/routing_slide_outline.json`

- [ ] **Step 1: Create the routing test fixture**

Create `tests/fixtures/routing_slide_outline.json`:

```json
{
  "narrative_arc": "problem-solution",
  "estimated_duration_minutes": 30,
  "total_slides": 10,
  "slides": [
    {
      "slide_number": 1,
      "slide_type": "title",
      "headline": "Building Production AI Agents",
      "body_points": [],
      "narrative_beat": "hook",
      "visual_direction": "Abstract network of connected nodes in deep blue, conveying interconnected intelligence",
      "visual_type": "hero_image",
      "layout_template": "title"
    },
    {
      "slide_number": 2,
      "slide_type": "section_divider",
      "headline": "Understanding the Fundamentals",
      "body_points": [],
      "narrative_beat": "setup",
      "visual_direction": "Soft geometric pattern in muted blue and grey tones",
      "visual_type": "pattern_background",
      "layout_template": "section_divider"
    },
    {
      "slide_number": 3,
      "slide_type": "content",
      "headline": "The Three Pillars",
      "body_points": ["Perception", "Reasoning", "Action"],
      "narrative_beat": "evidence-1",
      "visual_direction": "Three clean icons representing perception (eye), reasoning (brain), action (hand)",
      "visual_type": "icon_set",
      "layout_template": "content"
    },
    {
      "slide_number": 4,
      "slide_type": "image_feature",
      "headline": "Real-World Impact",
      "body_points": ["Deployed at 50+ enterprises"],
      "narrative_beat": "evidence-2",
      "visual_direction": "Dramatic photo of a modern data centre with blue LED lighting",
      "visual_type": "hero_image",
      "layout_template": "image_feature"
    },
    {
      "slide_number": 5,
      "slide_type": "data_chart",
      "headline": "Growth Trajectory",
      "body_points": [],
      "narrative_beat": "evidence-3",
      "visual_type": "chart",
      "layout_template": "data_chart",
      "data": {
        "chart_type": "bar",
        "data_source_label": "quarterly_revenue",
        "inline_data": {"labels": ["Q1", "Q2", "Q3", "Q4"], "values": [10, 25, 45, 80]}
      }
    },
    {
      "slide_number": 6,
      "slide_type": "diagram",
      "headline": "System Architecture",
      "body_points": [],
      "narrative_beat": "evidence-4",
      "visual_direction": "Flowchart showing agent loop: input -> process -> tool call -> output",
      "visual_type": "diagram",
      "layout_template": "content"
    },
    {
      "slide_number": 7,
      "slide_type": "content",
      "headline": "Design Principles",
      "body_points": ["Simplicity", "Reliability", "Observability"],
      "narrative_beat": "evidence-5",
      "visual_direction": "Subtle textured background in warm grey tones",
      "visual_type": "pattern_background",
      "layout_template": "content"
    },
    {
      "slide_number": 8,
      "slide_type": "icon_grid",
      "headline": "Tool Ecosystem",
      "body_points": [],
      "narrative_beat": "evidence-6",
      "visual_direction": "Six flat icons: database, API, cloud, security lock, monitoring dashboard, deployment rocket",
      "visual_type": "icon_set",
      "layout_template": "icon_grid"
    },
    {
      "slide_number": 9,
      "slide_type": "content",
      "headline": "Key Insight",
      "body_points": ["State management is the hard part"],
      "narrative_beat": "callback",
      "visual_type": "none",
      "layout_template": "content"
    },
    {
      "slide_number": 10,
      "slide_type": "closing",
      "headline": "Start Simple, Iterate Fast",
      "body_points": ["Begin with the simplest agent that could work"],
      "narrative_beat": "cta",
      "visual_type": "none",
      "layout_template": "closing"
    }
  ]
}
```

- [ ] **Step 2: Commit**

```bash
git add tests/fixtures/routing_slide_outline.json
git commit -m "test: add routing test fixture with all visual_types"
```

---

## Task 4: Image Router Module -- Tests

**Files:**
- Create: `tests/test_image_router.py`

- [ ] **Step 1: Write the routing logic tests**

Create `tests/test_image_router.py`:

```python
"""Tests for image routing logic -- routing matrix, fallback chains, classification."""

import json
import os
import pytest

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def load_fixture(name):
    path = os.path.join(FIXTURE_DIR, f'{name}.json')
    with open(path) as f:
        return json.load(f)


# --- Provider availability scenarios ---

ALL_PROVIDERS = {
    'ollama': {'available': True, 'models': ['x/z-image-turbo', 'x/flux2-klein']},
    'openai': {'available': True, 'model': 'gpt-image-1.5'},
    'google_vertex': {'available': True, 'model': 'imagen-4'},
    'fal': {'available': True, 'models': ['flux-2-pro', 'recraft-v4']},
    'recraft': {'available': True, 'model': 'recraft-v4'},
}

OLLAMA_ONLY = {
    'ollama': {'available': True, 'models': ['x/z-image-turbo', 'x/flux2-klein']},
    'openai': {'available': False},
    'google_vertex': {'available': False},
    'fal': {'available': False},
    'recraft': {'available': False},
}

CLOUD_ONLY = {
    'ollama': {'available': False, 'models': []},
    'openai': {'available': True, 'model': 'gpt-image-1.5'},
    'google_vertex': {'available': True, 'model': 'imagen-4'},
    'fal': {'available': True, 'models': ['flux-2-pro', 'recraft-v4']},
    'recraft': {'available': True, 'model': 'recraft-v4'},
}

NO_PROVIDERS = {
    'ollama': {'available': False, 'models': []},
    'openai': {'available': False},
    'google_vertex': {'available': False},
    'fal': {'available': False},
    'recraft': {'available': False},
}


class TestClassifyVisualType:
    def test_explicit_visual_type_returned(self):
        from src.image_router import classify_visual_type
        slide = {'slide_number': 1, 'slide_type': 'title', 'visual_type': 'hero_image'}
        assert classify_visual_type(slide) == 'hero_image'

    def test_none_visual_type(self):
        from src.image_router import classify_visual_type
        slide = {'slide_number': 9, 'slide_type': 'content', 'visual_type': 'none'}
        assert classify_visual_type(slide) == 'none'

    def test_chart_visual_type(self):
        from src.image_router import classify_visual_type
        slide = {'slide_number': 5, 'slide_type': 'data_chart', 'visual_type': 'chart'}
        assert classify_visual_type(slide) == 'chart'

    def test_missing_visual_type_infers_from_slide_type(self):
        from src.image_router import classify_visual_type
        slide = {'slide_number': 1, 'slide_type': 'title'}
        assert classify_visual_type(slide) == 'hero_image'

    def test_data_chart_slide_type_infers_chart(self):
        from src.image_router import classify_visual_type
        slide = {'slide_number': 5, 'slide_type': 'data_chart'}
        assert classify_visual_type(slide) == 'chart'

    def test_closing_slide_type_infers_none(self):
        from src.image_router import classify_visual_type
        slide = {'slide_number': 10, 'slide_type': 'closing'}
        assert classify_visual_type(slide) == 'none'


class TestRouteSlideDraftMode:
    def test_hero_image_routes_to_ollama_image(self):
        from src.image_router import route_slide
        slide = {'slide_number': 1, 'visual_type': 'hero_image'}
        decision = route_slide(slide, 'draft', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'ollama-image'

    def test_icon_set_routes_to_cloud_icon(self):
        from src.image_router import route_slide
        slide = {'slide_number': 3, 'visual_type': 'icon_set'}
        decision = route_slide(slide, 'draft', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'cloud-generate-icon'

    def test_pattern_routes_to_ollama_pattern(self):
        from src.image_router import route_slide
        slide = {'slide_number': 2, 'visual_type': 'pattern_background'}
        decision = route_slide(slide, 'draft', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'ollama-pattern'

    def test_diagram_routes_to_ollama_diagram(self):
        from src.image_router import route_slide
        slide = {'slide_number': 6, 'visual_type': 'diagram'}
        decision = route_slide(slide, 'draft', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'ollama-diagram'

    def test_chart_routes_to_render_chart(self):
        from src.image_router import route_slide
        slide = {'slide_number': 5, 'visual_type': 'chart'}
        decision = route_slide(slide, 'draft', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'render_chart'

    def test_none_routes_to_skip(self):
        from src.image_router import route_slide
        slide = {'slide_number': 9, 'visual_type': 'none'}
        decision = route_slide(slide, 'draft', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'skip'


class TestRouteSlideProductionMode:
    def test_hero_image_routes_to_cloud(self):
        from src.image_router import route_slide
        slide = {'slide_number': 1, 'visual_type': 'hero_image'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'cloud-generate-image'

    def test_pattern_routes_to_cloud(self):
        from src.image_router import route_slide
        slide = {'slide_number': 2, 'visual_type': 'pattern_background'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'cloud-generate-image'

    def test_icon_still_routes_to_cloud_icon(self):
        from src.image_router import route_slide
        slide = {'slide_number': 3, 'visual_type': 'icon_set'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'cloud-generate-icon'

    def test_diagram_still_routes_to_ollama_diagram(self):
        from src.image_router import route_slide
        slide = {'slide_number': 6, 'visual_type': 'diagram'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'ollama-diagram'

    def test_chart_still_routes_to_render_chart(self):
        from src.image_router import route_slide
        slide = {'slide_number': 5, 'visual_type': 'chart'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'render_chart'


class TestFallbackChains:
    def test_hero_falls_back_to_ollama_when_no_cloud(self):
        from src.image_router import route_slide
        slide = {'slide_number': 1, 'visual_type': 'hero_image'}
        decision = route_slide(slide, 'production', OLLAMA_ONLY, 'allow')
        assert decision.skill == 'ollama-image'
        assert decision.is_fallback is True

    def test_hero_falls_back_to_placeholder_when_no_providers(self):
        from src.image_router import route_slide
        slide = {'slide_number': 1, 'visual_type': 'hero_image'}
        decision = route_slide(slide, 'production', NO_PROVIDERS, 'allow')
        assert decision.skill == 'placeholder'

    def test_icon_falls_back_to_placeholder_when_no_cloud(self):
        from src.image_router import route_slide
        slide = {'slide_number': 3, 'visual_type': 'icon_set'}
        decision = route_slide(slide, 'draft', OLLAMA_ONLY, 'allow')
        assert decision.skill == 'placeholder'
        assert decision.is_fallback is True

    def test_pattern_falls_back_to_ollama_when_no_cloud(self):
        from src.image_router import route_slide
        slide = {'slide_number': 2, 'visual_type': 'pattern_background'}
        decision = route_slide(slide, 'production', OLLAMA_ONLY, 'allow')
        assert decision.skill == 'ollama-pattern'
        assert decision.is_fallback is True

    def test_diagram_succeeds_with_ollama_only(self):
        from src.image_router import route_slide
        slide = {'slide_number': 6, 'visual_type': 'diagram'}
        decision = route_slide(slide, 'draft', OLLAMA_ONLY, 'allow')
        assert decision.skill == 'ollama-diagram'
        assert decision.is_fallback is False

    def test_chart_succeeds_with_no_providers(self):
        from src.image_router import route_slide
        slide = {'slide_number': 5, 'visual_type': 'chart'}
        decision = route_slide(slide, 'draft', NO_PROVIDERS, 'allow')
        assert decision.skill == 'render_chart'
        assert decision.is_fallback is False


class TestBudgetDegradation:
    def test_degrade_forces_ollama_for_hero(self):
        from src.image_router import route_slide
        slide = {'slide_number': 1, 'visual_type': 'hero_image'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'degrade')
        assert decision.skill == 'ollama-image'

    def test_degrade_forces_placeholder_for_icons_when_no_ollama(self):
        from src.image_router import route_slide
        slide = {'slide_number': 3, 'visual_type': 'icon_set'}
        decision = route_slide(slide, 'production', CLOUD_ONLY, 'degrade')
        assert decision.skill == 'placeholder'

    def test_typography_only_forces_skip_or_placeholder(self):
        from src.image_router import route_slide
        slide = {'slide_number': 1, 'visual_type': 'hero_image'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'typography_only')
        assert decision.skill == 'placeholder'

    def test_typography_only_still_allows_charts(self):
        from src.image_router import route_slide
        slide = {'slide_number': 5, 'visual_type': 'chart'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'typography_only')
        assert decision.skill == 'render_chart'

    def test_allow_with_caps_downgrades_hero_model(self):
        from src.image_router import route_slide
        slide = {'slide_number': 1, 'visual_type': 'hero_image'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'allow_with_caps')
        assert decision.skill == 'cloud-generate-image'
        assert decision.model == 'imagen-4-fast'


class TestRouteAllSlides:
    def test_routes_all_slides_in_fixture(self):
        from src.image_router import route_all_slides
        outline = load_fixture('routing_slide_outline')
        decisions = route_all_slides(outline, 'draft', ALL_PROVIDERS, 'allow')
        # 10 slides total: 8 with images (2 with none, 1 chart handled separately)
        # hero(1) + pattern(2) + icon(3) + hero(4) + diagram(6) + pattern(7) + icon(8) = 7
        image_decisions = [d for d in decisions if d.skill != 'skip']
        assert len(image_decisions) == 7

    def test_all_placeholders_when_no_providers(self):
        from src.image_router import route_all_slides
        outline = load_fixture('routing_slide_outline')
        decisions = route_all_slides(outline, 'draft', NO_PROVIDERS, 'allow')
        image_decisions = [d for d in decisions if d.skill != 'skip']
        # Diagrams become placeholder (no ollama), icons become placeholder (no cloud)
        # Heroes become placeholder, patterns become placeholder
        # Charts are NOT in route_all_slides (separate function)
        for d in image_decisions:
            assert d.skill == 'placeholder'


class TestGetChartSlides:
    def test_extracts_chart_slides(self):
        from src.image_router import get_chart_slides
        outline = load_fixture('routing_slide_outline')
        charts = get_chart_slides(outline)
        assert len(charts) == 1
        assert charts[0]['slide_number'] == 5
        assert charts[0]['data']['chart_type'] == 'bar'

    def test_empty_when_no_charts(self):
        from src.image_router import get_chart_slides
        outline = {
            'narrative_arc': 'test',
            'estimated_duration_minutes': 10,
            'slides': [
                {'slide_number': 1, 'slide_type': 'title', 'visual_type': 'hero_image', 'headline': 'Test'}
            ]
        }
        charts = get_chart_slides(outline)
        assert len(charts) == 0


class TestPlaceholderColor:
    def test_hero_uses_background_alt(self):
        from src.image_router import generate_placeholder_color
        palette = {'primary': '1A365D', 'background_alt': '1A202C'}
        assert generate_placeholder_color(palette, 'hero_image') == '1A202C'

    def test_pattern_uses_primary(self):
        from src.image_router import generate_placeholder_color
        palette = {'primary': '1A365D', 'background_alt': '1A202C'}
        assert generate_placeholder_color(palette, 'pattern_background') == '1A365D'

    def test_icon_uses_secondary_or_primary(self):
        from src.image_router import generate_placeholder_color
        palette = {'primary': '1A365D', 'secondary': '2B6CB0', 'background_alt': '1A202C'}
        colour = generate_placeholder_color(palette, 'icon_set')
        assert colour in ('1A365D', '2B6CB0')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_image_router.py -v`

Expected: FAIL -- `src/image_router.py` not found (ModuleNotFoundError).

- [ ] **Step 3: Commit**

```bash
git add tests/test_image_router.py
git commit -m "test: add routing logic tests for imagegen-bridge"
```

---

## Task 5: Image Router Module -- Implementation

**Files:**
- Create: `src/image_router.py`

- [ ] **Step 1: Create the image router module**

Create `src/image_router.py`:

```python
"""Image routing matrix, fallback chains, and asset classification.

This module contains the pure routing logic for the imagegen-bridge skill.
It maps visual_type + mode + available providers + budget state to a
RoutingDecision that tells the bridge which skill to invoke.

The routing matrix is derived from research/05-multi-model-routing-pipeline.md
Finding 1.1, with fallback chains from Finding 5.2 and budget degradation
from research/13-cost-optimisation-caching.md Section 4.
"""

from collections import namedtuple


RoutingTarget = namedtuple('RoutingTarget', [
    'skill',           # skill name: 'ollama-image', 'cloud-generate-image', etc.
    'provider',        # provider key: 'ollama', 'openai', 'google_vertex', 'fal', 'recraft', 'local'
    'model',           # model identifier: 'x/z-image-turbo', 'gpt-image-1.5', etc.
    'cost_per_image',  # estimated USD cost
])

RoutingDecision = namedtuple('RoutingDecision', [
    'slide_number',    # which slide this is for
    'visual_type',     # classified visual type
    'skill',           # chosen skill name
    'provider',        # chosen provider
    'model',           # chosen model
    'cost_per_image',  # estimated cost
    'is_fallback',     # whether this was a fallback choice
])


# --- Routing Matrix ---
# Maps (visual_type, mode) -> list of RoutingTargets in priority order.
# The first target whose provider is available is selected.

ROUTING_MATRIX = {
    ('hero_image', 'draft'): [
        RoutingTarget('ollama-image', 'ollama', 'x/z-image-turbo', 0.00),
        RoutingTarget('cloud-generate-image', 'fal', 'flux-2-pro', 0.03),
        RoutingTarget('cloud-generate-image', 'openai', 'gpt-image-1.5-low', 0.009),
    ],
    ('hero_image', 'production'): [
        RoutingTarget('cloud-generate-image', 'fal', 'flux-2-pro', 0.03),
        RoutingTarget('cloud-generate-image', 'openai', 'gpt-image-1.5-med', 0.034),
        RoutingTarget('cloud-generate-image', 'google_vertex', 'imagen-4-standard', 0.04),
        RoutingTarget('ollama-image', 'ollama', 'x/z-image-turbo', 0.00),
    ],
    ('icon_set', 'draft'): [
        RoutingTarget('cloud-generate-icon', 'recraft', 'recraft-v4-svg', 0.08),
        RoutingTarget('cloud-generate-icon', 'fal', 'recraft-v4', 0.08),
    ],
    ('icon_set', 'production'): [
        RoutingTarget('cloud-generate-icon', 'recraft', 'recraft-v4-svg', 0.08),
        RoutingTarget('cloud-generate-icon', 'fal', 'recraft-v4', 0.08),
    ],
    ('pattern_background', 'draft'): [
        RoutingTarget('ollama-pattern', 'ollama', 'x/z-image-turbo', 0.00),
        RoutingTarget('cloud-generate-image', 'google_vertex', 'imagen-4-fast', 0.02),
        RoutingTarget('cloud-generate-image', 'fal', 'flux-2-pro', 0.03),
    ],
    ('pattern_background', 'production'): [
        RoutingTarget('cloud-generate-image', 'google_vertex', 'imagen-4-fast', 0.02),
        RoutingTarget('cloud-generate-image', 'fal', 'flux-2-pro', 0.03),
        RoutingTarget('ollama-pattern', 'ollama', 'x/z-image-turbo', 0.00),
    ],
    ('diagram', 'draft'): [
        RoutingTarget('ollama-diagram', 'ollama', 'x/flux2-klein', 0.00),
    ],
    ('diagram', 'production'): [
        RoutingTarget('ollama-diagram', 'ollama', 'x/flux2-klein', 0.00),
    ],
    ('chart', 'draft'): [
        RoutingTarget('render_chart', 'local', 'matplotlib', 0.00),
    ],
    ('chart', 'production'): [
        RoutingTarget('render_chart', 'local', 'matplotlib', 0.00),
    ],
    ('none', 'draft'): [],
    ('none', 'production'): [],
}

# Budget-degraded routing overrides
BUDGET_DEGRADED_MATRIX = {
    ('hero_image', 'allow_with_caps'): [
        RoutingTarget('cloud-generate-image', 'google_vertex', 'imagen-4-fast', 0.02),
        RoutingTarget('cloud-generate-image', 'fal', 'flux-2-pro', 0.03),
        RoutingTarget('ollama-image', 'ollama', 'x/z-image-turbo', 0.00),
    ],
    ('hero_image', 'degrade'): [
        RoutingTarget('ollama-image', 'ollama', 'x/z-image-turbo', 0.00),
    ],
    ('icon_set', 'allow_with_caps'): [
        RoutingTarget('cloud-generate-icon', 'recraft', 'recraft-v4-svg', 0.08),
    ],
    ('icon_set', 'degrade'): [],  # No local alternative for SVG icons
    ('pattern_background', 'allow_with_caps'): [
        RoutingTarget('ollama-pattern', 'ollama', 'x/z-image-turbo', 0.00),
    ],
    ('pattern_background', 'degrade'): [
        RoutingTarget('ollama-pattern', 'ollama', 'x/z-image-turbo', 0.00),
    ],
    ('diagram', 'allow_with_caps'): [
        RoutingTarget('ollama-diagram', 'ollama', 'x/flux2-klein', 0.00),
    ],
    ('diagram', 'degrade'): [
        RoutingTarget('ollama-diagram', 'ollama', 'x/flux2-klein', 0.00),
    ],
}

# Slide type to visual type inference (when visual_type is missing)
SLIDE_TYPE_TO_VISUAL_TYPE = {
    'title': 'hero_image',
    'section_divider': 'pattern_background',
    'content': 'none',
    'two_column': 'none',
    'image_feature': 'hero_image',
    'data_chart': 'chart',
    'stat_callout': 'pattern_background',
    'quote': 'pattern_background',
    'icon_grid': 'icon_set',
    'diagram': 'diagram',
    'closing': 'none',
    'blank_visual': 'hero_image',
}

VALID_VISUAL_TYPES = {'hero_image', 'icon_set', 'pattern_background', 'diagram', 'chart', 'none'}


def classify_visual_type(slide):
    """Classify a slide's visual type from its visual_type field or slide_type.

    Args:
        slide: dict with at least 'slide_type' and optionally 'visual_type'.

    Returns:
        One of: 'hero_image', 'icon_set', 'pattern_background', 'diagram', 'chart', 'none'.
    """
    visual_type = slide.get('visual_type')
    if visual_type and visual_type in VALID_VISUAL_TYPES:
        return visual_type
    # Infer from slide_type
    slide_type = slide.get('slide_type', 'content')
    return SLIDE_TYPE_TO_VISUAL_TYPE.get(slide_type, 'none')


def _is_provider_available(provider, available_providers):
    """Check if a provider is available.

    Args:
        provider: provider key string ('ollama', 'openai', etc.)
        available_providers: dict from provider_discovery.

    Returns:
        True if the provider is available.
    """
    if provider == 'local':
        return True  # local tools (matplotlib) are always available
    provider_info = available_providers.get(provider, {})
    if isinstance(provider_info, dict):
        return provider_info.get('available', False)
    return False


def route_slide(slide, mode, available_providers, budget_state):
    """Route a single slide to the appropriate generation skill.

    Args:
        slide: dict from SlideOutline with at least slide_number, visual_type.
        mode: 'draft' or 'production'.
        available_providers: dict from provider_discovery.
        budget_state: one of 'allow', 'allow_with_caps', 'degrade', 'typography_only'.

    Returns:
        RoutingDecision namedtuple.
    """
    slide_number = slide.get('slide_number', 0)
    visual_type = classify_visual_type(slide)

    # Skip for none
    if visual_type == 'none':
        return RoutingDecision(
            slide_number=slide_number,
            visual_type='none',
            skill='skip',
            provider='none',
            model='none',
            cost_per_image=0.0,
            is_fallback=False,
        )

    # Charts always route to render_chart regardless of budget
    if visual_type == 'chart':
        return RoutingDecision(
            slide_number=slide_number,
            visual_type='chart',
            skill='render_chart',
            provider='local',
            model='matplotlib',
            cost_per_image=0.0,
            is_fallback=False,
        )

    # Typography-only: placeholder for everything except charts
    if budget_state == 'typography_only':
        return RoutingDecision(
            slide_number=slide_number,
            visual_type=visual_type,
            skill='placeholder',
            provider='none',
            model='none',
            cost_per_image=0.0,
            is_fallback=True,
        )

    # Select routing targets based on budget state
    if budget_state in ('allow_with_caps', 'degrade'):
        targets = BUDGET_DEGRADED_MATRIX.get(
            (visual_type, budget_state),
            ROUTING_MATRIX.get((visual_type, mode), [])
        )
    else:
        targets = ROUTING_MATRIX.get((visual_type, mode), [])

    # Find first available target
    is_fallback = False
    for i, target in enumerate(targets):
        if _is_provider_available(target.provider, available_providers):
            return RoutingDecision(
                slide_number=slide_number,
                visual_type=visual_type,
                skill=target.skill,
                provider=target.provider,
                model=target.model,
                cost_per_image=target.cost_per_image,
                is_fallback=is_fallback,
            )
        is_fallback = True  # Any target after the first is a fallback

    # No targets available: try the full fallback chain from the normal routing
    if budget_state in ('allow_with_caps', 'degrade'):
        normal_targets = ROUTING_MATRIX.get((visual_type, mode), [])
        for target in normal_targets:
            if _is_provider_available(target.provider, available_providers):
                return RoutingDecision(
                    slide_number=slide_number,
                    visual_type=visual_type,
                    skill=target.skill,
                    provider=target.provider,
                    model=target.model,
                    cost_per_image=target.cost_per_image,
                    is_fallback=True,
                )

    # All fallbacks exhausted: placeholder
    return RoutingDecision(
        slide_number=slide_number,
        visual_type=visual_type,
        skill='placeholder',
        provider='none',
        model='none',
        cost_per_image=0.0,
        is_fallback=True,
    )


def route_all_slides(outline, mode, available_providers, budget_state):
    """Route all slides in an outline to generation skills.

    Excludes chart slides (handled separately by get_chart_slides).
    Excludes none slides (no image needed).

    Args:
        outline: dict with 'slides' array from SlideOutline.
        mode: 'draft' or 'production'.
        available_providers: dict from provider_discovery.
        budget_state: one of 'allow', 'allow_with_caps', 'degrade', 'typography_only'.

    Returns:
        List of RoutingDecision namedtuples for image-needing slides.
    """
    decisions = []
    for slide in outline.get('slides', []):
        visual_type = classify_visual_type(slide)
        if visual_type == 'chart':
            continue  # Charts handled by get_chart_slides
        decision = route_slide(slide, mode, available_providers, budget_state)
        decisions.append(decision)
    return decisions


def get_chart_slides(outline):
    """Extract slides that need chart rendering.

    Args:
        outline: dict with 'slides' array from SlideOutline.

    Returns:
        List of slide dicts where visual_type is 'chart' or slide_type is 'data_chart'.
    """
    charts = []
    for slide in outline.get('slides', []):
        visual_type = classify_visual_type(slide)
        if visual_type == 'chart':
            charts.append(slide)
    return charts


def generate_placeholder_color(palette, visual_type):
    """Pick an appropriate placeholder colour from the StyleGuide palette.

    Args:
        palette: dict with palette colours (6-char hex without #).
        visual_type: the visual type that failed generation.

    Returns:
        6-char hex colour string.
    """
    colour_map = {
        'hero_image': 'background_alt',
        'pattern_background': 'primary',
        'diagram': 'background_alt',
        'icon_set': 'secondary',
    }
    key = colour_map.get(visual_type, 'primary')
    return palette.get(key, palette.get('primary', '333333'))
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_image_router.py -v`

Expected: All tests PASS.

- [ ] **Step 3: Commit**

```bash
git add src/image_router.py
git commit -m "feat: add image routing matrix with fallback chains and budget degradation"
```

---

## Task 6: imagegen-bridge Skill

**Files:**
- Create: `.claude/skills/imagegen-bridge/SKILL.md`

- [ ] **Step 1: Create the skill directory**

Run: `mkdir -p .claude/skills/imagegen-bridge`

- [ ] **Step 2: Create the skill definition**

Create `.claude/skills/imagegen-bridge/SKILL.md`:

````markdown
---
name: imagegen-bridge
description: Top-level image orchestrator. Routes all slide image generation to the appropriate skill (ollama-image, ollama-icon, ollama-pattern, ollama-diagram, cloud-generate-image, cloud-generate-icon, render_chart). Produces ImageManifest and ChartManifest.
argument-hint: --mode draft|production
allowed-tools: Bash(python *), Bash(curl *), Read, Glob, Skill
---

# /imagegen-bridge

Orchestrate ALL image generation for a presentation deck. This skill is invoked by the Deck Conductor after the SlideOutline and StyleGuide have been produced.

You are the routing orchestrator. You NEVER generate images directly. You read the DeckContext, classify each slide's image needs, route to the appropriate generation skill, track budget and cache, post-process results, and write the ImageManifest and ChartManifest.

Consult the `image-generation-expert` agent for prompt translation advice when generating production-quality hero images.

## Parse Arguments

Parse `$ARGUMENTS` for:
- **--mode MODE**: `draft` or `production` (default: `draft`)

## Step 1: Run Provider Discovery

Discover which image generation providers are available for this run.

```bash
python src/provider_discovery.py
```

Parse the JSON output into an `available_providers` dict. Report the findings:
- Which providers are available (Ollama, OpenAI, Google Vertex, FAL.ai, Recraft)
- Which Ollama models are installed (if Ollama is available)
- Whether any cloud providers are configured

If NO providers are available at all (no Ollama, no cloud), warn that all images will be placeholders but continue -- the deck must always be completable.

## Step 2: Read DeckContext Inputs

Read the required DeckContext files:

1. Read `./tmp/deck/outline.json` (SlideOutline) using the Read tool
2. Read `./tmp/deck/style-guide.json` (StyleGuide) using the Read tool
3. Read `./tmp/deck/talk-brief.json` (TalkBrief) using the Read tool -- needed for data_sources (charts)

Verify all three files exist. If any is missing, report the error and stop.

Parse the JSON content of each file.

## Step 3: Initialise Budget Tracker

Read or initialise the budget state:

```bash
python -c "
import json, os
budget_path = './tmp/deck/budget-state.json'
if os.path.exists(budget_path):
    with open(budget_path) as f:
        budget = json.load(f)
    print(json.dumps(budget))
else:
    print(json.dumps({'state': 'allow', 'spent': 0.0, 'total_budget': 2.0}))
"
```

Parse the budget state. The `state` field is one of: `allow`, `allow_with_caps`, `degrade`, `typography_only`.

## Step 4: Route All Slides

Use the image router to determine which skill handles each slide:

```bash
python -c "
import json, sys
from src.image_router import route_all_slides, get_chart_slides

outline = json.loads(sys.argv[1])
mode = sys.argv[2]
providers = json.loads(sys.argv[3])
budget_state = sys.argv[4]

decisions = route_all_slides(outline, mode, providers, budget_state)
charts = get_chart_slides(outline)

result = {
    'image_decisions': [d._asdict() for d in decisions],
    'chart_slides': charts,
}
print(json.dumps(result, indent=2))
" 'OUTLINE_JSON' 'MODE' 'PROVIDERS_JSON' 'BUDGET_STATE'
```

Replace `OUTLINE_JSON`, `MODE`, `PROVIDERS_JSON`, and `BUDGET_STATE` with the actual values parsed in previous steps. For large JSON, write to a temporary file first:

```bash
python -c "
import json
from src.image_router import route_all_slides, get_chart_slides

with open('./tmp/deck/outline.json') as f:
    outline = json.load(f)

# providers and budget_state from earlier steps
providers = PROVIDERS_DICT  # substitute actual dict
budget_state = 'BUDGET_STATE'  # substitute actual state
mode = 'MODE'  # substitute actual mode

decisions = route_all_slides(outline, mode, providers, budget_state)
charts = get_chart_slides(outline)

result = {
    'image_decisions': [d._asdict() for d in decisions],
    'chart_slides': charts,
}
print(json.dumps(result, indent=2))
"
```

Review the routing decisions. Report a summary table:

| Slide | Visual Type | Skill | Provider | Model | Est. Cost | Fallback? |
|-------|-------------|-------|----------|-------|-----------|-----------|

## Step 5: Check Cache for Each Image

For each routing decision where `skill` is not `skip` and not `placeholder`:

```bash
python -c "
from src.cache_manager import ImageCacheManager
from src.prompt_translator import translate_prompt
import json

cache = ImageCacheManager()

# For each slide, check if cached
visual_direction = 'VISUAL_DIRECTION'
model = 'MODEL'
palette = PALETTE_LIST  # e.g., ['1A365D', '2B6CB0']
width = WIDTH
height = HEIGHT

cache_key = cache.compute_cache_key(visual_direction, (width, height), 'presentation', model, palette)
cached = cache.get(cache_key)
if cached is not None:
    print(f'CACHE_HIT:{cache_key}')
else:
    print(f'CACHE_MISS:{cache_key}')

cache.close()
"
```

Track which slides have cache hits and which need generation.

## Step 6: Construct Prompts

For each slide that needs generation (cache miss), construct the model-specific prompt:

```bash
python -c "
from src.prompt_translator import translate_prompt
import json

visual_direction = '''VISUAL_DIRECTION_TEXT'''

style_tokens = {
    'mood': 'MOOD',
    'color_direction': 'COLOR_DIRECTION',
    'style_modifiers': STYLE_MODIFIERS_LIST
}

palette = PALETTE_DICT

translated = translate_prompt(
    visual_direction=visual_direction,
    model='MODEL_NAME',
    style_tokens=style_tokens,
    palette=palette,
    width=WIDTH,
    height=HEIGHT,
)
print(translated)
"
```

For production-mode hero images, consult the `image-generation-expert` agent before finalising the prompt. Ask the agent: "I need to translate this visual direction for MODEL_NAME. The visual direction is: VISUAL_DIRECTION. The style tokens are: STYLE_TOKENS. What prompt adjustments do you recommend?"

## Step 7: Generate Images

For each slide that needs generation, invoke the appropriate skill. Process slides sequentially (Ollama is sequential; cloud skills handle their own parallelism).

### For ollama-image (hero_image in draft mode):

Invoke the skill:
```
/ollama-image "TRANSLATED_PROMPT" --output ./tmp/deck/images/slide-NN-hero.png --width 1024 --height 576 --model x/z-image-turbo
```

### For ollama-pattern (pattern_background in draft mode):

Invoke the skill:
```
/ollama-pattern "TRANSLATED_PROMPT" --output ./tmp/deck/images/slide-NN-pattern.png --width 1024 --height 1024
```

### For ollama-diagram (diagram in any mode):

Invoke the skill:
```
/ollama-diagram "TRANSLATED_PROMPT" --type TYPE --output ./tmp/deck/images/slide-NN-diagram.png --width 1024 --height 768
```

### For cloud-generate-image (hero_image or pattern_background in production mode):

Invoke the skill:
```
/cloud-generate-image "TRANSLATED_PROMPT" --output ./tmp/deck/images/slide-NN-TYPE.png --provider PROVIDER --model MODEL --quality QUALITY_TIER
```

Where QUALITY_TIER is `draft` for draft mode, `production` for production mode.

### For cloud-generate-icon (icon_set in any mode):

Invoke the skill:
```
/cloud-generate-icon "TRANSLATED_PROMPT" --output ./tmp/deck/images/slide-NN-icon --style flat --palette PALETTE_HEX_LIST
```

### For render_chart (chart type):

```bash
python src/render_chart.py --slide-number NN --chart-type TYPE --data 'INLINE_DATA_JSON' --style-guide ./tmp/deck/style-guide.json --output ./tmp/deck/images/slide-NN-chart.png
```

### For placeholder (all providers failed):

```bash
python -c "
from src.process_image import generate_placeholder
generate_placeholder(
    width=1920,
    height=1080,
    colour='COLOUR_HEX',
    alt_text='ALT_TEXT_DESCRIPTION',
    output_path='./tmp/deck/images/slide-NN-placeholder.png'
)
print('Placeholder generated')
"
```

## Step 8: Handle Failures and Fallbacks

If any skill invocation fails (non-zero exit code, error message, timeout):

1. Log the failure: slide number, skill, error message
2. Look up the next target in the fallback chain by re-running route_slide with the failed provider removed from available_providers
3. Retry with the fallback skill
4. If all fallbacks exhausted, generate a placeholder
5. Record the failure in the image manifest entry with `status: "failed"` or `status: "placeholder"`

## Step 9: Track Budget

After each cloud generation, update the budget tracker:

```bash
python -c "
from src.budget_tracker import DeckBudget
import json

budget_path = './tmp/deck/budget-state.json'
with open(budget_path) as f:
    budget_data = json.load(f)

budget = DeckBudget(total_budget=budget_data['total_budget'], spent=budget_data['spent'])
budget.log_api_call(model='MODEL_NAME', cost=ACTUAL_COST)

budget_data['spent'] = budget.spent
budget_data['state'] = budget.state.value

with open(budget_path, 'w') as f:
    json.dump(budget_data, f, indent=2)

print(f'Budget: \${budget.spent:.3f} / \${budget.total_budget:.2f} ({budget.state.value})')
"
```

If the budget state changes (e.g., from `allow` to `allow_with_caps`), re-route remaining slides using the new budget state.

## Step 10: Post-Process Generated Images

For each generated image (not cached, not placeholder):

```bash
python -c "
from src.process_image import resize, crop_to_aspect, compute_content_hash

# Resize to target dimensions for the slide layout
resize('INPUT_PATH', WIDTH, HEIGHT, method='lanczos')

# Crop to 16:9 if needed
crop_to_aspect('INPUT_PATH', '16:9')

# Compute content hash for the manifest
content_hash = compute_content_hash('INPUT_PATH')
print(f'hash:{content_hash}')
"
```

## Step 11: Cache Generated Images

For each newly generated image, store in cache:

```bash
python -c "
from src.cache_manager import ImageCacheManager

cache = ImageCacheManager()
with open('IMAGE_PATH', 'rb') as f:
    image_data = f.read()

cache.put(
    cache_key='CACHE_KEY',
    image_data=image_data,
    ttl=TTL_SECONDS  # 604800 for heroes (7 days), None for icons (permanent), 2592000 for patterns (30 days)
)
cache.close()
print('Cached')
"
```

## Step 12: Build and Write ImageManifest

Construct the ImageManifest from all generation results:

```bash
python -c "
import json
from datetime import datetime, timezone
from src.deckcontext import write_contract

images = IMAGES_LIST  # list of per-image dicts built from generation results

# Count statuses
generated = sum(1 for i in images if i['status'] == 'generated')
cached = sum(1 for i in images if i['status'] == 'cached')
placeholder = sum(1 for i in images if i['status'] == 'placeholder')
failed = sum(1 for i in images if i['status'] == 'failed')
total_time = sum(i.get('generation_time_seconds', 0) for i in images)

manifest = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'image_backend': 'multi-model',
    'images': images,
    'summary': {
        'total_images': len(images),
        'generated_count': generated,
        'cached_count': cached,
        'placeholder_count': placeholder,
        'failed_count': failed,
        'total_generation_seconds': round(total_time, 2),
    },
}

write_contract('./tmp/deck', 'image-manifest', manifest)
print('ImageManifest written to ./tmp/deck/image-manifest.json')
print(json.dumps(manifest['summary'], indent=2))
"
```

Each image entry in the `images` list must have these fields:
- `image_id`: `"slide-{NN}-{type}"` (e.g., `"slide-01-hero"`, `"slide-03-icon"`)
- `slide_number`: integer
- `file_path`: `"./tmp/deck/images/slide-{NN}-{type}.png"`
- `placement_zone`: `"background"`, `"image_zone"`, `"icon_1"`, etc. (from layout template)
- `dimensions`: `{"width": W, "height": H}`
- `source_prompt`: the translated prompt that was sent to the model
- `model_used`: the model identifier
- `alt_text`: accessibility text describing the image content
- `content_hash`: SHA-256 of the image bytes
- `cache_key`: the cache lookup key
- `status`: `"generated"`, `"cached"`, `"placeholder"`, or `"failed"`
- `retry_count`: number of retries (0 if first attempt succeeded)
- `generation_time_seconds`: how long generation took

## Step 13: Build and Write ChartManifest

For data_chart slides, construct the ChartManifest:

```bash
python -c "
import json
from src.deckcontext import write_contract

charts = CHARTS_LIST  # list of per-chart dicts from render_chart results

manifest = {'charts': charts}

write_contract('./tmp/deck', 'chart-manifest', manifest)
print('ChartManifest written to ./tmp/deck/chart-manifest.json')
print(f'Charts rendered: {len(charts)}')
"
```

Each chart entry must have: `chart_id`, `slide_number`, `file_path`, `chart_type`, `status`, `data_source_label`, `alt_text`, `dimensions`, `content_hash`.

If no data_chart slides exist, write an empty ChartManifest: `{"charts": []}`.

## Step 14: Report Generation Summary

Print a final summary report:

```
=== Image Generation Summary ===
Mode: draft|production
Provider availability: Ollama (yes/no), OpenAI (yes/no), Google (yes/no), FAL (yes/no), Recraft (yes/no)

Images:
  Total: N
  Generated: N (N via Ollama, N via cloud)
  Cached: N (saved $X.XX)
  Placeholders: N
  Failed: N

Charts:
  Total: N
  Rendered: N

Budget:
  Spent: $X.XX / $X.XX (NN%)
  Budget state: allow|allow_with_caps|degrade|typography_only

Timing:
  Total generation time: Xs
  Average per image: Xs
```

Do not ask follow-up questions. Report and stop.
````

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/imagegen-bridge/SKILL.md
git commit -m "feat: add imagegen-bridge skill for image routing and orchestration"
```

---

## Task 7: Image Generation Expert Agent

**Files:**
- Create: `.claude/agents/image-generation-expert.md`

- [ ] **Step 1: Create the agent definition**

Create `.claude/agents/image-generation-expert.md`:

````markdown
---
name: image-generation-expert
description: Domain knowledge for ALL image generation models — local Ollama and cloud APIs. Provides prompt engineering, model-specific translation, quality scoring, iteration convergence, safety filter recovery, and style consistency advice. Advisory only — never generates images directly.
---

# Image Generation Expert

You are an expert in image generation across ALL supported models — both local Ollama and cloud APIs. You know how to write effective prompts for each model, evaluate generated images, translate prompts between models, and maintain visual consistency across a presentation deck.

You are a knowledge resource, not an orchestrator. You provide expertise on prompt engineering, quality evaluation, model selection, and refinement strategy. The `/imagegen-bridge` skill handles routing and orchestration. Individual generation skills handle tool calls.

**Authority model:** Invoker — you act on behalf of the skill that called you. You escalate to the Deck Conductor, not to the Speaker directly.

**Prohibited actions:**
- Must not invoke image generation directly
- Must not make routing decisions (the imagegen-bridge routes)
- Must not access or modify DeckContext state
- Must not communicate with the Speaker directly

## Supported Models

### Local Models (Ollama)

| Model | Identifier | Best For | Default Steps | Timeout | Notes |
|-------|-----------|----------|---------------|---------|-------|
| Z-Image Turbo | `x/z-image-turbo` | Photorealism, skin textures, lighting, HDR | 8 | 120s | Fast. Default model. Best for photos, portraits, landscapes. |
| FLUX.2 Klein | `x/flux2-klein` | Text rendering, complex multi-subject scenes, spatial accuracy | 20+ | 600s | Slower but more precise. Best for diagrams, text-heavy images, complex compositions. |

Both models are distilled and use natural language prompts only. Neither supports ControlNet, LoRA, inpainting, or img2img.

### Cloud Models

| Model | Provider | Identifier | Best For | Cost | Notes |
|-------|----------|-----------|----------|------|-------|
| GPT Image 1.5 | OpenAI | `gpt-image-1.5` | Illustrations, text-in-image, reasoning | $0.009-$0.133 | Low/Med/High quality. Natural language paragraphs. |
| FLUX.2 Pro | BFL via FAL.ai | `flux-2-pro` | Hero images, photorealism | $0.03/MP | 30-80 word sweet spot. Photography prompts. |
| Imagen 4 | Google Vertex | `imagen-4` | Backgrounds, textures, people | $0.02-$0.06 | Fast/Standard/Ultra. Natural descriptive language. |
| Recraft V4 | Recraft | `recraft-v4` | Icons, SVG vector output | $0.08-$0.30 | ONLY native SVG model. Design-centric prompts. |
| Ideogram 3.0 | Ideogram | `ideogram-3` | Typography, text in images | $0.03-$0.09 | 90%+ text accuracy. But prefer overlay pattern. |

## Prompt Engineering: Z-Image Turbo (Ollama)

Z-Image Turbo excels at photorealistic images. Structure prompts as:

```
[Shot type & subject] + [Appearance details] + [Environment] + [Lighting] + [Mood] + [Style] + [Technical notes]
```

**Front-load the subject.** Put the most important element in the first 15-20 words. Attention fades after approximately 75 tokens.

**Use camera specifications** to improve photorealism: "Shot on Canon 5D Mark IV with 85mm f/1.4 lens, shallow depth of field"

**Effective lighting keywords:**
- "soft diffused daylight" — natural outdoor look
- "cinematic warm key light" — dramatic indoor/studio feel
- "noir high-contrast lighting" — moody, dark atmosphere
- "studio portrait lighting with softbox" — clean, professional portraits
- "golden hour rim lighting" — warm backlighting
- "overcast flat lighting" — even, muted tones

**Good example:**
> A weathered fisherman in his 60s mending nets on a wooden dock at dawn. He wears a faded blue rain jacket and wool cap. The harbour behind him is shrouded in morning mist, fishing boats barely visible. Soft golden hour light catches the texture of his hands and the frayed rope. Mood is contemplative and quiet. Photorealistic documentary style. Shot on Leica Q2 with 28mm lens, natural light, film grain.

**Bad example:**
> (masterpiece:1.5), best quality, fisherman, nets, dock, ((morning)), beautiful, 4k, ultra detailed
This fails because: weight syntax is not supported, quality tags do nothing, the subject is not described — it's just keywords.

## Prompt Engineering: FLUX.2 Klein (Ollama)

FLUX.2 Klein excels at text rendering and spatial precision. Structure prompts using spatial hierarchy:

```
In the foreground, [element]. Behind it, [element]. In the background, [element].
```

Write as if briefing a human artist. Be explicit about spatial relationships, sizes, and placement.

**For text in images**, specify:
- The exact text to render
- Font style (serif, sans-serif, handwritten, bold)
- Size relative to the image
- Color and any effects
- Exact placement (top-center, bottom-left, overlaid on element)

**Use more of the 250-word budget.** FLUX handles longer prompts well.

**Avoid "white background"** — causes fuzzy, undefined outputs. Use "clean light grey studio backdrop" instead.

**Good example:**
> A professional book cover design. In the foreground, a large bold serif title reading "THE ATLAS" in dark navy blue, centered in the upper third. Below the title, a smaller subtitle in light grey sans-serif reading "A Novel by Sarah Chen". The middle ground shows a detailed vintage map of the Mediterranean coast in warm sepia tones. In the background, a subtle gradient from cream at the top to warm amber at the bottom.

## Prompt Engineering: GPT Image 1.5 (OpenAI)

GPT Image 1.5 is a natively multimodal transformer. It processes natural language conversationally.

**Structure:** Background/scene -> Subject -> Key details -> Constraints

**Translation rules:**
1. Use natural paragraphs, not keyword lists
2. Long prompts work well — the model auto-optimises internally
3. Camera/lens terminology steers results reliably
4. Place literal text in quotes or ALL CAPS
5. For exclusions: "no watermark, no extra text, no logos"
6. Quality parameter: `quality="high"` for production, `quality="low"` for iteration
7. For transparency: `background="transparent"` and `output_format="png"`

**Template:**
```
Background: [SCENE/ENVIRONMENT].
Subject: [DETAILED_SUBJECT with materials, shapes, textures].
Key details: [LIGHTING], [CAMERA_ANGLE], [COLOUR_PALETTE].
Style: [VISUAL_MEDIUM].
Constraints: No watermarks, no extra text, no logos. [COMPOSITION].
```

## Prompt Engineering: FLUX.2 Pro (Cloud)

FLUX.2 Pro is a 32B-parameter model. Photography-specific prompts work best.

**Translation rules:**
1. Front-load the subject — word order affects prioritisation
2. Photography specifications dramatically improve quality: camera model, lens focal length, aperture, film stock
3. Hex colours work when paired with objects: "a vase in colour #FF6B35"
4. Prose over keywords
5. Lighting has the biggest impact: specify type, direction, quality
6. Single style reference per prompt
7. For transparency: `transparent_bg: true`

**Template:**
```
[SUBJECT, concrete, 15-20 words]. [ACTION/STATE]. [ENVIRONMENT, 10-15 words].
[LIGHTING: type, direction, quality]. Shot on [CAMERA], [FOCAL_LENGTH] at
f/[APERTURE], [FILM_STOCK]. [MOOD]. [COLOUR_PALETTE with hex codes].
[COMPOSITION]. 16:9 landscape format.
```

## Prompt Engineering: Imagen 4 (Google)

Imagen 4 excels at photorealism, especially people and corporate scenes.

**Translation rules:**
1. Start with "A photo of..." to leverage photorealistic capabilities
2. Structure: Subject + Context/Background + Style + Details
3. Keep initial prompts under 50 words; expand to 100-200 for complex scenes
4. Include 2-3 quality boosters maximum — more causes muddy outputs
5. Describe unwanted elements positively (not "no X")
6. Camera proximity terms: "close-up, macro, zoomed out, aerial, low-angle"
7. Person generation requires explicit API parameter

**Template:**
```
A [photo | professional photograph] of [SUBJECT].
[SETTING with time of day]. [LIGHTING].
[STYLE_MODIFIERS: 2-3 max]. [COMPOSITION]. 16:9 format.
```

## Prompt Engineering: Recraft V4 (Icons & SVG)

Recraft V4 is the ONLY model producing native SVG vector output.

**Translation rules:**
1. Focus on form and clarity, not photorealistic detail
2. Specify stroke weight: "consistent 2px stroke weight"
3. Use the API colour palette parameter for exact brand colours (hex codes)
4. Describe geometric properties: "circular form, balanced central placement"
5. For icon sets: generate 6 at once for consistency

**Template (icons):**
```
A [flat | line art | minimal] icon representing [CONCEPT].
[GEOMETRIC_DESCRIPTION]. Consistent [2px] stroke weight, monoline style.
[COLOR] on [transparent] background. Scalable vector design.
Modern [UI | corporate] aesthetic.
```

## Prompt Engineering: Ideogram 3.0 (Typography)

Ideogram 3.0 specialises in text rendering (90%+ accuracy).

**Translation rules:**
1. Natural sentence-style prompts
2. Place text in quotes EARLY in the prompt
3. Keep text SHORT: 1-4 word phrases
4. Max 25 characters per phrase, 2-3 phrases max
5. Describe font style properties, not font names

**Note:** For presentations, ALWAYS prefer the overlay pattern. Generate text-free backgrounds and overlay text programmatically. Only use Ideogram for stylized poster effects where programmatic overlay cannot achieve the desired aesthetic.

## Universal Prompt Rules (All Models)

- **Optimal length**: 80-250 words depending on model
- **No weight syntax**: `(word:1.5)` is not supported by any of these models
- **Be specific**: "a dog" produces generic results; detailed descriptions produce compelling imagery
- **Describe what you want, not what you don't want**: Mentioning unwanted elements can paradoxically include them
- **Always include "No text, no watermarks, no logos"** for images that will have text overlaid in slides
- **Palette injection**: Append hex codes to every prompt for consistency

## Model Selection Advice

Given an asset type and available providers, recommend the optimal model:

| Asset Type | First Choice | Second Choice | Third Choice |
|------------|-------------|---------------|--------------|
| Hero image (production) | FLUX.2 Pro (photorealism) | GPT Image 1.5 Medium (reasoning) | Imagen 4 Standard |
| Hero image (draft) | Ollama Z-Image Turbo (free) | GPT Image 1.5 Low ($0.009) | Imagen 4 Fast ($0.02) |
| Icon set | Recraft V4 SVG (vector) | Recraft via FAL.ai | Placeholder (unicode) |
| Pattern/background | Imagen 4 Fast (cheap, fast) | FLUX.2 Pro | Ollama Z-Image Turbo |
| Diagram | Ollama FLUX.2 Klein (spatial) | Placeholder + overlay | — |
| People/headshots | Imagen 4 Standard | FLUX.2 Pro | GPT Image 1.5 Medium |
| Conceptual illustration | GPT Image 1.5 Medium | FLUX.2 Pro | Ollama Klein |
| Quote background | Imagen 4 Fast | Ollama Z-Image Turbo | Placeholder + overlay |

## Prompt Transfer Between Models

When switching from an Ollama draft to a cloud production render:

| From -> To | Transfer Quality | Required Adjustments |
|------------|-----------------|---------------------|
| Klein -> FLUX.2 Pro | GOOD (same family) | Minimal. Same architecture family. Quality improves automatically. |
| Z-Image Turbo -> GPT Image 1.5 | PARTIAL | Strip negative prompts. Simplify camera terms. Rely on GPT's superior understanding. |
| Z-Image Turbo -> FLUX.2 Pro | MODERATE | Keep composition; add photography-specific terms. Front-load subject. |
| Z-Image Turbo -> Imagen 4 | MODERATE | Switch to "A photo of..." structure. Reduce quality boosters to 2-3. |
| Any -> Recraft V4 | POOR | Complete rewrite needed. Raster->vector modality gap. Focus on form, not photorealism. |
| Any -> Ideogram 3.0 | NONE | Completely different prompt structure. Place text early in quotes. |

## Scoring Rubric

When reviewing a generated image for a presentation, evaluate across these six dimensions. Each dimension is scored 1-10.

| Dimension | Weight | What to Assess |
|-----------|--------|----------------|
| Composition | 25% | Subject placement, negative space for text overlay, rule of thirds, visual balance, framing appropriate for slide layout |
| Colour & Palette Match | 20% | Brand palette adherence, colour harmony, lighting colour temperature consistent with deck mood |
| Clarity & Sharpness | 15% | Free of artifacts, distortion, extra limbs, warped text, blur, colour banding |
| Relevance to Slide | 20% | Matches visual_direction, appropriate for slide_type, supports the headline message |
| Technical Quality | 10% | Resolution appropriate for target size, proper aspect ratio, no banding or compression artifacts |
| Text Accuracy | 10% | For diagrams and text-bearing: legibility, correctness of rendered text. For text-free: score 8 (N/A baseline) |

**Weighted score formula:**
```
weighted_score = (composition * 0.25) + (colour_match * 0.20) +
                 (clarity * 0.15) + (relevance * 0.20) +
                 (technical * 0.10) + (text_accuracy * 0.10)
```

Be honest and critical. A 7 means "good with noticeable room for improvement." Reserve 9-10 for genuinely excellent results. A 5 means "right idea but significant execution problems."

## Score Bands and Mutation Strategies

| Score | Interpretation | What to Do |
|-------|---------------|------------|
| 8.0-10.0 | **Accept** | Stop iterating. This image meets the quality bar. |
| 7.0-7.9 | **Good, minor gaps** | **Additive refinement only.** Add lighting keywords, camera specs, mood descriptors. Do NOT restructure. |
| 5.0-6.9 | **Structural issues** | **Structural refinement.** Reorder elements, add/remove descriptive blocks, clarify spatial relationships. |
| 1.0-4.9 | **Fundamental mismatch** | **Rewrite from scratch.** Use iteration history to avoid repeating failed approaches. |

**Regression recovery:** If current iteration scores LOWER than previous, revert to the best-scoring prompt and apply only minor additive modifications.

## Convergence Rules

Stop iterating if ANY of these conditions are true:

1. **Accept threshold reached**: Weighted score >= 7.5
2. **Max iterations reached**: Hit the configured limit (3 for hero, 2 for illustration, 1 for other)
3. **Plateau detected**: Score has not improved by more than 0.3 across the last 2 consecutive iterations
4. **Oscillation detected**: Scores bouncing without upward trend (e.g., 5.8 -> 6.4 -> 5.9 -> 6.3)

When stopping early, always report the **best-scoring iteration**, not the last one.

**Escalation trigger**: Quality below 6.0 after max iterations -- recommend fallback to next provider in the chain. Report to the bridge which will handle the fallback routing.

## Safety Filter Recovery

When a cloud API rejects a prompt (safety filter, content policy violation):

1. **Remove potentially sensitive terms**: violence, medical procedures, specific political references
2. **Replace specific terms with metaphorical alternatives**: "battlefield" -> "competitive landscape", "explosion" -> "rapid expansion"
3. **Add professional qualifier**: prepend "Professional corporate presentation image of..."
4. **Abstract the concept**: "people protesting" -> "dynamic crowd scene with energy and movement"
5. **Switch provider**: Different providers have different safety policies. Try FAL.ai (most permissive) or Imagen 4 (configurable safety levels)
6. **Fall back to abstract**: Generate a text-free abstract background and use the overlay pattern

## Style Consistency Across a Deck

### Palette Injection

Append the deck's hex colours to EVERY prompt:
```
Colour palette strictly limited to: primary #HEX1, secondary #HEX2,
accent #HEX3, neutral dark #HEX4, neutral light #HEX5.
No other colours should appear prominently.
```

This does not guarantee exact matches but biases output toward complementary tones.

### Visual Baseline Approach

1. Generate the title slide hero image first with full creative freedom
2. Extract style description: colour quality, lighting quality, texture, mood
3. Construct a style suffix from the hero:
```
Consistent with the visual style: [COLOUR_QUALITY], [LIGHTING_QUALITY],
[TEXTURE], [MOOD]. [EXACT HEX CODES from hero].
```
4. Append this suffix to every subsequent prompt in the deck

### Style Suffixes for Presentations

Production-tested suffixes to maintain consistency:

**Corporate Professional:**
```
Clean corporate aesthetic, polished and modern. Soft studio lighting
with gentle shadows. Muted, sophisticated colour palette. No busy
backgrounds or visual clutter.
```

**Technical Conference:**
```
Modern tech aesthetic, clean lines, subtle gradients. Dark background
with accent lighting. Futuristic but grounded. Professional conference
keynote quality.
```

**Creative/Inspirational:**
```
Bold, vibrant imagery with confident composition. Dynamic lighting with
strong directional shadows. High contrast, editorial quality. Energy
and movement in the composition.
```

## Images for Presentations

### Sizing for 16:9 Slides (10" x 5.625")

| Use Case | Pixel Size | Notes |
|----------|-----------|-------|
| Full-bleed background | 1920x1080 or 1024x576 | Covers entire slide. Keep subtle. |
| Half-slide (left or right) | 512x576 or 960x1080 | Two-column layouts. |
| Content image | 1024x768 or 768x768 | Within a layout alongside text. |
| Icon | 512x512 | Generate large for sharpness. |
| Pattern/texture | 1024x1024 | Square for tiling. |

### Key Lessons

- **Camera specs dramatically improve photorealism** with Z-Image Turbo and FLUX.2 Pro
- **"No text, no words, no letters"** is essential for images that will have text overlaid
- **Semi-transparent overlays** (transparency 30-40%) make text readable over any image
- **1024x576 is sufficient** for slide backgrounds — 1920x1080 is slower with no visible quality gain
- **Don't generate text in images** — use images as backdrops and overlay text via layout tool
- **Generate hero image first** — use it to establish visual tone for the rest of the deck
````

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/image-generation-expert.md
git commit -m "feat: add image-generation-expert agent with cloud model knowledge"
```

---

## Task 8: Final Verification

**Files:** None (verification only)

- [ ] **Step 1: Run all routing tests**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_image_router.py -v`

Expected: All tests PASS.

- [ ] **Step 2: Run full test suite**

Run: `source .venv/bin/activate && python3 -m pytest tests/ -v --tb=short`

Expected: All tests PASS (existing + new routing tests).

- [ ] **Step 3: Verify Python syntax**

Run: `source .venv/bin/activate && python3 -m py_compile src/image_router.py && echo "Syntax OK"`

Expected: "Syntax OK"

- [ ] **Step 4: Verify skill and agent files exist and have correct frontmatter**

Run:
```bash
head -6 .claude/skills/imagegen-bridge/SKILL.md && echo "---" && head -4 .claude/agents/image-generation-expert.md
```

Expected: YAML frontmatter with correct `name` and `description` fields for both files.

- [ ] **Step 5: Verify research synthesis files exist**

Run:
```bash
ls -la research/synthesis-imagegen-bridge.md research/synthesis-image-generation-expert.md
```

Expected: Both files exist.

- [ ] **Step 6: Commit all Phase 4C deliverables (if any uncommitted)**

```bash
git status
```

If there are uncommitted changes:
```bash
git add -A
git commit -m "feat: complete Phase 4C -- imagegen-bridge routing and image-generation-expert advisory"
```

---

## Summary

After completing all 8 tasks, Phase 4C provides:

| Artifact | Purpose |
|----------|---------|
| `research/synthesis-imagegen-bridge.md` | Research distillation for bridge routing |
| `research/synthesis-image-generation-expert.md` | Research distillation for expert agent |
| `src/image_router.py` | Testable routing matrix, fallback chains, classification |
| `.claude/skills/imagegen-bridge/SKILL.md` | Top-level image orchestrator skill |
| `.claude/agents/image-generation-expert.md` | Advisory agent with all model knowledge |
| `tests/test_image_router.py` | Unit tests for routing decisions |
| `tests/fixtures/routing_slide_outline.json` | Test fixture with all visual_types |

**How the bridge orchestrates the pipeline:**
1. Deck Conductor invokes `/imagegen-bridge --mode draft`
2. Bridge runs provider discovery
3. Bridge reads SlideOutline and StyleGuide from DeckContext
4. Bridge calls `image_router.route_all_slides()` for routing decisions
5. Bridge checks cache for each routed slide
6. Bridge constructs model-specific prompts via `prompt_translator`
7. Bridge invokes generation skills: `/ollama-image`, `/ollama-pattern`, `/ollama-diagram`, `/cloud-generate-image`, `/cloud-generate-icon`
8. Bridge invokes `render_chart.py` for data_chart slides
9. Bridge generates placeholders when all providers fail
10. Bridge post-processes images, caches results, tracks budget
11. Bridge writes `image-manifest.json` and `chart-manifest.json`
12. Bridge reports generation summary

---

### Critical Files for Implementation

- `/Users/stevejones/Documents/Development/jack-tar-deckhand/docs/superpowers/plans/2026-03-29-phase-1-foundation.md` -- format template to follow for task structure, checkbox steps, complete code, and commit pattern
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/agents/ollama-image-expert.md` -- the existing 219-line agent that image-generation-expert extends with cloud model knowledge
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/research/05-multi-model-routing-pipeline.md` -- the routing matrix (Finding 1.1), fallback chains (Finding 5.2), and cost model that drive `src/image_router.py`
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/research/06-prompt-engineering-patterns.md` -- all 7 model-specific translation rules (Findings 3.1-3.7) that the expert agent encodes
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/skills/ollama-image/SKILL.md` -- the invocation pattern (argument format, output path, allowed-tools) the bridge must follow when calling Ollama skills