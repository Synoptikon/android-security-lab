from resilience_matrix import exercise_resilience


def test_resilience_matrix_is_deterministic_and_complete():
    first = exercise_resilience()
    second = exercise_resilience()
    assert first == second
    assert first["case_count"] == 6
    assert first["failed_cases"] == []
    assert first["invariant_failures"] == 0
    assert first["transition_coverage"] == 1.0
    assert first["transition_matrix_status"] == "PASS"
    assert first["overall_status"] == "PASS"
