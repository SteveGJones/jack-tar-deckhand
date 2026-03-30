# Synthesis: slide-stylist

> Distilled from: research/09-brand-extraction-style-transfer.md, research/10-font-strategy-typography.md, research/01-slide-layout-intelligence.md, docs/architecture/design-services.md, src/schemas/style_guide.schema.json

## 1. Collaborative Brainstorming Workflow

The slide-stylist does NOT generate a StyleGuide silently. It proposes design options and walks the Speaker through choices, one design area at a time.

### 1.1 Input Analysis

1. Read TalkBrief (topic, audience, tone, duration)
2. Read BrandProfile (if exists) -- loaded from `./tmp/deck/brand-profile.json`
3. Determine what is locked vs what needs decisions based on compliance mode

### 1.2 Design Areas (presented in order)

| # | Design Area | Strict Mode | Guided Mode | No Brand |
|---|-------------|-------------|-------------|----------|
| 1 | Palette direction | Locked -- show palette, confirm | Propose 2-3 variations within brand family | Propose 2-3 complete palettes based on topic + tone |
| 2 | Font pairing | Locked -- use brand fonts | Propose 2-3 pairings from the 10 scored set | Propose 2-3 pairings from the 10 scored set |
| 3 | Image style tokens | Mood within approved styles | Broader mood/style exploration | Full creative latitude |

### 1.3 Per-Area Proposal Format

For each design area, the slide-stylist:
1. Explains the rationale ("For a tech conference keynote, modern geometric fonts signal innovation...")
2. Presents 2-3 concrete options with reasoning for each
3. Includes contrast validation reasoning ("Option A: primary #002D72 on background #F8F9FA gives 15.2:1 contrast -- exceeds projection-safe 7:1")
4. Waits for Speaker selection before proceeding to the next area

### 1.4 Final Output

After all areas are resolved, produce the StyleGuide to `./tmp/deck/style-guide.json` conforming to `src/schemas/style_guide.schema.json`. This includes the 12 layout templates (added automatically, not discussed with the Speaker).

---

## 2. Font Pairing Selection

### 2.1 The 10 Scored Pairings (Research #10 Area 1)

Pairings are pre-scored and validated for projection readability. They are SELECTED from this set, never invented at runtime.

| # | Heading | Body | Visual Character | Best For |
|---|---------|------|-----------------|----------|
| 1 | Montserrat | Open Sans | Modern geometric | General conference, tech, business |
| 2 | Playfair Display | Source Sans Pro | Classic editorial | Luxury, literary, keynotes |
| 3 | Poppins | Roboto | Friendly geometric | Consumer tech, education, startups |
| 4 | Inter | Inter | Swiss precision | Tech, SaaS, data-heavy, developer conferences |
| 5 | Raleway | Lato | Elegant modern | Creative agencies, design events |
| 6 | Nunito | Nunito Sans | Warm rounded | Education, healthcare, community |
| 7 | Work Sans | IBM Plex Sans | Corporate technical | Enterprise tech, developer events |
| 8 | Oswald | Merriweather | Bold condensed + serif | Impact keynotes, news/media |
| 9 | Space Grotesk | DM Sans | Tech-forward | Tech startups, AI/ML, futuristic |
| 10 | Fira Sans | Source Serif Pro | Technical editorial | Academic, research conferences |

### 2.2 Tone-to-Pairing Mapping

| Talk Tone/Type | Primary Recommendation | Secondary Option |
|----------------|----------------------|------------------|
| Tech conference / Developer | **#4 Inter** | #7 Work Sans + IBM Plex Sans |
| Business / Corporate | **#1 Montserrat + Open Sans** | #3 Poppins + Roboto |
| Creative / Design | **#5 Raleway + Lato** | #9 Space Grotesk + DM Sans |
| Academic / Research | **#10 Fira Sans + Source Serif Pro** | #4 Inter |
| Luxury / Editorial keynote | **#2 Playfair Display + Source Sans Pro** | #8 Oswald + Merriweather |
| Education / Community | **#6 Nunito + Nunito Sans** | #3 Poppins + Roboto |
| Data-heavy / Dashboard | **#4 Inter** | #7 Work Sans + IBM Plex Sans |
| Bold / Impact keynote | **#8 Oswald + Merriweather** | #1 Montserrat + Open Sans |
| Startup pitch | **#3 Poppins + Roboto** | #9 Space Grotesk + DM Sans |
| Default / Unknown | **#4 Inter** | **#1 Montserrat + Open Sans** |

