import os
import sys
# ---------------------------------------------------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))
# ---------------------------------------------------------------------------------------------------------------------
from src.common.agent_runner import AgentRunner
from src.tools import calculator, get_weather
# ---------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    RUNNER = AgentRunner(agent_name="agent_simple", prompt_path="../../.claude/agents/agent_simple.md", tools={"calculator": calculator,"get_weather": get_weather}, experiment="agent_simple")
    query = sys.argv[1] if len(sys.argv) > 1 else "list your tools?"
    RUNNER.run(query)