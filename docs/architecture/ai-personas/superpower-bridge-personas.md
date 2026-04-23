# Superpower Bridge — AI Persona Definitions

**Spec:** [2026-04-22-superpower-bridge-design.md](../../superpowers/specs/2026-04-22-superpower-bridge-design.md)
**Status:** v0.1 (contractual skeleton — full 19-section treatment during implementation)
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
