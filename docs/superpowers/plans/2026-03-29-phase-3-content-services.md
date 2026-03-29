# Phase 3: Content Services — narrative-architect & speaker-notes-writer

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the two Content Services skills that transform a TalkBrief into structured presentation content — first a SlideOutline (via `narrative-architect`), then timed SpeakerNotes (via `speaker-notes-writer`). Both are Claude Code skills backed by SKILL.md files that use the DeckContext infrastructure from Phase 1.

**Architecture:** Two Claude Code skills in `.claude/skills/`, each reading DeckContext files via `src/deckcontext.py` and writing their output contract back. The `narrative-architect` reads `talk-brief.json` + `style-guide.json` and produces `outline.json`. The `speaker-notes-writer` reads `talk-brief.json` + `outline.json` and produces `speaker-notes.json`. The dependency is sequential: narrative-architect must run before speaker-notes-writer.

**Tech Stack:** Python 3.8+, jsonschema, pytest, src/deckcontext.py (Phase 1)

**Dependencies:** Phase 1 (Foundation) must be completed — `src/deckcontext.py`, all JSON Schemas in `src/schemas/`, and test fixtures must exist.

**Phases overview (this is Phase 3 of 6):**
- Phase 1: Foundation (completed) — DeckContext, schemas, utilities
- Phase 2: Design Services — `slide-stylist`
- **Phase 3: Content Services** (this plan) — `narrative-architect`, `speaker-notes-writer`
- Phase 4: Image Services — 8 skills + 1 agent
- Phase 5: Assembly & QA — `deck-assembler`, `deck-qa`, `presentation-reviewer`
- Phase 6: Orchestration — `deck-conductor`

---

## File Structure

```
research/
  synthesis-narrative-architect.md       # Research synthesis (MUST exist before Task 3)
  synthesis-speaker-notes-writer.md      # Research synthesis (MUST exist before Task 6)
src/
  narrative_architect.py                 # Outline generation logic
  speaker_notes_writer.py               # Speaker notes generation logic
.claude/
  skills/
    narrative-architect/
      SKILL.md                           # Claude Code skill definition
    speaker-notes-writer/
      SKILL.md                           # Claude Code skill definition
tests/
  test_narrative_architect.py            # Unit tests for outline generation
  test_speaker_notes_writer.py           # Unit tests for speaker notes generation
  test_content_integration.py            # Integration test: brief → outline → notes
  fixtures/
    valid_talk_brief.json                # (from Phase 1 — input)
    valid_style_guide.json               # (from Phase 1 — input)
    valid_slide_outline.json             # (from Phase 1 — used for validation)
    valid_speaker_notes.json             # (from Phase 1 — used for validation)
    talk_brief_technical_30min.json      # Extended fixture: technical 30-min talk
    talk_brief_keynote_45min.json        # Extended fixture: keynote 45-min talk
    talk_brief_lightning_5min.json       # Extended fixture: lightning 5-min talk
```

---

## Task 1: Research Synthesis — narrative-architect

**Files:**
- Create: `research/synthesis-narrative-architect.md`

- [ ] **Step 1: Create the narrative-architect research synthesis**

Create `research/synthesis-narrative-architect.md`:

```markdown
# narrative-architect — Research Synthesis

## Decision Summary
- Structure selection: Auto-select from 16 catalogued talk structures based on tone, audience, duration, and key_takeaways count — Source: #08 Section 1
- Slide density: Calibrate to duration × style — ~1 slide/min content-heavy, ~2 slides/min visual-heavy — Source: #08 Section 2
- Invisible slides: Section dividers, breathing room, and interaction beats are structural elements that must be injected — Source: #08 Section 3
- Architecture pattern: Pure function — reads TalkBrief + StyleGuide from DeckContext, writes SlideOutline to DeckContext
- Key constraint: All 12 slide types must be available; selection driven by narrative beat and content type

## Requirements (from research)
1. Select narrative arc from 16 structures (SCR, Monroe's, Hero's Journey, Problem-Solution-Impact, Problem-Demo-Impact, What-So What-Now What, Hook-Thesis-Body-Callback-CTA, Story-Point-Application, Pecha Kucha, Ignite, Lightning, Lessig, Takahashi, 10/20/30, Duarte Sparkline, Modular Deck) — Source: #08 §1
2. Slide density must match format: Pecha Kucha = exactly 20, Ignite = exactly 20, Lightning = 10-15, standard = duration × density factor — Source: #08 §2
3. Never place two data-heavy slides consecutively — Source: #08 §5.1 Rule 1
4. Section dividers before every major topic shift — Source: #08 §5.1 Rule 2
5. One idea per slide; max 5 body points; max 6 visual elements — Source: #08 §5.1 Rules 4-5
6. Opening: title → hook → (optional agenda) → first content — Source: #08 §5.2
7. Closing: recap → callback → CTA → resources → thank you — Source: #08 §5.3
8. Attention reset every 10 minutes (interaction beat, story, demo, visual change) — Source: #08 §5.4
9. visual_direction must be prose suitable for image prompt generation — Source: data-contracts §4
10. Each slide must have layout_template referencing a StyleGuide template — Source: data-contracts §4
11. transition_note provides the verbal bridge from the previous slide — Source: data-contracts §4
12. Layout archetypes: 18 defined with content zone specs — Source: #01

## Design Rules (machine-checkable where possible)
- Rule 1: Slide count within format bounds — Check: assert total_slides within [min, max] for the selected arc
- Rule 2: No consecutive data_chart slides — Check: iterate slides, assert no adjacent slide_type == "data_chart"
- Rule 3: Section divider before each narrative beat transition — Check: when narrative_beat changes between slides, previous slide or current slide should be section_divider
- Rule 4: body_points max 5 per slide — Check: len(slide.body_points) <= 5
- Rule 5: First slide is type "title" — Check: slides[0].slide_type == "title"
- Rule 6: Last slide is type "closing" — Check: slides[-1].slide_type == "closing"
- Rule 7: slide_number is sequential starting at 1 — Check: slides[i].slide_number == i + 1
- Rule 8: Every slide has a headline — Check: len(slide.headline) > 0
- Rule 9: narrative_arc is a non-empty string — Check: len(outline.narrative_arc) > 0
- Rule 10: estimated_duration_minutes matches TalkBrief.duration_minutes ± 20% — Check: abs(outline.estimated_duration_minutes - brief.duration_minutes) / brief.duration_minutes <= 0.2

## Recommended Libraries/APIs
| Library | Purpose | Install | License |
|---------|---------|---------|---------|
| jsonschema | Schema validation | pip install jsonschema | MIT |
| pytest | Testing | pip install pytest | MIT |

## Structure Selection Guide
| If the talk is... | Use this structure |
|--------------------|--------------------|
| Persuading executives to approve a strategy | situation-complication-resolution |
| Advocating for change with a clear ask | monroes-motivated-sequence |
| Telling a transformation story at a keynote | heros-journey |
| Pitching a product or startup | problem-solution-impact |
| Demoing a product to developers | problem-demo-impact |
| Presenting quarterly data to leadership | what-so-what-now-what |
| Giving a conference talk to inspire action | hook-thesis-body-callback-cta |
| Teaching through stories at a workshop | story-point-application |
| Presenting at a design meetup (6:40) | pecha-kucha |
| Sharing a quick idea at a tech meetup (5 min) | lightning-talk |
| Making a legal or advocacy argument | lessig-method |
| Presenting without design resources | takahashi-method |
| Running an unpredictable client meeting | modular-deck |
| Giving a vision/all-hands talk | duarte-sparkline |

## Open Questions
- Should the narrative-architect accept a user-provided arc override, or always auto-select?
  Decision: Accept optional `arc_override` in TalkBrief.preferences (not in schema yet — use tone + audience heuristics for now)

## Sources
- #08: Narrative Arc & Conference Storytelling Patterns (primary — all sections)
- #01: Slide Layout Intelligence & Design Rules Engine (secondary — layout types)
- #07: Conference Presentation QA Heuristics (secondary — anti-patterns to avoid in outline)
- data-contracts.md: SlideOutline schema specification
```

- [ ] **Step 2: Verify the synthesis covers all critical concerns**

Read through the synthesis and confirm:
1. All 16 talk structures from research #08 are listed
2. Slide density guidance is present
3. Sequencing rules are machine-checkable
4. The structure selection guide maps tone/audience to arc

- [ ] **Step 3: Commit**

```bash
git add research/synthesis-narrative-architect.md
git commit -m "docs: add narrative-architect research synthesis"
```

---

## Task 2: Extended Test Fixtures for Content Services

**Files:**
- Create: `tests/fixtures/talk_brief_technical_30min.json`
- Create: `tests/fixtures/talk_brief_keynote_45min.json`
- Create: `tests/fixtures/talk_brief_lightning_5min.json`

- [ ] **Step 1: Write extended fixture tests**

These fixtures test different durations, tones, and audience types to ensure the narrative-architect handles the full range of inputs.

Create `tests/fixtures/talk_brief_technical_30min.json`:

```json
{
  "topic": "Zero-Downtime Database Migrations at Scale",
  "audience": "Senior backend engineers running PostgreSQL in production",
  "duration_minutes": 30,
  "tone": "technical",
  "key_takeaways": [
    "Blue-green deployments eliminate migration downtime",
    "Schema changes must be backward-compatible for at least one release cycle",
    "pg_repack handles table rewrites without locks"
  ],
  "branding": {
    "company_name": "DataScale Inc",
    "primary_color": "0F172A",
    "secondary_color": "3B82F6"
  },
  "preferences": {
    "style": "diagram-heavy",
    "slide_count_hint": 25,
    "image_backend": "ollama",
    "resolution": "1080p",
    "include_speaker_notes": true,
    "include_charts": true
  },
  "data_sources": [
    {
      "label": "migration_downtime",
      "type": "inline_json",
      "content": "{\"before\": {\"avg_minutes\": 45, \"max_minutes\": 180}, \"after\": {\"avg_minutes\": 0, \"max_minutes\": 2}}"
    }
  ]
}
```

Create `tests/fixtures/talk_brief_keynote_45min.json`:

```json
{
  "topic": "The Future of Human-AI Collaboration in Creative Work",
  "audience": "Mixed audience of designers, engineers, and product managers at a company all-hands",
  "duration_minutes": 45,
  "tone": "inspirational",
  "key_takeaways": [
    "AI amplifies human creativity rather than replacing it",
    "The best results come from human-AI feedback loops",
    "Every team member can benefit from AI collaboration today"
  ],
  "preferences": {
    "style": "image-rich",
    "slide_count_hint": 35,
    "image_backend": "ollama",
    "resolution": "1080p",
    "include_speaker_notes": true,
    "include_charts": false
  }
}
```

Create `tests/fixtures/talk_brief_lightning_5min.json`:

```json
{
  "topic": "Why Your Error Messages Are Terrible (And How to Fix Them)",
  "audience": "Developers at a Python meetup",
  "duration_minutes": 5,
  "tone": "conversational",
  "key_takeaways": [
    "Good error messages tell the user what to do, not just what went wrong"
  ],
  "preferences": {
    "style": "minimalist",
    "image_backend": "ollama",
    "resolution": "1080p",
    "include_speaker_notes": true,
    "include_charts": false
  }
}
```

