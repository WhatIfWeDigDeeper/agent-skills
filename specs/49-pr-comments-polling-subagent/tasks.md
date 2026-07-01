# Spec 49: Tasks — pr-comments polling subagent

Check off each item as it completes — do not batch at the end. Use phrase
anchors (not line numbers) when editing SKILL.md / reference files; they shift
as edits land. Bump `metadata.version` exactly once for the whole PR.

## Phase 0: Baseline & re-verification

- [x] **0.1** Re-verify current state (it drifts): `rg '^  version:'
  skills/pr-comments/SKILL.md`, `wc -l skills/pr-comments/SKILL.md`,
  `wc -l skills/pr-comments/references/bot-polling.md`, and
  `git log --oneline -3 -- skills/pr-comments/`. Expected at spec-write time:
  **v1.48, SKILL.md 491 lines, bot-polling.md 322 lines**.
- [x] **0.2** Read all `tests/pr-comments/` files; list every literal string /
  behavior the new edits must preserve (signal names, canonical-login rule,
  tier model, all-skip routing). This change is additive — nothing existing
  should change semantics.
- [x] **0.3** Confirm no `Tier 0` / `Polling subagent` / `VERDICT` token already
  exists in the skill, references, tests, or evals
  (`rg -rni 'tier 0|polling subagent|verdict' skills/pr-comments tests/pr-comments evals/pr-comments evals/security/pr-comments.baseline.json`)
  so the new section introduces no collision.
- [x] **0.4** Pre-spec peer review — stage only the spec docs
  (`git add specs/49-pr-comments-polling-subagent/plan.md specs/49-pr-comments-polling-subagent/tasks.md`),
  then run two independent reviewers over the staged diff:
  - **Claude** (local CLI): `claude -p "review staged files"`.
  - **Copilot**: `/peer-review specs/49-pr-comments-polling-subagent/ with Copilot`
    (needs network + session-state access — lift any sandbox restrictions; in
    Claude Code: `dangerouslyDisableSandbox: true`).

  Apply valid findings, decline invalid findings with a short reason, and rerun
  whichever reviewer still flags issues until both produce zero valid findings or
  iteration cap **3**.
  > The Claude pass already ran as the brainstorming inline self-review (caught
  > and *removed* a spurious `reinvoke_needed` verdict outcome — the no-Tier-0
  > case is decided before spawn, so it is not a verdict; the contract's three
  > outcomes are `new_threads`/`all_clean`/`timeout`) — mark that reviewer's
  > first pass complete and start Copilot fresh.
- [x] **0.5** Record a per-reviewer, per-iteration summary inline. Format:
  `{Reviewer} iteration N: K valid findings (X critical, Y major, Z minor). Applied all. {Brief note on themes.}`
  - **Claude iteration 1:** 1 valid finding (0 critical, 0 major, 1 minor).
    Applied. Removed the spurious `reinvoke_needed` 4th verdict outcome — a
    subagent that only exists when a Tier-0 primitive is present can never
    return "can't background-poll," so the no-Tier-0 case is decided pre-spawn,
    not as a verdict. Fixed across tasks.md (3.1, 4.2) and plan.md (Risks,
    Testing).
  - **Copilot iteration 1:** 2 valid findings (0 critical, 1 major, 1 minor),
    1 declined. Applied — (a) task 0.3 collision grep omitted
    `evals/security/pr-comments.baseline.json` (where the pr-comments eval
    artifact lives); added it. (b) task 0.4's `reinvoke_needed` note lacked
    traceability; clarified the term was *removed* (not renamed) and named the
    three real outcomes. Declined — plan.md Goal 3 "(Opus)" without an "in
    Claude Code:" qualifier: the spec is a design doc that uses bare
    `Opus`/`Sonnet` as shorthand throughout (diagram, Decisions); the
    portability qualifier is enforced on shipped files via task 4.1, and
    a single-spot edit would be internally inconsistent.
  - Both reviewers clean at iteration 1 (no critical/blocking findings); exited
    well under cap 3.
- [x] **0.6** Commit the post-review spec docs as a single commit before Phase 1
  begins.

---

## Phase 1: Reference — add the Polling subagent path (`bot-polling.md`)

- [x] **1.1** In the **Runtime capability check** section, add **Tier 0** above
  Tier 1: a background task that resumes the parent agent on completion is
  available (in Claude Code: a `run_in_background` Agent on a cheaper model tier,
  e.g. Sonnet) → delegate the Shared polling loop to it per the new **Polling
  subagent** section. Keep Tiers 1/2/3 verbatim as fallbacks. State that a
  runtime with **no** Tier-0 primitive never spawns the subagent and runs the
  inline Tier 1/2/3 loop instead — decided here, *before* any handoff (so
  "can't background-poll" is not a verdict outcome).
- [x] **1.2** Add a new **`## Polling subagent`** section containing:
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
- [x] **1.3** In the new section, **reference** the existing **Signals** and
  **Poll interval and timeout** subsections as the spec of what the subagent
  runs — do **not** duplicate the signal queries. State explicitly that Signal 1
  keeps priority over Signals 2/3 inside the subagent and that Signal 2/3 match
  on the **canonical** `.user.login` (never `endswith("[bot]")`).
