# `.archon/inputs/` — Pre-fetched GitHub artifacts

Files in this directory are **authoritative source of truth** for workflow agents that cannot access GitHub directly (no network, no `gh` CLI).

## How files get here

Launcher scripts in `.archon/launchers/` fetch GitHub state via `gh` (which IS available on the host) and write the results here. Containers see these files via the workspace rsync.

## Naming convention

| File | Source command | Used by |
|---|---|---|
| `issue-NN-body.md` | `gh issue view NN --json body -q .body` | docs workflows that reference issue scope |
| `issue-NN.json` | `gh issue view NN --json number,title,body,labels,author,state` | workflows that need metadata (labels, status) |
| `pr-NN-body.md` | `gh pr view NN --json body -q .body` | review workflows |
| `pr-NN-comments.json` | `gh pr view NN --json comments` | review-after-feedback workflows |
| `epic-NN-children.json` | `gh issue list --search "in:body #NN" --json number,title,state` | EPIC-tracking docs |

If you need a new artifact type, add the launcher pattern to a launcher script and document the naming here.

## Rules

1. **Never edit files in this directory by hand.** They are cache, regenerated on every launcher run.
2. **Don't commit them to main.** Add `.archon/inputs/*` to `.gitignore`. The launcher refreshes them before each run, so committed copies will go stale.
3. **Workflow agents must reference these files by exact path.** Not `gh issue view N`, not `gh pr view N`. The agents have no `gh` and no network — they read the file or fail.

## What's currently here

This directory is populated by launcher runs. Empty between runs is normal.

```bash
ls -la .archon/inputs/
```

## Why workflows can't use `gh` directly

Containers run with `--cap-drop ALL --security-opt no-new-privileges` and no GitHub credentials mounted. This is a security boundary: a prompt-injection inside the container should not be able to read or modify your GitHub state. The launcher pattern keeps GitHub access on the trusted host where you control the credentials.
