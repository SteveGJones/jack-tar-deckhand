# pptx_native Manual Gate Checklist

The automated test suite validates everything we can check without opening PowerPoint. But the one thing that matters most — **"PowerPoint treats this as editable SmartArt"** — requires a human to open the file in PowerPoint Mac and verify.

Every new or modified `pptx_native` layout must pass this checklist before merging.

---

## How to run the gate

### 1. Generate a test output for the layout

```bash
.venv/bin/python -c "
from src.smartart_pptx_native import engine
from src.smartart_pptx_native.layouts import catalog

# Use the layout's committed example_input from the catalog
entry = catalog.get_entry('<layout_id>')
graphic_type = entry['integration']['smartart_type_mappings'][0]

result = engine.render(
    {'graphic_type': graphic_type, 'data': entry['example_input']},
    '/tmp/manual_gate',
)
print(f'open {result.output_path}')
"
```

Replace `<layout_id>` with `process1`, `cycle2`, `orgChart1`, etc.

### 2. Open the output in PowerPoint for Mac

```bash
open /tmp/manual_gate/pptx_native_<layout_id>.pptx
```

### 3. Work through the 7-point checklist below

Record pass/fail for each check. Any failure means the layout needs work before merging.

### 4. Log the result

Append a block to the "Gate log" section at the bottom of this file with:
- Date
- Layout id
- Pass/fail for each check
- Any notes on edge cases found

---

## The 7-point checklist

### Check 1 — Opens without repair

- [ ] PowerPoint opens the file with **no** "PowerPoint found a problem with content" dialog
- [ ] The file loads in a reasonable time (<2 seconds on modern hardware)

**If this fails:** The OOXML is malformed or PowerPoint can't parse the data model. Check `xmllint --noout` on `ppt/diagrams/data1.xml` from the output, and compare against the spike 4 working output.

### Check 2 — Graphic visible with correct content

- [ ] The SmartArt graphic appears on slide 1
- [ ] Every label from the catalog's `example_input` is visible
- [ ] Labels are not cut off, overlapping, or rendered at unreadable sizes
- [ ] The visual matches the catalog's `visual_character` description

**If this fails:** PowerPoint rendered the graphic but the data model's text bindings didn't reach the shapes. Check the `<a:t>` elements inside `<dgm:pt>` points in `data1.xml`.

### Check 3 — SmartArt Design ribbon appears

- [ ] Click the graphic
- [ ] A **SmartArt Design** tab appears in the ribbon
- [ ] Clicking elsewhere on the slide makes the tab disappear; re-clicking the graphic brings it back

**If this fails:** PowerPoint has detected the graphic as an editable SmartArt but something about the slide XML isn't triggering the ribbon. Usually a `<p:graphicFrame>` wrapper issue — verify the slide's `<a:graphicData uri="...diagram">` element is correctly formed.

### Check 4 — Text Pane is populated and editable

