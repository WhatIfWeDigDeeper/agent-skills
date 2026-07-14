# Referring to the commenter — `{commenter_ref}`

Canonical rule for naming a commenter in **anything this skill posts to GitHub**:
inline reply, review-body reply, timeline reply, nit skip/defer reply (Step 6d),
commit message (Step 10), follow-up issue body (Step 11). Every template *and every
line of your own prose* on those surfaces refers to a commenter as `{commenter_ref}`:

| Commenter | `{commenter_ref}` | Example |
|---|---|---|
| Human | `@` + login | `@alice` |
| Bot | bare display handle, **no `@`** | `Copilot`, `claude`, `renovate` |

## Detecting a bot

**A bot is any comment author with `user.type == "Bot"`** — the Step 2/2b/2c fetches
project this field as `author_type`, so that is the key to test on a fetched comment.
Do not test for a `[bot]` login suffix instead — the same bot reports different logins
on different endpoints (Copilot is `Copilot` on `/pulls/{pr_number}/comments` but
`copilot-pull-request-reviewer[bot]` on `/pulls/{pr_number}/reviews`), so a suffix-only
check misses it exactly where it matters. Fall back to the suffix only for a source that
carries no type. Derive the display handle with the **Bot Display Names** algorithm in
`references/bot-polling.md` (strip `[bot]`; if hyphens remain, keep the first
hyphen-separated token).

## Why the asymmetry

On a human, `@login` is a notification — on the flat PR timeline it is the only thing
that tells them you replied. On a bot, `@login` is a **command**: prefixing a bot's
login with `@` in a PR comment dispatches its coding agent (for Copilot, this starts it
pushing its own commits to the PR). Never emit a live `@`-mention of a bot in posted
content.

**This binds your own prose, not just the templates.** Do not `@`-mention a bot's login
in the free-form part of a reply, a commit message, or an issue body — use the bare
display handle. Never write "Good catch, @Copilot" <!-- bot-mention-example --> — that
live `@`-mention dispatches Copilot's coding agent instead of crediting it. Write "Good
catch, Copilot" or "as Copilot noted". The free-form route, not a template, is what
posted the mention this rule exists to prevent.

## Per-surface notes

- **Reply bodies (Steps 6d and 11)** — wrapper and prose both use `{commenter_ref}`. A
  bot reply carries no `@`, so its `>` blockquote is the **sole** linkage signal Step 2c
  uses to recognize the comment as addressed; drop the quote and the comment re-surfaces
  as unaddressed on every future run. When matching that quote, allow up to **3 leading
  spaces** before the `>` — CommonMark still renders it as a blockquote (the nit
  templates are nested in a markdown list, so their quote line is indented), and a
  column-1-only match would miss a reply that is correctly quoted on GitHub. At 4+ spaces
  it is an indented code block, not a quote, and does not link.
- **Commit messages (Step 10)** — credit lines read `(suggested by Copilot)`, never
  `(suggested by @Copilot)` <!-- bot-mention-example --> — an `@`-mention in a pushed
  commit message is still a live mention on GitHub. `Co-authored-by:` trailers are
  **unaffected**: they carry a noreply email, not a mention, and stay
  `Co-authored-by: <login> <<login>@users.noreply.github.com>` for bots and humans alike.
- **Follow-up issue bodies (Step 11)** — seed the shell variable with the placeholder
  (`commenter_ref="{commenter_ref}"`), never with an `@`-prefixed literal. An `@`-seeded
  default models the human shape, so a bot substituted into it posts a live mention.

Terminal output — status lines, confirmation prompts, the plan table — is never posted
to GitHub and is unaffected; it keeps using `@bot1`.
