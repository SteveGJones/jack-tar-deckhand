# Multi-Model Routing & Ollama Drafting Pipeline Architecture

## Research Synthesis for Jack-Tar Deckhand Image Pipeline

**Research Date:** 2026-03-28
**Total searches executed:** 28
**Total sources evaluated:** 42
**Sources included (CRAAP score 15+):** 34
**Sources excluded (CRAAP score < 15):** 8
**Target agent archetype:** Domain Expert (image pipeline orchestration)
**Research areas covered:** 8
**Identified gaps:** 2

---

## Area 1: Complete Routing Decision Matrix

### Key Findings

Every presentation asset type maps to a specific optimal model based on quality requirements, cost, and whether local drafting adds value. The routing decision combines asset type classification with a drafting-worthiness assessment.

**Finding 1.1 — Asset-to-Model Routing Table** [Confidence: HIGH]

The following matrix synthesises routing recommendations from prior model research (research reports 01 and 02) with new data on local Ollama capabilities, prompt transfer fidelity, and cost/speed profiles.

```
+-------------------------+----------+-------------------+------------------+-----------+----------+
| Asset Type              | Local    | Cloud Model       | Fallback         | Draft     | Est.     |
|                         | Usable?  | (Primary)         | (Cloud)          | Cycle     | Cost     |
|                         |          |                   |                  | Value     | (Cloud)  |
+-------------------------+----------+-------------------+------------------+-----------+----------+
| Cover / Title Hero      | YES      | FLUX.2 Pro (FAL)  | GPT Image 1.5    | HIGH      | $0.03    |
|                         | (draft)  |                   | Med              | (2-3 iter)|          |
+-------------------------+----------+-------------------+------------------+-----------+----------+
| Section Divider BG      | NO       | Imagen 4 Fast     | FLUX.2 Pro       | NONE      | $0.02    |
|                         | (skip)   |                   |                  | (skip)    |          |
+-------------------------+----------+-------------------+------------------+-----------+----------+
| Abstract Pattern /      | NO       | Imagen 4 Fast     | FLUX.2 Pro       | NONE      | $0.02    |
| Texture                 | (skip)   |                   |                  | (skip)    |          |
+-------------------------+----------+-------------------+------------------+-----------+----------+
| Flat Icons              | NO       | Recraft V4 SVG    | Recraft V4 Pro   | NONE      | $0.08    |
|                         | (N/A)    |                   | SVG              | (vector)  |          |
+-------------------------+----------+-------------------+------------------+-----------+----------+
| Quote Slide             | NO       | Ideogram 3.0      | GPT Image 1.5    | NONE      | $0.04    |
|                         | (poor    | Turbo             | Med              | (use      |          |
|                         |  text)   |                   |                  |  overlay) |          |
+-------------------------+----------+-------------------+------------------+-----------+----------+
| Chart Decoration        | YES      | Imagen 4 Fast     | FLUX.2 Pro       | LOW       | $0.02    |
|                         | (decent) |                   |                  | (1 iter)  |          |
+-------------------------+----------+-------------------+------------------+-----------+----------+
| Team / People Photos    | NO       | Imagen 4 Std      | FLUX.2 Pro       | NONE      | $0.04    |
|                         | (poor    |                   |                  | (anatomy  |          |
|                         |  anatomy)|                   |                  |  critical)|          |
+-------------------------+----------+-------------------+------------------+-----------+----------+
| Conceptual Illustration | YES      | GPT Image 1.5 Med | FLUX.2 Pro       | MEDIUM    | $0.034   |
|                         | (compos.)|                   |                  | (1-2 iter)|          |
+-------------------------+----------+-------------------+------------------+-----------+----------+
| Product Photo           | NO       | FLUX.2 Pro (FAL)  | GPT Image 1.5    | NONE      | $0.03    |
|                         | (quality |                   | High             | (needs    |          |
|                         |  insuff.)|                   |                  |  fidelity)|          |
+-------------------------+----------+-------------------+------------------+-----------+----------+
| Process Diagram         | NO       | Programmatic      | Recraft V4 Pro   | NONE      | $0.00    |
|                         | (N/A)    | (Mermaid/pycairo) |                  | (code-gen)|          |
+-------------------------+----------+-------------------+------------------+-----------+----------+
| Closing Slide           | YES      | Imagen 4 Fast     | FLUX.2 Pro       | LOW       | $0.02    |
|                         | (bg only)|                   |                  | (1 iter)  |          |
+-------------------------+----------+-------------------+------------------+-----------+----------+
```

Sources:
- Ollama Blog, "Image generation (experimental)," January 2026: https://ollama.com/blog/image-generation [CRAAP: 22]
- 302.AI, "FLUX.2 Klein Test: Sub-Second Generation Speed," January 2026: https://medium.com/@302.AI/flux-2-klein-test-sub-second-generation-speed-stuns-while-quality-faces-trade-offs-302-ai-c197a73df052 [CRAAP: 18]
- FAL.ai, "10 Best AI Image Generators in 2026": https://fal.ai/learn/tools/ai-image-generators [CRAAP: 19]
- Recraft, "API Reference Pricing": https://www.recraft.ai/docs/api-reference/pricing [CRAAP: 23]
- ImageGPT, "Flux 2 Pro vs Flux 2 Klein": https://imagegpt.cloud/learn/compare/flux-2-pro-vs-flux-2-klein [CRAAP: 17]

**Finding 1.2 — Routing Decision Logic** [Confidence: HIGH]

The routing decision is a two-phase classification:

Phase 1 — Asset Type Classification:
```
Input: slide intent description from deck outline
Output: one of {hero, section_bg, pattern, icon, quote, chart_decor,
                people, illustration, product, diagram, closing}
```

Phase 2 — Drafting Eligibility (applied only to draft-eligible types):
```
IF asset_type.draft_value >= MEDIUM
   AND ollama_available == true
   AND remaining_time_budget > (local_gen_time * max_iterations)
THEN route to local draft cycle first
ELSE route directly to cloud
```

**Finding 1.3 — The "Overlay Pattern" Eliminates Text Rendering from Image Generation** [Confidence: HIGH]

For quote slides and any text-bearing asset, the recommended architecture avoids embedding text in the generated image entirely. Instead:

1. Generate a text-free background/visual via the image model
2. Overlay text programmatically using python-pptx `addText()` or pptxgenjs `slide.addText()` with precise positioning
3. This sidesteps diffusion model text rendering failures completely

python-pptx supports z-order manipulation through shape ordering in the slide XML tree. Shapes added later appear on top. For explicit z-order control, the `slide.shapes._spTree` XML can be manipulated directly.

Sources:
- python-pptx issue #49 (z-order): https://github.com/scanny/python-pptx/issues/49 [CRAAP: 17]
- PptxGenJS Images API: https://gitbrent.github.io/PptxGenJS/docs/api-images.html [CRAAP: 21]

---

## Area 2: Ollama-to-Cloud Prompt Transfer Fidelity

### Key Findings

**Finding 2.1 — FLUX.2 Klein to FLUX.2 Pro/Max: GOOD Transfer (same architecture family)** [Confidence: HIGH]

Both Klein and Pro/Max share the FLUX.2 architecture foundation (Rectified Flow Transformer). However, there are important differences:

- Klein uses **Qwen3 text encoders** while Pro/Max uses **Mistral-3 24B vision-language model** as the text encoder
- Both models prefer natural language prose prompts over keyword lists
- The same prompt produces "comparable results" in terms of composition and subject, but Pro delivers "noticeably finer details, more coherent compositions" (ELO gap: 1170 vs 1066)
- Word order matters identically in both: subject-first prompting is recommended
- Prompt length guidelines are shared: 30-80 words for most production work

