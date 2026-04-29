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
- **Skill description has a 500-character hard limit** — the `description` field in SKILL.md frontmatter is capped at 500 characters by the skills runtime. Keep descriptions concise; count characters before finalizing.
- Preserve the existing workflow style in `SKILL.md`: numbered process sections, executable bash blocks, tables where useful, and examples where useful.
- When substantially modifying a skill, update its `README.md` entry and notes.
- Bump `metadata.version` on every `SKILL.md` change or reference-file change that affects the skill.
- On an active PR branch, re-run the check below before committing **any** `SKILL.md` change — not just when you intend to bump — to confirm no bump already exists relative to `origin/main`:

```bash
git fetch origin && git diff origin/main -- skills/<name>/SKILL.md | rg '^\+  version:'
```

- Only bump once per PR. Follow-up reviewer-fix commits should not add another bump. Each reviewer-fix commit should touch only the files needed to address the feedback. This limit applies to the PR as a whole — a PR touching SKILL.md plus multiple reference files still gets exactly one version increment total. Do not add a new bump for each changed reference file. **Exception: do not bump the version when a skill is first introduced** — a new skill's initial version (e.g. `"0.1"`) is set at creation time; the "once per PR" bump applies only to subsequent changes. Check `git diff --name-status origin/main...HEAD -- skills/<name>/SKILL.md`: `A` (added) means first introduction in this PR; `M` (modified) triggers the bump rule.

## Specs

- Spec step numbers drift. Re-verify references like "Step 5" or "Step 13" against the current `SKILL.md` before editing spec text.
- Use phrase anchors, not hardcoded line numbers, in specs for files that may change during the same task.
- If a spec has both `plan.md` and `tasks.md`, apply the corresponding fix to both files in the same pass.
- When working through `specs/*/tasks.md`, mark each checkbox complete immediately after completing that item.
- After editing spec files, re-read all modified spec files before finishing.

## Evals And Benchmarks

