# Copilot Instructions

**Keep `CLAUDE.md` in sync**: whenever you add, update, or remove a rule in this file, apply the equivalent change to `CLAUDE.md`. The two files serve different assistants (Copilot vs. Claude Code) but should encode the same project conventions. When running `/learn` in this project, always update **both** `CLAUDE.md` and `.github/copilot-instructions.md` without asking which to update.

## Project Overview

This repository contains reusable agent skills for Claude Code and other coding assistants. Skills are defined in `skills/<skill-name>/SKILL.md`. Development artifacts live separately:

- `evals/<skill-name>/`: eval cases, benchmark data, and benchmark docs
- `tests/<skill-name>/`: unit tests for classifiable logic
- `specs/<N>-<topic>/`: design specs and task tracking

Evals belong under `evals/` at the repo root, not inside skill directories.

## Core Editing Rules

- Keep instructions assistant-neutral unless a tool or platform detail is inherently assistant-specific.
- Preserve the existing workflow style in `SKILL.md`: numbered process sections, executable bash blocks, tables where useful, and examples where useful.
- When substantially modifying a skill, update its `README.md` entry and notes.
- Bump `metadata.version` on every `SKILL.md` change or reference-file change that affects the skill.
- On an active PR branch, re-run the check below before committing **any** `SKILL.md` change — not just when you intend to bump — to confirm no bump already exists relative to `origin/main`:

```bash
git fetch origin && git diff origin/main -- skills/<name>/SKILL.md | rg '^\+  version:'
```

- Only bump once per PR. Follow-up reviewer-fix commits should not add another bump. This limit applies to the PR as a whole — a PR touching SKILL.md plus multiple reference files still gets exactly one version increment total. Do not add a new bump for each changed reference file.

## Specs

- Spec step numbers drift. Re-verify references like "Step 5" or "Step 13" against the current `SKILL.md` before editing spec text.
- Use phrase anchors, not hardcoded line numbers, in specs for files that may change during the same task.
- If a spec has both `plan.md` and `tasks.md`, apply the corresponding fix to both files in the same pass.
- When working through `specs/*/tasks.md`, mark each checkbox complete immediately after completing that item.
- After editing spec files, re-read all modified spec files before finishing.

## Evals And Benchmarks

- Every skill with evals should keep `evals/<skill-name>/benchmark.json` in sync with the latest results.
- After updating a benchmark, also update the `Eval Δ` column in `README.md` and the `±` stat values in the `benchmark.md` Summary table — the table mirrors `run_summary` and is not auto-generated.
- `grading.json` files must include a `summary` block with `passed`, `failed`, `total`, and `pass_rate`.
- Use `null`, not `0` or `0.0`, for unknown token/time measurements in benchmark data (`tokens`, `time_seconds` feed `run_summary` aggregates). Treat `tool_calls` and `errors` as optional per-run metadata: use `null` only when truly unknown, keep `0` when actually measured. When updating or adding runs, backfill any existing `tokens: 0`, `time_seconds: 0.0`, `tool_calls: 0`, or `errors: 0` entries to `null` only when they represent unknown measurements.
- Keep `run_summary.delta.pass_rate` at 2-decimal precision.
- `run_summary.delta` values must be computed from exact (unrounded) run-data means, not from the rounded `mean` fields. When stored means are rounded, add a sentence to `benchmark.md`: "Summary-table Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means."
- When adding new evals or re-running existing evals, run them in the same task and update benchmark artifacts immediately — also update `metadata.skill_version` and `metadata.evals_run`. Exception: for validation-only runs, do not add run entries or bump `metadata.skill_version`.
- When changing pass/fail verdicts on existing benchmark expectations, re-run the eval rather than re-grading with hypothetical reasoning — hypothetical re-grades can describe fundamentally different behavior from what was originally observed.
- When adding a new skill to `README.md`, add an `Eval cost` note sourced from the skill's benchmark doc.
- If reviewer feedback suggests benchmark values, recompute from the actual `runs` array instead of copying the suggestion.
- When updating `pass_rate`, `passed`, `failed`, or `total` in a run entry, also scan both the run-level `notes` array and the top-level `notes` array for matching prose counts (e.g. "3/5 (60%)") and update them — numeric fields and prose strings drift independently.
- When adding version-scoped notes to `benchmark.json`'s top-level `notes` array, also audit older entries that reference the same eval IDs — they can describe behavior removed in an earlier version. Stale semantic descriptions contradict newer entries and mislead reviewers. Update or replace them in the same commit.
- Place the top-level `notes` array at the root of `benchmark.json`, not inside `metadata` — between the closing `}` of `metadata` and the opening `[` of `runs`.
- When renaming action labels or vocabulary in `SKILL.md`, also search `CLAUDE.md` for hardcoded step references that use the old name — step renames must propagate there just as they do to `evals.json` and `benchmark.json`.
- Eval assertions must test user-facing output, not internal signals: if a skill uses an internal return value from a subagent (e.g. `NO FINDINGS`) and translates it to user-visible text (e.g. `'No issues found.'`), the assertion must test the user-visible string — not the internal signal. An assertion testing the internal signal will never catch regressions in the translation/presentation layer.
- **When assertion semantics are inverted** (not just renamed), null ALL result fields in the affected `benchmark.json` runs: `pass_rate`, `passed`, `failed`, `time_seconds`, `tokens`, `tool_calls`, and `errors`. The measurement fields still feed `run_summary` aggregates even when pass/fail is null. After nulling, recompute `run_summary` excluding those runs from all stat calculations, then update `benchmark.md` Summary table and README Eval Δ.
- Fixture-based eval prompts must embed the fixture in the `prompt` field, not `expected_output`: `expected_output` is prose describing the expected grading outcome for the eval runner — it is not readable by the executor. Putting fixture CLI/tool responses in `expected_output` would confuse the executor about what to output, or cause the grader to treat fixture data as the expected result.
- When a run is excluded from both sides of the paired comparison (e.g. contaminated), null all result fields in BOTH the `with_skill` and `without_skill` entries — not just the contaminated side. Leaving one side non-null makes the documented paired-eval count inconsistent with what mechanical consumers derive from filtering non-null entries. When nulling result fields, also null the `passed` and `evidence` fields in the run's `expectations` array — leaving verdicts set while results are null implies the grading is valid when it is not.
- When a benchmark.json run entry has null result fields, the corresponding `benchmark.md` table row must show `N/A | — | —` in the Pass rate, Passed, and Failed columns — not the original computed values.

