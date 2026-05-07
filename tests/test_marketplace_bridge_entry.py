import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_marketplace_includes_bridge_entry():
    data = json.loads((REPO / ".claude-plugin" / "marketplace.json").read_text())
    bridges = [p for p in data["plugins"] if p["name"] == "jack-tar-superpower-bridge"]
    assert len(bridges) == 1
    entry = bridges[0]
    assert entry["version"] == "0.1.0"
    assert entry["source"] == "./plugins/jack-tar-superpower-bridge"


def test_msft_smartart_bumped_to_1_2_0():
    data = json.loads((REPO / "plugins/jack-tar-msft-smartart/.claude-plugin/plugin.json").read_text())
    assert data["version"] == "1.2.0"


def test_deckhand_bumped_to_1_2_0():
    data = json.loads((REPO / "plugins/jack-tar-deckhand/.claude-plugin/plugin.json").read_text())
    assert data["version"] == "1.2.0"


def test_marketplace_msft_smartart_bumped_to_1_2_0():
    data = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
    msft = [p for p in data["plugins"] if p["name"] == "jack-tar-msft-smartart"][0]
    assert msft["version"] == "1.2.0"


def test_marketplace_deckhand_bumped_to_1_2_0():
    data = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
    deckhand = [p for p in data["plugins"] if p["name"] == "jack-tar-deckhand"][0]
    assert deckhand["version"] == "1.2.0"
