"""
chainlit_app.py — reads TOOLS and MCP_SERVERS directly from each agent_*.py.

Run:
  chainlit run src/common/chainlit_app.py -w
"""
import os, sys, importlib.util, glob, traceback

# Project root = two levels up from src/common/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, PROJECT_ROOT)

import chainlit as cl
from chainlit.input_widget import Select, Slider
from src.common.chainlit_runner import ChainlitAgentRunner

# ---------------------------------------------------------------------------
# Discover agents
# ---------------------------------------------------------------------------
AGENTS_DIR = os.path.join(PROJECT_ROOT, "src", "agents")

def _discover() -> dict:
    found = {}
    pattern = os.path.join(AGENTS_DIR, "agent_*.py")
    paths   = sorted(glob.glob(pattern))
    print(f"[chainlit] scanning {pattern}  ({len(paths)} files)")
    for path in paths:
        name = os.path.basename(path).replace(".py", "")
        try:
            spec = importlib.util.spec_from_file_location(name, path)
            mod  = importlib.util.module_from_spec(spec)
            # ensure the agent can resolve its own relative paths
            mod.__file__ = path
            spec.loader.exec_module(mod)
            if hasattr(mod, "TOOLS"):
                found[name] = mod
                print(f"[chainlit] {name}  tools={list(mod.TOOLS.keys())}  mcp={[s[0] for s in getattr(mod,'MCP_SERVERS',[])]}")
            else:
                print(f"[chainlit] {name}  (no TOOLS defined — add: TOOLS = {{...}})")
        except Exception:
            print(f"[chainlit] ✗ {name}  import error:")
            traceback.print_exc()
    return found

AGENTS = _discover()

if not AGENTS:
    print(f"\n[chainlit] ERROR: no agents found in {AGENTS_DIR}")
    print("[chainlit] Each agent_*.py must define:  TOOLS = {...}")
    sys.exit(1)

DEFAULT_AGENT    = os.environ.get("AGENT_NAME",   next(iter(AGENTS)))
DEFAULT_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic")

# ---------------------------------------------------------------------------
# Runner factory
# ---------------------------------------------------------------------------
def _build_runner(agent_name: str, llm_provider: str,
                  max_iterations: int, max_tokens: int) -> ChainlitAgentRunner:
    mod      = AGENTS[agent_name]
    provider = None if llm_provider == "anthropic" else llm_provider
    runner   = ChainlitAgentRunner(
        agent_name     = agent_name,
        prompt_path    = os.path.join(PROJECT_ROOT, ".claude", "agents", f"{agent_name}.md"),
        tools          = mod.TOOLS,
        llm_provider   = provider,
        max_iterations = max_iterations,
        max_tokens     = max_tokens,
    )
    for srv in getattr(mod, "MCP_SERVERS", []):
        runner.add_mcp_server(*srv)
    return runner

def _welcome(agent_name: str, provider: str) -> str:
    mod = AGENTS[agent_name]
    tools = mod.TOOLS
    mcps = getattr(mod, "MCP_SERVERS", [])

    parts = [f"`{agent_name}` · `{provider}`"]
    if tools:parts.append(f"**Tools:** {', '.join(f'`{t}`' for t in tools)}")
    if mcps:parts.append(f"**MCP:** {', '.join(f'`{s[0]}`' for s in mcps)}")
    return '\n'.join(parts) if len(parts) > 1 else parts[0]

# ---------------------------------------------------------------------------
# Chainlit lifecycle
# ---------------------------------------------------------------------------
@cl.on_chat_start
async def on_chat_start():

    agents    = list(AGENTS.keys())
    providers = ["anthropic", "openai", "gemini"]

    settings = await cl.ChatSettings([
        Select(id="agent_name",   label="Agent",        values=agents,
               initial_index=agents.index(DEFAULT_AGENT) if DEFAULT_AGENT in agents else 0),
        Select(id="llm_provider", label="LLM provider", values=providers,
               initial_index=providers.index(DEFAULT_PROVIDER) if DEFAULT_PROVIDER in providers else 0),
        Slider(id="max_iterations", label="Max iterations", initial=10,   min=1,   max=30,   step=1),
        Slider(id="max_tokens",     label="Max tokens",     initial=1024, min=256, max=8192, step=256),
    ]).send()

    agent_name   = settings.get("agent_name",   DEFAULT_AGENT)
    llm_provider = settings.get("llm_provider", DEFAULT_PROVIDER)
    cl.user_session.set("runner", _build_runner(agent_name, llm_provider,
        int(settings.get("max_iterations", 10)), int(settings.get("max_tokens", 1024))))

    await cl.Message(content=_welcome(agent_name, llm_provider)).send()


@cl.on_settings_update
async def on_settings_update(settings: dict):
    agent_name   = settings.get("agent_name",   DEFAULT_AGENT)
    llm_provider = settings.get("llm_provider", DEFAULT_PROVIDER)
    cl.user_session.set("runner", _build_runner(agent_name, llm_provider,
        int(settings.get("max_iterations", 10)), int(settings.get("max_tokens", 1024))))
    await cl.Message(content=_welcome(agent_name, llm_provider)).send()


@cl.on_message
async def on_message(message: cl.Message):
    runner: ChainlitAgentRunner = cl.user_session.get("runner")
    await runner.run_async(message.content)