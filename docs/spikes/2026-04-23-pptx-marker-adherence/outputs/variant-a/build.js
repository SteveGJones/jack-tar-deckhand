// Build script for Variant A — "AI Agents That Actually Work"
// 10-slide conference talk, developer audience, 20 minutes.
// Uses named placeholder shapes prefixed IMAGE:, SMARTART:, BG: per brief.

const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10" x 5.625"
pres.author = "Jack-Tar Deckhand";
pres.title = "AI Agents That Actually Work";

// Palette — "Midnight Executive" w/ a coral accent for CTAs
const COLORS = {
  navy: "1E2761",
  ice: "CADCFC",
  white: "FFFFFF",
  ink: "0B1230",
  mute: "6B7280",
  accent: "F96167",
  gold: "F9E795",
};

const FONT_HEAD = "Georgia";
const FONT_BODY = "Calibri";

// Helper: add a marker placeholder rect. A low-opacity fill makes it
// visible-but-unobtrusive; the shape's objectName carries the marker.
function addMarker(slide, marker, { x, y, w, h, fillColor, label }) {
  slide.addShape(pres.shapes.RECTANGLE, {
    objectName: marker,
    x, y, w, h,
    fill: { color: fillColor || COLORS.ice, transparency: 70 },
    line: { color: COLORS.navy, width: 1, dashType: "dash" },
  });
  if (label) {
    slide.addText(label, {
      x, y, w, h,
      fontSize: 12, fontFace: FONT_BODY, color: COLORS.navy,
      align: "center", valign: "middle", italic: true, margin: 0,
    });
  }
}

// Helper: footer with slide number.
function addFooter(slide, n) {
  slide.addText(`AI Agents That Actually Work   ·   ${n}/10`, {
    x: 0.5, y: 5.25, w: 9, h: 0.3,
    fontSize: 10, fontFace: FONT_BODY, color: COLORS.mute,
    align: "right", margin: 0,
  });
}

// ========== Slide 1: Title ==========
{
  const s = pres.addSlide();
  s.background = { color: COLORS.navy };
  // Atmospheric background marker — this slide is a hero.
  addMarker(s, "BG:title-hero-dark-grid", {
    x: 0, y: 0, w: 10, h: 5.625,
    fillColor: COLORS.ink,
    label: "BG: atmospheric dark grid / circuit motif",
  });
  s.addText("AI Agents That Actually Work", {
    x: 0.5, y: 1.6, w: 9, h: 1.4,
    fontSize: 54, fontFace: FONT_HEAD, bold: true,
    color: COLORS.white, align: "left", margin: 0,
  });
  s.addText("Why most demos die in production — and the three pillars that save them.", {
    x: 0.5, y: 3.0, w: 9, h: 0.8,
    fontSize: 20, fontFace: FONT_BODY, color: COLORS.ice,
    italic: true, align: "left", margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.6, w: 0.6, h: 0.06, fill: { color: COLORS.accent }, line: { color: COLORS.accent },
  });
  s.addText("20-minute conference talk  ·  For developers shipping agents", {
    x: 0.5, y: 4.75, w: 9, h: 0.4,
    fontSize: 13, fontFace: FONT_BODY, color: COLORS.ice, margin: 0,
  });
}

// ========== Slide 2: The problem ==========
{
  const s = pres.addSlide();
  s.background = { color: COLORS.white };
  s.addText("The demo-to-production gap", {
    x: 0.5, y: 0.4, w: 9, h: 0.7,
    fontSize: 36, fontFace: FONT_HEAD, bold: true, color: COLORS.navy, margin: 0,
  });
  s.addText([
    { text: "Agents that wow on stage often crumble under real traffic.", options: { breakLine: true } },
    { text: "Where the wheels come off:", options: { bold: true, breakLine: true } },
    { text: "Non-deterministic failures are rarely reproducible in CI", options: { bullet: true, breakLine: true } },
    { text: "Tool calls silently misfire — no schema, no retry story", options: { bullet: true, breakLine: true } },
    { text: "Context windows explode as conversations drift", options: { bullet: true, breakLine: true } },
    { text: "Observability is bolted on, not designed in", options: { bullet: true } },
  ], {
    x: 0.5, y: 1.25, w: 5.2, h: 3.8,
    fontSize: 15, fontFace: FONT_BODY, color: COLORS.ink, paraSpaceAfter: 6,
  });
  // Illustration placeholder on the right column.
  addMarker(s, "IMAGE:demo-vs-prod-split", {
    x: 6.0, y: 1.25, w: 3.5, h: 3.5,
    label: "IMAGE: split scene — polished demo stage vs. chaotic prod pager",
  });
  addFooter(s, 2);
}

