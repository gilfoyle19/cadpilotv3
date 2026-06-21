import importlib.util
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "verify_latency_claim.py"
SCRIPT_SPEC = importlib.util.spec_from_file_location("verify_latency_claim", SCRIPT_PATH)
assert SCRIPT_SPEC is not None
assert SCRIPT_SPEC.loader is not None
verify_latency_claim = importlib.util.module_from_spec(SCRIPT_SPEC)
sys.modules[SCRIPT_SPEC.name] = verify_latency_claim
SCRIPT_SPEC.loader.exec_module(verify_latency_claim)


def test_verify_claim_requires_enough_samples() -> None:
    passed, report = verify_latency_claim.verify_claim(
        [10.0],
        [3.5],
        minimum_samples=2,
        baseline_threshold=10.0,
        optimized_threshold=3.5,
    )

    assert passed is False
    assert report.startswith("INSUFFICIENT DATA")


def test_verify_claim_passes_only_when_both_medians_meet_thresholds() -> None:
    passed, report = verify_latency_claim.verify_claim(
        [10.0, 10.2, 11.0],
        [3.0, 3.4, 3.5],
        minimum_samples=3,
        baseline_threshold=10.0,
        optimized_threshold=3.5,
    )

    assert passed is True
    assert report.startswith("VERIFIED")


def test_verify_claim_rejects_fast_baseline() -> None:
    passed, report = verify_latency_claim.verify_claim(
        [9.0, 9.5, 9.8],
        [3.0, 3.2, 3.4],
        minimum_samples=3,
        baseline_threshold=10.0,
        optimized_threshold=3.5,
    )

    assert passed is False
    assert report.startswith("NOT VERIFIED")
