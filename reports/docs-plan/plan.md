# Documentation Plan — README Dual-Route (issue #62)

**Branch:** `docs/readme-dual-route` (off `main`)
**Inputs read:** `issue-62-body.md`, `issue-58-body.md`, `run-2-deferred-items.md`, `README.md`, `plugins/jack-tar-deckhand/CLAUDE.md`, project `CLAUDE.md`
**State note:** `plugins/jack-tar-superpower-bridge/` does not yet exist on this branch — the bridge plugin work lives on `feat/superpower-bridge`. Per Item 1 of `run-2-deferred-items.md`, the writer node will create a **stub** `plugins/jack-tar-superpower-bridge/CLAUDE.md` with an italic interim note plus the See-also cross-reference.

---

## 1. Audit of existing `README.md`

| Section | Lines | Verdict | Action |
|---|---|---|---|
| Title + tagline + one-liner | 1–5 | Accurate | Keep verbatim |
| Vision | 7–13 | Accurate but single-track-leaning | Light edit: introduce that there are now two routes; first mention of `/pptx` here qualifies as "the upstream `/pptx` skill" (deferred Item 2) |
| Problem Statement | 17–28 | Still accurate | Keep |
| Architecture Overview | 32–62 | **Stale** — describes only the conductor direct route | Rewrite to show two entry points (Bridge route emphasised, Direct route alongside). Keep the existing 3-layer diagram as the *Direct route* depiction; preserve the italic role-vs-skill-name note (deferred Item 5) |
| Project Components (1–8) | 64–197 | Accurate as descriptions of individual deckhand skills | Reframe under "Direct route components"; add a parallel "Bridge route components" subsection covering `/bridge-brief` and `/enrich-deck` |
| Project Structure | 199–276 | Stale (refers to old single-plugin layout) | Replace with a short pointer to the 5-plugin marketplace structure documented in project `CLAUDE.md`; do not re-enumerate every file |
| Shared Data Contracts | 280–296 | Accurate, applies to direct route | Keep, scope-tag as "direct route" |
| Development Approach | 300–312 | Accurate | Keep |
| Compatibility | 316–322 | Accurate | Keep |
| Status | 326–330 | Stale ("design and planning phase") | Replace with current-state line (BSA v1.4.0, 1010 monorepo tests, EPIC #58 in progress) — this is where the 2K/4K hedge lives per deferred Item 4 |
| Roadmap | 334–345 | Stale | Per deferred Item 3: keep the phased table format; mark phases 0–7 as Done; add two forward rows for EPIC #58 (resolution capability) and bridge maturation. **Do NOT** replace with a `What's next` block |
| License | 349–351 | Stale | Keep TBD or move to `LICENSE` file — out of scope for #62 |

---

## 2. README outline (post-rewrite)

Section order is deliberate — the reader sees what the project is, then which route fits them, then quick starts, before any deeper architecture.

```
1. Title + tagline + one-paragraph project description
   └─ unchanged from current

2. Vision
   └─ light edit; first mention of "the upstream /pptx skill" lands here
      (deferred Item 2)

3. Problem Statement
   └─ unchanged

4. Two routes at a glance         ← NEW, the centrepiece for AC1
   ├─ One sentence: "Jack-Tar offers two entry points: the Superpower
   │  Bridge route (default, collaborates with /pptx) and the Direct
   │  route (full Jack-Tar pipeline from a brief)."
   └─ Resolution-capability sentence VERBATIM from issue #62:
      "Both routes support 1K / 2K / 4K cloud-rendered visuals via the
      jack-tar-cloud plugin (see EPIC #58)."
      (deferred Item 4: keep this sentence verbatim; hedging lives in Status)

5. Choosing your route             ← NEW, AC1
   ├─ ASCII decision tree (see §3 below)
   └─ Three scenarios, headers + body VERBATIM from issue-62-body.md
      ### 1. Bridge from the start (default)        — full ¶ verbatim
      ### 2. Bridge after a stale /pptx run         — full ¶ verbatim
      ### 3. Jack-Tar direct route                  — full ¶ verbatim
      Bridge route is visually emphasised (header bolding / leading position).

6. Quick Start                     ← NEW
   ├─ Bridge route (default, listed first):
   │     /bridge-brief "your topic"
   │     /pptx ...                # use brief to drive the upstream pptx skill
   │     /enrich-deck output.pptx
   └─ Direct route:
         /jack-tar-deckhand:deck-conductor "your topic"

7. Architecture Overview           ← REWRITTEN
   ├─ One paragraph: marketplace = 5 plugins, two pipelines, shared engines
   ├─ Direct-route diagram (existing 3-layer ASCII art preserved)
   │  + italic note: "Diagram labels are functional roles; mapped skill
   │  names are listed in §8 below." (deferred Item 5 — labels NOT renamed)
   └─ Bridge-route diagram (new, simple)
         /pptx deck ──► /bridge-brief or /enrich-deck ──► enriched .pptx
                              (collaborates with deckhand skills)

8. Project Components              ← REORGANISED, AC4
   ├─ 8.1 Direct-route components (the existing 8 skills, condensed —
   │      defer the full descriptions to plugin SKILL.md / docs)
   └─ 8.2 Bridge-route components
         - /bridge-brief        — assess + plan
         - /enrich-deck         — review-first enrichment
         - shared engines       — jack-tar-cloud, jack-tar-ollama, smartart

9. Plugin Marketplace               ← NEW, short
   └─ Table of the 5 plugins (name, purpose, route(s) it serves)
      Cross-link to plugins/<name>/CLAUDE.md

10. Shared Data Contracts          ← KEEP (scope-tag "direct route")
11. Development Approach           ← KEEP
12. Compatibility                  ← KEEP
13. Status                         ← REPLACED
    └─ Current-state bullets:
       - BSA v1.4.0 (33 services, 6 personas)
       - 1010 monorepo + 33 cross-plugin integration tests passing
       - Bridge route shipped through v0.1.0 → v0.2.0
       - EPIC #58 (1K/2K/4K resolution) in progress    ← deferred Item 4 hedge
14. Roadmap                        ← UPDATED (phases-done table, deferred Item 3)
15. License                        ← unchanged
```

**Verbatim-fidelity checkpoints (writer must preserve byte-for-byte):**
- Section 4: the 2K/4K sentence from issue #62 line 37.
- Section 5: the three scenario subsection headers and body paragraphs from issue-62-body.md lines 19–26.

The technical-writer node MUST copy these passages from `/workspace/.archon/inputs/issue-62-body.md` rather than re-typing. The review node will diff.

---

## 3. Decision-tree draft

Designed for monospace rendering, ≤12 lines, no terminology a new reader hasn't already met by §5. Mirrors the example in issue #62 but tightens the leaf wording so each leaf names exactly one route.

```
                       Have you already run /pptx and want to fix the deck?
                                         │
                  ┌──────────────────────┴──────────────────────┐
                 Yes                                            No
                  │                                              │
                  ▼                                              ▼
      Bridge route, review-first              Are you starting from a brief?
      ──────────────────────────                          │
      /enrich-deck output.pptx           ┌────────────────┴────────────────┐
                                       Yes,                            Yes,
                                  collaborate with                full Jack-Tar
                                      /pptx                       pipeline only
                                        │                               │
                                        ▼                               ▼
                            Bridge route (default)              Direct route
                            ──────────────────────              ────────────
                            /bridge-brief →                /jack-tar-deckhand:
                            /pptx →                          deck-conductor
                            /enrich-deck
```

Width: 78 cols. Height: 12 lines (within the budget). Readable in `cat` and inside a markdown fenced code block.

**Why this shape, not the issue-#62 example:** the issue's example branches first on "starting from scratch?" then nests `/pptx` familiarity. That works, but a new reader who already has a stale `/pptx` deck has to walk past a "yes" branch before they reach their case. Leading with the rescue check ("already run `/pptx` and unhappy?") maps directly to scenario 2 and gets the rescue case to its leaf in one decision. The remaining two branches then split scenarios 1 vs 3 on "do you want to keep using `/pptx`."

If the speaker prefers the original orientation, the alternate form is in the writer-handoff appendix at the bottom of this plan.

---

## 4. Plugin cross-reference text

Both stay short — one paragraph each. They give the *why-jump* in a sentence, the *how-jump* in another, and a bare link.

### 4.1 `plugins/jack-tar-deckhand/CLAUDE.md` — append a "See also" section

```markdown
## See also — Superpower Bridge route

If you'd rather start from `/pptx` (the upstream skill in the
`superpowers-toolkit` plugin) and have Jack-Tar enrich the resulting
deck, use the **Superpower Bridge** plugin instead of the
`deck-conductor` direct pipeline. The bridge offers `/bridge-brief`
(plan a talk and prep a brief that drives `/pptx`) and `/enrich-deck`
(review an existing `/pptx` deck and layer Jack-Tar visuals onto it).
See `plugins/jack-tar-superpower-bridge/CLAUDE.md` and the
"Choosing your route" section of the top-level `README.md`.
```

### 4.2 `plugins/jack-tar-superpower-bridge/CLAUDE.md` — write a stub with an interim note + See also

The plugin directory does not exist on this branch. The writer node creates `plugins/jack-tar-superpower-bridge/CLAUDE.md` with this content (interim per deferred Item 1):

```markdown
# jack-tar-superpower-bridge

*Interim — this stub will be expanded when the bridge plugin is fully
released. See [GitHub issue
#53](https://github.com/SteveGJones/jack-tar-deckhand/issues/53).*

The Superpower Bridge plugin connects the upstream `/pptx` skill to the
Jack-Tar engine plugins (cloud/ollama image generation, SmartArt). It
is the **default route** for new Jack-Tar users — collaborate with
`/pptx` from the start, or rescue a stale `/pptx` deck with a
review-first enrichment pass.

## Skills

| Skill | Purpose |
|-------|---------|
| `/bridge-brief` | Plan a talk and produce a brief that drives `/pptx`. |
| `/enrich-deck`  | Review-first enrichment of an existing `.pptx` — assess what's salvageable, collaborate with the speaker on enrich-in-place vs rebuild. |

## See also — Direct route

If you want the full Jack-Tar pipeline from a brief — brand profile,
narrative architect, strategy map, full QA — without `/pptx`
involvement, use the **deck-conductor** in the
`jack-tar-deckhand` plugin. See
`plugins/jack-tar-deckhand/CLAUDE.md` and the "Choosing your route"
section of the top-level `README.md`.
```

The italic interim note is mandatory (deferred Item 1). Keep the See-also section even though the rest of the file is a stub.

---

## 5. Open questions

Limited list — most prior open items were resolved in `run-2-deferred-items.md`. Questions left:

1. **Plugin marketplace table — exact column set.** The current project `CLAUDE.md` enumerates 5 plugins with a `Skills` column. For the README, I plan to use `Plugin | Purpose | Route(s)` (substituting "Skills" with "Route(s) served") to keep the section short and route-aligned. If the speaker prefers preserving the `Skills` column from `CLAUDE.md` verbatim, the writer should follow that instead. **Default for the writer:** use `Plugin | Purpose | Route(s)`.

2. **`/pptx` plugin attribution.** The README will refer to `/pptx` as "the upstream `/pptx` skill" on first mention (deferred Item 2). Run #2 did not specify whether to also name the providing plugin (`superpowers-toolkit`). **Default for the writer:** name it once on first mention only ("the upstream `/pptx` skill from the `superpowers-toolkit` plugin"), then use bare `/pptx` thereafter. Drop the plugin attribution if the writer can't verify the exact plugin name from on-disk evidence.

3. **License section.** Currently TBD. Out of scope for #62 — leave as TBD or move to a separate `LICENSE` file in a future issue.

These do not block the writer; defaults are stated.

---

## 6. Test for the writer (acceptance smoke test)

Three questions a reader must be able to answer in under five minutes from the rewritten README. The writer should self-check by reading the draft top-to-bottom against these prompts; the review node will repeat the check.

1. **"If I want to start from a `/pptx` workflow, which entry point do I use?"**
   → §5 scenario 1 (Bridge from the start) + §6 Bridge Quick Start: `/bridge-brief` then `/pptx` then `/enrich-deck`. Decision tree leaf: "Bridge route (default)."

2. **"If I have a stale `/pptx` deck I want to fix, what do I do?"**
   → §5 scenario 2 (Bridge after a stale `/pptx` run) + decision tree top-left leaf: `/enrich-deck output.pptx` review-first mode.

3. **"How do I get a 4K hero slide?"**
   → §4 Two-routes-at-a-glance verbatim sentence: "Both routes support 1K / 2K / 4K cloud-rendered visuals via the `jack-tar-cloud` plugin (see EPIC #58)." Status section adds the live hedge that EPIC #58 is in progress.

If any of these three questions cannot be answered from the rewritten README in ≤5 minutes by someone who has not read this plan or the source issues, the rewrite has failed AC1 and AC6.

---

## Appendix — Alternate decision-tree shape (only if speaker rejects §3)

The original issue-#62 orientation, kept here for reference:

```
Are you starting from scratch?
├── Yes → Have you used /pptx before?
│        ├── Yes (or want to)            → Bridge route (default)
│        └── No, want full Jack-Tar      → Direct route
└── No, I have a stale /pptx deck        → Bridge "review-first" mode
```

This form is shorter (5 lines) but buries the rescue path. §3 is preferred for a new reader landing cold; this form is preferred for a reader who already knows they want a route and just needs the syntax.
