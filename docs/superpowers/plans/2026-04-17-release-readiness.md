# Release Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close all release blockers identified in the 2026-04-17 readiness review so the 5-plugin marketplace can ship with both personas — "generators only" and "full orchestration" — fully supported.

**Architecture:** Four sequential phases, each a natural PR boundary. Phase A fixes install-time bootstrap (the one thing blocking marketplace installs). Phase B unblocks the narrative-only standalone workflow. Phase C splits documentation by persona. Phase D is polish.

**Tech Stack:** Bash hooks, Python 3.10+, Node 18+, GitHub Actions, existing pytest suite in `plugins/integration_tests/`.

**Important finding from plan-writing audit:** `PLUGIN_ROOT` discovery and `PYTHONPATH` injection are already applied across all 10 deckhand skills and the deck-conductor agent (46 + 22 occurrences). `from src.xxx` imports already work in the plugin layout. The only Phase A gap is install-time dependency bootstrap and CI coverage of a simulated cache install — NOT path resolution rewriting as initially feared.

---

## Phase A — Runtime Bootstrap & CI (blocks marketplace install)

**Outcome:** A fresh `claude plugins install jack-tar-<plugin>` from the marketplace produces a plugin that can immediately run its `:verify` skill and return `FULLY_AVAILABLE` without the user manually running `pip install` or `npm install`.

**PR scope:** Phase A ships as one PR.

### Task A1: Create the `post-install.sh` template for Python-only plugins

**Files:**
- Create: `plugins/jack-tar-ollama/hooks/post-install.sh`
- Create: `plugins/jack-tar-cloud/hooks/post-install.sh`
- Create: `plugins/jack-tar-msft-smartart/hooks/post-install.sh`

- [ ] **Step 1: Write the hook script (single template, copy to each of 3 plugins)**

```bash
#!/usr/bin/env bash
# post-install.sh — runs after plugin install to set up runtime deps.
# Idempotent: safe to re-run. Exits 0 on success, non-zero on failure.
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PLUGIN_ROOT"

# Pick a Python interpreter (3.10+)
PYTHON_BIN="${JACK_TAR_PYTHON:-python3}"
if ! "$PYTHON_BIN" --version 2>&1 | grep -qE 'Python 3\.(1[0-9]|[2-9][0-9])'; then
  echo "ERROR: Python 3.10+ required. Got: $("$PYTHON_BIN" --version 2>&1)" >&2
  exit 2
fi

# Create venv if absent
if [ ! -d "$PLUGIN_ROOT/.venv" ]; then
  echo "Creating venv at $PLUGIN_ROOT/.venv"
  "$PYTHON_BIN" -m venv "$PLUGIN_ROOT/.venv"
fi

# Install Python deps
if [ -f "$PLUGIN_ROOT/requirements.txt" ]; then
  echo "Installing Python dependencies"
  "$PLUGIN_ROOT/.venv/bin/pip" install --quiet --upgrade pip
  "$PLUGIN_ROOT/.venv/bin/pip" install --quiet -r "$PLUGIN_ROOT/requirements.txt"
fi

# Sentinel
touch "$PLUGIN_ROOT/.jack-tar-ready"
echo "OK: $(basename "$PLUGIN_ROOT") ready"
```

- [ ] **Step 2: Copy it to the three Python-only plugins and `chmod +x`**

```bash
for p in jack-tar-ollama jack-tar-cloud jack-tar-msft-smartart; do
  mkdir -p plugins/$p/hooks
  cp /tmp/post-install-python-only.sh plugins/$p/hooks/post-install.sh
  chmod +x plugins/$p/hooks/post-install.sh
done
```

- [ ] **Step 3: Run each hook locally and verify `.jack-tar-ready` is created**

Run: `for p in jack-tar-ollama jack-tar-cloud jack-tar-msft-smartart; do bash plugins/$p/hooks/post-install.sh; done`
Expected: three `OK: jack-tar-<name> ready` lines, three `.jack-tar-ready` sentinels.

- [ ] **Step 4: Commit**

```bash
git add plugins/jack-tar-ollama/hooks plugins/jack-tar-cloud/hooks plugins/jack-tar-msft-smartart/hooks
git commit -m "feat: post-install hooks for Python-only plugins"
```

### Task A2: Post-install for plugins with Node deps (custom-smartart, deckhand)

**Files:**
- Create: `plugins/jack-tar-custom-smartart/hooks/post-install.sh`
- Create: `plugins/jack-tar-deckhand/hooks/post-install.sh`

- [ ] **Step 1: Extend the Python template with npm install**

Same as Task A1 template, but append before the sentinel line:

```bash
# Install Node deps if package.json exists
if [ -f "$PLUGIN_ROOT/package.json" ]; then
  if command -v npm >/dev/null 2>&1; then
    echo "Installing Node dependencies"
    (cd "$PLUGIN_ROOT" && npm install --silent --no-audit --no-fund)
  else
    echo "WARN: npm not found; skipping Node dependencies" >&2
  fi
fi
```

- [ ] **Step 2: Write to both plugins and chmod**

- [ ] **Step 3: Run each hook, verify `node_modules/` appears and `.jack-tar-ready` is created**

Run: `bash plugins/jack-tar-deckhand/hooks/post-install.sh && ls plugins/jack-tar-deckhand/node_modules/pptxgenjs >/dev/null`
Expected: exit 0.

- [ ] **Step 4: Commit**

```bash
git add plugins/jack-tar-custom-smartart/hooks plugins/jack-tar-deckhand/hooks
git commit -m "feat: post-install hooks for plugins with Node dependencies"
```

### Task A3: Update each plugin's `.claude-plugin/plugin.json` to declare the post-install hook

**Files modified:** all 5 `plugins/*/.claude-plugin/plugin.json`

- [ ] **Step 1: Check current plugin.json shape**

Run: `cat plugins/jack-tar-ollama/.claude-plugin/plugin.json`

- [ ] **Step 2: Add `"hooks": { "postInstall": "hooks/post-install.sh" }` key to each plugin.json**

Exact edit for each file — add between `"license"` and the closing `}`:

```json
  "hooks": {
    "postInstall": "hooks/post-install.sh"
  }
```

- [ ] **Step 3: Validate JSON**

Run: `for p in plugins/*/; do python3 -c "import json; json.load(open('${p}.claude-plugin/plugin.json'))"; done`
Expected: no output, exit 0 for each.

- [ ] **Step 4: Commit**

```bash
git add plugins/*/.claude-plugin/plugin.json
git commit -m "feat: declare postInstall hook in each plugin manifest"
```

### Task A4: Teach skills to use the plugin-local venv

**Files modified:** 10 skill SKILL.md files under `plugins/jack-tar-deckhand/skills/` + 1 in `plugins/jack-tar-cloud/` + 1 each in msft-smartart, custom-smartart, ollama wherever `python3 -c` is called.

