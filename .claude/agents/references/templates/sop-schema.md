# SOP Schema Template

Use this template alongside Appendix G to document every SOP before registering it on an MCP server. Duplicate the structure below for each SOP file.

```markdown
# [SOP Title]

## Metadata
- **SOP ID:** 
- **Version:** 
- **Persona Alignment:** 
- **Domain Owner:** 
- **Accountable Role:** 
- **MCP Server Endpoint:** 
- **Environment:** (dev/test/prod)

## Purpose / Delegated Outcome
Describe the measurable business result this SOP guarantees. Link back to the Persona WHAT statement.

## Trigger
List the event, cadence, or upstream signal that activates the SOP. Include system names and payload references.

## Inputs
| Input Name | System of Record | Format | Notes |
| --- | --- | --- | --- |
|  |  |  |  |

## Procedure
| Step | Action | Evidence Required | Owner |
| --- | --- | --- | --- |
| 1 |  |  |  |

## Control Points
Document approvals, thresholds, or compliance reviews that gate execution.

## Vanilla-Agent Test Summary
- **Last Run:** 
- **Result:** (pass/hold)
- **Issues Noted:** 
- **Remediation Owner:** 

## Compliance Notes
Reference applicable regulations, retention rules, or escalation policies.

## MCP Payload Contract
Outline required request/response fields for `invoke_sop` along with traceability expectations.
```

See `Appendix-G-SOP-Integration-Patterns.md` §G.2 for field descriptions.
