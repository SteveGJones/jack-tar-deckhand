# Slide Layout Intelligence & Design Rules Engine

> **Research Report for Jack-Tar Deckhand**
> Date: 2026-03-29 | Status: Complete | Scope: All 7 research areas

---

## Quick Reference: Top 10 Rules

| # | Rule | Threshold | Severity |
|---|------|-----------|----------|
| 1 | **Minimum font size (keynote)** | Body text >= 28pt; titles >= 36pt | Error |
| 2 | **Maximum words per slide** | <= 30 words (exclude speaker notes) | Warning |
| 3 | **Margin safe zone** | All content >= 0.5" (457,200 EMU) from edges | Error |
| 4 | **Contrast ratio** | Text-to-background >= 4.5:1 (WCAG AA) | Error |
| 5 | **Maximum bullet points** | <= 5 per slide (prefer <= 4) | Warning |
| 6 | **White space ratio** | >= 40% of slide area should be empty | Warning |
| 7 | **Font count limit** | <= 2 font families per deck | Warning |
| 8 | **Colour palette limit** | <= 5 colours per deck (excluding images) | Warning |
| 9 | **Title hierarchy ratio** | Title font >= 1.5x body font size | Warning |
| 10 | **One idea per slide** | Each slide should convey a single core message | Info |

---

## Table of Contents

