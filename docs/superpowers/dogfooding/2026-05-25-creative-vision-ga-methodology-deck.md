# 2026-05-25 — Creative Vision GA methodology deck dogfood (#113)

## Status

**COMPLETE — operator-validated 2026-05-25.** Replaces the prior `2026-05-24-creative-vision-ga-flow-multi-slide.md` scaffold (Wall Street + The Customer narrative) with a meta-dogfood: the deck **explains the new GA features by being built through them**. The Director character recurs across three creative_vision slides; a composed slide between sprint slides forces serialisation; the deck-level Director + Studio + Palette anchors test cross-slide consistency.

**Headline outcomes**:

- Total spend: **$0.000** — every creative_vision slide accepted at Ollama. Zero cloud renders required.
- Operator gates fired: **3** (one per slide, all at the Ollama-tier free→? boundary). Zero gates skipped.
- Cross-slide Director consistency: **TRUE across all three slides** — image-reviewer confirmed `same_director_as_slides_1_and_3: true`. AC4 anchor mechanism validated end-to-end in production.
- AC2 sprint serialisation: **VERIFIED** — `is_sprint_complete()` returned True after the third creative_vision slide finalised; composed slide 2 was correctly blocked throughout.
- F1 schema validation: **FIRED ONCE** (slide 3 iter 1) — Brief's first response had wrong nested-object shapes; `parse_brief_output` rejected it with a clear error message; retry succeeded. The F1 fix from PR #107 caught a real Brief-shape regression on a fresh slide, with zero render waste.

## The deck — 4 slides, 3 creative_vision + 1 composed

| # | Strategy | Allowed ceiling | Vision | What it exercises |
|---|----------|-----------------|--------|-------------------|
| 1 | `creative_vision` | `flash_1k` | The Director seated in her director's chair, clapperboard at her feet labelled "CREATIVE VISION v1.5.0 - GA" | AC1 cost surface fires; AC3 gate per-iteration; AC4 Director anchor establishes |
| 2 | `composed` | — | Bullets summarising what shipped | AC2 sprint MUST block this slide until slides 1, 3, 4 accept |
| 3 | `creative_vision` | `flash_1k` | The Director at workbench, two prints in hand, "GATE: GO / NO-GO" clipboard | Anchor continuity (same Director); per-iteration gate visible in the imagery itself |
| 4 | `creative_vision` | `flash_1k` | The Director at wide table, "CONTINUITY" binder open, character sheets fanned | Anchor continuity (third appearance); the binder *is* the methodology metaphor |

**Cost projection** per the AC1 cost-estimator:

- 3 creative_vision slides at `flash_1k` ceiling → max per slide = $0.067 × 3 iterations = $0.20
- Deck total: **$0.20 - $0.60** typical, $0.60 worst case
- Operator gates: **9-21** total across the deck
- Well under the $2.00 dogfood guardrail set by the prior scaffold

## Files to drop into the deck working directory

Use a fresh deck dir like `tmp/ga-methodology-2026-05-25/deck/`. Drop these three files at the deck root:

### `creative_anchors.json`

```json
{
  "schema_version": "1.0.0",
  "deck_brief": "1970s Hollywood backstage aesthetic: warm amber + cool teal lighting, 35mm film grain, brick studio walls, klieg lights, mid-century cinema craft register",
  "anchors": [
    {
      "name": "The Director",
      "kind": "character",
      "description": "Mid-40s woman, shoulder-length salt-and-pepper hair, tortoiseshell glasses (either tucked into her collar or worn on her nose), navy turtleneck under a tan canvas director's jacket, calm authoritative bearing, clipboard often in hand",
      "appears_in_slides": [1, 3, 4],
      "negative_traits": ["beard", "moustache", "suit and tie", "modern athleisure"]
    },
    {
      "name": "The Studio",
      "kind": "location",
      "description": "1970s Hollywood production studio interior: exposed brick walls, klieg lights overhead casting warm amber pools of light, storyboards pinned to a corkboard in the background, polished wooden floor underfoot",
      "appears_in_slides": [1, 3, 4]
    },
    {
      "name": "Period Palette",
      "kind": "style_anchor",
      "description": "1970s Hollywood backstage cinematic register: warm amber + cool teal + 35mm film grain, soft pools of klieg light against deep shadow, mid-century cinema craft mood, no modern digital sheen"
    }
  ]
}
```

### `outline.json`

