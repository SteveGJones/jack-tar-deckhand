---
name: ollama-image
description: Generate images using local Ollama models with optional iterative refinement. Accepts a text prompt or prompt file, generates via Ollama, optionally reviews and refines using vision, saves to a specified path, and returns the file path.
argument-hint: "a description of the image" [--model MODEL] [--output PATH] [--prompt-file FILE] [--iterations N] [--width INT] [--height INT] [--steps INT] [--seed INT]
allowed-tools: Bash(python *), Bash(curl *), Bash(ollama *), Read, Glob
---

# /ollama-image

Generate an image and report the file path. When `--iterations` is greater than 1, run an iterative review-refine loop using your native vision to evaluate each image and improve the prompt between iterations.

Consult the `ollama-image-expert` agent for all domain knowledge: scoring rubric, prompt engineering strategies, mutation rules, and convergence criteria.

## Parse Arguments

Parse `$ARGUMENTS` for:
- **Prompt**: The quoted text description, OR use `--prompt-file PATH` to read a prompt from a file
- **--model MODEL**: Ollama model to use (must be an image generation model with `x/` prefix)
- **--output PATH**: Where to save the image (default: `output/YYYYMMDD-HHMMSS.png`)
- **--iterations N**: Max refinement iterations (default: 1 = one-shot, no review)
- **--width INT**: Image width (default: 1024)
- **--height INT**: Image height (default: 1024)
- **--steps INT**: Inference steps (default: 8 for z-image-turbo, 20 for flux models)
- **--seed INT**: Seed for reproducibility (optional)

If `--prompt-file` is specified, read the file contents as the prompt using the Read tool.

If no prompt and no `--prompt-file` is provided, stop and tell the user to provide a prompt.

Save the original prompt — you will need it if a full rewrite is required during refinement.

## Discover Available Models

If no `--model` is specified, or to validate the user's model choice, discover available image generation models:

```bash
ollama list
```

Filter the output for models with the `x/` prefix — these are image generation models. Examples: `x/z-image-turbo`, `x/flux2-klein`.

- If `--model` is specified: verify it appears in the list. If not, tell the user it's not available, show them the available `x/` models, and suggest `ollama pull MODEL`.
- If `--model` is NOT specified: default to `x/z-image-turbo` if available. If not, use the first available `x/` model. If NO `x/` models are available, tell the user to pull one: `ollama pull x/z-image-turbo`.

## Set Model-Appropriate Defaults

If `--steps` was not explicitly provided, set defaults based on the model:
- `x/z-image-turbo`: 8 steps (timeout auto-set to 120s)
- `x/flux2-klein` or other flux models: 20 steps (timeout auto-set to 600s)

The helper script auto-detects timeouts per model. You do NOT need to pass `--timeout` unless the user explicitly requests it.

## Verify Ollama Is Running

```bash
curl -s http://localhost:11434/api/tags
```

If this fails, tell the user: "Ollama is not running. Start it with: `ollama serve`" and stop.

## One-Shot Mode (--iterations 1 or omitted)

If iterations is 1 (the default), run a single generation with no review:

1. Run the helper script:
   ```bash
   python src/generate_image.py --prompt "THE PROMPT" --model "THE MODEL" --output "THE PATH" --width WIDTH --height HEIGHT --steps STEPS [--seed SEED]
   ```
2. If exit code is 0: read the output path from stdout.
3. If exit code is non-zero: read stderr and report the error.
4. Report the file path, model, and prompt. Done.

## Iterative Mode (--iterations > 1)

Run the generate-review-refine loop. Track iteration state as you go:
- Iteration history: list of (iteration number, prompt used, image path, dimension scores, weighted score)
- Best iteration: the one with the highest weighted score so far
- Current prompt: starts as the user's prompt, refined each iteration

### For each iteration (1 to max iterations):

#### Step 1: Generate

Determine the output path for this iteration. If `--output` was specified, use it for iteration 1 and append `-iter-N` for subsequent iterations (e.g., `fox.png`, `fox-iter-2.png`, `fox-iter-3.png`). If no `--output`, use `output/YYYYMMDD-HHMMSS-iter-N.png`.

Run the helper script with the current prompt:
```bash
python src/generate_image.py --prompt "CURRENT PROMPT" --model "MODEL" --output "ITER PATH" --width WIDTH --height HEIGHT --steps STEPS
```

If the helper fails, report the error and stop.

#### Step 2: Review

Read the generated image using the Read tool — you can see it natively.

Evaluate the image against the **original user prompt** (not the refined prompt) using the scoring rubric from the `ollama-image-expert` agent. Score each of the 6 dimensions (1-10):

1. Subject Accuracy (30%)
2. Style Adherence (20%)
3. Composition (15%)
4. Technical Quality (15%)
5. Color and Lighting (10%)
6. Overall Holistic (10%)

Calculate the weighted score. Be honest and critical.

Record this iteration in your history.

#### Step 3: Decide

Check the convergence rules from the `ollama-image-expert` agent, in this priority order:

1. **Accept**: weighted score >= 7.5 → stop, report this image
2. **Max iterations**: this is the last iteration → stop, report the best image from history
3. **Plateau**: score has not improved by > 0.3 for the last 2 consecutive iterations → stop early, report best
4. **Oscillation**: scores bouncing with no upward trend → stop early, report best
5. **Regression**: current score is lower than the best prior → revert to the best prior prompt and apply minor additive changes only (do NOT continue with the degraded prompt)
6. **Continue**: none of the above → proceed to refinement

#### Step 4: Refine

Identify the weakest-scoring dimension. Apply the mutation strategy from the `ollama-image-expert` agent based on the current score band:

- **7.0-7.9 (Additive)**: Add lighting keywords, camera specs, mood descriptors. Do not restructure.
- **5.0-6.9 (Structural)**: Reorder elements, add/remove descriptive blocks, clarify spatial relationships.
- **1.0-4.9 (Rewrite)**: Start fresh from the original user prompt. Use iteration history to avoid repeating failed approaches.

Apply model-specific prompt structure from the agent (Z-Image Turbo structure vs FLUX spatial hierarchy).

The refined prompt becomes the current prompt for the next iteration. Loop back to Step 1.

## Report Result

On completion (whether one-shot or iterative), report:

**For one-shot mode:**
- The absolute file path to the generated image
- The model used
- The prompt used

**For iterative mode:**
- The absolute file path to the **best-scoring** image (not necessarily the last one)
- Its weighted score and dimension breakdown
- The model used
- The prompt that produced the best image
- A brief iteration summary: how many iterations ran, scores per iteration, why iteration stopped (accepted, plateau, oscillation, max reached)

Do not ask follow-up questions. Do not offer to continue refining. Report and stop.
