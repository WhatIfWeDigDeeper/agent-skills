# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a collection of reusable skill definitions for Claude Code and other coding assistants. Skills are automated workflows defined in SKILL.md files that agents can invoke to perform specific tasks.

## Repository Structure

```
skills/
  <skill-name>/
    SKILL.md     # Skill definition with frontmatter + workflow
evals/
  <skill-name>/
    evals.json   # Test cases for the skill (not distributed with the skill)
specs/
  <N>-<topic>/  # Design specs: plan.md and tasks.md for planned changes
```

Evals live under `evals/` at the repo root, not inside `skills/` — they are development artifacts and should not be bundled when a skill is distributed.

**Eval fixtures with intentionally old/pinned versions** (e.g. `evals/uv-deps/fixtures/`) may conflict when a skill like `uv-deps` runs on main and updates those same files. During a merge, keep `--ours` to preserve the intentionally pinned versions.

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

## Adding New Skills

1. Create directory: `skills/<skill-name>/`
2. Create `SKILL.md` following the format above
3. Include YAML frontmatter with name and description
4. Document the workflow with numbered process steps
5. Add bash code blocks for commands that should be executed
6. Include example outputs where helpful
7. Create a symlink so Claude Code can discover it: `ln -s ../../skills/<skill-name> .claude/skills/<skill-name>` (local only — `.claude/skills/` is gitignored). **After editing an existing skill, verify the symlink still resolves correctly** — a skill invocation may load a stale version if the symlink points to a cached or wrong path.
8. Update `README.md` — add the skill to the table and add a notes section

When substantially modifying an existing skill, also update its entry in `README.md`.

## Sandbox Workarounds

- **GPG signing**: `git commit` may fail if GPG keyring is inaccessible. Use `--no-gpg-sign` as a fallback.
- **Heredocs**: `$(cat <<'EOF'...)` may fail with "can't create temp file". Use multiple `-m` flags for commit messages or write content to a temp file first.

## Spell Checking

This repo uses cspell. When you see a cspell diagnostic — whether from the IDE, a linter run, or noticing an unknown-word warning on a file you just edited — immediately add the term to the `words` list in `cspell.config.yaml`. Do not wait for the user to point it out. Use `npx cspell <file>` to check any file you've modified before finishing a task.

## Git Workflow

- **Never commit directly to `main`.** Always create a feature branch and open a PR for review.
- This repo only allows squash merges. Use `gh pr merge --squash --delete-branch` (or the GitHub UI).
- After merging a PR, sync local main with `git reset --hard origin/main` rather than `git pull` — local main may have diverged from origin after a squash merge. **Before running `git reset --hard`, check for uncommitted changes (`git status`). If any exist, stash them first (`git stash`) or ask the user — do not silently discard them.**
- After addressing PR review comments, resolve each thread via the GitHub GraphQL API:
  ```bash
  # Get thread IDs
  gh api graphql -f query='{ repository(owner: "OWNER", name: "REPO") { pullRequest(number: N) { reviewThreads(first: 20) { nodes { id isResolved comments(first: 1) { nodes { path line } } } } } } }'
  # Resolve each thread
  gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: "THREAD_ID"}) { thread { isResolved } } }'
  ```

## Testing

- After modifying skill and reference files run `uv run --with pytest pytest tests/` to verify changes don't break existing assertions.
- Consider whether new tests are needed to cover the changed behavior.
- **When adding a new skill or substantially modifying an existing skill**, propose adding or updating tests under `tests/<skill-name>/`. Tests should cover help trigger detection, argument parsing, and any classifiable logic (workflow routing, comment classification, etc.). Follow the patterns in existing test suites (e.g. `tests/js-deps/`, `tests/ship-it/`).

## Evals and Benchmarking

