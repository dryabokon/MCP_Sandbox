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
MCP_SERVERS = []
# ---------------------------------------------------------------------------------------------------------------------
Q1 = "List available tables in schema imdb"
Q2 = "Provide top 7 rated Movies linked with nconst nm0000093. Give names of the movies and who is the person we talk about"
Q3 = "Explore the DB structure if imdb database. Suggest 3 most illustrative natural language questions to showcase power of MCP Agent to query this database considering it's structure"
Q4 = "Who are the top 10 actors/actresses gained the most votes for 8+ rated movies"
Q5 = "What movies are the most highly-rated with significant counts, list 7 of them and say who has directed them"
Q6 = "What movies have the most counts, list 7 of them by providing rating and count together with director and actors"
# ---------------------------------------------------------------------------------------------------------------------
query = sys.argv[1] if len(sys.argv) > 1 else Q1
llm_provider = sys.argv[2] if len(sys.argv) > 2 else None
# ---------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    RUNNER = AgentRunner(agent_name,prompt_path,tools=TOOLS,llm_provider=llm_provider)
    RUNNER.run(query)