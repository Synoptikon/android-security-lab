"""Run scenarios and formal audit, then emit machine-readable evidence."""
from __future__ import annotations

import json
from pathlib import Path

from audit import run_audit
from manifest import build_manifest
from scenario import SCENARIOS, run_scenario


def main() -> int:
    results = [run_scenario(name, f"ci-{index:03d}") for index, name in enumerate(SCENARIOS, 1)]
    audit = run_audit()
    passed = all(result.passed for result in results) and audit.overall_status == "PASS"
    payload = {
        "schema": "frp-emulator-evidence/v2",
        "scope": "controlled-simulator-only",
        "scenarios": [result.__dict__ for result in results],
        "audit": audit.to_dict(),
        "passed": passed,
        "overall_status": "PASS" if passed else "FAIL",
    }

    evidence_path = Path("evidence.json")
    audit_path = Path("audit.json")
    evidence_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    audit_path.write_text(json.dumps(audit.to_dict(), indent=2, sort_keys=True) + "\n")

    manifest = build_manifest()
    manifest_path = Path("reproducibility-manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    print(json.dumps(payload, indent=2, sort_keys=True))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if payload["overall_status"] == "PASS" and manifest["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
