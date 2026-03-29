# AI Persona Tier Selection Guide

## Purpose

Use this guide to select the right tier of completion for the AI Persona Definition Template. Apply it before starting template work to avoid two failure modes: under-specification creates governance gaps; over-specification stalls discovery. The guide applies the risk classification dimensions from Chapter 10, Section 10.4 to select the minimum viable tier, then describes the progression path as personas mature or risk profiles change.

---

## Quick-Start Decision Tree

Assess the persona against the four risk classification dimensions from Chapter 10, Section 10.4, plus two additional qualifiers (financial authority and data scope). Apply the **Highest Factor Wins** rule -- the single highest-scoring dimension determines the minimum tier.

```
START: Score the persona against each dimension in the Scoring Matrix (below).

1. Does ANY of the four risk dimensions score HIGH?
   YES --> Tier 3 (Full Specification)
   NO  --> Continue

2. Does the persona have financial authority > $50K per autonomous decision?
   (Per-decision = single autonomous action, not annual aggregate.)
   YES --> Tier 3 (Full Specification)
   NO  --> Continue

3. Does the persona consume or produce data across domain boundaries?
   YES --> Tier 3 (Full Specification)
   NO  --> Continue

4. Does ANY of the four risk dimensions score MEDIUM?
   YES --> Tier 2 (Governance-Ready)
   NO  --> Continue

5. All dimensions LOW and single-domain operation?
   YES --> Tier 1 (Discovery)
```

When in doubt, select the higher tier. It is easier to defer sections than to retrofit missing governance after deployment.

---

## Scoring Matrix

Score each dimension independently. These are the same four dimensions used in Chapter 10, Section 10.4. The single highest-scoring dimension determines the minimum tier for the persona.

| Dimension | Low (Tier 1) | Medium (Tier 2) | High (Tier 3) |
|-----------|-------------|-----------------|---------------|
| **Industry Sector** | Unregulated or lightly regulated (e.g., internal operations, general retail) | Moderately regulated (e.g., manufacturing with safety standards, food supply chain) | Heavily regulated (e.g., financial services, healthcare, defence, pharmaceuticals) |
| **Data Sensitivity** | Internal operational data only; no PII, no customer data | Customer data with PII; commercially sensitive data | Regulated data (PHI, financial records, biometric); data subject to cross-border restrictions |
| **Decision Impact** | Recommendations only; no autonomous action; fully reversible | Autonomous actions within defined limits; reversible with cost | Irreversible decisions; safety-critical outcomes; direct customer-facing actions without human review |
| **Geography** | Single jurisdiction; no cross-border data flows | Multiple jurisdictions within one regulatory regime (e.g., US multi-state with CCPA); no cross-regime data transfers | Cross-regime operation (e.g., US + EU, US + APAC); jurisdictions with AI-specific legislation (EU AI Act); cross-border data transfers requiring SCCs or BCRs |

**Rule: Highest Factor Wins.** If a persona scores LOW on three dimensions but HIGH on one, the persona requires Tier 3. This conservative approach prevents governance gaps in the dimension that poses the greatest risk.

**Additional qualifiers** (assessed in the decision tree, not the scoring matrix): financial authority per autonomous decision (>$50K triggers Tier 3) and cross-domain data flows (triggers Tier 3). These qualifiers override the matrix score when applicable.

---

## Tier Descriptions

### Tier 1 -- Discovery / Low Risk

**What it produces:** A lightweight persona contract covering identification, governance, delegation intent, core capabilities, basic data boundaries, authority model, and a sign-off acknowledgement. Produces the same artefact as the "persona candidate card" from Chapter 6A, Section 6.2.2.

**Typical completion time:** 2--4 hours.

**Who participates:** Service Owner and AI RM liaison.

**When to use:** Initial discovery workshops, proof-of-concept explorations, and personas where all risk dimensions score LOW. Suitable for sandbox deployment and Stage 1 (Instrumented Observation) maturity.

**Sections completed:** 1, 2, 3, 4, 5, 6 (partial -- subsections 6.1 and 6.3 only), 8, 18 (lightweight sign-off).

### Tier 2 -- Governance-Ready / Medium Risk

**What it produces:** A production-grade persona contract that adds operational guardrails, service interaction maps, performance measurement, compliance requirements, and risk assessment to the Tier 1 foundation.

**Typical completion time:** 1--2 days.

**Who participates:** Service Owner, AI RM liaison, SOP Owner, and domain subject-matter expert.

**When to use:** Before production deployment; when any risk dimension scores MEDIUM; when the persona progresses beyond Stage 2 (Assisted Execution) maturity; when cross-team coordination is needed.

**Sections completed:** All Tier 1 sections, plus 6 (full), 7, 9, 10, 13, 14.

### Tier 3 -- Full Specification / High Risk

**What it produces:** The complete 19-section persona contract with multi-contributor attribution, lifecycle management, Trusted AI boundary documentation, data supply chain mapping, worked examples, and full compliance sign-off.

**Typical completion time:** 3--5 days of dedicated effort; 2--3 weeks elapsed time (stakeholder scheduling, compliance review cycles).

**Who participates:** Service Owner, AI RM liaison, SOP Owner, domain SME, Compliance Officer, and Data Governance representative.

