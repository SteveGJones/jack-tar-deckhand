// Build script for Variant C — "AI Agents That Actually Work"
// Follows the Brief C marker-placeholder protocol:
//   - IMAGE:<slug> -> dashed rectangle + centered label, shape name = marker
//   - SMARTART:<slug> -> dashed rectangle + centered label, shape name = marker
//   - BG:<slug> -> small corner label rectangle, shape name = marker
//
// Pattern mirrors the worked examples in brief-c-exemplar.md exactly.

const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";       // 10" x 5.625"
pres.author = "AI Agents Talk";
pres.title = "AI Agents That Actually Work";

// ---- Palette: Midnight Executive ----
const NAVY   = "1E2761";
const ICE    = "CADCFC";
const WHITE  = "FFFFFF";
const INK    = "1A1A1A";
const MUTED  = "64748B";

// ---- Helpers ----------------------------------------------------------------

// Marker helpers follow the worked example pattern from the brief:
// dashed F0F0F0/CCCCCC rectangle, shape name = the marker string,
// plus an overlaid text label showing the marker string.

function addImageMarker(slide, opts) {
  const { x, y, w, h, slug } = opts;
  const name = `IMAGE:${slug}`;
  slide.addShape(pres.ShapeType.rect, {
    x, y, w, h,
    fill: { color: "F0F0F0" },
    line: { color: "CCCCCC", width: 1, dashType: "dash" },
    name,
  });
  // Center the label vertically inside the box
  slide.addText(name, {
    x, y: y + h / 2 - 0.25, w, h: 0.5,
    align: "center", color: "888888", fontSize: 14,
  });
}

function addSmartArtMarker(slide, opts) {
  const { x, y, w, h, slug } = opts;
  const name = `SMARTART:${slug}`;
  slide.addShape(pres.ShapeType.rect, {
    x, y, w, h,
    fill: { color: "F0F0F0" },
    line: { color: "CCCCCC", width: 1, dashType: "dash" },
    name,
  });
  slide.addText(name, {
    x, y: y + h / 2 - 0.25, w, h: 0.5,
    align: "center", color: "888888", fontSize: 14,
  });
}

// BG marker follows the brief's worked example exactly: small corner label.
function addBgMarker(slide, slug) {
  const name = `BG:${slug}`;
  slide.addShape(pres.ShapeType.rect, {
    x: 0.2, y: 5.25, w: 1.8, h: 0.3,       // bottom-left corner on 16x9
    fill: { color: "F0F0F0" },
    line: { color: "CCCCCC", width: 1, dashType: "dash" },
    name,
  });
  slide.addText(name, {
    x: 0.2, y: 5.25, w: 1.8, h: 0.3,
    align: "center", color: "888888", fontSize: 10,
  });
}

function addTitle(slide, text) {
  slide.addText(text, {
    x: 0.5, y: 0.3, w: 9, h: 0.8,
    fontSize: 32, bold: true, color: NAVY, fontFace: "Calibri",
    margin: 0,
  });
}

function addBullets(slide, items, opts = {}) {
  const { x = 0.5, y = 1.5, w = 4.5, h = 3.2, fontSize = 18 } = opts;
  const runs = items.map((t, i) => ({
    text: t,
    options: { bullet: true, breakLine: i < items.length - 1 },
  }));
  slide.addText(runs, { x, y, w, h, fontSize, color: INK, fontFace: "Calibri", paraSpaceAfter: 6 });
}

// ---- Slides -----------------------------------------------------------------

// Slide 1 — Title (BG marker, per worked example)
const slide1 = pres.addSlide();
slide1.background = { color: WHITE };
slide1.addText("AI Agents That Actually Work", {
  x: 0.5, y: 2.0, w: 9, h: 1.2,
  fontSize: 48, bold: true, color: NAVY, align: "left", fontFace: "Calibri",
});
slide1.addText("A 20-minute field guide for developers", {
  x: 0.5, y: 3.2, w: 9, h: 0.6,
  fontSize: 20, italic: true, color: MUTED, fontFace: "Calibri",
});
addBgMarker(slide1, "dramatic-opening");

// Slide 2 — Why this talk now
const slide2 = pres.addSlide();
slide2.background = { color: WHITE };
addTitle(slide2, "Why this talk now");
addBullets(slide2, [
  "Agent demos look magical on stage",
  "Production agents quietly fall over",
  "The gap is architecture, not prompts",
  "20 minutes to close it",
]);
addImageMarker(slide2, { x: 5.5, y: 1.5, w: 4, h: 3, slug: "stage-vs-production" });

