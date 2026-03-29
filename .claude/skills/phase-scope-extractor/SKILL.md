---
name: phase-scope-extractor
description: Extracts a phase-specific subset from the full BSA — isolates which companies, services, AI Personas, SOPs, interactions, and actors are in scope for a given phase or demo scenario. Produces a scope boundary document.
---

# Phase Scope Extractor

This skill extracts a bounded subset of the full BSA for a specific phase, milestone, or demo scenario. It identifies exactly which entities are in scope and out of scope, producing a scope boundary document that serves as the single source of truth for what needs to be implemented, tested, or demonstrated.

## When to Use

- When starting a new implementation phase to define its boundary
- When preparing a demo to identify which entities must work end-to-end
- When onboarding new team members to a specific phase of work
- When creating test plans that need to cover all in-scope entities
- When assessing readiness for a milestone gate

## Instructions

### 1. Define the Scope Criteria

Choose the scope boundary based on the phase:

| Scope Type | Criteria | Example |
|-----------|----------|---------|
| Company subset | Which companies are in scope | Phase 1: AeroVista + SpinnyThings only |
| Scenario subset | Which demo scenarios must work | Quality Escape + AOG + Schedule Slip |
| Authority subset | Which authority levels are exercised | Phase 1: Levels 0-3 all demonstrated |
| Domain subset | Which service domains are active | Core Ops + Quality + Supply Chain (not Sustainability) |

### 2. Load Canonical Models

Load the canonical models for all in-scope companies:
`docs/architecture/bsa/canonical-models/[company].json`

Also load the collaborative model for cross-company interactions:
`docs/architecture/bsa/canonical-models/acid-collaborative.json`

### 3. Trace Scenario Entity Chains

For each in-scope demo scenario, trace the complete entity chain:

1. **Identify the trigger** — what event starts the scenario?
2. **Trace the response chain** — which service detects it? Which AI Persona acts?
3. **Follow cross-company paths** — when does an agent deploy to another company? Which SOPs does it invoke?
4. **Track human touchpoints** — where do humans approve, review, or escalate?
5. **Map authority boundaries** — at each step, what authority level is exercised?

Record each step as:

| Step | Actor/Persona | Action | Company | SOPs Invoked | Authority Level |
|------|---------------|--------|---------|-------------|----------------|

### 4. Extract In-Scope Entities

From the scenario traces, compile the complete list of entities:

#### Services
List every service (L0 and L1) that participates in at least one scenario. Include:
- Service ID (from canonical model)
- Name
- Company
- Which scenarios it participates in

#### AI Personas
List every AI Persona activated in at least one scenario. Include:
- Persona ID
- Name
- Company
- Authority level in this phase
- Which scenarios activate it

#### SOPs
List every SOP invoked in at least one scenario. Distinguish between:
- **MCP-exposed SOPs** (callable by external agents via the MCP server)
- **Internal SOPs** (used within a persona's own company node)

#### Interactions
List every interaction that fires, especially cross-company interactions.

#### Human Actors
List every human actor who participates (approvers, escalation targets, reviewers).

#### System Actors
List every system actor involved (ERP, MES, external systems).

### 5. Identify Gaps

Flag entities that are required by scenario logic but don't exist in the canonical models:

| # | Entity Type | Description | Required By | Status |
|---|------------|-------------|-------------|--------|
| 1 | SOP | `report_quality_issue` | Quality Escape | MISSING — needs creation |
| 2 | Human Actor | Plant Manager (2FA approver) | Quality Escape | MISSING — needs creation |

These gaps become immediate work items for model updates.

### 6. Write the Scope Document

Output structure:

```markdown
# ACID Phase [N] Scope: [Phase Description]

## Overview
[Brief description: companies, scenarios, entity counts]

## Scope Boundary
| Category | In Scope | Out of Scope |
|----------|----------|-------------|
[Clear boundary table]

## Demo-Essential Entities

### Services (In Scope)
[Table with IDs, names, companies, scenarios]

### AI Personas (In Scope)
[Table with IDs, names, authority, scenarios]

### SOPs (In Scope)
[Table split by MCP-exposed vs internal]

### Interactions (In Scope)
[Table with cross-company interactions highlighted]

### Human Actors (In Scope)
[Table with roles and demo involvement]

### System Actors (In Scope)
[Table with systems and integrations]

## Scenario Entity Maps
[Step-by-step chain per scenario]

## Missing Entities (Gaps)
[Table of gaps requiring model updates]

## Summary Statistics
[Counts and percentages vs full BSA]
```

### 7. Validate Completeness

After writing the scope document, verify:

- [ ] Every scenario has a complete entity chain from trigger to resolution
- [ ] Every entity in the chains exists in the canonical model (or is flagged as MISSING)
- [ ] Every cross-company interaction has matching entities on both sides
- [ ] Every human approval point has an identified actor
- [ ] Every SOP invocation has a defined SOP (or is flagged as MISSING)
- [ ] No entity appears in multiple scenarios with conflicting authority levels

## Output Location

Write scope documents to:
`docs/architecture/bsa/PHASE-[N]-SCOPE.md`

Example: `docs/architecture/bsa/PHASE-1-SCOPE.md`

## Relationship to Other Skills

- **Upstream**: `canonical-model-manager` (provides the models to extract from), `cross-model-validator` (validates cross-company consistency)
- **Downstream**: `bsa-persona-enricher` (uses scope to prioritise which personas to enrich), `demo-scenario-validator` (validates scenarios against scope), `dependency-register` (tracks dependencies within scope)
- **Informs**: Implementation work packages, test plans, demo rehearsal scripts

## Output

A phase scope document identifying every in-scope entity with canonical model IDs, scenario entity maps showing step-by-step chains, and a gap analysis flagging missing entities. This document becomes the authoritative boundary for the phase.
