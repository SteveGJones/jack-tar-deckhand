# Synthesis: brand-manager

> Distilled from: research/09-brand-extraction-style-transfer.md, research/10-font-strategy-typography.md, research/01-slide-layout-intelligence.md, docs/architecture/design-services.md, src/schemas/brand_profile.schema.json

## 1. Brand Input Sources

The brand-manager accepts five input types. Claude's native capabilities handle all extraction -- no Python colour libraries are used at runtime. The skill is a pure SKILL.md.

### 1.1 PDF Brand Guidelines

- **TalkBrief field:** `branding.brand_guidelines_path`
- **Method:** Claude reads PDF natively, extracts mandated colours (hex values), font families, usage rules, prohibited styles, and logo placement requirements.
- **What to extract:** Primary/secondary/accent colours, approved font families, minimum clear space rules, approved image styles, prohibited image styles (e.g. "no cartoons"), background colour preferences.

### 1.2 Corporate .pptx Template

- **TalkBrief field:** `branding.template_pptx_path`
- **Method:** Claude parses the .pptx file. Theme colours live in `<a:theme>/<a:themeElements>/<a:clrScheme>` XML. The 12 theme colour slots (dk1, lt1, dk2, lt2, accent1-6, hlink, folHlink) define the brand palette. Font families come from `<a:fontScheme>` -- majorFont (headings) and minorFont (body).
- **What to extract:** All 12 theme colours as hex, heading + body font families, slide layout placeholders (position, size, type), any custom slide masters.
- **Key insight (Research #09 Section 5):** Font inheritance cascades from master to layout to slide. All formatting properties flow down through the hierarchy.

### 1.3 Logo Vision Analysis

- **TalkBrief field:** `branding.logo_path`
- **Method:** Claude vision analyses the logo image to extract dominant colours and visual character (geometric vs organic, modern vs traditional, heavy vs light).
- **Colour extraction approach (Research #09 Section 1.1):** The MMCQ (Modified Median Cut Quantization) algorithm from ColorThief extracts dominant colours, but since brand-manager is a SKILL.md (no Python), Claude's vision reasoning performs the equivalent perceptual analysis directly.
- **Outputs:** 2-4 dominant colours (primary, secondary, potential accents), visual character descriptors that inform tone and image style.

### 1.4 Manual Entry

- **TalkBrief fields:** `branding.primary_color`, `branding.secondary_color`, `branding.font_preference`
- **Method:** Direct use -- values pass through to the BrandProfile without extraction.
- **Validation:** Hex codes must match `^[0-9A-Fa-f]{6}$` (6-char hex without hash prefix, per schema).

### 1.5 Company-Name Inference

- **TalkBrief field:** `branding.company_name` (when no other brand assets provided)
- **Method:** Claude infers appropriate defaults from industry, domain, and company type. Uses the industry-to-font mapping (Research #10 Section 2.1) and colour psychology to select sensible defaults.
- **Fallback order:** Existing brand_id profile > PDF guidelines > .pptx template > logo analysis > manual entry > company-name inference. Each successive source fills gaps left by earlier ones; earlier sources take priority when values conflict.

---

## 2. Palette Derivation Rules

### 2.1 The 60-30-10 Rule (Research #09 Section 1.6)

All brand palettes follow the 60-30-10 colour proportion rule:

| Role | Percentage | Slide Application | Schema Field |
|------|-----------|-------------------|--------------|
| **Dominant** | 60% | Slide background, large areas | `palette.background` |
| **Secondary** | 30% | Headers, charts, key visuals | `palette.primary` |
| **Accent** | 10% | CTAs, highlights, emphasis | `palette.accent` |

### 2.2 Split-Complementary Accent Derivation (Research #09 Section 1.2)

When only a primary colour is extracted (e.g. from logo), derive the rest:

1. **Secondary:** Analogous hue (+30 degrees in HSL) at same lightness/saturation
2. **Accent:** Split-complementary hue (+150 or +210 degrees) for visual punch
3. **Background:** Brand hue retained but lightness pushed to 0.97, saturation reduced to 8% -- creates a near-white tinted neutral (Research #09 Section 1.4)
4. **Background_alt:** Brand hue, lightness 0.93, saturation 6% -- slightly darker surface/card colour
5. **Text_primary:** Brand hue, lightness 0.13, saturation 20% -- near-black tinted
6. **Text_muted:** Brand hue, lightness 0.40, saturation 10% -- secondary text
7. **Text_on_dark:** Brand hue, lightness 0.93, saturation 5% -- for dark backgrounds
8. **Chart_series:** 3-8 colours derived from the brand primary using triadic, tetradic, and analogous harmonies, validated for mutual distinctness

### 2.3 WCAG Contrast Requirements (Research #09 Section 1.3)

All palette pairings must meet these thresholds:

| Pairing | Minimum Ratio | Standard |
|---------|--------------|----------|
| text_primary on background | 4.5:1 | WCAG AA normal text |
| text_primary on background_alt | 4.5:1 | WCAG AA normal text |
| text_on_dark on primary | 4.5:1 | WCAG AA normal text |
| Large text (24pt+) on any background | 3:1 | WCAG AA large text |
| **Projection-recommended** | **7:1** | WCAG AAA / projection safe |

Formula: `contrast = (L1 + 0.05) / (L2 + 0.05)` where L1 and L2 are relative luminances of the lighter and darker colours respectively.

**Projection override (Research #01 Section 6.2):** For projected content, use WCAG AAA ratios (7:1 normal text, 4.5:1 large text) as the minimum rather than AA. Ambient light washout degrades effective contrast.

### 2.4 Delta-E 2000 for Brand Colour Matching

When comparing extracted colours to known brand values (e.g. verifying that a .pptx template matches the PDF guidelines), use Delta-E 2000 perceptual distance:

| Delta-E | Interpretation |
|---------|---------------|
| < 1.0 | Not perceptible -- colours match |
| 1-2 | Perceptible through close observation |
| 2-10 | Perceptible at a glance -- flag for review |
| > 10 | Clearly different -- warn the Speaker |

---

## 3. Persistence Model

### 3.1 Directory Structure

```
./brands/{brand-id}/
    brand-profile.json     # BrandProfile schema instance
    logo.png               # Copied logo (if provided)
    source-guidelines.pdf  # Copied PDF (if provided)
```

The `brand-id` is a URL-safe slug (pattern `^[a-z0-9-]+$`) derived from the company name. Example: "Acme Financial Services" becomes `acme-financial-services`.

### 3.2 BrandProfile Schema Alignment

The persisted file conforms to `src/schemas/brand_profile.schema.json`. Required fields:

| Field | Type | Description |
|-------|------|-------------|
| `brand_id` | string | URL-safe slug identifier |
| `company_name` | string | Display name |
| `palette.primary` | hex string | Brand primary colour (required) |
| `typography.heading_font` | string | Heading font family |
| `typography.body_font` | string | Body font family |
| `compliance_mode` | enum | `strict` or `guided` |
| `extracted_at` | datetime | When profile was created/updated |

Optional fields: `source_inputs` (array tracking which inputs were used), `approved_image_styles`, `prohibited_image_styles`, `source_hash` (for change detection).

### 3.3 Session Copy

When a brand is used for a deck session, the brand-manager copies a reference to `./tmp/deck/brand-profile.json` for the current deck. This keeps the per-deck working directory self-contained while the canonical profile persists in `./brands/`.

---

## 4. Compliance Modes

### 4.1 Strict Mode

Brand values are non-negotiable. The slide-stylist receives hard constraints.

| Design Area | Locked | Permitted |
|-------------|--------|-----------|
| Primary colour | Locked from BrandProfile | -- |
| Secondary colour | Locked from BrandProfile | -- |
| Accent colour | Locked from BrandProfile | Tint/shade variations only |
| Background | Locked from BrandProfile | -- |
| Heading font | Locked from BrandProfile | -- |
| Body font | Locked from BrandProfile | -- |
| Image styles | Constrained to `approved_image_styles` | Mood within approved styles |
| Prohibited styles | Enforced -- these are hard blocks | -- |
| Layout preferences | -- | Full latitude |
| Background treatment | -- | Speaker chooses |

### 4.2 Guided Mode

Brand values provide a foundation. The slide-stylist may propose extensions.

| Design Area | Starting Point | Speaker May Approve |
|-------------|---------------|---------------------|
| Primary colour | From BrandProfile | -- (kept as anchor) |
| Secondary colour | From BrandProfile | Variations within brand family |
| Accent colour | From BrandProfile | Alternative harmonies (analogous, triadic) |
| Background | From BrandProfile | Alternative neutrals derived from brand hue |
| Heading font | From BrandProfile | Alternative pairings from the 10 scored set |
| Body font | From BrandProfile | Alternative pairings from the 10 scored set |
| Image styles | `approved_image_styles` as guidance | Broader style tokens with Speaker consent |
| Prohibited styles | Still enforced | -- |
| Layout preferences | -- | Full latitude |

### 4.3 Key Difference

In strict mode, the slide-stylist CANNOT propose changing the palette or fonts -- it can only work within them. In guided mode, the slide-stylist CAN propose alternatives but the Speaker must explicitly approve each change.

---

## 5. Speaker Approval Workflow

### 5.1 Existing Profile Review

When `brand_id` is provided and a profile exists at `./brands/{id}/brand-profile.json`:

1. Load the profile
2. Present a summary to the Speaker: company name, primary/secondary/accent colours (with visual swatches if possible), heading and body fonts, compliance mode, last updated date
3. Ask: "Is this still current, or do you want to update anything?"
4. If confirmed: proceed to slide-stylist
5. If updates needed: re-extract from updated assets, present diff, get approval

### 5.2 New Profile Extraction

When no existing profile matches:

1. Process all available brand inputs (PDF, .pptx, logo, manual values, company name)
2. Build a candidate BrandProfile
3. Present to the Speaker with clear provenance for each value:
   - "Primary colour #002D72 -- extracted from your logo"
   - "Heading font Montserrat -- inferred from your industry (finance/corporate)"
   - "Compliance mode: guided (default) -- change to strict if brand guidelines are mandatory"
4. Speaker approves or corrects each section
5. Persist to `./brands/{brand-id}/brand-profile.json`

### 5.3 Approval Gate

No BrandProfile enters the pipeline without explicit Speaker confirmation. This is a hard gate, not advisory. The brand-manager blocks until the Speaker approves.

---

## 6. Design Rules (Machine-Checkable)

These rules can be validated programmatically against the BrandProfile schema:

| Rule | Check | Severity |
|------|-------|----------|
| Palette has primary colour | `palette.primary` is non-empty 6-char hex | error |
| All hex values are valid | Each colour matches `^[0-9A-Fa-f]{6}$` | error |
| Text-on-background contrast >= 4.5:1 | Compute relative luminance ratio | error |
| Projection-safe contrast >= 7:1 | Compute relative luminance ratio for text on background | warning |
| Chart series has 3-8 colours | `palette.chart_series` length check | error |
| Compliance mode is set | `compliance_mode` in ["strict", "guided"] | error |
| Brand ID is URL-safe | `brand_id` matches `^[a-z0-9-]+$` | error |
| No pure white background | `palette.background` is not `FFFFFF` | warning |
| No pure black text | `palette.text_primary` is not `000000` | warning |

---

## 7. Anti-Patterns

- **Running Python colour extraction code.** Brand-manager is a SKILL.md -- Claude's vision and reasoning ARE the implementation. No ColorThief, no colour-science library at runtime.
- **Accepting a brand profile without Speaker approval.** Every profile must pass through the approval gate, even when loaded from a cached file.
- **Using guided mode as "anything goes."** Guided mode still anchors to the BrandProfile -- it permits extensions, not replacements. The primary colour is never changed in either mode.
- **Storing profiles in the per-deck `./tmp/deck/` directory.** Profiles persist in `./brands/` and are copied (not moved) into the deck session.
- **Using pure white (#FFFFFF) backgrounds or pure black (#000000) text.** Research consistently shows off-white (e.g. F8F9FA) and near-black (e.g. 1A1A2E) are superior for projection.

---

## Sources

- Research #09 (Brand Extraction & Style Transfer): Sections 1.1-1.6 (colour extraction, harmony, WCAG, neutrals, Delta-E, 60-30-10), Section 5 (PPTX template ingestion), Section 6 (StyleGuide schema)
- Research #10 (Font Strategy & Typography): Section 2.1 (industry-to-font mapping)
- Research #01 (Slide Layout Intelligence): Section 6.2 (projection contrast requirements)
- Design Services architecture: brand-manager workflow, compliance modes, persistence model
- Schema: `src/schemas/brand_profile.schema.json` (field names, types, patterns)
