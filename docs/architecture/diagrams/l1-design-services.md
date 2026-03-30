# L1 Design Services -- Drill-Down

> **Source**: `jack-tar-deckhand.json` | **Level**: L1 > L2 | **Parent**: Presentation Engineering | **Date**: 2026-03-29

![Design Services L2](jack-tar-deckhand-design-services-l2.svg)

## L2 Capabilities

| Capability | Type | Skill | Description |
|------------|------|-------|-------------|
| Brand Profile Management | Skill | `brand-manager` | Create, store, and serve reusable BrandProfile artefacts |
| Style Derivation | Skill | `slide-stylist` | Derive complete StyleGuide from brief + brand via collaborative design exploration |
| Layout Intelligence | Capability | within `slide-stylist` | 12-col grid, content zones, safe margins |

## Data Contract Summary

| Contract | Direction | Format | Description |
|----------|-----------|--------|-------------|
| **TalkBrief** | In | JSON | Topic, audience, tone, branding section with brand assets |
| **Brand Assets** | In (optional) | Files | Logo, brand guidelines PDF, corporate .pptx template, hex/font values |
| **BrandProfile** | Out (reusable) | JSON | Brand identity: palette, typography, image style constraints, compliance mode |
| **StyleGuide** | Out | JSON | Palette, typography, spacing, 12 layout templates, image style tokens, contrast pairs |

## Full Documentation

See [Design Services L1 Document](../design-services.md) for complete service specification including the collaborative brainstorming workflow, brand input sources, compliance modes, layout templates, and font pairing strategy.
