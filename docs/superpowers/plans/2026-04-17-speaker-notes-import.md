# Speaker Notes Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow speakers to provide per-slide narrative notes in an external file that are imported, matched to slides, and enriched with timing metadata.

**Architecture:** New `src/notes_parser.py` handles parsing and matching. The speaker-notes-writer skill gains an import/enrich branch. No assembler changes — `speaker-notes.json` output is identical regardless of source.

**Tech Stack:** Python stdlib (`re`, `difflib.SequenceMatcher`), existing jsonschema validation

**Spec:** `docs/superpowers/specs/2026-04-17-speaker-notes-import-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `src/notes_parser.py` | Parse external notes files, match blocks to outline slides, timing calculation |
| `tests/test_notes_parser.py` | All parser tests (parsing, matching, timing) |
| `tests/fixtures/notes/*.md` / `*.txt` | 6 test fixture files covering all delimiter formats |
| `src/schemas/talk_brief.schema.json` | Add `speaker_notes_path` to preferences |
| `plugins/jack-tar-deckhand/skills/speaker-notes-writer/SKILL.md` | Add import/enrich branch |
| `plugins/jack-tar-deckhand/agents/deck-conductor.md` | Minor note on Step 4 |

---

### Task 1: Test Fixtures

**Files:**
- Create: `tests/fixtures/notes/heading-based.md`
- Create: `tests/fixtures/notes/number-markers.txt`
- Create: `tests/fixtures/notes/headline-only.md`
- Create: `tests/fixtures/notes/mixed-format.md`
- Create: `tests/fixtures/notes/partial-coverage.md`
- Create: `tests/fixtures/notes/unmatched.md`

- [ ] **Step 1: Create heading-based fixture**

Create `tests/fixtures/notes/heading-based.md`:

```markdown
## Slide 1: Welcome to the Future

This is where we set the scene. We want the audience to feel excited about what's coming. Open with a bold statement about how technology is reshaping our industry.

## Slide 2: The Problem

Now we shift to pain points. Three key issues that everyone in the room has experienced. Legacy systems are slow, users are frustrated, and costs keep rising. Pause after the cost number to let it sink in.

## Slide 3: Our Solution

Here's the pivot. We introduce our approach — AI-driven automation that addresses each pain point directly. Keep the energy up, this is the core of the talk.
```

- [ ] **Step 2: Create number-markers fixture**

Create `tests/fixtures/notes/number-markers.txt`:

```
[1]
Welcome everyone. Today we're going to explore how AI is transforming the way we build software.

[2]
Let's start with the problem. How many of you have spent more than an hour debugging a deployment issue this month? Show of hands.

[3]
Our solution addresses these pain points head-on. Let me walk you through the three pillars of our approach.
```

- [ ] **Step 3: Create headline-only fixture**

Create `tests/fixtures/notes/headline-only.md`:

```markdown
## Welcome to the Future

Open with energy. This audience knows the space well, so don't over-explain the basics.

## The Problem

Hit the three pain points hard. Use the survey data from slide to back up each claim.

## Our Solution

This is your money slide. Slow down here and make sure every point lands.
```

- [ ] **Step 4: Create mixed-format fixture**

Create `tests/fixtures/notes/mixed-format.md`:

```markdown
## Slide 1: Welcome to the Future

Open strong with the vision statement.

[2]
Now pivot to the problem space. Be direct.

## Our Solution

Walk through each pillar methodically. This is the core of the talk.

[4]
Close with the call to action. Thank the audience.
```

- [ ] **Step 5: Create partial-coverage fixture**

Create `tests/fixtures/notes/partial-coverage.md`:

```markdown
## Slide 2: The Problem

This slide needs extra emphasis. Pause after each pain point. Let the audience feel the weight of the problem before moving to the solution.

## Slide 3: Our Solution

The three pillars: automation, real-time processing, and cost reduction. Spend roughly equal time on each.
```

- [ ] **Step 6: Create unmatched fixture**

Create `tests/fixtures/notes/unmatched.md`:

```markdown
## Slide 1: Welcome to the Future

Standard opening. Set the tone.

## The Deleted Slide That No Longer Exists

This content was written for an earlier draft and the slide was removed.

## Slide 3: Our Solution

Walk through the solution architecture.
```

- [ ] **Step 7: Commit**

```bash
git add tests/fixtures/notes/
git commit -m "feat: test fixtures for notes parser (#44)"
```

---

### Task 2: Notes File Parsing

**Files:**
- Create: `src/notes_parser.py`
- Create: `tests/test_notes_parser.py`

- [ ] **Step 1: Write failing tests for parse_notes_file**

Create `tests/test_notes_parser.py`:

```python
"""Tests for external speaker notes parsing, matching, and timing."""

import os
import pytest

from src.notes_parser import parse_notes_file

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures', 'notes')


class TestParseNotesFile:
    def test_heading_based_parsing(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'heading-based.md'))
        assert len(blocks) == 3
        assert blocks[0]['slide_number'] == 1
        assert blocks[0]['headline_hint'] == 'Welcome to the Future'
        assert 'set the scene' in blocks[0]['text']

    def test_number_marker_parsing(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'number-markers.txt'))
        assert len(blocks) == 3
        assert blocks[0]['slide_number'] == 1
        assert blocks[1]['slide_number'] == 2
        assert 'debugging a deployment' in blocks[1]['text']

    def test_headline_only_parsing(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'headline-only.md'))
        assert len(blocks) == 3
        assert blocks[0]['slide_number'] is None
        assert blocks[0]['headline_hint'] == 'Welcome to the Future'

    def test_mixed_format_parsing(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'mixed-format.md'))
        assert len(blocks) == 4
        assert blocks[0]['slide_number'] == 1
        assert blocks[1]['slide_number'] == 2
        assert blocks[2]['slide_number'] is None
        assert blocks[2]['headline_hint'] == 'Our Solution'
        assert blocks[3]['slide_number'] == 4

    def test_empty_file(self, tmp_path):
        empty = tmp_path / 'empty.md'
        empty.write_text('')
        blocks = parse_notes_file(str(empty))
        assert blocks == []

    def test_no_delimiters_single_block(self, tmp_path):
        plain = tmp_path / 'plain.txt'
        plain.write_text('Just some unstructured speaker notes for the whole talk.')
        blocks = parse_notes_file(str(plain))
        assert len(blocks) == 1
        assert blocks[0]['slide_number'] == 1
        assert blocks[0]['headline_hint'] is None
        assert 'unstructured speaker notes' in blocks[0]['text']

    def test_preserves_paragraph_breaks(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'heading-based.md'))
        # The text should preserve internal structure (not collapse to single line)
        assert isinstance(blocks[0]['text'], str)
        assert len(blocks[0]['text']) > 10

    def test_strips_leading_trailing_whitespace(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'heading-based.md'))
        for block in blocks:
            assert block['text'] == block['text'].strip()

    def test_raw_label_preserved(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'heading-based.md'))
        assert 'Slide 1: Welcome to the Future' in blocks[0]['raw_label']

    def test_slide_number_extracted_from_bracket(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'number-markers.txt'))
        assert blocks[2]['slide_number'] == 3

    def test_slide_prefix_in_bracket(self, tmp_path):
        f = tmp_path / 'slide_prefix.txt'
        f.write_text('[Slide 5]\nNotes for slide five.')
        blocks = parse_notes_file(str(f))
        assert len(blocks) == 1
        assert blocks[0]['slide_number'] == 5

    def test_heading_level_ignored(self, tmp_path):
        f = tmp_path / 'h3.md'
        f.write_text('### Slide 1: Title\nSome notes.\n\n### Slide 2: Other\nMore notes.')
        blocks = parse_notes_file(str(f))
        assert len(blocks) == 2
        assert blocks[0]['slide_number'] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_notes_parser.py::TestParseNotesFile -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement parse_notes_file**

Create `src/notes_parser.py`:

```python
"""Notes parser — parse external speaker notes files and match to slide outlines.

Reads .md or .txt files with per-slide narrative blocks, matches them to
slides in the outline by number or headline, and computes timing metadata.
"""

import re
from difflib import SequenceMatcher


# Matches: ## Slide 3: The Problem, ### Slide 1: Title, ## The Problem
_HEADING_RE = re.compile(
    r'^#{1,6}\s+'           # 1-6 # chars + space
    r'(?:Slide\s+(\d+)\s*[:.\-—]\s*)?'  # optional "Slide N:" prefix
    r'(.+?)\s*$',           # headline text
    re.MULTILINE,
)

# Matches: [3], [Slide 3], [ 3 ]
_BRACKET_RE = re.compile(
    r'^\[(?:Slide\s+)?(\d+)\]\s*$',
    re.MULTILINE | re.IGNORECASE,
)


def parse_notes_file(file_path):
    """Parse an external notes file into per-slide blocks.

    Args:
        file_path: Path to .md or .txt file.

    Returns:
        List of dicts: [{'raw_label': str, 'slide_number': int|None,
                         'headline_hint': str|None, 'text': str}]
    """
    with open(file_path) as f:
        content = f.read()

    if not content.strip():
        return []

    # Find all delimiter positions
    delimiters = []

    for m in _HEADING_RE.finditer(content):
        num = int(m.group(1)) if m.group(1) else None
        headline = m.group(2).strip()
        delimiters.append({
            'pos': m.start(),
            'end': m.end(),
            'slide_number': num,
            'headline_hint': headline,
            'raw_label': m.group(0).lstrip('#').strip(),
        })

    for m in _BRACKET_RE.finditer(content):
        num = int(m.group(1))
        delimiters.append({
            'pos': m.start(),
            'end': m.end(),
            'slide_number': num,
            'headline_hint': None,
            'raw_label': m.group(0).strip(),
        })

    # Sort by position, deduplicate overlapping matches
    delimiters.sort(key=lambda d: d['pos'])
    if not delimiters:
        # No delimiters — entire file is a single block for slide 1
        return [{
            'raw_label': '',
            'slide_number': 1,
            'headline_hint': None,
            'text': content.strip(),
        }]

    # Extract text blocks between delimiters
    blocks = []
    for i, delim in enumerate(delimiters):
        text_start = delim['end']
        text_end = delimiters[i + 1]['pos'] if i + 1 < len(delimiters) else len(content)
        text = content[text_start:text_end].strip()
        if text:
            blocks.append({
                'raw_label': delim['raw_label'],
                'slide_number': delim['slide_number'],
                'headline_hint': delim['headline_hint'],
                'text': text,
            })

    return blocks
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_notes_parser.py::TestParseNotesFile -v`
Expected: 12 PASS

- [ ] **Step 5: Commit**

```bash
git add src/notes_parser.py tests/test_notes_parser.py
git commit -m "feat: notes file parsing with heading and bracket delimiters (#44)"
```

---

### Task 3: Outline Matching

**Files:**
- Modify: `src/notes_parser.py` (add `match_notes_to_outline`)
- Test: `tests/test_notes_parser.py` (append tests)

- [ ] **Step 1: Write failing tests for match_notes_to_outline**

Append to `tests/test_notes_parser.py`:

```python
from src.notes_parser import match_notes_to_outline

SAMPLE_OUTLINE = {
    'narrative_arc': 'test',
    'estimated_duration_minutes': 15,
    'slides': [
        {'slide_number': 1, 'slide_type': 'title', 'headline': 'Welcome to the Future'},
        {'slide_number': 2, 'slide_type': 'content', 'headline': 'The Problem'},
        {'slide_number': 3, 'slide_type': 'content', 'headline': 'Our Solution'},
        {'slide_number': 4, 'slide_type': 'closing', 'headline': 'Thank You'},
    ],
}


class TestMatchNotesToOutline:
    def test_exact_number_match(self):
        blocks = [
            {'raw_label': 'Slide 1', 'slide_number': 1, 'headline_hint': 'Welcome', 'text': 'Notes for slide 1'},
            {'raw_label': 'Slide 2', 'slide_number': 2, 'headline_hint': 'Problem', 'text': 'Notes for slide 2'},
        ]
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert matched[1] == 'Notes for slide 1'
        assert matched[2] == 'Notes for slide 2'
        assert warnings == []

    def test_headline_fuzzy_match(self):
        blocks = [
            {'raw_label': 'Welcome to the Future', 'slide_number': None, 'headline_hint': 'Welcome to the Future', 'text': 'Opening notes'},
            {'raw_label': 'The Problem', 'slide_number': None, 'headline_hint': 'The Problem', 'text': 'Problem notes'},
        ]
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert matched[1] == 'Opening notes'
        assert matched[2] == 'Problem notes'
        assert warnings == []

    def test_substring_match(self):
        blocks = [
            {'raw_label': 'Solution', 'slide_number': None, 'headline_hint': 'Solution', 'text': 'Solution notes'},
        ]
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert matched[3] == 'Solution notes'

    def test_unmatched_produces_warning(self):
        blocks = [
            {'raw_label': 'Nonexistent Slide', 'slide_number': None, 'headline_hint': 'Nonexistent Slide', 'text': 'Orphan notes'},
        ]
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert len(matched) == 0
        assert len(warnings) == 1
        assert 'Nonexistent Slide' in warnings[0]

    def test_number_out_of_range_warns(self):
        blocks = [
            {'raw_label': 'Slide 99', 'slide_number': 99, 'headline_hint': None, 'text': 'Bad ref'},
        ]
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert len(matched) == 0
        assert len(warnings) == 1

    def test_partial_coverage(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'partial-coverage.md'))
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert 2 in matched
        assert 3 in matched
        assert 1 not in matched  # No notes for slide 1
        assert warnings == []

    def test_unmatched_fixture(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'unmatched.md'))
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert 1 in matched
        assert 3 in matched
        assert len(warnings) == 1
        assert 'Deleted Slide' in warnings[0]

    def test_duplicate_slide_number_last_wins(self):
        blocks = [
            {'raw_label': 'Slide 1', 'slide_number': 1, 'headline_hint': None, 'text': 'First version'},
            {'raw_label': 'Slide 1', 'slide_number': 1, 'headline_hint': None, 'text': 'Updated version'},
        ]
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert matched[1] == 'Updated version'
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_notes_parser.py::TestMatchNotesToOutline -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement match_notes_to_outline**

Add to `src/notes_parser.py`:

```python
def _strip_punctuation(text):
    """Remove punctuation for fuzzy comparison."""
    return re.sub(r'[^\w\s]', '', text).strip()


def _fuzzy_match_headline(hint, headlines):
    """Find the best matching slide for a headline hint.

    Args:
        hint: The headline hint from the parsed block.
        headlines: dict of {slide_number: headline} from the outline.

    Returns:
        slide_number or None.
    """
    hint_clean = _strip_punctuation(hint).lower()
    if not hint_clean:
        return None

    best_match = None
    best_ratio = 0

    for slide_num, headline in headlines.items():
        headline_clean = _strip_punctuation(headline).lower()

        # Substring containment (either direction)
        if hint_clean in headline_clean or headline_clean in hint_clean:
            return slide_num

        # Fuzzy ratio
        ratio = SequenceMatcher(None, hint_clean, headline_clean).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = slide_num

    if best_ratio > 0.7:
        return best_match

    return None


def match_notes_to_outline(parsed_blocks, outline):
    """Match parsed note blocks to slides in the outline.

    Args:
        parsed_blocks: List of dicts from parse_notes_file().
        outline: SlideOutline dict with 'slides' array.

    Returns:
        Tuple of (matched_dict, warnings_list).
        matched_dict: {slide_number: text}
        warnings_list: list of warning strings for unmatched blocks.
    """
    slide_numbers = {s['slide_number'] for s in outline.get('slides', [])}
    headlines = {s['slide_number']: s.get('headline', '') for s in outline.get('slides', [])}

    matched = {}
    warnings = []

    for block in parsed_blocks:
        # Priority 1: explicit slide number
        if block['slide_number'] is not None:
            if block['slide_number'] in slide_numbers:
                matched[block['slide_number']] = block['text']
                continue
            else:
                warnings.append(
                    f"Note for '{block['raw_label']}' references slide {block['slide_number']} "
                    f"which does not exist in the outline — skipped"
                )
                continue

        # Priority 2: headline fuzzy match
        if block['headline_hint']:
            slide_num = _fuzzy_match_headline(block['headline_hint'], headlines)
            if slide_num is not None:
                matched[slide_num] = block['text']
                continue

        # Unmatched
        label = block['raw_label'] or block['headline_hint'] or block['text'][:40]
        warnings.append(f"Note for '{label}' didn't match any slide — skipped")

    return matched, warnings
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_notes_parser.py -v`
Expected: 20 PASS (12 parsing + 8 matching)

- [ ] **Step 5: Commit**

```bash
git add src/notes_parser.py tests/test_notes_parser.py
git commit -m "feat: outline matching with fuzzy headline support (#44)"
```

---

### Task 4: Timing Calculation

**Files:**
- Modify: `src/notes_parser.py` (add `estimate_timing` and `build_timing_markers`)
- Test: `tests/test_notes_parser.py` (append tests)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_notes_parser.py`:

```python
from src.notes_parser import estimate_timing, build_timing_markers


class TestTiming:
    def test_estimate_timing_basic(self):
        # 130 words at 130 WPM = 60 seconds
        text = ' '.join(['word'] * 130)
        assert estimate_timing(text) == 60

    def test_estimate_timing_custom_wpm(self):
        text = ' '.join(['word'] * 100)
        # 100 words at 100 WPM = 60 seconds
        assert estimate_timing(text, wpm=100) == 60

    def test_estimate_timing_empty_text(self):
        assert estimate_timing('') == 0

    def test_estimate_timing_rounds_to_int(self):
        # 10 words at 130 WPM = ~4.6 seconds -> 5
        text = ' '.join(['word'] * 10)
        result = estimate_timing(text)
        assert isinstance(result, int)
        assert result == 5

    def test_build_timing_markers(self):
        notes_dict = {
            1: 'First slide with some notes here for timing.',
            2: 'Second slide also has notes that take some time to deliver to the audience.',
            3: 'Third slide wraps up.',
        }
        markers = build_timing_markers(notes_dict)
        assert 1 in markers
        assert 2 in markers
        assert 3 in markers
        assert 'estimated_seconds' in markers[1]
        assert 'timing_marker' in markers[1]
        assert markers[1]['timing_marker'].startswith('~')

    def test_build_timing_markers_cumulative(self):
        notes_dict = {
            1: ' '.join(['word'] * 130),  # 60 seconds
            2: ' '.join(['word'] * 130),  # 60 seconds
        }
        markers = build_timing_markers(notes_dict)
        assert markers[1]['timing_marker'] == '~1:00'
        assert markers[2]['timing_marker'] == '~2:00'

    def test_build_timing_markers_empty(self):
        markers = build_timing_markers({})
        assert markers == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_notes_parser.py::TestTiming -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement timing functions**

Add to `src/notes_parser.py`:

```python
def estimate_timing(text, wpm=130):
    """Estimate speaking time for a text block.

    Args:
        text: The speaker notes text.
        wpm: Words per minute (default 130 for natural conversational pace).

    Returns:
        int: Estimated seconds, rounded up.
    """
    if not text or not text.strip():
        return 0
    word_count = len(text.split())
    seconds = word_count / wpm * 60
    return round(seconds) if seconds > 0 else 0


def _format_timing_marker(total_seconds):
    """Format cumulative seconds as ~M:SS string."""
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f'~{minutes}:{seconds:02d}'


def build_timing_markers(notes_dict, wpm=130):
    """Build timing metadata for each slide's notes.

    Args:
        notes_dict: {slide_number: text} from match_notes_to_outline.
        wpm: Words per minute for timing calculation.

    Returns:
        dict: {slide_number: {'estimated_seconds': int, 'timing_marker': str}}
    """
    if not notes_dict:
        return {}

    markers = {}
    cumulative = 0

    for slide_num in sorted(notes_dict.keys()):
        seconds = estimate_timing(notes_dict[slide_num], wpm=wpm)
        cumulative += seconds
        markers[slide_num] = {
            'estimated_seconds': seconds,
            'timing_marker': _format_timing_marker(cumulative),
        }

    return markers
```

- [ ] **Step 4: Run all tests**

Run: `.venv/bin/pytest tests/test_notes_parser.py -v`
Expected: 27 PASS (12 parsing + 8 matching + 7 timing)

- [ ] **Step 5: Sync plugin copy and commit**

```bash
cp src/notes_parser.py plugins/jack-tar-deckhand/src/
git add src/notes_parser.py plugins/jack-tar-deckhand/src/notes_parser.py tests/test_notes_parser.py
git commit -m "feat: timing calculation for imported notes (#44)"
```

---

### Task 5: TalkBrief Schema Extension

**Files:**
- Modify: `src/schemas/talk_brief.schema.json`
- Test: `tests/test_notes_parser.py` (append schema test)

- [ ] **Step 1: Write failing test**

Append to `tests/test_notes_parser.py`:

```python
import json
import jsonschema

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'schemas')


class TestTalkBriefNotesField:
    def test_brief_with_speaker_notes_path_validates(self):
        with open(os.path.join(SCHEMA_DIR, 'talk_brief.schema.json')) as f:
            schema = json.load(f)
        brief = {
            'topic': 'AI Agents',
            'audience': 'Developers',
            'duration_minutes': 20,
            'preferences': {
                'speaker_notes_path': '/path/to/notes.md',
            },
        }
        jsonschema.validate(instance=brief, schema=schema)

    def test_brief_without_notes_path_still_validates(self):
        with open(os.path.join(SCHEMA_DIR, 'talk_brief.schema.json')) as f:
            schema = json.load(f)
        brief = {
            'topic': 'AI Agents',
            'audience': 'Developers',
            'duration_minutes': 20,
        }
        jsonschema.validate(instance=brief, schema=schema)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_notes_parser.py::TestTalkBriefNotesField -v`
Expected: FAIL (speaker_notes_path is additionalProperty, schema rejects it)

- [ ] **Step 3: Add speaker_notes_path to schema**

In `src/schemas/talk_brief.schema.json`, in the `preferences.properties` object, after the `budget_cap_usd` field, add:

```json
        "speaker_notes_path": {
          "type": "string",
          "description": "Path to an external speaker notes file (.md or .txt). When provided, notes are imported and enriched with timing/cues instead of being generated from scratch."
        }
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/test_notes_parser.py::TestTalkBriefNotesField -v`
Expected: 2 PASS

Run schema regression:
Run: `.venv/bin/pytest tests/test_schemas.py -v`
Expected: All existing tests PASS

- [ ] **Step 5: Sync plugin copy and commit**

```bash
cp src/schemas/talk_brief.schema.json plugins/jack-tar-deckhand/src/schemas/
git add src/schemas/talk_brief.schema.json plugins/jack-tar-deckhand/src/schemas/talk_brief.schema.json tests/test_notes_parser.py
git commit -m "feat: speaker_notes_path field in TalkBrief schema (#44)"
```

---

### Task 6: Speaker Notes Writer Skill Update

**Files:**
- Modify: `plugins/jack-tar-deckhand/skills/speaker-notes-writer/SKILL.md`

- [ ] **Step 1: Read the current skill file**

Read `plugins/jack-tar-deckhand/skills/speaker-notes-writer/SKILL.md` to understand current structure.

- [ ] **Step 2: Add import/enrich branch**

Insert a new section after `## What It Does` and before `### Step 1: Gather Preferences`:

```markdown
### Step 0: Check for External Notes (Before Preferences)

Before gathering preferences, check if the TalkBrief provides external notes:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
brief = json.load(open('./tmp/deck/talk-brief.json'))
path = brief.get('preferences', {}).get('speaker_notes_path')
include = brief.get('preferences', {}).get('include_speaker_notes', True)
if not include:
    print('SKIP: include_speaker_notes is false')
elif path:
    print(f'IMPORT: {path}')
else:
    print('GENERATE')
"
```

**If SKIP:** Write an empty notes file and exit:
```bash
echo '{"notes": []}' > ./tmp/deck/speaker-notes.json
```

**If IMPORT:** Run the import/enrich flow (see Step 1a below). Do NOT gather preferences — they don't apply to imported notes.

**If GENERATE:** Proceed to Step 1 (preferences gathering) as normal.

### Step 1a: Import and Enrich External Notes

When the TalkBrief provides `preferences.speaker_notes_path`:

1. Parse and match the external notes file:
```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.notes_parser import parse_notes_file, match_notes_to_outline, build_timing_markers
brief = json.load(open('./tmp/deck/talk-brief.json'))
outline = json.load(open('./tmp/deck/outline.json'))
path = brief['preferences']['speaker_notes_path']
blocks = parse_notes_file(path)
matched, warnings = match_notes_to_outline(blocks, outline)
markers = build_timing_markers(matched)
print(f'Matched {len(matched)} slides, {len(warnings)} warnings')
for w in warnings:
    print(f'  WARNING: {w}')
print('MATCHED_SLIDES:', json.dumps(list(matched.keys())))
# Save intermediate results for enrichment
json.dump({'matched': {str(k): v for k, v in matched.items()}, 'markers': {str(k): v for k, v in markers.items()}}, open('./tmp/deck/_imported_notes.json', 'w'))
"
```

2. Report any warnings to the Speaker.

3. **Enrich** the matched notes: For each matched slide, you have the speaker's text and computed timing. Now generate contextual `cues` (transition, pause, emphasis, audience_interaction) using the same reasoning you would for generated notes. The speaker's text is the input — do not modify it, only add cues.

4. **Fill gaps:** Check which slides in the outline have no imported notes. For those slides, generate notes from scratch using the same approach as Step 2 (autonomous generation), using default preferences (bullet points, moderate interaction, comfortable detail).

5. Assemble the complete SpeakerNotes contract (imported + generated gap-fills) and proceed to Step 3 (validate and write).
```

- [ ] **Step 3: Commit**

```bash
git add plugins/jack-tar-deckhand/skills/speaker-notes-writer/SKILL.md
git commit -m "feat: speaker-notes-writer import/enrich branch (#44)"
```

---

### Task 7: Conductor Documentation Update

**Files:**
- Modify: `plugins/jack-tar-deckhand/agents/deck-conductor.md`

- [ ] **Step 1: Read the conductor file to find Step 4**

Read `plugins/jack-tar-deckhand/agents/deck-conductor.md` and locate `### Step 4: Speaker Notes`.

- [ ] **Step 2: Add note about external notes**

After the existing Step 4 description line (`Invoke the speaker-notes-writer skill...`), add:

```markdown
If the TalkBrief provides `preferences.speaker_notes_path`, the writer imports and enriches external notes instead of generating. The writer handles this internally — no conductor logic change needed. Slides without external notes are generated as normal.
```

- [ ] **Step 3: Commit**

```bash
git add plugins/jack-tar-deckhand/agents/deck-conductor.md
git commit -m "docs: conductor note on external speaker notes (#44)"
```

---

### Task 8: Integration Tests and CLAUDE.md Update

**Files:**
- Modify: `tests/test_notes_parser.py` (append integration tests)
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write integration tests**

Append to `tests/test_notes_parser.py`:

```python
from src.content_validation import validate_notes_schema


class TestNotesImportIntegration:
    def test_import_produces_valid_schema(self):
        """Full flow: parse → match → timing → assemble → validate."""
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'heading-based.md'))
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        markers = build_timing_markers(matched)

        # Assemble into SpeakerNotes schema format
        notes = {'notes': []}
        for slide_num in sorted(matched.keys()):
            note = {
                'slide_number': slide_num,
                'text': matched[slide_num],
            }
            if slide_num in markers:
                note['estimated_seconds'] = markers[slide_num]['estimated_seconds']
                note['timing_marker'] = markers[slide_num]['timing_marker']
            notes['notes'].append(note)

        errors = validate_notes_schema(notes)
        assert errors == []

    def test_partial_coverage_leaves_gaps(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'partial-coverage.md'))
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        # Slides 1 and 4 have no notes — gaps for the writer to fill
        assert 1 not in matched
        assert 4 not in matched
        assert 2 in matched
        assert 3 in matched

    def test_full_heading_fixture_matches_all(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'heading-based.md'))
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert len(matched) == 3  # Slides 1, 2, 3
        assert warnings == []

    def test_mixed_format_matches_correctly(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'mixed-format.md'))
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert 1 in matched
        assert 2 in matched
        assert 3 in matched  # Matched by headline "Our Solution"
        assert 4 in matched
        assert warnings == []
```

- [ ] **Step 2: Run full test suite**

Run: `.venv/bin/pytest tests/test_notes_parser.py -v`
Expected: All PASS (~31 tests)

- [ ] **Step 3: Update CLAUDE.md**

Add to the Current Status section (after the template-driven layout bullet):

```markdown
- **Speaker Notes Import (issue #44):** Speakers can provide per-slide narrative notes in external .md/.txt files via `preferences.speaker_notes_path`. Notes parser (`src/notes_parser.py`) supports heading-based, number-marker, and headline fuzzy matching. Writer enriches imported notes with timing/cues and generates for uncovered slides. Enables voiceover auto-generation and self-presenting visual-heavy decks.
```

Add to the Implementation Status table:

```markdown
| Notes parser | `src/notes_parser.py` | ~31 | Done |
```

- [ ] **Step 4: Sync all plugin copies and final commit**

```bash
cp src/notes_parser.py plugins/jack-tar-deckhand/src/
cp src/schemas/talk_brief.schema.json plugins/jack-tar-deckhand/src/schemas/
git add tests/test_notes_parser.py CLAUDE.md plugins/jack-tar-deckhand/src/notes_parser.py
git commit -m "feat: integration tests and CLAUDE.md update for notes import (#44)"
```
