---
name: image-edit
description: Apply a targeted local edit to an existing image via mflux (MLX) — preserves everything the instruction does not name, instead of regenerating from scratch. $0, no API keys.
argument-hint: "the edit instruction" --image-paths BASE.png [REF.png ...] [--model MODEL] [--output PATH] [--seed INT] [--steps INT] [--guidance FLOAT] [--quantize N] [--lock-wait-timeout SECONDS] [--no-lock]
allowed-tools: Bash(python *), Bash(python3 *)
---

# /image-edit (jack-tar-mlx)

Apply a targeted edit to an existing image via mflux (MLX) and report the
file path. This is a **$0 local tier** — no API keys, no per-image cost.
An edit preserves everything the instruction does not name, instead of
discarding the whole image and regenerating it — useful when an operator
has already approved most of an image and only wants one thing changed.

This is a **separate skill from `/image`**, not a flag on it: `/image` is
flag-compatible with jack-tar-ollama's `/image` (a pure generation
contract), and an edit needs a base image and carries different
provenance semantics entirely. Do not try to fold edit arguments into
`/image`.

## Prerequisites

- `mflux` installed: `uv tool install --upgrade mflux`
- Weights for at least one **edit-capable** catalogued model cached
  locally — `mlx/flux2-klein-4b` (default, needs 16 GB RAM) or
  `mlx/qwen-image` (needs a 64 GB RAM edit tier — see below).
  `mlx/z-image-turbo` is **not edit-capable** (mflux ships no z-image
  edit CLI) — it cannot be used with this skill.
- Apple Silicon (mflux is MLX-based)

If you are not sure whether prerequisites are met, run
`/jack-tar-mlx:verify` first — it reports EDIT readiness per family
alongside generate readiness.

## Parse Arguments

Parse `$ARGUMENTS` for:
- **Edit instruction**: the quoted text describing what to change (required)
- **--image-paths BASE.png [REF.png ...]**: the base image to edit, optionally
  followed by one or more reference images (required, at least one path —
  the base MUST come first)
- **--model MODEL**: catalog model id — `mlx/flux2-klein-4b` (default) or
  `mlx/qwen-image` (64 GB RAM tier). `mlx/z-image-turbo` is rejected —
  not edit-capable.
- **--output PATH**: where to save the edited image (default:
  `output/YYYYMMDD-HHMMSS.png`)
- **--seed INT**: seed for reproducibility (optional — if omitted, the
  wrapper generates one and reports it; you do not need to invent one)
- **--steps INT**: inference steps (default: the model's pipeline-validated
  edit step count — 4 for flux2-klein-4b, 8 for qwen-image; you do not
  normally need to override this)
- **--guidance FLOAT**: edit strength (default **3.5** = optimal-strong).
  **Recommended range: 1.5–3.5.** 1.5 is subtle; there is a quality cliff
  between 3.5 and 6; 10 is unusable (noise, colour banding, bloom
  artefacts). Do not pass values above 6 without a specific reason.
- **--quantize N**: on-load quantization bits (3-8). Only relevant when
  the model falls back to its full-precision repo. You do not normally
  need to set this.
- **--lock-wait-timeout SECONDS**: how long to wait for the local
  single-flight locks (default: 600)
- **--no-lock**: skip the locks. Test fixtures / debug only.

**No `--width`/`--height` flags exist for this skill.** The edit ALWAYS
inherits the base image's dimensions. This is not a limitation to work
around — passing mismatched explicit dimensions to the underlying mflux
edit CLI is a confirmed reproducible hang (>10 minutes, no output). If
you need a different final size, resize as a separate post-process step
after the edit.

If no instruction or `--image-paths` is provided, stop and tell the user
what is missing.

## Documented failure modes — READ BEFORE USE

**(a) Do not use this skill to fix in-image TEXT.** A 2026-07-23 smoke
test showed the simplest possible word-for-word text correction
re-garbles the text it was trying to fix (a "NOTICE" sign edited to
correct nothing but spelling came back reading "NOBTICE") while
preserving everything else perfectly. If the feedback is "fix the
spelling of X" / "the label should read Y" / "correct the third line" —
**do not route it here**, even though the change sounds spatially small.
Use a full re-render, or `/jack-tar-deckhand:annotate-figure` for
labelled technical figures (perfect text by construction).

