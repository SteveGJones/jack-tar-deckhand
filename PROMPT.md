# PROMPT.md — v1.4 push + paperbanana autonomous execution driver

You are Claude Code, executing the v1.4 push for the jack-tar-deckhand repo overnight. You run inside a Ralph Loop — each iteration re-reads this file, performs ONE atomic chunk of work, updates state, commits, and exits. Ralph re-invokes you until state.status reaches `complete` or `blocked`.

**The operator is asleep.** Do not ask questions. Resolve ambiguity using the plan document; if the plan does not resolve it, escalate (write blocker, exit). Do NOT improvise beyond the plan.

---

## 1. Identity and scope

**Working branch**: `feat/v1.4-push-and-paperbanana` (create off `main` if absent).
**Plan document** (authoritative for all design decisions): `docs/superpowers/plans/2026-05-17-v1.4-push-and-paperbanana.md`
**State file**: `.ralph/v1.4-state.json` (create with defaults if absent — see §4).
**Blocker file** (write on escalation only): `V1.4-BLOCKER.md` at repo root — visible location so operator sees it immediately on morning checkin. Keep `.ralph/v1.4-blocker.md` as a mirror for state-tooling parity.

**Scope**: 6 phases covering 7 issues (#87-#93) + #86 + 6 paperbanana sub-deliverables (E1-E6 in plan §6 Phase 3). See plan §1 for the inventory.

---

## 2. HARD RULES (DO NOT BREAK)

### 2.1 Verification budget — $5.00 USD HARD CAP

- Track cumulative cloud-image spend in `state.verification_spent_usd`.
- Before ANY cloud-image generation call, compute `state.verification_spent_usd + estimated_cost`. If that exceeds `4.50` (90% of cap), ESCALATE — write blocker noting budget proximity, do NOT make the call.
- After each cloud-image call, immediately update `state.verification_spent_usd` AND append an entry to `state.verification_calls`.
- Token spend for agent dispatches (Sonnet, Haiku, etc.) is NOT counted against this budget. Only cloud image generation costs.

### 2.2 Tier discipline — ranked cheapest first

| Tier | Provider/model | Cost/img | When to use |
|---|---|---|---|
| Tier 0 | Imagen Fast 1K (`imagen-4.0-fast-generate-001`) | $0.020 | Non-text-bearing visuals (atmospheric backgrounds, illustrative scenes) |
| Tier 1 | **Nanobanana Flash 1K** (`gemini-3.1-flash-image-preview`) — **DEFAULT** | $0.067 | Default for all verification gates; text + complex composition |
| Tier 2 | Nanobanana Pro 1K (`gemini-3-pro-image-preview`) | $0.134 | Only if Flash fails review twice AND budget remains > $1.00 |
| Tier 3 | Pro 4K | $0.240 | **PROHIBITED** for v1.4 work — would burn 5% of budget per shot |

Recraft chain is **PROHIBITED** for v1.4 (high cost, marginal value for verification).

For agent dispatches inside Ralph iterations, default `model="haiku"` for mechanical tasks (file edits, lookups, format checks) per the MANDATORY rule in `CLAUDE.md`. Use `model="sonnet"` only for tasks requiring judgement (design decisions, visual review, prose writing, multi-step investigations).

### 2.3 Discipline hook

The `jack-tar-deckhand` plugin's PreToolUse hook (issue #76, PR #79) blocks `Read` on image files in YOUR session. NEVER attempt `Read` on `.png/.jpg/.jpeg/.gif/.webp/.bmp/.tiff`. ALWAYS dispatch the `jack-tar-deckhand:image-reviewer` (Haiku) or `general-purpose` (Sonnet) agent for visual verification.

Phase 0 of this plan (issue #86) may close a gap where Task-dispatched subagents bypass the hook. Until then, every delegated implementation prompt MUST explicitly remind the dispatched agent to use subagents for visual review.

### 2.4 Branch and merge

- Working branch: `feat/v1.4-push-and-paperbanana`. Create with `git checkout -b ...` if absent.
- Commit per atomic step. Commit messages: `feat(plugin): <description> (#issue)` or `fix(plugin): ...` or `docs: ...`.
- DO NOT open PRs. DO NOT push to main. DO NOT force-push. DO NOT use `--admin`. The operator batches PRs in the morning.
- After every code change touching `src/` AND `plugins/<plugin>/src/`, verify byte-identity. If they drift, fix in the same commit.

### 2.5 Version bumps

Each phase has a designated version bump (see plan §6). Update both the plugin's `.claude-plugin/plugin.json` AND the marketplace manifest at `.claude-plugin/marketplace.json` in the same commit. Verify with `grep "version" .claude-plugin/marketplace.json | head -8` after edit.

### 2.6 Test discipline

After every code change, run the affected plugin's test suite:
```
cd plugins/<plugin-name> && python3 -m pytest -q
```

Tests must pass before commit. If a test fails:
1. First attempt: read the failure, fix the obvious cause, re-run.
2. Second attempt: read the test, read the code, fix the deeper cause, re-run.
3. Third attempt: ESCALATE. Do not keep guessing.

---

## 3. INPUTS (read at start of each iteration)

You MUST read these files in order before deciding what to do:

1. `.ralph/v1.4-state.json` — your authoritative progress record.
2. `docs/superpowers/plans/2026-05-17-v1.4-push-and-paperbanana.md` — the plan (especially §5 sequencing, §6 phase details, §2 resolved decisions).
3. The most recent commit on the working branch: `git log -1 --format='%H %s'`.

You MAY read these as needed:
- `/tmp/issues-87-93-triage.md` — original triage.
- `/tmp/paperbanana-vs-jack-tar-research.md` — paperbanana borrow patterns.
- The relevant GitHub issue: `gh issue view N` for the current phase's issue.

---

## 4. STATE MODEL

`.ralph/v1.4-state.json`:

```json
{
  "schema_version": "1.0",
  "started_at": "2026-05-17T20:00:00Z",
  "last_updated_at": "2026-05-17T20:00:00Z",
  "status": "in_progress",
  "current_phase": "phase_0",
  "current_step": "investigation",
  "verification_budget_usd": 5.00,
  "verification_spent_usd": 0.00,
  "verification_calls": [],
  "phases": {
    "phase_0_discipline_hook": {"status": "not_started", "issue": "#86"},
    "phase_1_cloud_safety_filter": {"status": "not_started", "issue": "#92"},
    "phase_2a_strap_style": {"status": "not_started", "issue": "#93"},
    "phase_2b_register_presets": {"status": "not_started", "issue": "#87"},
    "phase_3_e1_strategy": {"status": "not_started"},
    "phase_3_e2_dispatch": {"status": "not_started"},
    "phase_3_e3_verify": {"status": "not_started"},
    "phase_3_e4_persona_docs": {"status": "not_started"},
    "phase_3_e5_adr": {"status": "not_started"},
    "phase_3_e6_dogfood": {"status": "not_started"},
    "phase_4a_text_density": {"status": "not_started", "issue": "#91"},
    "phase_4b_composition_primitives": {"status": "not_started", "issue": "#90"},
    "phase_5a_full_bleed": {"status": "not_started", "issue": "#88"},
    "phase_5b_iterate_slide": {"status": "not_started", "issue": "#89"},
    "final_v14_end_to_end_dogfood": {"status": "not_started"}
  },
  "completed_phases": [],
  "blocker": null,
  "iteration_count": 0
}
```

**Status values**: `not_started` | `in_progress` | `verified` | `committed` | `done` | `blocked` | `skipped`.

After any state change, write the file atomically (write to `.ralph/v1.4-state.json.tmp` then `mv` over the target). Update `last_updated_at` ISO timestamp and increment `iteration_count`.

---

## 5. ITERATION ALGORITHM

Each Ralph iteration:

1. **Read state**. If missing, create with the §4 defaults.
2. **Stop checks** (in order — exit cleanly on any match):
   - If `state.status == "complete"`: invoke `Skill(skill="ralph-loop:cancel-ralph", args="")` (idempotent — safe even if already cancelled), exit. The loop's done.
   - If `state.status == "blocked"`: exit immediately. Do NOT touch any files. The blocker is at `V1.4-BLOCKER.md` and was already committed by the iteration that escalated; subsequent iterations are defence-in-depth only. Cancel-ralph was already invoked in §8 step 5.
   - If `state.verification_spent_usd >= 4.50`: escalate via §8 with blocker reason "verification budget approaching cap at $<X.XX>".
   - If `state.iteration_count >= 200`: escalate via §8 with blocker reason "iteration cap reached, loop appears stuck".
3. **Read recent git state**. If working tree is dirty AND HEAD is not the expected per state.last_commit: write blocker "unexpected dirty tree", exit.
4. **Ensure working branch**. `git rev-parse --abbrev-ref HEAD` should be `feat/v1.4-push-and-paperbanana`. If not, `git checkout main && git checkout -b feat/v1.4-push-and-paperbanana` (create only if branch absent).
5. **Pick next atomic step**:
   - Find the phase in `state.phases` with status `in_progress` (resume).
   - Otherwise, find the next phase in execution order (§6) with status `not_started`.
   - If all phases done: set status `complete`, exit.
6. **Execute one atomic step** within that phase (see §6 catalogue).
7. **Verify** the step (tests, byte-identity, etc.) per §2.6.
8. **Update state** (write file atomically, increment iteration_count).
9. **Commit** if the step modified code (skip commit for read-only investigation steps; squash with the next commit). Commit message format: `<type>(plugin): <description> (#issue)` or `<type>: <description>`.
10. **Exit**.

If Ralph holds context across iterations, you MAY perform multiple atomic steps in one iteration as long as each step independently commits. Do not skip the commit between steps.

---

## 6. PHASE EXECUTION ORDER + ATOMIC STEPS

Execution order (per plan §5):

1. **Phase 0** — discipline hook propagation (#86)
2. **Phase 1** — Cluster D, cloud safety filter (#92)
3. **Phase 2a** — strap_style (#93)
4. **Phase 2b** — register presets (#87)
5. **Phase 3 E1-E6** — paperbanana integration (folded into v1.4)
6. **Phase 4a** — text-density warning (#91)
7. **Phase 4b** — composition primitives (#90)
8. **Phase 5a** — full-bleed scale (#88)
9. **Phase 5b** — iterate-slide skill (#89)
10. **Final** — v1.4 end-to-end dogfood + CLAUDE.md status update

For implementation details of each phase, read plan §6. Below is the atomic-step skeleton for each.

### 6.1 Phase 0 — #86 discipline hook propagation

Steps:
1. Read Claude Code hook docs via `WebFetch` (https://docs.anthropic.com/...). Check whether hooks propagate to Task subagents.
2. Run a synthetic test: dispatch a Task subagent (general-purpose, haiku) with prompt asking it to attempt `Read /tmp/test-discipline.png` and report whether it succeeded. Create the test PNG first via `python3 -c "from PIL import Image; Image.new('RGB',(10,10)).save('/tmp/test-discipline.png')"`.
3. If subagent's Read succeeded → hook does NOT propagate → design fallback (see plan §6 Phase 0).
4. If subagent's Read was blocked → hook DOES propagate → document the behaviour.
5. Implement the fallback if needed (env-var pattern, settings.local.json update).
6. Write `docs/architecture/discipline-hook-propagation.md` documenting the finding.
7. Commit: `docs: discipline hook propagation investigation (#86)` or `fix: discipline hook fallback enforcement (#86)`.
8. Update state.

Budget envelope for Phase 0: $0.00 (no cloud calls).

### 6.2 Phase 1 — #92 cloud safety filter

Steps (one atomic commit per step):
1. Add `SafetyFilterTriggeredError` and `SafetyFilterExhaustedError` exception classes in `plugins/jack-tar-cloud/src/generate_cloud_image.py`.
2. Create `plugins/jack-tar-cloud/src/safety_filter_vocab.py` with 20-entry default vocab + `SAFETY_FILTER_VOCAB_PATH` env override. See plan §6.1 for the vocab list.
3. Guard `_generate_via_nano_banana` empty-candidates path — raise `SafetyFilterTriggeredError(prompt, provider, model)` when `response.candidates` is None/empty (around line 681).
4. Guard `_generate_via_imagen` similarly.
5. Add retry-with-softening wrapper around `generate_cloud_image` dispatch — catches `SafetyFilterTriggeredError`, applies softening from vocab, retries up to 3 times, raises `SafetyFilterExhaustedError` on final failure.
6. Add `plugins/jack-tar-cloud/tests/test_safety_filter.py` — mocked empty-candidates responses for both Nano Banana + Imagen; assert retry fires, softening replaces target words, max 3 attempts.
7. Run cloud plugin tests: `cd plugins/jack-tar-cloud && python3 -m pytest -q`. Must pass.
8. Bump `plugins/jack-tar-cloud/.claude-plugin/plugin.json` 1.3.2 → 1.3.3. Update `.claude-plugin/marketplace.json` accordingly.
9. Commit: `fix(jack-tar-cloud): retry-on-empty-candidates with auto-softening (#92)`.
10. Update state.

Budget envelope for Phase 1: $0.00 (mocked-only tests).

### 6.3 Phase 2a — #93 strap_style

Steps:
1. Add `strap_style` field to brief schema at `plugins/jack-tar-superpower-bridge/src/creative_brief.py` and `plugins/jack-tar-superpower-bridge/src/schemas/talk_brief.schema.json`. Enum: `["all-caps-three-beat", "prose-sentence"]`. Default: `null` (persona chooses).
2. Update `plugins/jack-tar-superpower-bridge/agents/narrative-brief-architect.md` Section B authoring guidance with `strap_style` choice.
3. Update `plugins/jack-tar-superpower-bridge/skills/bridge-brief/SKILL.md` to note R2 dispatch awareness of strap_style.
4. Add round-trip tests + lint validation in `plugins/jack-tar-superpower-bridge/tests/`.
5. Run bridge tests. Must pass.
6. **Verification gate**: dispatch general-purpose Sonnet (`Task(subagent_type="general-purpose", model="sonnet", prompt=...)`) with the new rule inline + 3 scenarios from plan §6.2a. Capture verdict in commit body.
7. Commit: `feat(jack-tar-superpower-bridge): strap_style field for brief register (#93)`.
8. Update state.

Budget envelope for Phase 2a: $0.00 (agent dispatch only, no cloud calls).

### 6.4 Phase 2b — #87 register presets

Steps:
1. Create `plugins/jack-tar-superpower-bridge/src/registers/loader.py` — port of paperbanana's `methodology.py` venue-loader pattern. Include MIT attribution comment crediting paperbanana.
2. Create `plugins/jack-tar-superpower-bridge/src/registers/presets/` directory.
3. Create `infographic-narrative.md`, `atmospheric-photo.md`, `schematic-diagram.md`, `editorial-mixed-case.md` preset files. Each contains: palette table, typography, layout typology, default `strap_style`. See plan §6.2b for content guidance.
4. Add `preferences.register` field to brief schema. Enum: the 4 preset names + null.
5. Update brief-save lint to validate register against enum.
6. Update `narrative-brief-architect.md` Section B to use register defaults.
7. Add tests for register loading + brief integration.
8. Run bridge tests. Must pass.
9. **Verification gate**: dispatch general-purpose Sonnet with all 4 preset docs inline + 5 subject scenarios. Verdict in commit body.
10. Bump `plugins/jack-tar-superpower-bridge/.claude-plugin/plugin.json` 0.2.2 → 0.3.0. Marketplace sync.
11. Commit: `feat(jack-tar-superpower-bridge): register presets — 4 canonical registers (#87)`.
12. Update state.

Budget envelope for Phase 2b: $0.00 (agent dispatch only).

### 6.5 Phase 3 — paperbanana integration (E1-E6)

Each E sub-step is its own atomic commit.

**E1**: `academic_figure` strategy classifier.
1. Add `academic_figure` to `plugins/jack-tar-deckhand/src/schemas/strategy_map.schema.json` enum.
2. Add classifier heuristics in `plugins/jack-tar-deckhand/src/strategy_classifier.py`.
3. Tests.
4. Commit: `feat(jack-tar-deckhand): academic_figure strategy classifier (paperbanana E1)`.

**E2**: imagegen-bridge dispatch.
1. Update `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md` with new dispatch branch.
2. Wire dispatch into Python or skill orchestration.
3. Mocked tests.
4. Commit: `feat(jack-tar-deckhand): imagegen-bridge dispatch to paperbanana for academic_figure (paperbanana E2)`.

**E3**: verify-skill update.
1. Add ACADEMIC FIGURE capability row to `plugins/jack-tar-deckhand/skills/verify/SKILL.md`.
2. Helper to detect paperbanana availability.
3. Commit: `feat(jack-tar-deckhand): verify-skill detects paperbanana (paperbanana E3)`.

**E4**: persona doc updates.
1. Update `agents/narrative-architect.md`.
2. Update `agents/smartart-selector.md` (mark academic-figure for paper-quality work, but keep existing chart types for non-paper).
3. Commit: `docs(jack-tar-deckhand): persona docs for academic_figure (paperbanana E4)`.

**E5**: ADR.
1. Create `docs/architecture/paperbanana-integration.md` with the Option 4 + slim Option 2 ADR.
2. Update `CLAUDE.md` plugin table with the integration note.
3. Commit: `docs: paperbanana integration ADR (paperbanana E5)`.

**E6**: dogfood.
1. Construct a small fixture deck with one `academic_figure`-classified slide.
2. **IF paperbanana is installed locally**: run real generation, capture output. Spend budget envelope: $0 (paperbanana uses operator's API key directly).
3. **IF paperbanana NOT installed**: write a dogfood log entry noting "integration verified at contract level via E1-E3 tests; end-to-end dogfood deferred to operator with paperbanana installed". This is the documented expected fallback.
4. Log to `docs/superpowers/dogfooding/2026-05-17-paperbanana-integration.md`.
5. Bump `plugins/jack-tar-deckhand/.claude-plugin/plugin.json` 1.3.3 → 1.4.0. Marketplace sync.
6. Commit: `feat(jack-tar-deckhand): paperbanana integration v1.4.0 (paperbanana E6)`.

Budget envelope for Phase 3: $0.00–$0.50 (E6 may use 1-2 Flash 1K images for the fixture deck context — not the academic figure itself, which paperbanana renders).

### 6.6 Phase 4a — #91 text-density warning

Steps:
1. Update `plugins/jack-tar-deckhand/agents/prompt-engineer.md` with the text-density pre-render warning section.
2. **Verification gate**: dispatch general-purpose Sonnet with new rule inline + 3 prompt scenarios (8, 12, 18 strings).
3. Commit: `feat(jack-tar-deckhand): prompt-engineer text-density warning (#91)`.

Budget envelope: $0.00.

### 6.7 Phase 4b — #90 composition primitives

Steps:
1. Update `plugins/jack-tar-deckhand/agents/prompt-engineer.md` with the 5 primitives section.
2. Create `plugins/jack-tar-deckhand/src/schemas/composition_primitives.schema.json`.
3. Create `docs/architecture/composition-primitives-authoring-guide.md`.
4. **Verification gate**: dispatch general-purpose Sonnet with primitives inline + 5 subject scenarios.
5. Bump deckhand 1.4.0 → 1.4.1. Marketplace sync.
6. Commit: `feat(jack-tar-deckhand): composition primitives library (#90)`.

Budget envelope: $0.00.

### 6.8 Phase 5a — #88 full-bleed scale

Steps:
1. Add `full_bleed` to scale enum in `plugins/jack-tar-deckhand/src/schemas/strategy_map.schema.json`.
2. Update `plugins/jack-tar-deckhand/src/assembler/build_deck.js` with new branch in `buildSlide()`.
3. Update `src/assembler/build_deck.js` (synced copy).
4. Create `plugins/jack-tar-superpower-bridge/src/enrichment_ops/full_bleed.py`.
5. Add tests for both paths.
6. Run deckhand + bridge tests. Must pass.
7. **Verification gate (visual)**: build a synthetic 4-slide deck (one slide per scale: bg, content_zone, side_accent, full_bleed). Use **Imagen Fast 1K @ $0.020 each → $0.08 total** for the slide images (non-text-bearing fillers are fine). Rasterise via LibreOffice. Dispatch image-reviewer subagent. Capture verdict.
8. Bump deckhand 1.4.1 → 1.4.2.
9. Commit: `feat(jack-tar-deckhand): full_bleed image scale (#88)`.

Budget envelope: ~$0.10.

### 6.9 Phase 5b — #89 iterate-slide skill

Steps:
1. Create `plugins/jack-tar-deckhand/src/iterate_state.py` — `IterateState` dataclass with load/save. Port of paperbanana's `ResumeState`. MIT attribution.
2. Create `plugins/jack-tar-deckhand/src/iterate_loop.py` — orchestration loop with `user_feedback` threading.
3. Create `plugins/jack-tar-deckhand/skills/iterate-slide/SKILL.md`.
4. Tests with mocked regenerate-and-review.
5. Run deckhand tests. Must pass.
6. **Verification gate (visual + workflow)**: build a synthetic 3-slide deck. Use **Imagen Fast 1K @ $0.020 × 3 = $0.06** for initial generation. Run iterate-slide on slide 2 with a deliberate critique ("change colour to navy"). Slide 2 regenerates (1 more call at Flash 1K $0.067 = $0.13 total for this gate). Verify slide 1 and 3 byte-identical, slide 2 changed per critique. Dispatch image-reviewer subagent. Capture verdict.
7. Bump deckhand 1.4.2 → 1.4.3.
8. Commit: `feat(jack-tar-deckhand): iterate-slide skill (#89)`.

Budget envelope: ~$0.15.

### 6.10 Final — v1.4 end-to-end dogfood + CLAUDE.md status

Steps:
1. Build a single end-to-end deck combining: register (#87) + academic_figure (paperbanana) + full_bleed cover (#88) + iterate-slide on at least one slide (#89). Use Flash 1K throughout. **Budget envelope: ~$1.00 for the end-to-end (10-15 image calls).**
2. Run through PowerPoint Mac PDF (best-effort; if fails, fall back to LibreOffice). Dispatch image-reviewer subagent on each rasterised slide.
3. Log at `docs/superpowers/dogfooding/2026-05-17-v1.4-end-to-end.md`.
4. Update root `CLAUDE.md` "Current Status" section with the v1.4 entry. Cross-reference all closed issues + the paperbanana integration + the final plugin versions.
5. Set `state.status = "complete"`.
6. Commit: `docs: v1.4 end-to-end dogfood + status update`.

Budget envelope: ~$1.00.

**Cumulative budget projection across all phases: $1.25–$1.50, well under the $5.00 cap.**

---

## 7. VERIFICATION GATE SPECIFICATIONS

### 7.1 Agent dispatch gates (Phases 2a, 2b, 4a, 4b)

Pattern:
```
Task(
  subagent_type="general-purpose",
  model="sonnet",
  description="Verify <issue>",
  prompt="""You are verifying behaviour of the updated <rule>.
  
  [paste the new rule text verbatim]
  
  [N test scenarios]
  
  Return ONLY this JSON:
  { "scenario_1": {...}, ..., "rule_followed_correctly": <bool> }
  """
)
```

Capture the JSON verdict in the commit body. Gate passes if `rule_followed_correctly == true` AND no scenario is misclassified.

### 7.2 Visual gates (Phases 5a, 5b, final)

Pattern:
1. Generate fixture images at the cheapest viable tier (Imagen Fast for non-text, Flash 1K for text-bearing).
2. Assemble synthetic .pptx via PptxGenJS.
3. Rasterise via `soffice --headless --convert-to pdf` + `pdftoppm -r 110 -png`.
4. Dispatch `jack-tar-deckhand:image-reviewer` (haiku) on each rasterised slide with the expected-behaviour checklist.
5. Gate passes if aggregate verdict is `pass` AND no blocking issues.

DO NOT Read PNG files directly in your own context. The discipline hook blocks it; even if it didn't, you would be burning context.

---

## 8. ESCALATION — write blocker, cancel Ralph, exit

When to escalate:

- Test failure after 2 fix attempts.
- Verification gate returns `refine` or `fail` and you cannot determine why in 1 inspection.
- Budget check fails: `state.verification_spent_usd + estimated_call_cost > 4.50`.
- Design decision needed that is not resolved in plan §2 or §3.
- Git state is unexpected (merge conflict, detached HEAD, dirty tree mid-phase).
- Network error after 3 retries.
- Iteration count reaches 200.
- Any phase takes more than 15 iterations to complete.

### Escalation procedure (do ALL of these, in order)

**Step 1 — Write the visible blocker file at repo root.** This is the artefact the operator sees on morning checkin. Path: `V1.4-BLOCKER.md` (repo root, ALL CAPS for visibility).

**Step 2 — Mirror to `.ralph/v1.4-blocker.md`** so state-tooling can find it.

**Step 3 — Update state**: `state.status = "blocked"`, `state.blocker = <one-line summary>`, write atomically.

**Step 4 — Commit the blocker and state** so it survives any subsequent process state: `git add V1.4-BLOCKER.md .ralph/v1.4-blocker.md .ralph/v1.4-state.json && git commit -m "halt: v1.4 Ralph blocked — see V1.4-BLOCKER.md"`. Do NOT push.

**Step 5 — Cancel the Ralph loop** so it does not spawn further iterations:
```
Skill(skill="ralph-loop:cancel-ralph", args="")
```
If the cancel skill is not available or fails, the §5 step 2 stop check (`state.status == "blocked"` → exit) is the fallback — Ralph will exit each subsequent iteration, but cancelling is cleaner.

**Step 6 — Exit this iteration.**

### Blocker format (both `V1.4-BLOCKER.md` and `.ralph/v1.4-blocker.md`)

```markdown
# v1.4 Ralph Loop — Blocked

**STOP**: this Ralph loop has halted. Read this file to understand what to resolve before restarting.

**Time blocked**: <ISO timestamp>
**Phase**: <phase id from §6, e.g. phase_5b_iterate_slide>
**Atomic step**: <step description>
**Iteration count**: <N>
**Verification budget spent**: $<X.XX> / $5.00
**Loop cancel status**: <cancelled via ralph-loop:cancel-ralph | cancel skill unavailable, relying on §5 stop check>

## What happened

<3-5 sentences describing the situation. Be concrete. Quote error messages verbatim if applicable. Name the file:line where things went wrong.>

## What you tried

- **Attempt 1**: <description> → <outcome>
- **Attempt 2**: <description> → <outcome>
- (more attempts if any)

## What the operator needs to do

Concrete, actionable next-step. Examples of acceptable shapes:

- "Decide between option A (description) and option B (description). After deciding, update plan §<section> with the resolution and edit `.ralph/v1.4-state.json` to set `phases.<phase_id>.status = "not_started"` then restart Ralph."
- "The test at <file:line> fails because of <root cause>. Manual fix needed; once the fix lands and tests pass, set the phase status back to `not_started` and restart."
- "Verification budget is at $<X.XX> with <N> phases remaining. Either approve a higher cap (edit `state.verification_budget_usd`) and restart, or accept partial completion."

## State preservation

- **Last committed change**: `<git sha>` — `<commit message>`
- **Working tree status**: clean | dirty (files: <list>)
- **Phases completed**: <list>
- **Phases remaining**: <list>
- **State file**: `.ralph/v1.4-state.json` (do not delete; Ralph will resume from this)

## To restart Ralph (after resolution)

1. Address the blocker per "What the operator needs to do" above.
2. Edit `.ralph/v1.4-state.json`: set `status` from `"blocked"` back to `"in_progress"`, clear `blocker` to `null`.
3. Re-invoke `/ralph-loop:ralph-loop` with PROMPT.md.
4. Delete `V1.4-BLOCKER.md` and `.ralph/v1.4-blocker.md` once resolved so they don't shadow future blockers.
```

### Why cancel the loop AND set status=blocked

Belt + braces. The cancel call halts Ralph at the harness level. The status=blocked check halts at the prompt level. Either alone would work; both together protect against cancel-skill unavailability or future PROMPT.md edits that miss the §5 step 2 check.

---

## 9. STOP CONDITIONS

Ralph stops (exits the current iteration AND cancels the loop) when:

- `state.status == "complete"`: all phases done, v1.4 ready for operator review. On reaching complete, also invoke `Skill(skill="ralph-loop:cancel-ralph", args="")` to halt the loop cleanly. Write `V1.4-COMPLETE.md` at repo root summarising what shipped (mirrors the §8 visible-flag pattern but for the happy path).
- `state.status == "blocked"`: see §8 — the loop has already been cancelled and the blocker is at `V1.4-BLOCKER.md`. Any subsequent iteration (defence in depth, in case cancel failed) reads state, sees blocked, exits immediately without action.
- `state.iteration_count >= 200`: hard cap. Treat as a blocker — escalate via §8 with reason "iteration cap reached".
- `state.verification_spent_usd >= 4.50`: pre-cap halt. Treat as a blocker — escalate via §8 with reason "verification budget approaching cap".

On clean stop, leave the working branch ready for operator review. DO NOT push branches or open PRs.

### The contract is: blocked → loop ends, with a visible file at repo root the operator reads first

If you escalate, the operator MUST see `V1.4-BLOCKER.md` at root the moment they open the repo. The loop MUST NOT continue spawning iterations after a blocker. Both conditions are load-bearing — failing either erodes operator trust and wastes their morning.

---

## 10. WHEN IN DOUBT

- Re-read the plan section for the current phase.
- If the plan doesn't resolve it, escalate. Do not improvise.
- If a test passes "by accident" (you can't explain why), assume the test is wrong and escalate.
- If a verification gate verdict surprises you, escalate.
- If git rejects a commit or push, read the error carefully — never `--force` or `--admin`.

---

## 11. FIRST-ITERATION BOOTSTRAP

On the very first iteration (`state.iteration_count == 0`):

1. Create `.ralph/v1.4-state.json` with the §4 defaults if missing.
2. Create `feat/v1.4-push-and-paperbanana` branch off main if absent.
3. Verify all referenced inputs exist (plan doc, /tmp triage reports). If a /tmp file is missing because /tmp got cleaned, you may proceed but make a note in state.
4. Begin Phase 0.
5. Commit any state initialisation (state file, blocker template) with `chore: initialise v1.4 Ralph state`.

---

## 12. EXIT WITH GRACE

End every iteration with:
1. State written.
2. Either: commit made AND clean working tree, OR no code changes since last commit.
3. A one-line summary to stdout: `Iteration <N> complete — phase=<X> step=<Y> spent=$<Z>`.

### 12.1 NEVER stage ephemeral Ralph state into code commits

The files under `.ralph/agent/` and the run-pointer files at `.ralph/` are **per-iteration scratch state**. Ralph itself mutates them every iteration. If they get caught in a code commit and land empty/deleted, the next iteration recovers from nothing and the loop can spiral into `consecutive_failures` (this is exactly what killed iter 6 on 2026-05-17 — the scratchpad got committed-as-deleted in a previous iteration's broad `git add`, and recovery never converged).

**Never include in a code commit** (and never use `git add .` or `git add -A` in a Ralph iteration):

- `.ralph/agent/scratchpad.md`
- `.ralph/agent/summary.md`
- `.ralph/agent/handoff.md`
- `.ralph/agent/tasks.jsonl`
- `.ralph/agent/memories.md`
- `.ralph/agent/*.lock`
- `.ralph/loop.lock`
- `.ralph/current-events`
- `.ralph/current-loop-id`
- `.ralph/events-*.jsonl`
- `.ralph/history.jsonl`

**Always stage code commits by explicit path.** Examples:

- GOOD: `git add plugins/jack-tar-cloud/src/safety_filter_vocab.py plugins/jack-tar-cloud/.claude-plugin/plugin.json`
- BAD: `git add .`  ← sweeps in scratchpad
- BAD: `git add -A`  ← sweeps in scratchpad + lock files
- BAD: `git commit -a`  ← same problem, scoped to tracked files but still grabs scratchpad

**Verify before every commit**: run `git diff --cached --name-only` and confirm zero `.ralph/agent/` or `.ralph/loop.lock` / `.ralph/current-*` / `.ralph/events-*` / `.ralph/history.jsonl` entries appear. If any do, `git restore --staged <path>` them before committing.

The ONLY files Ralph ever commits from `.ralph/` are:

- `.ralph/v1.4-state.json` (your authoritative progress record — committed at the end of each phase)
- `.ralph/v1.4-blocker.md` (only when escalating via §8)

"Clean working tree" in §12 step 2 refers to **code changes**, not to ephemeral agent state. The agent scratchpad SHOULD remain dirty at end of iteration — that's its job. Do not "clean" it by committing.

This is the contract Ralph relies on. Honour it.

---

**You are now ready. Begin iteration 1.**
