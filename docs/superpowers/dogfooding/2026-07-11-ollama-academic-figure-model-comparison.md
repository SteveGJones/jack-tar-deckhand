# Dogfood — local Ollama model comparison for academic_figure (2026-07-11)

**Context:** first live exercise of the paperbanana local-first tier
(ADR v2 §8.5). Five renders of the same academic figure — the Jack-Tar
Deckhand pipeline architecture — same 1024×576, on the operator's
Apple Silicon machine via `jack-tar-ollama/src/generate_image.py`.
Renders 1–4 used the identical dense-prose prompt (built by
`paperbanana_dispatch._build_local_prompt`); render 5 was the
critique-loop iteration — the reviewer's findings fed back as an
F11-simplified label-list prompt. All reviews by the image-reviewer
subagent (same agent across all five, so comparisons are within one
context). Total spend: $0.00.

## Results

| Rank | Model | Steps | Prompt | Wall time | Labels | Structure | Verdict |
|---|---|---|---|---|---|---|---|
| **1** | `x/flux2-klein:9b` (iter 2) | 8 | **simplified label list** | 1m18s | **9/9 correctly spelled** | exactly as requested (5-box flow, 3 tiers, Critic loop) | **PASS** — production-usable draft |
| 2 | `x/flux2-klein:9b` (iter 1) | 8 | dense prose | 1m22s | title CORRECT, ~85% legible | pipeline narrative ✓, muted academic palette | REFINE (9/10) |
| 3 | `x/flux2-klein:4b` | 20 | dense prose | ~8 min | title garbled, ~70% legible | pipeline narrative ✓ | REFINE (6/10) |
| 4 | `x/flux2-klein:4b` | 8 | dense prose | ~3 min¹ | nonsense | abstract circles | FAIL (2/10) |
| 5 | `x/z-image-turbo:fp8` | 8 | dense prose | **45s** | 1/6 legible | **wrong paradigm** — photorealistic office/people grid, no diagram semantics | FAIL (1/10) |

¹ includes first model load; not directly comparable.

Renders in `plugins/jack-tar-deckhand/tmp/paperbanana-local-test/`
(gitignored; regenerate with the prompt recorded below).

## Findings

- **F1 — model size, not step count, is the text-fidelity lever for
  FLUX.2 Klein.** 9b at 8 steps beats 4b at 20 steps on label fidelity
  (title goes from unsalvageable to correct) in ~1/6 the wall time.
  Extra steps improved 4b's composition, never its text.
  → `detect_local_backend()` now prefers the largest parameter variant
  within a family (`_tag_param_size`); `local-config.json` pins
  `academic_figure_model: x/flux2-klein:9b`.
- **F2 — Z-Image Turbo is unsuitable for technical schematics.** Its
  photorealistic priors override the diagram intent entirely (renders
  a stock-photo team grid), and its text-rendering reputation did not
  hold for multi-label technical figures. It stays LAST in
  `_LOCAL_IMAGE_MODEL_PREFERENCE` — kept only as a
  better-than-nothing draft fallback when it is the sole image model;
  the F10 operator gate catches its output before any spend.
- **F3 — the text ceiling is prompt-shaped, not just model-shaped.**
  With dense prose, even 9b garbles descriptive text (~85% label
  fidelity, flavour text corrupt). With a **simplified label list**
  (≤8 short quoted labels, no prose), 9b rendered **9/9 labels
  correctly spelled** — the prompt's prose budget was competing with
  the text-rendering budget. For figures needing >8 labels or body
  text, escalate to paperbanana / Nano Banana.
- **F4 — the 8-step default in `generate_image.py` stands.** 20 steps
  costs ~2.5× for no text gain on 4b; 9b needs only 8 steps. No
  model-aware step override added — evidence didn't justify it.
