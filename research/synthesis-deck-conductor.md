# Synthesis: deck-conductor

> Distilled from: docs/architecture/ai-persona-summaries.md, docs/architecture/architecture-overview.md, docs/architecture/interaction-matrix.md, .bsa/models/jack-tar-deckhand.json, src/budget_tracker.py, src/deckcontext.py, src/schemas/pipeline_state.schema.json, research/05-multi-model-routing-pipeline.md, research/12-deckcontext-state-management.md, research/13-cost-optimisation-caching.md

## 1. Sequencing and State Management Role

The Deck Conductor is the TOP-LEVEL orchestration agent (L1, Hybrid authority). It sequences the full pipeline from TalkBrief to finished .pptx, but never generates content, images, or style decisions directly. Every creative output is delegated to the appropriate L1 service domain.

**Core principle: The Conductor sequences skills; each skill handles its own Speaker collaboration.** The narrative-architect presents 2-3 arc options to the Speaker. The slide-stylist presents design options. The speaker-notes-writer gathers voice preferences. The Conductor does not mediate these conversations -- it invokes the skill and the skill talks to the Speaker within its own scope. The Conductor only intervenes when escalation is needed (budget, ambiguity, repeated QA failure).

State is managed via the DeckContext filesystem (`./tmp/deck/`). All shared state is persisted as JSON files -- one file per data contract. The existing `deckcontext.py` module provides init, read, write, validate, and checksum operations. The Conductor owns the PipelineState contract and updates step status as each skill runs.

Key state management functions already implemented:
- `init_deck(deck_dir)` -- creates directory structure with `images/` and `output/` subdirectories
- `write_contract(deck_dir, contract_name, data)` -- validates against JSON schema and writes
- `read_contract(deck_dir, contract_name)` -- reads a contract file, returns None if missing
- `update_step(deck_dir, step_name, status)` -- updates step status with timestamps in PipelineState
- `compute_checksum(file_path)` -- SHA-256 for resumability

## 2. Draft/Production Lifecycle

The pipeline operates in two phases: **Draft** (iterative) and **Production** (single-pass).

### Draft Phase

Each draft cycle runs the full pipeline to produce a reviewable deck. The Speaker iterates on narrative, layout, slide structure, and visual direction across multiple cycles.

- **Design + Content:** Run at full quality in every cycle (LLM text generation has no quality difference between draft and production)
- **Image:** Uses draft-quality rendering:
  - **Early drafts:** Ollama for structural placeholders and composition testing (free)
  - **Later drafts:** Target cloud provider at reduced quality/size for prompt refinement (cheap but not free)
- **Assembly + QA + Review:** Build and review the draft deck

**Important:** Image prompts are model-specific. A prompt tuned for Ollama's flux2-klein produces very different results on GPT Image 1.5 or Imagen 4. Ollama drafts are useful for testing composition and layout placement, but when the Speaker is refining visual direction for cloud-rendered images, the draft cycle should use the target cloud provider at a reduced quality tier rather than Ollama. The Image Generation Expert handles model-specific prompt translation when switching between providers.

### Production Phase

Triggered when the Speaker approves the draft:

1. Re-render all images at full quality and full resolution using the approved providers
2. Assembly rebuilds the deck with production images
3. Final QA and Presentation Review run
4. Finished deck is delivered with cost summary

**The production budget covers full-quality renders only.** Draft cycles with Ollama are free; draft cycles with cloud providers at reduced quality are cheaper but not zero. The Conductor tracks cumulative spend across ALL cycles (draft + production).

## 3. Budget Management

### Reuse BudgetTracker

The existing `BudgetTracker` class in `src/budget_tracker.py` provides everything the Conductor needs:

- `__init__(total_budget_usd)` -- initialise with Speaker-declared budget cap
- `can_spend(amount_usd)` -- pre-check before each API call
- `log_api_call(model_key, cost_usd, image_id)` -- record spend with timestamp
- `log_cache_hit(cache_key, saved_usd)` -- record cache savings
- `estimate_cost(model_key)` -- lookup cost from MODEL_COSTS table
- `to_dict()` -- serialise full budget state for pipeline-state.json
- `cost_summary_markdown()` -- generate Markdown cost report for Speaker review

