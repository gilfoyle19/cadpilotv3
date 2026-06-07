import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "analyze_llm_traces.py"
SCRIPT_SPEC = importlib.util.spec_from_file_location("analyze_llm_traces", SCRIPT_PATH)
assert SCRIPT_SPEC is not None
assert SCRIPT_SPEC.loader is not None
analyze_llm_traces = importlib.util.module_from_spec(SCRIPT_SPEC)
sys.modules[SCRIPT_SPEC.name] = analyze_llm_traces
SCRIPT_SPEC.loader.exec_module(analyze_llm_traces)


def test_analyze_trace_dir_summarizes_runs_agents_retries_and_failures(tmp_path) -> None:
    trace_dir = tmp_path / "llm_runs"
    _write_metadata(
        trace_dir,
        "run-a",
        "001_intent_spec_agent",
        {
            "run_id": "run-a",
            "agent_name": "intent_spec_agent",
            "prompt_length_chars": 100,
            "response_length_chars": 20,
            "structured_attempt_number": 1,
            "validation_status": "passed",
        },
    )
    _write_metadata(
        trace_dir,
        "run-a",
        "002_intent_spec_agent",
        {
            "run_id": "run-a",
            "agent_name": "intent_spec_agent",
            "prompt_length_chars": 150,
            "response_length_chars": 25,
            "structured_attempt_number": 2,
            "validation_status": "passed",
        },
    )
    _write_metadata(
        trace_dir,
        "run-a",
        "003_code_generation_agent",
        {
            "run_id": "run-a",
            "agent_name": "code_generation_agent",
            "prompt_length_chars": 500,
            "response_length_chars": 200,
            "prompt_mode": "normal",
            "validation_status": "failed",
        },
    )
    _write_metadata(
        trace_dir,
        "run-a",
        "004_code_generation_agent",
        {
            "run_id": "run-a",
            "agent_name": "code_generation_agent",
            "prompt_length_chars": 250,
            "response_length_chars": 180,
            "prompt_mode": "compact_retry",
            "validation_status": "passed",
        },
    )
    _write_metadata(
        trace_dir,
        "run-b",
        "001_export_summary_agent",
        {
            "run_id": "run-b",
            "agent_name": "export_summary_agent",
            "prompt_length_chars": 300,
            "response_length_chars": 80,
            "parse_status": "failed",
        },
    )

    analysis = analyze_llm_traces.analyze_trace_dir(trace_dir)

    assert analysis.total_runs == 2
    assert analysis.total_calls == 5
    assert analysis.total_prompt_chars == 1300
    assert analysis.total_response_chars == 505
    assert analysis.total_retry_calls == 2
    assert analysis.total_failures == 2
    assert analysis.calls_per_run == {
        "min": 1,
        "median": 2.5,
        "max": 4,
    }

    run_a = analysis.runs["run-a"]
    assert run_a.calls == 4
    assert run_a.retry_calls == 2
    assert run_a.failures == 1
    assert run_a.agents["intent_spec_agent"].calls == 2
    assert run_a.agents["intent_spec_agent"].retry_calls == 1
    assert run_a.agents["code_generation_agent"].calls == 2
    assert run_a.agents["code_generation_agent"].retry_calls == 1

    codegen_stats = analysis.agents["code_generation_agent"]
    assert codegen_stats.calls == 2
    assert codegen_stats.prompt_chars == 750
    assert codegen_stats.avg_prompt_chars == 375
    assert codegen_stats.failures == 1


def test_analyze_trace_dir_skips_invalid_metadata(tmp_path) -> None:
    trace_dir = tmp_path / "llm_runs"
    invalid_path = trace_dir / "run-a" / "001_bad" / "metadata.json"
    invalid_path.parent.mkdir(parents=True)
    invalid_path.write_text("{not json", encoding="utf-8")

    _write_metadata(
        trace_dir,
        "run-a",
        "002_valid",
        {
            "run_id": "run-a",
            "agent_name": "parameter_agent",
            "prompt_length_chars": "42",
            "response_length_chars": 10,
        },
    )

    analysis = analyze_llm_traces.analyze_trace_dir(trace_dir)

    assert analysis.total_calls == 1
    assert analysis.total_prompt_chars == 42
    assert analysis.agents["parameter_agent"].calls == 1


def test_format_readable_report_includes_key_baseline_sections(tmp_path) -> None:
    trace_dir = tmp_path / "llm_runs"
    _write_metadata(
        trace_dir,
        "run-a",
        "001_intent_spec_agent",
        {
            "run_id": "run-a",
            "agent_name": "intent_spec_agent",
            "prompt_length_chars": 100,
            "response_length_chars": 20,
        },
    )

    analysis = analyze_llm_traces.analyze_trace_dir(trace_dir)
    report = analyze_llm_traces.format_readable_report(analysis)

    assert "LLM trace baseline" in report
    assert "Runs: 1 | Calls: 1" in report
    assert "intent_spec_agent: calls=1" in report
    assert "run-a: calls=1" in report


def test_analysis_to_dict_is_json_serializable(tmp_path) -> None:
    trace_dir = tmp_path / "llm_runs"
    _write_metadata(
        trace_dir,
        "run-a",
        "001_intent_spec_agent",
        {
            "run_id": "run-a",
            "agent_name": "intent_spec_agent",
            "prompt_length_chars": 100,
            "response_length_chars": 20,
        },
    )

    payload = analyze_llm_traces.analyze_trace_dir(trace_dir).to_dict()

    assert json.loads(json.dumps(payload))["total_calls"] == 1


def _write_metadata(
    trace_dir: Path,
    run_id: str,
    call_dir: str,
    metadata: dict,
) -> None:
    metadata_path = trace_dir / run_id / call_dir / "metadata.json"
    metadata_path.parent.mkdir(parents=True)
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