### 2.3 Projection Safety Warnings

These pairings require weight discipline on projection:

- **#2 Playfair Display:** High stroke contrast. Use ONLY for headings at 36pt+ Bold. Thin hairlines disappear on projection.
- **#5 Raleway:** Light weights are graceful but illegible on projection. Use SemiBold (600) minimum for headings.
- **#8 Oswald:** Condensed width -- use ONLY for short headings, never body text. Condensed fonts dramatically reduce distance legibility.
- **#9 Space Grotesk:** No italic variant. Use weight contrast for emphasis instead of italics.

### 2.4 Font Size Defaults (Research #10 Area 2)

| Element | Default Size | Minimum | Weight |
|---------|-------------|---------|--------|
| Title/Heading | 44pt | 36pt | Bold (700) or ExtraBold (800) |
| Subtitle | 32pt | 28pt | SemiBold (600) |
| Body text | 28pt | 24pt | Regular (400) or Medium (500) |
| Bullet points | 24pt | 20pt | Regular (400) |
| Captions/labels | 18pt | 16pt | Regular (400) |
| Source/footnote | 14pt | 12pt | Regular (400) -- only for attributions |

**Dark mode adjustment:** Increase body font weight by one step (Regular to Medium, Medium to SemiBold) to compensate for perceived thinning of light text on dark backgrounds.

### 2.5 Font Availability Strategy

Neither PptxGenJS nor python-pptx support font embedding. The slide-stylist must account for font availability:

1. **Preferred:** Use Google Font names (Inter, Montserrat, etc.) and check installation via `fc-list`
2. **Fallback:** If Google Fonts are not installed, map to universally safe fonts:

| Google Font | Safe Fallback |
|-------------|--------------|
| Inter | Arial |
| Montserrat | Arial, Verdana |
| Open Sans | Arial, Calibri |
| Roboto | Arial |
| Poppins | Trebuchet MS |
| Source Sans Pro | Calibri, Arial |
| Lato | Calibri |
| Raleway | Trebuchet MS |
| Source Serif Pro | Georgia |
| Merriweather | Georgia |

---

## 3. Image Style Token Derivation

### 3.1 What Image Style Tokens Are

Image style tokens are metadata in the StyleGuide (`image_style_tokens` object) that downstream services (imagegen-bridge, Image Generation Expert) use to generate visually consistent images. They consist of three components:

| Component | Schema Field | Purpose | Example |
|-----------|-------------|---------|---------|
| **Mood** | `mood` | Emotional tone of imagery | "professional, confident, innovative" |
| **Colour direction** | `color_direction` | How brand colours should appear in images | "cool blues and warm gold accents" |
| **Style modifiers** | `style_modifiers` | Technical generation parameters | ["clean flat photography", "soft gradients", "geometric shapes"] |

### 3.2 Derivation from Tone + Preferences

The slide-stylist derives image style tokens from:

1. **TalkBrief tone** -- maps to mood keywords
2. **BrandProfile palette** -- maps to colour direction
3. **BrandProfile approved/prohibited image styles** -- constrain style modifiers
4. **Speaker preferences** -- expressed during brainstorming

| TalkBrief Tone | Derived Mood | Typical Style Modifiers |
|----------------|-------------|------------------------|
| Formal / Corporate | "polished, authoritative, composed" | ["studio photography", "neutral backgrounds", "sharp lighting"] |
| Modern / Tech | "innovative, precise, forward-looking" | ["clean gradients", "geometric patterns", "flat design"] |
| Startup / Energetic | "dynamic, bold, aspirational" | ["vibrant colours", "isometric illustration", "action shots"] |
| Elegant / Luxury | "refined, sophisticated, understated" | ["soft lighting", "muted tones", "editorial photography"] |
| Friendly / Education | "warm, approachable, inclusive" | ["natural lighting", "rounded shapes", "diverse people"] |
| Bold / Impact | "powerful, dramatic, decisive" | ["high contrast", "full-bleed photography", "dark backgrounds"] |
| Technical / Data | "precise, credible, analytical" | ["minimal illustration", "clean backgrounds", "schematic style"] |

### 3.3 Brand Constraint Application to Image Tokens

- **Strict mode:** Style modifiers MUST come from `approved_image_styles`. Any style in `prohibited_image_styles` is a hard block. Colour direction is derived directly from the locked palette.
- **Guided mode:** `approved_image_styles` are the starting point but the Speaker may approve broader tokens. `prohibited_image_styles` remain hard blocks even in guided mode.

