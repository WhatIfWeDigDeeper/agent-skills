# Spec 54 Tasks: learn — Min-Chars Audit Trace

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans`. Read `plan.md` in this directory first. Check off each `- [ ]` immediately after completing it — do not batch updates at the end.

**Branch:** `spec/learn-audit-trace` (already created off `main` @ `bbf9460`)

**Global constraints** (repeated here because task implementers may not read `plan.md` in full):

- Bump `skills/learn/SKILL.md` `metadata.version` `"1.2"` → `"1.3"` exactly once, in Task 1. No further bumps on later tasks or reviewer-fix commits.
- Never commit to `main`.
- No hardcoded `/tmp/` — use `mktemp`, `$TMPDIR`, or `/private/tmp`.
- `benchmark.json` rewrites use `json.dump(..., indent=2)` with default `ensure_ascii=True`.

---

## Task 1: Promote the audit to a numbered step, with structural tests

**Files:**
- Create: `tests/learn/test_audit_trace.py`
- Modify: `skills/learn/SKILL.md`
- Modify: `skills/learn/references/multiconfig-routing.md`
- Modify: `tests/learn/test_multiconfig_routing.py`

**Interfaces:**
- Produces: an eight-step `## Process` section in `skills/learn/SKILL.md` whose Step 5 is `Audit Rule Text` and whose Step 6 plan template carries a `- Cut in audit:` field. Task 2's eval assertion depends on that exact field spelling, including the capital `C` and the trailing colon.

- [x] **Step 1: Write the failing structural test**

Create `tests/learn/test_audit_trace.py`:

```python
"""Structural tests for the learn skill's min-char audit trace (spec 54).

Issues #211 / #217: the audit was mandatory in wording but emitted no
artifact, so a skipped audit was indistinguishable from one that ran.
Spec 54 promotes it to its own numbered step and adds a ``Cut in audit:``
field to the plan template. These tests parse the real SKILL.md so the
step numbering and the template field cannot drift silently.
"""

import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "learn"
SKILL_MD = SKILL_DIR / "SKILL.md"
MULTICONFIG_MD = SKILL_DIR / "references" / "multiconfig-routing.md"

# ``### N. Title`` process steps. Fenced blocks are stripped first: the
# Route C skill template embeds a literal ``### 1. [First Step]`` that is
# example content, not a process step.
STEP_HEADING = re.compile(r"^### (\d+)\.[ \t]+(.+?)\s*$", re.MULTILINE)
FENCED_BLOCK = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


def prose() -> str:
    """SKILL.md with fenced code blocks removed."""
    return FENCED_BLOCK.sub("", SKILL_MD.read_text())


def step_headings() -> list[tuple[int, str]]:
    """All ``### N. Title`` process steps as (number, title) pairs."""
    return [(int(num), title) for num, title in STEP_HEADING.findall(prose())]


def step_number(title_fragment: str) -> int:
    for num, title in step_headings():
        if title_fragment in title:
            return num
    raise AssertionError(f"no step titled {title_fragment!r}: {step_headings()}")


def step_body(title_fragment: str) -> str:
    text = prose()
    matches = list(STEP_HEADING.finditer(text))
    for i, match in enumerate(matches):
        if title_fragment in match.group(2):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            return text[match.end() : end]
    raise AssertionError(f"no step titled {title_fragment!r}")


class TestStepNumbering:
    """Spec 54 Change 2: the audit is its own numbered step."""

    def test_steps_are_sequential_from_one(self):
        numbers = [num for num, _ in step_headings()]
        assert numbers == list(range(1, len(numbers) + 1)), (
            f"process step numbers must be gapless and start at 1, got {numbers}"
        )

    def test_audit_step_exists(self):
        assert step_number("Audit Rule Text") > 0

    def test_audit_step_precedes_plan_step(self):
        assert step_number("Audit Rule Text") < step_number("Present Plan")

    def test_old_preamble_audit_sentence_is_gone(self):
        # Anchor on the removed paragraph's distinctive opener, not on its closing
        # "the audit is not optional" — that phrase is generic enough to reappear
        # legitimately and false-fail this test. "Before showing the plan" alone is
        # not usable either: it still opens the dedup sentence in Present Plan.
        assert "audit each drafted rule body" not in SKILL_MD.read_text(), (
            "the preamble audit paragraph should have been replaced by the numbered step"
        )


class TestAuditStepContent:
    """Spec 54 Change 1: the procedure is per-clause and names its artifact."""

    def test_audit_step_names_the_split_boundary(self):
        assert "em-dash" in step_body("Audit Rule Text")

    def test_audit_step_points_at_the_plan_field(self):
        assert "Cut in audit" in step_body("Audit Rule Text")

    def test_audit_step_carries_the_skipped_signal(self):
        """Issue #217's falsifiable self-check."""
        assert "was skipped" in step_body("Audit Rule Text")

    def test_audit_step_has_no_hardcoded_forward_step_number(self):
        """A hardcoded 'Step 6' would drift on the next step insertion."""
        assert not re.search(r"Step \d", step_body("Audit Rule Text"))


class TestPlanTemplate:
    """Spec 54 Change 3: the audit leaves a trace the user can reject."""

    def test_template_has_cut_in_audit_field(self):
        assert "- Cut in audit:" in SKILL_MD.read_text()

    def test_cut_in_audit_precedes_destination(self):
        content = SKILL_MD.read_text()
        assert content.index("- Cut in audit:") < content.index("- Destination:")


class TestCrossReferences:
    """Spec 54 Change 4: references track the renumbered plan step."""

    def test_multiconfig_routing_points_at_current_plan_step(self):
        expected = step_number("Present Plan")
        text = " ".join(MULTICONFIG_MD.read_text().split())
        assert f"Step {expected} confirmation" in text, (
            f"multiconfig-routing.md must reference Step {expected} confirmation"
        )
```

