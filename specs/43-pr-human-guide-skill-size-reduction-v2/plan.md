# Spec 43: pr-human-guide — extract shell/gh calls to a new reference file (size reduction v2)

## Context

`skills/pr-human-guide/SKILL.md` is **270 lines** at v0.12 on `main` — well over
the ~200-line size target for a SKILL.md body, which is loaded into context on
**every** invocation. Spec 41 brought it 275→208 by compressing prose, but two
later specs grew it back: spec 42's Step 1 PR-fetch hardening (stderr capture,
explicit/auto-detect error branches, `jq` extractions) and an expanded Step 5
(file-writing-tool guidance, an empty-guide guard, a `<\!--`-corruption rejection
grep, trap cleanup).

Unlike spec 41 (prose compression), this spec uses a single mechanism: **move the
bulky executable shell into a new reference file** and leave imperative
delegations in SKILL.md. Reference files are read only when the workflow points
to them, so relocating the command bodies is a pure context-cost saving with no
behavioral change. The rendered review-guide block written to a PR body must be
byte-identical before and after.

### Constraints

1. **Byte-identical relocation.** Every shell snippet moves verbatim — no edits
   to commands, guards, traps, or error strings. Verified by extracting the code
   fences from both files and confirming each relocated block appears unchanged
   in the original (`git show HEAD:…/SKILL.md`).
2. **Step numbering stays 1–6.** The Security-model section's `(Step 1)` /
   `(Step 3)` / `(Step 5)` references and `output-format.md`'s `Step 4` / `Step 6`
   back-references must remain valid, so no step is renumbered.
3. **Security posture unchanged.** The `## Security model` block and the
   `<untrusted_pr_content>` template stay inline in SKILL.md (they are the
   substantive W011 defense and must stay adjacent to the ingestion step). The
   Snyk W011 baseline is raised against the whole skill — the scanner already
   lists `references/output-format.md`, `references/categories.md`, and
   `marker-helper.py` as instruction sources — so relocating the `gh pr view` /
   `gh pr diff` calls into a new reference file does **not** make W011 disappear.
   No baseline edit is expected.
4. **Imperative handoffs.** Per `skills/CLAUDE.md`, each mandatory delegation to
   the new file uses "**you must now execute …**" and names the exact section —
   not a passive "see …".
5. **Phrase anchors, not line numbers** throughout these spec docs.

**Goal:** bring SKILL.md from **270 → ~185 lines** (< 200 with margin) with zero
observable behavior change.

## Design

### Move 1 — create `skills/pr-human-guide/references/commands.md`

New reference file holding the three bulky shell blocks verbatim, mirroring
`output-format.md`'s intro style (an intro paragraph naming which steps execute
it). Three sections:

- **Fetch PR identity and repo (Step 1)** — the `gh pr view … --json …` block
  with `PR_VIEW_STDERR` capture and explicit/auto-detect error branches, the
  `jq` extractions into `pr_number`/`pr_url`/`pr_title`/`pr_body`, and the
  `gh repo view` → `OWNER`/`REPO_NAME` block, plus their explanatory prose.
- **Gather the diff (Step 2)** — the two `gh pr diff "${pr_number}"` calls and
  the "store separately" note.
- **Write the guide into the PR body (Step 5)** — the file-writing-tool
  instruction + zsh-`!`-corruption rationale, the stable guide temp-path
  snippet, and the full bash assembly block (`mktemp`/`trap`, the
  `[ -s "$GUIDE_FILE" ]` empty-guide guard, the `marker-helper.py` invocation,
  the `[ -s "$OUT_FILE" ]` guard, the `<\!-- pr-human-guide` corruption-rejection
  grep, `gh pr edit --body-file`), and the "never `--body`" warning.

Author this file with the file-writing tool (not shell) so the literal `<\!--`
content is copied byte-identically without zsh history expansion.

### Move 2 — slim SKILL.md Steps 1, 2, 5

- **Step 1:** keep the help-flag check, the `^[1-9][0-9]{0,5}$` validation prose,
  and the exact `Invalid PR number:` error; replace the two bash blocks and their
  explanatory paragraphs with one imperative delegation to `commands.md`'s "Fetch
  PR identity and repo" section, naming the variables it populates.
