---
name: xla-designer
description: Designs Experience Level Agreements (XLAs) for human-AI interaction quality. Defines how humans experience working with AI personas including response time, explanation quality, escalation smoothness, and trust calibration.
---

# XLA Designer

This skill designs Experience Level Agreements (XLAs) that measure the quality of human-AI collaboration from the human's perspective. XLAs complement SLAs: SLAs measure whether the system works, XLAs measure whether humans trust and value working with it.

XLAs are a Tier 3 measure in the 5-tier framework and are critical for AI Persona authority level progression.

## When to Use

- After completing AI Persona definition (Section 9: Interacting Services and Actors)
- During measurement blueprint design (Tier 3: Experiential & Operational)
- When designing human approval touchpoints in process flows
- Before promoting an AI Persona to higher authority levels
- During XLA performance reviews to assess trust calibration

## Key Concepts

### XLA vs SLA

| Aspect | SLA (System) | XLA (Experience) |
|--------|--------------|------------------|
| **Perspective** | System operator's view | Human user's view |
| **Measures** | Uptime, latency, throughput | Trust, clarity, ease, satisfaction |
| **Question** | "Is the system working?" | "Is the human able to work effectively with the AI?" |
| **Example** | 99.5% uptime, <500ms response | Explanation quality score >4.0/5.0 |

Both are needed. A system can have perfect SLAs but terrible XLAs (e.g., always available but explanations are incomprehensible).

### XLA Categories

Five dimensions of human-AI experience:

1. **Response Quality** — How helpful are the AI's outputs?
2. **Explanation Clarity** — Can humans understand why the AI made that recommendation?
3. **Escalation Smoothness** — When AI escalates to human, is context transfer complete?
4. **Trust Calibration** — Does AI communicate confidence appropriately?
5. **Override Ease** — How easy is it for humans to override AI decisions?

### XLA Measurement Methods

- **Subjective Surveys** — Post-interaction ratings (1-5 scale)
- **Objective Telemetry** — Interaction timing, override rates, escalation completeness
- **Comparative Analysis** — Human-AI outcomes vs human-only outcomes
- **Longitudinal Tracking** — Experience quality over time as AI learns

## Instructions

### 1. Identify Human-AI Touchpoints

From the AI Persona definition Section 9, extract every point where a human interacts with the persona:

```yaml
touchpoints:
  - touchpoint_id: "TP-QI-01"
    persona: "Quality Inspection AI"
    human_role: "Plant Manager"
    interaction_type: "Escalation for approval"
    frequency: "5-10 times per week"
    criticality: "High (production stop decisions)"

  - touchpoint_id: "TP-QI-02"
    persona: "Quality Inspection AI"
    human_role: "Quality Engineer"
    interaction_type: "Daily report review"
    frequency: "Once per day"
    criticality: "Medium (trend monitoring)"

  - touchpoint_id: "TP-QI-03"
    persona: "Quality Inspection AI"
    human_role: "Quality Director"
    interaction_type: "Weekly performance review"
    frequency: "Weekly"
    criticality: "Medium (trust calibration)"
```

### 2. Define XLA Metrics Per Touchpoint

For each touchpoint, specify measurable experience targets:

#### Touchpoint: Escalation for Approval (TP-QI-01)

**Response Quality XLA**
```yaml
metric: "Recommendation Actionability"
definition: "Plant Manager can make informed decision using only information provided by AI"
measurement: "Post-decision survey: 'Did the AI provide sufficient context?' (1-5 scale)"
target: ">= 4.2 / 5.0"
review_cadence: "Monthly average"
escalation_trigger: "< 3.5 for two consecutive months"
```

**Explanation Clarity XLA**
```yaml
metric: "Explanation Comprehensibility"
definition: "Plant Manager understands why AI recommended this action"
measurement: "Post-decision survey: 'Was the reasoning clear?' (1-5 scale)"
target: ">= 4.0 / 5.0"
review_cadence: "Monthly average"
escalation_trigger: "< 3.5 for two consecutive months"
data_points:
  - Confidence percentage provided (yes/no)
  - Evidence links included (count)
  - Alternative options presented (count)
  - Trade-offs explained (yes/no)
```

**Escalation Smoothness XLA**
```yaml
metric: "Context Transfer Completeness"
definition: "Human receives complete context without needing to ask follow-up questions"
measurement: "Objective telemetry: Number of clarifying questions before decision"
target: "<= 1 clarifying question on average"
review_cadence: "Weekly"
escalation_trigger: "> 2 questions per escalation for two consecutive weeks"
context_checklist:
  - Batch ID and material specification
  - Affected assemblies list with serial numbers
  - Failure test results with tolerances
  - Customer impact assessment
  - Financial impact estimate
  - Recommended action with alternatives
```

