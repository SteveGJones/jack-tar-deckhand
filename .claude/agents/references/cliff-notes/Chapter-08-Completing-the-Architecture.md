# Chapter 8: Completing the AI-First Service Architecture

**Thesis:** Chapter 8 extends the Level 0 and Level 1 blueprints with virtual services, support layers, persona dependency registers, and orchestration constraints so the architecture is complete and ready for Chapter 9 realization.

## Key Concepts

### Virtual Services

Virtual services are facades that stitch together existing business services and AI Personas to deliver a coherent experience. They do not implement new business logic; instead they coordinate already-defined services. At Oblivion Widgets, the Customer Order Status Portal virtual service orchestrates Manufacturing (production schedule), Logistics and Warehouse (delivery ETA), and Aftermarket and Service (warranty status) without duplicating their logic. Virtual services inherit governance from the business service that owns the experience. They reference AI Personas but never own them. In diagrams, virtual services use hatched styling per Appendix F so facilitators immediately see that no new Level 0 or Level 1 service has been added. The VMI programme is similarly captured as a virtual service under Sales and Marketing ownership rather than creating a new Level 0 service.

### Support and Shared Service Classification

Chapter 8 extends the architecture with three supporting layers. **Technical Support Services** cover platforms, data fabrics, and infrastructure capabilities (sensor meshes, AI platform operations, integration fabrics). **Associated Support Services** cover HR, Finance, Legal, and other enabling functions that keep the organization running -- they remind teams which corporate functions must be engaged when realizing a service. **AI RM** appears as a support service connected to every persona cluster, linking to the contract IDs managed in the AI RM platform. For shared services, the methodology differentiates three patterns using KPI analysis: **Common Base** (same conceptual frame but different objectives -- capture as separate services with shared data models), **Shared** (same mission and KPIs across domains -- declare a single service with one owner), and **Apparently Shared** (business wants separation despite functional alignment -- keep separate but annotate reusable AI assets). The Oblivion Widgets facilitator tested defect classification: Manufacturing measures production yield while Aftermarket measures warranty claim accuracy. Different KPIs meant Common Base, not Shared.

### AI Persona Dependency Register

With service maps complete, Chapter 8 makes persona-to-persona and persona-to-service dependencies explicit. The dependency register captures each persona's inbound and outbound data flows, decision rights, and escalation paths. Each dependency receives a unique ID (e.g., DEP-QI-SUP-01) logged in the AI RM inventory. The Quality Inspection AI, for example, shares telemetry with Supply Assurance AI via event schema QI-SUP-01, while Demand Forecasting AI aligns with Marketing Promotion AI through API DF-MP-02. The companion Cross-Domain SOP Register pairs with the dependency register, tracking which personas rely on another domain's procedures -- capturing the SOP ID, owning service, borrowing persona, MCP server, and Vanilla-Agent validation status. This register enforces the "one server, one owner" doctrine: only the owning service approves changes.

### Collaboration Archetypes

Three archetypes govern cross-domain AI interaction patterns. **Observer:** the persona only consumes telemetry and never sends commands -- for example, Compliance Sentinel AI reads Customer Insight Portal events to detect risky offers. **Collaborator:** personas share decisions bidirectionally within a single RACI -- Demand Forecasting AI and Marketing Promotion AI decide which bundles to push based on real-time stock. **Co-owner:** personas represent a shared or jointly funded capability with a dual-governance board. Higher collaboration demands stronger governance: Observers need only log-only integration with AI RM drift monitoring, Collaborators require shared KPI lists and monthly dependency reviews, and Co-owners require a joint AI RM board with a formal change authority matrix.

### Orchestration Constraints (No Super-Orchestrators)

The methodology explicitly prevents "super-orchestrator" anti-patterns where a single persona begins calling other personas directly without a supervising service. Virtual services may orchestrate flows, but ownership stays with the underlying business service and AI RM. RACI checklists assign Responsible (service owner invoking the persona), Accountable (business owner confirmed during Chapter 6 workshops), Consulted (AI RM duty officer plus partner service owners), and Informed (Compliance, Legal, and affected Level 0 leaders). Three anti-patterns to watch for: rogue orchestrators (reassign to a virtual or shared service), unreviewed data loops (register the dependency and update persona templates), and opaque partner personas (capture minimal contract with a secure annex).

## Key Diagrams

Refer to the full book for:
- **Figure 8-1:** Virtual Service Facade -- the Customer Insight Portal orchestrating services without owning business logic
- **Figure 8-2:** Support Service Classification -- mind map grouping technical, associated, and AI RM capabilities
- **Figure 8-3:** Persona Dependency Map -- Quality Inspection AI, Supply Assurance AI, and Logistics Partner AI dependency flows
- **Figure 8-4:** Collaboration Pattern Spectrum -- Observer, Collaborator, Co-owner progression with governance requirements
- **Figure 8-5:** Orchestration Guardrails -- sequence showing virtual service coordinating personas while AI RM logs every decision
- **Figure 8-6:** "You Are Here" Roadmap -- Chapter 8 positioned between AI RM definition and realization

## Practitioner Checklist

After reading this chapter, you should be able to:
- [ ] Identify when to create a virtual service versus a new Level 0 or Level 1 service
- [ ] Classify shared services as Common Base, Shared, or Apparently Shared using KPI analysis
- [ ] Map persona dependencies using the dependency register with unique IDs, data contracts, and escalation owners
- [ ] Maintain a Cross-Domain SOP Register tracking every persona that borrows another domain's procedures
- [ ] Select the correct collaboration archetype (Observer, Collaborator, Co-owner) based on interaction requirements
- [ ] Prevent super-orchestrator anti-patterns by enforcing RACI checklists and service-level ownership
- [ ] Complete the five-step dependency close-out before leaving the workshop (assign IDs, update contracts, notify AI RM, capture backlog items, schedule measurement review)
- [ ] Pass the Chapter 8 Readiness Scorecard with green rows for every persona/SOP pair before advancing to Chapter 9

## Cross-References

- **Templates:** Dependency Register Template, Cross-Domain SOP Register, RACI Checklist, Readiness Scorecard
- **Appendices:** Appendix F (Visual Notation Standards for virtual services, external services, and persona icons), Appendix G (SOP Integration Patterns and MCP contract structure)
- **Related Chapters:** Chapter 6 (produces Level 0/1 blueprints and persona candidate cards that Chapter 8 extends), Chapter 7 (AI RM governs every dependency and monitors collaboration patterns), Chapter 9 (consumes the completed architecture through four Realization Backlog lanes), Chapter 10 (measurement cadence for dependency review checkpoints)
