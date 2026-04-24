"""Shared dataclasses for the analyser, enrichment menu, and report.

Lifted from Spike 3's `parsers/slide_facts.py` and extended with the
EnrichmentChoice + AnalyserResult + OverlapWarning shapes used by the
production analyser orchestrator and the enrichment menu.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

VALID_MARKER_KINDS = {"IMAGE", "SMARTART", "BG"}
VALID_ENRICHMENT_KINDS = {"background", "image", "smartart"}
VALID_ENRICHMENT_ACTIONS = {"apply", "apply_clear_overlap", "skip"}


@dataclass
class Marker:
    kind: str
    identifier: str
    left_emu: int
    top_emu: int
    width_emu: int
    height_emu: int

    def __post_init__(self) -> None:
        if self.kind not in VALID_MARKER_KINDS:
            raise ValueError(f"invalid kind {self.kind!r}; want one of {VALID_MARKER_KINDS}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Marker":
        return cls(
            kind=d["kind"],
            identifier=d["identifier"],
            left_emu=int(d["left_emu"]),
            top_emu=int(d["top_emu"]),
            width_emu=int(d["width_emu"]),
            height_emu=int(d["height_emu"]),
        )


@dataclass
class SlideFacts:
    slide_index: int                                  # 1-based
    text_content: str
    markers: list[Marker] = field(default_factory=list)
    background_kind: str = "default"                  # default | solid | image | unknown
    element_types: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "slide_index": self.slide_index,
            "text_content": self.text_content,
            "markers": [m.to_dict() for m in self.markers],
            "background_kind": self.background_kind,
            "element_types": dict(self.element_types),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SlideFacts":
        return cls(
            slide_index=d["slide_index"],
            text_content=d["text_content"],
            markers=[Marker.from_dict(m) for m in d.get("markers", [])],
            background_kind=d.get("background_kind", "default"),
            element_types=dict(d.get("element_types", {})),
        )


@dataclass
class OverlapWarning:
    slide_index: int
    marker_id: str
    overlapping_shape_names: list[str]


@dataclass
class EnrichmentChoice:
    """A user's selection for a single enrichment opportunity."""
    slide_index: int
    kind: str                          # background | image | smartart
    marker_id: str | None              # None for unmarked-slide suggestions
    action: str = "apply"              # apply | apply_clear_overlap | skip
    notes: str = ""                    # optional user override text

    def __post_init__(self) -> None:
        if self.kind not in VALID_ENRICHMENT_KINDS:
            raise ValueError(f"invalid kind {self.kind!r}; want one of {VALID_ENRICHMENT_KINDS}")
        if self.action not in VALID_ENRICHMENT_ACTIONS:
            raise ValueError(
                f"invalid action {self.action!r}; want one of {VALID_ENRICHMENT_ACTIONS}"
            )


@dataclass
class AnalyserResult:
    slides: list[SlideFacts]
    duplicate_marker_ids: list[str] = field(default_factory=list)
    overlap_warnings: list[OverlapWarning] = field(default_factory=list)
    js_fallback_used: bool = False
    notes: list[str] = field(default_factory=list)

    @property
    def total_slides(self) -> int:
        return len(self.slides)

    @property
    def total_markers(self) -> int:
        return sum(len(s.markers) for s in self.slides)
