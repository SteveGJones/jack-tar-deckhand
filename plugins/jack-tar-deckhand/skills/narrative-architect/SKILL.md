---
name: narrative-architect
description: Transform a TalkBrief into a structured SlideOutline through collaborative arc selection and autonomous outline generation.
argument-hint: [--deck-dir PATH]
allowed-tools: Bash(python *), Read, Glob, Write
---

# /narrative-architect

Transform a TalkBrief into a structured SlideOutline. Works in two stages: collaborative arc selection with the Speaker, then autonomous outline generation.

## Prerequisites

- `./tmp/deck/talk-brief.json` must exist
- `./tmp/deck/style-guide.json` must exist (produced by slide-stylist)

## Usage

Invoked by the Deck Conductor after slide-stylist. Can also be invoked directly:

```
/narrative-architect
/narrative-architect --deck-dir ./tmp/deck
```

## What It Does

### Stage 1: Arc Proposal (Collaborative)

Read `./tmp/deck/talk-brief.json` for topic, audience, duration, tone, key takeaways, and data sources.

Based on these signals, select 2-3 narrative arc options that genuinely fit this specific talk. Do NOT present all 16 arcs from the catalogue -- curate down to the best matches.

For each proposed arc, present:

> "For a **{duration}-minute {tone}** talk on **{topic}**, here are the narrative structures I'd recommend:
>
> 1. **{Arc Name}** -- {one-line emotional description}
>    - Best for: {when this works}
>    - Your talk would flow: {beat1} -> {beat2} -> {beat3} -> ... -> {final beat}
>    - Slide count: ~{count} slides at {pacing} pacing
>
> 2. **{Arc Name}** -- {one-line emotional description}
>    - Best for: {when this works}
>    - Your talk would flow: {beat1} -> {beat2} -> ...
>    - Slide count: ~{count} slides
>
> 3. **{Arc Name}** -- {one-line emotional description}
>    - Best for: {when this works}
>    - Your talk would flow: {beat1} -> {beat2} -> ...
>    - Slide count: ~{count} slides
>
> **My recommendation:** {Arc Name} because {one-sentence rationale connecting to this specific talk}.
>
> Which structure speaks to you? (Or describe what you're looking for)"

Wait for the Speaker to select or describe their preference. If they describe something custom, map it to the closest arc or propose a hybrid.

### Arc Catalogue Reference

These are the established structures to draw from (Research #08):

| Arc | Best For | Pacing |
|-----|----------|--------|
| Situation-Complication-Resolution | Executive briefings, problem-solving | Standard |
| Monroe's Motivated Sequence | Persuasion, calls to action | Standard |
| Hero's Journey | Transformation stories, keynotes | Visual-heavy |
| Problem-Solution-Impact | Product talks, case studies | Standard |
| Problem-Demo-Impact | Technical demos, tool showcases | Content-heavy |
| What-So What-Now What | Data presentations, research findings | Content-heavy |
| Hook-Thesis-Body-Callback-CTA | Persuasion talks, thought leadership | Standard |
| Story-Point-Application | Rule of Three, teaching talks | Standard |
| Pecha Kucha | 6:40 fixed format, 20 slides x 20 seconds | Rapid-fire |
| Ignite | 5 min fixed, 20 slides x 15 seconds | Rapid-fire |
| Lightning Talk | 5-10 min, minimal slides | Standard |
| Lessig Method | Rapid visual reinforcement, advocacy | Rapid-fire |
| Takahashi Method | Japanese big-text style, storytelling | Rapid-fire |
| 10/20/30 Rule | Startup pitches, 10 slides | Content-heavy |
| Duarte Sparkline | Long keynotes, What Is vs What Could Be | Visual-heavy |
| Modular Deck | Flexible/reusable, workshop-style | Standard |

### Stage 2: Outline Execution (Autonomous)

Once the Speaker selects an arc, produce the full SlideOutline. This is expert craft -- do NOT seek per-slide approval.

**What you decide autonomously:**
- Exact slide count (calibrated to duration and pacing style)
- Slide type assignment per slide (from the 12 types)
- Headlines -- punchy conference headlines, not academic paper titles
- Body points (max 5 per slide)
- Narrative beat labels
- Visual direction prose per slide (specific enough for prompt engineering, incorporating StyleGuide image_style_tokens)
- Layout template references from StyleGuide
- Transition notes between slides
- Section divider placement (before every major beat transition)
- Attention reset beats (every ~10 minutes of duration)
- Data source mapping from TalkBrief to data_chart slides

**Pacing guidelines:**
- Content-heavy (data, technical deep-dive): 0.5-1.0 slides/min
- Standard (most conference talks): 1.0-1.5 slides/min
- Visual-heavy (keynotes, storytelling): 1.5-2.5 slides/min
- Rapid-fire (Pecha Kucha, Ignite, Lessig): 3.0-4.0 slides/min

**Structural overhead added to base count:**
- +1 title slide (always)
- +1 closing slide (always)
- +1 section divider per major beat transition
- +1 attention reset per 10 minutes of duration

If `preferences.slide_count_hint` is provided, use it as a soft target (within 20%) but override if the arc demands it.

**Read the StyleGuide** at `./tmp/deck/style-guide.json` for:
- Layout template names (ensure every slide's `layout_template` exists in `layout.templates`)
- Image style tokens (weave `mood`, `color_direction`, and `style_modifiers` into `visual_direction` prose)

### Step 3: Validate and Write

Validate the outline before writing:

```bash
source .venv/bin/activate && python3 -c "
import json
from src.content_validation import validate_outline_schema, check_outline_layout_references
outline = json.load(open('./tmp/deck/outline.json'))
style_guide = json.load(open('./tmp/deck/style-guide.json'))
schema_errors = validate_outline_schema(outline)
ref_issues = check_outline_layout_references(outline, style_guide)
for e in schema_errors: print(f'SCHEMA: {e}')
for e in ref_issues: print(f'REF: {e}')
if not schema_errors and not ref_issues:
    print('SlideOutline validates successfully')
"
```

Write the validated SlideOutline to `./tmp/deck/outline.json`.

## Output

`./tmp/deck/outline.json` (SlideOutline contract)

## Design Rules

- Headlines should be punchy conference headlines, not generic titles ("The 3-Second Rule for Slide Readability" not "Text Best Practices")
- Max 5 body points per slide
- Visual direction must be specific enough to generate images but not prescriptive about implementation
- Section dividers before every major narrative beat transition
- Title slide always first, closing slide always last
- Do NOT ask the Speaker about individual slide choices -- the arc approval is the collaboration point
