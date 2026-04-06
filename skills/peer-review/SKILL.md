---
name: peer-review
description: >-
  Get a fresh-context review of staged changes, branches, PRs, or file sets.
  Delegates to a fresh-context reviewer by default; routes to external LLM CLIs
  (Copilot, Codex, Gemini) when --model specifies one.
  Use when: user says "review my changes", "peer review", "check for consistency",
  "review staged", "review PR N", "check this for issues",
  "fresh review", "another set of eyes", "sanity check", "quick review before I push",
  "look this over", "anything wrong with this", or wants a lightweight review before
  opening a PR. Also use for "review these files", "check this diff", or when the user
  pastes a diff or spec and asks if anything looks off.
license: MIT
compatibility: Requires git; requires GitHub CLI (gh) for PR targets
metadata:
  author: Gregory Murray
  repository: github.com/whatifwedigdeeper/agent-skills
  version: "1.4"
---

# Peer Review

Get a fresh-context review of in-progress work — staged changes, a branch diff, a PR, or a set of files — without accumulated session assumptions. Returns severity-grouped findings the author can apply or skip.

## Arguments

The text following the skill invocation is available as `$ARGUMENTS` (in Claude Code: `/peer-review [target] [options]`).

If `$ARGUMENTS` is `help`, `--help`, `-h`, or `?`, print usage and exit:

```
Usage: /peer-review [target] [--model MODEL] [--focus TOPIC]

Targets (pick one):
  (none)            Auto-detect: staged, unstaged, or prompt if both exist
  --staged          Staged changes only — skip auto-detection (git diff --staged)
  --pr N            PR #N diff + description
  --branch NAME     Branch diff vs default branch
  path/to/file-or-dir  Specific files or directory

Options:
  --model MODEL     Reviewer model (default: claude-opus-4-6)
                    Claude models: any claude-* value uses the internal Claude reviewer
                    External CLIs: copilot[:submodel], codex[:submodel], gemini[:submodel]
                      copilot — npm install -g @github/copilot-cli (or VS Code extension)
                      codex   — npm install -g @openai/codex
                      gemini  — npm install -g @google/gemini-cli
  --focus TOPIC     Narrow emphasis (e.g. security, consistency, evals)
                    Does NOT suppress critical findings outside the focus area
```

Parse `$ARGUMENTS` left-to-right:
- Strip `--staged` → set target type to staged (explicit-staged flag = true; staged-only, no auto-detection)
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
| **Consistency** | Any file/dir path | Drift between related files — stale step references, mismatched terminology, missing parallel updates, underspecified items, shell command errors, internal math/count errors |

## Process

### 1. Parse Arguments

Parse `$ARGUMENTS` per the Arguments section above. Set `model` to `claude-opus-4-6` if not overridden.

### 2. Collect Content

Execute the appropriate collection command:

**Staged** (explicit `--staged`):
```bash
git diff --staged
```
If output is empty, warn: "No staged changes found. Stage files with `git add` first." and exit.

**Default** (no target — auto-detect):

Check for presence first (fast, no content captured):
```bash
git diff --staged --quiet; STAGED_PRESENT=$?
git diff --quiet; UNSTAGED_PRESENT=$?
```
(`0` = nothing present, `1` = changes present)

- **Neither present** → warn: "No staged or unstaged changes found. Working tree is clean." and exit.
- **Staged only** → collect staged content and proceed: `git diff --staged`
- **Unstaged only** → collect unstaged content and proceed: `git diff` — note in the output header: "No staged changes — reviewing unstaged changes."
- **Both present** → output: "You have both staged and unstaged changes. Review which? [staged/unstaged/all]" as your **final message and stop generating**. On reply, collect:
  - `staged` → `git diff --staged`
  - `unstaged` → `git diff`
  - `all` → `git diff HEAD`

**Branch** (`--branch NAME`):

Detect the default branch first (do not assume `main`):
```bash
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
if [ -z "$DEFAULT_BRANCH" ]; then
  DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | grep 'HEAD branch' | sed 's/.*: //')
fi
git diff ${DEFAULT_BRANCH}...NAME
```
If the branch is not found, error with: "Branch NAME not found. Available branches:" followed by `git branch -a`.

**PR** (`--pr N`):
```bash
gh pr view N --json number,title,body,baseRefName,headRefName,url
gh pr diff N
```
If the PR is not found, error and exit. Prepend the PR title and body as context to the diff before passing to the reviewer prompt — the title and body give the reviewer intent and scope that isn't visible in the diff alone.

**Path** (file or directory):

Read all files at the path (in Claude Code: use the `Read` tool). Set mode to **consistency**.

### 3. Select Prompt Template

Choose the template for the detected mode and apply the `--focus` filter if provided.

