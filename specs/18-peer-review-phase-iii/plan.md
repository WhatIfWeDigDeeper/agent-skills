# Spec 18: peer-review — Phase III (triage layer + post-apply re-scan) (v1.1 → v1.2)

## Problem

Phase II (v1.1) routes the review prompt to external CLIs (copilot, gemini, codex) and normalizes their output into severity-grouped findings. But:

1. **External CLIs are noisy.** They don't have project context — they flag things that are already documented, contradict verified behavior, or are low-confidence opinion. During Phase II testing, copilot flagged a "legacy install hint" that contradicted our own verified flag list; gemini flagged an "ARG_MAX risk" already noted in the plan. Both were false positives. The author has to manually judge each finding before applying.

2. **Apply has no verification pass.** After applying findings, there is no way to confirm the changes didn't introduce new inconsistencies. A spec edit that fixes one stale reference may create another.

Current state: `skills/peer-review/SKILL.md` v1.1, 356 lines.

---

## Design

### Feature 1: Claude triage layer (external CLI path only)

After Step 4d parses and normalizes the external CLI's findings, a new Step 4e spawns a fresh Claude subagent to classify each finding as `recommend` or `skip`.

The triage subagent receives:
- The normalized findings list (title, severity, file, location, problem, fix)
- The content collected in Step 2 — for path targets (spec/consistency) this is the file contents; for diff targets (staged/branch/PR) this is the diff text; the subagent cannot access files not already collected
- The review mode (`spec` / `consistency` / `diff`) so it knows how to interpret the content
- A triage prompt (see below)

The triage subagent returns a classification for each finding:
```
FINDING 1: recommend
FINDING 2: skip — ARG_MAX risk is already documented in the plan (see "Note: passing ... may fail")
FINDING 3: recommend
```

Findings are split into two buckets: **recommended** (present in Step 5 apply list) and **skipped** (listed below the apply prompt for transparency).

**Triage prompt:**
```
You are reviewing a list of findings produced by an external code reviewer.
Your job is to classify each finding as recommend or skip.

Review mode: [spec / consistency / diff]
Content type: [file contents / diff text]

Recommend a finding if:
- The issue is real and not already addressed in the reviewed content
- The finding adds information the author doesn't already have
- The fix is actionable

Skip a finding if:
- The issue is already documented or handled in the reviewed content
- The finding contradicts verified facts in the content
- The finding is speculative or opinion without clear evidence
- The fix is already present

For each finding, output exactly one line:
FINDING N: recommend
or
FINDING N: skip — [one-line reason]

[NORMALIZED FINDINGS]

[COLLECTED CONTENT — file contents for spec/consistency mode, diff text for diff mode]
```

**Triage failure fallback:** If the triage subagent output cannot be parsed (missing `FINDING N:` lines, wrong format, empty response), treat all findings as `recommend` and prepend a note to the Step 5 output: "Triage unavailable — showing all findings."

**Step 5 changes:**

If all findings were skipped (or there were no findings), output:

```
## Peer Review — [target] ([model])

No issues recommended.

Triage filtered all [N] findings:
- [title] — [reason]
```

Then stop. Do not show an apply prompt.

Otherwise, display recommended findings numbered sequentially, then skipped findings with an `S`-prefix:

```
## Peer Review — [target] ([model])

### Critical
1. **[Issue title]** — `[file]`
   [Problem]
   Fix: [fix]

### Major
2. ...

---
Triage filtered [M] of [N] findings:
S1. **[Skipped title]** — [reason]
S2. **[Skipped title]** — [reason]

Apply all recommended, include skipped by S-number, or skip? [all/1,2/1,S1/skip]
```

Recommended findings are numbered `1, 2, 3...` in presentation order. Skipped findings are numbered `S1, S2...`. This avoids display gaps and makes it visually clear which findings are triage overrides.

**`all` applies only recommended findings.** To include a skipped finding, the user references its S-number (e.g., `1,S1` or `S2`).

