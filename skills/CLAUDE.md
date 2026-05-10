# Skills

This file provides guidance when working in the `skills/` directory. It auto-loads in Claude Code when you read or edit files here.

## Skill Definition Format

Each skill follows this structure:

```markdown
---
name: skill-name
description: Brief description of what the skill does
license: MIT (optional)
compatibility: Runtime or access requirements (optional)
metadata: (optional)
  author: Author Name
  repository: github.com/org/repo
  version: "1.0"
---

# Skill Title

Workflow documentation with:
- Process sections numbered (### 1. Step Name)
- Bash code blocks for executable commands
- Tables for categorization/options
- Example outputs
```

Valid frontmatter fields: `name`, `description` (required), `license`, `compatibility`, `metadata` (optional). The skill-creator skill may suggest limiting to `name` and `description`, but all fields shown above are part of the skills spec and should not be flagged as violations.

**Skill description has a 500-character hard limit** — the `description` field in SKILL.md frontmatter is capped at 500 characters by the skills runtime. Keep descriptions concise; count characters before finalizing.

## Adding New Skills

1. Create directory: `skills/<skill-name>/`
2. Create `SKILL.md` following the format above
3. Include YAML frontmatter with name and description
4. Document the workflow with numbered process steps
5. Add bash code blocks for commands that should be executed
6. Include example outputs where helpful
7. Create a symlink so Claude Code can discover it: `ln -s ../../skills/<skill-name> .claude/skills/<skill-name>` (local only — `.claude/skills/` is gitignored). **After editing an existing skill, verify the symlink still resolves correctly** — a skill invocation may load a stale version if the symlink points to a cached or wrong path. **In a worktree, edit skills at the worktree path `skills/<name>/SKILL.md` — not via `.claude/skills/<name>/SKILL.md`**, which resolves to the main repo's copy. **Claude Code also caches skill content at session load** — edits to a skill file don't take effect until a fresh session is started.
8. Update `README.md` — add the skill to the table and add a notes section

When substantially modifying an existing skill, also update its entry in `README.md`.

**Bump the skill version** in the `metadata.version` frontmatter field on every change to a skill — any edit to SKILL.md or its reference files counts, including pure documentation refactors. There are no exempt change types. Use patch increments (e.g. `"0.7"` → `"0.8"`) for fixes and additions, minor increments (e.g. `"0.7"` → `"0.9"` or `"1.0"` → `"1.1"`) for significant workflow changes. This helps downstream users know when to pull updates. **Only bump once per PR**: before suggesting a version increment, run `git fetch origin && git diff origin/main -- skills/<name>/SKILL.md | rg '^\+  version:'` — if a bump already exists relative to `origin/main`, do not bump again for follow-up commits on the same branch. **When adding commits to address reviewer feedback within an active PR**, do not include an additional version bump — the version was already bumped in the PR's first substantive commit. Each reviewer-fix commit should touch only the files needed to address the feedback. Before committing *any* SKILL.md change on an active PR branch — not just when you intend to bump — re-run `git fetch origin && git diff origin/main -- skills/<name>/SKILL.md | rg '^\+  version:'` to confirm no bump already exists. **The "once per PR" limit applies to the PR as a whole** — a PR that touches SKILL.md plus multiple reference files still gets exactly one version increment total. Do not add a new bump for each changed reference file. **Exception: do not bump the version when a skill is first introduced** — a new skill's initial version (e.g. `"0.1"`) is set at creation time; the "once per PR" bump applies only to subsequent changes. Check `git diff --name-status origin/main...HEAD -- skills/<name>/SKILL.md`: `A` (added) means first introduction in this PR; `M` (modified) triggers the bump rule.

## Skill Design Patterns

