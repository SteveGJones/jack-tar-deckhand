import pytest

from src.msft_smartart_loader import (
    load_msft_smartart_api,
    MsftSmartArtNotFoundError,
    ALLOWED_SYMBOLS,
)


def test_loads_three_named_symbols():
    api = load_msft_smartart_api()
    assert hasattr(api, "engine")
    assert hasattr(api, "InjectionRequest")
    assert hasattr(api, "inject")
    # Engine has render() function
    assert callable(api.engine.render)
    # InjectionRequest is a dataclass with the fields the bridge uses
    req = api.InjectionRequest(slide_number=1, carrier_pptx="x.pptx",
                                placeholder_name="SMARTART:foo")
    assert req.slide_number == 1
    assert req.placeholder_name == "SMARTART:foo"


def test_allowed_symbols_is_documented_explicitly():
    # The supply-chain mitigation requires the imported surface to be named.
    assert set(ALLOWED_SYMBOLS) == {"engine.render", "InjectionRequest", "inject"}


def test_load_raises_when_plugin_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("JACK_TAR_SUPERPOWER_BRIDGE_FORCE_MSFT_ROOT", str(tmp_path / "missing"))
    with pytest.raises(MsftSmartArtNotFoundError):
        load_msft_smartart_api()


def test_loader_restores_bridge_src_modules_after_load():
    """Cross-plugin sys.modules contamination guard.

    Before this test, the conftest fixture has put the bridge's plugin path
    on sys.path[0] and may have imported some src.* modules (e.g. src.placeholder).
    The loader temporarily swaps to the msft-smartart path; after it returns,
    bridge's src.* must still resolve to bridge's modules, not msft-smartart's.
    """
    import sys
    # Pre-load a bridge module so we have something to track
    from src.placeholder import MARKER_RE as bridge_marker_re
    bridge_placeholder_id = id(sys.modules.get("src.placeholder"))
    assert bridge_placeholder_id is not None

    api = load_msft_smartart_api()
    assert hasattr(api, "engine")  # actually loaded msft-smartart

    # After load: bridge's src.placeholder must still be the bridge's module
    from src.placeholder import MARKER_RE as marker_re_after
    assert marker_re_after is bridge_marker_re, (
        "bridge's src.placeholder was clobbered by msft-smartart's src.* — "
        "the loader did not restore bridge's modules"
    )


def test_api_fields_match_allowed_symbols_count():
    """I-1 drift guard — if a future change adds a fourth loaded symbol to
    MsftSmartArtAPI, the ALLOWED_SYMBOLS constant must be updated in lockstep
    or this test fails."""
    from src.msft_smartart_loader import MsftSmartArtAPI
    import dataclasses
    field_names = {f.name for f in dataclasses.fields(MsftSmartArtAPI)}
    # Map ALLOWED_SYMBOLS ("engine.render") to dataclass field names ("engine")
    # by taking the prefix before the first dot.
    expected_fields = {s.split(".")[0] for s in ALLOWED_SYMBOLS}
    assert field_names == expected_fields, (
        f"MsftSmartArtAPI fields {field_names} do not match ALLOWED_SYMBOLS "
        f"{expected_fields} — update the constant or the dataclass in lockstep"
    )


def test_loader_logs_resolved_plugin_root(caplog):
    """I-2 troubleshooting hook — the loader must log which plugin_root it picked,
    so stale-cache bugs can be diagnosed."""
    import logging
    with caplog.at_level(logging.INFO, logger="src.msft_smartart_loader"):
        load_msft_smartart_api()
    # At least one INFO record must mention "plugin_root"
    assert any("plugin_root" in rec.getMessage() for rec in caplog.records), (
        f"loader did not log plugin_root; records: {[r.getMessage() for r in caplog.records]}"
    )
