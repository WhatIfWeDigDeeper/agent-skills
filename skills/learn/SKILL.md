---
name: learn
description: Analyzes conversations to extract lessons learned (corrections, discoveries, workarounds) and persists them to AI assistant configuration files. Supports CLAUDE.md, GEMINI.md, AGENTS.md, Cursor rules, GitHub Copilot instructions, Windsurf rules, and Continue config. Use after completing tasks that involved retries, debugging, finding workarounds, or discovering undocumented behavior.
arguments: Optional - specific assistant names to target (e.g., "claude cursor")
license: MIT
metadata:
  author: Gregory Murray
  repository: github.com/whatifwedigdeeper/agent-skills
  version: "0.3"
---

# Learn from Conversation

Analyze the conversation to extract lessons learned, then persist them to AI assistant configuration files.

## Supported Assistants

| Assistant | Config File | Format |
|-----------|-------------|--------|
| Claude Code | `CLAUDE.md` | Markdown |
| Gemini | `GEMINI.md` | Markdown |
| AGENTS.md | `AGENTS.md` | Markdown |
| Cursor | `.cursorrules` or `.cursor/rules/*.mdc` | Markdown/MDC |
| GitHub Copilot | `.github/copilot-instructions.md` | Markdown |
| Windsurf | `.windsurf/rules/rules.md` | Markdown |
| Continue | `.continuerc.json` | JSON |

See [references/assistant-configs.md](references/assistant-configs.md) for format details.

## Process

### 1. Detect Assistant Configurations

Scan for existing config files:

```bash
[ -f "CLAUDE.md" ] && echo "claude"
[ -f "GEMINI.md" ] && echo "gemini"
[ -f "AGENTS.md" ] && echo "agents"
[ -f ".cursorrules" ] && echo "cursor-legacy"
[ -d ".cursor/rules" ] && echo "cursor"
[ -f ".github/copilot-instructions.md" ] && echo "copilot"
[ -f ".windsurf/rules/rules.md" ] && echo "windsurf"
[ -f ".continuerc.json" ] && echo "continue"
```

**Behavior based on detection:**

| Scenario | Action |
|----------|--------|
| Single config found | Update it automatically |
| Multiple configs found | Prompt user to select which to update |
| No configs found | Guide user to initialize one first, then exit |

**When no configs found**, display:
```
No AI assistant configuration files detected.

Please initialize one first using your assistant's setup command:
- Claude Code: claude /init
- Cursor: Create .cursorrules or use Settings
- Copilot: Create .github/copilot-instructions.md
- Gemini: Create GEMINI.md
- Universal: Create AGENTS.md

Then run /learn again.
```

### 2. Assess Documentation Capacity

Before analyzing the conversation, check the state of target files and discover relevant skills.

#### Check Config File Sizes

For each detected config file, count lines:

```bash
wc -l CLAUDE.md 2>/dev/null || echo "0"
wc -l GEMINI.md 2>/dev/null || echo "0"
wc -l AGENTS.md 2>/dev/null || echo "0"
wc -l .cursorrules 2>/dev/null || echo "0"
wc -l .github/copilot-instructions.md 2>/dev/null || echo "0"
wc -l .windsurf/rules/rules.md 2>/dev/null || echo "0"
```

#### Size Thresholds

| Lines | Status | Action |
|-------|--------|--------|
| < 400 | Healthy | Add learnings directly |
| 400-500 | Warning | Add carefully, suggest cleanup |
| > 500 | Oversized | Refactor before adding new content |

See [references/size-management.md](references/size-management.md) for detailed guidance.

#### Discover Existing Skills

Scan for skills that might relate to learnings:

```bash
# Find all skills in the project
find . -name "SKILL.md" -type f 2>/dev/null | grep -v node_modules

# Extract skill names and descriptions for matching
for skill in $(find . -name "SKILL.md" -type f 2>/dev/null | grep -v node_modules); do
  echo "=== $skill ==="
  head -20 "$skill" | grep -E "^(name:|description:)"
done
```

Store discovered skills for routing decisions in Step 4.

### 3. Analyze Conversation

Scan for:
- **Corrections**: Commands retried, assumptions proven wrong, missing prerequisites
- **Discoveries**: Undocumented patterns, integration quirks, environment requirements
- **Improvements**: Steps that should be automated or validated earlier

### 4. Categorize and Route Each Learning

| Category | Primary Destination | Fallback When Oversized |
|----------|---------------------|------------------------|
| Project facts | Config file | Extract to new skill |
| Prerequisites | Config file | Extract to `project-setup` skill |
| Environment | Config file | Extract to `environment-setup` skill |
| Workflow pattern | Existing related skill | Create new skill |
| Automated workflow | New skill | New skill (always) |

#### Routing Decision Tree

For each learning, evaluate in order:

1. **Is this a multi-step automated workflow (>5 steps)?**
   - YES → Create new skill (skip to step 7)
   - NO → Continue

2. **Does an existing skill cover this topic?**
   - YES → Update that skill
   - NO → Continue

3. **Is the target config file oversized (>500 lines)?**
   - YES → Create new skill OR offer refactoring (see Step 6)
   - NO → Continue

4. **Is this learning situation-specific (applies to narrow context)?**
   - YES → Create new skill with `globs` or context constraints
   - NO → Add to config file

#### Size-Based Rules

