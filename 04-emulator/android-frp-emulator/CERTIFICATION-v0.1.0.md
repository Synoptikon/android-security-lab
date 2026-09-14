# FRP Emulator — Certification v0.1.0

## Scope

This certification applies only to the controlled Android FRP simulator under `04-emulator/android-frp-emulator/`.

It does not implement or validate FRP bypass on physical devices, ADB/Fastboot bypass procedures, credential recovery, or security-control evasion.

## Certified commit

- Commit: `a07fe3ed3dd575bfe5fb6e7034f050c2e68b6a5a`
- CI run: `34831152890`
- Job: `103934564174`
- Python: `3.12.14`

## Validation gates

1. Full pytest suite: PASS — 14 passed.
2. CI scenario `ci-001`: PASS — `DEVICE_READY`, 4 events.
3. Evidence generation: PASS — `evidence.json` produced.
4. Scenario coverage: PASS — `1.0`.
5. Transition coverage: PASS — `1.0`, no uncovered transitions.
6. Invariants: PASS — 0 failures.
7. Formal audit: PASS — overall status `PASS`.
8. Security boundary: PASS — `controlled-simulator-only`.
9. Reproducibility: PASS — commit SHA and evidence SHA-256 verified.
10. Artifact publication: PASS — evidence, audit, and reproducibility manifest uploaded.

## Reproducibility manifest

- Schema: `frp-emulator-reproducibility-manifest/v1`
- Evidence schema: `frp-emulator-evidence/v2`
- Audit schema: `frp-emulator-audit/v1`
- Evidence SHA-256: `8d3796b5bee7bf196096feba781a7a3428b05cb17b1abff2ac71dd8cb455c14b`
- Overall status: `PASS`

## Artifact

GitHub Actions artifact:

- Name: `frp-emulator-evidence`
- Artifact ID: `10341934173`
- Digest: `sha256:003aef001998987306b47230c64e37f4133d228304b71653f0c3fdc0768f4e35`
- Contents: `evidence.json`, `audit.json`, `reproducibility-manifest.json`

## Decision

**CERTIFIED: 10/10 validation gates PASS.**

This certification freezes the current simulator baseline before further feature development. Subsequent changes must preserve the same security boundary and rerun the complete validation chain.
