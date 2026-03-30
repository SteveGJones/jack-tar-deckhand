---
name: slide-stylist
description: Derive a complete StyleGuide through collaborative design exploration with the Speaker, working within brand constraints when a BrandProfile exists.
argument-hint: [--deck-dir PATH]
allowed-tools: Bash(python *), Read, Glob, Write
---

# /slide-stylist

Derive a complete StyleGuide (palette, typography, layout templates, image style tokens) through collaborative exploration with the Speaker.

## Prerequisites

- `./tmp/deck/talk-brief.json` must exist
- `./tmp/deck/brand-profile.json` may exist (produced by brand-manager)

## Usage

Invoked by the Deck Conductor after brand-manager. Can also be invoked directly:

```
/slide-stylist
/slide-stylist --deck-dir ./tmp/deck
```

## What It Does

### Step 1: Read Inputs

Read `./tmp/deck/talk-brief.json` for topic, audience, tone, and preferences.
Read `./tmp/deck/brand-profile.json` if it exists for brand constraints.

Determine the design mode:
- **BrandProfile with strict compliance:** Palette and fonts locked. Only propose accent, image mood, layout preferences.
- **BrandProfile with guided compliance:** Brand provides foundation. Propose variations.
- **No BrandProfile:** Full creative latitude.

### Step 2: Palette Direction

**With strict brand:** Skip -- use BrandProfile palette directly. Tell the Speaker:
> "Using your brand palette (strict compliance). Primary: #{primary}, Secondary: #{secondary}."

**With guided brand:** Propose 2-3 variations:
> "Your brand palette starts with Primary: #{primary}. Here are three accent directions:
> 1. **Split-complementary warm:** Accent #{accent1} -- energetic, draws attention to CTAs
> 2. **Analogous cool:** Accent #{accent2} -- cohesive, professional feel
> 3. **Triadic balanced:** Accent #{accent3} -- vibrant, good for data-heavy decks
>
> Which direction? (Or suggest your own)"

**No brand:** Propose 2-3 complete palettes based on topic + tone:
> "For a **{tone}** talk about **{topic}**, here are three palette directions:
> 1. **{name1}:** Primary #{p1}, Secondary #{s1}, Accent #{a1} -- {description}
> 2. **{name2}:** Primary #{p2}, Secondary #{s2}, Accent #{a2} -- {description}
> 3. **{name3}:** Primary #{p3}, Secondary #{s3}, Accent #{a3} -- {description}
>
> Which direction? (Or describe what you're looking for)"

After Speaker selects, derive the full palette (background, text colours, chart series) ensuring all contrast ratios meet thresholds.

### Step 3: Font Pairing

**With brand font preference:** Use brand font as heading, select best body complement:
> "Using **{brand_font}** for headings (per brand). For body text, I recommend **{body_font}** -- {rationale}. Does that work?"

**Without brand font:** Select from the 10 scored pairings based on tone and topic:

| Tone | Recommended Pairing |
|------|-------------------|
| technical | Inter (single family) -- #4 |
| professional | Montserrat + Open Sans -- #1 |
| conversational | Montserrat + Open Sans -- #1 |
| inspirational | Playfair Display + Source Sans Pro -- #2 |
| provocative | Oswald + Merriweather -- #8 |
| storytelling | Raleway + Lato -- #5 |

Topic keyword overrides:
- AI/ML/data/engineering/developer -> Inter or Work Sans + IBM Plex Sans
- startup/pitch/product -> Poppins + Roboto
- design/creative/art -> Raleway + Lato or Space Grotesk + DM Sans
- research/academic/science -> Fira Sans + Source Serif Pro

Present the recommendation:
> "For a **{tone}** talk about **{topic}**, I recommend:
> - **Heading:** {heading_font}
> - **Body:** {body_font}
> - **Code:** {mono_font}
>
> {brief rationale}. Does this feel right?"

### Step 4: Image Style Tokens

Derive from tone + preferences.style + palette:

> "For the visual style of generated images, I suggest:
> - **Mood:** {mood}
> - **Colour direction:** {color_direction}
> - **Style:** {style_modifiers}
>
> This means images will have a {description}. Does that match your vision?"

Mood mapping:
- professional -> "clean and authoritative"
- conversational -> "friendly and approachable"
- technical -> "precise and structured"
- inspirational -> "bold and aspirational"
- provocative -> "edgy and thought-provoking"
- storytelling -> "warm and narrative"

Style modifier mapping from preferences.style:
- minimalist -> ["clean lines", "ample white space", "simple geometry", "flat colour"]
- image-rich -> ["high detail", "photographic quality", "rich textures", "dramatic lighting"]
- data-heavy -> ["clean infographic style", "structured layouts", "subtle gradients"]
- diagram-heavy -> ["precise lines", "clear labels", "structured flow", "technical illustration"]
- corporate -> ["professional photography", "polished", "brand-consistent", "executive"]
- creative -> ["artistic", "bold composition", "experimental", "vibrant textures"]

### Step 5: Produce StyleGuide

Assemble the final StyleGuide with:
- Agreed palette (all 10 colour values)
- Agreed typography (heading_font, body_font, mono_font, heading_sizes, body_size, caption_size, line_spacing)
- All 12 layout templates (these are fixed engineering constants, not design choices):

| Slide Type | text_zone (x,y,w,h) | image_zone (x,y,w,h) | background_treatment |
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

- Agreed image style tokens (mood, color_direction, style_modifiers[])

Font sizes (fixed defaults from Research #10):
- title_slide: 44, section_divider: 36, slide_heading: 28, subheading: 20
- body_size: 16, caption_size: 12, line_spacing: 1.4

Layout dimensions (fixed):
- slide_width_inches: 10, slide_height_inches: 5.625, margin_inches: 0.5

### Step 6: Validate and Write

Validate the StyleGuide before writing:

```bash
source .venv/bin/activate && python3 -c "
import json
from src.style_validation import validate_style_guide, check_palette_contrast, check_completeness
sg = json.load(open('./tmp/deck/style-guide.json'))
schema_errors = validate_style_guide(sg)
contrast_issues = check_palette_contrast(sg.get('palette', {}))
completeness_issues = check_completeness(sg)
for e in schema_errors: print(f'SCHEMA: {e}')
for e in contrast_issues: print(f'CONTRAST: {e}')
for e in completeness_issues: print(f'COMPLETENESS: {e}')
if not schema_errors and not contrast_issues and not completeness_issues:
    print('StyleGuide validates successfully')
"
```

If validation fails, fix the issues and re-validate. Write the validated StyleGuide to `./tmp/deck/style-guide.json`.

## Output

`./tmp/deck/style-guide.json`

## Design Rules

- All hex values are 6 characters WITHOUT the # prefix (PptxGenJS convention)
- Left-align body text, centre only titles
- Target 7:1+ contrast ratio for all text/background pairs (projection readability)
- Never skip the Speaker collaboration steps -- always propose and get approval
- Layout templates are fixed constants -- do not ask the Speaker about coordinates
- Font sizes are fixed defaults -- do not ask the Speaker about point sizes
