# Dogfood — edit-tier smoke plan (2026-07-23, issue #143)

**Context:** pre-implementation smoke plan for the `mflux-generate-flux2-edit`
targeted-edit tier (design doc
[`docs/superpowers/plans/2026-07-23-edit-tier.md`](../plans/2026-07-23-edit-tier.md)).
Seven smokes (S1–S7) ran against the operator's Apple Silicon machine via
`mflux-generate-flux2-edit` (klein-4b, the same cached weights the existing
`mlx/flux2-klein-4b` generate path uses — no new download). All local, **$0
total spend**. S5b reused an existing on-disk Nano Banana Flash render at
zero new cloud spend. Every `[CONTINGENT-ON-Sx]` decision in the design doc
is resolved FIRM by this run — see design §8.1 for the canonical results
table; this log is the durable write-up the design's task T-S requires,
plus the raw commands/evidence backing each row.

Raw artifacts (bases, edited outputs, `.metadata.json` sidecars, and
per-run stdout/stderr logs) are in the session scratchpad under
`edit-smokes/` — not copied into the repo (binary PNGs; per the
image-review discipline hook, none were `Read` directly — verdicts below
come from subagent dispatch). Wall-clock and peak-memory figures quoted
below are read from the corresponding `edit-smokes/logs/*.log` `/usr/bin/time`
trailers.

## Results

| Smoke | Question | Result | Wall time (klein-4b, 4 steps) | Ruling |
|---|---|---|---|---|
| **S1 text-edit fidelity** | Does an edit FIX a garbled label or re-garble it? | **FAIL** | ~1m19s | **D9 FIRM: HARD-EXCLUDE.** Text-correction feedback never routes to edit. |
| **S2 guidance sweep** | Subtle vs strong edit magnitude across `--guidance` | **PASS** | ~2m30–2m42s per value (1.5/3.5/6/10) | **D10 FIRM.** Default 3.5; skill docs recommend 1.5–3.5, warn against >6. |
| **S3 determinism / seed** | Same seed ⇒ reproducible? Unseeded ⇒ replayable? | **PASS** | ~2m33–2m37s per run | Wrapper MUST generate+record a seed (F-08) — unseeded runs leave zero trace. |
| **S4 multi-reference influence** | Does a second `--image-paths` entry influence output? | **PASS (sharper risk)** | no-ref ~1m20s; with-ref ~2m06s (~1.6×) | **D11 FIRM: SHIP** with mandatory instruction-scoping + documented content-leakage failure mode. |
| **S5a ollama-produced base** | Can klein-4b-edit cleanly edit an Ollama draft? | **PASS** | ollama gen ~1m00s; edit ~1m20s | **D8 ollama class FIRM: ALLOWED.** |
| **S5b cloud-produced base** | Can klein-4b-edit edit a Nano Banana render without wrecking it? | **PASS** | n/a (reused on-disk render, $0 new spend) | **D8 cloud class FIRM: ALLOWED** (single-scenario evidence). |
| **S6 qwen-edit tier** | Confirm the 64 GB RAM gate + basic behaviour | **SKIPPED-RAM** (32 GB machine, gate refused correctly) | n/a | **D12 FIRM as designed** — RAM-gated, untested-live; wall-clock carried as a dogfood note. |
| **S7 non-square base dims** | Omit-to-inherit vs explicit differing dims | **SPLIT** | omit-to-inherit ~1m44–1m53s; explicit mismatched dims → **hang, >10 min, twice** | **F-03 wrapper-contract ruling: v1 wrapper exposes NO dims flags at all.** |

## Evidence detail

### S1 — text-edit fidelity (FAIL)

Command shape: `mflux-generate-flux2-edit --model <klein-4b repo> --image-paths
base-sign.png --prompt "change sign text to exactly NOTICE, keep everything
else" --steps 4 --guidance 3.5 --seed <fixed> --output notice-edit.png
--metadata`. Base image (`bases/base-sign.png`) carried a deliberately
garbled sign label; the instruction asked for the simplest possible
word-level correction. image-reviewer subagent dispatch on
`s1/notice-edit.png` (not `Read` directly) reported the sign now read
**"NOBTICE"** — every other region of the base (subject, background,
composition) preserved essentially unchanged, but the one thing the
instruction targeted came back wrong. Run: `edit-smokes/logs/s1-edit.log`
(~1m19s, peak MLX memory 12.44 GB).

