# CadPilot v3 Benchmarking Report

Generated: 2026-06-19

This report summarizes the current local benchmark signals available in the
repository. It is based on existing local trace artifacts and sandbox execution
artifacts, not a controlled fixed-prompt benchmark suite.

## Summary

CadPilot currently has an observability-backed benchmark baseline:

- LLM call traces are stored under `artifacts/llm_runs/`.
- Sandbox execution artifacts are stored under `.sandbox_runs/`.
- The main analyzer is `scripts/analyze_llm_traces.py`.

The current local corpus is useful for identifying cost, retry pressure, and
failure hotspots. It should not be treated as a clean model-comparison benchmark
because it mixes historical pipeline modes, prompts, settings, and graph
versions.

## Commands Run

```powershell
$env:UV_CACHE_DIR='.uv-cache'
uv run python scripts\analyze_llm_traces.py --format json
uv run python scripts\analyze_llm_traces.py --top-agents 12 --top-runs 8
```

Additional PowerShell aggregation was run over:

```text
.sandbox_runs/**/execution_artifacts.json
```

## LLM Trace Baseline

Source: `artifacts/llm_runs/`

| Metric | Value |
| --- | ---: |
| Runs | 56 |
| LLM calls | 473 |
| Prompt chars | 14,230,970 |
| Response chars | 2,769,149 |
| Total traced chars | 17,000,119 |
| Retry calls | 125 |
| Failed calls | 70 |
| Calls/run min | 1 |
| Calls/run median | 8.0 |
| Calls/run max | 16 |
| Retry-call rate | 26.4% |
| Failure-call rate | 14.8% |

Average per traced run:

| Metric | Value |
| --- | ---: |
| LLM calls/run | 8.45 |
| Prompt chars/run | 254,124 |
| Response chars/run | 49,449 |

## Agent-Level Baseline

| Agent | Calls | Prompt Chars | Avg Prompt | Response Chars | Retries | Failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `code_generation_agent` | 72 | 2,993,350 | 41,574 | 448,798 | 26 | 23 |
| `geometry_planner_agent` | 100 | 2,320,255 | 23,203 | 1,095,087 | 47 | 37 |
| `repair_agent` | 43 | 1,827,198 | 42,493 | 89,860 | 24 | 0 |
| `parameter_agent` | 58 | 1,733,084 | 29,881 | 497,911 | 6 | 4 |
| `export_summary_agent` | 32 | 1,448,552 | 45,267 | 325,205 | 0 | 0 |
| `critic_checkpoint_b` | 43 | 1,386,290 | 32,239 | 74,639 | 5 | 0 |
| `critic_checkpoint_a` | 63 | 1,326,709 | 21,059 | 86,195 | 11 | 0 |
| `intent_spec_agent` | 57 | 911,888 | 15,998 | 75,751 | 4 | 4 |
| `design_synthesis_agent` | 5 | 283,644 | 56,729 | 75,703 | 2 | 2 |

### Observations

- `geometry_planner_agent` is the largest failure hotspot by count:
  37 failed calls and 47 retry calls.
- `code_generation_agent` is the largest prompt-volume hotspot:
  2.99M prompt chars, with a high average prompt size of 41,574 chars.
- `repair_agent` has high prompt volume and high retry pressure, but no traced
  parse/validation failures in this corpus.
- `export_summary_agent` has large average prompts but no retries or failures.
  If LLM summaries are disabled, this cost path should largely disappear.
- `design_synthesis_agent` appears only 5 times. Current `.env` enables design
  synthesis, but this historical corpus is still dominated by the older
  intent/spec/planner/parameter front half. Do not use this corpus alone to
  judge the updated graph.

## Highest-Cost Runs

Top runs by prompt volume from the analyzer:

| Run ID | Calls | Prompt Chars | Response Chars | Retries | Failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| `ca6d55bb-79a3-4d18-a58f-5e169c472954` | 16 | 589,252 | 84,684 | 9 | 3 |
| `904ede22-a466-4fa9-9c6e-eeabdf37f53a` | 15 | 561,369 | 79,664 | 7 | 2 |
| `9d7d6012-2789-4900-9791-bba1a4aedcb2` | 14 | 544,025 | 140,034 | 7 | 2 |
| `54b14204-ad79-4dcb-8aa7-68ad639b2f8e` | 14 | 538,562 | 65,786 | 7 | 1 |
| `740be9ca-0396-4112-8172-587b7300fd1c` | 12 | 460,709 | 91,784 | 5 | 0 |
| `d3b419a1-7a0e-4589-84ab-3776c135db95` | 10 | 454,484 | 171,280 | 4 | 2 |
| `4935c3f4-5141-42e7-af3e-3c7c523868af` | 14 | 413,967 | 51,196 | 7 | 1 |
| `17ff9f86-9102-43fd-9dd7-56942855aa4c` | 11 | 394,828 | 71,469 | 3 | 2 |

The expensive runs are mostly retry-heavy. That points to repair/codegen/planner
looping as the primary cost driver, not just single-call prompt size.

## Sandbox Execution Baseline

Source: `.sandbox_runs/**/execution_artifacts.json`

