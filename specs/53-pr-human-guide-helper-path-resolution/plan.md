# Spec 53 — pr-human-guide: resolve `marker-helper.py` from the skill's own directory

Closes [#206](https://github.com/WhatIfWeDigDeeper/agent-skills/issues/206).

## Problem

Step 5 of `pr-human-guide` shells out to its own bundled helper using a
**repo-root-relative** path:

```bash
python3 skills/pr-human-guide/references/marker-helper.py \
```

That path is resolved against the working directory of the Bash call. It only
exists when the skill is being run from a checkout of *this* repository, where
skills live at a root-level `skills/`. Installed skills do not live there. They
live under `.claude/skills/`, `.agents/skills/`, `~/.claude/skills/`, or a
plugin cache — none of which the relative path reaches. In any of those layouts
Step 5 dies:

```
python3: can't open file '<repo>/skills/pr-human-guide/references/marker-helper.py': [Errno 2] No such file or directory
marker-helper produced empty output; abort
```

The existing `[ -s "$OUT_FILE" ]` guard catches it, so no PR body is blanked —
the failure is loud and safe, but the run still aborts and needs a manual retry
with a corrected prefix.

## What is *not* wrong

Two plausible-sounding contributing causes were investigated and ruled out.
Recording them so the fix is not over-built:

**The sandbox is not implicated.** Reading and executing a bundled `.py` from a
user-level or plugin-cache install works under Claude Code's sandbox — filesystem
*reads* are `denyOnly` against a short list that covers neither skills nor plugin
directories. Verified directly: `python3 ~/.claude/plugins/cache/.../hooks/_base.py`
exits `0`, and `marker-helper.py --help` runs fine when invoked by absolute path.
What *is* blocked is **writing** into `~/.claude/skills`, which this skill never
does — it only reads the helper. There is one bug here, not two.

**No other skill has this defect.** A repo-wide sweep for scripts invoked by a
repo-relative `skills/…` path returns exactly one hit — the line above:

```bash
rg -n '(python3|bash|sh|node|\./)[^`]*\bskills/[a-z-]+/' skills/
```

`uv-deps` writes its severity filter to a `mktemp` path and invokes that, so it
is unaffected.

## The fix

**Resolve the helper as a sibling of the reference file that describes it.**

`marker-helper.py` and `commands.md` both live in this skill's `references/`
directory. Any assistant executing Step 5 has *just read `commands.md`* — it
therefore already knows that directory's absolute path. It does not need to
search the filesystem, consult a base-directory header format, or know the name
of any vendor directory.

```bash
# marker-helper.py sits beside this file, in this skill's references/ directory.
# SKILL_DIR is the skill's base directory — the directory containing SKILL.md,
# i.e. the PARENT of the references/ directory you read this file from, not
# references/ itself (in Claude Code: the base-directory path announced above
# the skill content when the skill loads). Substitute its absolute path below.
# It works for every install layout — project-level, user-level, plugin cache,
# or a checkout of the skills repo. Never hardcode a `skills/` prefix. A pre-set
# SKILL_DIR in the environment overrides resolution.
SKILL_DIR="${SKILL_DIR:-<absolute path of this skill's base directory, the parent of references/>}"
HELPER="$SKILL_DIR/references/marker-helper.py"
[ -f "$HELPER" ] || { echo "marker-helper.py not found at $HELPER. Set SKILL_DIR to this skill's base directory and retry." >&2; exit 1; }
python3 "$HELPER" --body-file "$BODY_FILE" --guide-file "$GUIDE_FILE" --out "$OUT_FILE"
```

Three properties make this the right shape:

- **Vendor-neutral.** No `.claude/`, `.agents/`, or `skills/` string appears
  anywhere in the resolution logic, satisfying the Portability rules in
  `CLAUDE.md`. The one Claude Code-specific detail — that the base directory is
  announced above the skill content at load time — appears only as a
  parenthetical qualifier,
  matching the established pattern at `skills/pr-human-guide/SKILL.md`
  ("The text following the skill invocation is available as `$ARGUMENTS`
  (e.g. in Claude Code: `/pr-human-guide 42`)").
- **No candidate list to go stale.** An earlier draft probed
  `$ROOT/.claude/skills`, `$ROOT/skills`, and `$HOME/.claude/skills` as
  fallbacks. That was dropped: with sibling resolution the probe's only job
  would be recovering from an assistant that cannot tell the agent where the
  file it just read lives, which cannot happen. Dropping it also keeps a
  security-reviewed file short and avoids encoding a vendor directory list that
  must track every new harness.
- **Strictly narrower execution surface than today.** The current invocation is
  cwd-relative, so a checkout that ships `skills/pr-human-guide/references/marker-helper.py`
  has that copy executed unconditionally. After this change the only path ever
  executed is the skill's own directory, unless an operator deliberately points
  `SKILL_DIR` elsewhere. Nothing repo-supplied is reachable by default.

### `SKILL_DIR` as an escape hatch

The `${SKILL_DIR:-…}` form lets a pre-set environment value win. This exists for
one concrete case: **testing the skill from a git worktree.** `.claude/skills/`
is gitignored, so a fresh worktree has no symlink into it; the assistant loads
the skill from wherever else it is installed and the helper resolves to the
**main checkout's** copy. Edits made in the worktree are silently not the code
under test. The override fixes it:

```bash
export SKILL_DIR="$(git rev-parse --show-toplevel)/skills/pr-human-guide"
```

In the main checkout no override is needed — `.claude/skills/pr-human-guide`
symlinks to `../../skills/pr-human-guide`, so the path the assistant reads
`commands.md` from lands on the working-tree copy either way.

## Prose and citation sites

The issue lists four affected locations. They are not all the same kind of
thing, and only two change.

| Site | Current | Action |
|---|---|---|
| `commands.md` — the `python3 skills/pr-human-guide/…` invocation | executable | **Replace** with the resolution block above |
| `commands.md` — "the `marker-helper.py` path is repo-root-relative — adjust the prefix…" | prose, now false | **Rewrite** to describe sibling resolution |
| `commands.md` — `See [`skills/pr-human-guide/references/marker-helper.py`](marker-helper.py)` | display text | **Leave as-is** |
| `output-format.md` — same full path in prose | display text | **Leave as-is** |

The last two are documentation pointers naming the file's location *in this
repository*, and `skills/CLAUDE.md` explicitly requires that form: "**Cite
reference files by full path** (`skills/learn/references/refactoring.md`, not
`refactoring.md`) — bare names are ambiguous outside the home skill." They were
never what executed. Changing them to `references/marker-helper.py` would fix
nothing and would require carving an exception into that rule.

## Prevention

- **Regression test** in `tests/pr-human-guide/` asserting `commands.md` carries
  no `python3 skills/pr-human-guide` invocation and does invoke `python3 "$HELPER"`.
  Matches this repo's convention of shipping a TDD regression test with every
  substantive code fix (spec 51).
- **Portability guard across the whole shipped tree.** `commands.md` carries the
  resolution logic, but any shipped file can steer a non-Claude harness toward a
  layout that does not exist for it. `TestShippedFilesArePortable` sweeps
  `SKILL.md` plus every `references/*.{md,py}` and fails if one names an install
  path (`.claude/skills`, `.agents/skills`, `~/.claude`) or mentions an assistant
  outside a `(in …)` / `(e.g. in …)` qualifier — the two forms the Portability
  rules sanction. Both assertions were confirmed to fail on an injected
  violation, not merely to pass on current content.
- **CI workflow for the suite.** Implementation surfaced that no
  `test-pr-human-guide-skill.yml` existed — the entire `tests/pr-human-guide/`
  suite (8 files, 135 tests) was never CI-gated, so the new regression test would
  not have run on a PR either. `tests/CLAUDE.md` requires adding one when a
  skill's tests change and no workflow runs them. Created from the
  `test-pr-comments-skill.yml` shape, gated on `skills/pr-human-guide/**` and
  `tests/pr-human-guide/**`.
- **`skills/CLAUDE.md` authoring rule** — never shell out to a bundled script by
  a repo-relative `skills/…` path; resolve it from the skill's own directory.
- **Root `CLAUDE.md` worktree-testing rule** — the `export SKILL_DIR=…` guidance
  above. This file is this repo's own assistant config, not distributed with the
  skill, so it may name `.claude/skills/` directly; the Portability rules
  constrain skill files only.
- Both `CLAUDE.md` edits mirror into `.github/copilot-instructions.md`, enforced
  by the `instruction-sync` CI check.
- **Audit task** re-running the `rg` sweep above at implementation time to
  confirm the single-hit result still holds.

## Security model

The change *reduces* exposure, so the Security model section in `SKILL.md` gains
one sentence rather than a new mitigation bullet: helper resolution is confined
to the skill's own directory by default, so no repo-supplied file is executed
unless an operator sets `SKILL_DIR` to one — closing the
cwd-relative behavior described above. `evals/security/pr-human-guide.baseline.json`
is refreshed in the same PR per the rule in `CLAUDE.md`; the pinned `W011`
finding is expected to be unchanged, since it fires on the presence of
`gh pr view` / `gh pr diff` regardless of mitigations.

## Out of scope

- Changing `marker-helper.py` itself. Its argument interface, marker-anchoring,
  and stray-marker handling are untouched.
- Any change to Steps 1–4 or 6.
- Restructuring how other skills invoke bundled assets — the sweep found none
  needing it. The new `skills/CLAUDE.md` rule covers future cases.

## Verification

- `uv run --with pytest pytest tests/pr-human-guide/` passes, including the new
  regression test (run with sandbox lifted — `uv run` hits a cache EPERM
  otherwise).
- `npx cspell` clean on every modified file.
- `bash evals/security/scan.sh` reports no new findings or severity escalations.
- The `rg` sweep returns zero hits after the change.
- `skills/pr-human-guide/SKILL.md` version bumped `"0.14"` → `"0.15"` — exactly
  one bump for the PR as a whole, covering SKILL.md and both reference files.