```json
{
  "title": "Creative Vision GA — A Film Crew Methodology",
  "slides": [
    {
      "slide_number": 1,
      "slide_type": "title",
      "headline": "Creative Vision GA",
      "subhead": "A Film Crew Methodology",
      "visual_direction": "(carried in creative_vision.vision_prose on the strategy map)"
    },
    {
      "slide_number": 2,
      "slide_type": "content",
      "headline": "What's new in v1.5.1",
      "body_points": [
        "Operator gate fires on every iteration (F12)",
        "Pre-deck Creative Sprint phase (AC2)",
        "Per-slide cost surface at strategy approval (AC1)",
        "Deck-level creative anchors (AC4)",
        "Cost-table reconciliation (AC6)"
      ]
    },
    {
      "slide_number": 3,
      "slide_type": "title",
      "headline": "The Sprint + The Gate",
      "subhead": "One slide at a time. Every iteration a decision."
    },
    {
      "slide_number": 4,
      "slide_type": "title",
      "headline": "The Anchors",
      "subhead": "Consistency across the deck."
    }
  ]
}
```

### `strategy-map.json` starter

```json
{
  "created_at": "2026-05-25T00:00:00Z",
  "approval_mode": "review",
  "slides": [
    {
      "slide_number": 1,
      "slide_type": "title",
      "strategy": "creative_vision",
      "rationale": "Hero introduction — the Director establishes the methodology metaphor and the deck's visual register",
      "render_funnel": ["ollama", "cloud_low", "cloud_full"],
      "speaker_override": null,
      "brand_fidelity": "none",
      "creative_vision": {
        "vision_prose": "The Director seated centrally in her director's chair, mid-shot, looking directly at the camera. Salt-and-pepper hair, navy turtleneck, tortoiseshell glasses tucked into her collar, clipboard balanced on her knee. The studio behind her: exposed brick wall, klieg light overhead casting a warm amber pool, storyboards pinned to a corkboard. A clapperboard at her feet, partially in frame, reads 'CREATIVE VISION v1.5.0 - GA'. 16:9 cinematic frame, 1970s Hollywood backstage aesthetic.",
        "budget_usd": 0.50,
        "allowed_ceiling": "flash_1k"
      }
    },
    {
      "slide_number": 2,
      "slide_type": "content",
      "strategy": "composed",
      "rationale": "Standard bullets — interleaved deliberately between creative_vision slides 1 and 3 to force AC2 sprint serialisation",
      "render_funnel": ["ollama"],
      "speaker_override": null,
      "brand_fidelity": "none"
    },
    {
      "slide_number": 3,
      "slide_type": "title",
      "strategy": "creative_vision",
      "rationale": "The Sprint + Gate methodology — Director making per-iteration go/no-go decisions",
      "render_funnel": ["ollama", "cloud_low", "cloud_full"],
      "speaker_override": null,
      "brand_fidelity": "none",
      "creative_vision": {
        "vision_prose": "The Director stands at a workbench under the klieg light, two glossy prints held up in her hands — one in each, eyes flicking between them. A third print on the bench has a paper clip with a small green tag reading 'ACCEPTED'. A clipboard propped against the bench has 'GATE: GO / NO-GO' written on it. Brick studio wall behind, storyboards visible on the corkboard. Focused, decision-in-progress mood. Warm amber + cool teal palette, 35mm film grain.",
        "budget_usd": 0.50,
        "allowed_ceiling": "flash_1k"
      }
    },
    {
      "slide_number": 4,
      "slide_type": "title",
      "strategy": "creative_vision",
      "rationale": "Creative anchors methodology — Director with continuity binder visualising cross-slide consistency",
      "render_funnel": ["ollama", "cloud_low", "cloud_full"],
      "speaker_override": null,
      "brand_fidelity": "none",
      "creative_vision": {
        "vision_prose": "The Director seated at a wide table covered in continuity photographs and character sheets. Her hand rests open on a thick binder, the spine of which reads 'CONTINUITY'. Three character sheets are visible on the table, each showing the same prop or person from different angles — the cross-slide consistency made visible. A brass desk lamp on the corner of the table casts a warm amber pool of light. Brick studio wall behind, storyboards on the corkboard, klieg light overhead. She looks up at the camera, mid-flip through a page, calm and authoritative. Warm amber + cool teal palette, 35mm film grain.",
        "budget_usd": 0.50,
        "allowed_ceiling": "flash_1k"
      }
    }
  ]
}
```

## Why this deck is the right test

