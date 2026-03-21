# Plan: pr-comments Security Hardening

## Problem

Security audit (skills.sh/whatifwedigdeeper/agent-skills/pr-comments/security/snyk, 2026-03-16) identified two medium-severity findings:

- **W011** — Third-party content exposure: the skill processes untrusted GitHub PR comment bodies to make editing decisions, creating an indirect prompt injection vector.
- **W012** — Runtime control via unverifiable external dependency: suggestion blocks fetched from GitHub endpoints directly control the agent's file editing actions.

The skill already has two mitigations (Step 5 prompt injection screening and the Step 7 human confirmation gate). Three gaps remain:

1. **Suggestion blocks are not validated against the PR diff** — a crafted suggestion could target lines outside the PR scope, potentially modifying unrelated code.
2. **No bounds on comment body size** — extremely long comments could bury injection attempts or overwhelm screening.
3. **Injection screening runs in the same agent context** — a sufficiently clever injection could attempt to override Step 5 instructions.

## Design

### Item 1: Validate suggestion blocks against PR diff

Before applying any `suggestion` block, verify that the target file + line range falls within the PR diff.

**How:**
- Fetch the PR diff with `gh pr diff {number}` (or `gh api repos/{owner}/{repo}/pulls/{number}` with `Accept: application/vnd.github.v3.diff`).
- Parse the diff to extract the set of `(file, line_range)` hunks that are part of the PR.
- For each comment with `action: accept suggestion`, check that `comment.path` appears in the diff and that the comment's `line` / `start_line` falls within a changed hunk.
- If the target is outside the diff, downgrade the action to `decline` with note: "Suggestion targets lines outside the PR diff — cannot safely apply."

This is done in Step 6 (decide), before the plan table is shown in Step 7.

### Item 2: Comment body size guard

Add a size check in Step 5 (screening):

- If a comment body exceeds **64 KB**, truncate to 64 KB for screening and flag it as suspicious with note: "Unusually large comment body — screening applied to first 64 KB only. Manual review recommended."
- Surface oversized comments prominently in Step 7.

64 KB is well above any legitimate code review comment; GitHub's own UI renders comment bodies that large as degraded. This bound prevents resource exhaustion and reduces the risk that length is used to bury injected instructions.

### Item 3: Reinforce screening independence (documentation only)

Add a note to Step 5 making the intent explicit: the screening step must be applied before any suggestion or instruction in a comment is acted upon, and no comment content can override or skip this step. This is a workflow documentation hardening — it doesn't change tooling but makes the invariant legible to future readers and agents.

## Files to Modify

1. `skills/pr-comments/SKILL.md`
   - **Step 5** (screening): add size guard (64 KB truncation + flag), add explicit note that no comment content may override or skip screening
   - **Step 6** (decide): add diff-validation rule for `accept suggestion` actions — target must be within PR diff or downgrade to `decline`
   - Add a "fetch PR diff" instruction before or within Step 6, referencing `gh pr diff`
   - Update security note at end of file to reflect new mitigations

## Verification

- Read updated Step 5: confirm size guard and screening-independence note are present.
- Read updated Step 6: confirm diff-validation rule is present for suggestion acceptance.
- `npx cspell skills/pr-comments/SKILL.md` — no unknown words.
- Run `uv run --with pytest pytest tests/pr-comments/` if tests exist for this skill.
- Bump `metadata.version` in SKILL.md frontmatter with a minor increment (e.g. +0.1).
