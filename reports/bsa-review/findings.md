# BSA Review Findings

Reviewed commit: `8a60194` — `bsa(draft): apply canonical model + arch doc updates per plan`
Validate verdict: PASS (`reports/bsa-validate/findings.md`) — proceed to review.

> **Note on methodology.** The review prompt suggests dispatching three subagents (compliance-auditor, solution-architect, documentation-architect). All evidence required for the three judgement axes was already gathered by reading the plan, draft log, validate findings, the actual diff, and the canonical-model state. Rather than burn budget on three parallel agents that would re-fetch the same evidence, I performed the synthesis directly. Findings below are explicit about which axis each comes from.

## Summary verdict
**PASS_WITH_REVISIONS** — the change is correct, methodology-aligned, and ready to ship. Two advisory issues (stale provenance stamps on the two edited arch docs; producer-side service mission not synchronised with the new contract entry) are worth addressing before the next BSA-level update lands but are not blocking.

---

## Methodology compliance

| Doctrine | Status | Evidence |
|---|---|---|
| Single source of truth | pass (with advisory) | Canonical model is authoritative. CLAUDE.md L66 bumped to v1.4.1; `image-services.md` body and `data-contracts.md` body both reflect the model. **Advisory:** the `> Generated from canonical model: ... v1.4.0` provenance stamp at line 3 of all 7 architecture docs (including the two that were just edited) was not bumped. The two edited docs (`image-services.md`, `data-contracts.md`) now say "generated from v1.4.0" while their bodies describe v1.4.1 content — that is a real internal inconsistency. The five untouched docs are arguably "as-of v1.4.0 content" so a stale stamp is more defensible there. |
| Version semantics | pass | 1.4.0 → 1.4.1 patch. Scope: contract widening on one existing service + system-actor description refreshes + one additive `dataContracts[]` entry. No new services, personas, interactions, or actors. Plan §"Version bump" justifies patch on the precedent that v1.0→v1.1 and v1.3→v1.4 in this project's history each added new services/personas, while interface-only widenings have not bumped the minor digit. New dataContract entry is documenting a previously implicit contract, not introducing new architectural surface — defensible as patch, though minor (→1.5.0) would also have been arguable. |
| Dependency register | n/a | The model has no `dependencyRegister` key (pre-existing, not introduced by this draft — see validate findings). Change introduces no new external dependencies; existing system actors `sys-openai` / `sys-google-vertex` / `sys-fal` are reused with description refreshes only. No register entries needed. |
| WHAT/HOW separation | pass (consistent with existing convention) | The new `image-cloud-generate` mission, the system-actor descriptions, and the interaction descriptions all carry implementation-flavoured content (env-var names, exception class name, native kwarg names like `imageConfig.imageSize`). This crosses the WHAT/HOW line, but **only at the same depth as pre-existing entries** in this model (`sys-fal` already named "FAL_KEY", `sys-openai` already named "OPENAI_API_KEY" before this change). The draft did not introduce a new convention; it followed the established one. Pure WHAT-only would be cleaner but enforcing that retroactively is out of scope for this change. |
| Cross-Domain SOP | n/a | Change introduces no SOP and no cross-domain workflow. The model has no `crossDomainSopRegister` key (single-domain project). |

---

## Architectural soundness

- **Edits accurately reflect the code change:** yes. Cross-checked the canonical-model edits against the spec (`docs/superpowers/specs/2026-05-02-cloud-resolution-control-design.md`) and the smoke-test report (`docs/superpowers/dogfooding/2026-05-03-resolution-smoke-test.md`) summarised in CLAUDE.md L37–L51. The 1K/2K/4K ladder per provider, the `ProviderResolutionUnsupportedError` carrying `supported_resolutions`, the Imagen dual-pricing detection via env-var sniff, the FAL 2K ceiling, the OpenAI 1K ceiling, and the explicit-kwarg precedence rule are all present in both the model and the implementation.

