# Chapter 2: Defining AI-First Service Oriented Architecture

**Thesis:** Imprecise vocabulary makes governance impossible; this chapter establishes the shared definitions for services, capabilities, actors, and AI Personas that prevent accountability gaps, measurement failures, and regulatory risk.

## Key Concepts

### Why Precise Vocabulary Prevents Governance Failures

When two business units each deploy "customer engagement AI" with different definitions -- one meaning "answer product questions within documented policy" and the other meaning "improve customer satisfaction scores" -- their systems make contradictory decisions about the same customer. The conflict surfaces only after damage occurs. Precise vocabulary eliminates this by defining exactly what each AI Persona means, what authority it has, and where its boundaries lie. When executives ask "who is accountable for this AI's decisions?" the answer must trace to a specific owner, not circular references between IT, business units, and operations.

### Core Definitions Table

The methodology defines eleven key terms that serve as the working glossary for all workshops. A **Service** is the means by which consumer needs meet provider capabilities. A **Capability** is the real-world effect a provider delivers, defined in outcome language. An **Actor** is any party that consumes or provides services -- now including AI Personas alongside humans and systems. The **Level 0 Service Map** shows 4-8 major enterprise services plus AI RM as a shared service. The **Level 1 Service Sheet** drills down into a single Level 0 service showing internal services, actors, and delegation decisions. The **Domain Owner** is a named business leader with decision authority, budget authority, and performance accountability -- one per service, no shared ownership.

### Discoverable Policies: The Architectural Innovation

The core innovation of AI-First SOA is that services (providers) publish operational policies and AI Personas (consumers) query those policies at runtime. This PROVIDER/CONSUMER separation enables three governance outcomes: independent evolution (providers update policies centrally without reconfiguring every consuming AI Persona), accountability clarity (service failures become distinguishable from AI execution failures), and governance transparency (audit trails show which policy versions were active when decisions were made). For example, a Customer Support Service publishes its ticket creation policy; the "Customer Issue Handler" AI Persona discovers and follows the policy at runtime, logging which version it used.

### Persona Contract vs. Operational Policies

Formal delegation requires two complementary artifacts. The **Persona Contract** (WHAT accountability) defines mission, measurable results, guardrails, escalation paths, and telemetry requirements -- the service owner maintains it. **Operational policies** (HOW responsibility) define how services should be invoked: interaction rules, compliance constraints, approval gates, and evidence requirements -- services own and publish these for discoverability. Together they create an accountability boundary: the AI Persona is accountable for achieving delegated outcomes; services are responsible for defining correct interaction patterns.

### Delegation Readiness Assessment

Before adding an AI Persona to any service map, facilitators document the Three Questions of Delegation with quality rubrics. Strong answers are specific: "Approve standard purchase orders under $5,000 where vendor is pre-qualified, budget confirmed, and compliance checks pass." Weak answers are vague: "Help with procurement tasks." Show-stoppers -- inability to name a specific business outcome, accountable owner, or operational controls -- mean the capability must be deferred. Figure 2-2 provides the decision tree for assessing readiness during discovery workshops.

## Key Diagrams

Refer to the full book for:
- **Figure 2-1:** Execution Context With AI Personas -- shows how services connect consumers with providers, with humans, systems, and AI Personas as peer actors, deliberately omitting technical plumbing to maintain business focus
- **Figure 2-2:** AI Persona Delegation Readiness Assessment -- decision tree for workshop use, showing green (strong), orange (weak), and red (show-stopper) paths through the Three Questions of Delegation
- **Figure 2-3A:** Service Publishes HOW, AI Persona Queries -- illustrates the discoverable policy pattern with a concrete customer support example
- **Figure 2-3B:** Ownership Boundaries (Service vs. AI Persona) -- shows blue (service), purple (AI Persona), and orange (policy discovery) ownership zones

## Practitioner Checklist

After reading this chapter, you should be able to:
- [ ] Explain each of the eleven core terms to both executive sponsors and delivery teams
- [ ] Use the Three Questions of Delegation with the quality rubric to assess delegation readiness
- [ ] Distinguish Persona Contracts (WHAT accountability) from operational policies (HOW responsibility)
- [ ] Describe the discoverable policy pattern and why it enables governance at scale
- [ ] Position AI RM correctly as a mandatory shared service at Level 0

## Cross-References

- **Templates:** AI Persona Definition Template, Policy Discovery Worksheet (Appendix G)
- **Appendices:** Appendix A (Historical Context), Appendix E (Worked Examples with workshop-ready materials), Appendix F (Visual Notation Standards), Appendix G (SOP Integration Patterns for reference implementation)
- **Related Chapters:** Chapter 4 (Level 0 workshop techniques), Chapter 6 (Level 1 facilitation and Persona Contract implementation), Chapter 7 (AI RM operating model), Chapter 12 (execution modeling)
