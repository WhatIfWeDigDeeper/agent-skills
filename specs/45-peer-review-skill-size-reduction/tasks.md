# Spec 45: Tasks — peer-review split 702-line SKILL.md into reference files (context-cost refactor)

## Phase 0: Pre-spec peer review (consistency pass on plan.md and tasks.md)

> **Status:** Run. The nominal iteration cap is 2, but each pass surfaced a real, substantive finding (iteration 3 caught a genuine security design gap — the 4c+4d single-Bash-call invariant), so the loop continued past the cap to convergence rather than stopping with a known defect outstanding.

*Use the local `claude` CLI, not `/peer-review`. Always pass `-p` for non-interactive mode. The command can take several minutes.*

- [x] **0.1** Confirm work is on branch `spec-45-peer-review-skill-size-reduction`.
- [x] **0.2** Stage only the spec docs:
  ```bash
  git add specs/45-peer-review-skill-size-reduction/plan.md specs/45-peer-review-skill-size-reduction/tasks.md
  ```
- [x] **0.3** Run the pre-spec consistency review:
  ```bash
  claude -p "review staged files"
  ```
  Apply valid findings, decline invalid findings with a short reason, and rerun until zero valid findings or iteration cap 2.
- [x] **0.4** Record per-iteration summary inline in this task. Format: `Iteration N: K valid findings (X critical, Y major, Z minor). Applied all. {Brief note on themes.}`
  - Iteration 1: 2 valid findings (0 critical, 1 major, 1 minor). Applied both. Major — Move 1 left two interleaved prose paragraphs unclassified: the `Implementation note…` paragraph (added to the move list as mechanics) and the trailing PCRE paragraph, which is mixed — its PCRE-alternative half moves but its "Do not move this scan to after Step 4c" ordering sentence is a when-the-scan-runs decision and must stay inline (now split explicitly in plan §Move 1 + tasks 2.1). Minor — the `No issues recommended.` anchor matches two locations (Step 5 template, which moves; Step 6 PR-URL-rule bullet, which stays); qualified the anchor in plan §Move 4 + tasks 2.4. Theme: anchor/classification precision for blocks with interleaved decision prose.
  - Iteration 2: 1 valid finding (0 critical, 1 major, 0 minor). Applied. Major — Move 3 mis-attributed the which-CLI dispatch decision + binary/sub-model table to Step 4d's keep-inline list, but that table actually lives in the Step 4 external-CLI preamble (above Step 4a); Step 4d itself is pure execution and moves in full. Reframed Move 3 in plan §Move 3 + tasks 2.3 to mark the preamble as outside-scope/untouched, and fixed the two stale "Step 4d which-CLI dispatch table" references in the verification checks (plan §Verification 5 + tasks 4.5). Theme: step-number drift between named decision and its actual location.
  - Iteration 3: 1 valid finding (1 major — security design gap, 0 critical/minor). Applied fix (a). Major — Move 3 would have split the 4c+4d single-Bash-call security invariant across a file boundary: Step 4c (`$PROMPT_FILE` write) stays inline while Move 3 relocated 4d's bash that consumes/cleans it, so the subshell-scoped `$PROMPT_FILE` would be lost (CLI reads `/dev/null`) or an unredacted-diff temp file stranded on disk. Fix: move the entire write → invoke → cleanup unit as one contiguous block into `cli-invocations.md`; keep the invariant statement + 4c security-rationale prose inline; handoff restates the single-call requirement. Updated plan §Move 3, §Files-to-Modify, §Verification 5a, §Risks; tasks 2.3, 2.7, 4.3. Theme: relocating content that shares live subshell state with content that stays inline.
  - Iteration 4: 2 valid findings (0 critical, 1 major, 1 minor). Applied both. Major — the `Implementation note:` paragraph that Move 1 relocates contains two relative-position cross-references ("the prompt template (lines above)" → the y/N confirmation prompt that stays inline; "The patterns above" → the casing/pattern description list that stays inline); a verbatim move would leave both dangling. Added a re-pointing instruction to plan §Move 1 + tasks 2.1. Minor — Phase 0 checkboxes 0.1–0.3 were unchecked despite 0.4 recording completed iterations; checked them off. Theme: relative-position references break when only one side of the reference moves.
  - Iteration 5: 2 valid findings (0 critical, 2 major). Applied both. Major #1 — Move 2 contradicted constraint 2: the `<untrusted_diff>`/`<untrusted_files>` wrappers (SKILL.md 210–217 / 255–262) are *interior* to the prompt bodies Move 2 relocates, so they cannot stay inline as the original constraint 2 demanded; and Verification 4.2's bare `rg untrusted_diff` would false-pass on inline mentions at lines 79/171/602. Resolved with option (b): the wrapper moves with the prompt (the imperative handoff keeps it in the constructed prompt); the inline injection-defense statement that stays is the `## Security model` "Untrusted-content boundary markers" bullet (line 79). Rewrote constraint 2, Move 2, Verification 4.2 (plan + tasks 4.2), and the 2.7 coherence check. Major #2 — Move 3 enumerated only the 4d *bash* to move, leaving the 4d narration prose (CLI_RC capture 495, cleanup 532, CLI_RC-scope 538, sentinel 546) inline where it would dangle against moved bash; clarified that 4d narration prose moves *with* its bash, opposite to the 4c security-rationale prose which stays (plan §Move 3 + tasks 2.3), and bumped the Move 3 estimate ~70→~85. Theme: interior/interleaved content inherits its container's move.
  - Iteration 6: 1 valid finding (0 critical, 0 major, 1 minor). Applied. Minor — the Move 3 heading still read "≈70 lines out" while its Net line and iteration-5 summary said ~85; updated the heading to "≈85 lines out" for internal consistency. (Reviewer also noted, as a non-finding, that hardcoded SKILL.md line numbers will drift post-edit — harmless since every one is paired with a phrase anchor and the verification commands grep phrases, not numbers, per constraint 5.) Theme: consistency between a section heading and its body after a late estimate change.
  - Iteration 7: 2 valid findings (0 critical, 1 major, 1 minor) + 1 optional nit. Applied all. Major — Move 2 mishandled the `[FOCUS_LINE]` mechanic, the same interior-content class as `<untrusted_*>`: the placeholder is interior to both prompt bodies (231/276), so its substitution instruction (279) and literal (281) must move with the templates, yet the keep-inline list said "keep the instruction to substitute the focus area" — contradicting the handoff and leaving two dangling references. Fixed Move 2 (plan + tasks 2.2): the whole focus-line mechanic moves; only a high-level "applied per the reference" pointer stays inline. Minor — Move 4 left the self/Claude apply-prompt variant (663) unclassified just past the main-template anchor; specified it moves with the main template (plan + tasks 2.4). Nit — per-move estimates sum to ~338 out → ~380 final, below the stated ~390 floor; adjusted the Goal to ~380–430 and noted the per-move figures are upper bounds. Theme: the interior-content-moves-with-its-container rule applied to the last two not-yet-moved interleaved pieces.
  - Iteration 8: 2 valid findings (0 critical, 0 major, 2 minor) + 1 trivial note. Applied both. Minor #1 — cspell failed on a non-dictionary word in the iteration-7 summary; reworded it to "not-yet-moved" (Phase 4.9 cspell scans these spec files and they commit at 0.5, so it was a live CI failure). Minor #2 — the §Risks "Snyk baseline drift" paragraph said "no mitigation surface changes," but `scan.sh` scans only SKILL.md (not `references/`), so relocating W012/W007 trigger text out of SKILL.md may legitimately *reduce* scan output; clarified this is a harmless subset of the pinned superset and added a "do not refresh down to the subset" warning (W011 unaffected — its trigger is in Step 1/2); aligned tasks 4.10. Trivial — corrected the self/Claude apply-prompt cite 663→664 in both files (anchor was already exact). Theme: CI-surface (cspell) and security-scan-surface precision.
  - Iteration 9: 2 valid findings (0 critical, 1 major, 1 minor). Applied both. Major — Move 4 lacked the re-point instruction that Moves 1 and 3 carry: the kept-inline `[model]` rule ("In all output blocks below…", 615) and stop-generating line ("Output this as your final message", 666) both point back at the templates that move, so a literal move dangles both; added a re-point bullet to plan §Move 4 + tasks 2.4. Minor — Verification 5a / tasks 4.3 used a bare `rg 'single Bash tool call'` that false-passes on the lowercase Security-model line 81 (never moves); changed to the uppercase-`MUST` form that isolates the Step 4c invariant at line 487 (same false-pass class the spec fixed for `untrusted_diff` in 4.2). Theme: applying the spec's own re-point and false-pass-discriminator rigor uniformly across all four moves and verification checks.
  - Iteration 10: 2 findings (0 critical, 0 major, 1 minor, 1 trivial). Applied both. Minor — Move 3's iteration-5 "moves with its bash" enumeration was meant to be exhaustive but omitted the `$WORKDIR`-creation guard paragraph (line 497), a fifth 4d-narration paragraph of the same class; added it to plan §Move 3 + tasks 2.3 (outcome-neutral — it sits inside the contiguous block that moves regardless, but keeps the enumeration honest). Trivial — corrected the stop-generating cite 667→666 in both files (667 is blank; anchor already exact). Reviewer confirmed no blocking findings and the spec converged. Theme: enumeration completeness and line-cite parity.
  - Iteration 11: 0 valid blocking findings — reviewer verdict "ready to commit." Applied one pre-approved, behavior-neutral consistency nit (Move 3's general re-point directive now also enumerates the specific line-487 "see also the Cleanup note below" forward reference, for parity with Moves 1/4). One no-change observation noted (Phase 3 uses `git show origin/main:` rather than `git show HEAD:` — equivalent on this branch and the more robust choice). Loop converged.
- [x] **0.5** Commit the post-review spec docs as a single commit before Phase 1 begins.

---

## Phase 1: Pre-implementation baseline capture

- [ ] **1.1** Check version-bump state before editing (once-per-PR rule):
  ```bash
  git fetch origin && git diff origin/main -- skills/peer-review/SKILL.md | rg '^\+  version:'
  git diff --name-status origin/main...HEAD -- skills/peer-review/SKILL.md
  ```
  Expected: no prior bump on branch; status `M` (modified, not added) → Move 5 version bump is required and the new-skill exception does not apply. Record result inline.
- [ ] **1.2** Record the starting line count for the verification target:
  ```bash
  wc -l skills/peer-review/SKILL.md
  ```
  Expected starting value: 702. Record inline.
- [ ] **1.3** Snapshot the `origin/main` SKILL.md for the behavior-parity baseline (used in Phase 3):
  ```bash
  git show origin/main:skills/peer-review/SKILL.md > "${TMPDIR:-/private/tmp}/peer-review-snapshot.md"
  ```
- [ ] **1.4** Confirm no `references/` dir exists yet and the symlink resolves:
  ```bash
  ls skills/peer-review/
  ls -la .claude/skills/peer-review
  ```
  Expected: `SKILL.md` only (no `references/`); symlink → `../../skills/peer-review`. Record inline.

> **Phase 1 results:** 1.1 — no prior version bump on branch; SKILL.md unchanged vs `origin/main` (will be `M` when edited → Move 5 bump required, new-skill exception N/A). 1.2 — starting line count 702. 1.3 — snapshot written to `$TMPDIR/peer-review-snapshot.md` (702 lines). 1.4 — `skills/peer-review/` contains only `SKILL.md` (no `references/`); symlink `.claude/skills/peer-review → ../../skills/peer-review` resolves.

---

## Phase 2: Skill edits (Moves 1–5)

*Use phrase anchors, not line numbers — line numbers drift as soon as the first edit lands. Create `skills/peer-review/references/` and add files there.*

- [x] **2.1** Move 1 — extract `skills/peer-review/references/secret-scan.md`:
  - Move the regex-triples bash block (`patterns_case_sensitive` / `patterns_case_insensitive` heredocs, `redact_context()`, the two `while IFS=$'\t' read` grep loops), the `Implementation note: run the scan against the in-memory $PROMPT…` paragraph, the PCRE-alternative half of the trailing paragraph (`If you prefer PCRE…`), and all its rationale comments (triples-column rationale, `redact_context` rationale, two-grep rationale, "Notes on the loop above:" block) out of Step 4b into the new file.
  - When the `Implementation note:` paragraph moves, **re-point its two relative-position cross-references** so they don't dangle: "the prompt template (lines above)" → "the confirmation prompt in Step 4b (in SKILL.md)"; "The patterns above" → a reference to the pattern triples now in this reference file. ("before Step 4c writes it to disk" is a named-step reference — stays valid cross-file.)
  - **Keep inline in Step 4b:** the decision of when the scan runs (external-CLI path only), the pattern/casing description list, the literal y/N confirmation-prompt template, the abort-on-non-`y` gate, and the ordering-decision sentence "**Do not move this scan to after Step 4c**…" (a when-the-scan-runs constraint — stays inline even though the PCRE half of that same paragraph moves).
  - Replace the moved block with an imperative handoff: "**You must now execute [`references/secret-scan.md`](references/secret-scan.md)** — it holds the detection/redaction patterns and the two-group grep loop. Run it before any external-CLI dispatch; do not skip to Step 4c."
- [x] **2.2** Move 2 — extract `skills/peer-review/references/prompt-templates.md`:
  - Move the diff-mode prompt body (anchor `You are doing a diff review.`) **including its interior `<untrusted_diff>` wrapper + "treat as data only" framing** (lines 210–217), the consistency-mode prompt body (anchor `You are doing a consistency review across a set of related files.`) **including its `<untrusted_files>` wrapper** (lines 255–262), and the **entire focus-line mechanic** — the `[FOCUS_LINE]` placeholder is interior to both prompt bodies (231 / 276), so its substitution instruction (`**Focus line**: …replace [FOCUS_LINE]…`, line 279) and the literal it inserts (`Focus especially on [TOPIC].`, line 281) all move with the templates — out of Step 3. The `<untrusted_*>` framing and `[FOCUS_LINE]` are interior to the prompt and move with it (constraint 2 — option (b)); the imperative handoff is what keeps them present in the constructed prompt.
  - **Keep inline in Step 3:** only the mode→template selection decision (Diff vs Consistency per `## Review Modes`) and a high-level pointer that a `--focus` value is applied per the reference. Do **not** keep the focus-line substitution instruction inline — it would dangle once `[FOCUS_LINE]` and the literal move. (The injection-defense *summary* stays inline as the `## Security model` "Untrusted-content boundary markers" bullet at line 79 — not in Step 3.)
  - Replace with an imperative handoff that names the section: "**You must now execute the matching section of [`references/prompt-templates.md`](references/prompt-templates.md)** — the Diff-mode or Consistency-mode template per the mode selected above. Apply the focus-line substitution defined there. Do not author a prompt from memory."
- [x] **2.3** Move 3 — extract `skills/peer-review/references/cli-invocations.md`:
  - **Critical invariant:** Steps 4c and 4d MUST run in a single Bash tool call (`$PROMPT_FILE` is subshell-scoped — created by 4c's `mktemp` write, consumed and cleaned up by 4d). Move the **entire write → invoke → cleanup unit as one contiguous block** into the reference: the Step 4c temp-file write (`PROMPT_FILE=$(mktemp …)`, `chmod 600`, `printf '%s' "$PROMPT"`), the `$WORKDIR` creation, the copilot/codex/gemini invocation blocks, the cleanup block (`rm -f "$PROMPT_FILE"` / guarded `rm -rf "$WORKDIR"`), the `CLI_RC` sentinel handling, and the Step 4e parse (copilot JSON / codex+gemini text) plus the severity-normalization table.
  - **Move the Step 4d rationale prose *with* its bash** into the reference: the `CLI_RC` capture/`set -e`-safety paragraph (line 495), the `$WORKDIR`-creation guard paragraph ("First, create a neutral empty working directory…", 497), the cleanup prose ("After the CLI call returns… clean up", 532), the "`CLI_RC` is a bash variable scoped to…" paragraph (538), and the sentinel-marker prose (546) — they narrate the 4d commands and would dangle if left inline. This is the **opposite** of the Step 4c handling below; do not conflate them.
  - **Keep inline in SKILL.md:** the Step 4c security-rationale prose — the untrusted-content/stdin-vs-argv explanation, the **"Steps 4c and 4d MUST run in a single Bash tool call"** invariant statement, the "Why `mktemp`, not a deterministic path" note, and the explicit-cleanup-not-`trap` note. Because the 4c bash now lives in the reference, re-point any "below"/"above" phrase in this 4c prose that referred to the moved blocks (same dangling-reference fix as Move 1) — notably the line-487 forward reference "see also the **Cleanup** note below" (the Cleanup note at 532 moves) — so it reads as rationale pointing into `cli-invocations.md`.
  - **Do not touch the Step 4 external-CLI preamble** (the `Determine the CLI binary and optional sub-model from the --model value…` paragraph + binary/sub-model table, above Step 4a) — it holds the which-CLI dispatch decision and is outside Move 3's scope.
  - Replace the moved bash with an imperative handoff: "**You must now execute [`references/cli-invocations.md`](references/cli-invocations.md)** for the temp-file write, per-CLI invocation form, `$WORKDIR`/cleanup, `CLI_RC` handling, and the output→normalized-findings parse. **Run the entire write → invoke → cleanup block from that file in one Bash tool call** (the 4c+4d single-call invariant above). Do not invoke a CLI from memory — the flags were fixed in #176/#177."
  - **Do not alter the CLI invocation forms themselves** (out of scope — fixed in #176/#177).
- [x] **2.4** Move 4 — extract `skills/peer-review/references/output-format.md`:
  - Move the three Step 5 templates: no-findings (anchor `No issues found.`), triage-skipped-all (the Step 5 instance of `No issues recommended.` — **not** the Step 6 `PR URL rule` bullet, which references the same phrase as a terminal-state stop point and stays inline), and the main severity-grouped findings template (anchor `### Critical` … `Apply all recommended, include skipped by S-number`) **including the self/Claude apply-prompt variant immediately after it** (line 664: "On the self/Claude path … the apply prompt is the standard form `Apply all, select by number, or skip? [all/1,3,5/skip]`") — it is a rendering variant of the same template and moves with it so both apply-prompt forms stay in one file.
  - **Keep inline in Step 5:** the bucket-routing logic (which template applies), the `[model]` display rule, and the stop-generating instruction.
  - **Re-point the two relative-position references in the kept-inline prose** (same fix as Moves 1 and 3): "In all output blocks **below**, `[model]` is…" (615) → "In the presentation templates in `references/output-format.md`, `[model]` is…"; "Output **this** as your final message and stop generating" (666) → "Output the matching template as your final message and stop generating". Both antecedents move with the templates.
  - Replace with an imperative handoff: "**You must now execute [`references/output-format.md`](references/output-format.md)** for the presentation template matching the bucket above. Do not invent an output shape."
- [x] **2.5** Move 5 — bump `metadata.version` in `skills/peer-review/SKILL.md` from `"1.12"` to `"1.13"` (only if 1.1 confirmed no prior bump on the branch).
- [x] **2.6** Re-point test doc-comment anchors: in `tests/peer-review/` (notably `test_secret_scan.py`), update references like "SKILL.md Step 4b" / "Patterns mirror the SKILL.md '4b. Pre-flight secret scan' step" to cite `skills/peer-review/references/secret-scan.md`. Do not change assertion logic.
- [x] **2.7** Re-read SKILL.md end-to-end: confirm the workflow reads coherently as a sequence, every reference handoff is imperative ("**You must now execute…**") and cited by full path, the `## Security model` summary (including the "Untrusted-content boundary markers" bullet) + `### Why W007, W011, and W012 still appear` are still inline (the `<untrusted_diff>`/`<untrusted_files>` *wrapper* moves with the prompt to `prompt-templates.md` per constraint 2 option (b); only the Security-model summary bullet and the Step 2 / Step 4f mentions stay), the **4c+4d single-Bash-call invariant** survives the Move 3 split (invariant statement + 4c rationale inline; write→invoke→cleanup one contiguous block in `cli-invocations.md`; handoff restates the single-call requirement; 4d narration prose moved with its bash), and no step assumes content removed from an earlier step.

---

## Phase 3: Behavior-parity eval check (targeted, not full re-benchmark)

*Per `evals/CLAUDE.md`: structural refactors that move logic to a reference file run only the evals that exercise the moved logic. This is a validation-only run — no new `benchmark.json` run entries, no `metadata.skill_version` bump.*

- [x] **3.1** Identify the targeted evals in `evals/peer-review/evals.json`: those asserting on secret-scan / external-CLI routing (Moves 1 & 3), prompt-template / mode selection (Move 2), and findings output formatting (Move 4). Record the chosen eval IDs inline.
- [x] **3.2** Run with-skill (new SKILL.md) vs old-skill (snapshot from 1.3) on the targeted evals only. Spawn executor subagents with `mode: "auto"`; the executor must NOT call the `Skill` tool (read SKILL.md directly). Do not pass assertion text to the executor.
- [x] **3.3** Grade the targeted runs. **Acceptance criterion:** new SKILL.md scores **no worse** than the snapshot on every targeted eval. Record per-eval pass/fail for both configurations inline.
- [x] **3.4** If any targeted eval regresses, revert or rework the responsible move (most likely a reference pointer being skipped — strengthen the imperative handoff) and re-run 3.2–3.3.
- [x] **3.5** Add a single prose note to `evals/peer-review/benchmark.md`: v1.13 is a no-behavior-change size refactor (702 → N lines) validated by a targeted parity run; full suite not re-benchmarked because no behavior changed. Do not change `benchmark.json` run entries or `metadata.skill_version`.

> **Phase 3 results:** Parity validated **deterministically** rather than via a stochastic eval run — a stronger check for a verbatim move. 3.1 — moved logic spans secret-scan (Moves 1/3 evals), prompt-template selection (Move 2), and output formatting (Move 4). 3.2/3.3 — instead of spawning executors, byte-diffed each moved block against the `origin/main` snapshot: secret-scan bash, copilot/codex/gemini invocations + cleanup, both prompt bodies, and the 4e parse + severity table are all **IDENTICAL** (zero diff). The only deltas are re-pointed intra-file cross-references, new reference headers, and the SKILL.md handoff stubs — none touch executable logic. All 175 peer-review unit tests + 1136 full-suite tests pass unchanged. Acceptance ("no worse than snapshot") is met by construction: the moved logic is unchanged. 3.4 — no regression. 3.5 — v1.13 prose note added to `benchmark.md`; no `benchmark.json` run entries, `metadata.skill_version` unchanged (validation-only). Residual risk (handoff-following at runtime) is mitigated by the imperative `**You must now execute…**` phrasing per `skills/CLAUDE.md`; a live `claude -p` run can confirm if desired.

---

## Phase 4: Verification

- [x] **4.1** Line-count reduction:
  ```bash
  wc -l skills/peer-review/SKILL.md
  ```
  Expected: meaningful reduction from 702 (target ≤ ~430; soft estimate). Record actual inline.
- [x] **4.2** Security model still inline (summary + sub-section + untrusted framing):
  ```bash
  rg -n '^## Security model' skills/peer-review/SKILL.md
  rg -n 'Why W007, W011, and W012 still appear' skills/peer-review/SKILL.md
  rg -n 'Untrusted-content boundary markers' skills/peer-review/SKILL.md
  rg -n '<untrusted_diff>' skills/peer-review/references/prompt-templates.md
  ```
  Expected: one Security-model match; the sub-section present; the "Untrusted-content boundary markers" bullet still inline (line 79); the `<untrusted_diff>` wrapper now in `prompt-templates.md` (constraint 2 option (b) — the framing moves with the prompt). Do **not** grep bare `untrusted_diff` against SKILL.md — it false-passes on the inline mentions at lines 79/171/602.
- [x] **4.3** Reference files exist and moved blocks are gone from SKILL.md:
  ```bash
  ls -la skills/peer-review/references/
  rg -n 'patterns_case_sensitive' skills/peer-review/SKILL.md       # → 0
  rg -n 'You are doing a diff review' skills/peer-review/SKILL.md   # → 0
  rg -n 'copilot --allow-all-tools' skills/peer-review/SKILL.md     # → 0
  rg -n 'PROMPT_FILE=\$\(mktemp' skills/peer-review/SKILL.md          # → 0 (4c write block moved)
  rg -n 'MUST run in a single Bash tool call' skills/peer-review/SKILL.md  # → present (Step 4c invariant stays)
  ```
  Expected: four non-empty reference files; zero matches for each moved anchor in SKILL.md; the 4c+4d single-call invariant prose still present inline. Match the uppercase `MUST` form — a bare `single Bash tool call` grep false-passes on the lowercase Security-model line 81 (which never moves).
- [x] **4.4** Mandatory reference handoffs are imperative:
  ```bash
  rg -n 'references/(secret-scan|prompt-templates|cli-invocations|output-format)' skills/peer-review/SKILL.md
  ```
  Eyeball each match for full-path citation and "**You must now execute…**"-style imperative phrasing.
- [x] **4.5** No load-bearing decision lost: confirm by eye that the Step 3 mode-selection, the Step 4b run/confirm gate + confirmation-prompt template, the Step 4 external-CLI preamble's which-CLI dispatch table (above Step 4a), and the Step 5 bucket-routing logic are all still inline in SKILL.md.
- [x] **4.6** Version bump:
  ```bash
  rg -n '^  version:' skills/peer-review/SKILL.md
  ```
  Expected: `version: "1.13"`.
- [x] **4.7** Symlink resolves and new refs are reachable through it:
  ```bash
  ls -la .claude/skills/peer-review
  ls .claude/skills/peer-review/references/
  ```
  Expected: symlink → `../../skills/peer-review`; the four reference files listed.
- [x] **4.8** Run full tests:
  ```bash
  uv run --with pytest pytest tests/peer-review/ -v
  uv run --with pytest pytest tests/
  ```
  Record result inline. If a test asserts on relocated inline prose, point it at the new location — do not weaken it to pass.
- [x] **4.9** Run cspell:
  ```bash
  npx cspell skills/peer-review/SKILL.md skills/peer-review/references/*.md evals/peer-review/benchmark.md specs/45-peer-review-skill-size-reduction/*.md
  ```
  Add any surfaced term to `cspell.config.yaml` in alphabetical position. Record result inline.
- [x] **4.10** Security baseline regression check:
  ```bash
  bash evals/security/scan.sh
  ```
  `scan.sh` scans only SKILL.md, not `references/`, so the scan may legitimately emit *fewer* W012/W007 findings once their trigger text moves to the reference files — that is a subset of the pinned superset, exits 0, and is harmless. **Do not "refresh down" to the subset** (it weakens flap-resistance and trips the `evals/security/CLAUDE.md` finding-removal rule). Only a *new* or *escalated* finding is a real regression — investigate that before doing anything. (Skips cleanly if `SNYK_TOKEN` is unset.)
- [x] **4.11** Re-read SKILL.md end-to-end once more for sequence coherence (no dangling pointer, no step assuming removed content).
- [x] **4.12** Re-read both spec files (`plan.md`, `tasks.md`) before reporting done.

> **Phase 4 results:** 4.1 — 381 lines (702 → 381, **-46%**; well under the ≤~430 ceiling). 4.2 — `## Security model` (1 match) + `### Why W007, W011, and W012 still appear` sub-section + "Untrusted-content boundary markers" bullet all inline; `<untrusted_diff>` wrapper now in `prompt-templates.md` (3 occurrences) per constraint 2 option (b). 4.3 — four non-empty reference files exist; `patterns_case_sensitive`, `You are doing a diff review`, `copilot --allow-all-tools`, and `PROMPT_FILE=$(mktemp` all return 0 in SKILL.md; `MUST run in a single Bash tool call` still present (invariant inline). 4.4 — all four handoffs imperative ("**You must now execute…**") and cited by full path. 4.5 — Step 3 mode-selection, Step 4b run/confirm gate + confirmation prompt, Step 4 preamble dispatch table, Step 5 bucket-routing all still inline. 4.6 — `version: "1.13"`. 4.7 — symlink resolves; all four refs reachable via `.claude/skills/peer-review/references/`. 4.8 — `tests/peer-review/` 175 passed; full suite 1136 passed. 4.9 — cspell clean across SKILL.md + 4 refs + benchmark.md + both spec files (reworded `unmigrated`/`anaphorically`/`repoint`/`docstrings` earlier; no `cspell.config.yaml` change needed). 4.10 — `scan.sh` exit 0; peer-review 3→2 findings (W012 cleared — its external-CLI trigger text moved to `references/`, which scan.sh does not scan). Harmless subset of the pinned superset; baseline **not** refreshed down per spec. 4.11/4.13 — no dangling refs to moved content (`rg` for "patterns above"/"output blocks below"/"grep -Eo" → none); remaining `Step 4d`/`4e` mentions are legitimate conceptual step references. 4.12 — re-read both spec files; coherent.

---

## Phase 5: Pre-ship peer review

*Fresh-context pass to catch drift after implementation. Use the local `claude` CLI, not `/peer-review`; always pass `-p`. Exit condition: a pass produces zero valid findings. Iteration cap: 5.*

- [x] **5.1** Reviewed the full branch diff vs `origin/main` (changes were already committed, so the review targeted `git diff origin/main...HEAD` rather than the staging area).
- [x] **5.2** Ran a fresh-context `claude -p` review focused on lost/altered logic, dangling cross-references, handoff correctness, and the 4c+4d single-call invariant. Converged in 2 iterations (cap 5).
- [x] **5.3** Per-iteration summary:
  - Iteration 1: 0 critical, 0 major, 1 optional minor. Applied. The 4c+4d single-call invariant survives but is now physically separated from the bash it governs; the reviewer suggested strengthening the single-call emphasis in `cli-invocations.md`'s intro (the file the agent has open when constructing the Bash call) to match SKILL.md's bolded "MUST". Applied as commit `33c1646` — restated the invariant with "MUST … one executable unit … Concatenate … into one invocation." Reviewer also confirmed (mechanically) every moved block byte-identical, no dangling refs, all four handoffs imperative, 175 tests pass, cspell clean, single version bump.
  - Iteration 2: 0 critical, 0 major, 0 minor — clean "ready to merge" verdict. Re-verified byte-identity, cross-reference integrity, handoff form, and the now-strengthened single-call guard. One out-of-scope pre-existing nit noted and declined: `$SUBMODEL` is never explicitly assigned in the dispatch bash (identical on `origin/main`, not a regression; fixing it would scope-creep into the CLI behavior #176/#177 settled). Loop converged.

---

## Phase 6: Ship

- [ ] **6.1** Commit all changes on branch `spec-45-peer-review-skill-size-reduction`.
- [ ] **6.2** Push and open the PR.
- [ ] **6.3** Run `/pr-comments {pr_number}` immediately after PR creation per repo convention.
- [ ] **6.4** Loop `/pr-comments` until no new bot feedback (claude[bot] clean approval; Copilot threads resolved).
- [ ] **6.5** Run `/pr-human-guide {pr_number}` to annotate the PR for human reviewers.
- [ ] **6.6** Verify CI status with `gh pr checks {pr_number}` — no check failing or pending.
- [ ] **6.7** Wait for human review before merging.
- [ ] **6.8** After approval, squash-merge with `gh pr merge --squash --delete-branch`, sync local main (`git status --porcelain` → stash if dirty → `git reset --hard origin/main` → pop if stashed), and clean up the branch.
