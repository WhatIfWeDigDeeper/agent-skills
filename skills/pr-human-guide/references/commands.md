# Shell commands and gh calls

This file holds the executable shell for SKILL.md Steps 1, 2, and 5 — the PR
metadata fetch, the diff gather, and the guide write-back. SKILL.md keeps the
decision logic (argument validation, untrusted-content framing, marker rules)
and delegates here for the commands. Execute the section a step directs you to;
do not run a section out of order.

## Fetch PR identity and repo (Step 1)

Fetch PR metadata and capture the resolved values into shell variables that
later steps consume — pass `"${pr_number}"` when explicit, omit to auto-detect
from the current branch. Capturing `.number` from the response resolves the
auto-detect case to a concrete number, so Steps 2 and 5 receive a real PR ref
instead of an empty `""`:

```bash
# Explicit PR (pr_number set): gh pr view "${pr_number}" --json ...
# Auto-detect from branch:     gh pr view --json ...
# Capture stderr to a file (not 2>&1) so a stderr warning on an otherwise
# successful run cannot corrupt the JSON the jq extractions below parse. The
# file is scoped to this block and removed inline in both branches rather than
# via an EXIT trap: a shell allows only one EXIT trap at a time, so if a later
# step in the same shell installs its own EXIT trap it would replace this one
# and leak the temp file.
PR_VIEW_STDERR=$(mktemp "${TMPDIR:-/private/tmp}/pr-human-guide-pr-view-XXXXXX")
PR_JSON=$(gh pr view ${pr_number:+"${pr_number}"} \
  --json number,url,title,baseRefName,headRefName,body 2>"$PR_VIEW_STDERR") || {
  pr_view_err=$(cat "$PR_VIEW_STDERR")
  rm -f "$PR_VIEW_STDERR"
  if [ -n "${pr_number:-}" ]; then
    echo "Could not fetch PR #${pr_number} with 'gh pr view': ${pr_view_err}" >&2
  else
    echo "Could not fetch a PR for the current branch with 'gh pr view': ${pr_view_err}" >&2
    echo "If the branch has no associated PR, pass a PR number explicitly." >&2
  fi
  exit 1
}
rm -f "$PR_VIEW_STDERR"
pr_number=$(printf '%s' "$PR_JSON" | jq -r '.number')
pr_url=$(printf '%s' "$PR_JSON" | jq -r '.url')
pr_title=$(printf '%s' "$PR_JSON" | jq -r '.title')
pr_body=$(printf '%s' "$PR_JSON" | jq -r '.body // ""')
```

The error branch above surfaces the underlying `gh pr view` failure — the stderr
written to the `$PR_VIEW_STDERR` file and read back into `pr_view_err` before the
file is removed — rather than masking every failure as a missing PR, so auth,
network, or repo errors stay visible. Capturing stderr to a file keeps stdout as
clean JSON for the `jq` extractions — `2>&1` would let a stderr warning on a
successful run break the parse.

Also capture repo owner/name:

```bash
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>&1) || {
  echo "Failed to determine repo owner/name with 'gh repo view': ${REPO}" >&2
  exit 1
}
OWNER="${REPO%%/*}"
REPO_NAME="${REPO##*/}"
```

## Gather the diff (Step 2)

Run after Step 1 has resolved `pr_number`. The changed-file list and the full
diff both feed the Step 3 category analysis.

```bash
# Step 5 re-derives this same path to give marker-helper.py the diff, which is
# what lets a reviewer's checked items survive the re-run. Keep the two
# spellings identical.
DIFF_FILE="${TMPDIR:-/private/tmp}/pr-human-guide-diff-${pr_number}.diff"
gh pr diff "${pr_number}" --name-only
gh pr diff "${pr_number}" > "$DIFF_FILE" || {
  echo "Could not fetch the diff for PR #${pr_number} with 'gh pr diff'." >&2
  exit 1
}
cat "$DIFF_FILE"
```

Store the full diff for analysis. Store the file list separately. The saved
`$DIFF_FILE` is consumed again by Step 5 and removed by its cleanup trap.

## Write the guide into the PR body (Step 5)

Write only by replacing/appending the bounded `<!-- pr-human-guide -->` block on
the detected or explicit PR via `--body-file`.

**Write the Step 4 guide block (the entire `<!-- pr-human-guide -->` …
`<!-- /pr-human-guide -->` markdown) to the guide temp file using your
file-writing tool — never route it through a double-quoted shell variable.** The
block contains `<!--`; under interactive zsh a `GUIDE_CONTENT="…<!--…"` assignment
performs history expansion on the `!`, rewriting the opening marker to `<\!--`.
GitHub then renders the marker as literal text instead of hiding the HTML comment.
Writing through the file tool bypasses the shell entirely. Use a temp path keyed
to the PR so it is stable across the two tool calls below (resolve `$TMPDIR` and
`${pr_number}` to literal values when handing the path to your file-writing tool):

