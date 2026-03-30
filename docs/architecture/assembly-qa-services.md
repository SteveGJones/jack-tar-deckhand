# Assembly & QA Services -- L1 Service Document

> Generated from canonical model: `jack-tar-deckhand.json` v1.0.0
> Date: 2026-03-29
> Service ID: `assembly-qa-services`
> Parent: `presentation-engineering` (L0)

---

## Mission

Compose content and visual assets into finished, validated presentation files. Assembly & QA Services is the final stage of the pipeline, responsible for building the .pptx file, running automated quality checks, optimising file size, and providing human-judgement-level craft review via the Presentation Reviewer AI Persona.

---

## Scope

Assembly & QA Services answers three questions:

1. **Is the deck built correctly?** (PPTX Build + File Optimisation)
2. **Does it pass automated quality checks?** (Visual QA)
3. **Is it a good conference presentation?** (Presentation Reviewer)

The first two are mechanical. The third is judgement. This separation is a deliberate architectural choice -- automated QA and human-judgement review have different purposes, different feedback paths, and different correction mechanisms.

---

## L2 Sub-Services

| Service ID | Name | Type | Skill | Description |
|---|---|---|---|---|
| `assembly-pptx-build` | PPTX Build | Skill | `deck-assembler` | Compose all artefacts into a .pptx file via PptxGenJS |
| `assembly-file-optimisation` | File Optimisation | Capability | `deck-assembler` (internal) | Image compression, font subsetting, metadata stripping |
| `assembly-visual-qa` | Visual QA | Skill | `deck-qa` | 25 automated anti-pattern checks |
| `assembly-presentation-reviewer` | Presentation Reviewer | AI Persona | -- (agent/advisory) | Conference best practices review |

### L2 Diagram

![Assembly & QA Services L2](diagrams/jack-tar-deckhand-assembly-qa-services-l2.svg)

---

## PPTX Build (`deck-assembler`)

### Purpose

Compose the SlideOutline, StyleGuide, ImageManifest, ChartManifest, and SpeakerNotes into a finished .pptx file using PptxGenJS as the rendering engine.

### Key Responsibilities

- Create slides in outline order, applying the correct layout template from the StyleGuide
- Place text in text zones, images in image zones, charts in chart zones
- Apply typography (fonts, sizes, weights) from the StyleGuide
- Apply colour palette from the StyleGuide (backgrounds, text colours, accent colours)
- Embed speaker notes per slide
- Apply background treatments (solid_light, solid_dark, gradient, image_bleed)
- Write output to `./tmp/deck/output/presentation.pptx`

### System Actor

| Actor | Library | Runtime |
|---|---|---|
| PptxGenJS | v4.0.1, MIT license | Node.js (available in Claude Code) |

### File Optimisation (embedded capability)

After initial assembly, the deck-assembler applies optimisations:

- Image compression (reduce embedded image file sizes)
- Font subsetting (include only used glyphs)
- Metadata stripping (remove authoring metadata)
- File size management (target reasonable .pptx file size for email/sharing)

These optimisations are internal to the assembler and not independently invocable.

---

## Visual QA (`deck-qa`)

### Purpose

Run 25 automated, machine-checkable anti-pattern checks against the assembled .pptx file. Visual QA catches problems that are objectively wrong -- not matters of taste.

### Check Categories