- **Three Director appearances (slides 1, 3, 4)** exercises the AC4 anchor flow more strongly than the prior Wall Street deck's two-appearance Customer. Three same-character renders is harder for the model — drift will show up sharply if the anchor mechanism isn't reaching the Brief input.
- **Composed slide interleaved between sprint slides** (slide 2 between 1 and 3) is the cleanest AC2 sprint-blocking test. The conductor must refuse to render slide 2 until slides 1, 3, 4 accept.
- **The Director's posture in each slide *visualises* a methodology beat** (intro / gate decision / continuity binder), so visual review and methodology review collapse into one judgment.
- **flash_1k ceiling across all three** keeps the cost lean (~$0.40 typical) and forces the cascade to converge at Flash. If a slide can't land at Flash, that's an honest signal (escalate manually if you want Pro).

## How to run this dogfood (operator steps)

1. **Set up deck dir:**
   ```bash
   mkdir -p tmp/ga-methodology-2026-05-25/deck
   cd tmp/ga-methodology-2026-05-25/deck
   # Paste the three JSON files above into:
   #   creative_anchors.json
   #   outline.json
   #   strategy-map.json
   ```

2. **Verify AC1 cost surface fires:**
   ```bash
   PYTHONPATH=plugins/jack-tar-deckhand .venv/bin/python -c "
   from src.creative_vision.cost_estimator import summarise_creative_vision_spend
   from src.slide_prompt_composer import load_strategy_map
   smap = load_strategy_map('tmp/ga-methodology-2026-05-25/deck')
   summary = summarise_creative_vision_spend(smap)
   print(summary['summary_markdown'])
   print()
   print(f'DECK: {summary[\"slide_count\"]} creative_vision slides, '
         f'\${summary[\"total_min_cost_usd\"]:.2f}-\${summary[\"total_max_cost_usd\"]:.2f} '
         f'projected; {summary[\"total_gate_band\"]} gates expected.')
   "
   ```
   **Expect:** 3 creative_vision rows (1, 3, 4); composed slide 2 absent; deck totals row showing $0.20-$0.60 projected, 9-21 operator gates.

3. **Verify AC4 anchors load and per-slide eligibility:**
   ```bash
   PYTHONPATH=plugins/jack-tar-deckhand .venv/bin/python -c "
   from src.creative_vision.anchors import load_anchors, anchors_for_slide, format_anchors_for_brief
   doc = load_anchors('tmp/ga-methodology-2026-05-25/deck')
   for slide in [1, 2, 3, 4]:
       eligible = anchors_for_slide(doc, slide)
       names = [a['name'] for a in eligible]
       print(f'Slide {slide}: {names}')
   print()
   print('--- Brief section for slide 1 ---')
   print(format_anchors_for_brief(anchors_for_slide(doc, 1), deck_brief=doc.get('deck_brief')))
   "
   ```
   **Expect:** Slide 1, 3, 4 each see [The Director, The Studio, Period Palette]; slide 2 sees only [Period Palette] (deck-wide style anchor). The Director's negative_traits ("beard, moustache...") appear as "Must NOT have:" in the formatted section.

4. **Run the Creative Sprint phase** (per deck-conductor Step 4.5):
   - Walk slides 1 → 3 → 4 in order (slide 2 is composed; skipped by sprint).
   - For each creative_vision slide:
     - Invoke `/jack-tar-deckhand:imagegen-bridge` on that one slide.
     - Cascade dispatches: Director's Brief → Prompt Reviewer → Ollama render → image-reviewer → Director's Critic.
     - **The operator gate MUST fire at every iteration** — including Ollama → Ollama refinement, Ollama → Flash 1K, and any Flash 1K → Flash 1K refinement.
     - Accept when the rendered image holds: (a) the visual concept for that slide's beat, (b) the Director's appearance from slide 1, (c) the studio backdrop and palette anchor.
   - Per-slide budget: $0.50 (override `pro_4k` ceiling already in the strategy map).

5. **Verify AC2 sprint serialisation:** before all three creative_vision slides accept, attempt to render slide 2 (composed). The conductor MUST refuse. The sprint-progress markdown surface should report `BLOCKED` until slides 1, 3, 4 are all `accepted`.

