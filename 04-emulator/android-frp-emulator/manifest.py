"""Build a reproducibility manifest from the generated evidence and audit.

This layer records deterministic simulator metadata and cryptographic hashes.
It never accesses Android devices, ADB/Fastboot, credentials, or real FRP state.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

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
    evidence_path = Path("evidence.json")
    audit_path = Path("audit.json")
    if not evidence_path.exists() or not audit_path.exists():
        raise FileNotFoundError("evidence.json and audit.json must exist before manifest generation")

    evidence = json.loads(evidence_path.read_text())
    audit = json.loads(audit_path.read_text())
    passed = bool(evidence.get("passed")) and audit.get("overall_status") == "PASS"

    return {
        "schema": SCHEMA,
        "scope": "controlled-simulator-only",
        "commit_sha": _commit_sha(),
        "evidence_schema": evidence.get("schema"),
        "audit_schema": audit.get("schema"),
        "scenarios": [item["name"] for item in evidence.get("scenarios", [])],
        "scenario_coverage": audit.get("scenario_coverage"),
        "transition_coverage": audit.get("transition_coverage"),
        "invariant_failures": audit.get("invariant_failures"),
        "invalid_token_coverage": audit.get("invalid_token_coverage"),
        "recovery_coverage": audit.get("recovery_coverage"),
        "persistence_coverage": audit.get("persistence_coverage"),
        "security_boundary_status": audit.get("security_boundary_status"),
        "evidence_sha256": _sha256(evidence_path),
        "audit_status": audit.get("overall_status"),
        "overall_status": "PASS" if passed else "FAIL",
    }


def main() -> int:
    manifest = build_manifest()
    output = Path("reproducibility-manifest.json")
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if manifest["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
