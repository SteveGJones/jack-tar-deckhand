# pptx_native SmartArt Layout Catalog

> This file is auto-generated from `src/smartart_pptx_native/layouts/catalog.json`. Do not edit by hand — run `python -m src.smartart_pptx_native.layouts.catalog_markdown` to regenerate.

**Catalog version:** `2.0.0`

**v1 layouts:** 27 — Basic Process, Basic Cycle, Organization Chart, Basic List, Matrix 2, Pyramid 2, Basic Venn, Process Variant 4, Chevron Process, Horizontal Process 4, Horizontal Process 7, Horizontal Process 9, Horizontal Process 11, L-Shaped Process 2, Cycle Variant 8, Hierarchy 2, Hierarchy 4, Hierarchy 5, Hierarchy 6, Horizontal List 6, Vertical List 2, Vertical List 3, Vertical List 4, Vertical List 5, Three-Circle Venn, Basic Funnel, Target Diagram
**Future layouts (non-v1):** 2 — Picture List, Default Layout

## Summary

| Layout | Category | Data shape | Max nodes | Max label chars | Backs |
|---|---|---|---:|---:|---|
| **Basic Process** (`process1`) | Process | `flat_list` | 9 | 24 | `flowchart` |
| **Basic Cycle** (`cycle2`) | Cycle | `flat_list` | 8 | 20 | `cycle` |
| **Organization Chart** (`orgChart1`) | Hierarchy | `hierarchical` | 25 | 32 | `org_chart` |
| **Basic List** (`list1`) | List | `flat_list` | 8 | 30 | `list` |
| **Matrix 2** (`matrix2`) | Matrix | `flat_list` | 4 | 30 | `matrix` |
| **Pyramid 2** (`pyramid2`) | Pyramid | `flat_list` | 6 | 30 | `pyramid` |
| **Basic Venn** (`venn1`) | Relationship | `flat_list` | 8 | 28 | `venn` |
| **Process Variant 4** (`process4`) | Process | `flat_list` | 9 | 24 | `flowchart` |
| **Chevron Process** (`chevron1`) | Process | `flat_list` | 9 | 24 | `chevron_list` |
| **Horizontal Process 4** (`hProcess4`) | Process | `flat_list` | 9 | 24 | `flowchart` |
| **Horizontal Process 7** (`hProcess7`) | Process | `flat_list` | 9 | 24 | `flowchart` |
| **Horizontal Process 9** (`hProcess9`) | Process | `flat_list` | 9 | 24 | `flowchart` |
| **Horizontal Process 11** (`hProcess11`) | Process | `flat_list` | 9 | 24 | `flowchart` |
| **L-Shaped Process 2** (`lProcess2`) | Process | `flat_list` | 9 | 24 | `flowchart` |
| **Cycle Variant 8** (`cycle8`) | Cycle | `flat_list` | 8 | 20 | `cycle` |
| **Hierarchy 2** (`hierarchy2`) | Hierarchy | `hierarchical` | 25 | 32 | `hierarchy` |
| **Hierarchy 4** (`hierarchy4`) | Hierarchy | `hierarchical` | 25 | 32 | `hierarchy` |
| **Hierarchy 5** (`hierarchy5`) | Hierarchy | `hierarchical` | 25 | 32 | `hierarchy` |
| **Hierarchy 6** (`hierarchy6`) | Hierarchy | `hierarchical` | 25 | 32 | `hierarchy` |
| **Horizontal List 6** (`hList6`) | List | `flat_list` | 8 | 30 | `list` |
| **Vertical List 2** (`vList2`) | List | `flat_list` | 8 | 30 | `list` |
| **Vertical List 3** (`vList3`) | List | `flat_list` | 8 | 30 | `list` |
| **Vertical List 4** (`vList4`) | List | `flat_list` | 8 | 30 | `list` |
| **Vertical List 5** (`vList5`) | List | `flat_list` | 8 | 30 | `list` |
| **Three-Circle Venn** (`venn3`) | Relationship | `flat_list` | 8 | 28 | `venn` |
| **Basic Funnel** (`funnel1`) | Relationship | `flat_list` | 8 | 28 | `pipeline_funnel` |
| **Target Diagram** (`target3`) | Relationship | `flat_list` | 8 | 28 | `target` |

---

# Layouts in Detail

## Basic Process (`process1`)

- **Category:** Process
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/process1#1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-9 nodes, max 24 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/process1`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple2#4`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Horizontal row of connected rounded rectangles with chevron arrows between them. The default Basic Process layout.

