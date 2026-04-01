# Production Rendering Engine Strategy — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the one-size-fits-all production upgrade path with an expert-advised two-track system — raster upscale (cloud LLM models) and vector conversion (Recraft SVG) — where the image-generation-expert agent produces a reviewable Production Upgrade Plan before any money is spent.

**Architecture:** The image-generation-expert agent gains a new responsibility: producing a `production-upgrade-plan.json` artifact that maps each slide to its optimal production engine, tier, and dimensions. The existing `plan_production_upgrade()` function in `image_router.py` is replaced by an executor that reads this plan. The presentation-reviewer gains post-production quality verdicts (pass/escalate_tier/escalate_provider/flag_for_speaker) that feed back through the deck-conductor for Speaker approval.

**Tech Stack:** Python (jsonschema validation), JSON Schema Draft 2020-12, Claude Code agents (markdown), pytest

**Spec:** `docs/superpowers/specs/2026-03-31-production-rendering-engine-strategy.md`

---

### Task 1: Production Upgrade Plan Schema

**Files:**
- Create: `src/schemas/production_upgrade_plan.schema.json`
- Modify: `tests/test_schemas.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_schemas.py`:

```python
def test_production_upgrade_plan_schema_loads():
    schema_path = os.path.join(SCHEMA_DIR, 'production_upgrade_plan.schema.json')
    with open(schema_path) as f:
        schema = json.load(f)
    assert schema['title'] == 'ProductionUpgradePlan'
    assert 'entries' in schema['properties']


def test_production_upgrade_plan_valid_entry():
    schema_path = os.path.join(SCHEMA_DIR, 'production_upgrade_plan.schema.json')
    with open(schema_path) as f:
        schema = json.load(f)
    valid_plan = {
        'created_at': '2026-03-31T12:00:00Z',
        'deck_dir': './tmp/deck',
        'total_estimated_cost_usd': 0.45,
        'entries': [
            {
                'slide_number': 1,
                'image_id': 'slide-01-hero',
                'upgrade_track': 'raster_upscale',
                'recommended_provider': 'fal',
                'recommended_model': 'flux-2-pro',
                'recommended_tier': 'standard',
                'target_dimensions': '1920x1080',
                'estimated_cost_usd': 0.03,
                'reasoning': 'Abstract artistic hero — FLUX Pro best for bold colour',
                'brand_notes': None,
                'warnings': [],
                'draft_prompt': 'A dramatic teal wave...',
            },
            {
                'slide_number': 4,
                'image_id': 'slide-04-diagram',
                'upgrade_track': 'vector_conversion',
                'recommended_provider': 'recraft',
                'recommended_model': 'recraft-v4-svg',
                'recommended_tier': 'standard',
                'target_dimensions': None,
                'estimated_cost_usd': 0.08,
                'reasoning': 'Flowchart with 6 elements — clean vector output',
                'brand_notes': None,
                'warnings': [],
                'draft_prompt': 'A flowchart showing...',
            },
        ],
    }
    import jsonschema
    jsonschema.Draft202012Validator(schema).validate(valid_plan)


def test_production_upgrade_plan_rejects_invalid_track():
    schema_path = os.path.join(SCHEMA_DIR, 'production_upgrade_plan.schema.json')
    with open(schema_path) as f:
        schema = json.load(f)
    invalid = {
        'created_at': '2026-03-31T12:00:00Z',
        'deck_dir': './tmp/deck',
        'total_estimated_cost_usd': 0.0,
        'entries': [{
            'slide_number': 1,
            'image_id': 'x',
            'upgrade_track': 'magic_upgrade',
            'recommended_provider': 'fal',
            'recommended_model': 'flux-2-pro',
            'recommended_tier': 'standard',
            'target_dimensions': None,
            'estimated_cost_usd': 0.0,
            'reasoning': 'test',
            'brand_notes': None,
            'warnings': [],
            'draft_prompt': None,
        }],
    }
    import jsonschema
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(invalid)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_schemas.py::test_production_upgrade_plan_schema_loads tests/test_schemas.py::test_production_upgrade_plan_valid_entry tests/test_schemas.py::test_production_upgrade_plan_rejects_invalid_track -v`
Expected: FAIL — schema file does not exist

