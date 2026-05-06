# BSA Update Plan: Cloud Resolution Control (#59 / EPIC #58)

## Architectural impact summary

Issue #59 is an **interface-level extension** of an existing L2 service (`image-cloud-generate`) — no new services, no new AI personas, no new system actors, no new interactions. It adds a unified `resolution` parameter (`"512" | "1K" | "2K" | "4K"`) to `generate_cloud_image()`, plumbs it through to each provider's native field (OpenAI `size`, Google `image_size`/`imageConfig.imageSize`, FAL `image_size`), and surfaces per-model capability via `provider_discovery.discover_providers().supported_resolutions`. A new `ProviderResolutionUnsupportedError` exception lets callers retry at a closer tier. Imagen 4 cost estimation gains backend detection (Vertex flat vs Gemini Developer API token-based). The change is additive — every existing call site keeps its current behaviour because `resolution="1K"` is the default. Architecturally this is a contract widening on one service's public API, with corresponding capability metadata on its three downstream system actors. Minor BSA version bump (1.4.0 → 1.4.1).

## Canonical-model edits

> Note: the canonical model schema for this project does NOT have `interactions[i].contract`, `dependencyRegister`, or `crossDomainSopRegister` fields (verified by inspection of `.bsa/models/jack-tar-deckhand.json`). The structural surface available is `services[].mission`, `systemActors[].description`, `interactions[].description`/`dataFlows`, and `dataContracts[]`. All edits below conform to that surface.

### Edit 1 — bump BSA model version

- **File:** `.bsa/models/jack-tar-deckhand.json`
- **JSON path:** `modelMetadata.version`
- **Operation:** modify `"1.4.0"` → `"1.4.1"`
- **Rationale:** Additive interface change on an existing service; no structural reshape, no new entries. Patch-style minor bump within the 1.4.x line.

### Edit 2 — bump lastModifiedDate

- **File:** `.bsa/models/jack-tar-deckhand.json`
- **JSON path:** `modelMetadata.lastModifiedDate`
- **Operation:** modify `"2026-04-03"` → `"2026-05-03"`
- **Rationale:** Reflects the resolution-control merge date (matches dogfood report timestamp).

### Edit 3 — extend `image-cloud-generate` service mission

- **File:** `.bsa/models/jack-tar-deckhand.json`
- **JSON path:** `services[]` entry where `id == "image-cloud-generate"` → `.mission`
- **Operation:** modify the mission string from
  > `"Generate images via cloud APIs (OpenAI GPT Image 1.5, Google Imagen 4, FLUX.2 Pro) with provider routing based on availability and asset type."`
  to
  > `"Generate images via cloud APIs (OpenAI GPT Image 1.5, Google Imagen 4, Google Nano Banana Pro/Flash, FLUX.2 Pro) at requested resolution (1K / 2K / 4K) with provider routing based on availability, asset type, and per-model resolution support. Unsupported provider/model/resolution combinations raise ProviderResolutionUnsupportedError carrying the closest supported tier so callers can retry."`
