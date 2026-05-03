# Runbook — `bsa-feature-update`

**Workflow:** `.archon/workflows/bsa-feature-update.yaml`
**Team:** `.archon/teams/bsa-team.yaml` → `sdlc-worker:bsa-team`
**Launcher:** `.archon/launchers/bsa-feature-update.sh`
**Pattern:** `bsa-plan → bsa-draft → bsa-validate → bsa-review → bsa-synthesise`

## When to dispatch this workflow

Dispatch the `bsa-team` whenever a code-feature PR changes any of the following architectural surfaces:

| Change in code | Should the BSA model also change? |
|---|---|
| New service or capability added | **Yes** — new `services` entry, new interactions, possibly new persona |
| Existing service contract changed (new field, new return shape, new error) | **Yes** — modify `interactions[i].contract` |
| New AI persona or change to an existing persona's authority/scope | **Yes** — new or modified `aiPersonas` entry |
| New external dependency (SDK, API, library) added or version-pinned | **Yes** — new `dependencyRegister` entry |
| Cross-domain SOP added or modified | **Yes** — new or modified `crossDomainSopRegister` entry |
| Plugin marketplace version bumped because of architectural change | **Yes** — `bsaVersion` bump |
| Pure refactor with no contract change | **No** — code-only PR |
| Bug fix that doesn't change the contract | **No** |
| Test additions only | **No** |
| Doc additions only | **No** |

If unsure, run the workflow anyway — `bsa-validate` and `bsa-review` will return a no-change verdict if nothing actually moved at the architectural level.

## When NOT to dispatch

- The PR is a hotfix or doc-only change.
- The PR is for an EPIC that has multiple in-flight child PRs and you want to land all BSA changes in one consolidated update — instead, dispatch once per EPIC after the last child child merges.
- The PR is for a spike or experiment that may be reverted — wait for the design to land in main first.

## Standard dispatch sequence

```
# 1. From the FEATURE BRANCH worktree (e.g. ../jack-tar-deckhand-resolution)
cd <worktree>

# 2. Pre-fetch inputs (issue body, diff, spec, plan, dogfood, canonical model snapshot)
bash .archon/launchers/bsa-feature-update.sh <issue-or-pr-ref> [<base-branch>]
#   defaults: base-branch=main
#   example:  bash .archon/launchers/bsa-feature-update.sh 59 main

# 3. Run the workflow (background; ~20-25 min wall time)
/sdlc-workflows:workflows-run bsa-feature-update

# 4. Wait for completion. Artefacts land in the temp workspace at:
#       /var/folders/.../sdlc-bsa-XXXXXX/
#    with commits on a fresh seed git, not on the feature branch directly.

# 5. Review the synthesis report:
#       <workspace>/reports/bsa-synthesis/findings.md

# 6. If GO, cherry-pick the BSA commits onto the feature branch:
#       (Use the standard git format-patch + git apply --index pattern;
#        the workflows-run skill handles this automatically as option 1.)

# 7. Push the feature branch and (re)open the PR with BSA + code in lockstep.
```

## What the workflow does (per node)

| Node | Model | What it does | Output |
|---|---|---|---|
| `bsa-plan` | Opus 4.7 | Reads diff + spec + plan + dogfood + current canonical model. Identifies which architectural surfaces moved. Produces a precise edit plan. | `reports/bsa-plan/plan.md` |
| `bsa-draft` | Sonnet 4.6 | Applies the canonical-model JSON edits, arch-doc updates, and `BSA Architecture` line bump in `CLAUDE.md`. | `reports/bsa-draft/changes.md` + actual file edits |
| `bsa-validate` | Sonnet 4.6 | Schema check, JSON parse, cross-reference between CLAUDE.md and canonical model, diff scope check. Deterministic pass/fail. | `reports/bsa-validate/findings.md` |
| `bsa-review` | Opus 4.7 | Methodology compliance (single source of truth, version semantics, dependency register, WHAT/HOW separation, cross-domain SOP). Architectural soundness. Forward consistency vs spec/dogfood. | `reports/bsa-review/findings.md` |
| `bsa-synthesise` | Sonnet 4.6 | Decision-ready summary for speaker review. GO/REVISE/STOP recommendation. | `reports/bsa-synthesis/findings.md` |

## Inputs the launcher pre-fetches

