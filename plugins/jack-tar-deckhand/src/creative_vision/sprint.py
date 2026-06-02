"""Pre-deck creative_vision sprint phase — partitioning + progress tracking.

Issue #113 AC2. The Creative Sprint is the phase in the deck-conductor flow
where ALL creative_vision slides run to operator acceptance BEFORE composed
slides are assembled. This separates the slow, high-touch creative_vision
review cadence from the fast, low-touch standard-slide cadence so operators
don't context-switch between modes.

The CreativeVisionManifest at ``<deck_dir>/creative-vision/<slide_number>/manifest.json``
is the authoritative per-slide status — once its ``final`` field is populated
the slide is considered ``accepted`` for sprint purposes. Resumption after
interruption is automatic: ``creative_sprint_progress`` walks the strategy map
and reads each slide's manifest to compute the state.

Public surface:

- :func:`partition_strategy_map_for_creative_sprint` — split a strategy map
  into ``(creative_vision_slides, other_slides)`` lists so the conductor can
  iterate the creative slides first.
- :func:`creative_sprint_slide_status` — query the per-slide status (one of
  ``"accepted"``, ``"in_progress"``, ``"not_started"``).
- :func:`creative_sprint_progress` — deck-level aggregate of slide statuses.
- :func:`format_sprint_progress_markdown` — operator-facing markdown surface
  the deck-conductor / SKILL.md render between slides.
- :func:`is_sprint_complete` — guard for the conductor: must return True
  before the conductor proceeds to standard-slide assembly.
"""
from __future__ import annotations

import json
import os
from typing import Iterable

# Per-slide status terms — used as dict keys in progress aggregates AND as
# literal strings in operator-facing markdown. Keep stable.
STATUS_ACCEPTED = "accepted"
STATUS_IN_PROGRESS = "in_progress"
STATUS_NOT_STARTED = "not_started"

_ALL_STATUSES = (STATUS_ACCEPTED, STATUS_IN_PROGRESS, STATUS_NOT_STARTED)


def partition_strategy_map_for_creative_sprint(
    strategy_map: dict,
) -> tuple[list[dict], list[dict]]:
    """Split slides into (creative_vision_slides, other_slides).

    The Creative Sprint iterates the first list to operator acceptance before
    the conductor touches the second list. Order within each list mirrors the
    strategy map's slide order so cross-slide narrative anchors stay coherent.

    Returns:
        Two lists. The first contains every slide whose ``strategy`` equals
        ``"creative_vision"`` (in strategy-map order); the second contains the
        rest (in strategy-map order). The union is the full strategy map's
        slides; the intersection is empty.

    Notes:
        A slide is considered creative_vision strictly by its ``strategy``
        field. Slides with ``creative_vision: pending_vision_prose: true`` are
        still partitioned into the creative slides list — the sprint phase
        is responsible for prompting the operator for prose when it
        encounters them.
    """
    creative_vision = []
    other = []
    for slide in strategy_map.get("slides", []):
        if slide.get("strategy") == "creative_vision":
            creative_vision.append(slide)
        else:
            other.append(slide)
    return creative_vision, other


def _per_slide_manifest_path(deck_dir: str, slide_number: int) -> str:
    """Return the path that ``manifest.save_manifest`` writes to."""
    return os.path.join(
        deck_dir, "creative-vision", str(slide_number), "manifest.json"
    )


def creative_sprint_slide_status(deck_dir: str, slide_number: int) -> str:
    """Classify one creative_vision slide as accepted / in_progress / not_started.

    The classification is purely structural — it reads the per-slide
    CreativeVisionManifest written by ``creative_vision.manifest.save_manifest``
    and looks at two fields:

    - **No manifest file** → ``"not_started"``. The cascade hasn't been
      dispatched for this slide yet.
    - **Manifest exists, ``final`` is None or missing** → ``"in_progress"``.
      The cascade has been running but operator hasn't accepted a final.
    - **Manifest exists, ``final`` is a dict (truthy)** → ``"accepted"``.

    Args:
        deck_dir: Path to the deck working directory.
        slide_number: Slide number whose status to query.

    Returns:
        One of ``"accepted"``, ``"in_progress"``, ``"not_started"``.
    """
    path = _per_slide_manifest_path(deck_dir, slide_number)
    if not os.path.isfile(path):
        return STATUS_NOT_STARTED
    try:
        with open(path) as f:
            manifest = json.load(f)
    except (OSError, json.JSONDecodeError):
        # Corrupt manifest — treat as not_started so the operator notices on
        # next dispatch. We do NOT silently re-accept a half-written file.
        return STATUS_NOT_STARTED
    if manifest.get("final"):
        return STATUS_ACCEPTED
    return STATUS_IN_PROGRESS


