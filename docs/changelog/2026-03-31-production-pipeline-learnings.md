# Production Pipeline Learnings — 2026-03-31

First production render run of the Sparkline deck. Issues found and fixes applied.

## Pipeline Design Gaps Found

### 1. Draft prompts not stored in manifest
**Problem:** `source_prompt` field existed in the schema but was never populated during draft generation. The production upgrade plan couldn't carry prompts forward.
**Fix:** imagegen-bridge Step 7 now mandates storing `source_prompt` in every manifest entry. Step 12 documents the required field with example.
**Industrialise:** Enforce via schema validation — make `source_prompt` required for `status: "generated"` entries.

### 2. No per-image review during draft generation
**Problem:** Images were batch-generated without visual review. Broken images (garbled text, mutations, wrong subjects) reached the assembled deck.
**Fix:** imagegen-bridge Step 7 now has a mandatory review-and-refine loop — view every image, iterate up to 10x on Ollama (free), save versions as slide-NN-TYPE-vN.png.
**Industrialise:** Consider automated vision scoring as a first-pass filter before human review.

### 3. Ollama model tags not stored centrally
**Problem:** Model names were hardcoded without version tags (e.g., `x/z-image-turbo` instead of `x/z-image-turbo:fp8`), causing repeated generation failures.
**Fix:** `local-config.json` (gitignored) stores machine-specific model tags. imagegen-bridge Step 0 reads it before any generation. Image-generation-expert references it.
**Industrialise:** Provider discovery could auto-populate local-config.json from `ollama list`.

### 4. Outline visual_direction not updated when images were manually refined
**Problem:** Previous sessions refined slide 7, 13 images through iteration but didn't update the outline's `visual_direction`. Subsequent re-renders reverted to the original (wrong) concept.
**Fix:** Manual fix to outline.json for slides 1, 5, 7, 13 to match approved visual concepts.
**Industrialise:** When a prompt is refined and accepted, the imagegen-bridge should update the outline's `visual_direction` to match. Single source of truth.

## Provider Limitations Discovered

### 5. OpenAI GPT Image — fixed dimensions only
**Problem:** OpenAI supports only 1024x1024, 1536x1024, 1024x1536. Slide 5 element images (1024x368) were generated square and stretched by the assembler (179% distortion flagged by QA).
**Fix:** Switched slide 5 elements to FLUX Pro which supports arbitrary `{width, height}`.
**Industrialise:** image-generation-expert agent now documents dimension limitations per provider. Rule: always use FLUX Pro for non-standard aspect ratios.

### 6. Nanobanana — no dimension control
**Problem:** Nanobanana's generate_content API has no width/height or aspect_ratio parameter. Output dimensions are model-determined.
**Fix:** For full-slide 16:9 images, prefix prompt with "Slide:" to guide output dimensions. For custom ratios, use FLUX Pro instead.
**Industrialise:** Documented in image-generation-expert agent prompt engineering section.

### 7. FAL cost estimator didn't handle dict image_size
**Problem:** `estimate_fal_cost()` used `dict.get(image_size)` which fails when image_size is a dict `{width, height}` instead of a preset string.
**Fix:** Added isinstance check — if dict, calculate megapixels from width*height.
**Industrialise:** Add test case for dict image_size.

## Prompt Translation Issues

### 8. Recraft SVG prompts need different style than Ollama
**Problem:** Prompts written for Ollama's photorealistic style produced abstract conceptual art on Recraft instead of labeled diagrams. The draft FLUX Klein versions were better actual flowcharts.
**Fix:** Recraft needs design-centric prompts describing geometric layout, not photorealistic scenes. Slide 3 prompt needs rework.
**Status:** Pending — slide 3 prompt to be reworked.

### 9. SVG background colour mismatch
**Problem:** Recraft SVGs had white backgrounds (`rgb(253,253,253)`) instead of matching the slide surface colour. When rasterised to PNG, the white background showed.
**Fix:** SVG background needs to match slide surface colour (light slides: `#F5FBF7`, dark slides: `#0E1513`).
**Status:** Pending — fix for slides 3 & 6.

### 10. Full_render strategy needs title text option
**Problem:** Slide 1 (title slide) used full_render strategy — the entire slide is one AI image. But the deck title "Presentations, Engineered" was not visible because it wasn't baked into the image or overlaid.
**Fix:** Change slide 1 to `background` strategy with left_panel variant so the title is programmatic text overlay.
**Status:** Pending.

### 11. Slide 10 lost its approved visual concept
**Problem:** Previous session had iterated to an android/human head conversation visual. The re-draft used the original outline's abstract visual_direction instead.
**Fix:** Need to update outline visual_direction for slide 10 and re-draft via Ollama.
**Status:** Pending.
