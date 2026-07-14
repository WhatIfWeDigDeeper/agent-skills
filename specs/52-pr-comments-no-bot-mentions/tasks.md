# pr-comments: Never Emit a Live @-Mention of a Bot — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/pr-comments` refer to bot commenters by a bare display handle (`Copilot`) instead of a live `@`-mention (`@Copilot`) in everything it posts to GitHub, so crediting a bot stops dispatching a coding agent.

**Architecture:** Introduce one canonical concept — `{commenter_ref}` — defined once in `skills/pr-comments/references/reply-formats.md`: `@login` for humans, bare display handle for bots. Every surface that posts to GitHub (reply templates, free-form reply prose, commit credit lines, follow-up issue bodies, nit skip/defer replies) refers to that definition rather than restating the rule. Bot detection keys on `user.type == "Bot"`, not the `[bot]` login suffix. Terminal-only output is untouched.

**Tech Stack:** Markdown skill definitions; pytest (`uv run --with pytest`) for the classifiable logic mirrored in `tests/pr-comments/conftest.py`; JSON eval cases under `evals/pr-comments/`.

## Global Constraints

- **The rule:** in any content posted to GitHub, a bot commenter is referenced by a bare display handle (`Copilot`, `claude`, `coderabbitai`) — never `@Copilot`. Human commenters keep `@alice`.
- **Bot detection:** `user.type == "Bot"` on the comment author object is the primary signal. The `[bot]` login suffix is a fallback only — Copilot's login is bare `Copilot` on `/pulls/{n}/comments` and `copilot-pull-request-reviewer[bot]` on `/pulls/{n}/reviews`.
- **Bot display handle:** reuse the existing **Bot Display Names** algorithm in `references/bot-polling.md` — strip `[bot]`; if hyphens remain, keep the first hyphen-separated token. Do not invent new naming logic.
- **`Co-authored-by:` trailers are unchanged** — they carry noreply emails, not mentions.
- **Terminal-only output is unchanged** — status lines, confirmation prompts, and the plan table never reach GitHub and keep using `@bot1`.
- **Version bump:** `skills/pr-comments/SKILL.md` frontmatter `version: "1.50"` → `"1.51"`. Exactly **one** bump for the whole PR (Task 3), covering SKILL.md and both reference files. Do not bump again in later tasks or follow-up commits.
- Run tests with sandbox lifted (in Claude Code: `dangerouslyDisableSandbox: true`) — `uv run --with pytest` hits a cache EPERM otherwise.

---

### Task 1: `{commenter_ref}` helpers and unit tests

Mirrors the skill's bot-reference rule as pure Python in `conftest.py`, the way every other classifiable pr-comments rule is mirrored, so it can be unit-tested.

**Files:**
- Modify: `tests/pr-comments/conftest.py` (add three helpers after the existing `is_bot_login` / `split_human_bot` block, which currently ends at the `should_offer_poll` definition)
- Create: `tests/pr-comments/test_bot_mentions.py`

**Interfaces:**
- Consumes: existing `is_bot_login(login: str) -> bool` in `conftest.py` (checks the `[bot]` suffix). **Do not change its behavior** — the reviewer-list tests depend on it.
- Produces, for Tasks 2–5:
  - `is_bot_author(author: dict) -> bool`
  - `bot_display_name(login: str) -> str`
  - `commenter_ref(author: dict) -> str`

  where `author` is a comment-author dict shaped like the GitHub API's `user` object: `{"login": "Copilot", "type": "Bot"}`.

- [x] **Step 1: Write the failing tests**

Create `tests/pr-comments/test_bot_mentions.py`:

```python
"""
Tests for bot-mention suppression in posted content (spec 52):
- is_bot_author: user.type == "Bot" is primary; [bot] suffix is fallback
- bot_display_name: Bot Display Names algorithm (references/bot-polling.md)
- commenter_ref: "@alice" for humans, bare handle for bots
- No skill file emits a live @-mention of a known bot
"""

import re
from pathlib import Path

from conftest import bot_display_name, commenter_ref, is_bot_author

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "pr-comments"

KNOWN_BOT_HANDLES = ["copilot", "claude", "coderabbitai", "gemini", "renovate", "dependabot"]
BOT_MENTION_MARKER = "<!-- bot-mention-example -->"
_BOT_MENTION_PATTERN = re.compile(r"@(" + "|".join(KNOWN_BOT_HANDLES) + r")\b", re.IGNORECASE)


def _scan_lines_for_bot_mentions(lines: list[str]) -> list[int]:
    """Return 1-indexed line numbers that contain a live `@`-mention of a known bot.

    Any line containing the literal marker `<!-- bot-mention-example -->` is
    skipped, even if it also matches the bot-mention pattern. The marker exists
    so documentation prose can show the concrete anti-example (e.g. "never
    write: Good catch @Copilot") that the guard otherwise exists to catch —
    mirroring `<!-- cspell:disable-line -->` for intentional non-ASCII text.

    Only use this marker on documentation prose lines. Never add it to a
    template body: templates are interpolated and posted verbatim, so marking
    one would let a real `@`-mention slip through into a posted GitHub comment.
    """
    offenders = []
    for lineno, line in enumerate(lines, 1):
        if BOT_MENTION_MARKER in line:
            continue
        if _BOT_MENTION_PATTERN.search(line):
            offenders.append(lineno)
    return offenders


class TestIsBotAuthor:
    def test_type_bot_is_bot_even_without_suffix(self):
        """Copilot on /pulls/{n}/comments has login 'Copilot' and no [bot] suffix."""
        assert is_bot_author({"login": "Copilot", "type": "Bot"}) is True

    def test_bot_suffix_is_bot_when_type_missing(self):
        assert is_bot_author({"login": "coderabbitai[bot]"}) is True

    def test_human_is_not_bot(self):
        assert is_bot_author({"login": "alice", "type": "User"}) is False

    def test_human_without_type_is_not_bot(self):
        assert is_bot_author({"login": "alice"}) is False

    def test_human_login_containing_bot_substring_is_not_bot(self):
        """'botany' must not be misread as a bot."""
        assert is_bot_author({"login": "botany", "type": "User"}) is False


class TestBotDisplayName:
    def test_strips_bot_suffix(self):
        assert bot_display_name("renovate[bot]") == "renovate"

    def test_takes_first_hyphen_token(self):
        assert bot_display_name("copilot-pull-request-reviewer[bot]") == "copilot"

    def test_bare_login_unchanged(self):
        assert bot_display_name("Copilot") == "Copilot"

    def test_claude_bot(self):
        assert bot_display_name("claude[bot]") == "claude"


class TestCommenterRef:
    def test_human_keeps_at_mention(self):
        """@ on a human is their only notification on the flat PR timeline."""
        assert commenter_ref({"login": "alice", "type": "User"}) == "@alice"

    def test_bot_gets_bare_handle(self):
        """@copilot in a PR comment is a command, not a notification."""
        assert commenter_ref({"login": "Copilot", "type": "Bot"}) == "Copilot"

    def test_suffixed_bot_gets_bare_handle(self):
        assert commenter_ref({"login": "copilot-pull-request-reviewer[bot]", "type": "Bot"}) == "copilot"

    def test_no_bot_ref_ever_starts_with_at(self):
        bots = [
            {"login": "Copilot", "type": "Bot"},
            {"login": "claude[bot]", "type": "Bot"},
            {"login": "coderabbitai[bot]", "type": "Bot"},
            {"login": "gemini-code-assist[bot]", "type": "Bot"},
        ]
        for bot in bots:
            assert not commenter_ref(bot).startswith("@")


class TestSkillFilesHaveNoLiveBotMentions:
    """No posted-body template may @-mention a raw login, which expands to @Copilot for a bot."""

    KNOWN_BOT_HANDLES = KNOWN_BOT_HANDLES

    def _skill_md_files(self) -> list[Path]:
        return sorted(SKILL_DIR.rglob("*.md"))

    def _scan(self, predicate) -> list[str]:
        offenders = []
        for md in self._skill_md_files():
            for lineno, line in enumerate(md.read_text().splitlines(), 1):
                if predicate(line):
                    offenders.append(f"{md.relative_to(SKILL_DIR)}:{lineno}: {line.strip()}")
        return offenders

    def test_no_at_prefixed_login_placeholder(self):
        """`@{commenter_login}` expands to `@Copilot` for a bot commenter.

        This is how the `@` actually reached the posted body — not a hardcoded
        `@Copilot` literal. Templates must use `{commenter_ref}`, which drops
        the `@` for bots.
        """
        offenders = self._scan(lambda line: "@{commenter_login}" in line)
        assert offenders == [], (
            "Template @-mentions a raw login (expands to @Copilot for a bot); "
            "use {commenter_ref}:\n" + "\n".join(offenders)
        )

    def test_commenter_ref_is_defined(self):
        text = (SKILL_DIR / "references" / "reply-formats.md").read_text()
        assert "{commenter_ref}" in text
        assert "Referring to the commenter" in text

    def test_no_hardcoded_at_mention_of_known_bot(self):
        """Belt-and-braces: no literal `@Copilot` anywhere in skill content.

        A line is exempt only if it carries the literal marker
        `<!-- bot-mention-example -->` (see `_scan_lines_for_bot_mentions`),
        which lets documentation prose show the concrete anti-example the
        model must never write. This marker is for documentation prose only —
        never place it in a template body, since a template is interpolated
        and posted verbatim and the marker would suppress the exact literal
        this guard exists to catch.
        """
        offenders = []
        for md in self._skill_md_files():
            lines = md.read_text().splitlines()
            for lineno in _scan_lines_for_bot_mentions(lines):
                offenders.append(f"{md.relative_to(SKILL_DIR)}:{lineno}: {lines[lineno - 1].strip()}")
        assert offenders == [], "Live @-mention of a bot in skill content:\n" + "\n".join(offenders)


class TestBotMentionMarker:
    """Proves `<!-- bot-mention-example -->` suppresses only the line it's on."""

    def test_unmarked_mention_is_flagged(self):
        assert _scan_lines_for_bot_mentions(["Never write: Good catch @Copilot"]) == [1]

    def test_marked_mention_is_not_flagged(self):
        lines = [f"Never write: Good catch @Copilot {BOT_MENTION_MARKER}"]
        assert _scan_lines_for_bot_mentions(lines) == []

    def test_marker_does_not_suppress_other_lines(self):
        """The marker is not a blanket escape hatch — it only exempts its own line."""
        lines = [
            f"Never write: Good catch @Copilot {BOT_MENTION_MARKER}",
            "Also bad: @Copilot thanks",
        ]
        assert _scan_lines_for_bot_mentions(lines) == [2]
```

- [x] **Step 2: Run the tests to verify they fail**

```bash
uv run --with pytest pytest tests/pr-comments/test_bot_mentions.py -v
```

Expected: collection error — `ImportError: cannot import name 'bot_display_name' from 'conftest'`.

