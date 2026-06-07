from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

FailureStatus = Literal["failed"]


@dataclass
class AgentTraceStats:
    calls: int = 0
    prompt_chars: int = 0
    response_chars: int = 0
    retry_calls: int = 0
    failures: int = 0

    @property
    def avg_prompt_chars(self) -> int:
        return _safe_average(self.prompt_chars, self.calls)

    @property
    def avg_response_chars(self) -> int:
        return _safe_average(self.response_chars, self.calls)

    def to_dict(self) -> dict[str, int]:
        payload = asdict(self)
        payload["avg_prompt_chars"] = self.avg_prompt_chars
        payload["avg_response_chars"] = self.avg_response_chars
        return payload


@dataclass
class RunTraceStats:
    run_id: str
    calls: int = 0
    prompt_chars: int = 0
    response_chars: int = 0
    retry_calls: int = 0
    failures: int = 0
    agents: dict[str, AgentTraceStats] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "calls": self.calls,
            "prompt_chars": self.prompt_chars,
            "response_chars": self.response_chars,
            "retry_calls": self.retry_calls,
            "failures": self.failures,
            "agents": {
                agent: stats.to_dict()
                for agent, stats in sorted(self.agents.items())
            },
        }


@dataclass
class TraceAnalysis:
    trace_dir: str
    total_runs: int
    total_calls: int
    total_prompt_chars: int
    total_response_chars: int
    total_retry_calls: int
    total_failures: int
    calls_per_run: dict[str, int | float]
    agents: dict[str, AgentTraceStats]
    runs: dict[str, RunTraceStats]

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_dir": self.trace_dir,
            "total_runs": self.total_runs,
            "total_calls": self.total_calls,
            "total_prompt_chars": self.total_prompt_chars,
            "total_response_chars": self.total_response_chars,
            "total_retry_calls": self.total_retry_calls,
            "total_failures": self.total_failures,
            "calls_per_run": self.calls_per_run,
            "agents": {
                agent: stats.to_dict()
                for agent, stats in sorted(
                    self.agents.items(),
                    key=lambda item: (-item[1].calls, item[0]),
                )
            },
            "runs": {
                run_id: stats.to_dict()
                for run_id, stats in sorted(self.runs.items())
            },
        }


def analyze_trace_dir(trace_dir: Path) -> TraceAnalysis:
    metadata_files = sorted(trace_dir.glob("*/**/metadata.json"))
    runs: dict[str, RunTraceStats] = {}
    agents: dict[str, AgentTraceStats] = {}
    seen_agents_by_run: dict[str, set[str]] = {}

    for metadata_path in metadata_files:
        metadata = _read_metadata(metadata_path)
        if metadata is None:
            continue

        run_id = str(metadata.get("run_id") or metadata_path.parent.parent.name)
        agent_name = str(metadata.get("agent_name") or "unknown")
        prompt_chars = _as_int(metadata.get("prompt_length_chars"))
        response_chars = _as_int(metadata.get("response_length_chars"))
        is_failure = _is_failure(metadata)

        run_stats = runs.setdefault(run_id, RunTraceStats(run_id=run_id))
        agent_stats = agents.setdefault(agent_name, AgentTraceStats())
        run_agent_stats = run_stats.agents.setdefault(agent_name, AgentTraceStats())

        is_retry = _is_retry_call(
            metadata=metadata,
            agent_name=agent_name,
            seen_agents=seen_agents_by_run.setdefault(run_id, set()),
        )

        for stats in (run_stats, agent_stats, run_agent_stats):
            stats.calls += 1
            stats.prompt_chars += prompt_chars
            stats.response_chars += response_chars
            if is_retry:
                stats.retry_calls += 1
            if is_failure:
                stats.failures += 1

    call_counts = sorted(run.calls for run in runs.values())
    return TraceAnalysis(
        trace_dir=str(trace_dir),
        total_runs=len(runs),
        total_calls=sum(run.calls for run in runs.values()),
        total_prompt_chars=sum(run.prompt_chars for run in runs.values()),
        total_response_chars=sum(run.response_chars for run in runs.values()),
        total_retry_calls=sum(run.retry_calls for run in runs.values()),
        total_failures=sum(run.failures for run in runs.values()),
        calls_per_run={
            "min": call_counts[0] if call_counts else 0,
            "median": _median(call_counts),
            "max": call_counts[-1] if call_counts else 0,
        },
        agents=agents,
        runs=runs,
    )


