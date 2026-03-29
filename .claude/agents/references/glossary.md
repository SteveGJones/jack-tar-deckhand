# Glossary {.unnumbered}

**Actor**
: Any party that consumes or provides services within the architecture. Actors include humans, systems, and AI Personas. Each actor inherits the same expectations for outcomes and reporting, making AI Personas visible without granting them special status. Defined in Chapter 2.

**AI Dependency Statement**
: A mandatory field in the enhanced service definition template declaring whether a service currently delegates work to an AI Persona, is evaluating candidates, or intentionally excludes AI. This makes delegation decisions explicit and audit-ready. Introduced in Chapter 6.

**AI Persona**
: A formally delegated business responsibility assigned to AI with defined scope, decision authority, performance expectations, and clear accountability. Unlike generic AI tools, an AI Persona operates within explicit boundaries, has a named business owner, and is held to measurable outcomes. The term "Persona" is used deliberately rather than "Agent" to signal formal specification governing delegation. Defined in Chapter 1 and elaborated in Chapter 2.

**AI Persona Contract**
: The formal terms of delegation between a service and an AI Persona. Split into WHAT clauses (intent, guardrails, telemetry) and HOW clauses (operational policies, procedures, constraints). The service owner maintains the contract and updates it as business requirements evolve. Defined in Chapter 2 and detailed in Chapter 6.

**AI Persona Definition Template**
: A 19-section contractual specification used to define each AI Persona comprehensively. Sections include intent and mission, capabilities and limits, data contract, authority model, guardrails, interaction model, required SOPs, telemetry requirements, and ownership. Functions as the instantiation of the Persona Contract. Detailed in Chapter 6.

**AI Resource Management (AI RM)**
: The enterprise capability overseeing AI lifecycle risk and governance, functioning as the "HR of AI." AI RM handles onboarding, verification, guardrails, telemetry, and lifecycle management for every AI Persona. It operates as a mandatory shared service supporting every business domain, providing enterprise-wide consistent management infrastructure. Introduced in Chapter 1 and detailed in Chapter 7.

**Borrowing Agreement**
: A formal arrangement allowing a persona in one service domain to execute an SOP owned by another domain. The borrowing agreement documents the terms of cross-domain SOP usage, including approval from the owning service and Vanilla-Agent validation status. Referenced in Chapters 8 and 9.

**BPMN (Business Process Model and Notation)**
: The standard notation used for documenting service-oriented business processes. In AI-First architecture, BPMN diagrams include AI Persona swimlanes with purple headers, SOP ID callouts, MCP namespace labels, and confidence-based escalation gateways. Used extensively in Chapter 12.

**Capability**
: A real-world effect that a service provider delivers to a consumer, defined in outcome language independent of implementation. AI Personas help realize capabilities but never replace the capability definition itself. The key test is whether it can be stated without naming a specific technology. Defined in Chapter 2.

**Change Advisory Circle**
: A lightweight decision forum convened when changes cross domain boundaries, such as cross-domain SOP dependencies or new value exchanges between Level 1 domains. The circle reviews and approves changes that affect multiple service owners, preventing governance fragmentation. Introduced in Chapter 6 and referenced throughout Chapters 8, 9, and 12.

**Classification Lenses**
: Four complementary evaluation frameworks applied to every service and AI Persona pair: Value Classification (economic impact and differentiation), Maturity Classification (autonomy level and progression thresholds), Delivery Classification (requirements clarity and release complexity), and Risk Classification (regulatory, safety, and reputational constraints). Defined in Chapter 10.

**Collaborative Data Supply Chain**
: A modeling approach treating humans, systems, and AI Personas as nodes in data flows with explicit data contracts. Maps data lineage, freshness, and entitlement guardrails for every SOP dependency, ensuring data quality is known before processes execute. Detailed in Appendix B and referenced in Chapter 12.

**Collaborative Workspace**
: A designated repository (digital or physical) for architecture artifacts requiring multi-stakeholder input. Includes Level 0 maps, Level 1 drill-downs, AI Persona Contract drafts, and operational policy backlogs. Access is granted to Domain Owners, AI RM, strategy leads, and facilitators to prevent shadow architecture. Defined in Chapter 5.

