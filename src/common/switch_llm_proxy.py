import os
import subprocess
from pathlib import Path
# ---------------------------------------------------------------------------------------------------------------------
def setup_windows_env_variables(proxy_mode="off"):
    if proxy_mode == "on":
        provider = subprocess.check_output(["docker","exec","llm-proxy","/bin/sh","-lc",'printf "%s" "${PREFERRED_PROVIDER:-unknown}"'],text=True).strip()
        model = subprocess.check_output(["docker","exec","llm-proxy","/bin/sh","-lc",'printf "%s" "${SMALL_MODEL:-${BIG_MODEL:-}}"'],text=True).strip()
        if not model:
            print("Could not detect model from llm-proxy container")

        os.environ["ANTHROPIC_API_KEY"] = "dummy"
        os.environ["ANTHROPIC_BASE_URL"] = "http://localhost:8082"
        os.environ["ANTHROPIC_MODEL"] = "claude-sonnet-4-5"
        print(f"[WINDOWS]: Switched to {model} from {provider}")

    else:
        p = Path(os.path.dirname(__file__))
        key_file = p.parents[1] / 'infra/llm-proxy/secret_key_anthropic.txt'

        with open(key_file) as f:
            key = f.read().strip()
        os.environ["ANTHROPIC_API_KEY"] = key
        os.environ.pop("ANTHROPIC_BASE_URL", None)
        os.environ["ANTHROPIC_MODEL"] = "claude-sonnet-4-5"

        print("[WINDOWS]: Switched to native Anthropic")
