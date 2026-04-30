# jack-tar-superpower-bridge

Wraps around the `document-skills:pptx` superpower with a narrative pre-brief skill and a post-hoc visual enrichment skill. The bridge never modifies /pptx and never modifies the original .pptx — it consumes /pptx output and produces a new enriched file.

## Prerequisites

- Python 3.10+ with python-pptx, lxml, esprima, jsonschema
- `document-skills:pptx` (external superpower, install via marketplace)

## Optional engine plugins (auto-detected — install for full capability)

- `jack-tar-deckhand` — provides imagegen-bridge skill for AI image generation, and reuses image-reviewer + prompt-engineer agents
- `jack-tar-msft-smartart` — provides editable PowerPoint SmartArt engine + injection
- `jack-tar-ollama` — local image generation (free Ollama drafts)
- `jack-tar-cloud` — cloud image generation (production tier)

Without engine plugins, only the `/bridge-brief` skill works; `/enrich-deck` will surface a clear "no enrichment engines available" error.

## Skills

| Skill | Purpose |
|-------|---------|
| `/bridge-brief` | Phase 1 — collaborative narrative pre-brief; produces `creative-brief.md` |
| `/enrich-deck` | Phase 3 — analyse a /pptx-produced .pptx, propose enrichments, apply selected enrichments, deliver enriched deck + report |
| `/verify` | Plugin readiness check |

## Quick Start

```
/jack-tar-superpower-bridge:verify
/jack-tar-superpower-bridge:bridge-brief "AI agent architectures, 20 min conference talk for developers"
# user invokes /pptx with the brief, gets presentation.pptx + build.js
/jack-tar-superpower-bridge:enrich-deck presentation.pptx
```

## Specs and personas

- Design spec: `docs/superpowers/specs/2026-04-22-superpower-bridge-design.md`
- AI Persona contracts: `docs/architecture/ai-personas/superpower-bridge-personas.md`
- Implementation plan: `docs/superpowers/plans/2026-04-23-superpower-bridge.md`

## Canonical example briefs (dogfood-validated)

When writing a creative brief or extending the Narrative Brief Architect, these dogfood-validated briefs are the working references — pick the closest match to your deck's audience and register:

- **Run 6 — Velvet Ledger M&A acquisition deck** (`output/dogfood-bridge-run-6/creative-brief.md`). **Best reference for board / M&A / fiduciary / investment-committee / monetary-policy registers.** Canonical for institutional gravitas, Investigation-Verdict arc (judicial-audience pattern), warm ivory + ox-blood + antique gold + mauve-grey palette, conditional-approval verdict structure, and the full cycle exercise (Phase A Ollama → Flash → Pro escalation, privacy gate handshake). Validated end-to-end through PowerPoint Mac. Includes EXACT-spelled-labels lists for every text-bearing IMAGE marker (Run 6 Finding #19/#20 pattern).
- **Run 5 — Boardroom Stone strategy deck** (`output/dogfood-bridge-run-5/creative-brief.md`). **Best reference for senior-leadership strategy decks.** Canonical for sub-page SMARTART-FROM-LIST typology + native chart routing + BG-on-pivot + will/won't colour reservation.
- **Run 4 — Redline incident report deck** (`output/dogfood-bridge-run-4/creative-brief.md`). **Best reference for engineering-leadership / data-led / retrospective decks.** Canonical for sub-page IMAGE typology + data-led register.

Dogfood logs: `docs/superpowers/dogfooding/2026-04-{23,25,26,26,27,29}-bridge-dogfood-run-{1..6}.md` — each captures leading practices to entrench and anti-patterns to avoid. Run 6's log includes the full cloud-escalation walkthrough.

## Patterns repeatable for new operators

These are the load-bearing patterns the dogfood series has validated. They live in the agent definitions and SKILL.md files; this list is a quick reference for operators authoring their own briefs.

1. **Investigation-Verdict arc + warm-institutional palette** (Run 6) for board / M&A audiences — judicial register, conditional-approval verdict.
2. **Problem-Solution / Pruning Frame + Boardroom Stone palette** (Run 5) for senior-leadership strategy — diagnose / commit / suppress.
3. **Sub-page IMAGE coaching with explicit inch coordinates** (Run 4) — defaults /pptx away from content-zone-width heroes.
4. **EXACT spelled labels REQUIRED list per text-bearing IMAGE marker** (Run 6 Finding #19/#20) — without this, the reviewer ships misspellings; with it, the reviewer catches them reliably.
5. **SMARTART-FROM-LIST bullets ≤24 chars** (Runs 4/5/6 Finding #13) — fits the bridge's default `process1` layout.
6. **One BG marker per deck on the structural pivot only** (Run 5 leading practice 9) — the surface IS the atmosphere on every other slide.
7. **Build.js BG marker rect ONLY, no addText label** (Run 5 Finding #17) — addText survives enrichment as residual cosmetic.
8. **Native charts for chart-shaped subjects, not IMAGE markers** (Run 5 leading practice 8) — Section C language explicitly redirects.
9. **Brand palette table in Section B with Structural / Primary fill / Surface / Body text rows** (Run 4 Finding #12) — pins the bridge's palette derivation heuristic for SmartArt injection.
10. **Privacy gate handshake at first cloud call under internal tier** (Run 6) — fires once, confirmation persists for run.
