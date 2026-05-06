# Documentation Draft — README Dual-Route

## Your Role

You are a technical writer in the docs-team container. Your job is to execute the plan written by the previous node (`reports/docs-plan/plan.md`) — produce the rewritten `README.md`, update both plugin-level `CLAUDE.md` files, and verify your edits parse and render cleanly.

Use the technical-writer agent (via `Agent(subagent_type="sdlc-team-docs:technical-writer")`) for prose drafting, plain-language sweeps, and microcopy decisions. Use `document-skills:doc-coauthoring` for the structured-content workflow if it helps you sequence the work.

## Context

You are at `/workspace`, on a feature branch off `main`. The plan from the previous node is at `reports/docs-plan/plan.md` — read it first; it is your authoritative input.

**Before drafting, load:**
1. `reports/docs-plan/plan.md` — the plan (your spec)
2. `README.md` — the file you are rewriting
3. `plugins/jack-tar-deckhand/CLAUDE.md` — to know what cross-reference text fits
4. `plugins/jack-tar-superpower-bridge/CLAUDE.md` — same

## What To Do

### Phase 1: README rewrite

Implement the structure from the plan. Critical requirements:

- **Bridge as visually-emphasised default.** The "Choosing your route" subsection should lead with Bridge, with the three scenarios in this order: (1) Bridge from the start, (2) Bridge after stale `/pptx`, (3) Jack-Tar direct route.
- **Three scenarios VERBATIM from the pre-fetched issue body.** Open `/workspace/.archon/inputs/issue-62-body.md`. Find the `## Three entry-point scenarios (from project owner)` heading. **Copy the prose under each of the three `### N.` subheadings into the README without modification.** Do not paraphrase, do not abbreviate, do not "improve". Do not invent transitions or hand-off paths that aren't in the source. Match every word, including em-dashes, italics, and bold. This is the most important rule of this draft. The review node will perform a verbatim diff against this file as a critical acceptance criterion.
- **Decision tree.** Use the ASCII draft from the plan; refine for clarity; keep it under 12 lines so it fits in a glance.
- **Quick-start blocks.** Show actual command invocations:
  - Bridge: `/bridge-brief "your topic"` → `/pptx ...` → `/enrich-deck output.pptx`
  - Direct: `/jack-tar-deckhand:deck-conductor "your topic"`
- **Resolution capability mention.** A one-sentence note near the visual/output discussion: "Both routes support 1K / 2K / 4K cloud-rendered visuals via the `jack-tar-cloud` plugin (see EPIC #58)."
- **Preserve accurate sections.** Do not rewrite Status, Implementation Status, or the Architecture Summary if they are accurate. Refresh anything that is stale.
- **No emojis** unless the existing README uses them and you are matching style.
- **No marketing copy.** Plain-language, accurate, scoped to what is shipped.

### Phase 2: Plugin CLAUDE.md cross-references

For each plugin:
- Find the right anchor (likely after the "Quick Start" or "Skills" section).
- Add a "See also" subsection with the cross-reference text from the plan.
- Keep it one paragraph. Link to the other plugin's CLAUDE.md path within the repo.

Edit `plugins/jack-tar-deckhand/CLAUDE.md` and `plugins/jack-tar-superpower-bridge/CLAUDE.md`.

### Phase 3: Verify

Verify your edits do not break anything obvious:

```bash
# Verify README renders as valid markdown (no broken links, no unclosed code blocks)
grep -c "^```" README.md  # should be even (every fence opens and closes)

# Verify cross-reference links resolve
grep -oE "plugins/jack-tar-[a-z-]+/CLAUDE\.md" README.md plugins/jack-tar-deckhand/CLAUDE.md plugins/jack-tar-superpower-bridge/CLAUDE.md | sort -u
ls -la $(grep -oE "plugins/jack-tar-[a-z-]+/CLAUDE\.md" README.md | sort -u) 2>&1
```

Read your final `README.md` end-to-end as if you were a new user. Self-check:
- Can a new reader pick the right route within 5 minutes?
- Are the three scenarios distinguishable?
- Is the decision tree readable?

## Output

The artifacts are the edits themselves. Also write a brief change log to `/workspace/reports/docs-draft/changes.md`:

```markdown
# Draft change log

## Files modified
- README.md — sections rewritten: <list>
- plugins/jack-tar-deckhand/CLAUDE.md — added See-also section
- plugins/jack-tar-superpower-bridge/CLAUDE.md — added See-also section

## Open issues for review
- <anything you wanted to do but couldn't fully resolve>

## Self-test answers
For the three reader questions from the plan:
- Q1: <where in the new README the answer is>
- Q2: <where in the new README the answer is>
- Q3: <where in the new README the answer is>
```

## Commit

```bash
cd /workspace
mkdir -p reports/docs-draft
git add README.md plugins/jack-tar-deckhand/CLAUDE.md plugins/jack-tar-superpower-bridge/CLAUDE.md reports/docs-draft/changes.md
git commit -m "docs(draft): README dual-route rewrite + plugin cross-references (#62)"
```