| Learning Size | Preferred Destination |
|---------------|----------------------|
| < 3 lines | Config file (even if near threshold) |
| 3-30 lines | Follow decision tree above |
| > 30 lines | Strongly prefer skill creation |

#### Skill Relevance Matching

Match learnings to existing skills using these criteria:

| Learning Topic | Matching Skill Indicators |
|----------------|--------------------------|
| Testing patterns | Skill name contains: test, spec, e2e, unit |
| Build/compile issues | Skill name contains: build, compile, bundle |
| Dependencies | Skill name contains: package, dependency, npm, yarn |
| API patterns | Skill name contains: api, http, fetch, request |
| Database | Skill name contains: db, database, migration, schema |
| Deployment | Skill name contains: deploy, release, ci, cd |

Also check skill `description` field for keyword overlap with the learning topic.

### 5. Present and Confirm

For each learning, show:
```
**[Category]**: [Brief description]
- Source: [What happened in conversation]
- Proposed change: [Exact text or file to add]
- Destination(s): [List of config files to update]
```

Ask for confirmation before applying each change.

### 6. Handle Oversized Config Files

If a target config file exceeds 500 lines BEFORE adding new learnings:

#### Prompt User

```
Config file [filename] has [X] lines (threshold: 500).

Options:
1. Add learning anyway (not recommended)
2. Extract existing content to skills first, then add learning
3. Create a new skill for this learning instead
4. Skip this config file

Choose an option:
```

#### Option 2: Guided Refactoring

If user selects refactoring:

1. **Analyze existing content** - Identify extractable sections:
   ```
   Analyzing [filename]...

   Found extractable sections:
   - Lines 45-120: Testing workflow (75 lines) → Suggest: `testing-workflow` skill
   - Lines 200-280: API patterns (80 lines) → Suggest: `api-patterns` skill
   - Lines 300-350: Deployment steps (50 lines) → Suggest: `deployment` skill

   Extracting these would reduce file to ~295 lines.
   ```

2. **Confirm extraction targets** - Ask user which to extract

3. **Create skills** - For each confirmed extraction:
   - Create `skills/[name]/SKILL.md` with extracted content
   - Add reference to config file: `See [skill-name] skill for [topic]`

4. **Remove extracted content** - Delete moved sections from config

5. **Add new learning** - Now add the original learning

#### Extraction Template

When creating skills from extracted content:

```markdown
---
name: [extracted-topic]
description: [Brief description derived from section header]
---

# [Section Title]

[Extracted content, reformatted as workflow if applicable]

## Source

Extracted from [config-file] during documentation maintenance.
```

### 7. Apply Changes

Apply changes based on routing decision from Step 4:

#### Route A: Add to Config File

**Markdown configs** (CLAUDE.md, GEMINI.md, AGENTS.md, Copilot, Windsurf):
- Find appropriate section, preserve existing structure
- Append to relevant section or create new section if needed

**Cursor rules**:
- Legacy `.cursorrules`: Treat like markdown, append content
- Modern `.cursor/rules/*.mdc`: See [references/format-cursor-mdc.md](references/format-cursor-mdc.md)

**Continue** (`.continuerc.json`):
- Update `customInstructions` field, preserving existing content
- See [references/format-continue.md](references/format-continue.md)

#### Route B: Update Existing Skill

When adding to an existing skill:

1. Read the skill file: `skills/[name]/SKILL.md`
2. Find appropriate section or create new one
3. Append learning, maintaining the skill's existing structure
4. If skill has references, consider adding to reference file instead

**Skill update format:**
```markdown
## [New Section or append to existing]

[Learning content formatted as guidance or workflow step]
```

#### Route C: Create New Skill

Create in `skills/[name]/SKILL.md` with this template:

```markdown
---
name: [learning-topic]
description: [One-line description of what this handles]
---

# [Learning Topic]

[Learning content structured as workflow]

## When to Use

[Context/triggers for this skill]

## Process

### 1. [First Step]
[Details]
```

### 8. Summarize

List:
- Config files modified (with full paths)
- Sections updated in each file
- Any skills created

## Examples

| Situation | Learning |
|-----------|----------|
| "e2e tests failed because API wasn't running" | Add prerequisite to selected config(s) |
| "Parse SDK doesn't work with Vite out of the box" | Document workaround in selected config(s) |
| "Build failed because NODE_ENV wasn't set" | Add required env var to selected config(s) |
| "Every component needs tests, lint, build..." | Create `add-component` skill |

## Edge Cases

| Scenario | Handling |
|----------|----------|
| No configs detected | Guide user to initialize one first, exit early |
| Multiple configs found | Prompt user to select which to update |
| Malformed config file | Warn and skip that file |
| Duplicate content exists | Check before adding, warn if similar learning exists |
| Config file already oversized | Offer refactoring before adding (Step 6) |
| Learning matches multiple skills | Present options, let user choose which skill to update |
| Skill file also oversized | Suggest creating sub-skills or reference files |
| Learning is very small (<3 lines) | Prefer config file even if near threshold |
| Learning is very large (>30 lines) | Strongly suggest skill creation |
| No existing skills found | Skip skill matching, proceed with config or new skill |

## Guidelines

- **Be specific**: Include exact commands, paths, error messages
- **Be minimal**: Only add what genuinely helps future sessions
- **Avoid duplication**: Check for existing similar content in all selected configs
- **Preserve structure**: Fit into existing config file organization
- **Respect format**: Adapt content appropriately for each assistant's format
