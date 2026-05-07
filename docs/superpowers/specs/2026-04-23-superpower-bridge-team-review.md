# Superpower Bridge Spec — Team Review Synthesis

**Date:** 2026-04-23
**Reviewed spec:** [2026-04-22-superpower-bridge-design.md](2026-04-22-superpower-bridge-design.md) (incorporates Spike 1 & 2 findings)
**Review panel:** 6 specialist agents dispatched in parallel — critical-goal-reviewer, solution-architect, business-solution-architect (BSA methodology), ai-persona-architect, security-architect, ai-test-engineer.

## Overall verdict

**REQUEST CHANGES before writing the implementation plan.** The spec has strong bones and the spike findings are correctly folded in, but six cross-cutting themes surfaced that need resolution first. None requires another spike. All are spec edits.

## Cross-cutting themes

### 1. Analyser input: parse the .pptx, not the JS build script

**Raised by:** critical-goal, solution-architect, security, test engineer (4 of 6).

The open question in the risk register has a consensus answer: **parse the .pptx directly via python-pptx; use the build script only as a supplemental hint source for unmarked slides.**

Reasons converged across reviewers:
- OOXML is a stable schema; LLM-generated JavaScript is not. The same intent produces different code across model versions.
- Failure mode of a heuristic JS parser is silent under-matching, not a crash — the enrichment menu quietly shrinks.
- Shape names, coordinates, text content are all in OOXML as `<p:cNvPr @name>`, `<a:xfrm>`, `<a:t>`.
- Security (C2): parsing-not-executing is a hard requirement. A .pptx-first path has no `build.js` execution surface at all.
- Slide addressing becomes robust against user iteration between Phase 2 and Phase 3.

**Action:** Invert Section 3.1. Make .pptx parsing primary. Demote build-script use to optional hint-layering for unmarked-slide heuristics.

### 2. Text-scan fallback is load-bearing and currently missing

**Raised by:** critical-goal, test engineer, ai-persona-architect.

Spike 1 recommended a fallback: when OOXML shape names are absent (as in Variants B & C), scan slide text for `(IMAGE|SMARTART|BG):<slug>` strings. The on-slide text labels are always present because the brief tells /pptx to render them. The spec never folded this in.

Without the fallback, any brief that drifts (forgets `objectName`, uses wrong property name, etc.) degrades to zero adherence and the bridge becomes unusable without the user noticing.

**Action:** Add text-scan as a first-class second-tier path in Section 3.1. Make it explicit in the In Scope table.

### 3. AI Persona definitions missing

**Raised by:** BSA methodology, ai-persona-architect (2 of 6, both specialist lenses).

The bridge introduces AI agents but has no 19-section definitions. Methodology says this blocks readiness scorecard sign-off. Specifically:

- **`bridge-brief` is a persona.** Needs formal definition — proposed "Narrative Brief Architect", Invoker authority, Tier 1 risk, Sonnet-default.
- **`enrich-deck` is orchestration, not a single persona.** It invokes existing Prompt Engineer and Image Reviewer, plus a new **Enrichment Cohesion Reviewer** persona for the final visual review step (analogous to Image Reviewer but deck-level). Haiku-default, Tier 1.
- **Tripartite accountability** (Service Owner + SOP Owner + AI RM) is unassigned for both.
- **An alternative** worth considering: extend the existing `narrative-architect` skill with a "brief mode" output target rather than defining a new persona. Less scope expansion.

**Action:** Before writing the plan, decide persona boundaries and draft the 19-section definitions (or explicit "this is not a persona" statements). Update `.bsa/models/jack-tar-deckhand.json` and `docs/architecture/ai-persona-summaries.md`.

### 4. SMARTART brief-side contract is unverifiable as written

**Raised by:** critical-goal, BSA methodology, ai-persona-architect, test engineer (4 of 6).

Section 3.4 step 4 adopts a brief-side contract: SMARTART marker slides must carry only title + marker. This is a promise the brief makes; no one checks whether the superpower honoured it. When honoured the enrichment is clean; when violated, body text fragments bleed through behind the injected SmartArt.

The methodology's "guardrails must be enforceable" rule says this should be a verifiable analyser check, not a prose assertion.

**Action:** Add analyser step: on any slide carrying a SMARTART marker, detect other text frames whose bounding boxes overlap the marker's geometry. Flag for user in the enrichment menu with options: proceed anyway / clear overlapping text / drop this enrichment.

### 5. Transactional semantics across enrichments

**Raised by:** critical-goal, solution-architect (2 of 6).

Section 3.4 applies Op1, Op2, Op3 sequentially to a single file. If Op3 fails after Op2 succeeded, the file is left partially enriched with no rollback. "Never modify the original" is respected, but the copy is inconsistent with the approved plan.

**Action:** Accumulate all python-pptx mutations against a single in-memory `Presentation` object; save once when all ops succeed. SmartArt injection (which is read-all → mutate → write-fresh internally) sequences naturally after python-pptx ops complete. Add explicit "all-or-nothing" gate before the final rename.

