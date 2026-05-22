"""Aggregate calibration results into report.md.

Reads docs/spikes/2026-05-21-actual-token-pricing/calibration-results.json
and emits a Markdown delta report grouped by (provider, model, resolution).
"""
import json
import statistics
from collections import defaultdict
from pathlib import Path

RESULTS = Path("docs/spikes/2026-05-21-actual-token-pricing/calibration-results.json")
REPORT = Path("docs/spikes/2026-05-21-actual-token-pricing/report.md")


def main():
    rows = json.loads(RESULTS.read_text())
    successful = [r for r in rows if r.get("error") is None]
    errored = [r for r in rows if r.get("error") is not None]

    grouped = defaultdict(list)
    for r in successful:
        grouped[(r["provider"], r["model"], r["resolution"])].append(r)

    lines = [
        "# Phase 1 — Calibration Report",
        "",
        "**Spec:** `docs/superpowers/specs/2026-05-21-actual-token-pricing-validation-design.md`",
        "**Plan:** `docs/superpowers/plans/2026-05-21-actual-token-pricing.md`",
        "**Data:** `calibration-results.json` (16 cells, "
        + str(len(successful)) + " successful, " + str(len(errored)) + " errored)",
        "",
        "## Headline",
        "",
        "(filled in after generating the table — see verdict)",
        "",
        "## Delta per (provider, model, resolution)",
        "",
        "| Provider | Model | Resolution | N | Mean estimate | Mean actual | Median Δ% | Min Δ% | Max Δ% |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    overall_estimate = 0.0
    overall_actual = 0.0
    for (provider, model, res), bucket in sorted(grouped.items()):
        est_mean = statistics.mean(r["catalog_estimate_usd"] for r in bucket)
        act_mean = statistics.mean(r["computed_actual_usd"] for r in bucket)
        deltas = [r["delta_pct"] for r in bucket]
        lines.append(
            f"| {provider} | {model} | {res} | {len(bucket)} | "
            f"${est_mean:.4f} | ${act_mean:.4f} | "
            f"{statistics.median(deltas):+.1f}% | {min(deltas):+.1f}% | {max(deltas):+.1f}% |"
        )
        overall_estimate += sum(r["catalog_estimate_usd"] for r in bucket)
        overall_actual += sum(r["computed_actual_usd"] for r in bucket)

    lines += [
        "",
        f"**Cumulative catalog estimate:** ${overall_estimate:.3f}",
        f"**Cumulative actual:**           ${overall_actual:.3f}",
        f"**Overall delta:**               "
        f"{(overall_estimate - overall_actual) / overall_estimate * 100:+.1f}% "
        f"(negative = actual exceeds estimate)",
        "",
    ]

    # Per-prompt-size aggregation across all Google cells (the strongest signal)
    by_prompt = defaultdict(list)
    for r in successful:
        if r["provider"] == "google_nano_banana":
            by_prompt[r["prompt_key"]].append(r["delta_pct"])

    if by_prompt:
        lines += [
            "## Prompt-length sensitivity (Google Nano Banana only)",
            "",
            "| Prompt | N | Mean Δ% | Median Δ% |",
            "|---|---|---|---|",
        ]
        for key in ("short_a", "medium_a", "long_a"):
            if key in by_prompt:
                ds = by_prompt[key]
                lines.append(
                    f"| {key} | {len(ds)} | {statistics.mean(ds):+.1f}% | {statistics.median(ds):+.1f}% |"
                )
        lines.append("")

    # OpenAI caveat
    openai_rows = [r for r in successful if r["provider"] == "openai"]
    if openai_rows:
        lines += [
            "## OpenAI — caveat",
            "",
            "OpenAI deltas use placeholder rates ($5/MTok input, $40/MTok output) because openai.com"  # noqa: E501
            " pricing pages returned 403 during Task 4. Token counts are real; dollar conversion is"
            " provisional. If verified rates differ, delta direction could flip. Treat as directional only.",
            "",
        ]

    # Errored cells (sentinel rows)
    if errored:
        lines += [
            "## Errored cells",
            "",
            "| Provider | Model | Resolution | Prompt | Error |",
            "|---|---|---|---|---|",
        ]
        for r in errored:
            err = (r.get("error") or "")[:120].replace("|", "\\|")
            lines.append(f"| {r['provider']} | {r['model']} | {r['resolution']} | {r['prompt_key']} | {err} |")
        lines.append("")

    lines += [
        "## GO/NO-GO verdict",
        "",
        "Criteria from spec:",
        "- **GO** if any cell's median Δ ≥ 10%, OR cumulative actual is >10% below cumulative estimate.",
        "- **NO-GO** if all median Δ < 5%.",
        "- **AMBIGUOUS** if 5–10% deltas — extend matrix with _b prompts (budget permitting), then re-evaluate.",
        "",
        "**Verdict:** _TBD — fill in based on the table above before committing._",
        "",
        "## Key Findings (fill before committing)",
        "",
        "- Finding 1: ...",
        "- Finding 2: ...",
        "",
    ]

    REPORT.write_text("\n".join(lines))
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
