"""Deterministic resilience matrix for the controlled FRP simulator.

This module exercises normal operation, rejected inputs, recovery, persistence
corruption rejection, and invariant checks. It never accesses real devices,
ADB/Fastboot, credentials, or real FRP state.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from core import State, VirtualDevice
from fault_injection import exercise_faults
from scenario import run_scenario
from transition_matrix import exercise_transitions

ROOT = Path(__file__).resolve().parent
SCHEMA = "frp-emulator-resilience-matrix/v1"
SCOPE = "controlled-simulator-only"


def _normal() -> dict[str, object]:
    result = asdict(run_scenario("normal", "RESILIENCE-TOKEN"))
    return {
        "status": "PASS" if result["state"] == State.DEVICE_READY.value else "FAIL",
        "final_state": result["state"],
        "events": len(result["events"]),
        "invariant_errors": result.get("invariant_errors", []),
    }


def _invalid_token() -> dict[str, object]:
    result = asdict(run_scenario("invalid-token", "RESILIENCE-TOKEN"))
    return {
        "status": "PASS" if result["state"] == State.FRP_LOCKED.value and result["rejected_events"] == 1 else "FAIL",
        "final_state": result["state"],
        "rejected_events": result["rejected_events"],
        "invariant_errors": result.get("invariant_errors", []),
    }


def _illegal_transition() -> dict[str, object]:
    device = VirtualDevice()
    before = device.state
    after = device.transition(State.DEVICE_READY)
    rejected = after == before and device.events[-1].accepted is False
    return {
        "status": "PASS" if rejected else "FAIL",
        "state": device.state.value,
        "rejected": rejected,
        "invariant_errors": device.validate_invariants(),
    }


def _recovery() -> dict[str, object]:
    result = asdict(run_scenario("recovery", "RESILIENCE-TOKEN"))
    return {
        "status": "PASS" if result["state"] == State.FACTORY_RESET.value else "FAIL",
        "final_state": result["state"],
        "events": len(result["events"]),
        "invariant_errors": result.get("invariant_errors", []),
    }


def _persistence_corruption() -> dict[str, object]:
    result = exercise_faults()
    return {
        "status": result["overall_status"],
        "coverage": result["coverage"],
        "rejected_cases": result["rejected_cases"],
        "unexpectedly_accepted": result["unexpectedly_accepted"],
    }


def exercise_resilience() -> dict[str, object]:
    transition = exercise_transitions()
    cases = {
        "normal": _normal(),
        "invalid-token": _invalid_token(),
        "illegal-transition": _illegal_transition(),
        "recovery": _recovery(),
        "persistence-corruption": _persistence_corruption(),
    }
    invariant_failures = sum(len(case.get("invariant_errors", [])) for case in cases.values())
    failed_cases = [name for name, case in cases.items() if case.get("status") != "PASS"]
    failed_cases.extend(
        ["transition-matrix"] if transition.get("overall_status") != "PASS" else []
    )
    result = {
        "schema": SCHEMA,
        "scope": SCOPE,
        "cases": cases,
        "case_count": len(cases),
        "failed_cases": failed_cases,
        "invariant_failures": invariant_failures,
        "transition_coverage": transition["coverage"],
        "transition_matrix_status": transition["overall_status"],
        "overall_status": "PASS" if not failed_cases and invariant_failures == 0 else "FAIL",
    }
    (ROOT / "resilience-matrix.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    return result


def main() -> int:
    result = exercise_resilience()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
