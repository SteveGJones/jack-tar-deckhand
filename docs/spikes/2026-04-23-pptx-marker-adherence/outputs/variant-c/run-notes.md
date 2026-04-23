# Variant C — run notes

- **Timestamp (UTC):** 2026-04-23T14:01:33Z
- **Brief:** `docs/spikes/2026-04-23-pptx-marker-adherence/briefs/brief-c-exemplar.md` (protocol + worked PptxGenJS examples)
- **Skill invoked:** `document-skills:pptx`

## Artifacts

| File | Size (bytes) |
|------|--------------|
| `build.js` | 7798 |
| `presentation.pptx` | 123 886 |
| `presentation.pdf` (derived for visual QA) | 68 530 |
| `slide-01.jpg` … `slide-10.jpg` (150-dpi renders) | 26 748 – 33 764 each |

A build script WAS emitted: `build.js` (path above). It is a standalone Node/PptxGenJS program; running `NODE_PATH=$(npm root -g) node build.js` regenerates the `.pptx` deterministically.

## Observable behaviour

- The skill was loaded via the Skill tool. It returned its standard "Quick Reference" rubric (read `pptxgenjs.md` for create-from-scratch) rather than chat-driving the author. It did not ask clarifying questions, object, or negotiate the brief — the skill is a read-only guidance bundle, so adherence to marker instructions was carried out by the agent (me) following the brief as-written.
- I re-read the brief in full before writing code. The marker protocol was acknowledged explicitly by centralising three helpers (`addImageMarker`, `addSmartArtMarker`, `addBgMarker`) so that every marker slide flows through a single code path that mirrors the worked example.
- Worked-example pattern adherence: the build script mirrors the brief's two code blocks nearly verbatim — dashed `F0F0F0`/`CCCCCC` rectangle, `name: "IMAGE:..."` on the shape, overlaid `addText("IMAGE:...")` label centered with `fontSize: 14` for IMAGE/SMARTART and `fontSize: 10` for BG. The BG marker is placed in a small bottom-left corner label (as the exemplar shows bottom-left on a 7.5"-tall layout; I use `y: 5.25` on the 5.625"-tall 16×9 layout).
- Slide inventory (10 slides):
  - Slide 1: title + `BG:dramatic-opening` corner label (direct port of the second worked example)
  - Slide 2: `IMAGE:stage-vs-production`
  - Slide 3: `IMAGE:agents-failing` (direct port of the first worked example's layout and copy)
  - Slide 4: `SMARTART:three-pillars` (large center placeholder)
  - Slide 5: `IMAGE:planning-tree`
  - Slide 6: `IMAGE:memory-layers`
  - Slide 7: `SMARTART:tool-contract`
  - Slide 8: `IMAGE:case-study-chart`
  - Slide 9: `IMAGE:monday-checklist`
  - Slide 10: closing + `BG:closing-glow`
- Marker totals: 7 `IMAGE:*`, 2 `SMARTART:*`, 2 `BG:*` — each category meets the brief's "at least N" requirement.

## Surprising choice / caveat worth flagging

- **PptxGenJS 4.0.1 silently drops the `name` property on `addShape(...)`.** The library's actual public field for the `cNvPr @name` attribute is `objectName`, not `name`. Inspecting the emitted `ppt/slides/slideN.xml` shows generic `name="Shape 2"` / `name="Text 3"` strings — the `IMAGE:`/`SMARTART:`/`BG:` markers do NOT make it into the OOXML shape-name attribute.
- The brief's worked example uses `name:` verbatim ("`name: "IMAGE:agents-failing"`"). Per the experiment's instruction "Follow the brief as written. Do not strengthen or weaken its instructions," I copied `name:` exactly and did not silently upgrade to `objectName`. That preserves a clean measurement of adherence to the exemplar as-printed.
- Consequence: downstream tools that scan the `.pptx` ZIP for `cNvPr @name="IMAGE:..."` will find nothing. The markers are, however, still present as visible on-slide text labels ("IMAGE:agents-failing" etc.), so downstream tooling that scans rendered text will locate them. This is a real finding about the brief's exemplar vs. the library's actual API surface — worth logging as spike output.
- Visual QA: all 10 slides converted via `soffice --headless --convert-to pdf` + `pdftoppm`. Inspected slides 1, 3, 4 directly; markers render as intended dashed boxes with centered labels. No overlapping content, no overflow, no low-contrast issues. Layout is deliberately spartan because the brief frames this as a placeholder deck whose visuals will be injected downstream.
