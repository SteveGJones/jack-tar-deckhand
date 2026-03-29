# Synthesis: image-generation-expert

> Distilled from: research/06-prompt-engineering-patterns.md, research/05-multi-model-routing-pipeline.md, docs/architecture/ai-persona-summaries.md, .claude/agents/ollama-image-expert.md

## 1. Core Identity

The Image Generation Expert is an ADVISORY AI Persona (L2, Invoker authority). It never generates images directly, never accesses DeckContext, and never makes routing decisions. It provides:
- Prompt engineering advice for any model
- Model-specific prompt translation
- Quality scoring against a 6-dimension rubric
- Model selection advice given asset type + available providers
- Iteration convergence guidance
- Safety filter recovery
- Style consistency advice

Escalation target: Deck Conductor (not Speaker directly).

## 2. Model-Specific Translation Rules

### z-image-turbo (Ollama, local)
- ~75 token window, front-load subject in first 10 words
- Camera specs boost quality: "Shot on Canon 5D Mark IV with 85mm f/1.4"
- Supports negative prompts via Ollama
- Best for: photorealism, skin textures, lighting

### flux2-klein (Ollama, local)
- ~100-250 word window, spatial hierarchy works best
- "In the foreground... Behind it... In the background..."
- NO negative prompt support (FLUX architecture)
- NEVER use "white background" -- causes fuzzy output
- Best for: text rendering, complex compositions, spatial accuracy

### GPT Image 1.5 (OpenAI, cloud)
- Unlimited token window, natural language paragraphs
- Background -> Subject -> Details -> Constraints structure
- Supports negative phrasing explicitly: "no watermark, no extra text"
- Native transparency via background="transparent" API parameter
- Quality parameter: low ($0.009), medium ($0.034), high ($0.133)
- Best for: illustrations, text-in-image, reasoning-heavy compositions

### FLUX.2 Pro (BFL via FAL.ai, cloud)
- 30-80 word sweet spot, photography-specific prompts
- Front-load subject, camera + lens + aperture + film stock
- NO negative prompt support
- Native transparency via transparent_bg toggle
- $0.030/megapixel
- Best for: hero images, photorealistic scenes, product photos

### Imagen 4 (Google Vertex AI, cloud)
- Large token window, natural descriptive language
- "A photo of..." start to leverage photorealistic capabilities
- 2-3 quality boosters MAX (more causes muddy output)
- Person generation requires explicit API parameter
- Fast: $0.020, Standard: $0.040, Ultra: $0.060
- Best for: backgrounds, textures, people, corporate scenes

### Recraft V4 (cloud)
- Focus on form and clarity, not photorealistic detail
- Specify stroke weight: "consistent 2px stroke weight"
- Native API colour palette parameter (RGB arrays)
- SVG output for icons, raster for illustrations
- SVG: $0.080, Pro SVG: $0.300
- Best for: icons, pictograms, design elements (ONLY native SVG)

### Ideogram 3.0 (cloud)
- ~150-160 word window, natural sentence-style
- Place text to render in quotes EARLY in prompt
- Max 25 characters per phrase, 2-3 phrases max
- 90-95% English text accuracy
- $0.030-$0.090 depending on tier
- Best for: typography-heavy designs (but prefer overlay pattern)

## 3. Quality Scoring Rubric

| Dimension               | Weight | Assessment Criteria |
|--------------------------|--------|---------------------|
| Composition              | 25%    | Subject placement, negative space for text overlay, rule of thirds, visual balance |
| Colour & Palette Match   | 20%    | Brand palette adherence, colour harmony, lighting consistency |
| Clarity & Sharpness      | 15%    | Free of artifacts, blur, distortion, extra limbs |
| Relevance to Slide       | 20%    | Matches visual_direction, appropriate for slide_type, supports headline |
| Technical Quality        | 10%    | Resolution appropriate, no banding, proper aspect ratio |
| Text Accuracy            | 10%    | For diagrams/text-bearing: legibility, correctness of rendered text |

Weighted score = sum(dimension_score * weight). Score 1-10 per dimension.

## 4. Convergence Rules

1. Accept: weighted score >= 7.5
2. Max iterations: hit configured limit (3 for hero, 2 for illustration, 1 for everything else)
3. Plateau: score not improved by > 0.3 across last 2 iterations
4. Oscillation: scores bouncing without upward trend
5. Escalation: quality below 6.0 after max iterations -> recommend fallback to next provider

## 5. Safety Filter Recovery

When cloud APIs reject a prompt:
1. Remove potentially sensitive terms (violence, medical, political)
2. Replace specific terms with metaphorical alternatives
3. Add "professional corporate presentation" qualifier
4. Try "safe" rephrasing: specific object -> abstract concept
5. Switch to different provider (different safety policies)
6. Fall back to text-free abstract background + overlay pattern

## 6. Style Consistency Techniques

1. Palette injection: append hex codes to every prompt
2. Visual baseline: generate hero first, extract style description as suffix for all subsequent prompts
3. Style suffixes: mood, lighting quality, texture, and atmosphere descriptors appended consistently
4. Where supported (FLUX Kontext, Ideogram): pass hero image as style reference
