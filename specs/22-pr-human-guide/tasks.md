# Spec 22: Tasks — pr-human-guide

## Phase 1: Skill Scaffolding

- [x] **1.1** Create directory `skills/pr-human-guide/`
- [x] **1.2** Create `skills/pr-human-guide/SKILL.md` with:
  - YAML frontmatter: `name`, `description` (with trigger phrases), `license: MIT`, `compatibility` (requires git, gh, jq), `metadata` with author/repository/version `"0.1"`
  - `## Arguments` section — PR number (optional; auto-detects from current branch if omitted), `--help` routing
  - `## Process` with 6 numbered steps (see plan.md)
  - `## Notes` section covering: scope (not a code review, not a blocker), novel-pattern detection approach, idempotent re-run behavior, relationship to peer-review and pr-comments
- [x] **1.3** Create symlink: `ln -s ../../skills/pr-human-guide .claude/skills/pr-human-guide`

---

## Phase 2: Review Categories Reference File

- [x] **2.1** Create `skills/pr-human-guide/references/categories.md` defining the 6 review categories with:
  - Detection signals for each category (file name patterns, code patterns, import patterns)
  - Examples of what qualifies vs. what doesn't
  - Guidance on consolidating multiple hits in the same file/category
- [x] **2.2** Link to `references/categories.md` from the relevant step in SKILL.md

---

## Phase 3: Evals

- [x] **3.1** Create `evals/pr-human-guide/` directory
- [x] **3.2** Create `evals/pr-human-guide/evals.json` with at least 6 evals covering:
  - **Eval 1** (`security-changes`): PR diff containing auth/token changes → guide includes Security category
  - **Eval 2** (`config-changes`): PR diff with CI pipeline or Dockerfile changes → guide includes Config/Infrastructure category
  - **Eval 3** (`new-dependency`): PR diff adding a new npm/pip package → guide includes New Dependencies category
  - **Eval 4** (`novel-pattern`): PR diff introducing a pattern not in the existing codebase → guide includes Novel Patterns category
  - **Eval 5** (`no-special-areas`): PR diff with routine business logic changes → guide outputs "no areas requiring special human review attention"
  - **Eval 6** (`idempotent-rerun`): PR that already has a `<!-- pr-human-guide -->` block in its description → guide replaces the block rather than appending a second one
- [x] **3.3** Run evals (with_skill and without_skill) immediately after creating evals.json — do not wait for user instruction
- [x] **3.4** Create `evals/pr-human-guide/benchmark.json` with results from 3.3
- [x] **3.5** Create `evals/pr-human-guide/benchmark.md` with human-readable summary

---

## Phase 4: Documentation

- [x] **4.1** Add `pr-human-guide` to the Available Skills table in `README.md`:
  - Table row: name, description, trigger phrases, eval delta
  - Skill Notes section: what it does, what it doesn't do, eval cost bullet
- [x] **4.2** Add `pr-human-guide` to the Available Skills table in `CLAUDE.md` (trigger phrases: "review guide", "human review guide", "prep for review", "flag for review")
- [x] **4.3** Add the corresponding entry to `.github/copilot-instructions.md` (mirror of CLAUDE.md change per project convention)

---

## Phase 5: Verification

- [x] **5.1** Run `npx cspell skills/pr-human-guide/SKILL.md` — fix any unknown words in `cspell.config.yaml`
- [x] **5.2** Run `uv run --with pytest pytest tests/` — verify no regressions (678 passed)
- [x] **5.3** Re-read `skills/pr-human-guide/SKILL.md` end-to-end — verify all 6 steps are complete and reference the categories reference file
- [x] **5.4** Re-read both `plan.md` and `tasks.md` end-to-end — verify consistency between the two files
