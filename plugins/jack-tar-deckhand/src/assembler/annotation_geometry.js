/**
 * Shared annotation geometry helpers (issue #142 v2, T4).
 *
 * PORTS of the two Python geometry primitives that both assembler paths
 * (PptxGenJS + python-pptx template) must agree on bit-for-bit:
 *
 *   - segmentBoxEntry  <-> annotate_figure._segment_box_entry
 *                          (re-exported as annotation_payload.segment_box_entry)
 *   - estimateLabelBox <-> annotation_payload.estimate_label_box
 *
 * Design: docs/superpowers/plans/2026-07-17-annotate-figure-v2.md §4.6, §2.3.
 *
 * Plain CommonJS module, no dependencies (matches build_deck.js's module
 * style — see slide_masters.js / progressive_builds.js / optimise.js for
 * the sibling precedent). Cross-path parity with the Python originals is
 * pinned by tests/test_annotation_geometry_parity.py.
 */

'use strict';

// Formula reference point for estimateLabelBox (F13): 7 characters per
// inch at 18pt, scaled linearly by font size. Mirrors the constants in
// annotation_payload.py — NOT the default label font size (that is the
// AP-02 floor, resolved elsewhere).
const ESTIMATOR_REF_CPI = 7.0;
const ESTIMATOR_REF_PT = 18.0;

/**
 * Point where the segment p0 -> p1 first enters an axis-aligned box.
 *
 * Used to terminate a leader line at the edge of its own label box
 * nearest the anchor, instead of drawing into the box interior.
 * Slab-method clip: p1 is expected to be inside the box (the label
 * centre); if the segment never reaches the box (degenerate input),
 * p1 is returned unchanged as a safe fallback. Identical algorithm to
 * annotate_figure._segment_box_entry — see that docstring for the full
 * explanation; this port preserves every edge case, including the
 * anchor-inside-box zero-length collapse.
 *
 * @param {[number, number]} p0 - segment start (the anchor), e.g. inches.
 * @param {[number, number]} p1 - segment end (the label box centre).
 * @param {[number, number, number, number]} box - (left, top, right, bottom).
 * @returns {[number, number]} the entry point on the box perimeter (or p0
 *     if the anchor is already inside the box).
 */
function segmentBoxEntry(p0, p1, box) {
  const x0 = p0[0];
  const y0 = p0[1];
  const x1 = p1[0];
  const y1 = p1[1];
  const dx = x1 - x0;
  const dy = y1 - y0;

  let tMin = 0.0;
  let tMax = 1.0;

  const axes = [
    [dx, box[0], box[2], x0],
    [dy, box[1], box[3], y0],
  ];

  for (const axis of axes) {
    const delta = axis[0];
    const lo = axis[1];
    const hi = axis[2];
    const origin = axis[3];

    if (delta === 0) {
      if (origin < lo || origin > hi) {
        return [p1[0], p1[1]]; // parallel and outside the slab — degenerate
      }
    } else {
      let tA = (lo - origin) / delta;
      let tB = (hi - origin) / delta;
      if (tA > tB) {
        const tmp = tA;
        tA = tB;
        tB = tmp;
      }
      tMin = Math.max(tMin, tA);
      tMax = Math.min(tMax, tB);
    }
  }

  if (tMin > tMax) {
    return [p1[0], p1[1]]; // segment never enters the box — degenerate
  }

  const t = Math.max(0.0, tMin); // anchor inside box -> zero-length leader
  return [x0 + t * dx, y0 + t * dy];
}

/**
 * THE single shared label-box estimator (F13), ported verbatim from
 * annotation_payload.estimate_label_box:
 *
 *     chars_per_inch = 7.0 * (18.0 / font_size_pt)   # 7 cpi at 18pt, linear
 *     text_w_in = len(text) / chars_per_inch
 *     box_w_in  = text_w_in + 2 * pad_in
 *     box_h_in  = (font_size_pt / 72.0) * 1.4 + 2 * pad_in
 *
 * @param {string} text - the label string.
 * @param {number} fontSizePt - label font size, in points.
 * @param {number} [padIn=0.06] - fixed padding in inches on each side.
 * @returns {[number, number]} [boxWIn, boxHIn] in inches.
 */
function estimateLabelBox(text, fontSizePt, padIn) {
  if (padIn === undefined || padIn === null) {
    padIn = 0.06;
  }
  if (fontSizePt <= 0) {
    throw new Error(`fontSizePt must be positive, got ${fontSizePt}`);
  }
  const charsPerInch = ESTIMATOR_REF_CPI * (ESTIMATOR_REF_PT / fontSizePt);
  const textWIn = text.length / charsPerInch;
  const boxWIn = textWIn + 2 * padIn;
  const boxHIn = (fontSizePt / 72.0) * 1.4 + 2 * padIn;
  return [boxWIn, boxHIn];
}

module.exports = { segmentBoxEntry, estimateLabelBox };
