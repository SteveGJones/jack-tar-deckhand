"""Tests for QAReport generation and verdict logic."""

import pytest
from src.qa.report import compute_verdict, generate_report


class TestVerdict:
    def test_pass_when_no_findings(self):
        assert compute_verdict([]) == 'pass'

    def test_pass_with_info_only(self):
        findings = [{'severity': 'info', 'slide_number': 1, 'category': 'consistency',
                      'description': 'test'}]
        assert compute_verdict(findings) == 'pass'

    def test_pass_with_warnings(self):
        findings = [{'severity': 'warning', 'slide_number': 1, 'category': 'margin',
                      'description': 'test'}]
        assert compute_verdict(findings) == 'pass_with_warnings'

    def test_fail_on_error(self):
        findings = [{'severity': 'error', 'slide_number': 1, 'category': 'contrast',
                      'description': 'test'}]
        assert compute_verdict(findings) == 'fail'

    def test_fail_overrides_warnings(self):
        findings = [
            {'severity': 'warning', 'slide_number': 1, 'category': 'margin',
             'description': 'w'},
            {'severity': 'error', 'slide_number': 2, 'category': 'contrast',
             'description': 'e'},
        ]
        assert compute_verdict(findings) == 'fail'


class TestGenerateReport:
    def test_report_has_required_fields(self):
        report = generate_report([], './tmp/deck/output/presentation.pptx', 10)
        assert 'inspected_at' in report
        assert 'pptx_path' in report
        assert 'verdict' in report
        assert 'summary' in report
        assert 'findings' in report

    def test_report_counts_are_correct(self):
        findings = [
            {'severity': 'error', 'slide_number': 1, 'category': 'contrast',
             'description': 'e'},
            {'severity': 'warning', 'slide_number': 2, 'category': 'margin',
             'description': 'w'},
            {'severity': 'info', 'slide_number': 3, 'category': 'consistency',
             'description': 'i'},
        ]
        report = generate_report(findings, 'test.pptx', 5)
        assert report['summary']['errors'] == 1
        assert report['summary']['warnings'] == 1
        assert report['summary']['info'] == 1
        assert report['summary']['total_slides'] == 5

    def test_verdict_matches_findings(self):
        report = generate_report([], 'test.pptx', 3)
        assert report['verdict'] == 'pass'
