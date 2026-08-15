# Spec 56 — pr-human-guide: preserve checked guide items when the anchored content is unchanged

Closes [#221](https://github.com/WhatIfWeDigDeeper/agent-skills/issues/221).

## Problem

`marker-helper.py::update_body` replaces the whole `<!-- pr-human-guide -->` block on
every run:

```python
return before + guide + after
```

The new `guide` is rendered fresh by Step 4, and every item in it is rendered
`- [ ]`. So every box a human reviewer ticked is wiped. `SKILL.md`'s Notes section
documents this as intended behaviour:

> **Idempotency**: Any `- [x]` items checked by reviewers are reset to `- [ ]` on re-run — checked state is not preserved.

Content *outside* the block already round-trips correctly — `update_body` preserves
`before` and `after` verbatim and only strips stray duplicate markers. The reset is
confined to guide items inside the block.

This is only a papercut on a one-shot run. It is not a papercut in a repo whose
conventions run `/pr-human-guide` after **every** `/pr-comments` iteration — the
arrangement this repo's own root `CLAUDE.md` mandates:

> **The moment you would report a PR as ready for or waiting on human review, automatically run `/pr-human-guide` first — without asking.**

On an active PR that is many passes, each one wiping the reviewer's progress,
including for entries whose underlying code never changed. The reviewer either
re-does the work or stops trusting the checkboxes. The second outcome is worse,
because it degrades the guide into decoration.

## Why word-for-word matching is the wrong fix

The obvious repair — carry `- [x]` across when the item's text is unchanged — is
unsound, and would ship a bug worse than the one it fixes.

A rendered entry is `path + line range + prose reason`:

```
- [ ] [`src/auth/middleware.ts` (L42-67)](link) — New token validation logic
```

None of those three change when the code *inside* `L42-67` is rewritten. A
reviewer who ticked that box read the old token validation; text matching would
carry their tick onto a rewrite they have never seen. That is a false assurance
in exactly the situation the guide exists to prevent — silence about a security
change, presented as a completed review.

So preservation must key on the **anchored content**, not on the entry text: a
tick survives a re-render and never survives a rewrite.

## Correction to the issue text

Issue #221 proposes hashing "the anchored hunk's content" and notes:

> The skill already computes a SHA-256 diff anchor for the permalink URLs, so the input is on hand.

It does not. `references/output-format.md` computes:

```bash
ANCHOR=$(printf '%s' "path/to/file" | ... sha256sum ... | cut -d' ' -f1)
```

That hashes the **file path only** — it is GitHub's own `#diff-<sha256-of-path>`
fragment scheme. It is constant for the life of the file and carries no content
whatsoever, so it cannot detect a rewrite. A content hash has to be introduced.
This spec introduces one; the path anchor is left exactly as it is, and the two
are deliberately unrelated.

## Design

### Two phases: the model renders a placeholder, the helper resolves it

Identity is carried in an HTML comment on the item's own line. Rendering (Step 4,
done by the model) emits a **placeholder** that restates values the model already
has. Write-back (Step 5, done by `marker-helper.py`) resolves it to a hash.

Rendered by Step 4:

```
- [ ] [`src/auth/middleware.ts` (L42-67)](link) — New token validation logic <!-- pr-human-guide:item lines=42-67 path=src/auth/middleware.ts -->
```

Posted to the PR body by Step 5:

```
- [ ] [`src/auth/middleware.ts` (L42-67)](link) — New token validation logic <!-- pr-human-guide:id 9f2c41ab77e0d3b5 -->
```

The division of labour is the point. The model never computes a hash, never runs
a per-item shell command, and has nothing it could fabricate — a wrong `path=` or
`lines=` yields no id and the item simply renders unchecked. The hash is computed
in Python from the `gh pr diff` output, which makes it fully unit-testable without
a parallel reimplementation in the test suite.

### Hash definition

`sha256(heading + "\n" + path + "\n" + selected_diff_lines)`, first 16 hex chars.

- **heading** — the enclosing `### Category` line. Without it, the same file+range
  filed under two categories would share one identity, and ticking one would tick
  the other.
