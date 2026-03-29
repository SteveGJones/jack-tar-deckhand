---
name: vanilla-agent-test-harness
description: Automated Vanilla-Agent SOP validation test harness. Validates that a zero-knowledge agent can discover and execute SOPs correctly at a company node using MCP+SOP protocol.
---

# Vanilla-Agent Test Harness

This skill produces an automated test harness that validates the core ACID innovation: that a "vanilla agent" with zero hardcoded domain knowledge can arrive at a company node, discover available SOPs via MCP, and execute them correctly using only the protocol-provided information.

This is a release gate. No SOP may be marked production-ready without passing a Vanilla-Agent test.

## When to Use

- Before marking any SOP as production-ready
- During Checkpoint 4 of the readiness scorecard
- When validating MCP server implementations
- After any SOP schema changes
- During cross-domain SOP register updates
- As part of Change Advisory Circle review evidence

## Key Concepts

### What is a Vanilla Agent?

A vanilla agent is an AI agent with:
- **Zero hardcoded domain knowledge** — No company-specific, industry-specific, or system-specific logic
- **Pure protocol-based discovery** — Learns everything via `sop.discover` and SOP schema alone
- **No training data from this domain** — Cannot rely on pre-existing knowledge of SAP, aerospace, or company processes

This validates that the MCP+SOP protocol is self-describing and complete.

### Test Philosophy

The test asks: "If I sent a completely generic foundation model to this company node with only the MCP+SOP protocol documentation, could it successfully execute business operations?"

If the answer is no, the SOPs are not procedurally complete.

## Template Reference

Test log template: `methodology_draft/templates/vanilla-agent-log.md`

## Instructions

### 1. Set Up Test Context

Define the test environment:

```yaml
test_context:
  company_node_id: "spinnythings"
  company_node_name: "SpinnyThings Engine OEM"
  mcp_endpoint: "http://spinnythings:8100/mcp"
  agent_authority_level: 0  # Shadow mode for testing
  test_date: "2027-01-15"
  test_conductor: "AI RM Lab Lead"
  protocol_version: "UniversalSOPSchema v3.1.0"
```

### 2. Prepare Agent Credentials

Generate test credentials that represent a vanilla agent:

- **Agent ID**: `vanilla-test-agent-001`
- **Authority Level**: 0 (Shadow Mode — read-only, no mutations)
- **Issuer**: Test harness
- **Scope**: All SOPs at the target node
- **Delegation**: Temporary (test duration only)

Phase 1: Use simple JWT with test claims.
Phase 5: Use SPIFFE SVID with proper X.509 attestation.

### 3. Execute SOP Discovery

Call the MCP `sop.discover` endpoint:

```python
# Pseudo-code (actual implementation in WP-7)
discovery_response = mcp_client.call_method(
    method="sop.discover",
    params={
        "agent_id": "vanilla-test-agent-001",
        "authority_level": 0,
        "protocol_version": "3.1.0"
    }
)
```

### 4. Validate Discovery Response

For each SOP returned, validate:

#### Schema Compliance
- [ ] SOP follows UniversalSOPSchema v3.1.0 structure
- [ ] All required fields present: `sopId`, `name`, `version`, `operations`
- [ ] All operations have `operationId`, `name`, `description`
- [ ] Every operation parameter has `name`, `type`, `required`, `description`

#### Semantic Completeness
- [ ] Operation descriptions are clear and unambiguous
- [ ] Parameter types are explicit (string, integer, boolean, object, array)
- [ ] Semantic mappings reference actual ERP fields
- [ ] Example values provided for complex parameters
- [ ] Enum values listed for closed-set parameters

#### Authority Model Clarity
- [ ] Authority requirements specified per operation
- [ ] Escalation conditions defined
- [ ] Approval workflows described if needed
- [ ] Human-in-the-loop touchpoints identified

#### Error Handling
- [ ] Error codes enumerated
- [ ] Error recovery procedures documented
- [ ] Retry policies specified
- [ ] Timeout values provided

#### Constraint Documentation
- [ ] Business rules stated explicitly
- [ ] Data validation rules clear
- [ ] Rate limits specified
- [ ] Idempotency guarantees documented

### 5. Execute Dry-Run Tests

For each discovered SOP operation:

#### Generate Sample Parameters
Using only the SOP schema information, generate valid sample inputs:

```yaml
operation: check_inventory_atp
sample_params:
  material_number: "MAT-12345"  # Derived from parameter type and description
  plant_code: "1000"             # Derived from enum or example values
  quantity_required: 100         # Derived from integer type and constraints
```

#### Call the Operation
Execute in Shadow Mode (no actual ERP mutations):

```python
test_result = mcp_client.call_method(
    method="sop.execute_operation",
    params={
        "sop_id": "SOP-SPINY-INV-01",
        "operation_id": "check_inventory_atp",
        "parameters": sample_params,
        "authority_level": 0,  # Shadow mode
        "dry_run": true
    }
)
```

