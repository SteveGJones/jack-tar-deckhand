# Revision change log

## Critical issues addressed

- **[README.md:11] Item 2 — `/pptx` upstream labelling** — Changed `The existing \`/pptx\` skill` to `The upstream \`/pptx\` skill`. This is the first prose mention of `/pptx` in the Vision section, satisfying `run-2-deferred-items.md` Item 2 and the critical finding from the review.

## Advisory issues addressed

- **A1 [README.md:42–62] Decision-tree second branch** — Reformulated the second-level question from `Are you starting from a brief?` (whose two leaves both answered "Yes,…") to `Want to keep using /pptx?` with clear `Yes` / `No` branches. Yes → Bridge route (default); No → Direct route. Each leaf now directly answers the question it is under, and the two leaves are distinguishable without reading the prose below.
- **A2 [README.md:219] Status-line hedge accuracy** — Changed `EPIC #58 (1K / 2K / 4K resolution capability) in progress — available for testing via \`jack-tar-cloud\`` to `EPIC #58 (1K / 2K / 4K resolution capability) — 1K available via \`jack-tar-cloud\`; 2K / 4K wiring in flight (#59 / #60 / #61)`. This accurately reflects that only 1K is available today and 2K/4K wait on open issues, without touching the verbatim sentence in the "Two routes at a glance" section.
- **A4 [README.md:225] Roadmap Status column header** — Added `Status` column header and corresponding separator `--------` to the Roadmap table. The table previously had an implicit fourth column with `Done` / `In progress` / `Planned` values but no header.

## Advisory issues deferred (and why)

- **A3 [README.md:153–164] Project CLAUDE.md Plugin Architecture table** — Out of scope for #62. The README now lists 6 plugins (correct) but the project `CLAUDE.md` Plugin Architecture table still lists 5. Flagged as a follow-up; no action taken here to avoid touching files outside the PR scope.

## Unresolved critical issues

None.

## Open questions still pending for speaker

1. **Decision-tree second branch (A1) — speaker validation.** The second-level question was reworded from `Are you starting from a brief?` to `Want to keep using /pptx?` per advisory A1. The plan §3 chose the original shape deliberately; the speaker should confirm this reformulation is acceptable, or revert to the prior question with the understanding that the leaf labels will remain ambiguous.
2. **Status hedge phrasing (A2) — speaker validation.** The Status line now reads `1K available via \`jack-tar-cloud\`; 2K / 4K wiring in flight (#59 / #60 / #61)`. The deferred-items direction (Item 4) said "ensure the Status line carries the hedge" — both phrasings satisfy that letter. Speaker should confirm this level of specificity is desired or preferred.
3. **Roadmap Status column (A4).** `Status` column header added. Speaker should confirm the 4-column shape is preferred over folding status into the Phase cell with emoji (e.g. `**0 — Foundation** ✅`).

## Deferred-items verification (run-2-deferred-items.md)

- **Item 1** — Bridge plugin CLAUDE.md has an italic interim note at the top AND keeps its See-also section. **PASS** (pre-existing, unchanged this pass; confirmed at `plugins/jack-tar-superpower-bridge/CLAUDE.md:3–5` and `:20–27`).
- **Item 2** — First mention of `/pptx` in README now qualifies it as "upstream" (`README.md:11`). **PASS** (fixed this pass; was FAIL in review).
- **Item 3** — Phases-done table remains; no `What's next` block was added. **PASS** (unchanged).
- **Item 4** — 2K/4K verbatim sentence at `README.md:36` unchanged; Status line at `README.md:219` now carries an accurate hedge. **PASS**.
- **Item 5** — Italic note below architecture diagram remains (`README.md:117`); diagram labels NOT renamed. **PASS** (unchanged).

## Re-verification

- **Markdown sanity:** pass — fenced code blocks balanced; all internal anchors referenced in cross-references remain intact (no section headers renamed).
- **Three reader-test questions still answerable:** yes
  - Q1 ("If I want to start from a `/pptx` workflow, which entry point do I use?") — decision tree "Want to keep using /pptx? → Yes → Bridge route (default)" + Quick Start bridge block.
  - Q2 ("If I have a stale `/pptx` deck I want to fix, what do I do?") — decision tree top-left leaf: "Bridge route, review-first / `/enrich-deck output.pptx`" + scenario 2.
  - Q3 ("How do I get a 4K hero slide?") — "Two routes at a glance" verbatim sentence unchanged; Status section now accurately hedges that 2K/4K wiring is in flight.
- **Scenario text faithful to issue #62:** yes — verbatim scenarios in §1/§2/§3 under "Choosing your route" were not touched; remain byte-identical to `issue-62-body.md`.
