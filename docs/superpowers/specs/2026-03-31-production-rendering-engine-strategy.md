# Production Rendering Engine Strategy

**Date:** 2026-03-31
**Status:** Design approved

## Problem

The current production upgrade path (`plan_production_upgrade` in `image_router.py`) treats all images the same: re-render the draft prompt at higher resolution on a cloud model. This ignores two fundamental differences:

1. **Vector vs raster content** — diagrams, flowcharts, and icons are better served by SVG (Recraft) than by higher-resolution raster. There is no "low-res vector" — SVG scales to any size. The draft validates the concept; production is a format change, not a resolution bump.

2. **Model suitability per content character** — a photorealistic hero image, an abstract background, and a text-heavy diagram each have a different best-fit model. The current priority list doesn't consider content character.

## Design

### Two Production Tracks

**Raster Track (raster_upscale)** — pixel-based images where quality scales with resolution.

- Content: hero images, atmospheric backgrounds, conceptual metaphors, textures, element images
- Draft: Ollama (free, 1024x576)
- Production: cloud model selected by expert per-slide
- Upgrade = re-render proven prompt at higher resolution on better model

**Vector Track (vector_conversion)** — SVG output where quality is resolution-independent.

- Content: diagrams, flowcharts, process flows, icon grids, architecture visuals
- Draft: Ollama/FLUX (free, quick layout validation of the concept)
- Production: Recraft V4 standard ($0.08), with pro ($0.30) if quality review flags issues or Speaker pre-selects
- Upgrade = format change (raster to SVG), not resolution change

### Provider and Tier Matrix

#### Raster providers

| Provider | Tier | Cost | Best for |
|---|---|---|---|
| FLUX Pro (FAL) | single tier | $0.03 | Abstract/artistic, bold colour, prompt adherence |
| GPT Image (OpenAI) | low | $0.009-0.013 | Photorealism (budget) |
| GPT Image (OpenAI) | medium | $0.034-0.051 | Photorealism (production default) |
| GPT Image (OpenAI) | high | $0.133-0.200 | Photorealism (premium) |
| Nanobanana Flash (Google) | flash | $0.067 | Text-in-image, complex scenes (budget) |
| Nanobanana Pro (Google) | pro | $0.134 | Text-in-image, complex scenes (quality) |

#### Vector providers

| Provider | Tier | Cost | Best for |
|---|---|---|---|
| Recraft V4 (direct or FAL) | standard | $0.08 | Diagrams, flowcharts, icons (default) |
| Recraft V4 (direct or FAL) | pro | $0.30 | Complex diagrams with many elements |

#### Non-upgradeable

| Provider | Cost | Content |
|---|---|---|
| matplotlib (local) | $0.00 | Data charts — already production quality |

### "Try Cheap, Escalate If Needed" Principle

Both tracks follow the same pattern:

1. Expert recommends starting tier (usually the cheaper option)
2. Production render executes at that tier
3. Presentation-reviewer evaluates the result
4. If quality is insufficient, reviewer recommends escalation (higher tier or different provider)
5. Escalation goes back to Speaker for approval — never auto-escalates
6. Speaker can also pre-select a higher tier upfront

### Production Upgrade Plan (the artifact)

Before any production money is spent, the image-generation-expert agent produces a Production Upgrade Plan — a reviewable JSON artifact saved as `production-upgrade-plan.json` in the deck directory.

Each entry:

```json
{
  "slide_number": 3,
  "image_id": "slide-03-hero",
  "upgrade_track": "raster_upscale",
  "recommended_provider": "google",
  "recommended_model": "gemini-3.1-flash-image-preview",
  "recommended_tier": "flash",
  "target_dimensions": "1920x1080",
  "estimated_cost_usd": 0.067,
  "reasoning": "Complex scene with embedded text labels — Nanobanana handles text-in-image best. Flash tier sufficient for 4-element layout.",
  "brand_notes": "Primary palette #2B6CB0 — Nanobanana has strong colour fidelity for blues",
  "warnings": [],
  "draft_prompt": "..."
}
```

For vector_conversion entries, `target_dimensions` is null (SVG is resolution-independent).

Warnings are populated when:
- Speaker overrides to a questionable choice (expert confirms before executing)
- Content character mismatches the selected model
- Resolution exceeds model capability
- Unnecessarily expensive tier for simple content

Flow:
1. Expert reads draft ImageManifest + StrategyMap + StyleGuide
2. Expert produces the Production Upgrade Plan
3. Plan is presented to Speaker as a table with costs and reasoning
4. Speaker approves, overrides individual slides, or requests tier changes
5. If Speaker overrides with a questionable choice, expert adds warning and confirms
6. Approved plan is saved to `production-upgrade-plan.json`
7. imagegen-bridge executes the plan mechanically

### Expert Decision Framework

Encoded as guidance in the image-generation-expert agent file. The expert reasons contextually (Claude), not via deterministic lookup.

**Step 1 — Classify upgrade track:**

