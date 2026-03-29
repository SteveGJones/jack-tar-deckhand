# AI Persona Definition Template

## Start Here: How Much Documentation Do You Need?

This template supports three levels of rigour, aligned to your persona's risk profile:

- **Tier 1 (2--4 hours):** Low-risk discovery, sandbox deployment -- 8 sections
- **Tier 2 (1--2 days):** Production-ready, medium risk -- 14 sections
- **Tier 3 (3--5 days of effort; 2--3 weeks elapsed):** High-risk, regulated, or cross-domain -- all 19 sections

**Don't know your tier?** Use the **AI Persona Tier Selection Guide** (`templates/AI-Persona-Tier-Selection-Guide.md`). It takes 10 minutes and prevents both under-specification (governance gaps) and over-specification (analysis paralysis).

**Tier 1 -- Discovery / Low Risk (8 sections).** Captures the minimum viable definition needed for initial discovery workshops and low-risk personas where all risk dimensions score LOW. Produces a lightweight persona contract sufficient for sandbox deployment and Stage 1 maturity.

**Tier 2 -- Governance-Ready / Medium Risk (adds 6 sections).** Extends the Tier 1 foundation with operational, measurement, compliance, and risk sections required before production deployment. Apply when any risk dimension scores MEDIUM or the persona moves beyond Stage 2 maturity.

**Tier 3 -- Full Specification / High Risk (adds 5 sections).** Completes the full 19-section template for high-risk, regulated, or cross-domain personas. Required when any risk dimension scores HIGH, the persona handles regulated data, or multi-contributor KPI attribution is needed.

---

## Instructions

This template provides a comprehensive structure for defining an AI Persona in an AI-First Business Service Architecture. Complete the sections required by your tier to ensure proper governance, clear boundaries, and effective delegation.

**When to use this template:**
- After completing the Three-Question Discovery Process
- When delegating a new business function to AI
- When formalizing an existing AI implementation
- As part of service architecture documentation

**Key Principle:** An AI Persona is a formally delegated business responsibility with clear boundaries, not just an automated system.

### Tier Reference Table

| Section | Title | Tier 1 | Tier 2 | Tier 3 | Notes |
|---------|-------|--------|--------|--------|-------|
| 1 | Identification | **Required** | Required | Required | |
| 2 | Governance and Ownership | **Required** | Required | Required | |
| 3 | Three-Question Discovery | **Required** | Required | Required | |
| 4 | Intent and Mandate | **Required** | Required | Required | |
| 5 | Capabilities | **Required** | Required | Required | |
| 6 | Data Contract | **Partial** | Required | Required | Tier 1: subsections 6.1 and 6.3 only |
| 7 | Scope & Ways of Working | -- | **Required** | Required | |
| 8 | Authority Model | **Required** | Required | Required | |
| 9 | Interacting Services | -- | **Required** | Required | |
| 10 | Performance Measurement | -- | **Required** | Required | |
| 11 | Multi-Contributor KPI Attribution | -- | -- | **Required** | |
| 12 | Lifecycle Management | -- | -- | **Required** | |
| 13 | Regulatory and Compliance | -- | **Required** | Required | |
| 14 | Risk Management | -- | **Required** | Required | |
| 15 | Trusted AI Scope | -- | -- | **Required** | |
| 16 | Collaborative Data Supply Chain | -- | -- | **Required** | |
| 17 | Worked Example | -- | -- | **Required** | |
| 18 | Approval and Sign-Off | **Required** | Required | Required | Tier 1: lightweight sign-off only |
| 19 | Supporting Documentation | -- | -- | **Required** | |

---

## 1. AI Persona Identification **[TIER 1 REQUIRED]**

### 1.1 AI Persona Name
**Name:** `[Provide a clear, descriptive name reflecting the delegated function]`

**Example:** "Customer Churn Predictor & Retention Advisor"

**Naming Guidelines:**
- Use business function language, not technical jargon
- Be specific about what the AI does
- Avoid generic names like "AI Agent 1" or "ML Model"
- Should be recognizable to business stakeholders

---

### 1.2 Description
**Description:** `[Provide a brief overview of the delegated role and its function within the business context]`

**Example:** "Analyzes customer behavior data to predict churn risk and recommends personalized retention actions to account managers. Operates autonomously within defined rules to identify at-risk customers and suggest approved interventions."

**Should include:**
- Primary business function
- Key activities performed
- Value delivered to the business
- Context within larger business operations

---

### 1.3 Version and Status
**Version:** `[e.g., 1.0]`

**Status:** `[Draft | In Review | Approved | In Production | Deprecated]`

**Effective Date:** `[When this definition takes effect]`

**Review Date:** `[Next scheduled review]`

---

