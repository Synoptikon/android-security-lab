from scenario import run_scenario


def test_normal_scenario():
    result = run_scenario("normal", "scenario-001")
    assert result.passed
    assert result.state == "DEVICE_READY"
    assert result.event_count == 4
    assert result.rejected_events == 0


def test_invalid_token_scenario():
    result = run_scenario("invalid-token", "scenario-002")
    assert result.passed
    assert result.state == "FRP_LOCKED"
    assert result.accepted_events == 2
    assert result.rejected_events == 1


def test_illegal_transition_scenario():
    result = run_scenario("illegal-transition", "scenario-003")
    assert result.passed
    assert result.state == "FACTORY_RESET"
    assert result.rejected_events == 1


def test_recovery_scenario():
    result = run_scenario("recovery", "scenario-004")
    assert result.passed
    assert result.state == "FACTORY_RESET"
    assert result.event_count == 6
    assert result.rejected_events == 0
