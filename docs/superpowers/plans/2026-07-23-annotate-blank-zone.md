# Implementation Plan: annotate-figure blank-zone variant (issue #142, final scope item)

**Feature:** #142 blank-zone ("PR B")
**Branch:** `feat/annotate-blank-zone` — cut from `main` AFTER PR #148 (v2.1) merges
**Status:** Design (implementation-ready). DESIGN ONLY — no production code in this document.
**Author:** detailed-design lead (Claude)
**Created:** 2026-07-23
**Version target:** jack-tar-deckhand `1.11.0 → 1.12.0` (marketplace lockstep). NOTE for
cross-plan coordination: the edit-tier plan (`2026-07-23-edit-tier.md` PR D) claims
"next available minor at PR-D merge time — expected 1.12.0"; **this PR takes 1.12.0
and PR D shifts to 1.13.0** (PR D's own "next available minor" language already
absorbs this — no edit to that doc required, but its implementer should read this
stanza).
**Parent designs:** [`2026-07-17-annotate-figure-v2.md`](2026-07-17-annotate-figure-v2.md)
(§10 named this the v3 follow-up) · [`2026-07-23-annotate-figure-v2.1.md`](2026-07-23-annotate-figure-v2.1.md)
(conventions followed here)
**Review:** adversarial review 2026-07-23, GO-WITH-CHANGES — all rulings
applied, see §14.

Decisions are tagged **[FIRM]** (settled; implement as written) or
**[CONTINGENT-ON-DOGFOOD]** (the §8 dogfood calibrates them; do not treat the
stated value as final until the dogfood log lands).

---

## 1. Summary

v2/v2.1 place annotation labels in the image's outer **margin bands**
(`place_labels`, 12% strips at each edge) — occlusion-avoiding, but labels sit
*over* whatever the model happened to paint at the edges. The blank-zone
variant closes the loop from the other side: **ask the model to leave a chosen
region of the image deliberately empty, verify it actually did, and place the
labels inside that reserved region.** Three cooperating parts:

1. **Prompt-side directive** — the label-free prompt transform (bridge Step
   4.8 for native; the `/annotate-figure` flow for raster/standalone — BZ-1)
   additionally instructs the model to keep one named region visually quiet.
   A composition directive, **not a hard mask**: models comply partially or
   not at all, and the design assumes that.
2. **Placement preference** — a new deterministic placement function stacks all
   labels inside the reserved zone (leader lines still reach anchors on the
   subject), used when — and only when — the zone verifiably came back clear
   and has capacity for the label count.
3. **Zone verification** — the existing anchor-pass dispatch gains one
   structured question: "is the reserved region actually clear?" On `false`
   (or absent/malformed answer), placement **falls back to the standard v2
   margin-band flow. The feature degrades gracefully; it never blocks and
   never auto-re-renders.**

**The empirical dogfood (§8) is the heart of this feature.** Directive
compliance across local models is unknown; the code surface is deliberately
modest, and the feature is not "done" until a $0 local compliance matrix is
measured and its calibration decisions are folded back in.

What does NOT change: the assemblers (both paths — they are pure
resolved-coordinate painters; `label_pos` flows through unchanged), the QA
checks (AN-01/02/03 — §7.1), `estimate_label_box` / `segment_box_entry`, the
F10/F12 gate posture (everything here is $0 local unless the operator
separately escalates the base image), and the F4 invalidation guard's
PREDICATE (its refresh-instructions constant gains one line — BZ-4, §7.2).

---

## 2. Schema surface — where the operator expresses the blank zone

### 2.1 The field and its vocabulary [FIRM]

One optional enum on the strategy-map slide entry's existing `annotation`
object (`strategy_map.schema.json`):

```jsonc
// inside "annotation": { "properties": { ...
"blank_zone": {
  "type": "string",
  "enum": ["left_third", "right_third", "top_strip", "bottom_strip", "auto"],
  "description": "Optional. Reserve a deliberately empty region of the BASE IMAGE for label placement: the render prompt asks the model to keep this region visually quiet, the anchor pass verifies it came back clear, and labels are placed inside it when it did. Best-effort — on non-compliance (or an external source image with a busy region) placement falls back to the standard margin-band flow. 'auto' resolves from image aspect (resolve_blank_zone). Applies to both 'native' and 'raster' modes; ownership differs — see the mode-ownership note. Absent = v2 behaviour exactly."
}
```

No conditional (`allOf`) change: `blank_zone` is legal wherever `annotation`
itself is legal (which the existing v2 conditional already gates to
`annotation_mode: raster|native`). Absent ⇒ v2/v2.1 behaviour byte-for-byte.

**Mode ownership (BZ-1) [FIRM]:** the field applies to both modes, but the
FLOW that honours it follows the existing bridge routing split —
`native` is honoured by **imagegen-bridge Step 4.8** (§6); `raster` is
honoured **entirely inside the `/annotate-figure` flow** (§4.4), which the
bridge's Step 4 routing already declares self-contained for raster slides.
The bridge never computes raster placements; the annotate-figure flow never
writes a payload. Same field, same semantics, two owners — matching the
routing that already exists.

### 2.2 Vocabulary justification — the F8 collision audit [FIRM]

The v2 doc's F8 finding requires new zone vocabularies to be **distinct from
every existing zone/placement vocabulary** so grep and operator intuition never
cross wires. Audit of the four vocabularies already in play:

| Existing vocabulary | Values | Axis it describes |
|---|---|---|
| payload / manifest `placement_zone` (v2 F8) | `annotated_full_slide`, `annotated_image_zone` | which SLIDE rect the image occupies |
| image-manifest `placement_zone` (Step 4.7 / elements) | `full_bleed`, `background`, … | slide-level placement |
| `background` strategy variants | `left_panel`, `right_panel`, `bottom_bar`, `top_band`, `center_float` | slide TEXT zones over a background |
| `place_labels` internal band names | `top`, `bottom`, `left`, `right` | image margin bands (not operator-facing) |

Chosen values `left_third | right_third | top_strip | bottom_strip`:

- **`_third` / `_strip` suffixes are new** — no overlap with any value above.
  `top_band` was deliberately REJECTED (collides verbatim with the
  `background` variant vocabulary); bare `left`/`right`/`top`/`bottom` were
  rejected (collide with `place_labels`' internal band names and say nothing
  about extent).
