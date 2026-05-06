# Cross-Tier Prompt Refinement Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a prompt refinement loop that iterates on prompt quality at the cheap tier (Flash) before spending money on the expensive tier (Pro), with structured reviewer-to-prompt-engineer communication.

**Architecture:** Three existing markdown protocol files extended — no new Python modules. The image-reviewer agent gains `strengths[]` and `composition_notes{}` output fields. The prompt-engineer agent gains a "refinement mode" that preserves what works while fixing what's broken. The imagegen-bridge skill orchestrates the loop in Step 9A.

**Tech Stack:** Claude Code agent definitions (`.claude/agents/*.md`), skill protocols (`SKILL.md`). No Python code changes.

---

## Task 1: Extend image-reviewer output schema

Add `strengths[]`, `issues[]` (already exists but reinforce), and `composition_notes{}` to the image-reviewer agent's output format. The reviewer already sees the image and the intent — it just needs to structure its observations into "preserve" vs "fix" categories.

**Files:**
- Modify: `plugins/jack-tar-deckhand/agents/image-reviewer.md:63-98` (Output Format section)

- [ ] **Step 1: Update the Output Format section**

In `plugins/jack-tar-deckhand/agents/image-reviewer.md`, replace the Output Format section (lines 63–98) with the extended version. The key additions are `strengths[]` and `composition_notes{}`.

Replace the current block from `## Output Format` through the `summary` field definition (lines 63–98) with:

```markdown
## Output Format

Return ONLY this JSON structure. No other text.

### When the image passes:

```json
{
  "verdict": "pass",
  "confidence": 0.9,
  "strengths": [
    "Speaker is dominant figure, left third of frame",
    "Warm/cool lighting contrast works well"
  ],
  "issues": [],
  "composition_notes": {
    "subject_placement": "speaker left foreground — correct",
    "scale_hierarchy": "speaker dominates frame as intended",
    "text_rendering": "no text requested, none present"
  },
  "summary": "One sentence describing what works"
}
```

### When the image needs refinement:

```json
{
  "verdict": "refine",
  "confidence": 0.85,
  "strengths": [
    "Speaker is dominant figure, left third of frame",
    "Warm/cool lighting contrast between factory and stage"
  ],
  "issues": [
    "Factory section labels are illegible",
    "Captain is too prominent — same scale as speaker"
  ],
  "composition_notes": {
    "subject_placement": "speaker left foreground — correct",
    "scale_hierarchy": "speaker and captain similar size — wrong",
    "text_rendering": "banner OK, section labels failed"
  },
  "summary": "One sentence summary of the core problem"
}
```

### Field definitions:

- **verdict**: `"pass"` or `"refine"` — binary, no ambiguity
- **confidence**: 0.0–1.0 — how certain you are of the assessment
- **strengths**: array of strings — what the image got RIGHT. Be specific about composition, colour, subject placement. These are preserved during prompt refinement. Always populated, even on refine verdicts.
- **issues**: array of strings — each a specific, actionable observation. Empty on pass. Be concrete: "garbled text at top-center" not "text issues"
- **composition_notes**: object with three optional keys describing spatial relationships:
  - `subject_placement`: where the main subject is and whether that's correct
  - `scale_hierarchy`: relative sizes of elements and whether the hierarchy is right
  - `text_rendering`: which text rendered well and which failed
- **summary**: one sentence — this is what the calling context keeps. Make it informative enough to guide the next action without seeing the image again
```

- [ ] **Step 2: Update the examples**

Replace the existing examples section (lines 99–132) to include the new fields:

```markdown
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
  "strengths": [
    "Android/human dual profile concept correctly depicted",
    "Teal and mint palette matches brand within acceptable range",
    "Dark background provides clear contrast"
  ],
  "issues": [
    "garbled text at top of image reading 'API HEB CH HOSTAR LA2'",
    "secondary garbled text below reading 'Nanittonhoer tap'"
  ],
  "composition_notes": {
    "subject_placement": "profiles centered, facing each other — correct",
    "scale_hierarchy": "both heads similar size — appropriate for this concept",
    "text_rendering": "garbled text artifacts at top need elimination"
  },
  "summary": "Android/human concept correct with good palette, but garbled text artifacts at top need elimination"
}
```

