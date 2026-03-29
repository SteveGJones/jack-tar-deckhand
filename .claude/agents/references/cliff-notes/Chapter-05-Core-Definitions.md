# Chapter 5: Core Definitions and Approach

**Thesis:** Chapter 5 establishes the shared vocabulary, workshop disciplines, and change governance rhythms that transform informal AI discussions into governance-ready architecture.

## Key Concepts

### The Level Hierarchy (Level 0 / Level 1 / Level N)

The architecture decomposes the enterprise into nested views. Level 0 captures the 70,000-foot picture -- 4 to 12 major services that leadership can digest in minutes, always including AI RM as a support service. Level 1 breaks each Level 0 service into 5 to 9 sub-services, annotated with known actors including candidate AI Personas. Level N drills further only when the next decision requires more clarity about "what" or "who." At every level, actors are made explicit: human, system, and AI Persona icons appear directly on the map so governance teams can ask the right questions without diving into process diagrams.

### The Delegation Package (WHAT + HOW)

Every AI Persona operates under a Delegation Package consisting of two halves. The Persona Contract (WHAT) defines mission, guardrails, data rules, authority model, and named owner using the 19-section AI Persona Definition Template. Operational Policies (HOW) define the procedures, constraints, and evidence requirements that provider services publish through discoverable interfaces. This separation is critical: providers update policies centrally without reconfiguring consumers, and AI Personas discover current rules at runtime rather than embedding static configurations. Standing Authority permits autonomous action within defined scope; Invoked Authority requires explicit human approval before execution.

### AI Persona Dual Representation

An AI Persona is both a service and a delegated business role. As a service, it has consumers, an API surface, and a position in the architecture hierarchy. As a delegated role, it carries authority, guardrails, SOPs, and tripartite ownership. The canonical model reflects this duality with two entries: a service entry in `services[]` (with `isAIPersona: true`) that records WHERE the persona sits in the architecture, and a matching entry in `aiPersonas[]` that records WHAT is delegated -- the full persona contract. Both entries are created during discovery; the `canonical-model-manager` skill auto-pairs them and keeps references in sync. Practitioners should think of this as the "address" (service entry) and the "delegation contract" (persona entry) -- neither is complete without the other.

### Collaborative Discovery Workshops

AI-first discovery workshops demand 150 to 450 person-hours of executive capacity across 1 to 3 day sessions. This upfront investment prevents 6 to 9 months of retroactive governance cleanup costing 15 to 20 percent of Shadow AI spend. Participants must include decision-makers with commit authority, not note-takers. AI RM representatives attend every session to answer safety and lifecycle questions in real time. The workshop follows a dual-track approach: one track captures Persona Contracts (WHAT), the other captures operational policy requirements (HOW), with Domain Owners and AI RM rotating between tracks.

### The Language Ladder

Facilitators use a structured progression to convert raw stakeholder dialogue into governed persona definitions. The ladder climbs from a customer quote, to a service grouping, to a capability statement, to an actor role, and finally to an AI Persona contract. The key reframe: instead of asking "What does it do?" facilitators open with "What do you want to delegate to it?" This keeps conversations grounded in accountability. Anti-patterns to watch for include process obsession ("then I click..."), technology-first labels ("Salesforce Automation" instead of "Opportunity Management"), persona hype without a service anchor, and invisible AI RM.

### Dual-Track Change Governance

AI Personas drift. Chapter 5 establishes a dual-track change flow. Persona Contract changes -- new personas, material changes to authority or guardrails, cross-boundary interactions -- route through AI RM and the service architecture board. Procedural-only SOP updates follow a lighter path requiring SOP Owner sign-off and validation testing, as long as the Persona Contract stays untouched. Heartbeat reviews follow a regular cadence: Level 0 annually, Level 1 and below quarterly. Major organizational changes (mergers, acquisitions, divestitures) demand a full architecture review including comparison of AI Persona catalogs across organizations.

## Key Diagrams

Refer to the full book for:
- **Figure 5-1:** Level hierarchy with visible actors -- shows how human, system, and AI Persona icons appear at every decomposition level
- **Figure 5-2:** AI-First Discovery Event Loop -- the facilitation flow with explicit AI RM governance checkpoints
- **Figure 5-3:** Dual-Track Change Flow (Persona Contract + Operational Policy) -- the fast lane for policy-only updates alongside the full change board path
- **Figure 5-4:** Language Ladder from Narrative to Persona -- the five-rung progression from raw dialogue to governed persona definition

## Practitioner Checklist

After reading this chapter, you should be able to:
- [ ] Explain the distinction between Level 0, Level 1, and Level N views and when to stop drilling down
- [ ] Articulate the Delegation Package as the pairing of Persona Contract (WHAT) with Operational Policies (HOW)
- [ ] Plan a 1 to 3 day discovery workshop with the right participants, dual-track agenda, and AI RM representation
- [ ] Use the Language Ladder to convert stakeholder dialogue into persona candidate cards
- [ ] Apply dual-track change governance, routing persona contract changes through the architecture board while allowing lightweight SOP updates
- [ ] Verify the four approval gates before Chapter 6 progression: Level 0 validated, AI RM infrastructure confirmed, Persona contracts show accountable owners, operational policy backlog documented

## Cross-References

- **Templates:** AI Persona Definition Template (19 sections), SOP Schema Template
- **Appendices:** Appendix F (Visual Notation Standards), Appendix G (SOP Integration Patterns), Appendix I (Chapter 5 Facilitator Guide with planning guidance, artifact completion standards, and facilitation script library)
- **Related Chapters:** Chapter 4 (establishes top-down discovery), Chapter 6 (applies vocabulary to workshop templates and Level 0/1 creation), Chapter 7 (defines AI RM operations in detail)
