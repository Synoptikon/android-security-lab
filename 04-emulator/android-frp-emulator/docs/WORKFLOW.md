# FRP Emulator — Workflow v0.3

## Objective

Provide a repeatable workflow for selecting a simulated Android/device profile, driving the security state machine, evaluating policies/invariants, and producing auditable evidence.

## Execution workflow

```text
1. SELECT PROFILE
   Android version + device model + lock mode
             ↓
2. BUILD INITIAL STATE
   DEVICE_READY / LOCKED
             ↓
3. APPLY CONTROLLED EVENT
   RESET_REQUEST / AUTH_ATTEMPT / SCENARIO_ACTION
             ↓
4. STATE TRANSITION
   State machine validates transition
             ↓
5. POLICY EVALUATION
   Preconditions + invariants + forbidden transitions
             ↓
6. SYNTHETIC FAULT (optional)
   Inject only a modeled defect class
             ↓
7. ASSERT RESULT
   Expected secure/insecure simulated outcome
             ↓
8. CAPTURE EVIDENCE
   Events + result + invariant findings + hashes
             ↓
9. AUDIT
   Coverage + invariant failures + reproducibility
             ↓
10. CI GATE
    PASS → candidate for next release
    FAIL → inspect artifact/log → correct → rerun
```

## State contract

| Current | Event | Expected next state |
|---|---|---|
| `DEVICE_READY` | `LOCK` | `LOCKED` |
| `LOCKED` | `RESET_REQUEST` | `RESET_PENDING` |
| `RESET_PENDING` | `RESET_COMPLETE` | `FRP_LOCKED` when FRP policy is enabled |
| `FRP_LOCKED` | `VALID_ACCOUNT_AUTH` | `AUTHENTICATED` |
| `FRP_LOCKED` | `INVALID_AUTH` | `FRP_LOCKED` |

Any transition not explicitly declared is a testable rejection, not an implicit success path.

## Profile workflow

1. Load an `AndroidProfile`.
2. Load a `DeviceProfile` compatible with that simulated Android profile.
3. Select one lock mode: pattern, PIN or password.
4. Optionally enable the simulated Google-account-required state.
5. Generate a scenario ID and deterministic initial state.
6. Execute only declared scenario events.
7. Evaluate the invariant set.
8. Persist evidence and audit artifacts.

## Invariant gate

A run is releasable only when:

- transition coverage = `1.0`;
- policy-profile coverage = `1.0`;
- policy-decision coverage = `true`;
- invariant failures = `0`;
- reproducibility manifest status = `PASS`;
- evidence hash matches the manifest;
- commit SHA is recorded.

## CI workflow

The existing GitHub Actions workflow remains the execution authority. Documentation changes do not replace automated validation. Changes to emulator behavior must pass the existing test, transition-matrix, fault-injection, resilience, evidence, audit and release-validation stages.

## Failure handling

`FAIL` is terminal for the current candidate. Do not bypass a failed gate. Inspect the generated artifact and CI log, identify the causal defect, apply the smallest correction, then rerun validation.

## Safety boundary

The workflow intentionally stops at simulation and verification. It must not provide instructions, payloads or sequences for bypassing FRP or Google authentication on a real device.
