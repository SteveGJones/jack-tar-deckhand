# Feature Proposal: Programmatic figure annotation — perfect labels over generated or external images

**Proposal Number:** 142 ([issue #142](https://github.com/SteveGJones/jack-tar-deckhand/issues/142))
**Status:** In Progress
**Author:** Claude (AI Agent), directed by operator
**Created:** 2026-07-17
**Target Branch:** `feat/annotate-figure`

---

## Executive Summary

Add an annotation-overlay capability: render a diagram-class image WITHOUT
labels (or accept an operator-supplied EXTERNAL image), obtain anchor
coordinates for the parts to label via a vision pass, then draw leader
lines and typeset labels programmatically. Text is perfect by
construction; pointer correctness becomes a vision-coordinate problem
instead of a diffusion problem. PoC (2026-07-17): blind 10/10 on the
benchmark's B5 rubric at $0, vs a cloud TECH ceiling of 8.7 (PR #138).

## Motivation

The 2026-07-17 benchmark's central finding: exact labels + correct
structure is where every model — local and cloud — is weakest. Diffusion
models draw scenes well and text/pointers badly. Splitting the work
(model draws, code writes) dissolves the weakness. Accepting external
images extends the pipeline to imagery we did not generate (photos,
screenshots, product shots, existing diagrams).

### User Stories

- As an operator, I want labeled technical figures whose text is always
  perfectly spelled, at local-draft cost.
- As an operator, I want to hand the pipeline an existing image and get
  it labeled the same way.
- As a developer, I want the overlay engine testable without any model
  call (pure function of image + anchors + labels).

## Design (v1)

1. **Module** `plugins/jack-tar-deckhand/src/annotate_figure.py`:
   - `validate_anchors(payload) -> dict` — validates the vision pass's
     JSON contract `{"anchors": {label: [x, y]}, ...}` (normalized 0-1
     floats; labels non-empty unique strings); raises with actionable
     messages.
   - `place_labels(anchors, image_size, *, margin_band=0.12) -> dict` —
     automatic occlusion-avoiding placement: each label is pushed outward
     from its anchor into the nearest margin band (top/bottom/left/right
     by anchor proximity), with collision resolution by vertical/
     horizontal stacking within a band. Deterministic.
   - `annotate(image_path, labels, out_path, *, font_size=26, style
     opts) -> Path` — PIL: leader line anchor→label, terminus dot, white
     label box with border, typeset text. `labels` is either
     `{name: [x,y]}` (auto placement) or `{name: {"anchor": [x,y],
     "label_pos": [x,y]}}` (explicit override).
   - No model calls in the module — pure imaging. Font fallback chain
     (Helvetica → DejaVu → PIL default).
2. **Skill** `/jack-tar-deckhand:annotate-figure` orchestrates:
   - Source: `--image <path>` (external, F10-free) OR a prompt → local
     draft render with a LABEL-STRIPPED prompt transform (drop quoted
     label directives; append "No text, no labels, no annotations of any
     kind."), via the standard local-draft ladder (klein/z-image).
   - Anchor pass: dispatch image-reviewer/general-purpose with the
     structured JSON contract from the PoC (normalized coords + bow-side
     style sanity fields where applicable); validate via the module.
   - Overlay via the module; then a review pass that verifies ANCHOR
     CORRECTNESS ONLY (text is axiomatic) — one refine loop re-querying
     coordinates for any mispointed label.
   - Output: annotated PNG path + manifest-style summary (source,
     anchors, review verdict).
3. **Out of scope for v1** (tracked in #142): PPTX-native text-box
   variant, strategy-map auto-routing, blank-zone generation variant.

### Acceptance Criteria

Given a prompt describing a labeled diagram
When `/annotate-figure` runs with local rendering
Then the output image contains every requested label spelled exactly
(by construction) with leader lines the reviewer verifies as anchored
correctly, at $0 cloud spend.

Given an external image path and a label list
When `/annotate-figure` runs
Then the same overlay flow applies with no generation step.

## Success Criteria

- [ ] Module unit tests green (validation, placement determinism +
      collision handling, drawing, external-source path)
- [ ] E2E: ship PoC reproduced through the skill flow
- [ ] deckhand 1.8.0 → 1.9.0; marketplace lockstep; CI green
- [ ] PR merged referencing #142

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Vision anchor errors (wrong part) | Mislabeled figure | Anchor-verification review + one refine loop; operator gate remains final |
| Label placement occludes content | Cluttered figure | Margin-band placement + collision stacking; explicit label_pos override |
| Label-stripped prompts still render stray text | Double text | "No text" negative in transform + reviewer flags stray text |
| Process note | — | Compressed pipeline (no separate Opus design/adversarial review) — PoC validated the core; recorded here as a deliberate deviation |

## Changes Made

| Action | File |
|--------|------|
| Create | `plugins/jack-tar-deckhand/src/annotate_figure.py` |
| Create | `plugins/jack-tar-deckhand/tests/test_annotate_figure.py` |
| Create | `plugins/jack-tar-deckhand/skills/annotate-figure/SKILL.md` |
| Modify | plugin.json + marketplace (1.9.0), plugin CLAUDE.md, root CLAUDE.md |
| Create | this proposal + `retrospectives/142-annotate-figure.md` |
