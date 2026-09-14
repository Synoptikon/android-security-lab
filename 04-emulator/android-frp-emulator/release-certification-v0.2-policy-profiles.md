# Release Certification — v0.2-policy-profiles

**Status:** CERTIFIED
**Scope:** `controlled-simulator-only`

## Certified source

- Branch: `v0.2-policy-profiles`
- Certified commit: `158b51cec6486b126324f0c56bf681927fcea1d8`
- Certification branch: `v0.2-release-hardening`
- Certification date: 2026-09-14

## CI evidence

- Workflow: `frp-emulator-ci`
- Successful workflow run: `#49`
- Run ID: `34839769166`
- Result: `success`
- Python: `3.12.14`
- Pytest: `22/22 passed`

## Release gates

| Gate | Result |
|---|---|
| Scenario execution | PASS |
| Transition matrix | PASS — coverage 1.0 |
| Fault injection | PASS — coverage 1.0 |
| Resilience matrix | PASS — 6/6, 0 invariant failures |
| Evidence | PASS |
| Formal audit | PASS |
| Policy profile coverage | PASS — 1.0 |
| Policy decision coverage | PASS |
| Persistence coverage | PASS |
| Recovery coverage | PASS |
| Security boundary | PASS — `controlled-simulator-only` |
| Reproducibility | PASS |
| Release Gate v4 | PASS |

## Evidence integrity

- Evidence SHA-256: `452646650ee0b54124a33dd0f9fc99a28e3672883a6d838dbf221fa66af76a25`
- CI artifact: `frp-emulator-evidence`
- Artifact ID: `10345236924`
- Artifact digest: `sha256:452646650ee0b54124a33dd0f9fc99a28e3672883a6d838dbf221fa66af76a25`

## Certification boundary

This certification applies only to the deterministic Android FRP **simulator** and its synthetic lab-token/policy model. It does not authorize or implement FRP bypass, account recovery, credential recovery, ADB/Fastboot evasion, or modification of real Android devices.

## Freeze rule

`v0.2-policy-profiles` is the certified baseline. New functionality must be developed from a separate branch and must not alter this baseline. Before merging future functional changes, compare the proposed branch against this certified commit and rerun the complete release gate.
