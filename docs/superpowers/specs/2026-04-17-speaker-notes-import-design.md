# Speaker Notes Import — Design Spec

**Issue:** #44
**Date:** 2026-04-17
**Status:** Approved

## Summary

Allow speakers to provide per-slide narrative notes in an external file (.md or .txt), which are imported, matched to slides, and enriched with timing/cues by the existing speaker-notes-writer. This enables voiceover auto-generation and self-presenting visual-heavy decks.

## Scope

Three modes, all supported:

1. **Generate** (existing, unchanged) — no external file, writer generates notes from outline via collaborative preferences gathering
2. **Import + enrich** (new) — external file provides narrative text per slide, writer adds timing markers, cues, and fills gaps for slides without external notes
3. **Interactive on demand** (existing, unchanged) — speaker asks Jack Tar to generate notes at any point

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Input format | Markdown or plain text with per-slide blocks | Natural authoring for talk scripts |
| Delimiter matching | Flexible — heading with number, number marker, or headline fuzzy match | Speakers may not know slide numbers when writing notes early |
| Writer interaction | Enrich external notes (timing/cues) + generate for uncovered slides | Voiceover needs accurate timing; speaker's narrative stays untouched |
| Unmatched blocks | Warn and skip | Forgiving — typos shouldn't block a deck build |
| Assembler changes | None | Both assemblers already consume speaker-notes.json identically |

## Architecture

### 1. Notes Parser Module

**New file: `src/notes_parser.py`**

Reads an external notes file and produces structured per-slide blocks matched to the outline.

**Parsing rules:**
- Split file into blocks using any of these delimiters:
  - Markdown heading with number: `## Slide 3: The Problem`
  - Markdown heading without number: `## The Problem`
  - Number marker: `[3]` or `[Slide 3]`
- Each block's text is everything between one delimiter and the next, stripped of leading/trailing whitespace
- Blank lines within a block are preserved (paragraph breaks in the narrative)
- If no delimiters are found, the entire file is treated as a single block assigned to slide 1. This handles the edge case of a plain file with no structure — the speaker gets a warning that all text was assigned to slide 1

**Matching priority (per block):**
1. **Explicit slide number** — if the delimiter contains a number, match directly to that slide
2. **Headline match** — fuzzy match the delimiter text against `slide.headline` in the outline using `difflib.SequenceMatcher`. Match if ratio > 0.7 or if one is a substring of the other (case-insensitive, punctuation stripped)
3. **Unmatched** — add to warnings list, skip the block

**Timing calculation:**
- `estimate_timing(text, wpm=130)` — word count / WPM * 60 = estimated_seconds
- Cumulative timing markers formatted as `~M:SS`

**Key functions:**
- `parse_notes_file(file_path) -> list[dict]` — returns `[{'raw_label': str, 'slide_number': int|None, 'headline_hint': str|None, 'text': str}]`
- `match_notes_to_outline(parsed_blocks, outline) -> tuple[dict, list]` — returns `({slide_number: text}, [warning_strings])`
- `estimate_timing(text, wpm=130) -> int` — returns estimated_seconds
- `build_timing_markers(notes_dict, wpm=130) -> dict` — returns `{slide_number: {'estimated_seconds': int, 'timing_marker': str}}`

**No external dependencies** beyond stdlib. Fuzzy matching uses `difflib.SequenceMatcher`.

### 2. TalkBrief Schema Extension

**Modified file: `src/schemas/talk_brief.schema.json`**

Add one optional field to the `preferences` object:

```json
"speaker_notes_path": {
  "type": "string",
  "description": "Path to an external speaker notes file (.md or .txt). When provided, notes are imported and enriched with timing/cues instead of being generated from scratch."
}
```

The existing `include_speaker_notes` boolean (default true) stays unchanged. Interaction:
- `include_speaker_notes: true` + no path = generate (existing default)
- `include_speaker_notes: true` + path set = import + enrich
- `include_speaker_notes: false` = no notes at all (path ignored)

### 3. Speaker Notes Writer Skill Modification

