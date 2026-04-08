# Native PowerPoint SmartArt Engine — Design Specification

**Date:** 2026-04-08
**Status:** Approved — **all Phase 0 validation gates closed** on 2026-04-08. Four spikes verified: mutation (process1), generalisation (cycle2), injection (blank host), hierarchical tree + assistants (orgChart1).
**Spike report:** `docs/spikes/2026-04-08-pptx-native-smartart-injection.md` (four experiments, all passed in PowerPoint Mac)
**Research:** `research/report-1-landscape-and-spec.md`, `research/report-2-implementation-and-validation.md`
**Predecessor spec:** `docs/superpowers/specs/2026-04-03-smartart-intelligent-graphics-design.md`
**BSA Version:** v1.4.0 → v1.5.0

---

## 1. Overview

Add a fourth SmartArt rendering engine, `pptx_native`, that produces **editable PowerPoint SmartArt graphics** rather than rasterised PNGs. Where the existing `mermaid`, `vega_lite`, and `custom_svg` engines deliver baked images that the speaker cannot modify, `pptx_native` delivers diagrams that PowerPoint opens with the SmartArt Design ribbon active — the speaker can add nodes, rename them, change layouts, and re-style the graphic without leaving PowerPoint.

The technique is **template injection**: a small library of hand-authored seed `.pptx` files (one per supported PowerPoint built-in layout) is checked into the repository; at runtime the engine copies a seed, rewrites `ppt/diagrams/data1.xml` from extracted slide content, and deletes the cached `ppt/diagrams/drawing1.xml` so PowerPoint regenerates the layout from `layout1.xml` on first open. The engine produces no raster image — it produces a fragment of a `.pptx` package that the assembler injects.

The spike (see predecessor) confirmed the technique works end-to-end on macOS using only PowerPoint Mac for seed authoring and verification. The minimal data model (no `pres` tree, no `dgm:extLst`) is sufficient — PowerPoint regenerates the presentation tree from the layout definition.

### v1 scope

Four PowerPoint built-in layouts where post-delivery editability has the highest speaker value:

| Layout URI | Category | Maps from our graphic types |
|---|---|---|
| `urn:.../2005/8/layout/process1` | Process → Basic Process | `flowchart` (sequential, ≤ 9 nodes) |
| `urn:.../2005/8/layout/cycle1` | Cycle → Basic Cycle | New `cycle` graphic type |
| `urn:.../2005/8/layout/orgChart1` | Hierarchy → Organization Chart | New `org_chart` graphic type, plus `decision_tree` (when shape is hierarchical) |
| `urn:.../2005/8/layout/basicTimeline1` | Process → Basic Timeline | `timeline` |

Out of scope for v1: SWOT, feature matrix, Venn, gantt, pipeline funnel, all charts. These either have no clean PowerPoint equivalent or are better served by `custom_svg` / `vega_lite`.

---

## 2. Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Engine name | `pptx_native` | Names what it produces (native PowerPoint), distinguishes from rasterising engines |
| Seed authoring | Hand-built in PowerPoint Mac, one seed per layout, checked into `tests/fixtures/smartart_seeds/` | Smallest layout we have to author from scratch (the spec for `dgm:layoutDef` is huge); PowerPoint guarantees perfect compatibility |
| Data model emission | Minimal — `doc` + `node`/`parTrans`/`sibTrans` points + untyped `cxn` connections only. No `pres` tree, no `extLst`, no cached drawing | Spike proved PowerPoint regenerates the presentation tree from `layout1.xml`. Smaller code surface, simpler diffs, easier to test. |
| Engine output | Diagram XML fragment + slide XML patch instructions, *not* a PNG | Rasterising defeats the purpose — the entire value of this engine is editability |
| Assembler integration | **Two-stage assembly**: PptxGenJS builds the slide as normal with a placeholder rect, then a Python post-process step rewrites the slide's `.pptx` zip to inject the diagram parts and replace the placeholder with a `<p:graphicFrame>` referencing the diagram | Composes with existing slide construction (header, footer, body box). The alternative — pptx_native owning the entire slide — duplicates assembler responsibilities |
| Draft-phase rendering | `custom_svg` is rendered as a *preview proxy* during draft. The `pptx_native` engine only runs in the production phase. | LibreOffice cannot render `pptx_native` output (it needs the cached drawing we deleted). Image-reviewer needs *something* to score during draft. The custom_svg preview is structurally equivalent (same data model) so visual review of it is meaningful. |
| Production-phase verification | PowerPoint Mac manual open is the only ground truth; QA checks parse the output XML and confirm structural integrity but cannot verify "editable in PowerPoint" automatically | Only PowerPoint runs the layout algorithm; LibreOffice does not. We accept this constraint. |
| Selector recommendation | `pptx_native` only recommended when `enrichment_tier == 'pure_programmatic'` (T0). T1-T3 enrichment makes the graphic non-editable anyway because of overlaid AI elements. | Don't pretend a graphic is editable when half of it is a baked AI background |
| Comparator pattern | `pptx_native` opts out of the comparator. It is the *only* engine that delivers editable output for its graphic types, so there's nothing to compare against on its key dimension. | Comparator exists to pick the visually best rasteriser; not relevant when editability is the deciding factor |
| Failure fallback | If `pptx_native` rendering fails for any reason, the engine falls back to `custom_svg` for the same graphic type with a manifest warning | Graceful degradation — speaker still gets a diagram, just not editable |

---

## 3. Pipeline Integration

