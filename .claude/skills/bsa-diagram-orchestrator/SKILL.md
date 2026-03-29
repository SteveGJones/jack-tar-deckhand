---
name: bsa-diagram-orchestrator
description: Coordinates batch SVG diagram generation across multiple canonical models. Wraps the existing service-architecture-renderer skill to generate L0 + all L1 diagrams for a company or the entire supply chain in one invocation.
---

# BSA Diagram Orchestrator

This skill coordinates batch generation of SVG architecture diagrams across one or more canonical models. Instead of manually invoking `service-architecture-renderer` for each diagram, this skill discovers all renderable views in a model (or set of models) and generates them all in one pass.

## When to Use

- After completing or updating canonical models and needing all diagrams refreshed
- When preparing a complete architecture review package with all visual artifacts
- When a new company model is added and needs its full diagram set
- As part of the `bsa-pipeline-orchestrator` end-to-end pipeline
- Before stakeholder presentations that need current visual architecture

## Prerequisites

- Python 3.8+
- Graphviz installed (`brew install graphviz` or `apt install graphviz`)
- The renderer script at: `{methodology_repo}/distribution/diagram-tools/service_architecture_renderer.py`
- Style config at: `.claude/agents/references/schemas/style-config.json`

## Instructions

### 1. Select Scope

Choose the scope of diagram generation:

| Scope | Input | Diagrams Generated |
|-------|-------|--------------------|
| Single model | One `.json` file | L0 + all L1 views for that model |
| All company models | `docs/architecture/bsa/canonical-models/*.json` | L0 + all L1 for every company |
| Collaborative model | `acid-collaborative.json` | L0 network view + L1 per company node |
| Full suite | All of the above | Complete diagram set for entire architecture |

### 2. Discover Renderable Views

For each canonical model, identify all views to render:

1. **L0 Enterprise View**: Always generated — shows all level-0 services
2. **L1 Domain Views**: One per level-0 service that has level-1 children
3. **L2+ Views** (if present): One per level-1 service that has deeper children

Build a render manifest:

```markdown
### Render Manifest: [model name]

| # | View | Parent Service | Level | Output File |
|---|------|---------------|-------|-------------|
| 1 | Enterprise L0 | — | 0 | [model-id]-l0.svg |
| 2 | [Domain] L1 | [parent-id] | 1 | [model-id]-[parent-id]-l1.svg |
| 3 | [Sub-domain] L2 | [parent-id] | 2 | [model-id]-[parent-id]-l2.svg |
```

### 3. Generate Diagrams

For each entry in the render manifest, invoke the renderer:

```bash
# L0 Enterprise view
python3 {methodology_repo}/distribution/diagram-tools/service_architecture_renderer.py \
  <model.json> --l0 <output-dir>/<model-id>-l0.svg

# L1+ Drill-down views
python3 {methodology_repo}/distribution/diagram-tools/service_architecture_renderer.py \
  <model.json> <parent-service-id> <level> <output-dir>/<model-id>-<parent-id>-l<level>.svg
```

### 4. Output Directory Structure

Write all diagrams to a **flat** directory at:
`docs/architecture/bsa/diagrams/`

This matches the existing structure on disk (141+ SVGs). File names encode the model and view:

```
docs/architecture/bsa/diagrams/
├── aerovista-l0.svg
├── aerovista-core-operations-l1.svg
├── aerovista-quality-management-l1.svg
├── aerovista-supply-chain-management-l1.svg
├── spinnythings-l0.svg
├── spinnythings-manufacturing-l1.svg
├── acid-collaborative-l0.svg
├── acid-collaborative-aerovista-l1.svg
└── _manifest.md
```

**Naming convention**: `{model-id}-{domain-slug}-l{level}.svg` for drill-downs, `{model-id}-l0.svg` for enterprise views. Use kebab-case for domain slugs derived from the service `name`.

### 5. Generate Diagram Manifest

After all diagrams are generated, produce a manifest file at `docs/architecture/bsa/diagrams/_manifest.md`:

```markdown
# BSA Diagram Manifest

**Generated:** [date]
**Renderer:** service-architecture-renderer

## Diagrams by Company

### [Company Name] ([model file])

| View | Level | Parent | File | Entities | Interactions |
|------|-------|--------|------|----------|--------------|
| Enterprise | L0 | — | [path] | [count] | [count] |
| [Domain] | L1 | [parent] | [path] | [count] | [count] |

### Summary
- Total models processed: [count]
- Total diagrams generated: [count]
- Total L0 views: [count]
- Total L1+ views: [count]
```

### 6. Handling Errors

If a diagram fails to render:
- Log the error with the model file, view, and error message
- Continue generating remaining diagrams (do not abort the batch)
- Include failed diagrams in the manifest with status "FAILED" and error reason
- Common issues: missing Graphviz, malformed model JSON, empty service level

### 7. Incremental Mode

When only one model has changed, use incremental mode:
1. Read the existing manifest
2. Identify which model changed (by file modification time or explicit parameter)
3. Re-generate only diagrams for the changed model
4. Update the manifest with new timestamps

## Relationship to Other Skills

- **Wraps**: `service-architecture-renderer` (this skill orchestrates multiple invocations)
- **Upstream**: `canonical-model-manager` (creates models), `canonical-model-validator` (validates before rendering)
- **Parallel**: `bsa-documentation-generator` (produces markdown docs alongside SVG diagrams)
- **Downstream**: `bsa-pipeline-orchestrator` (includes this skill in the pipeline)

## Output

A complete set of SVG architecture diagrams covering all renderable views across the selected canonical models, plus a manifest documenting every diagram generated.
