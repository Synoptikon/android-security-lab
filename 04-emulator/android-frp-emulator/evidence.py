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
    payload = {
        "schema": "frp-emulator-evidence/v2",
        "scope": "controlled-simulator-only",
        "scenarios": [result.__dict__ for result in results],
        "audit": audit.to_dict(),
        "passed": all(result.passed for result in results) and audit.overall_status == "PASS",
    }
    output = Path("evidence.json")
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    manifest = build_manifest()
    print(json.dumps(payload, indent=2, sort_keys=True))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if payload["passed"] and manifest["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
