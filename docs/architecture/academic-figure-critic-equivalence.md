# Academic-figure critic equivalence testing — methodology

**Status**: Phase 1 active. PR `feat/academic-figure-claude-critic` (deckhand 1.5.2) lands the side-by-side surface; the equivalence verdict is what closes Phase 1.

**Cross-references**:
- Path-B decision context: PR #114 conversation (issue #113 follow-up)
- ADR v2 (paperbanana framing): [`paperbanana-integration-v2.md`](paperbanana-integration-v2.md)
- Loop implementation: imagegen-bridge SKILL.md Step 4.6.1
- Agent contract: [`agents/figure-critic.md`](../../plugins/jack-tar-deckhand/agents/figure-critic.md)

---

## What we're testing

The v1.4.1 academic_figure path delegated the iteration loop to paperbanana. Paperbanana's Gemini-Flash VLM critic decides accept/refine; jack-tar's role is dispatch + manifest. Path B moves the critic decision into jack-tar — the `figure-critic` agent (Sonnet) is now the decision-maker, paperbanana is the renderer.

We want to know: **does Claude-as-critic produce better, equivalent, or worse academic-figure outcomes than paperbanana-as-critic on the same input?**

"Better/equivalent/worse" against three signals:

1. **Decision agreement** — when both critics evaluate the same render, do they reach the same accept/reject verdict?
2. **Final-figure quality** — when the loops run end-to-end (operator gate honoured in both), does the final figure read as good to the operator?
3. **Loop cost** — total Gemini calls + Sonnet calls + paperbanana runs per accepted figure.

## Phase 1: side-by-side instrumentation (what this PR ships)

This PR adds the surface for an operator to run both critics on the same slide and capture both verdicts side-by-side. The flow:

1. Operator marks a slide `academic_figure.critic: "claude"` AND `academic_figure.log_paperbanana_verdict_for_comparison: true`.
2. Orchestrator runs the claude-critic loop (Step 4.6.1).
3. For each iteration, paperbanana renders one image. Paperbanana's own VLM critic ALSO runs (we can't disable it in 0.1.2 — see #213/#214 upstream). Jack-tar parses paperbanana's verdict from stdout.
4. The figure-critic agent receives the image + the paperbanana verdict in its input blob, with explicit "do NOT defer to this" language.
5. The figure-critic returns its own verdict + a boolean `agrees_with_paperbanana_verdict`.
6. Both verdicts persist in the manifest. Operator makes the final decision at the gate.

Over many runs, the operator accumulates a data set of `(image, claude_verdict, paperbanana_verdict, agrees, operator_decision)` tuples.

## The equivalence bar (what closes Phase 1)

We promote Claude-critic to default when **all three** of the following hold across a representative sample (target: ≥15 academic_figure slides, ≥5 distinct figure types):

### Bar 1 — agreement statistic

`agrees_with_paperbanana_verdict == true` on **≥75%** of iterations.

