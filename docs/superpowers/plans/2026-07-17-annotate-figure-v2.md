# Implementation Plan: annotate-figure v2 — deck-native annotations (issue #142)

**Feature:** #142 v2
**Branch:** `feat/annotate-figure-v2`
**Status:** Design (implementation-ready). DESIGN ONLY — no production code in this document.
**Author:** detailed-design lead (Claude)
**Created:** 2026-07-17
**Version target:** jack-tar-deckhand `1.9.0 → 1.10.0` (marketplace lockstep)

---

## 1. Summary

v1 (PR #144) ships `src/annotate_figure.py` (a pure-PIL overlay engine:
`validate_anchors` / `place_labels` / `annotate`) and the `/annotate-figure`
skill. v1 **bakes labels into pixels** — leader lines, casing, boxes and text
are drawn onto a raster PNG. That PNG then flows through the assembler as an
ordinary image asset.

v2 adds a **deck-native** mode: when an annotated figure goes INTO a deck, the
labels become **real PowerPoint text boxes + connector lines drawn over the
image**. Editable, vector-crisp, brand-fonted. The base image is placed
unlabelled; the assembler draws the overlay from a resolved-coordinates
payload. v1's raster path is retained unchanged as an explicit mode.

Three modes, surfaced on the strategy map:

| `annotation_mode` | Meaning | Who draws labels | Assembler change |
|---|---|---|---|
| `none` (default) | no annotation | — | none |
| `raster` | v1 flow — labels baked into the PNG | `annotate()` (PIL), at bridge time | none (normal image) |
| `native` | labels as PPTX text boxes + connectors over the image | the assembler (PptxGenJS / python-pptx) | new overlay renderer |

**Key insight that shapes the whole design:** v1's `place_labels` already
resolves collision-free, occlusion-avoiding label positions in
**image-normalized 0–1 coordinates**. v2 reuses `place_labels` **server-side
in the bridge** to produce those resolved positions, serialises them to a
payload, and the assembler consumes RESOLVED coordinates — it never re-runs
placement. The engine is shared; only the final rasteriser differs (PIL pixels
vs OOXML shapes).

---

## 2. Design question 1 — the contract

### 2.1 Where the payload lives

A **dedicated per-slide file**: `<deck_dir>/annotations/slide-NN-annotations.json`.

Referenced from the slide's `image-manifest.json` entry by a new
`annotations_path` field — mirroring the existing precedent of
`creative_vision_manifest_path` on creative_vision image entries (imagegen-bridge
SKILL.md Step 4.7 post-loop integration). The strategy map holds only the
declarative **request** (`annotation_mode` + the label list + target
descriptions); the resolved coordinates live in the payload the bridge writes.

Rationale for a separate file (not inline in the strategy map or the image
manifest):
- The strategy map is authored/edited by the operator and the strategy-map
  skill — it must stay small and declarative (labels + "what it points at"),
  never carry resolved pixel geometry.
- The image-manifest entry stays lean; it points at the payload the way it
  points at the creative_vision manifest.
- The assembler already reads per-slide manifest refs and per-slide JSON — this
  is the established pattern.

### 2.2 Payload schema — `src/schemas/annotations.schema.json` (new)

```jsonc
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/annotations.json",
  "title": "SlideAnnotations",
  "type": "object",
  "required": ["slide_number", "source", "base_image_path",
               "image_dimensions", "placement_zone", "fit", "labels"],
  "properties": {
    "slide_number": {"type": "integer", "minimum": 1},
    "source": {"type": "string", "enum": ["external", "generated"]},
    "base_image_path": {"type": "string",
      "description": "UNLABELLED base image (relative to deck_dir or absolute)."},
    "image_dimensions": {
      "type": "object", "required": ["width", "height"],
      "properties": {"width": {"type": "integer"}, "height": {"type": "integer"}}
    },
    "placement_zone": {
      "type": "string",
      "enum": ["full_slide", "composed_image_zone"],
      "description": "Which zone the base image occupies. full_slide for full_bleed/full_render/background/backdrop/academic_figure; composed_image_zone for composed."
    },
    "fit": {"type": "string", "enum": ["contain"], "default": "contain",
      "description": "Native annotation ALWAYS contain-fits — see §3.1. cover would crop anchors out of frame."},
    "labels": {
      "type": "array", "minItems": 1,
      "items": {
        "type": "object",
        "required": ["text", "anchor", "label_pos"],
        "properties": {
          "text": {"type": "string", "minLength": 1},
          "anchor":    {"$ref": "#/$defs/norm_point"},
          "label_pos": {"$ref": "#/$defs/norm_point"}
        }
      }
    },
    "style": {"$ref": "#/$defs/style"}
  },
  "$defs": {
    "norm_point": {
      "type": "array", "minItems": 2, "maxItems": 2,
      "items": {"type": "number", "minimum": 0, "maximum": 1},
      "description": "[x, y] normalized to the IMAGE, 0-1, origin top-left."
    },
    "style": {
      "type": "object",
      "description": "Vector-path style in POINTS (not v1's pixels). All optional; assembler falls back to defaults derived from style-guide typography + brand palette.",
      "properties": {
        "leader_width_pt":      {"type": "number", "default": 1.5},
        "casing_width_pt":      {"type": "number", "default": 3.5},
        "casing_color":         {"type": "string", "default": "FFFFFF"},
        "leader_color":         {"type": "string", "default": "141414"},
        "dot_radius_pt":        {"type": "number", "default": 3.0},
        "box_fill":             {"type": "string", "default": "FFFFFF"},
        "box_border":           {"type": "string", "default": "141414"},
        "box_border_width_pt":  {"type": "number", "default": 1.0},
        "text_color":           {"type": "string", "default": "141414"},
        "font_face":            {"type": "string"},
        "font_size_pt":         {"type": "number", "default": 12}
      }
    }
  }
}
```

