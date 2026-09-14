"""Deterministic FRP state machine for a virtual Android device.

SECURITY BOUNDARY: this module simulates policy decisions only. It never talks
ADB/Fastboot, accesses credentials, disables FRP, or operates on real devices.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import json
import re


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

    def transition(self, target: State, source: str = "simulator") -> State:
        if target not in TRANSITIONS[self.state]:
            self._log(source, target, False, "invalid_transition")
            raise InvalidTransition(f"{self.state.value} -> {target.value} is not allowed")
        previous = self.state
        self.state = target
        self._log(source, target, True, "transition_accepted", previous)
        return self.state

    def activate(self, token: str) -> State:
        if self.state is not State.FRP_LOCKED:
            self._log("activate", State.ACCOUNT_VERIFIED, False, "activation_requires_frp_locked")
            raise InvalidTransition("activation is only evaluated from FRP_LOCKED")
        if not TOKEN_RE.fullmatch(token):
            self._log("activate", State.ACCOUNT_VERIFIED, False, "invalid_lab_token")
            raise InvalidToken("expected synthetic token format LAB-FRP-XXXXXXXX")
        return self.transition(State.ACCOUNT_VERIFIED, source="activate")

    def _log(self, source: str, target: State, accepted: bool, reason: str, previous: State | None = None) -> None:
        self.events.append(Event(
            sequence=len(self.events) + 1,
            source=source,
            from_state=(previous or self.state).value,
            to_state=target.value,
            accepted=accepted,
            reason=reason,
        ))

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "state": self.state.value,
            "events": [e.__dict__ for e in self.events],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VirtualDevice":
        device = cls(device_id=str(data["device_id"]), state=State(data["state"]))
        events = [Event(**event) for event in data.get("events", [])]
        current = State.FACTORY_RESET
        for expected_sequence, event in enumerate(events, 1):
            if event.sequence != expected_sequence:
                raise ValueError("event sequence is not contiguous")
            try:
                source_state = State(event.from_state)
                target_state = State(event.to_state)
            except ValueError as exc:
                raise ValueError("event contains an unknown state") from exc
            if source_state is not current:
                raise ValueError("event history does not match previous state")
            if event.accepted:
                if target_state not in TRANSITIONS[current] or event.reason != "transition_accepted":
                    raise ValueError("accepted event violates the transition contract")
                current = target_state
            elif event.reason == "invalid_transition":
                if target_state in TRANSITIONS[current]:
                    raise ValueError("rejected event conflicts with transition contract")
            elif event.reason == "invalid_lab_token":
                if current is not State.FRP_LOCKED or target_state is not State.ACCOUNT_VERIFIED:
                    raise ValueError("invalid-token event violates activation contract")
            elif event.reason == "activation_requires_frp_locked":
                if current is State.FRP_LOCKED or target_state is not State.ACCOUNT_VERIFIED:
                    raise ValueError("activation rejection violates state contract")
            else:
                raise ValueError("unknown event rejection reason")
        if current is not device.state:
            raise ValueError("serialized state does not match event history")
        device.events = events
        return device

    @classmethod
    def from_json(cls, payload: str) -> "VirtualDevice":
        return cls.from_dict(json.loads(payload))


def run_full_scenario(device_id: str, token: str) -> VirtualDevice:
    device = VirtualDevice(device_id)
    device.transition(State.BOOT)
    device.transition(State.FRP_LOCKED)
    device.activate(token)
    device.transition(State.DEVICE_READY)
    return device
