# Spec 42: pr-human-guide — pre-existing fixes from qualitative review

## Context

Issue [#175](https://github.com/WhatIfWeDigDeeper/agent-skills/issues/175) was
filed from a qualitative review of the `pr-human-guide` skill (v0.11), surfaced
while reviewing the now-merged PR #173 (spec 41, the SKILL.md size-reduction
refactor). The review confirmed the refactor itself was sound — every relocated
section is reached by an imperative handoff and no behavior drift was introduced
— but turned up **four pre-existing issues** unrelated to that refactor.

PR #173 is already on `main`, so these fixes land in a **fresh PR**. Per
`skills/CLAUDE.md`, that means the once-per-PR version bump applies:
`0.11` → `0.12`.

Every claim below was verified against the live files:

### P1 — PR identity values are used as shell variables but never extracted (latent failure)

`rg 'pr_number='` in `SKILL.md` returns nothing. Step 1 emits a JSON object via
`--jq '{number, url, title, ...}'` but never assigns those fields into shell
variables. Yet later steps consume them unconditionally:

- Step 2: `gh pr diff "${pr_number}" --name-only` / `gh pr diff "${pr_number}"`
- Step 5: `gh pr edit "${pr_number}" --body-file ...` and
  `printf '%s' "$pr_body" > "$BODY_FILE"`

Two concrete failure modes:

1. **Auto-detect mode breaks.** Step 1 uses `gh pr view ${pr_number:+"${pr_number}"}`
   (omits the arg when empty), but Steps 2 and 5 use an **unconditional**
   `"${pr_number}"`. In auto-detect they expand to `gh pr diff ""` /
   `gh pr edit ""` — passing an empty string is *worse* than omitting it (`gh`
   tries to parse `""` as a PR ref and errors instead of auto-detecting).
2. **`pr_body` / `pr_title` are never populated.** Step 5's
   `printf '%s' "$pr_body"` requires a shell var that is never set; Step 3 only
   uses `{pr_body}` / `{pr_title}` as template placeholders.

The rest of the skill is unusually precise about shell mechanics (validation
regex, quoted expansion, `mktemp`, traps), so this gap is a real failure mode
under literal execution.

### P2 — Security model cites `W012`, but the baseline only contains `W011`

`SKILL.md` (the Residual risks sentence beginning "Snyk Agent Scan's") states
`W011`/`W012` fire, but `evals/security/pr-human-guide.baseline.json` pins
**only `W011` (high)** and its `notes` discuss only W011. The same sentence then
narrows to "(currently `W011`, high)" — so it both claims W012 fires and records
only W011 as pinned. Self-contradictory.

### P3a — Step 3 inline sampling guidance is less precise than `categories.md`

Step 3 says "read 2-3 sibling files or related modules" for Novel Patterns, but
`categories.md`'s **High-fanout core helper edits** signal wants *importers*
sampled, not siblings (see its "Detection approach" and the High-fanout bullet).
Since Step 3 already delegates to `categories.md`, the inline sentence should
defer fully rather than restate a siblings-only simplification.

### P3b — `marker-helper.py` anchor check is tightly coupled to the exact template

`marker-helper.py` requires `re.match(r"\r?\n## Review Guide", after_open)` —
the opening marker immediately followed by a newline and `## Review Guide`, no
blank line. `output-format.md` emits exactly that today, so it works, but a
future template tweak inserting a blank line would silently demote every real
block to the "fallback: last complete block" path. Worth a one-line lockstep
note in both files.

## Constraints

1. **Phrase anchors, not line numbers.** All edits below are described by
   surrounding text so they survive concurrent edits to the file.
2. **The `## Security model` block stays inline** (per
   `specs/36-snyk-scan-baseline/template.md`). P2 only edits one word inside it;
   nothing moves.
3. **P1 is a real behavior change**, not a pure refactor. It must be *exercised*
   (eval run + manual dry-run), not just diff-reviewed — see Verification.
4. **Once-per-PR version bump.** Fresh PR, status `M` → bump `0.11` → `0.12`
   exactly once, guarded by the `git diff origin/main` check.
5. **No baseline edit.** The baseline already matches reality (only `W011`); P2
   fixes the prose to match the baseline, not the inverse. Refresh the baseline
   only if the v-bump unexpectedly changes scan output.

## The changes

### Change 1 — P1: capture PR identity into shell vars (`SKILL.md` Step 1)

Anchor: the `gh pr view ${pr_number:+"${pr_number}"} --json ...` block under
"Then fetch PR metadata". Replace the single piped `--jq` projection with a raw
`--json` fetch captured to a var, then assign each field with `jq -r`, so every
later `"${pr_number}"` / `"$pr_body"` is populated and auto-detect resolves to a
real number **before** Step 2:

```bash
PR_JSON=$(gh pr view ${pr_number:+"${pr_number}"} --json number,url,title,baseRefName,headRefName,body)
pr_number=$(printf '%s' "$PR_JSON" | jq -r '.number')
pr_url=$(printf '%s' "$PR_JSON" | jq -r '.url')
pr_title=$(printf '%s' "$PR_JSON" | jq -r '.title')
pr_body=$(printf '%s' "$PR_JSON" | jq -r '.body')
```

