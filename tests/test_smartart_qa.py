"""Tests for SmartArt QA checks."""

import pytest


class TestSA01DataIntegrity:
    def test_all_data_present_passes(self):
        from src.qa.checks.smartart_checks import check_data_integrity
        outline_slide = {'body_points': ['Research', 'Design', 'Build', 'Launch']}
        spec = {
            'engine': 'mermaid',
            'data': {'syntax': 'graph TD\n  A[Research] --> B[Design]\n  B --> C[Build]\n  C --> D[Launch]', 'node_count': 4},
            'overflow_applied': 'none'
        }
        findings = check_data_integrity(outline_slide, spec, slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) == 0

    def test_missing_data_point_fails(self):
        from src.qa.checks.smartart_checks import check_data_integrity
        outline_slide = {'body_points': ['Research', 'Design', 'Build', 'Launch']}
        spec = {
            'engine': 'mermaid',
            'data': {'syntax': 'graph TD\n  A[Research] --> B[Design]', 'node_count': 2},
            'overflow_applied': 'none'
        }
        findings = check_data_integrity(outline_slide, spec, slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) > 0

    def test_overflow_applied_suppresses_error(self):
        from src.qa.checks.smartart_checks import check_data_integrity
        outline_slide = {'body_points': ['A', 'B', 'C', 'D', 'E', 'F', 'G']}
        spec = {
            'engine': 'custom_svg',
            'data': {'quadrants': [{'label': 'S', 'items': ['A', 'B']}]},
            'overflow_applied': 'truncate'
        }
        findings = check_data_integrity(outline_slide, spec, slide_number=3)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) == 0


class TestSA02LabelLegibility:
    def test_good_font_and_contrast_passes(self):
        from src.qa.checks.smartart_checks import check_label_legibility
        svg = '<text font-size="18" fill="#000000">Label</text>'
        findings = check_label_legibility(svg, '#ffffff', slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) == 0

    def test_small_font_fails(self):
        from src.qa.checks.smartart_checks import check_label_legibility
        svg = '<text font-size="10" fill="#000000">Tiny</text>'
        findings = check_label_legibility(svg, '#ffffff', slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) > 0

    def test_low_contrast_fails(self):
        from src.qa.checks.smartart_checks import check_label_legibility
        svg = '<text font-size="18" fill="#cccccc">Low contrast</text>'
        findings = check_label_legibility(svg, '#dddddd', slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) > 0

    def test_warns_for_medium_font(self):
        from src.qa.checks.smartart_checks import check_label_legibility
        svg = '<text font-size="14" fill="#000000">Medium</text>'
        findings = check_label_legibility(svg, '#ffffff', slide_number=5)
        warnings = [f for f in findings if f['severity'] == 'warning']
        assert len(warnings) > 0

    def test_large_text_lower_contrast_threshold(self):
        from src.qa.checks.smartart_checks import check_label_legibility
        # 24px text needs only 3:1 contrast ratio
        svg = '<text font-size="24" fill="#767676">Large text</text>'
        findings = check_label_legibility(svg, '#ffffff', slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        # #767676 on white is ~4.54:1 which passes 3:1 threshold for large text
        assert len(errors) == 0


class TestSA03EnrichmentAlignment:
    def test_enrichment_present_passes(self):
        from src.qa.checks.smartart_checks import check_enrichment_alignment
        manifest_entry = {
            'smartart_id': 'sa-slide-5-flowchart',
            'enrichment_tier': 'ai_background',
            'dimensions': {'width': 1920, 'height': 1080}
        }
        image_manifest = {
            'images': [{
                'image_id': 'img-1',
                'smartart_ref': 'sa-slide-5-flowchart',
                'status': 'generated',
                'dimensions': {'width': 1920, 'height': 1080}
            }]
        }
        findings = check_enrichment_alignment(manifest_entry, image_manifest, slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) == 0

    def test_missing_enrichment_fails(self):
        from src.qa.checks.smartart_checks import check_enrichment_alignment
        manifest_entry = {
            'smartart_id': 'sa-slide-5-flowchart',
            'enrichment_tier': 'ai_background',
            'dimensions': {'width': 1920, 'height': 1080}
        }
        image_manifest = {'images': []}
        findings = check_enrichment_alignment(manifest_entry, image_manifest, slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) > 0

    def test_pure_programmatic_skips_check(self):
        from src.qa.checks.smartart_checks import check_enrichment_alignment
        manifest_entry = {
            'smartart_id': 'sa-slide-3-swot',
            'enrichment_tier': 'pure_programmatic'
        }
        findings = check_enrichment_alignment(manifest_entry, {'images': []}, slide_number=3)
        assert len(findings) == 0


class TestSA04OverflowHandling:
    def test_no_overflow_passes(self):
        from src.qa.checks.smartart_checks import check_overflow_handling
        spec = {'overflow_applied': 'none'}
        findings = check_overflow_handling(spec, '<text>Normal</text>', slide_number=5)
        assert len(findings) == 0

    def test_truncate_without_indicator_fails(self):
        from src.qa.checks.smartart_checks import check_overflow_handling
        spec = {'overflow_applied': 'truncate'}
        svg = '<text>Item 1</text><text>Item 2</text>'
        findings = check_overflow_handling(spec, svg, slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) > 0

    def test_truncate_with_indicator_passes(self):
        from src.qa.checks.smartart_checks import check_overflow_handling
        spec = {'overflow_applied': 'truncate'}
        svg = '<text>Item 1</text><text>... and 3 more</text>'
        findings = check_overflow_handling(spec, svg, slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) == 0


class TestSA05Accessibility:
    def test_accessible_svg_passes(self):
        from src.qa.checks.smartart_checks import check_accessibility
        svg = '<svg><title>SWOT Analysis</title><desc>Four quadrant diagram</desc><g role="img" aria-label="Strengths"></g></svg>'
        manifest_entry = {'alt_text': 'SWOT diagram'}
        findings = check_accessibility(svg, manifest_entry, slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) == 0

    def test_missing_title_fails(self):
        from src.qa.checks.smartart_checks import check_accessibility
        svg = '<svg><desc>Description</desc></svg>'
        manifest_entry = {'alt_text': 'Chart'}
        findings = check_accessibility(svg, manifest_entry, slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) > 0

    def test_missing_alt_text_fails(self):
        from src.qa.checks.smartart_checks import check_accessibility
        svg = '<svg><title>Chart</title><desc>A chart</desc></svg>'
        manifest_entry = {}
        findings = check_accessibility(svg, manifest_entry, slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) > 0

    def test_empty_title_fails(self):
        from src.qa.checks.smartart_checks import check_accessibility
        svg = '<svg><title></title><desc>Desc</desc></svg>'
        manifest_entry = {'alt_text': 'Chart'}
        findings = check_accessibility(svg, manifest_entry, slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) > 0
