"""Resilience matrix reconciled with policy-profile scenarios."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from core import State, VirtualDevice
from fault_injection import exercise_faults
from scenario import run_scenario
from transition_matrix import exercise_transitions

ROOT = Path(__file__).resolve().parent
SCHEMA = "frp-emulator-resilience-matrix/v2"
SCOPE = "controlled-simulator-only"


def _normal() -> dict[str, object]:
    result = asdict(run_scenario("normal", "RESILIENCE-TOKEN"))
    return {"status": "PASS" if result["state"] == State.DEVICE_READY.value and result["passed"] else "FAIL", "final_state": result["state"], "events": result["event_count"], "policy": result["policy"], "invariant_errors": list(result["invariant_errors"])}


def _invalid_token() -> dict[str, object]:
    result = asdict(run_scenario("invalid-token", "RESILIENCE-TOKEN"))
    return {"status": "PASS" if result["state"] == State.FRP_LOCKED.value and result["rejected_events"] == 1 and result["passed"] else "FAIL", "final_state": result["state"], "rejected_events": result["rejected_events"], "policy": result["policy"], "invariant_errors": list(result["invariant_errors"])}


def _illegal_transition() -> dict[str, object]:
    result = asdict(run_scenario("illegal-transition", "RESILIENCE-TOKEN"))
    return {"status": "PASS" if result["state"] == State.FACTORY_RESET.value and result["rejected_events"] == 1 and result["passed"] else "FAIL", "final_state": result["state"], "rejected_events": result["rejected_events"], "policy": result["policy"], "invariant_errors": list(result["invariant_errors"])}


def _recovery() -> dict[str, object]:
    result = asdict(run_scenario("recovery", "RESILIENCE-TOKEN"))
    return {"status": "PASS" if result["state"] == State.FACTORY_RESET.value and result["passed"] else "FAIL", "final_state": result["state"], "events": result["event_count"], "policy": result["policy"], "invariant_errors": list(result["invariant_errors"])}


def _strict_recovery() -> dict[str, object]:
    result = asdict(run_scenario("strict-recovery", "RESILIENCE-TOKEN"))
    return {"status": "PASS" if result["state"] == State.DEVICE_READY.value and result["rejected_events"] == 1 and result["policy"] == "strict" and result["policy_decisions"] >= 1 and result["passed"] else "FAIL", "final_state": result["state"], "rejected_events": result["rejected_events"], "policy": result["policy"], "policy_decisions": result["policy_decisions"], "invariant_errors": list(result["invariant_errors"])}


def _persistence_corruption() -> dict[str, object]:
    result = exercise_faults()
    return {"status": result["overall_status"], "coverage": result["coverage"], "rejected_cases": result["rejected_cases"], "unexpectedly_accepted": result["unexpectedly_accepted"]}


def exercise_resilience() -> dict[str, object]:
    transition = exercise_transitions()
    cases = {"normal": _normal(), "invalid-token": _invalid_token(), "illegal-transition": _illegal_transition(), "recovery": _recovery(), "strict-recovery": _strict_recovery(), "persistence-corruption": _persistence_corruption()}
    invariant_failures = sum(len(case.get("invariant_errors", [])) for case in cases.values())
    failed_cases = [name for name, case in cases.items() if case.get("status") != "PASS"]
    if transition.get("overall_status") != "PASS":
        failed_cases.append("transition-matrix")
    result = {"schema": SCHEMA, "scope": SCOPE, "cases": cases, "case_count": len(cases), "failed_cases": failed_cases, "invariant_failures": invariant_failures, "transition_coverage": transition["coverage"], "transition_matrix_status": transition["overall_status"], "overall_status": "PASS" if not failed_cases and invariant_failures == 0 else "FAIL"}
    (ROOT / "resilience-matrix.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> int:
    result = exercise_resilience()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
