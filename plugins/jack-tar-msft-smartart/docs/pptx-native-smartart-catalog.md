# pptx_native SmartArt Layout Catalog

> This file is auto-generated from `src/smartart_pptx_native/layouts/catalog.json`. Do not edit by hand — run `python -m src.smartart_pptx_native.layouts.catalog_markdown` to regenerate.

**Catalog version:** `2.0.0`

**v1 layouts:** 28 — Basic Process, Basic Cycle, Organization Chart, Basic List, Matrix 2, Pyramid 2, Basic Venn, Process Variant 4, Chevron Process, Horizontal Process 4, Horizontal Process 7, Horizontal Process 9, Horizontal Process 11, L-Shaped Process 2, Cycle Variant 8, Hierarchy 2, Hierarchy 4, Hierarchy 5, Hierarchy 6, Horizontal List 6, Vertical List 2, Vertical List 3, Vertical List 4, Vertical List 5, Three-Circle Venn, Basic Funnel, Target Diagram, Picture List
**Future layouts (non-v1):** 1 — Default Layout

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
| **Vertical List 2** (`vList2`) | List | `flat_list` | 8 | 60 | `list` |
| **Vertical List 3** (`vList3`) | List | `picture` | 8 | 30 | `list` |
| **Vertical List 4** (`vList4`) | List | `picture` | 8 | 30 | `list` |
| **Vertical List 5** (`vList5`) | List | `flat_list` | 8 | 30 | `list` |
| **Three-Circle Venn** (`venn3`) | Relationship | `flat_list` | 8 | 28 | `venn` |
| **Basic Funnel** (`funnel1`) | Relationship | `flat_list` | 8 | 28 | `pipeline_funnel` |
| **Target Diagram** (`target3`) | Relationship | `flat_list` | 8 | 28 | `target` |
| **Picture List** (`pList1`) | Picture | `picture` | 7 | 30 | `picture_list` |

---

# Layouts in Detail

## Basic Process (`process1`)

- **Category:** Process
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/process1#1`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-9 nodes, max 24 chars per label
- **Layout directory:** `data/smartart_layouts/process1`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple2#4`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

A horizontal row of rectangular boxes connected by right-pointing arrows. Each box holds a single step label, and the arrows between them imply linear left-to-right progression. The simplest, most universally recognized process diagram.

### When to use

- Simple sequential workflows with 3-7 steps that follow a strict linear order
- When the audience needs to grasp a straightforward progression at a glance
- Onboarding flows, approval chains, or any process where every step must happen in sequence
- When you want maximum clarity with zero visual distraction — the default choice when nothing fancier is needed

### When NOT to use

- When steps have sub-steps or secondary details — the flat boxes offer no room for descriptions
- When the process branches, loops, or has parallel paths — this layout is strictly linear
- When you have more than 7-8 steps — the boxes shrink to unreadable sizes

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
- **Layout directory:** `data/smartart_layouts/cycle2`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple4#7`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

A ring of circles (typically 3-6) arranged in a circular pattern, connected by curved arrows flowing clockwise. Each circle contains a step label. The circular arrangement emphasizes that the process repeats continuously with no defined start or end.

### When to use

- Iterative or repeating processes (PDCA, sprint cycles, continuous improvement loops)
- When emphasizing there is no final step — the process returns to the beginning
- Feedback loops or any workflow where the output of the last step feeds the first
- When you need to contrast against linear processes — the circular shape signals ongoing

### When NOT to use

- When the process has a clear beginning and end — use a linear process instead
- When you have more than 6-7 steps — circles shrink and arrows clutter
- When steps have sub-details — circles offer minimal text space

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
- **Layout directory:** `data/smartart_layouts/orgChart1`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple2#3`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/colorful5`

### Visual character

A traditional top-down tree with rectangular boxes connected by vertical and horizontal lines. Root at top, subordinates branching downward. Supports assistant nodes that hang sideways with a distinctive right-angle connector, distinct from direct reports below.

### When to use

- Reporting structures and team hierarchies where manager-subordinate relationships must be explicit
- When you need assistant/deputy distinction — the only hierarchy layout supporting assistant nodes natively
- Organizational announcements, team introductions, or governance slides
- When the audience expects the conventional org chart format they already know

### When NOT to use

