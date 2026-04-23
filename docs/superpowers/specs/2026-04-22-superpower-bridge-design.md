# Superpower Bridge — Enrich pptx-Superpower Decks with Jack-Tar Visuals

## Problem

The `claude-api:pptx` superpower creates well-structured, well-designed decks — opinionated colour palettes, typography pairings, good layout vocabulary. But they're text-heavy and lack visual punch. Jack-tar-deckhand produces visually rich presentations (AI images, editable SmartArt, atmospheric backgrounds) but through a heavier orchestration pipeline. There's no way to combine the superpower's structural strengths with jack-tar's visual capabilities.

User feedback: people love both systems but want the best of each.

## Solution

A three-phase sequential workflow implemented as a new jack-tar plugin (`jack-tar-superpower-bridge`):

1. **Narrative Pre-Brief** — jack-tar produces a creative brief that guides the superpower
2. **Superpower Build** — the user invokes `/pptx` as normal with the brief as context
3. **Visual Enrichment** — jack-tar analyses the superpower's output and enriches it with visuals

The superpower is never modified. The bridge wraps around it.

## Phase 1: Narrative Pre-Brief

### Purpose

Produce a natural language creative brief that the user takes into the pptx superpower. The brief shapes how the superpower builds the deck — narrative arc, communication intent, and where to leave space for visuals.

### Invocation

`/bridge-brief` with topic, duration, audience. Collaborative — the skill proposes and the user adjusts.

### Output: Creative Brief Document

A markdown file (`creative-brief.md`) with three sections:

#### Section A: Narrative Architecture

