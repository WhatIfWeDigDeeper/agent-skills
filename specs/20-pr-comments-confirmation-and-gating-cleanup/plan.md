# Spec 20: pr-comments — Confirmation Prompt Dedup & Step 13b/14 Gating Consolidation (v1.25 → v1.26)

## Problem

The pr-comments skill (v1.25, 457 lines, 100% eval pass rate, +66pp delta) has accumulated two divergence-risk hot spots where the same rule is encoded in multiple places. Future edits can silently fix one site and miss the others:

1. **Step 7's `Proceed? [y/N/auto]` confirmation prompt is stated verbatim in two branches.**
   - SKILL.md:265 — manual-mode branch.
   - SKILL.md:269 — auto-mode escalation branch (security flags, oversized comments, diff-validation declines, consistency items).
   - Both branches independently restate: the prompt line, the "stop generating" instruction, the "do not supply an answer", the "do not assume `y`", the "do not continue to Step 8", and the "resume only after the user replies". A fix to one branch (e.g., clarifying what "resume" means) will not reach the other.

2. **Step 13b/14's "do not fall through" invariant is policed in three independent places.**
   - SKILL.md:418 — WARNING blockquote in Step 13b: "This step does NOT normally end at Step 14."
   - SKILL.md:435-440 — Numbered "do NOT proceed to Step 14 directly" checklist, 4 items.
   - SKILL.md:444 — Step 14 Entry gate blockquote: "If you just completed Step 13b... you are **not here yet** — return to Step 13b item 3 and resume the shared polling flow first."
   - The three guards accumulated as patches for past regressions. Each restates the rule in different wording; a future edit that fixes one leaves the others stale. The Step 14 Entry gate (L444) already enumerates the four valid handoff paths cleanly — it is the right place to state the rule.

## Why not the other items from the review pass

The original review pass identified five candidate cleanups under Track A (A2, A3, A4, A5, A8) and a Track B (reference file rebalancing). Cross-referencing against `specs/14-pr-comments-review-improvements/` (v1.18) and `specs/15-pr-comments-structural-cleanup/` (v1.21) showed that:

- Most structural opportunities were already addressed by those prior specs (Step 6 condensation, bot-polling.md 3-section restructure, error-handling.md extraction, `--auto N` → `--max N` migration, Steps 8/9 merge, Bot Display Names simplification).
- Missing Step 9 is **intentional** per spec 15 Phase 2E — renumbering would cascade across evals/benchmark/specs.
- bot-polling.md was **just restructured** in spec 14 Phase 3; further splitting would undo recent thoughtful work.
- error-handling.md is **intentionally thin** per spec 14 Phase 2A, which deliberately removed concrete backoff timings.

The remaining readability-only items (A4 Arguments reorg, A5 byline dedup, A8 Step 6c handoff prose) are valid but lower-value. They are **deferred** — this spec focuses only on the two items with real divergence-risk benefit.

Current baseline: v1.25, SKILL.md 457 lines.

---

## Design

### Phase 1: Extract the Step 7 Confirmation Prompt Template

**Goal.** Define the confirmation prompt — including the "stop generating + don't assume `y` + don't continue + resume only after user replies" language — exactly **once** in Step 7. Make both branches reference it.

**Current structure (SKILL.md:260-269).**

```
**Responses (when the confirmation prompt is shown):**
- `y` — proceed normally
- `n` — abort
- `auto` — proceed AND switch to auto mode for all remaining bot-review iterations; subsequent iterations skip this confirmation gate (plan table still shown for observability)

If `--manual` was passed, show the `Proceed? [y/N/auto]` prompt above and **stop generating**. Do not supply an answer, do not assume `y`, do not continue to Step 8. Output the prompt as your final message and wait. Resume only after the user replies with `y`, `n`, or `auto`.

Otherwise (auto mode, the default), skip this confirmation prompt entirely — show the plan table above but proceed without waiting.

If any condition requires manual confirmation in this iteration (for example, security screening flags from Step 5, oversized comments, diff-validation declines from Step 6, or `consistency` items from Step 6b), always drop to manual confirmation regardless of auto-mode — show the `Proceed? [y/N/auto]` prompt above and **stop generating**. Do not supply an answer, do not assume `y`, do not continue to Step 8. Output the prompt as your final message and wait. Resume only after the user replies with `y`, `n`, or `auto`. Here, `consistency` rows are inferred cross-file follow-ups from Step 6b and always require explicit confirmation, even in auto-mode.
```

**Target structure.** Introduce an explicit **Confirmation prompt template** sub-block inside Step 7 that defines the prompt string, the response semantics, and the "stop generating" behavior in one place. Then the three branches become short and distinct:

```
**Confirmation prompt template.** When this prompt needs to be shown, emit exactly:

    Proceed? [y/N/auto]

Responses:
- `y` — proceed normally
- `n` — abort
- `auto` — proceed AND switch to auto mode for all remaining bot-review iterations; subsequent iterations skip this confirmation gate (plan table still shown for observability)

Output the prompt as your final message and **stop generating**. Do not supply an answer, do not assume `y`, do not continue to Step 8. Resume only after the user replies with `y`, `n`, or `auto`.

**When to show the prompt:**
- **Manual mode (`--manual` was passed)** — always. Emit the Confirmation prompt template above.
- **Auto mode (default)** — skip the prompt; show the plan table for observability and proceed.
- **Auto mode escalation** — if any condition in this iteration requires manual confirmation (security screening flags from Step 5, oversized comments, diff-validation declines from Step 6, or `consistency` items from Step 6b), drop to manual confirmation regardless of mode and emit the Confirmation prompt template above. `consistency` rows always require explicit confirmation, even in auto mode.
```

