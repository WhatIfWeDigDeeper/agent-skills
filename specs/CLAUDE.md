# Specs

This file provides guidance when working in `specs/`. It auto-loads in Claude Code when you read or edit files in this directory.

Design specs live at `specs/<N>-<topic>/`, normally as a `plan.md` + `tasks.md` pair. The pre-flight check that runs *before* you start writing a spec ("verify the current version, line count, and recent commits for the skill") stays in the root `CLAUDE.md` under **Planning Workflow**, because it must fire before you touch anything under this directory.

## Rules

**Spec step numbers drift**: When editing or reviewing specs for an existing skill, verify step numbers (e.g. "Step 5", "Step 6") against the current SKILL.md — they shift as skills evolve and specs can silently fall out of sync.

**Check off spec tasks as you complete them**: When working through a `specs/*/tasks.md`, mark each `- [ ]` item as `- [x]` immediately after completing it — do not batch updates at the end.

**When editing a spec that has both `plan.md` and `tasks.md`**, apply every fix to both files in the same pass and re-read both before finishing — a fix applied to only one file is incomplete and will require a follow-up consistency pass to catch what was missed.

**Update a spec's embedded copy of a real file (test snippet, verification command) in the same commit as the file** — a re-runner follows the spec, not the code.

**After implementing review suggestions to spec files**, re-read all modified files before reporting done — catch consistency gaps yourself rather than leaving them for the next review round. For plan/tasks pairs, re-read both files end-to-end even when only one was edited.

**Use phrase anchors, not line numbers, when referencing locations in files under active development** — hardcoded line numbers shift the moment the first edit lands. Write "find the sentence containing 'X'" rather than "edit line N." This applies to spec task descriptions referencing benchmark.md, SKILL.md, or any file that will be edited in the same phase.
