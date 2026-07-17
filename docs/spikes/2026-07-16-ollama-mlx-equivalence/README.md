# Spike — Ollama ↔ MLX (mflux) like-for-like equivalence (issue #124, Phase 5)

**Date:** 2026-07-16 · **Operator machine:** Apple M2 Max, 32 GB · **Spend:** $0.00

## Question

Is the MLX (mflux) local backend equivalent to or better than Ollama on a
like-for-like basis for the `academic_figure` draft tier — same models, same
prompt, same scoring protocol as the 2026-07-11 baseline dogfood?

## Method

- **Prompt:** the 2026-07-11 dogfood **iteration-2 PASS prompt, verbatim**
  (9 labelled elements: Conductor / Narrative / Images / Assembly / QA /
  Ollama free / Flash / Pro / Critic; 5-box flow + 3 stacked + Critic
  return arrow). Klein 9b on Ollama scored PASS (9/9 labels) on this exact
  prompt — the standing baseline.
- **Matrix (5 cells × 2 seeds, 1024×576):**

| Cell | Runtime | Model | Steps | Role |
|---|---|---|---|---|
| A | Ollama | `x/flux2-klein:9b` | 8 | reference champion (9B has no commercial mflux counterpart — gated/non-commercial on HF) |
| B | Ollama | `x/flux2-klein:4b` | 20 | like-for-like pair 1 |
| C | mflux | `mlx/flux2-klein-4b` (Runpod 4-bit) | 20 | like-for-like pair 1 |
| D | Ollama | `x/z-image-turbo:fp8` | 8 | like-for-like pair 2 |
| E | mflux | `mlx/z-image-turbo` (filipstrand 4-bit) | 9 (family-native) | like-for-like pair 2 |

- **Seeds 42 and 7 per cell.** Seeds are NOT comparable across runtimes
  (different samplers/RNG); two seeds guard against single-draw variance
  within each cell, not for cross-runtime pairing.
- **Steps are family-idiomatic, not forced-identical:** 4b needs 20 steps
  (dogfood F9); z-image is 9-step distilled on mflux, 8 on Ollama. This is a
  deliberate "each runtime at its best like-for-like settings" comparison,
  not a parameter-identical one — the pipeline always runs each backend at
  its catalogued settings.
- **Scoring:** F15/F16 protocol — general-purpose **Sonnet** reviewer (not
  Haiku; F16 showed Haiku over-scores character fidelity), skeptical
  letter-by-letter transcription against the explicit 9-label checklist +
  structure inventory (5-box flow, 3 stacked under Images, Critic return
  arrow, arrow directions). Score /9 labels + structure verdict.
- **Blind review:** renders are copied to anonymised names
  (`render-<hash>.png`) before review dispatch; reviewers never see
  runtime/model/cell identity. Key held in `blind-key.csv` (committed after
  reviews complete).
- **Objective noise probe:** per-cell 512² flat-white render; high-frequency
  σ measured as std of (image − Gaussian-blur(4)). Instrument validated in
  the 2026-07-16 qwen diagnostics.
- **Wall-clock:** per-render, recorded by the driver script
  (`tmp/equiv-spike/run-matrix.sh`). Ollama renders benefit from a warm
  server after the first call of each model; mflux cold-loads per call —
  timings are reported as observed (pipeline-realistic), with the caveat
  noted.

## Results

### Label fidelity (blind Sonnet letter-by-letter, /9) + verdict

| Cell | Runtime | Model | Seed 42 | Seed 7 | Cell mean | Structure (both seeds) |
|---|---|---|---|---|---|---|
| A | Ollama | klein 9b @8 | **9/9** REFINE | **9/9** REFINE | **9.0** | FAIL (stack misplaced; return arrow wrong; ghost "Tiric"/"Flro") |
| B | Ollama | klein 4b @20 | 5/9 FAIL | 6/9 FAIL | 5.5 | FAIL (fused stack; duplicated corrupt Critic) |
| C | mflux | klein 4B @20 | 7/9 REFINE | 5/9 FAIL | 6.0 | FAIL (merged stack boxes; no Critic box) |
| D | Ollama | z-image fp8 @8 | 7/9 FAIL | 7/9 REFINE | 7.0 | FAIL (stack wrong parent; ghost "Proo"; dup box) |
| E | mflux | z-image 4-bit @9 | 8/9 REFINE | 8/9 REFINE | **8.0** | FAIL (stack under Narrative; forward Critic arc) |

Corrupted-token examples caught by the protocol: "Condlurtor", "Assowbly",
"Assowilly", "Asssnmly", "CA", "Crtieic", "Conadiior", "Ollaima free" —
the 1–3-character word-shaped corruption mode F16 predicts.

