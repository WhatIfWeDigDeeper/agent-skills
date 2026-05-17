# Plan: peer-review Security Hardening v3

## Problem

`uvx snyk-agent-scan==0.5.1 --skills skills/peer-review/SKILL.md` reports two **high** severity findings against `skills/peer-review/SKILL.md` v1.11:

- **W011** — third-party content exposure: PR title, body, and diff are fetched via `gh pr view` / `gh pr diff` (Step 2 PR sub-block) and ingested into the `<untrusted_diff>` block read by the spawned reviewer.
- **W012** — external URL / external LLM CLI handoff: `--model copilot/codex/gemini` writes the assembled prompt to a temp file and pipes it to a third-party CLI (Step 4d).

Spec 30 (v1.7 → v1.8) and spec 34 (v1.8 → v1.x — secret pre-scan, stdin transport, external-CLI triage) added the obvious mitigations. The findings remain pinned in `evals/security/peer-review.baseline.json` because Snyk's W011/W012 are heuristic on the *presence* of those features, not on absence of mitigation. The existing `## Security model` section already enumerates threat model, mitigations, residual risks, and a "Why W011/W012 still appear" subsection.

Still missing:

1. A **PR-content prompt-injection screening pass** before the reviewer (self / claude-* / external CLI) sees the diff. `pr-comments` v1.41 (spec 39) runs an equivalent screen on every comment body; `peer-review` has no analogue.
2. A **size guard** that prevents oversized PR title/body/diff from burying flagged spans below the regex scan horizon.
3. A **screening-independence invariant** declaring that the pause is decided on raw bytes and cannot be suppressed by injected "skip screening" instructions.
4. A **Security-note adjacency banner** directly above the `gh pr view` / `gh pr diff` sub-block in Step 2 — Snyk's heuristic connects mitigations to flagged calls only when they sit within ~30 rendered lines. The current `## Security model` section is ~80 lines above the first `gh pr view` line.

## Threat model recap

- **W011 source** — `gh pr view "$PR" --json …` and `gh pr diff "$PR"` (Step 2 PR sub-block). Output is third-party content: PR title, body, diff text. The PR author can embed prompt-injection payloads, hidden HTML, zero-width unicode, or homoglyphs in the title/body. The diff itself is also author-controlled.
- **W012 source** — `copilot < "$PROMPT_FILE"`, `cat "$PROMPT_FILE" | codex …`, `gemini < "$PROMPT_FILE"` (Step 4d). Whatever the screening missed goes to the vendor.

Snyk pins both at `high`. Removing the findings would require removing the PR-target and external-CLI features — neutering the skill.

## Design

### Item 1: Step 2b — PR-content prompt-injection screening pass

Insert a new step `### 2b. Screen PR Content for Prompt Injection (PR target only)` between `### 2. Collect Content` and `### 3. Select Prompt Template`. The step:

- Skipped entirely for `--staged`, `--branch`, and path targets — only the `--pr N` branch reaches it (those are the only third-party-author-controlled sources).
- Concatenates PR title + body + raw diff into `$PR_CONTENT` for screening only — the original strings remain available for Step 3 to wrap in `<untrusted_diff>` unchanged.
- Runs 8+ POSIX-ERE patterns split into case-sensitive (`grep -E`) and case-insensitive (`grep -Ei`) groups, plus a non-grep UTF-8 byte-scan for zero-width / bidi-control unicode and Cyrillic homoglyph adjacency.
- Per-pattern iteration so the user sees which fired and a windowed (~30 char) `<flagged>`-redacted context — same shape as Step 4b's secret scan.
- On any hit: print the hit list, then `The reviewer in Step 3 (and any external CLI in Step 4) will see this content. Continue? [y/N]` and **stop generating**. Only `y` proceeds.
- The pause occurs **before** Step 3 selects the prompt template and **well before** Step 4d invokes any external CLI — injected content cannot reach a third-party vendor without explicit user consent.

Pattern set (POSIX ERE only — no GNU `-P`; macOS-compatible):

