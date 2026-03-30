# Phase 3: Content Services — narrative-architect + speaker-notes-writer

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two Claude Code skills that transform a TalkBrief into structured presentation content — a narrative-architect (collaborative arc selection then autonomous outline generation) and a speaker-notes-writer (lightweight preference gathering then autonomous note generation), plus a thin Python validation module for timing arithmetic and reference integrity.

**Architecture:** Two SKILL.md files define how Claude collaborates with the Speaker on narrative arc selection and note preferences, then produces SlideOutline and SpeakerNotes autonomously. A thin Python module `src/content_validation.py` handles only machine-checkable validation: timing arithmetic (do note durations sum to talk duration?) and reference integrity (do layout templates exist in StyleGuide? do note slide numbers exist in outline?). All narrative reasoning — arc selection, slide sequencing, headline quality, visual direction prose — is Claude's contextual reasoning, not codified rules.

**Tech Stack:** Claude Code skills (SKILL.md), Python 3.8+ (content_validation.py, jsonschema, pytest), src/deckcontext.py (Phase 1)

**Dependencies:**
- Phase 1 (complete): `src/deckcontext.py`, `src/schemas/slide_outline.schema.json`, `src/schemas/speaker_notes.schema.json`
- Phase 2 (complete): StyleGuide contract (consumed by narrative-architect for layout template references)

**Supersedes:** `docs/superpowers/plans/2026-03-29-phase-3-content-services.md` (written for old non-collaborative architecture with Python arc selection logic)

---

## File Structure

```
research/
  synthesis-narrative-architect.md        # Research synthesis
  synthesis-speaker-notes-writer.md       # Research synthesis
src/
  content_validation.py                   # Timing arithmetic + reference integrity only
.claude/
  skills/
    narrative-architect/
      SKILL.md                            # Two-stage collaborative skill
    speaker-notes-writer/
      SKILL.md                            # Preference-gathering then autonomous skill
tests/
  test_content_validation.py              # Validation utility tests
  fixtures/
    talk_brief_technical_30min.json        # Extended fixture: technical talk
    talk_brief_lightning_5min.json         # Extended fixture: lightning talk
```

---

## Task 1: Research Synthesis Documents

**Files:**
- Create: `research/synthesis-narrative-architect.md`
- Create: `research/synthesis-speaker-notes-writer.md`

- [ ] **Step 1: Read primary research**

Read and synthesise:
- `research/08-narrative-arc-patterns.md` (16 arc structures, slide density research, invisible slides)
- `research/06-speaker-notes-design.md` (timing calibration, cue types, pacing)
- `docs/architecture/content-services.md` (L1 service document with collaborative workflow)

- [ ] **Step 2: Write narrative-architect synthesis**

Create `research/synthesis-narrative-architect.md` covering:
1. **Two-stage collaborative model:** Stage 1 (arc proposal with Speaker approval) and Stage 2 (autonomous outline execution)
2. **Arc catalogue summary:** The 16 structures from Research #08 with when each works best — grouped by talk duration and tone
3. **Arc-to-slide-count derivation:** Pacing styles (content-heavy 0.5-1.0/min, standard 1.0-1.5/min, visual-heavy 1.5-2.5/min, rapid-fire 3.0-4.0/min) plus structural overhead (title, closing, section dividers, attention resets)
4. **Slide type assignment patterns:** How narrative beats map to the 12 slide types
5. **Visual direction prose guidance:** How to write specific enough for prompt engineering without prescribing implementation
6. **What the architect decides autonomously:** Section dividers, sequencing, opening/closing sequences, body point allocation, layout template selection

- [ ] **Step 3: Write speaker-notes-writer synthesis**

Create `research/synthesis-speaker-notes-writer.md` covering:
1. **Lightweight preference gathering:** The 3 questions (format, interaction style, experience level) and defaults
2. **Timing calibration:** WPM-based calculation, cumulative timing markers, duration matching
3. **Cue type usage:** When to use each of the 6 cue types (transition, pause, audience_interaction, emphasis, demo, build_animation)
4. **Autonomous execution scope:** What the writer decides without seeking approval

- [ ] **Step 4: Commit**

```bash
git add research/synthesis-narrative-architect.md research/synthesis-speaker-notes-writer.md
git commit -m "docs: add research synthesis for narrative-architect and speaker-notes-writer"
```