**Prompt transfer adjustment needed:** Minimal. A prompt that works well on Klein will produce a higher-quality version of the same composition on Pro. The primary difference is output fidelity, not compositional interpretation. No prompt rewriting is needed when upgrading from local Klein draft to cloud Pro final.

Sources:
- BFL, "FLUX.2 Klein Prompting Guide": https://docs.bfl.ml/guides/prompting_guide_flux2_klein [CRAAP: 23]
- FAL.ai, "Flux 2 Klein Prompt Guide": https://fal.ai/learn/devs/flux-2-klein-prompt-guide [CRAAP: 20]
- ImageGPT, "Flux 2 Pro vs Flux 2 Klein": https://imagegpt.cloud/learn/compare/flux-2-pro-vs-flux-2-klein [CRAAP: 17]

**Finding 2.2 — Ollama Z-Image-Turbo to GPT Image 1.5: PARTIAL Transfer (different architecture)** [Confidence: MEDIUM]

Z-Image-Turbo (Alibaba Tongyi, 6B parameters, diffusion-based) uses fundamentally different text interpretation than GPT Image 1.5 (OpenAI, multimodal transformer). Transfer requires:

- **Style adjustments:** Z-Image-Turbo prompts tend toward photographic terminology; GPT Image 1.5 accepts more abstract/conceptual language
- **Negative prompts:** Z-Image-Turbo supports negative prompts via Ollama; GPT Image 1.5 does not use negative prompts (it auto-optimizes)
- **Composition intent transfers well:** Subject, setting, lighting direction remain interpretable
- **Fine details need rewriting:** Camera-specific terms (ISO, focal length) work differently across architectures

**Prompt transfer adjustment needed:** Moderate. Strip negative prompts, simplify camera-specific terminology, rely on GPT Image 1.5's superior prompt understanding to fill gaps. The composition will transfer; the stylistic execution will differ.

Sources:
- Ollama Blog, "Image generation": https://ollama.com/blog/image-generation [CRAAP: 22]
- OpenAI, "Image generation guide": https://developers.openai.com/api/docs/guides/image-generation [CRAAP: 24]

**Finding 2.3 — Ollama to Recraft V4: POOR Transfer (raster to vector)** [Confidence: HIGH]

Local Ollama models generate raster images. Recraft V4 generates native SVG vector graphics. The output modalities are fundamentally incompatible, making local drafting meaningless for icon workflows:

- Raster draft provides no useful signal for vector final output
- Composition, color relationships, and style do not transfer between raster generation and vector generation paradigms
- Recraft V4 has its own specialized prompt format for design-centric output (brand hex codes, stroke weights, icon style presets)

**Recommendation:** Skip local drafting entirely for icon/vector assets. Route directly to Recraft V4 cloud API.

Sources:
- Recraft, "API Reference": https://www.recraft.ai/api [CRAAP: 23]

**Finding 2.4 — Ollama to Ideogram 3.0: NO Transfer Value (typography gap)** [Confidence: HIGH]

Ideogram 3.0 was built specifically for text rendering (90%+ accuracy vs ~30% for typical diffusion models). No local Ollama model approaches this capability. The FLUX.2 Klein text rendering is rated "Good" but not comparable to Ideogram's specialist accuracy.

Local drafting of typography-heavy assets produces misleading results: the text will be garbled locally, making composition assessment unreliable.

**Recommendation:** Use the Overlay Pattern instead. Generate text-free backgrounds locally or via cloud, then overlay text programmatically. If text-in-image is truly needed (stylized poster effects), route directly to Ideogram 3.0 cloud API.

Sources:
- Ideogram, "API Pricing": https://ideogram.ai/features/api-pricing [CRAAP: 22]
- 302.AI Klein benchmark (text rendering comparison): https://medium.com/@302.AI/flux-2-klein-test-sub-second-generation-speed-stuns-while-quality-faces-trade-offs-302-ai-c197a73df052 [CRAAP: 18]

---

## Area 3: The Drafting Cycle Architecture

### Key Findings

**Finding 3.1 — Complete Drafting Cycle Flow** [Confidence: HIGH]

```
                                    +------------------+
                                    |  Asset Intent    |
                                    |  (from outline)  |
                                    +--------+---------+
                                             |
                                    +--------v---------+
                                    |  Asset Type      |
                                    |  Classification  |
                                    +--------+---------+
                                             |
                              +--------------+--------------+
                              |                             |
                     +--------v---------+          +--------v---------+
                     |  Draft-Eligible? |          |  Direct to Cloud |
                     |  (hero, illust., |          |  (icons, people, |
                     |   chart decor)   |          |   quotes, bg,    |
                     +--------+---------+          |   product, diag) |
                              |                    +--------+---------+
                              |                             |
                     +--------v---------+                   |
                     |  Ollama          |                   |
                     |  Available?      |                   |
                     +--+----------+----+                   |
                        |          |                        |
                       YES         NO ----------------------+
                        |                                   |
               +--------v---------+                         |
               |  LOCAL DRAFT     |                         |
               |  CYCLE           |                         |
               |                  |                         |
               |  Generate image  |                         |
               |       |          |                         |
               |  Vision review   |                         |
               |  (Claude vision) |                         |
               |       |          |                         |
               |  Converged? --+  |                         |
               |  NO: refine   |  |                         |
               |  prompt, loop |  |                         |
               |       |       |  |                         |
               |  Budget hit?  |  |                         |
               |  YES: use     |  |                         |
               |  best so far  |  |                         |
               +--------+--------+                         |
                        |                                   |
               +--------v---------+                         |
               |  Transfer prompt |                         |
               |  to cloud model  |<------------------------+
               |  (minimal edits) |
               +--------+---------+
                        |
               +--------v---------+
               |  CLOUD FINAL     |
               |  GENERATION      |
               +--------+---------+
                        |
               +--------v---------+
               |  POST-PROCESSING |
               |  - Background    |
               |    removal (if   |
               |    needed)       |
               |  - Color correct |
               |  - Resize to     |
               |    16:9 @ 300dpi |
               |  - Text overlay  |
               |    (if overlay   |
               |    pattern)      |
               +--------+---------+
                        |
               +--------v---------+
               |  EMBED IN PPTX   |
               +------------------+
```

Sources:
- Multi-model pipeline architecture patterns: https://dev.to/cliprise/architecting-a-multi-model-ai-creative-pipeline-without-model-lock-in-2oc8 [CRAAP: 16]
- Iterative refinement in compositional image generation: https://arxiv.org/html/2601.15286v1 [CRAAP: 20]

**Finding 3.2 — When to Use Local Drafting** [Confidence: HIGH]

Local drafting is cost-justified ONLY for asset types where:
1. Multiple composition iterations are expected (hero images, conceptual illustrations)
2. The local model produces output in the same architecture family as the cloud model (Klein to Pro)
3. The time budget accommodates local generation (105-210 seconds per image on Apple Silicon)

| Asset Type              | Draft? | Rationale                                          |
|-------------------------|--------|----------------------------------------------------|
| Cover / Title Hero      | YES    | Highest-impact slide, worth 2-3 composition tries  |
| Section Divider BG      | NO     | Simple abstract patterns; cloud is fast and cheap   |
| Abstract Pattern        | NO     | Same as above                                       |
| Flat Icons              | NO     | Vector output impossible locally                    |
| Quote Slide             | NO     | Use overlay pattern; text-free BG is trivial        |
| Chart Decoration        | MAYBE  | Only if deck has many decorated charts              |
| Team Photos             | NO     | Anatomy quality too poor locally                    |
| Conceptual Illustration | YES    | Composition is complex; iteration helps             |
| Product Photo           | NO     | Fidelity requirements too high for local draft      |
| Process Diagram         | NO     | Programmatic generation, not image model            |
| Closing Slide           | MAYBE  | Only if matching visual theme of cover              |

