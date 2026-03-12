import anthropic
import subprocess
import json
import os
import re
import sys
import time
import traceback
from typing import Dict, Optional
import platform

from src.common.run_logger import RunLogger, capture_stdio
from src.common import switch_llm_proxy
# ----------------------------------------------------------------------------------------------------------------------
class AgentRunner:
    def __init__(
        self,
        agent_name: str,
        prompt_path: str,
        tools: Dict[str, object],
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        max_iterations: int = 10,
        max_tokens: int = 1024,
        experiment: Optional[str] = None,
    ):

        # if platform.system() == "Windows":
        #     switch_llm_proxy.setup_windows_env_variables(proxy_mode="off")

        self.agent_name = agent_name
        self.system_prompt = self.load_text_file(os.path.join(os.path.dirname(__file__), prompt_path))
        self.tools = tools
        self.is_ready = False
        api_key = self.get_api_key()
        self.error_msg = 'ERROR: No API key found. Please set environment variable ANTHROPIC_API_KEY'
        if not api_key:
            print(self.error_msg)
        else:
            self.is_ready = True

        self.print_model_and_provider()

        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        self.base_url = base_url or os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        self.max_iterations = max_iterations
        self.max_tokens = max_tokens
        self.experiment = experiment or agent_name


        self.client = anthropic.Anthropic(api_key=api_key,base_url=self.base_url)

        return

    # ------------------------------------------------------------------------------------------------------------------
    def print_model_and_provider(self):
        ANTHROPIC_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "Empty")
        if ANTHROPIC_BASE_URL =='http://localhost:8082':
            provider = subprocess.check_output(["docker", "exec", "llm-proxy", "/bin/sh", "-lc", 'printf "%s" "${PREFERRED_PROVIDER:-unknown}"'],text=True).strip()
            model = subprocess.check_output(["docker", "exec", "llm-proxy", "/bin/sh", "-lc", 'printf "%s" "${SMALL_MODEL:-${BIG_MODEL:-}}"'],text=True).strip()
        else:
            provider = 'Anthropic'
            model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")

        print('--------------------------------')
        print(f"Using {model} from {provider}")
        print('--------------------------------')
        return
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
    def load_text_file(self,filename: str) -> str:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read().strip()

    # ------------------------------------------------------------------------------------------------------------------
    def extract_tool_calls_from_text(self,text: str) -> list[dict]:
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
    def execute_tools(self, tool_calls: list[dict], logger: RunLogger) -> str:
        results = []

        for call in tool_calls:
            tool_name = call["name"]
            tool_input = call["input"]

            print(f"\n  - Tool call : {tool_name}({tool_input})")
            ts0 = time.perf_counter()

            tool_module = self.tools.get(tool_name)
            result = tool_module.run(**tool_input) if tool_module else f"Unknown tool: {tool_name}"

            latency_ms = int((time.perf_counter() - ts0) * 1000)
            print(f"  - Tool result: {result}")

            logger.event("tool_call", {"tool": tool_name, "input": tool_input})
            logger.tool(tool_name, tool_input, result, latency_ms=latency_ms)
            logger.event("tool_result", {"tool": tool_name, "output": result, "latency_ms": latency_ms})

            results.append(f"{tool_name} result: {result}")

        return "\n".join(results)

    # ------------------------------------------------------------------------------------------------------------------
    def run(self, user_message: str) -> str:
        logger = RunLogger(experiment=self.experiment, run_name="manual")
        capture_stdio(logger.dir)

        logger.log_meta({
            "script": os.path.basename(sys.argv[0]),
            "agent": self.agent_name,
            "model": self.model,
            "base_url": self.base_url,
            "max_iterations": self.max_iterations,
        })
        logger.log_config({
            "model": self.model,
            "base_url": self.base_url,
            "max_iterations": self.max_iterations,
            "max_tokens": self.max_tokens,
            "tools": list(self.tools.keys()),
        })
        logger.save_text("prompt_system.md", self.system_prompt)
        logger.save_text("prompt_user.md", user_message)

        logger.event("user", {"text": user_message})
        messages = [{"role": "user", "content": user_message}]
        if not self.is_ready:
            return self.error_msg

        print(f"\n{'=' * 60}")
        print(f"USER: {user_message}")
        print(f"{'=' * 60}")

        try:
            for iteration in range(self.max_iterations):
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=self.system_prompt,
                    tools=[t.get_definition() for t in self.tools.values()],
                    messages=messages,
                )

                logger.event("llm_response", {
                    "iteration": iteration + 1,
                    "stop_reason": response.stop_reason,
                })

                print(f"\n[stop_reason: {response.stop_reason}  iteration: {iteration + 1}]")

                if response.stop_reason == "tool_use":
                    messages.append({"role": "assistant", "content": response.content})

                    tool_results = []
                    for block in response.content:
                        if block.type != "tool_use":
                            continue

                        print(f"\n  - Tool call : {block.name}({block.input})")
                        ts0 = time.perf_counter()

                        tool_module = self.tools.get(block.name)
                        result = tool_module.run(**block.input) if tool_module else f"Unknown tool: {block.name}"

                        latency_ms = int((time.perf_counter() - ts0) * 1000)
                        print(f"  - Tool result: {result}")

                        logger.event("tool_call", {"tool": block.name, "input": block.input})
                        logger.tool(block.name, block.input, result, latency_ms=latency_ms)
                        logger.event("tool_result", {"tool": block.name, "output": result, "latency_ms": latency_ms})

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                    messages.append({"role": "user", "content": tool_results})
                    continue

                if response.stop_reason == "end_turn":
                    text = next((b.text for b in response.content if hasattr(b, "text")), "")

                    tool_calls = self.extract_tool_calls_from_text(text)
                    if tool_calls:
                        logger.event("assistant", {"text": text, "mode": "proxy_tool_request"})
                        results_text = self.execute_tools(tool_calls, logger)

                        messages.append({"role": "assistant", "content": text})
                        messages.append({
                            "role": "user",
                            "content": f"Tool results:\n{results_text}\n\nNow answer the original question."
                        })
                        continue

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

        return