**Ruling adopted:** D9 HARD-EXCLUDE. Text-correction feedback is never
offered to the edit channel, not even with a warning, regardless of
spatial locality (design §4.1, §4.2 `classify_edit_locality` →
`text_excluded`).

### S2 — guidance range sweep (PASS)

Fixed base + instruction + seed, `--guidance` swept 1.5 / 3.5 / 6 / 10
(`edit-smokes/logs/s2-g1.5.log` … `s2-g10.log`, ~2m30–2m42s each, peak MLX
memory ~12.45 GB throughout — guidance does not materially change memory
footprint). Reviewer dispatch across the four outputs:

- **1.5** — subtle: the targeted change is visible but restrained, high
  collateral-preservation.
- **3.5** — optimal-strong: change fully committed, boundaries crisp,
  everything outside the instruction's scope preserved. **Default.**
- **6** — degradation onset: change stronger but background/texture
  quality starting to erode (early edge of the quality cliff).
- **10** — unusable: visible noise, colour banding, and bloom artefacts.

**Ruling adopted:** D10 FIRM, default 3.5. Skill docs (`/image-edit`)
recommend the 1.5–3.5 band and warn against exceeding 6.

### S3 — determinism / seed (PASS)

Two same-seed runs (`edit-smokes/logs/s3-runB.log`, ~2m33s) diffed
pixel-for-pixel against a matching earlier run: **max pixel diff 0** —
fully deterministic given base + instruction + seed. A third,
deliberately unseeded run (`s3-runC.log`, ~2m37s) was then inspected for
seed provenance: **stdout, stderr, and the `--metadata` JSON sidecar were
all silent/null on the seed** — there is no way to recover or replay an
unseeded edit's seed after the fact. This reproduces on plain klein
**generates** too (checked against `gen-base-sign.log` /
`gen-base-sq.log`, which also carry a null `.metadata.json` even with an
explicit `--seed`) — the null-sidecar quirk (`mflux_metadata_sidecar_null`)
is a family-wide mflux 0.18 behaviour, not something specific to the edit
CLI.

**Ruling adopted:** the wrapper MUST generate-and-record an explicit seed
whenever the caller omits one, reporting it as `MFLUX_SEED_USED=<n>` on
stderr (F-08) — otherwise `edit_chain` replay (PR D) is impossible. The
catalog's `mflux_metadata_sidecar_null` quirk note is reworded (T1) to
describe the family-wide scope rather than implying it is edit-specific.

### S4 — multi-reference influence (PASS, with sharper risk than expected)

Same base + instruction, once with only the base (`s4-noref.log`,
~1m20s) and once with a second `--image-paths` entry — a stylistically
distinct reference image (`bases/ref-a2-cartoon.jpg`, a fox character) —
appended (`s4-withref.log`, ~2m06s, ~1.6× slower). Reviewer dispatch on
`s4/with-ref.png` found the reference did not just nudge palette/lighting
as intended — **the reference's own subject (the fox) was injected into
the scene**, a direct element-transfer failure mode stronger than a
simple style pull.