**Output (pass):**
```json
{
  "verdict": "pass",
  "confidence": 0.88,
  "strengths": [
    "Clean android/human profile composition",
    "Teal/mint palette matches brand",
    "Dark background with clear quadrants for text overlay"
  ],
  "issues": [],
  "composition_notes": {
    "subject_placement": "profiles centered, symmetrical framing",
    "scale_hierarchy": "both profiles equal prominence — correct for concept",
    "text_rendering": "no text present — correct for backdrop strategy"
  },
  "summary": "Clean android/human profile composition, teal/mint palette matches brand, dark background with clear quadrants for text overlay"
}
```
```

- [ ] **Step 3: Commit**

```bash
git add plugins/jack-tar-deckhand/agents/image-reviewer.md
git commit -m "feat: extend image-reviewer output with strengths and composition_notes"
```

---

## Task 2: Add refinement mode to prompt-engineer agent

Add a second operating mode to the prompt-engineer. Currently it only generates prompts from slide briefs (creation mode). The new refinement mode takes an existing prompt + reviewer feedback and returns a refined prompt with composition specifics baked in.

**Files:**
- Modify: `plugins/jack-tar-deckhand/agents/prompt-engineer.md:38-79` (after Output section, before Prohibited)

- [ ] **Step 1: Add Refinement Mode section**

In `plugins/jack-tar-deckhand/agents/prompt-engineer.md`, add the following section between the current "Funnel stage adaptations" block (after line 66) and the "Colour accuracy for Ollama models" block (line 68). Insert before line 68:

```markdown

### Refinement mode

When you receive a **refinement brief** instead of a creation brief, you are refining an existing prompt based on reviewer feedback. The goal is to preserve what works while fixing what's broken.

#### Refinement input

You receive a JSON object with these fields:

| Field | Description |
|-------|-------------|
| `mode` | `"refine"` — distinguishes from creation briefs |
| `original_prompt` | The prompt that produced the reviewed image |
| `iteration` | Which refinement attempt this is (2, 3, etc.) |
| `reviewer_feedback.strengths` | Array of things the image got RIGHT — preserve these |
| `reviewer_feedback.issues` | Array of things to FIX |
| `reviewer_feedback.composition_notes` | Object with subject_placement, scale_hierarchy, text_rendering |
| `brand_constraints` | Same as creation mode — palette_hex, approved/prohibited styles |
| `funnel_stage` | Same as creation mode — ollama, cloud_low, cloud_full |

#### Refinement rules

1. **Preserve strengths explicitly.** If strengths says "speaker is dominant figure, left third of frame", the refined prompt MUST include "speaker occupying left third of frame, at least 3x the height of background figures". Don't assume the model will repeat what worked — lock it down with specific instructions.

2. **Fix issues with concrete spatial/scale instructions.** "Captain is too prominent" becomes "captain figure at most 1/4 the height of the speaker, positioned in the mid-ground behind the conveyor belt". Never use vague adjectives like "smaller" or "less prominent" — specify exact relative sizes and positions.

3. **Add a COMPOSITION section to the prompt.** After the scene description, insert a section starting with "COMPOSITION:" that lists explicit spatial constraints derived from strengths + issues. Example:
   ```
   COMPOSITION:
   - Speaker: left third, foreground, at least 3x height of any other human figure
   - Factory workers: mid-ground, no taller than speaker's waist
   - Conveyor belt: connects left (factory) to right (screen), runs through middle third
   ```

4. **Add a SCALE section for size-sensitive compositions.** When the reviewer flags scale_hierarchy issues, add:
   ```
   SCALE:
   - Primary subject: 60-70% of frame height
   - Secondary elements: no more than 25% of frame height
   - Background details: 10-15% of frame height
   ```

5. **Don't rewrite from scratch.** The original prompt's concept and mood are correct (the reviewer found strengths). Modify the original prompt by injecting COMPOSITION and SCALE sections and tightening vague descriptions into specific ones. Keep the same overall structure.

