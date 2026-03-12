#!/usr/bin/env bash
set -euo pipefail

HOOK_JSON="$(cat)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

TS="$(date -u +%Y%m%d_%H%M%S)"
RUN_DIR="${REPO_ROOT}/runs/claude_code/${TS}"
mkdir -p "${RUN_DIR}"

printf '%s\n' "$HOOK_JSON" > "${RUN_DIR}/session_end_input.json"

TRANSCRIPT_PATH="$(printf '%s' "$HOOK_JSON" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("transcript_path",""))')"
REASON="$(printf '%s' "$HOOK_JSON" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("reason",""))')"
CWD_HOOK="$(printf '%s' "$HOOK_JSON" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("cwd",""))')"
SESSION_ID="$(printf '%s' "$HOOK_JSON" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("session_id",""))')"

cat > "${RUN_DIR}/meta.json" <<EOF
{
  "source": "claude_code",
  "session_id": "${SESSION_ID}",
  "reason": "${REASON}",
  "cwd": "${CWD_HOOK}",
  "created_at_utc": "${TS}"
}
EOF

if [ -n "${TRANSCRIPT_PATH}" ] && [ -f "${TRANSCRIPT_PATH}" ]; then
  cp "${TRANSCRIPT_PATH}" "${RUN_DIR}/transcript.jsonl"
fi

STATUS_DIR="${REPO_ROOT}/.claude/tmp"

if [ -f "${STATUS_DIR}/latest_status.json" ]; then
  cp "${STATUS_DIR}/latest_status.json" "${RUN_DIR}/statusline.json"
fi

if [ -f "${STATUS_DIR}/latest_status_summary.json" ]; then
  cp "${STATUS_DIR}/latest_status_summary.json" "${RUN_DIR}/statusline_summary.json"
fi

python3 - <<'PY' "${RUN_DIR}"
import json
import sys
from pathlib import Path

run_dir = Path(sys.argv[1])
p = run_dir / "statusline.json"
if not p.exists():
    raise SystemExit(0)

data = json.loads(p.read_text(encoding="utf-8"))
out = {
    "model": (data.get("model") or {}).get("display_name"),
    "session_id": data.get("session_id"),
    "cwd": data.get("cwd"),
    "total_cost_usd": (data.get("cost") or {}).get("total_cost_usd"),
    "total_duration_ms": (data.get("cost") or {}).get("total_duration_ms"),
    "total_api_duration_ms": (data.get("cost") or {}).get("total_api_duration_ms"),
    "context_used_percentage": (data.get("context_window") or {}).get("used_percentage"),
}
(run_dir / "summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
PY

echo "Saved Claude Code run to ${RUN_DIR}" >&2