Arc selection (Problem-Solution, Hero's Journey, Build-Up-Reveal, Tension-Release, etc.), pacing across the deck, emotional beats — where to build tension, where to pivot, where to land. This is the strategic storytelling layer that the superpower doesn't provide.

Example:
> Open with a provocative question that challenges conventional thinking about AI agents. Build tension through 3-4 slides showing the gap between promise and reality. Pivot with a concrete case study that demonstrates the solution. Expand into the architecture that makes it work. Close with a forward-looking challenge to the audience.

#### Section B: Communication & Visual Intent

What the audience should walk away knowing. What they should feel. The tone (authoritative, conversational, provocative, inspiring). The visual personality (clean/minimal, bold/atmospheric, data-rich, cinematic).

This is NOT per-slide guidance — it's the overall intent that lets the superpower make good slide-level decisions on its own. The superpower is good at this; we just give it better raw material.

Example:
> **Audience takeaway:** AI agents need explicit architecture, not just prompt engineering.
> **Tone:** Confident but approachable — speaking from experience, not theory.
> **Visual feel:** Technical but warm. Dark backgrounds with accent colours. Architectural metaphors — blueprints, scaffolding, foundations.

#### Section C: Placeholder Instructions

Instructions addressed to the deck builder (the superpower) telling it where to leave space for visual enrichment. Three marker types:

| Marker prefix | Purpose | Example |
|--------------|---------|---------|
| `IMAGE:` | AI-generated illustration | `IMAGE:agent-architecture-diagram` |
| `SMARTART:` | Editable SmartArt graphic | `SMARTART:flowchart` |
| `BG:` | Slide is a candidate for an AI background | `BG:dramatic-contrast` |

Instructions tell the superpower to create named rectangles as visible placeholders:
- Light grey fill (`F0F0F0`), 1px dashed border (`CCCCCC`), marker name as visible text inside
- `IMAGE:` markers reserve space at specified position (e.g. right 40% of slide)
- `SMARTART:` markers replace bullet content that will become a diagram
- `BG:` markers are a small label shape in the corner indicating background intent

The pre-brief does NOT dictate which specific slides get markers. It describes the kinds of content that should be marked and lets the superpower decide where they go based on the content it creates.

##### PptxGenJS property — use `objectName`, NOT `name`

> **Validated by [Spike 1](../../spikes/2026-04-23-pptx-marker-adherence/README.md) on 2026-04-23. This is the single most important line in the protocol — get it wrong and every marker is silently dropped.**

PptxGenJS 4.0.1 **silently discards** the `name` property passed to `addShape()`. The correct API key is `objectName`. Spike 1 proved this with three variants: the variant using `objectName` had 100% marker adherence; the two variants using `name` (as specified verbatim in an earlier draft of this protocol) had 0% — the rectangles rendered correctly on-screen but the shape names never reached the OOXML `<p:cNvPr @name>` attribute where the downstream enrichment looks for them.

The brief MUST tell the superpower to use the `objectName` property. Example code the brief should include:

```javascript
// CORRECT — shape name survives into OOXML for downstream enrichment
slide.addShape(pres.shapes.RECTANGLE, {
  objectName: "IMAGE:agent-architecture",  // <-- objectName, not name
  x: 5.5, y: 1.5, w: 4, h: 3,
  fill: { color: "F0F0F0" },
  line: { color: "CCCCCC", width: 1, dashType: "dash" },
});
slide.addText("IMAGE:agent-architecture", {
  x: 5.5, y: 2.8, w: 4, h: 0.5,
  align: "center", color: "888888", fontSize: 14,
});
```

Identifier grammar after the colon: `[A-Za-z0-9_-]+`.

### Collaborative Flow

1. User provides topic, duration, audience
2. Skill proposes 2-3 narrative arcs with trade-offs and a recommendation
3. User selects or adjusts
4. Skill asks about communication intent — what should the audience take away?
5. Skill asks about visual personality — what should the deck feel like?
6. Skill generates the creative brief
7. User reviews, adjusts, approves
8. Brief saved to `creative-brief.md` in the working directory

## Phase 2: Superpower Build

The user invokes `/pptx` with the creative brief as context. This phase is entirely the user + superpower — the bridge plugin is not involved.

The superpower builds the deck following its normal workflow:
- Generates a PptxGenJS Node.js build script
- Executes it to produce a .pptx
- Runs its QA cycle (LibreOffice → PDF → slide images → visual review)

The creative brief influences the deck through prompt context:
- Narrative architecture shapes slide order and content flow
- Communication intent guides content depth and tone
- Placeholder instructions result in named marker shapes where visuals will go

**Output:** A .pptx file and the Node.js build script that generated it.

## Phase 3: Visual Enrichment

### 3.1 Deck Analysis

**Input:** The Node.js build script that the superpower generated, plus the .pptx file path for later enrichment.

The skill accepts the .pptx path and looks for the build script in the same directory (the superpower leaves it alongside the output). If the build script isn't found, the skill asks the user to provide its path. The .pptx is only used during enrichment application (Section 3.4) — all analysis works from the build script because it's richer and more readable than reverse-engineering the compiled .pptx.

The analyser parses the JS build script to extract per-slide information:
- Text content (from `addText()` calls)
- Shape names (looking for `IMAGE:`, `SMARTART:`, `BG:` markers)
- Shape coordinates and dimensions (from marker shapes)
- Background state (solid colour vs. image)
- Element types present (charts, tables, images, plain text)

**Classification per slide:**

| Category | Criteria | Enrichment |
|----------|----------|------------|
| Marker: IMAGE | Shape named `IMAGE:*` | AI element image at marker position |
| Marker: SMARTART | Shape named `SMARTART:*` | Editable SmartArt replacing marker |
| Marker: BG | Shape named `BG:*` | AI atmospheric background |
| Text-heavy (unmarked) | High text density, no images/charts | Candidate for AI background |
| List/process (unmarked) | Bullet points matching SmartArt patterns | Candidate for SmartArt |
| Already rich | Has charts, images, complex layout | Leave alone |

Unmarked slides can still be proposed for enrichment based on content analysis — markers just make it explicit and provide positioning.

### 3.2 Enrichment Menu

Present the analysis to the user as a selectable menu:

```
Marked enrichments:
  Slide 3: IMAGE:agent-architecture — AI illustration (right 40%)
  Slide 5: SMARTART:flowchart — 4-step process from bullets
  Slide 8: BG:dramatic-contrast — atmospheric background

Suggested enrichments (unmarked):
  Slide 10: text-heavy, no visuals — AI background candidate
  Slide 12: 5-item comparison list — SmartArt venn candidate

Already rich (no changes):
  Slide 1 (title), Slide 4 (chart), Slide 14 (closing)
```

The user selects which enrichments to apply — all, specific ones, none. They can adjust descriptions, change SmartArt types, or add their own requests. Collaborative, not automated.

### 3.3 Asset Generation — Draft/Review Cycle

For each approved enrichment, generate assets using the cheap-first principle.

#### AI Images (backgrounds and element images)

**Draft tier — always Ollama first:**
1. Generate with Ollama (free, local) — preferred even when cloud providers are available
2. View the image immediately
3. Assess against the intent from the pre-brief (mood, subject, composition)
4. If not right: refine prompt, regenerate at Ollama (up to 3 iterations, all free)

**Cloud draft tier — only if Ollama unavailable or user requests:**
- Imagen Fast ($0.02) or FLUX via FAL ($0.03)
- Same 3-iteration review cycle

**Production escalation:**
- If Ollama draft proves the prompt works but quality needs upgrading
- Escalate to Nanobanana Flash ($0.067) with the proven prompt
- Image-reviewer scores the result
- If Flash passes → done
- If Flash fails → Nanobanana Pro ($0.134) gets ONE shot
- If Pro fails → flag for user ("here are the attempts, the prompt may need human judgment")

**Principle:** Ollama proves the prompt works. Nanobanana produces the quality. If the prompt is wrong, free iterations fix it before any money is spent.

#### SmartArt

SmartArt skips the draft/review cycle entirely. The pptx_native engine is deterministic — same spec produces the same output. The review is structural:

1. Parse the bullet content from the build script into a SmartArt data spec (`{"items": [...]}` or `{"tree": {...}}`)
2. Select the layout from the catalog based on the `SMARTART:` marker type and item count
3. Validate the spec against layout capacity constraints
4. Render the carrier .pptx via `pptx_native/engine.render()`
5. Verify carrier XML structure (layout parts present, data model well-formed)

No visual rasterisation of SmartArt — PowerPoint renders from the diagram XML on first open, and LibreOffice renders SmartArt poorly. The layouts are proven by the existing test suite (290 pptx_native tests) and manual gate validation.

### 3.4 Draft Assembly & Internal Review

> **Validated by [Spike 2](../../spikes/2026-04-23-python-pptx-enrichment/README.md) on 2026-04-23.** All three operations work end-to-end against real PptxGenJS-produced OOXML, including the PowerPoint Mac open/save/PDF-export round trip. See the spike's findings for the full test matrix.

Apply all reviewed assets to a **copy** of the .pptx (never modify the original):

1. **Apply backgrounds.** python-pptx 1.0.2's `Slide.background` / `_Background.fill` facade does **not** expose a picture-fill setter — it only supports solid, gradient, patterned, and background fills. The bridge must do OOXML surgery:
   - Add the image as a part via `Image.from_file(path)` → `ImagePart.new(slide.part.package, img)` → `slide.part.relate_to(part, RT.IMAGE)` (returns an `rId`).
   - Hand-build `<p:bg><p:bgPr><a:blipFill r:embed="rId">…</a:blipFill></p:bgPr></p:bg>` via lxml and insert it as the first child of `<p:cSld>` (remove any existing `<p:bg>` first).
   - Remove the `BG:` marker shape by finding its `<p:nvSpPr>/<p:cNvPr name="BG:*">` and calling `.getparent().remove(sp)`.
   Reference implementation: [docs/spikes/2026-04-23-python-pptx-enrichment/prototypes/op1_background.py](../../spikes/2026-04-23-python-pptx-enrichment/prototypes/op1_background.py).

2. **Apply element images.** Find the shape with `cNvPr @name == "IMAGE:<slug>"` anywhere in the deck, capture `(left, top, width, height)`, remove the shape element, then call `slide.shapes.add_picture(path, left, top, width=w, height=h)`. This uses the supported high-level python-pptx API and preserves exact geometry. Reference: [op2_replace_image_shape.py](../../spikes/2026-04-23-python-pptx-enrichment/prototypes/op2_replace_image_shape.py).

3. **Apply SmartArt.** Build the spec, render the carrier, inject. The plan's earlier "rename marker to `pptx_native_placeholder_<N>`" step is **unnecessary** — `assembler_patch.InjectionRequest` accepts the marker name directly via its `placeholder_name` field:

   ```python
   from src import engine, assembler_patch
   from src.assembler_patch import InjectionRequest

   # Render carrier (single-slide .pptx containing one SmartArt graphic)
   result = engine.render(spec, carriers_dir)      # returns RenderResult(output_path, ...)

   # Inject — no marker renaming; placeholder_name takes the full marker string
   assembler_patch.inject(host_pptx, [
       InjectionRequest(
           slide_number=slide_index_1based,
           carrier_pptx=result.output_path,
           placeholder_name="SMARTART:three-pillars",   # <-- the marker string as-is
       )
   ])
   ```

   The carrier spec's `data` shape depends on the layout's data_shape:
   - Flat-list layouts (Process/Cycle/List/Matrix/Pyramid/Relationship) require `{"items": ["str1", "str2", …]}`. **Items must be plain strings, not dicts.** Passing `[{"text": "…"}]` raises `FlatListBuildError`.
   - Hierarchical layouts (OrgChart, Hierarchy2-6) require `{"tree": {…}}`.

   Reference: [op3_inject_smartart.py](../../spikes/2026-04-23-python-pptx-enrichment/prototypes/op3_inject_smartart.py).

4. **Marker-adjacent text clearing contract.** Spike 2 surfaced a cosmetic issue: when a SMARTART marker is replaced with an injected diagram, body text living in *other text boxes* on the same slide that happen to overlap the marker's geometry remains visible behind the SmartArt. The marker shape itself is cleanly removed; the fragments are from independent text frames. Two viable resolutions:
   - **Brief-side contract (preferred for v1):** the brief instructs the superpower that any slide carrying a SMARTART marker must contain only the slide title plus the marker — no competing body text. Simple, verifiable at analysis time.
   - **Enrichment-side geometric clearing:** on SMARTART replacement, enumerate all shapes on the slide whose bounding boxes intersect the marker's geometry and remove their content (or the shapes themselves). More complex, easy to over-delete.
   The brief-side contract is strictly simpler and fails safely; adopt it for v1 and reconsider if user feedback warrants.

5. **Render for review** — convert enriched .pptx to slide images via LibreOffice → PDF → pdftoppm (same toolchain the superpower uses). SmartArt slides will render poorly in LibreOffice but AI images and backgrounds will be visible. For authoritative visual verification of SmartArt, use PowerPoint Mac via [tools/pptx_to_pdf.sh](../../../tools/pptx_to_pdf.sh) (forces SmartArt cache regen on save).

6. **Internal deck review** — view every slide image:
   - Do AI backgrounds overpower the text? (contrast, readability)
   - Do element images fit their allocated space?
   - Is the visual style cohesive across enriched slides?
   - Do enriched slides feel consistent with non-enriched slides?
   - Any slides where the enrichment made things worse?

7. **Fix issues** — regenerate images, adjust, or drop an enrichment. Repeat until the deck passes internal review.

### 3.5 Delivery

Only after internal review passes, present the enriched deck to the user:

- Show the enriched slide images with a summary of what was applied
- Report the cost incurred (Ollama iterations are free, cloud costs itemised)
- The user can accept, request changes to specific enrichments, or drop any they don't like

**Output files:**
- `presentation-enriched.pptx` — the enriched deck (original untouched)
- `enrichment-report.md` — what was applied, costs, any SmartArt that needs PowerPoint to render

**PDF conversion note:** The superpower's text-only decks convert cleanly to PDF. AI backgrounds and element images also survive PDF conversion (they're embedded raster images). SmartArt may not render correctly in LibreOffice PDF export — the enrichment report flags this and recommends PowerPoint for PDF export if SmartArt was applied.

