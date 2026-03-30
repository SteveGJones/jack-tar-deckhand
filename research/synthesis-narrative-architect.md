# Synthesis: narrative-architect

> Distilled from: research/08-narrative-arc-patterns.md, docs/architecture/content-services.md, src/schemas/slide_outline.schema.json

## 1. Two-Stage Collaborative Model

The narrative-architect operates in two stages with a Speaker approval gate between them.

### Stage 1: Arc Proposal (Interactive)

1. Read the TalkBrief (topic, audience, duration, tone, key takeaways, data sources)
2. Read the StyleGuide (layout templates, slide types available)
3. Select 2-3 narrative arc options from the catalogue (Section 2 below), curated by duration, tone, and content type
4. For each option, present:
   - Arc name and origin
   - Why it suits this talk (audience + goal alignment)
   - Beat structure with approximate time allocations
   - Estimated slide count range
   - Example slide-type sequence (abbreviated)
5. Wait for Speaker to select one arc

### Stage 2: Outline Execution (Autonomous)

Once the arc is agreed, the narrative-architect produces the full SlideOutline (`./tmp/deck/outline.json`) without per-slide approval. Individual slide decisions are professional craft. The architect decides autonomously:

- Exact slide count within the arc's range
- Per-slide type assignment from the 12 available types
- Headlines (punchy, conference-style -- not academic paper titles)
- Body points (max 5 per slide, projection-readable)
- Narrative beat labels
- Visual direction prose per slide
- Visual type assignment (hero_image, diagram, chart, icon_set, pattern_background, none)
- Data source mapping from TalkBrief to data_chart slides
- Layout template references from the StyleGuide
- Transition notes between slides
- Placement of invisible slides (section dividers, breathing room, interaction beats)

---

## 2. Arc Catalogue

### 2.1 Grouped by Duration and Tone

**Short-form (5-10 minutes)**

| Arc | Beats | Fixed Slides | Best For |
|-----|-------|-------------|----------|
| Pecha Kucha | 20 images, 20s each | 20 (fixed) | Design showcases, creative portfolios, meetups |
| Ignite | 20 slides, 15s each | 20 (fixed) | Tech meetups, rapid-fire idea sharing |
| Lightning Talk | Flexible | 10-15 | Developer conferences, unconferences |

**Medium-form (15-30 minutes)**

| Arc | Beats | Typical Slides | Best For |
|-----|-------|---------------|----------|
| Problem-Solution-Impact | 3 | 7-15 | Sales pitches, client proposals, startup pitches |
| Problem-Demo-Impact | 3 | 10-15 + demo | Product launches, developer conferences |
| 10/20/30 (Kawasaki) | 10 prescribed | 10 (fixed) | Investor pitches, high-stakes proposals |
| What-So What-Now What | 3 per data point | 12-20 | Quarterly reviews, data presentations |
| Hook-Thesis-Body-Callback-CTA | 5 | 15-25 | Conference talks, thought leadership |

**Long-form (30-60 minutes)**

| Arc | Beats | Typical Slides | Best For |
|-----|-------|---------------|----------|
| SCR (Minto Pyramid) | 3 (or 4 with SCQA) | 10-20 | Executive briefings, strategy, consulting |
| Monroe's Motivated Sequence | 5 | 15-25 | Persuasion, advocacy, fundraising |
| Hero's Journey | 6 | 20-35 | Keynotes, transformation stories, case studies |
| Story-Point-Application | 3x3 = 9 | 18-30 | Motivational, leadership, workshops |
| Duarte Sparkline | Alternating contrast | 20-40 | Keynotes, vision talks, all-hands |

**Special formats (any duration)**

| Arc | Constraint | Best For |
|-----|-----------|----------|
| Lessig Method | 1 word/phrase/image per slide, 15s each | Advocacy, legal arguments, TED-style |
| Takahashi Method | Giant text only, many slides | Technical talks without design resources |
| Modular Deck | Reorderable core sections | Client meetings, unpredictable conversations |

### 2.2 Quick Selection Guide

| If the talk is... | Use |
|-------------------|-----|
| Persuading executives to approve a strategy | SCR (Minto Pyramid) |
| Advocating for change with a clear ask | Monroe's Motivated Sequence |
| Telling a transformation story at a keynote | Hero's Journey or Duarte Sparkline |
| Pitching a product or startup | Problem-Solution-Impact or 10/20/30 |
| Demoing a product to developers | Problem-Demo-Impact |
| Presenting quarterly data to leadership | What-So What-Now What |
| Giving a conference talk to inspire action | Hook-Thesis-Body-Callback-CTA |
| Teaching through stories at a workshop | Story-Point-Application (Rule of Three) |
| Presenting at a design meetup | Pecha Kucha |
| Sharing a quick idea at a tech meetup | Lightning Talk or Ignite |
| Making a legal or advocacy argument | Lessig Method |
| Presenting without design resources | Takahashi Method |
| Running an unpredictable client meeting | Modular Deck |
| Giving a vision/all-hands talk | Duarte Sparkline |

