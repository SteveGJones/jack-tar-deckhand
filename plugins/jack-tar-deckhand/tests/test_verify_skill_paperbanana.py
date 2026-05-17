"""Regression guard for the verify-skill paperbanana detection contract.

The verify skill at ``skills/verify/SKILL.md`` (paperbanana E3) invokes
``is_paperbanana_available`` via a flat sys.path import shape:

    sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/src')
    from paperbanana_dispatch import is_paperbanana_available

This differs from the package-style import used by
``test_paperbanana_dispatch.py`` (``from src.paperbanana_dispatch``).
If anyone renames ``paperbanana_dispatch.py`` or moves it into a
sub-package, the package-style tests still pass but the SKILL.md
import breaks silently. This test pins the contract.

The test runs the same import as a subprocess so any sys.modules
pollution from the package-style tests cannot mask a real failure.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PLUGIN_ROOT / "src"


def test_verify_skill_import_shape_resolves():
    """SKILL.md-shaped import must resolve to a callable returning a bool."""
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(SRC_DIR)!r}); "
        "from paperbanana_dispatch import is_paperbanana_available; "
        "result = is_paperbanana_available(env={}, fs_exists=lambda _p: False); "
        "assert isinstance(result, bool), type(result); "
        "print('AVAILABLE' if result else 'NOT_AVAILABLE')"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, (
        "SKILL.md-style import failed:\n"
        f"  stdout: {completed.stdout!r}\n"
        f"  stderr: {completed.stderr!r}"
    )
    assert completed.stdout.strip() in {"AVAILABLE", "NOT_AVAILABLE"}, completed.stdout


def test_skill_md_references_helper_by_name():
    """SKILL.md must invoke ``is_paperbanana_available`` by its current name.

    Catches drift where the helper is renamed without updating SKILL.md.
    """
    skill_md = PLUGIN_ROOT / "skills" / "verify" / "SKILL.md"
    text = skill_md.read_text()
    assert "is_paperbanana_available" in text, (
        "verify SKILL.md no longer references is_paperbanana_available — "
        "either restore the call or update this regression guard"
    )
    assert "paperbanana_dispatch" in text, (
        "verify SKILL.md no longer imports from paperbanana_dispatch — "
        "either restore the import or update this regression guard"
    )


def test_skill_md_advertises_academic_figure_capability():
    """SKILL.md Step 3 must declare an ACADEMIC FIGURE capability row.

    The plan §6.5 E3 step 1 explicitly requires this row so operators
    can see at a glance whether the academic_figure rendering strategy
    is on full or fallback.
    """
    skill_md = PLUGIN_ROOT / "skills" / "verify" / "SKILL.md"
    text = skill_md.read_text()
    assert "Academic figures" in text or "ACADEMIC FIGURE" in text, (
        "verify SKILL.md no longer mentions Academic figures / ACADEMIC FIGURE "
        "capability — Phase 3 E3 contract regressed"
    )
