"""Anti-regression tests for the release-gate evidence contract."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_evidence_builder_declares_overall_status() -> None:
    source = (ROOT / "evidence.py").read_text()
    assert '"overall_status": "PASS" if passed else "FAIL"' in source


def test_release_gate_requires_evidence_overall_status() -> None:
    source = (ROOT / "validate_release.py").read_text()
    assert 'evidence.get("overall_status") == "PASS"' in source