**Finding 3.3 — Iteration Budget Per Asset Type (Strict Caps)** [Confidence: MEDIUM]

To prevent runaway generation time, each asset type has a hard cap on local iterations:

| Asset Type              | Max Local Iterations | Max Local Time (M4 Pro) | Rationale            |
|-------------------------|:--------------------:|:-----------------------:|----------------------|
| Cover / Title Hero      | 3                    | ~5-7 min                | High-impact, worth it|
| Conceptual Illustration | 2                    | ~3.5-5 min              | Diminishing returns  |
| Chart Decoration        | 1                    | ~1.5-2 min              | Low-stakes asset     |
| Closing Slide           | 1                    | ~1.5-2 min              | Usually matches cover|
| ALL OTHER TYPES         | 0                    | 0                       | Direct to cloud      |

Sources:
- Z-Image-Turbo benchmark (M4 Pro: ~104-108s per image quantized): https://github.com/miroleon/z-image-turbo-benchmark [CRAAP: 19]
- FLUX performance on Apple Silicon (M4 Max: ~85s, M3 Max: ~105s at 1024x1024): https://www.apatero.com/blog/flux-apple-silicon-m1-m2-m3-m4-complete-performance-guide-2025 [CRAAP: 17]

**Finding 3.4 — Convergence Detection** [Confidence: MEDIUM]

Convergence detection in local drafting uses a Claude Vision review step. After each local generation:

1. **Composition check:** Does the image match the intended layout? (subject placement, negative space for text overlay)
2. **Theme check:** Does the image broadly match the deck's visual language?
3. **Artifact check:** Are there obvious generation artifacts (distorted hands, text garble, etc.)?

The draft is "converged" when:
- All three checks pass, OR
- The composition is acceptable even if details are imperfect (details will improve in cloud final)

Research on iterative refinement shows there is an optimal stopping point where "the discrepancy of the reconstruction to the true image reaches minimum" and "iterating too long means that the noise component dominates the solution." For local drafting, this maps to: stop when composition is right; do not chase local detail quality.

Sources:
- Estimation of optimal iteration for image quality: https://pmc.ncbi.nlm.nih.gov/articles/PMC7120759/ [CRAAP: 21]
- Iterative refinement for compositional image generation: https://arxiv.org/html/2601.15286v1 [CRAAP: 20]

---

## Area 4: Cost Modelling

### Key Findings

**Finding 4.1 — Cloud API Pricing Reference Table (March 2026)** [Confidence: HIGH]

| Model                  | Provider     | Cost/Image | Gen. Speed | Notes                        |
|------------------------|-------------|:----------:|:----------:|------------------------------|
| Imagen 4 Fast          | Google       | $0.020     | ~2.7s      | Budget backgrounds           |
| FLUX.2 Pro             | BFL via FAL  | $0.030/MP  | ~2-6s      | Megapixel-based pricing      |
| GPT Image 1.5 Med      | OpenAI       | $0.034     | ~8-12s     | Best text + reasoning        |
| GPT Image 1.5 Low      | OpenAI       | $0.009     | ~5-8s      | Draft quality, very cheap    |
| Imagen 4 Standard      | Google       | $0.040     | ~4s        | Good all-around              |
| Recraft V4 Vector      | Recraft      | $0.080     | ~15s       | ONLY native SVG option       |
| Ideogram 3.0 Turbo     | Ideogram     | $0.040     | ~4s        | Best typography              |
| Ideogram 3.0 Quality   | Ideogram     | $0.100     | ~15-25s    | Maximum text fidelity        |
| FLUX.2 Max             | BFL via FAL  | $0.070/MP  | ~10s       | Maximum photorealism         |
| Recraft V4 Pro Vector  | Recraft      | $0.300     | ~45s       | Premium SVG                  |
| GPT Image 1.5 High     | OpenAI       | $0.133     | ~15-20s    | Maximum quality              |

Sources:
- PricePerToken.com image model comparison: https://pricepertoken.com/image [CRAAP: 18]
- FAL.ai FLUX.2 pricing: https://fal.ai/models/fal-ai/flux-2-pro [CRAAP: 22]
- Recraft pricing: https://www.recraft.ai/docs/api-reference/pricing [CRAAP: 23]
- OpenAI Image Generation docs: https://developers.openai.com/api/docs/guides/image-generation [CRAAP: 24]
- GPT Image 1.5 latency: https://seadanceai.com/blog/gpt-image-1-5-review [CRAAP: 16]

**Finding 4.2 — Cost Model: Standard 25-Slide Deck** [Confidence: HIGH]

**Assumptions:** A standard 25-slide deck requires approximately 20-25 generated assets with the following typical distribution: 1 cover hero, 4 section dividers, 3 background patterns, 4 icons, 2 quote slides, 1 chart decoration, 2 team photos, 3 conceptual illustrations, 1 product photo, 1 process diagram (programmatic), 1 closing slide. Total: ~23 image assets + 1 programmatic diagram.

### Strategy A: All-Cloud (Multi-Model Routing)

```
Asset Breakdown              Model                Count  $/each   Subtotal
---------------------------------------------------------------------------
Cover hero                   FLUX.2 Pro (FAL)       1    $0.030    $0.030
Section dividers             Imagen 4 Fast          4    $0.020    $0.080
Background patterns          Imagen 4 Fast          3    $0.020    $0.060
Flat icons                   Recraft V4 SVG         4    $0.080    $0.320
Quote slides                 Ideogram 3.0 Turbo     2    $0.040    $0.080
Chart decoration             Imagen 4 Fast          1    $0.020    $0.020
Team photos                  Imagen 4 Standard      2    $0.040    $0.080
Conceptual illustrations     GPT Image 1.5 Med      3    $0.034    $0.102
Product photo                FLUX.2 Pro (FAL)       1    $0.030    $0.030
Process diagram              Programmatic           1    $0.000    $0.000
Closing slide                Imagen 4 Fast          1    $0.020    $0.020
---------------------------------------------------------------------------
TOTAL                                              23              $0.822

Wall-clock time (parallel across providers):     ~45-90 seconds
Wall-clock time (sequential single-provider):    ~3-5 minutes
```

### Strategy B: All-Local (Ollama Only)

```
Asset Breakdown              Model                Count  $/each   Subtotal
---------------------------------------------------------------------------
All 23 assets                Z-Image-Turbo (local)  23   $0.00     $0.00
---------------------------------------------------------------------------
TOTAL                                              23              $0.000

Quality assessment:
  - Icons: UNUSABLE (no SVG output, poor geometric precision)
  - Text: POOR (garbled typography, unreliable)
  - People: POOR (anatomy artifacts, "over-AI'd" appearance)
  - Backgrounds: ADEQUATE (acceptable for internal decks)
  - Hero images: ADEQUATE (composition OK, detail lacking)
  - Product photos: POOR (insufficient fidelity)

Wall-clock time (sequential, M4 Pro, quantized):
  23 images x ~105 seconds = ~40 minutes

Verdict: Free but produces sub-professional output. Only suitable
for internal draft/brainstorming decks where quality is secondary.
```

### Strategy C: Hybrid Routing (Draft Locally, Final in Cloud)

