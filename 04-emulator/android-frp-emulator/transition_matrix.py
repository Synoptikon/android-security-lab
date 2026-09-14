"""Deterministic transition-matrix audit for the controlled FRP simulator.

This module models only the simulator's explicit state graph. It never accesses
Android devices, ADB/Fastboot, credentials, or real FRP state.
"""
from __future__ import annotations

import json
from pathlib import Path

from core import TRANSITIONS, VirtualDevice


def expected_transitions() -> set[tuple[str, str]]:
    return {
        (source.value, target.value)
        for source, targets in TRANSITIONS.items()
        for target in targets
    }


def exercise_transitions() -> dict[str, object]:
    expected = expected_transitions()
    observed: set[tuple[str, str]] = set()
    rejected: list[dict[str, str]] = []

    for source, targets in TRANSITIONS.items():
        for target in targets:
            device = VirtualDevice(f"matrix-{source.value}-{target.value}")
            device.state = source
            previous = device.state.value
            result = device.transition(target)
            if result is target:
                observed.add((previous, result.value))
            else:
                rejected.append({"from": previous, "to": target.value})

    uncovered = sorted(expected - observed)
    return {
        "schema": "frp-emulator-transition-matrix/v1",
        "scope": "controlled-simulator-only",
        "expected_count": len(expected),
        "observed_count": len(observed),
        "coverage": len(observed & expected) / len(expected) if expected else 1.0,
        "uncovered": uncovered,
        "unexpected_rejections": rejected,
        "overall_status": "PASS" if not uncovered and not rejected else "FAIL",
    }


def main() -> int:
    report = exercise_transitions()
    Path("transition-matrix.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
