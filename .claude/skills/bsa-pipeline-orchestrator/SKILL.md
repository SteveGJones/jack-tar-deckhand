---
name: bsa-pipeline-orchestrator
description: End-to-end BSA pipeline — runs canonical-model-validator, cross-model-validator, service-architecture-renderer (all diagrams), bsa-documentation-generator, and methodology-compliance-check in sequence, producing a complete architecture package.
---

# BSA Pipeline Orchestrator

This skill runs the complete BSA architecture pipeline end-to-end, orchestrating all validation, rendering, documentation, and compliance skills in the correct dependency order. It produces a complete architecture package ready for governance review or stakeholder presentation.

## When to Use

- After completing a significant architecture update across one or more canonical models
- When preparing for a Change Advisory Circle review
- When producing a complete architecture package for stakeholders
- Before milestone gates (phase transitions, deployment readiness)
- On a regular cadence (e.g., weekly) to keep all architecture artifacts current

## Pipeline Stages

The pipeline runs these stages in order. Each stage must pass before the next begins:

```
Stage 1: Individual Model Validation
    └── canonical-model-validator (per model)

Stage 2: Cross-Model Validation
    └── cross-model-validator (all models)

Stage 3: Diagram Generation
    └── bsa-diagram-orchestrator (all diagrams)

Stage 4: Documentation Generation
    └── bsa-documentation-generator (per model + cross-reference)

Stage 5: Cross-Reference Index
    └── bsa-cross-reference-index (all models)

Stage 6: Methodology Compliance Check
    └── methodology-compliance-check (overall assessment)

Stage 7: Package Assembly
    └── Collect all outputs into final package
```

## Instructions

### 1. Select Pipeline Scope

Choose the scope before running:

| Scope | Models Included | Output |
|-------|----------------|--------|
| Single company | One company model | Validation + diagrams + docs for that company |
| All companies | All individual company models | Full validation + diagrams + docs per company |
| Full suite | All company models + collaborative model | Complete architecture package |

Default scope is **Full suite**.

### 2. Stage 1: Individual Model Validation

For each canonical model in `docs/architecture/bsa/canonical-models/*.json`:

1. Run `canonical-model-validator` checks
2. Record result: PASS / PASS WITH WARNINGS / FAIL
3. Collect all errors and warnings

**Gate**: If ANY model has errors (FAIL), stop the pipeline and report. Warnings are allowed to proceed.

```markdown
### Stage 1 Results: Individual Model Validation

| Model | Result | Errors | Warnings |
|-------|--------|--------|----------|
| aerovista.json | PASS | 0 | 2 |
| spinnythings.json | PASS WITH WARNINGS | 0 | 4 |
| acid-collaborative.json | FAIL | 3 | 1 |

**Gate Decision:** [PROCEED / HALT — fix errors in acid-collaborative.json]
```

### 3. Stage 2: Cross-Model Validation

Run `cross-model-validator` across all models:

1. Check cross-company interaction reciprocity
2. Check authority consistency
3. Check reference data alignment
4. Reconcile collaborative model against individual models

**Gate**: If cross-model errors exist, stop and report. Warnings proceed.

### 4. Stage 3: Diagram Generation

Run `bsa-diagram-orchestrator` in full suite mode:

1. Discover all renderable views across all models
2. Generate L0 + all L1 diagrams for every model
3. Generate diagram manifest
4. Report any rendering failures

**Gate**: Rendering failures for individual diagrams are warnings (pipeline continues). Total rendering failure is an error (halt).

### 5. Stage 4: Documentation Generation

Run `bsa-documentation-generator` for each model:

1. Generate service catalogue per model
2. Generate AI Persona summaries per model
3. Generate interaction matrices per model
4. Generate complete architecture packs

No gate — documentation generation always succeeds if models are valid.

### 6. Stage 5: Cross-Reference Index

Run `bsa-cross-reference-index` across all models:

1. Build persona index
2. Build SOP index
3. Build interaction index
4. Build company connectivity matrix
5. Generate quick-lookup sections

No gate — index generation always succeeds if models are valid.

### 7. Stage 6: Methodology Compliance Check

Run `methodology-compliance-check` using:

1. The validated canonical models
2. The generated diagrams and documentation
3. Any existing persona definitions, readiness scorecards, and dependency registers

Record the compliance verdict: Green / Amber / Red.

### 8. Stage 7: Package Assembly

Collect pipeline-specific outputs into `docs/architecture/bsa/generated/`. Diagrams and per-company documentation remain in their existing locations (not duplicated):

```
docs/architecture/bsa/generated/
├── _pipeline-report.md              ← Overall pipeline results
├── validation/
│   ├── aerovista-validation.md
│   ├── spinnythings-validation.md
│   ├── cross-model-validation.md
│   └── ...
├── cross-reference-index.md
└── compliance-report.md

docs/architecture/bsa/diagrams/       ← Existing location (flat, not duplicated)
├── _manifest.md                      ← Updated by Stage 3
├── aerovista-l0.svg
└── ...

docs/architecture/bsa/[company]/      ← Existing location (not duplicated)
├── _service-catalogue.md             ← Generated by Stage 4
├── _ai-persona-summary.md
└── _architecture-pack.md
```

**Key principle**: The `generated/` directory only contains pipeline-specific artifacts (validation reports, cross-reference index, compliance report, pipeline report). Diagrams and documentation are written to their canonical existing locations.

### 9. Pipeline Report

Generate the master pipeline report at `docs/architecture/bsa/generated/_pipeline-report.md`:

```markdown
# BSA Architecture Pipeline Report

**Run Date:** [date]
**Scope:** [Full Suite / Single Company / All Companies]
**Overall Result:** [GREEN / AMBER / RED]

## Pipeline Summary

| Stage | Skill | Result | Duration | Errors | Warnings |
|-------|-------|--------|----------|--------|----------|
| 1 | canonical-model-validator | PASS | — | 0 | 6 |
| 2 | cross-model-validator | PASS WITH WARNINGS | — | 0 | 3 |
| 3 | bsa-diagram-orchestrator | PASS | — | 0 | 0 |
| 4 | bsa-documentation-generator | PASS | — | 0 | 0 |
| 5 | bsa-cross-reference-index | PASS | — | 0 | 0 |
| 6 | methodology-compliance-check | AMBER | — | 0 | 5 |

## Models Processed
[List of all models with versions]

## Artifacts Generated
- Validation reports: [count]
- SVG diagrams: [count]
- Documentation files: [count]
- Cross-reference index: 1

## Warnings Summary
[Consolidated list of all warnings across all stages]

## Recommendations
[Based on compliance check results, list recommended next actions]
```

### 10. Incremental Mode

For efficiency, support incremental runs:

1. Check file modification times against last pipeline run
2. Only re-validate and re-generate for changed models
3. Always re-run cross-model validation and cross-reference index (they depend on all models)
4. Update the pipeline report with incremental results

## Relationship to Other Skills

This skill **orchestrates** the following skills in sequence:
1. `canonical-model-validator` (Stage 1)
2. `cross-model-validator` (Stage 2)
3. `bsa-diagram-orchestrator` which wraps `service-architecture-renderer` (Stage 3)
4. `bsa-documentation-generator` (Stage 4)
5. `bsa-cross-reference-index` (Stage 5)
6. `methodology-compliance-check` (Stage 6)

## Output

A complete architecture package in `docs/architecture/bsa/generated/` containing validation reports, SVG diagrams, markdown documentation, cross-reference indexes, and a compliance report — all tied together by a master pipeline report.
