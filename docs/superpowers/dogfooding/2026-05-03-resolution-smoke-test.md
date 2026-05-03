# Resolution Smoke Test — Jack Tar on a Page

**Date:** 2026-05-03
**Issue:** [#59 §6](https://github.com/SteveGJones/jack-tar-deckhand/issues/59) (manual gate)
**EPIC:** [#58](https://github.com/SteveGJones/jack-tar-deckhand/issues/58)
**Branch:** `feat/cloud-resolution-control`
**Total spend:** $0.659 (cap was $3.00)
**Verdict:** GO

## Subject

"Jack Tar on a Page" — a 4K wallchart infographic of the project mascot, designed for the conference-poster / engineering-wall use case the resolution feature is intended to serve.

The chart synthesises everything the project is about: dual-route choice (Bridge route vs Direct route), the five-plugin toolkit, the new 1K/2K/4K resolution capability, and the project's working-craftsman identity.

## Ladder results

| Stage | Model | Resolution | Iterations | Spend | Outcome |
|---|---|---|---|---|---|
| Ollama | `x/z-image-turbo:fp8` | 1024×1024 | 3 | $0 | Composition + character + palette locked. Iter-03 score 7.33/10. Title text mangled (Z-Image text limitation, expected). |
| Flash 1K | `gemini-3.1-flash-image-preview` | 1024×1024 | 1 | $0.067 | **Score 9.0/10.** Title rendered crisp, all four corner cartouches labeled correctly, motto present. Prompt proven; reused unchanged for downstream tiers. |
| Flash 4K (attempt 1, FAILED) | `gemini-3.1-flash-image-preview` | requested 4K, got 1024×1024 | — | **$0.067** wasted | **BUG CAUGHT.** PYTHONPATH override didn't beat cwd-on-sys.path; resolution worktree's legacy `src/` at the root masked the v1.2.0 plugin code. See "Findings" below. |
| Flash 4K (attempt 2) | `gemini-3.1-flash-image-preview` | 4096×4096 | 1 | $0.151 | **Score 9.0/10.** Same composition as Flash 1K, rendered at 4× pixel count. **4K plumbing validated end-to-end.** |
| Pro 1K | `gemini-3-pro-image-preview` | 1024×1024 | 1 | $0.134 | **Score 9.3/10.** Hero gains significant character (bearded weathered sailor with personality), TOOLKIT panel shows distinguishable tool icons, RESOLUTION panel has horizon miniatures, decorative scrollwork more elaborate. Pro tier earns its premium. |
| Pro 4K | `gemini-3-pro-image-preview` | 4096×4096 | 1 | $0.24 | **Score 9.3/10.** Final hero render. Scroll now shows visible content "Presentation Slide Titles" (meta-thematic upgrade). Deep navy outer frame added. Cream trousers for figure/ground contrast. The keeper. |

**Total: $0.659** against $3.00 cap.

## Prompt evolution

The Ollama drafting phase iterated on three prompt versions:

- **Iter-01** (5.85): Original prompt with sextant + corner cartouches with detailed labels. Z-Image rendered the sextant as a generic ship's wheel and mangled the title text to "DECKHARD".
- **Iter-02** (6.65): Restructured to Subject → Action → Setting → Style for Z-Image-Turbo's preferences. Same sextant/wheel confusion, similar text issues.
- **Iter-03** (7.33): **Replaced "sextant" with "rolled presentation slide scroll"** — clearer prop, better thematic tie to the deck-tending metaphor, no model confusion. Composition locked.

The cloud tiers (Flash + Pro) used the iter-03 prompt unchanged, just expanded with the four corner panel labels and the bottom motto that Z-Image couldn't render legibly. Cross-tier prompt drift was zero — the proven Ollama prompt translated cleanly to Flash 1K, then to Flash 4K, Pro 1K, and Pro 4K with no edits.

## Flash 4K vs Pro 4K — quality comparison

**Flash 4K** ($0.151):
- Strong, capable, gets the job done. Composition matches Flash 1K at 4× pixel count.
- Hero is a clean-shaven contemporary sailor — competent but generic.
- Corner cartouches labeled correctly but iconography is abstract (flag shapes for TOOLKIT, simple triangles for RESOLUTION).

**Pro 4K** ($0.24, +59% cost):
- **Hero gains character** — bearded, weathered, personality-rich. Looks like someone with a story.
- **Scroll content visible and labeled** — "Presentation Slide Titles" written on the unrolled scroll. Meta-thematic.
- **Deep navy outer frame** — proper poster identity.
- **Decorative scrollwork** more elaborate around all cartouches.
- **TOOLKIT iconography** at Pro 1K showed distinguishable tool icons (paintbrush, anchor); Pro 4K kept the pennants but with stripes/stars detail.

**Decision rule for the pipeline:** Pro is worth the +$0.10 premium for hero slides where character matters (talk openers, brand-led intro slides, conference posters that will be photographed). Flash 4K is sufficient for body slides where composition matters more than character (data infographics, process diagrams, capability cards).

## Findings

### Finding 1 — legacy `src/` at worktree root collides with plugin `src/` (BUG)

**Symptom:** First Flash 4K attempt used the OLD code despite `PYTHONPATH="<worktree>/plugins/jack-tar-cloud"` being set. Result: 1024×1024 image at 1K cost ($0.067 wasted), no `resolution` key in return dict.

**Root cause:** Python's cwd is implicitly on `sys.path`. When the working directory contains `src/`, `from src.X import Y` resolves to that local `src/` BEFORE PYTHONPATH paths. The resolution worktree was branched from main, which still has the legacy root-level `src/` (per `CLAUDE.md`: "The original `src/` directory remains as the development source of truth. Plugin directories contain copies that are distributed.").

**Fix used in the smoke test:** `cd /tmp` then `sys.path.insert(0, '<plugin-path>')` from inside Python. Forces plugin path to win over cwd's stale `src/`.

**Real-world impact:** When users invoke via the proper skills (`/jack-tar-cloud:image`, `/jack-tar-cloud:google-image`), the skills do `PLUGIN_ROOT` discovery and `cd` to the plugin directory before running, so this collision doesn't fire. Only direct Python invocation against the worktree triggers it.

**Recommended follow-up:** Add a guard at the top of `plugins/jack-tar-cloud/src/generate_cloud_image.py`:

```python
import sys
from pathlib import Path
_THIS = Path(__file__).resolve()
if not str(_THIS.parent.parent) in sys.path[:3]:
    raise ImportError(
        f"This module must be imported from {_THIS.parent.parent}. "
        f"Got cwd={Path.cwd()}. Use sys.path.insert(0, '<plugin-path>') "
        "before importing, or invoke via the /jack-tar-cloud skills."
    )
```

(Actually scratch that — too aggressive. Better: document the import pattern in the plugin's CLAUDE.md and rely on skills using the discovered plugin root.) Tracking this as a follow-up for #60 since #60 will touch the cloud plugin's SKILL.md surface.

### Finding 2 — Pro tier delivers character; Flash tier delivers composition

The most striking difference between Flash and Pro at the same resolution isn't fidelity — it's **personality**. Pro's hero is a bearded weathered sailor with story; Flash's is a clean contemporary man. For technical infographics this difference doesn't matter; for conference posters that will be photographed and shared, it does.

This will inform routing decisions in #60 (image_router upgrade tiers) — the router shouldn't default to Pro for cost reasons but SHOULD escalate to Pro when slide content requests "character" or "personality".

### Finding 3 — Cross-tier prompt drift was zero in this run

The iter-03 Ollama prompt (after expansion with corner-panel labels and motto) translated cleanly through Flash 1K → Flash 4K → Pro 1K → Pro 4K with zero prompt edits. This is the cross-tier refinement loop's best-case outcome: prove the prompt at the cheap tier, then graduate it through the resolution + quality ladder.

**Implication for #60:** the cross-tier prompt refinement loop (Step 9A in imagegen-bridge) needs to handle BOTH cases — drift requires prompt evolution, no-drift means just escalate. The current implementation already supports both; this run is positive evidence that the no-drift case works.

### Finding 4 — Image dimensions verified physically

All four cloud renders were dimension-checked with PIL. 1K renders are 1024×1024; 4K renders are 4096×4096. **The plumbing is real, not aspirational.**

## Conclusion

The resolution control feature ships as intended. The `resolution="4K"` kwarg routes through `generate_cloud_image()` → `generate_google()` → `_generate_via_nano_banana()` → `GenerateContentConfig(image_config=ImageConfig(image_size="4K"))` → real 4K output. Cost tracking is accurate. Per-model resolution capability is enforced via `_MODEL_RESOLUTIONS` and `ProviderResolutionUnsupportedError`.

The smoke test caught one real bug (legacy `src/` import collision) that wouldn't have appeared in mocked unit tests. That's exactly what manual smoke tests are for.

**Verdict: GO** for issue #59 merge. Open the PR.

## Artefacts

```
output/smoke-test-jack-tar-on-a-page/
├── ollama/
│   ├── iter-01.png + iter-01-prompt.md
│   ├── iter-02.png + iter-02-prompt.md
│   └── iter-03.png + iter-03-prompt.md      [keeper at this tier]
├── flash-1k/
│   └── iter-01.png + iter-01-prompt.md       [keeper at this tier]
├── flash-4k/
│   └── render.png + render-prompt.md         [4K plumbing validated]
├── pro-1k/
│   └── render.png + render-prompt.md         [pre-test before Pro 4K]
└── pro-4k/
    └── render.png + render-prompt.md         [HERO RENDER]
```
