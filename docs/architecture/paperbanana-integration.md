# Paperbanana Integration — Architecture Decision Record

**Status:** Accepted — shipped in v1.4 (jack-tar-deckhand 1.3.3 → 1.4.0)
**Date:** 2026-05-17
**Plan:** [docs/superpowers/plans/2026-05-17-v1.4-push-and-paperbanana.md](../superpowers/plans/2026-05-17-v1.4-push-and-paperbanana.md) §2.1, §6 Phase 3 (E1–E6)
**Decision-makers:** operator + Ralph (v1.4 push, 2026-05-17)

---

## 1. Context

[paperbanana](https://github.com/SteveGJones/paperbanana) is a sibling Claude Code plugin that renders publication-grade scientific figures — architecture diagrams with formal notation, equations, citations, training curves, ablation studies, attention maps. Its `/generate-diagram` skill consistently outperforms general-purpose image models (Nano Banana Pro / FLUX / Imagen) on these subjects because it composes a typeset pipeline (LaTeX-aware text rendering, vector primitives, paper-template palette) rather than asking a generative model to bake everything from prose.

The jack-tar-deckhand pipeline produces conference talks. A meaningful subset of those talks include "Figure N" slides that quote published results. Today those slides either:

- get classified `composed` and assembled from SmartArt + chart primitives — which works for tabular data but not for ML architecture diagrams or training-curve panels with mathematical notation; or
- get classified `full_render` and routed to Nano Banana Pro — which produces visually plausible but often inaccurate scientific figures (label garbling, fake citations, mis-rendered equations).

paperbanana solves the second case, and is already installed in the operator's environment. The question for v1.4 was **how** to make jack-tar-deckhand route to it without forcing every operator to install paperbanana.

---

## 2. Decision

**Composition approach:** Option 4 (skill cross-invocation) + slim Option 2 (new `academic_figure` strategy in the strategy enum).

Concretely:

1. **Strategy enum gains one value: `academic_figure`.** Strategy-map (`plugins/jack-tar-deckhand/src/schemas/strategy_map.schema.json`) and the rule-based fallback classifier (`plugins/jack-tar-deckhand/src/strategy_classifier.py`) both recognise it. Narrative-architect and smartart-selector personas know when to suggest it (see persona docs, E4).
2. **The imagegen-bridge dispatches cross-plugin via the Claude Code `Skill` tool.** When a slide's strategy is `academic_figure`, the bridge invokes `paperbanana:generate-diagram` directly. There is **no Python import**, **no pip dependency**, and **no shared process** between the two plugins.
3. **Availability is detected at runtime, not at install time.** `paperbanana_dispatch.is_paperbanana_available()` checks `$PAPERBANANA_ROOT` and the standard `~/.claude/plugins/{cache,}/paperbanana/.claude-plugin/plugin.json` locations. When paperbanana is absent, the bridge falls back to a cloud render (Nano Banana Flash 1K, $0.067) with academic-figure-aware prompting — the slide still ships, just not at publication tier.
4. **All cross-plugin glue lives in jack-tar-deckhand.** Paperbanana is unmodified; it ships and updates independently via its own marketplace.

### Rationale

- **Operator-friendly install.** Both plugins are installable independently via Claude Code's marketplace. No second-tier "wrapper plugin" to maintain. Operators who don't need scientific-figure rendering install only jack-tar-deckhand and lose nothing.
- **Loose coupling.** The contract surface is one skill name (`paperbanana:generate-diagram`) plus a fallback path. We can replace, upgrade, or remove the integration without touching the rest of the deckhand pipeline.
- **No pip dependency chain.** A Python-import-based integration would force every jack-tar-deckhand consumer to either install paperbanana's deps or wear a `try: import` smell. Skill cross-invocation routes around this — Claude Code's Skill tool already handles plugin discovery and dispatch.
- **Strategy enum is a clean routing seam.** `academic_figure` slots alongside `full_render`, `background`, `backdrop`, `composed`, etc. The strategy-map step already exists to make per-slide routing decisions; this just adds one more case to that switch. The decision lives in one place (strategy-map output → imagegen-bridge dispatch), not scattered.

### Confidence

**95 / 100** — six artefacts (E1 through E6) shipped, 103/103 deckhand suite green, contract-level integration verified via mocks. End-to-end dogfood deferred to operator with paperbanana installed (E6 fallback path — documented expected outcome, see plan §6.5 E6).

---

## 3. Alternatives considered

| Option | Sketch | Why rejected |
|---|---|---|
| **Option 1 — new wrapper plugin `jack-tar-paperbanana`** | A third plugin sits between deckhand and paperbanana, exposing a deckhand-shaped skill that internally calls paperbanana. | Too much maintenance overhead for the value. Double-install is operator-hostile. Three-plugin chain triples the version-bump churn on every paperbanana minor release. |
| **Option 3 — MCP server integration** | paperbanana runs as a long-lived MCP server; deckhand invokes via the MCP transport. | Cross-process complexity not justified for a skill that runs on demand. Paperbanana's MCP surface targets IDE integration (editor-side diagram authoring), not pipeline routing. Adds a port-binding failure mode no other deckhand path has. |
| **Option 2 (full) — new strategy AND new internal renderer** | Strategy enum gains `academic_figure`, AND deckhand grows a `src/academic_figure_renderer.py` that re-implements paperbanana's logic internally. | Re-implementing a working renderer is waste. Misses the underlying point — paperbanana is the renderer; deckhand is the orchestrator. Keep them in their lanes. |
| **Status quo — no integration** | Operators bake academic figures externally and `manifest_path` them in. | Acceptable for advanced operators, but defeats the point of an orchestrator. No surfacing in the strategy classifier means operators never even learn the option exists. |

The accepted decision is **Option 4 + slim Option 2** — combining the skill cross-invocation transport with the strategy enum routing seam. "Slim" because the strategy classifier only labels; the renderer is paperbanana's, not deckhand's.

---

## 4. Contract surface

The integration surface between the two plugins is **one skill invocation plus one availability check**. That's it.

### 4.1 Skill invocation

```
Skill(
  skill="paperbanana:generate-diagram",
  args=<JSON args from paperbanana_dispatch.build_dispatch().args>
)
```

The args mapping is built by `plugins/jack-tar-deckhand/src/paperbanana_dispatch.py::build_dispatch()`. The exact arg shape is paperbanana's contract, not deckhand's — deckhand passes through the slide's prompt, target output path, and any style metadata, and trusts paperbanana's defaults for everything else.

### 4.2 Availability check

```python
from paperbanana_dispatch import is_paperbanana_available

if is_paperbanana_available(env=os.environ):
    # route through Skill
else:
    # fall back to cloud (Nano Banana Flash 1K)
```

The check is filesystem-only — it does NOT invoke paperbanana. Search order:

1. `$PAPERBANANA_ROOT` env override (operator-supplied dev checkout)
2. `~/.claude/plugins/cache/paperbanana/.claude-plugin/plugin.json`
3. `~/.claude/plugins/paperbanana/.claude-plugin/plugin.json`

### 4.3 Manifest stability

Every academic-figure slide writes an `image-manifest.json` entry shaped like:

```json
{
  "slide_number": 7,
  "source_prompt": "...",
  "provider": "paperbanana",
  "model": "paperbanana:generate-diagram",
  "strategy": "academic_figure",
  "output_path": "...",
  "fallback_reason": null
}
```

When paperbanana was absent and the bridge fell back, `provider` becomes `"google"`, `model` becomes the fallback model (Flash 1K by default), and `fallback_reason` carries a human-readable note. Downstream consumers (production-upgrade-plan, QA checks, the eventual iterate-slide skill #89) read those fields to know which slides got the publication-tier renderer and which got the fallback.

### 4.4 Determinism boundary

**Deckhand does not cache paperbanana output.** Paperbanana owns its own cache strategy; the deckhand cache manager skips slides whose strategy is `academic_figure`. The reason: paperbanana's prompt translation and cache keys are paperbanana's contract, and we don't want a stale deckhand-side cache to mask a paperbanana behaviour change.

---

## 5. Fallback behaviour

When paperbanana is not detected, the bridge takes the cloud-fallback path **silently in pipeline terms but loudly in the manifest and verify-skill output**:

| Surface | Behaviour when paperbanana absent |
|---|---|
| Pipeline | Continues. The slide still gets a figure. |
| Tier | Nano Banana Flash 1K (`gemini-3.1-flash-image-preview`, $0.067/img). |
| Prompt | The same prompt that would have gone to paperbanana, with an academic-figure prefix hint baked in by the bridge. |
| Manifest | `provider: "google"`, `model: "gemini-3.1-flash-image-preview"`, `fallback_reason: "paperbanana not installed; cloud fallback used"`. |
| `/jack-tar-deckhand:verify` | Reports `paperbanana: NOT_AVAILABLE (academic_figure will use Flash 1K fallback)` in the ACADEMIC FIGURE capability row. |
| Operator awareness | The verify skill, the manifest, and the narrative-architect persona doc all surface that this is a fallback, not the intended path. |

This is the "graceful degradation" principle from CLAUDE.md applied to a cross-plugin integration — the pipeline never breaks because of an absent optional dependency; it just down-tiers and tells you.

---

## 6. Operator install guide

To enable paperbanana routing on a developer machine:

### 6.1 Install via Claude Code marketplace

```
/plugin marketplace add SteveGJones/paperbanana
/plugin install paperbanana
```

Paperbanana extracts to `~/.claude/plugins/cache/paperbanana/`. The deckhand availability check finds it automatically — no further configuration needed.

### 6.2 Install via local checkout (development)

```
git clone https://github.com/SteveGJones/paperbanana ~/dev/paperbanana
export PAPERBANANA_ROOT=~/dev/paperbanana
```

The `$PAPERBANANA_ROOT` env var takes precedence over the standard plugin cache lookup. Add the export to your shell profile to persist.

### 6.3 Verify

```
/jack-tar-deckhand:verify
```

Look for the **ACADEMIC FIGURE** capability row:

- `READY` — paperbanana detected. `academic_figure` slides route through `paperbanana:generate-diagram`.
- `FALLBACK` — paperbanana not detected. `academic_figure` slides will use Nano Banana Flash 1K with academic-figure prompting.

### 6.4 When to opt slides into `academic_figure`

The strategy classifier auto-labels when it sees two or more academic signals in the slide content (regression / ablation / attention / method diagram / training curve / loss landscape / Figure N caption / equation / citation). The narrative-architect persona will also suggest the label when the speaker is aiming for paper-quality output (see `agents/narrative-architect.md` — optional academic-figure strategy annotation, E4).

Operators can force the label by annotating the strategy directly in the strategy map: `{"strategy": "academic_figure", "rationale": "Figure 3 from <paper>"}`.

---

## 7. Artefact map (E1–E6)

| Sub-step | Artefact | Status |
|---|---|---|
| **E1** | `plugins/jack-tar-deckhand/src/strategy_classifier.py` + `src/schemas/strategy_map.schema.json` enum entry + tests | done |
| **E2** | `plugins/jack-tar-deckhand/src/paperbanana_dispatch.py` + `skills/imagegen-bridge/SKILL.md` Step 4.6 + 14 dispatch tests | done |
| **E3** | `plugins/jack-tar-deckhand/skills/verify/SKILL.md` Step 2.5 + ACADEMIC FIGURE capability row + 3 verify-skill tests | done |
| **E4** | `plugins/jack-tar-deckhand/skills/narrative-architect/SKILL.md` optional academic-figure annotation + `agents/smartart-selector.md` deferral rule | done |
| **E5** | `docs/architecture/paperbanana-integration.md` (this file) + CLAUDE.md plugin table note | done |
| **E6** | `docs/superpowers/dogfooding/2026-05-17-paperbanana-integration.md` — real end-to-end with paperbanana installed, or a documented fallback log | pending |

**Test coverage:** 103/103 deckhand suite green at E4 end-of-phase (commit `9d14347`). E5 is docs-only — no test surface added.

---

## 8. Risks and trade-offs

| Risk | Mitigation |
|---|---|
| Paperbanana renames or removes its `/generate-diagram` skill | Skill name is centralised in `paperbanana_dispatch.PAPERBANANA_SKILL_NAME`. One-line edit + version bump if it ever changes. |
| Paperbanana's arg contract evolves | `build_dispatch()` owns arg assembly. Contract changes land there + a manifest version bump on the manifest entry. |
| Operators install paperbanana but it's broken / out-of-date | The verify skill reports `READY` based on filesystem presence, not on actual skill invocation. If paperbanana is installed but the skill fails at runtime, the bridge surfaces the Skill-tool error — currently not auto-falling-back. Future work: catch the failure and degrade to Flash 1K with a `fallback_reason: "paperbanana skill failed: <error>"`. |
| Paperbanana licence shifts away from MIT | At Phase 3 start (2026-05-17) paperbanana was MIT. Any code we ported (the dispatch helper does NOT port paperbanana code — it only calls paperbanana's skill) carries an MIT attribution comment. Future ports (e.g. ResumeState in #89) must re-verify MIT before lifting. |
| Cross-plugin coupling discovered late | Deckhand tests mock the Skill invocation; we don't have a CI environment with paperbanana installed. End-to-end dogfood (E6) is the gate for the integration; it ran with the cloud fallback path during v1.4 and is deferred for the publication-tier path until the operator runs it manually. |

---

## 9. Related decisions

- **AI-First BSA methodology — service boundaries.** Paperbanana is an external L1 service (academic-figure render) consumed by deckhand's Image Services L1. The contract is one cross-service interaction; the dependency register entry lives in `.bsa/models/jack-tar-deckhand.json` (to be added when the canonical model is bumped for v1.4).
- **Plugin Architecture EPIC #40** (CLAUDE.md). Each plugin owns its skills and ships independently. This ADR extends that principle to optional cross-plugin routing.
- **Image router tiering** (`docs/superpowers/specs/2026-05-02-cloud-resolution-control-design.md`). The fallback path joins the existing routing matrix at the Flash 1K row — no new tier introduced.

---

## 10. References

- Plan: [docs/superpowers/plans/2026-05-17-v1.4-push-and-paperbanana.md](../superpowers/plans/2026-05-17-v1.4-push-and-paperbanana.md) §6 Phase 3 (E1–E6)
- Research: `/tmp/paperbanana-vs-jack-tar-research.md` (architectural mapping, 2026-05-17)
- Dispatch helper: [`plugins/jack-tar-deckhand/src/paperbanana_dispatch.py`](../../plugins/jack-tar-deckhand/src/paperbanana_dispatch.py)
- Classifier: [`plugins/jack-tar-deckhand/src/strategy_classifier.py`](../../plugins/jack-tar-deckhand/src/strategy_classifier.py)
- Bridge dispatch: [`plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md`](../../plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md) Step 4.6
- Verify detection: [`plugins/jack-tar-deckhand/skills/verify/SKILL.md`](../../plugins/jack-tar-deckhand/skills/verify/SKILL.md) Step 2.5
- Persona docs (E4): [`plugins/jack-tar-deckhand/skills/narrative-architect/SKILL.md`](../../plugins/jack-tar-deckhand/skills/narrative-architect/SKILL.md) + [`plugins/jack-tar-deckhand/agents/smartart-selector.md`](../../plugins/jack-tar-deckhand/agents/smartart-selector.md)
