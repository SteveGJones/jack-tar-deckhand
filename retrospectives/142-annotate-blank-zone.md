# Retrospective: Feature #142 — blank-zone annotation variant (final scope item)

**Branch**: `feat/annotate-blank-zone`
**Date**: 2026-07-24

_To be completed at feature close._

## Changes Made

- `plugins/jack-tar-deckhand/src/schemas/strategy_map.schema.json` — `annotation.blank_zone` enum (`left_third | right_third | top_strip | bottom_strip | auto`)
- `plugins/jack-tar-deckhand/src/schemas/annotations.schema.json` — optional `blank_zone` audit block (requested/resolved/verified_clear/placement)
- `plugins/jack-tar-deckhand/src/annotate_figure.py` — `BLANK_ZONE_RECTS`, `place_labels_in_zone` (height + width capacity gates, all-or-nothing), `parse_blank_zone_verdict`
- `plugins/jack-tar-deckhand/src/annotation_payload.py` — `resolve_blank_zone`, `_DISPLAYED_WIDTH_IN` conservative map, `build_annotation_payload(blank_zone=, blank_zone_clear=, blank_zone_requested=)` + audit block
- `plugins/jack-tar-deckhand/src/iterate_slide_dispatch.py` — `ANNOTATION_REFRESH_INSTRUCTIONS` blank-zone re-run extension (BZ-4)
- `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md` — Step 4.8 native-flow amendments (directive injection, amended three-key anchor contract, payload pass-through)
- `plugins/jack-tar-deckhand/skills/annotate-figure/SKILL.md` — raster/standalone half (§1 directive, §2 amended contract, §3 zone-preferred overlay, "Blank-zone variant" section)
- `plugins/jack-tar-deckhand/skills/iterate-slide/SKILL.md` — Step 7.5 blank-zone note
- `plugins/jack-tar-deckhand/tests/` — `test_annotate_figure.py`, `test_annotation_payload.py`, `test_strategy_map_annotation.py`, `test_iterate_slide_dispatch.py` extensions + new `test_annotate_blank_zone_skill_docs.py` (BZ-9 drift pin)
- `docs/superpowers/dogfooding/2026-07-24-blank-zone-compliance.md` — the T6 gate ($0, P1 outcome, reviewer-wording calibration)
- `plugins/jack-tar-deckhand/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` — deckhand `1.11.0 → 1.12.0`

## What went well

- The BZ-8 control protocol did its job: matching-zone controls separated
  directive effect (+54 to +67 pt lift) from natural blankness cleanly.
- The §8.3 reliability tripwire fired exactly as designed: the first-pass
  reviewer wording's lenient false-clear bias was caught by the mandated
  spot-checks and fixed with a wording revision at $0.

## What to watch

- Haiku zone verdicts jitter on borderline cells (whitecap texture, strip-edge
  intrusions). The conservative default + step-8 preview absorb this, but a
  repeat-variance measurement is a candidate future OQ.
- Ship-like tall subjects vs `top_strip` is the systematically hardest pairing;
  strategy-map authoring guidance (OQ-5, deferred) should steer these to side
  zones.
