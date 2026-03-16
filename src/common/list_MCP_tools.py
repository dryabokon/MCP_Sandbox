import os
import json
import requests
import pandas as pd
from tabulate import tabulate
import threading
from dotenv import load_dotenv
from pathlib import Path
# ----------------------------------------------------------------------------------------------------------------------
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
# ----------------------------------------------------------------------------------------------------------------------
def get_tools(url: str, extra_headers: dict = None) -> pd.DataFrame:
    if "/sse" in url:
        return _get_tools_sse(url, extra_headers)
    else:
        return _get_tools_http(url, extra_headers)
# ----------------------------------------------------------------------------------------------------------------------
def get_tools_v1(URL):
    """HTTP transport (Streamable HTTP). Kept for backward compatibility."""
    return _get_tools_http(URL)
# ----------------------------------------------------------------------------------------------------------------------
def get_tools_v2(URL):
    """SSE transport. Kept for backward compatibility."""
    return _get_tools_sse(URL)
# ----------------------------------------------------------------------------------------------------------------------
def _get_tools_http(url: str, extra_headers: dict = None) -> pd.DataFrame:
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if extra_headers:
        headers.update(extra_headers)

    init_resp = requests.post(url, headers=headers, json={
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "python", "version": "1.0"}},
    })
    session_id = init_resp.headers.get("mcp-session-id")
    if session_id:
        headers["mcp-session-id"] = session_id

    tools_resp = requests.post(url, headers=headers, json={
        "jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {},
    })

    # handle both SSE-wrapped and plain JSON responses
    ct = tools_resp.headers.get("Content-Type", "")
    if "text/event-stream" in ct or tools_resp.text.lstrip().startswith("data:"):
        for line in tools_resp.text.splitlines():
            if line.startswith("data:"):
                data = json.loads(line[5:])
                tools = data.get("result", {}).get("tools")
                if tools is not None:
                    return _to_df(tools)
    else:
        tools = tools_resp.json().get("result", {}).get("tools")
        if tools is not None:
            return _to_df(tools)

    return pd.DataFrame()
# ----------------------------------------------------------------------------------------------------------------------
def _get_tools_sse(url: str, extra_headers: dict = None) -> pd.DataFrame:
    base = url[: url.rfind("/sse")] if "/sse" in url else url.rstrip("/")

    session_path = None
    tools_result = None
    ready = threading.Event()
    done  = threading.Event()

    sse_headers = {"Accept": "text/event-stream"}
    if extra_headers:
        sse_headers.update(extra_headers)

    def listen_sse():
        nonlocal session_path, tools_result
        current_event = None
        with requests.get(url, stream=True, headers=sse_headers) as r:
            for raw in r.iter_lines():
                if done.is_set():
                    break
                if not raw:
                    current_event = None
                    continue
                line = raw.decode()
                if line.startswith("event:"):
                    current_event = line.replace("event:", "").strip()
                elif line.startswith("data:"):
                    data = line.replace("data:", "").strip()
                    if current_event == "endpoint" and session_path is None:
                        session_path = data
                        ready.set()
                    elif current_event == "message":
                        try:
                            msg = json.loads(data)
                            if msg.get("id") == 2:
                                tools_result = msg["result"]["tools"]
                                done.set()
                        except Exception:
                            pass

    t = threading.Thread(target=listen_sse, daemon=True)
    t.start()
    ready.wait(timeout=5)

    post_headers = {"Content-Type": "application/json"}
    if extra_headers:
        post_headers.update(extra_headers)

    def post(msg_id, method, params):
        requests.post(f"{base}{session_path}",
                      headers=post_headers,
                      json={"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params})

    post(1, "initialize", {"protocolVersion": "2024-11-05",
                           "clientInfo": {"name": "python", "version": "1.0"},
                           "capabilities": {}})
    post(2, "tools/list", {})

    done.wait(timeout=10)
    t.join(timeout=1)
    return _to_df(tools_result) if tools_result else pd.DataFrame()
# ----------------------------------------------------------------------------------------------------------------------
def _to_df(tools: list) -> pd.DataFrame:
    rows = []
    for tool in tools:
        props    = tool.get("inputSchema", {}).get("properties", {})
        required = tool.get("inputSchema", {}).get("required", [])
        rows.append({
            "name":        tool["name"],
            "description": tool.get("description", ""),
            "params":      ", ".join(props.keys()),
            "required":    ", ".join(required),
        })
    return pd.DataFrame(rows)
# ----------------------------------------------------------------------------------------------------------------------
def prettify(df, showheader=True, showindex=False, tablefmt='psql'):
    if df.shape[0] == 0 or df.shape[1] == 0:
        return ''
    df_fmt = df.copy()
    for col in df_fmt.select_dtypes(include=['float']):
        df_fmt[col] = df_fmt[col].map(lambda x: format(x, '.2f'))
    return tabulate(df_fmt, headers=df_fmt.columns if showheader else [],
                    tablefmt=tablefmt, showindex=showindex)
# ----------------------------------------------------------------------------------------------------------------------
URL_MCP_tools1 = "http://127.0.0.1:8931/mcp"
URL_MCP_tools2 = "http://127.0.0.1:8933/mcp"
URL_MCP_tools3 = "http://127.0.0.1:8934/mcp"
# ----------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    df = get_tools(URL_MCP_tools1)
    df.drop(columns=["description"], inplace=True)
    print(prettify(df))

