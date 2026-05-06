# Dogfood Pipeline Fixes

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix four bugs found during dogfood deck build: strategy map never assigns "smartart", picture builder ignores "text" key, picture fill mode wrong default, flat_list builder rejects dict items.

**Architecture:** Four independent fixes to the pptx_native SmartArt pipeline. Each is a single-function change with targeted tests. No schema changes, no assembler changes — all fixes are in the strategy classifier and SmartArt builders.

**Tech Stack:** Python 3.10+, pytest, existing test fixtures in `tests/`.

---

## Task 1: Strategy map assigns "smartart" for diagram slides

The assembler routes to `buildSmartArtSlide` only when `strategy === "smartart"` (line 201 of `src/assembler/build_deck.js`), but `classify_slide_strategy()` in `src/slide_prompt_composer.py` never returns `"smartart"`. Diagram slides get classified as `"composed"`, so the assembler falls through to `buildDiagramSlide` instead of `buildSmartArtSlide`, meaning pptx_native placeholders are never emitted and injection fails.

**Files:**
- Modify: `src/slide_prompt_composer.py:32-75` (`classify_slide_strategy()`)
- Test: `tests/test_slide_prompt_composer.py`

- [ ] **Step 1: Write the failing test**

```python
# In tests/test_slide_prompt_composer.py

def test_classify_diagram_slide_as_smartart():
    """Diagram slides should get 'smartart' strategy so the assembler
    routes them to buildSmartArtSlide and emits pptx_native placeholders."""
    from src.slide_prompt_composer import classify_slide_strategy

    slide = {
        "slide_number": 5,
        "slide_type": "diagram",
        "headline": "The Pipeline",
        "body_points": ["Step A", "Step B", "Step C"],
    }
    result = classify_slide_strategy(slide)
    assert result == "smartart", (
        f"diagram slides must be classified as 'smartart', got '{result}'"
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_slide_prompt_composer.py::test_classify_diagram_slide_as_smartart -v`
Expected: FAIL — `AssertionError: diagram slides must be classified as 'smartart', got 'composed'`

- [ ] **Step 3: Add "diagram" to the smartart classification in `classify_slide_strategy()`**

In `src/slide_prompt_composer.py`, find the `classify_slide_strategy()` function (line 32). Add a check for `slide_type == "diagram"` that returns `"smartart"` before the existing composed-types check.

The exact edit: after the full_render check and before the composed-types check, add:

```python
    # Diagram slides use SmartArt — the assembler routes "smartart" strategy
    # to buildSmartArtSlide which emits pptx_native placeholders for injection.
    # If no SmartArt manifest entry exists at assembly time, the assembler
    # falls back to buildContentSlide gracefully.
    if slide_type == "diagram":
        return "smartart"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_slide_prompt_composer.py::test_classify_diagram_slide_as_smartart -v`
Expected: PASS

- [ ] **Step 5: Run full slide_prompt_composer test suite to check for regressions**

Run: `.venv/bin/pytest tests/test_slide_prompt_composer.py -v`
Expected: all existing tests PASS (no diagram slides in existing fixtures should have changed behaviour since "diagram" was previously falling through to "composed" via `_COMPOSED_TYPES`)

- [ ] **Step 6: Commit**

```bash
git add src/slide_prompt_composer.py tests/test_slide_prompt_composer.py
git commit -m "fix: classify diagram slides as 'smartart' strategy

Dogfood finding: the assembler only routes to buildSmartArtSlide when
strategy is 'smartart', but classify_slide_strategy() never returned it.
Diagram slides fell through to 'composed', so pptx_native placeholders
were never emitted and SmartArt injection failed."
```

---

## Task 2: Picture builder accepts "text" as alias for "label"

`_extract_items()` in `src/smartart_pptx_native/builders/picture.py` reads `item.get("label", "")` for dict items (line 96). If items use `"text"` as the key (which is the natural key used by the outline schema and manual specs), the label silently defaults to empty string. The fix: check both `"label"` and `"text"`.

