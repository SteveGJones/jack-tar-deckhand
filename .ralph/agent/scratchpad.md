# Rendering Strategy Expansion Scratchpad

## Objective
Expand Jack-Tar Deckhand rendering pipeline from 3 strategies to 5:
- Keep: full_render, backdrop_render (backward compat), composed
- Add: background, backdrop, pragmatic_composition

## Plan
14 tasks in the implementation plan. Working sequentially.

Baseline: 446 tests passing.

## Phase 1: Foundation (Tasks 1-6)
- Task 1: Expand StrategyMap schema (add background, backdrop, pragmatic_composition to enum, add backdrop_variant and element_layout fields)
- Task 2: Expand ImageManifest schema (add detected_positions, element_id, placement_zone)
- Task 3: Update classify_slide_strategy (dense content → background instead of backdrop_render)
- Task 4: Add get_element_layout() function with 5 templates
- Task 5: Add select_backdrop_variant() function
- Task 6: Update assemble_brief() for new strategies

## Phase 2: Background Rendering (Tasks 7-8)
- Task 7: Add buildBackgroundSlide() to assembler
- Task 8: Add assembler routing for background strategy

## Phase 3: Backdrop Rendering (Tasks 9-10)
- Task 9: Create vision-analyst agent
- Task 10: Add buildBackdropSlide() with vision-detected positions

## Phase 4: Pragmatic Composition (Tasks 11-12)
- Task 11: Add buildPragmaticSlide() to assembler
- Task 12: QA checks AP-27, AP-28

## Phase 5: Integration (Tasks 13-14)
- Task 13: Strategy fixture and QA routing
- Task 14: Integration tests (Ollama-tagged)

## Notes
- TDD strict: test fails first, then implement
- All existing 446 tests must continue to pass
- No cloud API calls, Ollama only for image gen
- Commit after each task

## Task 2: Expand ImageManifest Schema — DONE
- Added `element_id` (string) and `detected_positions` (array with bbox + confidence) to image_manifest.schema.json
- Tests passed immediately because schema allows additional properties by default (no additionalProperties: false)
- Schema update still valuable to document the contract and enforce detected_positions item structure
- 452 tests passing (446 original + 6 from Task 1 StrategyMap schema expansion)

## Task 3: Expand Strategy Classification — DONE
- Updated classify_slide_strategy: dense content (>2 bullets) now returns 'background' instead of 'backdrop_render'
- Updated build_strategy_map overrides to include 'background' and 'backdrop' in full render funnel list
- Also needed to update test_conductor.py::test_upgrade_slide_strategy which asserted 'backdrop_render' — updated to 'background' (same intent, name changed)
- 454 tests passing (452 + 2 new Task 3 tests)

## Task 4: Add Element Layout Template Library — DONE
- Added _ELEMENT_LAYOUTS dict and get_element_layout() function to src/slide_prompt_composer.py
- 5 templates: three_across, two_column, grid_2x2, process_flow, hub_and_spoke
- get_element_layout() raises ValueError for count > 5 or unknown template
- Elements include id, label_source, x, y, w, h fields
- 6 new tests, all passing
- 460 tests passing (454 + 6 new)

## Task 5: Add backdrop_variant Selection — DONE
- Added _BACKDROP_VARIANTS list and select_backdrop_variant() function to src/slide_prompt_composer.py
- Cycles through 5 variants: left_panel, bottom_bar, right_panel, top_band, center_float
- Consecutive slides always get different variants due to cycling order
- 2 new tests, both passing
- 462 tests passing (460 + 2 new)

## Task 6: Update assemble_brief for New Strategies — DONE
- Added backdrop_variant and element_layout keyword args to assemble_brief()
- Extended text_instruction logic to cover 'background', 'backdrop', 'pragmatic_composition' (all get NO TEXT instruction)
- backdrop_variant and element_layout are included in brief only when provided
- 3 new tests, all passing
- 465 tests passing (462 + 3 new)
- Phase 1 Foundation COMPLETE (Tasks 1-6)

