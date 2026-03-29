# AI Image Generation Models & Platforms for Presentation Excellence

## Deep Research Report — Comprehensive Comparative Analysis for Programmatic PowerPoint Asset Creation

> **Prepared by:** Dr. Slide (AI Visual Communications Analyst Persona)
> **Research Date:** March 28, 2026
> **Version:** 1.0 | **Classification:** Internal — Engineering & Procurement
> **Target Use:** Claude Skill Architecture Decision — Extending cloud API image generation for automated PPTX pipelines

---

## 1. Executive Summary

This report provides a comprehensive, evidence-based comparative analysis of all major cloud-hosted AI image generation models and platforms, evaluated specifically through the lens of programmatic PowerPoint presentation asset creation via API. The research was conducted in March 2026 and covers 15+ distinct models across commercial APIs, platform aggregators, and emerging providers.

### 1.1 Top-Line Findings

**Quality Leader:** GPT Image 1.5 (OpenAI) leads the Artificial Analysis Text-to-Image Arena with an ELO of 1,266 as of March 2026, closely followed by Nano Banana 2 (Google Gemini 3.1 Flash Image) at 1,258 and Nano Banana Pro (Gemini 3 Pro Image) at 1,214.

**Best for Presentations Overall:** A multi-model routing approach is strongly recommended. No single model excels at all presentation asset types. The optimal architecture routes different slide elements to specialized models.

**Cost-Performance Sweet Spot:** FLUX.2 Pro (via FAL.ai at ~$0.03/MP) and Google Imagen 4 Standard ($0.04/image) deliver the best balance of quality and economy for high-volume presentation generation.

**Icons & Vectors:** Recraft V4 is the undisputed leader, being the only model that generates native, production-quality SVG output, which is ideal for scalable icons and brand assets in presentations.

**Text-in-Image:** GPT Image 1.5 and Ideogram 3.0 have essentially solved the text rendering problem that plagued earlier diffusion models, achieving 90%+ accuracy on complex typography.

**Midjourney Warning:** Despite leading in aesthetic quality, Midjourney still has no official public API. Integration requires unofficial third-party wrappers that violate Midjourney's Terms of Service. It is **NOT** recommended for automated pipelines.

**Commercial Safety:** Adobe Firefly remains the only major model trained exclusively on licensed and public-domain content, with IP indemnification for enterprise customers. However, API access requires an enterprise agreement (~$1,000/month minimum).

### 1.2 Strategic Recommendation

Implement a **multi-model routing architecture** within the Claude Skill, selecting the optimal model per asset type. The recommended stack uses three to four primary models with fallback chains, accessed primarily through **FAL.ai** as a unified aggregation layer (600+ models, single API key, lowest latency). Direct API integration with OpenAI is recommended for GPT Image 1.5 given its maturity and the availability of a robust Python SDK. Google Vertex AI should serve as a secondary channel for Imagen 4.

**Estimated cost** for generating a full 25-image presentation deck under this architecture: **$0.75 to $2.50** depending on quality settings and the mix of asset types. At 100 decks per month (2,500 images), the projected monthly spend is approximately **$75 to $250**.

---

## 2. Comparative Scoring Matrix

The following matrix scores each evaluated model against the key criteria using the 1–5 scale defined in the rubric. Scores are evidence-based and grounded in benchmarks, published reviews, API documentation, and community testing as of March 2026.

### 2.1 Tier 1 Commercial API Models — Summary Scores

