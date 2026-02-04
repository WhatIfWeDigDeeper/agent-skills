# Documentation Size Management

## Philosophy

Config files (CLAUDE.md, etc.) should contain:
- Quick reference information needed in every session
- Project-wide conventions and patterns
- Critical prerequisites and gotchas

Skills should contain:
- Multi-step workflows
- Situation-specific knowledge (applies only in certain contexts)
- Detailed procedures that would clutter the main config

## Size Thresholds

| File Type | Healthy | Warning | Oversized |
|-----------|---------|---------|-----------|
| CLAUDE.md | < 400 | 400-500 | > 500 |
| GEMINI.md | < 400 | 400-500 | > 500 |
| AGENTS.md | < 400 | 400-500 | > 500 |
| .cursorrules | < 300 | 300-400 | > 400 |
| .cursor/rules/*.mdc | < 100 each | 100-150 | > 150 |
| .github/copilot-instructions.md | < 400 | 400-500 | > 500 |
| .windsurf/rules/rules.md | < 400 | 400-500 | > 500 |

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
| Config file >500 lines | Refactor first OR create skill |
| Situation-specific learning | Create skill |
| Learning >30 lines | Prefer skill |
| Learning <3 lines | Prefer config |
| Small, universal learning | Add to config |