- Every skill with evals should keep `evals/<skill-name>/benchmark.json` in sync with the latest results.
- After updating a benchmark, also update the `Eval Δ` column in `README.md` and the `±` stat values in the `benchmark.md` Summary table — the table mirrors `run_summary` and is not auto-generated. Also update the `Eval cost` bullet in the skill's Skill Notes section in `README.md` — it contains the delta percentage and discriminating eval count and does not auto-update.
- `grading.json` files must include a `summary` block with `passed`, `failed`, `total`, and `pass_rate`.
- Eval `evidence` strings must be repo-relative — no absolute `/Users/...` paths in `benchmark.json` or `grading-*.json`.
- Use `null`, not `0` or `0.0`, for unknown token/time measurements in benchmark data (`tokens`, `time_seconds` feed `run_summary` aggregates). Treat `tool_calls` and `errors` as optional per-run metadata: use `null` only when truly unknown, keep `0` when actually measured. When updating or adding runs, backfill any existing `tokens: 0`, `time_seconds: 0.0`, `tool_calls: 0`, or `errors: 0` entries to `null` only when they represent unknown measurements.
- Keep `run_summary.delta.pass_rate` at 2-decimal precision.
- `run_summary.delta` values must be computed from exact (unrounded) run-data means, not from the rounded `mean` fields. When stored means are rounded, add a sentence to `benchmark.md`: "Summary-table Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means."
- When adding new evals or re-running existing evals, run them in the same task and update benchmark artifacts immediately — also update `metadata.skill_version` and `metadata.evals_run`. Exception: for validation-only runs, do not add run entries or bump `metadata.skill_version`.
- When changing pass/fail verdicts on existing benchmark expectations, re-run the eval rather than re-grading with hypothetical reasoning — hypothetical re-grades can describe fundamentally different behavior from what was originally observed. The same applies when adding a new assertion to an existing run entry — evidence must come from an observed transcript, not inferred reasoning. Spawn a fresh executor run to get real evidence.
- When renaming an eval's `name` field in `evals.json`, also update `eval_name` in all matching `benchmark.json` run entries, any prose mentions in `benchmark.json` `notes` strings, and the corresponding `benchmark.md` section header.
- When adding a new skill to `README.md`, add an `Eval cost` note sourced from the skill's benchmark doc.
- If reviewer feedback suggests benchmark values, recompute from the actual `runs` array instead of copying the suggestion.
- When updating `pass_rate`, `passed`, `failed`, or `total` in a run entry, also scan both the run-level `notes` array and the top-level `notes` array for matching prose counts (e.g. "3/5 (60%)") and update them — numeric fields and prose strings drift independently.
- When adding version-scoped notes to `benchmark.json`'s top-level `notes` array, also audit older entries that reference the same eval IDs — they can describe behavior removed in an earlier version. Stale semantic descriptions contradict newer entries and mislead reviewers. Update or replace them in the same commit.
- Place the top-level `notes` array at the root of `benchmark.json`, not inside `metadata` — between the closing `}` of `metadata` and the opening `[` of `runs`.
- When renaming action labels or vocabulary in `SKILL.md`, also search all CLAUDE.md files (`CLAUDE.md`, `evals/CLAUDE.md`, `skills/CLAUDE.md`) for hardcoded step references that use the old name — step renames must propagate there just as they do to `evals.json` and `benchmark.json`.
- Eval assertions must test user-facing output, not internal signals: if a skill uses an internal return value from a subagent (e.g. `NO FINDINGS`) and translates it to user-visible text (e.g. `'No issues found.'`), the assertion must test the user-visible string — not the internal signal. An assertion testing the internal signal will never catch regressions in the translation/presentation layer.
- **When assertion semantics are inverted** (not just renamed), null ALL result fields in the affected `benchmark.json` runs: `pass_rate`, `passed`, `failed`, `time_seconds`, `tokens`, `tool_calls`, and `errors`. The measurement fields still feed `run_summary` aggregates even when pass/fail is null. After nulling, recompute `run_summary` excluding those runs from all stat calculations, then update `benchmark.md` Summary table and README Eval Δ.
- Fixture-based eval prompts must embed the fixture in the `prompt` field, not `expected_output`: `expected_output` is prose describing the expected grading outcome for the eval runner — it is not readable by the executor. Putting fixture CLI/tool responses in `expected_output` would confuse the executor about what to output, or cause the grader to treat fixture data as the expected result.
- **Eval prompts must not name the skill or say "the user has invoked the X skill"** — skill-name leakage in the prompt context reaches the baseline agent, causing it to follow the skill's output format without needing the skill. All evals become non-discriminating and the delta collapses to 0%. Write prompts as natural user requests that don't reference the skill by name (e.g. "Can you add a review guide to PR #42?" not "The user has invoked the pr-human-guide skill on PR #42").
- When a run is excluded from both sides of the paired comparison (e.g. contaminated), null all result fields in BOTH the `with_skill` and `without_skill` entries — not just the contaminated side. Leaving one side non-null makes the documented paired-eval count inconsistent with what mechanical consumers derive from filtering non-null entries. When nulling result fields, also null the `passed` and `evidence` fields in the run's `expectations` array — leaving verdicts set while results are null implies the grading is valid when it is not.
- When a benchmark.json run entry has null result fields, the corresponding `benchmark.md` table row must show `N/A | — | —` in the Pass rate, Passed, and Failed columns — not the original computed values.
- **Eval executor subagents must NOT call Claude Code's `Skill` tool** — both `with_skill` and `without_skill`. For `with_skill`, the executor must follow SKILL.md directly (read it and act); calling `Skill` delegates to a fresh sub-instance instead, which is not what's being measured. For `without_skill`, prohibiting SKILL.md reads alone is insufficient — the agent can still register-and-invoke the skill via the `Skill` tool, contaminating the baseline. Phrase the agent prompt as: "Do NOT call the `Skill` tool. For `with_skill`, do the work yourself by reading SKILL.md." Detection signature: `TOOLS_USED: Other: Skill (...)`.
- **Per-run `tokens` in benchmark.json = `input_tokens + output_tokens` summed across assistant turns** (matches `learn`/`pr-comments`/`peer-review`). Track cache tokens in a separate `cache_tokens` field — they bill at 0.1× (reads) and 1.25–2× (creation), and folding them in inflates the headline 50–100× without proportional cost.
- **Validate expectation key schema after grading**: `jq '[.runs[] | .expectations[] | select((. | keys) != ["evidence","passed","text"])] | length'` must return `0`. Graders drift from `{text, passed, evidence}` despite explicit prompts — common drifts: `description`/`assertion` instead of `text`, stray `id`/`n` fields.
- **Use [`evals/scripts/extract_subagent_usage.py`](../evals/scripts/extract_subagent_usage.py) to backfill per-run usage from subagent JSONL transcripts** — implements the `tokens` (input + output) / `cache_tokens` (creation + reads) split and emits per-agent JSON. Don't roll your own parser.
- **Before committing a new category of artifact in `evals/`** (transcripts, scratch scripts, intermediate JSON), survey what parallel skills commit — `ls evals/*/`. If no other skill keeps that artifact, don't be the first. Fix "dangling reference" findings by removing the reference, not committing the file.
- **All `run_summary.delta` values are signed strings** (`"+0.31"`, `"+835"`) — not numbers. Applies to `pass_rate` / `time_seconds` / `tokens` / `cache_tokens`. Storing as numbers breaks consumers that expect the documented schema.
- **Commit grading json selectively; don't commit raw transcripts.** Other skills (`learn` / `peer-review` / `ship-it`) commit only `evals.json` + `benchmark.{json,md}` + `fixtures/`. `pr-comments` adds selective `grading-eval{N}-{config}.json` files only where graders made judgment calls — not the full set. Transcript content goes inline as quoted `evidence` in `benchmark.json`.