- [x] **Step 2: Run the test to verify it fails**

Run (sandbox lifted — `uv` cache hits EPERM otherwise; in Claude Code: `dangerouslyDisableSandbox: true`):

```bash
uv run --with pytest pytest tests/learn/test_audit_trace.py -v
```

Expected: failures in `TestStepNumbering::test_audit_step_exists`, `TestAuditStepContent::*`, `TestPlanTemplate::*`, and `TestCrossReferences::*`. `test_steps_are_sequential_from_one` passes already (1–7 is gapless today) — that one is a drift guard, not a red test.

- [x] **Step 3: Insert the new audit step in `skills/learn/SKILL.md`**

Delete the paragraph beginning `Before showing the plan, **audit each drafted rule body` (the second "Before showing the plan" paragraph, immediately above `Then show everything you plan to do:`), and insert this new step immediately **before** the `### 5. Present Plan and Wait for Confirmation` heading:

```markdown
### 5. Audit Rule Text

Split each drafted rule at sentence and em-dash boundaries. For every fragment, name what it contributes — rule, fix, non-obvious why, or concrete example — or cut it. Incident narratives, multi-clause rationales, and restated triggers fail the check.

Record the result in the next step's `Cut in audit:` line. If the user has to ask whether a draft is minimal, the audit was skipped, not just light.
```

Keep the deduplicate-candidates paragraph where it is — it stays in the Present-Plan step.

- [x] **Step 4: Renumber the downstream step headings**

Three edits in `skills/learn/SKILL.md`, applied individually (do **not** use `replace_all` — the same digits appear in Route/Principle text):

| From | To |
|---|---|
| `### 5. Present Plan and Wait for Confirmation` | `### 6. Present Plan and Wait for Confirmation` |
| `### 6. Apply Changes` | `### 7. Apply Changes` |
| `### 7. Summarize` | `### 8. Summarize` |

Apply bottom-up (`7. Summarize` first, then `6. Apply Changes`, then `5. Present Plan`) so no intermediate edit creates two headings with the same number.

- [x] **Step 5: Add the `Cut in audit:` field to the plan template**

In the fenced plan template inside the now-Step-6 section, insert one line between `Proposed change` and `Destination`:

```markdown
**[Category]**: [Brief description]
- Source: [what triggered this learning]
- Proposed change: [exact text to add, post-audit]
- Cut in audit: [clauses cut, or "none" + one-word defense per kept clause]
- Destination: [file] ([current lines] → [projected lines])
```

- [x] **Step 6: Bump the skill version**

In `skills/learn/SKILL.md` frontmatter: `  version: "1.2"` → `  version: "1.3"`.

- [x] **Step 7: Update the two live cross-references**

In `skills/learn/references/multiconfig-routing.md`, the sentence `If the user later expresses a narrower scope at the Step 5` / `confirmation, that also binds.` wraps across two lines — change `Step 5` to `Step 6` on its line.

In `tests/learn/test_multiconfig_routing.py`, the `TestIssuesFiledRegex` docstring: `"""Step 7: extract GitHub issue URLs filed during the session.` → `"""Step 8: extract GitHub issue URLs filed during the session.`

- [x] **Step 8: Run the new tests to verify they pass**

