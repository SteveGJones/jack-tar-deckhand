# Interaction Matrix -- Jack-Tar Deckhand

> Generated from canonical model: `jack-tar-deckhand.json` v1.0.0
> Date: 2026-03-28

This document maps all interactions between entities in the Jack-Tar Deckhand architecture. Interactions are grouped by functional concern: pipeline flow, provider discovery, image generation routing, and QA/review loops.

---

## Full Interaction Table

| ID | Source | Target | Type | Data Flows |
|---|---|---|---|---|
| `int-speaker-to-conductor` | Speaker | Deck Conductor | invocation | TalkBrief, Creative decisions, Budget approval |
| `int-conductor-to-design` | Deck Conductor | Design Services | invocation | TalkBrief, Brand assets (optional) |
| `int-conductor-to-content` | Deck Conductor | Content Services | invocation | TalkBrief, StyleGuide |
| `int-conductor-to-image` | Deck Conductor | Image Services | invocation | SlideOutline (visual_direction), StyleGuide (palette), Budget constraints |
| `int-conductor-to-assembly` | Deck Conductor | Assembly & QA Services | invocation | SlideOutline, StyleGuide, ImageManifest, ChartManifest, SpeakerNotes |
| `int-conductor-to-speaker-output` | Deck Conductor | Speaker | delivery | .pptx file, QAReport, Presentation Review, Cost summary |
| `int-conductor-to-reviewer` | Deck Conductor | Presentation Reviewer | invocation | Review request (post-QA) |
| `int-bridge-discovery` | Image Routing & Discovery | Ollama | probe | Availability check (HTTP) |
| `int-bridge-discovery-openai` | Image Routing & Discovery | OpenAI API | probe | OPENAI_API_KEY env var check |
| `int-bridge-discovery-google` | Image Routing & Discovery | Google Vertex AI | probe | GOOGLE_CLOUD_PROJECT env var check |
| `int-bridge-discovery-fal` | Image Routing & Discovery | FAL.ai | probe | FAL_KEY env var check |
| `int-bridge-discovery-recraft` | Image Routing & Discovery | Recraft API | probe | RECRAFT_API_KEY env var check |
| `int-bridge-to-ollama-skills` | Image Routing & Discovery | Ollama Image Generation | invocation | Routed generation request |
| `int-bridge-to-cloud-skills` | Image Routing & Discovery | Cloud Image Generation | invocation | Routed generation request |
| `int-ollama-skills-to-ollama` | Ollama Image Generation | Ollama | invocation | REST API inference call |
| `int-cloud-skills-to-openai` | Cloud Image Generation | OpenAI API | invocation | GPT Image 1.5 generation |
| `int-cloud-skills-to-google` | Cloud Image Generation | Google Vertex AI | invocation | Imagen 4 generation |
| `int-cloud-skills-to-fal` | Cloud Image Generation | FAL.ai | invocation | FLUX.2 / Ideogram generation |
| `int-cloud-icon-to-recraft` | Cloud Icon Generation | Recraft API | invocation | SVG icon generation |
| `int-cloud-icon-to-fal` | Cloud Icon Generation | FAL.ai | invocation | Recraft V4 access via aggregator |
| `int-chart-to-matplotlib` | Chart Rendering | Matplotlib | invocation | Headless chart generation |
| `int-assembly-to-pptxgenjs` | PPTX Build | PptxGenJS | invocation | .pptx file generation |
| `int-gen-skills-to-expert` | Ollama Image Generation | Image Generation Expert | consultation | Prompt engineering, quality scoring |
| `int-cloud-skills-to-expert` | Cloud Image Generation | Image Generation Expert | consultation | Model-specific prompt translation |
| `int-bridge-to-expert` | Image Routing & Discovery | Image Generation Expert | consultation | Model selection advice |
| `int-qa-correction-loop` | Visual QA | Deck Conductor | feedback | QA findings for correction cycle (max 2) |
| `int-reviewer-feedback` | Presentation Reviewer | Deck Conductor | feedback | Structured review for Speaker decision |

