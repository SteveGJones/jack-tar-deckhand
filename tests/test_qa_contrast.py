"""Tests for contrast and colour QA checks."""

import pytest
from src.qa.checks.contrast import (
    relative_luminance,
    contrast_ratio,
    simulate_deuteranopia,
    check_clashing_colours,
    check_colourblind_safety,
)


class TestRelativeLuminance:
    def test_black(self):
        assert relative_luminance(0, 0, 0) == pytest.approx(0.0, abs=0.001)

    def test_white(self):
        assert relative_luminance(255, 255, 255) == pytest.approx(1.0, abs=0.01)

    def test_mid_grey(self):
        lum = relative_luminance(128, 128, 128)
        assert 0.1 < lum < 0.5


class TestContrastRatio:
    def test_black_on_white(self):
        ratio = contrast_ratio((0, 0, 0), (255, 255, 255))
        assert ratio == pytest.approx(21.0, abs=0.5)

    def test_same_colour(self):
        ratio = contrast_ratio((128, 128, 128), (128, 128, 128))
        assert ratio == pytest.approx(1.0, abs=0.01)

    def test_symmetry(self):
        r1 = contrast_ratio((255, 0, 0), (0, 0, 255))
        r2 = contrast_ratio((0, 0, 255), (255, 0, 0))
        assert r1 == pytest.approx(r2, abs=0.01)


class TestSimulateDeuteranopia:
    def test_returns_tuple(self):
        result = simulate_deuteranopia(255, 0, 0)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_values_in_range(self):
        result = simulate_deuteranopia(100, 200, 50)
        for c in result:
            assert 0 <= c <= 255

    def test_grey_unchanged(self):
        result = simulate_deuteranopia(128, 128, 128)
        for c in result:
            assert abs(c - 128) < 30  # Approximately preserved


class TestClashingColours:
    def test_no_clash_for_similar_colours(self):
        colours = {(100, 100, 200), (110, 110, 210)}
        issues = check_clashing_colours(colours)
        assert len(issues) == 0

    def test_red_green_clash(self):
        colours = {(200, 20, 20), (20, 200, 20)}
        issues = check_clashing_colours(colours)
        red_green = [i for i in issues if 'Red-green' in i['description']]
        assert len(red_green) > 0

    def test_empty_colours(self):
        issues = check_clashing_colours(set())
        assert len(issues) == 0


class TestColourblindSafety:
    def test_distinguishable_colours(self):
        colours = {(0, 0, 255), (255, 255, 0)}  # Blue and yellow
        issues = check_colourblind_safety(colours)
        assert len(issues) == 0

    def test_indistinguishable_similar_colours(self):
        colours = {(200, 50, 50), (190, 55, 45)}  # Very similar reds
        issues = check_colourblind_safety(colours)
        assert len(issues) > 0