```
Asset Breakdown              Draft?  Cloud Model       Count  Cloud$   Subtotal
--------------------------------------------------------------------------------
Cover hero                   YES(3)  FLUX.2 Pro (FAL)    1   $0.030    $0.030
Section dividers             NO      Imagen 4 Fast       4   $0.020    $0.080
Background patterns          NO      Imagen 4 Fast       3   $0.020    $0.060
Flat icons                   NO      Recraft V4 SVG      4   $0.080    $0.320
Quote slides                 NO      Ideogram 3.0 Turbo  2   $0.040    $0.080
Chart decoration             YES(1)  Imagen 4 Fast       1   $0.020    $0.020
Team photos                  NO      Imagen 4 Standard   2   $0.040    $0.080
Conceptual illustrations     YES(2)  GPT Image 1.5 Med   3   $0.034    $0.102
Product photo                NO      FLUX.2 Pro (FAL)    1   $0.030    $0.030
Process diagram              NO      Programmatic        1   $0.000    $0.000
Closing slide                YES(1)  Imagen 4 Fast       1   $0.020    $0.020
--------------------------------------------------------------------------------
Cloud cost TOTAL                                        23             $0.822
Local drafting cost                                                    $0.000
TOTAL                                                                  $0.822

Local draft iterations: 3 + 1 + (3x2) + 1 = 11 local images
Local draft time: 11 x ~105s = ~19 minutes (runs during cloud gen)

Wall-clock time: ~20-25 minutes (local drafting dominates)
  - Cloud generation for non-draft assets: ~45-90s (parallel)
  - Local drafting for hero + illustrations: ~19 min (sequential)
  - These overlap: cloud assets generate while local drafts iterate
```

**Finding 4.3 — Hybrid vs All-Cloud Comparison** [Confidence: HIGH]

| Metric                    | All-Cloud | All-Local | Hybrid          |
|---------------------------|:---------:|:---------:|:---------------:|
| Cost per deck             | $0.82     | $0.00     | $0.82           |
| Cost per 100 decks/month  | $82       | $0.00     | $82             |
| Wall-clock time (25 slides)| 45-90s   | ~40 min   | ~20-25 min      |
| Quality floor             | HIGH      | LOW       | HIGH            |
| Hero image quality        | HIGH      | MEDIUM    | HIGHEST (iterated) |
| Icon quality              | HIGHEST   | UNUSABLE  | HIGHEST (cloud) |
| Typography quality        | HIGH      | POOR      | HIGH (overlay)  |
| Requires Ollama           | No        | Yes       | No (graceful)   |
| Requires internet         | Yes       | No        | Yes             |

**Key insight:** The hybrid approach costs the same as all-cloud because the local drafting is free. The value add is not cost savings but **improved composition quality** for high-impact assets through iteration before committing to a cloud generation. The tradeoff is wall-clock time: ~20 minutes vs ~90 seconds.

Sources:
- Prior research report cost model: Internal research-01, research-02 [CRAAP: N/A - internal]
- Z-Image-Turbo M4 Pro benchmark: https://github.com/miroleon/z-image-turbo-benchmark [CRAAP: 19]

---

## Area 5: Fallback Chains

### Key Findings

**Finding 5.1 — Primary Fallback Chain Architecture** [Confidence: HIGH]

Production AI image systems require multi-tier fallback with circuit breakers. The recommended pattern implements a sequential provider chain with health monitoring:

```
TIER 1: Primary Cloud Model (per asset type routing)
   |
   v  [fails: timeout, 5xx, rate limit, content policy]
TIER 2: Alternative Cloud Model (same capability class)
   |
   v  [fails: all cloud providers down or budget exhausted]
TIER 3: Local Ollama Generation (degraded quality)
   |
   v  [fails: Ollama not running or not available]
TIER 4: Solid Colour with Text (typographic fallback)
   |
   v  [fails: rendering failure]
TIER 5: Skip Element (graceful omission)
```

**Finding 5.2 — Per-Asset-Type Fallback Chains** [Confidence: HIGH]

```
Cover Hero:
  FLUX.2 Pro (FAL) -> GPT Image 1.5 Med -> Ollama Klein ->
    gradient background + title text overlay

Section Divider:
  Imagen 4 Fast -> FLUX.2 Pro -> Ollama Z-Image-Turbo ->
    solid colour with subtle CSS gradient pattern

Icons:
  Recraft V4 SVG -> Recraft V4 Pro SVG -> Lucide icon library (static SVG) ->
    Unicode symbol character in styled text box

Quote Slide:
  [Overlay Pattern] Text-free BG: Imagen 4 Fast -> Ollama -> solid colour
  + programmatic text overlay (never fails independently)

Team Photos:
  Imagen 4 Standard -> FLUX.2 Pro ->
    placeholder silhouette SVG with name label

Conceptual Illustration:
  GPT Image 1.5 Med -> FLUX.2 Pro -> Ollama Klein ->
    descriptive text box with decorative border

Product Photo:
  FLUX.2 Pro -> GPT Image 1.5 High ->
    placeholder box with product name text
```

**Finding 5.3 — Budget Exhaustion Fallback** [Confidence: HIGH]

When the per-deck spending limit is reached:
1. Switch ALL remaining images to local Ollama generation (zero marginal cost)
2. If Ollama not available, switch to typography-only mode: shapes, colours, text, and static SVG icons from Lucide library
3. Track which assets were degraded for potential re-generation later

**Finding 5.4 — Ollama Not Available Fallback** [Confidence: HIGH]

When Ollama is not running or macOS-only limitation blocks Linux/Windows users:
1. Route all images to cloud APIs (no local drafting step)
2. Use GPT Image 1.5 Low ($0.009/image) as budget substitute for composition exploration that would have been done locally
3. Total cost increase: minimal ($0.009 x ~11 draft iterations = ~$0.10 per deck)

**Finding 5.5 — No Image Generation Available (Full Degradation)** [Confidence: HIGH]

When no cloud APIs are reachable and Ollama is not available:
1. Typography-only deck with shapes and icons
2. Use Lucide SVG icons (1000+ icons, MIT license, zero API cost)
3. Use pycairo/Pillow for programmatic gradient backgrounds
4. Use matplotlib for chart imagery
5. Mark deck as "draft - images pending" for later enhancement

Sources:
- Fallback architecture patterns: https://medium.com/flux-it-thoughts/fallback-the-contingency-plan-when-your-ai-provider-fails-7faf01a26a6d [CRAAP: 17]
- Multi-provider resilience patterns: https://www.gocodeo.com/post/error-recovery-and-fallback-strategies-in-ai-agent-development [CRAAP: 16]
- Gemini API outage case study (March 2026): https://help.apiyi.com/en/google-gemini-aistudio-api-outage-march-2026-nano-banana-alternative-guide-en.html [CRAAP: 16]

---

## Area 6: Parallel Generation Strategy

### Key Findings

**Finding 6.1 — Ollama Sequential Constraint** [Confidence: HIGH]

Ollama processes image generation requests sequentially by default. The `OLLAMA_NUM_PARALLEL` environment variable can enable concurrent processing, but for image generation:

- Default: 1 request at a time (sequential)
- Increasing parallelism requires proportionally more VRAM
- Image generation models (4B-9B parameters) consume significant VRAM per request
- On a 32GB M4 Pro, running even 2 parallel image generations risks OOM crashes
- **Practical recommendation: keep Ollama sequential for image generation**

Additional requests are queued FIFO when parallelism is exceeded; max queue depth is configurable via `OLLAMA_MAX_QUEUE` (default: 512).