- [x] **1.4** Confirm the inline **Signals / Poll interval and timeout / On new
  threads detected** subsections are unchanged (they remain the fallback and the
  subagent's instruction set).

---

## Phase 2: SKILL.md wiring

- [x] **2.1** Step 6c: where it delegates to the Shared polling loop, add "(or
  delegate it to the polling subagent — see `references/bot-polling.md` →
  **Polling subagent**)." Anchor on the sentence containing "All-Skip Repoll
  Gate defined in `references/bot-polling.md`".
- [x] **2.2** Step 13b: where it says "Resume the shared bot-polling flow" /
  "proceed to the Shared polling loop," add the same parenthetical delegation
  pointer. Anchor on the sentence containing "Resume the shared bot-polling
  flow".
- [x] **2.3** Verify the pre-loop work is untouched: 6c's pending/post-fetch/
  stale-HEAD checks and 13b's re-request POST + `review_requested` verification
  gate stay in the main agent (they are credentialed / classification work).
- [x] **2.4** Bump `metadata.version` in `skills/pr-comments/SKILL.md` (once).
  First run `git fetch origin && git diff origin/main -- skills/pr-comments/SKILL.md | rg '^\+  version:'`
  to confirm no bump already exists on the branch.

---

## Phase 3: Tests

- [x] **3.1** Add `tests/pr-comments/` coverage asserting the `outcome` →
  main-action mapping: each of `new_threads` / `all_clean` / `timeout` routes to
  the correct main step. Also assert the pre-spawn branch: no Tier-0 primitive →
  inline loop, no subagent.
- [x] **3.2** Add an assertion that the VERDICT contract carries **no**
  comment-body / classification / plan-row fields (the security boundary — the
  subagent returns only signal metadata).
- [x] **3.3** Run `uv run --with pytest pytest tests/` (lift sandbox if the uv
  cache errors) — all existing + new tests green.

---

## Phase 4: Portability, spelling, security

- [x] **4.1** Grep the edited files for any hardcoded universal model/tool
  requirement (`rg -n 'Sonnet|run_in_background|Agent tool' skills/pr-comments`)
  — every occurrence must carry an "in Claude Code:" qualifier or equivalent
  capability-neutral framing.
- [x] **4.2** `npx cspell "skills/pr-comments/**/*.md" "specs/49-pr-comments-polling-subagent/*.md"`
  — add any new terms to `cspell.config.yaml` in alphabetical order.
- [x] **4.3** Re-run `bash evals/security/scan.sh` for pr-comments — confirm no
  new findings (subagent adds no ingestion). Refresh the baseline in-PR only if
  findings actually change (with justification per `evals/security/CLAUDE.md`).

---

## Phase 5: Pre-ship peer review

*Fresh-context pass over the full implementation diff to catch drift. Exit
condition: a pass produces zero valid findings. Iteration cap: 3.*

- [ ] **5.1** Stage the full branch diff and run the local `claude` CLI review
  (`claude -p "review staged files"`, non-interactive). Apply valid findings;
  decline invalid with a short reason.
- [ ] **5.2** Run `/peer-review with Copilot` over the same staged diff (needs
  network + session-state access — lift any sandbox restrictions; in Claude Code:
  `dangerouslyDisableSandbox: true`). Apply valid findings; decline invalid with
  a short reason. Rerun 5.1/5.2 until both reviewers are clean or iteration cap 3.
- [ ] **5.3** Record a per-reviewer, per-iteration summary inline.

---

## Phase 6: Ship

- [ ] **6.1** Open the PR (`/ship-it` or `gh pr create`), then immediately run
  `/pr-comments {pr}` per repo workflow; loop until `claude[bot]` (and Copilot,
  if requested) are clean with no new unresolved threads.
- [ ] **6.2** Run `/learn` on the branch to capture any implementation-discovered
  gotchas into **both** `CLAUDE.md` and `.github/copilot-instructions.md` (the
  instruction-sync CI check enforces the pairing; this replaces the old manual
  copilot-instructions mirror step). Run it **here** — after the bots converge
  but before the final CI/human-guide gates — so any `/learn` commit flows
  through those gates once: if it commits, re-run `/pr-comments {pr}` and loop
  back here before proceeding to 6.3.
- [ ] **6.3** Verify CI is green with `gh pr checks {pr}` — no check failing or
  pending — **before** 6.4, so the human-review signal never fires on a red or
  in-flight build. If a final commit from 6.1/6.2 left checks running, **poll**
  until they settle (`"no checks reported"` is transient for ~60s after a push —
  re-poll before trusting it). In practice the Copilot review usually outlasts
  the checks, but repos with long-running checks need the poll.
- [ ] **6.4** Run `/pr-human-guide {pr}` to annotate the PR for human reviewers.
- [ ] **6.5** Wait for human review — bot approval alone is not a merge signal.
- [ ] **6.6** After approval, squash-merge (`gh pr merge --squash --delete-branch`)
  and sync local `main` (`git status --porcelain` → stash if dirty →
  `git pull --ff-only origin main` → pop).
