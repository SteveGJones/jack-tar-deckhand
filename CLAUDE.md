# CLAUDE.md

All rules are in **CONSTITUTION.md**. Core instructions are in **CLAUDE-CORE.md**.

## MANDATORY: Visual Output Review (Constitution Article 9.4)

**NEVER return visual artifacts to the user without reviewing every output first.** This means:
- View each generated image (SmartArt, Ollama, cloud) immediately after creation
- View each rasterised PNG after SVG-to-PNG conversion
- View assembled slides after deck assembly (rasterise .pptx to PNG if needed)
- Compare every visual against the original intent
- "File exists" or "pipeline completed" is NOT a review

This rule exists because visual review was skipped THREE TIMES across multiple conversations, each time producing decks with blank slides, missing text, or broken graphics that the user had to catch.

## MANDATORY: Agent Definition Reloading

**Agent definitions in `.claude/agents/*.md` are loaded at session start, NOT on every dispatch.** When you modify an agent's protocol (e.g., `image-reviewer.md`):
- The change is NOT picked up by the actual subagent until Claude Code is restarted
- The `general-purpose` agent reads prompts fresh each call, so prompt-injected protocols work without restart
- For iterative reviewer development: test via `general-purpose` agent first, then restart and validate the actual subagent picks up the new definition
- Always tell the user to restart Claude Code after modifying agent definitions if you need the changes to take effect this session

**Validation pattern**: After updating `.claude/agents/<name>.md`, dispatch the subagent and check whether its responses reflect the new criteria. If they don't, the definition is cached and a restart is required.

**Vision capability note**: The `image-reviewer` agent uses Haiku, which has visual perception limitations (e.g., misjudging proportional widths in tapered shapes). For high-accuracy visual review, the `general-purpose` agent (Sonnet/Opus) is more reliable. Use both in parallel for cross-validation when possible.

## MANDATORY: Image-review discipline (issue #76 — enforced)

The `jack-tar-deckhand` plugin installs a `PreToolUse` hook that BLOCKS `Read` on image files (PNG, JPG, GIF, WEBP, BMP, TIFF). PNGs in orchestration context burn tokens that compound across every subsequent turn — review must happen out-of-context via subagent dispatch.

For every image generated:
- Dispatch `jack-tar-deckhand:image-reviewer` (Haiku, returns compact JSON)
- Or `general-purpose` (Sonnet/Opus, higher visual accuracy)
- Capture the verdict; never `Read` the PNG yourself.

**Bypass**: set `ALLOW_PNG_READ=1` only when the image IS the user-facing answer (the user explicitly said "show me X"). The bypass is a deliberate signal, not a workaround.

The hook is auto-installed when the plugin is enabled — no separate setup. Verify via `/jack-tar-deckhand:verify` (reports the "DISCIPLINE HOOK" section).

This rule was reaffirmed 2026-05-07 during the blog-post asset run when 9 PNGs were Read directly into context before the operator caught it. Memory alone does not bind; the harness has to.

### Subagent-scope gap (issue #86, confirmed 2026-05-17)

The `PreToolUse` hook governs the **orchestration session only**. It does **not** propagate into `Task`-dispatched subagent sessions — a synthetic test on 2026-05-17 confirmed that a `general-purpose` Haiku subagent successfully `Read` a PNG with the parent plugin's hook active. See `docs/architecture/discipline-hook-propagation.md` for the test evidence and root-cause analysis.

**Soft-policy mitigation in force**: every delegated implementation prompt that may touch generated images MUST inline this reminder near the top of the prompt:

> Do not `Read` PNG / JPG / GIF / WEBP / BMP / TIFF files directly. If you need to verify an image, dispatch the `jack-tar-deckhand:image-reviewer` subagent (Haiku, JSON verdict) or the `general-purpose` subagent (Sonnet, higher accuracy). Both subagents pull the image into THEIR context and return text.

`image-reviewer` and `general-purpose` agents are themselves exempt — giving them the image IS the dispatch's purpose. Orchestrators reviewing PRs should verify that delegated implementation prompts include the inline rule when image handling is in scope.

## MANDATORY: Operator gate at every free→cost cascade transition (issue #105, F10)

**Whenever a cascade is about to cross from a free tier (Ollama, $0) to any paid cloud tier (Flash/Pro/Recraft, cost > $0), the orchestrator MUST surface the latest free-tier render to the operator AND pause for explicit go-ahead before invoking any cloud generation.**

This is independent of how the Critic agent voted. The Critic evaluates against the prose; it cannot know whether the result matches the operator's intent. Only the operator can. The Critic returning `escalate_tier` is advisory — not authorisation to spend.

**What the gate looks like:**

1. After every Ollama (or other zero-cost) render, open the resulting image for the operator (`open <path>` on macOS, equivalent elsewhere)
2. State the prospective cloud spend ("rendering at Pro 1K will cost $0.134", or similar)
3. **Wait for explicit operator go-ahead** ("go", "yes", "proceed", "render", "render at Pro 1K" — affirmative signal)
4. Only after explicit affirmation, dispatch the cloud render

