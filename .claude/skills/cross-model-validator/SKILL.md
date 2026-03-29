---
name: cross-model-validator
description: Validates consistency ACROSS multiple canonical models — checks that cross-company interactions reference valid endpoints on both sides, shared reference data alignment, agent authority level consistency between home and host nodes.
---

# Cross-Model Validator

This skill validates consistency across multiple canonical service domain models. While `canonical-model-validator` checks a single model in isolation, this skill detects mismatches between models — broken cross-company interactions, inconsistent authority levels, misaligned reference data, and missing reciprocal endpoints.

## When to Use

- After creating or updating models for multiple companies in the ACID supply chain
- Before generating the collaborative network view (`acid-collaborative.json`)
- When adding a new company to the supply chain and connecting it to existing models
- When cross-company interactions are modified in any model
- As part of the `bsa-pipeline-orchestrator` pipeline

## Instructions

### 1. Load All Models

Load all canonical models from:
`docs/architecture/bsa/canonical-models/*.json`

Build a master index of:
- All services across all models (keyed by model + service ID)
- All AI Personas across all models
- All external interactions across all models
- All SOPs across all models

### 2. Cross-Company Interaction Validation (Errors)

For every `externalInteraction` in each model:

- [ ] **Reciprocal endpoint exists**: If Model A declares an external interaction with "SpinnyThings", Model B (SpinnyThings) must have a corresponding service or external interaction that references Model A's entity
- [ ] **Service name alignment**: The `externalServiceName` in Model A matches an actual service `name` in the target model
- [ ] **Domain alignment**: The `externalDomain` matches the target model's `modelMetadata.organisation`

For cross-company interactions in the collaborative model (`acid-collaborative.json`):

- [ ] **Source exists in source company model**: The `sourceId` maps to a real service in the source company's individual model
- [ ] **Target exists in target company model**: The `targetId` maps to a real service in the target company's individual model

### 3. Agent Authority Consistency (Errors)

When an AI Persona from Company A operates in Company B's node:

- [ ] **Authority model declared in both models**: The persona's authority level in the home model matches or is compatible with the authority level granted in the host model
- [ ] **Host authority <= Home authority**: A persona should never have MORE authority at a host node than at its home node
- [ ] **SOP access alignment**: SOPs the persona expects to invoke at the host node are actually exposed by the host node's model

### 4. Reference Data Alignment (Warnings)

Check shared reference data consistency:

- [ ] **Material codes**: Material identifiers used in one model map to recognised references in others (e.g., Ti-6Al-4V / AMS 4911 / R56400 consistency)
- [ ] **Quality standards**: AS9100, NADCAP, FAA references are consistent across models
- [ ] **Company identifiers**: Company IDs used in interactions match across all models
- [ ] **SOP naming**: SOPs referenced in cross-company interactions use consistent naming

### 5. Collaborative Model Reconciliation

Validate the collaborative model (`acid-collaborative.json`) against individual company models:

- [ ] **Every company model has a corresponding L0 service** in the collaborative model
- [ ] **L1 services in collaborative model** align with L0 services in individual company models
- [ ] **Cross-company interactions in collaborative model** are consistent with external interactions in individual models
- [ ] **AI Persona deployments** shown in collaborative model match persona definitions in individual models
- [ ] **No orphaned companies**: Every company in the collaborative model has an individual model file

### 6. SOP Cross-Reference (Warnings)

For SOPs that appear in multiple models (e.g., a persona in Model A invokes SOPs exposed by Model B):

- [ ] **SOP IDs match**: Same SOP ID used in both models
- [ ] **SOP names match**: Same human-readable name
- [ ] **MCP server alignment**: The MCP server name in the invoking model matches the server name in the hosting model
- [ ] **No SOP ownership conflicts**: Each SOP has exactly one owning domain (One Server, One Owner doctrine)

### 7. Supply Chain Topology Validation (Warnings)

- [ ] **No circular supply chains**: Company A supplies B supplies C does not loop back to A
- [ ] **Tier consistency**: If A is Tier 0 and B is Tier 1, interactions flow appropriately (OEM doesn't supply to itself)
- [ ] **Complete paths**: Every material flow has both source and destination
- [ ] **Demo scenario coverage**: The three demo scenarios (Quality Escape, AOG, Schedule Slip) have supporting interactions in the relevant models

### 8. Report Format

```markdown
# Cross-Model Validation Report

**Models Validated:** [count]
**Models:** [list of model files]
**Validated:** [date]
**Result:** [PASS / PASS WITH WARNINGS / FAIL]

## Summary
- Cross-model errors: [count]
- Cross-model warnings: [count]
- Models with issues: [list]

## Cross-Company Interaction Errors
| # | Source Model | Target Model | Interaction | Issue |
|---|------------|-------------|-------------|-------|
| 1 | aerovista | spinnythings | ext-003 | No reciprocal endpoint for "Engine Assembly Status" |

## Authority Consistency Errors
| # | Persona | Home Model | Host Model | Issue |
|---|---------|-----------|-----------|-------|
| 1 | ap-quality-agent | aerovista | spinnythings | Authority L3 at home but L1 at host (acceptable) |

## Reference Data Warnings
| # | Data Type | Model A Value | Model B Value | Issue |
|---|-----------|--------------|--------------|-------|
| 1 | Material Code | Ti-64 | R56400 | Different identifier for same material |

## Collaborative Model Reconciliation
| # | Issue Type | Details |
|---|-----------|---------|
| 1 | Missing company model | PowerCell appears in collaborative but has no individual model |

## Cross-Model Entity Index
| Model | Services | Personas | External Interactions | SOPs |
|-------|----------|----------|----------------------|------|
| aerovista | 12 | 3 | 5 | 8 |
| spinnythings | 10 | 2 | 4 | 6 |
| acid-collaborative | 11 | 0 | 0 | 0 |
```

## Relationship to Other Skills

- **Upstream**: `canonical-model-validator` (each model should pass individual validation first)
- **Parallel**: `bsa-cross-reference-index` (builds navigable index; this skill validates correctness)
- **Downstream**: `bsa-pipeline-orchestrator` (includes this in the pipeline), `methodology-compliance-check` (cross-model issues affect compliance)

## Output

A cross-model validation report identifying mismatches between canonical models, with categorised errors (must fix) and warnings (should fix), and a reconciliation check against the collaborative model.