## Tests And Validation

- After modifying skills or skill reference files, run:

```bash
uv run --with pytest pytest tests/
```

- Consider whether tests under `tests/<skill-name>/` need to be added or updated for behavior changes.
- Prefer test file basenames that remain unique across `tests/` subdirectories to avoid pytest import collisions when directories do not use `__init__.py`. Skill-prefixing is a recommended collision-avoidance convention (for example, `test_prhumanreview_argument_parsing.py` instead of a generic `test_argument_parsing.py`), but the key requirement is avoiding duplicate basenames. Recommended pattern: `test_<skillshortname>_<topic>.py`.
- When adding a new skill with tests, create a corresponding `.github/workflows/test-<skill-name>-skill.yml` that runs only on path changes to `skills/<skill-name>/**` and `tests/<skill-name>/**`. Use `test-learn-skill.yml` as the template — it covers `push`, `pull_request`, and `workflow_dispatch` triggers, runs `uv run --with pytest pytest tests/<skill-name>/ -v`, and uploads fixtures on failure.
- **New subdirectory CLAUDE.md format**: Use `# <Name>` as the first heading and make the first body line a brief auto-load note for that directory, following the existing pattern in `skills/CLAUDE.md` and `evals/CLAUDE.md` rather than requiring one exact sentence.
- This repo uses cspell. After editing markdown or instruction files, run `npx cspell <file>` on each modified file.
- If cspell flags a legitimate repo term, add it to `cspell.config.yaml` immediately.
- If a word is no longer used, remove it from `cspell.config.yaml` after confirming with `rg -w <word>`.
- Keep the `words` list in `cspell.config.yaml` alphabetically sorted — insert new entries in the correct alphabetical position, not at the end of the list.
- Adding a singular form to `cspell.config.yaml` does not automatically cover its plural — add both forms explicitly (e.g., `metacharacter` and `metacharacters`) if both appear in the codebase.
- Do not pipe `npx cspell` through `grep -v` — if the npm cache has an EPERM error, filtering with `grep -v "npm error"` silently swallows the failure, making it appear as "No matches found" when cspell never ran.

## Git And PR Workflow