**Ruling adopted:** D11 FIRM: SHIP the plural `--image-paths` surface, but
the `/image-edit` skill and creative_vision anchor-usage guidance MUST
carry a mandatory instruction-scoping caveat ("match the colour palette
and lighting of the second image; do NOT add any subject from it") and
document reference-content leakage as a checked failure mode in post-edit
review.

### S5a — Ollama-produced base (PASS)

Generated a draft via the Ollama wrapper (`x/flux2-klein:4b`,
`s5a-ollama-gen.log`, ~1m00s) at `s5a/ollama-base.png`, then ran
`mflux-generate-flux2-edit` against that Ollama-produced PNG
(`s5a-edit.log`, ~1m20s, peak MLX memory 12.44 GB) with a "darken sky,
keep subject" instruction. Reviewer dispatch reported a flawless
first-try edit — no cross-backend artefacts, no re-encode banding. This
is the load-bearing base-provenance class: bridge Step 4.6 renders
Ollama first for `academic_figure` local drafts, so most real
`iterate-slide` bases will be Ollama-produced.

**Ruling adopted:** D8 ollama class FIRM: ALLOWED.

### S5b — cloud-produced base (PASS)

Reused an existing on-disk Nano Banana Flash 1K render
(`bases/cloud-B5-w-refflash.jpg`, an annotated ship diagram carrying 6
distinct text labels) at zero new cloud spend, and edited it with a
non-text, spatially-local instruction. Reviewer dispatch confirmed **all
6 labels preserved verbatim** and cloud-render crispness maintained
through the local mflux re-encode — single-scenario evidence, but a
demanding one (dense text survives).

**Ruling adopted:** D8 cloud class FIRM: ALLOWED — broader evidence
accrues in PR D dogfood.

### S6 — qwen-edit tier (SKIPPED-RAM, correctly)

The smoke machine has 32 GB RAM — below the `edit_min_ram_gb: 64` gate
for `mlx/qwen-image`. `mflux-generate-qwen-edit` weights are cached and
the entrypoint is present, but the RAM gate refused to attempt a live
run, which is the intended defensive behaviour, not a smoke failure.

**Ruling adopted:** D12 FIRM as designed — qwen-edit ships RAM-gated and
untested-live. qwen-edit wall-clock (F-11, relevant to whether the 900s
timeout is adequate) remains unmeasured; carried forward as a non-blocking
dogfood note for an operator with a ≥64 GB machine.

### S7 — non-square base dims (SPLIT)

Omit-to-inherit: edited a 1408×768 base with **no** `--width`/`--height`
flags passed — output confirmed exactly 1408×768
(`s5b-nodims.log`/`edit-smokes/s5b/nodims-edit.png`; note this smoke's
artefacts are filed under the `s5b/` scratch directory but are the S7
no-dims case — a scratch-naming quirk, not a data error — ~1m44–1m53s,
peak MLX memory 12.75 GB, slightly higher than the square-base smokes).

Explicit, differing dims: passing `--width`/`--height` that disagreed
with the base's native dimensions produced a **reproducible hang** — run
1 (`s7-mismatched.log`) and its retry (`s7-mismatched-retry.log`) both
stalled at step 1/4 for **over 10 minutes**, both were killed rather than
completing, and both surfaced a
`multiprocessing.resource_tracker` **leaked semaphore** warning
(`There appear to be 1 leaked semaphore objects to clean up at
shutdown`) on teardown — consistent with the process wedging inside
mflux's dims-handling path rather than crashing cleanly. No output file
was produced by either attempt.

**Ruling adopted:** F-03 upgraded from "only emit dims when explicit" to
a hard wrapper-contract ruling — **the v1 `edit_image.py` exposes no
`--width`/`--height` flags at all.** `parse_args` rejects them as unknown
flags; the edit always inherits the base image's dimensions. A known,
reproducible hang is not an acceptable surface even behind a warning;
this is a documented mflux non-feature to revisit on a future mflux
release, not a wrapper bug to work around.

## Cost summary

$0.00 total — all renders local mflux (S1–S5a, S7) or Ollama (the S5a
base render), plus one zero-cost reuse of an existing cloud render (S5b).
No cloud API calls were made during this smoke plan.

## Disposition

Every `[CONTINGENT-ON-Sx]` tag in the design doc (D8 ollama/cloud split,
D9 text-edit routing, D10 guidance range, D11 multi-reference, D12
qwen-edit RAM gate, F-03 dims contract) is now FIRM per the table above.
No task in the design's §11 task breakdown remains smoke-blocked; PR C
(catalog + wrapper + skill) and PR D (iterate-slide / creative_vision
integration) can proceed against these rulings without further
smoke-gated re-litigation.
