# peer-review — pre-flight secret-scan mechanics (Step 4b)

This file holds the detection/redaction patterns and the two-group `grep` loop
for the Step 4b pre-flight secret scan. SKILL.md Step 4b keeps the *decision* of
when the scan runs (external-CLI path only), the casing/pattern description
list, the y/N confirmation-prompt template, the abort gate, and the ordering
constraint ("Do not move this scan to after Step 4c"). Run this scan against the
in-memory `$PROMPT` string before Step 4c writes it to disk.

The patterns below are POSIX ERE so they work with `grep -E` (case-sensitive
group) and `grep -Ei` (case-insensitive group). Because the confirmation prompt
in Step 4b (in SKILL.md) requires surfacing **which** pattern fired and **what**
substring matched (so the secret can be redacted before display), check each
pattern individually rather than collapsing them into a single `grep -Eq` with
many `-e` flags — `-q` only yields a boolean exit, and a multi-pattern `-e` list
can't tell you which `-e` matched. Iterate, capture the matched substring with
`grep -Eo`, and redact for display:

```bash
# Triples of "human-readable name<TAB>detection POSIX ERE<TAB>redaction POSIX ERE".
# Tab separator keeps the regexes (which contain spaces) intact when split with
# read -r name det red. Two columns of regex because the *detection* pattern
# may legitimately match more than just the secret bytes — e.g. the `sk-` rule
# uses a leading boundary group `(^|[^A-Za-z0-9])` to skip innocent English
# substrings, and the generic-credential rule matches the whole `key: value`
# assignment so it can fire on the right shape. If we redacted by literal
# substitution of the *detection* match, we would also remove the boundary
# character (`token = sk-...` → `token =<redacted>`) or the key prefix
# (`api_key: secret` → `<redacted>`), which loses readable context. The
# *redaction* pattern is the bare token portion that should be replaced with
# `<redacted>`. For rules where detection == redaction (most patterns), repeat
# the same regex in both columns.
patterns_case_sensitive=$(cat <<'PATS'
PEM private key	-----BEGIN [A-Z ]+PRIVATE KEY-----	-----BEGIN [A-Z ]+PRIVATE KEY-----
GitHub PAT (ghp_)	ghp_[A-Za-z0-9]{36,}	ghp_[A-Za-z0-9]{36,}
GitHub OAuth (gho_)	gho_[A-Za-z0-9]{36,}	gho_[A-Za-z0-9]{36,}
GitHub server (ghs_)	ghs_[A-Za-z0-9]{36,}	ghs_[A-Za-z0-9]{36,}
GitHub user (ghu_)	ghu_[A-Za-z0-9]{36,}	ghu_[A-Za-z0-9]{36,}
OpenAI/Anthropic-style (sk-)	(^|[^A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}	sk-[A-Za-z0-9_-]{20,}
AWS access key (AKIA)	AKIA[0-9A-Z]{16}	AKIA[0-9A-Z]{16}
Slack token (xox*)	xox[baprs]-[A-Za-z0-9-]{10,}	xox[baprs]-[A-Za-z0-9-]{10,}
PATS
)

patterns_case_insensitive=$(cat <<'PATS'
Generic credential assignment	(api[_-]?key|secret|password|bearer|authorization)[[:space:]]*[:=][[:space:]]*['"]?[A-Za-z0-9+/_=-]{16,}	['"]?[A-Za-z0-9+/_=-]{16,}
PATS
)

# redact_context: capture a windowed phrase around a *detection* match and
# replace just the *secret bytes* (per the redaction pattern) with the literal
# string "<redacted>". The window is up to ~20 chars on each side of the
# detection match, so the user can locate the line without seeing the secret.
#
# We use bash parameter substitution (${var//literal/replacement}) to mask the
# secret rather than `sed -E "s/${pat}/<redacted>/"`. Two reasons: (a) several
# patterns above contain a literal `/` (e.g. the generic-credential character
# class `[A-Za-z0-9+/_=-]{16,}`), which would clash with sed's default
# delimiter and force a per-pattern delimiter choice; (b) sed's
# case-insensitive `s///i` flag is a GNU extension and is not portable to
# BSD/macOS sed, which would silently leave the secret unredacted on macOS for
# the case-insensitive group. The two-grep + bash-substitution approach
# sidesteps both problems: `grep -Eo` returns the literal matched bytes, and
# `${window//$secret/<redacted>}` does literal-string replacement (no regex),
# so no characters in `$secret` are interpreted specially.
redact_context() {
  local det_pat="$1" red_pat="$2" flag="$3"   # flag: "" for case-sensitive, "i" for case-insensitive
  local window secret
  # First grep extracts the windowed context using the detection pattern (up
  # to ~20 chars on each side of a detection match). Then a SECOND grep
  # extracts the secret from inside that window using the *redaction* pattern
  # — not from `$PROMPT` directly. Two reasons:
  #
  # (1) The detection pattern may include leading boundary groups (e.g.
  #     `(^|[^A-Za-z0-9])sk-...`) or surrounding context (e.g. the
  #     generic-credential `key[:=]value` shape) that should *not* be
  #     replaced. The redaction pattern is the bare token portion. Using it
  #     for the literal substitution preserves the boundary character and
  #     the key prefix in the output (`token = <redacted>`, not
  #     `token =<redacted>`; `api_key: <redacted>`, not `<redacted>`).
  #
  # (2) Re-grepping `$PROMPT` independently with the detection pattern would
  #     drift on macOS BSD grep — its leftmost match for the windowed
  #     `.{0,20}${det_pat}.{0,20}` is not always the same as its leftmost
  #     match for bare `${det_pat}` (the leading `.{0,20}` backtracks
  #     differently than on GNU grep / ugrep). If `$secret` were a different
  #     occurrence than the one inside `$window`, the substitution would
  #     fail silently and leak an unredacted secret. Extracting `$secret`
  #     from `$window` guarantees it is present and substitutable.
  #
  # `grep -Eo -m1` stops after the first matching *line* but `-o` still emits
  # *every* match on that line — pipe through `head -n1` to keep just one
  # match, otherwise multi-secret lines yield multi-line strings that defeat
  # the literal-string substitution.
  window=$(printf '%s' "$PROMPT" | grep -Eo${flag} -m1 -- ".{0,20}${det_pat}.{0,20}" | head -n1)
  if [ -z "$window" ]; then
    return
  fi
  secret=$(printf '%s' "$window" | grep -Eo${flag} -m1 -- "${red_pat}" | head -n1)
  if [ -z "$secret" ]; then
    return
  fi
  printf '%s' "${window//$secret/<redacted>}"
}

