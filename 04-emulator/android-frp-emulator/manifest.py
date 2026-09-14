"""Build a reproducibility manifest from the latest emulator evidence and audit.

This layer records only deterministic simulator metadata and cryptographic hashes.
It never accesses Android devices, ADB/Fastboot, credentials, or real FRP state.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from audit import run_audit
from scenario import SCENARIOS, run_scenario

SCHEMA = "frp-emulator-reproducibility-manifest/v1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _commit_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def build_manifest() -> dict[str, object]:
    results = [run_scenario(name, f"manifest-{index:03d}") for index, name in enumerate(SCENARIOS, 1)]
    audit = run_audit()

    evidence = {
        "schema": "frp-emulator-evidence/v2",
        "scope": "controlled-simulator-only",
        "scenarios": [result.__dict__ for result in results],
        "audit": audit.to_dict(),
        "passed": all(result.passed for result in results) and audit.overall_status == "PASS",
    }
    evidence_path = Path("manifest-evidence.json")
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")

    manifest = {
        "schema": SCHEMA,
        "scope": "controlled-simulator-only",
        "commit_sha": _commit_sha(),
        "evidence_schema": evidence["schema"],
        "audit_schema": audit.schema,
        "scenarios": list(SCENARIOS),
        "scenario_coverage": audit.scenario_coverage,
        "transition_coverage": audit.transition_coverage,
        "invariant_failures": audit.invariant_failures,
        "invalid_token_coverage": audit.invalid_token_coverage,
        "recovery_coverage": audit.recovery_coverage,
        "persistence_coverage": audit.persistence_coverage,
        "security_boundary_status": audit.security_boundary_status,
        "evidence_sha256": _sha256(evidence_path),
        "audit_status": audit.overall_status,
        "overall_status": "PASS" if evidence["passed"] else "FAIL",
    }
    return manifest


def main() -> int:
    manifest = build_manifest()
    output = Path("reproducibility-manifest.json")
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if manifest["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
