"""Deterministic fault-injection audit for the controlled FRP simulator."""
from __future__ import annotations

import json
from pathlib import Path

from core import State, VirtualDevice

ROOT = Path(__file__).resolve().parent
REPORT_PATH = ROOT / "fault-injection.json"


def baseline() -> VirtualDevice:
    device = VirtualDevice("fault-baseline")
    device.transition(State.BOOT)
    device.transition(State.FRP_LOCKED)
    return device


def cases() -> dict[str, object]:
    valid = json.loads(baseline().to_json())
    bad_state = dict(valid)
    bad_state["state"] = "NOT_A_STATE"
    bad_event = dict(valid)
    bad_event["events"] = [{
        "sequence": 2,
        "source": "simulator",
        "from_state": "FACTORY_RESET",
        "to_state": "BOOT",
        "accepted": True,
        "reason": "transition_accepted",
    }]
    return {"malformed_json": "{\"device_id\":", "invalid_state": bad_state, "tampered_event": bad_event}


def exercise_faults() -> dict[str, object]:
    rejected: list[str] = []
    accepted_faults: list[str] = []
    fault_cases = cases()
    try:
        VirtualDevice.from_json(fault_cases["malformed_json"])
    except (json.JSONDecodeError, TypeError, KeyError, ValueError):
        rejected.append("malformed_json")
    try:
        VirtualDevice.from_dict(fault_cases["invalid_state"])
    except (KeyError, ValueError, TypeError):
        rejected.append("invalid_state")
    try:
        VirtualDevice.from_dict(fault_cases["tampered_event"])
    except (KeyError, ValueError, TypeError):
        rejected.append("tampered_event")
    else:
        accepted_faults.append("tampered_event")
    expected = {"malformed_json", "invalid_state", "tampered_event"}
    return {
        "schema": "frp-emulator-fault-injection/v1",
        "scope": "controlled-simulator-only",
        "expected_cases": sorted(expected),
        "rejected_cases": sorted(rejected),
        "unexpectedly_accepted": sorted(accepted_faults),
        "coverage": len(set(rejected) & expected) / len(expected),
        "overall_status": "PASS" if set(rejected) == expected and not accepted_faults else "FAIL",
    }


def main() -> int:
    report = exercise_faults()
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