Sources:
- Ollama FAQ on parallel requests: https://docs.ollama.com/faq [CRAAP: 23]
- Ollama parallel request handling: https://www.glukhov.org/post/2025/05/how-ollama-handles-parallel-requests/ [CRAAP: 17]
- Ollama concurrent request configuration: https://markaicode.com/ollama-concurrent-requests-parallel-inference/ [CRAAP: 16]

**Finding 6.2 — Cloud APIs: Parallel Across Providers** [Confidence: HIGH]

Cloud APIs from different providers can be called simultaneously since they use independent infrastructure:

```
CONCURRENT STREAMS (different providers):
  Stream 1: OpenAI   -> GPT Image 1.5 (illustrations)     [6 RPM Tier 1]
  Stream 2: Google    -> Imagen 4 Fast (backgrounds)        [10 IPM Tier 1]
  Stream 3: FAL.ai   -> FLUX.2 Pro (hero images)           [no published limit]
  Stream 4: FAL.ai   -> Recraft V4 SVG (icons)             [no published limit]
  Stream 5: Ideogram  -> Ideogram 3.0 (quote slides)       [rate varies by plan]
```

**Rate limit constraints per provider:**

| Provider  | Tier 1 Limit        | Tier 2 Limit        | Tier 3 Limit         |
|-----------|--------------------:|--------------------:|---------------------:|
| OpenAI    | 6 RPM              | 15 RPM              | 25 RPM               |
| Google    | 10 IPM             | 20 IPM              | 100+ IPM (negotiate) |
| FAL.ai    | Not published       | Not published       | Not published        |
| Ideogram  | Varies by plan      | Varies by plan      | Varies by plan       |
| Recraft   | Not published       | Not published       | Not published        |

Sources:
- OpenAI rate limits: https://www.aifreeapi.com/en/posts/gpt-image-1-tier-system-guide [CRAAP: 17]
- Google Imagen rate limits: https://ai.google.dev/gemini-api/docs/rate-limits [CRAAP: 23]

**Finding 6.3 — Optimal Scheduling Strategy** [Confidence: HIGH]

The optimal strategy interleaves local and cloud generation:

```
TIME  LOCAL (sequential)           CLOUD (parallel across providers)
----  --------------------------   ------------------------------------
0:00  Start hero draft #1          Start all bg/dividers (Imagen Fast)
      |                            Start all icons (Recraft V4)
      |                            Start team photos (Imagen Std)
1:45  Hero draft #1 complete       [bg/dividers done ~0:03]
      Vision review...             [icons done ~0:15]
      |                            [team photos done ~0:04]
2:00  Start hero draft #2          Start product photo (FLUX.2 Pro)
      |                            Start quote BGs (Imagen Fast)
3:45  Hero draft #2 complete       [product photo done ~2:06]
      Vision review - CONVERGED    [quote BGs done ~2:03]
4:00  Start illustration #1        Start illustrations 2,3 (cloud)
      |                            Start closing (Imagen Fast)
5:45  Illustration #1 complete     [illustration 2 done ~4:10]
      Vision review...             [illustration 3 done ~4:10]
6:00  Transfer hero prompt->cloud  [closing done ~4:03]
      FLUX.2 Pro hero final
6:06  Hero final DONE              All cloud assets DONE
      |
7:00  Transfer illust. prompt
      GPT Image 1.5 final
7:10  Illustration 1 final DONE
----
TOTAL WALL-CLOCK: ~7-8 minutes (hybrid)
vs. ALL-CLOUD: ~45-90 seconds
vs. ALL-LOCAL: ~40 minutes
```

**Finding 6.4 — Wall-Clock Time Estimates by Deck Size** [Confidence: MEDIUM]

| Deck Size  | Assets | All-Cloud (parallel) | All-Local (seq.) | Hybrid        |
|------------|:------:|:--------------------:|:----------------:|:-------------:|
| 10 slides  | ~10    | 20-45 seconds        | ~18 minutes      | ~5 minutes    |
| 25 slides  | ~23    | 45-90 seconds        | ~40 minutes      | ~8 minutes    |
| 40 slides  | ~35    | 60-120 seconds       | ~61 minutes      | ~12 minutes   |
| 60 slides  | ~50    | 90-180 seconds       | ~88 minutes      | ~18 minutes   |

Note: Hybrid time is dominated by local drafting. If local drafting is limited to only hero + 2 illustrations (regardless of deck size), hybrid time compresses to ~8 minutes for any deck size.

Sources:
- OpenAI parallel processing cookbook: https://github.com/openai/openai-cookbook/blob/main/examples/api_request_parallel_processor.py [CRAAP: 22]
- FAL.ai performance: https://fal.ai/learn/devs/gen-ai-performance-optimization [CRAAP: 19]

---

## Area 7: Budget Cap Enforcement

### Key Findings

**Finding 7.1 — Per-Deck Budget Tracking Architecture** [Confidence: HIGH]

The skill must implement client-side budget tracking since no cloud provider offers per-session spending caps with real-time enforcement. Google's Project Spend Caps have a ~10 minute delay, making them unsuitable for per-deck control.

```
DeckBudget:
  max_spend: float           # e.g., $2.00 per deck
  spent: float               # running total
  remaining: float           # max_spend - spent
  assets_generated: int
  assets_remaining: int
  degraded_assets: list      # assets that fell back due to budget

Per-generation check:
  estimated_cost = PRICING_TABLE[model][resolution]
  IF spent + estimated_cost > max_spend:
      IF remaining_assets > 0:
          switch_to_budget_mode()   # Ollama or lowest-cost cloud
      ELSE:
          skip_generation()
  ELSE:
      proceed_with_generation()
      spent += actual_cost          # track actual, not estimated
```

**Finding 7.2 — Budget Tier Recommendations** [Confidence: MEDIUM]

| Budget Tier   | Per-Deck Cap | Strategy                                    | Use Case           |
|---------------|:----------:|-----------------------------------------------|---------------------|
| Free          | $0.00      | All-local Ollama only                         | Internal brainstorm |
| Economy       | $0.50      | Cloud backgrounds + local everything else     | Draft decks         |
| Standard      | $1.00      | Full multi-model routing                      | Standard decks      |
| Premium       | $2.50      | Premium tiers (GPT High, FLUX Max)            | Client deliverables |
| Unlimited     | No cap     | Maximum quality, all premium models           | Board presentations |

**Finding 7.3 — Cost Tracking Implementation** [Confidence: HIGH]

Provider-side cost tracking mechanisms:

- **OpenAI:** Token usage reported in response headers; image generation costs can be computed from quality tier and resolution
- **Google:** Daily Cost Breakdown Graph in Billing Dashboard; Project Spend Caps available but with ~10 min delay
- **FAL.ai:** Usage tracked per API key; megapixel-based billing reported per request
- **Recraft:** Unit-based system ($1.00 = 1,000 units); balance queryable via API

The skill must maintain its own real-time ledger since provider billing dashboards are not granular or real-time enough for per-deck budgeting.

Sources:
- Google API cost controls: https://blog.google/innovation-and-ai/technology/developers-tools/more-control-over-gemini-api-costs/ [CRAAP: 22]
- OpenAI budget management: https://support.cmts.jhu.edu/hc/en-us/articles/38383798293133-Guide-to-Managing-API-Keys-and-Usage-Limits-on-platform-openai-com [CRAAP: 18]
- Multi-tenant budget proxy pattern: https://medium.com/@bimapangestu280/managing-openai-api-costs-with-budget-based-limiting-a-multi-tenant-proxy-solution-8c2a7a4d4b18 [CRAAP: 16]

---

## Area 8: Competitive Multi-Model Routing in Production

### Key Findings