- [ ] **Step 3: Create the schema**

Create `src/schemas/production_upgrade_plan.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/production-upgrade-plan.json",
  "title": "ProductionUpgradePlan",
  "description": "Expert-advised production upgrade plan mapping each slide to its optimal rendering engine, tier, and dimensions.",
  "type": "object",
  "required": ["created_at", "deck_dir", "total_estimated_cost_usd", "entries"],
  "properties": {
    "created_at": { "type": "string" },
    "deck_dir": { "type": "string" },
    "total_estimated_cost_usd": { "type": "number", "minimum": 0 },
    "entries": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "slide_number", "image_id", "upgrade_track",
          "recommended_provider", "recommended_model", "recommended_tier",
          "target_dimensions", "estimated_cost_usd", "reasoning",
          "brand_notes", "warnings", "draft_prompt"
        ],
        "properties": {
          "slide_number": { "type": "integer", "minimum": 1 },
          "image_id": { "type": "string" },
          "upgrade_track": {
            "type": "string",
            "enum": ["raster_upscale", "vector_conversion", "no_upgrade"]
          },
          "recommended_provider": { "type": "string" },
          "recommended_model": { "type": "string" },
          "recommended_tier": {
            "type": "string",
            "enum": ["standard", "pro", "flash", "low", "medium", "high"]
          },
          "target_dimensions": { "type": ["string", "null"] },
          "estimated_cost_usd": { "type": "number", "minimum": 0 },
          "reasoning": { "type": "string" },
          "brand_notes": { "type": ["string", "null"] },
          "warnings": {
            "type": "array",
            "items": { "type": "string" }
          },
          "draft_prompt": { "type": ["string", "null"] }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_schemas.py -v`
Expected: ALL PASS (including the 3 new tests)

- [ ] **Step 5: Commit**

```bash
git add src/schemas/production_upgrade_plan.schema.json tests/test_schemas.py
git commit -m "feat: add ProductionUpgradePlan JSON schema"
```

---

### Task 2: Production Upgrade Plan Loader and Executor

**Files:**
- Modify: `src/image_router.py`
- Modify: `tests/test_image_router.py`

This replaces the intelligence in `plan_production_upgrade()` with a thin executor that reads the expert's approved plan. The existing function and its tests stay for backward compatibility but are marked deprecated.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_image_router.py`:

```python
from src.image_router import load_upgrade_plan, execute_upgrade_plan_entry


def test_load_upgrade_plan_reads_file(tmp_path):
    plan = {
        'created_at': '2026-03-31T12:00:00Z',
        'deck_dir': str(tmp_path),
        'total_estimated_cost_usd': 0.11,
        'entries': [
            {
                'slide_number': 1,
                'image_id': 'slide-01-hero',
                'upgrade_track': 'raster_upscale',
                'recommended_provider': 'fal',
                'recommended_model': 'flux-2-pro',
                'recommended_tier': 'standard',
                'target_dimensions': '1920x1080',
                'estimated_cost_usd': 0.03,
                'reasoning': 'Abstract hero',
                'brand_notes': None,
                'warnings': [],
                'draft_prompt': 'A dramatic wave',
            },
        ],
    }
    plan_path = tmp_path / 'production-upgrade-plan.json'
    plan_path.write_text(json.dumps(plan))
    loaded = load_upgrade_plan(str(tmp_path))
    assert len(loaded['entries']) == 1
    assert loaded['entries'][0]['upgrade_track'] == 'raster_upscale'


def test_load_upgrade_plan_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_upgrade_plan(str(tmp_path))


def test_execute_entry_raster_returns_skill_and_provider():
    entry = {
        'upgrade_track': 'raster_upscale',
        'recommended_provider': 'google',
        'recommended_model': 'gemini-3.1-flash-image-preview',
        'recommended_tier': 'flash',
        'target_dimensions': '1920x1080',
    }
    result = execute_upgrade_plan_entry(entry)
    assert result['skill'] == 'cloud-generate-image'
    assert result['provider'] == 'google'
    assert result['model'] == 'gemini-3.1-flash-image-preview'
    assert result['width'] == 1920
    assert result['height'] == 1080


def test_execute_entry_vector_returns_icon_skill():
    entry = {
        'upgrade_track': 'vector_conversion',
        'recommended_provider': 'recraft',
        'recommended_model': 'recraft-v4-svg',
        'recommended_tier': 'standard',
        'target_dimensions': None,
    }
    result = execute_upgrade_plan_entry(entry)
    assert result['skill'] == 'cloud-generate-icon'
    assert result['provider'] == 'recraft'
    assert result['model'] == 'recraft-v4-svg'
    assert result['width'] is None
    assert result['height'] is None


def test_execute_entry_no_upgrade_returns_skip():
    entry = {
        'upgrade_track': 'no_upgrade',
        'recommended_provider': 'local',
        'recommended_model': 'matplotlib',
        'recommended_tier': 'standard',
        'target_dimensions': None,
    }
    result = execute_upgrade_plan_entry(entry)
    assert result['skill'] == 'skip'
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_image_router.py::test_load_upgrade_plan_reads_file tests/test_image_router.py::test_execute_entry_raster_returns_skill_and_provider tests/test_image_router.py::test_execute_entry_vector_returns_icon_skill tests/test_image_router.py::test_execute_entry_no_upgrade_returns_skip tests/test_image_router.py::test_load_upgrade_plan_missing_file_raises -v`
Expected: FAIL — functions not defined

- [ ] **Step 3: Implement the loader and executor**

Add to `src/image_router.py`:

```python
import json


def load_upgrade_plan(deck_dir):
    """Load the expert-approved production-upgrade-plan.json.

    Args:
        deck_dir: Path to the deck working directory.

    Returns:
        dict: The parsed production upgrade plan.

    Raises:
        FileNotFoundError: If production-upgrade-plan.json does not exist.
    """
    path = os.path.join(deck_dir, 'production-upgrade-plan.json')
    if not os.path.exists(path):
        raise FileNotFoundError(f'No production-upgrade-plan.json in {deck_dir}')
    with open(path) as f:
        return json.load(f)


def execute_upgrade_plan_entry(entry):
    """Map a single upgrade plan entry to execution parameters.

    Args:
        entry: dict from the production upgrade plan entries array.

    Returns:
        dict: {skill, provider, model, width, height} for the imagegen-bridge
              to execute. width/height are None for vector_conversion and no_upgrade.
    """
    track = entry['upgrade_track']

    if track == 'no_upgrade':
        return {
            'skill': 'skip',
            'provider': entry.get('recommended_provider', 'none'),
            'model': entry.get('recommended_model', 'none'),
            'width': None,
            'height': None,
        }

    if track == 'vector_conversion':
        return {
            'skill': 'cloud-generate-icon',
            'provider': entry['recommended_provider'],
            'model': entry['recommended_model'],
            'width': None,
            'height': None,
        }

    # raster_upscale
    dims = entry.get('target_dimensions')
    width, height = None, None
    if dims and 'x' in dims:
        parts = dims.split('x')
        width, height = int(parts[0]), int(parts[1])

    return {
        'skill': 'cloud-generate-image',
        'provider': entry['recommended_provider'],
        'model': entry['recommended_model'],
        'width': width,
        'height': height,
    }
```

Also add `import os` at top if not already present (it is not — the module currently uses only `collections.namedtuple`).

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_image_router.py -v`
Expected: ALL PASS (existing 40 tests + 5 new)

- [ ] **Step 5: Commit**

```bash
git add src/image_router.py tests/test_image_router.py
git commit -m "feat: add production upgrade plan loader and executor"
```

---

### Task 3: Update Image Generation Expert Agent

**Files:**
- Modify: `.claude/agents/image-generation-expert.md`

This is the major update — the expert gains the Production Upgrade Plan responsibility, the two-track decision framework, brand compliance checks, and guardrail logic.

- [ ] **Step 1: Add Production Upgrade Plan section to the agent**

After the existing "## Style Consistency Across a Deck" section and before the end of the file, add a new major section. The key additions:

```markdown
## Production Upgrade Plan

