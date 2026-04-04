# Copilot Instructions

**Keep `CLAUDE.md` in sync**: whenever you add, update, or remove a rule in this file, apply the equivalent change to `CLAUDE.md`. The two files serve different assistants (Copilot vs. Claude Code) but should encode the same project conventions.

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
- Use `null`, not `0` or `0.0`, for unknown token/time measurements in benchmark data.
- Keep `run_summary.delta.pass_rate` at 2-decimal precision.
- When adding new evals, run them in the same task and update benchmark artifacts immediately.
- When adding a new skill to `README.md`, add an `Eval cost` note sourced from the skill's benchmark doc.
- If reviewer feedback suggests benchmark values, recompute from the actual `runs` array instead of copying the suggestion.
- When updating `pass_rate`, `passed`, `failed`, or `total` in a run entry, also scan both the run-level `notes` array and the top-level `notes` array for matching prose counts (e.g. "3/5 (60%)") and update them — numeric fields and prose strings drift independently.
- Place the top-level `notes` array at the root of `benchmark.json`, not inside `metadata` — between the closing `}` of `metadata` and the opening `[` of `runs`.
- When renaming action labels or vocabulary in `SKILL.md`, also search `CLAUDE.md` for hardcoded step references that use the old name — step renames must propagate there just as they do to `evals.json` and `benchmark.json`.
- Eval assertions must test user-facing output, not internal signals: if a skill uses an internal return value from a subagent (e.g. `NO FINDINGS`) and translates it to user-visible text (e.g. `'No issues found.'`), the assertion must test the user-visible string — not the internal signal. An assertion testing the internal signal will never catch regressions in the translation/presentation layer.
- Fixture-based eval prompts must embed the fixture in the `prompt` field, not `expected_output`: `expected_output` is prose describing the expected grading outcome for the eval runner — it is not readable by the executor. Putting fixture CLI/tool responses in `expected_output` would confuse the executor about what to output, or cause the grader to treat fixture data as the expected result.

## Tests And Validation

- After modifying skills or skill reference files, run:

```bash
uv run --with pytest pytest tests/
```

- Consider whether tests under `tests/<skill-name>/` need to be added or updated for behavior changes.
- This repo uses cspell. After editing markdown or instruction files, run `npx cspell <file>` on each modified file.
- If cspell flags a legitimate repo term, add it to `cspell.config.yaml` immediately.
- If a word is no longer used, remove it from `cspell.config.yaml` after confirming with `rg -w <word>`.

## Git And PR Workflow

- Never commit directly to `main`.
- Do not rewrite history on a PR that already has review comments. Avoid force-push, rebase, and `git commit --amend` on pushed commits.
- This repo uses squash merges.
- After pushing follow-up commits to an existing PR branch, compare `git log origin/main..HEAD --oneline` against the PR title/body and update the PR description if behavior changed.
- After implementing or fully addressing a PR review comment, resolve the thread through the GitHub GraphQL API only when no further reviewer follow-up is needed.
- After merging a PR, sync local `main` with `git reset --hard origin/main`, but only after checking for uncommitted changes.

## Command And Tooling Gotchas

- Do not hardcode `/tmp/`; use `mktemp`, `$TMPDIR`, or `${TMPDIR:-/private/tmp}`. `${TMPDIR:-/tmp}` is also a violation — the fallback must be `/private/tmp`, not `/tmp`.
- If `git commit` fails because of GPG/keyring access, use `--no-gpg-sign` only as a fallback after the failure.
- In sandboxed environments, HTTPS `git push` may hang on credentials. A working pattern is:

```bash
TOKEN=$(gh auth token) && git -c "url.https://x:${TOKEN}@github.com/.insteadOf=https://github.com/" push
```

- `gh api --paginate --jq` applies `--jq` per page. To deduplicate across all pages, collect pages first with `jq -s`.
- When passing shell variables into `jq`, use `jq --arg name "$value"` instead of shell string interpolation inside the filter.
- `rg` alternation uses bare `|`, not `\|`.
- In an unquoted heredoc (`<<EOF`), `\"` is a literal backslash-quote — the receiver sees `\"`, not `"`. If you need a double quote in the heredoc body, write plain `"` directly, or use `<<'EOF'` to suppress shell processing.
- GitHub review thread `isOutdated` means the diff location moved, not that the concern is resolved.

## Skill Design Guidance

- Name skills from the user's action or role, not the underlying implementation detail.
- Prefer PR-driven workflows over auto-committing directly to shared branches.
- Validate changes after editing, and keep README / CLAUDE documentation in sync when the change is substantial.
- When a workflow pauses for user confirmation, make the stop explicit: tell the agent to output the prompt as its final message and stop generating until the user replies. If the workflow also has auto/manual modes, specify every confirmation gate each mode affects. If auto mode is meant to be hands-free, say explicitly whether later gates (for example push/re-request prompts) are skipped or still require confirmation.
- When listing exit conditions for a workflow loop, state that they are the only valid exit conditions and explicitly forbid subjective early exits.
- When a SKILL.md step does setup work (snapshot, POST, etc.) before delegating to a reference file that has its own entry/setup section covering the same actions, the delegation sentence must name the target section and list what not to re-run — otherwise agents re-enter the setup section and duplicate actions already done in SKILL.md.

## Persistence

- Store durable project learnings in `CLAUDE.md`, not in per-user hidden memory directories.
- Do not write to `~/.claude/projects/.../memory/` for this project.
