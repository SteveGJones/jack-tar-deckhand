---
name: verify
description: Check plugin readiness — verifies python-pptx, lxml, esprima are importable, that the jack-tar-msft-smartart plugin is locatable, and that the jack-tar-deckhand plugin's imagegen-bridge skill is reachable. Reports a STATUS line and a per-dependency table.
allowed-tools: Bash(python *), Skill
---

# /jack-tar-superpower-bridge:verify

Report whether the bridge plugin can run end-to-end. Used as a pre-flight check before /bridge-brief or /enrich-deck.

## Locate the plugin

```bash
PLUGIN_ROOT=$(python3 -c "
from pathlib import Path
import sys, os
if os.environ.get('JACK_TAR_SUPERPOWER_BRIDGE_ROOT'):
    print(os.environ['JACK_TAR_SUPERPOWER_BRIDGE_ROOT']); sys.exit()
home = Path.home()
for base in [home / '.claude' / 'plugins' / 'cache']:
    for p in base.rglob('jack-tar-superpower-bridge/.claude-plugin/plugin.json'):
        print(str(p.parent.parent)); sys.exit()
dev = Path.cwd() / 'plugins' / 'jack-tar-superpower-bridge'
if dev.exists():
    print(str(dev)); sys.exit()
print('NOT_FOUND')
" 2>/dev/null)
if [ -z "$PLUGIN_ROOT" ] || [ "$PLUGIN_ROOT" = "NOT_FOUND" ]; then
  echo "STATUS: NOT_AVAILABLE"; echo "ERROR: jack-tar-superpower-bridge not found"; exit 0
fi
```

## Step 1 — Python dependencies

The bridge depends on three Python packages:

- **python-pptx** — opens, edits, and writes .pptx files (post-hoc enrichment surgery).
- **lxml** — XML parsing for OOXML analyser and SmartArt graft operations.
- **esprima** — JavaScript AST parsing for the JS build-script fallback marker extractor.

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<'PY'
deps = []
for module in ("pptx", "lxml.etree", "esprima"):
    try:
        __import__(module)
        deps.append((module, "OK"))
    except Exception as exc:
        deps.append((module, f"MISSING ({exc.__class__.__name__})"))
print("DEPENDENCIES:")
for mod, status in deps:
    print(f"  {mod}: {status}")
PY
```

## Step 2 — msft-smartart plugin

The bridge requires the **jack-tar-msft-smartart** plugin to render editable SmartArt during enrichment:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<'PY'
from src.msft_smartart_loader import load_msft_smartart_api, MsftSmartArtNotFoundError
try:
    api = load_msft_smartart_api()
    print(f"MSFT_SMARTART: OK (engine.render={hasattr(api.engine, 'render')})")
except MsftSmartArtNotFoundError as exc:
    print(f"MSFT_SMARTART: MISSING ({exc})")
PY
```

## Step 3 — deckhand plugin (for imagegen-bridge skill)

The **jack-tar-deckhand** plugin provides the imagegen-bridge skill used to generate enrichment images. Invoke its verify skill if installed:

```bash
DECKHAND_VERIFY_OUTPUT=$(claude skill jack-tar-deckhand:verify 2>&1)
if echo "$DECKHAND_VERIFY_OUTPUT" | grep -q "STATUS:"; then
  echo "DECKHAND: $(echo "$DECKHAND_VERIFY_OUTPUT" | grep '^STATUS:')"
else
  echo "DECKHAND: NOT_AVAILABLE (install jack-tar-deckhand for AI image generation)"
fi
```

## Step 4 — Image-path allowlist sanity

The image-path allowlist requires existing directories at run time; we don't pre-create them, but verify the helper is importable:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<'PY'
from src.security import resolve_within_allowlist, AllowedPathError
print("SECURITY: OK (resolve_within_allowlist + AllowedPathError exposed)")
PY
```

## Step 5 — Report status

Aggregate the readiness signals into a single STATUS line:

- All deps OK + msft-smartart OK + deckhand reachable → `STATUS: FULLY_AVAILABLE`
- Deps OK + msft-smartart OK + deckhand absent → `STATUS: PARTIALLY_AVAILABLE` (SmartArt enrichment works; image enrichment falls back to placeholder rectangles)
- Any python dep missing OR msft-smartart missing → `STATUS: NOT_AVAILABLE`

Example output:

```
STATUS: FULLY_AVAILABLE
DEPENDENCIES:
  pptx: OK
  lxml.etree: OK
  esprima: OK
MSFT_SMARTART: OK (engine.render=True)
DECKHAND: STATUS: FULLY_AVAILABLE
SECURITY: OK
```