- [x] **Step 3: Add the three helpers to `conftest.py`**

Insert immediately after the existing `split_human_bot` function (before `should_offer_poll`):

```python
def is_bot_author(author: dict) -> bool:
    """Returns True if a comment author is a bot account.

    Primary signal is the GitHub ``user.type`` field. The ``[bot]`` login suffix
    is only a fallback: the same bot reports different logins on different
    endpoints (Copilot is ``Copilot`` on /pulls/{n}/comments but
    ``copilot-pull-request-reviewer[bot]`` on /pulls/{n}/reviews), so a
    suffix-only check misses it exactly where it matters.
    """
    if author.get("type") == "Bot":
        return True
    return is_bot_login(author.get("login", ""))


def bot_display_name(login: str) -> str:
    """Short display handle for a bot login.

    Implements the Bot Display Names algorithm in references/bot-polling.md:
    strip the ``[bot]`` suffix, then keep the first hyphen-separated token.
    """
    name = login[: -len("[bot]")] if login.endswith("[bot]") else login
    if "-" in name:
        name = name.split("-", 1)[0]
    return name


def commenter_ref(author: dict) -> str:
    """How a body posted to GitHub refers to a commenter (spec 52).

    Humans get an ``@``-mention — on the flat PR timeline it is the only thing
    that notifies them of a reply. Bots get a bare display handle: ``@copilot``
    in a PR comment is a *command* that dispatches a Copilot coding agent, not a
    notification.
    """
    login = author.get("login", "")
    if is_bot_author(author):
        return bot_display_name(login)
    return f"@{login}"
```

- [x] **Step 4: Run the tests**

```bash
uv run --with pytest pytest tests/pr-comments/test_bot_mentions.py -v
```

Expected, precisely:

| Test | State | Why |
|---|---|---|
| `TestIsBotAuthor`, `TestBotDisplayName`, `TestCommenterRef` | PASS | the helpers you just wrote |
| `test_no_at_prefixed_login_placeholder` | **FAIL** | `@{commenter_login}` still appears in `reply-formats.md` (3×) and `nit-gate.md` (3×); Tasks 2 and 4 remove them |
| `test_commenter_ref_is_defined` | **FAIL** | Task 2 adds the definition |
| `test_no_hardcoded_at_mention_of_known_bot` | PASS | verified: the skill contains **no** literal `@Copilot` today — the `@` reaches the posted body only via the `@{commenter_login}` placeholder. This test is a forward guard against someone hardcoding one later, so it is green from the start and must stay green. |

Record the offender list the two failing tests print and confirm every offender is a line Task 2 or Task 4 will touch. **If an offender appears in a file no later task touches, stop and report it** — the plan missed a surface.

- [x] **Step 5: Commit**

```bash
git add tests/pr-comments/conftest.py tests/pr-comments/test_bot_mentions.py
git commit -m "test(pr-comments): commenter_ref helpers — bots get a bare handle, humans keep @ (spec 52)"
```

The skill-file scan is red at this commit by design; Task 4 turns it green.

---

### Task 2: Define `{commenter_ref}` in `reply-formats.md`

The canonical definition lives here. Every other surface points at it.

**Files:**
- Modify: `skills/pr-comments/references/reply-formats.md`

**Interfaces:**
- Consumes: the Bot Display Names algorithm in `references/bot-polling.md` (referenced, not duplicated).
- Produces: the token `{commenter_ref}` and the section title **"Referring to the commenter"**, which Tasks 3 and 4 cite by name.

- [x] **Step 1: Add the canonical rule section**

Insert a new section immediately after the `## Byline` section (after the line `For example, Claude Code uses ...`) and before `## Nit replies (Step 6d nits-only gate)`:

```markdown
## Referring to the commenter — `{commenter_ref}`

Every body this skill posts to GitHub — inline reply, review-body reply, timeline
reply, nit skip/defer reply, commit message, follow-up issue — refers to a
commenter as `{commenter_ref}`:

| Commenter | `{commenter_ref}` | Example |
|---|---|---|
| Human | `@` + login | `@alice` |
| Bot | bare display handle, **no `@`** | `Copilot`, `claude`, `renovate` |

**A bot is any comment author with `user.type == "Bot"`.** Do not test for a
`[bot]` login suffix instead — the same bot reports different logins on different
endpoints (Copilot is `Copilot` on `/pulls/{pr_number}/comments` but
`copilot-pull-request-reviewer[bot]` on `/pulls/{pr_number}/reviews`), so a
suffix-only check misses it exactly where it matters. Derive the display handle
with the **Bot Display Names** algorithm in `references/bot-polling.md` (strip
`[bot]`; if hyphens remain, keep the first hyphen-separated token).

**Why the asymmetry.** On a human, `@login` is a notification — on the flat PR
timeline it is the only thing that tells them you replied. On a bot, `@login` is
a **command**: `@copilot` in a PR comment dispatches a Copilot coding agent,
which starts pushing its own commits to the PR. Never emit a live `@`-mention of
a bot in posted content.

**This binds your own prose, not just the templates below.** Do not write
"Good catch @Copilot" or "as @copilot noted" in the free-form part of a reply,
a commit message, or an issue body. Write "Good catch, Copilot" / "as Copilot
noted".

Terminal output — status lines, confirmation prompts, the plan table — is never
posted to GitHub and is unaffected; it keeps using `@bot1`.
```

- [x] **Step 2: Update the nit-replies pointer**

In the `## Nit replies (Step 6d nits-only gate)` section, replace this sentence fragment:

```
(Step 2c) nit via the issue comments endpoint, with a **timeline** reply
following the Timeline comment format below — start with `@{commenter_login}` and
include a `>` quote, or the commenter is not notified and the reply loses
context.
```

with:

```
(Step 2c) nit via the issue comments endpoint, with a **timeline** reply
following the Timeline comment format below — start with `{commenter_ref}` and
include a `>` quote, or the reply loses its link to the originating comment (and,
for a human commenter, they are not notified).
```

- [x] **Step 3: Update the Timeline comment template**

In `## Timeline comment (Step 2c)`, replace the whole body of the section (the prose sentence, the "Required format" block, and the `bash` block) with:

````markdown
Use the same issue comments endpoint. **The reply body must start with
`{commenter_ref}` (see "Referring to the commenter" above — `@alice` for a human,
a bare handle like `Copilot` for a bot) and include a `>` quote of the relevant
excerpt**, since the timeline is flat and has no thread nesting.

Both parts are required. Without them a human commenter is not notified, and —
for **any** commenter — the reply loses the context linking it to their comment.
The `>` quote is also what the Step 2c linkage dedup keys on to mark the comment
`skip` on the next run; for a bot commenter, whose `{commenter_ref}` carries no
`@`-mention by design, **the quote is the only linkage signal there is**. Never
drop it.

Required format:
```
{commenter_ref}
> [relevant excerpt from their comment]

[Your response]

---
🤖 Generated with [AssistantName](url)
```

```bash
gh api repos/{owner}/{repo}/issues/{pr_number}/comments \
  --method POST \
  --field 'body={commenter_ref}
> [relevant excerpt]

[Your response]

---
🤖 Generated with [AssistantName](url)'
```
````

- [x] **Step 4: Verify no stale token remains in this file**

```bash
rg -n 'commenter_login|@Copilot|@copilot' skills/pr-comments/references/reply-formats.md
```

Expected: no output.

- [x] **Step 5: Commit**

```bash
git add skills/pr-comments/references/reply-formats.md
git commit -m "feat(pr-comments): define {commenter_ref} — bots get a bare handle, never an @-mention (spec 52)"
```

---

### Task 3: Apply the rule to SKILL.md's four surfaces + version bump

**Files:**
- Modify: `skills/pr-comments/SKILL.md` (frontmatter `version`; Step 2c linkage note; Step 10 commit credit; Step 11 reply prose + follow-up issue body)

**Interfaces:**
- Consumes: `{commenter_ref}` and the "Referring to the commenter" section from Task 2.
- Produces: nothing new — this task only applies the rule.

- [x] **Step 1: Bump the version**

In the frontmatter, change:

```
  version: "1.50"
```

to:

```
  version: "1.51"
```

This is the **only** version bump in this PR. Do not add another in Task 4 or 5.

- [x] **Step 2: Note the bot-linkage asymmetry in Step 2c**

Find the Step 2c paragraph beginning "Build your **actionable timeline comments** set by excluding PR author...". Append this sentence to the end of that paragraph, immediately after "...or blockquotes their text." and before "Keep the full raw list for linkage detection before applying the exclusions.":

```
Replies to **bot** commenters carry no `@`-mention by design (see `references/reply-formats.md` — "Referring to the commenter"), so they link solely via the blockquote; do not treat a missing `@`-mention on a bot reply as a missing linkage.
```

- [x] **Step 3: Fix the commit-credit surface (Step 10)**

In `### 10. (If Changes Were Made) Commit with Commenter Credit`, immediately after the example commit's closing fence and before the line beginning "Deduplicate co-authors", insert:

```markdown
Credit lines name the commenter as `{commenter_ref}` (see `references/reply-formats.md` — "Referring to the commenter"): `@alice` for a human, a **bare handle for a bot** — write `(suggested by Copilot)`, never `(suggested by @Copilot)`. An `@`-mention of a bot in a pushed commit message is still a live mention on GitHub. `Co-authored-by:` trailers are unaffected — they carry a noreply email, not a mention, and remain `Co-authored-by: <login> <<login>@users.noreply.github.com>` for bots and humans alike.
```

The existing `@alice` / `@bob` examples in the commit block are humans and stay as they are.

- [x] **Step 4: Fix the reply-prose surface (Step 11)**

In `### 11. Reply to Comments`, immediately after the byline block (the fenced block containing `🤖 Generated with [AssistantName](url)`) and before the line beginning "`consistency` items (from Step 6b) have no associated review thread", insert:

```markdown
**Never `@`-mention a bot in a reply body.** Refer to a bot commenter by a bare handle — `Copilot`, not `@Copilot` — in the template wrapper **and in your own free-form prose** ("Good catch, Copilot", never "Good catch @Copilot"). `@copilot` in a PR comment is a command that dispatches a Copilot coding agent onto the PR, not an attribution. Human commenters keep `@alice`. See `references/reply-formats.md` — "Referring to the commenter".
```

- [x] **Step 5: Fix the follow-up-issue surface (Step 11)**

Replace the `gh issue create` bash block's body-file construction. Change:

```bash
issue_body_file="$(mktemp "${TMPDIR:-/private/tmp}/pr-comments-issue-XXXXXX")"
trap 'rm -f "$issue_body_file"' EXIT
{
  printf 'Suggested in PR #%s by @%s.\n\n' "N" "reviewer"
  printf '%s\n' "<comment body>"
} >"$issue_body_file"
```

to:

```bash
# Substitute {commenter_ref} the same way as {owner}/{repo} below: "@alice" for a
# human commenter; a bare handle (e.g. "Copilot") for a bot — never seed this with
# an @-prefixed literal, since an @-mention of a bot in an issue body is a live
# mention. See references/reply-formats.md — "Referring to the commenter".
commenter_ref="{commenter_ref}"
issue_body_file="$(mktemp "${TMPDIR:-/private/tmp}/pr-comments-issue-XXXXXX")"
trap 'rm -f "$issue_body_file"' EXIT
{
  printf 'Suggested in PR #%s by %s.\n\n' "N" "$commenter_ref"
  printf '%s\n' "<comment body>"
} >"$issue_body_file"
```

Note the format string loses its literal `@` — it now comes from `$commenter_ref`.

The confirmation prompt just above it (`File a follow-up GitHub issue for the out-of-scope suggestion from @reviewer? [y/n]`) is **terminal output, not posted content** — leave it unchanged.

- [x] **Step 6: Verify**

```bash
rg -n 'version:' skills/pr-comments/SKILL.md | head -1
rg -n 'suggested by @Copilot|by @%s' skills/pr-comments/SKILL.md
```

Expected: version reads `"1.51"`; the second command produces no output.

- [x] **Step 7: Commit**

```bash
git add skills/pr-comments/SKILL.md
git commit -m "feat(pr-comments): no @-mention of bots in replies, commits, or issue bodies (spec 52)"
```

---

### Task 4: Reword `nit-gate.md` and prove quote-only self-termination

Removing the `@` for bots leaves the `>` quote as the sole linkage signal for a bot timeline nit. This task makes that explicit in the docs and pins it with a test.

**Files:**
- Modify: `skills/pr-comments/references/nit-gate.md` (three references to the `@{commenter_login}` wrapper)
- Modify: `tests/pr-comments/test_bot_mentions.py` (add the quote-only linkage test)

**Interfaces:**
- Consumes: `is_already_addressed(comment, all_timeline_comments, pr_author, auth_user)` from `conftest.py` — **unchanged by this spec**. Its `@`-mention branch keeps its `(?<![A-Za-z0-9-])@{login}(?![A-Za-z0-9-])` regex for humans; bots resolve via its blockquote branch.

- [x] **Step 1: Write the failing test**

Append to `tests/pr-comments/test_bot_mentions.py`:

```python
class TestBotTimelineNitSelfTermination:
    """A bot nit reply has no @-mention, so the '>' quote is its only linkage signal."""

    def _c(self, author: str, body: str, created_at: str) -> dict:
        return {"author": author, "body": body, "created_at": created_at}

    def test_bot_reply_without_at_mention_links_via_quote(self):
        from conftest import is_already_addressed

        nit = self._c("Copilot", "nit: rename `tmp` to `filtered`.", "2026-01-01T10:00:00Z")
        # The Task 2 template: bare handle, no "@", plus the mandatory '>' quote.
        reply = self._c(
            "skillbot",
            "Copilot\n> nit: rename `tmp` to `filtered`.\n\nNoted as a nit — leaving as-is for now.",
            "2026-01-01T11:00:00Z",
        )
        assert is_already_addressed(nit, [nit, reply], pr_author="prowner", auth_user="skillbot") is True

    def test_bot_reply_without_quote_does_not_link(self):
        """Dropping the quote on a bot reply loses the only linkage signal — it re-surfaces."""
        from conftest import is_already_addressed

        nit = self._c("Copilot", "nit: rename `tmp` to `filtered`.", "2026-01-01T10:00:00Z")
        reply = self._c(
            "skillbot",
            "Copilot\n\nNoted as a nit — leaving as-is for now.",
            "2026-01-01T11:00:00Z",
        )
        assert is_already_addressed(nit, [nit, reply], pr_author="prowner", auth_user="skillbot") is False

    def test_human_reply_still_links_via_at_mention_alone(self):
        """The human path is unchanged: @mention alone suffices, no quote needed."""
        from conftest import is_already_addressed

        comment = self._c("alice", "Please add tests.", "2026-01-01T10:00:00Z")
        reply = self._c("skillbot", "@alice tests added, see latest commit.", "2026-01-01T11:00:00Z")
        assert is_already_addressed(comment, [comment, reply], pr_author="prowner", auth_user="skillbot") is True
```

- [x] **Step 2: Run it**

```bash
uv run --with pytest pytest tests/pr-comments/test_bot_mentions.py::TestBotTimelineNitSelfTermination -v
```

Expected: **all three PASS immediately.** `is_already_addressed` already accepts a blockquote as linkage, so no matcher change is needed — that is exactly the property this spec relies on, and these tests pin it against future regression. If `test_bot_reply_without_at_mention_links_via_quote` fails, the blockquote branch is broken and the spec's core assumption is wrong — **stop and report**, do not "fix" it by matching bare logins (see plan.md, "Explicitly rejected").

- [x] **Step 3: Reword the two `skip-all` / `issue-all` wrapper references**

In `nit-gate.md`, in the `### skip-all` section, replace:

```
timeline-originated nit needs the `@{commenter_login}` + `>` quote wrapper).
```

with:

```
timeline-originated nit needs the `{commenter_ref}` + `>` quote wrapper).
```

Then in the `### issue-all` section, replace:

```
matches the comment's origin (a timeline-originated nit needs the
`@{commenter_login}` + `>` quote wrapper). Do **not** commit code; leave
```

with:

```
matches the comment's origin (a timeline-originated nit needs the
`{commenter_ref}` + `>` quote wrapper). Do **not** commit code; leave
```

