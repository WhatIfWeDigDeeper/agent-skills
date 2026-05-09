#!/usr/bin/env bash
# evals/security/scan.sh
#
# Run snyk-agent-scan against each flagged skill and compare the parsed
# findings against the pinned baseline in evals/security/<skill>.baseline.json.
#
# Exits 0 when the parsed findings are a subset of the baseline (no new
# findings, no severity escalations). Exits 1 with a clear diff when a
# regression appears.
#
# Pre-existing baseline findings that no longer appear are reported as
# improvements but do NOT fail the gate — improvements are good.
#
# Usage:
#   bash evals/security/scan.sh                # diff against baseline (CI mode)
#   bash evals/security/scan.sh --scan-only    # print parsed scan output, no diff
#   bash evals/security/scan.sh --update-baselines --confirm
#                                              # rewrite baselines from current scan

set -euo pipefail

SCANNER_PKG="snyk-agent-scan==0.5.1"
SKILLS=(peer-review ship-it pr-comments pr-human-guide)

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BASELINE_DIR="${REPO_ROOT}/evals/security"

# The scanner requires a Snyk API token. When the token is missing (e.g., CI on
# a fork PR where the secret is not exposed), skip the scan with a clear notice
# rather than failing the gate — local maintainers and the post-merge baseline
# refresh still catch regressions; CI just loses its automated check on that
# run. Set SECURITY_SCAN_REQUIRE_TOKEN=1 to make missing-token a hard failure.
if [[ -z "${SNYK_TOKEN:-}" ]]; then
  echo "security-scan: SNYK_TOKEN is not set; scanner cannot authenticate." >&2
  echo "  Skipping scan. Set the SNYK_TOKEN repository secret to enable the CI gate," >&2
  echo "  or run \`bash evals/security/scan.sh --update-baselines --confirm\` locally" >&2
  echo "  to refresh baselines before merge." >&2
  if [[ "${SECURITY_SCAN_REQUIRE_TOKEN:-0}" == "1" ]]; then
    exit 2
  fi
  exit 0
fi

SCAN_ONLY=0
UPDATE_BASELINES=0
CONFIRM=0
for arg in "$@"; do
  case "$arg" in
    --scan-only) SCAN_ONLY=1 ;;
    --update-baselines) UPDATE_BASELINES=1 ;;
    --confirm) CONFIRM=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

if [[ "$UPDATE_BASELINES" == "1" && "$CONFIRM" != "1" ]]; then
  echo "--update-baselines requires --confirm to prevent accidental overwrites" >&2
  exit 2
fi

# Run the scanner once for one skill and emit JSON: [{"id":"W011","severity":"high"}, ...]
scan_skill() {
  local skill="$1"
  local skill_path="${REPO_ROOT}/skills/${skill}/SKILL.md"
  if [[ ! -f "$skill_path" ]]; then
    echo "skill not found: $skill_path" >&2
    return 2
  fi

  local raw
  if ! raw="$(uvx "${SCANNER_PKG}" --skills "$skill_path" 2>&1)"; then
    echo "scanner failed for ${skill}:" >&2
    echo "$raw" >&2
    return 2
  fi

  # Parse lines of the form "  ● [W011 high]: ..." or "  ● [W007 medium]: ..."
  # The scanner indents the bullet with whitespace; the bracketed token is
  # always [W### severity] where severity is one of low/medium/high/critical.
  printf '%s\n' "$raw" \
    | grep -oE '\[W[0-9]{3} (low|medium|high|critical)\]' \
    | sed -E 's/\[(W[0-9]{3}) (low|medium|high|critical)\]/{"id":"\1","severity":"\2"}/' \
    | python3 -c 'import json,sys; print(json.dumps(sorted([json.loads(line) for line in sys.stdin if line.strip()], key=lambda f:(f["id"],f["severity"]))))'
}

# Read baseline finding-set as a sorted JSON array.
read_baseline() {
  local skill="$1"
  local file="${BASELINE_DIR}/${skill}.baseline.json"
  if [[ ! -f "$file" ]]; then
    echo "[]"
    return
  fi
  python3 -c "
import json,sys
d=json.load(open('${file}'))
findings=d.get('findings',[])
print(json.dumps(sorted([{'id':f['id'],'severity':f['severity']} for f in findings], key=lambda f:(f['id'],f['severity']))))
"
}

