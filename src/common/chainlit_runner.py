"""
chainlit_runner.py — async subclass of AgentRunner for Chainlit UI.
Drop into src/common/ alongside agent_runner.py.
"""
import asyncio
import json
import traceback

import chainlit as cl

from src.common.agent_runner import AgentRunner
from src.common.run_logger import RunLogger, capture_stdio


class ChainlitAgentRunner(AgentRunner):
    """
    Chainlit-aware AgentRunner. Constructor signature mirrors AgentRunner exactly:
        ChainlitAgentRunner(agent_name, prompt_path, tools=..., llm_provider=..., max_iterations=..., max_tokens=...)

    Usage inside a Chainlit app:
        runner = ChainlitAgentRunner(agent_name, prompt_path, tools=..., llm_provider=llm_provider)
        await runner.run_async(message.content)
    """

    # ------------------------------------------------------------------
    async def run_async(self, user_message: str) -> str:
        if not self.is_ready:
            await cl.Message(content=self.error_msg).send()
            return self.error_msg

        self._ensure_mcp_connected()

        logger = RunLogger(experiment=self.agent_name, run_name="chainlit")
        capture_stdio(logger.dir)
        logger.log_meta({
            "script":         "chainlit",
            "agent":          self.agent_name,
            "model":          self.model,
            "base_url":       self.base_url,
            "max_iterations": self.max_iterations,
        })
        logger.log_config({
            "model":       self.model,
            "base_url":    self.base_url,
            "max_tokens":  self.max_tokens,
            "local_tools": list(self.tools.keys()),
            "mcp_tools":   list(self.mcp_registry.tool_to_server.keys()),
        })
        logger.save_text("prompt_system.md", self.system_prompt)
        logger.save_text("prompt_user.md",   user_message)
        logger.event("user", {"text": user_message})

        tools    = [t.get_definition() for t in self.tools.values()] + self.mcp_registry.anthropic_tools
        messages = [{"role": "user", "content": user_message}]

        reply = cl.Message(content="")
        await reply.send()
        loop = asyncio.get_event_loop()

        try:
            for iteration in range(self.max_iterations):
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.messages.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        system=self.system_prompt,
                        tools=tools,
                        messages=messages,
                    ),
                )
                logger.event("llm_response", {"iteration": iteration + 1, "stop_reason": response.stop_reason})

                if response.stop_reason == "tool_use":
                    handler = self._handle_native_tool_use_async if self._is_native else self._handle_proxy_tool_use_async
                    if await handler(response, messages, logger):
                        continue

                if response.stop_reason == "end_turn" and not self._is_native:
                    if await self._handle_proxy_tool_use_async(response, messages, logger):
                        continue

                text = next((b.text for b in response.content if hasattr(b, "text")), "")
                logger.event("assistant", {"text": text})
                logger.save_text("response_final.md", text)
                if hasattr(response, "usage"):
                    logger.usage(response.usage, extra={"model": self.model})
                logger.finalize("finished")
                reply.content = text
                await reply.update()
                return text

            logger.finalize("max_iterations")
            reply.content = "⚠️ Max iterations reached without a final answer."
            await reply.update()
            return ""

        except Exception:
            tb = traceback.format_exc()
            logger.save_text("traceback.txt", tb)
            logger.finalize("failed")
            reply.content = f"❌ Error\n```\n{tb}\n```"
            await reply.update()
            raise

    # ------------------------------------------------------------------
    async def _run_tool_async(self, tool_name: str, tool_input: dict, logger: RunLogger) -> str:
        async with cl.Step(name=tool_name, type="tool") as step:
            step.input = json.dumps(tool_input, indent=2)
            result_str, latency_ms = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._dispatcher.dispatch(tool_name, tool_input)
            )
            step.output = result_str
        logger.event("tool_call",   {"tool": tool_name, "input": tool_input})
        logger.tool(tool_name, tool_input, result_str, latency_ms=latency_ms)
        logger.event("tool_result", {"tool": tool_name, "output": result_str, "latency_ms": latency_ms})
        return result_str

    # ------------------------------------------------------------------
    async def _handle_native_tool_use_async(self, response, messages, logger) -> bool:
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = await self._run_tool_async(block.name, block.input, logger)
            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
        if not tool_results:
            return False
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user",      "content": tool_results})
        return True

    # ------------------------------------------------------------------
    async def _handle_proxy_tool_use_async(self, response, messages, logger) -> bool:
        text = next((b.text for b in response.content if hasattr(b, "text")), "")
        tool_calls = self.extract_tool_calls_from_text(text)
        if not tool_calls:
            return False
        logger.event("assistant", {"text": text, "mode": "proxy_tool_request"})
        results = [f"{c['name']} result: {await self._run_tool_async(c['name'], c['input'], logger)}" for c in tool_calls]
        messages.append({"role": "assistant", "content": text})
        messages.append({"role": "user", "content": f"Tool results:\n{chr(10).join(results)}\n\nNow answer the original question."})
        return True