import pytest

from core import InvalidToken, InvalidTransition, State, VirtualDevice, run_full_scenario, run_setup_wizard_scenario


def test_full_scenario_reaches_ready():
    device = run_full_scenario("emu-001", "LAB-FRP-AB12CD34")
    assert device.state is State.DEVICE_READY
    assert len(device.events) == 4
    assert all(event.accepted for event in device.events)


def test_full_scenario_event_sequence_is_deterministic():
    device = run_full_scenario("emu-001", "LAB-FRP-AB12CD34")
    assert [(event.from_state, event.to_state) for event in device.events] == [
        (State.FACTORY_RESET.value, State.BOOT.value),
        (State.BOOT.value, State.FRP_LOCKED.value),
        (State.FRP_LOCKED.value, State.ACCOUNT_VERIFIED.value),
        (State.ACCOUNT_VERIFIED.value, State.DEVICE_READY.value),
    ]
    assert [event.sequence for event in device.events] == [1, 2, 3, 4]


def test_setup_wizard_bypass_transition_reaches_ready():
    device = run_setup_wizard_scenario("emu-setup-001")
    assert device.state is State.DEVICE_READY
    assert [(event.from_state, event.to_state) for event in device.events] == [
        (State.FACTORY_RESET.value, State.BOOT.value),
        (State.BOOT.value, State.FRP_LOCKED.value),
        (State.FRP_LOCKED.value, State.SETUP_WIZARD.value),
        (State.SETUP_WIZARD.value, State.SIMULATED_BYPASS.value),
        (State.SIMULATED_BYPASS.value, State.ACCOUNT_VERIFIED.value),
        (State.ACCOUNT_VERIFIED.value, State.DEVICE_READY.value),
    ]


def test_setup_wizard_bypass_requires_setup_wizard_state():
    device = VirtualDevice("emu-setup-002")
    device.transition(State.BOOT)
    device.transition(State.FRP_LOCKED)
    with pytest.raises(InvalidTransition):
        device.simulate_setup_bypass()
    assert device.state is State.FRP_LOCKED
    assert device.events[-1].reason == "setup_bypass_requires_setup_wizard"


def test_setup_wizard_rejects_invalid_profile():
    device = VirtualDevice("emu-setup-003")
    device.transition(State.BOOT)
    device.transition(State.FRP_LOCKED)
    device.enter_setup_wizard()
    with pytest.raises(ValueError):
        device.simulate_setup_bypass("INVALID PROFILE")
    assert device.state is State.SETUP_WIZARD
    assert device.events[-1].reason == "invalid_simulation_profile"


def test_invalid_transition_is_rejected_and_logged():
    device = VirtualDevice("emu-002")
    with pytest.raises(InvalidTransition):
        device.transition(State.DEVICE_READY)
    assert device.events[-1].accepted is False
    assert device.events[-1].reason == "invalid_transition"
    assert device.state is State.FACTORY_RESET


def test_invalid_token_is_rejected_without_state_change():
    device = VirtualDevice("emu-003")
    device.transition(State.BOOT)
    device.transition(State.FRP_LOCKED)
    with pytest.raises(InvalidToken):
        device.activate("real-credential")
    assert device.state is State.FRP_LOCKED
    assert device.events[-1].reason == "invalid_lab_token"
    assert device.events[-1].accepted is False


def test_persistence_round_trip():
    original = run_full_scenario("emu-004", "LAB-FRP-1234ABCD")
    restored = VirtualDevice.from_json(original.to_json())
    assert restored.to_dict() == original.to_dict()


def test_setup_wizard_persistence_round_trip():
    original = run_setup_wizard_scenario("emu-setup-004")
    restored = VirtualDevice.from_json(original.to_json())
    assert restored.to_dict() == original.to_dict()


def test_recovery_returns_to_factory_reset():
    device = run_full_scenario("emu-005", "LAB-FRP-A1B2C3D4")
    device.transition(State.RECOVERY)
    device.transition(State.FACTORY_RESET)
    assert device.state is State.FACTORY_RESET


def test_recovery_path_preserves_event_sequence():
    device = run_full_scenario("emu-006", "LAB-FRP-CAFEBEEF")
    device.transition(State.RECOVERY)
    device.transition(State.FACTORY_RESET)
    assert [event.sequence for event in device.events] == [1, 2, 3, 4, 5, 6]
    assert device.events[-1].to_state == State.FACTORY_RESET.value