- [ ] **Step 2: Validate fixtures against TalkBrief schema**

Run:
```bash
source .venv/bin/activate && python3 -c "
import json
from jsonschema import validate

with open('src/schemas/talk_brief.schema.json') as f:
    schema = json.load(f)

for fixture in ['talk_brief_technical_30min', 'talk_brief_keynote_45min', 'talk_brief_lightning_5min']:
    with open(f'tests/fixtures/{fixture}.json') as f:
        data = json.load(f)
    validate(instance=data, schema=schema)
    print(f'{fixture}: VALID')
"
```

Expected: All 3 fixtures print VALID.

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/talk_brief_technical_30min.json tests/fixtures/talk_brief_keynote_45min.json tests/fixtures/talk_brief_lightning_5min.json
git commit -m "test: add extended TalkBrief fixtures for content services testing"
```

---

## Task 3: narrative-architect — Core Logic Module

**Files:**
- Create: `src/narrative_architect.py`
- Create: `tests/test_narrative_architect.py`

- [ ] **Step 1: Write unit tests for the narrative-architect**

Create `tests/test_narrative_architect.py`:

```python
"""Tests for narrative-architect outline generation logic."""

import json
import os
import pytest
from jsonschema import validate

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'schemas')
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def load_schema(name):
    path = os.path.join(SCHEMA_DIR, f'{name}.schema.json')
    with open(path) as f:
        return json.load(f)


def load_fixture(name):
    path = os.path.join(FIXTURE_DIR, f'{name}.json')
    with open(path) as f:
        return json.load(f)


class TestSelectNarrativeArc:
    def test_technical_tone_selects_appropriate_arc(self):
        from src.narrative_architect import select_narrative_arc
        brief = load_fixture('valid_talk_brief')
        arc = select_narrative_arc(brief)
        assert arc in [
            'problem-solution-impact',
            'problem-demo-impact',
            'hook-thesis-body-callback-cta',
            'what-so-what-now-what',
        ]

    def test_inspirational_tone_selects_story_arc(self):
        from src.narrative_architect import select_narrative_arc
        brief = load_fixture('talk_brief_keynote_45min')
        arc = select_narrative_arc(brief)
        assert arc in [
            'heros-journey',
            'duarte-sparkline',
            'hook-thesis-body-callback-cta',
        ]

    def test_short_duration_selects_compact_arc(self):
        from src.narrative_architect import select_narrative_arc
        brief = load_fixture('talk_brief_lightning_5min')
        arc = select_narrative_arc(brief)
        assert arc in [
            'lightning-talk',
            'problem-solution-impact',
        ]

    def test_all_arcs_are_valid_strings(self):
        from src.narrative_architect import KNOWN_ARCS
        assert len(KNOWN_ARCS) >= 14
        for arc in KNOWN_ARCS:
            assert isinstance(arc, str)
            assert len(arc) > 0


class TestCalculateSlideDensity:
    def test_30min_standard_density(self):
        from src.narrative_architect import calculate_slide_count
        count = calculate_slide_count(duration_minutes=30, style='image-rich')
        assert 15 <= count <= 35

    def test_5min_lightning_density(self):
        from src.narrative_architect import calculate_slide_count
        count = calculate_slide_count(duration_minutes=5, style='minimalist')
        assert 5 <= count <= 15

    def test_45min_keynote_density(self):
        from src.narrative_architect import calculate_slide_count
        count = calculate_slide_count(duration_minutes=45, style='image-rich')
        assert 25 <= count <= 50

    def test_respects_slide_count_hint(self):
        from src.narrative_architect import calculate_slide_count
        count = calculate_slide_count(
            duration_minutes=30, style='image-rich', slide_count_hint=20
        )
        # Should be within ±30% of the hint
        assert 14 <= count <= 26

    def test_data_heavy_style_uses_lower_density(self):
        from src.narrative_architect import calculate_slide_count
        count_data = calculate_slide_count(duration_minutes=30, style='data-heavy')
        count_image = calculate_slide_count(duration_minutes=30, style='image-rich')
        assert count_data <= count_image


class TestGenerateSlideSequence:
    def test_first_slide_is_title(self):
        from src.narrative_architect import generate_slide_sequence
        brief = load_fixture('valid_talk_brief')
        slides = generate_slide_sequence(
            brief, arc='problem-solution-impact', slide_count=15
        )
        assert slides[0]['slide_type'] == 'title'

    def test_last_slide_is_closing(self):
        from src.narrative_architect import generate_slide_sequence
        brief = load_fixture('valid_talk_brief')
        slides = generate_slide_sequence(
            brief, arc='problem-solution-impact', slide_count=15
        )
        assert slides[-1]['slide_type'] == 'closing'

    def test_slide_numbers_are_sequential(self):
        from src.narrative_architect import generate_slide_sequence
        brief = load_fixture('valid_talk_brief')
        slides = generate_slide_sequence(
            brief, arc='problem-solution-impact', slide_count=15
        )
        for i, slide in enumerate(slides):
            assert slide['slide_number'] == i + 1

    def test_all_slides_have_required_fields(self):
        from src.narrative_architect import generate_slide_sequence
        brief = load_fixture('valid_talk_brief')
        slides = generate_slide_sequence(
            brief, arc='problem-solution-impact', slide_count=15
        )
        for slide in slides:
            assert 'slide_number' in slide
            assert 'slide_type' in slide
            assert 'headline' in slide
            assert len(slide['headline']) > 0

    def test_all_slide_types_are_valid(self):
        from src.narrative_architect import generate_slide_sequence
        valid_types = {
            'title', 'section_divider', 'content', 'two_column',
            'image_feature', 'data_chart', 'stat_callout', 'quote',
            'icon_grid', 'diagram', 'closing', 'blank_visual',
        }
        brief = load_fixture('valid_talk_brief')
        slides = generate_slide_sequence(
            brief, arc='problem-solution-impact', slide_count=15
        )
        for slide in slides:
            assert slide['slide_type'] in valid_types, (
                f"Invalid slide_type: {slide['slide_type']}"
            )

    def test_body_points_max_five(self):
        from src.narrative_architect import generate_slide_sequence
        brief = load_fixture('valid_talk_brief')
        slides = generate_slide_sequence(
            brief, arc='problem-solution-impact', slide_count=15
        )
        for slide in slides:
            if 'body_points' in slide:
                assert len(slide['body_points']) <= 5

    def test_no_consecutive_data_chart_slides(self):
        from src.narrative_architect import generate_slide_sequence
        brief = load_fixture('talk_brief_technical_30min')
        slides = generate_slide_sequence(
            brief, arc='what-so-what-now-what', slide_count=20
        )
        for i in range(len(slides) - 1):
            if slides[i]['slide_type'] == 'data_chart':
                assert slides[i + 1]['slide_type'] != 'data_chart', (
                    f"Consecutive data_chart at slides {i+1} and {i+2}"
                )

    def test_section_dividers_at_beat_transitions(self):
        from src.narrative_architect import generate_slide_sequence
        brief = load_fixture('valid_talk_brief')
        slides = generate_slide_sequence(
            brief, arc='problem-solution-impact', slide_count=20
        )
        # Find all narrative beat transitions
        beat_transitions = []
        for i in range(1, len(slides)):
            prev_beat = slides[i-1].get('narrative_beat', '')
            curr_beat = slides[i].get('narrative_beat', '')
            if prev_beat and curr_beat and prev_beat != curr_beat:
                beat_transitions.append(i)
        # At least some transitions should have a section_divider nearby
        # (within 1 slide of the transition point)
        if beat_transitions:
            divider_positions = {
                i for i, s in enumerate(slides)
                if s['slide_type'] == 'section_divider'
            }
            covered = sum(
                1 for t in beat_transitions
                if t in divider_positions or t - 1 in divider_positions
            )
            # At least 50% of transitions should have dividers
            assert covered >= len(beat_transitions) * 0.5


class TestBuildOutline:
    def test_builds_valid_outline_from_brief(self):
        from src.narrative_architect import build_outline
        brief = load_fixture('valid_talk_brief')
        style_guide = load_fixture('valid_style_guide')
        outline = build_outline(brief, style_guide)
        schema = load_schema('slide_outline')
        validate(instance=outline, schema=schema)

    def test_outline_has_narrative_arc(self):
        from src.narrative_architect import build_outline
        brief = load_fixture('valid_talk_brief')
        style_guide = load_fixture('valid_style_guide')
        outline = build_outline(brief, style_guide)
        assert 'narrative_arc' in outline
        assert len(outline['narrative_arc']) > 0

    def test_outline_duration_matches_brief(self):
        from src.narrative_architect import build_outline
        brief = load_fixture('valid_talk_brief')
        style_guide = load_fixture('valid_style_guide')
        outline = build_outline(brief, style_guide)
        # Duration should be within ±20% of the brief
        ratio = outline['estimated_duration_minutes'] / brief['duration_minutes']
        assert 0.8 <= ratio <= 1.2

    def test_outline_total_slides_matches_array(self):
        from src.narrative_architect import build_outline
        brief = load_fixture('valid_talk_brief')
        style_guide = load_fixture('valid_style_guide')
        outline = build_outline(brief, style_guide)
        if 'total_slides' in outline:
            assert outline['total_slides'] == len(outline['slides'])

    def test_content_slides_have_visual_direction(self):
        from src.narrative_architect import build_outline
        brief = load_fixture('valid_talk_brief')
        style_guide = load_fixture('valid_style_guide')
        outline = build_outline(brief, style_guide)
        visual_slide_types = {
            'title', 'image_feature', 'content', 'two_column',
            'stat_callout', 'quote', 'blank_visual',
        }
        for slide in outline['slides']:
            if slide['slide_type'] in visual_slide_types:
                assert 'visual_direction' in slide, (
                    f"Slide {slide['slide_number']} ({slide['slide_type']}) "
                    f"missing visual_direction"
                )
                assert len(slide.get('visual_direction', '')) > 0

    def test_lightning_talk_produces_compact_outline(self):
        from src.narrative_architect import build_outline
        brief = load_fixture('talk_brief_lightning_5min')
        style_guide = load_fixture('valid_style_guide')
        outline = build_outline(brief, style_guide)
        assert len(outline['slides']) <= 15
        assert len(outline['slides']) >= 5

    def test_keynote_produces_expanded_outline(self):
        from src.narrative_architect import build_outline
        brief = load_fixture('talk_brief_keynote_45min')
        style_guide = load_fixture('valid_style_guide')
        outline = build_outline(brief, style_guide)
        assert len(outline['slides']) >= 20

    def test_data_chart_slides_present_when_data_sources_exist(self):
        from src.narrative_architect import build_outline
        brief = load_fixture('talk_brief_technical_30min')
        style_guide = load_fixture('valid_style_guide')
        outline = build_outline(brief, style_guide)
        chart_slides = [
            s for s in outline['slides']
            if s['slide_type'] == 'data_chart'
        ]
        # Brief has data_sources, so at least one data_chart slide expected
        if brief.get('data_sources'):
            assert len(chart_slides) >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_narrative_architect.py -v`

Expected: FAIL — `src.narrative_architect` module not found.

- [ ] **Step 3: Implement the narrative-architect module**

Create `src/narrative_architect.py`:

```python
"""narrative-architect — Generate a SlideOutline from TalkBrief + StyleGuide.

Selects a narrative arc based on talk characteristics, calculates slide
density, and produces a structured slide sequence with per-slide type,
headline, body points, narrative beat, visual direction, and layout template.

This module provides the core logic. The SKILL.md file in
.claude/skills/narrative-architect/ drives orchestration via Claude Code.
"""