6. **Same output format.** Return a single string — the refined prompt. No JSON wrapper, no preamble, no explanation. Max 200 words (same as creation mode).
```

- [ ] **Step 2: Commit**

```bash
git add plugins/jack-tar-deckhand/agents/prompt-engineer.md
git commit -m "feat: add refinement mode to prompt-engineer agent"
```

---

## Task 3: Add cross-tier refinement loop to imagegen-bridge Step 9A

Modify the imagegen-bridge's Step 9A to use the refinement loop when executing production upgrades. Flash iterations prove the prompt works before Pro spends money.

**Files:**
- Modify: `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md:379-457` (Step 9A)

- [ ] **Step 1: Replace Step 9A with refinement loop version**

In `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md`, replace the current Step 9A section (lines 379–457) with the version below. The key change is wrapping `raster_upscale` entries in a Flash-first refinement loop.

```markdown
## Step 9A: Production Mode — Execute Upgrade Plan With Prompt Refinement

In production mode, the imagegen-bridge reads `production-upgrade-plan.json` instead of computing routing decisions. The image-generation-expert agent has already determined the optimal engine for each slide.

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
from src.image_router import load_upgrade_plan, execute_upgrade_plan_entry
import json

plan = load_upgrade_plan('./tmp/deck')
for entry in plan['entries']:
    params = execute_upgrade_plan_entry(entry)
    print(f'Slide {entry[\"slide_number\"]}: {params[\"skill\"]} via {params[\"provider\"]} ({params[\"model\"]})')
"
```

For each entry:

### raster_upscale entries — Cross-Tier Prompt Refinement Loop

For raster_upscale entries, use the cheap tier (Flash/Imagen Fast) to validate and refine the prompt before spending on the expensive tier (Pro). This prevents paying premium prices for a sharp version of the wrong image.

**The loop:**

1. **Generate Flash draft** with the original prompt (carried from `draft_prompt` in the plan entry):
   ```bash
   /jack-tar-cloud:image "DRAFT_PROMPT" --provider google --model gemini-3.1-flash-image-preview --output ./tmp/deck/images/slide-NN-hero-flash-v1.png
   ```

2. **Dispatch image-reviewer** to assess the Flash draft:
   ```
   Review this generated image for quality.
   Image: ./tmp/deck/images/slide-NN-hero-flash-v1.png
   Visual direction: "VISUAL_DIRECTION_FROM_OUTLINE"
   Brand palette: HEX_VALUES
   Strategy: STRATEGY
   Iteration: 1 of 3 (Flash refinement)
   ```

3. **If verdict is "pass" → skip Pro.** Flash is good enough. Copy the Flash image to the final path (`slide-NN-hero.png`). Log the cost savings. Done with this entry.

4. **If verdict is "refine" → refine the prompt:**

   Dispatch the `prompt-engineer` agent in refinement mode:
   ```json
   {
     "mode": "refine",
     "original_prompt": "THE PROMPT THAT PRODUCED THE FLASH IMAGE",
     "iteration": 2,
     "reviewer_feedback": {
       "strengths": ["FROM REVIEWER"],
       "issues": ["FROM REVIEWER"],
       "composition_notes": {"FROM": "REVIEWER"}
     },
     "brand_constraints": {"palette_hex": ["FROM BRAND PROFILE"]},
     "funnel_stage": "cloud_low"
   }
   ```

   The prompt-engineer returns a refined prompt string.

5. **Generate Flash v2** with the refined prompt:
   ```bash
   /jack-tar-cloud:image "REFINED_PROMPT" --provider google --model gemini-3.1-flash-image-preview --output ./tmp/deck/images/slide-NN-hero-flash-v2.png
   ```

6. **Dispatch image-reviewer** again. Repeat up to **3 Flash iterations total**.

7. **After 3 Flash failures → escalate to speaker:**
   ```
   The prompt refinement loop could not produce a passing image after 3 Flash iterations.
   Here are the attempts and reviewer feedback:
   - v1: [summary]
   - v2: [summary]
   - v3: [summary]
   The prompt may need human judgment. Please review and either:
   (a) Provide a revised visual direction
   (b) Accept the best attempt (recommend vN)
   (c) Skip this slide's production upgrade
   ```

8. **If Flash passes → escalate the refined prompt to Pro:**
   ```bash
   /jack-tar-cloud:image "REFINED_PROMPT" --provider google --model gemini-3-pro-image-preview --output ./tmp/deck/images/slide-NN-hero.png --width WIDTH --height HEIGHT
   ```

9. **Dispatch image-reviewer** on the Pro output. One shot only:
   - If **pass**: done. Log the final cost.
   - If **refine**: flag for speaker rather than burning more Pro budget:
     ```
     Pro rendering of slide NN did not pass review.
     Reviewer: [summary]
     The Flash version (which passed) is available at slide-NN-hero-flash-vN.png.
     Options: (a) Use the Flash version, (b) Provide revised direction, (c) Accept Pro as-is
     ```

**Key rules:**
- Flash iterations are cheap (~$0.067 each) — budget for up to 3 per image
- The prompt-engineer receives `strengths` (preserve) AND `issues` (fix) — it builds on what works
- If Flash passes on the first try, skip Pro entirely — don't spend money for no reason
- Pro gets ONE shot — if it fails, flag for speaker rather than burning budget
- Store the final `source_prompt` (which may be the refined version) in the ImageManifest
- The `source_prompt` field MUST be updated to the refined prompt if refinement occurred

**Prompt selection:**
- If `image_id` contains `elem-`, use the plan's `draft_prompt` (element-specific, unchanged)
- Otherwise, start with `draft_prompt` and refine through the loop

### vector_conversion entries

Invoke `jack-tar-cloud:icon` with Recraft:

```bash
/jack-tar-cloud:icon "DRAFT_PROMPT" --provider recraft --output ./tmp/deck/images/slide-NN-diagram.svg
```

The output is SVG. After generation, rasterise it to PNG using `src/process_image.py`, passing the slide's background colour to fix Recraft's default white backgrounds:

```python
from src.process_image import rasterize_svg

