# Reference Distribution Governance Framework

**Framework Version:** 1.0.0
**Effective Date:** 2026-02-23
**Owner:** Governance Reviewer + Methodology Architect
**Scope:** BSA Methodology + MCP+SOP Protocol Reference Materials

---

## Executive Summary

This document defines the governance framework for distributing BSA (Business Service Architecture) methodology and MCP+SOP protocol reference materials to projects at `.clause/agents/references/`. It establishes version control strategy, update policies, completeness validation, and lifecycle management for reference distributions used by multiple agents and skills.

**Key Principles:**
1. **Semantic Versioning** - MAJOR.MINOR.PATCH for predictable change management
2. **Immutable Releases** - Released reference versions never change; publish new versions instead
3. **Automated Validation** - Pre-release validation ensures completeness and consistency
4. **Clear Update Paths** - Migration guides for breaking changes, backward compatibility for minor/patch
5. **Decoupled Versioning** - Reference version ≠ agent version ≠ skill version (independent lifecycles)

---

## 1. Version Control Strategy

### 1.1 Versioning Scheme: Semantic Versioning (SemVer)

**Format:** `MAJOR.MINOR.PATCH` (e.g., `2.1.0`)

| Component | Increment When | Examples |
|-----------|---------------|----------|
| **MAJOR** | Breaking changes to methodology structure, schema incompatibility, removed chapters | 1.x → 2.0: Schema v2 incompatible with v1<br/>2.x → 3.0: 17 chapters → 20 chapters (added 3) |
| **MINOR** | New methodology chapters, new templates, new schemas (backward compatible) | 2.0.x → 2.1.0: Added Chapter 18 (New Topic)<br/>2.1.x → 2.2.0: Added new persona template variant |
| **PATCH** | Typo fixes, clarifications, non-breaking examples, updated references | 2.1.0 → 2.1.1: Fixed typos in Chapter 7<br/>2.1.1 → 2.1.2: Updated diagram examples |

**Rationale for SemVer over date-based:**
- **Predictable Impact** - Version increment signals change magnitude (breaking vs safe)
- **Dependency Management** - Agents can specify `>=2.1.0, <3.0.0` for compatible versions
- **Ecosystem Alignment** - SemVer is universal in software; familiar to all developers
- **Long-Term Support** - Can maintain `2.x` branch while developing `3.x`

**Pre-Release Versions:**
- Alpha: `3.0.0-alpha.1` (internal testing, unstable API)
- Beta: `3.0.0-beta.1` (external testing, feature-complete, may have bugs)
- RC: `3.0.0-rc.1` (release candidate, production-ready unless critical bugs found)

### 1.2 Version Metadata

Every reference distribution MUST include a `VERSION.json` manifest:

```json
{
  "version": "2.1.0",
  "release_date": "2026-02-23",
  "methodology_version": "1.0.0",
  "mcp_sop_protocol_version": "1.2.0",
  "compatibility": {
    "min_agent_api_version": "1.0.0",
    "min_skill_api_version": "1.0.0",
    "breaking_changes_from": "1.x"
  },
  "contents": {
    "methodology": {
      "chapters": 17,
      "templates": 12,
      "schemas": 3
    },
    "mcp_sop": {
      "protocol_spec": "v1.2",
      "schema_version": "2.0.0",
      "examples": 8
    }
  },
  "checksums": {
    "sha256": "abc123...def789",
    "manifest_hash": "xyz456...uvw012"
  },
  "deprecations": [
    {
      "item": "Chapter 12 Section 3 (Old SOP Format)",
      "deprecated_in": "2.0.0",
      "removal_in": "3.0.0",
      "replacement": "Chapter 12 Section 4 (UniversalSOPSchema)"
    }
  ],
  "changelog_url": "https://github.com/org/repo/blob/main/CHANGELOG.md#210"
}
```

**Validation:** Every release MUST pass `validate-distribution.py --strict` (see Section 9).

---

## 2. Update Policy and Cadence

### 2.1 Release Cadence

| Release Type | Cadence | Trigger | Approval Required |
|--------------|---------|---------|-------------------|
| **MAJOR** | Every 12-18 months | Methodology restructuring, breaking schema changes | Methodology Architect + 2 senior practitioners |
| **MINOR** | Every 2-4 months | New chapters, new templates, new protocol features | Methodology Architect + 1 senior practitioner |
| **PATCH** | Ad-hoc (as needed) | Typos, clarifications, bug fixes | Methodology Architect (solo approval) |
| **Hotfix** | Immediate | Critical errors blocking projects | Methodology Architect + Governance Reviewer |

**Exception:** Security-related updates (e.g., updated threat model in MCP+SOP) are released as PATCH immediately, regardless of cadence.

### 2.2 Support Policy

| Version Branch | Support Type | Duration | Example |
|----------------|--------------|----------|---------|
| **Current MAJOR** | Active development, all updates | Indefinite | 2.x (current) |
| **Previous MAJOR** | Security + critical bug fixes only | 12 months after new MAJOR | 1.x (until 2027-02) |
| **EOL MAJOR** | No support (archived) | After 12-month sunset | 0.x (archived 2025-02) |

**Long-Term Support (LTS) Versions:**
- Every 3rd MINOR version is designated LTS (e.g., 2.3.0, 2.6.0, 2.9.0)
- LTS versions receive backported security/critical fixes for 24 months
- Projects can pin to LTS for stability without frequent upgrades

### 2.3 Deprecation Policy

**3-Release Deprecation Cycle:**

1. **Announce** (Version N) - Mark as deprecated, add warning, document replacement
2. **Warn** (Version N+1) - Increase warning visibility, add migration guide
3. **Remove** (Version N+2) - Remove deprecated item, breaking change (MAJOR version bump)

**Example:**
- **v2.1.0** - Deprecate old SOP format, warn "Use UniversalSOPSchema instead"
- **v2.2.0** - Escalate warning, add auto-migration script
- **v3.0.0** - Remove old SOP format entirely (breaking change)

**Deprecation Notice Format:**
```markdown
⚠️ **DEPRECATED in v2.1.0** (Removal in v3.0.0)
This template will be removed in version 3.0.0. Use `new-template.md` instead.
Migration guide: [MIGRATION-2.x-to-3.0.md](./docs/migrations/2.x-to-3.0.md)
```

---

## 3. Migration Path for Breaking Changes

### 3.1 Migration Artifacts (REQUIRED for MAJOR versions)

Every MAJOR version MUST include:

1. **Migration Guide** - `docs/migrations/MIGRATION-[OLD]-to-[NEW].md`
   - What changed (breaking changes list)
   - Why it changed (rationale)
   - How to migrate (step-by-step)
   - Risk assessment (low/medium/high impact per change)
   - Estimated migration time per project size

2. **Automated Migration Script** - `scripts/migrate-[OLD]-to-[NEW].py`
   - Detects old version in project
   - Transforms artifacts to new schema
   - Validates migrated artifacts
   - Generates migration report (what was changed, what needs manual review)

3. **Backward Compatibility Shim** (if feasible)
   - Adapter layer allowing old agent/skill code to work with new reference
   - Logs deprecation warnings when shim is used
   - Removed in MAJOR+1 version

4. **Migration Validation Checklist**
   - Pre-migration: Backup project, verify old version
   - Migration: Run automated script, review changes
   - Post-migration: Validate with `validate-distribution.py`, test agents/skills
   - Sign-off: Architect approval required

### 3.2 Migration Testing

**Pre-Release Testing:**
- Test migration on 3 real projects (small, medium, large complexity)
- Measure migration time (target: <2 hours for large projects)
- Document edge cases requiring manual intervention

**Post-Release Tracking:**
- Track migration issues in GitHub (label: `migration-[version]`)
- Issue emergency PATCH if >20% of projects hit same migration blocker

### 3.3 Migration Support Window

- **First 30 days** - Active migration support (dedicated Slack channel, office hours)
- **Days 31-90** - Standard support (GitHub issues, async responses)
- **After 90 days** - Community support (projects expected to complete migration)

---

## 4. Completeness and Consistency Validation

### 4.1 Pre-Release Validation Suite

**Mandatory Checks (ALL must pass for release):**

| Check ID | Check Name | What It Validates | Failure = |
|----------|------------|-------------------|-----------|
| V-001 | Schema Validity | All JSON schemas parse, no syntax errors | BLOCK RELEASE |
| V-002 | Template Completeness | All templates have required sections, no broken internal links | BLOCK RELEASE |
| V-003 | Cross-Reference Integrity | All `[See Chapter X]` references exist and are correct | BLOCK RELEASE |
| V-004 | Methodology Coherence | No contradictions between chapters (AI-assisted validation) | BLOCK RELEASE |
| V-005 | Example Validity | All examples validate against their schemas | BLOCK RELEASE |
| V-006 | Version Metadata | VERSION.json is complete, checksums are correct | BLOCK RELEASE |
| V-007 | Changelog Accuracy | CHANGELOG.md has entry for this version, follows format | BLOCK RELEASE |
| V-008 | License Compliance | All files have correct license headers | BLOCK RELEASE |

**Advisory Checks (failures logged as warnings):**

| Check ID | Check Name | What It Validates | Failure = |
|----------|------------|-------------------|-----------|
| A-001 | Writing Quality | Typos, grammar, readability score (Flesch-Kincaid) | WARNING |
| A-002 | Diagram Freshness | Diagrams match latest methodology text (AI visual diff) | WARNING |
| A-003 | Example Coverage | Each major concept has at least 1 example | WARNING |
| A-004 | Consistent Terminology | Same terms used consistently across all chapters | WARNING |

**Validation Command:**
```bash
python scripts/validate-distribution.py \
  --version 2.1.0 \
  --strict \
  --output-report dist/validation-report-2.1.0.json
```

**Validation Report Format:**
```json
{
  "version": "2.1.0",
  "validation_date": "2026-02-23T10:00:00Z",
  "status": "PASS",
  "mandatory_checks": {
    "passed": 8,
    "failed": 0,
    "skipped": 0
  },
  "advisory_checks": {
    "passed": 3,
    "warnings": 1,
    "details": [
      {
        "check": "A-002",
        "status": "WARNING",
        "message": "Diagram in Chapter 7 may be stale (text updated 2026-02-20, diagram last updated 2026-01-15)"
      }
    ]
  },
  "checksums": {
    "sha256": "abc123...def789"
  },
  "approver": "methodology-architect",
  "approval_date": "2026-02-23T11:30:00Z"
}
```

### 4.2 Continuous Validation (Post-Release)

**Automated Regression Testing:**
- Every commit to `main` branch runs full validation suite (CI/CD)
- Nightly validation against 5 known-good reference projects
- Quarterly deep validation with human review (spot-check 20% of content)

**Issue Tracking:**
- All validation failures tracked in GitHub Issues (label: `validation-failure`)
- P0 failures trigger hotfix process
- P1 failures rolled into next PATCH release

---

## 5. Relationship Between Reference, Agent, and Skill Versions

### 5.1 Independent Versioning (Decoupled Lifecycles)

**Three Version Spaces:**

| Component | Version Scheme | Change Trigger | Example |
|-----------|----------------|----------------|---------|
| **Reference Distribution** | SemVer (e.g., `2.1.0`) | Methodology/protocol changes | Chapters added, schema updated |
| **Agent Definitions** | SemVer (e.g., `1.3.0`) | Agent behavior/prompt changes | New capabilities, refined instructions |
| **Skills** | SemVer (e.g., `1.0.5`) | Skill implementation changes | Bug fixes, new features |

**Dependency Declarations:**

Agents and skills declare compatible reference versions in their metadata:

**Agent Metadata (agent-name.md front matter):**
```yaml
---
name: business-solution-architect
version: 1.3.0
requires_references:
  bsa_methodology: ">=2.0.0, <3.0.0"  # Compatible with any 2.x version
  mcp_sop_protocol: ">=1.2.0"
last_updated: 2026-02-23
---
```

**Skill Metadata (skill-name/skill.json):**
```json
{
  "name": "canonical-model-manager",
  "version": "1.0.5",
  "requires_references": {
    "bsa_methodology": ">=2.1.0, <3.0.0",
    "canonical_schema": "2.0.0"
  },
  "last_updated": "2026-02-23"
}
```

### 5.2 Compatibility Matrix

**Version Compatibility Rules:**

| Reference Change | Agent/Skill Impact | Required Action |
|------------------|-------------------|-----------------|
| PATCH (e.g., 2.1.0 → 2.1.1) | **No impact** (typo fixes, clarifications) | None (auto-update safe) |
| MINOR (e.g., 2.1.0 → 2.2.0) | **Optional enhancement** (new chapters/templates available) | Update agent if using new features; otherwise no change |
| MAJOR (e.g., 2.x → 3.0) | **Breaking change** (schema incompatible) | Update agent/skill to declare `requires_references: ">=3.0.0"` |

