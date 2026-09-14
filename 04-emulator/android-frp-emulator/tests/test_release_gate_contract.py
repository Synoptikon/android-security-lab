"""Anti-regression tests for the release-gate evidence contract."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_evidence_declares_overall_status() -> None:
    evidence = json.loads((ROOT / "evidence.json").read_text())
    assert "overall_status" in evidence
    assert evidence["overall_status"] in {"PASS", "FAIL"}


def test_release_gate_requires_evidence_overall_status() -> None:
    source = (ROOT / "validate_release.py").read_text()
    assert 'evidence.get("overall_status") == "PASS"' in source
