"""Generate docs/model-catalog.md from model-catalog.json.

Same pattern as smartart_pptx_native/layouts/catalog_markdown.py: the
markdown is a build artifact of the catalog; CI drift-checks that the two
were regenerated in the same commit (see
plugins/integration_tests/test_model_catalog_integrity.py).

Usage:
    python model-catalog/catalog_markdown.py          # rewrite docs/model-catalog.md
    python model-catalog/catalog_markdown.py --check  # exit 1 if doc is stale
"""

import json
import sys
from pathlib import Path

CATALOG_DIR = Path(__file__).resolve().parent
CATALOG_PATH = CATALOG_DIR / "model-catalog.json"
DOC_PATH = CATALOG_DIR.parent / "docs" / "model-catalog.md"

_PROVIDER_TITLES = {
    "google": "Google (Nano Banana + Imagen)",
    "openai": "OpenAI",
    "fal": "FAL.ai",
    "recraft": "Recraft",
    "ollama": "Ollama (local, free)",
    "mlx": "MLX (local, free)",
}


def _pricing_summary(entry):
    pricing = entry.get("pricing")
    if not pricing:
        return "—"
    parts = []
    if "flat" in pricing:
        parts.append(f"${pricing['flat']:.3f} flat")
    for res, cost in (pricing.get("per_resolution") or {}).items():
        parts.append(f"{res} ${cost:.3f}")
    for backend, table in (pricing.get("backends") or {}).items():
        inner = ", ".join(f"{res} ${cost:.3f}" for res, cost in table.items())
        parts.append(f"{backend}: {inner}")
    psq = pricing.get("per_size_quality") or {}
    if psq:
        low = min(psq.values())
        high = max(psq.values())
        parts.append(f"${low:.3f}–${high:.3f} by size×quality")
    for tier, cost in (pricing.get("per_tier") or {}).items():
        parts.append(f"{tier} ${cost:.2f}")
    tiered = pricing.get("tiered_megapixel")
    if tiered:
        parts.append(
            f"${tiered['first_mp']:.3f} first MP + "
            f"${tiered['per_extra_mp']:.3f}/extra MP"
        )
    suffix = " *(estimate)*" if pricing.get("estimate") else ""
    return "; ".join(parts) + suffix


def render(catalog):
    lines = [
        "# Model Catalog",
        "",
        "<!-- AUTO-GENERATED from model-catalog/model-catalog.json — do not edit by hand. -->",
        "<!-- Regenerate with: python model-catalog/catalog_markdown.py -->",
        "",
        f"Catalog version **{catalog['catalog_version']}**, "
        f"updated **{catalog['updated']}**, "
        f"min loader version {catalog['min_loader_version']}.",
        "",
        "Single source of truth for model identity, capability, and pricing "
        "across all jack-tar plugins (EPIC #125). Loaded by "
        "`model_catalog.py` with shipped → cached-remote → local-config "
        "precedence.",
        "",
        "## Role defaults",
        "",
        "| Role | Default |",
        "|---|---|",
    ]
    for role, value in sorted((catalog.get("role_defaults") or {}).items()):
        rendered = value if isinstance(value, str) else " → ".join(value)
        lines.append(f"| {role} | `{rendered}` |")
    lines.append("")

    by_provider = {}
    for entry in catalog["models"]:
        by_provider.setdefault(entry["provider"], []).append(entry)

    for provider in sorted(by_provider):
        lines += [
            f"## {_PROVIDER_TITLES.get(provider, provider)}",
            "",
            "| Model | Status | Roles | Resolutions | Pricing (USD) | Quirks | Aliases |",
            "|---|---|---|---|---|---|---|",
        ]
        for entry in by_provider[provider]:
            caps = entry.get("capabilities") or {}
            resolutions = ", ".join(caps.get("resolutions", [])) or "—"
            status = entry["status"]
            if status == "retired":
                status = f"retired → `{entry['replacement']}`"
            elif status == "deprecated" and entry.get("replacement"):
                status = f"deprecated → `{entry['replacement']}`"
            quirks = ", ".join(entry.get("quirks", [])) or "—"
            aliases = ", ".join(f"`{a}`" for a in entry.get("aliases", [])) or "—"
            lines.append(
                f"| `{entry['id']}` | {status} | {', '.join(entry['roles'])} "
                f"| {resolutions} | {_pricing_summary(entry)} | {quirks} "
                f"| {aliases} |"
            )
        lines.append("")

    lines += [
        "## Notes",
        "",
    ]
    for entry in catalog["models"]:
        if entry.get("notes"):
            lines.append(f"- **`{entry['id']}`** — {entry['notes']}")
        pricing_notes = (entry.get("pricing") or {}).get("notes")
        if pricing_notes:
            lines.append(f"- **`{entry['id']}` pricing** — {pricing_notes}")
    lines.append("")
    return "\n".join(lines)


def main(argv):
    catalog = json.loads(CATALOG_PATH.read_text())
    rendered = render(catalog)
    if "--check" in argv:
        current = DOC_PATH.read_text() if DOC_PATH.exists() else ""
        if current != rendered:
            print(
                f"STALE: {DOC_PATH} does not match {CATALOG_PATH}. "
                f"Regenerate with: python {Path(__file__).relative_to(Path.cwd())}",
                file=sys.stderr,
            )
            return 1
        print(f"OK: {DOC_PATH} is current.")
        return 0
    DOC_PATH.write_text(rendered)
    print(f"Wrote {DOC_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
