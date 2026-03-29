# Presentation engineering pipeline: the complete image toolchain

**The non-model image layer for AI-generated presentations is a rich but fragmented ecosystem of 100+ open-source tools, 44+ MCP servers/skills, and proven integration patterns — all viable on CPU-only Linux containers.** The most critical finding: a production-grade pipeline requires just **8-10 core libraries** (Pillow, pycairo, CairoSVG, rembg, python-pptx, matplotlib, Graphviz, Playwright, DiskCache, and an icon set like Lucide) forming a ~600 MB install footprint. Everything else is enhancement. This report catalogues every relevant tool, evaluates them on 10 dimensions, and provides a modular architecture with priority tiers for the Claude Skill library.

---

## Part 1: Community skills and MCP servers are booming

The MCP ecosystem for presentations and image work has exploded, with **44+ publicly discoverable servers and skills** across presentation creation, image generation, SVG manipulation, and diagramming. The landscape is dominated by small, single-author projects, but several stand out for production use.

### Presentation MCP servers

The most mature presentation servers are **GongRzhe/Office-PowerPoint-MCP-Server** (32+ tools across 11 modules, 25+ professional templates, 4 color schemes, installable via `uvx`) and **supercurses/powerpoint** (~145 stars, MIT, TogetherAI FLUX integration for slide images). The commercial **Plus AI MCP** (SOC 2 Type II, native PPTX/Google Slides, custom templates) represents the enterprise tier. **Deckrun-MCP** uniquely outputs presentation PDFs, narrated MP4 videos, and MP3 audio from Markdown.

On Smithery.ai, **daymade/ppt-creator** is the most complete agent skill — it generates structured content with Pyramid Principle storytelling, produces both Marp/Reveal.js HTML and python-pptx PPTX output, and renders chart PNGs via matplotlib. This is the closest existing analog to what the team is building.

### Image and SVG MCP servers

For image generation, **shinpr/mcp-image** stands out with automatic prompt optimization and a standalone SKILL.md that teaches any AI to write better image prompts — usable without MCP infrastructure. **GenWaveLLC/svgmaker-mcp** provides AI-powered SVG generation, editing, and image-to-SVG conversion. **agentic-ph/icon-mcp** aggregates search across 7+ icon libraries (Bootstrap, Feather, Heroicons, Lucide, Tabler) with fuzzy matching and caching.

### Diagram MCP servers

**antoinebou12/uml-mcp** is the most comprehensive diagram server, supporting **30+ diagram types** via PlantUML, Mermaid, Kroki, D2, Graphviz, TikZ, ERD, BlockDiag, BPMN, and C4 — with intelligent fallback between backends and SVG/PNG/PDF output. **andrewmoshu/diagram-mcp-server** handles multi-cloud infrastructure diagrams (AWS, GCP, Azure, K8s) with 2,000+ icons and auto .drawio export.

### Complete MCP/Skills catalogue

| Project | Type | URL | Stars | License | Relevance | Key Capability |
|---------|------|-----|-------|---------|-----------|----------------|
| GongRzhe/Office-PowerPoint-MCP-Server | MCP | github.com/GongRzhe/Office-PowerPoint-MCP-Server | High | MIT | **High** | 32+ PPTX tools, templates, themes |
| supercurses/powerpoint | MCP | github.com/supercurses/powerpoint | ~145 | MIT | **High** | PPTX + AI image gen |
| daymade/ppt-creator | Skill | smithery.ai/skills/daymade/ppt-creator | — | — | **High** | End-to-end slide pipeline |
| antoinebou12/uml-mcp | MCP | github.com/antoinebou12/uml-mcp | — | — | **High** | 30+ diagram types, multi-backend |
| andrewmoshu/diagram-mcp-server | MCP | github.com/andrewmoshu/diagram-mcp-server | — | — | **High** | Multi-cloud infra diagrams |
| shinpr/mcp-image | MCP+Skill | github.com/shinpr/mcp-image | — | — | **High** | Prompt optimization + Gemini |
| GenWaveLLC/svgmaker-mcp | MCP | github.com/GenWaveLLC/svgmaker-mcp | — | — | **High** | AI SVG gen/edit/convert |
| lgazo/drawio-mcp-server | MCP | github.com/lgazo/drawio-mcp-server | — | — | **High** | Draw.io diagram creation |
| Plus AI MCP | MCP | plusai.com/features/mcp | — | Commercial | **High** | Enterprise PPTX + Slides |
| agenticdecks/deckrun-mcp | MCP | github.com/agenticdecks/deckrun-mcp | — | — | **High** | PDF/video/audio from MD |
| ltc6539/mcp-ppt | MCP | github.com/ltc6539/mcp-ppt | — | — | **High** | PPTX + inline SVG gen |
| 2slides/mcp-2slides | MCP | github.com/2slides/mcp-2slides | — | — | Medium | Cloud-based, themes, 20+ langs |
| agentic-ph/icon-mcp | MCP | github.com/agentic-ph/icon-mcp | — | — | Medium | Multi-library icon search |
| GongRzhe/Image-Generation-MCP-Server | MCP | github.com/GongRzhe/Image-Generation-MCP-Server | — | — | Medium | Replicate Flux image gen |
| Ichigo3766/powerpoint-mcp | MCP | github.com/Ichigo3766/powerpoint-mcp | — | MIT | Medium | PPTX + local SD image gen |
| lansespirit/image-gen-mcp | MCP | github.com/lansespirit/image-gen-mcp | — | MIT | Medium | Multi-provider (OpenAI, Imagen) |
| matteoantoci/google-slides-mcp | MCP | github.com/matteoantoci/google-slides-mcp | — | — | Medium | Google Slides API |
| dvejsada/mcp-pptx-presentations-creator | MCP | github.com/dvejsada/mcp-pptx-presentations-creator | — | — | Medium | SSE transport, Docker |
| angrysky56/mcp-diagram-server | MCP | github.com/angrysky56/mcp-diagram-server | — | — | Medium | Mermaid + format conversion |
| awkoy/replicate-flux-mcp | MCP | github.com/awkoy/replicate-flux-mcp | — | — | Medium | Raster + SVG via Replicate |