**Diff mode prompt:**
```
You are doing a diff review. Your job is to find real problems — bugs, security issues,
missing tests, style violations, unintended behavioral changes.

Severity guide:
- critical: would cause incorrect behavior, data loss, or a security vulnerability in production
- major: likely to confuse users, break edge cases, or make future changes harder without being immediately fatal
- minor: style, naming, or polish issues that don't affect correctness

Do NOT report:
- Import ordering or grouping preferences
- Whitespace-only issues or formatting style (unless it changes behavior, e.g. Python indentation)
- Missing comments on self-explanatory code
- Suggestions to add type annotations when the file doesn't already use them
- Renaming suggestions based on personal preference when the current name is clear

Flag missing test coverage only for non-trivial behavioral changes — not for one-line renames, comment edits, or config tweaks.

[DIFF CONTENT]

Return a structured list of findings grouped by severity (critical/major/minor).
For each finding include:
- Title: one-line summary of the issue
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
Look for:
- Stale step references, mismatched terminology, missing parallel updates
- Descriptions that contradict each other
- Underspecified items — too vague to implement unambiguously
- Incorrect or incomplete shell commands
- Internal math or count errors (e.g. "10 items" when only 8 are listed)
- Items implied by one file but missing from another

Severity guide:
- critical: contradiction that would cause the reader to implement the wrong behavior
- major: stale reference, shell error, or missing item that would confuse a reader or require rework
- minor: wording ambiguity, count discrepancy, or cosmetic inconsistency that doesn't block implementation

Do NOT report:
- Minor wording preferences that don't change meaning
- Formatting differences between files (indentation, bullet style) unless they signal a copy-paste error
- Issues with content outside the provided files

[FILE CONTENTS]

Return a structured list of findings grouped by severity (critical/major/minor).
For each finding include:
- Title: one-line summary of the issue
- Severity: critical | major | minor
- File: relative path of the file with the issue
- Location: phrase anchor — quote a short phrase near the issue (do not use line numbers)
- Problem: what is inconsistent or missing
- Fix: what the change should be

If there are no findings, return exactly: NO FINDINGS

Do NOT implement any changes. Return findings only.
[FOCUS_LINE]
```

**Focus line** (append when `--focus` is provided):
```
Focus especially on [TOPIC]. Still report any critical findings outside this focus area.
```

### 4. Spawn Reviewer

**If `model` starts with `claude-` (including the default `claude-opus-4-6`):**

Delegate to a fresh-context Claude reviewer — pass the completed prompt (template + collected content). The reviewer has no prior session context — this is intentional. In Claude Code, spawn a subagent with `mode: "auto"` to suppress approval prompts.

The reviewer's only job is to return findings. It must not modify any files.

**Otherwise (external CLI path — copilot, codex, gemini):**

Determine the CLI binary and optional sub-model from the `--model` value. If `--model` contains `:` (e.g. `copilot:gpt-4o-mini`), split on `:` — the left part is the binary name, the right part is the sub-model.

| `--model` prefix | Binary | Sub-model flag |
|-----------------|--------|---------------|
| `copilot` | `copilot` | `--model SUBMODEL` |
| `codex` | `codex` | `--model SUBMODEL` |
| `gemini` | `gemini` | `-m SUBMODEL` |

If the prefix does not match `copilot`, `codex`, or `gemini`, error and stop: "Unsupported --model value: [value]. Supported external CLIs: copilot, codex, gemini. For Claude models, use a `claude-*` prefix (e.g. `--model claude-opus-4-6`)."

**4a. Check binary availability:**

```bash
command -v <binary> >/dev/null 2>&1 || { echo "<binary> CLI not found. Install with: <install hint>"; exit 1; }
```

Install hints:
- `copilot`: `npm install -g @github/copilot-cli` or via the GitHub Copilot VS Code extension
- `codex`: `npm install -g @openai/codex`
- `gemini`: `npm install -g @google/gemini-cli`

If the binary is not found, output the error message and stop. Do not proceed to Step 5.

**4b. Write prompt to temp file:**

```bash
PROMPT_FILE=$(mktemp "${TMPDIR:-/private/tmp}/peer-review-prompt.XXXXXX")
trap 'rm -f "$PROMPT_FILE"' EXIT INT TERM
printf '%s' "$PROMPT" > "$PROMPT_FILE"
```

Writing to a temp file preserves the exact multi-line prompt content and keeps prompt construction separate from the CLI invocation. In the commands below, correct quoting of `"$(cat "$PROMPT_FILE")"` is what prevents shell metacharacters in diff/PR content from being interpreted by the shell. The `trap` ensures the temp file is removed even if the CLI command fails or the process is interrupted.

**4c. Execute and capture output:**

