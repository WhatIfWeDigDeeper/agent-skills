# Spec 55 — pr-comments: stop discarding bot review findings at Step 6

## Problem

`/pr-comments` fetches review bodies (Step 2b) and PR timeline comments
(Step 2c) correctly, then throws away real findings at Step 6. One rule governs
both surfaces, and it names bot summaries as the canonical skip case:

> Most of these are non-actionable — classify them as `skip` and move on. Common
> examples: bot PR summaries (Copilot, Claude), praise ("Good job!"), general
> observations with no request. […] When in doubt about whether something is
> actionable, lean toward `skip`.

`fix` is reachable but described as "rare". Both named bots post substantive,
code-level findings to exactly those surfaces — so the example list points the
agent at the wrong answer, and the tie-breaker pushes it there.

## Evidence (PR #218)

**Surface 1 — Copilot suppressed-confidence blocks.** Findings arrive inside a
collapsed block in the review body, with **no inline comment posted**:

````
## Pull request overview

Copilot reviewed 11 out of 11 changed files in this pull request and generated no new comments.

<details>
<summary>Comments suppressed due to low confidence (2)</summary>

**skills/CLAUDE.md:74**
* The new authoring rule ends with `Guard with [ -f "$HELPER" ]`, but the bullet
  never defines `HELPER` […] either define `HELPER` before the guard or
  reference the variable that actually exists.
```
<snippet of current file content>
```
**.github/copilot-instructions.md:207**
* This mirrored rule has the same internal inconsistency […]
</details>
````

Four such reviews landed on #218 carrying 1, 1, 4, and 2 entries. **Three of the
four sit behind the headline `…generated no new comments.`** All 8 findings were
valid; all were fixed by hand, and two of the reviews went unnoticed for days.
The same review body also carries a *second* collapsed block,
`<summary>Show a summary per file</summary>`, holding the changed-files table —
genuinely non-actionable. So "collapsed block" is not a usable signal in either
direction; the `<summary>` string is.

**Surface 2 — `claude[bot]` timeline verdicts.** `claude[bot]` posts its review
to `/issues/{n}/comments`, not `/reviews` — findings included. On #218 one such
comment carried 3 findings under `## Code review` / `### N. <title>` headings,
all valid, all fixed. Structurally it is indistinguishable from the "bot PR
summary" the skip example names, so the current rule discards it.

## The rule

**Classify a review body or timeline comment on what it contains, not on who
wrote it.** A body carrying a concrete, code-level request is actionable
regardless of author. A body is non-actionable because it *is a summary* — a
file-count headline with no findings, a changed-files table, prose with no
request — not because a bot wrote it.

Two corollaries the skill must state explicitly, because both are places an
agent will otherwise rationalize a skip:

- **The headline count and the inline-comment count are not evidence of a clean
  review.** `generated no new comments` co-occurred with 4 suppressed findings.
- **`fix` on these surfaces is ordinary, not rare.** The tie-breaker aligns with
  the regular-comment branch: when in doubt, lean toward implementing.

## Design decisions

### 1. The security collision, and why the carve-out is keyed on the summary string

`references/security.md` flags "Collapsed `<details>` blocks with hidden
instructions in the body" as hidden text → `decline`. Step 5 runs **before**
Step 6, so extraction alone would relabel every suppressed finding `decline`
while the plan table still *looked* right.

The fix moves the trigger from *presence of a collapsed block* to *presence of
hidden instructions*, and carves out the one recognized container by its exact
`<summary>` string — `Comments suppressed due to low confidence (N)`. Never a
blanket `<details>` bypass: Copilot's own `Show a summary per file` block proves
other collapsed content ships in the same body.

The carve-out is **not** a trust grant. Each extracted entry is screened
individually at Step 5 like any other comment — injection phrases, homoglyphs,
zero-width characters, and URL-fetch directives all still flag the entry — and
both the whole body and each entry stay inside `<untrusted_comment_body>`
framing.

### 2. Loop termination is part of the fix, not a follow-up

Review bodies have no GraphQL thread ID: Step 12 skips them, and Step 6's
previously-handled skip keys on `in_reply_to_id`, which they do not have. So a
`fix` applied to an extracted entry leaves **nothing** marking it done, and every
later run re-extracts it. In auto mode that is a 10-iteration no-op loop.

This latent gap already exists today for `claude[bot]` timeline `fix` rows;
extraction makes it live and common. The terminator is an acknowledgment reply
that blockquotes the entry's prose — which the existing Step 2c linkage dedup
already recognizes (`is_already_addressed` matches a `>` line at ≤3 leading
spaces whose content appears in the original body). No new matcher.

That match is a plain substring test with **no newline tolerance**, and for a
bot the `@`-mention half of the matcher never fires — so the quote must be a
verbatim run from a single line of the entry. Reflowing it, or joining an
entry's prose to its following code fence, links nothing and re-opens the loop.
The reply template states this, and a negative test pins it.

State it as an **invariant that binds every terminal path**, not a Step 11-local
rule: *any path that resolves a review-body or timeline entry must post a reply
blockquoting that entry's prose.* It binds Step 11 `reply`, Step 11 `decline`,
the new Step 11 `fix`-ack, and every Step 6d nit-gate outcome (`skip-all` /
`issue-all` already quote via `reply-formats.md`; `fix-all` and `select`-with-fix
route through Steps 8–13 and inherit the Step 11 ack).