**Trust Calibration XLA**
```yaml
metric: "Confidence Communication Accuracy"
definition: "AI expresses uncertainty appropriately — not overconfident, not paralyzing"
measurement: "Objective telemetry: Correlation between stated confidence and actual outcome"
target: "Confidence-calibrated accuracy within 10% (e.g., 80% confidence → 75-85% correct)"
review_cadence: "Quarterly"
calculation:
  - Track: (AI stated confidence, human decision, actual outcome)
  - Plot: Confidence level vs outcome accuracy
  - Target: Tight calibration curve
```

**Override Ease XLA**
```yaml
metric: "Override Friction"
definition: "Human can override AI recommendation without excessive steps or guilt"
measurement: "Objective telemetry: Override process completion time"
target: "< 30 seconds from decision to override logged"
review_cadence: "Monthly"
process_steps:
  - Click 'Override' button (1 click)
  - Provide reason (free text, 1-3 sentences)
  - Confirm (1 click)
  - No secondary approval needed
  - No warning dialogs
```

### 3. Design Measurement Instruments

For each XLA metric, specify how it's measured:

#### Subjective Survey Instrument

```yaml
survey_instrument:
  touchpoint: "TP-QI-01 (Escalation for approval)"
  trigger: "Immediately after decision"
  delivery: "Modal dialog in Digital Twin dashboard"
  questions:
    - q1: "The AI provided sufficient context for my decision."
      scale: "1 (Strongly Disagree) to 5 (Strongly Agree)"
    - q2: "The AI's reasoning was clear and understandable."
      scale: "1 (Strongly Disagree) to 5 (Strongly Agree)"
    - q3: "The AI communicated its level of confidence appropriately."
      scale: "1 (Strongly Disagree) to 5 (Strongly Agree)"
    - q4_optional: "What would have made this interaction better?"
      type: "Free text (optional)"
  frequency: "Every interaction for first 50 decisions, then 20% sample"
  anonymity: "Results aggregated, not traced to individual"
```

#### Objective Telemetry Capture

```yaml
telemetry_events:
  - event: "escalation_presented"
    timestamp: "ISO 8601"
    session_id: "uuid"
    persona_id: "PERS-SPINY-QI-01"
    touchpoint_id: "TP-QI-01"
    context_fields_count: int
    confidence_stated: float (0.0-1.0)
    alternatives_count: int

  - event: "clarifying_question_asked"
    timestamp: "ISO 8601"
    session_id: "uuid"
    question_text: string (for categorization)

  - event: "decision_made"
    timestamp: "ISO 8601"
    session_id: "uuid"
    decision: "approve | reject | defer"
    override: boolean
    override_reason: string (if applicable)

  - event: "outcome_recorded"
    timestamp: "ISO 8601"
    session_id: "uuid"
    actual_result: "correct | incorrect | indeterminate"
    impact_severity: "none | minor | major | critical"
```

### 4. Create XLA Dashboard Specification

Design a dashboard view showing XLA performance:

```yaml
dashboard_layout:
  title: "Quality Inspection AI - Experience Dashboard"
  audience: "Quality Director, Plant Manager"
  refresh_rate: "Daily"

  sections:
    - section: "Overall Experience Score"
      visualization: "Gauge"
      metric: "Composite XLA Score"
      calculation: "Weighted average of 5 XLA categories"
      target: ">= 4.0 / 5.0"
      current_value: "4.3 / 5.0"
      trend: "7-day moving average"

    - section: "Escalation Quality"
      visualization: "Time series line chart"
      metrics:
        - "Recommendation Actionability (TP-QI-01)"
        - "Explanation Comprehensibility (TP-QI-01)"
      time_range: "Last 90 days"
      target_line: "4.0 threshold"

    - section: "Context Transfer Completeness"
      visualization: "Bar chart"
      metric: "Clarifying questions per escalation"
      grouping: "By week"
      target: "<= 1.0 average"

    - section: "Trust Calibration"
      visualization: "Scatter plot"
      x_axis: "AI Stated Confidence (%)"
      y_axis: "Actual Outcome Accuracy (%)"
      ideal_line: "y = x (perfect calibration)"
      data_points: "Last 100 decisions"

    - section: "Override Patterns"
      visualization: "Stacked area chart"
      metrics:
        - "Decisions approved as recommended"
        - "Decisions rejected (overridden)"
        - "Decisions deferred"
      time_range: "Last 90 days"
      insight: "Increasing override rate may indicate trust erosion"

    - section: "Recent Feedback"
      visualization: "Text feed"
      content: "Latest free-text survey responses (Q4)"
      filter: "Last 7 days"
      anonymized: true
```

### 5. Link XLAs to Authority Progression

Define how XLA performance gates authority level promotion:

