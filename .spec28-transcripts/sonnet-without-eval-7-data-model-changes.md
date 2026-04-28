=== SUMMARY ===
EVAL: 7 data-model-changes
CONFIG: without_skill (sonnet)

TOOLS_USED: Read: 0, Bash: 2, Write: 1, Other: none

GH_EDIT_COMMAND: did not run

FINAL_PR_BODY (verbatim):
<<<BODY
Migrates user profile schema to v2 — renames username field and removes legacy data.

---

## Review Guide

### Data Model Changes ⚠️ Needs careful review

- **Irreversible column rename** (`username` → `display_name`): This is a destructive, non-revertible migration. Any rollback would require a second migration renaming back. Verify there are no direct SQL queries, ORMs, or data exports still referencing `username` that would silently break.
- **Column drop** (`legacy_id`): `ALTER TABLE users DROP COLUMN legacy_id` permanently deletes data. Confirm the legacy_id data is no longer needed and has been fully migrated or archived if applicable.
- **`bio` made NOT NULL**: This will fail if any existing rows have `bio = NULL` at migration time. Verify all existing rows have a non-null `bio` before running, or add a default value (`SET DEFAULT ''`) to the migration.
- **GraphQL breaking change**: Removing `username` and `legacyId` from the `User` type and adding `displayName` is a breaking API change. Any clients querying these fields will error. Confirm all consumers (web, mobile, third-party integrations) have been updated or that a deprecation window was observed.
- **No down migration**: The SQL file has no rollback (`ALTER TABLE ... RENAME COLUMN display_name TO username` etc.). Confirm this is intentional and deployment runbooks account for it.
BODY>>>

NOTES: No skill invoked (baseline run). Analysis was done manually from the diff. Identified: destructive SQL migration (rename, drop, NOT NULL constraint), breaking GraphQL schema change, missing rollback path. All are data-model / breaking-change concerns requiring careful human review. Did not call `gh` as per simulation constraints.
=== END SUMMARY ===
