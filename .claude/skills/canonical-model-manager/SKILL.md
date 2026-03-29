---
name: canonical-model-manager
description: Creates, validates, and incrementally updates the canonical service domain model JSON. Use this when the user needs to build or modify the machine-readable architecture model that captures all services, AI Personas, actors, interactions, and governance data.
---

# Canonical Model Manager

This skill manages the canonical service domain model — the single machine-readable source of truth for all services, AI Personas, actors, interactions, processes, governance, and measurements in the architecture. It supports both single-company models and the multi-company collaborative model format.

## When to Use

- After Level 0 or Level 1 service discovery to capture results as structured JSON
- When adding AI Personas, actors, or interactions to an existing model
- When validating a model against the schema before rendering diagrams
- When merging discovery outputs from multiple workshop sessions
- When updating the collaborative network model (`acid-collaborative.json`) with cross-company data
- When performing targeted incremental updates (add-service, add-persona, add-interaction)

## Schema Reference

The canonical model must conform to the JSON schema at:
`.claude/agents/references/schemas/canonical-service-domain-model-schema.json`

Example models from the methodology:
- `design/canonical-model-example-oblivion-widgets.json` — Manufacturing company (simple)
- `design/canonical-model-example-digital-bank.json` — Digital bank (complex, 4 AI Personas)
- `design/canonical-model-example-vmi-programme.json` — VMI programme (7 services, 2 AI Personas)

ACID project models at:
`docs/architecture/bsa/canonical-models/*.json`

## Instructions

### 1. Creating a New Model

Start with the required top-level structure:

```json
{
  "modelMetadata": {
    "modelId": "unique-id",
    "modelName": "Programme Name - Canonical Service Domain Model",
    "version": "1.0.0",
    "organisation": "Organisation Name",
    "createdDate": "YYYY-MM-DD",
    "lastModified": "YYYY-MM-DD",
    "author": "Architect Name",
    "description": "Description of what this model covers."
  },
  "services": [],
  "aiPersonas": [],
  "humanActors": [],
  "systemActors": [],
  "interactions": [],
  "externalInteractions": [],
  "governance": {},
  "processes": []
}
```

### 2. Adding Services

Each service requires at minimum:

```json
{
  "id": "svc-id",
  "name": "Service Name",
  "level": 0,
  "mission": "What this service does for the business.",
  "serviceType": "core"
}
```

Key rules:
- **Level 0** services: 4-8 per organisation (enterprise view)
- **Level 1** services: 5-9 per parent domain (drill-down)
- Child services require `parentId` linking to parent service
- Service types: `core`, `support`
- AI Persona services set `isAIPersona: true`
- AI RM must appear as a visible shared/support service

### 3. Adding AI Personas

For each service marked `isAIPersona: true`, add an entry in `aiPersonas`:

```json
{
  "id": "ap-id",
  "serviceId": "svc-id",
  "authorityModel": "hybrid",
  "confidenceThresholds": {
    "autonomous": 0.8,
    "escalate": 0.5
  },
  "riskClassification": "tier-2",
  "sops": [
    {
      "sopId": "SOP-XXX-01",
      "name": "SOP Name",
      "mcpServer": "server-name.mcp"
    }
  ]
}
```

Authority models: `autonomous`, `hybrid`, `supervised`

### 4. Adding Actors and Interactions

**Human actors** require `id`, `name`, `isExternal`, and `serviceAssociations`.

**System actors** require `id`, `name`, and `serviceAssociations`.

**Interactions** require `id`, `sourceId`, `targetId`, `label`, and `interactionType`.

Interaction types: `capability_invocation`, `data_flow`, `escalation`, `support`, `external`, `approval`

Association types: `owner`, `consumer`, `provider`, `data_source`, `escalation_target`, `integration_target`

### 5. Collaborative (Multi-Company) Model

The collaborative model (`acid-collaborative.json`) captures the network-level view of the entire ACID supply chain. It differs from single-company models:

**Structure differences:**
- Each company appears as an L0 service (e.g., `av` for AeroVista, `st` for SpinnyThings)
- L1 services under each company represent that company's key capabilities
- Interactions represent cross-company material flows, agent deployments, and data exchanges
- `tags` on services indicate tier level (e.g., `tier-0`, `tier-1`, `tier-2`)

**When updating the collaborative model:**
1. Ensure every company with an individual model has a corresponding L0 service
2. L1 services should align with L0 services in the individual company model
3. Cross-company interactions must reference valid service IDs on both sides
4. Use `tags` to capture supply chain metadata (tier, material type, capability)
5. Processes in the collaborative model represent cross-company scenarios (Quality Escape, AOG, Schedule Slip)