### Persist Snapshots

The Conductor must persist budget snapshots into `pipeline-state.json` at each review point. Call `budget_tracker.to_dict()` and write it into the PipelineState contract. This allows resumability -- if a session is interrupted, the Conductor can reconstruct the BudgetTracker from the persisted snapshot.

### 4-State Degradation

The BudgetTracker implements a 4-state budget state machine with fixed thresholds:

| State | Utilisation | Image Strategy |
|-------|-------------|----------------|
| `allow` | 0-70% | Full multi-model routing: heroes to premium models, backgrounds to cheap models |
| `allow_with_caps` | 70-90% | Switch hero images to cheap models (Imagen 4 Fast), skip decorative images |
| `degrade` | 90-100% | All remaining images via Ollama (free) |
| `typography_only` | 100%+ | No image generation at all -- placeholders only |

**A deck is always completable at $0.** The degradation chain ensures the pipeline never blocks on budget exhaustion. The Conductor reports the current budget state to the Speaker at each review point.

Model cost reference (from MODEL_COSTS):
- GPT Image 1.5 high: $0.133/image (premium hero images)
- GPT Image 1.5 medium: $0.040/image
- Imagen 4 Standard: $0.040/image
- Imagen 4 Fast: $0.020/image (budget workhorse)
- FLUX.2 Pro: $0.050/image
- Recraft V4 SVG: $0.040/image (icons)
- GPT Image 1 Mini low: $0.005/image (cheapest option)

## 4. QA Correction Loop

### Two Quality Gates

The architecture enforces a strict separation between automated and human-judgement QA:

1. **Visual QA (deck-qa):** 25 automated, machine-checkable anti-pattern checks (contrast, margins, overflow, consistency). Returns pass, pass_with_warnings, or fail. Triggers the automated correction loop.
2. **Presentation Reviewer:** Human-judgement-level assessment (narrative coherence, visual storytelling, pacing). Produces structured recommendations. Feedback goes to the Speaker for decision -- does NOT trigger automatic correction.

### Correction Cycle Logic

1. Conductor invokes deck-assembler, then deck-qa
2. If deck-qa returns `fail`, Conductor re-invokes the producing service with corrective instructions
3. **Maximum 2 autonomous correction cycles** -- after 2 failures, escalate to Speaker with the best-effort deck and the QA findings
4. If deck-qa returns `pass` or `pass_with_warnings`, Conductor invokes the Presentation Reviewer
5. Reviewer feedback goes to the Conductor, which presents it to the Speaker for decision
6. The Conductor NEVER acts autonomously on Reviewer feedback -- it always goes to the Speaker

### What "Re-invoke the Producing Service" Means

The Conductor does not modify artefacts directly. When QA finds a contrast failure on slide 5, the Conductor:
- Identifies which service produced the failing artefact (e.g., slide-stylist for palette, imagegen-bridge for image)
- Re-invokes that service with the QA finding as corrective context
- The service regenerates the artefact
- Assembly and QA re-run

## 5. Authority Model

### Hybrid Authority

The Deck Conductor uses Hybrid authority: autonomous above 0.8 confidence, escalates to the Speaker below. This means routine pipeline decisions happen without interruption, while ambiguous, high-cost, or creative decisions always involve the Speaker.

### 8 Autonomous Decision Types (confidence >= 0.8)

These are decisions the Conductor makes without asking the Speaker:

1. **Parse and validate TalkBrief input** -- structural validation against the schema
2. **Generate deck plan** -- slide count, types, and narrative flow from TalkBrief
3. **Invoke L1 services in dependency order** -- choosing which service to call next
4. **Create and manage DeckContext state directory** -- initialising `./tmp/deck/`
5. **Invoke provider discovery and adapt routing** -- run discovery, adjust plan based on available providers
6. **Track cumulative cloud API spend** -- log costs, compute budget state
7. **Re-invoke services on QA failure** -- first 2 correction cycles are autonomous
8. **Report progress, cost, and timing** -- status updates to the Speaker