**Finding 8.1 — FAL.ai: Unified Model Aggregation** [Confidence: HIGH]

FAL.ai is the leading aggregation platform for multi-model image pipelines, providing:

- 600+ models accessible via a single API key and billing account
- Custom CUDA kernels optimized per model architecture (not generic wrappers)
- Cold starts of 5-10 seconds vs 20-60+ seconds on competing platforms
- FLUX models run up to 4x faster on FAL than Replicate or direct BFL API
- Regional GPU routing to nearest available cluster
- Autoscaling from zero to thousands of GPUs based on demand
- Model switching by changing a single endpoint string; no code changes needed

FAL.ai's architecture follows a three-tier design: Foundation (models + inference), Orchestration (resource management + workflows), Application (integration + interfaces). This maps directly to the routing architecture needed for Deckhand.

Sources:
- FAL.ai architecture guide: https://fal.ai/learn/devs/building-effective-gen-ai-model-architectures [CRAAP: 19]
- FAL.ai model explorer: https://fal.ai/explore/models [CRAAP: 22]

**Finding 8.2 — Replicate: Cog-Packaged Model Deployment** [Confidence: HIGH]

Replicate's approach differs from FAL.ai:

- Models packaged via Cog (open-source containerization)
- Per-second GPU compute billing rather than per-image
- Custom deployments with dedicated scaling controls
- Supports FLUX, Recraft, SD, and community fine-tuned models
- Cold starts are slower than FAL.ai (20-60+ seconds reported)

Replicate is better suited for custom/fine-tuned model hosting; FAL.ai is better for accessing standard commercial models at optimal speed.

Sources:
- Replicate deployment guide: https://replicate.com/docs/get-started/deploy-a-custom-model [CRAAP: 21]
- Replicate model best practices: https://replicate.com/docs/guides/build/model-best-practices [CRAAP: 21]

**Finding 8.3 — RouteT2I: Academic Research on Cloud-Edge Routing (ICCV 2025)** [Confidence: HIGH]

The RouteT2I framework (Xin et al., ICCV 2025) provides the most rigorous published architecture for routing between high-quality cloud models and lightweight local models:

**Architecture:**
- Routing model (58.17M parameters, trainable in 7 minutes on a single GPU) predicts whether a given prompt needs cloud quality or can be handled by an edge model
- Uses 10 multi-dimensional quality metrics evaluated via CLIP-based contrastive scoring
- Token-level analysis identifies which words in the prompt drive quality requirements
- Dual-gate Mixture-of-Experts architecture for per-metric quality prediction

**Results:**
- At 50% routing rate (half to cloud, half to edge): achieves 83.97% of cloud-only quality
- At 40% quality target: 71.81% cost savings vs random routing
- Routing model adds only 64.5ms prediction overhead per image
- Tested across 18 cloud-edge model pairs

**Relevance to Deckhand:** While RouteT2I focuses on routing identical prompts between quality tiers, the same principle applies: simple backgrounds and patterns can be routed to cheap/fast models (analogous to edge), while complex hero images need premium models (analogous to cloud). The 84% quality retention at 50% cost savings validates the multi-tier routing approach.

Sources:
- Xin et al., "Adaptive Routing of Text-to-Image Generation Requests," ICCV 2025: https://arxiv.org/html/2411.13787v2 [CRAAP: 23]

**Finding 8.4 — Production Pipeline Anti-Patterns** [Confidence: MEDIUM]

Common failure modes in multi-model pipelines from practitioner reports:

1. **Regeneration Multiplier:** The true cost formula is `(per-gen cost x regeneration rate) + refinement cost + time cost`. Teams tracking only base generation price ignore the dominant cost factor (regenerations).

2. **Single-Point Dependency:** In March 2026, Google's Gemini AI Studio API suffered a major outage affecting Nano Banana Pro and Nano Banana 2. Teams without fallback chains experienced total pipeline failure.

3. **Rate Limit Cascades:** OpenAI Tier 1 at 6 RPM means a 25-image deck takes 4+ minutes through OpenAI alone. Parallelising across providers is not optional -- it is required for acceptable latency.

4. **Quality Drift:** When models update, output characteristics change. The recommendation is: "Review model updates quarterly" and "keep routing documentation versioned."

Sources:
- Multi-model pipeline without lock-in: https://dev.to/cliprise/architecting-a-multi-model-ai-creative-pipeline-without-model-lock-in-2oc8 [CRAAP: 16]
- Gemini API outage (March 2026): https://help.apiyi.com/en/google-gemini-aistudio-api-outage-march-2026-nano-banana-alternative-guide-en.html [CRAAP: 16]
- AI API cost management best practices: https://skywork.ai/blog/ai-api-cost-throughput-pricing-token-math-budgets-2025/ [CRAAP: 17]

---

## Synthesis

### 1. Core Knowledge Base

- **Ollama supports two local image generation models as of January 2026:** Z-Image-Turbo (6B, Alibaba) and FLUX.2 Klein (4B/9B, BFL). Currently macOS only. Generation takes 85-210 seconds per 1024x1024 image on Apple Silicon depending on hardware and quantization. Source: https://ollama.com/blog/image-generation [Confidence: HIGH]

- **FLUX.2 Klein and FLUX.2 Pro share the same architecture family** (Rectified Flow Transformer) but use different text encoders (Qwen3 vs Mistral-3 24B). Prompts transfer between them with minimal modification; quality differences are in output fidelity, not compositional interpretation. ELO gap: 1170 (Pro) vs 1066 (Klein). Source: https://imagegpt.cloud/learn/compare/flux-2-pro-vs-flux-2-klein [Confidence: HIGH]

- **Local Ollama generation is strictly sequential** for image models. OLLAMA_NUM_PARALLEL can be configured but risks OOM for image generation workloads. Practical recommendation: one image at a time locally. Source: https://docs.ollama.com/faq [Confidence: HIGH]

- **Cloud APIs can be parallelised across providers** but each provider has independent rate limits. OpenAI Tier 1: 6 RPM. Google Tier 1: 10 IPM. FAL.ai: no published limits. Source: https://www.aifreeapi.com/en/posts/gpt-image-1-tier-system-guide [Confidence: HIGH]

- **The "overlay pattern" is the recommended approach for text on slides:** generate text-free images, overlay text programmatically via pptxgenjs/python-pptx. This completely avoids the text rendering limitations of diffusion models. Source: https://gitbrent.github.io/PptxGenJS/docs/api-images.html [Confidence: HIGH]

- **RouteT2I (ICCV 2025) provides academic validation** for quality-aware routing between cloud and edge models, achieving 84% of cloud-only quality at 50% cost savings. Source: https://arxiv.org/html/2411.13787v2 [Confidence: HIGH]

- **Recraft V4 is the ONLY model producing native SVG vector output.** No local alternative exists. Icons must go to cloud. Source: https://www.recraft.ai/docs/api-reference/pricing [Confidence: HIGH]

- **FAL.ai is the recommended aggregation layer** for multi-model access: single API key, fastest inference (custom CUDA kernels), 600+ models, model switching by endpoint change. Source: https://fal.ai/learn/devs/building-effective-gen-ai-model-architectures [Confidence: HIGH]

### 2. Decision Frameworks

- **When to use local drafting:** ONLY for hero images and conceptual illustrations where composition iteration adds value AND the time budget permits 5-7 minutes of local generation. All other asset types should route directly to cloud. Source: 302.AI benchmark + internal analysis [Confidence: HIGH]

