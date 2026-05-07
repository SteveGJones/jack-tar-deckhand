from pathlib import Path
import re

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = PLUGIN_ROOT / "skills" / "verify" / "SKILL.md"


def test_skill_exists():
    assert SKILL_PATH.exists()


def test_frontmatter_minimal():
    text = SKILL_PATH.read_text()
    assert text.startswith("---")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    assert fm["name"] == "verify"


def test_skill_reports_python_dependencies():
    text = SKILL_PATH.read_text()
    for dep in ("python-pptx", "lxml", "esprima"):
        assert dep in text


def test_skill_reports_plugin_dependencies():
    text = SKILL_PATH.read_text()
    assert "jack-tar-msft-smartart" in text
    assert "jack-tar-deckhand" in text


def test_skill_reports_status_line():
    text = SKILL_PATH.read_text()
    assert "STATUS" in text
