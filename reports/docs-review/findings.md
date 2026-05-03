# Documentation review: README dual-route (#62)

## Summary verdict
PASS_WITH_REVISIONS

One critical defect (deferred Item 2 — first-mention `/pptx` qualifier) and three advisory issues. The verbatim-fidelity check on the three scenarios passed cleanly (byte-identical to `issue-62-body.md`), and all five other acceptance criteria pass.

## Acceptance criteria

| # | Criterion | Verdict | Evidence (file:line) |
|---|---|---|---|
| AC1 | New reader identifies right route within 5 minutes | pass | Vision (README.md:9–13) introduces dual-route framing; "Two routes at a glance" (README.md:32–36); "Choosing your route" tree + scenarios (README.md:40–71); "Quick Start" (README.md:75–89). Self-tested against the three plan-spec questions; all answerable on a single skim. |
| AC2 | Both plugin CLAUDE.md files cross-reference the other route | pass | `plugins/jack-tar-deckhand/CLAUDE.md:43–52` (See also — Superpower Bridge route, links to bridge CLAUDE.md and README §Choosing your route). `plugins/jack-tar-superpower-bridge/CLAUDE.md:20–27` (See also — Direct route, links back to deckhand CLAUDE.md and README). Both link targets resolve. |
| AC3 | No code changes; no test changes | pass | `git show --stat 17175cf` (the draft commit) touches only `README.md`, `plugins/jack-tar-deckhand/CLAUDE.md`, `plugins/jack-tar-superpower-bridge/CLAUDE.md`, and `reports/docs-draft/changes.md`. Zero `src/`, `tests/`, or `plugins/*/src` paths. |
| AC4 | README mentions 2K/4K capability availability | pass | README.md:36 carries the verbatim sentence from issue #62 line 37. Status line at README.md:219 carries the in-progress hedge (deferred Item 4). See advisory A2 below — the hedge phrasing leans aspirational. |
| AC5 | Decision tree included and visually clear | pass | README.md:42–62. Max line width 79 characters (fits 80-col terminal without wrap); 21 lines tall; renders inside a fenced code block in monospace. Three scenarios are distinguishable as leaves. See advisory A1 — the second branch's leaf labels both start with "Yes,…" which weakens the binary decision. |
| AC6 | Three scenarios match `issue-62-body.md` VERBATIM | **pass (CRITICAL CHECK)** | Ran `diff <(sed -n '19,26p' .archon/inputs/issue-62-body.md) <(sed -n '64,71p' README.md)` — exit 0, no output, byte-identical. All three subsection headers and all three body paragraphs match. Em-dashes preserved, bold markers preserved, slash-command names preserved. |

## Deferred-items verification (from `run-2-deferred-items.md`)

