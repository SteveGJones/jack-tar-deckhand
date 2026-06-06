# Repo Cleanup & Stale-Branch Landing Implementation Plan

> **For agentic workers:** Steps use checkbox (`- [ ]`) syntax for tracking. This is a release-engineering / git-orchestration plan (land + triage + cleanup), not a TDD feature build — steps are concrete git/gh/test commands with expected output, not red-green cycles.

**Goal:** Land the recoverable work stranded in two stale worktree branches (token-pricing spike, phase-A release-readiness), then remove the dead worktrees and stale scratch from the repo.

**Architecture:** Three sequential steps. (1) Land existing PR #106 (token-pricing) — clean, CI-green, just needs freshening. (2) Triage the 42-commit phase-A branch into themed slices, re-landing survivors as small PRs off current `main` rather than one stale conflict-heavy merge. (3) Remove merged/landed worktrees and stale files.

**Tech Stack:** git, gh CLI, pytest (`.venv/bin/pytest`), GitHub Actions (9-job validation workflow).

**Key facts established during investigation (2026-06-02):**
- PR **#106** already open: base `main`, head `worktree-spike-actual-token-pricing`, 36 files, +4481/−171, **all 9 CI checks green** as of 2026-05-22. Branch is 51 commits behind main; local trial-merge is **clean (zero conflicts)**.
- `feat/release-readiness-phase-a`: 42 commits, **302 commits behind** main, last touched Apr 19, trial-merge shows **20+ files "changed in both"**. Work is genuinely un-landed (post-install hooks, `narrative_standalone.py`, omnibus builder all absent from main). Worktree is dirty (uncommitted `CLAUDE.md` + 2 untracked phase-e design docs).
- `feat/plugin-marketplace` worktree: fully merged to main, clean — safe to drop.
- Both token-pricing prod modules (`actual_cost_calculator.py`, `cloud_results.py`) are net-new on main.

---

## Step 1 — Land token-pricing PR #106

**Files (on branch `worktree-spike-actual-token-pricing`):**
- Review: `.claude/settings.local.json` (machine-local — should not ship in a feature PR)
- Ship: `plugins/jack-tar-cloud/src/{actual_cost_calculator,cloud_results,generate_cloud_image}.py`, `src/{actual_cost_calculator,cloud_results,budget_tracker,generate_cloud_image,render_funnel}.py`, spike docs, tools, tests

- [ ] **Step 1.1: Review the settings.local.json delta on the branch**

Run: `git diff main worktree-spike-actual-token-pricing -- .claude/settings.local.json`
Decide: if it is only local permission/allowlist noise, revert it on the branch (Step 1.2). If it grants a permission the feature genuinely needs, keep it. Default expectation: revert.

- [ ] **Step 1.2: If reverting, drop settings.local.json change from the branch**

```bash
git -C .claude/worktrees/spike-actual-token-pricing checkout main -- .claude/settings.local.json
git -C .claude/worktrees/spike-actual-token-pricing commit -m "chore: drop machine-local settings.local.json from PR" .claude/settings.local.json
```
Expected: one commit removing the settings delta. (Skip if Step 1.1 decided to keep it.)

- [ ] **Step 1.3: Freshen the branch against current main**

```bash
git -C .claude/worktrees/spike-actual-token-pricing merge origin/main
```
Expected: clean merge (local trial-merge confirmed zero conflicts). If conflicts surface, resolve, favouring main for any plugin.json/package-lock drift.

- [ ] **Step 1.4: Run the full test suite on the freshened branch**

Run: `cd .claude/worktrees/spike-actual-token-pricing && ../../../.venv/bin/pytest plugins/jack-tar-cloud/tests plugins/jack-tar-deckhand/tests tests/test_actual_cost_calculator.py tests/test_budget_tracker.py tests/test_cloud_results.py tests/test_pricing_freshness.py -q`
Expected: all pass. (Adjust the venv relative path as needed; the repo venv is at the main worktree root.)

- [ ] **Step 1.5: Push and confirm CI re-runs green**

```bash
git -C .claude/worktrees/spike-actual-token-pricing push
gh pr checks 106
```
Expected: all 9 jobs pass.

- [ ] **Step 1.6: Confirm the #113 cost-table reconciliation scope**