- The names describe a region **of the image**, not of the slide — a different
  axis from every slide-level vocabulary, and the suffix encodes the extent
  ("third" of width for the sides — the operator idiom from issue #142's
  "reserve a blank right third"; "strip" of height for top/bottom,
  deliberately NOT "quarter"/"band" so the fraction constant can be tuned
  (§4.1) without falsifying the name).

### 2.3 Who chooses `auto` [heuristic CONTINGENT-ON-DOGFOOD; owner FIRM]

**Owner: the flow that drives the render** — the bridge (Step 4.8) for
`native`, the `/annotate-figure` flow for `raster`/standalone (BZ-1, §4.4) —
resolved BEFORE rendering (the directive needs the concrete zone), via the
same new pure helper in `annotation_payload.py`:

```python
def resolve_blank_zone(requested, image_aspect):
    """'auto' -> a concrete zone; concrete zones pass through unchanged.

    image_aspect = W / H of the intended render (1024x576 default -> 1.78)
    or of the external source image.

        aspect >= 1.0  ->  'right_third'    # landscape: side thirds are wide
                                            # enough for label boxes and stack
                                            # many labels vertically
        aspect <  1.0  ->  'bottom_strip'   # portrait: a side third is too
                                            # narrow in absolute px for wide
                                            # label boxes; a strip is full-width
    """
```

Label count does NOT influence zone choice in this release — capacity is
handled at placement time (§4.2), and a count-driven zone switch would make
the directive depend on data the operator can't see. `right` over `left` is a
deterministic default (labels read after the figure in LTR reading order); the
§8 dogfood measures left-vs-right compliance separately and re-points this
default if the data disagrees.

---

## 3. Prompt-side directive [text patterns FIRM; effectiveness CONTINGENT-ON-DOGFOOD]

### 3.1 Where it is injected

imagegen-bridge Step 4.8, step 1 (the label-free transform — native slides),
and the `/annotate-figure` skill §1 (same transform — raster slides AND the
standalone flow, per the BZ-1 ownership split, §4.4). The directive is
appended **after** the scene description and **before** the existing no-text
negative, so the final prompt tail reads: *scene… + zone directive + "No text,
no labels, no leader lines, no annotations of any kind."*

**External images (`annotation.source_image_path`): no directive** — there is
nothing to prompt. Verification (§5) and zone-preferred placement (§4) still
run: an external image may happen to have a clear region, and the operator may
have chosen it for exactly that reason.

### 3.2 Directive text per zone

Per the F11 doctrine (work WITH model bias; positive space-claiming beats
stacked negatives), each directive is two sentences: one **positive**
composition instruction claiming the non-reserved region for the subject, one
short emptiness clause for the reserved region. No additional negatives are
stacked — the single existing no-text line already covers text.

| Zone | Directive text |
|---|---|
| `right_third` | `Compose the main subject and all scene detail within the left two-thirds of the frame. Keep the right third of the frame plain and empty — clean, uncluttered background with nothing in it.` |
| `left_third` | `Compose the main subject and all scene detail within the right two-thirds of the frame. Keep the left third of the frame plain and empty — clean, uncluttered background with nothing in it.` |
| `top_strip` | `Compose the main subject and all scene detail in the lower three-quarters of the frame. Keep the top of the frame plain and empty — clean open sky or flat background with nothing in it.` |
| `bottom_strip` | `Compose the main subject and all scene detail in the upper three-quarters of the frame. Keep the bottom of the frame plain and empty — clean, plain foreground with nothing in it.` |

These strings live as a dict constant next to the transform documentation in
the two SKILL.mds (they are prose the orchestrator interpolates, not code).
The §8 dogfood may reword them; the *structure* (positive claim + short
emptiness clause, ≤ 2 sentences, before the no-text negative) is FIRM.

**Interaction with the no-text negative:** none by construction — the
directive never mentions text/labels, so it cannot contradict or dilute the
existing negative. Klein-dialect models (exact-spellings prompt dialect, per
the 2026-07-17 benchmark) get the same directive unchanged — it contains no
spelled strings.

---

## 4. Placement preference — payload-builder changes

### 4.1 New placement function [FIRM; fraction constants CONTINGENT-ON-DOGFOOD]

New pure function in `annotate_figure.py` (the placement engine's home),
sibling to `place_labels` — v1's function is NOT modified (its determinism
tests stay untouched):

```python
BLANK_ZONE_RECTS = {           # normalized (x, y, w, h) of the reserved region
    'left_third':   (0.0,  0.0,  0.33, 1.0),
    'right_third':  (0.67, 0.0,  0.33, 1.0),
    'top_strip':    (0.0,  0.0,  1.0,  0.25),
    'bottom_strip': (0.0,  0.75, 1.0,  0.25),
}

def place_labels_in_zone(anchors, image_size, zone, *,
                         font_size_pt, displayed_width_in, pad=0.03):
    """Stack ALL labels inside the reserved zone. Returns the same
    {label: {"anchor": [...], "label_pos": [...]}} shape as place_labels,
    or None when the zone lacks capacity (caller falls back — §4.2).

    font_size_pt / displayed_width_in (BZ-3, BZ-6): the capacity checks
    need real label-box extents via estimate_label_box at the RESOLVED
    style font size (operator-variable, e.g. style.font_size_pt: 14 —
    not derivable from anchors), converted to a normalized fraction of
    the image via the zone-dependent effective displayed width in inches
    (§4.2). Both are required kwargs; the caller (build_annotation_payload
    for native, the annotate-figure flow for raster) always has them.

    Side zones: labels stack VERTICALLY, x centred in the zone, sorted by
    anchor y (tie-break label name) so leaders fan out monotonically —
    crossings are MINIMISED, not eliminated (BZ-5): a far-side anchor
    whose y-order differs from its slot's neighbours can produce a
    crossing; this is an accepted trade of the all-labels-to-one-zone
    design, and §10's tests do NOT pin non-crossing. Slots spaced by the
    v1 estimated box pitch (60px / image height, normalized), centred on
    the anchors' y-centroid, clamped to
    [zone_y + pad, zone_y + zone_h - pad].

    Top/bottom strips: labels spread HORIZONTALLY, y centred in the strip,
    sorted by anchor x (tie-break name), evenly slotted across
    [pad, 1 - pad] as v1's top/bottom spread does.

    Deterministic: same inputs -> same output, exactly like place_labels.
    """
```

Notes:

- **`0.33` / `0.25` are first-pass constants** matching the vocabulary's
  "third"/"strip" reading; the §8 dogfood tunes them against what models
  actually leave clear (a model that honours "right third" often clears
  ~25–40% — the placement rect should sit inside the *reliably* clear part).
