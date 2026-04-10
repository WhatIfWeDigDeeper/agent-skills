# Spec 21: peer-review — Portable Default Model (`self`) (v1.5 → v1.6)

## Problem

The peer-review skill hardcodes `claude-opus-4-6` as the default `--model` value in four places (find `(default: claude-opus-4-6)` in the help text, `Set model to claude-opus-4-6` in Step 1, `If \`model\` starts with \`claude-\`` in Step 4, and `For Claude models, use a \`claude-*\` prefix` in the Step 4 error). This creates two problems:

1. **Portability**: if a non-Claude assistant (Copilot, Gemini, Codex) invokes this skill, the default tells it to spawn a Claude subagent it can't access. The skill is meant to be assistant-neutral per the repo's portability guidelines.
2. **Staleness**: the hardcoded model ID goes stale as Claude releases new models. Every model bump requires a manual find-and-replace.

Current baseline: v1.5, SKILL.md 434 lines. Eval pass rate: 97% with-skill, 68% without-skill, +29% delta. 23 evals, 91 unit tests (all passing).

## Design

### Core Concept: `self` as Default

Replace the hardcoded `claude-opus-4-6` default with the keyword `self`, meaning "use yourself as the reviewer." Every assistant knows what it is and can spawn a fresh instance of itself.

- **Claude** invoking the skill → spawns a Claude subagent (same as today, but no hardcoded model ID)
- **Copilot** invoking the skill → spawns itself via `copilot -p ...`
- **Gemini** invoking the skill → spawns itself via `gemini -p ...`
- `--model copilot` from Claude → still routes to the copilot CLI (external routing unchanged)

`self` is the default when `--model` is not provided. Users can also pass `--model self` explicitly (no-op, same as omitting it).

### Routing Logic Change

Current condition (Step 4):
> If `model` starts with `claude-` → Claude path; otherwise → external CLI path

New condition:
> If `model` is `self` → **self path** (the assistant uses its own reviewer mechanism — in Claude Code this means spawning a subagent); if `model` starts with `claude-` → Claude path (explicit Claude model override); otherwise → external CLI path (copilot/codex/gemini)

The self path and the Claude path share identical behavior today — the only difference is that `self` doesn't name a specific model. For Claude, "self" *is* the Claude path. For a non-Claude assistant, "self" would mean using whatever subagent/subprocess mechanism that assistant supports. The skill can't prescribe exactly how — it just says "spawn a fresh instance of yourself."

### Header Display

Current: `## Peer Review — [target] ([model])`
Example: `## Peer Review — staged (claude-opus-4-6)`

New behavior:
- When model is `self` → show the assistant's own name/identifier (e.g. `claude-opus-4-6`, `copilot`, `gemini`) — the assistant substitutes its own identity
- When model is explicit → show the explicit value as before

Instruction: "If `model` is `self`, substitute your own model name or identifier in the header."

### Help Text Update

```
Options:
  --model MODEL     Reviewer model (default: self — use the current assistant)
                    Explicit Claude models: any claude-* value
                    External CLIs: copilot[:submodel], codex[:submodel], gemini[:submodel]
                      copilot — npm install -g @github/copilot-cli (or VS Code extension)
                      codex   — npm install -g @openai/codex
                      gemini  — npm install -g @google/gemini-cli
```

The three install-hint lines under "External CLIs" are retained unchanged — only the first line of the `--model` block changes.

### Error Message Update

The unsupported `--model` error (find `For Claude models, use a \`claude-*\` prefix` in Step 4) currently says:
> "For Claude models, use a `claude-*` prefix (e.g. `--model claude-opus-4-6`)."

Update to:
> "Supported values: self (default), claude-* (explicit Claude model), copilot, codex, gemini."

### What Does NOT Change

- The external CLI path (copilot/codex/gemini routing, triage layer, severity normalization) — unchanged
- The review prompt templates — unchanged
- The apply/re-scan workflow — unchanged
- The consistency-mode re-scan rationale note (already added) — unchanged
- Unit test logic for argument parsing, mode routing, triage — unchanged (these don't test the default model value)

## Impact

| Area | Change |
|------|--------|
| Help text (find `(default: claude-opus-4-6)`) | `(default: claude-opus-4-6)` → `(default: self — use the current assistant)` |
| Step 1 (find `Set model to claude-opus-4-6`) | `Set model to claude-opus-4-6` → `Set model to self`; also remove or replace the follow-on sentence "Opus is the default reviewer because review quality matters more than cost..." with a model-neutral rationale |
| Step 4 condition (find `If \`model\` starts with \`claude-\``) | add `self` alongside `claude-*` for the Claude/self path; also remove the parenthetical `(including the default claude-opus-4-6)` from the condition heading |
| Step 4 error (find `For Claude models, use a \`claude-*\` prefix`) | update supported values list |
| SKILL.md Step 5 | Header instruction: add "if model is self, substitute your own name" |
| Notes "Multi-LLM routing" (find `rather than spawning a Claude subagent`) | update to `rather than using the self path (spawning a fresh reviewer instance)` |
| evals.json eval 12 | `expected_output` mentions `(claude-opus-4-6)` in header — update to reflect self-substitution |
| benchmark.json eval 12 | Evidence strings reference `(claude-opus-4-6)` — will need re-run or text update |
| README.md | No change needed (doesn't mention the default model) |

## Eval Impact

- **Eval 12** (pr-target-context): `expected_output` hardcodes `(claude-opus-4-6)` in the header. Update to note the assistant substitutes its own identifier.
- **No other evals** assert on the model name in the header.
- **No new evals needed** for the `self` keyword itself — the behavior is identical to today for Claude users. A new eval could test `--model self` as an explicit argument, but it's a no-op and low value.
- Existing discriminating evals are unaffected — none depend on the hardcoded model name for their pass/fail logic.

## Line Count Impact

Estimated net change: +2 to +5 lines (slightly longer help text and routing condition). Well within the 500-line guideline.