import math

# All supported narrative arc identifiers
KNOWN_ARCS = [
    'situation-complication-resolution',
    'monroes-motivated-sequence',
    'heros-journey',
    'problem-solution-impact',
    'problem-demo-impact',
    'what-so-what-now-what',
    'hook-thesis-body-callback-cta',
    'story-point-application',
    'pecha-kucha',
    'ignite',
    'lightning-talk',
    'lessig-method',
    'takahashi-method',
    'kawasaki-10-20-30',
    'duarte-sparkline',
    'modular-deck',
]

# Valid slide types (must match slide_outline.schema.json enum)
VALID_SLIDE_TYPES = [
    'title', 'section_divider', 'content', 'two_column',
    'image_feature', 'data_chart', 'stat_callout', 'quote',
    'icon_grid', 'diagram', 'closing', 'blank_visual',
]

# Valid visual types (must match slide_outline.schema.json enum)
VALID_VISUAL_TYPES = [
    'hero_image', 'diagram', 'chart', 'icon_set',
    'pattern_background', 'none',
]

# Density multipliers by style (slides per minute)
STYLE_DENSITY = {
    'minimalist': 0.8,
    'data-heavy': 0.6,
    'image-rich': 1.0,
    'diagram-heavy': 0.7,
    'corporate': 0.7,
    'creative': 1.2,
}

# Arc templates: define the beat sequence for each narrative structure.
# Each beat is (beat_name, fraction_of_total_slides, suggested_slide_types).
ARC_TEMPLATES = {
    'situation-complication-resolution': [
        ('hook', 0.07, ['title']),
        ('situation', 0.25, ['content', 'image_feature', 'stat_callout']),
        ('complication', 0.30, ['content', 'data_chart', 'quote', 'two_column']),
        ('resolution', 0.30, ['content', 'diagram', 'icon_grid', 'two_column']),
        ('cta', 0.08, ['closing']),
    ],
    'monroes-motivated-sequence': [
        ('attention', 0.10, ['title', 'image_feature']),
        ('need', 0.25, ['content', 'data_chart', 'stat_callout', 'quote']),
        ('satisfaction', 0.30, ['content', 'diagram', 'two_column', 'icon_grid']),
        ('visualization', 0.20, ['image_feature', 'two_column', 'content']),
        ('action', 0.15, ['content', 'closing']),
    ],
    'heros-journey': [
        ('ordinary-world', 0.15, ['title', 'image_feature', 'content']),
        ('challenge', 0.15, ['content', 'data_chart', 'quote']),
        ('journey', 0.25, ['content', 'image_feature', 'two_column']),
        ('transformation', 0.20, ['content', 'diagram', 'stat_callout']),
        ('new-world', 0.15, ['content', 'image_feature', 'data_chart']),
        ('cta', 0.10, ['content', 'closing']),
    ],
    'problem-solution-impact': [
        ('hook', 0.07, ['title']),
        ('problem', 0.30, ['content', 'data_chart', 'stat_callout', 'quote', 'image_feature']),
        ('solution', 0.35, ['content', 'diagram', 'two_column', 'icon_grid', 'image_feature']),
        ('impact', 0.20, ['data_chart', 'stat_callout', 'content', 'quote']),
        ('cta', 0.08, ['closing']),
    ],
    'problem-demo-impact': [
        ('hook', 0.07, ['title']),
        ('problem', 0.25, ['content', 'data_chart', 'stat_callout']),
        ('demo', 0.40, ['content', 'diagram', 'image_feature', 'two_column']),
        ('impact', 0.20, ['data_chart', 'stat_callout', 'content']),
        ('cta', 0.08, ['closing']),
    ],
    'what-so-what-now-what': [
        ('hook', 0.07, ['title']),
        ('what-1', 0.12, ['data_chart', 'content']),
        ('so-what-1', 0.10, ['content', 'stat_callout']),
        ('now-what-1', 0.10, ['content', 'icon_grid']),
        ('what-2', 0.12, ['data_chart', 'content']),
        ('so-what-2', 0.10, ['content', 'stat_callout']),
        ('now-what-2', 0.10, ['content', 'icon_grid']),
        ('what-3', 0.12, ['data_chart', 'content']),
        ('so-what-3', 0.07, ['content', 'stat_callout']),
        ('now-what-3', 0.05, ['content', 'closing']),
        ('cta', 0.05, ['closing']),
    ],
    'hook-thesis-body-callback-cta': [
        ('hook', 0.08, ['title', 'image_feature']),
        ('thesis', 0.07, ['content', 'stat_callout']),
        ('evidence-1', 0.22, ['content', 'data_chart', 'image_feature', 'two_column']),
        ('evidence-2', 0.22, ['content', 'data_chart', 'image_feature', 'two_column']),
        ('evidence-3', 0.22, ['content', 'data_chart', 'image_feature', 'two_column']),
        ('callback', 0.07, ['image_feature', 'content']),
        ('cta', 0.12, ['content', 'closing']),
    ],
    'story-point-application': [
        ('hook', 0.05, ['title']),
        ('story-1', 0.12, ['image_feature', 'content']),
        ('point-1', 0.10, ['content', 'stat_callout']),
        ('application-1', 0.10, ['content', 'diagram']),
        ('story-2', 0.12, ['image_feature', 'content']),
        ('point-2', 0.10, ['content', 'stat_callout']),
        ('application-2', 0.10, ['content', 'diagram']),
        ('story-3', 0.12, ['image_feature', 'content']),
        ('point-3', 0.10, ['content', 'stat_callout']),
        ('cta', 0.09, ['content', 'closing']),
    ],
    'lightning-talk': [
        ('hook', 0.15, ['title']),
        ('problem', 0.25, ['content', 'stat_callout']),
        ('solution', 0.35, ['content', 'diagram', 'image_feature']),
        ('impact', 0.15, ['stat_callout', 'content']),
        ('cta', 0.10, ['closing']),
    ],
    'duarte-sparkline': [
        ('hook', 0.05, ['title']),
        ('what-is-1', 0.12, ['content', 'data_chart']),
        ('what-could-be-1', 0.12, ['image_feature', 'content']),
        ('what-is-2', 0.12, ['content', 'data_chart']),
        ('what-could-be-2', 0.12, ['image_feature', 'content']),
        ('what-is-3', 0.12, ['content', 'data_chart']),
        ('what-could-be-3', 0.12, ['image_feature', 'content']),
        ('new-bliss', 0.13, ['image_feature', 'content']),
        ('cta', 0.10, ['content', 'closing']),
    ],
    'pecha-kucha': [
        ('hook', 0.05, ['title']),
        ('body', 0.85, ['image_feature', 'blank_visual', 'content']),
        ('close', 0.10, ['closing']),
    ],
    'ignite': [
        ('hook', 0.05, ['title']),
        ('body', 0.85, ['image_feature', 'blank_visual', 'content']),
        ('close', 0.10, ['closing']),
    ],
    'lessig-method': [
        ('hook', 0.05, ['title']),
        ('argument', 0.85, ['blank_visual', 'quote', 'image_feature', 'stat_callout']),
        ('cta', 0.10, ['closing']),
    ],
    'takahashi-method': [
        ('hook', 0.05, ['title']),
        ('body', 0.85, ['blank_visual', 'stat_callout', 'content']),
        ('cta', 0.10, ['closing']),
    ],
    'kawasaki-10-20-30': [
        ('hook', 0.10, ['title']),
        ('problem', 0.10, ['content']),
        ('value-prop', 0.10, ['content', 'stat_callout']),
        ('technology', 0.10, ['diagram', 'content']),
        ('business-model', 0.10, ['content', 'data_chart']),
        ('go-to-market', 0.10, ['content', 'icon_grid']),
        ('competition', 0.10, ['two_column', 'content']),
        ('team', 0.10, ['icon_grid', 'content']),
        ('financials', 0.10, ['data_chart', 'content']),
        ('cta', 0.10, ['closing']),
    ],
    'modular-deck': [
        ('hook', 0.10, ['title', 'content']),
        ('module-1', 0.20, ['content', 'data_chart', 'image_feature']),
        ('module-2', 0.20, ['content', 'data_chart', 'image_feature']),
        ('module-3', 0.20, ['content', 'data_chart', 'image_feature']),
        ('module-4', 0.20, ['content', 'diagram', 'two_column']),
        ('close', 0.10, ['content', 'closing']),
    ],
}


def select_narrative_arc(brief):
    """Select the best narrative arc based on talk brief characteristics.

    Uses tone, duration, audience description, and key_takeaways count
    to pick the most appropriate structure from KNOWN_ARCS.

    Args:
        brief: TalkBrief dictionary.

    Returns:
        Arc identifier string from KNOWN_ARCS.
    """
    tone = brief.get('tone', 'professional')
    duration = brief.get('duration_minutes', 30)
    takeaways = brief.get('key_takeaways', [])

    # Fixed-format talks override everything
    if duration == 5:
        return 'lightning-talk'
    if duration <= 7:
        return 'lightning-talk'

    # Tone-based selection for standard durations
    arc_by_tone = {
        'technical': 'problem-solution-impact',
        'professional': 'situation-complication-resolution',
        'conversational': 'hook-thesis-body-callback-cta',
        'inspirational': 'heros-journey',
        'provocative': 'hook-thesis-body-callback-cta',
        'storytelling': 'story-point-application',
    }

    # Duration adjustments
    if duration >= 45 and tone == 'inspirational':
        return 'duarte-sparkline'
    if duration >= 45 and tone == 'storytelling':
        return 'heros-journey'
    if duration == 20 and len(takeaways) <= 3:
        return 'kawasaki-10-20-30'

    # Data-heavy talks with data_sources
    data_sources = brief.get('data_sources', [])
    if len(data_sources) >= 3:
        return 'what-so-what-now-what'

    return arc_by_tone.get(tone, 'problem-solution-impact')


def calculate_slide_count(duration_minutes, style='image-rich', slide_count_hint=None):
    """Calculate target slide count based on duration and style.

    Args:
        duration_minutes: Talk duration in minutes.
        style: Presentation style from TalkBrief.preferences.style.
        slide_count_hint: Optional user-provided slide count preference.

    Returns:
        Integer target slide count.
    """
    density = STYLE_DENSITY.get(style, 0.8)
    base_count = round(duration_minutes * density)

    # Enforce minimum and maximum bounds
    base_count = max(base_count, 5)
    base_count = min(base_count, 60)

    # If user provided a hint, bias toward it (within ±30%)
    if slide_count_hint:
        lower = round(slide_count_hint * 0.7)
        upper = round(slide_count_hint * 1.3)
        base_count = max(lower, min(base_count, upper))
        base_count = max(base_count, 5)

    return base_count


