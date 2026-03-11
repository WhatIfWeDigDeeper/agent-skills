---
name: learn
description: >-
  Extracts lessons learned from conversations and persists them to AI assistant
  config files (CLAUDE.md, GEMINI.md, AGENTS.md, Cursor, Copilot, Windsurf,
  Continue) or creates new skills from discovered workflows.
  Use this skill whenever: a command failed then succeeded (especially with a
  flag or env change), debugging revealed a workaround, an assumption proved
  wrong, undocumented behavior was discovered, a multi-step pattern was
  invented on the fly, or the user says "/learn", "remember this", "save this",
  "add this to CLAUDE.md", "don't forget this", or "make a skill for this".
  Also invoke proactively after any complex troubleshooting session where
  notable lessons emerged, even if the user didn't explicitly ask.
license: MIT
compatibility: Requires bash shell and file system write access
metadata:
  author: Gregory Murray
  repository: github.com/whatifwedigdeeper/agent-skills
  version: "0.6"
---

# Learn from Conversation

Analyze the conversation to extract lessons learned, then persist them to AI assistant configuration files or new skills.

## Arguments

Optional text to narrow what to learn (e.g. `sandbox workaround`, `that build fix`).

If `$ARGUMENTS` is `help`, `--help`, `-h`, or `?`, skip the workflow and read [references/options.md](references/options.md).

If `$ARGUMENTS` is a non-empty, non-help string, use it as a focus filter in Step 2: only surface learnings related to the specified topic, skip unrelated findings.

## Process

### 1. Detect Configurations and Existing Skills

```bash
for f in CLAUDE.md GEMINI.md AGENTS.md .cursorrules .github/copilot-instructions.md \
  .windsurf/rules/rules.md .continuerc.json; do
  [ -f "$f" ] && wc -l "$f"
done
find .cursor/rules -name "*.mdc" -exec wc -l {} \; 2>/dev/null
find . -name "SKILL.md" -type f 2>/dev/null | grep -v node_modules | \
  xargs grep -l "^name:" | while read -r f; do grep -m1 "^name:" "$f" | sed 's/name: //'; done
```

**Config detection:**
- Single config found → use it
- Multiple configs found → stop and ask before proceeding:
  ```
  Found multiple config files:
  1. CLAUDE.md (142 lines)
  2. .github/copilot-instructions.md (38 lines)

  Which should I update? (enter number, or "all")
  ```
- No configs found → show init commands from [references/assistant-configs.md](references/assistant-configs.md) and exit

**Size thresholds** for any config file:
- < 400 lines: healthy, add directly
- 400–500 lines: add carefully, note the file is getting large
- > 500 lines: offer to [refactor](references/refactoring.md) before adding

### 2. Analyze Conversation

Scan for learnings the user would want to carry forward:
- **Corrections**: commands retried with a flag or env change, wrong assumptions corrected
- **Discoveries**: undocumented behavior, integration quirks, environment requirements
- **Workflows**: multi-step patterns invented during the session that should be repeatable
- **Instruction violations**: if the user had to remind you of something already in the config, note it — the wording may need strengthening, not a new rule

### 3. Route Each Learning

For each learning, decide where it belongs:

1. **Does this feel like a procedure someone would invoke repeatedly?** Think: deployment runbooks, release checklists, debugging workflows, multi-phase processes where sequence matters or there are conditional branches. If yes → Create a new skill (Route C).
2. **Does an existing skill cover this topic?** → Update that skill (Route B)
3. **Is the config file oversized (>500 lines)?** → Create a skill or offer refactoring
4. **Is this situation-specific (narrow context, rarely applies)?** → Create a skill
5. Otherwise → Add to config file (Route A)

Short facts (<3 lines) go to the config file even when near the threshold. Large learnings (>30 lines) strongly prefer a new skill.

### 4. Present Plan and Wait for Confirmation

Show everything you plan to do before touching any files:

```
**[Category]**: [Brief description]
- Source: [what triggered this learning]
- Proposed change: [exact text to add]
- Destination: [file] ([current lines] → [projected lines])
```

If multiple learnings, list them all, then ask:
```
Ready to apply. Approve all, or review each one?
```

**Do not modify any files until the user responds to this step.**

### 5. Apply Changes

**Route A — Config file** (CLAUDE.md, GEMINI.md, etc.): find the appropriate section, preserve existing structure, append or create a section. See [references/assistant-configs.md](references/assistant-configs.md) for format details.

**Route B — Existing skill**: read `skills/[name]/SKILL.md`, append to the relevant section, maintain existing structure.

**Route C — New skill**: create `skills/[name]/SKILL.md`:
```markdown
---
name: [topic]
description: [when to use this and what it does]
---

# [Topic]

## Process

### 1. [First Step]
[Details]
```

### 6. Summarize

List what changed: files modified, sections updated, skills created.

## Guidelines

- **Be minimal**: only add what genuinely helps future sessions
- **Avoid duplication**: check for similar content before adding
- **Prefer specificity**: "Run `npm run dev` before e2e tests" beats "ensure services are running"
- **Focus on non-obvious**: skip things any developer would know; capture what surprised you
