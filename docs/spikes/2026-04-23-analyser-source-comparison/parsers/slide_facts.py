# parsers/slide_facts.py
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Literal

MarkerKind = Literal["IMAGE", "SMARTART", "BG"]
VALID_KINDS = {"IMAGE", "SMARTART", "BG"}


@dataclass
class Marker:
    kind: str
    identifier: str
    left_emu: int
    top_emu: int
    width_emu: int
    height_emu: int

    def __post_init__(self) -> None:
        if self.kind not in VALID_KINDS:
            raise ValueError(f"invalid kind {self.kind!r}; want one of {VALID_KINDS}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SlideFacts:
    slide_index: int          # 1-based
    text_content: str         # concatenated text on the slide
    markers: list[Marker] = field(default_factory=list)
    background_kind: str = "default"   # "default" | "solid" | "image" | "unknown"
    element_types: dict[str, int] = field(default_factory=dict)  # {"text": n, "shape": n, "image": n, "chart": n, "table": n}

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
            markers=[Marker(**m) for m in d.get("markers", [])],
            background_kind=d.get("background_kind", "default"),
            element_types=dict(d.get("element_types", {})),
        )