| Criterion | GPT Img 1.5 | Imagen 4 | FLUX.2 Pro | Recraft V4 | Ideogram 3 | Firefly | Nova Canvas | SD 3.5 | Midjourney |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Photorealism | **5** | 4 | **5** | 3 | 4 | 4 | 3 | 3 | **5** |
| Icon / Pictogram | 3 | 3 | 3 | **5** | 3 | 3 | 2 | 3 | 3 |
| Diagram / Infographic | 2 | 2 | 2 | 3 | 3 | 2 | 2 | 2 | 2 |
| Background / Texture | 4 | 4 | 4 | 4 | 3 | 4 | 3 | 3 | **5** |
| Text in Image | **5** | 4 | 4 | 4 | **5** | 3 | 2 | 2 | 2 |
| Illustration / Concept | 4 | 4 | 4 | **5** | 4 | 4 | 3 | 4 | **5** |
| Chart / Data Viz | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| People / Headshots | 4 | **5** | **5** | 3 | 4 | 4 | 3 | 3 | **5** |
| API Maturity | **5** | 4 | 4 | 4 | 4 | 3 | 4 | 4 | 1 |
| Prompt Fidelity | **5** | 4 | 4 | 4 | 4 | 3 | 3 | 3 | 4 |
| Editing APIs | 4 | 4 | 4 | 3 | 4 | 3 | 4 | 4 | 2 |
| Batch / Throughput | 4 | 4 | 4 | 3 | 3 | 3 | 4 | 4 | 1 |
| Output Formats | 4 | 4 | 4 | **5** | 4 | 3 | 3 | 4 | 3 |
| Consistency / Repro | 4 | 4 | 4 | 4 | 4 | 3 | 3 | 4 | 3 |
| Pricing Value | 4 | **5** | 4 | 4 | 4 | 2 | 4 | **5** | 2 |
| IP / Licensing | 4 | 4 | 4 | 4 | 4 | **5** | **5** | 3 | 3 |
| Enterprise Ready | 4 | **5** | 3 | 3 | 3 | **5** | **5** | 2 | 2 |
| 16:9 Optimization | 4 | 4 | 4 | 4 | 4 | 3 | 3 | 4 | 4 |
| Transparency (PNG) | 4 | 3 | 4 | **5** | 4 | 3 | 3 | 4 | 3 |
| Speed to Slide | 4 | **5** | 4 | 4 | 3 | 3 | 4 | 3 | 1 |

> **Scoring Legend:** 5 = Exceptional (best-in-class), 4 = Strong, 3 = Adequate, 2 = Weak, 1 = Poor/Unusable. Scores are based on Artificial Analysis ELO ratings, official API documentation, published benchmarks, and community testing. Midjourney scores are capability-based but penalized heavily on API/integration criteria due to the absence of an official API.

---

## 3. Detailed Model Profiles

### 3.1 OpenAI — GPT Image 1.5

- **Provider:** OpenAI
- **Model Version:** GPT Image 1.5 (also gpt-image-1, gpt-image-1-mini)
- **Architecture:** Natively multimodal transformer (not a diffusion model)
- **ELO Rating:** 1,266 (Artificial Analysis Arena, March 2026) — **#1 overall**
- **API Access:** REST API via `platform.openai.com/v1/images`; Python SDK (`openai` package); Azure OpenAI Service
- **Pricing (verified March 2026):** GPT Image 1.5: $0.009 (low), $0.034 (medium), $0.133 (high) per 1024×1024 image. GPT Image 1 Mini: $0.005 (low) to $0.052 (high). Batch API offers ~50% discount. DALL-E 3 and DALL-E 2 are deprecated.

**✅ Strengths for Presentations:**

GPT Image 1.5 is the current overall quality leader, excelling in photorealistic hero images for title slides, text rendering within images (critical for quote slides and statistic callouts), and broad prompt adherence for complex multi-element compositions. It handles corporate scenarios well including office settings, professional headshots, and business environments. The model's multimodal architecture means it treats text as linguistic information rather than visual patterns, which is why its text rendering accuracy far exceeds traditional diffusion approaches.

**❌ Weaknesses for Presentations:**

Moderate at icon/pictogram generation compared to Recraft's vector output. Cannot generate SVG. Transparency support requires post-processing. High-quality tier pricing ($0.133/image) adds up for large decks. Rate limits at lower API tiers (5 images per minute at Tier 1) may bottleneck batch generation of full presentation decks.

**🎯 Recommended Presentation Use Cases:**

Title slide hero images, section divider backgrounds, quote slides with embedded text, conceptual illustrations, professional people/team photographs. GPT Image 1.5 Medium ($0.034/image) is the recommended default quality tier for presentation assets.

---

### 3.2 Google — Imagen 4 (Vertex AI)