- [ ] SmartArt Design → **Text Pane** (or click the small arrow on the graphic's left edge)
- [ ] The Text Pane opens and shows an editable outline of every node in the graphic
- [ ] Changing a label in the Text Pane updates the corresponding box in the graphic
- [ ] For hierarchical layouts, the indentation in the Text Pane reflects the tree structure

**If this fails:** The presentation tree didn't regenerate correctly from `layout1.xml`. This usually means the data model is missing required structural elements — compare against a seed's data1.xml.

### Check 5 — Add Shape works

- [ ] Right-click any existing node → **Add Shape**
- [ ] Choose an insertion position (After, Before, Above, Below, or Assistant where applicable)
- [ ] A new empty node appears at the chosen position
- [ ] Type some text in the new node — it persists
- [ ] For **orgChart1 only:** `Add Shape → Add Assistant` produces a sideways-branching assistant node, NOT a regular subordinate

**If this fails:** The data model lacks the structural bookkeeping PowerPoint needs to add new nodes. Compare against the spike 4 output's data1.xml.

### Check 6 — Change Layout (in-group)

- [ ] Click the graphic → SmartArt Design → **Layouts** (gallery dropdown)
- [ ] Pick a different layout within the **same category**. Examples:
  - For `process1`, try "Step Up Process" or "Continuous Block Process"
  - For `cycle2`, try "Text Cycle" or "Block Cycle"
  - For `orgChart1`, try "Hierarchy" or "Labeled Hierarchy"
- [ ] The graphic re-renders with the new layout, **preserving the text content**
- [ ] Click the original layout to switch back — content still preserved

**If this fails:** PowerPoint can't convert the data model to the new layout's shape. Not necessarily a bug in our code — some layouts have incompatible data shape requirements. Just note which in-group layouts work and which don't.

### Check 7 — Change Layout (cross-group) — informational

- [ ] Click the graphic → SmartArt Design → Layouts
- [ ] Pick a layout from a **different category** (e.g., for `process1`, pick Hierarchy → Organization Chart)
- [ ] Observe what PowerPoint does:
  - **Accepts and converts:** PowerPoint maps the data to the new layout as best it can (may flatten hierarchy, may lose information)
  - **Refuses:** PowerPoint shows a dialog explaining the data shape is incompatible
  - **Partially converts:** Some content transfers, some is lost

This check is **informational only** — it doesn't pass/fail the gate. We want to know what PowerPoint does so we can document the speaker's experience when they try to switch between flat-list and hierarchical layouts after delivery.

---

## Gate log

Record results chronologically, most recent first. Each layout gets one entry per manual-gate run.

### 2026-04-08 — process1 (via spike 1)

- Check 1 (opens): ✅ PASS
- Check 2 (graphic): ✅ PASS — all 5 steps visible
- Check 3 (ribbon): ✅ PASS
- Check 4 (text pane): ✅ PASS
- Check 5 (add shape): ✅ PASS
- Check 6 (in-group layout change): ✅ PASS
- Check 7 (cross-group): Not tested in spike (informational only)
- **Result:** ✅ passed
- **Recorded by:** User confirmation during spike 1 iteration
- **Notes:** First proven case. Established the technique.

### 2026-04-08 — cycle2 (via spike 2)

- Check 1: ✅ PASS
- Check 2: ✅ PASS — all 6 phases visible in a ring
- Check 3: ✅ PASS
- Check 4: ✅ PASS
- Check 5: ✅ PASS
- Check 6: ✅ PASS
- Check 7: Not tested
- **Result:** ✅ passed
- **Recorded by:** User confirmation during spike 2 iteration
- **Notes:** Confirmed the technique generalises across algorithm families (lin → cycle). Catalog entry binds to `cycle2` not `cycle1`.

### 2026-04-08 — orgChart1 (via spike 4)

- Check 1: ✅ PASS
- Check 2: ✅ PASS — 8 nodes visible in correct tree shape
- Check 3: ✅ PASS
- Check 4: ✅ PASS — hierarchy shown correctly in Text Pane
- Check 5: ✅ PASS — both "Add Subordinate" and "Add Assistant" work natively; the two committed assistants (Executive Assistant, Tech Ops Assistant) render sideways with PowerPoint's distinctive right-angle connector
- Check 6: ✅ PASS
- Check 7: Not tested
- **Result:** ✅ passed
- **Recorded by:** User confirmation during spike 4 iteration
- **Notes:** Validated hierarchical data shape + assistant encoding (`type="asst"` on destination point). First catch for spike 4: original version omitted assistants; reviewer pushback led to extending the spike with the `is_asst` parameter. Both cases now proven.

### _(next layout's run goes here)_

---

## Notes for future layout authors

- The spike-level test runs documented above are one-off validations done during spike authoring. When adding a new layout via the Phase 7 seed-authoring workflow, run a fresh manual gate against that layout's specific example_input and log the result here. The historical spike entries don't count as "this layout was tested today" — every v1 release should include fresh gate runs for every layout.
- If you find a cross-group layout switch that works especially well (or especially badly), document it in your gate entry. Over time this builds empirical knowledge of which PowerPoint layout transitions are safe to recommend to speakers.
- If a check fails in a way that's a fundamental capability limit (not a bug), escalate to the spec — the layout may need to be removed from v1 scope.