| File | Source | Purpose |
|---|---|---|
| `.archon/inputs/issue-NN-body.md` | `gh issue view NN` | Authoritative work-item description |
| `.archon/inputs/issue-NN.json` | `gh issue view NN --json …` | Metadata (labels, status, author) |
| `.archon/inputs/feature-pr-diff.txt` | `git diff main...HEAD --stat` + full diff | Authoritative source of what code changed |
| `.archon/inputs/feature-commits.txt` | `git log --reverse main...HEAD` | Commit-by-commit narrative |
| `.archon/inputs/feature-spec.md` | first `docs/superpowers/specs/*.md` in diff | Design intent |
| `.archon/inputs/feature-plan.md` | first `docs/superpowers/plans/*.md` in diff | Implementation plan |
| `.archon/inputs/feature-dogfood.md` | first `docs/superpowers/dogfooding/*.md` in diff | Smoke-test findings (often surfaces architectural reality) |
| `.archon/inputs/canonical-model-snapshot.json` | copy of `.bsa/models/jack-tar-deckhand.json` | Pre-edit baseline for diff comparison |

The container has no `gh` CLI, no network — these pre-fetched files are the agents' authoritative source of truth. Same convention as the `docs-team` workflow.

## Cherry-pick decision for the BSA commits

The workflow runs in a temp workspace with a fresh git init. After completion, the `workflows-run` skill (or the manual cherry-pick pattern) replays the BSA commits onto the feature branch.

If the synthesis verdict is GO, cherry-pick all BSA commits (typically 5: bsa-plan, bsa-draft, bsa-validate, bsa-review, bsa-synthesise) onto the feature branch. They land alongside the code commits in the same PR.

If the verdict is REVISE, address the review findings (re-edit the canonical model, re-run validate + review locally, or re-dispatch the workflow with `--resume`). Do not cherry-pick yet.

If the verdict is STOP, drop the workspace and re-plan. This usually means the architectural impact is bigger than the workflow assumed and needs a real design conversation.

## Cost expectations

Per run (typical, no escalation):
- bsa-plan: ~3-5 min, Opus, ~$1-2
- bsa-draft: ~4-6 min, Sonnet, ~$0.5-1.5
- bsa-validate: ~2-3 min, Sonnet, ~$0.3-0.6
- bsa-review: ~4-6 min, Opus, ~$1-2
- bsa-synthesise: ~2-3 min, Sonnet, ~$0.3-0.6

**Total: ~$3-7 per run, ~20-25 min wall time.** Budget caps in the workflow YAML are set generously ($5 per node, $19 total) for spiral protection. Real spend tracks the lower end.

## Failure modes seen

- **Container has no `gh` CLI.** This is by design — the launcher pre-fetches issue/PR data into `.archon/inputs/`. Agents read those files, not GitHub.
- **Container has no network egress.** Same reason. If you find yourself wanting an agent to `curl` something, the right answer is to extend the launcher to pre-fetch it.
- **Default branch detection failure on workflow start.** Archon emits a warning when the temp workspace's git has no `origin/HEAD` — this is harmless. The workflow proceeds with `--no-worktree` flag.
- **Canonical model JSON parse fail post-draft.** `bsa-validate` catches this and returns FAIL. Re-dispatch the draft node with the validate findings as additional input, or fix manually.
- **Methodology drift between canonical model and CLAUDE.md `BSA Architecture` line.** `bsa-validate`'s cross-reference check catches this. Both must be bumped together.

## Related runbooks

- (none yet — this is the first containerised non-docs team workflow)

## Related issues

- [#58](https://github.com/SteveGJones/jack-tar-deckhand/issues/58) — Cloud resolution EPIC; the work that prompted creation of this team
- [#59](https://github.com/SteveGJones/jack-tar-deckhand/issues/59) — First feature to be processed by this workflow
- [#64](https://github.com/SteveGJones/jack-tar-deckhand/issues/64) — Plan-template improvement to default-include this workflow as a phase

## Maintenance

- The `bsa-team` Docker image is built from `.archon/teams/bsa-team.yaml`. Rebuild via `/sdlc-workflows:deploy-team --name bsa-team` whenever the manifest changes (new agents added, new context files, version bumps).
- The workflow YAML uses `claude-opus-4-7` and `claude-sonnet-4-6` model IDs. When newer model IDs supersede these, bump the workflow YAML — not urgent but good hygiene.
- The launcher script (`bsa-feature-update.sh`) hardcodes the spec/plan/dogfood file path patterns. If the project moves these directories, update the script's `grep -E` patterns.
