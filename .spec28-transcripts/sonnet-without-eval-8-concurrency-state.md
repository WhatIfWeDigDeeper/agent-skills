=== SUMMARY ===
EVAL: 8 concurrency-state
CONFIG: without_skill (sonnet)

TOOLS_USED: Read: 1, Bash: 2, Write: 0, Other: none

GH_EDIT_COMMAND: did not run

FINAL_PR_BODY (verbatim):
<<<BODY
Adds a background job processor using worker threads.

---

## Review Guide

### Concurrency / State
- **Module-level mutable state**: `activeJobCount` and `jobQueue` are declared at module scope. If this module is imported by multiple callers or used in a multi-threaded context, there is no synchronization — concurrent `enqueueJob` calls can race on both `jobQueue.push` and `activeJobCount++`. Verify that this module is only ever used from a single thread/context, or add explicit locking.
- **Counter correctness**: `activeJobCount` is incremented in `enqueueJob` but decremented in the worker's `'exit'` event. If a worker exits with a non-zero code (error), the counter still decrements — which is probably fine — but there is no distinction between successful and failed jobs. Confirm whether callers need to know about failures separately.
- **Unbounded concurrency**: `processNext` spawns a new `Worker` for every job in the queue with no limit on how many workers can run simultaneously. A burst of enqueued jobs will spawn an equal number of OS threads. Consider adding a max-concurrency cap.

### Error Handling
- The `Worker` instance has no `'error'` event listener. If the worker script throws or crashes before emitting `'exit'`, the error is silently swallowed. Add a `worker.on('error', ...)` handler.
- There is no mechanism to signal job failure back to the caller of `enqueueJob`. Consider returning a `Promise` or accepting a callback.

### Resource Management
- No worker pool or reuse — each job creates and destroys an OS thread. For high-throughput scenarios, this may be a bottleneck.
- `worker-script.js` path is hardcoded as a relative string. Verify this resolves correctly at runtime regardless of the process working directory.
BODY>>>

NOTES: Identified concurrency/state issues (module-level mutable shared state, no synchronization, unbounded parallelism), missing error handling, and resource management concerns. No gh command executed — simulation only. Did not use HTML comment markers or structured checkbox format; produced a freeform markdown review guide instead.
=== END SUMMARY ===
