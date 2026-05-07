# Superpower Bridge — AI Persona Definitions

**Spec:** [2026-04-22-superpower-bridge-design.md](../../superpowers/specs/2026-04-22-superpower-bridge-design.md)
**Status:** v1.0 (full 19-section treatment)
**Date:** 2026-04-23

The bridge introduces one new AI Persona and reuses two existing ones. Phase 3's `enrich-deck` skill is orchestration code, not a persona.

This document captures the essential contractual sections needed to unblock the implementation plan. The remaining sections of the 19-section AI Persona Definition Template (detailed measurement blueprint, readiness scorecard, tripartite accountability owners, failure mode analysis) are deferred until a named Service Owner + SOP Owner + AI RM are appointed.

---

## Persona 1: Narrative Brief Architect

**Persona ID:** `ap-narrative-brief-architect`
**Service:** `bridge-services/bridge-narrative-brief-architect-ai` (L2 under a proposed new L1 `bridge-services`; see Canonical Model Delta below)

### 1. Purpose (Three Questions of Delegation)

**Q1 — What does this persona decide?**
Arc selection from a fixed typology (Problem-Solution, Hero's Journey, Build-Up-Reveal, Tension-Release, etc.). Communication intent framing (audience takeaway, tone, visual personality). Which kinds of slide content should carry placeholder markers.

**Q2 — What could go wrong if those decisions are wrong?**
User takes a poorly-framed brief into `/pptx` and gets a structurally weak deck. The deck is correctable by re-running the brief step; no binary output is mutated.

**Q3 — Who is accountable for the decision?**
The user, who approves the brief before it is written to `creative-brief.md`. The persona's output is advisory; the file is only saved after explicit user sign-off. Accountability transfers at step 7 of the collaborative flow.

### 2. Authority model

**Invoker.** Acts on behalf of the user who invoked `/bridge-brief`. Never writes `creative-brief.md` without explicit user approval of the draft. Cannot initiate actions that consume tokens, cloud API credits, or mutate files without per-turn user interaction.

**Confidence threshold for autonomous progress:** 0.7. If user answers are unambiguous, the persona drafts the next section without a further clarifying round-trip. Below 0.7, it asks a targeted clarifying question.

### 3. Risk classification

**Tier 1** (lowest). Output is a text document, not an executed action. No cost exposure. No OOXML mutation. No external API calls. No file writes outside the session's working directory. No reading of sensitive files.

### 4. Data contract

**Inputs:**
- User-provided topic (string)
- Duration (minutes, integer)
- Audience (string)
- Optional: brand brief or prior deck for tone reference (path)
- Optional: `confidentiality` tier (`public` / `internal` / `restricted`, defaults to `public`)

**Outputs:**
- `creative-brief.md` (structured markdown with three sections — see Section C of the bridge spec)

**NOT in scope:**
- Reading any DeckContext, StyleGuide, or brand profile
- Writing anywhere other than `creative-brief.md` in the session's working directory
- Calling image generation, running `/pptx`, modifying .pptx files

### 5. Escalation triggers

- **User cannot converge on a narrative arc after two proposal rounds** → offer all three arcs as parallel options with a side-by-side trade-off table.
- **Topic is ambiguous to the point where placeholder types cannot be determined** → ask the user explicitly rather than guessing.
- **Confidentiality tier is ambiguous** → ask the user to set it explicitly before proceeding; do not default silently.

### 6. Prohibited actions

- Must not write `creative-brief.md` without explicit user approval of the final draft.
- Must not embed per-slide prescriptions (the brief shapes intent; the superpower decides slide-level execution).
- Must not specify `name:` as the PptxGenJS shape-name property in exemplar code — MUST use `objectName:` (Spike 1 finding).
- Must not propose marker counts in excess of ~15% of total slides (marker pressure makes decks feel template-generated).

### 7. Model sizing

**Sonnet** by default. Creative reasoning about narrative arcs, emotional pacing, and visual personality is genuinely multi-dimensional — Haiku produces thin, generic arc descriptions that users repeatedly reject. The bounded scope (one brief per invocation) means Sonnet's cost is negligible vs. the cost of a poor brief guiding a 20-slide deck.

No escalation pathway needed. The brief is bounded; one Sonnet session completes the work.

### 8. Measurement hooks (lean — full blueprint in implementation)

- **Adherence rate:** does the superpower's output contain the marker types the brief specified? (Checked by the Phase 3 analyser; target ≥90% when brief uses correct `objectName:` protocol, per Spike 1 Variant A evidence.)
- **Approval turn count:** how many revision rounds before user approves the brief? (Target ≤ 2.)
- **Structural completeness:** were all three brief sections present and non-trivial? (Structural validation, target 100%.)

---

## Persona 2: Enrichment Cohesion Reviewer

**Persona ID:** `ap-enrichment-cohesion-reviewer`
**Service:** `bridge-services/bridge-enrichment-cohesion-reviewer-ai` (L2)

Analogous to the existing **Image Reviewer** persona (per-image quality verdict) but one level higher — this persona reviews the *assembled enriched deck* as a whole, before it is shown to the user.

### 1. Purpose (Three Questions of Delegation)

**Q1 — What does this persona decide?**
For each enriched slide: does the enrichment belong on this deck? Does it preserve cohesion with unenriched neighbouring slides? Does the AI background overpower the text's readability? Is the visual register consistent across enrichments?

**Q2 — What could go wrong if those decisions are wrong?**
A cohesion failure that slips through goes to the user in the delivery report. Cosmetic embarrassment; not a destructive outcome. User can drop or re-run any flagged enrichment.

**Q3 — Who is accountable for the decision?**
The `enrich-deck` orchestration skill invokes this persona and acts on the returned verdicts. The user is the final arbiter at delivery time (Section 3.5) and can override any verdict. The persona is advisory, not deciding.

### 2. Authority model

**Invoker.** Runs when the orchestration skill invokes it post-assembly. Returns a structured JSON verdict per enriched slide; never applies fixes itself, never regenerates images, never mutates the .pptx.

### 3. Risk classification

**Tier 1** (advisory only). No cost exposure, no file mutation, no external API calls.

### 4. Data contract

**Inputs:**
- Rendered PNG images, one per slide (the post-enrichment render produced by Section 3.4 step 6)
- Manifest listing which slides were enriched and with what enrichment type (`background` / `image` / `smartart`)
- Optionally: the original brief's Section B (visual personality) as intent grounding

**Outputs (JSON verdict per enriched slide):**
- `verdict`: `pass` / `flag_contrast` / `flag_inconsistency` / `flag_overcrowded` / `unassessable_rasterisation`
- `severity`: `blocking` / `suggestion`
- `reason`: one-line human-readable explanation
- Aggregate deck-level verdict: `pass` / `requires_revision`

### 5. Escalation triggers

- **>50% of enriched slides return `blocking`** → escalate to user before delivery. Do not attempt automated correction.
- **Visual assessment is ambiguous due to poor rasterisation quality** (LibreOffice SmartArt artefacts, PDF conversion glitches) → flag the slide as `unassessable_rasterisation` and recommend a PowerPoint render pass.
- **3 consecutive Haiku verdicts are ambiguous on the same slide** → escalate that slide's review to Sonnet.

### 6. Prohibited actions

- Must not apply corrections to the .pptx.
- Must not regenerate images.
- Must not pass verdicts on non-enriched slides (the unenriched originals are not in scope).
- Must not conflate LibreOffice SmartArt rendering failure with SmartArt construction failure (the XML may be correct; the rasteriser may be wrong).

### 7. Model sizing

**Haiku** by default. Single visual assessment per invocation, compact JSON output — matches the existing Image Reviewer's envelope exactly. **Escalate to Sonnet** when 3 consecutive ambiguous Haiku verdicts on the same slide, or when the Haiku confidence score on any verdict is below 0.5.

### 8. Measurement hooks

- **First-pass acceptance rate:** fraction of enriched decks delivered without a `blocking` cohesion flag. (Target ≥85%.)
- **Recall:** fraction of user-requested changes after delivery that the cohesion reviewer had already flagged. (Target ≥70% — the reviewer exists to catch issues before they reach the user.)

---

## Persona 3 (reused, contract extension): Image Reviewer

The existing Image Reviewer persona ([.claude/agents/image-reviewer.md](../../../.claude/agents/image-reviewer.md)) is invoked by the bridge's imagegen-bridge calls during Phase 3. The bridge extends its data contract minimally:

- **Adds `source: enrichment-bridge`** to the invocation context so iteration counters don't leak across contexts.
- **Adds the originating marker type** (`IMAGE:` / `BG:`) so the reviewer can apply type-appropriate composition criteria.

No behavioural change required. Existing escalation from Haiku to Sonnet on 3 consecutive refine verdicts remains unchanged.

---

## Persona 4 (reused, contract extension): Prompt Engineer

The existing Prompt Engineer persona ([.claude/agents/prompt-engineer.md](../../../.claude/agents/prompt-engineer.md)) is invoked by the bridge's imagegen-bridge calls. The bridge extends its data contract minimally:

- **Adds two new composition modes:** `enrichment-element` (for IMAGE marker replacement) and `enrichment-background` (for BG marker atmospheric backgrounds). These are parallel to the existing `atmospheric` / `spatial-intent` / `element-level` modes.
- **Accepts partial `creative-brief.md` content** (Section B — communication and visual intent) as style grounding when the main-pipeline's Slide Prompt Composer is not in the loop.

No behavioural change required.

---

## Why enrich-deck is NOT a persona

Phase 3's `enrich-deck` skill is orchestration, not creative reasoning:

- **Deterministic:** parses OOXML, classifies slides, applies enrichments. Given the same .pptx and the same user selections, it produces the same output byte-for-byte (modulo AI image non-determinism, which is quarantined to the Prompt Engineer + Image Reviewer invocations).
- **No authority of its own:** it invokes Prompt Engineer, Image Reviewer, and (above) Enrichment Cohesion Reviewer. Each sub-invocation is where real reasoning happens.
- **Budget enforcement is mechanical:** per-call cost deducted from `budget_cap_usd`, halt if exhausted. No judgment required.

Treating enrich-deck as orchestration rather than a persona simplifies tripartite accountability (only three personas need owners) and matches the existing Deck Conductor pattern, where the conductor orchestrates but doesn't itself carry a creative-output contract.

---

## Tripartite accountability

Both personas require tripartite owners per AI-First BSA Chapter 9. v0.1 ships with a **consolidated tripartite** — Steve Jones holds all three roles, with the explicit understanding that they will be split as the maintainer team grows. This is methodology-valid (Chapter 9 permits consolidated tripartite for single-maintainer projects at Tier 1 risk) and unblocks readiness scorecard Item 3.

| Persona | Service Owner | SOP Owner | AI Risk Manager |
|---------|---------------|-----------|-----------------|
| Narrative Brief Architect | Steve Jones | Steve Jones | Steve Jones |
| Enrichment Cohesion Reviewer | Steve Jones | Steve Jones | Steve Jones |

**Split trigger:** when a second human maintainer joins the project, the SOP Owner role for both personas transfers to that person. When a third joins, the AI Risk Manager role transfers (separation of provider, consumer, and AI risk perspectives is the methodology's intent). Tracked in `CLAUDE.md`'s Bridge status section.

## Measurement blueprint — full 5-tier coverage

All measurement hooks named in the v0.1 skeleton are now implemented in `plugins/jack-tar-superpower-bridge/src/measurement.py`. v1.0 distributes them across the methodology's 5 tiers (Chapter 7) so the blueprint is hierarchically complete, not just an Activity-tier instrumentation list.

### Tier 1 — Strategic objective

| Metric | Target | Source |
|--------|--------|--------|
| Time-to-conference-quality-deck | ≤ 90 min from `/bridge-brief` to delivered enriched deck | wall-clock between `bridge-measurements.jsonl` brief entry and enrichment entry |

### Tier 2 — Service-level (KEY_RESULT / VALUE_CONTRIBUTION)

| Metric | Target | Source |
|--------|--------|--------|
| Cost per dogfood-grade deck | ≤ $1.00 average across runs | sum of `bridge-cost-ledger.jsonl` per run, averaged |
| Cohesion blocking rate | ≤ 15% of enriched decks ship with cohesion-blocking flags | `kind: enrichment` rows where `first_pass_acceptance: false` divided by total enrichment rows |

### Tier 3 — Experience Level Agreement (XLA)

| Metric | Target | Source |
|--------|--------|--------|
| Speaker satisfaction with `/bridge-brief` output | ≥ 4.0 / 5.0 mean rating | post-run free-form annotation in `enrichment-report.md` "Speaker feedback" section (added by the user manually); aggregated offline |
| Visual cohesion as judged by audience | ≥ 4.0 / 5.0 mean rating from post-talk speaker debrief | same source |

### Tier 4 — Activity (per-persona hooks from v0.1 skeleton)

| Hook | Persona | Module entry-point | Target |
|------|---------|---------------------|--------|
| Adherence rate | Narrative Brief Architect | `record_enrichment_run(adherence_rate=...)` (computed by /enrich-deck Step 12) | ≥ 90% |
| Approval turns | Narrative Brief Architect | `record_brief_run(approval_turns=...)` | ≤ 2 |
| Structural completeness | Narrative Brief Architect | `record_brief_run(structural_complete=...)` | 100% |
| First-pass acceptance | Enrichment Cohesion Reviewer | `record_enrichment_run(first_pass_acceptance=...)` | ≥ 85% |
| Cost-per-deck (generation+review) | both (orchestration) | `record_cost_event(kind, cost_usd, ...)` | rolls up into Tier 2 |

### Tier 5 — Contextual

| Metric | Purpose | Source |
|--------|---------|--------|
| Privacy tier distribution | Tells us how often confidentiality blocks cloud spend | `confidentiality` field in `bridge-measurements.jsonl` `kind: brief` rows |
| Marker-source breakdown (OOXML vs JS-fallback) | Tells us how often /pptx drifts from the `objectName` brief instruction | `js_fallback_used` counter (computed offline from `bridge-measurements.jsonl`; needs to be added to the enrichment row in a v1.1 update) |

### Recall hook — explicitly demoted to offline analysis (panel finding #11)

The Recall hook (≥ 70%) listed in the v0.1 persona contract is NOT instrumented per-run. v0.1 had it as an unmet target which created a false amber on Item 6. v1.0 demotes it to an offline analysis item: "Recall is computed offline from delivery-report annotations — count user-requested changes after delivery against the cohesion reviewer's flag set." A proxy is captured during the run via the `flags_for_user_attention` section of `enrichment-report.md`; comparing against post-delivery user requests is a manual exercise after the talk has been delivered.

## Readiness scorecard — v1.0 status

| # | Checkpoint | v0.1 | v1.0 | Evidence |
|---|------------|------|------|----------|
| 1 | Persona contracts written | green | green | This document |
| 2 | Authority model defined | green | green | Section 2 of each persona |
| 3 | Risk classification + accountability | amber | green | Tier 1 risk; consolidated tripartite (Steve Jones × 3) acceptable for single-maintainer project per Chapter 9 |
| 4 | Data contracts captured | green | green | Section 4 of each persona |
| 5 | Vanilla-Agent validation | amber | amber | Pending Phase 15 dogfooding gate (Tasks 33–35) |
| 6 | Measurement blueprint approved | amber | green | 5-tier blueprint above; hooks live in `src/measurement.py` |
| 7 | Escalation triggers documented | green | green | Section 5 of each persona |
| 8 | Prohibited actions enumerated | green | green | Section 6 of each persona |

Item 5 remains amber until Task 35 GO verdict.

---

## Canonical model delta (proposed for `.bsa/models/jack-tar-deckhand.json` v1.5.0)

- **New L1 service:** `bridge-services` under L0 Presentation Engineering.
- **New L2 services (personas):**
  - `bridge-narrative-brief-architect-ai`
  - `bridge-enrichment-cohesion-reviewer-ai`
- **New L2 services (skills):**
  - `bridge-narrative-prebrief` (hosts `/bridge-brief`)
  - `bridge-deck-enrichment` (hosts `/enrich-deck`)
- **New interactions** (minimum 9):
  1. Speaker → bridge-narrative-brief-architect-ai (TalkBrief-lite)
  2. bridge-narrative-brief-architect-ai → Speaker (CreativeBrief)
  3. Speaker → bridge-deck-enrichment (.pptx path + optional `budget_cap_usd`, `confidentiality` tier)
  4. bridge-deck-enrichment → imagegen-bridge (image generation requests)
  5. bridge-deck-enrichment → image-reviewer (per-image verdict)
  6. bridge-deck-enrichment → smartart-extractor (marker → spec conversion)
  7. bridge-deck-enrichment → msft-smartart/engine (carrier render)
  8. bridge-deck-enrichment → msft-smartart/assembler_patch (inject)
  9. bridge-deck-enrichment → bridge-enrichment-cohesion-reviewer-ai (deck-level review)
  10. bridge-deck-enrichment → Speaker (enriched deck + report)

- **Cross-Domain SOP Register entry:** SOP `smartart-injection` (owner `jack-tar-msft-smartart`, consumer `jack-tar-superpower-bridge`, archetype: **Collaborator**).

- **Dependency Register entries:**
  - `DEP-BRIDGE-SMARTART-01` — assembler_patch.inject API surface
  - `DEP-BRIDGE-OLLAMA-01` — via imagegen-bridge
  - `DEP-BRIDGE-CLOUD-01` — via imagegen-bridge
  - `DEP-BRIDGE-PPTXGENJS-01` — parseable build-script contract (fallback)
  - `DEP-BRIDGE-PYTHON-PPTX-01` — primary OOXML source

---

## Readiness scorecard items at v0.1

Per methodology Chapter 9's 8-checkpoint scorecard, three items are **amber** at this spec stage and will need to be resolved before deployment readiness:

- **Item 3 (risk classification)** — personas tiered above, but tripartite owners (Service Owner + SOP Owner + AI RM) unassigned.
- **Item 5 (Vanilla-Agent validation)** — Spikes 1-3 cover most of this. A zero-knowledge run of `/enrich-deck` against an unseen superpower deck should form part of the release gate before v1 ships.
- **Item 6 (measurement blueprint approved)** — lean measurement hooks captured above; full 5-tier blueprint deferred.

Items 1, 2, 4, 7, 8 should be **green** once the implementation plan is written.

---

## References

- Parent spec: [docs/superpowers/specs/2026-04-22-superpower-bridge-design.md](../../superpowers/specs/2026-04-22-superpower-bridge-design.md)
- Team review: [docs/superpowers/specs/2026-04-23-superpower-bridge-team-review.md](../../superpowers/specs/2026-04-23-superpower-bridge-team-review.md)
- Existing persona examples: [.claude/agents/image-reviewer.md](../../../.claude/agents/image-reviewer.md), [.claude/agents/prompt-engineer.md](../../../.claude/agents/prompt-engineer.md)
- Methodology reference: see `.claude/agents/TOOLKIT-REFERENCE.md`
