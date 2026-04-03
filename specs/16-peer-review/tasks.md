# Tasks: Spec 16 — peer-review skill

## Phase 1: Skill Scaffolding

### SKILL.md
- [ ] Create `skills/peer-review/SKILL.md` with frontmatter: name `peer-review`, description including trigger phrases: "review my changes", "peer review", "check for consistency", "review this spec", "review staged", "review PR"
- [ ] Implement argument parsing section: `--staged`, `--pr N`, `--branch NAME`, path target, `--model MODEL` (default `opus`), `--focus TOPIC`
- [ ] Document the three review modes (diff, consistency, spec) and how they are auto-detected
- [ ] Define the reviewer subagent prompt template for each mode
- [ ] Define the output format (severity-grouped findings with apply prompt)
- [ ] Document the apply step (user selects findings to apply; skill makes edits)
- [ ] Add Notes section: fresh-context guarantee (subagent has no prior session context); `--focus` narrows scope but does not suppress other severity:critical findings

### Symlink
- [ ] `ln -s ../../skills/peer-review .claude/skills/peer-review`

### README
- [ ] Add `peer-review` row to the Available Skills table in `README.md`
- [ ] Add Skill Notes section with description and Eval cost placeholder

## Phase 2: Content Collection

### Target handlers (one task per type)
- [ ] **Staged**: `git diff --staged` — if empty, warn "no staged changes" and exit
- [ ] **Branch**: `git diff main...NAME` — if branch not found, error with available branches
- [ ] **PR**: `gh pr view N --json title,body,files` + `gh pr diff N` — if PR not found, error
- [ ] **Path**: read all files at path with `Read` tool; detect spec mode if path contains `plan.md` + `tasks.md`; detect consistency mode otherwise
- [ ] **No target**: same as `--staged`

## Phase 3: Reviewer Subagent

- [ ] Write the diff-mode prompt template (bugs, security, style, missing tests, behavioral regressions)
- [ ] Write the consistency-mode prompt template (stale references, terminology drift, missing parallel updates)
- [ ] Write the spec-mode prompt template (consistency + plan/tasks gaps, shell command correctness, internal math, implied-but-missing tasks)
- [ ] Apply `--focus` filter to prompt: prepend "Focus especially on [TOPIC]. Still report any critical issues outside this focus."
- [ ] Spawn subagent with `mode: "auto"`, pass content + template, receive structured findings
- [ ] Parse findings into severity buckets (critical/major/minor)

## Phase 4: Apply Step

- [ ] Present findings in the defined output format
- [ ] Prompt: `Apply all, select by number, or skip? [all/1,3,5/skip]`
- [ ] Output prompt as final message and stop generating — do not assume a default response
- [ ] On user reply: apply selected findings using `Edit` tool; report each change made
- [ ] If user replies `skip`: proceed to summary without changes

## Phase 5: Evals

- [ ] Create `evals/peer-review/evals.json` with 3 initial evals:
  - eval 1 `staged-diff-review`: staged change with a bug and a style issue; assert findings include both
  - eval 2 `spec-consistency-review`: spec pair with a plan/tasks mismatch; assert the mismatch is found
  - eval 3 `consistency-mode`: SKILL.md + reference file with a stale step reference; assert drift is found
- [ ] Run all 3 evals with_skill and without_skill
- [ ] Grade; confirm each eval has at least 1 failing assertion without_skill
- [ ] Create `evals/peer-review/benchmark.json` and `benchmark.md`
- [ ] Update `README.md` Eval Δ column and Eval cost note

## Phase 6: Verification

- [ ] `/peer-review` on staged changes → diff-mode findings returned
- [ ] `/peer-review specs/16-peer-review` → spec-mode findings (dogfood test — must find at least 1 issue or confirm clean)
- [ ] `/peer-review --pr N` → PR diff findings
- [ ] `/peer-review --focus consistency skills/pr-comments/` → consistency findings across skill files
- [ ] `uv run --with pytest pytest tests/` — all pass
- [ ] `npx cspell skills/peer-review/SKILL.md`