**Files:**
- Modify: `src/smartart_pptx_native/builders/picture.py:96`
- Test: `tests/test_smartart_pptx_native/test_picture_builder.py` (or nearest existing test file)

- [ ] **Step 1: Find the existing test file**

Run: `.venv/bin/pytest --collect-only tests/ -q 2>/dev/null | grep picture`

- [ ] **Step 2: Write the failing test**

```python
# In the picture builder test file

def test_picture_builder_accepts_text_key():
    """Items with 'text' key should work the same as 'label' key."""
    from src.smartart_pptx_native.builders.picture import _extract_items

    catalog_entry = {
        "id": "vList3",
        "min_nodes": 2,
        "max_nodes": 8,
        "max_label_chars": 30,
    }
    extracted = {
        "items": [
            {"text": "Alpha", "image_path": "/tmp/fake.png"},
            {"text": "Beta", "image_path": "/tmp/fake2.png"},
        ]
    }
    items, has_images = _extract_items(extracted, catalog_entry)
    assert items[0]["label"] == "Alpha"
    assert items[1]["label"] == "Beta"
    assert has_images is True
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/pytest <test_file>::test_picture_builder_accepts_text_key -v`
Expected: FAIL — `AssertionError: assert '' == 'Alpha'` (empty label because "text" key is ignored)

- [ ] **Step 4: Fix `_extract_items()` to check "text" as fallback**

In `src/smartart_pptx_native/builders/picture.py`, line 96, change:

```python
            label = item.get("label", "")
```

to:

```python
            label = item.get("label") or item.get("text", "")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/pytest <test_file>::test_picture_builder_accepts_text_key -v`
Expected: PASS

- [ ] **Step 6: Run full picture builder test suite**

Run: `.venv/bin/pytest <test_file> -v`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add src/smartart_pptx_native/builders/picture.py <test_file>
git commit -m "fix: picture builder accepts 'text' as alias for 'label'

Dogfood finding: outline schema and manual specs use 'text' key but
the picture builder only checked 'label', causing silent empty labels."
```

---

## Task 3: Picture builder defaults to "fill" mode

The default `image_fill_mode` in `src/smartart_pptx_native/builders/picture.py` line 217 is `"fit"`, which renders square images as narrow vertical slivers inside circular pictRect placeholders. For picture SmartArt layouts (vList3, etc.), `"fill"` is the correct default — it crops the image to fill the placeholder shape, which is what PowerPoint's built-in picture SmartArt does.

**Files:**
- Modify: `src/smartart_pptx_native/builders/picture.py:217`
- Test: same test file as Task 2

- [ ] **Step 1: Write the failing test**

```python
def test_picture_builder_defaults_to_fill_mode():
    """Picture items without explicit fill mode should default to 'fill',
    not 'fit', so images fill circular placeholders correctly."""
    from src.smartart_pptx_native.builders.picture import _extract_items

    catalog_entry = {
        "id": "vList3",
        "min_nodes": 2,
        "max_nodes": 8,
        "max_label_chars": 30,
    }
    extracted = {
        "items": [
            {"label": "Alpha", "image_path": "/tmp/fake.png"},
            {"label": "Beta", "image_path": "/tmp/fake2.png"},
        ]
    }
    items, has_images = _extract_items(extracted, catalog_entry)
    # Items should preserve fill mode for the builder to use
    assert items[0].get("image_fill_mode", "fill") == "fill"