- 100% agreement would mean Claude is a redundant copy of paperbanana's verdict — useless.
- <50% agreement would suggest one critic is systematically wrong (or they're orthogonally good, both signal worth keeping).
- 75-90% is the sweet spot: substantial agreement on easy cases + meaningful disagreement on hard cases where Claude's judgement is the differentiator.

### Bar 2 — operator-decision alignment

When Claude and paperbanana disagree, **the operator agrees with Claude ≥60%** of the time.

This is the load-bearing signal. The operator's "go / no-go" at the gate is the ground truth; whichever critic the operator agrees with more often is the better critic.

A 60% bar (vs 50% / equal) requires Claude to be the *better* critic on disagreements, not merely as-good-as. We're not promoting Claude to default for parity; we're promoting it because it's measurably better.

### Bar 3 — final-figure-quality regression

Final accepted figures from the claude-critic path are **≥ as good** as the paperbanana-critic path on a blinded operator review. Specifically: present the operator a randomised pair of final figures (one from each path) and ask "which is better, or are they tied?" — Claude-critic path wins or ties on **≥50%** of pairs.

The blinded review controls for confirmation bias — the operator might subconsciously prefer the path they spent more interactive time with.

### Phase 1 sample-size minimum

- **≥15 academic_figure slides** that completed the claude-critic loop with side-by-side logging enabled.
- **≥5 distinct figure types** (architecture_diagram, equation, plot, table, algorithm_pseudocode, flowchart, other) represented.
- **At least one slide per figure type** with operator-flagged disagreement.

If after 15 slides we don't have disagreement on every figure type, extend to 25 slides or accept that some types are converged-on (both critics agree → either is fine).

## Phase 2: promote Claude-critic to default

When Phase 1 closes positively:

1. Strategy schema default changes: `academic_figure.critic` defaults to `"claude"` (previously `"paperbanana"`).
2. SKILL.md Step 4.6 (legacy paperbanana-critic path) moves to a "deprecated path" footnote; Step 4.6.1 becomes the canonical flow.
3. Plugin version bump to 1.6.0 (minor — behaviour default change).
4. Operator can still opt back to paperbanana-critic with `critic: "paperbanana"` for the slow-deprecation grace period (1-2 minor versions).

When Phase 1 closes negatively (Claude-critic loses to paperbanana-critic on bars 1-3):

1. Add the data set + analysis to this document.
2. Keep paperbanana-critic as the default.
3. Investigate: is the figure-critic agent definition off? Is Sonnet under-prompted? Move to Sonnet 4.7 / 5.x?
4. Either iterate on figure-critic.md, or close out Path B as a methodology dead end and pursue Path C (collapse academic_figure into creative_vision).

## Phase 3: deprecate paperbanana entirely (Path C)

A more radical step. If during Phase 1/2 the operator finds that the figure-critic's prompt could be enriched to subsume paperbanana's academic-figure-aware prompting, we could skip paperbanana for the render step too — calling cloud-image directly. Out of scope for the current PR.

The Phase 3 bar: figure-critic + cloud-image (no paperbanana) produces final figures that are ≥ paperbanana-rendered figures on a blinded operator review across all 7 figure types.

## What to log per iteration

The manifest entry for each iteration in the claude-critic loop SHOULD carry these fields for Phase 1 analysis (jack-tar writes this directly into the slide's image-manifest entry):

```json
{
  "slide_number": 5,
  "iteration_index": 2,
  "image_path": "tmp/deck/images/run_20260527_120000_abc123/iter_2.png",
  "paperbanana_run_id": "run_20260527_120000_abc123",
  "figure_critic_verdict": {
    "verdict": "refine",
    "per_axis_scores": {"methodology_fidelity": 75, "caption_alignment": 80, "legibility": 70, "figure_type_correctness": 78, "aesthetic_quality": 82},
    "refinement_feedback": "Add the missing 'Attention' block between Encoder and Decoder; the methodology lists three blocks, the figure shows two.",
    "agrees_with_paperbanana_verdict": false
  },
  "paperbanana_side_by_side_verdict": {
    "verdict": "pass",
    "raw_score": 88,
    "captured_from_stdout": true
  },
  "operator_decision": "refine",
  "cumulative_cost_usd": 0.134
}
```

The `operator_decision` field is the ground truth. Disagreement happens when:
- `figure_critic_verdict.agrees_with_paperbanana_verdict == false`
- AND the operator's decision matches one critic, not the other

That's the bar-2 signal.

## Practical operator workflow

To run the equivalence test on a slide:

```json
{
  "slide_number": 7,
  "strategy": "academic_figure",
  "academic_figure": {
    "critic": "claude",
    "figure_type": "architecture_diagram",
    "iteration_cap": 5,
    "log_paperbanana_verdict_for_comparison": true
  }
}
```

Run the imagegen-bridge. The Step 4.6.1 loop fires. Operator gates every iteration. The manifest accumulates the side-by-side data.

After 15+ slides across multiple figure types, run the analysis (a small script TODO — landed in Phase 1.5):

```bash
PYTHONPATH=plugins/jack-tar-deckhand .venv/bin/python -m src.academic_figure_equivalence_report \
  --deck-dir tmp/deck \
  --output equivalence-report.md
```

The report tabulates per-figure-type agreement statistics and operator-decision alignment, and computes the bar-1 / bar-2 / bar-3 thresholds.

## Why this matters

The honest read from the original Path-B decision (PR #114 discussion):

> "The deepest reason our integration hard-codes Gemini isn't technical — it's that paperbanana was framed as a 'sibling orchestrator, external CLI tool' per the ADR v2 framing. We treat it as a black box that owns its loop... The question 'why can't the critic be Claude?' is actually asking whether that black-box framing is right."

Path B is the experiment. Equivalence testing is how we know whether the experiment landed. If Claude-critic measurably beats paperbanana-critic on a representative sample of academic figures, we got the framing right. If it doesn't, we go back to the black-box framing and find a different lever.

Either way, the side-by-side surface this PR ships is reusable: it's the methodology for evaluating "should orchestrator-Claude be the critic for X" on any future paperbanana-like tool integration. The same shape would apply if we asked the same question about, say, an LLM-as-judge for SmartArt selection or a vision-language critic for full-bleed creative slides.

## Open questions for Phase 1 dogfood

1. **Can we reliably parse paperbanana's verdict from stdout?** Paperbanana's CLI uses `rich.console` for output. PR #186 (resume visualizer output fix) suggests the stdout format is in flux upstream. The `Output: <path>` line we already parse for the image path is stable; verdict capture would need a similar grep target. If unstable, fall back to running paperbanana's critic inspect-only OR omitting side-by-side logging.
2. **Does Sonnet over-refine?** Creative_vision dogfood evidence suggests Sonnet critics can be too eager to refine when an image is already shippable. Watch the agreement statistic on the paperbanana-pass + claude-refine quadrant — that's the failure mode.
3. **What's the operator-cost?** Each iteration is one paperbanana render + one Sonnet figure-critic call + one operator gate. For a 4-iteration loop that's 4 + 4 + 4 = 12 interactions per slide. Higher than v1.4.1's 1-2 interactions. Acceptable for high-stakes figures (a paper's hero diagram) but expensive for routine ones.
4. **Should the equivalence-testing flag default on for the first 15 slides?** Or operator-explicit-only? Default-on would build the data set faster; explicit-only respects operator agency. Recommend explicit-only — operators opt into the cost.
