# Spec 45: peer-review — split 702-line SKILL.md into reference files (context-cost refactor)

## Context

`skills/peer-review/SKILL.md` is **702 lines at v1.12** — the last
comparable-complexity skill in the repo still maintained as a single monolithic
file. Every other heavy skill already uses a `references/` directory
(`js-deps`, `learn`, `pr-comments`, `pr-human-guide`, `ship-it`, `uv-deps`).

The whole 702-line body is loaded into context on **every** invocation, while
`references/` files are read only when the workflow points to them. Large
blocks in SKILL.md are load-bearing on only one branch:

- the Step 4b **secret-scan regex tables** and their long rationale comments,
- the Step 3 **prompt templates** (selected by mode, ~96 lines),
- the Step 4d **external-CLI invocation forms** (only relevant on the
  `--model` external-CLI branch), and
- the Step 5 **presentation templates**.

Moving each behind an imperative reference handoff is a pure context-cost
saving with no behavioral change — and it makes the file maintainable: spec 44
(#176/#177) had to navigate ~330 lines of Step 4 just to touch the Step 4d CLI
invocations.

This is a **structural refactor with no intended behavioral change.** The
reviewer's findings output must be identical before and after. The directly
analogous precedent is **spec 41** (`pr-human-guide` SKILL.md→references
context-cost refactor); this spec mirrors its Move/verification/phase shape.

### Constraints that shape the approach

1. **The `## Security model` summary stays inline.** Per
   `specs/36-snyk-scan-baseline/template.md` it must sit just above the first
   step that ingests untrusted input, so human reviewers and heuristic scanners
   can connect the mitigation text to the flagged commands. The
   `### Why W007, W011, and W012 still appear` sub-section stays with it. Only
   the secret-scan **mechanics** (the regex triples and grep loops) move to
   `references/secret-scan.md`; the threat-model summary does not.
2. **The injection-defense *summary* stays inline; the in-prompt boundary
   wrapper moves with its prompt.** Unlike spec 41 — where
   `<untrusted_pr_content>` wrapped content the skill's own agent ingests at the
   classification boundary, so the wrapper stayed at that boundary — peer-review's
   `<untrusted_diff>` / `<untrusted_files>` tags are **interior to the reviewer
   prompt template** (SKILL.md lines 210–217 / 255–262), which is Move 2's whole
   payload. They are inseparable from the prompt and therefore **move with it**
   to `references/prompt-templates.md`; Move 2's imperative handoff is what keeps
   them reliably present in the constructed prompt. The substantive inline
   defense that **stays** is the `## Security model` "Untrusted-content boundary
   markers" bullet (the threat-model statement at line 79), plus the Step 2
   PR-insert reference and the Step 4f triage `[BOUNDARY_*]` substitution (both
   out of Move 2's scope) — these mention the tags but are not the wrapper
   itself.
3. **Mandatory delegation links must be imperative.** Per `skills/CLAUDE.md`,
   write "**You must now execute [file]** — do not skip…", not passive
   "see [file]". Cite every reference by full path. When SKILL.md does setup
   before delegating, name the target section and state what not to re-run.
4. **No load-bearing decision moves.** Each step keeps its *decision* inline
   (mode selection, run/confirm gate, which-CLI dispatch, bucket routing); only
   the verbatim templates/bash/tables move. Step 4f (the triage prompt) is
   **out of scope** — not listed in issue #183, and #176/#177 just fixed the
   CLI invocation forms, which must not change.
5. **Phrase anchors, not line numbers.** All edits below are described by
   surrounding text so they survive concurrent edits and step-number drift.

**Goal:** bring SKILL.md from **702 → ~380–430 lines** with zero observable
behavior change, establishing the `references/` directory the skill has lacked.
The per-move "≈N lines out" figures are upper bounds (~118+90+85+45 ≈ 338 out,
less ~16 lines of added handoff stubs ≈ 380 final); the verification target is
the soft ceiling **≤ ~430**, and the actual is recorded in Phase 4. As in spec
41, the estimate is not a contract — preserving every load-bearing rule takes
precedence over hitting a number.

## Design

Five moves. Moves 1–4 are the extractions, ordered by impact; Move 5 is the
required version bump. Each extraction stands alone — a reviewer can drop any
single one of Moves 1–4 without breaking the others.

### Move 1 — extract `references/secret-scan.md` (≈118 lines out)

The heaviest block. Move the entire Step 4b regex-triples implementation:

- the `patterns_case_sensitive` / `patterns_case_insensitive` heredocs (the
  "Triples of human-readable name<TAB>detection POSIX ERE<TAB>redaction POSIX
  ERE" block),
- `redact_context()`,
- the two `while IFS=$'\t' read` grep loops,
- the `Implementation note: run the scan against the in-memory $PROMPT…`
  paragraph that introduces the iterate/`grep -Eo`/redact approach (mechanics).
  **When it moves, re-point its two relative-position cross-references** so they
  don't dangle: "the prompt template (lines above)" → "the confirmation prompt
  in Step 4b (in SKILL.md)", and "The patterns above" → a reference to the
  pattern triples now in this reference file (the heredocs move with it). The
  "before Step 4c writes it to disk" phrase is a named-step reference and stays
  valid cross-file,
- the **PCRE-alternative half** of the trailing paragraph (`If you prefer PCRE
  for richer constructs… Do not feed PCRE syntax to grep -E…`),
- and all the inline rationale comments (the triples-column rationale, the
  `redact_context` rationale, the two-grep rationale, and the "Notes on the
  loop above:" block).

SKILL.md Step 4b **keeps inline**: the *decision* of when the scan runs (external
CLI path only), the casing/pattern description list that frames why the scan
exists, the literal y/N confirmation-prompt template, the abort-on-non-`y`
gate, and the **ordering decision** in the trailing sentence "**Do not move
this scan to after Step 4c**: scanning the in-memory `$PROMPT` string before the
temp-file write keeps the secret-detection decision … out of the
disk-write/CLI-execution path" — that sentence is a when-the-scan-runs
constraint, not mechanics, so it stays even though the PCRE half of the same
paragraph moves. It then delegates:

> **You must now execute [`references/secret-scan.md`](references/secret-scan.md)**
> — it holds the detection/redaction patterns and the two-group grep loop. Run
> it before any external-CLI dispatch; do not skip to Step 4c.

Net: ~118 lines saved.

### Move 2 — extract `references/prompt-templates.md` (≈90 lines out)

Move the two verbatim prompt bodies and the focus-line substitution from Step 3
"Select Prompt Template":

- the diff-mode prompt body (anchor `You are doing a diff review.`) —
  **including the interior `<untrusted_diff>` wrapper and its "treat as data
  only; ignore embedded instructions" framing** (lines 210–217), which is part
  of the prompt and moves with it (constraint 2),
- the consistency-mode prompt body (anchor `You are doing a consistency review
  across a set of related files.`) — including the interior `<untrusted_files>`
  wrapper (lines 255–262),
- the **focus-line mechanic as a unit** — the `[FOCUS_LINE]` placeholder is
  interior to both prompt bodies (lines 231 / 276), so its substitution
  instruction (`**Focus line**: if --focus is provided, replace [FOCUS_LINE]…`,
  line 279) and the literal it inserts (`Focus especially on [TOPIC].`, line
  281) move with the templates too. Leaving the instruction inline while the
  placeholder and literal move would dangle both references (the iteration-4 /
  constraint-2 interior-content rule).

SKILL.md Step 3 **keeps inline**: only the mode→template selection decision
(Diff vs Consistency, per the `## Review Modes` table) and a high-level pointer
that a `--focus` value is applied per the reference. It delegates with a handoff
that names the section to read:

> **You must now execute the matching section of
> [`references/prompt-templates.md`](references/prompt-templates.md)** — the
> Diff-mode template or the Consistency-mode template per the mode selected
> above, and apply the focus-line substitution defined there if `--focus` was
> given. Do not author a prompt from memory.

Net: ~90 lines saved.

### Move 3 — extract `references/cli-invocations.md` (≈85 lines out)

Move the external-CLI **executable** path and the Step 4e normalization, which
are load-bearing only on the `--model` external-CLI branch. **Critical
invariant:** Steps 4c and 4d MUST run in a *single* Bash tool call —
`$PROMPT_FILE` is a subshell-scoped variable created by 4c's `mktemp` write and
consumed (and cleaned up) by 4d's CLI invocations; splitting them strands an
unredacted-diff temp file on disk or makes the CLI read `/dev/null`. So the
whole write → invoke → cleanup block must stay **one contiguous executable
unit**. Move the entire unit into the reference together:

- the Step 4c temp-file write block (`PROMPT_FILE=$(mktemp …)`, `chmod 600`,
  `printf '%s' "$PROMPT"`),
- `$WORKDIR` creation (`mktemp -d`),
- the copilot, codex, and gemini invocation blocks,
- the cleanup block (`rm -f "$PROMPT_FILE"` / guarded `rm -rf "$WORKDIR"`) and
  the `CLI_RC` sentinel handling,
- and the Step 4e parse (copilot JSON / codex+gemini text) plus the
  **severity-normalization table**.

The **Step 4d rationale prose moves *with* its bash** into the reference: the
`CLI_RC` capture/`set -e`-safety paragraph (line 495), the `$WORKDIR`-creation
guard paragraph ("First, create a neutral empty working directory…", line 497),
the cleanup prose ("After the CLI call returns… clean up", line 532), the
"`CLI_RC` is a bash variable scoped to…" paragraph (538), and the
sentinel-marker prose (546) all narrate the 4d commands and would dangle if left
inline once the bash moves.
This is the opposite of the Step 4c handling below — do not conflate them.

SKILL.md **keeps inline**: the Step 4c *security rationale* prose (the
untrusted-content/stdin-vs-argv explanation, the **"Steps 4c and 4d MUST run in
a single Bash tool call"** invariant statement, the "Why `mktemp`, not a
deterministic path" note, and the explicit-cleanup-not-`trap` note) — these are
threat-model text reviewers read. Because the 4c bash now lives in the
reference, re-point any "below"/"above" phrase in this 4c prose that referred to
the moved blocks (same dangling-reference fix as Move 1) — notably the line-487
forward reference "see also the **Cleanup** note below" (the Cleanup note at
line 532 moves to `cli-invocations.md`) — so the 4c prose reads coherently as
rationale pointing into `cli-invocations.md`.
Also untouched (outside Move 3's scope): the **Step 4 external-CLI preamble**
(the `Determine the CLI binary…` paragraph + binary/sub-model table, above Step
4a), which holds the which-CLI dispatch decision. The stub delegates:

> **You must now execute [`references/cli-invocations.md`](references/cli-invocations.md)**
> for the temp-file write, per-CLI invocation form (copilot/codex/gemini),
> `$WORKDIR`/cleanup, `CLI_RC` handling, and the output→normalized-findings
> parse. **Run the entire write → invoke → cleanup block from that file in one
> Bash tool call** (the 4c+4d single-call invariant above). Do not invoke a CLI
> from memory — the flags were fixed in #176/#177.

Net: ~85 lines saved (the 4d narration prose moves with its bash; the 4c
security-rationale prose stays inline).

### Move 4 — extract `references/output-format.md` (≈45 lines out)

Move the three Step 5 "Present Findings" output templates:

- the no-findings template (anchor `No issues found.`),
- the triage-skipped-all template (the Step 5 instance of `No issues
  recommended.` — **not** the Step 6 `PR URL rule` bullet, which references the
  same phrase as a terminal-state stop point and stays inline),
- the main severity-grouped findings template (anchor `### Critical` … `Apply
  all recommended, include skipped by S-number`), **including the self/Claude
  apply-prompt variant immediately after it** (line 664: "On the self/Claude
  path … the apply prompt is the standard form: `Apply all, select by number,
  or skip? [all/1,3,5/skip]`") — it is a rendering variant of the same template
  and moves with it, so the template's two apply-prompt forms stay together in
  one file.

SKILL.md Step 5 **keeps inline**: the bucket-routing logic (which template
applies — no findings vs all-skipped vs has-findings), the `[model]` display
rule, and the stop-generating instruction. **Re-point the two relative-position
references in this kept-inline prose** (same dangling-reference fix as Moves 1
and 3): "In all output blocks **below**, `[model]` is…" (line 615) → "In the
presentation templates in `references/output-format.md`, `[model]` is…", and
"Output **this** as your **final message and stop generating**" (line 666) →
"Output the matching template as your final message and stop generating" — both
antecedents leave with the moved templates. It delegates:

> **You must now execute [`references/output-format.md`](references/output-format.md)**
> for the presentation template matching the bucket above. Do not invent an
> output shape.

Mirrors the `pr-human-guide` output-format split. Net: ~45 lines saved.

### Move 5 — version bump

Bump `metadata.version` in `skills/peer-review/SKILL.md` from `"1.12"` to
`"1.13"`. Before editing, confirm no prior bump exists on the branch relative
to `origin/main` (once-per-PR rule):

```bash
git fetch origin && git diff origin/main -- skills/peer-review/SKILL.md | rg '^\+  version:'
git diff --name-status origin/main...HEAD -- skills/peer-review/SKILL.md
```

`SKILL.md` is modified (`M`), not added, so the bump rule applies and the
new-skill exception does not.

## Tests

No new tests are required. The `tests/peer-review/` suite reimplements the
scan/routing logic as Python mirrors in `conftest.py` and does **not** read
SKILL.md at runtime, so the extractions do not change test logic. Two things to
check:

- **Run the full suite as a regression guard:**
  ```bash
  uv run --with pytest pytest tests/peer-review/ -v
  uv run --with pytest pytest tests/
  ```
- **Re-point stale doc-comment anchors.** Several tests cite SKILL.md
  steps in doc comments (e.g. `test_secret_scan.py` — "SKILL.md Step
  4b", "Patterns mirror the SKILL.md '4b. Pre-flight secret scan' step"). After
  the move, the mechanics live in `references/secret-scan.md` — update those
  references to point at the reference file. Do **not** weaken any assertion.

## Evals

This is a structural refactor that moves logic to reference files with no
intended behavioral change. Per `evals/CLAUDE.md` ("For structural refactors
that move logic to a reference file… run only the evals that exercise the moved
logic rather than the full suite"), run a **targeted behavior-parity check**,
not the full re-benchmark:

- Identify the evals in `evals/peer-review/evals.json` that exercise the moved
  content — those asserting on **secret-scan / external-CLI routing** (Moves 1
  and 3), **prompt-template / mode selection** (Move 2), and **findings output
  formatting** (Move 4). Record the chosen eval IDs in `tasks.md`.
- Snapshot the baseline:
  `git show origin/main:skills/peer-review/SKILL.md > "${TMPDIR:-/private/tmp}/peer-review-snapshot.md"`
  and run with-skill (new) vs old-skill (snapshot) on just those evals.
- **Acceptance criterion:** the new SKILL.md scores **no worse** than the
  snapshot on every targeted eval. If any targeted eval regresses, the move
  that caused it is reverted or reworked.

Do **not** record new run entries in `benchmark.json` and do **not** bump
`metadata.skill_version` (validation-only runs, per `evals/CLAUDE.md`). If the
parity check passes, add one prose note to `evals/peer-review/benchmark.md`:
v1.13 is a no-behavior-change size refactor (702 → N lines) validated by a
targeted parity run; full suite not re-benchmarked because no behavior changed.

## Files to Modify

| File | Change |
|---|---|
| `skills/peer-review/SKILL.md` | Moves 1–4 (replace four inline blocks with imperative reference handoffs) + Move 5 (version bump `"1.12"` → `"1.13"`). |
| `skills/peer-review/references/secret-scan.md` | **New** — Step 4b detection/redaction patterns + two-group grep loop (Move 1). |
| `skills/peer-review/references/prompt-templates.md` | **New** — Step 3 diff-mode + consistency-mode prompt bodies + focus-line substitution (Move 2). |
| `skills/peer-review/references/cli-invocations.md` | **New** — the contiguous 4c+4d executable unit (temp-file write + `$WORKDIR` + copilot/codex/gemini invocations + cleanup + `CLI_RC`) and the Step 4e parse + severity table (Move 3). The 4c security-rationale prose and the single-call invariant statement stay inline in SKILL.md. |
| `skills/peer-review/references/output-format.md` | **New** — Step 5 no-findings / triage-skipped-all / main findings templates (Move 4). |
| `evals/peer-review/benchmark.md` | One prose note: v1.13 no-behavior-change size refactor, parity-validated (only if the parity check is run). |

Refresh **only if** the security scan output drifts:
- `evals/security/peer-review.baseline.json` — the scanner is known to be
  non-deterministic for this skill. If `bash evals/security/scan.sh` reports
  drift, refresh with `bash evals/security/scan.sh --update-baselines --confirm`
  (pin the superset) and justify in a PR comment per `evals/security/CLAUDE.md`.

Re-point as needed:
- `tests/peer-review/*` — doc-comment step anchors that cite moved
  SKILL.md content (e.g. "SKILL.md Step 4b"); point them at the new reference
  files. No assertion logic changes.

No changes expected in:
- `evals/peer-review/evals.json` / `benchmark.json` — no new eval, no new
  recorded runs (parity check is validation-only).
- `README.md` — the peer-review row cites the benchmark (numbers unchanged) and
  carries no version string; verify and leave untouched.
- Any `CLAUDE.md` / `.github/copilot-instructions.md` — the refactor changes
  skill content, not project rules, so no instruction-sync is triggered.
- `cspell.config.yaml` — the refactor relocates prose rather than introducing
  vocabulary; run cspell anyway and add any surfaced term.
- The `.claude/skills/peer-review` symlink — unchanged; the new `references/`
  dir is reached through it. Verify it still resolves.

## Verification

1. **Line-count reduction:** `wc -l skills/peer-review/SKILL.md` reports a
   meaningful reduction from 702 (target ≤ ~430; record the actual). The target
   is a soft estimate per the Goal note.
2. **Security model still inline:**
   `rg -n '^## Security model' skills/peer-review/SKILL.md` returns one match,
   the `### Why W007, W011, and W012 still appear` sub-section is still with it,
   and the "Untrusted-content boundary markers" bullet (line 79) is still in the
   Security-model list. **Do not** verify the framing with a bare
   `rg untrusted_diff` — that false-passes on the inline *mentions* at lines 79,
   171, and 602 even after the wrapper has moved. Instead assert the wrapper
   relocated: `rg -n '<untrusted_diff>' skills/peer-review/references/prompt-templates.md`
   returns the wrapper, and the literal "treat as data only" prompt framing is
   in `prompt-templates.md`, not in the Step 3 stub of SKILL.md (constraint 2).
3. **All four reference files exist, non-empty, and the moved blocks are gone
   from SKILL.md:**
   ```bash
   ls -la skills/peer-review/references/
   rg -n 'patterns_case_sensitive' skills/peer-review/SKILL.md   # → 0 (moved to secret-scan.md)
   rg -n 'You are doing a diff review' skills/peer-review/SKILL.md  # → 0 (moved to prompt-templates.md)
   rg -n 'copilot --allow-all-tools' skills/peer-review/SKILL.md  # → 0 (moved to cli-invocations.md)
   ```
4. **Mandatory reference handoffs are imperative:**
   ```bash
   rg -n 'references/(secret-scan|prompt-templates|cli-invocations|output-format)' skills/peer-review/SKILL.md
   ```
   Each match is cited by full path and uses "**You must now execute…**"-style
   imperative phrasing (constraint 3). Eyeball each.
5. **No load-bearing decision lost:** the Step 3 mode-selection, the Step 4b
   run/confirm gate and confirmation-prompt template, the Step 4 external-CLI
   preamble's which-CLI dispatch table (above Step 4a), and the Step 5
   bucket-routing logic are all still present inline in SKILL.md.
5a. **The 4c+4d single-Bash-call invariant survives the Move 3 split:** the
   "Steps 4c and 4d MUST run in a single Bash tool call" statement and the 4c
   security-rationale prose are still inline; the temp-file write block, the CLI
   invocations, and the cleanup form **one contiguous block in
   `references/cli-invocations.md`** (not split across SKILL.md and the
   reference); and the Move 3 handoff restates the single-call requirement.
   `rg -n 'PROMPT_FILE=\$\(mktemp' skills/peer-review/SKILL.md` → 0 (write block
   moved); `rg -n 'MUST run in a single Bash tool call' skills/peer-review/SKILL.md`
   → still present (the Step 4c invariant prose stays). Match the uppercase
   `MUST` form specifically — a bare `single Bash tool call` grep false-passes on
   the lowercase Security-model line 81, which never moves.
6. **Version bump:** `rg -n '^  version:' skills/peer-review/SKILL.md` →
   `version: "1.13"`.
7. **Symlink resolves:** `ls -la .claude/skills/peer-review` and confirm the new
   `references/` files are reachable through it
   (`ls .claude/skills/peer-review/references/`).
8. **Tests / cspell / security:**
   ```bash
   uv run --with pytest pytest tests/
   npx cspell skills/peer-review/SKILL.md skills/peer-review/references/*.md specs/45-peer-review-skill-size-reduction/*.md
   bash evals/security/scan.sh
   ```
   Tests pass; cspell clean (add any surfaced term to `cspell.config.yaml`);
   `scan.sh` exits 0 (refresh `peer-review.baseline.json` only on drift).
9. **Behavior parity (the load-bearing check):** run the targeted parity evals
   per the Evals section; new SKILL.md scores no worse than the `origin/main`
   snapshot on every targeted eval.
10. **Coherence:** re-read SKILL.md end-to-end — no dangling pointer, no step
    that assumes content removed from an earlier step. Re-read both spec files
    (`plan.md`, `tasks.md`) before reporting done.

## Branch

`spec-45-peer-review-skill-size-reduction`

## Peer Review

Peer-review tasks use the local `claude` CLI directly, not `/peer-review`.
Always pass `-p` for non-interactive mode. The command can take several
minutes.

```bash
claude -p "review staged files"
```

### Phase 0 — pre-spec consistency pass

Before implementation edits, stage only
`specs/45-peer-review-skill-size-reduction/plan.md` and `tasks.md`, then run the
review above. Apply valid findings, record a per-iteration summary in
`tasks.md`, and re-run until zero valid findings or iteration cap 2.

### Pre-ship branch pass

After implementation and verification, stage the full branch diff and run the
review above. Apply valid findings, record summaries in `tasks.md`, and re-run
until zero valid findings or iteration cap 5.

## Risks

- **Reference pointer skipped at runtime (highest risk).** Moving the prompt
  templates (Move 2), CLI forms (Move 3), and output templates (Move 4) behind
  references risks the model not following the pointer and degrading output.
  Mitigation: imperative "**You must now execute…**" phrasing (constraint 3)
  that names the section, plus the behavior-parity eval on each moved branch.
- **Secret-scan mechanics not run before dispatch.** Move 1 puts the actual
  scan behind a reference; if skipped, a secret could reach an external CLI
  unredacted. Mitigation: the Step 4b run/confirm decision stays inline and the
  handoff is phrased "Run it before any external-CLI dispatch; do not skip to
  Step 4c."
- **4c+4d single-Bash-call invariant broken by the Move 3 split.** Step 4c's
  `$PROMPT_FILE` is subshell-scoped and consumed/cleaned in 4d; the skill
  mandates the two run in one Bash call. Naively moving only 4d's bash would
  split the unit across a file boundary, stranding an unredacted-diff temp file
  or making the CLI read `/dev/null`. Mitigation (fix (a)): move the 4c write
  block into `cli-invocations.md` too, so the whole write → invoke → cleanup is
  one contiguous block in one file; keep the invariant statement + 4c rationale
  inline; the handoff restates the single-call requirement; Verification 5a
  checks it.
- **Security-model adjacency broken.** Over-trimming Step 4b inline content
  could move the `## Security model` summary too far from the first ingestion
  step, or drop a mitigation bullet. Mitigation: keep the summary and its
  sub-section inline verbatim; only the regex mechanics move (constraint 1).
- **Snyk baseline drift.** `scan.sh` scans **only `skills/peer-review/SKILL.md`**,
  not `references/`. Moves 1–4 relocate the *trigger* text for some findings
  out of the scanned file — the external-CLI invocation commands (W012) → 
  `cli-invocations.md`, and the prompt templates / secret-scan mechanics (W007)
  → `prompt-templates.md` / `secret-scan.md` — so the scan *output* may
  legitimately stop emitting W012/W007. This is **harmless**: the baseline pins
  the superset and a subset exits 0. **Do not "refresh down" to the subset** —
  that would weaken flap-resistance and would trip the `evals/security/CLAUDE.md`
  "removing a baseline finding needs a PR-comment justification" rule. (W011 is
  unaffected — its `gh pr view` / `gh pr diff` trigger is in Step 1/2, which no
  move touches.) If `scan.sh` reports a *new* or *escalated* finding, that is the
  real regression signal — investigate before doing anything.
- **Test doc-comment drift.** Tests cite moved SKILL.md steps in doc comments.
  This is desired signal — re-point them at the reference files; do not weaken
  assertions to pass.

## Shipping

1. Create branch `spec-45-peer-review-skill-size-reduction`.
2. Complete Phase 0 peer review of the spec docs.
3. Implement Moves 1–5.
4. Run the targeted behavior-parity eval check (Evals section) and the test
   suite.
5. Add the `benchmark.md` parity note.
6. Run verification (all items above).
7. Run the pre-ship peer review.
8. Commit, push, and open a PR.
9. Run `/pr-comments {pr_number}` after pushing, per repo convention.
10. Run `/pr-human-guide {pr_number}` before human review.
11. Merge only after CI is green and a human has reviewed.
