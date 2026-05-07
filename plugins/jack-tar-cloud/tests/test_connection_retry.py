"""Tests for the connection-reset retry decorator (Run 6 Finding #16).

Run 6 dogfood (2026-04-29) Phase C Pro batch hit ``ConnectionResetError``
on the 3rd of 4 generations during the strategic-fit-diagram render. The
orchestrator manually retried; the bridge had no built-in retry. For
production runs this is a robustness gap — third-party API connections
reset routinely and a single transient failure should not abort an
otherwise-successful run.

This module verifies that ``retry_on_connection_reset`` wraps a callable
to retry up to 3 times with exponential backoff on
``ConnectionResetError`` / ``ConnectionError``, and re-raises non-connection
errors immediately.
"""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

import pytest
import requests

from src.generate_cloud_image import retry_on_connection_reset  # noqa: E402


def test_retry_succeeds_on_first_attempt_when_no_error():
    calls = []

    @retry_on_connection_reset()
    def ok():
        calls.append(1)
        return "fine"

    assert ok() == "fine"
    assert len(calls) == 1


def test_retry_recovers_from_one_connection_reset(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))
    attempts = {"n": 0}

    @retry_on_connection_reset()
    def flaky():
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise ConnectionResetError("connection reset by peer")
        return "recovered"

    assert flaky() == "recovered"
    assert attempts["n"] == 2
    # First retry waits 1 second per the documented backoff schedule
    assert sleeps == [1]


def test_retry_recovers_from_two_consecutive_connection_resets(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))
    attempts = {"n": 0}

    @retry_on_connection_reset()
    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise ConnectionResetError("transient")
        return "ok"

    assert flaky() == "ok"
    assert attempts["n"] == 3
    # Backoff schedule: 1s after first failure, 2s after second
    assert sleeps == [1, 2]


def test_retry_raises_after_three_failures(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))
    attempts = {"n": 0}

    @retry_on_connection_reset()
    def always_fails():
        attempts["n"] += 1
        raise ConnectionResetError("persistent")

    with pytest.raises(ConnectionResetError, match="persistent"):
        always_fails()
    assert attempts["n"] == 3
    # Two backoff sleeps before the final attempt; no sleep after the last
    # failure (we re-raise immediately).
    assert sleeps == [1, 2]


def test_retry_passes_through_non_connection_errors_immediately(monkeypatch):
    """Auth failures, value errors, etc. must NOT be retried — those are
    deterministic failures that won't recover by waiting."""
    sleeps: list[float] = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))
    attempts = {"n": 0}

    @retry_on_connection_reset()
    def auth_failure():
        attempts["n"] += 1
        raise ValueError("bad api key")

    with pytest.raises(ValueError, match="bad api key"):
        auth_failure()
    assert attempts["n"] == 1
    assert sleeps == []


def test_retry_handles_requests_connection_error(monkeypatch):
    """The FAL.ai path uses requests.get() which raises
    requests.exceptions.ConnectionError on TCP reset. The decorator must
    treat this as a retryable connection error too."""
    sleeps: list[float] = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))
    attempts = {"n": 0}

    @retry_on_connection_reset()
    def flaky_requests():
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise requests.exceptions.ConnectionError("connection aborted")
        return "ok"

    assert flaky_requests() == "ok"
    assert attempts["n"] == 2


def test_retry_preserves_arguments_and_kwargs(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    seen: list[tuple[tuple, dict]] = []

    @retry_on_connection_reset()
    def echo(*args, **kwargs):
        seen.append((args, kwargs))
        return (args, kwargs)

    result = echo("a", "b", x=1)
    assert result == (("a", "b"), {"x": 1})
    assert seen == [(("a", "b"), {"x": 1})]


def test_retry_custom_backoff_schedule(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))
    attempts = {"n": 0}

    @retry_on_connection_reset(max_attempts=4, backoff_seconds=(0.1, 0.2, 0.5))
    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 4:
            raise ConnectionResetError("e")
        return "ok"

    assert flaky() == "ok"
    assert sleeps == [0.1, 0.2, 0.5]