---

## Task 2: Test Fixtures

**Files:**
- Create: `tests/fixtures/talk_brief_technical_30min.json`
- Create: `tests/fixtures/talk_brief_lightning_5min.json`

- [ ] **Step 1: Create technical 30-minute talk fixture**

Create `tests/fixtures/talk_brief_technical_30min.json`:

```json
{
  "topic": "Building Fault-Tolerant Distributed Systems with Raft Consensus",
  "audience": "Backend engineers familiar with distributed systems but new to consensus algorithms",
  "duration_minutes": 30,
  "tone": "technical",
  "key_takeaways": [
    "Raft is simpler than Paxos without sacrificing correctness",
    "Leader election is the hardest part to get right",
    "Log replication handles network partitions gracefully"
  ],
  "branding": {
    "company_name": "Nexus Technologies",
    "brand_id": "nexus-tech",
    "compliance_mode": "guided"
  },
  "preferences": {
    "style": "diagram-heavy",
    "slide_count_hint": 25,
    "image_backend": "ollama",
    "resolution": "1080p",
    "include_speaker_notes": true,
    "include_charts": false
  },
  "data_sources": []
}
```

- [ ] **Step 2: Create lightning 5-minute talk fixture**

Create `tests/fixtures/talk_brief_lightning_5min.json`:

```json
{
  "topic": "One Weird Trick That Cut Our Deploy Time by 80%",
  "audience": "DevOps engineers and SREs at a meetup",
  "duration_minutes": 5,
  "tone": "conversational",
  "key_takeaways": [
    "Parallel test execution was the bottleneck, not build time"
  ],
  "preferences": {
    "style": "minimalist",
    "slide_count_hint": 8,
    "image_backend": "ollama",
    "resolution": "1080p",
    "include_speaker_notes": true,
    "include_charts": true
  },
  "data_sources": [
    {
      "label": "Deploy time before/after",
      "type": "inline_json",
      "content": "{\"before_minutes\": 45, \"after_minutes\": 9}"
    }
  ]
}
```

- [ ] **Step 3: Validate fixtures against schema**

Run:
```bash
source .venv/bin/activate && python3 -c "
import json
from jsonschema import validate
schema = json.load(open('src/schemas/talk_brief.schema.json'))
for f in ['talk_brief_technical_30min', 'talk_brief_lightning_5min']:
    brief = json.load(open(f'tests/fixtures/{f}.json'))
    validate(instance=brief, schema=schema)
    print(f'{f}.json validates')
"
```

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/talk_brief_technical_30min.json tests/fixtures/talk_brief_lightning_5min.json
git commit -m "test: add extended TalkBrief fixtures for content services"
```

---

## Task 3: Content Validation Utilities

**Files:**
- Create: `src/content_validation.py`
- Create: `tests/test_content_validation.py`

- [ ] **Step 1: Write tests**

Create `tests/test_content_validation.py`:

```python
"""Tests for content validation utilities — timing arithmetic and reference integrity."""

import json
import os
import pytest

from src.content_validation import (
    validate_outline_schema,
    validate_notes_schema,
    check_timing_total,
    check_notes_slide_references,
    check_outline_layout_references,
)

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def _load_fixture(name):
    with open(os.path.join(FIXTURE_DIR, name)) as f:
        return json.load(f)


class TestValidateOutlineSchema:
    def test_valid_outline_passes(self):
        outline = _load_fixture('valid_slide_outline.json')
        errors = validate_outline_schema(outline)
        assert len(errors) == 0

    def test_missing_slides_fails(self):
        outline = {"narrative_arc": "test", "estimated_duration_minutes": 10}
        errors = validate_outline_schema(outline)
        assert len(errors) > 0


class TestValidateNotesSchema:
    def test_valid_notes_passes(self):
        notes = _load_fixture('valid_speaker_notes.json')
        errors = validate_notes_schema(notes)
        assert len(errors) == 0

    def test_missing_notes_array_fails(self):
        notes = {"target_pace_wpm": 130}
        errors = validate_notes_schema(notes)
        assert len(errors) > 0


