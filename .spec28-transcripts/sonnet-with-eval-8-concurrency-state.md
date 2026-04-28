=== SUMMARY ===
EVAL: 8 concurrency-state
CONFIG: with_skill (sonnet)

TOOLS_USED: Read: 2, Bash: 3, Write: 1, Other: none

GH_EDIT_COMMAND:
gh pr edit 89 --body-file "$TMPFILE"

FINAL_PR_BODY (verbatim):
<<<BODY
Adds a background job processor using worker threads.

<!-- pr-human-guide -->
## Review Guide

> Areas identified by automated analysis as needing human judgment.
> This is not a complete review checklist — it highlights where your attention matters most.

### Concurrency / State
- [ ] [`src/workers/job-processor.ts` (L3-22)](https://github.com/owner/repo/pull/89/files#diff-8a871a3707d1f8569ae5b27b05dbf47bd9fb58a51c58749f573b8495293a902c) — Module-level mutable state (`activeJobCount`, `jobQueue`) written from `enqueueJob` and from the worker `exit` callback with no lock; `enqueueJob` increments the counter and calls `processNext` non-atomically, and the `exit` handler races with new enqueues against the shared queue

### Novel Patterns
- [ ] [`src/workers/job-processor.ts`](https://github.com/owner/repo/pull/89/files#diff-8a871a3707d1f8569ae5b27b05dbf47bd9fb58a51c58749f573b8495293a902c) — First use of `worker_threads` in this codebase; new `src/workers/` directory has no sibling files to compare conventions against, so the queue + worker pattern is novel by default

<!-- /pr-human-guide -->
BODY>>>

NOTES: Simulated PR — no gh commands executed. SHA-256 anchor for `src/workers/job-processor.ts` = 8a871a3707d1f8569ae5b27b05dbf47bd9fb58a51c58749f573b8495293a902c. Two categories flagged: Concurrency/State (shared mutable state + worker threads with no synchronization) and Novel Patterns (first worker_threads use, new directory with no siblings — per skill guidance for new directories without conventions). Security/Config/Dependencies/Data-Model categories not applicable. Body assembled by appending the guide to the existing one-line description with a blank-line separator (no existing marker block to replace).
=== END SUMMARY ===
