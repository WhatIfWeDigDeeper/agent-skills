# Tasks: Spec 09 — pr-comments Auto-Repoll on All-Skip

## Implementation

### Task 1: Add fetch timestamp to Step 2

**File:** `skills/pr-comments/SKILL.md`

- Before the `gh api repos/{owner}/{repo}/pulls/{pr_number}/comments` call in Step 2, add a `fetch_timestamp` capture:
  ```bash
  fetch_timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  ```
- Add a note: "Record `fetch_timestamp` before fetching — Step 6c uses it to detect bot reviews that arrived during or after the fetch."

### Task 2: Add Step 6c — Repoll Gate

**File:** `skills/pr-comments/SKILL.md`

Insert a new `### 6c. Repoll Gate: All-Skip with Pending Bots` section between Step 6b and Step 7. Contents:

- **Trigger condition**: After Step 6b, count items classified as `fix`, `accept suggestion`, `reply`, `decline`, or `consistency`. If count is zero (all `skip` or empty plan), proceed with the gate. Otherwise skip Step 6c entirely.
- **Pending bot check**: Query `requested_reviewers` for bots (same query as Step 3's early-poll check). Also query reviews API for any bot review with `submitted_at >= fetch_timestamp` (from Step 2) — this catches bots that submitted after our fetch but are no longer in `requested_reviewers`.
- **Post-fetch review detected**: If the reviews API shows a bot review with `submitted_at >= fetch_timestamp`, immediately loop back to Step 2 (full re-fetch) — do not enter polling. The bot's threads may already exist and polling's snapshot would miss them. Counts as one iteration toward `--auto N` cap.
- **Pending bots only (no post-fetch review)**: Enter polling. Auto-mode: log status line (`All threads skipped — pending bot reviewer(s) detected. Polling for @bot1...`), set `snapshot_timestamp = fetch_timestamp`, take fresh thread snapshot, enter polling workflow per `references/bot-polling.md`. On new threads, loop back to Step 2. Counts as one iteration toward `--auto N` cap.
- **Manual-mode behavior**: Show the all-skip plan, then prompt: `All items skipped, but @bot1 hasn't finished reviewing yet. Poll for new threads? [y/N]`. If confirmed, enter polling. If declined, proceed to report.
- **Rapid re-poll guard**: If this is the second consecutive all-skip result for the same bot(s), do not immediately re-fetch — fall into the standard 60-second polling loop from `references/bot-polling.md`.
- **No pending bots**: Skip this step, continue to Step 7 as normal.

### Task 3: Update bot-polling.md with Step 6c entry point

**File:** `skills/pr-comments/references/bot-polling.md`

- Add Step 6c to the entry point list at the top:
  ```
  - **Step 6c** — when all fetched threads are classified as `skip` but bot reviewers are pending or recently submitted
  ```
- In the "Polling behavior" section, add a note about `snapshot_timestamp` for the Step 6c entry: "When entering from Step 6c, follow the same `snapshot_timestamp` rules as in the main polling flow: reuse `fetch_timestamp` from Step 2 when appropriate, or record a new `snapshot_timestamp` just before starting to poll. The thread snapshot may be non-empty — use the current unresolved thread IDs as the baseline."
- In the "On new threads detected" section, confirm that Step 6c follows the same loop-back-to-Step-2 behavior as the other entry points.

### Task 4: Update auto-loop exit conditions

**File:** `skills/pr-comments/references/bot-polling.md`

- In the auto-loop exit conditions list, update condition 1 from:
  ```
  No new unresolved bot threads after poll → exit loop
  ```
  to:
  ```
  No new unresolved bot threads after poll AND no pending bot reviewers remain → exit loop
  ```
  This ensures the exit condition aligns with the new repoll gate — we don't exit if bots are still pending.

### Task 5: Update Notes section

**File:** `skills/pr-comments/SKILL.md`

- Add a note about the repoll gate:
  ```
  - **All-skip repoll**: When all fetched threads are classified as `skip` but bot reviewers
    are still pending (or submitted a review after the comment fetch), the skill re-polls
    rather than exiting. This prevents a timing gap where a bot posts a review between the
    comment fetch and classification from causing the skill to exit prematurely. In auto-mode,
    re-polling is automatic; in manual mode, the user is prompted.
  ```

### Task 6: Bump version

**File:** `skills/pr-comments/SKILL.md`

- Bump `metadata.version` from `"1.10"` to `"1.11"`
- First check: `git diff main -- skills/pr-comments/SKILL.md | grep '^+.*version'` — only bump if no bump already exists on this branch

### Task 7: Add test for repoll gate logic

**File:** `tests/pr-comments/test_bot_poll_routing.py` (or new file if cleaner)

- Add a `TestRepollGate` class with cases:
  - All-skip + pending bot → should enter polling
  - All-skip + no pending bot → should exit normally
  - All-skip + bot submitted after fetch_timestamp → should enter polling
  - Mixed actions (some fix, some skip) + pending bot → should NOT enter polling (normal flow)
  - Second consecutive all-skip for same bot → should use 60s polling interval (not immediate re-fetch)

### Task 8: Add eval scenario

**File:** `evals/pr-comments/evals.json`

- Add eval 23: "All-skip with pending bot reviewer — auto-repoll"
  - **Setup**: PR with one bot reviewer pending. Existing threads are all outdated or already replied to. Bot review arrives during/after fetch.
  - **Expected with skill**: Detects all-skip + pending bot, enters repoll, processes new threads when they arrive.
  - **Expected without skill**: Exits after seeing all-skip, misses the bot's new review.

### Task 9: Run evals and update benchmarks

**Files:** `evals/pr-comments/benchmark.json`, `evals/pr-comments/benchmark.md`, `README.md`

- Run eval 23 with_skill and without_skill
- Update `benchmark.json` with new run entries
- Update `benchmark.md` with analysis
- Update `README.md` Eval delta column if it changes

## Verification

- [ ] Run `uv run --with pytest pytest tests/pr-comments/` — all tests pass
- [ ] Run `npx cspell skills/pr-comments/SKILL.md skills/pr-comments/references/bot-polling.md`
- [ ] Verify Step 6c only triggers on all-skip (not partial-skip)
- [ ] Verify `fetch_timestamp` is recorded before Step 2 API calls
- [ ] Verify auto-mode enters polling without prompting
- [ ] Verify manual mode prompts before polling
- [ ] Verify iteration counts toward `--auto N` cap
- [ ] Verify existing Step 3 and Step 13 entry points unchanged
