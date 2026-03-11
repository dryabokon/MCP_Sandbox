#!/bin/bash
unset ANTHROPIC_API_KEY ANTHROPIC_BASE_URL ANTHROPIC_MODEL
python src/agents/agent_simple.py "$1"
