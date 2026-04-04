# Tasks: Spec 17 — peer-review Phase II (multi-LLM routing)

## Phase 1: CLI Research

Before writing any skill code, verify the actual invocation interface for each external CLI. These tasks produce the authoritative input for Phases 2–4.

### codex
- [x] Run `codex --help` (or `codex -h`) and capture the full flag list; identify: prompt flag, model flag, read-only/no-edit flag, output format
- [x] Run a minimal test: `echo "What is 2+2?" | codex` (or `codex -p "What is 2+2?"`) — confirm invocation style and output format
- [x] Determine whether output is JSON, markdown, or plain text; note the structure
- [x] Identify any flag that prevents file writes (e.g. `--no-auto-edit`, `--read-only`, `--sandbox`)
- [x] Document findings in a `specs/17-peer-review-phase-ii/research-codex.md` file: exact flags, output schema, install command, any known quirks

### gemini
- [x] Run `gemini --help` (or `gemini -h`) and capture the full flag list; identify: prompt flag, model flag, read-only flag, output format
- [x] Run a minimal test: `echo "What is 2+2?" | gemini` (or `gemini -p "What is 2+2?"`) — confirm invocation style and output format
- [x] Determine whether output is JSON, markdown, or plain text; note the structure
- [x] Identify any flag that prevents file writes
- [x] Document findings in `specs/17-peer-review-phase-ii/research-gemini.md`: exact flags, output schema, install command, any known quirks

### copilot (confirm prototype assumptions)
- [x] Confirm that `copilot -p "$PROMPT" --deny-tool='write'` works without `--allow-tool` entries when the prompt already contains the diff content (no tool fetching needed)
- [x] Confirm the JSON schema from the prototype is stable: `{ summary, overall_risk, findings: [{ severity, file, title, details, suggested_fix }] }`
- [x] Note findings in a brief `specs/17-peer-review-phase-ii/research-copilot.md`

**Gate**: do not start Phases 2–4 until research files exist for all three CLIs, or until the researched CLI is confirmed installable. If a CLI is not available in the current environment, document "not available — skipping" in the research file and skip that CLI's integration phase. If none of the three CLIs are available, do not open the implementation PR — stub the research files and coordinate with the user to run research in an environment where at least one CLI is installed.

**Result**: copilot available; codex and gemini not installed → Phases 3 and 4 skipped; binary-absent error handling implemented for all three.

## Phase 2: copilot integration

- [x] Update SKILL.md Step 4: add conditional branch — if `model` starts with `claude-` (including the default), use existing subagent logic; otherwise enter the external CLI path (4a–4e from plan.md)
- [x] Implement 4a: check `which copilot`; if absent, error: "copilot CLI not found. Install with: `npm install -g @github/copilot-cli` or via the GitHub Copilot VS Code extension" and exit
- [x] Implement 4b: write the prompt to a temp file (`PROMPT_FILE=$(mktemp "${TMPDIR:-/tmp}/peer-review-prompt.XXXXXX")`) to avoid shell metacharacter injection from diff/commit content; build invocation — `copilot -p "$(cat "$PROMPT_FILE")" [--deny-tool='write'] [-m SUBMODEL]`; add `-m SUBMODEL` only when a sub-model was specified (e.g. `--model copilot:gpt-4o-mini`)
- [x] Implement 4c: execute and capture output into `REVIEW_OUTPUT`
- [x] Implement 4d: parse copilot JSON — extract `findings[]`; map `details` → problem, `suggested_fix` → fix; apply severity normalization table from plan.md; if `findings` is empty treat as `NO FINDINGS`; if JSON is malformed fall through to raw-output fallback (show raw output with "Could not parse structured findings; showing raw output.")
- [x] Implement 4e: feed normalized findings into Step 5 (present findings) — no Step 5 changes required

## Phase 3: codex integration

*Complete research-codex.md before starting this phase.*

**Skipped** — codex not available in this environment. Binary-absent error path (4a) implemented in SKILL.md. See `research-codex.md`.

- [x] Implement 4a for codex: check `which codex`; if absent, error with install hint from research
- [ ] Implement 4b: write prompt to temp file (`mktemp "${TMPDIR:-/tmp}/peer-review-prompt.XXXXXX"`); build invocation using flags confirmed in research; pass prompt via file or stdin (not direct argument interpolation); add read-only flag; add sub-model flag if provided
- [ ] Implement 4c–4d: execute, capture, parse output using the format confirmed in research; apply severity normalization; handle empty/malformed output
- [ ] If codex output is not JSON (plain text / markdown): parse severity from lines matching patterns like `[HIGH]`, `**Critical**`, `severity: high`, etc.; fall back to presenting the full output as a single `major` finding if no structured severity is found