The pipeline shape is unchanged from the existing SmartArt spec (predecessor §2). `pptx_native` is added as a fourth value for the `engine` field in the spec contract, and the renderer dispatches to it like any other engine. Three steps need adaptation:

### 3.1 smartart-selector

Adds `pptx_native` to its candidate engine vocabulary. Updated decision logic:

- If `graphic_type` is in {`flowchart`, `org_chart`, `cycle`, `timeline`} **AND** the proposed `enrichment_tier == 'pure_programmatic'` (T0), include `pptx_native` as a candidate engine in at least one of the 2-3 ranked options it returns to narrative-architect.
- Selector's rationale field must explain the editability trade-off when proposing `pptx_native`: "Editable by speaker after delivery, locked to PowerPoint's process palette."
- Selector's confidence score for `pptx_native` is biased *down* slightly (-0.1) to bias towards the visually richer `custom_svg` unless the speaker has indicated post-delivery editing matters. This bias is configurable.

### 3.2 smartart-extractor

Extractor must produce a data model the new engine understands. For the four supported graphic types, the extracted spec already has the right *shape* (flat list for process/cycle, tree for org chart, time-anchored stages for timeline). The new engine just consumes a different field on the spec — `spec.data.steps` or `spec.data.nodes` depending on the layout. Extractor changes are mechanical: when `engine == 'pptx_native'`, populate `spec.data` with the keys the engine expects, in addition to (not instead of) the existing fields, so the `custom_svg` draft preview still works.

### 3.3 smartart-renderer

`_ENGINE_DISPATCH` gains a new entry: `'pptx_native': render_pptx_native`. The dispatcher needs one architectural change: existing engines return a single PNG path. `pptx_native` returns a richer structure:

```python
{
    'kind': 'pptx_native',
    'diagram_parts_dir': '/path/to/diagram_parts/slide_NN/',  # the four files
    'preview_png_path': '/path/to/draft_preview.png',          # custom_svg fallback for review
    'slide_patch': {                                            # instructions for the assembler
        'placeholder_id': 'smartart_NN',
        'layout_uri': 'urn:.../layout/process1',
        'rels_to_add': [...],
        'content_types_to_add': [...],
    }
}
```

The renderer continues to populate the manifest entry the same way for downstream consumers, but the `engine_used`/`file_path` fields point to the diagram parts directory and the new field `slide_patch` carries the assembler instructions.

### 3.4 deck-assembler

This is the most invasive change. The assembler currently runs PptxGenJS to build slides, embedding images by file path. For `pptx_native` slides, the flow becomes two-stage:

**Stage 1 (PptxGenJS):** the assembler builds the slide as it would for a `composed` slide, but where the graphic would go it places a `<p:sp>` rectangle as a placeholder, with a custom name like `smartart_placeholder_<slide_number>`. Header, footer, body text, and any other PptxGenJS shapes are constructed normally.

**Stage 2 (Python post-process):** after `pptx-deck-assembler` finishes writing the `.pptx` file, a new `inject_pptx_native_smartart.py` step:
1. Opens the `.pptx` zip in update mode
2. For each slide whose strategy includes a `pptx_native` smartart entry:
   - Reads the slide XML
   - Locates the `<p:sp>` placeholder by its name
   - Captures the placeholder's `<p:xfrm>` (offset + extents)
   - Replaces the `<p:sp>` element with a `<p:graphicFrame>` containing a `<dgm:relIds>` pointing at four new relationship IDs
   - Writes the four diagram parts (`data{n}.xml`, `layout{n}.xml`, `quickStyle{n}.xml`, `colors{n}.xml`) into `ppt/diagrams/`
   - Adds the four relationships to the slide's `_rels/slide{n}.xml.rels`
   - Adds the four content type overrides to `[Content_Types].xml`
   - **Does not** write `drawing{n}.xml` — PowerPoint will regenerate on first open
3. Saves the zip

The post-process step is idempotent and runs after every assemble. Slides with no `pptx_native` graphics pass through untouched.

**Technique verified by spike 3** (see spike report §10). A 5-step process diagram was successfully injected into a blank host `.pptx` (title + subtitle placeholders, no existing SmartArt, rId1 only), allocating rIds 2-5 for the new diagram parts and inserting a `<p:graphicFrame>` into the existing `<p:spTree>`. PowerPoint Mac opens the result with no repair dialog, renders the diagram correctly, and all editability checks (Design ribbon, Text Pane, Add Shape, Change Layout in-group) pass.

### 3.5 deck-qa

Three new checks (SA-06 through SA-08):

| Check | Logic | Failure mode |
|---|---|---|
| **SA-06** Diagram parts present | For each slide with `pptx_native` smartart, confirm the four diagram parts exist in the assembled `.pptx` | Engine emitted nothing or post-process step skipped |
| **SA-07** Slide references diagram | Confirm the slide XML contains a `<p:graphicFrame>` with `<dgm:relIds>` pointing at all four parts (no orphaned placeholders, no missing relationships) | Stage 1/2 mismatch |
| **SA-08** No drawing cache | Confirm `ppt/diagrams/drawing{n}.xml` does *not* exist for any `pptx_native` graphic | Engine left a stale cache that would override the layout algorithm |

There is no `SA-XX is the SmartArt Design ribbon visible` check — that requires PowerPoint and is the manual gate at delivery time.

---

## 4. Engine Architecture

### 4.1 File layout

