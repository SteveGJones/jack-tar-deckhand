# Synthesis: imagegen-bridge

> Distilled from: research/05-multi-model-routing-pipeline.md, research/13-cost-optimisation-caching.md, docs/architecture/architecture-overview.md, docs/architecture/data-contracts.md

## 1. Core Knowledge Base

- The imagegen-bridge is the TOP-LEVEL image orchestrator within Image Services. It is invoked by the Deck Conductor and delegates to individual generation skills. It never generates images directly.
- Provider discovery runs at the start of every image generation phase. Ollama is probed via HTTP health check to localhost:11434. Cloud providers are detected via environment variables: OPENAI_API_KEY, GOOGLE_CLOUD_PROJECT, FAL_KEY, RECRAFT_API_KEY.
- The system operates on a "use what's available" principle -- it works with Ollama alone, cloud APIs alone, or any combination.

## 2. Routing Matrix (from Research 05 Finding 1.1)

| visual_type        | Draft Mode            | Production Mode        |
|--------------------|-----------------------|------------------------|
| hero_image         | ollama-image          | cloud-generate-image   |
| icon_set           | cloud-generate-icon   | cloud-generate-icon    |
| pattern_background | ollama-pattern        | cloud-generate-image   |
| diagram            | ollama-diagram        | ollama-diagram         |
| chart              | render_chart.py       | render_chart.py        |
| none               | skip                  | skip                   |

Icons always route to cloud because Recraft V4 is the ONLY model producing native SVG output. Diagrams always route to Ollama because AI-generated diagrams have text quality limitations regardless of model; the overlay pattern handles labels. Charts always route to programmatic rendering via matplotlib -- never AI-generated.

## 3. Fallback Chains (from Research 05 Finding 5.2)

hero_image: cloud-generate-image (FLUX.2 Pro) -> cloud-generate-image (GPT Image 1.5) -> ollama-image -> placeholder
icon_set: cloud-generate-icon (Recraft V4) -> cloud-generate-icon (FAL Recraft) -> placeholder (unicode symbol)
pattern_background: cloud-generate-image (Imagen 4 Fast) -> cloud-generate-image (FLUX.2 Pro) -> ollama-pattern -> placeholder
diagram: ollama-diagram -> placeholder
chart: render_chart.py -> placeholder (should never fail)

## 4. Budget Degradation (from Research 13 Section 4)

| State            | Threshold  | Image Strategy                                 |
|------------------|------------|------------------------------------------------|
| ALLOW            | 0-70% spent| Full multi-model routing                       |
| ALLOW_WITH_CAPS  | 70-90%     | Downgrade heroes to Imagen 4 Fast, skip decorative |
| DEGRADE          | 90-100%    | All remaining via Ollama (free)                |
| TYPOGRAPHY_ONLY  | 100%       | No image generation, placeholders only         |

## 5. Draft vs Production Lifecycle

Draft mode: uses Ollama for quick composition testing (free), cloud at reduced quality for prompt refinement. Production mode: full-quality cloud rendering at approved resolution. The Deck Conductor manages the lifecycle; the bridge just respects the --mode parameter.

## 6. ImageManifest Contract

File: ./tmp/deck/image-manifest.json. Required fields per image: image_id, slide_number, file_path, status. Status enum: generated, cached, placeholder, failed. Summary object tracks counts and timing.

## 7. ChartManifest Contract

File: ./tmp/deck/chart-manifest.json. Required fields per chart: chart_id, slide_number, file_path, chart_type, status. Status enum: rendered, cached, failed.

## 8. Anti-Patterns

- Never draft icons locally (raster vs SVG modality mismatch)
- Never draft text-heavy slides locally (garbled text makes assessment impossible)
- Never route all images through a single cloud provider (outage risk)
- Never chase local detail quality -- stop when composition is right
