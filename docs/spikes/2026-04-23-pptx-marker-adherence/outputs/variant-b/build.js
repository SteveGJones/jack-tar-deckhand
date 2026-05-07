// Brief B — Explicit marker protocol
// Build 10-slide conference talk "AI Agents That Actually Work"
// Follows the placeholder protocol exactly: IMAGE:, SMARTART:, BG:
//
// Placeholder spec (from brief):
//   - Rectangle, fill F0F0F0, 1pt dashed border CCCCCC
//   - Visible text equal to shape's name
//   - PptxGenJS `name` property set so downstream tool can find it
//   - BG:* is a small ~1.5 x 0.3 in label in bottom-left corner

const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10" x 5.625"
pres.author = "AI Agents That Actually Work";
pres.title = "AI Agents That Actually Work";
pres.subject = "Conference talk — 20 min, developer audience";

// ---- Palette: "Ocean Gradient" (tech-feel, not default blue) ----
const C = {
  deep: "065A82",
  teal: "1C7293",
  midnight: "21295C",
  ink: "1E293B",
  muted: "64748B",
  bg: "FFFFFF",
  sand: "F5F5F5",
  accent: "F96167",
};

const FONT_H = "Georgia";
const FONT_B = "Calibri";

// ---- Helpers ----

// Standard IMAGE: / SMARTART: placeholder rectangle — follows brief spec verbatim.
function addMarkerRect(slide, name, { x, y, w, h, fontSize = 18 }) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    name,
    fill: { color: "F0F0F0" },
    line: { color: "CCCCCC", width: 1, dashType: "dash" },
  });
  slide.addText(name, {
    x, y, w, h,
    name,
    fontFace: "Consolas",
    fontSize,
    color: C.ink,
    align: "center",
    valign: "middle",
    margin: 0,
  });
}

// BG: marker — small ~1.5 x 0.3 in label in bottom-left corner.
function addBgMarker(slide, name) {
  const x = 0.3;
  const h = 0.3;
  const w = 1.5;
  const y = 5.625 - h - 0.2; // bottom-left, ~0.2" from bottom
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    name,
    fill: { color: "F0F0F0" },
    line: { color: "CCCCCC", width: 1, dashType: "dash" },
  });
  slide.addText(name, {
    x, y, w, h,
    name,
    fontFace: "Consolas",
    fontSize: 9,
    color: C.ink,
    align: "center",
    valign: "middle",
    margin: 0,
  });
}

function addFooter(slide, n) {
  slide.addText(`${n} / 10  ·  AI Agents That Actually Work`, {
    x: 0.5, y: 5.3, w: 9, h: 0.2,
    fontFace: FONT_B, fontSize: 9, color: C.muted, align: "left",
  });
}

function addTitle(slide, text, opts = {}) {
  slide.addText(text, {
    x: 0.5, y: 0.35, w: 9, h: 0.75,
    fontFace: FONT_H, fontSize: 34, bold: true,
    color: opts.color || C.midnight,
    align: "left", valign: "middle", margin: 0,
  });
  // subtle accent block (not a line under title — brief "never use accent lines under titles")
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.08, w: 0.5, h: 0.05,
    fill: { color: C.accent }, line: { color: C.accent, width: 0 },
  });
}

// -----------------------------------------------------------------------------
// Slide 1 — Title / opening. Full-bleed atmospheric BG requested.
// -----------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.midnight };

  s.addText("AI Agents That Actually Work", {
    x: 0.7, y: 1.8, w: 8.6, h: 1.2,
    fontFace: FONT_H, fontSize: 48, bold: true, color: "FFFFFF",
    align: "left", valign: "middle", margin: 0,
  });
  s.addText("Building systems that survive contact with production", {
    x: 0.7, y: 3.0, w: 8.6, h: 0.6,
    fontFace: FONT_B, fontSize: 20, italic: true, color: "CADCFC",
    align: "left", margin: 0,
  });
  s.addText("A 20-minute talk for developers", {
    x: 0.7, y: 3.7, w: 8.6, h: 0.4,
    fontFace: FONT_B, fontSize: 14, color: "9BB3E0", align: "left", margin: 0,
  });

  // BG marker — atmospheric opener
  addBgMarker(s, "BG:dramatic-contrast");
}