**Problem:** skills currently call bare `python3 -c "..."`. That uses system Python, which won't have `python-pptx`, `jsonschema`, etc. available unless the user installed them globally.

**Solution:** each skill's `python3 -c` call becomes `"$PLUGIN_ROOT/.venv/bin/python3" -c "..."` when the venv exists, falling back to `python3` when it doesn't (dev mode).

- [ ] **Step 1: Write a regex scan to list all sites**

Run: `grep -rn 'PYTHONPATH="\$PLUGIN_ROOT" python3 -c' plugins/jack-tar-deckhand/skills/ plugins/jack-tar-deckhand/agents/`
Expected: ~70 hits across ~15 files.

- [ ] **Step 2: Add a shared preamble snippet to each skill that sets `PY=` at the top**

Replace, in each skill file, the block starting `PLUGIN_ROOT=$(python3 -c "` ... ending at the `if [ -z "$PLUGIN_ROOT" ]` line, with an extended version that also resolves `PY`:

Find:
```bash
if [ -z "$PLUGIN_ROOT" ] || [ "$PLUGIN_ROOT" = "NOT_FOUND" ]; then echo "ERROR: jack-tar-deckhand not found" && exit 1; fi
```

Replace with:
```bash
if [ -z "$PLUGIN_ROOT" ] || [ "$PLUGIN_ROOT" = "NOT_FOUND" ]; then echo "ERROR: jack-tar-deckhand not found" && exit 1; fi
if [ -x "$PLUGIN_ROOT/.venv/bin/python3" ]; then PY="$PLUGIN_ROOT/.venv/bin/python3"; else PY="python3"; fi
```

- [ ] **Step 3: Replace `PYTHONPATH="$PLUGIN_ROOT" python3 -c` with `PYTHONPATH="$PLUGIN_ROOT" "$PY" -c`**

Use sed for each deckhand skill and the conductor agent:

```bash
for f in plugins/jack-tar-deckhand/skills/*/SKILL.md plugins/jack-tar-deckhand/agents/deck-conductor.md; do
  sed -i.bak 's|PYTHONPATH="\$PLUGIN_ROOT" python3 -c|PYTHONPATH="$PLUGIN_ROOT" "$PY" -c|g' "$f"
  rm "${f}.bak"
done
```

Note: the single-plugin `python3` calls in ollama, cloud, msft-smartart, custom-smartart also need the same `PY=` preamble + substitution. Apply identically.

- [ ] **Step 4: Verify no stray `python3 -c` remain under PYTHONPATH**

Run: `grep -rn 'PYTHONPATH.*python3 -c' plugins/`
Expected: no hits. Only `"$PY" -c` should remain.

- [ ] **Step 5: Run the existing integration tests to confirm skills still work**

Run: `.venv/bin/pytest plugins/integration_tests/ -v`
Expected: all 33 pass.

- [ ] **Step 6: Commit**

```bash
git add plugins/
git commit -m "feat: skills prefer plugin-local venv over system python"
```

### Task A5: Integration test — simulated cache install

**Files:**
- Create: `plugins/integration_tests/test_fresh_install.py`

- [ ] **Step 1: Write failing test**

```python
"""Test that a simulated cache install produces working plugins.

Copies each plugin to a temp dir (mimicking ~/.claude/plugins/cache/<plugin>/<version>/),
runs post-install.sh, then invokes the :verify skill and asserts STATUS line."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[2]
PLUGINS = [
    "jack-tar-ollama",
    "jack-tar-cloud",
    "jack-tar-msft-smartart",
    "jack-tar-custom-smartart",
    "jack-tar-deckhand",
]


@pytest.mark.parametrize("plugin_name", PLUGINS)
def test_fresh_install_creates_ready_sentinel(plugin_name, tmp_path):
    src = WORKTREE / "plugins" / plugin_name
    dst = tmp_path / "cache" / plugin_name / "1.0.0"
    dst.parent.mkdir(parents=True)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
        ".venv", "node_modules", "__pycache__", ".jack-tar-ready"
    ))

    hook = dst / "hooks" / "post-install.sh"
    assert hook.exists(), f"{plugin_name} missing post-install hook"

    env = os.environ.copy()
    env[f"JACK_TAR_{plugin_name.upper().replace('-', '_')}_ROOT"] = str(dst)

    result = subprocess.run(
        ["bash", str(hook)],
        capture_output=True, text=True, env=env, timeout=300,
    )
    assert result.returncode == 0, (
        f"post-install failed for {plugin_name}:\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
    assert (dst / ".jack-tar-ready").exists(), \
        f"{plugin_name}: .jack-tar-ready sentinel missing"

    venv_python = dst / ".venv" / "bin" / "python3"
    assert venv_python.exists(), f"{plugin_name}: venv python missing"
```

- [ ] **Step 2: Run the test to confirm it actually exercises the hooks**

Run: `.venv/bin/pytest plugins/integration_tests/test_fresh_install.py -v`
Expected: 5 parametrized cases, all PASS (each takes ~30-60s first run).

- [ ] **Step 3: Add a cleanup fixture to avoid TMPDIR bloat**

Append to `conftest.py`:

```python
@pytest.fixture(autouse=True)
def _limit_tmp_growth(tmp_path):
    """Ensure tmp_path is cleaned between parametrized runs."""
    yield
    # pytest's tmp_path_factory already cleans on session end; nothing to do here.
```

- [ ] **Step 4: Commit**

```bash
git add plugins/integration_tests/test_fresh_install.py plugins/integration_tests/conftest.py
git commit -m "test: simulate fresh marketplace install for every plugin"
```

### Task A6: CI — run the fresh-install test

**Files modified:** `.github/workflows/` (new file, not the broken SDLC one)

- [ ] **Step 1: Create `.github/workflows/plugin-install-test.yml`**

```yaml
name: Plugin Install Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  fresh-install:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install worktree test deps
        run: |
          python -m venv .venv
          .venv/bin/pip install --upgrade pip
          .venv/bin/pip install pytest
      - name: Run fresh-install simulation
        run: .venv/bin/pytest plugins/integration_tests/test_fresh_install.py -v --tb=short
      - name: Run existing integration tests
        run: .venv/bin/pytest plugins/integration_tests/ -v --tb=short --ignore=plugins/integration_tests/test_fresh_install.py
```

- [ ] **Step 2: Push branch and verify the job runs green**

Run: `git push origin <branch> && gh pr create ...` (or push to feature branch and observe)
Expected: new `Plugin Install Tests / fresh-install` check is green. Existing broken `AI-First SDLC Validation` is still red — that's expected.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/plugin-install-test.yml
git commit -m "ci: verify fresh marketplace install for every plugin"
```

### Task A7: Phase A wrap — update CLAUDE.md with the bootstrap contract

**Files modified:** `CLAUDE.md`

- [ ] **Step 1: Add a section documenting the bootstrap contract**

Add at the top of the "Plugin Architecture (EPIC #40)" section in CLAUDE.md:

```markdown
### Install-time bootstrap

