# Chapter 10: Classifying Services and AI Personas

**Thesis:** Without a shared classification framework, every service owner argues for top priority and budget debates devolve into politics -- Chapter 10 provides four complementary classification lenses (Value, Maturity, Delivery, Risk) that create a fact-based negotiation surface for sequencing, funding, and governance decisions.

## Key Concepts

### Value-Differentiation Matrix
Every service and AI Persona pair plots onto a 2x2 matrix scoring Value Contribution against Strategic Uniqueness. The four quadrants drive investment strategy: **Invest to Differentiate** (high value, high uniqueness) receives premium resources and dedicated MCP servers; **Stabilize & Scale** (high value, low uniqueness) focuses on reliability with shared SOPs; **Optimize Cost** (low value, low uniqueness) faces build-versus-buy scrutiny; **Selective Innovation** (low value, high uniqueness) runs in sandbox mode measured on learning velocity. In the Oblivion Widgets worked example, the Architecture Board allocated $2.8M across 8 services in 90 minutes -- Autonomous Line Balancing received 43% of budget based on patented algorithms and $2.7M quarterly revenue exposure, while Marketing Intelligence received zero Q1 funding because the team could not cite quantified KPI movement. The discipline is evidence-based: lack of evidence automatically drops a score one notch.

### 4-Stage Maturity Ladder
Not every persona is ready for full autonomy. The maturity ladder governs stage-gated progression: **Stage 1 -- Instrumented Observation** (persona shadows, collects data, takes no action), **Stage 2 -- Assisted Execution** (persona recommends, human approves), **Stage 3 -- Orchestrated Execution** (persona executes defined SOP steps, escalates edge cases), **Stage 4 -- Delegated Autonomy** (persona owns outcomes with kill-switches and guardrails). Each stage has explicit upgrade triggers -- for example, Stage 2 to Stage 3 requires 80% or higher recommendation acceptance rate AND a clean Vanilla-Agent dry run AND risk tier clearance from compliance. The Quality Inspection AI worked example progressed from Stage 1 to Stage 3 over six months: 30 days of stable telemetry qualified it for Stage 2, then 90 days of 87% acceptance rate plus ISO 9001 compliance resolution qualified it for Stage 3 with 10% random human sample review.

### Delivery Readiness Radar
Three axes evaluate backlog sequencing: **Requirements** (clear/emerging/exploratory), **Design** (blueprinted/pattern-based/net-new), and **Delivery** (low/medium/high complexity). Each persona scores 1-5 on each axis, with a minimum viable threshold of 3 on all axes. The radar resolves resource allocation conflicts by surfacing bottlenecks -- in the worked example, Shelf Availability AI (balanced 4/5/4 profile) shipped first while Autonomous Line Balancing (5/5/2 profile) waited six weeks for SCADA sensor upgrades. The key insight: infrastructure gaps block deployment regardless of design maturity. When two personas have equal heatmap scores, the one with clearer requirements and lower delivery complexity moves first.

### 4-Dimensional Risk Classification
Risk classification assesses four dimensions: **Industry** (regulatory sector intensity), **Data Sensitivity** (PII, financial, health data), **Decision Impact** (reversibility and financial exposure), and **Geography** (jurisdictional regulatory requirements like EU AI Act, GDPR, HIPAA). The "highest factor wins" rule assigns governance tiers: ANY dimension scoring HIGH triggers Tier 3 governance (executive review, staged rollout, dual sign-off). Cumulative HIGH dimensions add incremental oversight -- three HIGH dimensions require quarterly external audits plus monthly executive reviews. In the Shelf Availability AI worked example, all dimensions scored MEDIUM except Geography (MEDIUM-HIGH due to EU AI Act), resulting in Tier 2 classification with MCP access logging, transparency pack, retailer joint reviews, and compliance co-owner sign-off.

## Key Diagrams

Refer to the full book for:
- **Figure 10-1:** Value-Differentiation Matrix -- 2x2 quadrant mapping AI Personas by value contribution and strategic uniqueness, with investment strategy per quadrant
- **Figure 10-1 (Maturity Ladder):** Four-level maturity progression from Instrumented Observation through Delegated Autonomy with upgrade triggers at each gate
- **Figure 10-2:** Delivery Readiness Radar -- three-axis scoring model revealing infrastructure bottlenecks that block deployment regardless of design maturity
- **Figure 10-3:** Risk Classification Matrix -- four-factor assessment mapping personas to three governance tiers using the "highest factor wins" rule

## Practitioner Checklist

After reading this chapter, you should be able to:
- [ ] Facilitate a 90-minute value classification workshop using evidence-based scoring (patents, KPI baselines, quarterly revenue exposure) to allocate budget across service portfolio
- [ ] Assess any AI Persona's maturity stage (1-4) and identify the specific upgrade triggers required for promotion to the next stage
- [ ] Score delivery readiness across three axes and sequence backlog based on balanced radar profiles, deploying ready personas while unblocking high-value infrastructure dependencies in parallel
- [ ] Classify risk across four dimensions using the "highest factor wins" rule and assign governance controls with named owners for each required control
- [ ] Confirm every service/persona pair has all four classification profiles (value quadrant, maturity stage, delivery scores, risk tier) before proceeding to Chapter 11 measurement design

## Cross-References

- **Templates:** Value-Differentiation Matrix, Maturity Assessment, Delivery Readiness Radar, Risk Classification Matrix
- **Appendices:** Appendix C (Trusted AI Scope -- high-risk governance), Appendix D (Regulatory Compliance -- risk tier mapping), Appendix E (Worked Examples -- cross-industry benchmarks)
- **Related Chapters:** Builds on Chapter 9 (realization backlog provides the inventory to classify); feeds into Chapter 11 (classifications determine which KPIs to collect first, risk tiers determine real-time vs. batched telemetry)
