---
name: canonical-model-validator
description: Validates canonical model JSON files against the schema, checks referential integrity (actor refs, SOP refs, interaction endpoints), and reports errors/warnings. Works with the existing canonical-model-manager skill.
---

# Canonical Model Validator

This skill validates a canonical service domain model JSON file for structural correctness and referential integrity. It catches broken references, orphaned entities, methodology violations, and schema mismatches before they propagate to diagrams, documentation, or governance reviews.

## When to Use

- After creating or modifying a canonical model with `canonical-model-manager`
- Before rendering diagrams with `service-architecture-renderer`
- Before running `methodology-compliance-check` to ensure the model itself is sound
- As part of a CI/quality gate before merging architecture changes
- When importing or merging models from different sessions or authors

## Instructions

### 1. Locate the Model

Canonical models for this project live at:
`docs/architecture/bsa/canonical-models/*.json`

The collaborative (multi-company) model is:
`docs/architecture/bsa/canonical-models/acid-collaborative.json`

The schema is at:
`.claude/agents/references/schemas/canonical-service-domain-model-schema.json`

### 2. Structural Validation (Errors)

Check the following. Any failure here is an **error** (model is invalid):

#### Model Metadata
- [ ] `modelMetadata` exists with all required fields: `id`, `name`, `version`, `organisation`, `createdDate`
- [ ] `version` follows semver format (e.g., `1.0.0`)
- [ ] `status` is one of: `draft`, `review`, `approved`, `deprecated`

#### Services
- [ ] Every service has `id`, `name`, `level`, `mission`, `serviceType`
- [ ] `serviceType` is `core` or `support`
- [ ] `level` is a non-negative integer
- [ ] Level 1+ services have a `parentId` that references an existing service
- [ ] No circular `parentId` references
- [ ] No duplicate service `id` values
- [ ] Every `parentId` points to a service that exists

#### AI Personas
- [ ] Every entry in `aiPersonas` has `id`, `serviceId`
- [ ] Every `serviceId` references a service that exists and has `isAIPersona: true`
- [ ] Every service with `isAIPersona: true` has a matching `aiPersonas` entry
- [ ] `authorityModel` is one of: `autonomous`, `hybrid`, `supervised`
- [ ] If `authorityModel` is `hybrid`, `confidenceThresholds` is present with `autonomous` and `escalate` values
- [ ] Each SOP in `sops` array has `sopId` and `name`

#### Human Actors
- [ ] Every human actor has `id`, `name`, `isExternal`
- [ ] Every `serviceId` in `serviceAssociations` references an existing service
- [ ] `associationType` is one of: `owner`, `consumer`, `provider`, `data_source`, `escalation_target`, `integration_target`

#### System Actors
- [ ] Every system actor has `id`, `name`
- [ ] Every `serviceId` in `serviceAssociations` references an existing service

#### Interactions
- [ ] Every interaction has `id`, `sourceId`, `targetId`, `label`, `interactionType`
- [ ] `sourceId` references an existing entity (service, actor, or AI persona service)
- [ ] `targetId` references an existing entity
- [ ] `interactionType` is one of: `capability_invocation`, `data_flow`, `escalation`, `support`, `external`, `approval`
- [ ] No duplicate interaction `id` values

#### External Interactions
- [ ] Every external interaction has `id`, `internalServiceId`, `externalServiceName`
- [ ] `internalServiceId` references an existing service

### 3. Referential Integrity (Errors)

Build an index of all entity IDs across the model, then verify:

- [ ] **No dangling references**: Every `sourceId`, `targetId`, `serviceId`, `parentId` points to an entity that exists in the model
- [ ] **No orphaned AI Personas**: Every `aiPersonas` entry has a corresponding service with `isAIPersona: true`
- [ ] **No orphaned actors**: Every actor has at least one `serviceAssociation` pointing to a valid service
- [ ] **Bidirectional consistency**: If an interaction references a service, that service should logically participate in the interaction (warning, not error)

### 4. Methodology Compliance (Warnings)

These are warnings (model is valid but may not conform to methodology best practice):

- [ ] Level 0 has 4-8 services
- [ ] Each Level 1 domain has 5-9 sub-services
- [ ] AI RM appears as a shared/support service (if any AI Personas exist)
- [ ] Every AI Persona has at least one SOP defined
- [ ] Every service has an `owner` field populated
- [ ] No services without any interactions (fully disconnected)
- [ ] No actors associated only with services they don't interact with

