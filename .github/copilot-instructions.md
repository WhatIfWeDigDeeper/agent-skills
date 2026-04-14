# Copilot Instructions

**Keep `CLAUDE.md` in sync**: whenever you add, update, or remove a rule in this file, apply the equivalent change to `CLAUDE.md`. The two files serve different assistants (Copilot vs. Claude Code) but should encode the same project conventions. When running `/learn` in this project, always update **both** `CLAUDE.md` and `.github/copilot-instructions.md` without asking which to update.

## Project Overview

This repository contains reusable agent skills for Claude Code and other coding assistants. Skills are defined in `skills/<skill-name>/SKILL.md`. Development artifacts live separately:

- `evals/<skill-name>/`: eval cases, benchmark data, and benchmark docs
- `tests/<skill-name>/`: unit tests for classifiable logic

**Subdirectory instruction files**: `skills/CLAUDE.md` (skill format, version bumping, design patterns) and `evals/CLAUDE.md` (benchmarking rules) contain detailed guidance for those areas — refer to them when working in those directories.
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

## Tests And Validation

- After modifying skills or skill reference files, run:

```bash
uv run --with pytest pytest tests/
```

- Consider whether tests under `tests/<skill-name>/` need to be added or updated for behavior changes.
- Prefer test file basenames that remain unique across `tests/` subdirectories to avoid pytest import collisions when directories do not use `__init__.py`. Skill-prefixing is a recommended collision-avoidance convention (for example, `test_prhumanreview_argument_parsing.py` instead of a generic `test_argument_parsing.py`), but the key requirement is avoiding duplicate basenames. Recommended pattern: `test_<skillshortname>_<topic>.py`.
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
- After pushing follow-up commits to an existing PR branch, compare `git log origin/main..HEAD --oneline` against the PR title/body and update the PR description if behavior changed.
- After implementing or fully addressing a PR review comment, resolve the thread through the GitHub GraphQL API only when no further reviewer follow-up is needed.
- After merging a PR, sync local `main` with `git reset --hard origin/main`, but only after running `git status --porcelain` as a standalone command. If it produces any output, STOP — stash first (`git stash`), reset, then pop. Never chain `git status --porcelain && git reset --hard` — doing so bypasses the decision point and silently discards staged changes.
- **When `gh pr merge` errors locally** (e.g. uncommitted changes prevent the local branch update, or the local branch can't be checked out because it's already in use by a worktree), check `gh pr view --json state,mergedAt` — the GitHub merge may have already succeeded. If so, offer to stash uncommitted changes (`git stash`), run `git reset --hard origin/main`, then `git stash pop`.

## Command And Tooling Gotchas

