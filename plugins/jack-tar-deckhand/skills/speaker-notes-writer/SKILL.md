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

## Plugin Setup

```bash
PLUGIN_ROOT=$(python3 -c "
from pathlib import Path
import sys, os
if os.environ.get('JACK_TAR_DECKHAND_ROOT'):
    print(os.environ['JACK_TAR_DECKHAND_ROOT']); sys.exit()
home = Path.home()
for base in [home / '.claude' / 'plugins' / 'cache']:
    for p in base.rglob('jack-tar-deckhand/.claude-plugin/plugin.json'):
        print(str(p.parent.parent)); sys.exit()
dev = Path.cwd() / 'plugins' / 'jack-tar-deckhand'
if dev.exists():
    print(str(dev)); sys.exit()
print('NOT_FOUND')
" 2>/dev/null)
if [ -z "$PLUGIN_ROOT" ] || [ "$PLUGIN_ROOT" = "NOT_FOUND" ]; then echo "ERROR: jack-tar-deckhand not found" && exit 1; fi
```

### Step 3: Validate and Write

Validate the notes before writing:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
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