### When to use

- Sequential processes or workflows
- Step-by-step explanations
- Pipelines with a definite start and end

### When NOT to use

- Cyclical loops (use a Cycle layout)
- Hierarchical relationships (use Hierarchy)
- More than ~9 steps (becomes unreadable)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> process1 is the right choice when the content has {n} process items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `flowchart` (when conditions met)

**Selector routes to this layout when:** graphic_type in (flowchart) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 9] AND max(label_length) <= 24

---

## Basic Cycle (`cycle2`)

- **Category:** Cycle
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/cycle2#2`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 3-8 nodes, max 20 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/cycle2`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple4#7`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Circles arranged in a ring with directional arrows connecting each to the next. Flows clockwise from a 12-o-clock starting position.

### When to use

- Iterative or continuous processes
- Feedback loops
- Recurring workflows with 3-7 stages

### When NOT to use

- Linear sequences with a definite end (use Process)
- Hierarchical structures (use Hierarchy)
- More than ~8 stages (ring becomes cluttered)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> cycle2 is the right choice when the content has {n} cycle items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `cycle` (when conditions met)

**Selector routes to this layout when:** graphic_type in (cycle) AND enrichment_tier == 'pure_programmatic' AND node_count within [3, 8] AND max(label_length) <= 20

---

## Organization Chart (`orgChart1`)

- **Category:** Hierarchy
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/orgChart1#2`
- **Data shape:** `hierarchical`
- **Special node types:** `asst`
- **Capacity:** 3-25 nodes, max 32 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/orgChart1`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple2#3`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/colorful5`

### Visual character

Classic organization chart — root node at top, subordinates branching downward in a tree. Assistant nodes render sideways with a distinctive right-angle connector.

### When to use

- Tree-shaped content with parent-child relationships
- Reporting structures and management hierarchies
- Taxonomies with 2-4 levels of nesting

### When NOT to use

- Flat lists of peers (use List or Process)
- Cyclic relationships (use Cycle)
- More than ~25 total nodes or ~4 levels deep

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> orgChart1 is the right choice when the content describes a hierarchy tree of {n} nodes. Delivers editable SmartArt — speaker can restructure the tree in PowerPoint after delivery.

### Backs these graphic types

- `org_chart` (when conditions met)

**Selector routes to this layout when:** graphic_type in (org_chart) AND enrichment_tier == 'pure_programmatic' AND node_count within [3, 25] AND max(label_length) <= 32

---

## Basic List (`list1`)

- **Category:** List
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/list1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-8 nodes, max 30 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/list1`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Basic bulleted list — items stacked vertically with minimal visual treatment. Good for unordered collections.

### When to use

- Collections of related points without a specific order
- Feature lists, benefit summaries, key takeaways
- Items where emphasis matters more than sequence

### When NOT to use

- Ordered processes (use Process)
- Relationships between items (use Relationship)
- Data with quantitative values (use a chart)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> list1 is the right choice when the content has {n} list items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `list` (when conditions met)

**Selector routes to this layout when:** graphic_type in (list) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 8] AND max(label_length) <= 30

---

## Matrix 2 (`matrix2`)

- **Category:** Matrix
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/matrix2#1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 4-4 nodes, max 30 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/matrix2`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/3d2#1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/colorful1`

### Visual character

Four-quadrant matrix with items arranged in a 2x2 grid. Classic decision-matrix layout.

### When to use

- Four-quadrant frameworks (e.g. 2x2 decision matrices)
- Comparing four categories along two dimensions
- BCG-style matrices, SWOT-like 4-part breakdowns

### When NOT to use

- Sequences or hierarchies (use Process or Hierarchy)
- More than 4 quadrants (no matrix layout fits)
- Sparse grids (use a List or table)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> matrix2 is the right choice when the content has {n} matrix items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `matrix` (when conditions met)

**Selector routes to this layout when:** graphic_type in (matrix) AND enrichment_tier == 'pure_programmatic' AND node_count within [4, 4] AND max(label_length) <= 30

---

## Pyramid 2 (`pyramid2`)

- **Category:** Pyramid
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/pyramid2`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 3-6 nodes, max 30 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/pyramid2`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Pyramid with tiered levels — bigger ideas at the wider end, detail at the narrower. Hierarchy of importance.

### When to use

- Hierarchical importance (top-down or bottom-up)
- Maslow-style tiers, foundation-to-apex layering
- Prioritised content where the biggest idea sits at one end

### When NOT to use

