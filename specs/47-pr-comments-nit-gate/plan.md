# Spec 47: pr-comments — nits-only halt + per-nit decision gate

## Context

`skills/pr-comments/SKILL.md` can churn through many auto-loop rounds with bot
reviewers (notably Copilot): the bot surfaces low-value nitpicks, the skill
auto-fixes them, re-requests review, the bot finds more nits, and the loop
repeats. Each round spends a commit and a review cycle on changes the user may
not even want.

Today the skill has **no concept of severity** — classification is purely
action-based (`fix` / `accept suggestion` / `reply` / `decline` / `skip`), and
the auto-loop exit conditions in `references/bot-polling.md` *explicitly forbid*
stopping because "feedback is minor." So the loop cannot recognize a pure-nit
round and hand control back to the user.

### Current reality (verified before writing this spec)

- `skills/pr-comments/SKILL.md` is **v1.47, 467 lines**.
- `references/` holds 10 files. Relevant here: `argument-parsing.md` (parse
  order / stickiness / cap validation), `bot-polling.md` (auto-loop exit
  conditions — the "do not exit for subjective reasons" list), `reply-formats.md`
  (per-type reply bodies + byline), `report-templates.md` (Step 14 summary),
  `consistency-scans.md` (Step 6b).
- Classification vocabulary is the flat set `fix` / `accept suggestion` /
  `reply` / `decline` / `skip` (+ internal `consistency`). Grep confirms **no**
  `nit` / `nitpick` / `severity` concept exists anywhere in the skill or its
  references, tests, or evals.
- The all-`skip` round path is already owned by **Step 6c** (the all-skip repoll
  gate → `bot-polling.md` "Entry Point: All-Skip Repoll Gate").
- The existing per-decline follow-up-issue flow (`gh issue create`) lives in
  **Step 11**; auto-loop defers those offers to the Step 14 batch.

## Goals

1. **Tag nits.** Add a `nit` severity tag to `fix` / `accept suggestion`
   classification in Step 6.
2. **Halt on all-nit rounds.** New auto-mode gate (Step 6d): when every
   actionable row is a nit, stop auto-applying and present a table.
3. **Let the user decide per nit:** fix / skip / file a GitHub issue.
4. **Reply to the bot** for nits the user skips or defers to an issue (link the
   issue).
5. **`--all` escape hatch** restores today's behavior (auto-fix every comment,
   including pure-nit rounds).

Behavioral additions must preserve everything asserted by existing
`tests/pr-comments/`.

## Decisions (confirmed with user)

- Override flag is named **`--all`**.
- The gate triggers on **any** all-nits round, **including the first**
  invocation (not only loop rounds ≥2).
- Gate applies in **auto mode only** — `--manual` already gates every round at
  the Step 7 confirm prompt, so no new behavior there.

## Design

### What counts as a "nit"

A `fix` / `accept suggestion` row is tagged `nit` when it is clearly
cosmetic/trivial — no effect on correctness, behavior, security, performance, or
public API. Signals, in order:

- **Explicit markers** in the comment body: a leading `nit:`, `nitpick:`,
  `(nit)`, `minor:`, `style:`, `typo:`, or a bot-supplied low/trivial severity
  label.
- **Semantic fallback:** wording/spelling/comment-typo fixes, naming/style
  preferences, formatting/whitespace, doc phrasing, import ordering — changes
  with no functional consequence.
- **Conservative bias:** when in doubt, **not** a nit (treat as substantive →
  normal flow). A misjudged "real" issue is still auto-fixed and the loop still
  runs; only *clearly* trivial rows are gated. Mirrors the skill's existing
  "when in doubt, lean toward implementing."

`reply`, `decline`, `skip`, and `consistency` rows are never nits — the nit
dimension only modifies `fix` / `accept suggestion`. An **oversized comment (Step
5), or any comment Step 5 flagged for manual review, is never a nit** even if its
body reads as cosmetic: Step 6d runs before Step 7, so tagging such a row `nit`
would route it to the lightweight nit table and silently drop Step 5's "pause
auto-mode — manual review recommended" caveat.

### The gate (new Step 6d, auto mode only)

Placed after Step 6c (all-skip repoll gate) and before Step 7.