def generate_slide_sequence(brief, arc, slide_count):
    """Generate an ordered sequence of slide definitions for the given arc.

    Produces a list of slide dictionaries with slide_number, slide_type,
    headline, body_points, narrative_beat, visual_direction, visual_type,
    layout_template, and transition_note.

    Args:
        brief: TalkBrief dictionary.
        arc: Narrative arc identifier.
        slide_count: Target number of slides.

    Returns:
        List of slide dictionaries.
    """
    template = ARC_TEMPLATES.get(arc)
    if not template:
        template = ARC_TEMPLATES['problem-solution-impact']

    topic = brief.get('topic', 'Untitled Talk')
    audience = brief.get('audience', 'General audience')
    takeaways = brief.get('key_takeaways', [])
    data_sources = brief.get('data_sources', [])

    slides = []
    slide_number = 1
    remaining = slide_count
    data_source_index = 0

    for beat_index, (beat_name, fraction, suggested_types) in enumerate(template):
        # Calculate how many slides for this beat
        if beat_index == len(template) - 1:
            # Last beat gets all remaining slides
            beat_slides = max(remaining, 1)
        else:
            beat_slides = max(round(slide_count * fraction), 1)
            beat_slides = min(beat_slides, remaining)

        for i in range(beat_slides):
            slide = {
                'slide_number': slide_number,
                'narrative_beat': beat_name,
            }

            # Determine slide type
            if slide_number == 1:
                slide['slide_type'] = 'title'
                slide['headline'] = topic
                slide['body_points'] = []
                slide['visual_direction'] = (
                    f"Abstract visual representing the theme of "
                    f"'{topic}', suitable for a title slide background"
                )
                slide['visual_type'] = 'hero_image'
                slide['layout_template'] = 'title'
            elif remaining <= 1 or (beat_index == len(template) - 1 and i == beat_slides - 1):
                slide['slide_type'] = 'closing'
                slide['headline'] = _generate_closing_headline(takeaways)
                slide['body_points'] = takeaways[:3] if takeaways else []
                slide['visual_type'] = 'none'
                slide['layout_template'] = 'closing'
            else:
                # Check if we should insert a section divider
                if i == 0 and beat_index > 0 and slide_number > 2:
                    # Insert section divider at beat transitions
                    slide['slide_type'] = 'section_divider'
                    slide['headline'] = _beat_to_section_heading(beat_name)
                    slide['visual_type'] = 'pattern_background'
                    slide['layout_template'] = 'section_divider'
                    slide['body_points'] = []
                else:
                    # Select from suggested types, avoiding consecutive data_charts
                    prev_type = slides[-1]['slide_type'] if slides else None
                    available_types = list(suggested_types)
                    if prev_type == 'data_chart':
                        available_types = [
                            t for t in available_types if t != 'data_chart'
                        ]
                    if not available_types:
                        available_types = ['content']

                    # Use data_chart if we have data sources to place
                    if (data_sources and data_source_index < len(data_sources)
                            and 'data_chart' in suggested_types
                            and prev_type != 'data_chart'):
                        slide['slide_type'] = 'data_chart'
                        ds = data_sources[data_source_index]
                        slide['headline'] = _data_source_headline(ds)
                        slide['data'] = {
                            'chart_type': 'bar',
                            'data_source_label': ds['label'],
                        }
                        slide['visual_type'] = 'chart'
                        data_source_index += 1
                    else:
                        # Cycle through available types for variety
                        type_index = (slide_number - 1) % len(available_types)
                        slide['slide_type'] = available_types[type_index]

                    # Generate headline and content for non-special slides
                    if 'headline' not in slide:
                        slide['headline'] = _generate_headline(
                            topic, beat_name, slide_number
                        )
                    if 'body_points' not in slide:
                        slide['body_points'] = _generate_body_points(
                            topic, beat_name, takeaways, slide_number
                        )

                    # Set visual direction and type for visual slides
                    if 'visual_direction' not in slide:
                        slide['visual_direction'] = _generate_visual_direction(
                            slide['slide_type'], slide.get('headline', ''),
                            topic
                        )
                    if 'visual_type' not in slide:
                        slide['visual_type'] = _slide_type_to_visual_type(
                            slide['slide_type']
                        )

                    # Set layout template
                    if 'layout_template' not in slide:
                        slide['layout_template'] = slide['slide_type']

            # Add transition note (except for first slide)
            if slide_number > 1 and 'transition_note' not in slide:
                slide['transition_note'] = _generate_transition_note(
                    beat_name, slides[-1] if slides else None
                )

            slides.append(slide)
            slide_number += 1
            remaining -= 1

            if remaining <= 0:
                break

        if remaining <= 0:
            break

    # Ensure last slide is closing
    if slides and slides[-1]['slide_type'] != 'closing':
        slides[-1]['slide_type'] = 'closing'
        slides[-1]['headline'] = _generate_closing_headline(takeaways)
        slides[-1]['layout_template'] = 'closing'
        slides[-1]['visual_type'] = 'none'

    return slides


def build_outline(brief, style_guide):
    """Build a complete SlideOutline from TalkBrief and StyleGuide.

    This is the main entry point for the narrative-architect.

    Args:
        brief: TalkBrief dictionary (validated).
        style_guide: StyleGuide dictionary (validated).

    Returns:
        SlideOutline dictionary conforming to slide_outline.schema.json.
    """
    arc = select_narrative_arc(brief)
    style = brief.get('preferences', {}).get('style', 'image-rich')
    hint = brief.get('preferences', {}).get('slide_count_hint')
    slide_count = calculate_slide_count(
        brief['duration_minutes'], style=style, slide_count_hint=hint
    )

    slides = generate_slide_sequence(brief, arc, slide_count)

    return {
        'narrative_arc': arc,
        'estimated_duration_minutes': brief['duration_minutes'],
        'total_slides': len(slides),
        'slides': slides,
    }


# --- Private helpers ---

def _generate_headline(topic, beat_name, slide_number):
    """Generate a placeholder headline for a slide."""
    beat_labels = {
        'hook': 'Setting the Stage',
        'situation': 'The Current Landscape',
        'complication': 'The Challenge',
        'resolution': 'The Path Forward',
        'problem': 'The Problem We Face',
        'solution': 'Our Approach',
        'impact': 'The Results',
        'demo': 'See It in Action',
        'attention': 'Consider This',
        'need': 'Why This Matters',
        'satisfaction': 'How We Solve It',
        'visualization': 'Imagine the Possibilities',
        'action': 'Your Next Step',
        'thesis': 'The Key Insight',
        'cta': 'What You Can Do Today',
        'callback': 'Remember Where We Started',
        'ordinary-world': 'Where We Were',
        'challenge': 'The Turning Point',
        'journey': 'The Road Less Traveled',
        'transformation': 'The Breakthrough',
        'new-world': 'The New Reality',
        'close': 'In Summary',
    }
    # Use beat label or derive from beat name
    for key, label in beat_labels.items():
        if key in beat_name:
            return label
    return f"Slide {slide_number}"


def _generate_closing_headline(takeaways):
    """Generate a closing slide headline."""
    if takeaways:
        return "Key Takeaways"
    return "Thank You"


def _generate_body_points(topic, beat_name, takeaways, slide_number):
    """Generate placeholder body points."""
    # Return empty for types that typically don't have body points
    return []


def _generate_visual_direction(slide_type, headline, topic):
    """Generate a visual direction description for image generation."""
    type_directions = {
        'title': f"Abstract visual representing '{topic}', dramatic composition with space for text overlay",
        'section_divider': f"Minimalist background pattern with subtle texture, space for section heading",
        'content': f"Clean illustration related to '{headline}', professional style with negative space for text",
        'two_column': f"Split composition showing contrast or comparison related to '{headline}'",
        'image_feature': f"High-impact full-bleed photograph or illustration about '{headline}'",
        'data_chart': f"Clean background with subtle grid pattern, space for chart overlay",
        'stat_callout': f"Bold, minimal background with strong focal point for statistic display",
        'quote': f"Atmospheric background with bokeh or texture, space for quote text overlay",
        'icon_grid': f"Clean background for icon placement, consistent with presentation theme",
        'diagram': f"Technical diagram illustrating '{headline}', clear labels and flow",
        'closing': f"Subtle background echoing the title slide theme, space for summary text",
        'blank_visual': f"Striking full-bleed visual related to '{topic}', no text needed",
    }
    return type_directions.get(slide_type, f"Visual related to '{headline}'")


def _slide_type_to_visual_type(slide_type):
    """Map a slide type to its default visual type."""
    type_map = {
        'title': 'hero_image',
        'section_divider': 'pattern_background',
        'content': 'hero_image',
        'two_column': 'hero_image',
        'image_feature': 'hero_image',
        'data_chart': 'chart',
        'stat_callout': 'pattern_background',
        'quote': 'pattern_background',
        'icon_grid': 'icon_set',
        'diagram': 'diagram',
        'closing': 'none',
        'blank_visual': 'hero_image',
    }
    return type_map.get(slide_type, 'none')


def _data_source_headline(data_source):
    """Generate a headline from a data source."""
    label = data_source.get('label', 'Data')
    return label.replace('_', ' ').title()


def _beat_to_section_heading(beat_name):
    """Convert a beat name to a readable section heading."""
    # Clean up beat names
    heading = beat_name.replace('-', ' ').replace('_', ' ')
    # Remove numeric suffixes (e.g., 'evidence-1' -> 'evidence')
    parts = heading.split()
    clean_parts = [p for p in parts if not p.isdigit()]
    return ' '.join(clean_parts).title()


def _generate_transition_note(current_beat, prev_slide):
    """Generate a transition note from previous slide to current."""
    if not prev_slide:
        return ''
    prev_headline = prev_slide.get('headline', '')
    return f"Building on what we just discussed about '{prev_headline}'..."
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_narrative_architect.py -v`

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/narrative_architect.py tests/test_narrative_architect.py
git commit -m "feat: add narrative-architect outline generation module with TDD"
```

---

## Task 4: narrative-architect — SKILL.md

**Files:**
- Create: `.claude/skills/narrative-architect/SKILL.md`

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p .claude/skills/narrative-architect
```

- [ ] **Step 2: Create the SKILL.md file**

Create `.claude/skills/narrative-architect/SKILL.md`:

```markdown
---
name: narrative-architect
description: Generate a structured SlideOutline from a TalkBrief and StyleGuide. Selects the optimal narrative arc, calculates slide density, and produces an ordered slide sequence with per-slide type, headline, body points, narrative beat, visual direction, and layout template. Output is written to DeckContext as outline.json.
argument-hint: [--deck-dir PATH]
allowed-tools: Bash(python *), Read, Write, Glob
---

# /narrative-architect

Generate a SlideOutline from a TalkBrief and StyleGuide. This skill is part of the Content Services domain (L1) and is invoked after the `slide-stylist` has produced a StyleGuide.

