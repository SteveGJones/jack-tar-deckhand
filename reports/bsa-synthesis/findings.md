# BSA Update Synthesis Report: Cloud Resolution Control (#59 / EPIC #58)

## Summary

BSA model v1.4.0 → v1.4.1 was applied across four commits (plan → draft → validate → review). The draft touched the canonical model (10 edits), CLAUDE.md (1 line), and two architecture docs, accurately reflecting the cloud resolution control feature landed in `jack-tar-cloud` v1.2.0. Validate returned PASS with no critical issues; two pre-existing schema convention WARNs were noted as not-draft-defects. Review returned PASS_WITH_REVISIONS: no critical issues, two advisory items (stale provenance stamps on two edited arch docs; `image-routing-discovery` service mission not updated to mention its new producer role). Recommended verdict: **GO**.

---

## Files changed

| File | Lines + | Lines − | Summary |
|---|---|---|---|
| `.bsa/models/jack-tar-deckhand.json` | 22 | 9 | bsaVersion 1.4.0→1.4.1, lastModifiedDate, `image-cloud-generate` mission, `sys-google-vertex` + `sys-openai` + `sys-fal` descriptions, 3 interaction descriptions, new `contract-available-providers` dataContract |
| `CLAUDE.md` | 1 | 1 | BSA Architecture status line bumped to v1.4.1 |
| `docs/architecture/image-services.md` | 15 | 7 | Provider table expanded with Resolutions column; Resolution Selection subsection added |
| `docs/architecture/data-contracts.md` | 8 | 5 | AvailableProviders Key Fields table updated; Lifecycle producer reference corrected (imagegen-bridge → provider_discovery) |
| `reports/bsa-plan/plan.md` | 202 | 0 | Plan artifact (commit 298fad4) |
| `reports/bsa-draft/changes.md` | 115 | 0 | Draft node log (commit 8a60194) |
| `reports/bsa-validate/findings.md` | 98 | 0 | Validate node output (commit e37600f) |
| `reports/bsa-review/findings.md` | 97 | 0 | Review node output (commit 400b638) |

---

## Architectural deltas

| Surface | What changed | Commit | Code reflection |
|---|---|---|---|
| `modelMetadata.version` | `"1.4.0"` → `"1.4.1"` | 8a60194 | Patch bump for additive interface widening; no new services/personas/interactions |
| `modelMetadata.lastModifiedDate` | `"2026-04-03"` → `"2026-05-03"` | 8a60194 | Reflects cloud resolution control merge date |
| `image-cloud-generate` mission | Added Nano Banana Pro/Flash, 1K/2K/4K ladder, `ProviderResolutionUnsupportedError` semantics | 8a60194 | `src/generate_cloud_image.py` — `resolution=` param + exception class |
| `sys-openai` description | Added 1K-only resolution ceiling documentation | 8a60194 | OpenAI `size` field accepts only `"1024x1024"` and similar fixed values |
| `sys-google-vertex` description | Added Nano Banana Flash/Pro ladder (0.5K–4K), Imagen Fast/Standard/Ultra tiers, dual-pricing detection via env-var sniff | 8a60194 | `estimate_google_cost()` in `plugins/jack-tar-cloud/src/` |
| `sys-fal` description | Added FLUX.2 Pro 2K ceiling | 8a60194 | FAL `image_size` mapped to `"1024x1024"` / `"2048x2048"` |
| `int-cloud-skills-to-openai` description | Documents 1K-only + `ProviderResolutionUnsupportedError` raised pre-call | 8a60194 | Interaction dispatch in cloud skills → OpenAI path |
| `int-cloud-skills-to-google` description | Documents 1K/2K/4K support, explicit-kwarg precedence rule | 8a60194 | `imageConfig.imageSize` kwarg in Google path |
| `int-cloud-skills-to-fal` description | Documents explicit `image_size=` override takes precedence over `resolution=`-derived value | 8a60194 | FAL path kwarg precedence logic |
| `dataContracts[contract-available-providers]` | New entry: `AvailableProviders` — producedBy `image-routing-discovery`, consumed by `image-cloud-generate` / `image-keynote-rendering` / `deck-conductor`; fields: `providers`, `providers[].models`, `providers[].models[].supported_resolutions`, `providers[].models[].pricing_backend` | 8a60194 | `provider_discovery.discover_providers()` return type; previously implicit contract now formally tracked |

