# AI-First Architecture Toolkit - Reference Layer

**Version:** 2.0.0
**Methodology Version:** 1.0.0
**Last Updated:** 2026-02-24

## Overview

This reference layer provides the knowledge foundation for all toolkit agents and skills. It includes cliff notes, templates, schemas, examples, and links to full methodology content.

## Contents

### 📚 Cliff Notes (12 Chapters)
**Location:** `cliff-notes/`

Quick-reference chapter summaries (40-65 lines each) covering:
- **Part I (Chapters 1-3):** Foundation - The "WHAT"
- **Part II (Chapters 4-8):** Core Methodology - Creating the Business "WHAT"
- **Part III (Chapters 9-11):** Operating the "HOW"
- **Part IV (Chapter 12):** Modeling and Managing the "HOW"

**When to use:** Quick navigation, agent context, executive summaries

### 📝 Templates (10 Practitioner Artifacts)
**Location:** `templates/`

Ready-to-use templates for creating methodology artifacts:
1. **AI-Persona-Definition-Template.md** (19-section contractual specification)
2. **AI-Persona-Tier-Selection-Guide.md** (Risk tier calibration)
3. **Measurement-Blueprint-Template.md** (5-tier measurement design)
4. **Data-Product-Definition-Template.md** (Data supply chain artifacts)
5. **sop-schema.md** (SOP artifact structure)
6. **cross-domain-sop-register.md** (SOP borrowing tracker)
7. **readiness-scorecard.md** (8-checkpoint release gate)
8. **delegation-package-checklist.md** (8-item bundle)
9. **backlog-item-template.md** (Realization backlog structure)
10. **vanilla-agent-log.md** (Validation test log)

**When to use:** Creating formal AI Persona definitions, measurement blueprints, governance artifacts

### 🔧 Schemas (2 JSON Schemas)
**Location:** `schemas/`

Machine-readable schemas for validation:
1. **canonical-service-domain-model-schema.json** - Core schema for all architecture models
2. **style-config.json** - Visual rendering specifications for diagrams

**When to use:** Validating canonical models, configuring diagram rendering

### 💡 Examples (3 Worked Examples)
**Location:** `examples/`

Reference patterns showing "what good looks like":
1. **canonical-model-example-oblivion-widgets.json** - Manufacturing company (simple, 1 AI Persona)
2. **canonical-model-example-digital-bank.json** - Digital bank (complex, 4 AI Personas)
3. **canonical-model-example-vmi-programme.json** - Programme-level architecture (2 AI Personas)

**When to use:** Understanding canonical model structure, copying patterns for your domain

### 📖 Glossary
**Location:** `glossary.md`

Quick terminology reference (~150 key terms) with cross-references to defining chapters.

**When to use:** Understanding methodology vocabulary (AI Persona, AI RM, Service Owner, SOP, MCP, etc.)

### 🔗 Chapter Links
**Location:** `CHAPTER-LINKS.md`

Deep links to full chapters in the main methodology repository for detailed study.

**When to use:** Deep methodology work, facilitation guidance, worked examples with rationale

### 📋 Governance Framework
**Location:** `GOVERNANCE-FRAMEWORK.md`

Complete versioning, validation, and release management framework from Grupo Bimbo project.

**When to use:** Understanding toolkit versioning, release cadence, breaking change management

## Quick Start

### For Agents

Agents automatically discover references via `.claude/toolkit-config.json`:

```markdown
## Example: Loading a template

1. Read `.claude/toolkit-config.json` to confirm references location
2. Read `.claude/agents/references/templates/AI-Persona-Definition-Template.md`
3. Guide user through completing the template
```

### For Users

Access references directly:

```bash
# View cliff notes
cat .claude/agents/references/cliff-notes/Chapter-06-Creating-the-Architecture.md

# Copy template for editing
cp .claude/agents/references/templates/AI-Persona-Definition-Template.md \
   docs/architecture/personas/quality-escape-persona.md

# Validate canonical model against schema
python3 -m json.tool docs/architecture/canonical-model.json | \
  jsonschema -i /dev/stdin .claude/agents/references/schemas/canonical-service-domain-model-schema.json
```

## Reference Layer Philosophy

### Bundled vs. Linked

| Content | Strategy | Rationale |
|---------|----------|-----------|
| Cliff notes | **Bundled** | Fast access, frequent use, offline-capable |
| Templates | **Bundled** | Core practitioner tools, frequently used |
| Schemas | **Bundled** | Required for validation workflows |
| Examples | **Bundled** | Reference patterns, frequently consulted |
| Glossary | **Bundled** | Quick lookups during methodology work |
| Full chapters | **Linked** | Large size (~8,500 lines total), less frequent access |
| Appendices | **Linked** | Reference material, accessed as-needed |

### Design Principles

1. **Self-Contained:** References work offline, no network required
2. **Version-Locked:** References match toolkit version (v2.0.0)
3. **Agent-Optimized:** Structured for AI agent consumption (markdown, JSON)
4. **Practitioner-Focused:** Templates and examples for real work
5. **Lightweight:** ~280KB total, fast to copy and distribute

## Usage Patterns

### Pattern 1: Quick Navigation (Cliff Notes)
```
User: "What's the Three Questions framework?"
Agent: Reads cliff-notes/Chapter-06-Creating-the-Architecture.md
Agent: Provides summary with reference to full chapter if needed
```

### Pattern 2: Template Application
```
User: "Create an AI Persona for quality inspection"
Agent: Reads templates/AI-Persona-Definition-Template.md
Agent: Guides user through all 19 sections
```

### Pattern 3: Example Pattern Matching
```
User: "Show me a manufacturing example"
Agent: Reads examples/canonical-model-example-oblivion-widgets.json
Agent: Highlights relevant patterns for user's domain
```

### Pattern 4: Deep Methodology Study
```
User: "I need detailed guidance on service discovery facilitation"
Agent: Reads cliff-notes/Chapter-04-Start-at-the-Top.md (quick overview)
Agent: References CHAPTER-LINKS.md for full chapter path
Agent: Reads {methodology_repo}/methodology_draft/chapters/Chapter-04-Start-at-the-Top.md
```

## Version Compatibility

This reference layer (v2.0.0) is compatible with:
- **Toolkit:** v2.0.0 - v2.9.9
- **Methodology:** v1.0.0
- **Claude Code:** v1.0.0+

## Updates & Maintenance

**Quarterly Sync:** Reference layer syncs with methodology repository every quarter to ensure currency.

**Version Governance:** Managed via `GOVERNANCE-FRAMEWORK.md` with approval process for changes.

**Breaking Changes:** MAJOR version bump (v3.0.0) if schemas change incompatibly or chapters restructure significantly.

## Questions?

- **Toolkit usage:** See main toolkit `docs/AGENT-GUIDE.md` and `docs/SKILL-GUIDE.md`
- **Methodology questions:** See `CHAPTER-LINKS.md` for full chapter references
- **Missing content:** Contact methodology team (see `GOVERNANCE-FRAMEWORK.md` for roles)

---

**Complete Contents Inventory:**
- ✅ 12 cliff notes (Chapters 1-12)
- ✅ 10 practitioner templates
- ✅ 2 JSON schemas
- ✅ 3 worked examples
- ✅ Glossary (~150 terms)
- ✅ Chapter links (deep links to full methodology)
- ✅ Governance framework

**Total Size:** ~280KB
**Offline Capable:** Yes
**Agent Accessible:** Yes
**User Accessible:** Yes
