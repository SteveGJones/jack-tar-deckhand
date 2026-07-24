# Retrospective: Feature #142 v2.1 — composed zone + headline opt-in

**Branch**: `feat/annotate-figure-v2.1`
**Date**: 2026-07-23

_To be completed at feature close._

## Changes Made

- `plugins/jack-tar-deckhand/src/schemas/strategy_map.schema.json` — `annotation.show_headline` field
- `plugins/jack-tar-deckhand/src/assembler/build_deck.js` — composed zone routing + headline band
- `plugins/jack-tar-deckhand/src/assembler/build_deck_template.py` — composed zone routing + headline band + F-06 fallback chain
- `plugins/jack-tar-deckhand/src/qa/run_qa.py` — F-08 VISUAL_CHECKS for composed-strategy native slides
- `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md` — Step 4.8 composed placement-zone + dimensions wiring
- `plugins/jack-tar-deckhand/skills/annotate-figure/SKILL.md` — composed mode + headline opt-in documentation
- `plugins/jack-tar-deckhand/skills/iterate-slide/SKILL.md` — composed native + headline chrome-only notes
- `plugins/jack-tar-deckhand/tests/test_strategy_map_annotation.py`, `test_build_deck_annotation_js.py`, `test_build_deck_template_annotation.py`, `test_annotation_qa_checks.py`, `test_iterate_slide_dispatch.py` — new test coverage
- `plugins/jack-tar-deckhand/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` — deckhand `1.10.0 → 1.11.0`
- Filed follow-up issue [#147](https://github.com/SteveGJones/jack-tar-deckhand/issues/147) for F-09 (AN-01 relative-path hash-gate defect, pre-existing, not fixed in this release)