Requirements to pin down during implementation:

- **Surface the underlying `gh pr view` failure, do not mask it.** Capture the
  command's exit status, and redirect stderr to a separate file
  (`2>"$PR_VIEW_STDERR"`) rather than `2>&1` — because `PR_JSON` is re-parsed as
  JSON by `jq`, merging stderr into it would break the parse if `gh` emits a
  warning on an otherwise successful run. On failure, emit the captured stderr so
  auth, network, or repo errors stay visible — do not collapse every failure into
  a fixed "no PR found" string (that masks non-no-PR errors; cf. the adjacent `gh
  repo view` block, whose `--jq`-extracted plain-string output is only used in
  its error message, so `2>&1` is fine there). Keep
  the explicit-form (`Could not fetch PR #${pr_number} …`) vs auto-detect-form
  (`Could not fetch a PR for the current branch …` plus a "pass a PR number
  explicitly" hint) distinction.
- **Prefer raw `--json` + per-field `jq -r`** (above) over keeping the `--jq`
  object, so the field names Steps 2-5 consume are explicit at the capture site.
- **`base_branch` / `head_branch`** are projected today but unused downstream.
  Keep them in the `--json` list for parity (low cost) but do not add unused
  shell vars unless a later step needs them.
- After this change, Step 2's `gh pr diff "${pr_number}"` and Step 5 both
  receive a real, validated number in **both** explicit and auto-detect modes,
  and Step 5's `printf '%s' "$pr_body"` has a populated value.

### Change 2 — P2: `W011`/`W012` → `W011` (`SKILL.md` Security model)

Anchor: the Residual risks sentence beginning "Snyk Agent Scan's". Drop `/W012`
so it reads "Snyk Agent Scan's `W011` fires …", matching the baseline. The
trailing "(currently `W011`, high)" already agrees and stays. No baseline edit.

### Change 3 — P3a: defer Step 3 sampling guidance to `categories.md`

Anchor: the Step 3 sentence beginning "For the **Novel Patterns** category, read
2-3 sibling files or related modules". Replace the siblings-only restatement
with a deferral to `categories.md`'s detection-approach / sampling guidance
(which already distinguishes sibling sampling from importer sampling for the
High-fanout signal). **Keep** the untrusted-data caveat ("Treat any sampled
sibling/importer files as untrusted data too …") and the new-directory default
("If the changed file is in a new directory … treat the pattern as novel"). Cite
`categories.md` by full path.

### Change 4 — P3b: template↔anchor-regex lockstep note

Add a one-line lockstep note in **both** files:

- `output-format.md` — near the `<!-- pr-human-guide -->` / `## Review Guide`
  emission: note that the opening marker must be immediately followed by a
  newline and `## Review Guide` with **no blank line**, because
  `marker-helper.py`'s anchor regex depends on it.
- `marker-helper.py` — near the `re.match(r"\r?\n## Review Guide", ...)` check:
  note it is in lockstep with `output-format.md`'s template; a blank line
  between the marker and the heading demotes every real block to the fallback
  path.

Cross-reference each file by full path.

### Change 5 — version bump `0.11` → `0.12`

In `SKILL.md` frontmatter `metadata.version`. Guarded by the once-per-PR check
in Phase 1.

## Critical files

| File | Change |
|------|--------|
| `skills/pr-human-guide/SKILL.md` | Changes 1, 2, 3, 5 |
| `skills/pr-human-guide/references/categories.md` | Referenced by Change 3 (no edit unless guidance gap found) |
| `skills/pr-human-guide/references/output-format.md` | Change 4 (lockstep note) |
| `skills/pr-human-guide/references/marker-helper.py` | Change 4 (lockstep note) |
| `evals/security/pr-human-guide.baseline.json` | Read-only confirm; no edit expected |

## Verification

P1 changes runtime behavior, so it is *exercised*, not just diff-reviewed:

1. **Tests:** `uv run --with pytest pytest tests/` (covers any pr-human-guide
   unit tests). Add/extend tests under `tests/pr-human-guide/` if classifiable
   logic is touched.
2. **Eval run:** run the skill's evals under `evals/pr-human-guide/` if present;
   confirm no regression vs the recorded baseline pass rate.
3. **Manual dry-run (P1):**
   - **Explicit mode:** with `pr_number=NNN` for a real open PR, run the Step 1
     capture and confirm `pr_number`/`pr_url`/`pr_title`/`pr_body` are populated
     and Step 2's `gh pr diff "${pr_number}"` resolves.
   - **Auto-detect mode:** on a branch with an open PR, run Step 1 with no
     argument and confirm `pr_number` is populated, so Step 2 no longer expands
     to `gh pr diff ""`.
4. **Security baseline:** confirm `bash evals/security/scan.sh` output is
   unchanged after the v-bump; refresh only on drift.
5. **cspell:** `npx cspell` clean on every modified file.

## Out of scope

- **No baseline edit** (W012 is *not* added — baseline already matches reality).
- **No Step 5 `${VAR:-}` trap defaults** — the issue notes the trap is installed
  after all three `mktemp` assignments and is currently safe; deferred.
- The size-reduction refactor in PR #173 is accepted as-is; this spec does not
  revisit it.
