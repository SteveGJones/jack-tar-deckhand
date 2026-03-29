# Jack-Tar Deckhand — Research Index

> **Purpose:** Fast lookup across all research documents. Each entry has a one-line summary, key findings tags, and a relevance map showing which skills the research feeds.
>
> **How to use:** Search this index first. Read the full paper only when you need detail. The "Key Findings" section per entry gives you 80% of the value in 20% of the reading.

---

## Existing Research (Pre-2026-03-28)

### E1. AI Image Generation Models — Comparative Analysis
- **File:** `AI-Image-Generation-Models-Research-Report-2026.md`
- **Scope:** Cloud API image models scored against presentation-specific rubric
- **Key Findings:**
  - Multi-model routing beats single-model: GPT Image 1.5 (text/general), FLUX.2 Pro (photorealism), Recraft V4 (SVG icons), Imagen 4 Fast (cheap backgrounds), Ideogram 3.0 (typography)
  - Cost per 25-slide deck: ~$1.07 hybrid, ~$2.50 premium
  - No model generates accurate charts or editable diagrams — use programmatic tools
  - Midjourney excluded: no official API
- **Feeds:** imagegen-bridge, deck-conductor
- **Tags:** `image-models`, `pricing`, `routing`, `api-comparison`

### E2. AI Image Models for Presentations — Extended Analysis
- **File:** `ai-image-models-for-presentations.md`
- **Scope:** Deeper model profiles, enterprise readiness, licensing
- **Key Findings:**
  - GPT Image 1.5 ELO 1266 (#1), natively multimodal transformer, best text rendering
  - FLUX Kontext for character consistency across slides (up to 10 reference images)
  - Adobe Firefly: only IP-indemnified option but enterprise-gated ($1K/mo minimum)
  - Gemini 3.1 Flash: fastest and cheapest at $0.015/image
  - Recraft V4: ONLY model generating native SVG — irreplaceable for icons
- **Feeds:** imagegen-bridge, slide-stylist
- **Tags:** `image-models`, `licensing`, `enterprise`, `svg`, `text-rendering`

### E3. Presentation Engineering Toolchain
- **File:** `presentation-engineering-tool-research.md`
- **Scope:** MCP servers, open-source libraries, integration patterns
- **Key Findings:**
  - 44+ MCP servers for presentations and images
  - Core stack: 8-10 libraries (Pillow, python-pptx, rembg, matplotlib, CairoSVG, pycairo, Graphviz, DiskCache, Lucide)
  - #1 gap: no open-source slide layout intelligence engine
  - python-pptx maintainer largely inactive — python-pptx-ng fork exists
  - Mermaid CLI needs Chromium; D2 is browser-free alternative
- **Feeds:** deck-assembler, chart-renderer, deck-qa
- **Tags:** `toolchain`, `mcp`, `libraries`, `layout-gap`, `diagrams`

### E4. Image Manipulation Tools & Pipeline
- **File:** `image_manipulation_tools_and_skill.md`
- **Scope:** Non-model image processing layer, caching, quality gates
- **Key Findings:**
  - Pillow 12.1.1 scores 5.0/5.0 — foundation library
  - rembg with silueta model: 43MB, 2-5s CPU background removal
  - Real-ESRGAN NOT viable on CPU (30-120s per image) — use Lanczos or cloud API
  - Pango+Cairo for production-grade text rendering (browser-quality)
  - DiskCache + HashFS for content-addressable caching
  - Pipeline: Generate → Process → Composite → Optimize → Embed
- **Feeds:** imagegen-bridge, deck-assembler, deck-qa
- **Tags:** `image-processing`, `background-removal`, `caching`, `typography`, `pipeline`

---

## New Research (2026-03-28 overnight batch)

### 01. Slide Layout Intelligence & Design Rules Engine
- **File:** `01-slide-layout-intelligence.md` (700 lines)
- **Status:** COMPLETE
- **Scope:** Layout archetypes, grid systems, design principles, projection requirements, machine-checkable rules
- **Key Findings:**
  - 18 slide layout archetypes defined with content zone specs and EMU coordinates
  - 12-column grid system with exact measurements (margins, gutters, columns, rows) in inches/EMU/pixels
  - 35 machine-checkable rules with IDs (LAY/TYP/COL/CON/PRJ), check methods, severity, fixes
  - 7 academic systems analysed: SlideCoder, PPTAgent, SlideGen, Auto-Slides, etc.
  - Beautiful.ai reverse-engineered: 300+ templates, auto-layout mechanics, design constraints
  - Projection minimums: 28pt body / 44pt heading for large rooms, 7:1 contrast ratio recommended
- **Feeds:** slide-stylist, deck-assembler, deck-qa
- **Tags:** `layout`, `design-rules`, `grid`, `projection`, `archetypes`

### 02. Existing PPTX Skill Architecture Audit
- **File:** `02-pptx-skill-audit.md` (521 lines)
- **Status:** COMPLETE
- **Scope:** Feature inventory of 8 existing skills/agents, gap analysis, integration map
- **Key Findings:**
  - 8 skills/agents audited: pptx (pptxgenjs engine), generate-presentation, generate-image, generate-icon, generate-pattern, generate-diagram, image-generation-expert, theme-factory
  - 14 gaps identified: 5 critical (no narrative, no speaker notes, no data viz, no programmatic QA, no cloud image gen), 5 significant, 4 nice-to-have
  - Integration map: 2 REPLACE (deck-conductor replaces generate-presentation), 3 WRAP, 4 NEW
  - Existing pptx skill already has 10 colour palettes, font pairings, 8 layout types, QA protocol
  - Priority: P0 data contracts → P1 narrative+stylist → P2 cloud routing → P3 charts+notes → P4 assembly → P5 QA → P6 orchestrator
- **Feeds:** All skills (determines extend vs build-new decisions)
- **Tags:** `skill-audit`, `pptx`, `existing-capabilities`, `gap-analysis`

### 03. PptxGenJS vs python-pptx Technology Decision
- **File:** `03-pptxgenjs-vs-python-pptx.md` (525 lines)
- **Status:** COMPLETE
- **Scope:** Head-to-head feature comparison, ecosystem analysis, architectural recommendation
- **Key Findings:**
  - **Decision: Keep PptxGenJS + build Python image pipeline** (polyglot architecture)
  - 75-row feature matrix comparing both libraries
  - PptxGenJS v4.0.1: active, Node.js native to Claude Code, good chart support, no animations
  - python-pptx: dormant maintainer, python-pptx-ng fork exists, stronger XML access
  - Aspose.Slides ($1,399-$19,586): only option for animations/SmartArt — NOT recommended for this project
  - Architecture: JS for PPTX assembly, Python for image/chart processing, communicate via files
- **Feeds:** deck-assembler (foundational technology choice)
- **Tags:** `pptxgenjs`, `python-pptx`, `technology-decision`, `feature-matrix`

### 04. Cloud Image API Setup & Licensing Guide
- **File:** `04-cloud-api-setup-licensing.md` (1,418 lines)
- **Status:** COMPLETE
- **Scope:** Step-by-step setup for 9 providers, licensing terms, copy-paste code samples
- **Key Findings:**
  - 9 providers documented with full setup guides: OpenAI, Google Vertex AI, FAL.ai, Recraft, BFL, Ideogram, Replicate, Together AI, Ollama, Adobe Firefly
  - Code samples: ready-to-use Python for each provider
  - Google Imagen 4 deprecation notice: June 30, 2026 for older endpoints
  - FAL.ai recommended as unified aggregation layer (single API key, 600+ models)
  - Env var naming convention and security guidance for API key storage
  - Comparison table: provider × auth method × SDK × min cost × setup time × licensing
- **Feeds:** imagegen-bridge (developer onboarding)
- **Tags:** `api-setup`, `licensing`, `openai`, `google`, `fal`, `recraft`, `ollama`

### 05. Multi-Model Routing & Ollama Drafting Pipeline
- **File:** `05-multi-model-routing-pipeline.md` (955 lines)
- **Status:** COMPLETE
- **Scope:** Routing matrix, Ollama drafting cycle, cost models, fallback chains, parallel scheduling
- **Key Findings:**
  - 11-row routing matrix: asset type → local/cloud/model/cost
  - Prompt transfer: GOOD (Klein→FLUX Pro), PARTIAL (z-image→GPT), POOR (any→Recraft), NO VALUE (any→Ideogram)
  - Cost models: All-Cloud $0.82/deck, All-Local $0.00 (40 min), Hybrid $0.82 (20-25 min, best quality)
  - 5-tier fallback: primary cloud → alt cloud → local Ollama → solid colour → skip
  - Iteration budgets: hero 3, illustration 2, everything else 0 (one-shot)
  - RouteT2I (ICCV 2025) validates routing approach: 84% quality retention at 50% cost savings
  - The overlay pattern: generate text-free images, overlay text via pptxgenjs
- **Feeds:** imagegen-bridge, deck-conductor
- **Tags:** `routing`, `ollama`, `drafting`, `cost-model`, `fallback`

### 06. Prompt Engineering Patterns for Presentation Imagery
- **File:** `06-prompt-engineering-patterns.md` (1,357 lines)
- **Status:** COMPLETE
- **Scope:** 10 prompt templates, negative space, 7 model translation rules, style consistency, failure patterns
- **Key Findings:**
  - 10 production-ready prompt templates (title hero, section divider, illustration, stat, quote, team, device, icon, pattern, process)
  - Negative space techniques: rule-of-thirds in prompts, wider-canvas crop, semi-transparent overlay via pptxgenjs
  - Model-specific rules for all 7 models (z-image-turbo, flux2-klein, GPT 1.5, FLUX Pro, Recraft, Ideogram, Imagen 4)
  - visual_direction → prompt translation schema (TypeScript interfaces, 4-stage algorithm)
  - 15 common failure patterns with specific prompt fixes
  - Prompt sweet spots: z-image-turbo ~75 tokens, flux2-klein ~250 words, GPT 1.5 unlimited
- **Feeds:** imagegen-bridge
- **Tags:** `prompts`, `negative-space`, `style-consistency`, `templates`

### 07. Conference Presentation QA Heuristics & Anti-Patterns
- **File:** `07-qa-heuristics-anti-patterns.md` (1,747 lines)
- **Status:** COMPLETE
- **Scope:** 25 anti-patterns with detection algorithms, contrast rules, AV specs, QA pipeline design
- **Key Findings:**
  - 25 anti-patterns (AP-01 to AP-25) each with python-pptx detection algorithm code, severity, fix
  - Projection contrast: 7:1 minimum recommended (stricter than WCAG AA 4.5:1)
  - AV specs: 1920x1080 standard, 5% safe margin, 100MB file size limit, embed fonts
  - BRISQUE threshold: <40 = good quality for slides
  - 4-step QA pipeline: structural parse → visual render → cross-slide consistency → report
  - Visual regression: pixelmatch + perceptual hashing + LibreOffice headless rendering
  - 60+ sources attributed
- **Feeds:** deck-qa
- **Tags:** `qa`, `anti-patterns`, `contrast`, `projection`, `detection-algorithms`

### 08. Narrative Arc & Conference Storytelling Patterns
- **File:** `08-narrative-arc-patterns.md`
- **Status:** COMPLETE (1,082 lines)
- **Scope:** 12+ talk structures, slide density, invisible slides, speaker notes intelligence
- **Key Findings:**
  - 12+ talk structures catalogued: McKinsey SCR, Monroe's Sequence, Hero's Journey, Pecha Kucha, Ignite, Lightning, Lessig, Takahashi, etc.
  - Slide density: ~1/min content-heavy, ~2/min visual-heavy, varies by format
  - Invisible slides: section dividers, breathing room, interaction beats, blank slides
  - Analysis of TED, re:Invent, WWDC, Google I/O, PyCon patterns
  - Speaker notes calibration: ~150 words/minute speaking pace
- **Feeds:** narrative-architect, speaker-notes-writer
- **Tags:** `narrative`, `talk-structures`, `pacing`, `speaker-notes`, `storytelling`

### 09. Brand Extraction & Style Transfer
- **File:** `09-brand-extraction-style-transfer.md` (986 lines)
- **Status:** COMPLETE
- **Scope:** Logo-to-palette algorithms, font heuristics, colour enforcement, template ingestion, StyleGuide schema
- **Key Findings:**
  - Logo → palette: ColorThief MMCQ extraction + 5 harmony schemes (complementary, analogous, triadic, split-complementary, tetradic)
  - 13 industry/tone → font mapping rules
  - Model-by-model colour enforcement: Recraft best (exact hex), Ideogram (palette API param), FLUX (approximate), GPT (colour names > hex)
  - Post-generation Pillow colour correction algorithms with code
  - FLUX Kontext multi-reference, Ideogram style codes (8-char hex), Gemini 14-reference system
  - Corporate template ingestion: python-pptx theme parsing with code
  - Complete StyleGuide JSON Schema defined
- **Feeds:** slide-stylist
- **Tags:** `brand`, `palette`, `fonts`, `colour-enforcement`, `style-guide`

### 10. Font Strategy & Typography for Projection
- **File:** `10-font-strategy-typography.md`
- **Status:** COMPLETE (954 lines)
- **Scope:** 10 font pairings, projection sizes, embedding, screen vs projection, text rendering
- **Key Findings:**
  - 10 Google Font pairings with projection legibility assessment and selection guide
  - Font sizes: 8H rule with formulas, Kawasaki 10/20/30, practical defaults for Jack-Tar
  - PPTX embedding: PptxGenJS and python-pptx limitations, subsetting with fonttools
  - Screen vs projection: min Regular (400) weight, larger x-height fonts preferred, sans-serif dominates
  - Text rendering: Pango+Cairo vs Playwright vs Pillow comparison
  - Font installation: macOS defaults, Homebrew, fc-cache, Docker/CI patterns
- **Feeds:** slide-stylist, deck-assembler
- **Tags:** `fonts`, `typography`, `projection`, `embedding`, `legibility`

### 11. Competitive Landscape — AI Presentation Tools
- **File:** `11-competitive-landscape.md` (459 lines)
- **Status:** COMPLETE
- **Scope:** 15-tool feature comparison, differentiation analysis, target persona
- **Key Findings:**
  - 15 tools compared across 4 categories: AI-native SaaS, collaborative, developer/markdown, and Jack-Tar
  - 7 competitive gaps: Beautiful.ai auto-layout, Gamma web-native, Canva 250K templates, Tome narrative, Plus AI Workspace integration, real-time collab, template marketplace
  - 9 Jack-Tar differentiators: Claude Code integration, local gen, multi-model routing, conference intelligence, no lock-in, privacy, programmability, QA automation, cost control
  - Target persona: developer-presenter using Claude Code (secondary: startup technical founder)
  - Tome cautionary tale: pivot away from pure AI presentations shows market risk
  - Cost advantage: Jack-Tar $1-3/deck vs $12-50/month subscriptions
- **Feeds:** Project positioning, feature prioritisation
- **Tags:** `competition`, `gamma`, `beautiful-ai`, `positioning`, `differentiation`

### 12. DeckContext Serialisation & State Management
- **File:** `12-deckcontext-state-management.md` (1,405 lines)
- **Status:** COMPLETE
- **Scope:** JSON schemas, serialisation strategy, checkpointing, error recovery, caching
- **Key Findings:**
  - **Decision: Directory of JSON files in ./tmp/deck/** (Option B — one file per contract)
  - 8 complete JSON schemas: TalkBrief, PipelineState, StyleGuide, SlideOutline, SpeakerNotes, ImageManifest, ChartManifest, QAReport
  - PipelineState tracks step status with SHA-256 checksums for resumability
  - Per-image status tracking: retry only failed images, not entire slide set
  - Fallback chains per skill type: retry → simplify → different model → placeholder → abort
  - Max 2 QA cycles before delivering best effort
  - Cache key: SHA256(prompt + dimensions + model + style tokens + steps)
  - Implementation priority: directory structure → PipelineState → simple skills → caching last
- **Feeds:** deck-conductor (core pipeline architecture)
- **Tags:** `state`, `json-schema`, `checkpoint`, `error-recovery`, `pipeline`

### 13. Cost Optimisation & Caching Strategy
- **File:** `13-cost-optimisation-caching.md` (1,051 lines)
- **Status:** COMPLETE
- **Scope:** Cost models, 3-tier caching, degradation, batch APIs, pricing trends
- **Key Findings:**
  - Per-deck costs: Draft $0.16, Standard $1.95, Premium $9.26
  - 100 decks/month fully optimised: ~$57/month (71% savings from $195 baseline)
  - 3-tier cache: L1 in-memory LRU → L2 DiskCache/SQLite 1GB → L3 HashFS permanent
  - Cache savings estimate: 34% at full coverage (icons 60-80% hit, backgrounds 40-60%, heroes 5-15%)
  - Budget degradation: ALLOW → CAPS → DEGRADE → TYPOGRAPHY_ONLY — deck always completable at $0
  - Local "saves" money but costs $138 in dev productivity per deck — cloud wins for final output
  - Batch APIs (OpenAI, Google): 50% discount, async processing
  - Pricing trend: 78% drop since DALL-E 3 (2023), further 20-40% expected next 12 months
  - Working Python code: ImageCacheManager, DeckBudget, DeckCostReport, batch JSONL
- **Feeds:** deck-conductor, imagegen-bridge
- **Tags:** `cost`, `caching`, `diskcache`, `budget`, `degradation`

### 14. Animations, Transitions & Advanced PPTX
- **File:** `14-animations-advanced-pptx.md` (992 lines)
- **Status:** COMPLETE
- **Scope:** Animation feasibility, Aspose.Slides, progressive builds, morph, video, SmartArt
- **Key Findings:**
  - PptxGenJS v4.0.1: NO animation support; community fork @bapunhansdah/pptxgenjs adds 44 types
  - python-pptx: NO animation API; lxml XML injection possible but fragile
  - Aspose.Slides ($999 dev license): full animations/SmartArt/media — NOT justified for this project
  - **Progressive builds cover ~80% of "animation" use cases** (multiple slides simulating builds)
  - Morph transition achievable via mc:AlternateContent + p159:morph XML injection + `!!` naming
  - Video/audio: PptxGenJS native addMedia() for MP4/MOV/MP3/WAV/YouTube
  - GIFs work natively in PPTX; APNG unreliable; SVG animations stripped
  - **4-tier strategy:** T1 progressive builds + GIFs (now) → T2 transition XML (next) → T3 evaluate animation fork → T4 skip Aspose/raw XML
- **Feeds:** deck-assembler (stretch goal)
- **Tags:** `animations`, `transitions`, `morph`, `smartart`, `aspose`

---

## Cross-Reference: Research → Skill Mapping

| Skill | Primary Research | Secondary Research |
|-------|-----------------|-------------------|
| **deck-conductor** | 05 (routing), 12 (state), 13 (cost) | E1, E2, 08 (narrative) |
| **narrative-architect** | 08 (narrative arcs) | 01 (layout types), 07 (anti-patterns) |
| **imagegen-bridge** | 05 (routing), 06 (prompts), 04 (API setup) | E1, E2, E4 |
| **slide-stylist** | 01 (layout), 09 (brand), 10 (fonts) | E3 (toolchain) |
| **speaker-notes-writer** | 08 (narrative arcs) | 07 (QA — missing notes check) |
| **chart-renderer** | E3 (toolchain — matplotlib/charts) | 01 (layout — chart placement) |
| **deck-assembler** | 03 (pptxgenjs vs python-pptx), 01 (layout) | 14 (animations), 10 (fonts), E4 |
| **deck-qa** | 07 (QA heuristics), 01 (layout rules) | 10 (font rules), E4 (quality gates) |

## How to Search This Library

1. **By skill:** Find your skill in the cross-reference table above, read the primary research first
2. **By tag:** Grep for tags: `grep -i "routing" research/RESEARCH-INDEX.md`
3. **By topic:** Each entry's "Key Findings" gives the 80/20 summary — read the full paper only when you need implementation detail
4. **By decision:** Looking for a technology choice? → #03. Pricing? → E1, #13. Licensing? → #04.
