# Review Guide Output Format

This file is the canonical template for the rendered review-guide block that
SKILL.md Step 4 produces and SKILL.md Step 5 writes into the PR body via
`marker-helper.py`. Read it before generating output.

## With flagged items

Wrap the section in `<!-- pr-human-guide -->` / `<!-- /pr-human-guide -->`
markers (`marker-helper.py` uses these to anchor idempotent replacement). Emit
only the category sections that have at least one flagged item.

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
