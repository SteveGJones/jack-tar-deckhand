---
name: bsa-documentation-generator
description: Generates markdown documentation from canonical model JSON — service catalogues, AI Persona summaries, interaction matrices, dependency tables. Produces human-readable architecture docs from machine-readable models.
---

# BSA Documentation Generator

This skill transforms canonical service domain model JSON files into human-readable markdown documentation. It generates service catalogues, AI Persona summaries, interaction matrices, and dependency tables — ensuring architecture documentation stays in sync with the canonical model.

## When to Use

- After completing or updating a canonical model to produce stakeholder-ready documentation
- When preparing architecture review packages for Change Advisory Circles
- To generate service catalogues for onboarding new team members
- When preparing delegation packages that need readable summaries
- As part of the `bsa-pipeline-orchestrator` end-to-end architecture package

## Instructions

### 1. Locate the Canonical Model

Input is one or more canonical model JSON files from:
`docs/architecture/bsa/canonical-models/*.json`

If generating documentation for the entire ACID supply chain, also include the collaborative model:
`docs/architecture/bsa/canonical-models/acid-collaborative.json`

### 2. Choose Output Documents

Select which documents to generate based on the audience and need:

| Document | Audience | Content |
|----------|----------|---------|
| Service Catalogue | Architects, managers | All services with missions, owners, types, levels |
| AI Persona Summary | Governance, AI RM | All personas with authority, SOPs, risk tiers |
| Interaction Matrix | Integration teams | Source-target matrix of all interactions |
| Actor Directory | All stakeholders | Human and system actors with service associations |
| Dependency Table | Architects | Service dependencies extracted from interactions |
| SOP Register | MCP/SOP developers | All SOPs across all personas, grouped by server |
| Complete Architecture Pack | All audiences | All of the above in a single document |

### 3. Generate Service Catalogue

For each service in the model, produce:

```markdown
## Service Catalogue

### [Service Name] (`service-id`)

| Field | Value |
|-------|-------|
| Level | [0/1/2] |
| Type | [core/support] |
| Parent | [parent service name or "—" for L0] |
| Owner | [owner name] |
| AI Persona | [Yes/No] |
| Mission | [mission text] |
| Tags | [comma-separated tags] |

**Interactions:**
- [direction arrow] [other entity] — [label] ([interaction type])
```

Group services by level, then by parent. L0 services first, then L1 under each parent.

### 4. Generate AI Persona Summary

For each AI Persona:

```markdown
## AI Persona: [Persona Name]

| Field | Value |
|-------|-------|
| ID | [persona id] |
| Service | [owning service name] |
| Authority Model | [autonomous/hybrid/supervised] |
| Risk Classification | [tier] |
| Confidence Thresholds | Autonomous: [x], Escalate: [y] |

### SOPs
| SOP ID | Name | MCP Server |
|--------|------|------------|
| [id] | [name] | [server] |

### Interactions
[List all interactions where the persona's service is source or target]
```

### 5. Generate Interaction Matrix

Build a matrix showing all interactions between entities:

```markdown
## Interaction Matrix

| Source → Target | [Entity 1] | [Entity 2] | [Entity 3] | ... |
|-----------------|------------|------------|------------|-----|
| [Entity 1] | — | data_flow | | |
| [Entity 2] | escalation | — | capability | |
| [Entity 3] | | approval | — | |
```

For large models, split the matrix by:
- Intra-domain interactions (within a service domain)
- Cross-domain interactions (between L0 domains)
- External interactions (with outside systems)

### 6. Generate Actor Directory

```markdown
## Actor Directory

### Human Actors

| ID | Name | External | Service Associations |
|----|------|----------|---------------------|
| [id] | [name] | [Yes/No] | [service: role, service: role] |

### System Actors

| ID | Name | Service Associations |
|----|------|---------------------|
| [id] | [name] | [service: role, service: role] |
```

### 7. Generate Dependency Table

Extract dependencies from interactions:

```markdown
## Service Dependencies

| Service | Depends On | Via Interaction | Type | Critical |
|---------|-----------|-----------------|------|----------|
| [service] | [dependency] | [interaction id] | [type] | [Yes/No] |
```

Mark as critical if the interaction type is `capability_invocation` or `escalation`.

### 8. Generate SOP Register

```markdown
## SOP Register

### By MCP Server

#### [server-name.mcp]
| SOP ID | Name | Owning Persona | Authority Model |
|--------|------|----------------|-----------------|
| [id] | [name] | [persona name] | [model] |

### By Domain
[Group SOPs by the L0 domain of their owning persona's service]
```

### 9. Complete Architecture Pack

Combine all documents above into a single markdown file with a table of contents:

```markdown
# [Organisation] — Architecture Documentation
**Generated from:** [model file name]
**Model version:** [version]
**Generated:** [date]

## Table of Contents
1. Service Catalogue
2. AI Persona Summary
3. Interaction Matrix
4. Actor Directory
5. Service Dependencies
6. SOP Register

---
[Include all sections]
```

### 10. Output Location

Write generated documentation alongside existing per-company docs:
`docs/architecture/bsa/[company-name]/`

This matches the existing structure on disk where each company already has a directory (e.g., `docs/architecture/bsa/aerovista/`) with per-domain markdown files.

Use filenames:
- `_service-catalogue.md` (underscore prefix for generated files)
- `_ai-persona-summary.md`
- `_interaction-matrix.md`
- `_actor-directory.md`
- `_dependency-table.md`
- `_sop-register.md`
- `_architecture-pack.md` (complete)

The underscore prefix distinguishes generated files from hand-authored docs (e.g., `README.md`, `core-operations.md`).

For cross-model documentation (not specific to one company), write to:
`docs/architecture/bsa/generated/`

## Relationship to Other Skills

- **Upstream**: `canonical-model-manager` (creates the models), `canonical-model-validator` (validates before doc generation)
- **Parallel**: `service-architecture-renderer` (produces SVG diagrams alongside these markdown docs)
- **Downstream**: `methodology-compliance-check` (docs support compliance evidence), `bsa-pipeline-orchestrator` (includes this skill in the pipeline)

## Output

One or more markdown files containing human-readable architecture documentation generated directly from the canonical model JSON. All content is traceable back to the model — no manual content is added.