---

## Validate node verdict

**PASS — proceed to review.**

All draft changes structurally sound, version references consistent, all five self-test answers independently verifiable, commit scope exactly as planned. Two pre-existing WARNs:
- `bsaVersion` key path mismatch (validator expects top-level; model stores in `modelMetadata.version`) — not a draft defect
- Persona `name` field absent (validator expects `name`; model uses `id` + `description`) — not a draft defect

---

## Review node verdict

**PASS_WITH_REVISIONS** — change is correct, methodology-aligned, and ready to ship. No critical issues. Two advisory issues are not blocking.

---

## Methodology compliance

| Doctrine | Status | Evidence |
|---|---|---|
| Single source of truth | pass (advisory: stale provenance stamps on 2 arch docs) | Canonical model is authoritative; CLAUDE.md and arch doc bodies match. `image-services.md` and `data-contracts.md` line 3 still read `v1.4.0` while bodies reflect v1.4.1 content. |
| Version semantics | pass | 1.4.0 → 1.4.1 patch. Additive contract widening; no new services, personas, interactions, or actors. Defensible as patch per project precedent. |
| Dependency register | n/a | No `dependencyRegister` key in model (pre-existing). No new external dependencies introduced. |
| WHAT/HOW separation | pass (consistent with existing convention) | Implementation detail in mission/descriptions (env-var names, exception class name, native kwargs) matches depth of pre-existing entries. No new convention introduced. |
| Cross-Domain SOP | n/a | Single-domain project; no SOP involved. |

---

## Open questions for speaker

*(copied verbatim from review `reports/bsa-review/findings.md`)*

> **Plugin version is not tracked anywhere in the model.** The implementation change shipped as `jack-tar-cloud` v1.1.1 → v1.2.0. The BSA model has no plugin-version key. Plan §Q2 surfaced this and chose (correctly, in our view) to keep plugin versions in `marketplace.json` / `plugin.json` rather than introduce a new BSA schema concept just for this change. Not a miss; a deliberate scope boundary. Recorded here for traceability.

> **Consider adopting an ADR convention in a separate, future PR.** Plan §Q3 chose to defer. Several recent decisions (resolution control, pptx_native engine, image reviewer, rendering strategy expansion) would benefit from a short ADR series. Not for this PR; flagging for the project backlog.

---

## Advisory issues (not blocking; addressable in follow-on)

1. **Bump provenance stamp on two edited arch docs.** `docs/architecture/image-services.md` and `docs/architecture/data-contracts.md` line 3 read `> Generated from canonical model: jack-tar-deckhand.json v1.4.0`. Bodies now describe v1.4.1 content — internal inconsistency. One-line fix per file; can ride with the next BSA update or as a standalone tidy commit.

2. **Update `image-routing-discovery` service mission.** The new `contract-available-providers` entry names this service as producer; the service's mission text was not updated to mention it. Suggested addition: _"...produces the `AvailableProviders` data contract with per-model `supported_resolutions` capability used by routing."_

3. **CLAUDE.md §Cloud Resolution Control cross-ref (optional).** Plan §Q4 noted that updating `data-contracts.md` is a stronger cross-reference than a CLAUDE.md inline edit; both are acceptable. No action required.

---

## Critical issues (must fix before merge)

**None.**

---

## Decision aid

```
SPEAKER REVIEW VERDICT NEEDED:
  GO     — accept BSA update, ship with the feature PR
  REVISE — request specific changes (cite review findings.md sections)
  STOP   — fundamental issue, drop the BSA commits and re-plan
```

**Recommended verdict: GO**
The BSA update is accurate, complete within scope, and methodology-aligned. No critical issues were found at any node. The two advisory items (stale provenance stamps, missing producer-side mission update) are minor cosmetic inconsistencies that can be addressed in a follow-on tidy commit without blocking the feature PR.

---

## Branch / merge info

- Branch: `main`
- BSA commits ahead of feature-PR head before this run: 0
- BSA commits added by this run: 4 (plan → draft → validate → review)
- Report commit (this file): 1
- Suggested merge: BSA commits ride along with the feature PR (single PR for code + BSA in lockstep, per project convention `gh pr merge <n> --merge`)
- Pre-existing uncommitted changes in working tree (`bsa-feature-update.yaml`) are out-of-scope and should not be included in the feature PR