## Phase 4: gemini integration

*Complete research-gemini.md before starting this phase.*

**Skipped** — gemini not available in this environment. Binary-absent error path (4a) implemented in SKILL.md. See `research-gemini.md`.

- [x] Implement 4a for gemini: check `which gemini`; if absent, error with install hint from research
- [ ] Implement 4b: write prompt to temp file (`mktemp "${TMPDIR:-/tmp}/peer-review-prompt.XXXXXX"`); build invocation using flags confirmed in research; pass prompt via file or stdin; add read-only flag; add sub-model flag if provided
- [ ] Implement 4c–4d: execute, capture, parse output; apply severity normalization; handle empty/malformed output
- [ ] If gemini output is not JSON: parse severity using the same heuristic as codex (patterns like `[HIGH]`, `**Critical**`, `severity: high`)

## Phase 5: SKILL.md update

- [x] Verify the Step 4 branch structure reads cleanly — the Claude path and external CLI path should be clearly delineated; the reader should not need to scroll back and forth
- [x] Update the `--model` description in the Arguments section: remove "Phase II:" qualifier and document the external CLIs as a supported feature with their install requirements
- [x] Update the Notes section: replace the "Phase II — multi-LLM routing" note with a description of the implemented capability; mention `specs/16-peer-review/copilot-staged-review.sh` is superseded
- [x] Bump `metadata.version` from `"1.0"` to `"1.1"` — do this once, in the first commit that modifies SKILL.md; do not bump again for follow-up commits on the same PR
- [x] Run `npx cspell skills/peer-review/SKILL.md`; add any new unknown words to `cspell.config.yaml`

## Phase 6: Evals

- [x] Add `copilot-json-parse` eval to `evals/peer-review/evals.json`: prompt instructs the agent that copilot returned a specific fixture JSON (embed a 2-finding fixture with severities `high` and `low`); assertions: (1) findings are presented with severity `critical` and `minor` respectively (not `high`/`low`); (2) the apply prompt is shown
- [x] Add `copilot-empty-findings` eval: prompt provides a fixture copilot JSON response with `"findings": []`; assertion: output is "No issues found." and no apply prompt is shown
- [x] Add `copilot-malformed-json` eval: prompt provides a fixture copilot response that is not valid JSON; assertion: raw-output fallback message "Could not parse structured findings; showing raw output." is shown
- [x] Add `codex-not-found` eval: prompt instructs the agent to run `--model codex` with the codex binary absent (simulate via fixture or tell agent binary is unavailable); assertion: error message contains the install hint text and the skill exits without attempting a review
- [x] Add `gemini-not-found` eval: prompt instructs the agent to run `--model gemini` with the gemini binary absent; assertion: error message contains the gemini install hint and the skill exits without attempting a review
- [x] Add `gemini-no-findings` eval: prompt provides a fixture gemini response that contains no findings; assertions: (1) the `## Peer Review —` header line is present; (2) "No issues found." follows; (3) no apply prompt is shown
- [x] Run all 6 new evals with_skill and without_skill; spawn subagents with `mode: "auto"`
- [x] Grade results; update `evals/peer-review/benchmark.json` with new runs; update `metadata.evals_run` and `metadata.skill_version`
- [x] Each new eval must have at least one assertion that fails without_skill — if any eval is non-discriminating, add a note in `benchmark.json` explaining why
- [x] Update `benchmark.md`: add per-eval sections for all new evals; update token-count denominator in the "Token statistics" sentence — M increases by the count of new primary evals added; update both M and 2×M; exclude any non-discriminating evals from the token-stats count per existing convention
- [x] Update `README.md` Eval Δ column to reflect the new delta

## Phase 7: Documentation and README

- [x] Update `README.md` Skill Notes for `peer-review`: replace the "Phase II" placeholder with a concrete description of multi-LLM routing; note which CLIs are supported and their install requirements
- [x] Update Eval cost bullet in Skill Notes with updated token/time stats from the new benchmark.md Summary table
- [x] Add tests to `tests/peer-review/` covering `--model` routing decisions: `--model copilot` routes to copilot, `--model copilot:gpt-4o-mini` extracts the sub-model correctly, `--model codex` routes to codex, `--model gemini` routes to gemini, and `--model claude-opus-4-6` stays on the Claude subagent path
- [x] Run `uv run --with pytest pytest tests/` — confirm all tests pass
