from transition_matrix import exercise_transitions


def test_transition_matrix_is_complete_and_deterministic():
    first = exercise_transitions()
    second = exercise_transitions()
    assert first == second
    assert first["coverage"] == 1.0
    assert first["uncovered"] == []
    assert first["unexpected_rejections"] == []
    assert first["overall_status"] == "PASS"