## 2. Governance and Ownership **[TIER 1 REQUIRED]**

### 2.1 Business Owner(s)

| Name/Role | Responsibilities | Contact | Priority/Goal |
|-----------|-----------------|---------|---------------|
| `[e.g., VP of Customer Success]` | `[Accountable for AI Persona performance, risk management, and boundary adherence. Approves changes to AI rules and manages associated risks.]` | `[Email/phone]` | `[e.g., Reduce churn to <5%]` |

**Business Owner Authority:**
- Approve/reject changes to AI Persona capabilities
- Set performance targets and KPIs
- Manage business risks associated with AI actions
- Determine scope boundaries
- Approve budget for AI Persona operation

**Responsibilities include:**
- [ ] Regular performance review
- [ ] Boundary compliance monitoring
- [ ] Stakeholder communication
- [ ] Strategic alignment
- [ ] Change management approval

---

### 2.2 AI Resource Management Liaison

**Responsible Person/Team:** `[Name/role from AI Resource Management service]`

**Contact:** `[Email/phone]`

**Responsibilities:**
- Technical health monitoring
- Model performance tracking
- Infrastructure management
- Security and compliance (technical aspects)
- Escalation handling
- Lifecycle management (updates, retraining, decommissioning)

---

### 2.3 Controlling Domain

**Service Domain:** `[Specify the business service or domain responsible for this function]`

**Example:** "Customer Success Management Service" or "Sales Service → Customer Retention (Level 1)"

**Location in Service Hierarchy:**
- Level 0: `[Parent service]`
- Level 1: `[Service at this level, if applicable]`
- Level N: `[This AI Persona's position]`

---

## 3. Three-Question Discovery Results **[TIER 1 REQUIRED]**

### 3.1 Question 1: What Do You Want to Delegate to AI?

**Delegation Statement:** `[Clear, concise statement of what business function is being delegated]`

**Example:** "Delegate the continuous monitoring of customer health metrics and generation of retention recommendations to the AI Persona, while retaining human approval for final customer-facing actions."

**In Scope (What IS delegated):**
- `[Specific activity 1]`
- `[Specific activity 2]`
- `[Specific activity 3]`

**Out of Scope (What is NOT delegated):**
- `[Specific exclusion 1 - be explicit about boundaries]`
- `[Specific exclusion 2]`
- `[Specific exclusion 3]`

**Rationale for Delegation:**
`[Why is this function suitable for AI delegation? Business value, scale, consistency, etc.]`

---

### 3.2 Question 2: How Will You Manage That AI?

**Management Approach:** `[Describe oversight mechanisms]`

**Performance Measures:** (See Section 7 for details)
- Primary KPI: `[e.g., Churn reduction percentage]`
- Success Metrics: `[List 2-3 key metrics]`

**Monitoring Mechanisms:**
- **Frequency:** `[e.g., Daily automated reports, weekly reviews]`
- **Alerts:** `[What triggers escalation to Business Owner]`
- **Dashboards:** `[What information is tracked visually]`

**Control Mechanisms:**
- **Approval Workflows:** `[What requires human approval]`
- **Override Capabilities:** `[How humans can intervene]`
- **Kill Switch:** `[Emergency shutdown procedure]`

**Review Cadence:**
- Performance Review: `[e.g., Weekly]`
- Boundary Audit: `[e.g., Monthly]`
- Strategic Alignment: `[e.g., Quarterly]`
- Full Governance Review: `[e.g., Annually]`

---

### 3.3 Question 3: How Will You Include It in Your Team?

**Integration Model:** `[Select one: Assistant | Collaborator | Specialist]`

**Assistant:** AI supports human work, requires supervision
**Collaborator:** AI works peer-to-peer with humans in defined areas
**Specialist:** AI has expert responsibility in narrow domain

**Selected Model:** `[Your choice with justification]`

**Team Integration:**
- **Who Interacts:** `[Which roles/people work with this AI Persona]`
- **How They Interact:** `[Workflow description]`
- **Training Required:** `[What do humans need to learn to work with this AI]`
- **Communication Channels:** `[How AI "communicates" with team - alerts, dashboards, direct recommendations, etc.]`

**Cultural Considerations:**
`[How will this AI Persona's introduction be managed from a change management perspective? Team concerns? Training needs?]`

---

## 4. Intent and Mandate **[TIER 1 REQUIRED]**

### 4.1 Primary Intent

**Intent Name:** `[Descriptive name for this intent]`

**Mandate Statement:** `[Clear statement of the business goal the AI Persona is delegated to achieve]`

**Example:** "Proactively identify customers with >75% churn risk in the next 90 days and recommend approved retention actions to relevant Account Managers within 24 hours of risk detection."

