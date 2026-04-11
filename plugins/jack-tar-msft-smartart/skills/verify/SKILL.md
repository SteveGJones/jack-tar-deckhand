---
name: verify
description: Check python-pptx, lxml, layout fixtures, and test carrier build capability.
allowed-tools: Bash(python *)
---

# /verify

Check whether this plugin's prerequisites are met and report readiness.

## Step 1: Check Python dependencies

```bash
python3 -c "
import json
deps = {}
try:
    import pptx; deps['python-pptx'] = pptx.__version__
except Exception: deps['python-pptx'] = None
try:
    import lxml.etree; deps['lxml'] = lxml.etree.__version__
except Exception: deps['lxml'] = None
try:
    import jsonschema; deps['jsonschema'] = jsonschema.__version__
except Exception: deps['jsonschema'] = None
print(json.dumps(deps))
"
```

If python-pptx or lxml is None (not installed), report NOT_AVAILABLE.

## Step 2: Check layout fixtures

Count how many layout directories exist under the plugin's `data/smartart_layouts/` directory. Each should contain `layout.xml`, `quickStyle.xml`, `colors.xml`, and `meta.json`. Run this from the plugin directory:

```bash
python3 -c "
from pathlib import Path
import sys
plugin_root = Path(sys.argv[1])
data_dir = plugin_root / 'data' / 'smartart_layouts'
if not data_dir.exists():
    print('MISSING')
    sys.exit(1)
complete = [d for d in data_dir.iterdir() if d.is_dir() and (d / 'layout.xml').exists() and (d / 'meta.json').exists()]
print(f'{len(complete)} layouts present')
" /path/to/plugin/root
```

(The skill will discover the plugin root via Path(__file__) in the actual execution context.)

## Step 3: Test carrier build

Attempt to render a minimal process1 SmartArt carrier to a temp directory. If render succeeds, engine is working.

## Step 4: Report status

Example output:

```
PLUGIN: jack-tar-msft-smartart
VERSION: 1.0.0

DEPENDENCIES:
  python-pptx:     READY (1.0.2)
  lxml:            READY (5.1.0)
  jsonschema:      READY (4.21.0)

LAYOUT FIXTURES:
  Total:           29/29 present
  Process (8):     READY
  Cycle (2):       READY
  Hierarchy (5):   READY
  List (6):        READY
  Matrix (1):      READY
  Pyramid (1):     READY
  Relationship (4): READY

TEST CARRIER:
  process1:        BUILD OK

STATUS: FULLY_AVAILABLE
REASON: All dependencies installed, 29 layouts available, test carrier builds successfully
```
