=== SUMMARY ===
EVAL: 7 data-model-changes
CONFIG: with_skill (sonnet)

TOOLS_USED: Read: 3, Bash: 3, Write: 1, Other: none

GH_EDIT_COMMAND: gh pr edit 73 --body-file "${TMPDIR:-/private/tmp}/pr-human-guide-XXXXXX"

FINAL_PR_BODY (verbatim):
<<<BODY
Migrates user profile schema to v2 — renames username field and removes legacy data.

<!-- pr-human-guide -->
## Review Guide

> Areas identified by automated analysis as needing human judgment.
> This is not a complete review checklist — it highlights where your attention matters most.

### Data Model Changes
- [ ] [`migrations/20240312_user_profile_v2.sql` (L2-4)](https://github.com/owner/repo/pull/73/files#diff-706e5e7bec4712cda12744ddc0c34721c3e78792602909dee485336b62a1df3a) — Three elevated-risk changes: column rename (`username` → `display_name`) with no backward-compatibility alias, irreversible `DROP COLUMN legacy_id`, and removing nullable constraint on `bio` for existing rows
- [ ] [`schema.graphql` (L8-11)](https://github.com/owner/repo/pull/73/files#diff-efc1675187620595b0844197a25c35eac9b6df752f9182e5cffddee6f27a8489) — Breaking API contract changes: `username` field removed and replaced with `displayName` (existing clients will break), `legacyId` field removed from response schema

<!-- /pr-human-guide -->
BODY>>>

NOTES: Both changed files trigger Data Model Changes with multiple elevated-concern signals each. The SQL migration has three elevated signals: column rename (no alias), DROP COLUMN (irreversible), and ALTER COLUMN SET NOT NULL on an existing column. The GraphQL schema has two: removing a field from the API response (username -> displayName rename is a breaking change for existing clients) and removing legacyId. No other categories (Security, Config/Infrastructure, New Dependencies, Novel Patterns, Concurrency/State) apply. The gh pr edit command would write the body to a temp file using --body-file to avoid zsh ! expansion issues with the HTML comment markers.
=== END SUMMARY ===
