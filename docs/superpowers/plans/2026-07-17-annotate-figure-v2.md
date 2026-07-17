# Implementation Plan: annotate-figure v2 — deck-native annotations (issue #142)

**Feature:** #142 v2
**Branch:** `feat/annotate-figure-v2`
**Status:** Design (implementation-ready). Revised per adversarial review — see §13
"Design review disposition". DESIGN ONLY — no production code in this document.
**Author:** detailed-design lead (Claude)
**Created:** 2026-07-17 (rev 2, same day)
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
payload. v1's raster path is retained as an explicit mode (with one assembly
change — see F11 note in §3.1: annotated rasters contain-fit, never cover-crop).

Three modes, surfaced on the strategy map:

| `annotation_mode` | Meaning | Who draws labels | Assembler change |
|---|---|---|---|
| `none` (default) | no annotation | — | none |
| `raster` | v1 flow — labels baked into the PNG | `annotate()` (PIL), at bridge time | contain-fit routing on full-slide strategies (§3.1) |
| `native` | labels as PPTX text boxes + connectors over the image | the assembler (PptxGenJS / python-pptx) | new overlay renderer |

**Key insight that shapes the whole design:** v1's `place_labels` already
resolves collision-free, occlusion-avoiding label positions in
**image-normalized 0–1 coordinates**. v2 reuses `place_labels` **server-side
in the bridge** to produce those resolved positions, serialises them to a
payload, and the assembler consumes RESOLVED coordinates — it never re-runs
placement. The engine is shared; only the final rasteriser differs (PIL pixels
vs OOXML shapes).

**Native mode is PURE FIGURE** (review ruling F2): like `full_bleed`, a
native-annotated slide drops the headline AND body_points — the annotated
figure IS the slide. A headline opt-in is a fast-follow, not v2.

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
  "required": ["slide_number", "source", "base_image_path", "base_image_hash",
               "image_dimensions", "placement_zone", "fit", "labels", "style"],
  "properties": {
    "slide_number": {"type": "integer", "minimum": 1},
    "source": {"type": "string", "enum": ["external", "generated"]},
    "base_image_path": {"type": "string",
      "description": "UNLABELLED base image (relative to deck_dir or absolute)."},
    "base_image_hash": {"type": "string",
      "description": "sha256 content hash of the base image at payload-build time (process_image.compute_content_hash). Invalidation contract (F4): the assembler and AN-01 verify this against the on-disk image; on mismatch the overlay is REFUSED with a warning — anchors are only valid for the exact image they were derived from."},
    "image_dimensions": {
      "type": "object", "required": ["width", "height"],
      "properties": {"width":  {"type": "integer", "minimum": 1},
                     "height": {"type": "integer", "minimum": 1}}
    },
    "placement_zone": {
      "type": "string",
      "enum": ["annotated_full_slide", "annotated_image_zone"],
      "description": "Which zone the base image occupies. annotated_full_slide for full_bleed/full_render/background/backdrop/academic_figure; annotated_image_zone for composed. Values are deliberately DISTINCT from the image-manifest placement_zone vocabulary already used by Step 4.7 ('full_bleed') and element flows ('background') — no collision (F8)."
    },
    "fit": {"type": "string", "enum": ["contain"],
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
      "description": "Vector-path style in POINTS (not v1's pixels). NO schema defaults (F9): build_annotation_payload fills every field in code, so payloads on disk are always fully explicit and the assembler never guesses.",
      "required": ["leader_width_pt", "casing_width_pt", "casing_color",
                   "leader_color", "dot_radius_pt", "box_fill", "box_border",
                   "box_border_width_pt", "text_color", "font_face",
                   "font_size_pt"],
      "properties": {
        "leader_width_pt":      {"type": "number"},
        "casing_width_pt":      {"type": "number"},
        "casing_color":         {"type": "string"},
        "leader_color":         {"type": "string"},
        "dot_radius_pt":        {"type": "number"},
        "box_fill":             {"type": "string"},
        "box_border":           {"type": "string"},
        "box_border_width_pt":  {"type": "number"},
        "text_color":           {"type": "string"},
        "font_face":            {"type": "string"},
        "font_size_pt":         {"type": "number"}
      }
    }
  }
}
```

**Style defaults (applied in `build_annotation_payload` code, F9):**
`leader_width_pt` 1.5, `casing_width_pt` 3.5, `casing_color` FFFFFF,
`leader_color` 141414, `dot_radius_pt` 3.0, `box_fill` FFFFFF, `box_border`
141414, `box_border_width_pt` 1.0, `text_color` 141414, `font_face` from the
style guide's body font, **`font_size_pt` 18** — matching the deck-qa AP-02
minimum-font-size floor (F3d). Smaller sizes are allowed ONLY via an explicit
`annotation.style.font_size_pt` override on the strategy map; when the operator
overrides below 18pt, annotation label shapes are exempt from AP-02 (the
exemption is scoped to `annotation_label_*`-named shapes and documented in the
QA check — §7).

Both `anchor` and `label_pos` are image-normalized. `anchor` comes straight from
the (validated) vision pass; `label_pos` comes from `place_labels(...)`
(which already returns image-normalized `{label: {anchor, label_pos}}`). Storing
both means the assembler is a pure renderer of resolved coordinates — placement
is single-sourced and deterministic.

### 2.3 Who writes it

The **imagegen-bridge**, in a new sub-step (see §6), after the anchor pass. A
new module `src/annotation_payload.py` owns the write:

```python
# src/annotation_payload.py  (new — plugins/jack-tar-deckhand/src/ tree, F6)
def build_annotation_payload(slide_number, source, base_image_path,
                             image_dimensions, placement_zone, anchors,
                             *, style_overrides=None, style_guide=None) -> dict:
    """anchors is the VALIDATED {label: [x,y]} from validate_anchors().
    Resolves label positions via annotate_figure.place_labels, computes
    base_image_hash via process_image.compute_content_hash, merges
    style_overrides over the code-level defaults (F9), and returns a
    schema-valid FULLY-EXPLICIT payload dict. Pure apart from reading the
    base image file for its hash — no model calls."""
    from src.annotate_figure import place_labels
    from src.process_image import compute_content_hash
    placements = place_labels(anchors, (image_dimensions["width"],
                                         image_dimensions["height"]))
    labels = [{"text": name,
               "anchor": placements[name]["anchor"],
               "label_pos": placements[name]["label_pos"]}
              for name in anchors]
    ...  # fill style defaults + jsonschema.validate against annotations.schema.json

