# Creative Vision Renderer — Design Spec

**Status:** Proposed (awaiting implementation plan)
**Date:** 2026-05-21
**Issue:** [#105](https://github.com/SteveGJones/jack-tar-deckhand/issues/105)
**Sibling references:**
- [paperbanana-integration-v2.md](../../architecture/paperbanana-integration-v2.md) (the technical-figure equivalent — the structural mirror for this work)
- Issue #88 (`full_bleed` assembler strategy — the consumer of this pipeline's output)
- Issue #87 / PR #92 (register presets — the visual language the renderer speaks)
- `plugins/jack-tar-superpower-bridge/src/registers/presets/infographic-narrative.md`

---

## 1. Context

After v1.4.2 (issue #88) jack-tar-deckhand has three concepts that should compose, but only two are built. **paperbanana** renders technical, fixed-structure figures (architecture diagrams, equations, ablation plots) and is integrated through the `academic_figure` strategy. **`full_bleed`** is the assembler strategy that places a picture edge-to-edge with no chrome — the slide IS the image. The missing third leg is a **renderer for creative, vision-directed images**: the operator describes a specific vision in natural prose — four named ships in a four-way sea battle, framework components as cabins inside a man-o-war, sun phases as a left-to-right progression — and a pipeline brings that vision to life at presentation-or-print quality.

This is not abstract evocation (rendering "trust" as a mood image — easy, already covered by generic backdrop generation). It is **operator-as-director** — the operator authors a rich, often metaphorical vision with named entities, spatial directives, style cues, and optional within-frame compositional progression, and the system's job is to deliver that specific vision faithfully.

The renderer mirrors paperbanana **structurally** — multi-stage agent pipeline, internal critic loop, manifest with run-id, /iterate-slide integration, dispatch module — but renders a fundamentally different artefact and runs entirely in-process inside the deckhand plugin (paperbanana is an external CLI tool; this is internal code).

## 2. Design principles (load-bearing constraints)

These are the invariants the architecture honours. If any of them slip, the design loses its shape.

1. **Operator-as-director.** The operator writes the vision in free-form prose. No structured schema burden on the operator's side. The system parses, plans, prompts, renders, critiques.

2. **Prose is living ground truth, not a frozen oracle.** The operator's prose is the reference all critics grade against AND it is itself revisable. When the rendered image doesn't satisfy, the operator has three feedback channels: revise the prose, refine the prompt, or escalate the tier. The manifest persists prose with versioning so revisions don't lose history.

3. **Producer / consumer boundary — full-image review only.** The pipeline reviews rendered images as standalone vision-faithfulness artefacts. It does NOT review them in slide context. Downstream consumers (today, `full_bleed` assembly; later, a bridge marker) handle slide placement. Conflating the two review tasks would degrade the critic's discipline.

4. **The maker is never the judge.** The agent that writes / rewrites the prompt is structurally separate from the agent that grades the prompt against the vision, AND from the agents that grade the rendered image. Three distinct critic-class roles: Prompt Reviewer (text-side), image-reviewer (image visual quality, existing Haiku), Director's Critic (image vision-fidelity).

5. **Operator-opt-in only.** Neither auto-classifier emits `creative_vision`. The operator explicitly assigns it. Risk of cascade-spending without intent is too high for heuristics.

6. **Cascade economics — cheap-first, escalate on plateau, budget-capped.** Ollama free draft, then cloud cascade with resolution-first ladder, model-bump on plateau. Per-tier iteration caps. Per-slide hard budget cap.

7. **paperbanana-shaped but creative-domain.** Lives in its own dispatch module in the deckhand plugin, parallel to `paperbanana_dispatch.py`. Mirrors the structure (multi-stage, internal critic, manifest) but renders a fundamentally different artefact.

8. **Single-image only in v1.** Sequences-of-coordinated-images are deferred without a stub. Within-frame compositional progression (sun phases left-to-right) is fully supported — that's still a single image with rich composition semantics.

## 3. Architecture

Four agents, two gates, one cascade. Plus the existing image-reviewer.

### 3.1 Agents

| Agent | Status | Model | Role |
|-------|--------|-------|------|
| **Director's Brief** | NEW | Sonnet | Takes operator's prose + accumulated feedback + current tier's capabilities. Produces a `ParsedVision` intermediate AND a render-ready prompt for the current tier. Sole agent that touches the prompt — every refinement returns here. |
| **Prompt Reviewer** | NEW | Haiku | Takes operator's original prose + Brief's current prompt + parsed intermediate. Returns `pass | refine` + per-axis feedback (entities present? spatial honoured? style cue retained? text density within #91 threshold?). Text-side gate. |
| **image-reviewer** | EXISTING (reused) | Haiku | Takes the rendered image + minimal context. Returns `pass | refine` + visual quality issues. General visual-quality gate. |
| **Director's Critic** | NEW | Sonnet | Takes rendered image + operator's prose + parsed intermediate + run history. Returns `pass | refine_at_tier | escalate_tier | abort` + per-axis scores + recommended-action prose + gap_location diagnosis. Vision-fidelity gate. |

### 3.2 Pipeline flow inside one cascade tier

```
operator's prose
       │
       ▼
[Director's Brief] ←──── refine ────────────────┐
       │                                        │
       ▼                                        │
[Prompt Reviewer] ──── refine (cap 3) ──────────┤  text-side loop
       │ pass                                   │  (cheap, text-only)
       ▼                                        │
[Visualizer @ current tier] (RENDER — costs)    │
       │                                        │
       ▼                                        │
[image-reviewer] ──── refine ───────────────────┤  back to Brief — NEVER re-render
       │ pass                                   │  directly (every render goes
       ▼                                        │  through the text gate)
[Director's Critic]                             │
       │                                        │
       ├─ refine_at_tier ─────────────────────────┘
       │
       ├─ escalate_tier ──> bump tier; back to Brief with tier-change context
       │
       ├─ pass ───────────> ACCEPT + persist manifest
       │
       └─ abort ──────────> out of budget or unrecoverable — return best-so-far
```

### 3.3 Structural rules

1. **Every refinement path returns to the Director's Brief.** Visualizer is never re-invoked with an unchanged prompt; image-reviewer feedback never bypasses the text gate. This catches the "elements dropped in a rewrite" failure mode.

2. **Maker / judge separation is preserved at every stage.** Brief makes prompts; Reviewer judges prompts. Visualizer makes images; image-reviewer + Director's Critic judge images. No agent grades its own output.

### 3.4 Iteration caps (defaults, operator-overridable)

| Cap | Default | Purpose |
|-----|---------|---------|
| Text-side (Brief ↔ Prompt Reviewer) per render | 3 | Bounded text refinement before forcing pass with warning |
| Image-side at Ollama (T0) | 5 | Free tier — iterate generously to lock composition before paying |
| Image-side at Flash tiers (T1–T3 / Recraft Standard) | 3 | Standard refinement window at cheap-paid tiers |
| Image-side at Pro 1K / 2K (T4–T5 / Recraft Pro 2K) | 2 | Bounded because each iteration is expensive |
| Image-side at Pro 4K / Recraft 4K (top of ladder) | 1 | One shot at the ceiling |
| Hard floor | `budget_usd` per slide | Aborts and returns best-so-far when exhausted |

(See Section 5.4 for the same caps expressed as a YAML override surface for operators.)

## 4. Contracts (schemas)

Three artefacts moving between agents and across iterations. They live under `plugins/jack-tar-deckhand/src/schemas/`.

### 4.1 `ParsedVision`

What Director's Brief produces; what Prompt Reviewer and Director's Critic consume.

```json
{
  "schema_version": "1.0",
  "original_prose": "<verbatim operator prose, never rewritten>",
  "prose_version": 1,
  "subjects": [
    {"name": "SAP",        "role": "named_entity", "spatial_slot": "ship_NE"},
    {"name": "Databricks", "role": "named_entity", "spatial_slot": "ship_NW"},
    {"name": "OpenAI",     "role": "named_entity", "spatial_slot": "ship_SE"},
    {"name": "Anthropic",  "role": "named_entity", "spatial_slot": "ship_SW"}
  ],
  "spatial_directives": {
    "setting": "lake at battle",
    "layout": "four-way engagement",
    "containment": null,
    "named_relationships": ["ships engage in four-way"]
  },
  "style": {
    "explicit": null,
    "implied": "dramatic naval battle",
    "register_inherited_from": null
  },
  "composition": {
    "progression_axis": null,
    "primary_focus": "central engagement",
    "compositional_rules": []
  },
  "delivery": {
    "scale": "screen_16x9",
    "aspect": "16:9",
    "viewing_context": "conference projection"
  },
  "text_density_warning": {
    "estimated_text_elements": 4,
    "threshold_breach": false
  }
}
```

- `original_prose` is verbatim and never rewritten.
- `subjects` carries named entities with spatial slots — what the Critic checks for presence and correctness.
- `composition.progression_axis` covers within-frame progression (sun phases left-to-right, fireball size escalation); null for non-progressive compositions.
- `text_density_warning` is the #91 hook — if estimated text elements >12, Prompt Reviewer flags pre-render.

### 4.2 `DirectorsCriticVerdict`

What the Critic returns after each rendered image.

```json
{
  "verdict": "refine_at_tier",
  "per_axis_scores": {
    "entity_fidelity":   65,
    "spatial_fidelity":  85,
    "style_fidelity":    90,
    "quality":           80,
    "composition":       75
  },
  "issues": [
    {"axis": "entity_fidelity",
     "detail": "Databricks ship missing — only 3 of 4 named ships rendered"}
  ],
  "gap_location": "prompt",
  "recommended_action": "Re-emphasise Databricks as a labelled fourth ship in the NW position; ensure all four labels are visually prominent",
  "tier": "flash_2k",
  "iteration_index": 2,
  "plateau_signal": false
}
```

- Per-axis scores are 0–100, enabling numeric plateau detection.
- `plateau_signal: true` when the same axes haven't improved across 2 iterations at the current tier — drives `escalate_tier`.
- `gap_location` ∈ `{prose, prompt, tier, unknown}` powers /iterate-slide's three-channel feedback.
- `recommended_action` is prose direction the Brief consumes verbatim on the next iteration.

### 4.3 `CreativeVisionManifest`

Persisted state for /iterate-slide and audit. Path: `./tmp/deck/creative-vision/<slide_number>/manifest.json`, with `runs/` subdir for actual rendered PNGs from each attempt.

```json
{
  "run_id": "cv-2026-05-21-093142-slide-3",
  "slide_number": 3,
  "strategy": "creative_vision",
  "prose_history": [
    {"version": 1, "timestamp": "2026-05-21T09:31:42Z", "prose": "Four ships in a sea battle..."},
    {"version": 2, "timestamp": "2026-05-21T09:45:11Z", "prose": "Four 1980s Cold-War warships...",
     "revised_by": "operator", "reason": "fishing-boat-look in v1 render"}
  ],
  "attempts": [
    {
      "attempt_index": 1,
      "prose_version": 1,
      "tier": "ollama",
      "text_iterations": [
        {"prompt_draft": "...", "reviewer_verdict": "refine", "reviewer_feedback": "Databricks missing"},
        {"prompt_draft": "...", "reviewer_verdict": "pass"}
      ],
      "render": {"model": "flux-schnell", "resolution": "1024x576",
                 "cost_usd": 0.0, "output_path": "runs/01-ollama.png"},
      "image_reviewer_verdict": "pass",
      "directors_critic_verdict": {"...": "DirectorsCriticVerdict"},
      "cumulative_cost_usd": 0.0
    }
  ],
  "final": {
    "image_path": "runs/07-flash-4k.png",
    "accepted_at_tier": "flash_4k",
    "total_cost_usd": 0.43,
    "total_iterations": 7,
    "final_verdict": {"...": "DirectorsCriticVerdict with verdict: pass"}
  },
  "iterate_slide_hooks": {
    "can_revise_prose": true,
    "can_refine_prompt": true,
    "can_escalate_tier": true,
    "current_tier": "flash_4k",
    "next_tier_available": "pro_1k",
    "remaining_budget_usd": 2.07
  }
}
```

`prose_history` versioning enables the "revise prose" channel — operator revision bumps `prose_version`; pipeline restarts with the new prose but history is preserved for diagnosis. `iterate_slide_hooks` is the surface the /iterate-slide skill reads to know what actions are available NOW.

## 5. Tier cascade economics

### 5.1 Default ladder (`brand_fidelity: none | approximate`)

| Tier | Model + Resolution | Cost per render | Notes |
|------|--------------------|-----------------|-------|
| T0 | Ollama (FLUX schnell or sd-xl) 1024×576 | $0.00 | Free; iterate generously to lock composition + entity placement |
| T1 | Nano Banana Flash 1K | $0.067 | First paid tier; quality jump on style + text |
| T2 | Nano Banana Flash 2K | $0.101 | Resolution bump within same model |
| T3 | Nano Banana Flash 4K | $0.151 | Top of Flash ladder |
| T4 | Nano Banana Pro 1K | $0.134 | Model bump — better compositional intelligence |
| T5 | Nano Banana Pro 2K | $0.193 | |
| T6 | Nano Banana Pro 4K | $0.240 | Top of standard cascade |

### 5.2 Alternate ladder when `brand_fidelity: exact`

| Tier | Model + Resolution | Cost | Notes |
|------|--------------------|------|-------|
| T0 | Ollama draft | $0.00 | Same free composition-validation step |
| T1 | Recraft V4 Standard 1K | $0.04 | Hex-exact, slightly cheaper than Flash |
| T2 | Recraft V4 Pro 2K | $0.25 | |
| T3 | Recraft V4 Pro 4K (creative-upscale chain) | ~$0.50 | Top of brand-fidelity ladder |

The two ladders are **mutually exclusive per slide** — the strategy-map's `brand_fidelity` field picks the ladder. Mixing within one slide's cascade would shift style mid-iteration and degrade `style_fidelity` scoring.

### 5.3 Plateau detection — what triggers `escalate_tier`

The Director's Critic returns `escalate_tier` when ANY of:

1. **Numeric plateau** — per-axis scores haven't improved by ≥5 points on any axis across 2 consecutive iterations at the current tier. `plateau_signal: true`.
2. **Iteration cap reached** — per-tier cap exhausted with at least one axis still <80 and the Critic judging the model capable elsewhere.
3. **Capability ceiling diagnosed** — Critic explicitly judges "this failure is the model's, not the prompt's."

On `escalate_tier`, the orchestrator bumps to the next tier, resets the per-tier iteration counter, hands the Critic's diagnosis to the Brief as tier-change context, continues the loop.

### 5.4 Defaults (operator-overridable per-slide)

```yaml
budget_usd: 1.00
allowed_ceiling: pro_4k
iteration_caps:
  ollama: 5
  flash_1k: 3
  flash_2k: 3
  flash_4k: 3
  pro_1k: 2
  pro_2k: 2
  pro_4k: 1
text_iteration_cap: 3
```

### 5.5 Budget enforcement (the hard floor)

Before every paid render:

```
if cumulative_cost_usd + projected_next_render_cost > budget_usd:
    Critic returns verdict: "abort" with reason "budget_exhausted"
    Pipeline returns best-so-far image from the manifest's attempts
    /iterate-slide can later refresh the budget and continue from the saved manifest
```

Ollama renders don't count against `budget_usd`. The text-side loop doesn't count either — purely text.

Worst-case spend at default budget $1.00, ceiling `pro_4k`: T0–T3 exhausted (5 free Ollama + 9 paid Flash iterations ≈ $0.957), pipeline aborts before T4 Pro because next render would breach $1.00. A 3-slide creative_vision deck at default budget = $3.00 max.

### 5.6 Deck-level budget integration

`creative_vision` slides participate in `src/budget_tracker.py`. The orchestrator pre-flights total committed budget vs deck budget at strategy-map approval and surfaces a warning if the deck would over-spend.

## 6. Operator surface

### 6.1 Strategy-map entry shape

```json
{
  "slide_number": 3,
  "strategy": "creative_vision",
  "rationale": "operator-directed: four ships sea-battle metaphor",
  "render_funnel": ["ollama", "cloud_low", "cloud_full"],
  "speaker_override": null,
  "brand_fidelity": "none",
  "creative_vision": {
    "vision_prose": "Four warships on a lake — SAP, Databricks, OpenAI, Anthropic — engaged in a four-way naval battle. Dramatic, churning waters.",
    "budget_usd": 1.00,
    "allowed_ceiling": "pro_4k",
    "iteration_caps_override": null
  }
}
```

**Schema rule:** the `creative_vision` block is **required when `strategy: creative_vision`** and **forbidden otherwise**. Mirrors how `smartart_config` works today. `vision_prose` is the only required field inside; the rest take cascade defaults.

### 6.2 Authoring path — `/strategy-map` skill becomes vision-aware

When the operator (or Claude on their behalf) assigns a slide to `creative_vision`, the skill interactively gathers the prose and surfaces a cost banner:

> "Slide 3 marked `creative_vision`. Worst-case spend ~$1.00 per slide. Deck currently has 1 creative_vision slide; deck-level worst case ~$1.00. Provide the vision prose (free-form prose; describe what you want, including named entities, spatial directives, style, and any compositional progression):"

The prose lands in `creative_vision.vision_prose`. The operator can defer (skill records strategy + leaves prose empty with a `pending_vision_prose: true` flag; pipeline halts at this slide until prose is provided).

### 6.3 Pipeline placement — deck-conductor orchestration

```
Step 1: brand-manager
Step 2: slide-stylist
Step 3: narrative-architect
Step 3.5: strategy-map         ← vision-aware extension (interactive prose authoring)
Step 4: smartart-selector      ← SKIPPED for creative_vision slides
Step 5: smartart-extractor     ← SKIPPED for creative_vision slides
Step 6: speaker-notes-writer
Step 7: imagegen-bridge        ← DISPATCHES to creative_vision_dispatch.py for
                                 creative_vision slides; standard image_router
                                 path for all others
Step 8: deck-assembler         ← creative_vision slides routed through
                                 buildFullBleedSlide (issue #88 v1.4.2)
Step 9: deck-qa                ← skips text-based AP checks for creative_vision
                                 slides (no text to check); runs palette +
                                 image quality only
```

`imagegen-bridge` reads strategy-map, sees `strategy: creative_vision`, calls `creative_vision_dispatch.run(slide_entry, deck_dir, budget_remaining)`. The dispatch produces the manifest + final image path. The bridge folds the result into the standard ImageManifest so deck-assembler treats it as a normal image.

### 6.4 `/iterate-slide` extension — three operator-feedback channels

| /iterate-slide mode | Behaviour for a creative_vision slide |
|---|---|
| `enumerate` | Reads manifest; presents three explicit channels with the Director's Critic diagnosis: (1) revise prose — shows current prose, lets operator edit; (2) refine prompt — adds operator's note as Brief context, re-runs at current tier; (3) escalate tier — bumps to next cascade tier (only offered if `next_tier_available` and `remaining_budget_usd > tier_cost`). |
| `auto` | Reads `directors_critic_verdict.gap_location`. If `prose` + high confidence, prompts operator to revise (won't autonomously change prose — channel 1 requires explicit operator action). If `prompt`, refines prompt and re-runs. If `tier`, escalates if budget allows. |
| `draft` | Operator writes a free-form note. Skill heuristically routes: rewrite-shaped note → channel 1 (prose revision); targeted correction → channel 2 (prompt refinement). Operator confirms the routing. |

Channel 1 (prose revision) is the only channel that requires explicit operator narrative input. Channels 2 and 3 reuse the existing prose unchanged.

## 7. Code organisation

```
plugins/jack-tar-deckhand/
├── src/
│   ├── creative_vision_dispatch.py             # NEW — main entry (mirror of paperbanana_dispatch.py)
│   ├── creative_vision/                         # NEW — pipeline sub-package
│   │   ├── __init__.py
│   │   ├── orchestrator.py                     # the main loop tying agents + cascade
│   │   ├── brief.py                            # Director's Brief dispatch
│   │   ├── prompt_reviewer.py                  # Prompt Reviewer dispatch
│   │   ├── critic.py                           # Director's Critic dispatch
│   │   ├── cascade.py                          # tier ladder, plateau detection, budget enforcement
│   │   └── manifest.py                         # load/save/version of CreativeVisionManifest
│   ├── schemas/
│   │   ├── parsed_vision.schema.json           # NEW
│   │   ├── directors_critic_verdict.schema.json  # NEW
│   │   ├── creative_vision_manifest.schema.json  # NEW
│   │   └── strategy_map.schema.json            # EXTEND — add creative_vision block + enum value
│   └── iterate_slide_dispatch.py               # EXTEND — three-channel branch for creative_vision
├── agents/
│   ├── directors-brief.md                      # NEW (Sonnet)
│   ├── prompt-reviewer.md                      # NEW (Haiku)
│   ├── directors-critic.md                     # NEW (Sonnet)
│   └── image-reviewer.md                       # EXISTING, unchanged — reused
├── skills/
│   ├── strategy-map/SKILL.md                   # EXTEND — vision-aware interactive authoring
│   ├── imagegen-bridge/SKILL.md                # EXTEND — dispatch branch for creative_vision
│   └── iterate-slide/SKILL.md                  # EXTEND — three-channel logic
└── tests/
    ├── test_creative_vision_parser.py          # NEW
    ├── test_creative_vision_cascade.py         # NEW
    ├── test_creative_vision_manifest.py        # NEW
    ├── test_creative_vision_orchestrator.py    # NEW
    ├── test_creative_vision_dispatch.py        # NEW
    ├── test_creative_vision_schemas.py         # NEW
    └── test_creative_vision_e2e.py             # NEW (skipif unless ENABLE_E2E=1)

docs/architecture/
└── creative-vision-renderer.md                 # NEW — ADR mirroring paperbanana-integration-v2.md
```

Plugin version bump on landing: `1.4.2 → 1.5.0` (significant new capability + 3 new agents).

## 8. Testing strategy

Three layers:

1. **Unit tests** — fast, abundant, no agent dispatches. Cover module logic.
   - Parser produces valid ParsedVision for fixture prose corpus
   - Cascade transitions correctly on each verdict type
   - Plateau detection fires on flat-score windows; not on improving windows
   - Budget enforcement aborts cleanly when next render breaches cap
   - Manifest serialisation round-trips through schema validation
   - Schema rules (creative_vision block required-when-strategy, forbidden-otherwise)
   - Target: ~80 unit tests.

2. **Integration tests with mocked agents** — pipeline end-to-end with stubbed agent responses.
   - Brief returns canned ParsedVision + prompt; orchestrator advances
   - Reviewer returns refine then pass; loop terminates correctly
   - image-reviewer returns refine then pass; pipeline routes back to Brief
   - Critic returns refine_at_tier, escalate_tier, abort — orchestrator branches correctly
   - Prose revision triggers full restart with version bump; history preserved
   - Target: ~20 integration tests.

3. **End-to-end smoke tests with real agents** — gated by `ENABLE_E2E=1` env var.
   - One full Ollama-only run (no cloud spend) — validates real agent dispatches
   - One full cloud-tier run (skipif unless `ENABLE_CLOUD_TESTS=1` AND `BUDGET_OK=1`) — validates cascade end-to-end
   - Visual review via image-reviewer subagent dispatch — same discipline-hook rules as today
   - Target: 3–5 e2e tests; CI runs Ollama-only by default, cloud only on manual trigger.

Tests respect existing patterns: `plugins/jack-tar-deckhand/tests/` location, `PLUGIN_ROOT` discovery, `from src.module import` imports, `from __future__ import annotations`.

## 9. Future paths deferred from v1

With clean architectural hooks left in place; no v1 stubs.

1. **Sequences (N coordinated images sharing context).** A future sequence orchestrator wraps the single-image pipeline. No changes to pipeline internals. Added if/when a real use case emerges.

2. **Bridge marker for in-slide creative vision** (`CREATIVE-VISION:identifier`). The bridge plugin adds the marker kind; the marker consumes this pipeline unchanged. The producer/consumer boundary holds — pipeline still reviews full-image only; bridge handles slide placement.

3. **Brand-profile-driven style inheritance.** Today's prose carries all style cues explicitly. Future: parser also reads brand-profile + slide-stylist outputs and inherits register/palette into the ParsedVision automatically. v1 keeps the prose self-contained for predictability.

4. **Operator-defined critic axes.** Custom axes registered per deck or per slide. YAGNI for now; the per-axis scoring schema is extensible without breaking existing manifests.

5. **`auto+confirm` /iterate-slide mode.** High-spend slides may want operator confirmation before each automated decision. The /iterate-slide skill's mode set can grow; manifest hooks already expose the data needed.

(MCP transport considered and rejected — there is no cross-project consumer for this pipeline; it lives in deckhand, is called by deckhand code, and stays in-process. The asymmetry with paperbanana — which IS a separate project — explains why MCP makes sense there and not here.)

## 10. Risks and trade-offs

| Risk | Severity | Mitigation |
|---|---|---|
| **Sonnet × 2 (Brief + Critic) is expensive in token cost** | Medium | Brief and Critic dispatches are bounded by iteration caps; per-slide budget covers RENDER spend, not agent dispatches (which are deck-budget territory). The Director's Brief is the heaviest agent; if cost becomes a concern, demoting Brief to Haiku is a cheap experiment. |
| **Plateau detection is heuristic — may bump tier too early or too late** | Medium | Numeric scoring + 2-iteration window is conservative; combined with iteration cap as a hard backstop. Operator override available via `/iterate-slide enumerate`. |
| **Director's Critic could systematically over-grade or under-grade vision fidelity** | Medium | The Critic is the load-bearing decision-maker. Initial calibration via dogfood across the three founding examples (ships / man-o-war / sun phases). Per-axis breakdown lets operators see which axes the Critic is harsh or lenient on. |
| **Operator authoring fatigue** | Low–Medium | The prose-first model puts the operator in the driver's seat. Vision prose is a real authoring task. Mitigation: ChatGPT-or-Claude-assisted prose drafting; the strategy-map skill can offer to draft prose from talk-brief context with operator approval. |
| **Cascade budget pressure on hero slides** | Low | Default $1.00 / slide covers the entire Flash ladder. Operators wanting Pro 4K reach raise the per-slide budget. The pre-flight banner makes spend visible BEFORE commitment. |
| **The pipeline produces images that ARE the slide — no fallback if rendering fails entirely** | Low | The `abort` verdict path returns best-so-far. If even Ollama can't produce a viable draft, the manifest records the failure and the slide gets a placeholder; deck-qa flags it for operator attention. |
| **prose_version churn during long /iterate-slide sessions** | Low | Manifest history is append-only; storage cost is text + small PNGs per attempt. Operators inspecting history get full audit. |

## 11. Related decisions

- **Issue #88 / PR #104** — `full_bleed` assembler strategy. The consumer of this pipeline's output today.
- **paperbanana-integration-v2.md** — the structural mirror. paperbanana is external CLI; this is internal code. Both share the multi-stage / critic / manifest / iterate-slide pattern.
- **Issue #87 / PR #92** — register presets infrastructure (`infographic-narrative`, `atmospheric-photo`, etc.). The visual language the renderer's Stylist heuristics can reference for default style when prose is implicit.
- **Issue #90 (PR pending)** — prompt-engineer composition primitives. The Director's Brief will consume these for the assembly stage.
- **Issue #91 (PR pending)** — text-density warning. Wired into `ParsedVision.text_density_warning` for Prompt Reviewer pre-flight check.
- **Issue #105** — the parent feature ticket this spec satisfies.
