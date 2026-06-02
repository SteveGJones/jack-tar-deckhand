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

---

## Addendum (2026-05-22 → 2026-05-23): operator-driven extension of the same slide

The above section ran to its natural close at $0.067 with a 4-panel cartoon. The operator subsequently reviewed the deliverable and rejected it: *"that is a good cartoon, but it has no flow, I wanted the STYLE of a cartoon, not the 4 panel layout, I wanted to see the FLOWING of the data product."* What followed was an extended cascade across two more prose revisions, a Pro 4K diptych, a methodology rollback, and an operator-driven prompt simplification that finally landed.

### Cascade summary — full slide (14 attempts, $1.016 total)

| Attempt | Prose | Tier | Cost | Cumulative | Outcome |
|---|---|---|---|---|---|
| 1 | v1 (4-panel cartoon) | ollama | $0.00 | $0.000 | refine — sports cars missing, no signpost, modern-flat style |
| 2 | v1 (callouts added) | ollama | $0.00 | $0.000 | refine — style regressed; escalate_tier |
| 3 | v1 | flash_1k | $0.067 | $0.067 | original accept; operator later rejected "not flowing" |
| 4 | v2 (cinematic panorama) | ollama | $0.00 | $0.067 | refine — 4-panel grid despite "NO panels" |
| 5 | v2 (cinematographic rewrites) | flash_1k | $0.067 | $0.134 | refine — still 4-panel grid even with shouted negatives |
| 6 | v2 (architectural-continuity) | pro_1k | $0.134 | $0.268 | Critic abort, gap=prose; Haiku said continuity worked |
| 7 | v3 (customer×3 bookend) | ollama | $0.00 | $0.268 | refine — zone 5 absent at Ollama |
| 8 | v3 | pro_1k | $0.134 | $0.402 | reviewers said zone 5 absent; operator-override: zone 5 was actually in the foreground (F6 reviewer blindspot) |
| 9 | v3 → diptych Frame A | pro_4k | $0.240 | $0.642 | accept (operator initial approval — then withdrawn for methodology audit) |
| 10 | v3 → diptych Frame B | pro_4k | $0.240 | $0.882 | accept (same) |
| 11 | v3 (diptych Frame A v4 rewrites) | ollama | $0.00 | $0.882 | refine — "still one office, not three scenes" — camera-as-unifier rewrite failed |
| 12 | v3 (cinematic montage v1) | ollama | $0.00 | $0.882 | refine — 9-panel grid; "montage" interpreted as comic territory |
| 13 | v3 (**operator-simplified prompt**) | ollama | $0.00 | $0.882 | **pass** — 5 scenes clearly distinguishable; gate passed |
| 14 | v3 (same simplified) | **pro_1k** | $0.134 | **$1.016** | **OPERATOR FINAL ACCEPT** |

**Final image**: `tmp/creative-vision-dogfood/deck/creative-vision/2/runs/21-montage-simplified-pro-1k.png` — a 5-panel cinematic montage at Pro 1K with chyrons `SALES` / `FINANCE` / `CUSTOMER STATUS` / `DISTRIBUTION` / `FULFILLMENT FAILURE`; data-product (napkin → typed invoice) visibly traceable across panels; customer character (salt-and-pepper hair, tortoiseshell glasses) recognisable across his three appearances (bar / confused with invoice / shouting on phone at dusk).

**Pro 4K diptych** (`09-frame-a-pro-4k.png` + `10-frame-b-pro-4k.png`, $0.480) was rolled back from `final` per operator decision — the artefacts remain in the runs/ directory as audit evidence of the methodology gap.

### Findings — added to the F-list

#### F6 — Reviewer blindspot on foreground-placed elements (NEW)

Both reviewers reported "zone 5 absent" on the Pro 1K v3 render. The operator immediately saw that the zone 5 customer-on-phone-shouting *was* present — but in the foreground, not at the right edge as the prompt requested. The reviewers' "absent" verdict was actually a positional misread: they expected zone 5 at the right edge and didn't recognise it when it appeared centre-foreground.

**Proposed fix (deferred)**: image-reviewer and Director's Critic agent definitions should be updated to scan for prompted entities anywhere in the frame, not just the prompted spatial slot. The "where is X?" check should be a presence check first, position check second.

#### F7 — Critic verdict-coherence violation (was F3, retained)

Already captured — Critic returning `pass` with `style_fidelity: 72` on the v1 final. Fix proposed: add semantic validation to `critic.parse_critic_output` paralleling F1.

#### F8 — Diptych pivot as a strategic cascade move (NEW)

