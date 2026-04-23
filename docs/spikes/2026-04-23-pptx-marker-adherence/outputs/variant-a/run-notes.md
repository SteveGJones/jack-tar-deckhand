# Variant A — Run notes

- **Timestamp:** 2026-04-23 (local, Darwin)
- **Brief:** `docs/spikes/2026-04-23-pptx-marker-adherence/briefs/brief-a-minimal.md`
- **Skill invoked:** `document-skills:pptx`

## Build script emitted

- **Yes.** `build.js` saved alongside `presentation.pptx`.
- Generator: `pptxgenjs@4.0.1` (npm global, resolved via `NODE_PATH=$(npm root -g)`).
- Path: `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-a/build.js`

## Observable behaviour

- The skill provided a generic PPTX tutorial entry-point. It did **not** interactively ask clarifying questions and did **not** explicitly acknowledge or object to the marker instructions in the brief — the marker instructions are brief-level, and the skill's README covers general pptx creation without marker-specific guidance.
- The skill did surface its QA workflow (markitdown text extraction + soffice → pdftoppm visual pass with a subagent). I executed the content + visual QA steps locally (markitdown wasn't installed in this venv, so I substituted `python-pptx` shape-name introspection, which actually suits the marker-adherence check better).
- No clarifying questions were raised by the skill; it emitted design guidance (palette, type pairing, layout suggestions, "every slide needs a visual element") that I mapped onto the brief's marker scheme.

## How markers were realised

Marker placeholders were emitted as rectangular shapes with:

- `objectName: "IMAGE:..."` / `"SMARTART:..."` / `"BG:..."` — this is the PPTX shape name that downstream tooling can match on.
- A faint ice-blue dashed-outline fill so the marker is visually legible in a draft deck.
- A sibling italic text run with the same marker prefix repeated, to make the marker discoverable even if shape names are stripped.

Marker tally (from `python-pptx` shape-name read-back):

| Prefix     | Count | Slides                    | Brief minimum |
|------------|-------|---------------------------|---------------|
| `IMAGE:`   | 3     | 2 (demo-vs-prod), 6 (memory layers), 9 (case-study dashboard) | ≥ 2 |
| `SMARTART:`| 3     | 4 (three pillars), 5 (planning loop), 7 (tool-call sequence) | ≥ 1 |
| `BG:`      | 2     | 1 (title hero), 8 (case-study intro) | ≥ 1 |

All minimums met.

## File sizes

| File              | Size     |
|-------------------|----------|
| `presentation.pptx` | 157,465 B (~154 KB) |
| `build.js`          | 15,354 B  (~15 KB)  |

## Surprising choices

- The skill defaulted to "design ideas" rather than a structured TalkBrief → outline → design loop. Brief A's marker instructions were one-line prose; the skill neither flagged them nor treated them as contractual. Adherence here is driven by me reading the brief and encoding markers as `objectName`, not by the skill enforcing them.
- The skill's QA recipe assumes `markitdown` is installed globally; it wasn't in this worktree's venv. Substituted `python-pptx` — which is a stronger marker-check anyway, since `markitdown` strips shape names. Worth flagging for the spike scoring logic.
- `pptxgenjs` silently shortens `objectName` to the shape's displayed name in the .pptx (verified via python-pptx read-back — the full `"IMAGE:demo-vs-prod-split"` string is preserved verbatim as the shape name). Good signal that the marker contract survives the round trip.
- I omitted any external image generation (Ollama / cloud) because the brief says "leave a placeholder shape" — the markers are the deliverable, not rendered content.

## What I did not do

- Did not modify the brief.
- Did not strengthen marker instructions beyond the brief's wording.
- Did not invoke any other engine plugins (smartart, image gen) — markers stay as placeholders per Variant A's scope.
