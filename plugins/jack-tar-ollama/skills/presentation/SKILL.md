---
name: ollama-presentation
description: Create visually rich PowerPoint presentations with AI-generated images, icons, diagrams, and patterns. Orchestrates the pptx skill with image generation skills to produce slides that aren't just text-on-white.
argument-hint: "presentation topic or description" [--slides N] [--output PATH] [--style STYLE] [--prompt-file FILE]
allowed-tools: Bash(python *), Bash(node *), Bash(curl *), Bash(ollama *), Bash(npm *), Bash(pip *), Bash(pdftoppm *), Read, Write, Glob, Edit
---

# /ollama-presentation

Create a PowerPoint presentation with AI-generated visual assets. You orchestrate two capabilities:
1. **Image generation** — via `src/generate_image.py` and the `ollama-image-expert` agent for custom images, icons, diagrams, and patterns
2. **Slide creation** — via pptxgenjs (the pptx skill's creation engine)

Consult the `ollama-image-expert` agent for all image generation knowledge, including the "Images for Presentations" section specifically.

## Parse Arguments

Parse `$ARGUMENTS` for:
- **Topic/description**: The quoted text describing what the presentation is about
- **--slides N**: Approximate number of slides (default: 8-12)
- **--output PATH**: Output path (default: `output/presentation-YYYYMMDD-HHMMSS.pptx`)
- **--style STYLE**: Visual style — `corporate`, `creative`, `technical`, `minimal` (default: infer from topic)
- **--prompt-file PATH**: Read a detailed brief from a file
- **--no-images**: Skip image generation (text and shapes only, much faster)

If no topic and no `--prompt-file`, stop and ask what the presentation is about.

## Step 1: Plan the Presentation

Before generating anything, plan the full deck. Create a slide plan with:

For each slide:
- **Slide number and title**
- **Content summary** (key points, data, or message)
- **Layout type**: title-slide, two-column, icon-grid, stat-callout, image-feature, diagram, section-divider, closing
- **Visual asset needed**: what image/icon/diagram/pattern would enhance this slide
- **Asset generation approach**: which skill and prompt to use

**Visual asset strategy by layout:**

| Layout | Visual Asset | Generation Approach |
|--------|-------------|-------------------|
| Title slide | Background pattern or hero image | `/ollama-pattern` for texture background, or `/ollama-image` for hero |
| Two-column | Content illustration | `/ollama-image` with topic-specific prompt |
| Icon grid | 3-4 custom icons | `/ollama-icon --style flat` for each concept |
| Stat callout | Background accent or pattern | `/ollama-pattern` or use shapes only |
| Image feature | Full or half-bleed image | `/ollama-image` with composition-aware prompt |
| Diagram | Technical diagram | `/ollama-diagram --type flowchart/architecture` |
| Section divider | Subtle pattern or gradient image | `/ollama-pattern --style abstract` |
| Closing | Echo title slide background | Reuse title slide assets |

**Not every slide needs a generated image.** Charts, shapes, and icons from react-icons are faster and sometimes better. Use generated images where they add genuine value — hero shots, illustrations of concepts, custom diagrams, branded patterns.

## Step 2: Choose Color Palette and Typography

Pick a palette that matches the topic (don't default to blue). Reference the pptx skill's palette table or create a custom one. Define:
- Primary color (60-70% weight)
- Secondary color
- Accent color
- Background colors (dark for title/closing, light for content)
- Text colors (primary, muted)

Pick a font pairing — header font with personality, clean body font.

## Step 3: Generate Visual Assets

Generate all needed images BEFORE building slides. Store them in a temporary directory:

```bash
mkdir -p /tmp/presentation-assets
```

For each planned visual asset, run the appropriate generation:

**For content images:**
```bash
python src/generate_image.py --prompt "PROMPT" --model "MODEL" --output /tmp/presentation-assets/slide-N-image.png --width WIDTH --height HEIGHT
```

Image sizing for slides (16:9 at 10" × 5.625"):
- **Full-bleed background**: 1920x1080 (or 1024x576 for faster generation)
- **Half-slide image** (left or right): 960x1080 (or 512x576)
- **Content image in layout**: 768x768 or 1024x768
- **Icon**: 512x512

Consult the `ollama-image-expert` agent for prompt strategies, especially the "Images for Presentations" section for slide-specific guidance.

**For icons** — if react-icons doesn't have what you need:
```bash
python src/generate_image.py --prompt "ICON PROMPT" --model "x/flux2-klein" --output /tmp/presentation-assets/icon-N.png --width 512 --height 512 --steps 20
```

**For diagrams:**
```bash
python src/generate_image.py --prompt "DIAGRAM PROMPT" --model "x/flux2-klein" --output /tmp/presentation-assets/diagram-N.png --width 1024 --height 768 --steps 20
```

**For patterns/textures:**
```bash
python src/generate_image.py --prompt "PATTERN PROMPT" --model "x/z-image-turbo" --output /tmp/presentation-assets/pattern-N.png --width 1024 --height 1024 --steps 8
```

**Review each generated image** using the Read tool. If an image is poor quality or doesn't match the intent, regenerate with a refined prompt. Don't waste time on perfection — one retry is usually enough for presentations.

## Step 4: Build the Presentation

Ensure pptxgenjs is installed:
```bash
which pptxgenjs || npm install -g pptxgenjs
```

Write a Node.js script that builds the presentation using pptxgenjs. Follow the pptx skill's creation guide (`pptxgenjs.md`) for API reference. Key points:

- Use `slide.addImage({ path: "/tmp/presentation-assets/slide-N-image.png", ... })` for generated images
- Use `slide.background = { path: "/tmp/presentation-assets/pattern-N.png" }` for pattern backgrounds
- Set proper sizing with `sizing: { type: 'cover', w: W, h: H }` for backgrounds
- Use `sizing: { type: 'contain', w: W, h: H }` for content images to preserve aspect ratio

**Follow pptx skill design guidelines:**
- Every slide needs a visual element
- Don't repeat the same layout across slides
- Left-align body text, center only titles
- 0.5" minimum margins
- Never use `#` prefix on hex colors
- Don't reuse option objects (pptxgenjs mutates them)
- NEVER use accent lines under titles

Run the script:
```bash
node /tmp/presentation-build.js
```

## Step 5: QA

**Content QA:**
```bash
pip install "markitdown[pptx]" 2>/dev/null
python -m markitdown OUTPUT_PATH
```

Check for missing content, wrong order, typos.

**Visual QA:**
Convert to images and review:
```bash
python scripts/office/soffice.py --headless --convert-to pdf OUTPUT_PATH 2>/dev/null || soffice --headless --convert-to pdf OUTPUT_PATH
pdftoppm -jpeg -r 150 OUTPUT_PDF slide
```

Read the slide images with the Read tool. Check for:
- Overlapping elements
- Text overflow or cut off
- Generated images that look wrong or garbled
- Low contrast text
- Uneven spacing

Fix any issues found. Re-verify after fixes.

## Step 6: Clean Up and Report

```bash
rm -rf /tmp/presentation-assets /tmp/presentation-build.js
```

Report:
- Path to the generated .pptx file
- Number of slides
- Number of AI-generated images used
- The color palette and fonts chosen
- Any known limitations (e.g., "text in the diagram on slide 5 may not be fully legible")

## When to Skip Image Generation

Use `--no-images` or skip image generation when:
- The user needs a quick text-focused deck
- Ollama isn't running
- Speed matters more than visuals
- The topic is better served by charts and data than illustrations

In these cases, use shapes, react-icons, charts, and strong typography to create visual interest without generated images.
