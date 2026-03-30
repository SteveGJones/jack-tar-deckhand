"""Tests for JSON Schema validation of data contracts."""

import json
import os
import pytest
import jsonschema
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


class TestStyleGuideSchema:
    @pytest.fixture
    def schema(self):
        return load_schema('style_guide')

    def test_valid_style_guide(self, schema):
        guide = load_fixture('valid_style_guide')
        validate(instance=guide, schema=schema)

    def test_missing_palette_fails(self, schema):
        guide = {"typography": {"heading_font": "Inter", "body_font": "Inter"}, "layout": {}}
        with pytest.raises(ValidationError, match="palette"):
            validate(instance=guide, schema=schema)

    def test_invalid_color_format_fails(self, schema):
        guide = load_fixture('valid_style_guide')
        guide["palette"]["primary"] = "#FF0000"
        with pytest.raises(ValidationError):
            validate(instance=guide, schema=schema)


class TestSlideOutlineSchema:
    @pytest.fixture
    def schema(self):
        return load_schema('slide_outline')

    def test_valid_outline(self, schema):
        outline = load_fixture('valid_slide_outline')
        validate(instance=outline, schema=schema)

    def test_missing_slides_fails(self, schema):
        outline = {"narrative_arc": "problem-solution", "estimated_duration_minutes": 30}
        with pytest.raises(ValidationError, match="slides"):
            validate(instance=outline, schema=schema)

    def test_invalid_slide_type_fails(self, schema):
        outline = load_fixture('valid_slide_outline')
        outline["slides"][0]["slide_type"] = "invalid_type"
        with pytest.raises(ValidationError):
            validate(instance=outline, schema=schema)


class TestSpeakerNotesSchema:
    @pytest.fixture
    def schema(self):
        return load_schema('speaker_notes')

    def test_valid_notes(self, schema):
        notes = load_fixture('valid_speaker_notes')
        validate(instance=notes, schema=schema)

    def test_missing_notes_array_fails(self, schema):
        with pytest.raises(ValidationError, match="notes"):
            validate(instance={"target_pace_wpm": 130}, schema=schema)


class TestImageManifestSchema:
    @pytest.fixture
    def schema(self):
        return load_schema('image_manifest')

    def test_valid_manifest(self, schema):
        manifest = load_fixture('valid_image_manifest')
        validate(instance=manifest, schema=schema)

    def test_invalid_status_fails(self, schema):
        manifest = load_fixture('valid_image_manifest')
        manifest["images"][0]["status"] = "broken"
        with pytest.raises(ValidationError):
            validate(instance=manifest, schema=schema)


class TestChartManifestSchema:
    @pytest.fixture
    def schema(self):
        return load_schema('chart_manifest')

    def test_valid_manifest(self, schema):
        manifest = load_fixture('valid_chart_manifest')
        validate(instance=manifest, schema=schema)

    def test_invalid_chart_type_fails(self, schema):
        manifest = load_fixture('valid_chart_manifest')
        manifest["charts"][0]["chart_type"] = "sunburst"
        with pytest.raises(ValidationError):
            validate(instance=manifest, schema=schema)


class TestQAReportSchema:
    @pytest.fixture
    def schema(self):
        return load_schema('qa_report')

    def test_valid_report(self, schema):
        report = load_fixture('valid_qa_report')
        validate(instance=report, schema=schema)

    def test_invalid_verdict_fails(self, schema):
        report = {"verdict": "maybe", "findings": []}
        with pytest.raises(ValidationError):
            validate(instance=report, schema=schema)

    def test_invalid_severity_fails(self, schema):
        report = load_fixture('valid_qa_report')
        report["findings"][0]["severity"] = "critical"
        with pytest.raises(ValidationError):
            validate(instance=report, schema=schema)


class TestPipelineStateSchema:
    @pytest.fixture
    def schema(self):
        return load_schema('pipeline_state')

    def test_valid_state(self, schema):
        state = {
            "pipeline_id": "2026-03-29T12:00:00Z",
            "created_at": "2026-03-29T12:00:00Z",
            "status": "running",
            "current_step": "slide-stylist",
            "steps": {
                "validate-brief": {
                    "status": "completed",
                    "started_at": "2026-03-29T12:00:01Z",
                    "completed_at": "2026-03-29T12:00:02Z"
                },
                "slide-stylist": {
                    "status": "running",
                    "started_at": "2026-03-29T12:00:03Z"
                }
            }
        }
        validate(instance=state, schema=schema)

    def test_invalid_status_fails(self, schema):
        state = {
            "pipeline_id": "test",
            "created_at": "2026-03-29T12:00:00Z",
            "status": "crashed",
            "steps": {}
        }
        with pytest.raises(ValidationError):
            validate(instance=state, schema=schema)


