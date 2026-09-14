"""Deterministic policy profiles for the controlled FRP simulator.

SECURITY BOUNDARY: profiles model policy decisions only. They never access
Android devices, ADB/Fastboot, credentials, or real FRP state.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyProfile:
    name: str
    provisioning_required: bool
    account_verification_required: bool
    recovery_allowed: bool
    reset_returns_to_factory_state: bool

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("policy name must not be empty")
        if not self.account_verification_required and self.provisioning_required:
            raise ValueError(
                "provisioning_required requires account_verification_required in the lab model"
            )
        if not self.reset_returns_to_factory_state:
            raise ValueError("the controlled lab requires reset to return to FACTORY_RESET")

    def allows_account_activation(self) -> bool:
        return self.account_verification_required

    def allows_recovery(self) -> bool:
        return self.recovery_allowed


DEFAULT_POLICY = PolicyProfile(
    name="default",
    provisioning_required=True,
    account_verification_required=True,
    recovery_allowed=True,
    reset_returns_to_factory_state=True,
)

STRICT_POLICY = PolicyProfile(
    name="strict",
    provisioning_required=True,
    account_verification_required=True,
    recovery_allowed=False,
    reset_returns_to_factory_state=True,
)

POLICIES: dict[str, PolicyProfile] = {
    profile.name: profile for profile in (DEFAULT_POLICY, STRICT_POLICY)
}


def get_policy(name: str) -> PolicyProfile:
    try:
        profile = POLICIES[name]
    except KeyError as exc:
        raise KeyError(f"unknown policy profile: {name}") from exc
    profile.validate()
    return profile
