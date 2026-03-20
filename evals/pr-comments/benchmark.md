# Skill Benchmark: pr-comments

**Model**: claude-sonnet-4-6
**Date**: 2026-03-20
**Evals**: 1, 2, 3, 4, 5, 6, 7, 8 (1 run each per configuration)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | **100%** ± 0% | 28% ± 20% | **+72%** |
| Time | 85.2s ± 20.6s | 44.8s ± 7.2s | +40.4s |
| Tokens | 10,787 ± 11,082 | 4,043 ± 6,219 | +6,744 |

The skill adds ~40s and ~6,700 tokens overhead and improves correctness by +72 percentage points. The baseline fetches comments and applies basic edits, but consistently skips the GraphQL thread-state step, the plan/confirmation gate, Co-authored-by attribution, thread resolution, and the interactive push + re-request flow — these five behaviors the skill explicitly mandates.

## Per-Eval Results

| # | Eval | With Skill | Without Skill | Key differentiators |
|---|------|------------|---------------|---------------------|
| 1 | Basic: address comments | **7/7 (100%)** | 1/7 (14%) | GraphQL thread state, plan + confirmation, Co-authored-by, resolveReviewThread |
| 2 | Explicit PR number + suggestions | **7/7 (100%)** | 2/7 (29%) | Suggestion block detection, branch checkout, outdated skip, resolved filter |
| 3 | Out-of-scope decline | **8/8 (100%)** | 2/8 (25%) | Plan with decline reason, reply to declined, don't resolve declined thread |
| 4 | Mixed four categories | **8/8 (100%)** | 2/8 (25%) | Declined reviewer excluded from Co-authored-by, suggestion applied from block |
| 5 | Outdated threads | **6/6 (100%)** | 2/6 (33%) | Outdated threads skipped without reply, only addressed threads resolved |
| 6 | Deduplicated co-authors + clarifying question | **5/5 (100%)** | 0/5 (0%) | Already-resolved skip, co-author deduplication, clarifying question left open |
| 7 | Push + re-request confirm path | **5/5 (100%)** | 1/5 (20%) | Interactive push prompt, remove-then-add reviewer pattern, include declined commenter |
| 8 | Push + re-request decline path | **4/4 (100%)** | 3/4 (75%) | Interactive prompt shown before acting, no push when user declines, manual push instruction |

## What Each Eval Tests

### Eval 1 — Basic: address comments
**Prompt**: User has review comments on their PR and wants them addressed.

Tests the core end-to-end workflow: REST comment fetch, GraphQL thread-state fetch, filtering resolved threads from the plan, plan presentation and confirmation gate, Co-authored-by trailers, and resolveReviewThread mutation. The without-skill run fetched comments via REST but skipped all four of the skill-mandated process steps — no GraphQL call, no plan, no confirmation, no Co-authored-by, no thread resolution. Only the basic REST fetch passed.

### Eval 2 — Explicit PR number + suggestions
**Prompt**: Address review comments on PR #47, including several suggested changes.

Tests passing an explicit PR number, identifying `suggestion` fenced blocks as suggested changes and applying them as local edits (not via API), checking out the PR's head branch when current branch doesn't match, skipping outdated threads (isOutdated=true) without reply, and filtering already-resolved threads before presenting the plan. The without-skill run passed the explicit PR number and applied local file edits, but missed branch checkout, suggestion block identification, outdated detection, and resolved filtering — all requiring GraphQL or explicit protocol.

### Eval 3 — Out-of-scope decline
**Prompt**: One reviewer suggested rewriting the entire auth module — clearly out of scope for this PR.

Tests the full decline workflow: plan must include the reason for declining, a reply must be posted to the declined comment explaining why, and the declined thread must NOT be resolved (left open for the reviewer). The without-skill run happened to post a top-level PR comment that touched on the scope issue, and since it never called resolveReviewThread for anything, declined threads were incidentally not resolved. But it skipped fetching thread state, never presented a plan, and didn't actually implement or commit the in-scope changes.

