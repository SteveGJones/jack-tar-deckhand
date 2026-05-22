"""Top-level dispatch entry for creative_vision strategy.

Called by imagegen-bridge for each slide with strategy=creative_vision.
Mirror of paperbanana_dispatch.py — provides a single function the bridge
calls AND a dataclass describing the request. The actual orchestration
loop runs inside SKILL.md (imagegen-bridge), invoking the helpers in
src/creative_vision/ between agent dispatches. Issue #105.
"""
from __future__ import annotations
