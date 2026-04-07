"""Tests for SmartArt JSON schemas — validates both structure and sample data."""

import json
import os
import pytest
import jsonschema

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'schemas')


def _load_schema(name):
    with open(os.path.join(SCHEMA_DIR, name)) as f:
        return json.load(f)


class TestSmartArtRecommendationsSchema:
    def test_valid_recommendation(self):
        schema = _load_schema('smartart_recommendations.schema.json')
        doc = {
            "slides": [
                {
                    "slide_number": 5,
                    "recommendations": [
                        {
                            "graphic_type": "flowchart",
                            "enrichment_tier": "ai_background",
                            "engine": "mermaid",
                            "rationale": "Sequential process suits flowchart",
                            "confidence": 0.85,
                            "data_hint": "4 sequential steps"
                        }
                    ],
                    "approval_status": "approved",
                    "selected_index": 0
                }
            ]
        }
        jsonschema.validate(doc, schema)

    def test_rejects_invalid_graphic_type(self):
        schema = _load_schema('smartart_recommendations.schema.json')
        doc = {
            "slides": [
                {
                    "slide_number": 1,
                    "recommendations": [
                        {
                            "graphic_type": "invalid_type",
                            "enrichment_tier": "pure_programmatic",
                            "engine": "mermaid",
                            "rationale": "test",
                            "confidence": 0.5,
                            "data_hint": "test"
                        }
                    ],
                    "approval_status": "pending"
                }
            ]
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(doc, schema)


class TestSmartArtSpecSchema:
    def test_valid_mermaid_spec(self):
        schema = _load_schema('smartart_spec.schema.json')
        doc = {
            "specs": [
                {
                    "slide_number": 5,
                    "graphic_type": "flowchart",
                    "engine": "mermaid",
                    "enrichment_tier": "ai_background",
                    "data": {
                        "syntax": "graph TD\n  A[Research] --> B[Design]",
                        "diagram_type": "flowchart",
                        "node_count": 2
                    },
                    "overflow_applied": "none",
                    "style_tokens": {
                        "primary_color": "#1a73e8",
                        "font_family": "Inter"
                    },
                    "validation_status": "valid",
                    "comparator_engines": ["mermaid", "custom_svg"]
                }
            ]
        }
        jsonschema.validate(doc, schema)

    def test_valid_custom_svg_spec(self):
        schema = _load_schema('smartart_spec.schema.json')
        doc = {
            "specs": [
                {
                    "slide_number": 3,
                    "graphic_type": "swot",
                    "engine": "custom_svg",
                    "enrichment_tier": "pure_programmatic",
                    "data": {
                        "quadrants": [
                            {"label": "Strengths", "position": "top_left", "items": ["Brand"]},
                            {"label": "Weaknesses", "position": "top_right", "items": ["Scale"]},
                            {"label": "Opportunities", "position": "bottom_left", "items": ["AI"]},
                            {"label": "Threats", "position": "bottom_right", "items": ["Regulation"]}
                        ]
                    },
                    "overflow_applied": "none",
                    "style_tokens": {"primary_color": "#2B6CB0", "font_family": "Arial"},
                    "validation_status": "valid",
                    "comparator_engines": []
                }
            ]
        }
        jsonschema.validate(doc, schema)


class TestSmartArtManifestSchema:
    def test_valid_manifest_entry(self):
        schema = _load_schema('smartart_manifest.schema.json')
        doc = {
            "graphics": [
                {
                    "smartart_id": "sa-slide-5-flowchart",
                    "slide_number": 5,
                    "graphic_type": "flowchart",
                    "engine_used": "mermaid",
                    "enrichment_tier": "ai_background",
                    "file_path": "./tmp/deck/smartart/slide-5-flowchart.png",
                    "status": "rendered",
                    "dimensions": {"width": 1920, "height": 1080},
                    "alt_text": "Flowchart showing process"
                }
            ]
        }
        jsonschema.validate(doc, schema)


class TestModifiedSchemas:
    def test_slide_outline_accepts_visual_intent(self):
        schema = _load_schema('slide_outline.schema.json')
        doc = {
            "narrative_arc": "situation-complication-resolution",
            "estimated_duration_minutes": 20,
            "slides": [
                {
                    "slide_number": 1,
                    "slide_type": "content",
                    "headline": "Our Process",
                    "visual_intent": "Show the 4-step process as a flowchart",
                    "body_points": ["Research", "Design", "Build", "Launch"]
                }
            ]
        }
        jsonschema.validate(doc, schema)

    def test_strategy_map_accepts_smartart_strategy(self):
        schema = _load_schema('strategy_map.schema.json')
        doc = {
            "approval_mode": "review",
            "slides": [
                {
                    "slide_number": 5,
                    "strategy": "smartart",
                    "rationale": "Process flow suits flowchart",
                    "render_funnel": [],
                    "smartart_config": {
                        "graphic_type": "flowchart",
                        "enrichment_tier": "ai_background",
                        "engine": "mermaid",
                        "comparator_engines": ["mermaid", "custom_svg"]
                    }
                }
            ]
        }
        jsonschema.validate(doc, schema)

    def test_image_manifest_accepts_smartart_ref(self):
        schema = _load_schema('image_manifest.schema.json')
        doc = {
            "images": [
                {
                    "image_id": "img-slide-5-bg-001",
                    "slide_number": 5,
                    "file_path": "./tmp/deck/images/slide-5-bg.png",
                    "status": "generated",
                    "smartart_ref": "sa-slide-5-flowchart"
                }
            ]
        }
        jsonschema.validate(doc, schema)

    def test_qa_report_accepts_smartart_category(self):
        schema = _load_schema('qa_report.schema.json')
        doc = {
            "verdict": "pass",
            "findings": [
                {
                    "slide_number": 5,
                    "severity": "warning",
                    "category": "smartart",
                    "description": "SA-02: Font size 15px below recommended 16px minimum"
                }
            ]
        }
        jsonschema.validate(doc, schema)
