# Tasks: peer-review Security Hardening v3

## Phase 1 — Spec scaffolding

- [x] Write `specs/41-peer-review-hardening-v3/plan.md` with problem, threat model recap, design (six items), files to modify, verification, and risks.
- [x] Write `specs/41-peer-review-hardening-v3/tasks.md` (this file).

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
  - **Secret-scan path asymmetry (W007)** — Step 4b runs only on the external-CLI path; the structural gap is what the heuristic scanner flags as W007, and it is pinned in the baseline at `high` so future re-emergence is captured as part of the documented heuristic surface rather than silently regressing.

- [x] Rewrite the `### Why W007, W011, and W012 still appear` subsection to:
  - Name the new mitigations (screening pass, screening-independence, size guard, adjacency banner) alongside the existing ones (argument validation, boundary markers, stdin transport, secret scan, triage layer).
  - Document W007 (Step 4b path asymmetry) alongside the existing W011/W012 explanations. Note that all three findings are heuristic on call signatures the skill genuinely needs, and that closing them structurally would require removing the underlying features.
  - Narrate the W013 add→clear arc: W013 (attempt to modify system services) was added during the I-iteration when a cleanup-index file pattern was introduced at a deterministic path under `$TMPDIR/peer-review-pr-cleanup-index`, and cleared during the J-iteration when it was replaced by a per-invocation `mktemp -d` directory at mode 700 — no fixed-path side-effect remains for the scanner heuristic to match against.
  - Reaffirm the baseline-pinning rationale for W007/W011/W012 and point to `evals/security/CLAUDE.md`. Explain that pinning a currently-firing finding documents the heuristic baseline without masking anything — there is nothing to mask while the finding still fires.

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
  - Per-pattern negative cases for false-positive-prone patterns (override imperative on benign English, base64 length threshold below the 200-char bar, role-impersonation against benign phrasing, Cyrillic codepoint without an adjacency word, etc.).
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
  - `findings` → `W007`, `W011`, `W012` (all high). W013 was cleared during J-iteration by switching to a per-invocation `mktemp -d` directory with mode-700 perms; it no longer fires under `snyk-agent-scan==0.5.1` and is therefore not pinned. The remaining three findings are reported deterministically against the current SKILL.md and accepted as the current scanner heuristic baseline. `scan.sh diff_findings()` gates only on new IDs or severity escalations — baselined findings are accepted as expected, so pinning a currently-firing finding documents the heuristic baseline without masking anything.
  - `notes` → expanded prose naming spec 41, the new screening pass, byte-accurate size guard (mode-600 `mktemp` + pipeline-free `head -c FILE`), whitespace normalization, screening-independence invariant, adjacency banner, argument-validation length caps, the Bash-3-compatible `while IFS= read -r line; do arr+=("$line"); done < <(...)` first-match selection inside `screen_context()`, and the rationale for pinning the three heuristic findings (W007/W011/W012) that still fire after spec-41 hardening.

## Phase 5 — Spellcheck and CI hygiene

- [x] Run `npx cspell skills/peer-review/SKILL.md tests/peer-review/test_pr_screening.py specs/41-peer-review-hardening-v3/plan.md specs/41-peer-review-hardening-v3/tasks.md` and add any flagged words to `cspell.config.yaml` in alphabetical order. Added: `bidi`, `codepoint`, `mapfile`, `metachar`, `readarray`, `roleplay`, `zalgo` (initial set also included `reframings` and `unbaselined`; both were removed after claude[bot] review confirmed they no longer appeared in any non-self-referential content). Cyrillic test-fixture strings carry `# cspell:disable-line` per project rule.

## Phase 6 — Verification

- [x] `uv run --with pytest pytest tests/peer-review/ -v` — all green (296 passed).
- [x] `bash evals/security/scan.sh` (no `--update-baselines`) — exits 0; baseline pins W007 + W011 + W012 (all high). W013 was cleared during J-iteration when the cleanup-index pattern was replaced by per-invocation `mktemp -d` at mode 700.
- [x] `rg '^  version:' skills/peer-review/SKILL.md` → `version: "1.12"`.
- [x] `git fetch origin && git diff origin/main -- skills/peer-review/SKILL.md | rg '^\+  version:' | wc -l` → exactly `1`.
- [x] Baseline schema check: `python3 -c "import json; d=json.load(open('evals/security/peer-review.baseline.json')); assert d['skill_version']=='1.12' and d['captured_at']=='2026-05-17'; print('OK')"`.

## Phase 7 — Optional follow-ups (out of scope for this PR)

- [ ] Eval pass-rate sanity check: `uv run python -m evals.runner peer-review` — compare to current `benchmark.json` baseline; document any delta ≥3% in the PR description.
- [ ] If `SNYK_TOKEN` is available, run `bash evals/security/scan.sh --update-baselines --confirm` for a fresh scan; otherwise note in the PR description that the baseline was hand-edited and the scanner was not re-run locally.
