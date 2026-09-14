"""Presentation contract for the controlled Setup Wizard simulator.

SECURITY BOUNDARY: this module is presentation-only. It exposes the virtual
state machine to a future UI without adding Android/ADB/Fastboot operations,
credential handling, or real-device FRP bypass functionality.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from core import InvalidTransition, State, VirtualDevice


class WizardViewState(str, Enum):
    LOCKED = "LOCKED"
    SETUP_WIZARD = "SETUP_WIZARD"
    SIMULATED_BYPASS = "SIMULATED_BYPASS"
    ACCOUNT_VERIFIED = "ACCOUNT_VERIFIED"
    DEVICE_READY = "DEVICE_READY"


class WizardAction(str, Enum):
    ENTER_SETUP_WIZARD = "ENTER_SETUP_WIZARD"
    SIMULATE_BYPASS = "SIMULATE_BYPASS"
    CONTINUE = "CONTINUE"


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
    WizardViewState.SIMULATED_BYPASS: (WizardAction.CONTINUE,),
    WizardViewState.ACCOUNT_VERIFIED: (WizardAction.CONTINUE,),
    WizardViewState.DEVICE_READY: (),
}


@dataclass(frozen=True)
class SetupWizardViewModel:
    device_id: str
    state: WizardViewState
    allowed_actions: tuple[WizardAction, ...]
    profile: str = "lab-default"
    security_boundary: str = "controlled-simulator-only"

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "state": self.state.value,
            "allowed_actions": [action.value for action in self.allowed_actions],
            "profile": self.profile,
            "security_boundary": self.security_boundary,
        }

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def build_view_model(device: VirtualDevice, profile: str = "lab-default") -> SetupWizardViewModel:
    """Build the UI contract from the authoritative core state."""
    try:
        view_state = _STATE_TO_VIEW[device.state]
    except KeyError as exc:
        raise ValueError(f"state {device.state.value} is not exposed by the Setup Wizard UI") from exc
    return SetupWizardViewModel(
        device_id=device.device_id,
        state=view_state,
        allowed_actions=_ALLOWED_ACTIONS[view_state],
        profile=profile,
    )


def dispatch(device: VirtualDevice, action: WizardAction, profile: str = "lab-default") -> SetupWizardViewModel:
    """Apply one UI action through the core state machine and return the view."""
    view = build_view_model(device, profile)
    if action not in view.allowed_actions:
        raise InvalidTransition(f"action {action.value} is not allowed from {view.state.value}")

    if action is WizardAction.ENTER_SETUP_WIZARD:
        device.enter_setup_wizard()
    elif action is WizardAction.SIMULATE_BYPASS:
        device.simulate_setup_bypass(profile)
    elif action is WizardAction.CONTINUE:
        if device.state is State.SIMULATED_BYPASS:
            device.transition(State.DEVICE_READY, source="setup-wizard-ui")
        elif device.state is State.ACCOUNT_VERIFIED:
            device.transition(State.DEVICE_READY, source="setup-wizard-ui")
    return build_view_model(device, profile)
