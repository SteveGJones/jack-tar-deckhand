"""Brand profile persistence and validation utilities.

Manages BrandProfile JSON files at ./brands/{brand-id}/brand-profile.json.
Profiles persist across deck sessions for brand reuse.
"""

import json
import os
import re

import jsonschema

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schemas', 'brand_profile.schema.json')
DEFAULT_BRANDS_DIR = './brands'


def generate_brand_id(company_name):
    """Convert a company name to a URL-safe slug."""
    slug = company_name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    slug = slug.strip('-')
    return slug


def _brand_path(brand_id, brands_dir=None):
    """Return the path to a brand profile file."""
    base = brands_dir or DEFAULT_BRANDS_DIR
    return os.path.join(base, brand_id, 'brand-profile.json')


def brand_profile_exists(brand_id, brands_dir=None):
    """Check if a brand profile exists."""
    return os.path.isfile(_brand_path(brand_id, brands_dir))


def load_brand_profile(brand_id, brands_dir=None):
    """Load a brand profile by ID. Returns None if not found."""
    path = _brand_path(brand_id, brands_dir)
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return json.load(f)


def save_brand_profile(profile, brands_dir=None):
    """Save a brand profile to ./brands/{brand-id}/brand-profile.json."""
    brand_id = profile['brand_id']
    path = _brand_path(brand_id, brands_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(profile, f, indent=2)
    return path


def validate_brand_profile(profile):
    """Validate a BrandProfile dict against the JSON schema. Returns list of error messages."""
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    validator = jsonschema.Draft202012Validator(schema)
    return [e.message for e in validator.iter_errors(profile)]
