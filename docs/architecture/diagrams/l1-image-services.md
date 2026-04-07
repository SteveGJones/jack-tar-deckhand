# L1 Image Services — Drill-Down

> **Source**: `jack-tar-deckhand.json` v1.4.0 | **Level**: L1 > L2 | **Parent**: Presentation Engineering | **Date**: 2026-04-03

![Image Services L2](jack-tar-deckhand-image-services-l2.svg)

## L2 Capabilities

| Capability | Type | Skill | System Actor |
|------------|------|-------|--------------|
| Image Routing & Discovery | Skill | `imagegen-bridge` | -- (probes all) |
| Ollama Image Generation | Skill | `ollama-generate-image` | Ollama |
| Ollama Icon Generation | Skill | `ollama-generate-icon` | Ollama |
| Ollama Pattern Generation | Skill | `ollama-generate-pattern` | Ollama |
| Ollama Diagram Generation | Skill | `ollama-generate-diagram` | Ollama |
| Cloud Image Generation | Skill | `cloud-generate-image` | OpenAI, Google Vertex AI, FAL.ai |
| Cloud Icon Generation | Skill | `cloud-generate-icon` | Recraft, FAL.ai |
| Chart Rendering | Skill | `chart-renderer` | Matplotlib |
| Image Post-Processing | Skill | `image-processor` | -- |
| SmartArt Rendering | Skill | `smartart-renderer` | Mermaid CLI, Vega-Lite CLI |
| Image Generation Expert | AI Persona | -- | -- (advisory only) |
| Image Reviewer | AI Persona | -- | -- (quality gate) |
| Prompt Engineer | AI Persona | -- | -- (prompt engineering) |

## System Actor Details

| System Actor | Type | Models/Capabilities | Cost |
|-------------|------|---------------------|------|
| **Ollama** | Local runtime | z-image-turbo, flux2-klein | Free (local HW) |
| **OpenAI API** | Cloud API | GPT Image 1.5 | $0.009-$0.133/image |
| **Google Vertex AI** | Cloud API | Imagen 4, Gemini Flash | ~$0.02/image |
| **FAL.ai** | Cloud aggregator | FLUX.2 Pro, Recraft V4, Ideogram 3.0 | Varies |
| **Recraft API** | Cloud API | Recraft V4 (native SVG) | $0.04-$0.30/image |
| **Matplotlib** | Python library | Headless charts, 300 DPI, Agg backend | Free |
| **Mermaid CLI** | Node.js CLI | mmdc — Mermaid DSL to SVG | Free |
| **Vega-Lite CLI** | Node.js CLI | vl2svg — Vega-Lite spec to SVG | Free |

## Data Contract Summary

| Contract | Direction | Description |
|----------|-----------|-------------|
| **SlideOutline** (visual_direction) | In | Per-slide visual direction from Content Services |
| **StyleGuide** (palette) | In | Brand palette for colour enforcement |
| **Budget constraints** | In | Per-image and total budget caps from Conductor |
| **SmartArtSpec** | In | Engine-specific structured data from Content Services |
| **ImageManifest** | Out | Generated image files with metadata (incl. enrichment with smartart_ref) |
| **ChartManifest** | Out | Generated chart images with metadata |
| **SmartArtManifest** | Out | Rendered SmartArt graphics with comparator results |
