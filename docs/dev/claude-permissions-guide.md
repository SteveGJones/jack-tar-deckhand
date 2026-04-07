# Claude Code Permissions — Optimising the Free Loop

This guide explains how to configure Claude Code permissions in
`.claude/settings.local.json` so that the **free iteration loop** —
the Ollama draft + slide review cycle that costs nothing — runs with
the fewest possible interruptions for confirmation prompts.

## What is the "free loop"?

The Jack-Tar Deckhand pipeline has two cost regimes:

| Phase | Cost | Iteration cycle | Goal |
|---|---|---|---|
| **Draft loop** | $0 | Ollama renders → review → fix code → re-render | High iteration count, fast feedback |
| **Production** | $$ | Cloud renders → review → escalate provider/tier | Carefully gated, reviewer approves each spend |

During the draft loop you'll typically run dozens of cycles per session:
re-extract SmartArt → render with cairosvg → rasterise to PDF → split
into PNG slides → review → fix → repeat. Every confirmation prompt that
fires in the middle of that cycle breaks flow and slows iteration.

The goal of this guide: make the draft loop as close to zero-prompt as
possible, while keeping safety rails on destructive and external-impact
operations.

## How Claude Code permissions work

Permissions live in `.claude/settings.local.json` (per-project, gitignored)
or `.claude/settings.json` (per-project, committed). Each rule belongs to
one of three lists:

- **`allow`** — Claude runs the matching tool/command silently. No prompt.
- **`ask`** — Claude must request confirmation before running. You'll see
  a prompt with the exact command.
- **`deny`** — Claude refuses to run, even if you confirm. Use this for
  operations you never want Claude to attempt.

### Rule syntax

- `Tool` — matches every invocation of `Tool`. Example: `Read`
- `Bash(npm:*)` — matches any `npm ...` command (prefix match)
- `Bash(git status)` — exact match only
- `Bash(rm:*)` — matches any `rm ...`, including `rm -rf` variants
- `Skill(skill-name)` — matches a specific Skill invocation

Rules are evaluated in priority order: **deny → ask → allow**. A `deny`
match always wins.

## The three-tier model for the free loop

Group commands by their **blast radius**, not their frequency:

### Tier 1 — Allow silently (zero blast radius)

Read-only inspection, build steps, test runs, file creation under
project paths, anything that can be re-run trivially.

```json
{
  "permissions": {
    "allow": [
      "Bash(.venv/bin/python3:*)",
      "Bash(.venv/bin/pytest:*)",
      "Bash(node:*)",
      "Bash(npx:*)",
      "Bash(soffice:*)",
      "Bash(pdftoppm:*)",
      "Bash(ls:*)",
      "Bash(file:*)",
      "Bash(stat:*)",
      "Bash(du:*)",
      "Bash(diff:*)",
      "Bash(jq:*)",
      "Bash(cp:*)",
      "Bash(mkdir:*)",
      "Bash(find:*)",
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)"
    ]
  }
}
```

**Why these are safe:**
- `python3 / pytest / node / npx` execute project code in the venv;
  the worst case is a stack trace.
- `soffice / pdftoppm` only read the .pptx and write PNG/PDF outputs
  to a directory you choose.
- `cp / mkdir / find / ls / file / stat` are non-destructive filesystem
  ops. `cp` overwrites files but only at paths you specify, and Claude
  is reading/writing inside the project tree.
- `git status / diff / log / add / commit` read or stage local state.
  None of them affect the remote.

### Tier 2 — Ask first (medium blast radius, reversible)

Things that touch the local state in a destructive way but are
recoverable from git or backups.

```json
{
  "permissions": {
    "ask": [
      "Bash(rm:*)",
      "Bash(rm -rf:*)",
      "Bash(rmdir:*)",
      "Bash(git checkout --:*)",
      "Bash(git restore --:*)",
      "Bash(git clean -f:*)",
      "Bash(git branch -D:*)",
      "Bash(git commit --amend:*)",
      "Bash(brew install:*)",
      "Bash(npm uninstall:*)",
      "Bash(.venv/bin/pip uninstall:*)"
    ]
  }
}
```

**Why these need a prompt:**
- `rm / rmdir / git clean` destroys files. Even for "obviously safe"
  cleanups like temp files, you want a chance to confirm the path.
- `git checkout -- / git restore --` discards uncommitted changes.
- `git commit --amend / branch -D` rewrites or destroys history.
- Package un/installs change your environment.

### Tier 3 — Deny outright (irreversible or shared-state)

Anything Claude should never run, even with confirmation, on this
project. The user can still run them manually with `! <command>`.

```json
{
  "permissions": {
    "deny": [
      "Bash(git push --force:*)",
      "Bash(git push -f:*)",
      "Bash(git push --force-with-lease:*)",
      "Bash(git reset --hard:*)",
      "Bash(git update-ref -d:*)"
    ]
  }
}
```

