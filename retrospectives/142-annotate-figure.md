# Retrospective: Feature #142 — annotate-figure

**Branch**: `feat/annotate-figure`
**Date**: 2026-07-17

## What Went Well

- **PoC-first de-risking**: a 30-minute proof (unlabeled render + vision
  anchors + PIL overlay, blind 10/10 on the B5 rubric) justified a
  compressed pipeline — no separate Opus design or adversarial design
  review — and the bet held; implementation surprises were all in
  polish, not architecture.
- **The E2E iteration loop worked as designed**: v2 caught a broken
  anchor + leader-through-box (reviewer), v3's residual defect was
  caught by the OPERATOR — the reviewer misread an invisible
  dark-on-dark leader as absent. Casing fixed the class, and the skill
  now tells reviewers about it.
- Geometric tests (Liang-Barsky no-leader-crosses-sibling-box) caught a
  second placement defect during development that visual inspection had
  missed.

## What Could Improve

- The v2 review scored a "correct" Rudder that the operator immediately
  saw was wrong — anchor verification needs the zoomed-crop discipline
  the re-query agent used, not whole-image glances. Folded into the
  skill's review prompt; a stricter contract (evidence clause per
  anchor) is a v2 candidate.
- Compressed pipeline means no adversarial pass over the SKILL.md
  itself; the standard reviewer pass at PR time covers it.

## Lessons Learned

1. **Reviewer verdicts on visibility are contrast-bounded** — "absent"
   and "invisible against this background" are indistinguishable to a
   casual pass. Design artifacts for contrast (casing) rather than
   training reviewers to squint.
2. Perfect text by construction re-scopes review budget entirely onto
   spatial correctness — cheaper AND stricter than reviewing both.
3. Vision anchor accuracy is the new quality bottleneck; evidence-clause
   contracts and zoomed verification are where future effort pays.

## Changes Made

- `plugins/jack-tar-deckhand/src/annotate_figure.py` (+48 tests)
- `plugins/jack-tar-deckhand/skills/annotate-figure/SKILL.md`
- deckhand 1.9.0 + marketplace; proposal doc; this retrospective

## Metrics

- **Files created**: 5 · **Files modified**: 3 · **Tests added**: 48
- E2E iterations: 4 renders (v1 PoC hand-placed → v4 cased) at $0
