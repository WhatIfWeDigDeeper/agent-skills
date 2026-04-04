---
name: peer-review
description: >-
  Get a fresh-context review of specs, staged changes, branches, PRs, or file sets.
  Delegates to a fresh-context reviewer by default (Phase II: routes to external LLM CLIs — Copilot, Codex, Gemini).
  Use when: user says "review my changes", "peer review", "check for consistency",
  "review this spec", "review staged", "review PR N", "check this for issues",
  "fresh review", or wants a lightweight review before opening a PR.
license: MIT
compatibility: Requires git; requires GitHub CLI (gh) for PR targets
metadata:
  author: Gregory Murray
  repository: github.com/whatifwedigdeeper/agent-skills
  version: "1.0"
---

# Peer Review

Get a fresh-context review of in-progress work — specs, staged changes, a branch diff, a PR, or a set of files — without accumulated session assumptions. Returns severity-grouped findings the author can apply or skip.

## Arguments

The text following the skill invocation is available as `$ARGUMENTS` (in Claude Code: `/peer-review [target] [options]`).

If `$ARGUMENTS` is `help`, `--help`, `-h`, or `?`, print usage and exit:

```
Usage: /peer-review [target] [--model MODEL] [--focus TOPIC]

Targets (pick one):
  (none)            Staged changes (git diff --staged)
  --staged          Same as no target — explicit form
  --pr N            PR #N diff + description
  --branch NAME     Branch diff vs main
  path/to/file-or-dir  Specific files or directory

Options:
  --model MODEL     Reviewer model (default: claude-opus-4-6)
                    Phase II: --model copilot[:submodel], --model codex, --model gemini
  --focus TOPIC     Narrow emphasis (e.g. security, consistency, evals)
                    Does NOT suppress critical findings outside the focus area
```

Parse `$ARGUMENTS` left-to-right:
- Strip `--staged` → set target type to staged
- Strip `--pr N` → set target type to PR, store N
- Strip `--branch NAME` → set target type to branch, store NAME
- Strip `--model MODEL` → store model override
- Strip `--focus TOPIC` → store focus topic
- Remaining token (if any) → treat as a file/dir path target

**Conflict**: if more than one target selector is present after parsing (e.g. both `--pr N` and `--branch NAME`, or `--pr N` and a path, or `--staged` and a path, or two leftover path tokens), error: "specify one target at a time — targets are mutually exclusive."

## Review Modes

The skill auto-detects the review mode from the target:

| Mode | Trigger | Focus |
|------|---------|-------|
| **Diff** | `--staged`, `--branch`, `--pr`, no target | Bugs, security issues, missing tests, style violations, unintended behavioral changes |
| **Spec** | Path resolves to a directory containing both `plan.md` and `tasks.md` | All consistency checks + gaps between plan/tasks, underspecified items, incorrect shell commands, internal math errors, implied-but-missing tasks |
| **Consistency** | Any other file/dir path | Drift between related files — stale step references, mismatched terminology, missing parallel updates |

## Process

### 1. Parse Arguments

Parse `$ARGUMENTS` per the Arguments section above. Set `model` to `claude-opus-4-6` if not overridden.

### 2. Collect Content

Execute the appropriate collection command:

**Staged** (`--staged` or no target):
```bash
git diff --staged
```
If output is empty, warn: "No staged changes found. Stage files with `git add` first." and exit.

**Branch** (`--branch NAME`):
```bash
git diff main...NAME
```
If the branch is not found, error with: "Branch NAME not found. Available branches:" followed by `git branch -a`.

**PR** (`--pr N`):
```bash
gh pr view N --json number,title,body,baseRefName,headRefName
gh pr diff N
```
If the PR is not found, error and exit. Prepend the PR title and body as context to the diff before passing to the reviewer prompt — the title and body give the reviewer intent and scope that isn't visible in the diff alone.

**Path** (file or directory):

Read all files at the path (in Claude Code: use the `Read` tool). If the resolved path is a directory containing both `plan.md` and `tasks.md`, set mode to **spec**. Otherwise set mode to **consistency**.

### 3. Select Prompt Template

Choose the template for the detected mode and apply the `--focus` filter if provided.

