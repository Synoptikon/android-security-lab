# Release Certification — v0.2-policy-profiles

**Status:** CERTIFIED / HARDENING CLOSED
**Scope:** `controlled-simulator-only`

## Certified source

- Branch: `v0.2-policy-profiles`
- Certified commit: `158b51cec6486b126324f0c56bf681927fcea1d8`
- Certification branch: `v0.2-release-hardening`
- Certification date: 2026-09-14

## Original certification CI evidence

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

## Evidence integrity — certified release

- Evidence SHA-256: `452646650ee0b54124a33dd0f9fc99a28e3672883a6d838dbf221fa66af76a25`
- CI artifact: `frp-emulator-evidence`
- Artifact ID: `10345236924`
- Artifact digest: `sha256:452646650ee0b54124a33dd0f9fc99a28e3672883a6d838dbf221fa66af76a25`

## Release hardening verification

The hardening branch was validated without changing the certified simulator behavior.

- Hardening commit: `942376705d3a20e8d33eb78c0a1f6f5e4319bcc1`
- Workflow: `FRP Emulator Validation`
- Run: `#52`
- Run ID: `34840244120`
- Result: `success`
- Pytest: `24 passed`
- Transition matrix: PASS — 6/6, coverage 1.0
- Fault injection: PASS — 3/3, coverage 1.0
- Resilience matrix: PASS — 6/6, 0 invariant failures
- Evidence: PASS — `overall_status` present
- Formal audit: PASS
- Release Gate v4: PASS
- Reproducibility assertions: PASS
- Artifact: `frp-emulator-evidence`, ID `10346025699`
- Artifact digest: `sha256:5a1b61b253d536979c3c80626ea922f1cc1050fa42a2f9f1b3e360d6e9ebf74b`
- Hardening evidence SHA-256: `7374a3b769bc90fabf89b0efe021ad15ad6bdbb3d6fbc99569e61e070ad7d1be`

The anti-regression contract preventing removal of `overall_status` is therefore covered by a successful CI run.

## Certification boundary

This certification applies only to the deterministic Android FRP **simulator** and its synthetic lab-token/policy model. It does not authorize or implement FRP bypass, account recovery, credential recovery, ADB/Fastboot evasion, or modification of real Android devices.

## Freeze rule

`v0.2-policy-profiles` and `v0.2-certified` remain frozen certified baselines. New functionality must be developed from a separate branch. Before merging future functional changes, compare the proposed branch against the certified commit and rerun the complete release gate.