**Business Objective Alignment:**
`[Which business objective or strategic goal does this intent support?]`

**Success Criteria:**
`[How will we know this intent is being fulfilled successfully?]`

---

### 4.2 Secondary Intents (if applicable)

| Intent Name | Mandate | Priority | Success Measure |
|-------------|---------|----------|-----------------|
| `[Name]` | `[Mandate statement]` | `[High/Med/Low]` | `[Measure]` |

---

## 5. Capabilities (Permitted Actions & Tools) **[TIER 1 REQUIRED]**

### 5.1 Permitted Actions

List the specific, discrete actions the AI Persona is authorized to perform. Be precise and exhaustive.

| Capability ID | Action Description | Inputs Required | Outputs Produced | Approval Required? |
|---------------|-------------------|-----------------|------------------|-------------------|
| CAP-001 | `[e.g., Read customer data from CRM]` | `[Customer ID]` | `[Customer record]` | No |
| CAP-002 | `[e.g., Calculate churn probability score]` | `[Customer data, usage history]` | `[Risk score 0-100]` | No |
| CAP-003 | `[e.g., Generate retention recommendation]` | `[Risk score, customer segment]` | `[Recommended action]` | No |
| CAP-004 | `[e.g., Send alert to Account Manager]` | `[Risk data, recommendation]` | `[Alert notification]` | No |
| CAP-005 | `[e.g., Log prediction and outcome]` | `[All interaction data]` | `[Audit log entry]` | No |

**Additional Capabilities:**
- `[List any other permitted actions]`
- `[Be comprehensive - if it's not listed, it's not permitted]`

---

### 5.2 Prohibited Actions

Explicitly list actions the AI Persona must NOT perform:

- `[e.g., Direct contact with customers without human intermediary]`
- `[e.g., Access to personally identifiable information beyond specified fields]`
- `[e.g., Modification of pricing or discount structures]`
- `[e.g., Autonomous approval of retention offers >$X value]`
- `[Add others as appropriate]`

---

### 5.3 Tools and Systems Access

| System/Tool | Access Level | Permitted Operations | Restrictions |
|-------------|--------------|----------------------|--------------|
| `[e.g., Salesforce CRM]` | Read-Only | Query customer records | Specified fields only (see Data Contract) |
| `[e.g., Product Analytics DB]` | Read-Only | Query usage data | Last 12 months only |
| `[e.g., Internal Messaging System]` | Write | Send notifications | Account Managers only |
| `[e.g., Monitoring Database]` | Read/Write | Log predictions and outcomes | Append-only |

---

## 6. Data Contract (Information Access Scope) **[TIER 1 PARTIAL -- Complete 6.1 and 6.3 only; TIER 2 FULL]**

### 6.1 Permitted Data Sources

| Data Source | System Name | Access Type | Justification |
|-------------|-------------|-------------|---------------|
| `[e.g., Customer Master Data]` | `[Salesforce CRM]` | Read-Only | Required to identify customer and segment |
| `[e.g., Product Usage Logs]` | `[Product Analytics DB]` | Read-Only | Required to assess engagement level |
| `[e.g., Billing History]` | `[Billing System]` | Read-Only | Required to assess payment patterns |

---

### 6.2 Permitted Data Types and Fields

**Explicitly list all data elements the AI may access:**

**Customer Data:**
- Customer ID (unique identifier)
- Account Status (active/inactive/suspended)
- Subscription Tier (bronze/silver/gold)
- Customer Segment (enterprise/mid-market/SMB)
- Contract Start Date
- Contract End Date
- `[List other permitted fields]`

**Usage Data:**
- Login Frequency (last 90 days)
- Feature X Usage Count (last 90 days)
- Feature Y Usage Count (last 90 days)
- Session Duration Average (last 90 days)
- `[List other permitted fields]`

**Billing Data:**
- Payment Status (current/overdue/pending)
- Last Payment Date
- Outstanding Balance
- Payment Method Type (not details)
- `[List other permitted fields]`

**Support Data:**
- Support Ticket Count (last 90 days)
- Ticket Priority Distribution
- Average Resolution Time
- `[List other permitted fields]`

---

### 6.3 Data Restrictions and Constraints

**Access Constraints:**
- **Time Window:** `[e.g., Access limited to data from last 12 months only]`
- **Volume Constraints:** `[e.g., Maximum 10,000 records per query]`
- **Geographic Restrictions:** `[e.g., US customer data only, GDPR-compliant regions]`
- **Anonymization Requirements:** `[e.g., PII must be hashed before model training]`

**Prohibited Data:**
- `[e.g., Social Security Numbers]`
- `[e.g., Credit card numbers or payment credentials]`
- `[e.g., Free-text notes fields containing sensitive information]`
- `[e.g., Employee personal information]`
- `[e.g., Data from customers who have opted out of automated processing]`

