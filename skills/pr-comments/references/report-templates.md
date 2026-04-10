# Report Templates

Use these templates for Step 14, omitting lines that don't apply.

## Standard report

```
## Done

{changes line}
{declined line — omit if none}
{skipped line — omit if none}
{push/review status}
{poll status — omit if not applicable}

[List of each action taken]

PR #N is ready for your final review.
<PR URL>
```

**Changes line** (pick one):
- Changes made: `Applied N suggestions + implemented N comments → committed <hash>`
- No changes: `No changes — no code updates needed (threads replied to, declined, or outdated).`

**Declined line** (pick one):
- Some declined: `Declined N items — replied with explanations`
- All declined: `Declined all N items — replied with explanations`

**Skipped line** (pick one):
- `Skipped N outdated threads`
- `Skipped N threads already handled in the reply chain`
- `Skipped N threads (outdated or already handled)`
- `Skipped N timeline comments (already addressed or non-actionable)`

**Push/review status** (pick one):
- Pushed and re-requested: `Pushed and re-requested review from @user1, @user2`
- Re-requested only (no new commits): `Re-requested review from @user1, @user2 (no new commits to push)`
- User declined push: `Commit not pushed — run \`git push\` and re-request review manually when ready`
- No reviewers: omit, or `No reviewers to re-request (all threads outdated/no replies)`

**Poll status** (only include if polling was attempted, pick one):
- Poll found threads: `Polled for @bot1, @bot2 (~Ns) — found N new threads, processed above`
- Poll completed, no new threads: `Polled for @bot1, @bot2 (~Ns) — all reviews completed with no new threads`
- Poll timed out: `One or more polled bots haven't responded yet. Re-invoke the pr-comments skill when their reviews are ready`

## Auto-loop summary

Shown in place of the standard report when auto-mode was active:

```
## Auto-Loop Summary (N iterations)

| Iter | Threads | Fixed | Accepted | Declined | Skipped | Commit  |
|------|---------|-------|----------|----------|---------|---------|
| 1    | 5       | 3     | 1        | 1        | 0       | abc1234 |
| 2    | 2       | 2     | 0        | 0        | 0       | def5678 |
| 3    | 0       | —     | —        | —        | —       | (none)  |

Total: 5 fixes, 1 accepted suggestion, 1 declined across 2 commits.
Updated PR title: "Fix null checks and parameter naming per review"
Updated PR body: reflects 3 commits (was 1).
Exited: no new threads after iteration 3.

M out-of-scope declined comments — file follow-up issues? [all/select/none]

PR #N is ready for your final review.
<PR URL>
```

Omit "Updated PR title/body" lines if PR metadata was not changed. Omit the follow-up issues offer if there were no out-of-scope declines.

**Closing line** — MANDATORY. Every report, without exception, must end with the PR status line and URL. Do not omit the URL because the user "already knows it" or because the session is ending. The URL must be the last thing you output.

Before writing the closing line, check CI status:
```bash
gh pr checks {pr_number}
```
- If all checks pass (or no checks exist): use `PR #N is ready for your final review.`
- If any check is failing: use `PR #N has failing CI — fix before merging.` and list the failing check names.
- If checks are still running: use `PR #N — CI still running, re-check before merging.`

```
PR #N is ready for your final review.
<PR URL>
```

The `<PR URL>` line is not optional. Output it last, on its own line, every time.

## Exit reason values

- `Exited: no new threads after iteration N.`
- `Exited: reached max iterations (N).`
- `Exited: poll timeout (10 min) on iteration N.`
