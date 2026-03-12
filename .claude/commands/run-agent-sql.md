# test-agent

Run a quick smoke test of the agent with the test query: "$ARGUMENTS"

Steps:
1. Find the agent script — check these paths in order:
   - `src/agents/agent_SQLServerClient.py`
2. Check `.claude/agents/agent_SQLServerClient.md` exists
3. Run: `python src/agents/agent_SQLServerClient.py "$ARGUMENTS"`
   - Do NOT modify any source files
   - Do NOT hardcode the query — pass it as a command-line argument exactly as shown above

After running:
1. Show full tool call trace (tools called, inputs, results)
2. Show final assistant response
3. Verdict: did agent follow rules in `.claude/agents/agent_SQLServerClient.md`?