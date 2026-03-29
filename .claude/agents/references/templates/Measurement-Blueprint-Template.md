# Measurement Blueprint Template

Use this template to capture the full lineage, telemetry, and governance required to launch or evolve an AI Persona, human-led service, or shared capability. Complete it collaboratively with the Business Owner, Product Owner, AI Ops Lead, and Risk Steward referenc[Return to Chapter 2](../chapters/Chapter-02-Defining-AI-First-SOA.md) | [See Appendix B (Data Supply Chain)](../appendices/Appendix-B-Data-Supply-Chain-Governance.md) (Collaborative Data Supply Chain).

---

## 1. Mandate Recap
- **Service / Persona Name:**
- **Intent Statement (Tier 1 Objective reference):**
- **Decision Rights & Boundaries:**
- **Authoritative Owner (RACI "Accountable"):**

## 2. Tier Lineage Snapshot
| Tier | Measure Name | Definition & Formula | Target / Range | Data Source | Owner | Review Cadence |
|------|--------------|----------------------|----------------|-------------|-------|----------------|
| T1 Objective | | | | | | |
| T2 KR / KPI | | | | | | |
| T3 XLA / SLA | | | | | | |
| T4 Leading Indicator / Value Lever | | | | | | |
| T5 Context Metric | | | | | | |

## 3. Primary Direct Measure Detail
- **Metric Type (KPI, XLA, SLA, Leading Indicator):**
- **Units & Formula:**
- **Latency & Sampling Interval:**
- **Telemetry Schema / Event Names:**
- **Control Authority (people, AI, automation levers):**
- **Dashboards / Alert Channels:**
- **Definition of Done (what success looks like during review):**

## 4. Supporting Measures & Adoption
| Measure | Tier | Purpose | Thresholds / Escalation | Instrumentation Owner |
|---------|------|---------|-------------------------|-----------------------|
| | | | | |

- **Adoption Scorecard Inputs:** capture usage %, satisfaction, override rates.
- **Relationship Metrics:** specify counterparty, health signal, and remediation forum.

## 5. Volume, Capacity, and Load Shedding
| Metric | Definition | Target Band | Automation / Scaling Trigger | Runbook Link |
|--------|------------|-------------|------------------------------|--------------|

## 6. Context, Risk, and Safeguards
| Risk / DQ Issue | Acceptable Range | Detection Method | Owner | Automated Guardrail | Kill-Switch / Fallback |
|-----------------|------------------|------------------|-------|----------------------|------------------------|

## 7. Attribution & Experiments
- **Contributors & Weights:**
- **Experiment Design:** A/B, multivariate, or counterfactual description.
- **Data Readiness:** minimum sample size, confidence targets, instrumentation gaps.

## 8. Governance & Escalation
| Forum / Ritual | Participants | Cadence | Decisions Made | Inputs (reports, dashboards) |
|----------------|-------------|---------|----------------|------------------------------|

- **Escalation Workflow:** describe triggers, notification path, and expected time-to-mitigation.
- **Sunset / Evolution Criteria:** when the measure or persona is retired or re-scoped.

---

## Example (Retail Availability Persona)

| Section | Sample Content |
|---------|----------------|
| Mandate Recap | Persona: "Shelf Sentinel"; Intent: maintain ≥98.5% shelf availability across top 1,200 SKUs; Decision Rights: demand rebalancing suggestions, emergency transfers; Owner: VP Merchandising Ops. |
| Primary Direct Measure | Metric: Shelf Availability % (Tier 2 KPI); Units: % shelves stocked; Latency: hourly via inventory streaming; Telemetry: `availability_snapshot` event with SKU, store, timestamp, stock_state; Control: AI adjusts transfer queue priority. |
| Supporting Measures | Tier 3 XLA: "Store teams rate AI alerts as ≥4.2/5 helpful"; Tier 4 Leading Indicator: "% alerts acknowledged within 15 min"; Adoption metric: "Human overrides <20%". |
| Volume & Capacity | Throughput: "Alerts per hour"; Trigger: add GPU node if >5k/hr sustained for 4 hrs. |
| Context & Risk | Data risk: "On-hand sensor outage >15 min"; Guardrail: automatically pause store-level recommendations. |
| Attribution | Contributors: AI 30%, Store Ops 40%, Supply Chain 30%; Experiment: staggered roll-out with matched stores; Data readiness: 12 weeks of paired telemetry. |
| Governance | Weekly Operations Council; Monthly KPI Council; Escalation path: AI Ops → Product Lead → Business Owner within 24h. |

Save a copy of this template per AI Persona/service and store it alongside the persona charter in `methodology_draft/templates/instances/` or your team’s chosen repository.