### 10 Escalation Types (must involve Speaker)

These decisions always require Speaker input:

1. **Budget will be exceeded by next generation request** -- seek approval or accept degradation
2. **QA finds critical issues after 2 correction cycles** -- present best-effort deck with findings
3. **No image generation providers available** -- confirm whether to proceed with placeholders only
4. **Reviewer identifies structural narrative problems** -- narrative direction requires Speaker input
5. **Talk brief is ambiguous or missing required fields** -- cannot infer safely
6. **Design options selection** -- Conductor presents BrandProfile summary, compliance mode, and design options during the Design phase
7. **Narrative arc selection** -- the narrative-architect presents 2-3 arc options for Speaker choice
8. **Speaker notes voice preferences** -- speaker-notes-writer gathers style and format preferences
9. **Draft approval for production render** -- Speaker must explicitly approve before full-quality rendering
10. **Final delivery acceptance** -- presenting the finished deck, QAReport, Presentation Review, and cost summary

## 6. Pipeline Step Order

The canonical step order is defined in `deckcontext.py` as `DEFAULT_STEP_ORDER`:

```
1. validate-brief      -- Parse and validate TalkBrief against schema
2. brand-manager        -- Obtain or create BrandProfile from brand assets
3. slide-stylist        -- Derive StyleGuide from TalkBrief + BrandProfile
4. narrative-architect  -- Generate SlideOutline from TalkBrief + StyleGuide
5. speaker-notes-writer -- Generate SpeakerNotes from SlideOutline + TalkBrief
6. imagegen-bridge      -- Generate images for all slides (ImageManifest)
7. chart-renderer       -- Render data charts (ChartManifest)
8. deck-assembler       -- Assemble .pptx from all artefacts
9. deck-qa              -- Run 25 anti-pattern checks (QAReport)
```

After deck-qa passes, the Conductor invokes the Presentation Reviewer (not in DEFAULT_STEP_ORDER because it is an advisory persona, not a pipeline step).

### Step Dependencies

| Step | Requires | Produces |
|------|----------|----------|
| validate-brief | TalkBrief (from Speaker) | Validated TalkBrief |
| brand-manager | TalkBrief, brand assets (optional) | BrandProfile |
| slide-stylist | TalkBrief, BrandProfile | StyleGuide |
| narrative-architect | TalkBrief, StyleGuide | SlideOutline |
| speaker-notes-writer | SlideOutline, TalkBrief | SpeakerNotes |
| imagegen-bridge | SlideOutline, StyleGuide, AvailableProviders, budget | ImageManifest |
| chart-renderer | SlideOutline, StyleGuide | ChartManifest |
| deck-assembler | SlideOutline, StyleGuide, ImageManifest, ChartManifest, SpeakerNotes | .pptx |
| deck-qa | .pptx | QAReport |
| presentation-reviewer | .pptx, SlideOutline, StyleGuide, SpeakerNotes, TalkBrief | Structured Review |

### PipelineState Schema

Each step tracks: `status` (pending/running/completed/failed/skipped), `started_at`, `completed_at`, `output_file`, `error`, `retry_count`, `checksum`. The pipeline-level status is one of: running, completed, failed, paused.

## 7. Anti-Patterns

- **Never generate content directly** -- the Conductor delegates to L1 services, always
- **Never modify artefacts** -- only re-invoke the producing service with corrective instructions
- **Never skip QA** -- even if all previous steps passed cleanly
- **Never spend above budget without Speaker approval** -- degrade gracefully instead
- **Never proceed past provider discovery without confirming capabilities to the Speaker**
- **Never loop QA corrections beyond 2 cycles** -- escalate to Speaker
- **Never act on Reviewer feedback autonomously** -- Reviewer feedback always goes to the Speaker for decision
- **Never mediate skill-Speaker conversations** -- skills handle their own Speaker collaboration within their scope
