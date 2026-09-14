"""Scenario and invariant layer for the controlled FRP simulator.

This module defines reproducible lab scenarios and checks observable invariants.
It never accesses Android devices, ADB/Fastboot, real credentials, or FRP data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from core import InvalidToken, InvalidTransition, State, VirtualDevice


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    passed: bool
    state: str
    event_count: int
    accepted_events: int
    rejected_events: int
    invariant_errors: tuple[str, ...]


def _normal(device: VirtualDevice) -> None:
    device.transition(State.BOOT)
    device.transition(State.FRP_LOCKED)
    device.activate("LAB-FRP-AB12CD34")
    device.transition(State.DEVICE_READY)


def _invalid_token(device: VirtualDevice) -> None:
    device.transition(State.BOOT)
    device.transition(State.FRP_LOCKED)
    try:
        device.activate("INVALID")
    except InvalidToken:
        pass


def _illegal_transition(device: VirtualDevice) -> None:
    try:
        device.transition(State.DEVICE_READY)
    except InvalidTransition:
        pass


def _recovery(device: VirtualDevice) -> None:
    _normal(device)
    device.transition(State.RECOVERY)
    device.transition(State.FACTORY_RESET)


SCENARIOS: dict[str, Callable[[VirtualDevice], None]] = {
    "normal": _normal,
    "invalid-token": _invalid_token,
    "illegal-transition": _illegal_transition,
    "recovery": _recovery,
}


def validate_invariants(device: VirtualDevice) -> list[str]:
    errors: list[str] = []
    if [event.sequence for event in device.events] != list(range(1, len(device.events) + 1)):
        errors.append("event_sequence_not_contiguous")
    if any(event.accepted and event.from_state == event.to_state for event in device.events):
        errors.append("accepted_self_transition")
    for event in device.events:
        if event.accepted and event.reason not in {"transition_accepted"}:
            errors.append("accepted_event_reason_invalid")
    return errors


def run_scenario(name: str, device_id: str) -> ScenarioResult:
    try:
        runner = SCENARIOS[name]
    except KeyError as exc:
        raise ValueError(f"unknown scenario: {name}") from exc
    device = VirtualDevice(device_id)
    runner(device)
    errors = validate_invariants(device)
    return ScenarioResult(
        name=name,
        passed=not errors,
        state=device.state.value,
        event_count=len(device.events),
        accepted_events=sum(event.accepted for event in device.events),
        rejected_events=sum(not event.accepted for event in device.events),
        invariant_errors=tuple(errors),
    )