| Content nature | Track | Signal from strategy map |
|---|---|---|
| Diagrams, flowcharts, process flows | vector_conversion | strategy: composed, visual_type: diagram |
| Icons, icon grids | vector_conversion | visual_type: icon_set |
| Hero images, scene illustrations | raster_upscale | strategy: full_render, background, backdrop |
| Atmospheric textures, patterns | raster_upscale | visual_type: pattern_background |
| Element images | raster_upscale | strategy: pragmatic_composition |
| Data charts | no_upgrade | Already production quality (matplotlib) |

**Step 2a — Select provider and tier (raster):**

| Content character | First choice | Why |
|---|---|---|
| Photorealistic scenes, people | GPT Image medium | Strongest photorealism |
| Abstract, artistic, bold colour | FLUX Pro | Best prompt adherence, artistic flair |
| Text embedded in image | Nanobanana Flash | Native multimodal text handling |
| Complex scene, high detail | Nanobanana Flash | Strong scene composition |
| Brand-critical colour accuracy | GPT Image or Nanobanana | Better colour fidelity than FLUX |

**Step 2b — Select provider and tier (vector):**

- Default: Recraft standard ($0.08)
- Pre-select pro if: Speaker requests, diagram has 10+ elements, or expert judges architecturally complex

**Step 3 — Brand compliance check:**

- Read the StyleGuide palette
- If slide has brand-critical colours in prominent positions, note in brand_notes and prefer providers with better colour fidelity
- If brand uses specific illustration style (flat, isometric), factor into provider choice

**Step 4 — Guardrail check:**

- If Speaker has overridden any choices, validate them
- Warn (don't block) on: wrong model for content type, resolution beyond model capability, unnecessarily expensive tier for simple content
- Always confirm before executing a warned override
- The expert advises; the Speaker decides

### Post-Production Quality Gate

After production render, the presentation-reviewer evaluates each result.

**Raster assessment:**
- Visual metaphor clarity
- Colour fidelity against brand palette
- Resolution/detail sufficiency — artefacts, blurriness, muddy areas
- Text legibility (for text-in-image slides)

**Vector assessment:**
- Diagram readability — labels legible, lines clean, shapes distinct
- Complexity threshold — overlapping elements, text collisions
- Geometric consistency — shape alignment, even spacing

**Per-slide verdicts:**
- `pass` — production quality, no action needed
- `escalate_tier` — same provider, higher tier recommended (e.g., Recraft standard to pro, Nanobanana Flash to Pro)
- `escalate_provider` — different provider recommended (e.g., FLUX to GPT Image for colour fidelity)
- `flag_for_speaker` — subjective issue, Speaker should decide

Escalation recommendations go back to the Speaker for approval. The conductor never auto-escalates.

## Changes to Existing Code

### image_router.py — Minimal changes
- `plan_production_upgrade()` replaced by the expert agent's Production Upgrade Plan. Either becomes a thin executor that reads `production-upgrade-plan.json`, or removed in favour of imagegen-bridge reading the plan directly.
- `ROUTING_MATRIX` stays unchanged for draft routing.
- Add `upgrade_track` awareness: vector_conversion entries invoke `cloud-generate-icon` (Recraft) instead of `cloud-generate-image`.

### image-generation-expert agent — Major update
- New responsibility: produce the Production Upgrade Plan artifact
- Decision framework: content character to track to provider to tier
- Brand compliance checks: read StyleGuide palette, flag colour-critical slides
- Guardrail logic: warn on unsuitable Speaker overrides, confirm before executing
- "Try cheap first" principle and escalation tiers

### presentation-reviewer agent — Minor update
- Add vector-specific quality criteria (diagram readability, complexity threshold)
- Add per-slide verdict enum: pass, escalate_tier, escalate_provider, flag_for_speaker
- Knows which tier/provider was used so it can recommend the right escalation

### imagegen-bridge skill — Update execution path
- In production mode: read `production-upgrade-plan.json` instead of calling `plan_production_upgrade()`
- For vector_conversion entries: invoke `cloud-generate-icon` with Recraft endpoint
- For raster_upscale entries: invoke `cloud-generate-image` with specified provider/model/tier

### deck-conductor agent — Updated orchestration
- After draft is approved, invoke image-generation-expert to produce Production Upgrade Plan
- Present plan to Speaker for approval
- After production render, run presentation-reviewer for quality gate
- Collect escalation verdicts, present to Speaker, re-render if approved

### strategy-map skill — No change needed
Classifies rendering strategy (full_render, background, etc.), not production engine. Expert reads its output but doesn't modify it.

### New schema
`production-upgrade-plan.schema.json` for the plan artifact validation.

## What Does Not Change

- Draft routing matrix — Ollama-first for free iteration stays the same
- render_chart.py — matplotlib charts are already production quality
- The 5 rendering strategies — these describe how slides are assembled, not which engine renders the images
- DeckContext contract flow — the Production Upgrade Plan is a new artifact in the existing pipeline, not a replacement for any existing contract
