import pytest

from core import InvalidToken, InvalidTransition, State, VirtualDevice, run_full_scenario


def test_full_scenario_reaches_ready():
    device = run_full_scenario("emu-001", "LAB-FRP-AB12CD34")
    assert device.state is State.DEVICE_READY
    assert len(device.events) == 4
    assert all(event.accepted for event in device.events)


def test_invalid_transition_is_rejected_and_logged():
    device = VirtualDevice("emu-002")
    with pytest.raises(InvalidTransition):
        device.transition(State.DEVICE_READY)
    assert device.events[-1].accepted is False
    assert device.events[-1].reason == "invalid_transition"


def test_invalid_token_is_rejected():
    device = VirtualDevice("emu-003")
    device.transition(State.BOOT)
    device.transition(State.FRP_LOCKED)
    with pytest.raises(InvalidToken):
        device.activate("real-credential")
    assert device.state is State.FRP_LOCKED
    assert device.events[-1].reason == "invalid_lab_token"


def test_persistence_round_trip():
    original = run_full_scenario("emu-004", "LAB-FRP-1234ABCD")
    restored = VirtualDevice.from_json(original.to_json())
    assert restored.to_dict() == original.to_dict()


def test_recovery_returns_to_factory_reset():
    device = run_full_scenario("emu-005", "LAB-FRP-A1B2C3D4")
    device.transition(State.RECOVERY)
    device.transition(State.FACTORY_RESET)
    assert device.state is State.FACTORY_RESET
