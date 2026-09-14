"""Run the controlled scenario suite and emit machine-readable evidence."""
from __future__ import annotations

import json
from pathlib import Path

from scenario import SCENARIOS, run_scenario


def main() -> int:
    results = [run_scenario(name, f"ci-{index:03d}") for index, name in enumerate(SCENARIOS, 1)]
    payload = {
        "schema": "frp-emulator-evidence/v1",
        "scope": "controlled-simulator-only",
        "scenarios": [result.__dict__ for result in results],
        "passed": all(result.passed for result in results),
    }
    output = Path("evidence.json")
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