## Tests And Validation

- After modifying skills or skill reference files, run:

```bash
uv run --with pytest pytest tests/
```

- Consider whether tests under `tests/<skill-name>/` need to be added or updated for behavior changes.
- This repo uses cspell. After editing markdown or instruction files, run `npx cspell <file>` on each modified file.
- If cspell flags a legitimate repo term, add it to `cspell.config.yaml` immediately.
- If a word is no longer used, remove it from `cspell.config.yaml` after confirming with `rg -w <word>`.
- Adding a singular form to `cspell.config.yaml` does not automatically cover its plural — add both forms explicitly (e.g., `metacharacter` and `metacharacters`) if both appear in the codebase.

## Git And PR Workflow

- Never commit directly to `main`. Always create a feature branch and open a PR for review.
- Do not rewrite history on a PR that already has review comments. Avoid force-push, rebase, and `git commit --amend` on pushed commits.
- **When a PR branch has merge conflicts and rebase is forbidden** (review comments exist), run `git fetch origin && git merge origin/main` — not rebase — to resolve them.
- This repo uses squash merges.
- After pushing follow-up commits to an existing PR branch, compare `git log origin/main..HEAD --oneline` against the PR title/body and update the PR description if behavior changed.
- After implementing or fully addressing a PR review comment, resolve the thread through the GitHub GraphQL API only when no further reviewer follow-up is needed.
- After merging a PR, sync local `main` with `git reset --hard origin/main`, but only after checking for uncommitted changes.

## Command And Tooling Gotchas

- Do not hardcode `/tmp/`; use `mktemp`, `$TMPDIR`, or `${TMPDIR:-/private/tmp}`. `${TMPDIR:-/tmp}` is also a violation — the fallback must be `/private/tmp`, not `/tmp`.
- **`trap` cleanup fires at the end of each Bash tool call**: use `trap 'rm -f "$FILE"' EXIT INT TERM` immediately after `mktemp` only when that temp file is created and consumed within the same tool call. When a temp file must persist across multiple tool calls, write it to a named path (e.g. `"${TMPDIR:-/private/tmp}/name.txt"`) without a `trap` — `trap 'rm -f "$FILE"' EXIT` fires when the subshell exits at the end of each call, deleting the file before the next call runs. Clean up explicitly in a later call instead.
- If `git commit` fails because of GPG/keyring access, use `--no-gpg-sign` only as a fallback after the failure.
- In sandboxed environments, HTTPS `git push` may hang on credentials. A working pattern is:

```bash
TOKEN=$(gh auth token) && git -c "url.https://x:${TOKEN}@github.com/.insteadOf=https://github.com/" push
```

