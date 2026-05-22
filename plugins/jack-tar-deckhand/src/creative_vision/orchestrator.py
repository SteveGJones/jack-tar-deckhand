"""Creative-vision orchestrator state machine.

Pure logic — knows nothing about agent dispatch. The SKILL.md drives the agent
calls and invokes these helpers to advance state between dispatches. Issue #105.
"""
from __future__ import annotations