### Flat-field noise probe (512², hf σ = std(image − blur(4)); lower is better)

| Cell | hf σ | Mean (target 255) |
|---|---|---|
| A Ollama klein 9b | 0.34 | 253.0 |
| B Ollama klein 4b | 0.34 | 254.3 |
| C mflux klein 4B | 0.33 | 252.7 |
| D Ollama z-image | 0.24 | 252.2 |
| E mflux z-image | 0.44 | 254.2 |

**Equivalent across the board** (0.24–0.44) — no runtime-side noise pathology
for these families (contrast: mflux qwen 4-bit measured 4.14–7.36 in the
2026-07-16 diagnostics).

### Wall-clock (1024×576 diagram renders; mflux = clean re-timings after Ollama unload)

| Cell | Seed 42 | Seed 7 | Notes |
|---|---|---|---|
| A Ollama klein 9b @8 | 253 s¹ | 186 s | ¹ includes model load |
| B Ollama klein 4b @20 | 123 s | 140 s | warm server |
| C mflux klein 4B @20 | 121 s | 113 s | cold-load per call INCLUDED — still ties/beats B |
| D Ollama z-image @8 | 48 s | 50 s | warm server |
| E mflux z-image @9 | 69 s | 69 s | cold-load included; 1 extra step |

### Additional findings

1. **Keep-alive residency contamination (operator-caught).** The first pass
   ran mflux cells while the Ollama server still held 24.8 GB resident
   (`keep_alive` ≈ 5 min) — mflux klein timing inflated 140 s vs 117 s clean
   on a 32 GB machine. Sequential execution is NOT sufficient isolation
   when one runtime is a keep-alive server; the nested single-flight lock
   cannot see server-resident memory. **Horizon-2 implication: the bridge
   should issue `keep_alive: 0` unloads when switching local providers.**
2. **mflux is pixel-deterministic per seed.** All four contaminated-run
   renders were pixel-identical (max|diff| = 0.0) to their clean re-runs —
   memory pressure affects speed only, and seeds fully reproduce.
3. **Steps caveat on historical comparisons.** The 2026-07-15 smoke's
   "klein 9/10 at 35 s" ran at the registry's family-native 4 steps (the
   wrapper's CLI default), not the bridge's render_steps 20 — wall-clock
   claims must always state steps.

## Verdict

**MLX (mflux) is equivalent-or-better than Ollama like-for-like, blind-scored.**

- **Klein 4B pair:** 6.0 vs 5.5 mean labels — tie within n=2 noise;
  wall-clock tie (117 s vs 132 s avg, mflux's including cold-load).
- **Z-image pair:** 8.0 vs 7.0 — mflux nominally +1 on BOTH seeds and the
  lowest-variance cell in the matrix (8/9, 8/9). Ollama z-image is faster
  (49 s vs 69 s, warm server + one fewer step).
- **Klein 9b (Ollama-only) remains the label champion** — 9/9 on both
  blind seeds, replicating the 2026-07-11 baseline. Its mflux counterpart
  is gated/non-commercial, so **the strongest argument for keeping Ollama
  is 9b exclusivity, not runtime quality**.
- **Structure fails single-shot everywhere** — all 10 renders including
  both 9b seeds (stack placement, Critic return arrow, ghost tokens). The
  2026-07-11 PASS was critique-loop-assisted (iteration 2); the loop is
  load-bearing for this figure class regardless of runtime.

**Recommendations:** (1) keep the dual-provider arrangement as shipped —
Ollama-first while klein-9b is the best label model and Ollama-exclusive;
(2) within the z-image family, prefer the mflux variant when both are
present (consistent +1, deterministic, no daemon) — candidate follow-up for
cross-provider preference in `role_defaults`; (3) Horizon 2 (full Ollama
replacement) is VIABLE on quality evidence for 4b-class models but costs
access to klein 9b — defer until a commercial-usable 9b-class MLX model
appears; (4) add the provider-switch unload step (finding 1) to the bridge.

**Raw artifacts:** `tmp/equiv-spike/` (gitignored) — renders, blind copies +
key, timings.csv, driver scripts. Blind key: A=k3/p8, B=w1/d6, C=m9/t2,
D=r5/h7, E=b4/x0.

## Prior evidence this spike builds on

- 2026-07-11 dogfood (baseline + F1–F16):
  `docs/superpowers/dogfooding/2026-07-11-ollama-academic-figure-model-comparison.md`
- 2026-07-15/16 MLX smoke matrix + qwen isolation series: PR #132 comments,
  `mlx/*` catalog entry notes
- z-image variant-specificity finding (Ollama retirement does not carry to
  mflux): catalog `mlx/z-image-turbo` notes, commit `c643008`
