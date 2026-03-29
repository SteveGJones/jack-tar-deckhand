# Prompt Engineering Patterns for Presentation Imagery

## Research Methodology

- **Date of research**: 2026-03-28
- **Total searches executed**: 28
- **Total sources evaluated**: 42
- **Sources included (CRAAP score 15+)**: 34
- **Sources excluded (CRAAP score < 15)**: 8
- **Target agent archetype**: Domain Expert (imagegen-bridge skill)
- **Research areas covered**: 7
- **Identified gaps**: 2

---

## Area 1: Prompt Template Library Per Slide Type

### Key Findings

Each slide type demands a distinct prompt architecture. The templates below are production-ready, designed for 16:9 (1920x1080 or 1536x1024) output, and follow the Subject + Context + Style + Technical framework that works across models.

**Finding 1.1: Title Slide Hero Image**

Title slides require dramatic, high-impact imagery with deliberate negative space for text overlay. The image must set the emotional tone for the entire deck.

```
TEMPLATE: title_slide_hero

A dramatic [SCENE_DESCRIPTION], [MOOD] atmosphere. The subject is
positioned in the right two-thirds of the frame, leaving the left
third as clear negative space for title text. [LIGHTING_DESCRIPTION],
cinematic composition, 16:9 landscape format. Shot on [CAMERA_SPEC],
shallow depth of field with soft bokeh background. Professional
commercial photography style, high contrast, [COLOR_PALETTE].
No text, no watermarks, no logos.

EXAMPLE INSTANTIATION:
A dramatic aerial view of a modern glass skyscraper piercing through
morning fog, confident atmosphere. The building is positioned in the
right two-thirds of the frame, leaving the left third as clear
negative space for title text. Golden hour sunlight streaming through
clouds, cinematic composition, 16:9 landscape format. Shot on Sony
A7IV with 24mm f/2.8 lens, shallow depth of field with soft bokeh
background. Professional commercial photography style, high contrast,
deep navy and warm gold palette. No text, no watermarks, no logos.
```

