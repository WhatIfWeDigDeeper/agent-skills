# Spec 07: pr-comments — Actionable Review Body Comments

## Problem

Review body comments (the summary text submitted alongside a review via "Request Changes" or "Comment") are currently treated as second-class citizens: they are surfaced in the plan table with action `review-body` and always marked "manual response required." The skill does nothing with them automatically.

In practice, most review body comments fall into predictable categories:

- **Bot summaries** (e.g. Copilot's PR summary) — no action needed, `skip`
- **Praise / non-actionable human feedback** (e.g. "Good job!") — no action needed, `skip`
- **Out-of-scope suggestions** (e.g. "let's file a ticket for X") — `decline` with a reply, optionally file a follow-up issue
- **Genuine questions or clarifications** — `reply`, leave open for follow-up

The current blanket "manual response required" treatment is unhelpful for the first three cases (which cover nearly all real review body comments) and forces the user to handle them manually even when the right action is obvious.

## Proposed Change

Remove the special `review-body` action type. Include review body comments in the standard Step 6 judgment flow alongside inline comments — they get classified as `fix`, `reply`, `decline`, or `skip` using the same criteria. Since most are non-actionable, most will naturally become `skip`.

Two concrete differences from inline comments that must be accounted for:

1. **No thread to resolve** — review body comments have no GraphQL thread ID, so Step 12 skips the resolveReviewThread mutation for them.
2. **Different reply endpoint** — replies go to the PR timeline via the issue comments API, not the review comment reply endpoint:
   ```bash
   gh api repos/{owner}/{repo}/issues/{pr_number}/comments \
     --method POST \
     --field body="[Your reply]"
   ```

Everything else (plan table display, co-author credit if a code change results, re-request list inclusion, follow-up issue offer for out-of-scope declines) works the same as inline comments.

## Detailed Behavior

### Step 2b — Fetch Review Body Comments (updated)

No change to the fetch logic. Remove the paragraph stating these are "informational only" and excluded from automated actions. Add a note that replies use the issue comments API endpoint.

### Step 6 — Decision Logic (updated)

Review body comments enter the same decision tree as inline comments:

- **`skip`** — bot summaries, praise, general FYI, anything with no actionable request. This will be the most common classification.
- **`reply`** — a genuine question or clarification in the review body. Post a reply via the issue comments API. Do not "resolve" (no thread exists).
- **`decline`** — an out-of-scope request, something already handled elsewhere, or a suggestion outside this PR's scope. Post a reply explaining why. Optionally offer a follow-up issue (same as inline decline flow).
- **`fix`** — rare. If the review body contains an actionable code-level request with enough context to act on, implement it. In practice, reviewers with specific code suggestions use inline comments; review bodies are rarely actionable at the code level.

The `fix` case for review body comments has no `diff_hunk` or file reference — treat it like any other ambiguous comment where you use judgment based on the review body text and your knowledge of the codebase.

### Step 7 — Plan Table (updated)

Remove `review-body` from the action values table. These items now appear with standard actions (`fix`, `reply`, `decline`, `skip`). The location column still shows `*(review body)*` since there is no file/line reference.

### Step 11 — Replies (updated)

When posting a reply to a review body comment, use the issue comments endpoint instead of the review comment reply endpoint. Add a note distinguishing the two:

- **Inline comment reply**: `POST /repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies`
- **Review body reply**: `POST /repos/{owner}/{repo}/issues/{pr_number}/comments`

### Step 12 — Thread Resolution (updated)

Skip resolveReviewThread for review body items — they have no thread node ID. Only resolve threads for inline comments.

### Step 14 — Report (updated)

Remove the `{review-body line}` from the report template. These items are now reported inline with their actual action outcomes (skipped, replied, declined).

### Notes (updated)

Update the "Review threads vs. PR comments" note to reflect that review body comments are now handled in the same workflow, with the caveat that they cannot be resolved and use a different reply endpoint.

## Invariants (unchanged)

- Security screening (Step 5) still runs on review body comment text
- `decline` items still get reply explanations
- Co-author credit only for reviewers whose feedback was implemented (same rule)
- Re-request list includes authors of actioned review body comments (same rule as inline)
- `claude[bot]` skip exception unchanged
- Auto-loop behavior unchanged

## Skill Changes

Single file: `skills/pr-comments/SKILL.md`

Changes:
- **Step 2b**: remove "informational only" paragraph; add reply endpoint note
- **Step 6**: add review body comments to the decision flow; add `skip` criteria for bot summaries and non-actionable feedback; note no `diff_hunk` context available
- **Step 7**: remove `review-body` from action values table; keep `*(review body)*` as the location placeholder
- **Step 11**: add note distinguishing the two reply endpoints; use issue comments API for review body replies
- **Step 12**: add note to skip resolveReviewThread for review body items
- **Step 14**: remove `{review-body line}` from report template; update Notes
- **Version**: 1.6 → 1.7

## New Evals

Add two new eval scenarios to `evals/pr-comments/evals.json`:

**Eval 17 — Review body: skip and decline**
Prompt: PR has two review body comments — one from Copilot (a summary of the PR, no actionable request) and one from a human reviewer suggesting the code be refactored in a follow-up ticket. One inline thread also exists with a valid fix. The skill should skip the bot summary, decline the out-of-scope refactor with a reply, implement the inline fix, and not try to resolve any review-body threads.

Assertions:
- Bot summary classified as `skip` in the plan
- Out-of-scope review body comment classified as `decline`
- A reply is posted for the declined review body comment via the issue comments API
- No resolveReviewThread call made for the review body items
- Inline thread implemented and resolved normally

**Eval 18 — Review body: reply to question**
Prompt: PR has one review body comment from a human asking a clarifying question ("Why did you choose this approach over X?"), and one inline thread with a valid fix. The skill should reply to the question (without resolving, since there's no thread), implement the inline fix, and include the question author in the re-request list.

Assertions:
- Review body question classified as `reply` in the plan
- A reply is posted via the issue comments API (not the review comment reply endpoint)
- The review body thread is NOT "resolved" (no resolveReviewThread call)
- The question author is included in the push/re-request prompt
- Inline thread implemented and resolved normally

## Out of Scope

- Handling regular PR timeline comments (`/issues/{pr_number}/comments` GET) — these are not fetched; only review-submitted body comments are in scope
- Auto-replying to bot PR summaries (Copilot, etc.) — these are `skip`, no reply posted

## Tasks

See `tasks.md`.