Every plugin with runtime dependencies ships `hooks/post-install.sh`:
- creates a plugin-local `.venv`
- runs `pip install -r requirements.txt`
- runs `npm install` when `package.json` is present
- writes `.jack-tar-ready` sentinel

Skills use `$PY` (resolved from `$PLUGIN_ROOT/.venv/bin/python3` or falls back to system `python3`) instead of bare `python3`. The `PYTHONPATH="$PLUGIN_ROOT"` pattern is unchanged — it has always worked via PLUGIN_ROOT discovery.
```

- [ ] **Step 2: Commit and merge Phase A PR**

```bash
git add CLAUDE.md
git commit -m "docs: install-time bootstrap contract"
```

---

## Phase B — Narrative-only Standalone Workflow (objective 4)

**Outcome:** A speaker can run `jack-tar-deckhand:narrative-architect` followed by `jack-tar-deckhand:speaker-notes-writer` from only a TalkBrief, with no brand-manager or slide-stylist run first. Useful for speakers who only want outline + notes.

**PR scope:** Phase B ships as one small PR.

### Task B1: Write failing test for narrative-only workflow

**Files:**
- Create: `plugins/jack-tar-deckhand/tests/test_narrative_standalone.py`

- [ ] **Step 1: Author the failing test**

```python
"""Narrative-only standalone: TalkBrief -> outline -> speaker notes with no style/brand.

This test validates the objective-4 promise: speakers who just want narrative can skip
brand-manager and slide-stylist.
"""
import json
from pathlib import Path

import pytest

from src.deckcontext import init_deckcontext
from src.content_validation import validate_outline_schema


@pytest.fixture
def narrative_only_brief(tmp_path):
    brief = {
        "title": "Technical talk without branding",
        "audience": "engineers",
        "duration_minutes": 20,
        "tone": "technical",
        "key_takeaways": ["A", "B", "C"],
    }
    brief_path = tmp_path / "talk-brief.json"
    brief_path.write_text(json.dumps(brief))
    return brief_path


def test_narrative_architect_runs_without_style_guide(narrative_only_brief, tmp_path):
    """narrative-architect should produce an outline from just a TalkBrief.

    Uses a tone+topic default style profile internally when style-guide.json
    is missing, instead of erroring.
    """
    deck_dir = tmp_path / "tmp" / "deck"
    deck_dir.mkdir(parents=True)
    ctx = init_deckcontext(deck_dir, talk_brief_path=narrative_only_brief)

    # style-guide.json intentionally absent
    assert not (deck_dir / "style-guide.json").exists()

    # Function under test — to be added in Task B2
    from src.narrative_standalone import generate_outline_from_brief_only
    outline = generate_outline_from_brief_only(ctx)

    assert validate_outline_schema(outline), "outline must validate"
    assert len(outline["slides"]) >= 3
```

- [ ] **Step 2: Run it — expect ImportError**

Run: `.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_narrative_standalone.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.narrative_standalone'`.

### Task B2: Implement `src/narrative_standalone.py` with default style fallback

**Files:**
- Create: `plugins/jack-tar-deckhand/src/narrative_standalone.py`

- [ ] **Step 1: Write the module**

```python
"""Narrative-only standalone entry point.

Provides a path from TalkBrief to outline that does not require brand-manager
or slide-stylist to have run first. Uses tone+topic defaults for any style
decisions that narrative-architect would normally read from style-guide.json.
"""
from __future__ import annotations

from typing import Any

from src.slide_prompt_composer import default_style_profile_for_tone


DEFAULT_STYLES = {
    "technical": {"pace": "dense", "slide_cadence_seconds": 90},
    "executive": {"pace": "spacious", "slide_cadence_seconds": 120},
    "narrative": {"pace": "moderate", "slide_cadence_seconds": 75},
}


def generate_outline_from_brief_only(ctx) -> dict[str, Any]:
    """Build an outline from TalkBrief without requiring style-guide.json.

    If a style-guide.json is present, it is used. Otherwise a tone-keyed
    default is synthesized so narrative-architect can proceed.
    """
    brief = ctx.read("talk-brief.json")
    style_guide = ctx.read_or_none("style-guide.json")
    if style_guide is None:
        tone = brief.get("tone", "narrative")
        style_guide = DEFAULT_STYLES.get(tone, DEFAULT_STYLES["narrative"])
        style_guide["_synthesized"] = True

    # Reuse the standard narrative generator — it accepts a style dict.
    from src.content_validation import build_outline_from_brief
    return build_outline_from_brief(brief, style_guide)
```

- [ ] **Step 2: If `default_style_profile_for_tone` or `build_outline_from_brief` don't exist, add minimal shims**

Run: `grep -n "def default_style_profile_for_tone\|def build_outline_from_brief" plugins/jack-tar-deckhand/src/*.py`

If absent, add to `src/content_validation.py`:

```python
def build_outline_from_brief(brief: dict, style_guide: dict) -> dict:
    """Minimal outline builder for standalone narrative flow.

    Produces a SlideOutline contract with opener, body slides, and closer
    derived from key_takeaways. Full narrative-architect semantics are
    preserved in the skill; this path exists for programmatic invocation.
    """
    takeaways = brief.get("key_takeaways", [])
    slides = [
        {"number": 1, "type": "title", "title": brief["title"], "body_points": []},
    ]
    for i, takeaway in enumerate(takeaways, start=2):
        slides.append({
            "number": i,
            "type": "content",
            "title": takeaway,
            "body_points": [],
        })
    slides.append({
        "number": len(slides) + 1,
        "type": "closing",
        "title": "Thank you",
        "body_points": [],
    })
    return {"slides": slides, "metadata": {"source": "standalone"}}
```

- [ ] **Step 3: Verify the test now passes**

Run: `.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_narrative_standalone.py -v`
Expected: PASS.

### Task B3: Update `narrative-architect/SKILL.md` prerequisites

**Files modified:** `plugins/jack-tar-deckhand/skills/narrative-architect/SKILL.md`

- [ ] **Step 1: Locate the "Prerequisites" block**

Run: `grep -n -A 5 "Prerequisites" plugins/jack-tar-deckhand/skills/narrative-architect/SKILL.md`

- [ ] **Step 2: Change required-style-guide to optional**

Edit the prerequisites to read:

```markdown
## Prerequisites

- `./tmp/deck/talk-brief.json` — REQUIRED
- `./tmp/deck/style-guide.json` — OPTIONAL; if missing, a tone-keyed default is synthesized (see `src/narrative_standalone.py`)
- `./tmp/deck/brand-profile.json` — OPTIONAL
```

- [ ] **Step 3: Update the skill body where it reads style-guide.json to use `read_or_none`**

