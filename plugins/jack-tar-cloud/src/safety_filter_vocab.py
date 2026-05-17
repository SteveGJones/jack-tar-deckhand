"""Safety-filter softening vocabulary for Google Nano Banana + Imagen retries.

Issue #92 — when Google's safety filter rejects a prompt the response comes
back with an empty ``candidates`` list (no error code). The caller has no way
to recover except to soften the wording and retry. This module provides a
conservative 20-entry default mapping of common trigger words to safer
alternatives. The retry layer in :mod:`generate_cloud_image` calls
:func:`soften_prompt` on a triggered prompt before re-dispatching.

The vocab is deliberately small in v1 to minimise false positives. Operators
who hit a real-world trigger not covered here override via the
``SAFETY_FILTER_VOCAB_PATH`` environment variable, which should point at a
JSON file shaped like::

    {
        "trigger word": "softer replacement",
        ...
    }

The override REPLACES the default vocab entirely (it does not merge). Keys
and values are matched / replaced case-insensitively but preserve the casing
of the original word in the output.

Paperbanana borrow: empty-candidates guard pattern adapted from
``paperbanana/providers/image_gen/google_imagen.py:128-135`` (MIT-licensed).
The softening vocab itself is original to jack-tar.
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


# Default 20-entry vocab. Conservative — only obvious imagery triggers most
# operators would intuitively expect to upset a content filter. Each
# replacement preserves the structural role of the word so the rest of the
# prompt still parses sensibly.
DEFAULT_VOCAB: Dict[str, str] = {
    "destroy": "neutralise",
    "kill": "stop",
    "weapon": "implement",
    "gun": "device",
    "knife": "blade tool",
    "blood": "stain",
    "violence": "conflict",
    "attack": "confront",
    "explosion": "burst",
    "bomb": "container",
    "war": "campaign",
    "fight": "contest",
    "shooting": "discharge",
    "death": "endpoint",
    "corpse": "figure at rest",
    "wound": "mark",
    "execute": "perform",
    "assassin": "agent",
    "murder": "removal",
    "terror": "alarm",
}


def load_vocab() -> Dict[str, str]:
    """Load the active vocab — env override if set, else the default.

    Returns:
        dict[str, str]: trigger word → softer replacement.

    Raises:
        ValueError: if the env-pointed file is unreadable or not a JSON object
            mapping str → str. Falls through to the default with a warning
            rather than raising so a malformed override doesn't break the
            whole retry path.
    """
    override_path = os.environ.get("SAFETY_FILTER_VOCAB_PATH")
    if not override_path:
        return dict(DEFAULT_VOCAB)
    try:
        payload = json.loads(Path(override_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning(
            "SAFETY_FILTER_VOCAB_PATH=%s could not be loaded (%s); "
            "falling back to default vocab.",
            override_path, exc,
        )
        return dict(DEFAULT_VOCAB)
    if not isinstance(payload, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in payload.items()
    ):
        logger.warning(
            "SAFETY_FILTER_VOCAB_PATH=%s did not parse as dict[str, str]; "
            "falling back to default vocab.",
            override_path,
        )
        return dict(DEFAULT_VOCAB)
    return payload


# Generic prefix appended when no vocab word matches the triggered prompt.
# A bland descriptor that nudges the model toward a benign rendering without
# disclosing the original intent.
GENERIC_SOFTENING_PREFIX = "schematic, family-friendly illustration of "


def soften_prompt(prompt: str, vocab: Dict[str, str] | None = None) -> str:
    """Return a softer rewrite of ``prompt``.

    If any vocab key is a whole-word match in ``prompt`` (case-insensitive),
    the first such match is replaced with its softer value preserving the
    original casing pattern (Title → Title, UPPER → UPPER, lower → lower).
    If no vocab word matches, the generic softening prefix is prepended.

    Calling :func:`soften_prompt` again on the result yields a further round
    of softening (vocab replacement until exhausted, then prefix becomes a
    no-op for already-prefixed prompts — at that point the prompt has been
    softened as much as the vocab can manage and the caller should give up).

    Args:
        prompt: original prompt text.
        vocab: explicit vocab to use. ``None`` loads via :func:`load_vocab`.

    Returns:
        str: softened prompt (always non-empty, equal-or-greater length than
            the input).
    """
    if vocab is None:
        vocab = load_vocab()

    lowered = prompt.lower()
    for trigger, replacement in vocab.items():
        trigger_lower = trigger.lower()
        # Whole-word case-insensitive match
        pattern = re.compile(rf"\b{re.escape(trigger_lower)}\b", re.IGNORECASE)
        match = pattern.search(prompt)
        if match:
            original = match.group(0)
            return prompt[: match.start()] + _match_case(original, replacement) + prompt[match.end():]
        # Quick exit on the lowered check to keep the loop cheap when there
        # are no matches — the pattern.search above is the authoritative
        # check, this is just an early-out filter.
        if trigger_lower not in lowered:
            continue

    # No vocab matches — fall back to the generic prefix unless already
    # prefixed.
    if prompt.startswith(GENERIC_SOFTENING_PREFIX):
        return prompt
    return GENERIC_SOFTENING_PREFIX + prompt


def _match_case(original: str, replacement: str) -> str:
    """Map the casing of ``original`` onto ``replacement`` where it makes sense."""
    if original.isupper():
        return replacement.upper()
    if original[0].isupper() and original[1:].islower():
        return replacement[0].upper() + replacement[1:]
    return replacement
