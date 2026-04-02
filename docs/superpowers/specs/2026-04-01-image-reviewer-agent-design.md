# Image Reviewer Agent Design

> **For agentic workers:** This spec defines the image-reviewer AI Persona for Jack-Tar Deckhand.

**Goal:** A lightweight subagent that visually assesses generated images for quality defects, returning a compact text verdict so the main orchestration context never needs to hold images.

**Problem:** The imagegen-bridge's Step 7 review loop currently requires the main context to read and assess every generated image. With a 17-slide deck and up to 10 iterations per image, this rapidly exhausts the context window. The images are large but the useful output (pass/refine + a sentence of explanation) is tiny.

**Solution:** A dedicated image-reviewer agent dispatched per image. It reads the image in its own isolated context, returns a flat JSON verdict (~200 bytes), and its context is discarded. The main context accumulates only the verdict strings.

---

## Agent Identity

| Field | Value |
|-------|-------|
| Name | `image-reviewer` |
| Description | Assesses generated images for quality defects — artifacts, garbled text, wrong subject, palette drift, composition problems. Returns a pass/refine verdict with issues list. Read-only. |
| Model | Haiku (default), Sonnet (escalation) |
| Tools | `Read` only |
| Authority Model | Invoker (acts on behalf of imagegen-bridge) |
| Escalation Target | Deck Conductor |
| Confidence Minimum | 0.7 |

### Prohibited Actions

- Must not generate or modify images
- Must not refine prompts (image-generation-expert's role)
- Must not write to DeckContext or manifest files
- Must not communicate with Speaker directly

---

## Input Contract

The imagegen-bridge constructs the dispatch prompt with these fields:

| Input | Source | Purpose |
|-------|--------|---------|
| `image_path` | The just-generated image file | What to review |
| `visual_direction` | From outline.json for this slide | What the image should depict |
| `brand_palette` | From brand-profile.json | Hex colours to check against |
| `slide_strategy` | From strategy-map.json | Context: full_render / background / backdrop / pragmatic_composition / composed |
| `element_id` | From strategy-map element_layout (if applicable) | Which element this image is for |
| `iteration` | Current iteration number (1-10) | Context for strictness |

Example dispatch prompt:

```
Review this generated image for quality.
Image: ./tmp/deck/images/slide-10-scene-v3.png
Visual direction: "Side profile view of two heads facing each other..."
Brand palette: #006B5E, #5CDBC0, #0E1513, #F5FBF7
Strategy: backdrop
Iteration: 3 of 10
```

---

## Output Contract

The agent returns **JSON only** — no markdown, no preamble (same pattern as vision-analyst).

### Pass example:

```json
{
  "verdict": "pass",
  "confidence": 0.9,
  "issues": [],
  "summary": "Android/human heads correctly positioned, brand palette matches, no artifacts"
}
```

### Refine example:

```json
{
  "verdict": "refine",
  "confidence": 0.85,
  "issues": [
    "garbled text artifacts at top-center of image",
    "background is medium grey, should be dark teal (#0E1513)"
  ],
  "summary": "Concept is correct (android + human heads) but garbled text and wrong background colour"
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `verdict` | `"pass"` or `"refine"` | Binary decision — no ambiguity |
| `confidence` | 0.0–1.0 | How certain the agent is of its assessment |
| `issues` | string[] | Specific, actionable observations. Empty array on pass. |
| `summary` | string | One sentence — what the main context keeps |

---

## Assessment Criteria

Checked in order. Any issue on criterion 1 is an automatic `"refine"`.

1. **Artifacts** — garbled text, extra limbs, impossible geometry, colour bleed, mutations
2. **Subject match** — does the image depict what the visual_direction describes?
3. **Palette compliance** — dominant colours within reasonable distance of brand palette
4. **Composition** — for backdrop/background strategies, are there clear open areas for text overlay?
5. **Strategy fit** — full_render should work standalone; element images should be identifiable at small size

Criteria 2–5 require judgement — mild deviations can pass if the overall image works.

---

## Integration with imagegen-bridge

### New Step 7 flow

1. Generate image
2. Dispatch `image-reviewer` agent at Haiku tier with input contract
3. Receive flat JSON verdict (~200 bytes in main context)
4. If `"pass"` — proceed, log summary
5. If `"refine"` — use `issues` to guide prompt refinement, regenerate, dispatch new agent
6. After 3 consecutive `"refine"` verdicts — escalate to Sonnet tier for more nuanced assessment
7. After 10 iterations total — stop, accept best version, flag in manifest as `"status": "accepted_with_issues"`

### Context savings

The main context keeps only the `summary` string and `verdict` per image per iteration. A 17-slide deck with 3 iterations each accumulates ~17 short strings instead of ~51 images.

### Manifest integration

The accepted image's final verdict summary is stored in the manifest entry as `"review_summary"` alongside the existing `"source_prompt"` field.

---

## BSA Architecture Updates

The image-reviewer becomes the 5th AI Persona in the canonical model.

| BSA Field | Value |
|-----------|-------|
| Persona ID | `persona-image-reviewer` |
| Service ID | `image-image-reviewer` |
| Parent L1 Service | Image Service |
| Authority Model | Invoker |
| Escalation Target | Deck Conductor |

### Artifacts to update

1. **Canonical model** — `.bsa/models/jack-tar-deckhand.json` — add persona definition, service entry, interactions (imagegen-bridge -> image-reviewer)
2. **Service catalogue** — `docs/architecture/service-catalogue.md` — add image-reviewer row
3. **AI persona summaries** — `docs/architecture/ai-persona-summaries.md` — add 5th persona section
4. **L1 Image Service diagram** — `docs/architecture/diagrams/` — add image-reviewer to Image Service SVG
5. **Architecture overview** — `docs/architecture/architecture-overview.md` — update persona count from 4 to 5
6. **CLAUDE.md** — update persona count and test counts

### Interaction pattern

The imagegen-bridge dispatches the image-reviewer after each generation. The image-reviewer returns a verdict. The bridge acts on it. Standard Invoker pattern — same as the bridge dispatching vision-analyst and prompt-engineer.
