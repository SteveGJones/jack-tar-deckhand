# Draft change log

## Files modified
- `README.md` — sections rewritten: Vision (introduced two-route framing), Architecture Overview (rewritten for both routes), Project Components (reorganised into 8.1 Direct / 8.2 Bridge), Project Structure (replaced with Plugin Marketplace table), Status (replaced stale "design and planning phase" with current-state bullets), Roadmap (phases 0–7 marked Done, EPIC #58 and bridge maturation rows added); NEW sections added: "Two routes at a glance", "Choosing your route" (decision tree + three verbatim scenarios), "Quick Start" (both routes)
- `plugins/jack-tar-deckhand/CLAUDE.md` — added "See also — Superpower Bridge route" section after Quick Start
- `plugins/jack-tar-superpower-bridge/CLAUDE.md` — created as a stub with interim note, Skills table, and "See also — Direct route" section (directory did not previously exist on this branch)

## Open issues for review
- The Roadmap table gained a `Done` / `In progress` / `Planned` column, but that column is not in the original table schema. The plan said "keep the phased table format; mark phases 0–7 as Done" — the status column may need to be formatted differently if the review node finds it visually noisy.
- `/pptx` plugin attribution: named once as "the upstream `/pptx` skill" in the Vision section, without the `superpowers-toolkit` qualifier, because the exact plugin name could not be verified from on-disk evidence (per plan §5, open question 2 default: drop attribution if unverifiable).

## Self-test answers
For the three reader questions from the plan:

- **Q1: "If I want to start from a `/pptx` workflow, which entry point do I use?"**
  → "Choosing your route" §5, scenario 1 (Bridge from the start) + Quick Start bridge block: `/bridge-brief` → `/pptx` → `/enrich-deck`. Decision tree leaf: "Bridge route (default)."

- **Q2: "If I have a stale `/pptx` deck I want to fix, what do I do?"**
  → "Choosing your route" §5, scenario 2 (Bridge after a stale `/pptx` run) + decision tree top-left leaf: `/enrich-deck output.pptx` review-first mode.

- **Q3: "How do I get a 4K hero slide?"**
  → "Two routes at a glance" verbatim sentence: "Both routes support 1K / 2K / 4K cloud-rendered visuals via the `jack-tar-cloud` plugin (see EPIC #58)." Status section adds the live hedge that EPIC #58 is in progress.
