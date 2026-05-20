# schematic-diagram

Default strap_style: prose-sentence

## Palette

| Role | Hex | Usage |
|---|---|---|
| Surface | `#FFFFFF` | Pure white slide background — drafting-paper feel |
| Structural / Primary fill | `#1F2A37` | Slate blue-black for SmartArt shape fills, system blocks, dark UI chrome |
| Text on Brand colour | `#FFFFFF` | White text on slate shape fills |
| Body text | `#1F2A37` | Slate blue-black on white for paragraphs |
| Accent | `#2563EB` | Engineering blue — schematic highlights, primary arrows, in-scope markers |
| Subdued slate | `#94A3B8` | Light slate-grey for deferred / out-of-scope / "won't build" content |
| Subtle divider | `#E2E8F0` | Very-light slate for grid lines and section borders |
| Marker placeholder fill | `#F1F5F9` | Pale slate for IMAGE / BG placeholder rectangles |
| Marker placeholder border | `#94A3B8` | Mid-slate dashed border on placeholder rects |

## Typography

Display: humanist sans with strong x-height (Inter, IBM Plex Sans, Source Sans) at 28–34 pt for titles. Body: same family at 13–16 pt. Monospace (JetBrains Mono, IBM Plex Mono) reserved for code, schema field names, and labelled diagram annotations — never body prose. Straps are prose-sentence cadence, sentence-case, factual. Numbers in tables and charts use tabular figures.

## Layout typology

Defaults to full content-zone SMARTART (not SMARTART-FROM-LIST) when the slide IS the diagram — process pipelines, decision trees, organisation charts, layered architecture stacks. Sub-page SmartArt is the side-accent scale for "evidence cluster" slides where prose explains while the diagram enumerates. IMAGE markers are reserved for schematic illustrations the SmartArt library can't express (custom topology maps, free-form system diagrams, conviction-vs-drag style metaphors). Native CHART:slug for every quantitative series — bar / column / line / scatter. No photographic imagery; no BG markers.

## When to reach for this register

Engineering team updates, architecture reviews, incident retrospectives, RFC walkthroughs, technical decision documents, and any deck whose audience reasons through structure. Run 4 — Redline incident report deck — is the canonical engineering-leadership reference. Pair with Problem-Solution or Investigation-Verdict arcs; avoid this register for board / brand / fundraising audiences who expect warmth over precision.