**Data Quality Requirements:**
- Minimum data completeness: `[e.g., 95% of required fields populated]`
- Maximum data age: `[e.g., Updated within last 24 hours]`
- Data validation: `[e.g., Must pass schema validation before processing]`

---

## 7. Scope & Ways of Working (Operational & Ethical Guardrails) **[TIER 2 REQUIRED]**

### 7.1 Operational Rules

**Operating Schedule:**
- **Frequency:** `[e.g., Runs daily at 1 AM - 3 AM UTC]`
- **On-Demand:** `[Can it be triggered manually? By whom?]`
- **Blackout Periods:** `[Any times when it should NOT run?]`

**Processing Rules:**
- **Batch Size:** `[e.g., Process maximum 1000 customers per run]`
- **Priority Order:** `[e.g., Prioritize by customer lifetime value, highest first]`
- **Confidence Thresholds:**
  - Minimum confidence for action: `[e.g., 70%]`
  - Escalation threshold: `[e.g., Confidence <70% → Manual Review Queue]`
- **Action Catalog:** `[e.g., Only propose actions from currently approved 'Retention Offer Catalogue']`

**Decision Logic:**
- **Risk Score Calculation:** `[Brief description or reference to documentation]`
- **Segmentation Logic:** `[How customers are categorized]`
- **Recommendation Selection:** `[How AI chooses which action to recommend]`

**Escalation Rules:**
- **Automatic Escalation Triggers:**
  - `[e.g., Conflicting data flags (high usage but high churn score)]`
  - `[e.g., Customer in VIP segment]`
  - `[e.g., Potential revenue impact >$X]`
  - `[e.g., Confidence score <threshold]`

**Exception Handling:**
- **Data Quality Issues:** `[What happens if data is incomplete/invalid?]`
- **System Unavailability:** `[What happens if dependent system is down?]`
- **Anomalies Detected:** `[What happens if AI detects unexpected patterns?]`

---

### 7.2 Ethical Guardrails

**Fairness Constraints:**
- `[e.g., Must not use protected characteristics (race, gender, age, religion) in prediction model]`
- `[e.g., Regular bias testing against demographic groups]`
- `[e.g., Ensure recommendation distribution is equitable across customer segments]`

**Transparency Requirements:**
- `[e.g., All predictions must be explainable to customer-facing staff]`
- `[e.g., Maintain audit trail of all decisions]`
- `[e.g., Provide "reason codes" for all recommendations]`

**Human Dignity:**
- `[e.g., No automated denial of service without human review]`
- `[e.g., Customers always have right to human review]`
- `[e.g., AI must recommend, humans must approve customer-facing actions]`

**Compliance Alignment:**
- GDPR: `[Specific requirements, e.g., right to explanation, data minimization]`
- Industry Regulations: `[e.g., Financial services fairness requirements]`
- Corporate Ethics Policy: `[Reference to company policy]`

---

### 7.3 Business Rules

**Approval Workflows:**
- Actions requiring human approval:
  - `[e.g., Retention offers valued >$1000]`
  - `[e.g., Account modifications]`
  - `[e.g., Any action affecting enterprise customers]`

**Override Capabilities:**
- Who can override AI recommendations: `[Roles/positions]`
- Process for override: `[Documentation required? Approval levels?]`
- Override tracking: `[How are overrides logged and analyzed?]`

**Interaction with Other Systems:**
- `[e.g., Cannot override manual risk flags set by Account Managers]`
- `[e.g., Must respect customer communication preferences (frequency caps)]`
- `[e.g., Coordinate with Marketing automation to avoid message conflicts]`

---

## 8. Authority Model (Context of Action) **[TIER 1 REQUIRED]**

### 8.1 Authority Type

**Select One:**

- [ ] **Owner Authority**: AI acts autonomously based on its defined mandate and rules, on behalf of the controlling domain/owner. The owner delegates standing authority.

- [ ] **Invoker Authority**: AI acts as an assistant or tool for the specific human/system invoking it, operating under their immediate context. The invoker delegates temporary authority for a specific task.

**Selected:** `[Owner Authority | Invoker Authority]`

**Justification:** `[Why this authority model is appropriate for this AI Persona]`

---

### 8.2 Delegation Framework

**For Owner Authority:**
- Authority delegated by: `[Business Owner name/role]`
- Delegation scope: `[What decisions can AI make autonomously?]`
- Delegation constraints: `[What requires escalation?]`
- Authority review cycle: `[How often is delegation reviewed?]`

**For Invoker Authority:**
- Who can invoke: `[Specific roles/individuals]`
- Invocation context: `[Under what circumstances?]`
- Invoker's responsibility: `[What remains with human invoker?]`
- Result ownership: `[Who owns the outcome of AI action?]`