class TestTimingTotal:
    def test_timing_within_tolerance(self):
        notes = {
            "total_estimated_minutes": 10,
            "notes": [
                {"slide_number": 1, "text": "Hello", "estimated_seconds": 300},
                {"slide_number": 2, "text": "World", "estimated_seconds": 300},
            ]
        }
        issues = check_timing_total(notes, duration_minutes=10)
        assert len(issues) == 0

    def test_timing_too_long(self):
        notes = {
            "total_estimated_minutes": 30,
            "notes": [
                {"slide_number": 1, "text": "Hello", "estimated_seconds": 600},
                {"slide_number": 2, "text": "World", "estimated_seconds": 600},
                {"slide_number": 3, "text": "Extra", "estimated_seconds": 600},
            ]
        }
        issues = check_timing_total(notes, duration_minutes=10)
        assert len(issues) > 0
        assert any('exceeds' in i.lower() or 'over' in i.lower() for i in issues)

    def test_timing_without_seconds_skips(self):
        notes = {
            "notes": [
                {"slide_number": 1, "text": "Hello"},
            ]
        }
        issues = check_timing_total(notes, duration_minutes=10)
        assert len(issues) == 0


class TestNotesSlideReferences:
    def test_valid_references(self):
        outline = {
            "slides": [
                {"slide_number": 1, "slide_type": "title", "headline": "Hi"},
                {"slide_number": 2, "slide_type": "content", "headline": "Body"},
            ]
        }
        notes = {
            "notes": [
                {"slide_number": 1, "text": "Hello"},
                {"slide_number": 2, "text": "World"},
            ]
        }
        issues = check_notes_slide_references(notes, outline)
        assert len(issues) == 0

    def test_orphan_note_detected(self):
        outline = {
            "slides": [
                {"slide_number": 1, "slide_type": "title", "headline": "Hi"},
            ]
        }
        notes = {
            "notes": [
                {"slide_number": 1, "text": "Hello"},
                {"slide_number": 99, "text": "Orphan"},
            ]
        }
        issues = check_notes_slide_references(notes, outline)
        assert len(issues) > 0
        assert any('99' in i for i in issues)


class TestOutlineLayoutReferences:
    def test_valid_layout_references(self):
        outline = {
            "slides": [
                {"slide_number": 1, "slide_type": "title", "headline": "Hi", "layout_template": "title"},
                {"slide_number": 2, "slide_type": "content", "headline": "Body", "layout_template": "content"},
            ]
        }
        style_guide = {
            "layout": {
                "templates": {"title": {}, "content": {}}
            }
        }
        issues = check_outline_layout_references(outline, style_guide)
        assert len(issues) == 0

    def test_missing_template_detected(self):
        outline = {
            "slides": [
                {"slide_number": 1, "slide_type": "title", "headline": "Hi", "layout_template": "nonexistent"},
            ]
        }
        style_guide = {
            "layout": {
                "templates": {"title": {}, "content": {}}
            }
        }
        issues = check_outline_layout_references(outline, style_guide)
        assert len(issues) > 0

    def test_no_layout_template_skips(self):
        outline = {
            "slides": [
                {"slide_number": 1, "slide_type": "title", "headline": "Hi"},
            ]
        }
        style_guide = {"layout": {"templates": {}}}
        issues = check_outline_layout_references(outline, style_guide)
        assert len(issues) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_content_validation.py -v`

Expected: FAIL — `src.content_validation` not found.

- [ ] **Step 3: Implement content validation utilities**

Create `src/content_validation.py`:

```python
"""Content validation utilities — timing arithmetic and reference integrity.

This module handles ONLY machine-checkable validation:
- Schema conformance (SlideOutline, SpeakerNotes)
- Timing arithmetic (do note durations sum to talk duration?)
- Reference integrity (layout templates, slide numbers)

All narrative reasoning — arc selection, slide sequencing, headline quality,
visual direction prose — is Claude's contextual reasoning in the SKILL.md,
NOT codified rules here.
"""

import json
import os

import jsonschema

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), 'schemas')

TIMING_TOLERANCE_PCT = 20  # Allow 20% deviation from target duration


def validate_outline_schema(outline):
    """Validate a SlideOutline dict against the JSON schema. Returns list of error messages."""
    schema_path = os.path.join(SCHEMA_DIR, 'slide_outline.schema.json')
    with open(schema_path) as f:
        schema = json.load(f)
    validator = jsonschema.Draft202012Validator(schema)
    return [e.message for e in validator.iter_errors(outline)]


