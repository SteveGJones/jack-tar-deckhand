# Image Pipeline Gaps Specification

**Date:** 2026-03-29
**Status:** Draft
**Origin:** Observed during first end-to-end deck production run

## Context

During the first full pipeline run (Jack-Tar Deckhand self-demo deck), three image-handling operations had to be performed manually because no skill or module existed to handle them. All three represent gaps in the pipeline's ability to support iterative, surgical deck refinement.

The pipeline was designed for clean full-pipeline runs. These gaps emerge during the draft-to-production lifecycle and QA correction loops, where individual images need replacing, upgrading, or converting without re-running the entire image generation step.

---

## Gap 1: SVG-to-PNG Rasterisation

### Problem

The project has real architecture SVGs at `docs/architecture/diagrams/` (7 diagrams, produced by the `service-architecture-renderer` skill). When a diagram slide's best visual is an existing SVG rather than an AI-generated image, there is no automated path from SVG to a deck-ready PNG.

PptxGenJS cannot embed SVG directly — it requires raster formats (PNG, JPEG). During the pipeline run, we used `rsvg-convert` manually to convert the L1 architecture SVG to a 1705x1536 PNG.

### Current State

- `src/process_image.py` handles resize, crop, placeholder generation, PNG optimisation — zero SVG support
- `src/image_router.py` routes `diagram` visual types to `ollama-diagram` (generative) — no path for "use existing SVG"
- `imagegen-bridge` has no concept of a pre-built asset source

### Proposed Solution

**New function in `src/process_image.py`:**

```python
def rasterize_svg(
    svg_path: str,
    output_path: str,
    width: int = 2048,
    height: int | None = None,
    keep_aspect: bool = True,
) -> dict:
    """Convert SVG to PNG at specified dimensions.

    Returns:
        dict with keys: path, width, height, content_hash
        (matching the shape imagegen-bridge expects)
    """
```

- Primary backend: `cairosvg` (pure Python, pip-installable)
- Fallback: shell out to `rsvg-convert` if installed
- Returns metadata dict compatible with `image-manifest.json` entry shape

**Routing enhancement in `src/image_router.py`:**

Add a `source_file` field to the routing input. When present and pointing to an SVG, the router returns `route: 'rasterize'` instead of a generation provider. The `imagegen-bridge` skill would call `rasterize_svg` + `resize` + `crop_to_aspect` instead of invoking a generation skill.

### Scope

- `src/process_image.py`: add `rasterize_svg()` function
- `src/image_router.py`: add `source_file` routing path
- `imagegen-bridge` SKILL.md: add rasterise branch when source_file is SVG
- Tests: unit tests for rasterisation, routing test for source_file path

### Complexity: Small

---

## Gap 2: Manifest Update After Image Replacement

### Problem

After replacing an image file (swapping draft for production, inserting a converted SVG, or fixing a QA-flagged image), the `image-manifest.json` must be manually updated with new dimensions, content hash, model attribution, and alt text.

During the pipeline run, we had to run `shasum`, `sips`, and hand-edit JSON multiple times.

### Current State

- `src/process_image.py` has `get_dimensions()` and `compute_content_hash()` — the primitives exist
- `imagegen-bridge` builds the manifest from scratch during a full run — no incremental update support
- No utility ties the primitives together into a manifest update operation

### Proposed Solution

**New module: `src/manifest_utils.py`**

```python
def update_manifest_entry(
    deck_dir: str,
    image_id: str,
    new_file_path: str | None = None,
    model_used: str | None = None,
    alt_text: str | None = None,
) -> dict:
    """Update a single entry in image-manifest.json.

    Recomputes dimensions and content_hash from the file on disk.
    Only updates model_used and alt_text if provided.

    Returns:
        The updated manifest entry dict.
    """

def replace_image_in_manifest(
    deck_dir: str,
    slide_number: int,
    new_file_path: str,
    model_used: str,
    alt_text: str | None = None,
) -> dict:
    """Convenience wrapper — finds entry by slide_number instead of image_id."""

def rebuild_manifest_hashes(deck_dir: str) -> dict:
    """Walk all images in the manifest and recompute dimensions + hashes.

    Useful after bulk replacement (e.g., production re-render).

    Returns:
        The full updated manifest dict.
    """
```

