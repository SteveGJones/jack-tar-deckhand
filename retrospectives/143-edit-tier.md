# Retrospective: Feature #143 — edit tier (targeted $0 local edits)

**Branch**: `feat/edit-tier-loop` (PR D — final phase, consumes PR C `feat/edit-tier-mlx` already on `main`)
**Date**: 2026-07-24

_To be completed at feature close._

## Changes Made

- `plugins/jack-tar-deckhand/src/edit_dispatch.py` (new) — `detect_mlx_edit_backend`, `edit_channel_unavailable_reason` (F-06), `edit_channel_available` (D8), `classify_edit_locality` (D9 hard text carve-out), `build_edit_args` (F-08 seed always resolved), `record_edit` (D5 `edit_chain` provenance)
- `plugins/jack-tar-deckhand/src/iterate_slide_dispatch.py` — `available_channels_for_creative_vision` appends `"edit"`; new `edit_action` helper (flat image-manifest persistence, chains `edit_chain`)
- `plugins/jack-tar-deckhand/src/creative_vision/manifest.py` — `iterate_slide_hooks.can_edit` hook init + flip; `append_attempt`'s `mlx_edit` tier-position guard (F-10)
- `plugins/jack-tar-deckhand/src/creative_vision/cascade.py` — `"mlx_edit": (None, None, None)` in `TIER_TO_PROVIDER_MODEL_RESOLUTION`
- `plugins/jack-tar-deckhand/src/creative_vision/orchestrator.py` — `decide_next_action` gains optional `locality`/`can_edit` kwargs, returns `NextAction(kind="edit")` on `refine_at_tier` + local + can_edit
- `plugins/jack-tar-deckhand/src/schemas/creative_vision_manifest.schema.json` — optional `base_attempt_index`/`base_image_hash` (attempt), `can_edit` (iterate_slide_hooks)
- `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md` — Step 4.9 (Local edit)
- `plugins/jack-tar-deckhand/skills/iterate-slide/SKILL.md` — "Edit channel" section + creative_vision Channel 4
- `plugins/jack-tar-deckhand/tests/test_edit_dispatch.py` (new, 44 tests) + extensions to `test_creative_vision_{cascade,manifest,orchestrator,schemas,ga_flow,iterate_slide}.py`, `test_iterate_slide_dispatch.py`
- `plugins/integration_tests/test_imagegen_bridge_skill.py` — Step 4.9 drift pins
- `plugins/jack-tar-deckhand/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` — deckhand `1.12.0 → 1.13.0`

## What went well

- The smoke plan (executed in PR C before any PR D code) meant every design
  decision (D8/D9/D10/D11/F-03/F-08) was already FIRM going into
  implementation — zero contingent branches to hedge against.
- The `should_fire_operator_gate` F12 predicate needed literally no code
  change — `strategy == "creative_vision"` already fires unconditionally;
  only a `TIER_COSTS["mlx_edit"]` entry was needed so the lookup doesn't
  `KeyError` when an edit tier name is passed through.
- The F4 annotation-refresh guard needed no edit-specific code at all — its
  predicate only reads the strategy map's `annotation_mode`, so it already
  covers an edit-triggered replacement for free.

## What to watch

- The design's F-09 illustrative `render` shape (`prompt`/`image_path`) and
  the pre-existing schema's required `render` shape (`model`/`resolution`/
  `cost_usd`/`output_path`) disagree — no prior test had ever schema-validated
  a populated `attempts` array to surface this. Resolved by populating both
  key sets (additive, since the schema has no `additionalProperties: false`)
  rather than relitigating either shape. Worth a follow-up to decide which
  shape is canonical if a future PR tightens the schema.
- `classify_edit_locality`'s cue lists are hand-authored heuristics, not
  Critic-emitted (design OQ3, deferred). Real dogfood feedback strings will
  be the test of whether the local/global/text_excluded split holds up.
