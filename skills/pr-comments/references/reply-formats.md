# Reply Formats by Comment Type

Use the correct endpoint and body format based on the comment type being replied to.

## Inline comment (Step 2)

Use the review comment replies endpoint:

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies \
  --method POST \
  --field body="[Your reply]"
```

## Review body comment (Step 2b)

Use the issue comments endpoint (replies go to the PR timeline):

```bash
gh api repos/{owner}/{repo}/issues/{pr_number}/comments \
  --method POST \
  --field body="[Your reply]"
```

## Timeline comment (Step 2c)

Use the same issue comments endpoint. **The reply body must start with `@{commenter_login}` and include a `>` quote of the relevant excerpt**, since the timeline is flat and has no thread nesting. Do not post a bare reply without the `@mention` and quote — the commenter will not be notified and there will be no context linking your reply to their comment.

Required format:
```
@{commenter_login}
> [relevant excerpt from their comment]

[Your response]
```

```bash
gh api repos/{owner}/{repo}/issues/{pr_number}/comments \
  --method POST \
  --field body="@{commenter_login}
> [relevant excerpt]

[Your response]"
```
