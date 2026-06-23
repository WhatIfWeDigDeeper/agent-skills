# Argument Parsing

Full precedence, stickiness, and validation rules for `$ARGUMENTS`. The SKILL.md Arguments section keeps the invocation table; this file is the authoritative parse procedure. Parse and validate **before any shell call**.

## Parse order

1. **Strip the mode/cap tokens first.** Remove `--manual`, `--auto [N]`, and `--max N` from `$ARGUMENTS`. The token immediately following `--max` is consumed as its value unless that token is itself another `--` flag — so an invalid value such as `--max +10` is rejected by validation below rather than leaking through as a PR-number candidate. `--auto`'s value is optional and consumed only when the next token is all digits. Do **not** regex-check the whole `$ARGUMENTS` string or just its first token; the PR-number validation applies only to what remains after this strip.
2. **Validate the remaining PR-number token, if any.** Strip a single leading `#` (so `42` and `#42` both work) and require the cleaned value to match `^[1-9][0-9]{0,5}$`. If a token is present and does not match — **including a numeric-looking-but-invalid value** like `0`, `01`, or a 7+-digit string — hard-stop with `Invalid PR number: <value>. Must be a positive integer.` rather than falling through to branch detection. If no PR-number token remains, detect from the current branch.
3. **Validate the cap value (auto mode only).** In auto mode the cleaned `--max N` (or backward-compatible `--auto N`) value must match `^[1-9][0-9]{0,3}$` (1–9999, well above any realistic loop cap) or stop with `Invalid --max value: <value>. Must be a positive integer.` In `--manual` mode the supplied `--max` / `--auto N` value is discarded without use (manual mode has no auto-loop to cap), so it is neither validated nor an error — it never reaches a shell call or a loop bound.

## Mode and cap semantics

- **Auto mode is the default.** The Step 7 confirmation prompt and the Step 13 push/re-request prompt are skipped — the plan table is still shown each iteration for observability, but no user approval is required.
- **`--manual`** restores the confirmation gates (Step 7 before applying changes, Step 13 before pushing/re-requesting). `--manual` is **sticky**: once it appears anywhere in the arguments the whole invocation is manual regardless of token order, and a later `--auto` does not flip it back.
- **`--max N`** sets the maximum bot-review loop iterations (default 10). Ignored when `--manual` is present.
- **`--auto`** alone is a no-op alias retained only for legacy callers (auto is already the default); per the stickiness rule it never overrides `--manual`. **`--auto N`** (with a number) is treated as `--max N` for backward compatibility, likewise ignored under `--manual`; emit a deprecation note in auto mode: "`--auto N` is deprecated; use `--max N`".

## `--auto` + PR-number disambiguation

`--auto`'s value is consumed only when the next token is all digits — and because a bare PR number is also all digits, `--auto 42` is ambiguous and read as `--max 42`, leaving no PR-number token. To pair `--auto` with an explicit PR number:

- `/pr-comments 42 --auto` — put the number before `--auto`.
- `/pr-comments --auto #42` — keep the `#` prefix so the token is not all digits.
- `/pr-comments --max 10 42` — use `--max N` instead, with the PR number after the value.