```bash
uv run --with pytest pytest tests/learn/test_audit_trace.py -v
```

Expected: all 11 tests PASS.

- [x] **Step 9: Run the full suite for regressions**

```bash
uv run --with pytest pytest tests/ -q
```

Expected: no failures. If `tests/learn/test_multiconfig_routing.py` fails, the docstring edit in Step 7 changed executable content by mistake — revert and re-apply to the docstring only.

- [x] **Step 10: Verify the structural invariants by hand**

```bash
rg -c '^### [0-9]+\. [A-Z]' skills/learn/SKILL.md    # expect 8 ([A-Z] excludes the fenced "### 1. [First Step]")
rg -n 'Audit Rule Text' skills/learn/SKILL.md        # expect 1 match
rg -n 'Cut in audit' skills/learn/SKILL.md           # expect 2 matches
rg -n 'audit each drafted rule body' skills/learn/SKILL.md  # expect 0 matches (removed paragraph's distinctive opener)
rg -n 'Step 5 confirmation' skills/learn/references/multiconfig-routing.md  # expect 0 matches
rg '^  version:' skills/learn/SKILL.md               # expect "1.3"
```

- [x] **Step 11: Spell check**

```bash
npx cspell skills/learn/SKILL.md skills/learn/references/multiconfig-routing.md \
  tests/learn/test_audit_trace.py specs/54-learn-audit-trace/plan.md \
  specs/54-learn-audit-trace/tasks.md
```

Add any flagged term to the `words` list in `cspell.config.yaml` **in alphabetical position**. Do not pipe the output through `grep -v` — an npm cache EPERM would be silently swallowed.

- [x] **Step 12: Commit**

```bash
git add skills/learn/SKILL.md skills/learn/references/multiconfig-routing.md \
  tests/learn/test_audit_trace.py tests/learn/test_multiconfig_routing.py \
  specs/54-learn-audit-trace/ cspell.config.yaml
git commit -m "feat(learn): promote min-chars audit to its own step with a Cut in audit trace" \
  -m "The audit was mandatory in wording but emitted no artifact, so an audited rule and a first-draft rule produced byte-identical plans. Eval 9 measures the cost: turn1-rule-under-200-chars fails with_skill on both models." \
  -m "Adds Step 5 (Audit Rule Text) with a per-clause procedure, a Cut in audit: field on the plan template, and structural tests that guard step numbering against drift." \
  -m "Closes #211" -m "Closes #217"
```

If GPG signing fails, retry once with `--no-gpg-sign` (fallback only, not preemptive).

---

## Task 2: Add the eval assertion and re-run eval 9

**Files:**
- Modify: `evals/learn/evals.json`
- Modify: `evals/learn/benchmark.json`

**Interfaces:**
- Consumes: the `- Cut in audit:` plan field produced by Task 1.
- Produces: four replaced eval-9 run entries in `benchmark.json` with recomputed `run_summary` / `run_summary_by_model`. Task 3 reads the resulting pass rates and deltas.

- [x] **Step 1: Confirm the assertion does not already exist**

```bash
rg '"id":.*cut-in-audit' evals/learn/evals.json
```

Expected: no output. If it matches, stop — the task is a no-op and the spec needs revising.

- [x] **Step 2: Add the assertion to eval 9**

In `evals/learn/evals.json`, append to eval 9's `assertions` array (add a trailing comma to the current last element — the Edit tool does not validate JSON):

```json
{
  "id": "plan-shows-cut-in-audit",
  "text": "The turn-1 plan shown before any file write includes a 'Cut in audit:' line for the proposed rule, naming either the clauses removed or 'none' with a per-clause defense. Fail if the plan omits the field entirely"
}
```

- [x] **Step 3: Validate the JSON**

```bash
python3 -c 'import json; d=json.load(open("evals/learn/evals.json")); \
  e=[x for x in d["evals"] if x["id"]==9][0]; print(len(e["assertions"]))'
```

Expected: `6`.

- [x] **Step 4: Run eval 9 across both configurations and both models**

Four executor runs: `{with_skill, without_skill}` × `{claude-sonnet-5, claude-opus-5}`. Spawn each with `mode: "auto"`.

The v1.0 baseline was measured on `claude-sonnet-4-6` / `claude-opus-4-7`, but those executors are no longer reachable from the runner — the v1.3 runs and the v1.2 same-model control both used the Claude 5 pair, and future re-runs must too. A v1.0-vs-v1.3 comparison therefore crosses a model generation and cannot be attributed to the skill change; that is why the same-model v1.2 control exists.