- Equal-weight items (use List)
- Sequences (use Process)
- More than ~6 levels (pyramid becomes cramped)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> pyramid2 is the right choice when the content has {n} pyramid items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `pyramid` (when conditions met)

**Selector routes to this layout when:** graphic_type in (pyramid) AND enrichment_tier == 'pure_programmatic' AND node_count within [3, 6] AND max(label_length) <= 30

---

## Basic Venn (`venn1`)

- **Category:** Relationship
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/venn1#1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-8 nodes, max 28 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/venn1`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1#4`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/colorful1`

### Visual character

Two overlapping circles showing shared and unique attributes of two sets.

### When to use

- Overlapping or intersecting sets
- Many-to-many relationships between items
- Comparing shared and unique attributes

### When NOT to use

- Strictly sequential content (use Process)
- Tree-shaped content (use Hierarchy)
- Very dense overlap requirements (may need custom_svg)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> venn1 is the right choice when the content has {n} relationship items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `venn` (when conditions met)

**Selector routes to this layout when:** graphic_type in (venn) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 8] AND max(label_length) <= 28

---

## Process Variant 4 (`process4`)

- **Category:** Process
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/process4#1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-9 nodes, max 24 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/process4`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1#5`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2#1`

### Visual character

Alternative process variant with distinct styling from process1 — same sequential flow, different visual treatment.

### When to use

- Sequential processes or workflows
- Step-by-step explanations
- Pipelines with a definite start and end

### When NOT to use

- Cyclical loops (use a Cycle layout)
- Hierarchical relationships (use Hierarchy)
- More than ~9 steps (becomes unreadable)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> process4 is the right choice when the content has {n} process items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `flowchart` (when conditions met)

**Selector routes to this layout when:** graphic_type in (flowchart) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 9] AND max(label_length) <= 24

---

## Chevron Process (`chevron1`)

- **Category:** Process
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/chevron1#1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-9 nodes, max 24 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/chevron1`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple2#9`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Stacked forward-pointing chevron shapes conveying momentum and direction. Good for emphasising a progression that builds.

### When to use

- Sequential processes or workflows
- Step-by-step explanations
- Pipelines with a definite start and end

### When NOT to use

- Cyclical loops (use a Cycle layout)
- Hierarchical relationships (use Hierarchy)
- More than ~9 steps (becomes unreadable)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> chevron1 is the right choice when the content has {n} process items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `chevron_list` (when conditions met)

**Selector routes to this layout when:** graphic_type in (chevron_list) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 9] AND max(label_length) <= 24

---

## Horizontal Process 4 (`hProcess4`)

- **Category:** Process
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/hProcess4#1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-9 nodes, max 24 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/hProcess4`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/3d2#2`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Horizontal process variant with distinct visual treatment from the basic process layout.

### When to use

- Sequential processes or workflows
- Step-by-step explanations
- Pipelines with a definite start and end

### When NOT to use

- Cyclical loops (use a Cycle layout)
- Hierarchical relationships (use Hierarchy)
- More than ~9 steps (becomes unreadable)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> hProcess4 is the right choice when the content has {n} process items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `flowchart` (when conditions met)

**Selector routes to this layout when:** graphic_type in (flowchart) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 9] AND max(label_length) <= 24

---

## Horizontal Process 7 (`hProcess7`)

- **Category:** Process
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/hProcess7#1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-9 nodes, max 24 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/hProcess7`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Another horizontal process variant — check visual_character after manual gate.

### When to use

- Sequential processes or workflows
- Step-by-step explanations
- Pipelines with a definite start and end

### When NOT to use

- Cyclical loops (use a Cycle layout)
- Hierarchical relationships (use Hierarchy)
- More than ~9 steps (becomes unreadable)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> hProcess7 is the right choice when the content has {n} process items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `flowchart` (when conditions met)

**Selector routes to this layout when:** graphic_type in (flowchart) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 9] AND max(label_length) <= 24

---

## Horizontal Process 9 (`hProcess9`)

- **Category:** Process
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/hProcess9#2`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-9 nodes, max 24 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/hProcess9`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple4#6`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Horizontal process variant 9 — check visual_character after manual gate.

### When to use

- Sequential processes or workflows
- Step-by-step explanations
- Pipelines with a definite start and end

### When NOT to use

- Cyclical loops (use a Cycle layout)
- Hierarchical relationships (use Hierarchy)
- More than ~9 steps (becomes unreadable)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> hProcess9 is the right choice when the content has {n} process items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `flowchart` (when conditions met)

