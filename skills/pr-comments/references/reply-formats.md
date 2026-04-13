# Reply Formats by Comment Type

Use the correct endpoint and body format based on the comment type being replied to.

**Shell quoting safety**: Always use single-quoted strings for `--field body='...'` — never double-quoted. Backticks inside double-quoted shell strings trigger command substitution (e.g. `` `git stash drop` `` executes, dropping a stash). If the reply body contains single quotes, escape them as `'\''` or write the body to a temp file and use `--input`.

## Byline

Append this footer to **every** reply body (inline, review body, and timeline). Substitute your assistant's name and URL:

```
---
🤖 Generated with [AssistantName](url)
```

For example, Claude Code uses `[Claude Code](https://claude.com/claude-code)`.

## Inline comment (Step 2)

Use the review comment replies endpoint:

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies \
  --method POST \
  --field 'body=[Your reply]

---
🤖 Generated with [AssistantName](url)'
```

## Review body comment (Step 2b)

Use the issue comments endpoint (replies go to the PR timeline):

```bash
gh api repos/{owner}/{repo}/issues/{pr_number}/comments \
  --method POST \
  --field 'body=[Your reply]

---
🤖 Generated with [AssistantName](url)'
```

## Timeline comment (Step 2c)

Use the same issue comments endpoint. **The reply body must start with `@{commenter_login}` and include a `>` quote of the relevant excerpt**, since the timeline is flat and has no thread nesting. Do not post a bare reply without the `@mention` and quote — the commenter will not be notified and there will be no context linking your reply to their comment.

Required format:
```
@{commenter_login}
> [relevant excerpt from their comment]

[Your response]

---
🤖 Generated with [AssistantName](url)
```

```bash
gh api repos/{owner}/{repo}/issues/{pr_number}/comments \
  --method POST \
  --field 'body=@{commenter_login}
> [relevant excerpt]

[Your response]

---
🤖 Generated with [AssistantName](url)'
```
