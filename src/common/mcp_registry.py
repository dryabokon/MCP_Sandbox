import asyncio
import threading
from contextlib import AsyncExitStack
from typing import Optional

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client


class MCPToolRegistry:
    """
    Registry for MCP servers. Supports dynamic server registration matching
    the claude mcp add CLI pattern:

        agent.add_mcp_server("analytics-mcp", "sse",  "http://host:8080/sse")
        agent.add_mcp_server("explainer-mcp", "http", "http://host:5173/mcp/explainer")

    Internally runs a single persistent background event loop in a daemon thread
    so that async MCP sessions (and their AsyncExitStack) live for the full
    process lifetime and are never torn down by asyncio.run() recycling.
    """

    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.sessions: dict[str, ClientSession] = {}
        self.tool_to_server: dict[str, str] = {}
        self.anthropic_tools: list[dict] = []
        self._server_configs: list[dict] = []

        # Persistent background loop — created once, never closed until close().
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------------------------------------------------------
    def _run_loop(self):
        """Background thread: owns the event loop for all async MCP work."""
        self._loop.run_forever()

    def _run(self, coro):
        """Submit a coroutine to the background loop and block until done."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()  # propagates exceptions to caller

    # ------------------------------------------------------------------------------------------------------------------
    def add_server(
        self,
        name: str,
        transport: str,     # "sse" | "http"
        url: str,
        headers: Optional[dict] = None,
    ) -> "MCPToolRegistry":
        """
        Register an MCP server. Call before connect().
        Returns self for fluent chaining.
        """
        assert transport in ("sse", "http"), (
            f"Unknown transport '{transport}'. Use 'sse' or 'http'."
        )
        self._server_configs.append(
            {"name": name, "transport": transport, "url": url, "headers": headers or {}}
        )
        return self

    # ------------------------------------------------------------------------------------------------------------------
    def connect(self):
        """Blocking: open all registered MCP server connections."""
        self._run(self._connect_all())

    async def _connect_all(self):
        await self.exit_stack.__aenter__()
        for cfg in self._server_configs:
            await self._connect_one(
                cfg["name"], cfg["transport"], cfg["url"], cfg["headers"]
            )
        await self._refresh_tools()

    async def _connect_one(self, name: str, transport: str, url: str, headers: dict):
        if transport == "sse":
            read, write = await self.exit_stack.enter_async_context(
                sse_client(url=url, headers=headers)
            )
        else:  # "http"  (Streamable HTTP / MCP 2025-03-26)
            # streamable_http_client does NOT accept a headers kwarg in current mcp versions.
            # The result is a 3-tuple: (read_stream, write_stream, get_session_fn).
            result = await self.exit_stack.enter_async_context(
                streamable_http_client(url=url)
            )
            read, write = result[0], result[1]

        session = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await session.initialize()
        self.sessions[name] = session
        print(f"[MCP] Connected: {name} ({transport}) - {url}")

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _sanitize_schema(schema: dict) -> dict:
        """
        Remove JSON Schema keywords unsupported by some LLM backends.
        Vertex AI / Gemini rejects exclusiveMaximum, exclusiveMinimum, etc.
        Recurses through the full schema tree.
        """
        UNSUPPORTED = {"exclusiveMaximum", "exclusiveMinimum", "$schema", "additionalItems"}
        if not isinstance(schema, dict):
            return schema
        return {
            k: MCPToolRegistry._sanitize_schema(v)
            for k, v in schema.items()
            if k not in UNSUPPORTED
        }

    # ------------------------------------------------------------------------------------------------------------------
    async def _refresh_tools(self):
        self.anthropic_tools = []
        self.tool_to_server = {}

        for server_name, session in self.sessions.items():
            resp = await session.list_tools()
            for tool in resp.tools:
                self.tool_to_server[tool.name] = server_name
                self.anthropic_tools.append({
                    "name": tool.name,
                    "description": tool.description or f"MCP tool from {server_name}",
                    "input_schema": self._sanitize_schema(tool.inputSchema),
                })
            print(f"  [MCP] {server_name}: {len(resp.tools)} tools registered")

    # ------------------------------------------------------------------------------------------------------------------
    def call_tool(self, tool_name: str, tool_input: dict) -> str:
        """Blocking: call a remote MCP tool and return its text content."""
        return self._run(self._call_tool_async(tool_name, tool_input))

    async def _call_tool_async(self, tool_name: str, tool_input: dict) -> str:
        server_name = self.tool_to_server[tool_name]
        session = self.sessions[server_name]
        result = await session.call_tool(tool_name, tool_input)
        parts = [block.text for block in result.content if hasattr(block, "text")]
        return "\n".join(parts) if parts else "(no output)"

    # ------------------------------------------------------------------------------------------------------------------
    def close(self):
        """Blocking: clean up all MCP sessions and stop the background loop."""
        self._run(self.exit_stack.__aexit__(None, None, None))
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)