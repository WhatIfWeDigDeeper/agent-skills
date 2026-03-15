# js-deps Eval Notes

## Known Limitations

### No real JS project in this repo

The `agent-skills` repo has no application-level `package.json` — only test fixtures under `tests/js-deps/fixtures/`, which have intentionally pinned versions and should never be updated. This affects several evals:

- **Evals 3, 4** (update workflows): The agents correctly refuse to modify the fixtures and narrate what they *would* do. Assertions pass based on the planned workflow rather than actual execution.
- **Eval 1, 5** (audit workflows): `npm audit` runs but finds 0 vulnerabilities because the fixture lockfiles are stubs. Severity filtering and fix logic can't be exercised end-to-end.

For more discriminating evals, point the agents at a separate fixture repo with a real `package.json`, pinned older dependencies, and known vulnerabilities. The assertions would then verify actual file changes and git commits rather than narrated plans.

### Worktree sandbox restriction (eval 1)

`git worktree add ../branch-name` requires write access to the project's parent directory, which is outside the default sandbox allowlist. Agents that follow the skill strictly will hit this and surface the skill's sandbox guidance rather than proceeding. This causes eval 1 assertions about worktree creation to fail even when the skill logic is correct.

Workaround: agents can use `/private/tmp/` as the worktree destination (eval 4 did this successfully). The skill already documents this fallback.

### AskUserQuestion unavailable to subagents (eval 2)

The `AskUserQuestion` tool is not available in subagent eval runs. Eval 2 (--help flow) checks whether the skill attempts to invoke it — the skill correctly reaches that step, but the tool call fails. The assertion is reframed in `evals.json` to check for the *attempt* rather than successful execution.