### 3.4 AI Generation Configuration

The StyleGuide feeds provider-specific colour parameters to the imagegen-bridge:

| Provider | Colour Control Method | Research #09 Section |
|----------|----------------------|---------------------|
| Recraft V3/V4 | `colors[]` hex array -- best-in-class native support | 3.2 |
| Ideogram 3.0 | `color_palette` with weighted hex members | 3.3 |
| FLUX.2 Pro/Max | JSON prompt with hex codes mapped to objects | 3.4 |
| GPT Image 1.5 | Natural language + hex in prompt text | 3.1 |
| Gemini 3 Pro | Reference images (no explicit hex parameter) | 3.1 |

---

## 4. Layout Intelligence

Layout Intelligence is a capability WITHIN the slide-stylist. It is deterministic -- engineering constants, not design choices. These templates are included automatically in every StyleGuide without consulting the Speaker.

### 4.1 Canvas and Margin Constants

| Property | Value |
|----------|-------|
| Canvas width | 10.0 inches |
| Canvas height | 5.625 inches |
| Margin | 0.5 inches (all sides) |
| Content area | 9.0 x 4.625 inches |

### 4.2 The 12 Layout Templates

Zone coordinates are (x, y, width, height) in inches. `null` means the zone is not used for that template.

| Slide Type | `text_zone` | `image_zone` | `background_treatment` |
|------------|-------------|--------------|----------------------|
| `title` | (1.0, 1.5, 8.0, 2.5) | (0, 0, 10.0, 5.625) | `image_bleed` |
| `section_divider` | (1.0, 1.5, 8.0, 2.5) | null | `solid_dark` |
| `content` | (0.5, 1.0, 5.5, 4.0) | (6.5, 0.5, 3.0, 4.625) | `solid_light` |
| `two_column` | (0.5, 1.0, 4.0, 4.0) | (5.5, 1.0, 4.0, 4.0) | `solid_light` |
| `image_feature` | (0.5, 3.5, 4.0, 1.5) | (0, 0, 10.0, 3.2) | `image_bleed` |
| `data_chart` | (0.5, 0.5, 9.0, 1.0) | (0.5, 1.6, 9.0, 3.5) | `solid_light` |
| `stat_callout` | (1.5, 1.0, 7.0, 3.5) | null | `solid_dark` |
| `quote` | (1.5, 1.0, 7.0, 3.0) | null | `solid_dark` |
| `icon_grid` | (0.5, 0.5, 9.0, 1.0) | (0.5, 1.6, 9.0, 3.5) | `solid_light` |
| `diagram` | (0.5, 0.5, 9.0, 1.0) | (0.5, 1.8, 9.0, 3.3) | `solid_light` |
| `closing` | (1.0, 1.0, 8.0, 3.5) | null | `gradient` |
| `blank_visual` | null | (0, 0, 10.0, 5.625) | `image_bleed` |

### 4.3 Background Treatment Definitions

| Treatment | Description | When Used |
|-----------|-------------|-----------|
| `solid_light` | Background colour from palette | Most content slides |
| `solid_dark` | Primary or near-black from palette | Section dividers, callouts, quotes |
| `image_bleed` | Full-bleed image covers entire slide | Title, image feature, blank visual |
| `gradient` | Gradient using brand colours | Closing slide |
| `pattern_tile` | Repeating pattern from brand colours | Optional decorative |

### 4.4 Layout Template Validation Rules (Research #01 Section 7)

| Rule | Check | Severity |
|------|-------|----------|
| All content within safe margins | Shapes >= 0.5" from all edges | error |
| No overlapping text boxes | Bounding box intersection test | error |
| White space ratio >= 40% | Content area / slide area <= 60% | warning |
| Title position consistent across deck | Y-position variance < 0.25" | warning |
| No critical content in bottom 10% | Audience sight-line obstruction zone | warning |
| Image aspect ratio preserved | Width/height ratio within 5% of original | error |

---

## 5. Brand Constraint Application

### 5.1 How Compliance Mode Constrains the Design Space

The slide-stylist checks compliance mode FIRST before proposing any options:

**Strict mode constraints:**
- Palette: Locked. The slide-stylist presents the palette for confirmation only. May propose tint/shade variations of the accent for visual variety.
- Fonts: Locked. The brand's heading and body fonts are used exactly. No alternatives proposed.
- Image tokens: Constrained to `approved_image_styles` from BrandProfile. The slide-stylist proposes mood variations within that set.
- The slide-stylist's proposals are limited to: accent variations, image mood within approved styles, layout preferences, background treatment choices.

