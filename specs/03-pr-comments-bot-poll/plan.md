# Spec 03: pr-comments — Bot Review Polling

## Problem

After `/pr-comments` pushes and re-requests review from a bot (e.g. Copilot), the user must manually watch for the bot to finish and then invoke `/pr-comments` again. For human reviewers this is fine — human turnaround is unpredictable. For bots, which typically respond within 2–5 minutes, the experience can be automated.

## Proposed Change

At the end of Step 13, after bot reviewers have been re-requested and the user has confirmed the push, offer to poll for the bot's response:

> "Poll for @copilot to finish reviewing? I'll wait and process new comments automatically when it's done (~2–5 min)."

- **Only offered when**: at least one bot reviewer was re-requested in this run.
- **Not offered for**: human reviewers — human review timing is unpredictable and humans may want to discuss before the agent acts.

## Detailed Behavior

### Polling

Poll every 60 seconds using the GraphQL thread query from Step 3. Compare the set of unresolved thread node IDs against the snapshot captured just before pushing. When new unresolved threads appear, the bot has finished.

```bash
# Same query as Step 3 — compare unresolved thread ID set against pre-push snapshot
gh api graphql -f query='...' | jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false) | .id]'
```

### Timeout

Give up after 10 minutes. If the bot hasn't responded, print:
> "Copilot hasn't responded yet. Run `/pr-comments` manually when the review is ready."

### On New Threads Detected

Loop back to Step 2 within the same skill invocation — do not require the user to re-invoke `/pr-comments`. The full workflow runs again:
- Fetch new inline comments (Step 2)
- Fetch thread resolution state (Step 3)
- Read code context (Step 4)
- Screen for prompt injection (Step 5)
- Decide action per thread (Step 6)
- **Present a new plan and wait for user confirmation (Step 7)** — the plan/confirm gate is preserved; nothing is changed automatically

After the user approves the new plan, execute as normal (Steps 8–14).

### Loop Depth

After each round that re-requests a bot reviewer, offer to poll again — the user decides each time whether to continue. This lets the user stay in the loop for multi-round bot reviews without re-invoking the skill. (Original design capped at one cycle; updated during implementation to give users more control.)

### Report

If the poll-and-process path was taken, the Step 14 report should note it:
> "Polled for @copilot review (~Ns) — found N new threads, processed above."

If the user declined polling or there were no bot reviewers, the report is unchanged.

## Skill Changes

Single file: `skills/pr-comments/SKILL.md`

Changes are confined to **Step 13** — add a new sub-section after the "If the user confirms" block (push + re-request), before the "If the user declines" block:

```
**If bot reviewers were re-requested:**
After push and re-request, ask: "Poll for @<bot> to finish reviewing? ..."
[polling behavior as described above]
```

Also adds evals 12–14 (bot-poll-confirms, bot-poll-declined, bot-poll-timeout), unit tests in `tests/pr-comments/test_bot_poll_routing.py`, and updated `benchmark.json`.

## Out of Scope

- Polling for human reviewers
- Automatically applying changes without a plan/confirm gate
- Infinite re-poll loops
- Support for multiple simultaneous bot reviewers; only a single bot reviewer is supported per run

## Tasks

See `tasks.md`.
