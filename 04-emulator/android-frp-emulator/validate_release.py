"""Release gate for the controlled FRP simulator.

This validator checks generated artifacts only. It never accesses Android devices,
ADB/Fastboot, credentials, or real FRP state.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(name: str) -> dict[str, object]:
    path = ROOT / name
    if not path.is_file():
        raise SystemExit(f"missing artifact: {name}")
    return json.loads(path.read_text())


def main() -> int:
    evidence = load("evidence.json")
    audit = load("audit.json")
    manifest = load("reproducibility-manifest.json")

    evidence_path = ROOT / "evidence.json"
    evidence_sha = hashlib.sha256(evidence_path.read_bytes()).hexdigest()

    checks = {
        "scope": evidence.get("scope") == "controlled-simulator-only"
        and audit.get("scope") == "controlled-simulator-only"
        and manifest.get("scope") == "controlled-simulator-only",
        "evidence_passed": evidence.get("passed") is True,
        "audit_passed": audit.get("overall_status") == "PASS",
        "scenario_coverage": audit.get("scenario_coverage") == 1.0,
        "transition_coverage": audit.get("transition_coverage") == 1.0,
        "invariants": audit.get("invariant_failures") == 0,
        "invalid_token_coverage": audit.get("invalid_token_coverage") is True,
        "recovery_coverage": audit.get("recovery_coverage") is True,
        "persistence_coverage": audit.get("persistence_coverage") is True,
        "security_boundary": audit.get("security_boundary_status") == "PASS:controlled-simulator-only",
        "manifest_passed": manifest.get("overall_status") == "PASS",
        "evidence_hash": manifest.get("evidence_sha256") == evidence_sha,
        "commit_recorded": bool(manifest.get("commit_sha"))
        and manifest.get("commit_sha") != "unknown",
    }

    failed = [name for name, passed in checks.items() if not passed]
    print(json.dumps({"checks": checks, "failed": failed}, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
