---
name: sop-definition-generator
description: Generates UniversalSOPSchema v3.1.0 YAML definitions from canonical model SOP stubs. Transforms SOP IDs and names from persona definitions into complete, machine-readable SOP files with operations, parameters, authority requirements, and semantic mappings.
---

# SOP Definition Generator

This skill transforms SOP stubs (IDs and names from canonical model AI Persona definitions) into complete UniversalSOPSchema v3.1.0 YAML files. Each generated SOP definition is machine-readable, includes operation parameters, authority requirements, error handling, and ERP semantic mappings — ready for MCP server implementation.

## When to Use

- After canonical models define AI Personas with SOP references but no YAML definitions exist
- When preparing for MCP server implementation (Phase 3) and need SOP contracts
- When validating that demo scenarios have complete end-to-end SOP coverage
- When onboarding a new company to the ACID network and need to define their SOPs

## Schema Reference

The UniversalSOPSchema v3.1.0 is defined at:
`docs/spec/MCP-SOP-201-UNIVERSALSOPSCHEMA.md`

The MCP protocol specification for SOP discovery and execution:
`docs/spec/MCP-SOP-200-PROTOCOL-SPECIFICATION.md`

## Instructions

### 1. Identify SOP Stubs

Scan canonical models for SOP references. Each AI Persona's `sops` array contains stubs:

```json
"sops": [
  { "sopId": "sop-st-quality-inspect", "name": "Inspect Turbine Blade Quality" },
  { "sopId": "sop-st-batch-trace", "name": "Trace Material Batch Genealogy" }
]
```

Also check the PHASE-1-SCOPE.md for demo-essential SOPs that must be defined first.

### 2. Gather Context

For each SOP, collect:

- **Owning Persona**: Which AI Persona owns this SOP? What is its authority model?
- **Owning Service**: Which service domain contains the persona?
- **Company Context**: Which company's node will host this SOP?
- **ERP System**: What backend system does this SOP translate to? (SAP S/4HANA, Oracle, etc.)
- **Demo Scenarios**: Which demo scenarios invoke this SOP?

### 3. Generate SOP YAML

For each SOP, produce a YAML file following UniversalSOPSchema v3.1.0:

```yaml
# SOP Definition: [SOP Name]
# Generated from canonical model: [model-id]
# Schema: UniversalSOPSchema v3.1.0

sopId: "sop-st-quality-inspect"
name: "Inspect Turbine Blade Quality"
version: "1.0.0"
description: "Performs automated quality inspection on turbine blades using visual inspection data and dimensional measurements."

# Owning context
owner:
  personaId: "ap-st-blade-inspection-ai"
  serviceId: "st-quality-blade-inspect"
  company: "SpinnyThings"

# MCP Server registration
mcpServer:
  name: "spinnythings.quality.mcp"
  transport: "stdio"  # Phase 1; "http" for Phase 2+

# Authority requirements
authority:
  minimumLevel: 1  # Analyst — proposes disposition
  autonomousLevel: 2  # Operator — auto-reject below threshold
  escalationLevel: 3  # Principal — batch disposition
  escalationTarget: "ha-quality-dir"

# Operations (what the SOP can do)
operations:
  - id: "inspect_blade"
    name: "Inspect Turbine Blade"
    description: "Perform quality inspection on a turbine blade using visual and dimensional data."
    type: "query"  # query | mutation | subscription
    parameters:
      - name: "blade_serial_number"
        type: "string"
        required: true
        description: "Serial number of the blade to inspect"
      - name: "inspection_type"
        type: "enum"
        required: true
        values: ["visual", "dimensional", "metallurgical", "full"]
        description: "Type of inspection to perform"
      - name: "batch_id"
        type: "string"
        required: false
        description: "Material batch ID for traceability"
    returns:
      - name: "disposition"
        type: "enum"
        values: ["accept", "rework", "scrap", "mrb_review"]
        description: "Inspection disposition"
      - name: "confidence"
        type: "float"
        description: "AI confidence in disposition (0.0-1.0)"
      - name: "defects_found"
        type: "array"
        description: "List of defects identified"
    errors:
      - code: "BLADE_NOT_FOUND"
        description: "Blade serial number not found in inventory"
      - code: "INSPECTION_INCOMPLETE"
        description: "Required inspection data not available"

# Semantic mappings (how universal operations map to local ERP)
semanticMappings:
  erpSystem: "SAP S/4HANA"
  mappings:
    - universalField: "blade_serial_number"
      erpField: "SERNR"
      erpTable: "EQUI"
      transformation: "direct"
    - universalField: "batch_id"
      erpField: "CHARG"
      erpTable: "MCHA"
      transformation: "direct"
    - universalField: "disposition"
      erpField: "QMGRP"
      erpTable: "QMEL"
      transformation: "enum_map"
      enumMap:
        accept: "01"
        rework: "02"
        scrap: "03"
        mrb_review: "04"

# Access control
accessControl:
  exposedToExternal: true  # Visible to visiting agents
  requiredCredentials: ["jwt_valid", "company_acl"]
  partnerRestrictions:
    - companyId: "aerovista"
      operations: ["inspect_blade"]
      maxAuthority: 1  # AeroVista agents can only query, not auto-dispose

# Audit requirements
audit:
  logLevel: "full"  # full | summary | minimal
  retentionDays: 2555  # 7 years for aerospace
  hashChain: true
  regulatoryReferences: ["AS9100-8.6", "FAA-AC-00-56B"]

# Tags for discovery filtering
tags:
  - "quality"
  - "inspection"
  - "turbine-blade"
  - "visual-inspection"
```

