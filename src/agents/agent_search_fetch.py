import os
import sys
# ---------------------------------------------------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))
# ---------------------------------------------------------------------------------------------------------------------
from src.common.agent_runner import AgentRunner
# ---------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    RUNNER = AgentRunner(agent_name="agent_search_fetch", prompt_path="../../.claude/agents/agent_search_fetch.md", tools={}, experiment="agent_search_fetch")
    RUNNER.add_mcp_server("fetch", "http", "http://127.0.0.1:8931/mcp")
    RUNNER.add_mcp_server("filesystem", "http", "http://127.0.0.1:8933/mcp")
    RUNNER.add_mcp_server("slack", "http", "http://127.0.0.1:8934/mcp")

    Q = "fetch https://dou.ua/lenta/news/why-hasnt-e-hryvnia-been-launched-yet/?from=strichnews and summarize your thoughts into 'DOU_summary.md'"
    Q+= "Then post the result to Slack channel #general with header 'Test message for upcoming TechTalk' "

    query = sys.argv[1] if len(sys.argv) > 1 else Q
    RUNNER.run(query)