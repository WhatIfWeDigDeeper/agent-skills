# Spec 50 — Tasks

> Execute top-to-bottom. Check off each `- [ ]` immediately on completion (do not
> batch). Work on a feature branch, never on `main`. Open a PR when the skill
> change + evals are in place. Bump `pr-human-guide` `metadata.version` exactly
> once for the whole PR.

---

## Task 1: Refine the documentation exemption in `categories.md`

**Files:** `skills/pr-human-guide/references/categories.md`

Edit the `## Selectivity Threshold` "Exceptions — never flag these regardless of
content:" list. This is the load-bearing change.

### Steps

- [ ] **Step 1.1:** Replace the bullet `- Changes that only affect comments or
  documentation` with, verbatim:

  ```
  - Changes that only affect code comments or true documentation prose — README
    files, usage guides, and design/spec docs (e.g. `specs/**`) that *describe*
    code rather than define behavior. **Operative source is not
    documentation-exempt even when it is markdown:** in an agent-skills repo,
    `SKILL.md` and reference files under a `skills/` tree (any `skills/**/*.md`,
    including `skills/**/references/*.md`) are the operative behavioral source
    that defines what an agent does — its security/trust boundaries and workflow
    patterns — not prose about code (adjust the `skills/` prefix to match your
    repo's skill directory layout). Evaluate such files against the normal
    categories and this Selectivity Threshold: flag one only when the change
    introduces a security boundary, a trust boundary, or a novel workflow
    pattern. A pure wording, typo, or formatting edit to these files stays
    exempt.
  ```

- [ ] **Step 1.2:** Extend the "Auto-generated files" bullet to name
  cspell/wordlist entries, verbatim:

  ```
  - Auto-generated files (lockfiles with only version changes, compiled output,
    generated protobuf stubs) and data/config entries such as cspell/wordlist
    additions
  ```

- [ ] **Step 1.3:** Do NOT touch the threshold paragraph (the "Flag an area only
  if…" / "risk **or** uncertainty" / "File count alone is not a flagging signal"
  lines) or the six category sections. Re-read the whole `## Selectivity
  Threshold` section after editing to confirm the disjuncts are intact.

- [ ] **Step 1.4:** `rg -n 'only affect comments or documentation' skills/pr-human-guide/`
  returns no matches (old phrasing fully removed; no parallel occurrence left).

- [ ] **Step 1.5:** `npx cspell skills/pr-human-guide/references/categories.md` —
  add any new terms to `cspell.config.yaml` (alphabetically) if flagged.

---

## Task 2: Bump the skill version

**Files:** `skills/pr-human-guide/SKILL.md`

### Steps

- [ ] **Step 2.1:** Confirm no bump exists yet on this branch:
  `git fetch origin && git diff origin/main -- skills/pr-human-guide/SKILL.md | rg '^\+  version:'`
  (empty = safe to bump).

- [ ] **Step 2.2:** Set `metadata.version` `"0.13"` → `"0.14"`.

---

## Task 3: Add evals 13 and 14

**Files:** `evals/pr-human-guide/evals.json`

Append two eval objects. Each `prompt` embeds the fixture inline and **must not
name the skill**. Follow the existing object shape:
`{id, name, prompt, expected_output, assertions:[{id, text}]}`.

### Eval 13 — `operative-skill-source-boundary` (positive)

- **prompt** (natural request, no skill name): a request to prep/guide a PR whose
  diff edits a `skills/<name>/references/*.md` file adding a new trust-boundary /
  allow-list rule (model on the bot-polling.md VERDICT allow-list — a rule that
  keeps untrusted-comment classification in the main agent, out of a read-only
  subagent). Include a PR number, URL, current description, and a ` ```diff ```
  block touching only the `.md` file.
- **expected_output** (grader-only prose): the guide should flag the change under
  Security or Novel Patterns because the edited markdown is operative skill
  source introducing a trust boundary — not documentation-exempt.
- **assertions:**
  - `flags-the-boundary`: The guide flags the operative-markdown change under
    Security or Novel Patterns and does not exempt it as documentation.
  - `uses-html-markers`: The PR description update uses the exact markers
    `<!-- pr-human-guide -->` and `<!-- /pr-human-guide -->`.
  - `includes-diff-link`: The guide links to the PR diff / files-changed view.
  - `updates-pr-description`: The guide is written into the PR description.

### Eval 14 — `skill-doc-wording-exempt` (negative)

- **prompt**: a request to prep/guide a PR whose diff makes only a prose/wording
  tweak to a `SKILL.md`, plus a `specs/**` doc edit and a `cspell.config.yaml`
  wordlist addition — no new boundary or pattern. Include PR number, URL,
  description, and a ` ```diff ``` block across those files.
- **expected_output**: the guide should emit the bounded "no areas requiring
  special human review" message — pure wording on operative source, plus spec
  docs and cspell entries, all stay exempt.
- **assertions:**
  - `does-not-flag-skill-doc`: The guide does NOT flag the wording tweak, spec
    doc, or cspell entry under any category.
  - `outputs-no-areas-message`: The body contains the "no areas requiring special
    human review" message.
  - `uses-exact-markers`: The PR description update uses the exact markers (not
    alternative formats).

### Steps

- [ ] **Step 3.1:** Append eval 13 and eval 14 to the `evals` array (mind the
  trailing comma on the previous element — the Edit tool does not validate JSON).
- [ ] **Step 3.2:** `python3 -c "import json; json.load(open('evals/pr-human-guide/evals.json'))"`
  — valid JSON.

---

## Task 4: Run the new evals and record the benchmark

**Files:** `evals/pr-human-guide/benchmark.json`, `evals/pr-human-guide/grading-*.json`

Per `evals/CLAUDE.md`, inclusion here constitutes approval to run — do not wait
to be asked.

### Steps

- [ ] **Step 4.1:** For each of evals 13, 14, spawn a `with_skill` and a
  `without_skill` executor subagent (`mode: "auto"`, executor must NOT call the
  `Skill` tool in either config). Feed the eval `prompt` verbatim. **Run on
  `claude-opus-4-8` (executor and analyzer both), matching the evals 9–12
  bucket** — this is the `run_summary_by_model["claude-opus-4-8"]` set and the
  README line-97 Opus 4.8 bullet that the docs step updates. Do not run on the
  legacy Sonnet 4.6 / Opus 4.7 buckets (those are frozen at evals 1–8).
- [ ] **Step 4.2:** Grade each run's output against its assertions with an
  analyzer subagent. Confirm each eval has ≥1 assertion that **passes with_skill
  and fails without_skill** (discrimination bar). If not, revise the eval fixture
  and re-run.
- [ ] **Step 4.3:** Append run records to `benchmark.json` using the existing run
  schema (`eval_id, eval_name, executor_model, analyzer_model, configuration,
  run_number, result, expectations`; expectation objects exactly
  `{text, passed, evidence}`). Use `null` (not `0`) for unrecorded stats.
- [ ] **Step 4.4:** Bump `metadata.evals_run` and `metadata.skill_version`;
  recompute `run_summary` and `run_summary_by_model` (sample stddev N−1; signed
  2-decimal deltas from unrounded means).
- [ ] **Step 4.5:** Commit judgment-call grading JSON selectively
  (`grading-<model>-<config>-<N>.json`); never commit raw transcripts.
- [ ] **Step 4.6:** Validate:
  `python3 -c "import json; json.load(open('evals/pr-human-guide/benchmark.json'))"`
  and the expectation-schema jq check from `evals/CLAUDE.md` returns `0`.

---

## Task 5: Docs bookkeeping

**Files:** `evals/pr-human-guide/benchmark.md`, `README.md`

### Steps

- [ ] **Step 5.1:** `benchmark.md` — add Summary-table rows for evals 13/14, add
  per-eval sections (fixture + discriminators), and update the "Token
  statistics … N of M" denominator.
- [ ] **Step 5.2:** `README.md` — there is **no eval-count field** to bump. Make
  two targeted edits:
  1. **Line ~97 Opus 4.8 bullet** — currently
     `**Opus 4.8** (coverage evals 9–12 only … the Selectivity Threshold):
     +19,344 tokens for **+54% pass rate** (100% with-skill vs 46% baseline) —
     all four discriminate; …`. Widen the range `9–12` → `9–14`, and recompute
     the token delta and pass-rate figures over all **6** evals (9–14) from the
     new `run_summary_by_model["claude-opus-4-8"]` numbers. Update the
     "all four discriminate" clause to the new count.
  2. **Row `Eval Δ` column (line 13)** — `+31% Sonnet 4.6 / +42% Opus 4.7` is
     the frozen evals-1–8 headline; leave it unless the maintainer wants an
     Opus 4.8 figure surfaced there. If updated, keep it consistent with the
     line-97 bullet. (No change is the safe default — note the decision in the
     PR body.)

---

## Task 6: Verify and open the PR

### Steps

- [ ] **Step 6.1:** `npx cspell skills/pr-human-guide/references/categories.md specs/50-*/plan.md specs/50-*/tasks.md`
- [ ] **Step 6.2:** `uv run --with pytest pytest tests/` (lift sandbox if the uv
  cache errors) — existing assertions pass.
- [ ] **Step 6.3:** Manual spot check — feed the PR #202 diff to the updated
  skill; confirm the `bot-polling.md` trust boundary is now flagged without a
  manual override.
- [ ] **Step 6.4:** Commit on a feature branch and open a PR. In the PR body,
  note: single version bump `0.13 → 0.14`, two new evals, and that no `CLAUDE.md`
  / copilot-instructions change is needed. Then run `/pr-comments {pr}` per repo
  workflow.
