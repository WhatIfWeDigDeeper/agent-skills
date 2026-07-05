# Spec 50 — pr-human-guide: treat operative skill source (`skills/**/*.md`) as non-exempt

## Context

`pr-human-guide`'s **Selectivity Threshold** (in
`skills/pr-human-guide/references/categories.md`) lists "Changes that only affect
comments or documentation" as a hard exemption — never flag, regardless of
content. In a **skills repository** that exemption misfires: `SKILL.md` and
`skills/**/references/*.md` files are not prose *describing* code — they are the
*operative behavioral source* that defines what an agent does, including its
security/trust boundaries and workflow patterns.

A naive reading exempts *every* skill-file change, so `pr-human-guide` emits an
empty "no areas" guide for essentially every skill PR — defeating its purpose on
this repo's own changes. Concrete miss (issue #203): on PR #202 (spec 49), the
one change warranting human judgment — a new Tier-0 read-only polling-subagent
**trust boundary** in `skills/pr-comments/references/bot-polling.md` (the VERDICT
allow-list keeping untrusted-comment classification in the main agent) — lives in
a `.md` file the docs exception would exempt. It was flagged only by overriding
the exemption manually.

**Intended outcome:** refine the exemption so operative skill markdown is
evaluated against the normal categories + Selectivity Threshold (flagged only
when it introduces a security boundary, trust boundary, or novel workflow
pattern), while true documentation, spec/design docs, test files, auto-generated
files, and cspell/wordlist entries stay exempt. The rule stays **assistant-neutral
and path-pattern based** so it generalizes to any skills repo, not just this one.

## Scope decisions (confirmed with the user)

- **Full scope**: the SKILL/categories change **and** eval coverage for both
  branches of the new conditional rule (positive + negative), run immediately per
  `evals/CLAUDE.md`.
- **Confine the change to the Selectivity Threshold exemption bullet.** Do not add
  parallel notes in §1 Security / §5 Novel Patterns — their detection signals
  already fire on trust boundaries and new workflow patterns; the blanket docs
  exemption was the only gate that was wrong. A second location risks drift
  (CLAUDE.md "search for all parallel occurrences").
- **Path-pattern based, assistant-neutral.** Reference `skills/**/*.md` generically
  with an "adjust the prefix to match your repo's layout" portability note; do not
  hard-code this repo.