```yaml
authority_progression_gates:
  current_level: 1  # Analyst (proposes actions)
  target_level: 2   # Operator (executes within bounds)

  xla_requirements_for_promotion:
    - metric: "Overall Experience Score"
      current: 4.3
      target: ">= 4.2 for 8 consecutive weeks"
      status: "MET"

    - metric: "Context Transfer Completeness"
      current: 0.8 clarifying questions per escalation
      target: "<= 1.0 for 8 consecutive weeks"
      status: "MET"

    - metric: "Trust Calibration"
      current: "Confidence within 8% of actual outcomes"
      target: "Within 10%"
      status: "MET"

    - metric: "Override Rate"
      current: "12% of recommendations overridden"
      target: "< 15% (stability, not suppression)"
      status: "MET"
      note: "We WANT some overrides — means humans are engaged and trust is genuine, not blind compliance"

  additional_requirements:
    - "Shadow mode for 50 decisions minimum" (status: MET, 78 decisions)
    - "Vanilla-Agent test passed" (status: MET)
    - "No critical incidents attributed to AI error" (status: MET)
    - "Business Owner approval" (status: PENDING)
```

### 6. Design XLA Improvement Loops

When XLAs fall below targets, trigger improvement actions:

```yaml
improvement_triggers:
  - trigger_condition: "Explanation Comprehensibility < 3.5 for two consecutive months"
    investigation_actions:
      - "Review free-text feedback for themes"
      - "Interview 3 Plant Managers for detailed input"
      - "Compare high-rated vs low-rated explanations"
      - "A/B test alternative explanation formats"
    improvement_options:
      - "Add visual diagrams to escalation context"
      - "Include historical comparison data"
      - "Simplify technical jargon"
      - "Highlight key decision factors in bold"
    owner: "AI RM Steward + UX Designer"
    deadline: "30 days from trigger"

  - trigger_condition: "Context Transfer Completeness > 2 clarifying questions"
    investigation_actions:
      - "Categorize types of clarifying questions"
      - "Identify missing context fields"
      - "Update context checklist"
    improvement_options:
      - "Add missing fields to escalation payload"
      - "Provide contextual help tooltips"
      - "Pre-populate common follow-up questions"
    owner: "MCP Server Team + AI RM Steward"
    deadline: "14 days from trigger"
```

### 7. Validate XLA Completeness

Check that XLA design is comprehensive:

- [ ] All human-AI touchpoints from persona definition Section 9 have XLA metrics
- [ ] All 5 XLA categories covered (Response, Explanation, Escalation, Trust, Override)
- [ ] Mix of subjective (survey) and objective (telemetry) measures
- [ ] Targets are specific, measurable, and realistic
- [ ] Measurement instruments are non-intrusive (don't slow down work)
- [ ] Dashboard provides actionable insights
- [ ] XLA performance linked to authority progression
- [ ] Improvement loops defined for below-target performance
- [ ] Human override ability explicitly supported (not suppressed)

### 8. Document XLA Package

Produce a complete XLA specification:

```markdown
# XLA Definition: Quality Inspection AI (PERS-SPINY-QI-01)

## Overview

This XLA specification defines how humans will experience working with the Quality Inspection AI Persona at SpinnyThings. It covers all touchpoints from daily report review through critical production stop escalations.

## Touchpoint Summary

- **TP-QI-01**: Escalation for approval (Plant Manager, 5-10x/week, High criticality)
- **TP-QI-02**: Daily report review (Quality Engineer, 1x/day, Medium criticality)
- **TP-QI-03**: Weekly performance review (Quality Director, 1x/week, Medium criticality)

## XLA Metrics

[Full table of metrics from step 2]

## Measurement Instruments

[Survey questions and telemetry events from step 3]

## Dashboard Specification

[Dashboard layout from step 4]

## Authority Progression Gates

[Gates from step 5]

## XLA Improvement Loops

[Triggers and actions from step 6]

## Approval

- **Experience Owner**: Quality Director, SpinnyThings
- **AI RM Steward**: AI RM Lab Lead
- **Approval Date**: [YYYY-MM-DD]
```

## Output

A complete XLA package with:
- XLA metrics for all human-AI touchpoints
- Measurement instruments (surveys + telemetry)
- Dashboard specification
- Authority progression gates linked to XLA performance
- Improvement triggers and remediation actions
- Validation checklist completed

**File location**: `docs/architecture/bsa/generated/xla/[persona-id]-xla.md`

## Relationship to Other Skills

- **Upstream**: Requires `ai-persona-definition` (Section 9: Interacting Services and Actors)
- **Upstream**: Requires `measurement-blueprint` (Tier 3: Experiential & Operational)
- **Downstream**: Feeds authority progression decisions
- **Downstream**: Feeds persona lifecycle management (promotion/demotion criteria)
- **Related**: `bpmn-ai-process-generator` (human approval tasks become XLA touchpoints)
- **Related**: `readiness-scorecard` (XLA design is part of Checkpoint 6: Measurement hooks)