---

### 8.3 Accountability

**When AI Acts:**
- Immediate accountability: `[Who is responsible for this specific action?]`
- Ultimate accountability: `[Who bears business consequences?]`
- Legal accountability: `[Who is legally responsible?]`

**Traceability:**
- All actions logged: `[Yes/No - should always be Yes]`
- Action attribution: `[How do we trace an action back to specific AI decision?]`
- Human review capability: `[Can actions be reviewed post-facto?]`

---

## 9. Interacting Services and Actors **[TIER 2 REQUIRED]**

### 9.1 Service Interactions

**Services This AI Persona Consumes From:**

| Service Name | Capability Used | Frequency | Data Exchanged | SLA Dependency |
|--------------|----------------|-----------|----------------|----------------|
| `[e.g., CRM Service]` | `[Get Customer Data]` | `[Daily]` | `[Customer records]` | `[99.5% availability]` |
| `[e.g., Analytics Service]` | `[Get Usage Metrics]` | `[Daily]` | `[Usage statistics]` | `[99% availability]` |

**Services This AI Persona Provides To:**

| Service Name | Capability Provided | Frequency | Data Provided | Purpose |
|--------------|-------------------|-----------|---------------|---------|
| `[e.g., Account Management Service]` | `[Churn Alerts]` | `[Real-time]` | `[Risk scores, recommendations]` | `[Enable proactive retention]` |
| `[e.g., Reporting Service]` | `[Prediction Metrics]` | `[Daily]` | `[Aggregate statistics]` | `[Performance tracking]` |

---

### 9.2 Actor Interactions

**Human Actors:**

| Actor Role | Interaction Type | Frequency | Purpose |
|------------|-----------------|-----------|---------|
| `[e.g., Account Manager]` | Receives alerts and recommendations | Daily | Act on retention opportunities |
| `[e.g., Customer Success Director]` | Reviews performance dashboard | Weekly | Monitor AI effectiveness |
| `[e.g., Data Scientist]` | Model retraining and tuning | Monthly | Maintain AI accuracy |

**System Actors:**

| System Name | Interaction Type | Frequency | Purpose |
|-------------|-----------------|-----------|---------|
| `[e.g., Notification Service]` | Sends alerts | Real-time | Deliver AI outputs to humans |
| `[e.g., Retention Offer Catalogue]` | Queries available offers | Daily | Select appropriate recommendations |

---

## 10. Performance Measurement (5-Tier Framework) **[TIER 2 REQUIRED]**

### 10.1 Strategic Measures (Tier 1)

**Objective:**
`[Which business objective does this AI Persona support?]`

**Example:** "Improve customer retention and reduce churn"

---

### 10.2 Performance & Outcome Measures (Tier 2)

**Key Result:**
- Metric: `[e.g., Reduce churn rate from 8% to <5%]`
- Measurement Period: `[e.g., Quarterly]`
- Target: `[Specific number]`

**KPI Outcome (AI-Specific):**
- Primary KPI: `[e.g., Percentage of at-risk customers successfully retained]`
- Target: `[e.g., >60% retention rate for AI-flagged customers]`

**Value Contribution:**
- Financial Impact: `[e.g., $X revenue retained annually]`
- Calculation Method: `[How is this measured and attributed?]`

---

### 10.3 Experiential & Operational Measures (Tier 3)

**XLA (Experience Level Agreement):**
- Measure: `[e.g., Account Manager satisfaction with AI recommendations]`
- Target: `[e.g., >4.0/5.0 usefulness score]`
- Survey Frequency: `[e.g., Monthly]`

**SLA (Service Level Agreement):**
- Availability: `[e.g., 99.5% uptime during operating hours]`
- Response Time: `[e.g., Alerts delivered within 5 minutes of detection]`
- Accuracy: `[e.g., Prediction accuracy >75% (validated against actual churn)]`

---

### 10.4 Actionable Inputs & Levers (Tier 4)

**Leading Indicators:**
- Indicator: `[e.g., Number of at-risk customers identified per week]`
- Expected Range: `[e.g., 50-200 customers]`

**Value Levers:**
- Lever: `[e.g., Risk score threshold for alerting]`
- Current Setting: `[e.g., 75%]`
- Adjustment Authority: `[Who can change this?]`

---

### 10.5 Contextual Factors (Tier 5)

**Risk Level:**
- Risk Category: `[e.g., Reputational risk of false positives]`
- Risk Level: `[High/Medium/Low]`
- Mitigation: `[e.g., Human review of all recommendations before customer contact]`

