=== SUMMARY ===
EVAL: 7 data-model-changes
CONFIG: without_skill (opus)

TOOLS_USED: Read: 0, Bash: 2, Write: 1, Other: none

GH_EDIT_COMMAND: gh pr edit 73 --body-file /tmp/claude-501/exec-opus-without-eval-7-TUm3sN/pr-body.md

FINAL_PR_BODY (verbatim):
<<<BODY
Migrates user profile schema to v2 — renames username field and removes legacy data.

---

## Review Guide

This PR contains a **destructive database migration** combined with a **breaking GraphQL schema change**. Reviewers should focus carefully on the items below before approving.

### Areas needing careful attention

#### 1. Destructive / irreversible data migration (`migrations/20240312_user_profile_v2.sql`)
- `ALTER TABLE users DROP COLUMN legacy_id` — **data loss**. Once this runs in production, `legacy_id` values are gone. Confirm:
  - No code path (services, jobs, analytics, BI, exports) still reads `legacy_id`.
  - Data has been backfilled into a replacement column (or archived) if it is still needed.
  - There is a rollback / recovery plan (backup snapshot, point-in-time recovery window) before this lands.
- `ALTER TABLE users RENAME COLUMN username TO display_name` — breaks any consumer still selecting `username`. Confirm a coordinated deploy order (or a transitional view/alias) so old app instances don't error during rollout.
- `ALTER TABLE users ALTER COLUMN bio SET NOT NULL` — will **fail** if any existing row has `bio IS NULL`. Verify a backfill/default has been applied first, or this migration will halt mid-way and leave the schema in a partially-applied state.
- The migration file has **no transaction wrapper and no down-migration**. Consider whether each statement should be in its own transaction (some DDL in Postgres can't be combined) and whether a reverse migration is required by the team's policy.

#### 2. Breaking GraphQL schema change (`schema.graphql`)
- `username: String!` → `displayName: String!` is a **breaking change** for every API client (web, mobile, third-party). Confirm:
  - All clients have been updated, or a deprecation window with both fields exposed is in place.
  - Mobile apps in particular — old installed versions cannot be force-updated and will break on the next query.
- `legacyId: Int` removed — same concern; any client still requesting it will get a query validation error.
- No deprecation directives (`@deprecated(reason: "...")`) were used as a transitional step. Worth discussing whether this should be a two-phase rollout.

#### 3. Resolver / application-layer alignment (not visible in this diff)
The diff only shows SQL + schema. Reviewers should verify (or ask the author to confirm) that the corresponding changes exist:
- Resolvers / ORM models updated to map `display_name` ↔ `displayName`.
- All references to `username` and `legacyId` removed from the codebase.
- Tests updated; integration tests cover the new field name.

#### 4. Deploy coordination
Because this combines a destructive DB migration with a breaking API change, the order matters:
1. Backfill `bio` so the `NOT NULL` constraint is safe.
2. Deploy app code that handles both `username` and `display_name` (read either, write new).
3. Run the migration.
4. Deploy app code that uses only `display_name`.
5. Roll the GraphQL schema change once all clients are updated.

If the plan is to do all of this in a single deploy, that's worth flagging explicitly so reviewers can weigh the risk.

### Lower-risk areas
- The migration filename follows the project's date-prefixed convention.
- The GraphQL diff is minimal and easy to read.

### Suggested reviewers
- A backend engineer familiar with the `users` table and any downstream consumers.
- Someone from the API/clients side who can confirm mobile and third-party impact.
BODY>>>

NOTES: Did not invoke any skills per strict prohibitions. Did not execute the gh command (simulation). The proposed body preserves the existing one-line description, then appends a structured review guide focused on data-model and schema-breaking concerns visible in the diff (destructive DROP COLUMN, NOT NULL backfill risk, breaking GraphQL field rename/removal, and deploy ordering).
=== END SUMMARY ===
