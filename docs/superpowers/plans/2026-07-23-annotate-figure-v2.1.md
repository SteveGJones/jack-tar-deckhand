# Implementation Plan (addendum): annotate-figure v2.1 — composed zone + headline opt-in (issue #142)

**Feature:** #142 v2.1 (fast-follow to v2 / PR #146)
**Branch:** `feat/annotate-figure-v2.1`
**Status:** Design (implementation-ready). DESIGN ONLY — no production code in this document.
**Author:** detailed-design lead (Claude)
**Created:** 2026-07-23 (rev 2, same day — adversarial review applied, see §9)
**Version target:** jack-tar-deckhand `1.10.0 → 1.11.0` (marketplace lockstep)
**Parent design (single source of truth):** [`docs/superpowers/plans/2026-07-17-annotate-figure-v2.md`](2026-07-17-annotate-figure-v2.md)

---

## 1. Summary

v2 (PR #146, deckhand 1.10.0) shipped `annotation_mode: native` as a **pure
figure** (F2 ruling): editable PPTX label boxes + connector leaders over an
unlabelled, contain-fit base image, drawn by BOTH assembler paths, tested for
the full-slide strategies + `academic_figure` only. Two items were deliberately
deferred (v2 §10):

1. **`composed` strategy wiring (`annotated_image_zone`)** — schema-allowed and
   mapping-specified (v2 §3.3) but unimplemented in either assembler.
2. **Headline opt-in on native-annotated slides** — the F2 ruling made native =
   pure figure; a headline opt-in was recorded as a fast-follow.

This addendum designs both. Scope is deliberately narrow — the payload contract
(`annotations.schema.json`), the overlay renderer (`drawAnnotations` /
`_apply_native_annotation`'s draw passes), the shared geometry
(`estimate_label_box`, `segment_box_entry`), the QA checks (AN-01/02/03), and
the bridge's payload build are all UNCHANGED. The work is entirely in
**assembler routing + zone selection + chrome retention**, one small schema
field, and doc/version updates.

**Two design keystones carried from v2:**

- The overlay renderer is a **pure resolved-coordinate painter**. It maps
  image-normalized `[nx, ny]` into a **contain-fit rect** via
  `X = fx + nx·fw, Y = fy + ny·fh` (v2 §3.2). Both features below are just a
  change to *which rect* that fit is computed inside, and *what chrome*
  surrounds it — the painter itself does not change.
- **Placement zone is derived from the effective base strategy** in both
  assemblers (JS `slideStrategies[n] = speaker_override || strategy`; python
  `entry.get('speaker_override') or entry.get('strategy')`), NOT re-read from
  the payload. `composed ⇒ annotated_image_zone`; everything else ⇒
  `annotated_full_slide`. The bridge writes `placement_zone` into the payload
  to match (§2.5), but the assembler's routing decision is single-sourced on the
  strategy already in hand. This removes the need to load the payload just to
  decide routing (and works for `raster` composed, which has no payload). Per
  the F-02 ruling this keystone is delivered INSIDE the builders too:
  `buildNativeAnnotatedSlide`'s existing payload/manifest zone fallback is
  deleted, not merely bypassed (§2.2).

---

## 2. Feature A — `composed` strategy wiring (`annotated_image_zone`)

### 2.1 What "composed annotated" means (and how it differs from pure figure)

A `composed` slide keeps its chrome: brand background, accent bars, **headline**,
**body_points**, footer logo — the standard content-with-image slide. The
annotated figure occupies the slide's **image zone** (right column), NOT the
whole canvas. This is the OPPOSITE of the v2 pure-figure contract: v2 native
strips all chrome; composed native retains all of it and only swaps the image
zone's plain picture for a contain-fit picture + editable overlay.

The zone rect per path (v2 §3.3, confirmed against current code):

| Path | `annotated_image_zone` rect | Source in code |
|---|---|---|
| JS (`build_deck.js`) | `layouts.content_with_image.image_zone`, default `(SLIDE_W*0.525, SLIDE_H*0.107, SLIDE_W*0.428, SLIDE_H*0.787)` | already the default in `buildContentSlide` (lines ~478-483) and `resolveAnnotationZoneRect` (lines ~1059-1067) |
| python-pptx (`build_deck_template.py`) | picture-placeholder rect `(left, top, width, height)` of the resolved layout | `_find_placeholder_by_type(slide, 'picture', profile_layout)` — already used at lines ~632-637 |

**Slide-type scope (F-03 ruling, option b): EVERY composed annotated slide
renders with content_with_image chrome, regardless of `slide_type`.** The
annotation intercept keys on strategy + `annotation_mode` only — a composed
annotated slide with `slide_type: diagram` or `data_chart` (schema-legal per
`slide_outline.schema.json`) routes through `buildContentSlide` like any other,
never through `buildDiagramSlide`/`buildDataChartSlide`. Rationale: the
annotated figure IS the slide's visual content and needs an image zone +
contain-fit + overlay; `buildDiagramSlide`/`buildDataChartSlide` are built
around SmartArt/chart manifests, not figure images, and have no overlay hook.
Routing on strategy alone means annotation can never be silently dropped by a
slide-type mismatch, and behaviour is predictable from the strategy map alone.
Pinned by `test_composed_native_diagram_slide_type_uses_content_chrome` (§5.2).

### 2.2 JS assembler wiring (`build_deck.js`)

**Current behaviour (v2):** the annotation routing intercept at lines ~179-186
sends EVERY `native`/`raster` slide to `buildNativeAnnotatedSlide` (pure figure,
chrome dropped) — wrong for composed.

**Change — split the intercept by placement zone (derived from strategy):**

```js
const annotationMode = annotationEntry?.annotation_mode || 'none';
if ((annotationMode === 'native' || annotationMode === 'raster') && imageData) {
    // F-02: placement zone is derived HERE, from the effective strategy,
    // and passed down. The builders never resolve it from the payload or
    // the manifest entry.
    const placementZone = (strategy === 'composed')
        ? 'annotated_image_zone' : 'annotated_full_slide';
    if (placementZone === 'annotated_image_zone') {
        // Composed: keep chrome, overlay into the image zone.
        const annotationPayload = annotationMode === 'native'
            ? loadAnnotationPayload(imageData) : null;
        // F-10: a composed native slide whose image file is missing would
        // silently discard the payload inside buildContentSlide (hasImage
        // false) -- warn loudly at the routing site.
        if (annotationPayload && !fs.existsSync(resolveImagePath(imageData.file_path))) {
            console.warn(`Slide ${slideData.slide_number}: annotation payload present ` +
                         `but base image file is missing -- overlay will not be drawn`);
        }
        buildContentSlide(pptx, slideData, {
            palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN,
            logoPath, hasLogo, noteData, imageData, annotationPayload,
        });
    } else {
        // Full-slide: pure figure (v2), plus the new headline opt-in (§3).
        // F-04: the headline band is NATIVE-only, matching the schema text.
        buildNativeAnnotatedSlide(pptx, slideData, {
            palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H,
            noteData, imageData, annotationMode,
            placementZone,   // F-02: strategy-derived, always 'annotated_full_slide' here
            showHeadline: annotationMode === 'native'
                && annotationEntry?.annotation?.show_headline === true,
        });
    }
    continue;
}
```

**F-02 — deliver the single-sourcing keystone inside `buildNativeAnnotatedSlide`
too.** v2's builder currently resolves its zone from
`payload?.placement_zone || imageData?.placement_zone || 'annotated_full_slide'`
(build_deck.js line ~1230) — a reachable defect once the bridge starts writing
`annotated_image_zone`: if the operator later overrides a composed slide's
strategy to `full_bleed`, the stale payload value would contain-fit the figure
into the right-column rect on a full-slide build. T2 **deletes** that fallback
chain: the builder takes `ctx.placementZone` (strategy-derived at the routing
site, per the snippet above) and resolves the rect from it alone;
`resolveAnnotationZoneRect` keeps its value→rect mapping but its input now comes
only from the caller. Since composed routes to `buildContentSlide` in v2.1,
`buildNativeAnnotatedSlide` only ever receives `annotated_full_slide` — the
parameter exists for explicitness and future zones. Pinned by
`test_js_full_slide_ignores_stale_payload_zone` (§5.3).

**F-01 — composed fit-rect dimension source.** `buildContentSlide` computes its
contain fit from `imageData.dimensions` with a **1024×576 fallback** (line
~485). Step 4.8's manifest append currently writes NO `dimensions` field, so a
non-16:9 base (external source images are first-class) would be silently
mis-fitted — and the overlay mapped against the wrong rect. Two-part fix:

- **Assembler (T2):** when `ctx.annotationPayload` is present, the image block
  prefers `annotationPayload.image_dimensions` (payload-required, always real —
  `build_annotation_payload` reads them via `get_dimensions`) over
  `imageData.dimensions` for the fit computation.
- **Bridge (T6):** Step 4.8's manifest entry gains
  `"dimensions": {"width": ..., "height": ...}` (already computed in its step
  3), AND the `raster`-flow manifest entry gains the same field — raster
  composed has no payload, so the manifest is its only dimension source.

The python path is unaffected: `_place_contain_fit_picture` reads real
dimensions from the file via `get_dimensions` — noted for parity.

**Change — `buildContentSlide` gains an optional `annotationPayload` in `ctx`.**
Its image-placement block (lines ~476-509) already computes an aspect-preserving
contain-fit `(imgX, imgY, imgW, imgH)` inside `imgZone` — with the F-01 change,
the native ratio comes from `ctx.annotationPayload?.image_dimensions` first,
then `imageData.dimensions`, then the 1024×576 fallback. Add, immediately after
the existing `slide.addImage({...})` call:

```js
if (ctx.annotationPayload) {
    drawAnnotations(pptx, slide, ctx.annotationPayload,
                    { x: imgX, y: imgY, w: imgW, h: imgH },
                    slideData.slide_number);
}
```

`drawAnnotations` is the v2 renderer, unchanged — it takes a `fitRect` and
paints leaders/casing/dots/labels tagged with the `annotation_*` `objectName`
prefixes. The composed image zone's contain-fit rect IS that `fitRect`. No new
drawing code.

- **`raster` composed** carries no payload → `annotationPayload` is `null` →
  `buildContentSlide` places the already-labelled PNG contain-fit exactly as it
  does today (its image block is already aspect-preserving, so baked labels are
  never cropped). This is the correct behaviour with zero extra work.
- **Chrome parity:** because composed native/raster now flows through
  `buildContentSlide`, headline, body, accent bars, and footer logo are
  identical to a non-annotated composed slide — the whole point of the feature.

### 2.3 python-pptx template assembler wiring (`build_deck_template.py`)

**Current behaviour (v2):** the annotation block (lines ~560-597) short-circuits
BEFORE normal placeholder population, always passes `(0, 0, slide_w, slide_h)`
as the zone rect, and `_apply_native_annotation` strips ALL shapes (pure figure).

**Change — branch the annotation block on placement zone (from strategy).** The
strategy-map loop (lines ~533-539) already has `entry`; capture the effective
strategy alongside the mode:

```python
# in the strategy-map loop:
annotation_mode = entry.get('annotation_mode')
if annotation_mode in ('native', 'raster'):
    effective = entry.get('speaker_override') or entry.get('strategy')
    annotation_slides[entry['slide_number']] = (annotation_mode, effective)
    # also capture the show_headline flag for §3:
    show_headline = bool((entry.get('annotation') or {}).get('show_headline'))
    annotation_headline_slides[entry['slide_number']] = show_headline
```

In the per-slide block, split on `effective == 'composed'`:

- **`annotated_full_slide` (non-composed):** unchanged v2 path — pure figure,
  `_apply_native_annotation(..., (0, 0, slide_w, slide_h))` (plus headline band,
  §3).
- **`annotated_image_zone` (composed):** DO NOT strip chrome. Instead:
  1. Resolve the layout name + `profile_layout`
     (`_get_mapped_layout_name` / `_get_profile_layout`) — same as the normal
     composed path (lines ~611-612).
  2. Populate title + body placeholders (reuse the exact logic at lines
     ~615-624: `_populate_text(title_ph, headline)`, `_populate_body_points`).
  3. Resolve `zone_rect_emu` via a **defined fallback chain (F-06)** — layouts
     mapped for `content` routinely carry only title+content placeholders, so a
     missing picture placeholder must be handled now, not deferred:
     1. `_find_placeholder_by_type(slide, 'picture', profile_layout)` — when
        found, `zone_rect_emu = (ph.left, ph.top, ph.width, ph.height)`; remove
        the empty placeholder element
        (`ph._element.getparent().remove(ph._element)`) so no unfilled
        placeholder ships.
     2. Else the **content placeholder rect from `profile_layout`** — the same
        `placeholders[].type == 'content'` lookup `_emit_smartart_placeholder`
        already uses (build_deck_template.py lines ~457-462), converted via
        `Inches(...)`.
     3. Else the **hardcoded default rect** `_emit_smartart_placeholder` falls
        back to: `(Inches(0.6), Inches(2.3), Inches(12.13), Inches(4.57))`
        (line ~465).
     Whenever step 1 misses, print a stderr warning naming the slide and which
     fallback was used. Implementation note: extract this chain as a small
     helper (e.g. `_resolve_annotation_zone_rect(slide, profile_layout)`) so
     the fallback logic isn't duplicated inline. Pinned by
     `test_composed_native_no_picture_placeholder_falls_back` (§5.2).
     (When the figure lands in the content rect, body_points may sit behind it
     — layouts without a picture placeholder are single-column; the warning
     gives the operator the signal to pick an image-bearing layout mapping.)
  4. Draw the figure into that rect via a **chrome-preserving** overlay call:
     - **native:** `_apply_native_annotation(slide, abs_image_path, payload,
       slide_w, slide_h, zone_rect_emu, strip_chrome=False)`.
     - **raster / no-payload:** `_place_contain_fit_picture(slide,
       abs_image_path, zone_rect_emu, strip=False)`.
  5. Speaker notes; `continue`.

**Two small helper-signature changes (the only new plumbing):**

- `_place_contain_fit_picture(slide, image_path, zone_rect, *, strip=True)` —
  when `strip=False`, skip the strip-all-shapes step; still contain-fit into
  `zone_rect` and hoist the picture behind any later-added overlay shapes but
  IN FRONT of the background (append order after placeholders is sufficient —
  overlay shapes added afterward land on top). Full-slide callers keep
  `strip=True` (default) → byte-identical to today.
- `_apply_native_annotation(..., *, strip_chrome=True)` — passes `strip_chrome`
  through to `_place_contain_fit_picture`. When `False`, the picture is placed
  without stripping the populated title/body placeholders. The hash gate, the
  geometry precompute, and the draw passes are byte-identical to v2.

### 2.4 QA — no new checks; one small routing addition (F-08)

`run_qa` routes on `annotation_mode == 'native'` (lines ~127-155). A composed
native slide takes that branch and gets IMAGE_QUALITY + KEYNOTE + AN-01/02/03 +
STRUCTURAL (with `exempt_shape_name_prefixes = ['annotation_']`). Consequences,
verified against the check code:

- **AN-01/02/03 are zone-agnostic** — they select `annotation_*`-named shapes and
  count/compare against `payload.labels`, independent of whether the figure fills
  the slide or a column. They work unchanged for composed. **No per-zone variant
  and no new check are needed** (answers the brief's "do AN-01/02/03 apply
  per-zone?" — yes, unchanged).
- The composed slide's **real headline + body** are NOT `annotation_`-prefixed,
  so the exemption does NOT skip them — structural checks (min font, text
  density) validate the chrome normally. Correct.
- **AN-03 bounds** stays `[0, slide_w] × [0, slide_h]`. A composed label placed
  in the left margin could visually overlap body text; that is a placement
  nicety, not a bounds violation. Left as-is (see OQ-1).

**F-08 — visual checks for composed-zone native slides.** The `run_qa` native
branch runs IMAGE_QUALITY + KEYNOTE + STRUCTURAL(+exemption) + AN checks but
**no VISUAL_CHECKS** — acceptable for a pure figure, but a composed native
slide has real chrome that its plain-composed siblings get visually checked
for. Adopt (cheap): in the native branch, when the slide's effective strategy
is `composed`, additionally run VISUAL_CHECKS with the same
`annotation_exempt_cfg` (mirroring the invocation the composed strategy branch
uses). Full-slide native slides stay VISUAL_CHECKS-free, as v2 shipped. Folded
into T8 (which therefore DOES carry one small production change). Pinned by
`test_composed_native_runs_visual_checks` (§5.4).

`raster` composed slides carry `annotation_mode: raster`, so they fall to the
strategy-based branch (composed → structural + image + keynote + visual)
exactly as any composed slide. No AN checks (no payload) — correct.

**F-09 (pre-existing defect, noted as follow-up — NOT v2.1-blocking):** AN-01's
hash gate hashes `image_entry['file_path']` without resolving it against
`deck_dir` (annotation_checks.py lines ~81-87); a relative manifest path raises
`OSError` and the hash check silently skips. File a separate issue; do not fix
in this release (it predates v2.1 and touches the v2 test surface).

### 2.5 Bridge — set the composed placement zone

The bridge's Step 4.8 payload build (SKILL.md lines ~954-996) currently hardcodes
`placement_zone="annotated_full_slide"` with a "composed deferred" comment.
Change: derive it from the slide's base strategy —
`"annotated_image_zone" if effective_strategy == "composed" else
"annotated_full_slide"` — in both the `build_annotation_payload(...)` call and
the in-memory manifest append. This keeps the payload's `placement_zone`
consistent with the assembler's strategy-derived decision (they must agree; the
assembler does not trust the payload for routing, but AN/debugging read it).

**F-01 (bridge half):** the Step 4.8 manifest append additionally writes
`"dimensions": {"width": width, "height": height}` (from its step 3), and the
`raster`-flow manifest entry gains the same field (dimensions of the BAKED
labelled PNG, read via `get_dimensions`) — the raster path has no payload, so
the manifest is the JS assembler's only real-dimension source for the
contain fit.

### 2.6 iterate-slide — already covered

`annotation_refresh_required` (iterate_slide_dispatch.py ~line 574) returns
`True` for `annotation_mode == "native"` regardless of placement zone, so
composed native slides already trigger the mandatory anchor-pass + payload
rewrite on image replacement. Raster composed has no payload → no refresh, as
intended. **No code change**; add one sentence to the iterate-slide SKILL note
clarifying the guard applies to composed native slides too (T7).

---

## 3. Feature B — headline opt-in on native-annotated (full-slide) slides

### 3.1 Schema surface — `annotation.show_headline` (justified)

**Field:** `show_headline` (boolean, default `false`) on the strategy-map slide
entry's **`annotation` object** (`strategy_map.schema.json`).

**Why the `annotation` object, not the payload, not a top-level entry key:**

- **Not the payload.** `annotations.schema.json` is the *resolved image
  coordinate* contract — it carries only what is derived from the base image
  (anchors, label positions, dimensions, hash, vector style). A chrome toggle is
  not image-derived; putting it there would force the bridge to plumb a
  presentation choice through the coordinate builder and would muddy the "pure
  resolved coordinates" invariant that makes the overlay renderer a pure
  painter. **The payload and the bridge stay entirely unchanged for Feature B.**
- **Not a new top-level entry key.** `annotation_mode` is already the top-level
  discriminator; the request detail (`labels`, `source_image_path`, `style`)
  lives inside `annotation`. `show_headline` is request detail — it belongs with
  its siblings. Both assemblers already load the `annotation` object, so no new
  read plumbing.
- **The headline TEXT is sourced from the outline** (`slideData.headline` /
  `slide_data['headline']`), already available in both assemblers. `show_headline`
  is a pure toggle; no text duplication. (A custom headline string override is
  out of scope — see OQ-2.)

Schema diff (add inside the existing `annotation` object's `properties`):

```jsonc
"show_headline": {
  "type": "boolean",
  "default": false,
  "description": "Native full-slide annotation only: when true, render the slide's outline headline in a top band above the contain-fit figure. Default false = pure figure (v2 F2 contract). Ignored for composed (annotated_image_zone) slides, which always carry their own headline."
}
```

No conditional change is needed — `show_headline` is an optional boolean that
only takes effect for `native` + `annotated_full_slide`; the assembler ignores
it otherwise. Backward compatible: absent ⇒ `false` ⇒ v2 pure figure.

### 3.2 Geometry — top band + shrunk contain-fit zone

A single constant governs the band: `HEADLINE_BAND_FRAC = 0.14` (≈ 1.05" at
7.5" slide height — close to `buildContentSlide`'s heading zone). When the
headline is shown, the figure's placement zone shrinks from the full slide to
the region below the band:

```
band_h = SLIDE_H * HEADLINE_BAND_FRAC
figure zone Rz = (0, band_h, SLIDE_W, SLIDE_H - band_h)     # was (0, 0, W, H)
```

The contain-fit math (v2 §3.2) then runs against this reduced `Rz` unchanged.
Because anchors and `label_pos` are image-normalized, they map into the new
(smaller, lower) fit rect automatically — anchor VALIDITY is unaffected (they
are relative to the image, never the slide). Label boxes reposition
proportionally; AN-03 still guards on-slide bounds.

The band itself is a headline text box spanning `(0, 0, SLIDE_W, band_h)`,
brand-styled from the style guide (heading font/size/colour), left-padded by the
slide margin. **Background (F-05):** the JS builder's existing letterbox fill
covers only `zoneRect` (build_deck.js lines ~1242-1245) — under the shrunk
Feature-B zone the band would sit on white canvas, a visible seam on non-white
brand backgrounds. In `showHeadline` mode the JS builder therefore paints a
**full-slide** `palette.background` fill `(0, 0, SLIDE_W, SLIDE_H)` FIRST (in
place of the zone-only fill; the fill is gated on `showHeadline` so the default
path stays byte-parity with v2). The python template path inherits the layout
background and needs no change. Footer logo and body remain OFF — the opt-in
adds a headline ONLY.

**No-image fallback + `showHeadline` (F-05):** when the base image file is
missing, `buildNativeAnnotatedSlide` today sets `slide.background =
palette.primary` (lines ~1260-1263). With `showHeadline` true, the headline
band + `native_headline_*` textbox are STILL drawn over that fallback
background (headline text colour falls back to a light tone readable on
`palette.primary`) — the headline is chrome, independent of the figure, and
dropping it silently would hide the only identifying text on an already-broken
slide. Same rule for the python payload-absent path (§3.4, F-12).

### 3.3 Shape naming and QA

The headline text box is named **`native_headline_<slide_number>`** —
deliberately **NOT** `annotation_`-prefixed. Consequences:

- AN-01's exact-count prefixes (`annotation_label_/leader_/dot_/casing_/dotring_`)
  do NOT include it → headline never disturbs annotation counts.
- The `run_qa` native branch exempts only `annotation_`-prefixed shapes from
  structural checks, so `native_headline_*` **is** checked normally (min font
  size, etc.) — correct, it is real presentation text. Headline size is heading
  scale (≥ the AP-02 floor), so it passes.
- **No new QA check is needed.** (If `show_headline` is true but the outline
  headline is empty, the assembler logs a warning and draws no band — see OQ-3.)

### 3.4 Both assembler paths

**Mode gate (F-04):** the band is **`native`-only in BOTH paths**, matching the
schema description. The JS routing site computes `showHeadline` as
`annotationMode === 'native' && annotation.show_headline === true` (§2.2
snippet); the python caller only passes `headline_text` on the native branch —
the raster branch never sees it. A `raster` slide with `show_headline: true`
renders identically to one without (flag ignored, no band). Pinned in both
paths by the §5 raster+show_headline tests.

**JS (`buildNativeAnnotatedSlide`, full-slide branch only):** accept
`ctx.showHeadline`. When `showHeadline && slideData.headline`:

1. `const bandH = SLIDE_H * HEADLINE_BAND_FRAC;`
2. Shrink the zone rect passed to `computeContainFit`:
   `zoneRect = { x: 0, y: bandH, w: SLIDE_W, h: SLIDE_H - bandH }` for the base
   image; the background fill covers the FULL slide in this mode (F-05, §3.2)
   rather than only the zone rect.
3. After the image + overlay passes, `slide.addText(slideData.headline, {...
   fontFace: typo?.heading_font, fontSize: heading size, bold: true,
   objectName: 'native_headline_' + slideData.slide_number })` in the band.

   *(Note: `buildNativeAnnotatedSlide`'s ctx does not currently include `typo`;
   add `typo`/`slidePalette` to the ctx passed at the routing site so the
   headline can be brand-styled. Falls back to sane defaults if absent.)*

**python-pptx (`_apply_native_annotation`):** add `headline_text=None` kwarg.
When set (and non-empty):

1. `band_h = int(slide_h * HEADLINE_BAND_FRAC)`.
2. Compute the reduced zone rect from the incoming `zone_rect_emu`:
   `(zx, zy + band_h, zw, zh - band_h)` and use it for the contain-fit picture
   and coordinate mapping (the picture strip/place already happens first; the
   reduced rect simply feeds `_place_contain_fit_picture`).
3. After the draw passes, add a textbox at `(zx, zy, zw, band_h)` with the
   heading style, `name = f"native_headline_{slide_number}"`.

The template-mode caller (`build_deck_template.py`'s `build_deck`, full-slide
native branch — F-12 typo corrected) passes
`headline_text = slide_data.get('headline') if show_headline else None`. Default
(`None`) ⇒ byte-identical to v2 pure figure.

**Payload-absent native slide + `show_headline` (F-12):** the python
payload-absent fallback (build_deck_template.py lines ~576-585) calls
`_place_contain_fit_picture` directly, bypassing `_apply_native_annotation` —
so a naive implementation would drop the band. The headline is chrome,
independent of the payload: the fallback path MUST also honour `show_headline`
— contain-fit the picture into the reduced zone `(0, band_h, slide_w,
slide_h - band_h)` and add the `native_headline_*` textbox, exactly as the
payload-present path does. Simplest implementation: extract the band-drawing +
zone-shrink into a tiny shared helper both the fallback and
`_apply_native_annotation` call. Pinned by
`test_native_headline_survives_payload_absent_fallback` (§5.2).

### 3.5 iterate-slide — chrome-only, no invalidation

Toggling `show_headline` or editing the headline text changes chrome, not the
base image → the base image hash is unchanged → the payload stays valid.
**No anchor refresh, no payload rewrite** — only reassembly. Add one sentence to
the iterate-slide SKILL note stating that headline changes on native slides are
chrome-only and do not trigger the F4 invalidation guard (which fires only on
base-image replacement).

---

## 4. Cross-cutting notes

### 4.1 Placement-zone single-sourcing (recap)

Routing decision = effective base strategy, both assemblers. Payload
`placement_zone` = bridge-written, kept consistent, used only as informational /
cross-check data. This is the design's load-bearing consistency rule; the schema
already carries both `annotated_full_slide` and `annotated_image_zone` enum
values (no schema change for the zone vocabulary).

### 4.2 What is explicitly UNCHANGED

`annotations.schema.json`; `annotation_payload.py` (`build_annotation_payload`,
`write_annotation_payload`, `estimate_label_box`, `segment_box_entry`);
`annotate_figure.py`; `annotation_checks.py` (AN-01/02/03 check functions —
the F-09 relative-path defect is a separate follow-up issue);
`iterate_slide_dispatch.py` guard logic; the `drawAnnotations` /
`_apply_native_annotation` draw passes. Feature A touches assembler routing +
`_place_contain_fit_picture`/`_apply_native_annotation` signatures +
`buildContentSlide` ctx + one F-08 line in `run_qa`'s native branch
(VISUAL_CHECKS for composed-strategy native slides). Feature B touches one
schema field + the full-slide native builders. That is the entire surface.

### 4.3 Version + marketplace (CI version-match)

- `plugins/jack-tar-deckhand/.claude-plugin/plugin.json`: `1.10.0 → 1.11.0`.
- `.claude-plugin/marketplace.json`: the `jack-tar-deckhand` entry
  `1.10.0 → 1.11.0` (currently at line ~48). The `json-validation` CI job
  asserts plugin.json and the marketplace entry match — bump both in the same
  commit. No other plugin versions change (deckhand-only release).

---

## 5. Test matrix

Mirror v2's `tests/test_annotate_native_assembler.py` (both paths, toolchain
gates) and `tests/test_strategy_map_annotation.py` (schema). All new tests live
under `plugins/jack-tar-deckhand/tests/`.

### 5.1 `tests/test_strategy_map_annotation.py` (extend — schema)
- `test_schema_accepts_native_with_show_headline_true` — `annotation.show_headline: true` on a full_bleed native slide validates.
- `test_schema_accepts_annotation_without_show_headline` — omitted ⇒ valid (default false; backward-compat pin).
- `test_schema_rejects_non_boolean_show_headline` — `show_headline: "yes"` rejected.
- `test_schema_accepts_native_on_composed_with_annotation` — composed + native + `annotation` already validates (regression pin that composed remains legal for annotation).

### 5.2 `tests/test_annotate_native_assembler.py` (extend — python-pptx path, no toolchain gate)

Composed (Feature A):
- `test_composed_native_retains_headline_and_body` — a composed native slide has a populated title + body placeholder (chrome NOT stripped) AND the `annotation_*` overlay shapes.
- `test_composed_native_maps_anchor_into_image_zone` — anchor `[0.5, 0.5]` on a 16:9 image maps to the CENTRE of the picture-placeholder rect (EMU tolerance), NOT the slide centre.
- `test_composed_native_removes_empty_picture_placeholder` — no unfilled picture placeholder remains; exactly one `pic` in the zone.
- `test_composed_raster_places_contain_fit_in_zone_no_overlay` — composed raster ⇒ picture contain-fit in the image zone, ZERO `annotation_*` shapes.
- `test_composed_native_exact_shape_counts` — N labels ⇒ exactly N of each `annotation_*` sub-prefix (reuses the v2 count assertion at image-zone scale).
- `test_composed_native_diagram_slide_type_uses_content_chrome` (F-03) — a composed native slide with `slide_type: diagram` renders via content chrome (title + body populated) with the overlay; never the diagram builder path.
- `test_composed_native_no_picture_placeholder_falls_back` (F-06) — a layout with no picture placeholder ⇒ figure contain-fit into the content-placeholder rect (or the hardcoded default when that is also absent), warning emitted, overlay drawn.

Headline opt-in (Feature B):
- `test_native_full_slide_headline_opt_in_adds_band` — `show_headline=true` ⇒ one `native_headline_<n>` textbox at the top band with the outline headline text; figure fit rect is below the band.
- `test_native_full_slide_default_is_pure_figure` — `show_headline` absent/false ⇒ NO `native_headline_*` shape (v2 byte-parity pin).
- `test_native_headline_shrinks_fit_rect` — with the band, the picture's top ≥ `band_h`; anchor `[0, 0]` maps into the reduced rect, not slide origin.
- `test_native_headline_shape_not_annotation_prefixed` — the headline shape name starts `native_headline_`, so AN-01 counts are unaffected.
- `test_raster_show_headline_ignored_no_band` (F-04) — a raster full-slide slide with `show_headline: true` ⇒ NO `native_headline_*` shape (band is native-only).
- `test_native_headline_survives_payload_absent_fallback` (F-12) — native + `show_headline: true` + no payload ⇒ contain-fit picture in the reduced zone AND the `native_headline_*` textbox present (no overlay shapes).

End-to-end (skipif no template fixture):
- `test_build_deck_template_composed_native_end_to_end` — full `build_deck` run: composed native slide has headline + body + figure + overlay; a sibling plain composed slide keeps its chrome (backward-compat).
- `test_build_deck_template_full_slide_native_default_unchanged` — a non-headline native slide is byte-parity with v2 (regression).

### 5.3 `tests/test_annotate_native_assembler.py` (extend — JS path, skipif no node+pptxgenjs)
- `test_js_composed_native_emits_chrome_and_overlay` — subprocess `build_deck.js`; composed native slide OOXML has headline + body text AND N `annotation_label_*` textboxes.
- `test_js_composed_raster_no_overlay_shapes` — composed raster ⇒ contain-fit image, no `annotation_*` shapes.
- `test_js_native_headline_band_textbox` — `show_headline=true` ⇒ a `native_headline_*` textbox with the headline text; label overlay present below the band.
- `test_js_native_headline_absent_by_default` — no `native_headline_*` when the flag is off (v2 parity).
- `test_js_raster_show_headline_no_band` (F-04) — raster + `show_headline: true` ⇒ no `native_headline_*` in the OOXML (parity with the python test).
- `test_js_full_slide_ignores_stale_payload_zone` (F-02) — a payload whose `placement_zone` says `annotated_image_zone` on a slide whose effective strategy is `full_bleed` ⇒ the figure contain-fits the FULL slide (strategy-derived zone wins; payload zone is ignored for routing).
- `test_js_composed_native_fit_uses_payload_dimensions` (F-01) — a non-16:9 base image with a manifest entry lacking `dimensions` ⇒ the composed fit rect matches `payload.image_dimensions`' aspect (not the 1024×576 fallback), and the anchor mapping lands accordingly.
- `test_js_headline_mode_fills_full_slide_background` (F-05) — with `show_headline: true`, a background-fill rect spans the full slide (no unfilled band seam above the zone).

### 5.4 QA / iterate-slide (extend existing suites)
- `test_composed_native_runs_an_checks` (`test_annotation_qa_checks.py`) — AN-01/02/03 fire for a composed native slide exactly as for full-slide (zone-agnostic).
- `test_composed_native_chrome_still_structurally_checked` — the composed slide's real headline/body are NOT exempted (a genuinely deficient body still flags).
- `test_annotation_refresh_required_true_for_composed_native` (`test_iterate_slide_dispatch.py` or the annotation-guard test module) — the F4 guard fires for a composed native slide; still no-ops for composed raster / headline-only changes.
- `test_composed_native_runs_visual_checks` (F-08) — a composed-strategy native slide gets VISUAL_CHECKS findings (e.g. a planted visual defect flags); a full-slide native slide does NOT run VISUAL_CHECKS (v2 parity).

### 5.5 Regression
- Full existing deckhand suite green — v2 native full-slide + academic_figure tests must be byte-parity (default `strip=True` / `show_headline=false` / non-composed routing).
- `plugins/integration_tests/test_plugin_imports.py` green (plugin-tree-only edits).

**Run per plugin, never combined:** `cd plugins/jack-tar-deckhand && python -m pytest tests/` (and the integration suite separately). No cross-plugin change.

---

## 6. Task breakdown (Sonnet-sized)

All paths are `plugins/jack-tar-deckhand/` tree ONLY (issue #145 — root `src/`
is stale; do not touch it). Each DoD includes "flake8 + pre-commit clean;
touched tests green; per-plugin pytest only."

**Inline discipline reminder for every image-touching task prompt:** *Do not
`Read` PNG/JPG/GIF/WEBP/BMP/TIFF files directly. To verify an image, dispatch the
`jack-tar-deckhand:image-reviewer` (Haiku) or `general-purpose` (Sonnet)
subagent — they pull the image into THEIR context and return text.*

| # | Task | Depends on | DoD |
|---|---|---|---|
| T1 | Schema: add `annotation.show_headline` (boolean, default false) to `src/schemas/strategy_map.schema.json` (§3.1). No conditional change | — | §5.1 schema tests green; existing strategy-map tests green. |
| T2 | JS Feature A: routing intercept split by strategy-derived placement zone + missing-image warn (F-10) + `buildContentSlide` `ctx.annotationPayload` overlay call preferring `payload.image_dimensions` for the fit (F-01) + `buildNativeAnnotatedSlide` takes `ctx.placementZone` and DELETES the payload/manifest zone fallback (F-02) (§2.2) | T1 | §5.3 composed + stale-zone + payload-dimensions JS tests green; non-composed native/raster unchanged. |
| T3 | JS Feature B: `buildNativeAnnotatedSlide` `showHeadline` band (shrunk zone + `native_headline_*` textbox), native-only gate at the routing site (F-04), full-slide background fill + no-image-fallback band in headline mode (F-05), pass `typo`/`slidePalette` into ctx (§3.2, §3.4) | T1,**T2** (F-07 — both edit the routing intercept; sequence, don't parallelise) | §5.3 headline + raster-no-band + full-slide-fill JS tests green; default pure-figure byte-parity. |
| T4 | python Feature A: strategy-derived branch in `build_deck` annotation block (keyed on strategy only — F-03 option b); `_place_contain_fit_picture(strip=)` + `_apply_native_annotation(strip_chrome=)`; composed populates title/body; zone rect via the F-06 fallback chain (`_resolve_annotation_zone_rect`: picture ph → content ph → hardcoded default, with warning) (§2.3) | T1 | §5.2 composed + diagram-slide-type + no-picture-placeholder python tests green; full-slide path byte-parity. |
| T5 | python Feature B: `_apply_native_annotation(headline_text=)` band + `native_headline_*` textbox; caller passes headline only on the native branch (F-04); payload-absent fallback honours the band via a shared helper (F-12) (§3.4) | T1,T4 | §5.2 headline + raster-ignored + payload-absent-band python tests green; default byte-parity. |
| T6 | Bridge: Step 4.8 sets `placement_zone` by base strategy (composed ⇒ `annotated_image_zone`); writes `dimensions` into BOTH the Step 4.8 and raster-flow manifest entries (F-01); document `show_headline`; remove the composed-deferral notes (§2.5) | T1 | SKILL.md references correct values/fns; manifest entry snippets carry `dimensions`; no code path broken. |
| T7 | Docs: `/annotate-figure` SKILL — composed mode + headline opt-in section; iterate-slide SKILL — composed native covered + headline chrome-only note (§2.6, §3.5). File the F-09 follow-up issue (AN-01 relative-path hash skip) | T2–T5 | Skills document all three placement/chrome combinations + the no-invalidation headline note; F-09 issue filed. |
| T8 | QA: `run_qa` native branch runs VISUAL_CHECKS for composed-strategy native slides (F-08 — one small production change) + §5.4 tests (AN checks zone-agnostic, chrome checked, F4 guard for composed native) | T2,T4 | §5.4 tests green incl. `test_composed_native_runs_visual_checks`; existing QA + iterate suites green. |
| T9 | Version bump: plugin.json + marketplace.json `1.10.0 → 1.11.0` (lockstep); plugin CLAUDE.md skill-table note; root CLAUDE.md status stanza; retrospective stub `retrospectives/142-annotate-figure-v2.1.md` | T1–T8 | `json-validation` CI (version match) green; `plugins/integration_tests/test_plugin_imports.py` green; git diff is plugins-tree-only. |

**Suggested sequencing (F-07):** T1 → (T2, T4 in parallel) → (T3, T5 in
parallel) → (T6, T7, T8 in parallel) → T9. T3 strictly AFTER T2 — both touch
the JS routing-intercept block.

---

## 7. Out of scope

- **Blank-zone annotation variant** — still a v3 backlog item (v2 §10).
- **AN-04 leader-crossing / label-over-chrome check** — deferred (v2 §10, OQ-1).
- **Custom headline-text override** (a headline string distinct from the outline
  headline) — OQ-2; not needed for the opt-in.
- **Headline opt-in on composed** — meaningless (composed already has a
  headline); the flag is ignored there by design.
- **Slide-type-specific chrome for composed annotated slides** — per the F-03
  ruling (§2.1, option b) ALL composed annotated slides render with
  content_with_image chrome regardless of `slide_type`; per-slide-type chrome
  variants (diagram/data_chart styling) are explicitly not offered.

---

## 8. Open questions

| OQ | Question | Current disposition |
|---|---|---|
| OQ-1 | Should AN-03 (or a new AN-04) warn when a composed label box overlaps the headline/body chrome region — **including the footer-logo rect, which overlaps the bottom of the composed image zone (F-11)** — rather than only checking slide bounds? | **Defer.** Bounds-only for v2.1; a chrome-overlap warning needs the headline/body/footer-logo rects threaded into QA. Backlog with v2's AN-04, with the footer-logo rect explicitly named in that backlog item. Implementer should NOT add it in this release. |
| OQ-2 | Should `show_headline` allow a custom headline string (e.g. `annotation.headline_text`) distinct from the outline headline? | **No for v2.1.** Sourcing from `slideData.headline` keeps the field a pure toggle and avoids a second source of truth. Revisit only if an operator needs a figure caption ≠ slide headline. |
| OQ-3 | `show_headline: true` but the outline headline is empty — warn, or silently draw no band? | **Assembler logs a warning, draws no band** (no `native_headline_*` shape). No QA error (a missing optional band is not a contract breach). Confirm this matches operator expectation during the first dogfood. |
| OQ-4 | Is `HEADLINE_BAND_FRAC = 0.14` robust across the shipped template profiles? | **Assumption**, mirrors `buildContentSlide`'s heading zone. Validate against ≥1 real template fixture in the T4 end-to-end test. (The no-picture-placeholder half of the original OQ-4 is now DECIDED, not open — see the F-06 fallback chain in §2.3.) |

---

## 9. Adversarial review disposition (2026-07-23)

Verdict: GO-WITH-CHANGES — 6 major, 6 minor. All rulings applied; F-03 required
a choice (option b adopted).

| # | Sev | Finding (summary) | Resolution in this doc |
|---|---|---|---|
| F-01 | MAJOR | JS composed fit sourced from `imageData.dimensions` with a 1024×576 fallback, but Step 4.8 writes no `dimensions` — non-16:9 bases silently mis-fitted, overlay mapped against the wrong rect | Adopted as recommended: composed fit prefers `annotationPayload.image_dimensions` (§2.2, T2); T6 writes `dimensions` into BOTH the Step 4.8 and raster-flow manifest entries (§2.5); python parity noted (real `get_dimensions`). Test `test_js_composed_native_fit_uses_payload_dimensions` (§5.3). |
| F-02 | MAJOR | Keystone 2 undelivered: `buildNativeAnnotatedSlide` still resolved its zone from `payload?.placement_zone \|\| imageData?.placement_zone` (build_deck.js ~1230); stale payload zone + strategy override ⇒ full-slide build contain-fits into the right-column rect | Adopted: routing site passes strategy-derived `ctx.placementZone`; the payload/manifest fallback chain is DELETED from the builder; `resolveAnnotationZoneRect` keeps only the value→rect mapping (§2.2, T2). Python full-slide path already hardcodes the full slide — no change. Test `test_js_full_slide_ignores_stale_payload_zone` (§5.3). |
| F-03 | MAJOR | §2.1 said `content` slide-type only, but both routing snippets keyed on strategy — composed+diagram/data_chart annotated slides schema-legal and unspecified | **Option (b) adopted**: EVERY composed annotated slide renders with content_with_image chrome regardless of `slide_type` (§2.1). Rationale: the figure IS the content; `buildDiagramSlide`/`buildDataChartSlide` are manifest-driven with no overlay hook; strategy-only routing means annotation can never be silently dropped. Pinned by `test_composed_native_diagram_slide_type_uses_content_chrome` (§5.2); §7 bullet rewritten to match. |
| F-04 | MAJOR | raster + `show_headline` diverged: JS snippet drew the band, python never did; schema says native-only | Adopted: JS routing site gates `showHeadline` on `annotationMode === 'native'` (§2.2 snippet); python caller passes `headline_text` only on the native branch; mode-gate paragraph added to §3.4. Tests `test_raster_show_headline_ignored_no_band` (§5.2) + `test_js_raster_show_headline_no_band` (§5.3) assert no band in BOTH paths. |
| F-05 | MAJOR | §3.2's letterbox claim false: JS fill covers only `zoneRect` (~1242-1245) — headline band would sit on white canvas (seam on non-white brands); no-image fallback (~1260-1263) + `show_headline` unspecified | Adopted: in `showHeadline` mode JS paints a FULL-slide `palette.background` fill first (gated, preserving v2 byte-parity); no-image fallback still draws the band over `palette.primary` with a readable text fallback (§3.2). Python template mode inherits layout background — no change. Test `test_js_headline_mode_fills_full_slide_background` (§5.3). |
| F-06 | MAJOR | Template no-picture-placeholder fallback deferred to OQ-4, but `content`-mapped layouts routinely lack one — `zone_rect_emu` undefined | Decided now (§2.3): fallback chain picture-ph rect → content-ph rect (same lookup as `_emit_smartart_placeholder`, ~457-462) → hardcoded default `(0.6, 2.3, 12.13, 4.57)` in (~465), stderr warning naming the fallback; extracted as `_resolve_annotation_zone_rect` helper (T4). OQ-4 narrowed to the band-fraction question only. Test `test_composed_native_no_picture_placeholder_falls_back` (§5.2). |
| F-07 | minor | T2 and T3 both edit the JS routing-intercept block — "parallel" invited a merge conflict | Adopted: T3 depends on T2; sequencing rewritten T1 → (T2, T4) → (T3, T5) → (T6, T7, T8) → T9 (§6). |
| F-08 | minor | Composed native slides skipped VISUAL_CHECKS their plain-composed siblings get (run_qa native branch runs none) | Adopted (cheap): native branch additionally runs VISUAL_CHECKS when the effective strategy is `composed`, with the same exempt config; full-slide native stays VISUAL_CHECKS-free (§2.4). Folded into T8 as a small production change. Test `test_composed_native_runs_visual_checks` (§5.4). |
| F-09 | minor | Pre-existing AN-01 defect: hashes `image_entry['file_path']` without `deck_dir` resolution (annotation_checks.py ~81-87) — relative paths silently skip the hash gate | Noted in §2.4 as a follow-up issue, NOT v2.1-blocking (predates this release, touches the v2 test surface). Filing the issue added to T7's DoD. |
| F-10 | minor | JS composed native with a missing image file: `buildContentSlide` sets `hasImage=false` and the payload is silently unused | Adopted: `console.warn` at the routing site when the payload is present but the image file is missing (§2.2 snippet, T2). |
| F-11 | minor | Footer-logo rect overlaps the bottom of the composed image zone — labels can collide with the logo | Named under OQ-1 (§8): the AN-04 backlog item explicitly includes the footer-logo rect among the chrome rects to check. No v2.1 code change. |
| F-12 | minor | Python payload-absent native path bypasses `_apply_native_annotation` — `show_headline` band silently lost; plus "build_deck.py" typo | Clarified (§3.4): the payload-absent fallback MUST honour the band (reduced zone + `native_headline_*` textbox) via a shared helper; typo corrected to `build_deck_template.py`'s `build_deck`. Test `test_native_headline_survives_payload_absent_fallback` (§5.2, T5). |