**When to use:** Regulated industries or high-risk domains; when any risk dimension scores HIGH; when the persona handles cross-domain data flows; when multi-contributor KPI attribution is needed; when the persona has financial authority exceeding $50K per autonomous decision.

**Sections completed:** All 19 sections.

---

## Worked Examples

### Example 1: Internal Meeting Summariser -- Tier 1

**Persona:** Summarises internal team meetings and distributes action items via Slack.

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Industry Sector | LOW | Internal operations only; no regulatory exposure |
| Data Sensitivity | LOW | Internal meeting notes; no PII or customer data |
| Decision Impact | LOW | Recommendations only; humans review and edit summaries |
| Geography | LOW | Single office location; no cross-border data |

**Additional qualifiers:** No financial authority. Single-domain operation only.

**Result:** All dimensions LOW, no qualifier triggers. **Tier 1 applies.** Complete 8 sections in a single workshop session. Service Owner signs off. Deploy to sandbox within the week.

### Example 2: Customer Order Processing Assistant -- Tier 2

**Persona:** Reviews incoming customer orders, validates stock availability, flags exceptions, and routes orders for fulfilment. Modifies order quantities within approved limits.

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Industry Sector | LOW | General retail; no special regulatory requirements |
| Data Sensitivity | MEDIUM | Customer PII (names, addresses, order history) |
| Decision Impact | MEDIUM | Autonomous order modifications within $5K limit |
| Geography | LOW | Domestic operations only |

**Additional qualifiers:** Financial authority $5K per autonomous decision (below $50K threshold). Single-domain operation.

**Result:** Two dimensions score MEDIUM. No HIGH dimensions, no qualifier triggers. **Tier 2 applies.** Complete 14 sections over 1--2 days. SOP Owner defines operational rules. Compliance reviews PII handling. Deploy after Tier 2 checklist passes.

### Example 3: Regulatory Compliance Assessor -- Tier 3

**Persona:** Evaluates loan applications against regulatory requirements, flags compliance violations, and generates audit-ready assessment reports for financial services.

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Industry Sector | HIGH | Financial services; subject to SOX, Basel III, fair lending laws |
| Data Sensitivity | HIGH | Regulated financial data; applicant PII; credit history |
| Decision Impact | HIGH | Assessment outcomes directly affect loan approval decisions |
| Geography | HIGH | US + EU operations; GDPR, EU AI Act, state-level fair lending |

**Additional qualifiers:** Loan decisions range $10K--$500K per autonomous decision (exceeds $50K threshold). Cross-domain data flows between credit, compliance, and customer services.

**Result:** All four dimensions score HIGH, plus both qualifier triggers fire. **Tier 3 applies.** Complete all 19 sections over 3--5 days. Compliance Officer co-signs delegation contract. Data Governance maps cross-border data flows. External legal review recommended before production.

---

## Progression Path

Personas are not locked into their initial tier. As risk profiles evolve, maturity advances, or business context changes, personas graduate to higher tiers.

### Tier 1 to Tier 2 -- When to Upgrade

Upgrade when any of the following conditions arise:

- **Moving to production.** A Tier 1 persona was sufficient for discovery and sandbox testing, but production deployment requires operational guardrails, performance measures, and compliance review.
- **Risk profile changes.** The persona's scope expands, data sensitivity increases, or decision authority grows beyond the original LOW thresholds.
- **Cross-team integration needed.** The persona begins consuming from or providing to services outside its original domain.
- **Maturity progression.** The persona advances from Stage 1 (Instrumented Observation) to Stage 2 (Assisted Execution) or beyond.

**Action:** Complete Sections 6 (full), 7, 9, 10, 13, and 14. Schedule 1--2 days with expanded participant group.

### Tier 2 to Tier 3 -- When to Upgrade

Upgrade when any of the following conditions arise:

- **Regulatory requirements emerge.** New legislation applies (e.g., EU AI Act classification changes), or the persona enters a regulated market.
- **High-value decisions delegated.** Financial authority exceeds $50K per autonomous decision, or the persona gains authority over irreversible actions.
- **Multi-contributor KPI attribution needed.** The persona shares accountability for a KPI with human teams or other personas, requiring formal attribution methodology.
- **Cross-domain data flows.** The persona becomes a node in the collaborative data supply chain, consuming or producing data across domain boundaries.
- **Lifecycle complexity grows.** The persona requires formal drift detection, retraining schedules, or decommissioning protocols.

**Action:** Complete Sections 11, 12, 15, 16, 17, and 19. Engage Compliance Officer and Data Governance. Schedule 3--5 days.

---

## Cross-References

- **Chapter 6A, Section 6.2.2** -- Minimum Viable Definition: describes the persona candidate card that Tier 1 formalises.
- **Chapter 10, Section 10.4** -- Risk Classification: provides the four-dimensional scoring framework (Industry, Data Sensitivity, Decision Impact, Geography) used in this guide's scoring matrix. The "Highest Factor Wins" rule originates here.
- **Chapter 7** -- AI Resource Management: defines the AI RM lifecycle management responsibilities that govern tier progression and persona graduation.
- **AI Persona Definition Template** (`templates/AI-Persona-Definition-Template.md`) -- The template this guide supports, containing all 19 sections with tier markers.

---

*Use this guide at the start of any AI Persona definition exercise. Revisit the scoring matrix whenever the persona's scope, authority, or operating context changes.*