**The gate is the load-bearing checkpoint of the cascade economic model.** Skipping it turns a human-in-the-loop pipeline with a free preview into an agent loop that bills the operator. During the 2026-05-22 creative-vision dogfood (issue #105), this gate was skipped THREE times across the v2 / v3 / diptych rounds, leading to $0.480 of un-gated Pro 4K spend that the operator later identified as both methodologically wrong (gate skipped) and tier-inappropriate (Pro 1K would have sufficed — F9).

**The gate also catches prompt failures cheaply.** During the same dogfood, three consecutive Ollama drafts at the gate caught structural prompt failures (one room not three scenes, customer dropping, 9-panel grid) BEFORE any cloud spend, saving ~$0.40 of cloud renders that would have demonstrated the same failures at higher resolution. The free renders are the cheapest possible learning instrument.

**Bypass conditions — narrow:**
- The cascade is wholly within free tiers (no cost transition).
- The operator has set explicit budget pre-authorisation in writing for the current session AND the cost is below that authorisation. In all other cases the gate stands.

The orchestration layer that owns this rule is the creative_vision SKILL.md and the imagegen-bridge SKILL.md — see those for the concrete enforcement steps. This CLAUDE.md rule binds the agent's behaviour at the orchestration level regardless of which SKILL.md is driving.

## MANDATORY: Prompt simplification check on stalled cascades (issue #105, F11)

**When prompt iteration N has elaborated the prompt to address Critic feedback and composition is still failing, consider RADICAL SIMPLIFICATION before adding more directives.**

The Prompt Reviewer currently checks "does the prompt have enough?" — entity coverage, style cues, density. It does NOT check "does the prompt have too much?" During the 2026-05-22 dogfood, an elaborated ~1,100-word prompt (camera-as-unifier framing, four-figure roster, fax-machine bridge, atmospheric montage layering) failed to render the intended five-scene composition. The operator rewrote it as a six-line prompt that embraced the model's natural grid bias instead of fighting it — and the simpler prompt landed the deliverable.

**Heuristic — when to suspect over-specification:**
- Prompt is >400 words AND composition keeps failing
- Multiple consecutive Critic verdicts cite the same composition axis (the model isn't responding to elaboration)
- Negative directives are stacking ("NO panels", "NO grid", "NO fused room") — fighting a model bias rather than working with it
- Each iteration adds words without changing the verdict

**Counter-move:** propose a shortened prompt (≤200 words, ideally ≤100) that:
- Drops contradictory unifiers (e.g., "shared back wall" + "three rooms")
- Embraces the model's natural framing (if the model wants to render N panels, name N panels positively)
- States the scene list as one line each
- Carries only the most load-bearing entity and style cues

Then surface the simplified prompt to the operator as an alternative before rendering. The reviewer should consider both prompts and the operator decides which to run.

This rule pairs with the operator-gate rule above — at the free→cost boundary, the operator can also be asked "do you want to try a simplified prompt before paying for cloud?"

## MANDATORY: Creative_vision review is image-level, not slide-level (issue #113, F12)

**When a slide's strategy is `creative_vision`, the operator gate fires on EVERY iteration — including same-cost-tier refinements and same-resolution renders. The image IS the slide; only operator acceptance closes the slide.**

Standard composed / backdrop / full_render slides treat the image as an illustration on a slide — review is slide-level, gates fire only at free→cost transitions (F10). For creative_vision the asymmetry is fundamental: the image carries the entire conceptual weight, slides absorb 3-7 operator-gate touchpoints, and the image-reviewer + Director's Critic verdicts are advisory only. The Critic evaluates against the prose; only the operator can judge whether each render matches the creative intent.

**What this means in practice:**

1. **Every iteration fires the gate.** Flash 1K → Flash 1K iteration fires. Pro 1K → Pro 2K fires. Ollama → Ollama refinement fires. The single canonical predicate is `src/creative_vision/orchestrator.should_fire_operator_gate(strategy=, current_tier=, next_tier=)`. Both human reviewers and tests look there, not at SKILL.md prose.
2. **Pre-deck Creative Sprint phase.** The deck-conductor runs ALL creative_vision slides to operator acceptance BEFORE composed-slide assembly. Standard-slide work is BLOCKED until the sprint completes — context-switching between slow-high-touch and fast-low-touch review contaminates both modes. See `src/creative_vision/sprint.py`.
3. **Per-slide cost surface at strategy approval.** Before the operator approves the strategy map, every creative_vision slide shows an explicit cost band and operator-gate count. If declined on cost grounds, fallback strategies (composed / backdrop / full_render) are offered for the over-budget slides. See `src/creative_vision/cost_estimator.py::summarise_creative_vision_spend`.
4. **Deck-level creative anchors.** When a deck has multiple creative_vision slides sharing a recurring character / prop / location / style, capture them once in `<deck_dir>/creative_anchors.json` (schema: `src/schemas/creative_anchors.schema.json`). The Director's Brief reads the anchors and weaves them in by name so all slides agree on canonical appearance — closes the cross-slide character-drift gap.

**Why this rule exists.** The 2026-05-23 Agentic Naval Academy dogfood surfaced F12 after the operator observed: *"It feels like these images need a human review/insight on the generation OF THE IMAGE not the slide in a way that is different to our standard process."* Slide 2 of the data-supply-chain dogfood needed 14 attempts × ~10 gate touchpoints; slide 3 (Naval Academy) needed 7 attempts × 6 gates. Standard composed slides absorb 1-2 renders with 0-1 gates. The cost and time economics differ by an order of magnitude — interleaving the two cadences is methodology malpractice.

**Bypass conditions — none.** Unlike F10, this rule has no narrow bypass conditions. The Critic's `pass` verdict does not authorise closure of a creative_vision slide; only the operator's explicit acceptance at the gate does. If the cascade exhausts its budget cap and the Critic flags `abort`, the slide finalises with the best-so-far image AND the operator is surfaced the result for explicit accept/reject before the conductor proceeds to the next slide.

## MANDATORY: Model routing for delegated agents

**Spawn `claude-haiku-4-5` for lightweight tasks**: mechanical transforms, quick format checks, simple lookups, boilerplate fills, command line calls and MCP server calls.

Reserve Sonnet/Opus for tasks that require judgement — investigations, design decisions, prose writing, visual review, multi-step implementations with surface-area decisions.

When dispatching via `Task`, set `model: "haiku"` for the lightweight category. Default model inheritance from the parent session is wasteful for mechanical work.

## Plugin Architecture (EPIC #40)

This repository is now a **5-plugin Claude Code marketplace**. The presentation pipeline has been refactored into independently installable plugins:

| Plugin | Purpose | Skills |
|--------|---------|--------|
| `jack-tar-ollama` | Local AI image generation via Ollama | image, icon, pattern, diagram, presentation, verify |
| `jack-tar-cloud` | Cloud AI image generation (OpenAI, Google, FAL, Recraft) | openai-image, google-image, fal-image, recraft-icon, image, icon, verify |
| `jack-tar-msft-smartart` | Editable PowerPoint SmartArt (29 layouts) | render, inject, catalog, verify |
| `jack-tar-custom-smartart` | Data viz and custom graphics (SVG, Mermaid, Vega) | render, chart, verify |
| `jack-tar-deckhand` | Full presentation pipeline orchestrator | brand-manager, slide-stylist, narrative-architect, strategy-map, smartart-selector, smartart-extractor, speaker-notes-writer, imagegen-bridge, deck-assembler, deck-qa, verify |

**Plugin files:** `plugins/<name>/` — each plugin has `.claude-plugin/plugin.json`, `skills/`, `agents/`, `src/`, `tests/`

**Marketplace manifest:** `.claude-plugin/marketplace.json` — **v1.1.0** (all plugins)

**Quick start:** `/jack-tar-deckhand:verify` → reports which engine plugins are ready

The original `src/` directory remains as the development source of truth. Plugin directories contain copies that are distributed.

**Optional external tool — paperbanana:** `jack-tar-deckhand` v1.4.0+ routes slides classified as `academic_figure` (Figure-N captions, equations, citations, ablation studies, ML architecture diagrams) through the [paperbanana](https://github.com/llmsresearch/paperbanana) CLI via subprocess when paperbanana is installed locally (`pip install 'paperbanana[google]'`, `pipx`, or `uvx`). Paperbanana is treated as an external CLI tool — a sibling orchestrator, like LaTeX or ImageMagick — not as a Claude Code plugin. When paperbanana is absent the bridge falls back to Nano Banana Flash 1K with academic-figure-aware prompting — pipelines never break on absent optional dependencies. **Local-first tier (2026-07-10):** when local Ollama carries an image-capable model (`x/flux2-klein` preferred, `x/z-image-turbo` fallback; override via `local-config.json` → `ollama.academic_figure_model`), the academic_figure ladder renders a free Ollama draft FIRST and holds at the F10 operator gate before any paid tier (paperbanana or cloud). `detect_local_backend()` in `paperbanana_dispatch.py` is the probe; the `LocalBackend` seam is provider-shaped, and **MLX has now slotted in as that second local provider** (issue #124, 2026-07-15 — see below). See ADR v2 §8.5. ADR + operator install guide: [`docs/architecture/paperbanana-integration-v2.md`](docs/architecture/paperbanana-integration-v2.md) (v1 ADR at [`paperbanana-integration.md`](docs/architecture/paperbanana-integration.md) preserved as historical record).

## Project: Jack-Tar Deckhand

Claude Code skills and agents for conference-quality PowerPoint presentations. This is NOT a standalone app — it runs inside Claude Code.

### MANDATORY KNOWLEDGE: 2026-07-17 model benchmark — escalation economics changed

Full blind + adversarial benchmark (10 scenarios × 2 aspects × 6 local models + Nano Banana Flash/Pro anchors; 180 scored images, 89 adversarial corrections; spike: [`docs/spikes/2026-07-17-mlx-model-benchmark/`](docs/spikes/2026-07-17-mlx-model-benchmark/README.md), PR #138). Two conclusions BIND escalation decisions until superseded:

1. **Nano Banana Pro is NOT required for technical/academic figures at 1K.** Flash matched-or-beat Pro on technical figures (TECH 8.70 vs 8.40, blind). Escalate academic_figure slides to **Flash**, not Pro; Pro is for 2K/4K resolution needs or hero polish only. (Corrects the standing "Pro = best text rendering" heuristic at 1K.)
2. **Local models are more than adequate for hero/full_bleed images.** ERNIE-Image-Turbo (baidu base, on-load q8 via mflux) scored 8.75 on hero scenarios — above BOTH cloud anchors; Z-Image-Turbo 8.30. Cloud escalation for hero drafts should be the exception (operator-requested polish or resolution), not the default ladder step. Z-Image is the preferred local draft for text-bearing figures (quote-card winner, fastest at ~82 s); Klein-4b needs its exact-spellings prompt dialect to perform.

The model catalog entry notes carry these findings (gemini-3-pro-image, gemini-3.1-flash-image, mlx/z-image-turbo). ERNIE catalog entry + routing updates tracked as follow-up issues. Operators can query this doctrine interactively via `/jack-tar-advisor:model-advisor` (standalone jack-tar-advisor plugin 0.1.0). Labeled technical figures should use `/jack-tar-deckhand:annotate-figure` (v2: deck-native `annotation_mode` on the strategy map — perfect text by construction, PoC blind 10/10 at $0).

### Current Status (2026-07-23 — annotate-figure v2.1 shipped on branch, issue #142)

- **`feat/annotate-figure-v2.1` implements the two items v2 (#142 v2, PR #146, deckhand 1.10.0) deliberately deferred**: `composed` strategy wiring for `annotation_mode` (`annotated_image_zone`) and a `show_headline` opt-in on native full-slide annotated slides. Deckhand bumped `1.10.0 → 1.11.0` (marketplace lockstep).
  - **Feature A — composed zone wiring**: a composed slide with `annotation_mode: native`/`raster` now keeps its chrome — headline, body_points, accent bars, footer logo — and the annotated figure fills the slide's image zone (the picture-placeholder rect in template/python-pptx mode, the `content_with_image` image zone in PptxGenJS mode) instead of the whole canvas. This is the OPPOSITE of v2's pure-figure contract on full-slide strategies, which is unchanged. Placement zone is derived from the slide's EFFECTIVE strategy (`speaker_override` wins) at BOTH the routing site and inside the builders — a stale payload `placement_zone` can never mis-fit a slide whose strategy later changed (F-02). Every composed annotated slide gets content-with-image chrome regardless of `slide_type` — `diagram`/`data_chart` included (F-03 ruling).
  - **Feature B — headline opt-in**: `annotation.show_headline` (boolean, default false, native + full-slide only) renders the outline headline in a top band (`HEADLINE_BAND_FRAC = 0.14`) above a shrunk contain-fit figure. Ignored on `raster` mode (F-04) and on `composed` (already has its own headline). Chrome-only — does not invalidate the annotation payload or trigger `/iterate-slide`'s F4 anchor-refresh guard.
  - **What landed**: schema field `annotation.show_headline`; JS assembler (`build_deck.js`) routing intercept split by strategy-derived placement zone + `buildContentSlide`/`buildNativeAnnotatedSlide` changes; python-pptx assembler (`build_deck_template.py`) strategy-branched annotation block + `_resolve_annotation_zone_rect` F-06 fallback chain (picture placeholder → content placeholder → hardcoded default) + `strip`/`strip_chrome` kwargs + headline-band helpers; `run_qa` F-08 VISUAL_CHECKS for composed-strategy native slides; imagegen-bridge Step 4.8 composed placement-zone + manifest `dimensions` (F-01) wiring; `/annotate-figure` and `/iterate-slide` SKILL.md updates.
  - **F-09 follow-up filed, not fixed in this release**: AN-01's hash gate silently skips on a relative `image_entry['file_path']` (pre-existing defect, touches the v2 test surface) — [issue #147](https://github.com/SteveGJones/jack-tar-deckhand/issues/147).
  - **Design doc**: [`docs/superpowers/plans/2026-07-23-annotate-figure-v2.1.md`](docs/superpowers/plans/2026-07-23-annotate-figure-v2.1.md) (adversarially reviewed, GO-WITH-CHANGES, §9). **Parent design**: [`docs/superpowers/plans/2026-07-17-annotate-figure-v2.md`](docs/superpowers/plans/2026-07-17-annotate-figure-v2.md).

### Current Status (2026-07-15 — MLX (mflux) second local provider shipped on branch, issue #124)

- **New sibling plugin `jack-tar-mlx` v0.1.0** ships a second $0 local image-generation provider alongside `jack-tar-ollama` — Apple Silicon only, driven by the [mflux](https://github.com/filipstrand/mflux) CLI, no server daemon, flag-compatible with the Ollama wrapper. Three catalog entries (`mlx/flux2-klein-4b` default, `mlx/z-image-turbo`, `mlx/qwen-image`), all operator-installed and operator-weight-pulled — the plugin never auto-downloads. On branch `feat/mlx-local-backend`, 6 implementation commits (T1–T6 of the design doc's task breakdown, plus 3 preceding planning commits), not yet merged to `main`.
  - **What landed**: `model-catalog.json` `mlx/*` entries + schema fields (`min_ram_gb`, `render_steps`, `sdk.entrypoint`/`hf_repo`/`hf_repo_fallback`/`default_steps`/`quantize`) — catalog `1.0.0 → 1.1.0`; `plugins/jack-tar-mlx/` (wrapper + nested single-flight lock + `image`/`verify` skills); `detect_mlx_backend` + `detect_any_local_backend` composed probe in `paperbanana_dispatch.py` (Ollama-first by default, `local_provider_order` override); `probe_mlx_models` + `not_installed` local-provider verdict in `model_probe.py`; imagegen-bridge Step 4.6 `mlx_local` render branch with F10/F12 gate parity; marketplace + versions (`jack-tar-deckhand` 1.7.0 → 1.8.0, `jack-tar-cloud` 1.4.0 → 1.5.0, `jack-tar-mlx` new at 0.1.0).
  - **Licensing correction found during implementation (issue #124 review M6)**: two of the three pre-quantized community repos (`filipstrand/Z-Image-Turbo-mflux-4bit`, `filipstrand/Qwen-Image-mflux-6bit`) are licensed under the **Tongyi Qianwen licence, not Apache 2.0**, despite their base models being Apache 2.0 — a derivative repo's licence does not automatically inherit the base's. The klein primary (`Runpod/FLUX.2-klein-4B-mflux-4bit`) is confirmed Apache 2.0. All three Apache-2.0 fallback repos remain available for operators who need pure Apache-2.0 provenance.
  - **Design doc** (single source of truth for the implementation): [`docs/superpowers/plans/2026-07-15-mlx-local-backend.md`](docs/superpowers/plans/2026-07-15-mlx-local-backend.md). **Operator install guide**: [`docs/architecture/mlx-install-guide.md`](docs/architecture/mlx-install-guide.md). **ADR addendum**: [`docs/architecture/paperbanana-integration-v2.md`](docs/architecture/paperbanana-integration-v2.md) §8.6.
  - **Remaining before merge**: T7 (docs, this entry) then T8 — full-suite gate + PR to `main` referencing #124. Horizon 2 (MLX as *replacement* free tier, not just second provider) is a separate follow-up issue gated on a Phase 5 evaluation dogfood beating the Ollama Klein-9b baseline.

### Current Status (2026-05-21 — v1.4.2 shipped + v1.5.0 creative vision IN PROGRESS)

- **v1.4.2 full_bleed strategy shipped** via [PR #104](https://github.com/SteveGJones/jack-tar-deckhand/pull/104) (merge commit `d2253ad`). Plugin bumped `1.4.1 → 1.4.2`. Closes issue #88.
  - `full_bleed` rendering strategy: image IS the slide, zero chrome (no title overlay, no body text, no footer logo). `strategy_map.schema.json` extended with `full_bleed` enum value. `build_deck.js` + `build_deck_template.py` handle full-bleed assembly.

- **v1.5.0 creative vision renderer — IN PROGRESS on branch `feat/creative-page-renderer`** (28+ commits, 296 tests, issue #105).
  - **What it is**: paperbanana-shaped multi-agent cascade for operator prose → vision-faithful full-slide images. Abstract, conceptual images driven by a language-to-image pipeline.
  - **Pipeline**: operator prose → Director's Brief (Sonnet) → ParsedVision + prompt → Prompt Reviewer (Haiku) → render → image-reviewer (Haiku) → Director's Critic (Sonnet) → verdict → loop or escalate
  - **New agents**: `directors-brief.md` (Sonnet), `prompt-reviewer.md` (Haiku), `directors-critic.md` (Sonnet). In `plugins/jack-tar-deckhand/agents/`.
  - **New schemas**: `parsed_vision.schema.json`, `directors_critic_verdict.schema.json`, `creative_vision_manifest.schema.json` in `plugins/jack-tar-deckhand/src/schemas/`
  - **New strategy**: `creative_vision` enum in strategy_map (always pairs with `full_bleed` assembly; `allOf` conditional enforces bidirectional)
  - **New modules**: `src/creative_vision/{manifest,cascade,brief,prompt_reviewer,critic,orchestrator}.py`, `src/creative_vision_dispatch.py`
  - **iterate_slide extended**: 3 channels for creative_vision slides: `revise_prose`, `refine_prompt`, `escalate_tier`
  - **Cascade tiers**: Ollama (free) → Flash 1K ($0.067) → Flash 4K ($0.151) → Pro 1K ($0.134) → Pro 4K ($0.240); `allowed_ceiling` budget cap
  - **Sun-phases dogfood COMPLETE**: $0.067 total spend, 3 iters (Ollama ×2 + Flash 1K ×1). Entity 78, spatial 85, style 88, comp 80. Final: `tmp/creative-vision-dogfood/deck/creative-vision/1/runs/03-flash-1k.png`. Log: [`docs/superpowers/dogfooding/2026-05-21-creative-vision-renderer.md`](docs/superpowers/dogfooding/2026-05-21-creative-vision-renderer.md).
  - **F1** (Brief returns non-canonical parsed_vision shape — subjects as plain strings, wrong field names) and **F2** (prompt outside JSON fence at Flash tier) must be fixed before opening the PR. See dogfood log §Findings.

### Current Status (2026-05-23 — creative_vision v1.5.0 tested-but-not-GA in PR #107)

- **PR #107** (`feat/creative-page-renderer`, base `main`) — OPEN, 4 commits, 300/300 tests passing (1 skipped).
  - `30bbbd5` — F1 (brief schema validation) + F2 (Output Contract anti-patterns)
  - `b618830` — F10 (operator gate at free→cost) + F11 (prompt simplification heuristic)
  - `dc3e52c` — Prompt Simplifier architectural decision capture (#112)
  - `3998273` — Agentic Naval Academy dogfood + F12 (image-level review) + creative_vision per-iteration gate
- **Three dogfoods complete**:
  - Sun-phases (slide 1) — $0.067
  - Data supply chain (slide 2) — $1.016 — multi-scene narrative; F10/F11 surfaced + landed; F1/F2 fixed
  - Agentic Naval Academy (slide 3) — $0.268 — single-scene composition; F12 surfaced
- **creative_vision shipped as tested-but-not-GA**. Per operator: NOT GA until the deck-conductor enhancements land.
- **GA-blocking work**: issue **#113** captures six acceptance criteria — strategy-map per-slide cost surfacing, pre-deck creative_vision sprint phase, per-iteration gate validation tests, deck-level creative anchors file, CLAUDE.md updates, cost-table reconciliation (cloud module vs cascade.py TIER_COSTS disagreed on Pro 2K — $0.134 actual vs $0.193 in table).
- **Related follow-up**: issue **#112** — Prompt Simplifier agent (F11 implementation). Separate scope; should land before or alongside #113.
- **Branch strategy for GA work**: new branch `feat/creative-vision-ga` off `feat/creative-page-renderer`. New PR's base is `feat/creative-page-renderer` (not main) so it merges INTO PR #107. Once both PRs merge to main, the combined diff is the full creative_vision v1.5.0 GA release.

### Data supply chain dogfood (2026-05-22 — COMPLETE)

4-panel 1980s Wall Street-aesthetic storyboard: sales team scrawling orders on cocktail napkin → finance cleaning the napkin into typed paper → customer reading the invoice → supply chain confused at missing delivery address (truck driver peering at signpost). Budget $0.50, ceiling `pro_1k`.

- **Final image**: `tmp/creative-vision-dogfood/deck/creative-vision/2/runs/03-flash-1k.png` (all four callouts crisp, sports cars + signpost rendered, blank-signpost punchline lands)
- **Total spend**: $0.067 (Ollama×2 + Flash 1K×1; same envelope as sun-phases despite a more complex multi-entity vision)
- **Final scores at Flash 1K**: entity 82, spatial 85, style 72, quality 84, comp 88. Verdict `pass` (see F3 below — Critic violated its own ≥80 rule on style; documented).
- **Findings**:
  - **F1** (Brief returns non-canonical parsed_vision shape) — **FIXED in this PR**: `brief.parse_brief_output` now validates parsed_vision against the schema + rejects empty prompts. 3 new tests cover the failure paths.
  - **F2** (prompt outside JSON fence) — **FIXED in this PR**: directors-brief.md Output Contract now shows labelled CORRECT shape next to WRONG shape anti-pattern block with 4 concrete failures + self-check. 1 new agent-definition test pins the labels.
  - **F3** (Critic returned pass with style_fidelity 72 — verdict-coherence violation) — **NEW, deferred follow-up patch**: add semantic validation to `critic.parse_critic_output` so pass-with-any-axis-below-80 raises like the schema check.
- **Log**: [`docs/superpowers/dogfooding/2026-05-21-creative-vision-renderer-data-supply-chain.md`](docs/superpowers/dogfooding/2026-05-21-creative-vision-renderer-data-supply-chain.md)
- **Tests**: 296 → 300 passing (1 skipped). PR open for issue #105.

### Current Status (2026-05-20 — v1.4.1 shipped + v1.4 plan part-done)

- **v1.4.1 merged on main** via [PR #102](https://github.com/SteveGJones/jack-tar-deckhand/pull/102) (merge commit `4f8fc2b`). Plugin bumped `1.3.3 → 1.4.0 → 1.4.1`. CI 9/9 green.
- **What v1.4.1 ships:**
  - **Paperbanana integration as external CLI tool** (sibling orchestrator framing). New `academic_figure` strategy + `paperbanana_dispatch.py` helper module + ADR v2 ([`docs/architecture/paperbanana-integration-v2.md`](docs/architecture/paperbanana-integration-v2.md)) supersedes v1. Detection via `find_spec` + `shutil.which`; transport via CLI subprocess; manifest carries `paperbanana_run_id` + `paperbanana_args` for refinement.
  - **`/jack-tar-deckhand:iterate-slide` skill** (#89) — three-mode refinement contract (auto / enumerate / draft) derived empirically from the multi-tier dogfood. Helper module `src/iterate_slide_dispatch.py` covers mode dispatch + feedback assembly + F7 cwd workaround + manifest history + cost telemetry. 53 unit tests.
  - **Ralph pre-session work bundled in:** #87 (register presets), #92 (cloud retry-on-empty-candidates), #93 (`strap_style: prose-sentence`).
  - **Test suite:** 130/130 → **183/183 green** (130 dispatch + 53 iterate-slide).
- **Dogfood evidence + design findings:** [`docs/superpowers/dogfooding/2026-05-18-paperbanana-integration.md`](docs/superpowers/dogfooding/2026-05-18-paperbanana-integration.md) — F1–F11 captured across 4 tiers of dogfood (~$0.72 cumulative spend, under the $5 v1.4 cap). F8/F9/F10 drive the iterate-slide two-mode design. F11 — paperbanana Critic verdict ≠ jack-tar reviewer (visual reviewer is authoritative).
- **Architecture figure** at [`docs/architecture/diagrams/jack-tar-deckhand-architecture-paperbanana.png`](docs/architecture/diagrams/jack-tar-deckhand-architecture-paperbanana.png) — produced by paperbanana documenting jack-tar's own architecture (meta-dogfood); also embedded in ADR v2 §1.
- **Upstream issues filed at llmsresearch/paperbanana** (parallel work): #213 (pricing table), #214 (deprecated defaults), #215 (version inconsistency), #216 (PyPI staleness), #217 (`--continue-run` cwd resolution).

### v1.4 plan — remaining work (updated 2026-05-21)

Original v1.4 plan had 3 deferred issues. #88 shipped in PR #104. Remaining:

| # | Title | Cluster | Effort | Notes |
|---|---|---|---|---|
| ~~#88~~ | ~~Deck-assembler `full-bleed` scale~~ | — | — | **DONE** — PR #104 (`d2253ad`), deckhand 1.4.2. |
| #90 | Prompt-engineer composition-primitives library | A (prompt-engineer) | ~4–5 hr | **Pair with #91.** 5 primitives from the 2026-05-13 keynote. |
| #91 | Prompt-engineer pre-render text-density warning | A (prompt-engineer) | ~2–3 hr | **Pair with #90.** Safety net for #90's primitive templates. |

Sequencing:

1. **Next: finish issue #105** on branch `feat/creative-page-renderer` — complete data supply chain dogfood → fix F1+F2 → open PR → deckhand 1.4.2 → 1.5.0
2. **Then: #90 + #91 together** — coupled prompt-engineer scope; bumps deckhand to 1.5.1

Still-open issues NOT in the v1.4 scope: #86 (discipline-hook propagation — investigation-only commit landed; actual fix still open), #95 (Ralph false-completion — documented in dogfood log, cross-check rule applies meanwhile).

### Current Status (2026-05-12 — v1.3 push complete)

- **Issues #20, #33, #34, #49, #54, #55, #56, #57** all closed across PRs #80–#85. Bridge v0.2.0 → 0.2.2 (CHART marker + inline `·` separator fix), deckhand 1.3.1 → 1.3.3 (gantt selector criteria + inline_data refactor coverage + 5 custom-smartart layout defects), custom-smartart 1.1.0 → 1.1.1.
- **Triage cycle**: closed 27 issues total across a single session via 5 PRs + 17 already-fixed-on-main verdicts.
- **New rule established**: verification-before-merge (`feedback_verification_before_merge.md`) — CI green is necessary but not sufficient; visual / runtime gates run before merge for any PR touching visual output, render paths, or new markers.
- **New rule established**: verification for cached agents (`feedback_verification_for_cached_agents.md`) — dispatch general-purpose with new rule inline rather than the cached subagent.

### Current Status (2026-05-08)

- **Bug-batch + discipline hook shipped — main is now at:** cloud `1.3.2`, deckhand `1.3.1`, ollama `1.1.1`, msft-smartart `1.2.2`, bridge `0.2.0`, custom-smartart `1.1.0`.
- **PRs #77 / #78 / #79 merged**, closing issues #72–#76 (surfaced during the 2026-05-07 blog-post asset run):
  - **#72** — cloud retry decorator extended to cover `httpx.RemoteProtocolError`, `httpx.ConnectError`, `httpx.ReadError` (google-genai's underlying transport layer).
  - **#73** — Recraft V4 default style changed from `realistic_image` (V3-only, causes 400) to `None`; fall-through to FAL on style-rejection errors when `FAL_KEY` is configured.
  - **#74** — Imagen Fast resolution guard: `image_size` kwarg omitted for `imagen-4.0-fast-generate-001` (fixed resolution only — rejects the parameter with `400 INVALID_ARGUMENT`).
  - **#75** — Ollama single-flight lock: `fcntl.flock` at `/tmp/jack-tar-ollama-image.lock` serialises concurrent callers; new `--lock-wait-timeout` (default 600 s) and `--no-lock` flags.
  - **#76** — Discipline hook auto-installed by `jack-tar-deckhand`: `PreToolUse` hook blocks `Read` on image files; image review must go through `image-reviewer` or `general-purpose` subagent. `ALLOW_PNG_READ=1` bypass for legitimate cases.
- **Dogfood retrospective:** `docs/superpowers/dogfooding/2026-05-07-blog-post-asset-run.md` — 6-artefact blog-post asset run, $2.99 total, 7 discipline failures and bugs documented.
- **Plans:** `docs/superpowers/plans/2026-05-08-blog-post-bug-batch.md` · `docs/superpowers/plans/2026-05-08-discipline-hook.md`

### Current Status (2026-05-07)

- **Superpower Bridge v0.2.0 + EPIC #58 closed — main is now at:** cloud `1.3.0`, deckhand `1.3.0`, msft-smartart `1.2.2`, bridge `0.2.0`, ollama/custom-smartart `1.1.0`.
- **EPIC #58 (cloud image resolution control) CLOSED 2026-05-06** — 4/4 children landed: #62 (PR #63), #59 (PR #65), #60 (PRs #68 + #69), #61 (PR #70). 1K/2K/4K resolution + brand-fidelity (Recraft V4 raster) wired through render funnel + image router + imagegen-bridge Step 9A.
- **Superpower Bridge merged 2026-05-07** — 76 committed bridge commits + v0.2 polish (Findings #17/#18/#19/#20/#21/#22/#23/#24/#25/#26/#27/#28/#29) staged into 4 finding-labeled commits. Run 10 (2026-05-01) declared GO. Bridge ships with `/bridge-brief`, `/enrich-deck`, `/verify`. Known limitation: bridge runs its own enrichment cycle separate from imagegen-bridge Step 9A — does not yet consume EPIC #58 resolution/brand-fidelity surfaces; v0.3 candidate.

### Current Status (2026-04-27)

- **Superpower Bridge (issue #53) — six dogfood runs complete, all cycle paths exercised.** On branch `feat/superpower-bridge`. **225 tests passing** across the bridge suite. Plugin `jack-tar-superpower-bridge` v0.1.0 ships with `/bridge-brief`, `/enrich-deck`, `/verify`. Two new AI personas (Narrative Brief Architect; Enrichment Cohesion Reviewer) + contract extensions to Image Reviewer + Prompt Engineer. **Contracts 1+2 implemented and dogfood-validated across 6 visual personalities (Dark Industrial / Engineering Ink / Blueprint Retrospective / Redline / Boardroom Stone / Velvet Ledger).** Run 6 (2026-04-29) **fired all three uncovered cycle paths in one run** — Phase A → Phase B Flash → Phase C Pro escalation, plus the `terminate_pending_confirmation` privacy gate handshake (first time across all runs). Task 35 GO held until v0.1.x patch backlog ships.
  - **Dogfood logs (read in order, latest first):** [Run 6](docs/superpowers/dogfooding/2026-04-29-bridge-dogfood-run-6.md) (**Velvet Ledger / cloud escalation thesis fully validated** / Findings #19, #20, #21 surfaced) · [Run 5](docs/superpowers/dogfooding/2026-04-27-bridge-dogfood-run-5.md) (Boardroom Stone / sub-page SmartArt + chart routing + BG-at-marker entrenched) · [Run 4](docs/superpowers/dogfooding/2026-04-26-bridge-dogfood-run-4.md) (Redline / sub-page IMAGE proven) · [Run 3](docs/superpowers/dogfooding/2026-04-26-bridge-dogfood-run-3.md) (Contracts 1+2 validated) · [Run 2](docs/superpowers/dogfooding/2026-04-25-bridge-dogfood-run-2.md) · [Run 1](docs/superpowers/dogfooding/2026-04-23-bridge-dogfood-run-1.md)
  - **Findings tracker (21 items, see `project_superpower_bridge.md` memory)** — #11 fixed in flight; #16 resolved by Run 5 thesis; #19/#20/#21 surfaced by Run 6 (image-reviewer text-fidelity contract gap, fix patterns codified in agent + SKILL.md updates 2026-04-30); #12-#14, #17, #18 cosmetic/heuristic v0.1.x patches; **#15 release-shaping** (Section C language workaround validated in Run 5; v0.2 CHART marker kind formalises it).
  - **Implementation tasks 1–34 done.** Task 35 GO verdict pending v0.1.x patch backlog. All cycle paths validated in Run 6.
  - **Plan:** [docs/superpowers/plans/2026-04-23-superpower-bridge.md](docs/superpowers/plans/2026-04-23-superpower-bridge.md) — 35 tasks across 16 phases; v1.1 panel-revised.
  - **Spec:** [docs/superpowers/specs/2026-04-22-superpower-bridge-design.md](docs/superpowers/specs/2026-04-22-superpower-bridge-design.md) — final critical review verdict SHIP WITH CAVEATS; all 7 caveats addressed in the implementation.
  - **Personas:** [docs/architecture/ai-personas/superpower-bridge-personas.md](docs/architecture/ai-personas/superpower-bridge-personas.md) — promoted to v1.0 with consolidated tripartite (Steve Jones × 3 for v1; documented split trigger), full 5-tier measurement blueprint, scorecard Items 3 + 6 green, Item 5 amber pending dogfood.
  - **Canonical model:** `.bsa/models/jack-tar-deckhand.json` v1.5.0 — Bridge Services L1 + 4 services + 10 INT-BRIDGE interactions + Cross-Domain SOP register entry (with CAC + changeTrigger) + 5 dependency-register entries. Schema extended for the new top-level keys.
  - **Marketplace:** bridge registered v0.1.0; jack-tar-deckhand and jack-tar-msft-smartart bumped 1.1.0 → 1.2.0 (cache-key invalidation for downstream workspaces).
  - **Team review synthesis:** [docs/superpowers/specs/2026-04-23-superpower-bridge-team-review.md](docs/superpowers/specs/2026-04-23-superpower-bridge-team-review.md)
  - **Spike 1** ([docs/spikes/2026-04-23-pptx-marker-adherence/](docs/spikes/2026-04-23-pptx-marker-adherence/README.md)) — marker adherence. PptxGenJS 4.0.1 silently drops `name` property; `objectName` is correct. Variant A (correct) = 100% adherence; B and C (wrong key) = 0%.
  - **Spike 2** ([docs/spikes/2026-04-23-python-pptx-enrichment/](docs/spikes/2026-04-23-python-pptx-enrichment/README.md)) — python-pptx edits of /pptx output. Three prototype ops (background / image replace / SmartArt inject) pass tests, PowerPoint Mac gate, visual review, OOXML inspection.
  - **Spike 3** ([docs/spikes/2026-04-23-analyser-source-comparison/](docs/spikes/2026-04-23-analyser-source-comparison/README.md)) — analyser source comparison. HYBRID decision: OOXML primary (stable, always available), JS build-script fallback via esprima AST-only for marker extraction when OOXML finds zero markers AND build.js exists.
  - **Key design decisions baked into the implementation:** OOXML primary analyser; SMARTART overlap detection is analyser-side (verifiable); transactional all-or-nothing enrichment with explicit `try/finally` cleanup + `os.replace` atomic rename; `budget_cap_usd` default $1.00 covering BOTH generation AND review (caveat #6); brief `confidentiality` tier (public/internal/restricted); image-path allowlist mandatory with parent-symlink-escape protection; JS parsed AST-only with parse-never-execute hard contract test; cycle_state primitives for SKILL.md-driven loop (NOT a Python cycle that overrides callables — caveat #1 fix).
  - **Real-world bugs caught and fixed during execution** (not in original plan): JS parser had a dead lowercase ternary silently skipping valid markers; Phase B budget review charge was conditional (would let Pro escalate on an unpaid review); SmartArt parser couldn't handle Spike 1's inline label format (`SMARTART: x — A | B | C`); cross-plugin sys.modules contamination after msft-smartart loader. All caught by the review/integration cycle, all fixed in the underlying module.
  - **28 spike tests passing** — 10 for Spike 1, 6 for Spike 2, 12 for Spike 3.
  - **Run 4+5 dogfood insights embedded into user-facing artefacts 2026-04-27**: `narrative-brief-architect.md` agent codified sub-page SmartArt typology with explicit coordinates, native chart routing language, BG-on-pivot guidance, will/won't colour reservation, required Section B palette table template. `bridge-brief/SKILL.md` updated to require those patterns in Section C. Plugin CLAUDE.md points users at Run 4 + Run 5 briefs as canonical examples.
  - **Run 6 dogfood insights embedded into user-facing artefacts 2026-04-30**: image-reviewer agent (`plugins/jack-tar-deckhand/agents/image-reviewer.md`) now requires `expected_text_content` for text-bearing markers (Finding #19/#20 fix) + verdict-coherence self-check (Finding #21 fix). `enrich-deck/SKILL.md` extracts expected text from the brief's Section C and passes it on reviewer dispatch + adds SMARTART-FROM-LIST bullet-length pre-flight (Finding #13). `narrative-brief-architect.md` Section C requires "EXACT spelled labels REQUIRED" lists for text-bearing IMAGE markers + ≤24 char SmartArt bullet guidance. `bridge-brief/SKILL.md` codifies these as required Section C content. Plugin `CLAUDE.md` adds Run 6 (Velvet Ledger / institutional+M&A) as canonical example, plus a "Patterns repeatable for new operators" 10-pattern quick reference. **NOTE — restart Claude Code before any new dogfood run** so the updated agent definitions load.
  - **Next action — v0.1.x patch backlog**: Findings #3/#7 (codify split-dispatch in SKILL.md), #8 (Phase 1 cost ledger), #12 (palette heuristic), #13 (smartart label caps auto-truncate or layout-route by length), #14 (report counter), #16 (cloud connection retry decorator), #17 (BG addText cleanup), #18 (cohesion cost kind), #19/#20 (image-reviewer expected_text_content runtime fix — orchestrator extraction logic + agent contract enforcement), #21 (verdict-coherence guard at orchestrator level). Bump bridge plugin to v0.1.1 with this batch. After v0.1.x ships, Task 35 GO and v0.1.0 release.

- **BSA Architecture:** v1.5.0 (bumped 2026-04-24 by superpower bridge work) — adds Bridge Services L1 with Narrative Brief Architect + Enrichment Cohesion Reviewer personas. Earlier scope: keynote pipeline, rendering strategy expansion, image reviewer, SmartArt intelligent graphics.
  - Canonical model: `.bsa/models/jack-tar-deckhand.json` v1.5.0 (38 services, 8 AI personas, 70 interactions, plus crossDomainSopRegister + dependencyRegister top-level keys)
  - Documentation: `docs/architecture/` (10 docs + 7 SVG diagrams; superpower-bridge-personas.md at v1.0)

### Earlier Status (2026-05-03 — EPIC #58 mid-flight, pre-bridge merge)

- **Cloud Resolution Control (Issue #59 — landed):** `jack-tar-cloud` v1.2.0 added a unified `resolution=` kwarg routing 1K / 2K / 4K to each provider's native API field. New `ProviderResolutionUnsupportedError` carries supported-tier metadata for retry. Per-model capability surfaced via `provider_discovery.discover_providers()`. Imagen dual-pricing detection (Vertex flat vs Gemini Developer API token-based) wired into `estimate_google_cost`.
  - **What's wired:** Nano Banana Pro (1K/2K/4K), Nano Banana Flash (0.5K/1K/2K/4K), Imagen Standard/Ultra (1K/2K), Imagen Fast (1K only), FLUX 2 Pro (1K/2K). 4K ladder validated end-to-end on real API ($0.659 smoke-test spend).
  - **EPIC:** [#58](https://github.com/SteveGJones/jack-tar-deckhand/issues/58) closed 2026-05-06 (4/4 children complete: #62/#59/#60/#61).
  - **Spec:** `docs/superpowers/specs/2026-05-02-cloud-resolution-control-design.md`
  - **Plan:** `docs/superpowers/plans/2026-05-02-cloud-resolution-control.md` (10 phases, all complete)
  - **Spike:** `docs/spikes/2026-05-02-google-genai-image-config-spike.md` (PATH-B: typed `ImageConfig` from `google.genai.types`)
  - **Smoke test:** `docs/superpowers/dogfooding/2026-05-03-resolution-smoke-test.md` — Jack Tar wallchart through Ollama → Flash 1K → Flash 4K → Pro 1K → Pro 4K.

### Earlier Status (2026-04-16 — BSA pre-bridge)

- **BSA Architecture (pre-bridge):** v1.4.1, includes keynote pipeline + rendering strategy expansion + image reviewer + SmartArt intelligent graphics + cloud resolution control (1K/2K/4K)
  - Canonical model: `.bsa/models/jack-tar-deckhand.json` (33 services, 6 AI personas, 60 interactions)
  - Documentation: `docs/architecture/` (10 docs + 7 SVG diagrams)
  - Note: superseded by v1.5.0 BSA after the bridge merge above.

- **Research Library:** Complete — 20 papers, ~110K words in `research/`
  - Start with `research/RESEARCH-INDEX.md` for fast lookup
  - Create `research/synthesis-[skill-name].md` before implementing any skill
  - `research/report-1-landscape-and-spec.md` and `report-2-implementation-and-validation.md` are the pptx_native SmartArt research Phase 1/2

- **Test suite: comprehensive coverage across all plugins (run `pytest` per plugin for current counts)**
  - Phases 1-6: Foundation through Orchestration (518 tests)
  - SmartArt Intelligent Graphics (PR #21, merged 2026-04-07): 132 tests
  - pptx_native SmartArt engine (PR #39, merged 2026-04-10): ~300 tests across 17 test files — 28 layouts, picture embedding, multi-slide integration
  - Cross-plugin integration tests: `plugins/integration_tests/` (33 tests — verify contracts, PLUGIN_ROOT discovery, msft-smartart pipeline, bridge skill names)

- **Full Pipeline:** `/jack-tar-deckhand:deck-conductor` orchestrates: brand-manager → slide-stylist → narrative-architect → **smartart-selector** → **strategy-map** → **smartart-extractor** → speaker-notes-writer → imagegen-bridge → **smartart-renderer** → chart-renderer → deck-assembler → deck-qa → presentation-reviewer

- **deck-conductor invocation contract (issue #42, fixed):** The conductor is a conversational orchestrator — run as primary agent in a dedicated session, OR as a subagent when TalkBrief provides `preferences.budget_cap_usd` and `preferences.image_backend` (skips Step 0 escalation). Fix: `read_brief_defaults()` in conductor.py extracts budget/providers from brief; agent definition makes escalation conditional.

- **Template-Driven Layout Support (issue #45):** Speakers can provide a corporate .pptx template via `branding.template_pptx_path`. Template analyser (`src/template_analyser.py`) extracts layouts and placeholder geometry, auto-maps to slide types (Speaker confirms). python-pptx assembly engine (`src/assembler/build_deck_template.py`) opens the template, strips example slides, places content into typed placeholders (TITLE, BODY, CONTENT, PICTURE). Strategy map constrained to `composed` in template mode. SmartArt injection works unchanged via placeholder rects in content zones.
  - **Design spec:** `docs/superpowers/specs/2026-04-17-template-driven-layout-design.md`
  - **Implementation plan:** `docs/superpowers/plans/2026-04-17-template-driven-layout.md`

- **Speaker Notes Import (issue #44):** Speakers can provide per-slide narrative notes in external .md/.txt files via `preferences.speaker_notes_path`. Notes parser (`src/notes_parser.py`) supports heading-based, number-marker, and headline fuzzy matching. Writer enriches imported notes with timing/cues and generates for uncovered slides. Enables voiceover auto-generation and self-presenting visual-heavy decks.

- **SmartArt Intelligent Graphics (merged 2026-04-07, PR #21):** AI-driven templated graphic generation
  - 10 v1 graphic types: flowchart, decision tree, bar/line chart, radar chart, SWOT, feature matrix, Venn, timeline, pipeline/funnel, Gantt
  - 3 rendering engines: Mermaid.js (graph-based), Vega-Lite (data viz), Custom SVG (spatial/infographic)
  - 4 enrichment tiers: T0 pure programmatic, T1 AI background, T2 AI element icons, T3 full AI render
  - Draft-phase comparator: competing engines render same data, image-reviewer scores, winner locked for production
  - Negotiation pattern: smartart-selector proposes graphic types, narrative-architect approves/rejects (max 2 rounds)
  - New AI persona: SmartArt Selector (Haiku default, Sonnet escalation)
  - **Auto-routing for poor aspect ratios:** 4+ node flowcharts route from Mermaid LR to `src/smartart_svg/layouts/flowchart.py` (2x2/2x3/3x3 grid). 3+ rule decision trees route from Mermaid TB to `src/smartart_svg/layouts/decision_tree.py` (2-column "if/then" layout). Routing logic in `extract()` in `src/smartart_extractor.py`.
  - **Design spec:** `docs/superpowers/specs/2026-04-03-smartart-intelligent-graphics-design.md`
  - **Research:** `research/ai-driven-templated-graphic-generation-research.md`
  - **Latest demo deck:** `output/jack-tar-deckhand-smartart-demo-v7.pptx` (16.2 MB, 28 slides reviewed)
  - **GitHub issue:** #17 (closed)

- **pptx_native SmartArt engine (merged 2026-04-10, PR #39, issue #38):** Fourth SmartArt engine that produces editable PowerPoint SmartArt graphics (not rasterised PNGs). Speakers can edit nodes, rename them, switch layouts, and insert images directly in PowerPoint after delivery. 28 layouts across 8 categories, all MIT-sourced from `dotnet/Open-XML-SDK`. Picture SmartArt with AI-generated embedded images via child-node architecture. SmartArt over AI backgrounds.
  - **Technique:** template injection — three opaque XML parts per layout (layout.xml, quickStyle.xml, colors.xml) extracted from MIT-licensed SDK fixtures; engine generates a fresh `data1.xml` per graphic via generic builders; JS assembler places a named placeholder rect; Python post-process grafts the diagram parts in after build_deck.js finishes and replaces the placeholder with a `<p:graphicFrame>`.
  - **v1 scope (27 layouts shipped, 2 deferred across 9 categories):**
    - **Process (8):** process1 (Basic Process), process4, chevron1, hProcess4, hProcess7, hProcess9, hProcess11, lProcess2
    - **Cycle (2):** cycle2 (Basic Cycle), cycle8
    - **Hierarchy (5):** orgChart1 (Organization Chart — **includes asst node support**), hierarchy2, hierarchy4, hierarchy5, hierarchy6
    - **List (6):** list1 (Basic List), hList6, vList2, vList3, vList4, vList5
    - **Matrix (1):** matrix2
    - **Pyramid (1):** pyramid2
    - **Relationship (4):** venn1 (Basic Venn), venn3, funnel1, target3
    - **Deferred:** `pList1` (Picture List — needs spike 6 image integration), `default` (uncategorised)
    - basicTimeline1 not in SDK fixtures; deferred
  - **Architecture:** `src/smartart_pptx_native/` package
    - `engine.py` — `render(spec, output_dir)` builds carrier `.pptx` from scratch with hand-authored OOXML scaffolding + the three extracted layout XML files + generated data1.xml. No seed unzipping.
    - `data_model.py` — XML construction primitives: `gid`, `make_doc_pt`, `make_node_pt(text, is_asst=False)`, `make_par_trans`, `make_sib_trans`, `make_cxn`, `wrap_data_model`, `build_doc_prset(layout_uri, qs_type_id, cs_type_id)`
    - `builders/flat_list.py` — **generic** flat-list builder handles 22 layouts (Process, Cycle, List, Matrix, Pyramid, Relationship). Accepts `items` canonical key + legacy aliases `steps`/`stages`/`phases`/`nodes`/`labels`.
    - `builders/hierarchical.py` — **generic** hierarchical builder handles 5 layouts (OrgChart, hierarchy2-6). Respects `node_type_capabilities` — only layouts declaring `"asst"` emit `type="asst"` on assistant nodes.
    - `builders/__init__.py` — `BUILDER_BY_DATA_SHAPE` dispatcher. Engine calls `builders.build(data_shape, data, entry)`.
    - `assembler_patch.py` — Stage 2 Python post-process: `inject(host_pptx, requests)` grafts diagram parts from carriers into the assembled deck, allocating fresh rIds per slide rels, fresh diagram numbers per package
    - `pipeline.py` — `run_injection_step(deck_dir)` orchestration wrapper; `format_delivery_message(deck_dir)` speaker-facing status
    - `selector_integration.py` — `is_pptx_native_candidate` / `score_pptx_native_candidate` / `format_selector_rationale` helpers
    - `layouts/catalog.json` (v2.0.0) — **single source of truth for per-layout metadata** (29 entries, `layout_dir` + `qs_type_id` + `cs_type_id` + `data_shape` fields replace Phase 1-7 `seed_path` + `builder_module`). Canonical layouts ordered first so `get_layout_id_for_graphic_type` returns sensible defaults (`flowchart` → `process1`, `cycle` → `cycle2`, `org_chart` → `orgChart1`, etc.)
    - `layouts/catalog.schema.json` — Draft-07 validator for the new v2 shape
    - `layouts/catalog.py` — `load_catalog()`, `get_entry(id)`, `list_entries(v1_only=False)`, `resolve_layout_dir(entry)`, `get_layout_id_for_graphic_type(graphic_type)`, `list_layout_ids_for_graphic_type(graphic_type)`
    - `layouts/catalog_markdown.py` — generator for `docs/pptx-native-smartart-catalog.md` (CI drift detection)
    - `tests/fixtures/smartart_layouts/<id>/` — 29 extracted layout directories × 4 files each (layout.xml, quickStyle.xml, colors.xml, meta.json). All MIT-sourced.
  - **Adding a new layout is a pure catalog change** — zero Python code per layout. Generic builders dispatch by data_shape.
  - **Extraction tool:** `tools/extract_smartart_layouts.py` — walks `dotnet/Open-XML-SDK` repo, downloads every .pptx/.potx, extracts SmartArt layout content into the fixtures dir. `--sdk` mode runs against the full repo in one pass. Safe to rerun — overwrites existing layouts with the latest version. Handles any `.pptx`/`.potx` input if you want to extract from a different source.
  - **Engine integration:** wired into `src/smartart_renderer.py` `_ENGINE_DISPATCH['pptx_native']`. Extractor handles `engine='pptx_native'` with unified data shapes: `{"items": [...]}` for all flat-list graphic types, `{"tree": {...}}` for hierarchical. Org chart extractor parses 2-space-indented body_points with `(asst)` or `[asst]` markers.
  - **JS assembler:** `buildSmartArtSlide` in `src/assembler/build_deck.js` has a pptx_native branch — when `saEntry.engine_used === 'pptx_native'`, emits a named placeholder rect (name format `pptx_native_placeholder_<slide_number>`) instead of `addImage`.
  - **QA checks:** SA-06 (diagram parts present), SA-07 (slide references diagram + no orphaned placeholder), SA-08 (no stale drawing cache). All run post-injection.
  - **Test coverage (290 pptx_native tests, 940 total):** organised by scope:
    - Layout fixture sanity (164 parametrized tests across 27 v1 entries)
    - Catalog + schema + loader
    - Data model primitives
    - Generic builders (flat_list, hierarchical)
    - Engine render end-to-end
    - Extractor routing for all graphic types
    - Dispatch wiring into smartart_renderer
    - Assembler patch injection (spike 3 technique, per-slide + multi-slide)
    - JS placeholder emission
    - QA checks SA-06/07/08
    - Pipeline orchestration wrapper + delivery message
    - Selector integration helpers
    - **Multi-slide deck integration** — proves injection coexists with other strategies via byte-identity check on non-target slides
  - **Validation spikes (all 4 passed in PowerPoint Mac):**
    1. Mutation of process1 seed → editable SmartArt
    2. Generalisation to cycle2 (proves technique crosses algorithm families)
    3. Injection into blank host (proves delivery-time operation works)
    4. Recursive tree builder + assistant nodes for orgChart1
    (Spike 5 — layout stub experiment — obsoleted by Phase 8 full SDK adoption)
  - **Design spec:** `docs/superpowers/specs/2026-04-08-pptx-native-smartart-engine.md`
  - **Spike report:** `docs/spikes/2026-04-08-pptx-native-smartart-injection.md`
  - **Catalog docs:** `docs/pptx-native-smartart-catalog.md` (auto-generated)
  - **Layout provenance + licensing:** `tests/fixtures/smartart_layouts/LICENSING.md` (MIT-sourced, precedent documented)
  - **Extraction manifest:** `tests/fixtures/smartart_layouts/_extraction_manifest.json` (per-layout source trace)
  - **Manual gate checklist:** `tests/manual/MANUAL_GATE.md`
  - **GitHub issue:** #38 (closed), **PR:** #39 (merged 2026-04-10)
  - **Demo deck:** `tools/build_demo_deck.py` — 15-slide "Building AI Agents That Actually Work" conference talk exercising 10 layout types with AI backgrounds and picture embedding
  - **Remaining refinements (not blocking):**
    1. Per-layout capacity constraint refinement (first-pass defaults for non-core layouts)
    2. imagegen-bridge integration for automated image prompts per Picture SmartArt item
    3. Ollama image generation blocked by MLX architecture bug in Ollama 0.20.5 — use cloud (FAL/FLUX) for now
  - **Key design decisions:**
    - SDK as canonical source — all layout content from MIT-licensed `dotnet/Open-XML-SDK` test fixtures. Future Microsoft additions picked up by re-running the extraction script.
    - Generic builders keyed by data_shape, not per-layout modules. Adding a layout is a catalog-only change.
    - Canonical layout ordering in catalog.json (process1, cycle2, orgChart1, list1, matrix2, pyramid2, venn1 first) so reverse lookups return sensible defaults.
    - Injection happens AFTER the JS assembler finishes. JS owns position, Python owns surgery. Contract between them = a named placeholder rect.
    - No drawing1.xml ever written — PowerPoint regenerates the presentation tree from layout1.xml on first open (proven by all 4 spikes).
    - Catalog-driven throughout. Catalog markdown is CI drift-checked — if you edit catalog.json you MUST regenerate the markdown in the same commit.

- **Keynote Pipeline:** Five rendering strategies per slide (expanded from 3, 2026-03-30):
  - `full_render` — entire slide as AI-generated image (title, section divider, closing)
  - `background` — atmospheric AI background + text in template zones (5 variants: left_panel, right_panel, bottom_bar, top_band, center_float)
  - `backdrop` — structured AI scene + vision post-analysis for text positioning (Claude Code vision-analyst agent)
  - `pragmatic_composition` — individual AI-generated elements assembled at exact positions with text labels
  - `composed` — standard PptxGenJS assembly (diagrams, charts, code)
  - `backdrop_render` retained for backward compatibility (maps to `background` with `left_panel`)
  - Three-stage render funnel: Ollama draft (free) → cloud low 720p (cheap) → cloud full 2K+ (production)
  - Prompt Engineer agent (Haiku default, Sonnet escalation) generates creative prompts from structured briefs
  - Post-hoc single-slide upgrade via `upgrade_slide_strategy()`
  - **Spike:** `docs/spikes/backdrop-content-aware-positioning.md`
  - **Implementation plan:** `docs/superpowers/plans/2026-03-30-rendering-strategy-expansion.md` (14 tasks)

- **Production Rendering Engine Strategy (2026-03-31):** Expert-advised two-track production upgrade system
  - **Raster Track (raster_upscale):** Ollama draft → cloud production (FLUX Pro, GPT Image, Nanobanana Flash/Pro)
  - **Vector Track (vector_conversion):** Ollama/FLUX draft → Recraft V4 SVG (standard $0.08, pro $0.30)
  - Image-generation-expert produces `production-upgrade-plan.json` before any money is spent
  - Presentation-reviewer returns per-slide verdicts (pass/escalate_tier/escalate_provider/flag_for_speaker)
  - "Try cheap first" principle: start at cheaper tier, reviewer evaluates, escalate if needed
  - **Spec:** `docs/superpowers/specs/2026-03-31-production-rendering-engine-strategy.md`
  - **Google has TWO image tiers (different APIs):**
    - **Nanobanana** = Gemini image models (`gemini-3-pro-image-preview`, `gemini-3.1-flash-image-preview`). Uses `generate_content` API. Premium tier, best text rendering. Flash $0.067, Pro $0.134.
    - **Imagen** = `imagen-4.0-*` models. Uses `generate_images` API. Cheap tier like FLUX. Fast $0.020, Standard $0.040.
  - **Cross-Tier Prompt Refinement Loop (PR #50, merged 2026-04-19):** Flash proves the prompt works before Pro spends money
    - Image-reviewer extended output: `strengths[]`, `composition_notes{subject_placement, scale_hierarchy, text_rendering}` alongside existing `verdict`/`issues`/`summary`
    - Prompt-engineer refinement mode: takes existing prompt + reviewer feedback, returns refined prompt with COMPOSITION/SCALE sections baked in
    - Imagegen-bridge Step 9A: up to 3 cheap Flash iterations ($0.067 each), prompt-engineer refines between iterations, Pro gets ONE shot with the proven prompt, escalate to speaker on failure
    - **Design spec:** `docs/superpowers/specs/2026-04-19-cross-tier-prompt-refinement-design.md`
    - **Implementation plan:** `docs/superpowers/plans/2026-04-19-cross-tier-prompt-refinement.md`
  - **Two-Tier Google Provider Support (PR #50, merged 2026-04-19):** Wires up all four Google image models through the pipeline
    - `provider_discovery.py`: `tiers` dict on Google result (nanobanana_flash, nanobanana_pro, imagen_fast, imagen_standard with model IDs and costs)
    - `image_router.py`: `tier` field on RoutingTarget/RoutingDecision (defaults to None), `recommended_tier` on UpgradeDecision, real Google API model IDs replace abstract placeholders in routing matrices
    - `render_funnel.py`: `_generate_cloud()` now passes `model` through to `generate_cloud_image()` — previously dropped it, so Google always defaulted to Flash
    - google-image skill: fixed `provider='google_vertex'` → `'google'`, added `--model`/`--tier` params
    - image smart router: content-aware routing (text→Nanobanana, photo→FLUX, budget→Imagen)
    - verify skill: reports Google tiers separately (nanobanana + imagen)
    - **Design spec:** `docs/superpowers/specs/2026-04-19-two-tier-google-provider-design.md`
    - **Implementation plan:** `docs/superpowers/plans/2026-04-19-two-tier-google-provider.md`

- **Dogfood Deck (2026-04-19):** First full pipeline dogfood — 21-slide explainer deck about jack-tar-deckhand
  - Output: `output/jack-tar-deckhand-explainer-v1.pptx` (18.5 MB, $0.20 total)
  - Exercised: 9 SmartArt layouts, 2 charts, 9 Ollama images, 1 Nanobanana Pro image, full assembly + injection + QA
  - 4 pipeline bugs found and fixed: strategy map smartart classification, picture builder text/fill, flat_list dict items
  - Discovered cross-tier prompt refinement pattern (Flash draft → review → refine prompt → verify → Pro)

- **Resolution selection guide (issue #60, 2026-05-06):** Per-slide resolution opt-in via the StrategyMap `resolution` field. Default `1K` covers most slides. Speaker can mark hero/closer slides for `2K` or `4K` rendering through Google Nano Banana Pro/Flash.
  - Choose `2K` when: large display (>120"), mid-detail diagrams, photographic backgrounds with subtle gradients.
  - Choose `4K` when: hero opener / closer that may be photographed and re-shared; text-heavy slides where Nano Banana Pro's better text rendering matters at small body sizes.
  - **Flash 4K vs Pro 4K decision rule:** for `4K` slides, the imagegen-bridge runs an optional Flash 4K pre-test at $0.151 before escalating to Pro 4K at $0.240. If Flash 4K passes review, stop — Flash text rendering at 4K is often comparable to Pro 1K. If Flash 4K refines, proceed to Pro 4K (single shot). Pattern validated end-to-end during the #59 smoke test ($0.659 spend on a 5-stage ladder).
  - **Cost ladder per slide (worst case, 3 Flash refinements + Pro escalation):**
    - 1K: ~$0.335 (3 × $0.067 Flash + $0.134 Pro)
    - 2K: ~$0.437 (3 × $0.101 Flash + $0.134 Pro)
    - 4K: ~$0.693 (3 × $0.151 Flash + $0.240 Pro)
  - A deck with three 4K hero slides represents up to ~$2.08 of image generation spend.
  - **Where it lives:** `slide.resolution` in StrategyMap (schema `strategy_map.schema.json`); render funnel stages `cloud_2k`/`cloud_4k`; image router rows `production_2k`/`production_4k` for hero_image; imagegen-bridge Step 9A Pro escalation honours the requested tier.

- **Recraft V4 raster (issue #61, 2026-05-07):** Promoted from icon-only to first-class raster provider with 1K/2K/4K ladder. Best brand-color fidelity; speakers opt slides in via `brand_fidelity: "exact"` on the StrategyMap entry. Closes EPIC #58.
  - **When Recraft beats Nano Banana / FLUX:** logos, product shots, brand-led hero slides with 3+ specified hexes — Recraft renders exact hex; the others approximate.
  - **When Nano Banana / FLUX beats Recraft:** photorealistic detail, illustrative scenes — Recraft is design-centric, not photo-first.
  - **Recraft V4 vs Nano Banana Pro at 4K decision rule:**
    - Default 4K → Nano Banana Pro ($0.24, photorealistic)
    - `brand_fidelity: "exact"` → Recraft V4 Pro 4K via Creative Upscale chain (~$0.50, brand-fidelity premium)
    - The router's `production_brand_exact_4k` row encodes this; the deckhand image_router auto-derives the routing mode from `slide.brand_fidelity` and `slide.resolution`.
  - **Cost trade-off table (per slide, single-shot):**
    - 1K Recraft Standard: $0.04 — vs FLUX 1K $0.030 (Recraft only ~30% more for hex compliance)
    - 2K Recraft Pro: $0.25 — same flat rate as FAL FLUX 2 Pro 2K
    - 4K Recraft (chain): $0.50 — vs Nano Banana Pro 4K $0.24 (~2× premium)
  - **Implementation:** `generate_recraft_direct` (RECRAFT_API_KEY) and `generate_recraft_fal` (FAL_KEY) in `plugins/jack-tar-cloud/src/generate_cloud_image.py`. 4K is generate-2K-then-`creativeUpscale` chain. `_dispatch_recraft` auto-derives `tier` from `resolution` when caller doesn't specify (1K → standard, 2K/4K → pro), so `generate_cloud_image('x', 'recraft', '/tmp/x.png', resolution='4K')` works without speakers needing to know the tier matrix.
  - **Upscale price assumption:** Direct API upscale price not in public docs; assumed $0.25 (FAL parity). Override via `RECRAFT_UPSCALE_COST_USD` env var if discovered to differ.
  - **New skill:** `/jack-tar-cloud:recraft-image` — per-provider raster skill with `--tier`, `--resolution`, `--colors`, `--style` flags.
  - **Spike:** `docs/spikes/2026-05-07-recraft-creative-upscale.md` — endpoint + pricing findings.
  - **Schema:** `slide.brand_fidelity: "exact" | "approximate" | "none"` on `strategy_map.schema.json`. Default `none`. `approximate` is documentary; only `exact` triggers Recraft routing.

- **Image Reviewer Agent (2026-04-01):** Subagent-based visual quality gate
  - Dispatched per image after generation, returns compact JSON verdict (pass/refine)
  - Keeps images out of main orchestration context — bridge accumulates only summary strings
  - Haiku default, Sonnet escalation after 3 consecutive refine verdicts
  - 5 assessment criteria: artifacts, subject match, palette compliance, composition, strategy fit
  - `accepted_with_issues` status for images passing after max iterations
  - **Spec:** `docs/superpowers/specs/2026-04-01-image-reviewer-agent-design.md`

- **Production Pipeline Learnings (2026-03-31):** First production render documented 11 gaps
  - `docs/changelog/2026-03-31-production-pipeline-learnings.md`
  - Fixes: source_prompt in manifest, per-image review, local-config.json, provider dimension limits

- **Footer:** Metamirror logo bottom-right on every slide (assembler `addFooterLogo()` helper)

- **Architecture Docs:** `docs/architecture/` (10 docs + 7 SVG diagrams, 4 L1 service docs)

- **Existing ollama-* skills are upstream — do NOT fork or modify them.** The imagegen-bridge handles all DeckContext integration.

- **Local config:** `local-config.json` (gitignored) contains machine-specific settings — Ollama model tags, timeouts. Always read this before Ollama commands. Never hardcode model names without tags.

- **Claude Code permissions:** `.claude/settings.local.json` (tracked, per-developer overrides) controls which commands Claude can run silently vs prompts for. The free iteration loop (Ollama draft + slide review) needs minimal prompting — see `docs/dev/claude-permissions-guide.md` for the three-tier model and the exact commands the SmartArt loop needs. Use wildcard prefix matches (`Bash(tool:*)`) over exact strings.

- **CI:** `.github/workflows/validation.yml` runs five jobs on every PR — `code-quality` (flake8 + pre-commit), `plugin-tests` (pytest matrix per plugin), `integration-tests` (cross-plugin contracts), `json-validation` (canonical model + marketplace + per-plugin manifests parse and version-match), and a `summary` PR comment. All jobs must pass before merge. **No `--admin` merging** — if CI fails, fix it.

- **Merge convention:** Use `gh pr merge <n> --merge` (merge commit), never `--squash`. This project ships features through many small fix commits during iteration rounds, and squashing destroys the per-fix granularity.

### Implementation Status

| Module | Location | Tests | Status |
|--------|----------|-------|--------|
| DeckContext management | `src/deckcontext.py` | 10 | Done |
| JSON Schemas (8 contracts) | `src/schemas/` | 27 | Done |
| Image processing | `src/process_image.py` | 19 | Done |
| Provider discovery | `src/provider_discovery.py` | 27 | Done |
| Budget tracker | `src/budget_tracker.py` | 17 | Done |
| Chart renderer | `src/render_chart.py` | 15 | Done |
| Cache manager | `src/cache_manager.py` | 15 | Done |
| Prompt translator | `src/prompt_translator.py` | 20 | Done |
| Cloud image gen | `src/generate_cloud_image.py` | 49 | Done |
| Cloud icon gen | `src/generate_cloud_icon.py` | 28 | Done |
| Image router | `src/image_router.py` | 65 | Done |
| Integration test | `tests/test_integration.py` | 1 | Done |
| Deck assembler | `src/assembler/` | 5 | Done |
| QA checks (30 APs) | `src/qa/` | 65 | Done |
| Phase 5 E2E | `tests/test_phase5_integration.py` | 2 | Done |
| Brand profile utils | `src/brand_profile.py` | 12 | Done |
| Style validation | `src/style_validation.py` | 10 | Done |
| Schema tests (P2) | `tests/test_schemas.py` | 5 | Done |
| Content validation | `src/content_validation.py` | 12 | Done |
| Conductor utils | `src/conductor.py` | 19 | Done |
| Manifest utilities | `src/manifest_utils.py` | 7 | Done |
| SVG rasterisation | `src/process_image.py` | 27 | Done |
| Production upgrade | `src/image_router.py` | 40 | Done |
| Strategy Map schema | `src/schemas/strategy_map.schema.json` | 4 | Done |
| Slide prompt composer | `src/slide_prompt_composer.py` | 20 | Done |
| Prompt engineer agent | `.claude/agents/prompt-engineer.md` | -- | Done |
| Image reviewer agent | `.claude/agents/image-reviewer.md` | -- | Done |
| RenderLog schema | `src/schemas/render_log.schema.json` | 3 | Done |
| Render funnel | `src/render_funnel.py` | 10 | Done |
| Assembler keynote paths | `src/assembler/build_deck.js` | 6 | Done |
| Keynote QA checks | `src/qa/checks/keynote_checks.py` | 5 | Done |
| Strategy-aware QA | `src/qa/run_qa.py` | 65 | Done |
| Pipeline step order | `src/deckcontext.py` | 1 | Done |
| Upgrade slide strategy | `src/conductor.py` | 23 | Done |
| Production upgrade plan | `src/image_router.py`, `src/schemas/` | 11 | Done |
| Template analyser | `src/template_analyser.py` | 36 | Done |
| Template assembler | `src/assembler/build_deck_template.py` | 10 | Done |
| Template integration | `tests/test_template_integration.py` | 12 | Done |
| Notes parser | `src/notes_parser.py` | ~31 | Done |

### Architecture Summary

- **Approach B (Domain-Centric):** Services designed for reuse beyond deck production
- **4 L1 Services:** Content, Design, Image, Assembly & QA
- **6 AI Personas:** Deck Conductor (orchestrator), Image Generation Expert (advisory), Image Reviewer (quality), Presentation Reviewer (advisory), Prompt Engineer (invoker, Haiku/Sonnet), SmartArt Selector (invoker, Haiku/Sonnet)
- **24 Deliverables:** 17 skills + 3 capabilities + 6 agents
- **Naming Convention:** Provider prefix — `ollama-*` for local, `cloud-*` for cloud image skills

### Key Files

| File | Purpose |
|------|---------|
| `.bsa/models/jack-tar-deckhand.json` | Canonical model (single source of truth) |
| `docs/architecture/architecture-overview.md` | One-page architecture summary |
| `docs/architecture/ai-persona-summaries.md` | 6 agent contracts |
| `docs/architecture/diagrams/` | 7 SVG architecture diagrams |
| `research/RESEARCH-INDEX.md` | Research library index with key findings |
| `docs/superpowers/specs/2026-03-29-bsa-architecture-design.md` | Full design decisions |

# AI-First Architecture Toolkit

This project uses the AI-First Business Service Architecture methodology toolkit.

## Methodology Reference

The following file provides complete access to all agents, skills, and methodology references:

@.claude/agents/TOOLKIT-REFERENCE.md

For detailed documentation, see:
- Installation: .claude/agents/TOOLKIT-REFERENCE.md (Agents & Skills section)
- Diagram Tools: .bsa/diagram-tools/README.md
- Design Assets: .bsa/design/

