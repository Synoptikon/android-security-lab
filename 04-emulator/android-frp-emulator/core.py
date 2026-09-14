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
    SETUP_WIZARD = "SETUP_WIZARD"
    SIMULATED_BYPASS = "SIMULATED_BYPASS"
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
    State.FRP_LOCKED: {State.ACCOUNT_VERIFIED, State.SETUP_WIZARD},
    State.SETUP_WIZARD: {State.SIMULATED_BYPASS},
    State.SIMULATED_BYPASS: {State.ACCOUNT_VERIFIED},
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

    def enter_setup_wizard(self) -> State:
        """Enter the simulated Setup Wizard from the FRP-locked state."""
        if self.state is not State.FRP_LOCKED:
            self._log("setup-wizard", State.SETUP_WIZARD, False, "setup_wizard_requires_frp_locked")
            raise InvalidTransition("Setup Wizard entry is only evaluated from FRP_LOCKED")
        return self.transition(State.SETUP_WIZARD, source="setup-wizard")

    def simulate_setup_bypass(self, profile: str = "lab-default") -> State:
        """Advance the simulator through a synthetic Setup Wizard bypass.

        This is a policy-state transition inside the controlled simulator. It
        does not bypass FRP on Android, access credentials, or interact with a
        real device.
        """
        if self.state is not State.SETUP_WIZARD:
            self._log("setup-bypass", State.SIMULATED_BYPASS, False, "setup_bypass_requires_setup_wizard")
            raise InvalidTransition("simulated bypass requires SETUP_WIZARD")
        if not profile or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,31}", profile):
            self._log("setup-bypass", State.SIMULATED_BYPASS, False, "invalid_simulation_profile")
            raise ValueError("simulation profile must be 1-32 lowercase alphanumeric characters, '-' or '_'")
        self.transition(State.SIMULATED_BYPASS, source=f"setup-bypass:{profile}")
        return self.transition(State.ACCOUNT_VERIFIED, source="setup-bypass:complete")

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
            elif event.reason == "setup_wizard_requires_frp_locked":
                if current is State.FRP_LOCKED or target_state is not State.SETUP_WIZARD:
                    raise ValueError("Setup Wizard rejection violates state contract")
            elif event.reason == "setup_bypass_requires_setup_wizard":
                if current is State.SETUP_WIZARD or target_state is not State.SIMULATED_BYPASS:
                    raise ValueError("simulated bypass rejection violates state contract")
            elif event.reason == "invalid_simulation_profile":
                if current is not State.SETUP_WIZARD or target_state is not State.SIMULATED_BYPASS:
                    raise ValueError("invalid-profile event violates Setup Wizard contract")
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


def run_setup_wizard_scenario(device_id: str, profile: str = "lab-default") -> VirtualDevice:
    """Run the complete controlled Setup Wizard transition path."""
    device = VirtualDevice(device_id)
    device.transition(State.BOOT)
    device.transition(State.FRP_LOCKED)
    device.enter_setup_wizard()
    device.simulate_setup_bypass(profile)
    device.transition(State.DEVICE_READY)
    return device


class WizardViewState(str, Enum):
    """Frontend-neutral presentation states exposed by the simulator."""
    LOCKED = "LOCKED"
    SETUP_WIZARD = "SETUP_WIZARD"
    SIMULATED_BYPASS = "SIMULATED_BYPASS"
    ACCOUNT_VERIFIED = "ACCOUNT_VERIFIED"
    DEVICE_READY = "DEVICE_READY"


class WizardAction(str, Enum):
    ENTER_SETUP_WIZARD = "ENTER_SETUP_WIZARD"
    SIMULATE_BYPASS = "SIMULATE_BYPASS"
    COMPLETE = "COMPLETE"


_STATE_TO_VIEW = {
    State.FRP_LOCKED: WizardViewState.LOCKED,
    State.SETUP_WIZARD: WizardViewState.SETUP_WIZARD,
    State.SIMULATED_BYPASS: WizardViewState.SIMULATED_BYPASS,
    State.ACCOUNT_VERIFIED: WizardViewState.ACCOUNT_VERIFIED,
    State.DEVICE_READY: WizardViewState.DEVICE_READY,
}

_ALLOWED_ACTIONS = {
    WizardViewState.LOCKED: (WizardAction.ENTER_SETUP_WIZARD,),
    WizardViewState.SETUP_WIZARD: (WizardAction.SIMULATE_BYPASS,),
    WizardViewState.SIMULATED_BYPASS: (),
    WizardViewState.ACCOUNT_VERIFIED: (WizardAction.COMPLETE,),
    WizardViewState.DEVICE_READY: (),
}


@dataclass(frozen=True)
class SetupWizardViewModel:
    """UI contract derived from the authoritative state machine."""
    device_id: str
    state: WizardViewState
    allowed_actions: tuple[str, ...]
    simulation_profile: str | None = None
    security_boundary: str = "controlled-simulator-only"

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "state": self.state.value,
            "allowed_actions": list(self.allowed_actions),
            "simulation_profile": self.simulation_profile,
            "security_boundary": self.security_boundary,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def build_setup_wizard_view(device: VirtualDevice, profile: str | None = None) -> SetupWizardViewModel:
    """Build a frontend-neutral view model without duplicating core policy."""
    try:
        view_state = _STATE_TO_VIEW[device.state]
    except KeyError as exc:
        raise ValueError(f"state {device.state.value} is not exposed by the Setup Wizard contract") from exc
    actions = tuple(action.value for action in _ALLOWED_ACTIONS[view_state])
    return SetupWizardViewModel(device.device_id, view_state, actions, profile)


def dispatch_setup_wizard_action(
    device: VirtualDevice,
    action: WizardAction,
    profile: str = "lab-default",
) -> SetupWizardViewModel:
    """Apply one UI action through the core state machine."""
    view = build_setup_wizard_view(device, profile)
    if action.value not in view.allowed_actions:
        raise ValueError(f"action {action.value} is not allowed from {view.state.value}")
    if action is WizardAction.ENTER_SETUP_WIZARD:
        device.enter_setup_wizard()
    elif action is WizardAction.SIMULATE_BYPASS:
        device.simulate_setup_bypass(profile)
    elif action is WizardAction.COMPLETE:
        device.transition(State.DEVICE_READY, source="setup-wizard:complete")
    else:
        raise ValueError(f"unsupported Setup Wizard action: {action.value}")
    return build_setup_wizard_view(device, profile)
