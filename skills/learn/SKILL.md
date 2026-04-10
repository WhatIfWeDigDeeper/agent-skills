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
  version: "0.7"
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
- No configs found → **MANDATORY: read [`references/assistant-configs.md`](references/assistant-configs.md) in full** to show init commands, then exit. Do NOT load `refactoring.md` or `options.md` at this step.

**Size thresholds** for any config file:
- < 400 lines: healthy, add directly
- 400–500 lines: add carefully, note the file is getting large
- > 500 lines: **MANDATORY: read [`references/refactoring.md`](references/refactoring.md) in full** before proceeding, then offer to refactor. Do NOT load `assistant-configs.md` for this path unless also applying Route A changes.

### 2. Analyze Conversation

Before scanning, ask yourself:
- **Would I forget this?** If the lesson is obvious to any developer, skip it.
- **Is this already covered?** Check existing config entries — maybe the wording just needs tightening, not a new rule.
- **Is this universal or local?** Environment-specific workarounds must be labeled, not globalized.

Scan for learnings the user would want to carry forward:
- **Corrections**: commands retried with a flag or env change, wrong assumptions corrected
- **Discoveries**: undocumented behavior, integration quirks, environment requirements
- **Workflows**: multi-step patterns invented during the session that should be repeatable
- **Instruction violations**: if the user had to remind you of something already in the config, note it — the wording may need strengthening, not a new rule
- **Contradictions**: does this learning conflict with or supersede something already in the config? If so, flag for replacement, not addition

If no learnings pass the "Would I forget this?" filter, tell the user nothing non-obvious was found and exit — do not fabricate learnings to justify the invocation.

### 3. Route Each Learning

For each learning, ask: **would someone invoke this by name?** If you can imagine a user saying "run the [X] workflow," it's a skill. If not, it's a config entry.

1. **Is this a multi-step procedure someone would run as a workflow?** If the learning has 3+ numbered steps that execute in sequence — even if project-specific — it belongs in a new skill. Deploy checklists, release runbooks, "add an X" workflows are all skills. Single facts and gotchas are config. If yes → Route C (new skill).
2. **Does an existing skill cover this topic?** → Route B (update that skill)
3. **Is the config file oversized (>500 lines)?** → Route C or offer refactoring
4. Otherwise → Route A (config file)

The cleanest signal: **if it takes more than one command to execute, it probably belongs in a skill; if it's a single fact to remember, it belongs in the config.**

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

**Route A — Config file** (CLAUDE.md, GEMINI.md, etc.): **MANDATORY: read [`references/assistant-configs.md`](references/assistant-configs.md) in full** for format and section conventions before writing. Do NOT load `refactoring.md` for this route unless the file is also over 500 lines. Before appending, search the existing config for related content — if found, propose an update-in-place rather than a duplicate entry. Then find the appropriate section, preserve existing structure, append or create a section.

**Route B — Existing skill**: read `skills/[name]/SKILL.md`, append to the relevant section, maintain existing structure.

**Route C — New skill**: create `skills/[name]/SKILL.md`. The description field determines whether the skill will ever be activated — it must state WHAT the skill does, WHEN to use it, and include trigger KEYWORDS (action verbs, file types, domain terms). A vague description like "helps with deployment" means the skill will never fire.

```markdown
---
name: [topic]
description: [WHAT it does + WHEN to use it + trigger keywords]
---

# [Topic]

## Process

### 1. [First Step]
[Details]
```

### 6. Summarize

List files modified with before/after line counts, sections updated or created, and any skills created with their names. If a contradiction was resolved, note which version was kept and why.

## NEVER

- **NEVER extract basics** — "npm install before running" or "save your work" are noise that dilutes the config; skip anything any developer already knows, because a bloated config trains agents to skim it
- **NEVER treat one-off emergency fixes as universal rules** — a workaround scoped to one repo's broken state will actively mislead future sessions where the state differs; always annotate environment-specific workarounds with the project or condition that triggered them
- **NEVER add a new config rule when an existing rule just needs stronger wording** — two entries covering the same topic create ambiguity; the agent will follow whichever it reads first, which may be the weaker version; re-read the existing entry and tighten it instead
- **NEVER create a skill just to keep the config file short** — skill fragmentation is harder to maintain than a 450-line CLAUDE.md; use the size thresholds in Step 1 to decide
- **NEVER create a skill for a 2-step workflow with no branching** — if it fits in 2 config lines, it belongs in the config; a skill requires a reason to invoke, which a 2-step note doesn't earn
- **NEVER silently duplicate a learning that contradicts existing content** — always surface the conflict to the user and propose which version to keep; silent contradictions cause agents to behave inconsistently depending on which rule they encounter first
- **NEVER write vague learnings** — "be careful with deployments" teaches nothing; "run smoke tests against staging before promoting to prod because the CDN cache masks broken assets" is actionable and explains why

## Guidelines

- **Prefer specificity**: `Run npm run dev before e2e tests` beats `ensure services are running` — vague rules train agents to interpret rather than follow
- **One learning, one location**: if it already exists anywhere in the config or a skill, update that entry rather than creating a second one
- **Strip obvious explanations from rule text**: include only the non-obvious directive; omit common-knowledge consequences. "Use `git fetch origin && git merge origin/main` when review comments exist" is enough — don't append "this creates a merge commit without rewriting history."