# Get slide background colour from the StyleGuide's slidePalette:
#   title slides:   slidePalette.title_slide.background   (or palette.primary)
#   content slides: slidePalette.content_slides.background (or palette.background)
#   code slides:    slidePalette.code_slides.background    (or '#0E1513')
result = rasterize_svg(
    'tmp/deck/images/slide-NN-diagram.svg',
    'tmp/deck/images/slide-NN-diagram.png',
    width=1920,
    background_color=slide_bg_color,  # e.g. '#F5FBF7' or '#0E1513'
)
```

This replaces Recraft's near-white SVG backgrounds with the actual slide background colour, preventing visible white rectangles on assembled slides.

### Recraft prompt patterns (learned from production)

Recraft V4 interprets prompts differently from raster models. Follow these rules:

1. **Enumerate every element explicitly** — "Rectangle 1: labeled 'Brief'. Rectangle 2: labeled 'Brand'." not "8 connected stages flowing left to right"
2. **Specify the topology** — "snake pattern with 3 rows" or "single horizontal row" or "2x2 grid" not just "flow diagram"
3. **Forbid extras explicitly** — "No title. No subtitle. No footer. No annotations. No sub-labels. Only the N elements described above."
4. **Describe layout geometry** — "wide horizontal bar spanning full width at top" not just "orchestrator across the top"
5. **Consider slide aspect ratio** — 8 items in a horizontal line on a 16:9 slide will be tiny. Use snake/grid layouts for >4 nodes.
6. **Use design vocabulary** — "rounded rectangle filled with deep teal (#006B5E)" not "clean geometric node in brand teal"

These patterns reduced Recraft iterations from 3+ to 1-2 per diagram.

### Prompt selection for production upgrades

For slides with a single image, use the outline's `visual_direction` as the prompt (it may have been refined during drafting).

For slides with multiple element images (pragmatic_composition, three_across layouts), use the `draft_prompt` from the production upgrade plan entry for each element — NOT the outline's `visual_direction`. The outline has one visual_direction per slide but element images each need their own distinct prompt. Using the slide-level prompt for all elements produces identical images.

**Rule:** If `image_id` contains `elem-`, always use the production plan's `draft_prompt` for that entry.

### no_upgrade entries

Skip — the existing draft image is already production quality (matplotlib chart or similar).
```

- [ ] **Step 2: Commit**

```bash
git add plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md
git commit -m "feat: add cross-tier prompt refinement loop to imagegen-bridge Step 9A"
```