Both `anchor` and `label_pos` are image-normalized. `anchor` comes straight from
the (validated) vision pass; `label_pos` comes from `place_labels(...)`
(which already returns image-normalized `{label: {anchor, label_pos}}`). Storing
both means the assembler is a pure renderer of resolved coordinates — placement
is single-sourced and deterministic.

### 2.3 Who writes it

The **imagegen-bridge**, in a new sub-step (see §6), after the anchor pass. A
new module `src/annotation_payload.py` owns the write:

```python
# src/annotation_payload.py  (new)
def build_annotation_payload(slide_number, source, base_image_path,
                             image_dimensions, placement_zone, labels_with_targets,
                             anchors, *, style=None) -> dict:
    """anchors is the VALIDATED {label: [x,y]} from validate_anchors().
    Resolves label positions via annotate_figure.place_labels and returns a
    schema-valid payload dict. Pure — no file IO, no model calls."""
    from src.annotate_figure import place_labels
    placements = place_labels(anchors, (image_dimensions["width"],
                                         image_dimensions["height"]))
    labels = [{"text": name,
               "anchor": placements[name]["anchor"],
               "label_pos": placements[name]["label_pos"]}
              for name in anchors]
    ...  # assemble + jsonschema.validate against annotations.schema.json

def write_annotation_payload(deck_dir, slide_number, payload) -> str:
    """Atomic write to <deck_dir>/annotations/slide-NN-annotations.json
    (mkdir -p annotations/; os.replace tmp -> final, per manifest_utils.py)."""
```

`place_labels` is imported and reused verbatim — the load-bearing reuse the
task demanded. The bridge then patches the image-manifest entry
(`annotations_path`, `placement_zone`, `file_path` = the unlabelled base image)
via `manifest_utils`.

---

## 3. Design question 2 — coordinate mapping (both assembler paths)

The payload gives image-normalized `[nx, ny]`. The assembler must map to slide
inches (JS) / EMU (python-pptx). The map depends on the image's placement rect
on the slide.

### 3.1 The cover-vs-contain decision (a real deviation — flag)

Every full-slide strategy in the assembler today places its image with
`sizing: { type: 'cover' }` — `buildFullBleedSlide`, `buildFullRenderSlide`,
`buildBackgroundSlide`, `buildBackdropSlide` (build_deck.js 962–1013,
1086–1092, 1371–1382) and `_apply_full_bleed` (build_deck_template.py 122).
**`cover` crops the image** to fill the canvas. Under cover, an anchor computed
against the full image does NOT map linearly to the slide — anchors in the
cropped border are pushed off-frame, and the whole map is scaled/shifted by an
unknown crop.

**Decision: native annotation always `contain`-fits the base image.** The whole
image must be visible for the anchors to be valid. The assembler computes the
contain-fit rect of the image inside the placement zone (the exact
aspect-preserving math already in `buildContentSlide` 469–485 and
`buildDiagramSlide` 636–649), and maps normalized coordinates into THAT fitted
rect. Letterbox bands (if the image aspect ≠ zone aspect) are filled with
`palette.background`.

Consequence: a native-annotated full-slide image letterboxes when its aspect
differs from 16:9. **Mitigation:** the `/annotate-figure` skill already renders
base images at 1024×576 (16:9) by default (SKILL.md §1), so bands are nil in the
common path. This is the single biggest behavioural divergence from the
existing full-slide strategies — documented, deliberate, and the reason native
annotation is routed to its OWN builder rather than patched into the cover-based
builders.

### 3.2 Contain-fit + map formula (shared by both paths)

