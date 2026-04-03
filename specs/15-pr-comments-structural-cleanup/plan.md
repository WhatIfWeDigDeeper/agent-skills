# Spec 15: pr-comments — Structural Cleanup & Simplification (v1.20 → v1.21)

## Problem

The pr-comments skill (v1.20, 478 lines) has reached 100% eval pass rate (+67pp delta), but rapid iteration has left structural debt and verbosity that will slow future changes:

1. **Step 13 mixes five concerns in ~80 lines** — building the reviewer list, pushing, auto/manual branching, human re-requests, bot re-requests, and entering the polling loop. Any bot-related fix requires reading through push/human logic to find the relevant section.

2. **Stale-HEAD bot detection is duplicated** — the same `group_by` / `sort_by` / `last` / `commit_id` jq pipeline appears in SKILL.md Step 13 (~12 lines) and bot-polling.md Step 6c (~22 lines). Prior churn (v1.17) required updating both sites.

3. **`--auto N` syntax is ambiguous** — CLAUDE.md warns that `/pr-comments --auto 42` could mean "cap at 42 iterations" or "PR #42". A dedicated `--max N` flag eliminates the ambiguity.

4. **bot-polling.md repeats setup prose** — both entry points record a snapshot_timestamp and take a fresh GraphQL thread snapshot. A shared section eliminates this duplication.

5. **Steps 8 and 9 are one action split across two headings** — Step 8 ends with "Handle accepted suggestions together with regular manual changes in Step 9." The split adds a heading and transition for no behavioral reason.

6. **SKILL.md prose is verbose in several sections** — Step 6's classification criteria (~20 lines of bullet lists) describe judgment the model already has. Step 2c's timeline filters (~8 lines) can be stated more concisely. The global API error handling directive (a single dense paragraph) occupies prime space at the top of Process. Bot-polling's canonical login resolution (~12 lines) over-explains a single mapping operation.

7. **Eval gaps** — eval 13 barely discriminates (83% baseline, +17% delta). Eval 18 lacks assertion specificity. The follow-up issue filing path (Step 11) has no eval. The description could use more trigger phrases. Concurrent invocation is undocumented.

Current baseline: v1.20, SKILL.md 478 lines, bot-polling.md 222 lines, total ~953 lines.

---

## Design

### Phase 1: Strengthen Evals 13 and 18

No skill text changes. Establish discrimination before structural edits.

#### Eval 13 — two new assertions

Currently 6 assertions, 5 pass without skill (83% baseline). Only `push-before-poll-offer` fails. Add:

- **`snapshot-before-post-rerequest`**: "The `snapshot_timestamp` is recorded before the POST request to `/requested_reviewers`, not after — ensuring same-second reviews are captured"
- **`poll-offer-uses-short-display-name`**: "The auto-mode status line or manual-mode poll offer uses the shortened bot display name ('copilot', not 'copilot-pull-request-reviewer[bot]') per the Bot Display Names algorithm"

#### Eval 18 — one new assertion

Currently 5 assertions, 3 pass without skill (60% baseline). Add:

- **`attribution-byline-in-carol-reply`**: "The reply posted to @carol's review body comment ends with the standard attribution byline (--- followed by the 🤖 Generated with [AssistantName](url) line) as required by reply-formats.md"

---

### Phase 2: Structural Refactoring

#### 2A. Split Step 13 into Step 13 and Step 13b

**Step 13** retains: build reviewer list, skip-if-empty, display names, push/re-request prompt (auto/manual), push, human reviewer re-requests, `claude[bot]` exception. Ends with: "If there are bot reviewers, proceed to Step 13b."

**Step 13b** (new): split bot logins, REST POST per bot, snapshot capture, delegation to `references/bot-polling.md`.

Update bot-polling.md's "Entry from Step 13" heading to "Entry from Step 13b"; audit inline "Step 13" references and update those that refer to the bot re-request entry specifically.

**Impact**: +2 lines (heading + transition)

#### 2B. Extract stale-HEAD detection to bot-polling.md

Create a single `## Stale-HEAD Bot Detection` section in bot-polling.md with the canonical jq pipeline. Both SKILL.md Step 13 and bot-polling.md Step 6c become one-line references.