## Prerequisites

Before running, verify that these DeckContext files exist:
- `./tmp/deck/talk-brief.json` (produced by Deck Conductor)
- `./tmp/deck/style-guide.json` (produced by slide-stylist)

If either file is missing, STOP and report the error. Do not attempt to generate an outline without both inputs.

## Parse Arguments

Parse `$ARGUMENTS` for:
- **--deck-dir PATH**: DeckContext directory (default: `./tmp/deck`)

## Step 1: Read Inputs from DeckContext

```bash
python3 -c "
import json, sys
sys.path.insert(0, '.')
from src.deckcontext import read_contract

deck_dir = '${DECK_DIR:-./tmp/deck}'
brief = read_contract(deck_dir, 'talk-brief')
guide = read_contract(deck_dir, 'style-guide')

if brief is None:
    print('ERROR: talk-brief.json not found in DeckContext')
    sys.exit(1)
if guide is None:
    print('ERROR: style-guide.json not found in DeckContext')
    sys.exit(1)

print(json.dumps({'topic': brief['topic'], 'duration': brief['duration_minutes'], 'tone': brief.get('tone', 'professional')}, indent=2))
"
```

## Step 2: Generate the SlideOutline

Run the narrative-architect core logic to build the outline:

```bash
python3 -c "
import json, sys
sys.path.insert(0, '.')
from src.deckcontext import read_contract, write_contract, update_step
from src.narrative_architect import build_outline

deck_dir = '${DECK_DIR:-./tmp/deck}'

# Mark step as running
update_step(deck_dir, 'narrative-architect', 'running')

# Read inputs
brief = read_contract(deck_dir, 'talk-brief')
style_guide = read_contract(deck_dir, 'style-guide')

# Build outline
outline = build_outline(brief, style_guide)

# Write to DeckContext (validates against schema)
write_contract(deck_dir, 'outline', outline)

# Mark step as completed
update_step(deck_dir, 'narrative-architect', 'completed', output_file='outline.json')

print(f'SlideOutline generated: {outline[\"total_slides\"]} slides, arc: {outline[\"narrative_arc\"]}')
print(f'Written to {deck_dir}/outline.json')
"
```

## Step 3: Review and Refine the Outline

After generating the initial outline, review it with your knowledge of conference presentation best practices. The `build_outline` function produces a structural skeleton — you should now **enhance** it:

1. **Read the generated outline.json** using the Read tool
2. **Refine headlines** — replace generic placeholders with punchy, conference-quality headlines that match the topic and audience
3. **Refine body_points** — add 2-4 specific, relevant bullet points per content slide
4. **Refine visual_direction** — write specific, evocative descriptions that will produce good image generation prompts
5. **Verify narrative flow** — ensure transitions are smooth and the story arc is compelling
6. **Check sequencing rules**:
   - No two consecutive data_chart slides
   - Section dividers at major topic shifts
   - Opening: title → hook → content
   - Closing: recap → CTA → resources
7. **Add transition_notes** where missing — specific verbal bridges between slides

Write the refined outline back:

```bash
python3 -c "
import json, sys
sys.path.insert(0, '.')
from src.deckcontext import write_contract

deck_dir = '${DECK_DIR:-./tmp/deck}'
with open(f'{deck_dir}/outline.json') as f:
    outline = json.load(f)

# The refined outline has been loaded; write it back with validation
write_contract(deck_dir, 'outline', outline)
print('Refined outline written successfully')
"
```

## Step 4: Report

Report to the user:
- Narrative arc selected and why
- Total slide count
- Slide type distribution (how many of each type)
- Duration estimate
- Any notable decisions (e.g., "included 2 data_chart slides for your data sources")

## Key Design Decisions

### Narrative Arc Selection
The arc is auto-selected based on tone, duration, audience, and data sources:
- **technical** → problem-solution-impact
- **inspirational** (45+ min) → duarte-sparkline
- **storytelling** → story-point-application
- **conversational** → hook-thesis-body-callback-cta
- **5-min talks** → lightning-talk
- **3+ data sources** → what-so-what-now-what

### The 12 Slide Types
| Type | When to Use |
|------|-------------|
| `title` | First slide only |
| `section_divider` | Before major topic shifts |
| `content` | Standard text + optional image |
| `two_column` | Comparisons, before/after |
| `image_feature` | Full or half-bleed hero image |
| `data_chart` | Data visualisation (never consecutive) |
| `stat_callout` | Single bold statistic |
| `quote` | Expert or testimonial quote |
| `icon_grid` | 3-4 concept icons |
| `diagram` | Technical or process diagram |
| `closing` | Last slide only |
| `blank_visual` | Full-bleed image, no text |

### Slide Density by Style
| Style | Slides/Minute | 30-min Talk |
|-------|---------------|-------------|
| minimalist | 0.8 | ~24 slides |
| data-heavy | 0.6 | ~18 slides |
| image-rich | 1.0 | ~30 slides |
| diagram-heavy | 0.7 | ~21 slides |
| corporate | 0.7 | ~21 slides |
| creative | 1.2 | ~36 slides |
```

- [ ] **Step 3: Verify the skill is discoverable**

```bash
ls -la .claude/skills/narrative-architect/SKILL.md
```

Expected: File exists with correct permissions.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/narrative-architect/SKILL.md
git commit -m "feat: add narrative-architect Claude Code skill (SKILL.md)"
```

---

## Task 5: Research Synthesis — speaker-notes-writer

**Files:**
- Create: `research/synthesis-speaker-notes-writer.md`

- [ ] **Step 1: Create the speaker-notes-writer research synthesis**

Create `research/synthesis-speaker-notes-writer.md`:

```markdown
# speaker-notes-writer — Research Synthesis

## Decision Summary
- Pacing model: ~130 WPM default, adjustable per tone (100-120 for slow/technical, 160-170 for fast/motivational) — Source: #08 §6.1
- Timing markers: Cumulative format ~MM:SS at each slide — Source: #08 §6.2
- Transition cues: Explicit verbal bridges embedded in notes — Source: #08 §6.3
- Architecture pattern: Pure function — reads TalkBrief + SlideOutline from DeckContext, writes SpeakerNotes to DeckContext
- Key constraint: Total notes word count / WPM must not exceed duration_minutes

## Requirements (from research)
1. Word count calibration: ~130-150 words per minute at standard pace — Source: #08 §6.1
2. Per-slide word budget: 1-min slide ~130 words, 2-min slide ~260 words, 30-sec visual accent ~65 words — Source: #08 §6.1
3. Timing markers as cumulative time marks (e.g., ~5:30) on every slide — Source: #08 §6.2
4. Transition cues: explicit verbal bridge to the next slide — Source: #08 §6.3
5. Audience interaction prompts embedded at appropriate points — Source: #08 §6.4
6. Key emphasis markers for vocal inflection — Source: #08 §6.5
7. 6 cue types: transition, pause, audience_interaction, emphasis, demo, build_animation — Source: data-contracts §5
8. Total estimated minutes must match TalkBrief.duration_minutes ± 10% — Source: #08 §6.1
9. Notes anti-patterns: no full scripts, include timing markers, include transition cues — Source: #08 §6.7
10. Pacing adjustment for audience: non-native → slower (100-120 WPM), technical → standard (130 WPM), motivational → faster (160 WPM) — Source: #08 §6.1

## Design Rules (machine-checkable where possible)
- Rule 1: Every slide in the outline must have a corresponding note — Check: len(notes) == len(outline.slides)
- Rule 2: slide_number in each note matches a slide in the outline — Check: all note.slide_number in [s.slide_number for s in outline.slides]
- Rule 3: Total word count / target_pace_wpm <= duration_minutes — Check: sum(word_count(n.text)) / target_pace_wpm <= brief.duration_minutes * 1.1
- Rule 4: Every note has non-empty text — Check: all(len(n.text) > 0 for n in notes)
- Rule 5: timing_marker is present on every note — Check: all('timing_marker' in n for n in notes)
- Rule 6: timing_markers are monotonically increasing — Check: parsed times increase sequentially
- Rule 7: At least one 'transition' cue per beat transition — Check: beat transitions have transition cues
- Rule 8: Title slide has a 'pause' cue — Check: notes[0].cues contains type=='pause'

## Pacing Reference Table
| Speaking Pace | Words/Minute | Use Case |
|---------------|-------------|----------|
| Slow | 100-120 WPM | Complex technical content, non-native audience |
| Standard | 130-150 WPM | General presentations, conference talks |
| Fast | 160-170 WPM | Motivational speeches, lively narratives |

## Cue Types Reference
| Cue Type | When to Use |
|----------|-------------|
| `transition` | Verbal bridge to next slide |
| `pause` | After key points, after data, let audience absorb |
| `audience_interaction` | Show of hands, polls, questions |
| `emphasis` | Vocal stress on key words or statistics |
| `demo` | Switch to live demo window |
| `build_animation` | Click to advance animation build |

## Open Questions
- Should speaker notes be keyword-style or full-sentence style?
  Decision: Keyword-phrase style with full-sentence opening per slide. Anti-pattern: full scripts.

## Sources
- #08: Narrative Arc & Conference Storytelling Patterns (primary — §6 Speaker Notes Intelligence)
- #07: Conference Presentation QA Heuristics (secondary — missing notes = QA finding)
- data-contracts.md: SpeakerNotes schema specification
```

- [ ] **Step 2: Commit**

```bash
git add research/synthesis-speaker-notes-writer.md
git commit -m "docs: add speaker-notes-writer research synthesis"
```

---

## Task 6: speaker-notes-writer — Core Logic Module

**Files:**
- Create: `src/speaker_notes_writer.py`
- Create: `tests/test_speaker_notes_writer.py`

- [ ] **Step 1: Write unit tests for the speaker-notes-writer**

Create `tests/test_speaker_notes_writer.py`:

```python
"""Tests for speaker-notes-writer generation logic."""

import json
import os
import pytest
from jsonschema import validate

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'schemas')
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def load_schema(name):
    path = os.path.join(SCHEMA_DIR, f'{name}.schema.json')
    with open(path) as f:
        return json.load(f)


def load_fixture(name):
    path = os.path.join(FIXTURE_DIR, f'{name}.json')
    with open(path) as f:
        return json.load(f)


class TestSelectPace:
    def test_technical_tone_uses_standard_pace(self):
        from src.speaker_notes_writer import select_pace_wpm
        pace = select_pace_wpm(tone='technical', audience='Senior engineers')
        assert 120 <= pace <= 140

    def test_inspirational_tone_uses_faster_pace(self):
        from src.speaker_notes_writer import select_pace_wpm
        pace = select_pace_wpm(tone='inspirational', audience='General audience')
        assert 140 <= pace <= 170

    def test_conversational_tone_uses_standard_pace(self):
        from src.speaker_notes_writer import select_pace_wpm
        pace = select_pace_wpm(tone='conversational', audience='Developers')
        assert 125 <= pace <= 150

    def test_default_is_130_wpm(self):
        from src.speaker_notes_writer import select_pace_wpm
        pace = select_pace_wpm()
        assert pace == 130


class TestCalculateSlideSeconds:
    def test_even_distribution(self):
        from src.speaker_notes_writer import calculate_slide_seconds
        outline = load_fixture('valid_slide_outline')
        total_minutes = 30
        seconds = calculate_slide_seconds(outline['slides'], total_minutes)
        # Each slide gets some time
        assert all(s > 0 for s in seconds)
        # Total is within range
        total = sum(seconds)
        assert abs(total - total_minutes * 60) <= total_minutes * 60 * 0.15

    def test_title_slide_gets_less_time(self):
        from src.speaker_notes_writer import calculate_slide_seconds
        outline = load_fixture('valid_slide_outline')
        total_minutes = 30
        seconds = calculate_slide_seconds(outline['slides'], total_minutes)
        # Title slide should get less time than content slides
        # (assuming index 0 is title and index 1 is content)
        if len(seconds) > 1:
            assert seconds[0] <= seconds[1] * 1.5  # title not excessively long

    def test_section_dividers_get_minimal_time(self):
        from src.speaker_notes_writer import calculate_slide_seconds
        slides = [
            {'slide_number': 1, 'slide_type': 'title', 'headline': 'Test'},
            {'slide_number': 2, 'slide_type': 'content', 'headline': 'Content'},
            {'slide_number': 3, 'slide_type': 'section_divider', 'headline': 'Section'},
            {'slide_number': 4, 'slide_type': 'content', 'headline': 'More'},
            {'slide_number': 5, 'slide_type': 'closing', 'headline': 'End'},
        ]
        seconds = calculate_slide_seconds(slides, 10)
        # Section divider should get less time than content
        assert seconds[2] < seconds[1]


class TestGenerateTimingMarkers:
    def test_first_marker_is_zero(self):
        from src.speaker_notes_writer import generate_timing_markers
        seconds_per_slide = [20, 60, 90, 30]
        markers = generate_timing_markers(seconds_per_slide)
        assert markers[0] == '~0:00'

    def test_markers_are_cumulative(self):
        from src.speaker_notes_writer import generate_timing_markers
        seconds_per_slide = [20, 60, 90, 30]
        markers = generate_timing_markers(seconds_per_slide)
        assert markers[1] == '~0:20'
        assert markers[2] == '~1:20'
        assert markers[3] == '~2:50'

    def test_markers_format_minutes_correctly(self):
        from src.speaker_notes_writer import generate_timing_markers
        seconds_per_slide = [300, 300, 300]  # 5 min each
        markers = generate_timing_markers(seconds_per_slide)
        assert markers[0] == '~0:00'
        assert markers[1] == '~5:00'
        assert markers[2] == '~10:00'


class TestGenerateCues:
    def test_title_slide_gets_pause_cue(self):
        from src.speaker_notes_writer import generate_cues
        slide = {'slide_number': 1, 'slide_type': 'title', 'headline': 'Test'}
        prev_slide = None
        cues = generate_cues(slide, prev_slide, is_beat_transition=False)
        assert any(c['type'] == 'pause' for c in cues)

    def test_beat_transition_gets_transition_cue(self):
        from src.speaker_notes_writer import generate_cues
        slide = {'slide_number': 5, 'slide_type': 'content', 'headline': 'New Topic'}
        prev_slide = {'slide_number': 4, 'slide_type': 'content', 'headline': 'Old'}
        cues = generate_cues(slide, prev_slide, is_beat_transition=True)
        assert any(c['type'] == 'transition' for c in cues)

    def test_data_chart_gets_pause_cue(self):
        from src.speaker_notes_writer import generate_cues
        slide = {'slide_number': 3, 'slide_type': 'data_chart', 'headline': 'Data'}
        prev_slide = {'slide_number': 2, 'slide_type': 'content', 'headline': 'Context'}
        cues = generate_cues(slide, prev_slide, is_beat_transition=False)
        assert any(c['type'] == 'pause' for c in cues)

    def test_cue_types_are_valid(self):
        from src.speaker_notes_writer import generate_cues
        valid_types = {
            'transition', 'pause', 'audience_interaction',
            'emphasis', 'demo', 'build_animation',
        }
        slide = {'slide_number': 3, 'slide_type': 'content', 'headline': 'Test'}
        cues = generate_cues(slide, None, is_beat_transition=True)
        for cue in cues:
            assert cue['type'] in valid_types


class TestBuildSpeakerNotes:
    def test_builds_valid_notes_from_brief_and_outline(self):
        from src.speaker_notes_writer import build_speaker_notes
        brief = load_fixture('valid_talk_brief')
        outline = load_fixture('valid_slide_outline')
        notes = build_speaker_notes(brief, outline)
        schema = load_schema('speaker_notes')
        validate(instance=notes, schema=schema)

    def test_one_note_per_slide(self):
        from src.speaker_notes_writer import build_speaker_notes
        brief = load_fixture('valid_talk_brief')
        outline = load_fixture('valid_slide_outline')
        notes = build_speaker_notes(brief, outline)
        assert len(notes['notes']) == len(outline['slides'])

    def test_slide_numbers_match_outline(self):
        from src.speaker_notes_writer import build_speaker_notes
        brief = load_fixture('valid_talk_brief')
        outline = load_fixture('valid_slide_outline')
        notes = build_speaker_notes(brief, outline)
        outline_numbers = {s['slide_number'] for s in outline['slides']}
        note_numbers = {n['slide_number'] for n in notes['notes']}
        assert outline_numbers == note_numbers

    def test_all_notes_have_text(self):
        from src.speaker_notes_writer import build_speaker_notes
        brief = load_fixture('valid_talk_brief')
        outline = load_fixture('valid_slide_outline')
        notes = build_speaker_notes(brief, outline)
        for note in notes['notes']:
            assert len(note['text']) > 0

    def test_all_notes_have_timing_marker(self):
        from src.speaker_notes_writer import build_speaker_notes
        brief = load_fixture('valid_talk_brief')
        outline = load_fixture('valid_slide_outline')
        notes = build_speaker_notes(brief, outline)
        for note in notes['notes']:
            assert 'timing_marker' in note
            assert note['timing_marker'].startswith('~')

    def test_all_notes_have_estimated_seconds(self):
        from src.speaker_notes_writer import build_speaker_notes
        brief = load_fixture('valid_talk_brief')
        outline = load_fixture('valid_slide_outline')
        notes = build_speaker_notes(brief, outline)
        for note in notes['notes']:
            assert 'estimated_seconds' in note
            assert note['estimated_seconds'] > 0

    def test_total_time_within_duration(self):
        from src.speaker_notes_writer import build_speaker_notes
        brief = load_fixture('valid_talk_brief')
        outline = load_fixture('valid_slide_outline')
        notes = build_speaker_notes(brief, outline)
        total_seconds = sum(n['estimated_seconds'] for n in notes['notes'])
        total_minutes = total_seconds / 60
        target = brief['duration_minutes']
        # Within ±15% of target duration
        assert total_minutes <= target * 1.15
        assert total_minutes >= target * 0.5  # at least half (for very short fixture outlines)

    def test_timing_markers_increase(self):
        from src.speaker_notes_writer import build_speaker_notes
        brief = load_fixture('valid_talk_brief')
        outline = load_fixture('valid_slide_outline')
        notes = build_speaker_notes(brief, outline)
        # Parse timing markers and verify they increase
        prev_seconds = -1
        for note in notes['notes']:
            marker = note['timing_marker']  # format: ~M:SS or ~MM:SS
            parts = marker.lstrip('~').split(':')
            total = int(parts[0]) * 60 + int(parts[1])
            assert total >= prev_seconds
            prev_seconds = total

    def test_target_pace_wpm_is_set(self):
        from src.speaker_notes_writer import build_speaker_notes
        brief = load_fixture('valid_talk_brief')
        outline = load_fixture('valid_slide_outline')
        notes = build_speaker_notes(brief, outline)
        assert 'target_pace_wpm' in notes
        assert 100 <= notes['target_pace_wpm'] <= 170

    def test_total_estimated_minutes_is_set(self):
        from src.speaker_notes_writer import build_speaker_notes
        brief = load_fixture('valid_talk_brief')
        outline = load_fixture('valid_slide_outline')
        notes = build_speaker_notes(brief, outline)
        assert 'total_estimated_minutes' in notes
        assert notes['total_estimated_minutes'] > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_speaker_notes_writer.py -v`

Expected: FAIL — `src.speaker_notes_writer` module not found.

- [ ] **Step 3: Implement the speaker-notes-writer module**

Create `src/speaker_notes_writer.py`:

