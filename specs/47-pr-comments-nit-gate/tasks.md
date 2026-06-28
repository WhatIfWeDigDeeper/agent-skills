# Spec 47: Tasks — pr-comments nits-only halt + per-nit decision gate

Check off each item as it completes — do not batch at the end. Use phrase
anchors (not line numbers) when editing SKILL.md / reference files; they shift
as edits land.

## Phase 0: Baseline & re-verification

- [x] **0.1** Re-verify current state (it drifts): confirm SKILL.md `version`
  and line count (`rg '^  version:' skills/pr-comments/SKILL.md`,
  `wc -l skills/pr-comments/SKILL.md`) and `git log --oneline -3 --
  skills/pr-comments/`. Expected at spec-write time: **v1.47, 467 lines**.
- [x] **0.2** Read all `tests/pr-comments/` files; list every literal string /
  behavior the new edits must preserve (classification vocabulary, arg-parsing
  stickiness, all-skip repoll routing). The nit work is additive — nothing
  existing should change semantics.
- [x] **0.3** Confirm no `nit` / `nitpick` / `severity` token already exists in
  the skill, references, tests, or evals (`rg -rni 'nit|nitpick|severity'
  skills/pr-comments tests/pr-comments evals/pr-comments`) so the new tag
  introduces no collision.
- [x] **0.4** Run the pre-spec consistency review:
  ```bash
  claude -p "review staged files"
  ```
  Apply valid findings, decline invalid findings with a short reason, and rerun
  until zero valid findings or iteration cap 2.
- [x] **0.5** Record per-iteration summary inline in this task. Format:
  `Iteration N: K valid findings (X critical, Y major, Z minor). Applied all. {Brief note on themes.}`
  - Iteration 1: 2 valid findings (0 critical, 1 major, 1 minor). Applied all.
    Theme: stale baseline — skill advanced to v1.47 after this spec was drafted
    (version in 4 spots, line count in 2). Note: the review's line-count
    correction (468) was itself inaccurate — re-fixed to **467** against live
    `wc -l` (file ends in newline). The `nit`/`severity` grep is not literally
    clean (the word "nit" appears as descriptive prose in `benchmark.json`
    evidence strings and as typo substrings in eval/test files), but no severity
    *concept* or classification token exists — no collision.
  - Iteration 2: 3 valid findings (0 critical, 0 major, 3 minor). Applied all.
    Themes: (1) oversized/Step-5-flagged comments must be excluded from `nit`
    since 6d precedes Step 7; (2) the all-nits exit is a cross-reference to
    Step 6d, not a fifth peer item in bot-polling.md's post-poll checkpoint;
    (3) specified loop accounting (6d pause consumes no `--max` iteration) and
    thread state (skipped-nit reply leaves the thread open). Iteration cap (2)
    reached — stopping the review loop.
- [x] **0.6** Commit the post-review spec docs as a single commit before Phase 1
  begins.

---

## Phase 1: Classification — tag nits (Step 6)

