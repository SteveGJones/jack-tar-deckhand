---
name: change-advisory-circle-manager
description: Cross-domain governance workflow for the Change Advisory Circle (CAC). Defines charter, composition, and decision-making process for cross-company and cross-domain SOP changes. Enforces "One Server, One Owner" doctrine.
---

# Change Advisory Circle Manager

This skill establishes the Change Advisory Circle (CAC) governance framework for managing cross-domain SOP changes. The CAC is required when SOPs cross domain or company boundaries, enforcing the "One Server, One Owner" doctrine while enabling safe evolution of shared capabilities.

This addresses methodology compliance requirement R7: Change Advisory Circle composition and process definition.

## When to Use

- During architecture completion (Chapter 8) to establish CAC charter
- When a cross-domain SOP is identified in the dependency register
- When a consumer requests a change to a borrowed SOP
- Before deploying any AI Persona that invokes cross-domain SOPs
- During quarterly governance reviews
- When resolving SOP version conflicts between domains

## Key Concepts

### "One Server, One Owner" Doctrine

Every SOP runs on exactly one MCP server owned by exactly one named domain. No exceptions.

This creates a tension: **single owner, multiple consumers**. The CAC resolves this tension through governance, not technical duplication.

### CAC Purpose

The Change Advisory Circle exists to:
1. **Protect provider autonomy** — Owner can evolve their SOPs to meet their business needs
2. **Respect consumer dependency** — Changes that break consumers require negotiation
3. **Prevent vendor lock-in** — Consumers have a voice, not just a dependency
4. **Enforce versioning discipline** — Breaking changes follow semver and deprecation windows
5. **Maintain audit trails** — All cross-domain changes logged with rationale

### CAC Scope

**In Scope**:
- SOP schema changes (new parameters, removed parameters, type changes)
- SOP deprecation notices
- SOP ownership transfers (rare, requires executive approval)
- MCP server breaking changes
- New cross-domain SOP borrowing requests

**Out of Scope**:
- Within-domain SOP changes (owner has full autonomy)
- Non-breaking additions (new optional parameters, new SOPs)
- Performance tuning (as long as SLAs met)
- ERP system changes invisible to SOP interface

### Decision Types

| Decision | Definition | Voting |
|----------|-----------|--------|
| **Approve** | Change accepted as proposed, all parties agree | Consensus required |
| **Approve with Conditions** | Change accepted with specified modifications | Majority vote |
| **Reject** | Change blocked, owner must find alternative approach | Any consumer can veto breaking changes |
| **Defer** | Need more information, schedule follow-up | Majority vote |
| **Emergency Override** | Critical security/compliance issue, owner proceeds immediately, CAC ratifies post-hoc | Owner unilateral, 48hr notification |

## Instructions

### 1. Identify Cross-Domain SOP Clusters

From the dependency register and cross-domain SOP register, identify clusters of related dependencies:

```yaml
sop_cluster_example:
  cluster_id: "CLUSTER-INV-01"
  cluster_name: "Inventory Management Cross-Domain"

  provider:
    domain: "Supply Chain"
    mcp_server: "supplychain.mcp.spinnythings.local:8100"
    sop_ids: ["SOP-SC-INV-01", "SOP-SC-INV-02", "SOP-SC-INV-03"]

  consumers:
    - domain: "Manufacturing"
      persona_id: "PERS-SPINY-MFG-01"
      sop_usage: "SOP-SC-INV-01 (check_inventory_atp)"
      criticality: "High"

    - domain: "Quality"
      persona_id: "PERS-SPINY-QI-01"
      sop_usage: "SOP-SC-INV-02 (get_material_traceability)"
      criticality: "High"

    - external_company: "AeroVista"
      persona_id: "PERS-AERO-PROC-01"
      sop_usage: "SOP-SC-INV-01 (check_inventory_atp)"
      criticality: "Medium"
```

Each cluster gets a dedicated CAC sub-committee.

### 2. Define CAC Composition

For each SOP cluster, identify CAC members:

```yaml
cac_composition:
  cluster_id: "CLUSTER-INV-01"

  core_members:
    - role: "SOP Owner"
      person: "Supply Chain Director, SpinnyThings"
      responsibilities:
        - Propose changes
        - Maintain SOP documentation
        - Implement approved changes
        - Operate MCP server
      voting_power: "1 vote + tie-breaker"

    - role: "Primary Consumer (Internal)"
      person: "Manufacturing Operations Manager, SpinnyThings"
      responsibilities:
        - Represent Manufacturing AI Persona needs
        - Review change impact assessments
        - Test changes in staging
      voting_power: "1 vote"

    - role: "Primary Consumer (Internal)"
      person: "Quality Director, SpinnyThings"
      responsibilities:
        - Represent Quality AI Persona needs
        - Review regulatory implications
      voting_power: "1 vote"

    - role: "External Consumer"
      person: "Procurement Technology Lead, AeroVista"
      responsibilities:
        - Represent AeroVista AI Persona needs
        - Coordinate cross-company testing
      voting_power: "1 vote"

  advisory_members:
    - role: "AI RM Liaison"
      person: "AI RM Lab Lead, SpinnyThings"
      responsibilities:
        - Ensure Vanilla-Agent validation for changes
        - Advise on authority model impacts
        - Coordinate retraining if needed
      voting_power: "Advisory (no vote, but must sign off)"

    - role: "Solution Architect"
      person: "Platform Architect, SpinnyThings"
      responsibilities:
        - Assess technical feasibility
        - Propose versioning strategies
        - Coordinate dependency updates
      voting_power: "Advisory (no vote)"

    - role: "Security Architect"
      person: "Security Lead, SpinnyThings"
      responsibilities:
        - Review authorization impacts
        - Flag security concerns
        - Validate credential model changes
      voting_power: "Advisory (can escalate to veto for security issues)"
```

### 3. Create CAC Charter

Document the formal governance structure:

```markdown
# Change Advisory Circle Charter

## Cluster: Inventory Management Cross-Domain (CLUSTER-INV-01)

### Authority

This Change Advisory Circle is authorized to:
- Approve or reject changes to SOPs: SOP-SC-INV-01, SOP-SC-INV-02, SOP-SC-INV-03
- Set deprecation timelines for breaking changes
- Define versioning strategy and migration paths
- Resolve disputes between provider and consumers
- Escalate unresolvable conflicts to executive steering committee

### Decision-Making Rules

- **Quorum**: 3 of 4 core members (including SOP Owner)
- **Consensus preferred**: All parties agree (ideal outcome)
- **Majority vote**: 3 of 4 core members (for conditional approvals, deferrals)
- **Veto power**: Any consumer can veto a breaking change; triggers negotiation
- **Tie-breaker**: SOP Owner has tie-breaking vote
- **Advisory sign-off required**: AI RM Liaison must sign off on all changes (non-blocking, but recorded)

### Meeting Cadence

- **Regular meetings**: Monthly, 1st Thursday, 10:00-11:00 UTC
- **Emergency meetings**: Called by any core member with 24hr notice
- **Agenda deadline**: 3 business days before meeting
- **Minutes published**: Within 48 hours of meeting

### Change Request Process

[See step 4]

### Escalation Path

If CAC cannot reach consensus after 2 meetings:
1. Escalate to CTO (SpinnyThings) and VP Engineering (AeroVista)
2. If still unresolved, escalate to executive steering committee
3. Executive decision is final

### Charter Approval

- **Approved by**: CTO, SpinnyThings; VP Engineering, AeroVista
- **Effective Date**: 2027-02-01
- **Review Date**: 2027-08-01 (6 months)
```

### 4. Define Change Request Process

Establish the workflow for proposing and reviewing changes:

```yaml
change_request_workflow:
  step_1_submission:
    who: "SOP Owner or any consumer"
    action: "Submit change request via CAC portal"
    required_fields:
      - change_id: "Unique ID (e.g., CHG-INV-01-2027-02)"
      - sop_id: "Affected SOP ID"
      - change_type: "Breaking | Non-Breaking | Deprecation | New Feature"
      - rationale: "Business justification"
      - proposed_implementation: "Technical description"
      - impact_assessment: "Which consumers affected, how"
      - migration_path: "How consumers can adapt (if breaking)"
      - testing_plan: "Vanilla-Agent validation, staging tests"
      - proposed_timeline: "Dates for review, implementation, deployment"

  step_2_impact_analysis:
    who: "Solution Architect + AI RM Liaison"
    action: "Assess technical and persona impact"
    deliverables:
      - dependency_trace: "All affected personas and systems"
      - breaking_change_severity: "High | Medium | Low"
      - vanilla_agent_test_plan: "How to validate change"
      - retraining_requirement: "Yes | No | Uncertain"
    timeline: "5 business days from submission"

  step_3_consumer_review:
    who: "All consumer representatives"
    action: "Review change request and impact analysis"
    outputs:
      - support_vote: "Approve | Conditional | Reject | Need more info"
      - conditions: "If conditional, specify required modifications"
      - testing_commitment: "Agree to test in staging by [date]"
    timeline: "5 business days from impact analysis"

  step_4_cac_meeting:
    who: "All CAC members"
    action: "Discuss change request, vote on decision"
    meeting_agenda:
      - present_change: "SOP Owner or proposer presents (10 min)"
      - present_impact: "Architect presents analysis (5 min)"
      - consumer_feedback: "Each consumer states position (5 min each)"
      - discussion: "Open discussion (15 min)"
      - vote: "Formal vote (5 min)"
    outcomes:
      - approve: "Proceed to implementation"
      - approve_with_conditions: "Owner modifies and resubmits for fast-track"
      - reject: "Owner must find alternative approach"
      - defer: "Schedule follow-up with specific questions"

  step_5_implementation:
    who: "SOP Owner + MCP Server Team"
    action: "Implement approved change"
    requirements:
      - branch_deployment: "Deploy to staging first"
      - vanilla_agent_validation: "Run test harness, get PASS verdict"
      - consumer_staging_tests: "All consumers test with their personas"
      - documentation_update: "Update SOP schema, changelog, migration guide"
      - deprecation_window: "If breaking: min 90 days, communicated to all consumers"

  step_6_deployment:
    who: "SOP Owner"
    action: "Deploy to production"
    notifications:
      - pre_deploy_notice: "7 days before deployment"
      - deploy_announcement: "Day of deployment with changelog"
      - post_deploy_support: "Designated support contact for 14 days"
    rollback_plan: "Ability to revert to previous version within 4 hours"

  step_7_retrospective:
    who: "CAC"
    action: "Review change outcome at next regular meeting"
    questions:
      - "Did change achieve intended outcome?"
      - "Were any consumers negatively impacted?"
      - "Did Vanilla-Agent tests catch all issues?"
      - "What would we do differently next time?"
```