**COST_IMPACT**
: A Tier 2 measure type that quantifies the negative financial consequence of an activity, issue, or risk. Used to translate KPI outcomes into monetary terms showing costs incurred or costs avoided. Defined in Appendix H.

**Cross-Domain SOP Register**
: A governance artifact documenting every instance where an SOP owned by one domain is invoked by another service or persona. Records the borrowing service, dependency ID, Vanilla-Agent status, and approval chain. Maintained alongside the dependency register to support Change Advisory Circle reviews. Introduced in Chapter 8.

**DATA_QUALITY_ISSUE_IMPACT**
: A Tier 5 measure type that assesses the operational or financial impact of poor data quality. Helps prioritize data remediation by quantifying consequences such as wasted marketing spend from inaccurate records or flawed AI decisions from missing input data. Defined in Appendix H.

**Delegation Canvas**
: A one-page contract specifying what business outcomes are being delegated to AI, which decisions the AI can make autonomously, and how success will be measured. Forces the same clarity required when delegating to a human employee: scope, performance expectations, escalation triggers, and accountability. Introduced in Chapter 3.

**Delegation Package**
: The complete contractual pairing of a Persona Contract (defining WHAT: mission, guardrails, telemetry, escalation, owner) and operational policies (defining HOW: procedures, constraints, evidence requirements, validation patterns). AI Personas discover operational policies at runtime rather than embedding static rules. Defined in Chapter 5.

**Delivery Classification**
: One of the four classification lenses evaluating how clear requirements are, how mature the design is, and how complex the release will be. Used to sequence the realization backlog intelligently, distinguishing ready-to-deploy personas from those needing further definition. Defined in Chapter 10.

**Dependency Register**
: A comprehensive record of every data flow and service dependency across the architecture, each documented with a unique ID (e.g., DEP-QIA-SCADA-01). Each entry specifies provider service, consumer persona, data format, SLA requirements, and fallback behavior. Feeds directly into the realization backlog. Introduced in Chapter 8.

**Direct Measure**
: A metric that an AI Persona or service actor can change within their delegated authority, that responds within the same time horizon as the actor's decisions, and for which the causal mechanism is clear. Distinguished from indirect measures (which the actor merely influences) using a three-test checklist: Authority, Horizon, and Causality. Defined in Chapter 11.

**Discoverable Policies**
: The architectural innovation whereby services (providers) publish operational policies and AI Personas (consumers) query those policies at runtime rather than embedding static rules. This PROVIDER/CONSUMER separation enables independent evolution, accountability clarity, and audit transparency. Introduced in Chapter 2.

**Domain Owner**
: A named business leader with decision authority over service outcomes. The Domain Owner delegates work within the service boundary (including to AI Personas), retains accountability for all outcomes, approves Persona Contracts, maintains the policy inventory, and decides trade-offs between service quality, cost, and risk. Must have budget authority, performance accountability, and organizational authority. Defined in Chapter 2.

**Escalation Tiers**
: A three-tier classification system for AI incidents based on business severity and required response speed. Tier 1 (Routine) handles edge cases within four hours. Tier 2 (Boundary Breach) addresses scope exceedance within one hour. Tier 3 (Systemic Risk) demands 15-minute executive response for sustained drift, security violations, or compliance breaches. Defined in Chapter 7.

**Execution Context**
: The mechanism enabling provider/consumer communication, such as APIs, events, or prompt interfaces. Deliberately kept invisible at the service architecture level and referenced only when it affects delegation contracts or guardrails. Defined in Chapter 2.

**FINANCIAL_METRIC**
: A Tier 1 measure type that tracks financial health and performance, often tied to accounting principles. Stands alongside OBJECTIVE as a top-tier strategic goal. Examples include Net Profit Margin and Return on Investment. Defined in Appendix H.

**Five-Tier Measurement Framework (5-Tier)**
: A hierarchical measurement structure providing accountability lineage from daily operations to business value. Tier 1 covers Strategic Direction (Objectives, Financial Metrics), Tier 2 covers Performance and Outcome (Key Results, KPIs, Value Contribution, Cost Impact), Tier 3 covers Experiential and Operational measures (XLA, SLA), Tier 4 covers Actionable Inputs (Leading Indicators, Value Levers), and Tier 5 covers Contextual Factors (Risk Level, Data Quality). Defined in Chapter 11.

**Four-Lane Realization Backlog**
: See Realization Backlog.