// Slide 3 — Why most agents fail (mirrors worked example)
const slide3 = pres.addSlide();
slide3.background = { color: WHITE };
addTitle(slide3, "Why most agents fail");
addBullets(slide3, [
  "Prompt engineering hits a ceiling",
  "No persistent memory",
  "Tool use is brittle",
  "No recovery path when steps go wrong",
]);
addImageMarker(slide3, { x: 5.5, y: 1.5, w: 4, h: 3, slug: "agents-failing" });

// Slide 4 — The three pillars (SmartArt)
const slide4 = pres.addSlide();
slide4.background = { color: WHITE };
addTitle(slide4, "The three pillars of a working agent");
slide4.addText(
  "Planning, memory, and tool use — each load-bearing, each a common failure point.",
  { x: 0.5, y: 1.2, w: 9, h: 0.6, fontSize: 18, italic: true, color: MUTED, fontFace: "Calibri" }
);
addSmartArtMarker(slide4, { x: 1.0, y: 2.0, w: 8.0, h: 3.0, slug: "three-pillars" });

// Slide 5 — Pillar 1: Planning
const slide5 = pres.addSlide();
slide5.background = { color: WHITE };
addTitle(slide5, "Pillar 1 — Planning");
addBullets(slide5, [
  "Decompose goals into verifiable steps",
  "Budget tokens and tool calls per step",
  "Always leave a retry path",
  "Let the plan be inspected, not implicit",
]);
addImageMarker(slide5, { x: 5.5, y: 1.5, w: 4, h: 3, slug: "planning-tree" });

// Slide 6 — Pillar 2: Memory
const slide6 = pres.addSlide();
slide6.background = { color: WHITE };
addTitle(slide6, "Pillar 2 — Memory");
addBullets(slide6, [
  "Short-term: scratchpad for the current task",
  "Long-term: retrievable facts + episodes",
  "Evict aggressively; relevance beats recall",
  "Write-through, never write-only",
]);
addImageMarker(slide6, { x: 5.5, y: 1.5, w: 4, h: 3, slug: "memory-layers" });

// Slide 7 — Pillar 3: Tool use
const slide7 = pres.addSlide();
slide7.background = { color: WHITE };
addTitle(slide7, "Pillar 3 — Tool use");
addBullets(slide7, [
  "Narrow, typed, well-named tools",
  "One-shot success rate > tool count",
  "Return structured errors, never stack traces",
  "Treat tools as contracts, not endpoints",
]);
addSmartArtMarker(slide7, { x: 5.5, y: 1.5, w: 4, h: 3, slug: "tool-contract" });

// Slide 8 — Case study: the invoice agent
const slide8 = pres.addSlide();
slide8.background = { color: WHITE };
addTitle(slide8, "Case study: the invoice agent");
addBullets(slide8, [
  "Demo: flawless. Production: 38% failure.",
  "Root cause: no memory of prior invoices",
  "Fix: episodic memory + typed tools",
  "Result: 38% -> 4% after one sprint",
]);
addImageMarker(slide8, { x: 5.5, y: 1.5, w: 4, h: 3, slug: "case-study-chart" });

// Slide 9 — What to do on Monday
const slide9 = pres.addSlide();
slide9.background = { color: WHITE };
addTitle(slide9, "What to do on Monday");
addBullets(slide9, [
  "Instrument your agent's plan — make it visible",
  "Add one memory layer, measure recall accuracy",
  "Rewrite your three worst tool schemas",
  "Pick one failure mode per sprint, kill it",
]);
addImageMarker(slide9, { x: 5.5, y: 1.5, w: 4, h: 3, slug: "monday-checklist" });

// Slide 10 — Call to action + thanks
const slide10 = pres.addSlide();
slide10.background = { color: WHITE };
addTitle(slide10, "Ship agents that actually work");
slide10.addText(
  "Plan visibly. Remember deliberately. Use tools like contracts.",
  { x: 0.5, y: 1.4, w: 9, h: 0.8, fontSize: 24, italic: true, color: NAVY, fontFace: "Calibri" }
);
slide10.addText("Questions?  @your-handle", {
  x: 0.5, y: 4.5, w: 9, h: 0.6, fontSize: 18, color: MUTED, fontFace: "Calibri",
});
addBgMarker(slide10, "closing-glow");

// ---- Write ------------------------------------------------------------------

pres.writeFile({
  fileName: "/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/worktrees/sweet-varahamihira-bdd4cf/docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-c/presentation.pptx",
}).then((fileName) => {
  console.log("Wrote:", fileName);
});
