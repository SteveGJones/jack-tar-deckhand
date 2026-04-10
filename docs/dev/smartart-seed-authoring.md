# Authoring pptx_native SmartArt Seeds

**Who this is for:** Developers adding a new PowerPoint built-in SmartArt layout to the `pptx_native` engine.

**What you'll produce:** A hand-authored `.pptx` file (a "seed") containing exactly one empty SmartArt graphic of the target layout. The engine reads it at runtime to get layout1.xml, quickStyle1.xml, and colors1.xml as opaque blobs, and its doc-point URIs tell PowerPoint which layout to use.

**Prerequisites:**
- PowerPoint for Mac installed and working
- The target layout's catalog entry planned (see `docs/pptx-native-smartart-catalog.md` for existing entries)
- About 90 seconds of your time per seed

---

## Step-by-step

### 1. Open PowerPoint and insert the layout

1. Open PowerPoint for Mac → **New** → choose any blank template
2. Delete any existing slides except one — you want a presentation with exactly one blank slide
3. **Insert → SmartArt**
4. Pick the category you want (Process, Cycle, Hierarchy, etc.)
5. Click the specific layout tile you want to seed (e.g., "Basic Process", "Basic Cycle", "Organization Chart")
6. Click **OK** — PowerPoint inserts a default SmartArt graphic with 3-5 placeholder boxes on the slide

### 2. Leave the placeholder text alone

**Do not edit the placeholder labels.** The engine replaces `data1.xml` wholesale at runtime, so the placeholder content is irrelevant — only the four diagram parts' structure matters. Editing placeholders risks PowerPoint flattening the SmartArt on save.

### 3. Save to the fixture directory

1. **File → Save As…**
2. **Format:** choose `PowerPoint Presentation (.pptx)` — **NOT** `.pptm`, `.pps`, or `.ppt`
3. **Location:** `tests/fixtures/smartart_seeds/`
4. **Filename:** use the layout's PowerPoint URI short name + `_seed.pptx`. Examples:
   - `process1_seed.pptx` for Basic Process
   - `cycle1_seed.pptx` for Basic Cycle (note: PowerPoint Mac's "Basic Cycle" binds to `cycle2` internally — the seed filename can still be `cycle1_seed.pptx` for consistency with the catalog entry's `seed_path`)
   - `orgChart1_seed.pptx` for Organization Chart
5. Click **Save**

### 4. Quit PowerPoint

**This matters.** PowerPoint Mac locks the file while it's open, which prevents the test suite's seed sanity checks from reading it. Quit the app entirely (⌘Q, not just closing the window).

### 5. Find the actual layout URI

The `loTypeId` attribute on the seed's `<dgm:pt type="doc">` element is the *authoritative* layout URI — not whatever you think PowerPoint "should" be using. Extract it:

```bash
unzip -p tests/fixtures/smartart_seeds/<your_seed>.pptx ppt/diagrams/data1.xml \
  | grep -oE 'loTypeId="[^"]+"'
```

You'll see something like:

```
loTypeId="urn:microsoft.com/office/officeart/2005/8/layout/cycle2"
```

**Write down this URI verbatim** — it goes into the catalog entry's `layout_uri` field. Do NOT assume the URI from PowerPoint's gallery label. Mac PowerPoint's "Basic Cycle" maps to `cycle2`, not `cycle1`, and that kind of surprise is the reason we always extract the URI from the seed.

### 6. Add the catalog entry

Edit `src/smartart_pptx_native/layouts/catalog.json` and add a new entry following the schema in `catalog.schema.json`. Required fields:

- `id` — stable identifier, usually matches the URI's short name
- `layout_uri` — the URI you extracted in step 5
- `seed_path` — path to the seed file relative to repo root
- `builder_module` — Python dotted path to the layout builder module you'll write next
- `display_name` — human-friendly name (e.g., "Basic Cycle")
- `category` — one of Process / Cycle / Hierarchy / Timeline / List / Relationship / Matrix / Pyramid / Picture
- `v1` — true if in v1 scope
- `engine` — always `"pptx_native"` for v1 entries
- `data_shape` — `flat_list` or `hierarchical`
- `node_type_capabilities` — list of special node types the layout supports (e.g., `["asst"]` for org chart)
- `visual_character` — 1-3 sentence description of what the rendered graphic looks like
- `min_nodes` / `max_nodes` / `max_label_chars` — capacity constraints
- `max_label_chars_rationale` — explain why the limit is what it is
- `when_to_use` / `when_not_to_use` — list of guidance items for the selector
- `selector_rationale_template` — template with `{n}`, `{first}`, `{last}` placeholders
- `example_input` — small input object the tests will use
- `integration.smartart_type_mappings` — which `graphic_type` values this layout can back
- `integration.replaces_custom_svg_when` — the selector routing condition

### 7. Regenerate the catalog markdown

```bash
.venv/bin/python -m src.smartart_pptx_native.layouts.catalog_markdown
```

This overwrites `docs/pptx-native-smartart-catalog.md`. Commit both files together — the drift-detection test enforces they match.

### 8. Write the layout builder module

Create `src/smartart_pptx_native/layouts/<your_layout>.py`. The pattern:

```python
from src.smartart_pptx_native import data_model
from src.smartart_pptx_native.layouts import catalog

LAYOUT_ID = "your_layout_id"


class YourLayoutBuildError(ValueError):
    pass


def _validate(extracted, entry):
    # Check required keys, count constraints, label lengths
    ...


def build_data_model(extracted):
    entry = catalog.get_entry(LAYOUT_ID)
    # validate, then walk the data and emit points + connections via
    # data_model.make_doc_pt, make_node_pt, make_par_trans, make_sib_trans,
    # and make_cxn
    return data_model.wrap_data_model(pts_xml, cxns_xml)


def get_layout_uri():
    return catalog.get_entry(LAYOUT_ID)["layout_uri"]


def get_seed_path():
    return catalog.resolve_seed_path(catalog.get_entry(LAYOUT_ID))
```

Use `process.py` (flat list) or `org_chart.py` (recursive tree) as templates — they cover the two data shapes v1 supports.

### 9. Add extractor routing

In `src/smartart_extractor.py`, the `_extract_pptx_native` function maps `graphic_type` values to layout-specific data shapes. Add a branch for your new graphic type:

```python
if graphic_type == 'your_new_type':
    return {
        'engine': 'pptx_native',
        'graphic_type': graphic_type,
        'data': {'your_key': cleaned_labels},
    }
```

### 10. Write tests

Create `tests/test_pptx_native_layouts_<your_layout>.py` following the pattern in `test_pptx_native_process.py`:

- Catalog entry present with expected fields
- Builder happy path (min, middle, max node counts)
- Builder rejection cases (too few, too many, long labels, missing keys)
- End-to-end render through the engine
- Extractor routing for the new graphic type

The parametrized tests in `test_pptx_native_seeds.py` and `test_pptx_native_catalog_consolidation.py` automatically expand to cover your new entry — no extra test code needed for those.

### 11. Run the manual gate

Automated tests verify structural validity but cannot confirm "PowerPoint treats this as editable SmartArt." For that, you must:

1. Build an output .pptx for your new layout using the engine directly:

   ```python
   from src.smartart_pptx_native import engine
   result = engine.render(
       {"graphic_type": "your_new_type", "data": {...}},
       "/tmp",
   )
   print(result.output_path)
   ```

2. Open the output file in PowerPoint for Mac

3. Work through the 7-point checklist in `tests/manual/MANUAL_GATE.md`:
   - Opens with no repair dialog
   - Graphic visible with correct content
   - SmartArt Design ribbon active
   - Text Pane populated
   - Add Shape works
   - Change Layout (in-group) preserves content
   - Change Layout (cross-group) behaviour noted

4. Record pass/fail for each check in `tests/manual/MANUAL_GATE.md`

If any check fails, iterate on the builder or the seed — do NOT merge a layout that hasn't passed the manual gate.

### 12. Legal review (before merge)

Seed files are PowerPoint-authored content. Phase 1 §8 of the research flagged redistribution as plausibly an Office EULA concern distinct from the OOXML format itself. Before merging a new seed into the tracked fixture directory:

1. Add a provenance entry to `tests/fixtures/smartart_seeds/LICENSING.md`
2. Confirm the seed contains only the layout frame + placeholder boxes (no Office.com clip art, no theme imports beyond the default blank, no copyrighted content)
3. Get legal sign-off per `docs/superpowers/specs/2026-04-08-pptx-native-smartart-engine.md` §11.6

---

## Gotchas

### The layout URI is not what the gallery label suggests

Mac PowerPoint's "Basic Cycle" binds to `cycle2`, not `cycle1`. Always extract the URI from the seed's doc point — never assume it from the gallery label.

### Saving as .pptm (macro-enabled) breaks things

Some PowerPoint Mac dialogs default to `.pptm` if your preferences are set to "macro-enabled by default". The engine only supports `.pptx` — a `.pptm` seed will fail the seed sanity tests. Double-check the format dropdown in Save As.

### PowerPoint may flatten the SmartArt on some edits

If you accidentally ungroup the SmartArt, or edit it in ways that don't round-trip cleanly, PowerPoint may save it as a flat `<p:grpSp>` of shapes instead of a real `<p:graphicFrame>` with a diagram reference. The seed sanity test `test_seed_slide_references_diagram_not_flat_group` catches this. If it fires, re-create the seed from scratch.

### Deep or wide trees in hierarchical layouts

OrgChart1 supports 25 nodes and 4 levels of depth per the catalog entry. Beyond that, PowerPoint automatically shrinks boxes to the point of unreadability. If your use case needs bigger trees, consider `custom_svg` instead — the `pptx_native` engine's value prop (editability) is less important when the graphic is already too dense to read.

### The `asst` node type only works in hierarchical layouts

OrgChart1 is the only v1 layout that supports assistant nodes (`"asst": true` on a node dict). Process and cycle layouts don't have the concept — PowerPoint's layout algorithm for `lin` and `cycle` doesn't know how to position sideways branches. Setting `asst: true` on a node in a non-hierarchical layout is a silent bug in your catalog entry; the `node_type_capabilities` field is the source of truth.

---

## Related documentation

- `docs/spikes/2026-04-08-pptx-native-smartart-injection.md` — the four validation spikes that proved the template-injection technique
- `docs/superpowers/specs/2026-04-08-pptx-native-smartart-engine.md` — full design spec
- `docs/pptx-native-smartart-catalog.md` — auto-generated catalog summary
- `tests/fixtures/smartart_seeds/LICENSING.md` — per-seed provenance
- `tests/manual/MANUAL_GATE.md` — manual verification checklist
