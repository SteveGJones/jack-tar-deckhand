# Image Reviewer Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create an image-reviewer agent that assesses generated images for quality defects in its own isolated context, returning a compact text verdict so the main orchestration context never holds images.

**Architecture:** New `.claude/agents/image-reviewer.md` agent dispatched by the imagegen-bridge after each image generation. Returns flat JSON verdict (pass/refine). Image manifest schema extended with `review_summary` field and `accepted_with_issues` status. BSA canonical model updated with 5th AI persona.

**Tech Stack:** Claude Code agent (markdown), JSON Schema, Python (jsonschema for tests)

**Spec:** `docs/superpowers/specs/2026-04-01-image-reviewer-agent-design.md`

---

### Task 1: Create the image-reviewer agent

**Files:**
- Create: `.claude/agents/image-reviewer.md`

- [ ] **Step 1: Create the agent file**

```markdown
---
name: image-reviewer
description: Assesses generated images for quality defects — artifacts, garbled text, wrong subject, palette drift, composition problems. Returns a pass/refine verdict with issues list. Read-only — never modifies files, generates images, or refines prompts.
model: haiku
tools: Read
---

# Image Reviewer

You are a visual quality reviewer for AI-generated presentation images. You receive an image path, the intended visual direction, and the brand palette. You assess the image and return a structured JSON verdict.

## Identity

| Field | Value |
|---|---|
| Persona ID | `persona-image-reviewer` |
| Service ID | `image-image-reviewer` |
| Authority Model | Invoker (acts on behalf of imagegen-bridge) |
| Escalation Target | Deck Conductor |
| Confidence Minimum | 0.7 |

## Prohibited Actions

- Must not generate or modify images
- Must not refine or suggest prompts (image-generation-expert's role)
- Must not write to DeckContext or manifest files
- Must not communicate with Speaker directly

## Process

1. Read the image at the provided path using the Read tool
2. Assess against the five criteria below
3. Return JSON only — no markdown, no preamble, no explanation outside the JSON

## Assessment Criteria

Check in this order. Any issue on criterion 1 is an automatic "refine".

1. **Artifacts** — garbled text, extra limbs, impossible geometry, colour bleed, mutations, distorted faces, floating objects disconnected from scene
2. **Subject match** — does the image depict what the visual_direction describes? Check key subjects, composition, and mood
3. **Palette compliance** — are the dominant colours within reasonable distance of the brand palette? Minor shade variations are acceptable; completely wrong colour families are not
4. **Composition** — for backdrop/background strategies: are there clear open areas for text overlay? For full_render: does the image work as a standalone visual?
5. **Strategy fit** — full_render should be dramatic and complete; element images should have identifiable subjects at small display size; background images should be atmospheric, not competing with text

## Output Format

Return ONLY this JSON structure. No other text.

### When the image passes:

```json
{
  "verdict": "pass",
  "confidence": 0.9,
  "issues": [],
  "summary": "One sentence describing what works"
}
```

### When the image needs refinement:

```json
{
  "verdict": "refine",
  "confidence": 0.85,
  "issues": [
    "specific actionable observation 1",
    "specific actionable observation 2"
  ],
  "summary": "One sentence summary of the core problem"
}
```

### Field definitions:

- **verdict**: `"pass"` or `"refine"` — binary, no ambiguity
- **confidence**: 0.0–1.0 — how certain you are of the assessment
- **issues**: array of strings — each a specific, actionable observation. Empty on pass. Be concrete: "garbled text at top-center" not "text issues"
- **summary**: one sentence — this is what the calling context keeps. Make it informative enough to guide the next action without seeing the image again

## Examples

**Input:**
```
Review this generated image for quality.
Image: ./tmp/deck/images/slide-10-scene-v1.png
Visual direction: "Side profile view of two heads facing each other — android on left, human on right"
Brand palette: #006B5E, #5CDBC0, #0E1513, #F5FBF7
Strategy: backdrop
Iteration: 1 of 10
```

**Output (refine):**
```json
{
  "verdict": "refine",
  "confidence": 0.92,
  "issues": [
    "garbled text at top of image reading 'API HEB CH HOSTAR LA2'",
    "secondary garbled text below reading 'Nanittonhoer tap'"
  ],
  "summary": "Android/human concept correct with good palette, but garbled text artifacts at top need elimination"
}
```

**Output (pass):**
```json
{
  "verdict": "pass",
  "confidence": 0.88,
  "issues": [],
  "summary": "Clean android/human profile composition, teal/mint palette matches brand, dark background with clear quadrants for text overlay"
}
```
```

