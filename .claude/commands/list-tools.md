# list-tools

Read all `.md` files in the `tools/` folder.

For each tool, output a single line summary in this format:
`tool_name` — one sentence explaining what it does and when Claude calls it.

Then below the list, answer:
- Which tools are likely to be called together in the same request?
- Are there any overlapping responsibilities between tools?
- What tool is missing that would make this agent more capable?