### 4. SOP Naming Convention

Follow this naming pattern for SOP IDs:

```
sop-{company-prefix}-{domain}-{action}
```

Examples:
- `sop-av-quality-trace` — AeroVista quality tracing SOP
- `sop-st-inv-check-atp` — SpinnyThings inventory ATP check
- `sop-av-aog-commit` — AeroVista AOG commitment SOP

For MCP-exposed SOPs (callable by external agents), also define the legacy short names used in CLAUDE.md (e.g., `check_inventory_atp`, `verify_material_traceability`).

### 5. Batch Generation

When generating SOPs for a batch (e.g., all demo-essential SOPs):

1. List all SOP stubs from the PHASE-1-SCOPE.md or canonical models
2. Group by company and MCP server
3. Generate YAML for each SOP
4. Cross-reference to ensure no SOP is duplicated across servers
5. Produce a manifest listing all generated SOPs

### 6. Validation Checklist

For each generated SOP:

- [ ] sopId matches the ID in the canonical model
- [ ] All operations have complete parameter definitions
- [ ] All parameters have types, descriptions, and required flags
- [ ] Return types are defined for every operation
- [ ] Error codes cover expected failure modes
- [ ] Authority levels align with the owning persona's authority model
- [ ] Semantic mappings reference real ERP tables and fields
- [ ] Access control specifies which partners can invoke which operations
- [ ] Audit requirements meet aerospace regulatory standards (7-year retention)
- [ ] Tags enable correct SOP discovery filtering

## Output Location

Write SOP definitions to:
`docs/architecture/bsa/sop-definitions/[sop-id].yaml`

Example: `docs/architecture/bsa/sop-definitions/sop-st-quality-inspect.yaml`

Batch manifest:
`docs/architecture/bsa/sop-definitions/_manifest.md`

## Relationship to Other Skills

- **Upstream**: `canonical-model-manager` (provides SOP stubs), `phase-scope-extractor` (identifies demo-essential SOPs), `ai-persona-definition` (Section 5 capabilities define what SOPs do)
- **Downstream**: MCP server implementation (Phase 3), `demo-scenario-validator` (validates SOPs exist), `vanilla-agent-test-harness` (tests SOP discovery and execution)
- **Cross-reference**: `bsa-cross-reference-index` (SOP index), `dependency-register` (SOP dependencies)

## Output

Complete UniversalSOPSchema v3.1.0 YAML files for each SOP, ready for MCP server implementation. Each file is self-contained with operations, parameters, authority requirements, semantic mappings, access control, and audit configuration.
