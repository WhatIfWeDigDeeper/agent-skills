=== SUMMARY ===
EVAL: 5 no-special-areas
CONFIG: with_skill (sonnet)

TOOLS_USED: Read: 3, Bash: 2, Write: 0, Other: none

GH_EDIT_COMMAND: gh pr edit 101 --body-file "${TMPDIR:-/private/tmp}/pr-human-guide-XXXXXX"

FINAL_PR_BODY (verbatim):
<<<BODY
Adds bio and role display to UserCard component.

<!-- pr-human-guide -->
## Review Guide

No areas requiring special human review attention were identified.

<!-- /pr-human-guide -->
BODY>>>

NOTES: Diff is a pure presentational change (renders user.bio and user.role inside existing JSX) plus a routine RTL test file. No security boundary is crossed — user.role is displayed as a label, not used for an authorization decision. Test file is excluded by the Selectivity Threshold (no security fixtures, no production code-path effect). No config/infra, no new dependencies, no data model change, no novel pattern (consistent with existing JSX/className conventions in the same file), no concurrency. Emitted the "no areas" body per SKILL.md Step 4. SHA-256 anchors computed but not needed since no items were flagged.
=== END SUMMARY ===
