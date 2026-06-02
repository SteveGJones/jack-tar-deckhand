# 2026-05-23 — Creative Vision Renderer · Agentic Naval Academy dogfood (#105)

## Scope

Third creative_vision dogfood, run immediately after the methodology fixes from the data-supply-chain dogfood landed (F10 operator gate + F11 simplification heuristic, both in PR #107). This dogfood was a direct test of whether the gate + simplification discipline actually changes outcomes on a fresh slide.

The vision: an "Agentic Naval Academy" passing-out parade. Four AI-brand-aligned ships moored in the background (OpenAI shiny white mega yacht, Anthropic sleek beige hunter-killer attack ship, SAP industrial oil tanker, Google massive neon cruise ship), four regimental blocks of humanoid AI androids in the foreground arranged on a parade square, decorated human admirals on a reviewing podium, four android Sergeant Majors as the Academy's training cadre.

Single coherent ceremonial scene at one location at one moment — fundamentally different from the multi-scene narrative of the data-supply-chain. The composition risks here are not "multi-zone fusion" but rather: character-count, four-uniform differentiation, brand-iconography on ships, banner text fidelity.

Budget: **$0.50** with `allowed_ceiling: pro_1k` initially. Operator elected to escalate to Pro 2K for the final, which the cloud module reported at $0.134 (interestingly lower than the $0.193 in our cascade.py TIER_COSTS table — see "Surprises" below).

## Cascade summary — 7 attempts, $0.268 total spend

| # | Prose | Tier | Cost | Outcome |
|---|---|---|---|---|
| 1 | v1 | ollama | $0.000 | refine — crews are human sailors not androids; composition facing wrong direction |
| 2 | v2 (camera+androids) | ollama | $0.000 | refine — not four clear regimental blocks; need parade-square |
| 3 | v2 (elaborated to 516 words) | ollama | $0.000 | **refine — F11 over-elaboration symptom: ships REGRESSED, blocks still merged** |
| 4 | v2 (F11 simplified to 136 words) | ollama | $0.000 | **pass at Ollama** — composition holds with brevity |
| 5 | v2 simplified | **flash_1k** | $0.067 | refine — "almost perfect" but crews not all android, Sgt Majors human |
| 6 | v2 (CAST clarified: only admirals human) | flash_1k | $0.067 | **pass** — operator: "Excellent" |
| 7 | v2 (CAST clarified) | **pro_2k** | $0.134 | **OPERATOR FINAL ACCEPT** |

**Final image**: `tmp/creative-vision-dogfood/deck/creative-vision/3/runs/07-pro-2k-v5-final.png`
**Total cost**: $0.268 of $0.50 envelope ($0.232 remaining).
**Operator gates fired**: 6 (every Ollama draft + every Flash render). Zero gates skipped.

## What we proved — F10 and F11 work in practice

### F10 operator gate caught two real issues at the free tier

Iteration 1 surfaced for operator review at the gate. Operator flagged: "crews are people not AI agents (androids), should be facing TOWARDS the ships, podium should be facing TOWARDS the camera." Two completely real corrections that would have shipped at Pro 1K cost if the gate had been skipped.

**This is what F10 is for.** The Critic agent evaluates against the prose's text; it cannot know whether "agentic AI crews" was meant literally (androids) or figuratively (people running AI agents). Only the operator can. The gate exists to catch that.

### F11 simplification caught the third-iteration regression

Iteration 3 (prompt grown to 516 words from v1's 269) regressed the ships AND still didn't fix the regiment differentiation — classic F11 over-elaboration symptom. The simplification reset (516 → 136 words, embracing "four square regimental blocks" positively rather than fighting "not one merged mass") unblocked composition immediately on the very next Ollama draft.

**This validates the F11 heuristic.** When prompt iteration is failing AND word-count has grown without verdict improvement, the right move is to shorten and embrace, not lengthen and fight. The Prompt Reviewer's new over-elaboration check (Check 5 in `prompt-reviewer.md`) would have flagged this; in this run I reached for the simplification manually because the heuristic was fresh in mind. The forthcoming Prompt Simplifier agent (issue #112) will close this loop.

### Operator-chose-Flash-over-Pro discipline

After v4 simplification passed at Ollama, the operator explicitly chose Flash 1K ($0.067) rather than Pro 1K ($0.134) — "no need to jump straight to Pro." This saved $0.067 and the result was good enough to land the next gate ("almost perfect"). The F10 gate gave the operator the opportunity to make that frugal call.

**Pattern**: when the Ollama draft is structurally good, try the cheaper cloud tier first. Pro is for the final polish or for fixing specific axes that Flash can't.

## Surprises and observations

### Cloud module reported Pro 2K cost as $0.134, not $0.193

The cascade.py `TIER_COSTS` table has `pro_2k: 0.193` but the actual `generate_cloud_image` call returned `cost_usd: 0.134`. Either:
- Google's actual API pricing for Pro 2K has dropped since the cascade.py table was set
- The `estimate_google_cost` function in the cloud module has different per-tier pricing than the cascade.py orchestrator
- Both are slightly out of date

Action: file a follow-up to reconcile pricing between `plugins/jack-tar-cloud/src/generate_cloud_image.py::estimate_google_cost` and `plugins/jack-tar-deckhand/src/creative_vision/cascade.py::TIER_COSTS`. They should agree on a single source of truth.

### The single-scene composition is the model's friend

This slide rendered in 7 attempts to a finalised acceptance, vs slide 2's 14 attempts. The difference: this is **one coherent ceremonial scene at one location at one moment in time**. The model handles this naturally. The data-supply-chain slide was a multi-scene narrative across time which the model has hard structural priors against (collapse-to-fused-room OR grid-to-N-panels). When the operator's vision fits the model's natural composition territory, the cascade flies.

**Methodology takeaway**: at strategy-map time, the deck-conductor should ASK "is this slide a single-moment scene or a multi-scene narrative?" Single-moment scenes are creative_vision-friendly; multi-scene narratives need the operator forewarning that iteration counts will be 2-3× higher.

### Character-count is manageable up to ~40 distinct figures in formation

The Pro 2K final renders ~100+ android figures in four regimental blocks (~25 each), plus 4 Sgt Majors, plus 6 admirals on the podium, plus 4 ships in the background. The model handled this scale cleanly because the figures are in regimental formation (highly structured, repetitive — easier for the model to render than 100 individual people in chaotic arrangement) and the camera distance is wide enough that per-figure detail is naturally low.

**Methodology takeaway**: formation/uniform compositions scale better than individual-character scenes for creative_vision. Naval parade, marching band, military review, congregation — all good fits. Cocktail party with 30 distinct named guests — bad fit.

## NEW FINDING — F12: Creative_vision review is image-level, not slide-level

This is the load-bearing methodology insight from this dogfood, surfaced by the operator after acceptance:

> "It feels like these images need a human review/insight on the generation OF THE IMAGE not the slide in a way that is different to our standard process."

### The asymmetry

**Standard imagegen-bridge flow** (composed slides, backdrop, full_render): the image is an *illustration* on a slide. Operator's primary review is "does this slide work in the deck?" — slide-level review. Individual images get spot-checked at the manifest level by image-reviewer; deck-level review (presentation-reviewer) catches anything else.

**Creative_vision flow**: the image *IS* the slide. The visual carries the conceptual weight by itself. Every detail matters — wrong character types, wrong composition, wrong props all break the slide. Review must be **per-image**, not per-slide. This dogfood needed 7 attempts × 6 operator-gate touchpoints; slide 2 was 14 attempts × ~10 gate touchpoints. Standard composed slides are 1-2 renders with 0-1 operator interactions.

### Practical implications for slide-deck integration

1. **Time and cost asymmetry**: a deck with 20 composed slides + 3 creative_vision hero slides has very different review economics than 20 composed slides. Each creative_vision slide absorbs 5-10 operator-gate interactions and $0.25-$1.50 of cloud spend. A deck of "all creative_vision" would take a day per slide and would not scale.

2. **Strategy-map approval needs per-creative-vision-slide cost surfacing**: when strategy_map flags a slide as creative_vision, the deck-conductor should explicitly tell the operator at strategy-approval time: *"Slide N is creative_vision — expect 3-7 operator gates and ~$0.20-$1.50 cloud spend on this slide alone."* Currently strategy-map approval is a single yes/no for the whole deck; insufficient granularity.

3. **Per-image operator gate must be default for creative_vision (not just at free→cost)**: the F10 gate landed in PR #107 fires at the free→cost boundary across-the-board. For creative_vision slides specifically, the gate must fire at EVERY iteration regardless of cost transition — operator needs to see every render of a creative_vision image. SKILL.md updated in PR #107 to reflect this.

4. **Pre-deck creative_vision sprint phase**: the deck-conductor flow should run all creative_vision slides BEFORE composed slides. Operator focuses on creative review first (deep, per-image, slow), then standard slides come through faster paths. Separates concerns; prevents creative_vision context-switching from contaminating standard slide assembly.

5. **Cross-slide creative anchors**: when a deck has multiple creative_vision slides sharing a recurring character or visual style (e.g., "the customer" character appearing in slides 3 and 7), capture them in a deck-level `creative-anchors.json` file referenced by each slide's prompt. Not needed for slide 2 or 3 (they're separate stories) but blocking for any multi-slide creative_vision usage.

### Status — GA-blocking

Per operator: **creative_vision v1.5.0 is NOT GA until the deck-conductor enhancements above are implemented.** PR #107 ships creative_vision as a tested-but-not-GA feature; the GA-blocking work lands in a follow-up PR tracked in [issue #113](https://github.com/SteveGJones/jack-tar-deckhand/issues/113) (forthcoming).

## Methodology artefacts shipped in this dogfood

| Artefact | Purpose | Status |
|---|---|---|
| `tmp/creative-vision-dogfood/deck/creative-vision/3/manifest.json` | Full audit trail of 7 attempts | LANDED (local-only — tmp is gitignored) |
| `runs/07-pro-2k-v5-final.png` | Final Pro 2K accepted deliverable | LANDED |
| This dogfood log | Methodology evidence | LANDED in PR #107 |
| `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md` — creative_vision per-iteration gate | Per-image gate for creative_vision strategy | LANDED in PR #107 |
| GA-blocking tracked issue (#113) | Deck-conductor enhancements queued | LANDED in PR #107 |
| Deck-conductor enhancements implementation | GA-blocker | NEW PR — work starting immediately after this PR closes |

## Status

**Slide deliverable**: `runs/07-pro-2k-v5-final.png` accepted by operator 2026-05-23.
**Total slide spend**: $0.268 of $0.50 envelope ($0.232 remaining).
**Operator gates**: 6 fired, 0 skipped. Methodology discipline confirmed.
**F10 + F11 validation**: both rules caught real issues that would have shipped at cloud cost without them. F10 caught two operator-intent corrections at gate 1; F11 caught the v3 over-elaboration regression and unblocked composition via simplification.
**F12 surfaced**: creative_vision review is image-level not slide-level; deck-conductor methodology requires changes for GA. Tracked at #113.
