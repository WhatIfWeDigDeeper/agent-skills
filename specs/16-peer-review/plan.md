# Spec 16: peer-review skill

## Problem

There is no structured way to get a fresh-perspective review of in-progress work in this repo. Reviewers (human or bot) see the diff in a PR, but by then the author has deep context that makes it hard to spot consistency gaps, underspecification, or drift between related files. The need surfaces in three distinct situations:

1. **Spec review** — after drafting or editing a `specs/<NN>-<topic>/plan.md` + `tasks.md` pair, check for internal consistency, gaps, and underspecification before implementation starts.

2. **Change consistency review** — after editing a set of related files (e.g. `SKILL.md` + reference files + `evals.json`), check that terminology, step numbers, and behavioral descriptions are still in sync across all of them.

3. **Code/diff review** — before opening a PR, review staged changes, a branch diff, or an existing PR for bugs, style issues, security problems, and missing tests.

All three share the same core need: a **fresh-context reviewer** that hasn't accumulated session assumptions, given a well-structured prompt tuned to the target type, returning findings in a consistent format the author can triage and apply.

---

## Design

### Invocation

```
/peer-review [target] [--model MODEL] [--focus TOPIC]
```

**Targets:**
| Syntax | What is reviewed |
|--------|-----------------|
| *(no target)* | Staged changes (`git diff --staged`) |
| `--staged` | Same as no target — explicit form |
| `--pr N` | PR #N diff + description |
| `--branch NAME` | Branch vs the default branch (`git diff origin/HEAD...NAME`) |
| `path/to/file-or-dir` | Specific files or directory (consistency review) |

**Options:**
- `--model MODEL` — override reviewer model (default: `claude-opus-4-6`; phase II: `--model copilot`, `--model codex`, `--model gemini` routes to the respective CLI with optional sub-model, e.g. `--model copilot:gpt-4o-mini`)
- `--focus TOPIC` — narrow the review scope (e.g. `--focus security`, `--focus consistency`, `--focus evals`); narrows emphasis but does **not** suppress `critical` findings outside the focus area

### Review modes (auto-detected from target)

The skill selects a prompt template based on what it's reviewing:

**Diff mode** (staged, branch, PR): look for bugs, security issues, missing tests, style violations, unintended behavioral changes. Return findings grouped by severity.

**Consistency mode** (file/dir path): look for drift between related files — stale step references, mismatched terminology, missing parallel updates, underspecified tasks. Especially useful after editing spec pairs or SKILL.md + reference files together.

**Spec mode** (path resolves to a directory containing both `plan.md` and `tasks.md`): additionally check for gaps between `plan.md` and `tasks.md`, underspecified task items, incorrect shell commands, internal math errors, and missing tasks that the plan implies.

### Workflow

1. **Parse target** — determine target type and collect content:
   - Staged/branch/PR: run the appropriate `git diff` or `gh pr diff` command
   - File/dir path: read all files at the path; if the directory contains both `plan.md` and `tasks.md`, treat as spec mode; otherwise consistency mode
   - Conflict: if both `--staged` and a file path are provided, error with "specify one target at a time"
2. **Select prompt template** — choose diff/consistency/spec based on target type; apply `--focus` filter if provided
3. **Spawn fresh-context reviewer subagent** — pass collected content + prompt; use `mode: "auto"` to suppress approval prompts
4. **Receive findings** — structured as: severity (critical/major/minor), location (file + phrase anchor), description, suggested fix
5. **Present findings** — display to user grouped by severity; if findings list is empty, output "No issues found." and stop. Otherwise output the findings and ask: `Apply all, select by number, or skip? [all/1,3,5/skip]` — output this as your final message and **stop generating**; do not assume a default or proceed to the next step without a user reply
6. **Apply approved findings** — make the edits using the `Edit` tool; report each change made

### Reviewer prompt structure

The subagent receives:

```
You are reviewing [target description] for [review mode].

[File contents or diff]

Return a structured list of issues grouped by severity (critical/major/minor).
For each issue include:
- What the problem is (be specific, quote the problematic text)
- Where it is (file + phrase anchor — do not use line numbers)
- What the fix should be

Do NOT implement any changes. Return findings only.
```

For consistency/spec mode, the prompt also includes: "Check that related files are in sync with each other — stale references, mismatched terminology, missing parallel updates."

### Output format

```
## Peer Review — [target] ([model])

### Critical
1. **[Issue title]** — `[file]`
   [Description]
   Fix: [specific change]

### Major
...

### Minor
...

---
Apply all, select by number, or skip? [all/1,3,5/skip]
```

---

## Phase II: Multi-LLM support

When `--model copilot[:<submodel>]`, `--model codex`, or `--model gemini` is specified:
- Detect whether the CLI tool is available (`which copilot`, `which codex`, etc.); error with installation hint if not found
- Pipe the review prompt to the appropriate CLI; pass the sub-model flag when provided (e.g. `copilot -m gpt-4o-mini`)
- Parse output into the standard findings format (critical/major/minor)

`copilot-staged-review.sh` in this spec directory is a prototype for the Copilot CLI path. It is staged-only and outputs `high|medium|low` severity — Phase II will generalize it to all target types and align severity to `critical/major/minor`. It is not used by Phase I.

This is deferred to phase II because the CLI interfaces differ significantly and require individual integration work. The v1 Opus-via-subagent approach covers the primary use case.

---

## Relationship to `code-review`

`code-review` spawns multiple subagents with distinct reviewer personas (security, correctness, style, etc.), making it thorough but relatively expensive — best suited for full PR reviews before merge.

`peer-review` uses a single fresh-context reviewer and is optimized for lighter, faster checks: mid-draft spec validation, quick consistency sweeps, and staged-change review before opening a PR. Its key differentiator is multi-LLM routing (Phase II) — the reviewer can be Copilot, Codex, or Gemini rather than a Claude subagent, which is useful when the author wants a non-Claude perspective or needs a specific model.

---

## Verification

After implementation:
1. `/peer-review` on staged changes → returns diff-mode findings
2. `/peer-review specs/16-peer-review` → returns spec-mode findings (dogfood test)
3. `/peer-review --pr N` → returns PR diff findings
4. `/peer-review --focus consistency skills/pr-comments/` → returns consistency findings across skill files
5. `npx cspell skills/peer-review/SKILL.md`
