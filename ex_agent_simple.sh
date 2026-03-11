#!/bin/bash
if [ -z "$1" ]; then
	arg="What is difference between temperature in Kyiv and London"
else
	arg="$1"
fi
unset ANTHROPIC_API_KEY ANTHROPIC_BASE_URL ANTHROPIC_MODEL
python src/agents/agent_simple.py "$arg"