**(b) Reference-content leakage.** Passing a second `--image-paths`
entry as a style/mood reference can inject the REFERENCE's own subject
into the output, not just its palette or lighting — a 2026-07-23 smoke
test with a stylistically distinct reference image caused the
reference's own character to appear in the edited scene, unrequested.
If you use a reference image:
- Scope the instruction tightly, e.g. *"match the colour palette and
  lighting of the second image; do NOT add any subject from it."*
- Review the result specifically for injected elements from the
  reference that were not in the base or the instruction.
- Expect ~1.6× the wall-clock of a single-image edit.

Both failure modes are checked by the mandatory post-edit review step
below — do not skip it because the render is "just an edit."

## Locate Plugin

```bash
PLUGIN_ROOT=$(python3 -c "
from pathlib import Path
import sys, os

if os.environ.get('JACK_TAR_MLX_ROOT'):
    print(os.environ['JACK_TAR_MLX_ROOT']); sys.exit()

home = Path.home()
for base in [home / '.claude' / 'plugins' / 'cache']:
    for p in base.rglob('jack-tar-mlx/.claude-plugin/plugin.json'):
        print(str(p.parent.parent)); sys.exit()

dev = Path.cwd() / 'plugins' / 'jack-tar-mlx'
if dev.exists():
    print(str(dev)); sys.exit()

print('NOT_FOUND')
" 2>/dev/null)
if [ -z "$PLUGIN_ROOT" ] || [ "$PLUGIN_ROOT" = "NOT_FOUND" ]; then
  echo "ERROR: jack-tar-mlx plugin not found. Set JACK_TAR_MLX_ROOT or install the plugin."
  exit 1
fi
```

## Edit

```bash
python3 "$PLUGIN_ROOT/src/edit_image.py" \
  --prompt "THE EDIT INSTRUCTION" --image-paths BASE.png [REF.png ...] \
  --model "THE MODEL" --output "THE PATH" \
  [--seed SEED] [--steps STEPS] [--guidance FLOAT] [--quantize N] \
  [--lock-wait-timeout SECONDS] [--no-lock]
```

1. If exit code is 0: read the output path from the last stdout line.
   The model+repo actually used is on stderr as `MFLUX_REPO_USED=<repo>`;
   the seed that ran (whether you passed one or not) is on stderr as
   `MFLUX_SEED_USED=<n>` — capture it if you need to reproduce or chain
   further edits later.
2. If exit code is non-zero: read stderr and report the error verbatim
   — the wrapper's messages already name the exact remediation command
   (`uv tool install --upgrade mflux`, `hf download <repo>`, "not
   edit-capable", "edit base image not found", etc). Point the user at
   `/jack-tar-mlx:verify` for a full readiness report.

## Review the result

Do not `Read` the output PNG directly (image-review discipline hook).
Dispatch `jack-tar-deckhand:image-reviewer` or `general-purpose` on the
edited output, and explicitly ask it to check:
- Did the instructed change actually happen?
- Was everything OUTSIDE the instruction's scope preserved (no collateral
  drift on subjects, composition, or palette the instruction didn't
  mention)?
- If a reference image was passed: did any of the REFERENCE's own
  subject matter leak into the output?
- If the instruction touched in-image text: is the text now CORRECT
  letter-for-letter, or did it degrade? (If it degraded, this was the
  wrong channel for this feedback — re-render instead.)

## Nested lock note (issue #143/#124/#75)

This wrapper acquires the same **Ollama** single-flight lock first, then
the mlx lock, exactly like `/image`'s generate path — an edit and a
generate (either provider) correctly queue behind each other rather than
racing for the same GPU/unified-memory context. `--no-lock` skips both.

## Report Result

Report:
- The absolute file path to the edited image
- The model used (and which repo — primary or fallback — actually ran it)
- The seed that ran (`MFLUX_SEED_USED`) — needed to reproduce or chain edits
- The edit instruction used
- That this was a $0 local edit (no cost accrued)
- The image-reviewer verdict, including any flagged collateral drift or
  reference-content leakage

Do not ask follow-up questions. Report and stop.