def format_readable_report(
    analysis: TraceAnalysis,
    *,
    top_runs: int = 10,
    top_agents: int = 20,
) -> str:
    lines = [
        "LLM trace baseline",
        f"Trace dir: {analysis.trace_dir}",
        (
            "Runs: "
            f"{analysis.total_runs} | Calls: {analysis.total_calls} | "
            f"Prompt chars: {analysis.total_prompt_chars} | "
            f"Response chars: {analysis.total_response_chars}"
        ),
        (
            "Retry calls: "
            f"{analysis.total_retry_calls} | Failures: {analysis.total_failures} | "
            "Calls/run: "
            f"min {analysis.calls_per_run['min']}, "
            f"median {analysis.calls_per_run['median']}, "
            f"max {analysis.calls_per_run['max']}"
        ),
        "",
        "Agents:",
    ]

    sorted_agents = sorted(
        analysis.agents.items(),
        key=lambda item: (-item[1].prompt_chars, item[0]),
    )
    for agent_name, stats in sorted_agents[:top_agents]:
        lines.append(
            "  "
            f"{agent_name}: calls={stats.calls}, "
            f"prompt={stats.prompt_chars}, avg_prompt={stats.avg_prompt_chars}, "
            f"response={stats.response_chars}, retries={stats.retry_calls}, "
            f"failures={stats.failures}"
        )

    lines.extend(["", "Runs:"])
    sorted_runs = sorted(
        analysis.runs.values(),
        key=lambda run: (-run.prompt_chars, run.run_id),
    )
    for run in sorted_runs[:top_runs]:
        agent_counts = ", ".join(
            f"{agent}:{stats.calls}"
            for agent, stats in sorted(
                run.agents.items(),
                key=lambda item: (-item[1].calls, item[0]),
            )
        )
        lines.append(
            "  "
            f"{run.run_id}: calls={run.calls}, prompt={run.prompt_chars}, "
            f"response={run.response_chars}, retries={run.retry_calls}, "
            f"failures={run.failures}, agents=[{agent_counts}]"
        )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze local CadPilot LLM trace metadata.",
    )
    parser.add_argument(
        "--trace-dir",
        default="artifacts/llm_runs",
        help="Directory containing per-run LLM trace folders.",
    )
    parser.add_argument(
        "--format",
        choices=["readable", "json"],
        default="readable",
        help="Output format.",
    )
    parser.add_argument(
        "--top-runs",
        type=int,
        default=10,
        help="Number of highest-prompt runs to show in readable output.",
    )
    parser.add_argument(
        "--top-agents",
        type=int,
        default=20,
        help="Number of highest-prompt agents to show in readable output.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    analysis = analyze_trace_dir(Path(args.trace_dir))
    if args.format == "json":
        print(json.dumps(analysis.to_dict(), indent=2))
        return

    print(
        format_readable_report(
            analysis,
            top_runs=args.top_runs,
            top_agents=args.top_agents,
        )
    )


def _read_metadata(metadata_path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _is_retry_call(
    *,
    metadata: dict[str, Any],
    agent_name: str,
    seen_agents: set[str],
) -> bool:
    repeated_agent_call = agent_name in seen_agents
    seen_agents.add(agent_name)

    structured_attempt = _as_int(metadata.get("structured_attempt_number"))
    if structured_attempt > 1:
        return True

    if metadata.get("prompt_mode") == "compact_retry":
        return True

    if metadata.get("has_generation_feedback") is True:
        return True

    return repeated_agent_call


def _is_failure(metadata: dict[str, Any]) -> bool:
    return (
        metadata.get("validation_status") == "failed"
        or metadata.get("parse_status") == "failed"
    )


def _as_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value)
    return 0


def _median(values: list[int]) -> int | float:
    if not values:
        return 0
    midpoint = len(values) // 2
    if len(values) % 2:
        return values[midpoint]
    return (values[midpoint - 1] + values[midpoint]) / 2


def _safe_average(total: int, count: int) -> int:
    if count == 0:
        return 0
    return round(total / count)


if __name__ == "__main__":
    main()