```python
"""speaker-notes-writer — Generate timed SpeakerNotes from TalkBrief + SlideOutline.

Produces per-slide notes with timing markers, estimated seconds,
pacing calibrated to duration_minutes, and interaction cues
(transitions, pauses, audience interactions, emphasis, demos).

This module provides the core logic. The SKILL.md file in
.claude/skills/speaker-notes-writer/ drives orchestration via Claude Code.
"""

# Time weight multipliers by slide type.
# Higher weight = more speaking time allocated.
SLIDE_TIME_WEIGHTS = {
    'title': 0.5,
    'section_divider': 0.3,
    'content': 1.0,
    'two_column': 1.2,
    'image_feature': 0.7,
    'data_chart': 1.3,
    'stat_callout': 0.6,
    'quote': 0.5,
    'icon_grid': 0.8,
    'diagram': 1.2,
    'closing': 0.8,
    'blank_visual': 0.4,
}


def select_pace_wpm(tone=None, audience=None):
    """Select speaking pace in words per minute based on tone and audience.

    Args:
        tone: Presentation tone from TalkBrief.
        audience: Audience description from TalkBrief.

    Returns:
        Integer words per minute.
    """
    if tone is None:
        return 130

    pace_by_tone = {
        'technical': 130,
        'professional': 130,
        'conversational': 140,
        'inspirational': 150,
        'provocative': 140,
        'storytelling': 135,
    }

    base = pace_by_tone.get(tone, 130)

    # Adjust for audience if keywords suggest non-native speakers
    if audience:
        audience_lower = audience.lower()
        if any(term in audience_lower for term in ['non-native', 'international', 'global']):
            base = min(base, 120)

    return base


def calculate_slide_seconds(slides, total_minutes):
    """Calculate estimated speaking seconds per slide.

    Uses slide type weights to distribute time proportionally.
    Title and section_divider slides get less time; content and
    data_chart slides get more.

    Args:
        slides: List of slide dictionaries from SlideOutline.
        total_minutes: Target total duration in minutes.

    Returns:
        List of integers — estimated seconds per slide.
    """
    total_seconds = total_minutes * 60

    # Calculate weights
    weights = []
    for slide in slides:
        slide_type = slide.get('slide_type', 'content')
        weight = SLIDE_TIME_WEIGHTS.get(slide_type, 1.0)
        weights.append(weight)

    total_weight = sum(weights)
    if total_weight == 0:
        total_weight = len(slides)

    # Distribute time proportionally
    seconds = []
    allocated = 0
    for i, weight in enumerate(weights):
        if i == len(weights) - 1:
            # Last slide gets remaining time
            slide_seconds = total_seconds - allocated
        else:
            slide_seconds = round((weight / total_weight) * total_seconds)
        slide_seconds = max(slide_seconds, 10)  # minimum 10 seconds per slide
        seconds.append(slide_seconds)
        allocated += slide_seconds

    return seconds


def generate_timing_markers(seconds_per_slide):
    """Generate cumulative timing markers for each slide.

    Args:
        seconds_per_slide: List of integers — seconds allocated per slide.

    Returns:
        List of strings in format '~M:SS' or '~MM:SS'.
    """
    markers = []
    cumulative = 0
    for seconds in seconds_per_slide:
        minutes = cumulative // 60
        secs = cumulative % 60
        markers.append(f'~{minutes}:{secs:02d}')
        cumulative += seconds
    return markers


def generate_cues(slide, prev_slide, is_beat_transition):
    """Generate interaction cues for a slide.

    Args:
        slide: Current slide dictionary.
        prev_slide: Previous slide dictionary (or None for first slide).
        is_beat_transition: Whether the narrative beat changes at this slide.

    Returns:
        List of cue dictionaries with 'type' and 'text'.
    """
    cues = []
    slide_type = slide.get('slide_type', 'content')

    # Title slide always gets a pause
    if slide_type == 'title' or slide.get('slide_number') == 1:
        cues.append({
            'type': 'pause',
            'text': 'Let the title slide breathe for 3 seconds before speaking',
        })

    # Beat transitions get transition cues
    if is_beat_transition and prev_slide:
        cues.append({
            'type': 'transition',
            'text': (
                f"Transition from '{prev_slide.get('headline', 'previous topic')}' "
                f"to this new section"
            ),
        })

    # Data charts and stat callouts get pause cues
    if slide_type in ('data_chart', 'stat_callout'):
        cues.append({
            'type': 'pause',
            'text': 'Let the audience absorb the data — count to 3 silently',
        })

    # Section dividers get pause cues
    if slide_type == 'section_divider':
        cues.append({
            'type': 'pause',
            'text': 'Pause to signal the topic shift. Move position on stage if possible.',
        })

    # Diagram slides might need emphasis
    if slide_type == 'diagram':
        cues.append({
            'type': 'emphasis',
            'text': 'Walk through the diagram step by step',
        })

    # Closing slide
    if slide_type == 'closing':
        cues.append({
            'type': 'emphasis',
            'text': 'Slow down for the final takeaway — this is what they will remember',
        })

    return cues


def _generate_note_text(slide, pace_wpm, seconds):
    """Generate placeholder speaker notes text for a slide.

    Produces keyword-phrase style notes, not full scripts.

    Args:
        slide: Slide dictionary.
        pace_wpm: Target speaking pace.
        seconds: Allocated seconds for this slide.

    Returns:
        String with speaker notes text.
    """
    slide_type = slide.get('slide_type', 'content')
    headline = slide.get('headline', '')
    body_points = slide.get('body_points', [])
    transition = slide.get('transition_note', '')

    parts = []

    # Opening sentence
    if slide_type == 'title':
        parts.append(
            f"Welcome the audience. Introduce the talk: '{headline}'."
        )
    elif slide_type == 'section_divider':
        parts.append(f"Signal the transition to: '{headline}'.")
    elif slide_type == 'closing':
        parts.append(f"Summarise the key takeaways.")
    else:
        if transition:
            parts.append(transition)
        parts.append(f"Key point: {headline}")

    # Body point coverage
    if body_points:
        for point in body_points[:4]:
            parts.append(f"- {point}")

    # Data chart specific
    if slide_type == 'data_chart':
        data = slide.get('data', {})
        label = data.get('data_source_label', 'the data')
        parts.append(f"Walk through {label} — explain what the audience should take away.")

    return ' '.join(parts)


def build_speaker_notes(brief, outline):
    """Build complete SpeakerNotes from TalkBrief and SlideOutline.

    This is the main entry point for the speaker-notes-writer.

    Args:
        brief: TalkBrief dictionary (validated).
        outline: SlideOutline dictionary (validated).

    Returns:
        SpeakerNotes dictionary conforming to speaker_notes.schema.json.
    """
    tone = brief.get('tone', 'professional')
    audience = brief.get('audience', '')
    duration = brief.get('duration_minutes', 30)
    slides = outline.get('slides', [])

    # Select pace
    pace_wpm = select_pace_wpm(tone=tone, audience=audience)

    # Calculate time distribution
    seconds_per_slide = calculate_slide_seconds(slides, duration)

    # Generate timing markers
    timing_markers = generate_timing_markers(seconds_per_slide)

    # Build notes array
    notes = []
    for i, slide in enumerate(slides):
        prev_slide = slides[i - 1] if i > 0 else None

        # Detect beat transitions
        is_beat_transition = False
        if prev_slide:
            prev_beat = prev_slide.get('narrative_beat', '')
            curr_beat = slide.get('narrative_beat', '')
            if prev_beat and curr_beat and prev_beat != curr_beat:
                is_beat_transition = True

        # Generate cues
        cues = generate_cues(slide, prev_slide, is_beat_transition)

        # Generate note text
        text = _generate_note_text(slide, pace_wpm, seconds_per_slide[i])

        note = {
            'slide_number': slide['slide_number'],
            'text': text,
            'estimated_seconds': seconds_per_slide[i],
            'timing_marker': timing_markers[i],
        }
        if cues:
            note['cues'] = cues

        notes.append(note)

    # Calculate total estimated minutes
    total_seconds = sum(seconds_per_slide)
    total_minutes = round(total_seconds / 60, 1)

    return {
        'target_pace_wpm': pace_wpm,
        'total_estimated_minutes': total_minutes,
        'notes': notes,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_speaker_notes_writer.py -v`

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/speaker_notes_writer.py tests/test_speaker_notes_writer.py
git commit -m "feat: add speaker-notes-writer module with timed notes generation"
```

---

## Task 7: speaker-notes-writer — SKILL.md

**Files:**
- Create: `.claude/skills/speaker-notes-writer/SKILL.md`

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p .claude/skills/speaker-notes-writer
```

- [ ] **Step 2: Create the SKILL.md file**

Create `.claude/skills/speaker-notes-writer/SKILL.md`:

```markdown
---
name: speaker-notes-writer
description: Generate timed, cue-rich speaker notes from a TalkBrief and SlideOutline. Calibrates pacing to talk duration, adds timing markers, transition cues, audience interaction prompts, and emphasis markers. Output is written to DeckContext as speaker-notes.json.
argument-hint: [--deck-dir PATH]
allowed-tools: Bash(python *), Read, Write, Glob
---

# /speaker-notes-writer

Generate SpeakerNotes from a TalkBrief and SlideOutline. This skill is part of the Content Services domain (L1) and is invoked after the `narrative-architect` has produced a SlideOutline.

## Prerequisites

Before running, verify that these DeckContext files exist:
- `./tmp/deck/talk-brief.json` (produced by Deck Conductor)
- `./tmp/deck/outline.json` (produced by narrative-architect)

If either file is missing, STOP and report the error. The speaker-notes-writer depends on the outline — if the outline does not exist, invoke the narrative-architect first.

## Parse Arguments

Parse `$ARGUMENTS` for:
- **--deck-dir PATH**: DeckContext directory (default: `./tmp/deck`)

## Step 1: Read Inputs from DeckContext

```bash
python3 -c "
import json, sys
sys.path.insert(0, '.')
from src.deckcontext import read_contract

deck_dir = '${DECK_DIR:-./tmp/deck}'
brief = read_contract(deck_dir, 'talk-brief')
outline = read_contract(deck_dir, 'outline')

if brief is None:
    print('ERROR: talk-brief.json not found in DeckContext')
    sys.exit(1)
if outline is None:
    print('ERROR: outline.json not found in DeckContext — run narrative-architect first')
    sys.exit(1)

print(f'Talk: {brief[\"topic\"]}')
print(f'Duration: {brief[\"duration_minutes\"]} minutes')
print(f'Slides: {len(outline[\"slides\"])}')
print(f'Arc: {outline[\"narrative_arc\"]}')
"
```

## Step 2: Generate Speaker Notes

Run the speaker-notes-writer core logic:

```bash
python3 -c "
import json, sys
sys.path.insert(0, '.')
from src.deckcontext import read_contract, write_contract, update_step
from src.speaker_notes_writer import build_speaker_notes

deck_dir = '${DECK_DIR:-./tmp/deck}'

# Mark step as running
update_step(deck_dir, 'speaker-notes-writer', 'running')

# Read inputs
brief = read_contract(deck_dir, 'talk-brief')
outline = read_contract(deck_dir, 'outline')

# Build speaker notes
notes = build_speaker_notes(brief, outline)

# Write to DeckContext (validates against schema)
write_contract(deck_dir, 'speaker-notes', notes)

# Mark step as completed
update_step(deck_dir, 'speaker-notes-writer', 'completed', output_file='speaker-notes.json')

print(f'SpeakerNotes generated: {len(notes[\"notes\"])} notes')
print(f'Target pace: {notes[\"target_pace_wpm\"]} WPM')
print(f'Estimated duration: {notes[\"total_estimated_minutes\"]} minutes')
print(f'Written to {deck_dir}/speaker-notes.json')
"
```

## Step 3: Enhance the Notes

After generating the structural notes, review and **enhance** them with your knowledge of public speaking and the specific talk topic:

1. **Read the generated speaker-notes.json** using the Read tool
2. **Also read outline.json and talk-brief.json** for full context
3. **Rewrite note text** for each slide:
   - Replace generic placeholders with topic-specific talking points
   - Use keyword-phrase style, not full scripts
   - Include an opening sentence for each slide to get the speaker started
   - Add specific examples, anecdotes, or analogies relevant to the topic and audience
4. **Verify pacing** — total word count / target_pace_wpm should be close to duration_minutes
5. **Enrich cues**:
   - Add `audience_interaction` cues every 8-10 minutes for talks > 15 min
   - Add `emphasis` cues for key statistics or takeaways
   - Ensure `transition` cues provide specific verbal bridges, not generic ones
   - Add `pause` cues after emotionally intense or data-heavy slides
6. **Check timing flow** — timing markers should feel natural when reading through

Write the enhanced notes back:

```bash
python3 -c "
import json, sys
sys.path.insert(0, '.')
from src.deckcontext import write_contract

deck_dir = '${DECK_DIR:-./tmp/deck}'
with open(f'{deck_dir}/speaker-notes.json') as f:
    notes = json.load(f)