class TestBrandProfileSchema:
    def test_valid_profile(self):
        profile = load_fixture('valid_brand_profile')
        schema = load_schema('brand_profile')
        validate(instance=profile, schema=schema)

    def test_missing_brand_id_fails(self):
        schema = load_schema('brand_profile')
        profile = {"company_name": "Test", "palette": {"primary": "FF0000"},
                    "typography": {}, "compliance_mode": "strict",
                    "extracted_at": "2026-03-29T12:00:00Z"}
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=schema)

    def test_invalid_compliance_mode_fails(self):
        profile = load_fixture('valid_brand_profile')
        profile['compliance_mode'] = 'invalid'
        schema = load_schema('brand_profile')
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=schema)


class TestTalkBriefBrandingExtensions:
    def test_branded_brief_validates(self):
        with open(os.path.join(FIXTURE_DIR, 'branded_talk_brief.json')) as f:
            brief = json.load(f)
        schema = load_schema('talk_brief')
        validate(instance=brief, schema=schema)

    def test_brand_id_pattern_enforced(self):
        with open(os.path.join(FIXTURE_DIR, 'branded_talk_brief.json')) as f:
            brief = json.load(f)
        brief['branding']['brand_id'] = 'INVALID CAPS'
        schema = load_schema('talk_brief')
        with pytest.raises(ValidationError):
            validate(instance=brief, schema=schema)


class TestStrategyMapSchema:
    @pytest.fixture
    def schema(self):
        with open('src/schemas/strategy_map.schema.json') as f:
            return json.load(f)

    def test_valid_strategy_map(self, schema):
        data = {
            "created_at": "2026-03-29T12:00:00Z",
            "approval_mode": "review",
            "slides": [
                {
                    "slide_number": 1,
                    "strategy": "full_render",
                    "rationale": "Title slide with dramatic visual",
                    "render_funnel": ["ollama", "cloud_low", "cloud_full"],
                    "speaker_override": None
                }
            ]
        }
        jsonschema.Draft202012Validator(schema).validate(data)

    def test_invalid_strategy_fails(self, schema):
        data = {
            "created_at": "2026-03-29T12:00:00Z",
            "approval_mode": "review",
            "slides": [
                {
                    "slide_number": 1,
                    "strategy": "invalid_strategy",
                    "rationale": "Test",
                    "render_funnel": ["ollama"]
                }
            ]
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(data)

    def test_invalid_approval_mode_fails(self, schema):
        data = {
            "created_at": "2026-03-29T12:00:00Z",
            "approval_mode": "invalid",
            "slides": []
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(data)

    def test_invalid_funnel_stage_fails(self, schema):
        data = {
            "created_at": "2026-03-29T12:00:00Z",
            "approval_mode": "review",
            "slides": [
                {
                    "slide_number": 1,
                    "strategy": "composed",
                    "rationale": "Test",
                    "render_funnel": ["invalid_stage"]
                }
            ]
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(data)


class TestRenderLogSchema:
    @pytest.fixture
    def schema(self):
        with open('src/schemas/render_log.schema.json') as f:
            return json.load(f)

    def test_valid_render_log(self, schema):
        data = {
            "entries": [
                {
                    "slide_number": 1,
                    "strategy": "full_render",
                    "funnel_stage": "ollama",
                    "prompt_hash": "abc123",
                    "model": "x/z-image-turbo",
                    "resolution": "1024x576",
                    "vision_score": 6.5,
                    "iteration": 1,
                    "cost_usd": 0.0,
                    "timestamp": "2026-03-29T12:00:00Z"
                }
            ]
        }
        jsonschema.Draft202012Validator(schema).validate(data)

    def test_missing_entries_fails(self, schema):
        data = {}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(data)

    def test_invalid_funnel_stage_fails(self, schema):
        data = {
            "entries": [
                {
                    "slide_number": 1,
                    "strategy": "full_render",
                    "funnel_stage": "invalid",
                    "prompt_hash": "abc",
                    "model": "test",
                    "resolution": "1024x576",
                    "iteration": 1,
                    "cost_usd": 0.0,
                    "timestamp": "2026-03-29T12:00:00Z"
                }
            ]
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(data)
