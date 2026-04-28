=== SUMMARY ===
EVAL: 8 concurrency-state
CONFIG: without_skill (opus)

TOOLS_USED: Read: 0, Bash: 2, Write: 1, Other: none

GH_EDIT_COMMAND: gh pr edit 89 --body-file "$BODY_FILE"

FINAL_PR_BODY (verbatim):
<<<BODY
Adds a background job processor using worker threads.

---

## Review Guide

This PR introduces a background job processor that spawns worker threads to handle queued jobs. Below are the areas where reviewer judgment is most valuable.

### Concurrency & shared state

The processor maintains two pieces of shared mutable state — `activeJobCount` and `jobQueue` — that are mutated from both the calling thread (via `enqueueJob`) and from worker `exit` handlers. A few things worth a careful look:

- **`activeJobCount` accounting looks off.** It is incremented in `enqueueJob` (when a job is pushed onto the queue) and decremented in the worker's `exit` handler. But `processNext` does not increment when it actually starts a worker, and the counter currently represents "enqueued + running" rather than "running". If callers rely on `getActiveJobCount()` to reflect in-flight work, the semantics may not match the name. Worth confirming the intended definition.
- **No concurrency cap.** Every call to `enqueueJob` triggers a `processNext`, which spawns a worker immediately if the queue is non-empty. There is no max-parallelism guard, so a burst of `enqueueJob` calls will spawn N workers in parallel. Is that intentional, or should there be a worker pool / max-concurrency limit?
- **Race on `jobQueue.shift()`?** Node.js is single-threaded for JS execution on the main thread, so the array mutations themselves are safe, but the re-entrant `processNext` calls (one per worker `exit`) are worth tracing to confirm there is no scenario where two `exit` events fire near-simultaneously and both observe a non-empty queue but only one job exists. (In practice, with the event loop this should be fine — flagging for confirmation.)

### Error handling & worker lifecycle

- **No `error` handler on the worker.** Only `exit` is wired up. If the worker throws an uncaught exception, the process may crash or the job may be silently dropped. Consider `worker.on('error', ...)` and deciding on retry vs. dead-letter behavior.
- **Non-zero exit codes are not distinguished.** `exit` fires for both clean and crashed workers. The active-job counter decrements either way, but failed jobs are not surfaced anywhere.
- **No backpressure / queue bound.** `jobQueue` can grow without limit. Worth deciding whether the producer should be throttled.

### Module shape & testability

- **Module-level mutable state.** `activeJobCount` and `jobQueue` are module-scoped, which makes the processor effectively a singleton and harder to unit-test in isolation. Consider whether a class or factory function would be preferable.
- **Hardcoded worker script path.** `'./worker-script.js'` is resolved relative to the current working directory, not the module file. This will break depending on where the process is started from. Consider `new URL('./worker-script.js', import.meta.url)` or a configurable path.
- **`isMainThread` is imported but unused.** Either remove the import or add the guard if this file is intended to also run inside the worker.
- **Missing `Job` type.** The file references `Job` but does not import or define it — the build will fail unless it is defined elsewhere and picked up via ambient types. Worth confirming.

### Suggested reviewer focus

1. Confirm the intended semantics of `getActiveJobCount()` and fix the counter to match.
2. Decide on a max-concurrency policy.
3. Add `error` handling and decide on retry behavior.
4. Resolve the `Job` type import and the worker script path.

BODY>>>

NOTES: Baseline run with no skill access. Diff shows new worker_threads-based job processor with module-level mutable state, no concurrency cap, no error handler, miscounted activeJobCount, and a relative worker script path. Guide focuses on concurrency/state, error handling, and module shape — areas where reviewer judgment matters most. GH command not executed per simulation instructions; written as it would be invoked with the body passed via a file to avoid shell quoting issues.
=== END SUMMARY ===