- [x] **Step 4: Reword the load-bearing note**

In the "Thread state on skip/issue" bullet list, replace the whole **Timeline** sub-bullet:

```
  - **Timeline** nits have no thread, but the skip/issue reply's
    `@{commenter_login}` + `>` quote (required by `references/reply-formats.md`)
    is recognized by the Step 2c linkage dedup, which marks the comment `skip`
    next run. The `@mention` + quote is therefore load-bearing for
    self-termination, not just notification.
```

with:

```
  - **Timeline** nits have no thread, but the skip/issue reply's
    `{commenter_ref}` + `>` quote (required by `references/reply-formats.md`) is
    recognized by the Step 2c linkage dedup, which marks the comment `skip` next
    run. The wrapper is therefore load-bearing for self-termination, not just
    notification — and note the asymmetry. For a **human** commenter either
    signal alone suffices: the dedup accepts an `@`-mention **or** a blockquote.
    A **bot** commenter's `{commenter_ref}` carries no `@`-mention by design, so
    the `>` quote is its **sole** linkage signal. Never post a bot nit reply
    without the quote — it would re-surface and re-trigger this gate on every
    subsequent run.
```

- [x] **Step 5: Run the whole skill-file scan — it should now be green**

```bash
uv run --with pytest pytest tests/pr-comments/test_bot_mentions.py -v
```

Expected: **all** tests PASS — including `test_no_at_prefixed_login_placeholder` and `test_commenter_ref_is_defined`, both red since Task 1.

If `test_no_at_prefixed_login_placeholder` still reports offenders, they are surfaces this plan missed. Fix them in this same commit if they are genuinely posted content. If an offender is terminal-only output (a status line or `[y/N]` prompt in `bot-polling.md` / `report-templates.md` — these use `@bot1` placeholders, which the scan does not match), it is a **false positive**: exclude that file from the scan rather than rewriting the terminal copy, and say why in the commit message.

- [x] **Step 6: Commit**

```bash
git add skills/pr-comments/references/nit-gate.md tests/pr-comments/test_bot_mentions.py
git commit -m "fix(pr-comments): bot nit replies link via the quote alone — no @-mention (spec 52)"
```

---

### Task 5: Eval coverage for the free-form-prose route

The unit tests guard the *templates*. They cannot guard the route that actually caused this bug: the agent wrote "Good catch @Copilot" in free-form prose that no template produced. Only an eval catches that.

**Files:**
- Modify: `evals/pr-comments/evals.json` (append eval id 41 to the `evals` array)

**Interfaces:**
- Consumes: nothing from earlier tasks (evals exercise the skill end-to-end).

- [x] **Step 1: Read the eval conventions**

```bash
cat evals/CLAUDE.md
```

Follow whatever it says about adding cases and about whether a benchmark baseline re-run is required. If it requires a baseline run for a new case, note that in the final report rather than silently skipping it.

- [x] **Step 2: Append the eval case**