---

## Group 1: Pipeline Flow

The primary execution flow from Speaker input to finished deck output.

```
Speaker
  |
  | [invocation] TalkBrief, creative decisions, budget approval
  v
Deck Conductor
  |
  |--[1. invocation]--> Design Services
  |                     (TalkBrief, brand assets)
  |                     Returns: StyleGuide
  |
  |--[2. invocation]--> Content Services
  |                     (TalkBrief, StyleGuide)
  |                     Returns: SlideOutline, SpeakerNotes
  |
  |--[3. invocation]--> Image Services
  |                     (SlideOutline, StyleGuide, budget constraints)
  |                     Returns: ImageManifest, ChartManifest
  |
  |--[4. invocation]--> Assembly & QA Services
  |                     (SlideOutline, StyleGuide, ImageManifest,
  |                      ChartManifest, SpeakerNotes)
  |                     Returns: .pptx, QAReport, Review
  |
  | [delivery] .pptx, QAReport, Presentation Review, cost summary
  v
Speaker
```

| # | Source | Target | Type | Data Flows |
|---|---|---|---|---|
| 1 | Speaker | Deck Conductor | invocation | TalkBrief, Creative decisions, Budget approval |
| 2 | Deck Conductor | Design Services | invocation | TalkBrief, Brand assets (optional) |
| 3 | Deck Conductor | Content Services | invocation | TalkBrief, StyleGuide |
| 4 | Deck Conductor | Image Services | invocation | SlideOutline (visual_direction), StyleGuide (palette), Budget constraints |
| 5 | Deck Conductor | Assembly & QA Services | invocation | SlideOutline, StyleGuide, ImageManifest, ChartManifest, SpeakerNotes |
| 6 | Deck Conductor | Speaker | delivery | .pptx file, QAReport, Presentation Review, Cost summary |

---

## Group 2: Provider Discovery

At pipeline startup, the imagegen-bridge probes all potential image generation providers to build an AvailableProviders manifest. This determines which generation paths are viable for this run.

```
Image Routing & Discovery
  |
  |--[probe]--> Ollama          (HTTP health check: localhost:11434)
  |--[probe]--> OpenAI API      (env: OPENAI_API_KEY)
  |--[probe]--> Google Vertex AI (env: GOOGLE_CLOUD_PROJECT)
  |--[probe]--> FAL.ai          (env: FAL_KEY)
  |--[probe]--> Recraft API     (env: RECRAFT_API_KEY)
  |
  v
AvailableProviders manifest
```

| # | Source | Target | Type | Detection Method |
|---|---|---|---|---|
| 1 | Image Routing & Discovery | Ollama | probe | HTTP health check to localhost:11434 |
| 2 | Image Routing & Discovery | OpenAI API | probe | Check OPENAI_API_KEY environment variable |
| 3 | Image Routing & Discovery | Google Vertex AI | probe | Check GOOGLE_CLOUD_PROJECT environment variable |
| 4 | Image Routing & Discovery | FAL.ai | probe | Check FAL_KEY environment variable |
| 5 | Image Routing & Discovery | Recraft API | probe | Check RECRAFT_API_KEY environment variable |

---

## Group 3: Image Generation Routing

Once providers are discovered, the imagegen-bridge routes each image request to the best available provider based on asset type, quality requirements, and budget. The Image Generation Expert is consulted for prompt engineering and model selection advice.

```
Image Routing & Discovery
  |
  |--[consultation]--> Image Generation Expert
  |                    (model selection advice)
  |
  |--[invocation]--> Ollama Image Generation --[invocation]--> Ollama
  |                  |
  |                  |--[consultation]--> Image Generation Expert
  |                                       (prompt engineering, quality scoring)
  |
  |--[invocation]--> Cloud Image Generation
                     |
                     |--[consultation]--> Image Generation Expert
                     |                    (model-specific prompt translation)
                     |
                     |--[invocation]--> OpenAI API     (GPT Image 1.5)
                     |--[invocation]--> Google Vertex AI (Imagen 4)
                     |--[invocation]--> FAL.ai          (FLUX.2, Ideogram)

Cloud Icon Generation
  |--[invocation]--> Recraft API  (native SVG)
  |--[invocation]--> FAL.ai       (Recraft V4 via aggregator)

Chart Rendering
  |--[invocation]--> Matplotlib   (headless 300 DPI)
```

