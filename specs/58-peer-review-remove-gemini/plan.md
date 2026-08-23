# Remove Gemini CLI support from `peer-review`

## Context

Google discontinued the Gemini CLI (`@google/gemini-cli`) in favor of the Antigravity IDE. The `peer-review` skill offered `--model gemini` as one of three external-LLM routes (alongside `copilot` and `codex`), shelling out to the `gemini` binary. That route now points at an unmaintained tool, so it is removed rather than left to rot.

**Decisions:**
- **Hard removal.** No deprecation stanza. `--model gemini` falls through the existing prefix check and produces the skill's standard `Unsupported --model value:` error.
- **Root `CLAUDE.md` trimmed** (the external-CLI sandbox gotcha), with its mandatory mirror in `.github/copilot-instructions.md`.
- **Full eval repurpose** — the removal is pinned by a regression eval, not just deleted coverage.

**Explicit non-goals.** A blanket `rg -i gemini` mixes two unrelated things; these stay untouched:
- `GEMINI.md` as an *assistant-config file* — the `learn` skill writes to it. `skills/learn/`, `tests/learn/`, and `tests/learn/fixtures/**/GEMINI.md`.
- `gemini-code-assist[bot]` in `tests/pr-comments/test_bot_mentions.py` — a GitHub bot handle, unrelated to the CLI.
- Everything under `specs/` other than this directory — append-only historical records.
- `cspell.config.yaml` — the `geminicli` entry **stays**. cspell's scan corpus is `skills/**/*.md` + `specs/**/*.md`, and `@google/gemini-cli` survives in four older `specs/*/plan.md` files. Removing the entry breaks the `cspell-config` pre-commit job.
- `README.md`'s `learn` row, which lists Gemini as a config target.

## Design

Gemini appears on four independent axes in `SKILL.md`; each must be handled individually, since fixing three of four leaves stale prose in the fourth:

1. **Frontmatter** — the description's CLI list and the `"review with Gemini"` trigger phrase (500-char hard limit on the description).
2. **Help/options block** — the `External CLIs:` line and the npm install hint.
3. **Routing (Step 4)** — the dispatch table row (gemini was the only CLI using `-m`), the install hint, and *both* copies of the `Unsupported --model value:` string, which must stay identical to each other, to the test oracle in `tests/peer-review/conftest.py`, and to eval 26's expected output.
4. **Security model** — this needs *rewording*, not deletion. The narrative is built on a *gemini+codex stdin vs. copilot argv* split; with gemini gone it becomes *codex vs. copilot*. The `ARG_MAX` escape hatch in the Step 4c rationale recommended gemini first and must be re-pointed to codex as the sole remaining stdin CLI.

`references/cli-invocations.md` holds the only executable `gemini` shell-out in the repo; the whole invocation block is deleted and the "All three CLIs" count becomes "Both CLIs" (that count is also encoded in a test set literal).

## Eval strategy

Do **not** renumber evals — IDs gap, because `benchmark.md` headings and `benchmark.json` `eval_id` fields are keyed to them.

| Eval | Action |
|---|---|
| 9 `gemini-not-found` | **Repurpose** → `gemini-model-removed`: assert the unsupported-model error, and assert the skill does *not* check for a gemini binary or print an install hint. This is the regression pin. |
| 10 `gemini-no-findings` | **Delete** — coverage is duplicated by eval 6 `copilot-empty-findings`. |
| 16 `triage-all-skipped` | **Re-point** `--model gemini` → `--model copilot`. Gemini was only the vehicle. Copilot matches the existing simulated-CLI pattern in evals 5/6/7/15/28. Consequence: copilot carries triage coverage for evals 15 and 16, and the codex triage path is intentionally uncovered. |
| 26 `unsupported-model-error` | Drop `gemini` from the expected supported-values list and the assertion text. |

Evals 9, 16, and 26 have changed semantics, so they require **re-runs**, not text edits: null every result field and the nested `expectations[].passed` / `.evidence` on both `with_skill` and `without_skill` sides, then re-run.

