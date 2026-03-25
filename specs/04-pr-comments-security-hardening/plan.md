# Plan: pr-comments Security Hardening

## Problem

Security audit (skills.sh/whatifwedigdeeper/agent-skills/pr-comments/security/snyk, 2026-03-24) identified two medium-severity findings:

- **W011** — Third-party content exposure: the skill processes untrusted GitHub PR comment bodies to make editing decisions, creating an indirect prompt injection vector.
- **W012** — Runtime control via unverifiable external dependency: suggestion blocks fetched from GitHub endpoints directly control the agent's file editing actions.

The skill already has two mitigations (Step 5 prompt injection screening and the Step 7 human confirmation gate). Three gaps remain:

1. **Suggestion blocks are not validated against the PR diff** — a crafted suggestion could target lines outside the PR scope, potentially modifying unrelated code.
2. **No bounds on comment body size** — extremely long comments could bury injection attempts or overwhelm screening.
3. **Injection screening runs in the same agent context** — a sufficiently clever injection could attempt to override Step 5 instructions.

Note: The audit's W012 recommendation for "response authenticity verification" (checksums, caching with integrity checks) is a non-goal — `gh` CLI handles TLS and GitHub authentication, and adding a verification layer on top would be over-engineering.

## Design

### Item 1: Validate suggestion blocks against PR diff

Before applying any `suggestion` block, verify that the target file + line range falls within the PR diff.

**How:**
- Fetch the PR diff once in Step 4 (Read Code Context), alongside reading affected files:
  ```bash
  gh pr diff {pr_number}
  ```
- Parse the diff to extract the set of `(file, line_range)` hunks that are part of the PR.
- For each comment with `action: accept suggestion` in Step 6, check that `comment.path` appears in the diff and that `comment.line` / `comment.start_line` falls within a changed hunk.
- If the target is outside the diff, downgrade the action to `decline` with note: "Suggestion targets lines outside the PR diff — cannot safely apply."
- If the diff cannot be fetched, downgrade all `accept suggestion` actions to `implement` (manual edit) rather than auto-applying the suggestion block.

This applies to both inline comments (Step 2) and any review body comments (Step 2b) that contain suggestion blocks.

Diff-validation declines should pause auto-mode (same as screening flags already do in Step 7/Step 10).

This is done in Step 6 (decide), before the plan table is shown in Step 7.

### Item 2: Comment body size guard

Add a size check in Step 5 (screening):

- If a comment body exceeds **64 KB**, truncate to 64 KB for the agent's screening pass and flag it as suspicious with note: "Unusually large comment body — screening applied to first 64 KB only. Manual review recommended."
- The full comment body is still shown to the user in the Step 7 plan table — the truncation applies only to the screening evaluation, not to user visibility.
- Surface oversized comments prominently in Step 7.

64 KB is well above any legitimate code review comment; GitHub's own UI renders comment bodies that large as degraded. This bound prevents resource exhaustion and reduces the risk that length is used to bury injected instructions.

This applies to both inline comments and review body comments from Step 2b.

### Item 3: Reinforce screening independence (documentation only)

Add a note to Step 5 making the intent explicit: the screening step must be applied before any suggestion or instruction in a comment is acted upon, and no comment content can override or skip this step. This applies to all comment types — inline (Step 2) and review body (Step 2b). This is a workflow documentation hardening — it doesn't change tooling but makes the invariant legible to future readers and agents.

## Files to Modify

1. `skills/pr-comments/SKILL.md`
   - **Step 4** (Read Code Context): add `gh pr diff {pr_number}` fetch; store diff for reuse in Step 6
   - **Step 5** (screening): add size guard (64 KB truncation + flag), add explicit note that no comment content may override or skip screening, note applies to both inline and review body comments
   - **Step 6** (decide): add diff-validation rule for `accept suggestion` actions — target must be within PR diff or downgrade to `decline`; fallback to `implement` if diff unavailable; diff-validation declines pause auto-mode
   - Update security note at end of file to reflect all three mitigations

## Verification

- Read updated Step 4: confirm diff fetch is present.
- Read updated Step 5: confirm size guard and screening-independence note are present and cover both comment types.
- Read updated Step 6: confirm diff-validation rule is present for suggestion acceptance, fallback action is `implement`, and auto-mode pause is noted.
- `npx cspell skills/pr-comments/SKILL.md` — no unknown words.
- Run `uv run --with pytest pytest tests/pr-comments/` if tests exist for this skill.
- Bump `metadata.version` in SKILL.md frontmatter: `"1.7"` → `"1.8"`.