## Task 7: Expand Assembler Strategy Routing — DONE
- Created tests/fixtures/minimal_deck/strategy-map.json with full_render/background/composed slides
- Added test_build_deck_with_background_strategy to tests/test_assembler.py
- Updated build_deck.js: backdrop_render|background stub, backdrop stub, pragmatic_composition stub (all route to buildBackdropRenderSlide for now)
- Updated run_qa.py: expanded elif to cover backdrop_render|background|backdrop|pragmatic_composition
- 466 tests passing (465 + 1 new)
- Phase 2 Background Rendering: next task is Task 8 — implement buildBackgroundSlide

## Task 8: Implement buildBackgroundSlide with 5 Template Zones — DONE
- Added test_build_deck_background_variants (sets backdrop_variant: 'bottom_bar', checks returncode 0)
- Test passed with stub (returncode already 0), then implemented real buildBackgroundSlide
- Routing updated: backdrop_render|background now reads backdrop_variant from strategy map, calls buildBackgroundSlide
- 5 zones: left_panel, right_panel, bottom_bar, top_band, center_float — each with overlay rect + heading + body text
- Unknown variant falls back to left_panel
- 467 tests passing (466 + 1 new)
- Phase 2 Background Rendering COMPLETE

## Task 9: Implement split_element_briefs — DONE
- Added split_element_briefs() to src/slide_prompt_composer.py
- Produces 1 background brief + N element briefs for pragmatic composition
- Background brief: atmospheric texture, NO TEXT instruction
- Element briefs: individual illustration per element_layout slot, target_dimensions computed from resolution
- shared_style_prefix ties all briefs to a consistent visual style
- 2 new tests, both passing
- 469 tests passing (467 + 2 new)
- Next: Task 10 — buildPragmaticSlide in assembler

## Task 10: Implement buildPragmaticSlide — DONE
- Added findSlideImages() helper (filters all images for a slide, excluding failed)
- Added buildPragmaticSlide(): bg image full-bleed, element images at prescribed positions, text label pills, headline in title_region
- Updated pragmatic_composition routing to call buildPragmaticSlide with imageManifest + strategyEntry
- 470 tests passing (469 + 1 new)
- Next: Task 11 — Create vision-analyst agent

## Task 11: Create vision-analyst agent — DONE
- Created .claude/agents/vision-analyst.md
- Haiku model, returns normalised bounding boxes as JSON
- No Python tests (agent definition only)
- 470 tests still passing
- Next: Task 12 — buildBackdropSlide with vision-detected positions + fallback

## Task 12: Implement buildBackdropSlide — DONE
- Added buildBackdropSlide() to src/assembler/build_deck.js
- Full-bleed scene image, then text labels at vision-detected positions (falling back to element_layout positions when no detected_positions)
- Updated backdrop routing to call buildBackdropSlide with imageManifest + strategyEntry
- 2 new tests, both passing
- 472 tests passing (470 + 2 new)
- Phase 4 backDROP COMPLETE
- Next: Task 13 — QA checks AP-27 and AP-28

## Task 13: QA checks AP-27 and AP-28 — DONE
- Created src/qa/checks/element_layout.py with check_element_layout (AP-27) and check_vision_confidence (AP-28)
- AP-27 validates: element count ≤ 5, bounds within 0.0-1.0, label_source references valid body_point indices
- AP-28 flags detected_positions with confidence < 0.7
- Wired into run_qa.py after per-slide loop; guards for missing outline.json added (not in plan but required for robustness)
- 6 new tests, all passing
- 478 tests passing (472 + 6 new)
- Next: Task 14 — Integration tests (tagged @pytest.mark.ollama)

## Task 14: Integration Tests — DONE
- Created tests/test_integration_rendering.py with 2 ollama-tagged tests
- Created pyproject.toml with ollama marker registration
- Both integration tests PASSED (Ollama was running with x/z-image-turbo:fp8 model)
- Full suite: 480 tests passing (478 + 2 new)
- pytest -m "not ollama": 478 passed, 2 deselected
- OBJECTIVE COMPLETE: All 14 tasks done, 14 commits, 480 tests passing
