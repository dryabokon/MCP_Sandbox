import os
import sys
# ---------------------------------------------------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))
# ---------------------------------------------------------------------------------------------------------------------
from src.common.agent_runner import AgentRunner
from src.tools import SQLServerClient
from src.tools import AgentPromptEditor
# ---------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    RUNNER = AgentRunner(agent_name="agent_SQLServerClient",prompt_path="../../.claude/agents/agent_SQLServerClient.md",
                         tools={"SQLServerClient": SQLServerClient,"AgentPromptEditor": AgentPromptEditor},
                         experiment="agent_SQLServerClient")
    query = sys.argv[1] if len(sys.argv) > 1 else "List available tables in schema imdb"
    RUNNER.run(query)