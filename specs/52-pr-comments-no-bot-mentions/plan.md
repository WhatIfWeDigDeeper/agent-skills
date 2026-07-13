# Spec 52 — pr-comments: never emit a live @-mention of a bot

## Problem

`/pr-comments` posted a reply crediting a reviewer bot as `@Copilot`. GitHub
treats an `@copilot` mention in a PR comment as a **command**: it dispatched a
Copilot coding agent, which began pushing its own fixes to the PR. The skill's
reply was meant as attribution; GitHub read it as a work order.

The `@` reached the comment body by two independent routes:

1. **The template.** `references/reply-formats.md` requires every timeline reply
   to *start with* `@{commenter_login}` — with no carve-out for bot logins.
2. **Free-form prose.** The observed reply said "Good catch @Copilot — it was a
   claim about the diff, not the diff itself." No template produced that; the
   agent wrote it. Fixing only the template would leave this route open.

The same hazard exists on four more surfaces the skill writes to GitHub (commit
credit lines, follow-up issue bodies, nit skip/defer replies).

## The rule

**In any content posted to GitHub, a bot commenter is referenced by a bare
display handle — `Copilot`, `claude`, `coderabbitai` — never `@Copilot`. Human
commenters keep `@alice`.**

Asymmetric on purpose. On a human, the `@` is a notification, and on the flat PR
timeline it is the *only* thing that notifies them of a reply — that is why the
template mandates it today. On a bot, the `@` is not a notification at all; it is
a trigger. Dropping it for humans would fix the bug by breaking the feature.

## Detecting a bot

Primary signal: **`user.type == "Bot"`** on the comment author object.

The `[bot]` login suffix is **not** a sufficient test. As already recorded in
CLAUDE.md, Copilot's login varies by endpoint — it is
`copilot-pull-request-reviewer[bot]` on `/pulls/{n}/reviews` but a bare
`Copilot`, with no suffix, on the inline `/pulls/{n}/comments` endpoint. A
suffix-only check misses precisely the account that caused this bug.

The display handle then comes from the **Bot Display Names** algorithm that
already exists in `references/bot-polling.md` (strip `[bot]`; if hyphens remain,
take the first hyphen-separated token). This spec adds a second consumer of that
algorithm; it does not introduce new naming logic.

## Surfaces changed

| File | Location | Today | After |
|---|---|---|---|
| `references/reply-formats.md` | Timeline comment (Step 2c) format | body must start with `@{commenter_login}` | body must start with `{commenter_ref}` |
| `references/reply-formats.md` | Nit replies (Step 6d gate) | same `@{commenter_login}` wrapper | same wrapper, `{commenter_ref}` |
| `SKILL.md` | Step 11, reply prose | unconstrained | explicit prohibition on `@`-mentioning a bot anywhere in a body |
| `SKILL.md` | Step 10, commit credit | `(suggested by @alice)` | bare handle for bots: `(suggested by Copilot)` |
| `SKILL.md` | Step 11, follow-up issue body | `printf 'Suggested in PR #%s by @%s.\n\n'` | bare handle for bots |
| `references/nit-gate.md` | 3 references to the load-bearing `@mention` | assume `@` is always present | reworded (see below) |

`Co-authored-by:` trailers are **unchanged**. They carry a noreply email address,
not a mention — GitHub does not dispatch anything from them, and they are what
actually attributes the commit. Terminal-only output (status lines in
`references/report-templates.md` and `references/bot-polling.md`, confirmation
prompts) is also unchanged: it never reaches GitHub.

`{commenter_ref}` is defined once, in `references/reply-formats.md`, and the
other surfaces refer to that definition rather than restating the rule.

## Consequence: self-termination of bot timeline nits

`references/nit-gate.md` currently states that the `@mention` + `>` quote on a
timeline nit reply is *load-bearing for self-termination, not just notification*:
the Step 2c linkage dedup (SKILL.md Step 2c) marks a comment `skip` on the next
run when a later PR-author comment "`@mentions` the commenter **or** blockquotes
their text."

Removing the `@` for bots leaves the `>` quote as the **sole** surviving linkage
signal for a bot-directed timeline reply.

That is sufficient — the quote is already mandatory in the template and already
an accepted linkage signal, so the disjunct simply resolves via its second
branch. The fix is therefore **documentation, not matcher logic**: reword
`nit-gate.md` to say the quote is load-bearing on its own for bot commenters, and
harden the template so the quote cannot be dropped.

**Explicitly rejected:** extending the linkage matcher to also match a *bare*
login. `copilot` and `claude` are ordinary words in review prose ("copilot
flagged this too"), and a bare-substring match would silently classify live
comments as already-addressed. The existing matcher's `@`-anchored,
username-boundary regex in `tests/pr-comments/conftest.py` stays as-is for
humans; bots link via the quote. Precision beats redundancy here — a false `skip`
drops a real comment on the floor.

## Testing

Extend `tests/pr-comments/`:

- A bot-directed timeline reply carrying a `>` quote and **no** `@` still links
  back to its originating comment and is classified `skip` on the next run.
- No posted-body template emits `@` immediately followed by a bot login.
- Regression guard on the asymmetry: a human commenter still gets `@alice`.
- The existing human `@mention` linkage tests continue to pass unchanged.

**Allow-marker for the belt-and-braces scan.** The literal-`@Copilot` scan
(`test_no_hardcoded_at_mention_of_known_bot`) initially forbade the string
anywhere in `skills/pr-comments/`, which also blocked the skill's own
documentation from showing the concrete anti-example it exists to prevent —
e.g. "never write: Good catch @Copilot". Resolution: a line carrying the
literal marker `<!-- bot-mention-example -->` is skipped by the scan, mirroring
the repo's existing `<!-- cspell:disable-line -->` convention. The helper
(`_scan_lines_for_bot_mentions` in `tests/pr-comments/test_bot_mentions.py`)
implements the skip, and `TestBotMentionMarker` pins it in both directions: an
unmarked mention is still flagged, a marked one is not, and the marker does not
suppress mentions on other lines. The marker is documentation-only — it must
never appear on a template body, since templates are interpolated and posted
verbatim to GitHub, and marking one would let a real `@`-mention slip through.

## Non-goals

- Changing how humans are mentioned or notified.
- Suppressing bot mentions in terminal output or confirmation prompts.
- Touching `Co-authored-by` attribution.
- A general "escape all mentions" mechanism (e.g. backtick-wrapping or
  zero-width-space insertion). Bare handles read naturally in prose and need no
  escaping machinery.

## Version

`skills/pr-comments/SKILL.md` metadata version `1.50` → `1.51` (one bump for the
whole PR, covering SKILL.md and both reference files).
