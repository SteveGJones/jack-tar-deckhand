"""Tests for JSON Schema validation of data contracts."""

import json
import os
import pytest
from jsonschema import validate, ValidationError

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'schemas')
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def load_schema(name):
    path = os.path.join(SCHEMA_DIR, f'{name}.schema.json')
    with open(path) as f:
        return json.load(f)


def load_fixture(name):
    path = os.path.join(FIXTURE_DIR, f'{name}.json')
    with open(path) as f:
        return json.load(f)


class TestTalkBriefSchema:
    @pytest.fixture
    def schema(self):
        return load_schema('talk_brief')

    def test_valid_minimal_brief(self, schema):
        brief = {
            "topic": "Building AI Agents",
            "audience": "Software engineers",
            "duration_minutes": 30
        }
        validate(instance=brief, schema=schema)

    def test_valid_full_brief(self, schema):
        brief = load_fixture('valid_talk_brief')
        validate(instance=brief, schema=schema)

    def test_missing_topic_fails(self, schema):
        brief = {"audience": "Engineers", "duration_minutes": 30}
        with pytest.raises(ValidationError, match="topic"):
            validate(instance=brief, schema=schema)

    def test_missing_audience_fails(self, schema):
        brief = {"topic": "AI Agents", "duration_minutes": 30}
        with pytest.raises(ValidationError, match="audience"):
            validate(instance=brief, schema=schema)

    def test_missing_duration_fails(self, schema):
        brief = {"topic": "AI Agents", "audience": "Engineers"}
        with pytest.raises(ValidationError, match="duration_minutes"):
            validate(instance=brief, schema=schema)

    def test_invalid_duration_fails(self, schema):
        brief = {"topic": "AI Agents", "audience": "Engineers", "duration_minutes": 7}
        with pytest.raises(ValidationError):
            validate(instance=brief, schema=schema)

    def test_invalid_tone_fails(self, schema):
        brief = {
            "topic": "AI Agents",
            "audience": "Engineers",
            "duration_minutes": 30,
            "tone": "angry"
        }
        with pytest.raises(ValidationError):
            validate(instance=brief, schema=schema)

    def test_invalid_color_format_fails(self, schema):
        brief = {
            "topic": "AI Agents",
            "audience": "Engineers",
            "duration_minutes": 30,
            "branding": {"primary_color": "#FF0000"}
        }
        with pytest.raises(ValidationError):
            validate(instance=brief, schema=schema)

    def test_too_many_takeaways_fails(self, schema):
        brief = {
            "topic": "AI Agents",
            "audience": "Engineers",
            "duration_minutes": 30,
            "key_takeaways": ["one", "two", "three", "four", "five", "six"]
        }
        with pytest.raises(ValidationError):
            validate(instance=brief, schema=schema)

    def test_short_topic_fails(self, schema):
        brief = {"topic": "AI", "audience": "Engineers", "duration_minutes": 30}
        with pytest.raises(ValidationError):
            validate(instance=brief, schema=schema)
