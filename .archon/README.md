# `.archon/` — Containerised SDLC Workflows

This directory holds the SDLC workflow infrastructure for Archon-orchestrated container teams. See `/sdlc-workflows:workflows-setup` to install the runtime.

## Layout

| Subdir | Purpose |
|---|---|
| `workflows/` | Workflow YAML files. Each defines a DAG of nodes that run in containers. |
| `commands/` | Markdown command prompts loaded by workflow nodes. The agent inside the container reads these as its task brief. |
| `teams/` | Team manifests (`<name>.yaml`) describing which agents/skills/plugins compose each `sdlc-worker:<team>` Docker image. |
| `inputs/` | **Pre-fetched GitHub artifacts** that workflows reference as authoritative source of truth. See `inputs/README.md`. |
| `launchers/` | **Per-workflow launcher scripts** that fetch GitHub state into `inputs/` before invoking the workflow. See `launchers/README.md`. |
| `teams/.generated/` | Auto-generated per-team `CLAUDE.md` and `Dockerfile` (built by `/sdlc-workflows:deploy-team`). |
| `workflows/.generated/` | Auto-generated preprocessed workflow YAMLs (image: → bash: rewriting). |

## The pre-fetch convention

**Workflow containers have no GitHub access** — they run with `--cap-drop ALL` and no `gh` CLI. This is by design: containers are sealed, network-restricted environments.

When a workflow needs to reference GitHub state (issue bodies, PR descriptions, PR comments, EPIC scopes), the launcher script for that workflow MUST pre-fetch those artifacts into `.archon/inputs/` BEFORE the workspace is rsync'd to the temp container workspace. Inside the container, agents reference these files as authoritative.

**Naming convention for pre-fetched files:**
- `inputs/issue-NN-body.md` — issue body, plain markdown
- `inputs/issue-NN.json` — issue body + metadata (number, title, labels, author)
- `inputs/pr-NN-body.md` — PR description
- `inputs/pr-NN-comments.json` — PR comment thread
- `inputs/<other>.md` / `<other>.json` — other GitHub artifacts (releases, milestones, etc.)

Files in `inputs/` are **regenerated on every launcher run**. Never edit by hand. Treat them as cache, not source.

## Why this exists

The first run of `docs-readme-dual-route` produced README content that drifted from the canonical scenarios in issue #62. Root cause: the command file paraphrased the scenarios, and the container had no `gh` CLI to verify against the live issue. The verbatim-preservation requirement was unenforceable from inside the container.

Fix: pre-fetch authoritative state on the host (where `gh` is available), inject it into the workspace as a read-only file, and have agents reference it as the source of truth. Agents can no longer paraphrase a fact they cannot directly read — they read the file.

This pattern is reusable for all docs and review work that grounds in GitHub state.

## Running a workflow

```bash
# Step 1: launcher does the pre-fetch
bash .archon/launchers/<workflow-name>.sh

# Step 2: standard archon protocol via the wrapper skill
/sdlc-workflows:workflows-run <workflow-name>
```

Or in one shot if the launcher is configured to chain to the skill (see `launchers/README.md`).
