import anthropic
import json
import os
import re
import sys
# ---------------------------------------------------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))
from src.tools import calculator, get_weather
# ---------------------------------------------------------------------------------------------------------------------
def _get_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    claude_json = os.path.expanduser("~/.claude.json")
    if os.path.exists(claude_json):
        return json.load(open(claude_json)).get("primaryApiKey")
    return None
# ---------------------------------------------------------------------------------------------------------------------
MODEL  = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
CLIENT = anthropic.Anthropic(api_key=_get_api_key(),base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"))
SYSTEM = open(os.path.join(os.path.dirname(__file__), "../../.claude/agents/agent_simple.md")).read().strip()
TOOLS = {"calculator": calculator,"get_weather": get_weather}
MAX_ITERATIONS = 10
# ---------------------------------------------------------------------------------------------------------------------
def extract_tool_calls_from_text(text: str) -> list[dict]:
    """
    Proxy returns tool calls as text like:
        Tool usage:
        Tool: calculator
        Arguments: { "expression": "123 * 456" }

    Parse all of them out and return as list of dicts.
    """
    calls = []
    # Match each Tool: ... Arguments: {...} block
    pattern = r"Tool:\s*(\w+)\s*\nArguments:\s*(\{.*?\})"
    for match in re.finditer(pattern, text, re.DOTALL):
        tool_name = match.group(1).strip()
        try:
            tool_input = json.loads(match.group(2).strip())
        except json.JSONDecodeError:
            continue
        calls.append({"name": tool_name, "input": tool_input})
    return calls
# ---------------------------------------------------------------------------------------------------------------------
def execute_tools(tool_calls: list[dict]) -> str:
    """Run all tool calls and return combined results as text."""
    results = []
    for call in tool_calls:
        tool_name  = call["name"]
        tool_input = call["input"]
        print(f"\n  → Tool call : {tool_name}({tool_input})")

        tool_module = TOOLS.get(tool_name)
        result = tool_module.run(**tool_input) if tool_module else f"Unknown tool: {tool_name}"
        print(f"  ← Tool result: {result}")
        results.append(f"{tool_name} result: {result}")
    return "\n".join(results)
# ---------------------------------------------------------------------------------------------------------------------
def run_agent(user_message: str) -> str:
    print(f"\n{'='*60}")
    print(f"USER: {user_message}")
    print(f"{'='*60}")

    messages = [{"role": "user", "content": user_message}]

    for iteration in range(MAX_ITERATIONS):
        response = CLIENT.messages.create(model=MODEL,max_tokens=1024,system=SYSTEM,tools=[t.get_definition() for t in TOOLS.values()],messages=messages)
        print(f"\n[stop_reason: {response.stop_reason}  iteration: {iteration+1}]")

        # ── Native tool_use blocks (real Anthropic API) ───────────────────────
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                print(f"\n  → Tool call : {block.name}({block.input})")
                tool_module = TOOLS.get(block.name)
                result = tool_module.run(**block.input) if tool_module else f"Unknown tool: {block.name}"
                print(f"  ← Tool result: {result}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

            messages.append({"role": "user", "content": tool_results})
            continue

        # ── end_turn: check if proxy embedded tool calls in text ─────────────
        if response.stop_reason == "end_turn":
            text = next((b.text for b in response.content if hasattr(b, "text")), "")

            # Proxy fallback — tool calls returned as text
            tool_calls = extract_tool_calls_from_text(text)
            if tool_calls:
                results_text = execute_tools(tool_calls)
                # Inject tool results back as a user message and loop
                messages.append({"role": "assistant", "content": text})
                messages.append({"role": "user",      "content": f"Tool results:\n{results_text}\n\nNow answer the original question."})
                continue

            print(f"\nASSISTANT: {text}")
            return text

    print("ERROR: max iterations reached")
    return ""
# ---------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "What is 1+1?"
    run_agent(query)