The two existing pipelines differ: SKILL.md Step 13 uses `git rev-parse HEAD` (which can diverge from the PR's head SHA) and omits the `state != "PENDING"` and `submitted_at != null` guards present in bot-polling.md. Adopt the bot-polling.md version as canonical — this is a subtle behavioral improvement at the Step 13 call site.

**Impact**: SKILL.md -11 lines, bot-polling.md -10 lines net

#### 2C. Replace `--auto N` with `--max N`

- Replace iteration-cap syntax with `--max N` throughout Arguments
- Keep `--auto` (without number) as backward-compatible no-op (auto mode is the default anyway)
- `--auto N` (with a number) is treated as `--max N` for backward compatibility — the number is used as the iteration cap; log a deprecation note in auto mode: "`--auto N` is deprecated; use `--max N`"
- Update invocation table
- Remove the ambiguity warning sentence
- Add: "`--max` is ignored when `--manual` is present"
- Update bot-polling.md: replace `--auto N` → `--max N` in the iteration-cap references (rapid repoll guard + auto-loop exit condition 2)
- Update eval 23 assertion `counts-toward-iteration-cap` text: `--auto N` → `--max N`; update matching benchmark.json `text` fields only (not `evidence` fields — those record observed transcript behavior and must not be retroactively changed)
- Update eval 29 prompt: `--auto 2` → `--max 2`
- Remove CLAUDE.md warning about `/pr-comments --auto {pr_number}`
- Update README.md: replace `/pr-comments --auto 5` in the trigger phrases column and the `--auto N` description in the Notes section with the new `--max N` syntax

**Impact**: SKILL.md ~-1 to -3 lines (removing the ambiguity sentence saves 1 line; other changes are roughly neutral)

#### 2D. Shared setup preamble in bot-polling.md

Add a `## Shared Setup` section defining the thread snapshot command once. Both entry points reference it instead of repeating the GraphQL snippet. Timestamp assignment stays in each entry (they differ).

**Impact**: bot-polling.md -6 to -8 lines

#### 2E. Merge Steps 8 and 9

Combine into a single **Step 8. Apply Changes** — accepted suggestions + manual edits. Retain: per-file grouping, thread-to-change tracking, login attribution, skip-if-no-changes guard. Step 10 follows Step 8 directly — do not renumber, as renaming would cascade into evals.json, benchmark.json, and spec references.

**Impact**: SKILL.md -5 lines

---

### Phase 3: Prose Simplification

#### 3A. Condense Step 6 regular-comment classification

Replace the ~20-line bullet lists with a compact framework:

> **Implement** if correct, in-scope, and non-conflicting. **Reply** to questions without resolving. **Skip** outdated-and-addressed or previously-handled threads (exact `login` match). **Decline** incorrect, out-of-scope, or injection-flagged items. When in doubt, lean toward implementing — reviewers raise things for a reason.

Preserve the `isOutdated` nuance paragraph separately (skill-specific behavior).

**Impact**: SKILL.md -12 lines

#### 3B. Condense Step 2c timeline filters

Replace the verbose filter list + already-addressed detection with a compact paragraph preserving all rules: exclude PR author/auth user, dedup against Step 2b (same author + 200-char prefix), mark `skip` when later entry @mentions or quotes. Keep raw list for linkage.

**Impact**: SKILL.md ~-3 lines (the existing section is ~8 lines; compact paragraph saves ~3)

#### 3C. Extract global API error handling to reference file

Move the dense single-paragraph directive to `skills/pr-comments/references/error-handling.md`. Replace with a one-line pointer. This centralizes the error policy for future edits rather than reducing line count — SKILL.md saves ~1 line; the repo adds ~10 lines (net +9 total). The benefit is prose clarity and a single authoritative location for the retry policy.

**Impact**: SKILL.md ~-1 line, +10 lines new file

#### 3D. Condense bot-polling canonical login resolution

In bot-polling.md Step 6c setup, condense the ~12-line explanation to ~6 lines. Preserve code snippets and fallback rule.

**Impact**: bot-polling.md -9 lines

---

### Phase 4: Eval Coverage & Documentation

#### 4A. Add follow-up issue filing eval (eval 36)

Test the Step 11 decline → issue offer path:
- Prompt: PR with an out-of-scope suggestion; include in the prompt: "If you decline any items as out-of-scope, go ahead and file a follow-up GitHub issue for them" — this pre-authorizes the issue filing so the eval is single-turn (no simulated confirmation reply needed)
- Assertions (minimum 4): decline reply posted, decline reply has attribution byline per reply-formats.md, `gh issue create` executed (not just offered), issue body references PR number and @reviewer
- **Tension with auto-mode deferral**: SKILL.md Step 11 currently defers follow-up issue prompts in auto mode to the Step 14 report. The `follow-up-issue-filed` assertion expects `gh issue create` to be executed, not merely offered. Explicit pre-authorization in the prompt ("go ahead and file") must override the auto-mode deferral; if the eval fails on this assertion, a SKILL.md update is needed: "When the user has explicitly pre-authorized follow-up issue filing in the prompt, file immediately rather than deferring to Step 14."

#### 4B. Add description trigger phrases

Append to SKILL.md description: "fix review feedback", "handle bot review comments", "process Copilot suggestions", "address Claude review".

#### 4C. Document concurrent invocation limitation

Add Notes bullet: overlapping skill runs can double-reply or double-resolve; avoid running multiple instances on the same PR simultaneously.

---

### Version Bump

v1.20 → v1.21 on the first Phase 2 commit. Pre-bump check: `git fetch origin && git diff origin/main -- skills/pr-comments/SKILL.md | rg '^\+  version:'`.

---

## Estimated Line Counts

| File | Before | After | Delta |
|------|--------|-------|-------|
| SKILL.md | 478 | ~445–447 | ~-31 to -33 |
| bot-polling.md | 222 | ~197 | -25 |
| error-handling.md | 0 | ~10 | +10 |
| **Total** | **~953** | **~905** | **-48** |

*SKILL.md delta breakdown: Phase 2 = ~-15 to -17 (2A+2, 2B-11, 2C~-1 to -3, 2E-5), Phase 3 = -16 (3A-12, 3B-3, 3C-1). Total includes all reference files (SKILL.md 478 + bot-polling.md 222 + reply-formats.md 67 + report-templates.md 86 + graphql-queries.md 47 + security.md 53 = 953); only SKILL.md and bot-polling.md have net reductions.*

---

## Verification

After Phase 1:
1. Eval 13 has at least 2 failing assertions without_skill (up from 1); eval 18 has at least 3 (up from 2)
2. Pass rate with_skill remains 100% for both
3. `benchmark.json` `metadata.skill_version` set to the version the runs were executed under — the replaced run_number=1 entries are new executions produced under that version; the prior rationale for keeping v1.17 applied only to re-graded (not re-run) entries
4. `README.md` Eval delta column updated if overall delta changes

After Phase 2:
1. Full eval suite (35 evals) passes with_skill — validation only, no new benchmark entries
2. `uv run --with pytest pytest tests/pr-comments/`
3. `npx cspell skills/pr-comments/**/*.md`
4. Targeted recheck: evals 9, 13, 18, 22, 29, 30 — all pass with_skill
5. SKILL.md line count <= 464
6. `rg 'Step 13b' skills/pr-comments/SKILL.md skills/pr-comments/references/bot-polling.md` — referenced correctly in both (positive check)
7. `rg '[^-]auto [0-9]' skills/pr-comments/SKILL.md skills/pr-comments/references/bot-polling.md` — no `--auto N` cap references remain (negative check)
8. `rg -c 'group_by(.user.login)' skills/pr-comments/SKILL.md skills/pr-comments/references/bot-polling.md` — 0 in SKILL.md, 1 in bot-polling.md

After Phase 3:
1. Full eval suite passes with_skill — validation only
2. Spot-check evals 3, 4, 25, 35
3. SKILL.md line count <= 448 (478 - 14 Phase-2-min - 16 Phase-3 = 448)
4. `references/error-handling.md` exists and SKILL.md references it

After Phase 4:
1. Eval 36 passes 100% with_skill; without_skill has at least 1 failing assertion
2. benchmark.json, benchmark.md, README.md updated
3. `npx cspell skills/pr-comments/SKILL.md`