### 5. ID Convention Checks (Warnings)

Verify IDs follow the established naming convention:

| Entity | Expected Pattern | Example |
|--------|-----------------|---------|
| Services | `svc-*` or short abbreviation | `svc-quality`, `mfg`, `av-core-ops` |
| AI Personas | `ap-*` | `ap-quality`, `ap-demand` |
| Human actors | `ha-*` | `ha-plant-mgr` |
| System actors | `sa-*` | `sa-erp`, `sa-scada` |
| Interactions | `int-*` | `int-001`, `int-av-st-001` |
| External interactions | `ext-*` | `ext-001` |

### 6. Report Format

Produce a structured validation report:

```markdown
# Canonical Model Validation Report

**Model:** [model name]
**File:** [file path]
**Version:** [version]
**Validated:** [date]
**Result:** [PASS / PASS WITH WARNINGS / FAIL]

## Summary
- Errors: [count]
- Warnings: [count]
- Entities validated: [count] services, [count] personas, [count] actors, [count] interactions

## Errors (Must Fix)
| # | Category | Entity | Issue |
|---|----------|--------|-------|
| 1 | Referential Integrity | int-042 | targetId "svc-missing" not found |

## Warnings (Should Fix)
| # | Category | Entity | Issue |
|---|----------|--------|-------|
| 1 | Methodology | L0 | Only 3 services at Level 0 (expected 4-8) |

## Entity Index
[Summary table of all entities by type and count]
```

## AI Persona Consistency Checks

AI Personas have dual representation in the canonical model: a service entry (in `services[]`) with `isAIPersona: true`, and a matching delegation contract (in `aiPersonas[]`). Both must exist and stay in sync. The checks below ensure practitioners never end up with a half-defined persona that silently breaks diagrams, governance reports, or compliance checks.

### V-PERSONA-001: Bidirectional Consistency (ERROR)

Every AI Persona must be fully represented on both sides of the model. Check two directions:

1. **Service to contract.** For every service where `isAIPersona` is `true`, there must be an entry in `aiPersonas[]` whose `serviceId` equals that service's `id`. If missing:
   > "The '{service.name}' service is marked as an AI Persona but has no delegation contract. Use /ai-persona-definition to complete it."

2. **Contract to service.** For every entry in `aiPersonas[]`, the referenced `serviceId` must point to a service that exists in `services[]` and has `isAIPersona: true`. If the service is missing entirely:
   > "AI Persona '{aiPersona.id}' references service '{aiPersona.serviceId}', but that service does not exist. Use /canonical-model-manager to create the service entry."

   If the service exists but `isAIPersona` is not `true`:
   > "AI Persona '{aiPersona.id}' references service '{service.name}', but that service is not flagged as an AI Persona. Set isAIPersona: true on the service or remove the aiPersonas entry."

### V-PERSONA-002: Minimum Contract Completeness (WARNING)

A delegation contract without an authority model is incomplete. For every entry in `aiPersonas[]`, check that `authorityModel` is defined and is one of `autonomous`, `hybrid`, or `supervised`. If missing or empty:
> "AI Persona '{aiPersona.id}' has no authority model. Specify autonomous, hybrid, or supervised."

This is a warning rather than an error because the model is structurally valid without it, but no governance review or risk classification can proceed until the authority model is set.

### V-PERSONA-003: ID Convention (ADVISORY)

AI Persona IDs should follow the `ap-` prefix convention to distinguish them from service IDs at a glance. For every entry in `aiPersonas[]` whose `id` does not start with `ap-`:
> "AI Persona '{aiPersona.id}' does not follow the 'ap-' prefix convention. Consider renaming to 'ap-{suggested}' for consistency with the model's naming standards."

Where `{suggested}` is derived from the current ID by stripping any existing prefix and prepending `ap-`.

## Relationship to Other Skills

- **Upstream**: `canonical-model-manager` (creates/edits the models this skill validates)
- **Downstream**: `service-architecture-renderer` (validated models produce clean diagrams), `methodology-compliance-check` (validated models produce accurate compliance reports)
- **Cross-model**: `cross-model-validator` handles multi-model consistency; this skill validates a single model in isolation

## Output

A validation report with PASS/FAIL result, categorised errors and warnings, and an entity summary. The model is considered valid if there are zero errors.
