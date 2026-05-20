# Plan — paperbanana dispatch refactor (CLI-tool framing)

**Status:** ready to execute — operator approved framing A (external CLI tool) on 2026-05-18 after spike findings landed.
**Created:** 2026-05-18
**Working branch:** `feat/v1.4-push-and-paperbanana` (current Ralph branch; refactor happens in-place since Phase 3 was never shipped externally)
**Plan author:** Claude (orchestrator), folding in the 2026-05-17 spike report
**Supersedes:** Phase 3 of `docs/superpowers/plans/2026-05-17-v1.4-push-and-paperbanana.md` (E1–E5 were structurally landed against an invalid contract)
**Cross-reference:**
- Spike report: `~/Documents/Development/paperbanana/tmp/SPIKE_REPORT.md`
- Spike plan: `~/Documents/Development/paperbanana/tmp/SPIKE_PLAN.md`
- Original ADR (to supersede): `docs/architecture/paperbanana-integration.md`
- v1.4 driver: `PROMPT.md`, `.ralph/v1.4-state.json`

---

## 1. Context — why this plan exists

Ralph's v1.4 Run 2 (2026-05-17) landed Phase 3 deliverables E1 through E5 — `paperbanana_dispatch.py` (285 lines), `strategy_classifier.py`, verify-skill paperbanana row, persona docs, and the architecture ADR. The code was contract-tested via mocks. **The mocks were wrong.**

A focused 2-invocation spike against the real `llmsresearch/paperbanana` CLI ($0.28 spend, both renders passed independent visual review) confirmed:

- **Dispatch args contract is wrong in every field.** jack-tar sends `{subject, output_path, slide_number, context, palette_hex}`; paperbanana wants `{source_context, caption, aspect_ratio, iterations}`. Zero overlap.
- **Availability detection is wrong.** Probes for `.claude-plugin/plugin.json` — paperbanana is not a Claude Code plugin and ships no such file. Detection returns False even when paperbanana is runnably installed via pip.
- **Output path is wrong.** paperbanana writes to `<dir>/run_<ts>_<hash>/final_output.png`; CLI's `--output` honours only the parent directory; MCP path may re-compress to `.mcp.jpg` for PNGs >3.75 MB.
- **Transport model is wrong.** ADR assumed Claude-Code Skill cross-invocation; paperbanana's canonical Claude Code integration is via MCP server, and the simpler integration is CLI subprocess.

Quality verified: paperbanana clearly outperforms Nano Banana Flash 1K baseline on academic-figure subjects. The substrate is right; the integration is what's broken.

---

## 2. Reframing — paperbanana as external CLI tool (sibling orchestrator)

