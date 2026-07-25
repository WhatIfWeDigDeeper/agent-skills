# pr-human-guide: Resolve `marker-helper.py` From the Skill's Own Directory — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Step 5 of `pr-human-guide` invoke its bundled `marker-helper.py` via a path derived from the skill's own directory instead of a repo-root-relative `skills/pr-human-guide/…` prefix, so the skill works when installed under `.claude/skills/`, `.agents/skills/`, `~/.claude/skills/`, or a plugin cache.

**Architecture:** `marker-helper.py` is a sibling of `commands.md` — both live in this skill's `references/` directory. Any assistant executing Step 5 has just read `commands.md`, so it already knows that directory's absolute path and substitutes it into `SKILL_DIR`. No filesystem probe, no vendor directory names, no base-directory header format is required. A `${SKILL_DIR:-…}` default lets an operator override resolution from the environment, which is how the skill is tested from a git worktree.

**Tech Stack:** Markdown skill definitions; bash (`set -e`/`set -u`-safe snippets); pytest via `uv run --with pytest` for text-level regression assertions; `snyk-agent-scan` baselines under `evals/security/`.

## Global Constraints

- **No `skills/` prefix in any executable path.** The resolution logic must contain no `.claude/`, `.agents/`, or `skills/` string. Vendor-specific detail appears only as a parenthetical qualifier, per the Portability rules in `CLAUDE.md`.
- **Display-text citations are unchanged.** `commands.md`'s `See [`skills/pr-human-guide/references/marker-helper.py`](marker-helper.py)` and the same full path in `output-format.md` stay as-is — `skills/CLAUDE.md` requires citing reference files by full path.
- **Do not add a `trap`.** `commands.md` already sets one EXIT trap covering `BODY_FILE`/`OUT_FILE`/`GUIDE_FILE`; a second would clobber it.
- **Version bump:** `skills/pr-human-guide/SKILL.md` frontmatter `version: "0.14"` → `"0.15"`. Exactly **one** bump for the whole PR (Task 1), covering SKILL.md and both reference files. Do not bump again in later tasks or follow-up commits.
- **Both `CLAUDE.md` edits mirror into `.github/copilot-instructions.md`** — the `instruction-sync` CI check enforces the pairing.
- Run tests with sandbox lifted (in Claude Code: `dangerouslyDisableSandbox: true`) — `uv run --with pytest` hits a cache EPERM otherwise.
- `marker-helper.py` itself is not modified. Its argument interface is unchanged.

---

### Task 1: Sibling-directory resolution in `commands.md`

**Files:**
- Create: `tests/pr-human-guide/test_helper_path_resolution.py`
- Create: `.github/workflows/test-pr-human-guide-skill.yml` (see Step 9 — the suite was not CI-gated at all)
- Modify: `skills/pr-human-guide/references/commands.md` (the "Write the guide into the PR body (Step 5)" section)
- Modify: `skills/pr-human-guide/SKILL.md` (frontmatter `version`; the **Marker-replacement bounds** bullet in `## Security model`)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: the shell contract `SKILL_DIR` → `HELPER` → `python3 "$HELPER"` in `commands.md`. Task 2's authoring rule and Task 3's audit sweep both assert against this exact shape.

- [x] **Step 1: Confirm no version bump already exists on this branch**

```bash
git fetch origin && git diff origin/main -- skills/pr-human-guide/SKILL.md | rg '^\+  version:'
```

Expected: no output. If a `+  version:` line appears, a bump already landed — skip the bump in Step 8 and keep the existing value.

- [x] **Step 2: Write the failing regression test**

Create `tests/pr-human-guide/test_helper_path_resolution.py`:

```python
"""Regression tests for marker-helper.py path resolution (issue #206).

Step 5 must not invoke the helper through a repo-root-relative `skills/...`
path — that path only exists in a checkout of the skills repo, and breaks for
every installed layout (.claude/skills/, .agents/skills/, ~/.claude/skills/,
plugin cache).
"""

from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "pr-human-guide"
COMMANDS_MD = SKILL_DIR / "references" / "commands.md"


class TestHelperPathResolution:
    """The Step 5 invocation resolves the helper from the skill's own directory."""

    def test_no_repo_relative_invocation(self):
        assert "python3 skills/pr-human-guide" not in COMMANDS_MD.read_text()

    def test_invokes_resolved_helper_variable(self):
        assert 'python3 "$HELPER"' in COMMANDS_MD.read_text()

    def test_helper_derived_from_skill_dir(self):
        assert 'HELPER="$SKILL_DIR/references/marker-helper.py"' in COMMANDS_MD.read_text()

    def test_skill_dir_honors_environment_override(self):
        assert 'SKILL_DIR="${SKILL_DIR:-' in COMMANDS_MD.read_text()

    def test_guard_precedes_invocation(self):
        text = COMMANDS_MD.read_text()
        assert '[ -f "$HELPER" ]' in text
        assert text.index('[ -f "$HELPER" ]') < text.index('python3 "$HELPER"')

    def test_resolution_names_no_vendor_directory(self):
        """Portability: the distributed skill must not hardcode an assistant's layout."""
        text = COMMANDS_MD.read_text()
        for vendor in (".claude/skills", ".agents/skills", "~/.claude"):
            assert vendor not in text
```

- [x] **Step 3: Run the test to verify it fails**

```bash
uv run --with pytest pytest tests/pr-human-guide/test_helper_path_resolution.py -v
```

Expected: FAIL — `test_no_repo_relative_invocation`, `test_invokes_resolved_helper_variable`, `test_helper_derived_from_skill_dir`, `test_skill_dir_honors_environment_override`, and `test_guard_precedes_invocation` all fail (`test_resolution_names_no_vendor_directory` already passes; that is expected).

- [x] **Step 4: Rewrite the misleading prose in `commands.md`**

Find the sentence containing `the` `marker-helper.py` `path is repo-root-relative` and replace those two lines:

```markdown
Then assemble and post the body (the `marker-helper.py` path is repo-root-relative
— adjust the prefix to match your repo's layout if it differs):
```

with:

```markdown
Then assemble and post the body. `marker-helper.py` is resolved from this
skill's own directory — never a fixed `skills/` prefix — so the block works for
every install layout:
```

- [x] **Step 5: Replace the invocation with sibling-directory resolution**

Find the line containing `python3 skills/pr-human-guide/references/marker-helper.py` and replace it and its three continuation lines:

```bash
python3 skills/pr-human-guide/references/marker-helper.py \
  --body-file "$BODY_FILE" \
  --guide-file "$GUIDE_FILE" \
  --out "$OUT_FILE"
```

with:

```bash
# marker-helper.py sits beside this file, in this skill's references/ directory.
# Substitute the absolute path of the directory you read this file from (in
# Claude Code: the "Base directory for this skill" line in the SKILL.md header).
# It works for every install layout — project-level, user-level, plugin cache,
# or a checkout of the skills repo. Never hardcode a `skills/` prefix.
# A pre-set SKILL_DIR in the environment overrides resolution.
SKILL_DIR="${SKILL_DIR:-<absolute path of this skill's base directory>}"
HELPER="$SKILL_DIR/references/marker-helper.py"
[ -f "$HELPER" ] || { echo "marker-helper.py not found at $HELPER. Set SKILL_DIR to this skill's base directory and retry." >&2; exit 1; }
python3 "$HELPER" \
  --body-file "$BODY_FILE" \
  --guide-file "$GUIDE_FILE" \
  --out "$OUT_FILE"
```

Do **not** add a `trap` here — the existing `trap 'rm -f "$BODY_FILE" "$OUT_FILE" "$GUIDE_FILE"' EXIT INT TERM` a few lines above already covers cleanup, and a second EXIT trap would replace it.

- [x] **Step 6: Run the test to verify it passes**

```bash
uv run --with pytest pytest tests/pr-human-guide/test_helper_path_resolution.py -v
```

Expected: PASS, 6 passed.

- [x] **Step 7: Extend the Security model bullet in `SKILL.md`**

Find the bullet beginning `- **Marker-replacement bounds**` and replace it with:

```markdown
- **Marker-replacement bounds** — `references/marker-helper.py` selects the last
  anchored `<!-- pr-human-guide -->` block; extra or incomplete markers in
  `pr_body` are treated as untrusted text after canonical-block extraction and
  cannot shift replacement bounds. The helper is resolved from this skill's own
  directory — never a repo-relative `skills/…` path — so a checkout that ships a
  same-named file cannot have it executed (Step 5).
```

- [x] **Step 8: Bump the skill version**