def validate_notes_schema(notes):
    """Validate a SpeakerNotes dict against the JSON schema. Returns list of error messages."""
    schema_path = os.path.join(SCHEMA_DIR, 'speaker_notes.schema.json')
    with open(schema_path) as f:
        schema = json.load(f)
    validator = jsonschema.Draft202012Validator(schema)
    return [e.message for e in validator.iter_errors(notes)]


def check_timing_total(notes, duration_minutes):
    """Check that note durations sum to approximately the talk duration.

    Returns list of issue strings. Tolerates TIMING_TOLERANCE_PCT deviation.
    """
    issues = []
    total_seconds = 0
    has_timing = False
    for note in notes.get('notes', []):
        est = note.get('estimated_seconds')
        if est is not None:
            total_seconds += est
            has_timing = True

    if not has_timing:
        return []

    target_seconds = duration_minutes * 60
    deviation_pct = abs(total_seconds - target_seconds) / target_seconds * 100

    if total_seconds > target_seconds * (1 + TIMING_TOLERANCE_PCT / 100):
        issues.append(
            f'Notes total {total_seconds}s ({total_seconds/60:.1f}min) exceeds '
            f'talk duration {duration_minutes}min by {deviation_pct:.0f}%'
        )
    elif total_seconds < target_seconds * (1 - TIMING_TOLERANCE_PCT / 100):
        issues.append(
            f'Notes total {total_seconds}s ({total_seconds/60:.1f}min) under '
            f'talk duration {duration_minutes}min by {deviation_pct:.0f}%'
        )

    return issues


def check_notes_slide_references(notes, outline):
    """Check that every note references a slide that exists in the outline."""
    issues = []
    outline_slides = {s['slide_number'] for s in outline.get('slides', [])}
    for note in notes.get('notes', []):
        sn = note.get('slide_number')
        if sn is not None and sn not in outline_slides:
            issues.append(f'Note references slide {sn} which does not exist in outline')
    return issues


def check_outline_layout_references(outline, style_guide):
    """Check that every layout_template in the outline exists in the StyleGuide."""
    issues = []
    templates = style_guide.get('layout', {}).get('templates', {})
    for slide in outline.get('slides', []):
        lt = slide.get('layout_template')
        if lt and lt not in templates:
            issues.append(
                f'Slide {slide["slide_number"]} references layout template '
                f'"{lt}" which does not exist in StyleGuide'
            )
    return issues
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_content_validation.py -v`

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/content_validation.py tests/test_content_validation.py
git commit -m "feat: add content validation utilities (timing arithmetic, reference integrity)"
```

---

## Task 4: narrative-architect Skill Definition

**Files:**
- Create: `.claude/skills/narrative-architect/SKILL.md`

- [ ] **Step 1: Read research synthesis and architecture doc**

Read:
- `research/synthesis-narrative-architect.md`
- `research/08-narrative-arc-patterns.md` (sections 1.1-1.16 for arc catalogue)
- `docs/architecture/content-services.md`
- `src/schemas/slide_outline.schema.json`

- [ ] **Step 2: Write the narrative-architect skill**

Create `.claude/skills/narrative-architect/SKILL.md`:

```markdown
---
name: narrative-architect
description: Transform a TalkBrief into a structured SlideOutline through collaborative arc selection and autonomous outline generation.
argument-hint: [--deck-dir PATH]
allowed-tools: Bash(python *), Read, Glob, Write
---

# /narrative-architect

Transform a TalkBrief into a structured SlideOutline. Works in two stages: collaborative arc selection with the Speaker, then autonomous outline generation.

## Prerequisites

- `./tmp/deck/talk-brief.json` must exist
- `./tmp/deck/style-guide.json` must exist (produced by slide-stylist)

## Usage

Invoked by the Deck Conductor after slide-stylist. Can also be invoked directly:

```
/narrative-architect
/narrative-architect --deck-dir ./tmp/deck
```

## What It Does

### Stage 1: Arc Proposal (Collaborative)

Read `./tmp/deck/talk-brief.json` for topic, audience, duration, tone, key takeaways, and data sources.

Based on these signals, select 2-3 narrative arc options that genuinely fit this specific talk. Do NOT present all 16 arcs from the catalogue -- curate down to the best matches.

For each proposed arc, present:

> "For a **{duration}-minute {tone}** talk on **{topic}**, here are the narrative structures I'd recommend:
>
> 1. **{Arc Name}** -- {one-line emotional description}
>    - Best for: {when this works}
>    - Your talk would flow: {beat1} -> {beat2} -> {beat3} -> ... -> {final beat}
>    - Slide count: ~{count} slides at {pacing} pacing
>
> 2. **{Arc Name}** -- {one-line emotional description}
>    - Best for: {when this works}
>    - Your talk would flow: {beat1} -> {beat2} -> ...
>    - Slide count: ~{count} slides
>
> 3. **{Arc Name}** -- {one-line emotional description}
>    - Best for: {when this works}
>    - Your talk would flow: {beat1} -> {beat2} -> ...
>    - Slide count: ~{count} slides
>
> **My recommendation:** {Arc Name} because {one-sentence rationale connecting to this specific talk}.
>
> Which structure speaks to you? (Or describe what you're looking for)"

Wait for the Speaker to select or describe their preference. If they describe something custom, map it to the closest arc or propose a hybrid.

### Arc Catalogue Reference

These are the established structures to draw from (Research #08):

| Arc | Best For | Pacing |
|-----|----------|--------|
| Situation-Complication-Resolution | Executive briefings, problem-solving | Standard |
| Monroe's Motivated Sequence | Persuasion, calls to action | Standard |
| Hero's Journey | Transformation stories, keynotes | Visual-heavy |
| Problem-Solution-Impact | Product talks, case studies | Standard |
| Problem-Demo-Impact | Technical demos, tool showcases | Content-heavy |
| What-So What-Now What | Data presentations, research findings | Content-heavy |
| Hook-Thesis-Body-Callback-CTA | Persuasion talks, thought leadership | Standard |
| Story-Point-Application | Rule of Three, teaching talks | Standard |
| Pecha Kucha | 6:40 fixed format, 20 slides x 20 seconds | Rapid-fire |
| Ignite | 5 min fixed, 20 slides x 15 seconds | Rapid-fire |
| Lightning Talk | 5-10 min, minimal slides | Standard |
| Lessig Method | Rapid visual reinforcement, advocacy | Rapid-fire |
| Takahashi Method | Japanese big-text style, storytelling | Rapid-fire |
| 10/20/30 Rule | Startup pitches, 10 slides | Content-heavy |
| Duarte Sparkline | Long keynotes, What Is vs What Could Be | Visual-heavy |
| Modular Deck | Flexible/reusable, workshop-style | Standard |

### Stage 2: Outline Execution (Autonomous)

Once the Speaker selects an arc, produce the full SlideOutline. This is expert craft -- do NOT seek per-slide approval.

**What you decide autonomously:**
- Exact slide count (calibrated to duration and pacing style)
- Slide type assignment per slide (from the 12 types)
- Headlines -- punchy conference headlines, not academic paper titles
- Body points (max 5 per slide)
- Narrative beat labels
- Visual direction prose per slide (specific enough for prompt engineering, incorporating StyleGuide image_style_tokens)
- Layout template references from StyleGuide
- Transition notes between slides
- Section divider placement (before every major beat transition)
- Attention reset beats (every ~10 minutes of duration)
- Data source mapping from TalkBrief to data_chart slides

**Pacing guidelines:**
- Content-heavy (data, technical deep-dive): 0.5-1.0 slides/min
- Standard (most conference talks): 1.0-1.5 slides/min
- Visual-heavy (keynotes, storytelling): 1.5-2.5 slides/min
- Rapid-fire (Pecha Kucha, Ignite, Lessig): 3.0-4.0 slides/min

**Structural overhead added to base count:**
- +1 title slide (always)
- +1 closing slide (always)
- +1 section divider per major beat transition
- +1 attention reset per 10 minutes of duration

If `preferences.slide_count_hint` is provided, use it as a soft target (within 20%) but override if the arc demands it.

**Read the StyleGuide** at `./tmp/deck/style-guide.json` for:
- Layout template names (ensure every slide's `layout_template` exists in `layout.templates`)
- Image style tokens (weave `mood`, `color_direction`, and `style_modifiers` into `visual_direction` prose)

### Step 3: Validate and Write

Validate the outline before writing:

```bash
source .venv/bin/activate && python3 -c "
import json
from src.content_validation import validate_outline_schema, check_outline_layout_references
outline = json.load(open('./tmp/deck/outline.json'))
style_guide = json.load(open('./tmp/deck/style-guide.json'))
schema_errors = validate_outline_schema(outline)
ref_issues = check_outline_layout_references(outline, style_guide)
for e in schema_errors: print(f'SCHEMA: {e}')
for e in ref_issues: print(f'REF: {e}')
if not schema_errors and not ref_issues:
    print('SlideOutline validates successfully')
