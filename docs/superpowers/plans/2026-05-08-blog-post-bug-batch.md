# Plan — Blog-post bug batch (Issues #72, #73, #74, #75)

**Status:** ready to execute
**Created:** 2026-05-08
**Source:** [2026-05-07 blog-post asset run dogfood retrospective](../dogfooding/2026-05-07-blog-post-asset-run.md)
**Issues addressed:** #72 (cloud retry / httpx), #73 (Recraft V4 default style), #74 (Imagen Fast resolution kwarg), #75 (Ollama single-flight)
**Coordinated release:** lands together with #76 (discipline hook) — see [Coordinated release section](#coordinated-release) below.

## Why these four together

Four real bugs surfaced in a single end-to-end dogfood run on 2026-05-07. None block a release on its own; together they form a "polish batch" worth shipping behind one PR train. All four are localised to provider plumbing; none touch architecture, contracts, or tests outside the affected modules.

Order matters because three of the four sit in `plugins/jack-tar-cloud/src/generate_cloud_image.py` — doing them as separate PRs would force three sequential rebases. Better as one branch, one PR per issue (or one bundled), with the Ollama fix as a separate parallel branch since it's a different plugin.

## Branch strategy

Two branches, three PRs:

- **`fix/cloud-bug-batch-72-73-74`** — touches only `plugins/jack-tar-cloud/`. One PR per issue, stacked. Each PR small, each independently reviewable. Cherry-pick or rebase order: #72 → #73 → #74 (no inter-PR dependencies, but ordering matters for clean diffs).

- **`fix/ollama-single-flight-75`** — touches only `plugins/jack-tar-ollama/`. Independent. One PR.

Both branches can be developed in parallel.

## Pre-work

Before any code changes:

1. **Reproduce each bug as a test first** — TDD. The test must fail against current main before any fix lands.
2. **Confirm baseline test count.** `cd plugins/jack-tar-cloud && pytest tests -q` should report N passing. After all three fixes land, N + (new tests added) passing.
3. **Confirm cloud provider keys are set in the test environment** for the integration tests (where applicable). The unit tests for the retry decorator are mock-only, no keys required.

## Phase 1 — Issue #72 (cloud retry decorator misses httpx)

**Branch:** `fix/cloud-bug-batch-72-73-74` (first commit on branch)

### Tasks

1. **Write a failing test** in `plugins/jack-tar-cloud/tests/test_retry_decorator.py`:
   - Existing tests mock `requests.exceptions.ConnectionError` and assert retry behaviour. Add three new test cases mocking `httpx.RemoteProtocolError`, `httpx.ConnectError`, `httpx.ReadError`. Each should assert the wrapped fn is called 3 times before a final raise (confirming retry path was hit) — currently they will be called only once because the exception escapes the decorator immediately.
2. **Extend `_RETRYABLE`** in `plugins/jack-tar-cloud/src/generate_cloud_image.py`:
   ```python
   import httpx
   _RETRYABLE = (
       ConnectionResetError,
       ConnectionError,
       requests.exceptions.ConnectionError,
       httpx.RemoteProtocolError,
       httpx.ConnectError,
       httpx.ReadError,
   )
   ```
3. **Verify httpx is importable** — it's already an indirect dependency via `google-genai`. Confirm `requirements.txt` or `pyproject.toml` doesn't need an explicit declaration; if it does, add it.
4. **Update the decorator's docstring** to enumerate the new retryable types and clarify that "httpx connection-layer failures are retried; httpx HTTP status errors (4xx/5xx) are not".
5. **Run the test** — should now pass with all 3 retry attempts.
6. **Run the full test suite** — no regressions.

### Acceptance

- `httpx.RemoteProtocolError`, `httpx.ConnectError`, `httpx.ReadError` retry through the decorator with the existing (1, 2, 5) backoff.
- `requests.exceptions.HTTPError` (a 4xx/5xx) does NOT retry — verified by an explicit negative-case test.
- All existing tests pass.

### Cost

~30 min including TDD round.

## Phase 2 — Issue #73 (Recraft V4 default style)

**Branch:** `fix/cloud-bug-batch-72-73-74` (second commit, on top of phase 1)

### Tasks

1. **Investigate the Recraft V4 API style schema.**
   - Read https://docs.recraft.ai (or wherever the V4 style preset table lives) and confirm which top-level styles V4 accepts when `model='recraftv4'`.
   - Document the V4-vs-V3 style preset matrix in a comment in `generate_recraft_direct`.
