---
name: refresh-models
description: Fetch the latest model catalog (model names, capabilities, pricing) from the repository and install it locally after an operator-gated price review — no plugin release required.
allowed-tools: Bash(python *)
---

# /refresh-models

Update the local model catalog from the canonical published copy on the
repository's `main` branch. Model retirements, renames, new models, and
price corrections land as catalog-only commits — this skill picks them up
without reinstalling any plugin (EPIC #125, issue #128).

**The price diff is an operator gate.** Catalog prices drive the F10
free→cost cascade gates, so a refresh that changes ANY price must be shown
to the operator and explicitly accepted before it takes effect. Never skip
the gate; never auto-refresh.

## Step 1: Fetch and diff (read-only)

```bash
python3 - << 'EOF'
import json, sys
sys.path.insert(0, "PLUGIN_ROOT")  # replace with the plugin root path
from src.model_catalog_refresh import check_remote
from src.model_catalog import CatalogError

try:
    result = check_remote()
except CatalogError as exc:
    print(f"REFRESH BLOCKED: {exc}")
    print("The current catalog is unchanged. If this persists, the remote "
          "may require a newer plugin (min_loader_version) — update the "
          "plugin instead.")
    sys.exit(1)

diff = result["diff"]
print(f"Current: {result['current_version']} ({result['current_source']})")
print(f"Remote:  {diff['version']['new']}")
print(json.dumps(diff, indent=2))
# Persist the fetched doc for Step 3 so apply uses EXACTLY what was reviewed.
with open("/tmp/jack-tar-remote-catalog.json", "w") as f:
    json.dump(result["remote_doc"], f)
EOF
```

## Step 2: Operator gate

Render the diff for the operator:

- **`price_changes`** — table of model / component / old → new. This is the
  gate-relevant section. If non-empty, ask explicitly: *"These price changes
  will drive future cost estimates and cascade gates. Apply?"* and WAIT for
  an affirmative ("yes", "apply", "go").
- **`status_changes`** — retirements and deprecations (e.g. a model going
  `active → retired` with its replacement). Informational; include in the
  summary.
- **`added_models` / `removed_models`** — informational.
- If the diff is empty (same version, no changes), report "already current"
  and STOP — do not write anything.

## Step 3: Apply (only after explicit go-ahead)

```bash
python3 - << 'EOF'
import json, sys
sys.path.insert(0, "PLUGIN_ROOT")
from src.model_catalog_refresh import apply_refresh

with open("/tmp/jack-tar-remote-catalog.json") as f:
    doc = json.load(f)
summary = apply_refresh(doc)
print(f"Installed catalog {summary['version']} at {summary['cache_path']}")
if summary["previous_kept"]:
    print("Previous catalog kept alongside — roll back with: /refresh-models --rollback")
EOF
```

The write is atomic (temp file + rename); the previous cache is preserved at
`~/.jack-tar/model-catalog.json.prev`. Loaded catalogs pick up the new cache
on next process start; long-running sessions can force it with
`get_catalog(reload=True)`.

## Rollback (`--rollback`)

```bash
python3 - << 'EOF'
import sys
sys.path.insert(0, "PLUGIN_ROOT")
from src.model_catalog_refresh import rollback
print(rollback())
EOF
```

## Safety properties

- A remote catalog that fails validation, or whose `min_loader_version`
  exceeds the installed loader, is rejected BEFORE touching the cache.
- The loader independently re-validates the cache on every load and falls
  back to the shipped baseline if it is corrupt — a bad refresh can never
  brick image generation.
- Deleting `~/.jack-tar/model-catalog.json` always returns the install to
  the shipped baseline.
