"""Regression guards for the verify-skill paperbanana detection contract.

The verify skill at ``skills/verify/SKILL.md`` invokes
``is_paperbanana_available`` via a flat sys.path import shape:

    sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/src')
    from paperbanana_dispatch import is_paperbanana_available

This differs from the package-style import used by
``test_paperbanana_dispatch.py`` (``from src.paperbanana_dispatch``).
If anyone renames ``paperbanana_dispatch.py`` or moves it into a
sub-package, the package-style tests still pass but the SKILL.md
import breaks silently. These tests pin the contract.

The first test runs the same import as a subprocess so any sys.modules
pollution from the package-style tests cannot mask a real failure.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PLUGIN_ROOT / "src"


def test_verify_skill_import_shape_resolves():
    """SKILL.md-shaped import must resolve to a zero-arg callable returning a bool."""
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(SRC_DIR)!r}); "
        "from paperbanana_dispatch import is_paperbanana_available; "
        "result = is_paperbanana_available(); "
        "assert isinstance(result, bool), type(result); "
        "print('READY' if result else 'NOT_FOUND')"
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
    assert completed.stdout.strip() in {"READY", "NOT_FOUND"}, completed.stdout


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
    """SKILL.md Step 3 must declare an Academic figures capability row."""
    skill_md = PLUGIN_ROOT / "skills" / "verify" / "SKILL.md"
    text = skill_md.read_text()
    assert "Academic figures" in text, (
        "verify SKILL.md no longer mentions Academic figures capability — "
        "contract regressed"
    )


def test_skill_md_does_not_reference_old_plugin_marker():
    """SKILL.md must NOT reference the old filesystem-probe pattern.

    The pre-refactor verify-skill (Ralph's E3) probed for
    ``.claude-plugin/plugin.json`` at three paths under
    ``~/.claude/plugins``. The new detection uses ``find_spec`` +
    ``shutil.which``. This guard catches accidental regressions where
    the old probe sneaks back into the SKILL.md narrative.
    """
    skill_md = PLUGIN_ROOT / "skills" / "verify" / "SKILL.md"
    text = skill_md.read_text()
    assert "PAPERBANANA_ROOT" not in text, (
        "verify SKILL.md still references PAPERBANANA_ROOT — that env var "
        "was dropped in the Task 1 refactor; remove the reference"
    )
    # The new SKILL.md may still mention ".claude-plugin/plugin.json" in
    # explanatory text (e.g. "we used to probe for X"), but the bash
    # block must NOT actually invoke that path.
    bash_blocks_referencing_old_probe = [
        line
        for line in text.splitlines()
        if ".claude/plugins/cache/paperbanana/.claude-plugin/plugin.json" in line
        and not line.strip().startswith(("#", "//", ">", "*", "-"))
    ]
    assert not bash_blocks_referencing_old_probe, (
        "verify SKILL.md bash block still probes the old plugin.json path:\n"
        + "\n".join(bash_blocks_referencing_old_probe)
    )


def test_skill_md_advertises_install_paths():
    """When paperbanana is NOT_FOUND, SKILL.md must surface install guidance."""
    skill_md = PLUGIN_ROOT / "skills" / "verify" / "SKILL.md"
    text = skill_md.read_text()
    assert "pip install" in text, (
        "verify SKILL.md NOT_FOUND case must include pip install guidance"
    )
    assert "paperbanana[google]" in text, (
        "verify SKILL.md must reference paperbanana[google] extra"
    )
    assert "makersuite.google.com" in text or "GOOGLE_API_KEY" in text, (
        "verify SKILL.md must point at the Gemini key setup"
    )