- **Provider:** Google DeepMind (via Google Cloud Vertex AI / Gemini API)
- **Variants:** Imagen 4, Imagen 4 Fast, Imagen 4 Ultra
- **ELO Rating:** Nano Banana 2 (Gemini 3.1 Flash Image): 1,258; Nano Banana Pro (Gemini 3 Pro Image): 1,214 (Artificial Analysis, March 2026)
- **API Access:** REST API via Vertex AI (`predict` endpoint); Python SDK (`google-cloud-aiplatform`); Gemini Developer API
- **Pricing:** Imagen 4 Fast: $0.02/image; Imagen 4 Standard: $0.04/image; Imagen 4 Ultra: $0.06/image. Gemini 3 Pro Image: ~$0.134/image (1K output). Gemini 3.1 Flash Image: ~$0.045–$0.067/image.

**✅ Strengths:**

Excellent photorealism, particularly for people and faces where it scores among the best. Strong text rendering capabilities. The Imagen 4 Fast tier at $0.02/image is among the most cost-effective options available, making it ideal for high-volume batch generation of presentation assets. Native support for up to 4K resolution (4096×4096 on Ultra tier). Robust enterprise features via Google Cloud (SOC 2, DPA, data residency options). Person generation controls (`allow_all`, `allow_adult`, `dont_allow`) are useful for corporate contexts. Safety filter configurability is helpful for avoiding false positives on legitimate business content.

**❌ Weaknesses:**

Requires Google Cloud project setup with billing, service accounts, and IAM permissions, which adds integration overhead. Pricing is not always transparently broken out as a standalone SKU. No native SVG output. Aspect ratio flexibility is present but less emphasized than competitors. Imagen 4 Fast may produce lower-fidelity results with complex prompts, per Google's own documentation.

**🎯 Recommended Use Cases:**

High-volume background generation (Imagen 4 Fast at $0.02), professional headshots and team photos, photorealistic scene generation for section dividers. Use Imagen 4 Standard ($0.04) as a cost-effective workhorse for the majority of slide imagery needs.

---

### 3.3 Black Forest Labs — FLUX.2 Family

- **Provider:** Black Forest Labs (BFL), valued at $3.25B
- **Variants:** FLUX.2 Max, FLUX.2 Pro, FLUX.2 Dev (open-weight), FLUX.2 Klein (sub-second), FLUX Kontext
- **Architecture:** 32-billion parameter Rectified Flow Transformer + Mistral-3 24B Vision Language Model
- **ELO Rating:** FLUX.2 Max: 1,200; FLUX.2 Pro: ~1,175; FLUX.2 Dev Turbo: 1,164 (open-weights leader)
- **API Access:** Direct BFL API (bfl.ai); FAL.ai; Replicate; Together AI; Amazon Bedrock (selected variants)
- **Pricing (BFL direct):** Credit-based (1 credit = $0.01); megapixel-based for FLUX.2. FLUX.2 Pro: first MP $0.03 (FAL.ai), $0.055 (Replicate). FLUX.2 Max: first MP $0.07. FLUX Kontext Pro: ~$0.04/image.

**✅ Strengths:**

FLUX.2 Pro produces the most photorealistic output with camera-accurate optical characteristics including depth of field, lens distortion, and film grain that respond precisely to photography-specific prompts. Exceptional skin textures and lighting. Strong text rendering capabilities. The multi-reference system (up to 8 images via API, 10 in Playground) enables brand consistency across slide decks by maintaining character, product, and style identity. **Native transparent background toggle** (`transparent_bg`) for RGBA PNG output is a significant advantage for presentation overlays and icons. Seed-based reproducibility is supported. Speed is excellent, with FLUX 1.1 Pro generation in ~4.5 seconds.

**❌ Weaknesses:**

No negative prompts in the FLUX architecture, which makes it harder to exclude unwanted elements. Megapixel-based pricing can be confusing and costs escalate at higher resolutions. BFL direct API uses a polling/webhook architecture with 10-minute URL expiration, adding complexity. The open-weight Dev variant requires separate hosting or third-party inference. No native SVG output.

**🎯 Recommended Use Cases:**

