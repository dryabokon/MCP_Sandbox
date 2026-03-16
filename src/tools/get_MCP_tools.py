import os
from dotenv import load_dotenv
from pathlib import Path
import src.common.list_MCP_tools as _lib
# ----------------------------------------------------------------------------------------------------------------------
_HERE = os.path.dirname(__file__)
description = open(os.path.join(_HERE, "../../.claude/tools/get_mcp_tools.md"), encoding="utf-8").read().strip()
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
# ----------------------------------------------------------------------------------------------------------------------
def get_definition():
    return {
        "name": os.path.basename(__file__).replace(".py", ""),
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": {
                "server_url": {
                    "type": "string",
                    "description": "MCP server URL. Use /sse suffix for SSE transport, plain URL for HTTP transport."
                },
                "format": {
                    "type": "string",
                    "enum": ["markdown", "json", "names"],
                    "description": "Output format: markdown (default), names (name list), json (full schema)"
                }
            },
            "required": ["server_url"]
        }
    }
# ----------------------------------------------------------------------------------------------------------------------
def run(server_url: str, format: str = "markdown") -> str:

    jwt = os.getenv("RADAR_JWT")
    df = _lib.get_tools(server_url,extra_headers={"Authorization": f"Bearer {jwt}"} if jwt else None)

    if df.empty:
        return "No tools returned by server."

    if format == "names":
        return "\n".join(df["name"].tolist())

    if format == "json":
        return df.to_json(orient="records", indent=2)

    # markdown (default)
    lines = [f"**{len(df)} tools** on `{server_url}`\n"]
    for _, row in df.iterrows():
        lines.append(f"### `{row['name']}`")
        lines.append(row.get("description", "_(no description)_"))
        if row.get("params"):
            required = set(row["required"].split(", ")) if row.get("required") else set()
            for p in row["params"].split(", "):
                req = " *(required)*" if p in required else ""
                lines.append(f"- `{p}`{req}")
        lines.append("")
    return "\n".join(lines)