# Spec 13: pr-comments — Auto Mode as Default (v1.16)

## Problem

Auto mode (`--auto`) is the right choice for nearly every invocation of `pr-comments`. The manual confirmation gate (Step 7 `[y/N/auto]` prompt) adds friction without adding safety — security screening, oversized-comment guards, and consistency checks already force a manual pause when needed. Users frequently type `--auto` explicitly, and CLAUDE.md instructs agents to use `--auto` when re-invoking the skill automatically.

Flipping the default eliminates the routine confirmation prompt while keeping `--manual` as an explicit opt-in for users who want to review the plan before each iteration.

Current baseline: v1.15, SKILL.md is 458 lines.

---

## Design

### Argument Parsing Changes

**Old parsing logic (phase 1):**
- `auto = False` by default
- `--auto [N]` sets `auto = True`, optionally sets `max_iterations = N`

**New parsing logic (phase 1):**
- `auto = True` by default (max_iterations = 10)
- `--manual` sets `auto = False` (restores confirmation gate)
- `--auto [N]` still accepted for backward compatibility and to set the cap: sets `auto = True` (already default) + `max_iterations = N`
- A bare positive integer is still the PR number (unchanged)

**One-shot mode (documentation terminology only):** `/pr-comments --auto 1` — one iteration, no looping. "One-shot" is a description of this mode, not an accepted argument token. Document it in the Arguments section with the concrete flag syntax only.

### Updated Invocation Examples

| Invocation | Mode | Iterations |
|---|---|---|
| `/pr-comments` | auto | 10 |
| `/pr-comments 42` | auto | 10 |
| `/pr-comments --auto 5` | auto | 5 |
| `/pr-comments --auto 1` | auto | 1 (one-shot, no looping) |
| `/pr-comments --manual` | manual | n/a |
| `/pr-comments --manual 42` | manual | n/a |
| `/pr-comments 42 --manual` | manual | n/a |
| `/pr-comments --auto 5 42` | auto | 5 |

### Files to Change

#### `skills/pr-comments/SKILL.md`

1. **Arguments section** — Rewrite to:
   - State auto mode is the default
   - Document `--manual` flag restores the confirmation gate
   - Document `--auto [N]` is still accepted for setting the iteration cap (or for backward compat)
   - Update examples table
   - Remove the old anti-pattern note from CLAUDE.md (move fix to that file too)

2. **Step 7** — Invert condition:
   - Old: "If `--auto [N]` was passed, skip confirmation..."
   - New: "Skip confirmation unless `--manual` was passed. If `--manual` was passed, show the `[y/N/auto]` gate. If the user responds `auto`, switch to auto mode for remaining iterations."

3. **Step 7 — `auto` response** — Still valid mid-session switch from manual → auto. Wording stays, just context flips.

#### `skills/pr-comments/references/bot-polling.md`

- Update all "Auto-mode:" / "Manual mode:" dual-descriptions to reflect the new default
- Step 6c all-skip repoll: manual mode now requires explicit `--manual` to see the `[y/N]` prompt; default auto-enters polling

#### `tests/pr-comments/conftest.py`

- `parse_auto_flag()`: flip default from `{"auto": False, ...}` to `{"auto": True, ...}`
- Add `--manual` token detection: when found, set `auto = False`, remove from remaining_args
- Update docstring

#### `tests/pr-comments/test_pr_argument_parsing.py`

- Update `TestAutoFlagParsing` class: default case now expects `auto=True`
- Add `TestManualFlagParsing` class mirroring auto tests
- Update `TestCombinedAutoAndPRNumberParsing` default expectations

#### `CLAUDE.md`

- Line ~93: Update git workflow rule — drop the `--auto` guidance since it's now the default; the manual-mode branch becomes "`--manual` if the session is in manual mode"
- Add note about `--manual` override

#### `README.md`

- Update skill description and trigger examples to reflect auto-default
- Update Skill Notes section

### Version Bump

v1.15 → v1.16 (behavioral change to default mode)

---

## Verification

1. Run `uv run --with pytest pytest tests/pr-comments/` — all tests pass with updated expectations
2. Invoke `/pr-comments` (no flags) on a branch with an open PR → confirm no confirmation gate appears, auto-loop runs
3. Invoke `/pr-comments --manual` → confirm `[y/N/auto]` gate appears at Step 7
4. Invoke `/pr-comments --auto 1` → confirm runs exactly one iteration then exits
5. Invoke `/pr-comments --auto 5 42` → confirm targets PR #42, caps at 5 iterations
6. Run `npx cspell skills/pr-comments/SKILL.md` — no unknown words
7. Run affected pr-comments evals (minimum: eval 20 consistency, eval 22 early-poll, eval 23 all-skip repoll — the three that test auto-mode-specific branching); update `evals/pr-comments/benchmark.json` with results
8. Sync `README.md` Eval Δ column after benchmark update

**Eval scope note:** Run the targeted subset (evals 20, 22, 23) rather than the full suite — these are the evals that exercise auto-vs-manual branching. Other evals test comment classification and thread routing, which this spec does not change.
