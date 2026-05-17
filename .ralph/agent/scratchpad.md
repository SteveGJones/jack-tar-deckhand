# v1.4 Ralph scratchpad

## 2026-05-17 iter — phase_3_e5_adr (DONE @ 0869264)

State at start of iter:
- branch: feat/v1.4-push-and-paperbanana
- HEAD: 9d14347 (persona docs for academic_figure — E4)
- spent: $0.00 / $5.00
- last completed: phase_3_e4_persona_docs
- next: phase_3_e5_adr (budget: $0.00, docs-only)

E5 outcome:
- Wrote docs/architecture/paperbanana-integration.md — full ADR (10
  sections: context, decision, alternatives, contract surface,
  fallback behaviour, operator install guide, artefact map, risks,
  related decisions, references). Documents Option 4 (skill
  cross-invocation) + slim Option 2 (academic_figure strategy)
  composition. Operator install guide covers marketplace install +
  $PAPERBANANA_ROOT env-override + verify-skill READY/FALLBACK signal.
- Updated CLAUDE.md plugin-architecture table with an "Optional
  cross-plugin integration" paragraph linking the ADR.
- 103/103 deckhand suite still green (docs-only).
- Staged-by-explicit-path per §12.1; verified clean `git diff
  --cached --name-only` (only CLAUDE.md + the new ADR).
- commit=0869264.

Next iteration: phase_3_e6_dogfood (budget envelope: up to $0.50).
Per plan §6.5 E6, if paperbanana is not installed locally the
expected output is a documented fallback log at
`docs/superpowers/dogfooding/2026-05-17-paperbanana-integration.md`
noting "integration verified at contract level via E1-E3 tests;
end-to-end dogfood deferred to operator with paperbanana installed".
E6 also bumps deckhand 1.3.3 → 1.4.0 (plugin.json + marketplace.json).

## 2026-05-17 iter — phase_3_e4_persona_docs

State at start of iter:
- branch: feat/v1.4-push-and-paperbanana
- HEAD: 5f60cf6 (verify-skill detects paperbanana — E3)
- spent: $0.00 / $5.00
- last completed: phase_3_e3_verify
- next: phase_3_e4_persona_docs (budget: $0.00, docs-only)

E4 scope (plan §6.3):
1. plugins/jack-tar-deckhand/skills/narrative-architect/SKILL.md — add an
   "Optional: academic-figure strategy annotation" section in the same shape
   as the existing hero-resolution and brand-fidelity annotations. Tell
   narrative-architect WHEN to suggest the speaker pre-annotate a slide as
   academic_figure (Figure N captions, equations, citations, ablation
   studies, ML architecture diagrams) and that strategy-map +
   strategy_classifier.py will pick this up.
2. plugins/jack-tar-deckhand/agents/smartart-selector.md — add a deferral
   rule in Graphic Type Selection: if a slide's content already carries
   academic signals (Figure N: captions / equations / citations) AND the
   speaker is aiming for paper-quality output, DO NOT recommend
   bar_chart / line_chart / radar_chart. The strategy_classifier will route
   that slide to academic_figure (paperbanana E1/E2) which produces
   publication-grade output.

§12.1 reminder: NEVER `git add .` or `git add -A`. Stage by explicit path.
Code commit MUST contain only the two persona doc files. The
.ralph/agent/* files and the loose .ralph/* run-pointer files MUST stay
unstaged. Verify via `git diff --cached --name-only` before commit.