In `skills/pr-human-guide/SKILL.md` frontmatter, change `  version: "0.14"` to `  version: "0.15"`. Skip only if Step 1 found an existing bump.

- [x] **Step 9: Confirm CI runs the new test file**

```bash
ls .github/workflows/
```

**Finding: no `pr-human-guide` workflow existed.** The `tests/pr-human-guide/`
suite — 8 files, 135 tests before this spec — was never CI-gated, so neither the
existing tests nor the new regression test would have run on a PR. `tests/CLAUDE.md`
requires closing this: "A `tests/<skill>/` suite is CI-gated only if a
corresponding workflow exists … When changing a skill's tests, confirm a workflow
actually runs that suite; add one if missing."

Create `.github/workflows/test-pr-human-guide-skill.yml`, modeled on
`test-pr-comments-skill.yml` (the `test-learn-skill.yml` template plus a fixture
upload step, which `pr-human-guide` does not need — it has no `fixtures/` directory):

```yaml
name: Test PR Human Guide Skill

on:
  push:
    branches: [main]
    paths:
      - 'skills/pr-human-guide/**'
      - 'tests/pr-human-guide/**'
  pull_request:
    branches: [main]
    paths:
      - 'skills/pr-human-guide/**'
      - 'tests/pr-human-guide/**'
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Install uv
        uses: astral-sh/setup-uv@v7

      - name: Run tests
        run: uv run --with pytest pytest tests/pr-human-guide/ -v
```

- [x] **Step 10: Verify the whole suite and spelling**

```bash
uv run --with pytest pytest tests/pr-human-guide/ -v
npx cspell skills/pr-human-guide/references/commands.md skills/pr-human-guide/SKILL.md tests/pr-human-guide/test_helper_path_resolution.py
```

Expected: all tests pass; cspell reports no unknown words. If cspell flags a term, add it to the `words` list in `cspell.config.yaml` in correct alphabetical position. Do not pipe cspell through `grep -v`.

- [x] **Step 11: Commit**

```bash
git add tests/pr-human-guide/test_helper_path_resolution.py \
        skills/pr-human-guide/references/commands.md \
        skills/pr-human-guide/SKILL.md
git commit -m "fix(pr-human-guide): resolve marker-helper.py from the skill's own directory (spec 53)" \
           -m "Closes #206"
```

---

### Task 2: Authoring and worktree-testing rules

**Files:**
- Modify: `skills/CLAUDE.md` (the `## Skill Design Patterns` list)
- Modify: `CLAUDE.md` (the `## Testing` section)
- Modify: `.github/copilot-instructions.md` (mirror of both)

**Interfaces:**
- Consumes: the `SKILL_DIR` → `HELPER` contract established in Task 1; the rules describe it.
- Produces: nothing later tasks depend on.

- [x] **Step 1: Add the authoring rule to `skills/CLAUDE.md`**

Append to the `## Skill Design Patterns` bullet list, immediately after the bullet beginning `- **Repo-specific paths need portability notes**`:

```markdown
- **Never invoke a bundled script by a repo-relative `skills/<name>/…` path** — resolve it from the skill's own directory (`SKILL_DIR="${SKILL_DIR:-<absolute base directory>}"`, then `"$SKILL_DIR/references/<script>"`). Installed skills live under `.claude/skills/`, `.agents/skills/`, `~/.claude/skills/`, or a plugin cache, where a root-level `skills/` prefix does not exist; a cwd-relative path also silently executes a same-named file from whatever repo happens to be checked out. Guard with `[ -f "$HELPER" ]` and abort with a message naming `SKILL_DIR`.
```

- [x] **Step 2: Add the worktree-testing rule to the root `CLAUDE.md`**

Append to the `## Testing` bullet list:

```markdown
- **Exercising a skill that shells out to a bundled script, from a worktree**: `.claude/skills/` is gitignored and absent in a fresh worktree, so the assistant loads the skill from the main checkout and silently runs *that* copy of the script — your worktree edits are not under test. Export the worktree copy first: `export SKILL_DIR="$(git rev-parse --show-toplevel)/skills/<skill-name>"`.
```

- [x] **Step 3: Mirror both rules into `.github/copilot-instructions.md`**

