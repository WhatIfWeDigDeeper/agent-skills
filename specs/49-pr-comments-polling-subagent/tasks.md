# Spec 49: Tasks — pr-comments polling subagent

Check off each item as it completes — do not batch at the end. Use phrase
anchors (not line numbers) when editing SKILL.md / reference files; they shift
as edits land. Bump `metadata.version` exactly once for the whole PR.

## Phase 0: Baseline & re-verification

- [ ] **0.1** Re-verify current state (it drifts): `rg '^  version:'
  skills/pr-comments/SKILL.md`, `wc -l skills/pr-comments/SKILL.md`,
  `wc -l skills/pr-comments/references/bot-polling.md`, and
  `git log --oneline -3 -- skills/pr-comments/`. Expected at spec-write time:
  **v1.48, SKILL.md 491 lines, bot-polling.md 322 lines**.
- [ ] **0.2** Read all `tests/pr-comments/` files; list every literal string /
  behavior the new edits must preserve (signal names, canonical-login rule,
  tier model, all-skip routing). This change is additive — nothing existing
  should change semantics.
- [ ] **0.3** Confirm no `Tier 0` / `Polling subagent` / `VERDICT` token already
  exists in the skill, references, tests, or evals
  (`rg -rni 'tier 0|polling subagent|verdict' skills/pr-comments tests/pr-comments evals/pr-comments`)
  so the new section introduces no collision.
- [ ] **0.4** Run the pre-spec consistency review. Stage only the spec docs
  (`git add specs/49-pr-comments-polling-subagent/plan.md specs/49-pr-comments-polling-subagent/tasks.md`),
  then:
  ```bash
  claude -p "review staged files"
  ```
  Apply valid findings, decline invalid findings with a short reason, and rerun
  until zero valid findings or iteration cap 2.
- [ ] **0.5** Record per-iteration summary inline in this task. Format:
  `Iteration N: K valid findings (X critical, Y major, Z minor). Applied all. {Brief note on themes.}`
- [ ] **0.6** Commit the post-review spec docs as a single commit before Phase 1
  begins.

---

## Phase 1: Reference — add the Polling subagent path (`bot-polling.md`)

- [ ] **1.1** In the **Runtime capability check** section, add **Tier 0** above
  Tier 1: a background task that resumes the parent agent on completion is
  available (in Claude Code: a `run_in_background` Agent on a cheaper model tier,
  e.g. Sonnet) → delegate the Shared polling loop to it per the new **Polling
  subagent** section. Keep Tiers 1/2/3 verbatim as fallbacks. State that a
  runtime with **no** Tier-0 primitive never spawns the subagent and runs the
  inline Tier 1/2/3 loop instead — decided here, *before* any handoff (so
  "can't background-poll" is not a verdict outcome).
- [ ] **1.2** Add a new **`## Polling subagent`** section containing:
  - the **IN-state** table (owner/repo/pr_number, `snapshot_timestamp`,
    `unresolved_thread_ids[]`, canonical `bot_logins[]`, `poll_interval_secs`,
    `timeout_secs`, `mode`) with each field's source and purpose;
  - the **VERDICT** JSON contract (`outcome` ∈ {`new_threads`, `all_clean`,
    `timeout`}, `new_unresolved_thread_ids`, `bots_with_new_review`,
    `bots_pending`, `signal_fired`, `polled_seconds`, `note`);
  - the **read-only constraint** (only `gh api` reads + `jq`; no writes; no
    comment bodies / classifications / plan rows in the output);
  - the **model note** (cheaper tier, in Claude Code: Sonnet; suggestion, not a
    universal requirement);
  - the **outcome → main-action** mapping (`new_threads` → loop back to Step 2
    and re-screen; `all_clean` → Step 14 clean-exit note; `timeout` → Step 14
    re-invoke message).
- [ ] **1.3** In the new section, **reference** the existing **Signals** and
  **Poll interval and timeout** subsections as the spec of what the subagent
  runs — do **not** duplicate the signal queries. State explicitly that Signal 1
  keeps priority over Signals 2/3 inside the subagent and that Signal 2/3 match
  on the **canonical** `.user.login` (never `endswith("[bot]")`).
- [ ] **1.4** Confirm the inline **Signals / Poll interval and timeout / On new
  threads detected** subsections are unchanged (they remain the fallback and the
  subagent's instruction set).

---

## Phase 2: SKILL.md wiring

- [ ] **2.1** Step 6c: where it delegates to the Shared polling loop, add "(or
  delegate it to the polling subagent — see `references/bot-polling.md` →
  **Polling subagent**)." Anchor on the sentence containing "All-Skip Repoll
  Gate defined in `references/bot-polling.md`".
- [ ] **2.2** Step 13b: where it says "Resume the shared bot-polling flow" /
  "proceed to the Shared polling loop," add the same parenthetical delegation
  pointer. Anchor on the sentence containing "Resume the shared bot-polling
  flow".
- [ ] **2.3** Verify the pre-loop work is untouched: 6c's pending/post-fetch/
  stale-HEAD checks and 13b's re-request POST + `review_requested` verification
  gate stay in the main agent (they are credentialed / classification work).
- [ ] **2.4** Bump `metadata.version` in `skills/pr-comments/SKILL.md` (once).
  First run `git fetch origin && git diff origin/main -- skills/pr-comments/SKILL.md | rg '^\+  version:'`
  to confirm no bump already exists on the branch.

---

## Phase 3: Tests

- [ ] **3.1** Add `tests/pr-comments/` coverage asserting the `outcome` →
  main-action mapping: each of `new_threads` / `all_clean` / `timeout` routes to
  the correct main step. Also assert the pre-spawn branch: no Tier-0 primitive →
  inline loop, no subagent.
- [ ] **3.2** Add an assertion that the VERDICT contract carries **no**
  comment-body / classification / plan-row fields (the security boundary — the
  subagent returns only signal metadata).
- [ ] **3.3** Run `uv run --with pytest pytest tests/` (lift sandbox if the uv
  cache errors) — all existing + new tests green.

---

## Phase 4: Portability, spelling, security

- [ ] **4.1** Grep the edited files for any hardcoded universal model/tool
  requirement (`rg -n 'Sonnet|run_in_background|Agent tool' skills/pr-comments`)
  — every occurrence must carry an "in Claude Code:" qualifier or equivalent
  capability-neutral framing.
- [ ] **4.2** `npx cspell "skills/pr-comments/**/*.md" "specs/49-pr-comments-polling-subagent/*.md"`
  — add any new terms to `cspell.config.yaml` in alphabetical order.
- [ ] **4.3** Re-run `bash evals/security/scan.sh` for pr-comments — confirm no
  new findings (subagent adds no ingestion). Refresh the baseline in-PR only if
  findings actually change (with justification per `evals/security/CLAUDE.md`).

---

## Phase 5: Pre-ship peer review

- [ ] **5.1** Stage the full diff and run the local `claude` CLI review
  (`claude -p "review staged files"`, non-interactive). Apply valid findings;
  decline invalid with a reason; cap at 2 iterations.
- [ ] **5.2** Mirror any CLAUDE.md rule changes into
  `.github/copilot-instructions.md` (instruction-sync CI check). This spec is not
  expected to add CLAUDE.md rules, but confirm.

---

## Phase 6: Ship

- [ ] **6.1** Open the PR (`/ship-it` or `gh pr create`), then immediately run
  `/pr-comments {pr}` per repo workflow; address `claude[bot]` review.
- [ ] **6.2** Before reporting ready for human review, run `/pr-human-guide`.
- [ ] **6.3** Verify CI green (`gh pr checks {pr}`) before merge-ready.
