# Spec 33: pr-comments — portable bot polling outside Claude Code

## Problem

Issue #138 identifies a portability gap in the `pr-comments` bot-review polling flow. The skill currently describes the intended 60-second polling loop and gives a Claude Code-specific workaround when `sleep` is blocked: use `ScheduleWakeup` after each interval.

That is correct for Claude Code, but other assistant runtimes may not expose a delayed-resume primitive. VS Code/Copilot also forbids terminal `sleep` or similar wait commands. In those runtimes, the workflow's intended polling behavior is clear, but the fallback path is underspecified: an agent could silently stop early or violate host tool restrictions.

The fix is an instruction-portability change. Preserve the existing polling model where the runtime supports it, and explicitly define the no-scheduler/no-sleep fallback.

## Design

### Edit A — make poll waiting runtime-neutral

In `skills/pr-comments/references/bot-polling.md`, update the `Poll interval and timeout` section. Replace the current `When sleep is blocked` paragraph with a runtime-neutral wait policy:

1. Prefer the host runtime's delayed-resume or scheduler primitive when available. Use it after each 60-second interval and resume the same bounded polling loop.
2. If no scheduler exists but the host permits blocking waits, use a bounded `sleep 60` loop. Keep the existing `for i in $(seq 1 N); do` guidance and 10-minute timeout.
3. If neither a scheduler nor blocking waits are available, run one immediate signal check using the same Signals 1-3 queries. If no signal fires, report that bot review is still pending, tell the user to re-invoke `pr-comments` when the review lands, then proceed to Step 14 and end the invocation.

Keep Claude Code as an example only:

```text
In Claude Code, one delayed-resume primitive is ScheduleWakeup(delaySeconds=60, prompt=<invocation text used to start this skill, e.g. "/pr-comments 130">).
```

Keep the existing warning not to use `Monitor` for long intervals; `Monitor` is for short-interval polling, not waits of 60 seconds or longer.

### Edit B — preserve polling semantics

The wording change must not alter the core bot-review state machine:

- Poll interval remains 60 seconds.
- Timeout remains 10 minutes.
- Signals 1-3 remain the source of truth.
- Signal 1 still takes priority when multiple signals fire in the same cycle.
- New unresolved bot threads still loop back to Step 2 within the same invocation when the runtime can continue polling.
- If every polled bot submits a review without new inline threads, exit cleanly and proceed to the report.
- On timeout, keep the existing user-facing timeout message and proceed to Step 14.

The no-scheduler/no-sleep fallback is not a timeout and should not pretend it waited. It should say the review is pending because the host runtime cannot wait in this invocation.

### Edit C — version bump

`skills/pr-comments/references/bot-polling.md` is a reference file that affects skill behavior, so bump `metadata.version` in `skills/pr-comments/SKILL.md` once for this PR.

Before editing, check whether the active PR already contains a `pr-comments` version bump relative to `origin/main`:

```bash
git fetch origin && git diff origin/main -- skills/pr-comments/SKILL.md | rg '^\+  version:'
git diff --name-status origin/main...HEAD -- skills/pr-comments/SKILL.md
```

If this PR modifies an existing `SKILL.md` and no bump exists yet, increment from the current version. Do not add a second bump if one already exists in the branch.

## Tests

No unit-test change is expected. `tests/pr-comments/test_bot_poll_routing.py` covers routing and loop-exit decisions, while this change documents host runtime waiting behavior. Add tests only if implementation introduces executable helper logic.

Suggested manual review checks:

1. The `Poll interval and timeout` section explicitly names all three runtime cases: scheduler available, blocking waits allowed, and neither available.
2. The no-scheduler/no-sleep fallback performs an immediate signal check before reporting pending review.
3. The Claude Code `ScheduleWakeup` example is qualified as an example, not a universal instruction.
4. The instruction does not tell VS Code/Copilot agents to run `sleep` when their terminal tool forbids it.

## Evals and benchmarks

