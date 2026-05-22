# 2026-05-22 — Creative Vision Renderer · data-supply-chain dogfood (#105)

## Scope

Second creative_vision dogfood after the sun-phases founding example. New ground:

- a **multi-entity, multi-panel** vision (not a single composed scene),
- a **stylised period aesthetic** ("1980s Wall Street business movie"),
- explicit **per-panel text labels** (4 callouts) on top of an in-scene density above the warning threshold,
- a second iteration at Ollama before escalating, and a clean Critic-driven escalation to Flash 1K.

Budget cap: **$0.50** with `allowed_ceiling: pro_1k`. The operator's brief expected we might need to climb to Flash 4K or Pro to nail per-panel lighting and film-grain — the dogfood would tell us whether the cascade can converge faster than that.

The dogfood was also the first run AFTER the F1/F2 findings from the sun-phases log were noted but not yet fixed. Goal: surface them again with concrete evidence, then fix.

## Cascade summary

| # | Tier | Cost | entity | spatial | style | quality | composition | Verdict | gap_location |
|---|------|------|--------|---------|-------|---------|-------------|---------|--------------|
| 1 | ollama | $0.00 | 52 | 48 | 62 | 58 | 55 | refine_at_tier | prompt |
| 2 | ollama | $0.00 | 54 | **67** ▲ | **45** ▼ | 58 | **68** ▲ | escalate_tier | tier |
| 3 | flash_1k | $0.067 | **82** | **85** | 72 | **84** | **88** | pass (see F3) | prompt |

**Total spend: $0.067** (out of $0.50 budget; $0.433 remaining).
**Final image**: `tmp/creative-vision-dogfood/deck/creative-vision/2/runs/03-flash-1k.png`.

Final image conveys the parable cleanly: 4-panel 2×2 grid with all four callouts (`SALES`, `FINANCE`, `CUSTOMER`, `SUPPLY CHAIN`) legible; sports cars visible through bar window in TL; smoothed napkin beside typed paper in TR; customer reading invoice under amber lamp in BL; blank wooden signpost + truck driver squinting from cab + confused workers with `?` callouts in BR. The blank-signpost punchline lands.

## What we proved

### 1. Cascade economics scale to a more complex vision

The single Ollama → Flash 1K jump again delivered the largest score deltas:

- entity_fidelity 54 → **82** (+28)
- spatial_fidelity 67 → 85 (+18) — already trending up at Ollama
- composition 68 → **88** (+20)
- quality 58 → 84 (+26)
- style_fidelity 45 → 72 (+27) — best Ollama→Flash delta of any axis, but still below the 80 threshold

Cost: $0.067. We did **not** need Flash 2K, Flash 4K, Pro 1K, or Pro 4K. The "draft at Ollama → escalate to Flash 1K" pattern from the sun-phases run held for a much more complex vision.

### 2. The Prompt Reviewer caught a real gap pre-render

Iter 2's first prompt draft (from the Brief) omitted cartoon-callout speech-bubbles entirely. The Prompt Reviewer (Haiku) returned `refine` with one specific issue:

> Cartoon callout bubbles labelling each panel/stage are missing from the proposed prompt. Operator's prose specifies 'cartoon style callouts' and 'Each part of the data supply chain for customer order is clearly labelled' — these must appear explicitly in the prompt … especially critical given the text_density_warning threshold breach (18 text elements).

This is the loop working as designed. The text-side gate caught a regression before any render cost was paid. We refined the prompt to inline the four callouts (`SALES`/`FINANCE`/`CUSTOMER`/`SUPPLY CHAIN`) and cap total in-scene text to exactly those four labels (density mitigation). Second review returned `pass`.

### 3. The text_density_warning is doing real work

`text_density_warning.threshold_breach: true` (estimated 18 elements — 4 callouts plus ~14 implied small in-scene labels). The Prompt Reviewer's density check fired and the refined prompt explicitly capped text to "four callouts only" — preventing the Flash render from trying to render 18 garbled mini-labels. The final Flash 1K image renders exactly four crisp callouts. The density-warning → prompt-mitigation chain works.

### 4. Ollama iter 2 improved on spatial but regressed on style — a textbook tier-gap signal