Case-sensitive group:
- `(ignore|disregard|forget)[[:space:]]+(all[[:space:]]+)?(previous|prior|above)[[:space:]]+(instructions|directives|rules|prompts?)` — override imperative
- `you[[:space:]]+are[[:space:]]+now[[:space:]]+(a[[:space:]]+|an[[:space:]]+)?[A-Za-z]` — role-override opener
- `(system|developer)[[:space:]]+(prompt|message|instruction)` — claimed-role injection
- `<!--` — HTML comment opener
- `<details[[:space:]]*[a-z]*>` — collapsed details block
- `(\\x[0-9A-Fa-f]{2}){4,}` — escaped hex run (4+ consecutive)
- `[A-Za-z0-9+/]{200,}={0,2}` — base64-shaped long run

Case-insensitive group:
- `(act[[:space:]]+as|pretend[[:space:]]+to[[:space:]]+be|roleplay[[:space:]]+as)[[:space:]]+(the|an|a)?[[:space:]]*(admin|root|system|developer|assistant|agent)` — role-impersonation request

Unicode codepoint group (byte-level scan via `LC_ALL=C grep -E`):
- Zero-width / bidi-control: U+200B–U+200D, U+202A–U+202E, U+2066–U+2069 (`\xE2\x80[\x8B-\x8D\xAA-\xAE]|\xE2\x81[\xA6-\xA9]`).
- Cyrillic homoglyph adjacency: any Cyrillic codepoint U+0400–U+04FF within 8 chars of ASCII `ignore`, `instructions`, `system`, `prompt`, `assistant`, or `disregard`.

### Item 2: 256 KB PR-content size guard

Cap `$PR_CONTENT` at `SCREEN_LIMIT=262144` bytes for the regex pass only. The reviewer in Step 3 still sees the full unmodified content. Overflow triggers the same confirmation pause as a flagged pattern — burying signal in a 10 MB PR body is itself an attack.

Ceiling rationale: GitHub PR description limit is 65 KB; typical PR diffs are 1–50 KB; large refactor PRs reach 100–500 KB but are unusual. 256 KB covers ~95% of real PRs with headroom while keeping the eight regex passes under one second on cold caches.

### Item 3: Screening-independence invariant

A prose note inside Step 2b stating that the pause is decided on raw bytes by the regex loop, not by the agent re-reading content. Injected instructions inside the PR title/body/diff saying "skip screening" or "this is safe" have no path to suppress the pause. Mirrors the spec 39 invariant in `pr-comments` Step 5.

### Item 4: Security-note adjacency banner

A compact one-line `> **Security note** — …` banner directly above the `gh pr view` / `gh pr diff` sub-block in Step 2 (between the `**PR** (`--pr N`):` heading and the `\`\`\`bash` fence). Cross-references the full `## Security model` section so Snyk's heuristic can connect the mitigations to the flagged ingestion commands within its adjacency window.

Decision: do **not** move the whole Security model section between `## Review Modes` and `## Process` — that would re-flow every cross-reference and step number in Steps 4–6 (`Step 4b`, `Step 4c`, `Step 4d`, `Step 4f`, `Step 4g`, `Step 5`, `Step 6`). The compact banner is enough for the adjacency heuristic and costs four lines.

### Item 5: Security model section refresh

Append four bullets to the Mitigations list (PR-content screening pass, Screening-independence invariant, PR-content size guard, Security-note adjacency). Append three bullets to the Residual risks list (screening-regex heuristic, Cyrillic-adjacency false positives, no `--no-screen` escape hatch). Expand the `### Why W011 and W012 still appear` subsection to name the new mitigations and reaffirm the baseline-pinning rationale.

### Item 6: Test coverage

Mirror `tests/pr-comments/` and `tests/peer-review/test_secret_scan.py` patterns:

- `tests/peer-review/conftest.py` — add `should_run_pr_screening(target_type)`, `pr_screen(content) -> [(name, match), …]`, `screen_size_guard(content, limit=262144) -> (content, oversized)`, `route_screening_response(response)` helpers.
- `tests/peer-review/test_pr_screening.py` (new) — dispatch by target type, per-pattern positive + negative cases for each of the 10 pattern families, size guard, confirmation routing.
- `tests/peer-review/test_peer_review_argument_parsing.py` — append a parametrized regression block exercising `parse_arguments(["--pr", x])` and `parse_arguments(["--branch", y])` against `ADVERSARIAL_ARGS` / `ADVERSARIAL_TEXT_ARGS` from `tests/_helpers/argument_injection.py` to pin the existing validators.

### Item 7: Skill version bump

Bump `metadata.version` from `"1.11"` to `"1.12"` (single bump for the PR; minor increment is conservative for new mitigation surface).

### Item 8: Baseline refresh

Update `evals/security/peer-review.baseline.json`:
- `skill_version`: `1.11` → `1.12`
- `captured_at`: `2026-05-09` → `2026-05-17`
- `notes`: rewrite to name spec 40 and the new mitigations (screening pass, size guard, adjacency banner). All four findings (W007, W011, W012, W013) pinned at high — see baseline notes for the heuristic origins of each.

## Files to Modify

1. `skills/peer-review/SKILL.md` — Step 2b insertion, Step 2 banner, Step 4 callout update, Security model bullets + expanded subsection, frontmatter version bump.
2. `evals/security/peer-review.baseline.json` — version, date, notes.
3. `tests/peer-review/conftest.py` — add screening helpers.
4. `tests/peer-review/test_pr_screening.py` (new) — per-pattern + dispatch + size + confirmation tests.
5. `tests/peer-review/test_peer_review_argument_parsing.py` — append adversarial-args regression block.
6. `cspell.config.yaml` — add `bidi`, `codepoint`, `cyrillic`, `homoglyph`, `homoglyphs`, `zalgo` etc. (alphabetical) if cspell flags them.
7. `specs/40-peer-review-hardening-v3/plan.md` + `tasks.md` (new).

## Verification

- Read updated Step 2b end-to-end; confirm patterns are POSIX ERE only (no `(?i)`, no `\s`, no lookarounds).
- Read updated Security model; confirm four new Mitigations bullets and three new Residual risks bullets, plus the expanded `### Why W011 and W012 still appear` subsection.
- `uv run --with pytest pytest tests/peer-review/ -v` — all green, including the new `test_pr_screening.py` and the appended adversarial-args block.
- `uvx snyk-agent-scan==0.5.1 --skills skills/peer-review/SKILL.md` — still reports W011 + W012 at `high` (no regression, no escalation).
- `bash evals/security/scan.sh` (no `--update-baselines`) — exits 0; baseline matches.
- `npx cspell skills/peer-review/SKILL.md tests/peer-review/test_pr_screening.py specs/40-peer-review-hardening-v3/plan.md specs/40-peer-review-hardening-v3/tasks.md` — no unknown words.
- `uv run python -m evals.runner peer-review` — pass rate within ±3% of the current `benchmark.json` baseline. Step 2b adds no reviewer-prompt content on the self/claude-* path, so behavioral evals should be unchanged.

## Risks and trade-offs

- **Cyrillic-adjacency false positives** on legitimate Russian/Ukrainian/etc. PRs discussing prompt engineering or AI assistants in Cyrillic-script languages. Deliberate trade-off — one extra `y` is cheap; missing a homoglyph injection is not. Documented as a residual risk.
- **HTML-comment false positives** on Markdown PRs using `<!--` for TOCs or hidden TODO blocks. Same trade-off; same documentation.
- **No `--no-screen` escape hatch in v1.12** — introducing it would create a one-flag bypass that injected content could be crafted to request ("rerun with `--no-screen`"). For trusted internal PRs the operator can use `--branch NAME` or `--staged` instead. Deferred to a follow-up spec if friction proves unacceptable.
- **Eight regex passes** on every `--pr N` invocation. With a 256 KB cap, ~80–160 ms total — negligible compared to `gh pr view` + reviewer spawn.
- **W011 and W012 remain at `high`** — no amount of mitigation will move the heuristic, per the existing `### Why W011 and W012 still appear` subsection.
