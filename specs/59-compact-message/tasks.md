# Spec 59: Tasks — compact-message

## Phase 1: Tests first

- [x] **1.1** Create `tests/compact-message/conftest.py` with `is_help_request(args)` (exact, case-insensitive, whitespace-trimmed match on `help`/`--help`/`-h`/`?`) and `focus_text(args)` (trimmed text, or `None` for empty/help) — reference implementations mirroring the SKILL.md Arguments rules
- [x] **1.2** Create `tests/compact-message/test_compactmessage_arguments.py` — help triggers, case/whitespace variants, non-help args (`help me`, `-help`, `??`, empty, whitespace-only), focus-text passthrough
- [x] **1.3** Create `tests/compact-message/test_compactmessage_structure.py` — the SKILL.md and options.md structural assertions listed in plan.md **Testing** (frontmatter, gapless steps, Security model placement immediately before `## Process`, Step 4 rules, Step 5 fence/MANDATORY/stop-generating language, compaction-command portability note, options.md triggers)
- [x] **1.4** Run `uv run --with pytest pytest tests/compact-message/ -v` — confirm the structure tests fail (SKILL.md not yet written)

---

## Phase 2: Skill

- [x] **2.1** Create `skills/compact-message/SKILL.md`:
  - Frontmatter: `name`, `description` (with trigger phrases; ≤ 500 chars — count before finalizing), `license: MIT`, `metadata` author/repository/version `"0.1"`
  - `## Arguments` — `$ARGUMENTS` phrasing per root CLAUDE.md Portability; help routing to `references/options.md`; focus-text precedence
  - `## Security model` — per `specs/36-snyk-scan-baseline/template.md`, placed immediately above `## Process` (not between steps — a `##` heading there would orphan Steps 2–5)
  - `## Process` Steps 1–5 as in plan.md
  - `## Notes` — near-empty session, focus/inference conflicts, why the skill cannot run `/compact` itself
- [x] **2.2** Create `skills/compact-message/references/options.md` — usage, help triggers, focus-text examples, output shape
- [x] **2.3** Create a local symlink `.claude/skills/compact-message` in the checkout the manual-test session (5.4) will launch from, targeting this worktree's absolute `skills/compact-message` path (gitignored; `.claude/skills/` is sandbox-protected — lift the sandbox or have the user run it)
- [x] **2.4** Run `uv run --with pytest pytest tests/compact-message/ -v` — all pass

---

## Phase 3: CI and security baseline

- [x] **3.1** Create `.github/workflows/test-compact-message-skill.yml` from `test-learn-skill.yml`, paths `skills/compact-message/**` and `tests/compact-message/**`; drop the fixtures `upload-artifact` step (no fixtures dir)
- [x] **3.2** Add `compact-message` to `SKILLS` in `evals/security/scan.sh`
- [ ] **3.3** Create `evals/security/compact-message.baseline.json` — run `bash evals/security/scan.sh --update-baselines --confirm` if `SNYK_TOKEN` is available, then `git checkout --` every other baseline the run rewrote; otherwise stop and ask the user to run the scan locally — do not commit `"findings": []` without a scan, which fails CI on the first real finding when the `SNYK_TOKEN` secret is configured

---

## Phase 4: Documentation

- [x] **4.1** Add `compact-message` row to the Available Skills table in `README.md` (alphabetical; Eval Δ `—`) and a `### compact-message` Skill Notes section
- [x] **4.2** If any `CLAUDE.md` rule is added or changed, mirror it to `.github/copilot-instructions.md`

---

## Phase 5: Verification

- [x] **5.1** `npx cspell` on every new/modified file; add new words to `cspell.config.yaml` in alphabetical order
- [x] **5.2** `uv run --with pytest pytest tests/` — full suite, no regressions (sandbox lifted)
- [x] **5.3** Re-read `skills/compact-message/SKILL.md` end-to-end against plan.md
- [ ] **5.4** Manual check: in a **fresh** session (skill content is cached at session load) with the 2.3 symlink in place, run `/compact-message` and `/compact-message help` on a non-trivial conversation; confirm single line, `/compact ` prefix, concrete identifiers, rationale bullets, stop after output
- [x] **5.5** Re-read both `plan.md` and `tasks.md` end-to-end — verify consistency