// -----------------------------------------------------------------------------
// Slide 2 — Hook: most demos fail in production. IMAGE hero.
// -----------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  addTitle(s, "Most agent demos die in production");

  // Left column: big stat + supporting text
  s.addText("~80%", {
    x: 0.5, y: 1.5, w: 4.0, h: 1.4,
    fontFace: FONT_H, fontSize: 84, bold: true, color: C.accent,
    align: "left", valign: "middle", margin: 0,
  });
  s.addText("of polished demos never reach a real user", {
    x: 0.5, y: 2.9, w: 4.0, h: 0.5,
    fontFace: FONT_B, fontSize: 14, italic: true, color: C.muted,
    align: "left", margin: 0,
  });
  s.addText([
    { text: "Brittle prompts, no memory, flaky tools.", options: { bullet: true, breakLine: true } },
    { text: "Demo data is clean; production isn't.", options: { bullet: true, breakLine: true } },
    { text: "Latency and cost compound under load.", options: { bullet: true } },
  ], {
    x: 0.5, y: 3.5, w: 4.0, h: 1.6,
    fontFace: FONT_B, fontSize: 13, color: C.ink, paraSpaceAfter: 4,
  });

  // Right column: IMAGE placeholder (hero illustration of a "broken robot" concept)
  addMarkerRect(s, "IMAGE:demo-vs-production-hero", {
    x: 5.1, y: 1.4, w: 4.4, h: 3.6, fontSize: 14,
  });

  addFooter(s, 2);
}

// -----------------------------------------------------------------------------
// Slide 3 — The three architectural pillars (SMARTART candidate).
// -----------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  addTitle(s, "Three pillars of agents that work");

  s.addText("Planning, memory, and tool use — each non-optional.", {
    x: 0.5, y: 1.15, w: 9, h: 0.4,
    fontFace: FONT_B, fontSize: 14, italic: true, color: C.muted, margin: 0,
  });

  // SMARTART placeholder — the three pillars as a pyramid / relationship diagram
  addMarkerRect(s, "SMARTART:three-pillars", {
    x: 0.8, y: 1.7, w: 8.4, h: 3.3,
  });

  addFooter(s, 3);
}

// -----------------------------------------------------------------------------
// Slide 4 — Pillar 1: Planning. IMAGE architecture sketch.
// -----------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  addTitle(s, "Pillar 1 · Planning");

  // Left: text
  s.addText([
    { text: "Decompose before acting", options: { bold: true, fontSize: 16, color: C.deep, breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "Turn a goal into a graph of sub-goals.", options: { bullet: true, breakLine: true } },
    { text: "Re-plan when the world changes — don't freeze the plan.", options: { bullet: true, breakLine: true } },
    { text: "Make intermediate state inspectable.", options: { bullet: true, breakLine: true } },
    { text: "Budget steps; fail fast when the plan stalls.", options: { bullet: true } },
  ], {
    x: 0.5, y: 1.4, w: 4.3, h: 3.6,
    fontFace: FONT_B, fontSize: 13, color: C.ink, paraSpaceAfter: 4,
  });

  // Right: IMAGE placeholder — architecture sketch of a planner
  addMarkerRect(s, "IMAGE:pillar-planning-architecture", {
    x: 5.1, y: 1.4, w: 4.4, h: 3.6,
  });

  addFooter(s, 4);
}

