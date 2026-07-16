"""CI plugin-tests matrix self-guard (issue #124, design review M1).

The ``plugin-tests`` job in ``.github/workflows/validation.yml`` hard-codes
its ``matrix.plugin`` list rather than discovering plugin directories at
runtime. That means a NEW plugin with its own ``tests/`` directory (like
``jack-tar-mlx``) can be added to the repo and silently never run in CI if
nobody remembers to add it to the matrix.

This guard parses the workflow YAML (regex-based — no PyYAML dependency in
this project's requirements) to extract the ``plugin-tests`` job's
``matrix.plugin`` list, and asserts it is a superset of every
``plugins/*/`` directory that has a ``tests/`` subdirectory on disk.

A companion test proves the guard actually fires: it takes the REAL
extracted matrix, removes ``jack-tar-mlx`` from an IN-MEMORY copy, and
asserts the comparison helper raises. Nothing on disk is mutated — the
mutation lives only in a local Python set for the duration of that one
test.
"""
import re
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = WORKTREE / ".github" / "workflows" / "validation.yml"
PLUGINS_DIR = WORKTREE / "plugins"


def _extract_plugin_tests_matrix(workflow_text: str) -> set[str]:
    """Extract the plugin-tests job's matrix.plugin list from the raw
    workflow YAML text via regex (no PyYAML dependency).

    Looks for the ``plugin-tests:`` job block, then the ``plugin:`` matrix
    key inside it, then collects every ``- <name>`` list item until the
    next ``key:`` line (a plain YAML list under a mapping key, indented
    consistently — the shape used at validation.yml:55-68).
    """
    # Isolate the plugin-tests job block up to the next top-level job
    # (a line starting at column 2 with "<word>:" and no further indent,
    # i.e. the next sibling job key).
    job_match = re.search(
        r"^  plugin-tests:\n(.*?)(?=^  [A-Za-z_-]+:\n)",
        workflow_text,
        re.MULTILINE | re.DOTALL,
    )
    assert job_match, "Could not find 'plugin-tests:' job in validation.yml"
    job_block = job_match.group(1)

    matrix_match = re.search(
        r"^\s*plugin:\n((?:\s*-\s*\S+\n)+)",
        job_block,
        re.MULTILINE,
    )
    assert matrix_match, "Could not find 'plugin:' matrix list in plugin-tests job"

    items = re.findall(r"-\s*(\S+)", matrix_match.group(1))
    return set(items)


def _plugins_with_tests_dir(plugins_dir: Path) -> set[str]:
    return {
        p.name for p in plugins_dir.iterdir()
        if p.is_dir() and (p / "tests").is_dir()
    }


def _assert_matrix_covers_plugins(matrix: set[str], plugins_with_tests: set[str]) -> None:
    missing = plugins_with_tests - matrix
    assert not missing, (
        f"Plugin(s) with a tests/ dir are missing from the plugin-tests CI "
        f"matrix: {sorted(missing)} — add them to "
        f".github/workflows/validation.yml's plugin-tests matrix.plugin list"
    )


def test_workflow_file_exists():
    assert WORKFLOW_PATH.exists(), f"Missing CI workflow: {WORKFLOW_PATH}"


def test_extracts_known_plugins_from_real_workflow():
    text = WORKFLOW_PATH.read_text()
    matrix = _extract_plugin_tests_matrix(text)
    # Sanity: the extraction itself must actually find entries, not just
    # silently return an empty set.
    assert "jack-tar-deckhand" in matrix
    assert "jack-tar-mlx" in matrix


def test_matrix_is_superset_of_plugins_with_tests_dir():
    """The real guard: every plugins/*/tests/ dir on disk must be covered
    by the real CI matrix. This is the assertion that would have caught
    jack-tar-mlx being left out of validation.yml."""
    text = WORKFLOW_PATH.read_text()
    matrix = _extract_plugin_tests_matrix(text)
    plugins_with_tests = _plugins_with_tests_dir(PLUGINS_DIR)
    # integration_tests itself is not a plugin package (no plugin.json) and
    # is exercised by its own dedicated CI job, not the plugin-tests matrix.
    plugins_with_tests.discard("integration_tests")
    _assert_matrix_covers_plugins(matrix, plugins_with_tests)


def test_self_guard_fires_when_plugin_removed_from_matrix():
    """Mutation-check (T6 DoD): prove the guard is not a tautology.

    Takes the REAL matrix and REAL on-disk plugin set, removes
    'jack-tar-mlx' from an in-memory copy of the matrix only, and asserts
    the comparison helper raises. No file on disk is touched — the
    'mutation' is a local Python set copy scoped to this test.
    """
    text = WORKFLOW_PATH.read_text()
    real_matrix = _extract_plugin_tests_matrix(text)
    plugins_with_tests = _plugins_with_tests_dir(PLUGINS_DIR)
    plugins_with_tests.discard("integration_tests")
    assert "jack-tar-mlx" in plugins_with_tests, (
        "Precondition failed: jack-tar-mlx must have a tests/ dir on disk "
        "for this mutation check to be meaningful"
    )

    mutated_matrix = real_matrix - {"jack-tar-mlx"}

    try:
        _assert_matrix_covers_plugins(mutated_matrix, plugins_with_tests)
    except AssertionError as exc:
        assert "jack-tar-mlx" in str(exc)
    else:
        raise AssertionError(
            "Self-guard did not fire: removing jack-tar-mlx from an "
            "in-memory copy of the matrix should have raised"
        )