Photorealistic hero images requiring camera-specific aesthetics, product photography for slides, character-consistent imagery across multi-slide narratives (via Kontext), transparent PNG overlays for slide compositing. FLUX.2 Pro via FAL.ai ($0.03/MP) is the recommended cost-performance option for high-quality photorealistic content.

---

### 3.4 Recraft — V4 Family

- **Provider:** Recraft (AI startup, ~50 employees)
- **Variants:** Recraft V4, Recraft V4 Pro, Recraft V4 SVG, Recraft V4 Pro SVG
- **ELO Rating:** Recraft V4 tops HuggingFace Text-to-Image Arena, outranking Midjourney V8 in head-to-head human preference evaluations
- **API Access:** Direct Recraft API; FAL.ai; Replicate; WaveSpeedAI; Segmind
- **Pricing:** V4 Raster: $0.04/image; V4 Vector (SVG): $0.08/image; V4 Pro Raster: $0.25/image; V4 Pro Vector: $0.30/image. V3 legacy still available at same base rates.

**✅ Strengths:**

Recraft is the **ONLY AI image model that generates production-quality native SVG vector graphics**. This is a game-changing capability for presentation design, as icons, logos, and design elements generated as SVGs scale infinitely without quality loss and integrate directly into vector-aware design tools. The V4 model demonstrates exceptional "design taste" with balanced composition, cohesive color harmony, and refined visual hierarchy that feels professional rather than generic. Brand color specification is supported (exact hex/RGB values in prompts). Text rendering is strong. Style presets and custom style creation enable consistent look-and-feel across a presentation. The model is specifically optimized for professional visual communication, including marketing materials, brand assets, and UI elements.

**❌ Weaknesses:**

Photorealism lags behind FLUX.2 Pro and GPT Image 1.5 for naturalistic photography. The Pro tier pricing ($0.25–$0.30/image) is significantly more expensive for premium output. Enterprise features (SOC 2, SSO) are less mature than Google or AWS. Not ideal for generating realistic people or photographic-quality headshots. Community and ecosystem are smaller than competitors.

**🎯 Recommended Use Cases:**

Icon sets and pictograms (SVG output at $0.08/icon), brand-consistent graphic elements, process flow visual elements, infographic components, logos, and any presentation asset that benefits from vector scalability. **This is the MUST-USE model for icon generation in the skill routing layer.**

---

### 3.5 Ideogram — Version 3.0

- **Provider:** Ideogram (founded by ex-Google Brain researchers)
- **Release:** March 2025 for 3.0
- **API Access:** Direct Ideogram API; FAL.ai; Together AI; Replicate; Runware
- **Pricing:** API: ~$0.03–$0.09/image depending on quality tier (FAL.ai). Subscription plans: Free (100 images/day), Plus ($8/mo), Pro ($20/mo). API access starts at Plus tier.

**✅ Strengths:**

Ideogram was founded specifically to solve text rendering in AI images, and version 3.0 delivers on that mission with approximately **90–95% text accuracy**, handling multi-line layouts, stylized typography, and complex compositions that defeat other models. The Style Reference feature (up to 3 reference images) enables maintaining visual consistency across a presentation deck. Character consistency via character reference images is supported in 3.0. Supports negative prompts, seed values, and multiple aspect ratios including 16:9. Editing capabilities (inpainting, remixing, reframing) are built into the same API. The generous free tier (100 images/day) is useful for prototyping and testing.

**❌ Weaknesses:**

Maximum photorealistic fidelity is behind FLUX.2 Pro and Imagen 4. Enterprise features are less mature. The subscription model may add complexity compared to pure pay-per-image APIs. Community-reported issues with inconsistency in following strict business prompts. Username-based account system has limitations.

**🎯 Recommended Use Cases:**

Quote slides with embedded text, statistic callout images, poster-style slides, any slide element requiring accurate typography integrated into the visual design. Pair with GPT Image 1.5 as a fallback for text-heavy compositions.

---

### 3.6 Adobe — Firefly Image 4

