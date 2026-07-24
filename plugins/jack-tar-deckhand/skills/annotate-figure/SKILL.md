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

## Deck-native mode

Everything above is the **standalone flow**: you call `/annotate-figure` directly
and get back one labeled PNG, baked. Inside a deck build, a slide can opt into
annotation via the **strategy map** instead, and the pipeline resolves one of
three modes:

| `annotation_mode` | Meaning | Who draws the labels | Placement on full-slide strategies |
|---|---|---|---|
| `none` (default) | no annotation | — | unchanged |
| `raster` | v1 flow above — labels baked into the PNG | `annotate()` (PIL), at bridge time | **contain-fit**, not cover/stretch (see Letterbox price below) |
| `native` | labels drawn as real PPTX shapes over an unlabelled image | the assembler (PptxGenJS / python-pptx) | contain-fit (required for anchor validity) |

### Opting in on the strategy map

A slide requests annotation by adding two fields to its strategy-map entry:

```jsonc
{
  "slide_number": 4,
  "strategy": "full_bleed",
  "annotation_mode": "native",
  "annotation": {
    "labels": [
      {"text": "Mast", "target": "the vertical spar amidships"},
      {"text": "Rudder", "target": "the steering blade at the stern, below the waterline"}
    ],
    "source_image_path": "optional/external/image.png",
    "style": { "font_size_pt": 14 }
  }
}
```

- `annotation_mode` is `none | raster | native` (default `none`). Setting it to
  `raster` or `native` requires the sibling `annotation` object; `annotation`
  without a mode, or `annotation_mode: none` with an `annotation` object, both
  fail schema validation — the request is bidirectional, never implicit.
- `annotation.labels[]` is the same `{text, target}` pairing as the Inputs
  section above — `text` is the exact string placed, `target` feeds the vision
  anchor pass.
- `source_image_path` is optional — omit it to render a label-free base image
  through the standard funnel (step 1 above); set it to skip generation and
  annotate an operator-supplied image (`source: external`), exactly as in the
  standalone flow.
- `style` optionally overrides the vector-style defaults (leader width, colors,
  font size, …) — see `src/schemas/annotations.schema.json` for the full field
  list. Only `native` mode reads `style`; `raster` mode uses `annotate()`'s
  existing PIL styling.
- Allowed base strategies for either mode: `full_bleed`, `full_render`,
  `background`, `backdrop`, `academic_figure` (full-slide) — `composed`
  (image-zone) is schema-allowed but not yet wired through the assemblers.
  `creative_vision` and `smartart` slides cannot carry `annotation_mode` — the
  creative_vision image is the operator-certified deliverable, and SmartArt is
  a graphic, not a figure.

The imagegen-bridge is what actually reads this and drives generation +
anchoring — see **imagegen-bridge SKILL.md Step 4.8** ("native sub-step") for
the bridge-side procedure (obtain unlabelled base image → anchor pass →
resolve label positions → write the `annotations/slide-NN-annotations.json`
payload → append the image-manifest entry → throwaway-raster preview review
before assembly). This skill document describes what the modes MEAN; Step 4.8
describes who drives them.

### What `native` mode does differently

`native` never bakes a pixel. The base image goes into the deck **unlabelled**,
and the assembler — PptxGenJS or python-pptx, whichever path is building the
deck — draws the overlay as real PowerPoint objects from the bridge's resolved
coordinates:

- **Real, editable, brand-fonted shapes**: each label is a text box
  (`annotation_label_*`), each pointer is a leader line with a white casing
  halo (`annotation_leader_*` / `annotation_casing_*`), each anchor is a
  terminus dot with its own casing ring (`annotation_dot_*` /
  `annotation_dotring_*`). The operator can click into any of these in
  PowerPoint after delivery and edit the text, move a label, or restyle a
  leader — none of that is possible with a baked raster.
- **Pure figure**: a native-annotated slide drops the headline, body_points,
  AND the footer logo — the annotated figure IS the entire slide, the same
  contract as `full_bleed`. This holds even when the underlying base strategy
  (e.g. `background`/`backdrop`) would otherwise carry a text panel. A
  headline opt-in is a possible fast-follow, not part of this flow today.
- **Contain-fit, never cover-crop or stretch**: the assembler fits the base
  image inside its placement zone preserving aspect (the same box-fit math
  used for content/diagram image zones), then maps the bridge's
  image-normalized anchor/label coordinates into that fitted rect. This is
  required for correctness, not just aesthetics — cover-cropping a full-slide
  image (today's default for `full_bleed`/`full_render`/`background`/`backdrop`)
  pushes anchors in the cropped border off-frame entirely, and stretching (the
  template-mode default) distorts the figure and skews the coordinate map.

### The letterbox price (both `native` and `raster`)

Contain-fit means a base image whose aspect ratio isn't 16:9 shows background
bands on two sides of the slide. This applies to **both** deck-native modes:

- `native` needs contain-fit so normalized anchors land on the correct pixel
  of the visible image.
- `raster` (v1's baked-PNG flow) ALSO now contain-fits on full-slide
  strategies — cover-cropping a baked PNG would crop the margin-band labels
  themselves off the slide, and stretching would distort the typeset label
  text. Same fix, same reason.

Base images rendered by this skill's step 1 default to 1024×576 (16:9), so
bands are nil for the generated path. **External images of arbitrary aspect
WILL letterbox** on either mode — this is the accepted cost of keeping every
anchor (and every baked label) on-slide and undistorted, rather than silently
cropping or distorting.

### Anchor-pass failure — the three-way choice (never silent)

The standalone flow (step 2 above) already re-dispatches once on a validation
failure. In deck-native mode, if that re-dispatch ALSO fails, the bridge does
**not** fall through to an unlabeled figure automatically. It surfaces an
explicit three-way choice to the operator:

1. **Retry** — a fresh anchor-pass dispatch, optionally escalated to a
   stronger model tier (e.g. Sonnet instead of Haiku).
2. **Fall back to raster with manual anchors** — the operator supplies
   `{label: [x, y]}` coordinates by hand and the v1 `annotate()` flow (this
   skill's step 3) bakes them into the PNG.
3. **Ship unlabeled** — the plain base image goes into the deck as-is, no
   overlay, no baked labels.

Whichever choice is made, the manifest entry's status is set to at minimum
`accepted_with_issues` and the failure is recorded in `review_summary` — the
degradation is always operator-acknowledged, never accidental. Deck-QA's AN-01
check independently errors if a `native`-contracted slide reaches assembly
with no annotations payload at all, so a silent drop cannot pass QA even if
the three-way prompt were somehow skipped.



The 2026-07-17 benchmark (docs/spikes/2026-07-17-mlx-model-benchmark/) showed exact labels + pointer placement is the universal weakness — best local 5.8/10, cloud ceiling 8.7/10 on technical figures. This flow's PoC scored a blind 10/10 on the same rubric at $0: spelling cannot fail, and pointer accuracy became a vision-coordinate problem with a verification loop. External-image support extends the pipeline to imagery it did not generate.
