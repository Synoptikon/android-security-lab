from audit import run_audit


def test_audit_reports_complete_coverage():
    report = run_audit()
    assert report.scenario_coverage == 1.0
    assert report.transition_coverage == 1.0
    assert report.uncovered_transitions == ()
    assert report.invalid_token_coverage is True
    assert report.recovery_coverage is True
    assert report.persistence_coverage is True
    assert report.invariant_failures == 0
    assert report.security_boundary_status.startswith("PASS:")
    assert report.overall_status == "PASS"