```
src/smartart_pptx_native/
  __init__.py
  engine.py                  # render() entry point + dispatcher
  data_model.py              # XML construction primitives (gid, build_pt, build_cxn)
  assembler_patch.py         # Stage 2 post-process: inject diagram parts into assembled .pptx
  layouts/
    __init__.py              # LAYOUT_REGISTRY mapping graphic_type → builder
    catalog.json             # Layout catalog — single source of truth (see §5)
    catalog.schema.json      # JSONSchema for catalog entries
    catalog.py               # load_catalog(), get_entry(), validate against schema
    process.py               # process1 builder — reads SEED_PATH/LAYOUT_URI/max from catalog
    cycle.py                 # cycle2 builder
    org_chart.py             # orgChart1 builder
    timeline.py              # basicTimeline1 builder
```

`engine.py::render(spec, style_guide, output_dir)` dispatches by `spec.graphic_type` to the appropriate layout builder, returns the structured result described in §3.3. Layout modules read their seed path, layout URI, and capacity constraints from `catalog.json` at import time — there are no per-layout constants embedded in Python code.

### 4.2 Layout module pattern

Each layout module exports two functions:

```python
SEED_PATH = "tests/fixtures/smartart_seeds/process1_seed.pptx"
LAYOUT_URI = "urn:microsoft.com/office/officeart/2005/8/layout/process1"

def build_data_model(extracted: dict, doc_prset: str) -> bytes:
    """Construct ppt/diagrams/data1.xml bytes for this layout from extracted data.

    Args:
        extracted: smartart spec data section, e.g. {'steps': ['Research', ...]}
        doc_prset: the loTypeId/qsTypeId/csTypeId attribute string extracted
                   from the seed (carries layout binding)

    Returns:
        UTF-8 encoded XML for data1.xml
    """

def build_diagram_parts(extracted: dict, output_dir: str) -> dict:
    """Produce the four diagram parts from a seed copy + new data model.

    Returns dict with keys 'data', 'layout', 'quickStyle', 'colors',
    each pointing at a file path under output_dir.
    """
```

The data model construction is the only place each layout differs. `data_model.py` provides primitives — `make_doc_pt(loTypeId, qsTypeId, csTypeId)`, `make_node_pt(text, is_asst=False)`, `make_par_trans()`, `make_sib_trans()`, `make_cxn(src, dst, src_ord, par_id, sib_id)` — that the layout modules compose. ~30-50 lines of glue per layout for flat-list layouts (process, cycle, timeline); ~60-80 lines for `org_chart.py` because of the recursive tree walk.

**Flat-list layouts** (process1, cycle2, basicTimeline1) iterate `extracted['steps']` or `extracted['stages']` and emit one node + parTrans/sibTrans pair + one cxn from `doc` per item.

**Hierarchical layouts** (orgChart1) recurse over a tree. Each node emits itself + parTrans/sibTrans pair + a cxn from its *parent* (which may be any intermediate node, not just `doc`), then recurses into its children. Org chart also passes `is_asst=True` to `make_node_pt` when the tree node is flagged as an assistant — PowerPoint renders those sideways from the parent with a distinctive connector instead of below as a regular subordinate. The distinction is encoded purely by the `type="asst"` attribute on the destination point; the connection structure is identical to a regular subordinate. Verified by spike 4.

### 4.3 Seed lookup at engine start time

`engine.py` reads each seed once at module import and caches:
1. The four diagram parts as raw bytes (passes through `colors1.xml`/`quickStyle1.xml`/`layout1.xml` unchanged — we never mutate these)
2. The `doc_prset` string (the `loTypeId="..." qsTypeId="..." csTypeId="..."` attributes), extracted by regex from the seed's `data1.xml`

This means the runtime cost of each render is just data-model construction + zip operations — no per-call file IO against the seeds. Module import time goes up by ~50 ms (4 seeds × ~12 ms each).

---

## 5. Layout Catalog

### 5.1 Purpose

Every layout the engine supports needs a **structured description** that seven different consumers can read:

| Consumer | Reads the catalog to |
|---|---|
| Engine layout module | Know its own seed path, layout URI, builder function |
| `smartart-extractor` | Know per-layout max label length / max node count for truncation + fallback decisions |
| `smartart-selector` agent | Make informed recommendations — selector's prompt cites the catalog rather than restating layout info |
| `narrative-architect` review | See meaningful per-layout rationale when evaluating selector proposals |
| QA checks (SA-06–08) | Enforce max-capacity constraints programmatically |
| Manual gate checklists | Derive per-layout verification steps |
| New contributors + speakers | Understand the layout palette without reading source code |

Without a catalog, every one of those consumers has to hardcode or restate the per-layout knowledge, and the seven copies drift. The catalog is the single source of truth.

### 5.2 Location and format

```
src/smartart_pptx_native/layouts/
  catalog.json         # data
  catalog.schema.json  # JSONSchema v7 validator
  catalog.py           # Python loader — load_catalog() / get_entry(layout_id)
```

JSON (not YAML) so Python stdlib can parse it with no new dependency, and so we can ship `catalog.schema.json` alongside it for structural validation. The schema is enforced by a test (`tests/test_pptx_native_catalog_schema.py`) that runs against every entry on every CI run — any entry missing a required field, or violating a constraint, fails the build.

### 5.3 Entry schema

Every entry has the following fields (required unless marked optional):

