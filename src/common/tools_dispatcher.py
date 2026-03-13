import time
from typing import Dict, Any, Optional


# Per-tool argument normalizers
# Add a new entry here when a new local tool is registered.
# Each normalizer receives tool_input dict and returns a (possibly modified) dict.


def _normalize_sql_server_client(tool_input: dict) -> dict:
    """
    Proxies (Gemini/OpenAI) often omit the 'action' field and pass only 'sql'
    or 'table_name'. Infer the action from present keys.
    """
    if "action" in tool_input:
        return tool_input
    if "sql" in tool_input:
        return {"action": "query", **tool_input}
    if "table_name" in tool_input:
        return {"action": "describe_table", **tool_input}
    if "schema_name" in tool_input:
        return {"action": "list_tables", **tool_input}
    return {"action": "full_structure", **tool_input}


_NORMALIZERS: Dict[str, Any] = {
    "SQLServerClient": _normalize_sql_server_client,
}




class ToolDispatcher:
    """
    Routes tool calls to local tool modules or MCP servers.
    All errors are caught and returned as strings so the LLM can self-correct.
    """

    def __init__(self, tools: dict, mcp_registry):
        self.tools = tools                  # name - module with .run(**kwargs)
        self.mcp_registry = mcp_registry

    # --------------------------------------------------------------------------
    def dispatch(self, tool_name: str, tool_input: dict) -> tuple[str, int]:
        """
        Execute one tool call.
        Returns (result_str, latency_ms).
        Never raises � errors become result strings prefixed with 'ERROR:'.
        """
        normalizer = _NORMALIZERS.get(tool_name)
        if normalizer:
            tool_input = normalizer(tool_input)

        ts0 = time.perf_counter()
        try:
            result = self._call(tool_name, tool_input)
        except Exception as e:
            result = f"ERROR: {e}"
        latency_ms = int((time.perf_counter() - ts0) * 1000)
        return str(result), latency_ms

    # --------------------------------------------------------------------------
    def _call(self, tool_name: str, tool_input: dict) -> str:
        local = self.tools.get(tool_name)
        if local is not None:
            return local.run(**tool_input)
        if tool_name in self.mcp_registry.tool_to_server:
            return self.mcp_registry.call_tool(tool_name, tool_input)
        return f"Unknown tool: {tool_name}"

    # --------------------------------------------------------------------------
    def register_normalizer(self, tool_name: str, fn) -> None:
        """Allow callers to plug in additional normalizers at runtime."""
        _NORMALIZERS[tool_name] = fn