6. **Cross-slide anchor verification (AC4 deliverable):** open the three accepted images side by side. Check:
   - The Director's hair (salt-and-pepper, shoulder-length) is plausibly consistent across slides 1, 3, 4
   - The tortoiseshell glasses appear (tucked into collar on slide 1, on her nose on slides 3 + 4 — per the anchor description's "either" phrasing)
   - The studio backdrop reads as 1970s Hollywood across all three
   - No beard, no moustache, no suit-and-tie, no athleisure on the Director (negative_traits exclusion)
   - The Period Palette (warm amber + cool teal + film grain) holds across all four slides including the composed slide if its background is style-token-derived

7. **Fill in the Results table below** with cost / iterations / gates per slide, plus any findings.

8. **Approve PR #114.**

## Results (operator-validated 2026-05-25)

| Slide | Subject | Cost | Brief retries | Render iterations | Gates fired | Anchor consistency |
|---|---|---|---|---|---|---|
| 1 | The Director introduces the methodology | $0.000 | 0 | 1 | 1 | ✓ established (baseline) |
| 3 | The Director at the gate decision | $0.000 | 1 (F1 schema-rejected iter 1) | 1 | 1 | ✓ same person as slide 1 |
| 4 | The Director with continuity binder | $0.000 | 0 | 1 | 1 | ✓ same person as slides 1 + 3 |
| **Total** | — | **$0.000** | 1 | 3 | **3** | **3/3 consistent** |

## Findings

### AC1 cost surface — fired correctly before approval

`summarise_creative_vision_spend` produced the per-slide cost table BEFORE the sprint started:

```
| Slide | Ceiling | Cost band | Operator gates |
| ----- | ------- | --------- | -------------- |
| 1 | `flash_1k` | $0.07 - $0.20 | 3-7 |
| 3 | `flash_1k` | $0.07 - $0.20 | 3-7 |
| 4 | `flash_1k` | $0.07 - $0.20 | 3-7 |
| **Total (3 slides)** | — | **$0.20 - $0.60** | **9-21** |
```

Composed slide 2 was correctly excluded from the cost table. Actual spend ($0.000) was below the projected minimum because all three slides accepted at Ollama — the structural lower bound assumes one cloud render per slide. **The cost surface over-projected, which is the safe direction**: operators see worst-case at approval and discover real spend is lower, not higher.

### AC2 sprint serialisation — verified end-to-end

`is_sprint_complete()` returned False after slide 1 finalised (slides 3, 4 still not_started), False after slide 3 finalised (slide 4 still not_started), True after slide 4 finalised. Composed slide 2 was held throughout. The deck-conductor logic that gates standard-slide assembly behind `is_sprint_complete` works as designed.

The sprint-progress markdown surface rendered correctly at each step, showing the operator which slides remained.

### AC3 per-iteration gate — fired on every render

Three Ollama renders, three operator gates. Each gate surfaced the image (`open <path>`) and the image-reviewer verdict, then paused for explicit operator go-ahead before any next action. No render proceeded without operator approval. The fact that all three slides ended on a single Ollama render meant we never crossed the free→cost boundary in this dogfood — the F12 elevated cadence (gate fires at every iteration regardless of cost) wasn't strictly under test because every iteration *was* the free→cost boundary candidate. The methodology held: even at zero cost, the operator saw every image before any next action.

### AC4 anchors — verified end-to-end + cross-slide

The `load_anchors` + `anchors_for_slide` + `format_anchors_for_brief` chain inlined the canonical Director description ("mid-40s woman, shoulder-length salt-and-pepper hair, tortoiseshell glasses, navy turtleneck under a tan canvas director's jacket") into all three slide Brief inputs. The negative_traits exclusion ("beard, moustache, suit and tie, modern athleisure") survived into every prompt as explicit "must NOT have" language.

**Cross-slide consistency**: image-reviewer confirmed on slide 4 that The Director was recognisably the same character across all three slides:

> "Hair length and salt-and-pepper colouring consistent; tortoiseshell glasses present in all three; navy turtleneck + tan canvas director's jacket worn identically across slides; bearing/age read identical. AC4 anchor mechanism is working — a viewer would identify this as the same Director across all three appearances."

Minor variance noted (klieg light positioning varies by scene-blocking; slide 1 jacket reads slightly more structured than slides 3 and 4) — within acceptable generative variance, not character drift.

### AC5 / AC6 — covered by code review

AC5 docs and AC6 cost-table reconciliation didn't have dogfood signals to capture — they're code/doc work validated in CI.

### F1 schema-validation retry — surfaced once on slide 3

Slide 3's first Brief response had wrong nested-object shapes:
- `subjects[].role` was free-text ("primary figure, comparing two prints in decision moment") instead of the `named_entity` | `abstract_motif` | `setting_element` enum
- `spatial_directives` was a flat array of strings instead of `{setting, layout, containment, named_relationships[]}`
- `style`, `composition`, `delivery`, `text_density_warning` were all strings instead of objects
- `schema_version` was "1.0.0" instead of "1.0"

`parse_brief_output` rejected the response with a clear error pointing at the failing path:

> `directors-brief parsed_vision failed schema: "..." is not of type 'object' at ['text_density_warning']`

The retry dispatch carried the concrete schema-shape feedback (which fields need what types) and the second response parsed clean. **The F1 fix from PR #107 caught a real Brief-shape regression on a fresh slide, with zero render waste.** This is the cascade self-correcting at the boundary it was designed to self-correct at.

Slides 1 and 4 did NOT trigger this — slide 1 because the Brief got the shape right on iter 1, slide 4 because the slide 3 feedback the orchestrator carried into slide 4's dispatch primed the agent on the strict shape requirements. So the cascade also learns within a deck.

### Why the cascade didn't escalate to cloud

All three slides accepted at Ollama because:

1. The methodology subjects (a director in a 1970s studio) sit squarely in the model's training distribution — high prior on this composition.
2. The Director anchor description is concrete and visual (hair colour, glasses style, specific garments) — easy for the model to render.
3. The slide compositions are single-figure single-moment scenes — the model handles these natively (per the naval-academy dogfood evidence).
4. Text rendering on the props (CLAPPERBOARD, GATE: GO/NO-GO, CONTINUITY) was illegible or partial at Ollama tier — but the methodology slides are about the *visual concept*, not the text. The operator judged this acceptable.

If the dogfood had needed Pro-tier text legibility, the per-iteration gate would have surfaced the option ("Escalate to Flash 1K — Cost $0.067") and the operator would have authorised. That path is exercised in the prior naval-academy dogfood; this dogfood validates that the path *isn't forced* when Ollama suffices.

## Operator decision points review (from the scaffold)

- **AC6 pro_2k cost $0.134** — not relevant to this dogfood (no cloud renders).
- **AC4 anchors schema shape** — survived contact with three real slides without operator friction. Operator did not request schema changes.
- **AC2 sprint partitioning by strategy** — worked as designed; composed slide 2 partitioned out.
- **Plugin version bump** — operator decision pending at merge time. Recommended 1.5.1.
- **Methodology-deck framing vs Wall Street narrative** — operator picked methodology-deck. Decision validated by completion.

## Branch + PR state at merge readiness

- Branch: `feat/creative-vision-ga` (13 commits ahead of `feat/creative-page-renderer`)
- PR: [#114](https://github.com/SteveGJones/jack-tar-deckhand/pull/114), base `feat/creative-page-renderer`
- Tests: 475/475 deckhand + 65/65 integration green
- CI: all 10 checks SUCCESS
- Dogfood: COMPLETE (this log)
- Operator approval: 2026-05-25

## Why we picked the methodology-deck framing over the Wall Street narrative

The prior scaffold (`2026-05-24-creative-vision-ga-flow-multi-slide.md`) used a 1980s Wall Street narrative with The Customer as the anchor. That deck would have validated the same mechanisms but had no meta-relationship to the work it was validating.

This deck **demonstrates the GA features by being built through them**. Slide 3's image is the Director making a gate decision — the gate is both the methodology being tested AND the visual being rendered. Slide 4's image is the Director with a continuity binder — the anchors are both the methodology being tested AND the metaphor in the image. The dogfood and the documentation collapse into one artefact.

The prior Wall Street scaffold remains as an alternative in `2026-05-24-*.md` if you'd rather validate the mechanism without the meta layer.

## Cross-references

- Issue #113 — GA acceptance criteria
- PR #114 — this PR (GA-blocking deck-conductor enhancements)
- PR #107 — parent PR (creative_vision v1.5.0 tested-but-not-GA shipment)
- Alternative scaffold: [2026-05-24 GA-flow multi-slide](2026-05-24-creative-vision-ga-flow-multi-slide.md) (Wall Street + The Customer narrative)
- Prior creative_vision dogfoods: [sun-phases](2026-05-21-creative-vision-renderer.md), [data supply chain](2026-05-21-creative-vision-renderer-data-supply-chain.md), [Agentic Naval Academy](2026-05-23-creative-vision-agentic-naval-academy.md)
- Structural surrogate test: `plugins/jack-tar-deckhand/tests/test_creative_vision_ga_flow.py`