def creative_sprint_progress(
    deck_dir: str,
    strategy_map: dict,
) -> dict:
    """Deck-level sprint progress: counts + per-slide status detail.

    Walks the strategy map for creative_vision slides and aggregates each
    slide's status (read from its CreativeVisionManifest). The result is the
    payload the deck-conductor renders between sprint iterations so the
    operator sees what is left.

    Returns:
        A dict with:

        - ``total`` — count of creative_vision slides in the strategy map.
        - ``accepted`` / ``in_progress`` / ``not_started`` — counts per status.
        - ``slides`` — list of ``{slide_number, status}`` dicts in strategy-map
          order. Always includes every creative_vision slide so the operator
          can see the whole sprint board.
        - ``complete`` — convenience boolean: ``True`` iff every slide is
          ``accepted``.

        When the strategy map has no creative_vision slides, ``total`` is 0
        and ``complete`` is ``True`` (an empty sprint trivially passes).
    """
    creative_vision_slides, _ = partition_strategy_map_for_creative_sprint(strategy_map)

    counts = {status: 0 for status in _ALL_STATUSES}
    slides_detail: list[dict] = []

    for slide in creative_vision_slides:
        slide_number = slide["slide_number"]
        status = creative_sprint_slide_status(deck_dir, slide_number)
        counts[status] += 1
        slides_detail.append({"slide_number": slide_number, "status": status})

    return {
        "total": len(creative_vision_slides),
        "accepted": counts[STATUS_ACCEPTED],
        "in_progress": counts[STATUS_IN_PROGRESS],
        "not_started": counts[STATUS_NOT_STARTED],
        "slides": slides_detail,
        "complete": counts[STATUS_ACCEPTED] == len(creative_vision_slides),
    }


def is_sprint_complete(deck_dir: str, strategy_map: dict) -> bool:
    """Single-line conductor guard: True iff every creative_vision slide is accepted.

    The deck-conductor MUST NOT proceed to standard-slide assembly (composed,
    backdrop, full_render) until this returns True. Standard-slide work can
    safely run in parallel with creative_vision review only when there is no
    risk of context-switching — and the empirical evidence (F12) is that the
    risk is too high, so the conductor serialises.
    """
    return creative_sprint_progress(deck_dir, strategy_map)["complete"]


def format_sprint_progress_markdown(progress: dict) -> str:
    """Render the deck-conductor's sprint progress surface for the operator.

    The conductor shows this between iterations: a header counting slides at
    each status, followed by a per-slide table. When the sprint is complete,
    a clear completion line is shown so the operator knows the conductor will
    proceed to standard-slide assembly next.

    Args:
        progress: A dict returned by :func:`creative_sprint_progress`.

    Returns:
        Operator-ready markdown. Always non-empty.
    """
    total = progress["total"]
    if total == 0:
        return (
            "No creative_vision slides in this strategy map — Creative "
            "Sprint phase is trivially complete. Proceeding to standard-"
            "slide assembly."
        )

    lines = [
        f"## Creative Sprint progress ({progress['accepted']}/{total} accepted)",
        "",
        f"- **Accepted:** {progress['accepted']}",
        f"- **In progress:** {progress['in_progress']}",
        f"- **Not started:** {progress['not_started']}",
        "",
        "| Slide | Status |",
        "| ----- | ------ |",
    ]
    for entry in progress["slides"]:
        lines.append(f"| {entry['slide_number']} | `{entry['status']}` |")

    lines.append("")
    if progress["complete"]:
        lines.append(
            "**Creative Sprint complete.** Every creative_vision slide has "
            "been accepted by the operator. The deck-conductor will now "
            "proceed to standard-slide assembly (composed / backdrop / "
            "full_render) with the faster review cadence."
        )
    else:
        remaining = progress["in_progress"] + progress["not_started"]
        lines.append(
            f"**Sprint in progress.** {remaining} creative_vision slide(s) "
            f"remain. The deck-conductor will continue iterating on each "
            f"slide until the operator accepts. Standard-slide assembly is "
            f"BLOCKED until the sprint completes."
        )
    return "\n".join(lines)


def next_unaccepted_slide(progress: dict) -> int | None:
    """Return the slide number of the next slide for the conductor to work on.

    Picks the first slide in strategy-map order that is NOT ``accepted``.
    ``in_progress`` is preferred over ``not_started`` so the conductor
    resumes an interrupted slide rather than abandoning it. Returns ``None``
    when the sprint is complete.
    """
    in_progress = [
        s["slide_number"] for s in progress["slides"]
        if s["status"] == STATUS_IN_PROGRESS
    ]
    if in_progress:
        return in_progress[0]
    not_started = [
        s["slide_number"] for s in progress["slides"]
        if s["status"] == STATUS_NOT_STARTED
    ]
    if not_started:
        return not_started[0]
    return None