#### Validate Response Format
- [ ] Response matches declared return type
- [ ] All promised fields are present
- [ ] Data types match schema declarations
- [ ] Error responses follow error code schema

### 6. Test Comprehension

The agent must demonstrate it understands:

**Operation Purpose**
- Can the agent explain in natural language what this SOP operation does?
- Can it identify appropriate use cases for invoking it?
- Can it distinguish when NOT to invoke it?

**Parameter Semantics**
- Can the agent map parameters to business concepts?
- Does it understand parameter constraints and validation rules?
- Can it generate multiple valid example invocations?

**Authority Boundaries**
- Can the agent identify which authority level is required?
- Does it recognize when human approval is needed?
- Can it describe escalation paths?

**Error Recovery**
- Can the agent interpret error codes?
- Does it understand retry vs abort decisions?
- Can it propose corrective actions for common errors?

### 7. Score the Test

Apply verdicts per SOP:

**PASS** — All criteria met:
- Discovery response is schema-compliant
- All operations executable with sample parameters
- Agent demonstrates comprehension of purpose, parameters, authority, and errors
- No ambiguities or missing information that would block execution

**CONDITIONAL PASS** — Minor issues that don't block execution:
- Documentation could be clearer but is sufficient
- Example values missing but parameter types are clear
- Error handling complete but verbose
- Non-critical metadata missing

**FAIL** — Blocking issues:
- Schema validation failures
- Operations not executable with provided information
- Critical parameters lacking descriptions or types
- Authority requirements ambiguous
- Error codes not defined
- Agent cannot determine operation purpose

### 8. Generate Test Log

Populate the vanilla-agent-log template with:

```markdown
## Test Summary

- **Company Node**: SpinnyThings
- **Test Date**: 2027-01-15
- **Test Conductor**: AI RM Lab Lead
- **Agent ID**: vanilla-test-agent-001
- **Protocol Version**: UniversalSOPSchema v3.1.0

## Discovery Test

| Metric | Result |
|--------|--------|
| Total SOPs Discovered | 8 |
| Schema-Compliant SOPs | 8 |
| Total Operations | 34 |
| Operations with Complete Docs | 31 |

## Per-SOP Results

### SOP-SPINY-INV-01: Inventory Management

**Verdict**: PASS

| Operation | Discovery | Dry-Run | Comprehension | Verdict |
|-----------|-----------|---------|---------------|---------|
| check_inventory_atp | PASS | PASS | PASS | PASS |
| reserve_inventory | PASS | PASS | PASS | PASS |
| release_reservation | PASS | PASS | PASS | PASS |

**Issues**: None

---

### SOP-SPINY-QUAL-02: Quality Management

**Verdict**: CONDITIONAL PASS

| Operation | Discovery | Dry-Run | Comprehension | Verdict |
|-----------|-----------|---------|---------------|---------|
| report_quality_issue | PASS | PASS | CONDITIONAL | CONDITIONAL |
| get_material_traceability | PASS | PASS | PASS | PASS |

**Issues**:
- Operation `report_quality_issue` parameter `severity` lacks enum values (agent inferred from description but explicit enum would be clearer)

**Remediation**: Add explicit enum to `severity` parameter: `[Minor, Major, Critical, Safety]`

**Remediation Deadline**: 2027-01-20
```

### 9. Record Test Artifacts

Store:
- Full test log at: `docs/architecture/bsa/generated/vanilla-agent-tests/[company]-[date].md`
- Discovery response JSON at: `docs/architecture/bsa/generated/vanilla-agent-tests/[company]-[date]-discovery.json`
- Dry-run execution logs at: `docs/architecture/bsa/generated/vanilla-agent-tests/[company]-[date]-executions.json`

Link test log to:
- Cross-domain SOP register (Vanilla-Agent status column)
- Readiness scorecard (Checkpoint 4 evidence)
- Change Advisory Circle meeting minutes

### 10. Establish Test Cadence

**Trigger tests on**:
- Every SOP schema change
- MCP server version updates
- Before production deployment
- After Change Advisory Circle approvals
- Monthly regression tests for all SOPs

**Continuous validation**: Integrate into CI/CD pipeline. Every commit to SOP definitions triggers automated vanilla-agent tests.

## Output

A completed Vanilla-Agent test log with:
- Pass/Conditional Pass/Fail verdict per SOP
- Detailed test results per operation
- Blocking issues identified with remediation actions
- Evidence package suitable for readiness scorecard Checkpoint 4
- Test artifacts stored and linked to governance registers

## Relationship to Other Skills

- **Upstream**: Depends on `ai-persona-definition` (Section 5: Capabilities)
- **Upstream**: Depends on MCP server implementation (WP-7)
- **Downstream**: Feeds `readiness-scorecard` (Checkpoint 4)
- **Downstream**: Feeds `change-advisory-circle-manager` (CAC review evidence)
- **Related**: `dependency-register` (tracks which personas consume which SOPs)
