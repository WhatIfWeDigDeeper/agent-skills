Plan: Redesign Interactive Help Flow for js-deps and uv-deps
Context
Both skills support an interactive help mode when invoked ambiguously (no clear intent). The current uv-deps interactive-help uses multi-select questions for version filters and severity levels, which is harder to reason about than a tiered single-select. js-deps has no interactive-help at all, only keyword-based routing.

The goal is to redesign both skills' interactive flows to use single-select questions with a recommended option pre-selected (listed first, labeled "(Recommended)"). This makes the workflow more opinionated and easier to use.

New Interactive Flow Design
Q1 — Workflow type (single select)

Update dependencies (Recommended)
Security fixes only
Q2a — Version scope (single select, shown if "Update dependencies" selected)

Patch + Minor (Recommended)
Patch only
Patch + Minor + Major
Q3 — Skip x.y.0 releases (single select, shown after Q2a only if "Patch + Minor" or "Patch + Minor + Major" was selected — skip this question for "Patch only" since x.y.0 is a minor bump, not a patch)

Yes, skip x.y.0 — wait for x.y.1+ bug fixes (Recommended)
No, include x.y.0 releases
Q2b — Severity scope (single select, shown if "Security fixes only" selected)

Critical + High (Recommended)
Critical only
Critical + High + Moderate
All: Critical + High + Moderate + Low
Files to Modify
1. skills/uv-deps/references/interactive-help.md — Full rewrite
Replace multi-select Q2a (Major/Minor/Patch/Skip checkboxes) and Q2b (Critical/High/Moderate checkboxes) with the new single-select questions above. Update "After Selection" to describe how the new filter values map to update behavior.

2. skills/uv-deps/references/update-workflow.md — Update filter logic
The "Apply Version Filters" section currently describes independent Major/Minor/Patch toggles. Update to reflect the new tiered single-select:

"Patch only": include packages where only the patch version differs
"Patch + Minor" (default): include patch and minor version updates
"Patch + Minor + Major": include all updates
Skip x.y.0 logic stays the same (it's now a separate answer, not a checkbox)
3. skills/js-deps/references/interactive-help.md — New file
Create this file, mirroring the uv-deps structure but adapted for JS (npm/yarn/pnpm/bun). Use the same 3-question flow. Mention that package arguments, if provided, are already set.

4. skills/js-deps/SKILL.md — Update routing to interactive-help.md; delete options.md
The "Ambiguous" routing case already exists but points to references/options.md. Update both routing lines to point to references/interactive-help.md instead:

- The --help / -h / ? line (currently: Read references/options.md)
- The Ambiguous line (currently: Read references/options.md to present the interactive help flow)

Both should read: Read references/interactive-help.md

Then delete references/options.md — it is fully superseded by the new interactive-help.md.
5. skills/js-deps/references/update-workflow.md — Update filter language
Update the "Discover What Needs Updating" section filter description from "major/minor/patch" toggles to the new tiered model.

Verification
Read each updated file after editing to confirm correctness
Verify js-deps/SKILL.md routes to interactive-help.md for ambiguous invocations
Check that the update-workflow.md filter logic in both skills aligns with the new single-select answer values
