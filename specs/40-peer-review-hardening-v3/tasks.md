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
  - **Secret-scan path asymmetry (W007)** — Step 4b runs only on the external-CLI path; documents the structural gap that the `W007` heuristic surfaces and points to follow-up.

- [x] Rewrite the `### Why W007, W011, and W012 still appear` subsection to:
  - Name the new mitigations (screening pass, screening-independence, size guard, adjacency banner) alongside the existing ones (argument validation, boundary markers, stdin transport, secret scan, triage layer).
  - Record that W007 reflects the existing structural asymmetry of Step 4b (external-CLI path only) and fired intermittently during spec 40 development; closing it fully requires a behavior change deferred to a follow-up spec.
  - Reaffirm the baseline-pinning rationale for W007/W011/W012 and point to `evals/security/CLAUDE.md`.

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
  - `findings` → keep `W011` and `W012` (high) and pin `W007` (high) as a regression anchor. W007 fired intermittently during spec 40 development depending on how the `## Security model` prose framed the Step 4b asymmetry, and currently clears 20/20 against the post-peer-review-pass SKILL.md. Pinning anchors against re-emergence on future edits or scanner updates. Justification recorded in the baseline `notes` field.
  - `notes` → expanded prose naming spec 40, the new screening pass, byte-accurate size guard, whitespace normalization, screening-independence invariant, adjacency banner, argument-validation length caps, and the W007 heuristic-anchor framing.

## Phase 5 — Spellcheck and CI hygiene

- [x] Run `npx cspell skills/peer-review/SKILL.md tests/peer-review/test_pr_screening.py specs/40-peer-review-hardening-v3/plan.md specs/40-peer-review-hardening-v3/tasks.md` and add any flagged words to `cspell.config.yaml` in alphabetical order. Added: `bidi`, `codepoint`, `metachar`, `roleplay`, `zalgo`. Cyrillic test-fixture strings carry `# cspell:disable-line` per project rule.

## Phase 6 — Verification

- [x] `uv run --with pytest pytest tests/peer-review/ -v` — all green (287 passed, 1 skipped).
- [x] `bash evals/security/scan.sh` (no `--update-baselines`) — exits 0; baseline pins W007 + W011 + W012 (all high).
- [x] `rg '^  version:' skills/peer-review/SKILL.md` → `version: "1.12"`.
- [x] `git fetch origin && git diff origin/main -- skills/peer-review/SKILL.md | rg '^\+  version:' | wc -l` → exactly `1`.
- [x] Baseline schema check: `python3 -c "import json; d=json.load(open('evals/security/peer-review.baseline.json')); assert d['skill_version']=='1.12' and d['captured_at']=='2026-05-17'; print('OK')"`.

## Phase 7 — Optional follow-ups (out of scope for this PR)

- [ ] Eval pass-rate sanity check: `uv run python -m evals.runner peer-review` — compare to current `benchmark.json` baseline; document any delta ≥3% in the PR description.
- [ ] If `SNYK_TOKEN` is available, run `bash evals/security/scan.sh --update-baselines --confirm` for a fresh scan; otherwise note in the PR description that the baseline was hand-edited and the scanner was not re-run locally.