## Plugin Structure

New plugin: `jack-tar-superpower-bridge`

```
plugins/jack-tar-superpower-bridge/
  .claude-plugin/
    plugin.json
  skills/
    bridge-brief/
      SKILL.md              # Phase 1: narrative pre-brief
    enrich-deck/
      SKILL.md              # Phase 3: analyse + propose + apply
  src/
    analyser.py             # Parse JS build script, classify slides
    enrichment.py           # Apply enrichments to .pptx via python-pptx
    placeholder.py          # Placeholder protocol — find/parse/remove markers
    smartart_bridge.py      # Spec construction + carrier render + injection
    image_bridge.py         # Draft/review cycle for AI images
  tests/
    test_analyser.py
    test_enrichment.py
    test_placeholder.py
    test_smartart_bridge.py
    test_image_bridge.py
```

### Dependencies on other jack-tar plugins

| Plugin | What's used | How |
|--------|------------|-----|
| `jack-tar-deckhand` | imagegen-bridge skill, image review | Skill invocation for image generation |
| `jack-tar-msft-smartart` | `engine.render()`, `assembler_patch.inject()` | Python import for SmartArt carrier + injection |
| `jack-tar-cloud` | Cloud image providers | Via imagegen-bridge (not direct) |
| `jack-tar-ollama` | Local image generation | Via imagegen-bridge (not direct) |
| `jack-tar-custom-smartart` | Not used in v1 | Could add Mermaid/Vega in v2 |

