---
name: pr-comments
description: >-
  Address review comments on your own pull request: implement valid suggestions,
  reply to invalid ones, and resolve threads. Use when: user says "address PR
  comments", "implement PR feedback", "respond to review comments", "handle
  review feedback", "process PR review comments", or wants to work through open
  review threads on their pull request. Gives credit to commenters in commit messages.
license: MIT
compatibility: Requires git and GitHub CLI (gh) with authentication
metadata:
  author: Gregory Murray
  repository: github.com/whatifwedigdeeper/agent-skills
  version: "1.0"
---

# PR Review: Implement and Respond to Review Comments

Work through open PR review threads — implement valid suggestions, explain why invalid ones won't be addressed, and close the loop by resolving threads and committing with commenter credit.

## Arguments

Optional PR number (e.g. `42`). If omitted, detect from the current branch.

If `$ARGUMENTS` is `help`, `--help`, `-h`, or `?`, print usage and exit.

## Tool choice rationale

Different operations require different `gh` commands:

| Task | Command | Why |
|------|---------|-----|
| PR metadata | `gh pr view --json` | High-level; handles branch detection |
| List review comments | `gh api repos/{owner}/{repo}/pulls/{number}/comments` | REST; simpler than GraphQL for reads |
| Reply to a comment | `gh api repos/{owner}/{repo}/pulls/comments/{id}/replies` | REST; direct reply-to-comment endpoint |
| Get thread node IDs | `gh api graphql` | Thread node IDs only exist in GraphQL |
| Resolve a thread | `gh api graphql` mutation | No REST equivalent for resolution |

## Process

### 1. Identify the PR

```bash
gh pr view --json number,url,title,baseRefName,headRefName
```

If `$ARGUMENTS` is a number, pass it: `gh pr view $ARGUMENTS --json ...`. Otherwise, detect from the current branch. If no PR is found, tell the user and exit.

Also get the repo's owner/name for API calls:
```bash
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

**Ensure the working tree is on the PR's head branch.** If the current branch doesn't match `headRefName`, check it out now — otherwise file reads and edits will operate on the wrong code:

```bash
gh pr checkout <number>
```

### 2. Fetch Inline Review Comments

Pull all review comments on the PR using the REST endpoint:

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --paginate \
  --jq '.[] | {id, body, path, line, original_line, diff_hunk, in_reply_to_id, author: .user.login}' \
  | jq -s '.'
```

Filter to top-level comments only (`in_reply_to_id` is null) — replies are context, not action items. Read any reply chains to understand the full discussion thread.

### 3. Fetch Thread Resolution State

The REST API doesn't expose whether a thread is resolved. Use a focused GraphQL query to get that, along with the node IDs you'll need for resolution later:

```bash
gh api graphql -f query='
{
  repository(owner: "OWNER", name: "REPO") {
    pullRequest(number: PR_NUMBER) {
      reviewThreads(first: 100) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          comments(first: 1) {
            nodes { databaseId }
          }
        }
      }
    }
  }
}'
```

This gives you a mapping from REST `comment.id` (= `databaseId`) → GraphQL `thread.id` + `isResolved`. Discard threads that are already resolved.

If `pageInfo.hasNextPage` is true, repeat the query with `reviewThreads(first: 100, after: "END_CURSOR")` until all threads are fetched.

### 4. Read Code Context

For each unresolved thread, read the current file at the referenced path. The `diff_hunk` field shows what the reviewer saw; reading the current file shows what's there now. Both matter for your decision.

### 5. Decide: Implement or Decline

**Implement the comment if:**
- The suggestion is technically correct and would improve the code
- The referenced code still exists in its original form (thread not outdated)
- The change is within the scope of this PR
- It doesn't conflict with project conventions or other changes being made

**Decline the comment if:**
- The code has already been changed to address the concern (outdated thread)
- The suggestion is incorrect, would introduce a bug, or conflicts with project requirements
- It's a style preference that conflicts with established codebase conventions
- It's clearly out of scope (worth a follow-up issue, not this PR)
- The reviewer misunderstood the code's intent and the current approach is correct

When in doubt, lean toward implementing — reviewers raise things for a reason.

### 6. Present Plan and Confirm

Before touching anything, show the user a clear summary:

```
## PR Review Plan

### Will implement (N):
- [path:line] @username: "brief quote"
  → What you'll change

### Will decline (N):
- [path:line] @username: "brief quote"
  → Reason (this becomes your reply)

Proceed?
```

Wait for the user's go-ahead. They know the codebase and may want to override your judgment.

### 7. Implement Valid Changes

Make each code change. Group changes in the same file into a single edit pass. Keep track of which thread corresponds to which change, and which GitHub login authored each suggestion.

### 8. Commit with Commenter Credit

Stage and commit all changes. Give credit using `Co-authored-by` trailers — GitHub recognizes the noreply email format:

```
Co-authored-by: username <username@users.noreply.github.com>
```

Example commit:
```
Address PR review feedback

- Fix null check before dereferencing user object (suggested by @alice)
- Rename `tmp` to `filteredResults` for clarity (suggested by @bob)
- Extract magic number 42 to named constant MAX_RETRIES (suggested by @alice)

Co-authored-by: alice <alice@users.noreply.github.com>
Co-authored-by: bob <bob@users.noreply.github.com>
```

Deduplicate co-authors — one entry per person regardless of how many suggestions they made.

**Commit fallbacks:**
- If GPG signing fails, retry with `--no-gpg-sign`
- If heredoc fails with "can't create temp file", write the message to a temp file and use `git commit -F <file>`

### 9. Reply to Declined Comments

For each declined comment, post a reply using the replies REST endpoint:

```bash
gh api repos/{owner}/{repo}/pulls/comments/{comment_id}/replies \
  --method POST \
  --field body="Thanks for the suggestion. [Explanation of why not implementing]"
```

A good reply acknowledges the suggestion, gives a specific reason, and offers an alternative if appropriate (e.g., "I'll file a follow-up issue for this").

### 10. Resolve Implemented Threads

Resolve each thread that was addressed. Use the GraphQL node IDs captured in Step 3:

```bash
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {threadId: "THREAD_NODE_ID"}) {
    thread { isResolved }
  }
}'
```

Do not resolve declined threads — leave them open so the reviewer can see your reply and respond.

### 11. Report

```
## Done

Implemented N comments → committed <hash>
Declined N comments → replied with explanations

[List of each action taken]
```

If the branch hasn't been pushed, mention: "Run `git push` to push the commit."

## Notes

- **No sandbox**: `gh` requires macOS keyring access. Run with sandbox disabled.
- **Review threads vs. PR comments**: This skill handles inline code review threads. General PR body comments are out of scope.
- **Multiple reviewers raised the same issue**: Give all of them credit in the commit message.
- **Draft PRs**: Treat comments the same as on open PRs.
