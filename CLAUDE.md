# CLAUDE.md

All rules are in **CONSTITUTION.md**. Core instructions are in **CLAUDE-CORE.md**.

## Project: Jack-Tar Deckhand

Claude Code skills and agents for conference-quality PowerPoint presentations. This is NOT a standalone app — it runs inside Claude Code.

### Current Status (2026-03-29)

- **BSA Architecture:** Complete, user reviewed
  - Canonical model: `.bsa/models/jack-tar-deckhand.json`
  - Design spec: `docs/superpowers/specs/2026-03-29-bsa-architecture-design.md`
  - Documentation: `docs/architecture/` (6 docs + 7 SVG diagrams)
  - **Next step:** Invoke writing-plans skill for implementation plan

- **Research Library:** Complete — 18 papers, ~105K words in `research/`
  - Start with `research/RESEARCH-INDEX.md` for fast lookup
  - Create `research/synthesis-[skill-name].md` before implementing any skill

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

