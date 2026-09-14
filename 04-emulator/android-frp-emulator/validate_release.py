"""Deterministic release gate for the controlled FRP simulator."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(name: str) -> dict[str, object]:
    return json.loads((ROOT / name).read_text())


def main() -> int:
    evidence = load("evidence.json")
    audit = load("audit.json")
    manifest = load("reproducibility-manifest.json")
    matrix = load("transition-matrix.json")
    faults = load("fault-injection.json")
    resilience = load("resilience-matrix.json")
    evidence_hash = hashlib.sha256((ROOT / "evidence.json").read_bytes()).hexdigest()
    checks = {
        "scope": all(
            x.get("scope") == "controlled-simulator-only"
            for x in (evidence, audit, matrix, faults, resilience)
        ),
        "evidence_passed": evidence.get("overall_status") == "PASS",
        "audit_passed": audit.get("overall_status") == "PASS",
        "scenario_coverage": audit.get("scenario_coverage") == 1.0,
        "transition_coverage": audit.get("transition_coverage") == 1.0,
        "matrix_passed": matrix.get("overall_status") == "PASS",
        "matrix_coverage": matrix.get("coverage") == 1.0,
        "matrix_uncovered": matrix.get("uncovered") == [],
        "fault_injection_passed": faults.get("overall_status") == "PASS",
        "fault_injection_coverage": faults.get("coverage") == 1.0,
        "faults_unexpectedly_accepted": faults.get("unexpectedly_accepted") == [],
        "resilience_passed": resilience.get("overall_status") == "PASS",
        "resilience_failed_cases": resilience.get("failed_cases") == [],
        "resilience_invariant_failures": resilience.get("invariant_failures") == 0,
        "resilience_transition_coverage": resilience.get("transition_coverage") == 1.0,
        "invalid_token_coverage": audit.get("invalid_token_coverage") is True,
        "recovery_coverage": audit.get("recovery_coverage") is True,
        "persistence_coverage": audit.get("persistence_coverage") is True,
        "invariant_failures": audit.get("invariant_failures") == 0,
        "security_boundary": audit.get("security_boundary_status") == "PASS:controlled-simulator-only",
        "manifest_passed": manifest.get("overall_status") == "PASS",
        "evidence_sha256": manifest.get("evidence_sha256") == evidence_hash,
        "commit_sha_present": bool(manifest.get("commit_sha")) and manifest.get("commit_sha") != "unknown",
    }
    failed = [key for key, value in checks.items() if not value]
    result = {
        "schema": "frp-emulator-release-gate/v4",
        "checks": checks,
        "failed": failed,
        "overall_status": "PASS" if not failed else "FAIL",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