- **selected lines** — taken from the unified-diff section whose `+++ b/<path>`
  matches. Walk the hunks tracking the new-side cursor from `@@ … +c,d @@`; include
  each body line **with its `+` / `-` / space prefix** while the cursor sits inside
  `[start, end]`. Advance the cursor on context and `+` lines only, so `-` lines
  deleted inside the range are captured — a pure deletion inside a flagged range
  must change the identity. Skip `\ No newline at end of file`. With no line range
  (whole-file entry), take every body line for that path.
- **Line numbers are deliberately excluded from the hash.** An unrelated insertion
  above the range shifts `L42-67` to `L50-75` while leaving the content
  byte-identical, and the reviewer's tick should survive that. This is the
  feature's whole value and the property most worth verifying by hand.

Hunk bodies are consumed by decrementing the old-side and new-side counts from the
`@@` header rather than by pattern-guessing where a hunk ends. This is what makes a
diff body line that happens to begin `+++ ` or `--- ` (adding a line of text that
starts with dashes) parse as content instead of as a file header.

### Ordering inside `update_body`

All of it happens in one function, in this order, because the previous block's text
is only addressable once `_find_replacement_bounds` has returned:

```python
def update_body(body: str, guide: str, diff_text: str | None = None) -> str:
    bounds = _find_replacement_bounds(body)
    guide = resolve_item_placeholders(guide, diff_text)   # always — append path too
    if bounds is not None:
        start, end = bounds
        checked = collect_checked_ids(body[start:end])    # previous canonical block ONLY
        guide = apply_checked(guide, checked)
    ... splice exactly as today
```

Two details that must not slip:

- `collect_checked_ids` receives `body[start:end]`, never `body`. The signature is
  what enforces "reads the previous canonical block only" — not a regex that happens
  to be scoped. A tick smuggled into the surrounding body text must not reach the
  new guide.
- Placeholder resolution runs on the **append** path too. Otherwise the first run on
  a PR with no existing block ships raw `:item` placeholders into the PR body.

### Checkbox syntax tolerance

When a reviewer clicks a checkbox in the GitHub UI, GitHub rewrites the line. It
accepts and may emit `- [X]` as well as `- [x]`, and list items can carry leading
indentation. Collection therefore matches `[xX]` with tolerant leading whitespace,
and the flip preserves whatever indentation it matched. Getting this wrong fails
silently — the feature simply never works for UI-clicked boxes, which is every real
use.

### Everything unknown resets

Missing placeholder, unparsable placeholder, `path` absent from the diff, no
previous block, an id not present in the previous block, a block written by an
older skill version, any content change — every one of these falls through to
`- [ ]`. Today's behaviour is the failure mode, so a bug anywhere in this path
degrades to the status quo rather than misleading a reviewer.

Any `pr-human-guide:id` comment already present in the freshly rendered guide is
stripped before placeholders are resolved, so the only identities in the posted
body are ones the helper computed from the diff on this run.

### Security model

The change adds one `## Security model` bullet to `SKILL.md`:

> - **Checked-state preservation is content-keyed and body-independent** — on re-run
>   the helper reads the previous canonical block only, extracts identity hashes
>   matching `^[0-9a-f]{16}$` from `- [x]` lines (capped at 500), and carries across a
>   single boolean per hash; no text from the untrusted body reaches the new guide.
>   Hashes are recomputed by the helper from the `gh pr diff` output, never read from
>   the body, so a forged identity cannot make a check survive a content change.
>   Preservation grants no capability a body editor lacks — anyone able to edit the PR
>   body can already type `- [x]` (Step 5).

The threat worth stating plainly: the PR body is attacker-influenced input. What
crosses from it into the new guide is a set of 16-hex-character strings, used only
as set membership against hashes the helper computed itself this run. No body text
is copied. The worst an attacker who can edit the body can achieve is pre-ticking a
box — which they can already do directly, since they can edit the body.

## Scope

**In scope:** per-item identity, checked-state preservation inside the marker
block, the narrowed Notes rule, tests, one new eval, and a security-baseline
refresh.

