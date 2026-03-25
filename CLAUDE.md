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

**Spec step numbers drift**: When editing or reviewing specs for an existing skill, verify step numbers (e.g. "Step 5", "Step 6") against the current SKILL.md — they shift as skills evolve and specs can silently fall out of sync.

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

**Bump the skill version** in the `metadata.version` frontmatter field whenever you modify a skill's behavior or documentation — use patch increments (e.g. `"0.7"` → `"0.8"`) for fixes and additions, minor increments (e.g. `"0.7"` → `"0.9"` or `"1.0"` → `"1.1"`) for significant workflow changes. This helps downstream users know when to pull updates. **Only bump once per PR**: before suggesting a version increment, run `git diff main -- skills/<name>/SKILL.md | grep '^+.*version'` — if a bump already exists relative to `main`, do not bump again for follow-up commits on the same branch.

## Sandbox Workarounds

- **GPG signing**: `git commit` may fail if GPG keyring is inaccessible. Use `--no-gpg-sign` **only as a fallback after a signing failure** — do not use it preemptively. `dangerouslyDisableSandbox: true` (for keyring/network access) and GPG signing are separate; enabling sandbox does not mean GPG will fail.
- **Heredocs**: `$(cat <<'EOF'...)` may fail with "can't create temp file". Use multiple `-m` flags for commit messages or write content to a temp file first — use `mktemp` (which respects `$TMPDIR`) or a path under `${TMPDIR:-/private/tmp}` rather than a hardcoded, user-specific directory.
- **Do not hardcode `/tmp/`** — it is not writable in sandbox mode. Always use `mktemp`, `$TMPDIR`, or a generic `/private/tmp` path (not a user-specific subdirectory) when creating temp files in any shell command.

## Spell Checking

This repo uses cspell. When you see a cspell diagnostic — whether from the IDE, a linter run, or noticing an unknown-word warning on a file you just edited — immediately add the term to the `words` list in `cspell.config.yaml`. Do not wait for the user to point it out. Use `npx cspell <file>` to check any file you've modified before finishing a task. Conversely, when you change phrasing that caused a word to be added, remove it if it no longer appears anywhere in the repo (use `rg -w <word>` or `git grep -w <word>` to confirm) — stale wordlist entries accumulate silently and are caught by reviewers, not linters. Before merging a new cspell CI step (or after changing the set of files it scans), run `npx cspell "skills/**/*.md" "specs/**/*.md"` against all in-scope files locally to backfill any pre-existing wordlist gaps — otherwise CI will fail immediately on the first PR.

## Git Workflow