**Modified file: `plugins/jack-tar-deckhand/skills/speaker-notes-writer/SKILL.md`**

The skill gains a branching flow at the start:

**Detection:** Before preferences gathering, check if the TalkBrief has `preferences.speaker_notes_path`.

**Import mode (path provided):**
1. Read the file via `notes_parser.parse_notes_file(path)`
2. Match to outline via `match_notes_to_outline(blocks, outline)`
3. Report warnings to the Speaker (which blocks didn't match)
4. Enrich each matched slide:
   - `estimated_seconds` from word count at 130 WPM
   - `timing_marker` from cumulative seconds
   - `cues` — generate contextual transition/emphasis/interaction cues (LLM reasoning, same as generation mode)
5. **Fill gaps:** For slides in the outline that have no external notes, generate notes as normal (generation mode for those slides only)
6. Write `speaker-notes.json` — identical schema output

**Generation mode (no path):** Existing flow unchanged — preferences gathering, full generation.

The enrichment timing is computed by `notes_parser.estimate_timing()` and `build_timing_markers()`. Cue generation stays in the skill's LLM reasoning (contextual, not mechanical).

### 4. Pipeline Integration

**No new pipeline step.** The existing `speaker-notes-writer` step handles both modes internally. The skill detects the mode from the TalkBrief.

**Conductor change:** Minor documentation note on Step 4:
> "If the TalkBrief provides `preferences.speaker_notes_path`, the writer imports and enriches external notes instead of generating. Slides without external notes are generated as normal."

**Assembler changes: None.** Both JS and python-pptx assemblers already consume `speaker-notes.json` and only use the `text` field. Output schema is identical regardless of source.

**QA changes: None.** QA checks don't validate notes content.

### 5. File Layout

**New files:**

| File | Purpose |
|---|---|
| `src/notes_parser.py` | Parse external notes files, match to outline, timing calculation |
| `tests/test_notes_parser.py` | Parser and matching tests (~24 tests) |
| `tests/fixtures/notes/heading-based.md` | Test fixture — heading delimiters |
| `tests/fixtures/notes/number-markers.txt` | Test fixture — number delimiters |
| `tests/fixtures/notes/headline-only.md` | Test fixture — headline fuzzy match |
| `tests/fixtures/notes/mixed-format.md` | Test fixture — mixed delimiters |
| `tests/fixtures/notes/partial-coverage.md` | Test fixture — some slides only |
| `tests/fixtures/notes/unmatched.md` | Test fixture — unmatched block |

**Modified files:**

| File | Change |
|---|---|
| `src/schemas/talk_brief.schema.json` | Add `speaker_notes_path` to `preferences` |
| `plugins/jack-tar-deckhand/skills/speaker-notes-writer/SKILL.md` | Add import/enrich branch at start of flow |
| `plugins/jack-tar-deckhand/agents/deck-conductor.md` | Minor note on Step 4 about external notes |

Plugin copies synced in same commits.

### 6. Test Strategy

**Test fixtures:** 6 notes files covering heading-based, number markers, headline-only, mixed format, partial coverage, and unmatched blocks.

**Test coverage:**

| Module | Tests | Coverage |
|---|---|---|
| Parsing | ~12 | Heading-based, number markers, headline-only, mixed formats, empty file, no delimiters (single block), whitespace handling, paragraph preservation |
| Matching | ~8 | Exact number match, headline fuzzy match, substring containment, unmatched warnings, partial coverage, duplicate slide number |
| Timing | ~4 | Word count to seconds, cumulative markers, empty text, wpm override |
| Integration | ~4 | Import + enrich produces valid schema, gap-filling, full pipeline with notes file, no path falls back to generation |

**Estimated total: ~28 new tests**

### 7. What This Does NOT Cover

- Voiceover/TTS generation from notes (downstream consumer — not part of this feature)
- Notes editing UI (notes are authored externally)
- Rich formatting in notes (markdown is stripped to plain text for the notes field)
- Notes versioning or diff between external file and generated notes
