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

> **Validated by [Spike 3](../../spikes/2026-04-23-analyser-source-comparison/README.md) on 2026-04-23.** The HYBRID source strategy below was selected from a three-way empirical comparison (OOXML-only / JS-only / HYBRID) across four real cases.

**Input:** The .pptx file path. The Node.js build script (`build.js`), if present in the same directory, is consumed as a targeted fallback only.

#### Primary analysis — OOXML via python-pptx

The analyser opens the .pptx with python-pptx and extracts per-slide information directly from OOXML:

- **Marker shape names** via `<p:cNvPr @name>` matching `^(IMAGE|SMARTART|BG):[A-Za-z0-9_-]+$`
- **Marker geometry** via `<a:xfrm>` child elements (left / top / width / height in EMU)
- **Text content** via `<a:t>` descendants across every text frame
- **Background state** via both `<p:bg><p:bgPr>` (image / solid / gradient fills) **and** the slide element's `bgColor` attribute (PptxGenJS emits colour backgrounds via `bgColor`, not `<p:bg>` — Spike 3 observed a 0/10 agreement on this field when `bgColor` was ignored)
- **Element types present** (charts, tables, images, plain text, shapes) via python-pptx's `MSO_SHAPE_TYPE`

OOXML is chosen as primary because it is a stable, schema-defined format that is available in every case — including user-edited decks, Keynote exports, and corporate templates that have no `build.js` alongside them. Spike 3's "control" case proved that OOXML analysis produces useful results even when the build script is entirely absent.

**Security:** all XML parsing uses `lxml.etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)`. See the Security & Privacy section for the full input-validation contract.

#### Fallback — JS build-script parsing for marker extraction only

When **all three** conditions hold, the analyser additionally parses `build.js` via the `esprima` Python package (AST-based, read-only — the script is **never executed, imported, required, or spawned as a subprocess**):

