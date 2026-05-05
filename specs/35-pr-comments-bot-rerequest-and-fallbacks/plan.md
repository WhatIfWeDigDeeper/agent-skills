# Spec 35: pr-comments — bot re-request hardening and `@file` harness fallback

## Problem

Three open issues report distinct gaps in the `pr-comments` skill (currently v1.39, last touched in commit `2c48ab6`). All three were filed against recent `/pr-comments` runs and all touch Step 13b / reply-posting infrastructure, so bundling them into one PR is appropriate (one version bump, one review pass, related test surface).

| # | Title | Surface |
|---|-------|---------|
| 141 | warn that single-bot `gh pr edit --add-reviewer` exits 0 but silently no-ops | SKILL.md Step 13b text |
| 144 | Step 13b bot re-request POST silently fails to emit `review_requested` for previously-reviewed bots | SKILL.md Step 13b + `references/bot-polling.md` |
| 145 | document fallback for harnesses that deny `@file` refs in `gh api` calls | `references/error-handling.md` |

Intended outcome: agents (and humans) following the skill stop being silently misled by either the `gh pr edit` no-op or the silent-no-event POST, and have a documented fallback when a harness blocks `-F body=@<path>` content.

## Design

### Edit A — Issue #141: Step 13b "Bot reviewers" sentence

**File**: `skills/pr-comments/SKILL.md`. Replace the existing sentence in Step 13b that begins:

> **Bot reviewers** (e.g. `copilot-pull-request-reviewer[bot]`): `gh pr edit` uses the GraphQL `requestReviewsByLogin` endpoint which rejects bot accounts — and a bot in the list will cause the entire `gh pr edit` call to fail, blocking human re-requests too.

with the wording proposed in issue #141 ("After:"):

> **Bot reviewers** (e.g. `copilot-pull-request-reviewer[bot]`): `gh pr edit --add-reviewer` uses the GraphQL `requestReviewsByLogin` endpoint, which rejects bot accounts. Failure mode varies by form: a list containing a bot fails the whole call (blocking human re-requests too); a single-bot call may exit 0 and print the PR URL while silently no-op'ing. Never use `gh pr edit` for any bot login — always use the REST endpoint below.

The replacement keeps the existing search anchors (`gh pr edit`, `requestReviewsByLogin`, REST handoff), adds the silent-no-op warning for the single-bot form, and turns the implicit "use REST" into an explicit prohibition.

### Edit B — Issue #144: post-POST `review_requested` event verification gate

The fix lives primarily in `skills/pr-comments/references/bot-polling.md` (canonical POST location). `SKILL.md` Step 13b gets a one-line imperative pointer inserted as a new item in its existing "After the POST:" numbered list so agents reading SKILL.md don't miss the gate (see B3 below for exact placement).

#### B1. `references/bot-polling.md` — extend "Entry from Step 13b"

Insert a new step **between current step 3 (the POST) and current step 4 ("Proceed to the Shared polling loop")**. Renumber the existing step 4 to step 5.

The new step:

- Reuses `snapshot_timestamp` (already recorded in step 1, before the POST) as the lower bound for the event window — no new timestamp variable is introduced.
- Sleeps 5 seconds for the event to surface. Documents that the 5-second sleep is heuristic: GitHub event emission is normally near-instant for bots that aren't in the silent-no-op case, so a false negative on very fast emissions is acceptable; the fallback message tells the user to click the UI re-request arrow, which is safe even on a false negative.
- On harnesses where `sleep` is blocked, documents that the event check runs immediately (no wait) — at worst a false negative for very fast emissions, with the same UI-fallback safety property.
- Queries `/issues/{pr_number}/events --paginate` and filters for `event == "review_requested"`, `created_at >= $snapshot_timestamp`, and `requested_reviewer.login == $bot_reviewer`.
- If `event_count` is `0` for a bot, surfaces the user-facing fallback message and **rewrites the `bot_reviewers` array to the subset whose `event_count > 0`**, so the Shared polling loop iterates only over bots whose event actually fired. Bots dropped from polling still receive the user-facing fallback message.
- If every bot's event count is 0, skip the Shared polling loop entirely and proceed to Step 14 — the polling loop has nothing to poll for.

The user-facing fallback message uses a `text` fenced block (per the CLAUDE.md `text` block rule):

```text
@<bot-handle> was added to requested_reviewers but the review_requested event did not fire. GitHub may silently skip event emission for previously-reviewed bots. Click the "Re-request review" arrow next to @<bot-handle> in the PR sidebar, then re-invoke pr-comments to poll for the response.
```

#### B2. `references/bot-polling.md` — new "Known limitations" subsection

Append a subsection at the end of the file (after "Bot Display Names") titled `Known limitations: silent no-op POST for re-reviewed bots`. Content:

- One paragraph explaining the silent-no-op pattern: HTTP 201 + `requested_reviewers` updated, but no `review_requested` event for previously-reviewed bots, regardless of login form (`Copilot` short vs canonical `[bot]` form).
- Notes that the verification gate above detects this and the only known reliable workaround is the PR sidebar's "Re-request review" arrow.
- A diagnostic command using the same `/issues/{pr_number}/events` filter that returns `[]` when the event was silently dropped. Use a generic placeholder (`<timestamp_before_post>`) for the lower bound — this is a standalone diagnostic the user runs after the fact, separate from the in-flow `snapshot_timestamp` variable used by the gate.

#### B3. `skills/pr-comments/SKILL.md` — Step 13b imperative pointer

Step 13b already contains an "After the POST:" numbered list with three items: (1) confirm pre-POST snapshot recorded, (2) confirm POST re-request was sent, (3) resume the shared bot-polling flow in `references/bot-polling.md`. Insert the new verification pointer as a **new item 3** in this list, pushing the existing item 3 ("Resume the shared bot-polling flow…") to item 4. The pointer logically precedes the polling-flow resumption because the gate determines whether polling should run at all.

The new item 3 reads:

> **Verify the `review_requested` event was actually emitted** — see `references/bot-polling.md` → **Entry from Step 13b**, step 4. GitHub silently no-ops the POST (HTTP 201, no event) for bots that have previously reviewed this PR; without the verification gate, the polling loop will time out for nothing.

This matches the CLAUDE.md "mandatory-step reference link" pattern (imperative phrasing, named target section).

### Edit C — Issue #145: `@file` denial fallback

**File**: `skills/pr-comments/references/error-handling.md`. Append a new section after `## git push failures` titled `## Harness denies `@file` reference`. Content:

- One paragraph explaining the failure mode: some harnesses run a content-screening hook that denies `gh api ... -F body=@<path>` (Step 11) or `gh api ... -F query=@<path>` (Step 12) when the file content isn't in the recent transcript, even if the agent just wrote the file via Write. Typical deny message: "wasn't shown being created in the transcript".
- Notes the issue is environment-specific; the documented `@file` pattern remains correct for environments without such a hook.
- Two fallbacks in priority order:
  1. **Read the file before re-issuing**, so its content appears in the transcript. Re-run the same `-F body=@<path>` call.
  2. **Pass content inline via a shell variable** (`QUERY=$(cat "${TMPDIR:-/private/tmp}/resolve.graphql")`, then `-f query="$QUERY"`), with a note that this partially undoes the reason the skill uses `@file` (zsh `<!--` corruption / heredoc quoting), so prefer option 1 when feasible. Use `${TMPDIR:-/private/tmp}` rather than a hardcoded `/tmp/` to comply with the CLAUDE.md sandbox-writability rule.

### Edit D — version bump

Bump `metadata.version` in `skills/pr-comments/SKILL.md` from `"1.39"` to `"1.40"`. Apply once for the whole PR per the skills/CLAUDE.md "once per PR" rule.

Before bumping, check whether the active branch already contains a bump relative to `origin/main`:

```bash
git fetch origin && git diff origin/main -- skills/pr-comments/SKILL.md | rg '^\+  version:'
git diff --name-status origin/main...HEAD -- skills/pr-comments/SKILL.md
```

If a bump already exists in the branch (e.g. from a prior commit), do not add a second one.

## Tests

No unit-test change is expected. The three edits are documentation/agent-instruction text:

- `tests/pr-comments/test_bot_poll_routing.py` already covers Step 13b routing and loop-exit logic; the new verification gate's runtime jq filter is not a routing decision and would require an integration test against a real GitHub PR (out of scope for this PR).
- `tests/pr-comments/test_post_edit_drift.py` covers Step 9 drift scanning, unrelated to these edits.
- No new classifier or routing logic is added.

If implementation introduces any executable helper logic (none planned), add focused tests under `tests/pr-comments/`.

## Evals and benchmarks

No eval or benchmark update is expected. Existing `evals/pr-comments/evals.json` assertions cover Step 13b routing and bot polling at a behavioral level; the verification gate is a runtime check that cannot be exercised in offline transcripts.

If implementation changes any existing eval assertion semantics, follow the repo's benchmark rules: re-run affected evals from observed transcripts, update `benchmark.json`, `benchmark.md`, and `README.md`, and null result fields where assertion semantics are inverted.

## Files to Modify

| File | Change |
|---|---|
| `skills/pr-comments/SKILL.md` | Edit A (Step 13b sentence); Edit B3 (imperative pointer after POST snippet); Edit D (version bump 1.39 → 1.40). |
| `skills/pr-comments/references/bot-polling.md` | Edit B1 (insert verification-gate step into "Entry from Step 13b"); Edit B2 (append "Known limitations" subsection). |
| `skills/pr-comments/references/error-handling.md` | Edit C (append "Harness denies `@file` reference" section). |
| `tests/pr-comments/` | No edit expected. |
| `evals/pr-comments/` | No edit expected. |
| `cspell.config.yaml` | Add legitimate new terms (e.g. `webhook` if flagged) only if cspell flags them, keeping the list alphabetically sorted. |
| `README.md` | No edit expected (skill description and trigger phrases are unchanged). |
| `.github/copilot-instructions.md` | No edit expected (this PR does not change project-wide rules; the mirroring requirement applies to `CLAUDE.md` ↔ `copilot-instructions.md` rule changes, which this PR does not make). |

