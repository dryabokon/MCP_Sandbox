import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
# ---------------------------------------------------------------------------------------------------------------------
class RunLogger:
    def __init__(
        self,
        runs_root: str = "runs",
        experiment: str = "default",
        run_name: Optional[str] = None,
    ):
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        run_id = f"{ts}_{run_name}" if run_name else ts

        self.dir = Path(runs_root) / experiment / run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "artifacts").mkdir(exist_ok=True)

        self._conversation_f = open(self.dir / "conversation.jsonl", "a", encoding="utf-8")
        self._tools_f = open(self.dir / "tools.jsonl", "a", encoding="utf-8")

        self.meta: Dict[str, Any] = {
            "run_id": run_id,
            "experiment": experiment,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "status": "running",
        }

    # ---------- core ----------
    def finalize(self, status: str = "finished"):
        self.meta["status"] = status
        self.meta["finished_at"] = datetime.utcnow().isoformat() + "Z"
        self._write_json("meta.json", self.meta)
        self._conversation_f.close()
        self._tools_f.close()

    # ---------- meta / config ----------
    def log_meta(self, data: Dict[str, Any]):
        self.meta.update(data)
        self._write_json("meta.json", self.meta)

    def log_config(self, data: Dict[str, Any]):
        self._write_json("config.json", data)

    # ---------- text files ----------
    def save_text(self, filename: str, text: str):
        (self.dir / filename).write_text(text, encoding="utf-8")

    def save_artifact(self, name: str, content: bytes):
        (self.dir / "artifacts" / name).write_bytes(content)

    # ---------- events ----------
    def event(self, type_: str, payload: Dict[str, Any]):
        row = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "type": type_,
            **payload,
        }
        self._conversation_f.write(json.dumps(row, ensure_ascii=False) + "\n")
        self._conversation_f.flush()

    def tool(self, name: str, input_: Any, output: Any, latency_ms: Optional[int] = None):
        row = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "tool": name,
            "input": input_,
            "output": output,
            "latency_ms": latency_ms,
        }
        self._tools_f.write(json.dumps(row, ensure_ascii=False) + "\n")
        self._tools_f.flush()

    # ---------- usage ----------
    def usage(self, usage_obj: Any, extra: Optional[Dict[str, Any]] = None):
        data = {
            "input_tokens": getattr(usage_obj, "input_tokens", None),
            "output_tokens": getattr(usage_obj, "output_tokens", None),
            "cache_read_tokens": getattr(usage_obj, "cache_read_tokens", None),
            "cache_write_tokens": getattr(usage_obj, "cache_write_tokens", None),
        }
        if extra:
            data.update(extra)
        self._write_json("usage.json", data)

    # ---------- helpers ----------
    def _write_json(self, filename: str, data: Dict[str, Any]):
        (self.dir / filename).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
# ---------------------------------------------------------------------------------------------------------------------
class Tee:
    def __init__(self, path: Path, stream):
        self.file = open(path, "a", encoding="utf-8")
        self.stream = stream

    def write(self, data):
        self.file.write(data)
        self.file.flush()
        self.stream.write(data)
        self.stream.flush()

    def flush(self):
        self.file.flush()
        self.stream.flush()

# ---------------------------------------------------------------------------------------------------------------------
def capture_stdio(run_dir: Path):
    sys.stdout = Tee(run_dir / "stdout.txt", sys.stdout)
    sys.stderr = Tee(run_dir / "stderr.txt", sys.stderr)