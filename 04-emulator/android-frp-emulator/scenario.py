"""Scenario and invariant layer for the controlled FRP simulator.

This module defines reproducible lab scenarios and checks observable invariants.
It never accesses Android devices, ADB/Fastboot, real credentials, or FRP data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from core import InvalidToken, InvalidTransition, State, VirtualDevice
from policy import DEFAULT_POLICY, STRICT_POLICY, PolicyProfile, get_policy


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    policy: str
    passed: bool
    state: str
    event_count: int
    accepted_events: int
    rejected_events: int
    policy_decisions: int
    invariant_errors: tuple[str, ...]


def _normal(device: VirtualDevice, policy: PolicyProfile = DEFAULT_POLICY) -> None:
    device.transition(State.BOOT, policy=policy)
    device.transition(State.FRP_LOCKED, policy=policy)
    device.activate("LAB-FRP-AB12CD34", policy=policy)
    device.transition(State.DEVICE_READY, policy=policy)


def _invalid_token(device: VirtualDevice, policy: PolicyProfile = DEFAULT_POLICY) -> None:
    device.transition(State.BOOT, policy=policy)
    device.transition(State.FRP_LOCKED, policy=policy)
    try:
        device.activate("INVALID", policy=policy)
    except InvalidToken:
        pass


def _illegal_transition(device: VirtualDevice, policy: PolicyProfile = DEFAULT_POLICY) -> None:
    try:
        device.transition(State.DEVICE_READY, policy=policy)
    except InvalidTransition:
        pass


def _recovery(device: VirtualDevice, policy: PolicyProfile = DEFAULT_POLICY) -> None:
    _normal(device, policy)
    device.transition(State.RECOVERY, policy=policy)
    device.transition(State.FACTORY_RESET, policy=policy)


def _strict_recovery(device: VirtualDevice, policy: PolicyProfile = STRICT_POLICY) -> None:
    _normal(device, policy)
    try:
        device.transition(State.RECOVERY, policy=policy)
    except InvalidTransition:
        pass


SCENARIOS: dict[str, Callable[[VirtualDevice], None]] = {
    "normal": _normal,
    "invalid-token": _invalid_token,
    "illegal-transition": _illegal_transition,
    "recovery": _recovery,
    "strict-recovery": _strict_recovery,
}

SCENARIO_POLICIES: dict[str, PolicyProfile] = {
    "normal": DEFAULT_POLICY,
    "invalid-token": DEFAULT_POLICY,
    "illegal-transition": DEFAULT_POLICY,
    "recovery": DEFAULT_POLICY,
    "strict-recovery": STRICT_POLICY,
}


def validate_invariants(device: VirtualDevice) -> list[str]:
    errors: list[str] = []
    if [event.sequence for event in device.events] != list(range(1, len(device.events) + 1)):
        errors.append("event_sequence_not_contiguous")
    if any(event.accepted and event.from_state == event.to_state for event in device.events):
        errors.append("accepted_self_transition")
    for event in device.events:
        if event.accepted and event.reason != "transition_accepted":
            errors.append("accepted_event_reason_invalid")
    return errors


def run_scenario(name: str, device_id: str, policy: str | None = None) -> ScenarioResult:
    try:
        runner = SCENARIOS[name]
    except KeyError as exc:
        raise ValueError(f"unknown scenario: {name}") from exc
    selected_policy = get_policy(policy) if policy else SCENARIO_POLICIES[name]
    device = VirtualDevice(device_id)
    runner(device, selected_policy)
    errors = validate_invariants(device)
    policy_decisions = sum(
        event.reason.startswith("policy_") for event in device.events
    )
    return ScenarioResult(
        name=name,
        policy=selected_policy.name,
        passed=not errors,
        state=device.state.value,
        event_count=len(device.events),
        accepted_events=sum(event.accepted for event in device.events),
        rejected_events=sum(not event.accepted for event in device.events),
        policy_decisions=policy_decisions,
        invariant_errors=tuple(errors),
    )