# Write back with schema validation
write_contract(deck_dir, 'speaker-notes', notes)
print('Enhanced speaker notes written successfully')
"
```

## Step 4: Report

Report to the user:
- Target speaking pace (WPM) and why it was chosen
- Total estimated duration vs. target duration
- Number of notes generated
- Cue distribution (how many of each cue type)
- Any pacing concerns (if notes are too long/short for the duration)

## Pacing Reference

| Speaking Pace | Words/Minute | Use Case |
|---------------|-------------|----------|
| Slow | 100-120 WPM | Complex technical content, non-native audience |
| Standard | 130-150 WPM | General presentations, conference talks |
| Fast | 160-170 WPM | Motivational speeches, lively narratives |

## Per-Slide Word Budget (at 130 WPM)
| Slide Duration | Word Budget | Notes Style |
|----------------|-------------|-------------|
| 30 seconds | ~65 words | Visual accent — minimal notes |
| 1 minute | ~130 words | Standard content slide |
| 2 minutes | ~260 words | Deep-dive or demo slide |

## The 6 Cue Types
| Cue | Purpose | When |
|-----|---------|------|
| `transition` | Verbal bridge to next slide | At every beat transition |
| `pause` | Let audience absorb content | After data, after key points |
| `audience_interaction` | Engage the audience | Every 8-10 minutes |
| `emphasis` | Vocal stress | Key statistics, takeaways |
| `demo` | Switch to demo window | Before live demos |
| `build_animation` | Click to advance animation | Progressive disclosure slides |

## Speaker Notes Anti-Patterns (avoid these)
- Full scripts that will be read verbatim
- Missing timing markers
- Missing transition cues between sections
- Identical cues on every slide
- Notes longer than the time allows
```

- [ ] **Step 3: Verify the skill is discoverable**

```bash
ls -la .claude/skills/speaker-notes-writer/SKILL.md
```

Expected: File exists with correct permissions.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/speaker-notes-writer/SKILL.md
git commit -m "feat: add speaker-notes-writer Claude Code skill (SKILL.md)"
```

---

## Task 8: Content Services Integration Test

**Files:**
- Create: `tests/test_content_integration.py`

- [ ] **Step 1: Write the integration test**

Create `tests/test_content_integration.py`:

```python
"""Integration test: TalkBrief → narrative-architect → speaker-notes-writer.

Tests the complete Content Services pipeline: reads a TalkBrief and StyleGuide,
generates a SlideOutline via narrative-architect, then generates SpeakerNotes
via speaker-notes-writer. Validates all outputs against their JSON Schemas.
"""

import json
import os
import shutil
import pytest
from jsonschema import validate

DECK_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'test-deck-content')
SCHEMA_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'schemas')
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def load_schema(name):
    path = os.path.join(SCHEMA_DIR, f'{name}.schema.json')
    with open(path) as f:
        return json.load(f)


def load_fixture(name):
    path = os.path.join(FIXTURE_DIR, f'{name}.json')
    with open(path) as f:
        return json.load(f)


@pytest.fixture(autouse=True)
def clean_deck_dir():
    if os.path.exists(DECK_DIR):
        shutil.rmtree(DECK_DIR)
    yield
    if os.path.exists(DECK_DIR):
        shutil.rmtree(DECK_DIR)


class TestContentPipeline:
    """Test the full Content Services pipeline."""

    def _run_pipeline(self, brief_fixture='valid_talk_brief'):
        """Run the complete Content Services pipeline."""
        from src.deckcontext import init_deck, write_contract, update_step
        from src.narrative_architect import build_outline
        from src.speaker_notes_writer import build_speaker_notes

        # Setup DeckContext
        init_deck(DECK_DIR)
        brief = load_fixture(brief_fixture)
        style_guide = load_fixture('valid_style_guide')
        write_contract(DECK_DIR, 'talk-brief', brief)
        write_contract(DECK_DIR, 'style-guide', style_guide)
        update_step(DECK_DIR, 'validate-brief', 'completed')
        update_step(DECK_DIR, 'slide-stylist', 'completed')

        # Step 1: narrative-architect
        update_step(DECK_DIR, 'narrative-architect', 'running')
        outline = build_outline(brief, style_guide)
        write_contract(DECK_DIR, 'outline', outline)
        update_step(DECK_DIR, 'narrative-architect', 'completed',
                    output_file='outline.json')

        # Step 2: speaker-notes-writer
        update_step(DECK_DIR, 'speaker-notes-writer', 'running')
        notes = build_speaker_notes(brief, outline)
        write_contract(DECK_DIR, 'speaker-notes', notes)
        update_step(DECK_DIR, 'speaker-notes-writer', 'completed',
                    output_file='speaker-notes.json')

        return brief, outline, notes

    def test_pipeline_produces_valid_outline(self):
        brief, outline, notes = self._run_pipeline()
        schema = load_schema('slide_outline')
        validate(instance=outline, schema=schema)

    def test_pipeline_produces_valid_notes(self):
        brief, outline, notes = self._run_pipeline()
        schema = load_schema('speaker_notes')
        validate(instance=notes, schema=schema)

    def test_notes_cover_all_slides(self):
        brief, outline, notes = self._run_pipeline()
        assert len(notes['notes']) == len(outline['slides'])

    def test_notes_slide_numbers_match_outline(self):
        brief, outline, notes = self._run_pipeline()
        outline_numbers = sorted(s['slide_number'] for s in outline['slides'])
        notes_numbers = sorted(n['slide_number'] for n in notes['notes'])
        assert outline_numbers == notes_numbers

    def test_total_duration_reasonable(self):
        brief, outline, notes = self._run_pipeline()
        target = brief['duration_minutes']
        actual = notes['total_estimated_minutes']
        # Within ±25% (generous for generated content)
        assert actual <= target * 1.25
        assert actual >= target * 0.5

    def test_pipeline_state_tracking(self):
        from src.deckcontext import read_contract
        self._run_pipeline()
        state = read_contract(DECK_DIR, 'pipeline-state')
        assert state['steps']['narrative-architect']['status'] == 'completed'
        assert state['steps']['speaker-notes-writer']['status'] == 'completed'

    def test_technical_30min_pipeline(self):
        brief, outline, notes = self._run_pipeline('talk_brief_technical_30min')
        assert len(outline['slides']) >= 15
        assert len(outline['slides']) <= 35
        # Should have data_chart slides (brief has data_sources)
        chart_slides = [s for s in outline['slides'] if s['slide_type'] == 'data_chart']
        assert len(chart_slides) >= 1

    def test_keynote_45min_pipeline(self):
        brief, outline, notes = self._run_pipeline('talk_brief_keynote_45min')
        assert len(outline['slides']) >= 20
        assert notes['target_pace_wpm'] >= 130  # inspirational = faster pace

    def test_lightning_5min_pipeline(self):
        brief, outline, notes = self._run_pipeline('talk_brief_lightning_5min')
        assert len(outline['slides']) <= 15
        total_seconds = sum(n['estimated_seconds'] for n in notes['notes'])
        assert total_seconds <= 5 * 60 * 1.15  # within 15% of 5 minutes

    def test_files_written_to_deckcontext(self):
        self._run_pipeline()
        assert os.path.isfile(os.path.join(DECK_DIR, 'outline.json'))
        assert os.path.isfile(os.path.join(DECK_DIR, 'speaker-notes.json'))

    def test_no_consecutive_data_charts_across_pipeline(self):
        brief, outline, notes = self._run_pipeline('talk_brief_technical_30min')
        slides = outline['slides']
        for i in range(len(slides) - 1):
            if slides[i]['slide_type'] == 'data_chart':
                assert slides[i + 1]['slide_type'] != 'data_chart', (
                    f"Consecutive data_chart at slides "
                    f"{slides[i]['slide_number']} and {slides[i+1]['slide_number']}"
                )
```

- [ ] **Step 2: Run the integration test**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_content_integration.py -v`

Expected: All tests PASS.

- [ ] **Step 3: Run the complete test suite**

Run: `source .venv/bin/activate && python3 -m pytest tests/ -v --tb=short`

Expected: All tests PASS across all test files (schema, deckcontext, narrative_architect, speaker_notes_writer, content_integration).

- [ ] **Step 4: Commit**

```bash
git add tests/test_content_integration.py
git commit -m "test: add Content Services integration test (brief → outline → notes)"
```

---

## Task 9: Create __init__.py and Final Verification

**Files:**
- Possibly modify: `src/__init__.py` (if not already tracking new modules)

- [ ] **Step 1: Verify all modules import cleanly**

Run:
```bash
source .venv/bin/activate && python3 -c "
from src.narrative_architect import build_outline, select_narrative_arc, calculate_slide_count, generate_slide_sequence, KNOWN_ARCS, VALID_SLIDE_TYPES
from src.speaker_notes_writer import build_speaker_notes, select_pace_wpm, calculate_slide_seconds, generate_timing_markers, generate_cues
print('All Content Services modules import successfully')
print(f'Narrative arcs: {len(KNOWN_ARCS)}')
print(f'Slide types: {len(VALID_SLIDE_TYPES)}')
"
```

Expected: Clean import, no errors, correct counts.

- [ ] **Step 2: Verify Python syntax is clean**

Run:
```bash
source .venv/bin/activate && python3 -m py_compile src/narrative_architect.py && echo "narrative_architect: OK" && python3 -m py_compile src/speaker_notes_writer.py && echo "speaker_notes_writer: OK"
```

Expected: Both print OK.

- [ ] **Step 3: Run complete test suite one final time**

Run:
```bash
source .venv/bin/activate && python3 -m pytest tests/ -v --tb=short
```

Expected: All tests PASS.

- [ ] **Step 4: Verify both skills are discoverable**

Run:
```bash
ls -la .claude/skills/narrative-architect/SKILL.md .claude/skills/speaker-notes-writer/SKILL.md
```

Expected: Both files exist.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: Phase 3 Content Services complete — narrative-architect + speaker-notes-writer"
```

---

## Summary

After completing all 9 tasks, Phase 3 provides:

| Artifact | Purpose |
|----------|---------|
| `research/synthesis-narrative-architect.md` | Research distillation for outline generation |
| `research/synthesis-speaker-notes-writer.md` | Research distillation for notes generation |
| `src/narrative_architect.py` | Core logic: arc selection, slide density, sequence generation |
| `src/speaker_notes_writer.py` | Core logic: pacing, timing, cue generation |
| `.claude/skills/narrative-architect/SKILL.md` | Claude Code skill for outline generation |
| `.claude/skills/speaker-notes-writer/SKILL.md` | Claude Code skill for speaker notes generation |
| 3 extended TalkBrief fixtures | Test coverage for technical, keynote, and lightning talks |
| `tests/test_narrative_architect.py` | 20+ unit tests for outline generation |
| `tests/test_speaker_notes_writer.py` | 20+ unit tests for speaker notes generation |
| `tests/test_content_integration.py` | End-to-end pipeline test: brief → outline → notes |

**Key design decisions:**
1. Arc auto-selection based on tone + duration + data sources (16 arcs catalogued)
2. Slide density calibrated by style (0.6-1.2 slides/minute)
3. 12 slide types with sequencing rules (no consecutive data_charts, section dividers at transitions)
4. Pacing: 100-170 WPM based on tone and audience
5. 6 cue types: transition, pause, audience_interaction, emphasis, demo, build_animation
6. Both modules produce structural skeletons; SKILL.md Step 3 instructs Claude to enhance with topic-specific content

**Dependency chain:**
```
Phase 1 (Foundation) → Phase 2 (slide-stylist produces StyleGuide) → Phase 3a (narrative-architect reads Brief + StyleGuide, writes Outline) → Phase 3b (speaker-notes-writer reads Brief + Outline, writes Notes) → Phase 4+ (downstream consumers)
```