**Scope**: triage applies only to the external CLI path. When `--model` starts with `claude-`, Step 4 is unchanged — Claude's own output goes directly to Step 5 without a triage pass.

---

### Feature 2: Post-apply re-scan

After Step 6 applies at least one finding, offer a re-scan of the modified files:

```
Applied N finding(s).

Re-scan modified files for new issues? [y/n]
```

Output this as your **final message and stop generating**. Resume only after the user replies.

On `y`: collect the modified files' current content, build the **consistency mode** prompt (always consistency, regardless of the original review mode — after applying edits you're checking the changed files for drift, not regenerating a branch diff or re-reading a spec pair), and spawn a fresh Claude subagent (always Claude, regardless of the original `--model`). Present findings via Step 5. If no new issues are found, output "No new issues found in re-scan." and stop.

On `n`: stop.

**Trigger condition**: re-scan is offered only when at least one file was actually modified. If the user replied `skip` to the apply prompt, no re-scan is offered.

**Depth limit**: re-scan is offered at most once. When Step 6 executes during a re-scan cycle, it does not offer another re-scan — output "Applied N finding(s)." and stop.

---

## SKILL.md changes

### Step 4 (external CLI path only)

Current:
```
4a. Check binary
4b. Write temp file
4c. Execute
4d. Parse → normalized findings
4e. Continue to Step 5
```

New:
```
4a. Check binary
4b. Write temp file
4c. Execute
4d. Parse → normalized findings
4e. Triage findings (new)
    - Spawn Claude subagent with triage prompt + findings + file contents
    - Split findings into recommend/skip buckets
4f. Continue to Step 5 with classified findings
```

### Step 5

Add triage display logic:
- If no recommended findings: show "No issues recommended." + triage summary; stop; no apply prompt
- Otherwise: show recommended findings, then triage-filtered section, then modified apply prompt

### Step 6

Update selection parsing: `all` applies only recommended findings. An explicit number (e.g., `1,S1`) applies that finding regardless of triage classification — `S`-prefixed numbers refer to skipped findings by their triage order. `skip` stops with no changes.

After applying ≥1 finding: output re-scan offer; stop generating; resume on reply.
On `y`: run re-scan (Claude path, consistency mode, at most once); feed into Step 5.
On `n`: stop.

### Notes section

Add a bullet for each new feature:
- **Triage layer**: describe the triage-on-external-CLI behavior
- **Post-apply re-scan**: describe the opt-in re-scan

---

## Evals strategy

All new evals are fixture-based (no live CLI calls needed). The triage subagent call must be testable in isolation.

Six new evals:

- `triage-skips-false-positive` — fixture: 2 normalized findings, one of which contradicts content embedded in the prompt (e.g., "install hint is legacy" but the content already shows the correct hint); assertion: (1) the contradicted finding appears in the "Triage filtered" section, not in the apply list; (2) the valid finding is presented in the apply list
- `triage-all-skipped` — fixture: all findings are low-confidence opinions; assertion: (1) "No issues recommended." is shown; (2) no apply prompt is shown; (3) the triage filtered summary lists all skipped findings with reasons
- `triage-not-on-claude-path` — regression guard: ensures the triage layer does not accidentally activate on the Claude path; run with default `--model`; fixture: Claude subagent returns two findings; assertion: (1) findings are presented directly without a "Triage filtered" section; (2) apply prompt is the standard form ("Apply all, select by number, or skip?"), not the "Apply all recommended" form
- `triage-user-includes-skipped` — fixture: 1 recommended finding (number 1) and 1 skipped finding (number S1); user replies `S1` to include only the skipped finding; assertion: the skipped finding is applied and the recommended finding is not applied
- `rescan-offered-after-apply` — fixture: findings applied to a file; assertion: the re-scan offer ("Re-scan modified files for new issues?") is shown after "Applied N finding(s)."
- `rescan-not-offered-after-skip` — user replies `skip` to the apply prompt; assertion: no re-scan offer is shown; "Skipped N findings" is the final output

Existing evals 1–9 remain unchanged (they exercise the Claude path and are unaffected by the external-CLI-only triage layer).
