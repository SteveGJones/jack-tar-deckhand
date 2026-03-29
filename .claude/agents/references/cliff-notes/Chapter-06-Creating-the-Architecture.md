# Chapter 6: Creating an AI-First Service Architecture

**Thesis:** Chapter 6 turns shared vocabulary into a complete, workshop-ready method that produces Level 0 and Level 1 service maps with AI Personas explicitly identified, governed, and ready for AI RM onboarding.

## Key Concepts

### Provider/Consumer Separation

The foundational architectural principle: providers publish operational policies, consumers discover them at runtime. Third-party AI agents arrive with general capabilities but know nothing about your organization's specific approval thresholds or escalation paths. Rather than embedding policies through static configuration, provider services publish rules through discoverable interfaces. AI Personas query "What are today's approval limits?" dynamically, adapting immediately to policy updates without retraining. This separates agent capabilities (WHAT the AI knows) from organizational policies (HOW your organization wants things done). The Oblivion Widgets Quality Inspection AI, for example, discovers tolerance thresholds from the Quality Control service at runtime rather than carrying hard-coded defect rules.

### The Three Questions of Delegation

The facilitator's core script for exposing delegation opportunities. For every capability discussed during a workshop, the team answers three questions that produce the delegation package:

**Question 1 -- What do you want to delegate to AI?** Focus on outcomes, not tools. Capture the service capability the delegation belongs to. Watch for scope creep. Example: "We want the persona to scan live camera feeds for scratches finer than 0.2mm and queue flagged products for supervisor review."

**Question 2 -- How will you manage that AI?** Clarify ownership, oversight cadence, escalation paths, and telemetry. Link directly to AI RM. Example: "The Manufacturing Excellence VP will review weekly telemetry, while AI RM automates drift detection."

**Question 3 -- How will you include it in your team?** Describe collaboration rituals, choose an integration style (Assistant, Collaborator, or Specialist), and address change management. Example: "Quality Inspection AI posts a shift summary in Teams at 06:00 and escalation playbooks clarify which supervisor picks up a raised alert."

### Service and Persona Templates

The enhanced service definition template retains the classic fields (name, owner, mission, capabilities, actors) and adds three permanent AI-first fields: an AI dependency statement, a persona contract reference, and an AI RM interface naming the responsible steward. The companion AI Persona Definition Template translates the Three Questions into a governance-ready contract covering intent, capabilities, authority model (standing vs. invoked), guardrails, data contract, interaction model, required SOPs, telemetry, and tripartite ownership. During workshops, teams capture lightweight persona candidate cards; these graduate into full contracts within two weeks post-event.

### AI Persona Dual Representation (Section 6.1.7)

When a persona candidate is confirmed during Level 0 or Level 1 discovery, create both canonical model entries immediately: the service entry (WHERE) and the persona entry (WHAT). Deferring either half produces orphan records that block downstream tooling. The Three Questions map directly to both entries: Question 1 answers feed the service description and persona capabilities; Question 2 answers feed the authority model, SOP references, and oversight fields; Question 3 answers feed the interaction model and integration style on both sides. Practitioners may arrive from either direction -- service-first ("we need a quality inspection capability") or delegation-first ("we want to delegate defect detection to AI"). Both doors are valid; whichever door you enter, the facilitator ensures the other half is captured before the session closes. The `canonical-model-manager` skill enforces pairing: it will not accept a service with `isAIPersona: true` unless a matching `aiPersonas[]` entry exists, and vice versa.

### Stage 0 Readiness and the Discovery Event

Stage 0 is the dress rehearsal lasting 2 to 6 weeks. It produces sponsorship confirmation, stakeholder identification, an AI opportunity assessment, a data landscape map, a regulatory checklist, and an SOP baseline with owner roster. The discovery event runs 1 to 3 days with co-location bias. The Oblivion Widgets enterprise event followed a three-day agenda: Day 1 produced the draft Level 0 map; Day 2 refined Level 0 and ran Level 1 breakouts for top services; Day 3 focused on the VMI project and produced a persona prioritization list. Braided facilitation keeps WHAT (service definitions) and HOW (SOP requirements) synchronized through dual capture boards, with facilitators toggling between tracks every 3 to 7 minutes.

### Level 0 and Level 1 Construction

Level 0 follows a four-step cadence: define services (WHAT), add actors including persona candidates (WHO), map interactions and value exchanges (WHY), and flesh out templates with SOP references. The Oblivion Widgets Level 0 produced five customer-facing services plus support services including AI RM, with three persona candidates identified. Level 1 drill-downs follow four principles: only drill when ownership decisions require more detail, keep personas within their owner's service, document the SOP path for every persona, and depict external services with dashed borders. The Manufacturing Level 1 breakout decomposed into Production Planning, Quality Control, Maintenance, and other sub-services, with a 90-minute walkthrough capturing complete SOP summaries and validation scenarios.

### Persona Workshops and Cross-Domain Governance

Post-event persona definition workshops run 2 to 3 hours, converting candidate cards into full templates and matching SOP summaries. The output is a validated delegation package containing the persona contract, SOP summary with YAML snippet, updated service definition, governance checklist, and decision log. When a persona borrows an SOP from a different domain, a Change Advisory Circle convenes -- a 60-minute lightweight decision forum with consumer and provider service owners, SOP owner, AI RM steward, and facilitator. Every approved cross-domain borrowing is logged in the Cross-Domain SOP Register tracking consumer persona, provider SOP, interface version, monitoring arrangement, and review cadence.

## Key Diagrams

Refer to the full book for:
- **Figure 6-0:** Provider/Consumer SOP Discovery Patterns -- unified governance and capability portability
- **Figure 6-1:** Service-to-Persona Decision Tree -- prevents persona inflation by filtering for adaptive judgment needs
- **Figure 6-3:** Three-Question Discovery Loop -- the repeating cycle for every capability discussed
- **Figure 6-5:** Braided AI-First Discovery Event Loop -- shows WHAT/HOW facilitation tracks running in parallel
- **Figure 6-7:** Oblivion Widgets Enterprise Level 0 -- the worked example with five customer-facing services and persona annotations
- **Figure 6-8:** VMI Project Level 0 -- demonstrates the same method at project scope

## Practitioner Checklist

After reading this chapter, you should be able to:
- [ ] Explain Provider/Consumer Separation and why AI Personas discover policies at runtime
- [ ] Facilitate the Three Questions of Delegation for any service capability
- [ ] Complete Stage 0 pre-work including the four new AI-first deliverables (AI opportunity assessment, data landscape map, regulatory checklist, SOP baseline)
- [ ] Build a Level 0 map using the What/Who/Why/Flesh-out cadence with persona candidate annotations
- [ ] Run a braided WHAT/HOW facilitation session using dual capture boards
- [ ] Drill down to Level 1 and capture SOP summaries with trigger, policy call, human touchpoints, and validation hooks
- [ ] Convert persona candidate cards into full delegation packages through 2 to 3 hour workshops
- [ ] Convene a Change Advisory Circle when personas borrow SOPs across domain boundaries

## Cross-References

- **Templates:** AI Persona Definition Template, SOP Schema (Appendix G format), Cross-Domain SOP Register, Service Definition Template
- **Appendices:** Appendix E (Worked Examples for additional industries), Appendix F (Visual Notation Standards), Appendix G (SOP Integration Patterns)
- **Related Chapters:** Chapter 5 (provides vocabulary and change governance), Chapter 7 (AI RM operations consuming Chapter 6 outputs), Chapter 8 (completes architecture with virtual services and dependencies), Chapter 9 (Realization Backlog consumes artifacts across four lanes)
