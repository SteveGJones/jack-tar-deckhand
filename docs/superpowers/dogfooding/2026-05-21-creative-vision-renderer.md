# 2026-05-21 — Creative Vision Renderer first-run readiness (#105)

## Scope

Infrastructure readiness for the FIRST real cascade dogfood run of the new
creative_vision pipeline. The cascade itself is operator-driven (real-time
coordination + budget approval); this log captures what's in place and what
the operator needs to do to drive the first run.

## What landed (commits on feat/creative-page-renderer)

| Commit | Task | What |
|---|---|---|
| `64550da` | T1 | ParsedVision schema |
| `77fdb40` | T2 | DirectorsCriticVerdict schema |
| `a26afc6` | T3 | CreativeVisionManifest schema (DirectorsCriticVerdict inlined per authorised deviation) |
| `73b8e35` | T4 | strategy_map.schema.json extended with creative_vision enum + nested block + allOf rule |
| `8662432` | T5 | Package skeleton (8 stub files) |
| `6e4d062` | T6 | manifest create/load/save |
| `21769c4` | T7 | manifest.revise_prose |
| `2cad4b7` | T8 | manifest.append_attempt + finalise |
| `ac7818c` | T9 | cascade tier ladders + costs + iteration caps |
| `cbecc44` | T10 | cascade.detect_plateau |
| `c0f9c9c` | T11 | cascade.can_afford + next_tier |
| `07f279e`, `4d44ca4` | T12 | directors-brief.md agent (Sonnet) + review-loop fixes |
| `423cf47` | T13 | brief.py input/output helpers |
| `5975f44` | T14 | prompt-reviewer.md agent + prompt_reviewer.py |
| `e1989af` | T15 | directors-critic.md agent + critic.py |
| `523ec53` | T16 | orchestrator.advance_text_loop |
| `39f4844` | T17 | orchestrator.decide_next_action |
| `26d936f` | T18 | creative_vision_dispatch.initialise_dispatch |
| `e61405d` | T19 | imagegen-bridge SKILL.md — orchestration loop |
| `c31346b` | T20 | strategy-map SKILL.md — vision-aware authoring |
| `c2df3b3` | T21 | iterate-slide three-channel branch (revise_prose / refine_prompt / escalate_tier) |
| `6b366ae` | T22 | ADR docs/architecture/creative-vision-renderer.md |
| `b1c1311` | T23 | Plugin version bump 1.4.2 → 1.5.0 |
| `f4d90f6` | T24 | Ollama-only e2e smoke test (gated by ENABLE_E2E) |

Final test count: 296 plugin tests passing (baseline 226 + 70 new across creative_vision modules).

## Dogfood deck infrastructure prepared

- **Setup script**: `tmp/creative-vision-dogfood/setup_deck.py` (gitignored)
- **Vision prose**: sun-phases founding example (operator's example c from issue #105)
- **Budget**: $0.30 cap with `allowed_ceiling: flash_1k` — no Pro escalation in this dogfood
- **Manifest** initialised at `tmp/creative-vision-dogfood/deck/creative-vision/1/manifest.json`

### Manifest initialization state

Manifest run_id: `cv-2026-05-22-031123-d6e55c-slide-1`

Current state snapshot:
- **strategy**: creative_vision
- **prose_history length**: 1 (original sun-phases prose)
- **attempts**: 0 (no cascade runs yet)
- **final**: null (not finalised)
- **iterate_slide_hooks**:
  - current_tier: ollama
  - next_tier_available: flash_1k
  - can_revise_prose: true
  - can_refine_prompt: true
  - can_escalate_tier: true
  - remaining_budget_usd: $0.30

## What the operator needs to drive (the actual dogfood)

The infrastructure (agents, schemas, helpers, SKILL.md) is in place. The first real cascade run involves:

1. **Read** the manifest's current state (Ollama tier, no attempts yet, $0.30 budget).
2. **Build the Director's Brief input** via `brief.build_brief_input(vision_prose=..., prior_parsed_vision=None, accumulated_feedback=[], current_tier="ollama", brand_fidelity="none")`.
3. **Dispatch the `directors-brief` agent** (Sonnet) with that input. Receive the response.
4. **Parse the output** via `brief.parse_brief_output(response)` → `(parsed_vision, prompt)`.
5. **Build the Prompt Reviewer input** via `prompt_reviewer.build_reviewer_input(...)`.
6. **Dispatch the `prompt-reviewer` agent** (Haiku). Parse the verdict.
7. **Advance text-loop state** via `orchestrator.advance_text_loop(...)`. If `terminal: False`, return to step 2 with the reviewer's issues as accumulated feedback.
8. When text-loop is terminal, **render via Ollama** using the approved prompt (call `jack-tar-ollama:image` skill).
9. **Dispatch image-reviewer** on the rendered PNG (do NOT Read the PNG yourself — discipline hook applies).
10. If image-reviewer says refine, return to the Brief with the visual-quality issues as feedback.
11. When image-reviewer passes, **dispatch the Director's Critic** via `critic.build_critic_input(...)`.
12. **Parse** the critic verdict via `critic.parse_critic_output(...)` (schema-validates).
13. **Decide next action** via `orchestrator.decide_next_action(...)`.
14. **Append** the attempt to the manifest and `save_manifest()`.
15. Branch on the action.kind: `accept` (finalise), `refine_at_tier` (loop back), `escalate_tier` (bump to flash_1k), `abort`.

The imagegen-bridge SKILL.md section "Creative vision strategy (#105)" documents these steps with code snippets.

## What this dogfood will discover (the value)

This is the FIRST live exercise of:

- The Director's Brief agent's prompt design — does it preserve operator's prose verbatim under iteration?
- The Prompt Reviewer's named-entity preservation discipline — does it catch dropped elements?
- The Director's Critic's per-axis scoring rubric — do the 0-100 scores align with operator's intuition?
- The cascade plateau detection — does it fire at the right moment?
- The manifest's `iterate_slide_hooks` data shape — does iterate-slide consume it cleanly?

Any SKILL.md ambiguities or agent-prompt gaps surface here and feed back as follow-up issues.

## Status

**Infrastructure: READY** — all 25 plan tasks complete, full plugin test suite (296 tests) green, plugin version bumped to 1.5.0.

**First cascade run: PENDING OPERATOR DRIVE.** The setup script has initialised the manifest; the operator (or Claude under operator supervision, in a fresh session) drives the multi-agent loop per the imagegen-bridge SKILL.md instructions. Estimated spend for this dogfood: $0–$0.067 (Ollama free if it produces something usable; one Flash 1K render if Ollama draft is rejected).

## Recommended next steps after this dogfood

1. Capture the rendered image's reviewer verdict and Director's Critic verdict in this log.
2. File follow-up issues for any SKILL.md gaps or agent-prompt weaknesses surfaced.
3. Open PR for the entire feat/creative-page-renderer branch.
4. Once merged, run a second dogfood with one of the other founding examples (ships or man-o-war) to validate the named-entity preservation property.

## Cross-references

- Spec: [docs/superpowers/specs/2026-05-21-creative-vision-renderer-design.md](../specs/2026-05-21-creative-vision-renderer-design.md)
- Plan: [docs/superpowers/plans/2026-05-21-creative-vision-renderer.md](../plans/2026-05-21-creative-vision-renderer.md)
- ADR: [docs/architecture/creative-vision-renderer.md](../../architecture/creative-vision-renderer.md)
- Issue #105: https://github.com/SteveGJones/jack-tar-deckhand/issues/105
