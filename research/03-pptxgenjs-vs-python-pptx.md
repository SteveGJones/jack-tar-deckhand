# PptxGenJS vs python-pptx Technology Decision

**Date:** 2026-03-29
**Context:** Jack-Tar Deckhand — Claude Code skills for conference-quality PowerPoint presentations
**Status:** The existing pptx skill uses PptxGenJS (JavaScript/Node.js). All image processing research assumed python-pptx (Python). This report provides the definitive technology comparison.

---

## Table of Contents

1. [PptxGenJS Feature Inventory](#1-pptxgenjs-feature-inventory)
2. [python-pptx Feature Inventory](#2-python-pptx-feature-inventory)
3. [Head-to-Head Feature Matrix](#3-head-to-head-feature-matrix)
4. [Ecosystem Advantages](#4-ecosystem-advantages)
5. [Performance Under Batch Generation](#5-performance-under-batch-generation)
6. [Aspose.Slides Commercial Evaluation](#6-asposeslides-commercial-evaluation)
7. [Architectural Recommendation](#7-architectural-recommendation)

---

## 1. PptxGenJS Feature Inventory

### Project Status

| Metric | Value |
|--------|-------|
| **Current Version** | 4.0.1 |
| **Last Release** | June 26, 2025 |
| **GitHub Stars** | ~4,900 |
| **Open Issues** | 217 |
| **License** | MIT |
| **Total Commits** | 3,463 |
| **Runtime** | Node.js, Browser, React, Vite, Electron |
| **Dependencies** | Zero runtime dependencies |
| **Output Format** | OOXML (.pptx) |
| **Compatibility** | PowerPoint, Keynote, LibreOffice Impress, Google Slides (via import) |

Source: [npm - pptxgenjs](https://www.npmjs.com/package/pptxgenjs), [GitHub - gitbrent/PptxGenJS](https://github.com/gitbrent/PptxGenJS)

### Core Object Types

- **Text**: Full rich text with font properties (face, size, bold, italic, color), alignment, bullet/numbering, line spacing, tab stops, subscript/superscript, underline styles, highlight, strikethrough, text direction, wrap, fit modes (`none` | `shrink` | `resize`)
- **Images**: PNG, JPG, GIF (including animated), SVG; from file path, URL, or base64; sizing modes (`contain` | `cover` | `crop`); transparency (0-100), rotation, flip H/V, rounding, shadows, alt text, hyperlinks
- **Shapes**: 180+ built-in PowerPoint shapes; solid fill with color and transparency; line/border with dash types and arrow endpoints; shadows (outer/inner with opacity, blur, angle, offset); rotation, flip
- **Tables**: Cell formatting (background, borders, fonts, padding); colspan/rowspan merging; auto-paging across slides with header repeat; bullet and word-level formatting in cells
- **Charts**: area, bar, bar3D, bubble, bubble3D, doughnut, line, pie, radar, scatter; combo/multi-type charts; extensive axis options, data labels, legends
- **Media**: Audio and video embedding; YouTube online video support; cover images for media

Source: [PptxGenJS API Docs](https://gitbrent.github.io/PptxGenJS/), [TypeScript Definitions](https://github.com/gitbrent/PptxGenJS/blob/master/types/index.d.ts)

### Slide Masters and Layouts

- `defineSlideMaster()` creates reusable layouts with background, objects (lines, rectangles, text, images), and placeholders
- Multiple masters can be defined and referenced by name in `addSlide()`
- Masters become first-class Layouts in the exported PowerPoint file
- Placeholder objects support named references for dynamic content insertion

Source: [PptxGenJS Masters and Placeholders](https://gitbrent.github.io/PptxGenJS/docs/masters/)

### Speaker Notes

- `slide.addNotes()` method adds speaker notes to any slide

Source: [PptxGenJS Speaker Notes](https://gitbrent.github.io/PptxGenJS/docs/speaker-notes.html)

### Theme Support

- `ThemeProps` interface supports `headFontFace` and `bodyFontFace` for presentation-level font defaults
- SchemeColor system with text1/text2, background1/background2, accent1-accent6

### Export Formats

- base64, Blob, Buffer, Node stream
- Browser download with proper MIME handling
- Compression options for production output

### Known Limitations (Unimplemented Features)

| Feature | Status |
|---------|--------|
| **Animations** | Not supported |
| **Transitions** | Not supported |
| **SmartArt** | Not supported |
| **Import/Edit Existing PPTX** | Not supported (not on roadmap) |
| **Outlines** | Not supported |
| **Gradient Fills on Shapes** | Not natively supported (workaround: gradient images as backgrounds) |
| **Group Shapes** | No GroupProps type found in TypeScript definitions |

Source: [GitHub - PptxGenJS](https://github.com/gitbrent/PptxGenJS), [PptxGenJS Issues](https://github.com/gitbrent/PptxGenJS/issues/712)

---

## 2. python-pptx Feature Inventory

### Project Status

| Metric | Value |
|--------|-------|
| **Current Version** | 1.0.0 (latest docs) / 0.6.22 (stable PyPI) |
| **Last Release** | Inactive since August 2024 |
| **GitHub Stars** | ~3,200 |
| **Forks** | 669 |
| **License** | MIT |
| **Maintainer** | Steve Canny (scanny) — **inactive** |
| **Runtime** | Python (any platform) |
| **Dependencies** | lxml, Pillow, XlsxWriter (optional) |

Source: [PyPI - python-pptx](https://pypi.org/project/python-pptx/), [GitHub - scanny/python-pptx](https://github.com/scanny/python-pptx), [Snyk Health Analysis](https://snyk.io/advisor/python/python-pptx)

### Core Features

- **Read/Write/Modify**: Can open, modify, and save existing .pptx files (PowerPoint 2007+)
- **Text**: Rich text with paragraph and run formatting, bullets, numbering
- **Images**: `add_picture()` and placeholder `insert_picture()` with picture fills on shapes
- **Shapes**: Auto shapes with solid fills, gradient fills (linear path), pattern fills, picture fills; line formatting; shadow effects
- **Tables**: Full table support with cell merging (merge origin, `span_height`/`span_width`), split, per-cell formatting (background, borders, margins)
- **Charts**: area, 3D area, bar, bubble, doughnut, line, pie, radar, scatter (XY); `ChartData`, `XyChartData`, `BubbleChartData` for different chart types
- **Placeholders**: Full placeholder inheritance system (master -> layout -> slide); picture, table, and chart placeholders with content insertion methods
- **Speaker Notes**: `notes_text_frame` property for reading/writing notes; auto-creates notes slide on first use

### Slide Layouts and Masters

- Full access to slide master/layout/slide hierarchy
- Placeholder inheritance with idx-based stable references
- All formatting properties (position, size, fill, line, font) inherited from parent placeholder
- Can use existing .pptx files as templates by loading and adding slides

Source: [python-pptx Working with Presentations](https://python-pptx.readthedocs.io/en/latest/user/presentations.html)

### Known Limitations

| Feature | Status |
|---------|--------|
| **Animations (shape-level)** | Not supported — no public API for entrance/exit/emphasis effects |
| **Slide Transitions** | Partial — can be added via XML but not reliably through API |
| **SmartArt** | Not supported — preserves existing SmartArt but cannot create |
| **Gradient Fills** | Linear path only; no radial or other gradient types |
| **Multi-plot Charts** | Cannot create, but can access existing multi-plot charts |
| **Copy Slides Between Presentations** | Not natively supported |
| **Link Color Changes** | Known limitation |
| **Maintenance** | Inactive — no new releases since August 2024 |

Source: [GitHub Issues #1106](https://github.com/scanny/python-pptx/issues/1106), [GitHub Issues #400](https://github.com/scanny/python-pptx/issues/400), [GitHub Issues #942](https://github.com/scanny/python-pptx/issues/942)

### python-pptx-ng Fork

| Metric | Value |
|--------|-------|
| **Version** | 0.7.0 |
| **Released** | January 17, 2024 |
| **Maintainer** | Martin Chrastek (Martin005) |
| **GitHub Stars** | 1 |
| **License** | MIT |

**Features added beyond python-pptx:**
- **GroupShape support**: `GroupShape` and `GroupShapes` classes; `SlideShapes.add_group_shape()` with recursive multi-level nesting
- **Freeform shapes**: `SlideShapes.build_freeform()` for custom path shapes (maps, etc.)
- **Video support**: `SlideShapes.add_movie()` for video media embedding
- **Patterned fills**: Pattern fill types on shapes
- **Dashed lines**: `LineFormat.dash_style` property
- **Hyperlink improvements**: Jump-to-named-slide behavior on shape and run hyperlinks
- **Performance**: Improved `Shapes._next_shape_id` efficiency for high shape-count slides

Source: [PyPI - python-pptx-ng](https://pypi.org/project/python-pptx-ng/), [Libraries.io - python-pptx-ng](https://libraries.io/pypi/python-pptx-ng)

### python-pptx-fix Fork

| Metric | Value |
|--------|-------|
| **Version** | 0.6.21.2 |
| **Maintainer** | Community |
| **Focus** | Bug fixes for the original python-pptx |

Notable fix: Potential install bug triggered by importing `__version__` from package `__init__.py` file.

Source: [PyPI - python-pptx-fix](https://pypi.org/project/python-pptx-fix/)

---

## 3. Head-to-Head Feature Matrix

| # | Feature | PptxGenJS | python-pptx | Notes |
|---|---------|-----------|-------------|-------|
| **Core** | | | | |
| 1 | Create new presentations | Yes | Yes | Both create from scratch |
| 2 | Open/modify existing .pptx | **No** | **Yes** | Major python-pptx advantage |
| 3 | Template support | Define masters only | Load any .pptx as template | python-pptx loads real templates |
| 4 | Output format | .pptx (OOXML) | .pptx (OOXML) | Both standards-compliant |
| 5 | Zero dependencies | **Yes** | No (lxml, Pillow) | PptxGenJS advantage |
| **Text** | | | | |
| 6 | Rich text formatting | Yes | Yes | Both full-featured |
| 7 | Bullets and numbering | Yes | Yes | PptxGenJS has more bullet options |
| 8 | RTL text | Yes | Limited | PptxGenJS explicitly supports |
| 9 | Asian fonts | Yes | Yes | Both support |
| 10 | Text fit/shrink | Yes (none/shrink/resize) | Via placeholders | PptxGenJS more explicit |
| 11 | Tab stops | Yes | Limited | |
| 12 | Subscript/Superscript | Yes | Yes | |
| 13 | Hyperlinks in text | Yes | Yes | |
| **Images** | | | | |
| 14 | PNG/JPG/GIF | Yes | Yes | Both full support |
| 15 | SVG | Yes (modern PowerPoint) | No native | PptxGenJS advantage |
| 16 | Animated GIF | Yes (Office 365) | No | PptxGenJS advantage |
| 17 | Base64 image data | Yes | Via BytesIO | PptxGenJS more direct |
| 18 | Image from URL | Yes | No (download first) | PptxGenJS advantage |
| 19 | Image sizing modes | contain/cover/crop | Manual calculation | PptxGenJS advantage |
| 20 | Image transparency | Yes (0-100) | Limited | PptxGenJS advantage |
| 21 | Image rotation | Yes (0-359) | Via XML | PptxGenJS advantage |
| 22 | Image flip H/V | Yes | No | PptxGenJS advantage |
| 23 | Image rounding (circle) | Yes | No | PptxGenJS advantage |
| 24 | Picture fill on shapes | No | Yes | python-pptx advantage |
| **Shapes** | | | | |
| 25 | Built-in shape types | 180+ | 180+ (via MSO_SHAPE) | Both comprehensive |
| 26 | Solid fill | Yes | Yes | |
| 27 | Gradient fill | **No** (use image workaround) | **Yes** (linear only) | python-pptx advantage |
| 28 | Pattern fill | No | Yes (via python-pptx-ng) | python-pptx-ng advantage |
| 29 | Shadows | Yes (outer/inner) | Yes (inherited) | Both support |
| 30 | Transparency | Yes (0-100%) | Yes | |
| 31 | Line/border styles | Yes (dash types, arrows) | Yes (dash style via -ng) | |
| 32 | Group shapes | **No** | **Yes** (via python-pptx-ng) | python-pptx-ng advantage |
| 33 | Freeform shapes | No | Yes (via python-pptx-ng) | python-pptx-ng advantage |
| 34 | Shape rotation | Yes | Via XML | PptxGenJS advantage |
| **Tables** | | | | |
| 35 | Basic tables | Yes | Yes | |
| 36 | Cell merge (colspan/rowspan) | Yes | Yes | Both support |
| 37 | Cell formatting | Yes | Yes | |
| 38 | Borders | Yes (including borderless) | Yes | |
| 39 | Auto-paging | **Yes** | No | PptxGenJS advantage |
| 40 | HTML table conversion | **Yes** (tableToSlides) | No | PptxGenJS advantage |
| **Charts** | | | | |
| 41 | Bar/Column | Yes | Yes | |
| 42 | Line | Yes | Yes | |
| 43 | Pie | Yes | Yes | |
| 44 | Scatter (XY) | Yes | Yes | |
| 45 | Area | Yes | Yes | |
| 46 | Doughnut | Yes | Yes | |
| 47 | Radar | Yes | Yes | |
| 48 | Bubble | Yes (including 3D) | Yes | |
| 49 | 3D Bar | Yes | Yes | |
| 50 | Combo/Multi-type | **Yes** | Read-only | PptxGenJS advantage |
| 51 | Chart data labels | Yes | Yes | |
| 52 | Axis formatting | Yes (extensive) | Yes | |
| **Media** | | | | |
| 53 | Video embedding | Yes | Yes (via -ng add_movie) | |
| 54 | Audio embedding | Yes | No | PptxGenJS advantage |
| 55 | YouTube embed | **Yes** | No | PptxGenJS advantage |
| **Slides & Layout** | | | | |
| 56 | Slide masters | Yes (defineSlideMaster) | Yes (full hierarchy) | python-pptx deeper access |
| 57 | Slide layouts | Yes | Yes (layout inheritance) | python-pptx more flexible |
| 58 | Placeholders | Yes (named) | Yes (idx-based, inherited) | python-pptx more robust |
| 59 | Speaker notes | Yes | Yes | |
| 60 | Slide numbering | Yes | Yes | |
| 61 | Custom slide size | Yes | Yes | |
| **Advanced** | | | | |
| 62 | Animations | **No** | **No** | Neither library supports |
| 63 | Slide transitions | **No** | **Partial** (via XML) | Neither reliable |
| 64 | SmartArt creation | **No** | **No** | Neither supports; Aspose.Slides only |
| 65 | SmartArt preservation | N/A (creation only) | Yes (preserves existing) | python-pptx advantage |
| 66 | Morph transitions | No | No | Aspose.Slides only |
| 67 | OLE objects | No | Partial | |
| 68 | VBA macros | No | Partial (preserves) | |
| **DevEx** | | | | |
| 69 | TypeScript definitions | **Yes** (built-in) | N/A | PptxGenJS advantage |
| 70 | Maintenance status | **Active** (v4.0.1, Jun 2025) | **Inactive** (since Aug 2024) | PptxGenJS advantage |
| 71 | Node.js native | **Yes** | No (needs Python runtime) | PptxGenJS advantage for Claude Code |
| 72 | Browser support | **Yes** | No | PptxGenJS advantage |
| 73 | Read existing files | No | **Yes** | python-pptx advantage |
| 74 | Companion template tool | pptx-automizer (Node.js) | Built-in | |
| 75 | Community ecosystem | Moderate (npm) | Large (Python/PyPI) | python-pptx more packages |

---

## 4. Ecosystem Advantages

### PptxGenJS Advantages

1. **Native to Claude Code**: Claude Code uses Node.js natively. PptxGenJS scripts run directly via `node script.js` with no environment setup
2. **Zero dependencies**: No package installation friction; single `npm install pptxgenjs`
3. **Already integrated**: The existing pptx skill (`generate-presentation`) already uses PptxGenJS — proven, working
4. **Active maintenance**: v4.0.1 released June 2025 with ongoing bug fixes and feature additions
5. **TypeScript support**: Full type definitions for IDE assistance and error prevention
6. **Browser + Server**: Same code works in Node.js, browsers, React, Electron
7. **Image handling**: Direct URL support, base64, sizing modes (`contain`/`cover`/`crop`) — purpose-built for presentation generation

### python-pptx Advantages

1. **Template ecosystem**: Can open, read, modify, and save existing .pptx files — essential for corporate templates
2. **Python image processing**: All image manipulation libraries are Python-native (Pillow, rembg, matplotlib, CairoSVG, pycairo, OpenCV)
3. **Gradient fills**: Native gradient fill support on shapes (linear path)
4. **Group shapes** (via -ng fork): Recursive multi-level group shape support
5. **Freeform shapes** (via -ng fork): Custom path shapes for maps and complex graphics
6. **Deeper PPTX access**: Full Open XML structure access for edge cases via `element` property
7. **Large ecosystem**: Extensive Python community with packages like pptx-template, compress-pptx, pptx-downsizer

### Can We Use Both? (Polyglot Pipeline)

**Yes. This is the recommended approach.**

The pattern is well-established in production systems:

```
[Python Image Pipeline]          [Node.js PPTX Assembly]
        |                                |
  Pillow, rembg,                   PptxGenJS
  matplotlib, CairoSVG       (slide composition)
  OpenCV, pycairo                    |
        |                            |
  /tmp/assets/*.png  -------->  slide.addImage({path: ...})
        |                            |
  Image processing              Final .pptx output
```

**Integration pattern in Claude Code:**
- Python scripts process images (background removal, chart rendering, SVG conversion, compositing)
- Images saved to `/tmp/presentation-assets/`
- Node.js script uses PptxGenJS to assemble the final presentation, referencing the processed images by file path
- Claude Code orchestrates both via Bash tool calls

**This is exactly what the existing `generate-presentation` skill already does** — it calls `python src/generate_image.py` for image generation, then builds slides with PptxGenJS.

Source: [Node.js child_process documentation](https://www.tutorialspoint.com/run-python-script-from-node-js-using-child-process-spawn-method), [FreeCodeCamp - Integrate Python with Node.js](https://www.freecodecamp.org/news/how-to-integrate-a-python-ruby-php-shell-script-with-node-js-using-child-process-spawn-e26ca3268a11/)

---

## 5. Performance Under Batch Generation

### PptxGenJS Performance

- **70+ demo slides** are generated successfully in the library's demonstration application
- **Image encoding** is the main bottleneck — pre-encoding images to base64 eliminates read/encode overhead
- **Generation speed**: "PowerPoint presentations are automatically generated in seconds"
- **No published benchmarks** for 25-40 slide decks with heavy image content, but the architecture (streaming ZIP assembly) scales linearly with slide count
- **Memory**: Node.js handles large buffers well; base64 images increase memory by ~33% over raw binary

Source: [ClearPeaks - PptxGenJS](https://www.clearpeaks.com/generating-powerpoint-presentations-automatically-with-pptxgenjs/)

### python-pptx Performance

- Mature ZIP-based output similar to PptxGenJS
- No significant performance differences for generation workloads
- **File size optimization**: Images typically account for 80-90% of PPTX file size
- Tools like `compress-pptx` can reduce file sizes by 30-70% via JPEG conversion (default quality 85)
- **Expected output**: A 20-slide deck with optimized images should be 3-8MB

Source: [PyPI - compress-pptx](https://pypi.org/project/compress-pptx/), [GitHub - pptx-downsizer](https://github.com/scholer/pptx-downsizer)

### Practical Estimate for 25-40 Slide Conference Decks

| Phase | Time Estimate | Bottleneck |
|-------|--------------|------------|
| Image generation (AI) | 2-8 min | Ollama model inference |
| Image processing (Python) | 10-30 sec | rembg + compositing |
| PPTX assembly (PptxGenJS) | 1-5 sec | Image encoding + ZIP |
| **Total** | **~3-9 min** | **Image generation dominates** |

PPTX assembly is never the bottleneck. Image generation and processing dominate total wall-clock time.

---

## 6. Aspose.Slides Commercial Evaluation

### Pricing (2026)

| License Type | Price (USD) | Scope |
|-------------|-------------|-------|
| Developer Small Business | $1,399 | 1 developer, 1 deployment location |
| Developer OEM | $4,197 | 1 developer, unlimited locations |
| Site Small Business | $6,995 | 10 developers, 10 locations |
| Site OEM | $19,586 | 10 developers, unlimited locations |

50% renewal discount available with auto-renewal. Paid support and consulting sold separately.

Source: [Aspose.Slides Pricing](https://purchase.aspose.com/pricing/slides/family/)

### Unique Capabilities (vs. Open Source)

| Feature | Aspose.Slides | PptxGenJS | python-pptx |
|---------|--------------|-----------|-------------|
| SmartArt creation/modification | **Yes** | No | No |
| Shape-level animations | **Yes** (entrance, exit, emphasis, motion paths) | No | No |
| Morph transitions | **Yes** (by object, word, character) | No | No |
| All slide transitions | **Yes** | No | Partial |
| Convert to PDF | **Yes** (high fidelity) | No | No |
| Convert to video (MP4) | **Yes** (with animations preserved) | No | No |
| Convert to HTML/Markdown/SVG | **Yes** | No | No |
| VBA macro manipulation | **Yes** | No | Preserve only |
| OLE object manipulation | **Yes** | No | Partial |
| Digital signatures | **Yes** | No | No |
| Encryption/Decryption | **Yes** | No | No |

Source: [Aspose.Slides Product Page](https://products.aspose.com/slides/), [Aspose Morph Transition Tutorial](https://tutorials.aspose.com/slides/python-net/animations-transitions/implement-morph-transitions-aspose-slides-python/), [Aspose SmartArt Guide](https://tutorials.aspose.com/slides/python-net/smart-art-diagrams/aspose-slides-python-smartart-presentation-guide/)

### Verdict on Aspose.Slides for This Project

**Not recommended for Jack-Tar Deckhand at this time.**

Rationale:
1. **Cost**: $1,399-$4,197 annually for a single developer is significant for a skill toolkit
2. **The features it uniquely provides (SmartArt, animations, morph transitions) are not critical for conference presentations** — conference talks rarely use complex animations, and SmartArt can be replaced with well-designed grouped shapes or diagrams
3. **PDF/video export** can be achieved via LibreOffice headless conversion (`soffice --headless --convert-to pdf`)
4. **Licensing complexity** adds friction for open-source distribution

**Revisit if**: The project requires reliable SmartArt creation, animation-heavy corporate training decks, or high-fidelity PDF export without LibreOffice dependency.

---

## 7. Architectural Recommendation

### Decision: Keep PptxGenJS + Build Python Image Pipeline

**Do NOT rebuild in python-pptx. Do NOT switch. Extend the current PptxGenJS architecture with Python helpers for image processing.**

### Rationale

| Factor | Decision Driver |
|--------|----------------|
| **Existing investment** | The pptx skill and generate-presentation skill already work with PptxGenJS |
| **Active maintenance** | PptxGenJS is actively maintained (v4.0.1, Jun 2025); python-pptx is dormant |
| **Claude Code native** | Node.js runs natively in Claude Code; Python requires separate process spawning |
| **Feature parity** | For creation-only workflows, PptxGenJS matches or exceeds python-pptx |
| **Image processing** | Python excels here — but images are pre-processed and passed as files, so language doesn't matter for PPTX assembly |
| **Template support** | PptxGenJS's `defineSlideMaster()` is sufficient; for importing corporate templates, consider pptx-automizer as a companion |
| **Zero dependencies** | PptxGenJS has no runtime dependencies — simpler, more reliable |

### Architecture

```
Claude Code Orchestrator (Skill: generate-presentation)
    |
    |--- [Step 1] Plan slides (Claude reasoning)
    |
    |--- [Step 2] Generate images (Python)
    |       |--- src/generate_image.py (Ollama/FLUX)
    |       |--- Image post-processing (Pillow, rembg, CairoSVG)
    |       |--- Chart rendering (matplotlib/seaborn)
    |       |--- Output: /tmp/presentation-assets/*.png
    |
    |--- [Step 3] Build PPTX (Node.js)
    |       |--- PptxGenJS script
    |       |--- References /tmp/presentation-assets/
    |       |--- Applies slide masters, layouts, themes
    |       |--- Output: final.pptx
    |
    |--- [Step 4] QA (Python + CLI)
            |--- markitdown for content verification
            |--- soffice -> pdftoppm for visual QA
```

### Action Items

1. **Keep**: PptxGenJS as the PPTX assembly engine (no change)
2. **Build**: Python image processing pipeline for:
   - Background removal (rembg with silueta model)
   - Image compositing (Pillow + pycairo)
   - Chart rendering (matplotlib with presentation-ready styling)
   - SVG-to-PNG conversion (CairoSVG)
   - Icon generation and processing
3. **Add**: pptx-automizer (Node.js) if corporate template import becomes a requirement
4. **Skip**: python-pptx migration — no benefit justifies the cost
5. **Skip**: Aspose.Slides — too expensive for the features needed
6. **Monitor**: python-pptx-ng fork for group shape and freeform shape features — if these become critical, consider a hybrid where python-pptx-ng handles specific advanced shape work while PptxGenJS remains the primary engine

### Risk Mitigation

| Risk | Mitigation |
|------|------------|
| PptxGenJS lacks gradient fills | Pre-render gradient images in Python, use as shape backgrounds |
| PptxGenJS lacks animations | Conference presentations rarely need animations; add manually in PowerPoint if essential |
| PptxGenJS can't import templates | Use pptx-automizer as a companion; or define masters programmatically |
| PptxGenJS lacks group shapes | Compose grouped elements as positioned shapes; or render complex groups as images |
| python-pptx goes fully unmaintained | Already mitigated — we don't depend on it for core functionality |

---

## Sources

### PptxGenJS
- [npm - pptxgenjs](https://www.npmjs.com/package/pptxgenjs)
- [GitHub - gitbrent/PptxGenJS](https://github.com/gitbrent/PptxGenJS)
- [PptxGenJS Documentation](https://gitbrent.github.io/PptxGenJS/)
- [PptxGenJS API - Images](https://gitbrent.github.io/PptxGenJS/docs/api-images.html)
- [PptxGenJS API - Charts](https://gitbrent.github.io/PptxGenJS/docs/api-charts/)
- [PptxGenJS API - Tables](https://gitbrent.github.io/PptxGenJS/docs/api-tables.html)
- [PptxGenJS Masters and Placeholders](https://gitbrent.github.io/PptxGenJS/docs/masters/)
- [PptxGenJS Speaker Notes](https://gitbrent.github.io/PptxGenJS/docs/speaker-notes.html)
- [PptxGenJS Shapes and Schemes](https://gitbrent.github.io/PptxGenJS/docs/shapes-and-schemes/)
- [PptxGenJS CHANGELOG](https://github.com/gitbrent/PptxGenJS/blob/master/CHANGELOG.md)
- [PptxGenJS TypeScript Definitions](https://github.com/gitbrent/PptxGenJS/blob/master/types/index.d.ts)
- [Anthropic Skills - pptxgenjs.md](https://github.com/anthropics/skills/blob/main/skills/pptx/pptxgenjs.md)
- [ClearPeaks - Generating PowerPoint with PptxGenJS](https://www.clearpeaks.com/generating-powerpoint-presentations-automatically-with-pptxgenjs/)

### python-pptx
- [PyPI - python-pptx](https://pypi.org/project/python-pptx/)
- [GitHub - scanny/python-pptx](https://github.com/scanny/python-pptx)
- [python-pptx Documentation](https://python-pptx.readthedocs.io/)
- [python-pptx Working with Charts](https://python-pptx.readthedocs.io/en/latest/user/charts.html)
- [python-pptx Working with Tables](https://python-pptx.readthedocs.io/en/latest/user/table.html)
- [python-pptx Gradient Fill](https://python-pptx.readthedocs.io/en/latest/dev/analysis/dml-gradient.html)
- [python-pptx Notes Slide](https://python-pptx.readthedocs.io/en/latest/user/notes.html)
- [python-pptx Working with Presentations](https://python-pptx.readthedocs.io/en/latest/user/presentations.html)
- [python-pptx Placeholders](https://python-pptx.readthedocs.io/en/latest/user/placeholders-using.html)
- [Snyk - python-pptx Health Analysis](https://snyk.io/advisor/python/python-pptx)
- [GitHub Issue #1106 - Animations](https://github.com/scanny/python-pptx/issues/1106)
- [GitHub Issue #400 - Animation Control](https://github.com/scanny/python-pptx/issues/400)

### python-pptx Forks
- [PyPI - python-pptx-ng](https://pypi.org/project/python-pptx-ng/)
- [Libraries.io - python-pptx-ng](https://libraries.io/pypi/python-pptx-ng)
- [PyPI - python-pptx-fix](https://pypi.org/project/python-pptx-fix/)

### Aspose.Slides
- [Aspose.Slides Product Page](https://products.aspose.com/slides/)
- [Aspose.Slides Pricing - Family](https://purchase.aspose.com/pricing/slides/family/)
- [Aspose.Slides SmartArt Management](https://docs.aspose.com/slides/python-net/manage-smartart-shape/)
- [Aspose.Slides Morph Transitions](https://tutorials.aspose.com/slides/python-net/animations-transitions/implement-morph-transitions-aspose-slides-python/)
- [Aspose.Slides PowerPoint Animation](https://docs.aspose.com/slides/python-net/powerpoint-animation/)
- [Aspose.Slides Convert to Video](https://docs.aspose.com/slides/python-net/convert-powerpoint-to-video/)
- [Aspose.Slides Slide Transitions](https://docs.aspose.com/slides/python-net/slide-transition/)

### Ecosystem & Integration
- [pptx-automizer (npm)](https://www.npmjs.com/package/pptx-automizer)
- [GitHub - singerla/pptx-automizer](https://github.com/singerla/pptx-automizer)
- [compress-pptx (PyPI)](https://pypi.org/project/compress-pptx/)
- [npm trends - pptx libraries](https://npmtrends.com/node-pptx-vs-officegen-vs-pptxgenjs-vs-viewerjs)
- [Top 7 Free PowerPoint APIs (2025)](https://blog.fileformat.com/presentation/top-7-free-and-open-source-powerpoint-apis-&-libraries-for-developers/)
- [Node.js child_process - Run Python](https://www.tutorialspoint.com/run-python-script-from-node-js-using-child-process-spawn-method)