```

- [ ] **Step 2: Run test — may pass if we're testing the downstream usage**

The default is applied in `build()` at line 217, not in `_extract_items()`. The test needs to verify the actual data model XML output. Better test:

```python
def test_picture_builder_fill_mode_default_in_xml():
    """Generated data model XML should use 'fill' mode by default,
    producing srcRect-based cropping, not 'fit' letterboxing."""
    import re
    from src.smartart_pptx_native.builders import picture
    from pathlib import Path

    catalog_entry = {
        "id": "vList3",
        "layout_uri": "urn:microsoft.com/office/officeart/2005/8/layout/vList3",
        "qs_type_id": "urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1",
        "cs_type_id": "urn:microsoft.com/office/officeart/2005/8/colors/accent1_2",
        "min_nodes": 2,
        "max_nodes": 8,
        "max_label_chars": 30,
        "data_shape": "picture",
    }
    # Create a tiny valid PNG for the test
    import struct, zlib
    def make_1x1_png():
        sig = b'\x89PNG\r\n\x1a\n'
        ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
        ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
        ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
        raw = zlib.compress(b'\x00\x00\x00\x00')
        idat_crc = zlib.crc32(b'IDAT' + raw) & 0xffffffff
        idat = struct.pack('>I', len(raw)) + b'IDAT' + raw + struct.pack('>I', idat_crc)
        iend_crc = zlib.crc32(b'IEND') & 0xffffffff
        iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
        return sig + ihdr + idat + iend

    import tempfile
    tmp = Path(tempfile.mkdtemp())
    png = tmp / "test.png"
    png.write_bytes(make_1x1_png())

    extracted = {
        "items": [
            {"label": "A", "image_path": str(png)},
            {"label": "B", "image_path": str(png)},
        ]
    }
    result = picture.build(extracted, catalog_entry)
    assert isinstance(result, tuple), "picture build should return (bytes, refs) tuple"
    data_xml, refs = result
    xml_str = data_xml.decode("utf-8")

    # "fill" mode produces <a:srcRect> inside <a:stretch>
    # "fit" mode produces bare <a:stretch><a:fillRect/></a:stretch>
    assert "srcRect" in xml_str or "stretch" in xml_str, "should have fill/stretch directive"
    # Should NOT have the "fit" pattern (fillRect without srcRect)
    # Actually just check that the blipFill uses the dpi="0" pattern from fill mode
    assert 'dpi="0"' in xml_str, "fill mode uses dpi=0 in blipFill"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/pytest <test_file>::test_picture_builder_fill_mode_default_in_xml -v`
Expected: FAIL — the default is "fit" so the XML won't have `dpi="0"`

- [ ] **Step 4: Change the default fill mode from "fit" to "fill"**

In `src/smartart_pptx_native/builders/picture.py`, line 217, change:

```python
            fill_mode = item.get("image_fill_mode", "fit")
```

to:

```python
            fill_mode = item.get("image_fill_mode", "fill")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/pytest <test_file>::test_picture_builder_fill_mode_default_in_xml -v`
Expected: PASS

- [ ] **Step 6: Run full picture builder tests + SmartArt engine tests**

Run: `.venv/bin/pytest tests/ -k "picture" -v`
Expected: all PASS. Any existing tests that explicitly tested "fit" as default will need updating to expect "fill".

- [ ] **Step 7: Commit**

```bash
git add src/smartart_pptx_native/builders/picture.py <test_file>
git commit -m "fix: picture builder defaults to 'fill' mode, not 'fit'

Dogfood finding: 'fit' mode renders square images as narrow slivers
inside circular pictRect placeholders. 'fill' crops to fill the shape,
matching PowerPoint's native picture SmartArt behaviour."
```

---

## Task 4: Flat list builder accepts dict items gracefully

`_extract_items()` in `src/smartart_pptx_native/builders/flat_list.py` (line 60) requires all items to be plain strings. If an item is a dict (e.g. `{"text": "Step A"}` from a manual spec or from the outline's body_points), it raises `FlatListBuildError`. The fix: extract the string from dict items using "text" or "label" keys, matching the picture builder's pattern.

**Files:**
- Modify: `src/smartart_pptx_native/builders/flat_list.py:55-70` (`_extract_items()`)
- Test: `tests/test_smartart_pptx_native/test_flat_list_builder.py` (or nearest existing test file)

- [ ] **Step 1: Find the existing test file**

Run: `.venv/bin/pytest --collect-only tests/ -q 2>/dev/null | grep flat_list`

- [ ] **Step 2: Write the failing test**

```python
def test_flat_list_accepts_dict_items_with_text_key():
    """Dict items like {"text": "Step A"} should be accepted and
    the text extracted, not rejected with FlatListBuildError."""
    from src.smartart_pptx_native.builders.flat_list import _extract_items

    catalog_entry = {
        "id": "process1",
        "min_nodes": 2,
        "max_nodes": 9,
        "max_label_chars": 24,
    }
    extracted = {
        "items": [
            {"text": "Plan"},
            {"text": "Build"},
            {"text": "Ship"},
        ]
    }
    items = _extract_items(extracted, catalog_entry)
    assert items == ["Plan", "Build", "Ship"]