hits=""
while IFS=$'\t' read -r name det red; do
  [ -z "$name" ] && continue
  printf '%s' "$PROMPT" | grep -Eq -- "$det" || continue   # cheap match check
  ctx=$(redact_context "$det" "$red" "")
  hits="${hits}${name}: ${ctx}"$'\n'
done <<< "$patterns_case_sensitive"

while IFS=$'\t' read -r name det red; do
  [ -z "$name" ] && continue
  printf '%s' "$PROMPT" | grep -Eiq -- "$det" || continue
  ctx=$(redact_context "$det" "$red" "i")
  hits="${hits}${name}: ${ctx}"$'\n'
done <<< "$patterns_case_insensitive"

if [ -n "$hits" ]; then
  printf '%s' "$hits"   # surface in the confirmation prompt above
fi
```

A match in **either** group triggers the prompt. Do not collapse both groups into a single `grep -Ei` call: that turns `AKIA[0-9A-Z]{16}` into a case-insensitive match and `[0-9A-Z]` becomes `[0-9A-Za-z]`, so non-AWS lowercase strings like `akiamatashotokugawamotoharu` would falsely fire. The boundary anchor `(^|[^A-Za-z0-9])` on `sk-` prevents matching innocuous English substrings (`risk-mitigation-recommendations-list`, `task-management-…`, `disk-encryption-…`); real `sk-` keys appear at word boundaries (start of line, after whitespace, after `=`/`:`/quote).

Notes on the loop above:
- The detection step (`grep -Eq`) and the context step (`grep -Eo` for the window plus bash parameter substitution to mask the match span) are split intentionally: the `-q` form is the cheapest "did anything match" check and the windowed `-Eo` only runs when a hit is confirmed. The match itself is never bound to a shell variable that gets echoed — by the time `$ctx` is built, the secret characters have already been replaced with `<redacted>` in the pipeline.
- The user-facing output is the redacted-context phrase only (e.g. `token = <redacted>`). The raw secret value never enters `$hits`, never enters logs, and never goes to stdout — that is what makes the scan meaningful. If you modify the loop, preserve this property: any new branch that touches the match must redact before assigning to a variable that is later printed.
- `grep -E` exits non-zero on no match; `|| continue` keeps the loop going. The `... || continue` form is `set -e`-safe on its own — do **not** wrap it in `|| true`, which would also swallow real grep failures (binary-not-found, malformed regex, I/O error). If you need to distinguish "no match" (exit 1) from a real error (exit 2+), capture and inspect the status: `printf '%s' "$PROMPT" | grep -Eq -- "$pat"; rc=$?; case "$rc" in 0) ;; 1) continue ;; *) echo "grep failed: $rc" >&2; exit "$rc" ;; esac`.
- Per-pattern invocation also avoids the `-f patterns` form, which would read patterns from a file (no `patterns` file is created in this workflow; `grep -f patterns` would fail with `grep: patterns: No such file or directory`).
- The window size (`.{0,20}` on each side) is a safety margin: large enough to be useful for locating the secret, small enough that the surrounding context cannot accidentally include a second secret. If you increase it, audit the patterns above to make sure none of them can be embedded in another pattern's window.

If you prefer PCRE for richer constructs (e.g. `(?i)`, `\s`, lookarounds), use a PCRE-capable engine — `grep -P` (GNU grep, not available on macOS BSD grep), `perl -ne`, or `python -c "import re; ..."` — and rewrite the patterns accordingly. Do not feed PCRE syntax to `grep -E`; it will silently fail to match.
