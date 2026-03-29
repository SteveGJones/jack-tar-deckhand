# Pipeline Execution Flow

> **Source**: `jack-tar-deckhand.json` | **Type**: End-to-end pipeline | **Date**: 2026-03-29

![Pipeline Execution Flow](jack-tar-deckhand-pipeline-flow.svg)

## Pipeline Summary

### Setup

| Step | From | To | Data / Action |
|------|------|----|---------------|
| 1 | Speaker | Conductor | TalkBrief (topic, audience, duration, budget) |
| 2 | Conductor | Image Services | Provider Discovery (probe available providers) |
| 3 | Conductor | Speaker | Available providers + cost estimate; Speaker confirms budget |

### Draft Cycle (iterative)

| Step | From | To | Data / Action |
|------|------|----|---------------|
| 4 | Conductor | Design Services | Derive StyleGuide (palette, fonts, layout) |
| 5 | Conductor | Content Services | Generate Outline + Speaker Notes |
| 6 | Conductor | Image Services | Draft images (Ollama for layout, or cloud at reduced quality for prompt refinement) |
| 7 | Conductor | Assembly | Build draft PPTX |
| 8 | Speaker | Conductor | Review draft: iterate (back to step 4) or approve for production |

Steps 4-8 repeat until the Speaker approves the draft. Prompts are model-specific -- later drafts should use the target cloud provider at reduced quality, not Ollama, for accurate prompt refinement.

### Production (single pass)

| Step | From | To | Data / Action |
|------|------|----|---------------|
| 9 | Conductor | Image Services | Full-quality production images via best available provider |
| 10 | Conductor | Assembly | Build final PPTX + Visual QA (25 automated checks) |
| 11 | Conductor | Reviewer | Presentation Review (conference best practices) |
| 12 | Conductor | Speaker | Deliver .pptx + review + cost report |
