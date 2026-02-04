# Config File Refactoring

## Contents

- [Philosophy](#philosophy)
- [What Belongs Where](#what-belongs-where)
- [Refactoring Strategies](#refactoring-strategies)
- [Measuring Content Value](#measuring-content-value)
- [Quick Reference](#quick-reference)
- [Guided Refactoring Process](#guided-refactoring-process)
- [Extraction Template](#extraction-template)

## Philosophy

Config files (CLAUDE.md, etc.) should contain:
- Quick reference information needed in every session
- Project-wide conventions and patterns
- Critical prerequisites and gotchas

Skills should contain:
- Multi-step workflows
- Situation-specific knowledge (applies only in certain contexts)
- Detailed procedures that would clutter the main config

## What Belongs Where

### Keep in Config Files

- Project tech stack overview
- Build/test/lint commands
- Required environment variables (names, not values)
- Naming conventions
- File structure overview
- Critical "always do" / "never do" rules
- Small, universal learnings (<3 lines)

### Move to Skills

- Step-by-step procedures (>5 steps)
- Conditional workflows (if X then Y)
- Detailed debugging guides
- Integration-specific patterns
- Infrequently needed reference material
- Large learnings (>30 lines)
- Situation-specific knowledge

## Refactoring Strategies

When a config file exceeds the threshold:

### Strategy 1: Extract Workflow Skills

Identify multi-step processes in the config and convert to skills:
- "When adding a new component..." → `add-component` skill
- "To debug production issues..." → `debug-production` skill
- "For database migrations..." → `database-migration` skill

### Strategy 2: Extract Domain Skills

Group related learnings by domain:
- All testing guidance → `testing-patterns` skill
- All API patterns → `api-conventions` skill
- All deployment steps → `deployment` skill

### Strategy 3: Create Reference Files

For skills with dense reference material:
- Move tables and lists to `references/` subdirectory
- Keep main SKILL.md focused on workflow
- Link to references: `See [references/details.md](references/details.md)`

## Measuring Content Value

When evaluating what to keep vs. extract:

| Keep (High Value) | Extract (Lower Frequency) |
|-------------------|--------------------------|
| Used every session | Used occasionally |
| Prevents common errors | Handles edge cases |
| Universal to project | Specific to subsystem |
| Quick reference | Detailed procedure |
| < 5 lines | > 10 lines |

## Quick Reference

| Condition | Action |
|-----------|--------|
| Multi-step workflow (>5 steps) | Create new skill |
| Existing skill covers topic | Update that skill |
| Config file exceeds threshold | Refactor first OR create skill |
| Situation-specific learning | Create skill |
| Learning >30 lines | Prefer skill |
| Learning <3 lines | Prefer config |
| Small, universal learning | Add to config |

## Guided Refactoring Process

When a user chooses to extract existing content before adding new learnings:

### 1. Analyze Existing Content

Identify extractable sections:

```
Analyzing [filename]...

Found extractable sections:
- Lines 45-120: Testing workflow (75 lines) → Suggest: `testing-workflow` skill
- Lines 200-280: API patterns (80 lines) → Suggest: `api-patterns` skill
- Lines 300-350: Deployment steps (50 lines) → Suggest: `deployment` skill

Extracting these would reduce file to ~295 lines.
```

### 2. Confirm Extraction Targets

Ask user which sections to extract.

### 3. Create Skills

For each confirmed extraction, create `skills/[name]/SKILL.md` with extracted content and add reference to config file: `See [skill-name] skill for [topic]`

### 4. Remove Extracted Content

Delete moved sections from config.

### 5. Add New Learning

Now add the original learning.

## Extraction Template

When creating skills from extracted content:

```markdown
---
name: [extracted-topic]
description: [Brief description derived from section header]
---

# [Section Title]

[Extracted content, reformatted as workflow if applicable]
```
