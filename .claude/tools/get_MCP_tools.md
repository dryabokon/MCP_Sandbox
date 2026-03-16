# get_mcp_tools

## When to use
Call this tool when you need to discover what tools are available on a remote MCP server — for example before deciding which tool to call, when asked to summarize a server's capabilities, or when routing a task to the right server.

## Input
- `server_url` (string): the MCP server endpoint. Use the `/sse` suffix for SSE transport (e.g. `"http://host:8080/sse"`), or a plain URL for HTTP transport (e.g. `"http://host:5173/mcp/explainer"`)
- `format` (string, optional): output format — one of `"markdown"` (default), `"names"`, or `"json"`

## Output
Depending on `format`:
- `markdown` — human-readable list with tool names, descriptions, and parameters
- `names` — plain newline-separated list of tool names only
- `json` — full tool schema as returned by the server

## Notes
- Transport is detected automatically from the URL: `/sse` → SSE, otherwise HTTP
- Always call with `format="names"` first if you only need to check whether a specific tool exists
- Use `format="json"` if you need to inspect full input schemas before constructing a call