Executor prompt requirements (per `evals/CLAUDE.md`):
- `mktemp -d` a workspace under `${TMPDIR:-/private/tmp}`, Write eval 9's `files` fixture (`CLAUDE.md`) there, `cd` in, and forbid reads outside the workspace.
- Pass **only** the eval `prompt` — never assertion text.
- Eval 9 is two-turn: issue `followup_prompt` as a second user message after turn 1, and return both `SUMMARY_TURN1` and `SUMMARY_TURN2`.
- Do **not** call the `Skill` tool in either configuration. For `with_skill`, read `skills/learn/SKILL.md` and follow it directly. For `without_skill`, forbid reading `skills/learn/SKILL.md`.
- Report the exact character count of the turn-1 rule body written to `CLAUDE.md`, and quote the plan block verbatim.

- [x] **Step 5: Grade each run**

Spawn a grader per run with the **full assertion text strings** from `evals.json` (not the IDs — grader output uses `text` verbatim). Grader writes `grading.json` shaped as:

```json
{
  "summary": {"passed": 0, "failed": 0, "total": 6, "pass_rate": 0.0},
  "expectations": [{"text": "...", "passed": true, "evidence": "..."}]
}
```

Evidence strings must be repo-relative — no absolute `/Users/...` paths.

- [x] **Step 6: Replace the four eval-9 entries in `benchmark.json`**

Replace in place at `run_number: 1` — do **not** add `run_number: 2` entries and do **not** introduce a `regression_run_evals` field. The assertion set changed, so the prior entries are superseded, not supplemented.

Per entry set `total: 6` and the observed `passed` / `failed` / `pass_rate` / `time_seconds` / `tokens` / `tool_calls` / `errors`. Use `null` for any stat not actually measured — never `0`.

- [x] **Step 7: Update `metadata`**

- `metadata.skill_version`: `"1.0"` → `"1.3"` — required by `evals/CLAUDE.md` whenever new run entries are added.
- `metadata.timestamp`: the run date
- Give **every** `models_tested[]` entry its own `skill_version`, placed after `analyzer_model` (the shape `evals/pr-human-guide/benchmark.json` uses): `"1.0"` for the two v1.0 groups, `"1.3"` for the two Claude 5 groups. Without it the top-level block reads as one tuple — `claude-opus-4-7` at v1.3 dated 2026-07-30 — and no such run exists.
- Append a sentence to each `models_tested[].notes` recording that eval 9 was re-run at v1.3 with the added `plan-shows-cut-in-audit` assertion.
- `metadata.evals_run` already contains `9` — leave it.

- [x] **Step 8: Recompute `run_summary` and `run_summary_by_model`**

Compute from the `runs` array, not from the stored rounded means:

- **Sample** standard deviation (N−1 denominator), matching repo convention.
- `delta` values are **signed strings** at 2-decimal precision for `pass_rate` (e.g. `"+0.24"`), and signed strings for `time_seconds` / `tokens`.
- Derive deltas from exact unrounded means. If the stored means are rounded for display, Task 3 must add the "Summary-table Delta values are computed from unrounded means" sentence to `benchmark.md`.

Write the file with `json.dump(..., indent=2)` — the on-disk indentation, verified with `head -3 evals/learn/benchmark.json`, not assumed — and default `ensure_ascii=True` so the existing `\uXXXX` escapes are preserved. A wrong `indent` reformats all ~2,000 lines and buries the real change.

- [x] **Step 9: Validate schema and JSON**

```bash
python3 -c 'import json; json.load(open("evals/learn/benchmark.json"))'
jq '[.runs[] | .expectations[] | select((. | keys) != ["evidence","passed","text"])] | length' \
  evals/learn/benchmark.json
```

Expected: no error, and `0` from the jq check.

- [x] **Step 10: Record the acceptance outcome**

If `turn1-rule-under-200-chars` passes on both models with_skill → target met, note it in the run `notes`.

If it still fails → record the observed character counts in the run `notes` and carry the result into Task 3 honestly. **Do not loosen the 200-char threshold**, and do not reword the assertion to make it pass. A partial result ships as a partial result.

- [x] **Step 11: Commit**

```bash
git add evals/learn/evals.json evals/learn/benchmark.json
git commit -m "test(learn): add plan-shows-cut-in-audit assertion and re-run eval 9 at v1.3"
```

---

## Task 3: Propagate results to `benchmark.md` and `README.md`

