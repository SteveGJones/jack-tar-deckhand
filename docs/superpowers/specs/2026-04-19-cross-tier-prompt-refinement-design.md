# Cross-Tier Prompt Refinement Loop

## Problem

When escalating from a cheap image generation tier (Flash/Ollama) to an expensive tier (Pro), the pipeline currently re-runs the same prompt at higher quality. This wastes money — if the prompt's composition is wrong, higher quality just produces a sharper version of the wrong image. If the composition is right, you're paying premium for something the cheap tier already nailed.

Dogfood finding (2026-04-19): building the jack-tar-deckhand explainer deck, the Nanobanana Flash draft had the perfect composition (speaker dominant, factory behind), but Pro with the same prompt shifted the composition (captain too prominent). The fix was to analyze what Flash got right, bake those specifics into the prompt, verify with another Flash, then escalate the refined prompt to Pro.

## Solution

A prompt refinement loop that uses the cheap tier to iterate on prompt quality before spending on the expensive tier. Three existing actors, no new modules.

## The Loop

```
1. Generate Flash draft with original prompt
2. Image-reviewer scores → {verdict, strengths[], issues[]}
3. If pass → done (Flash is good enough, skip Pro, save money)
4. If refine →
   a. Prompt-engineer refines prompt using strengths + issues
   b. Generate Flash v2 with refined prompt
   c. Image-reviewer scores v2
   d. Repeat up to 3 Flash iterations total
5. After 3 Flash failures → escalate to speaker
   "Here are the 3 attempts and what the reviewer said.
    The prompt may need human judgment."
6. If Flash passes → escalate refined prompt to Pro
7. Image-reviewer scores Pro → pass / flag_for_speaker
```

### Key rules

- Flash iterations are cheap — budget for up to 3 per image before escalating to speaker
- The prompt-engineer receives `strengths` (preserve these) AND `issues` (fix these) — it's not starting from scratch each iteration
- If Flash passes on the first try, skip Pro entirely — don't spend money for no reason
- Pro gets ONE shot with the refined prompt — if it fails, flag for speaker rather than burning budget
- After 3 Flash failures, escalate to the speaker — the prompt is probably fundamentally wrong and throwing money at Pro won't fix it

### Principle

Flash proves the prompt works before Pro spends money on it. If Flash can't prove it, a human decides — not the budget.

## Reviewer → Prompt-Engineer Communication Contract

The reviewer must report what worked, not just what failed. The prompt-engineer must preserve good composition while fixing bad.

### Image-reviewer output (extended fields)

```json
{
  "verdict": "refine",
  "strengths": [
    "Speaker is dominant figure, left third of frame",
    "Warm/cool lighting contrast between factory and stage",
    "Conveyor belt connects factory to screen"
  ],
  "issues": [
    "Factory section labels are illegible",
    "Captain is too prominent — same scale as speaker",
    "SmartArt Drydock section is empty, no template hulls visible"
  ],
  "composition_notes": {
    "subject_placement": "speaker left foreground — correct",
    "scale_hierarchy": "speaker and captain similar size — wrong",
    "text_rendering": "banner OK, section labels failed"
  }
}
```

Existing fields (`verdict`, `review_summary`) are unchanged. New fields: `strengths[]`, `issues[]`, `composition_notes{}`.

### Prompt-engineer input (refinement mode)

```json
{
  "original_prompt": "...",
  "iteration": 2,
  "reviewer_feedback": {
    "strengths": ["..."],
    "issues": ["..."],
    "composition_notes": {}
  },
  "instruction": "Preserve everything in strengths. Fix everything in issues. Bake fixes as specific composition instructions, not vague adjectives."
}
```

### Prompt-engineer output

A new prompt string with fixes embedded as concrete spatial/scale instructions. Example: "speaker at least 3x taller than factory workers" not "speaker should be bigger". The prompt-engineer adds explicit COMPOSITION AND SCALE sections to the prompt rather than tweaking adjectives.

## Where This Lives

No new Python modules. Three existing files extended:

### 1. Image-reviewer agent (`.claude/agents/image-reviewer.md`)

Add `strengths[]`, `issues[]`, `composition_notes{}` to its output schema. Currently returns `verdict` + `review_summary` only. The reviewer already sees the image and the original intent — it just needs to structure its observations into "preserve" vs "fix" categories.

### 2. Prompt-engineer agent (`.claude/agents/prompt-engineer.md`)

Add a "refinement mode" to its protocol. Currently only generates prompts from slide briefs (creation mode). New mode: takes an existing prompt + reviewer feedback, returns a refined prompt with composition specifics baked in. The agent already runs at Haiku (default) or Sonnet (escalation) — refinement mode uses the same dispatch.

### 3. Imagegen-bridge skill (`plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md`)

Add the refinement loop to Step 9A (production upgrade execution). Currently generates once and moves on. New flow: Flash draft → review → refine → verify → Pro.

The bridge orchestrates by passing data between the reviewer and prompt-engineer subagents. It tracks iteration count and decides when to escalate to speaker vs Pro.

## Relationship to Render Funnel

The render funnel (`src/render_funnel.py`) handles the Ollama → cloud_low → cloud_full resolution escalation. The prompt refinement loop is a different axis — it's about prompt quality, not image resolution. They compose:

- The funnel decides WHEN to go to cloud
- The refinement loop decides HOW to use cloud effectively

The refinement loop only activates during production upgrade (Step 9A), not during draft rendering. Ollama drafts are free and already iterate up to 10 times.

## Not In Scope

- Changes to render_funnel.py — that's resolution escalation, not prompt refinement
- Changes to generate_cloud_image.py — it already handles both Flash and Pro correctly
- Changes to provider_discovery.py or image_router.py — those are Spec 2 (two-tier Google routing)
- New Python modules — the loop is skill-level orchestration, not library code
