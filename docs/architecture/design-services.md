# Design Services -- L1 Service Document

> Generated from canonical model: `jack-tar-deckhand.json` v1.0.0
> Date: 2026-03-29
> Service ID: `design-services`
> Parent: `presentation-engineering` (L0)

---

## Mission

Derive and enforce visual identity: palettes, typography, layout rules, and brand consistency. Design Services produces the StyleGuide that all downstream services consume for visual coherence, and manages reusable BrandProfile artefacts that persist across deck sessions.

---

## Scope

Design Services is the visual authority for the pipeline. It answers two questions:

1. **What does this brand look like?** (Brand Profile Management)
2. **What should this deck look like?** (Style Derivation + Layout Intelligence)

The domain owns all design decisions within its scope. The Deck Conductor orchestrates when Design Services runs, but does not override its expertise. The Speaker participates in design direction via a collaborative brainstorming workflow.

---

## L2 Sub-Services

| Service ID | Name | Type | Skill | Description |
|---|---|---|---|---|
| `design-brand-profile-management` | Brand Profile Management | Skill | `brand-manager` | Create, store, and serve reusable BrandProfile artefacts from multiple input formats |
| `design-style-derivation` | Style Derivation | Skill | `slide-stylist` | Derive a complete StyleGuide from TalkBrief and BrandProfile through collaborative design exploration |
| `design-layout-intelligence` | Layout Intelligence | Capability | `slide-stylist` (internal) | Apply machine-checkable layout rules: 12-column grid, content zones, safe margins, visual hierarchy |

### L2 Diagram

![Design Services L2](diagrams/jack-tar-deckhand-design-services-l2.svg)

---

## Brand Profile Management (`brand-manager`)

### Purpose

Create, store, and serve reusable BrandProfile artefacts from multiple input formats. BrandProfiles persist beyond a single deck session and are shared across multiple presentations for the same brand.

### Brand Input Sources

The brand-manager accepts any combination of the following inputs and uses Claude's native capabilities (vision, PDF reading, .pptx parsing) to extract structured brand identity:

| Source | TalkBrief Field | Extraction Method |
|---|---|---|
| Existing profile | `branding.brand_id` | Load from `./brands/{id}/brand-profile.json` |
| Brand guidelines PDF | `branding.brand_guidelines_path` | Claude reads PDF natively, extracts mandated colours/fonts/rules |
| Corporate .pptx template | `branding.template_pptx_path` | Claude reads .pptx, extracts slide master colours/fonts |
| Logo image | `branding.logo_path` | Claude vision extracts dominant colours and visual character |
| Manual entry | `branding.primary_color`, `secondary_color`, `font_preference` | Direct use |
| Company name only | `branding.company_name` | Claude infers appropriate defaults from industry/domain |

### Workflow

1. Read TalkBrief branding section
2. If `brand_id` exists and profile found: load, present to Speaker for confirmation ("Is this still current?")
3. If brand assets provided: extract structured data using Claude's native capabilities
4. Present extracted BrandProfile to Speaker for review
5. Speaker approves or corrects
6. Persist to `./brands/{brand-id}/brand-profile.json`
7. Copy reference to `./tmp/deck/brand-profile.json` for the current deck session

### Compliance Modes

The Speaker sets the compliance mode in the TalkBrief or during brand-manager interaction:

- **Strict** -- brand values are non-negotiable. Palette and fonts from the BrandProfile are used exactly. The slide-stylist may only propose accent variations, image mood, and layout preferences.
- **Guided** -- brand values provide a foundation. The slide-stylist may propose palette variations within the brand family, alternative font pairings, and broader visual directions.

### Design Decisions

- **No Python colour libraries.** Claude reads logos (vision), PDFs (native), and reasons about colour theory directly. The skill is a pure SKILL.md.
- **Persistent storage.** Brand profiles live at `./brands/{brand-id}/` outside the per-deck `./tmp/deck/` directory. Created once, reused across decks.
- **Speaker approval gate.** No brand profile enters the pipeline without explicit Speaker confirmation.

---

## Style Derivation (`slide-stylist`)

### Purpose

Derive a complete StyleGuide through collaborative design exploration with the Speaker, working within brand constraints when a BrandProfile exists.

### Collaborative Brainstorming Workflow

The slide-stylist does not generate a StyleGuide silently. It proposes design options and walks the Speaker through choices:

1. Read TalkBrief and BrandProfile (if exists)
2. Determine what is locked vs what needs decisions:
   - **Strict mode:** Palette and fonts locked from BrandProfile. Propose only accent variations, image mood, layout preferences
   - **Guided mode:** BrandProfile provides foundation. Propose palette variations within brand family, font pairing options, visual direction
   - **No brand:** Full creative latitude. Propose 2-3 complete palette/font/mood options based on topic + tone
