# Spec 24: learn — "Minimum viable rule text" guideline

## Problem

The `learn` skill's existing `## Guidelines` bullet "Strip obvious explanations from rule text" frames brevity as a side effect of stripping known content — not as an explicit goal. In practice, new config entries still land verbose on first pass because the guideline teaches *what to remove*, not *how short to aim*. The session that prompted this spec required a follow-up prompt ("use the bare minimum number of characters") to trim a two-sentence entry to one line.

## Design

### Change

**File:** `skills/learn/SKILL.md`
**Section:** `## Guidelines` (final bullet, currently "Strip obvious explanations from rule text")
**Action:** Replace in place — no additional bullet

**Remove:**
```
- **Strip obvious explanations from rule text**: include only the non-obvious directive; omit common-knowledge consequences. "Use `git fetch origin && git merge origin/main` when review comments exist" is enough — don't append "this creates a merge commit without rewriting history."
```

**Add:**
```
- **Minimum viable rule text**: write the fewest characters that still convey the rule without losing specificity. One line is the target; a second line is only justified for a non-obvious "why." `cd dir && cmd` (skips cmd if cd fails), not `cd dir; cmd`, beats a paragraph on shell exit semantics.
```

**Also:** bump `metadata.version` from `"0.7"` to `"0.8"` in the same edit.

### Rationale

- "Minimum viable rule text" names brevity as the goal, not a side effect of stripping obvious bits
- "without losing specificity" reconciles tension with the sibling "Prefer specificity" guideline — the two bullets are compatible (be specific *and* brief)
- "One line is the target; a second line only for non-obvious why" gives a concrete, testable default
- The `cd &&` vs `cd ;` example is universal (no tool-specific context required) and reads cold
- Replace-in-place matches the skill's own NEVER: "NEVER add a new config rule when an existing rule just needs stronger wording"
- The new bullet is ~45 words — borderline by its own standard; the single-line example earns the second sentence

## Files to Modify

| File | Change |
|------|--------|
| `skills/learn/SKILL.md` | Replace final `## Guidelines` bullet; bump `metadata.version` to `"0.8"` |
| `cspell.config.yaml` | Add any new unknown words flagged by cspell (if any) |

## Branch

`docs/minimum-viable-rule-text`

## Verification

1. `rg "Strip obvious explanations" skills/learn/SKILL.md` → no matches
2. `rg "Minimum viable rule text" skills/learn/SKILL.md` → exactly one match
3. `## Guidelines` bullet count unchanged (3)
4. `metadata.version: "0.8"` in frontmatter
5. `npx cspell skills/learn/SKILL.md` — `parentheticals` added to `cspell.config.yaml`
6. `uv run --with pytest pytest tests/` — no regressions

## Shipping

1. Commit on branch `docs/minimum-viable-rule-text`
2. Push and open PR; run `/pr-comments` after PR is created per project convention
3. Squash-merge, delete branch, sync local main

## Downstream Follow-up (separate PR, after upstream merges)

In `application-tracker`:
1. Branch `chore/sync-learn-skill` from main
2. `npx skills add -y whatifwedigdeeper/agent-skills`
3. Inspect diff — `npx skills add` is repo-wide; confirm changes limited to `.agents/skills/learn/SKILL.md` + `skills-lock.json`. If unrelated skills drift, decide whether to broaden the PR or pin learn alone.
4. Commit, push, PR, merge

## Risks

- `npx skills add` resync scope is repo-wide, not learn-only — always diff before committing downstream
