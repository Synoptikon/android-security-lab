"""Deterministic release gate for the controlled FRP simulator.

This gate validates generated artifacts only. It never accesses Android devices,
ADB/Fastboot, credentials, or real FRP state.
"""
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
    evidence_hash = hashlib.sha256((ROOT / "evidence.json").read_bytes()).hexdigest()
    checks = {
        "scope": all(item.get("scope") == "controlled-simulator-only" for item in (evidence, audit, matrix)),
        "evidence_passed": evidence.get("overall_status") == "PASS",
        "audit_passed": audit.get("overall_status") == "PASS",
        "scenario_coverage": audit.get("scenario_coverage") == 1.0,
        "transition_coverage": audit.get("transition_coverage") == 1.0,
        "matrix_passed": matrix.get("overall_status") == "PASS",
        "matrix_coverage": matrix.get("coverage") == 1.0,
        "matrix_uncovered": matrix.get("uncovered") == [],
        "invalid_token_coverage": audit.get("invalid_token_coverage") is True,
        "recovery_coverage": audit.get("recovery_coverage") is True,
        "persistence_coverage": audit.get("persistence_coverage") is True,
        "invariant_failures": audit.get("invariant_failures") == 0,
        "security_boundary": audit.get("security_boundary_status") == "PASS:controlled-simulator-only",
        "manifest_passed": manifest.get("overall_status") == "PASS",
        "evidence_sha256": manifest.get("evidence_sha256") == evidence_hash,
        "commit_sha_present": bool(manifest.get("commit_sha")) and manifest.get("commit_sha") != "unknown",
    }
    failed = [name for name, passed in checks.items() if not passed]
    result = {"schema": "frp-emulator-release-gate/v2", "checks": checks, "failed": failed,
              "overall_status": "PASS" if not failed else "FAIL"}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
