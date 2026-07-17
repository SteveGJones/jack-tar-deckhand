---
name: annotate-figure
description: Produce a labeled figure with PERFECT text — render a label-free image locally (or take an external image) then overlay leader lines and typeset labels programmatically from vision-derived anchor coordinates. Text is correct by construction; only pointer placement is reviewed.
allowed-tools: Read, Bash(python3 *), Bash(ls *), Task
---

# Annotate Figure

Split the work between what image models do well (drawing scenes and objects) and what code does perfectly (text and lines). Never ask a diffusion model to render the labels.

Do not `Read` PNG/JPG/image files directly — all image inspection goes through the `jack-tar-deckhand:image-reviewer` or `general-purpose` subagent (issue #76 discipline).

## Inputs

- **Either** `--image <path>` — an external image supplied by the operator (photo, screenshot, existing diagram; no generation, no spend), **or** a scene description to render locally.
- A **label list**: the exact strings to place (e.g., `Mast, Sail, Hull, Rudder, Bow, Stern`) and, per label, what it should point at.

## Procedure

### 1. Source the base image

- **External image**: use the given path as-is. Record `source: external`.
- **Generate**: transform the prompt to be LABEL-FREE — remove every quoted label directive and any "labelled/labeled X" phrasing, describe the parts that must be *visible* instead ("rudder visible at the rear below the waterline"), and append: `No text, no labels, no leader lines, no annotations of any kind.` Render via the standard local draft ladder (`local-config.json` model preferences; klein/z-image per the catalog `local_draft` role) at 1024×576 unless told otherwise. $0; the F10 gate is untouched (no paid tier is involved unless the operator later escalates the BASE image).

### 2. Anchor pass (vision → structured JSON)

Dispatch `jack-tar-deckhand:image-reviewer` (or `general-purpose` for complex scenes) with the image path and this contract — labels filled in from the request:

> Return NORMALIZED coordinates (x, y as fractions of width/height, 0–1, origin top-left) for the exact point a leader line should TOUCH for each of: <label>: <what it points at>, … Also give a one-line description of the depicted subject and any orientation facts needed to sanity-check (e.g. which side is the front). Output ONLY JSON: `{"description": "...", "anchors": {"<Label>": [x, y], ...}}`

Validate the response with `annotate_figure.validate_anchors` (module below); on validation failure, re-dispatch once with the error message included.

### 3. Overlay (perfect text, deterministic)

```bash
python3 - <<'PY'
import sys; sys.path.insert(0, '<PLUGIN_ROOT>/src')
from annotate_figure import annotate
annotate('<base image>', {<label>: [x, y], ...}, '<out path>')
PY
```

Automatic occlusion-avoiding placement puts each label in the nearest margin band; pass explicit `{"anchor": [...], "label_pos": [...]}` per label only when the reviewer flags a placement problem.

### 4. Anchor-verification review (pointers only — text is axiomatic)

Dispatch the reviewer on the ANNOTATED image: "For each labeled leader line, does it touch the anatomically/semantically correct part? Leader lines are dark with a white casing halo — over dark image regions look for the casing, and zoom before declaring a leader absent. Do not review spelling (programmatic). Flag any label box occluding important content and any stray text baked into the base image." One refine loop allowed: re-query coordinates for mispointed labels (include the reviewer's correction hints), re-run the overlay. More than one failed loop → surface to the operator with the best attempt (F12 stance: reviewer verdicts advisory; the operator certifies).

### 5. Deliver

Report: output path, source (external | generated + model + seed), anchor JSON used, review verdict. In deck context, hand the annotated PNG to the assembler like any figure asset.

## Why this exists (evidence)

The 2026-07-17 benchmark (docs/spikes/2026-07-17-mlx-model-benchmark/) showed exact labels + pointer placement is the universal weakness — best local 5.8/10, cloud ceiling 8.7/10 on technical figures. This flow's PoC scored a blind 10/10 on the same rubric at $0: spelling cannot fail, and pointer accuracy became a vision-coordinate problem with a verification loop. External-image support extends the pipeline to imagery it did not generate.
