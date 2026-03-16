import json
import requests

RADAR_URL = "https://radar.epam.com/api/mcp"

# session-id cached per process
_session_id: str | None = None


def _get_headers(jwt: str) -> dict:
    h = {
        "Authorization":  f"Bearer {jwt}",
        "Content-Type":   "application/json",
        "Accept":         "application/json, text/event-stream",
    }
    if _session_id:
        h["mcp-session-id"] = _session_id
    return h


def _parse_response(resp: requests.Response) -> dict:
    """Handle both plain JSON and SSE-wrapped responses."""
    ct = resp.headers.get("Content-Type", "")
    if "text/event-stream" in ct or resp.text.lstrip().startswith("data:"):
        for line in resp.text.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:])
        return {}
    return resp.json()


def initialize(jwt: str, url: str = RADAR_URL) -> None:
    global _session_id
    headers = _get_headers(jwt)
    resp = requests.post(url, headers=headers, json={
        "jsonrpc": "2.0", "id": 0, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "radar-agent", "version": "1.0"},
        },
    })
    sid = resp.headers.get("mcp-session-id")
    if sid:
        _session_id = sid


def call_tool(tool_name: str, params: dict, jwt: str, url: str = RADAR_URL) -> dict:
    """
    Call any Radar MCP tool by name with given params.
    Returns the result dict (or error dict).
    """
    headers = _get_headers(jwt)
    resp = requests.post(url, headers=headers, json={
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": params},
    })
    resp.raise_for_status()
    data = _parse_response(resp)

    if "error" in data:
        return {"error": data["error"]}

    # unwrap MCP content blocks - plain text/dict
    result = data.get("result", {})
    content = result.get("content", [])
    if content and content[0].get("type") == "text":
        try:
            return json.loads(content[0]["text"])
        except json.JSONDecodeError:
            return {"text": content[0]["text"]}
    return result