For a **bot** commenter the blockquote is the *only* linkage signal —
`references/commenter-ref.md` gives bots a bare handle with no `@`-mention by
design. The Step 2c reply template already mandates the `{commenter_ref}` + `>`
wrapper for exactly this reason; the Step 2b template does not have it. Aligning
them is what makes review-body replies detectable at all.

### 3. Step 6d will now fire routinely — a named behavior change

Most #218 suppressed findings are doc-phrasing rewordings, which Step 6's
semantic fallback tags `nit`. An all-nit round trips the Step 6d nits-only gate,
so **auto mode halts and presents the nits table instead of fixing**. That is
correct per the gate's design, but it is a user-visible change and must be named
rather than discovered. Mixed rounds still happen — the #218 "never defines
`HELPER`" entry is a snippet-correctness bug, not a nit.

`references/nit-gate.md` currently documents review-body nit re-surfacing as an
accepted limitation, on the grounds that "review bodies are rarely actionable
nits" and that there is no Step 2b dedup. This change overturns both halves of
that premise, so that bullet is rewritten rather than left standing.

### 4. The `path:line` pointer is untrusted prose

The `**path:line**` header is text inside a comment body, not a validated API
field like `comment.path` / `comment.line`. It is a pointer to verify by reading
the file — **never** an input to the Step 6 path/line gate, and these entries are
always `fix` (manual edit), never `accept suggestion`. The existing Step 6 rule
for `suggestion` blocks in review bodies already reaches the same conclusion; the
observed fences are plain, not `suggestion`, so they are context, not a diff.

### 5. Step 2b's `APPROVED` exclusion stays

Checked every Copilot review across PRs #199, #202, #209, #212, #218, #223,
#226, #227, #228: 48 `COMMENTED`, 1 `APPROVED`. All four suppressed-confidence
blocks were on `COMMENTED` reviews; the single `APPROVED` review carried none.
The filter is safe as written. Record the residual gap — an `APPROVED` review
carrying a suppressed block would be missed — and what to change if it is ever
observed.

## Files

| File | Change |
| --- | --- |
| `skills/pr-comments/references/bot-review-surfaces.md` | **New.** Extraction rules, non-evidence rule, structural summary predicates, entry normalization, cross-review dedup (keep the **earliest** sighting — a re-posted entry keeping its newest timestamp would outrun its own acknowledgment; defensive only, no entry repeated across #218's four blocks), `APPROVED` residual gap. |
| `skills/pr-comments/SKILL.md` | Step 2b expansion (entries are an *additional* stream — Step 2c's dedup keeps receiving unexpanded review bodies) + already-addressed check; Step 6 branch rewrite; Step 6d behavior note; Step 11 acknowledgment invariant; Security model paragraph; `version` `1.51` -> `1.52`. |
| `skills/pr-comments/references/security.md` | Narrow the hidden-text `<details>` bullet; add the summary-string-keyed carve-out. |
| `skills/pr-comments/references/security-model.md` | Suppressed entries as a named ingestion surface; carve-out under Mitigations; mimicked-summary residual risk. |
| `skills/pr-comments/references/reply-formats.md` | Step 2b template gains the mandatory `{commenter_ref}` + `>` wrapper; add the acknowledgment-reply form. |
| `skills/pr-comments/references/nit-gate.md` | Rewrite the review-body bullet under "Thread state on skip/issue"; add the `fix`-outcome case. |
| `tests/pr-comments/conftest.py` | `extract_suppressed_entries`, `dedupe_suppressed_entries`, `is_actionable_review_body`, `is_bot_summary_body`. |
| `tests/pr-comments/test_bot_review_surfaces.py` | **New.** Real #218 payloads as fixtures. |
| `evals/pr-comments/{evals.json,benchmark.json,benchmark.md}` | Evals 42 and 43, Sonnet 5 single-eval track. |
| `evals/security/pr-comments.baseline.json` | Refreshed in the same PR — ingestion and screening both change. |

## Out of scope

- No path/line gate built on the untrusted `path:line` pointer.
- No `accept suggestion` path for these surfaces.
- No change to `CLAUDE.md` / `.github/copilot-instructions.md` — both surface
  facts are already recorded and mirrored there, so `instruction-sync` has
  nothing to enforce here.
- No re-run of eval 24. Its `review-body-summary-skipped` assertion targets a
  genuine summary body and stays correct under the new prose — the body carries
  no `**path:line**` entries, no `### N.` finding sections, and no code-level
  request, so it satisfies the third structural summary predicate. Its
  assertion *text* does get an in-place swap: the trailing rationale read
  `(bot PR summary, non-actionable)`, which is exactly the vocabulary this
  change deletes from SKILL.md, and `evals/CLAUDE.md` requires propagating
  removed vocabulary into `evals.json` assertion text and the matching
  `benchmark.json` expectation strings. Semantics are unchanged, so no new run
  is needed. Eval 31 targets HTML comments, not `<details>`, and is untouched.