**Data Quality Issues:**
- Critical Dependencies: `[e.g., CRM data completeness >95%]`
- Monitoring: `[How is data quality tracked?]`
- Impact if Degraded: `[e.g., Prediction accuracy drops, alerts may be missed]`

---

## 11. Multi-Contributor KPI Attribution **[TIER 3 REQUIRED]**

### 11.1 Shared Responsibility

**KPI:** `[e.g., Overall Customer Churn Rate]`

**Contributors to This KPI:**
- AI Persona Contribution: `[e.g., Identifies at-risk customers, recommends actions]`
- Human Contribution: `[e.g., Account Managers execute retention strategies, build relationships]`
- Other Factors: `[e.g., Product quality, pricing, market conditions]`

### 11.2 Attribution Methodology

**Approach:** `[Select: Direct Attribution | Proportional Attribution | Experimental (A/B Testing) | Statistical Modeling]`

**Description:**
`[Explain how this AI Persona's contribution is measured separately from other factors]`

**Example:** "Compare retention rates for AI-flagged customers vs. control group. AI Persona credited with incremental improvement."

---

## 12. Lifecycle Management **[TIER 3 REQUIRED]**

### 12.1 Development and Training

**Initial Training:**
- Training Data: `[Description of data used]`
- Training Period: `[Date range]`
- Validation Approach: `[How model was validated]`
- Initial Accuracy: `[Baseline performance metrics]`

**Model Details:**
- Model Type: `[e.g., Gradient Boosted Trees, Neural Network, etc.]`
- Model Version: `[e.g., v1.0]`
- Training Framework: `[e.g., TensorFlow, scikit-learn, etc.]`

---

### 12.2 Deployment

**Deployment Date:** `[When AI Persona went into production]`

**Deployment Approach:**
- [ ] Pilot (limited scope)
- [ ] Phased Rollout
- [ ] Full Deployment
- [ ] A/B Testing (alongside existing process)

**Rollout Plan:** `[Description of deployment stages if phased]`

---

### 12.3 Monitoring and Evolution

**Performance Monitoring:**
- Frequency: `[e.g., Daily automated monitoring, weekly review]`
- Metrics Tracked: `[List key metrics]`
- Alert Thresholds: `[What triggers escalation]`

**Drift Detection:**
- Data Drift Monitoring: `[How is input data drift detected?]`
- Concept Drift Monitoring: `[How is model accuracy degradation detected?]`
- Response Protocol: `[What happens when drift is detected?]`

**Retraining Schedule:**
- Scheduled Retraining: `[e.g., Quarterly]`
- Trigger-Based Retraining: `[e.g., If accuracy drops below X%]`
- Retraining Process: `[Who approves? How is it tested?]`

---

### 12.4 Change Management

**Change Control Process:**
- Minor Changes (e.g., threshold adjustments): `[Approval required from ______]`
- Major Changes (e.g., new capabilities): `[Approval required from ______ + Business Owner]`
- Emergency Changes: `[Process for urgent modifications]`

**Version Control:**
- Current Version: `[e.g., 2.1]`
- Previous Versions: `[List with deployment dates]`
- Rollback Capability: `[Can previous version be restored? How?]`

---

### 12.5 Decommissioning

**Decommissioning Triggers:**
- `[e.g., Business function no longer needed]`
- `[e.g., Replaced by superior solution]`
- `[e.g., Consistently fails to meet performance targets]`
- `[e.g., Regulatory changes make approach non-compliant]`

**Decommissioning Process:**
1. Business Owner approval
2. Stakeholder notification (lead time: `[e.g., 30 days]`)
3. Data/log archival
4. System access revocation
5. Documentation archival
6. Post-decommission review

---

## 13. Regulatory and Compliance **[TIER 2 REQUIRED]**

### 13.1 Applicable Regulations

**Industry Regulations:**
- `[e.g., GDPR (General Data Protection Regulation)]`
- `[e.g., CCPA (California Consumer Privacy Act)]`
- `[e.g., Industry-specific regulations]`

**AI-Specific Regulations:**
- `[e.g., EU AI Act classification: _____]`
- `[e.g., Local AI governance requirements]`

**Data Privacy:**
- Data Classification: `[Public | Internal | Confidential | Restricted]`
- Privacy Impact Assessment: `[Completed? Date? Link?]`

---

### 13.2 Compliance Requirements

**Audit Requirements:**
- Audit Frequency: `[e.g., Quarterly]`
- Audit Scope: `[What is reviewed?]`
- Auditor: `[Internal/External]`

**Documentation Requirements:**
- Decision Logs: `[Retention period]`
- Model Documentation: `[What must be documented?]`
- Change History: `[Retention period]`

**Right to Explanation:**
- `[Does the user/customer have right to explanation? How is this provided?]`

**Right to Human Review:**
- `[Can users request human review of AI decision? Process?]`

