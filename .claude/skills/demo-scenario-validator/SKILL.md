---
name: demo-scenario-validator
description: Validates that demo scenarios have complete end-to-end paths through BSA artifacts — every persona has a definition, every SOP has a YAML, every interaction is reciprocal, every dependency is tracked.
---

# Demo Scenario Validator

This skill validates that a demo scenario can run end-to-end by checking completeness across all BSA artifacts. It traces the scenario entity chain from PHASE-1-SCOPE.md and verifies that every entity referenced actually exists and is sufficiently defined.

## When to Use

- Before demo rehearsals to confirm all artifacts are in place
- After persona enrichment (WP-3) to verify completeness
- After SOP generation (WP-4) to verify MCP readiness
- As a quality gate before transitioning from architecture to implementation
- When adding a new demo scenario to verify it has full BSA coverage

## Instructions

### 1. Load the Scope Document

Read the phase scope document:
`docs/architecture/bsa/PHASE-1-SCOPE.md`

Extract the scenario entity maps — these define the step-by-step chains that must work.

### 2. Load All Referenced Artifacts

For each entity in the scope document, check that the following artifacts exist:

| Entity Type | Required Artifact | Location |
|------------|-------------------|----------|
| AI Persona | 19-section persona definition | `docs/architecture/bsa/[company]/personas/[persona-slug].md` |
| AI Persona | Entry in canonical model | `docs/architecture/bsa/canonical-models/[company].json` |
| SOP (MCP-exposed) | YAML definition | `docs/architecture/bsa/sop-definitions/[sop-id].yaml` |
| SOP (internal) | At minimum, SOP stub in persona definition | Canonical model `aiPersonas[].sops` |
| Interaction | Entry in canonical model | Canonical model `interactions[]` |
| Cross-company interaction | Reciprocal entries in both models | Both company models + collaborative model |
| Human Actor | Entry in canonical model | Canonical model `humanActors[]` |
| System Actor | Entry in canonical model | Canonical model `systemActors[]` |

### 3. Validate Each Scenario

For each demo scenario, trace every step in the entity chain and check:

#### Step-Level Checks

- [ ] **Actor/Persona exists**: The entity performing the action exists in the canonical model
- [ ] **Persona is defined**: AI Personas have at minimum a canonical model entry with authority model, SOPs, and risk classification
- [ ] **Persona is enriched**: AI Personas have a 19-section definition document (check file exists)
- [ ] **SOP is defined**: Every SOP invoked has a YAML definition file
- [ ] **Authority is consistent**: The authority level claimed in the scenario matches the persona's authority model
- [ ] **Cross-company path works**: When an agent deploys to another company, both the source and destination have matching interaction entries

#### Scenario-Level Checks

- [ ] **Complete chain**: Every step has a next step (no dead ends unless the step is a terminal action)
- [ ] **All authority levels demonstrated**: The scenario exercises the authority levels it claims
- [ ] **Human approvals identified**: Every human approval point has a named actor
- [ ] **Escalation paths defined**: Every escalation in the chain has a defined escalation target
- [ ] **Timing feasible**: For time-critical scenarios (AOG: < 30 minutes), the chain doesn't include steps that would block

### 4. Check Completeness Scores

For each entity type, calculate a completeness percentage:

```markdown
### Scenario: Quality Escape

| Entity Type | Total Required | Exists | Defined | Enriched | % Complete |
|------------|---------------|--------|---------|----------|------------|
| AI Personas | 7 | 7 | 7 | 3 | 43% |
| MCP SOPs | 4 | 4 | 2 | — | 50% |
| Internal SOPs | 8 | 8 | 0 | — | 0% |
| Interactions | 5 | 5 | 5 | — | 100% |
| Human Actors | 2 | 2 | 2 | — | 100% |
```

### 5. Produce Validation Report

```markdown
# Demo Scenario Validation Report

**Date:** [date]
**Phase:** [phase number]
**Overall Result:** [READY / NOT READY / PARTIALLY READY]

## Summary

| Scenario | Personas | SOPs | Interactions | Actors | Overall |
|----------|----------|------|-------------|--------|---------|
| Quality Escape | 43% | 50% | 100% | 100% | NOT READY |
| AOG Emergency | 60% | 40% | 100% | 100% | NOT READY |
| Schedule Slip | 50% | 30% | 100% | 100% | NOT READY |

## Blocking Issues

| # | Scenario | Entity | Issue | Remediation |
|---|----------|--------|-------|-------------|
| 1 | Quality Escape | ap-st-blade-inspection-ai | No 19-section definition | Run bsa-persona-enricher |
| 2 | AOG Emergency | sop-st-inv-check-atp | No YAML definition | Run sop-definition-generator |

## Non-Blocking Issues

[Warnings that don't prevent the scenario from running but should be addressed]

## Recommendations

[Prioritised list of actions to reach READY status]
```

### 6. Readiness Gates

Define readiness levels:

| Level | Criteria | Meaning |
|-------|----------|---------|
| **READY** | All entities exist, defined, and enriched. All SOPs have YAML. All interactions reciprocal. | Demo can run end-to-end |
| **PARTIALLY READY** | All entities exist in canonical model. Some personas not enriched. Some SOPs missing YAML. | Architecture is sound but needs depth |
| **NOT READY** | Missing entities in canonical model. Broken interaction chains. | Cannot trace scenario end-to-end |

## Output Location

Write validation reports to:
`docs/architecture/bsa/generated/scenario-validation-[date].md`

## Relationship to Other Skills

- **Upstream**: `phase-scope-extractor` (defines what to validate), `bsa-persona-enricher` (enriches personas), `sop-definition-generator` (creates SOP YAMLs)
- **Parallel**: `readiness-scorecard` (validates individual personas), `cross-model-validator` (validates cross-model consistency)
- **Downstream**: Implementation work packages, demo rehearsal planning

## Output

A scenario validation report showing completeness percentages per entity type, blocking issues that prevent end-to-end scenario execution, and a prioritised remediation plan to reach READY status.
