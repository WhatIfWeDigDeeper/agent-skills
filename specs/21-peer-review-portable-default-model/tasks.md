# Spec 21: Tasks — Portable Default Model (`self`)

## Phase 1: SKILL.md Updates

- [x] **1.1** Update help text (find `(default: claude-opus-4-6)`) → `(default: self — use the current assistant)`. Add a line explaining that `self` means the assistant uses its own reviewer mechanism.
- [x] **1.2** Update Step 1 (find `Set model to claude-opus-4-6 if not overridden`) → `Set model to self if not overridden`. Also remove or replace the follow-on sentence "Opus is the default reviewer because review quality matters more than cost — a cheaper model might miss real issues." with a model-neutral rationale (e.g. "A fresh reviewer instance avoids accumulated session assumptions.").
- [x] **1.3** Update Step 4 routing condition (find `If model starts with claude-`) → `If model is self or starts with claude-`. Also remove the parenthetical `(including the default claude-opus-4-6)` from the condition heading. Add a sentence: "When model is `self`, the assistant spawns a fresh instance of itself as the reviewer. In Claude Code, this means spawning a subagent. Other assistants use their own subprocess mechanism."
- [x] **1.4** Update Step 4 error message (find `For Claude models, use a claude-* prefix`) → `Supported values: self (default), claude-* (explicit Claude model), copilot, codex, gemini.`
- [x] **1.5a** Update Notes bullet "Multi-LLM routing" (find `rather than spawning a Claude subagent`) → `rather than using the self path (spawning a fresh reviewer instance)` — assistant-neutral wording.
- [x] **1.5** Update Step 5 header instruction (find `## Peer Review — [target] ([model])`) → add: "If `model` is `self`, substitute your own model name or identifier in the header (e.g. a Claude assistant would display `claude-opus-4-6`, Copilot would display `copilot`)."
- [x] **1.6** Bump version in frontmatter: `"1.5"` → `"1.6"`.

## Phase 2: Eval & Benchmark Updates

- [x] **2.1** Update evals.json eval 12 `expected_output`: replace the hardcoded `(claude-opus-4-6)` header example with assistant-neutral language (e.g. "the header shows the assistant's own model identifier").
- [x] **2.2** Update benchmark.json eval 12 evidence strings that reference `(claude-opus-4-6)` — text-only update, no re-run needed since the assertion doesn't test the model name.
- [x] **2.3** Update `metadata.skill_version` in benchmark.json to `"1.6"`.

## Phase 3: Verification

- [x] **3.1** Run `uv run --with pytest pytest tests/peer-review/ -v` — all tests should still pass (no test logic depends on the default model value).
- [x] **3.2** Run `npx cspell skills/peer-review/SKILL.md` — check for any new unknown words.
- [x] **3.3** Re-read SKILL.md end-to-end and verify no remaining hardcoded `claude-opus-4-6` references exist anywhere in SKILL.md.
