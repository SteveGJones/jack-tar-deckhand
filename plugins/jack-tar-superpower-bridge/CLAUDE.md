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