Add to the `evals` array in `evals/pr-comments/evals.json` (remember: the preceding element's `}` needs a trailing `,`):

```json
{
  "id": 41,
  "name": "bot-credit-no-at-mention",
  "prompt": "Address the review comments on this PR in auto mode (no flags). There is one unresolved timeline comment from Copilot (a bot; `user.type` is `\"Bot\"`, login `Copilot`): \"The PR description claims the two files are identical, but they are not — line 1 is the title and line 3 points each mirror rule at the other file. Only the rules sections are kept in sync.\" The claim is correct: the PR description is wrong and should be corrected. There is also one unresolved timeline comment from alice (a human): \"Please add a test for the empty-input case.\" Both are valid and you should act on them.",
  "expected_output": "The skill fixes the PR description and adds the test, then replies to both commenters. The reply to Copilot refers to it by a bare handle — `Copilot` — with no `@` anywhere in the body, because an `@copilot` mention in a PR comment dispatches a Copilot coding agent rather than crediting it. The reply to alice keeps the `@alice` mention, which is her only notification on the flat timeline. Both timeline replies include a `>` quote of the originating comment. The commit message credits the bot as `(suggested by Copilot)`, not `(suggested by @Copilot)`, while `Co-authored-by:` trailers are unchanged for both.",
  "assertions": [
    {
      "id": "no-at-mention-of-bot-in-reply",
      "text": "The reply posted to the Copilot comment contains no `@`-mention of Copilot anywhere in the body — not in the opening wrapper and not in the free-form prose (e.g. it does not say 'Good catch @Copilot')"
    },
    {
      "id": "bot-referred-to-by-bare-handle",
      "text": "The reply to Copilot refers to it by a bare handle such as `Copilot`"
    },
    {
      "id": "bot-reply-keeps-quote",
      "text": "The reply to the Copilot timeline comment still includes a `>` blockquote of the original comment, which is its only remaining linkage signal"
    },
    {
      "id": "human-keeps-at-mention",
      "text": "The reply to alice's timeline comment still begins with `@alice`"
    },
    {
      "id": "commit-credit-has-no-bot-at-mention",
      "text": "The commit message credits the bot without an `@` (e.g. `(suggested by Copilot)`), and does not contain `@Copilot`"
    }
  ]
}
```

- [x] **Step 3: Validate the JSON**

The Edit tool does not check JSON syntax — a missing comma only surfaces at parse time.

```bash
python3 -c 'import json; d = json.load(open("evals/pr-comments/evals.json")); print(len(d["evals"]), "evals; last id:", d["evals"][-1]["id"])'
```

Expected: `41 evals; last id: 41`

- [x] **Step 4: Commit**

```bash
git add evals/pr-comments/evals.json
git commit -m "test(pr-comments): eval for bot credit without an @-mention (spec 52)"
```

---

### Task 5b: Run eval 41 and update the benchmark

**Added mid-flight.** The original plan stopped at *authoring* eval 41. `evals/CLAUDE.md` binds us further: "When adding new evals to `evals.json`, run them immediately — do not wait for the user to ask… update `benchmark.json` as part of the same task," and "When evals are listed in a spec's tasks.md or plan, run them without asking — inclusion in the plan/tasks constitutes prior approval." An unrun eval also proves nothing: it is the only artifact that can tell us whether the fixed skill actually stops writing `@Copilot` in free-form prose, which is the failure this whole spec exists to prevent.

**Files:**
- Modify: `evals/pr-comments/benchmark.json`
- Modify: `evals/pr-comments/benchmark.md`
- Modify: `README.md` (Eval Δ column + Eval cost bullet, only if the delta changes)
- Create (only if the grader made a judgment call): `evals/pr-comments/grading-eval41-{with,without}.json`

**Run it in two stages** (splitting keeps the numeric benchmark surgery away from the execution):

- [x] **Stage A — execute and grade.** Run eval 41 in both configurations per `evals/CLAUDE.md`. Binding rules: spawn executors with `mode: "auto"`; each works in a `mktemp -d` workspace; the executor is given ONLY the eval prompt and fixtures — **never** the assertion text; the `without_skill` executor may not read `skills/pr-comments/**`; **neither** executor may call the `Skill` tool (for `with_skill`, read SKILL.md and do the work directly). Then grade both transcripts against eval 41's five assertions, passing the grader the **full assertion text strings**, not the ids.

- [x] **Stage B — update the benchmark.** Using Stage A's real numbers only — **never fabricate a measurement**: append the two run entries; set `metadata.skill_version` to `"1.51"` and append `41` to `metadata.evals_run`; recompute `run_summary` (sample stddev, N−1; deltas from unrounded means, 2-decimal `pass_rate`); add eval 41's section to `benchmark.md` and update the "N of M" token-count denominator; update README's Eval Δ and Eval cost bullet if the delta moved.

**Acceptance:** eval 41 must **discriminate** — at least one assertion must FAIL in `without_skill`. If it passes 100% in both configurations it is non-discriminating: do not quietly bank it. Record that fact in `benchmark.json`'s notes and report it, since it would mean the baseline model already avoids `@`-mentioning bots and the skill's rule is belt-and-braces rather than load-bearing.

**Outcome (met):** eval 41 discriminates — `with_skill` 5/5, `without_skill` 2/5 (+0.60). Assertions 2 (bare handle), 3 (`>` blockquote) and 4 (`@alice` preserved) all FAIL without the skill.

Three deviations from the Stage B text above, each forced by what the data actually showed:

1. **A third executor-model track.** The Agent tool can only dispatch current models, so the retired `claude-sonnet-4-6` / `claude-opus-4-7` executors can no longer be pinned and eval 41 could not be appended to either existing track. It is recorded under `claude-sonnet-5` with its own `run_summary_by_model` block (N = 1, so `stddev` is `null` — sample stddev is undefined at N = 1).
2. **`run_summary` was not recomputed, and README's Eval Δ column did not move.** Both are scoped to the full-suite tracks, which eval 41 is not part of; changing either would have misreported one eval as a suite result. The "N of M" token denominator is likewise a Sonnet 4.6 figure and is unchanged for the same reason. README's *Eval cost* bullet did gain a Sonnet 5 sub-bullet.
3. **The recorded token delta is negative (−2,761) and must not be read as a saving.** `tokens` counts input + output only, and the with-skill run served nearly all its input from cache (62 uncached input tokens against 2,459,308 cache tokens, vs 1,296,190 for the baseline). Noted in both `benchmark.json` and `benchmark.md`.

One finding worth carrying to final review: assertion 1 (no `@`-mention of the bot) **passed in both configurations** — but only *vacuously* in the baseline, which referenced no commenter at all. An earlier variant of this scenario *did* make the baseline write a literal `@Copilot`, reproducing the production incident. The hazard is real but intermittent, so assertion 1 is a guard, not a discriminator; assertions 2–4 carry the delta. Recorded in the benchmark notes so a later reader does not mistake it for dead weight.

---

### Task 6: Repo hygiene — docs sync, spell check, full suite

**Files:**
- Modify: `cspell.config.yaml` (only if new terms appear)
- Modify: `README.md` (only if its `pr-comments` notes describe the reply format)
- Modify: `specs/52-pr-comments-no-bot-mentions/tasks.md` (check off completed items as you go)
- Modify: `specs/52-pr-comments-no-bot-mentions/plan.md` (record the allow-marker in Testing, per Step 0)
- Modify: `tests/pr-comments/test_bot_mentions.py` (only if Step 5 surfaces a real cross-suite regression, not anticipated when this task was planned)

- [x] **Step 0: Sync the spec with the mid-flight marker decision**

Task 2 surfaced a conflict this plan created: the belt-and-braces scan test forbade the literal `@Copilot` anywhere in skill markdown, which stopped the skill's **own documentation** from showing the concrete anti-example — the strongest instruction against the exact failure this spec exists to prevent. Resolution (human decision): the scan skips lines carrying `<!-- bot-mention-example -->`, mirroring the repo's existing `<!-- cspell:disable-line -->` convention, and the anti-example is restored on a marked line.

Update both spec files so they describe what was actually built:
- In `plan.md`, extend the **Testing** section to record the allow-marker and why it exists.
- In `tasks.md`, update Task 1's `TestSkillFilesHaveNoLiveBotMentions` code block to match the shipped implementation (the `_scan_lines_for_bot_mentions` helper and the marker tests).

A spec that no longer matches the code is worse than no spec.

- [x] **Step 1: Check whether README describes the reply format**

```bash
rg -n -A 12 'pr-comments' README.md | rg -n 'mention|@|reply|timeline'
```

If the `pr-comments` notes section describes the `@{commenter_login}` timeline reply format, update it to `{commenter_ref}` with a one-line note that bots get a bare handle. If it does not mention the reply format, **make no change** — do not pad the README.

- [x] **Step 2: Confirm CI actually runs this suite**

```bash
ls .github/workflows/ | rg 'pr-comments'
rg -n 'tests/pr-comments' .github/workflows/
```

Expected: a workflow (e.g. `test-pr-comments-skill.yml`) that runs `pytest tests/pr-comments/`. `test_bot_mentions.py` is picked up automatically by directory glob — no workflow edit needed. If **no** workflow runs this suite, stop and report: the new tests would not be CI-gated.

- [x] **Step 3: Spell check every file touched**

```bash
npx cspell skills/pr-comments/SKILL.md skills/pr-comments/references/reply-formats.md skills/pr-comments/references/nit-gate.md specs/52-pr-comments-no-bot-mentions/plan.md specs/52-pr-comments-no-bot-mentions/tasks.md README.md
```

Add any unknown word to the `words` list in `cspell.config.yaml` **in alphabetical position**. (`coderabbitai` was already added when plan.md was committed.) Do not pipe this through `grep -v` — an npm cache EPERM would be silently swallowed and read as "clean".

- [x] **Step 4: Run the full pr-comments suite**

```bash
uv run --with pytest pytest tests/pr-comments/ -v
```

Expected: all tests pass — the pre-existing suites (notably `test_timeline_comments.py`, whose human `@mention` linkage tests must be untouched, and `test_nit_gate.py`) plus the new `test_bot_mentions.py`.

- [x] **Step 5: Run the whole test suite**

```bash
uv run --with pytest pytest tests/ -q
```

Expected: no failures. `conftest.py` gained three helpers and changed none, so no other skill's suite should be affected — if one is, that is a real regression, not a flake.

**Found and fixed:** running `tests/pr-comments/` alone passed (552/552), but the full `tests/` tree failed 3 tests in `TestBotTimelineNitSelfTermination` with `ImportError: cannot import name 'is_already_addressed' from 'conftest' (.../tests/uv-deps/conftest.py)`. Cause: every `tests/<skill>/` directory has its own `conftest.py` and none of the directories have `__init__.py`, so the bare module name `conftest` is shared across the whole `tests/` tree (see `tests/CLAUDE.md`'s basename-collision warning — it applies to `conftest.py` itself, not just `test_*.py` files). `TestBotTimelineNitSelfTermination`'s three test methods each did a **function-scoped** `from conftest import is_already_addressed` (unlike the rest of the file, which imports at module level); by the time those deferred imports ran, `sys.modules['conftest']` had been overwritten by a later directory's `conftest.py`. Fix: moved `is_already_addressed` into the file's existing top-level `from conftest import (...)` statement and deleted the three function-scoped imports — matching the pattern every other test in the file already uses. No assertions changed.

- [x] **Step 6: Verify the version bumped exactly once**

```bash
git fetch origin && git diff origin/main -- skills/pr-comments/SKILL.md | rg '^\+  version:'
```

Expected: exactly one line, `+  version: "1.51"`.

- [x] **Step 7: Commit any hygiene changes**

Stage **explicit paths only** — never `git add -A`. The working tree has untracked scratch directories (`.pnpm-store/`, `node_modules/`) that are not git-ignored; `-A` would commit them.

```bash
git add cspell.config.yaml specs/52-pr-comments-no-bot-mentions/tasks.md specs/52-pr-comments-no-bot-mentions/plan.md
git commit -m "chore(pr-comments): spell check and docs sync (spec 52)"
```

Drop any of those paths that you did not actually change. Skip this commit entirely if Steps 1–6 produced no file changes.

The `tests/pr-comments/test_bot_mentions.py` cross-suite import fix found in Step 5 is a separate concern (a bug fix, not hygiene) and is committed on its own — see that step's note.

---

## Done When

- Every `- [ ]` above is checked.
- `uv run --with pytest pytest tests/ -q` passes.
- `rg -n '@\{commenter_login\}' skills/pr-comments/` returns nothing — this is the construct that put the `@` in front of `Copilot`, and it is the thing this spec exists to remove.
- Every `@Copilot`-style hit from `rg -ni '@(copilot|claude|coderabbitai)\b' skills/pr-comments/` is on a line carrying the literal `<!-- bot-mention-example -->` marker. Unmarked hits are not permitted (this is what `test_no_hardcoded_at_mention_of_known_bot` enforces); a hit that is *not* on a marked line is a genuine bug — stop and report it rather than papering over it. The bullet no longer requires the raw `rg` to return nothing: the marker convention (mirroring `<!-- cspell:disable-line -->`) was adopted mid-flight in Task 2 specifically so `reply-formats.md` and `SKILL.md` could keep showing the concrete `@Copilot` anti-example — the strongest instruction against the exact failure this spec exists to prevent.
- `skills/pr-comments/SKILL.md` reads `version: "1.51"`.
