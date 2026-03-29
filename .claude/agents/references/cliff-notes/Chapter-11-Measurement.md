# Chapter 11: Measuring Performance with the 5-Tier Framework

**Thesis:** Without direct measurement discipline, AI Persona budget reviews become political theater where the loudest voice wins funding -- the 5-Tier Measurement Framework creates accountability lineage from daily operational signals to strategic business value, enabling defensible ROI attribution and regulatory compliance.

## Key Concepts

### The 5-Tier Measurement Hierarchy
Twelve measure types organize into five cascading tiers that connect daily work to business outcomes. **Tier 1 -- Strategic Direction** holds OBJECTIVE and FINANCIAL_METRIC types owned by business leaders; AI Personas inherit the objective but never carry sole accountability for financial metrics. **Tier 2 -- Performance & Outcome** holds KEY_RESULT, KPI_OUTCOME, VALUE_CONTRIBUTION, and COST_IMPACT types that quantify success with verifiable targets. **Tier 3 -- Experiential & Operational** holds XLA (experience level agreements capturing human perception) and SLA (service level agreements for operational contracts); these provide fast feedback even when Tier 2 KPIs lag. **Tier 4 -- Actionable Inputs** holds LEADING_INDICATOR and VALUE_LEVER types -- the knobs operators can turn weekly or faster to steer performance. **Tier 5 -- Contextual Factors** holds RISK_LEVEL and DATA_QUALITY_ISSUE_IMPACT types that explain when the environment, not the persona, changed. The hierarchy provides single chain of custody (every measure references its parent tier), dual visibility (Tiers 1-2 confirm impact, Tiers 3-5 provide steering insight), and shared vocabulary across functions.

### Direct Measure Selection
The critical discipline separating effective measurement from attribution disputes. A measure qualifies as "direct" only if it passes three tests: **Authority** (can the actor change this measure within their delegated scope?), **Horizon** (does the measure respond within the same time frame as the actor's decisions?), and **Causality** (can we describe the causal mechanism?). If any test fails, the metric is indirect and requires attribution analysis. In the Shelf Availability AI worked example, the Product Lead initially proposed quarterly revenue as the primary KPI -- but revenue has 47 contributing factors, lags 90 days behind hourly AI decisions, and involves pricing teams outside AI authority. Applying the three-test checklist redirected the primary KPI to "% shelf availability for top 200 SKUs" (hourly, 98.5% target), which the AI directly controls. Revenue became a Tier 1 Objective with quarterly attribution. The CFO approved $0.8M funding within 48 hours because measurement was defensible.

### Healthcare Claims Triage Walkthrough
The tier walkthrough demonstrates cross-industry applicability. Tier 1 Objective: "Accelerate clean claim payout while controlling leakage." Tier 2 KPI: "% of clean claims auto-approved within 24 hours" (target 85%, monthly). Tier 3 SLA: "AI decision latency under 3 minutes" (real-time); XLA: "Adjusters rate AI explanations 4/5 or higher" (weekly). Tier 4 Leading Indicator: "Model confidence score at or above 0.92 for top 70% claims" (daily). Tier 5 Context: "Fraud flag false-positive rate under 3%" (hourly). Teams swap their own metrics into this structure to create ready-to-run lineage connecting daily operations to strategic outcomes.

### Multi-Contributor KPI Attribution
Most Tier 2 KPIs involve multiple contributors -- AI Personas, operations teams, store staff. The methodology provides throughput-weighted attribution to resolve disputes with math, not politics. In the worked example, Shelf Availability achieved 96.2% (target 98.5%) with $2.1M revenue impact. Attribution calculation: AI contributed 39% ($819K) based on 11,703 acknowledged alerts at 92% conversion quality; Merchandising Operations contributed 32% ($672K) based on 9,163 orders at 97% fulfillment; Store Teams contributed 29% ($609K) based on 8,870 restocks at 92% confirmation rate. The KPI Council convened, applied Figure 11-2's throughput-weighted methodology, and resolved the dispute in 90 minutes. The CFO approved Phase 2 funding because attribution math was auditable and transparent.

### Governance Escalation Model
Each tier maps to a specific governance forum and escalation cadence. Tier 5 issues surface in daily risk syncs. Tier 4 trends trigger weekly operations stand-ups. Tier 3 SLA/XLA breaches escalate to bi-weekly service reviews. Tier 2 variance above 5 points convenes the monthly KPI Council. Tier 1 objective drift exceeding 10% triggers quarterly Portfolio Council review. The 4-stage escalation workflow (Detect, Diagnose, Decide, Document) ensures issues route to the right decision authority: single-tier problems stay with the Ops Lead; cross-tier issues escalate to KPI Council within 24 hours; critical risks invoke kill-switches with executive sponsor notification.

## Key Diagrams

Refer to the full book for:
- **Figure 11-1:** Five-Tier Measurement Hierarchy -- strategic outcomes (Tiers 1-2) cascading to operational levers (Tiers 3-5), showing how daily work connects to business value
- **Figure 11-2:** Attribution Tree with Weighted Contributors -- multi-contributor KPI breakdown showing volume, quality factors, and dollar attribution per actor
- **Figure 11-3:** Direct vs. Indirect Measure Decision Tree -- three-test validation (Authority, Horizon, Causality) that separates controllable metrics from influenced ones
- **Figure 11-4:** Governance Escalation Flow -- 4-stage workflow (Detect, Diagnose, Decide, Document) with tier-based routing to appropriate governance forums

## Practitioner Checklist

After reading this chapter, you should be able to:
- [ ] Place any metric into its correct tier (1-5) and identify its measure type from the 12 standardized types (OBJECTIVE, FINANCIAL_METRIC, KEY_RESULT, KPI_OUTCOME, VALUE_CONTRIBUTION, COST_IMPACT, XLA, SLA, LEADING_INDICATOR, VALUE_LEVER, RISK_LEVEL, DATA_QUALITY_ISSUE_IMPACT)
- [ ] Apply the three-test checklist (Authority, Horizon, Causality) to validate whether a proposed KPI is a direct measure for a given AI Persona
- [ ] Complete a Measurement Blueprint for any AI Persona covering mandate recap, primary direct measure, supporting measures, volume/relationship metrics, and attribution methodology
- [ ] Calculate throughput-weighted attribution across multiple contributors using volume and quality factors to resolve KPI disputes
- [ ] Define governance escalation paths with clear ownership by tier, including triggers and response timeframes
- [ ] Balance XLA and SLA selection based on whether persona outputs serve humans (XLA primary) or trigger system-to-system actions (SLA primary)

## Cross-References

- **Templates:** Measurement Blueprint Template, Adoption Scorecard, Measurement Readiness Checklist
- **Appendices:** Appendix H (Measure Type Definitions -- all 12 types with formulas and attribution methodologies), Appendix E (Worked Examples -- cross-industry metric patterns), Appendix L (Telemetry Design Standards)
- **Related Chapters:** Builds on Chapter 10 (classifications determine which KPIs to collect and telemetry cadence); feeds into Chapter 12 (measurement proves what AI achieved, process models prove AI operated within authorized boundaries)