**Guardrails**
: Authorization boundaries preventing AI from accessing unauthorized data or making unapproved decisions. Analogous to spending limits on corporate credit cards, guardrails allow AI to operate freely within approved boundaries while escalating to human judgment when approaching limits. Technical controls enforce business policies regardless of conditions. Referenced throughout Chapters 6, 7, and 9.

**Heartbeat Reviews**
: Periodic architecture reviews maintaining governance currency. Level 0 reviews occur annually; Level 1 and deeper reviews occur quarterly. AI-first additions include reviewing AI Persona contracts when objectives change, new data enters scope, or AI RM updates enterprise guardrails. Defined in Chapter 5.

**Invoked Authority**
: An authorization model where an AI Persona analyzes and recommends but requires explicit human approval before executing decisions. Appropriate for high-risk, high-value, or judgment-intensive tasks. The human remains accountable for the final decision while the AI provides analysis and evidence. Defined in Chapter 5.

**KEY_RESULT**
: A Tier 2 measure type that provides a quantitative outcome measuring progress toward an Objective. Makes objectives measurable and verifiable with specific targets. Example: "Increase shelf availability to 98.5%." Defined in Appendix H.

**Kill Switch**
: An emergency shutdown procedure for an AI Persona that halts its autonomous operations immediately when triggered. Required as part of the AI Persona definition for risk management. May be invoked when Tier 5 risk thresholds are exceeded or when regulatory exposure demands immediate cessation. Referenced in the AI Persona Definition Template.

**KPI Council**
: A governance forum that convenes when measurement disputes cross tiers or require multi-contributor attribution resolution. Operates on a monthly cadence for routine reviews but can be assembled within 24 hours for attribution conflicts blocking funding decisions exceeding $500K. Defined in Chapter 11.

**KPI_OUTCOME**
: A Tier 2 measure type representing a Key Performance Indicator that measures a business result or historical output. Acts as a lagging indicator showing whether a desired outcome was achieved. Multiple KPI_OUTCOMES can roll up into a single KEY_RESULT. Defined in Appendix H.

**LEADING_INDICATOR**
: A Tier 4 measure type that provides predictive, input-focused measurement suggesting future results. Measures activities that can be influenced to affect a future KPI_OUTCOME. Serves as the primary tool for proactive management of AI Persona performance. Defined in Appendix H.

**Level 0 Service Map**
: The enterprise-wide view capturing 4-8 major business services plus their interactions, providing a picture that leadership can digest in minutes. In AI-first architecture, includes AI Persona candidate markers and AI RM as a mandatory shared service from the outset. Created during 1-2 half-day workshops. Defined in Chapter 2 and Chapter 5.

**Level 1 Service Sheet**
: A drill-down view for a single Level 0 service showing 5-9 internal sub-services and their actors. Captures persona delegation decisions, contracts, and dependencies per service. Created during 2-3 half-day workshops per service domain. Defined in Chapter 2 and Chapter 5.

**Level N**
: Continued drill-down beyond Level 1 as needed until the service owner can act on the definition. Decomposition continues only when the next decision requires more clarity about "what" or "who," not "how." Levels stop when further granularity would describe implementation rather than business capability. Defined in Chapter 5.

**Maturity Classification**
: One of the four classification lenses evaluating how autonomous an AI Persona currently is and what thresholds it must cross before gaining additional decision authority. Governs stage-gated progression from experimental to fully autonomous operation. Defined in Chapter 10.

**MCP Server (Model Context Protocol Server)**
: A technical implementation of the policy repository concept, providing the runtime interface where AI Personas discover and invoke Standard Operating Procedures. Each MCP server is domain-owned (not centrally operated) and follows the "One Server, One Owner" principle. AI RM governs standards and validation gates but does not operate individual MCP servers. Defined in Chapter 5 and detailed in Chapters 9 and 12.

**Measurement Blueprint**
: A reusable governance artifact documenting the complete measurement lineage for an AI Persona or service. Includes mandate recap, primary direct measure with formula and telemetry source, supporting measures (XLA/SLA/leading indicators), volume and relationship metrics, and context and attribution methodology. Must be completed before production deployment. Defined in Chapter 11.

