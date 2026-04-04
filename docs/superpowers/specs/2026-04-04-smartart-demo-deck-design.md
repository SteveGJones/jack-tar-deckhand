# Jack-Tar Deckhand Demo Deck — Design Specification

**Date:** 2026-04-04
**Status:** Approved
**Purpose:** Educational read deck that pitches Jack-Tar Deckhand as a product, using every pipeline capability to demonstrate itself. Also serves as a visual regression test for the full SmartArt pipeline.

---

## 1. Overview

A 28-slide read deck (emailed, not presented) that pitches Jack-Tar Deckhand by using it to explain itself. Three-act structure: Act 1 pitches the product, Act 2 walks through the pipeline building this very deck, Act 3 positions the architecture and roadmap.

### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Format | 45-minute read deck, emailed | Self-contained, no speaker needed, information-dense |
| Narrative | Hybrid pitch + journey | Pitch framing for accessibility, journey for education |
| Tone | Mixed technical/business | Must work for engineers AND non-technical decision-makers |
| Brand | Jack-Tar nautical/pirate | Demonstrates brand-manager capability, memorable identity |
| SmartArt coverage | All 10 types, all 4 tiers, all 3 engines | Educational completeness + visual regression test |
| Strategy coverage | All 6 rendering strategies | Proves full pipeline capability |

---

## 2. Brand Profile — Jack-Tar

| Field | Value |
|-------|-------|
| Company | Jack-Tar Deckhand |
| Tagline | "Your AI Crew for Conference-Quality Decks" |
| Primary | `#1B3A4B` (deep navy) |
| Secondary | `#456990` (steel blue) |
| Accent | `#C67B2F` (burnished gold) |
| Background | `#F5F0E8` (parchment cream) |
| Text | `#1A1A1A` (near-black) |
| Chart series | `#1B3A4B`, `#C67B2F`, `#456990`, `#8B4513`, `#2E8B57` |
| Heading font | Playfair Display (serif) |
| Body font | Source Sans Pro (clean sans-serif) |
| Image style | Nautical illustration, aged maritime maps, brass instruments, rope textures. No cartoon pirates. Royal Navy charts meets modern data design. |

---

## 3. Slide-by-Slide Specification

### Act 1: The Pitch (Slides 1-8)

**Slide 1 — Title**
- Headline: "Jack-Tar Deckhand: Your AI Crew for Conference-Quality Decks"
- Subtitle: "How an AI-First Skill Suite Turns Ideas into Presentations"
- Strategy: `full_render`
- SmartArt: none
- Visual: Nautical title card — ship's wheel or compass motif

**Slide 2 — The Problem**
- Headline: "Presentations Are the Dark Matter of Business Communication"
- Body: Hours spent on slides instead of thinking. Design inconsistency. Image hunting. Copy-paste from old decks. Speaker notes as an afterthought. The result: mediocre decks that don't serve the speaker or the audience.
- Strategy: `backdrop`
- SmartArt: none
- Visual: Structured storm scene with figurative elements (scattered slides, clock, frustrated figure), text positioned by vision analysis

**Slide 3 — The Solution**
- Headline: "One Brief In, Conference-Quality Deck Out"
- Body: Core proposition — provide a talk brief (topic, audience, duration, tone), the system produces a complete .pptx with narrative structure, branded visuals, AI-generated images, data charts, intelligent graphics, and timed speaker notes.
- Strategy: `background`
- SmartArt: none
- Visual: Atmospheric nautical calm — clear horizon, calm sea

**Slide 4 — The Pipeline at a Glance**
- Headline: "13 Steps from Brief to Deck"
- visual_intent: "Show the full pipeline as a flowchart"
- Body: validate-brief, brand-manager, slide-stylist, narrative-architect, smartart-selector, strategy-map, smartart-extractor, speaker-notes-writer, imagegen-bridge, smartart-renderer, chart-renderer, deck-assembler, deck-qa
- Strategy: `smartart`
- **SmartArt: flowchart, Mermaid, T1 ai_background**

**Slide 5 — Who It's For**
- Headline: "Built for Speakers Who Think, Not Designers Who Click"
- visual_intent: "Show the target audiences as a Venn diagram"
- Body: Three overlapping audiences — Conference Speakers (need quality fast), Technical Leaders (need architecture diagrams), Business Presenters (need data visualisation). Intersection: anyone with content but not design time.
- Strategy: `smartart`
- **SmartArt: venn, Custom SVG, T2 ai_elements**
- AI element icons: speaker at podium, engineer at keyboard, executive at whiteboard