// -----------------------------------------------------------------------------
// Slide 5 — Pillar 2: Memory.
// -----------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  addTitle(s, "Pillar 2 · Memory");

  // Two-column layout: short/long memory description, then IMAGE on right
  s.addText([
    { text: "Short, long, and sideways", options: { bold: true, fontSize: 16, color: C.deep, breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "Working memory: the live scratchpad.", options: { bullet: true, breakLine: true } },
    { text: "Episodic memory: what happened last time.", options: { bullet: true, breakLine: true } },
    { text: "Semantic memory: facts and embeddings.", options: { bullet: true, breakLine: true } },
    { text: "Forget deliberately — stale context is a bug.", options: { bullet: true } },
  ], {
    x: 0.5, y: 1.4, w: 4.3, h: 3.6,
    fontFace: FONT_B, fontSize: 13, color: C.ink, paraSpaceAfter: 4,
  });

  addMarkerRect(s, "IMAGE:pillar-memory-diagram", {
    x: 5.1, y: 1.4, w: 4.4, h: 3.6,
  });

  addFooter(s, 5);
}

// -----------------------------------------------------------------------------
// Slide 6 — Pillar 3: Tool use.
// -----------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  addTitle(s, "Pillar 3 · Tool use");

  s.addText([
    { text: "Typed interfaces beat prompt tricks", options: { bold: true, fontSize: 16, color: C.deep, breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "Every tool has a schema — validate inputs and outputs.", options: { bullet: true, breakLine: true } },
    { text: "Treat tool errors as signal, not noise.", options: { bullet: true, breakLine: true } },
    { text: "Meter tool calls: rate-limit, cache, retry with backoff.", options: { bullet: true, breakLine: true } },
    { text: "Keep the tool catalogue small enough to reason about.", options: { bullet: true } },
  ], {
    x: 0.5, y: 1.4, w: 4.3, h: 3.6,
    fontFace: FONT_B, fontSize: 13, color: C.ink, paraSpaceAfter: 4,
  });

  addMarkerRect(s, "IMAGE:pillar-tool-use-sketch", {
    x: 5.1, y: 1.4, w: 4.4, h: 3.6,
  });

  addFooter(s, 6);
}

// -----------------------------------------------------------------------------
// Slide 7 — Case study intro.
// -----------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  addTitle(s, "Case study · A support-triage agent");

  s.addText([
    { text: "Context", options: { bold: true, fontSize: 16, color: C.deep, breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "Mid-sized SaaS, ~4,000 tickets/week.", options: { bullet: true, breakLine: true } },
    { text: "Previous rules engine misrouted ~22% of tickets.", options: { bullet: true, breakLine: true } },
    { text: "Agent has 4 tools: classify, lookup-customer, draft-reply, escalate.", options: { bullet: true } },
  ], {
    x: 0.5, y: 1.4, w: 4.3, h: 3.6,
    fontFace: FONT_B, fontSize: 13, color: C.ink, paraSpaceAfter: 4,
  });

  // Right: big stat callout
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.5, w: 4.3, h: 3.4,
    fill: { color: C.sand }, line: { color: "E2E8F0", width: 1 },
  });
  s.addText("22% → 6%", {
    x: 5.2, y: 1.8, w: 4.3, h: 1.2,
    fontFace: FONT_H, fontSize: 54, bold: true, color: C.deep,
    align: "center", valign: "middle", margin: 0,
  });
  s.addText("Misroute rate after rollout (8 weeks)", {
    x: 5.2, y: 3.0, w: 4.3, h: 0.4,
    fontFace: FONT_B, fontSize: 12, italic: true, color: C.muted,
    align: "center", margin: 0,
  });
  s.addText([
    { text: "Average reply latency: 3.1 min", options: { bullet: true, breakLine: true } },
    { text: "Escalation precision: 0.91", options: { bullet: true, breakLine: true } },
    { text: "Cost per ticket: $0.04", options: { bullet: true } },
  ], {
    x: 5.5, y: 3.5, w: 3.7, h: 1.3,
    fontFace: FONT_B, fontSize: 12, color: C.ink, paraSpaceAfter: 2,
  });

  addFooter(s, 7);
}