- When the hierarchy is very deep (5+ levels) — boxes shrink at lower levels
- When relationships are non-hierarchical (matrix orgs, dotted-line reporting)
- When showing a conceptual hierarchy of ideas rather than people — use hierarchy2-6 instead

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
- **Layout directory:** `data/smartart_layouts/list1`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

A simple vertical stack of rectangular blocks, each containing a text label. Items arranged top-to-bottom with consistent spacing. No connectors or arrows — implies a flat, unordered collection.

### When to use

- Flat lists of items, features, or requirements where order is unimportant or implied
- Agenda slides, table-of-contents slides, or key-takeaway summaries
- When you have 3-8 items each needing a short label and possibly a brief description
- When you want a cleaner alternative to bullet points

### When NOT to use

- When items have a sequential relationship — use a process layout instead
- When items need nested detail — flat blocks don't support hierarchy
- When you have only 1-2 items — a list layout looks empty

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
- **Layout directory:** `data/smartart_layouts/matrix2`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/3d2#1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/colorful1`

### Visual character

A 2x2 grid of four equal quadrants, often with a small central hub element. Each quadrant contains a label and optional description. Naturally maps to two-axis frameworks.

### When to use

- 2x2 strategic frameworks (Eisenhower, BCG, risk/impact, build/buy decisions)
- When you have exactly 4 categories that pair along two axes
- Comparative analysis where two binary dimensions create four meaningful combinations
- When the audience is familiar with quadrant-based thinking from business strategy

### When NOT to use

- When you have more or fewer than 4 items — the fixed 2x2 grid cannot accommodate
- When items don't map to two meaningful axes — forcing into quadrants obscures
- When items are sequential or hierarchical — matrix implies parallel categories

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
- **Layout directory:** `data/smartart_layouts/pyramid2`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

A triangular pyramid divided into horizontal tiers, widest at base and narrowing to a point at top. Each tier is labeled, and the narrowing implies decreasing quantity, increasing importance, or rising abstraction from bottom to top.

### When to use