**Reconciliation with individual models:**
- After updating a company's individual model, check if the collaborative model needs corresponding updates
- The collaborative model is a summary view — it should not contain more detail than individual models
- Use `cross-model-validator` to check consistency after updates

### 6. Incremental Update Commands

For targeted updates without rewriting the entire model, use these patterns:

#### Add Service
```
add-service: Read the model, append to services array, assign next available ID following the model's convention, set parentId if L1+, update lastModified and increment patch version.
```

#### Add Persona
```
add-persona: Read the model, verify the target service exists and has isAIPersona: true, append to aiPersonas array, assign ap-{abbreviation} ID, update lastModified and increment patch version.
```

#### Add Interaction
```
add-interaction: Read the model, verify both sourceId and targetId exist, append to interactions array, assign next int-{nnn} ID, update lastModified and increment patch version.
```

#### Add Actor
```
add-actor: Read the model, append to humanActors or systemActors, verify all serviceAssociation serviceIds exist, assign ha-{role} or sa-{system} ID, update lastModified and increment patch version.
```

#### Update Entity
```
update-entity: Read the model, find entity by ID across all arrays, apply field updates, preserve unchanged fields, update lastModified and increment patch version.
```

#### Remove Entity
```
remove-entity: Read the model, find entity by ID, check for dangling references (interactions, associations), warn if references exist, remove entity, update lastModified and increment minor version.
```

## AI Persona Dual Representation

AI Personas live in two places in the canonical model: as a service (in `services[]`) with `isAIPersona: true`, and as a delegation contract (in `aiPersonas[]`) with the authority model, SOPs, and guardrails. Practitioners naturally think about AI Personas from either direction — sometimes as an architectural service ("it has an API, consumers, and sits in a domain") and sometimes as a delegated business role ("it has authority boundaries, SOPs, and escalation rules"). The tooling must accept either starting point and ensure both representations are created and kept in sync.

### Either Door In

When a practitioner asks to create an AI Persona, they may approach from either direction:

- **Service-first.** "Add a Quality AI service to the Quality domain." The practitioner is thinking architecturally — where the persona sits, what it connects to, who consumes it.
- **Delegation-first.** "Define an AI Persona that handles demand forecasting under hybrid authority." The practitioner is thinking about the business delegation — what the persona is allowed to do, how it escalates, what SOPs it runs.

In both cases, the skill ensures the other half is created so the model never contains a one-sided persona.

### Auto-Pairing Logic

#### Service-first (creating a service with isAIPersona: true)

When a new service is added with `isAIPersona: true`, or when an existing service has `isAIPersona` set to `true`:

1. Check whether an `aiPersonas[]` entry already exists with a matching `serviceId`.
2. If no matching entry exists, auto-create a stub delegation contract:
   ```json
   {
     "id": "ap-{service.id}",
     "serviceId": "{service.id}",
     "authorityModel": null,
     "sops": []
   }
   ```
3. Prompt the practitioner: "Created a stub delegation contract for '{service.name}'. What authority model should this persona use? (autonomous / hybrid / supervised)"
4. If the practitioner provides an authority model, populate it immediately. If they defer, leave the stub — the `canonical-model-validator` will raise a V-PERSONA-002 warning.

#### Delegation-first (creating an aiPersonas entry without a matching service)

When a practitioner asks to create an AI Persona entry and no matching service exists:

1. Prompt for architectural placement:
   - **Domain parent:** "Which domain should this persona sit under?" (list existing L0 services)
   - **Level:** Confirm level (typically L1 or L2 under the chosen parent)
   - **Service type:** Default to `core` unless the practitioner specifies otherwise
2. Create the service entry with `isAIPersona: true`:
   ```json
   {
     "id": "{domain-prefix}-{persona-name}-ai",
     "name": "{Persona Name}",
     "level": 1,
     "parentId": "{parent.id}",
     "mission": "{derived from persona description}",
     "serviceType": "core",
     "isAIPersona": true
   }
   ```
3. Set the `serviceId` on the `aiPersonas` entry to the newly created service's `id`.
4. Inform the practitioner: "Created service '{service.name}' under '{parent.name}' and linked it to the delegation contract."

### Paired Deletion

When deleting either side of an AI Persona's dual representation:

- **Deleting a service with isAIPersona: true.** Before removing, check for a matching `aiPersonas[]` entry. If found, warn: "This service has a linked delegation contract ('{aiPersona.id}'). Deleting the service will orphan the contract. Delete both? (yes / keep contract / cancel)" If the practitioner confirms paired deletion, remove both entries and clean up any interactions referencing the deleted service.
- **Deleting an aiPersonas entry.** Before removing, check the linked service. Warn: "The service '{service.name}' is still marked as an AI Persona but will have no delegation contract. Remove the isAIPersona flag from the service as well? (yes / keep flag / cancel)" If the practitioner confirms, either remove the `isAIPersona` flag or delete the service entirely, depending on the response.

In all cases, after paired deletion, scan `interactions[]` and actor `serviceAssociations[]` for dangling references and report them.

### ID Convention

The dual representation uses a consistent naming convention:

| Entity | Pattern | Example |
|--------|---------|---------|
| Service (AI Persona) | `{domain}-{name}-ai` | `quality-inspector-ai`, `demand-forecast-ai` |
| Delegation contract | `ap-{service.id}` | `ap-quality-inspector-ai`, `ap-demand-forecast-ai` |

When the service already has an established ID (e.g., `av-quality`), the persona ID derives from it: `ap-av-quality`. The `ap-` prefix ensures delegation contracts are immediately distinguishable from services in any listing, search, or report.

### 7. Pre-Write Validation

Before writing any changes to the model file, always validate:

- [ ] All new entity IDs are unique within the model
- [ ] All references (parentId, serviceId, sourceId, targetId) point to existing entities
- [ ] Service counts remain within methodology bounds after the change
- [ ] No new orphaned entities are created
- [ ] `modelMetadata.lastModified` is updated to today's date
- [ ] `modelMetadata.version` is incremented appropriately:
  - **Patch** (x.x.+1): Adding entities, updating fields
  - **Minor** (x.+1.0): Removing entities, structural changes
  - **Major** (+1.0.0): Breaking schema changes

For comprehensive validation after writes, use the `canonical-model-validator` skill.

### 8. Validation (Quick Check)

Before considering the model complete, verify:

- [ ] `modelMetadata` has all required fields
- [ ] Every service has `id`, `name`, `level`, `mission`, `serviceType`
- [ ] Level 1+ services have valid `parentId`
- [ ] Every `isAIPersona: true` service has a matching `aiPersonas` entry
- [ ] All `sourceId` and `targetId` in interactions reference valid entity IDs
- [ ] All `serviceId` references in actors and personas are valid
- [ ] Service counts are within methodology bounds (4-8 at L0, 5-9 at L1)
- [ ] AI RM appears as a shared/support service
- [ ] No orphaned entities (actors or personas without service associations)

## ID Naming Conventions

Follow the patterns established in existing ACID models:

**Single-company models** (e.g., aerovista.json):
- Services: `{company-prefix}-{domain}` (e.g., `av-core-ops`, `av-quality`, `st-manufacturing`)
- AI Personas: `ap-{company-prefix}-{function}` (e.g., `ap-av-quality`, `ap-st-demand`)
- Human actors: `ha-{company-prefix}-{role}` (e.g., `ha-av-quality-dir`)
- System actors: `sa-{company-prefix}-{system}` (e.g., `sa-av-sap`, `sa-st-mes`)
- Interactions: `int-{company-prefix}-{nnn}` (e.g., `int-av-001`)
- External interactions: `ext-{company-prefix}-{nnn}` (e.g., `ext-av-001`)

**Collaborative model** (acid-collaborative.json):
- Company services: Short 2-letter codes (e.g., `av`, `st`, `tf`, `sf`)
- Cross-company interactions: `int-{source}-{target}-{nnn}` (e.g., `int-av-st-001`)
- Processes: `proc-{scenario}` (e.g., `proc-quality-escape`, `proc-aog`)

## Relationship to Other Skills

- **Downstream**: `canonical-model-validator` (validates after changes), `service-architecture-renderer` (renders diagrams), `bsa-documentation-generator` (generates docs)
- **Enrichment**: `bsa-persona-enricher` (enriches persona stubs into full definitions)
- **Cross-model**: `cross-model-validator` (validates consistency after collaborative model changes)

## Output

The skill produces a valid JSON file that can be:
- Rendered as SVG diagrams using the `service-architecture-renderer` skill
- Validated using `canonical-model-validator` and `cross-model-validator`
- Used as input for governance reviews and compliance checks
- Stored as the living architecture artifact referenced throughout the methodology
