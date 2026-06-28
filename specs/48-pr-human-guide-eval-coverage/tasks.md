# Spec 48 — Tasks

> Execute top-to-bottom. Check off each `- [ ]` immediately on completion (do not
> batch). All eval prompts below are **verbatim authoritative content** — insert
> exactly. Build eval objects in a Python script and `json.dump` them so escaping
> is handled automatically; never hand-escape diffs into JSON.

---

## Task 1: Add evals 9–12 to `evals/pr-human-guide/evals.json`

**Files:** Modify `evals/pr-human-guide/evals.json`

Each eval object has fields `id`, `name`, `prompt`, `expected_output`,
`assertions` (list of `{id, text}`), matching evals 1–8. The `prompt` strings
below are shown as readable text — the script must store them with the real
newlines/diffs intact (a triple-quoted Python string + `json.dump` does this).

### Eval 9 — `sweeping-cross-cutting-refactor`

**prompt:**

```
Can you add a guide to PR #210's description so reviewers know where to focus? This one's a big sweep across the handlers.

PR #210 — 'Route all handler errors through centralized error middleware'
URL: https://github.com/owner/repo/pull/210
Current PR description: 'Replaces the inline 500-response in every route handler with next(err) so all errors flow through the new centralized error middleware. Touches 24 handler files; the transformation is identical in each.'

Three representative files are shown; the remaining 21 handlers follow the exact same change:

```diff
diff --git a/src/handlers/users.ts b/src/handlers/users.ts
index 1111111..2222222 100644
--- a/src/handlers/users.ts
+++ b/src/handlers/users.ts
@@ -14,9 +14,8 @@ export async function getUser(req, res, next) {
   try {
     const user = await db.users.findById(req.params.id);
     res.json(user);
-  } catch (err) {
-    console.error(err);
-    res.status(500).json({ error: 'Internal server error' });
+  } catch (err) {
+    next(err);
   }
 }
diff --git a/src/handlers/orders.ts b/src/handlers/orders.ts
index 3333333..4444444 100644
--- a/src/handlers/orders.ts
+++ b/src/handlers/orders.ts
@@ -22,9 +22,8 @@ export async function listOrders(req, res, next) {
   try {
     const orders = await db.orders.findByUser(req.user.id);
     res.json(orders);
-  } catch (err) {
-    console.error(err);
-    res.status(500).json({ error: 'Internal server error' });
+  } catch (err) {
+    next(err);
   }
 }
diff --git a/src/handlers/products.ts b/src/handlers/products.ts
index 5555555..6666666 100644
--- a/src/handlers/products.ts
+++ b/src/handlers/products.ts
@@ -18,9 +18,8 @@ export async function getProduct(req, res, next) {
   try {
     const product = await db.products.findById(req.params.id);
     res.json(product);
-  } catch (err) {
-    console.error(err);
-    res.status(500).json({ error: 'Internal server error' });
+  } catch (err) {
+    next(err);
   }
 }
```
```

**expected_output:** The agent should flag this as a single Novel Patterns
(sweeping cross-cutting refactor) item describing the aggregate transformation,
not one entry per file, and should name the behavior/contract delta (errors and
logging now produced by centralized middleware instead of each handler returning
its own 500). The guide is wrapped in the canonical markers and posted via
`gh pr edit`.

**assertions:**
- `flags-as-novel-pattern` — "The review guide flags this change under Novel Patterns (as a sweeping cross-cutting refactor / aggregate transformation)."
- `flags-aggregate-not-per-file` — "The review guide treats the refactor as a single aggregate item rather than creating a separate flagged entry for each of the 24 handler files."
- `notes-behavior-delta` — "The review guide identifies the runtime behavior/contract change (errors now routed through centralized middleware instead of each handler returning its own 500 response), not merely that many files changed."
- `uses-html-markers` — "The review guide is wrapped in <!-- pr-human-guide --> and <!-- /pr-human-guide --> markers."

### Eval 10 — `mechanical-rename-no-behavior-delta`

**prompt:**