| # | Source | Target | Type | Data Flows |
|---|---|---|---|---|
| 1 | Image Routing & Discovery | Image Generation Expert | consultation | Model selection advice given available providers |
| 2 | Image Routing & Discovery | Ollama Image Generation | invocation | Routed generation request (local assets) |
| 3 | Image Routing & Discovery | Cloud Image Generation | invocation | Routed generation request (high-quality assets) |
| 4 | Ollama Image Generation | Ollama | invocation | REST API inference call |
| 5 | Ollama Image Generation | Image Generation Expert | consultation | Prompt engineering, quality scoring |
| 6 | Cloud Image Generation | OpenAI API | invocation | GPT Image 1.5 generation |
| 7 | Cloud Image Generation | Google Vertex AI | invocation | Imagen 4 generation |
| 8 | Cloud Image Generation | FAL.ai | invocation | FLUX.2 / Ideogram generation |
| 9 | Cloud Image Generation | Image Generation Expert | consultation | Model-specific prompt translation |
| 10 | Cloud Icon Generation | Recraft API | invocation | SVG icon generation |
| 11 | Cloud Icon Generation | FAL.ai | invocation | Recraft V4 access via aggregator |
| 12 | Chart Rendering | Matplotlib | invocation | Headless chart generation at 300 DPI |
| 13 | PPTX Build | PptxGenJS | invocation | .pptx file generation engine |

---

## Group 4: QA / Review Loop

After assembly, the deck passes through two quality gates. The Visual QA runs automated checks; the Presentation Reviewer applies human-judgement-level assessment. Both feed back to the Deck Conductor, which may trigger correction cycles.

```
Deck Conductor
  |
  |--[invocation]--> Assembly & QA Services
  |                  |
  |                  |--> PPTX Build --[invocation]--> PptxGenJS
  |                  |
  |                  |--> Visual QA
  |                       |
  |                       |--[feedback]--> Deck Conductor
  |                                        (QA findings, max 2 correction cycles)
  |
  |--[invocation]--> Presentation Reviewer
                     |
                     |--[feedback]--> Deck Conductor
                                      (structured review for Speaker decision)
```

| # | Source | Target | Type | Data Flows |
|---|---|---|---|---|
| 1 | Deck Conductor | Assembly & QA Services | invocation | All artefacts for assembly |
| 2 | PPTX Build | PptxGenJS | invocation | .pptx file generation |
| 3 | Visual QA | Deck Conductor | feedback | QA findings for correction cycle (max 2 iterations) |
| 4 | Deck Conductor | Presentation Reviewer | invocation | Review request after QA passes |
| 5 | Presentation Reviewer | Deck Conductor | feedback | Structured review with prioritised recommendations |

### Correction Cycle Logic

1. Deck Conductor invokes PPTX Build, then Visual QA.
2. If Visual QA returns `fail`, the Conductor re-invokes the producing service with corrective instructions.
3. Maximum 2 correction cycles. After 2 failures, escalate to Speaker.
4. If Visual QA returns `pass` or `pass_with_warnings`, the Conductor invokes the Presentation Reviewer.
5. Reviewer feedback goes to the Conductor, which presents it to the Speaker for decision.

---

## Interaction Type Summary

| Type | Count | Description |
|---|---|---|
| invocation | 16 | One entity calls another to perform work |
| probe | 5 | Runtime discovery of provider availability |
| consultation | 3 | Advisory request to an AI Persona (no side effects) |
| delivery | 1 | Final output delivered to the Speaker |
| feedback | 2 | Quality findings returned to the Conductor for action |
| **Total** | **27** | |
