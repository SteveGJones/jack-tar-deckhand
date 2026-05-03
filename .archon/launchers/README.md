# `.archon/launchers/` — Workflow launcher scripts

Each script in this directory is a **per-workflow launcher**. It runs on the host (not in a container) and is responsible for:

1. **Pre-fetching GitHub artifacts** that the workflow needs, into `.archon/inputs/`.
2. **(Optional) chaining to the standard archon execution path** via `/sdlc-workflows:workflows-run`.

## Why launchers exist

Workflow containers have no GitHub access — see `.archon/README.md` for why. Launchers are the bridge: they fetch authoritative GitHub state on the host (where `gh` is available and credentialled) so the workflow has a fixed-point reference inside the sealed container.

## Script naming

`<workflow-name>.sh` — matches the `name:` field of the workflow YAML.

## Script contract

Every launcher must:

1. Be idempotent — safe to re-run before each workflow execution.
2. Fail fast on `gh` errors (issue not found, network down). Don't proceed with stale or missing inputs.
3. Write only into `.archon/inputs/` (or its own subdirs). Never modify `commands/`, `workflows/`, or `teams/`.
4. Print a summary of what was fetched, so the operator sees what state the workflow will use.

## Usage pattern

```bash
# Pre-fetch only (the operator runs the workflow separately)
bash .archon/launchers/<workflow-name>.sh

# Then:
/sdlc-workflows:workflows-run <workflow-name>
```

## Example: docs-readme-dual-route

```bash
bash .archon/launchers/docs-readme-dual-route.sh
# pre-fetches issue #62 body, EPIC #58 body
# writes:
#   .archon/inputs/issue-62-body.md
#   .archon/inputs/issue-58-body.md
```

Then run the workflow with the standard skill.

## Per-launcher runbooks

Each launcher should have a corresponding runbook in `.archon/runbooks/<workflow-name>.md` describing:

- When to dispatch the workflow (decision matrix)
- When NOT to dispatch
- Standard dispatch sequence
- What the workflow does node-by-node
- Cost and time expectations
- Failure modes seen in practice
- Maintenance notes

Existing runbooks:

- [`bsa-feature-update`](../runbooks/bsa-feature-update.md) — BSA model maintenance team for code-feature PRs

The runbook is the operational counterpart to the workflow YAML — YAML is what runs, runbook is when and why.

## Adding a new launcher

1. Create `<workflow-name>.sh` here.
2. Pattern: a `set -euo pipefail`-guarded bash script that runs `gh` commands and writes to `.archon/inputs/<artifact>.md`.
3. Update the workflow's command files to reference the pre-fetched file paths.
4. Update the workflow YAML's description to note that this launcher must run first.
5. Document any new artifact-naming patterns in `.archon/inputs/README.md`.
