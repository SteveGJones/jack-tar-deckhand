"""Tests for the safety-filter retry layer (Issue #92).

When Google's Nano Banana / Imagen safety filter blocks a prompt, the SDK
returns an empty ``candidates`` list (or empty ``generated_images``) with no
explicit error. v1.4 closes that gap by:

1. Surfacing the empty-response as a typed
   :class:`SafetyFilterTriggeredError` from inside each provider helper.
2. Wrapping the public :func:`generate_cloud_image` with a softening retry
   loop that uses :func:`soften_prompt` from the safety_filter_vocab module.
3. Raising :class:`SafetyFilterExhaustedError` if 3 softening attempts all
   come back empty.

These tests mock the Google client to simulate empty / non-empty responses
and verify the contract on each path.
"""
from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

import pytest

from src import generate_cloud_image as gci  # noqa: E402
from src.generate_cloud_image import (  # noqa: E402
    SafetyFilterTriggeredError,
    SafetyFilterExhaustedError,
    _generate_via_nano_banana,
    _generate_via_imagen,
    generate_cloud_image,
)
from src.safety_filter_vocab import (  # noqa: E402
    DEFAULT_VOCAB,
    GENERIC_SOFTENING_PREFIX,
    load_vocab,
    soften_prompt,
)


# --- Vocab + soften_prompt unit tests ---------------------------------------


def test_default_vocab_is_exactly_20_entries():
    assert len(DEFAULT_VOCAB) == 20, (
        "Plan §2.8 + Q4 in §3 fix v1 vocab size at 20 entries. "
        "Operator override path is SAFETY_FILTER_VOCAB_PATH."
    )


def test_default_vocab_keys_and_values_are_strings():
    for k, v in DEFAULT_VOCAB.items():
        assert isinstance(k, str) and k
        assert isinstance(v, str) and v


def test_soften_replaces_vocab_word_case_insensitive():
    # "destroy" → "neutralise"
    softened = soften_prompt("The team must destroy the obstacle.")
    assert "destroy" not in softened.lower()
    assert "neutralise" in softened.lower()


def test_soften_preserves_title_case():
    softened = soften_prompt("Destroy the obstacle.")
    # First match is "Destroy" → "Neutralise" (title case preserved)
    assert softened.startswith("Neutralise ")


def test_soften_preserves_upper_case():
    softened = soften_prompt("DESTROY the obstacle.")
    assert softened.startswith("NEUTRALISE ")


def test_soften_falls_back_to_prefix_when_no_vocab_match():
    benign = "A lighthouse at sunset, dramatic clouds"
    softened = soften_prompt(benign)
    assert softened == GENERIC_SOFTENING_PREFIX + benign


def test_soften_is_idempotent_for_already_prefixed_prompt():
    benign = "A lighthouse at sunset"
    once = soften_prompt(benign)
    twice = soften_prompt(once)
    # Second softening with no vocab word + already-prefixed → no-op
    assert once == twice


def test_soften_uses_explicit_vocab_when_passed():
    custom = {"banana": "fruit"}
    softened = soften_prompt("A yellow banana on a table.", vocab=custom)
    assert "banana" not in softened
    assert "fruit" in softened


def test_load_vocab_returns_default_when_env_unset(monkeypatch):
    monkeypatch.delenv("SAFETY_FILTER_VOCAB_PATH", raising=False)
    assert load_vocab() == DEFAULT_VOCAB


def test_load_vocab_loads_override_from_env(monkeypatch, tmp_path):
    override = {"foo": "bar"}
    override_path = tmp_path / "vocab.json"
    override_path.write_text(json.dumps(override))
    monkeypatch.setenv("SAFETY_FILTER_VOCAB_PATH", str(override_path))
    loaded = load_vocab()
    assert loaded == override


def test_load_vocab_falls_back_to_default_on_malformed_override(monkeypatch, tmp_path):
    # Malformed JSON
    bad_path = tmp_path / "broken.json"
    bad_path.write_text("not json")
    monkeypatch.setenv("SAFETY_FILTER_VOCAB_PATH", str(bad_path))
    assert load_vocab() == DEFAULT_VOCAB


def test_load_vocab_falls_back_when_override_is_not_dict(monkeypatch, tmp_path):
    bad_path = tmp_path / "list.json"
    bad_path.write_text(json.dumps(["a", "b"]))
    monkeypatch.setenv("SAFETY_FILTER_VOCAB_PATH", str(bad_path))
    assert load_vocab() == DEFAULT_VOCAB