- **Skip the gate entirely** when: `--all` was passed; OR `--manual` mode; OR
  the plan has zero actionable rows (that path is owned by Step 6c — an all-skip
  round must continue to route there, never to the nit gate).
- **Trigger:** plan has ≥1 actionable row **and every** actionable row is tagged
  `nit`.
- **On trigger:** present the nit table and collect decisions instead of
  auto-applying. This is a *user-gated pause*, modeled on the existing
  security-flag escalation (`bot-polling.md` exit condition #4) — the agent does
  **not** self-decide to stop; it surfaces the nits and the user decides.

### Nit table + decision prompt

```
## Nits-only round — your call

| # | File | Nit | Marker |
|---|------|-----|--------|
| 1 | src/util.ts:42 | Rename `tmp` -> `temp` for readability | nit: |
| 2 | docs/readme.md:10 | Fix a spelling typo in the heading | typo: |

Decide per nit — [fix-all / skip-all / issue-all / select]:
```

- `fix-all` → treat every nit as a normal `fix` / `accept suggestion`, then
  continue the auto-loop (commit, re-request, poll). Convergence is fine: a
  later all-nits round just shows the table again; the user can choose
  `skip-all` to terminate.
- `skip-all` → reply to each originating bot comment acknowledging the nit and
  declining to act now; do not commit; exit the loop.
- `issue-all` → file one follow-up issue per nit (offer one grouped issue as an
  alternative); reply to each bot comment linking the issue; exit the loop.
- `select` → per-row sub-prompt to choose `fix` / `skip` / `issue` individually;
  mixed outcomes (fix some, reply to the rest), then continue the loop only if
  at least one nit was fixed.
- Emit the prompt as the final message and **stop generating** until the user
  replies — reuse the existing confirmation-prompt discipline (the
  "Confirmation prompt template" pattern in Step 7).

**Loop & thread semantics (specify explicitly):**

- **Iteration accounting:** the 6d pause itself does not consume a `--max N`
  iteration; a `fix-all` / `select`-with-≥1-fix that resumes the loop consumes
  an iteration exactly as a normal fix round does (so the cap still bounds total
  commits). `skip-all` / `issue-all` exit, consuming none.
- **Thread state on skip:** a skipped or issue-deferred nit's reply **leaves the
  bot thread open** (do not resolve it). This lets the Step 6 "previously-handled
  skip" exact-login match self-terminate it on the next invocation, and lets a
  later edit-after-reply re-surface it if the bot follows up.

### Reuse, don't reinvent

The skip/issue outcomes map onto machinery that already exists:

- **Skip a nit** = a soft `decline` reply ("Noted as a nit — leaving as-is for
  now"), via `references/reply-formats.md`.
- **File an issue for a nit** = the existing Step 11 decline + `gh issue create`
  follow-up flow, plus a reply linking the created issue.
- **Fix a nit** = an ordinary `fix` / `accept suggestion`.

So the gate is mostly a *presentation + batching + loop-termination* layer over
existing fix / decline / issue / reply steps. New reference content captures the
table format, the four-choice prompt, and the per-outcome bot-reply wording.

### Reconciling the exit-condition negative constraint

`references/bot-polling.md` currently lists "feedback is minor" as an
**invalid** reason to exit (under "These are the ONLY valid reasons to exit the
auto-loop"). Reword that constraint to carve out one explicit exception: the
agent still may not *self-decide* to stop because feedback seems minor, but an
**all-nits round routes to the Step 6d user-gated nit table**, and the user's
`skip-all` / `issue-all` choice is a valid loop exit.

Add this as a **cross-reference**, not as a fifth peer item in the numbered
exit-condition list. That list is the *post-poll checkpoint* evaluated before
starting each new iteration; the all-nits exit fires later, at **Step 6d** —
reached only after looping back to Step 2 and re-running classification. Appended
as "condition #5" it would be misfiled and read as an agent-self-decided exit,
the exact failure the constraint guards against. Phrase it as: "an all-nits round
routes to the Step 6d user-gated nit table; the user's `skip-all` / `issue-all`
is a valid loop exit — the agent still may not self-decide to stop on 'minor.'"

## Files to modify

- **`skills/pr-comments/SKILL.md`**
  - Step 6 (heading "### 6. Decide: Plan action"): add a `nit` tag to the
    `fix` / `accept suggestion` classification — one paragraph defining the nit
    test + conservative bias.
  - New **"### 6d. Nits-only gate"** after the "### 6c. Repoll Gate" section:
    trigger conditions, the `--all` / `--manual` / zero-actionable skips, and a
    mandatory delegation to `references/nit-gate.md` (imperative
    "**you must now execute**" phrasing).
  - Step 7 plan table (heading "### 7. Present Plan and Confirm"): add a `Nit`
    indicator so nits are visible in normal mixed-round plans too.
  - Arguments section + invocation table: document `--all`.
  - Frontmatter `version`: bump `"1.47"` → `"1.48"` (trailing-integer increment,
    per the repo's scheme), once for the PR.
- **`skills/pr-comments/references/argument-parsing.md`** — strip `--all` in the
  token pass (boolean, non-sticky, no value); document semantics (auto mode
  only; ignored under `--manual`).
- **New `skills/pr-comments/references/nit-gate.md`** — full nit-table format,
  the `[fix-all / skip-all / issue-all / select]` prompt + stop-generating
  discipline, per-outcome handling, and the skip/issue bot-reply wording.
- **`skills/pr-comments/references/reply-formats.md`** — add the skip-nit and
  issue-link reply phrasings (still byline-terminated).
- **`skills/pr-comments/references/bot-polling.md`** — reword the "do not exit
  for subjective reasons" constraint to allow the user-gated all-nits exit; add
  the all-nits pause to the exit/escalation list.
- **`skills/pr-comments/references/report-templates.md`** — add a nit-gate
  outcome line to the Step 14 summary (e.g. "Nits: 2 fixed, 1 skipped, 1 filed
  as issue").
- **`README.md`** — refresh pr-comments notes to mention the nits-only gate and
  `--all`.
- **`cspell.config.yaml`** — add `nit` / `nitpick` (alphabetically) if not
  already present.

## Tests (required)

New `tests/pr-comments/test_nit_gate.py` with pure-function helpers (follow
`test_bot_poll_routing.py` / `test_comment_classification.py` patterns):

- `is_nit(body, action)` — marker detection (`nit:` / `typo:` / `style:` etc.),
  representative semantic cases, conservative default to non-nit, and
  non-applicability to `reply` / `decline` / `skip`.
- `should_present_nit_table(rows, all_flag, manual)` — True only when ≥1
  actionable row, all actionable rows are nits, not `--all`, and not manual;
  False on any non-nit row, on all-skip, on `--all`, and on manual.
- Extend `test_prcomments_argument_validation.py` + `test_pr_argument_parsing.py`
  for `--all` parsing (boolean; stripped before PR-number validation; ignored
  under `--manual`).

Run `uv run --with pytest pytest tests/` (sandbox lifted) after changes.

## Evals (recommended; benchmark refresh is a follow-up)

Add eval case(s) to `evals/pr-comments/evals.json`:

- An all-nits round → expect the nit table + bot replies, no auto-commit.
- A mixed round (substantive + nits) → expect auto-fix everything (gate does not
  trigger; nits ride along).

Per `evals/CLAUDE.md`, a full `benchmark.{json,md}` refresh is a larger lift and
may land as a follow-up rather than in this PR.

## Non-goals

- No severity tiers beyond the binary nit / not-nit. No ranking of nits.
- No change to manual-mode behavior beyond surfacing the `Nit` indicator in the
  plan table.
- No change to the all-`skip` repoll path (Step 6c) — it keeps owning empty /
  all-skip rounds.

## Verification

1. `uv run --with pytest pytest tests/pr-comments/` — all green, including the
   new nit-gate tests.
2. `npx cspell "skills/pr-comments/**/*.md" "specs/47-*/**/*.md"` — clean.
3. Classifier dry-run: a `nit:`-prefixed comment → gated; a "this will throw
   NPE" comment → not a nit → normal flow.
4. Confirm `--all` and `--manual` both bypass the gate, and that an all-`skip`
   round still routes to Step 6c (not the nit gate).
