# Tasks: Redesign Interactive Help Flow

Two agents can work in parallel — one per skill. All files are independent across skills.

---

## Agent 1 — uv-deps

### Task 1a: Rewrite `skills/uv-deps/references/interactive-help.md`
Replace multi-select Q2a and Q2b with the new single-select questions from the plan.
- Q1: Update dependencies (Recommended) | Security fixes only
- Q2a (if Update): Patch + Minor (Recommended) | Patch only | Patch + Minor + Major
- Q3 (after Q2a, only if "Patch + Minor" or "Patch + Minor + Major" was selected — omit for "Patch only" since x.y.0 is a minor bump, not a patch): Yes, skip x.y.0 (Recommended) | No, include x.y.0
- Q2b (if Security): Critical + High (Recommended) | Critical only | Critical + High + Moderate | All
- Update "After Selection" to map the new answer values to filter behavior.

### Task 1b: Update `skills/uv-deps/references/update-workflow.md`
In the "Apply Version Filters" section, replace the independent Major/Minor/Patch toggle logic with:
- "Patch only": include packages where only the patch version differs
- "Patch + Minor" (default): include patch and minor version updates
- "Patch + Minor + Major": include all updates
- Skip x.y.0 logic is unchanged — it's now a separate Q3 answer, not a checkbox modifier

Tasks 1a and 1b are independent and can be done in either order.

---

## Agent 2 — js-deps

### Task 2a: Create `skills/js-deps/references/interactive-help.md`
New file mirroring the uv-deps structure but adapted for JS (npm/yarn/pnpm/bun).
- Same branching flow with up to 3 questions as the new uv-deps interactive-help.md
- Swap Python/uv references for JS/package manager equivalents
- Include the note: if package arguments were provided, they are already set

### Task 2b: Update `skills/js-deps/SKILL.md` and delete `options.md`
- Change the `--help` / `-h` / `?` routing line to: `Read references/interactive-help.md`
- Change the "Ambiguous" routing line to: `Read references/interactive-help.md`
- Delete `skills/js-deps/references/options.md` (superseded by interactive-help.md)

Task 2b depends on 2a (interactive-help.md must exist before SKILL.md points to it).

### Task 2c: Update `skills/js-deps/references/update-workflow.md`
In the "Discover What Needs Updating" section, document the tiered filter model:
- "Patch only": include packages where only the patch version differs
- "Patch + Minor" (default): include patch and minor version updates
- "Patch + Minor + Major": include all updates
- Skip x.y.0: separate question, same logic as uv-deps

Task 2c is independent of 2a and 2b.

---

## Verification (after both agents complete)

- Read each modified/created file and confirm it matches the plan
- Confirm `js-deps/SKILL.md` routes both `--help` and "Ambiguous" to `interactive-help.md`
- Confirm `options.md` is deleted
- Confirm filter logic in both `update-workflow.md` files uses tiered language, not toggle language
- Confirm uv-deps and js-deps `interactive-help.md` files are structurally consistent