def write_annotation_payload(deck_dir, slide_number, payload) -> str:
    """Atomic write to <deck_dir>/annotations/slide-NN-annotations.json
    (mkdir -p annotations/; os.replace tmp -> final, per manifest_utils.py)."""

def estimate_label_box(text, font_size_pt, *, pad_in=0.06) -> (float, float):
    """THE single shared label-box estimator (F13). Both assembler paths use
    this exact formula (the JS assembler ports it verbatim):
        chars_per_inch = 7.0 * (18.0 / font_size_pt)   # 7 cpi at 18pt, linear
        text_w_in = len(text) / chars_per_inch
        box_w_in  = text_w_in + 2 * pad_in
        box_h_in  = (font_size_pt / 72.0) * 1.4 + 2 * pad_in
    Returns (box_w_in, box_h_in). Pinned by a cross-path parity test (§8.3)."""
```

`place_labels` is imported and reused verbatim — the load-bearing reuse the
task demanded.

**Manifest integration (F7):** the bridge **appends/updates the slide's entry in
the in-memory `image_manifest` dict** during Step 4 processing — exactly the
Step 4.7 creative_vision precedent (`image_manifest["images"].append({...})`) —
and writes the manifest once at the end of the bridge run. `manifest_utils`
functions are reserved for **post-write surgery** (iterate-slide refinements,
§6.3), not for the bridge's own in-flight writes.

---

## 3. Design question 2 — coordinate mapping (both assembler paths)

The payload gives image-normalized `[nx, ny]`. The assembler must map to slide
inches (JS) / EMU (python-pptx). The map depends on the image's placement rect
on the slide.

### 3.1 The fit decision: contain, for ALL annotated images (F11, F12)

The two assembler paths treat full-slide images differently today (corrected
per F12):

- **JS path**: every full-slide strategy places its image with
  `sizing: { type: 'cover' }` — `buildFullBleedSlide`, `buildFullRenderSlide`,
  `buildBackgroundSlide`, `buildBackdropSlide` in build_deck.js. **cover
  CROPS** the image to fill the canvas: anchors in the cropped border are
  pushed off-frame and the coordinate map is scaled/shifted by an unknown crop.
- **python-pptx template path**: `_apply_full_bleed`
  (build_deck_template.py, `add_picture(..., width=slide_w, height=slide_h)`)
  **STRETCHES** the image to the canvas — no crop. Under a stretch, normalized
  anchors DO map linearly to the slide, but any aspect mismatch distorts the
  figure (circles become ellipses), which is unacceptable for a technical
  figure.

**Decision: annotated images — BOTH `native` AND `raster` modes — always
`contain`-fit on full-slide strategies** (review ruling F11 extends the
original native-only decision to raster). For native, contain is required for
anchor validity (JS crop) and figure fidelity (template stretch). For raster,
cover-cropping a baked PNG would crop the margin-band labels themselves off
the slide, and stretching would distort the typeset label text — same
letterbox price, same fix. The assembler computes the contain-fit rect of the
image inside the placement zone (the exact aspect-preserving math already in
`buildContentSlide` and `buildDiagramSlide`), and maps normalized coordinates
into THAT fitted rect. Letterbox bands (if the image aspect ≠ zone aspect) are
filled with `palette.background`.

**The letterbox price, stated plainly:** a contain-fit image whose aspect
differs from 16:9 shows background bands on two sides. The `/annotate-figure`
skill renders base images at 1024×576 (16:9) by default (SKILL.md §1), so
bands are nil in the generated path; **external images of arbitrary aspect
WILL letterbox** — this is the accepted cost of keeping every anchor (and
every baked label) on-slide and undistorted.

This divergence from the existing full-slide builders is the reason annotated
slides are routed to their OWN builder rather than patched into the
cover/stretch-based builders.

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
| `full_bleed`, `full_render`, `background`, `backdrop`, `academic_figure` | `annotated_full_slide` | `(0, 0, SLIDE_W, SLIDE_H)` | `(0, 0, slide_w, slide_h)` EMU |
| `composed` (content slide w/ image) | `annotated_image_zone` | `layout.content_with_image.image_zone` (default `(SLIDE_W*0.525, SLIDE_H*0.107, SLIDE_W*0.428, SLIDE_H*0.787)`) | picture-placeholder rect from `profile_layout` |

**`academic_figure` reality check (F2):** build_deck.js today has NO
strategy-first branch for `academic_figure` — it falls through to the
slide-type `switch` and renders via the composed builders (typically
`buildDiagramSlide`/`buildContentSlide`, i.e. WITH heading chrome and a
contain-fit image zone). v2's native/raster annotation branch (§6.2) gives an
annotated academic_figure slide a dedicated pure-figure route for the first
time; un-annotated academic_figure slides keep today's fall-through behaviour
unchanged.

**Pure-figure behavioural change (F2 ruling):** a `native`-annotated slide
renders like `full_bleed` — **no headline, no body_points, no footer logo**;
the contain-fit figure plus its label overlay is the entire slide (speaker
notes are kept). This applies regardless of base strategy, including
`background`/`backdrop` whose un-annotated forms carry text panels. A headline
opt-in flag is a fast-follow, out of v2.

Image native `(W, H)` comes from the payload's `image_dimensions` (the assembler
never opens the PNG — respects the discipline hook and avoids a PIL dependency
in JS). The JS assembler already reads `imageData.dimensions` for aspect fits;
the payload duplicates it so the python path has it too.

`composed` / `annotated_image_zone` support is **deferred** (F2 ruling upholds
the deferral) — schema-allowed and mapping-specified, but v2 ships and tests
the full-slide strategies + `academic_figure` only.

---

## 4. Design question 3 — the PptxGenJS native path

Verified against `pptxgenjs@4.0.1` type defs (`types/index.d.ts`).

### 4.1 Leader lines — line shape, NOT a begin/end-point API (deviation)

**PptxGenJS 4.0.1 has no begin/end-point line API.** A `ShapeType.line`
(`'line'`) is drawn as a **bounding box** `(x, y, w, h)` whose un-flipped
diagonal runs top-left → bottom-right; `flipH`/`flipV` (ShapeProps) select
which diagonal. So a leader from anchor `A=(ax,ay)` to label-box edge
`B=(bx,by)` (inches) is:

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
(`_segment_box_entry`, annotate_figure.py).

`line` options confirmed present: `width`, `dashType`, `beginArrowType`,
`endArrowType`, and `color` via `ShapeFillProps` (ShapeLineProps).

### 4.2 Casing (white halo) — paired underlay line, no native option

PptxGenJS has no line-outline/casing option, so v2 mirrors v1's cartographic
casing (annotate_figure.py `_draw_leader` passes) with a **paired underlay**: a
white line of `casing_width_pt` drawn FIRST, then the dark leader of
`leader_width_pt` on top. Casing underlays get their **own name prefix** —
`annotation_casing_<n>_<i>` — distinct from the dark cores'
`annotation_leader_<n>_<i>` (F10), so QA can count cores exactly without
double-counting.

### 4.3 Label boxes + terminus dots

- **Box + text in one call:** `addText(text, { x, y, w, h, fill:{color:boxFill},
  line:{color:boxBorder, width:boxBorderWidthPt}, fontFace, fontSize, color:textColor,
  align:'center', valign:'middle', objectName:'annotation_label_<n>_<i>' })`.
  Box `(w, h)` comes from the **shared estimator** `estimate_label_box(text,
  font_size_pt)` (§2.3, F13) — the JS assembler ports the formula verbatim; the
  box is centred on the mapped `label_pos`.
- **Terminus dot:** `addShape(pptx.ShapeType.ellipse, { ..., fill:{color:leaderColor},
  line:{type:'none'}, objectName:'annotation_dot_<n>_<i>' })`, a `2*dot_radius_pt`
  square centred on the mapped `anchor`. Preceded by a white casing ellipse
  (`dot_radius_pt + casing_extra`) named `annotation_dotring_<n>_<i>` (F10) for
  the ring, matching v1's dot casing.

### 4.4 Z-order (insertion order)

PptxGenJS draws shapes in call order; there is no explicit z-index. Add in this
order (identical pass structure to v1's `annotate`):

1. letterbox background fill + base image (contain-fit)
2. ALL `annotation_casing_*` lines + ALL `annotation_dotring_*` rings
3. ALL `annotation_leader_*` dark cores + ALL `annotation_dot_*` dots
4. ALL `annotation_label_*` boxes + text (box over any leader beneath it)
5. speaker notes (NO headline band, NO footer logo — pure figure, F2)

### 4.5 The `objectName` lesson (Spike 1)

Every annotation shape sets **`objectName`**, never `name` — PptxGenJS 4.0.1
silently drops the `name` property (Spike 1, 2026-04-23; the pptx_native
placeholder uses `objectName` for exactly this reason). QA (§7) selects
annotation shapes by the `annotation_*` name prefixes, so the tags MUST survive
into the OOXML.

### 4.6 The label-box-edge termination point

v1 terminates the leader at the label box edge nearest the anchor
(`_segment_box_entry`, annotate_figure.py), not the box centre, so the line
never enters the box. The assembler reuses the SAME geometry: after sizing the
label box via `estimate_label_box`, compute the box rect in inches, then
`B = segment_box_entry(anchor_in, label_centre_in, box_rect_in)`. This helper is
pure geometry — **lift it into `annotation_payload.py` (shared geometry
helpers) so the Python template path uses it directly and the JS assembler
ports it** (~15 lines of slab-clip). Both the segment clip AND the box
estimator are pinned by cross-path parity tests (§8.3).

---

## 5. Design question 4 — the python-pptx template path

### 5.1 Connectors — explicit begin/end points (cleaner than JS)

python-pptx `slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, bx, by, ex, ey)`
takes explicit begin/end EMU points — **no flip arithmetic needed** (a genuine
asymmetry with the JS path, worth noting for implementers). Set
`conn.line.color.rgb = RGBColor(...)`, `conn.line.width = Pt(...)`. Casing =
a wider white connector added first (`conn.name = 'annotation_casing_<n>_<i>'`),
dark connector second (`'annotation_leader_<n>_<i>'`). Arrowheads are not
exposed by python-pptx's connector API — leaders are plain lines terminated by
the dot, exactly like v1 (no arrow). python-pptx `name` assignment works — the
Spike 1 drop is a PptxGenJS-only bug.

### 5.2 Dots + label boxes

- Dot: `slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, w, h)`; `fill.solid()`,
  `fill.fore_color.rgb`; `line.fill.background()`; names `annotation_dot_*` /
  casing ring `annotation_dotring_*` (F10), ring added first.
- Label box: `tb = slide.shapes.add_textbox(x, y, w, h)` with `(w, h)` from the
  SAME `estimate_label_box` helper (F13); box fill via
  `tb.fill.solid(); tb.fill.fore_color.rgb=...`; border via `tb.line.color.rgb` /
  `tb.line.width`; text via `tb.text_frame` paragraph run, `run.font.name/size/
  color.rgb/bold`. Centre with `tf.word_wrap=True`, paragraph alignment
  `PP_ALIGN.CENTER`, `tf.vertical_anchor = MSO_ANCHOR.MIDDLE`. Name
  `annotation_label_<n>_<i>`.

### 5.3 New function + template-mode constraints

New `_apply_native_annotation(slide, base_image_path, payload, slide_w, slide_h,
zone_rect_emu)` in build_deck_template.py, modelled on `_apply_full_bleed`:

0. **Hash gate (F4):** recompute the base image's content hash and compare with
   `payload.base_image_hash`. On mismatch: log a warning naming both hashes,
   place the base image contain-fit **WITHOUT any overlay** (warn-refuse — a
   stale overlay on a changed image is worse than none), and return. AN-01
   flags the slide at QA time (§7).
1. Strip all shapes (like full_bleed) — **pure figure (F2)**: native annotation
   in template mode does NOT populate the template's title/body/picture
   placeholders and adds NO headline textbox. The base image is added as a bare
   picture (hoisted after `nvGrpSpPr`/`grpSpPr` per the existing spTree-order
   fix in `_apply_full_bleed`) at the contain-fit rect — note this REPLACES
   the stretch-to-canvas behaviour for annotated slides (§3.1) — then
   connectors, ovals and textboxes are added AFTER it (spTree order = z-order,
   so they land on top).
2. Contain-fit the picture inside `zone_rect_emu` (§3.2, all math in EMU via
   `Inches`); letterbox fill first.
3. Draw casing connectors → dark connectors → casing rings → dots → label boxes
   (same z-order as §4.4).

Wire into `build_deck` (build_deck_template.py) as a short-circuit mirroring
the `full_bleed` block: read `annotation_mode` from the strategy map entry and,
when `native` AND the payload file exists AND the hash gate passes, call
`_apply_native_annotation` and `continue`. When `native` and the payload file
is ABSENT, place the image contain-fit without overlay and log a warning —
AN-01 raises the error at QA (§7, F3c/F5).

---

## 6. Design question 5 — strategy-map surfacing + bridge honouring

### 6.1 Schema diff — `strategy_map.schema.json`

Add two per-slide properties and one `allOf` conditional (mirroring the existing
creative_vision conditional):

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

Conditional (added to the per-slide `allOf`, alongside the creative_vision one).
**F1 blocker fix applied**: the `if` REQUIRES the `annotation_mode` key, so the
conditional cannot fire vacuously on existing strategy-map documents that omit
the key entirely (JSON Schema treats a missing property as satisfying any
`properties` constraint — without `required`, the `then` branch would have
fired for every legacy entry and rejected them all):

```jsonc
{
  "if": {
    "required": ["annotation_mode"],
    "properties": {"annotation_mode": {"enum": ["raster", "native"]}}
  },
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

The regression test `test_schema_accepts_entry_without_annotation_mode_key`
(§8.2) pins this: a strategy-map document with NO `annotation_mode` key on any
slide validates unchanged. (Entries with `annotation_mode: "none"` also take
the `else` branch, which correctly forbids an orphan `annotation` object.)

The `then` branch bidirectionally binds the request (mode set ⇒ `annotation`
required AND strategy restricted to image-dominant strategies). `creative_vision`
and `smartart` are deliberately excluded: creative_vision's image IS the
operator-certified deliverable (F12/issue #113), and smartart is a graphic, not
a figure.

### 6.2 How the conductor / bridge honour it

Read at the imagegen-bridge, per slide, from `strategy-map.json`:

- **`none` / absent** — unchanged pipeline.
- **`raster`** — bridge runs the v1 flow (label-stripped base render OR external
  image → anchor pass → `annotate()` bakes the labelled PNG). The labelled PNG
  becomes the slide's `file_path` in the image manifest with `placement_zone:
  "annotated_full_slide"` (or `annotated_image_zone`). **No annotations
  payload**, but the assembler routes annotated-zone images through the
  **contain-fit** placement (F11, §3.1) — never cover/stretch — so baked
  margin-band labels survive intact. No overlay renderer involved.
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
   `annotation.labels`. `validate_anchors(response)`; ONE re-dispatch on
   validation failure with the error message included.
   **Anchor-pass failure path (F5):** if the re-dispatch ALSO fails validation,
   NEVER fall through silently. Surface to the operator with an explicit
   three-way choice:
   (a) **retry** the anchor pass (fresh dispatch, optionally at Sonnet tier);
   (b) **fall back to raster with manual anchors** — the operator supplies
       `{label: [x, y]}` coordinates by hand and the v1 `annotate()` flow bakes
       them;
   (c) **ship unlabeled** — the base image goes in as a plain figure.
   Whatever the choice, the manifest entry's `status` is at minimum
   `accepted_with_issues` and `review_summary` records the anchor-pass failure.
   For (c), no payload is written and `annotation_mode` effectively degrades —
   AN-01's absent-payload error (§7, F3c) is the QA-side tripwire ensuring this
   degradation is always operator-acknowledged, never accidental.
3. Read the base image dimensions (`process_image.get_dimensions`).
4. `build_annotation_payload(...)` (§2.3) — resolves `label_pos` via
   `place_labels`, computes `base_image_hash` (F4), fills style defaults in
   code (F9), schema-validates.
5. `write_annotation_payload(deck_dir, slide_number, payload)` →
   `annotations/slide-NN-annotations.json`.
6. **Append the image-manifest entry to the in-memory manifest dict** (F7 —
   Step 4.7 precedent; no `manifest_utils` during the bridge run):
   `file_path` = base image, `placement_zone` (`annotated_full_slide` /
   `annotated_image_zone`), `annotations_path` =
   `annotations/slide-NN-annotations.json`, `status: generated`.
7. **Anchor-verification review — pre-assembly raster preview (OQ4 resolved):**
   run `annotate()` on the same anchors to produce a THROWAWAY raster preview,
   dispatch the pointers-only review on it (annotate-figure SKILL.md §4). One
   refine loop re-queries coordinates and rewrites the payload (steps 4–5).
   Cheaper than post-assembly rasterisation and keeps the loop before any
   OOXML is built; the preview PNG is never placed in the deck.

Assembler routing key = **`annotation_mode == native` on the strategy-map entry
AND presence of `annotations_path` on the image entry** — orthogonal to the
base strategy. Both assemblers gain a branch (JS: before the strategy switch in
`assembleDeck`; python: a short-circuit like full_bleed in `build_deck`) that
calls the new native-annotation builder and `continue`s. A `raster`-mode slide
routes to the same builder's image-placement path (contain-fit, pure figure)
with a no-op overlay (F11).

### 6.3 Invalidation contract — re-renders and iterate-slide (F4)

Anchors are a function of the exact base image. The contract:

- The payload stores `base_image_hash` (sha256 at payload-build time, §2.2).
- **Assembler**: hash-gate before drawing the overlay (§5.3 step 0). The
  python path enforces it directly; the JS builder stays dependency-free and
  trusts the payload — AN-01 is the cross-path enforcement point (see §13 F4
  disposition note).
- **AN-01** (§7) errors on hash mismatch AND on absent payload for a
  native-contracted slide.
- **Any re-render of a native-annotated slide invalidates the payload.** The
  imagegen-bridge, on regenerating the base image (funnel retry, provider
  fallback, operator-driven re-render), MUST re-run the anchor pass and
  `build_annotation_payload` before assembly.
- **iterate-slide (#89) integration — new task T12:** `iterate-slide` can
  replace a slide's image post-pipeline (via `manifest_utils.
  replace_image_in_manifest` — the legitimate post-write-surgery use, F7). For
  slides whose strategy-map entry has `annotation_mode: native`,
  `iterate_slide_dispatch.py` gains a guard: after image replacement it MUST
  re-run the anchor pass + `build_annotation_payload` + payload rewrite (or,
  if the operator declines, downgrade with the F5 three-way choice). The
  iterate-slide SKILL.md documents the extra step. Without this, an iterated
  image ships with the PREVIOUS image's anchors — the hash gate makes that
  fail safe (overlay refused), but the skill must make it fail CORRECT
  (anchors refreshed).

---

## 7. Design question 6 — new deck-qa checks

New module `src/qa/checks/annotation_checks.py`, three checks, registered as
`ANNOTATION_CHECKS` in `checks/__init__.py`.

**run_qa routing (F3a/F3b):** `run_qa` gains a **dedicated routing branch** for
slides whose strategy-map entry has `annotation_mode == "native"`:

- runs `IMAGE_QUALITY_CHECKS` + `KEYNOTE_CHECKS` + `ANNOTATION_CHECKS`;
- runs `STRUCTURAL_CHECKS` / `STRUCTURAL_CHECKS_WITH_PRESENTATION` with
  **`annotation_*`-named shapes EXEMPTED** — the exemption is passed via the
  check `config` (`config['exempt_shape_name_prefixes'] = ['annotation_']`) so
  text checks (e.g. AP-02 min font size, text-density) skip label shapes rather
  than flagging every deliberately-small overlay label. The AP-02 exemption for
  operator-overridden sub-18pt labels (§2.2) lives here.

**Supporting refactor (F3b, folded into T7):** `run_qa` currently reduces the
strategy map to `{slide_number: strategy_string}`. It is refactored to retain
the **full strategy-map entries** (`{slide_number: entry_dict}`) so the routing
branch can read `annotation_mode` (and future per-slide keys) without a second
file parse; existing call sites read `entry['speaker_override'] or
entry['strategy']` from the retained dict.

The checks (all read `annotations/slide-NN-annotations.json` as the source of
truth; annotation shapes are selected by name prefix — reliable because §4.5
tags every shape via `objectName` (JS) / `name` (python-pptx)):

- **AN-01 — annotation contract honoured.** For each slide contracted
  `annotation_mode: native`:
  - payload file ABSENT ⇒ **`error`** (F3c — the contract was dropped;
    pairs with the F5 operator-acknowledged degradation path);
  - `base_image_hash` ≠ hash of the manifest image on disk ⇒ **`error`**
    (F4 — stale anchors);
  - otherwise assert **EXACT counts** (F10): exactly `N = len(payload.labels)`
    shapes named `annotation_label_*`, exactly `N` named `annotation_leader_*`,
    exactly `N` named `annotation_dot_*`; and, when `style.casing_width_pt > 0`,
    exactly `N` `annotation_casing_*` and `N` `annotation_dotring_*`. Any
    deviation ⇒ `error`.
- **AN-02 — label text verbatim.** The multiset of `annotation_label_*` textbox
  strings must equal the multiset of `payload.labels[].text`, character-exact.
  Any mismatch (truncation, casing drift, missing) ⇒ `error`, naming
  expected vs actual. This is the whole point of the feature — text is perfect
  by construction, and QA proves the contract survived assembly.
- **AN-03 — boxes within slide bounds.** Every `annotation_label_*` shape rect
  must lie fully within `[0, slide_w] × [0, slide_h]`. Off-slide ⇒ `warning`
  (placement pushed a label off-canvas; operator should nudge `label_pos` or add
  an explicit override).

(Optional, deferred: AN-04 leader-does-not-cross-sibling-box — v1 guarantees this
in image px, but vector box sizes differ from PIL px so the guarantee is only
approximate. OQ2 ruling: ship as-is now, AN-04 to the backlog.)

---

## 8. Design question 7 — test matrix

Mirror existing patterns: `test_full_bleed_scale.py` (schema + `_apply_*` unit +
python `build_deck` OOXML + JS-subprocess OOXML, all gated on toolchain
availability) and `test_annotate_figure.py` (pure-function coverage).

### 8.1 `tests/test_annotation_payload.py` (new — payload writer + schema)
- `test_schema_valid_payload_passes` — a hand-built fully-explicit payload validates.
- `test_schema_rejects_out_of_range_norm_point` — anchor `[1.4, 0.2]` rejected.
- `test_schema_rejects_empty_labels` — `labels: []` rejected.
- `test_schema_rejects_zero_image_dimension` — `width: 0` rejected (F14).
- `test_schema_requires_contain_fit` — `fit: "cover"` rejected.
- `test_schema_requires_base_image_hash` — missing hash rejected (F4).
- `test_build_payload_resolves_label_pos_via_place_labels` — payload
  `label_pos` equals `place_labels(anchors, dims)` output (reuse assertion).
- `test_build_payload_is_deterministic` — same inputs → identical payload.
- `test_build_payload_preserves_label_text_verbatim` — special chars / spaces.
- `test_build_payload_computes_content_hash_of_base_image` (F4).
- `test_build_payload_fills_all_style_fields_in_code` (F9 — renamed intent: NO
  schema defaults; the CODE fills every style field, output is fully explicit;
  default `font_size_pt` is 18).
- `test_build_payload_style_override_wins` — explicit `font_size_pt: 14`
  survives into the payload.
- `test_write_payload_atomic_and_roundtrips` — file written under
  `annotations/`, reloads equal, tmp file gone (mirror manifest_utils atomicity).
- `test_estimate_label_box_formula` — pins the F13 formula at 18pt and one
  scaled size.

### 8.2 `tests/test_strategy_map_annotation.py` (new — schema surfacing)
- **`test_schema_accepts_entry_without_annotation_mode_key`** — F1 regression
  pin: a strategy-map document with NO `annotation_mode` key validates (legacy
  documents unaffected).
- `test_schema_accepts_annotation_mode_none_without_annotation`.
- `test_schema_accepts_native_with_annotation_on_full_bleed`.
- `test_schema_accepts_raster_with_annotation_on_academic_figure`.
- `test_schema_rejects_native_without_annotation` (conditional `then.required`).
- `test_schema_rejects_annotation_without_mode` (conditional `else.not`).
- `test_schema_rejects_annotation_with_mode_none`.
- `test_schema_rejects_native_on_creative_vision` (strategy enum in `then`).
- `test_schema_rejects_native_on_smartart`.
- `test_schema_rejects_label_missing_target`.
- `test_image_manifest_schema_accepts_annotations_path_and_zones` (F8 — the
  image-manifest schema gains `annotations_path` and documents the
  `annotated_full_slide` / `annotated_image_zone` zone values).

### 8.3 `tests/test_annotate_native_assembler.py` (new — BOTH assembler paths)

python-pptx path (no toolchain gate — always runs, like the `_apply_full_bleed`
unit tests):
- `test_apply_native_annotation_strips_chrome_then_adds_picture` — 1 picture at
  contain-fit rect; pre-existing placeholders gone; NO headline textbox (F2).
- `test_apply_native_annotation_emits_exact_shape_counts` — N labels ⇒ exactly N
  textboxes `annotation_label_*`, N connectors `annotation_leader_*`, N ovals
  `annotation_dot_*`, N casing connectors `annotation_casing_*`, N rings
  `annotation_dotring_*` (F10).
- `test_apply_native_annotation_label_text_is_verbatim` — each textbox text
  equals the payload label (OOXML `text_frame.text`).
- `test_apply_native_annotation_maps_anchor_into_fitted_rect` — a known anchor
  `[0.5, 0.5]` on a 16:9 image in a 16:9 zone → dot centre at zone centre
  (EMU assertion within tolerance).
- `test_apply_native_annotation_letterboxes_off_aspect_image` — 1:1 image in
  16:9 zone → fitted rect narrower than slide; anchor `[0,0]` maps to the band
  edge, not slide origin.
- `test_apply_native_annotation_refuses_overlay_on_hash_mismatch` — payload
  hash ≠ image hash ⇒ picture placed, ZERO `annotation_*` shapes (F4 warn-refuse).
- `test_apply_native_annotation_z_order_labels_after_picture` — in spTree,
  every `annotation_label_*` element index > the `pic` element index.
- `test_build_deck_template_native_annotation_end_to_end` (skipif no template
  fixture) — full `build_deck` run; native slide has picture + labels + no
  headline, sibling composed slide keeps its chrome (backward-compat, mirrors
  full_bleed test).
- `test_build_deck_template_raster_annotation_contains_not_stretches` — a
  raster-mode annotated slide's picture is contain-fit (aspect preserved), not
  stretched to canvas (F11).
- `test_build_deck_template_without_annotation_unchanged` — no
  `annotation_mode` ⇒ no annotation shapes, full_bleed still stretches as today
  (backward-compat).

JS path (skipif no node+pptxgenjs, mirroring `_have_node_with_pptxgenjs`):
- `test_js_assembler_native_annotation_emits_label_textboxes` — subprocess
  `build_deck.js`; native slide OOXML has exactly N `annotation_label_*`
  textboxes with verbatim text and N `annotation_leader_*` line shapes (F10
  exact counts).
- `test_js_assembler_native_annotation_objectname_survives` — asserts the
  `annotation_*` names appear in the OOXML (guards the Spike 1 `objectName`
  regression).
- `test_js_assembler_native_annotation_drops_headline_and_body` — pure figure
  (F2): outline headline/body strings absent from the slide OOXML.
- **Cross-path parity (F13 + §4.6):**
  - `test_js_segment_box_entry_parity` — JS `_segmentBoxEntry` output matches
    the Python `_segment_box_entry` for a fixed set of segments.
  - `test_label_box_estimator_parity` — for a fixed label set and two font
    sizes, the box rects produced by the python path and the JS path (extracted
    from each OOXML) agree within EMU rounding tolerance.

### 8.4 `tests/test_annotation_qa_checks.py` (new — QA)
- `test_an01_errors_when_payload_absent_for_native_slide` (F3c).
- `test_an01_errors_on_base_image_hash_mismatch` (F4).
- `test_an01_flags_wrong_leader_count` — payload has 3 labels, slide built with
  2 leaders ⇒ AN-01 error (exact-count, F10).
- `test_an01_flags_extra_label_shape` — N+1 label shapes ⇒ error (exact-count).
- `test_an01_passes_when_counts_exact`.
- `test_an02_flags_text_mismatch` — a textbox says "Ruddar" ⇒ AN-02 error naming
  the expected/actual.
- `test_an02_passes_on_exact_match`.
- `test_an03_flags_box_off_slide` — a `label_pos` mapping off-canvas ⇒ AN-03
  warning.
- `test_an03_passes_when_all_in_bounds`.
- `test_annotation_checks_skipped_for_raster_and_none` — non-native slides emit
  no AN findings.
- `test_run_qa_native_branch_exempts_annotation_shapes_from_structural` — an
  intentionally sub-18pt annotation label does NOT trip AP-02 on a native
  slide (F3a exemption), while a sub-18pt NON-annotation textbox still does.
- `test_run_qa_retains_full_strategy_entries` — the refactored loader exposes
  `annotation_mode` per slide (F3b).

### 8.5 Regression
- Full existing suite green (`test_full_bleed_scale.py`, `test_annotate_figure.py`
  unchanged — v1 engine untouched).
- `plugins/integration_tests/test_plugin_imports.py` green (F6 — the new
  modules live in the plugin tree and must import cleanly).

---

## 9. Design question 8 — task breakdown (Sonnet-sized)

**All file paths are in the `plugins/jack-tar-deckhand/` tree exclusively (F6).**
The repo-root `src/` is confirmed stale/divergent for these modules — do NOT
touch it; a separate cleanup issue is being filed. There is no
`release-mapping.yaml` in this repository.

Each task ≤ one focused PR-slice, with depends-on and a Definition of Done. All
DoD include "flake8 + pre-commit clean; touched tests green."

**Inline discipline reminder for every image-touching task prompt:** *Do not
`Read` PNG/JPG/GIF/WEBP/BMP/TIFF files directly. To verify an image, dispatch the
`jack-tar-deckhand:image-reviewer` (Haiku) or `general-purpose` (Sonnet)
subagent — they pull the image into THEIR context and return text.*

| # | Task | Depends on | DoD |
|---|---|---|---|
| T1 | `src/schemas/annotations.schema.json` (§2.2) **+ image_manifest.schema.json extension** — add `annotations_path` (string) and document the `annotated_full_slide` / `annotated_image_zone` placement_zone values (F8) | — | Both schemas parse; §8.1 schema cases + `test_image_manifest_schema_accepts_annotations_path_and_zones` green. |
| T2 | `src/annotation_payload.py` — `build_annotation_payload` (reuse `place_labels`; content hash F4; code-level style defaults F9) + `write_annotation_payload` + `estimate_label_box` (F13) (§2.3) | T1 | Payload writer tests green; atomic write verified; estimator formula pinned. |
| T3 | Strategy-map schema diff — `annotation_mode` + `annotation` + **F1-fixed** `allOf` conditional (§6.1) | — | `test_strategy_map_annotation.py` green INCLUDING the no-key regression pin; existing strategy-map tests green. |
| T4 | Shared geometry: lift `_segment_box_entry` into `annotation_payload.py` helpers + JS ports `_segmentBoxEntry` AND `estimateLabelBox` with parity tests (§4.6, §8.3, F13) | T2 | Both parity tests green. |
| T5 | python-pptx native builder `_apply_native_annotation` (hash gate F4, pure figure F2, contain-fit F11 incl. raster-mode routing) + `build_deck` wiring (§5) | T1,T4 | python-pptx assembler tests (§8.3) green incl. hash-refusal + raster-contain cases. |
| T6 | JS native builder `buildNativeAnnotatedSlide` + `drawAnnotations` + routing branch (native + raster contain-fit) (§3.3, §4, F10 prefixes, F2 pure figure) | T1,T4 | JS-subprocess assembler tests (§8.3) green; `objectName` survives; headline/body absent. |
| T7 | QA `annotation_checks.py` (AN-01 exact-count/absent-payload/hash, AN-02, AN-03) + `ANNOTATION_CHECKS` registration + **run_qa native routing branch with `annotation_*` structural exemption + full-entry strategy-map refactor** (§7, F3) | T1 | `test_annotation_qa_checks.py` green incl. exemption + full-entry tests; existing QA tests green against the refactored loader. |
| T8 | imagegen-bridge SKILL.md new §4.8 native sub-step (incl. F5 operator failure path, F7 in-memory manifest append, OQ4 pre-assembly preview review) + `annotation_mode` routing note in Step 4 (§6.2) | T2 | Doc references correct module fns + payload path; verify skill unaffected. |
| T9 | `/annotate-figure` SKILL.md — add a "deck-native mode" section pointing at the strategy-map opt-in + assembler behaviour (pure figure, contain-fit/letterbox price); keep v1 raster flow as-is | T8 | Skill documents all three modes + F5 failure path. |
| T10 | Docs + version bump — plugin.json `1.9.0→1.10.0`, marketplace lockstep, plugin CLAUDE.md skill-table note + root CLAUDE.md status stanza; retrospective stub `retrospectives/142-annotate-figure-v2.md` | T1–T9,T12 | JSON-validation CI (version match) green. |
| T11 | **Plugin-tree placement verification (rewritten per F6).** Confirm ALL new modules (`src/annotation_payload.py`, `src/schemas/annotations.schema.json`, `src/qa/checks/annotation_checks.py`, tests) exist ONLY under `plugins/jack-tar-deckhand/`; no root-`src/` edits in the diff | T2,T5,T6,T7 | `git diff --stat` shows plugins-tree-only changes; `plugins/integration_tests/test_plugin_imports.py` green. |
| T12 | **iterate-slide invalidation guard (F4).** `src/iterate_slide_dispatch.py`: for `annotation_mode: native` slides, image replacement triggers mandatory anchor-pass re-run + `build_annotation_payload` rewrite (or F5 operator downgrade); iterate-slide SKILL.md documents the step | T2,T8 | New iterate-slide unit tests green (guard fires for native slides, no-op for others); SKILL.md updated. |

Suggested sequencing: **T1+T3 in parallel** (independent) → **T2** → **T4** →
**T5+T6+T7 in parallel** → **T8+T9+T12** → **T10+T11**.

---

## 10. Out of scope

- **Blank-zone annotation variant** (generate the image with an intentional blank
  margin band, then place labels into guaranteed-empty space rather than over
  content) — **explicitly OUT of v2 scope.** Backlog note: file as a v3 follow-up
  on #142. It needs a prompt-side "reserve a blank right third" directive plus a
  placement mode that targets the reserved band instead of the nearest margin
  band, and a way to detect the band. Not required for deck-native labels.
- **`annotated_image_zone` (composed) native annotation** — schema-allowed and
  mapping-specified (§3.3), DEFERRED per F2 ruling: the right-column image zone
  is cramped for multi-label figures. v2 ships full-slide strategies +
  academic_figure as the tested path.
- **Headline opt-in on native-annotated slides** — fast-follow per F2 ruling
  (v2 is pure figure, always).
- **AN-04 leader-crossing check** — backlog per OQ2 ruling.

## 11. Open questions — all resolved by review rulings

| OQ | Question | Ruling |
|---|---|---|
| 1 | cover-crop vs contain | **Contain**, extended by F11 to ALL annotated images (raster + native) on full-slide strategies; letterbox price documented (§3.1). |
| 2 | `place_labels` box-metric mismatch in vector mode | **Ship as-is**; AN-04 to backlog. F13's shared estimator narrows the gap. |
| 3 | Headline on native slides | **Pure figure** (F2): no headline, no body, no footer logo; opt-in is a fast-follow. |
| 4 | Anchor-verification review timing | **Pre-assembly raster preview** (§6.2 step 7). |
| 5 | Canonical source tree | **`plugins/jack-tar-deckhand/src/` exclusively** (F6); root `src/` stale, separate cleanup issue. |

No unresolved open questions remain. One new assumption is recorded in §13
(F3d note on the AP-02 floor value).

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
- **The two full-slide paths mishandle annotated images in DIFFERENT ways**
  (corrected per F12): the JS builders `cover`-CROP (anchors/labels pushed
  off-frame), while the template path's `_apply_full_bleed` STRETCHES to canvas
  (anchors map linearly but the figure distorts). Both motivate the contain-fit
  own-builder decision (§3.1) — this is the largest structural decision.
- **`academic_figure` has no strategy-first assembler branch today** — it falls
  through to the composed slide-type routing with heading chrome (§3.3, stated
  per F2). v2's annotation branch is its first dedicated route.
- **`place_labels` already returns image-normalized coordinates** — so the
  server-side reuse is clean and the assembler is a pure resolved-coordinate
  renderer; no placement logic crosses into the assembler.

---

## 13. Design review disposition (adversarial review, 2026-07-17)

Verdict: APPROVE-WITH-CHANGES — 1 blocker, 5 major, 8 minor. All rulings
applied as directed; none relitigated.

| # | Sev | Finding (summary) | Resolution in this doc |
|---|---|---|---|
| F1 | BLOCKER | `allOf` conditional fired vacuously when `annotation_mode` absent — would have rejected every existing strategy map | `if` now carries `"required": ["annotation_mode"]` (§6.1); regression test `test_schema_accepts_entry_without_annotation_mode_key` added (§8.2). |
| F2 | Major | Native-mode chrome ambiguity; academic_figure reality unstated | RULING adopted: native = **pure figure** (no headline/body/footer) — §1, §3.3, §4.4, §5.3, tests §8.3; academic_figure's current composed fall-through stated in §3.3; headline opt-in fast-follow + composed-zone deferral recorded in §10; OQ3 closed (§11). |
| F3 | Major | QA routing under-specified; run_qa loses entry data; absent payload unhandled; default label font below AP-02 floor | (a) dedicated run_qa native branch: image-quality + keynote + AN checks, structural checks with `annotation_*` shapes exempted via config (§7); (b) run_qa refactored to retain full strategy-map entries — folded into T7; (c) AN-01 ERRORS on absent payload (§7); (d) default `font_size_pt` = 18 matching the AP-02 floor; sub-18 only via explicit override with scoped, documented AP-02 exemption (§2.2, §7). Tests §8.4. |
| F4 | Major | No invalidation contract — re-rendered image would ship with stale anchors | Payload gains required `base_image_hash` (§2.2); assembler warn-refuses overlay on mismatch (§5.3 step 0); AN-01 errors on mismatch (§7); §6.3 mandates anchor-pass + payload rebuild on ANY re-render; **new task T12** covers iterate-slide SKILL.md + `iterate_slide_dispatch.py`. Implementation stance recorded: the hash gate is enforced directly in the python path and by AN-01; the JS builder stays dependency-free and trusts the payload — AN-01 is the cross-path enforcement point. |
| F5 | Major | Anchor-pass double-failure fell through silently | Explicit operator three-way choice (retry / raster-with-manual-anchors / ship-unlabeled), manifest `status: accepted_with_issues` minimum, `review_summary` records the failure; AN-01 absent-payload error is the QA tripwire (§6.2 step 2), tying to F3(c). |
| F6 | Major | T11 referenced a non-existent `release-mapping.yaml`; root `src/` is stale | T11 rewritten: plugin-tree-only edits, DoD = plugins-tree-only diff + `plugins/integration_tests/test_plugin_imports.py` green (§9); F6 banner at top of §9; OQ5 closed. Verified during revision: `find` confirms no release-mapping file exists anywhere in the repo. |
| F7 | Minor | Bridge should append to the in-memory manifest, not use manifest_utils mid-run | §2.3 + §6.2 step 6 now specify in-memory append per the Step 4.7 precedent; `manifest_utils` scoped to post-write surgery (iterate-slide, §6.3). |
| F8 | Minor | image_manifest schema not extended; placement_zone value collision | T1 extends `image_manifest.schema.json` with `annotations_path` + zone vocabulary; zone values renamed to `annotated_full_slide` / `annotated_image_zone` — distinct from Step 4.7's `full_bleed` and the element flows' `background` (§2.2, §3.3, §6.2). Noted: the manifest's `placement_zone` is currently an untyped string, so this is a vocabulary introduction, not an enum migration. |
| F9 | Minor | Schema `default` keywords are inert; defaults belong in code | Schema `style` now has NO defaults and all fields required; `build_annotation_payload` fills defaults so on-disk payloads are fully explicit; test renamed to `test_build_payload_fills_all_style_fields_in_code` (§2.2, §8.1). |
| F10 | Minor | Casing shapes shared the core prefixes — counts ambiguous | Distinct prefixes `annotation_casing_*` and `annotation_dotring_*` (§4.2, §4.3, §5.1, §5.2); AN-01 asserts EXACT counts per prefix (§7); exact-count tests (§8.3, §8.4). |
| F11 | Minor | Raster-annotated PNGs would be cover-cropped/stretched too | RULING adopted: ALL annotated images route through contain-fit on full-slide strategies; letterbox price documented (§3.1, §6.2 raster bullet); raster-contain test added (§8.3). |
| F12 | Minor | Citation errors; template path STRETCHES (not crops) — rationale misattributed | §3.1 and §12 corrected: JS = cover-crop, template = stretch-distort; both motivate contain. Fragile line-number citations replaced with function-name references. |
| F13 | Minor | Label-box sizing unspecified per-path — boxes would diverge | ONE shared estimator `estimate_label_box` specified with the exact formula (7 cpi at 18pt, linear scale, fixed padding) in §2.3; both builders use it (§4.3, §5.2); cross-path box-rect parity test added (§8.3). |
| F14 | Minor | `image_dimensions` accepted 0 | `minimum: 1` on width/height (§2.2); rejection test added (§8.1). |

**New assumption recorded while applying rulings (F3d):** the AP-02 floor is
taken as 18pt per the review's statement ("matches AP-02 floor"); implementers
of T7 should read the actual constant from the QA config / structural check and
align the code-level default to THAT value if it differs — the design intent is
"default label size = the AP-02 floor", not the literal 18.
