---
name: service-architecture-renderer
description: Generates professional service architecture SVG diagrams from the canonical service domain model JSON. Use this when the user asks to create, update, or visualise a service architecture diagram at any level (L0 enterprise view or L1-L6 drill-downs).
---

# Service Architecture Renderer

This skill generates network-style service architecture diagrams from the canonical service domain model. Each diagram shows **one service level**: services, AI Personas, human and system actors, external interactions, and interaction flows.

The renderer uses **Graphviz** (neato engine) for professional force-directed layout with automatic edge routing and overlap avoidance, falling back to a manual network layout if Graphviz is not installed.

## ⚠️ IMPORTANT: This is the ONLY approved diagram renderer

**NEVER bypass this skill by:**
- Generating raw DOT files and calling `dot -Tsvg` directly
- Using `subprocess.run(['dot', '-Tsvg'])` in custom scripts
- Creating custom diagram renderers

This renderer uses Graphviz **for layout computation only** (`-Tjson`), then generates **professionally styled SVG** with Inter font, shadows, and business-friendly appearance. Raw Graphviz output produces technical diagrams unsuitable for business stakeholders.

## Prerequisites

- Python 3.8+
- Graphviz (`brew install graphviz` or `apt install graphviz`) — recommended but optional
- Style config at `.bsa/design/style-config.json` (auto-discovered)

## Instructions

### 1. Prepare or Locate the Canonical Model

The input is a canonical service domain model JSON file following the schema at `design/canonical-service-domain-model-schema.json`. The model contains all services, AI Personas, actors, interactions, and governance data for the entire organisation.

Existing examples:
- `design/canonical-model-example-oblivion-widgets.json` — Manufacturing company (simple)
- `design/canonical-model-example-digital-bank.json` — Digital bank (complex, 4 AI Personas)
- `design/canonical-model-example-vmi-programme.json` — VMI programme (7 services, 2 AI Personas)

### 2. Generate a Diagram

**Enterprise L0 view** (all top-level services):
```bash
python3 .bsa/diagram-tools/service_architecture_renderer.py <model.json> --l0 [output.svg]
```

**Drill-down view** (services under a parent at a specific level):
```bash
python3 .bsa/diagram-tools/service_architecture_renderer.py <model.json> <parent_service_id> <level> [output.svg]
```

### 3. Examples

```bash
# Enterprise L0 — shows all level-0 services and external actors
python3 .bsa/diagram-tools/service_architecture_renderer.py \
  design/canonical-model-example-digital-bank.json --l0 enterprise-l0.svg

# Manufacturing L1 — drill into Manufacturing, show level-1 services
python3 .bsa/diagram-tools/service_architecture_renderer.py \
  design/canonical-model-example-oblivion-widgets.json mfg 1 manufacturing-l1.svg

# Retail Banking L1 — complex view with 4 AI Personas, 35 interactions
python3 .bsa/diagram-tools/service_architecture_renderer.py \
  design/canonical-model-example-digital-bank.json retail 1 retail-banking-l1.svg
```

### 4. Output

- Generates a single `.svg` file with embedded styling
- Canvas auto-sizes to fit all entities
- Includes a legend showing entity types and interaction line styles

## Canonical Model JSON Structure

The model file must include at minimum:

```json
{
  "modelMetadata": {
    "organisation": "Company Name"
  },
  "services": [
    {
      "id": "svc-id",
      "name": "Service Name",
      "level": 0,
      "mission": "What this service does.",
      "serviceType": "core"
    },
    {
      "id": "child-svc",
      "name": "Child Service",
      "parentId": "svc-id",
      "level": 1,
      "mission": "Child service mission.",
      "serviceType": "core",
      "isAIPersona": true
    }
  ],
  "aiPersonas": [
    {
      "id": "ap-id",
      "serviceId": "child-svc",
      "authorityModel": "hybrid",
      "sops": []
    }
  ],
  "humanActors": [
    {
      "id": "human-id",
      "name": "Actor Name",
      "isExternal": false,
      "serviceAssociations": [
        { "serviceId": "child-svc", "associationType": "owner" }
      ]
    }
  ],
  "systemActors": [
    {
      "id": "sys-id",
      "name": "System Name",
      "serviceAssociations": [
        { "serviceId": "child-svc", "associationType": "integration_target" }
      ]
    }
  ],
  "externalInteractions": [
    {
      "id": "ext-id",
      "internalServiceId": "child-svc",
      "externalServiceName": "External System",
      "externalDomain": "Domain"
    }
  ],
  "interactions": [
    {
      "id": "int-001",
      "sourceId": "human-id",
      "targetId": "child-svc",
      "label": "Do Something",
      "interactionType": "capability_invocation"
    }
  ]
}
```

## Supported Types

**Service types:** `core`, `support`

**Association types:** `owner`, `consumer`, `provider`, `data_source`, `escalation_target`, `integration_target`

**Interaction types:** `capability_invocation` (blue solid), `data_flow` (green solid), `escalation` (red dashed), `support` (green dotted), `external` (grey dashed), `approval` (blue solid)

**Authority models** (AI Personas): `autonomous`, `hybrid`, `supervised`

## Visual Identity

Entity rendering follows the brand spec in `.bsa/design/style-config.json`:
- **Services** — Blue header boxes with mission text
- **AI Personas** — Purple gradient header with robot icon, authority badge, and SOP marker
- **Human actors** — Stick figure icons with name labels (EXT badge for external)
- **System actors** — Server rack icons with name labels
- **External services** — Dashed-border boxes with EXT badge

## Key Design Principle

Each diagram shows **one service level only**. The canonical model is the single source of truth; the renderer is a stateless filter. See `design/canonical-model-renderer-filtering.js` for the filtering logic reference.