### No dependency on

- The pptx superpower itself — the bridge reads its output (.pptx and build script) but never calls it
- The jack-tar assembler (`build_deck.js`) — enrichment uses python-pptx, not PptxGenJS

## User Flow (End to End)

```
User: "I need a deck about AI agent architectures, 20 min conference talk"

Phase 1:
  /bridge-brief "AI agent architectures, 20 min conference talk for developers"
  → Skill proposes Hero's Journey arc, user adjusts to Problem-Solution
  → Discusses communication intent and visual personality
  → Produces creative-brief.md
  → User reviews and approves

Phase 2:
  /pptx "Build a presentation following this brief: [paste or reference creative-brief.md]"
  → Superpower builds deck with narrative structure and placeholder markers
  → User reviews and iterates with superpower as normal
  → Final output: presentation.pptx + the build script

Phase 3:
  /enrich-deck presentation.pptx
  → Analyser reads the build script, classifies slides
  → Presents enrichment menu to user
  → User selects enrichments
  → Draft/review cycle: Ollama drafts → review → iterate → Nanobanana production
  → SmartArt: spec → carrier → inject (no visual review cycle needed)
  → Internal deck review: render all slides, check cohesion
  → Deliver: presentation-enriched.pptx + enrichment-report.md
  → User accepts or requests changes
```