- [ ] **Step 2: Verify the agent file is valid**

Run: `head -5 .claude/agents/image-reviewer.md`
Expected: YAML frontmatter with `name: image-reviewer`

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/image-reviewer.md
git commit -m "feat: add image-reviewer agent for visual quality assessment"
```

---

### Task 2: Extend image manifest schema

**Files:**
- Modify: `src/schemas/image_manifest.schema.json`
- Modify: `tests/test_schemas.py`
- Modify: `tests/fixtures/valid_image_manifest.json`

- [ ] **Step 1: Write the failing test for review_summary field**

Add to `tests/test_schemas.py` after the `test_image_manifest_accepts_element_placement` function:

```python
def test_image_manifest_accepts_review_summary():
    """ImageManifest should accept review_summary field on image entries."""
    import jsonschema
    with open('src/schemas/image_manifest.schema.json') as f:
        schema = json.load(f)
    manifest = {
        'images': [{
            'image_id': 'slide-10-scene',
            'slide_number': 10,
            'file_path': './tmp/deck/images/slide-10-scene.png',
            'status': 'generated',
            'review_summary': 'Clean android/human profile composition, brand palette matches',
        }],
    }
    jsonschema.Draft202012Validator(schema).validate(manifest)
```

- [ ] **Step 2: Write the failing test for accepted_with_issues status**

Add to `tests/test_schemas.py` after the previous test:

```python
def test_image_manifest_accepts_accepted_with_issues_status():
    """ImageManifest should accept 'accepted_with_issues' as a valid status."""
    import jsonschema
    with open('src/schemas/image_manifest.schema.json') as f:
        schema = json.load(f)
    manifest = {
        'images': [{
            'image_id': 'slide-02-bg',
            'slide_number': 2,
            'file_path': './tmp/deck/images/slide-02-bg.png',
            'status': 'accepted_with_issues',
            'review_summary': 'Minor palette drift but acceptable after 10 iterations',
        }],
    }
    jsonschema.Draft202012Validator(schema).validate(manifest)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_schemas.py::test_image_manifest_accepts_review_summary tests/test_schemas.py::test_image_manifest_accepts_accepted_with_issues_status -v`
Expected: Both FAIL — `review_summary` is not yet in schema, `accepted_with_issues` is not in status enum

- [ ] **Step 4: Update the schema**

In `src/schemas/image_manifest.schema.json`, add `review_summary` to the image item properties and `accepted_with_issues` to the status enum.

Change the properties section of the image items object — add after the `generation_time_seconds` property:

```json
"review_summary": {"type": "string"}
```

Change the status enum from:
```json
"enum": ["generated", "cached", "placeholder", "failed"]
```
to:
```json
"enum": ["generated", "cached", "placeholder", "failed", "accepted_with_issues"]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_schemas.py -v`
Expected: ALL pass (including existing tests)

- [ ] **Step 6: Commit**

```bash
git add src/schemas/image_manifest.schema.json tests/test_schemas.py
git commit -m "feat: add review_summary and accepted_with_issues to image manifest schema"
```

---

### Task 3: Update imagegen-bridge Step 7

**Files:**
- Modify: `.claude/skills/imagegen-bridge/SKILL.md`

- [ ] **Step 1: Replace the manual review cycle in Step 7**

In `.claude/skills/imagegen-bridge/SKILL.md`, find the section titled `### Per-image review cycle (MANDATORY)` inside Step 7. Replace the entire review cycle section (from `### Per-image review cycle` through the end of the iteration instructions including the common fixes list and the "Never skip review" line) with:

```markdown
### Per-image review cycle (MANDATORY)

After generating EVERY image, dispatch the `image-reviewer` agent to assess it. This keeps images out of the main orchestration context.

1. **Generate** the image with the current prompt
2. **Dispatch** the `image-reviewer` agent with:
   - Image path: the just-generated file
   - Visual direction: from outline.json for this slide
   - Brand palette: hex values from brand-profile.json
   - Strategy: from strategy-map.json for this slide
   - Element ID: from strategy-map element_layout (if applicable)
   - Iteration: current attempt number out of max (e.g., "3 of 10")

   Example dispatch:
   ```
   Review this generated image for quality.
   Image: ./tmp/deck/images/slide-10-scene-v3.png
   Visual direction: "Side profile view of two heads facing each other..."
   Brand palette: #006B5E, #5CDBC0, #0E1513, #F5FBF7
   Strategy: backdrop
   Iteration: 3 of 10
   ```

3. **Parse the JSON verdict** returned by the agent
4. **If verdict is "pass":** proceed to next image, log the summary
5. **If verdict is "refine":** use the `issues` array to guide prompt refinement, regenerate, and dispatch a new agent review
6. **Escalation:** after 3 consecutive "refine" verdicts, re-dispatch the image-reviewer at Sonnet tier for a more nuanced assessment
7. **Hard stop:** after 10 iterations total, accept the best version. Set status to `"accepted_with_issues"` in the manifest and store the final summary in `"review_summary"`
8. **Save versions** as `slide-NN-TYPE-vN.png` so the Speaker can review alternatives if needed. The final accepted version overwrites `slide-NN-TYPE.png`.

**Context savings:** The main context keeps only the `summary` string (~50 chars) per review, not the image itself. A 17-slide deck with 3 iterations each accumulates ~17 short strings instead of ~51 images.

**Never skip review.** A broken image that reaches the assembled deck wastes the Speaker's time and undermines confidence in the pipeline.
```

- [ ] **Step 2: Verify the edit**

Run: `grep -c "image-reviewer" .claude/skills/imagegen-bridge/SKILL.md`
Expected: At least 3 occurrences (agent name referenced in dispatch, escalation, context savings)

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/imagegen-bridge/SKILL.md
git commit -m "feat: integrate image-reviewer agent into imagegen-bridge Step 7"
```

---

### Task 4: Update BSA canonical model

**Files:**
- Modify: `.bsa/models/jack-tar-deckhand.json`

- [ ] **Step 1: Add the service entry**

In `.bsa/models/jack-tar-deckhand.json`, find the `image-vision-analysis` service entry (the last L2 service in Image Services, before the `assembly-qa-services` L1 block). Add the new service entry immediately after `image-vision-analysis`:

```json
    {
      "id": "image-image-reviewer",
      "name": "Image Reviewer",
      "level": 2,
      "parentId": "image-services",
      "serviceType": "core",
      "mission": "Visual quality assessment for AI-generated presentation images. Dispatched per image after generation to check for artifacts, subject match, palette compliance, composition, and strategy fit. Returns a compact pass/refine verdict so the orchestration context never holds images. Runs at Haiku tier by default, escalates to Sonnet after 3 consecutive refine verdicts.",
      "owner": "Steve Jones",
      "isAIPersona": true,
      "tags": ["l2", "agent", "ai-persona", "quality"]
    },
```

- [ ] **Step 2: Add the persona entry**

Find the `persona-presentation-reviewer` entry in the `aiPersonas` array. Add the new persona entry immediately before it:

```json
    {
      "id": "persona-image-reviewer",
      "serviceId": "image-image-reviewer",
      "description": "Visual quality reviewer for AI-generated presentation images. Dispatched per image after generation by the imagegen-bridge. Assesses against five criteria: artifacts (garbled text, mutations), subject match (vs visual_direction), palette compliance (vs brand palette), composition (open areas for text overlay), and strategy fit (standalone vs atmospheric). Returns a flat JSON verdict with pass/refine decision, confidence score, issues list, and one-line summary. Runs at Haiku tier for cost efficiency; escalates to Sonnet after 3 consecutive refine verdicts for more nuanced assessment. Never modifies images, refines prompts, or writes to DeckContext.",
      "authorityModel": "invoker",
      "confidenceThreshold": {
        "autonomousMin": 0.7,
        "escalationTarget": "persona-deck-conductor"
      },
      "scope": {
        "permitted": [
          "Read and visually assess generated image files",
          "Check for visual artifacts: garbled text, extra limbs, impossible geometry, colour bleed, mutations",
          "Assess whether image subject matches the visual_direction from the outline",
          "Check dominant colour compliance against brand palette hex values",
          "Assess composition suitability for the slide's rendering strategy",
          "Return structured JSON verdict with pass/refine decision"
        ],
        "prohibited": [
          "Must not generate or modify images",
          "Must not refine or suggest prompts — that is the image-generation-expert's role",
          "Must not write to DeckContext or manifest files",
          "Must not communicate with Speaker directly"
        ],
        "escalationTriggers": [
          "Image fails quality criteria after 3 consecutive assessments at Haiku tier — escalate to Sonnet for more nuanced review",
          "Image accepted after 10 iterations with remaining issues — flag as accepted_with_issues in manifest"
        ]
      },
      "dataSources": [
        {
          "sourceId": "content-outline-generation",
          "sourceName": "SlideOutline",
          "accessType": "read",
          "dataDescription": "visual_direction field for subject match assessment"
        },
        {
          "sourceId": "design-brand-profile-management",
          "sourceName": "BrandProfile",
          "accessType": "read",
          "dataDescription": "Brand palette hex values for colour compliance checking"
        }
      ],
      "sops": []
    },