The spike headline is "catalog under-estimates 32%". Decide whether updating `cascade.py TIER_COSTS` (the #113 Pro 2K $0.134-vs-$0.193 gap) belongs in this PR or in follow-ups #108–111. If in-scope, make the edit + a test on the branch and re-push. If follow-up, note it in the PR body and leave for #108–111.

- [ ] **Step 1.7: Merge PR #106**

```bash
gh pr merge 106 --merge
```
Expected: merged to main via merge commit (project convention — never `--squash`).

- [ ] **Step 1.8: Remove the token-pricing worktree**

```bash
git worktree remove .claude/worktrees/spike-actual-token-pricing
git worktree prune
```
Expected: worktree gone; `git worktree list` no longer shows it. The `.claude/worktrees/` parent dir (now empty) can be removed.

---

## Step 2 — Triage phase-A into themed slices

Do **not** merge `feat/release-readiness-phase-a` wholesale (302 behind, 20+ conflict files, 5 mixed concerns). Investigate per-cluster, then re-land survivors as small PRs off current `main`.

**Cluster map (from the 42-commit log):**

| Slice | Representative commits | Files | Initial call |
|-------|------------------------|-------|--------------|
| A. Install/bootstrap infra | `fc2bc13 016bf18 a08dd15 b9d1703 11b2b50 3b19027` + fresh-install CI `6021384 367a527` | `plugins/*/hooks/post-install.sh`, `plugins/*/package-lock.json`, plugin.json manifests | Re-land fresh — high value |
| B. Narrative/notes standalone | `071b775 07d5bfa 6ad3d23 ee6cdb6` | `src/narrative_standalone.py`, `tests/test_narrative_standalone.py`, narrative-architect/speaker-notes SKILL.md | Re-land fresh — feature + tests |
| C. Omnibus SmartArt builder | `b60d006 8363720 de3b278 df3c853 0e7772e 9e7a7c6` | `tools/build_smartart_omnibus.py`, `tools/omnibus_config.json`, `tests/test_build_smartart_omnibus.py` | Re-land if still wanted |
| D. Release docs | `a7f59ef 30e80af b402a3f 52a90ba e09d117 bcd154c 41c62bf 1e2e310` | README/USER-GUIDE, install/troubleshooting, TalkBriefs, env-var doc alignment | Audit — some superseded by 302 commits |
| E. Polish/fixes | `ad7e224 67a2ee2 46f1ff9 bb4a126 5d4d391` | QA check count, example data shapes, manifest naming | Likely already drifted/fixed — probably drop |

- [ ] **Step 2.1: Per-cluster superseded-check**

For each cluster A–E, confirm whether the target files/behaviour already exist on current main (they mostly do not, per the landing check, but docs/polish clusters D/E are the drift risks). Produce a keep/rework/drop verdict per cluster. Checkpoint with operator before cutting any PR.

- [ ] **Step 2.2: Slice A — install/bootstrap infra PR**

Cherry-pick cluster A commits onto a fresh `feat/plugin-post-install-hooks` branch off main. Resolve package-lock/plugin.json conflicts favouring current main's versions. Run `.venv/bin/pytest` + the fresh-install CI sim. Open PR → base main. Merge when green.

- [ ] **Step 2.3: Slice B — narrative standalone PR**

Cherry-pick cluster B onto `feat/narrative-standalone` off main. Run `.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_narrative_standalone.py`. Open PR → base main. Merge when green.

- [ ] **Step 2.4: Slice C — omnibus builder (operator-gated)**

Confirm with operator the omnibus dev tool is still wanted. If yes, cherry-pick cluster C onto `feat/smartart-omnibus-builder` off main, run `tests/test_build_smartart_omnibus.py`, open PR. If no, skip.

- [ ] **Step 2.5: Slices D + E — audit then re-land survivors**

Diff each doc/polish commit against current main. Re-land only the changes that are still accurate (env-var alignment, deck-conductor invocation fix likely survive; version bumps + test-count docs likely superseded). Bundle survivors into one `docs/release-readiness-survivors` PR. Drop the rest.

- [ ] **Step 2.6: Capture or discard the 2 untracked phase-e design docs**

`docs/superpowers/plans/2026-04-18-phase-e-release-fixes.md` + `.../specs/2026-04-18-phase-e-release-fixes-design.md` live only in the dirty phase-a worktree. If they have forward value, copy into `docs/` on a branch and commit; else note and discard.

- [ ] **Step 2.7: Remove the phase-a worktree once triage is complete**

```bash
git worktree remove --force .worktrees/phase-a-bootstrap   # --force: worktree is intentionally dirty post-triage
git branch -D feat/release-readiness-phase-a               # only after all survivors are re-landed
git worktree prune
```
Expected: worktree + stale branch gone. Do NOT run until Steps 2.2–2.6 have salvaged everything wanted.

---

## Step 3 — Worktree / disk / file cleanup

- [ ] **Step 3.1: Remove the fully-merged plugin-marketplace worktree**

```bash
git worktree remove .worktrees/plugin-marketplace
git worktree prune
```
Expected: gone (branch `feat/plugin-marketplace` is fully merged to main — safe).

- [ ] **Step 3.2: Delete the stale Ralph task spec**

```bash
rm .claude/ralph-task-creative-vision-ga.md
```
Expected: removed (#113 GA work has landed; the task spec is dead).

- [ ] **Step 3.3: Final state check**

Run: `git worktree list && git status --porcelain && du -sh .worktrees .claude/worktrees 2>/dev/null`
Expected: only the main worktree (+ any in-flight Step 2 branches) remain; no stranded `.worktrees/` or `.claude/worktrees/` clutter.

---

## Self-Review

- **Spec coverage:** Step 1 = token-pricing (PR #106). Step 2 = phase-A triage (all 5 clusters + dirty docs + worktree removal). Step 3 = remaining worktrees + ralph file + final check. The earlier `output/`+`tmp/` cleanup is already done (commit `fdc6368`). Covered.
- **Sequencing risk:** Step 2.7 (remove phase-a worktree) is explicitly gated behind 2.2–2.6 so no unmerged work is lost. Step 1.8 / 3.1 worktree removals are only for merged/landed branches.
- **Reversibility:** No `git branch -D` of an unmerged branch until its work is re-landed. PR merges use `--merge` per project convention. `--force` worktree removal is only used on phase-a *after* salvage.