| Category | Examples |
|---|---|
| `overlap` | Text boxes overlapping image zones |
| `contrast` | Text-on-background below WCAG AA (4.5:1) or projection (7:1) thresholds |
| `margin` | Content outside safe margins (0.5" from edges) |
| `text_overflow` | Text exceeding its allocated zone |
| `consistency` | Font or colour inconsistencies across slides |
| `image_quality` | Image resolution below threshold for slide dimensions |
| `placeholder_residue` | Unreplaced placeholder text or missing images |
| `missing_content` | Slides missing required elements (e.g., content slide with no body points) |
| `accessibility` | Missing alt text, insufficient colour differentiation |

### Verdicts

| Verdict | Meaning | Action |
|---|---|---|
| `pass` | No errors, zero or few info-level findings | Proceed to Presentation Reviewer |
| `pass_with_warnings` | No errors, some warnings | Proceed but include warnings in delivery |
| `fail` | One or more errors | Trigger correction cycle (max 2) |

### Correction Cycle

The Visual QA feeds findings back to the Deck Conductor. The Conductor re-invokes the producing service with corrective instructions. Maximum 2 correction cycles -- after 2 failures, the Conductor escalates to the Speaker rather than looping indefinitely.

---

## Presentation Reviewer (AI Persona -- Advisory)

**Persona ID:** `persona-presentation-reviewer`
**Authority Model:** Invoker (acts on behalf of the Deck Conductor, escalates to Deck Conductor)
**Confidence Threshold:** 0.7 minimum for autonomous assessment

### Role

Advisory persona that reviews assembled decks against conference presentation best practices. This is the human-judgement layer -- it catches problems that automated QA cannot detect.

### Review Dimensions

| Dimension | What It Assesses |
|---|---|
| Narrative coherence | Does the story flow logically? Does each slide build on the previous? |
| Visual storytelling | Do slide transitions create visual rhythm? Do image choices support the narrative? |
| Pacing | Is slide density appropriate for the duration? Is there breathing room? Are there interaction beats? |
| Speaker notes quality | Are notes specific and actionable, or generic filler? |
| Audience appropriateness | Does content match the stated audience and tone? |

### Output

A structured review with per-slide feedback and overall assessment. Each recommendation is tagged with a priority level:

| Priority | Meaning |
|---|---|
| `critical` | Fundamental problem that undermines the presentation's effectiveness |
| `suggested` | Meaningful improvement that would strengthen the deck |
| `polish` | Minor refinement for an already-good presentation |

### Boundaries

- Never modifies the deck, outline, images, or notes directly
- Never re-invokes any service -- only the Conductor acts on review feedback
- Never overrides the Speaker's creative choices -- flags concerns but respects stated preferences
- Never duplicates deck-qa's programmatic checks -- assumes automated QA has already passed
- Feedback goes to the Conductor, which presents it to the Speaker for decision

For the full persona specification, see [AI Persona Summaries](ai-persona-summaries.md).

---

## Data Contracts

### Consumed

| Contract | Source | Description |
|---|---|---|
| SlideOutline | Content Services (narrative-architect) | Structured slide plan with types, headlines, body points, layout templates |
| StyleGuide | Design Services (slide-stylist) | Palette, typography, 12 layout templates with zone coordinates |
| ImageManifest | Image Services (imagegen-bridge) | Generated image files with metadata, file paths, placement zones |
| ChartManifest | Image Services (chart-renderer) | Generated chart images with metadata |
| SpeakerNotes | Content Services (speaker-notes-writer) | Per-slide timed notes with interaction cues |
| TalkBrief | Speaker (via Deck Conductor) | Original brief for Presentation Reviewer alignment checking |

### Produced

| Contract | File | Consumers | Description |
|---|---|---|---|
| .pptx file | `./tmp/deck/output/presentation.pptx` | Speaker, Presentation Reviewer | Assembled, optimised presentation file |
| QAReport | `./tmp/deck/qa-report.json` | Deck Conductor, Presentation Reviewer | Pass/fail verdict with detailed findings |
| Presentation Review | (conversation context) | Deck Conductor, Speaker | Structured per-slide feedback with priority levels |

---

## Key Interactions

### Inbound

| Source | Type | Data |
|---|---|---|
| Deck Conductor | invocation | SlideOutline, StyleGuide, ImageManifest, ChartManifest, SpeakerNotes |
| Deck Conductor | invocation | Review request (post-QA, to Presentation Reviewer) |

### Outbound

| Target | Type | Data |
|---|---|---|
| Deck Conductor | feedback | QA findings for correction cycle (from Visual QA) |
| Deck Conductor | feedback | Structured review with prioritised recommendations (from Presentation Reviewer) |

### Internal Flow

```
Deck Conductor
  |
  | All artefacts (outline, style, images, charts, notes)
  v
deck-assembler
  |
  | .pptx file
  v
deck-qa (Visual QA)
  |
  +-- fail --> Deck Conductor (correction cycle, max 2)
  |
  +-- pass/pass_with_warnings
      |
      v
Presentation Reviewer
  |
  | Structured review
  v
Deck Conductor --> Speaker
```

### System Actor Dependencies

| System Actor | Type | Service | Description |
|---|---|---|---|
| PptxGenJS | JavaScript library (npm) | PPTX Build | .pptx file generation engine |
| Filesystem | Local storage | PPTX Build | Output directory for .pptx files |

---

## Implementation Status

| Component | Skill | Source | Tests | Status |
|---|---|---|---|---|
| PPTX Build | `deck-assembler` | `.claude/skills/deck-assembler/SKILL.md` | -- | Planned (Phase 5) |
| File Optimisation | (within deck-assembler) | -- | -- | Planned (Phase 5) |
| Visual QA | `deck-qa` | `.claude/skills/deck-qa/SKILL.md` | -- | Planned (Phase 5) |
| Presentation Reviewer | -- | -- | -- | Planned (Phase 6) |
| QAReport schema | -- | `src/schemas/qa_report.schema.json` | 27 (shared) | Done (Phase 1) |

The JSON schema for QAReport was defined in Phase 1. The skills themselves are planned for Phase 5 (Assembly & QA), which is the next implementation phase. The Presentation Reviewer AI Persona is planned for Phase 6 alongside the Deck Conductor.

---

## Related Documentation

| Document | Path |
|---|---|
| Architecture Overview | [architecture-overview.md](architecture-overview.md) |
| Service Catalogue | [service-catalogue.md](service-catalogue.md) |
| AI Persona Summaries | [ai-persona-summaries.md](ai-persona-summaries.md) |
| Data Contracts | [data-contracts.md](data-contracts.md) |
| Assembly & QA Services L2 Diagram | [diagrams/jack-tar-deckhand-assembly-qa-services-l2.svg](diagrams/jack-tar-deckhand-assembly-qa-services-l2.svg) |
| Research #07 (PPTX Generation) | [../../research/07-pptx-generation-engines.md](../../research/07-pptx-generation-engines.md) |
| Research #09 (Quality Assurance) | [../../research/09-presentation-quality-assurance.md](../../research/09-presentation-quality-assurance.md) |
