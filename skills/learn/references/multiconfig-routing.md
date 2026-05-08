# Multi-Config Routing

Loaded when Step 1 of `SKILL.md` detects more than one assistant config in the
project. Decides whether the skill can auto-skip the per-config selection
prompt, or must fall through to it.

## Scope

Steps 1a and 1b apply only to the Step 4 Markdown scope: `CLAUDE.md`,
`GEMINI.md`, `AGENTS.md`, `.github/copilot-instructions.md`, `.cursorrules`,
`.windsurf/rules/rules.md`. Non-Markdown configs (`.continuerc.json`,
`.cursor/rules/*.mdc`) are excluded from auto-skip evaluation entirely. When
auto-skip fires, any non-Markdown configs detected on the same project still
go through Step 1c's prompt.

## Step 1a — Mirror-rule detection

`rg -i` (case-insensitive) each detected Markdown config for the Step 4
mirror-rule patterns (`keep .* in sync`, `mirror .* to`,
`apply the equivalent change to`). For each match, record both the matching
line and a `±5`-line window around it. A mirror-rule **names another detected
Markdown config** when that other config's filename (e.g. `CLAUDE.md`,
`.github/copilot-instructions.md`) appears anywhere in that window — filename
matching is also case-insensitive. Record, per detected Markdown config, the
set of other detected Markdown configs it names; require that set to be
non-empty for the auto-skip check.

## Step 1b — Reciprocal "always both" auto-skip

Within the same `±5`-line window of each detected mirror-rule, search
(case-insensitive) for unambiguous fan-out intent using:

```
(always (update|apply) (to )?both|apply to both|without asking|do not prompt)
```

Auto-skip fires only when **both** of the following hold:

1. Every detected Markdown config has a mirror-rule whose `±5`-line window
   names at least one other detected Markdown config (Step 1a) **and**
   contains an "always both" phrase within that same window.
2. The "names" relationships form a **single connected component** spanning
   every detected Markdown config — treat each detected Markdown config as a
   node and add an undirected edge between A and B whenever A's window names
   B or B's window names A. If the resulting graph splits into two or more
   components (e.g. `{CLAUDE.md ↔ .github/copilot-instructions.md}` and
   `{AGENTS.md ↔ GEMINI.md}` with no cross-naming), `all` is not implied —
   fall through to Step 1c.

When the condition holds, print a one-line notice on its own line and proceed
as if the user had answered `all` for the eligible Markdown configs only:

```
Detected reciprocal "always both" rule across <config1> and <config2> — applying to all eligible Markdown configs without prompting.
```

Any non-Markdown configs detected on the same project (`.continuerc.json`,
`.cursor/rules/*.mdc`) still go through Step 1c's prompt path per the Scope
section. Any miss, one-sided declaration, mirror-rule that names no other
detected config, disconnected components, or weaker wording (e.g.
`consider mirroring`, `may want to mirror`) → keep the prompt behavior in
Step 1c.

## Step 1c — Prompt

When the auto-skip condition is not met, stop and ask:

```
Found multiple config files:
1. CLAUDE.md (142 lines)
2. .github/copilot-instructions.md (38 lines)

Which should I update? (enter number, or "all")
```

If one config contains a mirror-rule naming another (from Step 1a) without
the "always both" phrase, surface that in the prompt as informational context
— but the user's answer always binds, regardless of any partial mirror-rule
signal. If the user later expresses a narrower scope at the Step 5
confirmation, that also binds.
