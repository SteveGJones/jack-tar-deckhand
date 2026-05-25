# 2026-05-25 — Creative Vision GA methodology deck dogfood (#113)

## Status

**Operator-validation pending.** Replaces the prior `2026-05-24-creative-vision-ga-flow-multi-slide.md` scaffold (Wall Street + The Customer narrative) with a meta-dogfood: the deck **explains the new GA features by being built through them**. The Director character recurs across three creative_vision slides; a composed slide between sprint slides forces serialisation; the deck-level Director + Studio + Palette anchors test cross-slide consistency.

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

## Results (operator to fill in)

| Slide | Subject | Cost | Iterations | Gates fired | Anchor consistency |
|---|---|---|---|---|---|
| 1 | The Director introduces the methodology | _$X.YY_ | _N_ | _N_ | _The Director hair/glasses/jacket consistent? yes/no_ |
| 3 | The Director at the gate decision | _$X.YY_ | _N_ | _N_ | _Same Director as slide 1? yes/no_ |
| 4 | The Director with continuity binder | _$X.YY_ | _N_ | _N_ | _Same Director as slides 1+3? yes/no_ |
| **Total** | — | **$X.YY** | — | **N** | — |

## Findings (operator to fill in)

_Capture deviations from the GA-flow design. Specifically:_

- _Did the AC1 cost surface fire BEFORE strategy approval?_
- _Was AC2 sprint serialisation enforced (composed slide 2 blocked until creative_vision slides finalised)?_
- _Did the AC3 per-iteration gate fire on every iteration including cost-to-cost transitions?_
- _Did AC4 anchors actually reach the Director's Brief input? Inspect the dispatched prompt to confirm the anchor description was inlined verbatim._
- _Did the negative_traits exclusion ("no beard / moustache / suit / athleisure") survive into the rendered prompt?_
- _Cross-slide character drift: same Director or visibly different person across 1 / 3 / 4? If drifted, where did the description get lost?_

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