---

## 3. Arc-to-Slide-Count Derivation

### 3.1 Pacing Styles

| Pace | Slides/Minute | When to Use |
|------|---------------|-------------|
| Standard | 0.5-1.0 | Content-heavy: data presentations, technical deep dives, board meetings |
| Fast | 1.0-2.0 | Visual-heavy: storytelling keynotes, image-driven narratives |
| Rapid-fire | 2.0-4.0 | Fixed-format: Pecha Kucha, Ignite, Lessig, Takahashi |

### 3.2 Content Slide Duration

Each content slide is calibrated to approximately 1.5-2 minutes of speaking time at standard pace. This means:

- 5-minute talk: 3-5 content slides
- 20-minute talk: 10-13 content slides
- 30-minute talk: 15-20 content slides
- 45-minute talk: 22-30 content slides

### 3.3 Structural Overhead

Content slide counts above do NOT include structural "invisible" slides. Add:

| Structural Element | Count Rule | Purpose |
|-------------------|------------|---------|
| Title slide | 1 (always) | Opens the deck |
| Section dividers | 1 per major beat transition | Mental breathing room, topic shift signal |
| Closing slide | 1 (always) | CTA + contact/resources |
| Recap/checkpoint slides | 1 per 15 minutes of talk | Resets audience comprehension |
| Interaction beat slides | 1 per 10 minutes of talk | Resets attention (the 10-minute rule) |

**Example for a 30-minute talk using Hook-Thesis-Body-Callback-CTA:**
- Content slides: ~16
- Title: 1
- Section dividers: 3-4 (between body points + before callback)
- Closing: 1
- Checkpoint: 1 (at ~15 min)
- Total: ~22-23 slides

### 3.4 Fixed-Format Overrides

Some arcs have non-negotiable slide counts that override the derivation:

| Arc | Slide Count | Duration |
|-----|-------------|----------|
| Pecha Kucha | 20 (exactly) | 6:40 |
| Ignite | 20 (exactly) | 5:00 |
| 10/20/30 (Kawasaki) | 10 (exactly) | 20 min max |

---

## 4. Slide Type Assignment Patterns

### 4.1 The 12 Slide Types

From the SlideOutline schema: `title`, `section_divider`, `content`, `two_column`, `image_feature`, `data_chart`, `stat_callout`, `quote`, `icon_grid`, `diagram`, `closing`, `blank_visual`.

### 4.2 Beat-to-Type Mapping

| Narrative Function | Primary Type | Secondary Type |
|-------------------|-------------|----------------|
| Open / hook | `image_feature` or `stat_callout` | `blank_visual` (striking image) |
| Context / current state | `content` or `two_column` | `data_chart` |
| Problem / tension | `data_chart` or `stat_callout` | `content` |
| Solution / concept | `content` or `diagram` | `icon_grid` |
| Evidence / proof | `data_chart` | `quote` (testimonial) |
| Demo segment | `blank_visual` (screenshot) | `diagram` (architecture) |
| Vision / future | `image_feature` | `two_column` (before/after) |
| Story / anecdote | `image_feature` or `blank_visual` | `quote` |
| Recap / checkpoint | `content` (bullet summary) | `icon_grid` |
| Call to action | `closing` | `stat_callout` |
| Transition | `section_divider` | -- |

### 4.3 Sequencing Rules

1. **Never two data-heavy slides in a row.** Follow any `data_chart` with an insight (`content`), story (`image_feature`), or `section_divider`.
2. **Section dividers before every major topic shift.** One `section_divider` at each beat boundary.
3. **Progressive disclosure for complex ideas.** Concept (`content`) then data (`data_chart`) then conclusion (`stat_callout` or `content`).
4. **One idea per slide.** If a slide needs more than 2 minutes during practice, split it.
5. **Maximum 6 elements per slide.** Text blocks + images + chart elements combined.
6. **Vary slide types rhythmically.** Alternate between text-heavy, image-heavy, and data types. Insert a change-of-pace element every 8-10 minutes.
7. **Maximum 5 body points per slide.** Enforced by schema constraint.