- **All labels go to the zone, not just nearby ones** [FIRM]. That is the
  point of a reserved region — guaranteed-empty space. A far-side anchor gets
  a long leader crossing the subject; leaders are 1.5pt with a white casing
  halo and this is the standard cartographic trade. No per-label
  nearest-zone mixing (mixing zone boxes with margin-band boxes would need a
  cross-mode collision pass that v1 doesn't have).

### 4.2 Capacity — preference, not hard assignment [FIRM]

`place_labels_in_zone` computes capacity before placing. All box extents come
from `estimate_label_box(text, font_size_pt)` (inches), converted to a
normalized image fraction via `frac = extent_in / displayed_width_in` (or
`/ displayed_height_in`, derived from `displayed_width_in` and the image
aspect):

- **Conversion basis (BZ-6):** the inches→fraction conversion uses the
  **effective displayed width per placement zone**, NOT a flat 96-dpi
  assumption — a composed `annotated_image_zone` image displays at roughly
  5.7" (≈170 effective dpi for a 1024px base), so a 96-dpi conversion
  under-estimates box fractions and over-estimates capacity, producing
  overlapping labels. The caller passes `displayed_width_in` from a
  per-zone CONSERVATIVE constant map in `annotation_payload.py`:
  `{'annotated_full_slide': 12.0, 'annotated_image_zone': 4.8}` — both
  deliberately BELOW the true 16:9 contain-fit widths (13.33" / ~5.71"),
  because a smaller assumed display width yields LARGER normalized fractions
  and therefore LOWER capacity — errors land on the safe (fallback) side.
  The raster/standalone flow (which bakes at image resolution) passes the
  full-slide constant.
- **Side zones — height AND width gates (BZ-2):**
  - count: `floor(usable_h / slot_pitch)` with `slot_pitch = 60px /
    image_height` normalized (v1's estimated box pitch), `usable_h = zone_h -
    2*pad`;
  - width: the WIDEST label's normalized `estimate_label_box` width must fit
    the zone — `max_box_w_frac <= zone_w - 2*pad` — otherwise the box spills
    out of the reserved region onto the busy subject (or past the image
    edge), and NOTHING downstream catches it (AN-03 only warns on off-SLIDE
    boxes). A long label like "Orchestration Bus" at 18pt is wider than a
    0.33-wide side zone of a 1024px image; the width gate turns that into a
    clean fallback instead of a silent spill.
- **Strips:** `floor(usable_w / max_slot_w)` where `max_slot_w` is the widest
  label's normalized estimated width plus a fixed gap (height fits by
  construction — one box row in a 0.25 strip).

If any gate fails the function returns **None** and the caller falls back to
`place_labels` **for the whole label set** — all-or-nothing, no mixed
placement, one warning logged (`blank_zone 'right_third' lacks capacity for 9
labels (fits 6) — falling back to margin-band placement`, or `widest label
'Orchestration Bus' exceeds side-zone width — falling back`). The payload
records the outcome (§4.3), so the decision is auditable.

### 4.3 `build_annotation_payload` changes + payload schema addition [FIRM]

Two new keyword args (both default `None` ⇒ v2 behaviour and v2 payload shape,
byte-identical):

```python
def build_annotation_payload(..., *, style_overrides=None, style_guide=None,
                             blank_zone=None, blank_zone_clear=None):
    # blank_zone: resolved concrete zone string (never 'auto' here), or None
    # blank_zone_clear: True | False | None — the §5 verification verdict
    ...
    if blank_zone and blank_zone_clear is True:
        placements = place_labels_in_zone(
            anchors, dims, blank_zone,
            font_size_pt=style['font_size_pt'],          # BZ-3: resolved style,
                                                         # overrides already merged
            displayed_width_in=_DISPLAYED_WIDTH_IN[placement_zone],  # BZ-6
        )
        placement_used = 'zone' if placements is not None else 'fallback_margin'
        if placements is None:
            placements = place_labels(anchors, dims)
    else:
        placements = place_labels(anchors, dims)
        placement_used = 'fallback_margin' if blank_zone else None
```

(The style dict is resolved — defaults + `style_overrides` merged — BEFORE
this branch runs, so the capacity math sees the same `font_size_pt` the
assembler will render at; BZ-3.)

`annotations.schema.json` gains one OPTIONAL top-level property (NOT added to
the `required` list — every v2/v2.1 payload on disk stays valid):

```jsonc
"blank_zone": {
  "type": "object",
  "required": ["requested", "resolved", "verified_clear", "placement"],
  "properties": {
    "requested":      {"type": "string",
                       "enum": ["left_third", "right_third", "top_strip", "bottom_strip", "auto"]},
    "resolved":       {"type": "string",
                       "enum": ["left_third", "right_third", "top_strip", "bottom_strip"]},
    "verified_clear": {"type": ["boolean", "null"],
                       "description": "The anchor-pass zone verdict. null = reviewer did not answer / answer unparseable (treated as NOT clear)."},
    "placement":      {"type": "string", "enum": ["zone", "fallback_margin"],
                       "description": "Where labels actually went. 'fallback_margin' = standard v2 place_labels flow (zone not clear, no capacity, or unverified)."}
  }
}
```

Per the F9 rule the block carries no schema defaults: when a blank zone was
requested the code writes ALL four fields; when none was requested the block
is **absent entirely**. The block is audit data — the assemblers never read it
(`label_pos` is already resolved; the painter stays pure).

### 4.4 Raster mode — owned by the annotate-figure flow, NOT the bridge (BZ-1) [FIRM]

The bridge's Step 4 routing already declares that raster slides "stay
entirely inside the v1 `/annotate-figure` flow" with no separate bridge
sub-step — this design **keeps that routing intact** rather than growing a
raster branch in Step 4.8. The `/annotate-figure` flow itself honours
`blank_zone`, in all three of its invocation contexts (standalone, raster
deck slides, and any operator-manual run):

1. **§1 (base image):** the same zone directive (§3.2) is appended for
   generated images; external images skip it — identical rule to native.
2. **§2 (anchor pass):** the SAME amended output contract as §5.1 — the
   dispatch prompt's enumerated JSON shape includes the `blank_zone` field,
   and the flow calls `parse_blank_zone_verdict` on the response. Without
   this, `blank_zone_clear` could never be `True` for raster and the field
   would be dead on one of its two advertised modes. This amendment to
   annotate-figure SKILL §2 is explicitly in scope (T5).
3. **§3 (overlay):** on `clear: true`, compute placements via
   `place_labels_in_zone(...)` (same kwargs; `displayed_width_in` = the
   full-slide constant, §4.2) and pass them to `annotate()` as explicit
   per-label `{"anchor": ..., "label_pos": ...}` dicts (the
   explicit-placement path the skill's §3 already documents). On
   `clear` false/absent or capacity `None` → omit explicit placements and
   let `annotate()` run its standard margin-band flow — v1 exactly.

No payload exists for raster; the audit trail is one line in the flow's
delivery report (§5 of the skill): `blank_zone: right_third — honoured` /
`— fallback (zone not clear)`.

---

## 5. Zone verification — reviewer contract addition

### 5.1 One question, folded into the existing anchor pass [FIRM]

No second dispatch. When a blank zone is in play, the anchor-pass prompt
(bridge Step 4.8 step 2 for native; annotate-figure SKILL §2 for
raster/standalone — BZ-1) gains one assessment paragraph, and — critically —
the contract's **enumerated output shape itself is amended** rather than a
second instruction being appended after it (BZ-10: the base contract ends
with "Output ONLY JSON: `{"description": ..., "anchors": ...}`"; a model
obeying that ONLY would silently drop an appended extra field, and a
parser-side miss reads as `None` → fallback → a depressed zone-usage rate
that would pollute the §8 compliance signal). The amended contract:

> […existing anchor instructions…] Additionally: the **<zone phrase>** was
> requested to be kept visually quiet for label placement. Judge whether that
> region is clear: would white label boxes placed there sit over any salient
> object, figure, text, or high-detail structure? Plain backgrounds, open
> sky, water, gentle gradients and soft texture COUNT AS CLEAR; any distinct
> object, subject part, or busy detail extending into the region means NOT
> clear. Output ONLY JSON:
> `{"description": "...", "anchors": {"<Label>": [x, y], ...}, "blank_zone": {"clear": true|false, "notes": "one line"}}`

I.e. the single closing "Output ONLY JSON" line enumerates all THREE keys;
there is never a second, contradictory output instruction in the prompt.
When no blank zone is in play the contract is byte-identical to v2.

Zone phrases: `right third of the frame (x > 0.67)`, `left third of the frame
(x < 0.33)`, `top strip of the frame (y < 0.25)`, `bottom strip of the frame
(y > 0.75)` — kept in lockstep with `BLANK_ZONE_RECTS`, and drift-pinned by a
test that greps both SKILL.mds for the four zone names and the
0.67/0.33/0.25/0.75 phrase fractions (BZ-9; repo precedent: the
catalog-markdown CI drift check).

**Threshold semantics: binary, semantic, occlusion-framed** [FIRM]. The
reviewer (Haiku) cannot do pixel statistics; asking for a 0–1 blankness score
invites confabulated precision. The question is framed as the decision it
feeds ("would label boxes sit over meaningful content?"), with the
count-as-clear list making "quiet ≠ uniform" explicit (a gradient sky is
clear; low-variance-but-salient is not). A programmatic pixel metric is
deliberately NOT a gate in this release — it is recorded during the dogfood
for calibration only (OQ-3).

### 5.2 Parsing and the conservative default [FIRM]

New tolerant helper in `annotate_figure.py`:

```python
def parse_blank_zone_verdict(payload):
    """payload is the parsed anchor-pass JSON. Returns True, False, or None.
    None when the 'blank_zone' key is absent, or 'clear' is missing /
    non-boolean — NEVER raises. Absent/malformed is treated by the caller
    exactly like False: fall back to margin-band placement."""
```

`validate_anchors` already tolerates the extra `blank_zone` key (BZ-7 —
verified: it only inspects the `anchors` member, ignoring unknown top-level
keys), so no relaxation is needed; **T2** keeps the pinning test
(`test_validate_anchors_tolerates_blank_zone_key`) so a future validator
tightening cannot silently break the combined contract. Anchor validation and
zone verification are independent: a failed zone answer never triggers the F5
anchor-failure path — anchors can be perfectly valid while the zone is busy.

### 5.3 Failure semantics — graceful degradation, never block [FIRM]

This is EMPIRICAL territory: models may ignore the directive entirely. The
contract:

| Zone verdict | Action |
|---|---|
| `clear: true` | zone-preferred placement (§4.1); capacity overflow ⇒ margin fallback |
| `clear: false` | standard `place_labels` margin-band placement (v2 exactly) |
| absent / malformed / `null` | same as `false` (conservative) |

- **No automatic re-render.** A busy zone does not consume a render retry, a
  funnel escalation, or any spend — the labels simply go where v2 would have
  put them. If the operator WANTS a re-roll (free, local), that is an
  ordinary manual iteration; the directive travels with the prompt unchanged.
- **No new operator gate.** F10/F12 posture is untouched: the whole flow is
  $0 local; the existing gates fire exactly where they fired before.
- The outcome is visible in the payload's `blank_zone.placement` field and in
  the Step 4.8 step-8 throwaway preview (labels visibly in the zone or in the
  margins), which the operator sees via the existing preview review.

---

## 6. Bridge wiring — Step 4.8 amendments (NATIVE only, BZ-1) [FIRM]

Step 4.8 is entered only by `native` slides; the amendments below touch the
native flow exclusively. Raster slides never reach this step — their
blank-zone handling lives entirely in the `/annotate-figure` flow (§4.4),
matching the bridge's existing Step 4 routing statement that raster stays
entirely inside the v1 `/annotate-figure` flow and needs no separate bridge
step. Amendments to the existing numbered steps (no renumbering):

- **Step 1 (obtain base image):** when `annotation.blank_zone` is set and
  `source_image_path` is absent — resolve `auto` via
  `resolve_blank_zone(requested, intended_aspect)` FIRST, then append the
  §3.2 directive for the resolved zone to the label-free prompt, before the
  no-text negative. External image ⇒ resolve the zone from the image's real
  aspect, skip the directive.
- **Step 2 (anchor pass):** use the §5.1 AMENDED contract — the single
  "Output ONLY JSON" line enumerates `description` + `anchors` +
  `blank_zone` (BZ-10; never a second, appended output instruction); after
  `validate_anchors`, call `parse_blank_zone_verdict` on the same response.
- **Step 5 (build payload):** pass `blank_zone=<resolved>` and
  `blank_zone_clear=<verdict>` through to `build_annotation_payload` (which
  supplies `font_size_pt` from the resolved style and `displayed_width_in`
  from the placement zone — §4.3).
- **Step 8 (preview review):** unchanged. The preview naturally shows where
  labels landed; the pointers-only question already covers "flag any label
  box occluding important content", which doubles as a second-chance catch if
  the zone verdict was wrong.

`/annotate-figure` SKILL.md changes (T5 — this is where the raster and
standalone half of the feature lives, BZ-1):

- **§1** gains the zone-directive rule (resolved zone → §3.2 text appended
  before the no-text negative; external images skip the directive).
- **§2** gains the §5.1 amended anchor-pass contract (three-key enumerated
  output shape) plus the `parse_blank_zone_verdict` step — without this,
  `blank_zone_clear` could never be `True` for raster slides and the field
  would be dead on one of its two advertised modes.
- **§3** gains the zone-preferred overlay rule: on `clear: true`, compute
  `place_labels_in_zone(...)` and pass explicit placements to `annotate()`;
  on `clear` false/absent or capacity `None`, run `annotate()`'s standard
  margin-band flow (v1 exactly).
- A short "Blank-zone variant" section ties it together: the opt-in field,
  the vocabulary, the best-effort framing, the fallback guarantee, and the
  mode-ownership split (native = bridge Step 4.8; raster/standalone = this
  flow).

---

## 7. QA and iterate-slide

### 7.1 QA: zone preference is invisible to QA — by design [FIRM]

**No AN check changes, no new checks.** Rationale: AN-01/02/03 validate the
payload→OOXML contract (counts, verbatim text, on-slide bounds) against
`payload.labels[].label_pos` — which is authoritative REGARDLESS of how it was
chosen. Zone preference is a bridge-time placement decision, fully resolved
before assembly; QA re-checking it would mean re-deriving placement intent
from pixels, which is the reviewer's job (§5), not deck-qa's. The payload's
`blank_zone` block (§4.3) is the audit trail if a human ever asks "why are
these labels in the margins when I requested a zone?". AN-03's bounds check
applies to zone-placed labels unchanged (zone rects are strictly inside
[0,1]² so zone placement can only make AN-03 *less* likely to warn).

### 7.2 iterate-slide: the F4 PREDICATE already covers it; the INSTRUCTIONS constant does not (BZ-4) [FIRM]

A blank-zone re-render replaces the base image ⇒ new `base_image_hash` ⇒ the
existing guard **predicate** fires: `annotation_refresh_required`
(iterate_slide_dispatch.py) returns `True` for **every** `annotation_mode:
native` slide on image replacement, independent of placement zone or
blank-zone request (verified against the v2 T12 implementation and the v2.1
§2.6 confirmation). The predicate needs no change.

**But the guard is not only a predicate.** When it fires, the orchestrator is
surfaced `ANNOTATION_REFRESH_INSTRUCTIONS` (iterate_slide_dispatch.py)
VERBATIM — and that constant enumerates a plain v2 rebuild: anchor pass +
`build_annotation_payload` with no zone question and no
`blank_zone`/`blank_zone_clear` kwargs. An orchestrator following it to the
letter would rebuild a LEGAL v2-shaped payload (absent kwargs are valid) and
**silently revert the slide's labels from the reserved zone to the margin
bands on every iteration** — no warning, no schema violation, nothing for QA
to catch (§7.1 is placement-agnostic by design). The fix is a one-line
extension of the constant:

> …for slides whose `annotation` object carries `blank_zone`, re-run the
> FULL blank-zone sub-steps of Step 4.8 — the amended anchor-pass contract
> including the zone question — and pass `blank_zone` / `blank_zone_clear`
> through to `build_annotation_payload` (a new image means new anchors AND a
> fresh zone verdict; the new render may honour the directive differently).

One test pins that the constant mentions the blank-zone re-run
(`test_annotation_refresh_instructions_mention_blank_zone`, §10.2). The
iterate-slide SKILL note gains the matching sentence (T5, which therefore
carries this one small production change — the v2.1 T8 precedent). Raster
slides: no payload, no guard — unchanged, as today.

---

## 8. Empirical validation plan — the $0 dogfood [FIRM that it gates "done"]

**The feature is NOT declared done until this dogfood's log lands and its
calibration decisions (§8.4) are folded back into the docs/constants.**
Everything is local (Ollama and/or mflux per `local-config.json` /
`detect_any_local_backend`), total spend $0.

### 8.1 Matrix

| Dimension | Values |
|---|---|
| Models (2) | best-available Ollama image model (per local-config) + one mflux entry (`mlx/z-image-turbo` preferred — fastest at ~82 s; `mlx/flux2-klein-4b` if z-image absent) |
| Zones (4) | `left_third`, `right_third`, `top_strip`, `bottom_strip` |
| Scenes (3) | (a) the PoC sailing ship (known-good baseline scene), (b) a cutaway machine/engine (dense central subject), (c) a lighthouse coastal landscape (natural sky/water — easy mode) |
| Directive renders | 2 × 4 × 3 = **24** |
| Control renders | 6 (each scene × model, NO directive — measures natural blankness so directive LIFT is separable from luck) |

~30 renders ≈ 45–90 min of local render time. Fixed seeds where the backend
supports them, recorded in the log either way.

### 8.2 Measurement

Per render, dispatch the §5.1 blankness question via
`jack-tar-deckhand:image-reviewer` (never `Read` the PNGs in the orchestration
session — discipline hook). Record: zone verdict + notes, plus (for
calibration only, OQ-3) a programmatic luminance-stddev + edge-density figure
for the zone rect computed by a small PIL script. The operator spot-checks
every DISAGREEMENT between the reviewer verdict and the programmatic signal,
plus a random 25% of agreements — this measures the reviewer question's
reliability, not just the models'.

**Control protocol (BZ-8):** each control render (no directive) is scored on
ALL FOUR zone questions — one reviewer dispatch per zone, same §5.1 wording —
giving a per-zone natural-blankness rate for that scene×model. **Lift is
computed per-zone against the MATCHING control rate** (e.g. `right_third`
directive compliance minus the controls' `right_third` clear-rate), never
against a pooled control figure — scenes differ systematically in which
regions come back naturally empty (the lighthouse scene's sky clears
`top_strip` for free), and a pooled control would mask exactly the
directive-vs-luck distinction the controls exist to make.

### 8.3 Pass criteria [FIRM]

- **P1 — directive worth advertising:** aggregate directive compliance ≥ 60%
  AND lift over control ≥ +20 points ⇒ docs say "usually honoured"; `auto`
  default confirmed (or re-pointed at the best-complying zone).
- **P2 — coin-flip:** 40–60% compliance ⇒ directive ships unchanged (it is
  free), docs mark it "best-effort; the verification + fallback carry the
  guarantee, not the prompt".
- **P3 — poor compliance:** < 40% aggregate, or any single zone ≤ 1/6 ⇒ the
  design fallback applies: **ship placement-preference + verification only as
  the load-bearing mechanism**, directive documented as best-effort-weak (and
  the failing zone's directive text rewritten or its `auto` eligibility
  dropped). The code surface is IDENTICAL in all three outcomes — only
  documentation, directive wording, `BLANK_ZONE_RECTS` fractions, and the
  `auto` heuristic move.
- **Reviewer-question reliability:** agreement with operator spot-checks
  ≥ 80%; below that, the §5.1 wording is revised and re-measured on the
  existing renders (no new spend).
- **End-to-end:** ≥ 1 full bridge run demonstrating the HONOURED path (labels
  in zone, preview reviewed) and ≥ 1 demonstrating the FALLBACK path
  (deliberately busy zone → margin placement, no block, payload records
  `fallback_margin`).

### 8.4 Outputs

`docs/superpowers/dogfooding/2026-07-XX-blank-zone-compliance.md`: the full
matrix, per-zone/per-model compliance table, control comparison, reviewer
reliability figure, and an explicit CALIBRATION DECISIONS section resolving
every CONTINGENT-ON-DOGFOOD tag in this doc (fractions, directive wording,
`auto` heuristic, docs framing per P1/P2/P3).

---

## 9. What is explicitly UNCHANGED

Both assembler paths in full (`drawAnnotations`, `_apply_native_annotation`,
routing, contain-fit math); `place_labels` itself (new sibling function only);
`estimate_label_box` / `segment_box_entry`; `annotation_checks.py` (AN-01/02/03)
and `run_qa` routing; `iterate_slide_dispatch.py`'s guard PREDICATE
(`annotation_refresh_required` — its `ANNOTATION_REFRESH_INSTRUCTIONS`
constant DOES change, one line, BZ-4/§7.2); the F5 anchor-failure three-way
choice; the F10/F12 gate posture; `image-reviewer.md` (the zone question
rides in the DISPATCH PROMPT, exactly like the anchor contract does — no
agent-definition change, so no Claude Code restart dependency); the bridge's
Step 4 raster routing (raster stays annotate-figure-flow-owned, BZ-1).

---

## 10. Test matrix

All under `plugins/jack-tar-deckhand/tests/`; run per-plugin, never combined.

### 10.1 `test_annotate_figure.py` (extend — placement engine)
- `test_place_labels_in_zone_side_zone_stacks_vertically_sorted_by_anchor_y`
- `test_place_labels_in_zone_strip_spreads_horizontally_sorted_by_anchor_x`
- `test_place_labels_in_zone_positions_inside_zone_rect` (all four zones; every `label_pos` within `BLANK_ZONE_RECTS[zone]` ± pad)
- `test_place_labels_in_zone_is_deterministic` (same inputs ⇒ identical output; dict-order independence via name tie-break)
- `test_place_labels_in_zone_returns_none_over_capacity` (side zone, many labels)
- `test_place_labels_in_zone_returns_none_when_widest_label_exceeds_side_zone_width` (BZ-2 — e.g. "Orchestration Bus" at 18pt vs a 0.33 side zone of a 1024px image ⇒ `None`, no spill)
- `test_place_labels_in_zone_capacity_scales_with_displayed_width` (BZ-6 — same labels, smaller `displayed_width_in` ⇒ lower capacity; the image-zone constant is stricter than the full-slide constant)
- `test_place_labels_in_zone_far_anchor_keeps_anchor_verbatim` (anchor untouched; only `label_pos` moves)
- `test_place_labels_unchanged` (regression pin: v1 function output identical for a fixed fixture)
- `test_parse_blank_zone_verdict_true_false_absent_malformed` (all four → True/False/None/None, never raises)
- `test_validate_anchors_tolerates_blank_zone_key` (BZ-7 — tolerance holds today; the pin guards future validator tightening)

NOTE (BZ-5): no test pins leader NON-CROSSING for zone placement — the
monotone sort minimises crossings but far-side anchors can still produce one;
asserting zero crossings would pin a false invariant.

### 10.2 `test_annotation_payload.py` (extend — builder + schema)
- `test_build_payload_zone_placement_when_clear` (`blank_zone='right_third'`, `blank_zone_clear=True` ⇒ every `label_pos` in the zone rect; `blank_zone.placement == 'zone'`)
- `test_build_payload_falls_back_when_not_clear` (`clear=False` ⇒ output identical to a plain v2 build except the audit block; `placement == 'fallback_margin'`)
- `test_build_payload_falls_back_when_unverified` (`clear=None` ⇒ fallback)
- `test_build_payload_falls_back_on_capacity_overflow` (zone + clear + too many labels ⇒ margin placement + `fallback_margin`)
- `test_build_payload_blank_zone_block_fully_explicit` (all four fields present — F9)
- `test_build_payload_no_blank_zone_block_when_not_requested` (v2 byte-shape pin)
- `test_schema_accepts_payload_without_blank_zone` (v2/v2.1 payloads on disk stay valid)
- `test_schema_rejects_bad_blank_zone_placement_value`
- `test_build_payload_capacity_uses_resolved_font_size` (BZ-3 — a `style_overrides={'font_size_pt': 14}` build fits labels a default-18pt build rejects, or vice-versa: the capacity math sees the MERGED style)
- `test_resolve_blank_zone_auto_landscape_and_portrait` + `test_resolve_blank_zone_passthrough_concrete`
- `test_annotation_refresh_instructions_mention_blank_zone` (BZ-4 — `ANNOTATION_REFRESH_INSTRUCTIONS` names the blank-zone re-run + kwargs; lives in the iterate-slide test module alongside the existing guard tests)

### 10.3 `test_strategy_map_annotation.py` (extend — schema)
- `test_schema_accepts_annotation_blank_zone_all_values` (5 enum values, native + raster)
- `test_schema_rejects_unknown_blank_zone_value` (`"top_band"` — the rejected collision value — is the fixture)
- `test_schema_accepts_annotation_without_blank_zone` (backward-compat pin)

### 10.4 Docs drift + regression
- `test_skill_docs_blank_zone_vocabulary_drift_pin` (BZ-9 — greps BOTH
  SKILL.mds (imagegen-bridge + annotate-figure) for the four zone names AND
  the 0.67/0.33/0.25/0.75 zone-phrase fractions, asserting they match
  `BLANK_ZONE_RECTS`; repo precedent: the catalog-markdown CI drift check)
- Full existing deckhand suite green — v2/v2.1 annotation tests byte-parity
  (no blank zone requested ⇒ identical payloads and identical assembly).
- `plugins/integration_tests/test_plugin_imports.py` green.

No assembler tests: no assembler code changes (zone-placed `label_pos` values
exercise the existing mapping tests' coordinate range unchanged).

---

## 11. Task breakdown (Sonnet-sized)

All paths `plugins/jack-tar-deckhand/` tree ONLY (issue #145 — root `src/` is
stale; do not touch it). Each DoD includes "flake8 + pre-commit clean; touched
tests green; per-plugin pytest only."

**Inline discipline reminder for every image-touching task prompt:** *Do not
`Read` PNG/JPG/GIF/WEBP/BMP/TIFF files directly. To verify an image, dispatch
the `jack-tar-deckhand:image-reviewer` (Haiku) or `general-purpose` (Sonnet)
subagent — they pull the image into THEIR context and return text.*

| # | Task | Depends on | DoD |
|---|---|---|---|
| T1 | Schema: `annotation.blank_zone` enum in `src/schemas/strategy_map.schema.json` (§2.1); optional `blank_zone` block in `src/schemas/annotations.schema.json` (§4.3) | — | §10.3 + schema halves of §10.2 green; existing schema tests green. |
| T2 | Placement engine: `BLANK_ZONE_RECTS` + `place_labels_in_zone(anchors, image_size, zone, *, font_size_pt, displayed_width_in, pad)` (BZ-3 signature) with height + WIDTH capacity gates (BZ-2) and crossings-minimised docstring (BZ-5) + `parse_blank_zone_verdict` + `validate_anchors` tolerance pin (BZ-7 — no relaxation needed, test only) in `src/annotate_figure.py` (§4.1, §4.2, §5.2) | — | §10.1 green incl. the `place_labels` regression pin, the width-gate test, and the displayed-width capacity test. |
| T3 | Payload builder: `resolve_blank_zone` + `_DISPLAYED_WIDTH_IN` per-zone conservative map (BZ-6) + `build_annotation_payload(blank_zone=, blank_zone_clear=)` passing resolved-style `font_size_pt` + `displayed_width_in` through (BZ-3) + audit block in `src/annotation_payload.py` (§2.3, §4.3) | T1, T2 | §10.2 green (incl. the resolved-font capacity test); no-blank-zone byte-shape pin green. |
| T4 | Bridge SKILL (NATIVE flow only, BZ-1): Step 4.8 amendments — directive injection (per-zone texts, §3.2), the AMENDED three-key anchor-pass output contract (§5.1, BZ-10 — single "Output ONLY JSON" line, never an appended second instruction), payload pass-through, external-image no-directive rule (§6) + the BZ-9 SKILL-docs drift-pin test (`test_skill_docs_blank_zone_vocabulary_drift_pin`, both SKILL.mds) | T3 | SKILL references correct fns/values; fallback semantics table present; discipline block intact; drift-pin test green. |
| T5 | `/annotate-figure` SKILL — the raster/standalone half (BZ-1): §1 directive rule, §2 amended three-key anchor contract + `parse_blank_zone_verdict`, §3 zone-preferred explicit-placement overlay rule, "Blank-zone variant" section w/ mode-ownership split (§4.4, §6); iterate-slide: `ANNOTATION_REFRESH_INSTRUCTIONS` one-line blank-zone extension + test (BZ-4, §7.2 — one small production change, v2.1 T8 precedent) + SKILL note sentence | T4 | All three outcomes (honoured / not-clear / over-capacity) documented in the annotate-figure flow; `test_annotation_refresh_instructions_mention_blank_zone` green; F4 note present. |
| T6 | **Dogfood (§8)** — 24 directive + 6 control local renders, reviewer-dispatched measurement, operator spot-checks, compliance matrix, calibration decisions applied back (fractions / wording / auto heuristic / docs framing) | T1–T5 | Dogfood log committed; every CONTINGENT tag resolved; ≥1 honoured + ≥1 fallback end-to-end run recorded. |
| T7 | Version bump: plugin.json + marketplace.json `1.11.0 → 1.12.0` lockstep; plugin CLAUDE.md note; root CLAUDE.md status stanza (incl. the PR-D-shifts-to-1.13.0 note); retrospective stub `retrospectives/142-annotate-blank-zone.md` | T1–T6 | `json-validation` CI green; `git diff --stat` plugins-tree-only (+ marketplace + docs); integration imports green. |

**Sequencing:** (T1, T2 in parallel) → T3 → T4 → T5 → T6 → T7. T6 is the
long pole and the gate — T7 does not start until the dogfood log lands.

---

## 12. Out of scope

- **Hard masks / inpainting** to force the zone empty (the edit-tier PR C/D
  channel is the natural future home; a `blank_zone` + edit combination is a
  post-PR-D idea, not this release).
- **Programmatic blankness as a GATE** — measured for calibration only (OQ-3).
- **Per-label zone assignment / mixed placement** — all-or-nothing by design
  (§4.2).
- **Custom zone rects** (operator-supplied fractions) — the four named zones
  cover the composition idioms; revisit only on operator demand.
- **Cloud-tier compliance measurement** — the dogfood is $0 local by design;
  cloud models' (likely better) compliance is a bonus, not a claim.

## 13. Open questions

| OQ | Question | Current disposition |
|---|---|---|
| OQ-1 | Are `0.33` / `0.25` the right reserved fractions, and should the PLACEMENT rect be inset from the DIRECTIVE region (models blur the boundary)? | CONTINGENT-ON-DOGFOOD (§8.4). First-pass values match the vocabulary's literal reading; expect the dogfood to shrink the placement rect inside the reliably-clear core. |
| OQ-2 | Should a `verified_clear: true` zone relax the step-8 preview review's occlusion question (labels in a verified-empty zone can't occlude)? | Defer — keep the preview question unchanged as a second-chance catch for wrong zone verdicts. Revisit if the dogfood shows the double-check is pure noise. |
| OQ-3 | Should the programmatic PIL blankness metric (luminance stddev + edge density) become a pre-gate before the reviewer question? | Defer — recorded during the dogfood for calibration. Promote only if it agrees with operator judgment better than the reviewer question does. |
| OQ-4 | `auto` on left vs right for landscape — does model compliance actually differ by side? | CONTINGENT-ON-DOGFOOD — both side zones are in the matrix; re-point the default if the data shows a side bias. |
| OQ-5 | Does `blank_zone` deserve surfacing in the strategy-map skill's authoring guidance (when to recommend it — e.g. label count ≥ 4)? | Defer to the first real deck dogfood after this ships; T5 documents the field, recommendation heuristics need field data. |

---

## 14. Adversarial review disposition (2026-07-23)

Verdict: GO-WITH-CHANGES — 4 major, 6 minor. All rulings applied; none
relitigated. The reviewer additionally VERIFIED (no change needed): the F8
vocabulary audit, the no-agent-definition-change mechanism (prompt-injected
contract, v2 precedent), schema cleanliness (no `allOf` change; v2/v2.1
payload compat), AN-check placement-agnosticism, the F4 predicate firing (the
gap was only the instructions constant), version/branch consistency (1.12.0;
PR D absorbs 1.13.0), and external-image coherence.

| # | Sev | Finding (summary) | Resolution in this doc |
|---|---|---|---|
| BZ-1 | MAJOR | Raster wiring contradicted the bridge routing (Step 4 declares raster self-contained in the /annotate-figure flow; §4.4/§6 had the bridge computing raster placements) and the zone question was wired only into Step 4.8 — a branch raster slides never enter, so `blank_zone_clear` could never be True for raster | RULING adopted (reviewer's lean): **raster stays annotate-figure-flow-owned; no bridge sub-step.** §2.1 mode-ownership note added; §4.4 rewritten (flow §1/§2/§3 amendments incl. the amended anchor contract + `parse_blank_zone_verdict`); §6 retitled NATIVE-only, raster bullet removed, annotate-figure SKILL changes enumerated; §3.1 ownership cross-ref; T5 re-scoped to carry the raster/standalone half. |
| BZ-2 | MAJOR | Side-zone capacity was height-only — a wide label (e.g. "Orchestration Bus" ≈ 338px vs a 0.33×1024 zone) spills onto the subject or past the image edge, and nothing downstream catches it (AN-03 warns only on off-SLIDE boxes) | Width gate added (§4.2): widest `estimate_label_box` width (normalized) must fit `zone_w − 2·pad`, else `None` → fallback, mirroring the strips' `max_slot_w` logic; explicit warning text; test `test_place_labels_in_zone_returns_none_when_widest_label_exceeds_side_zone_width` (§10.1); T2 DoD updated. |
| BZ-3 | MAJOR | The FIRM signature `(anchors, image_size, zone, *, pad)` could not implement its own capacity spec — `estimate_label_box` needs the RESOLVED font size (operator-variable, `font_size_pt: 14` is the SKILL's own example), not derivable from anchors | Signature amended [FIRM]: `font_size_pt` + `displayed_width_in` required kwargs (§4.1); `build_annotation_payload` passes the MERGED style's `font_size_pt` (§4.3, with an explicit merge-ordering note); raster flow passes its bake font size (§4.4); test `test_build_payload_capacity_uses_resolved_font_size` (§10.2). |
| BZ-4 | MAJOR | §7.2's "no code change" was wrong in effect: `ANNOTATION_REFRESH_INSTRUCTIONS` is surfaced VERBATIM and enumerates a plain v2 rebuild — an orchestrator following it silently reverts labels to margin bands on every iteration (absent kwargs are a legal v2 shape; no warning, QA placement-agnostic) | §7.2 rewritten: predicate unchanged, INSTRUCTIONS constant gains a one-line blank-zone re-run extension (zone question + kwargs pass-through); "no code change" absolute dropped; §9 unchanged-list corrected; test `test_annotation_refresh_instructions_mention_blank_zone`; folded into T5 (one small production change, v2.1 T8 precedent). |
| BZ-5 | minor | "Leaders never cross" was a false invariant for all-labels-to-one-zone placement (far-side-anchor counterexample verified) | Docstring reworded (§4.1): crossings MINIMISED via monotone sort, possible for far-side anchors — accepted trade; §10.1 carries an explicit NOTE that no test pins non-crossing. |
| BZ-6 | minor | Flat 96-dpi inches→fraction conversion under-estimates box fractions for composed `annotated_image_zone` (~170 effective dpi) → capacity over-estimated → overlapping strip labels | Conversion basis is now the per-placement-zone effective displayed width (§4.2): `_DISPLAYED_WIDTH_IN = {'annotated_full_slide': 12.0, 'annotated_image_zone': 4.8}`, deliberately BELOW the true 16:9 fitted widths so capacity errs low (conservative direction argued in-text); builder supplies it (§4.3, T3); test `test_place_labels_in_zone_capacity_scales_with_displayed_width` (§10.1). |
| BZ-7 | minor | §5.2 said T4 relaxes `validate_anchors`; the task table said T2 — and tolerance already holds (the validator only inspects `anchors`) | §5.2 corrected: tolerance verified as already holding, no relaxation; pointer fixed to **T2**, which keeps the pinning test against future validator tightening (§10.1 note). |
| BZ-8 | minor | Dogfood control protocol under-specified — pooled controls would mask the directive-vs-luck distinction | §8.2 control protocol added: each control render is scored on ALL FOUR zone questions; lift is computed PER-ZONE against the matching control rate, never pooled (scene-systematic natural blankness argued in-text, e.g. lighthouse sky vs `top_strip`). |
| BZ-9 | minor | Zone names + phrase fractions live in two SKILL.mds and `BLANK_ZONE_RECTS` with no drift guard | Drift-pin test added (§5.1, §10.4): `test_skill_docs_blank_zone_vocabulary_drift_pin` greps BOTH SKILL.mds for the four zone names + the 0.67/0.33/0.25/0.75 fractions against `BLANK_ZONE_RECTS` (repo precedent: catalog-markdown drift check); assigned to T4. |
| BZ-10 | minor | Appending "add to your JSON" after a contract ending "Output ONLY JSON: {description, anchors}" invites the model to obey the earlier ONLY and drop the key — a parser-side miss silently depresses zone usage and pollutes the dogfood compliance signal | §5.1 rewritten: the enumerated output shape ITSELF is amended to three keys (`description`, `anchors`, `blank_zone`) on the single closing "Output ONLY JSON" line; no second output instruction ever appears; mirrored in Step 4.8 step 2 (§6) and annotate-figure §2 (§4.4); rationale recorded in-text. |