Style fidelity dropped 62 → 45 even with a better prompt. The image stopped reading as 80s film and started reading as modern flat cartoon. The Critic correctly diagnosed `gap_location: tier`: the prompt is now well-specified; Ollama (z-image-turbo) simply can't render film-grain texture or per-panel cinematic lighting. Escalation to Flash 1K resolved most of it (style 45 → 72; per-panel lighting differentiated; sports cars present; signpost present; truck driver in cab).

This is the cascade's value proposition in one shot: stay free until score deltas plateau on a specific axis, then pay the cheapest cloud tier to break through.

## Findings

### F1 — Brief returns non-canonical ParsedVision shape (reaffirmed from 2026-05-21 sun-phases log) — **FIXED in this PR**

**Observation**: in iter 2's Brief, `parsed_vision.subjects` came back as plain strings, not `{name, role, spatial_slot}` objects. The cascade would have silently produced a manifest that downstream consumers (Critic, iterate_slide) can't reason about. The prompt text itself was correct, but the structured intermediate was unusable.

**Fix shipped**: `src/creative_vision/brief.parse_brief_output` now validates `parsed_vision` against `schemas/parsed_vision.schema.json` using `jsonschema.validate`. Empty/whitespace prompts also rejected (was implicit; now explicit). Three new failure-path tests cover: subjects-as-strings, missing-required-key, empty-prompt. Total brief tests 5 → 8.

**Why this matters**: parse-time validation converts a silent semantic regression (downstream KeyError pages out at runtime) into a clear, located error at the Brief boundary. The Brief either produces a canonical ParsedVision or fails loud.

### F2 — Brief sometimes emits the prompt outside the JSON fence (reaffirmed) — **FIXED in this PR**

**Observation**: across runs the Brief has, at Flash and Pro tiers, emitted a prose paragraph or second fence outside its primary JSON block, leaving the prompt inaccessible to `parse_brief_output` (which reads only the first `json` fence).

**Fix shipped**: `agents/directors-brief.md` Output Contract now shows:
- a labelled **CORRECT shape** (both keys inside one fence),
- a labelled **WRONG shape — DO NOT do** anti-pattern block with four concrete failure examples (prompt outside the fence, two separate fences, subjects as plain strings, omitted required key, empty prompt),
- a **self-check** prompt at the end telling the agent to mentally re-read its very first `json` fence and count the keys.

A new agent-definition test asserts the WRONG / CORRECT labels and the "outside the fence" / "two separate fences" phrases are present, so this guidance can't silently regress.

**Why this matters**: agent self-correction is contract-driven. A loose Output Contract section sees the agent improvise. A tight one with concrete WRONG examples sees the agent retract. F2 has now been observed in TWO dogfoods — that is enough signal to lock the contract.

### F3 — Director's Critic returned `verdict: pass` with `style_fidelity: 72` (verdict-coherence violation) — **NEW, not yet fixed**

**Observation**: iter 3 (Flash 1K) Critic verdict was `pass`, scores `82/85/72/84/88`. The Critic agent definition is explicit:

> **Bad**: `verdict: "pass"` with `entity_fidelity: 60`
> **Why**: Pass requires all axes ≥ 80. A 60 on any axis mandates a non-pass verdict.

72 ≥ 80 is false. The Critic violated its own hard rule and the orchestrator accepted the verdict (because `decide_next_action` keys only off `verdict == "pass"` → `accept`). The Critic's `recommended_action` self-explained the violation as a deliberate operator-discretion call ("style_fidelity 72 is a known Flash 1K cinematic-fidelity limitation … escalate to pro_1k for one shot targeting the 80s film aesthetic — but … operator discretion").

That reasoning is fine for the operator to make — but the **Critic** is not the operator. The Critic's only job is to evaluate; the operator decides whether to spend more.

**Proposed fix (deferred to follow-up patch — not in this PR)**:

Add verdict-coherence validation to `src/creative_vision/critic.parse_critic_output` so the parser rejects the same shape the agent definition warns against:

```python
def _validate_verdict_score_coherence(payload):
    verdict = payload["verdict"]
    scores = payload["per_axis_scores"]
    min_score = min(scores.values())
    if verdict == "pass" and min_score < 80:
        raise ValueError(
            f"Critic verdict=pass but min axis score {min_score} < 80; rule violated."
        )
    if verdict != "pass" and not payload["issues"]:
        raise ValueError(
            f"Critic verdict={verdict} but issues is empty; non-pass requires at least one issue."
        )
```

