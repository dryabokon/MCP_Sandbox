import anthropic
import subprocess
import json
import os
import re
import sys
import traceback
from typing import Dict, Optional
from src.common import switch_llm_proxy
# ----------------------------------------------------------------------------------------------------------------------
from src.common.run_logger import RunLogger, capture_stdio
from src.common.mcp_registry import MCPToolRegistry
from src.common.tools_dispatcher import ToolDispatcher
# ----------------------------------------------------------------------------------------------------------------------
class AgentRunner:
    def __init__(
        self,
        agent_name: str,
        prompt_path: str,
        tools: Dict[str, object],
        llm_provider = None,
        max_iterations: int = 10,
        max_tokens: int = 1024,
        mcp_registry: Optional[MCPToolRegistry] = None,
    ):

        switch_llm_proxy.setup_env_variables(llm_provider)       #'gemini' | 'openai'

        self.agent_name = agent_name
        self.system_prompt = self.load_text_file(os.path.join(os.path.dirname(__file__), prompt_path))
        self.tools = tools
        self.is_ready = False
        api_key = self.get_api_key()
        self.error_msg = "ERROR: No API key found. Please set environment variable ANTHROPIC_API_KEY"
        if not api_key:
            print(self.error_msg)
        else:
            self.is_ready = True

        model, self.provider = self.get_model_and_provider()
        print(f"Using {model} from {self.provider}")


        self.model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        self.base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        self.max_iterations = max_iterations
        self.max_tokens = max_tokens
        self.client = anthropic.Anthropic(api_key=api_key, base_url=self.base_url)

        self.mcp_registry: MCPToolRegistry = mcp_registry or MCPToolRegistry()
        self._mcp_connected = False
        self._dispatcher: Optional[ToolDispatcher] = None   # built after MCP connects

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def _is_native(self) -> bool:
        return self.provider.lower() == "anthropic"

    # ------------------------------------------------------------------------------------------------------------------
    def add_mcp_server(self, name: str, transport: str, url: str, headers: Optional[dict] = None) -> "AgentRunner":
        self.mcp_registry.add_server(name, transport, url, headers)
        return self

    # ------------------------------------------------------------------------------------------------------------------
    def _ensure_mcp_connected(self):
        if self._mcp_connected:
            return
        if self.mcp_registry._server_configs:
            print("\n[MCP] Connecting to registered servers …")
            self.mcp_registry.connect()
        self._mcp_connected = True
        self._dispatcher = ToolDispatcher(self.tools, self.mcp_registry)

    # ------------------------------------------------------------------------------------------------------------------
    def get_model_and_provider(self):
        ANTHROPIC_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "Empty")
        if ANTHROPIC_BASE_URL not in ["http://localhost:8082", "http://localhost:8083"]:
            provider = "Anthropic"
            model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        else:
            container_name = "llm-proxy-gemini" if ANTHROPIC_BASE_URL == "http://localhost:8082" else "llm-proxy-openai"
            provider = subprocess.check_output(["docker", "exec", container_name, "/bin/sh", "-lc", 'printf "%s" "${PREFERRED_PROVIDER:-unknown}"'], text=True).strip()
            model    = subprocess.check_output(["docker", "exec", container_name, "/bin/sh", "-lc", 'printf "%s" "${SMALL_MODEL:-${BIG_MODEL:-}}"'], text=True).strip()
        return model, provider

    # ------------------------------------------------------------------------------------------------------------------
    def get_api_key(self) -> Optional[str]:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if key:
            return key
        claude_json = os.path.expanduser("~/.claude.json")
        if os.path.exists(claude_json):
            with open(claude_json, "r", encoding="utf-8") as f:
                return json.load(f).get("primaryApiKey")
        return None

    # ------------------------------------------------------------------------------------------------------------------
    def load_text_file(self, filename: str) -> str:
        with open(filename, "r", encoding="utf-8", errors="replace") as f:
            return f.read().strip()

    # ------------------------------------------------------------------------------------------------------------------
    def extract_tool_calls_from_text(self, text: str) -> list[dict]:
        calls = []
        pattern = r"Tool:\s*(\w+)\s*\nArguments:\s*(\{.*?\})"
        for match in re.finditer(pattern, text, re.DOTALL):
            tool_name = match.group(1).strip()
            try:
                tool_input = json.loads(match.group(2).strip())
            except json.JSONDecodeError:
                continue
            calls.append({"name": tool_name, "input": tool_input})
        return calls

    # ------------------------------------------------------------------------------------------------------------------
    def _run_tool(self, tool_name: str, tool_input: dict, logger: RunLogger) -> str:
        """Single tool execution with logging. Returns result string."""
        print(f"\n  - Tool call : {tool_name}({tool_input})")
        result, latency_ms = self._dispatcher.dispatch(tool_name, tool_input)
        print(f"  - Tool result: {result}")
        logger.event("tool_call",   {"tool": tool_name, "input": tool_input})
        logger.tool(tool_name, tool_input, result, latency_ms=latency_ms)
        logger.event("tool_result", {"tool": tool_name, "output": result, "latency_ms": latency_ms})
        return result

    # ------------------------------------------------------------------------------------------------------------------
    def _handle_native_tool_use(self, response, messages, logger) -> bool:
        """
        Native Anthropic: proper tool_use blocks with IDs.
        Must echo full content blocks as assistant turn so IDs match.
        """
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = self._run_tool(block.name, block.input, logger)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })

        if not tool_results:
            return False

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user",      "content": tool_results})
        return True

    # ------------------------------------------------------------------------------------------------------------------
    def _handle_proxy_tool_use(self, response, messages, logger) -> bool:
        """
        Proxy (Gemini/OpenAI): tool calls embedded as text.
        Echo plain text as assistant turn; feed results back as user turn.
        """
        text = next((b.text for b in response.content if hasattr(b, "text")), "")
        tool_calls = self.extract_tool_calls_from_text(text)
        if not tool_calls:
            return False

        logger.event("assistant", {"text": text, "mode": "proxy_tool_request"})
        results = [
            f"{c['name']} result: {self._run_tool(c['name'], c['input'], logger)}"
            for c in tool_calls
        ]
        messages.append({"role": "assistant", "content": text})
        messages.append({
            "role": "user",
            "content": f"Tool results:\n{chr(10).join(results)}\n\nNow answer the original question.",
        })
        return True

    # ------------------------------------------------------------------------------------------------------------------
    def run(self, user_message: str) -> str:
        if not self.is_ready:
            return self.error_msg

        self._ensure_mcp_connected()

        logger = RunLogger(experiment=self.agent_name, run_name="manual")
        capture_stdio(logger.dir)

        logger.log_meta({
            "script":         os.path.basename(sys.argv[0]),
            "agent":          self.agent_name,
            "model":          self.model,
            "base_url":       self.base_url,
            "max_iterations": self.max_iterations,
        })
        logger.log_config({
            "model":          self.model,
            "base_url":       self.base_url,
            "max_iterations": self.max_iterations,
            "max_tokens":     self.max_tokens,
            "local_tools":    list(self.tools.keys()),
            "mcp_tools":      list(self.mcp_registry.tool_to_server.keys()),
        })
        logger.save_text("prompt_system.md", self.system_prompt)
        logger.save_text("prompt_user.md",   user_message)

        tools    = [t.get_definition() for t in self.tools.values()] + self.mcp_registry.anthropic_tools
        messages = [{"role": "user", "content": user_message}]
        logger.event("user", {"text": user_message})

        print(f"\n{'=' * 60}")
        print(f"USER: {user_message}")
        print(f"{'=' * 60}")

        try:
            for iteration in range(self.max_iterations):
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=self.system_prompt,
                    tools=tools,
                    messages=messages,
                )
                logger.event("llm_response", {
                    "iteration":   iteration + 1,
                    "stop_reason": response.stop_reason,
                })
                print(f"\n[stop_reason: {response.stop_reason}  iteration: {iteration + 1}]")

                # ── tool_use ──────────────────────────────────────────────────
                if response.stop_reason == "tool_use":
                    handler = self._handle_native_tool_use if self._is_native else self._handle_proxy_tool_use
                    if handler(response, messages, logger):
                        continue

                # ── end_turn: proxy may still embed tool calls ─────────────────
                if response.stop_reason == "end_turn" and not self._is_native:
                    if self._handle_proxy_tool_use(response, messages, logger):
                        continue

                # ── final answer ───────────────────────────────────────────────
                text = next((b.text for b in response.content if hasattr(b, "text")), "")
                print(f"\nASSISTANT: {text}")
                logger.event("assistant", {"text": text})
                logger.save_text("response_final.md", text)
                if hasattr(response, "usage"):
                    logger.usage(response.usage, extra={"model": self.model})
                logger.finalize("finished")
                return text

            print("ERROR: max iterations reached")
            logger.save_text("response_final.md", "")
            logger.finalize("max_iterations")
            return ""

        except Exception:
            logger.save_text("traceback.txt", traceback.format_exc())
            logger.finalize("failed")
            raise