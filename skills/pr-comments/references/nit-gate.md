# Nits-only Gate (Step 6d)

You reach this file only from **Step 6d**, in **auto mode**, when the plan has
**≥1 actionable row and every actionable row is a `nit`** (a `fix` / `accept
suggestion` tagged in Step 6). This is a *user-gated pause*, modeled on the
security-flag escalation in `references/bot-polling.md` exit condition #4 — you
do **not** self-decide to stop because feedback seems minor; you surface the
nits and the user decides. Do not auto-apply anything before the user replies.

## Present the table

Emit the nits-only table. Columns: **#**, **File** (`path:line`), **Nit**
(one-line description of the change), **Marker** (the explicit marker that
tagged it — `nit:` / `nitpick:` / `(nit)` / `minor:` / `style:` / `typo:` / a
bot severity label — or `semantic` when the tag came from the semantic
fallback rather than an explicit marker).

```
## Nits-only round — your call

| # | File | Nit | Marker |
|---|------|-----|--------|
| 1 | src/util.ts:42 | Rename `tmp` -> `temp` for readability | nit: |
| 2 | docs/readme.md:10 | Fix a spelling typo in the heading | typo: |

Decide per nit — [fix-all / skip-all / issue-all / select]:
```

**Stop-generating discipline.** Emit the table followed by the
`Decide per nit — [fix-all / skip-all / issue-all / select]:` prompt on its own
line as your **final message**, then **stop generating**. Do not supply an
answer, do not assume a default, do not continue to any outcome below. Resume
only after the user replies. (Same discipline as the Step 7 "Confirmation
prompt template.")

## Per-outcome handling

### `fix-all`

Treat every nit as an ordinary `fix` / `accept suggestion` and proceed through
the normal apply flow — **Steps 8–13** (apply, drift re-scan, commit, reply,
resolve, push, re-request). This resumes the auto-loop. A later all-nits round
simply shows this table again; the user can pick `skip-all` then to terminate.

### `skip-all`

Do **not** commit. For each nit's originating bot comment, post the skip-nit
reply from `references/reply-formats.md` ("Noted as a nit — leaving as-is for
now") — using the endpoint/format that matches the comment's origin (a
timeline-originated nit needs the `@{commenter_login}` + `>` quote wrapper).
Leave each thread **open** (do not resolve — see thread semantics below).
Then **exit the loop** and go to **Step 14** (report).

### `issue-all`

File a follow-up GitHub issue per nit via the existing **Step 11**
`gh issue create` flow. First offer one grouped issue covering all nits as an
alternative: emit `One issue per nit, or one grouped issue? [per-nit/grouped]`
on its own line as your **final message**, then **stop generating**. Do not
supply an answer, do not assume a default, do not proceed to `gh issue create`.
Resume only after the user replies (same discipline as the "Present the table"
prompt above). Then, for each nit, post the issue-link reply from
`references/reply-formats.md` ("Filed as #NNN") — using the endpoint/format that
matches the comment's origin (a timeline-originated nit needs the
`@{commenter_login}` + `>` quote wrapper). Do **not** commit code; leave
each thread **open**. Then **exit the loop** and go to **Step 14**.

### `select`

Sub-prompt per row for `fix` / `skip` / `issue`. Emit the prompt block below as
your **final message**, then **stop generating**. Do not supply answers, do not
assume a default, do not proceed to apply any outcome. Resume only after the
user replies (same discipline as the "Present the table" prompt above).

```
Per nit — fix / skip / issue:
1. src/util.ts:42 ->
2. docs/readme.md:10 ->
```

Apply the mixed outcome: `fix` rows go through Steps 8–13; `skip` rows get the
skip-nit reply; `issue` rows go through the Step 11 issue flow with an
issue-link reply (always one issue per nit here — the grouped-issue offer
applies only to `issue-all`). **Continue the loop only if ≥1 nit was fixed** (a commit was
produced); if every selected row was skip/issue, exit to Step 14 like
`skip-all`.

## Loop & thread semantics

- **Iteration accounting:** the 6d pause itself consumes **no** `--max N`
  iteration. A `fix-all` or `select`-with-≥1-fix that resumes the loop consumes
  one iteration exactly as a normal fix round does (so `--max` still bounds total
  commits). `skip-all` and `issue-all` exit and consume none.
- **Pending async bots on exit:** `skip-all` and `issue-all` exit the loop
  immediately. Unlike the Step 6c all-skip repoll gate, they do **not** wait for
  a bot whose review is still generating, so a still-pending substantive review
  is deferred to the next invocation rather than caught this run. This is
  intentional — the same deferral as a human comment arriving mid-run; the next
  `/pr-comments` invocation picks it up.
- **Thread state on skip/issue:** a skipped or issue-deferred nit's reply
  **leaves the bot thread open** — do **not** resolve it. How the nit avoids
  re-surfacing (and re-triggering this gate) on the next invocation depends on
  where it originated:
  - **Inline** nits have a review thread: the Step 6 "previously-handled skip"
    exact-`login` match self-terminates it on the next run, and an
    edit-after-reply re-surfaces it if the bot follows up.
  - **Timeline** nits have no thread, but the skip/issue reply's
    `@{commenter_login}` + `>` quote (required by `references/reply-formats.md`)
    is recognized by the Step 2c linkage dedup, which marks the comment `skip`
    next run. The `@mention` + quote is therefore load-bearing for
    self-termination, not just notification.
  - **Review-body** nits have neither a thread nor a Step 2b dedup, so a
    skipped/issued review-body nit can re-trigger this gate on a later run if it
    remains the only actionable row. This is a pre-existing skill limitation
    (normal review-body replies/declines re-surface the same way), and review
    bodies are rarely actionable nits, so the case is narrow — the next
    invocation simply re-presents it.
