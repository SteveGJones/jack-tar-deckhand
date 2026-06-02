# 2026-05-21 — Creative Vision Renderer first cascade dogfood (#105)

## Scope

End-to-end exercise of the new creative_vision pipeline at Ollama + Flash 1K tiers, driving the multi-agent loop manually (the agents were defined in this session and aren't yet registered as proper subagent types). One slide, one vision prose (the sun-phases founding example from #105), budget capped at $0.30 with `allowed_ceiling: flash_1k`.

The aim was the dogfood the operator called out — **produce an actual rendered image and verify the cascade economics work**. We did not stop at "infrastructure ready."

## Cascade summary

| # | Tier | Cost | entity | spatial | style | quality | composition | Verdict | gap_location |
|---|------|------|--------|---------|-------|---------|-------------|---------|--------------|
| 1 | ollama | $0.00 | 45 | 62 | 72 | 70 | 55 | refine_at_tier | prompt |
| 2 | ollama | $0.00 | 52 | 70 | 60 ▼ | 72 | 68 | escalate_tier | tier |
| 3 | flash_1k | $0.067 | **78** | **85** | **88** | **84** | **80** | refine_at_tier | prompt |

**Total spend: $0.067** (out of $0.300 budget; $0.233 remaining).
**Final image**: `runs/03-flash-1k.png`. All five named entities present; painterly oil/watercolour style achieved; one more Flash 1K refinement could close the entity-fidelity gap on dramatic-crescendo framing.

## What we proved

### 1. Cascade economics work as designed

The single jump from Ollama (free) to Flash 1K ($0.067) produced:
- entity_fidelity 52 → 78 (+26)
- style_fidelity 60 → 88 (+28) — the axis Ollama plateaued on
- composition 68 → 80 (+12)
- quality 72 → 84 (+12)
- spatial_fidelity 70 → 85 (+15)

The "validate composition at free tier, escalate when model ceiling is reached" pattern delivered exactly what the cascade design promised. Style_fidelity in particular — which Ollama could not improve no matter how the prompt was refined — jumped 28 points on the first Flash render.

### 2. Plateau detection identifies tier ceiling correctly

Ollama iter 2 returned `escalate_tier` with `gap_location: tier`, citing "style + entity-merging are Ollama model ceiling issues." This is exactly the cascade's job — recognise when the bottleneck is the model and stop wasting iterations.

`plateau_signal` was `false` at iter 2 (scores DID change, mostly up; only style went down 12). The Critic over-rode plateau detection by judging `gap_location: tier` based on capability assessment, not just numeric flatness. This is the right behaviour for the agent.

### 3. Brief preserves operator intent over Critic suggestions

At Ollama iter 1, the Critic recommended "specify neutron star as tiny intensely bright pinpoint smaller than protostar... emphasize collapse-after-supernova arc." That contradicts the operator's prose ("each visibly larger and more dramatic" + "scientifically evocative not literal"). At iter 2, the Brief correctly resolved the tension by framing the neutron star as "most dramatic and luminous of all five" — preserving the operator's "each larger" intent while addressing the Critic's real concern (entity unrecognisability).

The Director's Brief agent's Principle 1 ("operator's prose is sacred") held under genuine adversarial pressure from a downstream agent. This is the load-bearing property the agent prompt was designed to enforce, and it worked.

### 4. Named-entity preservation holds across iterations + tier transition

Across all three attempts (Ollama × 2, Flash × 1), all five named entities (protostar, main sequence, red giant, supernova, neutron star) appeared by name in every prompt with their correct spatial slots. No entity was silently dropped during refinement — the failure mode the entire Brief↔Reviewer loop exists to catch did not occur in this dogfood.

### 5. Per-axis scoring drives targeted refinement

The Critic's per-axis breakdown enabled the Brief at iter 3 (Flash tier) to address style + composition + entity discrimination simultaneously — rather than guessing at a global improvement. The Flash iter 1 prompt was visibly more specific because the Brief had concrete signals to act on.

## Findings (issues for follow-up)

These are real gaps surfaced by the dogfood — not theoretical concerns from review of the spec.

### F1 — ParsedVision schema is documentation, not enforcement (high)

**Observed**: The Brief at Ollama iter 1 returned `spatial_directives.named_relationships` as a string instead of an array. The Brief at Ollama iter 2 returned a parsed_vision missing `schema_version`, `spatial_directives`, `composition`, `delivery`, `text_density_warning`, AND used `"position"` instead of `"spatial_slot"` on each subject. Nothing in the pipeline runtime-validates `parsed_vision` shape between iterations — neither the Brief output parser nor the Prompt Reviewer.

**Impact**: Downstream consumers (Critic, manifest, iterate-slide) silently absorb malformed intermediates. The agent's contract drift would not be caught until someone schema-validates manually.

**Fix candidates**:
- (a) Have `brief.parse_brief_output` schema-validate the parsed_vision before returning (cheap, immediate)
- (b) Extend Prompt Reviewer remit to include structural drift detection
- (c) Add a separate schema-validation gate between Brief and Reviewer

Probably (a) — smallest change, catches the bug at the right boundary. Open as a separate issue.

### F2 — Brief at Flash tier returned prompt OUTSIDE the JSON fence (high)

**Observed**: At Flash 1K iter 1, the Brief returned a fenced JSON block containing only `parsed_vision`, followed by a separate markdown code block labelled `**prompt:**`. The `parse_brief_output` regex expects both keys inside the SAME fence — this output would have failed parsing.

**Impact**: Brief output format is fragile under tier transitions. The agent may interpret "more detailed prompt for Flash" as licence to use richer markdown structure, breaking the contract.

**Fix candidates**:
- Tighten the agent prompt's Output Contract section to explicitly require BOTH keys in the SAME fenced block, with an anti-pattern showing the wrong shape
- Make `parse_brief_output` more permissive (read multiple JSON fences AND adjacent code blocks looking for the prompt)
- Add a parse-failure fallback that requests a regenerated output

Issue to file. Tightening the agent prompt is the cleaner fix (don't make the parser forgive bad output; make the output disciplined).

### F3 — Reviewer-vs-Critic style disagreement (medium)

**Observed**: At Ollama iter 2, image-reviewer said "painterly style consistent throughout" (pass, 0.88 confidence). Director's Critic said "No visible brushstrokes — reads as digital cosmic render, not oil-painting" (style_fidelity 60/100). Same image, two reviewers, opposite verdicts on style.

**Impact**: The two-gate design (image-reviewer for visual quality, Critic for vision fidelity) creates room for inconsistent signals. The Critic's verdict drives cascade decisions; the image-reviewer's pass doesn't override but might mislead.

**Root cause**: image-reviewer's bar is "wrong style entirely" (low threshold); Critic's bar is "explicit style consistently applied" (high threshold). Both are correct per their definitions — the gap is operator expectation calibration.

**Fix candidates**: Document the calibration gap in both agent prompts. Possibly add a "style cue: explicit oil-paint texture required" annotation that image-reviewer reads from the strategy entry.

### F4 — Prompt Reviewer's scope is narrow (medium)

**Observed**: At Ollama iter 2, the Brief returned a malformed parsed_vision. The Prompt Reviewer ran, looked at the prompt-vs-prose fidelity, and passed. It did not flag the structural drift because the agent's "What to check" list is prompt-fidelity-only.

**Impact**: The Reviewer is genuinely doing its job (the prompt was fine for the prose); but the system as a whole lacks a gate that catches structural failures in the parsed_vision contract.

**Fix candidates**: Combined with F1 — let the dispatch helper schema-validate, keep Reviewer's scope narrow. OR extend the Reviewer's "What to check" to include "parsed_vision matches schema" as a final mechanical step.

### F5 — Critic's gap_location heuristic conflated cause and recommendation (low)

**Observed**: At Ollama iter 1, the Critic identified a real semantic gap (operator says "each larger and more dramatic" but model rendered the rightmost element as a galaxy/nebula, not a star). The Critic's recommended_action included "specify neutron star as tiny intensely bright pinpoint smaller than protostar" — which contradicts the operator's prose. `gap_location` was `prompt`. The Brief had to OVERRIDE the Critic's recommendation to stay faithful to operator intent.

**Impact**: The Critic's "gap_location" mechanism conflates "where the gap LIVES" (prose vs prompt vs tier) with "what we should DO about it." The Critic correctly identified `prompt` as the location, but the recommendation drifted toward scientific accuracy (the Critic's own bias) when the prose explicitly disclaimed it ("scientifically evocative not literal").

**Fix candidates**: Tighten the Critic agent prompt's gap_location semantics — make it clear that gap_location IS the routing signal, but the recommended_action must STAY WITHIN operator's prose. Add an anti-pattern in the Critic agent for "do not recommend changes the operator's prose would forbid."

### F6 — Brief at Flash tier over-shot the 180-word cap (low)

**Observed**: The Flash tier prompt at iter 3 was 182 words. The agent's tier calibration says `cloud_flash` ≤180 words. Minor — the prompt is content-rich and the prose-fidelity-pass result suggests the over-shoot didn't degrade quality.

**Impact**: None observed in this dogfood. Long-prompt regression would surface in metrics over a wider population of runs.

**Fix**: Add a soft warning in `build_brief_input` or a Prompt Reviewer check for prompt length. Probably defer.

## Operator feedback channels — exercised partially

The /iterate-slide three-channel branch (revise_prose, refine_prompt, escalate_tier) was NOT exercised in this dogfood. The cascade drove itself via the orchestrator's `decide_next_action`. The channels are the operator surface, not the cascade's internal surface.

What this means: the iterate-slide branch is structurally in place but its first live exercise should happen during a real conductor pipeline run, not this isolated cascade dogfood.

## Bridge marker (future scope) — NOT exercised

The dogfood's vision (sun phases) is a single full-bleed image. The future `CREATIVE-VISION:identifier` bridge marker for in-slide creative_vision didn't enter scope. The pipeline's producer/consumer boundary held — we produced a vision-faithful image, the assembly path is downstream.

## Recommendations

### Block PR on these (high-impact gaps)

- **F1**: Add schema validation to `brief.parse_brief_output`. ~30 min, prevents an entire class of silent contract drift.
- **F2**: Tighten the Director's Brief agent prompt's Output Contract to explicitly forbid prompt-outside-fence. ~10 min, prevents parse failures at tier transitions.

### File but don't block

- **F3** (reviewer calibration), **F4** (Reviewer scope), **F5** (Critic recommendation drift), **F6** (Flash prompt length cap)

### Defer to v1.1+

- Comprehensive `gap_location` calibration across more visions
- Plateau detection tuning (this dogfood didn't trigger plateau_signal even when escalation was warranted — the Critic chose tier escalation on capability grounds instead)
- iterate-slide three-channel live exercise

## Conclusion — do we ship?

**Yes, with F1+F2 fixed first.** The cascade demonstrably works. The agents produce calibrated, useful output. The economics deliver. The named-entity preservation property holds under refinement and tier transition pressure. The operator-intent-over-Critic-suggestion balance worked exactly as designed in Principle 1 of the Brief agent.

The two fixes (F1, F2) are small and high-leverage. After those, the PR is justified — the infrastructure runs, the design works in practice, and the remaining findings are tuning opportunities rather than fundamental gaps.

## Artifacts produced

- `tmp/creative-vision-dogfood/deck/creative-vision/1/runs/01-ollama.png` — Ollama iter 1 (entity 45)
- `tmp/creative-vision-dogfood/deck/creative-vision/1/runs/02-ollama.png` — Ollama iter 2 (entity 52, escalate)
- `tmp/creative-vision-dogfood/deck/creative-vision/1/runs/03-flash-1k.png` — Flash 1K iter 1 (all axes ≥78, final accepted)
- `tmp/creative-vision-dogfood/deck/creative-vision/1/manifest.json` — full cascade history with versioned prose, 3 attempts, final block, iterate_slide_hooks state

## Cross-references

- Spec: [docs/superpowers/specs/2026-05-21-creative-vision-renderer-design.md](../specs/2026-05-21-creative-vision-renderer-design.md)
- Plan: [docs/superpowers/plans/2026-05-21-creative-vision-renderer.md](../plans/2026-05-21-creative-vision-renderer.md)
- ADR: [docs/architecture/creative-vision-renderer.md](../../architecture/creative-vision-renderer.md)
- Issue #105: https://github.com/SteveGJones/jack-tar-deckhand/issues/105
