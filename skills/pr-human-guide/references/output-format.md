# Review Guide Output Format

This file is the canonical template for the rendered review-guide block that
SKILL.md Step 4 produces and SKILL.md Step 5 writes into the PR body via
`marker-helper.py`. It also holds the diff-anchor and per-entry-format mechanics
(Step 4) and the user-facing report-summary templates printed at the end (Step
6). Read the relevant section when a step directs you here.

## Diff anchors and entry format

Generate a GitHub diff anchor for each file:

```bash
# SHA-256 of the file path (cross-platform: sha256sum on Linux, shasum on macOS)
ANCHOR=$(printf '%s' "path/to/file" | if command -v sha256sum >/dev/null 2>&1; then sha256sum; else shasum -a 256; fi | cut -d' ' -f1)
# Full link
LINK="https://github.com/${OWNER}/${REPO_NAME}/pull/${pr_number}/files#diff-${ANCHOR}"
# Line-level anchor (right side): append R{line} to the link
```

Format each entry as:

```
- [ ] [`path/to/file` (L{start}-{end})](link) — one-line reason
```

Omit the line range if changes are spread across the whole file.

## With flagged items

Wrap the section in `<!-- pr-human-guide -->` / `<!-- /pr-human-guide -->`
markers (`marker-helper.py` uses these to anchor idempotent replacement). Emit
only the category sections that have at least one flagged item.

**Lockstep with `marker-helper.py`**: the opening marker must be immediately
followed by a newline and `## Review Guide` with **no blank line between them**.
`skills/pr-human-guide/references/marker-helper.py` anchors on exactly that
(`re.match(r"\r?\n## Review Guide", ...)`); inserting a blank line here silently
demotes every real block to the helper's "last complete block" fallback path.
Keep both in sync if you change this template.

```markdown
<!-- pr-human-guide -->
## Review Guide

> Areas identified by automated analysis as needing human judgment.
> This is not a complete review checklist — it highlights where your attention matters most.

### Security
- [ ] [`src/auth/middleware.ts` (L42-67)](link) — New token validation logic

### Config / Infrastructure
- [ ] [`deploy/terraform/iam.tf` (L12-18)](link) — IAM role permissions widened

### Novel Patterns
- [ ] [`src/cache/redis.ts`](link) — First use of Redis in this codebase; no existing caching pattern to reference

<!-- /pr-human-guide -->
```

## With no flagged items

When no category produced any item, emit the bounded "no areas" body — never
omit the marker block entirely, since a future re-run needs an anchor point
to replace.

```markdown
<!-- pr-human-guide -->
## Review Guide

No areas requiring special human review attention were identified.

<!-- /pr-human-guide -->
```

## Report summary

The final report SKILL.md Step 6 prints to the user (not into the PR body).
Choose *added* vs *updated* by whether `marker-helper.py` replaced an existing
block (updated) or appended a new one (added).

Added (first time the guide is written):

```
Review guide added to PR #{number}: {title}
{N} item(s) across {M} category/categories.
{pr_url}
```

Updated (re-run that replaced an existing guide):

```
Review guide updated on PR #{number}: {title}
{N} item(s) across {M} category/categories.
{pr_url}
```

When N=0 (no items flagged), omit the item-count line from both formats — the
guide body already contains the "no areas" message.
