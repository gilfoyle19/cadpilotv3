# CadPilot v3 Chronological Improvement Analysis

Generated: 2026-06-19

This report orders local LLM trace runs by their first recorded LLM-call
timestamp and computes percentage improvement against the earliest observed
baseline.

## Method

Source data:

```text
artifacts/llm_runs/**/metadata.json
```

Definitions:

- Run timestamp: earliest `metadata.json.timestamp` for a run.
- Overall baseline: first chronological run,
  `249aa594-90aa-4b35-b20f-956478d82a9c`, at `2026-05-05 13:41:38 UTC`.
- Per-agent baseline: first chronological run in which that agent appears.
- Improvement formula for lower-is-better metrics:

```text
improvement_percent = (baseline_value - current_value) / baseline_value * 100
```

Positive percentages mean lower cost or lower instability. Negative percentages
mean regression versus the selected baseline.

Metrics treated as lower-is-better:

- LLM calls
- Prompt characters
- Retry calls
- Failed calls
- Per-agent average prompt characters
- Per-agent retry rate
- Per-agent failure rate

Important caveat: this is a historical local trace corpus, not a controlled
fixed-prompt benchmark. Prompt complexity, settings, graph shape, and pipeline
mode changed across runs. Use these numbers as trend signals, not proof of
causal improvement.

## Overall First-to-Latest Improvement

| Metric | First Run | Latest Run | Improvement |
| --- | ---: | ---: | ---: |
| Calls | 12 | 2 | +83.3% |
| Prompt chars | 207,380 | 118,811 | +42.7% |
| Retry calls | 6 | 1 | +83.3% |
| Failed calls | 3 | 1 | +66.7% |

Latest run:

```text
c57404eb-d382-499d-8e8e-e02279409fa2
2026-06-12 12:17:00 UTC
```

## Per-Agent First-to-Latest Improvement

| Agent | First UTC | Latest UTC | First Calls | Latest Calls | Calls Imp | Avg Prompt Imp | Retry-Rate Imp | Failure-Rate Imp |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `code_generation_agent` | 2026-05-05 13:41:38 | 2026-06-12 11:47:50 | 4 | 1 | +75.0% | -94.1% | +100.0% | +100.0% |
| `critic_checkpoint_a` | 2026-05-05 13:41:38 | 2026-06-08 21:45:23 | 2 | 1 | +50.0% | -63.3% | +100.0% | n/a |
| `critic_checkpoint_b` | 2026-05-05 13:41:38 | 2026-06-12 11:47:50 | 1 | 1 | +0.0% | -170.3% | n/a | n/a |
| `design_synthesis_agent` | 2026-06-12 11:47:50 | 2026-06-12 12:17:00 | 2 | 2 | +0.0% | -5.8% | +0.0% | +0.0% |
| `export_summary_agent` | 2026-05-05 14:40:15 | 2026-06-12 11:47:50 | 1 | 1 | +0.0% | -104.6% | n/a | n/a |
| `geometry_planner_agent` | 2026-05-05 13:41:38 | 2026-06-08 21:45:23 | 2 | 1 | +50.0% | -67.6% | +100.0% | n/a |
| `intent_spec_agent` | 2026-05-05 13:41:38 | 2026-06-08 21:45:23 | 1 | 1 | +0.0% | +6.4% | n/a | n/a |
| `parameter_agent` | 2026-05-05 13:41:38 | 2026-06-08 21:45:23 | 2 | 1 | +50.0% | -103.0% | +100.0% | n/a |
| `repair_agent` | 2026-05-05 14:40:15 | 2026-06-08 21:45:23 | 2 | 1 | +50.0% | -55.2% | +100.0% | n/a |

### Agent Notes

- The largest structural improvements are in call count and retry rate, not
  prompt size.
- Several agents show worse average prompt size in their latest observed run.
  This likely reflects richer prompts/contracts and changing graph behavior
  rather than pure inefficiency.
- `design_synthesis_agent` only appears in the latest portion of the corpus, so
  its trend is under-sampled.
- `n/a` means the first observed baseline was zero, so percentage improvement is
  mathematically undefined.

## Overall Runs In Chronological Order

