#!/usr/bin/env bash
set -euo pipefail

INPUT="$(cat)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_DIR="${REPO_ROOT}/.claude/tmp"
mkdir -p "$TMP_DIR"

printf '%s\n' "$INPUT" > "$TMP_DIR/latest_status.json"

python3 - <<'PY' "$TMP_DIR/latest_status.json" "$TMP_DIR/latest_status_summary.json"
import json
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])

data = json.loads(src.read_text(encoding="utf-8"))

out = {
    "session_id": data.get("session_id"),
    "model": (data.get("model") or {}).get("display_name"),
    "cwd": data.get("cwd"),
    "context_used_percentage": (data.get("context_window") or {}).get("used_percentage"),
    "total_cost_usd": (data.get("cost") or {}).get("total_cost_usd"),
    "total_duration_ms": (data.get("cost") or {}).get("total_duration_ms"),
    "total_api_duration_ms": (data.get("cost") or {}).get("total_api_duration_ms"),
}

dst.write_text(json.dumps(out, indent=2), encoding="utf-8")
PY

python3 - <<'PY' "$TMP_DIR/latest_status_summary.json"
import json
import sys
from pathlib import Path

p = Path(sys.argv[1])
d = json.loads(p.read_text(encoding="utf-8"))

model = d.get("model") or "?"
ctx = d.get("context_used_percentage")
cost = d.get("total_cost_usd")
wall_ms = d.get("total_duration_ms")
api_ms = d.get("total_api_duration_ms")

def fmt_ms(x):
    if x is None:
        return "?"
    return f"{x/1000:.1f}s"

def fmt_cost(x):
    if x is None:
        return "?"
    return f"${x:.4f}"

ctx_s = "?" if ctx is None else f"{ctx}%"
print(f"[{model}] ctx={ctx_s} cost={fmt_cost(cost)} api={fmt_ms(api_ms)} wall={fmt_ms(wall_ms)}")
PY