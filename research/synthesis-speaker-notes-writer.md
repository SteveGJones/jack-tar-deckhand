# Synthesis: speaker-notes-writer

> Distilled from: research/08-narrative-arc-patterns.md (Section 6: Speaker Notes Intelligence), docs/architecture/content-services.md, src/schemas/speaker_notes.schema.json

## 1. Lightweight Preference Gathering

The speaker-notes-writer gathers three preferences before autonomous execution. These are quick, single-answer questions -- not an extended interview.

### 1.1 The Three Questions

| # | Question | Options | Default |
|---|----------|---------|---------|
| 1 | **Note format** | Bullets (keywords/phrases) or Sentences (flowing prose) | Bullets |
| 2 | **Audience interaction style** | Minimal (few or no audience prompts), Moderate (show-of-hands, rhetorical questions), High (polls, discussions, scale ratings) | Moderate |
| 3 | **Speaker experience level** | Novice (detailed stage directions, explicit transitions), Experienced (key points and timing only), Expert (minimal -- timing markers and cues only) | Experienced |

### 1.2 How Preferences Shape Output

**Note format:**
- **Bullets:** Keywords and phrases. The speaker glances at notes for reminders, not scripts. Avoids reading. Recommended for most speakers.
- **Sentences:** Flowing talk track. Better for speakers who want a safety net or for talks being delivered by someone other than the author. Risk: reading verbatim kills audience connection.

**Interaction style:**
- **Minimal:** Interaction cues limited to transitions and emphasis. No audience_interaction cues inserted.
- **Moderate:** One interaction beat per 10 minutes (the attention-reset rule). Show-of-hands within first 2 minutes. Rhetorical questions at topic transitions.
- **High:** Interaction beats every 8 minutes. Polls, discussion prompts, scale ratings, reflection pauses. Only suitable for workshop-style or small-room talks.

**Experience level:**
- **Novice:** Full stage directions (`[PAUSE]`, `[SLOW DOWN]`, `[LOOK AT AUDIENCE]`), explicit transition phrases ("Now that we've covered X, let's move on to Y"), vocal emphasis markers, timing warnings.
- **Experienced:** Main points, transition cues, timing markers, key emphasis. No basic stage directions.
- **Expert:** Timing markers and interaction cues only. Trusts the speaker to handle delivery.

---

## 2. Timing Calibration

### 2.1 WPM-Based Calculation

| Speaking Pace | Words/Minute | When to Use |
|---------------|-------------|----------|
| Slow | 100-120 | Complex technical content, non-native audience |
| Standard | 130-150 | General conference talks (default: 130 WPM) |
| Fast | 160-170 | Motivational speeches, lively narratives |

The default target pace is 130 WPM. This is set in the SpeakerNotes output as `target_pace_wpm`.

### 2.2 Per-Slide Word Budget

Calculate the word budget for each slide's notes based on allocated time:

| Slide Duration | Words at 130 WPM | Typical Slide Type |
|----------------|------------------|--------------------|
| 30 seconds | ~65 words | Visual accent, blank_visual, section_divider |
| 1 minute | ~130 words | Simple content, stat_callout, quote |
| 1.5 minutes | ~195 words | Standard content slide |
| 2 minutes | ~260 words | Data-heavy, complex content, demo introduction |

### 2.3 Cumulative Timing Markers

Every slide in the SpeakerNotes includes a `timing_marker` showing the cumulative time at the START of that slide. Format: `~MM:SS`.

```
Slide 1:  timing_marker: "~0:00"
Slide 2:  timing_marker: "~0:30"
Slide 5:  timing_marker: "~5:30"
Slide 10: timing_marker: "~12:00"
Slide 15: timing_marker: "~20:00"
```

These markers let the speaker track progress against the clock. They are approximate (`~`) because actual delivery pace varies.

### 2.4 Duration Matching

The total of all `estimated_seconds` across all slides MUST equal (within 5%) the talk duration from the TalkBrief. If the sum exceeds the target duration, the writer must trim notes content. If it falls short, notes are too thin and need expansion.

**Validation formula:**

```
total_estimated_seconds = sum(note.estimated_seconds for note in notes)
target_seconds = talk_brief.duration_minutes * 60
drift = abs(total_estimated_seconds - target_seconds) / target_seconds
assert drift <= 0.05  # 5% tolerance
```

### 2.5 Duration Allocation by Slide Type

Not all slides get equal time. Structural slides are fast; content slides are slower:

| Slide Type | Typical Duration | Rationale |
|------------|-----------------|-----------|
| `title` | 15-30s | On screen as audience settles; brief welcome |
| `section_divider` | 10-20s | Pause for breath; transition phrase only |
| `content` | 90-120s | Main speaking slide |
| `two_column` | 90-120s | Compare/contrast needs explanation |
| `image_feature` | 60-90s | Image does work; less spoken |
| `data_chart` | 90-120s | Needs What + So What + Now What treatment |
| `stat_callout` | 30-60s | Let the number land, then interpret |
| `quote` | 30-45s | Read quote, add brief context |
| `icon_grid` | 60-90s | Walk through icons briefly |
| `diagram` | 90-120s | Walk through flow/architecture |
| `closing` | 45-60s | CTA and sign-off |
| `blank_visual` | 30-60s | Narrate over image; speaker's moment |

---

## 3. Cue Type Usage

The SpeakerNotes schema defines 6 cue types. Each slide's `cues` array contains zero or more cues.

### 3.1 When to Use Each Cue Type