| Field | Type | Purpose |
|---|---|---|
| `id` | string | Stable identifier, used by extractor and selector (e.g., `"process1"`). Must match a layout module filename. |
| `layout_uri` | string | The full `urn:microsoft.com/office/officeart/...` URI PowerPoint binds the layout to. Extracted verbatim from the seed. |
| `seed_path` | string | Path to the hand-authored seed, relative to repo root. Must exist at engine import time. |
| `builder_module` | string | Python dotted path to the layout's data model builder (e.g., `src.smartart_pptx_native.layouts.process`). |
| `display_name` | string | Human-friendly name shown in speaker-facing messaging (e.g., `"Basic Process"`). |
| `category` | enum | One of `Process`, `Cycle`, `Hierarchy`, `Timeline`, `List`, `Relationship`, `Matrix`, `Pyramid`, `Picture` — matching PowerPoint's SmartArt picker taxonomy. |
| `v1` | bool | True if in v1 scope. Future layouts can be added with `v1: false` without affecting behaviour. |
| `data_shape` | enum | `flat_list` or `hierarchical`. Determines which data-model builder primitive set applies. |
| `node_type_capabilities` | string[] | Which node types this layout supports beyond the default regular node. Valid values: `"asst"` (assistant, renders sideways). Empty list for layouts that only support regular nodes. Consumed by extractor to validate extracted data, and by selector to decide if the layout can represent the speaker's intent. |
| `visual_character` | string | 1-3 sentences describing what the rendered graphic looks like. Narrative-architect sees this when evaluating selector proposals. |
| `min_nodes` | int | Minimum node count. Below this, extractor rejects and falls back to custom_svg. |
| `max_nodes` | int | Maximum node count. Above this, extractor truncates or falls back. |
| `max_label_chars` | int | Per-node text length cap. Empirically determined during manual gating. |
| `max_label_chars_rationale` | string | Why the cap is what it is — links to manual gate findings. |
| `when_to_use` | string[] | Narrative scenarios where this layout is the right choice. Feeds selector prompt. |
| `when_not_to_use` | string[] | Anti-patterns. Feeds selector prompt. |
| `selector_rationale_template` | string | Template the selector uses when proposing this layout — supports `{n}`, `{first}`, `{last}` placeholders the selector fills from extracted content. |
| `example_input` | object | Small input object the tests and docs generator use to render a sample. |
| `integration` | object | `smartart_type_mappings` (list of graphic_type values this layout can back) and `replaces_custom_svg_when` (the condition under which the selector should bias toward pptx_native vs custom_svg for overlapping graphic types). |
| `engine` | enum | Always `pptx_native` for v1 entries. Included so the schema can host `custom_svg` entries in a future refactor (§16 non-goal note). |
| `extensions` | object (optional) | Free-form object for layout-specific extras. Not used in v1; reserved for future extensions. |

### 5.4 Example entry — process1

```json
{
  "id": "process1",
  "layout_uri": "urn:microsoft.com/office/officeart/2005/8/layout/process1",
  "seed_path": "tests/fixtures/smartart_seeds/process1_seed.pptx",
  "builder_module": "src.smartart_pptx_native.layouts.process",
  "display_name": "Basic Process",
  "category": "Process",
  "v1": true,
  "engine": "pptx_native",

  "data_shape": "flat_list",
  "node_type_capabilities": [],
  "visual_character": "Horizontal row of connected rounded rectangles with chevron arrows between them. Boxes share a single accent colour by default; PowerPoint reflows them into 2 rows automatically beyond ~7 steps.",

  "min_nodes": 2,
  "max_nodes": 9,
  "max_label_chars": 24,
  "max_label_chars_rationale": "PowerPoint shrinks labels above 24 chars to unreadable sizes on 16:9 slides. Empirically determined during manual gate — revisit if a future layout reflows more gracefully.",

  "when_to_use": [
    "Sequential processes where each step depends on the previous one",
    "Pipelines with a clear start and end",
    "How-to explanations with 3-7 stages",
    "Methodology walkthroughs where order matters"
  ],
  "when_not_to_use": [
    "Cyclical processes (use cycle2)",
    "Hierarchical decisions (use orgChart1)",
    "Timelines with date anchors (use basicTimeline1)",
    "More than 9 steps (the visual becomes unreadable)",
    "Parallel or concurrent steps (no native representation in this layout)"
  ],

  "selector_rationale_template": "process1 is the right choice when the content describes a sequence of {n} steps from \"{first}\" to \"{last}\" where order matters. Delivers editable SmartArt — speaker can add/rename/reorder steps in PowerPoint after delivery.",

  "example_input": {
    "steps": ["Research", "Design", "Build", "Test", "Ship"]
  },

  "integration": {
    "smartart_type_mappings": ["flowchart"],
    "replaces_custom_svg_when": "graphic_type == 'flowchart' AND enrichment_tier == 'pure_programmatic' AND node_count <= 9 AND max(label_length) <= 24"
  }
}
```

### 5.5 Example entry — orgChart1 (shows hierarchical shape + asst capability)

