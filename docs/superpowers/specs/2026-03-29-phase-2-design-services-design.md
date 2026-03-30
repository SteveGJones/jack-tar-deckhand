# Phase 2 Design Spec: Design Services — brand-manager + slide-stylist

> **Date:** 2026-03-29
> **Status:** Approved
> **Supersedes:** The original Phase 2 plan at `docs/superpowers/plans/2026-03-29-phase-2-design-services.md` was written before the BSA restructure. This spec reflects the updated architecture.

---

## What Changed

The original plan had slide-stylist as a single skill doing brand extraction, style derivation, and layout intelligence. BSA service discovery (2026-03-29) identified that Brand Extraction should be elevated to its own L2 service because:

1. Brand profiles are **reusable** across multiple decks for the same company
2. Brand extraction from heterogeneous inputs (PDF, .pptx, logo, manual) is a distinct responsibility
3. The slide-stylist should **collaborate** with the Speaker on design direction, not make unilateral choices
4. Strict vs guided compliance modes require brand constraints to be a first-class artifact

The canonical model, all architecture docs, and the Design Services L2 diagram have been updated to reflect this.

---

## Deliverables

### 1. brand-manager skill

**Service ID:** `design-brand-profile-management`
**Skill:** `.claude/skills/brand-manager/SKILL.md`
**Contract produced:** BrandProfile at `./brands/{brand-id}/brand-profile.json`

#### Purpose

Create, store, and serve reusable BrandProfile artifacts from multiple input formats. BrandProfiles persist beyond a single deck session.

#### Input Sources (any combination)

| Source | TalkBrief Field | How Claude Extracts |
|--------|-----------------|---------------------|
| Existing profile | `branding.brand_id` | Load from `./brands/{id}/brand-profile.json` |
| Brand guidelines PDF | `branding.brand_guidelines_path` | Claude reads PDF natively, extracts mandated colours/fonts/rules |
| Corporate .pptx template | `branding.template_pptx_path` | Claude reads .pptx, extracts slide master colours/fonts |
| Logo image | `branding.logo_path` | Claude vision extracts dominant colours and visual character |
| Manual entry | `branding.primary_color`, `secondary_color`, `font_preference` | Direct use |
| Company name only | `branding.company_name` | Claude infers appropriate defaults from industry/domain |

#### Workflow

1. Read TalkBrief branding section
2. If `brand_id` exists and profile found → load, present to Speaker for confirmation ("Is this still current?")
3. If brand assets provided → extract structured data using Claude's native capabilities
4. Present extracted BrandProfile to Speaker for review
5. Speaker approves or corrects
6. Persist to `./brands/{brand-id}/brand-profile.json`
7. Copy reference to `./tmp/deck/brand-profile.json` for the current deck session

#### Key Design Decisions

- **No Python colour libraries.** Claude reads logos (vision), PDFs (native), and reasons about colour theory directly. The skill is pure SKILL.md instructions.
- **Persistent storage.** Brand profiles live at `./brands/{brand-id}/` outside the per-deck `./tmp/deck/` directory. Created once, reused across decks.
- **Speaker approval gate.** No brand profile enters the pipeline without explicit Speaker confirmation. This is the management mechanism.
- **Compliance mode.** Set by the Speaker in TalkBrief or during brand-manager interaction. `strict` = brand values non-negotiable. `guided` = brand as foundation, extensions proposed.

---

### 2. slide-stylist skill (redesigned)

**Service ID:** `design-style-derivation`
**Skill:** `.claude/skills/slide-stylist/SKILL.md`
**Contract produced:** StyleGuide at `./tmp/deck/style-guide.json`

#### Purpose

Derive a complete StyleGuide through collaborative design exploration with the Speaker, working within brand constraints when a BrandProfile exists.

#### Inputs

- TalkBrief (`./tmp/deck/talk-brief.json`) — topic, audience, tone, preferences
- BrandProfile (`./tmp/deck/brand-profile.json`) — brand constraints (optional, produced by brand-manager)

#### Workflow (brainstorming pattern)

1. Read TalkBrief and BrandProfile (if exists)
2. Determine what's locked vs what needs decisions:
   - **Strict mode:** Palette and fonts locked from BrandProfile. Propose only: accent variations, image mood, layout preferences
   - **Guided mode:** BrandProfile provides foundation. Propose: palette variations within brand family, font pairing options, visual direction
   - **No brand:** Full creative latitude. Propose: 2-3 complete palette/font/mood options based on topic + tone
