# Jack-Tar Deckhand — BSA Architecture Design

**Date:** 2026-03-29
**Status:** Draft — pending review
**Authors:** Steve Jones, Claude

---

## 1. What We're Building

A suite of Claude Code skills and agents that generate conference-quality PowerPoint presentations. A speaker describes their talk, and the system delivers a polished, stage-ready .pptx — complete with AI-generated visuals, consistent branding, typographic hierarchy, and speaker notes.

This is NOT a standalone application. It runs inside Claude Code as skills (SKILL.md files), agents (.md files), and helper scripts (Python/JS). Claude Code is the runtime.

## 2. Architecture Approach

**Approach B: Domain-Centric Hierarchy** was selected over pipeline-centric or hybrid approaches.

**Rationale:** Services are designed around what they own, not when they execute. This maximises reuse — Image Services, Content Services, and Design Services are independently valuable beyond deck production. They could serve a report generator, social card maker, or any visual content pipeline.

The Deck Conductor sits at L0 as the orchestrator. It is one possible consumer of the L1 services, not the definition of the system.

## 3. Service Hierarchy

```
L0: Presentation Engineering
│
├── L1: Content Services
│   ├── L2: Outline Generation         (skill: narrative-architect)
│   └── L2: Speaker Notes              (skill: speaker-notes-writer)
│
├── L1: Design Services
│   ├── L2: Style Derivation           (skill: slide-stylist)
│   ├── L2: Brand Extraction           (capability within slide-stylist)
│   └── L2: Layout Intelligence        (capability within slide-stylist)
│
├── L1: Image Services
│   ├── L2: Image Routing & Discovery  (skill: imagegen-bridge)
│   ├── L2: Ollama Image Generation    (skill: ollama-generate-image)
│   ├── L2: Ollama Icon Generation     (skill: ollama-generate-icon)
│   ├── L2: Ollama Pattern Generation  (skill: ollama-generate-pattern)
│   ├── L2: Ollama Diagram Generation  (skill: ollama-generate-diagram)
│   ├── L2: Cloud Image Generation     (skill: cloud-generate-image)
│   ├── L2: Cloud Icon Generation      (skill: cloud-generate-icon)
│   ├── L2: Chart Rendering            (skill: chart-renderer)
│   ├── L2: Image Post-Processing      (skill: image-processor)
│   └── L2: Image Generation Expert    [AI PERSONA — agent]
│
├── L1: Assembly & QA Services
│   ├── L2: PPTX Build                 (skill: deck-assembler)
│   ├── L2: Visual QA                  (skill: deck-qa)
│   ├── L2: File Optimisation          (capability within deck-assembler)
│   └── L2: Presentation Reviewer      [AI PERSONA — agent]
│
└── L1: Deck Conductor                  [AI PERSONA — agent]
```

## 4. AI Personas

Three AI Personas with distinct, non-overlapping authority:

### Deck Conductor (L1, Orchestration)
- **Authority:** Hybrid — autonomous for sequencing/routing, escalates creative decisions and budget to Speaker
- **Role:** Sequences the pipeline, manages DeckContext state, enforces budget, handles QA correction loop (max 2 cycles)
- **Key constraint:** Never generates content, images, or style decisions directly — always delegates

### Image Generation Expert (L2, Image Services)
- **Authority:** Invoker — pure advisory, never acts autonomously
- **Role:** Prompt engineering, model-specific translation, quality scoring (6-dimension rubric), iteration convergence
- **Key constraint:** Never generates images or makes routing decisions — only advises

### Presentation Reviewer (L2, Assembly & QA Services)
- **Authority:** Invoker — reviews and recommends, never modifies
- **Role:** Reviews assembled deck against conference best practices — narrative coherence, visual storytelling, pacing, speaker notes quality
- **Key constraint:** Never modifies the deck — only the Conductor acts on review feedback

## 5. System Actors

| Actor | Type | Services | Discovery |
|---|---|---|---|
| Ollama | Local inference | Image Services (ollama-*) | Ping localhost:11434 |
| OpenAI API | Cloud generation | Image Services (cloud-*) | Check OPENAI_API_KEY env var |
| Google Vertex AI | Cloud generation | Image Services (cloud-*) | Check GOOGLE_CLOUD_PROJECT env var |
| FAL.ai | Cloud aggregator | Image Services (cloud-*) | Check FAL_KEY env var |
| Recraft API | SVG generation | Image Services (cloud-icon) | Check RECRAFT_API_KEY env var |
| PptxGenJS | PPTX rendering | Assembly | Always available (npm dependency) |
| Matplotlib | Chart rendering | Image Services (chart) | Always available (pip dependency) |
| Filesystem | State persistence | All services | Always available (./tmp/deck/) |

**Provider Discovery** is a foundational capability within the imagegen-bridge. At pipeline start, it probes all providers and reports what's available. The Conductor presents this to the Speaker before proceeding.

## 6. Human Actors

| Actor | Role |
|---|---|
| Speaker | Primary user. Provides talk brief, makes creative decisions, reviews output, approves budget. |
| Reviewer | Optional. Reviews finished deck for content/brand accuracy before delivery. |

## 7. Data Contracts