```json
{
  "id": "orgChart1",
  "layout_uri": "urn:microsoft.com/office/officeart/2005/8/layout/orgChart1",
  "seed_path": "tests/fixtures/smartart_seeds/orgChart1_seed.pptx",
  "builder_module": "src.smartart_pptx_native.layouts.org_chart",
  "display_name": "Organization Chart",
  "category": "Hierarchy",
  "v1": true,
  "engine": "pptx_native",

  "data_shape": "hierarchical",
  "node_type_capabilities": ["asst"],
  "visual_character": "Classic organization chart — root node at top, subordinates branching downward in a tree. Assistant nodes render to the side of their parent with a right-angle connector, distinct from the regular subordinate row below.",

  "min_nodes": 3,
  "max_nodes": 25,
  "max_label_chars": 32,
  "max_label_chars_rationale": "Org chart boxes are wider than process steps and can accommodate longer role titles. Empirically determined during manual gate — revisit if a deep tree forces smaller boxes.",

  "when_to_use": [
    "Reporting structures and management hierarchies",
    "Team compositions with clear parent-child relationships",
    "Any tree-shaped content with 3+ levels of nesting",
    "Structures that include assistants or advisors sitting outside the main reporting line"
  ],
  "when_not_to_use": [
    "Flat lists of peers (use process1 or cycle2)",
    "Cyclic relationships (use cycle2)",
    "More than 4 levels deep or more than 25 total nodes (the visual becomes unreadable at 16:9)",
    "Matrix or network relationships (orgChart1 is strictly a tree)"
  ],

  "selector_rationale_template": "orgChart1 is the right choice when the content describes a hierarchy of {n} roles with {depth} levels. Delivers editable SmartArt — speaker can add subordinates or assistants, promote/demote, and restructure the tree in PowerPoint after delivery.",

  "example_input": {
    "tree": {
      "title": "CEO",
      "children": [
        {"title": "Executive Assistant", "asst": true},
        {
          "title": "CTO",
          "children": [
            {"title": "Backend Lead"},
            {"title": "Frontend Lead"}
          ]
        },
        {
          "title": "CFO",
          "children": [
            {"title": "Finance Manager"}
          ]
        }
      ]
    }
  },

  "integration": {
    "smartart_type_mappings": ["org_chart", "decision_tree"],
    "replaces_custom_svg_when": "graphic_type IN ('org_chart', 'decision_tree') AND enrichment_tier == 'pure_programmatic' AND total_nodes <= 25 AND max_depth <= 4"
  }
}
```

The `node_type_capabilities: ["asst"]` flag is what tells the extractor that this layout can represent assistant nodes — so the extractor can accept `{"title": "...", "asst": true}` in extracted trees without erroring, and the selector can include assistant support in its rationale when pitching orgChart1 for content that mentions advisors, chiefs of staff, executive assistants, etc.

Four entries of this shape — one per v1 layout — total ~400-500 lines of structured JSON. Review-friendly, diff-friendly, easy to update when manual gating finds a new edge case.

### 5.5 Evolution — B→A

The catalog is delivered in two stages:

**Stage B — delivered with Phase 1 engine scaffold.** Minimal but functional:
- Schema file in place and validated by test
- One entry (process1) populated in full
- `catalog.py` loader with `load_catalog()` / `get_entry(layout_id)`
- Engine, extractor, and selector all consume the catalog programmatically — no hardcoded per-layout constants in Python

**Stage A — delivered by Phase 4.5 Catalog Consolidation** (new phase, between Phase 4 and Phase 5):
- Markdown generator script → `docs/pptx-native-smartart-catalog.md` (auto-regenerated, checked in, CI drift detection)
- Rationale template linting (every entry has all required fields; templates reference real placeholders)
- Per-entry test coverage (each entry has ≥ 1 data-model unit test + ≥ 1 manual-gate reference)
- Selector prompt refactor — prompt stops restating layout info and instead gets entries injected at build time
- A structured review pass on catalog content as a design artifact, not just data

Phases 2, 3, 4 each add their layout's catalog entry as part of the layout PR. By Phase 4 finale all four entries are present. Phase 4.5 then promotes the catalog to first-class.

### 5.6 Out of scope for v1

- **Custom_svg entries.** The schema has an `engine` field and an `extensions` block specifically so a future refactor can host the existing ten `custom_svg` graphic types alongside the four `pptx_native` layouts in a single catalog. That refactor is not in this feature — it's a separate follow-up, explicitly captured in the §16 non-goals.
- **Runtime catalog mutation.** The catalog is a build-time artifact. The engine does not support loading external catalogs at runtime, and the selector does not support learning new layouts without a code change.
- **Localisation of `when_to_use` / `when_not_to_use` / `selector_rationale_template`.** English only in v1.

---

## 6. Seed Authoring Workflow

### 5.1 Initial seed creation (one-time per layout)

Documented as a step-by-step in `docs/dev/smartart-seed-authoring.md` (new file). Summary:

1. Open PowerPoint Mac → New blank presentation
2. Insert → SmartArt → choose category and layout
3. **Do not edit the placeholder text.** The default placeholders are fine; we replace `data1.xml` wholesale.
4. File → Save As → `.pptx` format → save to `tests/fixtures/smartart_seeds/<layout_name>_seed.pptx`
5. Quit PowerPoint
6. Run `python tools/inspect_seed.py tests/fixtures/smartart_seeds/<layout_name>_seed.pptx` (new diagnostic script) to confirm the seed contains all four diagram parts and report the `loTypeId`/`qsTypeId`/`csTypeId` it found

### 5.2 Seed sanity check (committed test)

A new test `tests/test_smartart_seeds.py` validates each committed seed at test time:
- File exists and is a valid zip
- Contains `ppt/diagrams/{data1,layout1,quickStyle1,colors1}.xml`
- The `data1.xml`'s `doc` point has non-empty `loTypeId` matching the expected layout URI
- The slide references the diagram via `<dgm:relIds>` (not a flat group)

This catches the case where a seed gets corrupted, accidentally edited, or replaced with the wrong layout.

### 5.3 Seed replacement / upgrade

When a new PowerPoint version emits subtly different diagram XML, we can drop in a new seed without code changes — the engine never touches `layout1.xml`/`quickStyle1.xml`/`colors1.xml`. As long as the new seed's `loTypeId` matches what the engine expects, it works.

---

## 7. Lifecycle: Draft vs Production

The existing pipeline distinguishes:
- **Draft phase** — many cheap iterations, image-reviewer scores each graphic, enrichment is not yet finalised
- **Production phase** — single high-cost render run with finalised enrichment, used for delivery