- Hierarchical models where volume decreases upward (Maslow's, data-information-knowledge-wisdom)
- Prioritization frameworks where the top is most important and the base is broadest
- Market segmentation (mass at base, premium at apex) or organizational layers
- When the narrowing metaphor directly matches your narrative

### When NOT to use

- When tiers are of equal importance — narrowing incorrectly implies decreasing significance
- When you have more than 5-6 tiers — slices become too thin for labels
- When the hierarchy is inverted — a pyramid reads bottom-up which may confuse top-down narratives

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
- **Layout directory:** `data/smartart_layouts/venn1`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1#4`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/colorful1`

### Visual character

Two large overlapping circles, each with a distinct color and label. The overlapping region represents the intersection or common ground. Simple, clean, and immediately recognizable as a comparison-and-overlap diagram.

### When to use

- Comparing exactly two concepts and highlighting what they share
- When the overlap/intersection is the key insight of the slide
- Simple either/or/both frameworks where the audience sees shared and unique attributes
- When the visual must be instantly understood with zero explanation — universally recognized

### When NOT to use

- When comparing 3+ items — use venn3 or another layout
- When there is no meaningful overlap — empty intersection looks misleading
- When each concept has many sub-items — circles offer limited text space

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
- **Layout directory:** `data/smartart_layouts/process4`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1#5`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2#1`

### Visual character

A horizontal process where each step is a larger rounded rectangle with room for both a bold heading and a smaller description block beneath it. Steps are connected by subtle arrows, giving each stage more visual weight than Basic Process.

### When to use

- Sequential processes where each step needs a title AND a 1-2 sentence explanation
- Project phase overviews where each phase has a brief scope description
- When you want visual weight but need more information density per step than process1 allows
- Executive summaries where each stage must be self-explanatory without narration

### When NOT to use

- When steps are single words — the large boxes will look empty
- When you have 6+ steps — the wider boxes consume more horizontal space
- When Basic Process communicates clearly enough — extra description space adds unnecessary complexity

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
- **Layout directory:** `data/smartart_layouts/chevron1`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple2#9`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

A horizontal row of forward-pointing chevron (arrow-head) shapes that overlap, forming a continuous band. Each chevron holds a step label. The pointed shape itself implies forward momentum without needing separate arrow connectors.

### When to use

- Pipeline or maturity model narratives where you want to emphasize forward momentum
- Sales pipelines, phase gates, or stages where the driving forward metaphor reinforces the message
- When you want a more dynamic and modern look than plain rectangular boxes
- Horizontal timelines where the chevron shape suggests temporal flow

### When NOT to use

- When steps need sub-descriptions — chevron shapes have limited interior text space
- When the process is non-directional or cyclical — chevrons imply one-way movement
- When you have 6+ steps — the chevrons become narrow slivers

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
- **Layout directory:** `data/smartart_layouts/hProcess4`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/3d2#2`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

A horizontal process with alternating top-and-bottom text blocks connected to a central flow line. Steps sit above and below the central axis in a zigzag pattern, giving a staggered timeline-rail appearance.

### When to use

- Timelines or roadmaps where alternating placement distinguishes milestones
- When you have 5-8 steps and need vertical space to avoid horizontal crowding
- Comparative process flows where alternating positions can represent two parallel tracks
- When you want visual variety over a plain linear row while keeping sequential order

### When NOT to use

- When the audience needs to scan in a single straight line — zigzag adds overhead
- When steps have unequal importance — alternating layout implies equal weight
- When you have fewer than 4 steps — the staggered effect looks odd

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
- **Layout directory:** `data/smartart_layouts/hProcess7`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

A horizontal process using large circular or pill-shaped nodes connected by lines or arrows. Each node frames a step number or icon with the label adjacent. The circular shapes give a softer, more modern feel than rectangles.

### When to use

- Design-forward presentations where rounded shapes match the brand aesthetic
- Numbered step sequences where the circle naturally frames a numeral
- When you want to emphasize discrete milestones or checkpoints rather than continuous flow
- Innovation or creative process slides where softer geometry feels less rigid

### When NOT to use

- When steps need substantial text — circles have poor text-fill efficiency
- When the process is about continuous flow rather than discrete stops
- When you need more than 6 nodes — horizontal space fills rapidly

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
- **Layout directory:** `data/smartart_layouts/hProcess9`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple4#6`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

A horizontal process where each step is a prominent shape with a label, and smaller sub-step descriptions appear below. The layout shows both the high-level flow and supporting details in a two-tier arrangement.

### When to use

- Processes where each major step has 1-3 supporting actions that need to be visible
- Methodology overviews where the main phase and its key activities must appear together
- When the audience needs both the high-level flow and ground-level details on one slide
- Training content where each step needs brief explanatory bullets

### When NOT to use

- When steps are simple and self-explanatory — the sub-step area wastes space
- When you have more than 5 main steps — the two-tier layout becomes dense
- When sub-details vary wildly in length — uneven text blocks break symmetry

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
- **Layout directory:** `data/smartart_layouts/hProcess11`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple4#8`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

A horizontal process with bold colored blocks or ribbon-like segments with embedded icons or numbers, and descriptive text below. It has a polished, infographic-like feel with more graphical embellishment than simpler process layouts.

### When to use

- Executive or marketing presentations where visual impact matters as much as content
- When each process step maps to a deliverable, metric, or icon
- Annual reports or strategy decks needing polished, branded process overviews
- When you want infographic-quality without leaving PowerPoint

### When NOT to use

- Technical audiences who prefer clean, minimal diagrams over decorative layouts
- When the process has 6+ steps — embellishments consume space
- When content changes frequently — tight graphical layout is harder to update

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
- **Layout directory:** `data/smartart_layouts/lProcess2`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1#7`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2#2`

### Visual character

Steps arranged in an L-shaped path — flowing horizontally then turning 90 degrees vertically. The bend visually represents a pivot, phase shift, or handoff between two distinct stages of the process.

### When to use

- Processes with a clear turning point or handoff between phases
- When you want to show two distinct phases with different orientations or owners
- Customer journeys that shift from acquisition to retention
- When you need to use both horizontal and vertical slide space efficiently

### When NOT to use

- When the process is uniformly sequential with no natural pivot — the L-shape feels forced
- When the audience expects a standard left-to-right flow — the bend can confuse
- When you have fewer than 4 steps — the L needs enough steps to populate both legs

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
- **Layout directory:** `data/smartart_layouts/cycle8`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple2#2`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/colorful1`

### Visual character

A cycle using a segmented ring or gear-like arrangement where each segment represents a stage. Unlike cycle2's discrete circles, this uses pie-slice or arc segments joined into a continuous loop, often with a central hub. Emphasizes interconnectedness and equal contribution.

### When to use

- Ecosystems or interdependent systems where each component contributes equally
- When you want to emphasize unity and integration — the continuous ring looks cohesive
- Governance or compliance cycles where a closed, unbroken loop reinforces completeness
- When the cycle has 4-8 stages and you want more visual sophistication than cycle2

### When NOT to use

- When stages are unequal in importance — equal-sized segments imply parity
- When the audience needs to see directional flow clearly — segmented rings can obscure sequence
- When you have 3 or fewer stages — the ring looks sparse

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
- **Layout directory:** `data/smartart_layouts/hierarchy2`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

A horizontal hierarchy flowing left-to-right with the root on the left and child nodes branching rightward in indented tiers. Resembles an indented outline or file-tree explorer using horizontal brackets or lines.

### When to use

- Taxonomies, classification systems, or category breakdowns that read left-to-right
- When you have many leaf nodes at the lowest level — horizontal layout gives room for wide bottom tiers
- Slide layouts where vertical space is constrained but horizontal space is available
- When the hierarchy represents decomposition rather than a reporting structure

### When NOT to use

- When the audience expects a traditional top-down org chart — horizontal may confuse
- When you have many levels of depth — rightward indentation compresses deeper labels
- When you need assistant nodes — this layout does not support them

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
- **Layout directory:** `data/smartart_layouts/hierarchy4`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1#1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/colorful1`

### Visual character

A top-down hierarchy where child nodes are enclosed within or grouped under their parent as nested containers. Parents appear as header bars with children listed below in a contained region, creating a visual nesting effect rather than connected-box-and-line trees.

### When to use

- When you want to emphasize containment or ownership (department contains teams, system contains modules)
- Architectural decomposition slides where subsystems belong to larger systems
- When the grouping relationship matters more than the chain-of-command relationship
- Portfolio or catalog views organized into parent categories

### When NOT to use

- When you need to show cross-group connections — containment isolates groups visually
- When the hierarchy is deeper than 3 levels — nesting within nesting becomes confusing
- When equal emphasis on all items is needed — parent containers dominate visually

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
- **Layout directory:** `data/smartart_layouts/hierarchy5`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple5#1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent2_2`

### Visual character

A top-down tree with rounded or pill-shaped elements and gracefully fanning connector lines. The root sits prominently at the top with a balanced, symmetrical spread of branches below. Cleaner, more modern aesthetic than orgChart1.

### When to use

- Conceptual hierarchies (strategic priorities, goal breakdowns) where you want a polished look
- When the hierarchy represents ideas, objectives, or categories rather than people
- Pitch decks or external presentations where visual elegance matters
- When you have a balanced tree — the symmetrical spread looks best

### When NOT to use

- When you need assistant nodes — use orgChart1 instead
- When the tree is heavily unbalanced — asymmetry breaks the layout
- When showing reporting relationships between people — softer shapes may not convey authority

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
- **Layout directory:** `data/smartart_layouts/hierarchy6`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple4#2`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/colorful4`

### Visual character

A table-like or columnar hierarchy where each level is a distinct horizontal band. Parent items span full width, children arranged as cells in the next band below. Structured and grid-like, resembling a work breakdown structure (WBS).

### When to use

- Work breakdown structures for clean tabular decomposition of deliverables
- When hierarchy levels have different granularity (strategic → tactical → operational)
- Program or portfolio views where projects group under programs
- When the audience prefers structured, grid-aligned layouts over organic trees

### When NOT to use

- When the hierarchy is deep (4+ levels) — bands become thin and cramped
- When branches have very unequal widths — the grid wastes space on sparse branches
- When you need a free-form tree with crossing connections

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
- **Layout directory:** `data/smartart_layouts/hList6`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1#16`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2#5`

### Visual character

A horizontal row of vertical cards or panels side by side, each with a colored header bar and body text below. Resembles side-by-side feature cards or comparison columns.

### When to use

- Feature comparisons, service tier descriptions, or plan options displayed side by side
- When each item has both a title and supporting description benefiting from card containers
- Dashboard-style slides showing 3-5 parallel metrics or status summaries
- When items are peers of equal importance and horizontal space should be used fully

### When NOT to use

- When items exceed 5-6 — cards become too narrow for readable text
- When items have very different content lengths — uneven card density looks unbalanced
- When items are sequential — side-by-side implies parallel options, not ordered steps

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
- **Capacity:** 2-8 nodes, max 60 chars per label
- **Layout directory:** `data/smartart_layouts/vList2`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1#12`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2#4`

### Visual character

A vertical list where each item features a prominent accent shape (colored circle, number badge, or icon placeholder) on the left, with item text to its right. The accent shapes create a strong visual rhythm down the left edge.

### When to use

- Numbered lists or ranked items where the accent shape holds a numeral
- When you want a more visually engaging vertical list than plain stacked bars
- Key principles, values, or pillars where each item deserves individual visual emphasis
- When pairing with icons — the accent placeholder naturally frames an icon per item

### When NOT to use

- When items don't benefit from individual emphasis — accent shapes add clutter
- When you have more than 6-7 items — accents consume vertical space faster
- When the list is purely textual with no numbering or iconography — list1 is cleaner

### Capacity rationale

Refined 2026-05-01 (Run 7 Finding #22 spike validation). vList2 layout XML uses INF height + auto-shrink font (min 2pt); empirically renders prose-length bullets up to 60 chars at sub-page (3.5x3.5) and banner (10x2) scales without visible quality degradation. Bridge LAYOUT_BULLET_CAPS["vList2"]=60 now matches.

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
- **Data shape:** `picture`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-8 nodes, max 30 chars per label
- **Layout directory:** `data/smartart_layouts/vList3`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

A vertical list with each item as a wide horizontal bar containing a bold heading on the left and a description area on the right within the same bar. Resembles a definition list or glossary layout.

### When to use

- Term-and-definition pairs, glossaries, or key-concept explanations
- When each item has a short label AND a longer explanation on the same line
- FAQ-style slides where question and answer sit side by side
- When you want structured information density without resorting to a table

### When NOT to use

- When items are single-label entries with no descriptions — the right side is empty
- When descriptions are long paragraphs — horizontal split compresses both
- When you have more than 5-6 items — bars become thin

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
- **Data shape:** `picture`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-8 nodes, max 30 chars per label
- **Layout directory:** `data/smartart_layouts/vList4`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1#6`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

A vertical list where each item is a large rectangular card with a colored top section (heading) and lighter bottom section (description). Cards stacked vertically with clear spacing. Two-tone treatment gives each item a card-with-header appearance.

### When to use

- Category-based lists where each item has a clear label and supporting detail
- When you want more visual separation between items than vList2 or vList3 provide
- Status update slides where each card represents a workstream with heading and current state
- When the two-zone (header + body) structure matches your content's natural shape

### When NOT to use

- When items are short labels only — large cards with empty body zones waste space
- When you have more than 4-5 items — tall cards overflow the slide
- When all items have equal simplicity — card treatment adds unnecessary complexity

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
- **Layout directory:** `data/smartart_layouts/vList5`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

A vertical list with items as alternating or staggered blocks — some left-aligned, some right-aligned — creating a zigzag pattern. Each block contains heading and description text. Offset layout adds visual dynamism.

### When to use

- Creative or marketing presentations where visual rhythm matters more than rigid alignment
- Timeline-adjacent narratives where alternating positions suggest progression or contrast
- When you want to break monotony of a long vertical list while keeping top-to-bottom flow
- Portfolio or case-study summaries where each item benefits from distinct visual separation

### When NOT to use

- When the audience expects clean aligned layouts — zigzag can feel disorganized
- When items need to be scanned quickly — alternating positions slow reading
- When the slide will be printed — staggered layout doesn't translate well to linear reading

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
- **Layout directory:** `data/smartart_layouts/venn3`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1#17`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Three overlapping circles in a triangular pattern creating seven distinct regions: three unique areas, three pairwise overlaps, and one central triple-overlap zone. The central region represents the convergence of all three concepts.

### When to use

- Three-way comparisons where pairwise and triple overlaps carry distinct meaning
- When the central triple-intersection is the key message — the sweet spot where all three converge
- Strategic alignment diagrams (desirability-feasibility-viability, people-process-technology)
- When combining any two is insufficient — all three required for the ideal state

### When NOT to use

- When you have 2 or 4+ concepts — fixed at exactly three circles
- When overlap regions don't carry meaningful content — empty intersections look hollow
- When circles need lengthy text — pairwise and triple zones have very constrained space

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
- **Layout directory:** `data/smartart_layouts/funnel1`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple2#7`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

A vertically oriented funnel (wide at top, narrow at bottom) divided into horizontal bands. Each band is labeled with a stage name. The tapering shape represents volume reduction, filtering, or progressive narrowing from many to few.

### When to use

- Sales or marketing funnels (leads → MQLs → SQLs → opportunities → deals)
- Filtering or screening processes where input is progressively narrowed
- When the key narrative is about conversion rates or attrition at each stage
- Recruitment pipelines, support triage, or any process where quantity decreases per step

### When NOT to use

- When stages don't represent decreasing volume — funnel shape misleads
- When you need feedback loops or cycles — funnel is strictly one-way
- When you have more than 5-6 stages — narrow bottom bands become too thin

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
- **Layout directory:** `data/smartart_layouts/target3`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

Concentric circles (bullseye pattern) with the innermost circle representing the core goal and outer rings representing surrounding layers. Each ring is labeled. The visual centers attention on the innermost element.

### When to use

- Goal-centered models where the core objective sits at center with supporting elements around it
- Layered architecture diagrams (core platform → services → integrations → users)
- When you want to emphasize a central focus with context layers — bullseye draws the eye inward
- Security or defense-in-depth models with multiple protective layers

### When NOT to use

- When layers are sequential — use process or funnel instead; rings imply containment
- When outer layers are more important than center — bullseye privileges the core
- When you have more than 4-5 rings — outer rings become thin slivers

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> target3 is the right choice when the content has {n} relationship items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `target` (when conditions met)

**Selector routes to this layout when:** graphic_type in (target) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 8] AND max(label_length) <= 28

---

## Picture List (`pList1`)

- **Category:** Picture
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/pList1#1`
- **Data shape:** `picture`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-7 nodes, max 30 chars per label
- **Layout directory:** `data/smartart_layouts/pList1`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

A list where each item includes a rectangular picture placeholder on top with a text label below. The layout creates a catalog or media listing pattern with consistent image-and-text pairing. When paired with AI image generation, speakers get illustrated editable SmartArt.

### When to use

- Team introductions with headshots, product catalogs with images, portfolio items with thumbnails
- When each list item has an associated image that reinforces or identifies it
- Speaker bios, case study summaries, or content where visual identity matters alongside text
- When you want structured repeating image+text pattern that avoids ad-hoc picture placement

### When NOT to use

- When you don't have images for every item — empty placeholders look unprofessional
- When images are not meaningfully different — drawing attention to generic images adds no value
- When you have more than 4-5 items — image+text pairs consume significant area

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> pList1 is the right choice when the content has {n} picture items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `picture_list` (when conditions met)

**Selector routes to this layout when:** graphic_type in (picture_list) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 7] AND max(label_length) <= 30

