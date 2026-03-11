import os
_HERE = os.path.dirname(__file__)
description = open(os.path.join(_HERE, "../../.claude/tools/get_weather.md")).read().strip()

def get_definition():
    """Load description from .md, return tool schema."""
    return {
        "name": "get_weather",
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, e.g. 'Kyiv' or 'London'"
                }
            },
            "required": ["city"]
        }
    }

def run(city: str) -> str:
    """Execute the tool (stubbed data for demo)."""
    fake_data = {
        "kyiv":   "Kyiv: 12°C, partly cloudy",
        "london": "London: 8°C, rainy",
        "berlin": "Berlin: 10°C, overcast",
    }
    return fake_data.get(city.lower(), f"{city}: 20°C, sunny")