"
```

Write the validated SlideOutline to `./tmp/deck/outline.json`.

## Output

`./tmp/deck/outline.json` (SlideOutline contract)

## Design Rules

- Headlines should be punchy conference headlines, not generic titles ("The 3-Second Rule for Slide Readability" not "Text Best Practices")
- Max 5 body points per slide
- Visual direction must be specific enough to generate images but not prescriptive about implementation
- Never place two data_chart slides consecutively without a breathing slide between them
- Section dividers before every major narrative beat transition
- Title slide always first, closing slide always last
- Do NOT ask the Speaker about individual slide choices -- the arc approval is the collaboration point
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/narrative-architect/
git commit -m "feat: add narrative-architect skill with two-stage collaborative workflow"
```

---

## Task 5: speaker-notes-writer Skill Definition

**Files:**
- Create: `.claude/skills/speaker-notes-writer/SKILL.md`

- [ ] **Step 1: Read research synthesis and architecture doc**

Read:
- `research/synthesis-speaker-notes-writer.md`
- `research/06-speaker-notes-design.md`
- `docs/architecture/content-services.md`
- `src/schemas/speaker_notes.schema.json`

- [ ] **Step 2: Write the speaker-notes-writer skill**

Create `.claude/skills/speaker-notes-writer/SKILL.md`:

```markdown
---
name: speaker-notes-writer
description: Generate timed, transition-cued speaker notes calibrated to talk duration and audience profile, with lightweight preference gathering.
argument-hint: [--deck-dir PATH]
allowed-tools: Bash(python *), Read, Glob, Write
---

# /speaker-notes-writer

Generate per-slide speaker notes with timing markers, cumulative time marks, and interaction cues.

## Prerequisites

- `./tmp/deck/talk-brief.json` must exist
- `./tmp/deck/outline.json` must exist (produced by narrative-architect)

## Usage

Invoked by the Deck Conductor after narrative-architect. Can also be invoked directly:

```
/speaker-notes-writer
/speaker-notes-writer --deck-dir ./tmp/deck
```

## What It Does

### Step 1: Gather Preferences (Lightweight Collaboration)

Before generating notes, ask the Speaker three quick questions (if the answers aren't obvious from the TalkBrief):

> "Before I write your speaker notes, three quick questions:
>
> 1. **Note format:** Do you prefer bullet points/keywords or fuller sentences?
> 2. **Audience interaction:** Any preference? (show of hands, rhetorical questions, polls, none)
> 3. **Your experience level:** First-time presenter, comfortable, or seasoned?
>
> (Or just say 'defaults' and I'll use: bullet points, match-to-tone interaction, moderate detail)"

**Defaults if Speaker says 'defaults' or skips:**
- Format: Bullet points with key phrases
- Interaction: Match to tone (conversational = show of hands, professional = rhetorical, technical = none)
- Detail: Moderate (comfortable presenter)

### Step 2: Generate Notes (Autonomous)

Read `./tmp/deck/talk-brief.json` and `./tmp/deck/outline.json`.

For each slide in the outline, produce a note with:

**text** — The speaking content for this slide:
- Bullet format: key phrases and memory joggers
- Sentence format: near-script with natural spoken language
- Detail scaled to experience level (first-time = more explicit cues, seasoned = less)

**estimated_seconds** — Time allocation for this slide:
- Calculate from `target_pace_wpm` (default 130) and word count
- Heavier slides (data, key arguments) get more time
- Structural slides (title, dividers, closing) get less
- Total must sum to approximately `duration_minutes` from TalkBrief

**timing_marker** — Cumulative time mark (e.g., "~5:30", "~12:00"):
- Helps the speaker track progress during delivery
- Calculate from cumulative estimated_seconds

**cues** — Interaction cues appropriate to the slide:
- `transition`: How to bridge from the previous slide ("Building on that insight...")
- `pause`: Deliberate silence for impact ("[pause 2 seconds for the number to land]")
- `audience_interaction`: Engage the audience, matching the Speaker's preference
- `emphasis`: Key point to stress ("This is the number your CFO cares about")
- `demo`: Live demonstration beat ("Switch to terminal, run the command")
- `build_animation`: Timed reveal ("Click to reveal the second column")

**What you decide autonomously:**
- Word count per slide (calibrated to pace and duration)
- Timing allocation per slide
- Cumulative timing markers
- Transition cue placement and content
- Pause placement (after key data, before major shifts)
- Audience interaction beat placement (every ~10 minutes)
- Emphasis markers on key phrases
- Demo cues (when outline includes demo beats)
- Build animation triggers (when outline has progressive disclosure)

### Step 3: Validate and Write

Validate the notes before writing:

```bash
source .venv/bin/activate && python3 -c "
import json
from src.content_validation import validate_notes_schema, check_timing_total, check_notes_slide_references
notes = json.load(open('./tmp/deck/speaker-notes.json'))
outline = json.load(open('./tmp/deck/outline.json'))
brief = json.load(open('./tmp/deck/talk-brief.json'))
schema_errors = validate_notes_schema(notes)
timing_issues = check_timing_total(notes, brief['duration_minutes'])
ref_issues = check_notes_slide_references(notes, outline)
for e in schema_errors: print(f'SCHEMA: {e}')
for e in timing_issues: print(f'TIMING: {e}')
for e in ref_issues: print(f'REF: {e}')
if not schema_errors and not timing_issues and not ref_issues:
    print('SpeakerNotes validates successfully')
