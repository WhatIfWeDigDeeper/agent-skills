=== SUMMARY ===
EVAL: 7 data-model-changes
CONFIG: with_skill (sonnet)

TOOLS_USED: Read: 2, Bash: 4, Write: 2, Other: -

GH_EDIT_COMMAND:
gh pr edit 73 --body-file /tmp/claude-501/exec-sonnet-with-eval-7-tlTWUE/new-body.md

FINAL_PR_BODY (verbatim):
<<<BODY
Migrates user profile schema to v2 — renames username field and removes legacy data.

<!-- pr-human-guide -->
## Review Guide

> Areas identified by automated analysis as needing human judgment.
> This is not a complete review checklist — it highlights where your attention matters most.

### Data Model Changes
- [ ] [`migrations/20240312_user_profile_v2.sql`](https://github.com/owner/repo/pull/73/files#diff-706e5e7bec4712cda12744ddc0c34721c3e78792602909dee485336b62a1df3a) — Destructive migration: renames `username` to `display_name`, drops `legacy_id`, and adds `NOT NULL` to `bio` on an existing column. Verify backfill of `bio` for existing rows, rollback plan, and that all clients have been updated to the new field name before this runs.
- [ ] [`schema.graphql` (L8-13)](https://github.com/owner/repo/pull/73/files#diff-efc1675187620595b0844197a25c35eac9b6df752f9182e5cffddee6f27a8489) — Backwards-incompatible API contract changes: renames `username` to `displayName` and removes `legacyId`. Confirm no consumers still query the removed/renamed fields and that the migration is coordinated with this schema change.

<!-- /pr-human-guide -->
BODY>>>

NOTES: Both files cluster in Data Model Changes — strong elevated-concern signals (DROP COLUMN, removing nullable constraint, column rename without alias, removing field from API contract, backwards-incompatible field rename). No other categories apply: no auth/trust boundary (Security), no CI/IaC/env config (Config/Infra), no manifest changes (New Dependencies), migrations and GraphQL schema follow established conventions implied by file paths (Novel Patterns), no locking/shared mutable state (Concurrency). The migration line range is omitted since the entire 5-line file is the change. The schema.graphql range L8-13 covers the contiguous diff hunk.
=== END SUMMARY ===
