import io
import os
import zipfile
from pathlib import Path

import pytest
from lxml import etree

from src.security import (
    AllowedPathError,
    PptxPreflightError,
    XmlSecurityError,
    resolve_within_allowlist,
    preflight_pptx,
    safe_xml_parser,
    DEFAULT_DECOMPRESSED_CEILING_BYTES,
    DEFAULT_PART_COUNT_CEILING,
    DEFAULT_PER_PART_CEILING_BYTES,
)


# ----- image-path allowlist ----------------------------------------------------

def test_allowlist_accepts_path_inside_allowed_root(tmp_path):
    allowed = tmp_path / "generated"
    allowed.mkdir()
    img = allowed / "hero.png"
    img.write_bytes(b"fake")
    resolved = resolve_within_allowlist(img, allowed_roots=[allowed])
    assert resolved == img.resolve()


def test_allowlist_rejects_path_outside_roots(tmp_path):
    allowed = tmp_path / "generated"
    allowed.mkdir()
    other = tmp_path / "secret.png"
    other.write_bytes(b"x")
    with pytest.raises(AllowedPathError, match="outside the image-path allowlist"):
        resolve_within_allowlist(other, allowed_roots=[allowed])


def test_allowlist_rejects_symlinks(tmp_path):
    allowed = tmp_path / "generated"
    allowed.mkdir()
    target = tmp_path / "actual.png"
    target.write_bytes(b"x")
    link = allowed / "linked.png"
    os.symlink(target, link)
    with pytest.raises(AllowedPathError, match="symlink"):
        resolve_within_allowlist(link, allowed_roots=[allowed])


def test_allowlist_supports_multiple_roots(tmp_path):
    a = tmp_path / "a"; a.mkdir()
    b = tmp_path / "b"; b.mkdir()
    f = b / "x.png"; f.write_bytes(b"x")
    assert resolve_within_allowlist(f, allowed_roots=[a, b]) == f.resolve()


def test_allowlist_handles_relative_paths(tmp_path, monkeypatch):
    allowed = tmp_path / "generated"
    allowed.mkdir()
    img = allowed / "hero.png"
    img.write_bytes(b"x")
    monkeypatch.chdir(tmp_path)
    rel = Path("generated/hero.png")
    assert resolve_within_allowlist(rel, allowed_roots=[allowed]) == img.resolve()


# ----- .pptx pre-flight --------------------------------------------------------

def _build_pptx(tmp_path, parts: dict[str, bytes]) -> Path:
    p = tmp_path / "fake.pptx"
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in parts.items():
            zf.writestr(name, data)
    return p


def test_preflight_passes_for_normal_pptx(tmp_path):
    p = _build_pptx(tmp_path, {"[Content_Types].xml": b"<x/>", "ppt/slide1.xml": b"<x/>"})
    preflight_pptx(p)


def test_preflight_rejects_too_many_parts(tmp_path):
    parts = {f"ppt/slide{i}.xml": b"<x/>" for i in range(DEFAULT_PART_COUNT_CEILING + 5)}
    p = _build_pptx(tmp_path, parts)
    with pytest.raises(PptxPreflightError, match="part count"):
        preflight_pptx(p)


def test_preflight_rejects_oversized_part(tmp_path):
    big = b"A" * (DEFAULT_PER_PART_CEILING_BYTES + 1)
    p = _build_pptx(tmp_path, {"[Content_Types].xml": b"<x/>", "ppt/big.xml": big})
    with pytest.raises(PptxPreflightError, match="part size"):
        preflight_pptx(p)


def test_preflight_rejects_zip_bomb_ratio(tmp_path):
    # Highly compressible payload — zip will compress >100x
    big = b"\0" * (10_000_000)  # 10MB of zeros
    p = _build_pptx(tmp_path, {"[Content_Types].xml": b"<x/>", "ppt/zeros.bin": big})
    # Force the file size to be very small relative to decompressed size
    with pytest.raises(PptxPreflightError, match="ratio"):
        preflight_pptx(p, decompressed_ceiling_bytes=DEFAULT_DECOMPRESSED_CEILING_BYTES,
                      per_part_ceiling_bytes=20_000_000)


def test_preflight_rejects_total_decompressed_ceiling(tmp_path):
    # Lots of small parts each within per-part ceiling, but cumulative exceeds total ceiling
    parts = {f"ppt/p{i}.xml": (b"A" * 1_000_000) for i in range(50)}
    p = _build_pptx(tmp_path, parts)
    with pytest.raises(PptxPreflightError, match="decompressed"):
        preflight_pptx(p, decompressed_ceiling_bytes=10_000_000,
                      part_count_ceiling=200, per_part_ceiling_bytes=20_000_000)


def test_preflight_rejects_missing_file(tmp_path):
    with pytest.raises(PptxPreflightError, match="not a file"):
        preflight_pptx(tmp_path / "missing.pptx")


# ----- hardened XML parser -----------------------------------------------------

def test_safe_xml_parser_disables_entities():
    parser = safe_xml_parser()
    xxe = (
        b'<?xml version="1.0"?>'
        b'<!DOCTYPE r [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>'
        b'<r>&xxe;</r>'
    )
    # Resolution must NOT happen — the entity reference should not expand to file contents.
    tree = etree.fromstring(xxe, parser=parser)
    assert b"root:" not in etree.tostring(tree)


def test_safe_xml_parser_rejects_huge_tree():
    # huge_tree=False rejects deeply nested input (lxml's default limit kicks in)
    parser = safe_xml_parser()
    src = b"<r>" * 50_000 + b"x" + b"</r>" * 50_000
    with pytest.raises((etree.XMLSyntaxError, XmlSecurityError)):
        etree.fromstring(src, parser=parser)
