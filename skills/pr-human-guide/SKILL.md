---
name: pr-human-guide
description: >-
  Analyzes a PR diff and appends a categorized review guide to the PR
  description, highlighting where human judgment is needed: security,
  config/infrastructure, new dependencies, data model changes, novel
  patterns, and concurrency/state. Use this whenever a user wants to prepare
  a PR for human review or flag areas for reviewer attention — including
  casual phrasing like "prep this for review", "what should reviewers look
  at?", "add a review guide", or "flag this for human review".
license: MIT
compatibility: Requires git, gh, jq; sha256sum (Linux) or shasum (macOS)
metadata:
  author: Gregory Murray
  repository: github.com/whatifwedigdeeper/agent-skills
  version: "0.5"
---

# PR Human Guide

Analyzes a pull request and appends a categorized guide to the PR description
identifying areas that specifically need human judgment — security implications,
config changes, new dependencies, data model changes, novel patterns, and
concurrency/state changes.

This skill does **not** perform a code review. It identifies *where* a human
reviewer's attention is most needed, not *what* is right or wrong.

## Arguments

The text following the skill invocation is available as `$ARGUMENTS`
(e.g. in Claude Code: `/pr-human-guide 42`).

- **PR number** (optional) — if omitted, auto-detects from the current branch
- `--help` / `-h` / `help` / `?` — show this documentation and stop

## Process

### 1. Parse arguments and identify the PR

If `$ARGUMENTS`, after trimming whitespace and lowercasing, exactly matches
`help`, `--help`, `-h`, or `?`, output this skill's documentation and stop.

If a PR number is provided, use it. Otherwise detect from the current branch:

```bash
gh pr view --json number,url,title,baseRefName,headRefName,body \
  --jq '{number: .number, url: .url, title: .title, base_branch: .baseRefName, head_branch: .headRefName, body: .body}'
```

If no PR is found, stop with: `No open PR found for the current branch. Pass a PR number explicitly.`

Capture: `pr_number`, `pr_url`, `pr_title`, `base_branch`, `head_branch`, `pr_body`.

Also capture repo owner/name:

```bash
if ! REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>&1); then
  echo "Failed to determine repo owner/name with 'gh repo view': ${REPO}" >&2
  exit 1
fi
OWNER="${REPO%%/*}"
REPO_NAME="${REPO##*/}"
```

### 2. Gather the diff and changed file list

```bash
gh pr diff {pr_number} --name-only
gh pr diff {pr_number}
```

Store the full diff for analysis. Store the file list separately.

### 3. Analyze changes by category

Read `[references/categories.md](references/categories.md)` — it defines the
six review categories, their detection signals, and examples of what qualifies.

For each changed file, classify the changes against the six categories. For the
**Novel Patterns** category, read 2-3 sibling files or related modules to
understand existing conventions before judging whether the change introduces
something new. If the changed file is in a new directory with no sibling files,
treat the pattern as novel by default and note the absence of established
conventions to compare against.

Build an internal analysis table:

| File | Lines | Category | Reason |
|------|-------|----------|--------|

Rules:
- A file may appear in multiple categories if it has distinct concerns
- Multiple flagged regions in the same file/category → merge into one entry
  with a combined line range (or omit the range if changes are scattered)
- If a file is large and changes are spread throughout, note the file without
  a line range rather than listing every hunk
- Use a single threshold policy: flag an area only when human judgment is
  likely to materially affect review, risk assessment, or rollout decisions.
  Routine business logic, test updates, and documentation changes normally do
  not qualify; if a borderline change still has a concrete reviewer-relevant
  risk or judgment call, include it, otherwise leave it out.

### 4. Generate the review guide

If any items were flagged, format them into a categorized markdown section.

Generate a GitHub diff anchor for each file:

```bash
# SHA-256 of the file path (cross-platform: sha256sum on Linux, shasum on macOS)
ANCHOR=$(printf '%s' "path/to/file" | if command -v sha256sum >/dev/null 2>&1; then sha256sum; else shasum -a 256; fi | cut -d' ' -f1)
# Full link
LINK="https://github.com/${OWNER}/${REPO_NAME}/pull/${pr_number}/files#diff-${ANCHOR}"
# Line-level anchor (right side): append R{line} to the link
```

