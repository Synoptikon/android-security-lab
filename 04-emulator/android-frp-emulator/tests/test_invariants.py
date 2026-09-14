from __future__ import annotations

from core import State, VirtualDevice
from invariants import INVARIANT_NAMES, evaluate_invariants
from policy import DEFAULT_POLICY, STRICT_POLICY
from scenario import SCENARIO_POLICIES, SCENARIOS


def test_named_invariants_cover_expected_policy_contract() -> None:
    assert INVARIANT_NAMES == (
        "event_sequence_contiguous",
        "accepted_transitions_legal",
        "policy_denials_are_non_mutating",
        "invalid_token_never_verifies_account",
        "recovery_policy_is_respected",
        "final_state_matches_accepted_history",
    )


def test_all_controlled_scenarios_satisfy_named_invariants() -> None:
    for name, runner in SCENARIOS.items():
        policy = SCENARIO_POLICIES[name]
        device = VirtualDevice(f"INV-{name}")
        runner(device, policy)
        results = evaluate_invariants(device.state, device.events, policy)
        assert [result.name for result in results] == list(INVARIANT_NAMES)
        assert all(result.passed for result in results), name


def test_strict_policy_rejects_recovery_without_state_mutation() -> None:
    device = VirtualDevice("INV-STRICT")
    from scenario import _normal
    from core import InvalidTransition

    _normal(device, STRICT_POLICY)
    before = device.state
    try:
        device.transition(State.RECOVERY, policy=STRICT_POLICY)
    except InvalidTransition:
        pass

    assert before is State.DEVICE_READY
    assert device.state is State.DEVICE_READY
    results = evaluate_invariants(device.state, device.events, STRICT_POLICY)
    assert all(result.passed for result in results)


def test_invalid_token_cannot_produce_account_verified_state() -> None:
    device = VirtualDevice("INV-TOKEN")
    device.transition(State.BOOT, policy=DEFAULT_POLICY)
    device.transition(State.FRP_LOCKED, policy=DEFAULT_POLICY)
    from core import InvalidToken
    try:
        device.activate("INVALID", policy=DEFAULT_POLICY)
    except InvalidToken:
        pass

    assert device.state is State.FRP_LOCKED
    results = evaluate_invariants(device.state, device.events, DEFAULT_POLICY)
    assert all(result.passed for result in results)
