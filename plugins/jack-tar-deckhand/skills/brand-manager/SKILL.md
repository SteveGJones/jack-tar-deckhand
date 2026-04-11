---
name: brand-manager
description: Create, load, or update a reusable BrandProfile from brand assets (PDF guidelines, .pptx template, logo, manual input). Persists profiles for cross-deck reuse.
argument-hint: [--deck-dir PATH] [--brands-dir PATH]
allowed-tools: Bash(python *), Read, Glob, Write
---

# /brand-manager

Create or load a reusable BrandProfile from brand assets. Profiles persist at `./brands/{brand-id}/` for reuse across multiple deck sessions.

## Prerequisites

- `./tmp/deck/talk-brief.json` must exist (produced by the Speaker via Deck Conductor)

## Usage

Invoked by the Deck Conductor before slide-stylist. Can also be invoked directly:

```
/brand-manager
/brand-manager --brands-dir ./brands
```

## What It Does

### Step 1: Read TalkBrief Branding Section

Read `./tmp/deck/talk-brief.json` and examine the `branding` object. Determine which inputs are available:

| Field | What It Means |
|-------|---------------|
| `brand_id` | Load an existing profile from `./brands/{brand_id}/brand-profile.json` |
| `brand_guidelines_path` | Read the PDF and extract mandated colours, fonts, spacing rules, logo usage |
| `template_pptx_path` | Read the .pptx and extract slide master colours, fonts, layouts |
| `logo_path` | View the logo image and extract dominant colours and visual character |
| `primary_color` + `secondary_color` | Use as direct palette seeds |
| `font_preference` | Use as heading_font, select complementary body_font |
| `company_name` (only) | Infer appropriate defaults from industry/domain context |
| `compliance_mode` | `strict` or `guided` (default: `guided`) |

### Step 2: Load or Extract

**If `brand_id` is present and profile exists:**

```bash
source .venv/bin/activate && python3 -c "
from src.brand_profile import load_brand_profile
import json
profile = load_brand_profile('BRAND_ID')
if profile:
    print(json.dumps(profile, indent=2))
else:
    print('NOT FOUND')
"
```

If found, present the profile to the Speaker:
> "I found an existing brand profile for **{company_name}**. Here's what it contains:
> - Primary: #{primary}, Secondary: #{secondary}, Accent: #{accent}
> - Fonts: {heading_font} / {body_font}
> - Compliance: {compliance_mode}
> - Last extracted: {extracted_at}
>
> **Is this still current, or should I re-extract from updated assets?**"

If the Speaker confirms, copy to `./tmp/deck/brand-profile.json` and exit.

**If brand assets are provided, extract a new profile:**

1. **PDF guidelines:** Read the file using the Read tool. Look for:
   - Mandated hex colours (primary, secondary, accent)
   - Approved font families
   - Logo usage rules
   - Colour usage rules (what's prohibited)
   - Image style guidance

2. **Corporate .pptx template:** Read the file. Look for:
   - Slide master background colours
   - Title and body font families and sizes
   - Accent colours used in shapes/lines

3. **Logo image:** View the image using the Read tool. Identify:
   - 2-3 dominant colours and approximate hex values
   - Visual character: geometric vs organic, modern vs classic, bold vs subtle

4. **Manual colours/fonts:** Use directly as palette seeds.

5. **Company name only:** Infer from topic and company context:
   - Tech company -> blues, greys, Inter/Work Sans
   - Finance -> navy, gold, Montserrat/Open Sans
   - Creative -> vibrant, Raleway/Lato
   - Default -> professional blue palette (primary: 1A365D)

### Step 3: Derive Full Palette

From the extracted seed colours, derive a complete palette following the 60-30-10 rule:

- **primary** -- main brand colour (from extraction)
- **secondary** -- supporting brand colour (from extraction, or analogous to primary)
- **accent** -- split-complementary hue rotation (+150 degrees from primary)
- **background** -- near-white tinted with primary hue (lightness ~0.97)
- **background_alt** -- near-black tinted with primary hue (lightness ~0.12)
- **text_primary** -- dark neutral ensuring 7:1+ contrast on background
- **text_muted** -- medium grey ensuring 4.5:1+ contrast on background
- **text_on_dark** -- near-white ensuring 7:1+ contrast on background_alt
- **chart_series** -- 5 perceptually distinct colours anchored to brand palette

**Validate contrast:** All text/background pairings must meet WCAG AA (4.5:1) minimum. Target 7:1 for projection readability.

### Step 4: Present to Speaker for Approval

> "Here's the brand profile I've extracted for **{company_name}**:
>
> **Palette:**
> - Primary: #{primary} | Secondary: #{secondary} | Accent: #{accent}
> - Background: #{background} | Alt: #{background_alt}
> - Text: #{text_primary} on light, #{text_on_dark} on dark
>
> **Typography:** {heading_font} / {body_font}
>
> **Image styles approved:** {approved_image_styles}
> **Image styles prohibited:** {prohibited_image_styles}
>
> **Compliance mode:** {compliance_mode}
>
> **Does this look right? Any adjustments?**"

Apply any Speaker corrections.

### Step 5: Persist

```bash
source .venv/bin/activate && python3 -c "
import json
from src.brand_profile import save_brand_profile, validate_brand_profile

profile = json.load(open('./tmp/deck/brand-profile.json'))
errors = validate_brand_profile(profile)
if errors:
    print('Validation errors:', errors)
else:
    path = save_brand_profile(profile)
    print(f'Brand profile saved to {path}')
"
```

Save the profile to both:
- `./brands/{brand-id}/brand-profile.json` (persistent)
- `./tmp/deck/brand-profile.json` (current deck session)

## Output

`./brands/{brand-id}/brand-profile.json` and `./tmp/deck/brand-profile.json`

## Design Rules

- All hex values are 6 characters WITHOUT the # prefix
- Compliance mode defaults to `guided` if not specified
- Never skip the Speaker approval step -- even for cached profiles
- If no brand assets are provided at all, still produce a minimal BrandProfile with inferred defaults