1. [Slide Layout Archetypes](#1-slide-layout-archetypes)
2. [Design Grid System for 16:9 Slides](#2-design-grid-system-for-169-slides)
3. [Professional Design Principles](#3-professional-design-principles)
4. [Academic Work on Computational Slide Layout](#4-academic-work-on-computational-slide-layout)
5. [Beautiful.ai Reverse Engineering](#5-beautifulai-reverse-engineering)
6. [Projection-Specific Design Requirements](#6-projection-specific-design-requirements)
7. [Machine-Checkable Layout Rules](#7-machine-checkable-layout-rules)
8. [Implementation Priority](#8-implementation-priority)
9. [Sources](#9-sources)

---

## 1. Slide Layout Archetypes

Based on cross-referencing professional presentation design sources, Beautiful.ai's template taxonomy, PowerPoint's built-in layouts, and Slidev's layout system, the following 18 fundamental layout archetypes emerge.

### 1.1 Archetype Catalogue

| # | Archetype | Purpose | Content Zones | Typical Position in Talk |
|---|-----------|---------|---------------|--------------------------|
| 1 | **Title Slide** | Opening; establish topic and speaker | Centre-aligned title + subtitle; optional logo, date, speaker name at bottom | First slide |
| 2 | **Section Divider** | Mark major section transitions | Large section number/title; optional subtitle; minimal background graphic | Between major sections |
| 3 | **Agenda / Table of Contents** | Preview structure; aid navigation | Numbered list of sections; optional hyperlink anchors; highlight current section | Near start; repeated with highlight |
| 4 | **Single Point** | One big idea or statement | Single large text block (centred or rule-of-thirds positioned); full whitespace | Anywhere — key messages |
| 5 | **Two-Column** | Compare, contrast, or show cause/effect | Left zone + right zone of equal width; shared title at top | Comparisons, pros/cons |
| 6 | **Three-Column** | Multiple parallel items | Three equal-width zones; shared title; optional icons above each column | Features, options, team bios |
| 7 | **Image — Full Bleed** | Emotional impact, visual storytelling | Image covers 100% of slide; overlaid text with semi-transparent backing | Impact moments |
| 8 | **Image — Half Bleed** | Image + explanation | Image covers 50% (left or right); text in opposite half | Explanations with visual evidence |
| 9 | **Image — Corner/Inset** | Supporting visual with primary text | Main text area (60-70%); image inset in corner (30-40%) | Supporting evidence |
| 10 | **Stat Callout / Big Number** | Highlight a key metric | Giant number (100pt+); brief label below; optional context line | Data emphasis |
| 11 | **Icon Grid** | Multiple features, values, or steps | Grid of 3-6 icon + label pairs; equal spacing; shared title | Feature overviews |
| 12 | **Quote / Testimonial** | Social proof, authority | Large quotation marks; quote text centred; attribution below | Persuasion, credibility |
| 13 | **Comparison** | Side-by-side evaluation | Two or three columns with headers; optional check/cross icons; shared title | Decision support |
| 14 | **Timeline / Process** | Show sequence or progression | Horizontal or vertical line with milestone markers; dates/labels per marker | Process flows, history |
| 15 | **Data / Chart** | Present quantitative evidence | Chart occupies 60-70% of slide; title + single insight callout | Data-driven arguments |
| 16 | **Team / Bio** | Introduce people | Photo + name + role per person; grid layout (2-6 people) | Team introductions |
| 17 | **Closing / CTA** | Final slide; call to action | Central message; contact details; QR code or URL; social handles | Last slide |
| 18 | **Blank / Breathing Room** | Visual pause; let audience reflect | No content or very minimal background element | Between dense sections |

### 1.2 Content Zone Specifications

For a standard 16:9 slide (13.333" x 7.5" = 12,192,000 x 6,858,000 EMU):

**Title Slide Zones:**
- Title: centred, Y = 35-45% of slide height, width = 80% of slide width
- Subtitle: centred, Y = 50-60%, width = 60% of slide width
- Footer: bottom 10% for date, logo, speaker name

**Two-Column Zones:**
- Title bar: top 15% (Y: 0 to 1,028,700 EMU)
- Left column: X = 5% to 48%, Y = 18% to 90%
- Right column: X = 52% to 95%, Y = 18% to 90%
- Gutter: 4% of slide width between columns

**Full-Bleed Image Zones:**
- Image: 100% coverage (0,0 to slide width, slide height)
- Text overlay: positioned in bottom-third or left-third
- Semi-transparent backing rectangle: 40-60% opacity black/dark

---

## 2. Design Grid System for 16:9 Slides

### 2.1 The 12-Column Grid

A 12-column grid is the standard for 16:9 widescreen slides, borrowed from web design principles. The beauty of 12 columns lies in divisibility: halves (6+6), thirds (4+4+4), quarters (3+3+3+3), sixths, and twelfths all divide evenly.

**Grid Specifications for 13.333" x 7.5" Slides:**

| Property | Inches | EMU | Pixels (96 DPI) |
|----------|--------|-----|------------------|
| Slide width | 13.333" | 12,192,000 | 1280 |
| Slide height | 7.5" | 6,858,000 | 720 |
| Margin (each side) | 0.5" | 457,200 | 48 |
| Content area width | 12.333" | 11,277,600 | 1184 |
| Content area height | 6.5" | 5,943,600 | 624 |
| Column width (12-col) | 0.861" | 787,400 | 83 |
| Gutter width | 0.167" | 152,400 | 16 |

**Grid Divisions:**

| Layout | Columns Used | Content Width Each | Use Case |
|--------|-------------|-------------------|----------|
| Full width | 12 | 12.333" / 11,277,600 EMU | Title slides, full-bleed |
| Two-column | 6 + 6 | 5.833" each | Comparisons, image+text |
| Three-column | 4 + 4 + 4 | 3.722" each | Features, team bios |
| Four-column | 3 + 3 + 3 + 3 | 2.667" each | Icon grids |
| Sidebar + main | 4 + 8 | 3.722" + 8.111" | Navigation, ToC + content |
| Main + sidebar | 8 + 4 | 8.111" + 3.722" | Content + supporting info |

### 2.2 Row System

A 6-row system complements the 12-column grid:

| Row | Purpose | Y-start (EMU) | Height (EMU) |
|-----|---------|---------------|--------------|
| Row 1 | Title bar | 457,200 | 990,600 |
| Row 2 | Subtitle / breadcrumb | 1,447,800 | 990,600 |
| Row 3-5 | Main content area | 2,438,400 | 2,971,800 |
| Row 6 | Footer / page number | 5,410,200 | 990,600 |

### 2.3 Safe Zones

**Presentation Safe Zones (adapted from broadcast standards):**

| Zone | Inset from Edge | Purpose |
|------|----------------|---------|
| **Action Safe** | 3.5% (0.467" / 426,720 EMU) | All visual content must be inside this boundary |
| **Title Safe** | 5% (0.667" / 609,600 EMU) | All text and critical graphics must be inside |
| **Content Margin** | 0.5" (457,200 EMU) | Recommended minimum for professional presentations |
| **Comfortable Margin** | 0.75" (685,800 EMU) | Recommended for keynote-style presentations |

### 2.4 python-pptx Coordinate Reference

In python-pptx, all positions use EMU (English Metric Units):
- **1 inch = 914,400 EMU**
- **1 cm = 360,000 EMU**
- **1 point = 12,700 EMU**
- **1 pixel (96 DPI) = 9,525 EMU**

```python
from pptx.util import Inches, Pt, Emu

# Standard 16:9 slide
SLIDE_WIDTH = Inches(13.333)   # 12,192,000 EMU
SLIDE_HEIGHT = Inches(7.5)     # 6,858,000 EMU

# Safe margins
MARGIN = Inches(0.5)           # 457,200 EMU
CONTENT_LEFT = MARGIN
CONTENT_TOP = MARGIN
CONTENT_WIDTH = SLIDE_WIDTH - (2 * MARGIN)
CONTENT_HEIGHT = SLIDE_HEIGHT - (2 * MARGIN)

# 12-column grid
GUTTER = Inches(0.167)         # 152,400 EMU
COL_WIDTH = (CONTENT_WIDTH - 11 * GUTTER) / 12
```

---

## 3. Professional Design Principles

### 3.1 Nancy Duarte (Slide:ology, The Glance Test)

**The Glance Test** quantifies slide effectiveness by calculating a signal-to-noise ratio. Seven dimensions are scored: message singularity, audience relevance, visual clarity, data presentation, diagram helpfulness, arrangement, and animation.

- **Benchmark**: Typical business score is 4:7 (signal:noise). After training, scores reach 9:1 or better. A ratio of 5:1 or better passes the three-second glance test.
- **Three-Second Rule**: Presentations are "glance media" -- more closely related to billboards than documents. Can the message be processed in 3 seconds?
- **Signal amplifiers**: Clear focal point, relevant imagery, declarative titles, minimal text
- **Noise sources**: Decorative elements, redundant labels, excessive animation, clipart

**Quantitative Guidelines from Slide:ology:**
- Maximum 30 words per slide
- No more than 5 bullet points per slide
- Minimum 28pt font size (Kawasaki's 10/20/30 rule suggests 30pt)
- Pie charts: maximum 8 sections; largest starts at 12 o'clock
- Rule of Thirds for image composition and focal points

Sources: [Duarte Glance Test](https://www.duarte.com/resources/guides-tools/the-glance-test/), [Slide:ology Book Summary](https://medium.com/@brijsethi/slide-ology-nancy-duarte-book-summary-835a3144a1c8)

### 3.2 Garr Reynolds (Presentation Zen)

**Core Philosophy**: Simplicity, restraint, naturalness -- drawn from Japanese Zen aesthetics.

**Key Principles:**
1. **Simplicity**: Remove all superfluous elements. Embrace empty space.
2. **No "Slideuments"**: Slides support narration; they are not standalone documents. Quality slides are "virtually meaningless without the narration."
3. **Signal-to-Noise Ratio**: Minimize irrelevant information. Remove decorative elements, thin grid lines, footers, logos unless they serve the message.
4. **Design for Distance**: Think like highway signage. Audience should grasp meaning in approximately three seconds.
5. **Large, Full-Screen Images**: One powerful full-bleed image outperforms multiple smaller images.
6. **Contrast Principle**: Direct attention through strong visual differences. One clear focal point per slide.
7. **Rule of Thirds**: Place subjects at intersection points rather than centre.
8. **Restrain, Reduce, Emphasise**: For charts and data -- eliminate clutter, remove nonessential elements, use colour contrast and declarative titles.
9. **Typography**: Sans-serif for projected slides; one sans-serif + one accent font maximum; large sizes with adequate spacing.
10. **Colour Strategy**: Cool colours (blue, green) recede; warm colours (orange, red) advance. Dark backgrounds + light text for dark rooms; light backgrounds + dark text for lit spaces. Limit palette to 2-3 colours.
11. **Minimal Animation**: Avoid excessive transitions. Limit to 2-3 transition types across entire deck.

Sources: [Garr Reynolds Design Tips](https://www.garrreynolds.com/design-tips), [Presentation Zen](https://presentationzen.com/)

### 3.3 Edward Tufte (Data-Ink Ratio)

**Data-Ink Ratio**: The proportion of ink used to display data divided by total ink. Maximise data-ink; erase non-data-ink and redundant data-ink.

**Chartjunk**: Excessive use of graphical effects -- moiré vibration, heavy grids, 3D effects, self-promoting graphics that demonstrate the designer's ability rather than display data.

**Two Erasure Strategies:**
1. Erase non-data-ink: gridlines, meaningless colours, 3D effects, annotations that don't add to the message
2. Erase redundant data-ink: unnecessary legends, excessive labels, redundant information

**Projection-Specific Recommendation**: Tufte recommends testing in actual conditions. Use ivory/cream rather than pure white backgrounds to reduce video glare. The figure/ground contrast must overcome ambient light in the venue.

Sources: [Tufte's Principles](https://thedoublethink.com/tuftes-principles-for-visualizing-quantitative-information/), [Tufte on Projected Presentations](https://www.edwardtufte.com/notebook/recommended-background-for-projected-presentations/)

### 3.4 Evidence-Based Cognitive Science Principles

**Mayer's Multimedia Learning Principles (applied to slides):**
- **Redundancy Principle**: People learn better from graphics and narration than from graphics, narration, AND printed text
- **Temporal Contiguity**: Objects should appear only when mentioned
- **Signalling Principle**: Use cues (arrows, labels, circles) to guide attention toward essential material
- **Coherence Principle**: Remove extraneous material that doesn't support the learning objective

**Kosslyn's Principle of Salience**: "Attention is drawn to large perceptible differences." Use size, colour, and position to create clear focal points.

**Miller's Law (revised)**: Working memory holds 3-5 items (not 7 as originally believed). Maximum 4 bullets per slide, each containing 4 or fewer concepts.

**De-emphasis technique**: Previously discussed items should have reduced opacity (25%) to focus attention on current content.

Sources: [UCSD Evidence-Based Recommendations](https://multimedia.ucsd.edu/best-practices/presentation-design.html), [Rule of Seven Research](https://twistly.ai/the-rule-of-seven-optimal-slide-content-for-maximum-retention/)

### 3.5 The Squint Test

**What it is**: Squint your eyes at a slide so everything becomes blurry. Only the largest, most basic shapes should be perceivable. The elements that remain visible are what truly matters.

**The SPECS Framework for Visual Hierarchy:**
- **S -- Size**: Larger elements attract attention first. Titles and key stats should dominate.
- **P -- Position**: Placement guides the eye. Viewers scan top-left to bottom-right (Z-pattern).
- **E -- Elements**: Less is more. Remove unnecessary charts, icons, or text competing with the main message.
- **C -- Colour**: Use bold, contrasting colours for key elements; mute secondary ones.
- **S -- Strength**: Adjust weight, opacity, or brightness to emphasise important content.

**Key threshold**: Users take less than 10 seconds to focus on key information on a slide.

Sources: [Squint Test Explained](https://medium.com/design-bootcamp/have-you-heard-of-the-squint-test-95f26f6e3b9), [SPECS Framework](https://slidely.ai/blog/fixing-visual-hierarchy-in-presentations-the-squint-test-and-specs-framework)

### 3.6 White Space

**The 2/3 Rule**: Aim for approximately 2/3 of the slide to be white space, with 1/3 for content.

**Types of White Space:**
- **Active white space**: Deliberately created around elements to create focus and focal points
- **Passive white space**: Natural spacing between text lines, graphic elements, and page margins

**Cognitive benefit**: Good use of white space increases comprehension and helps audiences organise information.

Sources: [Presentation Process](https://www.presentation-process.com/slide-design.html), [BrightCarbon Whitespace](https://www.brightcarbon.com/blog/presentation-whitespace/)

### 3.7 Typography Hierarchy

**Classical typographic scale ratios (musical intervals):**

| Ratio Name | Value | Example (28pt base) |
|------------|-------|---------------------|
| Minor Second | 1.067 | 30pt |
| Major Second | 1.125 | 32pt |
| Minor Third | 1.200 | 34pt |
| Major Third | 1.250 | 35pt |
| **Perfect Fourth** | **1.333** | **37pt** |
| Augmented Fourth | 1.414 | 40pt |
| Perfect Fifth | 1.500 | 42pt |
| **Golden Ratio** | **1.618** | **45pt** |

**Recommended scale for keynote presentations (Perfect Fourth 1.333):**

| Element | Size | % of Slide Height |
|---------|------|--------------------|
| Title | 44pt | ~6.5% |
| Subtitle | 33pt | ~4.9% |
| Body text | 28pt | ~4.1% |
| Caption | 21pt | ~3.1% |
| Footnote | 16pt | ~2.4% |

Sources: [Typographic Scale](https://spencermortensen.com/articles/typographic-scale/), [BrightCarbon Font Size](https://www.brightcarbon.com/blog/presentation-font-size/)

### 3.8 Background and Contrast for Projection

**Light background + dark text:**
- 26% more accurate reading (Bauer & Cavonius, 1980)
- More resilient to washed-out projectors and ambient light
- Preferred for well-lit conference rooms

**Dark background + light text:**
- Less eye strain in dimly-lit theatres
- Risk of halation (glowing text effect) affecting ~50% of people with astigmatism
- Avoid pure white on pure black; use off-white on dark grey

**Recommendation**: Default to light background (ivory/light grey, not pure white) with dark text. Offer dark theme variant for theatre-style venues. Always test in actual conditions.

Sources: [Tufte on Backgrounds](https://www.edwardtufte.com/notebook/recommended-background-for-projected-presentations/), [Stephanie Walter](https://stephaniewalter.design/blog/create-better-conference-presentations-slides/)

---

## 4. Academic Work on Computational Slide Layout

### 4.1 SlideCoder (EMNLP 2025)

**Paper**: "SlideCoder: Layout-aware RAG-enhanced Hierarchical Slide Generation from Design"
**Venue**: EMNLP 2025 | **Code**: [github.com/vinsontang1/SlideCoder](https://github.com/vinsontang1/SlideCoder)

**Key Innovation**: Layout-aware framework that decomposes slide images using a Color Gradient-based Segmentation (CGSeg) algorithm, then generates editable code through hierarchical RAG.

**Technical Approach:**
1. **CGSeg**: Recursively decomposes slides through colour analysis -- divides into grids, computes Sobel gradient magnitudes, identifies activated blocks, applies flood-fill, and recursively segments sub-images while preserving positional metadata
2. **H-RAG**: Dual-level knowledge bases -- Shape Type KB (python-pptx terminology) and Operation Function KB (syntax and parameters). All agents query via BGE M3-Embedding with cosine similarity.
3. **Three-Agent Pipeline**: Describer (global + block-level descriptions) -> Coder (code from block descriptions) -> Assembler (combines with layout-aware coordinates)
4. **Slide Complexity Metric (SCM)**: Combines element count, type diversity, and Element Coverage Ratio. Correlates strongly with human judgment (r=0.873).

**Results**: Outperforms baselines by 40.5 points (simple), 34.0 (medium), 29.9 (complex). SlideMaster (7B) supports 44 object styles vs competitors' 16.

**Relevance**: The CGSeg approach and python-pptx shape taxonomy are directly applicable to layout rule checking.

### 4.2 PPTAgent (EMNLP 2025)

**Paper**: "PPTAgent: Generating and Evaluating Presentations Beyond Text-to-Slides"
**Venue**: EMNLP 2025 | **Code**: [github.com/icip-cas/PPTAgent](https://github.com/icip-cas/PPTAgent)

**Key Innovation**: Analyses reference presentations to extract slide-level functional types and content schemas, then generates editing actions to create new slides.

**Technical Approach:**
1. **Stage I -- Analysis**: Clusters slides into structural vs content types using hierarchical clustering on layout similarity. Extracts content schemas defining each element through category, description, and content.
2. **Stage II -- Generation**: Generates outlines, then produces editing actions (del_span, del_image, clone_paragraph, replace_span, replace_image) modifying reference slides. Uses HTML rendering for precision.
3. **PPTEval Framework**: Three dimensions evaluated on 1-5 scale:
   - **Content**: Text conciseness, grammar, image relevance
   - **Design**: Harmonious colours, proper layout, readability, no overlapping elements
   - **Coherence**: Progressive structure, background information inclusion

**Results**: Average score 3.67/5 across three dimensions; 97.8% success rate. PPTEval achieves 0.71 Pearson correlation with human preferences.

### 4.3 SlideGen (December 2025)

**Paper**: "SlideGen: Collaborative Multimodal Agents for Scientific Slide Generation"
**Archive**: [arxiv.org/abs/2512.04529](https://arxiv.org/abs/2512.04529)

**Key Innovation**: Six coordinated vision-language agents for paper-to-slide generation.

**Agent Architecture:**
1. **Outliner**: Constructs presentation structure, assigns bullet points
2. **Mapper**: Attaches figures and tables to corresponding text
3. **Formulizer**: Handles equations
4. **Speaker**: Generates presenter notes
5. **Arranger**: Selects templates and places assets based on planned content
6. **Refiner**: Merges sparse slides, adjusts layout consistency, applies visual emphasis

**Evaluation Dimensions**: Visual Aesthetics (geometry-aware density score), Communication Effectiveness (SlideQA), Holistic Quality (VLM-as-Judge), Textual Coherence.

**Relevance**: The Arranger agent's template selection and the Refiner agent's layout consistency checks are directly relevant to our rules engine.

### 4.4 Auto-Slides (ICME 2026)

**Paper**: "Auto-Slides: An Interactive Multi-Agent System for Creating and Customizing Research Presentations"
**Archive**: [arxiv.org/abs/2509.11062](https://arxiv.org/abs/2509.11062) | **Code**: [github.com/Westlake-AGI-Lab/Auto-Slides](https://github.com/Westlake-AGI-Lab/Auto-Slides)

**Key Innovation**: Three-phase pipeline with human-in-the-loop editing via natural language dialogue.

**Pipeline:**
1. **Content Understanding**: Parser + Planner agents analyse source and design slide structure in JSON
2. **Quality Assurance**: Verification + Adjustment agents ensure content fidelity
3. **Generation + Interaction**: Generator produces LaTeX slides; Editor agent facilitates revisions

### 4.5 SlidesGen-Bench (January 2026)

**Paper**: "SlidesGen-Bench: Evaluating Slides Generation via Computational and Quantitative Metrics"
**Archive**: [arxiv.org/abs/2601.09487](https://arxiv.org/abs/2601.09487)

**Key Innovation**: Unified evaluation framework treating outputs as renderings (agnostic to generation method). Three dimensions: Content, Aesthetics, and Editability. Includes Slides-Align1.5k human-preference dataset covering nine generation systems across seven scenarios.

### 4.6 DECKBench (February 2026)

**Paper**: "DECKBench: Benchmarking Multi-Agent Frameworks for Academic Slide Generation and Editing"
**Archive**: [arxiv.org/abs/2602.13318](https://arxiv.org/abs/2602.13318)

**Key Innovation**: Multi-level evaluation (slide-level, deck-level, interaction-level) with both reference-free and reference-based metrics. Uses Hungarian matching to align generated slides with ground truth. Metrics include Perplexity, Faithfulness, Text Similarity, Figure Similarity, and Layout Quality.

### 4.7 Constraint-Based Layout (Foundational)

The **Cassowary algorithm** (Badros & Borning, 1999) provides the foundational constraint solver for layout systems, solving hundreds of constraints in fractions of a second. Modern approaches like **Scout** introduce high-level constraints based on design concepts (semantic structure, emphasis, order) and formalise them into low-level spatial constraints.

**Relevance**: Our rules engine takes a constraint-checking approach (validate against rules) rather than constraint-solving approach (generate layouts from constraints), but understanding the constraint formalism informs rule design.

---

## 5. Beautiful.ai Reverse Engineering

### 5.1 Smart Slide Template Taxonomy

Beautiful.ai offers **300+ Smart Slide layouts** in 8 categories:

| Category | Description | Key Templates |
|----------|-------------|---------------|
| **Impact** | Headlines, countdowns, word clouds | Headline Slide, Word Cloud, Countdown, Big Number |
| **Structural** | Agendas, section breaks, titles | Title Slide, Agenda, Section Break, Contact Slide |
| **Data & Charts** | Bar charts, line charts, dashboards | Bar Graph, Column Chart, Line Chart, Pie/Donut, Waterfall, Gantt |
| **Comparison** | SWOT, Venn, comparison charts | SWOT Analysis, Venn Diagram, Data Comparison, Quadrant |
| **Diagrams & Timelines** | Timelines, flowcharts, funnels | Flowchart, Process Diagram, Funnel, Pyramid, Timeline, Journey Map |
| **Essentials** | Text, bullets, tables | Text Slide, Bullet Slide, Table Slide, Number List |
| **Product & Customer** | Screenshots, logos, ROI | Product Screenshot, Logo Grid, Desktop/Laptop Mockup |
| **People** | Team, org charts, quotes | Team, Org Chart, Quotation, About Us |

### 5.2 Auto-Layout Mechanics

**What Beautiful.ai enforces:**
1. **Auto-alignment**: Content realigns automatically as elements are added/removed
2. **Responsive resizing**: Text and visual components resize proportionally based on content volume
3. **Spacing intelligence**: Gaps between elements auto-adjust to maintain visual balance
4. **Brand consistency**: Themes synchronise fonts, colours, and logos across all slides
5. **Hierarchy enforcement**: Font sizing relationships and visual hierarchy maintained automatically
6. **Content density limits**: "Forced" constraints prevent cluttering -- users cannot freely position elements or fine-tune at pixel level

**What it prohibits:**
- Free-form element positioning
- Pixel-level customisation
- Unconventional layouts that break template structure
- Overlapping elements

### 5.3 Lessons for Our Rules Engine

Beautiful.ai's approach validates that:
1. **Constraint-based design works**: Users initially resist constraints but produce better presentations
2. **Template-first approach**: Matching content to pre-defined layout archetypes is more reliable than free-form generation
3. **Auto-spacing is critical**: Consistent gutters, margins, and alignment are the highest-impact rules
4. **Content density must be limited**: Automatic reflow when too much content is added

### 5.4 Slidebean's Approach

Slidebean uses a **genetic algorithm** to automatically arrange content by analysing predefined design traits, generating layouts that ensure professional consistency. Users focus on content; the AI handles layout, alignment, and design.

Sources: [Beautiful.ai Smart Slides](https://www.beautiful.ai/smart-slides), [Beautiful.ai Templates](https://www.beautiful.ai/slide-templates), [Slidebean](https://slidebean.com/)

---

## 6. Projection-Specific Design Requirements

### 6.1 Font Size by Venue

| Venue Type | Body Text Min | Title Min | Distance Rule |
|------------|--------------|-----------|---------------|
| Small meeting room (< 20 people) | 24pt | 36pt | Readable at 6-10 feet |
| Medium conference room (20-100) | 28pt | 40pt | Readable at 20-30 feet |
| Large auditorium (100-500) | 32pt+ | 48pt+ | Readable at 50-100 feet |
| Keynote theatre (500+) | 36pt+ | 54pt+ | Readable at 100+ feet |

**Font Size as Percentage of Slide Height:**

| Presentation Type | Title | Headers | Body | Caption |
|-------------------|-------|---------|------|---------|
| Keynote | ~6.5% | ~5% | ~4% | ~3% |
| Training/Sales | ~4% | ~3% | ~2% | ~1.5% |

**AVIXA Standard**: Provide 1 inch of text height for every 15 feet of maximum viewing distance. For 1080 resolution, 20pt font = 2.5% element height.

### 6.2 Contrast Requirements

| Standard | Normal Text | Large Text (>= 24pt or >= 18pt bold) |
|----------|-------------|--------------------------------------|
| WCAG 2.1 AA | >= 4.5:1 | >= 3:1 |
| WCAG 2.1 AAA | >= 7:1 | >= 4.5:1 |
| **Projection (recommended)** | **>= 7:1** | **>= 4.5:1** |

Projection environments require stricter contrast than screen viewing due to ambient light washout. Use AAA ratios as the minimum for projected content.

### 6.3 Resolution and Aspect Ratio

| Property | Specification |
|----------|--------------|
| Standard aspect ratio | 16:9 |
| Fallback aspect ratio | 16:10 (letterbox 16:9 content) |
| Legacy aspect ratio | 4:3 (avoid if possible) |
| Minimum resolution | 1920 x 1080 (1080p) |
| Optimal resolution | 3840 x 2160 (4K) for large venues |
| Slide dimensions | 13.333" x 7.5" (Widescreen) |
| Large-venue projector | 12,000 - 30,000 lumens, laser, 3-DLP |
| Minimum ambient for legibility | 400 lx projection illuminance |

### 6.4 Viewing Distance Rules

| Rule | Specification |
|------|--------------|
| First row minimum distance | Equal to screen width (e.g., 20' screen = 20' minimum) |
| Last row maximum distance | 8x screen height (e.g., 12' screen = 96' maximum) |
| AVIXA DISCAS BDM | Image height to furthest viewer = factor of 5 (at 1080p, 20pt) |
| Screen angle limits | 45 degrees to each side; top within 30 degrees above eye level |

### 6.5 Background Colour for Projection

**Default recommendation**: Light background (ivory #FFFFF0 or light grey #F5F5F5, not pure white #FFFFFF) with dark text (#333333, not pure black #000000).

**Dark theme variant**: Dark grey (#2D2D2D) with off-white text (#E8E8E8). Use only for controlled theatre-style lighting.

Sources: [AVIXA DISCAS](https://www.avixa.org/standards/discas-calculators/discas/learn-more-about-display-size), [BrightCarbon Font Size](https://www.brightcarbon.com/blog/presentation-font-size/), [WCAG Contrast](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)

---

## 7. Machine-Checkable Layout Rules

### Rule Format

Each rule follows this structure:
- **Rule ID**: `LAY-NNN` for layout, `TYP-NNN` for typography, `COL-NNN` for colour, `CON-NNN` for content, `PRJ-NNN` for projection
- **Description**: What the rule checks
- **Check Method**: How to detect a violation programmatically
- **Severity**: `error` (must fix), `warning` (should fix), `info` (recommendation)
- **Fix Suggestion**: Automated or manual remediation

### 7.1 Layout Rules

| ID | Description | Check Method | Severity | Fix Suggestion |
|----|-------------|-------------|----------|----------------|
| LAY-001 | Content within safe margins | All shapes: left >= 457,200 EMU, top >= 457,200 EMU, right <= slide_width - 457,200, bottom <= slide_height - 457,200 | error | Move shape inward to nearest grid snap point |
| LAY-002 | No overlapping text boxes | For each pair of text shapes, check if bounding boxes intersect | error | Reposition or resize overlapping elements |
| LAY-003 | Elements aligned to grid | Shape positions should be within 1/4 column-width of nearest grid line | warning | Snap to nearest grid intersection |
| LAY-004 | Consistent margins across deck | Compare margin usage (distance of outermost content from edge) across all slides; std dev < 0.25" | warning | Standardise margins to deck-wide value |
| LAY-005 | Title position consistent | Title placeholder Y-position varies by < 0.25" across slides | warning | Align all titles to same Y coordinate |
| LAY-006 | White space ratio adequate | Calculate total shape area / slide area; content should be <= 60% of slide area | warning | Remove elements or increase spacing |
| LAY-007 | No content in bottom 10% | Critical text/data not in bottom 10% of slide (often obscured by podium, audience heads) | warning | Move content upward |
| LAY-008 | Image aspect ratio preserved | Image width/height ratio matches original file within 5% tolerance | error | Reset image to original proportions |
| LAY-009 | Image resolution adequate | Image pixels >= 150% of displayed size in pixels at 96 DPI | warning | Replace with higher-resolution image |
| LAY-010 | Bleed images touch edges | If image is intended as full-bleed, verify it extends to or beyond all 4 slide edges | info | Extend image to cover full slide |

### 7.2 Typography Rules

| ID | Description | Check Method | Severity | Fix Suggestion |
|----|-------------|-------------|----------|----------------|
| TYP-001 | Minimum font size (keynote) | All text runs >= 28pt (355,600 EMU) for body; >= 36pt for titles | error | Increase font size to minimum |
| TYP-002 | Minimum font size (training) | All text runs >= 16pt for body; >= 20pt for titles | warning | Increase font size |
| TYP-003 | Font family count | Count distinct font families across deck; should be <= 2 | warning | Consolidate to primary + accent font |
| TYP-004 | Title-to-body size ratio | Title font size / body font size >= 1.33 (Perfect Fourth) | warning | Increase title or decrease body size |
| TYP-005 | No thin/decorative fonts | Check font weight; flag Light, Thin, UltraLight weights and script/decorative families | warning | Switch to Regular or Medium weight |
| TYP-006 | Consistent font sizing | Same-level text elements (e.g., all bullet items) use identical font size; variance = 0 | warning | Standardise to most common size at that level |
| TYP-007 | Line spacing adequate | Paragraph line spacing >= 1.2x font size | info | Set line spacing to 1.3-1.5x |
| TYP-008 | No sub-bullets | Detect indent level > 1 in bullet lists | warning | Flatten to single-level bullets or split into separate slides |

### 7.3 Colour Rules

| ID | Description | Check Method | Severity | Fix Suggestion |
|----|-------------|-------------|----------|----------------|
| COL-001 | Text contrast ratio | Calculate relative luminance contrast between text colour and background; >= 4.5:1 for normal text, >= 3:1 for large text | error | Adjust text or background colour |
| COL-002 | Palette size | Count distinct colours used across deck (excluding images); <= 5 | warning | Consolidate to brand palette |
| COL-003 | Consistent colour usage | Same semantic role (e.g., all titles) uses same colour across deck | warning | Apply consistent colour mapping |
| COL-004 | No pure black on pure white | If bg = #FFFFFF and text = #000000, flag for projection glare | info | Use #333333 on #F5F5F5 instead |
| COL-005 | Colour not sole indicator | Information conveyed by colour also has text label, pattern, or icon | warning | Add redundant non-colour indicator |
| COL-006 | Projection-safe contrast | For projected content, contrast ratio >= 7:1 | warning | Increase contrast for projection use |

### 7.4 Content Rules

| ID | Description | Check Method | Severity | Fix Suggestion |
|----|-------------|-------------|----------|----------------|
| CON-001 | Word count per slide | Count all visible text words; <= 30 for keynote, <= 75 for training | warning | Move excess text to speaker notes |
| CON-002 | Bullet count per slide | Count top-level bullet paragraphs; <= 5 (prefer <= 4) | warning | Split into multiple slides |
| CON-003 | Words per bullet | Each bullet item <= 10 words | info | Shorten to key phrases |
| CON-004 | One idea per slide | Heuristic: if slide has > 1 title-sized text element, or > 2 distinct content groups, flag | info | Split into separate slides |
| CON-005 | No full sentences in bullets | Detect periods at end of bullet text (excluding abbreviations) | info | Convert to fragments |
| CON-006 | Chart has declarative title | Chart slide title should contain a finding, not a label (e.g., "Sales grew 23%" not "Sales Data") | info | Rewrite title as insight statement |
| CON-007 | Pie chart segment limit | Pie/donut charts have <= 8 segments | warning | Consolidate small segments into "Other" |

### 7.5 Projection / Accessibility Rules

| ID | Description | Check Method | Severity | Fix Suggestion |
|----|-------------|-------------|----------|----------------|
| PRJ-001 | Aspect ratio correct | Slide dimensions match 16:9 (13.333" x 7.5") | error | Resize slide to 16:9 |
| PRJ-002 | No critical content in edges | Text and data shapes not within action-safe zone (3.5% from edges) | error | Move content inward |
| PRJ-003 | Alt text on images | All image shapes have non-empty alt text / description | warning | Add descriptive alt text |
| PRJ-004 | Slide numbers present | Slide number placeholder present and populated | info | Add slide numbers |

---

## 8. Implementation Priority

### Phase 1: Critical Rules (Implement First)

These rules have the highest impact and are straightforward to check:

1. **LAY-001**: Safe margins
2. **TYP-001**: Minimum font size
3. **COL-001**: Contrast ratio
4. **PRJ-001**: Aspect ratio
5. **LAY-002**: No overlapping text
6. **LAY-008**: Image aspect ratio

### Phase 2: High-Value Rules

7. **CON-001**: Word count per slide
8. **CON-002**: Bullet count per slide
9. **TYP-003**: Font family count
10. **COL-002**: Palette size
11. **LAY-006**: White space ratio
12. **TYP-004**: Title-to-body ratio

### Phase 3: Polish Rules

13. **LAY-003**: Grid alignment
14. **LAY-004**: Consistent margins
15. **LAY-005**: Title consistency
16. **TYP-006**: Consistent font sizing
17. **COL-003**: Consistent colour usage
18. **CON-006**: Declarative chart titles

### Phase 4: Advisory Rules

19-35: All remaining `info` severity rules, plus projection-specific checks.

### Layout Archetype Selection Algorithm

When generating slides, select archetype based on content analysis:

```
IF content has single key metric -> Stat Callout (#10)
ELIF content has single quote -> Quote (#12)
ELIF content has comparison of 2 items -> Two-Column (#5) or Comparison (#13)
ELIF content has comparison of 3+ items -> Three-Column (#6) or Comparison (#13)
ELIF content has timeline/sequential data -> Timeline (#14)
ELIF content has chart/data -> Data/Chart (#15)
ELIF content has team/people -> Team/Bio (#16)
ELIF content has 3-6 features/icons -> Icon Grid (#11)
ELIF content has image as primary element -> Full Bleed (#7) or Half Bleed (#8)
ELIF content has single statement -> Single Point (#4)
ELIF content is section transition -> Section Divider (#2)
ELIF content is navigation -> Agenda (#3)
ELIF content is opening -> Title Slide (#1)
ELIF content is closing -> Closing/CTA (#17)
ELSE -> Single Point (#4) with appropriate content zones
```

---

## 9. Sources

### Books and Primary Sources

1. Duarte, N. (2008). *Slide:ology: The Art and Science of Creating Great Presentations*. O'Reilly Media. [duarte.com/resources/books/slideology](https://www.duarte.com/resources/books/slideology/)
2. Reynolds, G. (2012). *Presentation Zen Design*. New Riders. [garrreynolds.com](https://www.garrreynolds.com)
3. Tufte, E. (1983). *The Visual Display of Quantitative Information*. Graphics Press. [thedoublethink.com/tuftes-principles](https://thedoublethink.com/tuftes-principles-for-visualizing-quantitative-information/)
4. Mayer, R.E. (2009). *Multimedia Learning*. Cambridge University Press.
5. Kosslyn, S. (2007). *Clear and to the Point*. Oxford University Press.
6. Miller, G.A. (1956). "The Magical Number Seven, Plus or Minus Two." *Psychological Review*.

### Academic Papers

7. SlideCoder (EMNLP 2025): [aclanthology.org/2025.emnlp-main.458](https://aclanthology.org/2025.emnlp-main.458/)
8. PPTAgent (EMNLP 2025): [aclanthology.org/2025.emnlp-main.728](https://aclanthology.org/2025.emnlp-main.728/)
9. SlideGen (Dec 2025): [arxiv.org/abs/2512.04529](https://arxiv.org/abs/2512.04529)
10. Auto-Slides (Sep 2025): [arxiv.org/abs/2509.11062](https://arxiv.org/abs/2509.11062)
11. SlidesGen-Bench (Jan 2026): [arxiv.org/abs/2601.09487](https://arxiv.org/abs/2601.09487)
12. DECKBench (Feb 2026): [arxiv.org/abs/2602.13318](https://arxiv.org/abs/2602.13318)
13. DOC2PPT: [arxiv.org/abs/2101.11796](https://arxiv.org/abs/2101.11796)
14. D2S (NAACL 2021): [aclanthology.org/2021.naacl-main.111](https://aclanthology.org/2021.naacl-main.111.pdf)
15. Badros, G.J. & Borning, A. (1999). "The Cassowary Linear Arithmetic Constraint Solving Algorithm."
16. Bauer, D. & Cavonius, C.R. (1980). "Improving the legibility of visual display units through contrast reversal."

### Professional Design Resources

17. Duarte Glance Test: [duarte.com/resources/guides-tools/the-glance-test](https://www.duarte.com/resources/guides-tools/the-glance-test/)
18. Garr Reynolds Design Tips: [garrreynolds.com/design-tips](https://www.garrreynolds.com/design-tips)
19. BrightCarbon Grid Systems: [brightcarbon.com/blog/advanced-powerpoint-grids-guides](https://www.brightcarbon.com/blog/advanced-powerpoint-grids-guides/)
20. BrightCarbon Font Size: [brightcarbon.com/blog/presentation-font-size](https://www.brightcarbon.com/blog/presentation-font-size/)
21. BrightCarbon Whitespace: [brightcarbon.com/blog/presentation-whitespace](https://www.brightcarbon.com/blog/presentation-whitespace/)
22. Stephanie Walter Conference Slides: [stephaniewalter.design/blog/create-better-conference-presentations-slides](https://stephaniewalter.design/blog/create-better-conference-presentations-slides/)
23. Tufte on Projected Presentations: [edwardtufte.com/notebook/recommended-background-for-projected-presentations](https://www.edwardtufte.com/notebook/recommended-background-for-projected-presentations/)
24. Visme Presentation Layout: [visme.co/blog/presentation-layout](https://visme.co/blog/presentation-layout/)
25. SlideModel Types of Slides: [slidemodel.com/types-of-slides](https://slidemodel.com/types-of-slides/)
26. UCSD Evidence-Based Design: [multimedia.ucsd.edu/best-practices/presentation-design.html](https://multimedia.ucsd.edu/best-practices/presentation-design.html)

### Tool Documentation

27. Beautiful.ai Smart Slides: [beautiful.ai/smart-slides](https://www.beautiful.ai/smart-slides)
28. Beautiful.ai Templates: [beautiful.ai/slide-templates](https://www.beautiful.ai/slide-templates)
29. Slidebean: [slidebean.com](https://slidebean.com/)
30. python-pptx Documentation: [python-pptx.readthedocs.io](https://python-pptx.readthedocs.io/en/latest/)
31. python-pptx Shape Position: [python-pptx.readthedocs.io/en/stable/dev/analysis/shp-pos-and-size.html](https://python-pptx.readthedocs.io/en/stable/dev/analysis/shp-pos-and-size.html)
32. Slidev Layouts: [sli.dev/builtin/layouts](https://sli.dev/builtin/layouts)
33. Microsoft Slide Layouts: [support.microsoft.com -- apply-a-slide-layout](https://support.microsoft.com/en-us/office/apply-a-slide-layout-158e6dba-e53e-479b-a6fc-caab72609689)

### Standards and Specifications

34. WCAG 2.1 Contrast: [w3.org/WAI/WCAG21/Understanding/contrast-minimum.html](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
35. AVIXA DISCAS Standard: [avixa.org/standards/discas-calculators](https://www.avixa.org/standards/discas-calculators/discas/learn-more-about-display-size)
36. Safe Area (Television): [en.wikipedia.org/wiki/Safe_area_(television)](https://en.wikipedia.org/wiki/Safe_area_(television))

### Design Community

37. Squint Test: [medium.com/design-bootcamp/have-you-heard-of-the-squint-test](https://medium.com/design-bootcamp/have-you-heard-of-the-squint-test-95f26f6e3b9)
38. SPECS Framework: [slidely.ai/blog/fixing-visual-hierarchy-in-presentations](https://slidely.ai/blog/fixing-visual-hierarchy-in-presentations-the-squint-test-and-specs-framework)
39. Typographic Scale: [spencermortensen.com/articles/typographic-scale](https://spencermortensen.com/articles/typographic-scale/)
40. Presentation Process White Space: [presentation-process.com/slide-design.html](https://www.presentation-process.com/slide-design.html)
41. Rule of Thirds in Presentations: [sixminutes.dlugan.com/rule-of-thirds-powerpoint](https://sixminutes.dlugan.com/rule-of-thirds-powerpoint/)
