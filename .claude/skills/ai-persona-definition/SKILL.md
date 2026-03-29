---
name: ai-persona-definition
description: Guides you through populating the 19-section AI Persona Definition Template to create a complete contractual specification for an AI Persona. Use this when defining a new AI Persona or formalising an existing one. Supports canonical model integration and batch mode.
---

# AI Persona Definition

This skill guides the creation of a complete AI Persona contractual specification using the methodology's 19-section template. The output is a filled-in definition document that serves as the formal delegation contract for an AI Persona. Supports reading persona stubs from canonical models, writing back enriched data, and batch-defining multiple personas in a domain.

## When to Use

- After the Three Questions of Delegation identify a strong AI Persona candidate
- When formalising an existing AI implementation into a governed persona
- When reviewing or updating an existing persona definition
- As part of the delegation package preparation (Chapter 8)
- When batch-defining all AI Personas in a domain or company model
- When enriching persona stubs from canonical models (see also `bsa-persona-enricher` for automated pre-population)

## Template Reference

The full template is at: `.claude/agents/references/templates/AI-Persona-Definition-Template.md`

## Instructions

### 1. Prerequisites

Before starting, ensure you have:
- Completed Three Questions of Delegation results (strong answers required)
- The service architecture context (which service domain owns this persona)
- A named business owner who will be accountable
- The risk classification tier (1/2/3) from Chapter 9

### 1b. Canonical Model Integration (Optional)

If a canonical model exists for the persona's company, read the persona stub to pre-populate sections:

1. Load the canonical model from `docs/architecture/bsa/canonical-models/[company].json`
2. Find the `aiPersonas` entry matching the persona being defined
3. Extract: `id`, `serviceId`, `authorityModel`, `confidenceThresholds`, `riskClassification`, `sops`
4. Find the owning service for `name`, `mission`, `owner`, `tags`
5. Find all interactions where the persona's service is `sourceId` or `targetId`
6. Find all actors associated with the persona's service

This pre-populates Sections 1, 2, 4, 5 (partially), 8, 9, and 13 (from tags). Remaining sections require manual input.

### 2. Work Through the 19 Sections

Complete each section in order. The sections are:

| # | Section | Key Inputs Needed | Auto-Fill from Model |
|---|---------|-------------------|---------------------|
| 1 | **AI Persona Identification** | Name, ID, version, owning service | Yes |
| 2 | **Governance and Ownership** | Business owner, AI RM liaison, controlling domain | Partial |
| 3 | **Three-Question Discovery Results** | Delegation statement, management approach, team integration | No |
| 4 | **Intent and Mandate** | Primary intent, business objective alignment, success criteria | Partial |
| 5 | **Capabilities (Permitted Actions)** | Exhaustive list of CAN do; explicit list of CANNOT do | Partial (from SOPs) |
| 6 | **Data Contract** | Permitted sources, fields, restrictions, quality thresholds | No |
| 7 | **Scope & Ways of Working** | Business rules, ethical guardrails, operational constraints | No |
| 8 | **Authority Model** | Owner vs Invoker authority, confidence thresholds, escalation triggers | Yes |
| 9 | **Interacting Services and Actors** | Service dependencies, human interactions, system integrations | Yes |
| 10 | **Performance Measurement (5-Tier)** | Measures at each tier the persona contributes to | No |
| 11 | **Multi-Contributor KPI Attribution** | How shared KPIs are attributed between human and AI | No |
| 12 | **Lifecycle Management** | Development, deployment, monitoring, retraining schedule | No |
| 13 | **Regulatory and Compliance** | Applicable regulations, audit needs | Partial (from tags) |
| 14 | **Risk Management** | Risk assessment, mitigation controls, incident response | Partial (risk tier) |
| 15 | **Trusted AI (Scope) Framework** | Scope boundary definition, clarity checklist | No |
| 16 | **Collaborative Data Supply Chain** | Data flow mapping, upstream/downstream contracts | Partial |
| 17 | **Worked Example** (optional) | Scenario walkthrough | No |
| 18 | **Approval and Sign-Off** | Business owner, AI RM, compliance sign-off | Partial |
| 19 | **Supporting Documentation** | References to diagrams, specs, related personas | Yes |

### 3. Quality Criteria for Each Section

**Section 3 — Three Questions must have STRONG answers:**

