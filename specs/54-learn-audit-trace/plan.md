# Spec 54: learn — Make the Min-Chars Audit Emit a Trace

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps in `tasks.md` use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the `learn` skill's "minimum viable rule text" audit produce an inspectable artifact in the plan output, so a skipped audit is visible to the user before anything is written to disk.

**Architecture:** Promote the audit from a preamble paragraph inside the Present-Plan step to its own numbered step with a per-clause procedure, and add a `Cut in audit:` field to the plan template that carries the audit's result. Structural regression tests parse the real `SKILL.md` to guard step numbering and the template field against drift.

**Tech Stack:** Markdown skill definitions, pytest (structural assertions over `SKILL.md`), JSON eval/benchmark harness.

**Closes:** [#211](https://github.com/WhatIfWeDigDeeper/agent-skills/issues/211), [#217](https://github.com/WhatIfWeDigDeeper/agent-skills/issues/217)

## Global Constraints

- Skill version bumps **exactly once** for this PR: `metadata.version` `"1.2"` → `"1.3"`. No further bump on reviewer-fix commits.
- Branch is `spec/learn-audit-trace`. Never commit to `main`.
- No hardcoded `/tmp/` in any command — use `mktemp`, `$TMPDIR`, or `/private/tmp`.
- Temp/scratch files must not be committed; `evals/learn/` keeps only `evals.json`, `benchmark.json`, `benchmark.md`, `fixtures/`.
- `benchmark.json` writes go through `json.dump(...)` with default `ensure_ascii=True` — the file stores `—` as a `\uXXXX` escape and contains no non-ASCII bytes, so the escapes must be preserved.
- New rule text added to any `CLAUDE.md` must itself pass Principle 5 — this spec changes the audit, so its own prose is held to it.

## Problem

`skills/learn/SKILL.md` Step 5 requires a "minimum viable rule text" audit before the plan is shown, and marks it **"the audit is not optional."** The audit produces no output. A plan containing an audited rule and a plan containing a first-draft rule are byte-identical, so the user has nothing to inspect and the omission surfaces only after the text has landed in a config file.

This is measured, not hypothetical. Eval 9 (`min-char-audit`) asserts the turn-1 rule body is ≤ 200 characters, and it **fails with the skill loaded** on both models:

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---|---|---|
| `turn1-rule-under-200-chars` **with_skill** | ❌ 209 chars | ❌ 308 chars |
| eval 9 overall **with_skill** | 4/5 (80%) | 4/5 (80%) |
| eval 9 overall **without_skill** | 2/5 (40%) | 2/5 (40%) |

`evals/learn/benchmark.md` already names this: *"The turn-1 ≤ 200-char assertion still fails at v1.0 on both models — the audit fires but doesn't get below 200 on first pass. That is the single known false-negative at v1.0."*

Issue #217 proposes strengthening the wording. Issue #211 argues that wording is the intervention that already exists and already fails — the line is the most emphatic in the file — and that the fix must be an artifact the user can reject in one word. The eval data supports #211. #217's contribution is a *falsifiable signal*, which this spec keeps as the audit step's self-check.

## Design

### Change 1 — Promote the audit to its own numbered step

**File:** `skills/learn/SKILL.md`

Remove this paragraph from the Present-Plan step (the second "Before showing the plan" paragraph, beginning `Before showing the plan, **audit each drafted rule body`):

```
Before showing the plan, **audit each drafted rule body against the Principles' "Minimum viable rule text" check** — apply "is this the min chars necessary?" to every clause and cut any clause you can't defend (incident narratives, multi-clause rationales, explanatory prose beyond a concrete example). First-draft text routinely needs trimming; the audit is not optional.
```

Insert a new step immediately **before** `### 5. Present Plan and Wait for Confirmation`:

```markdown
### 5. Audit Rule Text

Split each drafted rule at sentence and em-dash boundaries. For every fragment, name what it contributes — rule, fix, non-obvious why, or concrete example — or cut it. Incident narratives, multi-clause rationales, and restated triggers fail the check.

Record the result in the next step's `Cut in audit:` line. If the user has to ask whether a draft is minimal, the audit was skipped, not just light.
```

The second sentence of the second paragraph is issue #217's clause, kept as the step's falsifiable self-check.

The forward reference is phrased as "the next step's" rather than "Step 6" deliberately — a hardcoded number in the skill would drift the next time a step is inserted, which is exactly the failure mode `specs/CLAUDE.md` warns about.

### Change 2 — Renumber the downstream steps

| Before | After |
|---|---|
| `### 5. Present Plan and Wait for Confirmation` | `### 6. Present Plan and Wait for Confirmation` |
| `### 6. Apply Changes` | `### 7. Apply Changes` |
| `### 7. Summarize` | `### 8. Summarize` |

Steps 1–4 are unchanged, as is the Route A body's reference to "Step 4's sync-rule preservation" and the `$ARGUMENTS` reference to "Step 2".

### Change 3 — Add the trace field to the plan template

**File:** `skills/learn/SKILL.md`, the fenced plan template in the (renumbered) Present-Plan step.

```markdown
**[Category]**: [Brief description]
- Source: [what triggered this learning]
- Proposed change: [exact text to add, post-audit]
- Cut in audit: [clauses cut, or "none" + one-word defense per kept clause]
- Destination: [file] ([current lines] → [projected lines])
```

`Cut in audit:` is required on every item, including when nothing was cut. An optional field reverts to the invisible state this spec exists to remove: an absent line would mean either "audited, nothing to cut" or "never audited," which is the current ambiguity.

### Change 4 — Update the two live cross-references

| File | Current | New |
|---|---|---|
| `skills/learn/references/multiconfig-routing.md` | `If the user later expresses a narrower scope at the Step 5 confirmation` (wraps across two lines after `Step 5`) | `Step 6 confirmation` |
| `tests/learn/test_multiconfig_routing.py` | `class TestIssuesFiledRegex` docstring: `"""Step 7: extract GitHub issue URLs filed during the session.` | `Step 8:` |

**Deliberately not updated:** `evals/learn/benchmark.json` `evidence` strings such as `"Plan shown in Step 5 with category/destination/line counts before apply"`. Those are observations recorded from transcripts produced under the old numbering, not assertion criteria. Rewriting them would falsify run history. The `evals/CLAUDE.md` propagation rule targets `evals.json` assertion `text` and `benchmark.json` expectation `text` — no field of either type references a step number, verified by `rg 'Step [0-9]' evals/learn/evals.json`.

### Change 5 — Version bump

`skills/learn/SKILL.md` frontmatter `metadata.version`: `"1.2"` → `"1.3"`. A new numbered step is a workflow change, not a fix.

### Change 6 — Structural regression tests

**File (new):** `tests/learn/test_audit_trace.py`

Parses the real `skills/learn/SKILL.md` — the pattern already used by `tests/pr-comments/test_bot_mentions.py` (`SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / ...`) and `tests/pr-comments/test_jq_filters.py`. Fenced code blocks are stripped before scanning headings, because the Route C skill template in the (renumbered) Apply-Changes step contains a literal `### 1. [First Step]` that would otherwise be read as a step heading.

Coverage:

1. Step headings are sequential from 1 with no gaps or duplicates.
2. A step titled `Audit Rule Text` exists.
3. The audit step's number is lower than the Present-Plan step's number.
4. The audit step body names the per-clause split (`em-dash`) and points at `Cut in audit`.
5. The plan template contains `- Cut in audit:`.
6. `- Cut in audit:` appears before `- Destination:` in the template.
7. `multiconfig-routing.md` references the *current* Present-Plan step number — computed from the parsed headings, not hardcoded, so the test fails if renumbering happens again without updating the reference.

### Change 7 — Eval coverage

**File:** `evals/learn/evals.json`, eval 9 (`min-char-audit`). Add one assertion:

```json
{
  "id": "plan-shows-cut-in-audit",
  "text": "The turn-1 plan shown before any file write includes a 'Cut in audit:' line for the proposed rule, naming either the clauses removed or 'none' with a per-clause defense. Fail if the plan omits the field entirely"
}
```

Verified absent today: `rg '"id":.*cut-in-audit' evals/learn/evals.json` returns nothing.

Eval 9 goes from 5 assertions to 6. Because assertion sets changed, the existing eval 9 entries are **replaced** (still `run_number: 1`), not supplemented — no `regression_run_evals` field is introduced.

**Runs required:** eval 9 × {`with_skill`, `without_skill`} × {`claude-sonnet-5`, `claude-opus-5`} = 4 runs. Per `evals/CLAUDE.md`, a new assertion needs observed-transcript evidence, so `without_skill` is re-run too rather than inferred.

The v1.0 baseline was measured on `claude-sonnet-4-6` / `claude-opus-4-7`, but those executors are no longer reachable from the runner — the v1.3 runs and the v1.2 same-model control both used the Claude 5 pair, and future re-runs must too. A v1.0-vs-v1.3 comparison therefore crosses a model generation and cannot be attributed to the skill change; that is why the same-model v1.2 control exists.

### Acceptance target and the honest failure branch

**Target:** eval 9 `with_skill` reaches 6/6 on both models — `turn1-rule-under-200-chars` flips to pass and `plan-shows-cut-in-audit` passes.

**If `turn1-rule-under-200-chars` still fails:** record the observed char counts in `benchmark.json` and `benchmark.md` and ship the change on the strength of `plan-shows-cut-in-audit` alone. **Do not loosen the 200-char threshold.** `benchmark.md` documents the strictness as deliberate ("loosening it would weaken the signal that the audit ran unprompted"), and relaxing it would erase the measurement this change exists to move. A partial result is a real result; it does not get converted into a pass by moving the bar.

**Outcome:** the failure branch is what happened. `turn1-rule-under-200-chars` did not flip, and a same-model v1.2 control showed rules got marginally *longer* (239 → 243 Sonnet 5, 264 → 270 Opus 5). The threshold was left unchanged. `plan-shows-cut-in-audit` is fully discriminating, so the change ships as a transparency win, not a concision one. Full results and the model-generation caveat: `evals/learn/benchmark.md`, sections "Eval 9 — Min-char audit (two-turn)" and "v1.2 Control Runs (same-model A/B)". Claude 4.6/4.7 were unreachable from the harness, so the v1.3 runs are on `claude-sonnet-5` / `claude-opus-5` and are labeled as such.

## Files to Modify

| File | Change |
|---|---|
| `skills/learn/SKILL.md` | New Step 5; renumber 5→6, 6→7, 7→8; `Cut in audit:` template line; version `"1.2"` → `"1.3"` |
| `skills/learn/references/multiconfig-routing.md` | `Step 5 confirmation` → `Step 6 confirmation` |
| `tests/learn/test_audit_trace.py` | **New** — structural regression tests |
| `tests/learn/test_multiconfig_routing.py` | Docstring `Step 7:` → `Step 8:` |
| `evals/learn/evals.json` | Add `plan-shows-cut-in-audit` assertion to eval 9 |
| `evals/learn/benchmark.json` | Replace 4 eval-9 run entries; recompute `run_summary` + `run_summary_by_model`; `metadata.skill_version` → `"1.3"`; refresh `metadata.timestamp` and per-model `notes` |
| `evals/learn/benchmark.md` | Eval-9 summary-table row, Eval 9 section, Known-limitations bullet, per-model prose |
| `README.md` | `learn` row Eval Δ column; `learn` Skill Notes **Eval cost** bullet |
| `cspell.config.yaml` | Any new unknown words, inserted alphabetically |

`.github/copilot-instructions.md` needs no change — this spec adds no `CLAUDE.md` rule.

## Verification

1. `rg -c '^### [0-9]+\. [A-Z]' skills/learn/SKILL.md` → `8` (the `[A-Z]` guard excludes the literal `### 1. [First Step]` inside the Route C template fence, which a bare `^### [0-9]+\.` would miscount)
2. `rg -n 'Audit Rule Text' skills/learn/SKILL.md` → exactly one match
3. `rg -n 'Cut in audit' skills/learn/SKILL.md` → two matches (audit step body + plan template)
4. `rg -n 'audit each drafted rule body' skills/learn/SKILL.md` → no matches (old paragraph removed). Anchor on the removed paragraph's distinctive opener, not its closing "the audit is not optional" — that phrase is generic enough to reappear legitimately.
5. `rg -n 'Step 5 confirmation' skills/learn/references/multiconfig-routing.md` → no matches
6. `rg '^  version:' skills/learn/SKILL.md` → `"1.3"`
7. `python3 -c 'import json; json.load(open("evals/learn/evals.json"))'` → no error
8. `python3 -c 'import json; json.load(open("evals/learn/benchmark.json"))'` → no error
9. `uv run --with pytest pytest tests/` → all pass (sandbox lifted)
10. `npx cspell skills/learn/SKILL.md specs/54-learn-audit-trace/*.md tests/learn/test_audit_trace.py` → clean
11. `jq '[.runs[] | .expectations[] | select((. | keys) != ["evidence","passed","text"])] | length' evals/learn/benchmark.json` → `0`

## Risks and Carried-Forward Limits

- **The trace can be faked.** Nothing verifies that a `Cut in audit:` line reflects real per-clause reasoning rather than plausible filler. Carried forward verbatim from #211's non-goals: this raises the cost of skipping and makes omission visible at plan time; it does not make skipping impossible.
- **Plan verbosity increases** by one line per learning. Accepted — visibility is the deliverable.
- **Renumbering drift.** Mitigated by test 7, which derives the expected step number from the parsed headings rather than hardcoding it.
- **The 200-char assertion may not flip.** Handled explicitly in the acceptance section above; the threshold does not move.

## Shipping

1. Commit per task on `spec/learn-audit-trace`.
2. `/ship-it` to open the PR, then `/pr-comments` immediately (per project convention, initial PR creation is treated like a follow-up push).
3. `/pr-human-guide` before reporting the PR ready for human review.
4. Verify `gh pr checks` is clean — no failing or pending checks.
5. After a human review and squash-merge: close #211 and #217 referencing the PR, then `/learn` on the merged changes.