1. OOXML analysis produced **zero markers** (the brief likely used PptxGenJS's `name` property which PptxGenJS 4.0.1 silently drops — see Section C in Phase 1).
2. A file named `build.js` exists in the same directory as the .pptx.
3. JS parsing does not raise — if it does, the analyser logs the error and reports "no markers" rather than propagating.

The JS fallback extracts marker information from `slide.addShape(..., { objectName|name: "IMAGE:...", x, y, w, h })` calls, resolving PptxGenJS helper-function indirection (Spike 3 found three idioms across three real variants: block-scoped slide bindings, helper functions taking slide as parameter, and ObjectPattern destructuring with template-literal marker construction).

Because the JS fallback runs **only** when OOXML already found zero markers, the complexity of JS parsing is quarantined away from the primary path. A JS parse failure degrades the deck to "no markers found" plus a user-facing diagnostic — the same failure mode as OOXML-only analysis.

Spike 1's originally-proposed text-scan fallback (scan slide body text for marker strings when OOXML shape names are absent) is **subsumed by the JS fallback**. The marker strings appear in the JS source via `addText()` calls, so parsing the JS covers the same cases that text-scanning the rendered OOXML would cover, with the added benefit of recovering positional information. A text-scan mode was evaluated during Spike 3 and rejected as redundant.

#### Classification per slide

| Category | Criteria | Enrichment |
|----------|----------|------------|
| Marker: IMAGE | Shape named `IMAGE:*` | AI element image at marker position |
| Marker: SMARTART | Shape named `SMARTART:*` | Editable SmartArt replacing marker |
| Marker: BG | Shape named `BG:*` (geometry is IGNORED — BG applies to the slide background, not to the marker's rectangle) | AI atmospheric background |
| Text-heavy (unmarked) | High text density, no images/charts | Candidate for AI background |
| List/process (unmarked) | Bullet points matching SmartArt patterns | Candidate for SmartArt |
| Already rich | Has charts, images, complex layout | Leave alone |

Unmarked slides can still be proposed for enrichment based on content analysis — markers just make it explicit and provide positioning.

#### Marker uniqueness and grammar

- **Grammar:** `^(IMAGE|SMARTART|BG):[A-Za-z0-9_-]+$`. The identifier after the colon is lowercase letters, digits, hyphens, underscores.
- **Semantics of the identifier:** for `IMAGE:` and `BG:`, the identifier is a descriptive slug (e.g. `IMAGE:agent-architecture`, `BG:dramatic-opening`). For `SMARTART:`, the identifier hints at the graphic's *subject*, not the catalog layout ID — e.g. `SMARTART:three-pillars`, not `SMARTART:process1`. Layout selection is a separate step in Section 3.3 and uses the SmartArt item count plus graphic-type detection, not the slug.
- **Uniqueness:** marker identifiers must be unique within a deck. Duplicate identifiers are a brief-authoring error; the analyser flags them for user resolution before proceeding.

#### SMARTART marker-adjacent text — verifier (analyser-side)

For every slide carrying a `SMARTART:*` marker, the analyser additionally checks whether any **other** shape's bounding box on that slide intersects the marker's geometry. If an overlap is found, the analyser reports it in the enrichment menu with three user options: **proceed anyway** (accept faint residual text behind the injected SmartArt), **clear overlapping text** (remove the conflicting shape at enrichment time), or **drop this enrichment**.

This replaces the earlier "brief-side contract" where the brief asked the superpower to leave SMARTART slides uncluttered — Spike 2 surfaced the cosmetic issue, but a brief-side promise is unverifiable. The analyser-side verifier makes the contract enforceable at deck-reading time.

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

4. **All-or-nothing application (transactional gate).** Enrichments are applied against a single in-memory `Presentation` object held open throughout the ops cycle. Op1 and Op2 mutate the in-memory tree; the object is saved to a temporary file (`presentation-enriched.pptx.tmp-<pid>`) only after BOTH succeed. SmartArt injection (Op3) then runs against the saved temp file using `assembler_patch.inject()`, which is itself read-all → mutate → write-fresh internally. If every op has succeeded, the temp file is renamed to `presentation-enriched.pptx` via `os.replace()` (atomic on POSIX). If any op raises, the temp file is discarded and no output is produced. This gives all-or-nothing semantics: the user never receives a half-enriched deck. The SMARTART analyser-side verifier (Section 3.1) catches overlap issues BEFORE enrichment begins, so any shape-removal for overlap resolution happens during Op2-equivalent preparation, not mid-injection.

5. **Handle SMARTART marker-adjacent text clearing.** If the analyser's verifier (Section 3.1) flagged overlapping shapes on a SMARTART slide AND the user selected "clear overlapping text", the enrichment step removes those shapes from the in-memory tree before Op3 runs. If the user selected "proceed anyway", no clearing happens and the user accepts the known cosmetic trade-off. If the user selected "drop this enrichment", the SMARTART op is skipped entirely (the marker shape is NOT removed from the deck so the user can re-run later).

6. **Render for review** — convert the temporary enriched .pptx to slide images via LibreOffice → PDF → pdftoppm (same toolchain the superpower uses). SmartArt slides will render poorly in LibreOffice but AI images and backgrounds will be visible. For authoritative visual verification of SmartArt, use PowerPoint Mac via [tools/pptx_to_pdf.sh](../../../tools/pptx_to_pdf.sh) (forces SmartArt cache regen on save).

7. **Internal deck review** — view every slide image:
   - Do AI backgrounds overpower the text? (contrast, readability)
   - Do element images fit their allocated space?
   - Is the visual style cohesive across enriched slides?
   - Do enriched slides feel consistent with non-enriched slides?
   - Any slides where the enrichment made things worse?

8. **Fix issues** — regenerate images, adjust, or drop an enrichment. When a fix is applied, the entire enrichment cycle is re-run from step 1 against a fresh copy of the source .pptx — we never patch a previously-enriched output. This keeps the all-or-nothing semantics intact even across iteration rounds.

### 3.5 Delivery

Only after internal review passes, present the enriched deck to the user:

- Show the enriched slide images with a summary of what was applied
- Report the cost incurred (Ollama iterations are free, cloud costs itemised)
- The user can accept, request changes to specific enrichments, or drop any they don't like

**Output files:**
- `presentation-enriched.pptx` — the enriched deck (original untouched)
- `enrichment-report.md` — what was applied, costs, any SmartArt that needs PowerPoint to render

**PDF conversion note:** The superpower's text-only decks convert cleanly to PDF. AI backgrounds and element images also survive PDF conversion (they're embedded raster images). SmartArt may not render correctly in LibreOffice PDF export — the enrichment report flags this and recommends PowerPoint for PDF export if SmartArt was applied.

## Security & Privacy

The bridge reads user-authored .pptx files, parses user-influenced JS, writes modified .pptx files, and sends prompts derived from user briefs to external cloud providers. The review panel (security-architect lens) surfaced five risks that the implementation must address. They are captured here as hard contracts on the plugin's behaviour.

### Image-path allowlist (High — addresses review C1)

Any path passed to `python-pptx`'s image-loading APIs (`Image.from_file()`, `slide.shapes.add_picture()`) is **resolved against an explicit allowlist of directories** before loading. The default allowlist is:

- The working directory's `generated/` subdirectory (where the imagegen-bridge writes AI-generated images for this run)
- The plugin's run-local `carriers/` subdirectory (SmartArt carrier files)

After `Path(p).resolve()`, the path MUST satisfy `path.is_relative_to(allowed_root)` for at least one allowed_root. Symlinks are rejected outright (`path.is_symlink()` short-circuits to an error). Paths failing this check raise a hard error; they are never embedded into the output .pptx.

This prevents a malicious or mistake-filled brief from directing the bridge to embed arbitrary files (`~/.ssh/id_rsa`, `~/.aws/credentials`, arbitrary workspace files) as "PNG" parts in the output — python-pptx validates content-type headers but still embeds the raw bytes of anything it accepts as an image, which can exfiltrate sensitive files via a seemingly-innocuous deck.

### JS parsing is read-only (High — addresses review C2)

The JS fallback parser in Section 3.1 **never executes, imports, `require()`s, or spawns** the build script. It uses `esprima.parseScript()` with `tolerant=True` against the source text, then walks the AST. The allowed operations on a loaded build script are: read the AST, walk it, extract literal values. Any code path that would run or even partially evaluate user-authored JavaScript is prohibited.

This contract is testable — a simple test asserts that no `subprocess`, `eval`, `exec`, or module-import API is called during analyser execution on a build.js that *would* misbehave if run (e.g. one that `require('child_process').execSync(...)` inside a top-level call).

### .pptx input hardening (Medium-High — addresses review C3)

Every loaded .pptx must pass pre-flight checks before python-pptx opens it:

- **Decompressed size ceiling:** 200 MB. Refuse files whose compressed→decompressed ratio exceeds 100:1 (zip-bomb signal).
- **Part count ceiling:** 2,000 parts per package.
- **Per-part size ceiling:** 50 MB.
- **XML parser configuration:** `lxml.etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)` everywhere slide XML is parsed by bridge code — not just in the fallback path. This shuts down XXE and DTD-expansion attacks at the parser level.

These checks are front-loaded: a failing file is rejected before any enrichment work starts. The error is surfaced to the user with a diagnostic naming the specific check that failed.

### Atomic file writes (Medium — addresses review C4)

The output `presentation-enriched.pptx` is written via the pattern described in Section 3.4 step 4 — write to `presentation-enriched.pptx.tmp-<pid>` in the same directory, `fsync`, then `os.replace()` to the final name. Atomic on POSIX. If the destination file exists and is locked (PowerPoint has it open on macOS, or Windows file-lock semantics), the rename fails loudly with a "close PowerPoint first" diagnostic. The bridge never leaves a half-written output file on disk.

Timestamped backup of any pre-existing `presentation-enriched.pptx` before overwrite is NOT automatic — the user can request it via a flag, but defaulting to non-destructive writes would create unbounded on-disk clutter for users who iterate repeatedly.

### Privacy tiering for cloud providers (Medium — addresses review D1)

Briefs contain audience context, product names, and narrative intent. When the bridge escalates AI image generation from Ollama to cloud providers (Nanobanana, Imagen, FLUX via FAL), it sends user-authored prompt text — derived from the brief — to external APIs. For users handling confidential material this is an exfiltration risk.

The brief gains a `confidentiality` field with three values:

| Tier | Behaviour |
|------|-----------|
| `public` | Default. Full Ollama-first pipeline, cloud escalation allowed, prompts sent to cloud providers as-is. |
| `internal` | Cloud escalation allowed, but before the FIRST cloud call per run the bridge prompts the user for explicit confirmation, showing the exact prompt text about to be sent and the provider URL. |
| `restricted` | Cloud providers are DISABLED. Ollama is the only image source. If the brief wants cloud-quality results on a restricted deck, the user is told explicitly and asked to relax the tier or drop the enrichment. |

The tier defaults to `public` if the brief does not set it — existing jack-tar users see no change in behaviour.

### Budget cap (Medium — addresses review D3, converged recommendation)

The `/enrich-deck` invocation accepts a `budget_cap_usd` flag (default: **$1.00**). Every cloud API call's cost is deducted from a running total maintained in `image_bridge.py`. When the remaining budget falls below the cheapest-available cloud provider's per-call cost, the bridge halts cloud generation and either:

- Falls back to Ollama (free) if the affected enrichment tolerates draft quality.
- Stops and reports to the user with the per-enrichment cost ledger so far plus the remaining slides unspent.

The cap is a hard ceiling, not a suggestion. The user raises it by re-running with `--budget-cap=N.NN`.

### Supply-chain note (Medium)

The bridge imports from `plugins/jack-tar-msft-smartart/src` via PLUGIN_ROOT discovery (the same pattern every jack-tar plugin uses, documented in CLAUDE.md). This grants the msft-smartart plugin code execution inside the bridge's Python process. Two mitigations:

1. Plugin versions are pinned in `plugin.json`. Breaking-change versions of msft-smartart require an explicit bridge version bump.
2. The imported surface is named explicitly (`engine.render`, `assembler_patch.InjectionRequest`, `assembler_patch.inject`). Any expansion requires a spec amendment.

## Plugin Structure

New plugin: `jack-tar-superpower-bridge`

```
plugins/jack-tar-superpower-bridge/
  .claude-plugin/
    plugin.json             # Dependencies include esprima (>=4.0.1) for JS fallback
  requirements.txt          # esprima, python-pptx, lxml (explicit pins)
  skills/
    bridge-brief/
      SKILL.md              # Phase 1: narrative pre-brief
    enrich-deck/
      SKILL.md              # Phase 3: analyse + propose + apply
  agents/
    enrichment-cohesion-reviewer.md   # Deck-level visual review persona
  src/
    analyser.py             # OOXML primary (python-pptx); JS fallback (esprima)
    enrichment.py           # Apply enrichments via python-pptx, transactional gate
    placeholder.py          # Placeholder protocol — find/parse/remove markers
    smartart_bridge.py      # Spec construction + carrier render + injection
    image_bridge.py         # Draft/review cycle for AI images + budget tracking
    security.py             # Image-path allowlist, .pptx pre-flight, XML parser config
    enrichment_report.py    # Structured enrichment report writer (see Enrichment Report Schema below)
  tests/
    test_analyser.py
    test_enrichment.py
    test_placeholder.py
    test_smartart_bridge.py
    test_image_bridge.py
    test_security.py
    test_contract_pptx_superpower.py  # Pinned fixtures + /pptx behaviour contract tests
  docs/
    personas.md             # AI Persona definitions (see Personas section below)
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

2. **OOXML primary, JS build script fallback (HYBRID).** The analyser reads the .pptx via python-pptx as the primary source — OOXML is a stable schema, available in every case including non-/pptx decks (Keynote exports, corporate templates). The JS build script is parsed as a narrow fallback ONLY when OOXML finds zero markers AND `build.js` exists alongside the .pptx; this covers briefs that used the wrong PptxGenJS property key (Spike 1's `name`/`objectName` finding). Spike 3 proved each source has a failure mode the other doesn't — OOXML misses markers when the brief drifts; JS is unusable without a build script. The hybrid exploits both strengths without inheriting JS's primary-path complexity.

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
| Build script format changes | JS fallback parser silently under-matches on a new /pptx idiom | JS is a fallback only (used when OOXML finds zero markers). Primary path is OOXML, which has a stable schema and does not depend on build-script formatting. A JS parse failure degrades to "no markers found" — the same diagnosable failure mode as OOXML-only analysis. | **Spike 3:** confirmed. Three /pptx variants generated 48 hours apart required three rounds of JS-parser feature additions; this variability is exactly why JS is not the primary path. |
| python-pptx and PptxGenJS produce subtly different OOXML | Enrichment corrupts superpower's output | Validate with PPTXSchemaValidator after enrichment; test on real superpower output | **Spike 2:** all three ops pass against real PptxGenJS-produced OOXML with no corruption. File-size drop (python-pptx compacts zip) is cosmetic, not lossy. |
| User confusion about three-phase flow | Abandonment, partial usage | Clear invocation names, brief explains the full flow, each phase works independently | Not spiked. To be assessed via dogfooding once v1 ships. |
| Marker-adjacent body text bleeds through injected SmartArt | Visual artefact on SMARTART slides | Analyser-side verifier (Section 3.1) detects geometric overlap and surfaces 3 user options (proceed / clear overlapping text / drop enrichment) BEFORE enrichment runs. Replaces the earlier brief-side promise, which was unverifiable. | **Spike 2:** issue observed; now addressed by a verifiable analyser check rather than a brief-side contract. |
| Arbitrary file read via image paths | Attacker-influenced brief could embed `~/.ssh/id_rsa` as a "PNG" | Image-path allowlist: resolve paths, enforce `is_relative_to(allowed_root)`, reject symlinks. See Security & Privacy § Image-path allowlist. | Not spiked. Contract captured; implementation must ship with tests. |
| JS build script execution | Malicious build.js could `require('child_process').execSync(...)` if the parser ever runs it | Parser is AST-only via `esprima.parseScript()`. No `eval`, no `require`, no subprocess spawning. Testable via assertion on which APIs are called. See Security & Privacy § JS parsing is read-only. | Not spiked. Contract captured; implementation tests this. |
| .pptx zip-bomb / XXE / part-explosion | Malicious .pptx could exhaust resources or exfiltrate via XXE | Pre-flight checks: decompressed size ≤200 MB, part count ≤2000, per-part ≤50 MB. XML parser hardened with `resolve_entities=False, no_network=True, huge_tree=False`. | Not spiked. Contract captured. |
| PII exfiltration to cloud providers | Brief prompts sent to Nanobanana/Imagen/FLUX may contain confidential names | Brief `confidentiality` tier: `public` (default), `internal` (explicit confirmation before first cloud call), `restricted` (Ollama-only). See Security & Privacy § Privacy tiering. | Not spiked. Tier mechanism captured. |
| Unbounded cloud spend | A single run could accidentally cost many dollars on Nanobanana Pro | `budget_cap_usd` input (default $1.00), hard ceiling, per-call cost deducted. See Security & Privacy § Budget cap. | Not spiked. Cap mechanism captured. |
| OOXML misses colour-only backgrounds | Slides with PptxGenJS `bgColor` (no `<p:bg>`) misclassified | Analyser checks both `<p:bg>` AND slide element's `bgColor` attribute (Section 3.1). | **Spike 3:** observed 0/10 background agreement before fix; now required. |

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
