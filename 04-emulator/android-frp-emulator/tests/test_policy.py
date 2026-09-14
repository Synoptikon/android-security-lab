import pytest

from policy import DEFAULT_POLICY, STRICT_POLICY, get_policy


def test_default_policy_is_valid_and_allows_recovery():
    DEFAULT_POLICY.validate()
    assert DEFAULT_POLICY.allows_account_activation()
    assert DEFAULT_POLICY.allows_recovery()


def test_strict_policy_is_valid_and_blocks_recovery():
    STRICT_POLICY.validate()
    assert STRICT_POLICY.allows_account_activation()
    assert not STRICT_POLICY.allows_recovery()


def test_unknown_policy_is_rejected():
    with pytest.raises(KeyError, match="unknown policy profile"):
        get_policy("unknown")


def test_inconsistent_policy_is_rejected():
    from policy import PolicyProfile

    invalid = PolicyProfile(
        name="invalid",
        provisioning_required=True,
        account_verification_required=False,
        recovery_allowed=True,
        reset_returns_to_factory_state=True,
    )
    with pytest.raises(ValueError, match="requires account_verification_required"):
        invalid.validate()


def test_reset_policy_is_mandatory_for_controlled_lab():
    from policy import PolicyProfile

    invalid = PolicyProfile(
        name="unsafe-reset-model",
        provisioning_required=False,
        account_verification_required=False,
        recovery_allowed=True,
        reset_returns_to_factory_state=False,
    )
    with pytest.raises(ValueError, match="FACTORY_RESET"):
        invalid.validate()
