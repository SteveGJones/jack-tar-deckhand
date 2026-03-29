# Data Product Definition Template

> Duplicate this file for each operational or collaborative data product. Start at the top and move section-by-section so the discovery team can trace the lineage from purpose to ownership, then to contracts and lifecycle controls. Favor tables with additional rows over long-form prose so the information can be scanned and audited quickly.
>
> **How to populate this template**
> 1. **Identity first:** capture the name, tier, owner, and regulatory posture before filling in downstream details so everyone references the same artifact.
> 2. **Clarify intent:** document each business purpose, decision, and KPI individually—add rows for every distinct use so producers, augmenters, and consumers understand the demand signal they must satisfy.
> 3. **Map composition:** list every contributing operational product or upstream system, including transformations and latency expectations, to show how collaborative slices are assembled.
> 4. **Assign roles:** record all services (or AI Personas) that produce, augment, or consume the product, plus the accountable human owner for each role, and highlight any “fake augmenters” that are correcting upstream errors.
> 5. **Define trust:** complete the contract, cost-of-quality, issue diagnostics, and lifecycle tables to make accuracy expectations, financial impacts, and remediation workflows explicit.
> 6. **Maintain change history:** keep the dependency log and glossary updated whenever schemas, sources, or regulations shift so downstream services can adapt without surprises.

## 1. Product Overview
### 1.1 Identity & Ownership (single entries)
| Field | Entry |
| --- | --- |
| Data Product Name |  |
| Tier | Operational / Collaborative |
| Product Owner (Service + Accountable Person) |  |
| Version / Last Updated |  |
| Security Classification / Regulatory Category |  |

### 1.2 Business Purpose & Decisions (multi-entry)
| Decision / Use Case | Description | Producer / Augmenter / Consumer Roles Involved |
| --- | --- | --- |
|  |  |  |
|  |  |  |

### 1.3 KPI & Measurement Alignment (multi-entry)
| KPI / Measure | How This Product Supports It | Owner of KPI |
| --- | --- | --- |
|  |  |  |
|  |  |  |

### 1.4 Related Processes & Journeys (multi-entry)
| Process / Journey | Role of This Product | Notes |
| --- | --- | --- |
|  |  |  |
|  |  |  |

## 2. Composition & Lineage
| Source Product or System of Record | Producer Service | Key Data Elements Included | Transformations / Filters | Latency Requirement | Regulatory / Residency Constraints |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

> Add rows for each contributing operational product or upstream system. Use this table to illustrate how collaborative products are assembled from operational ones.

## 3. Producer / Augmenter / Consumer Matrix
| Role | Service / AI Persona | Accountable Owner | Purpose / Decisions Made | Interaction Channel (API, Event, UI, etc.) | Data Cost of Inaccuracy & KPI Impact |
| --- | --- | --- | --- | --- | --- |
| Producer |  |  |  |  |  |
| Augmenter |  |  |  |  |  |
| Consumer |  |  |  |  |  |
| (add more rows as needed) |  |  |  |  |  |

> Use this table to identify fake augmenters: if a role is correcting upstream errors rather than adding net-new value, note the remediation in Section 6.

## 4. Data Contract & Quality SLAs
| Metric | Threshold / Target | Monitoring Mechanism | Alert Channel & Escalation | Notes |
| --- | --- | --- | --- | --- |
| Freshness / Latency |  |  |  |  |
| Accuracy |  |  |  |  |
| Completeness |  |  |  |  |
| Validity / Schema Compliance |  |  |  |  |
| Provenance / Lineage Capture |  |  |  |  |
| Other |  |  |  |  |

## 5. Cost-of-Quality Attribution
| Interaction Stage | Potential Business Impact of Poor Data | KPI / Measure Affected | Cost Estimation Method | Root Cause Owner | Chargeback Mechanism |
| --- | --- | --- | --- | --- | --- |
| Producer |  |  |  |  |  |
| Augmenter |  |  |  |  |  |
| Consumer |  |  |  |  |  |
| Downstream Escalations |  |  |  |  |  |

## 6. Issue Diagnostics & Remediation Plan
| Issue / "Fake Augmenter" Finding | Evidence & Metrics | Assigned Owner | Remediation Actions | Target Completion |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 7. Lifecycle & Feedback Loops
| Activity | Cadence | Responsible Service | Tooling / Automation | Notes |
| --- | --- | --- | --- | --- |
| Data refresh |  |  |  |  |
| Model retraining / AI tuning |  |  |  |  |
| Contract review |  |  |  |  |
| Access audit / compliance review |  |  |  |  |
| KPI outcome review |  |  |  |  |

## 8. Dependency & Change Management Log
| Date | Change Description | Impacted Consumers | Communication Plan | Approval |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 9. Glossary & Data Element Notes
| Field / Attribute | Definition | Sensitive? (Y/N) | Steward | Reference Documentation |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

---

**Usage Tips**
- Keep the tables as the primary artifact; add rows rather than paragraphs when new services, KPIs, or controls emerge.
- Link each KPI to the organization’s measurement catalog so cost-of-quality statements are auditable.
- When collaborative products are composed from multiple operational datasets, ensure every upstream producer signs the contract in Section 4 and understands the attribution logic in Section 5.
