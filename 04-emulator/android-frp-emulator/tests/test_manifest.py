import hashlib
import json

import manifest


EXPECTED_SCENARIOS = {
    "normal",
    "invalid-token",
    "illegal-transition",
    "recovery",
}


def test_manifest_hashes_actual_evidence_and_preserves_audit_gates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    evidence = {
        "schema": "frp-emulator-evidence/v2",
        "scope": "controlled-simulator-only",
        "scenarios": [{"name": name} for name in sorted(EXPECTED_SCENARIOS)],
        "passed": True,
    }
    audit = {
        "schema": "frp-emulator-audit/v1",
        "overall_status": "PASS",
        "scenario_coverage": 1.0,
        "transition_coverage": 1.0,
        "invariant_failures": 0,
        "invalid_token_coverage": True,
        "recovery_coverage": True,
        "persistence_coverage": True,
        "security_boundary_status": "PASS:controlled-simulator-only",
    }
    evidence_path = tmp_path / "evidence.json"
    audit_path = tmp_path / "audit.json"
    evidence_path.write_text(json.dumps(evidence, sort_keys=True) + "\n")
    audit_path.write_text(json.dumps(audit, sort_keys=True) + "\n")
    monkeypatch.setattr(manifest, "_commit_sha", lambda: "TEST-COMMIT")

    result = manifest.build_manifest()

    assert result["schema"] == "frp-emulator-reproducibility-manifest/v1"
    assert result["scope"] == "controlled-simulator-only"
    assert result["commit_sha"] == "TEST-COMMIT"
    assert set(result["scenarios"]) == EXPECTED_SCENARIOS
    assert result["scenario_coverage"] == 1.0
    assert result["transition_coverage"] == 1.0
    assert result["invariant_failures"] == 0
    assert result["overall_status"] == "PASS"
    assert result["evidence_sha256"] == hashlib.sha256(evidence_path.read_bytes()).hexdigest()


def test_manifest_fails_when_evidence_or_audit_is_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "evidence.json").write_text("{}\n")

    try:
        manifest.build_manifest()
    except FileNotFoundError as exc:
        assert str(exc) == "evidence.json and audit.json must exist before manifest generation"
    else:
        raise AssertionError("build_manifest() must reject incomplete evidence/audit input")
