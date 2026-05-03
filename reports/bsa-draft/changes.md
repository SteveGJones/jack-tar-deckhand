# BSA Draft Changes

## Files modified

| File | Lines + | Lines − | Summary |
|---|---|---|---|
| `.bsa/models/jack-tar-deckhand.json` | ~25 | ~8 | Version bump, service mission, 3 system actor descriptions, 3 interaction descriptions, new AvailableProviders data contract |
| `CLAUDE.md` | 1 | 1 | BSA Architecture version line bumped 1.4.0 → 1.4.1 with cloud resolution control note |
| `docs/architecture/image-services.md` | ~18 | ~5 | Provider table expanded with Resolutions column + new Resolution Selection subsection; test count updated 49 → ~84 |
| `docs/architecture/data-contracts.md` | ~14 | ~6 | AvailableProviders Key Fields table updated with new fields; added v1.2.0 note and updated Lifecycle producer reference |

## Per-edit log

- **Edit 1:** Bump `modelMetadata.version` 1.4.0 → 1.4.1
  - Applied: yes
  - Result: `"version": "1.4.1"` in modelMetadata
  - Concerns: none

- **Edit 2:** Bump `modelMetadata.lastModifiedDate` → 2026-05-03
  - Applied: yes
  - Result: `"lastModifiedDate": "2026-05-03"` in modelMetadata
  - Concerns: none

- **Edit 3:** Extend `image-cloud-generate` service mission
  - Applied: yes
  - Result: Mission now includes Nano Banana Pro/Flash, resolution ladder, and `ProviderResolutionUnsupportedError` semantics
  - Concerns: none

- **Edit 4:** Refresh `sys-google-vertex` description
  - Applied: yes
  - Result: Description covers Imagen 4 (Fast/Standard/Ultra) + Nano Banana Pro/Flash with per-model resolution ladders and dual-pricing detection
  - Concerns: none

- **Edit 5:** Refresh `sys-openai` description
  - Applied: yes
  - Result: Description notes 1K-only resolution limit and that 2K/4K raise `ProviderResolutionUnsupportedError`
  - Concerns: none

- **Edit 6:** Refresh `sys-fal` description
  - Applied: yes
  - Result: Description notes FLUX.2 Pro 2K ceiling and 4K error
  - Concerns: none

- **Edit 7:** Annotate `int-cloud-skills-to-google` interaction description
  - Applied: yes
  - Result: Description covers both Vertex AI predict and Gemini generateContent endpoints, Nano Banana models, and resolution normalisation
  - Concerns: none

- **Edit 8:** Annotate `int-cloud-skills-to-fal` interaction description
  - Applied: yes
  - Result: Description documents FAL resolution→image_size mapping and explicit-kwarg override precedence
  - Concerns: none

- **Edit 9:** Annotate `int-cloud-skills-to-openai` interaction description
  - Applied: yes
  - Result: Description documents 1K-only constraint and pre-call error raise
  - Concerns: none

- **Edit 10:** Add `contract-available-providers` to `dataContracts[]`
  - Applied: yes (plan flagged as recommended, included)
  - Result: New entry with 4 fields covering providers keyed map, models map, `supported_resolutions`, and `pricing_backend`
  - Concerns: Plan noted this crosses into #60 territory; the contract is additive (no #60 work disrupted). Open question Q1 resolved in favour of including now.

- **Doc update 1:** `image-services.md` provider table + Resolution Selection subsection + test count
  - Applied: yes
  - Result: Table now has 7 rows with Resolutions column; new "#### Resolution Selection" subsection covers `resolution=` kwarg, default, error semantics, override precedence, and dual-pricing detection
  - Concerns: none

- **Doc update 2:** `data-contracts.md` AvailableProviders section
  - Applied: yes (Edit 10 was included, so full update applied rather than deferred note)
  - Result: Key Fields table updated with new schema fields; v1.2.0 note added cross-referencing canonical model entry and #60
  - Concerns: none

- **Doc update 3:** `architecture-overview.md` — no changes required per plan
  - Applied: n/a

- **Doc update 4:** New ADR — deferred per plan recommendation (no `decisions/` folder exists)
  - Applied: n/a

- **CLAUDE.md edit 1:** BSA Architecture version line
  - Applied: yes
  - Result: `v1.4.1, includes keynote pipeline + rendering strategy expansion + image reviewer + SmartArt intelligent graphics + cloud resolution control (1K/2K/4K)`
  - Concerns: none

- **CLAUDE.md edit 2:** 2026-05-03 status block already present — no edit needed per plan
  - Applied: n/a; plan called for optional cross-reference tweak if Edit 10 shipped. Updated `data-contracts.md` instead — the canonical model now defines the contract, which is a stronger cross-reference than a prose tweak in CLAUDE.md.

## JSON validity

After all edits: `python3 -c "import json; json.load(open('.bsa/models/jack-tar-deckhand.json'))"` exits 0: **yes**

## Self-test answers

1. **"What resolutions does Cloud Image Generation support after #59, broken down per provider/model?"**
   - A: `docs/architecture/image-services.md` — new 7-row table with Resolutions column under "Cloud Image Generation (`cloud-generate-image`)"; also in `sys-google-vertex`, `sys-openai`, `sys-fal` descriptions in canonical model

2. **"Which exception does the cloud image service raise when a caller asks for an unsupported resolution, and what information does it carry?"**
   - A: `image-cloud-generate` mission (canonical model): "raise ProviderResolutionUnsupportedError carrying the closest supported tier"; `docs/architecture/image-services.md` Resolution Selection subsection: "exception carries `supported_resolutions` metadata so the caller can retry at the nearest supported tier"

3. **"How does Imagen pricing differ between Vertex AI and the Gemini Developer API, and how does the system know which to bill?"**
   - A: `sys-google-vertex` description (canonical model): "flat per-image on Vertex (GOOGLE_APPLICATION_CREDENTIALS) vs token-based on Gemini Developer API (GOOGLE_API_KEY); jack-tar-cloud auto-detects via env var"; same in `image-services.md` Resolution Selection subsection

4. **"What is the BSA architecture version after this update, and what new capability does it document?"**
   - A: `CLAUDE.md` line 66: `v1.4.1, includes … + cloud resolution control (1K/2K/4K)`; `modelMetadata.version` in canonical model: `"1.4.1"`

5. **"If a caller passes both `resolution="1K"` and an explicit provider-specific `size=` or `image_size=`, which wins?"**
   - A: `int-cloud-skills-to-fal` description: "Explicit caller-supplied image_size= overrides resolution-derived dict"; `int-cloud-skills-to-openai` description: same precedence implied by "Resolution maps to native size kwarg"; `image-services.md` Resolution Selection: "Explicit provider-specific kwargs … take precedence over the `resolution=`-derived value with a logger warning"

## Concerns / unresolved

- **Open question Q1 (Edit 10 timing):** Included. The contract is small and additive; #60 can extend it. No concern.
- **Open question Q2 (plugin version tracking):** Not added to BSA model — plan's recommended default was to keep that in `marketplace.json`/`plugin.json`. No action taken.
- **Open question Q3 (ADR adoption):** Deferred per plan recommendation.
- **Open question Q4 (dataFlows on interactions):** Not added — plan's recommended default was to skip for consistency.
- **No edits made beyond what the plan listed.** All changes are a direct application of the 10 canonical-model edits and the 2 arch-doc updates specified in the plan.
