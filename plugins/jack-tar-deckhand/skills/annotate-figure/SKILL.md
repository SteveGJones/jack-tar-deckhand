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

- **External image**: use the given path as-is. Record `source: external`. **Blank-zone variant** (issue #142, final scope item): when a `blank_zone` was requested, resolve it against the image's REAL aspect via `annotation_payload.resolve_blank_zone(requested, image_aspect)` — there is nothing to inject a directive into, but verification (step 2) and zone-preferred placement (step 3) still run: the operator may have chosen this image because it already has a clear region.
- **Generate**: transform the prompt to be LABEL-FREE — remove every quoted label directive and any "labelled/labeled X" phrasing, describe the parts that must be *visible* instead ("rudder visible at the rear below the waterline"), and append: `No text, no labels, no leader lines, no annotations of any kind.` Render via the standard local draft ladder (`local-config.json` model preferences; klein/z-image per the catalog `local_draft` role) at 1024×576 unless told otherwise. $0; the F10 gate is untouched (no paid tier is involved unless the operator later escalates the BASE image). **Blank-zone variant:** when a `blank_zone` was requested, resolve `auto` FIRST via `annotation_payload.resolve_blank_zone(requested, intended_aspect)` (1024×576 default → aspect 1.78), then append the resolved zone's directive text below to the label-free prompt, AFTER the scene description and BEFORE the no-text negative:

  | Zone | Directive text |
  |---|---|
  | `right_third` | `Compose the main subject and all scene detail within the left two-thirds of the frame. Keep the right third of the frame plain and empty — clean, uncluttered background with nothing in it.` |
  | `left_third` | `Compose the main subject and all scene detail within the right two-thirds of the frame. Keep the left third of the frame plain and empty — clean, uncluttered background with nothing in it.` |
  | `top_strip` | `Compose the main subject and all scene detail in the lower three-quarters of the frame. Keep the top of the frame plain and empty — clean open sky or flat background with nothing in it.` |
  | `bottom_strip` | `Compose the main subject and all scene detail in the upper three-quarters of the frame. Keep the bottom of the frame plain and empty — clean, plain foreground with nothing in it.` |

  No `blank_zone` requested ⇒ this is a no-op, prompt unchanged (v1 exactly).

### 2. Anchor pass (vision → structured JSON)

Dispatch `jack-tar-deckhand:image-reviewer` (or `general-purpose` for complex scenes) with the image path and this contract — labels filled in from the request:

> Return NORMALIZED coordinates (x, y as fractions of width/height, 0–1, origin top-left) for the exact point a leader line should TOUCH for each of: <label>: <what it points at>, … Also give a one-line description of the depicted subject and any orientation facts needed to sanity-check (e.g. which side is the front). Output ONLY JSON: `{"description": "...", "anchors": {"<Label>": [x, y], ...}}`

**Blank-zone variant — amended contract (BZ-10).** When step 1 resolved a `blank_zone` for this image, the SAME dispatch uses this contract instead — the enumerated output shape ITSELF grows a third key on the SAME closing "Output ONLY JSON" line, never a second appended instruction (a model obeying an earlier "Output ONLY JSON" literally would silently drop an appended field):

> […existing anchor instructions…] Additionally: the **<zone phrase>** was requested to be kept visually quiet for label placement. Judge whether that region is clear: would white label boxes placed there sit over any salient object, figure, text, or high-detail structure? Plain backgrounds, open sky, water, gentle gradients and soft texture COUNT AS CLEAR; any distinct object, subject part, or busy detail extending into the region means NOT clear. Output ONLY JSON: `{"description": "...", "anchors": {"<Label>": [x, y], ...}, "blank_zone": {"clear": true|false, "notes": "one line"}}`

Zone phrases — kept in lockstep with `annotate_figure.BLANK_ZONE_RECTS` (drift-pinned against imagegen-bridge SKILL.md, BZ-9): `right third of the frame (x > 0.67)`, `left third of the frame (x < 0.33)`, `top strip of the frame (y < 0.25)`, `bottom strip of the frame (y > 0.75)`.

Validate the response with `annotate_figure.validate_anchors` (module below); on validation failure, re-dispatch once with the error message included. `validate_anchors` already tolerates the extra `blank_zone` top-level key. **Blank-zone variant:** after validation succeeds, call `annotate_figure.parse_blank_zone_verdict` on the same parsed response — `True`, `False`, or `None` (absent/malformed, treated exactly like `False`), never raises. Carry the result to step 3. A failed or absent zone verdict never affects anchor validity — the two are independent checks.

### 3. Overlay (perfect text, deterministic)

```bash
python3 - <<'PY'
import sys; sys.path.insert(0, '<PLUGIN_ROOT>/src')
from annotate_figure import annotate
annotate('<base image>', {<label>: [x, y], ...}, '<out path>')
PY
```

Automatic occlusion-avoiding placement puts each label in the nearest margin band; pass explicit `{"anchor": [...], "label_pos": [...]}` per label only when the reviewer flags a placement problem.

**Blank-zone variant — zone-preferred overlay.** When step 2's verdict is `clear: true`, compute placements via `place_labels_in_zone(anchors, image_size, resolved_zone, font_size_pt=<bake font size>, displayed_width_in=<the full-slide constant, annotation_payload._DISPLAYED_WIDTH_IN['annotated_full_slide']>)` and pass the result to `annotate()` as explicit per-label `{"anchor": ..., "label_pos": ...}` dicts (the explicit-placement path above). `place_labels_in_zone` returns `None` when the zone lacks capacity for the label set (height, or the widest label's width) — on `clear` false/absent OR a `None` return, omit explicit placements and let `annotate()` run its standard margin-band flow, v1 exactly. No automatic re-render either way — a busy or over-capacity zone just means the labels land in the margins, same $0 cost.