### Transferable patterns from GPT/agent ecosystems

Research across OpenAI GPTs, LangChain, AutoGen, and CrewAI revealed **10 reusable design patterns** directly applicable to Claude Skills:

- **Content-design separation**: All successful tools separate AI content generation from visual rendering. Claude generates structured JSON (titles, body text, image descriptions); a rendering engine produces the PPTX.
- **String-reference asset management**: Binary images never flow through the LLM. Use file paths, UUIDs, or storage keys as references — matching LangChain's `image_storage` dict and OpenAI's `file_id` annotation patterns.
- **Iterative critique loops**: AutoGen's generator-critic conversation pattern — one agent creates images, another evaluates and requests refinements until quality passes or max retries hit.
- **Typed slide data models**: CopilotKit's `SlideModel` interface (`title`, `content`, `backgroundImageDescription`, `spokenNarration`) shows that each slide field maps to a distinct generation step.
- **ToolSpec bundles**: LlamaIndex and CrewAI both group related tools (generate + vary + display). Skills should offer cohesive tool families, not isolated functions.

The **Gamma API** pattern is particularly instructive: POST generation request → receive ID → poll until complete → get hosted URL + PPTX export. This async generation model is the standard for operations exceeding 5 seconds.

---

## Part 2A: Core image processing libraries — the evaluated stack

### General-purpose image processing

**Pillow 12.1.1 scores a perfect 5.0/5.0** across all 10 evaluation dimensions. It is the unambiguous foundation: **~7 MB install**, zero heavy dependencies, native alpha compositing, full format support (PNG, JPEG, WebP, TIFF, GIF), and excellent resize/crop capabilities including LANCZOS interpolation. For performance-critical batch operations, **opencv-python-headless 4.13.0** (Apache 2.0, ~86.8K GitHub stars) provides 2-5× speed improvements over Pillow for resize and color conversion, though its BGR-default color ordering and numpy-centric API add friction. **Pillow-SIMD** is a drop-in replacement offering **4-6× faster** resize/blur/composite on x86 with AVX2 — install via `CC="cc -mavx2" pip install pillow-simd`.

| Library | Version | License | Install Size | Avg Score | Best For |
|---------|---------|---------|-------------|-----------|----------|
| **Pillow** | 12.1.1 | HPND | ~7 MB | **5.0** | Everything — core foundation |
| OpenCV (headless) | 4.13.0 | Apache-2.0 | ~50 MB | 4.5 | Batch performance, 200+ color conversions |
| scikit-image | 0.26.0 | BSD-3 | ~100 MB chain | 4.4 | Scientific processing (niche) |
| Wand (ImageMagick) | 0.7.0 | MIT | ~100 MB sys | 3.6 | **SVG rasterization** (⚠️ MAINTENANCE RISK) |
| imageio | 2.37.0 | BSD-2 | ~2 MB | 4.1 | I/O abstraction layer |

### Background removal

**rembg 2.0.74 is the clear winner** for CPU-only background removal, scoring 4.4/5.0. Critically, it uses **ONNX Runtime** (not PyTorch), making it ~1 GB lighter than PyTorch-based alternatives. The `silueta` model (43 MB) offers the best size-quality tradeoff, processing images in **~2-5 seconds on CPU**. Install via `pip install "rembg[cpu]"` for a total footprint of ~400 MB including onnxruntime and model.