**The new framing.** paperbanana is treated like LaTeX, ImageMagick, or ffmpeg — an external dependency the operator installs (`pip install paperbanana[google]` in jack-tar's venv, OR `pipx install`, OR `uvx`), and jack-tar shells out to it via subprocess on demand.

**Two complementary orchestrators, not host/plugin.** jack-tar runs the deck pipeline (brand → style → narrative → SmartArt → image → assembly → QA). paperbanana runs the figure pipeline (Retriever → Planner → Stylist → Visualizer → Critic). They specialise (decks vs academic figures) and compose via a stable text-in/image-out interface (CLI). Neither owns the other.

**What changes in concrete terms:**

| Concern | Old framing (plugin) | New framing (CLI tool) |
|---|---|---|
| Detection | filesystem probe × 3 paths for `.claude-plugin/plugin.json` | `shutil.which("paperbanana")` with optional `importlib.util.find_spec` |
| Install instructions | `/plugin marketplace add … && /plugin install` | `pip install 'paperbanana[google]'` (or `pipx`, or `uvx`) |
| Dispatch transport | "Skill cross-invocation" via `paperbanana:generate-diagram` | `subprocess.run([paperbanana, generate, ...])` |
| Output path | jack-tar dictates via `output_path` arg | jack-tar accepts whatever paperbanana writes |
| Budget enforcement | jack-tar tallies everything | delegate to `paperbanana --budget` |
| Verify-skill row | "OPTIONAL SKILL PLUGINS" | "EXTERNAL TOOLS" |
| Upstream contribution scope | `.claude-plugin/plugin.json` PR | pricing table + default-model PRs only |

**Deferred to v1.4.1+ (NOT in scope for this refactor):** MCP transport. Requires jack-tar's bridge to grow an MCP-dispatch primitive worth building. Right answer eventually; not the right scope now.

---

## 3. Task list — 6 tasks, ordered

Each task includes the file(s) it touches, the change shape, and the verification gate that proves it done.

### Task 1 — Rewrite `is_paperbanana_available()`

- **File:** `plugins/jack-tar-deckhand/src/paperbanana_dispatch.py:90–131`
- **Change:** replace the three-path filesystem probe with:
  ```python
  def is_paperbanana_available() -> bool:
      import importlib.util, shutil
      if importlib.util.find_spec("paperbanana") is not None:
          return True
      return shutil.which("paperbanana") is not None
  ```
  Drop `PAPERBANANA_ROOT_ENV`, `_DEFAULT_SEARCH_ROOTS`, the `env=` and `fs_exists=` parameters. Function is now zero-arg and 5 lines.
- **Why:** spike empirically confirmed `find_spec` returns the module when pip-installed in jack-tar's venv, and `which` covers the pipx / uvx cases.
- **Verification gate:** unit test with paperbanana actually pip-installed in the test venv returns True; unit test with paperbanana absent returns False. No mocked filesystem fixtures.

### Task 2 — Rewrite `build_dispatch_payload()`

- **File:** `plugins/jack-tar-deckhand/src/paperbanana_dispatch.py:152–233`
- **Change:** emit the real contract:
  ```python
  args = {
      "source_context": _build_source_context_from_slide(slide),
      "caption": _build_caption_from_slide(slide),
      "aspect_ratio": "16:9",   # match slide canvas
      "iterations": int(slide.get("paperbanana_iterations", 1)),
  }
  ```
  Drop `subject`, `output_path`, `slide_number` (it stays at the dispatch struct level for manifest accounting, not in args), `context`, `palette_hex` (paperbanana has no palette-injection surface — flag in §7 finding F2).

  Add two new helpers:
  - `_build_source_context_from_slide(slide)` — synthesises a methodology-style paragraph (5–20 sentences) from `speaker_notes + body_points + visual_direction`. Spike found a headline is too thin for paperbanana's Retriever agent.
  - `_build_caption_from_slide(slide)` — extracts the one-line figure caption from `headline / title` (semantic shape: communicative intent, not the figure's description).
- **Why:** spike report §2 (input contract) + §9.1 (source_context is methodology TEXT, not free-text subject). Without `_build_source_context_from_slide` the Retriever agent fires with insufficient context and quality drops.
- **Verification gate:** unit test asserting args dict shape matches the four-key contract; helper unit test asserting a synthesised source_context is ≥5 sentences when speaker notes are present.

### Task 3 — Rewrite `build_manifest_entry()`

- **File:** `plugins/jack-tar-deckhand/src/paperbanana_dispatch.py:236–285`
- **Change:**
  - `file_path` accepts whatever paperbanana returns verbatim — variable run-id path, possibly `.mcp.jpg` extension. Drop the deterministic `slide-NN-academic-fig.png` filename construction at the dispatch struct level.
  - Add `caption` field separate from `source_prompt` so iterate-slide (#89) can re-call `paperbanana generate --continue-run <id> --feedback` cheaply.
  - Add `paperbanana_run_id` field — parsed from the returned path's `run_<ts>_<hash>` directory name. Enables `paperbanana runs show <id>` for audit + cheap iterate-slide refinement.
- **Why:** spike report §9.2 (output_path not honourable) + §9.3 (MCP re-compression to `.mcp.jpg`).
- **Verification gate:** unit test for each of: PNG return, `.mcp.jpg` return, missing run_id (paperbanana didn't write to a run dir for some reason — graceful degradation).

### Task 4 — Update verify-skill (CLI-tool framing)

- **File:** `plugins/jack-tar-deckhand/skills/verify/SKILL.md`
- **Change:**
  - **Replace Step 2.5** with a three-part probe: (a) `command -v paperbanana` for PATH check, (b) `paperbanana doctor` parse for `GOOGLE_API_KEY` and `google-genai` status when on PATH, (c) inline install guidance when absent.
  - **Rename Step 5's section** "OPTIONAL SKILL PLUGINS" → "EXTERNAL TOOLS"; rename the capability row "ACADEMIC FIGURE" → "Academic figures" for consistency with other rows.
  - **Inline install guidance template:**
    ```
    paperbanana CLI:   NOT_FOUND
    Academic figures:  FALLBACK — academic_figure slides will use Nano Banana Flash 1K
                       with academic-figure-aware prompting (acceptable but not
                       publication-tier).

    To install paperbanana:
      pip install 'paperbanana[google]'           # simplest — in jack-tar venv
      pipx install 'paperbanana[google]'          # global CLI without polluting venvs
      uvx --from 'paperbanana[mcp]' paperbanana-mcp   # MCP server (v1.4.1+ candidate)

    After install:
      1. Get a free Gemini key:  https://makersuite.google.com/app/apikey
      2. Export GOOGLE_API_KEY:  export GOOGLE_API_KEY=...
      3. Smoke test:             paperbanana doctor
      4. Re-run /verify
    ```
- **Why:** spike confirmed pip-installed paperbanana with no `.claude-plugin/plugin.json` is the normal install state. Detection must match. Inline install guidance is surfaced at the exact moment operators look for it.
- **Verification gate:** run `/jack-tar-deckhand:verify` in a venv with paperbanana installed → reports READY; uninstall paperbanana → reports NOT_FOUND with install guidance; install paperbanana but unset GOOGLE_API_KEY → reports PARTIAL with hint about the missing key.

### Task 5 — Update persona docs + supersede the ADR

- **Files:**
  - `plugins/jack-tar-deckhand/skills/narrative-architect/SKILL.md` — update the academic-figure annotation section to reflect: paperbanana is an external CLI dep (not a plugin), install via pip, methodology context is required (synthesised from speaker notes if absent).
  - `plugins/jack-tar-deckhand/agents/smartart-selector.md` — academic-figure deferral rule wording unchanged but check the install-pointer language.
  - `docs/architecture/paperbanana-integration.md` — **mark superseded.** Add header pointing to the new ADR.
  - `docs/architecture/paperbanana-integration-v2.md` (NEW) — clean replacement ADR documenting CLI-tool framing, real contract surface, real fallback behaviour, real operator install guide.
- **Why:** the old ADR §3 (Option 4 skill cross-invocation), §4 (contract surface), and §6 (operator install via `/plugin install`) are all fictional. The new ADR documents reality.
- **Verification gate:** old ADR shows "Status: Superseded by [v2]" header; new ADR contains the four sections (decision, contract, fallback, install) reflecting CLI-tool framing; both persona docs updated to match.

### Task 6 — Update tests

- **Files:**
  - `plugins/jack-tar-deckhand/tests/test_paperbanana_dispatch.py` — 14 tests, all currently locking in the wrong shape. Rewrite around the four-key args contract, the `_build_source_context_from_slide` helper, and the new manifest entry shape with `paperbanana_run_id`.
  - `plugins/jack-tar-deckhand/tests/test_verify_skill_paperbanana.py` — 3 tests, currently asserting filesystem-probe behaviour. Rewrite with `which` + `find_spec` fixtures.
- **Why:** tests must lock in the new shape, not the old one.
- **Verification gate:** `pytest plugins/jack-tar-deckhand/tests/test_paperbanana_dispatch.py plugins/jack-tar-deckhand/tests/test_verify_skill_paperbanana.py -v` → all green. Full deckhand suite (103 tests pre-refactor) still green after task 6 lands.

---

## 4. E6 dogfood gate — the real validation

After all 6 refactor tasks land:

1. **Install paperbanana** in the jack-tar venv: `cd ~/Documents/Development/jack-tar-deckhand && .venv/bin/pip install 'paperbanana[google]'` (or use the existing clone at `~/Documents/Development/paperbanana` via `pip install -e ~/Documents/Development/paperbanana`).
2. **Run `/jack-tar-deckhand:verify`** — expect READY for paperbanana.
3. **Author a single-slide test deck** with one academic_figure slide (use the Transformer methodology from `~/Documents/Development/paperbanana/examples/sample_inputs/transformer_method.txt` as speaker notes; caption: "Transformer encoder architecture for sequence classification").
4. **Run the imagegen-bridge through the slide.** Expected behaviour: bridge classifies as academic_figure, dispatches via `subprocess.run([paperbanana, generate, --input <tmp file>, --caption ..., --aspect-ratio 16:9, --iterations 1, --image-model gemini-3.1-flash-image-preview, --output <deck images dir>, --budget 0.20])`, reads back the returned `run_*/final_output.png`, writes manifest with `paperbanana_run_id`.
5. **Visual review** the rendered figure via `general-purpose` subagent (NOT a direct PNG Read).
6. **Cost check:** spend should be ~$0.07–$0.14 per the spike's empirical data. Hard cap on this dogfood: $0.30.
7. **Log** at `docs/superpowers/dogfooding/2026-05-18-paperbanana-integration.md`:
   - The exact subprocess command that ran
   - Time elapsed
   - True spend (Gemini console)
   - Manifest entry produced
   - Visual verdict + comparison to Nano Banana Flash baseline (if appetite for a $0.07 comparative test)

**Gate outcome:**
- ✅ Pass: figure renders, manifest correct, visual review verdict pass → mark Phase 3 done in `.ralph/v1.4-state.json`, push, open PR for the refactor + dogfood as one commit chain.
- ❌ Fail: write `V1.4-BLOCKER.md` at repo root explaining what broke; do not proceed to phases 4a/4b/5a/5b.

---

## 5. Side PRs to upstream `llmsresearch/paperbanana`

Parallel, low priority, do NOT gate the v1.4 refactor:

| Upstream PR | Severity | Effort | What |
|---|---|---|---|
| Pricing table missing Gemini 3.x image preview models | medium | 30 min | Add entries for `gemini-3.1-flash-image-preview` ($0.067/1K) and `gemini-3-pro-image-preview` ($0.134/1K, $0.240/4K) to `paperbanana/core/pricing.py` so `--budget` enforces real cost. |
| Default models point at deprecated `gemini-2.0-flash` | medium | 1h | Bump defaults in `paperbanana/core/config.py:22,29` + `providers/vlm/gemini.py:31` + `providers/image_gen/google_imagen.py:28` to `gemini-2.5-flash` and `gemini-3.1-flash-image-preview` so first-run doesn't ClientError. |
| Version inconsistency: pyproject.toml=0.1.2, server.json=0.1.1 | low | 5 min | Unify on `0.1.2` (the higher) or whatever upstream prefers. |

PR-readiness already established by spike: MIT licence, no CLA, 7 distinct recent external contributors, ~4–5 day median merge latency. CONTRIBUTING.md flow: fork → branch from main → pytest + ruff → PR.

Open as three separate small PRs, not one batch — easier to review, easier for upstream to merge selectively.

---

## 6. Issues to file before starting

| Issue | Repo | Purpose |
|---|---|---|
| `fix(jack-tar-deckhand): paperbanana_dispatch refactor — detection, args, and manifest contract are wrong end-to-end` | `SteveGJones/jack-tar-deckhand` | Tracks the 6 tasks in §3 + the E6 gate in §4. Body links to this plan and the spike report. |
| `fix(ralph integration): loop framework declares "completed" while state.status says "in_progress"` | `SteveGJones/jack-tar-deckhand` | Tracks the false-completion defect surfaced by Run 2. Body documents the cross-check rule (`.ralph/v1.4-state.json` truth vs loop framework verdict) so the next overnight session catches it. |
| Pricing table missing Gemini 3.x image preview models | `llmsresearch/paperbanana` | Side PR per §5. |
| Out-of-box defaults point at deprecated `gemini-2.0-flash` | `llmsresearch/paperbanana` | Side PR per §5. |
| Version inconsistency between pyproject.toml and server.json | `llmsresearch/paperbanana` | Side PR per §5. |

The `.claude-plugin/plugin.json` upstream PR is **NOT** opened — the CLI-tool framing makes it architecturally unnecessary.

---

## 7. Findings folded in from the spike (reference only — no separate action)

Each of these is addressed by one of the tasks above; listed here so future readers can trace WHY the refactor is shaped the way it is.

- **F1: dispatch args contract is wrong end-to-end** → Task 2
- **F2: palette injection unsupported upstream** → Task 2 drops `palette_hex`. **Implication for strategy classifier:** if `slide.brand_fidelity == "exact"` AND classifier wants to label `academic_figure`, refuse the route and either downgrade or surface to speaker. **NOT in this refactor's scope** — file as follow-up issue if it bites in dogfood.
- **F3: output path not honourable** → Task 3 (`file_path` accepts paperbanana's return verbatim)
- **F4: MCP path re-compression to `.mcp.jpg` for PNGs >3.75 MB** → Task 3 accepts variable extension. CLI transport sidesteps this entirely; MCP transport (deferred to v1.4.1+) would need explicit handling.
- **F5: detection function probes wrong marker** → Task 1
- **F6: paperbanana's pricing table is incomplete** → §5 upstream PR
- **F7: paperbanana's default models are deprecated** → §5 upstream PR; jack-tar dispatch passes explicit `--image-model` + `--vlm-model` on every call (Task 2) so we don't depend on upstream defaults
- **F8: paperbanana version inconsistency** → §5 upstream PR (cosmetic)
- **F9: source_context expectation is methodology paragraphs (5–20 sentences)** → Task 2 adds `_build_source_context_from_slide()` helper
- **F10: aspect_ratio default ~3:4 vs 16:9 slide canvases** → Task 2 hard-codes `aspect_ratio="16:9"` for academic_figure (may need flexibility later; YAGNI for v1.4)
- **F11: run directory has substantial debug trail (`metadata.json`, `planning.json`, `prompts/`, per-iter intermediates)** → Task 3 records the `run_id`; cleanup helper deferred unless dogfood shows disk growth is problematic

---

## 8. Re-entry into Ralph (after refactor lands)

Once Tasks 1–6 + E6 dogfood are green:

1. Update `.ralph/v1.4-state.json`:
   - `phases.phase_3_e6_dogfood.status: done` (with the dogfood log path in `artifacts`)
   - `current_phase: phase_4a_text_density`
   - `current_step: not_started`
   - `verification_spent_usd: <actual spend from §4>`
2. Update `PROMPT.md` — add to §1 a one-line note "Phase 3 paperbanana refactor landed 2026-05-18; resume from phase_4a". Important so Ralph doesn't re-walk Phase 3.
3. **DO NOT trust Ralph's loop-framework "completed" verdict** when next run terminates. Cross-check `.ralph/v1.4-state.json`. (Tracked separately via the second issue in §6.)
4. Resume Ralph with the same hard rules as the original v1.4 push: $5.00 cap, Imagen Fast 1K / Flash 1K only, Pro 4K prohibited, image review only via subagent dispatch.

---

## 9. Hard rules

- **No `.claude-plugin/plugin.json` stub** anywhere — neither in this repo nor a thin-wrapper marketplace repo. CLI-tool framing makes the file unnecessary; adding it would re-invite the Plugin mental model the spike rejected.
- **No pip-dep on paperbanana inside jack-tar's `pyproject.toml`** — paperbanana must remain an OPTIONAL operator-installed CLI. Tests that exercise the dispatch path skip (not fail) when paperbanana isn't installed; e2e dogfood is the only place that demands it.
- **No `--image-model` hard-coding in production paths** other than `gemini-3.1-flash-image-preview` (Flash 1K) for v1.4. Pro 4K stays prohibited until budget telemetry is rebuilt around paperbanana's true-cost reporting (§5 upstream PR).
- **No PNG `Read` in the orchestration context** during dogfood — all visual review goes through subagent dispatch. The repo's `PreToolUse` hook enforces this in this session; the dogfood log must record the subagent's verdict, not a direct read.
- **Branch + PR, no force-push** — commit each task as a separate atomic commit; PR the lot at the end. Use `gh pr merge --merge`, not `--squash` (project convention preserves iteration history).

---

## 10. Verification gates summary

| Stage | Gate | How to verify |
|---|---|---|
| Task 1 done | detection works against real install | `python3 -c "from paperbanana_dispatch import is_paperbanana_available; print(is_paperbanana_available())"` returns True with paperbanana pip-installed, False without |
| Task 2 done | dispatch args match real contract | unit tests assert exact dict shape; `_build_source_context_from_slide` returns ≥5 sentences for a slide with speaker notes |
| Task 3 done | manifest entry accepts variable returned path | unit tests parametrise over PNG, .mcp.jpg, and missing-run-id cases |
| Task 4 done | verify-skill reports correct status | manual run with paperbanana installed → READY; uninstalled → NOT_FOUND with install hint visible |
| Task 5 done | old ADR superseded, new ADR exists, personas updated | filesystem check + spot-read |
| Task 6 done | tests green | `.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_paperbanana_dispatch.py plugins/jack-tar-deckhand/tests/test_verify_skill_paperbanana.py -v` → all pass, full deckhand suite still 103/103 green |
| E6 gate | real academic_figure renders + manifest correct | dogfood log at `docs/superpowers/dogfooding/2026-05-18-paperbanana-integration.md` with subprocess command, time, spend, manifest entry, visual verdict |

---

## 11. Time and cost estimate

| Phase | Effort | Spend |
|---|---|---|
| Tasks 1–6 refactor (Sonnet/Opus, judgement work) | 3–5 hours | $0 (no API spend; mocked unit tests) |
| E6 dogfood (single academic_figure slide) | 30 min wall time | ~$0.07–$0.14 Gemini |
| Side PRs to paperbanana upstream (parallel, optional) | 1–2 hours each | $0 |
| **Total to "Phase 3 genuinely done"** | **half a day** | **<$0.30** |

Then Ralph resumes Phase 4a (text density warning, #91) — out of scope for this plan.

---

## 12. Rollback / recovery

If E6 dogfood fails:

- **Failure mode A — paperbanana CLI invocation crashes.** Capture stdout/stderr, file an upstream bug, decide whether jack-tar's dispatch should catch the failure and degrade to Flash 1K fallback (probably yes — same shape as paperbanana being absent).
- **Failure mode B — figure renders but quality is unusable.** Check `aspect_ratio`, check the synthesised `source_context` is rich enough (try with more speaker-notes content), check the caption is well-formed. If still bad, this is a meaningful spike-followup: paperbanana's quality on slide-shaped subjects is different from the spike's portrait test cases. Write findings to dogfood log, decide whether Phase 3 ships at v1.4 or defers to v1.5.
- **Failure mode C — cost overshoots by >2x of spike's $0.14 baseline.** Investigate whether iterations crept up, whether the `source_context` ballooned VLM spend, whether paperbanana's `--budget` is enforcing what it claims (likely not — see §5 upstream PR #1).

All three failure modes write `V1.4-BLOCKER.md`. None justify proceeding to Phase 4.