`pptx_native` is **production-only** for two interlocking reasons:

1. **Image-reviewer can't score it.** LibreOffice can't render it (we proved this in the spike); the only renderer that can is PowerPoint itself, which is manual.
2. **Editability has no draft analogue.** The whole point of the engine is the final-file experience; there is no "iterate cheaply" version of editability.

The mitigation is the **draft preview proxy**: when the selector picks `pptx_native` for a slide, the smartart-renderer *also* runs `custom_svg` for that slide during draft. The custom_svg version is what the image-reviewer sees, what the speaker sees in the draft preview, and what the comparator (if invoked for sibling slides) compares against. Only the production-phase render call invokes the `pptx_native` engine.

This keeps the iteration loop fast and free, while still delivering editable graphics in production. The user accepts that **the production delivery is the first time anyone sees how `pptx_native` actually rendered** — a constraint that has to be made explicit in the conductor's status messaging so the speaker knows to open the file in PowerPoint after delivery, not just trust the draft.

### Conductor messaging

When a deck is delivered with `pptx_native` slides, the conductor's final status output includes:

```
N slide(s) use editable PowerPoint SmartArt (pptx_native engine).
These were not pre-rendered — please open the .pptx in PowerPoint
to verify visual quality before presenting.

Slides with editable SmartArt:
  Slide  4: process diagram (5 steps)
  Slide  9: cycle diagram (4 phases)
  Slide 12: org chart (3 levels, 11 nodes)
  Slide 21: timeline (6 stages)
```

---

## 8. SmartArt Selector Adaptations

The selector's prompt template gains a new section explaining the `pptx_native` engine:

> When proposing engines for graphics in {flowchart, cycle, org_chart, timeline} categories where enrichment_tier is pure_programmatic, you may recommend `pptx_native`. This engine produces graphics the speaker can edit in PowerPoint after delivery (add nodes, rename, restyle). The trade-off is that the visual style is locked to PowerPoint's built-in palette for that layout — you cannot override fonts, colours, or shapes beyond what PowerPoint's quickStyle system allows. Recommend `pptx_native` when:
>
> - The audience is technical / corporate and the speaker is likely to want to update the diagram before re-presenting
> - The graphic is structurally simple (≤ 9 nodes for flowchart, ≤ 8 for cycle, ≤ 25 for org_chart, ≤ 7 for timeline)
> - The narrative-architect has indicated post-delivery editing is valuable
>
> Do *not* recommend `pptx_native` when:
>
> - The graphic needs custom colour-coding beyond PowerPoint's quickStyle palette
> - The data is denser than the layout supports
> - The enrichment tier is T1 or higher (AI imagery overlaid on the graphic defeats editability)

The narrative-architect remains the final decider via the existing approve/reject loop (max 2 rounds). No new agent, no new negotiation rounds.

---

## 9. Schema Changes

### 8.1 SmartArt spec contract

`engine` enum gains `pptx_native` as a valid value.

New optional field on the spec: `pptx_native_layout_uri` (string) — populated by the extractor when `engine == 'pptx_native'`, copied verbatim from the corresponding layout module's `LAYOUT_URI` constant. The renderer uses it to look up the seed.

### 8.2 SmartArt manifest entry

New optional field on the manifest entry: `pptx_native_diagram_parts` (object), with keys:
- `data` (string) — path to data{n}.xml
- `layout` (string)
- `quickStyle` (string)
- `colors` (string)
- `placeholder_name` (string) — the PptxGenJS shape name the assembler must locate to inject the graphicFrame

When this field is present, the assembler post-process step processes this graphic. When absent, the graphic is treated as a regular image embed (existing behaviour).

### 8.3 StrategyMap

No changes — `smartart` strategy already exists, the engine is just a value of the existing `smartart_config.engine` field.

---

## 10. Test Plan

### 9.1 Unit tests

| Test file | Coverage |
|---|---|
| `tests/test_smartart_pptx_native_data_model.py` | XML construction primitives — make_doc_pt, make_node_pt, make_par_trans, make_sib_trans, make_cxn. Round-trip via `xmllint --noout` to confirm well-formedness. |
| `tests/test_smartart_pptx_native_layouts_process.py` | process1 builder — given 3, 5, 9 step inputs, produces valid data1.xml with correct point/connection counts |
| `tests/test_smartart_pptx_native_layouts_cycle.py` | cycle1 — same matrix, plus the cycle algorithm's specific ordering |
| `tests/test_smartart_pptx_native_layouts_org_chart.py` | orgChart1 — recursive tree, parent/child connections, levels 1-4 |
| `tests/test_smartart_pptx_native_layouts_timeline.py` | basicTimeline1 — chronological ordering, optional date strings |
| `tests/test_smartart_seeds.py` | Seed sanity (per §6.2) — runs against committed seeds |
| `tests/test_smartart_pptx_native_engine.py` | Engine entry point — mocks layout builders, confirms dispatch and result structure |
| `tests/test_smartart_pptx_native_assembler_patch.py` | Stage 2 post-process — given a fixture .pptx with placeholder shapes and a fixture diagram parts dir, runs the patch and confirms the output zip contains correct relationships, content types, and graphicFrame |
| `tests/test_smartart_pptx_native_qa_checks.py` | SA-06 / SA-07 / SA-08 |

### 9.2 Integration test