- Each skill with an `evals/` directory should have a corresponding `evals/<skill-name>/benchmark.json`.
- **After running evals for a skill, always update `evals/<skill-name>/benchmark.json`** with the new results. Do not leave stale benchmark data.
- The benchmark.json format mirrors `evals/ship-it/benchmark.json`: a `metadata` block, a `runs` array (one entry per eval × configuration), and a `run_summary` with mean/stddev/min/max stats plus a `delta` section comparing `with_skill` vs `without_skill`.
- **`grading.json` must include a `summary` block** or `aggregate_benchmark.py` will report 0% for all runs even when expectations pass. Required shape: `{"summary": {"passed": N, "failed": N, "total": N, "pass_rate": 0.N}, "expectations": [{"text": "...", "passed": true, "evidence": "..."}]}`. The `expectations` field names must be exactly `text`, `passed`, and `evidence` — the eval viewer depends on them.
- **After updating benchmark.json, also update the `Eval Δ` column in the `README.md` Available Skills table** to reflect the new pass-rate delta (e.g. `+62%`).
- **Spawn eval subagents with `mode: "auto"`** to suppress per-tool approval prompts. Default permission mode causes interruptions that slow down parallel eval runs and can break the workflow.
- **After creating a PR**, check which skills were modified and whether the changes affect eval-relevant behavior (workflow steps, decision logic, command sequences, assertion-tested output). If so, recommend the user run evals for those skills before merging. If the changes are documentation-only, cosmetic, or don't affect behavior tested by evals (e.g. adding notes, security guidance, or comments), note that re-running evals is not needed and explain why.

## Portability

Skills in this repo should work with any coding assistant, not just Claude Code. Keep workflow instructions in assistant-neutral language. When a step has a Claude Code-specific mechanic, note it with a qualifier rather than stating it as a universal requirement:

- **Arguments**: "The text following the skill invocation is available as `$ARGUMENTS` (e.g. in Claude Code: `/skill-name args`)" — not "Claude Code passes..."
- **Sandbox**: "Requires OS keyring/network access — lift any sandbox restrictions (in Claude Code: `dangerouslyDisableSandbox: true`)" — not "requires `dangerouslyDisableSandbox: true`"
- **PR attribution**: Use a generic placeholder like `Generated with [Claude Code](...)` that other assistants can substitute with their own name

## Skill Design Patterns

- **Naming perspective**: Name skills from the user's action/role, not the underlying operation. E.g., `pr-comments` (author addressing feedback on their PR) not `pr-review` (which implies being the reviewer).
- **Isolation**: Use dedicated branches to test changes without affecting the main working directory
- **Validation**: Run build/lint/test after making changes
- **Parallelization**: Use Task subagents for processing multiple items concurrently
- **Documentation sync**: Update CLAUDE.md/README.md when major versions change
- **PR-driven**: Create pull requests for review rather than auto-committing
- **GitHub suggested changes**: There is no public REST API to accept them. Extract the replacement from the `suggestion` fenced block in the comment body and apply it as a local edit.

## Interaction Patterns

- **Proactively offer next steps** at natural milestones (eval run complete, skill review done, PR merged, etc.). Don't wait for the user to ask "what should we do next?" — present a short prioritized list of options and let them choose.
- **Never bundle irreversible actions into option descriptions.** When presenting choices, keep destructive or hard-to-reverse steps (merging a PR, force-pushing, deleting branches) separate from preparatory work. Even if merging is the obvious next step after a cleanup, complete the reversible work first, then explicitly ask "ready to merge?" before executing. A user selecting option "1" authorizes the work described, not every downstream consequence implied by the framing.

## Persisting Learnings

- **Persisting Learnings**: When you discover a new gotcha, stack-specific pattern, or tool quirk during a session, add it directly to the relevant section of `CLAUDE.md` before ending the session — so teammates and future agents benefit. For repeatable multi-step processes, create a skill in `.claude/skills/`. **NEVER write to `~/.claude/projects/.../memory/` for this project** — those files are invisible to other contributors, may be reset, and are not the persistence mechanism for this repo. `CLAUDE.md` is the only approved place for project learnings. If any files exist in the memory directory, delete them.
