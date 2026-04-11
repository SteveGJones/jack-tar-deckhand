"""Verify jack-tar-deckhand modules load from plugin directory."""
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))


def test_deckcontext_imports():
    from src.deckcontext import init_deck, write_contract, read_contract
    assert callable(init_deck)


def test_conductor_imports():
    from src.conductor import init_pipeline, pipeline_summary_markdown
    assert callable(init_pipeline)


def test_budget_tracker_imports():
    from src.budget_tracker import BudgetTracker
    assert BudgetTracker is not None


def test_schemas_exist():
    schemas_dir = PLUGIN_ROOT / "src" / "schemas"
    schema_files = list(schemas_dir.glob("*.schema.json"))
    assert len(schema_files) >= 13, f"Expected 13+ schemas, found {len(schema_files)}"


def test_image_router_imports():
    from src.image_router import route_all_slides
    assert callable(route_all_slides)


def test_qa_run_imports():
    from src.qa.run_qa import run_qa
    assert callable(run_qa)


def test_brand_profile_imports():
    from src.brand_profile import load_brand_profile, save_brand_profile
    assert callable(load_brand_profile)


def test_content_validation_imports():
    from src.content_validation import validate_outline_schema
    assert callable(validate_outline_schema)