- **Rationale:** The service contract has widened — it now exposes a `resolution=` parameter and a typed exception. Mission must reflect that this service knows about Nano Banana Pro/Flash (which weren't in the original mission text), and that resolution selection is now a first-class concern. Also corrects the model list to include Nano Banana Pro/Flash, which are the only providers that reach 4K.

### Edit 4 — refresh `sys-google-vertex` description

- **File:** `.bsa/models/jack-tar-deckhand.json`
- **JSON path:** `systemActors[]` entry where `id == "sys-google-vertex"` → `.description`
- **Operation:** modify from
  > `"Imagen 4 and Gemini Flash — cost-effective image generation. Imagen 4 Fast at $0.02/image is the budget workhorse for backgrounds and textures. Requires GOOGLE_CLOUD_PROJECT and service account."`
  to
  > `"Imagen 4 (Fast/Standard/Ultra) and Gemini 3 Image (Nano Banana Pro/Flash) — cost-effective image generation across the 1K/2K/4K ladder. Imagen 4 Fast at $0.02/image (1K only) is the budget workhorse for backgrounds; Nano Banana Flash supports 0.5K/1K/2K/4K ($0.045-$0.151); Nano Banana Pro supports 1K/2K/4K ($0.134-$0.24) for hero renders. Imagen pricing is dual-tier — flat per-image on Vertex (GOOGLE_APPLICATION_CREDENTIALS) vs token-based on Gemini Developer API (GOOGLE_API_KEY); jack-tar-cloud auto-detects via env var. Requires GOOGLE_CLOUD_PROJECT + service account, OR GOOGLE_API_KEY for the Developer API path."`
- **Rationale:** This system actor now carries materially more capability — Nano Banana models, full 1K/2K/4K ladder on Flash, dual-pricing detection. The `estimate_google_cost()` env-var sniff is an architecturally significant detail because it changes how cost is computed at runtime; documenting it on the system actor (the boundary where the divergence originates) is the right home.

### Edit 5 — refresh `sys-openai` description

- **File:** `.bsa/models/jack-tar-deckhand.json`
- **JSON path:** `systemActors[]` entry where `id == "sys-openai"` → `.description`
- **Operation:** modify from
  > `"GPT Image 1.5 — highest quality general-purpose image generation. Best text rendering, strong prompt adherence. $0.009-$0.133/image depending on quality tier. Requires OPENAI_API_KEY."`
  to
  > `"GPT Image 1.5 — highest quality general-purpose image generation. Best text rendering, strong prompt adherence. $0.009-$0.133/image depending on quality tier. Resolution: 1K only (1024×1024 / 1536×1024 / 1024×1536); 2K/4K requests raise ProviderResolutionUnsupportedError. Requires OPENAI_API_KEY."`
- **Rationale:** Records that OpenAI is the resolution ceiling at 1K; consumers of the model can see that 4K traffic must route to Google.

### Edit 6 — refresh `sys-fal` description

- **File:** `.bsa/models/jack-tar-deckhand.json`
- **JSON path:** `systemActors[]` entry where `id == "sys-fal"` → `.description`
- **Operation:** modify from
  > `"Unified access to 600+ models including FLUX.2 Pro (photorealism), Recraft V4 (SVG icons), and Ideogram 3.0 (typography). Single API key. Recommended aggregation layer. Requires FAL_KEY."`
  to
  > `"Unified access to 600+ models including FLUX.2 Pro (photorealism), Recraft V4 (SVG icons), and Ideogram 3.0 (typography). FLUX.2 Pro supports 1K/2K (caps at 2048²); 4K requests raise ProviderResolutionUnsupportedError. Single API key — recommended aggregation layer. Requires FAL_KEY."`
- **Rationale:** Records FLUX.2 Pro's 2K ceiling so the routing layer (and humans reading the model) know that 4K cannot be served via FAL.

### Edit 7 — annotate `int-cloud-skills-to-google` interaction

- **File:** `.bsa/models/jack-tar-deckhand.json`
- **JSON path:** `interactions[]` entry where `id == "int-cloud-skills-to-google"` → `.description`
- **Operation:** modify from
  > `"Cloud skills call Google Vertex AI for Imagen 4 generation"`
  to
  > `"Cloud skills call Google for image generation. Imagen 4 (1K/2K) via Vertex AI predict endpoint or Gemini Developer API; Nano Banana Pro/Flash (1K/2K/4K) via Gemini generateContent endpoint with imageConfig.imageSize. Resolution kwarg is normalised to uppercase-K before dispatch."`
- **Rationale:** The interaction's surface now spans two distinct Google endpoints (Vertex predict and Gemini generateContent) and three model families with different resolution ladders. Updating the description prevents readers from assuming this interaction is Imagen-only.

### Edit 8 — annotate `int-cloud-skills-to-fal` interaction

- **File:** `.bsa/models/jack-tar-deckhand.json`
- **JSON path:** `interactions[]` entry where `id == "int-cloud-skills-to-fal"` → `.description`
- **Operation:** modify from
  > `"Cloud skills call FAL.ai for FLUX.2 and Ideogram generation"`
  to
  > `"Cloud skills call FAL.ai for FLUX.2 and Ideogram generation. Resolution maps to native image_size kwarg (preset for 1K, explicit width/height dict for 2K). Explicit caller-supplied image_size= overrides resolution-derived dict."`
- **Rationale:** Documents the precedence rule (explicit kwarg wins over `resolution=`) at the interaction boundary where the rule applies.

### Edit 9 — annotate `int-cloud-skills-to-openai` interaction

- **File:** `.bsa/models/jack-tar-deckhand.json`
- **JSON path:** `interactions[]` entry where `id == "int-cloud-skills-to-openai"` → `.description`
- **Operation:** modify from
  > `"Cloud skills call OpenAI API for GPT Image 1.5 generation"`
  to
  > `"Cloud skills call OpenAI API for GPT Image 1.5 generation. Resolution maps to native size kwarg (1K only — 2K/4K requests raise ProviderResolutionUnsupportedError before the call is made)."`
- **Rationale:** Symmetric annotation across all three cloud system-actor interactions so anyone reading `interactions[]` for cloud generation sees a consistent resolution-and-precedence story.

### Edit 10 — formalise the `AvailableProviders` data contract (RECOMMENDED — flag as open question)

- **File:** `.bsa/models/jack-tar-deckhand.json`
- **JSON path:** `dataContracts[]` — append new entry
- **Operation:** add
  ```json
  {
    "id": "contract-available-providers",
    "name": "AvailableProviders",
    "description": "Runtime manifest of which cloud and local image-generation providers are reachable in the current environment, what models each exposes, and what resolutions each model supports. Produced by provider_discovery.discover_providers() at the start of each pipeline run; consumed by the routing layer for model selection and by the cost estimator for tier selection.",
    "producedBy": "image-routing-discovery",
    "consumedBy": ["image-cloud-generate", "image-keynote-rendering", "deck-conductor"],
    "fields": [
      { "name": "providers", "type": "object", "description": "Keyed by provider id (openai | google | fal | recraft | ollama). Each value carries availability flag, missing-credential reason, and a models map." },
      { "name": "providers[].models", "type": "object", "description": "Keyed by model id (e.g. gpt-image-1.5, gemini-3-pro-image-preview, gemini-3.1-flash-image-preview, imagen-4.0-fast-generate-001, fal-ai/flux-2-pro). Each value carries supported_resolutions, cost_table_ref, and capability flags." },
      { "name": "providers[].models[].supported_resolutions", "type": "array", "description": "List of resolution tiers the model honours: subset of [\"512\", \"1K\", \"2K\", \"4K\"]. Routing must intersect this with the requested resolution before dispatch." },
      { "name": "providers[].models[].pricing_backend", "type": "string", "description": "For Google Imagen models only: \"vertex\" (flat per-image) or \"developer\" (token-based), auto-detected from GOOGLE_APPLICATION_CREDENTIALS vs GOOGLE_API_KEY env vars." }
    ]
  }
  ```
- **Rationale:** Today the `image-services.md` doc references `AvailableProviders` as a data contract (`(in-memory / conversation)`) but it does not appear in the canonical model. The resolution-control work elevates this contract because `supported_resolutions` per model is now a routing decision input, not just a debug aid. Formalising it now closes a pre-existing gap and gives #60's router work a contract to point at. **Flag as an open question** — see §"Open questions for speaker" — because adding a new data contract is a slightly bigger change than the rest of the edits and crosses into work that #60 owns.

## Architecture-doc updates

### Doc update 1 — `docs/architecture/image-services.md`

- **Section:** "Cloud Image Generation (`cloud-generate-image`)" (around lines 103-112)
- **Change:** Add a `Resolutions` column to the provider table:
  ```markdown
  | Provider | Model | Strengths | Resolutions |
  |---|---|---|---|
  | OpenAI | GPT Image 1.5 | Highest quality, best text rendering, strong prompt adherence | 1K |
  | Google Vertex AI | Imagen 4 Fast | Cost-effective backgrounds and textures | 1K |
  | Google Vertex AI | Imagen 4 Standard / Ultra | Cost-effective, dual-pricing (Vertex flat / Dev API token) | 1K, 2K |
  | Google Gemini API | Nano Banana Flash | Full ladder, cheap-to-mid hero renders | 0.5K, 1K, 2K, 4K |
  | Google Gemini API | Nano Banana Pro | Premium hero renders, character-rich output | 1K, 2K, 4K |
  | FAL.ai | FLUX.2 Pro | Photorealism (caps at 2048²) | 1K, 2K |
  | FAL.ai | Ideogram 3.0 | Typography | 1K |
  ```
- **Add new subsection** below the table titled "Resolution Selection" with ~6 lines covering: the unified `resolution` kwarg, the default of `1K`, `ProviderResolutionUnsupportedError` semantics, the precedence rule (explicit provider-specific kwarg wins), and the Imagen dual-pricing detection.
- **Update the implementation status table** (around line 483) to bump the test count for `cloud-generate-image` from 49 to ~84 (49 existing + 35 new resolution tests across 5 new test files: `test_resolution_dispatch.py`, `test_resolution_fal.py`, `test_resolution_google.py`, `test_resolution_helpers.py`, `test_resolution_openai.py`).

### Doc update 2 — `docs/architecture/data-contracts.md`

- **Action:** If Edit 10 is approved, add a new section documenting the `AvailableProviders` contract with the field definitions matching the canonical-model entry. Cross-reference from the existing "AvailableProviders" mention in `image-services.md` line 415.
- **If Edit 10 is deferred:** add a one-paragraph note under the existing AvailableProviders mention saying "Per-model `supported_resolutions: list[str]` is now part of the discovery output (added by jack-tar-cloud v1.2.0); see #60 for the formal contract definition."

### Doc update 3 — `docs/architecture/architecture-overview.md`

- **No changes required.** No service was added, no persona was added, no L1 boundary moved. The architecture overview operates at L0/L1 granularity and a contract widening on one L2 service does not change the diagram or the headline narrative.

### Doc update 4 — NEW ADR (optional — flag in open questions)

- **Path:** `docs/architecture/decisions/ADR-2026-05-03-cloud-resolution-control.md` (if the ADR convention is adopted; the `decisions/` folder does not currently exist)
- **Content:** captures the design decisions from `docs/superpowers/specs/2026-05-02-cloud-resolution-control-design.md` §2 in ADR shape — parameter name, default value, error-type scope, backend-detection mechanism, FAL 4K rejection (no silent upscale).
- **Recommendation:** **defer** — this project does not currently use ADRs (there is no `decisions/` folder). The design spec already captures the decisions in long form. Introducing ADRs as a convention is a separate proposal worth raising on its own merits, not as a side effect of #59.

## CLAUDE.md updates

### CLAUDE.md edit 1 — bump BSA Architecture version line

- **File:** `/workspace/CLAUDE.md`
- **Line 66 (current):** `- **BSA Architecture:** v1.4.0, includes keynote pipeline + rendering strategy expansion + image reviewer + SmartArt intelligent graphics`
- **New:** `- **BSA Architecture:** v1.4.1, includes keynote pipeline + rendering strategy expansion + image reviewer + SmartArt intelligent graphics + cloud resolution control (1K/2K/4K)`
- **Rationale:** Keeps the headline architecture version in sync with the canonical model.

### CLAUDE.md edit 2 — Status entry already present

- The 2026-05-03 status block (line 54) already documents the resolution feature in detail. **No further edit needed.**
- **Verify** that the bullet `Per-model capability surfaced via provider_discovery.discover_providers().` aligns with whatever language is chosen for Edit 10's new data contract; if Edit 10 ships, consider tweaking this line to read `Per-model capability surfaced via the AvailableProviders data contract (provider_discovery.discover_providers()).` for cross-reference.

## Version bump

- **From:** 1.4.0
- **To:** 1.4.1
- **Rationale:** **Patch-level (third digit) bump within the 1.4.x line.** The change is purely additive on a single existing service contract — no new services, no new personas, no new interactions, no new system actors, no removed fields. Existing callers that omit `resolution=` see no behaviour change. Plugin version (`jack-tar-cloud` 1.1.1 → 1.2.0) is independent — that's a *plugin* minor bump because the plugin gains a public-API parameter, while the *BSA model* tracks architectural surface change which is materially smaller. Following the existing project convention (BSA v1.0 → v1.1 added Approach B; v1.3 → v1.4 added image reviewer + SmartArt as new services/personas), interface-only widenings have not previously bumped the minor version, so 1.4.1 is the correct choice.

## Open questions for speaker

### Q1 — Formalise the `AvailableProviders` data contract now or in #60?

Edit 10 proposes adding `contract-available-providers` to the canonical model. The contract is *referenced* in `image-services.md` today but not *defined* in the model. Resolution control adds `supported_resolutions` to it, which is the natural moment to formalise. **Counter-argument:** #60 owns the routing layer changes and may want to shape this contract jointly with the upgrade-decision schema. **Recommended default:** include the contract now (it's a small additive change and gives #60 something to extend). **Speaker decision needed.**

### Q2 — Does the BSA model track plugin versions anywhere?

The `jack-tar-cloud` plugin bumped 1.1.1 → 1.2.0 in this PR. The canonical model does not currently carry plugin version metadata anywhere I can find. If you want plugin versions traceable from the architecture, that's a separate schema extension — flagging because it surfaced naturally here. **Recommended default:** do not add plugin-version tracking to the BSA model; keep that in `marketplace.json` and plugin-level `plugin.json` where it lives today. **Speaker decision needed only if you want to change current convention.**

### Q3 — ADR adoption?

There is no `docs/architecture/decisions/` folder today. The cloud-resolution design spec is comprehensive on its own. Worth introducing ADRs as a convention now? **Recommended default: no** — defer until the convention is proposed on its own. **Speaker decision needed.**

### Q4 — Should the `int-cloud-skills-to-*` interactions also gain explicit `dataFlows` arrays?

Some interactions in the model carry `dataFlows: ["..."]` (see `int-conductor-to-brand-manager` line 1139). The cloud-skill-to-system-actor interactions do not. Adding `dataFlows: ["prompt", "resolution", "model_id", "provider-specific kwargs"]` would make the data passing explicit. **Recommended default:** skip — the cloud-skill-to-API interactions are commodity REST calls and the canonical model has not used `dataFlows` for them historically; introducing them only here creates inconsistency. **Speaker decision needed.**

## Test for the draft node

A reader of the updated canonical model + arch docs should be able to answer:

1. **"What resolutions does Cloud Image Generation support after #59, broken down per provider/model?"** — Should be answerable from `image-services.md` Cloud Image Generation table (after Doc update 1) and from the `sys-google-vertex` / `sys-openai` / `sys-fal` system actor descriptions (after Edits 4-6).

2. **"Which exception does the cloud image service raise when a caller asks for an unsupported resolution, and what information does it carry?"** — Should be answerable from `image-cloud-generate` service mission (after Edit 3) and from the Resolution Selection subsection (after Doc update 1). Both should mention `ProviderResolutionUnsupportedError` and the closest-supported-tier metadata.

3. **"How does Imagen pricing differ between Vertex AI and the Gemini Developer API, and how does the system know which to bill?"** — Should be answerable from the `sys-google-vertex` description (after Edit 4) — env-var sniff (`GOOGLE_APPLICATION_CREDENTIALS` vs `GOOGLE_API_KEY`).

4. **"What is the BSA architecture version after this update, and what new capability does it document?"** — Should be answerable from `CLAUDE.md` line 66 (after CLAUDE.md edit 1) and `modelMetadata.version` in the canonical model (after Edit 1) — both reading 1.4.1, both citing cloud resolution control.

5. **"If a caller passes both `resolution="1K"` and an explicit provider-specific `size=` or `image_size=`, which wins?"** — Should be answerable from the updated interaction descriptions for `int-cloud-skills-to-fal` and `int-cloud-skills-to-openai` (after Edits 8-9): explicit kwarg wins over `resolution`-derived value, with a logger warning.
