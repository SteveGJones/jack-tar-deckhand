"""GenerationResult — the return value of generate_cloud_image().

Backwards-compatible: implements __fspath__ and __str__ so legacy callers
that pass the result to Path(), open(), or string interpolation keep working.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class GenerationResult:
    path: str
    cost_estimated: float
    cost_actual: Optional[float]
    usage_metadata: Optional[dict]
    provider: str
    model: str
    resolution: str

    def __fspath__(self) -> str:
        return self.path

    def __str__(self) -> str:
        return self.path
