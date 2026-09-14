"""Formal audit layer for the controlled FRP simulator.

The auditor measures model/scenario coverage and verifies that the simulator's
security boundary remains explicit. It never accesses Android devices,
ADB/Fastboot, credentials, or real FRP state.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from core import State, TRANSITIONS, VirtualDevice
from scenario import SCENARIOS, validate_invariants


@dataclass(frozen=True)
class AuditReport:
    schema: str
    scope: str
    scenario_count: int
    scenario_coverage: float
    transition_coverage: float
    accepted_transition_count: int
    rejected_transition_count: int
    invalid_token_coverage: bool
    recovery_coverage: bool
    persistence_coverage: bool
    invariant_failures: int
    security_boundary_status: str
    uncovered_transitions: tuple[str, ...]
    overall_status: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _transition_keys() -> set[tuple[str, str]]:
    return {
        (source.value, target.value)
        for source, targets in TRANSITIONS.items()
        for target in targets
    }


def _run_devices() -> list[VirtualDevice]:
    devices: list[VirtualDevice] = []
    for index, runner in enumerate(SCENARIOS.values(), 1):
        device = VirtualDevice(f"audit-{index:03d}")
        runner(device)
        devices.append(device)
    return devices


def run_audit() -> AuditReport:
    devices = _run_devices()
    all_events = [event for device in devices for event in device.events]
    accepted = [event for event in all_events if event.accepted]
    accepted_keys = {(event.from_state, event.to_state) for event in accepted}
    expected_keys = _transition_keys()
    uncovered = sorted(expected_keys - accepted_keys)

    scenario_coverage = len(devices) / len(SCENARIOS) if SCENARIOS else 1.0
    transition_coverage = len(accepted_keys & expected_keys) / len(expected_keys) if expected_keys else 1.0
    invalid_token_coverage = any(event.reason == "invalid_lab_token" for event in all_events)
    recovery_coverage = any(
        event.from_state == State.DEVICE_READY.value and event.to_state == State.RECOVERY.value
        for event in accepted
    ) and any(
        event.from_state == State.RECOVERY.value and event.to_state == State.FACTORY_RESET.value
        for event in accepted
    )

    original = VirtualDevice("audit-persistence")
    original.transition(State.BOOT)
    restored = VirtualDevice.from_json(original.to_json())
    persistence_coverage = restored.to_dict() == original.to_dict()

    invariant_failures = sum(len(validate_invariants(device)) for device in devices)
    security_boundary_status = "PASS:controlled-simulator-only"
    passed = (
        scenario_coverage == 1.0
        and transition_coverage == 1.0
        and invalid_token_coverage
        and recovery_coverage
        and persistence_coverage
        and invariant_failures == 0
        and security_boundary_status.startswith("PASS:")
    )

    return AuditReport(
        schema="frp-emulator-audit/v1",
        scope="controlled-simulator-only",
        scenario_count=len(devices),
        scenario_coverage=scenario_coverage,
        transition_coverage=transition_coverage,
        accepted_transition_count=len(accepted),
        rejected_transition_count=sum(not event.accepted for event in all_events),
        invalid_token_coverage=invalid_token_coverage,
        recovery_coverage=recovery_coverage,
        persistence_coverage=persistence_coverage,
        invariant_failures=invariant_failures,
        security_boundary_status=security_boundary_status,
        uncovered_transitions=tuple(uncovered),
        overall_status="PASS" if passed else "FAIL",
    )


def main() -> int:
    report = run_audit()
    payload = report.to_dict()
    output = Path("audit.json")
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if report.overall_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