```
${TMPDIR:-/private/tmp}/pr-human-guide-guide-${pr_number}.md
```

Then assemble and post the body. `marker-helper.py` is resolved from this
skill's own directory — never a fixed `skills/` prefix — so the block works for
every install layout:

```bash
# GUIDE_FILE was written above by your file-writing tool — not via the shell.
GUIDE_FILE="${TMPDIR:-/private/tmp}/pr-human-guide-guide-${pr_number}.md"
# Written by Step 2; re-derived here because shell variables do not survive
# between tool calls. marker-helper tolerates it being missing or empty — it
# warns and every item renders unchecked, which is the pre-0.16 behavior.
DIFF_FILE="${TMPDIR:-/private/tmp}/pr-human-guide-diff-${pr_number}.diff"
BODY_FILE=$(mktemp "${TMPDIR:-/private/tmp}/pr-human-guide-body-XXXXXX")
OUT_FILE=$(mktemp "${TMPDIR:-/private/tmp}/pr-human-guide-out-XXXXXX")
# One EXIT trap per shell — a second `trap ... EXIT` replaces this one and leaks
# the files it covered. Add new temp paths here rather than in another trap.
trap 'rm -f "$BODY_FILE" "$OUT_FILE" "$GUIDE_FILE" "$DIFF_FILE"' EXIT INT TERM
printf '%s' "$pr_body" > "$BODY_FILE"
# Confirm the file-writing tool actually populated the guide. A missing file
# crashes marker-helper (caught by the OUT_FILE check below), but an empty one
# does not: marker-helper would replace an existing block with "", and the
# resulting OUT_FILE is still non-empty, so the body would silently lose its
# guide and anchor markers.
[ -s "$GUIDE_FILE" ] || { echo "Guide file missing or empty ($GUIDE_FILE); write the Step 4 guide block with your file-writing tool before running marker-helper. Aborting." >&2; exit 1; }
# SKILL_DIR is the skill's base directory — the directory containing SKILL.md,
# i.e. the PARENT of the references/ directory you read this file from, not
# references/ itself (in Claude Code: the base-directory path announced above
# the skill content when the skill loads). Substitute its absolute path below;
# never hardcode a `skills/` prefix.
SKILL_DIR="${SKILL_DIR:-<absolute path of this skill's base directory, the parent of references/>}"
HELPER="$SKILL_DIR/references/marker-helper.py"
[ -f "$HELPER" ] || { echo "marker-helper.py not found at $HELPER. Set SKILL_DIR to this skill's base directory and retry." >&2; exit 1; }
# --diff-file is what enables checked-state preservation. If it is missing or
# empty the helper warns on stderr and every item renders unchecked — pass it
# unconditionally rather than building the argument list conditionally.
python3 "$HELPER" \
  --body-file "$BODY_FILE" \
  --guide-file "$GUIDE_FILE" \
  --diff-file "$DIFF_FILE" \
  --out "$OUT_FILE"
# A crashed marker-helper leaves the mktemp'd OUT_FILE empty; guard so the edit
# below does not run on it.
[ -s "$OUT_FILE" ] || { echo "marker-helper produced no output; aborting to avoid blanking the PR body." >&2; exit 1; }
# Refuse to post a marker that interactive zsh corrupted to <\!-- (the guide block
# reached the body through a double-quoted shell assignment instead of the
# file-writing tool). Patterns are single-quoted so zsh does not expand the !.
if grep -qF '<\!-- pr-human-guide' "$OUT_FILE" || grep -qF '<\!-- /pr-human-guide' "$OUT_FILE"; then
  echo 'Corrupted <\!-- pr-human-guide marker in generated body; aborting. Write the guide block to the temp file with your file-writing tool, not a double-quoted shell variable.' >&2
  exit 1
fi
gh pr edit "${pr_number}" --body-file "$OUT_FILE"
# Trap fires on shell exit and removes BODY_FILE/OUT_FILE/GUIDE_FILE/DIFF_FILE.
```

See [`skills/pr-human-guide/references/marker-helper.py`](marker-helper.py) for
selection-bounds and stray-marker handling (a smuggled fake marker cannot outlast
the replacement or shift bounds).
Never pass the body via `--body "$VAR"` — zsh corrupts `<!--` markers; always use
`--body-file`.
