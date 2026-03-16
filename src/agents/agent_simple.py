import os
import sys
# ---------------------------------------------------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))
agent_name   = os.path.basename(__file__).replace(".py", "")
prompt_path  = f"../../.claude/agents/{agent_name}.md"
# ---------------------------------------------------------------------------------------------------------------------
from src.common.agent_runner import AgentRunner
from src.tools import calculator, get_weather
# ---------------------------------------------------------------------------------------------------------------------
TOOLS       = {"calculator": calculator, "get_weather": get_weather}
MCP_SERVERS = []
# ---------------------------------------------------------------------------------------------------------------------
Q1 = "list your tools"
Q2 = "What is the weather in London?"
Q3 = "What is 2 and five?"
Q4 = "What is difference between temperature in Kyiv and London"
# ---------------------------------------------------------------------------------------------------------------------
query        = sys.argv[1] if len(sys.argv) > 1 else Q4
llm_provider = sys.argv[2] if len(sys.argv) > 2 else None
# ---------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    RUNNER = AgentRunner(str(agent_name), prompt_path, tools=TOOLS, llm_provider=llm_provider)
    RUNNER.run(query)
