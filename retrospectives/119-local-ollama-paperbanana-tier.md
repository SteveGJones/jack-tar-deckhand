# Retrospective: Feature #119 — Local-first Ollama tier + local_only mode

**Branch**: `feature/local-ollama-paperbanana-tier`
**Date**: 2026-07-11 (in progress; started 2026-07-10)

## What Went Well

- Critique-loop methodology proved itself live: Klein 9b went REFINE →
  PASS in one reviewer-driven prompt refinement; Klein 4b recovered
  from a 2/9 regression to a strong final via the annotation pattern +
  exact-spellings lock — all at $0.
- The whole feature landed without breaking any pre-existing contract:
  all v1.4 dispatch tests pass with `local_backend=False`.
- Negative findings were as valuable as positive ones: Klein's step
  curve inverting past ~20 steps (F8) and Z-Image's retirement for
  schemas (F11) both prevent future wasted renders.

## What Could Improve

- **The Haiku image-reviewer certified "Academic Figture" as correctly
  spelled "Academic Figure" (9b schema iter2)** — caught by the
  operator at the gate. Reviewer verdicts must stay advisory; an
  expected_text_content-style verbatim-transcription contract (as done
  for superpower-bridge Findings #19/#20) should be applied to
  academic-figure reviews.
- The long-lived reviewer agent's transcript expired mid-exercise after
  many resumes; per-review fresh dispatch with inlined history is the
  more robust pattern.
- SDLC artefacts (issue, proposal, branch) were created after the
  spike/dogfood work rather than before — acceptable for an
  exploration that turned into a feature, but the transition point
  should have been called earlier.

## Lessons Learned

1. For local diffusion models, prompt shape beats model size: label
   lists ≤8 + annotations out-render dense prose even on the bigger
   model.
2. Never repeat a label word inside the style block ("Background" vs
   "white background" collision).
3. Iteration caps in a free tier should be checkpoints (accept / loop
   again / hand-edit), not escalation triggers.
4. Human review at the gate catches what automated review misses —
   the operator found a misspelling the reviewer had certified.

## Changes Made

- See the proposal's Changes Made table; headline: local-first ladder +
  local_only mode in `paperbanana_dispatch.py`, critique loop in
  imagegen-bridge SKILL.md, 2-round dogfood log, ADR §8.5 addendum.

## Metrics

- **Files modified**: 5
- **Files created**: 4 (+ 14 dogfood render PNGs, gitignored)
- **Tests**: 34 → 69 in the dispatch suite; 441 plugin-wide, all green
- **Dogfood spend**: $0.00 (16 local renders, 2 subjects, 3 models)
