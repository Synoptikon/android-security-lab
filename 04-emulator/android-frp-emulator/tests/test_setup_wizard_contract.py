import pytest

from core import InvalidTransition, State, VirtualDevice
from setup_wizard_contract import WizardAction, WizardViewState, build_view_model, dispatch


def test_locked_view_exposes_only_setup_wizard_entry():
    device = VirtualDevice("ui-001")
    device.transition(State.BOOT)
    device.transition(State.FRP_LOCKED)
    view = build_view_model(device)
    assert view.state is WizardViewState.LOCKED
    assert view.allowed_actions == (WizardAction.ENTER_SETUP_WIZARD,)
    assert view.security_boundary == "controlled-simulator-only"


def test_dispatch_follows_core_authority():
    device = VirtualDevice("ui-002")
    device.transition(State.BOOT)
    device.transition(State.FRP_LOCKED)
    view = dispatch(device, WizardAction.ENTER_SETUP_WIZARD)
    assert view.state is WizardViewState.SETUP_WIZARD
    view = dispatch(device, WizardAction.SIMULATE_BYPASS)
    assert view.state is WizardViewState.ACCOUNT_VERIFIED
    view = dispatch(device, WizardAction.CONTINUE)
    assert view.state is WizardViewState.DEVICE_READY
    assert device.events[-1].source == "setup-wizard-ui"


def test_illegal_ui_action_is_rejected_without_state_change():
    device = VirtualDevice("ui-003")
    device.transition(State.BOOT)
    device.transition(State.FRP_LOCKED)
    with pytest.raises(InvalidTransition):
        dispatch(device, WizardAction.SIMULATE_BYPASS)
    assert device.state is State.FRP_LOCKED


def test_view_model_json_is_stable_and_explicit():
    device = VirtualDevice("ui-004")
    device.transition(State.BOOT)
    device.transition(State.FRP_LOCKED)
    payload = build_view_model(device).to_json()
    assert '"allowed_actions": [\n    "ENTER_SETUP_WIZARD"\n  ]' in payload
    assert '"security_boundary": "controlled-simulator-only"' in payload
    assert '"state": "LOCKED"' in payload