---

### 13.3 Compliance Monitoring

**Compliance Metrics:**
- `[e.g., % of decisions with complete audit trail: Target 100%]`
- `[e.g., % of data access requests within permitted scope: Target 100%]`

**Violations:**
- Reporting Process: `[How are compliance violations reported?]`
- Response Protocol: `[What happens when violation detected?]`

---

## 14. Risk Management **[TIER 2 REQUIRED]**

### 14.1 Risk Assessment

| Risk Category | Specific Risk | Likelihood | Impact | Mitigation |
|---------------|---------------|------------|--------|------------|
| **Operational** | `[e.g., AI downtime]` | `[H/M/L]` | `[H/M/L]` | `[e.g., Fallback to manual process]` |
| **Accuracy** | `[e.g., False positives]` | `[H/M/L]` | `[H/M/L]` | `[e.g., Human review workflow]` |
| **Security** | `[e.g., Unauthorized access to data]` | `[H/M/L]` | `[H/M/L]` | `[e.g., Access controls, monitoring]` |
| **Reputational** | `[e.g., Biased recommendations]` | `[H/M/L]` | `[H/M/L]` | `[e.g., Regular bias testing]` |
| **Regulatory** | `[e.g., Non-compliance with GDPR]` | `[H/M/L]` | `[H/M/L]` | `[e.g., Compliance monitoring]` |

---

### 14.2 Risk Mitigation

**Preventive Controls:**
- `[Controls in place to prevent risks]`

**Detective Controls:**
- `[Controls in place to detect when risks materialize]`

**Corrective Controls:**
- `[Controls in place to correct issues when detected]`

---

### 14.3 Incident Response

**Incident Types:**
- Performance Degradation: `[Response protocol]`
- Security Breach: `[Response protocol]`
- Boundary Violation: `[Response protocol]`
- Ethical Concern: `[Response protocol]`

**Escalation Path:**
1. `[First level - e.g., AI Resource Management]`
2. `[Second level - e.g., Business Owner]`
3. `[Third level - e.g., Executive leadership]`

---

## 15. Trusted AI (Scope) Framework Integration **[TIER 3 REQUIRED]**

### 15.1 Scope Boundary Visualization

`[Reference to diagram showing AI Persona's scope boundary - what's inside vs. outside]`

**Inside Scope:**
- `[Systems/data AI can access]`
- `[Actions AI can perform]`
- `[Decisions AI can make]`

**Outside Scope (Explicit Exclusions):**
- `[Systems/data AI cannot access]`
- `[Actions AI cannot perform]`
- `[Decisions AI cannot make]`

---

### 15.2 Scope Clarity Checklist

- [ ] Permitted actions are explicitly enumerated
- [ ] Prohibited actions are explicitly stated
- [ ] Data access boundaries are clearly defined
- [ ] Authority model is unambiguous
- [ ] Escalation paths are defined
- [ ] Human oversight mechanisms are in place
- [ ] Boundary adherence is monitored

---

## 16. Collaborative Data Supply Chain Integration **[TIER 3 REQUIRED]**

### 16.1 Data Flow Mapping

**Upstream Nodes (Data Providers to AI Persona):**

| Node Name | Node Type | Data Provided | Frequency | Quality SLA |
|-----------|-----------|---------------|-----------|-------------|
| `[e.g., CRM System]` | System | Customer records | Real-time | 99% accuracy |
| `[e.g., Analytics Platform]` | System | Usage metrics | Daily batch | 95% completeness |

**Downstream Nodes (Data Consumers from AI Persona):**

| Node Name | Node Type | Data Consumed | Frequency | Usage Purpose |
|-----------|-----------|---------------|-----------|---------------|
| `[e.g., Account Managers]` | Human | Risk alerts | Real-time | Take action |
| `[e.g., Reporting System]` | System | Prediction logs | Daily batch | Audit & analytics |

---

### 16.2 Data Contracts

**With Upstream Nodes:**
- Contract: `[e.g., CRM provides customer data with <1 hour lag]`
- SLA: `[e.g., 99% availability, 95% data completeness]`
- Breach Protocol: `[What happens if contract violated?]`

**With Downstream Nodes:**
- Contract: `[e.g., AI provides alerts within 5 minutes of detection]`
- SLA: `[e.g., 99.5% delivery success rate]`
- Breach Protocol: `[What happens if contract violated?]`

---

## 17. Worked Example **[TIER 3 REQUIRED]**

### 17.1 Scenario

`[Describe a specific example scenario showing this AI Persona in action]`

**Example:** "Customer ABC Corp shows declining usage (60% drop over 90 days), increased support tickets, and has an enterprise-tier subscription worth $100K annually."

---