```

- [ ] **Step 3: Add interaction entries**

Find the interactions array. Add these entries at the end of the array (before the closing `]`):

```json
    {
      "id": "int-imagegen-bridge-to-image-reviewer",
      "sourceId": "image-routing-discovery",
      "targetId": "image-image-reviewer",
      "type": "invocation",
      "description": "imagegen-bridge dispatches image-reviewer after each image generation for visual quality assessment",
      "dataFlows": ["Image path", "Visual direction", "Brand palette", "Slide strategy", "Iteration count"]
    },
    {
      "id": "int-image-reviewer-to-imagegen-bridge",
      "sourceId": "image-image-reviewer",
      "targetId": "image-routing-discovery",
      "type": "delivery",
      "description": "image-reviewer returns structured quality verdict to imagegen-bridge",
      "dataFlows": ["Verdict (pass/refine)", "Issues list", "Confidence score", "Summary"]
    }
```

- [ ] **Step 4: Update model metadata**

Update the `lastModifiedDate` field in `modelMetadata` to `"2026-04-01"` and the `version` to `"1.3.0"`.

- [ ] **Step 5: Validate JSON is well-formed**

Run: `python3 -c "import json; json.load(open('.bsa/models/jack-tar-deckhand.json')); print('Valid JSON')"`
Expected: `Valid JSON`

- [ ] **Step 6: Commit**

```bash
git add .bsa/models/jack-tar-deckhand.json
git commit -m "feat: add image-reviewer persona to BSA canonical model (v1.3.0)"
```

---

### Task 5: Update service catalogue

**Files:**
- Modify: `docs/architecture/service-catalogue.md`

- [ ] **Step 1: Read the current file**

Read `docs/architecture/service-catalogue.md` to find the Image Services table section.

- [ ] **Step 2: Add the image-reviewer row**

In the Image Services table, add a new row after the `image-generation-expert` row:

```markdown
| `image-image-reviewer` | Image Reviewer | L2 | image-services | core | **Yes** | -- (agent/quality) |
```

- [ ] **Step 3: Update the totals line**

Find the totals line that reads `4 AI Personas` and change it to `5 AI Personas`. Also increment the L2 service count by 1 and the total service count by 1.

- [ ] **Step 4: Commit**

```bash
git add docs/architecture/service-catalogue.md
git commit -m "docs: add image-reviewer to service catalogue"
```

---

### Task 6: Update AI persona summaries

**Files:**
- Modify: `docs/architecture/ai-persona-summaries.md`

- [ ] **Step 1: Read the current file**

Read `docs/architecture/ai-persona-summaries.md` to see the existing 4 persona sections and their structure.

- [ ] **Step 2: Add the 5th persona section**

Add after the section for Persona 4 (Presentation Reviewer):

```markdown
## 5. Image Reviewer

**Persona ID:** `persona-image-reviewer`
**Service ID:** `image-image-reviewer`

### Service Location

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | image-services (L1) |
| **Role** | Visual quality gate for AI-generated images |

### Description

Visual quality reviewer dispatched per image after generation by the imagegen-bridge. Assesses against five criteria (artifacts, subject match, palette compliance, composition, strategy fit) and returns a compact JSON verdict. Keeps images out of the main orchestration context — the bridge accumulates only the one-line summary strings, not the images themselves. Runs at Haiku tier for cost efficiency; escalates to Sonnet after 3 consecutive refine verdicts.

### Authority Model

| Field | Value |
|---|---|
| **Model** | Invoker |
| **Autonomous Confidence Minimum** | 0.7 |
| **Escalation Target** | persona-deck-conductor |

Acts on behalf of the imagegen-bridge. Returns verdicts directly to the bridge, which decides whether to iterate, escalate, or accept.

### Scope: Permitted Actions

- Read and visually assess generated image files
- Check for visual artifacts (garbled text, mutations, impossible geometry)
- Assess subject match against visual_direction from outline
- Check dominant colour compliance against brand palette
- Assess composition suitability for slide rendering strategy
- Return structured JSON verdict (pass/refine)

### Scope: Prohibited Actions

