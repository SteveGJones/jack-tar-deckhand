# BSA Update Validate

## Your Role

Run schema and structural validation against the canonical model the draft node produced. Surface any failures as critical issues for the review node. This is a deterministic check, not a judgement call — pass/fail.

## Context

You are at `/workspace` on the same feature branch. The draft node committed JSON edits + arch doc updates + CLAUDE.md version bump in the previous commit.

## What To Do

### Phase 1: JSON parse check

```bash
cd /workspace
python3 -c "
import json
with open('.bsa/models/jack-tar-deckhand.json') as f:
    model = json.load(f)
print('OK — valid JSON')
print(f'bsaVersion: {model.get(\"bsaVersion\", \"<missing>\")}')
print(f'service count: {len(model.get(\"services\", []))}')
print(f'persona count: {len(model.get(\"aiPersonas\", []))}')
print(f'interaction count: {len(model.get(\"interactions\", []))}')
print(f'dependency count: {len(model.get(\"dependencyRegister\", []))}')
"
```

If JSON is broken: STOP and report as CRITICAL.

### Phase 2: Schema validation (if validator available)

The project ships a `canonical-model-validator` skill. Try invoking it via Bash if the project's local skill directory is mounted in the workspace:

```bash
ls /workspace/.claude/skills/canonical-model-validator/ 2>/dev/null && echo "validator skill present" || echo "validator skill not in workspace — skipping"
```

If present, follow the skill's instructions to invoke its Python validator (likely `python3 .claude/skills/canonical-model-validator/<entry-point>` or similar). Capture the output.

If not present, do a manual structural check:

```bash
python3 << 'EOF'
import json
m = json.load(open('.bsa/models/jack-tar-deckhand.json'))

# Required top-level keys
required = ['bsaVersion', 'services', 'aiPersonas', 'interactions']
missing = [k for k in required if k not in m]
if missing:
    print(f"CRITICAL: missing required top-level keys: {missing}")

# bsaVersion is semver
import re
v = m.get('bsaVersion', '')
if not re.match(r'^\d+\.\d+\.\d+$', v):
    print(f"CRITICAL: bsaVersion '{v}' not semver")

# All interactions reference real services
service_ids = {s.get('id') for s in m.get('services', [])}
for inx, intr in enumerate(m.get('interactions', [])):
    src = intr.get('source')
    tgt = intr.get('target')
    if src and src not in service_ids and not src.startswith('persona:'):
        print(f"WARN interaction[{inx}].source '{src}' not in services")
    if tgt and tgt not in service_ids and not tgt.startswith('persona:'):
        print(f"WARN interaction[{inx}].target '{tgt}' not in services")

# Dependency register entries have unique IDs
dep_ids = [d.get('id') for d in m.get('dependencyRegister', [])]
seen = set()
for d in dep_ids:
    if d in seen:
        print(f"CRITICAL: duplicate dependency id '{d}'")
    seen.add(d)

print("Structural check complete")
EOF
```

### Phase 3: Cross-reference with CLAUDE.md

Check that the BSA version in CLAUDE.md matches the canonical model:

```bash
GREP_VER=$(grep -oE 'BSA Architecture[^v]*v\d+\.\d+\.\d+' /workspace/CLAUDE.md | head -1 | grep -oE 'v\d+\.\d+\.\d+' | tail -1)
JSON_VER=$(python3 -c "import json; print(json.load(open('/workspace/.bsa/models/jack-tar-deckhand.json'))['bsaVersion'])")
echo "CLAUDE.md says: v$GREP_VER  |  JSON says: $JSON_VER"
```

If they differ: CRITICAL.

### Phase 4: Test the draft's self-test answers

The draft node wrote self-test answers in `reports/bsa-draft/changes.md`. For each Q/A pair, independently verify the answer is now findable in the file the draft cited.

### Phase 5: Diff scope check

Confirm only expected files were touched:

```bash
git diff main --stat
```

Expected scope (per the plan): `.bsa/models/jack-tar-deckhand.json`, possibly `CLAUDE.md`, possibly `docs/architecture/...`. Anything else is OUT OF SCOPE — flag it.

## Output

Write the validation report to `/workspace/reports/bsa-validate/findings.md`:

```markdown
# BSA Validate Findings

## JSON parse
PASS | FAIL — <evidence>

## Schema check
PASS | FAIL — <which validator was used, what it reported>

## Cross-reference (CLAUDE.md ↔ canonical model)
PASS | FAIL — versions match: yes / no, both = vX.Y.Z

## Self-test answers
Each Q/A from the draft change log: VERIFIED | NOT FINDABLE | DRIFTED

## Diff scope
PASS — only expected files touched
or
FAIL — unexpected file: <path>, reason it shouldn't be here

## Critical issues
<list any CRITICAL findings — these block the review node from progressing>

## Verdict
PASS — proceed to review
FAIL — return to draft node for fixes (cite specific issues)
```

## Commit

```bash
cd /workspace
mkdir -p reports/bsa-validate
git add reports/bsa-validate/findings.md
git commit -m "bsa(validate): schema + cross-reference + scope check"
```