When invoked by the Deck Conductor to produce a Production Upgrade Plan, you read the draft ImageManifest, StrategyMap, and StyleGuide, then produce a `production-upgrade-plan.json` artifact.

### Your role

You are the expert who decides which rendering engine, provider, model, and tier is optimal for each slide's production image. You reason contextually about content character, brand requirements, and cost efficiency. You do NOT use a lookup table — you evaluate each slide individually.

### Two production tracks

**Raster Track (raster_upscale):** For hero images, atmospheric backgrounds, conceptual metaphors, textures, and element images. The draft (Ollama) validated the concept; production re-renders the proven prompt at higher resolution on a cloud model.

**Vector Track (vector_conversion):** For diagrams, flowcharts, process flows, icon grids, and architecture visuals. The draft (Ollama/FLUX) validated the concept; production generates a completely new SVG via Recraft V4. This is a format change, not a resolution bump — SVG is resolution-independent.

### Track classification

| Content nature | Track | Signals |
|---|---|---|
| Diagrams, flowcharts, process flows | vector_conversion | strategy: composed, visual_type: diagram |
| Icons, icon grids | vector_conversion | visual_type: icon_set |
| Hero images, scene illustrations | raster_upscale | strategy: full_render, background, backdrop |
| Atmospheric textures, patterns | raster_upscale | visual_type: pattern_background |
| Element images | raster_upscale | strategy: pragmatic_composition |
| Data charts | no_upgrade | Already production quality (matplotlib) |

### Raster provider selection

Evaluate the content character of each slide and recommend accordingly:

| Content character | First choice | Why |
|---|---|---|
| Photorealistic scenes, people | GPT Image medium ($0.034-0.051) | Strongest photorealism |
| Abstract, artistic, bold colour | FLUX Pro ($0.03) | Best prompt adherence, artistic flair |
| Text embedded in image | Nanobanana Flash ($0.067) | Native multimodal text handling |
| Complex scene, high detail | Nanobanana Flash ($0.067) | Strong scene composition |
| Brand-critical colour accuracy | GPT Image or Nanobanana | Better colour fidelity than FLUX |

### Vector tier selection

- Default: Recraft standard ($0.08) — sufficient for most diagrams and icons
- Recommend pro ($0.30) if: Speaker pre-selects, diagram has 10+ elements, or you judge the content is architecturally complex with many overlapping relationships

### "Try cheap first" principle

For both Nanobanana (Flash/Pro) and Recraft (standard/pro), always recommend the cheaper tier first. The presentation-reviewer will evaluate the result and may recommend escalation. You do not pre-emptively choose the expensive tier unless the content clearly warrants it or the Speaker has requested it.

### Brand compliance

- Read the StyleGuide palette before making recommendations
- If a slide features brand-critical colours in prominent positions (backgrounds, large shapes), note this in `brand_notes` and prefer providers with better colour fidelity
- If the brand uses a specific illustration style (flat, isometric, photorealistic), factor this into provider choice

### Guardrail checks

When the Speaker overrides your recommendations:
- **Warn but don't block** — you are advisory, the Speaker decides
- Flag specific concerns: wrong model for content type, resolution beyond model capability, unnecessarily expensive tier for simple content
- Add warnings to the plan entry and confirm before the plan is executed
- Example: "Ollama z-image-turbo is unreliable at 4K resolution — recommend a cloud provider instead. Proceed anyway?"

### Output format

Produce a JSON file conforming to `src/schemas/production_upgrade_plan.schema.json` and save it to `{deck_dir}/production-upgrade-plan.json`.

Present the plan to the Deck Conductor (who presents it to the Speaker) as a summary table:

| Slide | Track | Provider | Tier | Est. Cost | Reasoning |
|-------|-------|----------|------|-----------|-----------|

Include total estimated cost at the bottom.
```

- [ ] **Step 2: Verify the agent file parses correctly**

Run: `head -5 .claude/agents/image-generation-expert.md` — confirm frontmatter is intact.

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/image-generation-expert.md
git commit -m "feat: add Production Upgrade Plan responsibility to image-generation-expert"
```

---

### Task 4: Update Presentation Reviewer Agent — Post-Production Verdicts

**Files:**
- Modify: `.claude/agents/presentation-reviewer.md`

- [ ] **Step 1: Add post-production quality gate section**

After the existing "## Escalation Triggers" section, add:

```markdown
## Post-Production Quality Gate

After production images are rendered, the Deck Conductor may invoke you for a per-slide quality assessment. You evaluate each production image and return a verdict.

### Raster image assessment
- **Visual metaphor clarity** — does the image communicate the intended message?
- **Colour fidelity** — does the output match the brand palette from the StyleGuide?
- **Resolution/detail** — any artefacts, blurriness, banding, or muddy areas?
- **Text legibility** — for slides with text-in-image, is the text readable?

### Vector image assessment (Recraft SVG)
- **Diagram readability** — are labels legible, lines clean, shapes distinct?
- **Complexity threshold** — too many overlapping elements? Text collisions?
- **Geometric consistency** — are shapes aligned, spacing even?

### Per-slide verdicts

For each slide, return one of:
- `pass` — production quality, no action needed
- `escalate_tier` — same provider, higher tier recommended. Include which tier to escalate to (e.g., "Recraft standard → pro", "Nanobanana Flash → Pro")
- `escalate_provider` — different provider recommended. Include which provider and why (e.g., "FLUX → GPT Image for better colour fidelity on this photorealistic content")
- `flag_for_speaker` — subjective issue that requires Speaker judgement

**Never auto-escalate.** All escalation recommendations go to the Deck Conductor, who presents them to the Speaker for approval.

### Verdict output format

Return verdicts as a structured list:

| Slide | Image ID | Verdict | Detail |
|-------|----------|---------|--------|
| 1 | slide-01-hero | pass | Production quality achieved |
| 4 | slide-04-diagram | escalate_tier | Recraft standard → pro: 12 elements causing label overlap |
| 7 | slide-07-bg | flag_for_speaker | Colour temperature warmer than brand palette — may be intentional |
```

- [ ] **Step 2: Verify the agent file parses correctly**

Run: `head -5 .claude/agents/presentation-reviewer.md` — confirm frontmatter is intact.

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/presentation-reviewer.md
git commit -m "feat: add post-production quality verdicts to presentation-reviewer"
```

---

### Task 5: Update Deck Conductor — Production Upgrade Flow

**Files:**
- Modify: `.claude/agents/deck-conductor.md`

- [ ] **Step 1: Update the Draft/Production Lifecycle section**

In the existing "### Draft/Production Lifecycle" section, after the "If the Speaker approves:" block and the `set_phase('./tmp/deck', 'production')` code, replace the line "Then re-run Steps 5-8 at production quality." with the new production flow:

```markdown
Then execute the production upgrade flow:

#### Production Step A: Production Upgrade Plan

Invoke the image-generation-expert agent to produce a Production Upgrade Plan:

> "Review the draft ImageManifest, StrategyMap, and StyleGuide. Produce a production-upgrade-plan.json that recommends the optimal rendering engine, provider, model, and tier for each slide. Save it to ./tmp/deck/production-upgrade-plan.json."

The expert will produce a plan with two tracks:
- **raster_upscale** — re-render at higher resolution on a cloud model (FLUX Pro, GPT Image, Nanobanana Flash/Pro)
- **vector_conversion** — generate SVG via Recraft V4 (standard or pro tier)
- **no_upgrade** — already production quality (matplotlib charts)

