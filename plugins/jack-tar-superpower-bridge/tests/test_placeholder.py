import pytest
from src.placeholder import (
    MARKER_RE,
    parse_marker,
    is_marker_name,
    find_duplicate_marker_ids,
)
from src.slide_facts import Marker, SlideFacts


def test_grammar_lowercase_only_after_colon():
    assert MARKER_RE.match("IMAGE:agent-architecture") is not None
    assert MARKER_RE.match("SMARTART:three_pillars") is not None
    assert MARKER_RE.match("BG:dramatic-opening") is not None


def test_grammar_rejects_uppercase_in_identifier():
    assert MARKER_RE.match("IMAGE:AgentArchitecture") is None


def test_grammar_rejects_unknown_prefix():
    assert MARKER_RE.match("LOGO:hero") is None


def test_grammar_rejects_empty_identifier():
    assert MARKER_RE.match("IMAGE:") is None


def test_grammar_rejects_disallowed_chars():
    assert MARKER_RE.match("IMAGE:foo bar") is None
    assert MARKER_RE.match("IMAGE:foo.bar") is None
    assert MARKER_RE.match("IMAGE:foo/bar") is None


def test_parse_marker_returns_kind_and_identifier():
    kind, ident = parse_marker("SMARTART:three-pillars")
    assert kind == "SMARTART"
    assert ident == "three-pillars"


def test_parse_marker_returns_none_on_non_marker():
    assert parse_marker("Body Text 4") is None


def test_is_marker_name_true_false():
    assert is_marker_name("IMAGE:foo") is True
    assert is_marker_name("Title 1") is False


def test_find_duplicate_marker_ids_flags_dupes():
    slides = [
        SlideFacts(slide_index=1, text_content="", markers=[
            Marker("IMAGE", "foo", 0, 0, 0, 0),
        ]),
        SlideFacts(slide_index=3, text_content="", markers=[
            Marker("IMAGE", "foo", 0, 0, 0, 0),
            Marker("BG", "bar", 0, 0, 0, 0),
        ]),
    ]
    dupes = find_duplicate_marker_ids(slides)
    assert dupes == ["IMAGE:foo"]


def test_find_duplicate_marker_ids_empty_when_unique():
    slides = [
        SlideFacts(slide_index=1, text_content="", markers=[
            Marker("IMAGE", "foo", 0, 0, 0, 0),
        ]),
        SlideFacts(slide_index=2, text_content="", markers=[
            Marker("IMAGE", "bar", 0, 0, 0, 0),
        ]),
    ]
    assert find_duplicate_marker_ids(slides) == []
