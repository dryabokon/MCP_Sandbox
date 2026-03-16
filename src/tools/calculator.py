import os
# ------------------------------------------------------------------------------------------
_HERE = os.path.dirname(__file__)
description = open(os.path.join(_HERE, "../../.claude/tools/calculator.md")).read().strip()
# ----------------------------------------------------------------------------------------------------------------------
def get_definition():
    """Load description from .md, return tool schema."""
    return {
        "name": os.path.basename(__file__).replace(".py", ""),
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The expression to evaluate."
                }
            }
        }
    }
# ----------------------------------------------------------------------------------------------------------------------
def run(expression: str) -> str:
    """Execute the tool."""
    try:
        result = eval(expression, {"__builtins__": {}})
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error: {e}"