```
Prep PR #214 for review — add a guide pointing reviewers at anything that needs careful judgment.

PR #214 — 'Rename internal helper computeTotal to calculateTotal'
URL: https://github.com/owner/repo/pull/214
Current PR description: 'Pure rename of the internal helper computeTotal to calculateTotal. No signature, behavior, or public-API change. The old name is exhaustively replaced across all 25 internal call sites.'

Representative slice (the rest are identical one-token substitutions):

```diff
diff --git a/src/billing/total.ts b/src/billing/total.ts
index aaaaaaa..bbbbbbb 100644
--- a/src/billing/total.ts
+++ b/src/billing/total.ts
@@ -3,7 +3,7 @@
-export function computeTotal(items: Item[]): number {
+export function calculateTotal(items: Item[]): number {
   return items.reduce((sum, i) => sum + i.price, 0);
 }
diff --git a/src/billing/invoice.ts b/src/billing/invoice.ts
index ccccccc..ddddddd 100644
--- a/src/billing/invoice.ts
+++ b/src/billing/invoice.ts
@@ -10,7 +10,7 @@ export function buildInvoice(order: Order) {
-  const total = computeTotal(order.items);
+  const total = calculateTotal(order.items);
   return { ...order, total };
 }
diff --git a/src/billing/cart.ts b/src/billing/cart.ts
index eeeeeee..fffffff 100644
--- a/src/billing/cart.ts
+++ b/src/billing/cart.ts
@@ -5,7 +5,7 @@ export function cartSummary(cart: Cart) {
-  return { count: cart.items.length, total: computeTotal(cart.items) };
+  return { count: cart.items.length, total: calculateTotal(cart.items) };
 }
```
```

**expected_output:** The agent should NOT flag the rename. A pure single-token
rename exhaustively substituted, with no behavior delta, is routine per the
"What does NOT qualify" list and the Selectivity Threshold ("File count alone is
not a flagging signal"). The agent should emit the bounded "no areas requiring
special human review attention were identified" empty-guide variant, wrapped in
the canonical markers.

**assertions:**
- `does-not-flag-rename` — "The review guide does NOT flag the rename under Novel Patterns or any other category — it is a pure mechanical substitution with no behavior delta, and file count alone is not a flagging signal."
- `outputs-no-areas-message` — "The review guide body contains the message indicating no areas requiring special human review were identified."
- `uses-exact-markers` — "The PR description update uses the exact markers <!-- pr-human-guide --> and <!-- /pr-human-guide --> (not alternative formats)."

### Eval 11 — `high-fanout-core-helper`

**prompt:**

```
Add a review guide to PR #221 so the team knows what to scrutinize.

PR #221 — 'Add retry and shorten default timeout in the shared HTTP client'
URL: https://github.com/owner/repo/pull/221
Current PR description: 'Updates src/lib/http.ts, the request helper imported by every service in the repo.'

```diff
diff --git a/src/lib/http.ts b/src/lib/http.ts
index 1234567..89abcde 100644
--- a/src/lib/http.ts
+++ b/src/lib/http.ts
@@ -1,12 +1,28 @@
 import axios from 'axios';
 
-const DEFAULT_TIMEOUT_MS = 30000;
+const DEFAULT_TIMEOUT_MS = 5000;
+const MAX_RETRIES = 3;
 
 export async function request(url: string, opts: RequestOpts = {}) {
-  return axios({ url, timeout: DEFAULT_TIMEOUT_MS, ...opts });
+  let lastErr;
+  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
+    try {
+      return await axios({ url, timeout: DEFAULT_TIMEOUT_MS, ...opts });
+    } catch (err) {
+      lastErr = err;
+      if (err.response && err.response.status < 500) throw err;
+    }
+  }
+  throw lastErr;
 }
```
```

**expected_output:** The agent should flag `src/lib/http.ts` under Novel Patterns
as a high-fanout core helper edit — the path matches the shared-layout trigger
list (`lib/*`) and the helper is imported broadly. The guide should note the
change affects callers across the codebase (impact beyond the single file) and
identify the behavior change (shorter default timeout and/or new retry-on-5xx
loop). Canonical markers; posted via `gh pr edit`.

**assertions:**
- `flags-high-fanout-helper` — "The review guide flags the change to the shared HTTP client (src/lib/http.ts) under Novel Patterns / as a high-fanout core helper edit."
- `notes-broad-impact` — "The review guide notes the change affects callers across the codebase (impact extends beyond the single file because the helper is broadly imported)."
- `flags-behavior-change` — "The review guide identifies the behavior change (shortened default timeout and/or new retry-on-5xx loop) as the reviewer-relevant concern."
- `uses-html-markers` — "The review guide is wrapped in <!-- pr-human-guide --> and <!-- /pr-human-guide --> markers."

### Eval 12 — `selectivity-over-flagging`

**prompt:**

```
Can you add a review guide to PR #230 so reviewers know where to focus?

PR #230 — 'Add rate limiting to login endpoint plus housekeeping'
URL: https://github.com/owner/repo/pull/230
Current PR description: 'Adds rate limiting to the login endpoint. Also reformats a util file, bumps a dependency patch version, updates the README, and adds a test.'

```diff
diff --git a/src/auth/login.ts b/src/auth/login.ts
index 1111111..2222222 100644
--- a/src/auth/login.ts
+++ b/src/auth/login.ts
@@ -1,6 +1,15 @@
 import { verifyPassword } from './password';
+import { rateLimiter } from './rateLimiter';
 
 export async function login(req, res) {
+  const allowed = await rateLimiter.consume(req.ip);
+  if (!allowed) {
+    return res.status(429).json({ error: 'Too many attempts' });
+  }
   const ok = await verifyPassword(req.body.email, req.body.password);
   if (!ok) return res.status(401).json({ error: 'Invalid credentials' });
   return res.json({ token: issueToken(req.body.email) });
 }
diff --git a/package-lock.json b/package-lock.json
index 3333333..4444444 100644
--- a/package-lock.json
+++ b/package-lock.json
@@ -120,7 +120,7 @@
     "node_modules/express": {
-      "version": "4.18.1",
+      "version": "4.18.2",
       "resolved": "https://registry.npmjs.org/express/-/express-4.18.2.tgz"
     }
diff --git a/README.md b/README.md
index 5555555..6666666 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,3 @@
 # My App
-A web app.
+A web application for managing orders.
diff --git a/src/utils/format.ts b/src/utils/format.ts
index 7777777..8888888 100644
--- a/src/utils/format.ts
+++ b/src/utils/format.ts
@@ -1,1 +1,3 @@
-export function fmt(x){return x.trim()}
+export function fmt(x) {
+  return x.trim();
+}
diff --git a/tests/auth/login.test.ts b/tests/auth/login.test.ts
new file mode 100644
--- /dev/null
+++ b/tests/auth/login.test.ts
@@ -0,0 +1,8 @@
+import { login } from '../../src/auth/login';
+
+describe('login', () => {
+  it('rate limits repeated attempts', async () => {
+    // ...
+  });
+});
```
```

**expected_output:** The agent should flag only the login rate-limiting change
(Security). The `package-lock.json` patch version bump (version-only,
auto-generated), the README doc edit, the whitespace-only reformat of
`src/utils/format.ts`, and the new test file all fall under "What does NOT
qualify" and must not be flagged. The guide should contain a single flagged item,
wrapped in canonical markers.

**assertions:**
- `flags-security-change` — "The review guide flags the login rate-limiting change (Security category) as warranting review."
- `omits-lockfile-bump` — "The review guide does NOT flag the package-lock.json patch version bump (version-only / auto-generated)."
- `omits-docs-test-and-formatting` — "The review guide does NOT flag the README update, the whitespace-only reformat of src/utils/format.ts, or the new test file."
- `is-selective` — "The guide flags only the genuinely risky area (the rate-limit change); it does not emit a section or entry for every changed file."

### Steps

- [x] **Step 1.1:** Write a Python script (in scratchpad) that loads
  `evals/pr-human-guide/evals.json`, appends the four eval dicts above (ids 9–12)
  to `evals`, and writes the file back. To avoid reformatting the existing items,
  read the raw text and splice the 4 serialized objects before the final `]`
  (add a comma after eval 8); indent each with `textwrap.indent(json.dumps(obj, indent=2), '  ')`.
- [x] **Step 1.2:** Run it; then validate:
  `python3 -c 'import json; d=json.load(open("evals/pr-human-guide/evals.json")); assert [e["id"] for e in d["evals"]][-4:]==[9,10,11,12]; print("ok", len(d["evals"]))'`
- [x] **Step 1.3:** `git add evals/pr-human-guide/evals.json && git commit -m "test(pr-human-guide): add evals 9-12 for impact-risk signals + selectivity (spec 48)"`

---

## Task 2: Run evals 9–12 on Opus 4.8 (with_skill + without_skill)

**Files:** Create `evals/pr-human-guide/workspace/iteration-2/eval-<N>-<name>/{with_skill,without_skill}/output.md` and `…/eval_metadata.json` and `…/timing.json`

Spawn **all 8 subagents in the same turn** (4 evals × 2 configs), `mode: "auto"`,
executor model **claude-opus-4-8**.

- [x] **Step 2.1:** For each eval, write `eval_metadata.json` (`eval_id`,
  `eval_name`, `prompt`, `assertions: []`) into both config dirs.
- [x] **Step 2.2:** Spawn the 8 executor subagents. Each executor prompt MUST:
  - Receive only the eval `prompt` and this setup (NEVER the assertion text).
  - `mktemp -d` a workspace under `${TMPDIR:-/private/tmp}`, write any needed
    fixture context there, `cd` in.
  - **Not call the `Skill` tool.** `with_skill`: read
    `skills/pr-human-guide/SKILL.md` + referenced files and do the work directly.
    `without_skill`: do NOT read `skills/pr-human-guide/SKILL.md` or
    `skills/pr-human-guide/references/`, and do NOT call the `Skill` tool.
  - **Simulate** all `gh` calls (the PRs are fake): echo the command and the full
    body that would be posted; do not hit GitHub.
  - Save the final guide + terminal report to
    `evals/pr-human-guide/workspace/iteration-2/eval-<N>-<name>/<config>/output.md`.
- [x] **Step 2.3:** As each task notification arrives, write its `total_tokens` /
  `duration_ms` into `…/<config>/timing.json` (this is the only chance to capture
  it).

---

## Task 3: Grade the 8 runs

**Files:** Create `evals/pr-human-guide/workspace/iteration-2/eval-<N>-<name>/<config>/grading.json`

- [x] **Step 3.1:** Grade each run against its assertions. Pass the **full
  assertion text** strings (not ids) to the grader. Use a script for mechanical
  checks (marker presence, section-name presence, per-file entry counts, "no
  areas" phrase); judgment inline for selectivity/aggregate.
- [x] **Step 3.2:** Write each `grading.json` with shape
  `{"summary": {"passed":N,"failed":N,"total":N,"pass_rate":0.N}, "expectations":[{"text":"…","passed":bool,"evidence":"…"}]}`.
  Field names exactly `text`/`passed`/`evidence`. Evidence repo-relative, no
  absolute paths.
- [x] **Step 3.3:** Confirm each new eval discriminates (≥1 assertion fails
  without_skill). If any does not, note it (do not fabricate a delta).

---

## Task 4: Update `evals/pr-human-guide/benchmark.json`

**Files:** Modify `evals/pr-human-guide/benchmark.json`

- [x] **Step 4.1:** Append 8 run entries (evals 9–12 × 2 configs), executor model
  `claude-opus-4-8`, with `eval_name`, `pass_rate`, `passed`, `failed`, `total`,
  `expectations` (`{text,passed,evidence}` only), and `time_seconds`/`tokens`/
  `cache_tokens`/`tool_calls`/`errors` (`null` for any unrecorded measurement).
- [x] **Step 4.2:** Add an Opus-4.8 summary block (sample stddev, N−1) and a
  top-level `notes` entry naming the model + skill version v0.13; extend
  `metadata.evals_run` to `[1..12]`. Do NOT touch the 32 historical runs or their
  `run_summary`; leave `metadata.skill_version` at `"0.7"`.
- [x] **Step 4.3:** Validate JSON + key schema:
  `python3 -c 'import json; json.load(open("evals/pr-human-guide/benchmark.json"))'`
  and the `jq` expectation-keys check from plan Verification (returns `0`).
- [x] **Step 4.4:** Commit grading json **selectively** (only judgment-call
  gradings, per `evals/CLAUDE.md`); do NOT commit raw transcripts.

---

## Task 5: Update `benchmark.md` + `README.md` + cspell

**Files:** Modify `evals/pr-human-guide/benchmark.md`, `README.md`, `cspell.config.yaml`

- [x] **Step 5.1:** Add `### v0.13 — Opus 4.8 coverage for impact-risk signals +
  selectivity (spec 48)` under "Known Eval Limitations"; add four
  `### Eval N — \`name\`` per-eval sections; update the "Token statistics… N of M"
  denominator sentence to the new totals.
- [x] **Step 5.2:** Update the pr-human-guide `Eval cost` bullet in `README.md`
  to note the coverage expansion + Opus 4.8 run. Leave the table `Eval Δ` cell
  unless the full-suite headline changes (it does not).
- [x] **Step 5.3:** `npx cspell evals/pr-human-guide/*.md specs/48-pr-human-guide-eval-coverage/*.md`;
  add any unknown terms to `cspell.config.yaml` in alphabetical position.
- [x] **Step 5.4:** Commit:
  `git commit -m "docs(pr-human-guide): record Opus 4.8 coverage runs for evals 9-12 (spec 48)"`

---

## Task 6: Verify + review

- [x] **Step 6.1:** `uv run --with pytest pytest tests/pr-human-guide/` (lift
  sandbox) — must stay **135 passed**.
- [x] **Step 6.2:** Re-validate both JSON files parse and the expectation-key
  `jq` check returns `0`.
- [x] **Step 6.3:** Launch the eval viewer
  (`generate_review.py` on `iteration-2`, `--skill-name pr-human-guide`,
  `--benchmark …/benchmark.json`) so outputs are reviewable.
- [x] **Step 6.4:** Report results; if any with_skill eval failed (skill defect),
  surface it and propose a separate follow-up rather than editing the skill here.