Format each entry as:
```
- [ ] [`path/to/file` (L{start}-{end})](link) — one-line reason
```

Omit the line range if changes are spread across the whole file.

Wrap the section in HTML comment markers for idempotent re-runs.

**Important**: The opening marker `<!--` contains `!`, which zsh history expansion
can corrupt to `<\!--` when the guide body is built or passed inline through
double-quoted shell strings. Construct the guide body using single-quoted strings,
`$'...'` ANSI quoting, or Python. If using an inline `<<'PYEOF'` heredoc, avoid
literal `!` in the script body — use `chr(33)` instead:
```python
OPEN  = "<" + chr(33) + "-- pr-human-guide -->"
CLOSE = "<" + chr(33) + "-- /pr-human-guide -->"
```
This lets the script run via `python3 - <<'PYEOF'` without triggering Write-tool
approval for a temp file. Alternatively, write the script to disk and execute it
directly. Then pass the result to GitHub with `gh pr edit --body-file` so the
markers reach GitHub unescaped.

```markdown
<!-- pr-human-guide -->
## Review Guide

> Areas identified by automated analysis as needing human judgment.
> This is not a complete review checklist — it highlights where your attention matters most.

### Security
- [ ] [`src/auth/middleware.ts` (L42-67)](link) — New token validation logic

### Config / Infrastructure
- [ ] [`deploy/terraform/iam.tf` (L12-18)](link) — IAM role permissions widened

### Novel Patterns
- [ ] [`src/cache/redis.ts`](link) — First use of Redis in this codebase; no existing caching pattern to reference

<!-- /pr-human-guide -->
```

Omit any category section that has no flagged items.

If **no items** were flagged in any category, the section body is:

```markdown
<!-- pr-human-guide -->
## Review Guide

No areas requiring special human review attention were identified.

<!-- /pr-human-guide -->
```

### 5. Append or replace the review guide in the PR description

Check whether `<!-- pr-human-guide -->` already exists in `pr_body`.

**If it exists** — replace the content between the markers with the new guide
(idempotent re-run). Use a script that extracts everything before the opening
marker and everything after the closing marker, then sandwiches the new guide
between them. If the closing marker is missing (e.g., manual edits corrupted
the block), replace from the opening marker to the end of the body.

**If it does not exist** — append the guide to the end of the existing body,
with a blank line separator.

Update the PR description by writing the body to a temp file and using
`--body-file` (never `--body "$VAR"` — zsh corrupts the `<!--` marker):

```bash
TMPFILE=$(mktemp "${TMPDIR:-/private/tmp}/pr-human-guide-XXXXXX")
trap 'rm -f "$TMPFILE"' EXIT INT TERM
printf '%s' "$UPDATED_BODY" > "$TMPFILE"
gh pr edit {pr_number} --body-file "$TMPFILE"
rm -f "$TMPFILE"
trap - EXIT INT TERM
```

### 6. Report

Output a summary:

```
Review guide added to PR #{number}: {title}
{N} item(s) across {M} category/categories.
{pr_url}
```

If this is a re-run that replaced an existing guide, use:
```
Review guide updated on PR #{number}: {title}
{N} item(s) across {M} category/categories.
{pr_url}
```

When N=0 (no items flagged), omit the item count line from both formats — the
guide body already contains the "no areas" message.

MANDATORY — output the PR URL as the last line. Never omit it, even if the URL is visible elsewhere in the output.

## Notes

- **Scope**: This skill identifies areas for human attention, not code defects.
  It is complementary to peer-review (automated code review) and pr-comments
  (addressing reviewer feedback).
- **Novel pattern detection**: Requires reading sibling files — the quality of
  the "novel patterns" category depends on how representative the sampled files
  are. For large codebases, sample the most closely related modules.
- **Idempotency**: The HTML comment markers make re-runs safe. Running the
  skill again after new commits replaces the previous guide rather than
  appending a second one. Note: any `- [x]` items checked by reviewers are
  reset to `- [ ]` on re-run — checked state is not preserved.
- **False negatives vs. false positives**: Apply the same threshold as Step 3 — flag when human judgment is likely to materially affect review, risk, or rollout. The guide is framed as "where to focus" not "the only things to check," so under-flagging routine changes is correct behavior, not a gap.
- **No blocking**: This skill does not enforce review requirements or block
  merging. It is purely informational.
