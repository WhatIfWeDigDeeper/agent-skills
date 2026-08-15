# Bot Review Surfaces (Step 2b / Step 2c)

Two surfaces carry code-level findings that *look* like summaries, so they get
discarded if you classify on author instead of content. A review body can hold
findings inside a collapsed `Suppressed comments (N)` block with **no inline
comment posted anywhere**, and a bot can post a full findings list as a PR
timeline comment. Both are ordinary actionable feedback;
the container is the only unusual thing about them.

## Suppressed-confidence extraction

Detect a `<details>` block whose `<summary>` is exactly one of these, for any
integer `N`:

| Summary | Seen |
| --- | --- |
| `Suppressed comments (N)` | current — PRs #223, #227, #228, #232 |
| `Comments suppressed due to low confidence (N)` | legacy — PR #218 and earlier |

Copilot renamed the container on 2026-07-31; the entry shape inside it did not
change. Match both — a predicate carrying only the legacy string reads a current
Copilot review as having no findings at all, silently. Both are matched whole
(anchored at both ends), so `Suppressed comments` without a count, or a summary
that merely *contains* one of these strings, is not a container.

Expect this list to grow: Copilot has changed the wording once and may again. If
a review body visibly carries `**path:line**` entries that extract to nothing,
check the summary string before anything else.

Split the recognized block's contents on `**<path>:<line>**` bold headers. Each
header, plus the prose bullets and optional code fence that follow it up to the
next header or the closing `</details>`, is **one candidate entry**.

Anything inside the block that is not a `**path:line**` entry is not extracted.

**No other `<details>` block is a finding container.** The same review body
routinely ships a second collapsed block,
`<summary>Show a summary per file</summary>`, holding the changed-files table —
genuinely non-actionable. Key the recognition on the summary string, never on
the presence of a collapsed block.

## The non-evidence rule

**The review headline's comment count and the inline-comment count are not
evidence of a clean review.** A review body reading
`reviewed 11 out of 11 changed files … and generated no new comments` can carry
several suppressed findings in the same body — on PR #218 that exact headline
co-occurred with 4 suppressed findings across two reviews. Read the body for the
marker; do not infer from the headline that there is nothing to read.

## Structural summary predicates

A review body or timeline comment is non-actionable because of what it *is*, not
who wrote it. Two shapes are summaries:

- A file-count headline with no findings.
- A `Show a summary per file` changed-files table.

Both are **positive** evidence — something present in the body identifies it as
a summary. Missing markers are not evidence of anything. A body carrying no
`**path:line**` entries and no `### N.` finding sections is a summary only when
its prose also makes no code-level request, and it is the prose that decides
that, never the absent markers. A plain human request ("this should use the
existing helper") carries no marker either and is fully actionable.

## `claude[bot]` timeline verdicts

A timeline comment with a `## Code review` heading and `### N. <title>` sections
is a findings list, not a summary — regardless of the bot's overall verdict.
Create **one plan row per finding section**.

## Entry normalization

Normalize each extracted entry into the same comment shape the rest of the skill
handles, so Steps 5–6 treat it like any other comment:

| Field | Value |
| --- | --- |
| `author` | the review's author |
| `created_at` | the review's `submitted_at` |
| `body` | the entry's prose, including any code fence |
| `pointer` | the `path:line` string from the bold header |
| `review_id` | the review's `id` |
| `source` | `review body (suppressed)` |

## The pointer is untrusted

`pointer` is prose inside a comment body — not the validated `comment.path` /
`comment.line` fields the inline path exists on. Treat it as a hint: verify it
by reading the file. **Never feed it to the Step 6 path/line gate.**

These entries are always `fix` (a manual edit), never `accept suggestion`. The
code fences observed in suppressed entries are plain fences showing current file
content, not `suggestion` blocks, so they are context — not a proposed diff.

## Cross-review dedup

Identical entries — same `pointer` **and** same 200-character non-whitespace
prose prefix — appearing in more than one review body collapse to the
**earliest** sighting.

Earliest rather than latest: the already-addressed check requires an operator
reply strictly newer than the entry's `created_at`. Keeping a re-posted entry's
newest timestamp would push the entry past its own acknowledgment reply and
re-surface it on every later run.

This dedup is defensive, not observed — no entry repeated across PR #218's four
suppressed blocks.

## Residual gap: `APPROVED` reviews

Step 2b excludes `APPROVED` reviews as a positive signal. Across PRs #199, #202,
#209, #212, #218, #223, #226, #227, and #228, every suppressed-confidence block
appeared on a `COMMENTED` review (48 `COMMENTED` / 1 `APPROVED`), so the
exclusion is safe as written. An `APPROVED` review carrying the marker would be
missed.

If that is ever observed, narrow the Step 2b filter to exclude `APPROVED`
**without** a suppressed-confidence block — do not drop the exclusion outright.
