---
name: bsa-cross-reference-index
description: Builds a master cross-reference index across all canonical models — which personas appear where, which SOPs are referenced by which services, which interactions connect which companies. Produces a navigable index document.
---

# BSA Cross-Reference Index

This skill builds a comprehensive cross-reference index across all canonical models in the ACID supply chain. It answers questions like "Where does this persona operate?", "Which services reference this SOP?", and "What connects these two companies?" — providing a navigable lookup for architects, governance reviewers, and integration teams.

## When to Use

- When architects need to trace an entity across the entire supply chain
- Before making changes to understand the blast radius (what else references this entity)
- When onboarding new team members who need to understand cross-company relationships
- As part of the `bsa-pipeline-orchestrator` pipeline to produce navigable architecture documentation
- When preparing for Change Advisory Circle reviews that require impact assessment

## Instructions

### 1. Load All Models

Scan all canonical models from:
`docs/architecture/bsa/canonical-models/*.json`

Parse each model and build global indexes.

### 2. Build the Persona Index

Track every AI Persona across all models:

```markdown
## AI Persona Cross-Reference

| Persona ID | Name | Home Model | Home Service | Authority | Appears In (Models) | SOPs Owned | Interactions |
|-----------|------|-----------|-------------|-----------|--------------------|-----------:|-------------:|
| ap-quality | Quality AI | aerovista | av-quality-ai | hybrid | aerovista, acid-collaborative | 3 | 7 |
| ap-demand | Demand Forecast | spinnythings | st-demand-ai | autonomous | spinnythings, acid-collaborative | 2 | 4 |
```

For each persona, also list:
- **Home node**: Where it's defined and governed
- **Host nodes**: Where it deploys (from cross-company interactions)
- **SOP list**: All SOPs it owns or invokes
- **Interaction count**: How many interactions reference its service

### 3. Build the SOP Index

Track every SOP across all models:

```markdown
## SOP Cross-Reference

| SOP ID | Name | MCP Server | Owning Persona | Owning Model | Referenced By |
|--------|------|------------|----------------|-------------|---------------|
| SOP-QM-001 | Report Quality Issue | quality.mcp | ap-quality | aerovista | spinnythings (ap-agent) |
| SOP-INV-001 | Check Inventory ATP | inventory.mcp | ap-supply | spinnythings | aerovista (ext-003) |
```

### 4. Build the Service Index

Track services and their cross-model relationships:

```markdown
## Service Cross-Reference

| Service ID | Name | Model | Level | Parent | AI Persona | Connected Models |
|-----------|------|-------|-------|--------|------------|-----------------|
| av-core-ops | Core Operations | aerovista | 0 | — | No | spinnythings, skyframe |
| st-manufacturing | Manufacturing | spinnythings | 0 | — | No | aerovista, titanforge |
```

### 5. Build the Interaction Index

Track all interactions, especially cross-company ones:

```markdown
## Cross-Company Interaction Index

| Interaction ID | Source (Model) | Target (Model) | Label | Type | Scenario |
|---------------|---------------|----------------|-------|------|----------|
| int-av-st-001 | av-supply-chain (aerovista) | st-manufacturing (spinnythings) | Request Engine Status | capability_invocation | AOG |
| int-st-av-001 | st-quality (spinnythings) | av-quality (aerovista) | Report Quality Escape | escalation | Quality Escape |
```

Tag interactions with the demo scenarios they support (Quality Escape, AOG, Schedule Slip).

### 6. Build the Company Connectivity Matrix

Show which companies are connected and how:

```markdown
## Company Connectivity Matrix

| Company → | AeroVista | SpinnyThings | TitanForge | SkyFrame | ... |
|-----------|-----------|-------------|-----------|----------|-----|
| AeroVista | — | 5 interactions | 2 interactions | 3 interactions | |
| SpinnyThings | 5 interactions | — | 3 interactions | 0 | |
| TitanForge | 2 interactions | 3 interactions | — | 0 | |
```

For each cell with interactions, list the interaction types (capability, data_flow, escalation).

### 7. Build the Actor Index

Track actors across models:

```markdown
## Actor Cross-Reference

### Human Actors
| Actor ID | Name | Model | External | Services | Roles |
|---------|------|-------|----------|----------|-------|
| ha-plant-mgr | Plant Manager | spinnythings | No | st-manufacturing | owner |
| ha-quality-dir | Quality Director | aerovista | No | av-quality | owner |

### System Actors
| Actor ID | Name | Model | Services | Role |
|---------|------|-------|----------|------|
| sa-sap | SAP S/4HANA | aerovista | av-core-ops, av-supply-chain | data_source |
| sa-mes | Siemens Opcenter | spinnythings | st-manufacturing | integration_target |
```

### 8. Build the Tag Index

Collect all tags across all models and show which entities use them:

```markdown
## Tag Index

| Tag | Services Using | Models |
|-----|---------------|--------|
| AS9100 | av-quality, st-quality, tf-quality | aerovista, spinnythings, titanforge |
| tier-1 | sf, ax, ss | skyframe, avionix, steelstrut |
| ai-enabled | av-digital-twin, st-digital-twin | aerovista, spinnythings |
```

### 9. Generate Quick-Lookup Sections

For common queries, provide pre-built lookups:

```markdown
## Quick Lookups

### "What connects AeroVista to SpinnyThings?"
[List all interactions between these two companies with details]

### "Where does the Quality AI Persona operate?"
[Home model, host nodes, all interactions]

### "Which services are affected by a Quality Escape?"
[Trace through Quality Escape scenario interactions]

### "What SOPs does SpinnyThings expose to external agents?"
[List all SOPs accessible via cross-company interactions]
```

### 10. Output Location

Write the complete index to:
`docs/architecture/bsa/generated/cross-reference-index.md`

If the index is very large, split into separate files:
- `cross-reference-index.md` (master with links)
- `persona-index.md`
- `sop-index.md`
- `interaction-index.md`
- `connectivity-matrix.md`

Place all in: `docs/architecture/bsa/generated/`

## Relationship to Other Skills

- **Upstream**: `canonical-model-manager` (creates models), `canonical-model-validator` + `cross-model-validator` (validates before indexing)
- **Parallel**: `bsa-documentation-generator` (produces per-model docs; this skill produces cross-model index)
- **Downstream**: `bsa-pipeline-orchestrator` (includes this in the pipeline), `methodology-compliance-check` (index supports compliance evidence)

## Output

A navigable cross-reference index document (or set of documents) providing lookup tables for every persona, SOP, service, interaction, actor, and tag across the entire canonical model suite. Enables rapid impact assessment and architecture navigation.