- **Q1 (What to delegate):** Specific, bounded, measurable. Weak: "Help with tasks." Strong: "Approve standard POs under $5,000 where vendor is pre-qualified and budget confirmed."
- **Q2 (How to manage):** Concrete oversight mechanisms. Weak: "We'll monitor it." Strong: "Dual approval for vendors near limits; alert lead when variance exceeds 10%; quarterly audit."
- **Q3 (How to include):** Clear operational rhythm. Weak: "It runs in background." Strong: "Reviews requests every 2 hours; lead reviews weekly; team adjusts guardrails quarterly."

**Section 5 — Capabilities must be exhaustive:**
- If an action is not explicitly listed as permitted, it is prohibited
- Use a capability table: ID, action, inputs, outputs, approval required

**Section 8 — Authority model must be unambiguous:**
- **Owner Authority:** Standing delegation, persona acts autonomously within mandate
- **Invoker Authority:** Task-specific, persona acts as assistant for human/system request
- **Hybrid:** Autonomous above confidence threshold, escalates below it

### 4. Governance Calibration by Risk Tier

Adjust governance depth based on risk classification:

| Risk Tier | Governance Weight | Sections Requiring Extra Detail |
|-----------|------------------|-------------------------------|
| Tier 1 (Low) | Light | Sections 1-8 sufficient; 12-14 can be brief |
| Tier 2 (Medium) | Standard | All sections complete; quarterly reviews |
| Tier 3 (High) | Heavy | All sections with maximum detail; monthly reviews; external audit |

### 5. Batch Mode

When defining multiple personas across a domain or company:

1. **Survey**: List all AI Personas in the target scope (from canonical model `aiPersonas` array or from discovery outputs)
2. **Prioritise**: Order by risk tier (Tier 3 first) then by deployment timeline
3. **Batch summary**: Generate a tracking table:

```markdown
# Persona Definition Batch: [Domain/Company]

| # | Persona ID | Name | Risk Tier | Status | Sections Complete | Blocker |
|---|-----------|------|-----------|--------|-------------------|---------|
| 1 | ap-quality | Quality AI | Tier 3 | In Progress | 12/19 | Awaiting Q3 answer |
| 2 | ap-demand | Demand Forecast | Tier 2 | Not Started | 0/19 | — |
| 3 | ap-monitor | Production Monitor | Tier 1 | Complete | 19/19 | — |
```

4. **Cross-reference**: As you define each persona, note interactions with other personas in the batch — these inform Section 9 and Section 16 for related personas
5. **Completion**: After all personas are defined, run a consistency check across the batch to ensure cross-references are reciprocal

### 6. Write-Back to Canonical Model

After completing a persona definition, update the canonical model with any new information:

- New SOPs identified during capability analysis (Section 5) → add to `aiPersonas[].sops`
- New interactions identified (Section 9) → add to `interactions`
- New actors identified (Section 9) → add to `humanActors` or `systemActors`
- Updated risk classification (Section 14) → update `riskClassification`
- Updated authority thresholds (Section 8) → update `confidenceThresholds`

Use `canonical-model-manager` incremental update patterns for the write-back.

### 7. Completion Checklist

Before finalising, verify:
- [ ] All 19 sections completed with specific (not generic) information
- [ ] Three Questions have strong answers
- [ ] Business owner identified and accountable
- [ ] Scope boundaries explicitly defined (in-scope AND out-of-scope)
- [ ] Capabilities list is exhaustive
- [ ] Data contract specifies exact fields, not just system names
- [ ] Authority model is clear and appropriate for risk tier
- [ ] Performance measures span all 5 tiers
- [ ] Multi-contributor attribution method defined
- [ ] Tripartite accountability confirmed (Service Owner + SOP Owner + AI RM)
- [ ] Canonical model updated with any new information (if model integration used)

## Output Location

Write persona definitions alongside existing per-company persona docs:
`docs/architecture/bsa/[company-name]/personas/[persona-slug].md`

This matches the existing structure on disk (e.g., `docs/architecture/bsa/aerovista/personas/aog-response-coordinator-ai.md`). Use kebab-case slugs derived from the persona name.

Batch summary (if batch mode):
`docs/architecture/bsa/[company-name]/personas/_batch-summary.md`

## Relationship to Other Skills

- **Upstream**: `canonical-model-manager` (provides persona stubs), `bsa-persona-enricher` (automates pre-population)
- **Downstream**: `readiness-scorecard` (requires complete definition), `measurement-blueprint` (Sections 10-11)
- **Write-back**: `canonical-model-manager` (update model after definition), `canonical-model-validator` (validate after write-back)

## Output

A completed AI Persona Definition document following the 19-section template structure. This document becomes part of the delegation package alongside the SOP summary and readiness scorecard.