- **Step 2:** replace the two `gh pr diff` commands with a delegation to
  `commands.md`'s "Gather the diff" section; keep the "store separately" sentence.
- **Step 5:** keep the one-line replace/append intro, the inline `<!--` →
  `<\!--` zsh rationale summary, and the passive `marker-helper.py` pointer;
  delegate the bash to `commands.md`'s "Write the guide into the PR body" section.

### Move 3 — version bump

Bump `metadata.version` `"0.12"` → `"0.13"`. This is the first SKILL.md change on
the branch (status `M`, not `A`), so the bump rule applies and the new-skill
exception does not.

## Tests

No new tests required — the existing `tests/pr-human-guide/` suite is the
regression guard. Tests assert behaviors and exact strings (help triggers,
`Invalid PR number:`, marker format, anchor regex), not line counts or step
numbers, so a byte-identical relocation should not break any. If a test asserts
on a relocated inline string, update it to assert behavior or point at the new
location — do not weaken it.

```bash
uv run --with pytest pytest tests/pr-human-guide/ -v
uv run --with pytest pytest tests/
```

## Evals

No benchmark change. This is a byte-identical relocation with zero intended
behavior change; the moved shell is unchanged, so there is nothing for an eval to
exercise differently. No new `benchmark.json` run entries, no
`metadata.skill_version` change in benchmark data.

## Files to Modify

| File | Change |
|---|---|
| `skills/pr-human-guide/references/commands.md` | **New.** Three sections holding the relocated Step 1 / Step 2 / Step 5 shell, verbatim. |
| `skills/pr-human-guide/SKILL.md` | Slim Steps 1/2/5 to imperative delegations; bump `"0.12"` → `"0.13"`. |
| `README.md` | Extend the `pr-human-guide` Eval-cost note with a v0.13 size-refactor entry. |

No changes expected in `categories.md`, `output-format.md`, `marker-helper.py`,
`evals/`, `cspell.config.yaml` (run cspell anyway), or any `CLAUDE.md` /
`.github/copilot-instructions.md` (skill content, not project rules).

## Verification

1. `wc -l skills/pr-human-guide/SKILL.md` → **< 200** (expect ~185).
2. Byte-identity: extract code fences from `commands.md` and confirm each appears
   verbatim in `git show HEAD:skills/pr-human-guide/SKILL.md`.
3. Step numbering intact: `## Security model` and `output-format.md` step
   back-references still valid (Steps still 1–6).
4. Delegations imperative: `rg -n 'references/commands.md' skills/pr-human-guide/SKILL.md`
   → three matches, each "**you must now execute …**".
5. Security model + untrusted block still inline:
   `rg -n '^## Security model|untrusted_pr_content' skills/pr-human-guide/SKILL.md`.
6. `uv run --with pytest pytest tests/pr-human-guide/ -v` and `tests/` pass.
7. `bash evals/security/scan.sh` (skips cleanly without `SNYK_TOKEN`); W011 still
   fires, no baseline edit.
8. `npx cspell skills/pr-human-guide/SKILL.md skills/pr-human-guide/references/commands.md "specs/43-*/*.md" README.md`.
9. Re-read SKILL.md, `commands.md`, and both spec files end-to-end.
10. **skill-creator review loop (≤3 iterations):** spawn a subagent invoking
    `/skill-creator` to review the refactored skill; triage findings, implement
    only valid ones (reject anything conflicting with constraints 1–4 or the
    <200-line goal), and re-run the review after any change. Stop on a clean pass
    or after 3 iterations. Record accepted/rejected per iteration in `tasks.md`.
    Re-run verification 1–6 after any file-changing iteration.

## Branch

`spec-43-pr-human-guide-skill-size-reduction-v2`

## Risks

- **Reference pointer skipped at runtime.** Moving the command bodies behind a
  reference risks the model not following the pointer. Mitigation: imperative
  "**you must now execute …**" phrasing naming the exact section; the calls are
  load-bearing and the workflow cannot proceed without the variables they set,
  which the surrounding prose makes explicit.
- **Snyk baseline drift.** No mitigation surface changes and the scanner reads
  reference files, so no W011 change is expected. If `scan.sh` reports drift,
  investigate before refreshing.
- **Accidental edit during relocation.** Mitigated by the byte-identity check
  (Verification 2).
