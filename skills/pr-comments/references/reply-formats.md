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

The templates below name the commenter as `{commenter_ref}` — `@alice` for a
human, a bare handle with no `@` for a bot. The rule, the bot test, and the
per-surface notes live in **`references/commenter-ref.md`**; read it before
filling in any template here.

## Quoting the excerpt — verbatim, single line

**This binds every `>` quote in this file** — nit replies, review-body (Step 2b),
timeline (Step 2c), and fix acknowledgments alike.

**Each `>` line must be a verbatim run of characters copied from a single line of
the original body** — never paraphrase, summarize, or reflow it. The linkage
match is a plain substring test with no newline tolerance, so a quote that
rewords the excerpt, or joins two source lines (prose onto a following code
fence, or two wrapped lines of the same bullet), matches nothing. The comment
then reads as unaddressed and re-surfaces on every later run — and for a **bot**,
whose `{commenter_ref}` carries no `@`, the quote is the only linkage signal
there is, so a non-verbatim quote leaves no linkage at all.

Pick a short, distinctive line rather than a long one: one line that exists
verbatim in the source beats a faithful-looking rewrite of the whole paragraph.

## Nit replies (Step 6d nits-only gate)

When the Step 6d gate resolves a nit by **skipping** or **deferring to an
issue**, reply to the originating bot comment with the byline footer, using the
endpoint **and format** that match where the nit originated: an inline (Step 2)
nit via the inline replies endpoint below; a review-body (Step 2b) or timeline
(Step 2c) nit via the issue comments endpoint, with a **timeline** reply
following the Timeline comment format below.

Both templates below open with `{commenter_ref}` and a `>` quote. On a
review-body or timeline reply that wrapper is **mandatory**: the quote is what
links the reply back to the originating comment, and for a **bot** commenter —
whose `{commenter_ref}` carries no `@` — it is the *only* linkage signal there
is. Quote it verbatim from a single source line, per
"Quoting the excerpt — verbatim, single line" above: drop the quote, or
reword it, and the nit re-surfaces as unaddressed on every subsequent run.
(For a human, the `@` also notifies them.) On an *inline* reply the thread itself
carries the link, so the wrapper is redundant but harmless — keep it for
consistency. When the nit came from an inline comment, its review thread is left
**open** (not resolved); review-body and timeline comments have no thread to
resolve.

- **Skipped nit** (`skip-all`, or a `select` row chosen as skip):

  ```
  {commenter_ref}
  > [relevant excerpt from their comment]

  Noted as a nit — leaving as-is for now.

  ---
  🤖 Generated with [AssistantName](url)
  ```

- **Nit deferred to an issue** (`issue-all`, or a `select` row chosen as issue):

  ```
  {commenter_ref}
  > [relevant excerpt from their comment]

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

Use the issue comments endpoint (replies go to the PR timeline). **The reply body
must start with `{commenter_ref}` and include a `>` quote of the relevant
excerpt** — a review body has no thread, so the quote is what links the reply to
it and what the Step 2b linkage dedup keys on next run. For a bot commenter,
whose `{commenter_ref}` carries no `@`-mention by design, the quote is the only
linkage signal there is. Never drop it, and quote it verbatim from a single
source line, per "Quoting the excerpt — verbatim, single line" above — a
paraphrased quote links no better than a missing one.

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

## Fix acknowledgment (review body / timeline)

A `fix` on these surfaces has no thread to resolve, so this reply is the only
record that the entry was handled. One blockquote per entry covered.

Every `>` line here follows "Quoting the excerpt — verbatim, single line" above.

```
{commenter_ref}
> [entry 1 excerpt]

> [entry 2 excerpt]

Both findings were valid and are fixed in <short sha>.

---
🤖 Generated with [AssistantName](url)
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
drop it, and quote it verbatim from a single source line, per
"Quoting the excerpt — verbatim, single line" above — a paraphrased quote
links no better than a missing one.

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
