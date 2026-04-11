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

**text** -- The speaking content for this slide:
- Bullet format: key phrases and memory joggers
- Sentence format: near-script with natural spoken language
- Detail scaled to experience level (first-time = more explicit cues, seasoned = less)

**estimated_seconds** -- Time allocation for this slide:
- Calculate from `target_pace_wpm` (default 130) and word count
- Heavier slides (data, key arguments) get more time
- Structural slides (title, dividers, closing) get less
- Total must sum to approximately `duration_minutes` from TalkBrief

**timing_marker** -- Cumulative time mark (e.g., "~5:30", "~12:00"):
- Helps the speaker track progress during delivery
- Calculate from cumulative estimated_seconds

**cues** -- Interaction cues appropriate to the slide:
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