// ========== Slide 3: Why they fail — stats ==========
{
  const s = pres.addSlide();
  s.background = { color: COLORS.white };
  s.addText("Why most agent demos fail in production", {
    x: 0.5, y: 0.4, w: 9, h: 0.7,
    fontSize: 32, fontFace: FONT_HEAD, bold: true, color: COLORS.navy, margin: 0,
  });
  const stats = [
    { big: "73%", label: "of agent proofs-of-concept never reach production" },
    { big: "4.2x", label: "cost blow-up when context isn't managed" },
    { big: "1 in 5", label: "tool calls fail silently without structured schemas" },
  ];
  stats.forEach((stat, i) => {
    const x = 0.5 + i * 3.15;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.4, w: 2.9, h: 2.6,
      fill: { color: COLORS.ice, transparency: 40 },
      line: { color: COLORS.navy, width: 0 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.4, w: 0.08, h: 2.6, fill: { color: COLORS.accent }, line: { color: COLORS.accent },
    });
    s.addText(stat.big, {
      x: x + 0.2, y: 1.55, w: 2.6, h: 1.1,
      fontSize: 60, fontFace: FONT_HEAD, bold: true, color: COLORS.navy, margin: 0,
    });
    s.addText(stat.label, {
      x: x + 0.2, y: 2.75, w: 2.6, h: 1.15,
      fontSize: 13, fontFace: FONT_BODY, color: COLORS.ink, margin: 0,
    });
  });
  s.addText("Sources: practitioner surveys, internal telemetry, common autopsy patterns.", {
    x: 0.5, y: 4.3, w: 9, h: 0.3,
    fontSize: 10, fontFace: FONT_BODY, color: COLORS.mute, italic: true, margin: 0,
  });
  addFooter(s, 3);
}

// ========== Slide 4: The three pillars — overview ==========
{
  const s = pres.addSlide();
  s.background = { color: COLORS.white };
  s.addText("The three architectural pillars", {
    x: 0.5, y: 0.4, w: 9, h: 0.7,
    fontSize: 36, fontFace: FONT_HEAD, bold: true, color: COLORS.navy, margin: 0,
  });
  s.addText("Every agent that survives production gets these right.", {
    x: 0.5, y: 1.0, w: 9, h: 0.4,
    fontSize: 15, fontFace: FONT_BODY, color: COLORS.mute, italic: true, margin: 0,
  });
  // Diagram placeholder — showing the relationship between the three pillars.
  addMarker(s, "SMARTART:three-pillars-relationship", {
    x: 0.75, y: 1.6, w: 8.5, h: 3.3,
    label: "SMARTART: three pillars — Planning  |  Memory  |  Tool Use  (radial/triangle relationship)",
  });
  addFooter(s, 4);
}

// ========== Slide 5: Pillar 1 — Planning ==========
{
  const s = pres.addSlide();
  s.background = { color: COLORS.white };
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.25, h: 5.625, fill: { color: COLORS.accent }, line: { color: COLORS.accent },
  });
  s.addText("Pillar 1 — Planning", {
    x: 0.6, y: 0.4, w: 9, h: 0.7,
    fontSize: 32, fontFace: FONT_HEAD, bold: true, color: COLORS.navy, margin: 0,
  });
  s.addText([
    { text: "Explicit task decomposition beats hoping the model will figure it out.", options: { breakLine: true, italic: true } },
    { text: "", options: { breakLine: true } },
    { text: "Design the plan as a first-class artefact", options: { bullet: true, breakLine: true } },
    { text: "Re-plan on failure, not just on completion", options: { bullet: true, breakLine: true } },
    { text: "Constrain search — depth, budget, step count", options: { bullet: true, breakLine: true } },
    { text: "Log every decision for post-mortem analysis", options: { bullet: true } },
  ], {
    x: 0.6, y: 1.25, w: 5.4, h: 3.5,
    fontSize: 15, fontFace: FONT_BODY, color: COLORS.ink, paraSpaceAfter: 6,
  });
  // Flow diagram placeholder on the right — planning loop.
  addMarker(s, "SMARTART:planning-replan-loop", {
    x: 6.2, y: 1.25, w: 3.4, h: 3.5,
    label: "SMARTART: plan → act → observe → re-plan loop",
  });
  addFooter(s, 5);
}

