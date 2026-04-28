=== SUMMARY ===
EVAL: 5 no-special-areas
CONFIG: without_skill (opus)

TOOLS_USED: Read: 0, Bash: 2, Write: 1, Other: none

GH_EDIT_COMMAND: did not run (simulation: no gh commands executed per instructions)

FINAL_PR_BODY (verbatim):
<<<BODY
## Summary

Adds bio and role display to the `UserCard` component so user profile cards now surface a short biography and role label in addition to the existing name and email.

## Changes

- `src/components/UserCard.tsx`: Render `user.bio` inside a `<p className="user-bio">` and `user.role` inside a `<span className="user-role">` directly below the existing email line.
- `src/components/UserCard.test.tsx` (new): Adds a React Testing Library test that renders `UserCard` with a fixture user and asserts that both the bio ("Engineer") and role ("admin") appear in the document.

## Rationale

Profile cards previously showed only name and email. Surfacing bio and role gives consumers of `UserCard` enough context to identify a user at a glance without clicking through to a full profile view.

## Review notes

- The new fields assume `User` already includes `bio: string` and `role: string`. Reviewers may want to confirm the `User` type definition matches and decide whether either field should be optional (and how the card should render when missing/empty).
- Styling hooks `user-bio` and `user-role` are added as new class names; no CSS is included in this PR. Confirm that styles are added in a follow-up or that existing global styles cover them.
- No escaping/sanitization is applied to `bio` or `role`. React escapes text children by default, so this is safe for plain strings, but worth a quick sanity check if either field can contain rich content from an untrusted source.

## Test plan

- [ ] `npm test -- UserCard` (or the project's equivalent) passes locally.
- [ ] Visually verify the card in the app/storybook with a representative user.
- [ ] Verify rendering when `bio` or `role` is empty/undefined behaves acceptably.
BODY>>>

NOTES: Baseline (without_skill) run. No skill invoked, no $WT/skills/pr-human-guide read, no gh commands executed (simulation only). Drafted an enhanced PR description with Summary / Changes / Rationale / Review notes / Test plan sections based solely on the inline diff. Flagged a couple of reviewer-relevant points (User type assumptions, missing styling, trivial XSS sanity check) without using a categorized human-guide template.
=== END SUMMARY ===
