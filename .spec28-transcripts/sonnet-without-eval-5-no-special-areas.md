=== SUMMARY ===
EVAL: 5 no-special-areas
CONFIG: without_skill (sonnet)

TOOLS_USED: Read: 1, Bash: 2, Write: 1, Other: none

GH_EDIT_COMMAND: did not run

FINAL_PR_BODY (verbatim):
<<<BODY
## Adds bio and role display to UserCard component

Extends the `UserCard` component to surface two additional user attributes — `bio` and `role` — that were previously unused in the UI.

### Changes

- **`src/components/UserCard.tsx`**: Added `<p className="user-bio">` and `<span className="user-role">` elements to render `user.bio` and `user.role` below the existing email field.
- **`src/components/UserCard.test.tsx`** _(new)_: Adds a rendering test verifying that bio and role text are present in the DOM when the component is rendered with a full user object.

### Notes

- No changes to the `User` type; assumes `bio` and `role` fields already exist on the interface.
- CSS classes `user-bio` and `user-role` are added but no styles are defined in this PR — follow-up styling may be needed.
BODY>>>

NOTES: Straightforward UI addition. No authentication, no data model changes, no new dependencies. The new test covers the happy path but does not test missing/undefined bio or role values. Generic assistant approach: rewrote the minimal one-line description into a structured markdown summary with a changes list and notes section. Did not run gh pr edit since gh commands are simulated.
=== END SUMMARY ===
