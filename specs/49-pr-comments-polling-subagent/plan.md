# Spec 49: pr-comments — delegate the Shared polling loop to a background subagent

## Context

`skills/pr-comments/SKILL.md` (v1.48, 491 lines) enters a **Shared polling
loop** — defined in `references/bot-polling.md` (322 lines) — whenever it waits
for an async bot review. Two entry points reach it: **Step 6c** (the all-skip
repoll gate) and **Step 13b** (post-commit re-request). The loop polls three
signals every 60 s for up to 10 min and, when a signal fires, loops back to
Step 2 to re-fetch and reprocess.

On Claude Code (the loop's Tier 1), the 60 s cadence is implemented with
`ScheduleWakeup(60s, "/pr-comments N")` — which **ends the turn and re-invokes
the entire skill**. Each poll cycle therefore re-reads SKILL.md +
`bot-polling.md` and re-runs fetch → screen → classify just to check three
signals, and it re-runs untrusted-content screening (Steps 5–6) on every wake.
That is the real cost this spec targets: not in-context loop bloat, but repeated
full-skill re-invocation.

### Current reality (verified before writing this spec)

- `skills/pr-comments/SKILL.md` is **v1.48, 491 lines**.
- `references/bot-polling.md` is **322 lines**; it defines **Shared Setup**,
  **Entry from Step 13b**, **Entry from Step 6c**, **Stale-HEAD Bot Detection**,
  the **Shared polling loop** (Runtime capability check, Signals 1/2/3, Poll
  interval and timeout, On new threads detected), **Bot Display Names**, and a
  known-limitations section.
- `ScheduleWakeup` / "Shared polling loop" appear **12 times** in
  `bot-polling.md`.
- The loop's **Runtime capability check** already tiers runtimes: Tier 1
  (delayed-resume scheduler, e.g. `ScheduleWakeup`), Tier 2 (blocking
  `sleep 60`), Tier 3 (neither → single immediate pass then re-invoke message).
- **Signals** are read-only `gh api` + `jq`: Signal 1 = new unresolved threads
  vs. snapshot; Signal 2 = new review submitted per bot since
  `snapshot_timestamp`; Signal 3 = new timeline comment per bot. Signal 1 has
  priority; Signal 2/3 use the **canonical** `.user.login` (never
  `endswith("[bot]")`).
- Both entry points converge on the **same** Shared polling loop after their own
  pre-loop work (6c's pending/post-fetch/stale-HEAD checks; 13b's re-request
  POST + `review_requested` verification gate).

## Problem

Every 60 s poll on Claude Code re-invokes the whole skill (re-reading ~490 + 322
lines of instructions and re-running untrusted-content screening) to check three
read-only signals — expensive in tokens and redundant in security screening.

## Goals

1. **Isolate the poll.** Introduce a **read-only polling subagent** that owns
   *only* the Shared polling loop: it watches Signals 1/2/3 on the 60 s cadence
   and returns a compact verdict. The main turn carries none of the loop.
2. **Cut cost.** Run the subagent on a **cheaper/faster model tier** than the
   main agent (in Claude Code: Sonnet), and eliminate the 60 s full-skill
   re-invocations.
3. **Preserve every invariant.** All writes and **all** untrusted-content
   classification stay in the main agent (Opus). The subagent is read-only and
   returns only signal metadata — never comment bodies, classifications, or plan
   rows.
4. **Stay portable.** Express the delegation in capability-neutral language; the
   existing inline tier-aware loop remains the universal fallback and the
   canonical spec of what the subagent replicates.

## Non-goals

- Delegating fetch / screen / classify / apply / reply / resolve / push — those
  stay in the main agent. This spec touches **only** the wait-and-detect loop.
- Delegating the Step 13b re-request POST or its `review_requested` verification
  gate — those are credentialed and stay in main.
- Wiring up Codex/Copilot background-task primitives. Those runtimes keep the
  existing inline path unchanged; active support is optional future work gated
  on confirming each has the primitive.

## Decisions (confirmed with user)

- **Boundary: wait-and-detect only.** The subagent owns just the Shared polling
  loop. Main keeps the re-request POST, the verification gate, and looping back
  to Step 2 to reprocess.
- **Mechanism: background agent that notifies on completion.** Main launches the
  subagent with `run_in_background`, ends its turn, and is re-invoked with the
  verdict when a signal fires or the poll times out. No 60 s full-skill
  re-invocations.
- **Both entry points** (6c and 13b) route through the subagent — they already
  share one loop, so one subagent + one verdict contract covers both.
- **Portability: additive Tier-0 enhancement.** Capability-neutral delegation
  language; inline Tier 1/2/3 loop preserved verbatim as the fallback and the
  subagent's instruction set. No per-harness subagent lookup needed.
- **Model: cheaper tier, concretely Sonnet on Claude Code, behind a qualifier.**
  Named as a suggestion, never a universal requirement (Codex/Copilot never
  reach this path and could not dispatch on an Anthropic model anyway).

## Design

### Architecture & boundary

```
Main agent (Opus)                          Polling subagent (Sonnet, background)
─────────────────                          ─────────────────────────────────────
6c pre-loop checks  ─┐
13b re-request POST  ├─ hand off ──▶  receives IN-state (below)
+ verification gate  ┘
   (ends turn)                          polls Signals 1/2/3 on 60 s cadence
                                        until a signal fires or timeout
   re-invoked  ◀──── notify ───────  returns VERDICT (compact JSON)
   with verdict
   │
   ├─ new_threads      → loop back to Step 2 (re-fetch, re-screen, reprocess)
   ├─ all_clean        → Step 14 report (note clean exit)
   └─ timeout          → Step 14 "re-invoke when ready" message
```

If the runtime has **no** background-agent primitive (not Tier 0), main never
spawns the subagent — it runs the existing inline Tier 1/2/3 loop instead. That
branch is decided in the **Runtime capability check** *before* any handoff, so
"can't background-poll" is not a verdict the subagent returns.

Invariants preserved:

- **All writes stay in main** — re-request POST, commits, replies, resolves,
  push. The subagent runs only `gh api` reads and `jq`.
- **All untrusted-content screening/classification stays in main (Opus)** — on
  `new_threads` the subagent returns only thread IDs; main re-fetches those
  threads' bodies and re-screens (Steps 5–6) from scratch.
- **Signal priority preserved inside the subagent** — Signal 1 (new threads)
  outranks Signals 2/3 in the same cycle.

### State handoff — what main passes IN

The subagent holds no prior context; main passes the full poll state:

| Field | Source | Purpose |
|---|---|---|
| `owner`, `repo`, `pr_number` | Step 1 | API calls |
| `snapshot_timestamp` | recorded **before** POST (13b) or `= fetch_timestamp` (6c) | Signal 2/3 lower bound; ISO-8601 UTC ending `Z` |
| `unresolved_thread_ids[]` | fresh snapshot (Shared Setup) | Signal 1 baseline |
| `bot_logins[]` (canonical) | 6c setup / 13b reviewer list | Signal 2/3 per-bot equality match — never `endswith("[bot]")` |
| `poll_interval_secs` (60), `timeout_secs` (600) | reference defaults | cadence + stop |
| `mode` (auto/manual) | run mode | affects only whether main re-prompts on return; the subagent just watches |

### Verdict contract — what the subagent returns

```json
{
  "outcome": "new_threads | all_clean | timeout",
  "new_unresolved_thread_ids": ["..."],
  "bots_with_new_review": ["copilot-pull-request-reviewer[bot]"],
  "bots_pending": ["..."],
  "signal_fired": "1 | 2 | 3 | none",
  "polled_seconds": 180,
  "note": "human-readable one-liner for the report/observability"
}
```

Outcome → main's next action:

- `new_threads` → loop back to Step 2 (`new_unresolved_thread_ids` names what to
  re-fetch; main re-screens from scratch).
- `all_clean` → all polled bots have a Signal-2 review since `snapshot_timestamp`
  and Signal 1 never fired → Step 14 with a clean-exit note.
- `timeout` → Step 14 "re-invoke when ready" message.

(The no-background-primitive case is handled *before* spawn in the Runtime
capability check — main runs the inline tier loop and never spawns the subagent,
so it is not a verdict outcome.)

**Deliberately NOT in the contract:** no comment bodies, no classifications, no
plan rows. Pure signal metadata — this is what keeps the security boundary in
main.

### File changes

**`references/bot-polling.md`** (bulk of the change):

- In **Runtime capability check**, add a preferred tier above Tier 1: *"Tier 0 —
  a background task that resumes the parent agent on completion is available (in
  Claude Code: a `run_in_background` Agent on a cheaper model tier, e.g. Sonnet).
  Delegate the Shared polling loop to it per the **Polling subagent** section."*
  Tiers 1/2/3 stay verbatim as fallbacks; a runtime with no Tier-0 primitive
  never spawns the subagent and runs the inline loop instead.
- New **`## Polling subagent`** section: the IN-state table, the VERDICT JSON
  contract, the read-only constraint, the Sonnet-with-qualifier model note, and
  the `outcome` → main-action mapping. It **references** the existing **Signals**
  subsection as the spec of what the subagent runs — no signal logic duplicated.
- The existing **Signals / Poll interval and timeout / On new threads detected**
  subsections stay as-is: they are both the inline fallback and the subagent's
  instruction set.

**`skills/pr-comments/SKILL.md`**:

- Step 6c and Step 13b: where each delegates to "the Shared polling loop," add
  "(or delegate it to the polling subagent — see `references/bot-polling.md` →
  **Polling subagent**)."