**Example Scenarios:**

1. **Reference 2.1.0 → 2.1.1 (PATCH):**
   - Agent v1.3.0 (requires `>=2.0.0, <3.0.0`) continues working without changes
   - No agent version bump needed

2. **Reference 2.1.0 → 2.2.0 (MINOR):**
   - New Chapter 18 added
   - Agent v1.3.0 continues working (doesn't use Chapter 18)
   - If agent wants to use Chapter 18, bump to v1.4.0 and reference new chapter

3. **Reference 2.9.0 → 3.0.0 (MAJOR):**
   - Schema format changed (breaking)
   - Agent v1.3.0 declares `requires_references: ">=2.0.0, <3.0.0"` → incompatible with 3.0.0
   - Agent must update logic, test, bump to v2.0.0, declare `requires_references: ">=3.0.0, <4.0.0"`

### 5.3 Version Resolution at Runtime

**Claude Code Behavior:**

1. **Load Agent** - Read agent metadata, extract `requires_references`
2. **Check Installed References** - Read `.clause/agents/references/VERSION.json`
3. **Validate Compatibility** - Compare versions using SemVer rules
4. **Action:**
   - ✅ Compatible → Proceed
   - ⚠️ Outdated but compatible → Log warning "Reference 2.0.0 installed, agent works best with >=2.1.0"
   - ❌ Incompatible → Error "Agent requires reference >=3.0.0, found 2.9.0. Run `update-references.sh`"

**Version Pinning (Optional):**
Projects can pin exact reference version in `.claude/config.json`:
```json
{
  "references": {
    "bsa_methodology": "2.1.0",
    "mcp_sop_protocol": "1.2.0",
    "auto_update": false
  }
}
```

---

## 6. Handling Methodology Evolution

### 6.1 BSA Methodology Update Process

**Triggers for Methodology Updates:**

1. **New Chapters** (MINOR version bump)
   - New domain discovered (e.g., Chapter 18: Multi-Region BSA)
   - New tooling category (e.g., Chapter 19: AI Persona Testing Frameworks)

2. **Chapter Restructuring** (MAJOR version bump)
   - 17 chapters → 20 chapters (added 3)
   - Merged chapters (e.g., Chapters 10+11 → Chapter 10 only)
   - Removed deprecated chapters

3. **Schema Changes** (MAJOR if breaking, MINOR if additive)
   - Breaking: Canonical model schema v2 incompatible with v1
   - Additive: New optional fields in schema (backward compatible)

4. **Conceptual Refinements** (PATCH version bump)
   - Clarifications to existing concepts
   - Updated examples
   - Improved diagrams

**Methodology Change Approval Process:**

| Change Magnitude | Approval Required | Process |
|------------------|-------------------|---------|
| **MAJOR** (breaking) | Methodology Architect + 2 senior practitioners + 3 project retrospectives | 1. Propose change with rationale<br/>2. Test on 3 projects (measure impact)<br/>3. Write migration guide<br/>4. Formal approval vote<br/>5. 30-day public comment period<br/>6. Release |
| **MINOR** (additive) | Methodology Architect + 1 senior practitioner | 1. Propose change<br/>2. Test on 1 project<br/>3. Review and approve<br/>4. Release |
| **PATCH** (clarification) | Methodology Architect (solo) | 1. Make change<br/>2. Validate<br/>3. Release |

**Change Tracking:**
- All methodology changes tracked in `CHANGELOG.md` with rationale
- Major changes documented in `docs/methodology-evolution/ADR-[number]-[title].md` (Architecture Decision Record)

### 6.2 Backward Compatibility Strategy

**Compatibility Goals:**

| Version Type | Backward Compatibility Goal |
|--------------|----------------------------|
| PATCH | 100% backward compatible (drop-in replacement) |
| MINOR | 100% backward compatible (new features don't break old usage) |
| MAJOR | Breaking changes allowed (but migration guide required) |

**Deprecation-Driven Evolution:**
- Avoid breaking changes when possible
- Use deprecation cycle (3 releases) to phase out old patterns
- Provide dual support (old + new) during transition

**Example: Schema Evolution:**

**Version 2.0.0** - Canonical model schema has field `serviceType: string`

**Version 2.1.0** (MINOR) - Add new field `serviceCategory: enum` (optional, deprecated `serviceType`)
```json
{
  "serviceType": "core",  // DEPRECATED, use serviceCategory
  "serviceCategory": "business-capability"  // NEW, optional in 2.1.0
}
```
- Old agents using `serviceType` continue working
- New agents can use `serviceCategory`

**Version 3.0.0** (MAJOR) - Remove `serviceType`, make `serviceCategory` required
```json
{
  "serviceCategory": "business-capability"  // REQUIRED
}
```
- Breaking change: old agents fail validation
- Migration script auto-converts `serviceType` → `serviceCategory`

---

## 7. Approval Process for Reference Updates

### 7.1 Roles and Responsibilities

| Role | Responsibilities | Authority |
|------|------------------|-----------|
| **Methodology Architect** | Define methodology, approve changes, release management | Solo approval for PATCH, required for all releases |
| **Governance Reviewer** | Validate compliance, check methodology coherence, gate reviews | Veto power on MAJOR releases |
| **Senior Practitioners** | Field experience, real-world validation, migration testing | Approval required for MAJOR/MINOR (2 for MAJOR, 1 for MINOR) |
| **Maintainers** | Documentation, validation scripts, CI/CD, release automation | No approval authority (execution only) |

### 7.2 Approval Workflow

**PATCH Release:**
```
1. Methodology Architect proposes change
2. Run validation suite
3. Methodology Architect approves (solo)
4. Automated release (CI/CD)
```

**MINOR Release:**
```
1. Methodology Architect proposes change
2. Test on 1 reference project
3. Run validation suite
4. Senior Practitioner reviews and approves
5. Methodology Architect final approval
6. Automated release
```

**MAJOR Release:**
```
1. Methodology Architect proposes change (with ADR)
2. Test on 3 projects (small, medium, large)
3. Write migration guide + automated migration script
4. 2 Senior Practitioners review and approve
5. Governance Reviewer compliance check
6. 30-day public comment period (for major methodology changes)
7. Address feedback or justify why not addressed
8. Final approval vote (Methodology Architect + 2 Senior Practitioners)
9. Manual release (reviewed by Maintainers)
```

**Hotfix (Critical Bug):**
```
1. Issue identified (blocking production)
2. Methodology Architect + Governance Reviewer assess impact
3. Fix prepared and validated
4. Both approve (required for hotfix)
5. Immediate release as PATCH (e.g., 2.1.1 → 2.1.2)
6. Post-mortem within 48 hours
```

### 7.3 Approval Tracking

**Approval Manifest (included in every release):**
```json
{
  "release": "2.1.0",
  "approvals": [
    {
      "role": "Methodology Architect",
      "name": "Jane Doe",
      "approved_at": "2026-02-23T11:30:00Z",
      "signature": "pgp-signature-here"
    },
    {
      "role": "Senior Practitioner",
      "name": "John Smith",
      "approved_at": "2026-02-23T10:45:00Z",
      "signature": "pgp-signature-here"
    }
  ],
  "validation_report": "validation-report-2.1.0.json",
  "migration_tested": true,
  "test_projects": [
    "project-alpha-small",
    "project-beta-medium"
  ]
}
```

**Audit Trail:**
- All approvals recorded in Git commit messages (signed commits)
- Approval manifest included in release artifacts
- Governance Reviewer audits approval process quarterly

---

## 8. Tracking Project-Reference Versions

### 8.1 Project Version Registry

**Centralized Registry (Optional but Recommended):**

Maintain a registry of which projects use which reference versions:

**Format: `project-reference-registry.json`**
```json
{
  "registry_version": "1.0.0",
  "last_updated": "2026-02-23T12:00:00Z",
  "projects": [
    {
      "project_id": "vesper-commercial-product",
      "project_name": "Vesper SaaS",
      "reference_version": "2.1.0",
      "installed_date": "2026-02-20",
      "last_validated": "2026-02-23",
      "status": "up-to-date",
      "agent_count": 18,
      "skill_count": 11,
      "contact": "tech-lead@vesper.com"
    },
    {
      "project_id": "proyecto-bimbo-demo",
      "project_name": "Grupo Bimbo BSA Architecture",
      "reference_version": "2.0.0",
      "installed_date": "2026-01-15",
      "last_validated": "2026-02-01",
      "status": "outdated",
      "agent_count": 25,
      "skill_count": 21,
      "contact": "architect@example.com",
      "upgrade_plan": {
        "target_version": "2.1.0",
        "scheduled_date": "2026-03-01",
        "migration_owner": "Jane Doe"
      }
    }
  ],
  "statistics": {
    "total_projects": 2,
    "reference_version_distribution": {
      "2.1.0": 1,
      "2.0.0": 1
    },
    "outdated_projects": 1
  }
}
```

### 8.2 Project-Side Version Reporting

**Automated Beacon (Optional):**

Projects can optionally report their reference version to central registry:

```bash
# Run weekly via cron
python scripts/report-reference-version.py \
  --registry-url https://registry.example.com/api/v1/report \
  --project-id vesper-commercial-product \
  --api-key $REGISTRY_API_KEY
```

**What Gets Reported:**
- Project ID (anonymized if desired)
- Reference version installed
- Last validation timestamp
- Agent/skill count
- Validation status (passing/failing checks)

**Privacy:**
- Opt-in only (projects can disable reporting)
- No sensitive data transmitted (no project code, no business data)
- Used for ecosystem health metrics only

### 8.3 Version Adoption Metrics

**Tracked Metrics:**

| Metric | Purpose | Target |
|--------|---------|--------|
| **Adoption Rate** | % of projects on latest MINOR version within 90 days | >70% |
| **Migration Time** | Average time to migrate from version N to N+1 | <2 hours (MAJOR), <30 min (MINOR) |
| **Blocker Rate** | % of projects hitting migration blockers | <20% |
| **Stale Projects** | Projects on EOL versions (>12 months old) | <10% |

**Quarterly Adoption Report:**
```markdown
# Q1 2026 Reference Adoption Report

**Current Version:** 2.1.0 (released 2026-02-23)

**Adoption Breakdown:**
- 2.1.0 (latest): 45 projects (60%)
- 2.0.x: 25 projects (33%)
- 1.x (EOL): 5 projects (7%)

**Migration Progress:**
- 20 projects migrated from 2.0.0 → 2.1.0 in first 30 days (67% adoption rate)
- Average migration time: 1.2 hours
- 3 projects reported blockers (12% blocker rate)

**Action Items:**
- Contact 5 projects on 1.x (EOL) to schedule migration
- Address top blocker: "Schema validation error on custom fields" (hotfix planned for 2.1.1)
```

### 8.4 Upgrade Notifications

**Proactive Notifications:**

When new version released, notify projects:

1. **Email/Slack** - "Reference 2.1.0 released. You're on 2.0.0. Migration guide: [link]"
2. **CLI Warning** - When agent starts: `⚠️ Reference version 2.0.0 is installed. Version 2.1.0 is available. Run update-references.sh`
3. **GitHub Issue** - Auto-create issue in project repo (if registry has webhook access): "Upgrade available: 2.0.0 → 2.1.0"

**Notification Cadence:**
- MAJOR: Immediate (within 24 hours of release)
- MINOR: Weekly digest (if project is 1+ MINOR versions behind)
- PATCH: Monthly digest (low priority)

---

## 9. Deprecation and Sunset Policy

### 9.1 Deprecation Lifecycle

**Phase 1: Announce Deprecation (Version N)**
- Mark deprecated items with `⚠️ DEPRECATED` warnings
- Add replacement recommendations
- Log deprecation warnings when deprecated features used
- Update documentation with migration path

**Phase 2: Escalate Warnings (Version N+1)**
- Increase warning visibility (error-level logs)
- Add automated migration script
- Publish migration guide
- Notify all projects using deprecated feature

**Phase 3: Remove (Version N+2, MAJOR version)**
- Remove deprecated items entirely
- Breaking change (MAJOR version bump)
- Migration script mandatory for projects on N+1 → N+2

**Example Timeline:**

| Version | Date | Action | User Experience |
|---------|------|--------|----------------|
| 2.1.0 | 2026-02 | Deprecate old SOP format | Logs: `WARN: Old SOP format deprecated, use UniversalSOPSchema` |
| 2.2.0 | 2026-04 | Escalate warning | Logs: `ERROR: Old SOP format will be removed in 3.0.0. Migrate now!` |
| 3.0.0 | 2027-02 | Remove old format | Validation fails: `Schema error: Old SOP format not supported` |

### 9.2 Version Sunset (End-of-Life)

**Sunset Triggers:**

| Trigger | Action |
|---------|--------|
| **New MAJOR version released** | Previous MAJOR enters sunset period (12 months) |
| **12 months after sunset start** | Version reaches EOL (no more support) |
| **Security vulnerability in EOL version** | Advisory published, recommend immediate upgrade (no patch provided) |

**Sunset Communication:**

**Month 0 (New MAJOR released):**
- Email all projects: "Version 2.x entering 12-month sunset. Migrate to 3.x by 2027-02."
- Update docs: Add sunset banner to v2.x docs

**Month 6:**
- Reminder email: "6 months until 2.x EOL. 30% of projects still on 2.x."
- Offer migration support (office hours, consulting)

**Month 11:**
- Final warning: "1 month until 2.x EOL. Critical security patches will not be backported."

**Month 12 (EOL):**
- Version 2.x reaches EOL
- Archive 2.x documentation (read-only, marked as archived)
- No more support (GitHub issues closed, security advisories only)

**Post-EOL:**
- Projects on EOL versions receive no updates
- Security vulnerabilities publicly disclosed without patches
- Strong recommendation to upgrade immediately

### 9.3 Emergency Extension

If >30% of projects still on EOL version at sunset date:
- **Governance Reviewer + Methodology Architect** assess situation
- Options:
  1. **Extend sunset by 6 months** (if migration blockers exist)
  2. **Offer paid extended support** (for enterprise projects)
  3. **Proceed with EOL anyway** (if security risk is low)

---

## 10. Distribution Completeness Validation

### 10.1 Validation Script: `validate-distribution.py`

**Purpose:** Ensure every reference distribution is complete, consistent, and ready for release.

**Usage:**
```bash
python scripts/validate-distribution.py \
  --version 2.1.0 \
  --reference-path ./references/ \
  --strict \
  --output-report dist/validation-report-2.1.0.json
```

**Validation Checks (detailed):**

#### V-001: Schema Validity
- Parse all `.json` and `.yaml` files
- Validate against JSON Schema / YAML Schema
- Check for syntax errors, missing required fields
- **Failure:** Exit code 1, block release

#### V-002: Template Completeness
- Every template has required sections (defined in `template-schema.json`)
- No broken internal links (`[See Chapter X](#anchor)` → anchor exists)
- All placeholder variables documented (e.g., `{{PROJECT_NAME}}`)
- **Failure:** Exit code 1, block release

#### V-003: Cross-Reference Integrity
- Extract all cross-references: `[See Chapter X]`, `[Template Y]`, `[Schema Z]`
- Verify target exists and path is correct
- Check for circular references
- **Failure:** Exit code 1, block release

#### V-004: Methodology Coherence
- AI-assisted validation: Check for contradictions between chapters
  - Example: Chapter 7 says "AI Personas require 19 sections", Chapter 12 template has 18 sections
- Human review required if contradictions found
- **Failure:** Exit code 1, block release (with manual override option)

#### V-005: Example Validity
- Extract all example JSON/YAML snippets from markdown
- Validate examples against their declared schemas
- Check that examples are realistic (not trivial placeholders)
- **Failure:** Exit code 1, block release

#### V-006: Version Metadata
- `VERSION.json` exists and parses correctly
- All required fields present: `version`, `release_date`, `checksums`, etc.
- Version format is valid SemVer
- Checksums match distribution contents
- **Failure:** Exit code 1, block release

#### V-007: Changelog Accuracy
- `CHANGELOG.md` has entry for this version
- Changelog entry follows format (Keep a Changelog standard)
- All breaking changes documented
- All deprecations listed
- **Failure:** Exit code 1, block release

#### V-008: License Compliance
- All files have license headers (or LICENSE file in root)
- No files with incompatible licenses included
- Third-party dependencies declared with licenses
- **Failure:** Exit code 1, block release

**Advisory Checks (warnings only):**

#### A-001: Writing Quality
- Run grammar checker (LanguageTool)
- Calculate readability score (Flesch-Kincaid Grade Level)
- Flag complex sentences (>30 words) for review
- **Failure:** Warning logged, does not block release

#### A-002: Diagram Freshness
- Compare diagram last-modified date vs. related text last-modified date
- If text updated >30 days after diagram, flag for review
- AI visual diff: Check if diagram visually matches described architecture
- **Failure:** Warning logged, does not block release

#### A-003: Example Coverage
- Every major concept (H2 heading) should have ≥1 example
- Flag sections with no examples
- **Failure:** Warning logged, does not block release

#### A-004: Consistent Terminology
- Build glossary of key terms
- Check that terms used consistently across all chapters
- Flag inconsistencies (e.g., "AI Persona" vs "AI persona" vs "Persona")
- **Failure:** Warning logged, does not block release

### 10.2 Automated CI/CD Validation

**GitHub Actions Workflow (`.github/workflows/validate-reference.yml`):**

```yaml
name: Validate Reference Distribution

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run validation suite
        run: |
          python scripts/validate-distribution.py \
            --version $(cat VERSION.json | jq -r '.version') \
            --reference-path ./references/ \
            --strict \
            --output-report dist/validation-report.json

      - name: Upload validation report
        uses: actions/upload-artifact@v3
        with:
          name: validation-report
          path: dist/validation-report.json

      - name: Check for mandatory failures
        run: |
          if grep -q '"status": "FAIL"' dist/validation-report.json; then
            echo "❌ Validation failed. See report for details."
            exit 1
          fi

      - name: Post validation summary to PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync('dist/validation-report.json'));
            const summary = `
            ## Reference Distribution Validation

            **Status:** ${report.status}
            **Version:** ${report.version}

            **Mandatory Checks:** ${report.mandatory_checks.passed}/${report.mandatory_checks.passed + report.mandatory_checks.failed} passed
            **Advisory Checks:** ${report.advisory_checks.warnings} warnings

            ${report.status === 'FAIL' ? '❌ Validation failed. Review report artifact.' : '✅ Validation passed.'}
            `;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: summary
            });
```

**Pre-Release Gate:**
- No release tag created unless validation passes
- Maintainers cannot manually override (governance policy)

### 10.3 Manual Review Checklist

**Human Review Required (even if automated validation passes):**

- [ ] Methodology Architect reviews all breaking changes
- [ ] Senior Practitioner reviews new chapters/templates
- [ ] Governance Reviewer spot-checks 20% of changes for coherence
- [ ] Test migration on 1 real project (MINOR) or 3 projects (MAJOR)
- [ ] All deprecations have clear replacement paths
- [ ] CHANGELOG.md is user-friendly (not just commit messages)
- [ ] Migration guide tested by someone who didn't write it
- [ ] Version number increment is correct (MAJOR/MINOR/PATCH)

**Final Sign-Off:**
```markdown
## Release Approval: Reference Distribution v2.1.0

**Validation Report:** PASS (8/8 mandatory checks, 1 advisory warning)
**Migration Tested:** Yes (project-alpha, 1.5 hours, no blockers)
**Approvals:**
- [x] Methodology Architect (Jane Doe) - 2026-02-23
- [x] Senior Practitioner (John Smith) - 2026-02-23
- [x] Governance Reviewer (Alice Johnson) - 2026-02-23

**Advisory Warning:**
- A-002: Diagram in Chapter 7 flagged as potentially stale (text updated 2026-02-20, diagram last updated 2026-01-15)
- **Resolution:** Reviewed diagram, no changes needed (text was clarification only, not structural change)

**Release Decision:** APPROVED for release 2026-02-24
```

---

## 11. Distribution Packaging and Delivery

### 11.1 Distribution Artifact Structure

**Reference Distribution Package:**

```
bsa-methodology-mcp-sop-reference-v2.1.0/
├── VERSION.json                          # Version metadata (required)
├── CHANGELOG.md                          # Human-readable changelog
├── LICENSE                               # License (Apache 2.0 / MIT / CC-BY-4.0)
├── README.md                             # Quick start guide
├── MANIFEST.txt                          # File listing with checksums
│
├── methodology/                          # BSA Methodology
│   ├── chapters/                         # 17 methodology chapters
│   │   ├── 01-introduction.md
│   │   ├── 02-service-discovery.md
│   │   └── ...
│   ├── templates/                        # 12 templates
│   │   ├── ai-persona-definition.md
│   │   ├── readiness-scorecard.md
│   │   └── ...
│   ├── schemas/                          # JSON schemas
│   │   ├── canonical-service-domain-model-schema.json
│   │   ├── measurement-blueprint-schema.json
│   │   └── ...
│   └── examples/                         # Example artifacts
│       ├── vesper-canonical-model.json
│       ├── sample-ai-persona-definition.md
│       └── ...
│
├── mcp-sop-protocol/                     # MCP+SOP Protocol
│   ├── protocol-spec.md                  # Protocol specification
│   ├── schemas/                          # UniversalSOPSchema, etc.
│   │   ├── universal-sop-schema-v2.0.0.yaml
│   │   └── ...
│   ├── examples/                         # Example SOPs
│   │   ├── example-research-sop.yaml
│   │   └── ...
│   └── tools/                            # Validation tools
│       ├── validate-sop.py
│       └── ...
│
├── docs/                                 # Additional documentation
│   ├── migrations/                       # Migration guides
│   │   ├── MIGRATION-1.x-to-2.0.md
│   │   └── MIGRATION-2.0-to-2.1.md
│   ├── adr/                              # Architecture Decision Records
│   │   ├── ADR-001-semver-versioning.md
│   │   └── ...
│   └── glossary.md                       # Terminology glossary
│
├── scripts/                              # Automation scripts
│   ├── validate-distribution.py          # Validation script
│   ├── migrate-2.0-to-2.1.py            # Migration automation
│   └── install-references.sh             # Installation script
│
└── dist/                                 # Distribution artifacts
    ├── validation-report-2.1.0.json      # Pre-release validation report
    ├── approval-manifest-2.1.0.json      # Approval signatures
    └── checksums.sha256                  # All file checksums
```

### 11.2 Installation Process

**Target Installation Path:** `.clause/agents/references/`

**Installation Script:**
```bash
#!/bin/bash
# install-references.sh
# Installs BSA Methodology + MCP+SOP Protocol references

VERSION=${1:-latest}
TARGET_DIR=".clause/agents/references"

echo "📦 Installing BSA Methodology + MCP+SOP Reference Distribution v${VERSION}"

# 1. Download distribution
echo "⬇️  Downloading..."
curl -L -o /tmp/references.tar.gz \
  "https://github.com/org/repo/releases/download/v${VERSION}/bsa-mcp-sop-reference-v${VERSION}.tar.gz"

# 2. Verify checksum
echo "🔐 Verifying integrity..."
curl -L -o /tmp/checksums.sha256 \
  "https://github.com/org/repo/releases/download/v${VERSION}/checksums.sha256"
sha256sum -c /tmp/checksums.sha256 || exit 1

# 3. Extract to target directory
echo "📂 Extracting to ${TARGET_DIR}..."
mkdir -p "${TARGET_DIR}"
tar -xzf /tmp/references.tar.gz -C "${TARGET_DIR}" --strip-components=1

# 4. Run post-install validation
echo "✅ Validating installation..."
python "${TARGET_DIR}/scripts/validate-distribution.py" \
  --version "${VERSION}" \
  --reference-path "${TARGET_DIR}" \
  --quick

# 5. Update project config
echo "⚙️  Updating .clause/config.json..."
jq ".references.bsa_methodology = \"${VERSION}\" | .references.installed_date = \"$(date -Iseconds)\"" \
  .clause/config.json > .clause/config.json.tmp && mv .clause/config.json.tmp .clause/config.json

echo "✅ Installation complete! Reference v${VERSION} installed at ${TARGET_DIR}"
echo "📖 Quick start: cat ${TARGET_DIR}/README.md"
```

**Usage:**
```bash
# Install latest version
./install-references.sh

# Install specific version
./install-references.sh 2.1.0

# Upgrade existing installation
./update-references.sh
```

### 11.3 Distribution Channels

| Channel | Purpose | Audience | Update Frequency |
|---------|---------|----------|------------------|
| **GitHub Releases** | Official releases with changelog | All projects | Every MAJOR/MINOR/PATCH |
| **npm Package** | Node.js projects | JavaScript/TypeScript developers | Mirror of GitHub releases |
| **PyPI Package** | Python projects | Python developers | Mirror of GitHub releases |
| **Docker Image** | Containerized reference (read-only) | CI/CD pipelines | Every MAJOR/MINOR |
| **CDN (jsDelivr)** | Fast global access (read-only) | Claude Code CLI | Real-time (cached 24h) |

**GitHub Release Format:**
```markdown
## Reference Distribution v2.1.0

**Release Date:** 2026-02-23
**Compatibility:** Agents requiring `>=2.0.0, <3.0.0`

### What's New
- Added Chapter 18: Multi-Region BSA Patterns
- Added new template: `xla-designer-extended.md`
- Updated canonical model schema to 2.1.0 (backward compatible)

### Breaking Changes
None (fully backward compatible with v2.0.x)

### Deprecations
- Old SOP format deprecated (removal in v3.0.0). Use UniversalSOPSchema instead.

### Migration Guide
No migration required. Drop-in replacement for v2.0.x.

### Downloads
- [bsa-mcp-sop-reference-v2.1.0.tar.gz](https://github.com/.../v2.1.0/.tar.gz) (5.2 MB)
- [checksums.sha256](https://github.com/.../v2.1.0/checksums.sha256)
- [validation-report-2.1.0.json](https://github.com/.../v2.1.0/validation-report-2.1.0.json)

### Validation
- ✅ 8/8 mandatory checks passed
- ⚠️ 1 advisory warning (diagram freshness in Chapter 7, reviewed and approved)

### Approvals
- Methodology Architect: Jane Doe (2026-02-23)
- Senior Practitioner: John Smith (2026-02-23)
- Governance Reviewer: Alice Johnson (2026-02-23)
```

---

## 12. Emergency Response Procedures

### 12.1 Critical Bug Hotfix Process

**Trigger:** Production-blocking bug discovered in released reference version

**Response Timeline:**

| Time | Action | Owner |
|------|--------|-------|
| **T+0** (Discovery) | Issue reported, severity assessed | Reporter |
| **T+1h** | Methodology Architect + Governance Reviewer notified | Maintainer |
| **T+2h** | Impact assessment, hotfix scope defined | Methodology Architect |
| **T+4h** | Hotfix developed, tested on 1 project | Maintainer |
| **T+6h** | Validation suite passed, approvals obtained | Governance Reviewer |
| **T+8h** | Hotfix released as PATCH (e.g., 2.1.1 → 2.1.2) | Maintainer |
| **T+24h** | All affected projects notified | Maintainer |
| **T+72h** | Post-mortem published | Methodology Architect |

**Hotfix Release Notes:**
```markdown
## Hotfix Release v2.1.2 (CRITICAL)

**Release Date:** 2026-02-24 (emergency release)
**Severity:** Critical (production-blocking)

### Issue
Schema validation error in canonical-model-validator skill causing false failures on valid models.

### Impact
Projects on v2.1.1 unable to validate canonical models → blocking architecture changes.

### Fix
Corrected regex pattern in `canonical-service-domain-model-schema.json` (line 47).

### Action Required
**IMMEDIATE UPGRADE** for all projects on v2.1.1.

### Upgrade Command
```bash
./update-references.sh 2.1.2
```

### Verification
After upgrade, run:
```bash
python .clause/agents/references/scripts/validate-distribution.py --quick
```
Expected output: `✅ Validation passed`

### Post-Mortem
[Link to post-mortem](https://github.com/org/repo/blob/main/docs/postmortems/2026-02-24-schema-regex-bug.md)
```

### 12.2 Security Vulnerability Response

**Trigger:** Security vulnerability discovered (e.g., in MCP+SOP protocol implementation)

**Severity Levels:**

| Severity | Description | Response Time | Example |
|----------|-------------|---------------|---------|
| **Critical** | Remote code execution, credential leak | 24 hours | SOP schema allows arbitrary code execution |
| **High** | Privilege escalation, data exposure | 7 days | Canonical model exposes sensitive tenant data |
| **Medium** | Denial of service, information disclosure | 30 days | Validation script crashes on malformed input |
| **Low** | Minor information leak, non-exploitable | Next PATCH | Version metadata reveals internal paths |

**Response Process (Critical/High):**

1. **Private Disclosure** (T+0) - Report received via security@example.com
2. **Verification** (T+4h) - Reproduce vulnerability, assess impact
3. **CVE Assignment** (T+24h) - Request CVE from MITRE
4. **Patch Development** (T+48h) - Fix vulnerability, backport to supported versions
5. **Private Notification** (T+72h) - Notify projects in registry (private email)
6. **Security Advisory** (T+7d) - Publish advisory after 80% of projects upgraded
7. **Public Disclosure** (T+30d) - Full details published (allows time for stragglers)

**Security Advisory Format:**
```markdown
## Security Advisory: BSA Reference v2.1.1 - Arbitrary Code Execution (CVE-2026-12345)

**Severity:** CRITICAL (CVSS 9.8)
**Affected Versions:** 2.1.0, 2.1.1
**Fixed In:** 2.1.2 (released 2026-02-24)

### Summary
The SOP schema validation allows arbitrary code execution via crafted YAML payloads.

### Impact
An attacker with access to modify SOP definitions can execute arbitrary Python code during validation.

### Mitigation
**IMMEDIATE ACTION REQUIRED:** Upgrade to v2.1.2 or higher.

### Upgrade Command
```bash
./update-references.sh 2.1.2
```

### Workaround (if immediate upgrade not possible)
Disable SOP validation until upgrade:
```bash
export SKIP_SOP_VALIDATION=1
```
**WARNING:** This disables security checks. Upgrade ASAP.

### Timeline
- 2026-02-20: Vulnerability reported privately
- 2026-02-24: Hotfix v2.1.2 released
- 2026-03-01: Public disclosure (7 days after fix, 85% of projects upgraded)

### Credits
Discovered by [Researcher Name] - responsible disclosure
```

### 12.3 Rollback Procedure

**When to Rollback:**
- Critical bug introduced in new version (>50% of projects affected)
- Undetected breaking change (migration script failed for most projects)
- Security regression (new version less secure than previous)

**Rollback Process:**

1. **Decision** - Methodology Architect + Governance Reviewer approve rollback
2. **Mark as Yanked** - Tag release as yanked on GitHub (still accessible but not recommended)
3. **Notify Projects** - "v2.2.0 yanked due to critical issue. Stay on v2.1.0 or upgrade to v2.2.1 (hotfix)"
4. **Root Cause Analysis** - Why did validation miss this issue?
5. **Improve Validation** - Add new checks to prevent similar issues
6. **Re-Release** - Fix issue, release v2.2.1 with stronger validation

**Yanked Release Notice:**
```markdown
## ⚠️ Release v2.2.0 YANKED

**Status:** YANKED (do not use)
**Reason:** Critical migration script bug causing data loss in canonical models
**Replacement:** v2.2.1 (released 2026-03-15)

### What Happened
Migration script from v2.1.0 → v2.2.0 incorrectly deleted custom fields in canonical models.

### If You Already Upgraded to v2.2.0
1. **Do not panic** - Backups should have your data
2. Restore canonical model from backup (pre-upgrade)
3. Upgrade to v2.2.1 (fixed migration script)

### If You Haven't Upgraded Yet
- **Do not upgrade to v2.2.0**
- Wait for v2.2.1 (released 2026-03-15)

### Post-Mortem
[Link to detailed post-mortem](https://github.com/org/repo/blob/main/docs/postmortems/2026-03-15-migration-data-loss.md)
```

---

## 13. Governance Review Cadence

### 13.1 Quarterly Governance Review

**Purpose:** Assess reference distribution health, adoption, and ecosystem feedback

**Attendees:**
- Methodology Architect (required)
- Governance Reviewer (required)
- 2 Senior Practitioners (required)
- Maintainers (optional)

**Agenda:**

1. **Adoption Metrics Review** (30 min)
   - Version distribution across projects
   - Migration completion rates
   - Blocker/issue analysis
   - Stale project outreach plan

2. **Methodology Evolution** (45 min)
   - Proposed new chapters (MINOR candidates)
   - Deprecation candidates
   - Field feedback on existing chapters
   - ADRs for upcoming MAJOR version

3. **Validation Effectiveness** (30 min)
   - False positive/negative rate in validation suite
   - Missed issues (slipped through validation)
   - New validation checks needed

4. **Security & Compliance** (15 min)
   - Security advisories review
   - Compliance with own governance policies
   - Audit of approval processes

5. **Action Items** (15 min)
   - Assign owners to follow-up tasks
   - Set targets for next quarter

**Deliverables:**
- Quarterly Governance Report (published to community)
- Action item tracker (tracked in GitHub Projects)

### 13.2 Annual Methodology Summit

**Purpose:** Major strategic planning for methodology evolution

**Attendees:**
- All governance roles
- 10+ senior practitioners from field
- Representatives from major projects

**Topics:**
- MAJOR version planning (if applicable)
- Long-term methodology direction (3-year roadmap)
- Community feedback synthesis
- Governance policy updates

**Outcome:**
- Methodology Roadmap (3-year horizon)
- MAJOR version approval (if planned)
- Governance policy v2.0 (if updates needed)

---

## 14. Appendices

### Appendix A: Version Number Decision Tree

```
Is this a breaking change (incompatible with previous version)?
├─ YES → MAJOR version bump (e.g., 2.x → 3.0)
│   └─ Examples: Schema incompatible, chapters removed, template structure changed
│
└─ NO → Is this new functionality (chapters, templates, features)?
    ├─ YES → MINOR version bump (e.g., 2.1 → 2.2)
    │   └─ Examples: New chapter added, new template added, new schema fields (optional)
    │
    └─ NO → PATCH version bump (e.g., 2.1.0 → 2.1.1)
        └─ Examples: Typo fixes, clarifications, updated examples, improved diagrams
```

### Appendix B: Approval Matrix

| Change Type | Methodology Architect | Senior Practitioners | Governance Reviewer | Total Approvals |
|-------------|---------------------|---------------------|---------------------|-----------------|
| MAJOR | Required | 2 required | Required (veto power) | 4 |
| MINOR | Required | 1 required | Advisory only | 2 |
| PATCH | Required | Advisory only | Advisory only | 1 |
| Hotfix | Required | Advisory only | Required | 2 |

### Appendix C: Validation Check Details

See Section 10.1 for full validation check specifications.

**Quick Reference:**

| Check ID | Type | Blocks Release? | Description |
|----------|------|-----------------|-------------|
| V-001 | Mandatory | Yes | Schema validity (JSON/YAML parsing) |
| V-002 | Mandatory | Yes | Template completeness (required sections) |
| V-003 | Mandatory | Yes | Cross-reference integrity (broken links) |
| V-004 | Mandatory | Yes | Methodology coherence (AI-assisted) |
| V-005 | Mandatory | Yes | Example validity (schema validation) |
| V-006 | Mandatory | Yes | Version metadata (VERSION.json) |
| V-007 | Mandatory | Yes | Changelog accuracy (entry exists) |
| V-008 | Mandatory | Yes | License compliance (headers present) |
| A-001 | Advisory | No | Writing quality (grammar, readability) |
| A-002 | Advisory | No | Diagram freshness (vs text updates) |
| A-003 | Advisory | No | Example coverage (1 per major concept) |
| A-004 | Advisory | No | Consistent terminology (glossary check) |

### Appendix D: SemVer Compatibility Examples

| Installed | Required by Agent | Compatible? | Reason |
|-----------|------------------|-------------|--------|
| 2.1.0 | `>=2.0.0, <3.0.0` | ✅ Yes | Within range |
| 2.1.0 | `>=2.1.0, <3.0.0` | ✅ Yes | Exact min match |
| 2.0.0 | `>=2.1.0, <3.0.0` | ❌ No | Below minimum |
| 3.0.0 | `>=2.0.0, <3.0.0` | ❌ No | Above maximum (breaking change) |
| 2.1.5 | `>=2.1.0, <2.2.0` | ✅ Yes | PATCH updates always compatible |
| 2.2.0 | `>=2.1.0, <3.0.0` | ✅ Yes | MINOR updates backward compatible |

### Appendix E: Contact Information

**Governance Roles:**
- **Methodology Architect:** methodology-architect@example.com
- **Governance Reviewer:** governance-reviewer@example.com
- **Senior Practitioners:** senior-practitioners@example.com
- **Maintainers:** maintainers@example.com

**Support Channels:**
- **GitHub Issues:** https://github.com/org/repo/issues
- **Security Reports:** security@example.com (PGP key: [link])
- **General Questions:** community@example.com
- **Migration Support:** migration-help@example.com

**Office Hours:**
- **Weekly:** Wednesdays 10:00-11:00 AM PST (Zoom link in Slack)
- **Migration Sprint:** First week of each quarter (daily support)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-02-23 | Governance Reviewer | Initial framework document |

---

**End of Governance Framework**

**Next Steps:**
1. Review by Methodology Architect (approval required)
2. Review by 2 Senior Practitioners (feedback period: 7 days)
3. Publish to community for comment (30-day comment period)
4. Ratify as official governance policy (target: 2026-03-31)

**Related Documents:**
- [Agent Distribution Plan](AGENT-DISTRIBUTION.md)
- [Architecture Gaps Register](ARCHITECTURE-GAPS.md)
- [BSA Methodology Repository](https://github.com/org/agentic-solution-architecture-methodology)