3. Walk the Speaker through each design area:
   - Palette direction (with contrast validation reasoning)
   - Font pairing (from the 10 scored pairings in Research #10, or brand-mandated)
   - Image style tokens (mood, colour direction, style modifiers)
4. Speaker approves or adjusts each area
5. Produce the final StyleGuide with all 12 layout templates

#### Layout Intelligence (embedded capability)

The 12 layout templates are deterministic — fixed zone coordinates per slide type on a 10" x 5.625" canvas with 0.5" margins. These are not design choices; they're engineering constants derived from Research #01. The skill includes them automatically without asking the Speaker.

| Slide Type | text_zone | image_zone | background_treatment |
|------------|-----------|------------|---------------------|
| title | (1.0, 1.5, 8.0, 2.5) | (0, 0, 10.0, 5.625) | image_bleed |
| section_divider | (1.0, 1.5, 8.0, 2.5) | null | solid_dark |
| content | (0.5, 1.0, 5.5, 4.0) | (6.5, 0.5, 3.0, 4.625) | solid_light |
| two_column | (0.5, 1.0, 4.0, 4.0) | (5.5, 1.0, 4.0, 4.0) | solid_light |
| image_feature | (0.5, 3.5, 4.0, 1.5) | (0, 0, 10.0, 3.2) | image_bleed |
| data_chart | (0.5, 0.5, 9.0, 1.0) | (0.5, 1.6, 9.0, 3.5) | solid_light |
| stat_callout | (1.5, 1.0, 7.0, 3.5) | null | solid_dark |
| quote | (1.5, 1.0, 7.0, 3.0) | null | solid_dark |
| icon_grid | (0.5, 0.5, 9.0, 1.0) | (0.5, 1.6, 9.0, 3.5) | solid_light |
| diagram | (0.5, 0.5, 9.0, 1.0) | (0.5, 1.8, 9.0, 3.3) | solid_light |
| closing | (1.0, 1.0, 8.0, 3.5) | null | gradient |
| blank_visual | null | (0, 0, 10.0, 5.625) | image_bleed |

#### Key Design Decisions

- **Collaborative, not generative.** The skill proposes options and walks the Speaker through choices, following the brainstorming pattern. It does not generate a StyleGuide silently.
- **Brand-aware.** In strict mode, brand values are guardrails. In guided mode, they're starting points.
- **No Python code.** Like brand-manager, this is a SKILL.md — Claude's design reasoning IS the implementation. The output is validated against the existing `style_guide.schema.json`.
- **Font pairing from research.** 10 scored Google Font pairings from Research #10, mapped to tone/topic. Not invented at runtime.

---

## Data Flow

```
Speaker provides TalkBrief
    |
    v
brand-manager reads branding section
    |
    +-- brand_id exists? --> load ./brands/{id}/brand-profile.json
    +-- brand assets? --> extract with Claude vision/PDF/pptx reading
    +-- neither? --> skip, no BrandProfile
    |
    v
Speaker reviews/approves BrandProfile
    |
    v
slide-stylist reads TalkBrief + BrandProfile
    |
    +-- proposes design directions (palette, fonts, mood)
    +-- Speaker selects per area
    |
    v
StyleGuide written to ./tmp/deck/style-guide.json
    |
    v
Downstream consumers (assembler, chart-renderer, imagegen-bridge)
```

---

## Testing Strategy

Both skills are SKILL.md files — their "logic" is Claude's reasoning. Testing validates **outputs**, not code:

1. **Schema validation** — StyleGuide and BrandProfile outputs validate against their JSON schemas
2. **Contrast validation** — palette pairings meet WCAG AA (4.5:1) and projection (7:1) thresholds
3. **Completeness** — all required fields present, all 12 layout templates included
4. **Fixture-based smoke tests** — run both skills against known TalkBrief inputs and verify outputs
5. **Brand compliance** — in strict mode, verify brand-mandated values appear unchanged in StyleGuide

Python validation code in `src/` can provide reusable contrast-checking utilities that tests and the QA pipeline both use.

---

## What This Spec Does NOT Cover

- **Phase 3 (Content Services)** — narrative-architect and speaker-notes-writer are separate
- **Phase 6 (Deck Conductor)** — the orchestration of brand-manager → slide-stylist → downstream is the Conductor's responsibility
- **BrandProfile CRUD UI** — managing brand profiles (list, delete, update) is out of scope for Phase 2. The brand-manager creates and loads; management is future work.