### 4. Anchor-verification review (pointers only — text is axiomatic)

Dispatch the reviewer on the ANNOTATED image: "For each labeled leader line, does it touch the anatomically/semantically correct part? Leader lines are dark with a white casing halo — over dark image regions look for the casing, and zoom before declaring a leader absent. Do not review spelling (programmatic). Flag any label box occluding important content and any stray text baked into the base image." One refine loop allowed: re-query coordinates for mispointed labels (include the reviewer's correction hints), re-run the overlay. More than one failed loop → surface to the operator with the best attempt (F12 stance: reviewer verdicts advisory; the operator certifies).

### 5. Deliver

Report: output path, source (external | generated + model + seed), anchor JSON used, review verdict. In deck context, hand the annotated PNG to the assembler like any figure asset. **Blank-zone variant**: when a `blank_zone` was requested, add one line recording the outcome — `blank_zone: right_third — honoured` (zone verified clear, capacity fit) or `blank_zone: right_third — fallback (zone not clear)` / `— fallback (over capacity)` — this is `raster`/standalone mode's only audit trail (no payload exists to carry it, unlike `native`).

## Deck-native mode

Everything above is the **standalone flow**: you call `/annotate-figure` directly
and get back one labeled PNG, baked. Inside a deck build, a slide can opt into
annotation via the **strategy map** instead, and the pipeline resolves one of
three modes:

| `annotation_mode` | Meaning | Who draws the labels | Placement |
|---|---|---|---|
| `none` (default) | no annotation | — | unchanged |
| `raster` | v1 flow above — labels baked into the PNG | `annotate()` (PIL), at bridge time | **contain-fit**, not cover/stretch (see Letterbox price below); full-slide on full-slide strategies, the image zone on `composed` |
| `native` | labels drawn as real PPTX shapes over an unlabelled image | the assembler (PptxGenJS / python-pptx) | contain-fit (required for anchor validity); full-slide on full-slide strategies, the image zone on `composed` (v2.1) |

**Placement zone is derived from the slide's effective base strategy (v2.1,
`speaker_override` wins when present), never re-read from the payload at
assembly time**: `composed` → the picture-zone rect (`annotated_image_zone`,
chrome retained); every other allowed strategy → the full slide
(`annotated_full_slide`, pure figure, F2). Both assemblers make this decision
themselves; the payload's own `placement_zone` field is written to match but
is informational only.

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
    "style": { "font_size_pt": 14 },
    "show_headline": false,
    "blank_zone": "right_third"
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
- `show_headline` (boolean, default `false`, v2.1) — **native + full-slide
  strategies only.** When `true`, a top band renders the slide's OUTLINE
  headline (`slide.headline`, not a separate string — there is no
  `headline_text` override field) above a shrunk contain-fit figure. Ignored
  on `raster` mode (the schema field is `native`-only in name and in both
  assemblers' routing — a raster slide with `show_headline: true` renders
  identically to one without) and ignored on `composed` (a composed
  annotated slide already carries its own headline via its retained chrome —
  see below). Toggling this is a chrome-only change: it does NOT invalidate
  the annotation payload or trigger `/iterate-slide`'s F4 anchor-refresh
  guard, since the base image is untouched.
- Allowed base strategies for either mode: `full_bleed`, `full_render`,
  `background`, `backdrop`, `academic_figure` (full-slide, pure figure, F2 —
  no headline/body/footer, unless `show_headline` opts a headline band back
  in) and `composed` (image-zone, v2.1 — chrome RETAINED: headline, body,
  accent bars, footer logo all render as normal, and the figure fills the
  slide's picture-placeholder rect instead of the canvas; a composed
  annotated slide's own `slide_type` — `content`, `diagram`, `data_chart`,
  etc. — does not change this: EVERY composed annotated slide gets
  content-with-image chrome, regardless of `slide_type`).
  `creative_vision` and `smartart` slides cannot carry `annotation_mode` — the
  creative_vision image is the operator-certified deliverable, and SmartArt is
  a graphic, not a figure.