**Why these are denied:**
- `push --force` rewrites the remote history. If you have collaborators,
  this can destroy their work.
- `reset --hard` blows away local changes with no recovery path.
- `update-ref -d` deletes refs.

## Free-loop checklist for Jack-Tar Deckhand

These are the exact commands the SmartArt iteration cycle uses. If your
local config covers all of these in `allow`, the free loop runs with
zero prompts:

| Phase | Command | Permission rule |
|---|---|---|
| Re-render SmartArt | `.venv/bin/python3 tmp/deck/rerender_smartart.py` | `Bash(.venv/bin/python3:*)` |
| Run tests | `.venv/bin/pytest tests/test_smartart_*.py -q` | `Bash(.venv/bin/pytest:*)` |
| Reassemble deck | `node src/assembler/build_deck.js --deck-dir tmp/deck` | `Bash(node:*)` |
| Convert to PDF | `soffice --headless --convert-to pdf --outdir tmp/deck/review-slides tmp/deck/output/presentation.pptx` | `Bash(soffice:*)` |
| Rasterise PDF | `pdftoppm -png -r 150 presentation.pdf hslide` | `Bash(pdftoppm:*)` |
| Inspect outputs | `file tmp/deck/smartart/*.png` | `Bash(file:*)` |
| Copy approved deck | `cp tmp/deck/output/presentation.pptx output/jack-tar-deckhand-smartart-demo-vN.pptx` | `Bash(cp:*)` |
| Stage and commit | `git add ... && git commit -m '...'` | `Bash(git add:*)`, `Bash(git commit:*)` |

The `pdftoppm` example matters: a previous version of the config had
`Bash(pdftoppm -png -r 100 presentation.pdf slide)` — an exact match
that broke as soon as we used `-r 150` or `-f 16 -l 16` flags. Use the
wildcard form `Bash(pdftoppm:*)`.

## How to add permissions

Three options, in order of preference:

### 1. Use the `update-config` skill

Tell Claude:

> Allow `pdftoppm` in this project's local settings.

Claude will use the `update-config` skill to read your existing settings,
add the permission, and confirm what changed. It's the safest approach
because it merges with existing rules instead of replacing them.

### 2. Edit `.claude/settings.local.json` directly

The file is JSON. Add new rules to the appropriate `allow` / `ask` /
`deny` array. Always preserve existing entries.

```json
{
  "permissions": {
    "allow": [
      "Bash(pdftoppm:*)"
    ]
  }
}
```

Claude reads this file at session start. Restart Claude Code or run
`/hooks` to pick up changes mid-session.

### 3. Approve at the prompt

When Claude asks to run a command, you'll see options:
- **Yes** — run once
- **Yes, and don't ask again for `<rule>`** — adds an `allow` rule
  permanently
- **No** — refuse this run
- **No, and tell Claude what to do differently** — refuse with a
  natural-language reason

Choosing "and don't ask again" is the fastest way to build up your
allowlist over time. But be deliberate — once a rule is in `allow`,
it's silent forever.

## Audit trail

After a long iteration session, review what got auto-approved:

```bash
git diff .claude/settings.local.json
```

If a rule looks too broad, tighten it. For example, if Claude added
`Bash(rm:*)` to `allow` during a cleanup but you'd rather keep `rm` in
the prompt path, move it to `ask`:

```json
{
  "permissions": {
    "ask": ["Bash(rm:*)"]
  }
}
```

## Common pitfalls

- **Over-broad allows.** `Bash(*)` allows every shell command. Don't.
- **Exact-match traps.** `Bash(pdftoppm -png -r 100 presentation.pdf slide)`
  matches *only* that exact command. Use prefix wildcards.
- **`cd` and shell built-ins.** `cd` is interpreted by the shell, not
  spawned as a process. It doesn't need its own permission rule.
- **Compound commands.** `Bash(cmd1 && cmd2)` is treated as a single
  command for matching. If `cmd1` matches an allow rule but `cmd2`
  doesn't, the whole thing prompts.
- **Forgetting to gitignore.** `.claude/settings.local.json` is
  per-developer state. Ensure it stays out of version control if your
  team prefers to manage permissions individually.

## Reference: Jack-Tar Deckhand recommended set

The current `.claude/settings.local.json` in this repo is a good
starting point for any deckhand-related project. It includes:

- Python venv tooling (pytest, pip, python3)
- Node tooling (node, npx, mmdc, vl2svg)
- LibreOffice + pdftoppm + rsvg-convert for PDF/SVG conversions
- Read-only git and gh CLI commands
- File inspection (ls, file, stat, du, diff, find)
- JSON/YAML processing (jq, yq)
- Brew read-only inspection
- All `rm` variants in the `ask` list
- Force-push and hard-reset variants in `deny`

If you adopt this config, the free loop should run end-to-end with
prompts only when Claude is about to delete a file or amend history.