| Cue Type | Purpose | When to Insert | Example Text |
|----------|---------|----------------|-------------|
| `transition` | Connect the previous slide to this one | Start of every slide EXCEPT the first | "Building on that data point..." / "Now that we've seen the problem, let me show you how we solved it." |
| `pause` | Deliberate silence for effect | After a striking statistic, after a quote, after revealing a key number on a stat_callout | "[pause 2 seconds for the number to land]" |
| `audience_interaction` | Engage the audience directly | Within first 2 minutes (establish connection), every 8-10 minutes (attention reset), before introducing a solution (make the problem personal). Never during climax or conclusion. | "Show of hands -- who has experienced this?" / "Take 10 seconds to think about a time this happened to you." |
| `emphasis` | Key point the speaker must stress | One per slide maximum. The single most important sentence or phrase. | "This is the number your CFO cares about." / "[SLOW DOWN] This is the most important point in the talk." |
| `demo` | Live demonstration or screen switch | At the start of any demo segment. Paired with a corresponding "return to slides" cue on the next slide. | "Switch to terminal, run the command." / "Open the browser tab with the live dashboard." |
| `build_animation` | Timed reveal of slide elements | When the slide uses progressive disclosure (e.g., revealing bullet points one at a time, or showing a second column after discussing the first) | "Click to reveal the second column." / "[CLICK] Advance to show the chart." |

### 3.2 Cue Density Guidelines

| Speaker Experience | Cues per Slide (typical) |
|-------------------|-------------------------|
| Novice | 2-4 (transition + emphasis + stage direction cues) |
| Experienced | 1-2 (transition + one other when needed) |
| Expert | 0-1 (only non-obvious cues: demo, build_animation) |

### 3.3 Cue Placement Rules

- **transition:** Always the FIRST cue for a slide (if present). It tells the speaker how to arrive at this slide.
- **pause:** Placed AFTER the content that needs to sink in. Never at the start of a slide.
- **audience_interaction:** Placed at the natural conversation break. Include the expected response handling ("Wait 5 seconds for show of hands. Acknowledge the response.").
- **emphasis:** Placed inline with the text it modifies. Mark the specific word or phrase.
- **demo:** Placed at the exact moment the speaker should switch context. Include what to open and where.
- **build_animation:** Placed before the speaker begins talking about the element that will be revealed.

---

## 4. Autonomous Execution Scope

After gathering the three preferences, the speaker-notes-writer produces the full SpeakerNotes (`./tmp/deck/speaker-notes.json`) without per-slide review.

### 4.1 What the Writer Decides Autonomously

- Per-slide note text (specific, actionable -- "Explain the three cost reduction strategies" not "Talk about this slide")
- Per-slide timing allocation (estimated_seconds)
- Cumulative timing markers
- Cue selection and placement
- Transition phrasing between slides
- Emphasis markers on key phrases
- Audience interaction placement (governed by the chosen interaction style)
- Stage direction depth (governed by the chosen experience level)

### 4.2 What the Writer Does NOT Decide

- Slide order or content (comes from SlideOutline -- the writer follows it exactly)
- Slide types or headlines (immutable from the outline)
- Target speaking pace (default 130 WPM; could be overridden by TalkBrief preferences)
- Talk duration (from TalkBrief -- the writer calibrates to it, not the reverse)

### 4.3 Input Dependencies

The speaker-notes-writer REQUIRES the SlideOutline to exist before it runs. The outline provides:
- Slide order and count
- Per-slide type, headline, body points
- Narrative beat (governs emotional tone of notes)
- Transition notes (the architect's structural transitions, which the writer converts to spoken phrases)

### 4.4 Notes Structure Per Slide

Each entry in the SpeakerNotes array follows this structure (from the schema):

```json
{
  "slide_number": 5,
  "text": "The key insight from our Q3 data is...",
  "estimated_seconds": 90,
  "timing_marker": "~8:00",
  "cues": [
    {"type": "transition", "text": "Building on the trends we just saw..."},
    {"type": "emphasis", "text": "This is the number that changed our strategy."},
    {"type": "pause", "text": "[pause 2 seconds after revealing the 73% figure]"}
  ]
}
```

---

## 5. Notes Anti-Patterns

- **Writing full scripts.** Notes are glance-able reminders, not teleprompter scripts. Full sentences encourage reading, which kills audience connection. Exception: sentence format chosen by speaker preference.
- **Generic filler.** "Talk about this slide" or "Explain the chart" is useless. Notes must be specific: "Walk through the three cost drivers: licensing at 40%, compute at 35%, and support at 25%."
- **Missing timing markers.** Every slide needs a cumulative timing marker. Without them, the speaker has no clock discipline.
- **Missing transition cues.** Stumbling between slides is the most common delivery failure. Every slide (except the first) needs a transition cue.
- **Forgetting core-moment rule.** Opening, closing, and key stories should be memorized. Notes for these slides should be minimal keywords, not detailed text. The speaker must have eye contact at critical moments.
- **Overloading novice speakers with cues.** More than 4 cues per slide creates cognitive overload. Prioritize transition and emphasis; add others selectively.
- **Duration drift.** If total estimated time exceeds the TalkBrief duration by more than 5%, content must be trimmed. Do not silently produce notes that run over.

---

## Sources

- Research #08 (Narrative Arc & Conference Storytelling Patterns): Section 6 (Speaker Notes Intelligence -- WPM calibration, timing markers, transition cues, audience prompts, emphasis markers, notes structure template, anti-patterns)
- Research #08: Section 3 (Invisible Slides -- audience interaction beats, section dividers, pause slides, the 10-minute attention reset rule)
- Content Services L1 architecture document: speaker-notes-writer workflow, cue type table, collaborative preferences, data contracts
- Schema: `src/schemas/speaker_notes.schema.json` (output contract)