| Item | Status | Evidence |
|---|---|---|
| Item 1 — Bridge plugin stub with italic interim note + See-also | pass | `plugins/jack-tar-superpower-bridge/CLAUDE.md:3–5` (italic note pointing at issue #53); See-also at lines 20–27. |
| Item 2 — First `/pptx` mention qualified as "upstream" | **FAIL** | `README.md:11` — first prose mention says **"The existing `/pptx` skill"**, not "the upstream `/pptx` skill". The word "upstream" doesn't appear until line 81 (inside a code-block comment) and line 147 (Project Components table). The change log claims this was done; the file disagrees. |
| Item 3 — Phases-done Roadmap table preserved (no `What's next` block) | pass | README.md:225–236 — phased table format retained, phases 0–7 marked Done, EPIC #58 + bridge maturation as forward rows. The new `Done`/`In progress`/`Planned` column is informative; not a `What's next` block. |
| Item 4 — 2K/4K verbatim sentence unchanged + Status hedges | pass with caveat | Verbatim sentence at README.md:36 unchanged. Status line at README.md:219 says "EPIC #58 … in progress — available for testing via `jack-tar-cloud`". See advisory A2. |
| Item 5 — Italic note below diagram retained; diagram labels not renamed | pass | README.md:117 — italic note present. Functional role labels (`narrative`, `iconset`, `palette`, `pptx-build`, `slide-qa`, `brand-qa`, `layout`) retained at README.md:108–115. |

## Critical issues (must fix before merge)

- **[README.md:11]** First prose mention of `/pptx` reads `The existing \`/pptx\` skill`. Per `run-2-deferred-items.md` Item 2 (and the docs-plan §1 audit row for Vision lines 7–13), the first mention must qualify the skill as **"the upstream `/pptx` skill"**. The change log at `reports/docs-draft/changes.md:10` claims this was done but the file shows otherwise. **Fix:** change `The existing \`/pptx\` skill` → `The upstream \`/pptx\` skill` (or `The existing upstream \`/pptx\` skill` if "existing" must be retained). The `run-2-deferred-items.md` verification checklist explicitly lists this as a GO-blocker: "If any item failed, surface it as a critical issue in the synthesis report and DO NOT recommend GO."

## Advisory issues (worth addressing but not blocking)

- **A1. [README.md:42–62]** Decision-tree second branch ambiguity. The "No" branch asks `Are you starting from a brief?` and then both leaves answer `Yes,…` — `Yes, collaborate with /pptx` vs `Yes, full Jack-Tar pipeline only`. A binary question whose two leaves both say "Yes" doesn't actually decide between them; the real differentiator is `/pptx` involvement. Suggest reformulating the second-level question as `Want to keep using /pptx?` (Yes → Bridge default; No → Direct) so each leaf's label answers the question it's under. The plan defended the first-level rescue-first orientation, which is fine; the issue is only at the second level.
- **A2. [README.md:219]** Status-line hedge is louder than warranted. `EPIC #58 (1K / 2K / 4K resolution capability) in progress — available for testing via \`jack-tar-cloud\`` reads as "you can test 2K/4K today". Per `issue-58-body.md:12–28` the per-provider 2K/4K parameters are unwired (most rows ❌ in the capability matrix); only 1K is shipping today, and 2K/4K wait on issues #59/#60/#61. Suggest tightening to e.g. `EPIC #58 — 1K shipping; 2K/4K wiring in flight (#59/#60/#61)` or `EPIC #58 (1K / 2K / 4K resolution) — 1K available, 2K/4K not yet wired across providers`. The deferred-items direction was satisfied (a hedge exists); this advisory is about the hedge accurately matching the per-issue state.
- **A3. [README.md:153–164]** Plugin Marketplace table now lists 6 plugins; project `CLAUDE.md` Plugin Architecture table lists 5 (no `jack-tar-superpower-bridge` entry). The README is right — the bridge stub now exists — but the project `CLAUDE.md` will be out of date once this PR merges. Out of scope for #62; flag as a follow-up issue rather than fixing here.
- **A4. [README.md:225–236]** The Roadmap table now has a 4-column shape (`Phase | Milestone | Key Deliverables | Status`) but uses the existing 3-column header (`Phase | Milestone | Key Deliverables`); the `Done`/`In progress`/`Planned` cell sits in an implicit fourth column. The change log flagged this. Either add a `Status` column header, or drop the column and move status into the `Phase` cell (e.g. `**0 — Foundation** ✅`). Visual; not blocking.

## Strengths (keep these)

- The three scenarios are byte-identical to the issue source. The diff protocol caught no drift — em-dashes intact, bold markers intact, slash-command names intact. The first-run regression (paraphrased scenarios) did not recur.
- Bridge-as-default is signalled three times (Vision "the default", Two-routes-at-a-glance "default", Choosing-your-route subsection 1 "(default)"), and the Quick Start lists Bridge first. Hierarchy of emphasis is right.
- Decision tree fits 80 columns and renders predictably as monospace. The leaf-shape (rule-with-underline + slash-command labels) lets a scanner pick their leaf without reading the questions.
- Cross-references in both plugin CLAUDE.md files name *both* the sibling CLAUDE.md and the README's "Choosing your route" anchor — readers can navigate either way.
- The italic role-vs-skill-name disambiguation note (README.md:117) preserves diagram stability without forcing a rename ripple.
- The bridge plugin stub correctly carries the interim italic note pointing at issue #53, so future readers know the doc is incomplete by design.
- Project Components (§8.1 / §8.2) split keeps direct-route and bridge-route components legible without duplicating skill descriptions.

## Open questions for the speaker

1. **Decision-tree second branch (A1).** Should the second-level question be reworded so its leaves are a true binary (e.g. `Want to keep using /pptx?`)? The plan §3 chose the current shape deliberately; reworking would mean revisiting that choice. Speaker call.
2. **Status hedge phrasing (A2).** Is "available for testing via `jack-tar-cloud`" acceptable as today's hedge, or should the README be more explicit that 2K/4K wait on #59/#60/#61? The deferred-items direction said "ensure the Status line carries the hedge" — both phrasings satisfy that letter; the question is whether the spirit (don't oversell what's shipped) is met.
3. **Roadmap Status column (A4).** Add a header for the implicit Status column, or fold status into the Phase cell with an emoji?
