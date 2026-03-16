import os
import sys
# ---------------------------------------------------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))
agent_name = str(os.path.basename(__file__).replace(".py", ""))
prompt_path = f"../../.claude/agents/{agent_name}.md"
# ---------------------------------------------------------------------------------------------------------------------
from src.common.agent_runner import AgentRunner
from src.tools import SQLServerClient
# ---------------------------------------------------------------------------------------------------------------------
TOOLS = {"SQLServerClient": SQLServerClient}
MCP_SERVERS = [("fetch",      "http", "http://127.0.0.1:8931/mcp"),("filesystem", "http", "http://127.0.0.1:8933/mcp"),("slack",      "http", "http://127.0.0.1:8934/mcp")]
#MCP_SERVERS = [("slack",      "http", "http://127.0.0.1:8934/mcp")]
# ---------------------------------------------------------------------------------------------------------------------
# Q1 = "fetch https://dou.ua/lenta/news/why-hasnt-e-hryvnia-been-launched-yet/?from=strichnews and summarize your thoughts into 'DOU_summary.md'"
# Q1 += "Then post the result to Slack channel #general with header 'Test message for upcoming TechTalk' "
# ---------------------------------------------------------------------------------------------------------------------
Q1 =  "Provide top 7 rated Movies linked with nconst nm0000093. Give names of the movies and who is the person we talk about. Save result as nm0000093.txt file. Then post the result to Slack channel #general with header 'Test message for upcoming TechTalk' "
# ---------------------------------------------------------------------------------------------------------------------
query = sys.argv[1] if len(sys.argv) > 1 else Q1
llm_provider = sys.argv[2] if len(sys.argv) > 2 else None
# ---------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    RUNNER = AgentRunner(agent_name, prompt_path, tools=TOOLS, llm_provider=llm_provider)
    for name, transport, url in MCP_SERVERS:
        RUNNER.add_mcp_server(name, transport, url)
    RUNNER.run(query)