Source: BFL Prompting Guide (https://docs.bfl.ml/guides/prompting_guide_flux2), fal.ai FLUX 2 Guide (https://fal.ai/learn/devs/flux-2-prompt-guide) [Confidence: HIGH]

**Finding 1.2: Section Divider Background**

Section dividers must be subtle and atmospheric with a large clear zone for the section title. Low contrast and muted tones prevent competition with overlaid text.

```
TEMPLATE: section_divider

A soft, atmospheric [ABSTRACT_DESCRIPTION] in muted [COLOR_PALETTE]
tones. Minimalist composition with significant negative space across
the centre of the frame for text overlay. Low contrast, subtle
gradients blending from [COLOR_A] to [COLOR_B]. Gentle, diffused
lighting with no harsh shadows. Abstract, dreamlike quality. 16:9
landscape format, clean and uncluttered.
No text, no watermarks, no sharp focal points.

EXAMPLE:
A soft, atmospheric watercolour wash of overlapping geometric forms
in muted slate blue and warm grey tones. Minimalist composition with
significant negative space across the centre of the frame for text
overlay. Low contrast, subtle gradients blending from #3B4F6B to
#D4C5B2. Gentle, diffused lighting with no harsh shadows. Abstract,
dreamlike quality. 16:9 landscape format, clean and uncluttered.
No text, no watermarks, no sharp focal points.
```

Source: Gemini 2.5 Flash Prompting Guide (https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/), fal.ai GPT Image 1.5 Guide (https://fal.ai/learn/devs/gpt-image-1-5-prompt-guide) [Confidence: HIGH]

**Finding 1.3: Content Illustration**

Content illustrations support a key point with a conceptual metaphor. They must be clean and professional without visual clutter.

```
TEMPLATE: content_illustration

A clean, professional conceptual illustration of [METAPHOR_DESCRIPTION].
[STYLE: flat vector illustration | isometric design | minimal line art].
Simple composition with [2-3] main elements arranged with clear visual
hierarchy. [COLOR_PALETTE] colour scheme on a [clean white | light grey
#F5F5F5] background. Modern corporate aesthetic, balanced proportions.
16:9 landscape format.
No text, no decorative borders, no unnecessary detail.

EXAMPLE:
A clean, professional conceptual illustration of interconnected gears
and lightbulbs representing innovation in process automation. Flat
vector illustration style. Simple composition with three main elements
arranged with clear visual hierarchy. Deep teal #0D7377 and coral
#FF6B6B colour scheme on a clean white background. Modern corporate
aesthetic, balanced proportions. 16:9 landscape format.
No text, no decorative borders, no unnecessary detail.
```

Source: Ideogram Prompt Structure Guide (https://docs.ideogram.ai/using-ideogram/prompting-guide/3-prompt-structure), Recraft V4 Guide (https://www.imagine.art/blogs/recraft-V-4-prompt-guide) [Confidence: HIGH]

**Finding 1.4: Stat Callout Background**

Stat slides feature large numbers that must dominate. The background provides texture without competing.

```
TEMPLATE: stat_callout_bg

A minimal, muted [TEXTURE_TYPE] texture in [COLOR_PALETTE]. Extremely
low contrast, barely perceptible detail. Soft gradient from [COLOR_A]
at the edges to slightly lighter [COLOR_B] in the centre. No focal
point, no subjects, no distinct shapes. The entire frame should serve
as a quiet, textured canvas. 16:9 landscape format, ultra-minimalist.

EXAMPLE:
A minimal, muted brushed linen texture in warm charcoal #2C2C2C and
dark slate #1A1A2E. Extremely low contrast, barely perceptible detail.
Soft gradient from #1A1A2E at the edges to slightly lighter #2C2C2C
in the centre. No focal point, no subjects, no distinct shapes. The
entire frame should serve as a quiet, textured canvas. 16:9 landscape
format, ultra-minimalist.
```

Source: Ambience AI FLUX Guide (https://www.ambienceai.com/tutorials/flux-prompting-guide), Promptomania Pattern Prompts (https://promptomania.com/prompts/pattern-prompts) [Confidence: MEDIUM]

**Finding 1.5: Quote Slide Background**

Quote slides require atmospheric, contemplative imagery that evokes emotion without distraction.

```
TEMPLATE: quote_slide_bg

A contemplative, atmospheric [SCENE_DESCRIPTION] with [warm | cool]
[MOOD] tones. Extremely shallow depth of field rendering the entire
scene as a soft, painterly blur. Dominant colour palette: [COLOR_PALETTE].
The composition is open and spacious with the majority of the frame
serving as negative space for quote text. Gentle, [golden hour | blue
hour | overcast] lighting. 16:9 landscape format, editorial photography
style with intentional lens blur.
No text, no people, no sharp details.

EXAMPLE:
A contemplative, atmospheric morning mist rising over a still lake
with warm amber and soft blue tones. Extremely shallow depth of field
rendering the entire scene as a soft, painterly blur. Dominant colour
palette: amber #D4A373, dusty blue #8EAFC0, warm white #FFF8F0. The
composition is open and spacious with the majority of the frame
serving as negative space for quote text. Gentle, golden hour lighting.
16:9 landscape format, editorial photography style with intentional
lens blur.
No text, no people, no sharp details.
```

Source: Gemini Prompting Guide (https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/) [Confidence: HIGH]

**Finding 1.6: Team/People Photo**

Professional, diverse, authentic-feeling imagery of people in business contexts.

```
TEMPLATE: team_people_photo

A professional photograph of [NUMBER] diverse business professionals
[ACTION_DESCRIPTION] in a [SETTING]. Natural, authentic body language
and genuine expressions. [LIGHTING: soft natural window light | modern
office lighting]. Clean, uncluttered corporate environment with neutral
tones. Shot on Canon EOS R5, 35mm lens at f/4, eye-level perspective.
Professional editorial photography style, warm colour temperature,
16:9 landscape format.
No stock photo cliches, no forced smiles, no text overlays.

EXAMPLE:
A professional photograph of four diverse business professionals
collaborating around a whiteboard in a modern open-plan office.
Natural, authentic body language and genuine expressions. Soft natural
window light with gentle fill from overhead panels. Clean, uncluttered
corporate environment with neutral tones. Shot on Canon EOS R5, 35mm
lens at f/4, eye-level perspective. Professional editorial photography
style, warm colour temperature, 16:9 landscape format.
No stock photo cliches, no forced smiles, no text overlays.
```

Source: Existing research (AI-Image-Generation-Models-Research-Report-2026.md), fal.ai FLUX 2 Guide (https://fal.ai/learn/devs/flux-2-prompt-guide) [Confidence: HIGH]

**Finding 1.7: Product/Demo Screenshot Frame**

Clean device mockup providing context for a product screenshot.

```
TEMPLATE: device_mockup

A [DEVICE: modern laptop | smartphone | tablet | desktop monitor]
displaying a [SCREEN_CONTENT_DESCRIPTION] on a [SETTING: clean white
desk | minimal workspace | floating in space]. The device is angled
[slightly to the left | straight on] with subtle shadow beneath.
[DEVICE_COLOR] finish, realistic reflections and screen glow.
Professional product photography, three-point softbox lighting setup,
16:9 landscape format.
No brand logos on the device, no distracting elements.

EXAMPLE:
A modern laptop displaying a clean dashboard interface with blue and
white elements on a minimal white desk. The device is angled slightly
to the left with subtle shadow beneath. Space grey finish, realistic
reflections and screen glow. Professional product photography,
three-point softbox lighting setup, 16:9 landscape format.
No brand logos on the device, no distracting elements.
```

Source: GodOfPrompt Mockup Prompts (https://www.godofprompt.ai/blog/prompts-for-product-mockups) [Confidence: MEDIUM]

**Finding 1.8: Icon/Pictogram**

Flat-design icons require extreme simplicity, consistent geometry, and ideally vector output.

```
TEMPLATE: icon_pictogram

A single flat-design icon representing [CONCEPT]. Clean geometric
shapes, consistent 2px stroke weight, [BRAND_COLOR] on transparent
background. Minimal detail, no gradients, no shadows, no 3D effects.
Perfectly centred in a square 1:1 frame. Scalable vector style,
modern UI aesthetic.

EXAMPLE:
A single flat-design icon representing cloud computing. Clean
geometric shapes, consistent 2px stroke weight, #0066CC on transparent
background. Minimal detail, no gradients, no shadows, no 3D effects.
Perfectly centred in a square 1:1 frame. Scalable vector style,
modern UI aesthetic.
```

**Note**: This template is optimised for Recraft V4 SVG output. For raster models, replace "transparent background" with "clean white background" and plan for post-processing background removal.

Source: Recraft Logos and Icons Guide (https://www.recraft.ai/docs/prompt-engineering-guide/visual-formats/logos-and-icons), Recraft Image Sets (https://www.recraft.ai/blog/how-to-create-image-sets) [Confidence: HIGH]

**Finding 1.9: Abstract Pattern/Texture**

Seamless patterns for slide backgrounds must be subtle and brand-aware.

```
TEMPLATE: abstract_pattern

A seamless repeating geometric pattern of [SHAPE_DESCRIPTION].
[COLOR_PALETTE] colour scheme, subtle and low-contrast. Tileable
design suitable for a background texture. Minimalist, modern
corporate aesthetic. Uniform density across the entire frame with
no focal point or centre of attention. 16:9 landscape format.
No text, no logos, no photographic elements.

EXAMPLE:
A seamless repeating geometric pattern of interlocking hexagons with
thin connecting lines. Navy #1B2A4A and light grey #E8E8E8 colour
scheme, subtle and low-contrast. Tileable design suitable for a
background texture. Minimalist, modern corporate aesthetic. Uniform
density across the entire frame with no focal point or centre of
attention. 16:9 landscape format.
No text, no logos, no photographic elements.
```

Source: Promptomania Pattern Prompts (https://promptomania.com/prompts/pattern-prompts), PatternedAI (https://www.patterned.ai/) [Confidence: MEDIUM]

**Finding 1.10: Process/Timeline Visual**

Process visuals require clear spatial hierarchy with left-to-right or top-to-bottom flow.

```
TEMPLATE: process_timeline

A clean, modern infographic-style illustration showing a [NUMBER]-step
process flowing from left to right. Each step is represented by a
[circle | rounded rectangle | icon] connected by [arrows | lines |
dotted paths]. Clear spatial hierarchy with the first step on the
far left and the final step on the far right. [COLOR_PALETTE] colour
scheme with each step slightly different in shade to show progression.
Flat design, no photographic elements. White or light grey background.
16:9 landscape format, isometric or flat perspective.

EXAMPLE:
A clean, modern infographic-style illustration showing a 5-step
process flowing from left to right. Each step is represented by a
rounded rectangle connected by directional arrows. Clear spatial
hierarchy with the first step on the far left and the final step on
the far right. Teal-to-navy gradient colour scheme (#0D7377 through
#1B2A4A) with each step slightly different in shade to show
progression. Flat design, no photographic elements. White background.
16:9 landscape format, flat perspective.
```

**Note**: For complex process diagrams with accurate logical relationships, programmatic tools (Mermaid, draw.io, python-pptx shapes) are more reliable than AI image generation. Use AI-generated process visuals only for decorative/conceptual representations.

Source: AI Image Generation Models Research (existing research), Civitai Composition Guide (https://civitai.com/articles/16602/simple-composition-tricks-to-instantly-improve-ai-images-with-prompts) [Confidence: MEDIUM]

### Sources for Area 1

1. BFL FLUX.2 Prompting Guide - https://docs.bfl.ml/guides/prompting_guide_flux2 (CRAAP: 23)
2. fal.ai FLUX 2 Prompt Guide - https://fal.ai/learn/devs/flux-2-prompt-guide (CRAAP: 21)
3. fal.ai GPT Image 1.5 Guide - https://fal.ai/learn/devs/gpt-image-1-5-prompt-guide (CRAAP: 21)
4. OpenAI GPT Image 1.5 Prompting Guide - https://developers.openai.com/cookbook/examples/multimodal/image-gen-1.5-prompting_guide (CRAAP: 24)
5. Ideogram Prompt Structure - https://docs.ideogram.ai/using-ideogram/prompting-guide/3-prompt-structure (CRAAP: 22)
6. Gemini 2.5 Flash Prompting - https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/ (CRAAP: 23)
7. GodOfPrompt Mockup Prompts - https://www.godofprompt.ai/blog/prompts-for-product-mockups (CRAAP: 16)
8. Recraft Logos & Icons - https://www.recraft.ai/docs/prompt-engineering-guide/visual-formats/logos-and-icons (CRAAP: 22)
9. Civitai Composition Tricks - https://civitai.com/articles/16602/simple-composition-tricks-to-instantly-improve-ai-images-with-prompts (CRAAP: 17)

---

## Area 2: Negative Space Management

### Key Findings

Negative space management is the single most critical prompt engineering challenge for presentation imagery. AI models default to filling the frame and centring subjects, which directly conflicts with the need for text overlay zones.

**Finding 2.1: Prompt Phrases That Reliably Create Empty Zones**

Multiple sources confirm that explicit negative-space language must be "written into the prompt" because "composition is not automatic" for AI models. The following phrases have been validated across FLUX, GPT Image, and Gemini models:

**Tested effective phrases (ranked by reliability):**
1. `"minimalist composition with significant negative space in the [left third | upper half | centre]"` -- Most reliable across all models
2. `"subject positioned in the [right third | lower right] of the frame, leaving [left | upper] area clear for text overlay"` -- Works well with FLUX and GPT Image
3. `"wide shot with vast empty [sky | space | background] dominating the frame"` -- Effective for atmospheric backgrounds
4. `"clean, uncluttered composition with ample breathing room around the subject"` -- Good general-purpose phrase
5. `"rule of thirds composition with subject offset to the far-[left | right] third of the frame"` -- Specific positional control

**Phrases that work inconsistently:**
- `"with space for text"` -- Too vague; models often ignore it
- `"blank area on the left"` -- Models sometimes interpret "blank" literally as white
- `"leave room for..."` -- Instructional phrasing is less effective than descriptive phrasing

Source: Civitai Composition Tricks (https://civitai.com/articles/16602/simple-composition-tricks-to-instantly-improve-ai-images-with-prompts), Nano Banana Prompts (https://minimaxir.com/2025/11/nano-banana-prompts/) [Confidence: HIGH]

**Finding 2.2: Rule of Thirds in Prompts**

The rule of thirds is the most reliable composition technique for AI image generation. Models trained on photography data respond strongly to this concept.

**Implementation pattern:**
```
"[Subject description], positioned according to the rule of thirds
[horizontally and vertically]. Subject offset to the far-[left|right]
third of the frame. [Remaining two-thirds | opposite third] is
[empty sky | soft gradient | blurred background] providing clear
negative space."
```

**Key insight**: Simply including "rule of thirds composition" nudges the AI to arrange the scene with the subject away from centre, but for reliable text-overlay zones, you must explicitly describe BOTH where the subject goes AND what fills the empty space. Describing the empty space as something specific (e.g., "soft morning sky" rather than just "empty") produces better results.

**Industry-quality framing trick**: Phrases like "Pulitzer-prize-winning cover photo for The New York Times" improve compositional quality beyond simple aesthetic improvements, as the model generates better rule-of-thirds adherence and professional framing.

Source: Nano Banana Prompts (https://minimaxir.com/2025/11/nano-banana-prompts/), Civitai Composition Tricks (https://civitai.com/articles/16602/simple-composition-tricks-to-instantly-improve-ai-images-with-prompts) [Confidence: HIGH]

**Finding 2.3: Model-Specific Negative Space Behaviour**

Different models respond differently to negative space instructions:

| Model | Negative Space Reliability | Best Approach |
|-------|---------------------------|---------------|
| GPT Image 1.5 | Good | Descriptive scene-based: "vast desert highway stretching to the horizon, with clear sky filling the upper two-thirds" |
| FLUX 2 Pro | Good | Photography-based: "shot on 24mm wide-angle lens, subject in lower-right third, expansive sky above" |
| FLUX 2 Klein | Moderate | Keep prompts under 100 words; front-load composition directives |
| Gemini/Imagen | Good | Natural language: "describe the scene with the subject on one side, leaving the rest spacious and open" |
| Ideogram 3.0 | Moderate | Works best with the 8-part prompt structure placing composition in section 7 |
| Recraft V4 | Good for icons | Use "centred in frame with generous padding" for icons; "ample margins" for illustrations |

Source: BFL Guide (https://docs.bfl.ml/guides/prompting_guide_flux2), GPT Image 1.5 Guide (https://developers.openai.com/cookbook/examples/multimodal/image-gen-1.5-prompting_guide), Gemini Guide (https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/) [Confidence: HIGH]

**Finding 2.4: The Wider-Canvas Crop Technique**

When prompt-based negative space control is unreliable, an architectural workaround exists: generate at a wider aspect ratio (e.g., 3:1) than the target (16:9), then crop. This forces the subject to occupy a smaller portion of the frame, making it statistically more likely to land on one side. One practitioner reports that "in the vast majority of cases, that works, resulting in images that look great, with the subject on the left-hand side."

**Implementation**: Generate at 3072x1024 (3:1), then centre-crop or side-crop to 1920x1080 (16:9).

Source: Haje Jan Kamps (https://haje.medium.com/a-trick-to-place-the-subject-off-to-either-side-using-gen-ai-c4993a1b3c2f) [Confidence: MEDIUM]

**Finding 2.5: The Semi-Transparent Overlay Alternative**

When AI-generated images cannot reliably produce negative space, the overlay approach generates full-bleed images and adds a semi-transparent rectangle in pptxgenjs to ensure text readability.

**pptxgenjs implementation:**
```javascript
// Add background image at full bleed
slide.addImage({ path: imagePath, x: 0, y: 0, w: '100%', h: '100%' });

// Add semi-transparent overlay for text readability
slide.addShape(pptxgen.shapes.RECT, {
  x: 0, y: 0, w: '50%', h: '100%',   // left half overlay
  fill: { color: '000000', transparency: 60 }  // 60% transparent black
});

// Add text on top of overlay
slide.addText('Title Text', {
  x: 0.5, y: 2, w: '45%',
  color: 'FFFFFF', fontSize: 36, bold: true
});
```

**Overlay patterns by slide type:**
- **Title slide**: Left-half gradient overlay (black 70% transparent fading to fully transparent at 60% width)
- **Section divider**: Full-width horizontal band at centre (40% height, 50% transparent)
- **Quote slide**: Bottom-third overlay (dark, 50% transparent)
- **Stat callout**: Full-frame subtle darkening (80% transparent black)

This approach is more reliable than trying to force negative space through prompts and should be the fallback strategy.

Source: SlideTeam Text Over Images (https://www.slideteam.net/blog/11-hacks-to-make-text-over-images-more-readable-craft-a-stunning-slide), pptxgenjs Documentation (https://gitbrent.github.io/PptxGenJS/docs/usage-slide-options.html) [Confidence: HIGH]

### Sources for Area 2

1. Civitai Composition Tricks - https://civitai.com/articles/16602 (CRAAP: 17)
2. Nano Banana Prompts - https://minimaxir.com/2025/11/nano-banana-prompts/ (CRAAP: 20)
3. BFL Prompting Guide - https://docs.bfl.ml/guides/prompting_guide_flux2 (CRAAP: 23)
4. Haje Jan Kamps Medium - https://haje.medium.com/a-trick-to-place-the-subject-off-to-either-side-using-gen-ai-c4993a1b3c2f (CRAAP: 16)
5. pptxgenjs Docs - https://gitbrent.github.io/PptxGenJS/docs/usage-slide-options.html (CRAAP: 22)
6. SlideTeam Design Tips - https://www.slideteam.net/blog/11-hacks-to-make-text-over-images-more-readable-craft-a-stunning-slide (CRAAP: 16)

---

## Area 3: Model-Specific Prompt Translation Rules

### Key Findings

Each model has a distinct "prompt dialect" that maximises its capabilities. A generic prompt will produce adequate results, but a model-optimised prompt produces significantly better output. The translation layer must convert a single `visual_direction` into model-specific prompts.

**Finding 3.1: Ollama z-image-turbo Translation Rules**

Z-Image-Turbo is a 6B-parameter model from Alibaba's Tongyi Lab optimised for photorealistic output and bilingual text rendering. It runs locally via Ollama on macOS.

| Characteristic | Value |
|---|---|
| Effective token window | ~75-100 tokens (prompts exceeding 100 words create confusion) |
| Negative prompt support | Yes |
| Seed support | Yes (via Ollama parameter) |
| Best approach | Front-load subject, add camera specs, keep concise |

**Translation rules:**
1. Front-load the primary subject in the first 10 words
2. Camera specifications boost quality dramatically: "Shot on Canon 5D Mark IV with 85mm f/1.4"
3. Keep total prompt under 75 tokens (approximately 50-60 words)
4. Use negative prompts for exclusions: "no text, no watermarks, no blurry"
5. Specify lighting explicitly: "golden hour lighting" or "studio softbox"
6. Avoid abstract concepts; use concrete, visual descriptions

**Template:**
```
[SUBJECT in 10 words]. [CAMERA_SPEC]. [LIGHTING]. [COMPOSITION in 10 words].
[STYLE in 5 words]. [COLOR_PALETTE]. 16:9 landscape format.

Negative: blurry, text, watermark, low quality, distorted
```

Source: Ollama Blog (https://ollama.com/blog/image-generation), fal.ai FLUX 2 Klein Guide (https://fal.ai/learn/devs/flux-2-klein-prompt-guide) [Confidence: MEDIUM]

**Finding 3.2: Ollama flux2-klein Translation Rules**

FLUX 2 Klein runs locally via Ollama in 4B and 9B variants. It follows the FLUX architecture with a shorter inference time but supports the same prompt style.

| Characteristic | Value |
|---|---|
| Effective token window | ~100-250 words (longer prompts work better than z-image-turbo) |
| Negative prompt support | No (FLUX architecture does not support negative prompts) |
| Seed support | Yes |
| Best approach | Spatial hierarchy, layered descriptions, specific details |

**Translation rules:**
1. Use spatial hierarchy: "In the foreground... In the middle ground... In the background..."
2. Longer, more descriptive prompts work better than terse ones (30-80 words sweet spot)
3. NEVER use "white background" -- use "clean light grey studio backdrop" instead (white causes blown-out results)
4. Avoid negative phrasing entirely ("no X") -- describe what you WANT instead
5. Camera/lens specifications provide strong composition cues
6. Hex colours work: "the wall is colour #2C3E50"
7. Content words (nouns, proper nouns) exert stronger effects than modifiers

**Template:**
```
[SUBJECT_DESCRIPTION, 20-30 words]. In the foreground, [FOREGROUND_ELEMENT].
Behind it, [BACKGROUND_DESCRIPTION]. [LIGHTING_DESCRIPTION, specific direction
and quality]. [CAMERA: "Shot on [camera], [lens] at f/[aperture]"].
[STYLE_REFERENCE]. [COLOR_PALETTE with hex codes]. 16:9 landscape composition
with [COMPOSITION_RULE].
```

Source: BFL Prompting Guide (https://docs.bfl.ml/guides/prompting_guide_flux2), fal.ai FLUX 2 Klein Guide (https://fal.ai/learn/devs/flux-2-klein-prompt-guide) [Confidence: HIGH]

**Finding 3.3: GPT Image 1.5 Translation Rules**

GPT Image 1.5 is a natively multimodal transformer (not a diffusion model). It processes natural language conversationally and understands context, spatial relationships, and temporal references.

| Characteristic | Value |
|---|---|
| Effective token window | Very large (handles long, detailed prompts natively) |
| Negative prompt support | Yes (state exclusions explicitly: "no watermark") |
| Seed support | No native seed parameter |
| Transparency | Native `background: "transparent"` API parameter (PNG/WebP) |
| Best approach | Natural language paragraphs, contextual layering, iterative refinement |

**Translation rules:**
1. Structure as: background/scene -> subject -> key details -> constraints
2. Use natural paragraphs, not keyword lists
3. Long prompts work well -- the model auto-optimises internally
4. Camera/lens terminology steers results more reliably than generic "8K/ultra-detailed"
5. Place literal text in quotes or ALL CAPS; spell out challenging words letter-by-letter
6. For exclusions: "no watermark, no extra text, no logos/trademarks"
7. Quality parameter: use `quality="high"` for production, `quality="low"` for iteration
8. For transparency: set `background="transparent"` and `output_format="png"`

**Template:**
```
Background: [SCENE/ENVIRONMENT_DESCRIPTION].
Subject: [DETAILED_SUBJECT_DESCRIPTION with materials, shapes, textures].
Key details: [LIGHTING_DESCRIPTION], [CAMERA_ANGLE], [COLOUR_PALETTE].
Style: [VISUAL_MEDIUM: "professional studio photography" | "flat vector
illustration" | "watercolour painting"].
Constraints: No watermarks, no extra text, no logos. [COMPOSITION_DIRECTION].
```

**API parameters:**
```json
{
  "model": "gpt-image-1.5",
  "quality": "medium",
  "size": "1536x1024",
  "background": "auto",
  "output_format": "png"
}
```

Source: OpenAI GPT Image 1.5 Cookbook (https://developers.openai.com/cookbook/examples/multimodal/image-gen-1.5-prompting_guide), fal.ai GPT Image 1.5 Guide (https://fal.ai/learn/devs/gpt-image-1-5-prompt-guide) [Confidence: HIGH]

**Finding 3.4: FLUX 2 Pro (Cloud API) Translation Rules**

FLUX 2 Pro is a 32B-parameter Rectified Flow Transformer with a Mistral-3 24B Vision Language Model encoder. Available via BFL direct API and fal.ai.

| Characteristic | Value |
|---|---|
| Effective token window | Up to 32,000 tokens; sweet spot 30-80 words |
| Negative prompt support | No |
| Seed support | Yes |
| Transparency | Native `transparent_bg` toggle for RGBA PNG |
| Best approach | Photography-specific prompts, camera+lens, film stock references |

**Translation rules:**
1. Front-load the subject -- word order affects prioritisation
2. Photography specifications dramatically improve quality: camera model, lens focal length, aperture, film stock
3. Hex colours work when paired with specific objects: "a vase in colour #FF6B35"
4. Prose over keywords: write flowing descriptions, not comma-separated lists
5. Lighting has the biggest impact: specify type, direction, quality, and interaction with surfaces
6. Single style reference per prompt -- do not mix competing styles
7. Text in quotes: "a neon sign reading 'OPEN LATE'"
8. For transparency: set `transparent_bg: true` in API call

**Template:**
```
[SUBJECT, concrete and specific, 15-20 words]. [ACTION/STATE].
[ENVIRONMENT, 10-15 words]. [LIGHTING: type, direction, quality,
"warm golden sunset light streaming through windows, casting long
shadows"]. Shot on [CAMERA], [FOCAL_LENGTH] at f/[APERTURE],
[FILM_STOCK if photorealistic]. [MOOD/ATMOSPHERE]. [COLOUR_PALETTE
with hex codes]. [COMPOSITION: "rule of thirds" | "centred symmetry"
| "subject in right third"]. 16:9 landscape format.
```

**API parameters:**
```json
{
  "prompt": "...",
  "image_size": { "width": 1536, "height": 1024 },
  "seed": 42,
  "transparent_bg": false,
  "num_inference_steps": 28
}
```

Source: BFL Prompting Guide (https://docs.bfl.ml/guides/prompting_guide_flux2), Ambience AI FLUX Guide (https://www.ambienceai.com/tutorials/flux-prompting-guide), fal.ai FLUX 2 Guide (https://fal.ai/learn/devs/flux-2-prompt-guide) [Confidence: HIGH]

**Finding 3.5: Recraft V4 Translation Rules**

Recraft V4 is the only model producing native SVG vector output. Optimised for design work, icons, and brand assets.

| Characteristic | Value |
|---|---|
| Token window | Handles long, detailed prompts without losing structure |
| Negative prompt support | Yes |
| Seed support | Yes |
| SVG output | Yes (text-to-vector endpoint) |
| Colour control | Native hex/RGB colour palette parameter in API |

**Translation rules:**
1. Focus on form and clarity, not photorealistic detail
2. Specify stroke weight explicitly: "consistent 2px stroke weight" or "ultra-thin 1px stroke"
3. Use the API colour palette parameter for exact brand colours (hex codes)
4. Describe geometric properties: "circular form, balanced central placement"
5. For icon sets: generate 6 at once using the Set tool for consistency
6. Note: Style presets are NOT supported for V4 models via API (use V3 for style presets)
7. For brand consistency: create a custom style from reference images, then apply across generations

**Template (icons):**
```
A [flat | line art | minimal | bold] icon representing [CONCEPT].
[GEOMETRIC_DESCRIPTION: "circular form with inner triangle" |
"rounded square containing simplified [object]"]. Consistent
[1px | 2px | 3px] stroke weight, monoline style. [COLOR] on
[transparent | white] background. Scalable vector design,
works at small sizes. Modern [UI | corporate | tech] aesthetic.
```

**Template (illustrations):**
```
A professional [illustration style] of [SUBJECT]. Clean lines,
balanced composition, [COLOR_PALETTE]. [GEOMETRIC_STYLE: isometric |
flat | line art]. Corporate design aesthetic suitable for a
presentation. No photographic elements.
```

**API parameters:**
```json
{
  "prompt": "...",
  "style": "icon",
  "size": "1024x1024",
  "colors": [
    { "rgb": [0, 102, 204] },
    { "rgb": [255, 255, 255] }
  ]
}
```

Source: Recraft Logos and Icons (https://www.recraft.ai/docs/prompt-engineering-guide/visual-formats/logos-and-icons), Recraft Image Sets (https://www.recraft.ai/blog/how-to-create-image-sets), Replicate Recraft V4 (https://replicate.com/blog/recraft-v4) [Confidence: HIGH]

**Finding 3.6: Ideogram 3.0 Translation Rules**

Ideogram 3.0 specialises in typography and text rendering within images. Founded by ex-Google Brain researchers specifically to solve text-in-image generation.

| Characteristic | Value |
|---|---|
| Token window | ~150-160 words (~200 tokens); longer prompts may be ignored |
| Negative prompt support | Yes |
| Seed support | Yes |
| Text accuracy | 90-95% for English |
| Best approach | Natural sentence-style prompts, text in quotes early in prompt |

**Translation rules:**
1. Write natural sentences, not keyword lists -- Ideogram v2+ responds better to natural grammar
2. Place text to render in quotation marks EARLY in the prompt
3. Keep in-image text SHORT: 1-4 word phrases produce the most reliable results
4. Maximum 25 characters per text phrase; use 2-3 phrases maximum
5. Describe font style properties rather than font names: "bold sans-serif", "thin rounded bauhaus style", "refined formal script with flourishes"
6. Specify text placement relative to scene: "centred on the banner", "along the bottom edge"
7. Non-Latin alphabets are unreliable
8. Use Magic Prompt for enhanced styling, but turn it OFF when applying Style References
9. Style Reference: upload up to 3 reference images for visual consistency

**Template:**
```
[IMAGE_TYPE: "A poster" | "A presentation slide visual" | "A banner"]
featuring the text "[EXACT_TEXT]" in [FONT_STYLE_DESCRIPTION].
[SCENE/BACKGROUND_DESCRIPTION]. [COLOUR_PALETTE]. [MOOD/ATMOSPHERE].
[COMPOSITION_DESCRIPTION]. [STYLE: "modern corporate design" |
"editorial layout" | "tech conference aesthetic"].
```

**API parameters:**
```json
{
  "prompt": "...",
  "aspect_ratio": "16:9",
  "style_type": "realistic",
  "negative_prompt": "blurry, low quality, distorted text",
  "seed": 42
}
```

Source: Ideogram Text & Typography (https://docs.ideogram.ai/using-ideogram/prompting-guide/2-prompting-fundamentals/text-and-typography), Ideogram Prompt Structure (https://docs.ideogram.ai/using-ideogram/prompting-guide/3-prompt-structure) [Confidence: HIGH]

**Finding 3.7: Imagen 4 Translation Rules**

Google's Imagen 4 (accessed via Vertex AI or Gemini API) excels at photorealism, especially people, landscapes, and corporate scenes.

| Characteristic | Value |
|---|---|
| Token window | Large (Gemini context: 32,768 tokens) |
| Negative prompt support | Describe unwanted elements plainly (avoid "no"/"avoid") |
| Seed support | Yes (Imagen 4 Standard and Ultra) |
| Person generation | Controls: `allow_all`, `allow_adult`, `dont_allow` |
| Best approach | Natural descriptive language, scene-first, 2-3 quality boosters max |

**Translation rules:**
1. Start with "A photo of..." to leverage photorealistic capabilities
2. Structure: Subject + Context/Background + Style + Details
3. Keep initial prompts under 50 words; expand to 100-200 for complex scenes
4. Include 2-3 quality boosters maximum: "high-quality, detailed, professional" -- more causes muddy outputs
5. Describe unwanted elements plainly without "no" or "avoid" (use positive framing)
6. Camera proximity terms: "close-up, macro, zoomed out, aerial, low-angle"
7. Person generation requires explicit parameter setting in API
8. For corporate scenes: describe professional setting, lighting, and diverse representation explicitly
9. Iterative refinement: "generate, tweak one variable, regenerate"

**Template:**
```
A [photo | professional photograph] of [SUBJECT_DESCRIPTION].
[SETTING_DESCRIPTION with time of day]. [LIGHTING: "dramatic low-angle
shot in cold blue lighting" | "soft natural daylight"].
[STYLE_MODIFIERS: 2-3 max]. [COMPOSITION_DIRECTION]. 16:9 format.
```

**API parameters (Vertex AI):**
```json
{
  "instances": [{ "prompt": "..." }],
  "parameters": {
    "sampleCount": 1,
    "aspectRatio": "16:9",
    "personGeneration": "allow_adult",
    "safetyFilterLevel": "block_few",
    "seed": 42
  }
}
```

Source: Atlabs Imagen 4 Guide (https://www.atlabs.ai/blog/imagen-4-prompting-guide), Google Developers Blog (https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/) [Confidence: HIGH]

### Sources for Area 3

1. BFL FLUX.2 Prompting Guide - https://docs.bfl.ml/guides/prompting_guide_flux2 (CRAAP: 23)
2. fal.ai FLUX 2 Klein Guide - https://fal.ai/learn/devs/flux-2-klein-prompt-guide (CRAAP: 21)
3. OpenAI GPT Image 1.5 Cookbook - https://developers.openai.com/cookbook/examples/multimodal/image-gen-1.5-prompting_guide (CRAAP: 24)
4. Ollama Blog - https://ollama.com/blog/image-generation (CRAAP: 20)
5. Ideogram Text & Typography - https://docs.ideogram.ai/using-ideogram/prompting-guide/2-prompting-fundamentals/text-and-typography (CRAAP: 22)
6. Atlabs Imagen 4 Guide - https://www.atlabs.ai/blog/imagen-4-prompting-guide (CRAAP: 18)
7. Recraft Logos & Icons - https://www.recraft.ai/docs/prompt-engineering-guide/visual-formats/logos-and-icons (CRAAP: 22)
8. Ambience AI FLUX Guide - https://www.ambienceai.com/tutorials/flux-prompting-guide (CRAAP: 19)
9. Nano Banana Prompts - https://minimaxir.com/2025/11/nano-banana-prompts/ (CRAAP: 20)

---

## Area 4: Style Consistency Across a Deck

### Key Findings

Maintaining visual coherence across 25+ images is one of the hardest problems in AI image generation for presentations. Multiple complementary techniques exist, and the most reliable approach combines several of them.

**Finding 4.1: Seed-Based Reproducibility**

Seeds enable deterministic generation -- the same seed + prompt + model produces the same image. This is essential for iterating on a single image while keeping its character stable, but insufficient alone for cross-image consistency.

| Model | Seed Support | Notes |
|-------|-------------|-------|
| FLUX 2 Pro | Yes | Full deterministic reproducibility |
| FLUX 2 Klein | Yes | Via Ollama `--seed` parameter |
| z-image-turbo | Yes | Via Ollama `--seed` parameter |
| Imagen 4 | Yes | Standard and Ultra tiers |
| GPT Image 1.5 | No | No native seed parameter; no workaround |
| Ideogram 3.0 | Yes | Supported in API |
| Recraft V4 | Yes | Supported in API |
| Gemini 3 Pro (Nano Banana Pro) | No | Autoregressive architecture lacks seed support; no workaround has measurable effect |

**Key limitation**: Seeds produce the SAME image, not SIMILAR images. A seed is useful for iterating on one image's prompt, but using the same seed with a different prompt will produce an entirely different result. Seeds do NOT transfer style across different prompts.

Source: LaoZhang Nano Banana Seed (https://blog.laozhang.ai/en/posts/nano-banana-pro-seed-parameter), BFL Guide (https://docs.bfl.ml/guides/prompting_guide_flux2) [Confidence: HIGH]

**Finding 4.2: Style Reference Images**

Style reference is the most powerful technique for deck-wide consistency. Different models implement it differently:

**FLUX Kontext (Multi-Reference):**
- Supports up to 8 reference images (10 in Playground) in a single generation
- Preserves character identity, product appearance, and visual style
- Clearly describe each reference's role: "Subject from image 1, style from image 2, background from image 3"
- Superior multi-turn consistency compared to other editing models
- Available as Kontext Pro ($0.04/image) and Kontext Max

**Ideogram 3.0 Style Codes:**
- Upload up to 3 reference images as visual guides
- Style Codes: 8-character codes that capture a discovered style for reuse
- Style presets: General, Realistic, Design, Auto (4.3 billion combinations)
- Custom styles can be saved and reused across sessions
- Turn Magic Prompt OFF when using Style References to avoid conflicts
- Style strength parameter controls how much the reference overrides model defaults

**Gemini Style Reference:**
- Supports up to 14 reference images per generation (10 object fidelity + 4 character consistency)
- Upload 2-3 reference photos from different angles for best character consistency
- Conversational editing maintains identity across sequential changes

**Recraft Custom Styles:**
- Create unlimited custom styles from reference images
- Can blend or mix styles
- Note: Style presets NOT supported for V4 models; use V3 for style presets via API
- Generate 6 images simultaneously using the Set tool for intra-set consistency

Source: BFL Kontext (https://bfl.ai/models/flux-kontext), Ideogram Style Reference (https://docs.ideogram.ai/using-ideogram/features-and-tools/reference-features/style-reference), Google Developers Blog (https://developers.googleblog.com/introducing-gemini-2-5-flash-image/), Recraft Image Sets (https://www.recraft.ai/blog/how-to-create-image-sets) [Confidence: HIGH]

**Finding 4.3: Palette Injection (Hex Codes in Every Prompt)**

Appending exact hex codes to every prompt in a deck is the simplest and most universally applicable consistency technique.

**Implementation:**
```
DECK_PALETTE_SUFFIX = """
Colour palette strictly limited to: primary #0066CC, secondary #FF6B35,
accent #2ECC71, neutral dark #2C3E50, neutral light #ECF0F1.
No other colours should appear prominently.
"""

# Append to every prompt in the deck:
final_prompt = base_prompt + " " + DECK_PALETTE_SUFFIX
```

**Model-specific hex code support:**
- **FLUX 2 Pro**: Works when paired with specific objects: "the wall is colour #2C3E50"
- **Recraft V4**: Native API parameter for colour palettes (RGB arrays)
- **GPT Image 1.5**: Understands hex codes in natural language prompts
- **Gemini**: Hex codes work with the robust text encoder (32K tokens)
- **Ideogram 3.0**: Supports colour palette as a feature alongside style reference
- **z-image-turbo**: Limited hex code support; use natural colour names instead

**Key insight**: Hex codes bias the output but do NOT guarantee exact colour matches. For precise brand compliance, post-processing colour correction is necessary.

Source: Ambience AI FLUX Guide (https://www.ambienceai.com/tutorials/flux-prompting-guide), Recraft Colour Guide (https://www.recraft.ai/blog/how-to-generate-ai-images-in-specific-colors), Nano Banana Prompts (https://minimaxir.com/2025/11/nano-banana-prompts/) [Confidence: HIGH]

**Finding 4.4: Visual Baseline Approach**

Generate one defining "hero" image first, then use it as a style reference for all subsequent images in the deck.

**Workflow:**
1. Generate the title slide hero image with full creative freedom (multiple iterations to get it right)
2. Extract the style definition: describe its colour palette, lighting quality, texture, mood, and artistic approach in 2-3 sentences
3. Use this extracted description as a "style suffix" appended to every subsequent prompt
4. Where supported (FLUX Kontext, Ideogram, Gemini), also pass the hero image as a style reference image

**Style suffix extraction template:**
```
"Consistent with the visual style established in the deck:
[COLOUR_QUALITY: e.g., warm desaturated tones with navy and gold accents],
[LIGHTING_QUALITY: e.g., soft diffused studio lighting with subtle warmth],
[TEXTURE: e.g., clean and polished with slight film grain],
[MOOD: e.g., confident and professional].
[PALETTE: exact hex codes from hero image]."
```

Source: getimg.ai Reference Guide (https://getimg.ai/guides/guide-to-using-image-references), AI for Experts Style Prompt (https://www.ai-for-experts.com/ai-workflows/how-to-generate-consistent-ai-images-using-a-simple-style-prompt/) [Confidence: MEDIUM]

**Finding 4.5: Common Style Suffixes for Presentations**

Production-tested suffixes to append to ALL prompts in a deck:

**Corporate Professional:**
```
Professional corporate aesthetic. Clean, modern, polished.
Soft diffused lighting, muted colour palette. No visual noise.
High production value, editorial quality.
```

**Tech/Startup:**
```
Modern tech aesthetic. Bold gradients, dark backgrounds with
vibrant accent colours. Futuristic, innovative feel. Clean
geometry, digital precision.
```

**Creative/Agency:**
```
Bold creative agency aesthetic. High contrast, dynamic
composition. Artistic and expressive with controlled chaos.
Premium production quality.
```

**Data/Analytics:**
```
Clean data visualisation aesthetic. Precise, structured,
clinical. Cool-toned colour palette. Grid-aligned, systematic,
information-dense but uncluttered.
```

Source: Multiple sources synthesised from Ambience AI (https://www.ambienceai.com/tutorials/flux-prompting-guide), Layer prefix/suffix documentation (https://help.layer.ai/en/articles/11128614-how-to-use-prompt-prefix-suffix-in-layer), AI for Experts (https://www.ai-for-experts.com/ai-workflows/how-to-generate-consistent-ai-images-using-a-simple-style-prompt/) [Confidence: MEDIUM]

### Sources for Area 4

1. BFL Kontext - https://bfl.ai/models/flux-kontext (CRAAP: 23)
2. Ideogram Style Reference - https://docs.ideogram.ai/using-ideogram/features-and-tools/reference-features/style-reference (CRAAP: 22)
3. Recraft Image Sets - https://www.recraft.ai/blog/how-to-create-image-sets (CRAAP: 20)
4. LaoZhang Seed Parameter - https://blog.laozhang.ai/en/posts/nano-banana-pro-seed-parameter (CRAAP: 17)
5. Nano Banana Prompts - https://minimaxir.com/2025/11/nano-banana-prompts/ (CRAAP: 20)
6. getimg.ai Reference Guide - https://getimg.ai/guides/guide-to-using-image-references (CRAAP: 17)
7. AI for Experts Style Prompt - https://www.ai-for-experts.com/ai-workflows/how-to-generate-consistent-ai-images-using-a-simple-style-prompt/ (CRAAP: 16)

---

## Area 5: The visual_direction to Prompt Translation Layer

### Key Findings

The translation layer converts the narrative-architect's `visual_direction` field (a natural-language description of the desired slide visual) into model-specific prompts. This requires a structured intermediate representation and model-specific serialisation.

**Finding 5.1: Proposed Schema for the Translation Layer**

Based on synthesis of all model-specific requirements and the JSON structured prompting approach documented across FLUX, Ideogram, and GPT Image sources:

```typescript
interface VisualDirectionInput {
  // From narrative-architect
  visual_direction: string;        // Natural language: "A dramatic cityscape at sunset..."
  slide_type: SlideType;           // "title" | "section" | "content" | "stat" | "quote" | "team" | "demo" | "icon" | "pattern" | "process"
  text_overlay_zone: TextZone;     // "left_third" | "right_third" | "top_half" | "bottom_third" | "centre" | "none"
  text_content: string;            // The actual text going on this slide
  tone: string;                    // "bold" | "contemplative" | "energetic" | "professional" | "playful"
}

interface DeckStyleContext {
  // Deck-wide settings from the design system
  brand_palette: HexColour[];      // ["#0066CC", "#FF6B35", "#2ECC71"]
  style_suffix: string;            // "Professional corporate aesthetic. Clean, modern..."
  hero_reference_url?: string;     // URL to the hero image for style reference
  style_code?: string;             // Ideogram style code if using Ideogram
  font_style: string;              // "bold sans-serif" -- for text-in-image if needed
}

interface TranslatedPrompt {
  // Output: model-specific prompt
  model: ModelId;                  // "flux2-pro" | "gpt-image-1.5" | "recraft-v4-svg" | etc.
  prompt: string;                  // The final, model-optimised prompt text
  negative_prompt?: string;        // For models that support it
  api_params: Record<string, any>; // Model-specific API parameters
  fallback_model?: ModelId;        // If primary fails, try this model
  fallback_prompt?: string;        // Prompt adjusted for fallback model
}

type SlideType =
  | "title" | "section" | "content" | "stat"
  | "quote" | "team" | "demo" | "icon"
  | "pattern" | "process";

type TextZone =
  | "left_third" | "right_third" | "top_half"
  | "bottom_third" | "centre" | "full_frame" | "none";

type HexColour = string; // "#RRGGBB"

type ModelId =
  | "ollama/z-image-turbo" | "ollama/flux2-klein"
  | "gpt-image-1.5" | "flux2-pro" | "flux-kontext-pro"
  | "recraft-v4" | "recraft-v4-svg"
  | "ideogram-3" | "imagen-4-fast" | "imagen-4-standard";
```

Source: DualView JSON Prompts Guide (https://www.dualview.ai/blog/guides/json-prompts-ai-image.html), fal.ai Model APIs (https://fal.ai/learn/devs/flux-2-prompt-guide), synthesised from all model documentation [Confidence: HIGH]

**Finding 5.2: Translation Algorithm**

The translation proceeds in 4 stages:

**Stage 1: Model Selection** (based on slide_type from Area routing table)
```
slide_type -> model mapping:
  "title"   -> flux2-pro (photorealism) or gpt-image-1.5 (complex concepts)
  "section"  -> imagen-4-fast (cost-efficient) or flux2-pro
  "content"  -> gpt-image-1.5 (prompt adherence) or recraft-v4 (design)
  "stat"     -> imagen-4-fast (minimal texture)
  "quote"    -> gpt-image-1.5 (if text embedded) or flux2-pro (background only)
  "team"     -> imagen-4-standard (people generation controls)
  "demo"     -> gpt-image-1.5 (device mockup understanding)
  "icon"     -> recraft-v4-svg (ALWAYS -- only SVG generator)
  "pattern"  -> imagen-4-fast (cost) or flux2-pro (quality)
  "process"  -> recraft-v4 (design) or gpt-image-1.5 (spatial reasoning)
```

**Stage 2: Prompt Assembly** (model-agnostic intermediate form)
```
intermediate_prompt = {
  subject: extract_subject(visual_direction),
  environment: extract_environment(visual_direction),
  lighting: extract_or_default_lighting(visual_direction, tone),
  style: deck_style_context.style_suffix,
  composition: map_text_zone_to_composition(text_overlay_zone),
  colour_palette: deck_style_context.brand_palette,
  aspect_ratio: "16:9",
  exclusions: ["text", "watermarks", "logos"]
}
```

**Stage 3: Model-Specific Serialisation** (apply translation rules from Area 3)
```
For each model, apply its specific rules:
- Token budget enforcement (truncate/compress for z-image-turbo)
- Negative prompt extraction (split exclusions for models that support it)
- Photography spec injection (camera/lens for FLUX/Imagen)
- Hex code formatting (pair with objects for FLUX, palette param for Recraft)
- Natural language expansion (paragraphs for GPT Image 1.5)
```

**Stage 4: Overlay Decision**
```
if text_overlay_zone != "none":
  overlay_config = {
    zone: text_overlay_zone,
    overlay_type: select_overlay(slide_type),  // gradient | solid | blur
    opacity: 0.4 to 0.7 depending on image complexity
  }
```

Source: Synthesised from all model documentation and existing routing research [Confidence: HIGH]

**Finding 5.3: Text Zone to Composition Mapping**

The `text_overlay_zone` field must translate to specific composition instructions per model:

| Text Zone | Composition Instruction | Prompt Phrase |
|-----------|------------------------|---------------|
| `left_third` | Subject right, space left | "subject positioned in the right two-thirds, leaving the left third clear" |
| `right_third` | Subject left, space right | "subject positioned in the left two-thirds, leaving the right third clear" |
| `top_half` | Subject bottom, space top | "subject in the lower portion of the frame, expansive sky/space above" |
| `bottom_third` | Subject upper, space bottom | "subject in the upper two-thirds, clean gradient fading at the bottom" |
| `centre` | Subject peripheral, space centre | "elements arranged around the edges, central area clear for text" |
| `full_frame` | Full overlay planned | "full-bleed image, rich detail across entire frame" (overlay handles readability) |
| `none` | No text overlay | Standard composition, no negative space requirements |

Source: Civitai Composition Guide (https://civitai.com/articles/16602/simple-composition-tricks-to-instantly-improve-ai-images-with-prompts), OpenAI Cookbook (https://developers.openai.com/cookbook/examples/multimodal/image-gen-1.5-prompting_guide) [Confidence: HIGH]

### Sources for Area 5

1. DualView JSON Prompts Guide - https://www.dualview.ai/blog/guides/json-prompts-ai-image.html (CRAAP: 18)
2. All model API documentation (see Areas 3-4 sources)
3. Existing routing research (AI-Image-Generation-Models-Research-Report-2026.md)

---

## Area 6: Common Failure Patterns and Fixes

### Key Findings

The following 15 failure patterns are the most frequently encountered when generating presentation images with AI, documented with specific prompt-level fixes.

**Failure 1: Cluttered Composition**
- Symptom: Too many elements competing for attention; image feels busy and unprofessional
- Root cause: Prompt contains more than 5 distinct elements; conflicting instructions
- Fix: Limit to 2-3 main elements. Add "minimalist, clean, professional" to the prompt. Remove secondary details. Use "simple composition with clear visual hierarchy."
- Source: GodOfPrompt (https://www.godofprompt.ai/blog/10-ai-image-generation-mistakes-99percent-of-people-make-and-how-to-fix-them) [Confidence: HIGH]

**Failure 2: Text Rendered as Gibberish**
- Symptom: In-image text is garbled, misspelled, or unreadable
- Root cause: Most diffusion models treat text as visual patterns, not linguistic symbols
- Fix: Do NOT include text in the AI-generated image. Generate the image without text, then overlay typography in pptxgenjs using addText(). If text must be in the image, use GPT Image 1.5 or Ideogram 3.0 only, keep text to 1-4 words in quotes, and spell challenging words letter-by-letter.
- Source: Stockimg.ai (https://stockimg.ai/blog/ai-and-technology/fix-your-ai-created-text), Ideogram Typography (https://docs.ideogram.ai/using-ideogram/prompting-guide/2-prompting-fundamentals/text-and-typography) [Confidence: HIGH]

**Failure 3: Wrong Aspect Ratio Feel**
- Symptom: Image feels cramped, elements are awkwardly positioned, or composition does not suit 16:9 slides
- Root cause: Generated at square or portrait ratio, or prompt does not account for wide format
- Fix: Always specify "16:9 landscape format" or "wide landscape composition" in the prompt AND set the correct pixel dimensions in the API call (1536x1024 or 1920x1080). Include "cinematic widescreen composition" for better framing.
- Source: ArtSmart Aspect Ratio Guide (https://artsmart.ai/blog/what-is-image-aspect-ratio/) [Confidence: HIGH]

**Failure 4: Brand Colour Drift**
- Symptom: Generated colours are in the right family but not matching brand hex codes
- Root cause: AI models approximate colours; hex codes bias but do not guarantee exact matches
- Fix: Three-layer approach: (1) Include hex codes in prompt paired with specific objects, (2) Use model-specific colour palette parameters (Recraft API, Ideogram colour palette), (3) Apply post-processing colour correction using Python PIL/Pillow to map dominant colours to the nearest brand colour. Use CIELAB colour space for perceptually accurate matching (deltaE < 2.3 is imperceptible).
- Source: Recraft Colour Guide (https://www.recraft.ai/blog/how-to-generate-ai-images-in-specific-colors), Pillow Documentation (https://pillow.readthedocs.io/en/stable/reference/ImageColor.html) [Confidence: HIGH]

**Failure 5: No Negative Space for Text**
- Symptom: The entire frame is filled with detail, leaving no room for text overlay
- Root cause: AI defaults to filling the frame and centring subjects
- Fix: See Area 2 in detail. Short version: explicitly describe the empty zone ("subject in the right third, leaving the left third as clear sky"), use the wider-canvas-crop technique as a fallback, and implement semi-transparent overlays in pptxgenjs as the safety net.
- Source: See Area 2 sources [Confidence: HIGH]

**Failure 6: Inconsistent Style Across Slides**
- Symptom: Each slide image looks like it was generated by a different photographer/artist
- Root cause: No style anchoring across prompts
- Fix: See Area 4 in detail. Short version: (1) Define a style suffix and append to every prompt, (2) Use model style references (FLUX Kontext, Ideogram Style Codes), (3) Include the same hex palette in every prompt, (4) Stick to ONE model for most images in a deck.
- Source: See Area 4 sources [Confidence: HIGH]

**Failure 7: Uncanny Valley People**
- Symptom: Generated people have subtle distortions (wrong finger count, dead eyes, wax-like skin)
- Root cause: Human anatomy is the hardest subject for AI to render correctly
- Fix: Use FLUX 2 Pro or Imagen 4 Standard (best at people). Include "natural, authentic body language" and "genuine expressions." Specify "shot on [camera] with [portrait lens, 85mm f/1.8]" for natural rendering. For group shots, limit to 4 or fewer people. Describe poses explicitly.
- Source: Existing research (AI-Image-Generation-Models-Research-Report-2026.md), fal.ai FLUX Guide (https://fal.ai/learn/devs/flux-2-prompt-guide) [Confidence: HIGH]

**Failure 8: Overly Generic/Stock Photo Feel**
- Symptom: Image looks like a cliched stock photo (people shaking hands in front of a generic city)
- Root cause: Prompt uses generic descriptions; model defaults to most common training examples
- Fix: Add specificity: replace "business meeting" with "three engineers reviewing a prototype PCB board at a standing desk, one pointing at a specific component." Include unexpected details that break the stock photo template. Add "authentic, editorial photography style, not stock photo."
- Source: Gemini Prompting Guide (https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/) [Confidence: MEDIUM]

**Failure 9: Low-Resolution Artefacts on Large Displays**
- Symptom: Image looks fine on a laptop but blurry/pixelated when projected at a conference
- Root cause: Generated at 1024x1024 or lower resolution
- Fix: Generate at the highest resolution the model supports. Minimum 1536x1024 for 16:9. Use FLUX 2 Max or Imagen 4 Ultra for 4K output when needed. Use API upscaling or external upscalers (Real-ESRGAN) for images that need enlargement.
- Source: BFL Guide (https://docs.bfl.ml/guides/prompting_guide_flux2), Existing research [Confidence: HIGH]

**Failure 10: Flat Lighting / No Depth**
- Symptom: Image looks flat and lifeless, lacking three-dimensionality
- Root cause: No lighting specification in prompt; model uses default even lighting
- Fix: Always specify lighting. Use directional terms: "warm golden hour sunlight streaming from the left, casting long shadows across the surface." Include at least light type, direction, and quality. For product shots: "three-point softbox lighting setup."
- Source: Ambience AI FLUX Guide (https://www.ambienceai.com/tutorials/flux-prompting-guide), fal.ai FLUX Guide (https://fal.ai/learn/devs/flux-2-prompt-guide) [Confidence: HIGH]

**Failure 11: Conflicting Style Directives**
- Symptom: Image looks incoherent -- half photorealistic, half illustrated
- Root cause: Prompt mixes competing styles: "photorealistic cartoon" or "watercolour photography"
- Fix: Choose ONE clear artistic direction per image. Do not mix mediums. State it early and explicitly: "Professional studio photography" OR "Flat vector illustration" -- never both.
- Source: fal.ai GPT Image 1.5 Guide (https://fal.ai/learn/devs/gpt-image-1-5-prompt-guide) [Confidence: HIGH]

**Failure 12: Background Transparency Edge Artefacts**
- Symptom: Cutout elements (icons, people) have jagged edges, halos, or fringing
- Root cause: Background removal is imprecise; semi-transparent edges (glow, hair) are lost
- Fix: Use models with native transparency: GPT Image 1.5 (`background: "transparent"`) or FLUX 2 Pro (`transparent_bg: true`). Set quality to "high" for better edge detection. For icons, use Recraft V4 SVG (no background removal needed). As fallback, use dedicated removal APIs (remove.bg, Clipdrop).
- Source: OpenAI Image Generation API (https://developers.openai.com/api/docs/guides/image-generation), Existing research [Confidence: HIGH]

**Failure 13: Excessive Detail in Backgrounds**
- Symptom: Background elements are as detailed as the subject, creating visual confusion
- Root cause: No depth-of-field specification; model renders everything at equal sharpness
- Fix: Add "shallow depth of field" or "soft bokeh background" or specify aperture: "f/1.4 with creamy background blur." For abstract backgrounds: "soft, out-of-focus" or "barely perceptible."
- Source: BFL Guide (https://docs.bfl.ml/guides/prompting_guide_flux2), Civitai Composition (https://civitai.com/articles/16602/simple-composition-tricks-to-instantly-improve-ai-images-with-prompts) [Confidence: HIGH]

**Failure 14: Pattern/Texture Not Tileable**
- Symptom: Pattern has visible seams or is not repeatable
- Root cause: Standard image generation does not produce seamless tiles by default
- Fix: Include "seamless repeating pattern" and "tileable" in the prompt. Use specialised pattern generation tools (PatternedAI) for critical patterns. Test tileability by duplicating the image in a 2x2 grid. For subtle textures where exact tileability is not critical, use CSS/pptxgenjs fill modes with slight overlap.
- Source: PatternedAI (https://www.patterned.ai/), Promptomania (https://promptomania.com/prompts/pattern-prompts) [Confidence: MEDIUM]

**Failure 15: API Rate Limits Causing Incomplete Decks**
- Symptom: Some slides missing images because API calls failed mid-generation
- Root cause: OpenAI Tier 1 limits to 5 images/minute; batch generation of 25 images exceeds limits
- Fix: Implement retry logic with exponential backoff. Parallelise across multiple providers (FLUX via fal.ai + GPT via OpenAI + Imagen via Google -- different rate limits). Queue all images upfront and process with a rate limiter. Use lower-cost models for less critical slides to reduce pressure on rate-limited premium models.
- Source: Existing research (AI-Image-Generation-Models-Research-Report-2026.md) [Confidence: HIGH]

### Sources for Area 6

1. GodOfPrompt - https://www.godofprompt.ai/blog/10-ai-image-generation-mistakes-99percent-of-people-make-and-how-to-fix-them (CRAAP: 16)
2. Stockimg.ai - https://stockimg.ai/blog/ai-and-technology/fix-your-ai-created-text (CRAAP: 16)
3. Recraft Colour Guide - https://www.recraft.ai/blog/how-to-generate-ai-images-in-specific-colors (CRAAP: 20)
4. ArtSmart Aspect Ratio - https://artsmart.ai/blog/what-is-image-aspect-ratio/ (CRAAP: 16)
5. All model-specific sources from Areas 2-4

---

## Area 7: Prompt Length Optimisation

### Key Findings

The optimal prompt length varies dramatically by model, and exceeding the sweet spot actively degrades quality. "There is a tipping point where adding more detail to a prompt makes results worse."

**Finding 7.1: Sweet Spot Per Model**

| Model | Min Effective | Sweet Spot | Max Before Degradation | Token Limit | Notes |
|-------|--------------|------------|----------------------|-------------|-------|
| z-image-turbo (Ollama) | 15 words | 30-50 words | ~75 words | ~100 tokens | Front-load subject; camera specs count |
| flux2-klein (Ollama) | 20 words | 30-80 words | ~100 words | 32K tokens | Structure > length |
| FLUX 2 Pro | 10 words | 30-80 words | 150+ words | 32K tokens | Prose, not keywords |
| GPT Image 1.5 | 15 words | 50-150 words | No practical limit | Very large | Handles long prompts natively |
| Recraft V4 | 10 words | 30-80 words | 150+ words | Large | Design-focused clarity |
| Ideogram 3.0 | 10 words | 40-120 words | ~160 words (~200 tokens) | ~200 tokens | Hard ceiling; lead with text |
| Imagen 4 | 15 words | 30-100 words | ~200 words | 32K tokens | 2-3 quality boosters max |
| Gemini (Nano Banana) | 10 words | 50-200 words | Very long | 32K tokens | Markdown lists and ALL CAPS emphasis |

**Key principles:**
1. **Too short** (under 15 words): Generic, uncontrolled output lacking style or composition direction
2. **Sweet spot** (30-80 words for most models): Sufficient detail for subject, lighting, composition, and style without overwhelming the model
3. **Too long** (model-dependent): Conflicting instructions, lost details, muddled outputs. Ideogram hits a hard wall at ~160 words; z-image-turbo degrades above ~75 words
4. **Exception**: GPT Image 1.5 and Gemini handle very long prompts effectively due to their transformer/LLM-based architectures

Source: BFL Guide (https://docs.bfl.ml/guides/prompting_guide_flux2), fal.ai Klein Guide (https://fal.ai/learn/devs/flux-2-klein-prompt-guide), Ideogram Prompt Structure (https://docs.ideogram.ai/using-ideogram/prompting-guide/3-prompt-structure), Nano Banana Prompts (https://minimaxir.com/2025/11/nano-banana-prompts/) [Confidence: HIGH]

**Finding 7.2: Prompt Compression Strategy for Short-Window Models**

For models with tight token budgets (z-image-turbo, Ideogram), use this compression hierarchy:

1. **Always include** (budget: 15 words): Subject + primary action/state
2. **Include if budget allows** (budget: 15 words): Lighting + camera/lens specification
3. **Include if budget allows** (budget: 10 words): Composition direction + negative space
4. **Include if budget allows** (budget: 10 words): Colour palette (hex or descriptive)
5. **Include if budget allows** (budget: 10 words): Style reference + mood
6. **Drop first if over budget**: Secondary details, background description, atmospheric effects

**Compression example:**
```
FULL (120 words -- for GPT Image 1.5):
A dramatic aerial photograph of a modern glass skyscraper piercing
through morning fog in a bustling financial district. The building is
positioned in the right two-thirds of the frame, leaving the left
third as clear negative space for title text overlay. Warm golden
hour sunlight streaming through scattered clouds illuminates the
upper floors while the lower portions remain in cool blue shadow.
Shot on Sony A7IV with 24mm f/2.8 lens. Cinematic commercial
photography style. Colour palette: navy #1B2A4A, gold #D4A373,
cool grey #8B9DAF. 16:9 landscape format. No text, no watermarks.

COMPRESSED (50 words -- for z-image-turbo):
Dramatic aerial view of glass skyscraper piercing morning fog,
golden hour sunlight. Subject in right two-thirds, clear sky on
left. Shot on Sony A7IV, 24mm f/2.8. Cinematic, navy and gold
palette. 16:9 landscape.

Negative: text, watermarks, blurry, low quality

ULTRA-COMPRESSED (30 words -- for Ideogram text-focused):
"[TITLE TEXT]" in bold sans-serif on a dramatic aerial photograph
of a glass skyscraper in golden hour fog. Navy and gold, 16:9 format.
```

Source: Synthesised from all model documentation [Confidence: HIGH]

### Sources for Area 7

1. BFL FLUX.2 Guide - https://docs.bfl.ml/guides/prompting_guide_flux2 (CRAAP: 23)
2. fal.ai FLUX 2 Klein Guide - https://fal.ai/learn/devs/flux-2-klein-prompt-guide (CRAAP: 21)
3. Ideogram Prompt Structure - https://docs.ideogram.ai/using-ideogram/prompting-guide/3-prompt-structure (CRAAP: 22)
4. Nano Banana Prompts - https://minimaxir.com/2025/11/nano-banana-prompts/ (CRAAP: 20)
5. Atlabs Imagen 4 Guide - https://www.atlabs.ai/blog/imagen-4-prompting-guide (CRAAP: 18)
6. DetailMaster Paper - https://arxiv.org/html/2505.16915v1 (CRAAP: 22)

---

## Synthesis

### 1. Core Knowledge Base

- **AI models default to centred, frame-filling compositions**: Negative space for text overlay must be explicitly engineered into every prompt through descriptive (not instructional) language specifying both where the subject goes and what fills the empty space. [Multiple sources] [Confidence: HIGH]

- **Photography specifications are the most effective quality lever across all models**: Camera model, lens focal length, aperture, and film stock references produce more precise results than generic quality modifiers like "8K" or "ultra-detailed." [BFL Guide, fal.ai Guides] [Confidence: HIGH]

- **Prompt structure matters more than prompt length**: A well-structured 50-word prompt outperforms a rambling 200-word prompt. The universal hierarchy is: Subject -> Environment -> Lighting -> Style -> Technical specs -> Composition -> Constraints. [All model documentation] [Confidence: HIGH]

- **Hex codes bias colour but do not guarantee exact matches**: For precise brand compliance, a three-layer approach is required: prompt-level hex specification, model API colour parameters, and post-processing colour correction. [Recraft, Ambience AI] [Confidence: HIGH]

- **Text rendering in AI images is solved only by GPT Image 1.5 and Ideogram 3.0**: All other models produce unreliable text. The default approach for presentation slides should be to generate images WITHOUT text and overlay typography programmatically in pptxgenjs. [Multiple sources] [Confidence: HIGH]

- **Style consistency across a 25+ slide deck requires a multi-technique approach**: No single technique (seeds, style references, colour injection) is sufficient alone. The most reliable approach combines: (1) a style suffix appended to every prompt, (2) hex palette injection, (3) model style reference features where available, and (4) sticking to one primary model per aesthetic category. [Multiple sources] [Confidence: HIGH]

- **FLUX 2 does not support negative prompts**: This architectural constraint means all unwanted elements must be addressed through positive phrasing ("clean background" instead of "no clutter") or handled in post-processing. [BFL Guide] [Confidence: HIGH]

- **Native transparency is limited to GPT Image 1.5 (background: "transparent") and FLUX 2 Pro (transparent_bg: true)**: All other models require post-processing background removal. Recraft V4 SVG output inherently supports transparency through the vector format. [OpenAI Docs, BFL Guide] [Confidence: HIGH]

### 2. Decision Frameworks

- **When the slide requires text overlay on the image**: First attempt prompt-based negative space control with explicit composition directives. If the generated image lacks adequate clear space, fall back to the semi-transparent overlay approach in pptxgenjs. For critical presentations, use BOTH (generate with negative space AND add a subtle overlay for guaranteed readability). [Area 2 sources] [Confidence: HIGH]

- **When selecting a model for a specific slide type**: Use the routing table (Area 3, Finding 3.1) to select the primary model based on slide_type. For icons, ALWAYS use Recraft V4 SVG. For text-in-image, ALWAYS use GPT Image 1.5 or Ideogram 3.0. For photorealistic scenes, use FLUX 2 Pro. For budget backgrounds, use Imagen 4 Fast. [Existing research + model documentation] [Confidence: HIGH]

- **When prompt length exceeds a model's sweet spot**: Apply the compression hierarchy (Area 7, Finding 7.2) to reduce the prompt: keep subject + lighting + composition, drop atmospheric details and secondary elements first. If the model is GPT Image 1.5, no compression is needed. [All model guides] [Confidence: HIGH]

- **When brand colour accuracy is critical**: (1) Include hex codes in the prompt associated with specific objects, (2) Use Recraft's native colour palette API parameter for design elements, (3) Apply post-processing with Python PIL using CIELAB delta-E colour mapping to snap generated colours to the nearest brand colour. Threshold: deltaE < 2.3 is imperceptible to humans. [Recraft, Pillow docs] [Confidence: MEDIUM]

- **When choosing between local (Ollama) and cloud models**: Use local models (z-image-turbo, flux2-klein) for iteration, prototyping, and privacy-sensitive content. Use cloud models (FLUX 2 Pro, GPT Image 1.5) for final production-quality assets. The quality gap between local and cloud models is significant. [Ollama Blog, model benchmarks] [Confidence: HIGH]

- **When an image needs to maintain character/object consistency across slides**: Use FLUX Kontext Pro ($0.04/image) with the initial character image as a reference. Alternative: Gemini with up to 14 reference images. For simpler style consistency (not character identity), Ideogram Style Codes or the style-suffix approach are sufficient. [BFL Kontext, Ideogram Style Reference] [Confidence: HIGH]

### 3. Anti-Patterns Catalog

- **Keyword soup instead of prose**: Writing "cat, windowsill, sunlight, fur, cozy" instead of "A tabby cat curled on a sunny windowsill, warm afternoon light illuminating striped fur." Keyword lists produce incoherent compositions; prose produces intentional ones. -> Use flowing descriptive sentences for all models, especially FLUX and GPT Image. [BFL Guide, Ambience AI Guide]

- **Using "white background" with FLUX models**: This causes blown-out, overexposed results. -> Use "clean light grey studio backdrop" or "off-white #F5F5F5 background" instead. [fal.ai FLUX 2 Klein Guide]

- **Including "no" in FLUX prompts**: FLUX does not support negative prompts; including "no blur" or "no text" can actually INCREASE the likelihood of those elements appearing (the model processes the concepts without the negation). -> Describe desired outcomes positively: "sharp focus" not "no blur." [BFL Guide]

- **Overloading quality boosters**: Adding "8K, ultra-detailed, masterpiece, best quality, highly detailed" wastes tokens and produces muddy outputs. -> Use 2-3 specific quality terms maximum: "professional studio photography, sharp focus." For Imagen 4, exceeding 3 quality boosters actively degrades output. [Atlabs Imagen 4 Guide]

- **Mixing competing styles in one prompt**: "photorealistic watercolour cartoon" confuses the model. -> Choose ONE artistic direction per image and state it clearly. [fal.ai GPT Image 1.5 Guide]

- **Relying on seeds for cross-image style consistency**: Seeds produce the SAME image, not SIMILAR images with the same style. Using seed 42 with two different prompts produces two completely different images. -> Use style reference images or style suffixes for cross-prompt consistency; use seeds only for iterating on a single prompt. [LaoZhang Seed Article]

- **Putting important composition details at the end of long prompts**: Models prioritise early prompt content. Composition and subject details buried at position 100+ of a prompt may be ignored. -> Front-load subject and composition; put style and atmospheric details later. [BFL Guide, fal.ai Guides]

- **Attempting complex diagrams or data charts with AI image generation**: No current model reliably generates accurate flowcharts, org charts, or data visualisations. Spatial relationships and numerical accuracy are poor across all models (scoring 2-3 out of 5). -> Use programmatic tools (Mermaid, python-pptx shapes, Chart.js) for diagrams and charts. Use AI generation only for decorative/conceptual process illustrations. [Existing research]

- **Ignoring aspect ratio in the prompt when the API sets it**: Even when the API parameter specifies 16:9, including "16:9 landscape format" or "cinematic widescreen composition" in the prompt text improves composition by giving the model a semantic understanding of the format, not just a pixel count. -> Always include aspect ratio description in both the prompt AND API parameters. [ArtSmart Guide, Ideogram Docs]

- **Generating text-heavy quote slides as images**: Even with GPT Image 1.5's strong text rendering, generating a full quote as an image creates rigid output that cannot adapt to font changes, localisation, or accessibility requirements. -> Generate the atmospheric background as an AI image; overlay the quote text programmatically in pptxgenjs with proper font control. [Multiple sources]

### 4. Tool and Technology Map

**Image Generation Models (Cloud API)**

| Model | Provider | Best For | Transparency | Seeds | Price/Image |
|-------|----------|----------|-------------|-------|-------------|
| GPT Image 1.5 | OpenAI | Text rendering, complex concepts, versatile | Native | No | $0.034 (med) |
| FLUX 2 Pro | Black Forest Labs (via fal.ai) | Photorealism, camera aesthetics | Native | Yes | $0.03/MP |
| FLUX Kontext Pro | Black Forest Labs | Character/style consistency | Via parent | Yes | $0.04 |
| Recraft V4 SVG | Recraft (via fal.ai) | Icons, vectors, design elements | SVG native | Yes | $0.08 |
| Ideogram 3.0 | Ideogram (via fal.ai) | Typography, text-in-image, posters | No | Yes | $0.03-0.09 |
| Imagen 4 Fast | Google (Vertex AI) | Budget backgrounds, textures | No | Yes | $0.02 |
| Imagen 4 Standard | Google (Vertex AI) | People, professional scenes | No | Yes | $0.04 |

**Image Generation Models (Local/Ollama)**

| Model | Parameters | Best For | Seeds | Price |
|-------|-----------|----------|-------|-------|
| z-image-turbo | 6B | Quick photorealistic drafts | Yes | Free (local) |
| flux2-klein 4B | 4B | Fast iteration, text rendering | Yes | Free (local, Apache 2.0) |
| flux2-klein 9B | 9B | Better quality local generation | Yes | Free (local, Non-commercial) |

**Aggregation Platforms**

| Platform | Models Available | Key Advantage |
|----------|----------------|---------------|
| fal.ai | 600+ (FLUX, Recraft, Ideogram, etc.) | Single API key, fastest inference, unified billing |
| Replicate | 500+ | Pay-per-second, simple API |
| Together AI | 100+ | Competitive pricing |

**Post-Processing Tools**

| Tool | Purpose | Integration |
|------|---------|-------------|
| Python PIL/Pillow | Colour correction, format conversion | pip install Pillow |
| remove.bg / Clipdrop | Background removal fallback | REST API |
| Real-ESRGAN | Image upscaling | Python library or API |
| colour-science (Python) | CIELAB colour matching | pip install colour-science |

### 5. Interaction Scripts

**Trigger**: "Generate images for a presentation deck"
**Response pattern**: (1) Extract slide types from narrative outline, (2) Map each slide to a model using the routing table, (3) Apply deck-wide style context (palette, style suffix, hero reference), (4) Translate each visual_direction to model-specific prompts, (5) Generate in batches respecting rate limits, (6) Apply post-processing (colour correction, overlay configs), (7) Return image paths with overlay configurations.
**Key questions to ask first**: What is the brand colour palette (hex codes)? What tone/mood should the deck convey? Are there existing brand images for style reference? Is this for screen viewing or conference projection (affects resolution)?

**Trigger**: "The generated image has no space for text"
**Response pattern**: (1) Try regenerating with strengthened composition directives ("subject offset to the far-right third, expansive clear sky filling the left two-thirds"), (2) If still insufficient, use the wider-canvas-crop technique (generate 3:1, crop to 16:9), (3) If still insufficient, accept the full-bleed image and apply a semi-transparent overlay in pptxgenjs matching the slide type's overlay pattern.
**Key questions to ask first**: Which area of the slide needs the text zone? How much text is being overlaid (title only vs. paragraph)?

**Trigger**: "The images look inconsistent across the deck"
**Response pattern**: (1) Audit the prompt set for style consistency (is the style suffix present in every prompt?), (2) Check if multiple models are being used without a unifying style bridge, (3) Verify hex palette injection in every prompt, (4) Consider regenerating using FLUX Kontext with the hero image as a style reference, (5) As a final measure, apply post-processing colour grading to harmonise the palette across all images.
**Key questions to ask first**: Which slides look out of place? Is the inconsistency in colour, style, lighting, or composition?

**Trigger**: "The icon set does not match the brand"
**Response pattern**: (1) Verify Recraft V4 SVG is being used (only model for vector icons), (2) Check that brand colours are passed as RGB arrays in the API `colors` parameter, (3) Generate the full icon set simultaneously (6 at a time via Set tool) for intra-set consistency, (4) Specify exact stroke weight and style in the prompt, (5) If colours are still off, recolour SVG paths directly using the brand hex codes.
**Key questions to ask first**: What are the exact brand hex codes? What icon style (line, filled, duotone)? What stroke weight?

**Trigger**: "Translate this visual_direction to a prompt for [model]"
**Response pattern**: (1) Parse the visual_direction for subject, environment, lighting, mood, and style, (2) Look up model-specific translation rules from Area 3, (3) Apply prompt length constraints (compress for z-image-turbo/Ideogram, expand for GPT Image 1.5), (4) Inject deck-wide context (palette suffix, style suffix), (5) Map text_overlay_zone to composition directive, (6) Format API parameters for the target model, (7) Include a fallback model and adjusted prompt.
**Key questions to ask first**: Which model is being targeted? What is the slide_type? Where does text need to go?

---

## Identified Gaps

**GAP 1: Exact token window for Ollama z-image-turbo**
No official documentation specifies the exact token limit. The ~75 token estimate is derived from the general 6B model class and practitioner reports that "prompts exceeding 100 words create confusion." The official Ollama blog provides parameter controls but no token window specification.
- Queries attempted: "Ollama z-image-turbo token window limit", "z-image-turbo prompt length maximum"
- Recommendation: Conduct empirical testing with progressively longer prompts to find the degradation point.

**GAP 2: Post-processing colour correction pipeline for exact brand matching**
While individual techniques exist (CIELAB deltaE matching, PIL colour manipulation, Recraft colour palette API), no documented end-to-end pipeline exists for snapping AI-generated image colours to an exact brand palette while preserving image quality. The claim that "current image generators do not hard-lock exact HEX values" is well-established, but the correction workflow remains ad-hoc.
- Queries attempted: "AI image brand color drift fix post-generation color correction technique", "AI image color correction post-processing match brand palette hex colors Python PIL"
- Recommendation: Build and test a custom correction pipeline using Python PIL + colour-science library.

---

## Cross-References

- **Negative space (Area 2) directly determines overlay strategy (Area 5)**: The translation layer must decide at generation time whether to attempt prompt-based negative space or plan for a pptxgenjs overlay. This decision feeds into the `overlay_config` output of the translation layer.

- **Model token limits (Area 7) constrain the translation layer (Area 5)**: The translation algorithm must compress the assembled prompt to fit each model's sweet spot. The compression hierarchy (Area 7, Finding 7.2) should be implemented as a post-assembly step in the translation pipeline.

- **Style consistency (Area 4) and the style suffix pattern feed directly into every template (Area 1)**: All 10 slide-type templates should be treated as base templates to which the deck-wide style suffix, hex palette, and model-specific formatting are appended by the translation layer.

- **Text gibberish failure (Area 6, Failure 2) validates the overlay approach (Area 2, Finding 2.5)**: The consistent finding that text rendering is unreliable in most models reinforces the architectural decision to separate image generation from text overlay. Only GPT Image 1.5 and Ideogram 3.0 should ever receive text-in-image requests, and even then, the pptxgenjs overlay approach should be the default.

- **Recraft V4's SVG output (Area 3, Finding 3.5) eliminates multiple failure patterns**: SVG icons do not suffer from resolution artefacts (Failure 9), transparency edge issues (Failure 12), or colour drift (Failure 4 -- SVG paths can be directly recoloured). This reinforces Recraft as the mandatory choice for icons.

- **The wider-canvas-crop technique (Area 2, Finding 2.4) complements the translation layer's text zone mapping (Area 5, Finding 5.3)**: When prompt-based composition control fails, the translation layer can output a `wider_canvas: true` flag that triggers 3:1 generation followed by automated cropping to 16:9.

- **FLUX's lack of negative prompts (Area 3) means the failure fix for cluttered composition (Area 6, Failure 1) must use positive phrasing exclusively**: The translation layer must transform any "no X" constraints into "clean, [positive alternative]" when the target model is FLUX.