- Must not generate or modify images
- Must not refine or suggest prompts (image-generation-expert's role)
- Must not write to DeckContext or manifest files
- Must not communicate with Speaker directly

### Escalation Triggers

1. Image fails quality criteria after 3 consecutive Haiku assessments — escalate to Sonnet tier
2. Image accepted after 10 iterations with remaining issues — flag as accepted_with_issues

### Data Sources

| Source | Name | Access | Description |
|---|---|---|---|
| `content-outline-generation` | SlideOutline | read | visual_direction for subject match |
| `design-brand-profile-management` | BrandProfile | read | Palette hex values for colour compliance |

### Key Interactions

| Direction | Target | Type | Data |
|---|---|---|---|
| Receives from | imagegen-bridge | invocation | Image path, visual direction, palette, strategy, iteration |
| Returns to | imagegen-bridge | delivery | Verdict, issues, confidence, summary |
```

- [ ] **Step 3: Update the document title/count if mentioned**

If the document mentions "Four AI Personas" in its title or introduction, change to "Five AI Personas".

- [ ] **Step 4: Commit**

```bash
git add docs/architecture/ai-persona-summaries.md
git commit -m "docs: add image-reviewer to AI persona summaries"
```

---

### Task 7: Update architecture overview and CLAUDE.md

**Files:**
- Modify: `docs/architecture/architecture-overview.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Read architecture-overview.md**

Read `docs/architecture/architecture-overview.md` to find persona count references.

- [ ] **Step 2: Update architecture-overview.md**

Change all references from `4 AI Personas` to `5 AI Personas`. Update the persona list section — add:

```markdown
### 5. Image Reviewer (L2 — Quality)
```

with a one-line description: `Visual quality gate for generated images. Dispatched per image, returns pass/refine verdict. Haiku default, Sonnet escalation.`

Update the L2 service count (increment by 1) and total service count.

- [ ] **Step 3: Update CLAUDE.md**

In `CLAUDE.md`, find and update:
- `4 AI Personas` → `5 AI Personas`
- `4 L1 Services` remains unchanged (the reviewer is L2, not L1)
- The persona count in the Architecture Summary section
- Add a row to the Implementation Status table:

```markdown
| Image reviewer agent | `.claude/agents/image-reviewer.md` | -- | Done |
```

- [ ] **Step 4: Commit**

```bash
git add docs/architecture/architecture-overview.md CLAUDE.md
git commit -m "docs: update persona count to 5 across architecture docs"
```

---

### Task 8: Update L1 Image Service diagram

**Files:**
- Modify: `docs/architecture/diagrams/l1-image-services.svg` (or the appropriate Image Service diagram)

- [ ] **Step 1: Read the current diagram file**

Read the Image Services L1 diagram SVG to understand the layout and how existing services are positioned.

- [ ] **Step 2: Add the image-reviewer node**

Add a new SVG rectangle and text label for "Image Reviewer" positioned alongside the other L2 services in the Image Services group. Use the same styling as `image-generation-expert` (it's also an AI persona). Add an arrow from `image-routing-discovery` (imagegen-bridge) to the new node.

Follow the existing SVG conventions:
- Same fill colour as other AI persona boxes
- Same font size and family
- Label: `Image Reviewer`
- Dashed or special border if that's the convention for AI personas

- [ ] **Step 3: Verify the SVG renders**

Open the SVG in a browser to verify it renders correctly with the new node.

- [ ] **Step 4: Commit**

```bash
git add docs/architecture/diagrams/l1-image-services.svg
git commit -m "docs: add image-reviewer to L1 Image Services diagram"
```

---

### Self-Review

**Spec coverage check:**
- Agent identity & authority → Task 1 ✓
- Input contract → Task 1 (agent prompt) + Task 3 (bridge dispatch) ✓
- Output contract → Task 1 (agent examples) ✓
- Assessment criteria → Task 1 (agent criteria section) ✓
- Integration with imagegen-bridge → Task 3 ✓
- Manifest integration → Task 2 (schema + tests) ✓
- BSA updates → Tasks 4-8 ✓

**Placeholder scan:** No TBD, TODO, or "fill in later" found.

**Type consistency:** `review_summary` used consistently in schema (Task 2), agent output (Task 1), and bridge integration (Task 3). `accepted_with_issues` used consistently in schema enum (Task 2) and bridge flow (Task 3). `verdict`, `confidence`, `issues`, `summary` field names match between agent output format (Task 1) and bridge parsing (Task 3).
