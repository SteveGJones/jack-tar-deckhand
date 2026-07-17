# Spike — Full MLX model benchmark: 10 scenarios × 2 aspects × every local model vs cloud anchors

**Date:** 2026-07-16/17 (overnight commission) · **Machine:** Apple M2 Max 32 GB · **Cloud spend:** $4.02 of a $10 authorization

## Design

- **10 scenarios**: 5 hero-class (A1 photorealistic street, A2 flat cartoon, A3 impressionist painting, A4 cinematic harbor, A5 title poster) + 5 technical-class (B1 flowchart [the 2026-07-11 baseline prompt verbatim], B2 ER diagram, B3 typographic quote card, B4 three-panel infographic, B5 annotated ship diagram). One neutral-prose prompt per scenario with double-quoted labels; seed 42; each model at its validated steps.
- **2 aspects** per scenario: 16:9 (1024×576) and 1:1 (1024×1024) — operator-directed, on the observation that several models are near-square-trained.
- **Arms**: 6 local MLX generators + 2 cloud anchors (Nano Banana Flash/Pro 1K, both aspects) + 1 documented incompatibility (the mlx-gen-only `AbstractFramework/ernie-image-turbo-8bit` export, which loads silently on upstream mflux and renders pure noise — excluded from quality rankings; see the ERNIE incident below).
- **Scoring**: blind Stage-1 (Sonnet, per-class rubrics /10, mandatory letter-by-letter transcription on text scenarios, anonymized filenames, anchors mixed in) → **adversarial Stage-2** (one Fable judge per scenario re-verifying every high/low certification and force-ranking both aspects) → compile (Stage-2 corrections over Stage-1, de-blind, aggregate).
- **Objective instruments**: per-model 512² flat-field noise probe (hf σ); wall-clock and peak MLX memory per render.

## Final leaderboard (Stage-2-corrected means; 180 scored images, 89 adversarial corrections)

| Arm | HERO | TECH | ALL | wide | square | mean rank |
|---|---|---|---|---|---|---|
| **Nano Banana Pro** (anchor, $0.134/img) | 8.05 | 8.40 | **8.22** | 8.80 | 7.65 | 2.4 |
| Nano Banana Flash (anchor, $0.067/img) | 7.00 | **8.70** | 7.85 | 8.20 | 7.50 | 3.2 |
| **ERNIE-Image-Turbo q8 on-load** | **8.75** | 5.70 | **7.22** | 7.20 | 7.25 | 3.1 |
| Z-Image-Turbo 4-bit | 8.30 | 5.80 | 7.05 | 7.25 | 6.85 | 3.4 |
| Z-Image-Turbo q8 (self-saved) | 8.00 | 5.60 | 6.80 | 6.90 | 6.70 | 4.0 |
| FLUX.2-Klein-4B 4-bit | 7.35 | 3.70 | 5.53 | 5.50 | 5.55 | 5.0 |
| FLUX.2-Klein-base-4B 8-bit | 4.20 | 2.90 | 3.55 | 3.70 | 3.40 | 7.2 |
| Qwen-Image 4-bit | 4.00 | 1.40 | 2.70 | 2.60 | 2.80 | 7.6 |

Per-scenario force-ranked tables: `per-scenario-rankings.txt` in this directory. Raw artifacts (renders, blind set + key, stage-1/2 verdicts, timings): `tmp/bench/` (gitignored).

## Speed / memory / noise

| Arm | avg s/render | peak GB | flat-field hf σ |
|---|---|---|---|
| Z-Image 4-bit | **82** | ~9 | 0.44 |
| ERNIE q8 on-load | 109 | 14–19 | 1.03 |
| klein-base 8-bit | 138 | 7–10 | **0.28** |
| Z-Image q8 | 147 | ~11 | 0.36 |
| Klein-4b (20-step text renders dominate) | 239 | ~7 | 0.33 |
| Qwen 4-bit | **1088** (square renders ~36 min each) | 27 | 4.08 |

## Headline findings

