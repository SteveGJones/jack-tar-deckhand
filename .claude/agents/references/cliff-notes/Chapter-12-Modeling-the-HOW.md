# Chapter 12: Modeling the "HOW" for AI-First Services

**Thesis:** Measurement proves what AI achieved; process modeling proves the AI operated within authorized boundaries -- Chapter 12 provides the blueprinting discipline that transforms informal delegation ("the AI handles customer inquiries") into formal, governed process models documenting service boundaries, owner assignments, and escalation paths.

## Key Concepts

### Three Modeling Lenses
No single modeling style fits every audience. Blend three views depending on who must trust the model: **Business process (BPMN)** explains human-AI handoffs, approvals, and timing -- each AI swimlane references SOP IDs and Vanilla-Agent status. **Software/service blueprint (UML/API)** captures API calls, data objects, and system dependencies -- MCP operations appear as service calls with trace IDs. **Collaborative data supply chain** ensures data lineage, freshness, and entitlement guardrails -- linking to Appendix B tables and the cross-domain SOP register. Start every modeling session by asking "What decision are we enabling?" and "Who has to trust this model?" Those two questions determine how deep each view must go.

### AI Personas in BPMN Swimlanes
BPMN remains the lingua franca for service interactions, but AI Personas now appear as fully fledged actors. Three governance conventions enforce accountability: AI Persona lanes use purple headers with robot icons, SOP version callouts (e.g., `SOP-RMA-Eligibility-02 v1.2.0`), and MCP namespace labels (e.g., `returns-eligibility.mcp`). Personas must nest inside their owning service lane -- never float outside a service boundary. Confidence-based gateways route low-confidence decisions (below 80%) to human review. Dashed connectors mark cross-domain SOP calls, flagging which Change Advisory Circle must review the interaction. Three anti-patterns to avoid: floating personas (outside service lane, ambiguous ownership), overloaded gateways (more than three outbound paths), and silent escalations (missing `log_evidence()` calls).

### The RMA Worked Example
The Return Merchandise Authorization process demonstrates all three modeling lenses applied to one business scenario. In BPMN: Customer Care opens the case (SOP-CCA-01), RMA Eligibility AI checks entitlement, fraud, and hazard flags (SOP-RMA-Eligibility-02 on `returns-eligibility.mcp`), Logistics plans pickup via cross-domain SOP (SOP-RMA-Logistics-04, borrowed through the cross-domain register), and Finance issues the refund with AI-generated exception summaries. In the sequence diagram: the 5-phase SOP invocation pattern (Invocation, Validation, Execution, Evidence Logging, Response) traces every system call with parameter-level precision, propagating a unique trace ID through Order Management, Product Catalog, and Fraud Detection Service. In the data supply chain view: three source systems feed the AI Persona with contractual SLA tags, and two outputs (escalation cases, pickup schedules) flow to downstream consumers with freshness guarantees.

### Component Diagrams and API Catalogs
Component diagrams make "One Server, One Owner" governance visible at a glance by nesting MCP server components inside owning service boundaries with inbound AI Persona consumers, outbound system dependencies, and data store connections. API catalogs distinguish MCP-managed SOP endpoints (governed, Vanilla-Agent validated, version-locked, audit-logged) from legacy REST endpoints (unmanaged, no validation gate, no audit trail). Namespace prefixes (`mcp://` vs. `legacy://`) make governance boundaries visible in developer tooling. When catalogs make governance obvious, developers follow the path of least resistance into compliant integration patterns -- preventing Shadow AI.

### Versioning and Change Management
BPMN diagrams pin to SOP major versions, not patch versions. Three events trigger diagram updates: SOP scope changes (add/remove capability) require diagram major version increment; SOP parameter changes (add/modify interface fields) require minor increment; SOP implementation changes (no interface modification) require no diagram update. A version lock file (`version-manifest.yaml`) stores BPMN-SOP version mappings so CI/CD pipelines detect major version mismatches and block deployment with "Diagram review required" errors. This prevents silent drift where diagrams reference deprecated SOPs.

## Key Diagrams

Refer to the full book for:
- **Figure 12-1:** Process Wheel for MCP+SOP Modeling -- six-segment governance cycle (Discover, Delegate, Model, Implement, Monitor, Improve) showing how SOPs evolve continuously
- **Figure 12-2:** RMA Process BPMN (AI-First Service Pattern) -- governance-ready BPMN demonstrating service containment, cross-domain SOP calls, and confidence-based escalation
- **Figure 12-3:** BPMN Anti-Pattern Gallery -- wrong-vs-right panels showing floating personas, overloaded gateways, and correct service containment
- **Figure 12-4:** RMA Data Supply Chain -- data lineage from source systems through AI Persona to downstream consumers with SLA tags on every flow
- **Figure 12-5:** RMA Eligibility SOP Invocation Sequence -- 5-phase technical message flow (Invocation, Validation, Execution, Evidence Logging, Response) with trace ID propagation
- **Figure 12-6:** MCP Component Architecture -- component diagram documenting MCP server ownership, consumer relationships, and system dependencies

## Practitioner Checklist

After reading this chapter, you should be able to:
- [ ] Select the appropriate modeling lens (BPMN, UML/API, Data Supply Chain) based on audience and governance needs
- [ ] Create a governance-ready BPMN diagram with AI Persona swimlanes nested inside service boundaries, SOP version callouts, MCP namespace labels, and confidence-based escalation gateways
- [ ] Validate any BPMN diagram against the three anti-patterns (floating personas, overloaded gateways, silent escalations)
- [ ] Facilitate a 30-minute process modeling workshop using the structured script (Frame Decision, Swimlane Draft, SOP Annotation, Anti-Pattern Review)
- [ ] Document MCP server architecture using component diagrams that show inbound consumers, outbound dependencies, and data lineage
- [ ] Publish an API catalog distinguishing governed SOP endpoints from legacy endpoints with five governance attributes (Vanilla-Agent status, version lock, owner contact, audit requirement, cross-domain flag)

## Cross-References

- **Templates:** Process Wheel, BPMN Anti-Pattern Checklist, API Catalog Template, Version Manifest
- **Appendices:** Appendix B (Data Supply Chain Governance -- lineage and freshness), Appendix F (Visual Notation Standards -- icon library and conventions), Appendix G (SOP Integration Patterns -- schema, code samples, validation procedures)
- **Related Chapters:** Builds on Chapter 9 (every persona needs an SOP, MCP server, and readiness gate) and Chapter 11 (measurement proves outcomes; modeling proves authorized boundaries); feeds into Chapter 15 (legacy modernization targets emerge from gap analysis between current-state BPMN and AI-First patterns)