**transparent-background** (MIT, PyTorch-based) produces slightly better edge quality in some cases but requires **~1.5 GB** of PyTorch CPU dependencies — a dealbreaker for lean containers. **MODNet** has a fatal **CC BY-NC-SA 4.0 license** (non-commercial only), no PyPI package, and works only on portraits.

### Color manipulation

For palette extraction, **colorthief** (MIT, ~10 KB, zero deps beyond Pillow) provides dominant color and palette extraction via median cut. For professional color science — brand color matching via delta-E calculations, WCAG contrast compliance, color space conversions — **colour-science 0.4.7** (BSD-3, 2.2K stars) is the most comprehensive option with 50+ color spaces and CIE delta-E 2000 support. **wcag-contrast-ratio** (MIT, ~2 KB) handles WCAG 2.0 AA/AAA pass/fail checks in a single function.

### Image upscaling verdict

**Real-ESRGAN is NOT viable on CPU** — confirmed by multiple GitHub issues reporting 30-120 seconds per 512×512 image. The `--fp32` flag is mandatory (no half precision on CPU), and the ~1.5 GB PyTorch dependency is excessive. **Classical Lanczos interpolation** via `PIL.Image.resize(size, Image.LANCZOS)` or `cv2.resize(img, size, interpolation=cv2.INTER_LANCZOS4)` processes images in **microseconds** and produces excellent quality for 1.5-2× upscaling. For 4× upscaling, pair Lanczos with an unsharp mask filter. For AI upscaling, **delegate to external APIs** (Replicate, fal.ai) rather than running locally.

### Compositing for professional slide graphics

Three libraries serve distinct compositing needs:

**Pillow** handles basic compositing (`alpha_composite()`, `paste()` with masks, `ImageDraw` shapes) with zero additional dependencies. **pycairo 1.29.0** (LGPL-2.1/MPL-1.1) adds professional-grade vector capabilities: native **rounded rectangles**, linear/radial **gradients**, alpha masking, clipping paths, and text-to-path conversion — critical for polished slide backgrounds and decorative elements. Requires `apt install libcairo2-dev`. **skia-python 144.0** (BSD-3, Chrome/Android's rendering engine) is the most powerful option with drop shadows via SkMaskFilter, blur effects, layer management, and PDF output — but has sparse Python-specific documentation and requires OpenGL/EGL system libraries.

---

## Part 2B: Vector graphics, icons, diagrams, and charts

### SVG tools pipeline

The recommended SVG pipeline chains three tools: **drawsvg** (MIT, actively maintained) for programmatic SVG creation → **SVGO 4.0.1** (MIT, npm, 30+ optimization plugins) for minification → **CairoSVG 2.9.0** (LGPL-3, `apt install python3-cairosvg`) for SVG-to-PNG rasterization with configurable DPI. CairoSVG is the most battle-tested SVG rasterizer with both CLI and Python API. **svgwrite 1.4.3** is a lighter alternative for SVG creation but is in maintenance-only mode.

### Icon libraries for presentations

| Library | Icons | License | SVG? | Best Access Method |
|---------|-------|---------|------|-------------------|
| **Iconify** | **275,000+** | MIT (framework) | ✅ | `@iconify/json` npm (~200 MB offline JSON) |
| Phosphor | ~9,000 | MIT | ✅ | 6 weight variants, `@phosphor-icons/core` |
| Tabler Icons | ~5,700 | MIT | ✅ | `@tabler/icons` npm |
| Material Design | ~7,000 | Apache-2.0 | ✅ | `@mdi/svg` npm |
| Bootstrap Icons | ~2,000 | MIT | ✅ | `bootstrap-icons` npm |
| **Lucide** | ~1,694 | ISC | ✅ | `lucide-py` on PyPI (!) |
| Heroicons | ~316 | MIT | ✅ | Raw SVG download |
| Feather | ~287 | MIT | ✅ | `feather-icons` npm |

**Lucide** is the recommended primary set — clean, consistent line icons with an actual **Python package** (`lucide-py`), ISC license, and active maintenance. For breadth, **Iconify** aggregates 200+ icon sets into a single offline JSON package. The practical approach: download SVG files into a local directory during container build, then manipulate with lxml or string operations at runtime.

### Diagram generation without a GPU

**Graphviz** (EPL engine, MIT Python binding, `apt install graphviz`) remains the most reliable headless diagram tool — native apt package, sub-second rendering, and the **mingrammer/diagrams** Python library (MIT, 0.25.1) wraps it with 2,000+ pre-built cloud provider icons for architecture diagrams.

**D2** is the compelling modern alternative: a **single Go binary** with zero JVM/browser dependencies, installable via `curl -fsSL https://d2lang.com/install.sh | sh`. It produces beautiful SVG/PNG/PDF output with built-in themes and multiple layout engines (dagre, ELK, TALA).

**Mermaid CLI cannot run without a browser** — it requires Puppeteer launching headless Chromium (~2-3 second cold start per diagram). Accept this dependency or route through **Kroki**, which wraps 27+ diagram formats (including Mermaid, PlantUML, Graphviz, D2, Excalidraw) behind a unified HTTP API. Self-host via `docker run -p 8000:8000 yuzutech/kroki` or use the free public API at kroki.io.

### Charts that look professional, not academic

**matplotlib 3.10** + **seaborn 0.13** is the gold standard for headless chart rendering. The `Agg` backend requires **zero display server** — ideal for containers. Corporate styling is achievable via `.mplstyle` files controlling every visual parameter (font families, brand colors, title sizes, grid styles). The built-in `presentation` context preset upscales fonts for readability.

For declarative chart specification, **Altair 5.x** with **vl-convert-python** provides truly headless PNG/SVG/PDF export via a native binary — no browser needed. **Plotly 6.x** produces the most interactive-looking static charts but now requires Chromium via Kaleido v1 for static export.

**pygal 3.1.0** (LGPL-3) is an underrated option producing native SVG charts with attractive built-in styles (Neon, Clean, DarkSolarized) and zero external dependencies for SVG output.

---

## Part 2C: Typography that doesn't look like a script wrote it

Text rendering quality is the difference between "AI-generated" and "professionally designed" slides. The libraries span a dramatic quality range.

**Pillow's ImageDraw.text()** is adequate for watermarks and simple labels but has no automatic text wrapping, broken complex script rendering, and no kerning/ligature support without the optional Raqm engine. **Not recommended as primary text renderer** for professional output.

**Pango + Cairo (via PyGObject)** delivers **production-grade, browser-quality text layout** — the same engine powering GNOME/GTK. It provides automatic line wrapping, justification, bidirectional text, complex script rendering, HarfBuzz shaping, and font fallback. Install via `apt install gir1.2-pango-1.0 gir1.2-pangocairo-1.0 python3-gi python3-gi-cairo`.

**Playwright** (Apache-2.0, Microsoft) produces the **highest-fidelity text rendering** possible by leveraging a full browser engine. Use `page.set_content()` to render HTML/CSS strings, then `page.screenshot()` to capture. Full CSS typography: web fonts, flexbox layout, shadows, gradients. This is the approach used by commercial slide tools like Marp and Slidev for their PPTX export.

| Renderer | Quality | Auto-wrap | Complex Scripts | Install Overhead |
|----------|---------|-----------|-----------------|-----------------|
| Pillow | ⭐⭐½ | Manual | ❌ | ~7 MB |
| pycairo (toy API) | ⭐⭐⭐ | ❌ | ❌ | ~5 MB sys |
| **Pango + Cairo** | ⭐⭐⭐⭐⭐ | ✅ | ✅ | ~20 MB sys |
| skia-python | ⭐⭐⭐⭐ | ❌ | Via HarfBuzz | ~27 MB |
| **Playwright** | ⭐⭐⭐⭐⭐ | ✅ | ✅ | ~200 MB (Chromium) |

### Font management in containers

**Google Fonts API** (`googleapis.com/webfonts/v1/webfonts?key=KEY`) returns direct `.ttf` download URLs for all 1,600+ fonts. For containers, the recommended approach: selectively download 5-10 presentation fonts during build and run `fc-cache -fv`. Quick installs via apt: `apt install fonts-open-sans fonts-roboto fonts-lato fonts-inter fonts-noto`.

**Recommended font pairings** for professional slides: **Montserrat + Open Sans** (modern, business), **Playfair Display + Source Sans Pro** (elegant, creative), **Poppins + Roboto** (startup, clean), or **Inter** alone across multiple weights (minimalist, versatile). **fonttools** (MIT, 4.62.1) handles font subsetting (`pyftsubset`) to reduce embedded font sizes.

---

## Part 2D: PPTX generation — python-pptx and beyond

### The python-pptx landscape

**python-pptx 1.0.2** (MIT, `pip install python-pptx`) remains the foundation — covering ~70% of professional PPTX generation needs: slides, shapes, text boxes, tables, images, charts (bar/column/line/pie), placeholders, slide layouts, masters, gradient fills, shadows, and backgrounds. Dependencies are minimal: lxml, Pillow, XlsxWriter.

Its critical limitations: **no animations/transitions**, no SmartArt, no video/audio embedding, no native PDF export, and — notably — the **original maintainer is largely inactive** with issues accumulating since 2025. The **python-pptx-ng** fork (MIT, 0.7.0) addresses several bugs including OLE object embedding, security fixes, and proper line-break encoding. **python-pptx-interface** (MIT) adds a higher-level API with stylesheet classes and positioning helpers.

**Aspose.Slides for Python** (proprietary, ~$1K+ license) is the only option reaching **~95% feature completeness** — animations, transitions, SmartArt, media embedding, VBA macros, password protection, and built-in PDF export without LibreOffice. The evaluation version adds watermarks.

### Markdown-to-PPTX pathways

**Pandoc** (`apt install pandoc`, GPL-2.0) converts Markdown to editable PPTX via `pandoc input.md -t pptx -o output.pptx`, supporting custom templates via `--reference-doc`. Only 4 slide layouts are supported. **Marp CLI** (`npm install -g @marp-team/marp-cli`, MIT) produces image-based PPTX from Markdown — text is not editable but visual quality is high. **md2pptx** (MIT) is a Python-native alternative with Graphviz diagram support.

### Format conversion

**LibreOffice headless** is the standard PPTX→PDF conversion path: `libreoffice --headless --convert-to pdf file.pptx`. Quality is ~85% fidelity — install metrically-compatible fonts (`apt install fonts-crosextra-carlito fonts-crosextra-caladea fonts-noto`) to minimize spacing drift. **pdf2image** (MIT, requires `apt install poppler-utils`) then converts PDF pages to PIL Images at configurable DPI for thumbnails.

### The design intelligence gap

**No mature open-source "design rules engine" or automatic slide layout algorithm exists.** Beautiful.ai's "Smart Slides" (300+ intelligent layouts) is the closest commercial reference, but it's proprietary. This is the single largest capability gap in the open-source presentation toolchain. A Claude Skill implementing basic design heuristics (alignment grids, whitespace rules, visual hierarchy) would be a significant contribution.

---

## Part 2E and Part 3: Pipeline architecture for production

### Caching strategy

**DiskCache 5.6.3** (Apache 2.0, pure Python, SQLite-backed) is the recommended caching layer — thread-safe, process-safe, with LRU/LFU eviction, tag-based management, and cache stampede protection. Pair with **HashFS 0.7.2** (MIT) for content-addressable image storage with automatic deduplication. The two-layer pattern: hash generation parameters → DiskCache lookup → HashFS retrieval.

```
Cache key = SHA256(prompt + dimensions + style + model_version)
L1: In-memory LRU (functools.lru_cache) for hot images
L2: DiskCache with 1GB size limit and TTL eviction  
L3: HashFS for permanent content-addressable storage
```

### Quality gates

**pyiqa 0.1.13** (Apache 2.0, PyTorch-based, 40+ metrics) provides automated quality scoring. For CPU-only pipelines, use lightweight metrics: **BRISQUE** (no-reference, fast) with scores <40 indicating good quality, and **PSNR/SSIM** (full-reference, very fast) for processing verification. For visual regression testing, **pixelmatch** (ISC, pure Python, ~255K monthly downloads) compares generated images pixel-by-pixel with anti-aliasing detection.

### Image optimization for PPTX embedding

Three system tools handle file size optimization before embedding:

- **pngquant**: `apt install pngquant` — lossy PNG compression with **60-80% size reduction**
- **cwebp**: `apt install webp` — WebP conversion for modern format support
- **mozjpeg**: build from source (no apt package) — 3-5% better JPEG compression than jpegoptim
- **piexif** (MIT, pure Python): strip EXIF metadata for privacy with `piexif.remove(image_bytes)`

### Recommended pipeline architecture

```
┌─ Generate ─┐   ┌─ Process ──┐   ┌─ Composite ┐   ┌─ Optimize ─┐   ┌── Embed ──┐
│ AI API or  │──▶│ resize,    │──▶│ overlay,   │──▶│ pngquant,  │──▶│ insert    │
│ chart/diag │   │ crop,      │   │ blend,     │   │ strip EXIF │   │ into PPTX │
│ rendering  │   │ remove bg  │   │ text, icon │   │            │   │           │
└────────────┘   └────────────┘   └────────────┘   └────────────┘   └───────────┘
      │                │                │                │                │
      └────────────────┴────────────────┴────────────────┴────────────────┘
                  Quality Gate (pyiqa BRISQUE < 40 or pixelmatch < 5%)
                  Cache Layer (DiskCache + HashFS by parameter hash)
```

The pipeline follows a **sequential-with-gates** pattern. Each step receives and returns a PIL Image or file path. If a quality gate fails, the pipeline either retries with modified parameters or falls back through a degradation chain: AI-generated → stock lookup → solid color with text → skip element.

For batch processing across slides, use **ProcessPoolExecutor** with file-path passing (not image data) to minimize inter-process transfer. Benchmarks show **~5-6× speedup** on 8-core CPUs for independent image operations.

---

## Recommended skill library architecture

### P0 — Foundation (must-have, build first)

| Skill | Core Libraries | Purpose |
|-------|---------------|---------|
| **Image Processor** | Pillow, Pillow-SIMD | Resize, crop, format convert, alpha channel, basic compositing |
| **PPTX Generator** | python-pptx (or -ng) | Slide creation, layout, text, shapes, tables, charts |
| **Background Remover** | rembg[cpu] | Remove backgrounds from photos for slide composition |
| **Chart Renderer** | matplotlib, seaborn | Professional data visualizations at 300 DPI |
| **SVG Rasterizer** | CairoSVG, drawsvg | SVG creation and SVG→PNG conversion |
| **Asset Cache** | DiskCache, HashFS | Content-addressable caching with deduplication |

### P1 — Enhancement (high value, build second)

| Skill | Core Libraries | Purpose |
|-------|---------------|---------|
| **Diagram Generator** | Graphviz, D2, mingrammer/diagrams | Architecture, flow, and org chart diagrams |
| **Icon Manager** | Lucide (lucide-py), Iconify JSON | Search, retrieve, and customize SVG icons |
| **Text Renderer** | Pango+Cairo or Playwright | Professional text-on-image with web fonts |
| **Color Intelligence** | colorthief, colour-science, wcag-contrast-ratio | Palette extraction, brand matching, accessibility |
| **PDF Exporter** | LibreOffice headless, pdf2image | PPTX→PDF→thumbnails pipeline |

### P2 — Advanced (targeted capabilities)

| Skill | Core Libraries | Purpose |
|-------|---------------|---------|
| **Slide Compositor** | pycairo or skia-python | Gradients, rounded corners, shadows, masking |
| **Mermaid Renderer** | Mermaid CLI (+ Chromium) or Kroki | Flowcharts, sequence, Gantt, ER from text |
| **Image Optimizer** | pngquant, cwebp, piexif | File size optimization and metadata stripping |
| **Quality Gate** | pyiqa (BRISQUE), pixelmatch | Automated image quality scoring and diff testing |
| **Font Manager** | fonttools, Google Fonts API | Font download, installation, subsetting |

### P3 — Experimental (explore when core is stable)

| Skill | Core Libraries | Purpose |
|-------|---------------|---------|
| **HTML Slide Renderer** | Playwright | HTML/CSS→image for complex layouts |
| **Template Engine** | pptx-template, Jinja2 | Data-driven template filling |
| **Design Linter** | Custom rules engine | Automated design quality checks |
| **Declarative Charts** | Altair + vl-convert | Vega-Lite specification → static charts |
| **PlantUML/Kroki** | Kroki Docker, PlantUML | 27+ diagram formats via unified API |

---

## Capability gap analysis

### Critical gaps with no open-source solution

- **Automatic slide layout intelligence**: No open-source equivalent to Beautiful.ai's smart layout. The team should build design heuristics (grid alignment, whitespace rules, visual hierarchy scoring) as a custom skill.
- **PPTX animations and transitions**: python-pptx cannot create these. Only Aspose.Slides (commercial) supports them. Workaround: use LibreOffice headless to apply transitions from a template.
- **SmartArt generation**: No open-source tool creates SmartArt programmatically. Build equivalent layouts using shapes and connectors in python-pptx.
- **AI image upscaling on CPU**: Real-ESRGAN and all neural upscalers are impractically slow on CPU. Must delegate to external APIs or accept Lanczos quality.

### GPU-dependent tools with no viable CPU alternative

| Tool | GPU Task | CPU Status | Recommendation |
|------|----------|------------|----------------|
| Real-ESRGAN | 4× image upscaling | 30-120s per image | Delegate to Replicate/fal.ai API |
| SwinIR/BSRGAN | Super-resolution | Similar CPU penalty | Use Lanczos or external API |
| SAM (Segment Anything) | Fine segmentation | Extremely slow | Use rembg (ONNX) instead |
| Stable Diffusion | Image generation | Not feasible | Cloud APIs only |

### Commercial-only capabilities

| Capability | Tool | Cost | Open-Source Status |
|------------|------|------|--------------------|
| Full PPTX features (animations, SmartArt, media) | Aspose.Slides | ~$1K+ | No equivalent |
| Professional auto-layout | Beautiful.ai | $12+/mo | No equivalent |
| Stock photo integration | Shutterstock/Getty API | Per-image | Unsplash API (limited free) |
| Enterprise SVG generation | SVGMaker.io | API credits | drawsvg + manual design |

---

## Dependency health report

### Healthy and actively maintained (low risk)

| Library | Stars | Last Release | Maintainers | License | Python Compat |
|---------|-------|-------------|-------------|---------|--------------|
| Pillow | 12.5K | Feb 2026 | 5+ core | HPND | 3.9-3.13 |
| OpenCV | 86.8K | Feb 2026 | 20+ | Apache-2.0 | 3.8-3.13 |
| matplotlib | 20K+ | 2026 | 10+ | BSD | 3.10+ |
| python-pptx | 2.3K | 2024 | 1 (⚠️) | MIT | 3.8+ |
| rembg | 17K | 2025 | 1 | MIT | 3.8+ |
| pycairo | 657 | 2026 | 3 | LGPL/MPL | 3.9+ |
| DiskCache | 2.4K | 2024 | 1 | Apache-2.0 | 3.7+ |
| CairoSVG | 2.2K | 2025 | 3 | LGPL-3.0 | 3.7+ |
| Graphviz (Python) | 1.7K | 2024 | 1 | MIT | 3.8+ |
| skia-python | 278 | Mar 2026 | 2 | BSD-3 | 3.9+ |

### Maintenance risk flags (12+ months without release)

| Library | Last Activity | Risk | Mitigation |
|---------|--------------|------|------------|
| **Wand** (ImageMagick) | Marked "Inactive" by Snyk | ⚠️ HIGH | Use CairoSVG for SVG, Pillow for raster |
| **colorthief** | No updates in years | ⚠️ MEDIUM | Stable API, unlikely to break; tiny codebase |
| **officegen** (Node.js) | Years inactive | ⚠️ HIGH | Use PptxGenJS instead |
| **palettable** | 2023 | ⚠️ LOW | Stable palette data, no breaking changes expected |

### License compatibility matrix

| License | Libraries | Commercial Use | Copyleft Risk |
|---------|-----------|---------------|--------------|
| MIT | python-pptx, rembg, Lucide, drawsvg, DiskCache, SVGO, fonttools, Marp | ✅ Free | None |
| BSD | OpenCV, matplotlib, seaborn, Altair, scikit-image, skia-python | ✅ Free | None |
| Apache-2.0 | pyiqa, albumentations, Google Fonts, HashFS | ✅ Free | None |
| HPND | Pillow | ✅ Free | None |
| ISC | pixelmatch, Lucide icons | ✅ Free | None |
| LGPL-2.1/3.0 | pycairo, CairoSVG, pygal | ✅ (dynamic link) | Weak copyleft — OK for Python imports |
| MPL-2.0 | D2, pycairo alt | ✅ Free | File-level copyleft only |
| GPL-2.0 | Pandoc, PlantUML (code) | ⚠️ Caution | Output is not GPL-encumbered; tool use is fine |
| **CC BY-NC-SA 4.0** | MODNet | ❌ No commercial | **Do not use** |
| Proprietary | Aspose.Slides | Paid license | Evaluate ROI |

---

## Integration cookbook: top 10 patterns

### 1. Background removal → slide composition

```python
from rembg import remove
from PIL import Image
import io

# Remove background (CPU, ~3s)
input_img = Image.open("photo.jpg")
output_img = remove(input_img, model_name="silueta")  # 43MB model

# Composite onto slide background
slide_bg = Image.new("RGBA", (1920, 1080), "#1a1a2e")
output_img = output_img.resize((600, 800), Image.LANCZOS)
slide_bg.paste(output_img, (100, 140), output_img)  # Alpha mask
slide_bg.save("slide_image.png")
# ⚠️ Common pitfall: rembg returns RGBA — always use alpha channel as paste mask
```

### 2. Professional chart → PPTX embedding

```python
import matplotlib
matplotlib.use('Agg')  # Headless — no display needed
import matplotlib.pyplot as plt

# Corporate theme
plt.rcParams.update({'font.family': 'Inter', 'axes.prop_cycle': 
    plt.cycler(color=['#2563eb', '#f59e0b', '#10b981', '#ef4444'])})

fig, ax = plt.subplots(figsize=(10, 5.625))  # 16:9 ratio
ax.bar(categories, values)
fig.savefig('chart.png', dpi=300, bbox_inches='tight', transparent=True)
plt.close(fig)  # ⚠️ Always close — prevents memory leaks in batch
```

### 3. SVG icon → sized PNG for PPTX

```python
import cairosvg
# Rasterize SVG at exact dimensions with transparency
cairosvg.svg2png(url="icon.svg", write_to="icon.png", 
                 output_width=128, output_height=128)
# ⚠️ CairoSVG may not render all SVG features — test with target icons
```

### 4. Architecture diagram from Python

```python
from diagrams import Diagram, Cluster
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS

with Diagram("Architecture", filename="arch", outformat="png", show=False):
    with Cluster("VPC"):
        web = EC2("Web Server")
        db = RDS("Database")
        web >> db
# Output: arch.png — ready for slide embedding
```

### 5. Content-addressable image caching

```python
import diskcache, hashlib, json

cache = diskcache.Cache('/tmp/img_cache', size_limit=2**30)  # 1GB

def cached_generate(prompt, width, height, style):
    key = hashlib.sha256(json.dumps(
        {"p": prompt, "w": width, "h": height, "s": style}, 
        sort_keys=True).encode()).hexdigest()
    result = cache.get(key)
    if result is None:
        result = generate_image(prompt, width, height, style)
        cache.set(key, result, expire=86400, tag='session_123')
    return result
# ⚠️ Cache key must include model version — invalidate on model change
```

### 6. Quality gate with fallback chain

```python
from image_quality import brisque

def quality_gate(image_path, threshold=40.0):
    score = brisque.score(image_path)  # Lower = better
    if score > threshold:
        return None  # Trigger fallback
    return image_path

# Fallback chain
result = quality_gate(ai_image) or quality_gate(stock_image) or solid_color_fallback()
```

### 7. Batch image processing with multiprocessing

```python
from concurrent.futures import ProcessPoolExecutor
import os

def process_slide_image(path):
    img = Image.open(path)
    img = img.resize((1920, 1080), Image.LANCZOS)
    img.save(path.replace('.jpg', '_processed.png'), optimize=True)
    return path

with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
    results = list(pool.map(process_slide_image, image_paths))
# ⚠️ Pass file paths, not PIL Images — avoids serialization overhead
```

### 8. D2 diagram rendering (zero-browser)

```python
import subprocess
diagram_text = """
direction: right
User -> API: Request
API -> DB: Query  
DB -> API: Response
API -> User: Result
"""
with open("flow.d2", "w") as f:
    f.write(diagram_text)
subprocess.run(["d2", "--theme", "200", "flow.d2", "flow.svg"], 
               timeout=30, check=True)
# ⚠️ D2 binary must be on PATH — install via: curl -fsSL https://d2lang.com/install.sh | sh
```

### 9. Professional text rendering with Pango+Cairo

```python
import cairo, gi
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1920, 1080)
ctx = cairo.Context(surface)
layout = PangoCairo.create_layout(ctx)
layout.set_width(1600 * Pango.SCALE)  # Auto-wrap at 1600px
font = Pango.FontDescription("Montserrat Bold 48")
layout.set_font_description(font)
layout.set_text("Professional heading text", -1)
PangoCairo.show_layout(ctx, layout)
surface.write_to_png("text_render.png")
```

### 10. PPTX → PDF → thumbnail pipeline

```python
import subprocess
from pdf2image import convert_from_path

# PPTX → PDF via LibreOffice headless
subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", 
                "--outdir", "/tmp/", "presentation.pptx"], timeout=120)

# PDF → thumbnails at 150 DPI
images = convert_from_path("/tmp/presentation.pdf", dpi=150)
for i, img in enumerate(images):
    img.save(f"slide_{i:03d}.png")
# ⚠️ Install fonts: apt install fonts-crosextra-carlito fonts-noto
```

---

## Ten most valuable tools for the pipeline

1. **Pillow 12.1.1** — Core image processing, zero-friction, perfect scores
2. **python-pptx 1.0.2** (or python-pptx-ng) — PPTX generation foundation
3. **rembg 2.0.74** — Best CPU background removal via ONNX Runtime
4. **matplotlib 3.10** — Headless, professional charts at 300 DPI
5. **CairoSVG 2.9.0** — SVG rasterization with DPI control
6. **pycairo 1.29.0** — Vector compositing (gradients, rounded corners, shadows)
7. **Graphviz + diagrams** — Headless architecture and flow diagrams
8. **DiskCache 5.6.3** — Production-grade image caching
9. **D2** — Modern, browser-free diagram rendering
10. **Lucide** — Clean SVG icon set with Python package

The five most useful community projects are: **GongRzhe/Office-PowerPoint-MCP-Server** (most feature-rich PPTX MCP), **daymade/ppt-creator** (end-to-end slide skill), **antoinebou12/uml-mcp** (30+ diagram types), **shinpr/mcp-image** (prompt optimization skill), and **andrewmoshu/diagram-mcp-server** (multi-cloud architecture diagrams). The critical gap remaining is **automatic slide layout intelligence** — no open-source design rules engine exists, making this a high-value custom skill to build.