# Spec 22: pr-human-guide — PR Review Guide for Human Reviewers

## Problem

When an AI assistant creates or modifies a PR, human reviewers face a wall of diffs with no guidance on where their attention matters most. Automated reviews (claude[bot], pr-comments) catch mechanical issues, but humans are needed for judgment calls: security implications, config changes with blast radius, and novel patterns that don't match existing codebase conventions. Currently there's no structured way to surface these areas — reviewers either scan everything equally or rely on intuition about which files matter.

## Design

### Core Concept

A standalone skill that analyzes the full PR diff against the existing codebase and produces a categorized review guide — appended to the PR description — highlighting areas that specifically need human judgment. The guide is based on the *nature of the changes*, not on where bot comments landed.

### Review Categories

The skill analyzes the diff and flags areas in these categories (ordered by priority):

| Category | Signal | Why a human is needed |
|----------|--------|-----------------------|
| **Security** | Auth logic, crypto, token handling, permissions, input validation, query construction, CORS/CSP, secrets management | Security review requires threat modeling, not just pattern matching |
| **Config / Infrastructure** | CI/CD pipelines, Dockerfiles, deploy configs, env vars, IAM/permissions, package.json scripts | Blast radius assessment — config changes can affect all environments |
| **New Dependencies** | Added packages in lockfiles/manifests, especially those with network/fs/native access | Supply chain risk evaluation, license compatibility |
| **Data Model Changes** | Migrations, schema changes, API contract changes, protobuf/GraphQL schema edits | Backwards compatibility, rollback safety, client impact |
| **Novel Patterns** | Code that doesn't match existing patterns in the codebase — new frameworks, unfamiliar abstractions, first use of a library, different error handling strategy | Architectural consistency, maintainability judgment |
| **Concurrency / State** | New locks, caches, shared mutable state, async patterns not used elsewhere | Race condition risk, deadlock potential |

Categories with no flagged items are omitted from the output.

### Novel Pattern Detection

This is where the skill adds value beyond a linter. The agent:

1. Reads the full PR diff
2. For each changed file, samples the surrounding codebase (sibling files, imports, similar modules) to understand existing patterns
3. Flags code that introduces something the codebase hasn't seen before

Examples: first use of a caching layer, a different ORM query pattern than the rest of the repo, introducing a new error handling convention, a file structure that breaks the existing directory conventions.

### Workflow

#### Step 1 — Identify the PR

Parse `$ARGUMENTS` for a PR number. If none provided, detect from the current branch via `gh pr view`.

```bash
gh pr view --json number,url,title,baseRefName,headRefName,body \
  --jq '{number, url, title, baseRefName, headRefName, body}'
```

#### Step 2 — Gather the diff and file list

```bash
gh pr diff {pr_number}
gh pr diff {pr_number} --name-only
```

#### Step 3 — Analyze changes by category

For each changed file, classify the changes against the review categories. For the **Novel Patterns** category, read sibling files and imports to compare against existing conventions.

Build an internal table:

| File | Lines | Category | Reason |
|------|-------|----------|--------|
| `src/auth/middleware.ts` | 42-67 | Security | New token validation logic |
| `deploy/terraform/iam.tf` | 12-18 | Config / Infrastructure | IAM role permissions widened |
| `src/cache/redis.ts` | 1-89 | Novel Patterns | First use of Redis; no existing caching pattern |

Consolidate entries: if a file has multiple flagged regions in the same category, merge them into one entry with a combined line range.

#### Step 4 — Generate the review guide

Format the guide as a categorized markdown section with file diff links.

GitHub diff anchor format:
```bash
# SHA-256 of the file path for the diff anchor (cross-platform)
if command -v sha256sum >/dev/null 2>&1; then
  printf '%s' "path/to/file" | sha256sum | cut -d' ' -f1
else
  printf '%s' "path/to/file" | shasum -a 256 | cut -d' ' -f1
fi
```

Link format: `https://github.com/{owner}/{repo}/pull/{number}/files#diff-{sha256}`
Line-level anchors: append `R{line}` for right-side lines (e.g., `#diff-{sha256}R42`).

#### Step 5 — Append to PR description

Fetch the current PR body, append the review guide in a demarcated block, and update:

```bash
CURRENT_BODY=$(gh pr view {pr_number} --json body --jq .body)
# Append or replace the review guide section, then write to temp file
BODY_FILE=$(mktemp)
trap 'rm -f "$BODY_FILE"' EXIT INT TERM
printf '%s' "$UPDATED_BODY" > "$BODY_FILE"
gh pr edit {pr_number} --body-file "$BODY_FILE"
```

Use HTML comment markers so the section is identifiable and replaceable on re-runs:

```markdown
<!-- pr-human-guide -->
## Review Guide

### Security
- [`src/auth/middleware.ts` (L42-67)](link) — New token validation logic
- [`src/api/validate.ts` (L15-23)](link) — Input sanitization changes

### Config / Infrastructure
- [`deploy/terraform/iam.tf` (L12-18)](link) — IAM role permissions widened

### Novel Patterns
- [`src/cache/redis.ts`](link) — First use of Redis in this codebase; no existing caching pattern to reference

<!-- /pr-human-guide -->
```

If no items are flagged in any category, append a short note: "No areas requiring special human review attention were identified."

If the markers already exist in the body, replace the block between them (idempotent on re-runs).

#### Step 6 — Report

Output a summary to the terminal:

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

When N=0, omit the item count line.

### Interaction with Other Skills

- **ship-it**: Could invoke pr-human-guide as a final step after creating the PR. Not wired in v1 — users invoke manually.
- **pr-comments**: After addressing all comments, users can run pr-human-guide to prep for final human review. Not auto-invoked in v1.
- **peer-review**: Complementary — peer-review does the automated code review, pr-human-guide tells the human where to focus their own review.

### What This Skill Does NOT Do

- Does not perform a code review (that's peer-review / code-review)
- Does not address or reply to review comments (that's pr-comments)
- Does not judge code quality — it identifies *areas* for human judgment
- Does not block merging or enforce checks

## Files to Create

| File | Description |
|------|-------------|
| `skills/pr-human-guide/SKILL.md` | Skill definition with frontmatter + workflow |
| `evals/pr-human-guide/evals.json` | Eval test cases |
| `evals/pr-human-guide/benchmark.json` | Benchmark results (after running evals) |
| `evals/pr-human-guide/benchmark.md` | Human-readable benchmark report |

## Files to Modify

| File | Description |
|------|-------------|
| `README.md` | Add pr-human-guide to the Available Skills table and Skill Notes |
| `CLAUDE.md` | Add pr-human-guide to the Available Skills table with trigger phrases |

## Verification

1. Create the skill and invoke it on an existing PR to verify output format
2. Verify the PR description is correctly updated with the review guide section
3. Re-invoke to verify idempotent replacement of the guide section
4. Run `npx cspell skills/pr-human-guide/SKILL.md` for spell checking
5. Run `uv run --with pytest pytest tests/` to verify no regressions
6. Run evals and populate benchmark files