**ESCALATE:** Present the Production Upgrade Plan to the Speaker as a table with per-slide reasoning and total estimated cost. The Speaker can:
- Approve the plan as-is
- Override individual slide choices (provider, tier, model)
- Request changes to the overall budget approach

If the Speaker overrides with a questionable choice, the expert will have added warnings — relay these and confirm before proceeding.

Log approval:
```bash
source .venv/bin/activate && python3 -c "
from src.conductor import log_speaker_approval
log_speaker_approval('./tmp/deck', 'production_plan_approved', 'Speaker approved production upgrade plan')
"
```

#### Production Step B: Execute Production Renders

Invoke `/imagegen-bridge` in production mode. The bridge reads `production-upgrade-plan.json` and executes each entry mechanically:
- `raster_upscale` entries → `cloud-generate-image` with the specified provider/model/tier
- `vector_conversion` entries → `cloud-generate-icon` with Recraft endpoint
- `no_upgrade` entries → skip

#### Production Step C: Post-Production Quality Gate

Invoke the presentation-reviewer agent for a per-slide quality assessment of the production images:

> "Review each production image against the brand palette and content requirements. Return a per-slide verdict: pass, escalate_tier, escalate_provider, or flag_for_speaker."

**If any verdicts are escalate_tier or escalate_provider:**
**ESCALATE:** Present the escalation recommendations to the Speaker:
> "The reviewer recommends upgrading these slides to a higher tier/provider: [table]. Estimated additional cost: $X.XX. Would you like to proceed with these upgrades?"

If approved, re-render only the escalated slides and re-run assembly.

**If all verdicts are pass:** Proceed to assembly.

#### Production Step D: Assembly and Final QA

Re-run Steps 6-8 (assembly, QA, review) with the production images.
```

- [ ] **Step 2: Add Production Upgrade Plan approval to escalated decisions table**

In the "## Escalated Decisions (Must Ask Speaker)" table, add:

```markdown
| Production upgrade plan approval | Expert recommendations involve spending money |
| Post-production escalation approval | Reviewer recommends higher tier/provider |
```

- [ ] **Step 3: Verify the agent file parses correctly**

Run: `head -5 .claude/agents/deck-conductor.md` — confirm frontmatter is intact.

- [ ] **Step 4: Commit**

```bash
git add .claude/agents/deck-conductor.md
git commit -m "feat: add production upgrade flow to deck-conductor"
```

---

### Task 6: Update Imagegen-Bridge Skill — Production Plan Execution

**Files:**
- Modify: `.claude/skills/imagegen-bridge/SKILL.md`

- [ ] **Step 1: Add production plan execution section**

After the existing "## Step 9: Track Budget" section (before Step 9.5), add:

```markdown
## Step 9A: Production Mode — Execute Upgrade Plan

In production mode, the imagegen-bridge reads `production-upgrade-plan.json` instead of computing routing decisions. The image-generation-expert agent has already determined the optimal engine for each slide.

```bash
source .venv/bin/activate && python3 -c "
from src.image_router import load_upgrade_plan, execute_upgrade_plan_entry
import json

plan = load_upgrade_plan('./tmp/deck')
for entry in plan['entries']:
    params = execute_upgrade_plan_entry(entry)
    print(f'Slide {entry[\"slide_number\"]}: {params[\"skill\"]} via {params[\"provider\"]} ({params[\"model\"]})')
"
```

For each entry:

### raster_upscale entries

Invoke `cloud-generate-image` with the plan's provider, model, and dimensions:

```bash
/cloud-generate-image "DRAFT_PROMPT" --provider PROVIDER --model MODEL --width WIDTH --height HEIGHT --output ./tmp/deck/images/slide-NN-hero.png
```

The draft prompt is carried from the draft ImageManifest via the plan's `draft_prompt` field. Use it directly — it was already validated during drafting.

### vector_conversion entries

Invoke `cloud-generate-icon` with Recraft:

```bash
/cloud-generate-icon "DRAFT_PROMPT" --provider recraft --output ./tmp/deck/images/slide-NN-diagram.svg
```