---

# Future (non-v1) Layouts

## Default Layout (`default`)

- **Category:** Other
- **Engine:** `pptx_native`
- **Layout URI:** `urn:microsoft.com/office/officeart/2005/8/layout/default`
- **Data shape:** `flat_list`
- **Special node types:** none (only regular nodes)
- **Capacity:** 2-10 nodes, max 30 chars per label
- **Layout directory:** `data/smartart_layouts/default`
- **Quick style URI:** `urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1`
- **Colors URI:** `urn:microsoft.com/office/officeart/2005/8/colors/accent1_2`

### Visual character

PowerPoint's fallback default layout — typically renders as a basic block list when no specific layout is resolved. Uncategorised placeholder, not intended for production use.

### When to use

- Internal testing or fallback scenarios where a specific layout isn't available

### When NOT to use

- Production decks — always select a specific layout from the catalog
- Any speaker-facing content — the default layout has no distinctive visual character

### Capacity rationale

First-pass default per category norms. Refine after manual gate validation.

### Selector rationale template

> default is the right choice when the content has {n} other items from "{first}" to "{last}". Delivers editable SmartArt — speaker can add/rename items in PowerPoint after delivery.

### Backs these graphic types

- `none` (when conditions met)

**Selector routes to this layout when:** graphic_type in (no mapped graphic_type) AND enrichment_tier == 'pure_programmatic' AND node_count within [2, 10] AND max(label_length) <= 30

---
