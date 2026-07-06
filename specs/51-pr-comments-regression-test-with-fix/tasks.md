# Spec 51: Tasks — pr-comments regression test with every substantive code fix

Check off each item as it completes — do not batch at the end. Use phrase
anchors (not line numbers) when editing SKILL.md / reference / test files; they
shift as edits land.

## Phase 0: Baseline & re-verification

- [x] **0.1** Re-verify current state (it drifts): confirm SKILL.md `version`
  and line count (`rg '^  version:' skills/pr-comments/SKILL.md`,
  `wc -l skills/pr-comments/SKILL.md`) and `git log --oneline -3 --
  skills/pr-comments/`. Expected at spec-write time: **v1.49, 491 lines**.
- [x] **0.2** Read all `tests/pr-comments/` files — especially `conftest.py`
  (`is_nit`, `classify_comment`) and `test_nit_gate.py` — to model the new
  predicate and test file on the existing pattern.
- [x] **0.3** Commit these spec docs (`plan.md` + `tasks.md`) on the
  implementation branch before touching SKILL.md.

---

## Phase 1: SKILL.md rule

- [x] **1.1** In **Step 8 (Apply Changes)**, immediately after the sentence
  containing "Track which thread and login correspond to each change.", insert
  the regression-test rule (~14–20 lines): applies to non-`nit`
  `fix` / `accept suggestion` rows touching executable code; **test-first / TDD
  order** — (1) write/extend the test, (2) run it and confirm it **fails** for
  the expected reason (red), (3) apply the fix, (4) confirm it **passes**
  (green); the test lands in the **same commit** (Step 10); explicitly skip
  `nit` rows and non-code changes (mirror the `nit` predicate's "no effect on
  correctness, behavior, security, performance, or public API" wording);
  sandbox/can't-run fallback still writes the test first but validates red/green
  via the available harness and notes in the commit/reply that it couldn't be
  run; frame as a strong default ("default to adding a regression test… unless
  the change is a `nit` or has no runtime surface"), not an absolute mandate.
- [x] **1.2** In **Step 7 (Present Plan and Confirm)**, specify that rows which
  will get a regression test are flagged in the plan-table `Note` column (e.g.
  `+ regression test`) — **no new column**, no separate confirmation; the
  existing `Proceed? [y/N/auto]` gate confirms the fix and its test together
  (in `--manual` mode) or rides along in auto mode. Mirror the `Nit` column's
  informational, non-gating precedent.
- [x] **1.3** In **Step 10 (Commit with Commenter Credit)**, add a one-line
  cross-reference that the regression test from Step 8 is committed here, in the
  same commit as its fix.
- [x] **1.4** Bump `metadata.version` `"1.49"` → `"1.50"`. Run
  `git diff origin/main -- skills/pr-comments/SKILL.md` first to confirm the
  version is bumped **exactly once** for this PR.

## Phase 2: Reciprocal-docs check

- [x] **2.1** Confirm the change is skill-workflow-only and needs **no**
  `CLAUDE.md` / `.github/copilot-instructions.md` mirror — the CLAUDE.md sync
  rule governs repo instruction files, not skill bodies. Record the
  determination in the PR description (no docs edit required).

## Phase 3: Tests

- [x] **3.1** Add `requires_regression_test(...)` to
  `tests/pr-comments/conftest.py`, layered on the existing `is_nit(body,
  action)`: returns True only for `fix` / `accept suggestion` that are non-nit
  **and** touch code; False for nits, non-code changes, and
  `reply` / `decline` / `skip`.
- [x] **3.2** Add `tests/pr-comments/test_regression_test_gate.py` covering:
  non-nit `fix` touching code → required; non-nit `accept suggestion` touching
  code → required; `nit`-tagged `fix` / `accept suggestion` → not required;
  non-code `fix` (docs/prose/formatting) → not required;
  `reply` / `decline` / `skip` → not required.
- [x] **3.3** Run `uv run --with pytest pytest tests/` and confirm all pass
  (lift sandbox if the uv cache errors, per CLAUDE.md). Confirm at least one new
  assertion fails if the predicate is stubbed to always-True and one if
  always-False (each test pins a distinct branch).

## Phase 4: Portability / spelling / security

- [x] **4.1** Run `npx cspell` on every changed file
  (`skills/pr-comments/SKILL.md`, the two test files, both spec files); add any
  new legitimate terms to `cspell.config.yaml` in alphabetical position.
- [x] **4.2** Confirm no security-model impact — the rule adds no new
  untrusted-content ingestion, so no `## Security model` template or
  `evals/security/` baseline refresh is needed. Record the determination.
- [x] **4.3** Confirm workflow language stays assistant-neutral (per CLAUDE.md
  Portability) — the sandbox fallback is phrased as "if the environment can't
  run the test", not Claude-Code-specific.

## Phase 5: Verification

- [x] **5.1** All `tests/pr-comments/` pass under
  `uv run --with pytest pytest tests/`.
- [x] **5.2** Read Step 6 → 7 → 8 → 10 of SKILL.md end-to-end: the Step 8 rule
  states the test-first/TDD red→green order, the Step 7 plan-table `Note` flag
  and "no separate confirmation" are present, and the Step 10 cross-reference
  reads coherently — all reusing the Step 6 `nit` predicate without redefining
  it.
- [x] **5.3** `metadata.version` is `1.50`, bumped exactly once
  (`git diff origin/main`).
