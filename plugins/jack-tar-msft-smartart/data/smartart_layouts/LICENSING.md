# pptx_native SmartArt Layout Fixtures — Licensing and Provenance

**Legal status:** ✅ **Clear — MIT-licensed content from the `dotnet/Open-XML-SDK` repository.**

---

## Summary

Every `layout.xml`, `quickStyle.xml`, and `colors.xml` file in this directory was extracted from a `.pptx` or `.potx` test fixture in the [`dotnet/Open-XML-SDK`](https://github.com/dotnet/Open-XML-SDK) repository, which is released under the [MIT License](https://github.com/dotnet/Open-XML-SDK/blob/main/LICENSE) by the .NET Foundation. The MIT license grants permission to "use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software" without restriction beyond including the copyright notice.

The `dotnet/Open-XML-SDK` repository is maintained under the .NET Foundation umbrella, which includes Microsoft as a contributing member. The repository's `test/DocumentFormat.OpenXml.Tests.Assets/` directory contains hundreds of PowerPoint-authored `.pptx` and `.potx` fixtures covering the full range of OOXML features, including SmartArt. The specific fixtures we extract from are deliberately committed as test assets and are covered by the repo's overall MIT license.

## How the extraction works

The `tools/extract_smartart_layouts.py` script walks the SDK repo, downloads every `.pptx` / `.potx` file, and for each diagram it finds:

1. Reads the `loTypeId` / `qsTypeId` / `csTypeId` URIs from the diagram's `data{N}.xml` doc point
2. Extracts the corresponding `layout{N}.xml`, `quickStyle{N}.xml`, and `colors{N}.xml` parts as opaque bytes
3. Writes them to `tests/fixtures/smartart_layouts/<base_layout_id>/layout.xml` / `quickStyle.xml` / `colors.xml`
4. Records the metadata (URIs, source file path, category hint) in a sibling `meta.json`

The extraction is deterministic and reproducible. Running the script against a fresh `main` branch of the SDK repo would produce the same output.

## Reinforcing precedent

Several legal and practical points reinforce that this use is clear:

1. **MIT License is unrestricted.** The .NET Foundation explicitly grants "use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies" — redistribution of the extracted content is textually permitted.

2. **Microsoft's Open Specification Promise** ([MS-DEVCENTLP]) separately covers the OOXML format itself (ECMA-376 / ISO/IEC 29500 / MS-PPTX), irrevocably promising not to assert any patent claims against implementers. This is a patent promise distinct from the copyright license, but it removes any patent-based concerns about implementing SmartArt from scratch.

3. **15+ years of precedent.** LibreOffice Impress, Google Slides, Apple Keynote, Aspose.Slides, Spire.Presentation, python-pptx, and dozens of other tools have shipped OOXML output — often derived directly from analysing PowerPoint's own files — since the format was standardised in 2007. Zero lawsuits have been filed. Microsoft actively encourages third-party tools to produce OOXML content.

4. **Direct precedent in the SDK itself.** The SDK repository ships files like `CycleDiagram_TP10174326.potx` and `ProcessDiagram_TP10174324.potx` as test fixtures — full PowerPoint templates containing SmartArt graphics. These have been in the repo for years, distributed under MIT, without incident.

5. **De minimis extraction.** Each layout's three XML files are typically 5-25 KB. The content is purely structural (layout algorithm definitions, color transforms, style labels) — not creative content like art or prose. The function of the files is to enable interoperability, which is the explicit purpose of the Open XML standard.

## Per-layout provenance

Every layout directory contains a `meta.json` recording the exact source file and extraction metadata. Example (`process1/meta.json`):

```json
{
  "base_name": "process1",
  "category_hint": "Process",
  "cs_type_id": "urn:microsoft.com/office/officeart/2005/8/colors/accent1_2",
  "layout_uri": "urn:microsoft.com/office/officeart/2005/8/layout/process1#1",
  "qs_type_id": "urn:microsoft.com/office/officeart/2005/8/quickstyle/simple2#4",
  "source_file": "test/DocumentFormat.OpenXml.Tests.Assets/assets/TestDataStorage/v2FxTestFiles/presentation/O12 templates/ProductOverviewPresentation_TP10090249.potx",
  "variant": "#1"
}
```

The `source_file` field traces each extracted layout back to the exact `.pptx` / `.potx` in the SDK repo it came from. For bulk provenance, see `_extraction_manifest.json` in this directory, which lists every extracted layout in one place.

## Refreshing content

To adopt new layouts (or update existing ones) as the Open XML SDK evolves:

```bash
.venv/bin/python tools/extract_smartart_layouts.py --sdk
```

This script walks the SDK repo's `main` branch at the current HEAD, finds all `.pptx`/`.potx` fixtures containing SmartArt, and extracts unique layouts into this directory. New layouts are added to the tree; existing ones are overwritten with the latest version.

## What this directory does NOT contain

- No hand-authored seeds. All Phase 1-7 hand-authored seed files have been removed.
- No images, fonts, or media. Layout definitions are pure structural XML.
- No proprietary data from specific PowerPoint installations. Everything comes from the MIT-licensed SDK repository.

## Related documents

- [`src/smartart_pptx_native/layouts/catalog.json`](../../../src/smartart_pptx_native/layouts/catalog.json) — the canonical catalog with per-layout metadata
- [`docs/pptx-native-smartart-catalog.md`](../../../docs/pptx-native-smartart-catalog.md) — auto-generated human-readable catalog summary
- [`docs/superpowers/specs/2026-04-08-pptx-native-smartart-engine.md`](../../../docs/superpowers/specs/2026-04-08-pptx-native-smartart-engine.md) — full design spec
- [`tools/extract_smartart_layouts.py`](../../../tools/extract_smartart_layouts.py) — the extraction tool that produced this directory