- Never commit directly to `main`. Always create a feature branch and open a PR for review.
- Do not rewrite history on a PR that already has review comments. Avoid force-push, rebase, and `git commit --amend` on pushed commits.
- **When a PR branch has merge conflicts and rebase is forbidden** (review comments exist), run `git fetch origin && git merge origin/main` — not rebase — to resolve them.
- **`git merge` blocked by untracked files**: `git stash -u`, merge, then `git stash pop`. If pop reports "already exists" or conflicts, verify stash contents (`git stash show -p`) before `git stash drop` — pop may not have fully restored everything.
- This repo uses squash merges.
- After pushing follow-up commits or reverts to an existing PR branch, compare `git log origin/main..HEAD --oneline` against the PR title/body and update the PR description if behavior changed.
- **After pushing commits to a PR outside of a `/pr-comments` invocation**, immediately invoke the skill without asking: run `/pr-comments {pr_number}` (auto mode, the default) or `/pr-comments {pr_number} --manual` if the session is already in manual mode. **This includes when `/ship-it` creates a new PR.** Check the `anthropics/claude-code-action` workflow trigger: `on: pull_request` re-triggers on push; if it uses `on: workflow_dispatch`, first identify the workflow by searching `.github/workflows/` for `anthropics/claude-code-action` and use the matching workflow filename, or run `gh workflow list` and use the workflow name or ID it returns, then run `gh workflow run <workflow> -f pr_number={pr_number}` after the push.
- **After `/pr-comments` iterations complete, run `/pr-human-guide` before merging**: it annotates the PR for human reviewers. Do not merge until a human has reviewed — bot approval alone is not a substitute.
- **Before reporting a PR as ready to merge, verify CI status with `gh pr checks {pr_number}` — no check may be failing or pending (`"no checks reported"` counts as pass); a clean review is not a substitute.**
- After implementing or fully addressing a PR review comment, resolve the thread through the GitHub GraphQL API only when no further reviewer follow-up is needed.
- After merging a PR, sync local `main` with `git reset --hard origin/main`, but only after running `git status --porcelain` as a standalone command. If it produces any output, STOP — stash first (`git stash`), reset, then pop. Never chain `git status --porcelain && git reset --hard` — doing so bypasses the decision point and silently discards staged changes.
- **When `gh pr merge` errors locally** (e.g. uncommitted changes prevent the local branch update, or the local branch can't be checked out because it's already in use by a worktree), check `gh pr view --json state,mergedAt` — the GitHub merge may have already succeeded. If so, offer to stash uncommitted changes (`git stash`), run `git reset --hard origin/main`, then `git stash pop`.

## Command And Tooling Gotchas

- Do not hardcode `/tmp/`; use `mktemp`, `$TMPDIR`, or `${TMPDIR:-/private/tmp}`. `${TMPDIR:-/tmp}` is also a violation — the fallback must be `/private/tmp`, not `/tmp`.
- **`chmod +x` can fail on temp files in sandbox mode**: files written under `$TMPDIR` / `/private/tmp/` may be writable but still reject setting the executable bit in sandbox mode. Invoke scripts via an interpreter (e.g. `bash /path/script.sh`) instead of relying on `chmod +x`.
- **`dangerouslyDisableSandbox: true` switches `$TMPDIR`** (sandbox: `/tmp/claude-501/`, disabled: `/var/folders/.../T/`). A `${TMPDIR}/foo` reference written in one mode won't resolve in the other. Pass an absolute path matching the writer's `$TMPDIR`, or keep writer and consumer in the same mode.
- **`mktemp` X's must be last in the path component on macOS/BSD** — a suffix after the X's (e.g. `name-XXXXXX.md`) causes `mktemp` to fail or not substitute the Xs. Use `mktemp "${TMPDIR:-/private/tmp}/name-XXXXXX"` with no file-extension suffix.
- **`trap` cleanup fires at the end of each Bash tool call**: use `trap 'rm -f "$FILE"' EXIT INT TERM` immediately after `mktemp` only when that temp file is created and consumed within the same tool call. When a temp file must persist across multiple tool calls, write it to a named path (e.g. `"${TMPDIR:-/private/tmp}/name.txt"`) without a `trap` — `trap 'rm -f "$FILE"' EXIT` fires when the subshell exits at the end of each call, deleting the file before the next call runs. Clean up explicitly in a later call instead.
- If `git commit` fails because of GPG/keyring access, use `--no-gpg-sign` only as a fallback after the failure.
- In sandboxed environments, HTTPS `git push` may hang on credentials. A working pattern is:

```bash
TOKEN=$(gh auth token) && git -c "url.https://x:${TOKEN}@github.com/.insteadOf=https://github.com/" push
```

- `git push` denied as "pushing to main": branch is tracking `origin/main` (or upstream misconfigured); use `git push -u origin HEAD` to push and set the correct upstream.
- `gh api --paginate --jq` applies `--jq` per page. To deduplicate across all pages, collect pages first with `jq -s`.
- When passing shell variables into `jq`, use `jq --arg name "$value"` instead of shell string interpolation inside the filter.
- `rg` alternation uses bare `|`, not `\|`.
- In an unquoted heredoc (`<<EOF`), `\"` is a literal backslash-quote — the receiver sees `\"`, not `"`. If you need a double quote in the heredoc body, write plain `"` directly, or use `<<'EOF'` to suppress shell processing.
- **`--field 'body=...'` not `--field body="..."`**: backticks in double-quoted strings execute as shell commands (e.g. `` `git stash drop` `` dropped a real stash). For bodies with single quotes, use `'\''` or `--field body=@/path/to/file`. `--input` requires the full JSON payload, not a raw body string.
- GitHub review thread `isOutdated` means the diff location moved, not that the concern is resolved.
- **`replace_all` removing trailing text can merge the next line**: when the removed substring is the last non-whitespace content on a line, the Edit tool may collapse the following line onto the same line. Verify surrounding context after any `replace_all` that targets text at the end of a line.
- **Before `replace_all`, `rg` each occurrence — the same token may carry different meanings**: the same numeric range or identifier can appear as both an incrementable counter (a value you want to bump) and a named label pinned to specific members (a set you want anchored). Use targeted Edits when meanings diverge.
- **Inserting elements into a JSON array with Edit requires a trailing comma on the preceding element**: when replacing the closing `]` to insert new objects, the previous element's `}` must end with `,` in the replacement string. Validate after array edits: `python3 -c 'import json; json.load(open("file.json"))'`.
- **JSON files with `\uXXXX` escapes** (e.g. `benchmark.json` stores `—` as `\u2014`): Python rewrites must use `json.dump(...)` with the default `ensure_ascii=True`; `ensure_ascii=False` un-escapes all unicode and explodes the diff. Edit tool matches literal bytes, so `old_string="—"` won't match `\u2014` — use Python or escape it as `\\u2014`.
- **External CLI tools (gemini, copilot) may need network access and writable filesystem access outside a restrictive sandbox**: `gemini` needs network access to make API calls, and `copilot` may also need writable access for session-state files to avoid EPERM noise. In Claude Code, this may require enabling `dangerouslyDisableSandbox: true`; in other runtimes, use the equivalent setting that grants the needed capabilities.
- **zsh escapes `!` in double-quoted strings and jq filters**: In interactive zsh, `!` inside double-quoted strings triggers history expansion — `"<!--"` becomes `"<\!--"` and `"!="` in jq becomes `"\!="`. This silently corrupts content written to files or passed as arguments. Workarounds: use single-quoted strings (`'<!-- marker -->'`), `$'...'` ANSI quoting, or write content via Python (`subprocess` / file I/O) which bypasses shell history expansion entirely. For jq specifically: write the filter to a file and use `jq -f`, or rewrite `!=` as `(== | not)`. Skill jq snippets and any bash that emits HTML comment markers must avoid double-quoted `!`. **This also applies to any heredoc** — quoted delimiters (`<<'EOF'`, `<<'PYEOF'`) do not prevent zsh history expansion, which runs before the heredoc is constructed. Python scripts: `\\!` becomes `\!`. Plain text (GraphQL types, `<!--` markers, JSON with `!`): `!` becomes `\!` in the written file. For literal `!` in string literals (e.g. `<!--` markers), use `chr(33)` — it avoids the Write-tool approval prompt triggered when writing a temp file to `$TMPDIR`. For `!=` comparisons, rewrite as `not (a == b)`. Fall back to writing the script to a file with the Write tool when there are many such rewrites. **This also applies to `if ! cmd`** — use `cmd || { ... }` instead.
- **In a worktree, edit skills at the worktree path `skills/<name>/SKILL.md` — not via `.claude/skills/<name>/SKILL.md`**, which resolves to the main repo's copy via the symlink.
- **Git write operations in a worktree may require sandbox restrictions to be lifted**: `git add`, `git commit`, and `git push` write lock files to the main repo's `.git/worktrees/<id>/` path — outside the sandbox write allowlist that covers only `.` (the worktree directory). In Claude Code, this may require `dangerouslyDisableSandbox: true`.
- **Worktree directory outlives git registration**: `git worktree remove` unregisters the worktree but does not delete the directory. Run `rm -rf .claude/worktrees/<id>` manually afterward. Agent-isolation worktrees are locked — use `-f -f` (double `-f` overrides the lock).
- **Worktree-isolated agents must prefix Read/Edit paths with `$WT`**: Read/Edit take absolute paths, so passing `/Users/.../skills/<name>/SKILL.md` to an agent launched with `isolation: "worktree"` clobbers the main repo, not the worktree copy. In the agent's prompt, set `WT=$(git rev-parse --show-toplevel)` and require `$WT/...` prefixes. Symptom: main repo's HEAD ends up on the agent's branch.
- **`git checkout` fails on `.claude/settings.json`**: file is sandbox-blocked; use `dangerouslyDisableSandbox: true`.
- **GraphQL queries with `!` type markers cannot be passed as inline shell strings in zsh** — `String!`, `Int!`, etc. trigger history expansion and produce `UNKNOWN_CHAR` errors from `gh api graphql`. Pass the query via Python subprocess (`subprocess.run(['gh', 'api', 'graphql', '--field', 'query=' + q], check=True)`) or write it to a file and pass `--field query=@/path/to/file`. This applies to any `gh api graphql` call with typed variable declarations.
- **`gh api --jq` does not accept `--arg`**: it treats any tokens after the filter as positional args and errors with "accepts 1 arg(s), received N". To inject a shell variable into a filter across paginated results, drop `--jq` and pipe the raw paginated stream to `jq -s --arg name "$value" '[.[] | .[] | select(...)]'` — the `-s` slurps the page-stream into one array and `--arg` is safe on standalone jq.
- **`gh run view --log` cache (`~/.cache/gh/`) fails EPERM in sandbox** — prefix with `XDG_CACHE_HOME="${TMPDIR:-/private/tmp}/gh-cache"`.
- **jq bot-login exclusions need exact equality, not `contains()`**: when excluding a specific bot from a jq filter, use `.user.login == "claude[bot]"` — not `.user.login | contains("claude")`, which silently excludes unrelated bots sharing the substring (e.g. `claude-reviewer[bot]`, `claude-pr-reviewer[bot]`). This bug is easy to introduce and passes casual review; catch it by naming the exact login you mean to exclude.
- **Bash auto-backgrounds long-running commands**: don't rerun — check the prior command's output or use your environment's wait/follow mechanism to retrieve results.
- **GitHub Actions `workflow_dispatch` inputs**: never use `${{ inputs.field }}` directly in `run:` (injection risk) — pass via `env: VAR: ${{ inputs.field }}` and reference `"$VAR"`. Sanitize before using in git refs.
- **Don't `SendMessage`-retry a transient-failed `Agent` launch** — the resume path silently inherits the parent's model, not the Agent's `model:` parameter. Re-spawn instead. Verify with `message.model` in the agent's JSONL.
- **Subagent JSONL transcripts at `~/.claude/projects/.../subagents/agent-*.jsonl` record every turn's `message.model`, `message.usage`, tool blocks, and timestamps** — per-subagent time/tokens/tool_calls/errors are recoverable; parse the JSONL rather than recording them as `null`.

