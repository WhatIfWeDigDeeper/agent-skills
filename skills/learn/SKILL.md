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
  version: "1.1"
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
- Multiple configs found → check for a reciprocal "always both" rule first; if absent, prompt:

  **Step 1a — Mirror-rule detection.** `rg` each detected config for the Step 4 mirror-rule patterns (`keep .* in sync`, `mirror .* to`, `apply the equivalent change`). Record which configs contain a mirror-rule that names at least one other detected config.

  **Step 1b — Reciprocal "always both" auto-skip.** Within ~5 lines of each detected mirror-rule, search for unambiguous fan-out intent using:
  ```
  (always (update|apply) (to )?both|apply to both|without asking|do not prompt)
  ```
  If **every** detected config contains both (1) a mirror-rule that names the others **and** (2) an "always both" phrase within ~5 lines of that mirror-rule, skip the prompt. Print a one-line notice on its own line and proceed as if the user had answered `all`:
  ```
  Detected reciprocal "always both" rule across <config1> and <config2> — applying to all without prompting.
  ```
  Any miss, one-sided declaration, or weaker wording (e.g. `consider mirroring`, `may want to mirror`) → keep the prompt behavior in Step 1c.

  **Step 1c — Prompt.** When the auto-skip condition is not met, stop and ask:
  ```
  Found multiple config files:
  1. CLAUDE.md (142 lines)
  2. .github/copilot-instructions.md (38 lines)

  Which should I update? (enter number, or "all")
  ```
  If one config contains a mirror-rule naming another (from Step 1a) without the "always both" phrase, surface that in the prompt as informational context — but the user's choice still binds. An explicit user answer at this prompt always overrides Step 1b's auto-skip; if the user later expresses a narrower scope at the Step 5 confirmation, that also binds.
- No configs found → **MANDATORY: read [`references/assistant-configs.md`](references/assistant-configs.md) in full** to show init commands, then exit. Do NOT load `refactoring.md` or `options.md` at this step.

**Size thresholds** for any config file:
- < 400 lines: healthy, add directly
- 400–500 lines: add carefully, note the file is getting large
- > 500 lines: **MANDATORY: read [`references/refactoring.md`](references/refactoring.md) in full** before proceeding, then offer to refactor. Do NOT load `assistant-configs.md` for this path unless also applying Route A changes.

### 2. Analyze Conversation

Default is **reject**. Each candidate learning must earn inclusion by passing three filters in order:

1. **Would I forget this?** If any developer already knows it (`npm install` before `npm start`, commit before switching branches, read errors carefully), skip it. Baseline knowledge dilutes the config and trains agents to skim.
2. **Is this already covered?** Search existing config entries for the topic — if found, tightening the wording beats adding a second rule.
3. **Is this universal or local?** Environment-specific workarounds (broken keyring, one repo's tooling quirk) must carry a scope qualifier, not be globalized.

Only candidates that survive all three get scanned for shape:
- **Corrections**: commands retried with a flag or env change, wrong assumptions corrected
- **Discoveries**: undocumented behavior, integration quirks, environment requirements
- **Workflows**: multi-step patterns invented during the session that should be repeatable
- **Instruction violations**: if the user had to remind you of something already in the config, the wording may need strengthening, not a new rule
- **Contradictions**: does this learning conflict with or supersede existing content? Flag for replacement, not addition — even if the user didn't call out the conflict

If nothing passes the filters, tell the user nothing non-obvious was found and exit — do not fabricate learnings to justify the invocation.

### 3. Route Each Learning

For each learning, ask: **would someone invoke this by name?** If you can imagine a user saying "run the [X] workflow," it's a skill. If not, it's a config entry.

1. **Is this a multi-step procedure someone would run as a workflow?** If the learning has 3+ numbered steps that execute in sequence — even if project-specific — it belongs in a new skill. Deploy checklists, release runbooks, "add an X" workflows are all skills. Single facts and gotchas are config. If yes → Route C (new skill).
2. **Does an existing skill cover this topic?** → Route B (update that skill)
3. **Is the config file oversized (>500 lines)?** → Route C or offer refactoring
4. Otherwise → Route A (config file)

The cleanest signal: **if it takes more than one command to execute, it probably belongs in a skill; if it's a single fact to remember, it belongs in the config.**

### 4. Preserve Cross-Config Sync Rules

**Scope: Markdown-based configs only** — `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `.github/copilot-instructions.md`, `.cursorrules`, `.windsurf/rules/rules.md`. Out of scope: `.cursor/rules/*.mdc` and `.continuerc.json` (non-Markdown formats; mirror-rule detection there is a follow-up).

Within the Markdown scope, when multiple configs are present:

1. **Detect** mirror-rule text in each detected config — patterns like `keep ... in sync`, `mirror ... to`, `apply the equivalent change to`, near another config's filename.
2. **Respect the Step 1 choice.** Operate only on the configs the user chose. A mirror-rule in an *unchosen* config does **not** trigger fan-out — the user may have deliberately scoped this learning narrowly (e.g., the Copilot file is style-scoped).
3. **Preserve** mirror-rule text during every edit. Do not clobber it with a section rewrite.
4. **Reciprocate.** For any chosen config that lacks a mirror-rule referencing the other chosen configs, add one (e.g., add `Keep CLAUDE.md in sync: mirror rule changes back to CLAUDE.md` to the top of `.github/copilot-instructions.md` if it had no reciprocal rule).

**Why:** The mirror-rule is load-bearing — it is how future sessions know to keep configs in sync. Silently updating one config without the other, or deleting the mirror-rule during a rewrite, lets the configs drift and the rule die. User choice still binds because narrower scoping is often legitimate.

### 5. Present Plan and Wait for Confirmation

Before showing the plan, **audit each drafted rule body against the Principles' "Minimum viable rule text" check** — apply "is this the min chars necessary?" to every clause and cut any clause you can't defend (incident narratives, multi-clause rationales, explanatory prose beyond a concrete example). First-draft text routinely needs trimming; the audit is not optional.

Then show everything you plan to do:

```
**[Category]**: [Brief description]
- Source: [what triggered this learning]
- Proposed change: [exact text to add, post-audit]
- Destination: [file] ([current lines] → [projected lines])
```

If multiple learnings, list them all, then ask:
```
Ready to apply. Approve all, or review each one?
```

**Do not modify any files until the user responds to this step.**

### 6. Apply Changes

**Route A — Config file** (CLAUDE.md, GEMINI.md, etc.): **MANDATORY: read [`references/assistant-configs.md`](references/assistant-configs.md) in full** for format and section conventions before writing. Do NOT load `refactoring.md` for this route unless the file is also over 500 lines. Before appending, search the existing config for related content — if found, propose an update-in-place rather than a duplicate entry, and if the new rule contradicts an existing one, name the conflict explicitly in the summary (Principle 4). Then find the appropriate section, preserve existing structure, append or create a section. Apply Step 4's sync-rule preservation during every write.

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

### 7. Summarize

List files modified with before/after line counts, sections updated or created, and any skills created with their names. If a contradiction was resolved, name it explicitly — which rule conflicted with which, and which version was kept. If cross-config sync rules were honored (preserved or reciprocated), mention that too.

**Issues filed this session.** Scan the session's tool-call history for `gh issue create` invocations and for any URLs matching `https?://github\.com/[^/]+/[^/]+/issues/\d+` produced during the session. If any were filed, render them under an **Issues filed this session** subheading, one bullet per issue:

```
### Issues filed this session
- #301 — CI: split verify-pr.yaml into per-stack workflows
  https://github.com/owner/repo/issues/301
```

Omit the subheading entirely if none were filed. Deduplicate by issue number (different URLs that resolve to the same issue collapse to one bullet). The title may not always be recoverable from session output — when missing, omit the `— <title>` segment and keep the URL.

## Principles

1. **Reject noise; include only non-obvious lessons.** A bloated config trains agents to skim. If any developer already knows it ("npm install before npm start", "commit before switching branches"), skip it — and say which items you rejected so the user can override.
2. **Annotate scope; never globalize a one-off fix.** A workaround that worked today may harm tomorrow's session if the environment differs. Label the condition that triggered the fix (broken keyring, specific macOS version, this repo's build quirk) so future agents can decide whether it applies. Use qualifiers like "when X fails" or "as a fallback after Y", not unconditional "always use Z" phrasing.
3. **One topic, one location.** If a rule already exists anywhere in the config or a skill, update that entry. Two entries on the same topic create ambiguity — the agent follows whichever it reads first, which may be the weaker version. Tightening the existing wording beats appending a parallel bullet.
4. **Surface contradictions; never silently duplicate or replace.** If a learning conflicts with existing content, propose replacement with the conflict named explicitly in the plan and summary ("this supersedes the existing X rule because Y"). A silent replace leaves the user unaware the rule changed; silent duplicates cause inconsistent agent behavior depending on which one is read first.
5. **Minimum viable rule text.** Every clause must be load-bearing — the rule, the fix, a non-obvious "why", or a concrete example. Draft, then audit with **"is this the min chars necessary?"** Cut any clause you can't defend. `` `cd dir && cmd` (skips cmd if cd fails) `` beats a paragraph on shell exit semantics; incident narratives and multi-clause consequences belong in commit messages, not the rule body.

**NEVER write vague learnings** — "be careful with deployments" teaches nothing; "run smoke tests against staging before promoting to prod because the CDN cache masks broken assets" is actionable and explains why. This one hard prohibition remains NEVER because specificity is the single non-negotiable input to every other principle.