2. **Write a failing integration test** that calls `generate_cloud_image(provider='recraft', resolution='1K')` with `RECRAFT_API_KEY` set in CI. Skip if `RECRAFT_API_KEY` not set. Currently fails with `BadRequestError`; after fix should succeed.
3. **Primary fix — change the default**: in `generate_recraft_direct`, change the parameter default from `style='realistic_image'` to `style=None`. In the request body, omit the `style` key entirely if `None`. Recraft V4's API renders without a style preset when none is supplied.
4. **Secondary fix — fall-through on style errors**: wrap the `client.images.generate(...)` call. If it raises `openai.BadRequestError` with `code: invalid_image_type` AND `FAL_KEY` is set in env, log a warning and call `generate_recraft_fal()` with the same args. Otherwise re-raise.
5. **Update the dispatcher comment** at `_dispatch_recraft` to note the fall-through behaviour.
6. **Add an explicit unit test** for the fall-through path (mock the direct call to raise the V4 style error, assert FAL is called).
7. **Update memory `feedback_engine_selection_by_constraint.md`** if needed (probably not — that memory is about selection, not internals).

### Acceptance

- `generate_cloud_image(provider='recraft', resolution='1K')` succeeds when only `RECRAFT_API_KEY` is set.
- The fall-through to FAL fires only when `BadRequestError` is the V4-style-mismatch class (confirmed via mock test).
- Existing FAL-path test still passes.
- Cost reporting unchanged ($0.04 / 1K standard).

### Cost

~45 min — the API research is the load-bearing step.

## Phase 3 — Issue #74 (Imagen Fast resolution kwarg)

**Branch:** `fix/cloud-bug-batch-72-73-74` (third commit, on top of phase 2)

### Tasks

1. **Confirm Imagen Fast's API behaviour.** The error `sampleImageSize is not adjustable` indicates Imagen Fast hardcodes the output dimension. The Google Imagen API docs may already specify which models accept `image_size` — confirm and cite in the code comment.
2. **Write a failing test** in `plugins/jack-tar-cloud/tests/`: assert that calling `generate_cloud_image(provider='google', model='imagen-4.0-fast-generate-001', resolution='1K')` does NOT pass `image_size` to the underlying API. Mock the google-genai client and assert on the call kwargs. Currently fails because the kwarg IS passed.
3. **Identify the Imagen branch** in `generate_google()` / `_generate_via_imagen()`. Add a guard:
   ```python
   IMAGEN_RESOLUTION_AWARE_MODELS = {
       'imagen-4.0-generate-001',     # Standard — supports 1K, 2K
       'imagen-4.0-ultra-generate-001',  # Ultra — supports 1K, 2K
       # imagen-4.0-fast-generate-001 NOT listed — only 1K native, no image_size kwarg
   }

   if model in IMAGEN_RESOLUTION_AWARE_MODELS:
       config_kwargs['image_size'] = _resolution_to_image_size(resolution)
   else:
       # Imagen Fast renders at native 1K only.
       if resolution and resolution != '1K':
           logger.warning(f"{model} only renders at 1K; ignoring resolution={resolution!r}")
   ```
4. **Decide on the unsupported-tier behaviour for Imagen Fast.** When operator passes `resolution='2K'` to Imagen Fast, two reasonable behaviours: (a) silently render at 1K with a warning, OR (b) raise `ProviderResolutionUnsupportedError(supported=['1K'])`. The retrospective recommends (a) — operator-friendlier, matches the documented contract that the kwarg is "the requested output tier". Implement (a).
5. **Add a test for the warning path** — call with `resolution='2K'`, assert no `image_size` reaches the API, assert a warning is logged.
6. **Update `_check_resolution_compatibility`** (the router-side helper) so it can flag this at upgrade-decision time too if needed.

### Acceptance

- `generate_cloud_image(provider='google', model='imagen-4.0-fast-generate-001', resolution='1K')` succeeds.
- Same with `resolution='2K'` succeeds, logs a warning, output is 1K.
- Imagen Standard 1K and 2K paths unchanged.
- New test asserts the request body does not include `image_size` for Imagen Fast.

### Cost

~30 min.

## Phase 4 — Issue #75 (Ollama single-flight protection)

**Branch:** `fix/ollama-single-flight-75` (parallel to the cloud branch)

### Tasks

1. **Reproduce the timeout** with the test pattern in the issue (4 parallel ThreadPoolExecutor calls). Confirm the failure mode in the test environment before fixing.
2. **Add `fcntl`-based file lock** to `plugins/jack-tar-ollama/src/generate_image.py`:
   ```python
   from contextlib import contextmanager
   from pathlib import Path
   import fcntl, time

   @contextmanager
   def _single_flight_lock(timeout_seconds: int):
       lock_path = Path.home() / '.cache' / 'jack-tar-ollama' / 'single-flight.lock'
       lock_path.parent.mkdir(parents=True, exist_ok=True)
       with open(lock_path, 'w') as lock:
           deadline = time.monotonic() + timeout_seconds
           while True:
               try:
                   fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                   break
               except BlockingIOError:
                   if time.monotonic() > deadline:
                       raise TimeoutError(
                           f"timed out waiting for Ollama single-flight lock after {timeout_seconds}s"
                       )
                   time.sleep(1)
           try:
               yield
           finally:
               fcntl.flock(lock, fcntl.LOCK_UN)
   ```