- `blank_zone` (optional, `left_third | right_third | top_strip |
  bottom_strip | auto`, issue #142 final scope item) — reserve a
  deliberately empty region of the BASE IMAGE for label placement instead
  of the standard margin bands. See the **Blank-zone variant** section
  below for the full contract. Applies to BOTH `native` and `raster`
  modes.

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
- **Pure figure on full-slide strategies**: a native-annotated slide on
  `full_bleed`/`full_render`/`background`/`backdrop`/`academic_figure` drops
  the headline, body_points, AND the footer logo — the annotated figure IS
  the entire slide, the same contract as `full_bleed`. This holds even when
  the underlying base strategy (e.g. `background`/`backdrop`) would
  otherwise carry a text panel. The optional `show_headline` (v2.1, above)
  opts a single headline band back in above the figure — everything else
  (body_points, footer logo) stays dropped.
- **Chrome retained on `composed` (v2.1)**: the exact opposite contract.
  Headline, body_points, accent bars, and footer logo all render exactly as
  a plain composed slide's would — the annotated figure fills the slide's
  image zone (the picture-placeholder rect in template mode, the
  `content_with_image` image zone in PptxGenJS mode) instead of the canvas.
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

**Manifest dimensions (v2.1 F-01).** The `raster` flow has no payload to
carry `image_dimensions` — the image-manifest entry is the assembler's ONLY
source for the baked PNG's native aspect when computing the contain-fit
rect. The manifest entry MUST carry a `dimensions` field (read via
`src.process_image.get_dimensions` on the FINAL baked PNG, after
`annotate()` runs), matching the standard shape every other image-manifest
entry already carries. `native` mode has the same requirement covered
independently: the payload always carries `image_dimensions` (required by
`build_annotation_payload`), and the manifest entry gains a matching
`dimensions` field too (imagegen-bridge Step 4.8) so any manifest-only
consumer stays consistent.

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

## Blank-zone variant (issue #142, final scope item)

Opt-in field: `annotation.blank_zone` (`left_third | right_third |
top_strip | bottom_strip | auto`, absent by default). It closes the
labelling loop from the other side of v2's margin-band placement: instead
of placing labels wherever the model happened to paint at the edges, it
asks the model to leave a chosen region deliberately empty, verifies the
region actually came back clear, and places labels inside it when it did.

- **Vocabulary**: `left_third` / `right_third` reserve a 33%-wide vertical
  slice; `top_strip` / `bottom_strip` reserve a 25%-tall horizontal slice
  (`annotate_figure.BLANK_ZONE_RECTS`); `auto` resolves from the image's
  aspect via `annotation_payload.resolve_blank_zone` (landscape →
  `right_third`, portrait → `bottom_strip`).
- **Best-effort, not a hard mask**: the directive (step 1) is a composition
  instruction, not a guaranteed constraint — models comply partially or not
  at all. The design assumes that.
- **Fallback guarantee**: the anchor pass (step 2) is the single source of
  truth for whether the zone actually came back clear. `clear: true` AND
  enough capacity for the whole label set (both height and width, checked
  by `place_labels_in_zone`) ⇒ labels go in the zone. Anything else — busy
  zone, unverified/malformed verdict, or capacity overflow — falls back to
  the standard v2 `place_labels` margin-band flow automatically. No block,
  no automatic re-render, no new operator gate; the whole flow stays $0
  local unless the operator separately escalates the base image.
- **Mode ownership (BZ-1)**: `native` slides are driven entirely by
  **imagegen-bridge Step 4.8** (base image, anchor pass, and payload build
  all happen there — see that SKILL.md's "Blank-zone variant" note).
  `raster` slides — and every standalone/manual invocation of this
  skill — are driven entirely by THIS flow's steps 1–3 above; the bridge
  never computes a raster placement. Same field, same semantics, two
  owners, matching the routing split that already exists for
  `annotation_mode`.
- **Audit trail**: `native` mode records the outcome in the payload's
  `blank_zone` block (`requested` / `resolved` / `verified_clear` /
  `placement`). `raster` mode has no payload — the outcome is one line in
  this flow's delivery report (step 5): `blank_zone: right_third —
  honoured` / `— fallback (zone not clear)`.

Design doc: `docs/superpowers/plans/2026-07-23-annotate-blank-zone.md`.

The 2026-07-17 benchmark (docs/spikes/2026-07-17-mlx-model-benchmark/) showed exact labels + pointer placement is the universal weakness — best local 5.8/10, cloud ceiling 8.7/10 on technical figures. This flow's PoC scored a blind 10/10 on the same rubric at $0: spelling cannot fail, and pointer accuracy became a vision-coordinate problem with a verification loop. External-image support extends the pipeline to imagery it did not generate.