- `gh api --paginate --jq` applies `--jq` per page. To deduplicate across all pages, collect pages first with `jq -s`.
- When passing shell variables into `jq`, use `jq --arg name "$value"` instead of shell string interpolation inside the filter.
- `rg` alternation uses bare `|`, not `\|`.
- In an unquoted heredoc (`<<EOF`), `\"` is a literal backslash-quote — the receiver sees `\"`, not `"`. If you need a double quote in the heredoc body, write plain `"` directly, or use `<<'EOF'` to suppress shell processing.
- **`gh api -f body` strips backtick-quoted text**: backticks inside a `-f body="..."` argument are interpreted as shell command substitution, silently stripping the content. Use a heredoc with `--input -` or write the body to a temp file and pass `--body-file` instead.
- GitHub review thread `isOutdated` means the diff location moved, not that the concern is resolved.
- **`replace_all` removing trailing text can merge the next line**: when the removed substring is the last non-whitespace content on a line, the Edit tool may collapse the following line onto the same line. Verify surrounding context after any `replace_all` that targets text at the end of a line.
- **Inserting elements into a JSON array with Edit requires a trailing comma on the preceding element**: when replacing the closing `]` to insert new objects, the previous element's `}` must end with `,` in the replacement string. Validate after array edits: `python3 -c 'import json; json.load(open("file.json"))'`.
- **External CLI tools (gemini, copilot) may need network access and writable filesystem access outside a restrictive sandbox**: `gemini` needs network access to make API calls, and `copilot` may also need writable access for session-state files to avoid EPERM noise. In Claude Code, this may require enabling `dangerouslyDisableSandbox: true`; in other runtimes, use the equivalent setting that grants the needed capabilities.
- **zsh escapes `!` in jq filters**: `!=` in a jq expression passed as a Bash argument becomes `\!=`, causing jq parse errors. Workarounds: write the jq filter to a file and use `jq -f`, or rewrite `!=` as `(== | not)`. For null checks, use `(.field | type == "string")` instead of `.field != null`. Skill jq snippets must avoid `!=` for portability.
- **In a worktree, edit skills at the worktree path `skills/<name>/SKILL.md` — not via `.claude/skills/<name>/SKILL.md`**, which resolves to the main repo's copy via the symlink.
- **Git write operations in a worktree may require sandbox restrictions to be lifted**: `git add`, `git commit`, and `git push` write lock files to the main repo's `.git/worktrees/<id>/` path — outside the sandbox write allowlist that covers only `.` (the worktree directory). In Claude Code, this may require `dangerouslyDisableSandbox: true`.
- **jq bot-login exclusions need exact equality, not `contains()`**: when excluding a specific bot from a jq filter, use `.user.login == "claude[bot]"` — not `.user.login | contains("claude")`, which silently excludes unrelated bots sharing the substring (e.g. `claude-reviewer[bot]`, `claude-pr-reviewer[bot]`). This bug is easy to introduce and passes casual review; catch it by naming the exact login you mean to exclude.

## Skill Design Guidance

- Name skills from the user's action or role, not the underlying implementation detail.
- **Prefer auto-detection with a disambiguation prompt over adding new flags** when a behavior is only needed in genuinely ambiguous situations. Handle unambiguous cases silently (e.g., only unstaged changes → auto-review with a note); prompt only when intent is unclear (e.g., both staged and unstaged → `[staged/unstaged/all]`). Explicit flags can still be offered as an escape hatch for scripting.
- Keep README / CLAUDE documentation in sync when skill changes are substantial.
- When a workflow pauses for user confirmation, make the stop explicit: tell the agent to output the prompt as its final message and stop generating until the user replies. If the workflow also has auto/manual modes, specify every confirmation gate each mode affects. If auto mode is meant to be hands-free, say explicitly whether later gates (for example push/re-request prompts) are skipped or still require confirmation.
- When listing exit conditions for a workflow loop, state that they are the only valid exit conditions and explicitly forbid subjective early exits.
- When a SKILL.md step does setup work (snapshot, POST, etc.) before delegating to a reference file that has its own entry/setup section covering the same actions, the delegation sentence must name the target section and list what not to re-run — otherwise agents re-enter the setup section and duplicate actions already done in SKILL.md.
- When a SKILL.md step creates a temp file with `mktemp` and uses it within the same tool call, document `trap 'rm -f "$FILE"' EXIT INT TERM` immediately after the `mktemp` call — a manual `rm -f` at the end of the block is skipped on error or interruption. When the temp file must persist across multiple tool calls, use a named path without `trap` instead (see the `trap` cleanup bullet above).
- Bash snippets that assign CLI output to a variable should include `2>&1` so error messages flow into the captured variable and reach fallback/error handling paths (e.g., `REVIEW_OUTPUT=$(cli ... 2>&1)`).
- **When capturing `git diff --quiet` exit codes**, use `VAR=0; git diff --quiet || VAR=$?` — not `git diff --quiet; VAR=$?`. In strict runners (`set -e`) the non-zero exit from "changes present" aborts the script before the assignment runs.

## Persistence

- Store durable project learnings in `CLAUDE.md`, not in per-user hidden memory directories.
- Do not write to `~/.claude/projects/.../memory/` for this project.
- Write timeless rules, not session history — do not reference specific PR numbers, dates, or session details in config rules. Those belong in commit messages.
