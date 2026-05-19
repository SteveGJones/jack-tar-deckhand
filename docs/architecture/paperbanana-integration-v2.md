# Paperbanana Integration — Architecture Decision Record (v2)

**Status:** Accepted — supersedes [paperbanana-integration.md](paperbanana-integration.md) (2026-05-17, v1)
**Date:** 2026-05-18
**Plan:** [docs/superpowers/plans/2026-05-18-paperbanana-dispatch-refactor.md](../superpowers/plans/2026-05-18-paperbanana-dispatch-refactor.md)
**Spike:** `~/Documents/Development/paperbanana/tmp/SPIKE_REPORT.md` (out of repo)
**Decision-makers:** operator + Claude (2026-05-18, after the 2026-05-17 spike)
**Issue:** [#94](https://github.com/SteveGJones/jack-tar-deckhand/issues/94)

---

## 1. Context

[paperbanana](https://github.com/llmsresearch/paperbanana) is an open-source Python package and MCP server that renders publication-quality scientific figures — methodology diagrams, training curves, ablation plots, architecture sketches — via a multi-agent pipeline (Retriever → Planner → Stylist → Visualizer → Critic) over Google Gemini.

A 2026-05-17 spike (2 invocations against the real CLI, both passed independent visual review at $0.28 total Gemini spend) confirmed paperbanana clearly outperforms Nano Banana Flash 1K baseline on academic-figure subjects. The substrate is right for the `academic_figure` rendering strategy in jack-tar-deckhand.

The v1 ADR (2026-05-17, [now superseded](paperbanana-integration.md)) assumed paperbanana was a Claude Code plugin we'd invoke via skill cross-invocation. That assumption was wrong. The integration code Ralph wrote during Phase 3 (E1–E5) targets a fictional contract, never ran paperbanana once, and detects paperbanana by probing for a marker file it doesn't ship.

This v2 ADR documents the real framing, the real contract, and the real operator install path.

---

## 2. Decision

**Framing:** paperbanana is an **external CLI tool** (sibling orchestrator), not a Claude Code plugin. It is treated like LaTeX, ImageMagick, or ffmpeg — an external dependency operators install via `pip install 'paperbanana[google]'` (or `pipx` / `uvx`), and jack-tar shells out to it via subprocess on demand.

**Transport:** CLI subprocess for v1.4. MCP server transport is a v1.4.1+ candidate.

**Composition:** two complementary orchestrators sharing a stable text-in/image-out interface:
- **jack-tar pipeline** — brand → style → narrative → SmartArt → image → assembly → QA
- **paperbanana pipeline** — Retriever → Planner → Stylist → Visualizer → Critic

They specialise (decks vs academic figures) and compose via the CLI. Neither owns the other. This is the Unix-philosophy framing: each does one thing well, the contract is small and inspectable, replacement or upgrade is local.

### Rationale

- **Matches paperbanana's actual distribution model.** paperbanana ships as a PyPI package with bundled Claude Code skills + an MCP server. It has no `.claude-plugin/plugin.json` and was never designed to be `/plugin install`-able. Framing it as a CLI tool is congruent with how the project distributes itself.
- **Smallest refactor surface.** Detection becomes a 5-line `find_spec` + `which` probe. Args become a four-key dict matching paperbanana's real signature. Output handling defers to paperbanana's run-directory layout. No new infrastructure required.
- **Decouples release cycles.** paperbanana versions independently on its own cadence; jack-tar never pins a Python dependency on paperbanana. Operators upgrade paperbanana when they want to; jack-tar's pipeline doesn't break.
- **Leverages paperbanana's own cost-safety controls.** The `--budget` flag (when its pricing table catches up — upstream issue #213) caps spend per call. The `--cost-only` and `--dry-run` flags allow projection without spend.
- **Surfaces install guidance at the failure moment.** The verify-skill's NOT_FOUND case emits the install command inline — operators see the fix exactly when they need it.

### Alternatives considered and rejected

| Option | Sketch | Why rejected |
|---|---|---|
| **MCP transport (Option B in plan §2)** | jack-tar's bridge dispatches `mcp__paperbanana__generate_diagram` directly. | Cleanest Claude-Code-native shape, but jack-tar's bridge has no MCP-dispatch primitive today — would need building. No `--output dir` control, no `--budget`, and the MCP path may re-compress to `.mcp.jpg` for PNGs >3.75 MB. Right answer eventually; v1.4.1+ candidate. |
| **Python library import (Option C)** | `from paperbanana import PaperBananaPipeline` as a hard dep in jack-tar's venv. | Lowest overhead but couples release cycles (paperbanana pulls in pydantic, google-genai, pillow, typer; version conflicts harvestable later). v1 ADR §3 rationale "no pip dependency chain" stands. CLI gets us 95% of the benefit without the coupling. |
| **v1 framing: skill cross-invocation** | `paperbanana:generate-diagram` via Claude Code's Skill tool. | The `paperbanana:` skill namespace doesn't exist (paperbanana isn't a marketplace plugin). paperbanana's own SKILL.md files have no namespace prefix. This was the v1 ADR's assumption, surfaced as fictional by the spike. |
| **PR a `.claude-plugin/plugin.json` upstream** | Make paperbanana installable as a Claude Code plugin. | Would push paperbanana toward a distribution model that doesn't suit it (it's a Python package + MCP server, not a Claude Code skill bundle). Spike concluded this is the wrong shape of contribution; valuable upstream PRs are pricing-table + default-model fixes (issues #213, #214 upstream). |

### Confidence

**High** on the framing and contract direction. The 2026-05-17 spike empirically verified:
- Real arg contract (`{source_context, caption, aspect_ratio, iterations}`) via SKILL.md + CLI signature + Python API examples
- Quality bar (2 visual-reviewer-confirmed publication-grade outputs)
- Cost (~$0.14 per academic figure, 2 iterations, Flash 1K)
- Detection via `find_spec` + `which` works against real install
- Install paths (pip, pipx, uvx) all viable

**Medium** on the operator-experience trade-offs. The CLI-subprocess transport adds ~150 ms process-spawn overhead per slide vs in-process. For deck pipelines with 1–5 academic_figure slides, that's negligible; for batch-figure workflows (>20 figures), MCP transport will be worth the v1.4.1 refactor.

---

## 3. Detection mechanism

`paperbanana_dispatch.is_paperbanana_available()` (`plugins/jack-tar-deckhand/src/paperbanana_dispatch.py`) probes:

```python
import importlib.util, shutil
if importlib.util.find_spec("paperbanana") is not None:
    return True
return shutil.which("paperbanana") is not None
```

Two layers:

1. **`find_spec`** — covers pip-installed-in-jack-tar-venv. The most common install path for v1.4 dogfood. Catches the case where the operator runs `pip install 'paperbanana[google]'` inside `jack-tar-deckhand/.venv`.
2. **`shutil.which`** — covers pipx, system install, and active venv. Catches the case where the operator installed paperbanana globally (or via `uvx`) and only the CLI is on PATH; the Python package isn't on jack-tar's `sys.path`.

Either check returning True is sufficient. Filesystem checks for `.claude-plugin/plugin.json` are NOT performed — that marker doesn't exist on paperbanana installs.

---

## 4. Contract surface

The integration surface between jack-tar-deckhand and paperbanana is **one subprocess invocation** + **availability check**. That's it.

### 4.1 CLI invocation (the v1.4 transport)

```
paperbanana generate \
  --input <tmpfile-with-source-context-text> \
  --caption "<one-line communicative intent>" \
  --aspect-ratio 16:9 \
  --iterations <n> \
  --image-model gemini-3.1-flash-image-preview \
  --vlm-model gemini-2.5-flash \
  --output <output_dir> \
  --budget <slide-envelope-usd>
```

The bridge (`plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md` Step 4.6) constructs this from `paperbanana_dispatch.build_dispatch_payload()` output. Note:

- `--vlm-model` and `--image-model` are passed explicitly on every call (work around paperbanana's deprecated defaults — upstream issue #214).
- `--budget` is passed as a belt-and-braces guard; jack-tar's own budget accounting is the authoritative gate because paperbanana's pricing table is incomplete (upstream issue #213).
- `--output` is the **parent directory** paperbanana writes its run subdirectory into. The caller does NOT control the run-id or filename — paperbanana writes `<output_dir>/run_<YYYYMMDD>_<HHMMSS>_<short-hash>/final_output.png` unconditionally. The bridge reads back from this path after the subprocess exits.

### 4.2 Availability detection

```python
from paperbanana_dispatch import is_paperbanana_available
if is_paperbanana_available():
    # dispatch via subprocess
else:
    # cloud Flash 1K fallback
```

Probes runnability (`find_spec` + `which`), not installation marker. See §3.

### 4.3 Manifest entry

Each academic-figure slide writes an `image-manifest.json` entry shaped:

```json
{
  "slide_number": 7,
  "file_path": "<output_dir>/run_<ts>_<hash>/final_output.png",
  "status": "generated",
  "image_id": "slide-07-academic-figure",
  "model_used": "paperbanana",
  "backend": "paperbanana",
  "source_prompt": "<the source_context methodology paragraph>",
  "caption": "<the figure caption>",
  "content_hash": "<sha256>",
  "paperbanana_run_id": "run_<ts>_<hash>",
  "paperbanana_args": {
    "source_context": "...",
    "caption": "...",
    "aspect_ratio": "16:9",
    "iterations": 1
  }
}
```

When paperbanana was absent and the bridge took the cloud fallback:
- `backend` becomes `"cloud_fallback"`
- `model_used` becomes `dispatch.fallback_model` (default `"gemini-3.1-flash-image-preview"`)
- `paperbanana_run_id` and `paperbanana_args` are omitted
- `fallback_reason` is added (human-readable explanation)

Downstream consumers:
- production-upgrade-plan reads `model_used` + `backend` to know which slides got publication-tier rendering vs fallback
- QA checks treat `backend: paperbanana` slides as exempt from generic SmartArt quality rules
- iterate-slide (#89) reads `paperbanana_run_id` + `paperbanana_args` to re-call paperbanana via `--continue-run <id> --feedback "<note>"` for cheap critique-driven refinement instead of re-running from scratch

### 4.4 Output-file handling

- **Format:** PNG by default. Paperbanana CLI supports `--format png|jpeg|webp`. Manifest stores whatever extension paperbanana wrote.
- **MCP edge case:** if jack-tar ever switches to MCP transport (v1.4.1+), paperbanana may re-compress PNGs >3.75 MB to `<dir>/final_output.mcp.jpg`. The manifest `file_path` field accepts this verbatim (regression-tested in the dispatch module).
- **Side files:** paperbanana writes substantial debug artefacts to the run directory (`metadata.json`, `planning.json`, `prompts/`, per-iteration intermediates). jack-tar does NOT clean these up automatically — operators can `paperbanana runs delete <id>` periodically. Disk-growth follow-up filed if dogfood shows pain.
- **Determinism boundary:** jack-tar does not cache paperbanana output (the deckhand cache manager skips slides with `strategy: academic_figure`). Paperbanana owns its own cache strategy via `runs continue`.

---

## 5. Fallback behaviour

When paperbanana is not detected (or detected-but-broken), the bridge takes the cloud-fallback path **silently in pipeline terms but loudly in the manifest and verify-skill output**:

| Surface | Behaviour when paperbanana absent |
|---|---|
| `is_paperbanana_available()` | returns False |
| `build_dispatch_payload()` | returns `PaperbananaDispatch(available=False, …)` with `fallback_provider="google"`, `fallback_model="gemini-3.1-flash-image-preview"`, populated `fallback_reason` |
| imagegen-bridge Step 4.6 | dispatches Nano Banana Flash 1K with academic-figure-aware prompting instead of paperbanana CLI |
| manifest entry | `backend: "cloud_fallback"`, `model_used: "gemini-3.1-flash-image-preview"`, `fallback_reason` populated |
| `/jack-tar-deckhand:verify` | reports `Academic figures: FALLBACK (paperbanana not installed — Flash 1K fallback active)` with inline install guidance |

Pipeline never blocks on paperbanana absence. The deck always ships; only the academic-figure tier degrades from publication to acceptable.

---

## 6. Operator install guide

To enable paperbanana routing on a developer machine:

### 6.1 Install in jack-tar's venv (simplest)

```
cd ~/Documents/Development/jack-tar-deckhand
.venv/bin/pip install 'paperbanana[google]'
```

`find_spec("paperbanana")` returns True from inside jack-tar's venv → `is_paperbanana_available()` returns True. No further configuration.

### 6.2 Install via pipx (global CLI, no venv pollution)

```
pipx install 'paperbanana[google]'
which paperbanana   # → ~/.local/bin/paperbanana
```

`shutil.which("paperbanana")` returns the path → `is_paperbanana_available()` returns True from any context.

### 6.3 Install via uvx (MCP server transport, v1.4.1+ candidate)

```
uvx --from 'paperbanana[mcp]' paperbanana-mcp
```

Then wire MCP config in `~/.claude/claude_code_config.json`:

```jsonc
{
  "mcpServers": {
    "paperbanana": {
      "command": "uvx",
      "args": ["--from", "paperbanana[mcp]", "paperbanana-mcp"],
      "env": {
        "GOOGLE_API_KEY": "...",
        "GOOGLE_IMAGE_MODEL": "gemini-3.1-flash-image-preview"
      }
    }
  }
}
```

v1.4 doesn't use this path — jack-tar's bridge dispatches CLI subprocess, not MCP. v1.4.1+ may switch if MCP transport proves valuable.

### 6.4 Setup checklist (any install method)

```
1. Get a free Gemini key:  https://makersuite.google.com/app/apikey
2. Export GOOGLE_API_KEY:  export GOOGLE_API_KEY=...
3. Smoke test:             paperbanana doctor
4. Verify jack-tar sees it: /jack-tar-deckhand:verify
                            → Academic figures: READY
```

### 6.5 When to opt slides into `academic_figure`

The strategy classifier auto-labels when it sees two or more academic signals in the slide content (regression / ablation / attention / method diagram / training curve / loss landscape / Figure N caption / equation / citation). The narrative-architect persona may suggest the label when the speaker is aiming for paper-quality output (see `skills/narrative-architect/SKILL.md` — optional academic-figure strategy annotation).

Operators can force the label by annotating the strategy directly in the strategy map: `{"strategy": "academic_figure", "rationale": "Figure 3 from <paper>"}`.

**Content quality matters:** paperbanana's Retriever + Planner agents work from the `source_context` field, which the bridge synthesises from the slide's `methodology_context` (operator pre-annotation), `speaker_notes` (when ≥200 chars), or `body_points + visual_direction` joined into prose. Thin slides (headline-only) produce thinner figures. For best results, the narrative-architect should write substantive `speaker_notes` or `methodology_context` for `academic_figure` slides.

---

## 7. Artefact map (refactor task → artefact)

| Refactor task | Artefact | Status |
|---|---|---|
| 1 | `plugins/jack-tar-deckhand/src/paperbanana_dispatch.py` `is_paperbanana_available()` rewrite | committed `7bb18ac` |
| 2 | `plugins/jack-tar-deckhand/src/paperbanana_dispatch.py` `build_dispatch_payload()` + 2 helpers | committed `31e0ee8` |
| 3 | `plugins/jack-tar-deckhand/src/paperbanana_dispatch.py` `build_manifest_entry()` + `_extract_run_id()` | committed `7b7d7db` |
| 4 | `plugins/jack-tar-deckhand/skills/verify/SKILL.md` Step 2.5 + Step 5 | committed `e3a5da1` |
| 5 | This file + persona doc updates + ADR v1 superseded header | THIS commit |
| 6 | `plugins/jack-tar-deckhand/tests/test_paperbanana_dispatch.py` + `test_verify_skill_paperbanana.py` | pending |
| E6 | `docs/superpowers/dogfooding/2026-05-18-paperbanana-integration.md` | pending |

---

## 8. Risks and trade-offs

| Risk | Mitigation |
|---|---|
| Paperbanana renames the `generate` subcommand or changes CLI flags | All CLI args are constructed in one place (`build_dispatch_payload()`). Version-bump + dispatch update if it ever changes. Pin a paperbanana version in install docs once stable. |
| Paperbanana's MCP transport diverges from the CLI transport | We use CLI for v1.4; MCP is a separate refactor for v1.4.1+. CLI is the documented stable interface. |
| Operators install paperbanana but `GOOGLE_API_KEY` is missing | verify-skill reports PARTIAL with inline guidance to set the key. paperbanana also fails fast with a clear error message at first invocation. |
| Paperbanana licence shifts away from MIT | At Phase 3 start (2026-05-17), paperbanana was MIT. jack-tar does not vendor any paperbanana code (we shell out). A licence change wouldn't affect us until we considered taking a hard dep. |
| Paperbanana's quality regresses on a future release | jack-tar pins by version in install docs. Quality smoke-test (E6 dogfood) re-run on each paperbanana version bump catches regressions. |
| Paperbanana's `--budget` flag doesn't enforce true cost (upstream #213) | jack-tar's own budget accounting in `provider_discovery.py` has correct Flash 1K pricing ($0.067/img) and is the authoritative gate. Paperbanana's `--budget` is belt-and-braces. |
| Cross-plugin coupling discovered late | E6 dogfood is the gate before Phase 3 is declared done. Visual review + manifest correctness + cost verification all checked in one pass. |
| Brand-fidelity slides (`brand_fidelity: "exact"`) need paperbanana but paperbanana has no palette injection | Strategy classifier should refuse to route `brand_fidelity: "exact"` + `academic_figure` combination — either downgrade or surface to speaker. Tracked as a follow-up if dogfood surfaces the combination. |

---

## 9. Related decisions

- [paperbanana-integration.md](paperbanana-integration.md) — v1 ADR, superseded by this file
- [docs/superpowers/plans/2026-05-18-paperbanana-dispatch-refactor.md](../superpowers/plans/2026-05-18-paperbanana-dispatch-refactor.md) — the refactor plan tracking the 6-task execution
- [docs/superpowers/plans/2026-05-17-v1.4-push-and-paperbanana.md](../superpowers/plans/2026-05-17-v1.4-push-and-paperbanana.md) — the v1.4 plan whose Phase 3 this work resets
- Spike report at `~/Documents/Development/paperbanana/tmp/SPIKE_REPORT.md` (operator's local clone; out of repo)
- Issue [#94](https://github.com/SteveGJones/jack-tar-deckhand/issues/94) — this refactor's tracking issue
- Issue [#95](https://github.com/SteveGJones/jack-tar-deckhand/issues/95) — Ralph false-completion defect surfaced by the v1.4 Run 2 that produced the v1 ADR
- Upstream issues [llmsresearch/paperbanana#213](https://github.com/llmsresearch/paperbanana/issues/213), [#214](https://github.com/llmsresearch/paperbanana/issues/214), [#215](https://github.com/llmsresearch/paperbanana/issues/215) — side PRs we filed during this work

---

## 10. References

- paperbanana repo: <https://github.com/llmsresearch/paperbanana>
- paperbanana paper: arXiv:2601.23265 (PaperBanana: Automating Academic Illustration for AI Scientists)
- Claude Code MCP integration: <https://docs.anthropic.com/claude-code/mcp>
- Google Gemini API pricing (May 2026): Flash 1K $0.067/img, Pro 1K $0.134/img