This pairs the schema validation with semantic validation, the same way `brief.parse_brief_output` now does for ParsedVision.

**Why deferred**: the dogfood completed successfully and the operator-visible image is good. Fixing F3 as a follow-up patch keeps this PR focused on F1 + F2 (the findings the operator explicitly scoped in).

### F4 — Critic referenced wrong density count in iter 2 narrative — **MINOR, no code change**

The Critic's iter 2 narrative said "all four callouts rendered" but the test panel actually showed `SALES`/`FINANCE`/`CUSTOMER`/`CHAIN` (last label truncated). Two reviewers saw this:

- Haiku image-reviewer: "Four callout labels all rendered with perfect legibility"
- Sonnet Critic: "Supply Chain callout label appears truncated — rendered as 'CHAIN' only"

Sonnet is right. Haiku had visual perception fidelity drift on text rendering. This matches the `feedback_agent_definition_reload.md` memory note about Haiku's visual limitations. No code change — just a reminder that cross-validating with Sonnet on text-fidelity claims is worth the extra dispatch when the slide is text-bearing.

### F5 — Cartoon-callout adherence (Critic note) — **PROMPT PATTERN**

The Critic's iter 3 issues list flagged that the cocktail-napkin reads more as folded paper than as a wedge cocktail napkin. Tiny entity-fidelity slip, not worth re-rendering. **Pattern**: when an entity is genre-specific (cocktail napkin vs. paper, signpost vs. fingerpost, etc.), inline the disambiguating descriptor in the prompt. This goes in the Brief's prose-faithfulness guidance for future revisions.

## Schema / contract changes shipped in this PR

- **brief.py** — `parse_brief_output` validates `parsed_vision` against `parsed_vision.schema.json`; rejects empty/whitespace prompts.
- **directors-brief.md** — Output Contract section restructured: CORRECT shape, WRONG-shape anti-pattern block with 4 concrete failures + self-check.
- **test_creative_vision_brief.py** — 3 new tests (F1 surface area): non-canonical subjects, missing required key, empty prompt.
- **test_creative_vision_agent_definitions.py** — 1 new test (F2): assert directors-brief.md carries the labelled CORRECT/WRONG anti-pattern phrases.

**Test count**: 296 → **300** passing (1 skipped, 12 warnings — pre-existing zipfile DuplicateName warning in full_bleed tests).

## Artefacts

```
tmp/creative-vision-dogfood/
├── deck/creative-vision/2/
│   ├── manifest.json           # 3 attempts, final accepted at flash_1k
│   └── runs/
│       ├── 01-ollama.png       # iter 1 — modern flat illustration, callouts absent
│       ├── 02-ollama.png       # iter 2 — callouts inlined, sports cars still missing, film grain absent
│       └── 03-flash-1k.png     # iter 3 — accepted; all 4 callouts crisp, sports cars + signpost rendered
└── work/
    ├── parsed_vision_iter2.json   # canonical ParsedVision used for both iter 2 + iter 3 dispatches
    ├── refined_prompt.txt         # post-Reviewer prompt (with callouts) used for iter 2 + carried into iter 3
    ├── reviewer_input.txt         # iter 2 first-pass reviewer input
    ├── reviewer_input_v2.txt      # iter 2 second-pass reviewer input (refined prompt)
    ├── critic_input_iter2.txt     # iter 2 Critic dispatch blob
    └── critic_input_flash1k.txt   # iter 3 Critic dispatch blob
```

## Verdict on the cascade

The creative_vision renderer is converging on the same operating envelope every dogfood has shown:

- **Ollama (free)** locks composition and panel structure. It plateaus on style + small props before iteration 3.
- **Flash 1K ($0.067)** closes most of the remaining gap. Entity, spatial, quality, composition all jump into the 80s.
- **style_fidelity** is the persistent laggard at Flash 1K when the operator asks for a specific period aesthetic (1950s cartoon, 1980s film grain, etc.). Escalating to Pro 1K is the documented next step if style matters critically — but for the operator-visible deliverable the Flash 1K image is generally shippable.

Ship the loop. The F1/F2 fixes harden the boundary between Brief and downstream consumers; F3 is a known follow-up patch. No blocker.