## v1 Scope

| In scope | Out of scope (v2+) |
|----------|-------------------|
| Narrative pre-brief skill | Custom data viz (Mermaid/Vega-Lite charts) |
| Build script analyser | Full slide re-renders (full_render strategy) |
| AI background enrichment | Backdrop strategy with vision analysis |
| Editable SmartArt enrichment (pptx_native) | Pragmatic composition (multi-element positioning) |
| AI element images via placeholder markers | Wrapped single-command invocation |
| Ollama-first draft/review cycle | Modifying the pptx superpower |
| Internal review before delivery | Animation or transition injection |
| Cost tracking and reporting | |

## Key Design Decisions

1. **Three phases, not one.** The superpower is good at building decks. We don't replace it — we wrap around it with narrative guidance before and visual enrichment after.

2. **Analyse the build script, not the .pptx.** The JS script has richer semantic information than the compiled binary. Coordinates, text content, shape names, intent — all readable as text.

3. **Placeholder protocol via named shapes.** The pre-brief instructs the superpower to leave markers. The enrichment skill finds them by name. Same proven pattern as jack-tar's SmartArt placeholder injection.

4. **Ollama first, always.** Even when cloud providers are available, draft with Ollama (free). Prove the prompt works before spending money. This matches the cross-tier refinement loop from PR #50.

5. **SmartArt skips the review cycle.** The pptx_native engine is deterministic and proven by 290 tests. Review is structural (spec validation), not visual (no reliable rasteriser for SmartArt outside PowerPoint).

6. **Never modify the original .pptx.** Enrichment produces a new file. The user can always go back to the superpower's output.

7. **Collaborative at every stage.** Pre-brief proposes arcs, user selects. Analyser proposes enrichments, user selects. Results reviewed internally before delivery. No silent automation.

8. **PDF conversion preserved.** Embedded raster images and SmartArt survive PDF export. SmartArt renders best via PowerPoint's PDF export, flagged in the enrichment report.

## Risk Register

