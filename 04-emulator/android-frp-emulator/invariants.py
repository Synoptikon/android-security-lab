"""Named invariants for the controlled FRP simulator.

SECURITY BOUNDARY: this module evaluates synthetic simulator state only. It
never accesses Android devices, ADB/Fastboot, credentials, or real FRP state.
"""
from __future__ import annotations

from dataclasses import dataclass

from core import Event, State, TRANSITIONS
from policy import PolicyProfile


@dataclass(frozen=True)
class InvariantResult:
    name: str
    passed: bool
    detail: str = ""


INVARIANT_NAMES = (
    "event_sequence_contiguous",
    "accepted_transitions_legal",
    "policy_denials_are_non_mutating",
    "invalid_token_never_verifies_account",
    "recovery_policy_is_respected",
    "final_state_matches_accepted_history",
)


def evaluate_invariants(
    state: State,
    events: list[Event],
    policy: PolicyProfile,
) -> list[InvariantResult]:
    """Evaluate explicit safety properties over one synthetic simulator trace."""
    results: list[InvariantResult] = []
    results.append(
        InvariantResult(
            "event_sequence_contiguous",
            [event.sequence for event in events] == list(range(1, len(events) + 1)),
        )
    )

    current = State.FACTORY_RESET
    accepted_legal = True
    for event in events:
        if event.accepted:
            try:
                target = State(event.to_state)
            except ValueError:
                accepted_legal = False
                break
            if event.from_state != current.value or target not in TRANSITIONS[current]:
                accepted_legal = False
                break
            current = target
    results.append(InvariantResult("accepted_transitions_legal", accepted_legal))

    policy_denials_non_mutating = all(
        not event.accepted
        or not event.reason.startswith("policy_")
        or event.from_state == event.to_state
        for event in events
    )
    results.append(
        InvariantResult("policy_denials_are_non_mutating", policy_denials_non_mutating)
    )

    invalid_token_safe = all(
        event.reason != "invalid_lab_token"
        or event.to_state != State.ACCOUNT_VERIFIED.value
        or not event.accepted
        for event in events
    )
    results.append(
        InvariantResult("invalid_token_never_verifies_account", invalid_token_safe)
    )

    recovery_allowed = policy.allows_recovery()
    recovery_policy_respected = all(
        event.to_state != State.RECOVERY
        or event.accepted == recovery_allowed
        for event in events
    )
    results.append(
        InvariantResult("recovery_policy_is_respected", recovery_policy_respected)
    )

    results.append(
        InvariantResult(
            "final_state_matches_accepted_history",
            state is current,
        )
    )
    return results


def assert_invariants(state: State, events: list[Event], policy: PolicyProfile) -> None:
    """Raise a deterministic error if any named invariant fails."""
    failures = [result.name for result in evaluate_invariants(state, events, policy) if not result.passed]
    if failures:
        raise AssertionError("invariant failures: " + ",".join(failures))
