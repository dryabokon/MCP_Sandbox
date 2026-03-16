import os
import sys
# ---------------------------------------------------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))
agent_name = str(os.path.basename(__file__).replace(".py", ""))
prompt_path = f"../../.claude/agents/{agent_name}.md"
# ---------------------------------------------------------------------------------------------------------------------
from src.common.agent_runner import AgentRunner
from src.tools import get_MCP_tools
# ---------------------------------------------------------------------------------------------------------------------
TOOLS = {"get_MCP_tools": get_MCP_tools}
MCP_SERVERS = []
# ---------------------------------------------------------------------------------------------------------------------
URL_MCP_tools1 = "http://127.0.0.1:8931/mcp"
URL_MCP_tools2 = "http://127.0.0.1:8933/mcp"
URL_MCP_tools3 = "http://127.0.0.1:8934/mcp"
# ---------------------------------------------------------------------------------------------------------------------
Q = f'list tools from {URL_MCP_tools3}'
# ---------------------------------------------------------------------------------------------------------------------
query = sys.argv[1] if len(sys.argv) > 1 else Q
llm_provider = sys.argv[2] if len(sys.argv) > 2 else None
# ---------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    RUNNER = AgentRunner(agent_name, prompt_path, tools=TOOLS, llm_provider=llm_provider)
    RUNNER.run(query)