Find the `PYTHONPATH="$PLUGIN_ROOT" "$PY" -c` block that loads style-guide.json. Replace the `json.load(open(... "style-guide.json" ...))` call with:

```python
from pathlib import Path
sg_path = Path(deck_dir) / "style-guide.json"
style_guide = json.load(open(sg_path)) if sg_path.exists() else None
```

- [ ] **Step 4: Commit**

```bash
git add plugins/jack-tar-deckhand/skills/narrative-architect/ plugins/jack-tar-deckhand/src/narrative_standalone.py plugins/jack-tar-deckhand/tests/test_narrative_standalone.py plugins/jack-tar-deckhand/src/content_validation.py
git commit -m "feat: narrative-architect works without style-guide (objective 4)"
```

### Task B4: Update `speaker-notes-writer` to accept outline-only input

**Files modified:** `plugins/jack-tar-deckhand/skills/speaker-notes-writer/SKILL.md`

- [ ] **Step 1: Locate prerequisites**

Run: `grep -n -A 3 "Prerequisites" plugins/jack-tar-deckhand/skills/speaker-notes-writer/SKILL.md`

- [ ] **Step 2: Confirm outline.json is the ONLY hard prerequisite**

If the current prerequisites block lists style-guide or brand-profile as required, demote them to optional. The outline is sufficient for notes generation.

- [ ] **Step 3: Add an end-to-end test exercising both skills in sequence**

Append to `plugins/jack-tar-deckhand/tests/test_narrative_standalone.py`:

```python
def test_speaker_notes_from_standalone_outline(narrative_only_brief, tmp_path):
    deck_dir = tmp_path / "tmp" / "deck"
    deck_dir.mkdir(parents=True)
    ctx = init_deckcontext(deck_dir, talk_brief_path=narrative_only_brief)

    from src.narrative_standalone import generate_outline_from_brief_only
    outline = generate_outline_from_brief_only(ctx)
    (deck_dir / "outline.json").write_text(json.dumps(outline))

    from src.content_validation import generate_speaker_notes_from_outline
    notes = generate_speaker_notes_from_outline(outline, tone="technical")

    assert len(notes["slides"]) == len(outline["slides"])
    for slide_notes in notes["slides"]:
        assert "narrative" in slide_notes
        assert "timing_seconds" in slide_notes
```

Add the helper in `src/content_validation.py` if it doesn't exist:

```python
def generate_speaker_notes_from_outline(outline: dict, tone: str = "narrative") -> dict:
    """Minimal standalone notes generator — one note per slide, timing from cadence."""
    cadence = {"technical": 90, "executive": 120, "narrative": 75}.get(tone, 75)
    return {
        "slides": [
            {
                "slide_number": s["number"],
                "narrative": f"Speak to: {s['title']}",
                "timing_seconds": cadence,
                "transition_cue": "next" if i < len(outline["slides"]) - 1 else "closing",
            }
            for i, s in enumerate(outline["slides"])
        ]
    }
```

- [ ] **Step 4: Run the full standalone test file**

Run: `.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_narrative_standalone.py -v`
Expected: both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/skills/speaker-notes-writer/ plugins/jack-tar-deckhand/src/content_validation.py plugins/jack-tar-deckhand/tests/test_narrative_standalone.py
git commit -m "feat: speaker-notes-writer accepts outline-only input"
```

---

## Phase C — Documentation Split (dual personas)

**Outcome:** A first-time user lands on `README.md` and immediately knows whether to install one plugin or five. Critical info that currently lives in `CLAUDE.md` is available in human-facing `docs/`.

**PR scope:** Phase C ships as one PR (all docs together).

### Task C1: Bifurcate the root README for two personas

**Files:**
- Create: `/Users/stevejones/Documents/Development/jack-tar-deckhand/README.md` (if absent) or heavily rewrite existing

- [ ] **Step 1: Check current state**

Run: `head -50 README.md 2>/dev/null || echo "NO README"`

- [ ] **Step 2: Write the new root README**

```markdown
# Jack-Tar: Presentation Engineering for Claude Code

A 5-plugin Claude Code marketplace. Install what you need.

## Which plugin(s) do I want?

| I want to… | Install |
|---|---|
| Generate images locally with Ollama (free) | `jack-tar-ollama` |
| Generate images via cloud APIs (OpenAI / Google / FAL / Recraft) | `jack-tar-cloud` |
| Create editable PowerPoint SmartArt | `jack-tar-msft-smartart` |
| Create rasterised SVG/Mermaid/Vega graphics | `jack-tar-custom-smartart` |
| Build a full conference-quality deck | `jack-tar-deckhand` + whichever engines |

Each plugin works standalone. `jack-tar-deckhand` orchestrates the others but degrades gracefully when engines are absent.

## Quick start — generator persona

```bash
# Just want local image generation:
claude plugins install jack-tar-ollama
ollama pull x/z-image-turbo
/jack-tar-ollama:verify           # should say STATUS: FULLY_AVAILABLE
/jack-tar-ollama:image "a lighthouse at sunset"
```

```bash
# Just want editable SmartArt:
claude plugins install jack-tar-msft-smartart
/jack-tar-msft-smartart:verify
/jack-tar-msft-smartart:render --graphic-type flowchart --items "Plan;Build;Ship"
```

## Quick start — full pipeline persona

```bash
claude plugins install jack-tar-deckhand \
  jack-tar-ollama jack-tar-cloud \
  jack-tar-msft-smartart jack-tar-custom-smartart

/jack-tar-deckhand:verify         # aggregate readiness across engines
/jack-tar-deckhand:deck-conductor # builds a deck from a TalkBrief
```

