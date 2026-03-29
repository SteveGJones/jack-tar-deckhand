---
name: measurement-blueprint
description: Creates 5-tier measurement hierarchies connecting AI Persona activity to business outcomes. Use this when designing the measurement framework for a service or AI Persona, including KPI attribution models.
---

# Measurement Blueprint

This skill creates a 5-tier measurement blueprint that connects an AI Persona's or service's operational activity all the way up to strategic business objectives. It uses the methodology's 12 measure types across 5 tiers and includes multi-contributor KPI attribution.

## When to Use

- After defining an AI Persona (Section 10 of the 19-section template)
- When designing measurement for a new or existing service
- When multiple contributors (human + AI) share a KPI and need attribution
- During Chapter 10-11 measurement design workshops

## Template Reference

The measurement blueprint template is at: `methodology_draft/templates/Measurement-Blueprint-Template.md`

## Instructions

### 1. Start at Tier 1 (Top Down)

Always start from the strategic objective, never from operational metrics.

**Tier 1: Strategic Direction** — WHAT we aim to achieve
| Measure Type | Definition | Example |
|-------------|-----------|---------|
| OBJECTIVE | Qualitative goal | "Protect on-shelf availability" |
| FINANCIAL_METRIC | Business stakes in currency | "Lost sales due to out-of-stocks below $2M annually" |

Ownership: Business Owners (C-suite, VP)
Review cadence: Quarterly Portfolio Council

### 2. Define Tier 2 (Results)

**Tier 2: Performance & Outcome** — RESULTS we measure
| Measure Type | Definition | Example |
|-------------|-----------|---------|
| KEY_RESULT | Quantified target | "Increase shelf availability from 91% to 96%" |
| KPI_OUTCOME | Lagging indicator | "Monthly revenue per store" |
| VALUE_CONTRIBUTION | Financial impact of AI | "$735K attributable to AI Persona" |
| COST_IMPACT | Cost savings or avoidance | "$120K reduced waste from predictive ordering" |

Ownership: Service Owners, AI Persona Owners
Review cadence: Monthly Ops Council

### 3. Design Tier 3 (Experience & Operations)

**Tier 3: Experiential & Operational** — HOW it FEELS and RUNS
| Measure Type | Definition | Example |
|-------------|-----------|---------|
| XLA | Human experience quality | "Merchandiser satisfaction with AI recommendations > 4.0/5.0" |
| SLA | Operational performance | "99.5% uptime; alerts within 5 minutes" |

Ownership: Experience Owner, AI Ops Lead
Review cadence: Weekly sprint retrospectives

**Key distinction:** XLAs measure how humans experience working with the AI. SLAs measure whether the AI operates within technical bounds. Both are needed.

### 4. Identify Tier 4 (Levers)

**Tier 4: Actionable Inputs** — LEVERS we adjust
| Measure Type | Definition | Example |
|-------------|-----------|---------|
| LEADING_INDICATOR | Predictive metric | "At-risk items identified per week" |
| VALUE_LEVER | Adjustable parameter | "Risk score threshold for alerting" |

Ownership: AI Ops Lead, Data Steward
Review cadence: Daily operational standups

These are the dials you turn to influence Tier 3 outcomes.

### 5. Map Tier 5 (Context)

**Tier 5: Contextual Factors** — RISKS and DATA QUALITY
| Measure Type | Definition | Example |
|-------------|-----------|---------|
| RISK_LEVEL | Threat to performance | "Reputational risk of false positives" |
| DATA_QUALITY_ISSUE_IMPACT | Data freshness/completeness/accuracy | "CRM completeness > 95% required" |

Ownership: Risk Steward, Data Gov Lead
Review cadence: Daily monitoring, monthly attestation

### 6. Connect the Tiers

Draw explicit connections showing how:
- Tier 4 **levers** drive Tier 3 **agreements**
- Tier 3 agreements support Tier 2 **outcomes**
- Tier 2 outcomes align to Tier 1 **objectives**
- Tier 5 **context** can undermine any tier above

Every measure should have a clear upward connection. If a metric doesn't connect to a Tier 1 objective, challenge whether it's needed.

### 7. Design Multi-Contributor Attribution

When multiple actors (human + AI) contribute to a shared KPI:

1. **Identify the shared KPI** — Which Tier 2 measure is shared?
2. **Map direct contributions** — What does each contributor directly control?
3. **Calculate attribution** — Use adoption-based capping:
   - AI contribution = direct measure impact x adoption rate
   - Example: 96.2% availability x $7,650 revenue per point = $735K AI-attributable
4. **Validate with Tier 3** — XLA scores confirm humans trust and use AI recommendations
5. **Document the model** — Clear formula, data sources, review cadence

Record in the blueprint:
```markdown
| Contributor | Direct Measure | Weight | Attribution Method |
|-------------|---------------|--------|-------------------|
| AI Persona | Shelf availability % | 30% | Adoption-capped direct impact |
| Store Ops team | Restock execution time | 40% | Direct operational metric |
| Supply Chain | Delivery fill rate | 30% | Upstream fulfilment metric |
```

### 8. Define Escalation Triggers

At each tier, define what warrants escalation:

| Tier | Trigger | Escalation To | Response Time |
|------|---------|--------------|---------------|
| Tier 2 | KPI misses target by >10% | Business Owner | Within 48 hours |
| Tier 3 | XLA drops below 3.5/5.0 | Experience Owner | Within 1 week |
| Tier 3 | SLA breach (uptime <99%) | AI Ops Lead | Within 4 hours |
| Tier 4 | Leading indicator anomaly | AI Ops Lead | Within 24 hours |
| Tier 5 | Data quality below threshold | Data Steward | Within 24 hours |

### 9. Complete the Blueprint Template

Fill in the full template at `methodology_draft/templates/Measurement-Blueprint-Template.md` with all 8 sections:
1. Mandate Recap
2. Tier Lineage Snapshot
3. Primary Direct Measure Detail
4. Supporting Measures & Adoption
5. Volume, Capacity, and Load Shedding
6. Context, Risk, and Safeguards
7. Attribution & Experiments
8. Governance & Escalation

## Output

A completed measurement blueprint with:
- All 5 tiers populated with specific measures
- Clear tier-to-tier connections
- Multi-contributor attribution model (if applicable)
- Escalation triggers at each tier
- Ownership and review cadences defined
