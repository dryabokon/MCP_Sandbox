# get_weather

## When to use
Call this tool whenever the user asks about the current weather in any city.

## Input
- `city` (string): name of a city, e.g. `"Kyiv"` or `"London"`

## Output
Returns a plain text summary of current conditions, e.g. `"Kyiv: 12°C, partly cloudy"`

## Notes
- Works for any city name in English
- If city is not found, returns a default sunny response
- Do not infer or guess weather — always call this tool
