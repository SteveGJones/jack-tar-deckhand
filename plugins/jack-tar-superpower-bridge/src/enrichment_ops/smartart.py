"""Op3 — graft a pptx_native SmartArt carrier into a host .pptx.

Unlike Op1 and Op2, this op operates on FILES (the msft-smartart
`assembler_patch.inject` reads + writes the host zip directly). The
transactional orchestrator handles the in-memory→temp-file save before
calling this op.
"""
from __future__ import annotations

from pathlib import Path

from src.msft_smartart_loader import load_msft_smartart_api


def inject_smartart_into_file(
    *,
    host_pptx: Path,
    slide_index_1based: int,
    marker_name: str,
    carrier_pptx: Path,
) -> None:
    api = load_msft_smartart_api()
    request = api.InjectionRequest(
        slide_number=slide_index_1based,
        carrier_pptx=Path(carrier_pptx),
        placeholder_name=marker_name,
    )
    api.inject(Path(host_pptx), [request])