**Guided mode constraints:**
- Palette: The BrandProfile primary colour is the anchor. The slide-stylist may propose secondary and accent variations using colour harmony rules (analogous, triadic, split-complementary from Research #09 Section 1.2).
- Fonts: The BrandProfile fonts are the starting point. The slide-stylist may propose alternative pairings from the 10 scored set, explaining why the alternative might better suit the talk's tone.
- Image tokens: `approved_image_styles` are guidance, not hard constraints. Broader style exploration is permitted with Speaker consent. `prohibited_image_styles` remain hard blocks.

**No brand:**
- Full creative latitude. The slide-stylist proposes 2-3 complete design directions (palette + fonts + mood) based on topic and tone.

### 5.2 Validation After Style Derivation

Before writing the StyleGuide, validate:

1. **Contrast:** All text-on-background pairings meet WCAG AA (4.5:1) minimum, with projection-safe (7:1) as a warning threshold
2. **Palette size:** Total distinct colours (excluding images) <= 5 (COL-002 from Research #01)
3. **Font count:** <= 2 font families (TYP-003 from Research #01)
4. **Font sizes:** Title >= 1.33x body (Perfect Fourth ratio, TYP-004 from Research #01)
5. **All 12 layout templates present:** The templates table is complete
6. **Brand compliance (strict mode only):** palette.primary, palette.secondary, typography.heading_font, typography.body_font match BrandProfile values exactly

---

## 6. Design Rules (Machine-Checkable)

These rules validate the StyleGuide output:

| Rule | Check | Severity |
|------|-------|----------|
| Schema valid | Passes `style_guide.schema.json` validation | error |
| Palette complete | All required palette fields present and valid hex | error |
| Contrast AA | text_primary on background >= 4.5:1 | error |
| Contrast projection | text_primary on background >= 7:1 | warning |
| Font families <= 2 | Count distinct families in typography section | warning |
| 12 templates present | All 12 slide types in layout.templates | error |
| Title >= 1.33x body | heading_sizes.title_slide / body_size >= 1.33 | warning |
| No thin weights | heading/body weights >= 400 | warning |
| Body size >= 20pt | body_size >= 20 | error |
| Caption size >= 14pt | caption_size >= 14 | warning |
| Strict brand match | palette + fonts unchanged from BrandProfile when strict | error |

---

## 7. Anti-Patterns

- **Inventing font pairings at runtime.** Pairings come from the validated set of 10. Random combinations risk poor projection legibility and visual clash.
- **Generating the StyleGuide without Speaker interaction.** The collaborative workflow is the point -- the slide-stylist proposes, the Speaker decides. Silent generation bypasses the design partnership.
- **Using thin/light font weights for projection.** Minimum Regular (400) for body text, SemiBold (600) for headings. Thin (100-300) weights are invisible on projection.
- **Ignoring prohibited_image_styles in guided mode.** Prohibitions are hard blocks regardless of compliance mode. Only approved styles are relaxed in guided mode.
- **Proposing palette changes in strict mode.** Strict means the palette is non-negotiable. The slide-stylist works WITHIN the palette, not around it.
- **Using condensed fonts for body text.** Oswald and other condensed fonts are heading-only. Character width is more important than serif/sans-serif for distance legibility.
- **Using pure white or pure black.** Off-white backgrounds (~F5F5F5) and near-black text (~1A1A2E) are superior for projection. Pure extremes cause glare or excessive contrast.

---

## Sources

- Research #09 (Brand Extraction & Style Transfer): Section 1.2 (colour harmony derivation), Section 1.6 (60-30-10 rule), Section 3 (AI generation colour control), Section 6 (StyleGuide schema)
- Research #10 (Font Strategy & Typography): Area 1 (10 scored pairings + quick selection guide), Area 2 (font sizes for projection), Area 4 (weight/contrast/x-height for projection), Area 5 (text rendering)
- Research #01 (Slide Layout Intelligence): Section 2 (12-column grid, safe zones), Section 3 (design principles), Section 6 (projection requirements), Section 7 (machine-checkable rules)
- Design Services architecture: slide-stylist workflow, compliance modes, layout intelligence, design decisions
- Schema: `src/schemas/style_guide.schema.json` (output contract)