Add the Step 1 rule to the skill-authoring/design-patterns section and the Step 2 rule to the testing section, matching how that file already mirrors `skills/CLAUDE.md` content (see its existing `In a worktree, edit skills at the worktree path` line for placement precedent).

- [x] **Step 4: Verify the instruction-sync check passes**

```bash
rg -n 'Never invoke a bundled script|export SKILL_DIR' skills/CLAUDE.md CLAUDE.md .github/copilot-instructions.md
```

Expected: the authoring rule appears in both `skills/CLAUDE.md` and `.github/copilot-instructions.md`; the worktree rule appears in both `CLAUDE.md` and `.github/copilot-instructions.md`.

- [x] **Step 5: Spell-check**

```bash
npx cspell skills/CLAUDE.md CLAUDE.md .github/copilot-instructions.md
```

Expected: no unknown words.

- [x] **Step 6: Commit**

```bash
git add skills/CLAUDE.md CLAUDE.md .github/copilot-instructions.md
git commit -m "docs: forbid repo-relative bundled-script paths; document SKILL_DIR worktree testing (spec 53)"
```

---

### Task 3: Repo-wide audit and security baseline refresh

**Files:**
- Modify: `evals/security/pr-human-guide.baseline.json` (only if the scan reports drift)
- Modify: any skill file the audit sweep flags (expected: none)

**Interfaces:**
- Consumes: the completed `commands.md` change from Task 1.
- Produces: nothing.

- [x] **Step 1: Re-run the repo-wide sweep for repo-relative script invocations**

```bash
rg -n '(python3|bash|sh|node|\./)[^`]*\bskills/[a-z-]+/' skills/
```

Expected: **zero** hits. Before this spec the sweep returned exactly one — the `commands.md` invocation Task 1 replaced. If any other hit appears, apply the same `SKILL_DIR` resolution pattern to it and note it in the commit message.

- [x] **Step 2: Confirm the display-text citations were left intact**

```bash
rg -n 'skills/pr-human-guide/references/marker-helper.py' skills/pr-human-guide/
```

Expected: exactly two hits — the `See [...]` link in `references/commands.md` and the prose path in `references/output-format.md`. Both are documentation pointers and must survive unchanged. Zero hits means they were wrongly rewritten; revert that.

- [x] **Step 3: Run the security scan**

```bash
bash evals/security/scan.sh
```

Expected: no new finding IDs and no severity escalations against `evals/security/pr-human-guide.baseline.json`. The pinned `W011` (high) should still be present — it fires on the presence of `gh pr view` / `gh pr diff` regardless of mitigations.

- [x] **Step 4: Refresh the baseline**

```bash
bash evals/security/scan.sh --update-baselines --confirm
git diff --stat evals/security/
```

If `evals/security/pr-human-guide.baseline.json` changed, append a sentence to its `notes` field recording that spec 53 confined helper resolution to the skill's own directory. If a finding was **removed**, that requires a PR-comment justification explaining why the mitigation actually closed it — do not silently drop it.

Note: this file stores `—` as `—`. Edit it with Python and `json.dump(..., ensure_ascii=True)`, not the Edit tool.

- [x] **Step 5: Run the full test suite**

```bash
uv run --with pytest pytest tests/
```

Expected: all tests pass.

- [x] **Step 6: Commit**

```bash
git add evals/security/
git commit -m "chore(security): refresh pr-human-guide baseline after helper-path fix (spec 53)"
```

---

### Task 4: Ship

- [x] **Step 1: Confirm every spec task above is checked off**

Re-read this file. Every `- [ ]` must be `- [x]`.

- [x] **Step 2: Commit the spec itself**

```bash
git add specs/53-pr-human-guide-helper-path-resolution/
git commit -m "spec(53): pr-human-guide helper-script path resolution"
```

- [ ] **Step 3: Open the PR**

Use the `ship-it` skill. The PR body must reference `Closes #206`.

- [ ] **Step 4: Address review feedback**

Immediately after the PR is created, invoke `/pr-comments {pr_number}` without asking — this repo requires it after any push to a PR branch, including initial creation. Do not add a second version bump in reviewer-fix commits.

- [ ] **Step 5: Prepare for human review**

Once `/pr-comments` iterations complete and `gh pr checks {pr_number}` is clean, run `/pr-human-guide {pr_number}`. This is also the end-to-end smoke test of the fix — the skill exercising its own repaired Step 5.