When a single-image composition has reached its model-capability ceiling for a multi-zone narrative, *splitting per-image complexity in half via a deliberate diptych* (zones 1-3 in Frame A, zones 4-5 in Frame B) is a viable cascade pattern beyond single-image refinement. Each frame has fewer zones → character consistency holds → composition can breathe. The diptych itself can mirror a before/after narrative (order placed / order failed) in a meaningful way.

This is a documented strategic move for future complex-narrative dogfoods. Note: it did NOT solve the data-supply-chain composition (the operator subsequently rejected the diptych framing in favour of a 5-panel montage), but it is a valid tool when the multi-zone problem dominates.

#### F9 — Tier overspend symptom (NEW — closed in this PR via rollback)

The Pro 4K diptych ($0.480) was conservatively over-spent: the Critic recommended either *(b) split into two frames at lower per-image complexity* OR *(c) Pro 4K with refined prompt*, and I conflated them — applied both at once. The diptych structure made each frame simpler; Pro 1K would have sufficed for that complexity (3-zone + 2-zone). Pro 4K was the unbudget-disciplined choice.

The methodology lesson — that lower per-image complexity is the load-bearing lever, not the tier bump — is the takeaway. The Pro 4K diptych was rolled back from `final` per operator decision; the artefacts stay in runs/ as audit evidence.

#### F10 — Skipped operator gate at free→cost transition (NEW — root cause for F9, closed in this PR)

**THE HEADLINE FINDING.** The whole reason Ollama exists in the cascade is to give the operator a free preview that they sign off on before any money is spent. During this dogfood, this gate was skipped three times:

1. **v2 cascade**: rendered Ollama v2, sent to Critic, got `escalate_tier`, immediately rendered Flash 1K. Operator never saw the Ollama draft.
2. **v3 cascade**: skipped Ollama entirely; went straight to Pro 1K. Operator asked to see the Ollama draft AFTER the cloud spend.
3. **Diptych**: rendered Frame A and Frame B at Pro 4K immediately. No Ollama drafts. No gate.

The Critic's `escalate_tier` verdict is **advisory, not authorisation to spend**. Only the operator can know whether a draft is structurally on-track for what they want; the Critic evaluates against the prose but not against operator intent. Letting the Critic drive cloud spend turns the cascade from "human-in-the-loop with a free preview" into "agent loop that bills the operator."

The methodology fix is landed in this PR:
- `CLAUDE.md` — new MANDATORY section "Operator gate at every free→cost cascade transition (issue #105, F10)"
- `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md` — new Step H.1 enforcing the gate at the cascade boundary; cost-to-cost transitions exempt; bypass conditions explicit and narrow
- `plugins/jack-tar-deckhand/agents/prompt-reviewer.md` — paired enhancement (see F11)

After the gate was reinstated, the cascade caught three consecutive structural prompt failures at the free tier before any cloud spend: one-room fusion (attempt 11), 9-panel-grid (attempt 12), and finally the operator-driven simplification breakthrough (attempt 13). Those three free Ollama renders saved ~$0.40 of cloud spend that would have demonstrated the same failures at higher resolution.

#### F11 — Prompt simplification when fighting model bias (NEW — methodology insight closed in this PR)

After 10+ prompt iterations from me (each more elaborate than the last, growing to ~1,100 words for the montage attempt, with stacking negative directives like "NO panels", "NO grid", "NOT a storyboard"), the operator rewrote the prompt as a six-line description that simply embraced the 5-panel structure rather than fighting it:

```
A 16:9 ultra-widescreen 5-panel image, 1980s Wall Street cinematic style, 35mm film grain. Top neon chyrons read: SALES, FINANCE, CUSTOMER STATUS, DISTRIBUTION, FULFILLMENT FAILURE.
Panel 1: Neon bar, older customer drinking, young rep writing on napkin.
Panel 2: Cyan office, rep handing napkin to female worker.
Panel 3: Amber office, customer looking confused at invoice.
Panel 4: Night loading dock, lost truck driver pointing at blank signpost.
Panel 5: Dusk office, customer furious on phone, crumpling invoice.
```

This prompt landed what my 1,100-word elaboration could not.

**The methodology insight**: when prompt iteration N has elaborated to address Critic feedback and composition is still failing, the right move can be to *shorten and simplify* the prompt, not add more directives. The Prompt Reviewer currently only checks "does the prompt have enough?" — entity coverage, style cues, density. It does NOT check "does the prompt have too much?" or "is the prompt fighting a model bias by stacking negative directives?"