- **Naming perspective**: Name skills from the user's action/role, not the underlying operation. E.g., `pr-comments` (author addressing feedback on their PR) not `pr-review` (which implies being the reviewer).
- **Prefer auto-detection with a disambiguation prompt over adding new flags** when a behavior is only needed in genuinely ambiguous situations. Check the state first, handle unambiguous cases silently (e.g., only unstaged changes present → auto-review with a note), and prompt only when intent is unclear (e.g., both staged and unstaged present → prompt `[staged/unstaged/all]`). Explicit flags can still be offered as an escape hatch for scripting, but should not be the primary interface.
- **Spec tracking files belong on the implementation PR branch**: plan.md, tasks.md, and CLAUDE.md learnings from a spec should be committed to the same branch as the implementation — not a separate tracking branch that requires cherry-picking to consolidate later.
- **GitHub suggested changes**: There is no public REST API to accept them. Extract the replacement from the `suggestion` fenced block in the comment body and apply it as a local edit.
- **Mandatory-step reference links must be imperative**: When a step delegates to an external file for mandatory continuation, write "**you must now execute [file]** — do not skip to the report" rather than "see [file]". Agents treat passive cross-references as informational and will skip them when generating the final output.
- **`gh api --paginate --jq` applies the filter per page**: `--jq '[.[] | filter] | unique'` deduplicates only within each page response. To merge all pages before deduplicating, omit the outer array wrapper in `--jq` and pipe to `| jq -s 'add | unique'` (or `| jq -s '.'` to collect a flat array). Example: `gh api .../reviews --paginate --jq '[.[] | .user.login]' | jq -s 'add | unique'`. When omitting `--jq` entirely and piping to `jq -s`, each page arrives as a separate array so the input is a stream of arrays — use `[.[] | .[] | select(...)]` (double-unwrap) to filter individual items across all pages; `[.[] | select(...)]` runs select on the page arrays themselves and silently matches nothing.
- **Guard `.login` for Team objects in GitHub reviewer lists**: Team entries in `requested_reviewers` have no `.login` field — `(.login | endswith("[bot]"))` will throw a jq error on PRs with team reviewers. Use `((.login? // "") | endswith("[bot]"))` as a safeguard whenever filtering reviewer arrays by login.
- **Closed exit condition lists need negative constraints**: When a skill defines a finite set of exit/termination conditions (e.g., loop exit, workflow abort), add an explicit statement that these are the **only** valid reasons to exit, with examples of invalid reasons the agent might rationalize (e.g., "diminishing returns", "feedback is minor"). Without this, agents will follow the positive rules but invent subjective reasons to stop early. The pattern: "**These are the ONLY valid exit conditions. Do not exit for subjective reasons** such as [concrete examples of the failure mode]."
- **Disjuncts and tie-breakers in classification rules are load-bearing**: in a rule like "include X only when it has a concrete risk **or** judgment call" or "when in doubt, flag only when...", each disjunct and tie-breaker is a distinct case — not a redundant adjective. Cutting one narrows classifier behavior even when the prose looks tighter.
- **Reviewer prompt fields must match the output format template**: if the display format expects `**[Issue title]**`, the reviewer prompt must explicitly ask for `- Title: one-line summary`. A mismatch forces the presentation step to either omit the field or invent it — both produce inconsistent output.
- **When updating a check or condition in a skill reference file, search for all parallel occurrences** in the same file before closing the task — the same logic often appears independently at multiple entry points. Use `rg -n '<key phrase>' <file>` to find all instances.
- **`rg` alternation uses unescaped `|`**: ripgrep uses Rust regex syntax — `\|` is a literal pipe character, not an alternation operator. Use `rg 'pattern1|pattern2'` for alternation (or `-e pattern1 -e pattern2`). Using `\|` instead silently searches for the literal pipe chain and will report false-clean.
- **GitHub review thread `isOutdated` is a location flag, not a resolution flag**: it means the diff hunk anchor moved (surrounding code changed), not that the concern was addressed. Do not auto-skip `isOutdated` threads — read the current file and verify whether the concern persists. If it does, classify as `fix`/`reply`/`decline` with a note that the thread location has shifted.
- **Use `jq --arg` for shell variables in filters**: Pass shell variables (timestamps, SHAs, logins) to jq using `--arg name "$var"` and reference `$name` in the filter — not shell string interpolation (`"'"$var"'"`), which can embed control characters that break jq parsing. Example: `jq -s --arg ts "$snapshot_timestamp" '[.[] | .[] | select(.submitted_at >= $ts)]'`
- **Confirmation prompts require "stop generating" instructions**: Telling an agent to "wait for user input" or "wait for the user's go-ahead" is insufficient — agents answer their own prompts and proceed. When a skill step must pause for user input, write: "Output the prompt as your final message and **stop generating**. Do not supply an answer, do not assume a default, do not continue to the next step. Resume only after the user replies." Name the next step explicitly as the boundary not to cross.
- **Mandatory output lines need "always" and "never omit" language**: An agent will skip a closing URL, summary line, or required output if the instruction reads as optional or contextual. To enforce it, write: "MANDATORY — output this on its own line as the last thing you write. Do not omit it because the user already knows the value." The word "mandatory" and an explicit "never omit" clause are what differentiate required output from suggestions.
- **Temp file cleanup in bash snippets**: When a SKILL.md step creates a temp file with `mktemp` and uses it within the same Bash tool call, document `trap 'rm -f "$FILE"' EXIT INT TERM` immediately after the `mktemp` call — not a manual `rm -f` at the end of the block, which is skipped on error or interruption. When the temp file must persist across multiple tool calls, use a named path without `trap` (see the `trap` cleanup bullet in Sandbox Workarounds in the root CLAUDE.md).
- **Sequential `trap` snippets clobber earlier traps in the same shell**: bash supports one EXIT trap per shell — a later `trap 'rm -f "$B"' EXIT INT TERM` replaces the earlier `trap 'rm -f "$A"' EXIT INT TERM` and leaks `$A`. When a SKILL.md chains snippets that may run in one shell, combine cleanup in one trap with `${VAR:-}` defaults: `trap 'rm -f "$BODY_FILE" "${PR_VIEW_STDERR:-}"' EXIT INT TERM`.
- **Capture stderr in CLI output**: Bash snippets that assign CLI output to a variable should include `2>&1` so error messages flow into the captured variable and reach fallback/error handling paths (e.g., `REVIEW_OUTPUT=$(cli ... 2>&1)`).
- **`|| true` is too broad for a specific expected error** — capture `resp=$(cmd 2>&1)` and `case`-match the tolerated status (e.g., `HTTP 422`); other errors still abort.
- **When capturing `git diff --quiet` exit codes**, use `VAR=0; git diff --quiet || VAR=$?` — not `git diff --quiet; VAR=$?`. In strict runners (`set -e`) the non-zero exit from "changes present" aborts the script before the assignment runs.
- **Reference-file delegation must name the target section and list what to skip**: When a SKILL.md step does setup work (e.g. snapshot, POST re-request) before delegating to a reference file that has its own entry/setup section covering the same actions, the delegation sentence must explicitly name the section to enter **and** say what not to re-run. E.g.: "proceed to the **Shared polling loop** — do not restart at the Step 13b entry/setup section, do not take another snapshot, and do not send another POST." Without this, agents re-enter the setup section and duplicate the snapshot/POST already done in SKILL.md.
- **Repo-specific paths need portability notes**: When a skill step references a layout-specific path (e.g., `skills/*/SKILL.md`), add `(adjust prefix to match your repo's skill directory structure)` — downstream consumers with a different layout silently miss the trigger.
- **Cite reference files by full path** (`skills/learn/references/refactoring.md`, not `refactoring.md`) — bare names are ambiguous outside the home skill.
- **For verbatim user-facing strings in a skill, use fenced ` ```text ` blocks plus an explicit "fences are markdown only" instruction** — markdown blockquotes wrapping inline backticks (`` > `@<bot>` ... ``) get emitted literally with the backticks.
- **Move conditional skill logic into `references/` when content is load-bearing on only one branch and exceeds ~15-20 lines** — replace the inline block with a `**MANDATORY: read [...] in full**` link so other branches don't pay the context cost. Examples: `skills/learn/references/assistant-configs.md` (no-configs branch), `skills/learn/references/refactoring.md` (refactoring branch), `skills/learn/references/multiconfig-routing.md` (multi-config branch).
