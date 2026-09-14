from fault_injection import exercise_faults


def test_fault_injection_rejects_corrupted_persistence_deterministically():
    first = exercise_faults()
    second = exercise_faults()
    assert first == second
    assert first["coverage"] == 1.0
    assert first["rejected_cases"] == ["invalid_state", "malformed_json", "tampered_event"]
    assert first["unexpectedly_accepted"] == []
    assert first["overall_status"] == "PASS"