- **When to use the overlay pattern vs text-in-image:** ALWAYS prefer overlay for business presentations. Text-in-image (via Ideogram 3.0) only for stylized poster effects or artistic typography where programmatic text overlay cannot achieve the desired aesthetic. Source: Ideogram review + FLUX text rendering analysis [Confidence: HIGH]

- **When to switch from hybrid to all-cloud:** When wall-clock time matters more than composition iteration. For real-time deck generation (user waiting), skip local drafting entirely. For batch/overnight generation, use hybrid for quality improvement on hero images. [Confidence: MEDIUM]

- **Budget tier selection:** Free ($0) for internal brainstorming, Standard ($1.00) for most decks, Premium ($2.50) for client deliverables. Unlimited only for board-level presentations. Source: Pricing analysis across all providers [Confidence: HIGH]

### 3. Anti-Patterns Catalogue

- **Drafting icons locally:** Local Ollama models produce raster output; Recraft V4 produces SVG. No transfer value. Route icons directly to cloud. Source: Recraft V4 architecture analysis [Confidence: HIGH]

- **Drafting text-heavy slides locally:** Klein's text rendering is "Good" but unreliable. Garbled local text makes composition assessment impossible for text-bearing assets. Use overlay pattern instead. Source: 302.AI FLUX Klein benchmark [Confidence: HIGH]

- **Single-provider dependency:** Google Gemini API suffered a major outage in March 2026. Any pipeline routing all images through one provider will experience total failure during outages. Always maintain fallback chains across independent providers. Source: https://help.apiyi.com/en/google-gemini-aistudio-api-outage-march-2026-nano-banana-alternative-guide-en.html [Confidence: HIGH]

- **Ignoring the regeneration multiplier:** True cost = base_cost x regeneration_rate. Teams tracking only per-image pricing underestimate actual costs by 2-5x. Local drafting is free and can reduce cloud regenerations to 1x for hero images. Source: https://dev.to/cliprise/architecting-a-multi-model-ai-creative-pipeline-without-model-lock-in-2oc8 [Confidence: MEDIUM]

- **Sequential cloud generation:** Generating all 23 images through a single provider at 6 RPM takes 4+ minutes. Parallelising across 3-4 providers reduces wall-clock time to under 90 seconds. Not optional for acceptable UX. Source: OpenAI rate limit documentation [Confidence: HIGH]

- **Chasing local quality instead of local composition:** The convergence criterion for local drafting should be "composition is correct" not "details are perfect." Details improve automatically when the prompt transfers to the cloud model. Over-iterating locally wastes time without proportional quality gain. Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC7120759/ [Confidence: MEDIUM]

### 4. Tool & Technology Map

**Cloud Image Generation APIs:**

| Tool             | License        | Key Feature                    | When to Choose                  |
|------------------|---------------|--------------------------------|---------------------------------|
| FLUX.2 Pro (FAL) | Commercial    | Best photorealism, $0.03/MP   | Hero images, product photos     |
| Imagen 4 Fast    | Commercial    | $0.02/image, 2.7s latency    | Backgrounds, textures, bulk     |
| GPT Image 1.5    | Commercial    | Best reasoning + text, $0.034 | Illustrations, text-in-image    |
| Recraft V4 SVG   | Commercial    | ONLY native SVG output, $0.08| Icons, pictograms, logos        |
| Ideogram 3.0     | Commercial    | 90%+ text accuracy, $0.04    | Typography-heavy designs        |

**Local Image Generation:**

| Tool             | License        | Key Feature                    | When to Choose                  |
|------------------|---------------|--------------------------------|---------------------------------|
| Ollama + Klein   | Apache 2.0    | Free, FLUX family, 4B/9B     | Drafting hero/illustration      |
| Ollama + Z-Image | Apache 2.0    | Free, 6B, photorealistic      | Drafting hero/illustration      |

**Aggregation Platforms:**

| Tool             | License        | Key Feature                    | When to Choose                  |
|------------------|---------------|--------------------------------|---------------------------------|
| FAL.ai           | Commercial    | 600+ models, fastest inference| Primary aggregation layer       |
| Replicate        | Commercial    | Cog containers, custom models | Custom fine-tuned models        |

**Post-Processing:**

| Tool             | License        | Key Feature                    | When to Choose                  |
|------------------|---------------|--------------------------------|---------------------------------|
| Pillow 12.x      | HPND          | Universal image processing    | Always (foundation library)     |
| rembg 2.0        | MIT           | Background removal on CPU     | Transparency for overlays       |
| pycairo 1.29     | LGPL-2.1      | Gradients, rounded rects      | Programmatic BG generation      |
| CairoSVG         | LGPL-3.0      | SVG to PNG rasterisation      | Converting Recraft SVGs         |
| Lucide           | MIT           | 1000+ static SVG icons        | Fallback when API unavailable   |

**Version notes:** Ollama image generation is experimental as of January 2026. macOS only; Windows/Linux support announced but not yet released. FLUX.2 model family was released in late 2025. Recraft V4 released February 2026. All tool-specific details should be verified against current documentation before production deployment.

### 5. Interaction Scripts

**Trigger:** "Generate a presentation on [topic]"
**Response pattern:** Classify all slides, determine asset types, check Ollama availability, check budget tier, route each asset. Generate local drafts for hero/illustrations in parallel with cloud generation for all other assets. Apply overlay pattern for all text. Assemble final deck.
**Key questions to ask first:** What is the budget tier? Is Ollama available? What is the time constraint? Is this for internal or external audience?

**Trigger:** "The hero image doesn't look right"
**Response pattern:** Re-enter drafting cycle for the specific asset. Use Claude Vision to analyse the current image and the user's feedback. Generate a revised prompt. If local drafting was used, increment iteration count (respect cap). Generate new cloud final with adjusted prompt.
**Key questions to ask first:** What specifically is wrong? (composition, style, colour, subject)

**Trigger:** "This is taking too long"
**Response pattern:** Check if local drafting is active. If so, skip remaining local iterations and send current best prompt directly to cloud. If cloud generation is the bottleneck, check for rate limiting and switch to alternative providers.
**Key questions to ask first:** None -- act immediately to reduce wait time.

**Trigger:** "I'm getting API errors"
**Response pattern:** Activate fallback chain. Log the failing provider and error type. Switch to next provider in the chain. If all cloud providers fail, switch to local-only mode. If Ollama also unavailable, switch to typography-only mode.
**Key questions to ask first:** None -- automatic failover should be transparent.

**Trigger:** "Make it cheaper" / "Stay under $X"
**Response pattern:** Adjust budget cap. Re-route remaining assets through budget-optimised path: Imagen 4 Fast for everything that doesn't need specialisation, GPT Image 1.5 Low for illustrations, skip Recraft (use Lucide SVGs instead), use overlay pattern exclusively (no Ideogram).
**Key questions to ask first:** What is the target budget per deck?

**Trigger:** "I don't have Ollama installed"
**Response pattern:** Skip all local drafting. Route everything to cloud. Use GPT Image 1.5 Low ($0.009) for composition exploration if needed before committing to final generation. Total workflow is faster but loses free iteration capability.
**Key questions to ask first:** None -- Ollama availability is detected automatically.

---

## Identified Gaps

### Gap 1: Exact Ollama Image Generation Times for FLUX.2 Klein on Apple Silicon

Despite searching for specific benchmarks, no source provides authoritative generation times for FLUX.2 Klein (as opposed to Z-Image-Turbo) specifically running through Ollama on M3/M4 Apple Silicon. The Z-Image-Turbo benchmarks (104-108s on M4 Pro with quantization) were found, but Klein-specific Ollama benchmarks were not.