| Metric | Value |
| --- | ---: |
| Execution artifacts | 100 |
| Syntax precheck passed | 100 |
| Execution succeeded | 47 |
| Geometry report present | 44 |
| Avg execution time | 0.971 s |
| Min execution time | 0.000 s |
| Median execution time | 0.858 s |
| Max execution time | 3.793 s |

Derived rates:

| Metric | Value |
| --- | ---: |
| Execution success rate | 47.0% |
| Geometry report rate | 44.0% |
| Geometry report among successes | 93.6% |

Error-type distribution:

| Error Type | Count |
| --- | ---: |
| none / success | 47 |
| `ValueError` | 42 |
| `Standard_Failure` | 4 |
| `SyntaxError` | 2 |
| `Standard_ConstructionError` | 2 |
| `StdFail_NotDone` | 1 |
| `ParseException` | 1 |
| `AttributeError` | 1 |

Part-count distribution for runs with geometry reports:

| Part Count | Count |
| ---: | ---: |
| 1 | 21 |
| 2 | 4 |
| 3 | 2 |
| 4 | 4 |
| 5 | 2 |
| 6 | 6 |
| 7 | 1 |
| 8 | 1 |
| 14 | 2 |
| 15 | 1 |

### Sandbox Observations

- Sandbox execution is fast in successful/local cases; the median run is under
  one second.
- Execution success is currently below 50% across the historical artifact set.
  This is a mixed corpus, but it confirms that generated code/runtime recovery
  is one of the major quality levers.
- `ValueError` dominates execution failures. That usually deserves deeper
  classification because it can represent bad dimensions, invalid sketches,
  selector assumptions, or CadQuery operation misuse.
- Geometry inspection works for most successful executions. Only 3 successful
  executions failed to produce a geometry report.

## Current Benchmarking Strengths

- Local traces preserve exact prompts, raw responses, parsed outputs, validated
  outputs, generated scripts, retry metadata, and codegen validation status.
- The analyzer already produces a useful baseline for calls, prompt volume,
  response volume, retries, and failures.
- Sandbox artifacts capture actual execution time, error types, generated
  validation payloads, build manifests, and geometry metadata.
- The architecture can compare pipeline modes because key behavior is
  controlled by settings such as design synthesis, conditional Critic B, LLM
  export summaries, and direct repair codegen.

## Current Limitations

- There is no fixed prompt corpus, so the current numbers are not directly
  comparable across code changes unless the same prompts/settings are rerun.
- The trace analyzer uses character counts, not normalized token or cost totals.
  Some `usage_metadata` is captured, but the benchmark script does not aggregate
  it yet.
- Sandbox timing is not integrated into `analyze_llm_traces.py`.
- Contract-validation pass/fail rates are not aggregated into a benchmark
  report yet.
- End-to-end wall-clock duration per run is not aggregated.
- The trace corpus mixes legacy and updated graph behavior. Design synthesis is
  underrepresented in the current local data.

## Recommended Benchmark Plan

1. Add a fixed prompt corpus under `benchmarks/prompts/`.
2. Run each prompt under a named configuration:
   - legacy front half
   - design synthesis enabled
   - conditional Critic B enabled
   - deterministic export summary enabled
   - direct repair codegen enabled
3. Record per-run metrics:
   - wall-clock duration
   - LLM calls
   - prompt/response tokens or chars
   - retry count
   - parse/schema/codegen validation failures
   - sandbox execution success
   - contract-validation status
   - final export success
   - repair loop count
4. Extend `scripts/analyze_llm_traces.py` or add a new benchmark analyzer to
   join `artifacts/llm_runs` with `.sandbox_runs`.
5. Emit a machine-readable JSON report and a Markdown summary.

## Suggested Success Metrics

For the updated graph, track these as the primary benchmark targets:

| Metric | Direction |
| --- | --- |
| Median LLM calls/run | lower |
| Retry-call rate | lower |
| Codegen validation failure rate | lower |
| Geometry planner failure rate | lower |
| Sandbox execution success rate | higher |
| Contract-validation pass rate | higher |
| Export success rate | higher |
| Median wall-clock runtime | lower |
| Median prompt chars/run | lower |

## Immediate Optimization Priorities

1. Reduce geometry planner retries and failures. This is the largest failure
   hotspot in the trace corpus.
2. Reduce codegen prompt size and codegen validation failures. Codegen is the
   largest prompt-volume hotspot and a major retry source.
3. Aggregate sandbox failures by normalized `ExecutionValidationAgent.error_class`
   instead of raw Python exception type.
4. Benchmark the updated design-synthesis graph separately. The current corpus
   does not contain enough design-synthesis runs for a trustworthy comparison.
5. Disable or keep disabled LLM export summaries when benchmarking core CAD
   generation, otherwise summary prompts can obscure CAD-pipeline cost.

## Reproduction Notes

The current baseline can be regenerated with:

```powershell
$env:UV_CACHE_DIR='.uv-cache'
uv run python scripts\analyze_llm_traces.py --top-agents 12 --top-runs 8
```

For a cleaner benchmark, clear or archive old trace directories, run a fixed
prompt set, and analyze only that new trace directory.