Given placement zone `Rz = (zx, zy, zw, zh)` and image native `(W, H)`:

```
imgRatio  = W / H
zoneRatio = zw / zh
if imgRatio > zoneRatio:        # image wider than zone -> fit to width
    fw = zw;            fh = zw / imgRatio
    fx = zx;            fy = zy + (zh - fh) / 2
else:                           # fit to height
    fh = zh;            fw = zh * imgRatio
    fx = zx + (zw - fw) / 2;    fy = zy
# fitted rect Rf = (fx, fy, fw, fh)

# map normalized (nx, ny) -> slide units
X = fx + nx * fw
Y = fy + ny * fh
```

### 3.3 Where the zone rect is known, per strategy

| Base strategy | `placement_zone` | `Rz` (JS build_deck.js) | `Rz` (template build_deck_template.py) |
|---|---|---|---|
| `full_bleed`, `full_render`, `background`, `backdrop`, `academic_figure` | `full_slide` | `(0, 0, SLIDE_W, SLIDE_H)` | `(0, 0, slide_w, slide_h)` EMU |
| `composed` (content slide w/ image) | `composed_image_zone` | `layout.content_with_image.image_zone` (default `(SLIDE_W*0.525, SLIDE_H*0.107, SLIDE_W*0.428, SLIDE_H*0.787)`, build_deck.js 463) | picture-placeholder rect from `profile_layout` |

Image native `(W, H)` comes from the payload's `image_dimensions` (the assembler
never opens the PNG — respects the discipline hook and avoids a PIL dependency
in JS). The JS assembler already reads `imageData.dimensions` for aspect fits;
the payload duplicates it so the python path has it too.

`composed` support is **optional in v2** — see Open Questions §11 (a labelled
figure in the narrow right-hand image column is cramped). The recommended v2
target set is the full-slide strategies + `academic_figure`.

---

## 4. Design question 3 — the PptxGenJS native path

Verified against `pptxgenjs@4.0.1` type defs (`types/index.d.ts`).

### 4.1 Leader lines — line shape, NOT a begin/end-point API (deviation)

**PptxGenJS 4.0.1 has no begin/end-point line API.** A `ShapeType.line`
(`'line'`, enum line 167) is drawn as a **bounding box** `(x, y, w, h)` whose
un-flipped diagonal runs top-left → bottom-right; `flipH`/`flipV` (ShapeProps,
lines 1318/1323) select which diagonal. So a leader from anchor `A=(ax,ay)` to
label-box edge `B=(bx,by)` (inches) is:

```js
const x = Math.min(ax, bx), y = Math.min(ay, by);
const w = Math.abs(bx - ax), h = Math.abs(by - ay);
// unflipped line occupies TL & BR corners; our endpoints occupy
// TL&BR when (ax<=bx) === (ay<=by), else TR&BL -> flip one axis.
const flipV = (ax <= bx) !== (ay <= by);
slide.addShape(pptx.ShapeType.line, {
  x, y, w, h, flipV,
  line: { color: leaderColor, width: leaderWidthPt,
          beginArrowType: 'none', endArrowType: 'none' },
  objectName: `annotation_leader_${n}_${i}`,
});
```

Degenerate cases: `w === 0` (vertical leader) or `h === 0` (horizontal) render
fine along the axis (flip irrelevant). If BOTH are ~0 (anchor ≈ label centre),
skip the leader entirely — matches v1's zero-length collapse
(`_segment_box_entry`, annotate_figure.py 126).

`line` options confirmed present: `width`, `dashType`, `beginArrowType`,
`endArrowType`, and `color` via `ShapeFillProps` (ShapeLineProps, 1030–1050).

### 4.2 Casing (white halo) — paired underlay line, no native option

PptxGenJS has no line-outline/casing option, so v2 mirrors v1's cartographic
casing (annotate_figure.py 368–371) with a **paired underlay**: a white line of
`casing_width_pt` drawn FIRST, then the dark leader of `leader_width_pt` on top.
Because PptxGenJS z-orders by insertion, all casing lines are added before all
dark cores (§4.4).

### 4.3 Label boxes + terminus dots

- **Box + text in one call:** `addText(text, { x, y, w, h, fill:{color:boxFill},
  line:{color:boxBorder, width:boxBorderWidthPt}, fontFace, fontSize, color:textColor,
  align:'center', valign:'middle', objectName:'annotation_label_<n>_<i>' })`.
  Box rect is sized from the text + font + padding (assembler-side; the payload
  carries only `label_pos` centre — the box is centred on the mapped `label_pos`).
- **Terminus dot:** `addShape(pptx.ShapeType.ellipse, { x, y, w, h, fill:{color:leaderColor},
  line:{type:'none'}, objectName:'annotation_dot_<n>_<i>' })`, a `2*dot_radius_pt`
  square centred on the mapped `anchor`. Preceded by a white casing ellipse
  (`dot_radius_pt + casing_extra`) for the ring, matching v1 (annotate_figure.py 477–487).