- **Never commit directly to `main`.** Always create a feature branch and open a PR for review.
- **Never rewrite history on a PR that has review comments** (from humans or bots). This means no force push, no `git rebase`, no `git commit --amend` on pushed commits. Rewriting history detaches inline comments from their source lines and disrupts reviewers who have already pulled the branch. If commits need fixing after comments exist, add a new commit instead. Squash happens at merge time.
- This repo only allows squash merges. Use `gh pr merge --squash --delete-branch` (or the GitHub UI). When merging via `gh pr merge`, a PostToolUse hook will automatically handle prompting for `/learn` on the merged changes; when merging via the GitHub UI or any other method, explicitly ask the user to run `/learn` on the merged PR (or on `main`) so the assistant can update its context. **PostToolUse hooks fire on pattern match, not success**: the grep-based hook triggers on every Bash call containing the pattern — write hook messages as "If [action] succeeded..." not "[action] happened..." to avoid misleading output on failed commands, `--help` calls, or partial matches.
- After merging a PR, sync local main with `git reset --hard origin/main` rather than `git pull` — local main may have diverged from origin after a squash merge. **Before running `git reset --hard`, check for uncommitted changes (`git status`). If any exist, stash them first (`git stash`) or ask the user — do not silently discard them.**
- **After pushing follow-up commits to an existing PR branch**, check whether the PR title/body still reflects all commits (`git log main..HEAD --oneline`) and update with `gh pr edit` if needed.
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
- **After updating benchmark.json, immediately update the `Eval Δ` column in the `README.md` Available Skills table** to reflect the new pass-rate delta (e.g. `+62%`). Do not finish the task or open a PR without doing this.
- **Spawn eval subagents with `mode: "auto"`** to suppress per-tool approval prompts. Default permission mode causes interruptions that slow down parallel eval runs and can break the workflow.
- **After creating a PR**, check which skills were modified and whether the changes affect eval-relevant behavior (workflow steps, decision logic, command sequences, assertion-tested output). If so, recommend the user run evals for those skills before merging. If the changes are documentation-only, cosmetic, or don't affect behavior tested by evals (e.g. adding notes, security guidance, or comments), note that re-running evals is not needed and explain why.
- **`eval_name` must be present for ALL runs** in `benchmark.json`, not just newly added ones. When adding runs for new evals, backfill `eval_name` for any existing runs that lack it — a partial population breaks schema uniformity with the ship-it format.
- **Use `tokens: null` (not `0`) in `benchmark.json`** when the token count was not recorded for a run. `0` implies measured-as-zero and will skew mean/stddev stats. When updating or adding runs, backfill any existing `tokens: 0` entries that represent unknown counts to `null`, similar to the `eval_name` rule above.
- **When adding new runs to an existing benchmark.json**, also update `metadata.evals_run` (append the new eval ID) and `metadata.skill_version` to match the current skill version — easy to miss when adding a single targeted eval rather than re-running the full suite.
- **When prompting eval subagents**, pass the full assertion text strings from `evals.json` explicitly in the prompt — otherwise subagents use assertion IDs as the `text` field in `grading.json` (e.g. `"skips-previously-replied-thread"` instead of the full sentence), which breaks alignment with the eval viewer.
- **Non-discriminating evals** (both configurations score 100%) are expected when the scenario makes the correct behavior explicit enough for the baseline to handle it. Document them with a note in `benchmark.json` — they establish a baseline but don't contribute to the delta. Evals 13 and 16 in pr-comments are examples.
- **When adding supplementary regression runs** (run_number > 1 for specific evals): add a `regression_run_evals` field to `metadata` listing which eval IDs have supplementary runs, scope token stats notes to "primary (run_number=1) runs", and update `benchmark.md` accordingly. Keep `runs_per_configuration` equal to the primary suite's value — do not bump it to the max `run_number`, which would misrepresent evals that only have one run.
- **For structural refactors that move logic to a reference file** (no behavioral change), run only the evals that exercise the moved logic rather than the full suite. Get the old-skill baseline via `git show HEAD:skills/<name>/SKILL.md > "$TMPDIR/<name>-snapshot.md"`.
- **When a grader flags a missing assertion**, add it to `evals.json` and re-grade the existing transcript — no need to re-spawn the executor if the transcript is detailed enough to provide evidence.

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
- **Mandatory-step reference links must be imperative**: When a step delegates to an external file for mandatory continuation, write "**you must now execute [file]** — do not skip to the report" rather than "see [file]". Agents treat passive cross-references as informational and will skip them when generating the final output.

## Interaction Patterns

- **Proactively offer next steps** at natural milestones (eval run complete, skill review done, PR merged, etc.). Don't wait for the user to ask "what should we do next?" — present a short prioritized list of options and let them choose.
- **Never bundle irreversible actions into option descriptions.** When presenting choices, keep destructive or hard-to-reverse steps (merging a PR, force-pushing, deleting branches) separate from preparatory work. Even if merging is the obvious next step after a cleanup, complete the reversible work first, then explicitly ask "ready to merge?" before executing. A user selecting option "1" authorizes the work described, not every downstream consequence implied by the framing.
- **Suggest a fresh conversation on topic changes.** When the user starts work on an unrelated skill, feature, or task and the current conversation already has significant history (compressed messages, multiple completed tasks), suggest starting a new conversation to avoid stale context bleeding into unrelated work.
- **Exit plan mode before running skills.** When a skill is invoked while plan mode is active, silently exit plan mode first so the skill's own confirmation prompts (e.g. `y/N/auto`) work as designed.

## Persisting Learnings

- **Persisting Learnings**: When you discover a new gotcha, stack-specific pattern, or tool quirk during a session, add it directly to the relevant section of `CLAUDE.md` before ending the session — so teammates and future agents benefit. For repeatable multi-step processes, create a skill in `.claude/skills/`. **NEVER write to `~/.claude/projects/.../memory/` for this project** — those files are invisible to other contributors, may be reset, and are not the persistence mechanism for this repo. `CLAUDE.md` is the only approved place for project learnings. If any files exist in the memory directory, delete them.