**Selector routes to this layout when:** graphic_type in (flowchart) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 9] AND max(label_length) <= 24

---

## Horizontal Process 11 (`hProcess11`)

- **Category:** Process
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/hProcess11#1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-9 nodes, max 24 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/hProcess11`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple4#8`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Horizontal process variant 11 — check visual_character after manual gate.

### When to use

- Sequential processes or workflows
- Step-by-step explanations
- Pipelines with a definite start and end

### When NOT to use

- Cyclical loops (use a Cycle layout)
- Hierarchical relationships (use Hierarchy)
- More than ~9 steps (becomes unreadable)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> hProcess11 is the right choice when the content has {n} process items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `flowchart` (when conditions met)

**Selector routes to this layout when:** graphic_type in (flowchart) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 9] AND max(label_length) <= 24

---

## L-Shaped Process 2 (`lProcess2`)

- **Category:** Process
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/lProcess2#1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-9 nodes, max 24 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/lProcess2`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1#7`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2#2`

### Visual character

L-shaped process that wraps a sequence across two axes, useful when horizontal row would be too wide.

### When to use

- Sequential processes or workflows
- Step-by-step explanations
- Pipelines with a definite start and end

### When NOT to use

- Cyclical loops (use a Cycle layout)
- Hierarchical relationships (use Hierarchy)
- More than ~9 steps (becomes unreadable)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> lProcess2 is the right choice when the content has {n} process items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `flowchart` (when conditions met)

**Selector routes to this layout when:** graphic_type in (flowchart) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 9] AND max(label_length) <= 24

---

## Cycle Variant 8 (`cycle8`)

- **Category:** Cycle
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/cycle8#1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 3-8 nodes, max 20 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/cycle8`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple2#2`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/colorful1`

### Visual character

Alternative cycle variant — check visual_character after manual gate.

### When to use

- Iterative or continuous processes
- Feedback loops
- Recurring workflows with 3-7 stages

### When NOT to use

- Linear sequences with a definite end (use Process)
- Hierarchical structures (use Hierarchy)
- More than ~8 stages (ring becomes cluttered)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> cycle8 is the right choice when the content has {n} cycle items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `cycle` (when conditions met)

**Selector routes to this layout when:** graphic_type in (cycle) AND enrichment_tier == 'pure_programmatic' AND node_count within [3, 8] AND max(label_length) <= 20

---

## Hierarchy 2 (`hierarchy2`)

- **Category:** Hierarchy
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/hierarchy2`
- **Data shape:** `hierarchical`
- **Special node types:** none (only regular nodes)
- **Capacity:** 3-25 nodes, max 32 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/hierarchy2`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Hierarchy layout variant 2 — check visual_character after manual gate.

### When to use

- Tree-shaped content with parent-child relationships
- Reporting structures and management hierarchies
- Taxonomies with 2-4 levels of nesting

### When NOT to use

- Flat lists of peers (use List or Process)
- Cyclic relationships (use Cycle)
- More than ~25 total nodes or ~4 levels deep

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> hierarchy2 is the right choice when the content describes a hierarchy tree of {n} nodes. Delivers editable SmartArt — speaker can restructure the tree in PowerPoint after delivery.

### Backs these graphic types

- `hierarchy` (when conditions met)

**Selector routes to this layout when:** graphic_type in (hierarchy) AND enrichment_tier == 'pure_programmatic' AND node_count within [3, 25] AND max(label_length) <= 32

---

## Hierarchy 4 (`hierarchy4`)

- **Category:** Hierarchy
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/hierarchy4#1`
- **Data shape:** `hierarchical`
- **Special node types:** none (only regular nodes)
- **Capacity:** 3-25 nodes, max 32 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/hierarchy4`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1#1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/colorful1`

### Visual character

Hierarchy layout variant 4 — check visual_character after manual gate.

### When to use

- Tree-shaped content with parent-child relationships
- Reporting structures and management hierarchies
- Taxonomies with 2-4 levels of nesting

### When NOT to use

- Flat lists of peers (use List or Process)
- Cyclic relationships (use Cycle)
- More than ~25 total nodes or ~4 levels deep

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> hierarchy4 is the right choice when the content describes a hierarchy tree of {n} nodes. Delivers editable SmartArt — speaker can restructure the tree in PowerPoint after delivery.

### Backs these graphic types

- `hierarchy` (when conditions met)

**Selector routes to this layout when:** graphic_type in (hierarchy) AND enrichment_tier == 'pure_programmatic' AND node_count within [3, 25] AND max(label_length) <= 32

