# Cursor MDC Format

Cursor's modern rules use MDC (Markdown Components) format with YAML frontmatter.

## File Location

Rules are stored in `.cursor/rules/` directory with `.mdc` extension:

```
.cursor/
  rules/
    project-conventions.mdc
    testing-patterns.mdc
    api-guidelines.mdc
```

## MDC Structure

```markdown
---
description: Brief description of when this rule applies
globs: ["**/*.ts", "**/*.tsx"]
alwaysApply: false
---

# Rule Title

Rule content in markdown...
```

## Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `description` | Yes | When/why this rule applies |
| `globs` | No | File patterns to match (e.g., `["*.ts"]`) |
| `alwaysApply` | No | Always include in context (default: false) |

## Adding Learnings

**Option 1: Create new rule file** (recommended for distinct topics)

Create a new `.mdc` file for each learning category:
- `.cursor/rules/api-patterns.mdc`
- `.cursor/rules/testing-conventions.mdc`

**Option 2: Append to existing file**

Find the most relevant existing `.mdc` file and append a new section.

## Example

```markdown
---
description: API error handling patterns for this project
globs: ["src/api/**/*.ts", "src/services/**/*.ts"]
---

# API Error Handling

Always wrap API calls in try-catch and use the custom ApiError class:

\`\`\`typescript
try {
  const result = await apiClient.fetch(endpoint);
} catch (error) {
  throw new ApiError(error.message, error.status);
}
\`\`\`
```

## Legacy Format (.cursorrules)

The legacy `.cursorrules` file in the project root is plain markdown without frontmatter. Treat it like CLAUDE.md - find the appropriate section and append content.