### 4.4 Opening Conventions

**Talks > 15 minutes:**
1. `title` -- on screen as audience settles
2. `image_feature` or `stat_callout` -- the hook
3. `content` (optional) -- thesis/agenda for longer talks
4. First content slide

**Talks < 15 minutes:**
1. `title` -- brief
2. Hook -- go directly into content. No agenda slide.

### 4.5 Closing Conventions

1. `content` -- recap/summary (key takeaways)
2. Callback slide (reference the opening hook) -- type varies by hook type
3. `closing` -- call to action + resources/contact

---

## 5. Visual Direction Prose Guidance

The `visual_direction` field on each slide provides prose guidance for Image Services. It must be specific enough for prompt engineering but not prescriptive about implementation.

### 5.1 What Visual Direction Includes

- **Subject matter:** What the image should depict ("server room with glowing network connections", "diverse team collaborating around a whiteboard")
- **Mood/atmosphere:** Emotional tone ("warm and inviting", "dramatic and high-contrast", "clean and clinical")
- **Composition hints:** Where the subject sits in frame ("subject left with open space right for text overlay", "centered with radial symmetry")
- **Colour alignment:** References to StyleGuide palette ("use brand primary blue as dominant tone", "warm palette consistent with section mood")
- **Negative space requirement:** Whether text will overlay the image ("needs clear area in lower-third for headline", "full-bleed with no text overlay")

### 5.2 What Visual Direction Does NOT Include

- Specific model or provider names (that is the imagegen-bridge's decision)
- Prompt syntax or tokens (visual_direction is human-readable prose, not a prompt)
- Exact hex colours (reference the palette semantically)
- Technical generation parameters (dimensions, steps, seed)

### 5.3 Visual Direction by Slide Type

| Slide Type | Visual Direction Focus |
|------------|----------------------|
| `title` | Full-bleed hero image with negative space for title text |
| `section_divider` | No image needed (solid dark background) or subtle texture |
| `content` | Supporting illustration in right zone, 3:4 aspect ratio |
| `image_feature` | Hero image in upper zone, subject-centric, high impact |
| `data_chart` | No image (chart is the visual); may note chart colour guidance |
| `stat_callout` | No image; visual emphasis is typographic |
| `quote` | No image or subtle background texture |
| `blank_visual` | Full-bleed storytelling image, cinematic composition |
| `icon_grid` | Icon style description (flat, outlined, filled) + subject per icon |

### 5.4 Visual Type Assignment

Each slide gets a `visual_type` from: `hero_image`, `diagram`, `chart`, `icon_set`, `pattern_background`, `none`.

| Slide Type | Default visual_type | Override When |
|------------|-------------------|---------------|
| `title` | `hero_image` | No image needed: `pattern_background` |
| `section_divider` | `none` | Decorative: `pattern_background` |
| `content` | `hero_image` | Text-only: `none` |
| `image_feature` | `hero_image` | -- |
| `data_chart` | `chart` | -- |
| `stat_callout` | `none` | -- |
| `quote` | `none` | Background texture: `pattern_background` |
| `icon_grid` | `icon_set` | -- |
| `diagram` | `diagram` | -- |
| `closing` | `none` | Brand image: `hero_image` |
| `blank_visual` | `hero_image` | -- |
| `two_column` | `hero_image` | Comparison: `none` |

---

## 6. Anti-Patterns

- **Proposing more than 3 arc options.** Choice paralysis. Propose 2-3, curated for the specific talk.
- **Seeking per-slide approval.** Stage 2 is autonomous. The arc was approved; individual slides are craft decisions.
- **Using academic paper titles as headlines.** Headlines should be punchy and conference-ready: "Revenue Doubled -- Here's How" not "Analysis of Revenue Growth Factors."
- **Ignoring structural overhead.** Raw content slide count without section dividers, title, and closing produces too few slides.
- **Consecutive data slides.** Follow every data_chart with interpretation. Never stack two data-heavy slides without a breathing slide between them.
- **Empty visual_direction.** Every slide that needs imagery must have specific prose guidance. "Add an image" is not direction.
- **Exceeding 5 body points per slide.** Schema-enforced maximum for projection readability.

---

## Sources

- Research #08 (Narrative Arc & Conference Storytelling Patterns): Sections 1-6 (16 arc structures, slide density, invisible slides, conference analysis, sequencing rules, speaker notes intelligence)
- Content Services L1 architecture document: narrative-architect workflow, responsibilities, constraints
- Schema: `src/schemas/slide_outline.schema.json` (output contract)