// -----------------------------------------------------------------------------
// Slide 8 — Case study timeline / process (SMARTART).
// -----------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  addTitle(s, "How we rolled it out");

  s.addText("Eight weeks from first prompt to production default.", {
    x: 0.5, y: 1.15, w: 9, h: 0.4,
    fontFace: FONT_B, fontSize: 14, italic: true, color: C.muted, margin: 0,
  });

  // SMARTART placeholder — rollout timeline / process
  addMarkerRect(s, "SMARTART:rollout-timeline", {
    x: 0.8, y: 1.7, w: 8.4, h: 3.3,
  });

  addFooter(s, 8);
}

// -----------------------------------------------------------------------------
// Slide 9 — What we learned (dense text slide, no extra marker).
// -----------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  addTitle(s, "Four things we got wrong first");

  // 2x2 grid of lessons
  const cards = [
    { title: "Over-planned", body: "Deep plans rotted as tickets changed mid-flight. Shorter horizons + re-plan won." },
    { title: "Under-memoried", body: "Agent forgot the same customer twice in one thread. Added a per-conversation store." },
    { title: "Tool sprawl", body: "12 tools meant hallucinated calls. Cut to 4; precision jumped." },
    { title: "No kill switch", body: "First week: one bad loop, $400 in API spend. Now: step budget + hard cap." },
  ];
  const grid = { x0: 0.5, y0: 1.4, w: 4.4, h: 1.75, gapX: 0.2, gapY: 0.15 };
  cards.forEach((card, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = grid.x0 + col * (grid.w + grid.gapX);
    const y = grid.y0 + row * (grid.h + grid.gapY);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: grid.w, h: grid.h,
      fill: { color: C.sand }, line: { color: "E2E8F0", width: 1 },
    });
    // left accent bar
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.08, h: grid.h,
      fill: { color: C.accent }, line: { color: C.accent, width: 0 },
    });
    s.addText(card.title, {
      x: x + 0.25, y: y + 0.15, w: grid.w - 0.35, h: 0.4,
      fontFace: FONT_H, fontSize: 16, bold: true, color: C.midnight,
      align: "left", margin: 0,
    });
    s.addText(card.body, {
      x: x + 0.25, y: y + 0.6, w: grid.w - 0.35, h: grid.h - 0.7,
      fontFace: FONT_B, fontSize: 12, color: C.ink, align: "left", margin: 0,
    });
  });

  addFooter(s, 9);
}

// -----------------------------------------------------------------------------
// Slide 10 — Call to action / closing. BG atmospheric.
// -----------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.midnight };

  s.addText("Build small. Measure ruthlessly. Ship.", {
    x: 0.7, y: 1.6, w: 8.6, h: 1.4,
    fontFace: FONT_H, fontSize: 44, bold: true, color: "FFFFFF",
    align: "left", valign: "middle", margin: 0,
  });
  s.addText([
    { text: "Pick one workflow. Automate the narrow slice.", options: { bullet: true, breakLine: true } },
    { text: "Instrument every tool call. Review the traces weekly.", options: { bullet: true, breakLine: true } },
    { text: "Kill agents that don't earn their cost.", options: { bullet: true } },
  ], {
    x: 0.7, y: 3.1, w: 8.6, h: 1.6,
    fontFace: FONT_B, fontSize: 18, color: "CADCFC", paraSpaceAfter: 6,
  });

  s.addText("github.com/your-org/agents-that-work  ·  @you", {
    x: 0.7, y: 4.8, w: 8.6, h: 0.4,
    fontFace: FONT_B, fontSize: 14, italic: true, color: "9BB3E0",
    align: "left", margin: 0,
  });

  // BG marker — calm closer contrasting with dramatic opener
  addBgMarker(s, "BG:calm-minimal");
}

// -----------------------------------------------------------------------------
// Write file
// -----------------------------------------------------------------------------
const outPath = "/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/worktrees/sweet-varahamihira-bdd4cf/docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-b/presentation.pptx";
pres.writeFile({ fileName: outPath }).then((f) => {
  console.log("Wrote:", f);
});
