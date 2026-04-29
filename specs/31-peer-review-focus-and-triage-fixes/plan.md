# Spec 31: peer-review — focus flag fixes and triage forwarding

## Problem

Three improvement and hardening items identified during spec-30 review of `peer-review` v1.8:

1. **`--focus ""` produces a malformed reviewer prompt.** If the user passes `--focus` with an empty string (or as the last token with no value), the focus line appended to the reviewer prompt becomes `"Focus especially on . Still report…"` — a grammatically broken directive that confuses the reviewer model.

2. **Path target gives no user-friendly error for a missing path.** When the user supplies a file/dir path that doesn't exist, the skill calls the `Read` tool which then errors on its own — without a clear "path not found" message.

3. **`--focus TOPIC` is not forwarded to the external-CLI triage subagent.** The triage subagent in Step 4e sees findings and reviewed content but not the focus area, so it cannot account for focus when deciding to recommend or skip low-severity findings.

## Finding-by-finding assessment

| # | Finding | Severity | Verdict | Action |
|---|---------|----------|---------|--------|
| 1 | `--focus ""` → malformed focus line in reviewer prompt | Minor bug | **Fix** | Validate that `$FOCUS` is non-empty when `--focus` was provided |
| 2 | Missing-path target produces unhelpful `Read` tool error | Minor UX | **Fix** | Add existence check at start of the Path paragraph in Step 2 |
| 3 | `--focus` value not passed to triage; triage skips/keeps based on issue text alone | Minor accuracy | **Fix** | Add `Focus area:` line to triage prompt + one context-aware skip criterion |

## Design

### Edit A — `--focus` empty validation (and parser variable naming)

Two sub-edits:

**A1.** In the `Parse $ARGUMENTS` bullet list, change the `--focus` line from `Strip --focus TOPIC → store focus topic` to `Strip --focus TOPIC → store TOPIC as $FOCUS`. This mirrors `$PR` and `$BRANCH` naming and makes Edit A2's reference to `$FOCUS` unambiguous.

Phrase anchor: the line containing `strip --focus TOPIC`.

**A2.** In Step 1 "Validate parsed arguments before use", add a fourth bullet immediately after the `--model VALUE` bullet:

> - `$FOCUS` (from `--focus TOPIC`): if `--focus` was provided, require the topic to be non-empty. If empty or whitespace-only, error: `--focus requires a non-empty topic` and stop.

Phrase anchor for insertion: the line containing `--model VALUE`: validated downstream by the supported-prefix check in Step 4.

### Edit B — path-not-found message

In Step 2 under `**Path** (file or directory):`, prepend a sentence before the existing `Read all files…` sentence:

> If the path does not exist, error: `Path not found: <path>` and stop.

Placeholder style `<path>` matches the existing convention in Steps 1's `--pr` and `--branch` error messages (`got: <value>`); phrasing "Path not found:" mirrors "Branch ${BRANCH} not found." in the Branch block.

Phrase anchor: the paragraph starting with `**Path** (file or directory):`.

### Edit C — forward `--focus` into triage prompt

In Step 4e, two sub-edits following the same pattern as `[FOCUS_LINE]` in Step 3:

**C1.** In the triage prompt fenced block, add `[FOCUS_AREA_LINE]` on its own line after `Content type: [file contents for consistency mode / diff text for diff mode]`.

**C2.** Immediately after the closing ` ``` ` of the triage prompt fenced block, add a sibling definition block:

> **Focus area line** (include in triage prompt only when `--focus` is provided):
> ```
> Focus area: [TOPIC]
> ```

**C3.** Add one bullet to the "Skip a finding if:" list inside the triage prompt:

> - When a focus area is specified, the finding is minor severity and is clearly unrelated to that focus area

Phrase anchor for C1: `Content type: [file contents for consistency mode / diff text for diff mode]`.
Phrase anchor for C2: the closing ` ``` ` of the triage prompt fenced block, before the "Parse the triage subagent's response" paragraph.

### Edit D — version bump

`metadata.version: "1.8"` → `metadata.version: "1.9"`. Per `skills/CLAUDE.md`, exactly one bump per PR.

## Files to Modify

| File | Change |
|------|--------|
| `skills/peer-review/SKILL.md` | Edits A–D |
| `cspell.config.yaml` | No new tokens expected |

## Out of Scope

- **`--focus` consuming an adjacent flag as its TOPIC** (e.g. `--focus --model`). The consumed `--model` string is non-empty, so Edit A doesn't catch it — the reviewer just gets a strange focus topic. This is a malformed invocation, not a security risk, and fixing it requires a full left-to-right flag-aware parser. Out of scope.
- **Secret-scanning for path targets.** Edit B only adds a path-existence check; it does not scan file contents for secrets before sending to external models. That was scoped out in spec-30 and remains out of scope here.
- **Eval re-run.** The three fixes are narrow behavior corrections. No evals test `--focus` forwarding to triage or the path-not-found message. Optional spot check in verification.

## Verification

1. `rg -n 'requires a non-empty topic' skills/peer-review/SKILL.md` → exactly 1 match (Edit A)
2. `rg -n 'store TOPIC as' skills/peer-review/SKILL.md` → exactly 1 match in the parser bullet list (Edit A1)
3. `rg -n 'Path not found:' skills/peer-review/SKILL.md` → exactly 1 match in Step 2 path paragraph (Edit B)
4. `rg -n 'FOCUS_AREA_LINE' skills/peer-review/SKILL.md` → exactly 2 matches (placeholder in triage template + definition block) (Edit C)
5. `rg -n '^  version:' skills/peer-review/SKILL.md` → `version: "1.9"` (Edit D)
6. `uv run --with pytest pytest tests/` — no regressions
7. Negative test: `/peer-review --focus ""` should error with `--focus requires a non-empty topic`
8. Re-read the triage prompt fenced block end-to-end and confirm `[FOCUS_AREA_LINE]` is inside the fenced block and the `**Focus area line**` definition block is immediately after the closing fence

## Branch

`spec-31-peer-review-focus-and-triage-fixes`

## Peer review (bookend)

- **Phase 0 (pre-spec consistency pass).** Before any SKILL.md edits, run `/peer-review` against `specs/31-peer-review-focus-and-triage-fixes/` to catch drift between `plan.md` and `tasks.md`. Iteration cap 2. Auto-approve valid findings; record summaries inline in tasks.md.
- **Phase 4 (pre-ship branch pass).** After implementation and Phase 3 verification, run `/peer-review --branch spec-31-peer-review-focus-and-triage-fixes` to catch cross-file drift. Iteration cap 3. Loop until zero valid findings or cap. Record summaries inline.
