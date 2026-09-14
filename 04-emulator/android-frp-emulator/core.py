"""Deterministic FRP state machine for the controlled Android FRP simulator.

SECURITY BOUNDARY: simulator-only policy modeling. Never accesses devices,
ADB/Fastboot, credentials, or real FRP state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import json
import re

from policy import DEFAULT_POLICY, PolicyProfile


class State(str, Enum):
    FACTORY_RESET = "FACTORY_RESET"
    BOOT = "BOOT"
    FRP_LOCKED = "FRP_LOCKED"
    ACCOUNT_VERIFIED = "ACCOUNT_VERIFIED"
    DEVICE_READY = "DEVICE_READY"
    RECOVERY = "RECOVERY"


class InvalidTransition(ValueError):
    pass


class InvalidToken(ValueError):
    pass


TOKEN_RE = re.compile(r"^LAB-FRP-[A-Z0-9]{8}$")
TRANSITIONS = {
    State.FACTORY_RESET: {State.BOOT},
    State.BOOT: {State.FRP_LOCKED},
    State.FRP_LOCKED: {State.ACCOUNT_VERIFIED},
    State.ACCOUNT_VERIFIED: {State.DEVICE_READY},
    State.DEVICE_READY: {State.RECOVERY},
    State.RECOVERY: {State.FACTORY_RESET},
}


@dataclass
class Event:
    sequence: int
    source: str
    from_state: str
    to_state: str
    accepted: bool
    reason: str


@dataclass
class VirtualDevice:
    device_id: str
    state: State = State.FACTORY_RESET
    events: list[Event] = field(default_factory=list)

    def transition(self, target: State, source: str = "simulator", policy: PolicyProfile = DEFAULT_POLICY) -> State:
        if target not in TRANSITIONS[self.state]:
            self._log(source, target, False, "invalid_transition")
            raise InvalidTransition(f"{self.state.value} -> {target.value} is not allowed")
        if target is State.RECOVERY and not policy.allows_recovery():
            self._log(source, target, False, f"policy_recovery_denied:{policy.name}")
            raise InvalidTransition(f"{self.state.value} -> {target.value} denied by policy {policy.name}")
        previous = self.state
        self.state = target
        self._log(source, target, True, "transition_accepted", previous)
        return self.state

    def activate(self, token: str, policy: PolicyProfile = DEFAULT_POLICY) -> State:
        if self.state is not State.FRP_LOCKED:
            self._log("activate", State.ACCOUNT_VERIFIED, False, "activation_requires_frp_locked")
            raise InvalidTransition("activation is only evaluated from FRP_LOCKED")
        if not policy.allows_account_activation():
            self._log("activate", State.ACCOUNT_VERIFIED, False, f"policy_activation_denied:{policy.name}")
            raise InvalidTransition(f"activation denied by policy {policy.name}")
        if not TOKEN_RE.fullmatch(token):
            self._log("activate", State.ACCOUNT_VERIFIED, False, "invalid_lab_token")
            raise InvalidToken("expected synthetic token format LAB-FRP-XXXXXXXX")
        return self.transition(State.ACCOUNT_VERIFIED, source="activate", policy=policy)

    def _log(self, source: str, target: State, accepted: bool, reason: str, previous: State | None = None) -> None:
        self.events.append(Event(len(self.events) + 1, source, (previous or self.state).value, target.value, accepted, reason))

    def validate_invariants(self) -> list[str]:
        errors: list[str] = []
        if [e.sequence for e in self.events] != list(range(1, len(self.events) + 1)):
            errors.append("event_sequence_not_contiguous")
        state = State.FACTORY_RESET
        for event in self.events:
            if event.from_state != state.value:
                errors.append("event_history_from_state_mismatch")
                break
            if event.accepted:
                try:
                    target = State(event.to_state)
                except ValueError:
                    errors.append("accepted_event_to_state_invalid")
                    break
                if target not in TRANSITIONS[state]:
                    errors.append("accepted_transition_illegal")
                    break
                if event.reason != "transition_accepted":
                    errors.append("accepted_event_reason_invalid")
                    break
                state = target
            elif event.reason == "invalid_transition":
                try:
                    target = State(event.to_state)
                except ValueError:
                    errors.append("rejected_event_to_state_invalid")
                    break
                if target in TRANSITIONS[state]:
                    errors.append("rejected_legal_transition")
                    break
            elif event.reason == "invalid_lab_token":
                if state is not State.FRP_LOCKED or event.to_state != State.ACCOUNT_VERIFIED.value:
                    errors.append("invalid_token_event_context_invalid")
                    break
            elif event.reason == "activation_requires_frp_locked":
                if state is State.FRP_LOCKED or event.to_state != State.ACCOUNT_VERIFIED.value:
                    errors.append("activation_rejection_context_invalid")
                    break
            elif event.reason.startswith("policy_"):
                if event.to_state not in {s.value for s in State}:
                    errors.append("policy_event_to_state_invalid")
                    break
            else:
                errors.append("unknown_rejection_reason")
                break
        if state.value != self.state.value:
            errors.append("serialized_state_does_not_match_history")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {"device_id": self.device_id, "state": self.state.value, "events": [e.__dict__ for e in self.events]}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VirtualDevice":
        device = cls(device_id=str(data["device_id"]), state=State(data["state"]))
        raw_events = data.get("events", [])
        if not isinstance(raw_events, list):
            raise ValueError("events must be a list")
        try:
            device.events = [Event(**event) for event in raw_events]
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid event payload") from exc
        errors = device.validate_invariants()
        if errors:
            raise ValueError("invalid persisted state: " + ",".join(errors))
        return device

    @classmethod
    def from_json(cls, payload: str) -> "VirtualDevice":
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("serialized device must be an object")
        return cls.from_dict(data)


def run_full_scenario(device_id: str, token: str) -> VirtualDevice:
    device = VirtualDevice(device_id)
    device.transition(State.BOOT)
    device.transition(State.FRP_LOCKED)
    device.activate(token)
    device.transition(State.DEVICE_READY)
    return device