The output is SVG. The assembler's existing SVG rasterisation path (`src/process_image.py`) handles conversion to PNG at the target slide resolution for embedding in the .pptx.

### no_upgrade entries

Skip — the existing draft image is already production quality (matplotlib chart or similar).
```

- [ ] **Step 2: Update the existing Step 5 (production mode note)**

In the existing "## Step 5: Route Slides" section, add a note at the top:

```markdown
**Production mode:** If `production-upgrade-plan.json` exists in the deck directory, skip this step and use Step 9A instead. The upgrade plan takes precedence over the routing matrix for production renders.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/imagegen-bridge/SKILL.md
git commit -m "feat: add production plan execution path to imagegen-bridge"
```

---

### Task 7: Update ROUTING_MATRIX with Vector Track Entries

**Files:**
- Modify: `src/image_router.py`
- Modify: `tests/test_image_router.py`

The draft routing matrix currently sends diagrams to `ollama-diagram`. This stays for drafting. But we need to add `diagram` to `_UPGRADEABLE_VISUAL_TYPES` so the backward-compatible `plan_production_upgrade()` also handles it (for anyone still calling the old function). We also update the production routing for diagrams to prefer Recraft.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_image_router.py`:

```python
def test_diagram_is_upgradeable():
    from src.image_router import _UPGRADEABLE_VISUAL_TYPES
    assert 'diagram' in _UPGRADEABLE_VISUAL_TYPES


def test_production_diagram_routes_to_recraft():
    slide = {'slide_number': 1, 'visual_type': 'diagram'}
    providers = {
        'ollama': {'available': True, 'models': ['x/flux2-klein']},
        'recraft': {'available': True, 'model': 'recraft-v4'},
    }
    decision = route_slide(slide, 'production', providers, 'allow')
    assert decision.provider == 'recraft'
    assert decision.skill == 'cloud-generate-icon'
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_image_router.py::test_diagram_is_upgradeable tests/test_image_router.py::test_production_diagram_routes_to_recraft -v`
Expected: FAIL

- [ ] **Step 3: Update the routing matrix and upgradeable set**

In `src/image_router.py`:

1. Add `'diagram'` to `_UPGRADEABLE_VISUAL_TYPES`:

```python
_UPGRADEABLE_VISUAL_TYPES = {'hero_image', 'pattern_background', 'icon_set', 'diagram'}
```

2. Update the `('diagram', 'production')` entry in `ROUTING_MATRIX`:

```python
    ('diagram', 'production'): [
        RoutingTarget('cloud-generate-icon', 'recraft', 'recraft-v4-svg', 0.08),
        RoutingTarget('ollama-diagram', 'ollama', 'x/flux2-klein', 0.00),
    ],
```

- [ ] **Step 4: Run all image_router tests**

Run: `.venv/bin/pytest tests/test_image_router.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/image_router.py tests/test_image_router.py
git commit -m "feat: add diagram to upgradeable types, route production diagrams to Recraft"
```

---

### Task 8: Integration Test — Full Plan Load and Execute Cycle

**Files:**
- Modify: `tests/test_image_router.py`

- [ ] **Step 1: Write an integration test**

Add to `tests/test_image_router.py`:

```python
def test_full_plan_load_and_execute_cycle(tmp_path):
    """Integration: write a plan, load it, execute each entry, verify routing."""
    plan = {
        'created_at': '2026-03-31T12:00:00Z',
        'deck_dir': str(tmp_path),
        'total_estimated_cost_usd': 0.19,
        'entries': [
            {
                'slide_number': 1,
                'image_id': 'slide-01-hero',
                'upgrade_track': 'raster_upscale',
                'recommended_provider': 'fal',
                'recommended_model': 'flux-2-pro',
                'recommended_tier': 'standard',
                'target_dimensions': '1920x1080',
                'estimated_cost_usd': 0.03,
                'reasoning': 'Abstract hero',
                'brand_notes': None,
                'warnings': [],
                'draft_prompt': 'A dramatic wave',
            },
            {
                'slide_number': 4,
                'image_id': 'slide-04-diagram',
                'upgrade_track': 'vector_conversion',
                'recommended_provider': 'recraft',
                'recommended_model': 'recraft-v4-svg',
                'recommended_tier': 'standard',
                'target_dimensions': None,
                'estimated_cost_usd': 0.08,
                'reasoning': 'Flowchart — clean vector',
                'brand_notes': None,
                'warnings': [],
                'draft_prompt': 'A flowchart showing data pipeline',
            },
            {
                'slide_number': 7,
                'image_id': 'slide-07-chart',
                'upgrade_track': 'no_upgrade',
                'recommended_provider': 'local',
                'recommended_model': 'matplotlib',
                'recommended_tier': 'standard',
                'target_dimensions': None,
                'estimated_cost_usd': 0.0,
                'reasoning': 'Already production quality',
                'brand_notes': None,
                'warnings': [],
                'draft_prompt': None,
            },
            {
                'slide_number': 10,
                'image_id': 'slide-10-hero',
                'upgrade_track': 'raster_upscale',
                'recommended_provider': 'google',
                'recommended_model': 'gemini-3.1-flash-image-preview',
                'recommended_tier': 'flash',
                'target_dimensions': '1920x1080',
                'estimated_cost_usd': 0.067,
                'reasoning': 'Text-in-image scene',
                'brand_notes': 'Primary blue #2B6CB0 — Nanobanana reliable for blues',
                'warnings': [],
                'draft_prompt': 'A scene with embedded labels',
            },
        ],
    }

    # Write the plan
    plan_path = tmp_path / 'production-upgrade-plan.json'
    plan_path.write_text(json.dumps(plan))

    # Load and execute
    loaded = load_upgrade_plan(str(tmp_path))
    results = [execute_upgrade_plan_entry(e) for e in loaded['entries']]

    # Verify routing
    assert results[0]['skill'] == 'cloud-generate-image'
    assert results[0]['provider'] == 'fal'
    assert results[0]['width'] == 1920

    assert results[1]['skill'] == 'cloud-generate-icon'
    assert results[1]['provider'] == 'recraft'
    assert results[1]['width'] is None

    assert results[2]['skill'] == 'skip'

    assert results[3]['skill'] == 'cloud-generate-image'
    assert results[3]['provider'] == 'google'
    assert results[3]['model'] == 'gemini-3.1-flash-image-preview'
```

- [ ] **Step 2: Run the test**

Run: `.venv/bin/pytest tests/test_image_router.py::test_full_plan_load_and_execute_cycle -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_image_router.py
git commit -m "test: integration test for production upgrade plan load-execute cycle"
```

---

### Task 9: Run Full Test Suite

**Files:** None (verification only)

- [ ] **Step 1: Run all Python tests**

Run: `.venv/bin/pytest tests/ -v`
Expected: ALL PASS (491 existing + ~11 new = ~502 tests)

- [ ] **Step 2: Verify no regressions in existing upgrade tests**

Run: `.venv/bin/pytest tests/test_image_router.py -v -k "upgrade"`
Expected: ALL existing upgrade tests still pass — `plan_production_upgrade()` is unchanged, just augmented with new functions alongside it.

---

### Task 10: Update CLAUDE.md — Test Count and Implementation Table

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update test count**

Update the "All Phases COMPLETE" line to reflect the new test count (verify exact number from Task 9 output).

- [ ] **Step 2: Add production upgrade plan to implementation table**

Add row:

```markdown
| Production upgrade plan | `src/image_router.py`, `src/schemas/` | ~11 | Done |
```

- [ ] **Step 3: Update the pipeline description**

In the "Full Pipeline" section, after the existing pipeline description, add:

```markdown
- **Production Upgrade:** Expert-advised two-track system — raster_upscale (FLUX Pro, GPT Image, Nanobanana Flash/Pro) and vector_conversion (Recraft V4 standard/pro). Try cheap tier first, reviewer evaluates, escalate if needed.
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with production rendering engine status"
```