**Files:**
- Modify: `evals/learn/benchmark.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: the recomputed `run_summary` / `run_summary_by_model` and per-run pass rates from Task 2.

- [x] **Step 1: Update the per-eval summary table row**

In `evals/learn/benchmark.md`, the row beginning `| 9 | Min-char audit (two-turn) |` — replace all four cells with the new `N/6 (XX%)` values.

- [x] **Step 2: Update the per-model Summary tables**

Every per-model table — the `claude-sonnet-4-6` / `claude-opus-4-7` groups (evals 0-5, 7, 8 at v1.0) **and** the `claude-sonnet-5` / `claude-opus-5` groups (eval 9 at v1.3): `Pass rate`, `Time`, `Tokens` rows and their `Delta` column must mirror `run_summary_by_model` exactly. Moving eval 9 into its own model groups changes the v1.0 groups' numbers too. These values are not auto-generated and drift silently.

- [x] **Step 3: Update the per-model prose paragraphs**

The sentences listing discriminating `without_skill` cells name eval 9 with its old figures (`eval 9 min-char-audit (2/5 — 370-char rule + 38% trim + embedded incident narrative)`). Update to the new denominator and observed numbers.

- [x] **Step 4: Rewrite the `### Eval 9 — Min-char audit (two-turn)` section**

Cover: what the added assertion tests, the observed turn-1 character counts per model, and whether `turn1-rule-under-200-chars` flipped.

- [x] **Step 5: Update the Known-limitations bullet**

The bullet beginning `- **Eval 9 has one known false-negative at v1.0.**` describes the ≤200-char failure. If the assertion now passes, replace the bullet with a note that v1.3's audit-trace step closed it. If it still fails, update the version reference to v1.3 and keep the deliberate-strictness rationale intact.

- [x] **Step 6: Update the `Models tested` / `Evals` header lines**

Note that eval 9 was re-run at v1.3 with 6 assertions. Total run count stays 36 — the eval-9 entries were replaced, not added. Eval count stays 9, so the "Token statistics are computed only over N of M" denominator does not change.

- [x] **Step 7: Update `README.md`**

Two places:
- The `learn` row's Eval Δ column: `[+22% Sonnet 4.6 / +11% Opus 4.7](evals/learn/benchmark.md)` → the new percentages.
- The `learn` Skill Notes **Eval cost** bullet: the pass-rate percentages, the seconds/token deltas, and the discriminating-eval counts. Spell out "seconds", not "s".

- [x] **Step 8: Cross-check the numbers against `benchmark.json`**

```bash
rg -n 'Min-char audit|Pass rate|Eval cost|Eval Δ|\+2[0-9]%|\+1[0-9]%' \
  evals/learn/benchmark.md README.md
```

Every percentage shown must match a `pass_rate` or `delta` in `benchmark.json`. `benchmark.json` is authoritative; prose is not.

- [x] **Step 9: Spell check and commit**

```bash
npx cspell evals/learn/benchmark.md README.md
git add evals/learn/benchmark.md README.md cspell.config.yaml
git commit -m "docs(learn): update benchmark and README for v1.3 eval 9 results"
```

---

## Task 4: Ship

- [x] **Step 1: Confirm the branch is ahead of `main` and clean**

```bash
git fetch origin && git log origin/main..HEAD --oneline && git status --porcelain
```

- [x] **Step 2: Open the PR**

Run `/ship-it`. The PR body must describe all three commits — the skill change, the eval assertion, and the doc propagation — and state the acceptance outcome from Task 2 Step 10 plainly, including the case where the 200-char assertion did not flip.

- [ ] **Step 3: Address review immediately**

Run `/pr-comments {pr_number}` right after `/ship-it` reports the URL — per project convention, initial PR creation is treated the same as a follow-up push. Let the bot-polling loop run to completion.

- [ ] **Step 4: Verify CI**

```bash
gh pr checks {pr_number}
```

No check may be failing or pending. `"no checks reported"` is transient for ~60s after a push — re-poll before trusting it.

- [ ] **Step 5: Annotate for human review**

Run `/pr-human-guide` before reporting the PR ready. Do not merge on bot approval alone.

- [ ] **Step 6: After a human review and squash-merge**

```bash
gh pr merge {pr_number} --squash --delete-branch
```

Then on `main`: `git status --porcelain` as a standalone step, then `git pull --ff-only origin main`.

- [ ] **Step 7: Close the issues**

`Closes #211` / `Closes #217` in the commit message should auto-close both on merge. Verify with `gh issue view 211 --json state` and `gh issue view 217 --json state`; close manually with a link to the PR if either is still open.