"
```

Write the validated SpeakerNotes to `./tmp/deck/speaker-notes.json`.

## Output

`./tmp/deck/speaker-notes.json` (SpeakerNotes contract)

## Design Rules

- Notes must be specific and actionable -- "Explain that Raft uses heartbeats for failure detection" not "Talk about this slide"
- Total timing must match talk duration within 20%
- Every content slide should have a transition cue (how to get there from the previous slide)
- Audience interaction beats every ~10 minutes of duration
- Do NOT ask the Speaker to review individual slide notes -- deliver the complete set
- The target_pace_wpm default is 130 (natural conversational pace)
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/speaker-notes-writer/
git commit -m "feat: add speaker-notes-writer skill with preference gathering"
```

---

## Task 6: Mark Old Plan Superseded, Update CLAUDE.md

**Files:**
- Modify: `docs/superpowers/plans/2026-03-29-phase-3-content-services.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Run full test suite**

Run: `source .venv/bin/activate && python3 -m pytest tests/ -v`

Expected: All tests PASS (354 existing + new Phase 3 tests).

- [ ] **Step 2: Mark old plan superseded**

Add at the top of `docs/superpowers/plans/2026-03-29-phase-3-content-services.md`:

```markdown
> **SUPERSEDED** by `docs/superpowers/plans/2026-03-29-phase-3-content-services-v2.md`. Redesigned with collaborative arc selection workflow and thin validation module (no Python arc logic). This plan is retained for historical reference.
```

- [ ] **Step 3: Update CLAUDE.md**

Add to the implementation table:
```
| Content validation | `src/content_validation.py` | N | Done |
```

Update Phase 3 status from "planned, NEXT" to "COMPLETE".

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md docs/superpowers/plans/2026-03-29-phase-3-content-services.md
git commit -m "docs: update CLAUDE.md with Phase 3 completion, mark old plan superseded"
```

---

### Critical Files for Implementation

- `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/skills/narrative-architect/SKILL.md` — two-stage collaborative skill (arc proposal + autonomous outline)
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/skills/speaker-notes-writer/SKILL.md` — preference gathering then autonomous notes
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/src/content_validation.py` — timing arithmetic and reference integrity only (~60 lines)
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/docs/architecture/content-services.md` — L1 service document (authoritative design reference)
