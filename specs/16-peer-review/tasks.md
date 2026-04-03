# Tasks: Spec 16 — peer-review skill

## Phase 1: Skill Scaffolding

### SKILL.md
- [x] Create `skills/peer-review/SKILL.md` with frontmatter: name `peer-review`, description including trigger phrases: "review my changes", "peer review", "check for consistency", "review this spec", "review staged", "review PR"
- [x] Implement argument parsing section: `--staged`, `--pr N`, `--branch NAME`, path target, `--model MODEL` (default `claude-opus-4-6`), `--focus TOPIC`
- [x] Document the three review modes (diff, consistency, spec) and how they are auto-detected
- [x] Define the reviewer subagent prompt template for each mode
- [x] Define the output format (severity-grouped findings with apply prompt)
- [x] Document the apply step (user selects findings to apply; skill makes edits)
- [x] Add Notes section: fresh-context guarantee (subagent has no prior session context); `--focus` narrows scope but does not suppress `critical` findings outside the focus area; relationship to `code-review` (single reviewer vs multi-persona, lighter weight, multi-LLM routing in Phase II)

### Symlink
- [x] `ln -s ../../skills/peer-review .claude/skills/peer-review`

### README
- [x] Add `peer-review` row to the Available Skills table in `README.md`
- [x] Add Skill Notes section with description, Eval cost placeholder, and a "vs `code-review`" note (single reviewer / lighter weight / multi-LLM routing in Phase II)

### Reference
- [x] Note `specs/16-peer-review/copilot-staged-review.sh` in the Phase II section of SKILL.md as a prototype for the Copilot CLI integration path (staged-only, `high|medium|low` severity — to be generalized in Phase II)

## Phase 2: Content Collection

### Target handlers (one task per type)
- [x] **Staged**: `git diff --staged` — if empty, warn "no staged changes" and exit
- [x] **Branch**: `git diff main...NAME` — if branch not found, error with available branches
- [x] **PR**: `gh pr view N --json title,body,files` + `gh pr diff N` — if PR not found, error; title+body prepended as context, diff is the review content
- [x] **Path**: read all files at path with `Read` tool; detect spec mode if the resolved directory contains both `plan.md` and `tasks.md`; detect consistency mode otherwise
- [x] **Conflict**: if both `--staged` and a path are provided, error: "specify one target at a time"
- [x] **No target**: same as `--staged` (fall through to staged handler)

## Phase 3: Reviewer Subagent

- [x] Write the diff-mode prompt template (bugs, security, style, missing tests, behavioral regressions)
- [x] Write the consistency-mode prompt template (stale references, terminology drift, missing parallel updates)
- [x] Write the spec-mode prompt template (consistency + plan/tasks gaps, shell command correctness, internal math, implied-but-missing tasks)
- [x] Apply `--focus` filter to prompt: prepend "Focus especially on [TOPIC]. Still report any critical issues outside this focus area."
- [x] Spawn subagent with `mode: "auto"`, pass content + template, receive structured findings
- [x] Parse findings into severity buckets (critical/major/minor)

## Phase 4: Apply Step

- [x] Present findings in the defined output format
- [x] If findings list is empty: output "No issues found." and stop — no apply prompt needed
- [x] Otherwise: prompt `Apply all, select by number, or skip? [all/1,3,5/skip]` — output as final message and stop generating; do not assume a default response
- [x] On user reply: apply selected findings using `Edit` tool; report each change made
- [x] If user replies `skip`: output summary of skipped count without making changes

## Phase 5: Evals

- [x] Create `evals/peer-review/evals.json` with 3 initial evals:
  - eval 1 `consistency-mode-stale-step-ref`: fixture SKILL.md + reference.md with stale step reference
  - eval 2 `spec-mode-plan-tasks-mismatch`: spec pair missing --verbose task
  - eval 3 `staged-no-changes-exit`: --staged with no staged changes → graceful exit
- [x] Run all 3 evals with_skill and without_skill
- [x] Grade; evals 1 and 2 have failing assertions without_skill (eval 3 is non-discriminating — documented in benchmark.md)
- [x] Create `evals/peer-review/benchmark.json` and `benchmark.md`
- [x] Update `README.md` Eval Δ column (+13%) and Eval cost note

## Phase 6: Verification

- [x] `/peer-review` on staged changes → verified via eval 3 (no staged changes path works; staged diff path pending until PR branch has staged changes)
- [x] `/peer-review specs/16-peer-review` → spec-mode findings returned (2 major, 5 minor — dogfood works)
- [ ] `/peer-review --pr N` → PR diff findings (pending — no PR created yet)
- [x] `/peer-review --focus consistency skills/pr-comments/` → 5 real consistency findings returned across skill files
- [x] `uv run --with pytest pytest tests/` — 561 passed
- [x] `npx cspell skills/peer-review/SKILL.md` — clean
