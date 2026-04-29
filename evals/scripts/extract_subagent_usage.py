#!/usr/bin/env python3
"""Extract per-subagent usage from a Claude Code agent's JSONL transcript.

The runtime stores each spawned subagent's full transcript at
`~/.claude/projects/<project-key>/subagents/agent-<id>.jsonl`. The agent's
`output_file` symlink (returned at spawn time and visible at
`${TMPDIR:-/private/tmp}/claude-<uid>/.../tasks/<id>.output`, where
`<uid>` is the user's POSIX uid; `TMPDIR` switches between sandboxed and
non-sandboxed Claude Code runs) points there. This file
records every assistant turn's `message.model`, `message.usage`, content
blocks (tool_use / tool_result / text), and timestamps — which means
per-subagent time, tokens, tool calls, and errors are recoverable post-hoc
even when the parent agent didn't capture them at spawn time.

Use this script to backfill `time_seconds`, `tokens`, `cache_tokens`,
`tool_calls`, and `errors` for runs that were recorded as `null` because
their usage wasn't available at the parent level (the spec 26 / spec 27
"Opus measurement gap" pattern).

Usage:
    python3 extract_subagent_usage.py <jsonl-or-output-path> [...]

Pass either the JSONL transcript directly or the output_file symlink at
.../tasks/<agent-id>.output — the script follows symlinks. Multiple paths
are aggregated as a JSON array on stdout.

Conventions (match the repo's benchmark.json schema):
- `tokens` = input_tokens + output_tokens (full-rate billing footprint).
- `cache_tokens` = cache_creation_input_tokens + cache_read_input_tokens
  (kept separate; cache reads bill at 0.1x and creation at 1.25-2x).
- `time_seconds` = max-minus-min event timestamp.
- `tool_calls` = count of tool_use content blocks.
- `errors` = count of tool_result content blocks with is_error: true.
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def extract(path):
    """Parse a single JSONL transcript and return a usage dict."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return {"path": str(path), "error": "not found"}
    models = set()
    input_tokens = 0
    output_tokens = 0
    cache_creation = 0
    cache_read = 0
    tool_calls = 0
    errors = 0
    timestamps = []
    with open(p) as f:
        for line in f:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            ts = parse_ts(rec.get("timestamp"))
            if ts:
                timestamps.append(ts)
            msg = rec.get("message", {}) or {}
            m = msg.get("model")
            if m and m != "<synthetic>":
                models.add(m)
            usage = msg.get("usage") or {}
            if usage:
                input_tokens += usage.get("input_tokens", 0) or 0
                output_tokens += usage.get("output_tokens", 0) or 0
                cache_creation += usage.get("cache_creation_input_tokens", 0) or 0
                cache_read += usage.get("cache_read_input_tokens", 0) or 0
            content = msg.get("content")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        t = block.get("type")
                        if t == "tool_use":
                            tool_calls += 1
                        elif t == "tool_result" and block.get("is_error"):
                            errors += 1
    elapsed = None
    if len(timestamps) >= 2:
        elapsed = round((max(timestamps) - min(timestamps)).total_seconds(), 2)
    return {
        "path": str(p),
        "models": sorted(models),
        "time_seconds": elapsed,
        "tokens": input_tokens + output_tokens,
        "cache_tokens": cache_creation + cache_read,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_creation_input_tokens": cache_creation,
        "cache_read_input_tokens": cache_read,
        "tool_calls": tool_calls,
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument(
        "paths",
        nargs="+",
        help="JSONL transcript path(s) or .../tasks/<id>.output symlink(s).",
    )
    args = parser.parse_args()
    results = [extract(p) for p in args.paths]
    # Always emit a JSON array — predictable shape for jq/scripts regardless of arg count.
    json.dump(results, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