### 6. Security surface needs hardening

**Raised by:** security-architect (1 of 6, specialist lens).

Five findings, three at High severity:

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| C1 | High | Arbitrary file-read via image paths — brief could direct the bridge to embed `~/.ssh/id_rsa` as a "PNG" | Resolve image paths against an allowlist of directories; reject symlinks; `path.is_relative_to(allowed_root)` |
| C2 | High | JS build script parsing must never execute the script (no `node build.js`, no `eval`, no `require`) | State this explicitly in Section 3.1. Alternative resolution: theme #1 (parse .pptx, skip the build script) |
| C3 | Med-High | .pptx zip-bombs, XXE, part-explosion | Pre-flight size/part/ratio ceilings; `lxml.etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)` everywhere |
| C4 | Medium | TOCTOU / concurrent-write on output files | Write to `.tmp-<pid>` + `os.replace()`; fail loudly if destination is locked |
| D1 | Medium | PII exfiltration to cloud providers (names, products embedded in prompts) | Add privacy tier to brief; default Ollama-only if `restricted`; explicit confirmation before first cloud call |

Plus medium-severity items on supply-chain trust (the bridge `sys.path`-mutates to import from `jack-tar-msft-smartart`) and cost/DoS (no enforced budget cap).

**Action:** Add a new "Security & Privacy" section to the spec covering input validation, image-path allowlisting, XML parser config, atomic writes, PII tiering.

## Per-reviewer notable single findings

- **Critical-goal:** "SmartArt layout selection is hand-waved. Marker examples use both `SMARTART:<type>` (flowchart) and `SMARTART:<semantic-tag>` (three-pillars). Pick one."
- **Solution-architect:** Proposed canonical layout for the storage of enrichment state: accumulate mutations, single save. Called the sequential-apply pattern "a cleanup bomb waiting to detonate."
- **BSA methodology:** Proposed concrete canonical-model delta for v1.5.0 — new L1 "Bridge Services", two personas, 9 interactions, Cross-Domain SOP Register entry, 4 Dependency Register entries. Proposed full 5-tier measurement blueprint.
- **Persona-architect:** Proposed the `narrative-architect` reuse alternative; proposed Enrichment Cohesion Reviewer with full skeleton contract.
- **Security:** Flagged that `Image.from_file()` + attacker-influenced paths can embed arbitrary files as "PNG". This is the single highest-severity finding across the review.
- **Test engineer:** Proposed a 77-test structure across `test_placeholder.py`, `test_analyser.py`, `test_enrichment.py`, `test_smartart_bridge.py`, `test_image_bridge.py`, `test_contract_pptx_superpower.py`, plus 4 cross-plugin integration tests. Concrete test names provided.

## Residual single-reviewer items worth keeping

- Budget cap input `budget_cap_usd` with default $1.00 (security, methodology, persona — convergent)
- SMARTART layout selection grammar decision (critical-goal)
- Marker identifier duplicate handling (critical-goal, test)
- `BG:` marker coordinate is meaningless — spec should say so (solution-architect)
- PLUGIN_ROOT discovery pattern for the msft-smartart import (solution-architect)
- Enrichment report schema is undefined (critical-goal, solution-architect, test)
- Spike 1 re-run with `objectName` brief not done — Variant A is existence-proof but not confirmation (critical-goal)

## Recommended next steps (priority order)

1. **Decide and rewrite Section 3.1:** analyser reads .pptx, not build script. Add text-scan fallback as second tier. (Resolves themes 1, 2, partially 6-C2.)
2. **Add Section 3.4 transactional gate:** in-memory Presentation accumulator, all-ops-succeed before save. (Resolves theme 5.)
3. **Convert SMARTART brief-side contract into analyser check.** (Resolves theme 4.)
4. **Draft Security & Privacy section:** image-path allowlist, XML parser hardening, atomic writes, PII tiering, `budget_cap_usd` input. (Resolves theme 6.)
5. **Write 19-section AI Persona definitions** (or explicit non-persona declarations) for Narrative Brief Architect and Enrichment Cohesion Reviewer. Or fold into existing narrative-architect if reuse wins. (Resolves theme 3.)
6. **Update .bsa/models/jack-tar-deckhand.json** to v1.5.0 with the new L1, personas, SOP register entry, and dependency register entries.
7. **Sketch the enrichment report schema** with field-level detail.
8. **Decide marker grammar conventions:** `SMARTART:<layout-id>` or `SMARTART:<semantic-slug>`? Uniqueness scope? Add to Placeholder Instructions.
9. **Optional follow-up spike:** re-run Spike 1 Variants B and C with the corrected `objectName` brief to close the empirical loop. Low-cost confirmation. Only needed if Variant A feels insufficient.

After these edits, a second (shorter) review pass is recommended before the implementation plan is written. The themes above are tractable — the spec does not require a redesign.

## Review logs

Raw per-reviewer outputs retained in this session's message log. If needed for future reference, they can be extracted and saved per-reviewer on request.