All functions read, validate against schema, mutate, and write the manifest atomically.

### Scope

- New file: `src/manifest_utils.py`
- Tests: `tests/test_manifest_utils.py`
- Integration: `imagegen-bridge` and `deck-conductor` can call these during correction loops

### Complexity: Small

---

## Gap 3: Draft-to-Production Image Upgrade

### Problem

The production phase requires upgrading draft Ollama images (1024x576, free) to cloud-rendered images (1536x1024, paid). Currently this requires re-running `/imagegen-bridge` from scratch, which:

- Regenerates ALL images (including charts, placeholders, and already-approved images)
- Does not preserve the prompts that produced the best draft results
- Rebuilds the entire manifest rather than surgically upgrading entries
- Cannot selectively upgrade some images while keeping others

During the pipeline run, we manually called `cloud-generate-image` for each of 6 images, then manually updated the manifest for each.

### Current State

- `deck-conductor.md` says "re-run Steps 5-8 at production quality" — a full re-invocation
- `imagegen-bridge` has no concept of "upgrade mode" or "incremental re-render"
- `image_router.py` has `route_image()` but no `plan_upgrade()` function

### Proposed Solution

**New function in `src/image_router.py`:**

```python
def plan_production_upgrade(
    draft_manifest: dict,
    outline: dict,
    available_providers: dict,
    budget_state: dict,
) -> list[dict]:
    """Plan which images to upgrade from draft to production.

    Returns a list of upgrade decisions:
    [
        {
            "slide_number": 1,
            "image_id": "slide-01-hero_image",
            "action": "upgrade",        # or "keep"
            "reason": "hero_image type benefits from cloud quality",
            "draft_prompt": "...",       # from draft manifest
            "target_provider": "openai",
            "target_model": "gpt-image-1.5",
            "target_size": "1536x1024",
            "estimated_cost_usd": 0.051,
        },
        {
            "slide_number": 4,
            "image_id": "slide-04-diagram",
            "action": "keep",
            "reason": "SVG-converted diagram already at production quality",
        },
    ]
    """
```

Decision logic:
- `hero_image`, `pattern_background`: upgrade to cloud
- `diagram` from SVG source: keep (already high quality)
- `chart` from matplotlib: keep (already production quality)
- `placeholder`: keep (will remain placeholder)
- Budget check: skip upgrade if estimated cost exceeds remaining budget

**Enhancement to `imagegen-bridge` SKILL.md:**

Add `--upgrade-from-draft` flag. When set:
1. Read existing `image-manifest.json`
2. Call `plan_production_upgrade()` for upgrade decisions
3. Only regenerate images marked `action: "upgrade"`
4. Use draft manifest's prompt as the base prompt
5. Use `replace_image_in_manifest()` (Gap 2) to update each entry
6. Preserve entries marked `action: "keep"` unchanged

### Scope

- `src/image_router.py`: add `plan_production_upgrade()` function
- `imagegen-bridge` SKILL.md: add `--upgrade-from-draft` branch
- Depends on Gap 2 (`manifest_utils.py`) being implemented first
- Tests: unit tests for upgrade planning logic, routing test for cost estimation

### Complexity: Medium

---

## Implementation Order

1. **Gap 2 (manifest utils)** — dependency for Gaps 1 and 3
2. **Gap 1 (SVG rasterisation)** — standalone, small
3. **Gap 3 (production upgrade)** — depends on Gap 2, medium

## Dependencies

- Gap 3 depends on Gap 2
- Gap 1 requires `cairosvg` pip dependency (add to requirements.txt)
- No changes to existing tests required — all additive