**Model Context Protocol (MCP)**
: An open standard supported by major cloud providers (AWS, Microsoft Azure, Google Cloud, SAP) that provides a uniform interface for invoking SOPs. Paired with SOPs, MCP enables consistency (same verb and payload regardless of channel), auditability (SOP YAML documents ownership and execution), and velocity (teams reuse SOPs across personas without re-engineering guardrails). Detailed in Chapter 9 and Appendix G.

**OBJECTIVE**
: A Tier 1 measure type providing a high-level, qualitative goal describing what the organization or team wants to achieve. Sets direction and answers "What are we trying to accomplish?" Business Owners own Tier 1 Objectives; AI Personas inherit them but are never the sole accountability. Defined in Appendix H.

**One Server, One Owner**
: The governance doctrine stating that every SOP runs on exactly one MCP server owned by a named domain. Only the owning service can approve changes to its SOPs, though borrowing services may invoke them through formal cross-domain agreements. Prevents governance fragmentation and ensures clear accountability for procedural accuracy. Established in Chapter 6 and enforced throughout Chapters 9 and 12.

**Operational Policy**
: Procedural instructions for executing a capability, published by provider services through discoverable interfaces for runtime consumption by AI Personas and other consumers. Services own and maintain their operational policies. Represents the HOW half of the Delegation Package. Defined in Chapter 5.

**Persona Candidate Card**
: A lightweight version of the full AI Persona Definition Template captured during discovery workshops. Contains intent, proposed capabilities, owning service, and preliminary answers to the Three Questions of Delegation. Cards graduate into full contracts within two weeks post-event after validation by the service owner, AI RM, and data stewards. Introduced in Chapter 6.

**Persona Inflation**
: An anti-pattern where organizations create AI Personas for every task simply because the technology exists, resulting in unnecessary complexity and governance overhead. The Service-to-Persona Decision Tree prevents this by requiring that delegation candidates demonstrate need for adaptive judgment, conversational ability, or large-scale pattern recognition. Identified in Chapter 6.

**Persona Lifecycle**
: The six-stage governance journey for every AI Persona: Intake and Verification, Guardrail Configuration, Procedural Infrastructure Deployment, Performance Baseline, Operational Onboarding, and Ongoing Governance. Each stage has defined governance gates managed by AI RM. Mirrors employee lifecycle management. Defined in Chapter 7.

**Policy Repository**
: A governance-controlled source publishing operational policies for discovery by consuming actors. Each service domain operates its own repository as a vertical, domain-owned capability. Services own and maintain their repositories; consumers query for current policies at runtime. One repository per service boundary with clear ownership. Defined in Chapter 5.

**Pre-Delegation Suitability Filters**
: Three screening criteria applied before the formal Three Questions of Delegation: (1) Can this task be codified into a repeatable procedure? (2) Can the outcome be measured and verified? (3) Does the task require uniquely human judgment, empathy, or creativity? Only candidates clearing all three filters proceed to formal delegation. Defined in Chapter 7.

**Procedural Validation**
: Verification that operational policies are clear, complete, and achievable by consuming actors. During architecture definition, facilitators assess policy clarity through manual review. Organizations with AI infrastructure may automate validation using Vanilla-Agent Tests. Manual validation suffices for workshops; automation applies during implementation. Defined in Chapter 5.

**Provider/Consumer Separation**
: The architectural principle whereby providers publish operational policies and consumers discover them at runtime, enabling independent evolution. Providers update policies centrally without reconfiguring every consuming AI Persona. Consumers adapt immediately to policy updates without retraining or redeployment. Foundational to the methodology's approach to governance. Established in Chapter 2 and Chapter 6.

**RACI Matrix**
: A responsibility assignment framework (Responsible, Accountable, Consulted, Informed) extended in AI-first architecture to include AI Personas as Responsible parties while humans remain Accountable. Used to document service-actor assignments and clarify roles across human teams, systems, and AI Personas. Referenced throughout Chapters 1, 7, and 9.

**Readiness Scorecard**
: A green/yellow/red assessment tracking deployment prerequisites for each AI Persona. Evaluates data quality gates, service availability, governance approvals, and stakeholder training. Yellow flags trigger work items in the realization backlog; red flags block deployment. Feeds directly into Chapter 9 backlog prioritization. Introduced in Chapter 8.