### 17.2 AI Persona Processing

Step-by-step walkthrough:
1. `[e.g., AI retrieves customer data and calculates risk score: 87%]`
2. `[e.g., AI determines customer segment: Enterprise]`
3. `[e.g., AI selects recommendation from approved catalog: Executive Business Review]`
4. `[e.g., AI generates alert to Account Manager Sarah Johnson]`
5. `[e.g., Sarah reviews, approves, schedules EBR]`
6. `[e.g., AI logs prediction, action, and outcome for tracking]`

---

### 17.3 Outcome

`[What happened? Was intervention successful? What was learned?]`

---

## 18. Approval and Sign-Off **[TIER 1 REQUIRED -- Lightweight sign-off only]**

### 18.1 Approval History

| Version | Date | Approved By | Role | Notes |
|---------|------|-------------|------|-------|
| 1.0 | `[Date]` | `[Name]` | Business Owner | Initial approval |
| 1.1 | `[Date]` | `[Name]` | AI Resource Mgmt | Technical validation |

---

### 18.2 Current Status

**Status:** `[Draft | In Review | Approved | Active | Under Revision | Deprecated]`

**Approved By:**
- Business Owner: `[Name, Date, Signature]`
- AI Resource Management: `[Name, Date, Signature]`
- Compliance Officer: `[Name, Date, Signature]` (if required)

**Next Review Date:** `[Date]`

---

## 19. Supporting Documentation **[TIER 3 REQUIRED]**

### 19.1 References

- Service Architecture Diagram: `[Link or reference]`
- BPMN Process Diagram: `[Link or reference]`
- Measure Hierarchy Diagram: `[Link or reference]`
- Technical Implementation Details: `[Link or reference]`
- Model Card/Documentation: `[Link or reference]`
- Data Privacy Impact Assessment: `[Link or reference]`

---

### 19.2 Related AI Personas

**Collaborating AI Personas:**
- `[List AI Personas this one works with]`

**Predecessor/Successor:**
- Replaces: `[Previous approach or AI Persona]`
- May be replaced by: `[Future planned evolution]`

---

### 19.3 Change Log

| Version | Date | Changed By | Change Description |
|---------|------|------------|-------------------|
| 1.0 | `[Date]` | `[Name]` | Initial creation |
| 1.1 | `[Date]` | `[Name]` | Updated data contract to add new field |

---

**End of AI Persona Definition**

---

## Tiered Completion Checklist

Use the checklist matching the tier assigned to this AI Persona. Each tier includes all items from lower tiers.

### Tier 1 Checklist -- Discovery / Low Risk

- [ ] **Section 1:** Persona name, description, version, and status recorded
- [ ] **Section 2:** Business Owner and AI RM liaison identified; controlling domain specified
- [ ] **Section 3:** Three-Question Discovery results documented with in-scope and out-of-scope boundaries
- [ ] **Section 4:** Primary intent and mandate statement defined with business objective alignment
- [ ] **Section 5:** Capabilities list is exhaustive (if not listed, not permitted); prohibited actions stated
- [ ] **Section 6 (partial):** Permitted data sources (6.1) and data restrictions (6.3) specified
- [ ] **Section 8:** Authority model selected (Owner or Invoker) with delegation framework
- [ ] **Section 18 (lightweight):** Business Owner sign-off obtained; AI RM acknowledgement recorded

### Tier 2 Checklist -- Governance-Ready / Medium Risk

All Tier 1 items, plus:

- [ ] **Section 6 (full):** Permitted data types and fields (6.2) completed with exact field names
- [ ] **Section 7:** Operational rules, ethical guardrails, and business rules documented
- [ ] **Section 9:** Consuming and providing service interactions mapped with SLA dependencies
- [ ] **Section 10:** Performance measures defined across all 5 tiers with targets
- [ ] **Section 13:** Applicable regulations identified; compliance monitoring metrics set
- [ ] **Section 14:** Risk assessment completed with preventive, detective, and corrective controls

### Tier 3 Checklist -- Full Specification / High Risk

All Tier 1 and Tier 2 items, plus:

- [ ] **Section 11:** Multi-contributor KPI attribution methodology defined with shared responsibility model
- [ ] **Section 12:** Lifecycle management plan covering development, deployment, monitoring, change, and decommissioning
- [ ] **Section 15:** Trusted AI (Scope) boundary visualised with scope clarity checklist completed
- [ ] **Section 16:** Data supply chain mapped with upstream and downstream node contracts
- [ ] **Section 17:** Worked example scenario documented showing end-to-end persona operation
- [ ] **Section 18 (full):** Compliance Officer sign-off obtained in addition to Business Owner and AI RM
- [ ] **Section 19:** All supporting documentation referenced and linked
