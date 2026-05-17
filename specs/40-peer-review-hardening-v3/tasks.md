# Tasks: peer-review Security Hardening v3

## Phase 1 — Spec scaffolding

- [x] Write `specs/40-peer-review-hardening-v3/plan.md` with problem, threat model recap, design (six items), files to modify, verification, and risks.
- [x] Write `specs/40-peer-review-hardening-v3/tasks.md` (this file).

## Phase 2 — SKILL.md edits

- [x] Bump `metadata.version` from `"1.11"` to `"1.12"` in `skills/peer-review/SKILL.md`. Single bump for the PR.

- [x] Add a one-line `> **Security note** — …` banner immediately above the `\`\`\`bash` fence under `**PR** (`--pr N`):` in Step 2. Cross-references the `## Security model` section and names Step 2b.

- [x] Insert a new `### 2b. Screen PR Content for Prompt Injection (PR target only)` step between `### 2. Collect Content` and `### 3. Select Prompt Template`. Contents:
  - Skip rule (`--staged`, `--branch`, path → skip; only `--pr N` runs the screen).
  - Screening-independence invariant prose.
  - `$PR_CONTENT` assembly (title + body + diff).
  - 256 KB `SCREEN_LIMIT` size guard with `OVERSIZED` flag.
  - Case-sensitive POSIX-ERE pattern TSV block (seven patterns).
  - Case-insensitive POSIX-ERE pattern TSV block (one pattern).
  - Unicode byte-scan group (zero-width / bidi + Cyrillic adjacency).
  - `screen_context()` helper analogous to `redact_context()` from Step 4b.
  - Per-pattern iteration loops accumulating `hits`.
  - Confirmation surfacing with `<flagged>` redaction and `[y/N]` pause language matching Step 4b.
  - Note on interaction with `--model copilot/codex/gemini` (screening occurs before external CLI invocation).
  - Closing note that the regex set is heuristic and the screening pause is one defense layer alongside boundary markers (Step 3) and the external-CLI triage layer (Step 4f).

- [x] Update the existing Step 4 callout `**See the Security model section above for the full trust model and pre-flight checks.**` to also mention Step 2b screening alongside Step 4b secret scan.

- [x] Append four new bullets to the Mitigations list in `## Security model`:
  - **PR-content screening pass** — what Step 2b does and when.
  - **Screening-independence invariant** — pause is byte-decided, not agent-decided.
  - **PR-content size guard** — 256 KB cap rationale.
  - **Security-note adjacency** — describes the new banner above the `gh pr view` sub-block.

- [x] Append new bullets to the Residual risks list:
  - **Screening-regex heuristic** — novel obfuscation can bypass.
  - **Cyrillic-adjacency false positives** — non-English PRs may trigger the pause.
  - **No `--no-screen` escape hatch** — `--branch` / `--staged` skip Step 2b instead.
  - **Secret-scan path asymmetry (W007)** — Step 4b runs only on the external-CLI path; documents the structural gap and points to follow-up.

- [x] Replace the `### Why W011 and W012 still appear` subsection with the expanded `### Why W007, W011, and W012 still appear` version that:
  - Names the new mitigations (screening pass, screening-independence, size guard, adjacency banner) alongside the existing ones (argument validation, boundary markers, stdin transport, secret scan, triage layer).
  - Explains W007 as a pre-existing structural property newly surfaced under v1.12's improved security documentation.
  - Reaffirms the baseline-pinning rationale and points to `evals/security/CLAUDE.md`.