The methodology fix is landed in this PR:
- `plugins/jack-tar-deckhand/agents/prompt-reviewer.md` — new check 5 "Over-elaboration / fighting-the-model bias check (F11)" with concrete signals: >400 words AND same failing axis as two iterations ago; stacking negative directives; internal contradictions; word-count growing without verdict change.
- `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md` Step H.1 paragraph 4 — at every operator gate, when the elaborated prompt has hit the over-elaboration heuristic, offer the operator a simplified prompt as an alternative.
- `CLAUDE.md` — new MANDATORY section "Prompt simplification check on stalled cascades (issue #105, F11)" — heuristic + counter-move documented.

This is paired with F10: the operator gate is where simplification offers naturally surface, because the operator is the one with the visual taste to choose between elaborated and simplified.

### Other narrative observations from this addendum

- **Chyron rename**: the operator's six-line prompt used `SALES` / `FINANCE` / `CUSTOMER STATUS` / `DISTRIBUTION` / `FULFILLMENT FAILURE` as the chyron labels — describing the *data state* at each panel rather than just the organisational function. This was sharper than my `SALES` / `FINANCE` / `CUSTOMER` / `SUPPLY CHAIN` and is worth carrying forward in future supply-chain visualisations.
- **The customer emotional arc** (relaxed at bar → confused with invoice → furious on phone) makes the failure feel *earned*. The middle "a bit confused" beat was operator-introduced and is what gives the narrative its hinge. Useful for similar 5-step narrative compositions.
- **Cinematic montage vs split-screen vs panorama vs grid** — the operator's final-accepted framing was a 5-panel image (effectively a stylised grid) that they explicitly endorsed because the photoreal Wall Street treatment and the data-product traceability across panels did the cinematic work that "single panorama" couldn't. Sometimes the model's natural framing IS the right framing — fighting it is the failure mode.

### Methodology artefacts shipped in this PR

| Artefact | Purpose | Tied to |
|---|---|---|
| `CLAUDE.md` — Operator gate MANDATORY section | Bind orchestrator behaviour at free→cost boundary | F10 |
| `CLAUDE.md` — Prompt simplification MANDATORY section | Heuristic for over-elaboration; pair with operator gate | F11 |
| `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md` — Step H.1 | Concrete enforcement of operator gate + simplification offer | F10 + F11 |
| `plugins/jack-tar-deckhand/agents/prompt-reviewer.md` — Check 5 | Prompt Reviewer raises `over_elaboration` issue when signals fire | F11 |
| `tmp/creative-vision-dogfood/deck/creative-vision/2/manifest.json` | Full audit trail of 14 attempts, finalised on Pro 1K montage | All |
| This addendum | Methodology learning | F6 / F8 / F9 / F10 / F11 |

### Status

**Slide deliverable**: `runs/21-montage-simplified-pro-1k.png` accepted by operator 2026-05-23.
**Total slide spend**: $1.016 of $1.50 envelope ($0.484 remaining).
**Tests**: 300/300 passing (1 skipped) — unchanged from pre-addendum baseline; the F10 + F11 fixes are in CLAUDE.md / SKILL.md / agent definitions (no new code tests required).
**PR**: #107 — methodology fixes land alongside the manifest finalisation.

### Architectural decision (2026-05-23): Prompt Simplifier as F11's missing piece

The F11 fix in this PR shipped the *heuristic* (over-elaboration check in the Prompt Reviewer) and the *gate-level invitation to simplify* (CLAUDE.md + SKILL.md Step H.1 paragraph 4), but didn't ship an *agent whose job is to produce the simplified prompt*. During the dogfood the operator did the simplification by hand.

Operator review of the dogfood proposed three options:
- A. Three prompt-mutation agents (Expand / Maintain / Shrink) giving the reviewer alternatives
- B. Just the simplification heuristic that this PR shipped
- C. Two agents — Director's Brief (existing, elaboration) + a new **Prompt Simplifier** (Shrink counterpart), dispatched in parallel at the operator gate when F11 fires, both prompts surfaced to the operator who picks

**Operator decision: Option C.** Two clean single-responsibility agents; Maintain implicit (the Brief can choose not to grow when it judges that's right); the operator gets a real choice exactly when they need it; no over-engineering until dogfood evidence demands a third agent.

Tracked as issue [#112](https://github.com/SteveGJones/jack-tar-deckhand/issues/112) — explicitly scoped to a follow-up PR (not this PR) to keep the F1/F2/F10/F11 methodology fixes clean and auditable. The Prompt Simplifier will be the first dogfood-driven agent addition to the creative-vision cascade since its founding implementation in PR #107.