**Queries attempted:**
- "FLUX.2 Klein generation time seconds Apple Silicon Mac M4 Pro benchmark Ollama"
- "Ollama image generation time seconds FLUX Klein z-image-turbo Apple Silicon M1 M2 M3 M4"
- "Ollama FLUX.2 Klein local image generation speed quality benchmark"

**Mitigation:** The existing FLUX.1 performance data on Apple Silicon (M4 Max: ~85s at 1024x1024) provides an upper-bound estimate. FLUX.2 Klein is architecturally optimised for speed (sub-second on RTX 4090), so Apple Silicon performance should be somewhat faster than Z-Image-Turbo. Conservative estimate: 80-120 seconds on M4 Pro. Must be validated with local benchmarking.

### Gap 2: FAL.ai and Recraft Rate Limits

Neither FAL.ai nor Recraft publish their API rate limits. The parallel generation strategy assumes these providers can handle concurrent requests, but the actual throughput ceiling is unknown.

**Queries attempted:**
- "FAL.ai rate limits images per minute concurrent requests"
- "Recraft V4 API rate limit requests per minute"

**Mitigation:** Start with conservative parallelism (2-3 concurrent requests per provider) and increase based on empirical testing. Implement backoff on 429 responses.

---

## Cross-References

- **Finding 1.3 (Overlay Pattern) connects to Finding 2.4 (Ideogram no-transfer):** The overlay pattern eliminates the need for local typography drafting entirely, which removes the weakest link in the local-to-cloud prompt transfer chain. This is a case where an architectural decision (overlay) solves a model limitation (poor local text rendering).

- **Finding 4.3 (Hybrid costs same as all-cloud) connects to Finding 6.3 (scheduling):** The hybrid approach's value proposition is not cost savings but quality improvement through composition iteration. This only makes sense when wall-clock time is not the primary constraint. For time-sensitive generation, all-cloud with parallel scheduling is always superior.

- **Finding 5.2 (per-asset fallback chains) connects to Finding 8.4 (March 2026 Gemini outage):** The fallback chain design is validated by real-world outages. The Gemini API outage in March 2026 would have caused total pipeline failure for any team using Imagen 4 as their sole provider. Multi-provider routing is not a theoretical best practice -- it is a production necessity.

- **Finding 6.2 (parallel across providers) connects to Finding 7.1 (budget tracking):** When generating images in parallel across 4-5 providers simultaneously, the budget tracking must be predictive (pre-deducting estimated costs before generation starts) rather than reactive (tracking after completion). Otherwise, parallel generation can overshoot the budget before any single generation completes.

- **Finding 8.3 (RouteT2I) connects to Finding 1.1 (routing matrix):** The academic RouteT2I framework validates the intuition behind asset-type routing. Simple assets (backgrounds, patterns) can be handled by cheaper/faster models with minimal quality loss, while complex assets (hero images, illustrations) benefit from premium models. The 84% quality retention at 50% cost figure provides empirical grounding for the routing matrix design.

---

## Sources Summary

All sources used in this document, ordered by CRAAP score:

| # | Source | CRAAP | URL |
|---|--------|:-----:|-----|
| 1 | OpenAI Image Generation API Docs | 24 | https://developers.openai.com/api/docs/guides/image-generation |
| 2 | BFL FLUX.2 Klein Prompting Guide | 23 | https://docs.bfl.ml/guides/prompting_guide_flux2_klein |
| 3 | Google Gemini API Rate Limits | 23 | https://ai.google.dev/gemini-api/docs/rate-limits |
| 4 | Recraft API Pricing | 23 | https://www.recraft.ai/docs/api-reference/pricing |
| 5 | Xin et al., RouteT2I, ICCV 2025 | 23 | https://arxiv.org/html/2411.13787v2 |
| 6 | Ollama FAQ (parallel requests) | 23 | https://docs.ollama.com/faq |
| 7 | Ollama Blog (image generation) | 22 | https://ollama.com/blog/image-generation |
| 8 | FAL.ai FLUX.2 Pro model page | 22 | https://fal.ai/models/fal-ai/flux-2-pro |
| 9 | FAL.ai model explorer | 22 | https://fal.ai/explore/models |
| 10 | Google API cost controls blog | 22 | https://blog.google/innovation-and-ai/technology/developers-tools/more-control-over-gemini-api-costs/ |
| 11 | OpenAI parallel processor cookbook | 22 | https://github.com/openai/openai-cookbook/blob/main/examples/api_request_parallel_processor.py |
| 12 | Ideogram API Pricing | 22 | https://ideogram.ai/features/api-pricing |
| 13 | Replicate deployment docs | 21 | https://replicate.com/docs/get-started/deploy-a-custom-model |
| 14 | PptxGenJS Images API | 21 | https://gitbrent.github.io/PptxGenJS/docs/api-images.html |
| 15 | PMC optimal iteration estimation | 21 | https://pmc.ncbi.nlm.nih.gov/articles/PMC7120759/ |
| 16 | FAL.ai Klein prompt guide | 20 | https://fal.ai/learn/devs/flux-2-klein-prompt-guide |
| 17 | Iterative refinement (arXiv) | 20 | https://arxiv.org/html/2601.15286v1 |
| 18 | Z-Image-Turbo benchmark repo | 19 | https://github.com/miroleon/z-image-turbo-benchmark |
| 19 | FAL.ai generative media arch. | 19 | https://fal.ai/learn/devs/building-effective-gen-ai-model-architectures |
| 20 | FAL.ai performance optimisation | 19 | https://fal.ai/learn/devs/gen-ai-performance-optimization |
| 21 | FAL.ai image generators 2026 | 19 | https://fal.ai/learn/tools/ai-image-generators |
| 22 | PricePerToken image pricing | 18 | https://pricepertoken.com/image |
| 23 | 302.AI Klein benchmark | 18 | https://medium.com/@302.AI/flux-2-klein-test-sub-second-generation-speed-stuns-while-quality-faces-trade-offs-302-ai-c197a73df052 |
| 24 | OpenAI budget management guide | 18 | https://support.cmts.jhu.edu/hc/en-us/articles/38383798293133 |
| 25 | Glukhov parallel requests blog | 17 | https://www.glukhov.org/post/2025/05/how-ollama-handles-parallel-requests/ |
| 26 | GPT-Image-1 tier system guide | 17 | https://www.aifreeapi.com/en/posts/gpt-image-1-tier-system-guide |
| 27 | ImageGPT Klein vs Pro | 17 | https://imagegpt.cloud/learn/compare/flux-2-pro-vs-flux-2-klein |
| 28 | python-pptx z-order issue | 17 | https://github.com/scanny/python-pptx/issues/49 |
| 29 | Apple Silicon FLUX guide | 17 | https://www.apatero.com/blog/flux-apple-silicon-m1-m2-m3-m4-complete-performance-guide-2025 |
| 30 | AI API cost best practices | 17 | https://skywork.ai/blog/ai-api-cost-throughput-pricing-token-math-budgets-2025/ |
| 31 | Fallback architecture patterns | 17 | https://medium.com/flux-it-thoughts/fallback-the-contingency-plan-when-your-ai-provider-fails-7faf01a26a6d |
| 32 | Multi-model pipeline lock-in | 16 | https://dev.to/cliprise/architecting-a-multi-model-ai-creative-pipeline-without-model-lock-in-2oc8 |
| 33 | Gemini outage March 2026 | 16 | https://help.apiyi.com/en/google-gemini-aistudio-api-outage-march-2026-nano-banana-alternative-guide-en.html |
| 34 | GPT Image 1.5 review | 16 | https://seadanceai.com/blog/gpt-image-1-5-review |