| Contract | Producer | Consumers | File |
|---|---|---|---|
| TalkBrief | Speaker | Conductor, all L1 services | ./tmp/deck/talk-brief.json |
| AvailableProviders | imagegen-bridge | Conductor | ./tmp/deck/available-providers.json |
| StyleGuide | slide-stylist | Content, Image, Assembly | ./tmp/deck/style-guide.json |
| SlideOutline | narrative-architect | Image, Assembly, Reviewer | ./tmp/deck/outline.json |
| SpeakerNotes | speaker-notes-writer | Assembly, Reviewer | ./tmp/deck/speaker-notes.json |
| ImageManifest | imagegen-bridge | Assembly | ./tmp/deck/image-manifest.json |
| ChartManifest | chart-renderer | Assembly | ./tmp/deck/chart-manifest.json |
| QAReport | deck-qa | Conductor | ./tmp/deck/qa-report.json |
| PipelineState | Conductor | Conductor (checkpoint/resume) | ./tmp/deck/pipeline-state.json |

Full JSON schemas defined in research paper #12.

## 8. Pipeline Execution Flow

```
1. Speaker → Conductor:     TalkBrief
2. Conductor → Image Svc:   Provider Discovery
3. Conductor → Speaker:     "Available: OpenAI + Ollama. Est. cost: $0.85. Proceed?"
4. Conductor → Design Svc:  Derive StyleGuide
5. Conductor → Content Svc: Generate SlideOutline + SpeakerNotes
6. Conductor → Image Svc:   Generate images per slide (via imagegen-bridge routing)
7. Conductor → Assembly:    Build .pptx via PptxGenJS
8. Conductor → Assembly:    Run Visual QA (25 anti-pattern checks)
9. [If QA issues, max 2x]:  Conductor → relevant service with corrections
10. Conductor → Assembly:   Presentation Review (craft assessment)
11. Conductor → Speaker:    Deliver .pptx + review + cost report
```

## 9. Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Service hierarchy | Domain-centric (Approach B) | Maximises reuse — services are independent of deck production |
| PPTX engine | PptxGenJS (keep existing) | Already used by pptx skill, JS native to Claude Code, add Python image pipeline |
| Image routing | Multi-model via imagegen-bridge | Route by asset type + available providers + budget. No single model excels at everything. |
| Ollama role | Drafting/iteration + direct output for low-fidelity assets | Free for backgrounds/textures/patterns. Drafting cycle for hero images before cloud spend. |
| State management | Directory of JSON files in ./tmp/deck/ | One file per contract. Enables checkpoint/resume. Per CONSTITUTION.md Article 4.6. |
| Naming convention | Provider prefix (ollama-*, cloud-*) | Avoids namespace clashes. Enables clear separation of local vs cloud skills. |
| AI Personas | 3 only (Conductor, Image Expert, Reviewer) | Authority only where genuine decision-making needed. Skills use Claude's intelligence without needing delegated authority. |
| QA approach | Programmatic (deck-qa) + Craft review (Presenter Reviewer) | Mechanical checks first, then qualitative assessment. Different concerns, different tools. |
| Provider discovery | Runtime env var + endpoint probing | Adapts to whatever the developer has configured. Graceful degradation to typography-only mode. |

## 10. Skill Naming Map

| BSA Service (L2) | Skill Name | Type |
|---|---|---|
| Outline Generation | narrative-architect | Skill |
| Speaker Notes | speaker-notes-writer | Skill |
| Style Derivation | slide-stylist | Skill |
| Image Routing & Discovery | imagegen-bridge | Skill |
| Ollama Image Generation | ollama-generate-image | Skill |
| Ollama Icon Generation | ollama-generate-icon | Skill |
| Ollama Pattern Generation | ollama-generate-pattern | Skill |
| Ollama Diagram Generation | ollama-generate-diagram | Skill |
| Cloud Image Generation | cloud-generate-image | Skill |
| Cloud Icon Generation | cloud-generate-icon | Skill |
| Chart Rendering | chart-renderer | Skill |
| Image Post-Processing | image-processor | Skill |
| PPTX Build | deck-assembler | Skill |
| Visual QA | deck-qa | Skill |
| Deck Conductor | deck-conductor | Agent |
| Image Generation Expert | image-generation-expert | Agent |
| Presentation Reviewer | presentation-reviewer | Agent |

**Total: 14 skills + 3 agents = 17 deliverables**

Note: Brand Extraction and Layout Intelligence are modelled as separate L2 services in the canonical model (for documentation and traceability) but will be implemented as capabilities within the single `slide-stylist` skill. Similarly, File Optimisation is a capability within `deck-assembler`. The canonical model captures architectural intent; implementation may consolidate where it makes sense.

## 11. Canonical Model

The machine-readable canonical model is at `.bsa/models/jack-tar-deckhand.json`. It contains:
- 25 services (1 L0, 5 L1, 19 L2)
- 3 AI Persona contracts with full scope/authority definitions
- 2 human actors
- 8 system actors
- 27 interactions

Documentation generated from the model is in `.bsa/docs/`.

## 12. What This BSA Intentionally Excludes

- **AI RM / operational management** — Claude Code handles this natively
- **Governance SOPs** — not needed for a skill suite; Claude Code's permission model is sufficient
- **Measurement hierarchies** — premature; add after skills are built and producing output
- **BPMN process definitions** — the pipeline flow is simple enough that a sequence description suffices
- **Enterprise compliance** — CONSTITUTION.md already covers code quality, validation, and git workflow