**Load-bearing phrases that must survive the edit** (per CLAUDE.md "Confirmation prompts require 'stop generating' instructions"):
- "stop generating"
- "do not supply an answer"
- "do not assume `y`"
- "do not continue to Step 8"
- "resume only after the user replies"

All must appear in the Confirmation prompt template block — not in the branches.

**Estimated impact.** ~5 lines removed. The escalation branch (currently L269, the longest sentence in Step 7) becomes a single pointer bullet. No behavior change; the agent's observable behavior is identical.

---

### Phase 2: Consolidate the Step 13b/14 "Do Not Fall Through" Invariant

**Goal.** Make the **Step 14 Entry gate blockquote (SKILL.md:444)** the single authoritative statement of valid Step 14 entry conditions. Replace the two redundant guards in Step 13b with minimal forward pointers.

**Current structure (SKILL.md:416-444).**

- **L416-418** Step 13b opens with a WARNING blockquote: "This step does NOT normally end at Step 14. After the POST, follow `references/bot-polling.md`: in the normal path, enter the polling loop. Step 14 is reachable only through the polling-loop exit conditions or the documented manual-mode decline path from `references/bot-polling.md` — never by falling through from 13b."
- **L435-440** After the POST call, a numbered list:
  1. Confirm the pre-POST snapshot was recorded.
  2. Confirm the POST re-request was sent for each bot reviewer.
  3. **Resume the shared bot-polling flow in `references/bot-polling.md` after its setup section** — do not restart setup (snapshot + POST already done).
  4. Step 14 only when `references/bot-polling.md` routes you there: either after the polling flow exits through its defined exit conditions, or immediately after the user declines the manual-mode poll offer.
- **L444** Step 14 Entry gate blockquote: "Reach Step 14 via one of: Step 13 found no reviewers (empty list); the user declined the Step 13 push/re-request prompt (manual mode); the shared polling loop in `references/bot-polling.md` reached one of its documented exit conditions; or the user declined the manual-mode poll offer in `references/bot-polling.md`. If you just completed Step 13b with bot reviewers re-requested and the user has **not** declined polling, you are **not here yet** — return to Step 13b item 3 and resume the shared polling flow's signal-checking/exit logic first."

**Target structure.**

- **L416-418** Replace the WARNING with a concise forward pointer at the top of Step 13b:
  > After the POST below, follow the shared polling flow in `references/bot-polling.md`. See the Step 14 Entry gate for valid exits from Step 13b.
- **L435-440** Keep items 1-3 as-is (they are the concrete resumption checklist). **Delete item 4** — it duplicates the Step 14 Entry gate.
- **L444** Unchanged. This is now the only place that enumerates valid Step 14 entry paths and the "you are not here yet" constraint.

**Estimated impact.** ~8-10 lines removed. No behavior change — the agent still cannot fall through from 13b to Step 14 except via `bot-polling.md`'s polling-loop exits, because that's precisely what L444 says.

**Invariant preserved.** After the edit, the `bot-polling.md` ↔ Step 14 handoff is governed by exactly one statement (the entry gate at L444). Step 13b only points at it.

---

## Impact

| File | Before | After | Δ |
|---|---|---|---|
| `skills/pr-comments/SKILL.md` | 457 | ~444 | -13 |

- No reference file edits
- No test edits
- No eval edits
- No benchmark edits
- One version bump: v1.25 → v1.26

## Out of scope (deferred)

- **A4** (Arguments section table-first reorg) — readability-only
- **A5** (byline duplication between Step 11 and `references/reply-formats.md`) — readability-only
- **A8** (Step 6c → `bot-polling.md` handoff narrative tightening) — readability-only
- **Track B** (bot-polling.md further split, error-handling.md decision) — already addressed by spec 14 Phase 3
- **Tracks D + E** from the original review (eval coverage expansion, v1.25 benchmark refresh) — separate PRs if desired

---

## Verification

1. `wc -l skills/pr-comments/SKILL.md` → ≤ 446 lines
2. `uv run --with pytest pytest tests/pr-comments/` → all 216 tests pass
3. `npx cspell skills/pr-comments/SKILL.md` → no unknown words
4. `rg -n 'Proceed\? \[y/N/auto\]' skills/pr-comments/SKILL.md` → expect exactly 2 matches (Arguments section + Step 7 confirmation prompt block)
5. `rg -n 'not here yet' skills/pr-comments/SKILL.md` → expect exactly 1 match (the unchanged Step 14 Entry gate at L444)
6. `rg -n 'do NOT proceed|does NOT normally end at Step 14' skills/pr-comments/SKILL.md` → expect 0 matches (both defensive guards removed)
7. `rg -n 'stop generating' skills/pr-comments/SKILL.md` → expect 1 match in Step 7 (inside the template block; no orphaned instances in the branches)
8. Pre-commit version-bump check: `git fetch origin && git diff origin/main -- skills/pr-comments/SKILL.md | rg '^\+  version:'` → exactly one increment
9. Eval regression spot-check (simulated, documentation-only changes): evals 1, 12, 28, 34 with_skill → 100% pass. If any assertion text references the *exact* pre-edit wording that's being removed, update the assertion text in the same PR (per CLAUDE.md "renaming action labels or vocabulary" rule).