3. **Wire into the main flow** — the lock is acquired BEFORE the API call, released AFTER (whether success, error, or timeout). The existing per-call API timeout (120s default) still applies once the lock is acquired.
4. **Add a `--lock-wait-timeout SECONDS` CLI flag**, default 600 (10 minutes — covers 4-5 sequential GPU calls of ~120s).
5. **Stale-lock recovery (defensive)**: if the lock file's mtime is older than 30 minutes AND the lock acquisition is blocked, reclaim the lock. This handles the case where a previous process crashed without releasing.
6. **Write a test** that spawns 3 subprocesses in parallel hitting the same lock; assert all three succeed sequentially with appropriate gap timestamps. Mock the actual generation step so we don't need a real Ollama instance for the unit test.
7. **Update SKILL.md** at `plugins/jack-tar-ollama/skills/image/SKILL.md` to document the lock mechanism and the `--lock-wait-timeout` flag.
8. **Update CLAUDE.md** for `jack-tar-ollama` to document the constraint.

### Acceptance

- 4 parallel subprocess invocations of the skill against one Ollama instance all succeed sequentially. Total wall time ≈ 4 × per-image-gen-time, no timeouts.
- Lock released on success, error, and SIGTERM (test by sending signal mid-acquisition).
- Single-invocation behaviour unchanged.
- SKILL.md documents the mechanism.

### Cost

~60 min — fcntl + the parallel subprocess test is the heaviest part.

## Phase 5 — Version bumps + marketplace sync

This phase is **shared with the discipline-hook plan (#76)** — see [Coordinated release](#coordinated-release) below. All three plugins bump together as one release. Do NOT land version bumps from this plan independently — the marketplace manifest churn is unified.

## Coordinated release

This plan and the [discipline-hook plan](2026-05-08-discipline-hook.md) (#76) ship as a **single coordinated release** even though their work is independent. Three plugins bump together:

| Plugin | Current | Next | Driving issue(s) |
|---|---|---|---|
| `jack-tar-cloud` | 1.3.1 | **1.3.2** | #72 (httpx retry) + #73 (Recraft V4 style) + #74 (Imagen Fast resolution) |
| `jack-tar-ollama` | 1.1.0 | **1.1.1** | #75 (single-flight) |
| `jack-tar-deckhand` | 1.3.0 | **1.3.1** | #76 (discipline hook) |
| `.claude-plugin/marketplace.json` | — | sync all three | — |

**Sequencing within the release:**

1. Land all four bug-batch PRs (cloud + ollama branches) — code only, no version bumps yet.
2. Land the discipline-hook PR (deckhand branch) — code only, no version bump yet.
3. Single "release" PR bumps all three plugin manifests, syncs marketplace.json, updates root CLAUDE.md "Current Status", tags the release.

This avoids three half-released versions floating between intermediate merges and gives marketplace consumers a single coherent upgrade.

**Update root CLAUDE.md "Current Status"** in the release PR:
- Note bug-batch + discipline hook landed.
- Reference issues #72, #73, #74, #75, #76 + both plan docs.
- Update plugin version numbers in the plugin table.

## Phase 6 — CI / regression check

Final gate before any release tag:

1. Full validation workflow runs and passes — code-quality, plugin-tests (cloud + ollama matrix), integration-tests, json-validation, summary.
2. Total monorepo test count grew by ~6-8 tests (1-2 per bug, plus the Ollama parallel-subprocess test).
3. `gh pr merge --merge` (per project convention — never `--squash`).

## Risk register

| Risk | Mitigation |
|---|---|
| `httpx` not actually importable in some test environments because it's only a transitive dependency | Add explicit `import httpx` guard with a clear ImportError message; add `httpx>=0.24` to requirements if needed. |
| Recraft V4 API changes its style preset names again before this PR ships | The fall-through-to-FAL logic protects against this — even if the default style is wrong, FAL is a working escape hatch. |
| `fcntl` not available on Windows | Project doesn't currently support Windows; SKILL.md should note macOS/Linux only. If Windows support is added later, swap to `portalocker` or msvcrt-based locking. |
| The Ollama parallel-subprocess test is flaky in CI | Use deterministic mocks for the actual generation step; the test asserts only on lock acquisition order, not real GPU time. |
| Imagen Fast warning becomes noisy if users frequently pass `resolution='2K'` to it | The warning is a documented operator signal — they should switch to Imagen Standard. If actually noisy in practice, demote to debug-level after one release cycle. |

## Operator hand-off

When the PRs are ready for review, this plan should be linked from each PR description. The single PR per bug pattern (rather than one mega-PR) is deliberate — each fix is independently reviewable, mergeable, and revertable.

Estimated total work: **~3 hours** including TDD, documentation, and CI verification. A single afternoon if focused.
