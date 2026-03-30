"""Tests for brand profile persistence and validation utilities."""

import json
import os
import shutil
import pytest

from src.brand_profile import (
    load_brand_profile,
    save_brand_profile,
    brand_profile_exists,
    validate_brand_profile,
    generate_brand_id,
)

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')
TEST_BRANDS_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'test-brands')


@pytest.fixture(autouse=True)
def clean_test_brands():
    """Create and clean test brands directory."""
    os.makedirs(TEST_BRANDS_DIR, exist_ok=True)
    yield
    if os.path.exists(TEST_BRANDS_DIR):
        shutil.rmtree(TEST_BRANDS_DIR)


class TestGenerateBrandId:
    def test_lowercases_and_slugifies(self):
        assert generate_brand_id("Acme Corp") == "acme-corp"

    def test_removes_special_chars(self):
        assert generate_brand_id("O'Brien & Sons Ltd.") == "obrien-sons-ltd"

    def test_collapses_multiple_dashes(self):
        assert generate_brand_id("My   Company   Name") == "my-company-name"

    def test_strips_leading_trailing_dashes(self):
        assert generate_brand_id("  Acme  ") == "acme"


class TestSaveAndLoad:
    def test_save_creates_directory_and_file(self):
        profile = json.load(open(os.path.join(FIXTURE_DIR, 'valid_brand_profile.json')))
        save_brand_profile(profile, brands_dir=TEST_BRANDS_DIR)
        expected_path = os.path.join(TEST_BRANDS_DIR, 'nexus-tech', 'brand-profile.json')
        assert os.path.isfile(expected_path)

    def test_load_returns_saved_profile(self):
        profile = json.load(open(os.path.join(FIXTURE_DIR, 'valid_brand_profile.json')))
        save_brand_profile(profile, brands_dir=TEST_BRANDS_DIR)
        loaded = load_brand_profile('nexus-tech', brands_dir=TEST_BRANDS_DIR)
        assert loaded['brand_id'] == 'nexus-tech'
        assert loaded['company_name'] == 'Nexus Technologies'

    def test_load_nonexistent_returns_none(self):
        result = load_brand_profile('nonexistent', brands_dir=TEST_BRANDS_DIR)
        assert result is None


class TestBrandProfileExists:
    def test_returns_false_for_missing(self):
        assert brand_profile_exists('nonexistent', brands_dir=TEST_BRANDS_DIR) is False

    def test_returns_true_for_existing(self):
        profile = json.load(open(os.path.join(FIXTURE_DIR, 'valid_brand_profile.json')))
        save_brand_profile(profile, brands_dir=TEST_BRANDS_DIR)
        assert brand_profile_exists('nexus-tech', brands_dir=TEST_BRANDS_DIR) is True


class TestValidateBrandProfile:
    def test_valid_profile_passes(self):
        profile = json.load(open(os.path.join(FIXTURE_DIR, 'valid_brand_profile.json')))
        errors = validate_brand_profile(profile)
        assert len(errors) == 0

    def test_missing_brand_id_fails(self):
        profile = {"company_name": "Test", "palette": {"primary": "FF0000"},
                    "typography": {}, "compliance_mode": "strict",
                    "extracted_at": "2026-03-29T12:00:00Z"}
        errors = validate_brand_profile(profile)
        assert len(errors) > 0

    def test_invalid_hex_colour_fails(self):
        profile = json.load(open(os.path.join(FIXTURE_DIR, 'valid_brand_profile.json')))
        profile['palette']['primary'] = 'ZZZZZZ'
        errors = validate_brand_profile(profile)
        assert len(errors) > 0
