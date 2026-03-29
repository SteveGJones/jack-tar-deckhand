# CLAUDE.md

All rules are in **CONSTITUTION.md**. Core instructions are in **CLAUDE-CORE.md**.

## Project: Jack-Tar Deckhand

Claude Code skills and agents for conference-quality PowerPoint presentations. This is NOT a standalone app — it runs inside Claude Code.

### Current Status (2026-03-29)

- **BSA Architecture:** Complete, user reviewed
  - Canonical model: `.bsa/models/jack-tar-deckhand.json`
  - Documentation: `docs/architecture/` (6 docs + 7 SVG diagrams)

- **Research Library:** Complete — 18 papers, ~105K words in `research/`
  - Start with `research/RESEARCH-INDEX.md` for fast lookup
  - Create `research/synthesis-[skill-name].md` before implementing any skill

- **Implementation Plans:** `docs/superpowers/plans/` (7 plans)
  - Phase 1: Foundation — COMPLETE (38 tests)
  - Phase 2: Design Services (slide-stylist) — planned, not started
  - Phase 3: Content Services (narrative-architect, speaker-notes-writer) — planned, not started
  - Phase 4A: Image Utilities — COMPLETE (98 tests, 136 total)
  - Phase 4B: Cloud Generation (cloud-generate-image, cloud-generate-icon) — planned, NEXT
  - Phase 4C: Routing & Advisory (imagegen-bridge, image-generation-expert) — planned
  - Phase 5: Assembly & QA — planned
  - Phase 6: Orchestration (deck-conductor) — planned

- **Existing ollama-* skills are upstream — do NOT fork or modify them.** The imagegen-bridge handles all DeckContext integration.

### Implementation Status

| Module | Location | Tests | Status |
|--------|----------|-------|--------|
| DeckContext management | `src/deckcontext.py` | 10 | Done |
| JSON Schemas (8 contracts) | `src/schemas/` | 27 | Done |
| Image processing | `src/process_image.py` | 19 | Done |
| Provider discovery | `src/provider_discovery.py` | 12 | Done |
| Budget tracker | `src/budget_tracker.py` | 17 | Done |
| Chart renderer | `src/render_chart.py` | 15 | Done |
| Cache manager | `src/cache_manager.py` | 15 | Done |
| Prompt translator | `src/prompt_translator.py` | 20 | Done |
| Integration test | `tests/test_integration.py` | 1 | Done |

### Architecture Summary

- **Approach B (Domain-Centric):** Services designed for reuse beyond deck production
- **4 L1 Services:** Content, Design, Image, Assembly & QA
- **3 AI Personas:** Deck Conductor (orchestrator), Image Generation Expert (advisory), Presentation Reviewer (advisory)
- **17 Deliverables:** 14 skills + 3 agents
- **Naming Convention:** Provider prefix — `ollama-*` for local, `cloud-*` for cloud image skills

### Key Files

| File | Purpose |
|------|---------|
| `.bsa/models/jack-tar-deckhand.json` | Canonical model (single source of truth) |
| `docs/architecture/architecture-overview.md` | One-page architecture summary |
| `docs/architecture/ai-persona-summaries.md` | 3 agent contracts |
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

