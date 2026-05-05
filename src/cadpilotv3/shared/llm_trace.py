from __future__ import annotations

import json
import re
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from cadpilotv3.config.settings import get_settings

_trace_run_id: ContextVar[str | None] = ContextVar("llm_trace_run_id", default=None)
_trace_call_counter: ContextVar[int] = ContextVar("llm_trace_call_counter", default=0)


def configure_llm_trace(run_id: str) -> None:
    _trace_run_id.set(run_id)
    _trace_call_counter.set(0)


def clear_llm_trace() -> None:
    _trace_run_id.set(None)
    _trace_call_counter.set(0)


def record_llm_call(
    *,
    prompt: str,
    response_text: str,
    agent_name: str | None,
    response_metadata: dict[str, Any],
    usage_metadata: dict[str, Any] | None,
    response_id: str | None,
    raw_response_repr: str,
    extra_metadata: dict[str, Any] | None = None,
) -> Path | None:
    settings = get_settings()
    if not settings.llm_trace_outputs:
        return None

    run_id = _trace_run_id.get()
    if not run_id:
        return None

    call_number = _next_call_number()
    safe_agent_name = _safe_path_part(agent_name or "llm_call")
    run_dir = Path(settings.cad_artifacts_dir) / "llm_runs" / _safe_path_part(run_id)
    trace_dir = run_dir / f"{call_number:03d}_{safe_agent_name}"
    if trace_dir.exists():
        trace_dir = run_dir / f"{call_number:03d}_{safe_agent_name}_{uuid4().hex[:8]}"
    trace_dir.mkdir(parents=True, exist_ok=True)

    (trace_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    (trace_dir / "raw_response.txt").write_text(response_text, encoding="utf-8")

    metadata = {
        "run_id": run_id,
        "call_number": call_number,
        "agent_name": agent_name,
        "timestamp": datetime.now(UTC).isoformat(),
        "prompt_length_chars": len(prompt),
        "response_length_chars": len(response_text),
        "response_metadata": response_metadata,
        "usage_metadata": usage_metadata,
        "response_id": response_id,
        "raw_response_repr": raw_response_repr[:4000],
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    _write_metadata(trace_dir, metadata)
    return trace_dir


def update_llm_trace(
    trace_dir: str | Path | None,
    *,
    metadata_updates: dict[str, Any] | None = None,
    files: dict[str, str] | None = None,
) -> None:
    if trace_dir is None:
        return

    trace_path = Path(trace_dir)
    if files:
        for filename, content in files.items():
            (trace_path / filename).write_text(content, encoding="utf-8")

    if not metadata_updates:
        return

    metadata_path = trace_path / "metadata.json"
    metadata: dict[str, Any] = {}
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.update(metadata_updates)
    _write_metadata(trace_path, metadata)


def _next_call_number() -> int:
    current = _trace_call_counter.get()
    next_value = current + 1
    _trace_call_counter.set(next_value)
    return next_value


def _safe_path_part(value: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", value.strip())
    return safe[:120] or "unnamed"


def _write_metadata(trace_dir: Path, metadata: dict[str, Any]) -> None:
    (trace_dir / "metadata.json").write_text(
        json.dumps(_to_jsonable(metadata), indent=2),
        encoding="utf-8",
    )


def _to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    try:
        json.dumps(value)
    except TypeError:
        return str(value)
    return value
