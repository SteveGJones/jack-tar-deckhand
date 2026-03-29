# Synthesis: deck-assembler

> Distilled from: research/03-pptxgenjs-vs-python-pptx.md, research/14-animations-advanced-pptx.md, research/01-slide-layout-intelligence.md, research/10-font-strategy-typography.md, research/02-pptx-skill-audit.md, docs/architecture/data-contracts.md

---

## 1. Technology Decision: PptxGenJS v4.0.1 via Node.js

**Decision:** Use PptxGenJS v4.0.1 as the PPTX assembly engine. Do not switch to python-pptx.

**Rationale (from Research #03, Section 7):**

| Factor | Assessment |
|--------|------------|
| Existing investment | The upstream `pptx` skill and `generate-presentation` skill already use PptxGenJS |
| Active maintenance | PptxGenJS v4.0.1 released June 2025; python-pptx dormant since August 2024 |
| Claude Code native | Node.js runs natively in Claude Code; Python requires separate process spawning |
| Feature parity | For creation-only workflows, PptxGenJS matches or exceeds python-pptx |
| Zero dependencies | PptxGenJS has no runtime dependencies |
| Image sizing | Built-in `contain`/`cover`/`crop` modes -- purpose-built for presentations |
| TypeScript | Full type definitions for IDE assistance and error prevention |

**Architecture:** Python handles all image processing (Pillow, rembg, matplotlib, CairoSVG). Images are saved to `./tmp/deck/images/`. Node.js (PptxGenJS) assembles the final `.pptx`, referencing images by file path. Claude Code orchestrates both via Bash tool calls.

**Performance:** PPTX assembly takes 1-5 seconds for a 25-40 slide deck. Image generation (2-8 minutes) dominates total wall-clock time. Assembly is never the bottleneck.

---

## 2. Input Contracts

The deck-assembler reads five upstream contracts from the `./tmp/deck/` directory. All are JSON files validated against schemas in `src/schemas/`.

| Contract | File | Schema | Producer | Key Fields for Assembly |
|----------|------|--------|----------|------------------------|
| SlideOutline | `./tmp/deck/outline.json` | `src/schemas/slide_outline.schema.json` | narrative-architect | `slides[].slide_number`, `slide_type`, `headline`, `body_points`, `layout_template`, `visual_type` |
| StyleGuide | `./tmp/deck/style-guide.json` | `src/schemas/style_guide.schema.json` | slide-stylist | `palette`, `typography`, `layout.templates`, `layout.margin_inches`, `layout.slide_width_inches`, `layout.slide_height_inches` |
| ImageManifest | `./tmp/deck/image-manifest.json` | `src/schemas/image_manifest.schema.json` | imagegen-bridge | `images[].slide_number`, `file_path`, `placement_zone`, `dimensions`, `alt_text`, `status` |
| ChartManifest | `./tmp/deck/chart-manifest.json` | `src/schemas/chart_manifest.schema.json` | chart-renderer | `charts[].slide_number`, `file_path`, `chart_type`, `dimensions`, `alt_text`, `status` |
| SpeakerNotes | `./tmp/deck/speaker-notes.json` | `src/schemas/speaker_notes.schema.json` | speaker-notes-writer | `notes[].slide_number`, `text`, `cues` |

**Loading sequence:**

1. Read and validate `style-guide.json` -- provides dimensions, palette, typography, and layout templates
2. Read and validate `outline.json` -- the ordered slide definitions
3. Read `image-manifest.json` -- match images to slides by `slide_number`
4. Read `chart-manifest.json` -- match charts to slides by `slide_number`
5. Read `speaker-notes.json` -- match notes to slides by `slide_number`

All contracts are frozen (immutable) by the time deck-assembler runs. The assembler is a pure consumer -- it reads but never modifies any upstream contract.

---

## 3. Slide Master Definitions

Each of the 12 `slide_type` enum values from the SlideOutline schema maps to a PptxGenJS `defineSlideMaster()` call. Master definitions reference the layout archetypes catalogued in Research #01 Section 1.1.

### Master Registration

```javascript
const pptx = new PptxGenJS();

// Set presentation-level theme from StyleGuide
pptx.theme = {
  headFontFace: styleGuide.typography.heading_font,
  bodyFontFace: styleGuide.typography.body_font
};

// Set slide dimensions from StyleGuide
pptx.defineLayout({
  name: "WIDESCREEN_16x9",
  width: styleGuide.layout.slide_width_inches,   // 10
  height: styleGuide.layout.slide_height_inches   // 5.625
});
pptx.layout = "WIDESCREEN_16x9";
```

### Master-to-Archetype Mapping

| slide_type | Research #01 Archetype | Background Treatment | Content Zones |
|------------|----------------------|---------------------|---------------|
| `title` | #1 Title Slide | `solid_dark` or `image_bleed` | Centre title (80% width), subtitle (60% width), footer strip |
| `section_divider` | #2 Section Divider | `solid_dark` or `gradient` | Large section text centred, optional subtitle |
| `content` | #4 Single Point | `solid_light` | Title bar (top 15%), body zone (remaining) |
| `two_column` | #5 Two-Column | `solid_light` | Title bar, left column (5-48%), right column (52-95%) |
| `image_feature` | #7/#8 Full/Half Bleed | `image_bleed` or `solid_light` | Image zone (50-100%), text overlay or adjacent text zone |
| `data_chart` | #15 Data/Chart | `solid_light` | Title bar, chart zone (60-70%), insight callout |
| `stat_callout` | #10 Stat Callout / Big Number | `solid_light` or `solid_dark` | Giant number zone (centre), label below, context line |
| `quote` | #12 Quote / Testimonial | `solid_light` | Quote text centred with quotation marks, attribution below |
| `icon_grid` | #11 Icon Grid | `solid_light` | Title bar, grid of 3-6 icon+label pairs |
| `diagram` | #8/#9 Image with Context | `solid_light` | Title bar, diagram image zone, optional annotation text |
| `closing` | #17 Closing / CTA | `solid_dark` | Central message, contact details, optional QR code |
| `blank_visual` | #18 Blank / Breathing Room | `solid_light` or `image_bleed` | Minimal or no content; visual pause |

### defineSlideMaster() Pattern

Each master is registered with the PptxGenJS instance before any slides are created:

```javascript
pptx.defineSlideMaster({
  title: "MASTER_CONTENT",
  background: { color: styleGuide.palette.background },
  objects: [
    // Title placeholder
    {
      placeholder: {
        options: {
          name: "title",
          type: "title",
          x: margin, y: margin,
          w: contentWidth, h: titleHeight,
          fontSize: styleGuide.typography.heading_sizes.slide_heading,
          fontFace: styleGuide.typography.heading_font,
          color: styleGuide.palette.text_primary,
          bold: true
        }
      }
    },
    // Slide number
    {
      text: {
        text: "{{slideNumber}}",
        options: {
          x: slideWidth - margin - 0.5,
          y: slideHeight - margin,
          w: 0.5, h: 0.3,
          fontSize: styleGuide.typography.caption_size,
          color: styleGuide.palette.text_muted,
          align: "right"
        }
      }
    }
  ]
});
```

---

## 4. Content Zone Mapping

The StyleGuide `layout.templates` object defines per-slide-type zones with `x`, `y`, `w`, `h` coordinates in inches. These map directly to PptxGenJS positioning parameters.

### Coordinate System

PptxGenJS uses inches as its native coordinate unit. The StyleGuide schema stores coordinates in inches. No unit conversion is required.

| StyleGuide Property | PptxGenJS Parameter | Default (inches) |
|--------------------|--------------------|-------------------|
| `layout.slide_width_inches` | Presentation `width` | 10 |
| `layout.slide_height_inches` | Presentation `height` | 5.625 |
| `layout.margin_inches` | Safe zone inset | 0.5 |

### Template Zone Resolution

For each slide, the assembler resolves the layout template:

1. Look up `slide.layout_template` in `styleGuide.layout.templates`
2. If not found, fall back to a default template derived from `slide.slide_type`
3. Extract `text_zone`, `image_zone`, and `background_treatment`

```javascript
function resolveTemplate(slide, styleGuide) {
  const templates = styleGuide.layout.templates || {};
  const templateName = slide.layout_template || slide.slide_type;
  const template = templates[templateName] || getDefaultTemplate(slide.slide_type, styleGuide);
  return template;
}
```

### Default Zone Calculations

When no explicit template is provided, zones are computed from the 12-column grid (Research #01, Section 2.1):

| Layout | Text Zone (x, y, w, h) | Image Zone (x, y, w, h) |
|--------|------------------------|--------------------------|
| Full-width content | (0.5, 1.2, 9.0, 3.9) | -- |
| Two-column | Left: (0.5, 1.2, 4.1, 3.9), Right: (4.9, 1.2, 4.6, 3.9) | -- |
| Image left + text right | (5.3, 1.2, 4.2, 3.9) | (0.5, 1.2, 4.5, 3.9) |
| Image right + text left | (0.5, 1.2, 4.2, 3.9) | (5.0, 1.2, 4.5, 3.9) |
| Full-bleed image | Overlay: (0.5, 3.5, 5.0, 1.6) | (0, 0, 10, 5.625) |
| Chart with callout | Callout: (0.5, 1.2, 3.0, 1.5) | Chart: (3.8, 1.2, 5.7, 3.9) |

All zones respect the 0.5" safe margin (457,200 EMU) from Research #01, Rule LAY-001. The bottom 10% of the slide is avoided for critical content (Rule LAY-007).

---

## 5. Image Placement

### Matching Images to Slides

Images from the ImageManifest are matched to slides by `slide_number`. Each image entry includes a `placement_zone` string that specifies where on the slide the image belongs.

```javascript
function getImagesForSlide(slideNumber, imageManifest) {
  return imageManifest.images.filter(
    img => img.slide_number === slideNumber
          && img.status !== "failed"
  );
}
```

### placement_zone to addImage() Mapping

The `placement_zone` string maps to the corresponding zone coordinates from the resolved template:

| placement_zone | Target Zone | Sizing Mode |
|----------------|-------------|-------------|
| `background` | Full slide (0, 0, slideW, slideH) | `cover` |
| `image_zone` | Template's `image_zone` coordinates | `contain` |
| `icon_1`, `icon_2`, ... `icon_6` | Computed grid positions | `contain` |
| `hero` | Template's `image_zone` or full-bleed | `cover` |

### PptxGenJS addImage() Call

```javascript
slide.addImage({
  path: image.file_path,          // from ImageManifest
  x: zone.x,                      // from template
  y: zone.y,
  w: zone.w,
  h: zone.h,
  sizing: {                        // PptxGenJS sizing modes
    type: sizingMode,              // "contain", "cover", or "crop"
    w: zone.w,
    h: zone.h
  },
  altText: image.alt_text || ""    // from ImageManifest (accessibility)
});
```

### Sizing Mode Selection

PptxGenJS provides three sizing modes (Research #03, Feature Matrix row 19):

| Mode | Behaviour | Use Case |
|------|-----------|----------|
| `contain` | Scale to fit within zone, preserving aspect ratio; may leave empty space | Default for content images, icons, diagrams |
| `cover` | Scale to fill zone, preserving aspect ratio; overflows cropped | Full-bleed backgrounds, hero images |
| `crop` | Display specified portion of the image | When a specific region is needed |

**Selection logic:**

```javascript
function selectSizingMode(placementZone, slideType) {
  if (placementZone === "background") return "cover";
  if (slideType === "image_feature" && placementZone === "image_zone") return "cover";
  if (slideType === "blank_visual") return "cover";
  return "contain";
}
```

### Background Images

For slides with `background_treatment: "image_bleed"`, the image is set as the slide background rather than added as an element:

```javascript
if (template.background_treatment === "image_bleed" && bgImage) {
  slide.background = { path: bgImage.file_path };
} else {
  slide.background = { color: styleGuide.palette.background };
}
```

### Failed/Placeholder Images

Images with `status: "failed"` are skipped. Images with `status: "placeholder"` are placed normally (the placeholder image file was generated as a fallback by the imagegen-bridge).

---

## 6. Chart Placement

Charts are pre-rendered as PNG images by the chart-renderer (using matplotlib). The deck-assembler treats them identically to content images -- they are placed via `slide.addImage()`, not via PptxGenJS's native chart API.

**Rationale:** Using pre-rendered PNGs ensures visual consistency with the StyleGuide palette and typography. The chart-renderer already applies the correct fonts, colours, and de-cluttered Tufte-style formatting. Re-creating charts via PptxGenJS's native chart API would require duplicating all that styling logic.

### Matching Charts to Slides

```javascript
function getChartsForSlide(slideNumber, chartManifest) {
  return chartManifest.charts.filter(
    chart => chart.slide_number === slideNumber
            && chart.status !== "failed"
  );
}
```

### Placement

Charts are placed in the template's `image_zone` (or a dedicated `chart_zone` if the template defines one). For `data_chart` slide types, the chart typically occupies 60-70% of the content area (Research #01, Archetype #15).

```javascript
const chartZone = template.chart_zone || template.image_zone || {
  x: 3.8, y: 1.2, w: 5.7, h: 3.9
};

slide.addImage({
  path: chart.file_path,
  x: chartZone.x,
  y: chartZone.y,
  w: chartZone.w,
  h: chartZone.h,
  sizing: { type: "contain", w: chartZone.w, h: chartZone.h },
  altText: chart.alt_text || ""
});
```

### stat_card Chart Type

The `stat_card` chart type (from ChartManifest) is a special case. It renders a large number with supporting context as an image. For `stat_callout` slides, the assembler places the stat_card image in the centre of the slide at a larger size to match the "big number" archetype (Research #01, Archetype #10).

---

## 7. Speaker Notes

### Contract

SpeakerNotes entries are matched to slides by `slide_number`. Each entry contains:

- `text` -- the speaker notes prose, with optional timing markers (e.g., `[~5:30]`)
- `estimated_seconds` -- estimated speaking duration
- `timing_marker` -- cumulative time mark
- `cues` -- array of interaction cues typed as `transition`, `pause`, `audience_interaction`, `emphasis`, `demo`, or `build_animation`

### PptxGenJS API

PptxGenJS exposes `slide.addNotes()` for adding speaker notes to any slide:

```javascript
const noteEntry = speakerNotes.notes.find(
  n => n.slide_number === slide.slide_number
);

if (noteEntry) {
  // Format notes text with cue annotations
  let notesText = noteEntry.text;

  if (noteEntry.timing_marker) {
    notesText = `[${noteEntry.timing_marker}] ${notesText}`;
  }

  if (noteEntry.cues && noteEntry.cues.length > 0) {
    const cueLines = noteEntry.cues
      .map(cue => `[${cue.type.toUpperCase()}] ${cue.text}`)
      .join("\n");
    notesText += "\n\n---\n" + cueLines;
  }

  slide.addNotes(notesText);
}
```

### Formatting Conventions

Speaker notes are plain text (PptxGenJS does not support rich-text notes). The assembler uses a consistent formatting convention:

- Timing marker at the start: `[~5:30]`
- Main notes body as prose
- Separator line (`---`)
- Cues in `[TYPE] description` format

---

## 8. Progressive Builds

### Concept (Research #14, Section 5)

Neither PptxGenJS nor python-pptx supports shape-level animations. The standard workaround is progressive builds: generating multiple slides where each successive slide adds one more element. The presenter clicks through, creating the effect of elements "appearing."

This approach covers approximately 80% of what presenters call "animations" (Research #14, Section 11).

### Trigger: build_animation Cues

The SpeakerNotes contract includes `cues` with `type: "build_animation"`. When a slide's notes contain one or more `build_animation` cues, the assembler generates multiple copies of that slide with incremental content.

### Implementation

```javascript
function generateBuildSlides(pptx, slideDef, template, styleGuide, noteEntry) {
  const bodyPoints = slideDef.body_points || [];
  const buildCues = (noteEntry?.cues || [])
    .filter(c => c.type === "build_animation");

  // If no build cues or <= 1 body point, generate a single slide
  if (buildCues.length === 0 || bodyPoints.length <= 1) {
    return [generateSingleSlide(pptx, slideDef, template, styleGuide)];
  }

  const slides = [];
  for (let step = 1; step <= bodyPoints.length; step++) {
    const slide = pptx.addSlide({ masterName: masterForType(slideDef.slide_type) });

    // Title is always visible
    addTitle(slide, slideDef.headline, styleGuide);

    // Add bullets up to current step
    for (let i = 0; i < step; i++) {
      const isCurrent = (i === step - 1);
      slide.addText(bodyPoints[i], {
        x: template.text_zone.x,
        y: template.text_zone.y + (i * 0.6),
        w: template.text_zone.w,
        h: 0.5,
        fontSize: styleGuide.typography.body_size,
        fontFace: styleGuide.typography.body_font,
        color: isCurrent
          ? styleGuide.palette.text_primary
          : styleGuide.palette.text_muted,   // Dim previous items (25% de-emphasis per Research #01 Section 3.4)
        bullet: true
      });
    }

    // Speaker notes only on the last build slide
    if (step === bodyPoints.length && noteEntry) {
      slide.addNotes(noteEntry.text);
    }

    slides.push(slide);
  }

  return slides;
}
```

### File Size Impact

Each duplicated slide adds approximately 2-5 KB for text-only content. Background images are stored once in the `.pptx` archive and referenced by each slide, not duplicated. A 4-bullet build generates 4 slides instead of 1, adding approximately 8-20 KB -- negligible for a typical presentation (Research #14, Section 5).

### Advantages Over True Animations

- Works when exported to PDF (animations do not)
- Works reliably in screen sharing and video conferencing
- Accessible -- screen readers can process each slide independently
- No fragile OOXML animation XML required

---

## 9. File Optimisation

### Image Compression Before Embedding

Images typically account for 80-90% of PPTX file size (Research #03, Section 5). The assembler should optimise images before PptxGenJS embeds them.

**Pre-embedding compression pipeline (Python, run before Node.js assembly):**

```python
from PIL import Image
import os

def optimise_for_pptx(image_path, max_dimension=1920, quality=85):
    """Compress and resize image for PPTX embedding."""
    img = Image.open(image_path)

    # Strip EXIF metadata (privacy + file size)
    if hasattr(img, "info"):
        img.info.pop("exif", None)

    # Resize if larger than needed
    # At 96 DPI on a 10" wide slide, max useful width is ~960px
    # At 150% oversampling (Rule LAY-009), target is ~1440px
    # Use 1920px as safe maximum for full-bleed images
    if max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    # Save as optimised PNG (for transparency) or JPEG (for photos)
    if img.mode == "RGBA" or image_path.lower().endswith(".png"):
        img.save(image_path, "PNG", optimize=True)
    else:
        img = img.convert("RGB")
        img.save(image_path, "JPEG", quality=quality, optimize=True)
```

**Target sizes:**

| Image Role | Max Dimension (px) | Format | Expected Size |
|------------|-------------------|--------|---------------|
| Full-bleed background | 1920 | JPEG (quality 85) | 200-500 KB |
| Content/hero image | 1440 | JPEG or PNG | 150-400 KB |
| Chart render | 1440 | PNG (optimised) | 100-300 KB |
| Icon | 512 | PNG (transparent) | 10-50 KB |

### Metadata Stripping

All images should have EXIF metadata stripped before embedding:

- Removes GPS location data (privacy)
- Removes camera/device information
- Removes thumbnail previews
- Reduces file size by 5-50 KB per image

### Expected Output Size

A 20-slide deck with optimised images should be 3-8 MB (Research #03, Section 5). A 40-slide conference deck with heavy imagery should remain under 15 MB.

### PptxGenJS Compression

PptxGenJS supports compression options on export:

```javascript
pptx.writeFile({
  fileName: "presentation.pptx",
  compression: true   // Enable ZIP compression
});
```

---

## 10. Wrapping the pptx Skill

### Relationship to Existing Skills

The deck-assembler **wraps** the existing `pptx` skill (Research #02, Section 4). It does not replace PptxGenJS -- every slide ultimately gets built through PptxGenJS. The assembler adds DeckContext awareness on top.

### What the Assembler Adds

| Capability | Existing pptx Skill | deck-assembler Adds |
|-----------|---------------------|---------------------|
| Slide creation | Ad hoc via conversation | Driven by SlideOutline contract |
| Palette application | Manual selection from 10 presets | Automatic from StyleGuide contract |
| Typography | Manual font pairing selection | Automatic from StyleGuide (heading_font, body_font, sizes) |
| Image placement | Manual positioning | Automatic from ImageManifest + layout templates |
| Chart placement | Not supported | Automatic from ChartManifest |
| Speaker notes | Not supported | Automatic from SpeakerNotes contract |
| Slide masters | No registration system | Programmatic `defineSlideMaster()` for all 12 types |
| Progressive builds | Not supported | Automatic from `build_animation` cues |
| Visual consistency | Design guidelines (not enforced) | Enforced via StyleGuide-driven parameters |

### Assembly Pipeline

The deck-assembler executes as a single Node.js script called via Claude Code's Bash tool:

```
node src/assemble_deck.js --deck-dir ./tmp/deck --output ./tmp/deck/output/presentation.pptx
```

**Internal pipeline:**

1. **Load contracts** -- Read and validate all five input JSON files
2. **Initialise PptxGenJS** -- Set theme, layout, and define all slide masters from StyleGuide
3. **Iterate slides** -- For each slide in the SlideOutline:
   a. Resolve layout template (from StyleGuide or defaults)
   b. Create slide with appropriate master
   c. Add headline text
   d. Add body content (body_points, stat numbers, quote text)
   e. Place images from ImageManifest (matched by slide_number)
   f. Place charts from ChartManifest (matched by slide_number)
   g. Handle progressive builds if `build_animation` cues present
   h. Add speaker notes from SpeakerNotes contract
4. **Write file** -- Export to `./tmp/deck/output/presentation.pptx` with compression

### DeckContext Awareness

The assembler reads from the DeckContext directory (`./tmp/deck/`) but does not write any contract files. Its sole output is the `.pptx` file in `./tmp/deck/output/`. The Deck Conductor updates `pipeline-state.json` with the assembler's completion status.

### Font Strategy (Research #10)

The assembler sets fonts from the StyleGuide's `typography` fields. PptxGenJS does not embed fonts -- font names are stored as string references in the PPTX XML (Research #10, Area 3). The recommended approach:

1. Use Google Font names from the StyleGuide (e.g., "Inter", "Montserrat + Open Sans")
2. Accept that machines without the specified font will use automatic substitution
3. All 10 recommended pairings from Research #10 use SIL Open Font License and are embeddable
4. If font embedding is critical, the `pptx-embed-fonts` npm package can be used as a post-processing step

### Typography Sizes (Research #10)

Default font sizes from the StyleGuide `typography` object, informed by Research #10:

| Element | StyleGuide Field | Default (pt) | Minimum (pt) |
|---------|-----------------|-------------|---------------|
| Title | `heading_sizes.title_slide` | 44 | 36 |
| Section divider | `heading_sizes.section_divider` | 44 | 36 |
| Slide heading | `heading_sizes.slide_heading` | 32 | 28 |
| Subheading | `heading_sizes.subheading` | 28 | 24 |
| Body text | `body_size` | 24 | 20 |
| Caption | `caption_size` | 18 | 16 |

### Error Handling

The assembler should be resilient to missing or incomplete upstream data:

| Condition | Behaviour |
|-----------|-----------|
| Missing image file (path in manifest but file not on disk) | Skip image, log warning |
| Image with `status: "failed"` | Skip entirely |
| No speaker notes for a slide | Slide created without notes |
| No images for a slide | Slide created with text content only |
| No charts for a slide | Slide created without chart |
| Missing layout template | Fall back to default template for the slide_type |
| Empty body_points | Slide created with headline only |

---

## Summary of Key Decisions

| Decision | Choice | Source |
|----------|--------|--------|
| PPTX engine | PptxGenJS v4.0.1 (Node.js) | Research #03 |
| Animation strategy | Progressive builds (multi-slide generation) | Research #14 |
| Chart embedding | Pre-rendered PNG via `addImage()`, not native charts | Research #02 |
| Image sizing | `contain` default, `cover` for backgrounds/heroes | Research #03 |
| Font strategy | Google Font names, no embedding by default | Research #10 |
| Slide dimensions | 10" x 5.625" (16:9), 0.5" margins | Research #01 |
| Coordinate units | Inches (PptxGenJS native) | Research #01 |
| Build trigger | `build_animation` cues in SpeakerNotes | Research #14 |
| File optimisation | Pre-compress images, strip EXIF, enable ZIP compression | Research #03 |
| Skill relationship | Wraps upstream `pptx` skill; adds DeckContext awareness | Research #02 |