# Compare two sorted JSON arrays of {id, severity}; print regressions/improvements.
# Exit 0 if scan ⊆ baseline (no regressions); exit 1 if any finding in scan is
# not in baseline OR severity escalated.
diff_findings() {
  local skill="$1"
  local scanned="$2"
  local baseline="$3"
  python3 - "$skill" "$scanned" "$baseline" <<'PYEOF'
import json,sys
skill, scanned_json, baseline_json = sys.argv[1], sys.argv[2], sys.argv[3]
scanned = json.loads(scanned_json)
baseline = json.loads(baseline_json)

SEV_RANK = {"low":0,"medium":1,"high":2,"critical":3}

baseline_by_id = {f["id"]: f["severity"] for f in baseline}
scanned_by_id = {f["id"]: f["severity"] for f in scanned}

new_findings = [f for f in scanned if f["id"] not in baseline_by_id]
escalations = [
    {"id": fid, "from": baseline_by_id[fid], "to": sev}
    for fid, sev in scanned_by_id.items()
    if fid in baseline_by_id and SEV_RANK.get(sev,0) > SEV_RANK.get(baseline_by_id[fid],0)
]
improvements = [f for f in baseline if f["id"] not in scanned_by_id]
de_escalations = [
    {"id": fid, "from": baseline_by_id[fid], "to": sev}
    for fid, sev in scanned_by_id.items()
    if fid in baseline_by_id and SEV_RANK.get(sev,0) < SEV_RANK.get(baseline_by_id[fid],0)
]

regressed = bool(new_findings or escalations)

print(f"  baseline: {len(baseline)} findings  |  scanned: {len(scanned)} findings", file=sys.stderr)
for f in new_findings:
    print(f"  REGRESSION  new finding: {f['id']} ({f['severity']})", file=sys.stderr)
for e in escalations:
    print(f"  REGRESSION  severity escalation: {e['id']} {e['from']} -> {e['to']}", file=sys.stderr)
for f in improvements:
    print(f"  improvement  finding cleared: {f['id']} (was {f['severity']})", file=sys.stderr)
for d in de_escalations:
    print(f"  improvement  severity de-escalated: {d['id']} {d['from']} -> {d['to']}", file=sys.stderr)

sys.exit(1 if regressed else 0)
PYEOF
}

write_baseline() {
  local skill="$1"
  local scanned_json="$2"
  local file="${BASELINE_DIR}/${skill}.baseline.json"
  local skill_version
  skill_version="$(grep -E '^  version:' "${REPO_ROOT}/skills/${skill}/SKILL.md" | head -1 | sed -E 's/.*"([^"]+)".*/\1/')"
  python3 - "$skill" "$skill_version" "$scanned_json" "$file" "$SCANNER_PKG" <<'PYEOF'
import json,sys,datetime
skill, version, scanned_json, file, scanner_pkg = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
scanner_version = scanner_pkg.split("==", 1)[1] if "==" in scanner_pkg else "unknown"
findings = json.loads(scanned_json)
out = {
    "scanner": "snyk-agent-scan",
    "scanner_version": scanner_version,
    "skill": skill,
    "skill_version": version,
    "findings": findings,
    "captured_at": datetime.date.today().isoformat(),
}
with open(file, "w") as f:
    json.dump(out, f, indent=2)
    f.write("\n")
print(f"  wrote {file}")
PYEOF
}

EXIT_CODE=0
for skill in "${SKILLS[@]}"; do
  echo "=== ${skill} ==="
  scanned="$(scan_skill "$skill")" || { EXIT_CODE=2; continue; }

  if [[ "$SCAN_ONLY" == "1" ]]; then
    echo "$scanned" | python3 -m json.tool
    continue
  fi

  if [[ "$UPDATE_BASELINES" == "1" ]]; then
    write_baseline "$skill" "$scanned"
    continue
  fi

  baseline="$(read_baseline "$skill")"
  if ! diff_findings "$skill" "$scanned" "$baseline"; then
    EXIT_CODE=1
  fi
done

if [[ "$EXIT_CODE" -ne 0 ]]; then
  echo "" >&2
  echo "security-scan: regression(s) detected. Either fix the regression or update the baseline with a PR-comment justification (per evals/security/CLAUDE.md)." >&2
fi
exit "$EXIT_CODE"
