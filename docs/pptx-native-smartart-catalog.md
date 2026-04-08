# pptx_native SmartArt Layout Catalog

> This file is auto-generated from `src/smartart_pptx_native/layouts/catalog.json`. Do not edit by hand — run `python -m src.smartart_pptx_native.layouts.catalog_markdown` to regenerate.

**Catalog version:** `1.0.0`

**v1 layouts:** 3 — Basic Process, Basic Cycle, Organization Chart

## Summary

| Layout | Category | Data shape | Max nodes | Max label chars | Backs |
|---|---|---|---:|---:|---|
| **Basic Process** (`process1`) | Process | `flat_list` | 9 | 24 | `flowchart` |
| **Basic Cycle** (`cycle2`) | Cycle | `flat_list` | 8 | 20 | `cycle` |
| **Organization Chart** (`orgChart1`) | Hierarchy | `hierarchical` | 25 | 32 | `org_chart` |

---

# Layouts in Detail

## Basic Process (`process1`)

- **Category:** Process
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/process1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-9 nodes, max 24 chars per label
- **Seed file:** `tests/fixtures/smartart_seeds/process1_seed.pptx`
- **Builder module:** `src.smartart_pptx_native.layouts.process`

### Visual character

Horizontal row of connected rounded rectangles with chevron arrows between them. Boxes share a single accent colour by default; PowerPoint reflows them into 2 rows automatically beyond ~7 steps.

### When to use

- Sequential processes where each step depends on the previous one
- Pipelines with a clear start and end
- How-to explanations with 3-7 stages
- Methodology walkthroughs where order matters

### When NOT to use

- Cyclical processes (use cycle2)
- Hierarchical decisions (use orgChart1)
- Timelines with date anchors (use basicTimeline1)
- More than 9 steps (the visual becomes unreadable)
- Parallel or concurrent steps (no native representation in this layout)

### Capacity rationale

PowerPoint shrinks labels above 24 chars to unreadable sizes on 16:9 slides. Empirically determined during manual gating — revisit if a future layout reflows more gracefully.

### Selector rationale template

> process1 is the right choice when the content describes a sequence of {n} steps from "{first}" to "{last}" where order matters. Delivers editable SmartArt — speaker can add/rename/reorder steps in PowerPoint after delivery.

### Backs these graphic types

- `flowchart` (when conditions met)

**Selector routes to this layout when:** graphic_type == 'flowchart' AND enrichment_tier == 'pure_programmatic' AND node_count <= 9 AND max(label_length) <= 24

---

## Basic Cycle (`cycle2`)

- **Category:** Cycle
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/cycle2`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 3-8 nodes, max 20 chars per label
- **Seed file:** `tests/fixtures/smartart_seeds/cycle1_seed.pptx`
- **Builder module:** `src.smartart_pptx_native.layouts.cycle`

### Visual character

Circles arranged in a ring with directional arrows connecting each to the next. Flows around clockwise from a 12 o'clock starting position. Conveys iteration or recurring process.

### When to use

- Iterative processes with no clear start or end (they loop)
- Continuous improvement cycles (Plan-Do-Check-Act, OODA)
- Recurring workflows with 3-6 stages
- Feedback loops where each stage feeds the next

### When NOT to use

- Linear sequences with a definite end (use process1)
- Hierarchical structures (use orgChart1)
- More than 8 stages (the ring becomes cluttered)
- Parallel or branching flows (cycle is strictly sequential)

### Capacity rationale

Cycle boxes are smaller than process boxes because they sit in a ring rather than a row, and the ring shrinks as node count grows. 20 chars determined empirically during the spike 2 manual gate.

### Selector rationale template

> cycle2 is the right choice when the content describes an iterative {n}-stage loop from "{first}" back around. Delivers editable SmartArt — speaker can add/rename stages and PowerPoint automatically redistributes them around the ring.

### Backs these graphic types

- `cycle` (when conditions met)

**Selector routes to this layout when:** graphic_type == 'cycle' AND enrichment_tier == 'pure_programmatic' AND node_count <= 8 AND max(label_length) <= 20

---

## Organization Chart (`orgChart1`)

- **Category:** Hierarchy
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/orgChart1`
- **Data shape:** `hierarchical`
- **Special node types:** `asst`
- **Capacity:** 3-25 nodes, max 32 chars per label
- **Seed file:** `tests/fixtures/smartart_seeds/orgChart1_seed.pptx`
- **Builder module:** `src.smartart_pptx_native.layouts.org_chart`

### Visual character

Classic organization chart — root node at top, subordinates branching downward in a tree. Assistant nodes render to the side of their parent with a right-angle connector, distinct from the regular subordinate row below.

### When to use

- Reporting structures and management hierarchies
- Team compositions with clear parent-child relationships
- Any tree-shaped content with 3+ levels of nesting
- Structures that include assistants sitting outside the main reporting line

### When NOT to use

- Flat lists of peers (use process1 or cycle2)
- Cyclic relationships (use cycle2)
- More than 4 levels deep or more than 25 total nodes (visual becomes unreadable at 16:9)
- Matrix or network relationships (orgChart1 is strictly a tree)

### Capacity rationale

Org chart boxes are wider than process/cycle boxes and can accommodate longer role titles. Empirically determined during the spike 4 manual gate — revisit if deep trees force smaller boxes.

### Selector rationale template

> orgChart1 is the right choice when the content describes a hierarchy of {n} roles. Delivers editable SmartArt — speaker can add subordinates or assistants, promote/demote, and restructure the tree in PowerPoint after delivery.

### Backs these graphic types

- `org_chart` (when conditions met)

**Selector routes to this layout when:** graphic_type == 'org_chart' AND enrichment_tier == 'pure_programmatic' AND total_nodes <= 25 AND max_depth <= 4

---