- **Preserve the load-bearing disjuncts** in the threshold paragraph ("risk **or**
  uncertainty", "File count alone is not a flagging signal") — do not touch them.

## Current state (verified)

- `skills/pr-human-guide/SKILL.md` — v`0.13`, 178 lines. → bump to `0.14`.
- `skills/pr-human-guide/references/categories.md` — 248 lines. The exemption is a
  single bullet under the `## Selectivity Threshold` "Exceptions — never flag
  these regardless of content:" list: `- Changes that only affect comments or
  documentation`.
- Security §1 detection signals already cover "input handling at trust
  boundaries"; Novel Patterns §5 already covers "a new workflow pattern." So an
  operative `.md` introducing those is caught by existing category signals once
  the blanket exemption is removed — **no new category is needed.**
- `evals/pr-human-guide/evals.json` — 12 evals (ids 1–12). New evals take ids
  13, 14. Next spec number is **50** (49 is highest).

## Design

### 1. Refine the documentation exemption in `categories.md` (load-bearing edit)

Replace the single exemption bullet with a bullet that keeps true documentation
exempt, carves operative skill markdown out of the exemption, and stays
path-pattern based. Final wording (verbatim, copied into tasks.md):

```
- Changes that only affect code comments or true documentation prose — README
  files, usage guides, and design/spec docs (e.g. `specs/**`) that *describe*
  code rather than define behavior. **Operative source is not
  documentation-exempt even when it is markdown:** in an agent-skills repo,
  `SKILL.md` and reference files under a `skills/` tree (any `skills/**/*.md`,
  including `skills/**/references/*.md`) are the operative behavioral source that
  defines what an agent does — its security/trust boundaries and workflow
  patterns — not prose about code (adjust the `skills/` prefix to match your
  repo's skill directory layout). Evaluate such files against the normal
  categories and this Selectivity Threshold: flag one only when the change
  introduces a security boundary, a trust boundary, or a novel workflow pattern.
  A pure wording, typo, or formatting edit to these files stays exempt.
```

Extend the "Auto-generated files" exemption bullet to also name cspell/wordlist
and other data/config entries (they sit outside `skills/` so are already exempt,
but naming them prevents misreading the new rule as flagging them):

```
- Auto-generated files (lockfiles with only version changes, compiled output,
  generated protobuf stubs) and data/config entries such as cspell/wordlist
  additions
```

### 2. Version bump

`skills/pr-human-guide/SKILL.md` `metadata.version` `"0.13"` → `"0.14"` (patch —
a classification refinement, not a workflow change). Once per PR; before
committing run
`git fetch origin && git diff origin/main -- skills/pr-human-guide/SKILL.md | rg '^\+  version:'`
to confirm no bump already exists.

## Eval designs

Two evals, one per branch of the new conditional rule. Each embeds its fixture
inline in `prompt`, never names the skill, and has ≥1 assertion that fails
`without_skill`.

### Eval 13 — `operative-skill-source-boundary` (positive)

A PR whose only substantive change edits a `skills/<name>/references/*.md` file to
add a new **trust boundary / allow-list** rule (modeled on the bot-polling.md
VERDICT allow-list). The updated skill must flag it under Security or Novel
Patterns rather than exempting it as documentation.

Assertions:
- `flags-the-boundary` — the guide flags the operative-markdown change under
  Security or Novel Patterns (does not exempt it as documentation).
- `uses-html-markers` — the PR description update uses the exact markers
  `<!-- pr-human-guide -->` / `<!-- /pr-human-guide -->`.
- `includes-diff-link` — the guide links to the PR diff / files-changed view.
- `updates-pr-description` — the guide is written into the PR description, not
  just chat.

### Eval 14 — `skill-doc-wording-exempt` (negative)

A PR that only tweaks prose/wording in a `SKILL.md`, **plus** a `specs/**` doc
edit and a `cspell.config.yaml` wordlist addition — no new boundary or pattern.
The updated skill must still emit the bounded "no areas" message.

Assertions:
- `does-not-flag-skill-doc` — the guide does NOT flag the wording tweak, spec
  doc, or cspell entry under any category (operative-source rule fires only on a
  new boundary/pattern; pure wording stays exempt).
- `outputs-no-areas-message` — the body contains the "no areas requiring special
  human review" message.
- `uses-exact-markers` — the PR description update uses the exact markers (not
  alternative formats).

### Deliberately out of scope

- No third eval for "spec docs remain exempt in isolation" — eval 14 already
  bundles a `specs/**` doc + cspell entry into the negative case, so the exempt
  branch is covered without a separate case.
- No change to the six category sections' detection signals — they already fire
  once the exemption is fixed.

## Acceptance criteria for discrimination

Each new eval must have at least one assertion that **passes `with_skill` and
fails `without_skill`** (per `evals/CLAUDE.md`). Expected discriminators:
- Eval 13: `uses-html-markers` + `flags-the-boundary`. `flags-the-boundary`
  genuinely exercises the **new** rule — a baseline (and the pre-change skill)
  would exempt the operative `.md` as documentation. `uses-html-markers` is a
  format discriminator (baseline produces no marker-wrapped guide at all).
- Eval 14: `uses-exact-markers` + `outputs-no-areas-message`. These are
  **format/regression discriminators**, not new-rule discriminators — the
  negative case guards against the refined rule *over*-flagging pure wording;
  the baseline simply does not emit the bounded no-areas markers. Eval 13 is the
  case that proves the behavior change; eval 14 proves it did not overreach.

## Benchmark recording approach

Run both evals `with_skill` and `without_skill` (executor subagents spawned with
`mode: "auto"`, never calling the Skill tool; analyzer grades against assertions).
**Run on `claude-opus-4-8` for both executor and analyzer** — the same bucket as
evals 9–12 (`run_summary_by_model["claude-opus-4-8"]`, skill_version 0.13 in that
`models_tested` entry). The legacy Sonnet 4.6 / Opus 4.7 buckets are frozen at
evals 1–8 and are not extended. Append run records to
`evals/pr-human-guide/benchmark.json` using the existing
run schema (`eval_id, eval_name, executor_model, analyzer_model, configuration,
run_number, result, expectations, notes`; expectation objects exactly
`{text, passed, evidence}`). Bump `metadata.evals_run` and `metadata.skill_version`;
recompute `run_summary` / `run_summary_by_model` (sample stddev, N−1; signed
2-decimal deltas from unrounded means). Use `null`, not `0`, for unrecorded stats.

## benchmark.md updates

- Summary table: add rows for evals 13/14.
- Add per-eval sections describing fixture + discriminators.
- Update the "Token statistics ... N of M" denominator sentence for the new count.

## README updates

The pr-human-guide entry has **no eval-count field** (the row carries only an
`Eval Δ` column). The real edit is the **line ~97 Opus 4.8 bullet**, whose
`(coverage evals 9–12 only …)` range and `+19,344 tokens for +54% pass rate`
figures must widen to `9–14` and be recomputed over the 6 Opus-4.8 evals from
the new `run_summary_by_model["claude-opus-4-8"]`. The row `Eval Δ` column
(`+31% Sonnet 4.6 / +42% Opus 4.7`) is the frozen evals-1–8 headline — leave it
unchanged by default and note that decision in the PR body.

## Files to modify

| File | Change |
|------|--------|
| `skills/pr-human-guide/references/categories.md` | Rewrite the documentation-exemption bullet; extend the auto-generated bullet to name cspell/wordlist |
| `skills/pr-human-guide/SKILL.md` | `metadata.version` `0.13` → `0.14` |
| `evals/pr-human-guide/evals.json` | Add evals 13 (positive) + 14 (negative) |
| `evals/pr-human-guide/benchmark.json` | Append run records for evals 13/14; bump `metadata.evals_run` + `skill_version`; recompute summaries |
| `evals/pr-human-guide/benchmark.md` | Summary table + per-eval sections + denominator |
| `README.md` | Widen the line-97 Opus 4.8 bullet range `9–12` → `9–14` and recompute its token/pass-rate figures (no eval-count field exists) |
| `evals/pr-human-guide/grading-*.json` | Commit judgment-call gradings only, if any |

**No changes to**: the Selectivity Threshold paragraph disjuncts, the six
category sections, SKILL.md workflow steps, or `CLAUDE.md` /
`.github/copilot-instructions.md` (this is a skill change, not an instruction
rule — `instruction-sync` does not apply).

## Verification

- `npx cspell skills/pr-human-guide/references/categories.md specs/50-*/plan.md specs/50-*/tasks.md`
- `python3 -c "import json; json.load(open('evals/pr-human-guide/evals.json')); json.load(open('evals/pr-human-guide/benchmark.json'))"` — valid JSON
- `uv run --with pytest pytest tests/` (sandbox lifted) — existing assertions pass
- Run evals 13 & 14 `with_skill`/`without_skill`; confirm each has ≥1 assertion
  passing `with_skill` and failing `without_skill`.
- Manual spot check: feed the PR #202 diff to the updated skill and confirm the
  `bot-polling.md` trust boundary is now flagged without a manual override.
