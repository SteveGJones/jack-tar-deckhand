# Chapter 7: AI Resource Management

**Thesis:** Chapter 7 establishes AI Resource Management (AI RM) as the enterprise shared service accountable for the systemic risk, governance, and day-to-day operations of every AI Persona -- the "HR of AI" that makes the digital workforce visible, governable, and systematically scalable.

## Key Concepts

### The AI Governance Gap and Four Forces

Organizations deploy AI Personas without the systematic governance they require for human employees. When a Customer Service AI issues unauthorized refunds, no one owns the failure. Manufacturing deploys Quality Inspection AI without defining what happens when it flags unknown defect types. Multiple business units independently build identical capabilities. AI RM closes this gap by ensuring every persona enters service with defined accountability, operates within verified boundaries, and maintains audit evidence. Four external forces continuously pressure AI governance: model evolution (new foundation model versions alter behavior), regulatory change (EU AI Act, state-level regulations), business strategy shifts (growth-optimized personas misalign with cost-reduction mandates), and technical landscape changes (API deprecations requiring coordinated updates).

### The Eight Capability Clusters

AI RM operates through eight capability clusters. **Onboarding and Verification** validates delegation readiness through a five-stage workflow (handoff, delegation validation, data lineage review, baseline evaluation, go/no-go decision). **Performance Management** detects drift through three layers: statistical drift detection, behavioral anomaly detection, and business outcome monitoring. **FinOps and Capacity Planning** tracks model and runtime costs. **Cyber, Security, and Privacy** applies enterprise guardrails and jailbreak protection. **Red-Teaming and Testing** runs quarterly adversarial drills including prompt injection attacks, data poisoning simulations, escalation bypass attempts, guardrail circumvention, and regulatory compliance stress tests. **Enterprise Guardrails and Policies** publishes standards and escalation procedures. **Observability and Telemetry** maintains centralized logging and audit evidence. **Procedural Infrastructure Management** governs MCP servers, SOP registries, and Vanilla-Agent labs, enforcing the "one server, one owner" principle.

### The Persona Lifecycle (Six Stages)

Every AI Persona progresses through six governance-gated stages: (1) Intake and Verification -- confirm owner, validate intent against service mandate, review data lineage; (2) Guardrail Configuration -- configure monitoring dashboards, link telemetry thresholds, register escalation contacts; (3) Procedural Infrastructure Deployment -- assign MCP server, schedule Vanilla-Agent tests, publish SOPs; (4) Performance Baseline -- capture metrics, set review cadence, attach to KPI hierarchy; (5) Operational Onboarding -- issue persona identity, grant scoped access, enable audit logging; (6) Ongoing Governance -- attend reviews, update maturity status (Exploration, Pilot, Operational, Trusted), trigger quarterly red-team drills. The Quality Inspection AI worked example in Section 7.6.1 demonstrates this flow with concrete artifacts at each stage.

### Tripartite Accountability

Every persona operates under three accountable owners. The **Service Owner** defines business success criteria, budgets improvements, signs contract updates, and leads business remediation during incidents. The **SOP Owner** aligns procedures with service KPIs, budgets SOP tooling and MCP hosting, signs SOP revisions, and executes recovery playbooks. **AI RM** verifies telemetry and Vanilla-Agent coverage, budgets shared infrastructure, issues go/no-go after guardrail checks, and leads technical forensics during incidents. If any column in the accountability table is blank, the persona must stay in the backlog until accountability is assigned.

### Human-AI Collaboration Rules and Escalation Tiers

AI Personas operate autonomously when three conditions are met: bounded mandate (action within defined scope), low consequence threshold (impact below risk classification), and telemetry green (no drift or anomaly alerts). Escalation follows three tiers. **Tier 1 (Routine Variance, 4-hour SLA):** persona encounters an edge case not covered by SOP but within overall mandate -- service owner reviews and updates SOP. **Tier 2 (Boundary Breach, 1-hour SLA):** persona attempts action outside defined scope -- AI RM steward pauses persona and investigates root cause. **Tier 3 (Systemic Risk, 15-minute SLA):** sustained drift, jailbreak attempt, or compliance violation -- persona suspended immediately, AI RM on-call engages executive sponsor. Every persona generates audit evidence tied to four transparency pillars: Identity, Authority, Rationale, and Outcome.