// ========== Slide 6: Pillar 2 — Memory ==========
{
  const s = pres.addSlide();
  s.background = { color: COLORS.white };
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.25, h: 5.625, fill: { color: COLORS.accent }, line: { color: COLORS.accent },
  });
  s.addText("Pillar 2 — Memory", {
    x: 0.6, y: 0.4, w: 9, h: 0.7,
    fontSize: 32, fontFace: FONT_HEAD, bold: true, color: COLORS.navy, margin: 0,
  });
  s.addText([
    { text: "Context is a budget. Spend it like one.", options: { breakLine: true, italic: true } },
    { text: "", options: { breakLine: true } },
    { text: "Short-term: conversation scratchpad, reset aggressively", options: { bullet: true, breakLine: true } },
    { text: "Long-term: vector store, keyed by user + task", options: { bullet: true, breakLine: true } },
    { text: "Summarise before you run out of tokens, not after", options: { bullet: true, breakLine: true } },
    { text: "Cache tool results — deterministic calls shouldn't re-run", options: { bullet: true } },
  ], {
    x: 0.6, y: 1.25, w: 5.4, h: 3.5,
    fontSize: 15, fontFace: FONT_BODY, color: COLORS.ink, paraSpaceAfter: 6,
  });
  addMarker(s, "IMAGE:memory-layers-illustration", {
    x: 6.2, y: 1.25, w: 3.4, h: 3.5,
    label: "IMAGE: three-layer memory stack — scratchpad / session / long-term",
  });
  addFooter(s, 6);
}

// ========== Slide 7: Pillar 3 — Tool Use ==========
{
  const s = pres.addSlide();
  s.background = { color: COLORS.white };
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.25, h: 5.625, fill: { color: COLORS.accent }, line: { color: COLORS.accent },
  });
  s.addText("Pillar 3 — Tool Use", {
    x: 0.6, y: 0.4, w: 9, h: 0.7,
    fontSize: 32, fontFace: FONT_HEAD, bold: true, color: COLORS.navy, margin: 0,
  });
  s.addText([
    { text: "Tools are the agent's API to reality — treat them that way.", options: { breakLine: true, italic: true } },
    { text: "", options: { breakLine: true } },
    { text: "Strict JSON schemas for every tool — no free-text arguments", options: { bullet: true, breakLine: true } },
    { text: "Idempotent calls where possible; explicit retry policy otherwise", options: { bullet: true, breakLine: true } },
    { text: "Least-privilege scopes — read before write, write before delete", options: { bullet: true, breakLine: true } },
    { text: "Trace every call: args in, result out, latency, error code", options: { bullet: true } },
  ], {
    x: 0.6, y: 1.25, w: 5.4, h: 3.5,
    fontSize: 15, fontFace: FONT_BODY, color: COLORS.ink, paraSpaceAfter: 6,
  });
  addMarker(s, "SMARTART:tool-call-sequence", {
    x: 6.2, y: 1.25, w: 3.4, h: 3.5,
    label: "SMARTART: agent → schema validator → tool → trace sink",
  });
  addFooter(s, 7);
}

// ========== Slide 8: Case study — intro ==========
{
  const s = pres.addSlide();
  s.background = { color: COLORS.navy };
  addMarker(s, "BG:case-study-server-room", {
    x: 0, y: 0, w: 10, h: 5.625, fillColor: COLORS.ink,
    label: "BG: soft server-room / dashboard atmosphere, heavy dark overlay",
  });
  s.addText("Case study: a support agent at scale", {
    x: 0.5, y: 0.5, w: 9, h: 0.9,
    fontSize: 36, fontFace: FONT_HEAD, bold: true, color: COLORS.white, margin: 0,
  });
  s.addText("Mid-size SaaS, 40k tickets/month. Two engineers. Nine weeks from spike to GA.", {
    x: 0.5, y: 1.4, w: 9, h: 0.5,
    fontSize: 16, fontFace: FONT_BODY, color: COLORS.ice, italic: true, margin: 0,
  });
  const beats = [
    { h: "Before", b: "Median response 14m, 62% first-contact resolution, on-call burned out." },
    { h: "What we changed", b: "Explicit plan artefact per ticket. Cached retrieval over product docs. Tools with strict schemas + retry." },
    { h: "After", b: "Median 52s, 81% first-contact resolution, on-call reclaimed Fridays." },
  ];
  beats.forEach((beat, i) => {
    const y = 2.1 + i * 1.05;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y, w: 9, h: 0.95, fill: { color: COLORS.white, transparency: 85 }, line: { color: COLORS.ice, width: 0 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y, w: 0.08, h: 0.95, fill: { color: COLORS.accent }, line: { color: COLORS.accent },
    });
    s.addText(beat.h, {
      x: 0.75, y: y + 0.1, w: 2, h: 0.4,
      fontSize: 14, fontFace: FONT_HEAD, bold: true, color: COLORS.white, margin: 0,
    });
    s.addText(beat.b, {
      x: 2.8, y: y + 0.1, w: 6.6, h: 0.75,
      fontSize: 13, fontFace: FONT_BODY, color: COLORS.ice, margin: 0,
    });
  });
  addFooter(s, 8);
}