**Slide 6 — The Competitive Landscape**
- Headline: "How Jack-Tar Compares"
- visual_intent: "Show a feature comparison matrix"
- Body: Compare Jack-Tar vs Manual PowerPoint vs Canva AI vs Beautiful.ai vs Gamma.app across: narrative intelligence, image generation, brand enforcement, SmartArt/data viz, speaker notes, programmatic assembly, quality assurance
- Strategy: `smartart`
- **SmartArt: feature_matrix, Custom SVG, T0 pure_programmatic**

**Slide 7 — Strategic Position**
- Headline: "SWOT: Where Jack-Tar Stands"
- visual_intent: "SWOT analysis of the Jack-Tar platform"
- Body:
  - Strengths: Deep narrative intelligence, 6 AI personas, 3 rendering engines, brand-aware
  - Weaknesses: Requires Claude Code environment, no GUI, learning curve
  - Opportunities: Enterprise deck automation, conference speaker market, education sector
  - Threats: Native AI features in PowerPoint/Google Slides, Canva's API ecosystem
- Strategy: `smartart`
- **SmartArt: swot, Custom SVG, T3 full_ai_render**
- T3 demonstrates full AI render tier; if data fidelity fails, auto-downgrades to T1

**Slide 8 — Capability Radar**
- Headline: "Six Dimensions of Deck Quality"
- visual_intent: "Radar chart comparing Jack-Tar capabilities"
- Body: Narrative Structure: 9/10, Visual Design: 8/10, Image Quality: 8/10, Data Visualisation: 9/10, Brand Consistency: 9/10, Speaker Support: 7/10
- Strategy: `smartart`
- **SmartArt: radar_chart, Vega-Lite, T0 pure_programmatic**

---

### Act 2: The Journey (Slides 9-20)