# --- Provider-helper guard tests -------------------------------------------


def _build_response_with_empty_candidates():
    """Mock a google-genai response that simulates safety-filter rejection."""
    resp = MagicMock()
    resp.candidates = None
    return resp


def _build_response_with_image():
    """Mock a successful google-genai response with one image part."""
    resp = MagicMock()
    part = MagicMock()
    part.inline_data.mime_type = "image/png"
    part.inline_data.data = b"\x89PNG\r\n\x1a\nfake"
    content = MagicMock()
    content.parts = [part]
    candidate = MagicMock()
    candidate.content = content
    resp.candidates = [candidate]
    return resp


def test_nano_banana_raises_safety_filter_on_empty_candidates():
    client = MagicMock()
    client.models.generate_content.return_value = _build_response_with_empty_candidates()
    with pytest.raises(SafetyFilterTriggeredError) as exc_info:
        _generate_via_nano_banana(client, "gemini-3.1-flash-image-preview", "bad prompt", "1K")
    assert exc_info.value.provider == "google"
    assert exc_info.value.model == "gemini-3.1-flash-image-preview"
    assert exc_info.value.prompt == "bad prompt"


def test_nano_banana_succeeds_on_normal_response():
    client = MagicMock()
    client.models.generate_content.return_value = _build_response_with_image()
    data = _generate_via_nano_banana(client, "gemini-3.1-flash-image-preview", "fine prompt", "1K")
    assert data == b"\x89PNG\r\n\x1a\nfake"


def test_imagen_raises_safety_filter_on_empty_generated_images():
    client = MagicMock()
    resp = MagicMock()
    resp.generated_images = []
    client.models.generate_images.return_value = resp
    with pytest.raises(SafetyFilterTriggeredError) as exc_info:
        _generate_via_imagen(client, "imagen-4.0-fast-generate-001", "bad prompt", "16:9", "1K")
    assert exc_info.value.provider == "google"
    assert exc_info.value.model == "imagen-4.0-fast-generate-001"


def test_imagen_succeeds_on_normal_response():
    client = MagicMock()
    resp = MagicMock()
    image = MagicMock()
    image.image.image_bytes = b"imagen-data"
    resp.generated_images = [image]
    client.models.generate_images.return_value = resp
    data = _generate_via_imagen(client, "imagen-4.0-fast-generate-001", "fine prompt", "16:9", "1K")
    assert data == b"imagen-data"


# --- Public generate_cloud_image retry loop --------------------------------


@pytest.fixture
def fake_provider(monkeypatch):
    """Install a fake provider into _PROVIDERS that can be configured to raise."""
    calls = []

    def maybe_raise(behaviour):
        def provider(prompt, output_path, *, resolution='1K', **kwargs):
            calls.append({"prompt": prompt, "resolution": resolution, "kwargs": kwargs})
            response = behaviour(len(calls) - 1, prompt)
            if isinstance(response, Exception):
                raise response
            return response
        return provider

    monkeypatch.setattr(gci, "_PROVIDERS", dict(gci._PROVIDERS))
    yield calls, maybe_raise


def test_generate_succeeds_on_first_attempt_when_no_safety_trigger(fake_provider, monkeypatch):
    calls, maybe_raise = fake_provider

    def behaviour(idx, prompt):
        return {"file_path": "/tmp/x.png", "status": "ok"}

    monkeypatch.setitem(gci._PROVIDERS, "google", maybe_raise(behaviour))
    result = generate_cloud_image("benign prompt", "google", "/tmp/x.png")
    assert result["status"] == "ok"
    assert len(calls) == 1
    assert calls[0]["prompt"] == "benign prompt"


def test_generate_softens_and_retries_after_safety_trigger(fake_provider, monkeypatch):
    """First call raises; second softened call succeeds."""
    calls, maybe_raise = fake_provider
    sleeps: list[float] = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))

    def behaviour(idx, prompt):
        if idx == 0:
            return SafetyFilterTriggeredError(prompt=prompt, provider="google", model="m")
        return {"file_path": "/tmp/x.png", "status": "ok"}

    monkeypatch.setitem(gci._PROVIDERS, "google", maybe_raise(behaviour))
    result = generate_cloud_image("destroy the obstacle", "google", "/tmp/x.png")
    assert result["status"] == "ok"
    assert len(calls) == 2
    # First call uses the original prompt
    assert calls[0]["prompt"] == "destroy the obstacle"
    # Second call has had "destroy" replaced with "neutralise"
    assert "destroy" not in calls[1]["prompt"].lower()
    assert "neutralise" in calls[1]["prompt"].lower()


