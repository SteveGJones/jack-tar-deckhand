---
name: dependency-register
description: Builds and maintains the dependency register with unique IDs tracking all cross-service and cross-domain dependencies. Use this during architecture completion (Chapter 8) to document how services, AI Personas, and SOPs depend on each other.
---

# Dependency Register

This skill builds the dependency register — the authoritative record of all cross-service and cross-domain dependencies in the architecture. Each dependency gets a unique ID and is tracked through the Change Advisory Circle process.

## When to Use

- During Chapter 8 architecture completion workshops
- When adding new AI Personas that consume capabilities from other domains
- When an SOP owned by one domain is invoked by another service or persona
- Before Change Advisory Circle reviews to document what's changing
- When updating the cross-domain SOP register

## Template References

- Cross-domain SOP register: `methodology_draft/templates/cross-domain-sop-register.md`
- Delegation package checklist: `methodology_draft/templates/delegation-package-checklist.md`

## Instructions

### 1. Identify Dependencies

For each AI Persona and service, ask:

- What data does it consume from other domains?
- What capabilities does it invoke from other domains' MCP servers?
- What SOPs does it borrow from other domains?
- What escalation paths cross domain boundaries?
- What shared KPIs create measurement dependencies?

### 2. Assign Unique Dependency IDs

Use the naming convention: `DEP-{consumer abbreviation}-{provider abbreviation}-{sequence}`

Examples:
- `DEP-QIA-SCADA-01` — Quality Inspection AI depends on SCADA system
- `DEP-DFA-LOG-01` — Demand Forecasting AI depends on Logistics data
- `DEP-MFG-SC-03` — Manufacturing depends on Supply Chain service

### 3. Document Each Dependency

For each dependency, capture:

| Field | Description | Example |
|-------|-------------|---------|
| **Dependency ID** | Unique identifier | `DEP-QIA-SCADA-01` |
| **Consumer** | Service or AI Persona that depends on the capability | Quality Inspection AI Persona |
| **Provider** | Service or system that provides the capability | SCADA System (Manufacturing) |
| **Dependency Type** | data_flow, capability_invocation, escalation, approval | `data_flow` |
| **Description** | What is being consumed and why | "Real-time sensor readings for defect detection" |
| **Criticality** | High/Medium/Low — impact if dependency fails | High |
| **SOP Reference** | If an SOP is borrowed, its ID | `SOP-MFG-03` |
| **MCP Server** | If capability invocation, the hosting MCP server | `manufacturing-control.mcp` |
| **Owning Domain** | Domain that owns the providing capability | Manufacturing |
| **Consuming Domain** | Domain that consumes the capability | Manufacturing (Quality sub-service) |
| **Cross-Domain?** | Yes/No — does this cross domain boundaries? | No (same parent) |
| **CAC Required?** | Does this require Change Advisory Circle review? | Yes (if cross-domain) |
| **Fallback** | What happens if this dependency is unavailable | "Manual inspection queue activated" |

### 4. Build the Register Table

```markdown
| Dep ID | Consumer | Provider | Type | Criticality | Cross-Domain | CAC Required | Status |
|--------|----------|----------|------|-------------|--------------|-------------|--------|
| DEP-QIA-SCADA-01 | Quality AI | SCADA | data_flow | High | No | No | Active |
| DEP-QIA-SUP-01 | Quality AI | Supplier Portal | capability_invocation | Medium | Yes | Yes | Pending |
```

### 5. Validate the Register

Check for completeness:

- [ ] Every AI Persona has at least one dependency entry (data source at minimum)
- [ ] Every cross-domain SOP borrowing has a corresponding dependency
- [ ] All dependencies have unique IDs following the naming convention
- [ ] Criticality is assessed for each dependency
- [ ] Cross-domain dependencies are flagged for Change Advisory Circle review
- [ ] Fallback procedures documented for all high-criticality dependencies
- [ ] "One Server, One Owner" — every SOP has exactly one owning domain
- [ ] No circular dependencies that could create deadlocks

### 6. Cross-Domain SOP Register

For dependencies involving borrowed SOPs, also populate the cross-domain SOP register:

| Field | Description |
|-------|-------------|
| **SOP ID** | Stable SOP identifier (e.g., `SOP-LOG-02`) |
| **Owning service/domain** | Service responsible for the SOP and MCP server |
| **Borrowing service/persona** | Service or persona that invokes the SOP |
| **Dependency ID** | Link back to dependency register (e.g., `DEP-QI-SUP-01`) |
| **MCP server** | Endpoint hosting the SOP |
| **Invocation purpose** | What value exchange is being satisfied |
| **Vanilla-Agent status** | Latest dry run date and result |
| **Change Advisory Circle date** | Last review date and attendees |

### 7. Collaboration Archetypes

For each cross-domain dependency, assign a collaboration archetype:

- **Observer** — Consumer receives telemetry/notifications only (read-only)
- **Collaborator** — Bidirectional shared decisions (both contribute to outcomes)
- **Co-owner** — Dual governance board required (shared accountability)

## Output

A completed dependency register with:
- Unique DEP-IDs for every cross-service dependency
- Cross-domain SOP register entries for borrowed SOPs
- Collaboration archetypes assigned
- Change Advisory Circle requirements flagged
- Fallback procedures for critical dependencies
