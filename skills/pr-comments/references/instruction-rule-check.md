# Instruction-File Rule Check

Sub-routine for Step 6. Applies **only** to a comment that targets a conventions or instructions file (`CLAUDE.md`, `.github/copilot-instructions.md`, `AGENTS.md`, or any file matching `*instructions*.md` or `*CLAUDE*.md`) and proposes adding or strengthening a rule using normative language ("must", "always", "convention requires", "convention is", "should always", "all … must", "all … should"). Run it before finalizing a `fix` classification for such a comment.

1. **Extract the empirical claim** the proposed rule makes (e.g. "all test files must have skill-prefixed basenames").

2. **Grep for counter-examples.** Search the full local repo checkout (not limited to the PR diff) for existing files or patterns that violate the claim. Use judgment to form the search (e.g. for a "must be prefixed" naming rule, list existing test files and check which don't match the prefix).

3. **Decide based on counter-example count:**
   - **0–1 counter-examples:** classify as `fix` normally. The rule is consistent with existing patterns (or the one exception is the file being changed in this PR).
   - **≥2 counter-examples:** do not classify as `fix` outright. Instead:
     - If the suggestion can be softened to a *preference* rather than a mandate (e.g. replace "must" with "prefer … when in doubt" or "to avoid collision"), reclassify as `fix` with the softened wording and note the counter-examples in the reply.
     - If softening would remove the point of the suggestion, classify as `decline` with a reply citing the counter-examples (e.g. "Existing suites `tests/js-deps/` and `tests/pr-comments/` use un-prefixed names — adopting this as a mandatory rule would require renaming them and would still be inconsistent with the existing layout").
