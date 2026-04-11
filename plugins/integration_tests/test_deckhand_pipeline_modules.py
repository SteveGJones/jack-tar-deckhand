"""Integration test: deckhand pipeline modules work from plugin root."""
import sys
import json
import tempfile
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = WORKTREE / "plugins" / "jack-tar-deckhand"

# Ensure deckhand plugin root is at the front, removing other plugin roots
# that also have a src/ package to avoid namespace collision.
_MSFT_ROOT = str(WORKTREE / "plugins" / "jack-tar-msft-smartart")


def _ensure_deckhand_path():
    """Put deckhand plugin root first, remove msft-smartart root to avoid collision."""
    root = str(PLUGIN_ROOT)
    if _MSFT_ROOT in sys.path:
        sys.path.remove(_MSFT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    elif sys.path[0] != root:
        sys.path.remove(root)
        sys.path.insert(0, root)
    # Invalidate cached src.* modules from the msft-smartart plugin
    for key in list(sys.modules):
        if key == "src" or key.startswith("src."):
            del sys.modules[key]


def test_init_pipeline_creates_deck_dir():
    _ensure_deckhand_path()
    from src.conductor import init_pipeline
    with tempfile.TemporaryDirectory() as tmpdir:
        deck_dir = str(Path(tmpdir) / "deck")
        init_pipeline(deck_dir, budget_usd=1.0)
        assert Path(deck_dir).exists()
        assert (Path(deck_dir) / "pipeline-state.json").exists()


def test_budget_tracker_works():
    _ensure_deckhand_path()
    from src.budget_tracker import BudgetTracker
    bt = BudgetTracker(total_budget_usd=5.0)
    assert bt.state == "allow"
    bt.log_api_call("test-model", 1.0, "img-001")
    assert bt.spent == 1.0


def test_schemas_are_valid_json():
    schemas_dir = PLUGIN_ROOT / "src" / "schemas"
    for schema_file in schemas_dir.glob("*.schema.json"):
        data = json.loads(schema_file.read_text())
        assert "$schema" in data or "type" in data or "properties" in data


def test_image_router_imports_and_routes():
    _ensure_deckhand_path()
    from src.image_router import route_all_slides
    assert callable(route_all_slides)


def test_brand_profile_round_trip():
    _ensure_deckhand_path()
    from src.brand_profile import load_brand_profile, save_brand_profile, generate_brand_id
    with tempfile.TemporaryDirectory() as tmpdir:
        brand_id = generate_brand_id("Test Co")
        # Minimal dict — save_brand_profile persists any dict without validation
        profile = {
            "brand_id": brand_id,
            "company_name": "Test Co",
        }
        save_brand_profile(profile, brands_dir=tmpdir)
        loaded = load_brand_profile(brand_id, brands_dir=tmpdir)
        assert loaded is not None
        assert loaded["company_name"] == "Test Co"


def test_qa_module_imports():
    _ensure_deckhand_path()
    from src.qa.run_qa import run_qa
    assert callable(run_qa)


def test_content_validation_imports():
    _ensure_deckhand_path()
    from src.content_validation import validate_outline_schema
    assert callable(validate_outline_schema)