**Realization Backlog**
: A four-lane delivery structure converting architectural artifacts into governed work packages. The four lanes are: Persona Enablement (finalize delegation, configure telemetry), SOP and MCP Deployment (build SOPs, deploy to servers, validate), Integration and Orchestration (build APIs, configure dependencies, establish fallbacks), and Human Enablement (training, communication, RACI updates). Treated as a living artifact updated whenever personas or SOPs change. Defined in Chapter 9.

**Risk Classification**
: One of the four classification lenses evaluating regulatory, safety, and reputational factors constraining AI Persona deployment. Uses three tiers: Tier 1 (Low risk, lightweight governance), Tier 2 (Medium risk, standard controls), and Tier 3 (High risk, based on data sensitivity, decision authority, and regulatory exposure, requiring full governance). Determines audit-defensible control levels. Defined in Chapter 10.

**RISK_LEVEL**
: A Tier 5 measure type providing qualitative or quantitative assessment of a potential threat, defined by its likelihood and potential impact. Monitored alongside operational dashboards to explain unexpected changes in higher-tier metrics. Defined in Appendix H.

**Service**
: The means by which consumer needs meet provider capabilities, described in business value terms rather than technology terms. Services represent "what the business does" and are the fundamental organizing unit of the architecture. AI Personas can execute service capabilities within business-defined boundaries. Defined in Chapter 2.

**Service Architecture Heatmap**
: A visual artifact overlaying value classification, AI Persona indicators, and readiness badges onto the service map. Each service/persona pair appears as a colored tile showing investment priority and deployment status. Published alongside the realization backlog to keep prioritization evidence next to the delivery plan. Introduced in Chapter 10.

**Service Definition Template**
: The foundational template for documenting a business service, including service name, business owner, mission, actors, capabilities, preconditions, postconditions, and invariants. The AI-first enhancement adds three permanent fields: AI dependency statement, persona contract reference, and AI RM interface. Defined in Chapter 6.

**Service Owner**
: See Domain Owner. The terms are used interchangeably to refer to the named business leader accountable for all outcomes of a service, including outcomes produced by AI Personas operating within that service.

**Shadow AI**
: AI systems deployed without formal approval, documentation, or oversight. Creates accountability vacuums, redundant spending, and compliance exposure. Shadow AI results from the absence of enterprise visibility into AI deployments, allowing teams to independently build similar capabilities without coordination. AI RM and the methodology's governance framework are designed to prevent and remediate Shadow AI. Referenced in Chapters 3, 4, and 7.

**Shared Service**
: A centrally provided capability consumed by multiple domains. In AI-first architecture, shared services must declare whether they host shared AI Personas or provide governance and telemetry APIs. AI RM is the primary example of a mandatory shared service. Defined in Chapter 2.

**SLA (Service Level Agreement)**
: A Tier 3 measure type representing a commitment regarding the operational performance and reliability of a service. Sets specific technical targets such as uptime, response latency, and throughput thresholds. Used as the primary direct measure when AI Persona output triggers system-to-system actions rather than human consumption. Defined in Appendix H.

**SOP (Standard Operating Procedure)**
: Machine-readable, step-by-step instructions governing AI decisions, formatted so AI Personas can discover and execute them automatically via MCP servers. Each SOP documents trigger conditions, scope (permitted and prohibited actions), data requirements, procedural steps, escalation rules, guardrails, telemetry requirements, and ownership. Distinguished from traditional paper-based manuals. Defined in Chapter 7 and detailed in Chapter 9 and Appendix G.

**SOP Borrowing**
: See Borrowing Agreement.

**SOP Owner**
: The individual responsible for maintaining the procedural accuracy of a specific SOP. Part of the tripartite accountability model alongside the Service Owner (who defines business success criteria) and AI RM (who enforces enterprise standards). The SOP Owner ensures procedures remain current, clear, and validated. Referenced in Chapters 7 and 9.

**Stage 0 (Pre-Work)**
: The preparatory phase before the main discovery event, producing reference material that makes service templates defensible. Stage 0 outputs include AI opportunity scan highlights linked to services, data landscape notes showing feeds and lineage, and regulatory checklist extracts flagging invariants and compliance requirements. Defined in Chapter 6.

**Standing Authority**
: An authorization model where an AI Persona acts independently within defined scope without requiring per-transaction human approval. Appropriate for high-volume, low-risk, well-bounded tasks. Requires strong guardrails, continuous telemetry, and clear escalation protocols. Contrasts with Invoked Authority. Defined in Chapter 5.