## Verification

1. Confirm Edit A's anchor phrases survived:

   ```bash
   rg -n 'requestReviewsByLogin|silently no-op|Never use .gh pr edit. for any bot' skills/pr-comments/SKILL.md
   ```

2. Confirm Edit B1's verification step exists and Edit B3's pointer is in SKILL.md (use simple anchors rather than a single ordering-sensitive regex):

   ```bash
   rg -n 'review_requested' skills/pr-comments/SKILL.md skills/pr-comments/references/bot-polling.md
   rg -n '[Vv]erify.*event' skills/pr-comments/SKILL.md
   rg -n 'Entry from Step 13b' skills/pr-comments/SKILL.md
   ```

3. Confirm Edit B2's "Known limitations" subsection exists:

   ```bash
   rg -n 'Known limitations: silent no-op POST' skills/pr-comments/references/bot-polling.md
   ```

4. Confirm Edit C's `@file` fallback section exists:

   ```bash
   rg -n 'Harness denies .@file. reference' skills/pr-comments/references/error-handling.md
   ```

5. Confirm version state:

   ```bash
   rg -n '^  version:' skills/pr-comments/SKILL.md
   ```

6. Run focused tests:

   ```bash
   uv run --with pytest pytest tests/pr-comments/ -v
   ```

7. Run the repo-level test suite before opening a PR:

   ```bash
   uv run --with pytest pytest tests/
   ```

8. Run cspell on modified markdown/instruction files:

   ```bash
   npx cspell skills/pr-comments/SKILL.md skills/pr-comments/references/bot-polling.md skills/pr-comments/references/error-handling.md specs/35-pr-comments-bot-rerequest-and-fallbacks/*.md
   ```

9. Re-read all modified spec and skill files before reporting done — both `plan.md` and `tasks.md`, both SKILL.md Step 13b and bot-polling.md "Entry from Step 13b" end-to-end. Verify the SKILL.md pointer and the bot-polling.md verification step reference each other consistently and that step renumbering inside "Entry from Step 13b" is correct.

## Branch

`spec-35-pr-comments-bot-rerequest-and-fallbacks`

## Peer review

### Phase 0 — pre-spec consistency pass

Before implementation edits, stage only `specs/35-pr-comments-bot-rerequest-and-fallbacks/plan.md` and `tasks.md`, then run `/peer-review staged files`. Apply valid findings, record a per-iteration summary in `tasks.md`, and re-run until zero valid findings or iteration cap 2.

### Pre-ship branch pass

After implementation and verification, stage the full branch diff and run `/peer-review staged files`. Apply valid findings, record summaries in `tasks.md`, and re-run until zero valid findings or iteration cap 4.

## Risks

- **Renumbering drift inside "Entry from Step 13b".** Inserting a new step 4 and renumbering the old step 4 → 5 must be applied consistently in any cross-references inside `bot-polling.md`. Check for `step 4` / `step 5` references in the file and update any that point at the renumbered target.
- **Sleep-5 reliability.** A 5-second sleep before checking `/issues/{pr_number}/events` is a heuristic; GitHub event emission is normally near-instant for bots that aren't in the silent-no-op case, but a slow API path could cause a false negative. The fallback message instructs the user to click the UI re-request arrow, which is a safe action even on a false negative — they re-invoke the skill afterward. Document this trade-off in the verification step itself.
- **Verification only catches the documented case.** The gate detects `event_count == 0`, which is the issue #144 pattern. It does not catch other future no-op modes (e.g. event fires but webhook delivery fails downstream). Keep the gate scoped to what is empirically documented.
- **Sandbox `sleep` block.** Some harnesses block `sleep`. The verification gate uses `sleep 5` once (not a polling loop), which most harnesses allow; however, if the harness blocks even short sleeps, the verification simply runs the event check immediately — at worst a false negative for very fast event emissions. Document this in the gate text.
- **Cross-skill mirroring not required.** This PR does not change project-wide rules in `CLAUDE.md`, so no `.github/copilot-instructions.md` change is needed.

## Shipping

1. Create branch `spec-35-pr-comments-bot-rerequest-and-fallbacks`.
2. Complete Phase 0 peer review of the spec docs.
3. Implement Edits A–D.
4. Run verification.
5. Run the pre-ship peer review on the staged branch diff.
6. Commit, push, and open a PR with `Closes #141`, `Closes #144`, `Closes #145` in the PR body.
7. Run `/pr-comments {pr_number}` after pushing per repo convention.
8. Run `/pr-human-guide` before human review.
9. Merge only after CI is green and a human has reviewed.
10. After merge, verify issues #141, #144, #145 are closed; close any not auto-closed.