1. **ERNIE-Image-Turbo is the best local hero-image model — it beat both cloud anchors on hero mean (8.75 vs 8.05/7.00), blind.** It won A3 (both aspects) and A4-sq outright and was verbatim-perfect on the A5 poster text. Its technical-figure scores are mid-pack (structure errors, gibberish body text). It exists in the rankings only because the operator challenged a "surprisingly bad" result (see incident below).
2. **Z-Image-Turbo is the best local all-rounder for text.** It won B3 (quote card) outright in both aspects — the hardest text test — and A5-sq. The 4-bit community export and the self-saved q8 are statistically close (7.05 vs 6.80 overall); the q8's licence-cleanliness remains its main advantage, not quality.
3. **The cloud anchors keep the technical crown** (8.40–8.70 TECH vs 5.80 best-local) — label fidelity + structure at once is still where the frontier gap is widest. But local hero images are now genuinely competitive.
4. **Klein-4b underperformed its history** (3.70 TECH vs its 9/9 dogfood pedigree): this suite used neutral prompts, not the exact-spellings dialect that rescues Klein — dialect sensitivity is a real deployment consideration, not a benchmark artifact.
5. **Klein-base-8bit (non-distilled) collapses on text** ("PENIJOR", "Jock Tor") while being decent painterly — ran at default guidance; a guidance sweep is future work before final judgment.
6. **Qwen 4-bit confirmed unusable** (2.70 overall, flat-field σ 4.08, 36-min square renders at 27 GB) — consistent with the per-step q4 compounding diagnosis (2026-07-16).
7. **Aspect findings**: most arms are aspect-stable (±0.3); Nano Banana Pro drops −1.15 on square — partly because **several cloud "1:1" renders came back 16:9** (the `aspect_ratio` param appears not to bind on the Gemini `generate_content` path; Stage-2 judges penalized the wrong-aspect files in-bucket). Benchmark caveat + pipeline bug lead worth filing.
8. **The adversarial stage changed 89 of 180 scores** and caught: a false "all lines correct" 10/10 (actual 3/10 — missing label + three mispointed leader lines), a Stage-1 review describing a different image (1→6), inflations and unfair harshness in both directions, systematically skipped noise renders, and refuted/confirmed crow's-foot notation by pixel-level prong counting. **F15/F16 fully vindicated: single-stage review is not certification.**

## The ERNIE incident (methodology finding as important as the rankings)

The fork-saved `AbstractFramework/ernie-image-turbo-8bit` export loads without error on upstream mflux 0.18.0 and renders pure noise (hf σ 52.9; a "load test" checking only exit-code+file-exists passed it). Root cause (researched, ~95% confidence): mlx-gen's ERNIE port (May 25) and upstream's (PR #417, June 6) wereindependently authored with different module trees; upstream's loader accepts the foreign checkpoint via its metadata stamp and `strict=False` silently drops every mismatched weight (entire text encoder + the AdaLN projection). The model card says "Requires mlx-gen ≥ 0.18.5" — it is fork-only by construction. The fair arm (baidu base, on-load `-q 8`, the upstream README's canonical path) verified clean and went on to win the hero class. **Rules adopted: pixel-check every load test; "loads" ≠ "works"; on-load or self-saved quantization from source bases is the standard acquisition path** (matches the AbstractFramework supply-chain research verdict: use-with-verification, bus factor ≈ 1, in `research/mlx/sub-research/`).

## Recommendations (catalog/pipeline follow-ups — separate issues)

1. **Add `mlx/ernie-image-turbo` to the catalog** (baidu base + on-load q8; or `mflux-save` a local q8 for faster loads) as the preferred **hero/full_bleed draft model**; keep z-image/klein for text-bearing drafts. Smoke → catalog entry per the #124 playbook.
2. **Prefer z-image for words-on-page/quote-card style figures** (B3 winner both aspects).
3. Retire `mlx/qwen-image` from `local_draft` consideration on ≤32 GB (already noted in catalog; benchmark confirms).
4. **File the aspect-ratio bug** on the cloud path (`aspect_ratio` not binding for `generate_content` models) — it silently affects every 16:9 deck render routed to Nano Banana.
5. Drop `AbstractFramework` exports except empirically-gated ones (klein-base works; ERNIE doesn't); never adopt without a pixel-checked render. Bonsai: watchlist only (fork-runtime-only; typographic disintegration per verification research).
6. Klein-base guidance sweep + SeedVR2 upscale pass evaluation remain queued as the next spikes.

## Prior work this builds on
- `docs/spikes/2026-07-16-ollama-mlx-equivalence/` (runtime equivalence)
- `research/mlx/` + `research/mlx/sub-research/` (model landscape, AbstractFramework trust, Bonsai verification)
- 2026-07-11 Ollama model-comparison dogfood (baseline prompt + F15/F16 protocol)