### Two-Tier KPI Framework

Executive dashboards answer strategic questions through five KPIs: AI Risk Exposure Score (percentage of personas with complete governance, target over 95%), Business Value Enabled (personas scaled from pilot to production per quarter), Compliance Readiness (time-to-audit evidence, target under 48 hours), Enterprise Coordination Efficiency (needs met by reuse versus new builds), and Portfolio Health Distribution (balance across Exploration, Pilot, Operational, and Trusted maturity stages). Operational metrics serve as leading indicators: SOP Update Velocity, Vanilla-Agent Pass Rate, Engineering Independence Rate, Guardrail Violation Rate, and Delegation Package Throughput. When executive KPIs decline, operational metrics diagnose root causes.

### Implementation: The 30-Day Pilot and Operating Model

AI RM investment scales across three maturity stages: Pilot (under 10 personas, 2 to 3 FTE, 400K to 600K annually), Scale (10 to 30 personas, 5 to 8 FTE, 800K to 1.3M), and Enterprise (30-plus personas, 10 to 15 FTE, 1.8M to 2.8M). The 30-day pilot follows four weekly phases: Week 1 discovers and prioritizes pilot personas, Week 2 conducts intake interviews revealing governance gaps, Week 3 establishes monitoring baselines and runs Vanilla-Agent validation, Week 4 presents findings and budget request to executive leadership. A worked example for a 25-persona organization shows Year 1 ROI of 51 percent with breakeven at Month 8. Three operating models (Centralized, Hub-and-Spoke, Federated) suit different portfolio scales. The staffing formula is: 1 Lead plus ceiling of persona count divided by 12 Stewards, plus specialists as scale demands.

## Key Diagrams

Refer to the full book for:
- **Figure 7-0:** External Forces Pressuring AI Persona Governance -- four forces requiring coordinated AI RM response
- **Figure 7-1:** AI RM Capability Clusters and Methodology Integration -- eight clusters mapped to chapter interfaces
- **Figure 7-3:** AI Persona Lifecycle Stages and Governance Gates -- six stages with explicit approval requirements
- **Figure 7-4:** Autonomous Operation Boundaries and Escalation Triggers -- three-tier escalation model
- **Figure 7-5:** AI Persona Inventory: The Org Chart for Agents -- enterprise-wide persona visibility
- **Figure 7-6:** Two-Tier KPI Framework: Executive and Operational Metrics -- leading indicators driving strategic outcomes

## Practitioner Checklist

After reading this chapter, you should be able to:
- [ ] Articulate why AI RM is necessary using the four external forces and the governance gap analysis
- [ ] Walk an AI Persona through the six lifecycle stages with governance gates at each transition
- [ ] Apply the tripartite accountability model assigning Service Owner, SOP Owner, and AI RM responsibilities
- [ ] Classify escalation scenarios into the three tiers (Routine Variance, Boundary Breach, Systemic Risk) with correct SLAs
- [ ] Present the five executive KPIs and explain how operational metrics serve as diagnostic leading indicators
- [ ] Execute a 30-day AI RM pilot (discovery, intake, baseline, executive demo)
- [ ] Choose an operating model (Centralized, Hub-and-Spoke, Federated) based on persona portfolio size and organizational maturity
- [ ] Use the staffing formula and complexity multipliers to size an AI RM team

## Cross-References

- **Templates:** AI RM Intake Checklist, AI Persona Template (consuming Chapter 6 outputs), RACI Matrix, Delegation Canvas
- **Appendices:** Appendix D (Risk Classification), Appendix G (SOP Integration Patterns and MCP reference implementation), Appendix H (Vanilla-Agent test methodology)
- **Related Chapters:** Chapter 3 (governance imperatives and delegation loop), Chapter 6 (produces intake artifacts AI RM consumes), Chapter 8 (AI RM appears in support service catalogs), Chapter 9 (realization consumes AI RM readiness signals), Chapter 11 (5-tier measurement framework integrates AI RM KPIs)
