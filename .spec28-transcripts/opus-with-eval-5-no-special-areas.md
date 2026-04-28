=== SUMMARY ===
EVAL: 5 no-special-areas
CONFIG: with_skill (opus)

TOOLS_USED: Read: 2, Bash: 2, Write: 1, Other: 

GH_EDIT_COMMAND: gh pr edit 101 --body-file "$TMPFILE"

FINAL_PR_BODY (verbatim):
<<<BODY
Adds bio and role display to UserCard component.

<!-- pr-human-guide -->
## Review Guide

No areas requiring special human review attention were identified.

<!-- /pr-human-guide -->
BODY>>>

NOTES: Diff is a routine additive UI change in src/components/UserCard.tsx (renders user.bio and user.role) plus a new test file UserCard.test.tsx. No security/auth boundaries, no config/infra files, no new dependencies, no schema/API contract changes, no concurrency primitives, and the pattern follows existing component conventions. Test files are excluded by the selectivity threshold. Therefore zero items flagged across all six categories — emitted the empty-guide variant per Step 4. Existing PR body does not contain the pr-human-guide marker, so the guide is appended with a blank-line separator (Step 5 "If it does not exist" branch). SHA-256 anchors computed for completeness: UserCard.tsx -> 6d745e69d6b0f04b7ef63fa623c62cd79873b48acb57af4a2b71fdc411ecd1a9; UserCard.test.tsx -> ff07ff30b7f3745d8010acbcdb0b4865c6d5cfb935dca7599f142acd09ceffe0 (unused since no items were flagged). Body written to a temp file ($TMPFILE) and applied via --body-file per skill guidance to avoid zsh corruption of the <!-- markers.
=== END SUMMARY ===