## Available Skills

When the user's request matches a skill's trigger phrases, read the skill file and follow its workflow exactly.

| Skill | File | Trigger phrases |
|-------|------|-----------------|
| peer-review | `skills/peer-review/SKILL.md` | "peer review", "fresh review", "another set of eyes", "sanity check", "quick review before I push", "review with Gemini/Copilot/Codex" |
| pr-human-guide | `skills/pr-human-guide/SKILL.md` | "review guide", "human review guide", "prep for review", "flag for review", "flag for human review", "add review guide" |

**Do NOT trigger** `peer-review` on bare "review" phrases like "review my changes" or "review PR N" — those route to `code-review`.

## Skill Design Guidance

- Name skills from the user's action or role, not the underlying implementation detail.
- **Prefer auto-detection with a disambiguation prompt over adding new flags** when a behavior is only needed in genuinely ambiguous situations. Handle unambiguous cases silently (e.g., only unstaged changes → auto-review with a note); prompt only when intent is unclear (e.g., both staged and unstaged → `[staged/unstaged/all]`). Explicit flags can still be offered as an escape hatch for scripting.
- Keep README / CLAUDE documentation in sync when skill changes are substantial.
- When a workflow pauses for user confirmation, make the stop explicit: tell the agent to output the prompt as its final message and stop generating until the user replies. If the workflow also has auto/manual modes, specify every confirmation gate each mode affects. If auto mode is meant to be hands-free, say explicitly whether later gates (for example push/re-request prompts) are skipped or still require confirmation.
- When listing exit conditions for a workflow loop, state that they are the only valid exit conditions and explicitly forbid subjective early exits.
- **Disjuncts and tie-breakers in classification rules are load-bearing**: in a rule like "include X only when it has a concrete risk **or** judgment call" or "when in doubt, flag only when...", each disjunct and tie-breaker is a distinct case — not a redundant adjective. Cutting one narrows classifier behavior even when the prose looks tighter.
- When a SKILL.md step does setup work (snapshot, POST, etc.) before delegating to a reference file that has its own entry/setup section covering the same actions, the delegation sentence must name the target section and list what not to re-run — otherwise agents re-enter the setup section and duplicate actions already done in SKILL.md.
- When a SKILL.md step creates a temp file with `mktemp` and uses it within the same tool call, document `trap 'rm -f "$FILE"' EXIT INT TERM` immediately after the `mktemp` call — a manual `rm -f` at the end of the block is skipped on error or interruption. When the temp file must persist across multiple tool calls, use a named path without `trap` instead (see the `trap` cleanup bullet above).
- **Repo-specific paths need portability notes**: When a skill step references a layout-specific path (e.g., `skills/*/SKILL.md`), add `(adjust prefix to match your repo's skill directory structure)` — downstream consumers with a different layout silently miss the trigger.
- Bash snippets that assign CLI output to a variable should include `2>&1` so error messages flow into the captured variable and reach fallback/error handling paths (e.g., `REVIEW_OUTPUT=$(cli ... 2>&1)`).
- `|| true` is too broad for a specific expected error — capture `resp=$(cmd 2>&1)` and `case`-match the tolerated status (e.g., `HTTP 422`); other errors still abort.
- **When capturing `git diff --quiet` exit codes**, use `VAR=0; git diff --quiet || VAR=$?` — not `git diff --quiet; VAR=$?`. In strict runners (`set -e`) the non-zero exit from "changes present" aborts the script before the assignment runs.

## Persistence

- Store durable project learnings in `CLAUDE.md`, not in per-user hidden memory directories.
- Do not write to `~/.claude/projects/.../memory/` for this project.
- Write timeless rules, not session history — do not reference specific PR numbers, dates, or session details in config rules. Those belong in commit messages.
- In "X not Y" contrasts, annotate immediately after X — trailing parentheticals read as describing Y. `` `cd dir && cmd` (skips if cd fails), not `cd dir; cmd` ``
