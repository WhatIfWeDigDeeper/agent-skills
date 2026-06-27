# Spec 46: Tasks — pr-comments eval-driven review-and-improve pass

Tracks issue
[#196](https://github.com/WhatIfWeDigDeeper/agent-skills/issues/196). Check off
each item as it completes — do not batch at the end.

## Phase 0: Baseline & re-verification

- [x] **0.1** Re-verify current state (it drifts): confirmed **v1.46**, 465
  lines, 38 evals. Step numbers in `plan.md` reconcile against current SKILL.md.
- [x] **0.2** Confirm benchmark baseline directly from `benchmark.json` run
  entries: `skill_version` 1.36, Opus with/without means **0.9887 / 0.5986**, 9
  non-discriminating Opus eval IDs **5, 6, 24, 27, 29, 32, 33, 35, 38**
  (computed over run entries, not prose).
- [x] **0.3** Snapshotted pre-edit `skills/pr-comments/` (v1.46) to
  `/tmp/claude-501/pr-comments-baseline-v1.46` for the without-skill arm.
- [x] **0.4** Read all four test files. Phase 1 must preserve, inside the Step 13
  section: the literal ` ```bash\n   git push\n   ``` ` block before
  "Run the canonical query"; "Run the canonical query" absent from list-building
  (text before "If `--manual` was passed"); and the strings "remote HEAD",
  "clean approval", "empty", "no commit was made in Step 10". Phase 2's `--auto
  42` row has no test dependency (`test_pr_argument_parsing.py` /
  `test_prcomments_argument_validation.py` import from conftest, don't read
  SKILL.md).

---

## Phase 1: Area 1 — Trim Step 13 redundancy

- [x] **1.1** Added a single labeled **Stale-HEAD invariant** block right after
  the five-source list in Step 13 stating once: the pre-push commenter list is
  never final; stale-HEAD bots (incl. clean-approval-only) are detected/merged at
  step 2 after any push; prompts/status-lines name the detection step and drop
  the `from @user…` clause when empty; holds even when no commit was made.
- [x] **1.2** Collapsed the per-variant restatements: removed the two lead-in
  paragraphs (folded into the invariant), the manual-prompt "pre-push
  commenter-derived set only" sentence, the auto status-line restatement clause,
  and the standalone empty-list paragraph (replaced by a one-line "per the
  stale-HEAD invariant above" pointer before the templates); trimmed the
  numbered step-2 rationale to a pointer. Net: Step 13 dropped ~3 paragraphs.
- [x] **1.3** **Decision: collapse in place** (templates NOT moved to
  `bot-polling.md`). Rationale: the templates are short and user-facing;
  `test_stale_head_ordering.py` reads the Step 13 section directly and asserts
  the `"empty"` / `"no commit was made in Step 10"` branches live there, so moving
  them out adds handoff risk for no real context savings. The invariant block
  already carries the shared reasoning the move would have justified.
- [x] **1.4** Re-ran `test_stale_head_ordering.py` + `test_push_rerequest_routing.py`
  — 16 passed, no wording changes needed (all asserted strings preserved).

---

## Phase 2: Area 2 — Finish Arguments dedup

- [x] **2.1** Confirmed `references/argument-parsing.md` still holds the full
  `--auto`/`--max` deprecation (lines 7, 16) + the dedicated "`--auto` +
  PR-number disambiguation" section with three worked examples (lines 18–24).
- [x] **2.2** Reduced the `--auto 42` **table row** to a one-line note + pointer
  below the table: "A digit token after `--auto` is read as the cap … See
  `references/argument-parsing.md` → '`--auto` + PR-number disambiguation'." No
  test depends on the row (both arg-parsing test files import from conftest and
  never read SKILL.md prose), so this is safe.
- [x] **2.3** Ran `test_pr_argument_parsing.py` +
  `test_prcomments_argument_validation.py` — 195 passed.

---

## Phase 3: Area 3 — Hunt logic gaps

- [x] **3.1** Classified each candidate against current SKILL.md + conftest:
  - [x] (a) edited/updated comment bodies across runs — **genuine miss (fixed).**
    The Step 6 previously-handled skip (SKILL.md ~line 222) keyed only on "has an
    operator reply," matched by exact login; it never compared the reviewer
    comment's `updated_at` to the reply time. A reviewer editing an
    already-replied (unresolved) thread to add new feedback would be skipped.
    Note: this only bites unresolved-but-replied threads (questions/declines) —
    fix-and-reply threads are resolved at Step 12 and discarded at Step 3, so
    they never reach Step 6.
  - [x] (b) reaction-only feedback — **intentional exclusion.** Steps 2/2b/2c read
    comment *bodies* (`jq '... {body, ...}'`); reactions carry no body and no
    request. Documented in Notes.
  - [x] (c) resolved-then-reopened threads — **already handled, no gap.** Step 3
    discards `isResolved == true` only; a reopened thread reports
    `isResolved == false` and flows through Steps 4–6 normally. No change needed.
  - [x] (d) comments on the PR description/body — **intentional exclusion.** The
    PR body is authored by the PR author (the operator), not a reviewer, and is
    not fetched by any of Steps 2/2b/2c. Documented in Notes.
  - [x] (e) human comments arriving mid-run — **accepted limitation (deferred).**
    The Step 6c repoll gate is bot-only by design: bots have an async "pending
    review in flight" signal; humans do not, so polling for a possible human
    comment would never terminate. Next invocation picks them up. Documented in
    Notes; widening deferred rather than risking a non-terminating poll.
- [x] **3.2** Added a "**Feedback boundaries**" Notes bullet covering (b) reactions
  and (d) PR-body, plus a "**Human comments arriving mid-run**" Notes bullet for
  (e). No behavioral change for these three.
- [x] **3.3** Genuine miss (a) fixed minimally: added an **edited-after-reply
  exception** sentence to the Step 6 previously-handled skip — re-plan when the
  comment's `updated_at` is newer than the latest operator reply. Self-terminating
  (the fresh reply's timestamp then exceeds `updated_at`), so no loop risk. (e)'s
  repoll-widening was scoped as large/risky (non-termination) and deferred per the
  task's own escape hatch.
- [x] **3.4** Added `tests/pr-comments/test_previously_handled_skip.py` (7 cases)
  plus the `is_previously_handled` conftest helper. No new eval added: the fix is
  classifiable unit-logic with no observable executor-output change beyond the
  skip/re-plan boundary, and eval *runs* are deferred this pass (Phase 4). Full
  suite: 428 passed.

---

## Phase 4: Area 4 — Refresh benchmark

> **DEFERRED per user decision ("Edits now, defer eval run").** Only the 4.4
> methodology note is prepped this pass (added as a "Pending refresh" blockquote
> in `benchmark.md`). The actual 76-run re-evaluation (4.1–4.3) is a follow-up.

- [ ] **4.1** _(deferred)_ Re-run all 38 evals — with_skill (current skill) vs the Phase 0.3
  snapshot baseline — on Opus 4.7 executor / Sonnet 4.6 analyzer (to stay
  comparable with the recorded run); grade and aggregate per `evals/CLAUDE.md`.
- [ ] **4.2** _(deferred)_ Re-evaluate the 9 non-discriminating evals (5, 6, 24, 27, 29, 32,
  33, 35, 38): for each, leave as-is / strengthen assertions / note why it stays
  non-discriminating. Record decisions in `benchmark.md`.
- [ ] **4.3** _(deferred)_ Update `benchmark.json` to the new `skill_version`, run entries,
  `run_summary`, and `run_summary_by_model`. Rewrite via `json.dump(...,
  ensure_ascii=True)` to preserve `\uXXXX` escapes (root CLAUDE.md note).
- [x] **4.4** **Methodology note added** (the only Phase 4 item done this pass).
  Added a "Pending refresh — `without_skill` arm redefinition (spec 46)"
  blockquote to `benchmark.md` right after the **Skill version** line: it states
  the refresh will redefine `without_skill` from the v1.36 true no-skill baseline
  (59.9%, delta **+39 pts** on Opus) to the pre-edit v-current snapshot (task
  0.3), so the refreshed near-zero delta reads as a *changed measurement, not a
  regression*. Prose rate/framing updates (problem-statement, non-discriminating
  notes) wait for the deferred re-run. _(No `benchmark.json` change — no new runs
  produced, so `skill_version` stays v1.36 per `evals/CLAUDE.md`.)_

---

## Phase 5: Version, security, docs

- [x] **5.1** Bumped `metadata.version` **1.46 → 1.47** (patch; the (a) fix is a
  behavior change + doc additions). `git diff origin/main` confirms exactly one
  `+  version:` line on the branch.
- [x] **5.2** **No README change.** The edited-after-reply exception is an
  internal skip-boundary refinement that doesn't alter the high-level pr-comments
  row description, and the Eval Δ stays as-recorded (eval re-run deferred, Phase
  4). Nothing in the row needs updating.
- [x] **5.3** **Skipped (no ingestion path changed).** Steps 2/2b/2c fetch
  commands are untouched; the Step 6 edit is decision/classification prose that
  reads an already-fetched `updated_at` field — it adds no new fetch or
  untrusted-content surface. Per the task's "Otherwise skip," the security
  baseline is not refreshed.

---

## Phase 6: Cspell + consistency

- [x] **6.1** Ran cspell on SKILL.md + all references + spec files — **13 files,
  0 issues**. No wordlist additions needed.
- [x] **6.2** Re-read SKILL.md end-to-end — Step 13 stale-HEAD invariant stated
  once (line ~365) with prompts/status-lines pointing back to it; Step 6
  edited-after-reply exception reads cleanly; the two new Notes bullets
  (Feedback boundaries, Human comments mid-run) are consistent; version 1.47;
  step numbering intact; no dangling cross-references.
- [x] **6.3** Re-read `plan.md` and `tasks.md` end-to-end — consistent. plan.md
  carries the original full Area 4 benchmark-refresh design; tasks.md records the
  user's deferral of the eval re-run. No contradiction (plan = design intent,
  tasks = execution log).

---

## Phase 7: Verification

- [x] **7.1** `uv run --with pytest pytest tests/pr-comments/` — **428 passed**
  (includes the 7 new `test_previously_handled_skip.py` cases).
- [x] **7.2** `uv run --with pytest pytest tests/` — **1154 passed**, no
  regressions (4 pre-existing pytest deprecation warnings, unrelated).
- [ ] **7.3** _(deferred with Phase 4)_ Benchmark with_skill ≥ v1.36 baseline —
  no new eval run this pass, so nothing to confirm; verified at the deferred
  re-run.
- [x] **7.4** `git diff origin/main -- skills/pr-comments/SKILL.md |
  rg '^\+  version:'` — exactly one bump (`+  version: "1.47"`).
