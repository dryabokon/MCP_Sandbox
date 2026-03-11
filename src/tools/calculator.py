import os
_HERE = os.path.dirname(__file__)
description = open(os.path.join(_HERE, "../../.claude/tools/calculator.md")).read().strip()

def get_definition():
    """Load description from .md, return tool schema."""
    return {
        "name": "calculator",
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression to evaluate, e.g. '2 + 2' or '10 * 3.5'"
                }
            },
            "required": ["expression"]
        }
    }

def run(expression: str) -> str:
    """Execute the tool."""
    try:
        result = eval(expression, {"__builtins__": {}})
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error: {e}"