def test_generate_raises_exhausted_after_three_softening_attempts(fake_provider, monkeypatch):
    """Initial + 3 retries = 4 attempts, then SafetyFilterExhaustedError."""
    calls, maybe_raise = fake_provider
    monkeypatch.setattr("time.sleep", lambda s: None)

    def always_block(idx, prompt):
        return SafetyFilterTriggeredError(prompt=prompt, provider="google", model="m")

    monkeypatch.setitem(gci._PROVIDERS, "google", maybe_raise(always_block))
    with pytest.raises(SafetyFilterExhaustedError) as exc_info:
        generate_cloud_image("destroy the obstacle and kill it", "google", "/tmp/x.png")
    # Exhausted after the 4th attempt (initial + 3 retries)
    assert len(calls) == 4
    err = exc_info.value
    assert err.original_prompt == "destroy the obstacle and kill it"
    assert len(err.attempts) == 4
    assert err.provider == "google"
    assert err.model == "m"
    # Each attempt has a distinct (softer) prompt
    prompts = [a["prompt"] for a in err.attempts]
    # First is the original
    assert prompts[0] == "destroy the obstacle and kill it"
    # Subsequent are softened
    for p in prompts[1:]:
        assert p != "destroy the obstacle and kill it"


def test_generate_exhausted_carries_model_from_inner_exception(fake_provider, monkeypatch):
    """SafetyFilterExhaustedError.model reflects the failing inner model."""
    _, maybe_raise = fake_provider
    monkeypatch.setattr("time.sleep", lambda s: None)

    def with_model(idx, prompt):
        return SafetyFilterTriggeredError(prompt=prompt, provider="google", model="imagen-4.0-fast-generate-001")

    monkeypatch.setitem(gci._PROVIDERS, "google", maybe_raise(with_model))
    with pytest.raises(SafetyFilterExhaustedError) as exc_info:
        generate_cloud_image("a banned subject", "google", "/tmp/x.png")
    assert exc_info.value.model == "imagen-4.0-fast-generate-001"


def test_generate_softens_multiple_vocab_words_across_retries(fake_provider, monkeypatch):
    """If the prompt has multiple vocab words, each retry softens one more."""
    calls, maybe_raise = fake_provider
    monkeypatch.setattr("time.sleep", lambda s: None)

    # Behaviour: first 2 attempts fail, third succeeds
    def behaviour(idx, prompt):
        if idx < 2:
            return SafetyFilterTriggeredError(prompt=prompt, provider="google", model="m")
        return {"file_path": "/tmp/x.png", "status": "ok"}

    monkeypatch.setitem(gci._PROVIDERS, "google", maybe_raise(behaviour))
    # Prompt has two vocab words: "destroy" and "kill"
    result = generate_cloud_image("destroy and kill the obstacle", "google", "/tmp/x.png")
    assert result["status"] == "ok"
    assert len(calls) == 3
    # First call: original
    assert "destroy" in calls[0]["prompt"].lower()
    # Second call: first vocab word softened (destroy → neutralise)
    assert "destroy" not in calls[1]["prompt"].lower()
    # Third call: should also have "kill" softened (kill → stop)
    assert "kill" not in calls[2]["prompt"].lower()


def test_generate_exhausted_via_imagen_path_real_function(monkeypatch, tmp_path):
    """End-to-end via the imagen helper: client mocked to always return empty."""
    monkeypatch.setattr("time.sleep", lambda s: None)
    # Pretend Google is configured
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    class FakeClient:
        class models:
            @staticmethod
            def generate_images(model, prompt, config):
                resp = MagicMock()
                resp.generated_images = []
                return resp

    monkeypatch.setattr(gci.genai, "Client", lambda **kw: FakeClient())

    out = tmp_path / "img.png"
    with pytest.raises(SafetyFilterExhaustedError):
        generate_cloud_image(
            "destroy the obstacle",
            "google",
            str(out),
            model="imagen-4.0-fast-generate-001",
        )


def test_generate_cloud_image_unchanged_for_unknown_provider():
    """ValueError for unknown provider must still propagate (not caught by safety loop)."""
    with pytest.raises(ValueError, match="Unknown provider"):
        generate_cloud_image("p", "definitely-not-a-provider", "/tmp/x.png")
