# Full Chapter Reference Links

This reference layer includes **cliff notes** (40-65 line summaries) for quick navigation. For deep methodology work, reference the full chapters in the main methodology repository.

## How to Use

1. **Quick Navigation:** Use cliff notes in `cliff-notes/` directory
2. **Deep Work:** Follow links below to full chapters
3. **Path Discovery:** Agents read `.claude/toolkit-config.json` to find `methodology_repository` path

## Part I: Foundation - The "WHAT"

### Chapter 1: Introduction to AI-First Service Architecture
- **Cliff Note:** [cliff-notes/Chapter-01-Introduction.md](cliff-notes/Chapter-01-Introduction.md)
- **Full Chapter:** `{methodology_repo}/methodology_draft/chapters/Chapter-01-Introduction-AI-First-Service-Architecture.md`

### Chapter 2: Defining AI-First SOA
- **Cliff Note:** [cliff-notes/Chapter-02-Defining-AI-First-SOA.md](cliff-notes/Chapter-02-Defining-AI-First-SOA.md)
- **Full Chapter:** `{methodology_repo}/methodology_draft/chapters/Chapter-02-Defining-AI-First-SOA.md`

### Chapter 3: Why AI-First Is Important
- **Cliff Note:** [cliff-notes/Chapter-03-Why-AI-First-Is-Important.md](cliff-notes/Chapter-03-Why-AI-First-Is-Important.md)
- **Full Chapter:** `{methodology_repo}/methodology_draft/chapters/Chapter-03-Why-AI-First-Is-Important.md`

## Part II: Core Methodology - Creating the Business "WHAT"

### Chapter 4: Start at the Top (Enterprise Service Discovery)
- **Cliff Note:** [cliff-notes/Chapter-04-Start-at-the-Top.md](cliff-notes/Chapter-04-Start-at-the-Top.md)
- **Full Chapter:** `{methodology_repo}/methodology_draft/chapters/Chapter-04-Start-at-the-Top.md`

### Chapter 5: Core Definitions (Service Domain Model)
- **Cliff Note:** [cliff-notes/Chapter-05-Core-Definitions.md](cliff-notes/Chapter-05-Core-Definitions.md)
- **Full Chapter:** `{methodology_repo}/methodology_draft/chapters/Chapter-05-Core-Definitions/`

### Chapter 6: Creating the Architecture (AI Persona Definition)
- **Cliff Note:** [cliff-notes/Chapter-06-Creating-the-Architecture.md](cliff-notes/Chapter-06-Creating-the-Architecture.md)
- **Full Chapter:** `{methodology_repo}/methodology_draft/chapters/Chapter-06-Creating-the-Architecture.md`

### Chapter 7: AI Resource Management (AI RM)
- **Cliff Note:** [cliff-notes/Chapter-07-AI-Resource-Management.md](cliff-notes/Chapter-07-AI-Resource-Management.md)
- **Full Chapter:** `{methodology_repo}/methodology_draft/chapters/Chapter-07-AI-Resource-Management/`

### Chapter 8: Completing the Architecture (Dependencies & Governance)
- **Cliff Note:** [cliff-notes/Chapter-08-Completing-the-Architecture.md](cliff-notes/Chapter-08-Completing-the-Architecture.md)
- **Full Chapter:** `{methodology_repo}/methodology_draft/chapters/Chapter-08-Completing-the-Architecture.md`

## Part III: Operating the "HOW"

### Chapter 9: Realizing the Architecture (MCP + SOP Execution)
- **Cliff Note:** [cliff-notes/Chapter-09-Realizing-the-Architecture.md](cliff-notes/Chapter-09-Realizing-the-Architecture.md)
- **Full Chapter:** `{methodology_repo}/methodology_draft/chapters/Chapter-09-Realizing-the-Architecture.md`

### Chapter 10: Classification (Risk Tiers & Authority Models)
- **Cliff Note:** [cliff-notes/Chapter-10-Classification.md](cliff-notes/Chapter-10-Classification.md)
- **Full Chapter:** `{methodology_repo}/methodology_draft/chapters/Chapter-10-Classification.md`

### Chapter 11: Measurement (5-Tier Framework)
- **Cliff Note:** [cliff-notes/Chapter-11-Measurement.md](cliff-notes/Chapter-11-Measurement.md)
- **Full Chapter:** `{methodology_repo}/methodology_draft/chapters/Chapter-11-Measurement.md`

## Part IV: Modeling and Managing the "HOW"

### Chapter 12: Modeling the HOW (BPMN + Process Architecture)
- **Cliff Note:** [cliff-notes/Chapter-12-Modeling-the-HOW.md](cliff-notes/Chapter-12-Modeling-the-HOW.md)
- **Full Chapter:** `{methodology_repo}/methodology_draft/chapters/Chapter-12-Modelling-the-HOW.md`

## Part V: Delivery and Management

### Chapter 13-17: Advanced Topics
**Note:** Chapters 13-17 cover legacy extraction, project planning, IT support, governance, and summary. Full chapters available in methodology repository:
- Chapter 13: Legacy Extraction
- Chapter 14: Project Planning
- Chapter 15: IT Support
- Chapter 16: Governance
- Chapter 17: Summary and Next Steps

## Appendices

Full appendices available in methodology repository:
- **Appendix A:** Historical Context (BSA 3.1 → AI-First evolution)
- **Appendix B:** Data Supply Chain Governance
- **Appendix C:** Trusted AI Scope (Executive Brief)
- **Appendix D:** Regulatory Compliance
- **Appendix E:** Worked Examples (Oblivion Widgets, Digital Bank, VMI Programme)
- **Appendix F:** Visual Notation Standards
- **Appendix G:** SOP Schema & MCP Interface
- **Appendix H:** Measure Type Definitions
- **Appendix I:** Chapter 5 Facilitator Guide
- **Appendix J:** Data Supply Chain (Technical Reference)
- **Appendix K:** AI RM Red-Team Playbook
- **Appendix L:** Telemetry Design Standards
- **Appendix M:** Trusted AI Scope (Practitioner Guide)

## Usage Pattern for Agents

```markdown
## Example: Agent needs Chapter 6 details

1. Read `.claude/toolkit-config.json` to get `methodology_repository` path
2. Quick overview: Read `cliff-notes/Chapter-06-Creating-the-Architecture.md`
3. Deep dive: Read `{methodology_repo}/methodology_draft/chapters/Chapter-06-Creating-the-Architecture.md`
```

## Bundled vs. Linked Content

| Content Type | Location | Why |
|--------------|----------|-----|
| **Cliff Notes** | Bundled in `cliff-notes/` | Fast access, offline-capable |
| **Templates** | Bundled in `templates/` | Frequently used |
| **Schemas** | Bundled in `schemas/` | Validation requirement |
| **Examples** | Bundled in `examples/` | Reference patterns |
| **Full Chapters** | Linked to methodology repo | Large size, less frequent access |
| **Appendices** | Linked to methodology repo | Reference material |

## Glossary

For quick terminology reference, see [glossary.md](glossary.md) in this directory.

## Governance Framework

For versioning, release management, and distribution governance, see [GOVERNANCE-FRAMEWORK.md](GOVERNANCE-FRAMEWORK.md) in this directory.

---

**Toolkit Version:** 2.0.0
**Methodology Version:** 1.0.0
**Last Updated:** 2026-02-24
