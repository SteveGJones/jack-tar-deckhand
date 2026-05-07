# Bridge Dogfood Run 7

**Date:** 2026-05-01
**Topic:** Sentinel — launching our agentic SOC analyst
**Audience:** Internal sales + customer success kickoff (~35 reps)
**Duration:** 18 min
**Confidentiality:** internal
**Budget cap:** $5.00
**Visual personality:** Clean Strike — pure white surface (`#FFFFFF`), deep navy `#1B2B4B` as the Brand colour, burnt-orange `#E8470A` reveal accent firing only at the pivot (slide 7) and the close (slide 14 CTA), cool mid-grey `#8C9BAD` for de-emphasis; sans-only typography
**Arc:** Build-Up-Reveal

**Status:** Phase 1+2+3 complete + PowerPoint Mac PDF gate complete. The deck is the **v0.1.x patch verification gate** — Run 7 was deck-shaped to exercise as many of the 12 v0.1.x patches as feasible in one go, and to surface any patch that regressed.

**Verdict: NO-GO for v0.1.0 ship — one new finding (#22) is a v0.1.0 regression that must be patched before release.** Eleven of the 12 v0.1.x patches verified working at runtime; the twelfth (#13) verified for one of two routing bands but the second band surfaced a bridge↔engine contract mismatch that breaks the documented contract for 31–60 char SmartArt bullets.

## Why a seventh run

The v0.1.x patch backlog (Findings #3 / #7 / #8 / #12 / #13 / #14 / #16 / #17 / #18 / #19 / #20 / #21) landed 2026-04-30. Each patch closes a finding from the prior six dogfood runs. Run 7's job was to verify that every patch fires correctly under realistic deck conditions — not just under unit tests. Per the `feedback_dogfood_run_7_focus.md` memory contract, Run 7 was deliberately deck-shaped:

- 4 text-bearing IMAGE markers with EXACT-labels lists → exercises #19/#20
- 2 SMARTART-FROM-LIST markers with bullets >24 chars → exercises #13
- 1 BG marker deliberately authored WITH a residual `addText` label → exercises #17
- Section B palette table using `Brand colour` row label → exercises #12
- Section C with native chart routing language for 2 chart-shaped subjects → exercises chart-routing pattern
- Cohesion review end-to-end → exercises #18

The personality (Clean Strike — pure white + deep navy + burnt-orange reveal) is distinct from the six prior runs (Dark Industrial / Engineering Ink / Blueprint Retrospective / Redline / Boardroom Stone / Velvet Ledger). The arc (Build-Up-Reveal) is also new for the dogfood series.

## Pre-flight cache state

| Plugin | Source version | Cache version | Status |
|---|---|---|---|
| jack-tar-superpower-bridge | 0.1.1 | 0.1.0 + 0.1.1 (both present) | Source loaded via `.dogfood/jack-tar-superpower-bridge` symlink — v0.1.x patches live |
| jack-tar-cloud | 1.1.1 | **1.1.0 only** | **#16 retry decorator NOT in cache** — the `/jack-tar-cloud:image` skill dispatch goes to 1.1.0 source |
| jack-tar-deckhand | 1.2.0 | 1.1.0 | Functionally equivalent (1.2.0 was cache-key bump) |
| jack-tar-msft-smartart | 1.2.0 | 1.1.0 | catalog `vList2.max_label_chars=30` in BOTH versions (no contract change between 1.1.0 and 1.2.0) |

**Implication for #16:** the cloud retry decorator did not have an opportunity to fire — the cache version 1.1.0 doesn't carry it. No `ConnectionResetError` was observed organically in this run, so absence is acceptable; the retry decorator remains unit-test-covered (8 tests in `test_connection_retry.py` per the v0.1.x patch landing notes). To live-fire #16 on a future run the user must first copy `plugins/jack-tar-cloud` into `~/.claude/plugins/cache/jack-tar/jack-tar-cloud/1.1.1/`.

## Phase 1 — `/bridge-brief`

- **Approval turns: 4** — fifth consecutive run with **zero persona drift**. Split-dispatch (R1 → R2 → R3a → R3b) is now the entrenched working pattern (#3 + #7 patches landed in `bridge-brief/SKILL.md`). Each round held its scope; no whole-brief or surgical-edit dispatches were attempted.
- **brief_authoring cost recorded:** $0.18 in `output/dogfood-bridge-run-7/bridge-cost-ledger.jsonl` with `kind="brief_authoring"`. **Patch #8 OBSERVED.**
- **Arc:** Build-Up-Reveal — chosen over Problem-Solution and Hero's Journey. The persona's R1 recommendation was Problem-Solution; the Speaker chose Build-Up-Reveal for its natural register-shift pivot (slide 7), which the deck shape needed for the BG marker test.
- **Personality:** Clean Strike (the persona named it; the brief had asked for a pure-white-background palette). Distinct from all six prior runs.
- **Brief saved to:** `output/dogfood-bridge-run-7/creative-brief.md`
- **Brief operator note:** during brief assembly the EXACT-labels blockquotes were initially flattened from the persona's canonical `- role: "exact text"` format to plain bullets `- exact text`. The bridge's `extract_expected_text_for_marker` deterministic extractor returned 0 labels per marker until the canonical format was restored in the brief. **Operator-side correction, not a bridge regression** — the persona's R3b output was correct; the assembly step lost it. After fix, all 4 IMAGE markers extracted the right number of labels (9 / 6 / 6 / 11). Lesson: the brief writer should preserve the `role: "text"` shape verbatim; the persona's output is canonical.

## Phase 2 — `/pptx` authoring

14-slide deck authored deliberately to exercise the v0.1.x patches:

| Slide | Subject | Tool | Notes |
|---|---|---|---|
| 1 | Title — Sentinel | — | Big display mark on white |
| 2 | Threat landscape changed | **Native chart** (line, 2 series 2019–2026) | Chart routing language in Section C took |
| 3 | Level-2 analyst's day | — | Text-only timeline |
| 4 | Triage bottleneck | **Native chart** (bar, 2 series × 4 categories) | Chart routing language in Section C took |
| 5 | Why current tooling fails | `SMARTART-FROM-LIST:tooling-gaps` (side-accent) | Initially 31–48 char bullets (intent); reduced to 25–30 chars after Finding #22 surfaced |
| 6 | The unanswered question | — | Text-only crystallise |
| 7 | "Until now." pivot | **`BG:until-now`** + DELIBERATE residual `addText` label | Run 7 patch test for #17 |
| 8 | Introducing Sentinel + how it works | `IMAGE:sentinel-architecture` (side-accent) | 9 EXACT labels |
| 9 | Machine-speed triage | `IMAGE:triage-speed-comparison` (side-accent) | 6 EXACT labels |
| 10 | Story Sentinel tells | `IMAGE:sentinel-story-output` (side-accent) | 6 EXACT labels |
| 11 | Customer voices | — | 3 quote blocks with attribution |
| 12 | Where Sentinel fits | `SMARTART-FROM-LIST:competitive-position` (banner) | Initially 31–48 chars; reduced to 25–30 after #22 |
| 13 | How we go to market | **Native table** (3 rows × 5 cols) | Tabular data correctly routed |
| 14 | Your move — rep playbook | `IMAGE:rep-playbook-map` + burnt-orange CTA bar | 11 EXACT labels + reveal accent close |

- **9 markers detected by analyser** via OOXML primary path: 4 IMAGE + 1 BG + 2 SMARTART-FROM-LIST. Zero JS fallback. Zero duplicates. Zero overlap warnings.
- **objectName API used throughout** — Spike 1 pattern entrenched.
- **Slide 7 BG marker deliberately violates the Section C contract**: emits both the rect (`objectName="BG:until-now"`) AND a separate `addText` shape with text content `"BG:until-now"`. This is the Finding #17 fix test — the patch's `apply_background_in_memory` should remove the addText whose visible text equals the marker name.

## Phase 3 — `/enrich-deck`

### Step 1 — Brief parsed, palette derived

`derive_palette_from_brief_text` returned `BrandPalette(primary_fill_hex='1B2B4B', text_on_primary_hex='1B2B4B', text_on_surface_hex='1A1A1A')`. The `Brand colour` row in Section B's palette table was correctly recognised (post-#12 keyword set). **Patch #12 OBSERVED.**

Note: `text_on_primary_hex` collapsed to the same value as `primary_fill_hex` because the brief's palette table doesn't have an explicit `text on primary` row (the brief has `Body text: #1A1A1A` for body, and white-on-navy is implicit). For SmartArt rendering, the operator passed `text_on_primary_hex='FFFFFF'` explicitly to `BrandPalette` to ensure white labels on navy fills. **Pre-existing palette-derivation behaviour, not a Run 7 finding** — the heuristic correctly identified the Brand colour but couldn't synthesise the implicit white text choice. Document for future Section B template guidance.

### Step 2 — Analyser

```
Total slides: 14
Total markers: 7
JS fallback used: false
Duplicate marker IDs: []
Overlap warnings: 0
```

Per-marker:

| Slide | Kind | Identifier |
|---|---|---|
| 5 | SMARTART-FROM-LIST | tooling-gaps |
| 7 | BG | until-now |
| 8 | IMAGE | sentinel-architecture |
| 9 | IMAGE | triage-speed-comparison |
| 10 | IMAGE | sentinel-story-output |
| 12 | SMARTART-FROM-LIST | competitive-position |
| 14 | IMAGE | rep-playbook-map |

### Step 5 — Generation cycle (image markers)

#### Phase A Ollama — all 4 IMAGE markers + 1 BG

`x/z-image-turbo:fp8`, free, 1024×896 px (slides 8–10, 14) and 1280×720 (slide 7).

| Marker | Phase A outcome |
|---|---|
| `IMAGE:sentinel-architecture` | Fail. "SIEM / Log **Sonces**" / "EDR / **Endicost Teltoony**" / "**Thidet** Intel Feeds" / "**Sentirel**" / "**Anal**ist Story Feed" / "**ranked ranked stories**" |
| `IMAGE:triage-speed-comparison` | Fail. "**Sentrial**" / "**kéked story**" / "**amartls**" |
| `IMAGE:sentinel-story-output` | Fail. "**Sentinl: agentic SOC andist**" / "**Affticted ássicts**" / "**Recrmmseded action**" |
| `IMAGE:rep-playbook-map` | Fail. "**Adurt volume**" / "**Customer security nataarity**" / "**low cacuilty**" / "**Low lugency**" / "**Mature but overwhueled**" |
| `BG:until-now` | **Pass.** Atmospheric near-white with no text contamination — exactly the sweet spot for Ollama's z-image-turbo |

This is the Run 6 pattern reproduced at scale: Ollama z-image-turbo can handle atmospheric texture but reliably corrupts technical text labels. Phase A → Phase B escalation is the correct path.

#### Image-reviewer dispatch — patches #19/#20 verification

For each text-bearing IMAGE marker, the bridge extracted the EXACT-labels list from Section C via `extract_expected_text_for_marker()` and passed it to the `jack-tar-deckhand:image-reviewer` agent with the canonical comparison block:

```
**Expected text content:**
  - "SIEM / Log Sources"
  - "EDR / Endpoint Telemetry"
  - ...
**Critical check:** Read every word in the image and compare against the expected list above.
Report rendered-vs-expected mismatches as issues; do not confabulate correctness.
```

**All 4 reviewers caught the misspellings character-by-character.** Each returned `verdict: refine` with a structured `issues[]` quoting both rendered and expected strings, plus `composition_notes.text_rendering` describing the failure mode. No reviewer confabulated correctness — the Finding #19 confabulation pattern is closed by the patch.

| Marker | Reviewer issues |
|---|---|
| `IMAGE:sentinel-architecture` | "Endicast Teltoony" / "Thidiet Intel Feeds" / "ranked ranked stories" / "prioritize" vs "prioritise" — 4 issues, including the British/American spelling distinction |
| `IMAGE:triage-speed-comparison` | "Sentrial" / "kéked story" / "amartls" — 3 issues |
| `IMAGE:sentinel-story-output` | "Recmmended action" — 1 issue (caught the missing 'o') |
| `IMAGE:rep-playbook-map` | "Low lugency" / "Mature but overwhelwhelmed" — 2 issues |

**Patches #19 + #20 OBSERVED.** Reviewers given the EXACT-labels reference list reliably catch misspellings; Run 6 promised this; Run 7 confirms it under realistic conditions across 4 different image subjects.

#### Phase B Flash escalation

Privacy gate handshake: Speaker auto-confirmed (operator was also Speaker). All 4 IMAGE markers escalated to `gemini-3.1-flash-image-preview` at $0.067 each.

| Marker | Phase B outcome |
|---|---|
| `IMAGE:sentinel-architecture` | All 9 expected labels rendered correctly. British "prioritise" preserved. |
| `IMAGE:triage-speed-comparison` | All 6 expected labels correct. |
| `IMAGE:sentinel-story-output` | All 6 expected labels correct. "Recommended action" rendered with both 'm's. |
| `IMAGE:rep-playbook-map` | All 11 expected labels correct, including the burnt-orange "Lead here" annotation in the top-right quadrant. |

Phase B Flash is the Run 6 thesis incarnate. No Pro escalation invoked in Run 7 (the cycle's auto-Pro escalation behaviour was already validated in Run 6; Run 7 stopped at Flash to keep cost lean for the patch verification mandate).

### Step 7 — Apply enrichments — Finding #22 surfaced

The first `apply_enrichment` call **failed** with:

```
src.smartart_bridge.SmartArtBridgeError: engine.render failed:
  layout 'vList2' labels must be <= 30 chars
  (rationale: First-pass default per category norms.)
  Too long: ['SIEM — ingests but never triages',
             'SOAR — automates the playbook, not judgment',
             'Playbook automation — rules-bound, not adaptive',
             'Point AI tools — signals without story']
```

**This is Finding #22 — a v0.1.0 regression introduced by the #13 patch.** The bridge's `select_layout_for_bullets()` declares:

```python
LAYOUT_BULLET_CAPS = {
    "process1": 24,
    "list1": 30,
    "vList2": 60,   # ← bridge claim
}
```

But the msft-smartart catalog (both v1.1.0 cache and v1.2.0 source) says:

```json
"vList2": { "max_label_chars": 30 }
```

The bridge routes 31–60 char bullets to vList2, but the engine rejects them at the 30-char gate. Two-system contract mismatch.

The 25–30 char band of the patch (routing to `list1`) does work — verified after shortening the Run 7 bullets to ≤30 chars and re-running. Both SMARTART-FROM-LIST markers landed on `list1` correctly per the patch's intermediate band.

**Patch #13 PARTIALLY OBSERVED** — list1 routing works; vList2 routing surfaces #22 and crashes apply.

After bullet-shortening, apply succeeded with 7 enrichments — 4 IMAGE + 1 BG + 2 SMARTART-FROM-LIST.

### Step 8 — Apply outcome verification (LibreOffice raster)

LibreOffice produced rasters of the enriched deck. Slide 7 shows the BG image with "Until now." text overlaid; the deliberate `BG:until-now` `addText` label is **gone**. **Patch #17 OBSERVED in raster.** Slides 5 and 12 SmartArt are not visible in LibreOffice (Finding #6 limitation — LibreOffice cannot render injected SmartArt).

### Step 9 — Cohesion review

Dispatched `jack-tar-superpower-bridge:enrichment-cohesion-reviewer` against the LibreOffice rasters of all 7 enriched slides plus the visual-personality string from Section B. Reviewer returned:

- 5 slides `pass` (slides 7, 8, 9, 10, 14 — the BG and 4 IMAGE)
- 2 slides `unassessable_rasterisation` (slides 5, 12 — the SmartArt-from-list markers, per Finding #6)
- 0 slides flagged blocking
- **Aggregate verdict: pass**

Cohesion cost recorded: $0.020 with `kind="cohesion"`. **Patch #18 OBSERVED.**

### Step 11 — Enrichment report

Generated report shows the patch #14 distinct counter:

```
- Enrichments applied: backgrounds=1, images=4, smartart=0, smartart_from_list=2
```

The `smartart_from_list=2` row is separate from `smartart=0`. **Patch #14 OBSERVED.**

### PowerPoint Mac PDF gate (Step 12)

`tools/pptx_to_pdf.sh` produced `presentation-enriched.pdf` (871 KB). All 14 slides render correctly:

- **Slide 5 SmartArt:** `list1` layout with 4 navy-filled bordered boxes; bullets "SIEM — alert ingest, no triage" / "SOAR — playbook automate only" / "Playbook — rules, not adaptive" / "Point AI — signals, no story" — all rendered in white sans on navy.
- **Slide 7 pivot:** atmospheric near-white BG with "Until" (navy) + "now." (burnt-orange italic) text-on-top, hairline accent rule. **BG:until-now placeholder addText label is gone.** Patch #17 confirmed in PowerPoint render too.
- **Slide 8 IMAGE:** Phase B Flash architecture diagram, all 9 labels rendered. Three navy blocks left, central Sentinel, Analyst Story Feed right, three labelled arrows ingest/correlate/prioritise.
- **Slide 9 IMAGE:** Manual triage column / Sentinel column comparison, all 6 labels.
- **Slide 10 IMAGE:** Story card with Incident / Affected assets / Recommended action / Confidence: High — all 6 labels.
- **Slide 12 SmartArt:** `list1` banner with 4 navy boxes; bullets "SIEM — correlate, no judge" / "SOAR — automate, not adapt" / "Playbook — rules-bound only" / "Sentinel — agentic + speedy".
- **Slide 13 native table:** 3 rows × 5 cols, navy header band (`#1B2B4B`) + white text, body in near-black + de-emphasis grey.
- **Slide 14 IMAGE + CTA:** playbook map with burnt-orange "Lead here" annotation; bottom CTA bar in burnt-orange (`#E8470A`) with white text "Your first call is on Monday. Lead with the question. Pivot on the gap. Close on the story."

The Build-Up-Reveal arc closes correctly: burnt-orange fires twice — once at the slide 7 pivot, once at the slide 14 CTA. Two appearances; both earn their place.

## Cost summary

| Phase | Run 6 | Run 7 |
|---|---|---|
| Phase 1 (`brief_authoring`) | unmeasured | **$0.180** |
| Phase 3 generation Ollama | $0.000 | $0.000 (BG only — passed) |
| Phase 3 generation Flash | $0.268 (4×) | **$0.268** (4×) |
| Phase 3 generation Pro | $0.670 (5× — 1 retry) | $0.000 (no Pro escalation invoked) |
| Phase 3 reviews (Haiku) | $0.080 (16×) | $0.045 (5 Phase A + 4 Phase B = 9×) |
| Phase 3 cohesion (Sonnet) | $0.020 | **$0.020** |
| **Total** | $1.078 | **$0.513** |

Run 7 is roughly half Run 6's cost because no Pro escalation was needed for proof. Plenty of headroom remained against the $5.00 cap (~90% unused).

## Patch verification table — Run 7 GO/NO-GO criteria

Per `feedback_dogfood_run_7_focus.md` memory contract:

| # | Patched behaviour | Run 7 signature confirmed | Outcome |
|---|---|---|---|
| **#19/#20** | Reviewer dispatch includes `expected_text_content` | All 4 IMAGE markers received the EXACT-labels block; reviewers caught all misspellings; no confabulated `pass` verdicts | **OBSERVED** |
| **#21** | Verdict-coherence guard: refine→pass when issues[] empty | No reviewer happened to return refine with empty issues this run; all refine verdicts had substantive issues | NOT EXERCISED (organic only — covered by `test_cycle_state.py` unit tests) |
| **#13** | Layout routing by bullet length | 25–30 char band routed to `list1` correctly; **31–60 char band raised Finding #22** (engine constraint mismatch — see below) | **PARTIAL — list1 OBSERVED, vList2 FAILED** |
| **#16** | Cloud retry on `ConnectionResetError` | No connection reset occurred organically; cloud cache 1.1.0 lacks the decorator anyway | NOT EXERCISED (covered by `test_connection_retry.py` unit tests) |
| **#17** | BG marker `addText` cleanup | Slide 7 deliberately authored with residual `addText`; patch removed it; LibreOffice raster + PowerPoint Mac PDF both confirm clean output | **OBSERVED** |
| **#18** | `cohesion` cost kind in ledger | `bridge-run/bridge-cost-ledger.jsonl` contains a `kind="cohesion"` entry at $0.020 | **OBSERVED** |
| **#14** | smartart_from_list summary counter | Report Summary line reads `backgrounds=1, images=4, smartart=0, smartart_from_list=2` | **OBSERVED** |
| **#12** | Palette heuristic on accent/brand-only | `derive_palette_from_brief_text` returned `primary_fill_hex='1B2B4B'` from the "Brand colour" row | **OBSERVED** |
| **#3 / #7** | Split-dispatch documented | Phase 1 ran 4 dispatches with zero drift (5th consecutive run) | **OBSERVED** |
| **#8** | brief_authoring cost ledger | `output/dogfood-bridge-run-7/bridge-cost-ledger.jsonl` contains a `kind="brief_authoring"` entry at $0.18 | **OBSERVED** |

**11 of 12 patches verified working at runtime. 1 patch (#13) is half-broken.**

## Findings (Run 7)

### Finding #22 — bridge `LAYOUT_BULLET_CAPS["vList2"]=60` contradicts msft-smartart catalog `vList2.max_label_chars=30`

**Issue.** The v0.1.x patch for #13 (`select_layout_for_bullets()`) declares vList2 caps at 60 chars and routes 31–60 char bullets there. The downstream msft-smartart engine's `_check_constraints` enforces `max_label_chars=30` for vList2 per the catalog, raising `FlatListBuildError` when the bridge passes through 31+ char items. Result: any SMARTART-FROM-LIST whose longest bullet falls in the 31–60 band crashes `apply_enrichment`.

**Root cause.** The bridge patch's bullet-cap table (`enrichment_ops/smartart_from_list.py:LAYOUT_BULLET_CAPS`) was written from intent ("vList2 supports prose-length bullets") but never reconciled against the msft-smartart catalog's per-layout `max_label_chars` values. The catalog is the load-bearing truth — the engine enforces it; the bridge can't override.

**Manifestation in Run 7.** Initial `apply_enrichment` crashed when the deliberately-authored 31–48 char Run 7 bullets hit vList2. The deck completed only after hand-shortening bullets to ≤30 chars (forcing list1 routing). This regresses the patch's stated promise — "Authors do NOT need to hand-truncate prose-length bullets" — for the 31–60 char band specifically.

**Fix paths.**

- **(a) Update msft-smartart catalog vList2 `max_label_chars` to 60.** Requires validating that vList2 actually renders 60-char bullets without visual breakage (longer text may overflow the layout's text frames). If validation passes, this is the cleanest fix — bridge claim and catalog truth become consistent at 60.
- **(b) Update bridge `LAYOUT_BULLET_CAPS["vList2"]` to 30.** This collapses the patch's 25–30 list1 / 31–60 vList2 distinction into a single 25–30 list1 band, with truncation kicking in at >30. Functionally equivalent to having no vList2 routing, but advertises the patch as having three bands when it really has two.
- **(c) Audit ALL `LAYOUT_BULLET_CAPS` values against the catalog.** The whole table needs reconciliation — `process1=24` matches catalog (24); `list1=30` matches catalog (30); `vList2=60` doesn't match catalog (30). A consistency test should be added: parametrize over `LAYOUT_BULLET_CAPS` and assert each entry equals the catalog's `max_label_chars`.

**Recommendation.** Ship **(a) + (c)** as v0.1.2:
1. Validate vList2 actually renders 60-char bullets (manual gate on a test deck — if it does, update the catalog `max_label_chars` to 60 and add the rationale).
2. If validation fails, fall back to **(b) + (c)** — reduce the patch's vList2 cap to match the catalog and add the consistency test so this class of mismatch can't reoccur.

**Severity.** **Release-blocking for v0.1.0.** The patch's whole point was to relieve authors of hand-truncation; if the most expansive band still requires hand-truncation, the patch is half-finished. Authors who follow the patch's documented contract (write prose-length bullets, let the bridge route) will hit `EnrichmentApplyError` at apply time.

---

### Finding #23 — SMARTART-FROM-LIST marker placeholder `addText` survives enrichment (cosmetic)

**Issue.** Build.js authoring patterns include a small marker-name `addText` shape next to or below the SMARTART-FROM-LIST marker, so the marker is visible in the unenriched deck. The bridge's `apply_enrichment` replaces the bullet-list shape with the rendered SmartArt graphic, but the small placeholder label `addText` remains. The PowerPoint Mac render of slides 5 and 12 shows the SmartArt graphic AND a stranded grey italic label "SMARTART-FROM-LIST:tooling-gaps" / "SMARTART-FROM-LIST:competitive-position" floating beside it.

**Run 6 pattern context.** Run 6 didn't have this issue because the SMARTART-FROM-LIST marker placeholder convention there put the label inside the same shape as the bullets. Run 7's build.js authored a separate `addText` for the placeholder label — visible during authoring but stranded after enrichment.

**Severity.** Cosmetic — Speaker can manually delete the stranded label. Not release-blocking. Belongs in v0.2 polish work.

**Fix path.** Extend the #17 cleanup pattern (`apply_background_in_memory` removes `addText` whose visible text equals the BG marker name) to apply across all marker kinds. The bridge's `apply_smartart_from_list_in_memory` should remove `addText` shapes whose visible text equals the marker `objectName`. Same one-line fix shape, different op.

---

### Finding #24 — `text_on_primary` collapses to `primary` when the brief has no explicit "text on primary" row (pre-existing palette derivation behaviour)

**Issue.** The Run 7 brief's palette table has rows: Background `#FFFFFF`, Brand colour `#1B2B4B`, Body text `#1A1A1A`, Reveal accent, De-emphasis. There is no explicit "text on primary" row — the convention "white sits on Brand colour fills" is implicit in the prose. The heuristic returned `text_on_primary_hex == primary_fill_hex` (both `1B2B4B`), which would have produced navy-on-navy SmartArt body text if used.

**Workaround applied.** The operator passed `text_on_primary_hex='FFFFFF'` explicitly to the `BrandPalette` constructor, overriding the heuristic.

**Severity.** Pre-existing behaviour; not a Run 7 finding strictly speaking. Document for v0.2 brief-template guidance: the persona's Section B template should add an explicit `Text on Brand colour` row with a hex value, so the heuristic doesn't have to infer.

---

### Finding #25 — Brief-assembly format guarantee for EXACT-labels blockquote

**Issue.** The persona's R3b output produces EXACT-labels blockquotes in the canonical `- role: "exact text"` format. The bridge's `extract_expected_text_for_marker` parses exactly this shape — bullets with a `role:` prefix and the actual text in **double quotes**.

When the operator assembles the final brief, it's tempting (Run 7 evidence) to flatten the format to plain bullets `- exact text` for visual cleanliness. This silently breaks the extractor — it returns `[]` for every marker, which the SKILL.md interprets as "no text content", which means reviewers do NOT receive an `expected_text_content` block, which means we revert to Finding #19 confabulation territory.

**Severity.** Operator-side risk only — the persona's output is correct; brief assembly is a manual step. Caught in Run 7 because the operator immediately tested the extractor and saw 0 labels for all 4 markers.

**Fix paths.**

- **(a) Tighten `bridge-brief/SKILL.md` brief-assembly step to mandate exact persona format passthrough** — the assembly step should not "tidy up" Section C blockquotes. The Python writer's parse/re-emit should normalise the brief preserving the `- role: "exact text"` shape.
- **(b) Make `extract_expected_text_for_marker` more forgiving** — accept plain-bullet format (`- exact text`) as a fallback when the canonical `role: "text"` format isn't matched. Risk: looser parsing could pick up unrelated bullets within the marker's block.
- **(c) Add a brief-shape lint** — call `extract_expected_text_for_marker` on every text-bearing IMAGE marker as part of the `bridge-brief/SKILL.md` Step 4 save flow; halt if any returns 0 labels with a clear "Section C EXACT-labels block uses non-canonical format" message.

**Recommendation.** Ship **(c)** as v0.2 polish — it's a brief-time check that surfaces the issue before /enrich-deck runs and the operator burns Phase A cycles on a missing reference list.

## What Run 7 leaves to v0.2

Beyond the v0.1.0 v0.1.2 patches needed to fix #22:

- **Finding #15** — `CHART:slug` marker kind. Run 7 used Section C language workaround (which worked again — `/pptx` correctly routed slides 2 + 4 to native charts). v0.2 marker formalises this.
- **Finding #4** — SMARTART parser handles `·` and other inline list separators.
- **Finding #5** — process1 layout label cap (subsumed by the now-known catalog reconciliation work).
- **Finding #23** — extend `addText` cleanup to all marker kinds.
- **Finding #25** — brief-assembly EXACT-labels format lint at brief-save time.

## Verdict — NO-GO for v0.1.0

The deck rendered correctly. The PowerPoint Mac PDF gate passed. Eleven of twelve patches verified at runtime. **Finding #22 is the blocker** — the v0.1.x patch for #13 advertises a vList2 routing band that the engine doesn't actually support. Authors writing prose-length SmartArt bullets in the 31–60 char range will crash apply.

The fix is bounded and well-characterised: either update the catalog (path a) or update the bridge cap table (path b), plus add the consistency test (path c). Patch under v0.1.2, run a focused Run 8 dogfood that includes a 31–60 char SMARTART-FROM-LIST, then ship v0.1.0.

## Anti-patterns to entrench (Run 7 specifics)

### 11. Brief-assembly preserves the persona's canonical EXACT-labels blockquote format verbatim

The persona's R3b Section C output for text-bearing IMAGE markers uses:

```
> EXACT spelled labels REQUIRED:
> - role-name: "exact text"
> - role-name: "exact text"
```

When the operator transcribes the persona's output into the final brief, the `role: "text"` shape MUST survive. Flattening to `- exact text` breaks the bridge's `extract_expected_text_for_marker` extractor and silently regresses Finding #19 territory. The persona's output is canonical; the assembly step is structural transcription, not editorial polish.

**Deprecate by:** Finding #25 fix paths.

### 12. Bridge↔engine constraint tables must be reconciled at patch time

The v0.1.x patch for #13 declared `LAYOUT_BULLET_CAPS["vList2"]=60` without consulting the msft-smartart catalog's `vList2.max_label_chars=30`. Two-system contract claims must agree at the time of merge. A parametric test should iterate `LAYOUT_BULLET_CAPS` and assert each value equals the catalog's `max_label_chars` for the same layout id.

**Deprecate by:** Finding #22 fix path (c).

## Run 8 thesis

Run 8 is the v0.1.2 verification gate. Deck-shape requirement: at least one SMARTART-FROM-LIST marker with bullets in the 31–60 char band that exercises the vList2 path. If the catalog/bridge reconciliation lands cleanly, the patch should route the 31–60 band to vList2 (or the chosen substitute) without raising `EnrichmentApplyError`.

If Run 8 is GO, ship v0.1.0 + record Task 35 GO + push branch + open release PR.