**Diff mode prompt:**
```
You are doing a diff review. Your job is to find real problems — bugs, security issues,
missing tests, style violations, unintended behavioral changes.

[DIFF CONTENT]

Return a structured list of findings grouped by severity (critical/major/minor).
For each finding include:
- Severity: critical | major | minor
- File: relative path (use "diff" if not file-specific)
- Location: phrase anchor — quote a short phrase near the issue (do not use line numbers)
- Problem: what is wrong (be specific)
- Fix: what the change should be

If there are no findings, return exactly: NO FINDINGS

Do NOT implement any changes. Return findings only.
[FOCUS_LINE]
```

**Consistency mode prompt:**
```
You are doing a consistency review across a set of related files.
Look for: stale step references, mismatched terminology, missing parallel updates,
descriptions that contradict each other, and underspecified items.

[FILE CONTENTS]

Return a structured list of findings grouped by severity (critical/major/minor).
For each finding include:
- Severity: critical | major | minor
- File: relative path of the file with the issue
- Location: phrase anchor — quote a short phrase near the issue (do not use line numbers)
- Problem: what is inconsistent or missing
- Fix: what the change should be

If there are no findings, return exactly: NO FINDINGS

Do NOT implement any changes. Return findings only.
[FOCUS_LINE]
```

**Spec mode prompt:**
```
You are doing a spec review. The input is a plan.md + tasks.md pair.

Check for:
1. Consistency between plan.md and tasks.md — every behavior in the plan should have a task; every task should trace to the plan
2. Underspecified task items — tasks that are too vague to implement unambiguously
3. Incorrect or incomplete shell commands
4. Internal math or count errors
5. Tasks implied by the plan but missing from tasks.md
6. Contradictions within or between the two files

[FILE CONTENTS]

Return a structured list of findings grouped by severity (critical/major/minor).
For each finding include:
- Severity: critical | major | minor
- File: plan.md or tasks.md
- Location: phrase anchor — quote a short phrase near the issue (do not use line numbers)
- Problem: what is wrong or missing
- Fix: what the change should be

If there are no findings, return exactly: NO FINDINGS

Do NOT implement any changes. Return findings only.
[FOCUS_LINE]
```

**Focus line** (append when `--focus` is provided):
```
Focus especially on [TOPIC]. Still report any critical findings outside this focus area.
```

### 4. Spawn Reviewer Subagent

Delegate to a fresh-context reviewer — pass the completed prompt (template + collected content). The reviewer has no prior session context — this is intentional. In Claude Code, spawn a subagent with `mode: "auto"` to suppress approval prompts.

The reviewer's only job is to return findings. It must not modify any files.

### 5. Present Findings

If the reviewer returns `NO FINDINGS`, output:

```
## Peer Review — [target] ([model])

No issues found.
```

Then stop. Do not show an apply prompt.

Otherwise, parse the findings into severity buckets and display:

```
## Peer Review — [target] ([model])

### Critical
1. **[Issue title]** — `[file]`
   [Problem description]
   Fix: [specific change]

### Major
...

### Minor
...

---
Apply all, select by number, or skip? [all/1,3,5/skip]
```

Output this as your **final message and stop generating**. Do not supply an answer, do not assume a default, do not proceed to the next step. Resume only after the user replies.

### 6. Apply

On user reply:

- `all` — apply every finding by editing the files directly (in Claude Code: use the `Edit` tool); report each change as you make it
- `1,3,5` (comma-separated numbers) — apply only the listed findings
- `skip` — output "Skipped N findings. No changes made." and stop

When applying a finding, use the phrase anchor from the finding's Location field to locate the text in the file — do not use line numbers.

## Notes

- **Fresh-context guarantee**: the reviewer has no history from the current session. It sees only the content you pass it. This is the primary value of the skill — the reviewer cannot rationalize away issues the author has normalized.
- **`--focus` does not suppress critical findings**: narrowing focus changes emphasis, not the severity threshold. A `critical` finding outside the focus topic will still be reported.
- **vs `code-review`**: the built-in `code-review` skill spawns multiple subagents with distinct reviewer personas (security, correctness, style, etc.) — thorough but relatively expensive, best for full PR reviews before merge. `peer-review` uses a single reviewer and is optimized for lighter checks: mid-draft spec validation, quick consistency sweeps, and staged-change review before opening a PR.
- **Phase II — multi-LLM routing**: `--model copilot[:submodel]`, `--model codex`, and `--model gemini` will route the review prompt to the respective CLI tool rather than the default internal reviewer. This allows using a non-Claude model as the reviewer (e.g. `--model copilot:gpt-4o-mini`). `specs/16-peer-review/copilot-staged-review.sh` is a prototype for the Copilot path (staged-only; deferred to Phase II).
