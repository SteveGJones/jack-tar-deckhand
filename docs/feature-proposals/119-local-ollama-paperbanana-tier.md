# Feature Proposal: Local-first Ollama tier + local_only mode for the academic_figure pipeline

**Proposal Number:** 119 ([issue #119](https://github.com/SteveGJones/jack-tar-deckhand/issues/119))
**Status:** In Progress
**Author:** Claude (AI Agent), directed by operator
**Created:** 2026-07-11
**Target Branch:** `feature/local-ollama-paperbanana-tier`

---

## Executive Summary

Extend the paperbanana way of working (the `academic_figure` rendering
strategy) to run on local Ollama models, with a `local_only` mode that
guarantees zero cloud spend. The free local draft always renders first;
paid tiers (paperbanana CLI / Nano Banana) become escalation choices
behind the F10 operator gate — or cease to exist entirely in local_only
mode. A `LocalBackend` provider seam prepares for a future MLX backend.

---

## Motivation

### Problem Statement

Before this feature, an `academic_figure` slide on a machine without the
paperbanana CLI went **straight to paid cloud rendering** (Nano Banana
Flash 1K) with no free preview — inconsistent with the F10 rule (operator
gate at every free→cost transition) that the creative_vision cascade
already enforces, and inconsistent with the cascade's free Ollama tier 0.
Additionally, no mode existed in which an operator could guarantee a
deck's academic figures cost $0.

### User Stories

- As an operator, I want academic figures drafted free on my local
  Ollama models first, so I only pay for cloud rendering after seeing
  and approving a free preview.
- As an operator, I want a `local_only` option so that a run can NEVER
  reach a paid tier, no matter what any reviewer agent recommends.
- As a developer, I want the local backend behind a provider seam so an
  MLX backend can be added without touching the ladder logic.

---

## Proposed Solution

1. `detect_local_backend()` in `paperbanana_dispatch.py` probes Ollama's
   `/api/tags` (2 s budget, degrades to None on any failure). Family
   priority `x/flux2-klein` > `x/z-image-turbo`; largest parameter
   variant within a family; operator override via `local-config.json` →
   `ollama.academic_figure_model`. Exact installed tags only.
2. `PaperbananaDispatch` gains `backend`, `local_provider`,
   `local_model`, `local_args {prompt, caption, width, height,
   iterations}`, `local_only`. Escalation args ride on the same struct
   so post-gate escalation needs no payload rebuild.
3. Ladder: **Ollama draft ($0) → free critique loop → F10 operator gate
   → paperbanana CLI or Nano Banana Flash 1K.** With no local backend,
   pre-existing v1.4 behaviour is unchanged.
4. `local_only` (per-slide `slide.local_only` or machine-wide
   `local-config.json` → `ollama.academic_figure_local_only`): paid
   tiers do not exist; iteration budget 5 (vs 3 in ladder mode; parity
   with the creative_vision ollama cap); exhausting the budget surfaces
   best-so-far at the gate (accept / loop again free / hand-edit). If no
   local backend is up, dispatch returns `backend:
   "local_only_blocked"` — never a silent cloud fallback.
5. Free critique loop codified in imagegen-bridge SKILL.md Step 4.6:
   render → image-reviewer → prompt refinement (F11 label-list
   simplification, annotation demotion, exact-spellings lock) →
   re-render; stop on PASS or 2-render plateau.
6. Manifest entries: `backend: "ollama_local"`, exact `model_used` tag,
   `local_provider`, `local_args`, `local_only`; `backend_used=`
   override records post-gate escalations truthfully.

### Acceptance Criteria

Given Ollama is running with `x/flux2-klein` pulled
When an `academic_figure` slide is dispatched
Then the first render is a free local draft and no paid call occurs
before explicit operator go-ahead at the F10 gate.

Given `local_only` is set (slide or machine level)
When the critique loop exhausts its 5-render budget without a PASS
Then the best-so-far render is surfaced at the operator gate and no
paperbanana/cloud dispatch is ever made.

Given `local_only` is set and Ollama is unreachable
When the slide is dispatched
Then the dispatch returns `local_only_blocked` and the bridge skips the
slide with remediation guidance — it does not fall through to cloud.

---

## Success Criteria

- [x] Dispatch unit tests green (69/69; 431 plugin-wide)
- [x] Live dogfood round 1: model comparison (Klein 4b/9b, Z-Image) — $0
- [x] Live dogfood round 2: full critique loops on the deck-schema
      figure across all three models — $0
- [ ] 9b schema figure at a true operator-verified 9/9 (reviewer missed
      "Academic Figture" — see Risks)
- [ ] PR merged with CI green

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Haiku image-reviewer certifies misspelled labels (observed: passed "Academic Figture" as correct) | Operator ships a figure with a typo | F12 stance: reviewer verdicts advisory, operator gate certifies. Follow-up: expected_text_content contract (superpower-bridge Finding #19/#20 treatment) for academic-figure reviews |
| Ollama API shape changes | Detection breaks | Probe degrades to None → pre-existing ladder; single probe function to update |
| Step-count folklore ("more steps = better") | Wasted renders, regressions | F8 documented: Klein step curve inverts past ~20; codified in dogfood log |
| local_only blocked when Ollama down | Slide unrendered | Explicit `local_only_blocked` state with remediation message; never silent spend |

---

## Changes Made

| Action | File |
|--------|------|
| Modify | `plugins/jack-tar-deckhand/src/paperbanana_dispatch.py` (LocalBackend, detect_local_backend, local-first ladder, local_only, manifest) |
| Modify | `plugins/jack-tar-deckhand/tests/test_paperbanana_dispatch.py` (34 → 69 tests) |
| Modify | `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md` (Step 4.6 local branch, critique loop, local_only gate) |
| Modify | `docs/architecture/paperbanana-integration-v2.md` (§8.5 addendum) |
| Modify | `CLAUDE.md` (paperbanana section: local-first tier) |
| Create | `docs/superpowers/dogfooding/2026-07-11-ollama-academic-figure-model-comparison.md` |
| Create | `local-config.json` (gitignored, machine-specific) |
| Create | `docs/feature-proposals/119-local-ollama-paperbanana-tier.md` (this file) |
| Create | `retrospectives/119-local-ollama-paperbanana-tier.md` |
