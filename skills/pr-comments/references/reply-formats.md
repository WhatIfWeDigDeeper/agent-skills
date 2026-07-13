# Reply Formats by Comment Type

**Shell quoting safety**: Always use single-quoted strings for `--field body='...'` — never double-quoted. Backticks inside double-quoted shell strings trigger command substitution (e.g. `` `git stash drop` `` executes, dropping a stash). If the reply body contains single quotes, escape them as `'\''` or write the body to a temp file and pass `--field body=@/path/to/file`. If you use `--input`, the file must contain the full JSON payload (e.g. `{"body":"..."}`), not just the raw body.

## Byline

Append this footer to **every** reply body (inline, review body, and timeline). Substitute your assistant's name and URL:

```
---
🤖 Generated with [AssistantName](url)
```

For example, Claude Code uses `[Claude Code](https://claude.com/claude-code)`.

## Referring to the commenter — `{commenter_ref}`

Every body this skill posts to GitHub — inline reply, review-body reply, timeline
reply, nit skip/defer reply, commit message, follow-up issue — refers to a
commenter as `{commenter_ref}`:

| Commenter | `{commenter_ref}` | Example |
|---|---|---|
| Human | `@` + login | `@alice` |
| Bot | bare display handle, **no `@`** | `Copilot`, `claude`, `renovate` |

**A bot is any comment author with `user.type == "Bot"`.** Do not test for a
`[bot]` login suffix instead — the same bot reports different logins on different
endpoints (Copilot is `Copilot` on `/pulls/{pr_number}/comments` but
`copilot-pull-request-reviewer[bot]` on `/pulls/{pr_number}/reviews`), so a
suffix-only check misses it exactly where it matters. Derive the display handle
with the **Bot Display Names** algorithm in `references/bot-polling.md` (strip
`[bot]`; if hyphens remain, keep the first hyphen-separated token).

**Why the asymmetry.** On a human, `@login` is a notification — on the flat PR
timeline it is the only thing that tells them you replied. On a bot, `@login` is
a **command**: prefixing a bot's login with `@` in a PR comment dispatches its
coding agent (for Copilot, this starts it pushing its own commits to the PR).
Never emit a live `@`-mention of a bot in posted content.

**This binds your own prose, not just the templates below.** Do not `@`-mention
a bot's login in the free-form part of a reply, a commit message, or an issue
body — use the bare display handle instead. For example, never write: "Good
catch, @Copilot" <!-- bot-mention-example --> — that live `@`-mention dispatches
Copilot's coding agent instead of crediting it. Write "Good catch, Copilot" or
"as Copilot noted" instead.

Terminal output — status lines, confirmation prompts, the plan table — is never
posted to GitHub and is unaffected; it keeps using `@bot1`.

## Nit replies (Step 6d nits-only gate)

When the Step 6d gate resolves a nit by **skipping** or **deferring to an
issue**, reply to the originating bot comment with the byline footer, using the
endpoint **and format** that match where the nit originated: an inline (Step 2)
nit via the inline replies endpoint below; a review-body (Step 2b) or timeline
(Step 2c) nit via the issue comments endpoint, with a **timeline** reply
following the Timeline comment format below — start with `{commenter_ref}` and
include a `>` quote, or the reply loses its link to the originating comment (and,
for a human commenter, they are not notified). When the nit came from an inline comment, its review thread is left
**open** (not resolved); review-body and timeline comments have no thread to
resolve.

- **Skipped nit** (`skip-all`, or a `select` row chosen as skip):

  ```
  Noted as a nit — leaving as-is for now.

  ---
  🤖 Generated with [AssistantName](url)
  ```

- **Nit deferred to an issue** (`issue-all`, or a `select` row chosen as issue):

  ```
  Filed as #NNN.

  ---
  🤖 Generated with [AssistantName](url)
  ```

  Substitute `NNN` with the created issue number (when nits are grouped into one
  issue, every reply links the same number).

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

Use the same issue comments endpoint. **The reply body must start with
`{commenter_ref}` (see "Referring to the commenter" above — `@alice` for a human,
a bare handle like `Copilot` for a bot) and include a `>` quote of the relevant
excerpt**, since the timeline is flat and has no thread nesting.

Both parts are required. Without them a human commenter is not notified, and —
for **any** commenter — the reply loses the context linking it to their comment.
The `>` quote is also what the Step 2c linkage dedup keys on to mark the comment
`skip` on the next run; for a bot commenter, whose `{commenter_ref}` carries no
`@`-mention by design, **the quote is the only linkage signal there is**. Never
drop it.

Required format:
```
{commenter_ref}
> [relevant excerpt from their comment]

[Your response]

---
🤖 Generated with [AssistantName](url)
```

```bash
gh api repos/{owner}/{repo}/issues/{pr_number}/comments \
  --method POST \
  --field 'body={commenter_ref}
> [relevant excerpt]

[Your response]

---
🤖 Generated with [AssistantName](url)'
```