- `metadata.version` bump (once, per repo rule).

**Portability framing** throughout: capability-neutral language with "in Claude
Code: …" qualifiers; no hardcoded model or tool name stated as a universal
requirement.

### Testing & security

- **Tests** (`tests/pr-comments/`): the `outcome` → main-action mapping and
  IN-state completeness are classifiable — add coverage asserting each of the
  three outcomes routes to the correct main step (plus the pre-spawn
  no-Tier-0 branch), and that the contract carries no
  comment-body/classification fields (security boundary).
- **Security baseline** (`evals/security/pr-comments.baseline.json`): the
  subagent adds no new ingestion (returns only signal metadata), so no baseline
  change is expected. Re-run `bash evals/security/scan.sh` to confirm; refresh
  in-PR only if findings actually change.
- **Existing `tests/pr-comments/` must stay green** — this change is additive.

## Risks & mitigations

- **Verdict correctness** (missed signal / false `all_clean`). Mitigation: the
  subagent runs the *same* Signal logic as the inline loop (relocated, not
  rewritten); Sonnet headroom over Haiku for the per-bot tracking; tests assert
  the outcome mapping.
- **State-handoff loss** (dropped `snapshot_timestamp` or thread snapshot breaks
  the same-second / stale-HEAD invariants). Mitigation: explicit IN-state table;
  main takes the snapshot **before** the POST exactly as today and passes it in
  verbatim.
- **Portability regression.** Mitigation: inline loop untouched as fallback;
  delegation is capability-gated — a runtime with no Tier-0 primitive never
  spawns the subagent and runs the inline Tier 1/2/3 loop (decided before any
  handoff, not a verdict outcome).
