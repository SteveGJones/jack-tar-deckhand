---
name: ollama-diagram
description: Generate technical diagrams — flowcharts, architecture diagrams, system diagrams, and process flows. Uses FLUX model for better text rendering and spatial accuracy.
argument-hint: "diagram description" [--type flowchart|architecture|sequence|network] [--output PATH] [--model MODEL]
allowed-tools: Bash(python *), Bash(curl *), Bash(ollama *), Read, Glob
---

# /ollama-diagram

Generate a technical diagram. Diagrams need text rendering, spatial precision, and clean layouts — so the default model is `x/flux2-klein` which excels at these.

Consult the `ollama-image-expert` agent for model-specific prompt strategies, especially the FLUX spatial hierarchy approach.

## Parse Arguments

Parse `$ARGUMENTS` for:
- **Description**: The quoted text describing the diagram
- **--type TYPE**: `flowchart`, `architecture`, `sequence`, `network`, or `general` (default: `general`)
- **--output PATH**: Output path. Default: `output/diagram-YYYYMMDD-HHMMSS.png`
- **--model MODEL**: Override model (default: `x/flux2-klein`)
- **--width INT**: Width (default: 1024)
- **--height INT**: Height (default: 768 — landscape default for diagrams)
- **--prompt-file PATH**: Read description from a file

If no description and no `--prompt-file`, stop and ask the user what diagram they need.

## Discover Available Models

Discover available image generation models:

```bash
ollama list
```

Filter the output for models with the `x/` prefix — these are image generation models (e.g., `x/z-image-turbo`, `x/flux2-klein`). Machines with more memory may have more models available.

- If `--model` is specified: verify it appears in the list. If not, tell the user it's not available, show them the available `x/` models, and suggest `ollama pull MODEL`.
- If `--model` is NOT specified: default to `x/flux2-klein` if available (better for diagrams and text). If not, use any available `x/` model. If NO `x/` models are available, tell the user to pull one: `ollama pull x/flux2-klein`.

## Build the Diagram Prompt

Take the user's description and wrap it in diagram-optimized prompt structure using FLUX's spatial hierarchy approach.

**For flowchart:**
> A clean technical flowchart diagram. [DESCRIPTION]. The diagram flows from top to bottom (or left to right). Each step is in a rounded rectangle box with clear readable text labels inside. Decision points use diamond shapes with Yes/No labels on the outgoing arrows. Arrows connect the boxes showing the flow direction. Professional flat design, clean sans-serif typography, light grey background, dark blue boxes with white text. No decorative elements. The text must be sharp and legible.

**For architecture:**
> A professional system architecture diagram. [DESCRIPTION]. Components are shown as labeled rectangular boxes arranged in logical layers or groups. Larger boundary rectangles group related components. Arrows between components are labeled with the type of interaction (API call, data flow, etc.). Clean flat design, professional color coding to distinguish component types, sans-serif typography, light background. All text labels must be clearly readable.

**For sequence:**
> A sequence diagram showing interactions between participants. [DESCRIPTION]. Participants are shown as labeled boxes across the top. Vertical dashed lifelines extend downward from each participant. Horizontal arrows between lifelines show messages, labeled with the message name. Time flows from top to bottom. Clean technical style, sans-serif font, light background, clearly readable text labels on all arrows and participants.

**For network:**
> A network topology diagram. [DESCRIPTION]. Network devices are shown as labeled icons or simple shapes (rectangles for servers, circles for endpoints, cloud shapes for external networks). Connection lines between devices are labeled with protocols or link types. Logical groupings are shown with dashed boundary boxes. Clean technical style, professional color coding, all labels clearly readable.

**For general (default):**
> A clean technical diagram. [DESCRIPTION]. Use simple geometric shapes (rectangles, circles, diamonds) with clear text labels inside each shape. Connect shapes with labeled arrows showing relationships or flow. Professional flat design with a clean color palette. Sans-serif typography. Light grey or white background. All text must be sharp and legible. Prioritize clarity and readability over decorative elements.

## Generate

Run the helper script:

```bash
python src/generate_image.py --prompt "BUILT PROMPT" --model "MODEL" --output "PATH" --width WIDTH --height HEIGHT --steps 20
```

Steps default to 20 for flux (diagrams need the extra quality for text rendering).

## Review (Optional)

After generation, read the image and assess whether the text labels are legible. If they are garbled or unreadable (common with diffusion models), inform the user honestly:

"The diagram structure looks [good/reasonable], but some text labels are [garbled/partially readable]. Diffusion models often struggle with precise text. For production diagrams, consider using this as a layout reference and recreating it with a proper diagramming tool."

Do NOT score this formally or enter a refinement loop unless the user asked for `--iterations`. Just give an honest one-line assessment.

## Report Result

Report:
- Path to the generated diagram
- The model used
- A brief honest note on text legibility

One shot. No follow-up.