No eval or benchmark update is expected for the implementation pass. Existing `evals/pr-comments/evals.json` assertions check the intended polling behavior: 60-second intervals, GraphQL thread polling, and looping back to Step 2 on new unresolved bot threads. Historical `evals/pr-comments/benchmark.json` evidence mentioning `sleep 60` records observed prior runs and should not be rewritten for this documentation-only portability fix.

If implementation changes any existing eval assertion semantics, follow the repo's benchmark rules: re-run affected evals from observed transcripts, update `benchmark.json`, `benchmark.md`, and `README.md`, and null result fields where assertion semantics are inverted.

## Files to Modify

| File | Change |
|---|---|
| `skills/pr-comments/references/bot-polling.md` | Replace the `When sleep is blocked` paragraph with the three-case portable wait policy. |
| `skills/pr-comments/SKILL.md` | Bump `metadata.version` once if the branch does not already contain a `pr-comments` bump. |
| `tests/pr-comments/test_bot_poll_routing.py` | No edit expected unless helper logic is introduced. |
| `evals/pr-comments/evals.json` | No edit expected unless implementation intentionally expands assertions. |
| `evals/pr-comments/benchmark.json` | No edit expected; keep historical evidence intact. |
| `cspell.config.yaml` | Add legitimate new terms only if cspell flags them, keeping the list sorted. |

## Verification

1. Confirm the fallback language exists:

   ```bash
   rg -n 'delayed-resume|blocking waits|neither.*scheduler|immediate signal check|ScheduleWakeup' skills/pr-comments/references/bot-polling.md
   ```

2. Confirm version state:

   ```bash
   rg -n '^  version:' skills/pr-comments/SKILL.md
   ```

3. Run focused tests:

   ```bash
   uv run --with pytest pytest tests/pr-comments/ -v
   ```

4. Run the repo-level test suite before opening a PR:

   ```bash
   uv run --with pytest pytest tests/
   ```

5. Run cspell on modified markdown/instruction files:

   ```bash
   npx cspell skills/pr-comments/references/bot-polling.md skills/pr-comments/SKILL.md specs/33-pr-comments-portable-bot-polling/*.md
   ```

6. Re-read all modified spec files before reporting done.

## Branch

`spec-33-pr-comments-portable-bot-polling`

## Peer review

### Phase 0 — pre-spec consistency pass

Before implementation edits, stage only `specs/33-pr-comments-portable-bot-polling/plan.md` and `tasks.md`, then run `/peer-review staged files`. Apply valid findings, record a per-iteration summary in `tasks.md`, and re-run until zero valid findings or iteration cap 2.

### Pre-ship branch pass

After implementation and verification, stage the full branch diff and run `/peer-review staged files`. Apply valid findings, record summaries in `tasks.md`, and re-run until zero valid findings or iteration cap 4.

## Risks

- **Ambiguous runtime capability detection.** Agents may not know whether their host supports delayed resume or blocking waits. The wording should direct them to use the best available primitive and choose the immediate-check fallback when neither is available.
- **False appearance of waiting.** The no-scheduler/no-sleep fallback must not imply that the agent waited for bot review. It should clearly report that review is pending and the host runtime cannot wait in this invocation.
- **Over-changing the polling loop.** The implementation should not rewrite Signals 1-3, bot identity matching, timeout behavior, or auto-loop exit conditions.
- **Version bump discipline.** Only bump once for the PR, even though the behavior-affecting edit is in a reference file.

## Shipping

1. Create branch `spec-33-pr-comments-portable-bot-polling`.
2. Complete Phase 0 peer review of the spec docs.
3. Implement Edits A-C.
4. Run verification.
5. Run the pre-ship peer review on the staged branch diff.
6. Commit, push, and open a PR with `Closes #138` in the PR body.
7. Run `/pr-comments {pr_number}` after pushing per repo convention.
8. Run `/pr-human-guide` before human review.
9. Merge only after CI is green and a human has reviewed.
10. After merge, verify issue #138 is closed; close it manually if the PR did not auto-close it.