- Do not hardcode `/tmp/`; use `mktemp`, `$TMPDIR`, or `${TMPDIR:-/private/tmp}`. `${TMPDIR:-/tmp}` is also a violation — the fallback must be `/private/tmp`, not `/tmp`.
- **`mktemp` X's must be last in the path component on macOS/BSD** — a suffix after the X's (e.g. `name-XXXXXX.md`) causes `mktemp` to fail or not substitute the Xs. Use `mktemp "${TMPDIR:-/private/tmp}/name-XXXXXX"` with no file-extension suffix.
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
- **`--field 'body=...'` not `--field body="..."`**: backticks in double-quoted strings execute as shell commands (e.g. `` `git stash drop` `` dropped a real stash). For bodies with single quotes, use `'\''` or `--field body=@/path/to/file`. `--input` requires the full JSON payload, not a raw body string.
- GitHub review thread `isOutdated` means the diff location moved, not that the concern is resolved.
- **`replace_all` removing trailing text can merge the next line**: when the removed substring is the last non-whitespace content on a line, the Edit tool may collapse the following line onto the same line. Verify surrounding context after any `replace_all` that targets text at the end of a line.
- **Inserting elements into a JSON array with Edit requires a trailing comma on the preceding element**: when replacing the closing `]` to insert new objects, the previous element's `}` must end with `,` in the replacement string. Validate after array edits: `python3 -c 'import json; json.load(open("file.json"))'`.
- **External CLI tools (gemini, copilot) may need network access and writable filesystem access outside a restrictive sandbox**: `gemini` needs network access to make API calls, and `copilot` may also need writable access for session-state files to avoid EPERM noise. In Claude Code, this may require enabling `dangerouslyDisableSandbox: true`; in other runtimes, use the equivalent setting that grants the needed capabilities.
- **zsh escapes `!` in double-quoted strings and jq filters**: In interactive zsh, `!` inside double-quoted strings triggers history expansion — `"<!--"` becomes `"<\!--"` and `"!="` in jq becomes `"\!="`. This silently corrupts content written to files or passed as arguments. Workarounds: use single-quoted strings (`'<!-- marker -->'`), `$'...'` ANSI quoting, or write content via Python (`subprocess` / file I/O) which bypasses shell history expansion entirely. For jq specifically: write the filter to a file and use `jq -f`, or rewrite `!=` as `(== | not)`. Skill jq snippets and any bash that emits HTML comment markers must avoid double-quoted `!`. **This also applies to Python scripts passed via `<<'PYEOF'` heredoc** — `\\!` in the heredoc body may still reach Python as `\!`, causing strings to contain a literal backslash instead of `<!--`. Prefer `chr(33)` for `!` in the script body — it avoids the Write-tool approval prompt triggered when writing a temp file to `$TMPDIR`. Fall back to writing the script to a file only when `chr(33)` would be unwieldy.
- **In a worktree, edit skills at the worktree path `skills/<name>/SKILL.md` — not via `.claude/skills/<name>/SKILL.md`**, which resolves to the main repo's copy via the symlink.
- **Git write operations in a worktree may require sandbox restrictions to be lifted**: `git add`, `git commit`, and `git push` write lock files to the main repo's `.git/worktrees/<id>/` path — outside the sandbox write allowlist that covers only `.` (the worktree directory). In Claude Code, this may require `dangerouslyDisableSandbox: true`.
- **`git checkout` fails on `.claude/settings.json`**: file is sandbox-blocked; use `dangerouslyDisableSandbox: true`.
- **GraphQL queries with `!` type markers cannot be passed as inline shell strings in zsh** — `String!`, `Int!`, etc. trigger history expansion and produce `UNKNOWN_CHAR` errors from `gh api graphql`. Pass the query via Python subprocess (`subprocess.run(['gh', 'api', 'graphql', '--field', 'query=' + q], check=True)`) or write it to a file and pass `--field query=@/path/to/file`. This applies to any `gh api graphql` call with typed variable declarations.
- **jq bot-login exclusions need exact equality, not `contains()`**: when excluding a specific bot from a jq filter, use `.user.login == "claude[bot]"` — not `.user.login | contains("claude")`, which silently excludes unrelated bots sharing the substring (e.g. `claude-reviewer[bot]`, `claude-pr-reviewer[bot]`). This bug is easy to introduce and passes casual review; catch it by naming the exact login you mean to exclude.
- **Bash auto-backgrounds long-running commands**: don't rerun — check the prior command's output or use your environment's wait/follow mechanism to retrieve results.

## Available Skills

When the user's request matches a skill's trigger phrases, read the skill file and follow its workflow exactly.

| Skill | File | Trigger phrases |
|-------|------|-----------------|
| peer-review | `skills/peer-review/SKILL.md` | "peer review", "fresh review", "another set of eyes", "sanity check", "quick review before I push", "review with Gemini/Copilot/Codex" |
| pr-human-guide | `skills/pr-human-guide/SKILL.md` | "review guide", "human review guide", "prep for review", "flag for review", "flag for human review", "add review guide" |

**Do NOT trigger** `peer-review` on bare "review" phrases like "review my changes" or "review PR N" — those route to `code-review`.

## Persistence

- Store durable project learnings in `CLAUDE.md`, not in per-user hidden memory directories.
- Do not write to `~/.claude/projects/.../memory/` for this project.
- Write timeless rules, not session history — do not reference specific PR numbers, dates, or session details in config rules. Those belong in commit messages.
- In "X not Y" contrasts, annotate immediately after X — trailing parentheticals read as describing Y. `` `cd dir && cmd` (skips if cd fails), not `cd dir; cmd` ``
