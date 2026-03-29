---
name: methodology-compliance-check
description: Validates the current architecture against the AI-First BSA methodology's completeness criteria. Use this to identify gaps, missing artifacts, or governance issues before proceeding to the next phase.
---

# Methodology Compliance Check

This skill runs a systematic compliance check against the AI-First BSA methodology, validating that all required artifacts, governance structures, and quality gates are in place for the current architecture phase.

## When to Use

- After completing a discovery phase (L0 or L1) to verify completeness
- Before entering the execution phase (Chapter 9) as a final gate
- During periodic architecture health checks
- When onboarding a new team that needs to understand what's missing
- Before Change Advisory Circle reviews

## Instructions

### 1. Determine Current Phase

Identify which methodology phase the architecture is in:

| Phase | Chapters | Key Artifacts Expected |
|-------|----------|----------------------|
| Foundation | 1-3 | Business case, stakeholder alignment |
| Service Discovery | 4-6 | L0 services, L1 drill-downs, AI Persona candidates |
| AI Persona Definition | 6E-7 | 19-section persona definitions, AI RM placement |
| Architecture Completion | 8 | Dependency register, cross-domain SOP register, readiness scorecards |
| Execution Readiness | 9 | Realization backlog, risk classification, Vanilla-Agent logs |
| Measurement Design | 10-11 | 5-tier blueprints, attribution models, XLAs |
| Process Modelling | 12 | BPMN diagrams with AI Persona swimlanes |

### 2. Run the Compliance Checklist

Check each applicable section. Mark items as:
- **Green** — Complete and compliant
- **Amber** — Partially complete or needs attention
- **Red** — Missing or non-compliant (blocking)

#### Service Architecture (Chapters 4-6)

- [ ] Level 0 has 4-8 services (not capabilities, not processes)
- [ ] Each service has a named domain owner
- [ ] AI RM is visible as a shared/support service
- [ ] Level 1 has 5-9 sub-services per parent domain
- [ ] AI Persona candidates have strong Three Questions answers
- [ ] Canonical service domain model JSON is valid against schema
- [ ] Service architecture diagrams generated for L0 and L1

#### AI Persona Definitions (Chapters 6E, 7)

- [ ] Each AI Persona has a completed 19-section definition
- [ ] Authority model specified (Owner, Invoker, or Hybrid with thresholds)
- [ ] Data contract defines permitted sources, fields, and restrictions
- [ ] Scope boundaries explicitly define what persona CANNOT do
- [ ] Business owner identified and accountable
- [ ] AI RM liaison assigned

#### Architecture Completion (Chapter 8)

- [ ] Dependency register populated with unique IDs (e.g., `DEP-QIA-SCADA-01`)
- [ ] Cross-domain SOP register tracks all borrowed SOPs
- [ ] "One Server, One Owner" doctrine enforced — every SOP has exactly one owning domain
- [ ] Virtual services identified (if any) with clear ownership
- [ ] Collaboration archetypes assigned (Observer/Collaborator/Co-owner)
- [ ] No super-orchestrators — virtual services coordinate but don't own

#### Execution Readiness (Chapter 9)

- [ ] Realization backlog organised into 4 lanes (Persona Enablement, SOP & MCP Deployment, Integration & Orchestration, Human Enablement)
- [ ] Risk classification applied (Tier 1/2/3) per AI Persona
- [ ] Tripartite accountability defined: Service Owner + SOP Owner + AI RM
- [ ] Change Advisory Circle composition defined for cross-domain changes
- [ ] Vanilla-Agent validation planned for each SOP
- [ ] 7-step implementation cadence documented

#### Measurement (Chapters 10-11)

- [ ] 5-tier measurement blueprint per service/persona
- [ ] Multi-contributor attribution models defined for shared KPIs
- [ ] XLAs designed for human experience of AI interactions
- [ ] Escalation triggers defined at each tier
- [ ] Review cadences assigned (quarterly/monthly/weekly/daily per tier)

#### Process Modelling (Chapter 12)

- [ ] BPMN process diagrams include AI Persona swimlanes
- [ ] Service containment principle followed (processes live within services)
- [ ] Human touchpoints and decision points clearly marked
- [ ] Data flows between swimlanes documented

### 3. Classify and Prioritise Gaps

For each non-green item, classify:

| Gap | Category | Severity | Remediation | Owner | Target Date |
|-----|----------|----------|-------------|-------|-------------|
| [description] | Service/Persona/Governance/Measurement | Red/Amber | [specific action] | [name] | [date] |

Prioritise by:
1. **Red items first** — these block progress
2. **Deployment risk impact** — gaps affecting production AI Personas
3. **Cross-domain impact** — gaps that affect multiple teams
4. **Governance gaps** — missing accountability or oversight

### 4. Produce the Compliance Report

Structure the report as:

```markdown
# Methodology Compliance Report

**Date:** [date]
**Assessor:** [name]
**Architecture Phase:** [current phase]
**Overall Status:** [Green/Amber/Red]

## Summary
[1-2 sentences: overall compliance posture and key findings]

## What's Well Done
[Acknowledge completed items and strong areas]

## Gaps Requiring Attention
### Red (Blocking)
[List with specific remediation actions]

### Amber (Needs Attention)
[List with conditions and deadlines]

## Recommendation
[Proceed / Proceed with Conditions / Halt and Remediate]

## Next Steps
[Specific actions, owners, and dates]
```

### 5. Methodology Artifact Cross-Reference

Verify these artifacts exist and are current:

| Artifact | Template Location | Status |
|----------|------------------|--------|
| Canonical service domain model | `design/canonical-service-domain-model-schema.json` | |
| Service architecture diagrams (L0, L1) | Generated via `service-architecture-renderer` | |
| AI Persona definitions (19-section) | `methodology_draft/templates/AI-Persona-Definition-Template.md` | |
| Dependency register | Built via `dependency-register` skill | |
| Cross-domain SOP register | `methodology_draft/templates/cross-domain-sop-register.md` | |
| Readiness scorecards | `methodology_draft/templates/readiness-scorecard.md` | |
| Delegation packages | `methodology_draft/templates/delegation-package-checklist.md` | |
| Vanilla-Agent test logs | `methodology_draft/templates/vanilla-agent-log.md` | |
| Measurement blueprints | `methodology_draft/templates/Measurement-Blueprint-Template.md` | |
| Realization backlog | 4-lane structure per Chapter 9 | |

## Output

A structured compliance report with:
- Phase-appropriate checklist results (green/amber/red)
- Prioritised gap list with specific remediation actions
- Artifact cross-reference showing what exists and what's missing
- Clear recommendation: proceed, proceed with conditions, or halt