- **Provider:** Adobe
- **Model:** Firefly Image Model 4
- **Training:** Exclusively licensed Adobe Stock + public domain content
- **API Access:** Firefly Services API (enterprise only, ~$1,000/month minimum). Consumer plans do NOT include API access. Requires enterprise agreement with 100+ users minimum.
- **Pricing:** ~$0.02–$0.10 per image for API users; credit-based system. Consumer: $9.99 (Standard), $19.99 (Pro), $199.99 (Premium) per month.

**✅ Strengths:**

The only major model trained exclusively on licensed content, making it the safest option for commercial use and client deliverables. Enterprise plans include IP indemnification. Content Credentials (C2PA metadata) on all outputs. Deep integration with Adobe Creative Cloud ecosystem. Custom Model training allows brand-specific style enforcement. Over 30 generative and creative APIs in Firefly Services.

**❌ Weaknesses:**

API access is gated behind enterprise agreements with high minimums, making it impractical for smaller teams or a Claude Skill used across variable workloads. Integration requires OAuth server-to-server authentication and significant engineering effort (estimated 80–120 hours for production-ready integration). Text rendering is less reliable than GPT Image 1.5 or Ideogram. Image quality, while good, does not lead on photorealism benchmarks. Aggressive safety filters may occasionally reject legitimate business content.

**🎯 Recommendation:**

Consider only if the team requires IP indemnification for client-facing presentation deliverables and has the budget for enterprise commitment. **Not recommended as a primary model** for the Claude Skill due to access barriers and integration complexity.

---

### 3.7 Amazon — Nova Canvas (Bedrock)

- **Provider:** AWS
- **Access:** Amazon Bedrock API exclusively
- **Max Resolution:** 2048×2048
- **Pricing:** Standard: $0.04 (1024×1024), $0.06 (2048×2048). Premium: $0.06 (1024×1024), $0.08 (2048×2048).

**✅ Strengths:**

Enterprise-grade security (GDPR, HIPAA compliant via Bedrock). AWS IP indemnity coverage for Nova model outputs. Invisible watermarking for traceability. Built-in content moderation. Virtual try-on and style options. Familiar AWS SDK integration (Boto3 for Python). Seamless for teams already on AWS.

**❌ Weaknesses:**

Image quality is adequate but does not compete with top-tier models. Limited to AWS regions (US East, Europe Ireland, Asia Pacific Tokyo). No SVG output. Text rendering is weak. Limited creative flexibility compared to specialized image models. Locked into AWS ecosystem.

**🎯 Recommendation:**

Suitable as a fallback model for teams heavily invested in AWS infrastructure who need enterprise compliance guarantees. Not recommended as a primary model for presentation-quality assets.

---

### 3.8 Midjourney — V7/V8

- **Provider:** Midjourney Inc.
- **Latest:** V8 (launched March 2026, 5× faster, native 2K). V7 is the default since June 2025.
- **API Access:** ⛔ **NO OFFICIAL PUBLIC API.** Web interface and Discord only. Third-party unofficial APIs exist but violate Midjourney ToS and risk account bans.
- **Pricing:** Subscription: $10 (Basic), $30 (Standard), $60 (Pro), $120 (Mega) per month. Estimated ~$0.04–$0.07 per image depending on plan.

**✅ Strengths:**

Produces the most aesthetically pleasing, artistically refined output of any image generator. Unmatched for editorial, cinematic, and conceptual imagery. Character reference (`--cref`) and style reference (`--sref`) parameters enable consistency. V8 delivers native 2K output with 5× faster generation.

**⛔ Critical Limitation for This Use Case:**

The absence of an official API makes Midjourney **unsuitable for automated presentation pipelines**. Unofficial third-party APIs (ImagineAPI, PiAPI, APIFRAME) exist but carry account ban risk, inconsistent availability, and ToS violations. This is a **dealbreaker** for production systems. **Midjourney is EXCLUDED from the skill routing recommendation.**

---

### 3.9 Stability AI — Stable Diffusion 3.5 / Stable Image

- **Variants:** SD 3.5 Large (8B), SD 3.5 Medium (2.5B), SD 3.5 Large Turbo, Stable Image Core, Stable Image Ultra
- **API Access:** Stability Platform API; Amazon Bedrock; Replicate; FAL.ai
- **Pricing:** Stable Image Core: $0.03/image (direct API), $0.04/image (Bedrock). SD 3.5 via Bedrock: $0.08/image.

