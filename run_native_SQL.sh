#!/bin/bash
if [ -z "$1" ]; then
	arg="Provide top 7 rated Movies linked with nconst nm0000093. Give names of the movies and who is the person we talk about"
	#arg="Explore the DB structure if imdb database. Suggest 3 most illustrative natural language questions to showcase power of MCP Agent to query this database considering it's structure"
	#arg="Who are the top 10 actors/actresses with the most movie credits, and what are their names?"
	#arg="Which movie director has directed the most highly-rated movies (with an average rating above 8.0), and what are the names of those movies?"
else
	arg="$1"
fi

python src/agents/agent_SQLServerClient.py "$arg"


