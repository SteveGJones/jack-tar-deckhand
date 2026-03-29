# L1 Content Services — Drill-Down

> **Source**: `jack-tar-deckhand.json` | **Level**: L1 > L2 | **Parent**: Presentation Engineering | **Date**: 2026-03-29

![Content Services L2](jack-tar-deckhand-content-services-l2.svg)

## L2 Capabilities

| Capability | Skill | Consumes | Produces |
|------------|-------|----------|----------|
| Outline Generation | `narrative-architect` | TalkBrief, StyleGuide | SlideOutline |
| Speaker Notes | `speaker-notes-writer` | TalkBrief, SlideOutline | SpeakerNotes |

## Data Contract Summary

| Contract | Format | Description |
|----------|--------|-------------|
| **TalkBrief** (in) | JSON | Speaker's talk topic, audience, duration, preferences |
| **StyleGuide** (in) | JSON | Palette, fonts, layout rules from Design Services |
| **SlideOutline** (out) | JSON | Per-slide: type, headline, body points, narrative beat, visual direction |
| **SpeakerNotes** (out) | JSON | Per-slide: timed notes, transition cues, calibrated to duration |
