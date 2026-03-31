# Draft Deck — Layout Testing Scratchpad

## 2026-03-31 — Iteration 1: Init + Strategy Map

**Starting state:** No draft-state.json. Old strategy-map.json had only 3 strategies (full_render, composed, backdrop_render).

**This iteration:**
- Created draft-state.json (phase: strategy_map)
- Wrote new strategy-map.json with all 5 strategies:
  - full_render: slides 1, 13
  - background: slides 2 (left_panel), 7 (right_panel), 12 (bottom_bar)
  - backdrop: slides 5 (grid_2x2), 10 (grid_2x2)
  - pragmatic_composition: slides 9 (three_across), 11 (three_across)
  - composed: slides 3, 4, 6, 8, 14
- Validated: all 5 strategies present, 14 slides
- Created 5 tasks for remaining phases

**Existing images (wrong naming convention):**
- slide-01-hero.png ✓ (full_render, keep)
- slide-02-hero.png ✗ (should be slide-02-bg.png)
- slide-03-diagram.png ✓ (composed, keep)
- slide-05-hero.png ✗ (should be slide-05-scene.png)
- slide-06-diagram.png ✓ (composed, keep)
- slide-07-hero.png ✗ (should be slide-07-bg.png)
- slide-09-hero.png ✗ (should be slide-09-bg.png + 3 elements)
- slide-10-hero.png ✗ (should be slide-10-scene.png)
- slide-11-hero.png ✗ (should be slide-11-bg.png + 3 elements)
- slide-12-hero.png ✗ (should be slide-12-bg.png)
- slide-13-hero.png ✓ (full_render, keep)
- logo.png ✓ (keep)
- slide-04-diagram.png — stale, not needed
- slide-06-hero.png — stale, not needed

**Next iteration:** Start task deck:gen-images. Clean up old images, then generate all 17 images needed.
Key images to generate in priority order:
1. slide-02-bg.png, slide-07-bg.png, slide-12-bg.png (background slides)
2. slide-05-scene.png, slide-10-scene.png (backdrop scenes — needed for vision analysis)
3. slide-09-bg.png + 3 elements, slide-11-bg.png + 3 elements (pragmatic)
4. slide-01-hero.png already exists — check if reusable
5. slide-13-hero.png already exists — check if reusable
6. Diagrams: slide-03-diagram.png, slide-06-diagram.png — keep existing

**generate_image.py location:** need to confirm it's at `src/generate_image.py` or find the right path.

## 2026-03-31 — Iteration 2: Image Generation

**Task:** deck:gen-images (task-1774931438-2b9d) — Generate all 17 images

**Actions taken:**
- Cleaned up stale/misnamed images: slide-02-hero.png, slide-05-hero.png, slide-07-hero.png, slide-09-hero.png, slide-10-hero.png, slide-11-hero.png, slide-12-hero.png, slide-04-diagram.png, slide-06-hero.png
- Kept: slide-01-hero.png, slide-03-diagram.png, slide-06-diagram.png, slide-13-hero.png, logo.png
- Generated 13 new images with x/z-image-turbo:fp8 at 1024x576 (elements at 512x512)

**All 17 images now present:**
- slide-01-hero.png (full_render) — reused
- slide-02-bg.png (background/left_panel) — generated
- slide-03-diagram.png (composed) — reused
- slide-05-scene.png (backdrop) — generated
- slide-06-diagram.png (composed) — reused
- slide-07-bg.png (background/right_panel) — generated
- slide-09-bg.png + 3 elements (pragmatic_composition) — generated
- slide-10-scene.png (backdrop) — generated
- slide-11-bg.png + 3 elements (pragmatic_composition) — generated
- slide-12-bg.png (background/bottom_bar) — generated
- slide-13-hero.png (full_render) — regenerated (was already there)

**Phase:** generating → next is vision_analysis for slides 5 and 10

**Next iteration:** Run vision analysis (task deck:vision-analysis) on slide-05-scene.png and slide-10-scene.png using vision-analyst agent. Detect positions of 4 element groups in each scene.
