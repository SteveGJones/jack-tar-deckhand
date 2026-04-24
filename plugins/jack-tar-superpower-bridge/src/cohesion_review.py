"""Cohesion review — verdict envelope parsing + decision table (caveat #2).

The Enrichment Cohesion Reviewer agent (agents/enrichment-cohesion-reviewer.md)
returns a structured JSON envelope. This module:

  1. Parses + validates the envelope into typed dataclasses.
  2. Implements the decision table that maps verdict + severity +
     enrichment_kind -> an AutoAction the orchestrator executes.

Caveat #2: the spec lists verdicts but doesn't say what the orchestrator
DOES with each. The table here is the canonical answer.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

VALID_AGGREGATES = {"pass", "requires_revision"}
VALID_VERDICTS = {
    "pass",
    "flag_contrast",
    "flag_inconsistency",
    "flag_overcrowded",
    "unassessable_rasterisation",
}
VALID_SEVERITIES = {"blocking", "suggestion"}
VALID_KINDS = {"background", "image", "smartart"}


@dataclass
class SlideVerdict:
    slide_index: int
    enrichment_kind: str
    verdict: str
    severity: str
    confidence: float
    reason: str


@dataclass
class DeckVerdict:
    aggregate_verdict: str
    slide_verdicts: list[SlideVerdict]


@dataclass
class AutoAction:
    """One of: no_action | record_only | regenerate | retry_clear_overlap | surface_to_user."""
    kind: str
    guidance: str
    slide_index: int | None = None


def parse_reviewer_envelope(payload: dict[str, Any]) -> DeckVerdict:
    agg = payload.get("aggregate_verdict")
    if agg not in VALID_AGGREGATES:
        raise ValueError(
            f"aggregate_verdict {agg!r} not in {VALID_AGGREGATES}"
        )
    slide_verdicts: list[SlideVerdict] = []
    for sv in payload.get("slide_verdicts", []):
        verdict = sv.get("verdict")
        severity = sv.get("severity")
        kind = sv.get("enrichment_kind")
        if verdict not in VALID_VERDICTS:
            raise ValueError(f"verdict {verdict!r} not in {VALID_VERDICTS}")
        if severity not in VALID_SEVERITIES:
            raise ValueError(f"severity {severity!r} not in {VALID_SEVERITIES}")
        if kind not in VALID_KINDS:
            raise ValueError(f"enrichment_kind {kind!r} not in {VALID_KINDS}")
        slide_verdicts.append(SlideVerdict(
            slide_index=int(sv["slide_index"]),
            enrichment_kind=kind,
            verdict=verdict,
            severity=severity,
            confidence=float(sv.get("confidence", 0.0)),
            reason=sv.get("reason", ""),
        ))
    return DeckVerdict(aggregate_verdict=agg, slide_verdicts=slide_verdicts)


def decide_action(sv: SlideVerdict) -> AutoAction:
    """The decision table. Caveat #2 — verdict + severity + kind -> action."""
    if sv.verdict == "pass":
        return AutoAction(kind="no_action", guidance="", slide_index=sv.slide_index)

    if sv.verdict == "unassessable_rasterisation":
        return AutoAction(
            kind="record_only",
            guidance="LibreOffice rasterisation could not assess this slide; "
                     "render via PowerPoint (tools/pptx_to_pdf.sh) for authoritative check.",
            slide_index=sv.slide_index,
        )

    # Suggestion verdicts always record-only
    if sv.severity == "suggestion":
        return AutoAction(
            kind="record_only",
            guidance=f"{sv.verdict}: {sv.reason}",
            slide_index=sv.slide_index,
        )

    # Blocking verdicts map by verdict+kind
    if sv.verdict == "flag_contrast":
        return AutoAction(
            kind="regenerate",
            guidance=("Regenerate the enrichment with the contrast issue threaded "
                       "into the prompt. Keep the same composition; reduce brightness "
                       "or add a darkening overlay where text sits."),
            slide_index=sv.slide_index,
        )

    if sv.verdict == "flag_overcrowded":
        if sv.enrichment_kind == "smartart":
            return AutoAction(
                kind="retry_clear_overlap",
                guidance=("Re-run the SMARTART enrichment with action=apply_clear_overlap; "
                          "remove the overlapping body shapes before injecting."),
                slide_index=sv.slide_index,
            )
        return AutoAction(
            kind="surface_to_user",
            guidance=(f"{sv.enrichment_kind} enrichment overcrowds the slide; "
                       f"reviewer recommends user judgement: {sv.reason}"),
            slide_index=sv.slide_index,
        )

    if sv.verdict == "flag_inconsistency":
        # Auto-regen rarely fixes consistency at deck level — escalate
        return AutoAction(
            kind="surface_to_user",
            guidance=(f"Visual register clashes with neighbouring slides: {sv.reason}. "
                       f"User judgement recommended."),
            slide_index=sv.slide_index,
        )

    # Defensive default
    return AutoAction(
        kind="surface_to_user",
        guidance=f"Unhandled blocking verdict {sv.verdict!r}; surface to user.",
        slide_index=sv.slide_index,
    )


def aggregate_for_report(slide_verdicts: list[SlideVerdict]) -> dict[str, Any]:
    """Produce a structured summary the enrichment_report.py module embeds."""
    pass_count = sum(1 for v in slide_verdicts if v.verdict == "pass")
    suggestion_count = sum(1 for v in slide_verdicts if v.severity == "suggestion"
                            and v.verdict != "pass")
    blocking_count = sum(1 for v in slide_verdicts if v.severity == "blocking"
                          and v.verdict != "pass")
    actions = []
    for sv in slide_verdicts:
        action = decide_action(sv)
        actions.append({
            "slide_index": sv.slide_index,
            "verdict": sv.verdict,
            "severity": sv.severity,
            "action": action.kind,
            "guidance": action.guidance,
            "reason": sv.reason,
        })
    return {
        "pass_count": pass_count,
        "suggestion_count": suggestion_count,
        "blocking_count": blocking_count,
        "actions": actions,
    }
