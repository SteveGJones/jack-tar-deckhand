# L1 Content Services — Drill-Down

> **Source**: `jack-tar-deckhand.json` v1.4.0 | **Level**: L1 > L2 | **Parent**: Presentation Engineering | **Date**: 2026-04-03

![Content Services L2](jack-tar-deckhand-content-services-l2.svg)

## L2 Capabilities

| Capability | Type | Skill | Consumes | Produces |
|------------|------|-------|----------|----------|
| Outline Generation | Skill | `narrative-architect` | TalkBrief, StyleGuide | SlideOutline |
| Speaker Notes | Skill | `speaker-notes-writer` | TalkBrief, SlideOutline | SpeakerNotes |
| SmartArt Selection | AI Persona | `smartart-selector` | SlideOutline, StyleGuide, TalkBrief | SmartArtRecommendations |
| SmartArt Data Extraction | Skill | `smartart-extractor` | SlideOutline, SmartArtRecommendations | SmartArtSpec |

## Data Contract Summary

| Contract | Format | Description |
|----------|--------|-------------|
| **TalkBrief** (in) | JSON | Speaker's talk topic, audience, duration, preferences |
| **StyleGuide** (in) | JSON | Palette, fonts, layout rules from Design Services |
| **SlideOutline** (out) | JSON | Per-slide: type, headline, body points, narrative beat, visual direction, visual_intent |
| **SpeakerNotes** (out) | JSON | Per-slide: timed notes, transition cues, calibrated to duration |
| **SmartArtRecommendations** (out) | JSON | Per-slide: approved graphic type, enrichment tier, engine |
| **SmartArtSpec** (out) | JSON | Per-slide: engine-specific structured data for rendering |