---

## Hierarchy 5 (`hierarchy5`)

- **Category:** Hierarchy
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/hierarchy5`
- **Data shape:** `hierarchical`
- **Special node types:** none (only regular nodes)
- **Capacity:** 3-25 nodes, max 32 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/hierarchy5`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple5#1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent2_2`

### Visual character

Hierarchy layout variant 5 — check visual_character after manual gate.

### When to use

- Tree-shaped content with parent-child relationships
- Reporting structures and management hierarchies
- Taxonomies with 2-4 levels of nesting

### When NOT to use

- Flat lists of peers (use List or Process)
- Cyclic relationships (use Cycle)
- More than ~25 total nodes or ~4 levels deep

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> hierarchy5 is the right choice when the content describes a hierarchy tree of {n} nodes. Delivers editable SmartArt — speaker can restructure the tree in PowerPoint after delivery.

### Backs these graphic types

- `hierarchy` (when conditions met)

**Selector routes to this layout when:** graphic_type in (hierarchy) AND enrichment_tier == 'pure_programmatic' AND node_count within [3, 25] AND max(label_length) <= 32

---

## Hierarchy 6 (`hierarchy6`)

- **Category:** Hierarchy
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/hierarchy6`
- **Data shape:** `hierarchical`
- **Special node types:** none (only regular nodes)
- **Capacity:** 3-25 nodes, max 32 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/hierarchy6`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple4#2`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/colorful4`

### Visual character

Hierarchy layout variant 6 — check visual_character after manual gate.

### When to use

- Tree-shaped content with parent-child relationships
- Reporting structures and management hierarchies
- Taxonomies with 2-4 levels of nesting

### When NOT to use

- Flat lists of peers (use List or Process)
- Cyclic relationships (use Cycle)
- More than ~25 total nodes or ~4 levels deep

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> hierarchy6 is the right choice when the content describes a hierarchy tree of {n} nodes. Delivers editable SmartArt — speaker can restructure the tree in PowerPoint after delivery.

### Backs these graphic types

- `hierarchy` (when conditions met)

**Selector routes to this layout when:** graphic_type in (hierarchy) AND enrichment_tier == 'pure_programmatic' AND node_count within [3, 25] AND max(label_length) <= 32

---

## Horizontal List 6 (`hList6`)

- **Category:** List
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/hList6#1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-8 nodes, max 30 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/hList6`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1#16`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2#5`

### Visual character

Horizontal list variant — items arranged in a row rather than stacked.

### When to use

- Collections of related points without a specific order
- Feature lists, benefit summaries, key takeaways
- Items where emphasis matters more than sequence

### When NOT to use

- Ordered processes (use Process)
- Relationships between items (use Relationship)
- Data with quantitative values (use a chart)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> hList6 is the right choice when the content has {n} list items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `list` (when conditions met)

**Selector routes to this layout when:** graphic_type in (list) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 8] AND max(label_length) <= 30

---

## Vertical List 2 (`vList2`)

- **Category:** List
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/vList2#1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-8 nodes, max 30 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/vList2`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1#12`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2#4`

### Visual character

Vertical list variant 2 — distinct styling from the basic list.

### When to use

- Collections of related points without a specific order
- Feature lists, benefit summaries, key takeaways
- Items where emphasis matters more than sequence

### When NOT to use

- Ordered processes (use Process)
- Relationships between items (use Relationship)
- Data with quantitative values (use a chart)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> vList2 is the right choice when the content has {n} list items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `list` (when conditions met)

**Selector routes to this layout when:** graphic_type in (list) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 8] AND max(label_length) <= 30

---

## Vertical List 3 (`vList3`)

- **Category:** List
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/vList3`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-8 nodes, max 30 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/vList3`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Vertical list variant 3.

### When to use

- Collections of related points without a specific order
- Feature lists, benefit summaries, key takeaways
- Items where emphasis matters more than sequence

### When NOT to use

- Ordered processes (use Process)
- Relationships between items (use Relationship)
- Data with quantitative values (use a chart)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> vList3 is the right choice when the content has {n} list items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `list` (when conditions met)

**Selector routes to this layout when:** graphic_type in (list) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 8] AND max(label_length) <= 30

---

## Vertical List 4 (`vList4`)

- **Category:** List
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/vList4#1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-8 nodes, max 30 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/vList4`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1#6`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Vertical list variant 4 — one of the most stylable list layouts, with many PowerPoint-provided style variants.

### When to use