For copilot:
```bash
if [ -n "$SUBMODEL" ]; then
  REVIEW_OUTPUT=$(copilot --allow-all-tools --deny-tool='write' -p "$(cat "$PROMPT_FILE")" --model "$SUBMODEL" 2>&1)
else
  REVIEW_OUTPUT=$(copilot --allow-all-tools --deny-tool='write' -p "$(cat "$PROMPT_FILE")" 2>&1)
fi
```

For codex (`--no-auto-edit` suppresses file writes; unverified — adjust if your version uses a different flag):
```bash
if [ -n "$SUBMODEL" ]; then
  REVIEW_OUTPUT=$(cat "$PROMPT_FILE" | codex --no-auto-edit --model "$SUBMODEL" 2>&1)
else
  REVIEW_OUTPUT=$(cat "$PROMPT_FILE" | codex --no-auto-edit 2>&1)
fi
```

For gemini (`--approval-mode plan` enables read-only mode):
```bash
if [ -n "$SUBMODEL" ]; then
  REVIEW_OUTPUT=$(gemini --approval-mode plan -m "$SUBMODEL" -p "$(cat "$PROMPT_FILE")" 2>&1)
else
  REVIEW_OUTPUT=$(gemini --approval-mode plan -p "$(cat "$PROMPT_FILE")" 2>&1)
fi
```

The `trap` set in Step 4b will remove `$PROMPT_FILE` on completion or interruption.

**4d. Parse output → normalized findings:**

For copilot: output is JSON with schema `{ summary, overall_risk, findings: [{ severity, file, title, details, suggested_fix }] }`. Extract `findings[]`; map `details` → problem, `suggested_fix` → fix. Apply severity normalization below. If `findings` is empty, treat as `NO FINDINGS`. If JSON is malformed, fall through to raw-output fallback.

For codex and gemini: output is markdown or plain text. First check if output is exactly `NO FINDINGS` — if so, treat as no issues. Otherwise parse severity from lines matching patterns like `[HIGH]`, `**Critical**`, `severity: high` (case-insensitive). Extract title, file, problem, and fix from surrounding lines. If no structured severity pattern is found, present the full output as a single `major` finding.

If parsing fails for any CLI: output raw text with the prefix "Could not parse structured findings; showing raw output."

**Severity normalization** (apply case-insensitively for all CLIs):

| Input severity | Normalized |
|---------------|-----------|
| `high` / `error` / `critical` | `critical` |
| `medium` / `warning` / `major` | `major` |
| `low` / `info` / `note` / `minor` | `minor` |

**4e. Triage findings (external CLI path only):**

Spawn a fresh Claude subagent (with `mode: "auto"` in Claude Code) with the following triage prompt:

```
You are reviewing a list of findings produced by an external code reviewer.
Your job is to classify each finding as recommend or skip.

Review mode: [consistency / diff]
Content type: [file contents for consistency mode / diff text for diff mode]

Recommend a finding if:
- The issue is real and not already addressed in the reviewed content
- The finding adds information the author doesn't already have
- The fix is actionable

Skip a finding if:
- The issue is already documented or handled in the reviewed content
- The finding contradicts verified facts in the content
- The finding is speculative or opinion without clear evidence
- The fix is already present

For each finding, output exactly one line:
FINDING N: recommend
or
FINDING N: skip — [one-line reason]

[NORMALIZED FINDINGS — title, severity, file, location, problem, fix for each]

[COLLECTED CONTENT — file contents for consistency mode / diff text for diff mode]
```

Parse the triage subagent's response. For each `FINDING N:` line, assign the finding to `recommended` or `skipped`. If the triage output cannot be parsed or is otherwise invalid (including missing `FINDING N:` lines, wrong format, empty response, duplicate `FINDING N:` lines, conflicting `recommend` and `skip` decisions for the same `N`, IDs outside the valid `1..N` finding range, or any other violation of the "exactly one line per finding" rule), treat all findings as `recommended` and note "Triage unavailable — showing all findings." at the start of the Step 5 output.

**4f.** Continue to Step 5 with the classified findings (`recommended` and `skipped` buckets). When coming from the Claude path (Step 4 first branch), there is no triage — pass all findings directly to Step 5 as `recommended`.

### 5. Present Findings

If there are no findings (reviewer returned `NO FINDINGS` on the Claude path, or the external CLI returned nothing before triage), output:

```
## Peer Review — [target] ([model])

No issues found.
```

Then stop. Do not show an apply prompt.

**External CLI path only — if triage skipped all findings**, output:

```
## Peer Review — [target] ([model])

No issues recommended.

Triage filtered all [N] findings:
- [title] — [reason]
```

Then stop. Do not show an apply prompt.

**Otherwise**, display the recommended findings numbered sequentially (`1, 2, 3...`) grouped by severity. If there are triage-skipped findings, list them below the separator with `S`-prefix numbering (`S1, S2...`):