**Out of scope:** checkbox state *outside* the marker block (already round-trips
correctly — issue #221 says so explicitly), and any change to the path-only
`#diff-` permalink anchor.

## Files changed

| File | Change |
|------|--------|
| `skills/pr-human-guide/references/marker-helper.py` | All new logic: `compute_item_id`, `resolve_item_placeholders`, `collect_checked_ids`, `apply_checked`, `diff_text` threading, optional `--diff-file` |
| `skills/pr-human-guide/references/output-format.md` | Placeholder in the entry template and the with-items example; new "Per-item identity comment" subsection |
| `skills/pr-human-guide/references/commands.md` | Step 2 saves the diff to a temp file; Step 5 passes `--diff-file` and extends the existing single `trap` |
| `skills/pr-human-guide/SKILL.md` | Version `0.15` → `0.16`; new Security-model bullet; Step 4/5 mentions; rewritten Notes bullet |
| `tests/pr-human-guide/test_item_identity.py` | New — hashing and placeholder resolution |
| `tests/pr-human-guide/test_marker_helper.py` | New preservation cases |
| `tests/pr-human-guide/test_helper_path_resolution.py` | Assert `commands.md` passes `--diff-file` |
| `tests/pr-human-guide/conftest.py` | One comment recording that preservation is helper-only by design |
| `evals/pr-human-guide/evals.json` | New eval 15 `preserves-checked-unchanged-items` |
| `evals/pr-human-guide/benchmark.json`, `benchmark.md`, `README.md` | Recorded runs, summary stats, Eval Δ, Eval cost |
| `evals/security/pr-human-guide.baseline.json` | Refreshed in the same PR |

Deliberately **not** changed:

- The `## Review Guide` anchor line in `output-format.md`. Four sites depend on its
  exact shape (`marker-helper.py`'s `re.match(r"\r?\n## Review Guide", …)`, the
  lockstep comment above it, the lockstep note in `output-format.md`, and
  `tests/pr-human-guide/conftest.py::_select_guide_bounds`).
- `SKILL.md`'s `compatibility:` line. `sha256sum`/`shasum` are still required for the
  path-only `#diff-` anchor even though the item hash is computed in Python.
- `docs/imgs/pr_human_guide_flow.svg`. No new step is added, and its Step 2 labels
  name the `gh pr diff` commands rather than their destinations.
- `tests/pr-human-guide/conftest.py`'s placement logic. It already carries a parallel
  copy of the helper's block selection that has drifted (`> next_start` where the
  helper uses `>= next_open`), acknowledged in `test_marker_helper.py`'s docstring.
  Adding a second parallel copy for preservation would make that worse; the
  preservation tests import the shipped helper directly.

## Verification

1. `uv run --with pytest pytest tests/pr-human-guide/ -v`, then the full `tests/`
   suite. Both need sandbox restrictions lifted (cache EPERM), and so does
   `git push`, because the `pre-push` hook runs pytest.
2. `python3 -c 'import json; json.load(open("evals/pr-human-guide/benchmark.json"))'`
   after the benchmark edits, plus the expectation-key schema check from
   `evals/CLAUDE.md`:
   `jq '[.runs[] | .expectations[] | select((. | keys) != ["evidence","passed","text"])] | length'`
   must return `0`.
3. `npx cspell` on every changed `.md`, adding new terms to `cspell.config.yaml` in
   alphabetical position.
4. `bash evals/security/scan.sh` reports no findings beyond the pinned `W011`.
5. **End-to-end on a live PR** — the check that matters, since no unit test
   exercises the model:
   - run the skill, tick a box in the GitHub UI, re-run → the tick survives and the
     `:id` comment round-trips;
   - push a commit editing the flagged range, re-run → that item alone resets while
     an untouched item stays ticked;
   - push a commit inserting lines *above* a flagged range, re-run → the tick
     survives the renumbering.
6. Per repo convention, `/pr-comments` runs immediately after the PR is pushed, and
   `/pr-human-guide` before the PR is reported ready for human review — the latter
   doubles as a live dogfood of this change.