- [x] **1.1** In SKILL.md, under the heading "### 6. Decide: Plan action", add a
  paragraph defining the `nit` tag for `fix` / `accept suggestion` rows:
  explicit markers (`nit:` / `nitpick:` / `(nit)` / `minor:` / `style:` /
  `typo:` / bot low-severity label), the semantic fallback (wording / spelling /
  naming / formatting / doc phrasing — no functional consequence), and the
  conservative bias ("when in doubt, **not** a nit"). State that `reply` /
  `decline` / `skip` / `consistency` rows are never nits, **and that an oversized
  comment (Step 5) or any Step-5-flagged comment is never a nit** (else 6d, which
  runs before Step 7, would drop Step 5's "manual review recommended" caveat).
- [x] **1.2** In the Step 7 plan table (heading "### 7. Present Plan and
  Confirm"), add a `Nit` indicator (column or a Note marker) so nits show in
  normal mixed-round plans. Update the example table accordingly.

## Phase 2: The gate (new Step 6d)

- [x] **2.1** Add a new section "### 6d. Nits-only gate" immediately after the
  "### 6c. Repoll Gate: All-Skip with Pending Bots" section. State: applies in
  auto mode only; skip when `--all`, when `--manual`, or when the plan has zero
  actionable rows (that path belongs to Step 6c). Trigger: ≥1 actionable row and
  every actionable row is `nit`.
- [x] **2.2** End Step 6d with an imperative mandatory delegation:
  "**you must now execute `references/nit-gate.md`**" — do not auto-apply, do not
  skip to Step 7 until that section's logic has been evaluated.
- [x] **2.3** Create `skills/pr-comments/references/nit-gate.md`:
  - The "## Nits-only round — your call" table format (columns: #, File, Nit,
    Marker).
  - The `Decide per nit — [fix-all / skip-all / issue-all / select]:` prompt,
    with explicit "emit as your final message and **stop generating**" discipline
    (mirror Step 7's "Confirmation prompt template").
  - Per-outcome handling: `fix-all` (route to normal fix flow → continue loop),
    `skip-all` (reply to each bot, no commit, exit loop), `issue-all` (file
    per-nit issue or offer one grouped issue, reply with link, exit loop),
    `select` (per-row fix / skip / issue; continue loop only if ≥1 fixed).
  - Point fix handling at Steps 8–13 and issue handling at the existing Step 11
    `gh issue create` flow rather than restating them.
  - State the loop & thread semantics: the 6d pause consumes no `--max`
    iteration; a resuming `fix-all` / `select`-with-fix consumes one as a normal
    fix round does; `skip-all` / `issue-all` consume none. A skipped or
    issue-deferred nit's reply **leaves the bot thread open** (do not resolve).

## Phase 3: Replies & arguments

- [x] **3.1** In `references/reply-formats.md`, add the skip-nit reply phrasing
  ("Noted as a nit — leaving as-is for now") and the issue-link reply phrasing
  ("Filed as #NNN"). Both must keep the mandatory byline footer.
- [x] **3.2** In SKILL.md Arguments section + invocation table, document `--all`
  (auto-fix every comment, disables the nits-only halt; ignored under
  `--manual`). Add a representative invocation table row.
- [x] **3.3** In `references/argument-parsing.md`, add `--all` to the token-strip
  pass (boolean, no value, non-sticky) and document its semantics under "Mode
  and cap semantics" (auto mode only; discarded under `--manual`).

## Phase 4: Exit conditions & reporting

- [x] **4.1** In `references/bot-polling.md`, reword the "**These are the ONLY
  valid reasons to exit the auto-loop. Do not exit for subjective reasons**"
  constraint to carve out the user-gated all-nits exception (agent must not
  self-decide on "minor"; an all-nits round routes to Step 6d, and the user's
  `skip-all` / `issue-all` is a valid exit). Add the all-nits exit as a
  **cross-reference**, not a fifth peer item in the numbered list — that list is
  the post-poll checkpoint, but 6d fires later (after loop-back to Step 2), so a
  peer "#5" would read as an agent-self-decided exit, the failure the constraint
  guards against.
- [x] **4.2** In `references/report-templates.md`, add a nit-gate outcome line to
  the Step 14 summary (e.g. "Nits: N fixed, N skipped, N filed as issue").

## Phase 5: Tests

- [x] **5.1** Create `tests/pr-comments/test_nit_gate.py` with `is_nit(body,
  action)` and `should_present_nit_table(rows, all_flag, manual)` (see plan.md
  "Tests"). Follow conftest/import patterns of `test_bot_poll_routing.py`.
- [x] **5.2** Extend `test_prcomments_argument_validation.py` +
  `test_pr_argument_parsing.py` for `--all` (boolean; stripped before PR-number
  validation; ignored under `--manual`).
- [x] **5.3** Run `uv run --with pytest pytest tests/` (sandbox lifted) — all
  green.

## Phase 6: Version, docs, lint

- [x] **6.1** Bump SKILL.md `version` `"1.47"` → `"1.48"` (trailing-integer
  increment, per the repo's scheme). First run
  `git fetch origin && git diff origin/main -- skills/pr-comments/SKILL.md |
  rg '^\+  version:'` to confirm no bump exists yet — once per PR.
- [x] **6.2** Update `README.md` pr-comments notes (nits-only gate + `--all`).
- [x] **6.3** Add `nit` / `nitpick` to `cspell.config.yaml` (alphabetical) if
  missing; run `npx cspell "skills/pr-comments/**/*.md" "specs/47-*/**/*.md"`.
  (Both words are already in cspell's default dictionary — no additions needed;
  in-scope markdown passes with 0 issues.)
- [x] **6.4** Verify the `.claude/skills/pr-comments` symlink still resolves.

## Phase 7: Evals (optional in this PR)

- [x] **7.1** Add an all-nits eval case and a mixed-round eval case to
  `evals/pr-comments/evals.json`. Added id 39 (`all-nits-gate-halts`) and id 40
  (`mixed-round-no-nit-gate`) — one per branch of the gate-fires/does-not-fire
  conditional.
- [x] **7.2** Note benchmark refresh as a follow-up per `evals/CLAUDE.md` (or run
  it if scope allows). Ran both new evals on Sonnet 4.6 (executor mode auto, no
  assertion leakage); graded; recorded 4 runs in `benchmark.json` (eval 39
  with 4/4, without 0/4; eval 40 with 4/4, without 3/4), bumped
  `evals_run`→[1..40] and `skill_version`→"1.48", recomputed the Sonnet by-model
  block (delta still "+0.63"), and added a provenance note. Refreshed
  `README.md` (39/40 discriminate; denominators 76→80) and `benchmark.md`
  (header counts, Summary stat, per-eval table rows, per-eval sections for
  evals 39–40). Opus 4.7 runs for evals 39–40 left as a documented pending
  follow-up.