- [x] Tighten argument validation in Step 1: `--pr` regex bumped from `^[1-9][0-9]*$` to `^[1-9][0-9]{0,5}$` (6-digit cap); `--branch` regex bumped from `^[A-Za-z0-9._/-]+$` to `^[A-Za-z0-9._/-]{1,255}$` AND a `..`-sequence rejection (matches git's own ref-name rule). Error messages updated to reflect the new constraints.

## Phase 3 — Tests

- [x] Extend `tests/peer-review/conftest.py` with screening helpers:
  - `should_run_pr_screening(target_type: str) -> bool` — returns True only for `"pr"`.
  - `pr_screen(content: str) -> list[tuple[str, str]]` — runs all 10 patterns (7 case-sensitive + 1 case-insensitive + 2 unicode/adjacency) and returns `[(pattern_name, matched_substring), …]`. Translates POSIX ERE → Python regex following the same approach as `secret_scan` (explicit `[ \t]` for spaces, line-by-line iteration where applicable).
  - `screen_size_guard(content: str, limit: int = 262144) -> tuple[str, bool]` — returns `(possibly_truncated, oversized_flag)`.
  - `route_screening_response(response: str | None) -> str` — mirrors `route_confirmation_response`.

- [x] Create `tests/peer-review/test_pr_screening.py`:
  - Dispatch by target type (4 tests): staged/branch/path → False; pr → True.
  - Per-pattern positive cases for each of the 10 families.
  - Per-pattern negative cases for false-positive-prone patterns (override imperative on benign English, sk- inside `risk-`/`task-`/`disk-`, base64 length threshold, Cyrillic without adjacency word, etc.).
  - Multi-pattern combined input → all hits reported.
  - Size guard: under limit (passthrough), exactly limit (passthrough), over limit (truncated + flagged).
  - Confirmation routing: `y`/`Y`/` y `/`y\n` → proceed; `n`/`no`/`yes`/empty/None → abort.

- [x] Append an adversarial-args regression block to `tests/peer-review/test_peer_review_argument_parsing.py`:
  - Import `ADVERSARIAL_ARGS` and `ADVERSARIAL_TEXT_ARGS` from `tests/_helpers/argument_injection.py`.
  - Parametrized test: every `ADVERSARIAL_ARGS` entry fed as `parse_arguments(["--pr", bad])` produces a non-None `error`.
  - Parametrized test: every `ADVERSARIAL_TEXT_ARGS` entry fed as `parse_arguments(["--branch", bad])` produces a non-None `error`.

## Phase 4 — Baseline refresh

- [x] Update `evals/security/peer-review.baseline.json`:
  - `skill_version` → `"1.12"`.
  - `captured_at` → `"2026-05-17"`.
  - `findings` → add `W007` (high) alongside existing `W011` / `W012` (heuristic asymmetry surfaced under v1.12).
  - `notes` → expanded prose naming spec 40, the new screening pass, size guard, screening-independence invariant, adjacency banner, argument-validation length caps, and the W007 rationale.

## Phase 5 — Spellcheck and CI hygiene

- [x] Run `npx cspell skills/peer-review/SKILL.md tests/peer-review/test_pr_screening.py specs/40-peer-review-hardening-v3/plan.md specs/40-peer-review-hardening-v3/tasks.md` and add any flagged words to `cspell.config.yaml` in alphabetical order. Added: `behaviour`, `bidi`, `codepoint`, `metachar`, `roleplay`, `zalgo`. Cyrillic test-fixture strings carry `# cspell:disable-line` per project rule.

## Phase 6 — Verification

- [x] `uv run --with pytest pytest tests/peer-review/ -v` — all green (287 passed, 1 skipped).
- [x] `bash evals/security/scan.sh` (no `--update-baselines`) — exits 0; baseline matches (W007 heuristic, fires intermittently — pinned to avoid CI flake).
- [x] `rg '^  version:' skills/peer-review/SKILL.md` → `version: "1.12"`.
- [x] `git fetch origin && git diff origin/main -- skills/peer-review/SKILL.md | rg '^\+  version:' | wc -l` → exactly `1`.
- [x] Baseline schema check: `python3 -c "import json; d=json.load(open('evals/security/peer-review.baseline.json')); assert d['skill_version']=='1.12' and d['captured_at']=='2026-05-17'; print('OK')"`.

## Phase 7 — Optional follow-ups (out of scope for this PR)

- [ ] Eval pass-rate sanity check: `uv run python -m evals.runner peer-review` — compare to current `benchmark.json` baseline; document any delta ≥3% in the PR description.
- [ ] If `SNYK_TOKEN` is available, run `bash evals/security/scan.sh --update-baselines --confirm` for a fresh scan; otherwise note in the PR description that the baseline was hand-edited and the scanner was not re-run locally.
