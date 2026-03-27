# Spec 12: pr-comments -- Add PR Timeline Comment Support (v1.14)

## Problem

The pr-comments skill (v1.13) is blind to a third category of PR feedback: plain timeline comments posted via the issue comments API (`GET .../issues/{pr}/comments`). These are top-level conversation comments not attached to any review object. A `claude[bot]` comment was missed because it was posted this way -- the skill only fetches inline review threads (Step 2) and review body comments (Step 2b).

This is a gap in coverage, not a bug in existing logic. Spec 07 explicitly scoped out timeline comments when adding review body support (v1.7). This spec brings them in.

## Design

Timeline comments share all structural properties with review body comments:
- No GraphQL thread ID (can't be "resolved")
- No file/line reference (no `diff_hunk`)
- Replies go to `POST .../issues/{pr}/comments` (same endpoint)

This means they slot into the existing architecture as a third comment source alongside inline threads and review bodies, with minimal new abstractions.

### New: Step 2c -- Fetch PR Timeline Comments

**Endpoint:** `GET repos/{owner}/{repo}/issues/{pr_number}/comments`

**Filters:**
1. Exclude PR author's own comments (not review feedback)
2. Exclude authenticated user's own comments (prior skill replies)
3. Dedup against Step 2b: if a timeline comment's author matches a review body comment's author AND their first 200 non-whitespace characters match, discard the timeline comment (keep the review body version which has review state metadata)

**Already-addressed detection:** A timeline comment is considered already addressed only if a later timeline comment (by `created_at`) from the PR author or authenticated user either (a) `@mentions` the original commenter's login, or (b) quotes their text (line starting with `>`). A plain unrelated follow-up from the PR author does not count -- without explicit mention or quote linkage, there is no reliable signal that the feedback was addressed. Comments that pass neither check flow through to Step 6 classification as normal.

### Updated steps

| Step | Change |
|------|--------|
| 3 | Exit check includes "no timeline comments from Step 2c" |
| 4 | Note: timeline comments skip this step (no file reference) |
| 5 | Security screening covers timeline comments |
| 6 | Classification broadened to "review body and timeline comments" |
| 7 | Plan table includes `*(timeline)*` source marker |
| 11 | Timeline replies use same endpoint as review body replies |
| 12 | Timeline comments skip resolve (no thread ID) |
| 13 | Timeline comment authors added to re-request list |

### Bot polling -- Signal 3

Add a third polling signal in `references/bot-polling.md`:
```bash
gh api repos/{owner}/{repo}/issues/{pr_number}/comments --paginate \
  | jq -s '[.[] | .[] | select(.user.login == "<bot_login>" and .created_at != null and .created_at >= "'"${snapshot_timestamp}"'")]'
```
Signal 3 only checks bots that are currently being polled (the same bot set as Signals 1 and 2), not all bot comments -- this avoids false positives from unrelated bots in multi-bot repos.
Captures bots that post only timeline comments without submitting a review. Also update the all-skip repoll gate (Step 6c entry) to check for bot timeline comments after `fetch_timestamp`.

### Deduplication rationale

Some bots (claude[bot], Copilot) post both a review body AND a timeline comment. The 200-char prefix match per author is conservative -- it catches near-exact duplicates without false positives on related-but-different content. If a bot posts a review body summarizing findings AND a separate timeline comment with detailed feedback, both should be processed.

## Files to modify

- `skills/pr-comments/SKILL.md` -- Steps 2c (new), 3, 4, 5, 6, 7, 11, 12, 13, tool table, frontmatter
- `skills/pr-comments/references/bot-polling.md` -- Signal 3, all-skip gate update
- `skills/pr-comments/references/report-templates.md` -- skipped-line variant for timeline comments

No changes: `references/security.md` (content-based, source-agnostic), `references/graphql-queries.md` (timeline comments have no GraphQL representation).

## New evals

### Eval 24 -- Bot timeline comment (the original bug)

A PR has a `claude[bot]` timeline comment with actionable feedback ("this function has a potential null pointer dereference") plus a review body comment from the same bot with different content (a general summary). Tests that:
- Timeline comment is fetched and visible (not invisible like before)
- Timeline and review body from same bot are not incorrectly deduped (content differs)
- Timeline comment is classified as `fix` or `reply` (not silently skipped)

### Eval 25 -- Timeline comment dedup + already-addressed

A PR has:
- A `copilot[bot]` review body AND a timeline comment with identical content (dedup test)
- A human `@alice` timeline comment with a question, followed by a later timeline comment from the PR author that `@mentions` alice (already-addressed test)

Tests that:
- Duplicate bot timeline comment is discarded (review body version kept)
- Already-addressed human comment is classified as `skip`
- Only the non-duplicate, non-addressed items appear in the plan

### Existing evals

No changes to evals 1-23. The new comment source is additive -- existing scenarios don't involve timeline comments and their behavior is unchanged.

## Test suite

Add test cases under `tests/pr-comments/` covering:
- Timeline comment filtering logic (exclude PR author, exclude authenticated user)
- Dedup logic (200-char prefix match against review bodies)
- Already-addressed detection (@mention or quote linkage required; unrelated later comment does not suppress)

## Verification

1. Run existing tests: `uv run --with pytest pytest tests/`
2. Spell check: `npx cspell skills/pr-comments/SKILL.md skills/pr-comments/references/bot-polling.md skills/pr-comments/references/report-templates.md`
3. Grep all `references/` links in SKILL.md -- verify each target exists
4. Run evals 24, 25 (with_skill + without_skill)
5. Update `evals/pr-comments/benchmark.json` with new results
6. Update `README.md` Eval delta column if pass-rate delta changes