// ========== Slide 9: Case study — the three pillars applied ==========
{
  const s = pres.addSlide();
  s.background = { color: COLORS.white };
  s.addText("How the pillars showed up in the build", {
    x: 0.5, y: 0.4, w: 9, h: 0.7,
    fontSize: 30, fontFace: FONT_HEAD, bold: true, color: COLORS.navy, margin: 0,
  });
  const cols = [
    { h: "Planning", b: "Each ticket got an explicit 3-step plan: classify → retrieve → draft. Re-plan on retrieval miss." },
    { h: "Memory", b: "Session scratchpad flushed per ticket. Long-term: embeddings of resolved tickets, 14-day TTL." },
    { h: "Tool Use", b: "Four tools only — search_docs, read_ticket, post_reply, escalate. All schema-validated, all traced." },
  ];
  cols.forEach((col, i) => {
    const x = 0.5 + i * 3.15;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.3, w: 2.9, h: 2.9,
      fill: { color: COLORS.ice, transparency: 50 }, line: { color: COLORS.navy, width: 0 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.3, w: 2.9, h: 0.08, fill: { color: COLORS.accent }, line: { color: COLORS.accent },
    });
    s.addText(col.h, {
      x: x + 0.2, y: 1.45, w: 2.6, h: 0.5,
      fontSize: 20, fontFace: FONT_HEAD, bold: true, color: COLORS.navy, margin: 0,
    });
    s.addText(col.b, {
      x: x + 0.2, y: 2.0, w: 2.6, h: 2.1,
      fontSize: 13, fontFace: FONT_BODY, color: COLORS.ink, margin: 0,
    });
  });
  addMarker(s, "IMAGE:case-study-dashboard", {
    x: 0.5, y: 4.4, w: 9, h: 0.55,
    label: "IMAGE: before/after dashboard strip — response time, FCR, on-call load",
  });
  addFooter(s, 9);
}

// ========== Slide 10: Call to action ==========
{
  const s = pres.addSlide();
  s.background = { color: COLORS.navy };
  s.addText("Start here on Monday", {
    x: 0.5, y: 0.7, w: 9, h: 0.9,
    fontSize: 44, fontFace: FONT_HEAD, bold: true, color: COLORS.white, margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.75, w: 0.6, h: 0.06, fill: { color: COLORS.accent }, line: { color: COLORS.accent },
  });
  s.addText([
    { text: "Write the plan artefact before you write the prompt.", options: { bullet: true, breakLine: true } },
    { text: "Put tools behind a schema. If it's free-text, it's a bug.", options: { bullet: true, breakLine: true } },
    { text: "Budget your context like tokens cost money — because they do.", options: { bullet: true, breakLine: true } },
    { text: "Trace every call. You cannot debug what you cannot see.", options: { bullet: true } },
  ], {
    x: 0.5, y: 2.0, w: 6.5, h: 3.0,
    fontSize: 18, fontFace: FONT_BODY, color: COLORS.white, paraSpaceAfter: 10,
  });
  s.addText("Thank you.", {
    x: 0.5, y: 4.9, w: 5, h: 0.5,
    fontSize: 20, fontFace: FONT_HEAD, italic: true, color: COLORS.gold, margin: 0,
  });
  s.addText("@yourhandle  ·  talks.example.com/agents", {
    x: 5.5, y: 5.0, w: 4, h: 0.35,
    fontSize: 12, fontFace: FONT_BODY, color: COLORS.ice, align: "right", margin: 0,
  });
}

pres.writeFile({ fileName: "presentation.pptx" })
  .then((f) => console.log("Wrote:", f))
  .catch((e) => { console.error(e); process.exit(1); });
