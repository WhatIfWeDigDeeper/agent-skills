# Spec 09: pr-comments — Auto-Repoll on All-Skip with Pending Bot Reviewers

## Problem

When the pr-comments skill runs in `--auto` mode and fetches review comments, it may classify every thread as `skip` (e.g., all threads are outdated, already replied to, or non-actionable bot summaries). The current auto-loop exit condition — "no new unresolved bot threads after poll" — treats an all-skip iteration the same as a genuinely empty poll result and exits.

However, when bot reviewers are still pending (their review hasn't landed yet), the all-skip result doesn't mean "nothing left to do" — it means "the bot's new review arrived after we fetched comments but before we finished classifying, or the bot hasn't responded yet." The skill exits, and the user must manually re-invoke it.

This was observed in practice: Copilot posted a new review after the comment list was fetched but before classification finished. All threads from the *prior* fetch were correctly skipped, but the *new* review's threads were never seen.

### Why this matters in `--auto` mode specifically

In manual mode, the user sees the all-skip plan and can re-invoke. In `--auto` mode, the expectation is hands-off operation — the skill should keep watching until bots finish reviewing, not silently exit because of a timing gap between fetch and classify.

## Proposed Change

Add a **repoll gate** between Step 6 (classification) and Step 7 (plan presentation) that detects the all-skip-with-pending-bots condition and re-fetches before exiting.

### Decision Logic

After Step 6 completes classification, before presenting the plan in Step 7:

1. **Check if all actionable items are `skip`.** Count items classified as `fix`, `accept suggestion`, `reply`, `decline`, or `consistency`. If the count is zero (every item is `skip` or there are no items at all), proceed to step 2. Otherwise, continue to Step 7 as normal.

2. **Check for pending bot reviewers.** Query the pending reviewer list:
   ```bash
   gh api repos/{owner}/{repo}/pulls/{pr_number} \
     --jq '[.requested_reviewers[] | select(.type == "Bot" or (.login | endswith("[bot]"))) | .login]'
   ```
   Also check Signal 2 (reviews API) for bots that were previously re-requested — a bot may have submitted a review (which removed it from `requested_reviewers`) but its threads arrived after our Step 2 fetch.

3. **If pending bots exist (or a bot submitted a review after our Step 2 fetch timestamp):**
   - **Auto-mode**: Log a status line and enter the polling workflow automatically:
     ```
     All threads skipped — pending bot reviewer(s) detected. Re-polling for @bot1...
     ```
     Record a new `snapshot_timestamp`, take a fresh thread snapshot, and poll using the same Signal 1 / Signal 2 logic from `references/bot-polling.md`. On new threads detected, loop back to Step 2 (not Step 6 — full re-fetch needed). This counts as a loop iteration toward the `--auto N` cap.
   - **Manual mode**: Show the all-skip plan, then offer to poll:
     ```
     All items skipped, but @bot1 hasn't finished reviewing yet. Poll for new threads? [y/N]
     ```
     If confirmed, enter the polling workflow. If declined, proceed to the report.

4. **If no pending bots and no recent bot review:** Proceed normally — present the all-skip plan and exit (or continue to Step 7 → Step 14).

### Where This Fits in the Workflow

This is a new **Step 6c** inserted between Step 6b (consistency check) and Step 7 (plan presentation). It only fires when the plan is entirely `skip` items — a narrow condition that doesn't affect the normal workflow.

The step is skipped entirely if `--auto` was not passed and the user is in their first (non-polling) iteration — in that case, the existing Step 3 early-poll logic already handles the "no comments yet" case. Step 6c specifically targets the "comments exist but are all stale/handled" scenario that Step 3 doesn't cover.

### Interaction with Existing Polling

- **Step 3 early-poll**: Handles "no comments at all + pending bots." Unchanged.
- **Step 13 bot-polling**: Handles "just pushed + re-requested bots." Unchanged.
- **New Step 6c**: Handles "comments fetched but all classified as skip + pending/recently-reviewed bots." This is the gap between the other two.

All three entry points converge on the same `references/bot-polling.md` workflow, so polling behavior is consistent.

### Fetch Timestamp Tracking

To detect whether a bot review arrived after our comment fetch, Step 2 must record a timestamp before the API call:

```bash
fetch_timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
# then fetch comments...
```

Step 6c compares this against bot review `submitted_at` values. If any bot review has `submitted_at >= fetch_timestamp`, the bot responded during or after our fetch — re-polling is warranted even if the bot is no longer in `requested_reviewers`.

### Edge Cases

- **All-skip on iteration 2+ of auto-loop**: The repoll gate applies on every iteration, not just the first. If iteration 2 produces all-skip with a pending bot, it re-polls rather than exiting.
- **Bot responded with only review-body comments (no inline threads)**: Signal 2 fires but Signal 1 doesn't. The existing bot-polling logic handles this — exit poll cleanly. Step 6c's re-fetch would pick up the review-body items via Step 2b.
- **Max iteration cap**: The repoll triggered by Step 6c counts toward the `--auto N` cap. If the cap is reached, exit with the standard max-iteration message.
- **Multiple bots, partial response**: If bot A has responded (all-skip threads) but bot B is still pending, poll for bot B only.
- **All-skip from non-bot comments**: If all threads are skip but they're from human reviewers (no pending bots), do not repoll — exit normally. The repoll gate is specifically for bot timing gaps.
- **Rapid re-poll loop prevention**: If Step 6c triggers a re-fetch and the second fetch also produces all-skip with the same pending bot, enter the standard 60-second polling loop (don't immediately re-fetch a third time). The poll interval prevents hammering the API.

## Files to Modify

| File | Change |
|------|--------|
| `skills/pr-comments/SKILL.md` | Add Step 6c (repoll gate), add `fetch_timestamp` to Step 2, update auto-loop exit conditions in `references/bot-polling.md`, update Notes section, bump version |
| `skills/pr-comments/references/bot-polling.md` | Add Step 6c as a third entry point; document the all-skip trigger |
| `evals/pr-comments/evals.json` | Add eval scenario(s) for the all-skip + pending bot case |
| `evals/pr-comments/benchmark.json` | Update after running new evals |
| `README.md` | Update pr-comments description if needed, update Eval delta |
| `tests/pr-comments/` | Add test for repoll-gate classification logic |

## Verification

- [ ] Step 6c only fires when ALL items are `skip` and pending bots exist
- [ ] Auto-mode enters polling automatically; manual mode prompts
- [ ] Re-poll loops back to Step 2 (full re-fetch), not just Step 6
- [ ] Iteration counts toward `--auto N` cap
- [ ] `fetch_timestamp` is recorded before Step 2 API calls
- [ ] Rapid re-poll prevented (falls into 60s polling on second all-skip)
- [ ] Existing Step 3 and Step 13 polling unaffected
- [ ] Tests pass: `uv run --with pytest pytest tests/pr-comments/`
- [ ] cspell clean: `npx cspell skills/pr-comments/SKILL.md`
