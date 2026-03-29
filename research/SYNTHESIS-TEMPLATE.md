# Research Synthesis Template

> Use this template when creating per-skill synthesis documents from the research library.
> A synthesis is a 1-2 page distillation of ALL relevant research for a single skill.

## Structure

```markdown
# [Skill Name] — Research Synthesis

## Decision Summary
- Technology choice: [X over Y because Z]
- Architecture pattern: [brief description]
- Key constraints: [what limits the design]

## Requirements (from research)
1. [Requirement] — Source: [paper #]
2. [Requirement] — Source: [paper #]
...

## Design Rules (machine-checkable where possible)
- Rule 1: [description] — Check: [how to verify]
- Rule 2: ...

## Recommended Libraries/APIs
| Library | Purpose | Install | License |
|---------|---------|---------|---------|

## Open Questions
- [Question not answered by research]

## Sources
- [Paper #]: [specific sections referenced]
```

## When to Create a Synthesis

Create one synthesis per skill BEFORE implementation begins. The synthesis replaces reading 5-8 full research papers — it extracts only what that specific skill needs.

## Synthesis Naming Convention

`research/synthesis-[skill-name].md`

Examples:
- `research/synthesis-imagegen-bridge.md`
- `research/synthesis-slide-stylist.md`
- `research/synthesis-deck-qa.md`
