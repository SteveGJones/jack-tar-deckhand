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

## Plugin Setup

```bash
PLUGIN_ROOT=$(python3 -c "
from pathlib import Path
import sys, os
if os.environ.get('JACK_TAR_DECKHAND_ROOT'):
    print(os.environ['JACK_TAR_DECKHAND_ROOT']); sys.exit()
home = Path.home()
for base in [home / '.claude' / 'plugins' / 'cache']:
    for p in base.rglob('jack-tar-deckhand/.claude-plugin/plugin.json'):
        print(str(p.parent.parent)); sys.exit()
dev = Path.cwd() / 'plugins' / 'jack-tar-deckhand'
if dev.exists():
    print(str(dev)); sys.exit()
print('NOT_FOUND')
" 2>/dev/null)
if [ -z "$PLUGIN_ROOT" ] || [ "$PLUGIN_ROOT" = "NOT_FOUND" ]; then echo "ERROR: jack-tar-deckhand not found" && exit 1; fi
```

### Step 3: Validate and Write

Validate the outline before writing:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
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

## Optional: hero-slide resolution annotation

If the speaker is shooting for a memorable opener or closing slide, ask: "Would you like this slide rendered at 4K (Nano Banana Pro, ~$0.24) or 2K?" Annotate the slide with a `resolution` field in the SlideOutline if so — the strategy-map step will carry it through to the StrategyMap entry. Default `1K` unchanged.

## Optional: brand-fidelity annotation

If the talk is brand-led (product launch, company keynote, vendor pitch) or has slides where exact brand-color match is critical (logos, product shots), ask: "For [slide N], should brand colors be rendered hex-exact (`brand_fidelity: \"exact\"` → Recraft V4 raster, ~2× cost at 4K) or close-enough (default → FLUX or Nano Banana)?" Annotate `brand_fidelity` on the SlideOutline entry if so — the strategy-map step will carry it through. Default `"none"` unchanged.

## Optional: academic-figure strategy annotation (paperbanana E4)

If the talk is research-flavoured — a paper readout, a thesis defence, a
conference deep-dive on an ML architecture, a tutorial on an algorithm —
some slides will be **figures**, not narrative beats. They carry one or
more of:

- An explicit caption (`Figure 3: ...`, `Fig. 2.`) repeated from the paper
- A block equation or LaTeX math (`$$ ... $$`, `\frac`, `\sum`, `\alpha`, `\theta`, ...)
- Numbered citations (`[12]`) or "et al." author refs in the body
- An `Algorithm N` heading or `pseudocode` block
- Subjects like "system architecture (encoder/decoder/heads)", "ablation
  study", "confusion matrix"

For those slides, the `strategy_classifier.py` heuristic (paperbanana E1)
will set `strategy: "academic_figure"` automatically in the StrategyMap,
and the imagegen-bridge will dispatch to the **paperbanana**
`/generate-diagram` skill (paperbanana E2) for publication-grade rendering
when the plugin is installed (falls back to cloud Flash 1K otherwise — see
`/jack-tar-deckhand:verify` for live availability).

What this means for you (narrative-architect):

- **Do** write `visual_direction` prose that names the academic subject
  literally ("Figure 3: encoder-decoder architecture with 4 attention
  heads"). The literal caption keywords are what the classifier matches.
- **Do** preserve any paper-style notation in `body_points` rather than
  paraphrasing it into business language. `[12]` and "et al." are signal,
  not noise.
- **Don't** force these slides into a SmartArt graphic_type. The
  smartart-selector defers academic figures to the paperbanana route
  (see its "Academic-figure deferral rule") — recommending `bar_chart` or
  `line_chart` for a slide that's actually Figure 3 of a paper would
  bypass paperbanana and produce a generic chart instead of the
  paper-quality figure the speaker wants.
- **Don't** prompt the speaker about this — the classifier is content-
  driven. Only ask if the speaker explicitly wants to override (e.g. force
  a slide that lacks signals into academic_figure for stylistic
  consistency with the rest of the figure set).

If `paperbanana` is not installed on the speaker's machine, the bridge
falls back to cloud generation with academic-figure-aware prompting. The
slide will still render; it just won't be publication-tier. The
`/jack-tar-deckhand:verify` skill reports whether paperbanana is reachable
before the deck builds — if the speaker cares about publication tier and
the verify check is amber, point them at the paperbanana plugin install
guide (see `docs/architecture/paperbanana-integration.md`).
