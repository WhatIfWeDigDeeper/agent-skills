=== SUMMARY ===
EVAL: 7 data-model-changes
CONFIG: with_skill (opus)

TOOLS_USED: Read: 2, Bash: 4, Write: 2, Other: none

GH_EDIT_COMMAND: gh pr edit 73 --body-file "$TMPFILE"

FINAL_PR_BODY (verbatim):
<<<BODY
Migrates user profile schema to v2 — renames username field and removes legacy data.

<!-- pr-human-guide -->
## Review Guide

> Areas identified by automated analysis as needing human judgment.
> This is not a complete review checklist — it highlights where your attention matters most.

### Data Model Changes
- [ ] [`migrations/20240312_user_profile_v2.sql` (L1-5)](https://github.com/owner/repo/pull/73/files#diff-706e5e7bec4712cda12744ddc0c34721c3e78792602909dee485336b62a1df3a) — Destructive migration: drops `legacy_id` column, renames `username` → `display_name` without alias, and adds NOT NULL to existing `bio` column (will fail if any row has NULL bio); verify backfill, rollback plan, and behavior under concurrent traffic
- [ ] [`schema.graphql` (L8-13)](https://github.com/owner/repo/pull/73/files#diff-efc1675187620595b0844197a25c35eac9b6df752f9182e5cffddee6f27a8489) — Breaking GraphQL API change: renames `username` → `displayName` and removes `legacyId` field; confirm all clients are migrated before merge

<!-- /pr-human-guide -->
BODY>>>

NOTES: Both files classified under Data Model Changes — the SQL migration hits multiple elevated-concern signals (DROP COLUMN, rename without alias, removing nullable from existing column) and the GraphQL change is a breaking API contract change (rename + field removal). No other categories triggered. Did not execute gh; constructed the gh pr edit command per skill Step 5 (--body-file via mktemp). PR body was appended (no existing pr-human-guide markers in the original description).
=== END SUMMARY ===