**Model-cohort constraint:** the original corpus was produced on `claude-sonnet-4-6` / `claude-opus-4-7`, which are no longer spawnable. The re-runs are therefore recorded as a separate `claude-sonnet-5` / `claude-opus-5` cohort, following the precedent already set in `evals/learn/benchmark.json` (eval 9 recorded on Sonnet 5 / Opus 5 while evals 0–8 stayed on the 4-6/4-7 cohort). The stale 4-6/4-7 entries for evals 9/16/26 are retained with all result fields nulled, so the paired-eval bookkeeping stays auditable. The new cohort's 12 runs are recorded for provenance but **excluded from `run_summary` and `run_summary_by_model`** — a 3-eval sample cannot support an aggregate, and folding it into a v1.6/v1.7 corpus would misattribute the 96 untouched runs. Aggregates stay scoped to the 24 paired 4-6/4-7 evals.

**Known contamination channel (must be documented in `benchmark.json` notes and `benchmark.md`):** every `without_skill` run in the new cohort named `copilot` and `codex` without reading SKILL.md. The leak is the skill's own frontmatter description, injected into every subagent's system prompt via the available-skills listing. This is distinct from the eval-26 Sonnet 4.6 contamination (a filesystem SKILL.md read) and **fencing the executor out of SKILL.md does not close it**. It hits eval 9 hardest — the repurposed eval asks precisely what the description states. The bias raises the baseline, so the recorded deltas are lower bounds. Treat `TestGeminiRemoved` in `tests/peer-review/test_model_routing.py`, not eval 9, as the authoritative regression guard.

**Local constraint:** `codex` is not installed on this machine. This does not block the work — all Gemini-touching evals are simulated (CLI output is supplied inline in the eval `prompt`), so no external binary is invoked. The `codex` invocation block in `cli-invocations.md` remains un-smoke-tested locally, which is already its documented state.

## Security baseline

The pinned findings (`W007`/`W011`/`W012`) **do not change** — `W012` fires on any external-CLI handoff and copilot/codex still trip it. Do **not** run `scan.sh --update-baselines`: it rewrites every baseline, and the scanner is non-deterministic, so unrelated pins come back with severities lowered, which fails CI as a regression on the next flap. Run the bare scan to confirm no *new* finding ID, then hand-edit `skill_version`, `captured_at`, and the `notes` prose.

## Verification

1. `rg -i gemini` across `skills/ tests/ evals/ docs/ README.md CLAUDE.md .github/copilot-instructions.md`, excluding `skills/learn/`, `tests/learn/`, `tests/pr-comments/`. `skills/` must be zero. Surviving hits elsewhere must be only: `README.md`'s learn row plus the two prose notes explaining the removal; eval 9's regression-pin text in `evals.json` and its run entries in `benchmark.json`; the v1.15 notes in `benchmark.json` / `benchmark.md` / `peer-review.baseline.json`; the `TestGeminiRemoved` test class; and historical `benchmark.md` changelog entries (the v1.13 line's "copilot/codex/gemini invocations" is a true claim *about v1.13* — do not rewrite it).
2. `rg -w geminicli cspell.config.yaml` and `rg 'gemini-cli' --glob 'specs/**/*.md'` — the wordlist entry must still be justified.
3. The two `Unsupported --model value` strings in `SKILL.md` must agree verbatim with the oracle in `tests/peer-review/conftest.py`.
4. `uv run --with pytest pytest tests/ -q` (sandbox lifted — uv's cache EPERMs otherwise).
5. `python3 -c 'import json; ...'` on `evals.json`, `benchmark.json`, `peer-review.baseline.json`.
6. `npx cspell "skills/**/*.md" "specs/**/*.md"`.
7. `bash evals/security/scan.sh` — no new finding ID for peer-review. `scan.sh` takes no per-skill argument.
8. Expectation-schema validation: `jq '[.runs[] | .expectations[]? | select((. | keys) != ["evidence","passed","text"])] | length'` must return `0`.