3. Walk the Speaker through each design area:
   - Palette direction (with contrast validation reasoning)
   - Font pairing (from the 10 scored pairings in Research #10, or brand-mandated)
   - Image style tokens (mood, colour direction, style modifiers)
4. Speaker approves or adjusts each area
5. Produce the final StyleGuide with all 12 layout templates

### Font Pairing Strategy

Font pairings are drawn from 10 pre-scored Google Font combinations documented in Research #10, mapped to tone and topic. Pairings are not invented at runtime -- they are selected from a validated set that accounts for readability at projection distance, contrast between heading and body, and availability on all platforms.

### Design Decisions

- **Collaborative, not generative.** The skill proposes options and walks the Speaker through choices. It does not produce output silently.
- **Brand-aware.** In strict mode, brand values are guardrails. In guided mode, they are starting points.
- **No Python code.** Like brand-manager, this is a SKILL.md -- Claude's design reasoning is the implementation. The output is validated against the existing `style_guide.schema.json`.
- **Font pairing from research.** Pre-scored pairings from Research #10, not invented at runtime.

---

## Layout Intelligence (capability within `slide-stylist`)

### Purpose

Apply machine-checkable layout rules for the 12 slide types. Layout Intelligence is deterministic -- these are engineering constants, not design choices.

### Layout Templates

All layouts target a 10" x 5.625" canvas with 0.5" margins. Zone coordinates are (x, y, width, height) in inches:

| Slide Type | text_zone | image_zone | background_treatment |
|---|---|---|---|
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

These templates are included automatically in every StyleGuide without asking the Speaker.

---

## Data Contracts

### Consumed

| Contract | Source | Description |
|---|---|---|
| TalkBrief | Speaker (via Deck Conductor) | Topic, audience, tone, duration, branding section with brand assets |
| Brand assets | Speaker (files) | Logo image, brand guidelines PDF, corporate .pptx template, manual hex/font values |

### Produced

| Contract | File | Consumers | Description |
|---|---|---|---|
| BrandProfile | `./brands/{brand-id}/brand-profile.json` | slide-stylist, Image Generation Expert, Deck Conductor | Reusable brand identity: palette, typography, image style constraints, compliance mode |
| StyleGuide | `./tmp/deck/style-guide.json` | imagegen-bridge, chart-renderer, deck-assembler, Image Generation Expert, Presentation Reviewer | Complete visual design system: palette, typography, 12 layout templates, image style tokens |

---

## Key Interactions

### Inbound

| Source | Type | Data |
|---|---|---|
| Deck Conductor | invocation | TalkBrief, brand assets (optional) |
| Speaker | review/approval | BrandProfile confirmation, design direction choices |

### Outbound

| Target | Type | Data |
|---|---|---|
| Style Derivation (internal) | data-provision | BrandProfile flows from brand-manager to slide-stylist |
| Image Generation Expert | data-provision | BrandProfile (approved_image_styles, prohibited_image_styles) |
| Deck Conductor | consultation | Design options, BrandProfile summary, compliance mode for Speaker presentation |

### Internal Flow

```
Deck Conductor
  |
  | TalkBrief + brand assets
  v
brand-manager
  |
  | BrandProfile
  v
Speaker reviews/approves
  |
  v
slide-stylist
  |
  | Proposes design directions (palette, fonts, mood)
  v
Speaker selects per area
  |
  v
StyleGuide written to ./tmp/deck/style-guide.json
```

---

## Implementation Status

| Component | Skill | Source | Tests | Status |
|---|---|---|---|---|
| Brand Profile Management | `brand-manager` | `.claude/skills/brand-manager/SKILL.md` | -- | Planned (Phase 2) |
| Style Derivation | `slide-stylist` | `.claude/skills/slide-stylist/SKILL.md` | -- | Planned (Phase 2) |
| Layout Intelligence | (within slide-stylist) | -- | -- | Planned (Phase 2) |
| BrandProfile schema | -- | `src/schemas/brand_profile.schema.json` | -- | Planned (Phase 2) |

Both skills are SKILL.md files -- their logic is Claude's reasoning. Testing validates outputs, not code:
- Schema validation against `style_guide.schema.json` and `brand_profile.schema.json`
- Contrast validation (WCAG AA 4.5:1, projection 7:1 thresholds)
- Completeness (all required fields present, all 12 layout templates included)
- Fixture-based smoke tests against known TalkBrief inputs
- Brand compliance (strict mode preserves brand-mandated values unchanged)

---

## Related Documentation

| Document | Path |
|---|---|
| Architecture Overview | [architecture-overview.md](architecture-overview.md) |
| Service Catalogue | [service-catalogue.md](service-catalogue.md) |
| Data Contracts | [data-contracts.md](data-contracts.md) |
| Design Services L2 Diagram | [diagrams/jack-tar-deckhand-design-services-l2.svg](diagrams/jack-tar-deckhand-design-services-l2.svg) |
| Research #10 (Typography) | [../../research/10-typography-font-management.md](../../research/10-typography-font-management.md) |
| Research #01 (Slide Design) | [../../research/01-slide-design-principles.md](../../research/01-slide-design-principles.md) |
