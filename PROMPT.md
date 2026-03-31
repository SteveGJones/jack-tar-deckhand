# Rendering Strategy Expansion — Overnight Build

## What You Are Doing

You are implementing the rendering strategy expansion for Jack-Tar Deckhand. This expands the pipeline from 3 rendering strategies (full_render, backdrop_render, composed) to 5 (+ background, backdrop, pragmatic_composition).

## References

- **Implementation plan:** `docs/superpowers/plans/2026-03-30-rendering-strategy-expansion.md` — Follow this task by task, in order. Each task has exact file paths, test code, implementation code, and commit instructions.
- **Design spec:** `docs/superpowers/specs/2026-03-30-rendering-strategy-expansion.md`
- **Architecture spike:** `docs/spikes/backdrop-content-aware-positioning.md`
- **Project instructions:** `CLAUDE.md` and `CONSTITUTION.md`

## How To Execute

1. Read the implementation plan at `docs/superpowers/plans/2026-03-30-rendering-strategy-expansion.md`
2. Execute Tasks 1 through 14 sequentially
3. For each task:
   a. Write the failing test(s) first
   b. Run them to confirm they fail
   c. Write the implementation
   d. Run the tests to confirm they pass
   e. Run the full test suite: `source .venv/bin/activate && pytest -x -q`
   f. If all tests pass, commit with the message specified in the plan
   g. If tests fail, fix the issue before moving to the next task — do NOT skip ahead
4. After completing all 14 tasks, run the full suite one final time and report the result

## Rules

- **TDD strictly.** Write the test, watch it fail, write the code, watch it pass. No exceptions.
- **No cloud API calls.** All image generation uses Ollama only. Integration tests (Task 14) are tagged with `@pytest.mark.ollama` — run them if Ollama is available, skip if not.
- **Commit after every task.** Each task is a self-contained unit. Commit immediately after tests pass.
- **Do not modify files outside the plan.** The plan specifies exact file paths. Don't refactor, clean up, or "improve" code beyond what the plan calls for.
- **Backward compatibility.** Existing `backdrop_render` strategy must continue to work. The existing 446 tests must still pass after every task.
- **If a test in the plan doesn't match reality** (e.g., a function signature has changed since the plan was written), adapt the test to match the actual code — but preserve the test's intent.
- **Use `source .venv/bin/activate`** before any Python command.
- **Use `node`** for assembler commands.

## Verification

After all 14 tasks are complete:

```bash
source .venv/bin/activate && pytest -x -q
```

Expected: All original 446 tests + ~44 new tests = ~490 tests passing.

If Ollama is running, also run:

```bash
source .venv/bin/activate && pytest tests/test_integration_rendering.py -m ollama -v
```

## What Success Looks Like

- 14 commits, one per task
- All tests pass (original + new)
- Strategy map schema accepts 6 strategy values
- Image manifest schema accepts detected_positions and element_id
- `classify_slide_strategy()` returns `background` for dense content slides
- 5 element layout templates available via `get_element_layout()`
- `buildBackgroundSlide()` renders 5 template zone variants
- `buildPragmaticSlide()` assembles multi-image slides with text labels
- `buildBackdropSlide()` places text at detected or prescribed positions
- Vision analyst agent defined at `.claude/agents/vision-analyst.md`
- AP-27 and AP-28 QA checks implemented and wired into run_qa.py
