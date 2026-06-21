# peer-review — Present Findings templates (Step 5)

SKILL.md Step 5 selects the bucket (no findings / triage skipped all / has
findings) and directs you here. Use the template matching that bucket. `[model]`
is the displayed model identifier per the Step 5 rule; the PR-URL and
stop-generating behaviors stay in SKILL.md Step 5.

## No findings

Reviewer returned `NO FINDINGS` on the self/Claude path, or the external CLI returned nothing before triage:

```
## Peer Review — [target] ([model])

No issues found.
```

## Triage skipped all (external CLI path only)

Triage classified every finding as skip:

```
## Peer Review — [target] ([model])

No issues recommended.

Triage filtered all [N] findings:
- [title] — [reason]
```

## Findings

Display the recommended findings numbered sequentially (`1, 2, 3...`) grouped by severity. If there are triage-skipped findings, list them below the separator with `S`-prefix numbering (`S1, S2...`):

```
## Peer Review — [target] ([model])

### Critical
1. **[Issue title]** — `[file]`
   [Problem description]
   Fix: [specific change]

### Major
2. ...

### Minor
3. ...

---
Triage filtered [M] of [N] findings:
S1. **[Skipped title]** — [reason]
S2. **[Skipped title]** — [reason]

Apply all recommended, include skipped by S-number, or skip? [all/1,2/1,S1/skip]
```

On the self/Claude path (no triage), there is no "Triage filtered" section and the apply prompt is the standard form: `Apply all, select by number, or skip? [all/1,3,5/skip]`