| # | UTC Start | Run | Calls | Calls Imp | Prompt Chars | Prompt Imp | Retries | Retry Imp | Failures | Failure Imp |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2026-05-05 13:41:38 | `249aa594` | 12 | +0.0% | 207,380 | +0.0% | 6 | +0.0% | 3 | +0.0% |
| 2 | 2026-05-05 14:07:01 | `9de53a93` | 7 | +41.7% | 163,977 | +20.9% | 2 | +66.7% | 3 | +0.0% |
| 3 | 2026-05-05 14:13:12 | `551edc42` | 7 | +41.7% | 170,405 | +17.8% | 2 | +66.7% | 3 | +0.0% |
| 4 | 2026-05-05 14:25:27 | `ccc847d8` | 7 | +41.7% | 141,864 | +31.6% | 2 | +66.7% | 3 | +0.0% |
| 5 | 2026-05-05 14:37:38 | `319fb844` | 5 | +58.3% | 93,436 | +54.9% | 1 | +83.3% | 2 | +33.3% |
| 6 | 2026-05-05 14:40:15 | `83cfc854` | 10 | +16.7% | 224,867 | -8.4% | 2 | +66.7% | 1 | +66.7% |
| 7 | 2026-05-05 17:28:14 | `8eea3564` | 16 | -33.3% | 325,232 | -56.8% | 10 | -66.7% | 0 | +100.0% |
| 8 | 2026-05-05 17:54:21 | `edcfa310` | 5 | +58.3% | 100,596 | +51.5% | 1 | +83.3% | 2 | +33.3% |
| 9 | 2026-05-05 18:00:19 | `a74428dd` | 10 | +16.7% | 230,817 | -11.3% | 2 | +66.7% | 0 | +100.0% |
| 10 | 2026-05-05 20:45:54 | `5afd17a0` | 10 | +16.7% | 334,772 | -61.4% | 2 | +66.7% | 1 | +66.7% |
| 11 | 2026-05-05 21:52:44 | `587425be` | 6 | +50.0% | 138,195 | +33.4% | 1 | +83.3% | 1 | +66.7% |
| 12 | 2026-05-14 10:22:16 | `26c7c620` | 8 | +33.3% | 169,849 | +18.1% | 1 | +83.3% | 1 | +66.7% |
| 13 | 2026-05-14 10:29:19 | `5d444d69` | 8 | +33.3% | 176,384 | +14.9% | 1 | +83.3% | 1 | +66.7% |
| 14 | 2026-05-14 10:39:42 | `17fa1e01` | 8 | +33.3% | 171,706 | +17.2% | 1 | +83.3% | 1 | +66.7% |
| 15 | 2026-05-14 10:46:21 | `29caf6c0` | 9 | +25.0% | 269,755 | -30.1% | 2 | +66.7% | 2 | +33.3% |
| 16 | 2026-05-15 08:46:28 | `737993bd` | 9 | +25.0% | 205,762 | +0.8% | 1 | +83.3% | 1 | +66.7% |
| 17 | 2026-05-15 08:50:24 | `a7acbd28` | 9 | +25.0% | 208,537 | -0.6% | 2 | +66.7% | 2 | +33.3% |
| 18 | 2026-05-15 08:54:51 | `f3041fd4` | 9 | +25.0% | 219,410 | -5.8% | 2 | +66.7% | 2 | +33.3% |
| 19 | 2026-05-16 11:31:17 | `c8a98991` | 11 | +8.3% | 298,295 | -43.8% | 3 | +50.0% | 2 | +33.3% |
| 20 | 2026-05-18 10:34:46 | `23a41d60` | 9 | +25.0% | 242,705 | -17.0% | 2 | +66.7% | 2 | +33.3% |
| 21 | 2026-05-18 10:43:56 | `e1bc17cc` | 9 | +25.0% | 235,254 | -13.4% | 2 | +66.7% | 2 | +33.3% |
| 22 | 2026-05-18 11:32:27 | `e7498586` | 11 | +8.3% | 329,785 | -59.0% | 3 | +50.0% | 1 | +66.7% |
| 23 | 2026-05-18 11:47:05 | `54b14204` | 14 | -16.7% | 538,562 | -159.7% | 7 | -16.7% | 1 | +66.7% |
| 24 | 2026-05-18 13:05:50 | `904ede22` | 15 | -25.0% | 561,369 | -170.7% | 7 | -16.7% | 2 | +33.3% |
| 25 | 2026-05-18 13:13:41 | `4935c3f4` | 14 | -16.7% | 413,967 | -99.6% | 7 | -16.7% | 1 | +66.7% |
| 26 | 2026-05-18 13:42:23 | `dfa1b881` | 9 | +25.0% | 230,918 | -11.4% | 1 | +83.3% | 1 | +66.7% |
| 27 | 2026-05-18 13:59:16 | `e4230bfe` | 8 | +33.3% | 241,242 | -16.3% | 1 | +83.3% | 1 | +66.7% |
| 28 | 2026-05-18 14:19:08 | `ce4dc1c8` | 11 | +8.3% | 353,372 | -70.4% | 3 | +50.0% | 1 | +66.7% |
| 29 | 2026-05-18 14:27:42 | `2cdd1b36` | 8 | +33.3% | 257,787 | -24.3% | 1 | +83.3% | 1 | +66.7% |
| 30 | 2026-05-18 14:40:25 | `17ff9f86` | 11 | +8.3% | 394,828 | -90.4% | 3 | +50.0% | 2 | +33.3% |
| 31 | 2026-05-18 14:57:05 | `51a06d08` | 9 | +25.0% | 271,350 | -30.8% | 2 | +66.7% | 2 | +33.3% |
| 32 | 2026-05-18 15:04:09 | `639f62b6` | 7 | +41.7% | 188,070 | +9.3% | 2 | +66.7% | 3 | +0.0% |
| 33 | 2026-05-18 15:08:15 | `ca6d55bb` | 16 | -33.3% | 589,252 | -184.1% | 9 | -50.0% | 3 | +0.0% |
| 34 | 2026-05-18 17:18:02 | `f4bfdf86` | 8 | +33.3% | 217,018 | -4.6% | 1 | +83.3% | 1 | +66.7% |
| 35 | 2026-05-18 17:24:45 | `0a28b98b` | 14 | -16.7% | 366,291 | -76.6% | 6 | +0.0% | 2 | +33.3% |
| 36 | 2026-05-18 17:32:47 | `2ea19988` | 8 | +33.3% | 227,776 | -9.8% | 1 | +83.3% | 1 | +66.7% |
| 37 | 2026-05-18 17:37:40 | `9d7d6012` | 14 | -16.7% | 544,025 | -162.3% | 7 | -16.7% | 2 | +33.3% |
| 38 | 2026-05-18 22:41:34 | `9a8e5922` | 9 | +25.0% | 235,593 | -13.6% | 2 | +66.7% | 2 | +33.3% |
| 39 | 2026-05-19 17:24:29 | `792327ff` | 8 | +33.3% | 278,008 | -34.1% | 0 | +100.0% | 0 | +100.0% |
| 40 | 2026-05-19 17:39:55 | `740be9ca` | 12 | +0.0% | 460,709 | -122.2% | 5 | +16.7% | 0 | +100.0% |
| 41 | 2026-05-19 17:49:01 | `4ab793ea` | 6 | +50.0% | 276,923 | -33.5% | 0 | +100.0% | 0 | +100.0% |
| 42 | 2026-05-19 17:52:43 | `afad69fd` | 7 | +41.7% | 257,152 | -24.0% | 0 | +100.0% | 0 | +100.0% |
| 43 | 2026-05-19 18:03:30 | `52e04eff` | 7 | +41.7% | 256,314 | -23.6% | 0 | +100.0% | 0 | +100.0% |
| 44 | 2026-05-19 18:07:47 | `84d40e82` | 7 | +41.7% | 256,111 | -23.5% | 0 | +100.0% | 0 | +100.0% |
| 45 | 2026-05-19 18:13:20 | `34dc9de3` | 5 | +58.3% | 167,115 | +19.4% | 1 | +83.3% | 1 | +66.7% |
| 46 | 2026-05-19 19:58:56 | `4cba1489` | 4 | +66.7% | 103,283 | +50.2% | 0 | +100.0% | 0 | +100.0% |
| 47 | 2026-05-21 09:42:25 | `49219c86` | 7 | +41.7% | 348,682 | -68.1% | 0 | +100.0% | 0 | +100.0% |
| 48 | 2026-05-21 10:48:26 | `594d3ab8` | 4 | +66.7% | 115,304 | +44.4% | 0 | +100.0% | 0 | +100.0% |
| 49 | 2026-05-21 10:55:54 | `509dbcdf` | 4 | +66.7% | 103,001 | +50.3% | 0 | +100.0% | 0 | +100.0% |
| 50 | 2026-05-21 11:55:39 | `d3b419a1` | 10 | +16.7% | 454,484 | -119.2% | 4 | +33.3% | 2 | +33.3% |
| 51 | 2026-05-22 12:47:20 | `0deb4025` | 5 | +58.3% | 164,809 | +20.5% | 1 | +83.3% | 1 | +66.7% |
| 52 | 2026-05-22 21:19:48 | `b28ec46e` | 3 | +75.0% | 104,886 | +49.4% | 1 | +83.3% | 2 | +33.3% |
| 53 | 2026-06-08 21:45:23 | `95d5a665` | 6 | +50.0% | 190,101 | +8.3% | 0 | +100.0% | 0 | +100.0% |
| 54 | 2026-06-12 11:47:50 | `ef608251` | 5 | +58.3% | 232,368 | -12.0% | 1 | +83.3% | 1 | +66.7% |
| 55 | 2026-06-12 12:06:43 | `6b2df3b8` | 1 | +91.7% | 52,506 | +74.7% | 0 | +100.0% | 0 | +100.0% |
| 56 | 2026-06-12 12:17:00 | `c57404eb` | 2 | +83.3% | 118,811 | +42.7% | 1 | +83.3% | 1 | +66.7% |

## Interpretation

The overall latest run is substantially lighter than the earliest traced run:

- 83.3% fewer LLM calls
- 42.7% fewer prompt characters
- 83.3% fewer retry calls
- 66.7% fewer failed traced calls

The best-looking chronological improvements appear in the latest June runs, but
those runs are also shorter and include the newer graph behavior. The trace set
does not prove that every individual agent became intrinsically cheaper; several
agents have larger latest prompts because newer prompts carry richer contracts,
manifests, and validation requirements.

For a controlled improvement measurement, rerun the same prompt corpus under two
named configurations and compute these percentages between those paired runs.
