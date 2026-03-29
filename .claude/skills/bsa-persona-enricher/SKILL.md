---
name: bsa-persona-enricher
description: Takes a basic AI Persona stub from a canonical model and enriches it into the full 19-section AI Persona Definition Template. Bridges the gap between discovery-phase persona candidates and fully specified personas.
---

# BSA Persona Enricher

This skill bridges the gap between the lightweight AI Persona stubs captured during service discovery (in canonical models) and the comprehensive 19-section AI Persona Definition Template required for governance and deployment. It reads persona data from a canonical model, pre-populates the template with known information, and guides completion of the remaining sections.

## When to Use

- After service discovery has identified AI Persona candidates in a canonical model
- When a canonical model has `aiPersonas` entries that need full governance definitions
- When batch-defining multiple personas across a domain or company
- To ensure consistency between the canonical model and persona definition documents
- As a bridge between `canonical-model-manager` and `ai-persona-definition` skills

## Instructions

### 1. Read the Canonical Model

Load the canonical model JSON and extract all AI Persona entries:

```
docs/architecture/bsa/canonical-models/[company].json
```

For each entry in `aiPersonas`, gather:
- Persona `id` and `serviceId`
- The owning service's `name`, `mission`, `owner`, `level`, `parentId`
- The `authorityModel`, `confidenceThresholds`, `riskClassification`
- The `sops` array (SOP IDs, names, MCP servers)
- All interactions where the persona's service is `sourceId` or `targetId`
- All actors associated with the persona's service

### 2. Pre-Populate the 19-Section Template

Map canonical model data to template sections:

| Template Section | Source in Canonical Model |
|-----------------|-------------------------|
| 1. AI Persona Identification | `aiPersonas.id`, service `name`, `version` from modelMetadata |
| 2. Governance and Ownership | Service `owner`, parent domain owner, AI RM from support services |
| 3. Three-Question Discovery | **Requires manual input** — prompt user |
| 4. Intent and Mandate | Service `mission`, `tags` |
| 5. Capabilities (Permitted Actions) | `sops` array mapped to capability table |
| 6. Data Contract | **Requires manual input** — infer from system actors and data_flow interactions |
| 7. Scope & Ways of Working | **Requires manual input** — infer from `tags` and domain context |
| 8. Authority Model | `authorityModel`, `confidenceThresholds` |
| 9. Interacting Services and Actors | Interactions and actor associations from model |
| 10. Performance Measurement | **Requires manual input** — use `measurement-blueprint` skill |
| 11. Multi-Contributor KPI Attribution | **Requires manual input** |
| 12. Lifecycle Management | **Requires manual input** — suggest defaults by risk tier |
| 13. Regulatory and Compliance | Infer from `tags` (e.g., `AS9100`, `FAA-Part-21`) |
| 14. Risk Management | `riskClassification` maps to governance depth |
| 15. Trusted AI (Scope) Framework | Derive from capabilities (what it CAN do implies boundary) |
| 16. Collaborative Data Supply Chain | Data flow interactions from model |
| 17. Worked Example | **Optional** — suggest scenario from demo scenarios |
| 18. Approval and Sign-Off | Service `owner` + AI RM placeholder |
| 19. Supporting Documentation | Link to canonical model, diagrams, SOP specs |

### 3. Generate the Enriched Document

Produce a markdown document for each persona:

```markdown
# AI Persona Definition: [Persona Name]

> Auto-populated from canonical model `[model-id]` v[version] on [date].
> Sections marked [AUTO] were populated from the model. Sections marked [MANUAL] require human input.

## Section 1: AI Persona Identification [AUTO]

| Field | Value |
|-------|-------|
| Persona Name | [from service name] |
| Persona ID | [from aiPersonas.id] |
| Version | 1.0.0 |
| Owning Service | [service name] ([service id]) |
| Parent Domain | [parent service name] |
| Status | Draft |

## Section 2: Governance and Ownership [AUTO]

| Role | Name |
|------|------|
| Business Owner | [service owner] |
| Domain Owner | [parent service owner] |
| AI RM Liaison | [from AI RM service, if found] |

[... continue for all 19 sections ...]

## Section 3: Three-Question Discovery Results [MANUAL]

**Q1 — What exactly are we delegating?**
> [NEEDS INPUT: Provide a specific, bounded, measurable delegation statement]

**Q2 — How will we manage this delegation?**
> [NEEDS INPUT: Concrete oversight mechanisms, review cadences, alert thresholds]

**Q3 — How will we include this AI in the team?**
> [NEEDS INPUT: Operational rhythm, human touchpoints, team integration]
```

### 4. Batch Mode

When enriching multiple personas from a single model:

1. Extract all `aiPersonas` entries
2. Generate a summary table:

```markdown
# Persona Enrichment Batch: [Model Name]

| # | Persona ID | Service | Authority | Risk Tier | Auto-Fill % | Manual Sections |
|---|-----------|---------|-----------|-----------|-------------|-----------------|
| 1 | ap-quality | Quality AI | hybrid | tier-2 | 55% | 3, 6, 7, 10, 11, 12 |
| 2 | ap-demand | Demand Forecast | autonomous | tier-1 | 50% | 3, 6, 7, 10, 11, 12 |
```

3. Generate individual documents for each persona
4. Track completion status across the batch

### 5. Write-Back to Canonical Model

After enrichment, update the canonical model with any new information discovered:

- New SOPs identified during capability analysis → add to `aiPersonas[].sops`
- New interactions identified → add to `interactions`
- New actors identified → add to `humanActors` or `systemActors`
- Updated risk classification → update `riskClassification`

Use `canonical-model-manager` patterns for the write-back, and run `canonical-model-validator` after.

### 6. Output Location

Write enriched persona definitions alongside existing per-company persona docs:
`docs/architecture/bsa/[company-name]/personas/`

This matches the existing structure on disk where each company already has a `personas/` directory (e.g., `docs/architecture/bsa/aerovista/personas/`) containing persona markdown files.

Use filenames matching existing convention: `[persona-slug].md` (kebab-case derived from persona name, e.g., `quality-ai.md`, `demand-forecast-ai.md`)

For batch summary: `docs/architecture/bsa/[company-name]/personas/_enrichment-summary.md`

### 7. Completion Criteria

A persona is considered fully enriched when:
- [ ] All 19 sections have content (no `[NEEDS INPUT]` placeholders remaining)
- [ ] Three Questions have STRONG answers (specific, bounded, measurable)
- [ ] Capability table is exhaustive (includes CAN and CANNOT)
- [ ] Data contract specifies exact fields, not just system names
- [ ] Authority model thresholds are numeric and justified
- [ ] At least one interaction per persona in the canonical model
- [ ] Risk tier matches the governance depth applied

## Relationship to Other Skills

- **Upstream**: `canonical-model-manager` (provides persona stubs), `service-discovery-facilitator` agent (identifies candidates)
- **Wraps**: `ai-persona-definition` (this skill pre-populates the same 19-section template)
- **Downstream**: `readiness-scorecard` (requires complete persona definitions), `measurement-blueprint` (sections 10-11)
- **Write-back**: `canonical-model-validator` (validates after write-back)

## Output

One markdown file per AI Persona containing the 19-section definition template pre-populated from the canonical model, with clear markers for sections requiring manual input. Optionally, a batch summary showing enrichment status across all personas in the model.
