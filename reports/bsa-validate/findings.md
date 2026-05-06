# BSA Validate Findings

Validated commit: `8a60194` — `bsa(draft): apply canonical model + arch doc updates per plan`

---

## JSON parse
PASS — `python3 -c "import json; json.load(...)"` exits 0. Valid JSON.

Counts after draft commit:
- services: 33
- aiPersonas: 6
- interactions: 60
- dataContracts: 5 (AvailableProviders added as new entry)
- dependencyRegister: 0 (key absent from model; pre-existing; not introduced by draft)

---

## Schema check
PASS (with pre-existing schema convention notes — neither blocks review)

The canonical-model-validator skill is present at `.claude/skills/canonical-model-validator/SKILL.md` but contains only documentation, no executable Python entry point. A manual structural check was run instead.

**Manual structural check results:**

1. **`bsaVersion` top-level key absent** — WARN (pre-existing, not a draft defect). The validator script expected `bsaVersion` at the document root. This model stores version in `modelMetadata.version` (= `"1.4.1"`), which is the established schema convention for this project. The field is present and correct; only the key path differs from the generic check's assumption.

2. **AI personas missing `name` field** — WARN (pre-existing, not a draft defect). The validator expected `name` on each persona. This model's schema uses `id` + `description` for persona identity (e.g., `id: "persona-deck-conductor"`). All 6 personas have valid `id` and `description`. No names were stripped by the draft; this field was never in the schema.

3. **All interaction endpoints resolve** — PASS. All `source`/`target` values in the 60 interactions resolve to known service IDs or `persona:` prefixed identifiers. No dangling references.

4. **No duplicate dependency IDs** — PASS (trivially; register is empty).

5. **All 33 services have `id` and non-empty fields** — PASS.

6. **New `contract-available-providers` entry** — PASS. Correctly added under `dataContracts` with `id`, `name`, and field definitions. No schema violation.

---

## Cross-reference (CLAUDE.md ↔ canonical model)
PASS — versions match: yes, both = v1.4.1

- `CLAUDE.md` line 66: `**BSA Architecture:** v1.4.1, includes ... + cloud resolution control (1K/2K/4K)`
- `modelMetadata.version` in `.bsa/models/jack-tar-deckhand.json`: `"1.4.1"`
- `modelMetadata.lastModifiedDate`: `"2026-05-03"` (matches today)

---

## Self-test answers

**Q1** — "What resolutions does Cloud Image Generation support after #59, broken down per provider/model?"
- VERIFIED. `docs/architecture/image-services.md` lines 107–114: 7-row provider table with Resolutions column present. Covers OpenAI (1K), Imagen Fast (1K), Imagen Standard/Ultra (1K, 2K), Nano Banana Flash (0.5K, 1K, 2K, 4K), Nano Banana Pro (1K, 2K, 4K), FLUX.2 Pro (1K, 2K), Ideogram (1K). Also confirmed in `sys-google-vertex`, `sys-openai`, `sys-fal` system actor descriptions in the canonical model.

**Q2** — "Which exception does the cloud image service raise when a caller asks for an unsupported resolution, and what information does it carry?"
- VERIFIED. `image-cloud-generate` mission: "Unsupported provider/model/resolution combinations raise ProviderResolutionUnsupportedError carrying the closest supported tier so callers can retry." `image-services.md` Resolution Selection subsection (line 119): exception carries `supported_resolutions` metadata.

**Q3** — "How does Imagen pricing differ between Vertex AI and the Gemini Developer API, and how does the system know which to bill?"
- VERIFIED. `sys-google-vertex` description: "Imagen pricing is dual-tier — flat per-image on Vertex (GOOGLE_APPLICATION_CREDENTIALS) vs token-based on Gemini Developer API (GOOGLE_API_KEY); jack-tar-cloud auto-detects via env var." Same in `image-services.md` line 119.

**Q4** — "What is the BSA architecture version after this update, and what new capability does it document?"
- VERIFIED. `CLAUDE.md` line 66: `v1.4.1, includes … + cloud resolution control (1K/2K/4K)`. `modelMetadata.version`: `"1.4.1"`.

**Q5** — "If a caller passes both `resolution="1K"` and an explicit provider-specific `size=` or `image_size=`, which wins?"
- VERIFIED. `int-cloud-skills-to-fal` description: "Explicit caller-supplied image_size= overrides resolution-derived dict." `int-cloud-skills-to-openai` description: documents 1K-only with ProviderResolutionUnsupportedError pre-call. `image-services.md` Resolution Selection subsection: "Explicit provider-specific kwargs … take precedence over the `resolution=`-derived value with a logger warning."

---

## Diff scope
PASS — the draft commit (8a60194) touched exactly the expected files:

| File | Expected? |
|------|-----------|
| `.bsa/models/jack-tar-deckhand.json` | YES — canonical model edits 1–10 |
| `CLAUDE.md` | YES — version line bump |
| `docs/architecture/data-contracts.md` | YES — doc update 2 |
| `docs/architecture/image-services.md` | YES — doc update 1 |
| `reports/bsa-draft/changes.md` | YES — draft node output artifact |

**Uncommitted changes in working tree** (pre-existing, not introduced by draft):
- `M .archon/workflows/bsa-feature-update.yaml` — present in git status at session start, unrelated to BSA model edits; out-of-scope but NOT part of the draft commit
- `?? .archon/logs/` — untracked workflow runtime output
- `?? .archon/workflows/.generated/` — untracked generated workflow artifacts

None of the pre-existing uncommitted changes are from the draft node. No unexpected files were committed.

---

## Critical issues
None.

The two WARN items (`bsaVersion` key naming, persona `name` field) are pre-existing schema conventions in this model, not defects introduced by the draft. They represent a mismatch between the generic validator's assumptions and this project's actual schema shape. Both were true before the draft commit and will require a separate schema-alignment task if resolution is desired.

---

## Verdict
PASS — proceed to review.

All draft changes are structurally sound, version references are consistent, all five self-test answers are independently verifiable in the cited locations, and the commit scope is exactly what the plan specified. No blocking issues found.
