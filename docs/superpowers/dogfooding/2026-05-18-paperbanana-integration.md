# Dogfood — paperbanana integration E6 gate

**Date:** 2026-05-18
**Plan:** [docs/superpowers/plans/2026-05-18-paperbanana-dispatch-refactor.md](../plans/2026-05-18-paperbanana-dispatch-refactor.md) §4
**Branch:** `feat/v1.4-push-and-paperbanana`
**Tracking issue:** [#94](https://github.com/SteveGJones/jack-tar-deckhand/issues/94)
**Gate outcome:** ✅ **PASS** — figure rendered, manifest correct, visual review passed, $0.14 actual spend (under $0.30 cap)

---

## 1. What we tested

We exercised the post-refactor paperbanana dispatch chain end-to-end by having paperbanana itself generate the figure that documents the jack-tar-deckhand system architecture. Meta-appropriate dogfood: paperbanana renders the figure that explains how jack-tar dispatches to paperbanana.

**Subject of the figure:** The jack-tar-deckhand 5-plugin architecture — orchestrator + 4 specialised engine plugins + peer superpower-bridge wrapper + optional paperbanana CLI for academic figures.

**Methodology context** (paperbanana's `source_context` arg): A 5-paragraph, ~480-word architectural description naming the 11 user-facing skills, 6 AI persona agents, 4 engine plugins (with their underlying providers), the peer bridge plugin, and the paperbanana external tool. Saved to [`2026-05-18-paperbanana-methodology-input.txt`](2026-05-18-paperbanana-methodology-input.txt) for traceability.

**Caption** (paperbanana's `caption` arg): "Jack-Tar Deckhand: orchestrator + 4 engines + optional paperbanana CLI"

---

## 2. The dispatch chain that fired

We drove the dogfood through the real refactored helpers, not a synthetic command. Sequence:

1. **`is_paperbanana_available()`** — returned `True` (paperbanana pip-installed in jack-tar's venv via `pip install -e ~/Documents/Development/paperbanana`).
2. **`build_dispatch_payload(slide, output_dir=…)`** — returned `PaperbananaDispatch(available=True, slide_number=1, output_dir='/tmp/jack-tar-dogfood', args={4-key dict})`. Verified `args` shape: `{aspect_ratio: "16:9", caption: "...", iterations: 2, source_context: <3481 char methodology>}`. The `_build_source_context_from_slide` helper used `slide["methodology_context"]` directly (priority 1 in the synthesis chain).
3. **CLI invocation** (the exact command the imagegen-bridge will emit after the bridge SKILL.md follow-up lands — see §6):
   ```
   paperbanana generate \
     --input /tmp/jack-tar-dogfood/methodology.txt \
     --caption "Jack-Tar Deckhand: orchestrator + 4 engines + optional paperbanana CLI" \
     --aspect-ratio 16:9 \
     --iterations 2 \
     --vlm-provider gemini --vlm-model gemini-2.5-flash \
     --image-provider google_imagen \
     --image-model gemini-3.1-flash-image-preview \
     --output /tmp/jack-tar-dogfood \
     --budget 0.25
   ```
4. **`build_manifest_entry(dispatch, dispatch_succeeded=True, output_path=…, content_hash=…)`** — produced the full manifest entry with `paperbanana_run_id` extracted via regex from the returned path and `paperbanana_args` snapshot.

---

## 3. Outcome

| Metric | Value |
|---|---|
| Wall time | **3 min 20 s** (200 s — 2 iterations, retrieval + planning + styling + 2× visualizer + 2× critic) |
| Tracked spend | $0.0085 (VLM only — image pricing missing from paperbanana's table, see upstream #213) |
| True spend | **~$0.14** (Flash 1K × 2 iterations × $0.067 + 11 VLM calls at ~$0.001 each) |
| Cost cap on the CLI | $0.25 (`--budget 0.25`); never approached |
| Image dimensions | 2752 × 1536 (16:9 honoured ✓) |
| File size | 3.9 MB (right at the MCP re-compression threshold of 3.75 MB — would have re-compressed to `.mcp.jpg` via MCP transport) |
| Output path | `/tmp/run_20260518_190654_814b57/final_output.png` — see §5 finding F2 |

Copied into the repo as **[`docs/architecture/diagrams/jack-tar-deckhand-architecture-paperbanana.png`](../../architecture/diagrams/jack-tar-deckhand-architecture-paperbanana.png)** for project use.

---

## 4. Visual review

Dispatched via `general-purpose` subagent (Sonnet, higher visual accuracy than Haiku). Did NOT direct-Read the PNG — followed the discipline rule. Subagent's JSON verdict (abridged):

```json
{
  "verdict": "pass",
  "subject_match": "Strong match. Orchestrator centrally placed with skills (7/11 listed) + agents (5/6 listed) compartments. All 4 engine plugins present, correctly tagged. Bridge as peer wrapper above. Paperbanana bottom-right as optional external CLI. Inputs/outputs correctly externalised.",
  "composition": "Orchestrator visually central and largest. Engine plugins arrayed horizontally beneath with labelled arrows (Draft Image Output, Production Image Output, SmartArt Render Pipeline, etc.). Bridge above showing wrap relationship with bidirectional arrows. Paperbanana visually separated with terminal icon + 'Optional:' label + dashed border.",
  "text_rendering": "Excellent — every plugin name spelled correctly (jack-tar-deckhand, jack-tar-superpower-bridge, jack-tar-ollama, jack-tar-cloud, jack-tar-msft-smartart, jack-tar-custom-smartart, paperbanana). All skill names correctly hyphenated. No invented names, no garbled glyphs.",
  "defects": [
    "Skill list 7/11 (missing: strategy-map, speaker-notes-writer, deck-qa, verify)",
    "Agent list 5/6 (missing: presentation-reviewer)",
    "smartart-selector appears in both skills+agents columns (correct but may confuse without footnote)",
    "Small text cramping near the bridge box arrows",
    "No legend distinguishing solid-border (in-system) from dashed-border (optional/external)"
  ],
  "strengths": [
    "Orchestrator centrality unambiguous",
    "All 4 engine plugins distinguishable by colour + purpose-tagline",
    "Paperbanana's optional/external status conveyed three ways (dashed border, 'Optional:' label, terminal icon, separate visual band)",
    "Bridge wrapper relationship correct with bidirectional arrows",
    "I/O arrows labelled with payload types (TalkBriefs, Image Gen Request, Academic Figure Request)",
    "Conference-appropriate restrained palette"
  ],
  "would_a_speaker_use_this_in_a_real_talk": "yes with caveats",
  "comparison_to_what_nano_banana_flash_1k_would_have_produced": "clearly better"
}
```

The defects are real but minor — most are "the figure shows representative subsets, not exhaustive lists." A speaker using this in a talk could either expand the lists in a footer caption ("Representative selection — full catalogue in `verify` output") or run a 3rd iteration with explicit feedback asking for all 11 skills + 6 agents.

---

## 5. Findings — operational

### F1 — `--output` flag ignored in current paperbanana source

**Severity:** medium

We passed `--output /tmp/jack-tar-dogfood` and paperbanana wrote to `/tmp/run_20260518_190654_814b57/final_output.png` — **the requested parent directory was ignored entirely**. Paperbanana wrote to the system temp root, not to our dir.

The 2026-05-17 spike report §3 claimed `--output` "keeps only the parent directory" — that was true on that machine's paperbanana state but is no longer true on the current source. Either paperbanana changed its `--output` semantics between the spike's checkout and today's `pip install -e ~/Documents/Development/paperbanana`, or the flag has always been partly broken and the spike got lucky.

**Implication for our dispatch:** `_extract_run_id()` still works because the regex finds the `run_<ts>_<hash>` pattern regardless of parent dir. Manifest entry is correct. But the bridge SKILL.md must NOT assume paperbanana wrote inside `output_dir` — it should grep paperbanana's stdout for the `Output: <path>` line and read back from there. Captured in §6 follow-up.

### F2 — PyPI 0.1.2 ships a stripped-down CLI vs source main

**Severity:** medium

`pip install 'paperbanana[google]'` installs paperbanana 0.1.2 from PyPI, but the CLI in that release **does not have `--aspect-ratio`, `--budget`, `--cost-only`, `--dry-run`, `--format`, `--vector`, `--auto`, or `--continue-run`** — only the bare `--input`, `--caption`, `--output`, `--iterations`, model/provider flags, and `--config`. The source clone at `~/Documents/Development/paperbanana` has the full surface but is also labelled `0.1.2` in `pyproject.toml`.

Per upstream issue [llmsresearch/paperbanana#215](https://github.com/llmsresearch/paperbanana/issues/215), version inconsistency between `pyproject.toml` and `server.json` was already flagged. This finding is **more severe** — the PyPI release is months behind main. Operators following our ADR's install guide via `pip install 'paperbanana[google]'` will get a CLI that doesn't support our dispatch's args.

**Mitigation we applied:** `pip install -e ~/Documents/Development/paperbanana` from the clone gets the full CLI surface.

**For ADR install guide:** update §6 to either (a) document `pip install -e git+https://github.com/llmsresearch/paperbanana.git@main#egg=paperbanana[google]` as the recommended install until upstream cuts a new release, or (b) file an additional upstream issue requesting an immediate 0.2.0 release that catches PyPI up with main. Recommend (b) — operators shouldn't have to install from git for a stable integration.

### F3 — `platformdirs` missing from PyPI install dependencies

**Severity:** low-medium

After installing from the source clone, `paperbanana generate` failed with `ModuleNotFoundError: No module named 'platformdirs'` until we `pip install platformdirs` manually. The source clone's `pyproject.toml` lists `platformdirs>=4.0` as a runtime dep, but the editable reinstall in our jack-tar venv didn't pick it up properly (likely a stale `paperbanana[google]` extra resolution). Worth verifying whether the next PyPI release picks it up cleanly.

### F4 — Critic flagged 3 visual issues at iter 2 we didn't address

The paperbanana Critic agent reported at the end of iter 2:
- System boundary fill + border too faint (almost invisible against background)
- Bridge plugin's "soft light coral" came out almost white
- paperbanana CLI box's fill + dashed border too faint

These are real issues we'd address with a 3rd iteration. We capped at 2 for cost control. For a hero deck figure where the operator cares about polish, 3 iterations (~$0.21 total spend) would be the right call. The subagent's visual review didn't flag these (the contrast issues are subtle on full-screen viewing).

### F5 — `iterate-slide` refinement is well-positioned by `paperbanana_run_id`

The manifest entry's `paperbanana_run_id: "run_20260518_190654_814b57"` lets us cheaply refine via `paperbanana generate --continue-run run_20260518_190654_814b57 --feedback "increase contrast on the system boundary and the paperbanana CLI box"` for ~$0.07 incremental spend, exactly as the iterate-slide skill (#89) will do. The architectural decision in Task 3 paid off immediately.

### F6 — paperbanana's tracked spend is 6% of true spend

paperbanana reported `$0.0085` total cost. Real spend is ~$0.14 (the $0.131 image cost is unaccounted because Flash 1K isn't in paperbanana's pricing table — upstream issue #213). This is exactly the failure mode we predicted; our jack-tar-side budget accounting in `provider_discovery.py` must be the authoritative gate, not paperbanana's `--budget` cap.

---

## 6. Follow-up: imagegen-bridge SKILL.md update (NEW — not in original plan)

**The refactor plan's 6 tasks did NOT include updating the imagegen-bridge SKILL.md's Step 4.6 academic_figure branch.** Ralph's E2 had wired the bridge to dispatch via "Skill cross-invocation" — the refactor's new ADR says CLI subprocess transport instead. The dispatch helper now returns the right payload, but the bridge SKILL.md is still pointing at the wrong transport.

**Recommended follow-up commit before PR:** update `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md` Step 4.6 to:

1. Call `build_dispatch_payload(slide, output_dir=…)` from python helper
2. If `dispatch.available is True`: write `dispatch.args["source_context"]` to a tmp file, then `subprocess.run(["paperbanana", "generate", "--input", tmpfile, "--caption", dispatch.args["caption"], "--aspect-ratio", dispatch.args["aspect_ratio"], "--iterations", str(dispatch.args["iterations"]), "--vlm-provider", "gemini", "--vlm-model", "gemini-2.5-flash", "--image-provider", "google_imagen", "--image-model", "gemini-3.1-flash-image-preview", "--output", dispatch.output_dir, "--budget", "0.25"], capture_output=True, text=True)`
3. Parse paperbanana's stdout for the `Output: <path>` line (since `--output` parent-dir is ignored — finding F1)
4. Compute sha256 + call `build_manifest_entry(dispatch, dispatch_succeeded=True, output_path=<parsed>, content_hash=<sha>)`
5. If `dispatch.available is False`: take the cloud Flash 1K fallback path with academic-figure-aware prompting

This is a Task 7 we should add to the plan retroactively. ~30 min of work. Lands as a follow-up commit on the same branch before pushing the PR.

---

## 7. Gate verdict

✅ **PASS — proceed to push + PR.**

Evidence:
- Detection works in real venv (`is_paperbanana_available()` returns `True`)
- Dispatch helper produces the correct 4-key args
- Real subprocess invocation succeeded
- Output file landed (in unexpected location per F1, but `_extract_run_id` handles it)
- Visual review verdict: pass, "clearly better than Nano Banana Flash 1K baseline"
- Manifest entry has all expected fields including `paperbanana_run_id` and `paperbanana_args`
- True spend $0.14 (under $0.30 dogfood cap)
- Subagent confirmed the figure would be usable in a real talk (with the noted caveats)

Six new operational findings (F1–F6) — none block the PR, all should be folded into the dispatch / install-guide narrative as we go.

The architecture figure at `docs/architecture/diagrams/jack-tar-deckhand-architecture-paperbanana.png` is a useful project artefact — usable in the README, in the ADR, or in future talks about the project.

---

## 7b. Iterate-slide refinement attempt (second-order dogfood)

Operator requested a refinement pass via `paperbanana generate --continue-run` to exercise the iterate-slide pattern (#89) end-to-end, address the Critic's three contrast flags (F4), and add the missing skills/agents the Sonnet reviewer noted. This validates whether the `paperbanana_run_id` manifest field actually enables cheap refinement as designed.

**Setup gotcha (new finding F7):** `--continue-run <id>` looks for the run dir under `settings.output_dir` (default `outputs/` relative to cwd), NOT at the path paperbanana originally wrote to (`/tmp/run_<id>/`). We had to `cp -r /tmp/run_20260518_190654_814b57 outputs/` before the continuation would find the prior state. The bridge's CLI subprocess wrapper will need to handle this by either (a) running paperbanana with cwd=`output_dir`, (b) symlinking the run dir to the canonical location, or (c) waiting for upstream to honour `--output-dir` on `generate --continue-run`. The dogfood log captures this as F7 — file as upstream issue.

**The refinement command:**

```
paperbanana generate \
  --continue-run run_20260518_190654_814b57 \
  --iterations 1 \
  --feedback "Three contrast fixes: (1) strengthen the outer 'Jack-Tar Deckhand System' boundary…
              Three content fixes: (1) include all 11 skills…
              One layout fix: reroute the 'Upstream /pptx' arrow…" \
  --vlm-provider gemini --vlm-model gemini-2.5-flash \
  --image-provider google_imagen --image-model gemini-3.1-flash-image-preview \
  --budget 0.15
```

**Outcome:** Iter 4 produced in 60.5s for ~$0.07 (Flash 1K image + ~4 VLM calls).

**Visual review verdict (via general-purpose subagent comparing iter-2 vs iter-4):** **comparable, do NOT replace the repo figure**.

| Feedback item | Outcome |
|---|---|
| 1. Outer boundary contrast | partially_fixed (title got bolder, border thinned) |
| 2. Bridge coral saturation | **fixed** ✓ |
| 3. paperbanana CLI box contrast | partially_fixed |
| 4. Eleven skills listed | **regressed** ✗ (went from 7/11 to 6/11) |
| 5. Six agents listed | **regressed** ✗ (went from 5/6 to 4/6) |
| 6. smartart-selector dual-column footnote | not addressed |
| 7. Upstream arrow routing | **fixed** ✓ |

The reviewer flagged a new defect: **the smartart-selector appearing in both columns (a correct dual-status signal) was REMOVED in iter 4**, even though the feedback asked us to add a footnote explaining the duality.

### F8 — Single-iteration refinement is patchy for content additions

**Severity:** medium

The mechanical iterate-slide path works exactly as designed: `--continue-run` loads prior state, `--feedback` reaches the Critic, a new iteration runs, the cost is genuinely ~50% of a fresh 2-iter run ($0.07 vs $0.14). The cheap-refinement architectural claim is validated.

But the Visualizer agent's ability to fully address content additions in a single iteration is limited. The Critic's iter-4 notes **echo the same content critiques verbatim** ("should be updated to include all 11 skills mentioned in the methodology") — meaning the Critic identified the gap but the Visualizer didn't close it. Contrast fixes (purely visual) landed cleanly; content-additive fixes (list items, footnotes) did not.

**Implication for iterate-slide (#89) design:**

1. **Single-iter refinement is reliable ONLY for visual/contrast/layout tweaks.** The bridge coral fix and the arrow rerouting are clean wins.
2. **Content-additive feedback (add 4 items to a list, add a footnote) should NOT be batched in a single iteration.** Each content item likely needs its own refinement turn, OR a fresh 2-iteration run from scratch with updated `methodology_context`.
3. **A failsafe rollback mechanism is essential.** When refinement is verdict=`comparable` or `worse`, the iterate-slide skill MUST preserve the prior file and not overwrite. We applied this manually here — the repo figure stays at iter-2; iter-4 is scratch.
4. **The reviewer's "next iteration" suggestion is mechanistic** — it explicitly enumerated the 11 skills + 6 agents in the feedback text. That kind of "exhaustive list in the prompt" feedback might land better than the "include all 11 skills" abstract instruction. Worth A/B-testing in the #89 design phase.
5. **Refinement cost projection is realistic** at ~$0.07 per Flash 1K iter. A 3-iter refinement cycle (visual fix → review → content fix → review → polish) would land at ~$0.21 — competitive with a fresh 2-iter run from scratch ($0.14) only if it's more reliable, which it isn't yet for content changes.

### F7 — `--continue-run` cwd / output-dir resolution

**Severity:** low-medium

`paperbanana generate --continue-run <id>` looks for the run dir under `settings.output_dir` (default `outputs/` relative to cwd). Paperbanana CLI flags `--output` and `--output-dir` (the latter on `runs list`) do not change this lookup path. Workaround: copy/symlink the run dir to `<cwd>/outputs/run_<id>/` OR set `OUTPUT_DIR` env var (untested; needs confirming whether pydantic-settings picks it up via the bare field name).

The imagegen-bridge's CLI subprocess wrapper (Step 4.6) will need to either:

- Run paperbanana with cwd set to the output_dir's parent, OR
- Set `OUTPUT_DIR=$DECK_DIR/images` env var on the subprocess call, OR
- Wait for an upstream fix that makes `--continue-run` honour `--output-dir`

Worth filing as a 4th upstream issue (separate from #213/#214/#215).

### Tier-2 follow-up — explicit enumeration + permission to shrink + 2 more iterations

Operator requested a multi-tier convergence experiment to find the threshold at which content-additive feedback actually lands. Ran a second refinement against iter 4, this time with:

- **Explicit enumeration:** "Skills list MUST contain EXACTLY these 11 entries in this exact order: brand-manager, slide-stylist, narrative-architect, strategy-map, smartart-selector, smartart-extractor, speaker-notes-writer, imagegen-bridge, deck-assembler, deck-qa, verify"
- **Permission to shrink:** "Visualizer must NOT drop items to fit them in. Permission granted to shrink the body font, narrow the line height, or split into a 2-column sub-grid"
- **Strong imperative language:** "MUST contain EXACTLY", "NO substitutions and NO omissions", "CRITICAL"
- **Verbatim footnote text + format:** "in 12pt or smaller, reading exactly: '* smartart-selector appears in both columns…'"
- **Preserve list:** named the iter-4 wins to keep (bridge coral, arrow routing, paperbanana box contrast)
- **2 iterations** rather than 1

**Outcome:** **Critic SATISFIED at iter 6** — first time in the experiment. Wall 1m 49s, ~$0.15 spend.

Visual review verdict (subagent comparing iter 6 to iter 2 baseline): **"iter 6 clearly better, should replace the repo figure."**

| Tier-2 ask | Outcome |
|---|---|
| Skills list — all 11 items in order | **fully fixed** ✓ (subagent enumerated all 11) |
| Agents list — all 6 items in order | **fully fixed** ✓ (subagent enumerated all 6) |
| smartart-selector dual-column | **yes, both columns** ✓ |
| Footnote present + correctly formatted | **yes** ✓ ("* smartart-selector appears in both columns; it is both a user-facing skill and an AI persona agent.") |
| Solid ~2px outer system boundary | **yes** ✓ |
| Bridge coral preserved | **yes** ✓ (saturated coral from iter 4 kept) |
| Arrow routing preserved | **yes** ✓ |

Minor trade-off the Visualizer made (the reviewer accepted it): list rendering switched from clean two-column bullets to inline comma-separated prose to fit 11+6 names at the canvas size. The dual-column smartart-selector signal now depends on the footnote rather than spatial alignment.

### F9 — Multi-tier convergence: explicit enumeration > vague refinement

**Severity:** high (drives iterate-slide skill #89 design)

| Tier | Iters | Feedback style | Critic outcome | Content fixes |
|---|---|---|---|---|
| 0 (baseline) | 2 (fresh) | none | partial flags | 7/11 skills, 5/6 agents |
| 1 (refinement) | +1 | vague "include all 11" | echoed same critique | **regressed** to 6/11 + 4/6 |
| 2 (refinement) | +2 | EXPLICIT enumeration + permission-to-shrink + STRONG imperative | **SATISFIED at iter 6** | 11/11 + 6/6 + footnote |

The Visualizer agent reliably acts on explicit enumeration that the operator does the listing work for. Vague "include all N" reliably fails because the model defends its prior layout against unbounded growth. Permission to shrink (or change layout) unblocks the trade-off.

**Implications for iterate-slide skill #89 design:**

1. **The refinement-feedback prompt template should encourage explicit enumeration.** If the operator says "list all the missing items," #89 should expand "missing items" into the full inventory before sending the feedback to paperbanana.
2. **The skill should generate trade-off permissions automatically.** When the feedback adds N items to a list, also add "permission granted to shrink font / change layout to fit them."
3. **2 iterations is the practical floor for content-additive refinement.** Single-iter (Tier 1) regressed; 2-iter (Tier 2) converged. Default `--iterations 2` on refinement.
4. **Re-bracket the protected items.** Tier-2 feedback named iter-4 wins explicitly under a "KEEP" header — those properties stuck through 2 more iterations. Without that, refinement might lose them via the same overfit-on-current-ask pathology.
5. **Critic-satisfied is the natural stopping signal.** When `--auto` is wired up properly, it could converge in fewer roundtrips. Worth testing in a Tier-3 dogfood if budget allows.

### What we kept

- **Repo figure:** `docs/architecture/diagrams/jack-tar-deckhand-architecture-paperbanana.png` — **iter 6 version** (Tier-2 refined). 4.1 MB, 2752×1536, sha256 `78d72ff0…0348af06`. Replaces the iter-2 version that was committed earlier in the dogfood.
- **Discarded:** iter 4 (Tier-1 attempt) — comparable to baseline, not retained.
- **Preserved (forensics):** the `metadata_continued.json` and `iter_3`/`iter_4`/`iter_5`/`iter_6` subdirs all live under the gitignored `outputs/run_20260518_190654_814b57/` on the dogfood machine. Useful for reproducing or auditing.

### Tier-3 — `--auto` mode (no operator feedback)

Operator requested a third tier to test paperbanana's `--auto` flag end-to-end: can the Critic+Visualizer loop reach a `satisfied` state on a fresh run with NO operator-supplied enumeration feedback?

**Setup:** Fresh paperbanana run with `--auto --max-iterations 4`. Same methodology text + caption as the baseline. New run id: `run_20260518_212056_f719d8`.

**Outcome:** 3 visualizer iterations completed in 3:53 wall, ~$0.22 spend. **`--auto` terminated at iter 3 with Critic still flagging a defect** (missing primary output arrow from orchestrator to the .pptx deck node). Did not hit `--max-iterations 4`. The reason for early stop is unclear — possibly counts the Planning+Styling phase as an iteration, possibly some other safety condition.

**Visual review verdict (subagent comparing Tier-3 to Tier-2 baseline):** **Tier-2 clearly better** for our use case (architecture-documentation figure), but Tier-3 is **better on flow / explanatory clarity** — it's not worse, it's *different*.

### F10 — Two-axis design space: completeness vs explanatory flow

**Severity:** high (this is the most important #89 design finding from the multi-tier dogfood)

| Dimension | Tier-2 (explicit enumeration) | Tier-3 (--auto, no feedback) |
|---|---|---|
| Skills enumeration | **all 11** ✓ | 2 examples (brand-manager, deck-assembler) ✗ |
| Agents enumeration | **all 6** ✓ | 2 examples (deck-conductor, prompt-engineer) ✗ |
| Smartart-selector dual-column footnote | yes ✓ | not addressable (lists are abbreviated) |
| Outer system boundary | solid 2px dark ✓ | dashed faint light-grey ✗ |
| Bridge plugin visual emphasis | saturated coral ✓ | pale lavender ✗ |
| **Arrow labels for engine plugins** | terse one-way requests | **richer bidirectional with labelled returns** ✓ |
| **Bridge contract semantics** | generic "enriches upstream" caption | **explicit role tags + 4 labelled contract arrows** ✓ |
| **paperbanana conditional invocation** | "Academic Figure Request" label | **"invokes for academic figures (conditional)" + "returns academic figure"** ✓ |
| **Hierarchical clarity** | dense | **cleaner top-to-bottom: TalkBriefs → Orchestrator → 4 engines → Deck** ✓ |
| **Visual crowdedness** | crowded (especially the inline skills/agents prose) | **less crowded; better legibility at small sizes** ✓ |

The Critic optimises for **visual and flow coherence**, NOT for enumeration completeness. When the figure's value lies in *completeness* (specification artifact, e.g. "every skill is listed for audit"), `--auto` cannot infer "list all 11 by name" from a caption that says "with skills and agents." When the figure's value lies in *flow* (explanatory diagram, e.g. "show how a request travels through the system"), `--auto` produces a richer result than operator-driven enumeration.

**Implications for the iterate-slide skill (#89) design — supersede F8/F9's "do this once" thinking with a two-mode skill:**

1. **Two operator modes, not one.** The skill should expose `--mode auto` (Critic-driven convergence, for explanatory/conceptual figures) and `--mode enumerate` (operator-supplied checklist, for specification/contract figures). The Tier-2 vs Tier-3 evidence shows these produce qualitatively different outputs and serve different deck purposes.
2. **Default routing:** `auto` for body-of-talk illustrative slides, `enumerate` for the "system overview" / "what's in scope" / "team roster" / "API surface" hero slides where completeness is the value.
3. **The operator-checklist surface for enumerate mode** should be structured, not free-text:
   - `must-mention`: list of items that MUST appear in the figure
   - `must-be-visually-prominent`: visual properties that must hold (e.g., "this box should be the largest", "this border must be solid not dashed")
   - `keep-from-prior`: properties to preserve across refinement iterations (the Tier-2 "KEEP" header pattern)
4. **`--auto` mode default-stops at the safety cap, not at Critic-satisfied.** The dogfood showed that `--auto --max-iterations N` can terminate without convergence; the skill must check the final Critic verdict (satisfied vs needs-revision) and surface that to the operator rather than silently shipping a non-converged figure.
5. **A `--draft` mode could combine the two:** `--auto` for first 2 iterations (cheap exploration) then if not converged, switch to operator-checklist for the final round (deterministic completion). This is the recipe Tier-2 effectively followed.
6. **Cost telemetry per mode:** Tier-2 (3 iters split as 2 fresh + 1 vague + 2 enumerated) cost $0.36 cumulative. Tier-3 (3 iters auto) cost $0.22. For *equivalent quality on a completeness artifact*, the operator-supplied checklist is more cost-effective than `--auto` looping; for *equivalent quality on a flow diagram*, `--auto` is more cost-effective than operator iteration.

### What we kept (cumulative across all 3 tiers)

- **Repo figure remains the Tier-2 iter-6.** For the architecture-documentation use case, completeness wins. Tier-3 is genuinely better at flow but doesn't list all the skills + agents — fatal for the figure's purpose as a system specification.
- **Tier-3 output preserved on dogfood machine** at `outputs/run_20260518_212056_f719d8/final_output.png` (gitignored). Useful as a comparative artifact when designing #89 — it's the canonical "what `--auto` produces for a completeness-style brief" example.
- **Cumulative spend across all tiers: ~$0.58** ($0.14 baseline + $0.07 Tier-1 + $0.15 Tier-2 + $0.22 Tier-3). Over the $0.30 single-dogfood gate but the multi-tier experiment was explicitly authorised by the operator and the design-input value is significant.

---

## 8. Artefacts

- **Final figure:** [`docs/architecture/diagrams/jack-tar-deckhand-architecture-paperbanana.png`](../../architecture/diagrams/jack-tar-deckhand-architecture-paperbanana.png) (3.9 MB, 2752×1536)
- **Methodology input:** [`2026-05-18-paperbanana-methodology-input.txt`](2026-05-18-paperbanana-methodology-input.txt) (3.5 KB, 5 paragraphs)
- **paperbanana run dir:** `/tmp/run_20260518_190654_814b57/` (preserved on dogfood machine; contains `metadata.json`, `planning.json`, `prompts/`, iter intermediates — operator can `paperbanana runs show run_20260518_190654_814b57` for full audit, or `paperbanana runs delete` to clean up)
- **Plan:** [`docs/superpowers/plans/2026-05-18-paperbanana-dispatch-refactor.md`](../plans/2026-05-18-paperbanana-dispatch-refactor.md)
- **ADR v2:** [`docs/architecture/paperbanana-integration-v2.md`](../../architecture/paperbanana-integration-v2.md)
- **Spike report:** `~/Documents/Development/paperbanana/tmp/SPIKE_REPORT.md` (out of repo, operator's local machine)
