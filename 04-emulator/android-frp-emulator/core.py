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

    def transition(
        self,
        target: State,
        source: str = "simulator",
        policy: PolicyProfile = DEFAULT_POLICY,
    ) -> State:
        if target not in TRANSITIONS[self.state]:
            self._log(source, target, False, "invalid_transition")
            raise InvalidTransition(f"{self.state.value} -> {target.value} is not allowed")
        if target is State.RECOVERY and not policy.allows_recovery():
            self._log(source, target, False, f"policy_recovery_denied:{policy.name}")
            raise InvalidTransition(
                f"{self.state.value} -> {target.value} denied by policy {policy.name}"
            )
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
        device.events = [Event(**event) for event in data.get("events", [])]
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
