"""Verify jack-tar-cloud modules load from plugin directory."""
import sys
from pathlib import Path

# Inject plugin root into sys.path
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))


def test_provider_discovery_imports():
    from src.provider_discovery import discover_providers
    assert callable(discover_providers)


def test_prompt_translator_imports():
    from src.prompt_translator import translate_prompt
    assert callable(translate_prompt)


def test_generate_cloud_image_imports():
    from src.generate_cloud_image import generate_cloud_image
    assert callable(generate_cloud_image)


def test_generate_cloud_icon_imports():
    from src.generate_cloud_icon import generate_cloud_icon
    assert callable(generate_cloud_icon)