**Slide 9 — Section Divider**
- Headline: "How It Works: Watch the Pipeline Build This Deck"
- Strategy: `pragmatic_composition`
- SmartArt: none
- Visual: Individual nautical elements (compass, telescope, ship's wheel, map) generated separately, placed at exact coordinates with labels

**Slide 10 — Brand Extraction**
- Headline: "Every Deck Starts with a Brand"
- Body: Explain brand-manager. This deck's nautical palette and Playfair Display headings were derived from a Jack-Tar brand profile. "This slide's styling is proof the system works."
- Strategy: `composed`
- SmartArt: none

**Slide 11 — Narrative Architecture**
- Headline: "The AI Doesn't Just Arrange Slides — It Thinks About Story"
- visual_intent: "Show the decision tree for narrative arc selection"
- Body: Evaluates brief → selects arc pattern. Persuasive? → hook-body-callback-cta. Problem-solving? → situation-complication-resolution. Historical? → chronological. Technical? → deep-dive. Comparison? → compare-contrast.
- Strategy: `smartart`
- **SmartArt: decision_tree, Mermaid, T1 ai_background**

**Slide 12 — SmartArt Selection**
- Headline: "The Selector Sees Structure Where You See Bullets"
- visual_intent: "Show the 10 graphic types mapped to their content triggers as a feature matrix"
- Body: Columns: Content Pattern, Graphic Type, Engine. Rows mapping each pattern to its type.
- Strategy: `smartart`
- **SmartArt: feature_matrix, Custom SVG, T0 pure_programmatic**

**Slide 13 — Data Extraction**
- Headline: "From Prose to Structured Data — No LLM Required"
- Body: Pure Python extraction — regex and string parsing, deterministic and testable. Overflow handling via truncation, pagination, or summarisation.
- Strategy: `composed`
- SmartArt: none

**Slide 14 — Three Rendering Engines**
- Headline: "One Data Structure, Three Ways to Draw It"
- visual_intent: "Show the three rendering engines as a Venn diagram"
- Body: Mermaid (graphs), Vega-Lite (data viz), Custom SVG (spatial). Overlaps: Mermaid + Custom SVG both do flowcharts; Vega-Lite + Matplotlib both do bar/line charts. Comparator runs both, reviewer picks winner.
- Strategy: `smartart`
- **SmartArt: venn, Custom SVG, T0 pure_programmatic**

**Slide 15 — The Comparator Pattern**
- Headline: "Draft Phase: Compete. Production Phase: Execute."
- visual_intent: "Show the draft-to-production funnel"
- Body: All Engines Render → Image Reviewer Scores → Winner Selected → Production Locked. Scoring: data legibility 35%, layout clarity 25%, aesthetics 20%, style compliance 20%.
- Strategy: `smartart`
- **SmartArt: pipeline_funnel, Custom SVG, T1 ai_background**

**Slide 16 — Four Enrichment Tiers**
- Headline: "From Clean SVG to Full AI Render"
- visual_intent: "Show the enrichment tiers as a timeline from simplest to richest"
- Body: T0 Pure SVG → T1 + Background → T2 + Icons → T3 Full AI. Each tier adds visual richness at increasing cost.
- Strategy: `smartart`
- **SmartArt: timeline, Custom SVG, T1 ai_background**

**Slide 17 — Image Generation**
- Headline: "Local Draft, Cloud Production — Try Cheap First"
- visual_intent: "Show the render funnel stages as a pipeline"
- Body: Three-stage funnel. Ollama free → Cloud 720p $0.02 → Cloud 2K+ $0.13. Budget-aware routing.
- Strategy: `smartart`
- **SmartArt: pipeline_funnel, Custom SVG, T0 pure_programmatic**

**Slide 18 — Assembly & QA**
- Headline: "35 Automated Checks Before Any Human Sees It"
- visual_intent: "Show the QA categories as a bar chart"
- Body: 35 checks across 10 categories. Data: Contrast: 4, Margins: 3, Text Overflow: 3, Consistency: 5, Image Quality: 4, Placeholders: 2, Missing Content: 3, Accessibility: 3, Keynote: 3, SmartArt: 5
- Strategy: `smartart`
- **SmartArt: bar_chart, Vega-Lite, T0 pure_programmatic**

**Slide 19 — The Six AI Personas**
- Headline: "Not One AI — A Crew"
- visual_intent: "Show the persona activity phases as a Gantt chart"
- Body: Map 6 personas to pipeline phases. Deck Conductor (all phases), SmartArt Selector (selection), Prompt Engineer (image gen), Image Reviewer (quality gate), Presentation Reviewer (final review).
- Strategy: `smartart`
- **SmartArt: gantt, Mermaid, T0 pure_programmatic**

**Slide 20 — The Result**
- Headline: "From 3 Sentences to 28 Slides in Minutes"
- Body: Summary stats — 28 slides, nautical brand, 10 SmartArt types, 3 engines, 4 enrichment tiers, 35 QA checks passed. Total cost figure.
- Strategy: `composed`
- SmartArt: none

---

### Act 3: The Edge (Slides 21-28)

**Slide 21 — Section Divider**
- Headline: "Why This Architecture Wins"
- Strategy: `backdrop`
- SmartArt: none
- Visual: Treasure map scene with figurative landmarks, title/subtitle positioned by vision analysis

**Slide 22 — Service Architecture**
- Headline: "33 Services, 6 Personas, 60 Interactions"
- Body: 4 L1 domains (Content, Design, Image, Assembly & QA) orchestrated by Deck Conductor. Each domain owns its decisions. Every service independently invocable.
- Strategy: `composed`
- SmartArt: none (embed existing L1 SVG diagram)

**Slide 23 — Cost Model**
- Headline: "Conference Quality Doesn't Mean Conference Budget"
- visual_intent: "Show costs by category as a bar chart"
- Body: Ollama Drafts: $0, Cloud Drafts: $0.50, Production Images: $1.50, SmartArt: $0, Total: ~$2.00
- Strategy: `smartart`
- **SmartArt: bar_chart, Vega-Lite, T0 pure_programmatic**

**Slide 24 — Quality Gates**
- Headline: "Three Layers of Review, Zero Tolerance for Mediocrity"
- visual_intent: "Show the quality pipeline as a flowchart"
- Body: Image Reviewer (per-image, 5 criteria) → Deck QA (35 automated checks, max 2 cycles) → Presentation Reviewer (narrative coherence, pacing, audience fit). Each gates the next.
- Strategy: `smartart`
- **SmartArt: flowchart, Mermaid, T0 pure_programmatic**

**Slide 25 — Rendering Strategy Spectrum**
- Headline: "Six Ways to Build a Slide"
- visual_intent: "Show the 6 rendering strategies as a timeline from simplest to most complex"
- Body: composed → smartart → background → backdrop → pragmatic_composition → full_render
- Strategy: `smartart`
- **SmartArt: timeline, Custom SVG, T0 pure_programmatic**

**Slide 26 — Development Velocity**
- Headline: "From Research to 603 Tests in 6 Days"
- visual_intent: "Show the project phases as a line chart tracking cumulative tests"
- Body: Phase 1 (38) → Phase 2 (65) → Phase 3 (77) → Phase 4A (175) → Phase 4B (264) → Phase 4C (310) → Phase 5 (377) → Phase 6 (396) → Keynote (504) → Image Reviewer (518) → SmartArt (603)
- Strategy: `smartart`
- **SmartArt: line_chart, Vega-Lite, T1 ai_background**

**Slide 27 — Roadmap**
- Headline: "What's Next"
- visual_intent: "Show the roadmap as a Gantt chart"
- Body: Phase A (Now): SmartArt v1 — 10 types, 3 engines, 4 tiers. Phase B (Next): Complex diagrams — org charts, journey maps, mind maps. Phase C (Future): Brand Kit integration. Phase D (Horizon): Visual regression, D3.js integration.
- Strategy: `smartart`
- **SmartArt: gantt, Mermaid, T1 ai_background**

**Slide 28 — Closing**
- Headline: "Set Sail. Your Deck Awaits."
- Subtitle: "Jack-Tar Deckhand — AI-First Presentation Engineering"
- Strategy: `full_render`
- SmartArt: none
- Visual: Nautical closing — ship at sunset or compass rose

---

## 4. Coverage Matrix

### SmartArt Types (10/10)

| Type | Slides | Engine | Tiers Used |
|------|--------|--------|------------|
| flowchart | 4, 24 | Mermaid | T1, T0 |
| decision_tree | 11 | Mermaid | T1 |
| bar_chart | 18, 23 | Vega-Lite | T0, T0 |
| line_chart | 26 | Vega-Lite | T1 |
| radar_chart | 8 | Vega-Lite | T0 |
| swot | 7 | Custom SVG | T3 |
| feature_matrix | 6, 12 | Custom SVG | T0, T0 |
| venn | 5, 14 | Custom SVG | T2, T0 |
| timeline | 16, 25 | Custom SVG | T1, T0 |
| pipeline_funnel | 15, 17 | Custom SVG | T1, T0 |
| gantt | 19, 27 | Mermaid | T0, T1 |

### Engines (3/3)

| Engine | Slide Count |
|--------|-------------|
| Mermaid | 6 (slides 4, 11, 19, 24, 27) |
| Vega-Lite | 4 (slides 8, 18, 23, 26) |
| Custom SVG | 8 (slides 5, 6, 7, 12, 14, 15, 16, 17, 25) |

### Enrichment Tiers (4/4)

| Tier | Slide Count |
|------|-------------|
| T0 pure_programmatic | 10 |
| T1 ai_background | 7 |
| T2 ai_elements | 1 (slide 5) |
| T3 full_ai_render | 1 (slide 7) |

### Rendering Strategies (6/6)

| Strategy | Slide Count | Slides |
|----------|-------------|--------|
| full_render | 2 | 1, 28 |
| background | 1 | 3 |
| backdrop | 2 | 2, 21 |
| pragmatic_composition | 1 | 9 |
| composed | 4 | 10, 13, 20, 22 |
| smartart | 18 | 4-8, 11-12, 14-19, 23-27 |

---

## 5. TalkBrief

```json
{
  "topic": "Jack-Tar Deckhand: AI-First Presentation Engineering — How an AI Crew Turns Ideas into Conference-Quality Decks",
  "audience": "Technical leaders, conference speakers, and business presenters evaluating AI-powered presentation tools. Mixed technical and non-technical. Reading the deck independently via email, not attending a live presentation.",
  "duration_minutes": 45,
  "tone": "professional",
  "key_takeaways": [
    "Jack-Tar Deckhand is a complete AI-First presentation engineering system with 33 services and 6 AI personas",
    "SmartArt intelligent graphics automatically turn structured data into flowcharts, matrices, charts, and diagrams using 3 rendering engines",
    "The draft-to-production lifecycle keeps costs low ($0-2 per deck) while maintaining conference quality",
    "35 automated QA checks and 3 layers of AI review ensure every deck meets professional standards",
    "The system demonstrates itself — this deck was built by the system it describes"
  ],
  "branding": {
    "company_name": "Jack-Tar Deckhand",
    "primary_color": "#1B3A4B",
    "secondary_color": "#456990",
    "font_preference": "Playfair Display"
  },
  "preferences": {
    "style": "nautical",
    "slide_count_hint": 28,
    "include_speaker_notes": false,
    "include_charts": true
  }
}
```

---

## 6. Implementation Notes

### What This Deck Tests

This deck serves as a comprehensive visual regression test:

1. **All 10 SmartArt types** render without errors
2. **All 4 enrichment tiers** produce valid output (including T3 downgrade)
3. **All 3 rendering engines** execute successfully (Mermaid CLI, Vega-Lite CLI, custom SVG)
4. **All 6 rendering strategies** produce valid slides
5. **Brand profile extraction** applies consistently across all slides
6. **SmartArt QA checks** (SA-01 to SA-05) pass on all SmartArt slides
7. **Assembler** handles `buildSmartArtSlide()` for all enrichment tiers
8. **Comparator** runs on flowchart (Mermaid vs custom_svg) and bar_chart (Vega-Lite vs Matplotlib) during draft

### File Outputs

```
./tmp/deck/
  talk-brief.json
  brand-profile.json
  style-guide.json
  outline.json
  smartart-recommendations.json
  strategy-map.json
  smartart-spec.json
  image-manifest.json
  smartart-manifest.json
  chart-manifest.json
  qa-report.json
  pipeline-state.json
  render-log.json
  images/
  smartart/
  output/
    jack-tar-deckhand-demo.pptx
```
