import sys
import inspect
import importlib
from pathlib import Path
# ---------------------------------------------------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
# ---------------------------------------------------------------------------------------------------------------------
from mcp.server.fastmcp import FastMCP
# ---------------------------------------------------------------------------------------------------------------------
mcp = FastMCP("MCP Sandbox")
# ---------------------------------------------------------------------------------------------------------------------
def _tool_name(tool_def: dict, fallback: str) -> str:
    return tool_def.get("name", fallback)
# ---------------------------------------------------------------------------------------------------------------------
def _tool_description(tool_def: dict, fallback: str = "") -> str:
    return tool_def.get("description", fallback)
# ---------------------------------------------------------------------------------------------------------------------
def register_tool_module(module_name: str):
    module = importlib.import_module(module_name)

    if not hasattr(module, "get_definition") or not hasattr(module, "run"):
        return

    tool_def = module.get_definition()
    tool_name = _tool_name(tool_def, module_name.split(".")[-1])
    tool_desc = _tool_description(tool_def, f"{tool_name} tool")
    run_func = module.run
    sig = inspect.signature(run_func)
    params = list(sig.parameters.values())

    if len(params) != 1:
        raise ValueError(f"{module_name}.run must have exactly one argument")

    arg_name = params[0].name

    def wrapper(**kwargs):
        return str(run_func(**kwargs))

    wrapper.__name__ = tool_name
    wrapper.__signature__ = inspect.Signature(parameters=[inspect.Parameter(name=arg_name,kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,annotation=str)])
    mcp.tool(name=tool_name, description=tool_desc)(wrapper)
    return
# ---------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    tools_dir = ROOT / "tools"
    for path in tools_dir.glob("*.py"):
        if path.name.startswith("_"):
            continue
        module_name = f"tools.{path.stem}"
        register_tool_module(module_name)

    print("MCP custom server ready", file=sys.stderr, flush=True)
    mcp.run()