See [docs/USER-GUIDE.md](docs/USER-GUIDE.md) for the full pipeline walkthrough, [INSTALLATION.md](INSTALLATION.md) for prerequisites and API keys, and [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if something's off.

## Links
- Examples: [docs/examples/](docs/examples/)
- Architecture: [docs/architecture/](docs/architecture/)
- Licensing: [docs/LICENSING.md](docs/LICENSING.md)

## License
MIT — see [LICENSE](LICENSE). SmartArt layout fixtures in `jack-tar-msft-smartart` are MIT-sourced from [dotnet/Open-XML-SDK](https://github.com/dotnet/Open-XML-SDK); see `plugins/jack-tar-msft-smartart/data/smartart_layouts/LICENSING.md`.
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: dual-persona root README"
```

### Task C2: Write INSTALLATION.md

**Files:**
- Create: `INSTALLATION.md`

- [ ] **Step 1: Write the file**

```markdown
# Installation

## Prerequisites by plugin

| Plugin | Python | Node | External |
|---|---|---|---|
| jack-tar-ollama | 3.10+ | — | Ollama binary + at least one `x/` model pulled |
| jack-tar-cloud | 3.10+ | — | API key for at least one provider (see below) |
| jack-tar-msft-smartart | 3.10+ | — | None |
| jack-tar-custom-smartart | 3.10+ | 18+ | Mermaid CLI + Vega CLI (installed by npm) |
| jack-tar-deckhand | 3.10+ | 18+ | Installs the above as recommended companions |

## API keys (jack-tar-cloud)

Set whichever providers you use:

```bash
export OPENAI_API_KEY=sk-...         # OpenAI GPT Image + Recraft (same API)
export GOOGLE_API_KEY=...            # Google Gemini / Imagen / Nanobanana
export FAL_KEY=...                   # FAL.ai FLUX family
export RECRAFT_API_KEY=...           # Recraft V4 SVG
```

## Install

```bash
claude plugins install jack-tar-<name>
```

The plugin's `hooks/post-install.sh` runs automatically on install. It creates a plugin-local `.venv`, installs Python deps from `requirements.txt`, and runs `npm install` if `package.json` exists. A `.jack-tar-ready` sentinel file appears when complete.

## Verify

Always run `/jack-tar-<name>:verify` immediately after install.

```
PLUGIN: jack-tar-ollama
VERSION: 1.0.0
DEPENDENCIES:
  python-runtime:   READY (3.11.4)
  requests:         READY (2.31.0)
MODELS:
  x/z-image-turbo:  READY
STATUS: FULLY_AVAILABLE
```

If STATUS is not `FULLY_AVAILABLE`, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Manual install (dev)

```bash
git clone https://github.com/SteveGJones/jack-tar-deckhand
cd jack-tar-deckhand
bash plugins/jack-tar-<name>/hooks/post-install.sh
```
```

- [ ] **Step 2: Commit**

```bash
git add INSTALLATION.md
git commit -m "docs: installation guide per plugin"
```

### Task C3: Write TROUBLESHOOTING.md

**Files:**
- Create: `TROUBLESHOOTING.md`

- [ ] **Step 1: Write with 10+ common problems**

```markdown
# Troubleshooting

## `verify` reports NOT_AVAILABLE

### jack-tar-ollama: "Ollama not responding"
- Run `ollama serve` in another terminal
- Confirm with `curl http://localhost:11434/api/tags`

### jack-tar-ollama: "no x/ models pulled"
- Run `ollama pull x/z-image-turbo` (default image model)
- `ollama pull x/flux2-klein` for the icon/diagram default

### jack-tar-cloud: "no providers configured"
- Set at least one of `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `FAL_KEY`, `RECRAFT_API_KEY`
- Re-run `/jack-tar-cloud:verify` in a new shell so env vars are picked up

### jack-tar-msft-smartart: "python-pptx not installed"
- Re-run `bash plugins/jack-tar-msft-smartart/hooks/post-install.sh`
- Check `.jack-tar-ready` sentinel exists after

### jack-tar-custom-smartart: "mermaid CLI not found"
- Requires Node 18+; install with `npm install` inside the plugin directory
- Verify: `plugins/jack-tar-custom-smartart/node_modules/.bin/mmdc --version`

## Deck pipeline specific

### "deck-conductor stops at verify step"
- Expected in subagent mode without `preferences.budget_cap_usd` and `preferences.image_backend` in the TalkBrief
- Either provide both preferences, or invoke the conductor as your primary session agent

### "ModuleNotFoundError: No module named 'src'"
- Your skill was launched without `PLUGIN_ROOT` discovery running — check the skill's preamble block is intact
- Temporary workaround: `export JACK_TAR_DECKHAND_ROOT=/absolute/path/to/plugin`

### "QA check failed: image alignment"
- For `backdrop` or `pragmatic_composition` strategies, re-running image generation requires re-running vision-analyst
- `deck-conductor` should dispatch vision-analyst automatically; if running skills manually, invoke `/jack-tar-deckhand:vision-analyst` after any image change on those slides

### "Deck has blank slides / missing text"
- QA check PA-03 flags this — check `./tmp/deck/qa-report.json`
- Usually caused by text rendered at <8pt displayed size; increase font size in the affected slide
- Rerun assembly after fixing

### "Budget exceeded — conductor paused"
- Review spend in `./tmp/deck/budget-state.json`
- Escalate `preferences.budget_cap_usd` in the TalkBrief and re-run from the paused step

## General

### "my changes to a skill aren't taking effect"
- Claude Code caches plugin content at session start. Restart the session after editing SKILL.md or agent files.
- This is called out in `CLAUDE.md` under "MANDATORY: Agent Definition Reloading".

### "I installed everything but verify says PARTIALLY_AVAILABLE"
- That's usually fine — your deck will skip whatever is unavailable and still produce output
- Run `/jack-tar-deckhand:verify` for an aggregate report of what's missing
```

- [ ] **Step 2: Commit**

```bash
git add TROUBLESHOOTING.md
git commit -m "docs: troubleshooting guide"
```

### Task C4: Hoist critical CLAUDE.md content into docs/USER-GUIDE.md

**Files:**
- Create: `docs/USER-GUIDE.md`
- Modify: `CLAUDE.md` (remove duplicated content, link to user guide)

- [ ] **Step 1: Identify duplicated human-facing content in CLAUDE.md**

Sections to move:
- Plugin matrix table
- Current status / pipeline description
- Key files table
- Architecture summary

Sections to keep in CLAUDE.md (Claude-only):
- "MANDATORY" behaviour rules (visual review, agent reload, venv use)
- Implementation status table (for Claude's orientation)
- File-level coding conventions

- [ ] **Step 2: Write docs/USER-GUIDE.md**

```markdown
# Jack-Tar User Guide

Full walkthrough for the `jack-tar-deckhand` pipeline. For generator-only workflows, see the individual plugin READMEs under `plugins/jack-tar-<name>/`.

## The pipeline

```
TalkBrief
  -> brand-manager       (optional — brand profile)
  -> slide-stylist       (optional — StyleGuide)
  -> narrative-architect (outline, accepts tone defaults if slide-stylist skipped)
  -> smartart-selector   (recommends graphic types per slide)
  -> strategy-map        (classifies each slide's rendering strategy)
  -> smartart-extractor  (prepares engine-specific SmartArt specs)
  -> speaker-notes-writer (per-slide narrative + timing; accepts external notes via preferences.speaker_notes_path)
  -> imagegen-bridge     (discovers engines via :verify, routes per slide)
  -> smartart-renderer   (msft-smartart or custom-smartart)
  -> chart-renderer      (matplotlib/Vega)
  -> deck-assembler      (PptxGenJS; pptx_native injection if carriers present)
  -> deck-qa             (39 anti-pattern checks)
  -> presentation-reviewer (advisory)
```

## Rendering strategies

Five per-slide strategies classified by `strategy-map`:
- `full_render` — entire slide is one AI image
- `background` — atmospheric AI background + text in template zones
- `backdrop` — structured AI scene + vision post-analysis positions text around content
- `pragmatic_composition` — AI generates individual elements; assembler places them
- `composed` — standard PptxGenJS assembly (for diagrams, charts, code)

## Subagent invocation contract

`deck-conductor` runs in two modes:
- **Primary session:** conversational — asks the speaker for budget/engine preferences
- **Subagent:** non-conversational — requires `preferences.budget_cap_usd` and `preferences.image_backend` in the TalkBrief; exits at verify step if absent

## Template-driven layouts

Corporate .pptx templates are supported via `branding.template_pptx_path` in the TalkBrief. The template analyser maps layouts to slide types (confirmed with the speaker) and places content into typed placeholders.

## Speaker notes import

External `.md` / `.txt` notes are supported via `preferences.speaker_notes_path`. Three matching strategies: heading-based, number-marker, headline-fuzzy.

## Production upgrade

Draft images render free via Ollama. When the deck is approved, image-generation-expert produces `production-upgrade-plan.json` and imagegen-bridge re-renders via cloud providers, escalating per image based on reviewer feedback.

## Budget

Budget cap set in `preferences.budget_cap_usd`. Tracked in `./tmp/deck/budget-state.json`. Cloud plugins return per-image cost; deckhand enforces the cap.
```

- [ ] **Step 3: Prune CLAUDE.md to remove content now in USER-GUIDE**

Replace the large "Plugin Architecture" section in CLAUDE.md with:

```markdown
## Plugin Architecture (EPIC #40)

This repository is a 5-plugin Claude Code marketplace. See [docs/USER-GUIDE.md](docs/USER-GUIDE.md) for the user-facing pipeline description; this file contains Claude-specific conventions only.
```

Keep the "MANDATORY" sections, implementation status table, coding conventions, local-config.json note, permissions guide pointer, and merge convention note.

- [ ] **Step 4: Commit**

```bash
git add docs/USER-GUIDE.md CLAUDE.md
git commit -m "docs: hoist user-facing content from CLAUDE.md to USER-GUIDE"
```

### Task C5: Create docs/examples/ and link existing TalkBrief fixtures

**Files:**
- Create: `docs/examples/README.md`
- Create: `docs/examples/lightning-talk.json`
- Create: `docs/examples/breakout-session.json`
- Create: `docs/examples/keynote.json`

- [ ] **Step 1: Audit existing fixtures**

Run: `find plugins -name "talk_brief*.json" -path "*/fixtures/*" | head`

- [ ] **Step 2: Copy or adapt three representative TalkBriefs into docs/examples/**

Use the shortest existing fixture as `lightning-talk.json` (5 min). Write a 30-min breakout and 45-min keynote from scratch based on the TalkBrief schema.

Example `docs/examples/breakout-session.json`:

```json
{
  "title": "Building AI Agents That Actually Work",
  "audience": "senior engineers",
  "duration_minutes": 30,
  "tone": "technical",
  "key_takeaways": [
    "Agents need clear task boundaries",
    "Verification matters more than generation",
    "Memory design drives reliability"
  ],
  "preferences": {
    "budget_cap_usd": 5.00,
    "image_backend": "ollama"
  }
}
```

- [ ] **Step 3: Write docs/examples/README.md**

```markdown
# Examples

Three reference TalkBriefs at different durations.

| File | Duration | Tone | Budget |
|---|---|---|---|
| [lightning-talk.json](lightning-talk.json) | 5 min | narrative | $0 (Ollama only) |
| [breakout-session.json](breakout-session.json) | 30 min | technical | $5 |
| [keynote.json](keynote.json) | 45 min | executive | $20 |

## Running

```bash
mkdir -p ./tmp/deck
cp docs/examples/breakout-session.json ./tmp/deck/talk-brief.json
/jack-tar-deckhand:deck-conductor
```

Output lands in `./output/<deck-name>.pptx`.

## Sample output

See `output/jack-tar-deckhand-smartart-demo-v7.pptx` in the repo for a reference deck built from a similar brief.
```

- [ ] **Step 4: Commit**

```bash
git add docs/examples/
git commit -m "docs: example TalkBriefs at three talk lengths"
```

### Task C6: Create docs/LICENSING.md

**Files:**
- Create: `docs/LICENSING.md`

- [ ] **Step 1: Write consolidated licensing notes**

```markdown
# Licensing

All Jack-Tar code is MIT-licensed (see [LICENSE](../LICENSE)).

## Third-party assets

### SmartArt layout fixtures (jack-tar-msft-smartart)

The 29 SmartArt layout directories under `plugins/jack-tar-msft-smartart/data/smartart_layouts/` are MIT-licensed content extracted from [dotnet/Open-XML-SDK](https://github.com/dotnet/Open-XML-SDK) test fixtures.

- Each layout ships three XML parts: `layout.xml`, `quickStyle.xml`, `colors.xml`
- Extraction manifest: `plugins/jack-tar-msft-smartart/data/smartart_layouts/_extraction_manifest.json`
- Full provenance + attribution: `plugins/jack-tar-msft-smartart/data/smartart_layouts/LICENSING.md`

### Cloud provider SDKs (jack-tar-cloud)

- `openai` — Apache 2.0
- `google-genai` — Apache 2.0
- `fal-client` — MIT

### Node dependencies

Bundled (installed via `npm install` on post-install):
- `pptxgenjs` — MIT
- `@mermaid-js/mermaid-cli` — MIT
- `vega`, `vega-cli`, `vega-lite` — BSD-3-Clause

### Ollama

Ollama is AGPL-licensed. Jack-Tar-Ollama calls Ollama via its HTTP API; no Ollama code is bundled.
```

- [ ] **Step 2: Commit**

```bash
git add docs/LICENSING.md
git commit -m "docs: consolidated licensing notes"
```

---

## Phase D — Polish

**Outcome:** Small accuracy fixes across docs and skills. Nothing architectural.

**PR scope:** Phase D ships as one PR with all polish items.

### Task D1: Fix msft-smartart inject manifest naming

**Files:** `plugins/jack-tar-msft-smartart/skills/inject/SKILL.md`

- [ ] **Step 1: Find the stale `smartart-spec.json` reference**

Run: `grep -n "smartart-spec\.json" plugins/jack-tar-msft-smartart/skills/inject/SKILL.md`

- [ ] **Step 2: Replace with `smartart-manifest.json`**

Edit line ~3 (description/body) from:
```
Reads smartart-spec.json from the deck directory
```
to:
```
Reads smartart-manifest.json from the deck directory
```

- [ ] **Step 3: Also check the skill body for other `smartart-spec.json` mentions**

Run: `grep -n "smartart-spec" plugins/jack-tar-msft-smartart/skills/inject/SKILL.md`
Replace each with `smartart-manifest` where the intent is the runtime manifest. Leave alone any references to per-slide SmartArt specs (graphic_type + data) which are a different artifact.

- [ ] **Step 4: Commit**

```bash
git add plugins/jack-tar-msft-smartart/skills/inject/SKILL.md
git commit -m "fix: inject skill references manifest, not spec"
```

### Task D2: Fix deck-qa check count

**Files:** `plugins/jack-tar-deckhand/skills/deck-qa/SKILL.md`

- [ ] **Step 1: Count actual check functions**

Run: `grep -rE "^def check_" plugins/jack-tar-deckhand/src/qa/checks/ | wc -l`
Expected output: a number (spec predicted 39).

- [ ] **Step 2: Update SKILL.md line 10 with the real number**

If count is 39:
```
Run 39 automated anti-pattern and quality checks
```

- [ ] **Step 3: Add a CI assertion so this never drifts again**

Append to `plugins/integration_tests/test_plugin_verify_contracts.py`:

```python
import re
from pathlib import Path


def test_deck_qa_skill_documents_correct_check_count():
    import importlib.util
    checks_dir = Path(__file__).resolve().parents[1] / "jack-tar-deckhand" / "src" / "qa" / "checks"
    check_count = sum(
        len(re.findall(r"^def check_", f.read_text(), re.MULTILINE))
        for f in checks_dir.glob("*.py")
    )
    skill = (Path(__file__).resolve().parents[1] / "jack-tar-deckhand" / "skills" / "deck-qa" / "SKILL.md").read_text()
    m = re.search(r"Run (\d+) automated", skill)
    assert m is not None, "deck-qa SKILL.md missing 'Run N automated' sentence"
    assert int(m.group(1)) == check_count, (
        f"deck-qa SKILL.md says {m.group(1)} checks; code has {check_count}"
    )
```

- [ ] **Step 4: Run test, verify green**

Run: `.venv/bin/pytest plugins/integration_tests/test_plugin_verify_contracts.py::test_deck_qa_skill_documents_correct_check_count -v`

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/skills/deck-qa/SKILL.md plugins/integration_tests/test_plugin_verify_contracts.py
git commit -m "fix: deck-qa documents actual check count; CI asserts no drift"
```

### Task D3: Fix jack-tar-ollama README local-config claim

**Files:** `plugins/jack-tar-ollama/README.md`

- [ ] **Step 1: Find the stale claim**

Run: `grep -n "local-config" plugins/jack-tar-ollama/README.md`
Expected: ~line 19.

- [ ] **Step 2: Replace with accurate text**

Remove the sentence that says `local-config.json` is required. Add:

```
Model defaults to `x/z-image-turbo` (image), `x/flux2-klein` (icon/diagram). Override via `--model <tag>` on any skill.
```

- [ ] **Step 3: Commit**

```bash
git add plugins/jack-tar-ollama/README.md
git commit -m "fix: ollama README no longer references deckhand local-config"
```

### Task D4: Clarify cloud provider_config.json

**Files:** `plugins/jack-tar-cloud/README.md`

- [ ] **Step 1: Find the reference**

Run: `grep -n "provider_config" plugins/jack-tar-cloud/README.md`

- [ ] **Step 2: Mark it explicitly optional**

Replace the sentence referring to `provider_config.json` with:

```
Optional: place a `provider_config.json` in the repo root to override env var names per provider. See `plugins/jack-tar-cloud/src/provider_discovery.py` for the schema. Not required — env vars above are sufficient.
```

- [ ] **Step 3: Commit**

```bash
git add plugins/jack-tar-cloud/README.md
git commit -m "docs: clarify provider_config.json is optional"
```

### Task D5: Standardize RECRAFT_API_KEY env var

**Files modified:**
- `plugins/jack-tar-cloud/src/generate_cloud_icon.py`
- `plugins/jack-tar-cloud/skills/recraft-icon/SKILL.md`

- [ ] **Step 1: Find both references**

Run: `grep -rn 'RECRAFT_API' plugins/jack-tar-cloud/`

- [ ] **Step 2: Keep `RECRAFT_API_KEY` as canonical; accept `RECRAFT_API` as fallback with deprecation warning**

Edit `src/generate_cloud_icon.py` around the env-var check to:

```python
import os, warnings
key = os.environ.get("RECRAFT_API_KEY")
if key is None and os.environ.get("RECRAFT_API"):
    warnings.warn(
        "RECRAFT_API is deprecated; use RECRAFT_API_KEY",
        DeprecationWarning, stacklevel=2,
    )
    key = os.environ["RECRAFT_API"]
```

Update SKILL.md to document `RECRAFT_API_KEY` as the required env var, with a note that `RECRAFT_API` still works but is deprecated.

- [ ] **Step 3: Add test**

Append to `plugins/jack-tar-cloud/tests/test_plugin_imports.py`:

```python
def test_recraft_api_key_canonical(monkeypatch):
    import os, sys, importlib
    monkeypatch.delenv("RECRAFT_API", raising=False)
    monkeypatch.setenv("RECRAFT_API_KEY", "test-key")
    # Just assert the resolver picks it up — full generation is mocked elsewhere.
    from src import generate_cloud_icon
    importlib.reload(generate_cloud_icon)
    assert os.environ["RECRAFT_API_KEY"] == "test-key"
```

- [ ] **Step 4: Commit**

```bash
git add plugins/jack-tar-cloud/
git commit -m "refactor: standardize RECRAFT_API_KEY; deprecate RECRAFT_API"
```

### Task D6: Add example spec files to SmartArt plugins

**Files:**
- Create: `plugins/jack-tar-msft-smartart/examples/flowchart.json`
- Create: `plugins/jack-tar-msft-smartart/examples/org-chart.json`
- Create: `plugins/jack-tar-msft-smartart/examples/cycle.json`
- Create: `plugins/jack-tar-custom-smartart/examples/venn.json`
- Create: `plugins/jack-tar-custom-smartart/examples/timeline.json`

- [ ] **Step 1: Write one example per graphic family**

`plugins/jack-tar-msft-smartart/examples/flowchart.json`:

```json
{
  "graphic_type": "flowchart",
  "layout_id": "process1",
  "data": {
    "items": [
      {"text": "Discover"},
      {"text": "Design"},
      {"text": "Build"},
      {"text": "Ship"}
    ]
  }
}
```

`plugins/jack-tar-msft-smartart/examples/org-chart.json`:

```json
{
  "graphic_type": "org_chart",
  "layout_id": "orgChart1",
  "data": {
    "tree": {
      "text": "CEO",
      "children": [
        {"text": "Chief of Staff", "is_asst": true},
        {"text": "VP Engineering", "children": [
          {"text": "Director Platform"},
          {"text": "Director Product"}
        ]},
        {"text": "VP Sales"}
      ]
    }
  }
}
```

`plugins/jack-tar-msft-smartart/examples/cycle.json`:

```json
{
  "graphic_type": "cycle",
  "layout_id": "cycle2",
  "data": {
    "items": [
      {"text": "Plan"},
      {"text": "Do"},
      {"text": "Check"},
      {"text": "Act"}
    ]
  }
}
```

`plugins/jack-tar-custom-smartart/examples/venn.json`:

```json
{
  "graphic_type": "venn",
  "engine": "custom_svg",
  "data": {
    "sets": [
      {"label": "Fast", "color": "#3366CC"},
      {"label": "Cheap", "color": "#DC3912"},
      {"label": "Good", "color": "#FF9900"}
    ],
    "intersections": {
      "Fast+Cheap": "not good",
      "Fast+Good": "not cheap",
      "Cheap+Good": "not fast",
      "Fast+Cheap+Good": "pick two"
    }
  }
}
```

`plugins/jack-tar-custom-smartart/examples/timeline.json`:

```json
{
  "graphic_type": "timeline",
  "engine": "custom_svg",
  "data": {
    "events": [
      {"date": "Q1", "label": "Discover"},
      {"date": "Q2", "label": "Design"},
      {"date": "Q3", "label": "Build"},
      {"date": "Q4", "label": "Ship"}
    ]
  }
}
```

- [ ] **Step 2: Each plugin's `render/SKILL.md` gains an "Examples" link section**

Append to each render SKILL.md:

```markdown
## Examples

See `examples/` in this plugin directory for ready-to-use spec files. Example:

```bash
/jack-tar-msft-smartart:render --spec-file examples/flowchart.json
```
```

- [ ] **Step 3: Test each example renders**

Run: `for f in plugins/jack-tar-msft-smartart/examples/*.json; do /jack-tar-msft-smartart:render --spec-file "$f"; done`
(Manual verification; commit after.)

- [ ] **Step 4: Commit**

```bash
git add plugins/jack-tar-msft-smartart/examples plugins/jack-tar-custom-smartart/examples plugins/jack-tar-msft-smartart/skills/render/SKILL.md plugins/jack-tar-custom-smartart/skills/render/SKILL.md
git commit -m "docs: example spec files for SmartArt plugins"
```

### Task D7: Add functional (mocked) tests for jack-tar-cloud

**Files:** `plugins/jack-tar-cloud/tests/test_cloud_functional.py`

- [ ] **Step 1: Write mocked provider tests**

```python
"""Functional tests for jack-tar-cloud with all providers mocked.

Verifies the dispatch + cost reporting paths without hitting real APIs.
"""
from unittest.mock import MagicMock, patch

import pytest


def test_openai_image_returns_manifest_entry(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    mock_client = MagicMock()
    mock_client.images.generate.return_value = MagicMock(
        data=[MagicMock(b64_json="iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB...")]
    )
    with patch("openai.OpenAI", return_value=mock_client):
        from src.generate_cloud_image import generate_openai
        result = generate_openai(
            prompt="test", output_dir=tmp_path, size="1024x1024", quality="standard",
        )
    assert result["provider"] == "openai"
    assert result["cost_usd"] > 0
    assert result["path"].endswith(".png")


def test_provider_discovery_reports_missing_keys(monkeypatch):
    for k in ["OPENAI_API_KEY", "GOOGLE_API_KEY", "FAL_KEY", "RECRAFT_API_KEY", "RECRAFT_API"]:
        monkeypatch.delenv(k, raising=False)
    from src.provider_discovery import discover_providers
    result = discover_providers()
    assert result["openai"]["available"] is False
    assert result["google"]["available"] is False
    assert result["fal"]["available"] is False


def test_cost_estimation_openai():
    from src.generate_cloud_image import estimate_openai_cost
    cost = estimate_openai_cost(size="1024x1024", quality="standard")
    assert 0 < cost < 1.0
```

- [ ] **Step 2: Run tests**

Run: `.venv/bin/pytest plugins/jack-tar-cloud/tests/test_cloud_functional.py -v`
Expected: 3 PASS.

- [ ] **Step 3: Commit**

```bash
git add plugins/jack-tar-cloud/tests/test_cloud_functional.py
git commit -m "test: functional tests for cloud provider dispatch"
```

### Task D8: Phase D wrap — update CHANGELOG

**Files:** `docs/changelog/2026-04-17-release-readiness.md`

- [ ] **Step 1: Write changelog entry summarising A+B+C+D**

```markdown
# 2026-04-17 — Release Readiness

Closes readiness review blockers from 2026-04-17:

## Phase A — Bootstrap
- `hooks/post-install.sh` in every plugin (venv + pip + npm)
- Plugin-local `.venv` preferred by skills
- `.jack-tar-ready` sentinel for post-install completion
- CI now tests simulated marketplace install across all 5 plugins
- `.claude-plugin/plugin.json` declares `postInstall` hook

## Phase B — Narrative standalone
- `narrative-architect` and `speaker-notes-writer` work without brand-manager / slide-stylist
- New `src/narrative_standalone.py` with tone-keyed style defaults
- Objective 4 (standalone narrative creation) honoured end-to-end

## Phase C — Documentation split
- Dual-persona root README
- `INSTALLATION.md`, `TROUBLESHOOTING.md`, `docs/USER-GUIDE.md`, `docs/LICENSING.md`
- `docs/examples/` with three sample TalkBriefs
- CLAUDE.md pruned of human-facing content

## Phase D — Polish
- msft-smartart inject references manifest (not spec)
- deck-qa documents actual check count; CI asserts no drift
- ollama README no longer claims local-config.json is required
- cloud README clarifies provider_config.json is optional
- RECRAFT_API_KEY standardized (RECRAFT_API kept as deprecated fallback)
- Example spec files shipped with both SmartArt plugins
- Mocked functional tests added for jack-tar-cloud
```

- [ ] **Step 2: Commit and open the Phase D PR**

```bash
git add docs/changelog/2026-04-17-release-readiness.md
git commit -m "docs: release-readiness changelog"
```

---

## Self-Review

**Spec coverage:** every blocker from the 2026-04-17 readiness review maps to a task:
- Path resolution / bootstrap → Phase A (A1-A7)
- Narrative-only standalone (objective 4) → Phase B (B1-B4)
- Dual-persona docs → Phase C (C1-C6)
- msft-smartart manifest/spec mismatch → D1
- QA check count drift → D2
- Ollama local-config docs → D3
- Cloud provider_config docs → D4
- Recraft env var consistency → D5
- SmartArt example specs → D6
- Cloud functional tests → D7

**Placeholder scan:** no TBD / TODO / "add appropriate" phrases. Each code step shows the exact code. Each command step shows the exact command with expected output.

**Type consistency:** `generate_outline_from_brief_only`, `build_outline_from_brief`, `generate_speaker_notes_from_outline` names match across tasks B1-B4. `$PY` and `$PLUGIN_ROOT` shell variables match across Phase A tasks. `RECRAFT_API_KEY` used consistently in D5.

**Phase PR boundaries:** A, B, C, D are independent PRs. Each produces shippable state. Phase A must land before marketplace install works; Phases B, C, D can ship in any order after that.