```
## Peer Review — [target] ([model])

### Critical
1. **[Issue title]** — `[file]`
   [Problem description]
   Fix: [specific change]

### Major
2. ...

### Minor
3. ...

---
Triage filtered [M] of [N] findings:
S1. **[Skipped title]** — [reason]
S2. **[Skipped title]** — [reason]

Apply all recommended, include skipped by S-number, or skip? [all/1,2/1,S1/skip]
```

On the Claude path (no triage), there is no "Triage filtered" section and the apply prompt is the standard form: `Apply all, select by number, or skip? [all/1,3,5/skip]`

Output this as your **final message and stop generating**. Do not supply an answer, do not assume a default, do not proceed to the next step. Resume only after the user replies.

### 6. Apply

On user reply:

- `all` — apply every **recommended** finding by editing the files directly (in Claude Code: use the `Edit` tool); report each change as you make it. On the Claude path (no triage), `all` applies every finding.
- `1,3,5` (comma-separated numbers) — apply only the listed findings. Numbers refer to the sequential display positions of recommended findings as numbered in Step 5 (not original finding IDs — when triage skips some findings, the remaining recommended findings are renumbered `1, 2, 3...`); `S`-prefixed numbers (e.g. `S1`, `S2`) refer to skipped findings by their triage order. Both can be mixed (e.g. `1,S1`).
- `skip` — output "Skipped N findings. No changes made." and stop. No re-scan is offered.

When applying a finding, use the phrase anchor from the finding's Location field to locate the text in the file — do not use line numbers. If the phrase anchor cannot be found in the file, skip that finding and note it: "Skipped finding N — location anchor not found in [file]."

**PR target**: applying findings edits local files only. Do not stage, commit, or push. After applying, the changes are uncommitted local edits the author can review before deciding to push. Before applying, check that the current branch matches the PR's `headRefName` — if not, warn: "You are on branch X, not the PR branch Y — applying will edit files on X."

**Diff mode**: after applying all findings, suggest running tests or linting if the changes touched code: "Consider running tests to verify the applied changes."

After all edits are complete, output: "Applied N finding(s)." on its own line.

**Post-apply re-scan** (offered only when at least one file was actually modified, and only once — not during a re-scan cycle):

```
Applied N finding(s).

Re-scan modified files for new issues? [y/n]
```

Output this as your **final message and stop generating**. Do not supply an answer, do not assume a default, do not continue to the next step. Resume only after the user replies.

On `y`: collect the modified files' current content, build the **consistency mode** prompt (always consistency, regardless of the original review mode), and spawn a fresh Claude subagent (always Claude regardless of the original `--model`). Feed findings into Step 5 using the Claude path (no triage section, standard apply prompt `[all/1,3,5/skip]`). If no new issues are found, output "No new issues found in re-scan." and stop. **Do not offer another re-scan** — after applying during a re-scan cycle, output "Applied N finding(s)." and stop. If the target was `--pr N`, output the PR URL as the final line in all cases (after re-scan completes, after "No new issues found", or after "Applied N finding(s)" in a re-scan cycle).

On `n`: if the target was `--pr N`, output the PR URL as the final line. Then stop.

If no re-scan is offered (no files were modified, or this is a re-scan cycle), output the PR URL as the final line when the target was `--pr N`.

## Notes

- **Fresh-context guarantee**: the reviewer has no history from the current session. It sees only the content you pass it. This is the primary value of the skill — the reviewer cannot rationalize away issues the author has normalized.
- **`--focus` does not suppress critical findings**: narrowing focus changes emphasis, not the severity threshold. A `critical` finding outside the focus topic will still be reported.
- **Multi-LLM routing**: `--model copilot[:submodel]`, `--model codex`, and `--model gemini` route the review prompt to the respective external CLI rather than spawning a Claude subagent. This allows getting a non-Claude perspective (e.g. `--model copilot:gpt-4o-mini`). The binary must be installed and on `PATH`; if absent the skill errors with an install hint. Each CLI's output is normalized to the same severity-grouped findings format before Step 5.
- **Triage layer** (external CLI path only): after normalizing findings from an external CLI, a fresh Claude subagent classifies each finding as `recommend` or `skip`. Recommended findings are numbered `1, 2, 3...` in the apply prompt; skipped findings are listed below the separator with `S`-prefix numbering. Users can include a skipped finding by referencing its S-number (e.g. `1,S1`). If triage output cannot be parsed, all findings are treated as recommended. The triage layer does not activate on the Claude path.
- **Post-apply re-scan**: after applying at least one finding, the skill offers to re-scan the modified files for new issues. The re-scan always uses consistency mode and always spawns a Claude subagent (regardless of the original `--model`). The re-scan is offered at most once — a second apply during a re-scan cycle does not trigger another offer.