`tests/test_smartart_pptx_native_e2e.py` runs the full pipeline against a 4-slide synthetic deck (one slide per supported layout), asserts:
- Renderer produces diagram parts for all 4 slides
- Assembler post-process injects them
- QA checks pass
- The resulting `.pptx` has 4 graphic frames with correct `<dgm:relIds>` references

### 9.3 Manual gate

For each new layout added to v1, after CI passes, a human runs:

```bash
.venv/bin/python tests/manual/build_pptx_native_demo.py <layout>
```

which produces `tmp/manual_pptx_native_<layout>.pptx`, then opens it in PowerPoint Mac and confirms:

1. File opens with no repair dialog
2. SmartArt graphic visible with correct content
3. SmartArt Design ribbon appears when clicked
4. Text Pane is populated and editable
5. Add Shape works
6. Re-saving the file from PowerPoint and re-opening produces the same content

A `tests/manual/MANUAL_GATE.md` checklist captures the result of each layout's gate. The checklist is committed; the `.pptx` files are not.

---

## 11. Open Questions

Each of these wants a decision before implementation begins.

### 10.1 Does the technique generalise across layouts? — **RESOLVED**

**Resolved 2026-04-08 by spike 2** (see spike report §9). A 6-phase cycle diagram was built by mutating `cycle1_seed.pptx` (which binds to `urn:.../layout/cycle2` — Mac PowerPoint's "Basic Cycle" maps to `cycle2`, not `cycle1`) with the same data-model builder used for `process1`, with only the `loTypeId` attribute changed. PowerPoint Mac opens the result as editable SmartArt, regenerates the presentation tree from `layout1.xml`, and all editability checks pass.

**Key finding:** the `cycle` algorithm regenerates as cleanly as `lin`. The flat-list data shape (doc + node + parTrans + sibTrans with untyped `cxn` connections) is the *same* for both — only the layout binding URI changes. This strongly suggests `basicTimeline1` (another flat-list layout) will work without per-layout surprises. `orgChart1` is the one remaining unknown, because it uses the hierarchical `hierChild` algorithm with a tree data shape — spike 4 (org chart mutation) should run before that layout's engine module is written.

### 10.2 How are seeds created on Windows-only PowerPoint installs?

Mac PowerPoint stores the `diagramDrawing` rel at the slide level and uses `vnd.ms-office` content type. Windows PowerPoint may store it at the data1.xml level (the form Phase 1 §2.2 documented) and use the `vnd.openxmlformats-officedocument` content type. If so, `inject_pptx_native_smartart.py` needs to detect both forms — or we standardise on Mac-authored seeds and document the constraint.

### 10.3 Should the comparator pattern apply at all?

Section 2 says no — `pptx_native` opts out because no rasterised preview exists for image-reviewer to score. But there is a weak alternative: render the seed's *cached drawing* as the preview (PowerPoint already wrote it). It would not reflect the new data we're injecting (text would still say "[Text]") but it would show the layout. Worth it? Probably no — the custom_svg draft proxy is structurally more accurate.

### 10.4 What's the assembler post-process invocation point?

Two options:
- **Inside `build_deck.js`** — after PptxGenJS writes the file, invoke a Python subprocess from Node. Adds a Node→Python boundary.
- **Outside `build_deck.js`** — `conductor.py` runs `build_deck.js`, then runs `inject_pptx_native_smartart.py` as a separate step. Cleaner separation; conductor already orchestrates Python steps.

Recommend the second. Conductor is already the orchestrator; build_deck stays single-purpose.

### 10.5 What happens if PowerPoint Mac rejects the production output?

Section 6 says "the production delivery is the first time anyone sees how `pptx_native` actually rendered." If a layout breaks (PowerPoint repair dialog, or opens but Design ribbon missing), the speaker has no fallback. Two options:

- **Belt-and-braces:** smartart-renderer always renders custom_svg as well, and the assembler embeds *both* — the editable SmartArt and a hidden image fallback. If PowerPoint borks the diagram, the speaker can delete it and the image is there. Adds package size.
- **Trust + manual gate:** rely on the §10.3 manual gate to catch any layout that breaks before it ships, and the §7 conductor messaging to remind the speaker to verify before presenting. Smaller package, but a single point of failure.

Recommend trust + manual gate for v1, then revisit if a regression slips through.

### 10.6 Licensing — can we ship Mac PowerPoint–authored seeds?

Phase 1 §8 flagged this as plausibly an Office EULA concern, distinct from the OOXML format itself. Our seeds contain *only* a single empty SmartArt frame with no Microsoft template content (no Office.com clip art, no theme imports, no built-in slide masters beyond the default blank). This is plausibly fair use, but **the spec should not be merged without legal review.** Add a `LICENSING.md` in `tests/fixtures/smartart_seeds/` documenting how each seed was created and what it contains.

### 10.7 How does the engine handle text overflow?

PowerPoint's process layout will shrink text to fit a fixed box. If a step label is 50 characters, PowerPoint will render it at 8pt. The current `custom_svg` engine has explicit overflow strategies (multi-line wrap, font stepdown to a 12pt floor, outside-bar placement with leader lines). `pptx_native` has none of those — PowerPoint owns the rendering. **Mitigation:** the extractor enforces a max-length-per-label constraint (e.g., 24 characters for process, 18 for cycle) and rejects extracted data that exceeds it, falling back to `custom_svg` for that slide. The constraint per layout needs to be empirically determined per-layout via the manual gate.

---

## 12. Out of Scope (v1 → potential v2)

These are deliberate exclusions, not oversights:

- **All other PowerPoint built-in layouts** beyond the four chosen — ~150 exist; we add more only if speakers ask for them
- **Style customisation** — speakers get the layout's default quickStyle; no per-deck colour overrides for `pptx_native` graphics
- **Multi-graphic slides** — one `pptx_native` graphic per slide. Two on the same slide need separate diagram numbering (`data2.xml`, `layout2.xml`...) which is straightforward but not in v1
- **Round-trip preservation** — if the speaker edits the graphic in PowerPoint, saves, and re-runs the deck pipeline, their edits will be overwritten by the engine's regeneration. This is the same constraint as every other deck regeneration; it is not specific to `pptx_native`
- **Custom layout authoring** — we ship only PowerPoint built-ins. Authoring custom `dgm:layoutDef` files is a Phase 1 §3 capability we don't need for v1

---

## 13. Implementation Plan

Implementation breaks into these phases. Phase 0 is a validation gate — if it fails, the spec is rethought before any engine code is written.

**Phase 0 — Org chart validation spike**
Mutate an `orgChart1_seed.pptx` with a small hardcoded tree, verify PowerPoint Mac opens as editable SmartArt. Closes the one remaining algorithm family (`hierChild`) not covered by spikes 1-3. Mirror of spike 2's shape; 60 seconds of user time + one throwaway script.

**Phase 1 — Engine scaffold (includes catalog Stage B, per §5.5)**
- `src/smartart_pptx_native/` directory scaffold
- `data_model.py` XML construction primitives (`gid`, `make_doc_pt`, `make_node_pt`, `make_par_trans`, `make_sib_trans`, `make_cxn`)
- `layouts/catalog.schema.json` — JSONSchema for catalog entries
- `layouts/catalog.json` — **one populated entry (process1) in full**, no stubs
- `layouts/catalog.py` — loader with `load_catalog()`, `get_entry(id)`, schema validation
- `layouts/process.py` — process1 builder module, reads its constants from `get_entry("process1")`
- Tests: data model primitives, process1 builder output, catalog schema validation, seed fixture sanity

**Phase 2 — Renderer dispatch + extractor support**
- `engine.py::render()` wired into `_ENGINE_DISPATCH`
- Extractor populates `pptx_native_layout_uri` and enforces per-layout max-length from catalog
- Manifest entry shape extended per §3.3

**Phase 3 — Assembler post-process**
- `inject_pptx_native_smartart.py` — injects diagram parts into assembled .pptx per §3.4 (technique verified by spike 3)
- Conductor invocation after `build_deck.js`
- Integration test with a 1-slide fixture deck
- QA checks SA-06 / SA-07 / SA-08 (since they're tightly coupled to the post-process step)

**Phase 4 — Three more layouts**
Three separate PRs, one per remaining layout. Each PR adds:
- `layouts/<name>.py` builder module
- New entry in `catalog.json`
- Seed sanity test for the new seed
- Data model unit tests
- Manual gate run against PowerPoint Mac, checklist updated

**Phase 4.5 — Catalog consolidation (Stage A, per §5.5)**
Promotes the catalog to first-class after all four entries are in place:
- Markdown generator script → `docs/pptx-native-smartart-catalog.md` (regenerated from catalog.json, checked in, CI drift detection)
- Rationale template linting
- Per-entry test coverage audit
- Selector prompt refactor — prompt stops restating layout info, gets entries injected at build time from `catalog.py`
- Structured review pass on catalog content as a design artifact

**Phase 5 — Selector integration finalisation**
- Selector candidate engine logic (when to propose `pptx_native` vs `custom_svg`)
- Negotiation-loop integration with narrative-architect
- End-to-end tests of the negotiation against synthetic deck fixtures

**Phase 6 — Conductor delivery messaging**
Final status output when `pptx_native` slides are present (per §7).

**Phase 7 — Documentation**
- `docs/dev/smartart-seed-authoring.md` — step-by-step seed creation guide
- `LICENSING.md` in `tests/fixtures/smartart_seeds/` — per-seed provenance
- Manual gate checklist template

Each phase is an independent PR. **Phase 0 is the validation gate** — if the org chart spike fails, the spec is rethought before any engine code is written. Phase 1 through Phase 4.5 are the core build; Phases 5-7 are integration and polish.

---

## 14. Dependencies

- No new Python dependencies (the spike used only stdlib `zipfile`, `re`, `uuid`)
- No new Node dependencies (assembler stays PptxGenJS-based; the post-process is pure Python)
- One PowerPoint Mac install required for seed authoring and manual gating — **this is a hard requirement and must be documented in `docs/dev/smartart-seed-authoring.md`**

---

## 15. Success Criteria

The engine ships v1 when:

1. All four supported layouts have committed seeds passing `tests/test_smartart_seeds.py`
2. All four layouts have passed the §10.3 manual gate in PowerPoint Mac
3. The integration test (§10.2) passes in CI
4. A demo deck with one slide per layout has been built end-to-end and opened in PowerPoint Mac with no repair dialog
5. The conductor delivers status messaging when `pptx_native` slides are present
6. Legal review (§11.6) has signed off on shipping the seeds

---

## 16. Non-Goals

To be explicit about what this is *not*:

- Not a replacement for `custom_svg` for the four supported graphic types — the selector continues to recommend `custom_svg` for visually-rich enrichment cases
- Not a replacement for `mermaid` or `vega_lite` for any graphic type
- Not a "make all graphics editable" project — only the four PowerPoint built-in layouts are in scope
- Not Windows-targeted in v1 — Mac authoring/verification only; Windows compatibility is the §11.2 open question
- Not free of manual review — the manual gate at §10.3 is a permanent part of the engine's lifecycle, not a temporary scaffolding