**Support Service**
: A service that keeps core domains running, such as HR, Finance, Procurement, and Compliance. In AI-first operations, AI Resource Management is added as a mandatory support service providing shared guardrails, lifecycle controls, and escalation mediation for AI Personas. Defined in Chapter 2 and Chapter 5.

**Technical Service**
: Non-business utility services enabling IT capabilities such as cloud hosting, integration, identity management, and data pipelines. In AI-first architecture, technical services include AI-specific utilities (model hosting, vector storage, prompt gateways, evaluation harnesses), each treated as a service with a contract and owners. Defined in Chapter 5.

**Three Questions of Delegation**
: The formal discovery process anchoring every AI Persona identification decision. (1) What do you want to delegate to AI? (Define the precise service outcome.) (2) How do you want to manage that delegation? (Describe guardrails, telemetry, escalation paths, and name the accountable owner.) (3) How will you include the persona within your team? (Document operating rhythms, shared tools, cross-training.) Show-stopper failures on any question mean the capability is not ready for delegation. Introduced in Chapter 1 and detailed in Chapters 2 and 6.

**Tripartite Accountability**
: The three-owner governance model ensuring no AI Persona operates without clear distributed responsibility. Service Owners define business success criteria and own outcomes, SOP Owners maintain operational procedure accuracy, and AI RM enforces enterprise standards and leads incident response. Prevents governance gaps by separating business accountability, procedural authority, and compliance oversight. Defined in Chapter 7.

**Trusted AI Scope**
: The boundary definition establishing which data, decisions, and interactions fall within an AI Persona's authorized operating envelope. Used to determine compliance requirements and map the persona's access to systems and information. Referenced in Chapter 2 and Appendix M.

**Value Classification**
: One of the four classification lenses evaluating which capabilities protect or create the most economic value and how differentiated the organization's approach is versus competitors. Uses a 2x2 matrix (Value Contribution vs. Strategic Uniqueness) producing four quadrants: Invest to Differentiate, Stabilize and Scale, Optimize Cost, and Selective Innovation. Defined in Chapter 10.

**VALUE_CONTRIBUTION**
: A Tier 2 measure type that quantifies the positive financial or strategic value created by an initiative, feature, or activity. Translates KPI outcomes into monetary terms showing value generated. Example: "Additional revenue generated by the AI-powered recommendation engine." Defined in Appendix H.

**VALUE_LEVER**
: A Tier 4 measure type representing a specific operational or strategic element that the business can adjust to influence outcomes. Acts as a "knob" that can be turned to directly affect a Leading Indicator or KPI Outcome. Only includes elements the service owner can adjust weekly or faster. Defined in Appendix H.

**Vanilla-Agent**
: A baseline, generic AI with no company-specific training used to test whether Standard Operating Procedures are clear enough for correct execution. If a Vanilla-Agent can follow the documented procedure successfully, procedural clarity is proven. Passes or failures are logged and must be completed before AI RM grants production deployment approval. Business value extends beyond AI validation, as procedures passing Vanilla-Agent testing are also clearer for human employees. Defined in Chapter 7 and detailed in Chapter 9.

**Vanilla-Agent Validation**
: The testing process whereby a generic, untrained AI executes an SOP to verify procedural completeness. If the Vanilla-Agent produces correct results following only the written procedure, the SOP is considered procedurally complete. Failures indicate ambiguous or incomplete documentation requiring revision before deployment. Part of the AI RM governance gates. Detailed in Chapter 9 and Appendix G.

**Virtual Service**
: An architectural pattern representing multiple providers behind a single contract or interface. Frequently used to expose ecosystem partners, AI marketplaces, or multi-persona coordination scenarios. Depicted with a hatched pattern for ownership clarity. Distinguished from AI Persona, which is an actor type that can operate within any service. Defined in Chapter 2 and detailed in Chapter 8.

**XLA (Experience Level Agreement)**
: A Tier 3 measure type representing a commitment focused on the quality of the human experience when interacting with a service. Measures satisfaction, effort, and sentiment rather than technical performance. Prioritized as the primary direct measure when an AI Persona's output is consumed by people. Distinguished from SLA, which measures operational performance. Defined in Appendix H.
