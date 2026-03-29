# Cross-Domain SOP Register Template

Use this register whenever an SOP owned by one domain is invoked by another service or persona. Maintain it alongside the dependency register from [Chapter 8](../chapters/Chapter-08-Completing-AI-First-Service-Architecture.md) so Change Advisory Circles can see exactly who must approve an update.

| Field | Description | Example |
| --- | --- | --- |
| **SOP ID** | Stable identifier from [Appendix G](../appendices/Appendix-G-SOP-Integration-Patterns.md) §G.2.1. | `SOP-LOG-02` |
| **Owning service / domain** | Service responsible for the SOP and MCP server. | Distribution & Logistics |
| **Borrowing service / persona** | Service or persona that invokes the SOP. | Manufacturing / Quality Inspection AI |
| **Dependency ID** | Link to dependency register entry (DEP-XXX). | `DEP-QI-SUP-01` |
| **MCP server** | Endpoint hosting the SOP. | `logistics-control.mcp` |
| **Invocation purpose** | Outcome or value exchange being satisfied. | “Pause shipments until QC clears lot.” |
| **Vanilla-Agent status** | Date + pass/fail from latest dry run. | `2025-02-10 – Pass` |
| **Change Advisory Circle date** | Last review date + attendees. | `2025-02-12 – Manufacturing, Logistics, AI RM` |
| **Notes** | Constraints, escalation paths, or blockers. | “Borrower limited to 3 concurrent holds.” |

> **Usage:** Update this register immediately after dependency workshops ([Chapter 8](../chapters/Chapter-08-Completing-AI-First-Service-Architecture.md)) and whenever [Chapter 9](../chapters/Chapter-09-Realizing-AI-First-Service-Architecture.md) releases change an SOP. AI RM should store the authoritative copy in the MCP repo and publish a read-only view for facilitators.