Stable Diffusion's open-source ecosystem offers maximum flexibility for custom fine-tuning (LoRA, ControlNet), but the latest proprietary models from competitors now outperform it on benchmarks. The SD 3.5 family is viable as a budget option and for teams needing specialized fine-tuned models, but is not recommended as a primary presentation asset generator given the availability of higher-quality alternatives at similar price points.

---

## 4. Use-Case Routing Recommendations

For each presentation asset type, the following table recommends the optimal model with a runner-up and concise rationale.

| Asset Type | Recommended Model | Runner-Up | Rationale |
|---|---|---|---|
| Title slide hero image (photorealistic) | **FLUX.2 Pro** | GPT Image 1.5 | Best camera-accurate optical characteristics; multi-reference for brand consistency. |
| Section divider background (abstract) | **Imagen 4 Fast** | FLUX.2 Pro | Best cost-performance at $0.02/image for abstract patterns, gradients, and textures. |
| Process flow icons (flat design set) | **Recraft V4 SVG** | Recraft V4 Pro SVG | Only model generating native SVG vectors. Icons scale perfectly at any size. $0.08/icon. |
| Conceptual illustration | **GPT Image 1.5** | Midjourney (manual) | Strong prompt adherence for abstract concepts. Use Recraft V4 if brand-style consistency is critical. |
| Professional headshot / team photo | **Imagen 4 Standard** | FLUX.2 Pro | Excellent at diverse, professional-quality people generation with safety controls. |
| Data visualization decoration | **Imagen 4 Fast** | FLUX.2 Dev | Decorative data imagery only; actual charts should use programmatic tools (matplotlib/Chart.js). |
| Quote slide text treatment | **GPT Image 1.5** | Ideogram 3.0 | Best text rendering (ELO #1). Ideogram 3.0 as specialist fallback with 90–95% text accuracy. |
| Isometric technical diagram | **Recraft V4 Pro** | GPT Image 1.5 | Recraft's design-oriented output excels at structured technical visuals. |
| Subtle textured background | **Imagen 4 Fast** | FLUX.2 Pro | Cost-efficient at $0.02 for subtle textures. FLUX.2 for more photographic textures. |
| Brand-consistent icon set | **Recraft V4 SVG** | N/A | No alternative generates native SVG. Use style presets and brand colors for consistency. |

---

## 5. Architecture Recommendation

### 5.1 Decision: Multi-Model Routing Layer

The Claude Skill should implement a **routing layer** that selects the optimal model per asset type rather than using a single model for all images. The quality gains from specialization far outweigh the additional integration complexity.

#### Primary Stack (3 Models + 1 Aggregator)

1. **GPT Image 1.5 (via OpenAI API):** Default model for general-purpose presentation imagery, text-in-image compositions, and conceptual illustrations. Python SDK available. Medium quality ($0.034/image) as default tier.
2. **Recraft V4 SVG (via FAL.ai):** Dedicated model for icons, pictograms, logos, and any asset requiring vector output. $0.08/vector. Irreplaceable capability.
3. **Imagen 4 Fast (via Google Vertex AI or Gemini API):** Budget model for backgrounds, textures, and high-volume decorative imagery. $0.02/image. Also strong for people/headshots.
4. **FAL.ai (aggregation layer):** Unified access to FLUX.2 Pro, Recraft V4, Ideogram 3.0, and 600+ other models via a single API key. Fastest inference times. Eliminates multi-provider credential management.

#### Routing Logic

```python
if asset_type in ['icon', 'pictogram', 'logo', 'symbol']:
    → Recraft V4 SVG ($0.08)
elif asset_type in ['background', 'texture', 'gradient', 'pattern']:
    → Imagen 4 Fast ($0.02)
elif asset_type in ['quote_slide', 'text_treatment', 'statistic_callout']:
    → GPT Image 1.5 Medium ($0.034)
elif asset_type in ['headshot', 'team_photo', 'people']:
    → Imagen 4 Standard ($0.04)
elif asset_type in ['hero_image', 'product_photo']:
    → FLUX.2 Pro via FAL.ai ($0.03)
else:
    → GPT Image 1.5 Medium ($0.034)  # default fallback
```

### 5.2 Cost Projection

**Typical 25-image presentation deck cost breakdown:**

| Asset Category | Model | Per Image | Subtotal | Notes |
|---|---|---:|---:|---|
| Icons/pictograms (6 images) | Recraft V4 SVG | $0.08 | $0.48 | Native vector output |
| Backgrounds/textures (4 images) | Imagen 4 Fast | $0.02 | $0.08 | Budget tier sufficient |
| Hero/section images (5 images) | FLUX.2 Pro | $0.03 | $0.15 | Photorealistic quality |
| People/headshots (3 images) | Imagen 4 Standard | $0.04 | $0.12 | Strong people generation |
| Text treatments (3 images) | GPT Image 1.5 Med | $0.034 | $0.10 | Best text rendering |
| Illustrations (4 images) | GPT Image 1.5 Med | $0.034 | $0.14 | Default fallback |
| **TOTAL (25 images)** | | | **$1.07** | |

**At scale (100 decks/month):** ~$107/month for 2,500 images. Compare to single-model approach using GPT Image 1.5 Medium for all 2,500 images: ~$85/month. The multi-model approach costs ~26% more but delivers significantly higher quality for specialized asset types (especially icons as SVG and photorealistic hero images).

**Maximum quality scenario:** If using premium tiers across the board (GPT Image 1.5 High for all non-icon/non-background images), the per-deck cost rises to approximately $2.50, or $250/month at scale. This is recommended only for high-stakes client deliverables.

---

## 6. Gap Analysis & Risk Register

### 6.1 Current Capability Gaps

**Diagrams & Flowcharts:**
No current AI image model reliably generates accurate diagrams, org charts, or process flows. All models score 2–3 at best. Spatial relationships and logical flow accuracy remain poor. **RECOMMENDATION:** Continue using programmatic diagramming tools (Mermaid, draw.io, python-pptx shape primitives) rather than AI-generated diagram images.

**Data Visualization:**
AI models cannot generate accurate charts or data visualizations where the data relationships matter. Generated chart images are purely decorative. **RECOMMENDATION:** Use matplotlib, Chart.js, or similar libraries for actual data charts, then embed as images. AI-generated imagery should only be used for decorative or conceptual data-related backgrounds.

**Brand-Perfect Consistency:**
While multi-reference systems (FLUX Kontext, Ideogram Style Reference) have improved, achieving pixel-perfect brand consistency across 25+ images in a single deck remains challenging. Color fidelity to specific hex codes is approximate rather than exact. **RECOMMENDATION:** Implement post-processing color correction when brand precision is critical.

**Transparency Quality:**
Most models do not natively generate PNG with alpha channels. FLUX.2 Pro offers a `transparent_bg` toggle, and background removal APIs exist, but edge quality varies. Semi-transparent elements (glows, soft shadows) are rarely preserved. **RECOMMENDATION:** Use FLUX.2 `transparent_bg` for cutout elements; fall back to dedicated background removal APIs (Clipdrop, remove.bg) for edge cases.

### 6.2 Risk Register

| Risk | Likelihood | Impact | Mitigation Strategy |
|---|:---:|:---:|---|
| **Vendor Lock-In** | Medium | High | Multi-model approach inherently mitigates this. FAL.ai aggregation provides model-switching flexibility. Maintain direct API credentials for primary models as backup. |
| **Pricing Volatility** | High | Medium | AI image pricing has dropped 5–10× in the past year and continues to decrease. Budget conservatively at current rates; downward price pressure is likely. Monitor quarterly. |
| **Content Policy Drift** | Medium | Medium | Models may become more restrictive over time. Maintain fallback models with different policy thresholds. Adobe Firefly is the most stable in this regard. |
| **Model Deprecation** | Medium | High | OpenAI has already deprecated DALL-E 2 and DALL-E 3. Google is deprecating older Imagen endpoints by June 2026. Build abstraction layers to swap models with minimal code changes. |
| **API Rate Limits** | High | Medium | OpenAI Tier 1 limits to 5 images/minute. Batch generation of a 25-image deck takes 5 min. Mitigate by parallelizing across multiple providers. |
| **Quality Regression** | Low | Medium | Model updates can occasionally reduce quality in specific domains. Pin to specific model versions/snapshots where available. Test before upgrading. |
| **Midjourney API Launch** | Low | Low | If Midjourney launches an official API, it could become the aesthetic leader for presentation imagery. Monitor announcements. Not currently actionable. |

---

## 7. Source Registry & Methodology Notes

### 7.1 Primary Sources Consulted

**Benchmark Data:** Artificial Analysis Text-to-Image Arena & Leaderboard (artificialanalysis.ai/image) — ELO ratings from millions of blind human preference comparisons. Accessed March 28, 2026.

**OpenAI Pricing:** Official OpenAI Pricing Page (platform.openai.com/docs/pricing) and GPT Image 1 Model Page (platform.openai.com/docs/models/gpt-image-1). Verified March 24–28, 2026.

**Google Imagen / Vertex AI:** Google Cloud Vertex AI Pricing (cloud.google.com/vertex-ai/generative-ai/pricing) and Gemini Developer API Pricing (ai.google.dev/gemini-api/docs/pricing). Verified March 26–28, 2026.

**Black Forest Labs FLUX:** BFL Official Pricing (docs.bfl.ml/quick_start/pricing) and FAL.ai model pages (fal.ai/models/fal-ai/flux-2-pro). Verified March 2026.

**Recraft:** Recraft API Pricing (recraft.ai/docs/api-reference/pricing) and FAL.ai model pages (fal.ai/recraft-v4). Verified March 2026.

**Ideogram:** Ideogram API Pricing (ideogram.ai/features/api-pricing) and Ideogram 3.0 release page (ideogram.ai/features/3.0). Verified March 2026.

**Adobe Firefly:** Adobe Firefly Enterprise page (business.adobe.com/products/firefly-business.html) and community analysis. Enterprise API pricing approximate due to custom quoting.

**Amazon Nova Canvas:** Amazon Bedrock Pricing (aws.amazon.com/bedrock/pricing/) and Nova Canvas Service Card (docs.aws.amazon.com/ai/responsible-ai/nova-canvas/overview.html). Verified March 2026.

**Comparative Reviews:** Cliprise Medium analysis (Feb 2026), MindStudio model comparison guide (Feb 2026), TeamDay.ai 14-model ranking (March 2026), FAL.ai best image generators guide (March 2026), WaveSpeedAI Recraft V4 analysis (March 2026), LaoZhang AI pricing comparison (Feb 2026).

### 7.2 Methodology Notes & Confidence Flags

All pricing data has been verified against official provider pages between March 24–28, 2026. Prices change frequently; reverify before procurement decisions.

ELO scores from Artificial Analysis are based on crowdsourced blind human preference comparisons and represent the most objective quality benchmark available. However, ELO scores measure general aesthetic preference and may not perfectly correlate with presentation-specific use cases.

Rubric scores in the scoring matrix are the analyst's assessment synthesizing benchmark data, API documentation review, published reviews, and community reports. Scores for criteria where direct testing was not performed are flagged where applicable.

> ⚠️ **Staleness Warning:** The AI image generation landscape evolves rapidly. Models released or updated after March 28, 2026, including potential Midjourney API launch, FLUX.2 updates, and new entrants, may significantly alter these recommendations. Recommend quarterly re-evaluation.

**Anthropic Image Generation:** As of March 2026, Anthropic (Claude) does not offer a standalone image generation API. Claude can describe and analyze images but does not generate them. This is confirmed absent.

**Tier 2/3 Coverage:** Tencent Hunyuan Image 3.0 (ELO 1,238) and ByteDance Seedream 4.5 (ELO 1,225) show competitive quality from Chinese providers. API availability outside China is expanding. Alibaba Tongyi Wanxiang / Qwen Image Max 2512 (ELO 1,151 in open weights) is accessible via international APIs. These are monitored but not recommended as primary models due to data residency concerns and less mature English-language documentation.

---

*— End of Report —*

*Prepared with the rigor of a technology due diligence assessment.*