- Collections of related points without a specific order
- Feature lists, benefit summaries, key takeaways
- Items where emphasis matters more than sequence

### When NOT to use

- Ordered processes (use Process)
- Relationships between items (use Relationship)
- Data with quantitative values (use a chart)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> vList4 is the right choice when the content has {n} list items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `list` (when conditions met)

**Selector routes to this layout when:** graphic_type in (list) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 8] AND max(label_length) <= 30

---

## Vertical List 5 (`vList5`)

- **Category:** List
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/vList5`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-8 nodes, max 30 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/vList5`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Vertical list variant 5.

### When to use

- Collections of related points without a specific order
- Feature lists, benefit summaries, key takeaways
- Items where emphasis matters more than sequence

### When NOT to use

- Ordered processes (use Process)
- Relationships between items (use Relationship)
- Data with quantitative values (use a chart)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> vList5 is the right choice when the content has {n} list items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `list` (when conditions met)

**Selector routes to this layout when:** graphic_type in (list) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 8] AND max(label_length) <= 30

---

## Three-Circle Venn (`venn3`)

- **Category:** Relationship
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/venn3#1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-8 nodes, max 28 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/venn3`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1#17`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Three overlapping circles — classic Venn diagram for visualising three-set relationships.

### When to use

- Overlapping or intersecting sets
- Many-to-many relationships between items
- Comparing shared and unique attributes

### When NOT to use

- Strictly sequential content (use Process)
- Tree-shaped content (use Hierarchy)
- Very dense overlap requirements (may need custom_svg)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> venn3 is the right choice when the content has {n} relationship items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `venn` (when conditions met)

**Selector routes to this layout when:** graphic_type in (venn) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 8] AND max(label_length) <= 28

---

## Basic Funnel (`funnel1`)

- **Category:** Relationship
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/funnel1#1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-8 nodes, max 28 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/funnel1`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple2#7`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Tapered funnel showing stages narrowing from a wide top to a focused bottom. Good for conversion funnels or filtering processes.

### When to use

- Overlapping or intersecting sets
- Many-to-many relationships between items
- Comparing shared and unique attributes

### When NOT to use

- Strictly sequential content (use Process)
- Tree-shaped content (use Hierarchy)
- Very dense overlap requirements (may need custom_svg)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> funnel1 is the right choice when the content has {n} relationship items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `pipeline_funnel` (when conditions met)

**Selector routes to this layout when:** graphic_type in (pipeline_funnel) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 8] AND max(label_length) <= 28

---

## Target Diagram (`target3`)

- **Category:** Relationship
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/target3`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-8 nodes, max 28 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/target3`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Concentric circles (target) showing layered goals or priorities, with the most important at the centre.

### When to use

- Overlapping or intersecting sets
- Many-to-many relationships between items
- Comparing shared and unique attributes

### When NOT to use

- Strictly sequential content (use Process)
- Tree-shaped content (use Hierarchy)
- Very dense overlap requirements (may need custom_svg)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> target3 is the right choice when the content has {n} relationship items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `target` (when conditions met)

**Selector routes to this layout when:** graphic_type in (target) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 8] AND max(label_length) <= 28

---

# Future (non-v1) Layouts

## Picture List (`pList1`)

- **Category:** Picture
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/pList1#1`
- **Data shape:** `picture`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-7 nodes, max 30 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/pList1`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Picture list — each list item includes an image placeholder alongside text. When paired with our image generation pipeline, speakers can request AI-generated illustrations per item.

### When to use

- Visual-first content where each item has an illustrative image
- Product showcases, team photos, concept illustrations
- Speaker wants to combine structured text with AI-generated imagery

### When NOT to use

- Text-only content (use a non-Picture layout)
- Decks rendered without image generation budget
- Microsites or PDF-only output (images may not transfer cleanly)

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> pList1 is the right choice when the content has {n} picture items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `picture_list` (when conditions met)

**Selector routes to this layout when:** graphic_type in (picture_list) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 7] AND max(label_length) <= 30

---

## Default Layout (`default`)

- **Category:** Other
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/default`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-10 nodes, max 30 chars per label
- **Layout directory:** `tests/fixtures/smartart_layouts/default`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Default placeholder layout — uncategorised. Not intended for production use.

### When to use

- Catalog placeholder — uncategorised layout

### When NOT to use

- Use a more specific category layout

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> default is the right choice when the content has {n} other items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `none` (when conditions met)

**Selector routes to this layout when:** graphic_type in (no mapped graphic_type) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 10] AND max(label_length) <= 30

---