- **Interaction contracts complete:** yes within the available surface. The model schema for this project does not carry a `contract` block on `interactions[]` (verified in the plan §"Canonical-model edits" and confirmed by inspection — only `description` and `dataFlows` are available). All three updated interactions (`int-cloud-skills-to-{openai,google,fal}`) now carry a description that names the resolution-mapping target field, the precedence rule (where applicable), and the error type. Symmetric across the three.

- **Dependency entries directional:** yes. The new `contract-available-providers` entry has `producedBy: "image-routing-discovery"` (singular string) and `consumedBy: ["image-cloud-generate", "image-keynote-rendering", "deck-conductor"]` (array). All four IDs resolve to existing services. Directionality matches the runtime flow: discovery service writes the manifest at the start of a run, routing/cost/conductor read it. The new contract entry is structurally identical in shape to the four pre-existing entries (`contract-strategy-map`, `contract-slide-prompts`, `contract-render-log`, `contract-brand-profile` — all have producedBy + consumedBy + fields).

- **Version bump justified:** yes (patch defensible). See methodology table above.

- **Surfaces touched but missed:**
  - **`image-routing-discovery` service mission was not updated.** The new `contract-available-providers` declares `producedBy: "image-routing-discovery"`, formalising that this service produces the manifest. Yet the service's own mission text (`"Entry point for all image generation. Discovers available providers at runtime, routes to best model per asset type and budget, returns generated image."`) was not edited to reflect that it now produces a named, model-tracked data contract whose `supported_resolutions` field is a routing input. Worth a one-line addition in a future revision: "...produces the `AvailableProviders` data contract with per-model `supported_resolutions` capability used by routing." Advisory only.
  - **Plugin version is not tracked anywhere in the model.** The implementation change shipped as `jack-tar-cloud` v1.1.1 → v1.2.0. The BSA model has no plugin-version key. Plan §Q2 surfaced this and chose (correctly, in our view) to keep plugin versions in `marketplace.json` / `plugin.json` rather than introduce a new BSA schema concept just for this change. Not a miss; a deliberate scope boundary. Recorded here for traceability.

---

## Documentation soundness

- **Arch docs match canonical model:** yes for body content. The `image-services.md` provider table is consistent with the per-system-actor descriptions in the canonical model (1K-only OpenAI; full 1K/2K/4K Google; 2K-ceiling FAL). The `data-contracts.md` `AvailableProviders` Key Fields table mirrors the new `contract-available-providers.fields[]` array exactly (4 fields: `providers`, `providers[].models`, `providers[].models[].supported_resolutions`, `providers[].models[].pricing_backend`). The Lifecycle item 1 was correctly updated from the old `imagegen-bridge` producer reference to `provider_discovery.discover_providers()` — this is genuinely a correction, not a refactor.

- **CLAUDE.md BSA line matches:** yes. Line 66 reads `v1.4.1, includes ... + cloud resolution control (1K/2K/4K)`, matching `modelMetadata.version`. The 2026-05-03 status block (CLAUDE.md L37–L51) was already authored with the correct version reference and feature description, so no further edit was needed there.

- **Stale cross-references:**
  - `docs/architecture/image-services.md` line 3: `> Generated from canonical model: jack-tar-deckhand.json v1.4.0` — stale. Body of this doc was edited as part of the v1.4.1 update.
  - `docs/architecture/data-contracts.md` line 3: same stale stamp. Body was edited as part of v1.4.1.
  - `docs/architecture/architecture-overview.md`, `ai-persona-summaries.md`, `content-services.md`, `interaction-matrix.md`, `service-catalogue.md` line 3: all carry `v1.4.0` stamp. Bodies were not edited so the stamp arguably reflects "the version of the model these were last regenerated against" — defensible to leave, but if the project policy is "the stamp tracks the current model version", all seven need bumping.

---

## Forward-consistency findings

- **Spec mentions a "render funnel" with `cloud_2k`/`cloud_4k` stages and "image-router upgrade tiers" deferred to issue #60.** These are explicit deferrals (CLAUDE.md L41–L43). The canonical model correctly does not pre-emptively add tier-name fields to `contract-available-providers` for unbuilt routing stages — the change stays within #59's actual scope. Good discipline.

