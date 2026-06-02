# Creative Vision Renderer — Architecture Decision Record

**Status:** Accepted — implementation in progress on branch `feat/creative-page-renderer`
**Date:** 2026-05-21
**Issue:** [#105](https://github.com/SteveGJones/jack-tar-deckhand/issues/105)
**Spec:** [docs/superpowers/specs/2026-05-21-creative-vision-renderer-design.md](../superpowers/specs/2026-05-21-creative-vision-renderer-design.md)
**Plan:** [docs/superpowers/plans/2026-05-21-creative-vision-renderer.md](../superpowers/plans/2026-05-21-creative-vision-renderer.md)
**Sibling ADR:** [paperbanana-integration-v2.md](paperbanana-integration-v2.md) — the technical-figure equivalent

---

## 1. Context

After v1.4.2 (issue #88), jack-tar-deckhand has three concepts that should compose, but only two are built. **paperbanana** renders technical, fixed-structure figures — architecture diagrams, equations, ablation plots — through the `academic_figure` strategy, running as an external CLI tool. **`full_bleed`** is the assembler strategy that places a picture edge-to-edge with no chrome. The missing third leg is a renderer for **creative, operator-directed vision images**.

These are slides where the operator describes a specific rich vision in natural prose — four named warships in a four-way sea battle with named logos, framework components as cabins inside an old man-o-war in a 1950s cartoon style, sun phases as a left-to-right horizontal progression inside a single frame — and the pipeline's job is to deliver that *specific* vision faithfully. This is not abstract mood evocation ("trust as a warm glow"). That category is already covered by generic backdrop generation, which renders atmospheric imagery well but has no machinery to honour named entities, spatial directives, or compositional progressions. The distinction matters because generic backdrop generation runs a single-shot Flash tier with a best-effort prompt; the creative vision renderer runs a multi-stage agent pipeline because there is an authoritative ground truth — the operator's prose — to grade rendered output against.

### What this is not

- **Not a replacement for paperbanana** — paperbanana handles technical figures with formal structure (methodology diagrams, training curves, citations). The creative vision renderer handles creative, metaphorical, operator-directed imagery. The two strategies are complementary, not competing.
- **Not an extension of generic backdrop** — backdrop generation optimises for visual atmosphere behind text content. Creative vision slides ARE the content; the slide has no text layer.
- **Not an extension of `full_bleed`** — `full_bleed` is an assembly directive (how to place an image). `creative_vision` is a rendering strategy (how to produce an image). The pairing is intentional: every `creative_vision` slide is assembled as `full_bleed`, but the two concerns stay separated.

### Founding examples that shaped the design

The three examples below drove every design decision in the pipeline. A design that cannot credibly render all three is the wrong design:

1. **Four warships (entity fidelity under spatial constraint):** SAP, Databricks, OpenAI, Anthropic as warships on a lake, engaged in a four-way naval battle. Tests: four named entities, spatial placement, compositional balance in a symmetric scene.
2. **Man-o-war cabins (containment + style register):** framework components (retrieval, planner, stylist, visualizer, critic) as named cabins inside an old man-o-war hull, 1950s cartoon style. Tests: within-frame containment hierarchy, named labels, explicit style register.
3. **Sun phases (within-frame progression):** sun phases as a left-to-right horizontal progression within a single frame. Tests: compositional axis, ordered sequence, no text required.

All three are single images. All three require a critic that can grade entity presence, spatial adherence, and style fidelity independently. A single-score "pass/fail" verdict is insufficient — the failing warship example above passes on style (dramatic naval scene) while failing on entity fidelity (only 3 of 4 ships labelled).

---

## 2. Decision

### Framing

The creative vision renderer is an **internal pipeline** inside the deckhand plugin. It mirrors paperbanana structurally — multi-stage agent pipeline, internal critic loop, manifest with run-id, /iterate-slide integration — but renders a fundamentally different artefact (creative vision vs technical figure) and runs entirely **in-process** inside the deckhand plugin. paperbanana is external because it is its own project with an independent release lifecycle; this pipeline has no cross-project consumer and belongs in deckhand.

### Strategy enum

A new `creative_vision` value is added to the StrategyMap strategy enum alongside the existing values (`full_render`, `background`, `backdrop`, `pragmatic_composition`, `composed`, `full_bleed`, `academic_figure`). The `creative_vision` strategy always pairs with `full_bleed` assembly. It is **operator-opt-in only** — neither the strategy classifier nor the narrative-architect emits it automatically. The cascade economics are high enough that accidental auto-classification is unacceptable.

### Pipeline design

Four agents, two gates, one cascade:

- **Three new agents** (Director's Brief, Prompt Reviewer, Director's Critic) plus the **existing image-reviewer** (reused unchanged).
- **Two structural gates**: a text-side gate (Brief ↔ Prompt Reviewer) before each render, and an image-side gate (image-reviewer → Director's Critic) after each render.
- **One cascade**: Ollama free draft → cloud tier ladder, with tier-first resolution-step and model-bump on plateau.

### Rationale

**Why an internal pipeline rather than an external CLI (like paperbanana)?** Because this pipeline's consumers are exclusively deckhand SKILL.md flows — imagegen-bridge, iterate-slide, deck-assembler. It has no cross-project consumer and no independent release lifecycle. The paperbanana decision inverted this: paperbanana is an externally maintained PyPI package with its own CLI and MCP surface; treating it as an external tool is exactly right. Treating a deckhand-specific sub-pipeline as an external tool would add process-spawn overhead, a subprocess interface, and a separate release cadence for no benefit.

**Why a new `creative_vision` strategy enum value rather than extending `full_bleed` with a `vision_prose` field?** Two reasons. First, the pipeline is paperbanana-sized: three new agents, three new schemas, a cascade module, and /iterate-slide integration. A field on `full_bleed` would imply minor variation; this is a distinct rendering strategy. Second, keeping assembly and rendering concerns separated makes the system legible — operators read the strategy name and know which pipeline fires.

**Why a text-side gate (Prompt Reviewer) before every render?** The most common failure mode when iterating image prompts is that a refinement pass drops required entities to fix a different axis. A text-side gate catches this before spending a render token. The gate is pure text — cheap, fast, bounded to three iterations by default. Live discovery during the design loop (2026-05-21 brainstorm) surfaced this as the highest-leverage addition; it is not in paperbanana because paperbanana's prompts are structurally generated by its Planner agent, not human-authored prose.

**Why sequential image-side gates (image-reviewer THEN Director's Critic) rather than a combined reviewer?** The two agents have different competence scopes. image-reviewer (existing Haiku) grades visual quality basics — garbled text, palette drift, artefacts. Director's Critic grades vision fidelity — named entities present and spatially correct, style register honoured, compositional axis respected. Combining them into one agent would require Sonnet on every check (expensive for the quality gate) or risk visual-quality concerns dominating the vision-fidelity verdict. Sequential gates: image-reviewer first as a cheap quality triage, Critic only when the image passes basic quality.

**Why operator-opt-in only?** The cascade can spend up to $2.50 per slide in the worst case (Pro 4K ceiling). A misclassified `full_bleed` slide that should have been `background` would silently run the full cascade. The strategy must be intentional.

### Alternatives considered and rejected

| Option | Why rejected |
|---|---|
| **Extend `full_bleed` with `vision_prose`** | Conflates assembly and rendering concerns; pipeline size is decision-record-worthy, not a field extension |
| **External CLI (subprocess, like paperbanana)** | No cross-project consumer; adds 150 ms spawn overhead + subprocess interface for an internal pipeline |
| **Single combined reviewer (image-reviewer + vision-fidelity in one agent)** | Conflates quality and fidelity concerns; Sonnet-always overhead for quality checks; harder to calibrate independently |
| **Auto-classify from narrative-architect signals** | Cascade economics too high for heuristic; operator intent must be explicit |
| **Reuse paperbanana for creative subjects** | paperbanana's Planner is tuned for formal academic figures; creative subjects produce structure-first outputs (labels and boxes) instead of compositional scene rendering — confirmed by 2026-05-21 brainstorm |

---

## 3. Architecture

Four agents, two gates, one cascade. The pipeline runs per slide; the manifest persists per slide.

### 3.1 Agent roles

| Agent | Status | Model | Role |
|-------|--------|-------|------|
| Director's Brief | NEW | Sonnet | Parses operator prose into a `ParsedVision` intermediate; writes a render-ready prompt targeting the current tier's capabilities; rewrites the prompt on every refinement path, consuming Prompt Reviewer feedback, image-reviewer feedback, and Director's Critic recommendations |
| Prompt Reviewer | NEW | Haiku | Text-side gate — grades the Brief's prompt against the operator's prose and `ParsedVision`; returns `pass | refine` with per-axis feedback (entities present? spatial honoured? style cue retained? text density within #91 threshold?); never sees rendered images |
| image-reviewer | EXISTING | Haiku | Image-side quality gate — grades the rendered image for visual quality basics (artefacts, palette drift, garbled text); returns compact JSON verdict; unchanged from its current contract |
| Director's Critic | NEW | Sonnet | Image-side vision-fidelity gate — grades the rendered image against the operator's prose + ParsedVision; returns per-axis scores (entity fidelity, spatial fidelity, style fidelity, quality, composition) + plateau signal + `gap_location` for /iterate-slide routing; the load-bearing decision-maker for tier escalation |

The maker/judge separation is structurally enforced: Director's Brief makes prompts; Prompt Reviewer judges prompts. Every image goes through image-reviewer and Director's Critic. No agent grades its own output.

### 3.2 Per-tier loop

```
operator's prose
       │
       ▼
[Director's Brief] ←──── refine ─────────────────────┐
       │                                              │
       ▼                                              │
[Prompt Reviewer] ──── refine (cap: 3) ──────────────┤  text-side loop
       │ pass                                         │
       ▼                                              │
[Visualizer @ current tier] (RENDER — costs money)    │
       │                                              │
       ▼                                              │
[image-reviewer] ──── refine ────────────────────────┤  back to Brief
       │ pass                                         │  (never re-render
       ▼                                              │  directly)
[Director's Critic]                                   │
       │                                              │
       ├─ refine_at_tier ───────────────────────────────┘
       │
       ├─ escalate_tier ──> bump tier; resume from Brief with tier-change context
       │
       ├─ pass ───────────> ACCEPT + persist manifest
       │
       └─ abort ──────────> budget_exhausted — return best-so-far
```

The rule "every refinement path returns to the Director's Brief" prevents the prompt from drifting as feedback accumulates. This is the key structural invariant.

### 3.3 Iteration caps (defaults)

| Gate | Default cap |
|---|---|
| Text-side per render | 3 |
| Image-side at Ollama (T0) | 5 |
| Image-side at Flash tiers (T1–T3) or Recraft Standard | 3 |
| Image-side at Pro 1K / 2K (T4–T5) or Recraft Pro | 2 |
| Image-side at Pro 4K or Recraft 4K (ceiling) | 1 |

All caps are operator-overridable per slide via the strategy-map `iteration_caps_override` field. See spec §3.4 for the full YAML override surface.

### 3.4 Code organisation

The pipeline lives in `plugins/jack-tar-deckhand/src/creative_vision/` (sub-package) with a top-level entry point at `src/creative_vision_dispatch.py` (mirrors `paperbanana_dispatch.py` in naming and role). Three new agent definitions in `plugins/jack-tar-deckhand/agents/`. See spec §7 for the full file tree.

---

## 4. Contracts

Three new JSON schemas under `plugins/jack-tar-deckhand/src/schemas/`, plus an extension to the existing `strategy_map.schema.json`.

**`parsed_vision.schema.json`** — the intermediate produced by Director's Brief and consumed by Prompt Reviewer and Director's Critic. Carries: `original_prose` (verbatim, never rewritten), `subjects` (named entities with spatial slots), `spatial_directives` (setting, layout, containment, named relationships), `style` (explicit + implied register + brand-profile inheritance pointer), `composition` (progression axis, primary focus, compositional rules), `delivery` (scale + aspect), and `text_density_warning` (the issue #91 hook — fires pre-render when estimated text elements exceed the threshold). `original_prose` is the ground truth; the Critic grades every rendered image against `subjects` and `spatial_directives` from this structure.

**`directors_critic_verdict.schema.json`** — what Director's Critic returns per rendered image. Carries: `verdict` (`pass | refine_at_tier | escalate_tier | abort`), `per_axis_scores` (entity_fidelity, spatial_fidelity, style_fidelity, quality, composition; 0–100 each), `issues` (array of per-axis detail), `gap_location` (`prose | prompt | tier | unknown` — consumed by /iterate-slide to route feedback), `recommended_action` (prose consumed by Director's Brief on next refinement), `tier`, `iteration_index`, `plateau_signal` (true when scores haven't improved ≥5 points across 2 consecutive iterations — drives `escalate_tier`).

**`creative_vision_manifest.schema.json`** — persisted state per slide across the full lifecycle. Carries: `run_id`, `slide_number`, `strategy`, `prose_history` (versioned array — prose revision bumps version, history preserved), `attempts` (per-attempt array carrying text iterations, render metadata, reviewer verdicts, Critic verdict, cumulative cost), `final` (accepted image path, tier, total cost, iteration count), and `iterate_slide_hooks` (the surface /iterate-slide reads: `can_revise_prose`, `can_refine_prompt`, `can_escalate_tier`, `current_tier`, `next_tier_available`, `remaining_budget_usd`).

**`strategy_map.schema.json` extension** — adds `creative_vision` to the strategy enum and a `creative_vision` block (object with required `vision_prose` and optional `budget_usd`, `allowed_ceiling`, `iteration_caps_override`). The block is **required when `strategy: creative_vision`** and **forbidden otherwise**, enforced via `allOf` conditional. Mirrors how the existing `smartart_config` block works. `vision_prose` is the only required field inside the block; all other fields take cascade defaults. See spec §4 for full schema shapes with examples.

---

## 5. Cascade economics

### 5.1 Default ladder (`brand_fidelity: none | approximate`)

Ollama (free) → Nano Banana Flash 1K/2K/4K → Nano Banana Pro 1K/2K/4K.

| Tier | Cost per render |
|---|---|
| T0 — Ollama | $0.00 |
| T1 — Flash 1K | $0.067 |
| T2 — Flash 2K | $0.101 |
| T3 — Flash 4K | $0.151 |
| T4 — Pro 1K | $0.134 |
| T5 — Pro 2K | $0.193 |
| T6 — Pro 4K | $0.240 |

### 5.2 Brand-fidelity ladder (`brand_fidelity: exact`)

Ollama → Recraft V4 Standard 1K → Recraft V4 Pro 2K → Recraft V4 Pro 4K (creative-upscale chain, ~$0.50). The two ladders are mutually exclusive per slide. Mixing mid-cascade would shift the style register and corrupt `style_fidelity` scoring.

### 5.3 Plateau detection

Director's Critic returns `escalate_tier` when any of: (a) per-axis scores haven't improved by ≥5 points on any axis across 2 consecutive iterations (`plateau_signal: true`), (b) per-tier iteration cap exhausted with at least one axis still <80, or (c) Critic explicitly diagnoses a model capability ceiling. On `escalate_tier`, the orchestrator bumps to the next tier, resets the per-tier counter, and hands the Critic's diagnosis to Director's Brief as tier-change context.

### 5.4 Budget enforcement

Before every paid render, the orchestrator checks `cumulative_cost_usd + projected_next_render_cost > budget_usd`. If the check fails, Critic verdict becomes `abort`, and the pipeline returns the best-so-far image from the manifest. Ollama renders and the text-side loop do not count against `budget_usd`. Default per-slide budget is $1.00, covering the full Flash ladder (≈$0.957 worst case). Operators raise the ceiling via `creative_vision.budget_usd` in the strategy-map entry. The /iterate-slide `enumerate` mode can later refresh the budget and continue from the saved manifest.

### 5.5 Deck-level visibility

`creative_vision` slides participate in `src/budget_tracker.py`. At strategy-map approval the skill surfaces a pre-flight cost banner: deck-level worst-case spend, per-slide committed spend, and remaining deck budget. The banner makes cascade commitment visible before any renders fire.

See spec §5 for the full cost table, default YAML override surface, and per-tier iteration cap details.

---

## 6. Operator surface

### 6.1 Strategy-map authoring

The `/strategy-map` skill becomes vision-aware. When a slide is assigned `creative_vision`, the skill interactively gathers the vision prose and surfaces the cost banner before committing. Operators can defer prose (the skill records the strategy with `pending_vision_prose: true`; the pipeline halts at the slide until prose is provided and the operator re-runs the skill step). Claude-assisted prose drafting is available: the skill can draft vision prose from talk-brief context and present it for operator approval before locking it.

### 6.2 imagegen-bridge dispatch

`imagegen-bridge` reads the strategy-map, detects `strategy: creative_vision`, and calls `creative_vision_dispatch.run(slide_entry, deck_dir, budget_remaining)` instead of the standard `image_router` path. The dispatch returns a final image path and manifest. The bridge folds the result into the standard `ImageManifest` so `deck-assembler` sees a normal image entry. The `creative_vision` slide is then assembled via `buildFullBleedSlide` (issue #88 v1.4.2).

### 6.3 Deck-conductor placement

```
Step 3.5: strategy-map     ← vision-aware prose authoring + cost banner
Step 4:   smartart-selector  ← SKIPPED for creative_vision slides
Step 5:   smartart-extractor ← SKIPPED for creative_vision slides
Step 7:   imagegen-bridge  ← dispatches to creative_vision_dispatch.py
Step 8:   deck-assembler   ← buildFullBleedSlide for creative_vision output
Step 9:   deck-qa          ← text-based AP checks skipped; palette + image quality only
```

### 6.4 /iterate-slide integration — three feedback channels

`creative_vision` slides get three distinct refinement channels in `/iterate-slide`:

| Channel | What it does |
|---|---|
| **Revise prose** | Operator edits the vision prose; pipeline restarts with the new prose, bumps `prose_version`, preserves prior attempt history in the manifest |
| **Refine prompt** | Operator adds a targeted correction note; Director's Brief rewrites the prompt with the note as context; pipeline re-renders at the current tier |
| **Escalate tier** | Bumps to the next cascade tier; only offered when `next_tier_available` and `remaining_budget_usd > tier_cost`; Director's Critic diagnosis displayed so operator understands why the Critic requested escalation |

In `/iterate-slide auto` mode, the skill reads `gap_location` from the Critic's last verdict: `prose` → prompt operator to revise (never autonomous prose changes); `prompt` → refine prompt and re-render; `tier` → escalate if budget allows. In `/iterate-slide draft` mode, the skill heuristically routes the operator's free-form note to channel 1 or 2 and confirms the routing before proceeding.

See spec §6 for the strategy-map entry shape and full authoring flow.

---

## 7. Risks and trade-offs

| Risk | Severity | Mitigation |
|---|---|---|
| Sonnet × 2 (Director's Brief + Director's Critic) per iteration has non-trivial token cost | Medium | Iteration caps bound dispatches; per-slide budget covers RENDER spend — agent dispatch cost falls under deck budget, not slide budget. If Brief token cost becomes a concern, demoting Brief to Haiku for the prompt-rewrite step is a cheap experiment |
| Plateau detection heuristic may escalate tier too early or too late | Medium | Numeric threshold (5-point improvement across 2-iteration window) is conservative; combined with per-tier iteration cap as a hard backstop. Operator can override via `/iterate-slide enumerate` |
| Director's Critic calibration — may systematically over-grade or under-grade vision fidelity | Medium | Per-axis breakdown surfaces Critic biases visibly. Initial calibration via the three founding examples (ships / man-o-war / sun phases). Operators can adjust prose and rerun without spending additional render budget |
| Operator authoring fatigue — vision prose is a real authoring task | Low–Medium | Claude-assisted prose drafting offered by the strategy-map skill; defer-prose pattern avoids blocking the pipeline while operator composes. The prose-first model puts the operator in the driver's seat intentionally — this is operator-as-director |
| Cascade budget pressure on hero slides | Low | Default $1.00/slide covers the entire Flash ladder. Pre-flight cost banner at strategy-map approval makes spend visible before commitment. Operators explicitly raise the ceiling for Pro-tier hero slides |
| Full-image render failure — the slide IS the image; no fallback text layer | Low | `abort` verdict returns best-so-far from manifest; deck-qa flags the slide for operator attention; /iterate-slide can continue from the saved manifest after refreshing the budget |

---

## 8. Related decisions

- **Issue #88 / PR #104** — `full_bleed` assembler strategy. The downstream consumer of every image this pipeline produces. Creative vision slides are assembled as `full_bleed` slides.
- **[paperbanana-integration-v2.md](paperbanana-integration-v2.md)** — the structural mirror for this ADR. paperbanana is an external CLI tool rendering technical figures; the creative vision renderer is an internal pipeline rendering operator-directed creative imagery. Both share the multi-stage-pipeline / critic-loop / manifest / /iterate-slide pattern. The asymmetry (external vs internal) is explained by cross-project consumer presence: paperbanana has one, this pipeline does not.
- **Issue #87 / PR #92** — register presets (`infographic-narrative`, `atmospheric-photo`, etc.). The visual language the Director's Brief can reference for default style register when the operator's prose is stylistically implicit.
- **Issue #90 (pending)** — prompt-engineer composition primitives (two-port-fixture, asymmetric-towers, multi-craft-hub, instrument-grid, three-tier-chain). The Director's Brief will consume these for the composition-construction stage of prompt assembly.
- **Issue #91 (pending)** — prompt-engineer text-density warning. Wired into `ParsedVision.text_density_warning`: the Prompt Reviewer fires the threshold check before any render, catching >12–15 text elements that would garble at Nano Banana Flash.
- **Issue #105** — the parent feature ticket for this implementation. All tasks for the creative vision renderer are tracked here.
