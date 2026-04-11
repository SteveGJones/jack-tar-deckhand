"""Shared fixtures for cross-plugin integration tests.

Each plugin has its own `src/` package. To avoid namespace collision when
tests run in sequence, we use importlib-based loading inside each test
rather than relying on global sys.path state.
"""
import sys
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
MSFT_SMARTART_ROOT = WORKTREE / "plugins" / "jack-tar-msft-smartart"
DECKHAND_ROOT = WORKTREE / "plugins" / "jack-tar-deckhand"