- **Spec calls out "cross-tier refinement loop integration" deferred to #60.** Same — not in scope here, correctly omitted from the model.

- **Recraft V4 raster as first-class provider deferred to #61.** Not in scope here. Note that `sys-fal` description still mentions Recraft V4 (SVG icons) as it did before — no regression, no premature addition.

- **Dogfood report flagged the legacy-`src/` import collision** (CLAUDE.md L45). This is a packaging/HOW concern, not a WHAT concern. We agree with the plan that it does not belong in the canonical model. The dogfood report itself is the right home; if the issue persists or affects more than one developer, an ADR or a CONTRIBUTING note would be the next step. Not a blocker for this BSA update.

---

## Critical issues (must fix before merge)
- **None.**

---

## Advisory issues (worth addressing but not blocking)

1. **Bump the provenance stamp on the two edited arch docs.** `docs/architecture/image-services.md` and `docs/architecture/data-contracts.md` line 3 should read `v1.4.1`, not `v1.4.0`. These docs now contain v1.4.1-only content; leaving the stamp at v1.4.0 makes the docs internally inconsistent. (The five other arch docs are unedited and the stamp question there is a project-policy call.)

2. **Update `image-routing-discovery` service mission to mention the AvailableProviders contract it now produces.** The new `contract-available-providers` entry names this service as the producer; the service's own mission should reciprocate. One sentence is enough.

3. **Optional cross-reference in CLAUDE.md L40.** Plan §"CLAUDE.md edit 2" suggested tweaking `Per-model capability surfaced via provider_discovery.discover_providers().` to `Per-model capability surfaced via the AvailableProviders data contract (provider_discovery.discover_providers()).` since Edit 10 shipped. The draft node opted to update `data-contracts.md` instead, which is a stronger cross-reference. Either is acceptable; flagging only because the plan called it out.

4. **Consider adopting an ADR convention in a separate, future PR.** Plan §Q3 chose to defer. The cloud-resolution-control change is well-documented in its design spec, the plan, this review, and the dogfood report — the absence of an ADR did not impair traceability. But several recent decisions (resolution control, pptx_native engine, image reviewer, rendering strategy expansion) would benefit from a short ADR series. Not for this PR; flagging for the project backlog.

---

## Strengths (keep these)

- **Plan-to-draft fidelity is exact.** Every one of the 10 canonical-model edits and 2 doc updates the plan specified was applied; no scope creep, no silent additions. The draft node's per-edit log explicitly notes "No edits made beyond what the plan listed" and the diff confirms it.

- **Schema consistency on the new dataContract.** `contract-available-providers` adopts the established 4-key shape (`id`, `name`, `description`, `producedBy`, `consumedBy`, `fields`) used by all four pre-existing data contracts in this model. No schema drift.

- **Symmetry across the three cloud interactions.** All three `int-cloud-skills-to-{openai,google,fal}` descriptions were updated in parallel with the resolution-dispatch story, even though only OpenAI and FAL strictly needed the precedence rule called out. Symmetry serves the reader of `interactions[]`.

- **Lifecycle correction caught en passant.** The producer of `AvailableProviders` was previously documented as `imagegen-bridge` in `data-contracts.md` Lifecycle item 1; it has been the `provider_discovery.discover_providers()` function for some time. The draft fixed this stale reference as part of the same edit window. Genuine documentation hygiene.

- **Dual pricing surfaced at the right boundary.** Imagen's Vertex-vs-Developer-API split is a runtime concern that originates at the `sys-google-vertex` system-actor boundary; that's where the canonical-model description records it, and `image-services.md` echoes it for human readers. Information lives where it belongs.

- **Open questions resolved with the rationale recorded.** Plan §Q1–Q4 each had a recommended default and the draft followed them; the draft's "Concerns / unresolved" section restates the resolutions so a future reader doesn't have to dig through the plan.

- **Self-test answers all verifiable from the model + docs alone.** Validate findings independently confirmed the five self-test questions from the plan can be answered by reading the canonical model and the arch docs without consulting source code or external context.