### 5. Create Meeting Template

Standardize CAC meeting structure:

```markdown
# CAC Meeting Minutes Template

## Meeting Details

- **Date**: [YYYY-MM-DD]
- **Time**: [HH:MM UTC]
- **Cluster**: [Cluster ID and Name]
- **Attendees**: [List core members, advisory members, guests]
- **Absent**: [List with apologies]

## Agenda

1. **Review minutes from last meeting** (5 min)
2. **Standing items** (10 min)
   - Dependency register updates
   - Vanilla-Agent test results
   - Incident reports related to cross-domain SOPs
3. **Change requests** (30 min)
   - [CHG-INV-01-2027-02]: Add new parameter to check_inventory_atp
   - [CHG-INV-02-2027-02]: Deprecate legacy material_id format
4. **New business** (10 min)
   - New borrowing requests
   - Upcoming SOP roadmap items
5. **Action items review** (5 min)

## Discussion Summary

### Change Request: CHG-INV-01-2027-02

**Proposer**: Supply Chain Director (SOP Owner)

**Change**: Add optional parameter `include_reserved_stock` (boolean) to `check_inventory_atp` operation

**Rationale**: Manufacturing needs visibility into reserved inventory to optimize line scheduling

**Impact Assessment**:
- Breaking change: No (new parameter is optional)
- Affected consumers: All 3 consumers
- Default behavior: Unchanged (defaults to false)
- Vanilla-Agent test: Pending

**Discussion**:
- Manufacturing: Strongly support, this solves our scheduling blind spot
- Quality: Neutral, doesn't affect our use case but no objection
- AeroVista: Request that reserved quantities include reason code (who reserved it, why)
- Architect: Technically straightforward, suggest adding `reservation_details` sub-object

**Vote**:
- Supply Chain: Approve with conditions
- Manufacturing: Approve with conditions
- Quality: Approve
- AeroVista: Approve with conditions

**Decision**: APPROVED WITH CONDITIONS
- Modify to add `reservation_details` sub-object with `reserved_by`, `reason_code`, `release_date`
- Fast-track re-review (email vote, no meeting needed)
- Implementation target: 2027-03-01

**Action Items**:
- [ ] Supply Chain: Modify proposal with reservation_details sub-object (by 2027-02-20)
- [ ] Architect: Update Vanilla-Agent test plan (by 2027-02-20)
- [ ] AI RM: Run Vanilla-Agent tests in staging (by 2027-02-25)
- [ ] All consumers: Test in staging (by 2027-02-28)

---

[Repeat for each change request]

---

## Action Items Summary

| ID | Owner | Action | Deadline | Status |
|----|-------|--------|----------|--------|
| ACT-01 | Supply Chain | Modify CHG-INV-01 proposal | 2027-02-20 | Open |
| ACT-02 | Architect | Update Vanilla-Agent test plan | 2027-02-20 | Open |

## Next Meeting

- **Date**: 2027-03-06 10:00 UTC
- **Agenda deadline**: 2027-03-03

## Approval

- **Minutes recorded by**: [Facilitator]
- **Approved by**: [Core members sign off]
```

### 6. Build CAC Tracking Dashboard

Create a view of CAC activity for governance transparency:

```yaml
cac_dashboard_specification:
  title: "Change Advisory Circle Dashboard"
  audience: "All CAC members, executive sponsors, auditors"
  refresh_rate: "Daily"

  sections:
    - section: "Active Change Requests"
      visualization: "Table"
      columns:
        - change_id
        - sop_id
        - change_type
        - status: "Submitted | Under Review | Pending Vote | Approved | Rejected | Deployed"
        - proposer
        - target_date
        - days_in_flight
      filters:
        - cluster
        - status
        - change_type

    - section: "CAC Meeting Schedule"
      visualization: "Calendar"
      events:
        - regular_meetings: "Monthly, 1st Thursday"
        - emergency_meetings: "Flagged in red"
        - agenda_deadlines: "3 days before meeting"

    - section: "Decision Velocity"
      visualization: "Bar chart"
      metric: "Average days from submission to decision"
      grouping: "By month"
      target: "<= 15 business days"

    - section: "Change Type Distribution"
      visualization: "Pie chart"
      metric: "Count of change requests by type"
      categories:
        - breaking_changes
        - non_breaking_additions
        - deprecations
        - new_borrowing_requests

    - section: "Veto and Escalation Tracker"
      visualization: "List"
      content: "Any change requests that were vetoed or escalated"
      fields:
        - change_id
        - veto_reason
        - escalation_status
        - executive_decision

    - section: "Cross-Domain SOP Health"
      visualization: "Table"
      content: "All cross-domain SOPs with key metrics"
      columns:
        - sop_id
        - consumer_count
        - last_change_date
        - vanilla_agent_test_status
        - incident_count_90d
        - next_cac_review_date
```

### 7. Establish Emergency Protocols

Define how to handle urgent cross-domain SOP issues:

```yaml
emergency_protocols:
  trigger_conditions:
    - "Security vulnerability discovered in cross-domain SOP"
    - "Production incident caused by cross-domain SOP"
    - "Regulatory non-compliance identified"
    - "Critical customer impact (AOG, safety)"

  emergency_response:
    step_1_notification:
      who: "SOP Owner"
      action: "Notify all CAC members within 1 hour"
      channels: ["Email", "Slack", "SMS for core members"]

    step_2_assessment:
      who: "SOP Owner + Security Architect"
      action: "Assess severity and impact"
      timeline: "Within 2 hours"
      output: "Emergency change proposal"

    step_3_decision:
      authority: "SOP Owner has unilateral authority to deploy emergency fix"
      constraint: "Must notify CAC within 1 hour of deployment"
      rationale_required: "Document why emergency override was necessary"

    step_4_ratification:
      who: "CAC"
      action: "Emergency meeting within 48 hours to ratify change"
      outcomes:
        - ratify: "Change is approved post-hoc"
        - ratify_with_conditions: "Change approved, but follow-up changes required"
        - reject: "Change must be rolled back, alternative approach required"

  post_incident_review:
    who: "CAC + Incident Commander"
    timeline: "Within 7 days of incident"
    deliverables:
      - incident_timeline
      - root_cause_analysis
      - prevention_measures
      - cac_process_improvements
```

### 8. Validate CAC Completeness

Check that CAC governance is comprehensive:

- [ ] All cross-domain SOP clusters identified from dependency register
- [ ] CAC composition defined for each cluster (core + advisory members)
- [ ] Charter approved by executive sponsors
- [ ] Decision-making rules clear (quorum, voting, veto, escalation)
- [ ] Change request process documented with clear steps
- [ ] Meeting template standardized
- [ ] Tracking dashboard specified
- [ ] Emergency protocols established
- [ ] CAC members notified and onboarded
- [ ] First meeting scheduled

## Output

A complete Change Advisory Circle governance package with:
- CAC charter with authority, composition, and decision rules
- Change request process workflow
- Meeting minutes template
- CAC tracking dashboard specification
- Emergency protocol procedures
- Initial CAC meeting schedule

**File locations**:
- `docs/architecture/bsa/generated/governance/cac-charter-[cluster-id].md`
- `docs/architecture/bsa/generated/governance/cac-meeting-template.md`
- `docs/architecture/bsa/generated/governance/cac-change-request-workflow.md`
- `docs/architecture/bsa/generated/governance/cac-emergency-protocols.md`

## Relationship to Other Skills

- **Upstream**: Requires `dependency-register` (identifies cross-domain SOP clusters)
- **Upstream**: Requires `ai-persona-definition` (identifies consumers of cross-domain SOPs)
- **Upstream**: Requires `readiness-scorecard` (Checkpoint 5: CAC sign-off required)
- **Downstream**: Feeds `vanilla-agent-test-harness` (changes trigger re-validation)
- **Downstream**: Feeds compliance audits (CAC minutes are governance evidence)
- **Related**: `bpmn-ai-process-generator` (CAC approval points become process gateways)
- **Related**: `measurement-blueprint` (CAC effectiveness becomes a Tier 3 operational metric)