def test_flat_list_accepts_dict_items_with_label_key():
    """Dict items with 'label' key should also work."""
    from src.smartart_pptx_native.builders.flat_list import _extract_items

    catalog_entry = {
        "id": "process1",
        "min_nodes": 2,
        "max_nodes": 9,
        "max_label_chars": 24,
    }
    extracted = {
        "items": [
            {"label": "Alpha"},
            {"label": "Beta"},
        ]
    }
    items = _extract_items(extracted, catalog_entry)
    assert items == ["Alpha", "Beta"]


def test_flat_list_accepts_mixed_string_and_dict_items():
    """Mixed strings and dicts should both be accepted."""
    from src.smartart_pptx_native.builders.flat_list import _extract_items

    catalog_entry = {
        "id": "process1",
        "min_nodes": 2,
        "max_nodes": 9,
        "max_label_chars": 24,
    }
    extracted = {
        "items": [
            "Plain string",
            {"text": "Dict item"},
            {"label": "Label item"},
        ]
    }
    items = _extract_items(extracted, catalog_entry)
    assert items == ["Plain string", "Dict item", "Label item"]
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv/bin/pytest <test_file>::test_flat_list_accepts_dict_items_with_text_key -v`
Expected: FAIL — `FlatListBuildError: flat_list items must be strings; found ['dict']`

- [ ] **Step 4: Update `_extract_items()` to handle dict items**

In `src/smartart_pptx_native/builders/flat_list.py`, find the item validation loop (around line 55-65). Replace the strict string-only check with one that extracts text from dicts:

Find the block that iterates over raw items and validates they're strings. Replace with:

```python
    items = []
    for item in raw:
        if isinstance(item, str):
            items.append(item.strip())
        elif isinstance(item, dict):
            label = item.get("text") or item.get("label") or ""
            if not isinstance(label, str):
                raise FlatListBuildError(
                    f"flat_list dict item 'text'/'label' must be a string, "
                    f"got {type(label).__name__}"
                )
            items.append(label.strip())
        else:
            raise FlatListBuildError(
                f"flat_list items must be strings or dicts with 'text'/'label' key; "
                f"found {type(item).__name__!r}"
            )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest <test_file> -k "dict_items" -v`
Expected: all 3 new tests PASS

- [ ] **Step 6: Run full flat_list builder + SmartArt test suite**

Run: `.venv/bin/pytest tests/ -k "flat_list" -v`
Expected: all PASS — existing string-only tests unchanged

- [ ] **Step 7: Commit**

```bash
git add src/smartart_pptx_native/builders/flat_list.py <test_file>
git commit -m "fix: flat_list builder accepts dict items with text/label keys

Dogfood finding: manual specs and outline body_points use dict format
like {\"text\": \"Step A\"} but the flat_list builder required plain
strings. Now extracts the text gracefully from either key."
```

---

## Self-Review

**Spec coverage:** All four dogfood bugs have a task:
- Strategy map "smartart" → Task 1
- Picture builder "text" key → Task 2
- Picture builder fill mode → Task 3
- Flat list builder dict items → Task 4

**Placeholder scan:** No TBD/TODO. Each step shows exact code. Test file paths need discovery (Step 1 in Tasks 2-4) since test organization may vary.

**Type consistency:** `_extract_items()` signature matches across Tasks 2-4. `classify_slide_strategy()` return value matches assembler expectation of `"smartart"` string. `"fill"` mode string matches `data_model.py` line 166 branch.

**Independence:** All four tasks are independent — can be implemented in any order. No cross-task dependencies.