| Risk | Impact | Mitigation | Spike status |
|------|--------|------------|--------------|
| Superpower doesn't follow placeholder instructions | Markers missing → fewer enrichment targets | Analyser still proposes enrichments for unmarked text-heavy/list slides | **Spike 1:** confirmed 100% adherence with the `objectName` protocol; 0% with `name`. Fall-back path still required for briefs that drift. |
| LibreOffice SmartArt rendering poor | Internal review can't visually verify SmartArt | SmartArt is deterministic + structurally validated; flag in report. Use PowerPoint Mac via tools/pptx_to_pdf.sh for authoritative checks. | **Spike 2:** PowerPoint Mac open/save/PDF-export round-trip passes on first try. |
| Build script format changes | Analyser parsing breaks | Parser is heuristic (looking for `addText`, `addShape`, shape names), not a formal JS AST — resilient to formatting changes | Not spiked. **Open design question:** should the analyser parse the .pptx directly instead of the build script? OOXML has shape names, coordinates, text content — everything the script has. To be decided. |
| python-pptx and PptxGenJS produce subtly different OOXML | Enrichment corrupts superpower's output | Validate with PPTXSchemaValidator after enrichment; test on real superpower output | **Spike 2:** all three ops pass against real PptxGenJS-produced OOXML with no corruption. File-size drop (python-pptx compacts zip) is cosmetic, not lossy. |
| User confusion about three-phase flow | Abandonment, partial usage | Clear invocation names, brief explains the full flow, each phase works independently | Not spiked. To be assessed via dogfooding once v1 ships. |
| Marker-adjacent body text bleeds through injected SmartArt | Visual artefact on SMARTART slides | Brief-side contract: SMARTART marker slides carry only title + marker (see Section 3.4 step 4) | **Spike 2:** issue observed on one slide; contract proposed and accepted. |

## Spike validation (2026-04-23)

Before writing the implementation plan, two spikes validated the design's highest-risk assumptions.

### Spike 1 — /pptx marker adherence

[docs/spikes/2026-04-23-pptx-marker-adherence/README.md](../../spikes/2026-04-23-pptx-marker-adherence/README.md) — **GO with adjusted protocol**. Three variant briefs were run through `document-skills:pptx`:

- **Variant A** (minimal brief): subagent independently chose `objectName` → 100% marker adherence (8 markers in OOXML).
- **Variants B and C** (explicit protocol + worked example, both specifying `name:` as in an earlier draft of this spec): 0% marker adherence. Rectangles rendered correctly on-screen; shape names never reached `<p:cNvPr @name>` because PptxGenJS 4.0.1 silently drops `name` and only honours `objectName`.

Finding folded in: Section C "PptxGenJS property — use `objectName`, NOT `name`" above.

### Spike 2 — python-pptx editing of /pptx output

[docs/spikes/2026-04-23-python-pptx-enrichment/README.md](../../spikes/2026-04-23-python-pptx-enrichment/README.md) — **GO**. Three enrichment prototypes were built and validated against Spike 1 Variant A's real PptxGenJS-produced OOXML:

| Op | Unit tests | PowerPoint Mac | Visual review | OOXML inspection |
|----|------------|----------------|---------------|------------------|
| Op1 — background image | 2/2 | Open/save/PDF-export all pass | Background applied, title readable | `<p:bg><a:blipFill>` well-formed |
| Op2 — image replacement | 2/2 | Open/save/PDF-export all pass | Picture at exact marker geometry | Picture shape present, rels correct |
| Op3 — SmartArt injection | 2/2 | Open/save/PDF-export all pass | PowerPoint renders diagram correctly | `<p:graphicFrame>` with all 4 diagram rels |

Three API corrections folded into Section 3.4 above:
1. `ImagePart.new(package, Image)` — not `(package, blob, ct, ext)`. Use `Image.from_file()`.
2. `InjectionRequest.placeholder_name` accepts the marker string directly — the plan's marker-renaming step is unnecessary.
3. Flat-list SmartArt items must be plain strings — dicts raise `FlatListBuildError`.

One non-blocking cosmetic issue surfaced and got a contract resolution: marker-adjacent body text clearing (Section 3.4 step 4).

## Related

- GitHub issue: #53
- EPIC #40 (plugin marketplace — plugin architecture)
- #38 / PR #39 (pptx_native SmartArt engine)
- PR #50 (cross-tier prompt refinement loop)
- #45 / PR #46 (template-driven layouts — template analyser)
- [Spike 1: /pptx marker adherence](../../spikes/2026-04-23-pptx-marker-adherence/README.md) (2026-04-23)
- [Spike 2: python-pptx enrichment](../../spikes/2026-04-23-python-pptx-enrichment/README.md) (2026-04-23)