### 4.4 Z-order (insertion order)

PptxGenJS draws shapes in call order; there is no explicit z-index. Add in this
order (identical pass structure to v1's `annotate`):

1. base image (contain-fit) + letterbox background fill
2. ALL casing lines + ALL dot casing rings
3. ALL dark leader cores + ALL terminus dots
4. ALL label boxes + text (one `addText` per label — box over any leader beneath it)
5. optional headline band, footer logo, notes

### 4.5 The `objectName` lesson (Spike 1)

Every annotation shape sets **`objectName`**, never `name` — PptxGenJS 4.0.1
silently drops the `name` property (Spike 1, 2026-04-23; the pptx_native
placeholder uses `objectName` for exactly this reason, build_deck.js 1546). QA
(§7) selects annotation shapes by the `annotation_*` name prefix, so the tag
MUST survive into the OOXML.

### 4.6 The label-box-edge termination point

v1 terminates the leader at the label box edge nearest the anchor
(`_segment_box_entry`, annotate_figure.py 87–127), not the box centre, so the
line never enters the box. The assembler reuses the SAME geometry: after sizing
the label box from the text, compute the box rect in inches, then
`B = segment_box_entry(anchor_in, label_centre_in, box_rect_in)`. This helper is
pure geometry — **lift it into `annotation_payload.py` (or a shared
`annotation_geometry` helper) so both the Python template path and a small JS
port use identical logic.** (The JS assembler needs a JS re-implementation of
`_segment_box_entry`; it is ~15 lines of slab-clip — port it and pin it with a
parity test against the Python output for a few segments.)

---

## 5. Design question 4 — the python-pptx template path

### 5.1 Connectors — explicit begin/end points (cleaner than JS)

python-pptx `slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, bx, by, ex, ey)`
takes explicit begin/end EMU points — **no flip arithmetic needed** (a genuine
asymmetry with the JS path, worth noting for implementers). Set
`conn.line.color.rgb = RGBColor(...)`, `conn.line.width = Pt(...)`. Casing =
a wider white connector added first, dark connector second. Arrowheads are not
exposed by python-pptx's connector API — leaders are plain lines terminated by
the dot, exactly like v1 (no arrow). Name via `conn.name = 'annotation_leader_<n>_<i>'`
(python-pptx `name` works — the Spike 1 drop is a PptxGenJS-only bug).

### 5.2 Dots + label boxes

- Dot: `slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, w, h)`; `fill.solid()`,
  `fill.fore_color.rgb`; `line.fill.background()`. Casing oval added first.
- Label box: `tb = slide.shapes.add_textbox(x, y, w, h)`; box fill via
  `tb.fill.solid(); tb.fill.fore_color.rgb=...`; border via `tb.line.color.rgb` /
  `tb.line.width`; text via `tb.text_frame` paragraph run, `run.font.name/size/
  color.rgb/bold`. Centre with `tf.word_wrap=True`, paragraph alignment
  `PP_ALIGN.CENTER`, `tf.vertical_anchor = MSO_ANCHOR.MIDDLE`.

### 5.3 New function + placeholder constraint

New `_apply_native_annotation(slide, base_image_path, payload, slide_w, slide_h,
zone_rect_emu)` in build_deck_template.py, modelled on `_apply_full_bleed`
(98–131):

1. Strip all shapes (like full_bleed) — annotation chrome is the labels, not
   template placeholders. **Template-mode placeholder constraint:** because we
   strip placeholders, native annotation in template mode does NOT populate the
   template's title/body/picture placeholders. The base image is added as a bare
   picture (hoisted after `nvGrpSpPr`/`grpSpPr` per the existing spTree-order fix,
   build_deck_template.py 124–131) at the contain-fit rect, then connectors,
   ovals and textboxes are added AFTER it (spTree order = z-order, so they land
   on top). Optional headline can be re-added as a plain textbox if
   `slideData.headline` is wanted.
2. Contain-fit the picture inside `zone_rect_emu` (§3.2, all math in EMU via
   `Inches`).
3. Draw casing connectors → dark connectors → casing ovals → dots → label boxes
   (same z-order as §4.4).

Wire into `build_deck` (build_deck_template.py 218+) as a short-circuit mirroring
the `full_bleed` block (229–237): read `annotation_mode` from the strategy map
entry and, when `native` AND `<deck_dir>/annotations/slide-NN-annotations.json`
exists, call `_apply_native_annotation` and `continue`.

---

## 6. Design question 5 — strategy-map surfacing + bridge honouring

### 6.1 Schema diff — `strategy_map.schema.json`

Add two per-slide properties and one `allOf` conditional (mirroring the existing
creative_vision conditional at lines 135–141):

```jsonc
"annotation_mode": {
  "type": "string",
  "enum": ["none", "raster", "native"],
  "default": "none",
  "description": "Opt-in figure annotation. 'raster' bakes labels into the PNG (v1). 'native' draws labels as editable PPTX text boxes + connectors over the image. Default 'none'."
},
"annotation": {
  "type": "object",
  "required": ["labels"],
  "properties": {
    "labels": {
      "type": "array", "minItems": 1,
      "items": {
        "type": "object",
        "required": ["text", "target"],
        "properties": {
          "text":   {"type": "string", "minLength": 1,
                     "description": "Exact label string to place (perfect by construction)."},
          "target": {"type": "string", "minLength": 1,
                     "description": "What this label points at — fed to the vision anchor pass."}
        }
      }
    },
    "source_image_path": {"type": "string",
      "description": "Optional external image (no generation). Absent -> render a label-stripped base image via the funnel."},
    "style": {"type": "object",
      "description": "Optional vector-style overrides (see annotations.schema.json $defs.style)."}
  }
}
```

Conditional (added to the per-slide `allOf`, alongside the creative_vision one):

```jsonc
{
  "if": {"properties": {"annotation_mode": {"enum": ["raster", "native"]}}},
  "then": {
    "required": ["annotation"],
    "properties": {
      "strategy": {"enum": ["full_bleed", "full_render", "background",
                            "backdrop", "composed", "academic_figure"]}
    }
  },
  "else": {"not": {"required": ["annotation"]}}
}
```

This bidirectionally binds the request (mode set ⇒ `annotation` required AND
strategy restricted to image-dominant strategies) and forbids an orphan
`annotation` object when mode is `none`/absent — the exact style of the existing
creative_vision `allOf`. `creative_vision` and `smartart` are deliberately
excluded from the allowed set: creative_vision's image IS the operator-certified
deliverable (F12), and smartart is a graphic, not a figure.

### 6.2 How the conductor / bridge honour it

Read at the imagegen-bridge, per slide, from `strategy-map.json`:

- **`none` / absent** — unchanged pipeline.
- **`raster`** — bridge runs the v1 flow (label-stripped base render OR external
  image → anchor pass → `annotate()` bakes the labelled PNG). The labelled PNG
  becomes the slide's `file_path` in the image manifest. **No annotations
  payload, no assembler change** — it is an ordinary image asset. The base
  strategy renders it as it always would (cover/contain per that strategy).
- **`native`** — new bridge sub-step (below). The UNLABELLED base image is the
  slide image; the assembler draws the overlay.

**Native bridge sub-step** (new §4.8 in imagegen-bridge SKILL.md, placed after
the strategy-routing step):

1. Obtain the **unlabelled base image**: if `annotation.source_image_path` set,
   use it (`source: external`, F10-free); else render via the standard funnel
   with the label-stripped prompt transform (SKILL.md `/annotate-figure` §1 —
   drop quoted-label directives, append "No text, no labels…").
2. **Anchor pass**: dispatch `image-reviewer` / `general-purpose` with the
   structured JSON contract (annotate-figure SKILL.md §2), labels/targets from
   `annotation.labels`. `validate_anchors(response)`; one re-dispatch on failure.
3. Read the base image dimensions (`process_image.get_dimensions`).
4. `build_annotation_payload(...)` (§2.3) — resolves `label_pos` via
   `place_labels`, schema-validates.
5. `write_annotation_payload(deck_dir, slide_number, payload)` →
   `annotations/slide-NN-annotations.json`.
6. Patch the image-manifest entry: `file_path` = base image, `placement_zone`
   (`full_slide` / `composed_image_zone`), `annotations_path` =
   `annotations/slide-NN-annotations.json`, `status: generated`.
7. The **native anchor-verification review** (annotate-figure SKILL.md §4,
   pointers-only) runs AFTER assembly on the rasterised slide, OR on a
   throwaway `annotate()` raster preview of the same anchors before assembly —
   recommend the latter (cheaper, keeps the loop pre-assembly). One refine loop
   re-queries coordinates and rewrites the payload.

Assembler routing key = **presence of `annotations_path` on the image entry AND
`annotation_mode == native`** — orthogonal to the base strategy. Both assemblers
gain a branch (JS: before the strategy switch, build_deck.js ~171; python: a
short-circuit like full_bleed, build_deck_template.py ~229) that calls the new
native-annotation builder and `continue`s.

---

## 7. Design question 6 — new deck-qa checks

New module `src/qa/checks/annotation_checks.py`, three checks, wired
strategy-aware into `run_qa` (only for slides whose effective `annotation_mode
== native`). Register an `ANNOTATION_CHECKS` list in `checks/__init__.py` and
dispatch it in the per-slide loop (run_qa.py ~59) for native-annotated slides,
reading the strategy map entry + the payload file.

- **AN-01 — annotations present when contracted.** For each native-annotation
  slide, assert the assembled slide carries ≥ `len(payload.labels)` shapes named
  `annotation_label_*` AND ≥ `len(payload.labels)` shapes named
  `annotation_leader_*`. Missing ⇒ `error` (the overlay silently dropped).
- **AN-02 — label text verbatim.** The set of `annotation_label_*` textbox
  strings must equal the set of `payload.labels[].text`, character-exact. Any
  mismatch (truncation, casing drift, missing) ⇒ `error`. This is the whole
  point of the feature — text is perfect by construction, and QA proves the
  contract survived assembly.
- **AN-03 — boxes within slide bounds.** Every `annotation_label_*` shape rect
  must lie fully within `[0, slide_w] × [0, slide_h]`. Off-slide ⇒ `warning`
  (placement pushed a label off-canvas; operator should nudge `label_pos` or add
  an explicit override).

Selection is by shape name prefix — reliable because §4.5 tags every shape via
`objectName` (JS) / `name` (python-pptx). All three read `payload.labels` from
`annotations/slide-NN-annotations.json` as the source of truth for the expected
set.

(Optional, deferred: AN-04 leader-does-not-cross-sibling-box — v1 guarantees this
in image px, but vector box sizes differ from PIL px so the guarantee is only
approximate. Left for a follow-up; QA covers bounds + verbatim text now.)

---

## 8. Design question 7 — test matrix

Mirror existing patterns: `test_full_bleed_scale.py` (schema + `_apply_*` unit +
python `build_deck` OOXML + JS-subprocess OOXML, all gated on toolchain
availability) and `test_annotate_figure.py` (pure-function coverage).

### 8.1 `tests/test_annotation_payload.py` (new — payload writer + schema)
- `test_schema_valid_payload_passes` — a hand-built payload validates.
- `test_schema_rejects_out_of_range_norm_point` — anchor `[1.4, 0.2]` rejected.
- `test_schema_rejects_empty_labels` — `labels: []` rejected.
- `test_schema_requires_contain_fit` — `fit: "cover"` rejected.
- `test_build_payload_resolves_label_pos_via_place_labels` — payload
  `label_pos` equals `place_labels(anchors, dims)` output (reuse assertion).
- `test_build_payload_is_deterministic` — same inputs → identical payload.
- `test_build_payload_preserves_label_text_verbatim` — special chars / spaces.
- `test_write_payload_atomic_and_roundtrips` — file written under
  `annotations/`, reloads equal, tmp file gone (mirror manifest_utils atomicity).
- `test_build_payload_applies_style_defaults` — missing style → schema defaults.

### 8.2 `tests/test_strategy_map_annotation.py` (new — schema surfacing)
- `test_schema_accepts_annotation_mode_none_default`.
- `test_schema_accepts_native_with_annotation_on_full_bleed`.
- `test_schema_accepts_raster_with_annotation_on_academic_figure`.
- `test_schema_rejects_native_without_annotation` (conditional `then.required`).
- `test_schema_rejects_annotation_without_mode` (conditional `else.not`).
- `test_schema_rejects_native_on_creative_vision` (strategy enum in `then`).
- `test_schema_rejects_native_on_smartart`.
- `test_schema_rejects_label_missing_target`.

### 8.3 `tests/test_annotate_native_assembler.py` (new — BOTH assembler paths)

python-pptx path (no toolchain gate — always runs, like the `_apply_full_bleed`
unit tests):
- `test_apply_native_annotation_strips_chrome_then_adds_picture` — 1 picture at
  contain-fit rect; pre-existing placeholders gone.
- `test_apply_native_annotation_emits_expected_shape_counts` — N labels ⇒ N
  textboxes named `annotation_label_*`, N connectors `annotation_leader_*`, N
  ovals `annotation_dot_*`, plus casing shapes.
- `test_apply_native_annotation_label_text_is_verbatim` — each textbox text
  equals the payload label (OOXML `text_frame.text`).
- `test_apply_native_annotation_maps_anchor_into_fitted_rect` — a known anchor
  `[0.5, 0.5]` on a 16:9 image in a 16:9 zone → dot centre at zone centre
  (EMU assertion within tolerance).
- `test_apply_native_annotation_letterboxes_off_aspect_image` — 1:1 image in
  16:9 zone → fitted rect narrower than slide; anchor `[0,0]` maps to the band
  edge, not slide origin.
- `test_apply_native_annotation_z_order_labels_after_picture` — in spTree,
  every `annotation_label_*` element index > the `pic` element index.
- `test_build_deck_template_native_annotation_end_to_end` (skipif no template
  fixture) — full `build_deck` run; native slide has picture + labels, sibling
  composed slide keeps its chrome (backward-compat, mirrors full_bleed test).
- `test_build_deck_template_without_annotation_unchanged` — no
  `annotation_mode` ⇒ no annotation shapes (backward-compat).

JS path (skipif no node+pptxgenjs, mirroring `_have_node_with_pptxgenjs`):
- `test_js_assembler_native_annotation_emits_label_textboxes` — subprocess
  `build_deck.js`; native slide OOXML has N `annotation_label_*` textboxes with
  verbatim text and N `annotation_leader_*` line shapes.
- `test_js_assembler_native_annotation_objectname_survives` — asserts the
  `annotation_*` names appear in the OOXML (guards the Spike 1 `objectName`
  regression).
- `test_js_segment_box_entry_parity` — JS `_segmentBoxEntry` output matches the
  Python `_segment_box_entry` for a fixed set of segments (port-parity pin).

### 8.4 `tests/test_annotation_qa_checks.py` (new — QA)
- `test_an01_flags_missing_leader_shapes` — payload has 3 labels, slide built
  with 2 leaders ⇒ AN-01 error.
- `test_an01_passes_when_all_present`.
- `test_an02_flags_text_mismatch` — a textbox says "Ruddar" ⇒ AN-02 error naming
  the expected/actual.
- `test_an02_passes_on_exact_match`.
- `test_an03_flags_box_off_slide` — a `label_pos` mapping off-canvas ⇒ AN-03
  warning.
- `test_an03_passes_when_all_in_bounds`.
- `test_annotation_checks_skipped_for_raster_and_none` — non-native slides emit
  no AN findings.

### 8.5 Regression
- Full existing suite green (`test_full_bleed_scale.py`, `test_annotate_figure.py`
  unchanged — v1 engine untouched).

---

## 9. Design question 8 — task breakdown (Sonnet-sized)

Each task ≤ one focused PR-slice, with depends-on and a Definition of Done. All
DoD include "flake8 + pre-commit clean; touched tests green."

**Inline discipline reminder for every image-touching task prompt:** *Do not
`Read` PNG/JPG/GIF/WEBP/BMP/TIFF files directly. To verify an image, dispatch the
`jack-tar-deckhand:image-reviewer` (Haiku) or `general-purpose` (Sonnet)
subagent — they pull the image into THEIR context and return text.*

| # | Task | Depends on | DoD |
|---|---|---|---|
| T1 | `src/schemas/annotations.schema.json` (§2.2) | — | Schema parses; `test_annotation_payload.py` schema cases green. |
| T2 | `src/annotation_payload.py` — `build_annotation_payload` (reuse `place_labels`) + `write_annotation_payload` (§2.3) | T1 | Payload writer tests green; atomic write verified. |
| T3 | Strategy-map schema diff — `annotation_mode` + `annotation` + `allOf` conditional (§6.1) | — | `test_strategy_map_annotation.py` green; existing strategy-map tests green. |
| T4 | Shared geometry: lift `_segment_box_entry` into a reusable helper + a JS port `_segmentBoxEntry` with a parity test (§4.6, §8.3) | — | Parity test green. |
| T5 | python-pptx native builder `_apply_native_annotation` + `build_deck` wiring (§5) | T1,T4 | python-pptx assembler tests (§8.3) green. |
| T6 | JS native builder `buildNativeAnnotatedSlide` + `drawAnnotations` + routing branch (§3.3, §4) | T1,T4 | JS-subprocess assembler tests (§8.3) green; `objectName` survives. |
| T7 | QA `annotation_checks.py` (AN-01/02/03) + `ANNOTATION_CHECKS` registration + run_qa dispatch (§7) | T1 | `test_annotation_qa_checks.py` green. |
| T8 | imagegen-bridge SKILL.md new §4.8 native sub-step + `annotation_mode` routing note in Step 4 (§6.2) | T2 | Doc references correct module fns + payload path; verify skill unaffected. |
| T9 | `/annotate-figure` SKILL.md — add a "deck-native mode" section pointing at the strategy-map opt-in + assembler behaviour; keep v1 raster flow as-is | T8 | Skill documents all three modes. |
| T10 | Docs + version bump — plugin.json `1.9.0→1.10.0`, marketplace lockstep, plugin CLAUDE.md skill-table note + root CLAUDE.md status stanza; retrospective stub `retrospectives/142-annotate-figure-v2.md` | T1–T9 | JSON-validation CI (version match) green. |
| T11 | Release-mapping — ensure new `src/annotation_payload.py`, `schemas/annotations.schema.json`, `qa/checks/annotation_checks.py` are copied into the distributed plugin dir per `release-mapping.yaml` | T2,T5,T6,T7 | `/release-plugin` dry-run lists the new files; `plugins/` copy matches `src/`. |

Suggested sequencing: **T1+T3+T4 in parallel** (independent) → **T2** → **T5+T6+T7
in parallel** → **T8+T9** → **T10+T11**.

Note on release layout: this repo keeps a development `src/` AND distributed
copies under `plugins/jack-tar-deckhand/src/`. The target files given in the task
are already under `plugins/jack-tar-deckhand/...`, so implementers edit there;
T11 confirms the release-mapping still holds (some modules also live at repo-root
`src/`). Confirm which tree is canonical for these paths before T5/T6 (the v1
`annotate_figure.py` lives at `plugins/jack-tar-deckhand/src/` — follow that).

---

## 10. Design question 9 handling — out of scope

- **Blank-zone annotation variant** (generate the image with an intentional blank
  margin band, then place labels into guaranteed-empty space rather than over
  content) — **explicitly OUT of v2 scope.** Backlog note: file as a v3 follow-up
  on #142. It needs a prompt-side "reserve a blank right third" directive plus a
  placement mode that targets the reserved band instead of the nearest margin
  band, and a way to detect the band. Not required for deck-native labels.
- **`composed_image_zone` native annotation** — schema-allowed and mapping is
  specified (§3.3), but recommended DEFERRED to a fast-follow: the right-column
  image zone is cramped for multi-label figures. v2 ships full-slide strategies +
  academic_figure as the tested path; composed can land once the full-slide path
  is proven. (If implemented in v2, it reuses `buildNativeAnnotatedSlide` with
  the image-zone rect.)

---

## 11. Open questions (flagged, not guessed)

1. **Cover→contain divergence (§3.1).** Native annotation letterboxes non-16:9
   base images where the parent strategy would have cover-cropped. Recommended:
   contain + palette-fill bands + render bases at 16:9. Confirm the operator
   accepts letterboxing for off-aspect external images (the only case bands
   appear), or whether we should cover-crop AND remap anchors through the crop
   (more code, loses border anchors). **Recommendation: contain.**
2. **place_labels box-size mismatch.** `place_labels`' collision-free guarantee
   was computed against v1's PIL pixel box metrics; the vector path sizes boxes
   from PPTX font metrics, so no-overlap is only approximate in native mode. Ship
   as-is (margin-band separation still holds) and add AN-04 later, or have the
   bridge pass a font-metric estimate into a `place_labels` variant? **Recommend
   ship-as-is + AN-04 backlog.**
3. **Headline on native-annotation slides.** Should a native-annotated full-slide
   figure keep a headline band (like `full_render`) or be pure figure (like
   `full_bleed`)? Proposed: keep headline only if `slideData.headline` is
   non-empty AND the base strategy is not `full_bleed`. Needs operator confirm.
4. **Anchor-verification review timing (§6.2 step 7).** Pre-assembly raster
   preview vs post-assembly slide rasterisation for the pointers-only review.
   Recommend pre-assembly preview (cheaper, keeps the refine loop before OOXML).
   Confirm acceptable.
5. **Canonical source tree for new modules (§9 T11).** `annotate_figure.py` lives
   under `plugins/jack-tar-deckhand/src/`; confirm the new modules follow that
   tree (not the repo-root `src/`) and that release-mapping copies them correctly.

---

## 12. Deviations from expectation found while reading the code

- **PptxGenJS has no begin/end line API** — leaders are bbox+`flipV` (§4.1). The
  task brief anticipated "line shape with begin/end points"; 4.0.1 doesn't offer
  that. python-pptx `add_connector` DOES take begin/end points, so the two paths
  build leaders differently (§5.1) — an asymmetry implementers must know.
- **No native line casing** in either engine — v1's white-halo casing must be
  reproduced with paired underlay lines/connectors (§4.2, §5.1), exactly as the
  task's "paired underlay line like v1" fallback anticipated. There is no
  PptxGenJS line-outline option.
- **`objectName` vs `name`** (Spike 1) is load-bearing here, not incidental: QA
  selects annotation shapes by name, so the PptxGenJS `name`-drop bug would break
  AN-01/02/03 silently. Pinned by a dedicated survival test (§8.3).
- **Existing full-slide strategies all `cover`-crop** — the reason native
  annotation needs its own builder and a contain-fit, rather than a patch into
  `buildFullBleedSlide` et al. (§3.1). This is the largest structural decision.
- **`place_labels` already returns image-normalized coordinates** — so the
  server-side reuse is clean and the assembler is a pure resolved-coordinate
  renderer; no placement logic crosses into the assembler.
```
