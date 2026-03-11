#!/bin/bash
export ANTHROPIC_API_KEY=dummy
export ANTHROPIC_BASE_URL=http://localhost:8082
export ANTHROPIC_MODEL=claude-sonnet-4-5
python src/agents/agent_simple.py "$1"
