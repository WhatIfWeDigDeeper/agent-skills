#!/usr/bin/env bash

set -euo pipefail

if ! command -v copilot >/dev/null 2>&1; then
  printf 'copilot is not installed or not on PATH\n' >&2
  exit 127
fi

if ! command -v jq >/dev/null 2>&1; then
  printf 'jq is not installed or not on PATH\n' >&2
  exit 127
fi

usage() {
  printf 'Usage: %s [-m MODEL|--model MODEL] [additional review focus]\n' "${0##*/}"
}

model=""
extra_focus_parts=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--model)
      if [[ $# -lt 2 ]]; then
        printf 'missing value for %s\n' "$1" >&2
        usage >&2
        exit 2
      fi
      model="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      extra_focus_parts+=("$@")
      break
      ;;
    *)
      extra_focus_parts+=("$1")
      shift
      ;;
  esac
done

extra_focus="${extra_focus_parts[*]:-}"

prompt="$(cat <<EOF
Review the currently staged git changes in this repository.
Use git diff --cached and git status --short.
Do not modify any files.

Return JSON only.
Do not use markdown fences.
Do not add commentary before or after the JSON.

Schema:
{
  "summary": "string",
  "overall_risk": "low|medium|high",
  "findings": [
    {
      "severity": "high|medium|low",
      "file": "string",
      "title": "string",
      "details": "string",
      "suggested_fix": "string"
    }
  ]
}

Rules:
- Report only concrete findings.
- If there are no findings, return "findings": [].
- Keep file paths relative to the repo root.
EOF
)"

if [[ -n "$extra_focus" ]]; then
  prompt+=$'\n\nAdditional review focus:\n'
  prompt+="$extra_focus"
fi

copilot_args=(
  -p "$prompt"
  --allow-tool='shell(git diff --cached)'
  --allow-tool='shell(git status --short)'
  --deny-tool='write'
)

if [[ -n "$model" ]]; then
  copilot_args+=(-m "$model")
fi

review_json="$(
  copilot "${copilot_args[@]}"
)"

if ! printf '%s\n' "$review_json" | jq -e . >/dev/null; then
  printf 'Copilot did not return valid JSON\n' >&2
  exit 1
fi

printf '%s\n' "$review_json"
