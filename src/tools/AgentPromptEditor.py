from pathlib import Path
import json
import os
import shutil
from typing import Optional

# ----------------------------------------------------------------------------------------------------------------------
def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]

# ----------------------------------------------------------------------------------------------------------------------
def _agents_dir() -> Path:
    return _repo_root() / ".claude" / "agents"

# ----------------------------------------------------------------------------------------------------------------------
def _safe_target(filename: str) -> Optional[Path]:
    if not filename:
        return None

    # only plain filenames, no folders
    name = os.path.basename(filename)
    if name != filename:
        return None

    if not name.endswith(".md"):
        return None

    if not name.startswith("agent_"):
        return None

    target = (_agents_dir() / name).resolve()
    agents_dir = _agents_dir().resolve()

    try:
        target.relative_to(agents_dir)
    except ValueError:
        return None

    return target

# ----------------------------------------------------------------------------------------------------------------------
def get_definition():
    return {
        "name": "AgentPromptEditor",
        "description": (
            "Safely read or rewrite agent prompt markdown files under .claude/agents only. "
            "Use only when explicitly asked to improve or update an agent prompt."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["read", "rewrite"]
                },
                "filename": {
                    "type": "string",
                    "description": "Example: agent_SQLServerClient.md"
                },
                "content": {
                    "type": "string",
                    "description": "Full new file content for rewrite action"
                },
                "allow_self_modify": {
                    "type": "boolean",
                    "description": "Must be true to allow rewrite"
                },
                "create_backup": {
                    "type": "boolean",
                    "description": "Whether to create .bak backup before overwrite"
                }
            },
            "required": ["action", "filename"]
        }
    }

# ----------------------------------------------------------------------------------------------------------------------
def run(
    action: str,
    filename: str,
    content: Optional[str] = None,
    allow_self_modify: bool = False,
    create_backup: bool = True,
) -> str:

    target = _safe_target(filename)
    if target is None:
        return "ERROR: Only .claude/agents/agent_*.md filenames in the agents folder are allowed"

    if action == "read":
        if not target.exists():
            return f"ERROR: File not found: {target.name}"
        return target.read_text(encoding="utf-8")

    if action == "rewrite":
        if not allow_self_modify:
            return "ERROR: rewrite denied because allow_self_modify=false"

        if content is None or not content.strip():
            return "ERROR: content is required for rewrite"

        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists() and create_backup:
            backup_path = target.with_suffix(target.suffix + ".bak")
            shutil.copy2(target, backup_path)

        tmp_path = target.with_suffix(target.suffix + ".tmp")
        tmp_path.write_text(content.strip() + "\n", encoding="utf-8")
        tmp_path.replace(target)

        return f"OK: rewritten {target.name}"

    return f"ERROR: Unsupported action: {action}"

# ----------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    print(json.dumps(get_definition(), indent=2))