# Tasks — Remove Gemini CLI support from `peer-review`

## 1. `skills/peer-review/SKILL.md`

- [x] Bump `metadata.version` to `"1.15"` (once for the whole PR)
- [x] Frontmatter: drop `Gemini` from the routed-CLI list and drop the `"review with Gemini"` trigger phrase
- [x] Help block: drop `gemini[:submodel]` from the `External CLIs:` line and delete the `@google/gemini-cli` install line
- [x] Routing: delete the `| gemini | gemini | -m SUBMODEL |` dispatch row and the gemini install hint
- [x] Routing: drop `gemini[:submodel]` from **both** copies of the `Unsupported --model value:` string; narrow the prefix check to "does not match `copilot` or `codex`"
- [x] Routing: `(external CLI path — copilot, codex, gemini)` → `(copilot, codex)`
- [x] Security model: rename the stdin bullet to `**Stdin transport for codex**`, delete the gemini clause, keep the `codex exec -` sentinel description and the copilot-argv exception
- [x] Security model: update the cross-reference to that bullet in the W007/W011/W012 paragraph (it names the bullet by title)
- [x] Security model: `copilot/codex/gemini` → `copilot/codex` in the triage, context-isolation, provenance, third-party-exposure, and W012 sentences
- [x] Residual risks: "gemini and codex retain stdin transport" → "codex retains stdin transport"
- [x] Step 4c rationale: rewrite so codex is the sole stdin CLI, and re-point the `ARG_MAX` fallback advice to `--model codex` only

## 2. `skills/peer-review/references/cli-invocations.md`

- [x] Header: `(copilot / codex / gemini)` → `(copilot / codex)`
- [x] Delete the gemini rationale sentence and its entire invocation block (the only executable gemini shell-out in the repo)
- [x] Step 4e: `All three CLIs (copilot, codex, gemini)` → `Both CLIs (copilot, codex)`

## 3. `tests/peer-review/`

- [x] `conftest.py`: delete the `elif prefix_lower == "gemini"` branch and drop gemini from the `ValueError` message and all docstrings
- [x] `test_model_routing.py`: delete `TestGeminiRouting` and `test_gemini_parses_as_prose`; shrink the parse-path set literal to 2 elements
- [x] `test_model_routing.py`: rename `test_reference_file_states_copilot_parsed_like_codex_gemini` → `…_like_codex`
- [x] `test_secret_scan.py`: drop the gemini parametrize entries and the docstring mention
- [x] `test_triage_routing.py`: drop gemini from the route tuple and delete the two gemini triage tests (replace one with a codex-submodel case)
- [x] Add a `TestGeminiRemoved` class: both `gemini` and `gemini:gemini-2.0-flash` raise `ValueError`; the message enumerates exactly self / claude-\* / copilot / codex; `SKILL.md` and `cli-invocations.md` contain no `gemini` substring

## 4. `evals/peer-review/`

- [x] `evals.json`: repurpose eval 9 → `gemini-model-removed` with the unsupported-model, no-binary-check, and no-install-hint assertions
- [x] `evals.json`: delete eval 10 (`gemini-no-findings`) — do not renumber
- [x] `evals.json`: re-point eval 16's `--model gemini` → `--model copilot`
- [x] `evals.json`: drop gemini from eval 26's `expected_output`, `context`, and `supported-options-listed` assertion
- [x] `benchmark.json`: delete the 4 eval-10 runs
- [x] `benchmark.json`: null all result fields and nested `expectations[].passed`/`.evidence` on the stale 4-6/4-7 entries for evals 9, 16, 26 (both configurations)
- [x] Re-run evals 9, 16, 26 × {with_skill, without_skill} on the current model cohort; grade against the full assertion text
- [x] `benchmark.json`: add the new cohort's runs, add a `models_tested` entry, update `metadata.evals_run`, keep `skill_version` at `"1.7"` and extend `skill_version_note`
- [x] `benchmark.json`: recompute `run_summary` and `run_summary_by_model` (sample stddev, N−1; delta from unrounded means, signed strings at 2dp)
- [x] `benchmark.md`: update the results table, rewrite eval 9's section, delete eval 10's, update eval 16's scenario line, fix the unsupported-model narrative, add a v1.15 changelog entry, update the Summary table and the token-denominator sentence
- [x] `README.md`: update the peer-review `Eval Δ` column and the `Eval cost` bullet

## 5. `evals/security/peer-review.baseline.json`

- [x] Run `bash evals/security/scan.sh` (bare — no `--update-baselines`) and confirm no new finding ID
- [x] Hand-edit `skill_version`, `captured_at`, and the `notes` prose; leave `findings` unchanged

## 6. Docs

- [x] `README.md`: peer-review trigger phrases, multi-LLM routing bullet, triage bullet, security-model bullet (leave the `learn` row alone)
- [x] `docs/imgs/peer-review-flow.mmd`: both `(copilot/codex/gemini)` labels

## 7. `CLAUDE.md` + mirror

- [x] `CLAUDE.md`: trim the external-CLI sandbox gotcha to copilot/codex
- [x] `.github/copilot-instructions.md`: mirror that edit (required by the `instruction-sync` CI check)
- [x] `.github/copilot-instructions.md`: skill index row → `"review with Copilot/Codex"`

## 8. Verification

- [x] Scoped `rg -i gemini` returns only the sanctioned survivors
- [x] `rg -w geminicli cspell.config.yaml` still justified by `specs/`
- [x] `Unsupported --model value` strings agree across SKILL.md and conftest.py
- [x] `uv run --with pytest pytest tests/ -q`
- [x] JSON integrity on all three edited JSON files
- [x] `npx cspell "skills/**/*.md" "specs/**/*.md"`
- [x] Expectation-schema `jq` check returns `0`