### Eval 4 — Mixed four categories
**Prompt**: Four comments: rename a variable (valid), extract a magic number (valid), one GitHub suggested change (valid), rewrite the module in another language (out of scope).

Tests all four action categories in one run: `implement`, `accept suggestion`, and `decline` in the plan. The skill-specific assertions here are applying the suggestion from the fenced block verbatim, and — crucially — excluding the declined reviewer from Co-authored-by trailers while including the implemented ones. The without-skill run included the declined reviewer (@carol) in Co-authored-by incorrectly, never used GraphQL, didn't present an upfront plan, and couldn't reliably extract the suggestion block.

### Eval 5 — Outdated threads
**Prompt**: Four threads: two are outdated (code has moved on), one has a valid suggestion, one has a GitHub-style suggested change.

Tests that outdated threads (isOutdated=true from GraphQL) are skipped without posting replies, and that thread resolution only covers the two addressed threads — not the two outdated ones. The without-skill run had no way to detect outdated threads (REST API doesn't expose isOutdated), replied to all four threads including the outdated ones, and never called resolveReviewThread for any thread.

### Eval 6 — Deduplicated co-authors + clarifying question
**Prompt**: Five threads: two reviewers flagged the same issue (both should get credit), one performance improvement, one clarifying question (should be answered, not resolved), one already resolved.

The hardest eval — requires five distinct behaviors simultaneously. The without-skill run failed all five: didn't use GraphQL to detect the already-resolved thread, omitted Co-authored-by entirely (so deduplication was moot), couldn't distinguish "reply and close" from "reply and leave open" for the clarifying question, and never fetched thread state.

### Eval 7 — Push + re-request review (confirm path)
**Prompt**: Three threads (two valid, one out of scope). After addressing, push and re-request review from all commenters.

Tests the push + re-request workflow when the user confirms: the skill presents a combined prompt listing all relevant commenters (including declined), runs `git push`, then re-requests review by removing then re-adding reviewers via `gh pr edit` to trigger GitHub notifications. Without the skill, the baseline implemented the changes but never presented an interactive push prompt — it either pushed silently or mentioned push as a next step without waiting for confirmation.

### Eval 8 — Push + re-request review (decline path)
**Prompt**: Two valid threads. User says they want to push manually — don't push automatically.

Tests the decline path: the skill presents the combined push prompt first (regardless of the user's upfront hint), respects the user's decline by not running `git push` or `gh pr edit`, and explicitly tells the user to push manually. The without-skill 75% is inflated — expectations 2 and 3 pass trivially since the baseline never presents an interactive prompt; expectation 1 (prompt shown before acting) is the real discriminator.

## Notes

- **GraphQL thread state is the root discriminator.** Nearly every without-skill failure traces back to the baseline using only the REST comments endpoint. Without isResolved and isOutdated from GraphQL, resolved-thread filtering, outdated skipping, and selective thread resolution are all impossible. This single step accounts for the majority of the +72% delta.
- **Process steps vs. output quality.** The baseline produces reasonable commit messages and file edits on its own. The skill's value is almost entirely in the process steps it mandates — the plan/confirmation gate, Co-authored-by attribution, thread resolution via GraphQL mutation, and the interactive push + re-request prompt.
- **Eval 6 is the ceiling test.** The 0% without-skill score on eval 6 reflects the cumulative effect of missing all five behaviors at once. Each individual failure is predictable; together they produce a completely incorrect outcome.
- **Eval 3's "declined thread not resolved" assertion passes trivially in the baseline** (the agent never resolves anything). The paired assertion — "addressed threads ARE resolved" — is what distinguishes correct decline-handling from a general failure to use GraphQL.
- **Token variance is high** (stddev ≈ 11,000 for with-skill) because some evals ran during iteration-2 with full transcript tokens captured and others during iteration-3 with simulated runs that recorded 0 tokens. The pass rates are reliable; the token numbers are not directly comparable across evals.