- **F5 — the free critique loop is validated and codified.** One
  iteration of reviewer-feedback → F11 radical simplification →
  re-render took 9b from REFINE to PASS at $0. The imagegen-bridge
  local branch (Step 4.6.2) runs the loop with label-list
  simplification on text-corruption verdicts; budget per gate visit:
  **3 renders in ladder mode, 5 in local_only mode** (operator
  decision 2026-07-11 — parity with the creative_vision ollama cap;
  ~7 min wall at Klein 9b's measured ~80s/render). In local_only the
  cap is a **checkpoint, not a wall**: paid tiers do not exist, so
  exhausting the budget surfaces best-so-far at the gate where the
  operator can loop again free, accept, or hand-edit. Plateau
  (2 consecutive non-improving renders) stops a budget early;
  iteration cannot rescue paradigm drift (Z-Image's people-grid).
- **F6 — F11 empirical confirmation, inverse direction.** Removing
  ~300 words of prose flipped the verdict from REFINE to PASS —
  the strongest evidence yet that over-specification, not
  under-specification, is the dominant local-model failure mode for
  text-bearing figures.

## Round 2 — full critique loops on the deck-schema figure (same day)

Second exercise: the deck object schema (Deck → Slide → six strategy-type
boxes + "(Local only)" under Academic Figure; **9 labels, deliberately one
past the observed ceiling**), run through the full local-only critique loop
on all three models. Renders in `tmp/paperbanana-local-test/schema-*.png`.

| Model | Loop history (score /9 per iteration) | Final | Renders used |
|---|---|---|---|
| `x/flux2-klein:9b` | 6/9 → 8/9¹ ("Figture") → 8/9 ("Acaademic Figture" — negative directive backfired) → 7/9 (label fixed, Slide dropped, "Blsen" stray) → **8/9 best-so-far** (all 9 strings letter-perfect; ghost duplicate line + 1 reversed arrowhead) | `schema-9b-iter5.png` (budget exhausted, operator gate: accept / loop again / hand-edit) | 5/5 |
| `x/flux2-klein:4b` | Haiku in-loop scores 5/9 → 7/9 → 2/9 → 7/9 → "9/9 PASS"; **Sonnet char-level audit corrected the certified renders to iter2 5/9, iter4 3/9, iter5 5/9** — no PASS. True best: iter5 (only 4b render with correct 3-level topology) | `schema-4b-iter5.png` (5/9, NOT certified) | 5/5 |
| `x/z-image-turbo:fp8` | 2/9 → 1/9 — **plateau called, retired for schemas** | best-so-far `schema-zimage-iter1.png` | 2/5 |

¹ The image-reviewer certified 9b iter2 as 9/9; **the operator caught
"Academic Figture" at the gate** — actual score 8/9. See F12 below.

Findings (continue numbering from round 1):

- **F7 — the annotation pattern beats the label ceiling.** Demoting the
  9th element ("Local only") from a full label box to a small annotation
  tag took 9b from 6/9 to 9/9 in one iteration. Canonical pattern for
  schema figures: **≤8 full label boxes; extras as annotations/badges;
  two rows of three for six siblings.**
- **F8 — the step curve INVERTS past ~20 on Klein 4b.** 8→20 steps:
  +22pp. 20→30 steps: −56pp (labels dropped wholesale). Never retry a
  failed render by raising steps past 20; switch lever (annotation,
  spellings lock) or model size instead.
- **F9 — an exact-spellings lock rescues 4b.** Enumerating labels with
  "spelled exactly, no variants" plus naming the observed miss ("Full
  Render", NOT "Full Rendered"; "Slide" mandatory) took 4b from 7/9 to
  9/9 on its final render. 4b CAN produce publication-grade schema
  figures — it needs 20 steps + annotation pattern + spellings lock,
  where 9b needs only the annotation pattern at 8 steps.
- **F10 — "Background" label vs "white background" style directive
  collide.** The label vanished in all three models' iteration 1 while
  the style block said "white background"; it returned in every render
  where either the word was de-collided ("plain white canvas") or the
  label budget dropped to 8. Prompt template rule: never repeat a
  label word inside the style block.
- **F11 — Z-Image Turbo is retired for schema/academic figures.** Label
  lists fix its paradigm drift (it stayed flat-vector) but text
  fidelity went 2/9 → 1/9 across the loop, with the root label
  garbled. Its family stays LAST in `_LOCAL_IMAGE_MODEL_PREFERENCE`.
- **F12 (this exercise) — the image-reviewer certified a misspelling as
  correct.** The Haiku reviewer transcribed 9b iter2's "Academic
  **Figture**" as "Academic Figure" and scored it 9/9; the operator
  caught it at the gate. Consequences: (a) reviewer verdicts on
  text-bearing figures are advisory — the operator gate is the
  certification step, exactly per the root-CLAUDE.md F12 stance; (b)
  academic-figure reviews should adopt the `expected_text_content`
  verbatim-transcription contract from superpower-bridge Findings
  #19/#20, and character-level checks deserve a second reviewer at
  higher visual accuracy (general-purpose Sonnet) when a render is
  about to be certified PASS. Tracked in issue #119.
- **F13 — negative directives seed the failure token.** Iter3's prompt
  said the label is "Academic Figure", NOT "Figture" — and the render
  produced "Figture" again (plus a new "Acaademic"). Diffusion models
  don't process negation; naming the misspelling hands it the token.
  Prompt rule: corrections must be stated positively only. (Same
  mechanism as the F11 note on stacking negative directives.)
- **F14 — letter-by-letter spell-outs can transcribe literally.**
  Iter5's "spelled A-c-a-d-e-m-i-c F-i-g-u-r-e" fixed the target label
  but leaked a ghost duplicate line "Acade-mic Figure" into the box.
  Prefer "the box contains exactly the two words 'Academic Figure' and
  nothing else" — the per-box exact-text constraint alone (which also
  eliminated iter4's "Blsen" stray).
- **F15 — Haiku vs Sonnet review protocol for certification.** After
  the operator caught the Haiku miss (F12), iterations 3–5 were
  reviewed by a general-purpose Sonnet agent under an explicit
  skeptical letter-by-letter protocol; it caught every defect the
  loop then chased ("Acaademic", "Blsen", the leak, a reversed
  arrowhead). Cadence recommendation: Haiku for in-loop refine
  verdicts, Sonnet char-level pass before any PASS certification,
  operator gate as final certification always.
- **F16 — full audit: every Haiku certification in this batch
  over-scored, in the same direction.** Audited: 4b-iter5 "9/9" →
  actual 5/9 ("Dedk", "Backgroond", "Acadiric", annotation missing a
  paren and under the wrong box, reversed arrow); 4b-iter2 "7/9" →
  5/9 (Slide box MISSING though certified "all 9 present"; annotation
  rendered as a bogus tree node); 4b-iter4 "7/9" → 3/9 (five corrupted
  labels certified "clean": "Deek", "Backgnound", "Rended", "Bleeed",
  "Acadimic"); plus the original 9b "Figture" miss. Failure mode is
  consistent: word-shaped tokens with 1–3 corrupted characters pass a
  shape-level read, and missing structural elements get counted as
  present. **Corrected cross-loop ranking: 9b-iter5 (8/9, structure
  correct) ≫ 4b best (iter5, 5/9).** Haiku review is usable for gross
  layout/composition verdicts only; character fidelity and element
  inventory require letter-by-letter transcription against an explicit
  checklist (Sonnet-class), and round-1 scores in this log that were
  not re-audited should be read as shape-level, not character-level.

## Baseline for future model evaluations

Any new local model (MLX backends included) should be tested against
this same brief and must beat Klein 9b on: (1) title legibility,
(2) tier-label fidelity, (3) structure recognition (pipeline
narrative, not scene drift). Candidates worth testing when available:
Qwen-Image-family, newer FLUX variants.

## Iteration-2 prompt (verbatim — the PASS render)

> Academic figure for a research paper: architecture diagram of a
> presentation-engineering pipeline. A horizontal flowchart of five
> labelled boxes connected by left-to-right arrows, labelled exactly:
> "Conductor", "Narrative", "Images", "Assembly", "QA". Below the
> "Images" box, three small stacked boxes labelled exactly: "Ollama
> free", "Flash", "Pro". A curved arrow returns from a box labelled
> "Critic" back to the "Images" box. Style: clean flat vector diagram,
> white background, thin precise lines, correctly spelled labels, muted
> professional colour palette, generous whitespace, 16:9 composition.
> No photorealism, no people, no decorative clutter, no watermark.

## Iteration-1 prompt (verbatim, renders 1–4)

> Academic figure for a research paper: Jack-Tar Deckhand pipeline
> architecture. The figure must faithfully depict this methodology:
> Jack-Tar Deckhand is a multi-stage presentation-engineering pipeline.
> A Deck Conductor orchestrates sequential stages: brand profiling,
> style derivation, narrative architecture, per-slide
> rendering-strategy classification, SmartArt selection, image
> generation, deck assembly, and automated quality assurance. Image
> generation routes each slide to one of three backends by cost tier: a
> free local Ollama draft tier, a mid-price cloud tier (Gemini Flash),
> and a premium cloud tier (Gemini Pro). A Critic agent reviews every
> rendered image and either accepts it or escalates to the next tier,
> with a human operator gate at every free-to-paid transition. Style:
> clean publication-quality academic paper figure, flat vector diagram
> aesthetic, white background, thin precise lines, clearly labelled
> components with correctly spelled text, muted professional colour
> palette, generous whitespace, 16:9 composition. No photorealism, no
> decorative clutter, no watermark.

## See also

- ADR: `docs/architecture/paperbanana-integration-v2.md` §8.5
- Dispatch module: `plugins/jack-tar-deckhand/src/paperbanana_dispatch.py`
- Bridge branch: `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md` Step 4.6
